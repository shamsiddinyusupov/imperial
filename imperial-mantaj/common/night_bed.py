"""Original bed #14 (not used before): summer night — crickets, an airy breathy flute melody (D minor pentatonic),
a soft low string pad and a slow heartbeat pulse; lifts to F major on the end card. 72 BPM.

night_bed(path, total, end_at, seed=14)
"""
import wave

import numpy as np
from scipy.signal import butter, fftconvolve, lfilter

SR = 48000
BPM = 72
BEAT = 60 / BPM


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def flute(m, dur, rng, vel=1.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    vib = 1 + 0.004 * np.sin(2 * np.pi * 5.2 * t) * np.clip((t - 0.25) / 0.4, 0, 1)
    ph = 2 * np.pi * np.cumsum(hz(m) * vib) / SR
    tone = np.sin(ph) + 0.22 * np.sin(2 * ph) + 0.08 * np.sin(3 * ph) + 0.03 * np.sin(4 * ph)
    br = rng.normal(0, 1, n)
    f0 = hz(m)
    b, a = butter(2, [f0 * 0.8 / (SR / 2), min(0.99, f0 * 3.0 / (SR / 2))], "band")
    br = lfilter(b, a, br)
    br /= np.abs(br).max() + 1e-9
    att = np.clip(t / 0.09, 0, 1) ** 1.5
    rel = np.clip((dur - t) / 0.25, 0, 1)
    chiff = rng.normal(0, 1, n) * np.exp(-t / 0.02) * 0.25
    y = (tone * 0.85 + br * 0.18 * (0.6 + 0.4 * np.exp(-t / 0.15)) + chiff) * att * rel
    return y * vel


def pad(tones, dur, rng):
    n = int(dur * SR)
    t = np.arange(n) / SR
    out = np.zeros(n)
    for m in tones:
        for det in (-0.25, 0.0, 0.3):
            f = hz(m) + det
            ph = (f * t + rng.uniform(0, 1)) % 1.0
            out += 2 * ph - 1
    b, a = butter(2, 700 / (SR / 2), "low")
    out = lfilter(b, a, out)
    env = np.minimum(1, t / 1.2) ** 1.5 * np.clip((dur - t) / 1.4, 0, 1)
    return out * env / (np.abs(out).max() + 1e-9)


def beat(rng):
    d = 0.35
    t = np.arange(int(d * SR)) / SR
    f = 55 * np.exp(-t / 0.08) + 38
    y = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.12)
    return y


def cricket(rng):
    """one chirp: 3-4 short 4.6 kHz pulses"""
    f = rng.uniform(4300, 5000)
    pulses = rng.integers(3, 5)
    d = 0.022
    out = []
    for _ in range(pulses):
        t = np.arange(int(d * SR)) / SR
        out.append(np.sin(2 * np.pi * f * t) * np.sin(np.pi * t / d) ** 2)
        out.append(np.zeros(int(0.014 * SR)))
    return np.concatenate(out)


def hall(seed, secs=3.0):
    r = np.random.default_rng(seed)
    t = np.arange(int(secs * SR)) / SR
    ir = r.normal(0, 1, len(t)) * np.exp(-t / 0.9)
    ir = lfilter([0.3], [1, -0.7], ir)
    ir[: int(0.02 * SR)] = 0
    return ir / np.sqrt((ir ** 2).sum())


# (beat offset, midi, beats) — D minor pentatonic phrase, answered; last phrase rises
MEL = [(0, 69, 1.5), (1.5, 72, 0.5), (2, 74, 2), (4.5, 72, 0.5), (5, 69, 1), (6, 67, 2),
       (8, 69, 1), (9, 72, 1), (10, 77, 1.5), (11.5, 76, 0.5), (12, 74, 3),
       (16, 69, 1.5), (17.5, 72, 0.5), (18, 74, 1), (19, 76, 1), (20, 77, 3)]
CHORDS = [(0, [50, 57, 60, 65]), (8, [46, 53, 58, 62]), (16, [48, 55, 58, 64]), (24, [50, 57, 60, 65])]


def night_bed(path, total, end_at, seed=14):
    rng = np.random.default_rng(seed)
    n = int((total + 4) * SR)
    L, R = np.zeros(n), np.zeros(n)

    def add(sig, t0, p=0.0, g=1.0):
        i = int(round(t0 * SR))
        if i >= n or i < 0:
            return
        j = min(n, i + len(sig))
        L[i:j] += sig[: j - i] * g * (1 - p) ** 0.5
        R[i:j] += sig[: j - i] * g * (1 + p) ** 0.5

    # crickets all the way, two "fields" left/right
    for side in (-0.7, 0.6):
        t = rng.uniform(0, 0.4)
        while t < total + 1:
            add(cricket(rng), t, side, 0.05)
            t += rng.uniform(0.55, 0.9)
    # quiet night air
    air = rng.normal(0, 1, n)
    b, a = butter(1, 400 / (SR / 2), "low")
    air = lfilter(b, a, air)
    air /= np.abs(air).max()
    L += air * 0.03
    R += np.roll(air, 2000) * 0.03
    # pad chords loop until the end card, then F major lift
    loop = 32 * BEAT
    t0 = 0.0
    while t0 < end_at:
        for k, (b_, tones) in enumerate(CHORDS[:-1]):
            ts = t0 + b_ * BEAT
            te = min(end_at + 0.6, t0 + CHORDS[k + 1][0] * BEAT + 0.8)
            if ts < end_at:
                add(pad(tones, te - ts + 1.2, rng), ts, 0, 0.13)
        t0 += 24 * BEAT
    add(pad([41, 53, 57, 60, 64], total - end_at + 2, rng), end_at - 0.3, 0, 0.2)
    # heartbeat pulse (lub-dub) every 2 beats, softer later
    t = BEAT * 2
    while t < total - 1.5:
        g = 0.22 if t < end_at else 0.14
        add(beat(rng), t, 0, g)
        add(beat(rng), t + 0.28, 0, g * 0.55)
        t += 2 * BEAT
    # flute melody (starts after the hook settles), repeats until end card
    start = 1.2
    tt = start
    while tt < end_at - 1.0:
        for b_, m, d in MEL:
            ts = tt + b_ * BEAT
            if ts + d * BEAT > end_at + 0.8:
                break
            add(flute(m, d * BEAT + 0.1, rng, 0.9), ts, 0.15, 0.2)
        tt += 24 * BEAT
    # end card: final long flute note A over F major
    add(flute(81, 2.6, rng, 0.8), end_at + 0.2, 0.1, 0.11)
    add(flute(77, 2.2, rng, 0.7), end_at + 1.9, -0.1, 0.09)

    wl, wr = fftconvolve(L, hall(141))[:n], fftconvolve(R, hall(142))[:n]
    L, R = L * 0.75 + wl * 0.45, R * 0.75 + wr * 0.45
    b_, a_ = butter(2, 32 / (SR / 2), "high")
    L, R = lfilter(b_, a_, L), lfilter(b_, a_, R)
    m = int(total * SR)
    L, R = L[:m], R[:m]
    fi = int(0.4 * SR)
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


if __name__ == "__main__":
    night_bed("/tmp/claude-0/-home-claude/29c18e40-edfd-55e7-a3e1-da5539b3418b/scratchpad/night_test.wav", 22, 16.5)
    print("ok")
