"""Locked-tripod stabilisation for the dikey clip IMG_3656 (SDR 4K, handheld).
Track features only on static parts (valance + ceiling, away from the moving tulle and the worker) with OpenCV LK +
RANSAC similarity on a 1/4-scale grey copy, fit a constant (deg 0) camera, then render each output frame straight from
the 4K frame: output = synthetic crop/pan ∘ locked camera ∘ actual⁻¹. Native resolution for the detail crops.

python3 stab2.py [names...]
"""
import math
import subprocess
import sys

import cv2
import numpy as np

D = "/home/claude/reels/n11"
SRC = f"{D}/src/IMG_3656.mov"
SW, SH = 2160, 3840
K = 4
OW, OH = 1080, 1920
FPS = 30
GRADE = ("colorbalance=rm=-0.02:gm=0.03:bm=-0.01:rh=-0.01:gh=0.02,eq=contrast=1.05:saturation=0.95:gamma=1.03,"
         "unsharp=5:5:0.25")
MASK = (0.36, 0.0, 1.0, 1.0)           # x0, y0, x1, y1 (fractions): everything right of the worker; RANSAC keeps the static majority
# name: (ss, dur, crop0, crop1, deg)  crop = (cx, cy, width) in source px; height = width * 16/9
WIDE = (0.275 * SW + SW / 1.38 / 2, 0.14 * SH + SH / 1.38 / 2, SW / 1.38)
MASKS = {"d1": (0.45, 0.18, 1.0, 0.75)}   # detail: track the plane we look at (parallax)
SHOTS = {
    "w_close": (0.3, 4.4, WIDE, WIDE, 0),
    "w_open": (14.9, 4.8, WIDE, WIDE, 1),
    "d1": (6.3, 3.6, (1620, 1900, 1080), (1510, 1900, 1080), 1),
    "d2": (10.0, 3.2, (1240, 1860, 1080), (1240, 1700, 1080), 1),
}


def gray(ss, dur):
    w, h = SW // K, SH // K
    p = subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-ss", f"{ss}", "-t", f"{dur}", "-i", SRC, "-an",
                        "-vf", f"scale={w}:{h},format=gray", "-f", "rawvideo", "-"], capture_output=True, check=True)
    return np.frombuffer(p.stdout, np.uint8).reshape(-1, h, w)


def track(g, mask=MASK):
    h, w = g.shape[1:]
    m = np.zeros((h, w), np.uint8)
    x0, y0, x1, y1 = mask
    m[int(y0 * h):int(y1 * h), int(x0 * w):int(x1 * w)] = 255
    A = np.eye(3)
    out = [A.copy()]
    for i in range(1, len(g)):
        p0 = cv2.goodFeaturesToTrack(g[i - 1], maxCorners=500, qualityLevel=0.003, minDistance=6, blockSize=7, mask=m)
        M = None
        if p0 is not None and len(p0) >= 12:
            p1, st, _ = cv2.calcOpticalFlowPyrLK(g[i - 1], g[i], p0, None, winSize=(31, 31), maxLevel=4)
            ok = st.reshape(-1) == 1
            if ok.sum() >= 10:
                M, inl = cv2.estimateAffinePartial2D(p0[ok], p1[ok], method=cv2.RANSAC, ransacReprojThreshold=1.0)
        if M is not None:                         # sanity: a handheld phone does not jump >0.6 deg or >3 % per frame
            ang = math.degrees(math.atan2(M[1, 0], M[0, 0]))
            sc = math.hypot(M[0, 0], M[1, 0])
            if abs(ang) > 0.6 or abs(sc - 1) > 0.03:
                M = np.array([[1, 0, M[0, 2]], [0, 1, M[1, 2]]], float)
        Mi = np.eye(3) if M is None else np.vstack([M, [0, 0, 1]])
        A = Mi @ A                                    # frame0 -> frame i (analysis scale)
        out.append(A.copy())
    return out


def decompose(A):
    s = math.hypot(A[0, 0], A[1, 0])
    return A[0, 2], A[1, 2], math.atan2(A[1, 0], A[0, 0]), math.log(s)


