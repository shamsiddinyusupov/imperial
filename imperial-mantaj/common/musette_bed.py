"""Original bed #22 (not used before): «to‘rt fasl» — a musette accordion waltz (3/4, two detuned reeds + a centre
reed, bellows swell), oom-pah-pah bass and chords, a soft string pad, and a seasonal ambience that changes with the
picture: spring birds, summer cicadas, autumn wind with rustling leaves, winter wind and a tiny chime. One season =
two bars. G major -> C -> A minor (autumn) -> E minor (winter) -> back to G at the end.

musette_bed(path, total, bar, real_at, end_at, seed=22)
"""
import wave

import numpy as np
from scipy.signal import butter, fftconvolve, lfilter, sosfilt

SR = 48000


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def reed(m, dur, rng, bright=3200, vel=1.0, musette=True):
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = np.zeros(n)
    dets = (-0.0, 0.0045, -0.0045) if musette else (0.0, 0.0015)
    for k, dt in enumerate(dets):
        f = hz(m) * (1 + dt) * (1 + 0.0012 * np.sin(2 * np.pi * 5.2 * t + k))
        ph = (np.cumsum(f) / SR + rng.uniform(0, 1)) % 1.0
        x += (2 * ph - 1) * (1.0 if k == 0 else 0.8)
    x = sosfilt(butter(2, bright / (SR / 2), "low", output="sos"), x)
    x += 0.5 * sosfilt(butter(2, [700 / (SR / 2), 1600 / (SR / 2)], "band", output="sos"), x)   # reed body formant
    att, rel = 0.035, 0.09
    env = np.minimum(1, t / att) * np.clip((dur - t) / rel, 0, 1)
    env *= 1 + 0.05 * np.sin(2 * np.pi * 4.0 * t)                                         # bellows
    return x * env * vel / (np.abs(x).max() + 1e-9)


def pad(tones, dur, rng, cut=1100):
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = np.zeros(n)
    for m in tones:
        for det in (-0.1, 0.0, 0.09):
            f = hz(m) * (1 + det / 100)
            ph = (np.cumsum(np.full(n, f)) / SR + rng.uniform(0, 1)) % 1.0
            x += 2 * ph - 1
    x = sosfilt(butter(2, cut / (SR / 2), "low", output="sos"), x)
    env = np.minimum(1, t / 0.8) * np.clip((dur - t) / 0.8, 0, 1)
    return x * env / (np.abs(x).max() + 1e-9)


def bird(rng):
    out = []
    for _ in range(int(rng.integers(2, 5))):
        d = rng.uniform(0.05, 0.09)
        t = np.arange(int(d * SR)) / SR
        f0, f1 = rng.uniform(2800, 3600), rng.uniform(3800, 5200)
        f = f0 + (f1 - f0) * (t / d) ** 0.7
        out += [np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * t / d) ** 2,
                np.zeros(int(rng.uniform(0.04, 0.09) * SR))]
    return np.concatenate(out)


def noise_bed(n, rng, lo, hi):
    x = sosfilt(butter(2, [lo / (SR / 2), hi / (SR / 2)], "band", output="sos"), rng.normal(0, 1, n))
    return x / (np.abs(x).max() + 1e-9)


def hall(seed, secs=2.8):
    r = np.random.default_rng(seed)
    t = np.arange(int(secs * SR)) / SR
    ir = r.normal(0, 1, len(t)) * np.exp(-t / 0.75)
    ir = lfilter([0.35], [1, -0.6], ir)
    ir[: int(0.018 * SR)] = 0
    return ir / np.sqrt((ir ** 2).sum())


# bars: (bass root, chord tones, melody notes per bar [(beat, len, midi)])
G, D, Em, C, Am, F, E, B7, Bm = ([43, [59, 62, 67]], [38, [57, 62, 66]], [40, [59, 64, 67]], [36, [60, 64, 67]],
                                 [45, [60, 64, 69]], [41, [60, 65, 69]], [40, [59, 64, 68]], [47, [59, 63, 66]],
                                 [47, [59, 62, 66]])
BARS = [  # spring
    (G, [(0, 1.5, 74), (1.5, 0.5, 76), (2, 1, 79)]), (D, [(0, 1, 78), (1, 1, 76), (2, 1, 74)]),
    # summer
    (C, [(0, 1.5, 76), (1.5, 0.5, 77), (2, 1, 79)]), (G, [(0, 1, 83), (1, 1, 81), (2, 1, 79)]),
    # autumn
    (Am, [(0, 1.5, 76), (1.5, 0.5, 74), (2, 1, 72)]), (E, [(0, 1, 71), (1, 1, 72), (2, 1, 74)]),
    # winter
    (Em, [(0, 2, 71), (2, 1, 67)]), (B7, [(0, 1.5, 66), (1.5, 0.5, 69), (2, 1, 71)]),
    # real shots, then the end: D -> G (held to the end)
    (C, [(0, 1, 72), (1, 1, 76), (2, 1, 79)]), (D, [(0, 1.5, 78), (1.5, 0.5, 76), (2, 1, 74)]),
    (G, [(0, 3, 79)])]


