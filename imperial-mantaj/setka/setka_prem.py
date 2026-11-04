"""Moskit setka — premium «Bu ovozni oxirgi marta eshityapsiz». Overlays (900 frames) + sound design, 30 s."""
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
T_CLOSE, T_SILENCE_END = 4.0, 5.0
SECT = [5.0, 9.0, 13.0, 17.0, 21.0]
SLEN = 4.0
T_END = 25.0
D = "/home/claude/reels/setka"
OUT = f"{D}/ovp"
FI = "/usr/share/fonts/opentype/inter/"
CX = "/usr/share/fonts/truetype/crosextra/"
_F = {}


def F(name, size):
    k = (name, size)
    if k not in _F:
        _F[k] = ImageFont.truetype(name if name.startswith("/") else FI + name, size)
    return _F[k]


SER = lambda s: F(CX + "Caladea-Regular.ttf", s)
SERI = lambda s: F(CX + "Caladea-Italic.ttf", s)
MED = lambda s: F("Inter-Medium.otf", s)
REG = lambda s: F("Inter-Regular.otf", s)
LIT = lambda s: F("Inter-LightItalic.otf", s)
CREAM, GOLD = (244, 238, 226), (205, 170, 105)
SOFT, DIM = (222, 214, 200), (185, 178, 166)

