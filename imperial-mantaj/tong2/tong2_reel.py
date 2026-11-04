"""«Hamma narsa yangi. Bittasidan tashqari.» — renew old plisse/kombo fabric. Overlays + music bed, timed by timing.json.

python3 tong2_reel.py            -> bed.wav + bed_nomusic.wav + ov/0000.png …
python3 tong2_reel.py prev 1,5   -> overlay previews into frames/
"""
import json
import os
import sys
import wave
from multiprocessing import Pool

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H, FPS = 1080, 1920, 30
D = "/home/claude/reels/tong2"
TIM = json.load(open(f"{D}/timing.json"))
TOTAL = TIM["total"]
NF = round(TOTAL * FPS)
LN = TIM["lines"]
BT = TIM["beats"]
T_END = BT[6][0]
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
LIT = lambda s: F("Inter-LightItalic.otf", s)
RUF = lambda s: F("Inter-Italic.otf", s)
CREAM, GOLD = (246, 240, 228), (214, 178, 108)
DIM = (214, 206, 192)
MAXW = 930


def ls(i, frac=0.0):
    """Time inside narration line i (0-based) at fraction frac of its length."""
    return LN[i]["start"] + frac * LN[i]["len"]


# beat index -> lines: (text, kind, size, colour, y, appear_time)
BEATS = {
    0: [("IMPERIAL  ·  PLISSE  ·  KOMBO", "label", 26, GOLD, 404, -1.0),
        ("Hamma narsa", "ser", 126, CREAM, 452, -1.0),
        ("yangi.", "seri", 126, CREAM, 584, -1.0),
        ("Всё новое.", "ru", 36, DIM, 742, 0.35)],
    1: [("Bittasidan tashqari.", "seri", 104, CREAM, 440, ls(1, 0.0)),
        ("Derazadagi — eski jalyuzi.", "ser", 72, CREAM, 576, ls(1, 0.45)),
        ("Кроме одного — старых жалюзи на окне", "ru", 32, DIM, 686, ls(1, 0.6))],
    2: [("Uni tashlamang.", "ser", 104, CREAM, 430, ls(2, 0.0)),
        ("Plisse va kombo matosini", "seri", 76, CREAM, 562, ls(2, 0.25)),
        ("yangilaymiz.", "seri", 76, GOLD, 650, ls(2, 0.8)),
        ("Не выбрасывайте — обновим ткань плиссе и комбо", "ru", 30, DIM, 768, ls(2, 0.4))],
    3: [("Siz yoqtirgan rangda.", "ser", 92, CREAM, 440, ls(3, 0.0) - 0.1),
        ("Siz yoqtirgan uslubda.", "seri", 92, CREAM, 552, ls(3, 0.56)),
        ("В цвете и стиле, который нравится вам", "ru", 31, DIM, 690, ls(3, 0.66))],
    4: [("Matosi joyida, faqat kir bo‘lsa?", "ser", 70, CREAM, 440, ls(4, 0.0)),
        ("Yechib, yuvib, qayta o‘rnatamiz.", "seri", 70, CREAM, 532, ls(4, 0.55)),
        ("Ткань цела, но загрязнилась? Снимем, постираем, повесим", "ru", 29, DIM, 646, ls(4, 0.62))],
    5: [("Yangilangan xonaga —", "ser", 96, CREAM, 440, ls(5, 0.0)),
        ("yangilangan deraza.", "seri", 96, GOLD, 552, ls(5, 0.55)),
        ("Обновлённой комнате — обновлённое окно", "ru", 31, DIM, 690, ls(5, 0.7))],
}


def ease(x):
    x = max(0.0, min(1.0, x))
    return 1 - (1 - x) ** 3


def alpha(layer, a):
    if a >= 1:
        return layer
    l2 = layer.copy()
    l2.putalpha(layer.getchannel("A").point(lambda v: int(v * max(0, a))))
    return l2


def shadow(L, b=14, a=0.6):
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
    tr = 0.3 if kind == "label" else 0.0
    while tw(text, fn(size), tr) > MAXW and size > 20:
        size -= 2
    return fn(size), tr


def line_layer(text, kind, size, fill):
    f, tr = font_for(kind, size, text)
    L = Image.new("RGBA", (W, int(size * 1.6)), (0, 0, 0, 0))
    d = ImageDraw.Draw(L)
    w = tw(text, f, tr)
    x0 = (W - w) / 2
    tracked(d, (x0, 0), text, f, fill, tr)
    if kind == "label":
        yy = int(size * 0.62)
        d.line([(x0 - 80, yy), (x0 - 24, yy)], fill=GOLD, width=2)
        d.line([(x0 + w + 18, yy), (x0 + w + 74, yy)], fill=GOLD, width=2)
    return shadow(L)


LAYERS = {b: [(line_layer(t, k, s, c), y, at) for t, k, s, c, y, at in lines] for b, lines in BEATS.items()}


