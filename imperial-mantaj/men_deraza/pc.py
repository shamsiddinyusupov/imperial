"""jitter of a rendered clip: phase-correlation motion between consecutive frames (1/4 scale), minus its 0.5 s moving
average; RMS in output pixels. python3 pc.py a.mp4 [b.mp4 ...]"""
import subprocess
import sys

import cv2
import numpy as np


def jit(path):
    w, h = 270, 480
    raw = subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-i", path, "-vf", f"scale={w}:{h},format=gray", "-f",
                          "rawvideo", "-"], capture_output=True).stdout
    fr = np.frombuffer(raw, np.uint8).reshape(-1, h, w).astype(np.float32)
    win = np.hanning(w)[None, :] * np.hanning(h)[:, None]
    d = np.array([cv2.phaseCorrelate(fr[i - 1] * win, fr[i] * win)[0] for i in range(1, len(fr))])
    sm = np.stack([np.convolve(d[:, k], np.ones(15) / 15, mode="same") for k in range(2)], 1)
    return float(np.sqrt(((d - sm) ** 2).sum(1).mean())) * 4


if __name__ == "__main__":
    for p in sys.argv[1:]:
        print(p, round(jit(p), 2))
