"""Plisse FAQ reel — "Mijoz so'raydi, Imperial javob beradi" (1080x1920, 30 fps).

Segments (seg/S0..S6) are joined with 0.3 s cross-fades by build.sh; this script renders the
RGBA overlay sequence for the whole timeline plus the UI sound effects.
"""
import math
import os
import sys
import wave

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H, FPS = 1080, 1920, 30
DUR = [3.2, 163 / 30, 7.2, 5.6, 5.6, 5.6, 6.0]
ANS = [1.25] * 5          # answer appears this many seconds after its scene starts
_TJ = os.environ.get("FAQ_TIMING")
TIM = None
if _TJ:
    import json
    TIM = json.load(open(_TJ))
    DUR, ANS = TIM["dur"], TIM["ans"]
XF = 0.3
START = [0.0]
for d in DUR[:-1]:
    START.append(START[-1] + d - XF)
TOTAL = START[-1] + DUR[-1]
NF = math.ceil(TOTAL * FPS)
OUT = sys.argv[1] if len(sys.argv) > 1 else "/home/claude/reels/faq/ov"
os.makedirs(OUT, exist_ok=True)

FI = "/usr/share/fonts/opentype/inter/"
MONO_B = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
_F = {}


def font(name, size):
    k = (name, size)
    if k not in _F:
        _F[k] = ImageFont.truetype(name if name.startswith("/") else FI + name, size)
    return _F[k]


SEMI = lambda s: font("InterDisplay-SemiBold.otf", s)
MED = lambda s: font("InterDisplay-Medium.otf", s)
REG = lambda s: font("Inter-Regular.otf", s)
BMED = lambda s: font("Inter-Medium.otf", s)
BSEMI = lambda s: font("Inter-SemiBold.otf", s)
MONO = lambda s: font(MONO_B, s)

PAPER = (245, 241, 233)
GOLD = (214, 176, 98)
INK = (30, 28, 25)
CARD = (20, 18, 16)


def ease(x):
    x = max(0.0, min(1.0, x))
    return 1 - (1 - x) ** 3


def tracked(d, xy, text, f, fill, track=0.12):
    x, y = xy
    for ch in text:
        d.text((x, y), ch, font=f, fill=fill)
        x += f.getlength(ch) + f.size * track
    return x


def shadowed(layer, blur=10, alpha=0.55):
    a = layer.getchannel("A").filter(ImageFilter.GaussianBlur(blur))
    sh = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    sh.putalpha(a.point(lambda v: int(v * alpha)))
    out = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    out.alpha_composite(sh, (0, 6))
    out.alpha_composite(layer)
    return out


def with_alpha(layer, a):
    if a >= 1:
        return layer
    l2 = layer.copy()
    l2.putalpha(layer.getchannel("A").point(lambda v: int(v * max(0.0, a))))
    return l2


def rich(d, xy, text, f, base, hl, lh):
    """Draw multi-line text; **segments** are drawn in the highlight colour."""
    x0, y = xy
    for line in text.split("\n"):
        x = x0
        parts = line.split("**")
        for i, p in enumerate(parts):
            if not p:
                continue
            d.text((x, y), p, font=f, fill=hl if i % 2 else base)
            x += f.getlength(p)
        y += lh
    return y


def scrim():
    ys = np.arange(H, dtype=np.float32)
    top = np.clip((420 - ys) / 420, 0, 1) ** 1.4 * 0.45          # top shade for the comment card
    bot = np.clip((ys - 820) / 560, 0, 1) ** 0.9 * 0.82          # bottom shade for the answer
    a = np.maximum(top, bot)
    img = np.zeros((H, W, 4), np.uint8)
    img[..., :3] = (10, 9, 8)
    img[..., 3] = (np.repeat(a[:, None], W, 1) * 255).astype(np.uint8)
    return Image.fromarray(img, "RGBA")


SCRIM = scrim()

