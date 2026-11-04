"""Sales Reel «Derazangizga — ikki yo‘l»: overlays + music bed, timed by timing.json and cuts.json.

python3 tong3_reel.py           -> bed.wav, bed_nomusic.wav, ov/0000.png …
python3 tong3_reel.py prev 1,5  -> overlay previews
"""
import json
import os
import sys
import wave
from multiprocessing import Pool

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H, FPS = 1080, 1920, 30
D = "/home/claude/reels/tong3"
TIM = json.load(open(f"{D}/timing.json"))
CUT = json.load(open(f"{D}/cuts.json"))
TOTAL = TIM["total"]
NF = round(TOTAL * FPS)
LN = TIM["lines"]
T_END = CUT["t4"]
CTA_ON = 3.0
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
SEMI = lambda s: F("Inter-SemiBold.otf", s)
LIT = lambda s: F("Inter-LightItalic.otf", s)
RUF = lambda s: F("Inter-Italic.otf", s)
CREAM, GOLD, INK = (246, 240, 228), (214, 178, 108), (24, 22, 20)
DIM = (214, 206, 192)
MAXW = 930


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


def pill_layer(text, size, fg, outline, fill_rgba, pad=(36, 16)):
    f = MED(size)
    w = f.getlength(text)
    L = Image.new("RGBA", (W, size * 3), (0, 0, 0, 0))
    d = ImageDraw.Draw(L)
    x0 = (W - w) / 2
    d.rounded_rectangle((x0 - pad[0], 4, x0 + w + pad[0], 4 + size + 2 * pad[1]), (size + 2 * pad[1]) // 2,
                        fill=fill_rgba, outline=outline, width=2)
    d.text((x0, 4 + pad[1] - size * 0.08), text, font=f, fill=fg)
    return L


def ch(i, frac):
    t = LN[i]["start"] + frac * LN[i]["len"]
    cs = TIM.get("chunks")
    if not cs:
        return t
    return min((c[0] for c in cs[i]), key=lambda s: abs(s - t))


# (start, end, [(layer, y, appear)])
B1 = (0.0, CUT["t1"])
B2 = (CUT["t1"], CUT["t2"])
B3 = (CUT["t2"], CUT["t3"])
B4 = (CUT["t3"], CUT["t4"])
BEATS = [
    (B1, [("IMPERIAL  ·  PLISSE  ·  KOMBO", "label", 26, GOLD, 300, -1.0),
          ("Derazangizga —", "ser", 104, CREAM, 346, -1.0),
          ("ikki yo‘l.", "seri", 120, GOLD, 462, LN[0]["start"] + 0.5 * LN[0]["len"]),
          ("Два пути для вашего окна", "ru", 32, DIM, 620, 0.8)]),
    (B2, [("1  ·  YANGI KOMBO", "label", 30, GOLD, 404, CUT["t1"] + 0.05),
          ("Yangi kombo.", "ser", 112, CREAM, 450, CUT["t1"] + 0.1),
          ("Toshkentda o‘lchov va o‘rnatish — bepul", "seri", 58, CREAM, 590, CUT["l2b"]),
          ("O‘lchovdan keyin — 3 kunda tayyor", "seri", 58, CREAM, 668, CUT["l2c"]),
          ("Замер и установка бесплатно · готово за 3 дня", "ru", 30, DIM, 760, CUT["l2c"] + 0.3)]),
    (B3, [("2  ·  ESKISINI YANGILASH", "label", 30, GOLD, 404, CUT["t2"] + 0.05),
          ("Eskisini yangilash.", "ser", 100, CREAM, 450, CUT["t2"] + 0.1),
          ("Plisse va kombo matosini almashtiramiz", "seri", 58, CREAM, 584, CUT["l3b"]),
          ("Yoki — yuvib beramiz", "seri", 62, GOLD, 662, CUT["l3c"]),
          ("Заменим ткань плиссе и комбо · или постираем", "ru", 30, DIM, 760, CUT["l3c"] + 0.3)]),
    (B4, [("1 yil", "ser", 210, GOLD, 430, CUT["t3"] + 0.05),
          ("kafolat", "seri", 120, CREAM, 640, CUT["t3"] + 0.25),
          ("Гарантия 1 год", "ru", 32, DIM, 800, CUT["t3"] + 0.4)]),
]
LAYERS = [(b, [(line_layer(t, k, s, c), y, a) for t, k, s, c, y, a in lines]) for b, lines in BEATS]


def grad_top(y1, amax):
    ys = np.arange(H, dtype=np.float32)
    a = np.clip(1 - ys / y1, 0, 1) ** 1.25 * amax
    img = np.zeros((H, W, 4), np.uint8)
    img[..., :3] = (10, 9, 8)
    img[..., 3] = (np.repeat(a[:, None], W, 1) * 255).astype(np.uint8)
    return Image.fromarray(img, "RGBA")


