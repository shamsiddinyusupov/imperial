"""Original bed #23 (not used before): «tipologiya» — a minimalist chamber-string piece: bowed spiccato ostinato
(short off-the-string strokes: detuned saws with a bow-noise attack and a body resonance), a sustained cello/bass
line, legato violins that enter as the catalogue fills, a soft paper «tick» for every plate that appears, a rising
spiccato scale while the plates sort by tone, a held suspended chord as one plate is chosen, an open full-string
chord on the real window, and a quiet cadence. B minor -> D major, 112 BPM.

spiccato_bed(path, total, marks, seed=23)
marks = dict(steps=[t,..], sort, sel, zoom, full, end)
"""
import wave

import numpy as np
from scipy.signal import butter, fftconvolve, lfilter, sosfilt

SR = 48000
BPM = 112
E8 = 60.0 / BPM / 2


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


_BODY = [butter(2, [b / (SR / 2), c / (SR / 2)], "band", output="sos") for b, c in ((260, 420), (900, 1500),
                                                                                     (2400, 3600))]


def bowed(m, dur, rng, att=0.012, rel=0.06, bright=3200, vib=0.0, noise=0.25):
    n = int((dur + rel) * SR)
    t = np.arange(n) / SR
    x = np.zeros(n)
    for det in (-0.0035, 0.0, 0.004):
        f = hz(m) * (1 + det) * (1 + vib * np.sin(2 * np.pi * 5.3 * t + rng.uniform(0, 6)) * np.minimum(1, t / 0.3))
        ph = (np.cumsum(f) / SR + rng.uniform(0, 1)) % 1.0
        x += 2 * ph - 1
    x = sosfilt(butter(2, bright / (SR / 2), "low", output="sos"), x)
    x = 0.6 * x + sum(g * sosfilt(s, x) for g, s in zip((0.8, 0.9, 0.45), _BODY))
    bn = sosfilt(butter(2, [1500 / (SR / 2), 7000 / (SR / 2)], "band", output="sos"), rng.normal(0, 1, n))
    x += noise * bn * np.exp(-t / 0.02) * 3
    env = np.minimum(1, t / att) * np.clip((dur + rel - t) / rel, 0, 1)
    if dur < 0.3:
        env *= np.exp(-t / (dur * 0.9))
    return x * env / (np.abs(x).max() + 1e-9)


def tick(rng):
    t = np.arange(int(0.05 * SR)) / SR
    n = sosfilt(butter(2, [2500 / (SR / 2), 9000 / (SR / 2)], "band", output="sos"), rng.normal(0, 1, len(t)))
    return n / (np.abs(n).max() + 1e-9) * np.exp(-t / 0.006)


def hall(seed, secs=2.6):
    r = np.random.default_rng(seed)
    t = np.arange(int(secs * SR)) / SR
    ir = r.normal(0, 1, len(t)) * np.exp(-t / 0.8)
    ir = lfilter([0.35], [1, -0.55], ir)
    ir[: int(0.02 * SR)] = 0
    return ir / np.sqrt((ir ** 2).sum())


# chord per bar (bass, ostinato pattern of 8 eighths)
Bm, G, D, A, Em, Fs = ((35, [59, 62, 66, 62, 71, 62, 66, 62]), (31, [59, 62, 67, 62, 71, 62, 67, 62]),
                       (38, [57, 62, 66, 62, 69, 62, 66, 62]), (33, [57, 61, 64, 61, 69, 61, 64, 61]),
                       (40, [59, 64, 67, 64, 71, 64, 67, 64]), (42, [58, 61, 66, 61, 70, 61, 66, 61]))
PROG = [Bm, G, D, A]