def musette_bed(path, total, bar, real_at, end_at, seed=22):
    rng = np.random.default_rng(seed)
    n = int((total + 3) * SR)
    L, R = np.zeros(n), np.zeros(n)
    beat = bar / 3

    def add(sig, t0, p=0.0, g=1.0):
        i = int(round(t0 * SR))
        if i < 0 or i >= n:
            return
        j = min(n, i + len(sig))
        L[i:j] += sig[: j - i] * g * (1 - p) ** 0.5
        R[i:j] += sig[: j - i] * g * (1 + p) ** 0.5

    for b, ((root, chord), mel) in enumerate(BARS):
        t0 = b * bar
        if t0 > total:
            break
        last = b == len(BARS) - 1
        # left hand: bass on 1, chord on 2 and 3 (held on the last bar)
        add(reed(root, beat * 0.9, rng, 650, 1.0, False), t0, -0.15, 0.19)
        if last:
            add(reed(root, total - t0, rng, 650, 1.0, False), t0, -0.15, 0.17)
            for m in chord:
                add(reed(m, total - t0, rng, 1800, 0.6), t0, 0.1, 0.12)
        else:
            for k in (1, 2):
                for m in chord:
                    add(reed(m, beat * 0.55, rng, 1800, 0.6), t0 + k * beat, 0.1, 0.10)
        add(pad(chord + [root + 12], bar + 0.8, rng), t0 - 0.2, 0, 0.10)
        for bb, ln, m in mel:
            add(reed(m, ln * beat * 1.02, rng, 3200, 1.0), t0 + bb * beat, 0.05, 0.34)
    # end flourish: final G chord on the melody reed
    tf = (len(BARS) - 1) * bar
    for j, m in enumerate([67, 71, 74, 79, 83]):
        add(reed(m, max(0.5, total - tf - 0.8 - 0.25 * j), rng, 3000, 0.7), tf + 0.6 + 0.25 * j, -0.2 + 0.1 * j, 0.09)
    # seasonal ambience (2 bars each)
    s = 2 * bar
    for t0 in [0.5, 1.2, 2.3, 2.9]:
        add(bird(rng), t0, rng.uniform(-0.7, 0.7), 0.045)
    for t0 in [total - 3.0, total - 2.2]:
        add(bird(rng), t0, rng.uniform(-0.7, 0.7), 0.03)
    m = int(s * SR)
    tt = np.arange(m) / SR
    cic = noise_bed(m, rng, 4200, 6200) * (0.5 + 0.5 * np.sin(2 * np.pi * 34 * tt) ** 2) * np.sin(np.pi * tt / s)
    add(cic, s, 0.3, 0.035)
    wind = noise_bed(m, rng, 200, 900) * (0.4 + 0.6 * np.sin(np.pi * tt / s) ** 2)
    rust = noise_bed(m, rng, 2500, 7000) * (rng.random(m) < 0.004).astype(float)
    rust = np.convolve(rust, np.exp(-np.arange(400) / 80.0), "same")
    add(wind, 2 * s, -0.2, 0.05)
    add(rust / (np.abs(rust).max() + 1e-9), 2 * s, 0.3, 0.03)
    add(noise_bed(m, rng, 150, 600) * np.sin(np.pi * tt / s), 3 * s, 0.1, 0.05)
    t3 = np.arange(int(2.2 * SR)) / SR
    for j, mm in enumerate([88, 93, 95]):
        add(np.sin(2 * np.pi * hz(mm) * t3) * np.exp(-t3 / 0.7) * (1 - np.exp(-t3 / 0.003)), 3 * s + 1.2 + 0.09 * j,
            0.4 - 0.3 * j, 0.03)

    wl, wr = fftconvolve(L, hall(221))[:n], fftconvolve(R, hall(222))[:n]
    L, R = L * 0.8 + wl * 0.32, R * 0.8 + wr * 0.32
    b_, a_ = butter(2, 35 / (SR / 2), "high")
    L, R = lfilter(b_, a_, L), lfilter(b_, a_, R)
    mm_ = int(total * SR)
    L, R = L[:mm_], R[:mm_]
    fi = int(0.25 * SR)
    L[:fi] *= np.linspace(0, 1, fi)
    R[:fi] *= np.linspace(0, 1, fi)
    fo = int(2.2 * SR)
    L[-fo:] *= np.linspace(1, 0, fo) ** 1.5
    R[-fo:] *= np.linspace(1, 0, fo) ** 1.5
    pk = max(np.abs(L).max(), np.abs(R).max()) + 1e-9
    st = (np.stack([L, R], 1) / pk * 0.7 * 32767).astype(np.int16)
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(st.tobytes())


if __name__ == "__main__":
    import time
    t0 = time.time()
    musette_bed("/tmp/claude-0/-home-claude/29c18e40-edfd-55e7-a3e1-da5539b3418b/scratchpad/musette_test.wav", 23.0,
                1.7, 13.2, 16.23)
    print("ok", round(time.time() - t0, 1))
