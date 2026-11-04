"""Plisse «3 xil mato» Reel: overlays (660 frames) + 120 BPM music, 22 s."""
import math
import os
import sys
import wave
from multiprocessing import Pool

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H, FPS = 1080, 1920, 30
BEAT = 0.5
TOTAL = 44 * BEAT          # 22 s
NF = round(TOTAL * FPS)    # 660
SECT = [3.0, 8.0, 13.0]
T_END, T_CTA = 18.0, 19.4
D = "/home/claude/reels/mato"
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
BOLD = lambda s: font("InterDisplay-Bold.otf", s)
MED = lambda s: font("Inter-Medium.otf", s)
REG = lambda s: font("Inter-Regular.otf", s)
MON = lambda s: font(MONO, s)
PAPER, GOLD, INK = (245, 241, 233), (214, 176, 98), (30, 28, 25)
SOFT = (226, 220, 209)
MAXW = 860

FABRICS = [
    ("Yarim shaffof", "Yumshoq yorug‘lik, kunduzi ko‘zdan pana", "130 000", "Полупрозрачная · мягкий свет · 130 000 сум за створку", 1),
    ("Dimout", "Xonani soya qiladi, yorug‘lik xiralashadi", "170 000", "Димаут · приглушённый свет · 170 000 сум за створку", 2),
    ("Blackout", "Mato yorug‘lik o‘tkazmaydi", "200 000", "Блэкаут · не пропускает свет · 200 000 сум за створку", 3),
]
SCALE = ["Shaffof", "Yarim shaffof", "Dimout", "Blackout"]


def fit(text, mk, size, maxw=MAXW):
    while mk(size).getlength(text) > maxw and size > 28:
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


SCRIM = scrim(820, 1500, 0.8)


def badge(d, x, y, n, r=42):
    d.ellipse((x, y, x + 2 * r, y + 2 * r), fill=GOLD)
    f = BOLD(int(r * 1.25))
    t = str(n)
    d.text((x + r - f.getlength(t) / 2, y + r - f.size * 0.62), t, font=f, fill=INK)


def hook():
    L = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(L)
    tracked(d, (86, 1060), "IMPERIAL JALYUZI · PLISSE", MON(30), GOLD)
    f = SEMI(128)
    y = 1104
    for txt, col in (("3 xil mato.", PAPER), ("Qaysi biri", GOLD), ("sizniki?", GOLD)):
        d.text((76, y), txt, font=f, fill=col)
        y += 146
    d.text((86, y + 14), "3 ткани — какая ваша?", font=REG(38), fill=SOFT)
    return shadow(L)


def hook_num(n):
    L = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(L)
    badge(d, 80, 300, n, 56)
    return shadow(L, 10, 0.5)


def section(i):
    name, claim, price, ru, idx = FABRICS[i]
    L = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(L)
    y0 = 1150
    badge(d, 80, y0 + 18, idx, 44)
    tracked(d, (196, y0 + 6), "PLISSE MATOSI", MON(28), GOLD)
    d.text((192, y0 + 40), name, font=fit(name, SEMI, 96, 760), fill=PAPER)
    d.text((86, y0 + 150), claim, font=fit(claim, MED, 40), fill=PAPER)
    pt = "Tabaqasiga " + price + " so‘m"
    fp = SEMI(44)
    d.rounded_rectangle((80, y0 + 212, 80 + fp.getlength(pt) + 56, y0 + 282), 35, fill=(18, 16, 14, 215), outline=GOLD + (255,), width=2)
    d.text((108, y0 + 222), pt, font=fp, fill=GOLD)
    # thickness scale: Shaffof → Blackout (the real order of the four fabric groups)
    sx, sy, sw, gap = 86, y0 + 316, 196, 10
    for k, lab in enumerate(SCALE):
        on = k == idx
        d.rounded_rectangle((sx + k * (sw + gap), sy, sx + k * (sw + gap) + sw, sy + 12), 6, fill=GOLD + (255,) if on else (255, 255, 255, 80))
        fl = MED(24) if on else REG(24)
        d.text((sx + k * (sw + gap), sy + 20), lab, font=fl, fill=GOLD if on else (220, 214, 204))
    d.text((86, y0 + 372), ru, font=fit(ru, REG, 30), fill=(205, 200, 190))
    return shadow(L, 10, 0.6)


def triptych():
    L = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(L)
    for y in (638, 1278):
        d.rectangle((0, y, W, y + 4), fill=PAPER + (255,))
    for (name, _, price, _, idx), py in zip(FABRICS, (440, 1080, 1340)):
        d.rounded_rectangle((60, py, 60 + 560, py + 120), 26, fill=(14, 13, 12, 190))
        badge(d, 78, py + 18, idx, 42)
        d.text((180, py + 14), name, font=SEMI(50), fill=PAPER)
        d.text((182, py + 72), price + " so‘m / tabaqa", font=MED(30), fill=GOLD)
    return shadow(L, 10, 0.45)


