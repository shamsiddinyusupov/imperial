"""Original bed #9 (not used before): night-city electric piano (FM 'tine' Rhodes: 1:1 carrier with a 14x bell
partial and soft tremolo), a slow pulsing sub, brushed hats only after the 'solution' point, warm tape air.
Key of C minor -> Ab major, ~78 BPM. Sits under a narrator (duck it with the voice).

rhodes_bed(path, total, plan, seed=9)
  plan = dict(chords=[(t, root_midi, [tones])...], hats=(t0, t1), hits=[t...])
"""
import wave

import numpy as np
from scipy.signal import butter, fftconvolve, lfilter

SR = 48000
BPM = 78
BEAT = 60 / BPM


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def ep(m, vel, rng, dur=3.2):
    t = np.arange(int(dur * SR)) / SR
    f = hz(m) * (1 + rng.normal(0, 0.0008))
    idx = 1.6 * vel * np.exp(-t / 0.35) + 0.25
    y = np.sin(2 * np.pi * f * t + idx * np.sin(2 * np.pi * f * t))
    y += 0.10 * np.sin(2 * np.pi * f * 14 * t) * np.exp(-t / 0.02)          # tine bell
    env = (1 - np.exp(-t / 0.003)) * np.exp(-t / (1.6 - 0.6 * (m - 48) / 36))
    return y * env * vel


def chord_sig(tones, dur, rng, vel=0.55):
    out = np.zeros(int((dur + 3.4) * SR) + int(3.2 * SR))
    for k, m in enumerate(tones):
        s = ep(m, vel * (0.9 + 0.1 * rng.random()), rng)
        o = int((k * 0.018 + rng.uniform(0, 0.006)) * SR)          # gentle strum
        out[o:o + len(s)] += s
    t = np.arange(len(out)) / SR
    return out * (1 + 0.18 * np.sin(2 * np.pi * 4.2 * t))          # tremolo


def sub(root, dur):
    t = np.arange(int(dur * SR)) / SR
    pulse = 0.55 + 0.45 * np.cos(2 * np.pi * t / BEAT) ** 8
    return np.sin(2 * np.pi * hz(root - 12) * t) * pulse * np.minimum(1, t / 0.08) * np.clip((dur - t) / 0.3, 0, 1)


def hat(rng):
    t = np.arange(int(0.12 * SR)) / SR
    b, a = butter(2, [6000 / (SR / 2), 14000 / (SR / 2)], "band")
    return lfilter(b, a, rng.normal(0, 1, len(t))) * np.exp(-t / 0.03)


def swell(dur=1.6):
    t = np.arange(int(dur * SR)) / SR
    r = np.random.default_rng(5).normal(0, 1, len(t))
    b, a = butter(2, [300 / (SR / 2), 3000 / (SR / 2)], "band")
    return lfilter(b, a, r) * (t / dur) ** 2.5 * np.clip((dur - t) / 0.05, 0, 1)


def hall(seed, secs=3.0):
    r = np.random.default_rng(seed)
    t = np.arange(int(secs * SR)) / SR
    ir = r.normal(0, 1, len(t)) * np.exp(-t / 0.85)
    ir = lfilter([0.3], [1, -0.7], ir)
    ir[: int(0.02 * SR)] = 0
    return ir / np.sqrt((ir ** 2).sum())


def rhodes_bed(path, total, plan, seed=9):
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
        t1 = ch[k + 1][0] if k + 1 < len(ch) else total + 1
        add(chord_sig(tones, t1 - t0, rng), t0, -0.15, 0.30)
        # a soft re-strike on beat 3 of each long chord
        if t1 - t0 > 2 * BEAT * 2:
            add(chord_sig(tones[1:], t1 - t0, rng, 0.35), t0 + 2 * BEAT, 0.2, 0.22)
        add(sub(root, t1 - t0 + 0.2), t0, 0, 0.32)
    h0, h1 = plan.get("hats", (0, 0))
    t, i = h0, 0
    while t < h1:
        add(hat(rng), t, 0.35 * (1 if i % 2 else -1), 0.05 if i % 2 else 0.03)
        t += BEAT / 2
        i += 1
    for t0 in plan.get("hits", []):
        add(swell(), t0 - 1.6, 0, 0.12)
    air = lfilter([0.02], [1, -0.97], rng.normal(0, 1, n))
    air /= np.abs(air).max() + 1e-9
    L += air * 0.008
    R += air[::-1] * 0.008
    wl, wr = fftconvolve(L, hall(91))[:n], fftconvolve(R, hall(92))[:n]
    L, R = L * 0.75 + wl * 0.5, R * 0.75 + wr * 0.5
    b_, a_ = butter(2, 35 / (SR / 2), "high")
    L, R = lfilter(b_, a_, L), lfilter(b_, a_, R)
    m = int(total * SR)
    L, R = L[:m], R[:m]
    fi = int(0.05 * SR)
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
