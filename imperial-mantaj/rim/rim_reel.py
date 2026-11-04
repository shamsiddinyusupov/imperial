"""Rimskiy shtora Reel: overlays + soft 100 BPM music, 18.6 s."""
import math
import os
import sys
import wave
from multiprocessing import Pool

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H, FPS = 1080, 1920, 30
BEAT = 0.6
TOTAL = 32 * BEAT            # 19.2 s
NF = round(TOTAL * FPS)      # 576
T_DROP, T_W2, T_W3, T_END, T_CTA = 3.0, 6.6, 10.8, 13.2, 15.3
D = "/home/claude/reels/rim"
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
SOFT = (226, 220, 209)
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


SCRIM_HOOK = scrim(700, 1450, 0.74)
SCRIM_WORD = scrim(1120, 1660, 0.74)
SCRIM_END = scrim(520, 1100, 0.88)


def hook():
    L = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(L)
    tracked(d, (86, 1080), "IMPERIAL JALYUZI", MON(30), GOLD)
    lines = (("Oshxonangizga", PAPER), ("rimskiy shtora", GOLD))
    f = min((fit(t, SEMI, 128) for t, _ in lines), key=lambda f: f.size)
    y = 1128
    for txt, col in lines:
        d.text((76, y), txt, font=f, fill=col)
        y += int(f.size * 1.16)
    d.text((86, y + 18), "Римская штора на кухню", font=REG(38), fill=SOFT)
    return shadow(L)


WORDS = [
    ("Yumshoq taxlamlar", "Мягкие складки"),
    ("Tekis va toza ko‘rinish", "Ровный, аккуратный вид"),
    ("Uyga shinamlik", "Уют в доме"),
]


def word_layer(i):
    uz, ru = WORDS[i]
    L = Image.new("RGBA", (W, 330), (0, 0, 0, 0))
    d = ImageDraw.Draw(L)
    tracked(d, (88, 0), f"0{i + 1} / 03", MON(34), GOLD)
    f = fit(uz, SEMI, 104)
    d.text((80, 50), uz, font=f, fill=PAPER)
    d.text((88, 50 + int(f.size * 1.2)), ru, font=REG(38), fill=SOFT)
    return shadow(L, 10, 0.6)


WORD_L = [word_layer(i) for i in range(3)]


def check(d, y, line):
    cx, cy = 100, y + 24
    d.ellipse((cx - 16, cy - 16, cx + 16, cy + 16), fill=GOLD)
    d.line([(cx - 8, cy), (cx - 2, cy + 7), (cx + 9, cy - 7)], fill=INK, width=4)
    d.text((134, y), line, font=MED(38), fill=PAPER)


def endcard():
    L = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(L)
    tracked(d, (86, 900), "RIMSKIY SHTORA", MON(32), GOLD)
    f = fit("o‘lchab tayyorlaymiz", SEMI, 100)
    d.text((80, 946), "Har bir derazaga", font=f, fill=PAPER)
    d.text((80, 946 + int(f.size * 1.16)), "o‘lchab tayyorlaymiz", font=f, fill=GOLD)
    y = 946 + int(f.size * 2.4) + 10
    for line in ("Toshkent shahrida o‘lchov va o‘rnatish bepul", "1 yil kafolat", "Click, Payme, karta yoki naqd"):
        check(d, y, line)
        y += 64
    return shadow(L, 10, 0.6)


def cta():
    L = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(L)
    f = SEMI(52)
    t = "Direktga yozing"
    w = f.getlength(t)
    x0, y0 = 84, 1404
    d.rounded_rectangle((x0, y0, x0 + w + 150, y0 + 104), 52, fill=GOLD)
    d.text((x0 + 40, y0 + 22), t, font=f, fill=INK)
    ax, ay = x0 + w + 92, y0 + 52
    d.polygon([(ax - 12, ay - 18), (ax - 12, ay + 18), (ax + 14, ay)], fill=INK)
    d.text((88, y0 + 128), "Deraza rasmini yuboring — narxini aytamiz", font=MED(34), fill=PAPER)
    d.text((88, y0 + 172), "Пришлите фото окна — назовём цену", font=REG(30), fill=(214, 206, 192))
    d.text((88, y0 + 212), "@imperial_jalyuzi_uz", font=MED(30), fill=GOLD)
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
    seg = None
    if T_DROP <= t < T_W2:
        seg = (WORD_L[0], t - T_DROP, T_W2 - T_DROP)
    elif T_W2 <= t < T_W3:
        seg = (WORD_L[1], t - T_W2, T_W3 - T_W2)
    elif T_W3 <= t < T_END:
        seg = (WORD_L[2], t - T_W3, T_END - T_W3)
    if seg:
        wl, lt, dur = seg
        a = ease(lt / 0.18) * (1 - ease((lt - (dur - 0.18)) / 0.16) if lt > dur - 0.18 else 1)
        L.alpha_composite(alpha(SCRIM_WORD, 1 if 0.1 < t - T_DROP < T_END - T_DROP - 0.1 else 0.6))
        s = 0.92 + 0.08 * ease(lt / 0.25)
        wl2 = wl.resize((int(W * s), int(wl.height * s)), Image.LANCZOS) if s < 1 else wl
        L.alpha_composite(alpha(wl2, a), (int(80 * (1 - s)), 1424 + int(24 * (1 - ease(lt / 0.25)))))
    if t >= T_END:
        a = ease((t - T_END) / 0.4)
        L.alpha_composite(alpha(SCRIM_END, a))
        L.alpha_composite(alpha(END, a), (0, int(40 * (1 - a))))
        if t >= T_CTA:
            c = ease((t - T_CTA) / 0.35)
            L.alpha_composite(alpha(CTA, c), (0, int(40 * (1 - c))))
    if T_DROP - 0.02 <= t < T_DROP + 0.22:
        f = 1 - (t - T_DROP + 0.02) / 0.24
        L.alpha_composite(Image.new("RGBA", (W, H), (255, 250, 240, int(100 * max(0, f)))))
    return L


