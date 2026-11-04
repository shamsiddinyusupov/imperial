"""Plisse «Qaysi xonaga qaysi mato?» — style B (oversized outlined numbers), 22 s, lo-fi bed."""
import os
import sys
from multiprocessing import Pool

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H, FPS = 1080, 1920, 30
TOTAL = 22.0
NF = round(TOTAL * FPS)
SECT = [3.0, 8.0, 13.0]
T_END, T_CTA = 18.0, 19.4
D = "/home/claude/reels/mato"
OUT = f"{D}/ovb"
FI = "/usr/share/fonts/opentype/inter/"
_F = {}


def F(name, size):
    k = (name, size)
    if k not in _F:
        _F[k] = ImageFont.truetype(FI + name, size)
    return _F[k]


BLACK = lambda s: F("InterDisplay-Black.otf", s)
XB = lambda s: F("InterDisplay-ExtraBold.otf", s)
SEMI = lambda s: F("InterDisplay-SemiBold.otf", s)
REG = lambda s: F("Inter-Regular.otf", s)
MED = lambda s: F("Inter-Medium.otf", s)
PAPER, GOLD, INK = (245, 241, 233), (214, 176, 98), (30, 28, 25)
SOFT, DIM = (228, 222, 212), (190, 184, 174)

FAB = [
    ("01", "YARIM SHAFFOF", "Mehmonxona uchun", "Yorug‘ va shinam, kunduzi ko‘zdan pana", "Полупрозрачная — для гостиной"),
    ("02", "DIMOUT", "Oshxona va bolalar xonasi uchun", "Quyosh nuri yumshoq tushadi", "Димаут — для кухни и детской"),
    ("03", "BLACKOUT", "Yotoqxona uchun", "Kunduzi ham qorong‘i, bemalol uxlaysiz", "Блэкаут — для спальни"),
]


def ease(x):
    x = max(0.0, min(1.0, x))
    return 1 - (1 - x) ** 3


def alpha(layer, a):
    if a >= 1:
        return layer
    l2 = layer.copy()
    l2.putalpha(layer.getchannel("A").point(lambda v: int(v * max(0, a))))
    return l2


def shadow(L, blur=10, a=0.4, dy=4):
    sh = Image.new("RGBA", L.size, (0, 0, 0, 0))
    sh.putalpha(L.getchannel("A").filter(ImageFilter.GaussianBlur(blur)).point(lambda v: int(v * a)))
    o = Image.new("RGBA", L.size, (0, 0, 0, 0))
    o.alpha_composite(sh, (0, dy))
    o.alpha_composite(L)
    return o


def tracked(d, xy, t, f, fill, tr=0.04):
    x, y = xy
    for c in t:
        d.text((x, y), c, font=f, fill=fill)
        x += f.getlength(c) + f.size * tr
    return x


def tw(t, f, tr=0.04):
    return sum(f.getlength(c) + f.size * tr for c in t)


def fit_tracked(t, mk, size, maxw=900, tr=0.04):
    while tw(t, mk(size), tr) > maxw and size > 30:
        size -= 2
    return mk(size)


def grad(y0, y1, amax):
    ys = np.arange(H, dtype=np.float32)
    a = np.clip((ys - y0) / (y1 - y0), 0, 1) ** 1.3 * amax
    img = np.zeros((H, W, 4), np.uint8)
    img[..., :3] = (8, 8, 10)
    img[..., 3] = (np.repeat(a[:, None], W, 1) * 255).astype(np.uint8)
    return Image.fromarray(img, "RGBA")


GRAD = grad(880, 1600, 0.84)


def big_num(n, size=330):
    L = Image.new("RGBA", (W, 420), (0, 0, 0, 0))
    ImageDraw.Draw(L).text((54, 0), n, font=BLACK(size), fill=(255, 255, 255, 0), stroke_width=4, stroke_fill=GOLD + (255,))
    return L


NUMS = [big_num(f[0]) for f in FAB]


def section_text(i):
    _, name, room, line, ru = FAB[i]
    L = Image.new("RGBA", (W, 400), (0, 0, 0, 0))
    d = ImageDraw.Draw(L)
    tracked(d, (84, 0), name, fit_tracked(name, XB, 80), PAPER)
    d.text((84, 132), room, font=SEMI(48), fill=GOLD)
    d.text((86, 194), line, font=REG(34), fill=SOFT)
    d.text((86, 244), ru, font=REG(28), fill=DIM)
    return shadow(L)


SECTS = [section_text(i) for i in range(3)]


def hook_text():
    L = Image.new("RGBA", (W, 420), (0, 0, 0, 0))
    d = ImageDraw.Draw(L)
    f = fit_tracked("QAYSI XONAGA", XB, 96)
    tracked(d, (84, 0), "QAYSI XONAGA", f, PAPER)
    tracked(d, (84, 112), "QAYSI MATO?", f, GOLD)
    d.text((86, 250), "Какая ткань для какой комнаты?", font=REG(34), fill=SOFT)
    return shadow(L)


HOOK = hook_text()


