"""Demo of one learned technique — the 'depth' effect: the title lives on the tulle plane, BEHIND the barxat panels.

Photo (owner's, dikey with brown barxat sides and white patterned tulle) -> mask of the barxat panels (colour)
-> slow push-in on the photo; the word slides in from behind the left panel, the panels stay in front.
Text is deep cocoa printed onto the tulle (keeps a little of the pattern), colours from the photo itself.
"""
import subprocess
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, "/home/claude/reels/dikey_style")
sys.path.insert(0, "/home/claude/reels/common")
import grade  # noqa: E402
from faqat_qarang import DID, ITA, LAB, RU, text_img  # noqa: E402

D = "/home/claude/reels/incoming"
SRC = "/home/claude/reels/dikey_style/new/photo1.jpg"
W, H, FPS, T = 1080, 1920, 30, 9.0

img = cv2.imread(SRC)
h, w = img.shape[:2]
base = max(W / w, H / h)

# --- barxat mask (brown, saturated, not bright) in photo coordinates
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
Hh, S, V = hsv[..., 0].astype(int), hsv[..., 1].astype(int), hsv[..., 2].astype(int)
m = ((Hh >= 5) & (Hh <= 24) & (S >= 70) & (V <= 175)).astype(np.uint8) * 255
m[: int(h * 0.12)] = 0                                   # ceiling / rail
m[int(h * 0.80):] = 0                                    # carpet (has brown patterns) — text never goes there
m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((25, 25), np.uint8))
m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((9, 9), np.uint8))
# keep only big vertical blobs (the panels)
n, lab, st, _ = cv2.connectedComponentsWithStats(m)
keep = np.zeros_like(m)
for i in range(1, n):
    if st[i, cv2.CC_STAT_HEIGHT] > h * 0.3:
        keep[lab == i] = 255
mask = cv2.GaussianBlur(keep, (0, 0), 1.6).astype(np.float32) / 255
cv2.imwrite(f"{D}/mask.png", (mask * 255).astype(np.uint8))

xs = np.arange(W, dtype=np.float32)
CLIP = (np.clip((xs - 250) / 40, 0, 1) * np.clip((900 - xs) / 40, 0, 1))[None, :, None]   # tulle plane only
COCOA = (52, 34, 20)          # from the barxat, deepened for text
CARAMEL = (150, 105, 62)

word = text_img("DIKEY", DID(168), COCOA + (255,), 0.07)
lab = text_img("IMPERIAL  ·  JALYUZI", LAB(20), CARAMEL + (255,), 0.45)
sub = text_img("oq tyul va jigarrang barxat", ITA(40), COCOA + (255,))
ru = text_img("белый тюль и коричневый бархат", RU(25), CARAMEL + (255,))


def ease(x):
    x = min(1.0, max(0.0, x))
    return 1 - (1 - x) ** 3


def text_layer(t):
    L = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    cx = 586                                              # centre of the tulle between the panels
    p = ease((t - 0.5) / 1.9)
    x = cx - word.width / 2 - 520 * (1 - p)               # slides in from behind the left panel
    L.alpha_composite(word, (int(x), 720))
    a = ease((t - 2.2) / 0.7)
    for im, y in ((lab, 690), (sub, 935), (ru, 992)):
        if a > 0:
            l2 = im.copy()
            l2.putalpha(l2.getchannel("A").point(lambda v: int(v * a)))
            L.alpha_composite(l2, (int(cx - im.width / 2), y + int(10 * (1 - a))))
    return np.asarray(L, dtype=np.float32) / 255


def frame(t):
    u = t / T
    s = base * (1.0 + 0.07 * u)                           # slow push-in
    cx, cy = w / 2, h * 0.44
    M = np.array([[s, 0, W / 2 - s * cx], [0, s, H * 0.46 - s * cy]])
    bg = cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT).astype(np.float32) / 255
    pm = cv2.warpAffine(mask, M, (W, H), flags=cv2.INTER_LINEAR)[..., None]
    tl = text_layer(t)
    ta = tl[..., 3:4] * (1 - pm) * CLIP                   # the panels hide the text; it lives only on the tulle plane
    tc = tl[..., :3][..., ::-1]                           # RGBA(PIL) -> BGR
    printed = tc * 0.82 + bg * tc * 0.18 / np.maximum(tc.mean(2, keepdims=True), 0.05) * 0.0 + bg * 0.18 * tc / 0.25
    printed = np.clip(tc * 0.8 + bg * 0.2 * (tc / max(tc.max(), 1e-3)), 0, 1)
    out = bg * (1 - ta * 0.94) + printed * ta * 0.94
    return (np.clip(out, 0, 1) * 255).astype(np.uint8)


if __name__ == "__main__":
    wb = f"{D}/wb.jpg"
    cv2.imwrite(wb, cv2.resize(img, (round(w * base), round(h * base)), interpolation=cv2.INTER_AREA))
    vf = grade.vf(grade.gains(wb)) + ",unsharp=5:5:0.3"
    enc = subprocess.Popen(["ffmpeg", "-nostdin", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}",
                            "-r", str(FPS), "-i", "-", "-i", f"{D}/bed.wav", "-vf", vf,
                            "-af", f"afade=t=in:d=0.5,afade=t=out:st={T - 1.2}:d=1.2,loudnorm=I=-16:TP=-1.5",
                            "-t", str(T), "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-pix_fmt", "yuv420p",
                            "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", f"{D}/demo_chuqurlik.mp4"],
                           stdin=subprocess.PIPE)
    for i in range(int(T * FPS)):
        enc.stdin.write(frame(i / FPS).tobytes())
    enc.stdin.close()
    enc.wait()
    print("ok")
