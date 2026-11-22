"""Slider-smooth stabilisation for the «Men — derazangizman» scene clips (owner 22.11: «kadrlar silliq emas»).
Per shot: LK features + RANSAC similarity on a 1/4-scale grey copy (optionally only on static parts), sanity limits
per frame, camera path smoothed by a low-order polynomial (locked / linear) or a wide Gaussian (walks, pans), then each
output frame is rendered straight from the 4K (tone-mapped) frame with one warp: crop ∘ smooth ∘ actual⁻¹.
Also prints a jitter metric (residual frame-to-frame motion after removing the smooth path) before/after.
python3 stab3.py [names...]
"""
import json
import math
import subprocess
import sys

import cv2
import numpy as np
from scipy.ndimage import gaussian_filter1d

D = "/home/claude/reels/deraza"
ITEMS = {i["id"]: i for i in json.load(open("/home/claude/baza_work/items.json"))}
TM = ("zscale=t=linear:npl=203,format=gbrpf32le,zscale=p=bt709,tonemap=hable:desat=0,"
      "zscale=t=bt709:m=bt709:r=tv")
OW, OH, FPS, K = 1080, 1920, 30, 4
GRADE = "eq=contrast=1.04:saturation=1.05,unsharp=5:5:0.3"
# name: (item id, ss, dur, smoothing, mask)   smoothing: ("poly", deg) | ("gauss", sigma frames)
SHOTS = {
    "s1": (619, 0.3, 4.6, ("gauss", 22), None),
    "s2b": (557, 0.0, 2.7, ("gauss", 24), None),
    "m704": (704, 5.0, 2.6, ("gauss", 16), None),
    "noon": (595, 1.0, 3.8, ("gauss", 24), None),
    "s2c": (610, 0.2, 4.4, ("gauss", 24), None),
    "w619": (619, 5.0, 3.6, ("poly", 1), None),
    "s4": (705, 2.0, 4.0, ("poly", 1), (0.45, 0.0, 1.0, 1.0)),
    "s5": (650, 0.0, 6.0, ("gauss", 12), (0.80, 0.0, 1.0, 1.0)),
    "s6": (705, 8.5, 8.0, ("gauss", 26), (0.45, 0.0, 1.0, 1.0)),
    "s8": (751, 4.5, 5.0, ("gauss", 24), None),
}


def src_size(it):
    """displayed (rotation-applied) size of the source"""
    p = subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-i", it["path"], "-frames:v", "1", "-f", "image2pipe",
                        "-vcodec", "png", "-"], capture_output=True)
    im = cv2.imdecode(np.frombuffer(p.stdout, np.uint8), cv2.IMREAD_GRAYSCALE)
    return im.shape[1], im.shape[0]


def gray(it, ss, dur, w, h):
    p = subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-ss", f"{ss}", "-t", f"{dur}", "-i", it["path"], "-an",
                        "-vf", f"scale={w}:{h},format=gray", "-f", "rawvideo", "-"], capture_output=True, check=True)
    return np.frombuffer(p.stdout, np.uint8).reshape(-1, h, w)


def track(g, mask):
    h, w = g.shape[1:]
    m = np.zeros((h, w), np.uint8)
    x0, y0, x1, y1 = mask or (0, 0, 1, 1)
    m[int(y0 * h):int(y1 * h), int(x0 * w):int(x1 * w)] = 255
    A = np.eye(3)
    out = [A.copy()]
    for i in range(1, len(g)):
        p0 = cv2.goodFeaturesToTrack(g[i - 1], maxCorners=600, qualityLevel=0.003, minDistance=6, blockSize=7, mask=m)
        M = None
        if p0 is not None and len(p0) >= 12:
            p1, st, _ = cv2.calcOpticalFlowPyrLK(g[i - 1], g[i], p0, None, winSize=(31, 31), maxLevel=4)
            ok = st.reshape(-1) == 1
            if ok.sum() >= 10:
                M, _ = cv2.estimateAffinePartial2D(p0[ok], p1[ok], method=cv2.RANSAC, ransacReprojThreshold=1.0)
        if M is not None:
            ang = math.degrees(math.atan2(M[1, 0], M[0, 0]))
            sc = math.hypot(M[0, 0], M[1, 0])
            if abs(ang) > 0.8 or abs(sc - 1) > 0.04:
                M = np.array([[1, 0, M[0, 2]], [0, 1, M[1, 2]]], float)
        Mi = np.eye(3) if M is None else np.vstack([M, [0, 0, 1]])
        A = Mi @ A
        out.append(A.copy())
    return out