def compose(tx, ty, a, ls):
    s = math.exp(ls)
    return np.array([[s * math.cos(a), -s * math.sin(a), tx], [s * math.sin(a), s * math.cos(a), ty], [0, 0, 1]])


def run(name):
    ss, dur, c0, c1, deg = SHOTS[name]
    g = gray(ss, dur)
    As = track(g, MASKS.get(name, MASK))
    n = len(As)
    P = np.array([decompose(A) for A in As])
    t = np.linspace(-1, 1, n)
    Sm = np.stack([np.polyval(np.polyfit(t, P[:, k], deg), t) for k in range(4)], 1)
    Kc = np.diag([K, K, 1.0])
    stab = [Kc @ compose(*Sm[i]) @ np.linalg.inv(As[i]) @ np.linalg.inv(Kc) for i in range(n)]   # full-res
    # synthetic camera: crop window moves linearly (eased) from c0 to c1
    def crop_mat(u, grow=1.0):
        e = u * u * (3 - 2 * u) * 0.4 + u * 0.6
        cx = c0[0] + (c1[0] - c0[0]) * e
        cy = c0[1] + (c1[1] - c0[1]) * e
        cw = (c0[2] + (c1[2] - c0[2]) * e) / grow
        s = OW / cw
        return np.array([[s, 0, OW / 2 - s * cx], [0, s, OH / 2 - s * cy], [0, 0, 1]])

    corners = np.array([[0, 0, 1], [OW, 0, 1], [0, OH, 1], [OW, OH, 1]], float).T

    def ok(grow):
        for i in range(n):
            M = crop_mat(i / max(1, n - 1), grow) @ stab[i]
            src = np.linalg.inv(M) @ corners
            if (src[0] < 1).any() or (src[0] > SW - 1).any() or (src[1] < 1).any() or (src[1] > SH - 1).any():
                return False
        return True

    grow = 1.0
    while not ok(grow) and grow < 1.4:
        grow += 0.01
    dec = subprocess.Popen(["ffmpeg", "-nostdin", "-v", "error", "-ss", f"{ss}", "-t", f"{dur}", "-i", SRC, "-an",
                            "-vf", "format=bgr24", "-f", "rawvideo", "-"], stdout=subprocess.PIPE)
    enc = subprocess.Popen(["ffmpeg", "-nostdin", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24",
                            "-s", f"{OW}x{OH}", "-r", str(FPS), "-i", "-", "-vf", f"format=yuv420p,{GRADE},setsar=1",
                            "-c:v", "libx264", "-preset", "fast", "-crf", "14", "-pix_fmt", "yuv420p",
                            f"{D}/st2/{name}.mp4"], stdin=subprocess.PIPE)
    fsz = SW * SH * 3
    k = 0
    while k < n:
        buf = dec.stdout.read(fsz)
        if len(buf) < fsz:
            break
        fr = np.frombuffer(buf, np.uint8).reshape(SH, SW, 3)
        M = crop_mat(k / max(1, n - 1), grow) @ stab[k]
        out = cv2.warpAffine(fr, M[:2], (OW, OH), flags=cv2.INTER_AREA if M[0, 0] < 0.8 else cv2.INTER_CUBIC,
                             borderMode=cv2.BORDER_REFLECT)
        enc.stdin.write(out.tobytes())
        k += 1
    dec.stdout.close()
    dec.wait()
    enc.stdin.close()
    enc.wait()
    rng = np.ptp(P[:, :2], 0) * K
    print(f"{name}: frames {k}/{n}, shake range {rng.round(0)} px (4K), rot {np.degrees(np.ptp(P[:, 2])):.2f} deg, "
          f"extra zoom {grow:.2f}", flush=True)


if __name__ == "__main__":
    import os
    os.makedirs(f"{D}/st2", exist_ok=True)
    names = sys.argv[1:] or list(SHOTS)
    from multiprocessing import Pool
    with Pool(2) as p:
        p.map(run, names, chunksize=1)
