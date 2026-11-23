"""Original bed #27 (not used before): «nay» — the Uzbek end-blown flute: a breathy sine-based tone with chiff, slow
vibrato and portamento between notes, over a bowed low string drone and a soft doira (frame drum: low «dum», rim
«tak», a whisper of jingles). Sparse and warm so it sits under a voice. D minor in the hook, F major after the
reveal, a hushed pedal for the «old curtain» moment, the groove back for the end, a Bb-C-F cadence on the end card.
80 BPM.

nay_bed(path, total, marks, seed=27)
marks = dict(reveal, call, slat, go, end)
"""
import wave

import numpy as np
from scipy.signal import butter, fftconvolve, lfilter, sosfilt

SR = 48000
BPM = 80
BEAT = 60.0 / BPM
BAR = 4 * BEAT


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def nay_phrase(notes, rng, vib=5.2):
    """notes: list of (midi, dur). One breath: legato with short portamento, chiff at the start."""
    total = sum(d for _, d in notes)
    n = int((total + 0.6) * SR)
    t = np.arange(n) / SR
    f = np.zeros(n)
    acc = 0.0
    prev = None
    for m, d in notes:
        i0, i1 = int(acc * SR), int((acc + d) * SR)
        f[i0:i1] = hz(m)
        if prev is not None:
            g = min(int(0.07 * SR), i1 - i0)
            f[i0:i0 + g] = np.linspace(hz(prev), hz(m), g)
        prev = m
        acc += d
    f[int(acc * SR):] = hz(prev)
    depth = 0.006 * np.clip((t - 0.25) / 0.6, 0, 1)
    f = f * (1 + depth * np.sin(2 * np.pi * vib * t + rng.uniform(0, 6)))
    ph = 2 * np.pi * np.cumsum(f) / SR
    tone = np.sin(ph) + 0.22 * np.sin(2 * ph + 0.3) + 0.07 * np.sin(3 * ph + 1.1)
    breath = sosfilt(butter(2, [900 / (SR / 2), 4200 / (SR / 2)], "band", output="sos"), rng.normal(0, 1, n))
    breath = breath / (np.abs(breath).max() + 1e-9)
    env = np.minimum(1, t / 0.09) * np.clip((total + 0.25 - t) / 0.35, 0, 1)
    swell = 0.85 + 0.15 * np.sin(np.pi * np.clip(t / max(total, 0.1), 0, 1))
    chiff = np.exp(-t / 0.05) * 0.5
    y = env * swell * (tone * 0.8 + breath * (0.22 + chiff))
    return y / (np.abs(y).max() + 1e-9)


def bow(m, dur, rng, cut=900):
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = np.zeros(n)
    for d in (-0.06, 0.0, 0.05):
        fr = hz(m) * (1 + d / 100) * (1 + 0.002 * np.sin(2 * np.pi * 4.6 * t + rng.uniform(0, 6)))
        ph = np.cumsum(fr) / SR + rng.uniform(0, 1)
        x += 2 * (ph % 1.0) - 1
    x = sosfilt(butter(2, cut / (SR / 2), "low", output="sos"), x)
    env = np.minimum(1, t / 0.8) * np.clip((dur - t) / 0.9, 0, 1)
    return x * env / (np.abs(x).max() + 1e-9)


def pad(tones, dur, rng, cut=1100):
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = np.zeros(n)
    for m in tones:
        for d in (-0.07, 0.0, 0.08):
            x += np.sin(2 * np.pi * hz(m) * (1 + d / 100) * t + rng.uniform(0, 6))
            x += 0.3 * np.sin(4 * np.pi * hz(m) * (1 + d / 100) * t + rng.uniform(0, 6))
    x = sosfilt(butter(2, cut / (SR / 2), "low", output="sos"), x)
    env = np.minimum(1, t / 1.2) * np.clip((dur - t) / 1.2, 0, 1)
    return x * env / (np.abs(x).max() + 1e-9)


def dum(rng):
    t = np.arange(int(0.45 * SR)) / SR
    f = 82 + 40 * np.exp(-t / 0.025)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.22)
    skin = sosfilt(butter(2, [200 / (SR / 2), 900 / (SR / 2)], "band", output="sos"), rng.normal(0, 1, len(t)))
    skin = skin / (np.abs(skin).max() + 1e-9) * np.exp(-t / 0.02) * 0.25
    return body + skin


def tak(rng, g=1.0):
    t = np.arange(int(0.18 * SR)) / SR
    x = sosfilt(butter(2, [1800 / (SR / 2), 5200 / (SR / 2)], "band", output="sos"), rng.normal(0, 1, len(t)))
    x = x / (np.abs(x).max() + 1e-9) * np.exp(-t / 0.018)
    j = sosfilt(butter(2, 6500 / (SR / 2), "high", output="sos"), rng.normal(0, 1, len(t)))
    j = j / (np.abs(j).max() + 1e-9) * np.exp(-t / 0.06) * 0.25
    return (x + j) * g


def hall(seed, secs=3.2):
    r = np.random.default_rng(seed)
    t = np.arange(int(secs * SR)) / SR
    ir = r.normal(0, 1, len(t)) * np.exp(-t / 1.0)
    ir = lfilter([0.35], [1, -0.62], ir)
    ir[: int(0.025 * SR)] = 0
    return ir / np.sqrt((ir ** 2).sum())


