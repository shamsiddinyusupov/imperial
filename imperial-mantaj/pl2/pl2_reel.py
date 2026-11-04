"""Plisse mood Reel: overlays (396 frames) + soft 100 BPM music, 13.2 s."""
import math
import os
import sys
import wave
from multiprocessing import Pool

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H, FPS = 1080, 1920, 30
BEAT = 0.6
TOTAL = 22 * BEAT            # 13.2 s
NF = round(TOTAL * FPS)      # 396
T_DROP, T_END, T_CTA = 3.0, 7.8, 9.9
D = "/home/claude/reels/pl2"
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
MED = lambda s: font("Inter-Medium.otf", s)
REG = lambda s: font("Inter-Regular.otf", s)
MON = lambda s: font(MONO, s)
PAPER, GOLD, INK = (245, 241, 233), (214, 176, 98), (30, 28, 25)
MAXW = 850


def fit(text, mk, size, maxw=MAXW):
    while mk(size).getlength(text) > maxw and size > 40:
        size -= 2
    return mk(size)


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


def scrim(y0, y1, amax):
    ys = np.arange(H, dtype=np.float32)
    a = np.clip((ys - y0) / (y1 - y0), 0, 1) ** 1.2 * amax
    img = np.zeros((H, W, 4), np.uint8)
    img[..., :3] = (10, 9, 8)
    img[..., 3] = (np.repeat(a[:, None], W, 1) * 255).astype(np.uint8)
    return Image.fromarray(img, "RGBA")


SCRIM_HOOK = scrim(700, 1450, 0.72)
SCRIM_WORD = scrim(780, 1380, 0.72)
SCRIM_END = scrim(560, 1150, 0.86)


def hook():
    L = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(L)
    tracked(d, (86, 1040), "IMPERIAL JALYUZI · PLISSE", MON(30), GOLD)
    lines = (("Yorug‘lik kiradi,", PAPER), ("begona nigoh", GOLD), ("kirmaydi", PAPER))
    f = min((fit(t, SEMI, 124) for t, _ in lines), key=lambda f: f.size)
    y = 1088
    for txt, col in lines:
        d.text((76, y), txt, font=f, fill=col)
        y += int(f.size * 1.16)
    d.text((86, y + 16), "Свет — есть, чужих взглядов — нет", font=REG(36), fill=(226, 220, 209))
    return shadow(L)


WORDS = [
    ("Yumshoq yorug‘lik", "Мягкий свет"),
    ("Ko‘zdan pana", "Без чужих взглядов"),
    ("Har bir tabaqaga", "На каждую створку"),
    ("3 kunda tayyor", "Готово за 3 дня"),
]


def word_layer(i):
    uz, ru = WORDS[i]
    L = Image.new("RGBA", (W, 330), (0, 0, 0, 0))
    d = ImageDraw.Draw(L)
    tracked(d, (88, 0), f"0{i + 1} / 04", MON(34), GOLD)
    f = fit(uz, SEMI, 104)
    d.text((80, 50), uz, font=f, fill=PAPER)
    d.text((88, 50 + int(f.size * 1.2)), ru, font=REG(38), fill=(226, 220, 209))
    return shadow(L, 10, 0.6)


WORD_L = [word_layer(i) for i in range(4)]


def endcard():
    L = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(L)
    tracked(d, (86, 940), "PLISSE JALYUZI", MON(32), GOLD)
    d.text((86, 986), "Standart uy oynasida tabaqasiga", font=MED(40), fill=(232, 226, 214))
    f = fit("100 000 so‘mdan", SEMI, 116)
    d.text((80, 1040), "100 000 so‘mdan", font=f, fill=PAPER)
    y = 1040 + int(f.size * 1.25) + 6
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
    x0, y0 = 84, 1440
    d.rounded_rectangle((x0, y0, x0 + w + 150, y0 + 104), 52, fill=GOLD)
    d.text((x0 + 40, y0 + 22), t, font=f, fill=INK)
    ax, ay = x0 + w + 92, y0 + 52
    d.polygon([(ax - 18, ay - 12), (ax + 18, ay - 12), (ax, ay + 14)], fill=INK)
    d.text((88, y0 + 128), "Напишите NARX — пришлём цены в директ", font=REG(32), fill=(214, 206, 192))
    d.text((88, y0 + 176), "@imperial_jalyuzi_uz", font=MED(32), fill=GOLD)
    return shadow(L, 12, 0.5)


