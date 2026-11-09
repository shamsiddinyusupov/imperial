"""Original bed #12 (not used before): «process» groove — soft woodblock clock ticks, filtered-saw pluck ostinato,
round sub, a rising riser into the reveal, then a warm bell chord + pad when the work is done. A minor -> C major,
104 BPM. Built for step-by-step «from zero to finished» videos.

tick_bed(path, total, plan, seed=12)
  plan = dict(steps=[t...], reveal=t, chords=[(t, root, [tones])...])
"""
import wave

import numpy as np
from scipy.signal import butter, fftconvolve, lfilter

SR = 48000
BPM = 104
BEAT = 60 / BPM


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def block(rng, f=1800, dur=0.06):
    t = np.arange(int(dur * SR)) / SR
    y = np.sin(2 * np.pi * f * t) * np.exp(-t / 0.008) + 0.5 * np.sin(2 * np.pi * f * 1.48 * t) * np.exp(-t / 0.004)
    return y + rng.normal(0, 0.05, len(t)) * np.exp(-t / 0.003)


def pluck(m, vel, dur=0.5):
    t = np.arange(int(dur * SR)) / SR
    f = hz(m)
    ph = (f * t) % 1.0
    saw = 2 * ph - 1
    cut = 600 + 3200 * np.exp(-t / 0.05)
    y = np.zeros_like(t)
    # time-varying one-pole low-pass
    a = np.exp(-2 * np.pi * cut / SR)
    acc = 0.0
    for i in range(len(t)):
        acc = (1 - a[i]) * saw[i] + a[i] * acc
        y[i] = acc
    return y * np.exp(-t / 0.16) * (1 - np.exp(-t / 0.002)) * vel


def sub(m, dur):
    t = np.arange(int(dur * SR)) / SR
    return np.sin(2 * np.pi * hz(m - 12) * t) * np.minimum(1, t / 0.02) * np.exp(-t / 0.5)


def bell(m, dur=4.0):
    t = np.arange(int(dur * SR)) / SR
    f = hz(m)
    y = sum(a * np.sin(2 * np.pi * f * r * t) * np.exp(-t / d)
            for r, a, d in [(1, 1, 2.2), (2.0, 0.5, 1.4), (2.76, 0.35, 0.9), (5.4, 0.15, 0.4)])
    return y * (1 - np.exp(-t / 0.002))


def pad(tones, dur, rng):
    t = np.arange(int(dur * SR)) / SR
    out = np.zeros_like(t)
    for m in tones:
        for det in (-0.4, 0.4):
            ph = 2 * np.pi * (hz(m) + det) * t + rng.uniform(0, 6.28)
            out += sum(np.sin(h * ph) / h ** 1.6 for h in range(1, 6))
    env = np.minimum(1, t / 0.8) ** 1.5 * np.clip((dur - t) / 1.5, 0, 1)
    return out * env / (np.abs(out).max() + 1e-9)


def riser(dur, rng):
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = rng.normal(0, 1, n)
    out = np.zeros(n)
    for k in range(10):
        s, e = k * n // 10, (k + 1) * n // 10
        fc = 400 * 2 ** (k * 0.45)
        b, a = butter(2, [fc * 0.7 / (SR / 2), min(0.99, fc * 1.4 / (SR / 2))], "band")
        out[s:e] = lfilter(b, a, x[s:e])
    return out * (t / dur) ** 2


def hall(seed, secs=2.6):
    r = np.random.default_rng(seed)
    t = np.arange(int(secs * SR)) / SR
    ir = r.normal(0, 1, len(t)) * np.exp(-t / 0.7)
    ir = lfilter([0.3], [1, -0.68], ir)
    ir[: int(0.015 * SR)] = 0
    return ir / np.sqrt((ir ** 2).sum())


def tick_bed(path, total, plan, seed=12):
    rng = np.random.default_rng(seed)
    n = int((total + 4) * SR)
    L, R = np.zeros(n), np.zeros(n)

    def add(sig, t0, p=0.0, g=1.0):
        i = int(round(t0 * SR))
        if i >= n:
            return
        if i < 0:
            sig, i = sig[-i:], 0
        j = min(n, i + len(sig))
        L[i:j] += sig[: j - i] * g * (1 - p) ** 0.5
        R[i:j] += sig[: j - i] * g * (1 + p) ** 0.5

    rv = plan["reveal"]
    t, i = 0.0, 0
    while t < rv - 0.05:                                    # clock ticks + ostinato until the reveal
        add(block(rng, 1900 if i % 2 == 0 else 1500), t, 0.3 * (1 if i % 2 else -1), 0.10 if i % 4 == 0 else 0.06)
        i += 1
        t += BEAT / 2
    ch = plan["chords"]
    for k, (t0, root, tones) in enumerate(ch):
        t1 = ch[k + 1][0] if k + 1 < len(ch) else total
        if t0 >= rv:
            add(pad(tones, total - t0 + 1, rng), t0, 0, 0.22)
            for j, m in enumerate(tones):
                add(bell(m + 12), t0 + 0.03 * j, 0.3 * (j - 1), 0.18)
            add(sub(root, 3.0), t0, 0, 0.35)
            continue
        seq = [tones[0] + 12, tones[1] + 12, tones[2] + 12, tones[1] + 12]
        tt, j = t0, 0
        while tt < min(t1, rv) - 0.05:
            add(pluck(seq[j % 4], 0.22 if j % 2 == 0 else 0.15), tt, 0.4 * np.sin(j * 1.3))
            if j % 4 == 0:
                add(sub(root, BEAT * 1.8), tt, 0, 0.32)
            j += 1
            tt += BEAT / 2
    for st in plan.get("steps", []):
        add(bell(81, 1.5), st, 0, 0.06)
    add(riser(1.8, rng), rv - 1.8, 0, 0.09)
    wl, wr = fftconvolve(L, hall(121))[:n], fftconvolve(R, hall(122))[:n]
    L, R = L * 0.8 + wl * 0.4, R * 0.8 + wr * 0.4
    b_, a_ = butter(2, 38 / (SR / 2), "high")
    L, R = lfilter(b_, a_, L), lfilter(b_, a_, R)
    m = int(total * SR)
    L, R = L[:m], R[:m]
    fi = int(0.03 * SR)
    L[:fi] *= np.linspace(0, 1, fi)
    R[:fi] *= np.linspace(0, 1, fi)
    fade = int(2.0 * SR)
    L[-fade:] *= np.linspace(1, 0, fade) ** 1.5
    R[-fade:] *= np.linspace(1, 0, fade) ** 1.5
    pk = max(np.abs(L).max(), np.abs(R).max()) + 1e-9
    st = (np.stack([L, R], 1) / pk * 0.7 * 32767).astype(np.int16)
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(st.tobytes())
