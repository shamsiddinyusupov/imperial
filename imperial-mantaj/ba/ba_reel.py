"""Dikey jalyuzi «Oldin → keyin» Reel: overlays (450 frames) + rhythmic music, 15 s, 120 BPM."""
import math
import os
import sys
import wave
from multiprocessing import Pool

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H, FPS, TOTAL = 1080, 1920, 30, 15.0
NF = int(TOTAL * FPS)
D = "/home/claude/reels/ba"
OUT = f"{D}/ov"
FI = "/usr/share/fonts/opentype/inter/"
MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
_F = {}


def font(name, size):
    k = (name, size)
    if k not in _F:
        _F[k] = ImageFont.truetype(name if name.startswith("/") else FI + name, size)
    return _F[k]


SEMI = lambda s: font("InterDisplay-SemiBold.otf", s)
BOLD = lambda s: font("InterDisplay-Bold.otf", s) if os.path.exists(FI + "InterDisplay-Bold.otf") else SEMI(s)
MED = lambda s: font("Inter-Medium.otf", s)
REG = lambda s: font("Inter-Regular.otf", s)
MON = lambda s: font(MONO, s)
PAPER, GOLD, INK = (245, 241, 233), (214, 176, 98), (30, 28, 25)

T_DROP, T_END = 4.5, 10.5


def ease(x):
    x = max(0.0, min(1.0, x))
    return 1 - (1 - x) ** 3


def alpha(layer, a):
    if a >= 1:
        return layer
    l2 = layer.copy()
    l2.putalpha(layer.getchannel("A").point(lambda v: int(v * max(0, a))))
    return l2


def shadow(layer, blur=12, a=0.55):
    sh = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    sh.putalpha(layer.getchannel("A").filter(ImageFilter.GaussianBlur(blur)).point(lambda v: int(v * a)))
    out = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    out.alpha_composite(sh, (0, 5))
    out.alpha_composite(layer)
    return out


def tracked(d, xy, text, f, fill, tr=0.14):
    x, y = xy
    for ch in text:
        d.text((x, y), ch, font=f, fill=fill)
        x += f.getlength(ch) + f.size * tr
    return x


def tw(text, f, tr=0.14):
    return sum(f.getlength(c) + f.size * tr for c in text)


def scrim(y0, y1, amax):
    ys = np.arange(H, dtype=np.float32)
    a = np.clip((ys - y0) / (y1 - y0), 0, 1) ** 1.2 * amax
    img = np.zeros((H, W, 4), np.uint8)
    img[..., :3] = (10, 9, 8)
    img[..., 3] = (np.repeat(a[:, None], W, 1) * 255).astype(np.uint8)
    return Image.fromarray(img, "RGBA")


SCRIM_HOOK = scrim(700, 1450, 0.7)
SCRIM_END = scrim(560, 1150, 0.86)


def tag(word):
    f = MON(34)
    w = tw(word, f)
    L = Image.new("RGBA", (int(w) + 60, 72), (0, 0, 0, 0))
    d = ImageDraw.Draw(L)
    d.rounded_rectangle((0, 0, w + 56, 70), 35, fill=(18, 16, 14, 205), outline=GOLD + (230,), width=2)
    tracked(d, (28, 15), word, f, GOLD)
    return L


TAG_OLDIN, TAG_KEYIN = tag("OLDIN"), tag("KEYIN")


def hook():
    L = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(L)
    tracked(d, (86, 1040), "IMPERIAL JALYUZI", MON(30), GOLD)
    y = 1090
    for txt, col in (("Bu deraza", PAPER), ("3 kunda", GOLD), ("o‘zgardi", PAPER)):
        d.text((76, y), txt, font=SEMI(132), fill=col)
        y += 146
    d.text((86, y + 16), "Это окно преобразилось за 3 дня", font=REG(36), fill=(226, 220, 209))
    return shadow(L)


def midlabel():
    L = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(L)
    t2 = "Imperial Jalyuzi · Toshkent"
    w = max(tw("DIKEY JALYUZI", MON(32)), MED(38).getlength(t2))
    d.rounded_rectangle((62, 1520, 62 + w + 52, 1652), 28, fill=(18, 16, 14, 200))
    tracked(d, (88, 1542), "DIKEY JALYUZI", MON(32), GOLD)
    d.text((88, 1588), t2, font=MED(38), fill=PAPER)
    return shadow(L, 10, 0.4)


