"""Original bed #18 (not used before): «baroque meets modern» — harpsichord (two plucked choirs, 8' + 4', with jack
clicks) playing 16th-note broken chords over a circle-of-fifths progression in D minor, a soft string pad; from
`beat_at` a modern soft beat (kick, rim, hats) joins under it; paper page-turn swishes at the given times; ends on a
rolled D major chord (Picardy third). 96 BPM.

clavecin_bed(path, total, end_at, beat_at, turns=[t...], seed=18)
"""
import wave

import numpy as np
from scipy.signal import butter, fftconvolve, lfilter

SR = 48000
BPM = 96
BEAT = 60 / BPM


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def ks(f, dur, rng, bright=0.9, decay=0.996, pick=0.12):
    N = max(2, int(round(SR / f)))
    n = int(dur * SR)
    ex = rng.uniform(-1, 1, N)
    a = np.exp(-2 * np.pi * (1500 + 9000 * bright) / SR)
    ex = lfilter([1 - a], [1, -a], ex)
    k = max(1, int(N * pick))
    ex = ex - np.roll(ex, k)
    out = np.zeros(n + 2 * N)
    out[:N] = ex - ex.mean()
    for i in range(N, n + N, N):
        prev = out[i - N:i]
        sh = out[i - N - 1:i - 1] if i - N - 1 >= 0 else np.concatenate([[0.0], prev[:-1]])
        out[i:i + N] = decay * 0.5 * (prev + sh)
    y = out[:n]
    return y / (np.abs(y).max() + 1e-9)


def harpsi(m, dur, rng):
    """8' + 4' choirs, slightly detuned, plus a jack click"""
    y = ks(hz(m), dur, rng, 0.95, 0.9955) + 0.45 * ks(hz(m + 12) * 1.002, dur, rng, 1.0, 0.994)
    t = np.arange(len(y)) / SR
    click = rng.normal(0, 1, len(y)) * np.exp(-t / 0.0015) * 0.25
    y = (y + click) * np.exp(-t / 1.1)
    r = int(0.03 * SR)
    y[-r:] *= np.linspace(1, 0, r)
    return y


def strings(tones, dur, rng):
    n = int(dur * SR)
    t = np.arange(n) / SR
    out = np.zeros(n)
    for m in tones:
        for det in (-0.25, 0.0, 0.25):
            vib = 1 + 0.003 * np.sin(2 * np.pi * 5.0 * t + rng.uniform(0, 6.28))
            ph = np.cumsum((hz(m) + det) * vib) / SR
            out += 2 * (ph % 1.0) - 1
    b, a = butter(2, 1600 / (SR / 2), "low")
    out = lfilter(b, a, out)
    env = np.minimum(1, t / 0.6) * np.clip((dur - t) / 0.6, 0, 1)
    return out * env / (np.abs(out).max() + 1e-9)


def kick():
    t = np.arange(int(0.3 * SR)) / SR
    f = 46 + 95 * np.exp(-t / 0.03)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.15)


def rim(rng):
    t = np.arange(int(0.08 * SR)) / SR
    y = np.sin(2 * np.pi * 1700 * t) * np.exp(-t / 0.008) + rng.normal(0, 0.5, len(t)) * np.exp(-t / 0.004)
    b, a = butter(2, 700 / (SR / 2), "high")
    return lfilter(b, a, y)


def hat(rng, open_=False):
    d = 0.12 if open_ else 0.04
    x = rng.normal(0, 1, int(d * SR))
    b, a = butter(2, 7500 / (SR / 2), "high")
    return lfilter(b, a, x) * np.exp(-np.arange(len(x)) / (SR * (0.04 if open_ else 0.01)))


def page_turn(rng, dur=0.42):
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = rng.normal(0, 1, n)
    b, a = butter(2, [900 / (SR / 2), 7000 / (SR / 2)], "band")
    x = lfilter(b, a, x)
    crinkle = 1 + 2.5 * (rng.random(n) < 0.004) * rng.random(n)
    crinkle = np.convolve(crinkle, np.ones(60) / 60, "same")
    env = np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 1.5
    return x * env * crinkle