# ---------------------------------------------------------------- content
QA = [
    ("Deraza ochilsa, plisse\nxalaqit bermaydimi?",
     "**Yo‘q.** Plisse har bir tabaqaga\nalohida o‘rnatiladi va tabaqa\nbilan **birga ochiladi.**",
     "Нет: плиссе ставится на каждую створку\nи открывается вместе с ней."),
    ("Yechib olib yuvsa\nbo‘ladimi?",
     "**Ha, albatta.** To‘rt tomonidagi\nmahkamlagichdan yechib olib\n**yuvsa bo‘ladi.**",
     "Да: плиссе снимается с четырёх креплений\nи его можно постирать."),
    ("Yotoqxonaga qaysi\nmato yaxshi?",
     "**Dimout yoki blackout** —\nxona qorong‘i bo‘ladi. Zal va\noshxonaga — **shaffof** mato.",
     "В спальню — димаут или блэкаут,\nв зал и на кухню — прозрачные ткани."),
    ("Yorug‘likni qanday\nboshqaraman?",
     "Qo‘l bilan surasiz —\nplisse **kerakli balandlikda**\n**to‘xtaydi.**",
     "Двигаете рукой — плиссе\nостанавливается на нужной высоте."),
    ("Qancha vaqtda\ntayyor bo‘ladi?",
     "O‘lchovdan keyin **3 kunda.**\nToshkent shahrida o‘lchov,\nyetkazish va o‘rnatish — **bepul.**",
     "Через 3 дня после замера. По Ташкенту\nзамер и установка — бесплатно."),
]


def hook_layer():
    L = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(L)
    tracked(d, (86, 1052), "IMPERIAL JALYUZI  ·  PLISSE", MONO(30), GOLD, 0.14)
    rich(d, (80, 1100), "Plisse haqida\neng ko‘p beriladigan\n**5 ta savol**", SEMI(96), PAPER, GOLD, 108)
    d.text((86, 1438), "5 частых вопросов о плиссе — с ответами", font=REG(36), fill=(226, 220, 209))
    # little "answers below" chip
    t = "Javoblar bilan"
    f = BSEMI(34)
    w = f.getlength(t)
    d.rounded_rectangle((84, 1514, 84 + w + 104, 1588), 37, fill=GOLD)
    d.text((112, 1530), t, font=f, fill=INK)
    ax, ay = 84 + w + 66, 1551
    d.polygon([(ax - 12, ay - 9), (ax + 12, ay - 9), (ax, ay + 10)], fill=INK)
    return shadowed(L)


def bubble(q):
    """Instagram-style comment card with the customer question."""
    L = Image.new("RGBA", (W, 420), (0, 0, 0, 0))
    d = ImageDraw.Draw(L)
    lines = q.split("\n")
    qf = BSEMI(46)
    h = 110 + 58 * len(lines)
    d.rounded_rectangle((84, 20, W - 84, 20 + h), 34, fill=(255, 255, 255, 250))
    # avatar
    d.ellipse((116, 52, 188, 124), fill=(226, 216, 197))
    d.ellipse((140, 66, 164, 90), fill=(170, 154, 126))
    d.pieslice((126, 92, 178, 140), 180, 360, fill=(170, 154, 126))
    d.text((210, 52), "Mijoz savoli", font=BSEMI(30), fill=INK)
    d.text((210 + BSEMI(30).getlength("Mijoz savoli") + 14, 56), "· Вопрос клиента", font=REG(26), fill=(140, 132, 120))
    y = 104
    for ln in lines:
        d.text((210, y), ln, font=qf, fill=INK)
        y += 58
    # tail
    d.polygon([(150, 20 + h - 2), (190, 20 + h - 2), (156, 20 + h + 26)], fill=(255, 255, 255, 250))
    return shadowed(L, blur=14, alpha=0.4)


def answer(a, ru, extra=None, top=1098):
    L = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(L)
    lf = MONO(26)
    lw = sum(lf.getlength(c) + lf.size * 0.14 for c in "IMPERIAL JAVOBI")
    d.rounded_rectangle((80, top, 80 + lw + 36, top + 48), 24, fill=(18, 16, 14, 215))
    tracked(d, (98, top + 10), "IMPERIAL JAVOBI", lf, GOLD, 0.14)
    y = rich(d, (80, top + 68), a, SEMI(62), PAPER, GOLD, 76)
    y += 14
    for ln in ru.split("\n"):
        d.text((86, y), ln, font=REG(32), fill=(214, 206, 192))
        y += 42
    if extra:
        extra(d, y + 18)
    return shadowed(L)


