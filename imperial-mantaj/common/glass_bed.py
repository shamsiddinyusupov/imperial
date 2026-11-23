"""Original bed #26 (not used before): «oltin tomir» — a glass harmonica (rubbed glass: near-sine tones with a slow
swell, a faint inharmonic partial and a soft beating tremolo), a bowed contrabass drone, a granular «pour» shimmer
(tiny bright grains that thicken while the gold runs along the veins), a crystal ping when the still frame comes alive,
one chord per cut, and a quiet cadence on the end card. D major / B minor.

glass_bed(path, total, cuts, alive, end, seed=26)   cuts = scene start times after «alive»
"""
import wave

import numpy as np
from scipy.signal import butter, fftconvolve, lfilter, sosfilt

SR = 48000


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def glass(m, dur, rng, att=0.35, vel=1.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = hz(m) * (1 + 0.0015 * np.sin(2 * np.pi * 0.4 * t + rng.uniform(0, 6)))
    ph = 2 * np.pi * np.cumsum(f) / SR
    x = np.sin(ph) + 0.12 * np.sin(2.0 * ph + 0.3) + 0.05 * np.sin(2.76 * ph)
    trem = 1 + 0.10 * np.sin(2 * np.pi * (3.2 + rng.uniform(-0.4, 0.4)) * t)
    env = (1 - np.exp(-t / att)) * np.clip((dur - t) / 0.6, 0, 1)
    return x * trem * env * vel


def bowed_bass(m, dur, rng):
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = np.zeros(n)
    for d in (-0.002, 0.0, 0.0025):
        ph = (hz(m) * (1 + d) * t + rng.uniform(0, 1)) % 1.0
        x += 2 * ph - 1
    x = sosfilt(butter(2, 420 / (SR / 2), "low", output="sos"), x)
    env = np.minimum(1, t / 0.8) * np.clip((dur - t) / 0.8, 0, 1)
    return x * env / (np.abs(x).max() + 1e-9)


def grains(dur, rng, dens0, dens1):
    n = int(dur * SR)
    out = np.zeros(n + SR)
    t = 0.0
    while t < dur:
        d = dens0 + (dens1 - dens0) * t / dur
        f = rng.uniform(3000, 9000)
        g = int(rng.uniform(0.01, 0.04) * SR)
        tt = np.arange(g) / SR
        s = np.sin(2 * np.pi * f * tt) * np.hanning(g) * rng.uniform(0.3, 1)
        i = int(t * SR)
        out[i:i + g] += s
        t += rng.exponential(1 / d)
    return out[:n]


def ping(m, rng):
    t = np.arange(int(2.5 * SR)) / SR
    return (np.sin(2 * np.pi * hz(m) * t) + 0.3 * np.sin(2 * np.pi * hz(m) * 2.76 * t) * np.exp(-t / 0.3)) * \
        np.exp(-t / 1.0) * (1 - np.exp(-t / 0.002))


def hall(seed, secs=3.4):
    r = np.random.default_rng(seed)
    t = np.arange(int(secs * SR)) / SR
    ir = r.normal(0, 1, len(t)) * np.exp(-t / 1.1)
    ir = lfilter([0.3], [1, -0.6], ir)
    ir[: int(0.025 * SR)] = 0
    return ir / np.sqrt((ir ** 2).sum())


CH = [(38, [62, 66, 69, 74]), (35, [62, 66, 71, 74]), (43, [62, 67, 71, 74]), (33, [61, 64, 69, 73]),
      (38, [62, 66, 69, 78])]          # D  Bm  G  A  D(add)


def glass_bed(path, total, cuts, alive, end, seed=26):
    rng = np.random.default_rng(seed)
    n = int((total + 3) * SR)
    L, R = np.zeros(n), np.zeros(n)

    def add(sig, t0, p=0.0, g=1.0):
        i = int(round(t0 * SR))
        if i < 0 or i >= n:
            return
        j = min(n, i + len(sig))
        L[i:j] += sig[: j - i] * g * (1 - p) ** 0.5
        R[i:j] += sig[: j - i] * g * (1 + p) ** 0.5

    # the pour: a single glass tone swelling, grains thickening
    add(glass(74, alive + 0.8, rng, 0.9), 0.0, -0.2, 0.20)
    add(glass(81, alive + 0.8, rng, 1.4), 0.4, 0.2, 0.12)
    add(bowed_bass(38, alive + 1.0, rng), 0.0, 0, 0.16)
    gr = grains(alive - 0.2, rng, 8, 60)
    gr = sosfilt(butter(2, 2500 / (SR / 2), "high", output="sos"), gr)
    add(gr / (np.abs(gr).max() + 1e-9), 0.1, 0.3, 0.05)
    # alive: crystal ping + first chord
    add(ping(86, rng), alive, 0.2, 0.14)
    add(ping(93, rng), alive + 0.08, -0.3, 0.08)
    seq = [alive] + list(cuts) + [end]
    for k in range(len(seq) - 1):
        a, b = seq[k], seq[k + 1]
        root, tones = CH[k % len(CH)]
        add(bowed_bass(root, b - a + 0.8, rng), a - 0.1, 0, 0.18)
        for j, m in enumerate(tones):
            add(glass(m, b - a + 0.9, rng, 0.45), a + 0.06 * j, -0.45 + 0.3 * j, 0.11)
        # a slow melodic note in the middle of each scene
        mel = [78, 79, 76, 81, 78][k % 5]
        add(glass(mel, (b - a) * 0.6 + 0.6, rng, 0.25), a + (b - a) * 0.35, 0.25, 0.12)
    # end card: D major, a little descending glass figure
    for j, m in enumerate([62, 66, 69, 74, 78]):
        add(glass(m, total - end + 0.5, rng, 0.6), end + 0.05 * j, -0.4 + 0.2 * j, 0.11)
    add(bowed_bass(38, total - end + 0.5, rng), end, 0, 0.2)
    for j, m in enumerate([86, 83, 81, 78]):
        add(ping(m, rng), end + 1.2 + 0.45 * j, 0.3 - 0.2 * j, 0.07)

    wl, wr = fftconvolve(L, hall(261))[:n], fftconvolve(R, hall(262))[:n]
    L, R = L * 0.72 + wl * 0.45, R * 0.72 + wr * 0.45
    b_, a_ = butter(2, 35 / (SR / 2), "high")
    L, R = lfilter(b_, a_, L), lfilter(b_, a_, R)
    m_ = int(total * SR)
    L, R = L[:m_], R[:m_]
    fi = int(0.2 * SR)
    L[:fi] *= np.linspace(0, 1, fi)
    R[:fi] *= np.linspace(0, 1, fi)
    fo = int(2.0 * SR)
    L[-fo:] *= np.linspace(1, 0, fo) ** 1.5
    R[-fo:] *= np.linspace(1, 0, fo) ** 1.5
    pk = max(np.abs(L).max(), np.abs(R).max()) + 1e-9
    st = (np.stack([L, R], 1) / pk * 0.7 * 32767).astype(np.int16)
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(st.tobytes())
