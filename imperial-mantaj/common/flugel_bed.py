"""Original bed #30 (not used before): «jurnal» — a late-evening jazz ballad: muted flugelhorn lead (breathy, soft
attack, slow vibrato), upright bass in two-feel, brushes (swish + soft taps), warm organ-like chord pad, plus a paper
page-turn rustle on every flip. 76 BPM, Eb major ii-V-I colours (Fm9 Bb13 Ebmaj9 Cm9 ...).

flugel_bed(path, total, marks, seed=30)
marks = dict(flips=[t..], end=t)
"""
import wave

import numpy as np
from scipy.signal import butter, fftconvolve, lfilter, sosfilt

SR = 48000
BPM = 76
BEAT = 60.0 / BPM
BAR = 4 * BEAT


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def bp(x, lo, hi):
    return sosfilt(butter(2, [lo / (SR / 2), hi / (SR / 2)], "band", output="sos"), x)


def lp(x, f):
    return sosfilt(butter(2, f / (SR / 2), "low", output="sos"), x)


def flugel(notes, rng):
    total = sum(d for _, d in notes)
    n = int((total + 0.7) * SR)
    t = np.arange(n) / SR
    f = np.zeros(n)
    amp = np.zeros(n)
    acc, prev = 0.0, None
    for m, d in notes:
        i0, i1 = int(acc * SR), int((acc + d) * SR)
        f[i0:i1] = hz(m) if m else (hz(prev) if prev else 220)
        if m and prev:
            g = min(int(0.05 * SR), i1 - i0)
            f[i0:i0 + g] = np.linspace(hz(prev), hz(m), g)
        if m:
            k = np.arange(i1 - i0) / SR
            amp[i0:i1] = np.minimum(1, k / 0.07) * (0.85 + 0.15 * np.exp(-k / 0.3)) * np.clip((d - k) / 0.08, 0.15, 1)
            prev = m
        acc += d
    vib = 0.005 * np.clip((t - 0.3) / 0.4, 0, 1)
    ph = 2 * np.pi * np.cumsum(f * (1 + vib * np.sin(2 * np.pi * 5.0 * t + rng.uniform(0, 6)))) / SR
    x = np.zeros(n)
    for k, a in ((1, 1.0), (2, 0.45), (3, 0.22), (4, 0.10), (5, 0.05)):
        x += a * np.sin(k * ph)
    x = lp(x, 2400)
    breath = bp(rng.normal(0, 1, n), 1200, 5000) * 0.05
    y = (x + breath) * amp
    return y / (np.abs(y).max() + 1e-9)


def bass(m, dur, rng):
    t = np.arange(int((dur + 0.4) * SR)) / SR
    f = hz(m)
    x = np.sin(2 * np.pi * f * t) + 0.35 * np.sin(4 * np.pi * f * t) + 0.12 * np.sin(6 * np.pi * f * t)
    pluck = lp(rng.normal(0, 1, len(t)), 700) * np.exp(-t / 0.015) * 0.3
    return (x * np.exp(-t / 0.9) + pluck) * np.minimum(1, t / 0.006) * np.clip((dur + 0.3 - t) / 0.2, 0, 1)


def pad(tones, dur, rng):
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = np.zeros(n)
    for m in tones:
        for k, a in ((1, 1), (2, 0.5), (4, 0.25)):
            x += a * np.sin(2 * np.pi * hz(m) * k * (1 + rng.uniform(-0.0006, 0.0006)) * t + rng.uniform(0, 6))
    x *= 1 + 0.08 * np.sin(2 * np.pi * 5.5 * t)
    env = np.minimum(1, t / 0.5) * np.clip((dur - t) / 0.6, 0, 1)
    return lp(x, 1800) * env / (np.abs(x).max() + 1e-9)


def swish(rng, dur):
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = bp(rng.normal(0, 1, n), 3000, 9000)
    env = np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 2
    return x * env / (np.abs(x).max() + 1e-9)


def tap(rng):
    t = np.arange(int(0.12 * SR)) / SR
    x = bp(rng.normal(0, 1, len(t)), 2000, 7000) * np.exp(-t / 0.02)
    return x / (np.abs(x).max() + 1e-9)