def fabric_meter(d, y):
    """Q3 extra: four fabrics by thickness with a light meter."""
    items = [("Shaffof", 4), ("Yarim shaffof", 3), ("Dimout", 2), ("Blackout", 1)]
    x = 86
    f = BMED(28)
    for name, light in items:
        w = f.getlength(name) + 30 + 4 * 12
        d.rounded_rectangle((x, y, x + w + 24, y + 54), 27, fill=CARD + (190,))
        d.text((x + 18, y + 11), name, font=f, fill=PAPER)
        bx = x + 18 + f.getlength(name) + 14
        for k in range(4):
            d.rounded_rectangle((bx, y + 16, bx + 7, y + 38), 2, fill=GOLD if k < light else (95, 88, 78))
            bx += 12
        x += w + 36


Q2_TOP = 1010
HELP_Y = Q2_TOP + 68 + 3 * 76 + 14 + 2 * 42 + 22
HELP_T = TIM["help"] if TIM else 3.1        # seconds after the Q2 segment starts


def help_card():
    """Q2 extra, appears later: washing help + YUVISH keyword."""
    L = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(L)
    y = HELP_Y
    d.rounded_rectangle((84, y, 940, y + 150), 30, fill=(24, 21, 18, 232), outline=GOLD + (200,), width=2)
    # water drop icon
    cx, cy = 140, y + 75
    d.ellipse((cx - 22, cy - 6, cx + 22, cy + 38), fill=GOLD)
    d.polygon([(cx, cy - 40), (cx - 21, cy + 12), (cx + 21, cy + 12)], fill=GOLD)
    d.ellipse((cx - 9, cy + 10, cx + 1, cy + 24), fill=(24, 21, 18))
    rich(d, (196, y + 26), "Qiynalsangiz — **Imperial ustalari** yordam beradi.\nDirektga **YUVISH** yozing — qo‘llanma yuboramiz.",
         BMED(30), PAPER, GOLD, 50)
    return shadowed(L, blur=12, alpha=0.5)


EXTRAS = {2: fabric_meter}
TOPS = {1: Q2_TOP}
HOOK = hook_layer()
BUBBLES = [bubble(q) for q, _, _ in QA]
ANSWERS = [answer(a, ru, EXTRAS.get(i), TOPS.get(i, 1098)) for i, (_, a, ru) in enumerate(QA)]
HELP = help_card()

# ---------------------------------------------------------------- CTA (last segment), animated
CT = [0.75, 0.93, 1.11, 1.29]   # typing N-A-R-X
C_SEND, C_REPLY, C_DM, C_FOOT = 1.65, 1.95, 2.6, 3.15
if TIM:
    _c = TIM["cta"]
    CT = [_c["type"] + 0.16 * k for k in range(4)]
    C_SEND = CT[-1] + 0.32
    C_REPLY = C_SEND + 0.3
    C_DM = max(C_REPLY + 0.5, _c["dm"])
    C_FOOT = max(C_DM + 0.5, _c["foot"])


