"""Original bed #15 (not used before): airy «tulle» ambience — soft formant choir «aah» pad, wind chimes that rustle
while the fabric moves, a low warm drone. No beat. G major colours (Gmaj9 -> Em9 -> Cmaj9 -> Dsus), ~60 BPM feel.

airy_bed(path, total, end_at, chimes=[(t0, t1), ...], seed=15)
  chimes = time ranges where the curtain / tulle moves (chimes cluster there)
"""
import wave

import numpy as np
from scipy.signal import butter, fftconvolve, lfilter

SR = 48000


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


FORM = [(850, 90, 1.0), (1220, 100, 0.55), (2810, 140, 0.25)]          # vowel «a», soft female choir


def choir(tones, dur, rng):
    n = int(dur * SR)
    t = np.arange(n) / SR
    src = np.zeros(n)
    for m in tones:
        for _ in range(3):                                              # three singers per note
            f = hz(m) * (1 + rng.uniform(-0.004, 0.004))
            vib = 1 + 0.006 * np.sin(2 * np.pi * rng.uniform(4.6, 5.6) * t + rng.uniform(0, 6.28))
            ph = np.cumsum(f * vib) / SR
            src += 2 * (ph % 1.0) - 1
    src += rng.normal(0, 0.15, n)                                        # breath
    out = np.zeros(n)
    for fc, bw, g in FORM:
        b, a = butter(2, [(fc - bw) / (SR / 2), (fc + bw) / (SR / 2)], "band")
        out += lfilter(b, a, src) * g
    env = np.minimum(1, t / 1.6) ** 1.6 * np.clip((dur - t) / 1.8, 0, 1)
    return out * env / (np.abs(out).max() + 1e-9)


def chime(m, rng, dur=3.5):
    t = np.arange(int(dur * SR)) / SR
    f = hz(m)
    y = sum(a * np.sin(2 * np.pi * f * r * t + rng.uniform(0, 6.28)) * np.exp(-t / d)
            for r, a, d in [(1, 1, 1.6), (2.76, 0.45, 0.9), (5.40, 0.22, 0.5), (8.93, 0.10, 0.25)])
    return y * (1 - np.exp(-t / 0.001))


def drone(m, dur):
    t = np.arange(int(dur * SR)) / SR
    y = np.sin(2 * np.pi * hz(m) * t) + 0.3 * np.sin(2 * np.pi * hz(m + 12) * t) + 0.15 * np.sin(2 * np.pi * hz(m + 19) * t)
    return y * np.minimum(1, t / 2.0) * np.clip((dur - t) / 2.0, 0, 1)


def hall(seed, secs=4.0):
    r = np.random.default_rng(seed)
    t = np.arange(int(secs * SR)) / SR
    ir = r.normal(0, 1, len(t)) * np.exp(-t / 1.3)
    ir = lfilter([0.3], [1, -0.72], ir)
    ir[: int(0.025 * SR)] = 0
    return ir / np.sqrt((ir ** 2).sum())


CH = [[55, 62, 66, 69, 74], [52, 59, 62, 66, 71], [48, 55, 59, 64, 71], [50, 57, 62, 67, 69]]
ROOTS = [31, 28, 24, 26]
PENT = [74, 76, 79, 81, 83, 86, 88, 91]                                 # G major pentatonic, high


def airy_bed(path, total, end_at, chimes=(), seed=15):
    rng = np.random.default_rng(seed)
    n = int((total + 5) * SR)
    L, R = np.zeros(n), np.zeros(n)

    def add(sig, t0, p=0.0, g=1.0):
        i = int(round(t0 * SR))
        if i >= n or i < 0:
            return
        j = min(n, i + len(sig))
        L[i:j] += sig[: j - i] * g * (1 - p) ** 0.5
        R[i:j] += sig[: j - i] * g * (1 + p) ** 0.5

    seg = max(3.2, end_at / 4)                                           # 4 chords over the video, then home
    for k in range(4):
        t0 = k * seg
        add(choir(CH[k], seg + 2.2, rng), max(0, t0 - 0.6), 0, 0.30)
        add(drone(ROOTS[k] + 12, seg + 2.0), max(0, t0 - 0.5), 0, 0.06)
    add(choir([55, 62, 67, 71, 74, 79], total - end_at + 3, rng), end_at - 0.8, 0, 0.34)
    add(drone(43, total - end_at + 3), end_at - 0.6, 0, 0.07)
    for (a, b) in chimes:                                                # rustle while the tulle moves
        t = a
        while t < b:
            add(chime(rng.choice(PENT), rng), t, rng.uniform(-0.8, 0.8), rng.uniform(0.04, 0.08))
            t += rng.uniform(0.08, 0.32)
    t = 0.8
    while t < total - 2:                                                 # a few sparse chimes elsewhere
        add(chime(rng.choice(PENT[:5]), rng), t, rng.uniform(-0.6, 0.6), 0.03)
        t += rng.uniform(1.6, 2.8)
    for k, m in enumerate([79, 83, 86, 91]):                             # end card: a gentle arpeggio
        add(chime(m, rng, 4.0), end_at + 0.15 + 0.18 * k, -0.4 + 0.25 * k, 0.07)

    wl, wr = fftconvolve(L, hall(151))[:n], fftconvolve(R, hall(152))[:n]
    L, R = L * 0.7 + wl * 0.5, R * 0.7 + wr * 0.5
    b_, a_ = butter(2, 40 / (SR / 2), "high")
    L, R = lfilter(b_, a_, L), lfilter(b_, a_, R)
    m = int(total * SR)
    L, R = L[:m], R[:m]
    fi = int(0.5 * SR)
    L[:fi] *= np.linspace(0, 1, fi)
    R[:fi] *= np.linspace(0, 1, fi)
    fade = int(2.2 * SR)
    L[-fade:] *= np.linspace(1, 0, fade) ** 1.5
    R[-fade:] *= np.linspace(1, 0, fade) ** 1.5
    pk = max(np.abs(L).max(), np.abs(R).max()) + 1e-9
    st = (np.stack([L, R], 1) / pk * 0.7 * 32767).astype(np.int16)
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(st.tobytes())


if __name__ == "__main__":
    airy_bed("/tmp/claude-0/-home-claude/29c18e40-edfd-55e7-a3e1-da5539b3418b/scratchpad/airy_test.wav", 21, 15.3,
             [(0.2, 4.0), (11.0, 15.0)])
    print("ok")
