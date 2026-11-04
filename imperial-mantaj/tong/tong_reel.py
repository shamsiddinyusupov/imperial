"""Plisse — premium «Yangi uydagi birinchi tong» (16.5 s). Overlay frames + sound design.

python3 tong_reel.py            -> sound_tong.wav + ov/0000.png … (495 frames)
python3 tong_reel.py prev 1,5   -> preview overlays at those times into frames/
python3 tong_reel.py nomusic    -> sound_tong_nomusic.wav (ambience + foley only)
"""
import math
import os
import sys
import wave
from multiprocessing import Pool

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H, FPS = 1080, 1920, 30
TOTAL = 16.5
NF = round(TOTAL * FPS)
CUTS = [3.9, 6.9, 10.0]          # dissolve centres between shots A|B|C|D
T_END = 12.8                     # end card
D = "/home/claude/reels/tong"
OUT = f"{D}/ov"
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
RUF = lambda s: F("Inter-Italic.otf", s)
CREAM, GOLD = (246, 240, 228), (214, 178, 108)
SOFT, DIM = (226, 218, 204), (214, 206, 192)
MAXW = 920

# (start, end, [(text, font_fn, size, colour, y, delay)])
BEATS = [
    (0.0, CUTS[0] - 0.15, [
        ("IMPERIAL  ·  PLISSE", "label", 27, GOLD, 392, -0.6),
        ("Yangi uydagi", "ser", 112, CREAM, 438, -0.6),
        ("birinchi tong.", "seri", 112, CREAM, 560, 0.2),
        ("Первое утро в новом доме", "ru", 34, DIM, 712, 0.55),
    ]),
    (CUTS[0] + 0.1, CUTS[1] - 0.15, [
        ("Bitta harakat —", "ser", 92, CREAM, 430, 0.0),
        ("xona yorug‘likka to‘ladi.", "seri", 92, CREAM, 534, 0.55),
        ("Одно движение — и в комнате светло", "ru", 32, DIM, 668, 0.9),
    ]),
    (CUTS[1] + 0.1, CUTS[2] - 0.15, [
        ("O‘lchovdan 3 kun o‘tib —", "ser", 88, CREAM, 430, 0.0),
        ("derazangiz tayyor.", "seri", 88, CREAM, 530, 0.5),
        ("Готово через 3 дня после замера", "ru", 32, DIM, 660, 0.85),
    ]),
    (CUTS[2] + 0.1, T_END - 0.05, [
        ("Toshkent shahrida", "ser", 88, CREAM, 430, 0.0),
        ("o‘lchov va o‘rnatish bepul.", "seri", 88, CREAM, 530, 0.45),
        ("Замер и установка по Ташкенту — бесплатно", "ru", 30, DIM, 660, 0.8),
    ]),
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


def shadow(L, b=14, a=0.55):
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


def font_for(kind, size, text):
    fn = {"ser": SER, "seri": SERI, "label": MED, "ru": RUF}[kind]
    tr = 0.32 if kind == "label" else 0.0
    while tw(text, fn(size), tr) > MAXW and size > 20:   # shrink to fit the safe width
        size -= 2
    return fn(size), tr


def line_layer(text, kind, size, fill):
    f, tr = font_for(kind, size, text)
    L = Image.new("RGBA", (W, int(size * 1.6)), (0, 0, 0, 0))
    d = ImageDraw.Draw(L)
    w = tw(text, f, tr)
    x0 = (W - w) / 2
    tracked(d, (x0, 0), text, f, fill, tr)
    if kind == "label":                      # thin gold rules either side of the label
        yy = int(size * 0.62)
        d.line([(x0 - 86, yy), (x0 - 26, yy)], fill=GOLD, width=2)
        d.line([(x0 + w + 20, yy), (x0 + w + 80, yy)], fill=GOLD, width=2)
    return shadow(L)


LAYERS = [[(line_layer(t, k, s, c), y, dl) for t, k, s, c, y, dl in lines] for _, _, lines in BEATS]


def grad_top(y1, amax):
    ys = np.arange(H, dtype=np.float32)
    a = np.clip(1 - ys / y1, 0, 1) ** 1.25 * amax
    img = np.zeros((H, W, 4), np.uint8)
    img[..., :3] = (10, 9, 8)
    img[..., 3] = (np.repeat(a[:, None], W, 1) * 255).astype(np.uint8)
    return Image.fromarray(img, "RGBA")


SCRIM = grad_top(1180, 0.86)
DARK = Image.new("RGBA", (W, H), (12, 10, 9, 150))


def plane(d, cx, cy, s, col):
    """Instagram-style 'send' paper plane outline."""
    p = [(cx - s, cy - s * 0.15), (cx + s, cy - s * 0.85), (cx + s * 0.2, cy + s * 0.95), (cx - s * 0.05, cy + s * 0.12)]
    d.line(p + [p[0]], fill=col, width=4, joint="curve")
    d.line([(cx - s * 0.05, cy + s * 0.12), (cx + s, cy - s * 0.85)], fill=col, width=4)


def end_card():
    L = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(L)
    plane(d, W / 2, 640, 34, GOLD)
    for text, kind, size, col, y in (("Yangi uyga ko‘chayotgan", "ser", 84, CREAM, 722),
                                     ("yaqiningizga yuboring.", "seri", 84, GOLD, 822),
                                     ("Отправьте тому, кто переезжает в новый дом", "ru", 31, DIM, 950)):
        f, tr = font_for(kind, size, text)
        tracked(d, ((W - tw(text, f, tr)) / 2, y), text, f, col, tr)
    d.line([(W / 2 - 60, 1032), (W / 2 + 60, 1032)], fill=GOLD, width=2)
    f = SER(70)
    tracked(d, ((W - tw("IMPERIAL", f, 0.2)) / 2, 1062), "IMPERIAL", f, CREAM, 0.2)
    f = MED(26)
    tracked(d, ((W - tw("PLISSE  ·  JALYUZI", f, 0.34)) / 2, 1150), "PLISSE  ·  JALYUZI", f, GOLD, 0.34)
    t = "Narxi uchun izohga NARX deb yozing"
    f = MED(34)
    w = f.getlength(t)
    d.rounded_rectangle((W / 2 - w / 2 - 42, 1222, W / 2 + w / 2 + 42, 1294), 36, outline=GOLD, width=2)
    d.text((W / 2 - w / 2, 1238), t, font=f, fill=CREAM)
    t = "Цена — напишите NARX в комментариях · @imperial_jalyuzi_uz"
    f = LIT(27)
    d.text(((W - f.getlength(t)) / 2, 1326), t, font=f, fill=DIM)
    return shadow(L)


END = end_card()


def overlay(t):
    L = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if t < T_END + 0.3:
        L.alpha_composite(alpha(SCRIM, 1 - ease((t - T_END) / 0.3) if t > T_END else 1))
    for (t0, t1, _), lays in zip(BEATS, LAYERS):
        if not (t0 <= t < t1 + 0.01):
            continue
        out = 1 - ease((t - (t1 - 0.3)) / 0.3) if t > t1 - 0.3 else 1
        for lay, y, dl in lays:
            p = (t - t0 - dl) / 0.6
            if p <= 0:
                continue
            a = ease(p) * out
            L.alpha_composite(alpha(lay, a), (0, y + int(16 * (1 - ease(p)))))
    if t >= T_END:
        a = ease((t - T_END) / 0.6)
        L.alpha_composite(alpha(DARK, a))
        ca = ease((t - T_END - 0.3) / 0.7)
        L.alpha_composite(alpha(END, ca), (0, int(22 * (1 - ca))))
    return L


def job(i):
    overlay(i / FPS).save(f"{OUT}/{i:04d}.png", compress_level=1)


# ---------------------------------------------------------------- sound design
SR = 48000


def sound(path, music=True):
    n = int(SR * (TOTAL + 1.5))
    L = np.zeros(n)
    R = np.zeros(n)
    rng = np.random.default_rng(7)

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

    # quiet morning room tone
    x = lp(lp(rng.normal(0, 1, n), 60), 30)
    x /= np.abs(x).max()
    L += x * 0.012
    R += np.roll(x, 900) * 0.012

    # distant birds: short gliding chirps, sparse at first, more once light comes in
    def chirp(t0, f0, f1, dur, v, pan):
        t = tt(dur)
        f = f0 + (f1 - f0) * (t / dur) ** 0.7 + 90 * np.sin(2 * np.pi * 34 * t)
        s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * t / dur) ** 2
        add(s * v, t0, 1 - pan, pan)

    def song(t0, v, pan):
        base = rng.uniform(2900, 3600)
        for k in range(rng.integers(2, 5)):
            chirp(t0 + k * rng.uniform(0.09, 0.14), base * rng.uniform(0.95, 1.1), base * rng.uniform(1.15, 1.35), rng.uniform(0.05, 0.09), v, pan)

    for t0, v in ((0.6, 0.010), (2.2, 0.012), (3.4, 0.022), (4.6, 0.026), (5.5, 0.02), (7.5, 0.026), (8.4, 0.02),
                  (9.3, 0.018), (10.9, 0.016), (12.2, 0.014), (13.9, 0.012), (15.2, 0.01)):
        song(t0 + rng.uniform(-0.1, 0.1), v, rng.uniform(0.2, 0.8))

    # fabric / rail foley at the hand moves (soft pleat swish)
    def swish(t0, dur=0.55, v=0.05):
        t = tt(dur)
        nz = rng.normal(0, 1, len(t))
        bp = lp(nz, 3) - lp(nz, 26)
        env = np.sin(np.pi * np.minimum(1, t / dur)) ** 1.5
        add(bp * env * v, t0, 0.9, 1.0)

    for t0 in (1.25, 2.55, 4.2, 5.4, 7.15, 8.3):
        swish(t0)

    # morning light: a slow airy swell under each reveal
    def air(t0, dur=2.4, v=0.03):
        t = tt(dur)
        a = lp(lp(rng.normal(0, 1, len(t)), 18), 9)
        a /= np.abs(a).max() + 1e-9
        add(a * np.sin(np.pi * t / dur) ** 2 * v, t0, 0.85, 1.0)

    for t0 in (2.6, 4.0, 7.0):
        air(t0)

    def piano(m, dur, v):
        t = tt(dur)
        fr = note(m)
        s = sum(np.sin(2 * np.pi * fr * k * t) * np.exp(-t * (0.8 + 1.2 * k)) / k ** 1.4 for k in range(1, 7))
        s = lp(s, 3)
        return s * np.minimum(1, t / 0.006) * np.minimum(1, (dur - t) / 0.25) * v

    def pad(ms, dur, v=0.035):
        t = tt(dur)
        s = sum(np.sin(2 * np.pi * note(m) * t + k) + 0.5 * np.sin(2 * np.pi * note(m) * 1.002 * t) for k, m in enumerate(ms))
        return s * np.minimum(1, t / 1.0) * np.minimum(1, (dur - t) / 1.0) / len(ms) * v

    def thump(t0, v=0.2):
        t = tt(0.6)
        add(np.sin(2 * np.pi * np.cumsum(40 + 30 * np.exp(-t / 0.08)) / SR) * np.exp(-t / 0.25) * v, t0)

    if music:
        # D major, open voicings: D – A/C# – Bm – G – D(add9)
        starts = [0.0, CUTS[0], CUTS[1], CUTS[2], T_END]
        chords = [[62, 66, 69, 74], [61, 64, 69, 73], [59, 62, 66, 71], [55, 59, 62, 69], [62, 66, 69, 76]]
        roots = [38, 37, 35, 31, 38]
        arp = [0, 2, 1, 3, 2, 1, 3, 2]
        for i, t0 in enumerate(starts):
            dur = (starts[i + 1] if i + 1 < len(starts) else TOTAL) - t0
            ch = chords[i]
            add(pad([m - 12 for m in ch], dur + 1.0, 0.045), max(0, t0 - 0.2))
            add(piano(roots[i] + 12, 3.0, 0.1), t0)
            if i:
                thump(t0, 0.14 if i < 4 else 0.22)
            for k in range(int(dur / 0.45)):
                if i == 4 and k > 5:
                    break
                vel = (0.034 if i == 0 else 0.048) + 0.01 * (k % 2 == 0)
                add(piano(ch[arp[k % 8]] + 12, 1.6, vel), t0 + 0.05 + k * 0.45, 1.0 - 0.15 * (k % 2), 0.85 + 0.15 * (k % 2))
        add(piano(88, 2.5, 0.05), T_END + 0.45, 0.85, 1.0)      # small "send" chime
        add(piano(93, 2.5, 0.04), T_END + 0.62, 1.0, 0.85)
    else:
        add(piano(88, 2.5, 0.035), T_END + 0.45, 0.85, 1.0)
        add(piano(93, 2.5, 0.03), T_END + 0.62, 1.0, 0.85)

    m = int(TOTAL * SR)
    L, R = L[:m], R[:m]
    wet_L, wet_R = np.zeros(m), np.zeros(m)
    for dl, g in ((0.047, 0.3), (0.079, 0.24), (0.121, 0.18), (0.173, 0.12), (0.251, 0.08), (0.34, 0.05)):
        s_ = int(dl * SR)
        wet_L[s_:] += R[:-s_] * g
        wet_R[s_:] += L[:-s_] * g
    L += wet_L
    R += wet_R
    fadev = np.minimum(1, (m - np.arange(m)) / (1.2 * SR)) * np.minimum(1, np.arange(m) / (0.08 * SR))
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
            overlay(float(s)).save(f"{D}/frames/ov_{s}.png")
        sys.exit()
    if len(sys.argv) > 1 and sys.argv[1] == "nomusic":
        sound(f"{D}/sound_tong_nomusic.wav", music=False)
        sys.exit()
    sound(f"{D}/sound_tong.wav")
    with Pool(2) as p:
        p.map(job, range(NF), chunksize=15)
    print("frames", NF)
