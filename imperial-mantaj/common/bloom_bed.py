"""Original calm bed #3 (not used before): warm analogue-style string pad whose filter 'blooms' open, soft celesta
(FM bell) motif, round sine bass, faint tape air, long hall. Key of E♭, ~72 BPM. Silent until `start` (the bloom),
one chord per section, a short rising celesta figure at the end card.

bloom_bed(path, total, start, sections, end_t, seed=9)
  sections = list of section start times (>= start); chords advance at each
"""
import wave

import numpy as np
from scipy.signal import butter, fftconvolve, lfilter

SR = 48000
CH = [  # (bass, pad tones, celesta tones)
    (51, [58, 62, 65, 70], [77, 79, 82, 74]),       # E♭maj9
    (48, [55, 58, 62, 65], [79, 75, 74, 72]),       # Cm9
    (44, [55, 60, 63, 67], [79, 75, 72, 74]),       # A♭maj7
    (46, [53, 58, 60, 65], [77, 74, 72, 70]),       # B♭sus4
    (51, [55, 58, 62, 65], [74, 77, 79, 82]),       # E♭add9 (end)
]
BEAT = 60 / 72


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def pad(notes, dur, rng, cut0, cut1, att=0.9, rel=1.4):
    t = np.arange(int(dur * SR)) / SR
    cutoff = cut0 + (cut1 - cut0) * np.clip(t / 1.6, 0, 1) ** 1.5          # the bloom
    out = np.zeros_like(t)
    for m in notes:
        for det in (-0.004, 0.0, 0.004):
            f = hz(m) * (1 + det)
            ph = 2 * np.pi * f * t + rng.uniform(0, 6.28)
            for n in range(1, 18):
                g = 1 / n / (1 + (n * f / cutoff) ** 4)
                out += np.sin(n * ph) * g
    env = np.minimum(1, t / att) * np.clip((dur - t) / rel, 0, 1)
    return out * env / (np.abs(out).max() + 1e-9)


def bell(m, dur, vel):
    t = np.arange(int(dur * SR)) / SR
    f = hz(m)
    idx = 2.2 * np.exp(-t / 0.35)
    y = np.sin(2 * np.pi * f * t + idx * np.sin(2 * np.pi * f * 3.5 * t))
    y += 0.3 * np.sin(2 * np.pi * f * 2 * t) * np.exp(-t / 0.4)
    env = (1 - np.exp(-t / 0.004)) * np.exp(-t / 1.1)
    return y * env * vel


def bass(m, dur):
    t = np.arange(int(dur * SR)) / SR
    y = np.sin(2 * np.pi * hz(m) * t) + 0.25 * np.sin(2 * np.pi * hz(m) * 2 * t)
    env = np.minimum(1, t / 0.5) * np.clip((dur - t) / 0.9, 0, 1)
    return y * env / 1.25


def hall(seed, secs=3.4):
    r = np.random.default_rng(seed)
    t = np.arange(int(secs * SR)) / SR
    ir = r.normal(0, 1, len(t)) * np.exp(-t / 0.85)
    ir = lfilter([0.3], [1, -0.7], ir)
    ir[: int(0.015 * SR)] = 0
    return ir / np.sqrt((ir ** 2).sum())


def bloom_bed(path, total, start, sections, end_t, seed=9):
    rng = np.random.default_rng(seed)
    n = int((total + 3.5) * SR)
    L, R = np.zeros(n), np.zeros(n)

    def add(sig, t0, pan=0.0, g=1.0):
        i = int(t0 * SR)
        if i >= n or i < 0:
            return
        j = min(n, i + len(sig))
        L[i:j] += sig[: j - i] * g * (1 - pan) ** 0.5
        R[i:j] += sig[: j - i] * g * (1 + pan) ** 0.5

    bounds = sorted(set([start] + [s for s in sections if start <= s < end_t])) + [end_t]
    for k in range(len(bounds) - 1):
        t0, t1 = bounds[k], bounds[k + 1]
        b, pd, ce = CH[min(k, len(CH) - 2)]
        first = k == 0
        add(pad(pd, t1 - t0 + 1.5, rng, 260 if first else 900, 2400, att=0.25 if first else 0.8), t0 - (0 if first else 0.3), 0, 0.30)
        add(bass(b - 12 if b > 47 else b, t1 - t0 + 1.0), t0, 0, 0.22)
        # celesta: one note every two beats, wandering over the chord's tones
        t, i = t0 + (0.45 if first else BEAT), 0
        while t < t1 - 0.2:
            add(bell(ce[i % len(ce)], 2.2, 0.16 + 0.04 * rng.random()), t + rng.normal(0, 0.006), 0.35 * np.sin(i * 1.7))
            i += 1
            t += 2 * BEAT
    # end card: rising figure + final chord
    b, pd, ce = CH[-1]
    for i, m in enumerate([70, 74, 77, 79, 82, 86]):
        add(bell(m, 2.6, 0.13 + 0.015 * i), end_t + 0.1 + i * 0.11, -0.3 + 0.12 * i)
    add(pad(pd, total - end_t + 2.5, rng, 1200, 2600, att=0.6, rel=2.0), end_t, 0, 0.30)
    add(bass(b - 12, total - end_t + 2.5), end_t, 0, 0.22)
    # tape air from the bloom on
    air = lfilter([0.02], [1, -0.97], rng.normal(0, 1, n))
    air /= np.abs(air).max() + 1e-9
    gate = np.clip((np.arange(n) / SR - start) / 0.8, 0, 1)
    L += air * gate * 0.018
    R += air[::-1] * gate * 0.018
    wl, wr = fftconvolve(L, hall(21))[:n], fftconvolve(R, hall(22))[:n]
    L, R = L * 0.75 + wl * 0.55, R * 0.75 + wr * 0.55
    b_, a_ = butter(2, 60 / (SR / 2), "high")
    L, R = lfilter(b_, a_, L), lfilter(b_, a_, R)
    m = int(total * SR)
    L, R = L[:m], R[:m]
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
