"""«Ikki xona»: smooth-glide stabilisation + grade for «Faqat qarang» v2, and Ken Burns moves for the owner's photos.

Video shots: 4K HLG -> track features on a small grey copy (OpenCV LK + RANSAC similarity) -> camera path
-> fit a low-order polynomial (0 = locked tripod, 1 = constant glide, 2 = gentle ease) -> warp each full frame
onto that path, with one constant zoom per shot so no border ever shows -> centre crop 1080x1920
-> per-shot white balance + 'Iliq krem' look (grade.py).
Photos: sub-pixel zoom/drift on the full-resolution JPEG (no ffmpeg zoompan jitter), same look.

python3 stab.py            # all shots
python3 stab.py A C P1     # some shots
"""
import math
import os
import subprocess
import sys

import cv2
import numpy as np

sys.path.insert(0, "/home/claude/reels/dikey_style")  # grade.py lives there
import grade  # noqa: E402

LOOK_W = grade.LOOK
LOOK_N = ("huesaturation=saturation=-0.85:colors=c+b:strength=8,curves=all='0/0.03 0.25/0.245 0.5/0.52 0.75/0.79 1/0.975',"
          "eq=saturation=0.97,vignette=angle=PI/9,noise=alls=4:allf=t")


LOOK_C = ("huesaturation=saturation=-0.85:colors=c+b:strength=8,curves=all='0/0.0 0.12/0.085 0.5/0.49 0.82/0.84 1/0.96',"
          "eq=saturation=0.92:contrast=1.04,colorbalance=rs=-0.015:bs=0.02:rm=0.02:bm=-0.02:rh=0.025:bh=-0.03,"
          "vignette=angle=PI/5,noise=alls=5:allf=t")


def gains_for(path, kind):
    g = grade.gains(path)
    return __import__("numpy").full(3, float(g.mean())) if kind == "n" else g


def vf_for(g, kind):
    return f"colorchannelmixer=rr={g[0]:.3f}:gg={g[1]:.3f}:bb={g[2]:.3f},{ {'n': LOOK_N, 'c': LOOK_C}.get(kind, LOOK_W)}"


D = "/home/claude/reels/trailer"
TM = ("zscale=t=linear:npl=203,format=gbrpf32le,zscale=p=bt709,tonemap=hable:desat=0,"
      "zscale=t=bt709:m=bt709:r=tv,format=yuv420p")
FW, FH = 1296, 2304          # working canvas (20 % margin)
OW, OH = 1080, 1920
K = 4                        # analysis is done at FW/K x FH/K
FPS = 30
# video shots: (clip, start, seconds, speed, max polynomial degree)
VID = {   # (clip file, start, seconds, speed, max degree, grade)  — v2: the classic hall appears once
    "S1": ("20260325_133852.mp4", 3.6, 4.0, 1.0, 2, "c"),    # ornate ceiling -> chandelier reveal (only hall shot)
    "S2": ("IMG_5533.mov", 6.0, 3.2, 1.0, 2, "c"),           # light through tulle, brown lamellas
    "S3": ("IMG_5454.mov", 1.5, 2.6, 1.0, 2, "c"),           # bright room, white plisse
    "S4": ("IMG_4421.mov", 0.6, 2.6, 1.0, 2, "c"),           # dark plisse on dark frames
    "S5": ("IMG_5498.mov", 4.0, 2.6, 1.0, 2, "c"),           # white dikey with a gold panel
    "S6": ("IMG_5535.mov", 9.0, 1.4, 1.0, 1, "c"),           # hit 1
    "S7": ("IMG_5459.mov", 1.0, 1.4, 1.0, 1, "c"),           # hit 2
    "S8": ("IMG_5496.mov", 4.5, 1.4, 1.0, 1, "c"),           # hit 3
    "R1": ("IMG_5536.mov", 1.0, 1.6, 1.0, 1, "c"),           # riser montage
    "R2": ("IMG_5453.mov", 2.0, 1.3, 1.0, 1, "c"),
    "R3": ("IMG_5534.mov", 6.0, 1.2, 1.0, 1, "c"),
    "R4": ("IMG_5497.mov", 4.0, 1.1, 1.0, 1, "c"),
    "HERO": ("IMG_5680.mov", 0.6, 3.4, 1.0, 2, "c"),        # walnut window with plisse — final
}
PHO = {}
ENC = ["-c:v", "libx264", "-preset", "fast", "-crf", "14", "-pix_fmt", "yuv420p", "-r", str(FPS)]