def triptych():
    L = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(L)
    for y in (638, 1278):
        d.rectangle((0, y, W, y + 4), fill=PAPER + (255,))
    for (n, name, room, _, _), py in zip(FAB, (300, 940, 1300)):
        box = Image.new("RGBA", (W, 300), (0, 0, 0, 0))
        bd = ImageDraw.Draw(box)
        bd.text((54, 0), n, font=BLACK(150), fill=(255, 255, 255, 0), stroke_width=3, stroke_fill=GOLD + (255,))
        tracked(bd, (290, 30), name, fit_tracked(name, XB, 56, 720), PAPER)
        bd.text((292, 104), room, font=SEMI(34), fill=GOLD)
        g = Image.new("RGBA", (W, 300), (0, 0, 0, 0))
        gd = ImageDraw.Draw(g)
        gd.rounded_rectangle((36, -6, 36 + 256 + max(tw(name, fit_tracked(name, XB, 56, 720)), SEMI(34).getlength(room)) + 60, 186), 30, fill=(10, 10, 12, 160))
        L.alpha_composite(g, (0, py))
        L.alpha_composite(shadow(box, 8, 0.5, 3), (0, py))
    return L


def cta():
    L = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(L)
    d.rounded_rectangle((48, 690, W - 48, 1080), 34, fill=(10, 10, 12, 232))
    f = fit_tracked("SIZNING XONANGIZGA", XB, 64, 900)
    x = (W - tw("SIZNING XONANGIZGA", f)) / 2
    tracked(d, (x, 724), "SIZNING XONANGIZGA", f, PAPER)
    x2 = (W - tw("QAYSI BIRI MOS?", f)) / 2
    tracked(d, (x2, 806), "QAYSI BIRI MOS?", f, GOLD)
    d.rectangle((W / 2 - 70, 900, W / 2 + 70, 908), fill=GOLD)
    t = "Izohga raqamini yozing: 1, 2 yoki 3"
    fm = MED(38)
    d.text(((W - fm.getlength(t)) / 2, 930), t, font=fm, fill=PAPER)
    t2 = "Mosini direktda tanlab beramiz · Подберём в директ"
    fr = REG(30)
    d.text(((W - fr.getlength(t2)) / 2, 994), t2, font=fr, fill=DIM)
    return shadow(L, 16, 0.5, 8)


TRI, CTA = triptych(), cta()


def overlay(t):
    L = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if t < SECT[0]:
        a = ease((t - 0.03) / 0.3) * (1 - ease((t - (SECT[0] - 0.3)) / 0.28) if t > SECT[0] - 0.3 else 1)
        L.alpha_composite(alpha(GRAD, a))
        k = min(2, int(t // 1.0))
        lt = t - k
        na = ease(lt / 0.22) * a
        L.alpha_composite(alpha(NUMS[k], na), (0, 900 + int(30 * (1 - ease(lt / 0.3)))))
        L.alpha_composite(alpha(HOOK, a), (0, 1290 + int(26 * (1 - ease(t / 0.3)))))
    for i, t0 in enumerate(SECT):
        t1 = SECT[i + 1] if i + 1 < len(SECT) else T_END
        if t0 <= t < t1:
            lt = t - t0
            a = ease(lt / 0.3) * (1 - ease((t - (t1 - 0.25)) / 0.22) if t > t1 - 0.25 else 1)
            L.alpha_composite(alpha(GRAD, a))
            L.alpha_composite(alpha(NUMS[i], a), (int(-40 * (1 - ease(lt / 0.45))), 930))
            ta = ease((lt - 0.12) / 0.3) * (a if lt > 0.4 else 1)
            L.alpha_composite(alpha(SECTS[i], ta), (0, 1300 + int(24 * (1 - ease((lt - 0.12) / 0.35)))))
            bw = int(140 * ease((lt - 0.2) / 0.4))
            if bw > 0:
                bar = Image.new("RGBA", (W, H), (0, 0, 0, 0))
                ImageDraw.Draw(bar).rectangle((84, 1400, 84 + bw, 1408), fill=GOLD + (int(255 * a),))
                L.alpha_composite(bar)
    if t >= T_END:
        a = ease((t - T_END) / 0.35)
        L.alpha_composite(alpha(TRI, a))
        if t >= T_CTA:
            c = ease((t - T_CTA) / 0.35)
            s = 0.92 + 0.08 * c
            cl = CTA.resize((int(W * s), int(H * s)), Image.LANCZOS) if s < 1 else CTA
            L.alpha_composite(alpha(cl, c), (int(W * (1 - s) / 2), int(H * (1 - s) / 2)))
    for tf in [1.0, 2.0] + SECT + [T_END]:
        if tf - 0.02 <= t < tf + 0.16:
            f = 1 - (t - tf + 0.02) / 0.18
            L.alpha_composite(Image.new("RGBA", (W, H), (255, 250, 240, int(80 * max(0, f)))))
    return L


def job(i):
    overlay(i / FPS).save(f"{OUT}/{i:04d}.png", compress_level=1)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    if len(sys.argv) > 1 and sys.argv[1] == "prev":
        for s in sys.argv[2].split(","):
            overlay(float(s)).save(f"{D}/frames/ovb_{s}.png")
        sys.exit()
    with Pool(2) as p:
        p.map(job, range(NF), chunksize=12)
    print("frames", NF)