HOOK, END, CTA = hook(), endcard(), cta()


def overlay(t):
    L = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if t < T_DROP + 0.1:
        a_in = ease((t - 0.05) / 0.35)
        a_out = 1 - ease((t - (T_DROP - 0.35)) / 0.3) if t > T_DROP - 0.35 else 1
        a = a_in * a_out
        L.alpha_composite(alpha(SCRIM_HOOK, a))
        L.alpha_composite(alpha(HOOK, a), (0, int(30 * (1 - a_in))))
    if T_DROP <= t < T_END:
        k = int((t - T_DROP) // (2 * BEAT))
        lt = t - T_DROP - k * 2 * BEAT
        a = ease(lt / 0.18) * (1 - ease((lt - 1.02) / 0.16) if lt > 1.02 else 1)
        L.alpha_composite(alpha(SCRIM_WORD, 1 if 0.1 < t - T_DROP < T_END - T_DROP - 0.1 else 0.6))
        wl = WORD_L[min(k, 3)]
        s = 0.92 + 0.08 * ease(lt / 0.25)
        if s < 1:
            wl2 = wl.resize((int(W * s), int(wl.height * s)), Image.LANCZOS)
        else:
            wl2 = wl
        L.alpha_composite(alpha(wl2, a), (int(80 * (1 - s)), 1160 + int(24 * (1 - ease(lt / 0.25)))))
    if t >= T_END:
        a = ease((t - T_END) / 0.4)
        L.alpha_composite(alpha(SCRIM_END, a))
        L.alpha_composite(alpha(END, a), (0, int(40 * (1 - a))))
        if t >= T_CTA:
            c = ease((t - T_CTA) / 0.35)
            L.alpha_composite(alpha(CTA, c), (0, int(40 * (1 - c))))
    if T_DROP - 0.02 <= t < T_DROP + 0.22:
        f = 1 - (t - T_DROP + 0.02) / 0.24
        L.alpha_composite(Image.new("RGBA", (W, H), (255, 250, 240, int(110 * max(0, f)))))
    return L


def job(i):
    overlay(i / FPS).save(f"{OUT}/{i:04d}.png", compress_level=1)


# ---------------------------------------------------------------- music, 100 BPM, warm
SR = 48000


def music(path):
    n = int(SR * (TOTAL + 2))
    L = np.zeros(n)
    R = np.zeros(n)
    rng = np.random.default_rng(11)

    def add(sig, t0, gl=1.0, gr=1.0):
        i = int(t0 * SR)
        if i >= n:
            return
        j = min(n, i + len(sig))
        L[i:j] += sig[: j - i] * gl
        R[i:j] += sig[: j - i] * gr

    tt = lambda d: np.arange(int(d * SR)) / SR
    note = lambda m: 440.0 * 2 ** ((m - 69) / 12)

    def kick(v=0.8):
        t = tt(0.35)
        f = 44 + 70 * np.exp(-t / 0.04)
        return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.13) * v

    def clap(v=0.22):
        t = tt(0.25)
        x = rng.normal(0, 1, len(t))
        x = x - np.convolve(x, np.ones(10) / 10, "same")
        env = np.exp(-t / 0.08) * (1 + 0.5 * (np.exp(-((t - 0.012) / 0.004) ** 2) + np.exp(-((t - 0.024) / 0.004) ** 2)))
        return x * env * v

    def shaker(v=0.06):
        t = tt(0.06)
        x = rng.normal(0, 1, len(t))
        x = x - np.convolve(x, np.ones(3) / 3, "same")
        return x * np.sin(np.pi * np.minimum(1, t / 0.06)) * v

    def rhodes(m, d, v=0.07):
        t = tt(d)
        f = note(m)
        s = np.sin(2 * np.pi * f * t + 0.8 * np.sin(2 * np.pi * f * t) * np.exp(-t / 0.4))
        s += 0.25 * np.sin(2 * np.pi * 2 * f * t) * np.exp(-t / 0.25)
        trem = 1 + 0.15 * np.sin(2 * np.pi * 4.5 * t)
        e = np.minimum(1, t / 0.006) * np.exp(-t / 1.1) * np.minimum(1, (d - t) / 0.08)
        return s * e * trem * v

    def bass(m, d, v=0.3):
        t = tt(d)
        f = note(m)
        s = np.sin(2 * np.pi * f * t) + 0.3 * np.sin(2 * np.pi * 2 * f * t)
        return s * np.minimum(1, t / 0.01) * np.exp(-t / 0.5) * np.minimum(1, (d - t) / 0.03) * v

    def bell(m, v=0.05):
        t = tt(0.9)
        f = note(m)
        s = np.sin(2 * np.pi * f * t) + 0.3 * np.sin(2 * np.pi * 3.01 * f * t) * np.exp(-t / 0.2)
        return s * np.minimum(1, t / 0.002) * np.exp(-t / 0.35) * v

    def swell(t0, d, v=0.35):
        t = tt(d)
        x = np.convolve(rng.normal(0, 1, len(t)), np.ones(24) / 24, "same")
        add(x * (t / d) ** 2.2 * v, t0)

    bar = 4 * BEAT
    # Fmaj7 - Em7 - Dm7 - Cmaj7 (warm, descending)
    chords = [(41, [53, 57, 60, 64]), (40, [52, 55, 59, 62]), (38, [50, 53, 57, 60]), (36, [48, 52, 55, 59])]
    nbar = int(math.ceil(TOTAL / bar)) + 1
    for b in range(nbar):
        t0 = b * bar
        root, tones = chords[b % 4]
        for k, m in enumerate(tones):
            add(rhodes(m + 12, bar + 0.2, 0.06), t0 + 0.012 * k, 0.9 + 0.1 * (k % 2), 1.0 - 0.1 * (k % 2))
        add(rhodes(tones[2] + 12, BEAT * 1.5, 0.045), t0 + 2.5 * BEAT, 1.0, 0.8)   # off-beat comp
        if t0 >= T_DROP - 0.01:
            add(bass(root, BEAT * 1.4), t0)
            add(bass(root, BEAT * 0.5, 0.22), t0 + 1.5 * BEAT)
            add(bass(root + 7, BEAT * 0.9, 0.24), t0 + 2.5 * BEAT)
    # melody bells over the cuts, on the word changes
    for k, m in enumerate([76, 74, 72, 71]):
        add(bell(m), T_DROP + k * 2 * BEAT, 0.8, 1.0)
        add(bell(m - 5, 0.03), T_DROP + k * 2 * BEAT + BEAT, 1.0, 0.8)
    nb = int(round(TOTAL / BEAT))
    for i in range(nb):
        tb = i * BEAT
        if tb < T_DROP:
            add(shaker(0.03), tb + BEAT / 2, 0.8, 1.0)
            continue
        out = tb >= TOTAL - 1.2
        add(kick(0.55 if out else 0.8), tb)
        if i % 2 == 1:
            add(clap(0.14 if tb >= T_END else 0.22), tb, 1.0, 0.9)
        for q in (0.25, 0.5, 0.75):
            add(shaker(0.07 if q == 0.5 else 0.04), tb + q * BEAT, 0.75, 1.0)
    swell(T_DROP - 1.2, 1.2)
    n_out = int(TOTAL * SR)
    L, R = L[:n_out], R[:n_out]
    # gentle room: short multi-tap echo
    for dl, g in ((0.031, 0.25), (0.053, 0.18), (0.089, 0.12)):
        s = int(dl * SR)
        L[s:] += R[:-s] * g
        R[s:] += L[:-s] * g * 0.9
    fade = np.minimum(1, (n_out - np.arange(n_out)) / (0.7 * SR)) * np.minimum(1, np.arange(n_out) / (0.03 * SR))
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
    music(f"{D}/music_pl2.wav")
    with Pool(2) as p:
        p.map(job, range(NF), chunksize=10)
    print("frames", NF)