def grad_bottom(y0, amax):
    ys = np.arange(H, dtype=np.float32)
    a = np.clip((ys - y0) / (H - y0), 0, 1) ** 1.3 * amax
    img = np.zeros((H, W, 4), np.uint8)
    img[..., :3] = (10, 9, 8)
    img[..., 3] = (np.repeat(a[:, None], W, 1) * 255).astype(np.uint8)
    return Image.fromarray(img, "RGBA")


SCRIM = grad_top(1180, 0.86)
LOW = grad_bottom(1300, 0.6)
DARK = Image.new("RGBA", (W, H), (12, 10, 9, 165))


def hook_frame():
    """Gold divider between the two halves and a label on each half."""
    L = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(L)
    d.line([(0, 959), (W, 959)], fill=GOLD, width=4)
    for txt, y in (("1 · YANGI", 868), ("2 · YANGILASH", 990)):
        f = SEMI(30)
        w = f.getlength(txt)
        d.rounded_rectangle((60, y, 60 + w + 48, y + 62), 31, fill=(14, 12, 10, 200), outline=GOLD, width=2)
        d.text((84, y + 13), txt, font=f, fill=CREAM)
    return L


HOOK = hook_frame()
CTA = pill_layer("Izohga NARX yoki YANGILASH yozing", 31, CREAM, GOLD, (14, 12, 10, 190))


def end_card():
    L = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(L)
    f = MED(28)
    t = "IZOHGA YOZING"
    tracked(d, ((W - tw(t, f, 0.32)) / 2, 560), t, f, GOLD, 0.32)
    rows = (("NARX", "yangi kombo va boshqa", "jalyuzilar narxi"), ("YANGILASH", "eski plisse yoki kombo:", "mato yoki yuvish"))
    y = 640
    for kw, a, b in rows:
        fk = SEMI(44)
        wk = fk.getlength(kw)
        d.rounded_rectangle((110, y, 110 + wk + 64, y + 92), 46, fill=GOLD + (255,))
        d.text((142, y + 18), kw, font=fk, fill=INK)
        d.text((110 + wk + 100, y + 4), a, font=SER(40), fill=CREAM)
        d.text((110 + wk + 100, y + 50), b, font=SERI(40), fill=DIM)
        y += 140
    d.line([(W / 2 - 60, 960), (W / 2 + 60, 960)], fill=GOLD, width=2)
    f = SER(72)
    tracked(d, ((W - tw("IMPERIAL", f, 0.2)) / 2, 990), "IMPERIAL", f, CREAM, 0.2)
    f = MED(26)
    t = "PLISSE  ·  KOMBO  ·  TOSHKENT"
    tracked(d, ((W - tw(t, f, 0.32)) / 2, 1080), t, f, GOLD, 0.32)
    t = "Toshkentda o‘lchov va o‘rnatish bepul · 3 kunda tayyor · 1 yil kafolat"
    f = REGF(27)
    d.text(((W - f.getlength(t)) / 2, 1150), t, font=f, fill=DIM)
    t = "Напишите NARX — цены, YANGILASH — обновим старые · @imperial_jalyuzi_uz"
    f = LIT(25)
    d.text(((W - f.getlength(t)) / 2, 1196), t, font=f, fill=DIM)
    return shadow(L)


REGF = lambda s: F("Inter-Regular.otf", s)
END = end_card()


def overlay(t):
    L = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if t < T_END + 0.3:
        L.alpha_composite(alpha(SCRIM, 1 - ease((t - T_END) / 0.3) if t > T_END else 1))
    if t < B1[1]:
        L.alpha_composite(alpha(HOOK, 1 - ease((t - (B1[1] - 0.15)) / 0.15) if t > B1[1] - 0.15 else 1))
    for (t0, t1), lays in LAYERS:
        t1e = t1 - 0.04
        if not (t0 - 0.2 <= t < t1e + 0.01):
            continue
        out = 1 - ease((t - (t1e - 0.22)) / 0.22) if t > t1e - 0.22 else 1
        for lay, y, at in lays:
            p = (t - at) / 0.45
            if p <= 0:
                continue
            L.alpha_composite(alpha(lay, ease(p) * out), (0, y + int(14 * (1 - ease(p)))))
    if CTA_ON <= t < T_END:
        a = ease((t - CTA_ON) / 0.5) * (1 - ease((t - (T_END - 0.3)) / 0.3) if t > T_END - 0.3 else 1)
        L.alpha_composite(alpha(LOW, a))
        pulse = 1 + 0.04 * max(0.0, np.sin((t - CTA_ON) * 2 * np.pi / 3.0)) ** 8
        c = CTA if abs(pulse - 1) < 1e-3 else CTA.resize((int(W * pulse), int(CTA.height * pulse)))
        L.alpha_composite(alpha(c, a), (int((W - c.width) / 2), 1510 - int((c.height - CTA.height) / 2)))
    if t >= T_END:
        a = ease((t - T_END) / 0.5)
        L.alpha_composite(alpha(DARK, a))
        ca = ease((t - T_END - 0.2) / 0.6)
        L.alpha_composite(alpha(END, ca), (0, int(22 * (1 - ca))))
    return L


