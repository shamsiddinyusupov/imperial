"""Hook «Bu rasmni quyosh chizgan»: find the sunlit window shape on the blind in one reference frame, follow the
camera with frame-to-frame tracking, and return its outline per frame (output px) for an orange line that draws
itself along it. Writes trace.json: {"n": frames, "paths": [[[x, y], ...] per frame]} (one closed outline)."""
import json
import subprocess

import cv2
import numpy as np

D = "/home/claude/reels/rollo1"
W, H = 1080, 1920
REF = 30          # frame index (1.0 s)


def frames():
    raw = subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-i", f"{D}/seg/trace.mp4", "-f", "rawvideo",
                          "-pix_fmt", "bgr24", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, H, W, 3)


def outline(im):
    hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV).astype(np.float32)
    lab = cv2.cvtColor(im, cv2.COLOR_BGR2LAB).astype(np.float32)
    sc = (cv2.GaussianBlur(hsv[..., 2], (0, 0), 5) - 200) / 30 + (cv2.GaussianBlur(lab[..., 2], (0, 0), 5) - 145) / 5
    m = (sc > 1.3).astype(np.uint8) * 255
    m[: int(H * 0.45)] = 0
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((7, 7), np.uint8))
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((15, 15), np.uint8))
    cs, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    c = max(cs, key=cv2.contourArea)[:, 0, :].astype(np.float32)
    # smooth the outline and resample evenly
    k = 9
    pad = np.vstack([c[-k:], c, c[:k]])
    ker = np.ones(2 * k + 1) / (2 * k + 1)
    sm = np.stack([np.convolve(pad[:, j], ker, mode="same")[k:-k] for j in range(2)], 1)
    seg = np.hypot(*np.diff(np.vstack([sm, sm[:1]]), axis=0).T)
    s = np.concatenate([[0], np.cumsum(seg)])
    u = np.linspace(0, s[-1], 420, endpoint=False)
    closed = np.vstack([sm, sm[:1]])
    pts = np.stack([np.interp(u, s, closed[:, j]) for j in range(2)], 1)
    # start the stroke at the top tip of the shape
    i0 = int(np.argmin(pts[:, 1]))
    return np.roll(pts, -i0, axis=0)


def track(fr):
    g = [cv2.cvtColor(cv2.resize(f, (W // 2, H // 2)), cv2.COLOR_BGR2GRAY) for f in fr]
    n = len(g)
    A = [np.eye(3) for _ in range(n)]           # maps frame REF -> frame i (half-res)

    def step(a, b):
        p0 = cv2.goodFeaturesToTrack(g[a], 500, 0.005, 8)
        p1, st, _ = cv2.calcOpticalFlowPyrLK(g[a], g[b], p0, None, winSize=(31, 31), maxLevel=4)
        ok = st.reshape(-1) == 1
        M, _ = cv2.estimateAffinePartial2D(p0[ok], p1[ok], method=cv2.RANSAC, ransacReprojThreshold=1.0)
        return np.vstack([M, [0, 0, 1]])
    for i in range(REF + 1, n):
        A[i] = step(i - 1, i) @ A[i - 1]
    for i in range(REF - 1, -1, -1):
        A[i] = step(i + 1, i) @ A[i + 1]
    S = np.diag([2.0, 2.0, 1.0])
    return [S @ a @ np.linalg.inv(S) for a in A]


def main():
    fr = frames()
    c = outline(fr[REF])
    A = track(fr)
    paths = []
    for a in A:
        p = (np.c_[c, np.ones(len(c))] @ a.T)[:, :2]
        paths.append(np.round(p, 1).tolist())
    json.dump(dict(n=len(fr), paths=paths), open(f"{D}/trace.json", "w"))
    print("frames", len(fr), "points", len(c))


if __name__ == "__main__":
    main()