F_PROG = [(41, [65, 69, 72, 77]), (36, [64, 67, 72, 76]), (38, [62, 65, 69, 74]), (34, [62, 65, 70, 74])]  # F C Dm Bb
# nay lines (midi, beats) over F C Dm Bb, F major pentatonic-ish, ornamented
NAY_A = [(72, 1.5), (74, 0.5), (77, 2.0)]
NAY_B = [(79, 1.0), (77, 0.5), (76, 0.5), (74, 2.0)]
NAY_C = [(74, 1.0), (72, 1.0), (69, 2.0)]
NAY_D = [(70, 1.0), (72, 1.0), (74, 1.5), (72, 0.5)]


def beats(line):
    return [(m, b * BEAT) for m, b in line]


def nay_bed(path, total, marks, seed=27):
    rng = np.random.default_rng(seed)
    n = int((total + 3.5) * SR)
    L, R = np.zeros(n), np.zeros(n)

    def add(sig, t0, p=0.0, g=1.0):
        i = int(round(t0 * SR))
        if i < 0 or i >= n:
            return
        j = min(n, i + len(sig))
        L[i:j] += sig[: j - i] * g * (1 - p) ** 0.5
        R[i:j] += sig[: j - i] * g * (1 + p) ** 0.5

    rv, call, slat, go, end = (marks[k] for k in ("reveal", "call", "slat", "go", "end"))

    # hook (D minor): drone + one breathy question phrase
    add(bow(38, rv + 0.8, rng), 0.0, -0.1, 0.30)
    add(bow(45, rv + 0.8, rng, 700), 0.0, 0.15, 0.16)
    add(nay_phrase(beats([(69, 0.75), (70, 0.5), (69, 0.75), (65, 1.5)]), rng), 0.15, 0.2, 0.22)
    add(tak(rng, 0.25), rv - 0.45, 0.25, 0.25)
    add(tak(rng, 0.3), rv - 0.22, -0.25, 0.25)

    def groove(t0, t1, lines, start_bar=0, drums=True, nay_gain=0.17):
        t, b = t0, start_bar
        while t < t1 - 0.2:
            root, tones = F_PROG[b % 4]
            ln = min(BAR + 1.2, t1 - t + 1.0)
            add(bow(root, ln, rng), t, -0.15, 0.24)
            add(pad(tones, ln, rng), t, 0.1, 0.09)
            if drums:
                for k, (kind, g) in enumerate([("d", 1), (None, 0), ("t", .55), ("t", .4), ("d", .8), ("t", .5),
                                               (None, 0), ("t", .45)]):
                    tt = t + k * BEAT / 2
                    if kind and tt < t1 - 0.05:
                        add(dum(rng) if kind == "d" else tak(rng, g), tt, 0.12 if kind == "t" else 0, 0.26 * g
                            if kind == "d" else 0.13)
            if lines and b % 2 == 0:
                ph = nay_phrase(beats(lines[(b // 2) % len(lines)]), rng)
                if t + len(ph) / SR < t1 + 0.6:
                    add(ph, t + BEAT * 0.5, 0.2, nay_gain)
            t += BAR
            b += 1
        return b

    # reveal: F major opens, swelling chord on the reveal
    add(pad([65, 69, 72, 77, 81], 2.4, rng, 2000), rv - 0.1, 0, 0.13)
    groove(rv, call, [NAY_A, NAY_B])
    # «old curtain»: hushed D pedal, low nay sigh
    add(bow(38, slat - call + 1.0, rng, 600), call, -0.1, 0.28)
    add(pad([62, 69, 74], slat - call + 1.0, rng, 800), call, 0.1, 0.08)
    add(nay_phrase(beats([(69, 1.0), (67, 0.5), (65, 2.5)]), rng), call + 0.5, 0.25, 0.15)
    # one slat: light pulse returns (Bb F), then the full groove
    b = groove(slat, go, [NAY_D], start_bar=3, drums=False, nay_gain=0.14)
    for k in range(int((go - slat) / BEAT)):
        add(tak(rng, 0.35), slat + k * BEAT + BEAT / 2, 0.2, 0.1)
    groove(go, end, [NAY_C, NAY_A], start_bar=0)
    # end card: Bb -> C -> F, nay closes
    seq = [(34, [62, 65, 70, 74]), (36, [64, 67, 72, 76])]
    for k, (root, tones) in enumerate(seq):
        add(bow(root, BAR / 2 + 1.0, rng), end + k * BAR / 2, -0.15, 0.24)
        add(pad(tones, BAR / 2 + 1.0, rng), end + k * BAR / 2, 0.1, 0.09)
        add(dum(rng), end + k * BAR / 2, 0, 0.22)
    tf = end + BAR
    add(bow(41, total - tf + 1.0, rng), tf, -0.15, 0.26)
    add(pad([65, 69, 72, 77], total - tf + 1.0, rng, 1600), tf, 0.1, 0.11)
    add(dum(rng), tf, 0, 0.24)
    add(nay_phrase(beats([(72, 1.0), (74, 0.5), (72, 0.5), (69, 1.0), (72, 1.0), (77, 3.0)]), rng), tf + 0.3, 0.2, 0.17)

    wl, wr = fftconvolve(L, hall(271))[:n], fftconvolve(R, hall(272))[:n]
    L, R = L * 0.8 + wl * 0.36, R * 0.8 + wr * 0.36
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