def cta():
    L = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(L)
    d.rounded_rectangle((60, 760, W - 60, 1040), 34, fill=(14, 13, 12, 225), outline=GOLD + (255,), width=3)
    f = SEMI(62)
    t1 = "Qaysi biri sizniki?"
    d.text(((W - f.getlength(t1)) / 2, 784), t1, font=f, fill=PAPER)
    f2 = MED(38)
    t2 = "Izohga raqamini yozing: 1, 2 yoki 3"
    d.text(((W - f2.getlength(t2)) / 2, 870), t2, font=f2, fill=GOLD)
    f3 = REG(30)
    t3 = "Narxlar uchun izohga NARX  ·  Напишите NARX — пришлём цены"
    f3 = fit(t3, REG, 30, 900)
    d.text(((W - f3.getlength(t3)) / 2, 940), t3, font=f3, fill=SOFT)
    f4 = MED(26)
    t4 = "Standart uy oynasida, har bir tabaqa uchun"
    d.text(((W - f4.getlength(t4)) / 2, 988), t4, font=f4, fill=(200, 194, 184))
    return shadow(L, 14, 0.5)


HOOK = hook()
NUMS = [hook_num(n) for n in (1, 2, 3)]
SECTIONS = [section(i) for i in range(3)]
TRI, CTA = triptych(), cta()


