"""Original bed #24 (not used before): «quyosh» — a mellow, sunny steelpan piece: steel-drum notes (inharmonic modal
partials with a metallic attack), a warm round bass, soft shaker and rim, and a rising pan arpeggio that speeds up
and climbs while the camera pulls back from one window to the whole mosaic; a bright chord bloom when the sun
emblem appears, a shimmer with the light sweep, a bell when the logo turns crisp, and a gentle groove under the end
card. F major, 92 BPM.

steelpan_bed(path, total, marks, seed=24)
marks = dict(zoom0, zoom1, sweep, crisp, end)
"""
import wave

import numpy as np
from scipy.signal import butter, fftconvolve, lfilter, sosfilt

SR = 48000
BPM = 92
BEAT = 60.0 / BPM


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def pan(m, dur=1.6, vel=1.0, rng=None):
    """steel drum: fundamental + octave + twelfth, slightly detuned, metallic attack"""
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = hz(m)
    parts = [(1.0, 1.0, 0.9), (2.0, 0.55, 0.55), (3.01, 0.22, 0.35), (4.02, 0.12, 0.22), (5.4, 0.05, 0.12)]
    x = np.zeros(n)
    for mult, amp, dec in parts:
        x += amp * np.sin(2 * np.pi * f * mult * t + (rng.uniform(0, 6) if rng is not None else 0)) * np.exp(-t / dec)
    x += 0.25 * np.sin(2 * np.pi * f * 2.0 * t) * np.exp(-t / 0.04)                  # stick «ping»
    att = 1 - np.exp(-t / 0.0025)
    am = 1 + 0.06 * np.sin(2 * np.pi * 6.0 * t) * np.minimum(1, t / 0.2)             # pan shimmer
    return x * att * am * vel / 1.8


def bass(m, dur):
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = np.sin(2 * np.pi * hz(m) * t) + 0.25 * np.sin(2 * np.pi * hz(m) * 2 * t)
    return x * (1 - np.exp(-t / 0.01)) * np.exp(-t / 0.9) * np.clip((dur - t) / 0.1, 0, 1)


def shaker(rng, ln=0.08):
    t = np.arange(int(ln * SR)) / SR
    x = sosfilt(butter(2, [5000 / (SR / 2), 11000 / (SR / 2)], "band", output="sos"), rng.normal(0, 1, len(t)))
    return x / (np.abs(x).max() + 1e-9) * np.sin(np.pi * t / ln) ** 2


def rim(rng):
    t = np.arange(int(0.06 * SR)) / SR
    x = np.sin(2 * np.pi * 1750 * t) * np.exp(-t / 0.012) + 0.4 * rng.normal(0, 1, len(t)) * np.exp(-t / 0.004)
    return x


def pad(tones, dur, rng):
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = np.zeros(n)
    for m in tones:
        for det in (-0.08, 0.0, 0.07):
            ph = (hz(m) * (1 + det / 100) * t + rng.uniform(0, 1)) % 1.0
            x += 2 * ph - 1
    x = sosfilt(butter(2, 1200 / (SR / 2), "low", output="sos"), x)
    env = np.minimum(1, t / 0.8) * np.clip((dur - t) / 0.8, 0, 1)
    return x * env / (np.abs(x).max() + 1e-9)


def hall(seed, secs=2.4):
    r = np.random.default_rng(seed)
    t = np.arange(int(secs * SR)) / SR
    ir = r.normal(0, 1, len(t)) * np.exp(-t / 0.65)
    ir = lfilter([0.35], [1, -0.6], ir)
    ir[: int(0.015 * SR)] = 0
    return ir / np.sqrt((ir ** 2).sum())


# F major: F  Dm  Bb  C
CH = [(41, [65, 69, 72, 77]), (38, [62, 65, 69, 74]), (46, [62, 65, 70, 74]), (36, [64, 67, 72, 76])]


