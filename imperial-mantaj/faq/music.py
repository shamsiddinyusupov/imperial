"""Soft background bed for the plisse FAQ reel (original, synthesized here — no licensing issues).

84 BPM, D major: Dmaj9 – Bm9 – Gmaj7 – A6sus, felt-piano arpeggios over a warm pad, sub bass,
quiet kick + shaker from bar 3. Writes music.wav (48 kHz stereo) of the requested length.
Usage: python3 music.py SECONDS
"""
import sys
import wave

import numpy as np

SR = 48000
BPM = 84
BEAT = 60 / BPM
BAR = 4 * BEAT
LEN = float(sys.argv[1]) if len(sys.argv) > 1 else 70.0
N = int(SR * (LEN + 3))
rng = np.random.default_rng(7)


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


# midi notes: (bass root, pad chord, arpeggio notes)
CHORDS = [
    (38, [62, 66, 69, 73, 76], [74, 78, 81, 85, 88, 81, 78, 76]),   # Dmaj9
    (35, [59, 62, 66, 69, 73], [71, 74, 78, 81, 85, 78, 74, 73]),   # Bm9
    (31, [55, 59, 62, 66, 69], [67, 71, 74, 78, 79, 78, 74, 71]),   # Gmaj7
    (33, [57, 62, 64, 66, 69], [69, 74, 76, 78, 81, 78, 76, 74]),   # A6sus
]

L = np.zeros(N)
R = np.zeros(N)


def add(buf, sig, t0):
    i = int(t0 * SR)
    if i >= N:
        return
    j = min(N, i + len(sig))
    buf[i:j] += sig[: j - i]


def env(n, a, d, sustain_tail=True):
    t = np.arange(n) / SR
    e = np.minimum(1, t / a) * np.exp(-t / d)
    if sustain_tail:
        e *= np.minimum(1, (n - np.arange(n)) / (0.05 * SR))
    return e


def piano(f, dur, vel):
    n = int(dur * SR)
    t = np.arange(n) / SR
    s = (np.sin(2 * np.pi * f * t) + 0.35 * np.sin(2 * np.pi * 2 * f * t) * np.exp(-t / 0.4)
         + 0.12 * np.sin(2 * np.pi * 3 * f * t) * np.exp(-t / 0.2))
    return vel * s * env(n, 0.006, 0.9)


def pad(freqs, dur):
    n = int(dur * SR)
    t = np.arange(n) / SR
    s = np.zeros(n)
    for f in freqs:
        for det in (-0.12, 0.12):
            ff = f * 2 ** (det / 12)
            s += np.sin(2 * np.pi * ff * t) + 0.25 * np.sin(2 * np.pi * 2 * ff * t)
    e = np.minimum(1, t / 0.9) * np.minimum(1, (dur - t) / 0.9)
    lfo = 0.85 + 0.15 * np.sin(2 * np.pi * 0.21 * t)
    return s * e * lfo / len(freqs)


def bass(f, dur):
    n = int(dur * SR)
    t = np.arange(n) / SR
    s = np.sin(2 * np.pi * f * t) + 0.2 * np.sin(2 * np.pi * 2 * f * t)
    return s * np.minimum(1, t / 0.03) * np.minimum(1, (dur - t) / 0.15) * (0.7 + 0.3 * np.exp(-t / 0.5))


def kick():
    n = int(0.35 * SR)
    t = np.arange(n) / SR
    f = 48 + 70 * np.exp(-t / 0.03)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.12)


def shaker():
    n = int(0.09 * SR)
    x = rng.normal(0, 1, n)
    x = x - np.convolve(x, np.ones(6) / 6, "same")          # crude high-pass
    return x * np.exp(-np.arange(n) / SR / 0.025)


bars = int(np.ceil(LEN / BAR)) + 1
for b in range(bars):
    t0 = b * BAR
    root, chord, arp = CHORDS[b % 4]
    p = pad([hz(m) for m in chord], BAR + 0.6)
    add(L, 0.16 * p, t0)
    add(R, 0.16 * p, t0)
    bs = bass(hz(root), BAR * 0.98)
    add(L, 0.22 * bs, t0)
    add(R, 0.22 * bs, t0)
    for k, m in enumerate(arp):                                 # eighth-note arpeggio, gently humanized
        tt = t0 + k * BEAT / 2 + rng.uniform(-0.008, 0.008)
        v = 0.11 * (1.0 if k % 2 == 0 else 0.75) * rng.uniform(0.85, 1.0)
        pn = piano(hz(m), 1.6, v)
        pan = 0.5 + 0.35 * np.sin(k * 0.9 + b)
        add(L, pn * (1 - pan) * 1.2, tt)
        add(R, pn * pan * 1.2, tt)
    if b >= 2:
        for k in range(4):
            if k in (0, 2):
                add(L, 0.20 * kick(), t0 + k * BEAT)
                add(R, 0.20 * kick(), t0 + k * BEAT)
        for k in range(8):
            if k % 2 == 1:
                sh = 0.018 * shaker()
                add(L, sh * 0.8, t0 + k * BEAT / 2 + 0.01)
                add(R, sh * 1.2, t0 + k * BEAT / 2)


def reverb(x, seed, secs=2.2):
    n = int(secs * SR)
    ir = np.random.default_rng(seed).normal(0, 1, n) * np.exp(-np.arange(n) / SR / 0.55)
    ir = np.convolve(ir, np.ones(30) / 30, "same")              # darker tail
    ir /= np.sqrt(np.sum(ir ** 2))
    m = len(x) + n - 1
    size = 1 << (m - 1).bit_length()
    y = np.fft.irfft(np.fft.rfft(x, size) * np.fft.rfft(ir, size), size)[: len(x)]
    return y


wl, wr = reverb(L, 1), reverb(R, 2)
L = 0.78 * L + 0.32 * wl
R = 0.78 * R + 0.32 * wr

# gentle low-pass (one-pole) for warmth
a = np.exp(-2 * np.pi * 7000 / SR)
for buf in (L, R):
    y = 0.0
    out = np.empty_like(buf)
    # vectorised one-pole via lfilter-like recursion in chunks
    from itertools import accumulate  # noqa: E402  (kept local, simple)
    out[:] = list(accumulate(buf * (1 - a), lambda p, v: a * p + v))
    buf[:] = out

n_out = int(LEN * SR)
L, R = L[:n_out], R[:n_out]
fade_in = np.minimum(1, np.arange(n_out) / (1.2 * SR))
fade_out = np.minimum(1, (n_out - np.arange(n_out)) / (2.5 * SR))
L *= fade_in * fade_out
R *= fade_in * fade_out
peak = max(np.abs(L).max(), np.abs(R).max())
L, R = L / peak * 0.89, R / peak * 0.89
pcm = (np.stack([L, R], 1) * 32767).astype(np.int16)
with wave.open("/home/claude/reels/faq/music.wav", "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(pcm.tobytes())
print("music.wav", LEN, "s")
