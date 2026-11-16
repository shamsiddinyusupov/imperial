"""Original bed #21 (not used before): «quyosh» — a plucked two-string dutar (Karplus-Strong with a drone string and a
small wooden body), a soft doira (frame drum: dum, tak and ring jingles), a warm string pad, and a few far-away
morning birds. Follows a day: rubato dawn, a dutar phrase at sunrise, a rising run for the morning->noon timelapse,
a bright noon groove, a falling run to sunset, a calm closing, a lamp chime, then the groove under the real shots and
a D major ending. D Dorian.

dutar_bed(path, total, marks, seed=21)
marks = dict(rise, tl1, noon, tl2, close, lamp, real, end)  (seconds)
"""
import wave

import numpy as np
from scipy.signal import butter, fftconvolve, lfilter, sosfilt

SR = 48000
BPM = 96
BEAT = 60.0 / BPM


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def ks(m, dur, rng, bright=0.6, decay=0.996):
    """Karplus-Strong pluck via lfilter (integer delay)"""
    n = int(dur * SR)
    N = max(2, int(round(SR / hz(m))))
    x = np.zeros(n)
    burst = rng.uniform(-1, 1, N)
    burst = lfilter([bright, 1 - bright], [1], burst)                 # pick brightness
    x[:N] = burst
    a = np.zeros(N + 2)
    a[0] = 1
    a[N] = -decay * 0.5
    a[N + 1] = -decay * 0.5
    y = lfilter([1], a, x)
    return y / (np.abs(y).max() + 1e-9)


def body(y):
    """small wooden body: two resonances + a touch of the raw string"""
    b1 = sosfilt(butter(2, [200 / (SR / 2), 320 / (SR / 2)], "band", output="sos"), y)
    b2 = sosfilt(butter(2, [900 / (SR / 2), 1500 / (SR / 2)], "band", output="sos"), y)
    return 0.65 * y + 1.6 * b1 + 0.8 * b2


def dutar(m, dur, rng, vel=1.0, grace=None):
    y = ks(m, dur, rng, bright=0.55 + 0.2 * rng.random(), decay=0.9965)
    if grace is not None:                       # quick hammer-on: grace note, then the main note 55 ms later
        g = ks(grace, 0.08, rng, 0.6, 0.99) * np.linspace(1, 0, int(0.08 * SR))
        off = int(0.055 * SR)
        out = np.zeros(len(y) + off)
        out[:len(g)] += g * 0.7
        out[off:] += y
        y = out
    env = np.minimum(1, np.arange(len(y)) / (0.002 * SR))
    return body(y * env) * vel


def dum(rng):
    t = np.arange(int(0.45 * SR)) / SR
    f = 58 + 30 * np.exp(-t / 0.03)
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.20)
    n = sosfilt(butter(2, 400 / (SR / 2), "low", output="sos"), rng.normal(0, 1, len(t))) * np.exp(-t / 0.015)
    return s + 0.4 * n / (np.abs(n).max() + 1e-9)


def tak(rng):
    t = np.arange(int(0.12 * SR)) / SR
    n = sosfilt(butter(2, [1800 / (SR / 2), 4200 / (SR / 2)], "band", output="sos"), rng.normal(0, 1, len(t)))
    ring = np.sin(2 * np.pi * 860 * t) * np.exp(-t / 0.035)
    return (n / (np.abs(n).max() + 1e-9)) * np.exp(-t / 0.022) * 0.8 + 0.35 * ring


def zang(rng):
    t = np.arange(int(0.22 * SR)) / SR
    n = sosfilt(butter(2, 6000 / (SR / 2), "high", output="sos"), rng.normal(0, 1, len(t)))
    am = 0.6 + 0.4 * np.sin(2 * np.pi * 38 * t)
    return n / (np.abs(n).max() + 1e-9) * np.exp(-t / 0.06) * am * 0.5


def bird(rng):
    out = []
    for _ in range(int(rng.integers(2, 5))):
        d = rng.uniform(0.05, 0.09)
        t = np.arange(int(d * SR)) / SR
        f0, f1 = rng.uniform(2800, 3600), rng.uniform(3800, 5200)
        f = f0 + (f1 - f0) * (t / d) ** 0.7
        s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * t / d) ** 2
        out += [s, np.zeros(int(rng.uniform(0.04, 0.09) * SR))]
    return np.concatenate(out)


