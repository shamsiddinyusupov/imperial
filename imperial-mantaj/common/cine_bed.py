"""Original bed #29 (not used before): «atelier» — a dark cinematic product-film score with built-in sound design.
Low drone in D minor (detuned saws, slow filter), a sub pulse at 100 BPM, felt-mallet bell motif, taiko-like
hits on every reveal, and precise «clicks» for each part landing (metal tick + soft thud), a roll rumble, a light-
sweep shimmer, a closing chord. Made for assemblies where parts snap into place one by one.

cine_bed(path, total, ev, seed=29)
ev = dict(clicks=[t..], ticks=[t..], rolls=[(t0, t1)..], sweeps=[t..], hits=[t..], risers=[(t0, t1)..], end=t)
"""
import wave

import numpy as np
from scipy.signal import butter, fftconvolve, lfilter, sosfilt

SR = 48000
BPM = 100
BEAT = 60.0 / BPM


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def bp(x, lo, hi, order=2):
    return sosfilt(butter(order, [lo / (SR / 2), hi / (SR / 2)], "band", output="sos"), x)


def lp(x, f, order=2):
    return sosfilt(butter(order, f / (SR / 2), "low", output="sos"), x)


def drone(tones, dur, rng, cut0=300, cut1=900):
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = np.zeros(n)
    for m in tones:
        for d in (-0.09, 0.0, 0.1):
            ph = np.cumsum(np.full(n, hz(m) * (1 + d / 100))) / SR + rng.uniform(0, 1)
            x += 2 * (ph % 1.0) - 1
    cut = cut0 + (cut1 - cut0) * (0.5 - 0.5 * np.cos(2 * np.pi * t / max(dur, 1)))
    y = np.zeros(n)
    blk = 2048
    for i in range(0, n, blk):
        y[i:i + blk] = lp(x[max(0, i - 4096):i + blk], float(cut[i]))[-len(x[i:i + blk]):]
    env = np.minimum(1, t / 1.5) * np.clip((dur - t) / 1.5, 0, 1)
    return y * env / (np.abs(y).max() + 1e-9)


def sub(f0=46, dur=0.5):
    t = np.arange(int(dur * SR)) / SR
    f = f0 * (1 + 0.6 * np.exp(-t / 0.03))
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.18)


def taiko(rng, g=1.0):
    t = np.arange(int(1.2 * SR)) / SR
    f = 62 * (1 + 0.9 * np.exp(-t / 0.02))
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.35)
    skin = lp(rng.normal(0, 1, len(t)), 900) * np.exp(-t / 0.05)
    skin /= np.abs(skin).max() + 1e-9
    return (body + 0.35 * skin) * g


def click(rng, g=1.0):
    t = np.arange(int(0.25 * SR)) / SR
    tick = bp(rng.normal(0, 1, len(t)), 2500, 9000) * np.exp(-t / 0.006)
    tick /= np.abs(tick).max() + 1e-9
    ping = np.sin(2 * np.pi * rng.uniform(2600, 3400) * t) * np.exp(-t / 0.04) * 0.35
    thud = np.sin(2 * np.pi * 110 * t) * np.exp(-t / 0.05) * 0.6
    return (tick + ping + thud) * g


def tick(rng, g=1.0):
    t = np.arange(int(0.08 * SR)) / SR
    x = bp(rng.normal(0, 1, len(t)), 3000, 8000) * np.exp(-t / 0.004)
    return x / (np.abs(x).max() + 1e-9) * g


def roll(dur, rng):
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = lp(rng.normal(0, 1, n), 400) * 0.8 + bp(rng.normal(0, 1, n), 900, 2500) * 0.15
    x *= 1 + 0.25 * np.sin(2 * np.pi * 18 * t)
    env = np.minimum(1, t / 0.15) * np.clip((dur - t) / 0.1, 0, 1)
    return x * env / (np.abs(x).max() + 1e-9)