def steelpan_bed(path, total, marks, seed=24):
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

    z0, z1, sw, cr, end = (marks[k] for k in ("zoom0", "zoom1", "sweep", "crisp", "end"))
    # intro: a simple pan phrase over the single window
    for k, (b, m) in enumerate([(0, 72), (0.5, 77), (1.0, 81), (1.5, 79), (2.0, 77)]):
        add(pan(m, 1.8, 0.9, rng), 0.15 + b * BEAT, 0.2, 0.35)
    add(pad(CH[0][1], z0 + 1.5, rng), 0.0, 0, 0.08)
    # pull back: arpeggio that accelerates and climbs, bass walks, pad swells
    t = z0
    k = 0
    while t < z1 - 0.1:
        u = (t - z0) / (z1 - z0)
        step = BEAT * (0.5 - 0.3 * u)                          # eighths -> fast
        root, tones = CH[int(u * 8) % 4]
        oct_ = 12 * int(u * 2.2)
        m = tones[k % 4] + oct_
        add(pan(m, 1.0, 0.7 + 0.3 * u, rng), t, -0.4 + 0.8 * ((k % 4) / 3), 0.22 + 0.08 * u)
        if k % 4 == 0:
            add(bass(root, BEAT * 2), t, 0, 0.32)
            add(pad(tones, BEAT * 2.4, rng), t, 0, 0.06 + 0.06 * u)
        if k % 2 == 1:
            add(shaker(rng), t, 0.3, 0.05 + 0.06 * u)
        t += step
        k += 1
    # riser into the reveal
    m_ = int((z1 - z0) * SR)
    tt = np.arange(m_) / SR
    rs = sosfilt(butter(2, [2000 / (SR / 2), 9000 / (SR / 2)], "band", output="sos"), rng.normal(0, 1, m_))
    add(rs / (np.abs(rs).max() + 1e-9) * (tt / tt[-1]) ** 3, z0, 0, 0.04)
    # reveal: chord bloom (F major, wide), the sun melody
    for j, m in enumerate([53, 65, 69, 72, 77, 81, 84]):
        add(pan(m, 3.2, 0.9, rng), z1 + 0.02 * j, -0.5 + j / 6, 0.15)
    add(bass(41, 3.0), z1, 0, 0.3)
    add(pad([65, 69, 72, 76], cr - z1 + 1.0, rng), z1, 0, 0.17)
    add(pad([62, 65, 70, 74], total - cr + 0.5, rng), cr - 0.3, 0, 0.13)
    mel = [(0, 81), (0.5, 79), (1.0, 77), (1.5, 76), (2.0, 77), (3.0, 72), (3.5, 74), (4.0, 76), (5.0, 77)]
    for b, m in mel:
        add(pan(m, 1.6, 0.9, rng), sw + b * BEAT, 0.15, 0.42)
    # sweep shimmer: a quick high run
    for j, m in enumerate([84, 86, 88, 89, 91, 93]):
        add(pan(m, 0.8, 0.6, rng), sw + 0.05 * j, -0.6 + 0.24 * j, 0.09)
    # crisp logo: bell
    t3 = np.arange(int(2.5 * SR)) / SR
    for j, m in enumerate([89, 96]):
        add(np.sin(2 * np.pi * hz(m) * t3) * np.exp(-t3 / 0.9) * (1 - np.exp(-t3 / 0.002)), cr + 0.08 * j, 0, 0.13)
    # end card groove: bass + shaker + rim + gentle pan comping, final F chord
    t = end
    b = 0
    while t < total - 2.2:
        root, tones = CH[(b // 4) % 4]
        if b % 4 == 0:
            add(bass(root, BEAT * 1.8), t, 0, 0.42)
        if b % 2 == 1:
            add(rim(rng), t, 0.2, 0.12)
        add(shaker(rng), t + BEAT / 2, 0.35, 0.09)
        if b % 2 == 0:
            add(pan(tones[(b // 2) % 4], 1.2, 0.7, rng), t + BEAT / 2, -0.3, 0.32)
        if b % 4 == 3:
            add(pan(tones[(b // 4) % 4] + 12, 1.4, 0.7, rng), t + BEAT * 0.75, 0.3, 0.22)
        t += BEAT
        b += 1
    for j, m in enumerate([65, 69, 72, 77]):
        add(pan(m, 3.0, 0.8, rng), total - 2.2 + 0.03 * j, -0.3 + 0.2 * j, 0.22)
    add(bass(41, 2.5), total - 2.2, 0, 0.35)

    wl, wr = fftconvolve(L, hall(241))[:n], fftconvolve(R, hall(242))[:n]
    L, R = L * 0.82 + wl * 0.3, R * 0.82 + wr * 0.3
    b_, a_ = butter(2, 40 / (SR / 2), "high")
    L, R = lfilter(b_, a_, L), lfilter(b_, a_, R)
    m_ = int(total * SR)
    L, R = L[:m_], R[:m_]
    fi = int(0.15 * SR)
    L[:fi] *= np.linspace(0, 1, fi)
    R[:fi] *= np.linspace(0, 1, fi)
    fo = int(1.8 * SR)
    L[-fo:] *= np.linspace(1, 0, fo) ** 1.5
    R[-fo:] *= np.linspace(1, 0, fo) ** 1.5
    pk = max(np.abs(L).max(), np.abs(R).max()) + 1e-9
    st = (np.stack([L, R], 1) / pk * 0.7 * 32767).astype(np.int16)
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(st.tobytes())
