"""«Imperial — kino treyleri»: own footage only, hard cuts, black title cards, letterbox, original trailer sound
(drone, braams, deep booms, riser, a silence beat, choir pad on the title). Silent-friendly: the cards tell the story.

python3 build.py [overlay|sound|final|all]
"""
import os
import subprocess
import sys
import wave

import numpy as np
from PIL import Image, ImageDraw
from scipy.signal import butter, fftconvolve, lfilter

sys.path.insert(0, "/home/claude/reels/common")
sys.path.insert(0, "/home/claude/reels/dikey_style")
from faqat_qarang import DID, ITA, LAB, LIG, RU, soft_shadow, sweep, text_img  # noqa: E402

D = "/home/claude/reels/trailer"
W, H, FPS, SR = 1080, 1920, 30, 48000
BAR = 170
# (kind, name, t0, t1): kind 'card' = black, 'shot' = seg/<name>.mp4 from its start
TL = [("card", "C0", 0.0, 1.8), ("shot", "S1", 1.8, 4.7), ("card", "C1", 4.7, 5.9), ("shot", "S2", 5.9, 8.6),
      ("card", "C2", 8.6, 9.8), ("shot", "S3", 9.8, 11.3), ("shot", "S4", 11.3, 12.8), ("shot", "S5", 12.8, 14.3),
      ("shot", "S6", 14.3, 18.4), ("card", "SIL", 18.4, 18.8), ("shot", "S7", 18.8, 20.9), ("card", "END", 20.9, 26.4)]
TOTAL = TL[-1][3]
CREAM, CARAMEL, DIM = (240, 232, 218), (204, 170, 124), (150, 142, 130)
PAD = 24
WORDS = {"S3": "Yorug‘lik.", "S4": "Sokinlik.", "S5": "Did."}


