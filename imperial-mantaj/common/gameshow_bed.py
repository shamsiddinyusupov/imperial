"""Original bed #17 (not used before): «game show» — a slot-reel tick on every flash (tick-tock pair), pulsing
octave synth bass on the flash grid, suspense minor chords with a rising filter, a riser, then a three-bell «win» hit
and a warm major groove (soft kick, shaker, bell arpeggio) for the reveal. Flash grid 0.333 s = 8ths at 90 BPM.

gameshow_bed(path, total, flash_times, game_end, seed=17)
"""
import wave

import numpy as np
from scipy.signal import butter, fftconvolve, lfilter

SR = 48000
BPM = 90
BEAT = 60 / BPM


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def tick(rng, hi=True):
    d = 0.05
    t = np.arange(int(d * SR)) / SR
    f = 2600 if hi else 1900
    y = np.sin(2 * np.pi * f * t) * np.exp(-t / 0.006) + rng.normal(0, 0.35, len(t)) * np.exp(-t / 0.002)
    b, a = butter(2, 900 / (SR / 2), "high")
    return lfilter(b, a, y)


def saw_note(m, dur, cut0, cut1, rng):
    n = int(dur * SR)
    t = np.arange(n) / SR
    out = np.zeros(n)
    for det in (-0.08, 0.08):
        ph = (hz(m) * (1 + det / 100) * t + rng.uniform(0, 1)) % 1.0
        out += 2 * ph - 1
    cut = cut0 + (cut1 - cut0) * np.exp(-t / 0.06)
    a = np.exp(-2 * np.pi * cut / SR)
    y = np.zeros(n)
    acc = 0.0
    for i in range(n):
        acc = (1 - a[i]) * out[i] + a[i] * acc
        y[i] = acc
    env = np.minimum(1, t / 0.004) * np.exp(-t / (dur * 0.6))
    return y * env


def pad(tones, dur, rng, bright=600):
    n = int(dur * SR)
    t = np.arange(n) / SR
    out = np.zeros(n)
    for m in tones:
        for det in (-0.3, 0.3):
            ph = (hz(m) + det) * t + rng.uniform(0, 1)
            out += 2 * (ph % 1.0) - 1
    b, a = butter(2, bright / (SR / 2), "low")
    out = lfilter(b, a, out)
    env = np.minimum(1, t / 0.25) * np.clip((dur - t) / 0.4, 0, 1)
    return out * env / (np.abs(out).max() + 1e-9)


def bell(m, dur=2.0):
    t = np.arange(int(dur * SR)) / SR
    f = hz(m)
    y = sum(a * np.sin(2 * np.pi * f * r * t) * np.exp(-t / d) for r, a, d in [(1, 1, 1.0), (2.0, 0.5, 0.6), (3.01, 0.25, 0.3), (5.2, 0.1, 0.12)])
    return y * (1 - np.exp(-t / 0.001))


def kick():
    t = np.arange(int(0.3 * SR)) / SR
    f = 46 + 100 * np.exp(-t / 0.03)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.14)


def shaker(rng):
    x = rng.normal(0, 1, int(0.05 * SR))
    b, a = butter(2, 7000 / (SR / 2), "high")
    return lfilter(b, a, x) * np.exp(-np.arange(len(x)) / (SR * 0.012))


def whoosh(rng, dur=0.7):
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = rng.normal(0, 1, n)
    out = np.zeros(n)
    for k in range(10):
        s, e = k * n // 10, (k + 1) * n // 10
        fc = 3000 * 2 ** (-k * 0.3)
        b, a = butter(2, [fc * 0.6 / (SR / 2), min(0.99, fc * 1.5 / (SR / 2))], "band")
        out[s:e] = lfilter(b, a, x[s:e])
    return out * np.sin(np.pi * t / dur)


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


def hall(seed, secs=1.6):
    r = np.random.default_rng(seed)
    t = np.arange(int(secs * SR)) / SR
    ir = r.normal(0, 1, len(t)) * np.exp(-t / 0.4)
    ir = lfilter([0.35], [1, -0.55], ir)
    ir[: int(0.01 * SR)] = 0
    return ir / np.sqrt((ir ** 2).sum())