def hall(seed, secs=2.0):
    r = np.random.default_rng(seed)
    t = np.arange(int(secs * SR)) / SR
    ir = r.normal(0, 1, len(t)) * np.exp(-t / 0.55)
    ir = lfilter([0.35], [1, -0.6], ir)
    ir[: int(0.012 * SR)] = 0
    return ir / np.sqrt((ir ** 2).sum())


# circle of fifths in D minor, one chord per bar: (bass, arpeggio tones)
PROG = [(38, [62, 65, 69, 74]), (43, [62, 67, 70, 74]), (36, [60, 64, 67, 72]), (41, [60, 65, 69, 72]),
        (34, [62, 65, 70, 74]), (43, [58, 62, 67, 70]), (33, [61, 64, 69, 73]), (38, [62, 65, 69, 74])]
PAT = [0, 2, 1, 2, 3, 2, 1, 2]           # broken-chord figure over 8 sixteenths (half a bar), repeated


def clavecin_bed(path, total, end_at, beat_at, turns=(), seed=18):
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
    s16 = BEAT / 4
    t, k = 0.0, 0
    while t < end_at - 0.05:
        bass, tones = PROG[k % len(PROG)]
        add(strings([bass + 12, tones[0], tones[2]], bar + 0.6, rng), t, 0, 0.10)
        add(harpsi(bass, 1.4, rng), t, -0.1, 0.30)
        add(harpsi(bass + 12, 1.0, rng), t + 2 * BEAT, -0.1, 0.18)
        for s in range(16):
            ts = t + s * s16
            if ts >= end_at - 0.05:
                break
            m = tones[PAT[s % 8]] + (12 if s >= 8 and k % 2 else 0)
            add(harpsi(m, 0.7, rng), ts, 0.25 * np.sin(s * 0.8), 0.15 if s % 4 == 0 else 0.11)
        if t >= beat_at - 0.05:
            for b_ in range(4):
                tb = t + b_ * BEAT
                if tb >= end_at - 0.05:
                    break
                add(kick(), tb, 0, 0.20)
                if b_ in (1, 3):
                    add(rim(rng), tb, 0.1, 0.10)
                for e in range(2):
                    add(hat(rng, e == 1 and b_ == 3), tb + e * BEAT / 2, 0.45, 0.05 if e else 0.035)
        t += bar
        k += 1
    for tt in turns:
        add(page_turn(rng), tt - 0.12, 0.0, 0.11)
    # end: Picardy D major roll + strings, soft pulse continues lightly
    for j, m in enumerate([38, 50, 57, 62, 66, 69, 74, 78]):
        add(harpsi(m, 2.8, rng), end_at + 0.045 * j, -0.4 + 0.11 * j, 0.20)
    add(strings([50, 57, 62, 66, 69], total - end_at + 1, rng), end_at, 0, 0.16)
    tt = end_at + bar / 2
    while tt < total - 1.8:
        add(kick(), tt, 0, 0.18)
        add(harpsi([62, 66, 69, 74][int((tt - end_at) / BEAT) % 4] + 12, 0.6, rng), tt + BEAT / 2, 0.3, 0.07)
        tt += BEAT

    wl, wr = fftconvolve(L, hall(181))[:n], fftconvolve(R, hall(182))[:n]
    L, R = L * 0.82 + wl * 0.3, R * 0.82 + wr * 0.3
    b_, a_ = butter(2, 32 / (SR / 2), "high")
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
    clavecin_bed("/tmp/claude-0/-home-claude/29c18e40-edfd-55e7-a3e1-da5539b3418b/scratchpad/clav_test.wav", 24.5, 18.0,
                 10.5, [3.0, 5.5, 8.0, 10.5, 13.0, 15.5, 18.0])
    print("ok", round(time.time() - t0, 1))
