"""Premium look for real shots: slow push-in, tilt-shift depth of field, the same grade as asm3d (split tone, bloom,
vignette, grain). python3 lookpass.py  -> seg/L_<name>.mp4"""
import subprocess
import sys
from multiprocessing import Pool

import cv2
import numpy as np

sys.path.insert(0, "/home/claude/reels/yigil2")
from asm3d import look  # noqa: E402

D = "/home/claude/reels/yigil2"
W, H = 1080, 1920
# name: (src, zoom0, zoom1, focus centre y (0..1), focus angle deg, sharp half-width px, blur sigma, exposure)
JOBS = {"x_dikey": ("seg/x_dikey.mp4", 1.04, 1.14, 0.45, -12, 260, 9, 0.95),
        "x_kombo": ("seg/x_kombo.mp4", 1.04, 1.14, 0.5, 20, 280, 9, 1.0),
        "x_plisse": ("seg/x_plisse_s.mp4", 1.03, 1.12, 0.5, -25, 300, 9, 0.92),
        "x_rollo": ("seg/x_rollo.mp4", 1.04, 1.14, 0.45, 8, 300, 8, 0.95),
        "y_dikey": ("seg/m_dikey.mp4", 1.02, 1.06, 0.5, 0, 520, 6, 1.0),
        "y_kombo": ("seg/y_kombo.mp4", 1.02, 1.06, 0.45, 0, 520, 6, 1.0),
        "y_plisse": ("seg/y_plisse.mp4", 1.02, 1.06, 0.4, 0, 520, 6, 1.0),
        "y_rollo": ("seg/y_rollo.mp4", 1.02, 1.06, 0.5, 0, 520, 6, 1.0)}


def run(name):
    src, z0, z1, fy, ang, hw, sig, ex = JOBS[name]
    raw = subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-i", f"{D}/{src}", "-f", "rawvideo", "-pix_fmt", "bgr24",
                          "-"], capture_output=True, check=True).stdout
    fr = np.frombuffer(raw, np.uint8).reshape(-1, H, W, 3)
    n = len(fr)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    a = np.radians(ang)
    dist = np.abs((yy - fy * H) * np.cos(a) - (xx - W / 2) * np.sin(a))
    m = np.clip((dist - hw) / 520, 0, 1)[..., None]
    p = subprocess.Popen(f"ffmpeg -nostdin -v error -y -f rawvideo -pix_fmt bgr24 -s {W}x{H} -r 30 -i - -c:v libx264 "
                         f"-preset fast -crf 15 -pix_fmt yuv420p {D}/seg/L_{name}.mp4", shell=True, stdin=subprocess.PIPE)
    for i in range(n):
        u = i / max(1, n - 1)
        z = z0 + (z1 - z0) * (u * u * (3 - 2 * u) * 0.7 + 0.3 * u)
        M = cv2.getRotationMatrix2D((W / 2, H * 0.48), 0, z)
        im = cv2.warpAffine(fr[i], M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT).astype(np.float32)
        im = im * ex
        bl = cv2.GaussianBlur(im, (0, 0), sig)
        im = im * (1 - m) + bl * m
        p.stdin.write(look(im, 500 + i).astype(np.uint8).tobytes())
    p.stdin.close()
    p.wait()
    return name, n


if __name__ == "__main__":
    with Pool(2) as pool:
        print(pool.map(run, sys.argv[1:] or list(JOBS)))
