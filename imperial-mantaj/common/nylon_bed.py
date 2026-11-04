"""Original calm bed #2 (not used before): nylon-string guitar arpeggios (Karplus–Strong), soft bowed-string pad,
low drone, room air and a long hall. Key of F, ~66 BPM. One chord per shot; a slow harp-like glissando opens the end card.

nylon_bed(path, total, cuts, end_t, seed=5)
  cuts  = times where the picture changes (chord changes there)
  end_t = end-card start (gliss + final F add9)
"""
import wave

import numpy as np
from scipy.signal import butter, fftconvolve, lfilter

SR = 48000
CHORDS = [  # (bass, [arpeggio tones], [pad tones])
    (41, [53, 60, 64, 67, 69], [60, 64, 69]),          # Fmaj9
    (38, [50, 57, 60, 64, 65], [57, 60, 65]),          # Dm9
    (46, [53, 57, 62, 64, 65], [57, 62, 65]),          # B♭maj9
    (45, [52, 57, 60, 64, 69], [60, 64, 69]),          # Fmaj7/A
    (43, [50, 53, 57, 58, 62], [53, 58, 62]),          # Gm9
    (48, [55, 60, 65, 67, 70], [60, 65, 67]),          # C9sus4
    (41, [53, 60, 67, 69, 72], [60, 67, 69]),          # F add9 (end)
]
PATTERN = [0, 2, 3, 4, 3, 2, 1, 3]                     # eighth-note arpeggio over the chord tones
EIGHTH = 60 / 66 / 2


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def pluck(m, dur, vel, rng, bright=0.5, loss=0.996):
    f = hz(m)
    N = max(2, int(round(SR / f)))
    exc = rng.uniform(-1, 1, N)
    k = int(2 + (1 - bright) * 6)                       # softer attack for nylon
    exc = np.convolve(exc, np.ones(k) / k, "same")
    exc = exc - np.roll(exc, int(0.17 * N))             # pluck position
    x = np.zeros(int(dur * SR))
    x[:N] = exc
    a = np.zeros(N + 2)
    a[0], a[N], a[N + 1] = 1.0, -0.5 * loss, -0.5 * loss
    y = lfilter([1.0], a, x)
    y = lfilter([0.35], [1, -0.65], y)                  # body warmth
    rel = int(0.25 * SR)
    y[-rel:] *= np.linspace(1, 0, rel)
    return y / (np.abs(y).max() + 1e-9) * vel


def pad(notes, dur, rng, att=1.4, rel=1.6):
    t = np.arange(int(dur * SR)) / SR
    out = np.zeros_like(t)
    for m in notes:
        for det in (-0.0035, 0.0, 0.0035):
            f = hz(m) * (1 + det)
            vib = 1 + 0.0012 * np.sin(2 * np.pi * (5.1 + rng.uniform(-0.3, 0.3)) * t + rng.uniform(0, 6.28))
            ph = 2 * np.pi * np.cumsum(f * vib) / SR
            for n in range(1, 9):
                out += np.sin(n * ph + rng.uniform(0, 6.28)) / n ** 1.7
    env = np.minimum(1, t / att) * np.minimum(1, (dur - t) / rel).clip(0, 1)
    return out * env / (np.abs(out).max() + 1e-9)


def drone(m, dur):
    t = np.arange(int(dur * SR)) / SR
    y = np.sin(2 * np.pi * hz(m) * t) + 0.35 * np.sin(2 * np.pi * hz(m + 12) * t)
    y *= 0.8 + 0.2 * np.sin(2 * np.pi * 0.11 * t)
    env = np.minimum(1, t / 1.5) * np.minimum(1, (dur - t) / 1.5).clip(0, 1)
    return y * env / 1.35


def hall(n, seed, secs=3.2):
    r = np.random.default_rng(seed)
    t = np.arange(int(secs * SR)) / SR
    ir = r.normal(0, 1, len(t)) * np.exp(-t / 0.75)
    ir = lfilter([0.25], [1, -0.75], ir)
    ir[: int(0.012 * SR)] = 0
    return ir / np.sqrt((ir ** 2).sum())


