"""Original bed #28 (not used before): «galereya» — a slow solo cello over felt piano, like a quiet museum room.
Cello: three detuned saws through body formants, slow bow attack, delayed vibrato, bow hiss. Felt piano: soft
hammers, slightly inharmonic partials, a low-pass «felt». 72 BPM, D major (D A/C# Bm G | G D/F# Em A), no drums.
Piano alone for the hook, the cello enters with the gallery, lifts with the view, softens, cadence G-A-D at the end.

cello_bed(path, total, marks, seed=28)
marks = dict(cello, lift, soft, end)
"""
import wave

import numpy as np
from scipy.signal import butter, fftconvolve, lfilter, sosfilt

SR = 48000
BPM = 72
BEAT = 60.0 / BPM
BAR = 4 * BEAT


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def piano(m, dur, rng, vel=1.0):
    n = int((dur + 1.6) * SR)
    t = np.arange(n) / SR
    f0 = hz(m)
    x = np.zeros(n)
    for k in range(1, 9):
        fk = f0 * k * np.sqrt(1 + 0.0004 * k * k)
        if fk > 7000:
            break
        dec = 2.6 / (1 + 0.55 * (k - 1)) * (1.2 if m < 55 else 1.0)
        x += np.sin(2 * np.pi * fk * t + rng.uniform(0, 6)) * np.exp(-t / dec) / k ** 1.25
    hammer = sosfilt(butter(2, 1800 / (SR / 2), "low", output="sos"), rng.normal(0, 1, n)) * np.exp(-t / 0.012) * 0.12
    x = (x + hammer) * np.minimum(1, t / 0.006)
    rel = np.clip((dur + 0.5 - t) / 0.5, 0, 1)
    x = sosfilt(butter(2, (1600 + 900 * vel) / (SR / 2), "low", output="sos"), x * rel)
    return x * vel / (np.abs(x).max() + 1e-9)


def cello(notes, rng):
    """notes: list of (midi, dur) legato with short slides."""
    total = sum(d for _, d in notes)
    n = int((total + 0.8) * SR)
    t = np.arange(n) / SR
    f = np.zeros(n)
    acc, prev = 0.0, None
    for m, d in notes:
        i0, i1 = int(acc * SR), int((acc + d) * SR)
        f[i0:i1] = hz(m)
        if prev is not None:
            g = min(int(0.09 * SR), i1 - i0)
            f[i0:i0 + g] = np.linspace(hz(prev), hz(m), g)
        prev, acc = m, acc + d
    f[int(acc * SR):] = hz(prev)
    vib = 0.0045 * np.clip((t - 0.35) / 0.5, 0, 1)
    x = np.zeros(n)
    for dt in (-0.05, 0.0, 0.06):
        fr = f * (1 + dt / 100) * (1 + vib * np.sin(2 * np.pi * 5.3 * t + rng.uniform(0, 6)))
        ph = np.cumsum(fr) / SR + rng.uniform(0, 1)
        x += 2 * (ph % 1.0) - 1
    body = np.zeros(n)
    for fc, q, g in ((220, 3, 1.0), (520, 4, 0.8), (1250, 5, 0.45), (2600, 6, 0.15)):
        bw = fc / q
        body += g * sosfilt(butter(2, [(fc - bw / 2) / (SR / 2), (fc + bw / 2) / (SR / 2)], "band", output="sos"), x)
    hiss = sosfilt(butter(2, [2500 / (SR / 2), 7000 / (SR / 2)], "band", output="sos"), rng.normal(0, 1, n)) * 0.02
    env = np.minimum(1, t / 0.18) * np.clip((total + 0.5 - t) / 0.6, 0, 1)
    sw = 0.8 + 0.2 * np.sin(np.pi * np.clip(t / max(total, 0.1), 0, 1))
    y = (body + hiss) * env * sw
    return y / (np.abs(y).max() + 1e-9)


def strings(tones, dur, rng):
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = np.zeros(n)
    for m in tones:
        for dt in (-0.08, 0.0, 0.07):
            ph = np.cumsum(np.full(n, hz(m) * (1 + dt / 100))) / SR + rng.uniform(0, 1)
            x += 2 * (ph % 1.0) - 1
    x = sosfilt(butter(2, 1400 / (SR / 2), "low", output="sos"), x)
    env = np.minimum(1, t / 1.0) * np.clip((dur - t) / 1.0, 0, 1)
    return x * env / (np.abs(x).max() + 1e-9)


def room(seed, secs=2.6):
    r = np.random.default_rng(seed)
    t = np.arange(int(secs * SR)) / SR
    ir = r.normal(0, 1, len(t)) * np.exp(-t / 0.75)
    ir = lfilter([0.4], [1, -0.55], ir)
    ir[: int(0.018 * SR)] = 0
    return ir / np.sqrt((ir ** 2).sum())