def page(rng):
    n = int(0.7 * SR)
    t = np.arange(n) / SR
    x = bp(rng.normal(0, 1, n), 1500, 7000)
    crackle = (rng.random(n) < 0.004) * rng.normal(0, 1, n) * 2
    env = np.sin(np.pi * np.clip(t / 0.6, 0, 1)) ** 1.5 * (1 + 0.6 * np.sin(2 * np.pi * 9 * t))
    y = (x + bp(crackle, 2000, 8000)) * env
    return y / (np.abs(y).max() + 1e-9)


def room(seed):
    r = np.random.default_rng(seed)
    t = np.arange(int(2.2 * SR)) / SR
    ir = r.normal(0, 1, len(t)) * np.exp(-t / 0.55)
    ir = lfilter([0.4], [1, -0.5], ir)
    ir[: int(0.015 * SR)] = 0
    return ir / np.sqrt((ir ** 2).sum())


# Eb: Fm9 | Bb13 | Ebmaj9 | Cm9 | Abmaj7 | G7alt | Cm9 | F9 -> Bb
PROG = [(41, [56, 60, 63, 67]), (34, [56, 62, 65, 67]), (39, [55, 58, 62, 65]), (36, [55, 58, 62, 63]),
        (44, [55, 60, 63, 67]), (43, [53, 59, 62, 63]), (36, [55, 58, 62, 63]), (41, [57, 60, 63, 67])]
LINES = [[(72, 1.5), (70, 0.5), (68, 1.0), (67, 1.0)], [(65, 2.0), (0, 0.5), (67, 0.5), (68, 0.5), (70, 0.5)],
         [(70, 1.5), (67, 0.5), (65, 2.0)], [(63, 1.0), (65, 1.0), (67, 2.0)],
         [(72, 1.0), (75, 1.0), (74, 1.0), (72, 1.0)], [(71, 2.0), (0, 1.0), (67, 1.0)],
         [(70, 1.5), (68, 0.5), (67, 1.0), (65, 1.0)], [(63, 3.0), (0, 1.0)]]


def flugel_bed(path, total, marks, seed=30):
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

    end = marks["end"]
    t, b = 0.0, 0
    while t < end - 0.1:
        root, tones = PROG[b % 8]
        add(pad(tones, BAR + 0.4, rng), t, 0.15, 0.11)
        add(bass(root, BEAT * 1.9, rng), t, -0.15, 0.30)
        add(bass(root + 7 if b % 2 == 0 else root + 3, BEAT * 1.9, rng), t + 2 * BEAT, -0.15, 0.24)
        for k in range(4):
            add(swish(rng, BEAT * 0.9), t + k * BEAT, 0.3, 0.035)
            if k % 2 == 1:
                add(tap(rng), t + k * BEAT, 0.25, 0.06)
                add(tap(rng), t + k * BEAT + BEAT * 0.66, 0.25, 0.035)
        if t > BEAT * 2:
            add(flugel([(m, d * BEAT) for m, d in LINES[b % 8]], rng), t, -0.05, 0.20)
        t += BAR
        b += 1
    for tf in marks.get("flips", []):
        add(page(rng), tf, 0.35, 0.16)
    # ending: Ebmaj9 held, flugel answers with a slow rising line
    add(pad([55, 58, 62, 65, 70], total - end + 1.5, rng), end, 0.1, 0.13)
    add(bass(39, total - end + 0.5, rng), end, -0.15, 0.3)
    add(flugel([(67, 0.8), (70, 0.8), (74, 1.0), (75, 2.6)], rng), end + 0.4, -0.05, 0.2)
    add(swish(rng, 1.6), end, 0.3, 0.05)

    wl, wr = fftconvolve(L, room(301))[:n], fftconvolve(R, room(302))[:n]
    L, R = L * 0.85 + wl * 0.3, R * 0.85 + wr * 0.3
    b_, a_ = butter(2, 35 / (SR / 2), "high")
    L, R = lfilter(b_, a_, L), lfilter(b_, a_, R)
    m_ = int(total * SR)
    L, R = L[:m_], R[:m_]
    fi = int(0.05 * SR)
    L[:fi] *= np.linspace(0, 1, fi)
    R[:fi] *= np.linspace(0, 1, fi)
    fo = int(1.6 * SR)
    L[-fo:] *= np.linspace(1, 0, fo) ** 1.5
    R[-fo:] *= np.linspace(1, 0, fo) ** 1.5
    pk = max(np.abs(L).max(), np.abs(R).max()) + 1e-9
    st = (np.stack([L, R], 1) / pk * 0.72 * 32767).astype(np.int16)
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(st.tobytes())