def nylon_bed(path, total, cuts, end_t, seed=5, music=True):
    rng = np.random.default_rng(seed)
    n = int((total + 3.5) * SR)
    gL, gR = np.zeros(n), np.zeros(n)                  # guitar
    pL, pR = np.zeros(n), np.zeros(n)                  # pad + drone
    bounds = [0.0] + list(cuts) + [total]
    bounds = sorted(set([b for b in bounds if b <= total]))

    def add(L, R, sig, t0, pan=0.0, g=1.0):
        i = int(t0 * SR)
        if i >= n:
            return
        j = min(n, i + len(sig))
        L[i:j] += sig[: j - i] * g * (1 - pan) ** 0.5
        R[i:j] += sig[: j - i] * g * (1 + pan) ** 0.5

    if music:
        for s in range(len(bounds) - 1):
            t0, t1 = bounds[s], bounds[s + 1]
            if t0 >= end_t - 0.05:
                break
            bass, arp, pd = CHORDS[min(s, len(CHORDS) - 2)]
            add(pL, pR, pad(pd, t1 - t0 + 1.6, rng), max(0, t0 - 0.4), 0.0, 0.22)
            add(pL, pR, drone(bass, t1 - t0 + 1.8), max(0, t0 - 0.3), 0.0, 0.10)
            add(gL, gR, pluck(bass, 4.0, 0.55, rng, 0.35, 0.997), t0 + 0.02, -0.1)
            k = 1
            t = t0 + EIGHTH
            while t < min(t1, end_t) - 0.05:
                m = arp[PATTERN[k % len(PATTERN)]]
                vel = 0.32 + 0.1 * rng.random() + (0.06 if k % 4 == 0 else 0)
                add(gL, gR, pluck(m, 2.8, vel, rng, 0.45), t + rng.normal(0, 0.008), 0.25 * np.sin(k * 1.3))
                k += 1
                t += EIGHTH
        # end card: slow ascending gliss, then a soft F add9 strum and a long pad
        bass, arp, pd = CHORDS[-1]
        gl = [53, 57, 60, 65, 67, 69, 72, 77]
        for i, m in enumerate(gl):
            add(gL, gR, pluck(m, 3.5, 0.26 + 0.02 * i, rng, 0.55), end_t + 0.05 + i * 0.075, -0.4 + 0.1 * i)
        st = end_t + 0.05 + len(gl) * 0.075 + 0.35
        for i, m in enumerate([bass] + arp):
            add(gL, gR, pluck(m, 4.5, 0.42 if i == 0 else 0.3, rng, 0.4, 0.998), st + i * 0.035, -0.2 + 0.08 * i)
        add(pL, pR, pad(pd, total - end_t + 2.5, rng, att=1.0, rel=2.0), end_t, 0.0, 0.24)
        add(pL, pR, drone(bass, total - end_t + 2.5), end_t, 0.0, 0.11)
    # room air (always, very low) so the track never sits in digital silence
    air = lfilter([0.02], [1, -0.98], rng.normal(0, 1, n))
    air /= np.abs(air).max() + 1e-9
    L = gL * 1.0 + pL + air * 0.02
    R = gR * 1.0 + pR + air[::-1] * 0.02
    wl = fftconvolve(L, hall(n, 11))[:n]
    wr = fftconvolve(R, hall(n, 12))[:n]
    L, R = L * 0.78 + wl * 0.5, R * 0.78 + wr * 0.5
    b, a = butter(2, 65 / (SR / 2), "high")           # phone speakers: nothing useful below ~65 Hz
    L, R = lfilter(b, a, L), lfilter(b, a, R)
    m = int(total * SR)
    L, R = L[:m], R[:m]
    fade = int(1.4 * SR)
    L[-fade:] *= np.linspace(1, 0, fade) ** 1.5
    R[-fade:] *= np.linspace(1, 0, fade) ** 1.5
    pk = max(np.abs(L).max(), np.abs(R).max()) + 1e-9
    st = (np.stack([L, R], 1) / pk * 0.7 * 32767).astype(np.int16)
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(st.tobytes())