def endcard():
    L = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(L)
    tracked(d, (86, 960), "DIKEY JALYUZI", MON(32), GOLD)
    # no price in videos (owner, 29.10.2026) — price goes to Direct via the NARX bot
    d.text((80, 1006), "Parda ko‘rinishi,", font=SEMI(96), fill=PAPER)
    d.text((84, 1112), "jalyuzi qulayligi", font=SEMI(72), fill=GOLD)
    y = 1230
    for line in ("Toshkent shahrida o‘lchov va o‘rnatish bepul", "O‘lchovdan keyin 3 kunda tayyor", "1 yil kafolat"):
        cx, cy = 100, y + 24
        d.ellipse((cx - 16, cy - 16, cx + 16, cy + 16), fill=GOLD)
        d.line([(cx - 8, cy), (cx - 2, cy + 7), (cx + 9, cy - 7)], fill=INK, width=4)
        d.text((134, y), line, font=MED(38), fill=PAPER)
        y += 64
    return shadow(L, 10, 0.6)


def cta():
    L = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(L)
    f = SEMI(52)
    t = "Izohga NARX yozing"
    w = f.getlength(t)
    x0, y0 = 84, 1438
    d.rounded_rectangle((x0, y0, x0 + w + 150, y0 + 104), 52, fill=GOLD)
    d.text((x0 + 40, y0 + 22), t, font=f, fill=INK)
    ax, ay = x0 + w + 92, y0 + 52
    d.polygon([(ax - 18, ay - 12), (ax + 18, ay - 12), (ax, ay + 14)], fill=INK)
    d.text((88, y0 + 128), "Напишите NARX — пришлём цены в директ", font=REG(32), fill=(214, 206, 192))
    d.text((88, y0 + 176), "@imperial_jalyuzi_uz", font=MED(32), fill=GOLD)
    return shadow(L, 12, 0.5)


HOOK, MID, END, CTA = hook(), midlabel(), endcard(), cta()


