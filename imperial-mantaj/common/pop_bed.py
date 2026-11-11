"""Original bed #16 (not used before): bright «quiz» pop — plucky synth arpeggios, soft four-on-the-floor kick,
claps on 2 and 4, 16th shaker, sub bass; a bell «ding» on every option, a riser before the end card, then a
sustained resolve. F major (F - C - Dm - Bb), 100 BPM.

pop_bed(path, total, end_at, dings=[t...], seed=16)
"""
import wave

import numpy as np
from scipy.signal import butter, fftconvolve, lfilter

SR = 48000
BPM = 100
BEAT = 60 / BPM


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def pluck(m, dur=0.32, bright=1.0):
    t = np.arange(int(dur * SR)) / SR
    f = hz(m)
    ph = (f * t) % 1.0
    sq = np.where(ph < 0.5, 1.0, -1.0) * 0.6 + (2 * ph - 1) * 0.4
    cut = 500 + 4200 * bright * np.exp(-t / 0.045)
    a = np.exp(-2 * np.pi * cut / SR)
    y = np.zeros_like(t)
    acc = 0.0
    for i in range(len(t)):                                              # short notes: plain loop is fine
        acc = (1 - a[i]) * sq[i] + a[i] * acc
        y[i] = acc
    return y * np.exp(-t / 0.11) * (1 - np.exp(-t / 0.002))


def kick():
    t = np.arange(int(0.3 * SR)) / SR
    f = 48 + 110 * np.exp(-t / 0.035)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.13)


def clap(rng):
    out = np.zeros(int(0.25 * SR))
    for k, d in enumerate([0, 0.011, 0.022]):
        x = rng.normal(0, 1, int(0.2 * SR))
        x *= np.exp(-np.arange(len(x)) / (SR * (0.009 if k < 2 else 0.06)))
        i = int(d * SR)
        out[i:i + len(x)] += x[: len(out) - i]
    b, a = butter(2, [900 / (SR / 2), 5500 / (SR / 2)], "band")
    return lfilter(b, a, out)


def shaker(rng, acc):
    x = rng.normal(0, 1, int(0.06 * SR))
    b, a = butter(2, 6500 / (SR / 2), "high")
    return lfilter(b, a, x) * np.exp(-np.arange(len(x)) / (SR * (0.018 if acc else 0.01)))


def sub(m, dur):
    t = np.arange(int(dur * SR)) / SR
    return np.sin(2 * np.pi * hz(m) * t) * np.minimum(1, t / 0.01) * np.clip((dur - t) / 0.05, 0, 1)


def bell(m, dur=2.5):
    t = np.arange(int(dur * SR)) / SR
    f = hz(m)
    y = sum(a * np.sin(2 * np.pi * f * r * t) * np.exp(-t / d) for r, a, d in [(1, 1, 1.2), (2.0, 0.4, 0.7), (3.0, 0.2, 0.4), (4.2, 0.1, 0.2)])
    return y * (1 - np.exp(-t / 0.001))


def pad(tones, dur, rng):
    t = np.arange(int(dur * SR)) / SR
    out = np.zeros_like(t)
    for m in tones:
        for det in (-0.6, 0.6):
            out += np.sin(2 * np.pi * (hz(m) + det) * t + rng.uniform(0, 6.28))
    env = np.minimum(1, t / 0.6) * np.clip((dur - t) / 1.5, 0, 1)
    return out * env / (np.abs(out).max() + 1e-9)


def riser(dur, rng):
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = rng.normal(0, 1, n)
    out = np.zeros(n)
    for k in range(12):
        s, e = k * n // 12, (k + 1) * n // 12
        fc = 500 * 2 ** (k * 0.38)
        b, a = butter(2, [fc * 0.7 / (SR / 2), min(0.99, fc * 1.4 / (SR / 2))], "band")
        out[s:e] = lfilter(b, a, x[s:e])
    return out * (t / dur) ** 2


