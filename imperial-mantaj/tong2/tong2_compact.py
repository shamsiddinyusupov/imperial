"""Awareness Reel «Hamma narsa yangi. Bittasidan tashqari.» — compact premium captions + calm bed (v2 style).

python3 tong2_compact.py           -> bed.wav, bed_nomusic.wav, ov/0000.png …
python3 tong2_compact.py prev 1,5  -> overlay previews into frames/
"""
import json
import os
import sys
from multiprocessing import Pool

from PIL import Image, ImageDraw

sys.path.insert(0, "/home/claude/reels/common")
from compact import (CREAM, DIM, GOLD, INK, LIT, MED, SEMI, SER, SERI, W, H, alpha, block, calm_bed, draw, ease,  # noqa: E402
                     grad_top, shadow, text_layer, tracked, tw)

FPS = 30
D = "/home/claude/reels/tong2"
TIM = json.load(open(f"{D}/timing.json"))
TOTAL = TIM["total"]
NF = round(TOTAL * FPS)
LN, BT, CH = TIM["lines"], TIM["beats"], TIM["chunks"]
T_END = BT[6][0]
OUT = f"{D}/ov"


def ls(i, frac=0.0):
    return LN[i]["start"] + frac * LN[i]["len"]


Y = 300
BLOCKS = [
    (BT[0], block(Y, [("IMPERIAL  ·  PLISSE  ·  KOMBO", "label", 22, GOLD, -1.0),
                      ("Hamma narsa yangi.", "head", 84, CREAM, -1.0),
                      ("Всё новое.", "ru", 26, DIM, 0.4)])),
    (BT[1], block(Y, [("ESKI JALYUZI", "label", 22, GOLD, ls(1) - 0.05),
                      ("Bittasidan tashqari.", "head", 68, CREAM, ls(1)),
                      ("derazadagi eski jalyuzi", "sub", 50, CREAM, ls(1, 0.45)),
                      ("Кроме старых жалюзи на окне", "ru", 24, DIM, ls(1, 0.6))])),
    (BT[2], block(Y, [("YANGILASH", "label", 22, GOLD, ls(2) - 0.05),
                      ("Tashlamang.", "head", 68, CREAM, ls(2)),
                      ("plisse va kombo matosini yangilaymiz", "sub", 46, GOLD, CH[2][1][0]),
                      ("Обновим ткань плиссе и комбо", "ru", 24, DIM, CH[2][1][0] + 0.4)])),
    (BT[3], block(Y, [("RANG VA USLUB", "label", 22, GOLD, ls(3) - 0.05),
                      ("Siz yoqtirgan rangda.", "head", 68, CREAM, ls(3)),
                      ("siz yoqtirgan uslubda", "sub", 50, CREAM, ls(3, 0.56)),
                      ("Ваш цвет и стиль", "ru", 24, DIM, ls(3, 0.66))])),
    (BT[4], block(Y, [("YUVISH", "label", 22, GOLD, ls(4) - 0.05),
                      ("Faqat kir bo‘lsa —", "head", 68, CREAM, ls(4)),
                      ("yechib, yuvib, qayta o‘rnatamiz", "sub", 48, CREAM, ls(4, 0.55)),
                      ("Снимем, постираем, повесим обратно", "ru", 24, DIM, ls(4, 0.62))])),
    (BT[5], block(Y, [("IMPERIAL", "label", 22, GOLD, ls(5) - 0.05),
                      ("Yangilangan xonaga —", "head", 68, CREAM, ls(5)),
                      ("yangilangan deraza", "sub", 54, GOLD, ls(5, 0.55)),
                      ("Новой комнате — новое окно", "ru", 24, DIM, ls(5, 0.7))])),
]
SCRIM = grad_top(1000, 0.72)
DARK = Image.new("RGBA", (W, H), (12, 10, 9, 170))


def end_card():
    L = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(L)

    def ctr(text, f, y, col, tr=0.0):
        tracked(d, ((W - tw(text, f, tr)) / 2, y), text, f, col, tr)

    ctr("ESKI JALYUZINGIZ BORMI?", MED(22), 690, GOLD, 0.32)
    ctr("Rasmini direktga yuboring", SER(64), 730, CREAM)
    ctr("ko‘rib, aytib beramiz", SERI(44), 812, DIM)
    d.line([(W / 2 - 50, 900), (W / 2 + 50, 900)], fill=GOLD, width=2)
    fk, ft = SEMI(30), SER(36)
    kw, rest = "YANGILASH", "deb izohga yozing"
    wk, wr = fk.getlength(kw) + 48, ft.getlength(rest)
    x = (W - (wk + 18 + wr)) / 2
    d.rounded_rectangle((x, 932, x + wk, 990), 29, fill=GOLD + (255,))
    d.text((x + 24, 943), kw, font=fk, fill=INK)
    d.text((x + wk + 18, 938), rest, font=ft, fill=CREAM)
    ctr("IMPERIAL", SER(56), 1040, CREAM, 0.22)
    ctr("PLISSE  ·  KOMBO  ·  TOSHKENT", MED(20), 1114, GOLD, 0.34)
    ctr("Пришлите фото в директ или напишите YANGILASH", LIT(23), 1166, DIM)
    ctr("Ta’mir qilayotgan yaqiningizga ham yuboring  ·  @imperial_jalyuzi_uz", LIT(22), 1204, DIM)
    return shadow(L)


END = end_card()


def overlay(t):
    L = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if t < T_END + 0.3:
        L.alpha_composite(alpha(SCRIM, 1 - ease((t - T_END) / 0.3) if t > T_END else 1))
    for (t0, t1), items in BLOCKS:
        if t0 - 0.3 <= t < t1:
            draw(L, items, t, t1 - 0.03)
    if t >= T_END:
        L.alpha_composite(alpha(DARK, ease((t - T_END) / 0.6)))
        ca = ease((t - T_END - 0.25) / 0.7)
        L.alpha_composite(alpha(END, ca), (0, int(18 * (1 - ca))))
    return L


def job(i):
    overlay(i / FPS).save(f"{OUT}/{i:04d}.png", compress_level=1)


def make_bed(path, music):
    c_mid = CH[2][1][0]
    kombo_on = CH[2][1][0] + 0.27 * (CH[2][1][1] - CH[2][1][0])
    m0, m1 = BT[3]
    sections = [(0.0, BT[1][0], [57, 60, 64, 71], 33), (BT[1][0], c_mid, [57, 60, 64, 69], 33),
                (c_mid, BT[3][0], [60, 64, 67, 71], 36), (BT[3][0], BT[4][0], [65, 69, 72, 76], 41),
                (BT[4][0], BT[5][0], [62, 65, 69, 72], 38), (BT[5][0], BT[6][0], [67, 71, 74, 78], 43),
                (BT[6][0], TOTAL, [60, 64, 67, 71], 36)]
    accents = [kombo_on, CH[2][2][0]] + [m0 + k * (m1 - m0) / 6 for k in range(1, 6)] + [BT[4][0] + 0.2]
    calm_bed(path, TOTAL, sections, accents, T_END, music=music, seed=11, tone="piano", step=0.84)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
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