def job(i):
    overlay(i / FPS).save(f"{OUT}/{i:04d}.png", compress_level=1)


SR = 48000


def bed(path, music=True):
    n = int(SR * (TOTAL + 1.5))
    Lc = np.zeros(n)
    Rc = np.zeros(n)
    rng = np.random.default_rng(5)

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
    x = lp(lp(rng.normal(0, 1, n), 60), 30)
    x /= np.abs(x).max()
    Lc += x * 0.008
    Rc += np.roll(x, 900) * 0.008

    def swish(t0, dur=0.3, v=0.035):
        t = tt(dur)
        nz = rng.normal(0, 1, len(t))
        add((lp(nz, 3) - lp(nz, 22)) * np.sin(np.pi * t / dur) ** 1.5 * v, t0, 0.9, 1.0)

    def piano(m, dur, v):
        t = tt(dur)
        fr = note(m)
        s = sum(np.sin(2 * np.pi * fr * k * t) * np.exp(-t * (0.8 + 1.2 * k)) / k ** 1.4 for k in range(1, 7))
        s = lp(s, 3)
        return s * np.minimum(1, t / 0.006) * np.minimum(1, (dur - t) / 0.25) * v

    def pad(ms, dur, v=0.04):
        t = tt(dur)
        s = sum(np.sin(2 * np.pi * note(m) * t + k) + 0.5 * np.sin(2 * np.pi * note(m) * 1.002 * t) for k, m in enumerate(ms))
        return s * np.minimum(1, t / 0.6) * np.minimum(1, (dur - t) / 0.6) / len(ms) * v

    def kick(t0, v=0.16):
        t = tt(0.45)
        add(np.sin(2 * np.pi * np.cumsum(45 + 55 * np.exp(-t / 0.05)) / SR) * np.exp(-t / 0.16) * v, t0)

    def shaker(t0, v=0.012):
        t = tt(0.07)
        add(lp(rng.normal(0, 1, len(t)), 2) * np.exp(-t / 0.02) * v, t0, 0.7, 1.0)

    for k in ("t1", "l2b", "l2c", "t2", "l3b", "l3c", "t3", "t4"):
        swish(CUT[k] - 0.06)
    if music:
        step = 0.4                                        # 75 BPM eighths
        sections = [(0.0, CUT["t1"], [57, 60, 64, 69], 33), (CUT["t1"], CUT["t2"], [60, 64, 67, 72], 36),
                    (CUT["t2"], CUT["t3"], [65, 69, 72, 77], 41), (CUT["t3"], CUT["t4"], [67, 71, 74, 79], 43),
                    (CUT["t4"], TOTAL, [60, 64, 67, 74], 36)]
        arp = [0, 2, 1, 3, 2, 1, 3, 2]
        for si, (a, b, chd, root) in enumerate(sections):
            d = b - a
            add(pad([m - 12 for m in chd], d + 0.8, 0.045), max(0, a - 0.15))
            add(piano(root + 12, 2.8, 0.1), a)
            for k in range(int(d / step)):
                if si == 4 and k > 7:
                    break
                add(piano(chd[arp[k % 8]] + 12, 1.4, 0.045 + 0.01 * (k % 2 == 0)), a + 0.03 + k * step, 1.0 - 0.15 * (k % 2), 0.85 + 0.15 * (k % 2))
                if si in (1, 2, 3):
                    if k % 4 == 0:
                        kick(a + k * step)
                    if k % 2 == 1:
                        shaker(a + k * step)
    add(piano(88, 2.5, 0.05 if music else 0.035), T_END + 0.35, 0.85, 1.0)
    add(piano(93, 2.5, 0.04 if music else 0.03), T_END + 0.52, 1.0, 0.85)
    m = int(TOTAL * SR)
    Lc, Rc = Lc[:m], Rc[:m]
    wl, wr = np.zeros(m), np.zeros(m)
    for dl, g in ((0.047, 0.28), (0.079, 0.22), (0.121, 0.16), (0.173, 0.1), (0.251, 0.06)):
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