def grad_top(y1, amax):
    ys = np.arange(H, dtype=np.float32)
    a = np.clip(1 - ys / y1, 0, 1) ** 1.25 * amax
    img = np.zeros((H, W, 4), np.uint8)
    img[..., :3] = (10, 9, 8)
    img[..., 3] = (np.repeat(a[:, None], W, 1) * 255).astype(np.uint8)
    return Image.fromarray(img, "RGBA")


SCRIM = grad_top(1200, 0.86)
DARK = Image.new("RGBA", (W, H), (12, 10, 9, 160))


def plane(d, cx, cy, s, col):
    p = [(cx - s, cy - s * 0.15), (cx + s, cy - s * 0.85), (cx + s * 0.2, cy + s * 0.95), (cx - s * 0.05, cy + s * 0.12)]
    d.line(p + [p[0]], fill=col, width=4, joint="curve")
    d.line([(cx - s * 0.05, cy + s * 0.12), (cx + s, cy - s * 0.85)], fill=col, width=4)


def end_card():
    L = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(L)
    plane(d, W / 2, 640, 34, GOLD)
    for text, kind, size, col, y in (("Eski jalyuzingiz rasmini", "ser", 84, CREAM, 722),
                                     ("direktga yuboring.", "seri", 84, GOLD, 822),
                                     ("Пришлите фото старых жалюзи в директ", "ru", 31, DIM, 950)):
        f, tr = font_for(kind, size, text)
        tracked(d, ((W - tw(text, f, tr)) / 2, y), text, f, col, tr)
    d.line([(W / 2 - 60, 1032), (W / 2 + 60, 1032)], fill=GOLD, width=2)
    f = SER(70)
    tracked(d, ((W - tw("IMPERIAL", f, 0.2)) / 2, 1062), "IMPERIAL", f, CREAM, 0.2)
    f = MED(26)
    tracked(d, ((W - tw("PLISSE  ·  KOMBO", f, 0.34)) / 2, 1150), "PLISSE  ·  KOMBO", f, GOLD, 0.34)
    t = "Ko‘rib, aytib beramiz"
    f = MED(34)
    w = f.getlength(t)
    d.rounded_rectangle((W / 2 - w / 2 - 42, 1222, W / 2 + w / 2 + 42, 1294), 36, outline=GOLD, width=2)
    d.text((W / 2 - w / 2, 1238), t, font=f, fill=CREAM)
    t = "Ta’mir qilayotgan yaqiningizga ham yuboring · @imperial_jalyuzi_uz"
    f = LIT(27)
    d.text(((W - f.getlength(t)) / 2, 1326), t, font=f, fill=DIM)
    return shadow(L)


END = end_card()


def overlay(t):
    L = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if t < T_END + 0.3:
        L.alpha_composite(alpha(SCRIM, 1 - ease((t - T_END) / 0.3) if t > T_END else 1))
    for b, lays in LAYERS.items():
        t0, t1 = BT[b]
        t1 = t1 - 0.05
        if not (t0 - 0.2 <= t < t1 + 0.01):
            continue
        out = 1 - ease((t - (t1 - 0.28)) / 0.28) if t > t1 - 0.28 else 1
        for lay, y, at in lays:
            p = (t - at) / 0.55
            if p <= 0:
                continue
            a = ease(p) * out
            L.alpha_composite(alpha(lay, a), (0, y + int(16 * (1 - ease(p)))))
    if t >= T_END:
        a = ease((t - T_END) / 0.6)
        L.alpha_composite(alpha(DARK, a))
        ca = ease((t - T_END - 0.25) / 0.7)
        L.alpha_composite(alpha(END, ca), (0, int(22 * (1 - ca))))
    return L


def job(i):
    overlay(i / FPS).save(f"{OUT}/{i:04d}.png", compress_level=1)


# ---------------------------------------------------------------- music bed + foley (voice is mixed later)
SR = 48000


