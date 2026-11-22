"""Original bed #25 (not used before): «chang» — the Uzbek hammered dulcimer: struck metal strings (two detuned
Karplus-Strong courses with a hard hammer attack and a bright soundboard), soft tremolo rolls, a low drone string,
a warm pad and a gentle frame-drum pulse. Quiet enough to sit under a voice: sparse arpeggios, a glittering
tremolo swell into the «too much sun» moment, warm major chords after it, a calm cadence on the end card.
E minor -> G major, 84 BPM.

chang_bed(path, total, marks, seed=25)
marks = dict(sun, dress, choose, end)
"""
import wave

import numpy as np
from scipy.signal import butter, fftconvolve, lfilter, sosfilt

SR = 48000
BPM = 84
BEAT = 60.0 / BPM


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def ks(m, dur, rng, bright=0.75, decay=0.9985, det=0.0):
    n = int(dur * SR)
    N = max(2, int(round(SR / (hz(m) * (1 + det)))))
    x = np.zeros(n)
    x[:N] = lfilter([bright, 1 - bright], [1], rng.uniform(-1, 1, N))
    a = np.zeros(N + 2)
    a[0] = 1
    a[N] = -decay * 0.5
    a[N + 1] = -decay * 0.5
    return lfilter([1], a, x)


_BOARD = [butter(2, [b / (SR / 2), c / (SR / 2)], "band", output="sos") for b, c in ((380, 620), (1800, 3200))]


def chang(m, dur=2.2, vel=1.0, rng=None):
    y = ks(m, dur, rng, 0.8, 0.9988) + 0.8 * ks(m, dur, rng, 0.8, 0.9988, det=0.0025)
    y = 0.7 * y + 0.6 * sosfilt(_BOARD[0], y) + 0.35 * sosfilt(_BOARD[1], y)
    t = np.arange(len(y)) / SR
    hammer = rng.normal(0, 1, len(y)) * np.exp(-t / 0.003) * 0.4
    y = (y + hammer) * np.minimum(1, t / 0.001)
    return y * vel / (np.abs(y).max() + 1e-9)


def tremolo(m, dur, rng, rate=11.0, vel=0.6):
    out = np.zeros(int((dur + 2.0) * SR))
    k = 0
    while k / rate < dur:
        s = chang(m, 1.2, vel * (0.75 + 0.25 * np.sin(k)), rng)
        i = int(k / rate * SR)
        out[i:i + len(s)] += s[: len(out) - i] * (0.5 + 0.5 * min(1, k / (rate * dur) * 2))
        k += 1
    return out


def drum(rng, low=True):
    t = np.arange(int(0.35 * SR)) / SR
    if low:
        f = 70 + 25 * np.exp(-t / 0.03)
        return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.18)
    x = sosfilt(butter(2, [1500 / (SR / 2), 5000 / (SR / 2)], "band", output="sos"), rng.normal(0, 1, len(t)))
    return x / (np.abs(x).max() + 1e-9) * np.exp(-t / 0.03) * 0.7


def pad(tones, dur, rng, cut=1000):
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = np.zeros(n)
    for m in tones:
        for d in (-0.08, 0.0, 0.07):
            ph = (hz(m) * (1 + d / 100) * t + rng.uniform(0, 1)) % 1.0
            x += 2 * ph - 1
    x = sosfilt(butter(2, cut / (SR / 2), "low", output="sos"), x)
    env = np.minimum(1, t / 1.0) * np.clip((dur - t) / 1.0, 0, 1)
    return x * env / (np.abs(x).max() + 1e-9)


def hall(seed, secs=3.0):
    r = np.random.default_rng(seed)
    t = np.arange(int(secs * SR)) / SR
    ir = r.normal(0, 1, len(t)) * np.exp(-t / 0.9)
    ir = lfilter([0.35], [1, -0.6], ir)
    ir[: int(0.02 * SR)] = 0
    return ir / np.sqrt((ir ** 2).sum())


EM = [(40, [64, 67, 71, 76]), (36, [64, 67, 72, 76]), (43, [62, 67, 71, 74]), (38, [62, 66, 69, 74])]   # Em C G D
GM = [(43, [67, 71, 74, 79]), (40, [67, 71, 76, 79]), (36, [67, 72, 76, 79]), (38, [66, 69, 74, 78])]   # G Em C D


def chang_bed(path, total, marks, seed=25):
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

    sun, dress, choose, end = (marks[k] for k in ("sun", "dress", "choose", "end"))
    bar = 4 * BEAT
    pat = [0, 2, 1, 3, 2, 1]
    # part 1 (E minor): sparse arpeggios until the sun moment
    t, b = 0.1, 0
    while t < sun - 0.2:
        root, tones = EM[b % 4]
        add(chang(root, 3.0, 0.6, rng), t, -0.3, 0.30)
        add(pad(tones, bar + 1.0, rng), t, 0, 0.07)
        for k, j in enumerate(pat):
            tt = t + k * bar / 6
            if tt < sun - 0.2:
                add(chang(tones[j], 1.8, 0.6, rng), tt, -0.3 + 0.12 * k, 0.22)
        if b >= 1:
            add(drum(rng), t, 0, 0.18)
            add(drum(rng, False), t + 2 * BEAT, 0.2, 0.05)
        t += bar
        b += 1
    # the sun: glittering tremolo swell
    add(tremolo(83, dress - sun, rng, 13, 0.55), sun, 0.35, 0.16)
    add(tremolo(88, dress - sun, rng, 15, 0.45), sun + 0.3, -0.35, 0.12)
    add(pad([64, 71, 76, 83], dress - sun + 0.6, rng, 2200), sun, 0, 0.09)
    # dressed: warm G major from here
    t, b = dress, 0
    while t < end - 0.1:
        root, tones = GM[b % 4]
        add(chang(root, 3.0, 0.6, rng), t, -0.3, 0.32)
        add(pad(tones, bar + 1.0, rng), t, 0, 0.08)
        for k, j in enumerate(pat):
            tt = t + k * bar / 6
            if tt < end - 0.1:
                add(chang(tones[j] + (12 if (t >= choose and k % 3 == 0) else 0), 1.8, 0.6, rng), tt,
                    0.3 - 0.12 * k, 0.22)
        add(drum(rng), t, 0, 0.2)
        add(drum(rng, False), t + 2 * BEAT, 0.2, 0.06)
        t += bar
        b += 1
    # end card: cadence D -> G and a slow roll
    add(pad([62, 66, 69, 74], 2.2, rng), end, 0, 0.09)
    add(chang(38, 3.0, 0.7, rng), end, -0.2, 0.3)
    for k, m in enumerate([62, 66, 69, 74, 78]):
        add(chang(m, 2.0, 0.6, rng), end + k * BEAT / 2, -0.3 + 0.15 * k, 0.22)
    tg = end + 2.0
    add(pad([67, 71, 74, 79], total - tg + 0.5, rng), tg, 0, 0.1)
    add(chang(43, 4.0, 0.7, rng), tg, -0.2, 0.34)
    add(tremolo(79, 1.6, rng, 11, 0.5), tg + 0.2, 0.2, 0.14)
    for k, m in enumerate([67, 71, 74, 79, 83]):
        add(chang(m, 3.0, 0.6, rng), tg + 1.2 + k * BEAT / 3, -0.3 + 0.15 * k, 0.2)

    wl, wr = fftconvolve(L, hall(251))[:n], fftconvolve(R, hall(252))[:n]
    L, R = L * 0.8 + wl * 0.34, R * 0.8 + wr * 0.34
    b_, a_ = butter(2, 45 / (SR / 2), "high")
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
