"""Original calm bed #4 (not used before): soft vibraphone (mallet partials 1:4:10, slow motor tremolo),
warm bowed cello pad in the low register, faint room air, long hall. Key of A major, ~70 BPM.
One chord per shot; a rising vibraphone figure opens the end card.

vibe_bed(path, total, cuts, end_t, seed=4)
  cuts  = times where the picture changes (chord changes there)
  end_t = end-card start
"""
import wave

import numpy as np
from scipy.signal import butter, fftconvolve, lfilter

SR = 48000
BEAT = 60 / 70
CH = [  # (cello root, cello fifth/third, vibraphone tones)
    (45, 52, [69, 73, 76, 80]),        # Amaj9 (A C# E G#)
    (42, 49, [69, 73, 76, 78]),        # F#m7
    (38, 45, [66, 69, 73, 76]),        # Dmaj7
    (40, 47, [68, 71, 74, 76]),        # E (E G# B D)
    (49, 56, [69, 73, 76, 80]),        # A/C#
    (38, 45, [69, 73, 76, 78]),        # Dmaj9
    (45, 52, [69, 71, 73, 76]),        # Aadd9 (end)
]


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def vibe(m, dur, vel):
    t = np.arange(int(dur * SR)) / SR
    f = hz(m)
    y = np.sin(2 * np.pi * f * t) * np.exp(-t / 2.6)
    y += 0.22 * np.sin(2 * np.pi * f * 4.0 * t) * np.exp(-t / 0.5)      # bar overtone
    y += 0.05 * np.sin(2 * np.pi * f * 10.0 * t) * np.exp(-t / 0.12)    # mallet tick
    trem = 1 - 0.22 * (0.5 + 0.5 * np.sin(2 * np.pi * 4.6 * t))         # slow motor
    env = (1 - np.exp(-t / 0.003)) * trem
    return y * env * vel


def cello(notes, dur, rng, att=0.9, rel=1.2):
    t = np.arange(int(dur * SR)) / SR
    out = np.zeros_like(t)
    for m in notes:
        f = hz(m)
        vib = 1 + 0.0035 * np.sin(2 * np.pi * 4.8 * t + rng.uniform(0, 6.28)) * np.clip(t / 1.2, 0, 1)
        ph = 2 * np.pi * f * np.cumsum(vib) / SR
        for n in range(1, 14):
            g = (1 / n) / (1 + (n * f / 1500) ** 3)
            out += np.sin(n * ph + rng.uniform(0, 6.28)) * g
    env = np.minimum(1, t / att) ** 1.5 * np.clip((dur - t) / rel, 0, 1)
    return out * env / (np.abs(out).max() + 1e-9)


def hall(seed, secs=3.6):
    r = np.random.default_rng(seed)
    t = np.arange(int(secs * SR)) / SR
    ir = r.normal(0, 1, len(t)) * np.exp(-t / 0.95)
    ir = lfilter([0.3], [1, -0.72], ir)
    ir[: int(0.018 * SR)] = 0
    return ir / np.sqrt((ir ** 2).sum())


def vibe_bed(path, total, cuts, end_t, seed=4):
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

    bounds = sorted(set([0.0] + [c for c in cuts if 0 < c < end_t])) + [end_t]
    for k in range(len(bounds) - 1):
        t0, t1 = bounds[k], bounds[k + 1]
        root, fifth, tones = CH[min(k, len(CH) - 2)]
        first = k == 0
        add(cello([root, fifth], t1 - t0 + 1.4, rng, att=0.4 if first else 0.9), t0 - (0 if first else 0.35), 0, 0.30)
        t, i = t0 + (0.25 if first else 0.45), 0
        while t < t1 - 0.25:
            add(vibe(tones[(i * 2 + k) % len(tones)], 3.2, 0.17 + 0.04 * rng.random()), t + rng.normal(0, 0.005),
                0.4 * np.sin(i * 1.9 + k))
            i += 1
            t += 2 * BEAT
    root, fifth, tones = CH[-1]
    for i, m in enumerate([69, 73, 76, 80, 81, 85]):
        add(vibe(m, 3.4, 0.12 + 0.015 * i), end_t + 0.15 + i * 0.13, -0.35 + 0.14 * i)
    add(cello([root, fifth, root + 12], total - end_t + 2.5, rng, att=0.7, rel=2.0), end_t, 0, 0.30)
    air = lfilter([0.02], [1, -0.975], rng.normal(0, 1, n))
    air /= np.abs(air).max() + 1e-9
    L += air * 0.014
    R += air[::-1] * 0.014
    wl, wr = fftconvolve(L, hall(31))[:n], fftconvolve(R, hall(32))[:n]
    L, R = L * 0.72 + wl * 0.58, R * 0.72 + wr * 0.58
    b_, a_ = butter(2, 55 / (SR / 2), "high")
    L, R = lfilter(b_, a_, L), lfilter(b_, a_, R)
    m = int(total * SR)
    L, R = L[:m], R[:m]
    fi = int(0.25 * SR)
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
    vibe_bed("/tmp/vibe_test.wav", 26.5, [3.6, 7.9, 10.9, 15.3, 18.5, 20.9], 20.9)
