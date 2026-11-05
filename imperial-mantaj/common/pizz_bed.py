"""Original bed #6 (not used before): string pizzicato (short Karplus-Strong plucks with a wooden body),
soft felt kick and brushed shaker, warm low pad. Key of G major, 96 BPM — confident, light «checklist» feel.

pizz_bed(path, total, plan, seed=6)
  plan = dict(chords=[(t, root_midi, [tones])...], hits=[(t, midi, vel, pan)...], end=t_end_card,
              groove=(t0, t1))   # kick + shaker only inside groove
"""
import wave

import numpy as np
from scipy.signal import butter, fftconvolve, lfilter

SR = 48000
BPM = 96
BEAT = 60 / BPM


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def pluck(m, vel, rng, dur=1.2):
    f = hz(m)
    N = max(2, int(round(SR / f)))
    n = int(dur * SR)
    b, a = butter(1, min(0.99, (1500 + 10 * f) / (SR / 2)))
    y = np.zeros(n + N + 1)
    y[:N] = lfilter(b, a, rng.uniform(-1, 1, N))
    rho = 0.4935
    k = N
    while k < n + 1:
        e = min(k + N, n + 1)
        seg = y[k - N:e - N]
        prv = y[k - N - 1:e - N - 1] if k - N - 1 >= 0 else np.concatenate([[0.0], y[k - N:e - N - 1]])
        y[k:e] = rho * (seg + prv[:len(seg)])
        k = e
    y = y[N:N + n]
    t = np.arange(n) / SR
    y += 0.35 * np.sin(2 * np.pi * f * t) * np.exp(-t / 0.18)          # wooden body
    y *= (1 - np.exp(-t / 0.0015)) * np.exp(-t / 0.35)
    return y / (np.abs(y).max() + 1e-9) * vel


def pad(tones, dur, rng, att=0.8, rel=1.2):
    t = np.arange(int(dur * SR)) / SR
    out = np.zeros_like(t)
    for m in tones:
        for det in (-0.25, 0.22):
            ph = 2 * np.pi * (hz(m) + det) * t + rng.uniform(0, 6.28)
            for h in range(1, 6):
                out += np.sin(h * ph) / h ** 1.6
    env = np.minimum(1, t / att) ** 1.5 * np.clip((dur - t) / rel, 0, 1)
    return out * env / (np.abs(out).max() + 1e-9)


def kick():
    t = np.arange(int(0.35 * SR)) / SR
    f = 52 + 60 * np.exp(-t / 0.03)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.12) * (1 - np.exp(-t / 0.002))


def shaker(rng):
    t = np.arange(int(0.09 * SR)) / SR
    b, a = butter(2, [5000 / (SR / 2), 11000 / (SR / 2)], "band")
    return lfilter(b, a, rng.normal(0, 1, len(t))) * np.exp(-t / 0.025) * np.minimum(1, t / 0.01)


def hall(seed, secs=2.6):
    r = np.random.default_rng(seed)
    t = np.arange(int(secs * SR)) / SR
    ir = r.normal(0, 1, len(t)) * np.exp(-t / 0.6)
    ir = lfilter([0.3], [1, -0.68], ir)
    ir[: int(0.015 * SR)] = 0
    return ir / np.sqrt((ir ** 2).sum())


def pizz_bed(path, total, plan, seed=6):
    rng = np.random.default_rng(seed)
    n = int((total + 3) * SR)
    L, R = np.zeros(n), np.zeros(n)

    def add(sig, t0, pan=0.0, g=1.0):
        i = int(round(t0 * SR))
        if i >= n:
            return
        if i < 0:
            sig, i = sig[-i:], 0
        j = min(n, i + len(sig))
        L[i:j] += sig[: j - i] * g * (1 - pan) ** 0.5
        R[i:j] += sig[: j - i] * g * (1 + pan) ** 0.5

    ch = plan["chords"]
    for k, (t0, root, tones) in enumerate(ch):
        t1 = ch[k + 1][0] if k + 1 < len(ch) else total + 1.0
        add(pad(tones, t1 - t0 + 1.2, rng), t0 - (0 if k == 0 else 0.3), 0, 0.16)
        # pizzicato ostinato: root, fifth, octave, tones — on eighths
        pat = [root + 12, root + 19, tones[0] + 12, tones[1] + 12, root + 19, tones[2] + 12, root + 24, tones[1] + 12]
        t, i = t0, 0
        while t < t1 - 0.05:
            accent = 1.0 if i % 2 == 0 else 0.7
            add(pluck(pat[i % len(pat)], 0.16 * accent, rng), t + rng.normal(0, 0.004), 0.35 * np.sin(i * 1.3))
            if i % 4 == 0:
                add(pluck(root, 0.22, rng, 1.6), t, 0, 1.0)
            i += 1
            t += BEAT / 2
    g0, g1 = plan.get("groove", (0, 0))
    t, i = g0, 0
    while t < g1:
        if i % 2 == 0:
            add(kick(), t, 0, 0.30)
        add(shaker(rng), t + BEAT / 4, 0.3, 0.05 if i % 2 else 0.035)
        i += 1
        t += BEAT
    for t0, m, vel, pan in plan.get("hits", []):
        add(pluck(m, vel, rng, 1.8), t0, pan)
    wl, wr = fftconvolve(L, hall(51))[:n], fftconvolve(R, hall(52))[:n]
    L, R = L * 0.8 + wl * 0.45, R * 0.8 + wr * 0.45
    b_, a_ = butter(2, 35 / (SR / 2), "high")
    L, R = lfilter(b_, a_, L), lfilter(b_, a_, R)
    m = int(total * SR)
    L, R = L[:m], R[:m]
    fi = int(0.05 * SR)
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