SECTIONS = [
    ("01 · SURMA SETKA", "Eshik uchun", "Shabada kiradi. Chivin — yo‘q.", "Ветер — да. Комары — нет."),
    ("02 · SURMA SETKA", "Deraza uchun", "Deraza ochiq. Tun tinch.", "Окно открыто. Ночь спокойна."),
    ("03 · PETLYALI SETKA", "Eshikdek ochiladi", "Siz uchun ochiladi. Chivin uchun — yo‘q.", "Открывается для вас. Не для комаров."),
    ("04 · STANDART SETKA", "4 tomondan qotiriladi", "Bitta tirqish ham qolmaydi.", "Ни одной щели."),
    ("05 · UNI SETKA", "Har bir derazaga o‘lchab", "Faqat toza havo.", "Только свежий воздух."),
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


def shadow(L, b=12, a=0.5):
    sh = Image.new("RGBA", L.size, (0, 0, 0, 0))
    sh.putalpha(L.getchannel("A").filter(ImageFilter.GaussianBlur(b)).point(lambda v: int(v * a)))
    o = Image.new("RGBA", L.size, (0, 0, 0, 0))
    o.alpha_composite(sh, (0, 3))
    o.alpha_composite(L)
    return o


def tracked(d, xy, t, f, fill, tr):
    x, y = xy
    for c in t:
        d.text((x, y), c, font=f, fill=fill)
        x += f.getlength(c) + f.size * tr
    return x


def tw(t, f, tr=0.0):
    return sum(f.getlength(c) + f.size * tr for c in t)


def ctext(d, y, t, f, fill, tr=0.0):
    tracked(d, ((W - tw(t, f, tr)) / 2, y), t, f, fill, tr)


def grad(y0, y1, amax):
    ys = np.arange(H, dtype=np.float32)
    a = np.clip((ys - y0) / (y1 - y0), 0, 1) ** 1.4 * amax
    img = np.zeros((H, W, 4), np.uint8)
    img[..., 3] = (np.repeat(a[:, None], W, 1) * 255).astype(np.uint8)
    return Image.fromarray(img, "RGBA")


GRAD = grad(1150, 1760, 0.78)
DARK = Image.new("RGBA", (W, H), (8, 8, 10, 150))


def line_layer(t, f, fill, y, tr=0.0):
    L = Image.new("RGBA", (W, 200), (0, 0, 0, 0))
    ctext(ImageDraw.Draw(L), 0, t, f, fill, tr)
    return shadow(L), y


HOOK_LINES = [line_layer(t, SER(96), CREAM, 740 + k * 110) for k, t in enumerate(("Bu ovozni", "oxirgi marta", "eshityapsiz."))]
HOOK_SUB = [line_layer("OVOZNI YOQING", MED(26), (200, 192, 178), 1214, 0.32), line_layer("Вы слышите этот звук в последний раз", LIT(30), DIM, 1264)]
SIL = [line_layer("Jimlik.", SERI(120), CREAM, 820), line_layer("Тишина.", LIT(32), DIM, 980)]


def section_layer(i):
    tag, title, line, ru = SECTIONS[i]
    L = Image.new("RGBA", (W, 300), (0, 0, 0, 0))
    d = ImageDraw.Draw(L)
    d.line([(90, 16), (170, 16)], fill=GOLD, width=2)
    tracked(d, (190, 0), tag, MED(28), GOLD, 0.3)
    d.text((88, 44), title, font=SERI(70), fill=CREAM)
    d.text((90, 144), line, font=SER(40), fill=SOFT)
    d.text((90, 198), ru, font=LIT(28), fill=DIM)
    return shadow(L)


SECTS = [section_layer(i) for i in range(5)]


def end_card():
    L = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(L)
    ctext(d, 740, "IMPERIAL", SER(120), CREAM, 0.22)
    ctext(d, 885, "MOSKIT SETKALAR", MED(30), GOLD, 0.34)
    d.line([(W / 2 - 60, 940), (W / 2 + 60, 940)], fill=GOLD, width=2)
    ctext(d, 970, "Surma · Petlyali · Standart · Uni", SERI(46), CREAM)
    ctext(d, 1042, "Toshkent shahrida bepul o‘lchov va o‘rnatish · 1 yil kafolat", REG(28), (205, 198, 186))
    t = "Direktga yozing — mosini tanlab beramiz"
    f = MED(34)
    w = f.getlength(t)
    d.rounded_rectangle((W / 2 - w / 2 - 40, 1112, W / 2 + w / 2 + 40, 1182), 35, outline=GOLD, width=2)
    d.text((W / 2 - w / 2, 1127), t, font=f, fill=CREAM)
    ctext(d, 1212, "Подберём сетку в директ · @imperial_jalyuzi_uz", LIT(28), DIM)
    return shadow(L)


END = end_card()


def fade(t, t0, t1, fi=0.4, fo=0.35):
    if t < t0 or t >= t1:
        return 0.0
    return ease((t - t0) / fi) * (1 - ease((t - (t1 - fo)) / fo) if t > t1 - fo else 1)


def bars(d, t, cx, cy, amp):
    hs = [10, 26, 44, 30, 58, 36, 20, 48, 28, 14]
    x0 = cx - len(hs) * 14 / 2
    for k, h in enumerate(hs):
        hh = max(6, h * (0.45 + 0.55 * abs(math.sin(t * 9 + k * 0.8))) * amp)
        d.rounded_rectangle((x0 + k * 14, cy - hh / 2, x0 + k * 14 + 6, cy + hh / 2), 3, fill=GOLD + (255,))


def overlay(t):
    L = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if t < T_CLOSE:
        for k, (lay, y) in enumerate(HOOK_LINES):
            a = fade(t, 0.15 + k * 0.45, T_CLOSE - 0.05, 0.5, 0.25)
            if a > 0:
                L.alpha_composite(alpha(lay, a), (0, y + int(18 * (1 - ease((t - 0.15 - k * 0.45) / 0.5)))))
        a = fade(t, 1.4, T_CLOSE - 0.05, 0.5, 0.25)
        if a > 0:
            bl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            bars(ImageDraw.Draw(bl), t, W / 2, 1150, min(1.0, 0.4 + t / 4))
            L.alpha_composite(alpha(bl, a))
            for lay, y in HOOK_SUB:
                L.alpha_composite(alpha(lay, a), (0, y))
    if T_CLOSE <= t < T_SILENCE_END + 0.2:
        a = fade(t, T_CLOSE + 0.12, T_SILENCE_END + 0.2, 0.3, 0.3)
        for lay, y in SIL:
            L.alpha_composite(alpha(lay, a), (0, y))
    for i, t0 in enumerate(SECT):
        if t0 <= t < t0 + SLEN:
            lt = t - t0
            a = fade(t, t0, t0 + SLEN, 0.45, 0.35)
            L.alpha_composite(alpha(GRAD, a))
            ta = fade(t, t0 + 0.25, t0 + SLEN, 0.6, 0.35)
            L.alpha_composite(alpha(SECTS[i], ta), (0, 1424 + int(20 * (1 - ease((lt - 0.25) / 0.6)))))
    if t >= T_END:
        a = ease((t - T_END) / 0.6)
        L.alpha_composite(alpha(DARK, a))
        ca = ease((t - T_END - 0.35) / 0.7)
        L.alpha_composite(alpha(END, ca), (0, int(24 * (1 - ca))))
    return L


def job(i):
    overlay(i / FPS).save(f"{OUT}/{i:04d}.png", compress_level=1)


# ---------------------------------------------------------------- sound design
SR = 48000


def sound(path, music=True):
    n = int(SR * (TOTAL + 1.5))
    L = np.zeros(n)
    R = np.zeros(n)
    rng = np.random.default_rng(31)

    def add(sig, t0, gl=1.0, gr=1.0):
        i = int(t0 * SR)
        if i >= n or i < 0:
            return
        j = min(n, i + len(sig))
        L[i:j] += sig[: j - i] * gl
        R[i:j] += sig[: j - i] * gr

    tt = lambda d: np.arange(int(d * SR)) / SR
    note = lambda m: 440.0 * 2 ** ((m - 69) / 12)
    lp = lambda x, k: np.convolve(x, np.ones(k) / k, "same")

    # mosquito: approaches for 4 s, then is cut off the moment the net closes
    d = T_CLOSE
    t = tt(d)
    jitter = np.cumsum(rng.normal(0, 1, len(t))) / SR * 40
    f = 610 + 28 * np.sin(2 * np.pi * 4.7 * t) + 12 * np.sin(2 * np.pi * 0.9 * t) + jitter - 40 * (t / d)
    ph = 2 * np.pi * np.cumsum(f) / SR
    s = sum(np.sin(k * ph) * (1 / k) ** 1.2 for k in range(1, 10))
    s = s - 0.6 * lp(s, 30)
    am = 0.75 + 0.25 * np.sin(2 * np.pi * 41 * t)
    env = (0.12 + 0.88 * (t / d) ** 1.8) * np.minimum(1, t / 0.2)
    pan = 0.5 + 0.42 * np.sin(2 * np.pi * 0.35 * t + 1.0)
    add(s * am * env * 0.16 * (1 - pan) * 2, 0, 1, 0)
    add(s * am * env * 0.16 * pan * 2, 0, 0, 1)
    # latch click at the cut
    ct = tt(0.05)
    add(rng.normal(0, 1, len(ct)) * np.exp(-ct / 0.004) * 0.35 + np.sin(2 * np.pi * 2300 * ct) * np.exp(-ct / 0.006) * 0.2, T_CLOSE)

    # night crickets, very low, from the start to the end of the silence and faintly after
    for k in range(int(TOTAL * 3)):
        t0 = k / 3 + rng.uniform(0, 0.15)
        ch = tt(0.09)
        chirp = np.sin(2 * np.pi * 4300 * ch) * (0.5 + 0.5 * np.sin(2 * np.pi * 60 * ch)) * np.sin(np.pi * ch / 0.09)
        v = 0.012 if t0 < T_SILENCE_END + 1 else 0.005
        add(chirp * v, t0, 0.6 + 0.4 * (k % 2), 1.0 - 0.4 * (k % 2))

    # felt piano + warm pad from the end of the silence
    def piano(m, dur, v):
        t = tt(dur)
        fr = note(m)
        s = sum(np.sin(2 * np.pi * fr * k * t) * np.exp(-t * (0.9 + 1.3 * k)) / k ** 1.4 for k in range(1, 7))
        s = lp(s, 3)
        return s * np.minimum(1, t / 0.006) * np.minimum(1, (dur - t) / 0.2) * v

    def pad(ms, dur, v=0.035):
        t = tt(dur)
        s = sum(np.sin(2 * np.pi * note(m) * t + k) + 0.5 * np.sin(2 * np.pi * note(m) * 1.002 * t) for k, m in enumerate(ms))
        return s * np.minimum(1, t / 1.2) * np.minimum(1, (dur - t) / 1.2) / len(ms) * v

    def thump(t0, v=0.25):
        t = tt(0.6)
        s = np.sin(2 * np.pi * np.cumsum(38 + 30 * np.exp(-t / 0.08)) / SR) * np.exp(-t / 0.25) * v
        add(s, t0)

    def breeze(t0, dur=2.2, v=0.05):
        t = tt(dur)
        x = lp(lp(rng.normal(0, 1, len(t)), 40), 20)
        x /= np.abs(x).max() + 1e-9
        add(x * np.sin(np.pi * t / dur) ** 2 * v, t0 - 0.3, 0.8, 1.0)

    chords = [[62, 66, 69, 73], [59, 62, 66, 69], [55, 59, 62, 66], [57, 61, 64, 69], [62, 66, 69, 74]]
    roots = [38, 35, 31, 33, 38]
    arp = [0, 2, 1, 3, 2, 1, 3, 2]
    for i, t0 in enumerate(SECT + [T_END] if music else []):
        ch = chords[i % len(chords)]
        dur = SLEN if i < len(SECT) else TOTAL - T_END
        add(pad([m - 12 for m in ch], dur + 1.0, 0.04), t0 - 0.2)
        add(piano(roots[i % len(roots)] + 12, 3.0, 0.11), t0)
        thump(t0, 0.18 if i < len(SECT) else 0.25)
        breeze(t0)
        steps = int(dur / 0.5)
        for k in range(steps):
            if i == len(SECT) and k > 5:
                break
            add(piano(ch[arp[k % 8]] + 12, 1.6, 0.05 + 0.012 * (k % 2 == 0)), t0 + k * 0.5, 1.0 - 0.15 * (k % 2), 0.85 + 0.15 * (k % 2))
    if music:
        add(piano(86, 3.5, 0.05), T_END + 1.5, 0.9, 1.0)

    m = int(TOTAL * SR)
    L, R = L[:m], R[:m]
    # room reverb: a few diffuse echoes (applied only after the cut, so the silence stays clean)
    wet_L, wet_R = np.zeros(m), np.zeros(m)
    for dl, g in ((0.043, 0.3), (0.071, 0.24), (0.113, 0.18), (0.167, 0.12), (0.241, 0.08)):
        s_ = int(dl * SR)
        wet_L[s_:] += R[:-s_] * g
        wet_R[s_:] += L[:-s_] * g
    gate = np.ones(m)
    gate[: int(T_CLOSE * SR)] = 0.25
    L += wet_L * gate
    R += wet_R * gate
    fadev = np.minimum(1, (m - np.arange(m)) / (1.4 * SR)) * np.minimum(1, np.arange(m) / (0.05 * SR))
    L, R = L * fadev, R * fadev
    pk = max(np.abs(L).max(), np.abs(R).max())
    pcm = (np.stack([L, R], 1) / pk * 0.9 * 32767).astype(np.int16)
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    if len(sys.argv) > 1 and sys.argv[1] == "prev":
        for s in sys.argv[2].split(","):
            overlay(float(s)).save(f"{D}/frames/ovp_{s}.png")
        sys.exit()
    if len(sys.argv) > 1 and sys.argv[1] == "nomusic":
        sound(f"{D}/sound_prem_nomusic.wav", music=False)
        sys.exit()
    sound(f"{D}/sound_prem.wav")
    with Pool(2) as p:
        p.map(job, range(NF), chunksize=15)
    print("frames", NF)