def pad(tones, dur, rng, cut=1300):
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = np.zeros(n)
    for m in tones:
        for det in (-0.10, 0.0, 0.09):
            f = hz(m) * (1 + det / 100) * (1 + 0.002 * np.sin(2 * np.pi * 0.25 * t + rng.uniform(0, 6)))
            ph = (np.cumsum(f) / SR + rng.uniform(0, 1)) % 1.0
            x += 2 * ph - 1
    x = sosfilt(butter(2, cut / (SR / 2), "low", output="sos"), x)
    env = np.minimum(1, t / 0.9) * np.clip((dur - t) / 0.9, 0, 1)
    return x * env / (np.abs(x).max() + 1e-9)


def hall(seed, secs=3.2):
    r = np.random.default_rng(seed)
    t = np.arange(int(secs * SR)) / SR
    ir = r.normal(0, 1, len(t)) * np.exp(-t / 0.9)
    ir = lfilter([0.35], [1, -0.65], ir)
    ir[: int(0.02 * SR)] = 0
    return ir / np.sqrt((ir ** 2).sum())


# chords (pad tones) and dutar scale degrees, D Dorian
CH = {"Dm": [50, 57, 60, 64, 65], "C": [48, 55, 60, 64, 67], "Bb": [46, 53, 58, 62, 65], "F": [41, 53, 57, 60, 64],
      "Gm": [43, 55, 58, 62, 65], "A": [45, 57, 61, 64, 69], "D": [50, 57, 62, 66, 69]}
SCALE = [62, 64, 65, 67, 69, 71, 72, 74, 76, 77, 79]      # D4 .. G5 (D Dorian)


