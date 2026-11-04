"""Three text layouts for the depth demo (same picture, same effect), for the owner to choose.

A — Markaz: clear hierarchy, everything fully visible on the tulle, generous spacing
B — Vertikal: letters stacked down the tulle like the slats themselves
C — Jurnal: big word high (edges tucked behind the panels), information at the bottom of the tulle
python3 layouts.py board            -> layouts_board.jpg
python3 layouts.py render A|B|C     -> demo_chuqurlik_<X>.mp4
"""
import subprocess
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw

sys.argv_saved = sys.argv
sys.path.insert(0, "/home/claude/reels/incoming")
import demo_depth as d  # noqa: E402
from demo_depth import DID, ITA, LAB, RU, text_img  # noqa: E402

W, H = 1080, 1920
CX = 586                       # tulle centre at the final framing
COCOA = (52, 34, 20)
COCOA2 = (92, 66, 44)          # softer cocoa for secondary lines (reads on white tulle)
CAR = (128, 88, 50)            # darker caramel: legible on the tulle


def fade(im, a):
    l2 = im.copy()
    l2.putalpha(l2.getchannel("A").point(lambda v: int(v * max(0.0, min(1.0, a)))))
    return l2


def place(L, im, cx, y, a=1.0, dx=0, dy=0):
    if a > 0:
        L.alpha_composite(fade(im, a), (int(cx - im.width / 2 + dx), int(y + dy)))


def hair(L, cx, y, wpx, a, col=CAR):
    if a > 0:
        ImageDraw.Draw(L).line([(cx - wpx / 2 * a, y), (cx + wpx / 2 * a, y)], fill=col + (int(255 * a),), width=2)


e = d.ease

# ---------------------------------------------------------------- A
A_lab = text_img("IMPERIAL  ·  JALYUZI", LAB(19), CAR + (255,), 0.5)
A_word = text_img("DIKEY", DID(124), COCOA + (255,), 0.09)
A_sub = text_img("oq tyul va jigarrang barxat", ITA(38), COCOA + (255,))
A_ru = text_img("белый тюль и коричневый бархат", RU(24), COCOA2 + (255,))


def layer_A(t):
    L = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    p = e((t - 0.5) / 1.9)
    place(L, A_word, CX, 640, 1, dx=-520 * (1 - p))
    a = e((t - 2.0) / 0.7)
    place(L, A_lab, CX, 575, a, dy=8 * (1 - a))
    hair(L, CX, 850, 70, e((t - 2.3) / 0.6))
    a = e((t - 2.5) / 0.7)
    place(L, A_sub, CX, 866, a, dy=8 * (1 - a))
    a = e((t - 2.8) / 0.7)
    place(L, A_ru, CX, 932, a)
    return np.asarray(L, dtype=np.float32) / 255


# ---------------------------------------------------------------- B
B_letters = [text_img(c, DID(150), COCOA + (255,)) for c in "DIKEY"]
B_lab = text_img("IMPERIAL  ·  JALYUZI", LAB(19), CAR + (255,), 0.5)
B_sub = text_img("oq tyul va jigarrang barxat", ITA(36), COCOA + (255,))
B_ru = text_img("белый тюль и коричневый бархат", RU(23), COCOA2 + (255,))


def layer_B(t):
    L = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    y = 470
    for k, im in enumerate(B_letters):
        p = e((t - 0.4 - 0.22 * k) / 1.3)
        place(L, im, CX, y, 1, dx=-480 * (1 - p))
        y += 152
    a = e((t - 2.2) / 0.7)
    place(L, B_lab, CX, 420, a, dy=8 * (1 - a))
    hair(L, CX, 1300, 70, e((t - 2.4) / 0.6))
    a = e((t - 2.6) / 0.7)
    place(L, B_sub, CX, 1316, a, dy=8 * (1 - a))
    a = e((t - 2.9) / 0.7)
    place(L, B_ru, CX, 1378, a)
    return np.asarray(L, dtype=np.float32) / 255


# ---------------------------------------------------------------- C
C_word = text_img("DIKEY", DID(176), COCOA + (255,), 0.07)
C_lab = text_img("IMPERIAL  ·  JALYUZI", LAB(19), CAR + (255,), 0.5)
C_sub = text_img("oq tyul va jigarrang barxat", ITA(40), COCOA + (255,))
C_ru = text_img("белый тюль и коричневый бархат", RU(24), COCOA2 + (255,))


def layer_C(t):
    L = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    p = e((t - 0.5) / 1.9)
    place(L, C_word, CX, 470, 1, dx=-520 * (1 - p))
    a = e((t - 2.0) / 0.7)
    place(L, C_lab, CX, 420, a, dy=8 * (1 - a))
    hair(L, CX, 1255, 70, e((t - 2.4) / 0.6))
    a = e((t - 2.6) / 0.7)
    place(L, C_sub, CX, 1270, a, dy=8 * (1 - a))
    a = e((t - 2.9) / 0.7)
    place(L, C_ru, CX, 1333, a)
    return np.asarray(L, dtype=np.float32) / 255


LAYERS = {"A": layer_A, "B": layer_B, "C": layer_C}
NAMES = {"A": "A — Markaz", "B": "B — Vertikal", "C": "C — Jurnal"}


def still(x, t=5.0):
    d.text_layer = LAYERS[x]
    return d.frame(t)


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "board":
        from compact import MED
        tiles = []
        for x in "ABC":
            fr = Image.fromarray(cv2.cvtColor(still(x), cv2.COLOR_BGR2RGB)).resize((540, 960), Image.LANCZOS)
            tiles.append(fr)
        B = Image.new("RGB", (540 * 3 + 40, 1030), (24, 18, 13))
        dr = ImageDraw.Draw(B)
        for i, (x, im) in enumerate(zip("ABC", tiles)):
            B.paste(im, (10 + i * 550, 60))
            dr.text((20 + i * 550, 14), NAMES[x], font=MED(30), fill=(214, 178, 128))
        B.save("/home/claude/reels/incoming/layouts_board.jpg", quality=92)
    else:
        x = sys.argv[2]
        d.text_layer = LAYERS[x]
        D, T, FPS = d.D, d.T, d.FPS
        import grade
        wb = f"{D}/wb.jpg"
        vf = grade.vf(grade.gains(wb)) + ",unsharp=5:5:0.3"
        enc = subprocess.Popen(["ffmpeg", "-nostdin", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}",
                                "-r", str(FPS), "-i", "-", "-i", f"{D}/bed.wav", "-vf", vf,
                                "-af", f"afade=t=in:d=0.5,afade=t=out:st={T - 1.2}:d=1.2,loudnorm=I=-16:TP=-1.5",
                                "-t", str(T), "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-pix_fmt", "yuv420p",
                                "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", f"{D}/demo_chuqurlik_{x}.mp4"],
                               stdin=subprocess.PIPE)
        for i in range(int(T * FPS)):
            enc.stdin.write(d.frame(i / FPS).tobytes())
        enc.stdin.close()
        enc.wait()
        print("ok", x)