def overlay(t):
    L = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    # tag OLDIN / KEYIN (pop on the drop)
    if t < T_END - 0.1:
        if t < T_DROP:
            L.alpha_composite(TAG_OLDIN, (80, 250))
        else:
            k = ease((t - T_DROP) / 0.25)
            s = 0.6 + 0.4 * k + 0.08 * math.sin(min(1, (t - T_DROP) / 0.35) * math.pi)
            tg = TAG_KEYIN.resize((max(1, int(TAG_KEYIN.width * s)), max(1, int(TAG_KEYIN.height * s))), Image.LANCZOS)
            a = 1 - ease((t - (T_END - 0.4)) / 0.3) if t > T_END - 0.4 else 1
            L.alpha_composite(alpha(tg, a), (80, 250 + (TAG_KEYIN.height - tg.height) // 2))
    # hook
    if t < 3.6:
        a_in = ease((t - 0.05) / 0.35)
        a_out = 1 - ease((t - 3.2) / 0.35) if t > 3.2 else 1
        a = a_in * a_out
        L.alpha_composite(alpha(SCRIM_HOOK, a))
        L.alpha_composite(alpha(HOOK, a), (0, int(30 * (1 - a_in))))
    # small label during the cuts
    if T_DROP + 0.4 < t < T_END:
        a = ease((t - T_DROP - 0.4) / 0.3) * (1 - ease((t - (T_END - 0.3)) / 0.3) if t > T_END - 0.3 else 1)
        L.alpha_composite(alpha(MID, a))
    # end card + CTA
    if t >= T_END:
        a = ease((t - T_END) / 0.4)
        L.alpha_composite(alpha(SCRIM_END, a))
        L.alpha_composite(alpha(END, a), (0, int(40 * (1 - a))))
        if t >= 12.4:
            c = ease((t - 12.4) / 0.35)
            L.alpha_composite(alpha(CTA, c), (0, int(40 * (1 - c))))
    # white flash on the drop
    if T_DROP - 0.02 <= t < T_DROP + 0.25:
        f = 1 - (t - T_DROP + 0.02) / 0.27
        L.alpha_composite(Image.new("RGBA", (W, H), (255, 250, 240, int(150 * max(0, f)))))
    return L


def job(i):
    overlay(i / FPS).save(f"{OUT}/{i:04d}.png", compress_level=1)


# ---------------------------------------------------------------- music, 120 BPM
SR = 48000
BEAT = 0.5


def music(path):
    n = int(SR * (TOTAL + 1.5))
    L = np.zeros(n)
    R = np.zeros(n)
    rng = np.random.default_rng(3)

    def add(sig, t0, gl=1.0, gr=1.0):
        i = int(t0 * SR)
        if i >= n:
            return
        j = min(n, i + len(sig))
        L[i:j] += sig[: j - i] * gl
        R[i:j] += sig[: j - i] * gr

    def tt(d):
        return np.arange(int(d * SR)) / SR

    def kick():
        t = tt(0.32)
        f = 46 + 90 * np.exp(-t / 0.035)
        return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.11) * 0.9

    def clap():
        t = tt(0.22)
        x = rng.normal(0, 1, len(t))
        x = x - np.convolve(x, np.ones(8) / 8, "same")
        env = np.exp(-t / 0.06) * (1 + 0.6 * (np.exp(-((t - 0.012) / 0.004) ** 2) + np.exp(-((t - 0.024) / 0.004) ** 2)))
        return x * env * 0.32

    def hat(open_=False):
        t = tt(0.12 if open_ else 0.04)
        x = rng.normal(0, 1, len(t))
        x = x - np.convolve(x, np.ones(4) / 4, "same")
        return x * np.exp(-t / (0.05 if open_ else 0.012)) * 0.12

    def note(m):
        return 440.0 * 2 ** ((m - 69) / 12)

    def bass(m, d):
        t = tt(d)
        f = note(m)
        s = sum(np.sin(2 * np.pi * f * k * t) / k for k in range(1, 6))
        return s * np.minimum(1, t / 0.01) * np.exp(-t / 0.35) * 0.32

    def pluck(m, d=0.28, v=0.12):
        t = tt(d)
        f = note(m)
        s = np.sin(2 * np.pi * f * t) + 0.4 * np.sin(2 * np.pi * 2 * f * t) * np.exp(-t / 0.05) + 0.15 * np.sign(np.sin(2 * np.pi * f * t))
        return s * np.minimum(1, t / 0.003) * np.exp(-t / 0.09) * v

    def pad(ms, d):
        t = tt(d)
        s = sum(np.sin(2 * np.pi * note(m) * t + k) + np.sin(2 * np.pi * note(m) * 1.004 * t) for k, m in enumerate(ms))
        e = np.minimum(1, t / 0.4) * np.minimum(1, (d - t) / 0.4)
        return s * e / len(ms) * 0.07

    def riser(t0, d):
        t = tt(d)
        x = rng.normal(0, 1, len(t))
        sm = np.convolve(x, np.ones(16) / 16, "same")
        add(sm * (t / d) ** 2 * 0.5, t0)

    def impact(t0):
        t = tt(1.2)
        s = np.sin(2 * np.pi * np.cumsum(38 + 60 * np.exp(-t / 0.08)) / SR) * np.exp(-t / 0.45) * 0.7
        x = rng.normal(0, 1, len(t)) * np.exp(-t / 0.09) * 0.25
        add(s + x, t0)

    # A minor: Am F C G, one chord per bar (2 s)
    chords = [(57, [57, 60, 64, 69]), (53, [53, 57, 60, 65]), (48, [55, 60, 64, 67]), (55, [55, 59, 62, 67])]
    bars = int(math.ceil(TOTAL / 2)) + 1
    for b in range(bars):
        t0 = b * 2.0
        root, tones = chords[b % 4]
        add(pad([m + 12 for m in tones[:3]], 2.2), t0, 0.9, 1.0)
        for k in range(8):                                   # eighth-note pluck arpeggio
            tb = t0 + k * BEAT / 2
            if tb >= TOTAL:
                break
            m = tones[[0, 2, 1, 3, 2, 1, 3, 2][k]] + 12
            v = 0.06 if tb < 1.5 else (0.09 if tb < T_DROP else 0.12)
            pan = 0.35 + 0.3 * (k % 2)
            add(pluck(m, v=v), tb, 1 - pan + 0.35, pan + 0.35)
    for i in range(int(TOTAL / BEAT)):
        tb = i * BEAT
        if 1.5 <= tb < T_DROP:                               # build: kick on 1 and 3, hats
            if i % 2 == 0:
                add(kick() * 0.7, tb)
            add(hat(), tb + BEAT / 2, 0.8, 1.0)
        elif T_DROP <= tb < T_END:                           # drop: four on the floor
            add(kick(), tb)
            if i % 2 == 1:
                add(clap(), tb, 1.0, 0.9)
            add(hat(), tb + BEAT / 2, 0.8, 1.0)
            add(hat(), tb + BEAT / 4, 0.5, 0.6)
            b = int(tb // 2) % 4
            add(bass(chords[b][0] - 12, BEAT * 0.9), tb)
        elif tb >= T_END + 1.0 and tb < TOTAL - 1.0:         # outro: light pulse
            if i % 2 == 0:
                add(kick() * 0.45, tb)
            add(hat() * 0.7, tb + BEAT / 2)
    riser(0.9, 0.6)
    riser(T_DROP - 1.0, 1.0)
    impact(T_DROP)
    impact(T_END)
    n_out = int(TOTAL * SR)
    L, R = L[:n_out], R[:n_out]
    fade = np.minimum(1, (n_out - np.arange(n_out)) / (0.6 * SR)) * np.minimum(1, np.arange(n_out) / (0.03 * SR))
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
    if len(sys.argv) > 1 and sys.argv[1] == "prev":
        for s in sys.argv[2].split(","):
            overlay(float(s)).save(f"{D}/frames/ov_{s}.png")
        sys.exit()
    music(f"{D}/music_ba.wav")
    with Pool(2) as p:
        p.map(job, range(NF), chunksize=10)
    print("frames", NF)