PROG = [(41, [65, 69, 72, 77]), (36, [64, 67, 72, 76]), (38, [62, 65, 69, 74]), (34, [62, 65, 70, 74])]
PAT = [0, 2, 1, 3, 2, 1, 3, 2]                                          # arpeggio order over 8 eighths


def hall(seed, secs=1.8):
    r = np.random.default_rng(seed)
    t = np.arange(int(secs * SR)) / SR
    ir = r.normal(0, 1, len(t)) * np.exp(-t / 0.45)
    ir = lfilter([0.35], [1, -0.55], ir)
    ir[: int(0.01 * SR)] = 0
    return ir / np.sqrt((ir ** 2).sum())


def pop_bed(path, total, end_at, dings=(), seed=16):
    rng = np.random.default_rng(seed)
    n = int((total + 3) * SR)
    L, R = np.zeros(n), np.zeros(n)

    def add(sig, t0, p=0.0, g=1.0):
        i = int(round(t0 * SR))
        if i >= n or i < 0:
            return
        j = min(n, i + len(sig))
        L[i:j] += sig[: j - i] * g * (1 - p) ** 0.5
        R[i:j] += sig[: j - i] * g * (1 + p) ** 0.5

    bar = 4 * BEAT
    stop = end_at - 0.05
    t, k = 0.0, 0
    while t < stop:
        root, tones = PROG[k % 4]
        for e in range(8):
            te = t + e * BEAT / 2
            if te >= stop:
                break
            add(pluck(tones[PAT[e]] + 12, 0.3, 0.8 + 0.2 * (e % 2 == 0)), te, 0.35 * (1 if e % 2 else -1), 0.16)
        for b_ in range(4):
            tb = t + b_ * BEAT
            if tb >= stop:
                break
            if t > 0.5 or b_ > 0:
                add(kick(), tb, 0, 0.27)
            if b_ in (1, 3):
                add(clap(rng), tb, 0.05, 0.10)
            add(sub(root, BEAT * 0.9), tb, 0, 0.13)
        for s in range(16):
            ts = t + s * BEAT / 4
            if ts >= stop:
                break
            add(shaker(rng, s % 4 == 2), ts, 0.5, 0.05 if s % 4 == 2 else 0.03)
        t += bar
        k += 1
    for d in dings:
        add(bell(84, 1.8), d, 0.2, 0.10)
        add(bell(91, 1.4), d + 0.09, -0.2, 0.06)
    add(riser(1.6, rng), end_at - 1.6, 0, 0.07)
    # end card: resolve on F, light pulse continues softly
    add(pad([53, 60, 65, 69, 72, 77], total - end_at + 2, rng), end_at, 0, 0.24)
    add(sub(41, 2.0), end_at, 0, 0.18)
    for j, m in enumerate([77, 81, 84, 89]):
        add(bell(m, 2.4), end_at + 0.1 * j, -0.3 + 0.2 * j, 0.07)
    tt = end_at + 4 * BEAT
    while tt < total - 1.0:
        add(pluck([77, 81, 84, 81][int((tt - end_at) / (BEAT / 2)) % 4], 0.3, 0.6), tt, 0.3, 0.10)
        tt += BEAT / 2

    wl, wr = fftconvolve(L, hall(161))[:n], fftconvolve(R, hall(162))[:n]
    L, R = L * 0.85 + wl * 0.28, R * 0.85 + wr * 0.28
    b_, a_ = butter(2, 30 / (SR / 2), "high")
    L, R = lfilter(b_, a_, L), lfilter(b_, a_, R)
    m = int(total * SR)
    L, R = L[:m], R[:m]
    fi = int(0.02 * SR)
    L[:fi] *= np.linspace(0, 1, fi)
    R[:fi] *= np.linspace(0, 1, fi)
    fade = int(1.6 * SR)
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
    import time
    t0 = time.time()
    pop_bed("/tmp/claude-0/-home-claude/29c18e40-edfd-55e7-a3e1-da5539b3418b/scratchpad/pop_test.wav", 23, 17.2,
            [2.9, 6.7, 10.4, 14.3])
    print("ok", round(time.time() - t0, 1))