def job(i):
    overlay(i / FPS).save(f"{OUT}/{i:04d}.png", compress_level=1)


# ---------------------------------------------------------------- music, 100 BPM, warm
SR = 48000


def music(path):
    n = int(SR * (TOTAL + 2))
    L = np.zeros(n)
    R = np.zeros(n)
    rng = np.random.default_rng(21)

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

    def rim(v=0.12):
        t = tt(0.08)
        x = rng.normal(0, 1, len(t))
        x = x - np.convolve(x, np.ones(5) / 5, "same")
        tone = np.sin(2 * np.pi * 1700 * t) * np.exp(-t / 0.015)
        return (x * np.exp(-t / 0.02) * 0.6 + tone * 0.5) * v

    def shaker(v=0.06):
        t = tt(0.06)
        x = rng.normal(0, 1, len(t))
        x = x - np.convolve(x, np.ones(3) / 3, "same")
        return x * np.sin(np.pi * np.minimum(1, t / 0.06)) * v

    def piano(m, d, v=0.07):
        t = tt(d)
        f = note(m)
        s = sum(np.sin(2 * np.pi * f * k * t) * np.exp(-t * (1.2 + 1.6 * k)) / k ** 1.3 for k in range(1, 6))
        e = np.minimum(1, t / 0.004) * np.minimum(1, (d - t) / 0.1)
        return s * e * v

    def pad(ms, d, v=0.05):
        t = tt(d)
        s = sum(np.sin(2 * np.pi * note(m) * t + k) + 0.6 * np.sin(2 * np.pi * note(m) * 1.003 * t) for k, m in enumerate(ms))
        e = np.minimum(1, t / 0.5) * np.minimum(1, (d - t) / 0.5)
        return s * e / len(ms) * v

    def bass(m, d, v=0.3):
        t = tt(d)
        f = note(m)
        s = np.sin(2 * np.pi * f * t) + 0.3 * np.sin(2 * np.pi * 2 * f * t)
        return s * np.minimum(1, t / 0.01) * np.exp(-t / 0.5) * np.minimum(1, (d - t) / 0.03) * v

    def swell(t0, d, v=0.3):
        t = tt(d)
        x = np.convolve(rng.normal(0, 1, len(t)), np.ones(24) / 24, "same")
        add(x * (t / d) ** 2.2 * v, t0)

    bar = 4 * BEAT
    # Cmaj9 - Am7 - Fmaj7 - G6 : soft kitchen-morning feel
    chords = [(36, [60, 64, 67, 71, 74]), (33, [57, 60, 64, 67, 72]), (29, [57, 60, 64, 65, 69]), (31, [55, 59, 62, 64, 67])]
    nbar = int(math.ceil(TOTAL / bar)) + 1
    arp = [0, 2, 4, 1, 3, 2, 4, 1]
    for b in range(nbar):
        t0 = b * bar
        root, tones = chords[b % 4]
        add(pad(tones[:4], bar + 0.4), t0, 0.95, 1.0)
        for k in range(8):
            tb = t0 + k * BEAT / 2
            if tb >= TOTAL:
                break
            v = 0.05 if tb < T_DROP else 0.065
            add(piano(tones[arp[k]] + 12, 0.9, v), tb, 1.0 - 0.15 * (k % 2), 0.85 + 0.15 * (k % 2))
        if t0 >= T_DROP - 0.01:
            add(bass(root + 12, BEAT * 1.4), t0)
            add(bass(root + 12, BEAT * 0.5, 0.2), t0 + 1.5 * BEAT)
            add(bass(root + 19, BEAT * 0.9, 0.22), t0 + 2.5 * BEAT)
    nb = int(round(TOTAL / BEAT))
    for i in range(nb):
        tb = i * BEAT
        if tb < T_DROP:
            add(shaker(0.03), tb + BEAT / 2, 0.8, 1.0)
            continue
        soft = tb >= T_END
        add(kick(0.6 if soft else 0.75), tb)
        if i % 2 == 1:
            add(rim(0.1 if soft else 0.14), tb, 1.0, 0.85)
        for q in (0.25, 0.5, 0.75):
            add(shaker(0.065 if q == 0.5 else 0.035), tb + q * BEAT, 0.75, 1.0)
    swell(T_DROP - 1.2, 1.2, 0.25)
    swell(T_END - 1.2, 1.2, 0.2)
    n_out = int(TOTAL * SR)
    L, R = L[:n_out], R[:n_out]
    for dl, g in ((0.029, 0.25), (0.047, 0.18), (0.083, 0.12)):
        s = int(dl * SR)
        L[s:] += R[:-s] * g
        R[s:] += L[:-s] * g * 0.9
    fade = np.minimum(1, (n_out - np.arange(n_out)) / (0.8 * SR)) * np.minimum(1, np.arange(n_out) / (0.03 * SR))
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
    music(f"{D}/music_rim.wav")
    with Pool(2) as p:
        p.map(job, range(NF), chunksize=10)
    print("frames", NF)