def dutar_bed(path, total, marks, seed=21):
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

    m = marks
    # pads per section
    secs = [(0.0, m["rise"], "Dm", 900), (m["rise"], m["rise"] + 1.85, "Dm", 1300), (m["rise"] + 1.85, m["tl1"], "C", 1400),
            (m["tl1"], m["noon"], "Bb", 1700), (m["noon"], m["tl2"], "F", 2000), (m["tl2"], m["tl2"] + 0.9, "Gm", 1500),
            (m["tl2"] + 0.9, m["close"], "A", 1300), (m["close"], m["real"], "Dm", 1000),
            (m["real"], m["real"] + 2.0, "Bb", 1400), (m["real"] + 2.0, m["end"], "C", 1500), (m["end"], total, "D", 1500)]
    for a, b, c, cut in secs:
        add(pad(CH[c], b - a + 1.0, rng, cut), a - 0.3, 0, 0.16)
        add(pad([CH[c][0] - 12], b - a + 1.0, rng, 300), a - 0.3, 0, 0.18)
    # drone string (D3/A3), very soft, through the whole piece
    for k, t0 in enumerate(np.arange(0.2, total - 1, BEAT * 4)):
        add(dutar(50, 3.0, rng, 0.25), t0, -0.2, 0.25 if t0 < m["real"] else 0.18)
        add(dutar(57, 3.0, rng, 0.18), t0 + BEAT * 2, 0.2, 0.2)
    # dawn: sparse rubato notes
    for t0, mm in [(0.6, 69), (1.5, 67), (2.1, 65), (2.6, 62)]:
        add(dutar(mm, 2.5, rng, 0.7, grace=mm - 2 if mm != 62 else None), t0, 0.25, 0.55)
    # birds (far, soft) at sunrise and in the morning
    for t0 in [m["rise"] + 0.4, m["rise"] + 1.6, m["rise"] + 2.4, m["rise"] + 3.3]:
        add(bird(rng), t0, rng.uniform(-0.7, 0.7), 0.05)
    # sunrise phrase (eighths), then the morning groove
    motif = [(0, 4), (0.5, 3), (1.0, 2), (1.5, 3), (2.0, 4), (2.5, 6), (3.0, 4), (3.5, 3)]
    def phrase(t0, shift, vel=0.8, bars=1):
        for b in range(bars):
            for beat, deg in motif:
                d = deg + shift + (1 if b % 2 else 0) * (deg in (2, 4))
                mm = SCALE[int(np.clip(d, 0, len(SCALE) - 1))]
                g = mm - 2 if (beat in (0, 2.0) and rng.random() < 0.5) else None
                add(dutar(mm, 1.6, rng, vel), t0 + (b * 4 + beat) * BEAT, 0.15, 0.5 if g is None else 0.5)
    phrase(m["rise"] + 0.3, 0, 0.8, 1)
    phrase(m["rise"] + 0.3 + 4 * BEAT, 1, 0.8, 1)
    # timelapse 1: fast rising run
    run_n = int((m["noon"] - m["tl1"]) / (BEAT / 4))
    for k in range(run_n):
        mm = SCALE[min(len(SCALE) - 1, k * len(SCALE) // max(1, run_n))]
        add(dutar(mm, 0.9, rng, 0.55 + 0.4 * k / run_n), m["tl1"] + k * BEAT / 4, -0.3 + 0.6 * k / run_n, 0.45)
    # noon: bright phrase
    phrase(m["noon"] + 0.05, 2, 0.9, 1)
    # timelapse 2: falling run
    run_n = int((m["close"] - m["tl2"]) / (BEAT / 4))
    for k in range(run_n):
        mm = SCALE[max(0, len(SCALE) - 1 - k * len(SCALE) // max(1, run_n))]
        add(dutar(mm, 0.9, rng, 0.85 - 0.4 * k / run_n), m["tl2"] + k * BEAT / 4, 0.3 - 0.6 * k / run_n, 0.42)
    # closing: two slow notes, the lamp chime
    add(dutar(65, 2.8, rng, 0.7, grace=64), m["close"] + 0.2, 0.2, 0.5)
    add(dutar(62, 3.2, rng, 0.7), m["close"] + 1.0, -0.1, 0.5)
    t = np.arange(int(2.5 * SR)) / SR
    for j, mm in enumerate([81, 86, 90]):
        add(np.sin(2 * np.pi * hz(mm) * t) * np.exp(-t / 0.8) * (1 - np.exp(-t / 0.003)), m["lamp"] + 0.06 * j,
            -0.3 + 0.3 * j, 0.05)
    # doira: morning (soft), noon, real section
    def doira(a, b, g):
        for k, t0 in enumerate(np.arange(a, b - 0.05, BEAT)):
            bar_pos = k % 4
            if bar_pos in (0, 2):
                add(dum(rng), t0, 0, g)
            if bar_pos in (1, 3):
                add(tak(rng), t0, 0.15, g * 0.55)
            add(tak(rng), t0 + BEAT * 0.5, -0.15, g * 0.25)
            add(zang(rng), t0 + BEAT * 0.75, 0.3, g * 0.35)
    doira(m["rise"] + 0.3 + 4 * BEAT, m["tl1"], 0.22)
    doira(m["noon"], m["tl2"], 0.30)
    doira(m["real"] + 0.1, m["end"], 0.30)
    # real section phrase, ending: D major figure + strum
    phrase(m["real"] + 0.1, 0, 0.8, 2)
    for j, mm in enumerate([62, 66, 69, 74]):
        add(dutar(mm, 3.5, rng, 0.8), m["end"] + 0.15 + 0.035 * j, -0.2 + 0.13 * j, 0.5)
    for j, mm in enumerate([74, 76, 78, 81]):
        add(dutar(mm, 2.6, rng, 0.6), m["end"] + 1.2 + j * BEAT / 2, 0.2, 0.42)
    add(dutar(74, 4.0, rng, 0.7), m["end"] + 1.2 + 4 * BEAT / 2 + BEAT, 0, 0.45)

    wl, wr = fftconvolve(L, hall(211))[:n], fftconvolve(R, hall(212))[:n]
    L, R = L * 0.8 + wl * 0.35, R * 0.8 + wr * 0.35
    b_, a_ = butter(2, 35 / (SR / 2), "high")
    L, R = lfilter(b_, a_, L), lfilter(b_, a_, R)
    mm_ = int(total * SR)
    L, R = L[:mm_], R[:mm_]
    fi = int(0.3 * SR)
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


if __name__ == "__main__":
    import time
    t0 = time.time()
    dutar_bed("/tmp/claude-0/-home-claude/29c18e40-edfd-55e7-a3e1-da5539b3418b/scratchpad/dutar_test.wav", 22.7,
              dict(rise=2.9, tl1=6.5, noon=8.0, tl2=9.8, close=11.6, lamp=12.6, real=13.4, end=17.2))
    print("ok", round(time.time() - t0, 1))
