"""Moskit setka «Chivinning kundaligi» Reel: animated mosquito + overlays (900 frames) + quirky 120 BPM music, 30 s."""
import math
import os
import sys
import wave
from multiprocessing import Pool

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H, FPS = 1080, 1920, 30
TOTAL = 30.0
NF = round(TOTAL * FPS)
SECT = [3.0, 7.5, 12.0, 16.5, 21.0]
SLEN = 4.5
T_END = 25.5
T_CARD = 27.0
D = "/home/claude/reels/setka"
OUT = f"{D}/ov"
FI = "/usr/share/fonts/opentype/inter/"
MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
_F = {}


def F(name, size):
    k = (name, size)
    if k not in _F:
        _F[k] = ImageFont.truetype(name if name.startswith("/") else FI + name, size)
    return _F[k]


BLACK = lambda s: F("InterDisplay-Black.otf", s)
XB = lambda s: F("InterDisplay-ExtraBold.otf", s)
SEMI = lambda s: F("InterDisplay-SemiBold.otf", s)
MED = lambda s: F("Inter-Medium.otf", s)
REG = lambda s: F("Inter-Regular.otf", s)
ITAL = lambda s: F("Inter-MediumItalic.otf", s)
MON = lambda s: F(MONO, s)
PAPER, GOLD, INK = (245, 241, 233), (214, 176, 98), (30, 28, 25)
SOFT, DIM = (228, 222, 212), (190, 184, 174)

SECTIONS = [
    ("01", "SURMA SETKA", "Eshik uchun, yonga suriladi", "Eshik ochiq... lekin kira olmadim!", "Дверь открыта… а не пролететь!"),
    ("02", "SURMA SETKA", "Deraza uchun, tepadan pastga", "Deraza ochiq... yana setka!", "Окно открыто… опять сетка!"),
    ("03", "PETLYALI SETKA", "Eshikdek ochiladi", "Odamlarga ochiladi, menga — yo‘q.", "Людям открывается, мне — нет."),
    ("04", "STANDART SETKA", "4 tomondan qotiriladi", "To‘rt tomoni mahkam. Bitta teshik ham yo‘q!", "С 4 сторон — ни одной щёлки!"),
    ("05", "UNI SETKA", "Toza havo, chivinsiz", "Uni setka... Umid qolmadi.", "Сетка Uni… надежды нет."),
]
END_QUOTE = ("Bu shaharda Imperial setkalari ko‘payib ketibdi...", "В этом городе слишком много сеток Imperial…")


def ease(x):
    x = max(0.0, min(1.0, x))
    return 1 - (1 - x) ** 3