def shimmer(rng, dur=1.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = np.zeros(n)
    for f in (2093, 2637, 3136, 4186):
        x += np.sin(2 * np.pi * f * t + rng.uniform(0, 6)) * np.exp(-t / 0.5)
    hiss = bp(rng.normal(0, 1, n), 5000, 12000) * np.exp(-t / 0.25) * 0.3
    env = np.minimum(1, t / 0.04)
    return (x / 4 + hiss) * env


def riser(dur, rng):
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = rng.normal(0, 1, n)
    y = np.zeros(n)
    blk = 1024
    for i in range(0, n, blk):
        f = 400 + 6000 * (i / n) ** 2
        y[i:i + blk] = bp(x[max(0, i - 2048):i + blk], f, f * 1.6)[-len(x[i:i + blk]):]
    return y * (t / dur) ** 2 / (np.abs(y).max() + 1e-9)


def mallet(m, rng, g=1.0):
    t = np.arange(int(2.5 * SR)) / SR
    f = hz(m)
    x = np.sin(2 * np.pi * f * t) + 0.3 * np.sin(2 * np.pi * f * 2.76 * t) * np.exp(-t / 0.3)
    return x * np.exp(-t / 0.9) * np.minimum(1, t / 0.004) * g


def hall(seed, secs=3.0):
    r = np.random.default_rng(seed)
    t = np.arange(int(secs * SR)) / SR
    ir = r.normal(0, 1, len(t)) * np.exp(-t / 0.9)
    ir = lfilter([0.35], [1, -0.6], ir)
    ir[: int(0.02 * SR)] = 0
    return ir / np.sqrt((ir ** 2).sum())


MOTIF = [74, 69, 72, 69, 77, 76, 72, 69]


def cine_bed(path, total, ev, seed=29):
    rng = np.random.default_rng(seed)
    n = int((total + 3) * SR)
    L, R = np.zeros(n), np.zeros(n)
    WL, WR = np.zeros(n), np.zeros(n)   # reverb send

    def add(sig, t0, p=0.0, g=1.0, wet=0.3):
        i = int(round(t0 * SR))
        if i < 0 or i >= n:
            return
        j = min(n, i + len(sig))
        s = sig[: j - i] * g
        L[i:j] += s * (1 - p) ** 0.5
        R[i:j] += s * (1 + p) ** 0.5
        WL[i:j] += s * wet * (1 - p) ** 0.5
        WR[i:j] += s * wet * (1 + p) ** 0.5

    end = ev["end"]
    add(drone([38, 45, 50], end + 0.5, rng), 0, -0.1, 0.22, 0.4)
    add(drone([26], end + 0.5, rng, 120, 200), 0, 0, 0.30, 0.1)
    k = 0
    t = 0.0
    while t < end - 0.1:
        add(sub(), t, 0, 0.5 if (k % 4 == 0) else 0.28, 0.05)
        if k % 2 == 1:
            add(tick(rng), t, 0.3 * ((k // 2) % 2 * 2 - 1), 0.06, 0.2)
        if k % 4 == 0:
            add(mallet(MOTIF[(k // 4) % len(MOTIF)], rng), t + BEAT * 0.5, 0.25, 0.11, 0.6)
        t += BEAT
        k += 1
    for t0 in ev.get("clicks", []):
        add(click(rng), t0, rng.uniform(-0.4, 0.4), 0.30, 0.25)
    for t0 in ev.get("ticks", []):
        add(tick(rng), t0, rng.uniform(-0.3, 0.3), 0.16, 0.2)
    for a, b in ev.get("rolls", []):
        add(roll(b - a, rng), a, 0, 0.22, 0.2)
        add(click(rng, 1.2), b, 0, 0.32, 0.3)
    for t0 in ev.get("sweeps", []):
        add(shimmer(rng), t0, 0.2, 0.12, 0.6)
    for a, b in ev.get("risers", []):
        add(riser(b - a, rng), a, 0, 0.16, 0.5)
    for t0 in ev.get("hits", []):
        add(taiko(rng), t0, 0, 0.55, 0.35)
        add(sub(40, 1.0), t0, 0, 0.5, 0.05)
    # end: big hit, shimmer, D minor add9 chord in mallets + drone swell
    add(taiko(rng, 1.2), end, 0, 0.6, 0.4)
    add(shimmer(rng, 2.5), end + 0.05, 0, 0.22, 0.7)
    for j, m in enumerate([62, 69, 72, 76, 81]):
        add(mallet(m, rng), end + 0.25 + 0.12 * j, 0.3 - 0.15 * j, 0.12, 0.7)
    add(drone([38, 45, 53, 57], total - end + 1.5, rng, 400, 1100), end, 0, 0.24, 0.5)

    hl, hr = hall(291), hall(292)
    L = L + fftconvolve(WL, hl)[:n] * 0.9
    R = R + fftconvolve(WR, hr)[:n] * 0.9
    b_, a_ = butter(2, 28 / (SR / 2), "high")
    L, R = lfilter(b_, a_, L), lfilter(b_, a_, R)
    m_ = int(total * SR)
    L, R = L[:m_], R[:m_]
    fo = int(1.4 * SR)
    L[-fo:] *= np.linspace(1, 0, fo) ** 1.5
    R[-fo:] *= np.linspace(1, 0, fo) ** 1.5
    pk = max(np.abs(L).max(), np.abs(R).max()) + 1e-9
    st = (np.stack([L, R], 1) / pk * 0.75 * 32767).astype(np.int16)
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(st.tobytes())