def cta(t):
    L = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    a0 = ease((t - 0.2) / 0.35)
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dl = ImageDraw.Draw(lay)
    tracked(dl, (86, 262), "NARXINI BILMOQCHIMISIZ?", MONO(32), GOLD, 0.14)
    y = 306
    for ln in ["Izohga", "NARX deb", "yozing"]:
        dl.text((76, y), ln, font=SEMI(140), fill=PAPER)
        y += 150
    dl.text((86, 790), "Narxlar va kalkulyator — darhol direktga", font=REG(36), fill=(214, 206, 192))
    L.alpha_composite(with_alpha(lay, a0))
    fy = 876
    fa = ease((t - 0.3) / 0.3)
    if fa > 0:
        fl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        fd = ImageDraw.Draw(fl)
        fd.rounded_rectangle((84, fy, W - 84, fy + 128), 64, fill=(255, 255, 255, 255))
        fd.ellipse((110, fy + 24, 188, fy + 102), fill=(226, 216, 197))
        fd.ellipse((136, fy + 40, 162, fy + 66), fill=(170, 154, 126))
        fd.pieslice((122, fy + 66, 176, fy + 120), 180, 360, fill=(170, 154, 126))
        n = sum(1 for tt in CT if t >= tt)
        txt = "NARX"[:n]
        tf = BSEMI(56)
        if txt:
            fd.text((214, fy + 32), txt, font=tf, fill=INK)
        else:
            fd.text((214, fy + 38), "Izoh qoldiring…", font=REG(42), fill=(160, 152, 140))
        if t < C_SEND and int(t * 2.4) % 2 == 0:
            cx = 214 + (tf.getlength(txt) + 6 if txt else 0)
            fd.rectangle((cx, fy + 32, cx + 5, fy + 96), fill=(176, 138, 62))
        pr = 1.0 - 0.12 * max(0.0, 1 - abs(t - C_SEND) / 0.12)
        bx, by = W - 84 - 72, fy + 64
        r = 45 * pr
        fd.ellipse((bx - r, by - r, bx + r, by + r), fill=GOLD if n == 4 else (222, 214, 200))
        s = 20 * pr
        fd.polygon([(bx - s * .8, by - s), (bx + s, by), (bx - s * .8, by + s), (bx - s * .4, by)], fill=INK)
        L.alpha_composite(with_alpha(fl, fa))
    ra = ease((t - C_REPLY) / 0.3)
    if ra > 0:
        rl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        rd = ImageDraw.Draw(rl)
        oy = int(30 * (1 - ra))
        bx0, by0 = 230, fy + 156 + oy
        rd.rounded_rectangle((bx0, by0, W - 150, by0 + 124), 34, fill=(44, 40, 35, 240))
        px, py = bx0 + 34, by0 + 38
        rd.polygon([(px, py + 24), (px + 50, py), (px + 34, py + 52), (px + 25, py + 33)], fill=GOLD)
        rd.text((bx0 + 110, by0 + 20), "imperial_jalyuzi_uz", font=BSEMI(30), fill=GOLD)
        rd.text((bx0 + 110, by0 + 62), "Narxlarni direktga yubordik", font=REG(36), fill=(238, 233, 224))
        L.alpha_composite(with_alpha(rl, ra))
    da = ease((t - C_DM) / 0.35)
    if da > 0:
        nl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        nd = ImageDraw.Draw(nl)
        oy = int(-40 * (1 - da))
        x0, y0 = 84, 1196 + oy
        nd.rounded_rectangle((x0, y0, W - 150, y0 + 166), 34, fill=(255, 255, 255, 250))
        nd.rounded_rectangle((x0 + 28, y0 + 30, x0 + 108, y0 + 110), 22, fill=INK)
        nd.text((x0 + 44, y0 + 44), "IJ", font=SEMI(44), fill=GOLD)
        nd.text((x0 + 134, y0 + 24), "Direkt  ·  hozir", font=BMED(28), fill=(120, 112, 100))
        nd.text((x0 + 134, y0 + 62), "Plisse: 100 000 – 200 000 so‘m/tabaqa", font=BSEMI(36), fill=INK)
        nd.text((x0 + 134, y0 + 108), "Narx kalkulyatori  ·  Bepul o‘lchov →", font=REG(31), fill=(176, 138, 62))
        L.alpha_composite(with_alpha(nl, da))
    fa2 = ease((t - C_FOOT) / 0.4)
    if fa2 > 0:
        fl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        fd = ImageDraw.Draw(fl)
        rich(fd, (86, 1400), "Yoki **deraza rasmini** direktga yuboring —\ntaxminiy narxni aytamiz.", BMED(38), PAPER, GOLD, 50)
        fd.text((86, 1512), "Напишите NARX или пришлите фото окна в директ", font=REG(30), fill=(196, 188, 174))
        L.alpha_composite(with_alpha(fl, fa2))
    return shadowed(L, blur=12, alpha=0.5)