# (bass, chord tones) per bar: D A/C# Bm G | G D/F# Em A
PROG = [(38, [62, 66, 69]), (37, [61, 64, 69]), (35, [62, 66, 71]), (31, [62, 67, 71]),
        (31, [62, 67, 71]), (30, [62, 66, 69]), (28, [64, 67, 71]), (33, [61, 64, 69])]
CEL = [[(54, 2), (57, 1), (59, 1)], [(57, 3), (52, 1)], [(54, 2), (50, 1), (52, 1)], [(55, 4)],
       [(59, 2), (57, 1), (55, 1)], [(54, 3), (57, 1)], [(55, 2), (52, 2)], [(57, 4)]]
CEL_HI = [[(66, 2), (69, 1), (71, 1)], [(69, 3), (64, 1)], [(66, 2), (62, 1), (64, 1)], [(67, 4)]]


def cello_bed(path, total, marks, seed=28):
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

    ce, lift, soft, end = (marks[k] for k in ("cello", "lift", "soft", "end"))

    def piano_bar(b, t, vel=0.8):
        bass, tones = PROG[b % 8]
        add(piano(bass, BAR, rng, vel * 0.9), t, -0.2, 0.30)
        pat = [tones[0] + 12, tones[1] + 12, tones[2] + 12, tones[1] + 12]
        for k, m in enumerate(pat * 2):
            add(piano(m, BEAT * 0.9, rng, vel * (0.75 if k % 2 else 0.9)), t + k * BEAT / 2, 0.2 - 0.1 * (k % 3),
                0.13)

    t, b = 0.0, 0
    while t < end - 0.05:
        vel = 0.85 if t < lift else 0.95
        if soft <= t < soft + 2 * BAR:
            vel = 0.7
        piano_bar(b, t, vel)
        if t + BAR > ce:
            line = CEL_HI[b % 4] if lift <= t < soft else CEL[b % 8]
            start = max(t, ce)
            cut = [(m, d * BEAT) for m, d in line]
            if start > t:
                skip = start - t
                cut2 = []
                acc = 0.0
                for m, d in cut:
                    if acc + d > skip:
                        cut2.append((m, acc + d - max(skip, acc)))
                    acc += d
                cut = cut2
            if cut:
                add(cello(cut, rng), start, -0.05, 0.26 if lift <= t < soft else 0.22)
        if t >= lift:
            add(strings(PROG[b % 8][1], BAR + 0.8, rng), t, 0.1, 0.05)
        t += BAR
        b += 1
    # cadence G - A - D
    for k, (bass, tones) in enumerate([(31, [62, 67, 71]), (33, [61, 64, 69])]):
        tt = end + k * BAR / 2
        add(piano(bass, BAR / 2, rng, 0.9), tt, -0.2, 0.3)
        for j, m in enumerate(tones):
            add(piano(m + 12, BAR / 2, rng, 0.8), tt + j * 0.05, 0.15, 0.12)
    add(cello([(57, BAR / 2), (61, BAR / 2), (62, 2.5 * BEAT)], rng), end, -0.05, 0.24)
    tf = end + BAR
    add(piano(26, total - tf + 1.5, rng, 0.9), tf, -0.2, 0.32)
    for j, m in enumerate([62, 66, 69, 74, 78]):
        add(piano(m, total - tf + 1.5, rng, 0.75), tf + j * 0.11, 0.25 - 0.1 * j, 0.12)
    add(strings([62, 66, 69], total - tf + 1.0, rng), tf, 0.1, 0.06)

    wl, wr = fftconvolve(L, room(281))[:n], fftconvolve(R, room(282))[:n]
    L, R = L * 0.82 + wl * 0.32, R * 0.82 + wr * 0.32
    b_, a_ = butter(2, 35 / (SR / 2), "high")
    L, R = lfilter(b_, a_, L), lfilter(b_, a_, R)
    m_ = int(total * SR)
    L, R = L[:m_], R[:m_]
    fi = int(0.06 * SR)
    L[:fi] *= np.linspace(0, 1, fi)
    R[:fi] *= np.linspace(0, 1, fi)
    fo = int(1.6 * SR)
    L[-fo:] *= np.linspace(1, 0, fo) ** 1.5
    R[-fo:] *= np.linspace(1, 0, fo) ** 1.5
    pk = max(np.abs(L).max(), np.abs(R).max()) + 1e-9
    st = (np.stack([L, R], 1) / pk * 0.7 * 32767).astype(np.int16)
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(st.tobytes())