def ease(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


def fade(L, a):
    if a >= 1:
        return L
    o = L.copy()
    o.putalpha(L.getchannel("A").point(lambda v: int(v * max(0.0, a))))
    return o


def centre(L, im, y):
    L.alpha_composite(im, ((W - im.width) // 2, int(y) - PAD))


class Ov:
    def __init__(self):
        self.c0 = text_img("IMPERIAL  TAQDIM  ETADI", LAB(30), CARAMEL, 0.55)
        self.c1 = text_img("Har bir derazaning…", ITA(70), CREAM)
        self.c2 = text_img("…o‘z hikoyasi bor.", ITA(70), CREAM)
        self.words = {k: soft_shadow(soft_shadow(text_img(v, DID(132), CREAM), 26, 0.7), 10, 0.5) for k, v in WORDS.items()}
        self.imp = text_img("IMPERIAL", DID(150), CREAM, 0.16)
        self.jal = text_img("JALYUZI", LAB(26), CARAMEL, 0.9)
        self.f1 = text_img("Toshkentda o‘lchov va o‘rnatish bepul  ·  1 yil kafolat", LIG(28), DIM)
        self.cta = text_img("Izohga NARX yozing — narxlarni direktga yuboramiz", ITA(40), CREAM)
        self.ru = text_img("Напишите NARX — пришлём цены в директ", RU(28), DIM)

    def frame(self, t):
        L = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        kind, name, t0, t1 = next(s for s in TL if s[2] <= t < s[3]) if t < TOTAL else TL[-1]
        u = t - t0
        d = t1 - t0
        if kind == "shot":                                     # letterbox bars + hit words
            dr = ImageDraw.Draw(L)
            if name in self.words:                             # dim the bright fabric so the word reads
                dr.rectangle((0, BAR, W, H - BAR), fill=(14, 10, 6, 105))
            dr.rectangle((0, 0, W, BAR), fill=(0, 0, 0, 255))
            dr.rectangle((0, H - BAR, W, H), fill=(0, 0, 0, 255))
            if name in self.words:
                a = min(ease(u / 0.12), 1 - ease((u - (d - 0.25)) / 0.25))
                centre(L, fade(self.words[name], a), 880)
            return L
        if name == "C0":
            centre(L, fade(self.c0, min(ease((u - 0.3) / 0.5), 1 - ease((u - 1.35) / 0.4))), 945)
        elif name == "C1":
            centre(L, fade(self.c1, min(ease(u / 0.3), 1 - ease((u - 0.95) / 0.25))), 920)
        elif name == "C2":
            centre(L, fade(self.c2, min(ease(u / 0.3), 1 - ease((u - 0.95) / 0.25))), 920)
        elif name == "END":
            a = ease(u / 0.35)
            imp = sweep(self.imp, (u - 0.9) / 1.2) if 0.9 < u < 2.1 else self.imp
            centre(L, fade(imp, a), 740)
            centre(L, fade(self.jal, ease((u - 0.4) / 0.5)), 935)
            dr = ImageDraw.Draw(L)
            hl = ease((u - 0.7) / 0.6)
            if hl > 0:
                dr.line([(W // 2 - int(70 * hl), 1010), (W // 2 + int(70 * hl), 1010)], fill=CARAMEL + (255,), width=2)
            centre(L, fade(self.f1, ease((u - 1.2) / 0.5)), 1045)
            centre(L, fade(self.cta, ease((u - 1.8) / 0.5)), 1400)
            centre(L, fade(self.ru, ease((u - 2.1) / 0.5)), 1470)
            if u > d - 0.6:
                return fade(L, 1 - ease((u - (d - 0.6)) / 0.6))
        return L


def overlay():
    os.makedirs(f"{D}/ov", exist_ok=True)
    ov = Ov()
    n = round(TOTAL * FPS)
    p = subprocess.Popen(["ffmpeg", "-nostdin", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-c:v", "prores_ks", "-profile:v", "4444", "-pix_fmt", "yuva444p10le",
                          f"{D}/ov/titles.mov"], stdin=subprocess.PIPE)
    for i in range(n):
        p.stdin.write(ov.frame(i / FPS).tobytes())
    p.stdin.close()
    p.wait()
    print("overlay ok")


# ---------------------------------------------------------------- sound
def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def lp(x, f, order=2):
    b, a = butter(order, f / (SR / 2), "low")
    return lfilter(b, a, x)


def saw(f, t):
    return 2 * ((f * t) % 1.0) - 1


def braam(notes, dur, open_t=0.5):
    t = np.arange(int(dur * SR)) / SR
    y = sum(saw(hz(m) * (1 + d), t) for m in notes for d in (-0.003, 0.003))
    # filter opens then closes: approximate with two lowpasses blended over time
    lo, hi = lp(y, 220, 2), lp(y, 1400, 2)
    k = np.clip(t / open_t, 0, 1) * np.exp(-np.clip(t - open_t, 0, None) / 0.9)
    y = lo * (1 - k) + hi * k
    y = np.tanh(1.6 * y / (np.abs(y).max() + 1e-9))
    env = (1 - np.exp(-t / 0.06)) * np.exp(-t / 1.3)
    return y * env


def boom(dur=2.4, big=1.0):
    t = np.arange(int(dur * SR)) / SR
    f = 34 + 40 * np.exp(-t / 0.08)
    y = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / (0.9 * big))
    rng = np.random.default_rng(int(big * 10))
    y += lp(rng.normal(0, 1, len(t)), 900) * np.exp(-t / 0.05) * 0.6
    return np.tanh(1.4 * y)


def swell(dur=0.45, seed=1):
    rng = np.random.default_rng(seed)
    t = np.arange(int(dur * SR)) / SR
    y = lp(rng.normal(0, 1, len(t)), 2500) * (t / dur) ** 3
    return y / (np.abs(y).max() + 1e-9)


def riser(dur):
    rng = np.random.default_rng(7)
    t = np.arange(int(dur * SR)) / SR
    u = t / dur
    noise = rng.normal(0, 1, len(t))
    out = np.zeros_like(t)
    for k in range(6):                                    # stepped band sweep
        f0 = 300 * 2 ** (k / 1.5)
        b, a = butter(2, [min(f0 * (1 + 3 * u.mean()), 9000) / (SR / 2) * 0.5, min(f0 * 4, 20000) / (SR / 2)], "band")
        out += lfilter(b, a, noise) * (u ** (1.5 + 0.3 * k))
    gl = sum(np.sin(2 * np.pi * np.cumsum(hz(50 + 12 * o) * 2 ** (2.5 * u)) / SR) for o in range(3)) * u ** 2
    y = out / (np.abs(out).max() + 1e-9) * 0.7 + gl / 3 * 0.5
    return y * u ** 1.5


def choir(notes, dur, att=1.2, rel=2.0):
    t = np.arange(int(dur * SR)) / SR
    y = np.zeros_like(t)
    for m in notes:
        for d in (-0.004, 0.0, 0.004):
            vib = 1 + 0.004 * np.sin(2 * np.pi * 5.2 * t + m)
            y += saw(1, np.cumsum(hz(m) * (1 + d) * vib) / SR)
    out = np.zeros_like(y)
    for f, g, bw in ((800, 1.0, 120), (1150, 0.6, 140), (2900, 0.25, 220)):   # vowel «a»
        b, a = butter(2, [(f - bw) / (SR / 2), (f + bw) / (SR / 2)], "band")
        out += lfilter(b, a, y) * g
    env = np.minimum(1, t / att) * np.clip((dur - t) / rel, 0, 1)
    return out / (np.abs(out).max() + 1e-9) * env


def hall(seed, secs=3.0):
    r = np.random.default_rng(seed)
    t = np.arange(int(secs * SR)) / SR
    ir = r.normal(0, 1, len(t)) * np.exp(-t / 0.8)
    ir = lfilter([0.3], [1, -0.7], ir)
    ir[: int(0.02 * SR)] = 0
    return ir / np.sqrt((ir ** 2).sum())


def sound():
    n = int((TOTAL + 3) * SR)
    L, R = np.zeros(n), np.zeros(n)

    def add(sig, t0, g=1.0, pan=0.0):
        i = int(t0 * SR)
        j = min(n, i + len(sig))
        L[i:j] += sig[: j - i] * g * (1 - pan) ** 0.5
        R[i:j] += sig[: j - i] * g * (1 + pan) ** 0.5

    t = np.arange(int(18.4 * SR)) / SR
    drone = (np.sin(2 * np.pi * hz(26) * t) + 0.5 * np.sin(2 * np.pi * hz(38) * t)) * np.clip(t / 6, 0, 1) ** 1.2
    air = lp(np.random.default_rng(3).normal(0, 1, len(t)), 500) * np.clip(t / 10, 0, 1) * 0.4
    add((drone * 0.5 + air) * np.clip((18.4 - t) / 0.02, 0, 1), 0.0, 0.32)
    add(braam([38, 41, 45, 50], 3.0), 1.8, 0.55)                     # D minor
    add(braam([34, 41, 46, 50], 3.0), 5.9, 0.55)                     # B♭
    for k, tt in enumerate((9.8, 11.3, 12.8)):
        add(swell(0.45, k), tt - 0.45, 0.25)
        add(boom(2.2, 0.8), tt, 0.85)
    r = riser(4.1)
    r[-int(0.01 * SR):] *= np.linspace(1, 0, int(0.01 * SR))
    add(r, 14.3, 0.45)
    add(boom(3.2, 1.4), 18.8, 1.0)
    add(braam([38, 42, 45, 50], 4.0, 0.3), 18.8, 0.6)                 # D major — the turn to light
    add(choir([62, 66, 69, 74], TOTAL - 18.9 + 1.5), 18.9, 0.35)
    wl, wr = fftconvolve(L, hall(11))[:n], fftconvolve(R, hall(12))[:n]
    L, R = L * 0.8 + wl * 0.45, R * 0.8 + wr * 0.45
    m = int(TOTAL * SR)
    L, R = L[:m], R[:m]
    s0, s1 = int(18.4 * SR), int(18.8 * SR)                          # the silence beat stays silent
    L[s0:s1] *= 0.02
    R[s0:s1] *= 0.02
    fo = int(1.8 * SR)
    L[-fo:] *= np.linspace(1, 0, fo) ** 1.5
    R[-fo:] *= np.linspace(1, 0, fo) ** 1.5
    pk = max(np.abs(L).max(), np.abs(R).max()) + 1e-9
    st = (np.stack([L, R], 1) / pk * 0.8 * 32767).astype(np.int16)
    os.makedirs(f"{D}/out", exist_ok=True)
    with wave.open(f"{D}/out/sound_raw.wav", "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(st.tobytes())
    subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-i", f"{D}/out/sound_raw.wav", "-af",
                    "loudnorm=I=-14:TP=-1.5:LRA=14", "-ar", "48000", f"{D}/out/sound.wav"], check=True)
    print("sound ok")


def final():
    ins, fl, labels = [], [], []
    k = 0
    for kind, name, t0, t1 in TL:
        d = t1 - t0
        if kind == "shot":
            ins += ["-i", f"{D}/seg/{name}.mp4"]
            fl.append(f"[{k}:v]trim=0:{d:.4f},setpts=PTS-STARTPTS,settb=AVTB,fps={FPS},format=yuv420p[v{k}]")
        else:
            ins += ["-f", "lavfi", "-i", f"color=c=black:s={W}x{H}:r={FPS}:d={d:.4f}"]
            fl.append(f"[{k}:v]settb=AVTB,fps={FPS},format=yuv420p[v{k}]")
        labels.append(f"[v{k}]")
        k += 1
    fl.append(f"{''.join(labels)}concat=n={k}:v=1:a=0[base]")
    ins += ["-i", f"{D}/ov/titles.mov", "-i", f"{D}/out/sound.wav"]
    fl.append(f"[{k}:v]format=yuva420p[ov];[base][ov]overlay=0:0:eof_action=pass,format=yuv420p[vout]")
    out = f"{D}/out/imperial_kino_treyler.mp4"
    subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y"] + ins + ["-filter_complex", ";".join(fl), "-map", "[vout]",
                    "-map", f"{k + 1}:a", "-t", f"{TOTAL}", "-c:v", "libx264", "-preset", "slow", "-crf", "17",
                    "-pix_fmt", "yuv420p", "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
                    "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", out + ".tmp.mp4"], check=True)
    os.replace(out + ".tmp.mp4", out)
    subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-ss", "19.6", "-i", out, "-frames:v", "1", "-q:v", "2",
                    f"{D}/out/imperial_kino_treyler_muqova.jpg"], check=True)
    print("final ok")


if __name__ == "__main__":
    w = sys.argv[1] if len(sys.argv) > 1 else "all"
    if w in ("overlay", "all"):
        overlay()
    if w in ("sound", "all"):
        sound()
    if w in ("final", "all"):
        final()