def frames_gray(src, ss, dur):
    w, h = FW // K, FH // K
    p = subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-ss", f"{ss}", "-t", f"{dur}", "-i", src, "-an",
                        "-vf", f"scale={FW}:{FH}:force_original_aspect_ratio=increase,crop={FW}:{FH},scale={w}:{h},format=gray", "-f", "rawvideo", "-"], capture_output=True, check=True)
    return np.frombuffer(p.stdout, np.uint8).reshape(-1, h, w)


def mat(tx, ty, a, ls, c):
    """Similarity about the image centre c, as 3x3."""
    s = math.exp(ls)
    R = np.array([[s * math.cos(a), -s * math.sin(a), 0], [s * math.sin(a), s * math.cos(a), 0], [0, 0, 1]])
    C = np.array([[1, 0, c[0]], [0, 1, c[1]], [0, 0, 1]])
    Ci = np.array([[1, 0, -c[0]], [0, 1, -c[1]], [0, 0, 1]])
    T = np.array([[1, 0, tx], [0, 1, ty], [0, 0, 1]])
    return T @ C @ R @ Ci


def params(A, c):
    """tx, ty (centre displacement), angle, log-scale of a 3x3 similarity."""
    a, b = A[0, 0], A[1, 0]
    s = math.hypot(a, b)
    ang = math.atan2(b, a)
    cc = A @ np.array([c[0], c[1], 1.0])
    return cc[0] - c[0], cc[1] - c[1], ang, math.log(s)


def track(g):
    h, w = g.shape[1:]
    c = (w / 2, h / 2)
    A = np.eye(3)
    path = [params(A, c)]
    for i in range(1, len(g)):
        p0 = cv2.goodFeaturesToTrack(g[i - 1], maxCorners=400, qualityLevel=0.005, minDistance=8, blockSize=7)
        M = None
        if p0 is not None and len(p0) >= 12:
            p1, st, _ = cv2.calcOpticalFlowPyrLK(g[i - 1], g[i], p0, None, winSize=(25, 25), maxLevel=3)
            ok = st.reshape(-1) == 1
            if ok.sum() >= 10:
                M, _ = cv2.estimateAffinePartial2D(p0[ok], p1[ok], method=cv2.RANSAC, ransacReprojThreshold=1.5)
        Mi = np.eye(3) if M is None else np.vstack([M, [0, 0, 1]])
        A = Mi @ A                                   # frame0 -> frame i
        path.append(params(A, c))
    return np.array(path), c


def fit(path, deg):
    t = np.linspace(-1, 1, len(path))
    return np.stack([np.polyval(np.polyfit(t, path[:, k], deg), t) for k in range(4)], 1)


def warps(path, smooth, c):
    """Per-frame warp (analysis scale): smooth_camera ∘ actual⁻¹."""
    out = []
    for p, q in zip(path, smooth):
        A = mat(*p, c)
        S = mat(*q, c)
        out.append(S @ np.linalg.inv(A))
    return out


def need_zoom(Ws, c):
    """Smallest constant zoom about the centre so the output crop never leaves the source frame."""
    w, h = 2 * c[0], 2 * c[1]
    cw, ch = OW / K, OH / K
    corners = np.array([[c[0] - cw / 2, c[1] - ch / 2, 1], [c[0] + cw / 2, c[1] - ch / 2, 1],
                        [c[0] - cw / 2, c[1] + ch / 2, 1], [c[0] + cw / 2, c[1] + ch / 2, 1]]).T

    def ok(z):
        Z = mat(0, 0, 0, math.log(z), c)
        for W in Ws:
            src = np.linalg.inv(Z @ W) @ corners
            if (src[0] < 0.5).any() or (src[0] > w - 0.5).any() or (src[1] < 0.5).any() or (src[1] > h - 0.5).any():
                return False
        return True

    lo, hi = 1.0, 1.6
    if ok(lo):
        return lo
    for _ in range(25):
        mid = (lo + hi) / 2
        lo, hi = (lo, mid) if ok(mid) else (mid, hi)
    return hi


def encoder(name, g, speed, kind="w"):
    slow = f",setpts=PTS/{speed},framerate=fps={FPS}:interp_start=0:interp_end=255:scene=100" if speed != 1.0 else ""
    vf = f"{vf_for(g, kind)},unsharp=5:5:0.3{slow},setsar=1"
    return subprocess.Popen(["ffmpeg", "-nostdin", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24",
                             "-s", f"{OW}x{OH}", "-r", str(FPS), "-i", "-", "-vf", vf] + ENC + [f"{D}/seg/{name}.mp4"],
                            stdin=subprocess.PIPE)