def overlay(t):
    L = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if t < SECT[0]:
        a = ease((t - 0.03) / 0.3) * (1 - ease((t - (SECT[0] - 0.3)) / 0.28) if t > SECT[0] - 0.3 else 1)
        L.alpha_composite(alpha(SCRIM, a))
        L.alpha_composite(alpha(HOOK, a), (0, int(26 * (1 - ease(t / 0.3)))))
        n = min(2, int(t // 1.0))
        lt = t - n
        k = ease(lt / 0.2)
        L.alpha_composite(alpha(NUMS[n], k * a), (0, int(-20 * (1 - k))))
    for i, t0 in enumerate(SECT):
        t1 = SECT[i + 1] if i + 1 < len(SECT) else T_END
        if t0 <= t < t1:
            lt = t - t0
            a = ease(lt / 0.3) * (1 - ease((t - (t1 - 0.25)) / 0.22) if t > t1 - 0.25 else 1)
            L.alpha_composite(alpha(SCRIM, a))
            L.alpha_composite(alpha(SECTIONS[i], a), (0, int(30 * (1 - ease(lt / 0.35)))))
    if t >= T_END:
        a = ease((t - T_END) / 0.35)
        L.alpha_composite(alpha(TRI, a))
        if t >= T_CTA:
            c = ease((t - T_CTA) / 0.35)
            s = 0.9 + 0.1 * c
            cl = CTA.resize((int(W * s), int(H * s)), Image.LANCZOS) if s < 1 else CTA
            L.alpha_composite(alpha(cl, c), (int(W * (1 - s) / 2), int(H * (1 - s) / 2)))
    for tf in [1.0, 2.0] + SECT + [T_END]:
        if tf - 0.02 <= t < tf + 0.16:
            f = 1 - (t - tf + 0.02) / 0.18
            L.alpha_composite(Image.new("RGBA", (W, H), (255, 250, 240, int(95 * max(0, f)))))
    return L


def job(i):
    overlay(i / FPS).save(f"{OUT}/{i:04d}.png", compress_level=1)


# ---------------------------------------------------------------- music 120 BPM
SR = 48000


def music(path):
    n = int(SR * (TOTAL + 1.5))
    L = np.zeros(n)
    R = np.zeros(n)
    rng = np.random.default_rng(9)

    def add(sig, t0, gl=1.0, gr=1.0):
        i = int(t0 * SR)
        if i >= n or i < 0:
            return
        j = min(n, i + len(sig))
        L[i:j] += sig[: j - i] * gl
        R[i:j] += sig[: j - i] * gr

    tt = lambda d: np.arange(int(d * SR)) / SR
    note = lambda m: 440.0 * 2 ** ((m - 69) / 12)

    def kick(v=0.9):
        t = tt(0.32)
        f = 46 + 90 * np.exp(-t / 0.035)
        return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.11) * v

    def clap(v=0.3):
        t = tt(0.22)
        x = rng.normal(0, 1, len(t))
        x = x - np.convolve(x, np.ones(8) / 8, "same")
        env = np.exp(-t / 0.06) * (1 + 0.6 * (np.exp(-((t - 0.012) / 0.004) ** 2) + np.exp(-((t - 0.024) / 0.004) ** 2)))
        return x * env * v

    def hat(v=0.11, open_=False):
        t = tt(0.12 if open_ else 0.04)
        x = rng.normal(0, 1, len(t))
        x = x - np.convolve(x, np.ones(4) / 4, "same")
        return x * np.exp(-t / (0.05 if open_ else 0.012)) * v

    def bass(m, d, v=0.32):
        t = tt(d)
        f = note(m)
        s = sum(np.sin(2 * np.pi * f * k * t) / k for k in range(1, 6))
        return s * np.minimum(1, t / 0.01) * np.exp(-t / 0.35) * v

    def pluck(m, d=0.3, v=0.11):
        t = tt(d)
        f = note(m)
        s = np.sin(2 * np.pi * f * t) + 0.4 * np.sin(2 * np.pi * 2 * f * t) * np.exp(-t / 0.05) + 0.12 * np.sign(np.sin(2 * np.pi * f * t))
        return s * np.minimum(1, t / 0.003) * np.exp(-t / 0.1) * v

    def pad(ms, d, v=0.06):
        t = tt(d)
        s = sum(np.sin(2 * np.pi * note(m) * t + k) + np.sin(2 * np.pi * note(m) * 1.004 * t) for k, m in enumerate(ms))
        return s * np.minimum(1, t / 0.3) * np.minimum(1, (d - t) / 0.3) / len(ms) * v

    def swish(t0, d=0.35, v=0.25):  # fabric "fwip" on each section change
        t = tt(d)
        x = rng.normal(0, 1, len(t))
        x = np.convolve(x, np.ones(6) / 6, "same")
        add(x * np.sin(np.pi * t / d) ** 2 * v, t0 - d * 0.6, 0.8, 1.0)

    def impact(t0, v=0.55):
        t = tt(1.0)
        s = np.sin(2 * np.pi * np.cumsum(40 + 60 * np.exp(-t / 0.07)) / SR) * np.exp(-t / 0.4) * v
        add(s + rng.normal(0, 1, len(t)) * np.exp(-t / 0.08) * 0.2, t0)

    chords = [(57, [57, 60, 64, 69]), (53, [53, 57, 60, 65]), (48, [55, 60, 64, 67]), (55, [55, 59, 62, 67])]
    arp = [0, 2, 1, 3, 2, 1, 3, 2]
    bars = int(math.ceil(TOTAL / 2)) + 1
    for b in range(bars):
        t0 = b * 2.0
        if t0 >= TOTAL:
            break
        root, tones = chords[b % 4]
        add(pad([m + 12 for m in tones[:3]], 2.2), t0, 0.9, 1.0)
        for k in range(8):
            tb = t0 + k * BEAT / 2
            if tb < TOTAL:
                add(pluck(tones[arp[k]] + 12, v=0.09 if tb >= T_END else 0.11), tb, 0.65 + 0.3 * (k % 2), 0.95 - 0.3 * (k % 2))
    for i in range(int(TOTAL / BEAT)):
        tb = i * BEAT
        b = int(tb // 2) % 4
        if tb < SECT[0]:
            add(kick(0.75), tb)
            add(hat(0.09), tb + BEAT / 2)
            if i % 2 == 1:
                add(clap(0.2), tb)
        elif tb < T_END:
            add(kick(), tb)
            if i % 2 == 1:
                add(clap(), tb, 1.0, 0.9)
            add(hat(), tb + BEAT / 2, 0.8, 1.0)
            add(hat(0.06), tb + BEAT / 4, 0.5, 0.6)
            add(bass(chords[b][0] - 12, BEAT * 0.9), tb)
        else:
            if i % 2 == 0:
                add(kick(0.55), tb)
            add(hat(0.07), tb + BEAT / 2)
            if i % 4 == 0:
                add(bass(chords[b][0] - 12, BEAT * 1.6, 0.25), tb)
    for t0 in [1.0, 2.0] + SECT + [T_END]:
        swish(t0, 0.3 if t0 < SECT[0] else 0.4, 0.16 if t0 < SECT[0] else 0.24)
    for t0 in SECT:
        impact(t0, 0.35)
    impact(T_END, 0.45)
    n_out = int(TOTAL * SR)
    L, R = L[:n_out], R[:n_out]
    fadev = np.minimum(1, (n_out - np.arange(n_out)) / (0.8 * SR)) * np.minimum(1, np.arange(n_out) / (0.02 * SR))
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
    os.makedirs(f"{D}/frames", exist_ok=True)
    if len(sys.argv) > 1 and sys.argv[1] == "prev":
        for s in sys.argv[2].split(","):
            overlay(float(s)).save(f"{D}/frames/ov_{s}.png")
        sys.exit()
    music(f"{D}/music_mato.wav")
    with Pool(2) as p:
        p.map(job, range(NF), chunksize=12)
    print("frames", NF)
