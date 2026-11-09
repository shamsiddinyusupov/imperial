"""Original bed #10 (not used before): handpan (steel shell modes f, 2f, ~3f with slow beating, soft mallet),
a low 'ding', airy string pad, a soft cloth 'whoosh' for curtain moves. D Kurd scale (D minor), ~80 BPM.

handpan_bed(path, total, plan, seed=10)
  plan = dict(notes=[(t, midi, vel)...], pads=[(t, [tones])...], whoosh=[(t, dur)...], ding=[t...])
"""
import wave

import numpy as np
from scipy.signal import butter, fftconvolve, lfilter

SR = 48000


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def pan_note(m, vel, rng, dur=3.6):
    t = np.arange(int(dur * SR)) / SR
    f = hz(m)
    y = np.sin(2 * np.pi * f * t) * np.exp(-t / 1.5)
    y += 0.42 * np.sin(2 * np.pi * (2 * f + 0.7) * t) * np.exp(-t / 0.9)     # octave mode, slight beating
    y += 0.20 * np.sin(2 * np.pi * (2.98 * f) * t) * np.exp(-t / 0.45)       # compound fifth
    y += 0.06 * np.sin(2 * np.pi * (4.1 * f) * t) * np.exp(-t / 0.15)
    att = 1 - np.exp(-t / 0.004)
    thump = np.exp(-t / 0.012) * rng.normal(0, 0.25, len(t))
    b, a = butter(2, 900 / (SR / 2))
    thump = lfilter(b, a, thump)
    return (y * att + thump) * vel


def pad(tones, dur, rng, att=1.4, rel=1.6):
    t = np.arange(int(dur * SR)) / SR
    out = np.zeros_like(t)
    for m in tones:
        for det in (-0.35, 0.0, 0.33):
            ph = 2 * np.pi * (hz(m) + det) * t + rng.uniform(0, 6.28)
            for h in range(1, 6):
                out += np.sin(h * ph) / h ** 1.8
    env = np.minimum(1, t / att) ** 1.7 * np.clip((dur - t) / rel, 0, 1)
    return out * env / (np.abs(out).max() + 1e-9)


def whoosh(dur, rng):
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = rng.normal(0, 1, n)
    out = np.zeros(n)
    # sweeping band-pass for a soft fabric slide
    for k in range(8):
        s, e = k * n // 8, (k + 1) * n // 8
        fc = 500 + 2200 * (k / 7)
        b, a = butter(2, [fc * 0.6 / (SR / 2), fc * 1.6 / (SR / 2)], "band")
        out[s:e] = lfilter(b, a, x[s:e])
    env = np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 1.5
    return out * env


def hall(seed, secs=3.4):
    r = np.random.default_rng(seed)
    t = np.arange(int(secs * SR)) / SR
    ir = r.normal(0, 1, len(t)) * np.exp(-t / 1.0)
    ir = lfilter([0.3], [1, -0.72], ir)
    ir[: int(0.02 * SR)] = 0
    return ir / np.sqrt((ir ** 2).sum())


def handpan_bed(path, total, plan, seed=10):
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

    pads = plan.get("pads", [])
    for k, (t0, tones) in enumerate(pads):
        t1 = pads[k + 1][0] if k + 1 < len(pads) else total + 1
        add(pad(tones, t1 - t0 + 1.6, rng), t0 - (0 if k == 0 else 0.5), 0, 0.16)
    for i, (t0, m, vel) in enumerate(plan.get("notes", [])):
        add(pan_note(m, vel, rng), t0 + rng.normal(0, 0.005), 0.4 * np.sin(i * 1.9))
    for t0 in plan.get("ding", []):
        add(pan_note(50, 0.9, rng, 5.0), t0, 0, 1.0)
    for t0, d in plan.get("whoosh", []):
        add(whoosh(d, rng), t0, 0.2, 0.10)
    wl, wr = fftconvolve(L, hall(101))[:n], fftconvolve(R, hall(102))[:n]
    L, R = L * 0.72 + wl * 0.55, R * 0.72 + wr * 0.55
    b_, a_ = butter(2, 40 / (SR / 2), "high")
    L, R = lfilter(b_, a_, L), lfilter(b_, a_, R)
    m = int(total * SR)
    L, R = L[:m], R[:m]
    fi = int(0.05 * SR)
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