SUS = [(45, [57, 60, 64]), (41, [57, 60, 65]), (43, [59, 62, 67]), (40, [56, 59, 64])]       # Am F G E
WARM = [(48, [60, 64, 67, 71]), (45, [60, 64, 69, 72]), (41, [60, 65, 69, 72]), (43, [59, 62, 67, 71])]   # C Am F G


def gameshow_bed(path, total, flash_times, game_end, seed=17):
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

    # game: tick on every flash, octave bass on the same grid, suspense chords, filter opens
    for k, ft in enumerate(flash_times):
        add(tick(rng, k % 2 == 0), ft, 0.25 if k % 2 else -0.25, 0.30)
    bar = 4 * BEAT
    t, k = 0.0, 0
    while t < game_end - 0.05:
        root, tones = SUS[k % 4]
        prog = min(1.0, t / max(1e-3, game_end))
        add(pad(tones, min(bar, game_end - t) + 0.2, rng, 500 + 1500 * prog), t, 0, 0.16)
        for e in range(8):
            te = t + e * BEAT / 2
            if te >= game_end - 0.05:
                break
            m = root - 12 + (12 if e % 2 else 0)
            add(saw_note(m, BEAT / 2 * 0.9, 250 + 500 * prog, 1200 + 2500 * prog, rng), te, 0, 0.20)
            if e % 2 == 0:
                add(kick(), te, 0, 0.30 if e % 4 == 0 else 0.18)
        t += bar
        k += 1
    add(riser(1.4, rng), game_end - 1.4, 0, 0.10)
    # win hit
    add(whoosh(rng), game_end - 0.15, 0, 0.12)
    for j, m in enumerate([84, 88, 91]):
        add(bell(m, 1.8), game_end + 0.09 * j, -0.3 + 0.3 * j, 0.12)
    # reveal groove
    t, k = game_end, 0
    stop = total - 2.2
    while t < stop:
        root, tones = WARM[k % 4]
        add(pad(tones, min(bar, total - t) + 0.4, rng, 1400), t, 0, 0.16)
        for b_ in range(4):
            tb = t + b_ * BEAT
            if tb >= stop:
                break
            add(kick(), tb, 0, 0.22)
            add(sub_s := np.sin(2 * np.pi * hz(root - 12) * np.arange(int(BEAT * 0.9 * SR)) / SR)
                * np.exp(-np.arange(int(BEAT * 0.9 * SR)) / (SR * 0.3)), tb, 0, 0.14)
            for s in range(4):
                add(shaker(rng), tb + s * BEAT / 4, 0.5, 0.04 if s == 2 else 0.025)
        for e in range(8):
            te = t + e * BEAT / 2
            if te >= stop:
                break
            add(bell(tones[(e * 3) % 4] + 12, 0.9), te, 0.4 * np.sin(e), 0.05)
        t += bar
        k += 1
    for j, m in enumerate([60, 64, 67, 72, 76]):
        add(bell(m + 12, 2.6), stop + 0.06 * j, -0.3 + 0.15 * j, 0.07)
    add(pad([48, 55, 60, 64, 67], 3.0, rng, 1200), stop, 0, 0.2)

    wl, wr = fftconvolve(L, hall(171))[:n], fftconvolve(R, hall(172))[:n]
    L, R = L * 0.85 + wl * 0.25, R * 0.85 + wr * 0.25
    b_, a_ = butter(2, 30 / (SR / 2), "high")
    L, R = lfilter(b_, a_, L), lfilter(b_, a_, R)
    m = int(total * SR)
    L, R = L[:m], R[:m]
    fi = int(0.01 * SR)
    L[:fi] *= np.linspace(0, 1, fi)
    R[:fi] *= np.linspace(0, 1, fi)
    fade = int(1.5 * SR)
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
    ft = [i / 3 for i in range(27)]
    gameshow_bed("/tmp/claude-0/-home-claude/29c18e40-edfd-55e7-a3e1-da5539b3418b/scratchpad/gs_test.wav", 20, ft, 9.0)
    print("ok")
