"""Original bed #11 (not used before): rosewood marimba (partials 1 : 3.93 : 9.2, mallet knock, short resonator
tail), round finger-bass, soft clap + shaker groove, light airy pad. Key of G major, 92 BPM — bright daytime home.

marimba_bed(path, total, plan, seed=11)
  plan = dict(chords=[(t, root_midi, [tones])...], groove=(t0, t1), hits=[(t, midi)...])
"""
import wave

import numpy as np
from scipy.signal import butter, fftconvolve, lfilter

SR = 48000
BPM = 92
BEAT = 60 / BPM


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def mar(m, vel, rng, dur=1.4):
    t = np.arange(int(dur * SR)) / SR
    f = hz(m) * (1 + rng.normal(0, 0.001))
    tail = 0.55 - 0.004 * (m - 55)
    y = np.sin(2 * np.pi * f * t) * np.exp(-t / max(0.18, tail))
    y += 0.35 * np.sin(2 * np.pi * f * 3.93 * t) * np.exp(-t / 0.09)
    y += 0.10 * np.sin(2 * np.pi * f * 9.2 * t) * np.exp(-t / 0.025)
    knock = rng.normal(0, 1, len(t)) * np.exp(-t / 0.004)
    b, a = butter(2, [400 / (SR / 2), 2500 / (SR / 2)], "band")
    y += 0.25 * lfilter(b, a, knock)
    return y * (1 - np.exp(-t / 0.0015)) * vel


def bass(m, dur):
    t = np.arange(int(dur * SR)) / SR
    f = hz(m)
    y = np.sin(2 * np.pi * f * t) + 0.25 * np.sin(4 * np.pi * f * t) * np.exp(-t / 0.08)
    return y * np.exp(-t / 0.45) * (1 - np.exp(-t / 0.004))


def pad(tones, dur, rng):
    t = np.arange(int(dur * SR)) / SR
    out = np.zeros_like(t)
    for m in tones:
        for det in (-0.3, 0.3):
            ph = 2 * np.pi * (hz(m) + det) * t + rng.uniform(0, 6.28)
            out += np.sin(ph) + 0.3 * np.sin(2 * ph) + 0.1 * np.sin(3 * ph)
    env = np.minimum(1, t / 0.9) ** 1.5 * np.clip((dur - t) / 1.0, 0, 1)
    return out * env / (np.abs(out).max() + 1e-9)


def clap(rng):
    t = np.arange(int(0.18 * SR)) / SR
    x = rng.normal(0, 1, len(t))
    env = np.zeros_like(t)
    for d in (0, 0.009, 0.018):
        env += np.exp(-np.clip(t - d, 0, None) / 0.006) * (t >= d)
    env += 0.4 * np.exp(-t / 0.06)
    b, a = butter(2, [900 / (SR / 2), 4500 / (SR / 2)], "band")
    return lfilter(b, a, x) * env


def shaker(rng):
    t = np.arange(int(0.09 * SR)) / SR
    b, a = butter(2, [5500 / (SR / 2), 12000 / (SR / 2)], "band")
    return lfilter(b, a, rng.normal(0, 1, len(t))) * np.exp(-t / 0.02) * np.minimum(1, t / 0.008)


def hall(seed, secs=2.4):
    r = np.random.default_rng(seed)
    t = np.arange(int(secs * SR)) / SR
    ir = r.normal(0, 1, len(t)) * np.exp(-t / 0.55)
    ir = lfilter([0.3], [1, -0.66], ir)
    ir[: int(0.012 * SR)] = 0
    return ir / np.sqrt((ir ** 2).sum())


def marimba_bed(path, total, plan, seed=11):
    rng = np.random.default_rng(seed)
    n = int((total + 3) * SR)
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

    ch = plan["chords"]
    for k, (t0, root, tones) in enumerate(ch):
        t1 = ch[k + 1][0] if k + 1 < len(ch) else total + 1
        add(pad(tones, t1 - t0 + 1.0, rng), t0 - (0 if k == 0 else 0.25), 0, 0.10)
        # marimba arpeggio on eighths: 1 5 8 10 8 5 ...
        seq = [tones[0] + 12, tones[1] + 12, tones[2] + 12, tones[1] + 24, tones[2] + 12, tones[1] + 12]
        t, i = t0, 0
        while t < t1 - 0.05:
            acc = 1.0 if i % 4 == 0 else (0.75 if i % 2 == 0 else 0.6)
            add(mar(seq[i % len(seq)], 0.22 * acc, rng), t + rng.normal(0, 0.004), 0.45 * np.sin(i * 1.1))
            if i % 4 == 0:
                add(bass(root, BEAT * 1.6), t, 0, 0.30)
            if i % 4 == 3:
                add(bass(root + 7, BEAT * 0.8), t, 0, 0.18)
            i += 1
            t += BEAT / 2
    g0, g1 = plan.get("groove", (0, 0))
    t, i = g0, 0
    while t < g1:
        if i % 4 in (1, 3):
            add(clap(rng), t, 0.1, 0.10)
        add(shaker(rng), t + BEAT / 2, 0.35, 0.045)
        add(shaker(rng), t, -0.35, 0.025)
        i += 1
        t += BEAT
    for t0, m in plan.get("hits", []):
        add(mar(m, 0.35, rng, 2.0), t0, 0, 1.0)
        add(mar(m + 12, 0.2, rng, 2.0), t0 + 0.01, 0.2, 1.0)
    wl, wr = fftconvolve(L, hall(111))[:n], fftconvolve(R, hall(112))[:n]
    L, R = L * 0.8 + wl * 0.42, R * 0.8 + wr * 0.42
    b_, a_ = butter(2, 38 / (SR / 2), "high")
    L, R = lfilter(b_, a_, L), lfilter(b_, a_, R)
    m = int(total * SR)
    L, R = L[:m], R[:m]
    fi = int(0.03 * SR)
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
