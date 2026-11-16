"""Original bed #20 (not used before): «analog night» — a warm 80s analog polysynth (detuned saw «brass» pad with a
slow filter swell, like the classic film synths), soft FM bell motifs, a deep sub, and the distant city hum that
thins out as the windows go dark. The pad filter CLOSES while the blind comes down (sound follows the fabric), a
bright swell + bell cluster when the mark appears, an open pull-back chord, then a calm cadence. A minor -> C major.

analog_bed(path, total, down_at, down_dur, logo_at, back_at, end_at, seed=20)
"""
import wave

import numpy as np
from scipy.signal import butter, fftconvolve, lfilter, sosfilt

SR = 48000


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def saw_pad(tones, dur, rng, cut_fn):
    """detuned saws through a time-varying one-pole low-pass (cut_fn(t) in Hz)"""
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = np.zeros(n)
    for m in tones:
        for det in (-0.12, 0.0, 0.11):
            f = hz(m) * (1 + det / 100) * (1 + 0.0015 * np.sin(2 * np.pi * 0.3 * t + rng.uniform(0, 6)))
            ph = (np.cumsum(f) / SR + rng.uniform(0, 1)) % 1.0
            x += 2 * ph - 1
    cut = cut_fn(t)
    # block-wise biquad low-pass so the cutoff can move
    y = np.zeros(n)
    blk = 1024
    zi = np.zeros((1, 2))
    for i in range(0, n, blk):
        fc = float(np.clip(cut[min(i + blk // 2, n - 1)], 80, 12000))
        sos = butter(2, fc / (SR / 2), "low", output="sos")
        y[i:i + blk], zi = sosfilt(sos, x[i:i + blk], zi=zi)
    env = np.minimum(1, t / 1.2) * np.clip((dur - t) / 1.2, 0, 1)
    return y * env / (np.abs(y).max() + 1e-9)


def fm_bell(m, dur=2.5, idx=2.2):
    t = np.arange(int(dur * SR)) / SR
    f = hz(m)
    mod = idx * np.exp(-t / 0.5) * np.sin(2 * np.pi * f * 3.5 * t)
    return np.sin(2 * np.pi * f * t + mod) * np.exp(-t / 0.9) * (1 - np.exp(-t / 0.002))


def sub(m, dur):
    t = np.arange(int(dur * SR)) / SR
    return np.sin(2 * np.pi * hz(m) * t) * np.minimum(1, t / 0.8) * np.clip((dur - t) / 1.0, 0, 1)


def hum(n, rng):
    x = rng.normal(0, 1, n)
    y = lfilter([1], [1, -0.996], x)
    y = sosfilt(butter(2, 220 / (SR / 2), "low", output="sos"), y)
    return y / (np.abs(y).max() + 1e-9)


def hall(seed, secs=4.0):
    r = np.random.default_rng(seed)
    t = np.arange(int(secs * SR)) / SR
    ir = r.normal(0, 1, len(t)) * np.exp(-t / 1.4)
    ir = lfilter([0.3], [1, -0.7], ir)
    ir[: int(0.025 * SR)] = 0
    return ir / np.sqrt((ir ** 2).sum())


CH = [(45, [57, 60, 64, 71]), (41, [57, 60, 65, 69]), (43, [55, 59, 62, 67]), (40, [55, 59, 64, 71])]   # Am9 F G Em7


def analog_bed(path, total, down_at, down_dur, logo_at, back_at, end_at, seed=20):
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

    def cut_global(t_abs):
        c = 900 + 2600 * np.clip(t_abs / max(1e-3, down_at), 0, 1)                 # opens up toward the blind
        d = np.clip((t_abs - down_at) / down_dur, 0, 1)
        c = c * (1 - 0.72 * d)                                                    # closes as the fabric comes down
        lg = np.clip((t_abs - logo_at) / 0.8, 0, 1) * np.clip(1 - (t_abs - back_at - 1.5) / 3, 0, 1)
        return c + 3800 * lg

    seg = 3.15
    t0, k = 0.0, 0
    while t0 < end_at - 0.1:
        root, tones = CH[k % 4]
        d = min(seg + 1.4, total - t0)
        add(saw_pad(tones, d, rng, lambda tt, a=t0: cut_global(tt + a)), max(0, t0 - 0.4), 0, 0.30)
        add(sub(root - 12, d), max(0, t0 - 0.4), 0, 0.22)
        t0 += seg
        k += 1
    # bells: a descending motif while the blind comes down, a cluster when the mark appears
    for j, m in enumerate([88, 86, 84, 81, 79, 76]):
        add(fm_bell(m, 2.2, 1.6), down_at + j * down_dur / 6, 0.4 * np.sin(j), 0.06)
    for j, m in enumerate([72, 76, 79, 83, 88]):
        add(fm_bell(m, 3.0, 2.6), logo_at + 0.07 * j, -0.4 + 0.2 * j, 0.07)
    for j, m in enumerate([60, 67, 72, 76]):
        add(fm_bell(m, 3.0, 1.2), back_at + 0.4 + 0.12 * j, 0.3 - 0.2 * j, 0.05)
    # end: C major cadence
    add(saw_pad([60, 64, 67, 72, 76], total - end_at + 1, rng, lambda tt: 2600 + 0 * tt), end_at - 0.3, 0, 0.30)
    add(sub(36, total - end_at + 1), end_at - 0.3, 0, 0.22)
    for j, m in enumerate([79, 84, 88]):
        add(fm_bell(m, 3.0, 1.8), end_at + 0.3 + 0.2 * j, -0.3 + 0.3 * j, 0.05)
    # distant city hum, thinning as the house falls asleep
    h = hum(n, rng)
    tt = np.arange(n) / SR
    env = np.clip(1 - (tt - down_at) / (back_at - down_at + 2), 0.25, 1) * np.minimum(1, tt / 1.0)
    L += h * env * 0.10
    R += np.roll(h, 1500) * env * 0.10

    wl, wr = fftconvolve(L, hall(201))[:n], fftconvolve(R, hall(202))[:n]
    L, R = L * 0.75 + wl * 0.45, R * 0.75 + wr * 0.45
    b_, a_ = butter(2, 28 / (SR / 2), "high")
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
    import time
    t0 = time.time()
    analog_bed("/tmp/claude-0/-home-claude/29c18e40-edfd-55e7-a3e1-da5539b3418b/scratchpad/an_test.wav", 21, 3.6, 3.5,
               8.3, 10.4, 15.6)
    print("ok", round(time.time() - t0, 1))