def spiccato_bed(path, total, marks, seed=23):
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

    steps, sort, sel, zoom, full, end = (marks[k] for k in ("steps", "sort", "sel", "zoom", "full", "end"))
    bar = 8 * E8
    # ostinato from the start until the zoom; density grows with each catalogue step
    t, b = 0.25, 0
    while t < zoom:
        bass, pat = PROG[b % 4]
        lvl = 1 + sum(1 for s in steps if t >= s)            # 1..6
        for k, m in enumerate(pat):
            tt = t + k * E8
            if tt >= zoom:
                break
            if lvl < 2 and k % 2:
                continue
            add(bowed(m, 0.09, rng, 0.006, 0.05, 2600 + 300 * lvl), tt, 0.25 if k % 2 else -0.15,
                0.16 + 0.025 * lvl)
            if lvl >= 4 and k % 2 == 0:
                add(bowed(m + 12, 0.08, rng, 0.006, 0.05, 3800), tt, 0.45, 0.06 + 0.012 * lvl)
        add(bowed(bass, bar * 0.95, rng, 0.15, 0.3, 900, 0.004, 0.05), t, -0.3, 0.13 + 0.015 * min(lvl, 4))
        if lvl >= 3:                                         # legato violas: chord tones
            add(bowed(pat[2] - 12, bar * 0.95, rng, 0.3, 0.4, 1600, 0.005, 0.03), t, 0.2, 0.05 + 0.012 * lvl)
        if lvl >= 5:                                         # violins: long melody notes
            add(bowed(pat[4] + 12, bar * 0.9, rng, 0.35, 0.5, 2800, 0.006, 0.03), t, 0.35, 0.06)
        t += bar
        b += 1
    # a tick per catalogue step (plates landing)
    for s in steps:
        for j in range(6):
            add(tick(rng), s + 0.55 + 0.05 * j, rng.uniform(-0.6, 0.6), 0.10)
    # sorting: rising spiccato scale (B minor) over the sort
    scale = [59, 61, 62, 64, 66, 67, 69, 71, 73, 74, 76, 78, 79, 81, 83, 86]
    dur = max(1.0, sel - sort - 0.6)
    for k, m in enumerate(scale):
        add(bowed(m, 0.1, rng, 0.006, 0.05, 3600), sort + 0.1 + dur * k / len(scale), -0.5 + k / len(scale), 0.2)
    # selection: suspended chord held, then the zoom swell
    for m, p in zip((47, 59, 64, 66, 71), (-0.4, -0.2, 0.0, 0.2, 0.4)):
        add(bowed(m, full - sel + 0.3, rng, 0.5, 0.5, 1800, 0.005, 0.03), sel, p, 0.11)
    # full-screen real window: open D major, warm
    for m, p in zip((38, 50, 57, 62, 66, 69, 74), (-0.4, -0.3, -0.1, 0.0, 0.15, 0.3, 0.45)):
        add(bowed(m, end - full + 0.4, rng, 0.6, 0.9, 2200, 0.006, 0.02), full - 0.1, p, 0.12)
    for k, m in enumerate([74, 76, 78, 81, 78, 76, 74, 69]):
        add(bowed(m, 0.55, rng, 0.08, 0.3, 3000, 0.008, 0.05), full + 0.6 + k * 0.6, 0.3, 0.10)
    # end card: quiet cadence A -> D, a last spiccato figure
    for m in (45, 57, 61, 64):
        add(bowed(m, 1.4, rng, 0.3, 0.6, 1800, 0.005, 0.02), end, 0, 0.11)
    for m in (38, 50, 54, 57, 62, 66):
        add(bowed(m, total - end - 1.0, rng, 0.4, 1.2, 1900, 0.005, 0.02), end + 1.3, 0, 0.11)
    for k, m in enumerate([62, 66, 69, 74, 69, 66, 62]):
        add(bowed(m, 0.09, rng, 0.006, 0.05, 3000), end + 1.4 + k * E8, -0.3 + 0.1 * k, 0.16)

    wl, wr = fftconvolve(L, hall(231))[:n], fftconvolve(R, hall(232))[:n]
    L, R = L * 0.8 + wl * 0.36, R * 0.8 + wr * 0.36
    b_, a_ = butter(2, 55 / (SR / 2), "high")
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
