"""12 kombo variants from the owner's two Telegram videos, each framed in the same «slot window».
tg1 = 8110753870440430114.mp4 (1080x1920, baroque/damask kombo), tg2 = -521053696648825206.mp4 (4K, geometric).
VAR = (video, start, available seconds, blind centre x, centre y, blind width) in 1080x1920 coordinates.
"""
import subprocess

import cv2
import numpy as np

D = "/home/claude/reels/kombo_tg"
W, H = 1080, 1920
WIN = (70, 400, 1010, 1540)            # slot window x0, y0, x1, y1
WW, WH = WIN[2] - WIN[0], WIN[3] - WIN[1]
RAD = 46
VAR = [
    ("tg1", 1.0, 3.0, 477, 975, 846),
    ("tg1", 4.8, 2.0, 525, 1020, 930),
    ("tg1", 7.3, 1.5, 465, 945, 846),
    ("tg1", 9.3, 1.7, 504, 1092, 846),
    ("tg1", 23.0, 1.2, 549, 1011, 1023),
    ("tg1", 28.2, 1.4, 579, 1044, 945),
    ("tg2", 33.4, 2.4, 519, 978, 945),
    ("tg2", 36.6, 2.8, 534, 969, 930),
    ("tg2", 40.3, 2.7, 462, 981, 906),
    ("tg2", 43.7, 1.3, 483, 1011, 855),
    ("tg2", 47.0, 2.9, 540, 933, 1080),
    ("tg2", 58.4, 1.6, 546, 978, 1011),
]
FAMILY = ["klassik"] * 6 + ["geometrik"] * 6
GRADE = "eq=contrast=1.04:saturation=1.05,unsharp=5:5:0.4"


def frames(v, ss, dur):
    """decode a slice at 1080x1920, 30 fps, graded -> uint8 array (n, H, W, 3) BGR"""
    p = subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-ss", f"{ss}", "-t", f"{dur}", "-i", f"{D}/src/{v}.mp4",
                        "-an", "-vf", f"scale={W}:{H}:flags=lanczos,fps=30,{GRADE},format=bgr24", "-f", "rawvideo", "-"],
                       capture_output=True, check=True)
    return np.frombuffer(p.stdout, np.uint8).reshape(-1, H, W, 3)


def window_affine(i, extra=1.0):
    _, _, _, cx, cy, bw = VAR[i]
    s = max(900.0 / bw, WW / W + 0.005) * extra
    tx = WW / 2 - s * cx
    ty = WH / 2 - s * cy
    tx = min(0.0, max(WW - s * W, tx))                 # keep the window inside the frame
    ty = min(0.0, max(WH - s * H, ty))
    return np.array([[s, 0, tx], [0, s, ty]], np.float32)


_mask = None


def mask():
    global _mask
    if _mask is None:
        m = np.zeros((WH, WW), np.uint8)
        cv2.rectangle(m, (RAD, 0), (WW - RAD, WH), 255, -1)
        cv2.rectangle(m, (0, RAD), (WW, WH - RAD), 255, -1)
        for cx, cy in [(RAD, RAD), (WW - RAD, RAD), (RAD, WH - RAD), (WW - RAD, WH - RAD)]:
            cv2.circle(m, (cx, cy), RAD, 255, -1, lineType=cv2.LINE_AA)
        _mask = (cv2.GaussianBlur(m, (3, 3), 0).astype(np.float32) / 255.0)[..., None]
    return _mask


def compose(fr, i, extra=1.0):
    """full 1080x1920 frame: blurred dark background of the same shot + the blind in the rounded slot window."""
    small = cv2.resize(fr, (W // 8, H // 8), interpolation=cv2.INTER_AREA)
    bg = cv2.GaussianBlur(small, (0, 0), 6)
    bg = cv2.resize(bg, (W, H), interpolation=cv2.INTER_LINEAR).astype(np.float32) * 0.42
    win = cv2.warpAffine(fr, window_affine(i, extra), (WW, WH), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)
    m = mask()
    x0, y0 = WIN[0], WIN[1]
    bg[y0:y0 + WH, x0:x0 + WW] = bg[y0:y0 + WH, x0:x0 + WW] * (1 - m) + win.astype(np.float32) * m
    return np.clip(bg, 0, 255).astype(np.uint8)


def still(i, t_off=0.3):
    """the blind itself (window crop) as RGB for thumbnails"""
    v, ss, dur, *_ = VAR[i]
    fr = frames(v, ss + t_off, 0.05)[0]
    win = cv2.warpAffine(fr, window_affine(i), (WW, WH), flags=cv2.INTER_AREA, borderMode=cv2.BORDER_REFLECT)
    return cv2.cvtColor(win, cv2.COLOR_BGR2RGB)


if __name__ == "__main__":
    from PIL import Image
    ims = []
    for i, (v, ss, *_r) in enumerate(VAR):
        fr = frames(v, ss + 0.3, 0.05)[0]
        ims.append(Image.fromarray(cv2.cvtColor(compose(fr, i), cv2.COLOR_BGR2RGB)).resize((216, 384)))
    c = Image.new("RGB", (218 * 6, 386 * 2), "white")
    for k, im in enumerate(ims):
        c.paste(im, ((k % 6) * 218, (k // 6) * 386))
    c.save(f"{D}/cs/cards.jpg", quality=85)