def decompose(A):
    return A[0, 2], A[1, 2], math.atan2(A[1, 0], A[0, 0]), math.log(math.hypot(A[0, 0], A[1, 0]))


def compose(tx, ty, a, ls):
    s = math.exp(ls)
    return np.array([[s * math.cos(a), -s * math.sin(a), tx], [s * math.sin(a), s * math.cos(a), ty], [0, 0, 1]])


def jitter(P):
    """RMS of frame-to-frame translation after removing a 0.5 s moving average (analysis px)"""
    d = np.diff(P[:, :2], axis=0)
    sm = np.stack([np.convolve(d[:, k], np.ones(15) / 15, mode="same") for k in range(2)], 1)
    return float(np.sqrt(((d - sm) ** 2).sum(1).mean()))


def run(name):
    iid, ss, dur, smooth, mask = SHOTS[name]
    it = ITEMS[iid]
    SW, SH = src_size(it)
    g = gray(it, ss, dur, SW // K, SH // K)
    As = track(g, mask)
    n = len(As)
    P = np.array([decompose(A) for A in As])
    if smooth[0] == "poly":
        t = np.linspace(-1, 1, n)
        Sm = np.stack([np.polyval(np.polyfit(t, P[:, k], smooth[1]), t) for k in range(4)], 1)
    else:
        Sm = np.stack([gaussian_filter1d(P[:, k], smooth[1], mode="nearest") for k in range(4)], 1)
    Kc = np.diag([K, K, 1.0])
    stab = [Kc @ compose(*Sm[i]) @ np.linalg.inv(As[i]) @ np.linalg.inv(Kc) for i in range(n)]
    cw0 = min(SW, SH * 9 / 16)
    corners = np.array([[0, 0, 1], [OW, 0, 1], [0, OH, 1], [OW, OH, 1]], float).T

    def crop(grow):
        cw = cw0 / grow
        s = OW / cw
        return np.array([[s, 0, OW / 2 - s * SW / 2], [0, s, OH / 2 - s * SH / 2], [0, 0, 1]])

    def ok(grow):
        C = crop(grow)
        for i in range(n):
            src = np.linalg.inv(C @ stab[i]) @ corners
            if (src[0] < 1).any() or (src[0] > SW - 1).any() or (src[1] < 1).any() or (src[1] > SH - 1).any():
                return False
        return True

    grow = 1.02
    while not ok(grow) and grow < 1.24:
        grow += 0.01
    hdr = it.get("trc") == "arib-std-b67"
    vf = (TM + "," if hdr else "") + "format=bgr24"
    dec = subprocess.Popen(["ffmpeg", "-nostdin", "-v", "error", "-ss", f"{ss}", "-t", f"{dur}", "-i", it["path"], "-an",
                            "-vf", vf, "-f", "rawvideo", "-"], stdout=subprocess.PIPE)
    enc = subprocess.Popen(["ffmpeg", "-nostdin", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24",
                            "-s", f"{OW}x{OH}", "-r", str(FPS), "-i", "-", "-vf", f"format=yuv420p,{GRADE},setsar=1",
                            "-c:v", "libx264", "-preset", "fast", "-crf", "14", "-pix_fmt", "yuv420p",
                            f"{D}/seg/{name}.mp4"], stdin=subprocess.PIPE)
    fsz = SW * SH * 3
    C = crop(grow)
    k = 0
    while k < n:
        buf = dec.stdout.read(fsz)
        if len(buf) < fsz:
            break
        fr = np.frombuffer(buf, np.uint8).reshape(SH, SW, 3)
        M = C @ stab[k]
        out = cv2.warpAffine(fr, M[:2], (OW, OH), flags=cv2.INTER_AREA if M[0, 0] < 0.8 else cv2.INTER_CUBIC,
                             borderMode=cv2.BORDER_REFLECT)
        enc.stdin.write(out.tobytes())
        k += 1
    dec.stdout.close()
    dec.wait()
    enc.stdin.close()
    enc.wait()
    print(f"{name}: {SW}x{SH} frames {k}/{n}, source jitter {jitter(P) * K:.2f}px, zoom {grow:.2f}", flush=True)


if __name__ == "__main__":
    names = sys.argv[1:] or list(SHOTS)
    from multiprocessing import Pool
    with Pool(2) as p:
        p.map(run, names, chunksize=1)