def overlay(t):
    L = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    s6 = START[6]
    if t < s6 + 0.1:
        L.alpha_composite(with_alpha(SCRIM, 1 - ease((t - s6) / 0.3) if t > s6 else 1))
    if t < START[1] + 0.12:                                   # hook: visible from frame 0
        a = 1 - ease((t - START[1]) / 0.12) if t > START[1] else 1
        L.alpha_composite(with_alpha(HOOK, a))
    for i in range(5):
        s, e = START[i + 1], START[i + 2]
        if not (s <= t < e + 0.12):
            continue
        out = 1 - ease((t - e) / 0.12) if t > e else 1
        bp = ease((t - (s + 0.2)) / 0.28)
        if bp > 0:
            b = with_alpha(BUBBLES[i], bp * out)
            L.alpha_composite(b, (0, int(250 - 40 * (1 - bp))))
        ap = ease((t - (s + ANS[i])) / 0.35)
        if ap > 0:
            L.alpha_composite(with_alpha(ANSWERS[i], ap * out), (0, int(36 * (1 - ap))))
        if i == 1:
            hp = ease((t - (s + HELP_T)) / 0.35)
            if hp > 0:
                L.alpha_composite(with_alpha(HELP, hp * out), (0, int(30 * (1 - hp))))
    if t >= s6:
        L.alpha_composite(cta(t - s6))
    return L


def sfx(path):
    sr = 48000
    out = np.zeros(int(sr * TOTAL) + sr)

    def tone(t0, f, d, a, shape="sine", f2=None):
        n = int(sr * d)
        tt = np.arange(n) / sr
        fr = f if f2 is None else np.linspace(f, f2, n)
        ph = 2 * np.pi * np.cumsum(np.full(n, fr) if f2 is None else fr) / sr
        w = np.sin(ph) if shape == "sine" else np.sign(np.sin(ph)) * 0.5
        env = np.minimum(1, tt / 0.004) * np.exp(-tt / (d * 0.4))
        i0 = int(sr * t0)
        out[i0:i0 + n] += a * w * env

    def whoosh(t0, d=0.32, a=0.08):
        n = int(sr * d)
        noise = np.random.default_rng(int(t0 * 100)).normal(0, 1, n)
        k = np.exp(-((np.arange(n) / n - 0.45) ** 2) / 0.03)
        sm = np.convolve(noise, np.ones(24) / 24, "same")
        i0 = int(sr * t0)
        out[i0:i0 + n] += a * sm * k * 3

    for i in range(1, 7):
        whoosh(START[i] - 0.05)
    for i in range(5):
        s = START[i + 1]
        tone(s + 0.22, 1320, 0.07, 0.16)                 # comment pop
        tone(s + 0.29, 1760, 0.09, 0.12)
        tone(s + ANS[i] + 0.03, 880, 0.12, 0.07)         # answer
    tone(START[2] + HELP_T + 0.03, 1046, 0.12, 0.12)       # help card
    tone(START[2] + HELP_T + 0.12, 1568, 0.2, 0.10)
    s6 = START[6]
    for tt in CT:
        tone(s6 + tt, 2600, 0.014, 0.07, "square")
    tone(s6 + C_SEND, 500, 0.18, 0.2, f2=1400)
    tone(s6 + C_REPLY, 1320, 0.08, 0.18)
    tone(s6 + C_REPLY + 0.07, 1760, 0.12, 0.18)
    tone(s6 + C_DM, 1046, 0.16, 0.18)
    tone(s6 + C_DM + 0.12, 1568, 0.3, 0.16)
    out = np.clip(out * 1.6, -0.95, 0.95)
    pcm = (out * 32767).astype(np.int16)
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(np.repeat(pcm[:, None], 2, axis=1).tobytes())


if __name__ == "__main__":
    if len(sys.argv) > 2:
        for s in sys.argv[2].split(","):
            overlay(float(s)).save(f"{OUT}/prev_{s}.png")
        print("starts", [round(x, 3) for x in START], "total", round(TOTAL, 3))
        sys.exit()
    sfx("/home/claude/reels/faq/sfx.wav")
    for fr in range(NF):
        overlay(fr / FPS).save(f"{OUT}/{fr:04d}.png", compress_level=1)
    print("frames", NF, "total", round(TOTAL, 3))
