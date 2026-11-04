"""Sales Reel «Derazangizga — ikki yo‘l»: compact premium captions, NARX / YANGILASH call, calm e-piano bed.

python3 tong3_compact.py           -> bed.wav, bed_nomusic.wav, ov/0000.png …
python3 tong3_compact.py prev 1,5  -> overlay previews into frames/
"""
import json
import os
import sys
from multiprocessing import Pool

from PIL import Image, ImageDraw

sys.path.insert(0, "/home/claude/reels/common")
from compact import (CREAM, DIM, GOLD, INK, LIT, MED, SEMI, SER, W, H, alpha, block, calm_bed, draw, ease,  # noqa: E402
                     grad_top, shadow, tracked, tw)

FPS = 30
D = "/home/claude/reels/tong3"
TIM = json.load(open(f"{D}/timing.json"))
CUT = json.load(open(f"{D}/cuts.json"))
TOTAL = TIM["total"]
NF = round(TOTAL * FPS)
LN = TIM["lines"]
T_END = CUT["t4"]
CTA_ON = 3.0
OUT = f"{D}/ov"
Y = 300

BLOCKS = [
    ((0.0, CUT["t1"]), block(Y, [("IMPERIAL  ·  PLISSE  ·  KOMBO", "label", 22, GOLD, -1.0),
                                 ("Derazangizga — ikki yo‘l.", "head", 76, CREAM, -1.0),
                                 ("Два пути для вашего окна", "ru", 26, DIM, 0.5)])),
    ((CUT["t1"], CUT["t2"]), block(Y, [("01  —  YANGI KOMBO", "label", 22, GOLD, CUT["t1"] + 0.05),
                                       ("Yangi kombo.", "head", 70, CREAM, CUT["t1"] + 0.1),
                                       ("Toshkentda o‘lchov va o‘rnatish bepul", "sub", 44, CREAM, CUT["l2b"]),
                                       ("o‘lchovdan keyin 3 kunda tayyor", "sub", 44, GOLD, CUT["l2c"]),
                                       ("Замер и установка бесплатно · готово за 3 дня", "ru", 24, DIM, CUT["l2c"] + 0.35)])),
    ((CUT["t2"], CUT["t3"]), block(Y, [("02  —  ESKISINI YANGILASH", "label", 22, GOLD, CUT["t2"] + 0.05),
                                       ("Eskisini yangilash.", "head", 70, CREAM, CUT["t2"] + 0.1),
                                       ("plisse va kombo matosini almashtiramiz", "sub", 44, CREAM, CUT["l3b"]),
                                       ("yoki yuvib beramiz", "sub", 48, GOLD, CUT["l3c"]),
                                       ("Заменим ткань или постираем", "ru", 24, DIM, CUT["l3c"] + 0.35)])),
    ((CUT["t3"], CUT["t4"]), block(Y, [("KAFOLAT", "label", 22, GOLD, CUT["t3"] + 0.02),
                                       ("1 yil kafolat.", "head", 80, GOLD, CUT["t3"] + 0.06),
                                       ("Гарантия 1 год", "ru", 24, DIM, CUT["t3"] + 0.3)])),
]
SCRIM = grad_top(1000, 0.72)
DARK = Image.new("RGBA", (W, H), (12, 10, 9, 172))


def hook_frame():
    L = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(L)
    d.line([(0, 959), (W, 959)], fill=GOLD, width=3)
    for txt, y in (("01  ·  YANGI", 884), ("02  ·  YANGILASH", 990)):
        f = MED(22)
        w = tw(txt, f, 0.28)
        d.rounded_rectangle((84, y, 84 + w + 40, y + 48), 24, fill=(14, 12, 10, 205), outline=GOLD, width=1)
        tracked(d, (104, y + 12), txt, f, CREAM, 0.28)
    return L


HOOK = hook_frame()


def cta_pill():
    L = Image.new("RGBA", (W, 90), (0, 0, 0, 0))
    d = ImageDraw.Draw(L)
    f1, f2 = MED(26), SEMI(26)
    parts = [("Izohga ", f1, CREAM), ("NARX", f2, GOLD), (" yoki ", f1, CREAM), ("YANGILASH", f2, GOLD), (" yozing", f1, CREAM)]
    w = sum(f.getlength(t) for t, f, _ in parts)
    x = (W - w) / 2
    d.rounded_rectangle((x - 30, 8, x + w + 30, 70), 31, fill=(14, 12, 10, 200), outline=GOLD, width=1)
    for t, f, c in parts:
        d.text((x, 22), t, font=f, fill=c)
        x += f.getlength(t)
    return L