def ease_io(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def alpha(layer, a):
    if a >= 1:
        return layer
    l2 = layer.copy()
    l2.putalpha(layer.getchannel("A").point(lambda v: int(v * max(0, a))))
    return l2


def shadow(L, blur=10, a=0.45, dy=5):
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


def fitf(t, mk, size, maxw=900, tr=0.0):
    while tw(t, mk(size), tr) > maxw and size > 26:
        size -= 2
    return mk(size)


def grad(y0, y1, amax):
    ys = np.arange(H, dtype=np.float32)
    a = np.clip((ys - y0) / (y1 - y0), 0, 1) ** 1.3 * amax
    img = np.zeros((H, W, 4), np.uint8)
    img[..., :3] = (8, 8, 10)
    img[..., 3] = (np.repeat(a[:, None], W, 1) * 255).astype(np.uint8)
    return Image.fromarray(img, "RGBA")


GRAD = grad(900, 1620, 0.86)


# ---------------------------------------------------------------- mosquito sprite
def mosquito(flap, size=150, dizzy=False):
    S = size
    im = Image.new("RGBA", (S * 3, S * 3), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    cx, cy = S * 1.5, S * 1.5
    ink = (36, 30, 28, 255)
    # legs (long, thin, bent)
    for k, (dx, dy) in enumerate(((-0.55, 0.55), (-0.15, 0.7), (0.3, 0.68), (-0.6, 0.35), (0.1, 0.5), (0.5, 0.45))):
        x1, y1 = cx + dx * S * 0.35, cy + S * 0.12
        x2, y2 = cx + dx * S * 1.2, cy + dy * S * 1.15
        x3, y3 = x2 + dx * S * 0.35, y2 + S * 0.35
        d.line([(x1, y1), (x2, y2), (x3, y3)], fill=ink, width=max(2, S // 50), joint="curve")
    # abdomen (striped), thorax, head
    d.ellipse((cx - S * 0.95, cy - S * 0.07, cx - S * 0.1, cy + S * 0.2), fill=(70, 58, 52, 255))
    for k in range(4):
        x = cx - S * 0.85 + k * S * 0.18
        d.line([(x, cy - S * 0.05), (x + S * 0.04, cy + S * 0.18)], fill=(150, 130, 110, 255), width=max(2, S // 40))
    d.ellipse((cx - S * 0.2, cy - S * 0.16, cx + S * 0.22, cy + S * 0.18), fill=ink)
    d.ellipse((cx + S * 0.16, cy - S * 0.13, cx + S * 0.42, cy + S * 0.11), fill=ink)
    eye = (cx + S * 0.33, cy - S * 0.04)
    if dizzy:
        for r in (S * 0.06, S * 0.035):
            d.arc((eye[0] - r, eye[1] - r, eye[0] + r, eye[1] + r), 0, 300, fill=(255, 255, 255, 255), width=2)
    else:
        d.ellipse((eye[0] - S * 0.05, eye[1] - S * 0.05, eye[0] + S * 0.05, eye[1] + S * 0.05), fill=(255, 255, 255, 255))
        d.ellipse((eye[0] - S * 0.02, eye[1] - S * 0.025, eye[0] + S * 0.03, eye[1] + S * 0.025), fill=ink)
    # proboscis
    d.line([(cx + S * 0.4, cy + S * 0.02), (cx + S * 0.95, cy + S * 0.2)], fill=ink, width=max(2, S // 45))
    # antennae
    d.line([(cx + S * 0.36, cy - S * 0.1), (cx + S * 0.6, cy - S * 0.34)], fill=ink, width=2)
    # wings (flapping): two slim wings hinged at the thorax
    wing = Image.new("RGBA", im.size, (0, 0, 0, 0))
    for k, base in enumerate((62, 38)):
        a0 = base + 28 * flap * (1 if k == 0 else 0.7)
        w = Image.new("RGBA", (int(S * 0.9), int(S * 0.26)), (0, 0, 0, 0))
        ImageDraw.Draw(w).ellipse((0, 0, w.width - 1, w.height - 1), fill=(225, 235, 245, 115), outline=(255, 255, 255, 210), width=2)
        big = Image.new("RGBA", (w.width * 2, w.width * 2), (0, 0, 0, 0))
        big.alpha_composite(w, (w.width, w.width - w.height // 2))  # hinge at the wing root
        big = big.rotate(180 - a0, resample=Image.BICUBIC)
        wing.alpha_composite(big, (int(cx - big.width / 2), int(cy - S * 0.08 - big.height / 2)))
    out = Image.new("RGBA", im.size, (0, 0, 0, 0))
    out.alpha_composite(wing)
    out.alpha_composite(im)
    return out.filter(ImageFilter.SMOOTH)


SPR = [mosquito(f) for f in (0.0, 1.0)]
SPR_DIZZY = [mosquito(f, dizzy=True) for f in (0.0, 1.0)]


def paste_sprite(L, spr, x, y, s=1.0, sx=1.0, sy=1.0, rot=0.0, a=1.0):
    w, h = spr.size
    im = spr.resize((max(1, int(w * s * sx)), max(1, int(h * s * sy))), Image.BICUBIC)
    if rot:
        im = im.rotate(rot, expand=True, resample=Image.BICUBIC)
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
    sh.putalpha(im.getchannel("A").filter(ImageFilter.GaussianBlur(6)).point(lambda v: int(v * 0.35)))
    L.alpha_composite(alpha(sh, a), (int(x - im.width / 2 + 4), int(y - im.height / 2 + 10)))
    L.alpha_composite(alpha(im, a), (int(x - im.width / 2), int(y - im.height / 2)))


def star(d, x, y, r, col):
    pts = []
    for k in range(10):
        rr = r if k % 2 == 0 else r * 0.45
        a = -math.pi / 2 + k * math.pi / 5
        pts.append((x + rr * math.cos(a), y + rr * math.sin(a)))
    d.polygon(pts, fill=col)


# ---------------------------------------------------------------- text layers
def wrap(text, f, maxw):
    words, lines, cur = text.split(), [], ""
    for w_ in words:
        t = (cur + " " + w_).strip()
        if f.getlength(t) <= maxw or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = w_
    lines.append(cur)
    return lines


def bubble(uz, ru, maxw=760):
    fu, fr = ITAL(46), REG(28)
    lines = wrap("\u00ab" + uz + "\u00bb", fu, maxw - 64)
    w = int(max(max(fu.getlength(l) for l in lines), fr.getlength(ru)) + 64)
    h = 40 + 58 * len(lines) + 44
    B = Image.new("RGBA", (w + 20, h + 46), (0, 0, 0, 0))
    d = ImageDraw.Draw(B)
    d.rounded_rectangle((0, 0, w, h), 34, fill=(255, 255, 255, 246))
    d.polygon([(w - 150, h - 2), (w - 100, h - 2), (w - 80, h + 40)], fill=(255, 255, 255, 246))
    for k, l in enumerate(lines):
        d.text((32, 24 + 58 * k), l, font=fu, fill=INK)
    d.text((34, 30 + 58 * len(lines)), ru, font=fr, fill=(110, 104, 96))
    return shadow(B, 14, 0.35, 8)


BUBBLES = [bubble(s[3], s[4]) for s in SECTIONS]
END_BUBBLE = bubble(*END_QUOTE)


def big_num(n, size=300):
    L = Image.new("RGBA", (W, 380), (0, 0, 0, 0))
    ImageDraw.Draw(L).text((54, 0), n, font=BLACK(size), fill=(255, 255, 255, 0), stroke_width=4, stroke_fill=GOLD + (255,))
    return L


NUMS = [big_num(s[0]) for s in SECTIONS]


def lower(i):
    _, name, desc, _, _ = SECTIONS[i]
    L = Image.new("RGBA", (W, 300), (0, 0, 0, 0))
    d = ImageDraw.Draw(L)
    tracked(d, (84, 0), name, fitf(name, XB, 80, 900, 0.04), PAPER)
    d.text((84, 104), desc, font=SEMI(46), fill=GOLD)
    return shadow(L)


LOWERS = [lower(i) for i in range(5)]


def hook_text():
    L = Image.new("RGBA", (W, 420), (0, 0, 0, 0))
    d = ImageDraw.Draw(L)
    tracked(d, (86, 0), "IMPERIAL JALYUZI · MOSKIT SETKALAR", MON(28), GOLD, 0.12)
    f = fitf("CHIVINNING", XB, 120, 900, 0.04)
    tracked(d, (80, 44), "CHIVINNING", f, PAPER)
    tracked(d, (80, 44 + int(f.size * 1.02)), "KUNDALIGI", f, GOLD)
    d.text((86, 44 + int(f.size * 2.16)), "Bir kecha, besh xonadon · Дневник комара", font=REG(34), fill=SOFT)
    return shadow(L)


HOOK = hook_text()


def card():
    L = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(L)
    tracked(d, (86, 1040), "IMPERIAL JALYUZI", MON(30), GOLD, 0.12)
    f = fitf("MOSKIT SETKALAR", XB, 96, 920, 0.04)
    tracked(d, (80, 1084), "MOSKIT SETKALAR", f, PAPER)
    d.rectangle((84, 1084 + f.size + 24, 224, 1084 + f.size + 32), fill=GOLD)
    y = 1084 + f.size + 58
    d.text((84, y), "Surma · Petlyali · Standart · Uni", font=SEMI(48), fill=GOLD)
    d.text((86, y + 66), "Toshkent shahrida o‘lchov va o‘rnatish bepul · 1 yil kafolat", font=fitf("Toshkent shahrida o‘lchov va o‘rnatish bepul · 1 yil kafolat", MED, 34, 900), fill=SOFT)
    t = "Derazangizga mosini direktda tanlab beramiz"
    fb = fitf(t, SEMI, 40, 860)
    yb = y + 134
    d.rounded_rectangle((80, yb, 80 + fb.getlength(t) + 60, yb + 78), 39, fill=GOLD)
    d.text((110, yb + 15), t, font=fb, fill=INK)
    d.text((86, yb + 96), "Подберём сетку в директ · @imperial_jalyuzi_uz", font=REG(30), fill=DIM)
    return shadow(L, 12, 0.5)


CARD = card()


# ---------------------------------------------------------------- choreography
HOME = (800, 640)
HIT = (520, 960)


def section_mosquito(lt, t):
    """Mosquito position/scale for local time lt inside a section; returns (x, y, s, sx, sy, rot, dizzy)."""
    bob = math.sin(t * 7) * 14
    if lt < 1.0:  # enters and hovers
        k = ease(lt / 0.6)
        return (HOME[0] + 340 * (1 - k), HOME[1] + bob + 120 * (1 - k), 1.0, 1, 1, -8 + 6 * math.sin(t * 5), False)
    if lt < 1.5:  # dives at the net
        k = ease_io((lt - 1.0) / 0.5)
        return (HOME[0] + (HIT[0] - HOME[0]) * k, HOME[1] + (HIT[1] - HOME[1]) * k, 1 + 0.9 * k, 1, 1, -8 - 20 * k, False)
    if lt < 1.7:  # squash on the mesh
        k = (lt - 1.5) / 0.2
        sq = math.sin(k * math.pi)
        return (HIT[0], HIT[1], 1.9, 1 + 0.25 * sq, 1 - 0.3 * sq, -28, True)
    if lt < 2.3:  # knocked back
        k = ease((lt - 1.7) / 0.6)
        wob = math.sin((lt - 1.7) * 30) * 18 * (1 - k)
        return (HIT[0] + (HOME[0] - HIT[0]) * k + wob, HIT[1] + (HOME[1] - HIT[1]) * k, 1.9 - 0.9 * k, 1, 1, -28 + 40 * k, True)
    return (HOME[0] + math.sin(t * 2.3) * 10, HOME[1] + bob, 1.0, 1, 1, 10 + 6 * math.sin(t * 4), lt < 3.3)


def overlay(t):
    L = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    flap = int(t * FPS) % 2
    d = ImageDraw.Draw(L)
    if t < SECT[0]:  # hook: the mosquito flies in on a wavy path
        a = ease((t - 0.03) / 0.3) * (1 - ease((t - (SECT[0] - 0.3)) / 0.28) if t > SECT[0] - 0.3 else 1)
        L.alpha_composite(alpha(GRAD, a))
        L.alpha_composite(alpha(HOOK, a), (0, 1160 + int(26 * (1 - ease(t / 0.3)))))
        k = min(1, t / 2.6)
        x = -120 + (HOME[0] + 120) * ease_io(k)
        y = 820 - 220 * k + math.sin(t * 6) * 60
        paste_sprite(L, SPR[flap], x, y, 0.9 + 0.1 * k, rot=-10 + 14 * math.sin(t * 5))
    for i, t0 in enumerate(SECT):
        if t0 <= t < t0 + SLEN:
            lt = t - t0
            a = ease(lt / 0.3) * (1 - ease((lt - (SLEN - 0.25)) / 0.22) if lt > SLEN - 0.25 else 1)
            L.alpha_composite(alpha(GRAD, a))
            L.alpha_composite(alpha(NUMS[i], a), (int(-40 * (1 - ease(lt / 0.45))), 1000))
            L.alpha_composite(alpha(LOWERS[i], ease((lt - 0.12) / 0.3) * a), (0, 1330 + int(22 * (1 - ease((lt - 0.12) / 0.35)))))
            x, y, s, sx, sy, rot, dz = section_mosquito(lt, t)
            if 1.5 <= lt < 2.1:  # ripple on the mesh at the hit point
                k = (lt - 1.5) / 0.6
                r = 30 + 160 * k
                rp = Image.new("RGBA", (W, H), (0, 0, 0, 0))
                ImageDraw.Draw(rp).ellipse((HIT[0] - r, HIT[1] - r * 0.7, HIT[0] + r, HIT[1] + r * 0.7), outline=(255, 255, 255, int(200 * (1 - k))), width=5)
                L.alpha_composite(rp)
            paste_sprite(L, (SPR_DIZZY if dz else SPR)[flap], x, y, s, sx, sy, rot, a)
            if 1.7 <= lt < 3.3:  # dizzy stars
                for k in range(3):
                    ang = t * 6 + k * 2.09
                    star(d, x + 70 * math.cos(ang), y - 70 + 22 * math.sin(ang), 16, GOLD + (255,))
            if lt >= 2.15:
                b = BUBBLES[i]
                ba = ease((lt - 2.15) / 0.25) * a
                s2 = 0.85 + 0.15 * ease((lt - 2.15) / 0.3)
                bb = b.resize((int(b.width * s2), int(b.height * s2)), Image.LANCZOS)
                L.alpha_composite(alpha(bb, ba), (int(min(W - bb.width - 40, HOME[0] + 60 - bb.width * 0.88)), int(HOME[1] - 120 - bb.height)))
    if t >= T_END:
        lt = t - T_END
        ca = ease((lt - (T_CARD - T_END)) / 0.4) if t >= T_CARD else 0
        L.alpha_composite(alpha(GRAD, max(ca, 0.5)))
        k = ease(lt / 0.8)
        x = HOME[0] - 80 * k + math.sin(t * 2) * 10
        y = HOME[1] + 40 * k + math.sin(t * 6) * 10
        paste_sprite(L, SPR[flap], x, y, 1.0, rot=18)
        b = END_BUBBLE
        ba = ease((lt - 0.3) / 0.3)
        L.alpha_composite(alpha(b, ba), (int(min(W - b.width - 40, x + 60 - b.width * 0.88)), int(y - 120 - b.height)))
        if ca > 0:
            L.alpha_composite(alpha(CARD, ca), (0, int(40 * (1 - ca))))
    for tf in SECT + [T_END]:
        if tf - 0.02 <= t < tf + 0.14:
            f = 1 - (t - tf + 0.02) / 0.16
            L.alpha_composite(Image.new("RGBA", (W, H), (255, 250, 240, int(70 * max(0, f)))))
    return L


def job(i):
    overlay(i / FPS).save(f"{OUT}/{i:04d}.png", compress_level=1)


# ---------------------------------------------------------------- music + sfx
SR = 48000


def music(path):
    n = int(SR * (TOTAL + 1.5))
    L = np.zeros(n)
    R = np.zeros(n)
    rng = np.random.default_rng(23)

    def add(sig, t0, gl=1.0, gr=1.0):
        i = int(t0 * SR)
        if i >= n or i < 0:
            return
        j = min(n, i + len(sig))
        L[i:j] += sig[: j - i] * gl
        R[i:j] += sig[: j - i] * gr

    tt = lambda d: np.arange(int(d * SR)) / SR
    note = lambda m: 440.0 * 2 ** ((m - 69) / 12)

    def pizz(m, v=0.12):
        t = tt(0.35)
        f = note(m)
        s = np.sin(2 * np.pi * f * t) + 0.5 * np.sin(2 * np.pi * 2 * f * t) * np.exp(-t / 0.04) + 0.2 * np.sin(2 * np.pi * 3 * f * t) * np.exp(-t / 0.02)
        return s * np.minimum(1, t / 0.002) * np.exp(-t / 0.09) * v

    def marimba(m, v=0.1):
        t = tt(0.6)
        f = note(m)
        s = np.sin(2 * np.pi * f * t) + 0.3 * np.sin(2 * np.pi * 3.93 * f * t) * np.exp(-t / 0.03)
        return s * np.minimum(1, t / 0.002) * np.exp(-t / 0.22) * v

    def bass(m, v=0.3):
        t = tt(0.3)
        f = note(m)
        s = np.sin(2 * np.pi * f * t) + 0.3 * np.sin(2 * np.pi * 2 * f * t)
        return s * np.minimum(1, t / 0.005) * np.exp(-t / 0.12) * v

    def kick(v=0.6):
        t = tt(0.25)
        f = 50 + 80 * np.exp(-t / 0.03)
        return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.08) * v

    def snap(v=0.16):
        t = tt(0.12)
        x = rng.normal(0, 1, len(t))
        x = x - np.convolve(x, np.ones(6) / 6, "same")
        return x * np.exp(-t / 0.03) * v

    def shaker(v=0.04):
        t = tt(0.05)
        x = rng.normal(0, 1, len(t))
        x = x - np.convolve(x, np.ones(3) / 3, "same")
        return x * np.sin(np.pi * np.minimum(1, t / 0.05)) * v

    def buzz(t0, d, v=0.06, f0=560):
        t = tt(d)
        f = f0 + 35 * np.sin(2 * np.pi * 5.5 * t) + 15 * np.sin(2 * np.pi * 1.3 * t)
        ph = 2 * np.pi * np.cumsum(f) / SR
        s = sum(np.sin(k * ph) / k for k in range(1, 9))
        am = 0.7 + 0.3 * np.sin(2 * np.pi * 38 * t)
        env = np.minimum(1, t / 0.15) * np.minimum(1, (d - t) / 0.15)
        pan = 0.5 + 0.4 * np.sin(2 * np.pi * 0.6 * t)
        add(s * am * env * v * (1 - pan) * 2, t0, 1, 0)
        add(s * am * env * v * pan * 2, t0, 0, 1)

    def bonk(t0):
        t = tt(0.5)
        thud = np.sin(2 * np.pi * np.cumsum(140 * np.exp(-t / 0.05) + 55) / SR) * np.exp(-t / 0.09) * 0.5
        f = 620 * np.exp(-t / 0.22) + 180
        boing = np.sin(2 * np.pi * np.cumsum(f * (1 + 0.06 * np.sin(2 * np.pi * 18 * t))) / SR) * np.exp(-t / 0.18) * 0.22
        add(thud + boing, t0)

    # C - Am - F - G, one chord per 2 s; playful staccato
    chords = [(48, [60, 64, 67]), (45, [57, 60, 64]), (41, [57, 60, 65]), (43, [55, 59, 62])]
    mel = [72, 74, 76, 79, 76, 74, 72, 71, 72, 76, 77, 76, 74, 72, 71, 67]
    for b in range(int(math.ceil(TOTAL / 2)) + 1):
        t0 = b * 2.0
        if t0 >= TOTAL:
            break
        root, tones = chords[b % 4]
        for k in range(4):  # off-beat pizzicato chords
            tb = t0 + k * 0.5 + 0.25
            for m in tones:
                add(pizz(m, 0.05), tb, 0.9, 1.0)
        add(bass(root), t0)
        add(bass(root + 7, 0.22), t0 + 1.0)
        if t0 >= SECT[0] - 0.01 and t0 < T_END:
            for k in range(4):
                tb = t0 + k * 0.5
                add(marimba(mel[(b * 4 + k) % len(mel)], 0.075), tb, 1.0, 0.85)
    for i in range(int(TOTAL / 0.5)):
        tb = i * 0.5
        if tb < SECT[0] or tb >= TOTAL - 0.5:
            continue
        soft = tb >= T_END
        if i % 2 == 0:
            add(kick(0.45 if soft else 0.6), tb)
        else:
            add(snap(0.1 if soft else 0.16), tb, 1.0, 0.9)
        add(shaker(), tb + 0.25, 0.75, 1.0)
    buzz(0.0, 3.0, 0.05)
    for t0 in SECT:
        buzz(t0, 1.5, 0.045, 600)
        bonk(t0 + 1.5)
        buzz(t0 + 2.0, 1.2, 0.025, 480)
    buzz(T_END, 1.6, 0.03, 470)
    m = int(TOTAL * SR)
    L, R = L[:m], R[:m]
    for dl, g in ((0.027, 0.2), (0.051, 0.14)):
        s = int(dl * SR)
        L[s:] += R[:-s] * g
        R[s:] += L[:-s] * g * 0.9
    fade = np.minimum(1, (m - np.arange(m)) / (0.9 * SR)) * np.minimum(1, np.arange(m) / (0.03 * SR))
    L, R = L * fade, R * fade
    pk = max(np.abs(L).max(), np.abs(R).max())
    pcm = (np.stack([L, R], 1) / pk * 0.9 * 32767).astype(np.int16)
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(f"{D}/frames", exist_ok=True)
    if len(sys.argv) > 1 and sys.argv[1] == "prev":
        for s in sys.argv[2].split(","):
            overlay(float(s)).save(f"{D}/frames/ov_{s}.png")
        sys.exit()
    music(f"{D}/music_chivin.wav")
    with Pool(2) as p:
        p.map(job, range(NF), chunksize=15)
    print("frames", NF)