def bed(path, music=True):
    n = int(SR * (TOTAL + 1.5))
    Lc = np.zeros(n)
    Rc = np.zeros(n)
    rng = np.random.default_rng(11)

    def add(sig, t0, gl=1.0, gr=1.0):
        i = int(t0 * SR)
        if i >= n or i < 0:
            return
        j = min(n, i + len(sig))
        Lc[i:j] += sig[: j - i] * gl
        Rc[i:j] += sig[: j - i] * gr

    tt = lambda d: np.arange(int(d * SR)) / SR
    note = lambda m: 440.0 * 2 ** ((m - 69) / 12)
    lp = lambda x, k: np.convolve(x, np.ones(k) / k, "same")

    x = lp(lp(rng.normal(0, 1, n), 60), 30)          # quiet room tone
    x /= np.abs(x).max()
    Lc += x * 0.01
    Rc += np.roll(x, 900) * 0.01

    def swish(t0, dur=0.32, v=0.035):
        t = tt(dur)
        nz = rng.normal(0, 1, len(t))
        add((lp(nz, 3) - lp(nz, 22)) * np.sin(np.pi * t / dur) ** 1.5 * v, t0, 0.9, 1.0)

    def air(t0, dur=2.0, v=0.035):
        t = tt(dur)
        a = lp(lp(rng.normal(0, 1, len(t)), 18), 9)
        a /= np.abs(a).max() + 1e-9
        add(a * np.sin(np.pi * t / dur) ** 2 * v, t0, 0.85, 1.0)

    def piano(m, dur, v):
        t = tt(dur)
        fr = note(m)
        s = sum(np.sin(2 * np.pi * fr * k * t) * np.exp(-t * (0.8 + 1.2 * k)) / k ** 1.4 for k in range(1, 7))
        s = lp(s, 3)
        return s * np.minimum(1, t / 0.006) * np.minimum(1, (dur - t) / 0.25) * v

    def pad(ms, dur, v=0.04):
        t = tt(dur)
        s = sum(np.sin(2 * np.pi * note(m) * t + k) + 0.5 * np.sin(2 * np.pi * note(m) * 1.002 * t) for k, m in enumerate(ms))
        return s * np.minimum(1, t / 0.8) * np.minimum(1, (dur - t) / 0.8) / len(ms) * v

    def thump(t0, v=0.2):
        t = tt(0.6)
        add(np.sin(2 * np.pi * np.cumsum(40 + 30 * np.exp(-t / 0.08)) / SR) * np.exp(-t / 0.25) * v, t0)

    # foley: montage cuts, the colour-return swell, end chime
    m0, m1 = BT[3]
    for k in range(6):
        swish(m0 + k * (m1 - m0) / 6 - 0.05)
    CH = TIM["chunks"][2]
    c_mid = CH[1][0]                                  # colour returns on the word "Plisse"
    kombo_on = CH[1][0] + 0.27 * (CH[1][1] - CH[1][0])
    air(c_mid - 0.4, 2.4, 0.045)
    swish(kombo_on - 0.05, 0.4, 0.04)                 # cut to kombo
    swish(CH[2][0] - 0.05, 0.4, 0.035)                # cut to the kombo room
    swish(BT[4][0] + 0.2, 0.5, 0.04)

    if music:
        # beat 0: single held note (the hook stays sparse); beats 1–2 minor (the "old"), colour return → major
        add(piano(57, 3.5, 0.08), 0.05)
        add(pad([45, 52, 57, 60], BT[1][0] + 0.6, 0.03), 0.0)
        sections = [  # (start, end, chord, root)
            (BT[1][0], c_mid, [57, 60, 64, 69], 33),           # A minor — the old blind
            (c_mid, BT[3][0], [60, 64, 67, 72], 36),            # C major — colour returns
            (BT[3][0], BT[4][0], [65, 69, 72, 77], 41),         # F — montage
            (BT[4][0], BT[5][0], [62, 65, 69, 74], 38),         # Dm
            (BT[5][0], BT[6][0], [67, 71, 74, 79], 43),         # G
            (BT[6][0], TOTAL, [60, 64, 67, 74], 36),            # C(add9) — end card
        ]
        arp = [0, 2, 1, 3, 2, 1, 3, 2]
        step = 0.42
        for si, (a, b, ch, root) in enumerate(sections):
            dur = b - a
            add(pad([m - 12 for m in ch], dur + 0.9, 0.045), max(0, a - 0.2))
            add(piano(root + 12, 3.0, 0.1), a)
            thump(a, 0.16 if si < 5 else 0.22)
            if si == 0:
                continue                         # keep the "old" part sparse
            for k in range(int(dur / step)):
                if si == 5 and k > 6:
                    break
                vel = 0.045 + 0.01 * (k % 2 == 0) + (0.01 if si == 2 else 0)
                add(piano(ch[arp[k % 8]] + 12, 1.5, vel), a + 0.05 + k * step, 1.0 - 0.15 * (k % 2), 0.85 + 0.15 * (k % 2))
    add(piano(88, 2.5, 0.05 if music else 0.035), T_END + 0.45, 0.85, 1.0)
    add(piano(93, 2.5, 0.04 if music else 0.03), T_END + 0.62, 1.0, 0.85)

    m = int(TOTAL * SR)
    Lc, Rc = Lc[:m], Rc[:m]
    wl, wr = np.zeros(m), np.zeros(m)
    for dl, g in ((0.047, 0.3), (0.079, 0.24), (0.121, 0.18), (0.173, 0.12), (0.251, 0.08), (0.34, 0.05)):
        s_ = int(dl * SR)
        wl[s_:] += Rc[:-s_] * g
        wr[s_:] += Lc[:-s_] * g
    Lc += wl
    Rc += wr
    fv = np.minimum(1, (m - np.arange(m)) / (1.2 * SR)) * np.minimum(1, np.arange(m) / (0.05 * SR))
    Lc, Rc = Lc * fv, Rc * fv
    pk = max(np.abs(Lc).max(), np.abs(Rc).max())
    pcm = (np.stack([Lc, Rc], 1) / pk * 0.9 * 32767).astype(np.int16)
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
    bed(f"{D}/bed.wav")
    bed(f"{D}/bed_nomusic.wav", music=False)
    for f in os.listdir(OUT):
        os.remove(f"{OUT}/{f}")
    with Pool(2) as p:
        p.map(job, range(NF), chunksize=15)
    print("frames", NF)