CTA = cta_pill()


def end_card():
    L = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(L)

    def ctr(text, f, y, col, tr=0.0):
        tracked(d, ((W - tw(text, f, tr)) / 2, y), text, f, col, tr)

    ctr("IZOHGA YOZING", MED(22), 640, GOLD, 0.34)
    rows = (("NARX", "yangi jalyuzi narxlari"), ("YANGILASH", "eskisini yangilash"))
    fk, ft = SEMI(30), SER(38)
    wk_max = max(fk.getlength(k) for k, _ in rows) + 48
    wt_max = max(ft.getlength(t) for _, t in rows)
    x0 = (W - (wk_max + 26 + wt_max)) / 2
    y = 690
    for kw, txt in rows:
        wk = fk.getlength(kw) + 48
        d.rounded_rectangle((x0 + wk_max - wk, y, x0 + wk_max, y + 58), 29, fill=GOLD + (255,))
        d.text((x0 + wk_max - wk + 24, y + 11), kw, font=fk, fill=INK)
        d.text((x0 + wk_max + 26, y + 6), txt, font=ft, fill=CREAM)
        y += 84
    d.line([(W / 2 - 50, 880), (W / 2 + 50, 880)], fill=GOLD, width=2)
    ctr("IMPERIAL", SER(56), 912, CREAM, 0.22)
    ctr("PLISSE  ·  KOMBO  ·  TOSHKENT", MED(20), 986, GOLD, 0.34)
    ctr("Toshkentda o‘lchov va o‘rnatish bepul  ·  3 kunda tayyor  ·  1 yil kafolat", LIT(23), 1036, DIM)
    ctr("Напишите NARX — цены, YANGILASH — обновим старые  ·  @imperial_jalyuzi_uz", LIT(22), 1074, DIM)
    return shadow(L)


END = end_card()


def overlay(t):
    L = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if t < T_END + 0.3:
        L.alpha_composite(alpha(SCRIM, 1 - ease((t - T_END) / 0.3) if t > T_END else 1))
    if t < CUT["t1"]:
        L.alpha_composite(alpha(HOOK, 1 - ease((t - (CUT["t1"] - 0.15)) / 0.15) if t > CUT["t1"] - 0.15 else 1))
    for (t0, t1), items in BLOCKS:
        if t0 - 0.3 <= t < t1:
            draw(L, items, t, t1 - 0.03)
    if CTA_ON <= t < T_END:
        a = ease((t - CTA_ON) / 0.5) * (1 - ease((t - (T_END - 0.3)) / 0.3) if t > T_END - 0.3 else 1)
        L.alpha_composite(alpha(CTA, a), (0, 1540))
    if t >= T_END:
        L.alpha_composite(alpha(DARK, ease((t - T_END) / 0.5)))
        ca = ease((t - T_END - 0.2) / 0.6)
        L.alpha_composite(alpha(END, ca), (0, int(18 * (1 - ca))))
    return L


def job(i):
    overlay(i / FPS).save(f"{OUT}/{i:04d}.png", compress_level=1)


def make_bed(path, music):
    sections = [(0.0, CUT["t1"], [62, 66, 69, 73], 38), (CUT["t1"], CUT["t2"], [59, 62, 66, 69], 35),
                (CUT["t2"], CUT["t3"], [55, 59, 62, 66], 31), (CUT["t3"], CUT["t4"], [57, 61, 64, 69], 33),
                (CUT["t4"], TOTAL, [62, 66, 69, 76], 38)]
    accents = [CUT[k] for k in ("t1", "l2b", "l2c", "t2", "l3b", "l3c", "t3", "t4")]
    calm_bed(path, TOTAL, sections, accents, T_END, music=music, seed=21, tone="epiano", step=1.0)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(f"{D}/frames", exist_ok=True)
    if len(sys.argv) > 1 and sys.argv[1] == "prev":
        for s in sys.argv[2].split(","):
            overlay(float(s)).save(f"{D}/frames/ov_{s}.png")
        sys.exit()
    make_bed(f"{D}/bed.wav", True)
    make_bed(f"{D}/bed_nomusic.wav", False)
    for f in os.listdir(OUT):
        os.remove(f"{OUT}/{f}")
    with Pool(2) as p:
        p.map(job, range(NF), chunksize=15)
    print("frames", NF)
