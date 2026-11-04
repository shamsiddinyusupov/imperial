"""Original bed #5 (not used before): plucked concert harp (Karplus-Strong strings with a soft body),
airy string-machine pad, a deep sub on the downbeats, long hall. Key of D major, ~72 BPM.
Built for «assembly» pictures: every landing can carry a harp note, so the arrangement follows the picture.

harp_bed(path, total, plan, seed=5)
  plan = dict(
    chords=[(t, root_midi, [pad tones])...],   # chord changes (pad + sub)
    plucks=[(t, midi, vel, pan)...],           # harp notes at exact times (landings, accents)
    gliss=[(t, [midis], step, vel)...],        # quick harp runs
  )
"""
import wave

import numpy as np
from scipy.signal import butter, fftconvolve, lfilter

SR = 48000


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def harp(m, dur, vel, rng):
    """Karplus-Strong string, computed one period at a time (fast), with a little body resonance."""
    f = hz(m)
    N = max(2, int(round(SR / f)))
    n = int(dur * SR)
    exc = rng.uniform(-1, 1, N)
    b, a = butter(1, min(0.99, (2200 + 18 * f) / (SR / 2)))
    exc = lfilter(b, a, exc)                       # a finger, not a pick
    y = np.zeros(n + N + 1)
    y[:N] = exc
    rho = 0.4985 * (0.9995 if f < 400 else 0.9988)
    k = N
    while k < n + 1:
        e = min(k + N, n + 1)
        seg = y[k - N:e - N]
        prv = y[k - N - 1:e - N - 1] if k - N - 1 >= 0 else np.concatenate([[0.0], y[k - N:e - N - 1]])
        y[k:e] = rho * (seg + prv[:len(seg)])
        k = e
    y = y[N:N + n]
    t = np.arange(n) / SR
    y += 0.25 * np.sin(2 * np.pi * f * t) * np.exp(-t / 1.6)        # body
    env = (1 - np.exp(-t / 0.002)) * np.exp(-t / (2.4 if f < 500 else 1.5))
    y = y * env
    return y / (np.abs(y).max() + 1e-9) * vel


def pad(tones, dur, rng, att=1.2, rel=1.6):
    t = np.arange(int(dur * SR)) / SR
    out = np.zeros_like(t)
    for m in tones:
        f = hz(m)
        for det in (-0.18, 0.21):
            ph = 2 * np.pi * (f + det) * t + rng.uniform(0, 6.28)
            for h in range(1, 9):
                g = (1 / h) / (1 + (h * f / 1100) ** 2.5)
                out += np.sin(h * ph) * g
    sw = 1 + 0.06 * np.sin(2 * np.pi * 0.21 * t + rng.uniform(0, 6))
    env = np.minimum(1, t / att) ** 1.7 * np.clip((dur - t) / rel, 0, 1) * sw
    return out * env / (np.abs(out).max() + 1e-9)


def sub(m, dur):
    t = np.arange(int(dur * SR)) / SR
    return np.sin(2 * np.pi * hz(m) * t) * np.minimum(1, t / 0.08) * np.exp(-t / 1.8)


def hall(seed, secs=3.8):
    r = np.random.default_rng(seed)
    t = np.arange(int(secs * SR)) / SR
    ir = r.normal(0, 1, len(t)) * np.exp(-t / 1.05)
    ir = lfilter([0.3], [1, -0.70], ir)
    ir[: int(0.022 * SR)] = 0
    return ir / np.sqrt((ir ** 2).sum())


def harp_bed(path, total, plan, seed=5):
    rng = np.random.default_rng(seed)
    n = int((total + 4) * SR)
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
        t1 = ch[k + 1][0] if k + 1 < len(ch) else total + 1.5
        add(pad(tones, t1 - t0 + 1.6, rng, att=0.9 if k else 1.6), t0 - (0 if k == 0 else 0.4), 0, 0.22)
        add(sub(root, min(3.0, t1 - t0 + 0.6)), t0, 0, 0.30)
    for t0, m, vel, pan in plan.get("plucks", []):
        add(harp(m, 3.6, vel, rng), t0 + rng.normal(0, 0.003), pan)
    for t0, ms, step, vel in plan.get("gliss", []):
        for i, m in enumerate(ms):
            add(harp(m, 3.0, vel * (0.85 + 0.3 * i / max(1, len(ms) - 1)), rng), t0 + i * step, -0.5 + i / max(1, len(ms) - 1))
    air = lfilter([0.02], [1, -0.975], rng.normal(0, 1, n))
    air /= np.abs(air).max() + 1e-9
    L += air * 0.012
    R += air[::-1] * 0.012
    wl, wr = fftconvolve(L, hall(41))[:n], fftconvolve(R, hall(42))[:n]
    L, R = L * 0.75 + wl * 0.55, R * 0.75 + wr * 0.55
    b_, a_ = butter(2, 40 / (SR / 2), "high")
    L, R = lfilter(b_, a_, L), lfilter(b_, a_, R)
    m = int(total * SR)
    L, R = L[:m], R[:m]
    fi = int(0.12 * SR)
    L[:fi] *= np.linspace(0, 1, fi)
    R[:fi] *= np.linspace(0, 1, fi)
    fade = int(1.8 * SR)
    L[-fade:] *= np.linspace(1, 0, fade) ** 1.5
    R[-fade:] *= np.linspace(1, 0, fade) ** 1.5
    pk = max(np.abs(L).max(), np.abs(R).max()) + 1e-9
    st = (np.stack([L, R], 1) / pk * 0.7 * 32767).astype(np.int16)
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(st.tobytes())