def video(name):
    clip, ss, dur, speed, maxdeg, kind = VID[name]
    src = f"{D}/src/{clip}"
    g = frames_gray(src, ss, dur)
    path, c = track(g)
    best = None
    for deg in range(0, maxdeg + 1):                 # prefer the calmest path that needs little zoom
        sm = fit(path, deg)
        Ws = warps(path, sm, c)
        z = need_zoom(Ws, c)
        best = (deg, z, Ws)
        if z <= 1.08:
            break
    deg, z, Ws = best
    # white balance from the middle frame (tone-mapped, centre crop)
    wb = f"{D}/seg/{name}_wb.jpg"
    subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-ss", f"{ss + dur / 2:.2f}", "-i", src, "-frames:v", "1",
                    "-vf", f"scale={FW}:{FH}:force_original_aspect_ratio=increase,crop={FW}:{FH},{TM},crop={OW}:{OH}", "-q:v", "2", wb], check=True)
    gains = gains_for(wb, kind)
    dec = subprocess.Popen(["ffmpeg", "-nostdin", "-v", "error", "-ss", f"{ss}", "-t", f"{dur}", "-i", src, "-an",
                            "-vf", f"scale={FW}:{FH}:flags=lanczos:force_original_aspect_ratio=increase,crop={FW}:{FH},{TM},format=bgr24", "-f", "rawvideo", "-"],
                           stdout=subprocess.PIPE)
    enc = encoder(name, gains, speed, kind)
    Kc = np.diag([K, K, 1.0])
    Z = mat(0, 0, 0, math.log(z), c)
    n = 0
    fsz = FW * FH * 3
    x0, y0 = (FW - OW) // 2, (FH - OH) // 2
    while True:
        buf = dec.stdout.read(fsz)
        if len(buf) < fsz or n >= len(Ws):
            break
        fr = np.frombuffer(buf, np.uint8).reshape(FH, FW, 3)
        Wf = Kc @ (Z @ Ws[n]) @ np.linalg.inv(Kc)
        out = cv2.warpAffine(fr, Wf[:2], (FW, FH), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)
        enc.stdin.write(np.ascontiguousarray(out[y0:y0 + OH, x0:x0 + OW]).tobytes())
        n += 1
    dec.stdout.close()
    dec.wait()
    enc.stdin.close()
    enc.wait()
    rng = np.ptp(path[:, :2], 0) * K
    print(f"{name} {clip}: frames {n}, path range {rng.round(0)} px, degree {deg}, zoom {z:.3f}, gains {np.round(gains, 3)}")


def photo(name):
    fn, dur, z0, z1, dy, kind = PHO[name]
    img = cv2.imread(f"{D}/src/{fn}")
    h, w = img.shape[:2]
    base = max(OW / w, OH / h)                       # cover 1080x1920
    cv2.imwrite(f"{D}/seg/{name}_wb.jpg", cv2.resize(img, (round(w * base), round(h * base)), interpolation=cv2.INTER_AREA))
    gains = gains_for(f"{D}/seg/{name}_wb.jpg", kind)
    enc = encoder(name, gains, 1.0, kind)
    n = round(dur * FPS)
    for i in range(n):
        u = i / (n - 1)
        u = u * u * (3 - 2 * u) * 0.35 + u * 0.65     # mostly linear, softened ends
        s = base * (z0 + (z1 - z0) * u)
        cx, cy = w / 2, h / 2 - dy * u / s
        M = np.array([[s, 0, OW / 2 - s * cx], [0, s, OH / 2 - s * cy]])
        out = cv2.warpAffine(img, M, (OW, OH), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)
        enc.stdin.write(out.tobytes())
    enc.stdin.close()
    enc.wait()
    print(f"{name} {fn}: frames {n}, zoom {z0}->{z1}, gains {np.round(gains, 3)}")


def job(name):
    (video if name in VID else photo)(name)


if __name__ == "__main__":
    os.makedirs(f"{D}/seg", exist_ok=True)
    names = sys.argv[1:] or list(VID) + list(PHO)
    from multiprocessing import Pool
    with Pool(3) as p:
        p.map(job, names, chunksize=1)
