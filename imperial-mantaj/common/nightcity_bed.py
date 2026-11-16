"""Original bed #19 (not used before): «night city» — clean electric guitar (Karplus-Strong through a pickup filter,
chorus and tremolo) playing slow arpeggios over a warm sub pad, with a city ambience (traffic rumble, passing cars,
a distant horn) that gets MUFFLED and quiet the moment the blind closes; a glass «whoosh» when the camera goes
through the window and a soft swell + chime when the logo appears. E minor colours, 72 BPM.

nightcity_bed(path, total, whoosh_at, inside_at, close_at, logo_at, end_at, seed=19)
"""
import wave

import numpy as np
from scipy.signal import butter, fftconvolve, lfilter, sosfilt

SR = 48000
BPM = 72
BEAT = 60 / BPM


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def ks(f, dur, rng, bright=0.6, decay=0.9975):
    N = max(2, int(round(SR / f)))
    n = int(dur * SR)
    ex = rng.uniform(-1, 1, N)
    a = np.exp(-2 * np.pi * (800 + 6000 * bright) / SR)
    ex = lfilter([1 - a], [1, -a], ex)
    ex = ex - np.roll(ex, max(1, N // 5))
    out = np.zeros(n + 2 * N)
    out[:N] = ex - ex.mean()
    for i in range(N, n + N, N):
        prev = out[i - N:i]
        sh = out[i - N - 1:i - 1] if i - N - 1 >= 0 else np.concatenate([[0.0], prev[:-1]])
        out[i:i + N] = decay * 0.5 * (prev + sh)
    y = out[:n]
    return y / (np.abs(y).max() + 1e-9)


def guitar(m, dur, rng):
    y = ks(hz(m), dur, rng)
    sos = butter(2, [120 / (SR / 2), 3200 / (SR / 2)], "band", output="sos")
    y = sosfilt(sos, y)
    t = np.arange(len(y)) / SR
    return y * np.exp(-t / 2.2) / (np.abs(y).max() + 1e-9)


def chorus(x, rng):
    n = len(x)
    t = np.arange(n) / SR
    d = (0.012 + 0.003 * np.sin(2 * np.pi * 0.6 * t)) * SR
    idx = np.clip(np.arange(n) - d, 0, n - 1)
    i0 = idx.astype(int)
    fr = idx - i0
    i1 = np.minimum(i0 + 1, n - 1)
    return x[i0] * (1 - fr) + x[i1] * fr


def pad(tones, dur, rng):
    n = int(dur * SR)
    t = np.arange(n) / SR
    out = np.zeros(n)
    for m in tones:
        for det in (-0.2, 0.2):
            out += np.sin(2 * np.pi * (hz(m) + det) * t + rng.uniform(0, 6.28))
    env = np.minimum(1, t / 1.5) * np.clip((dur - t) / 1.5, 0, 1)
    return out * env / (np.abs(out).max() + 1e-9)


def city(n, rng):
    """traffic rumble + passing cars + far horn"""
    x = rng.normal(0, 1, n)
    rumble = lfilter([1], [1, -0.995], x)
    rumble = sosfilt(butter(2, 180 / (SR / 2), "low", output="sos"), rumble)
    rumble /= np.abs(rumble).max() + 1e-9
    out = rumble * 0.6
    t = 0.4
    while t < n / SR:
        d = rng.uniform(2.5, 4.0)
        m = int(d * SR)
        i = int(t * SR)
        if i + m > n:
            break
        car = rng.normal(0, 1, m)
        tt = np.arange(m) / SR
        fc = 900 * (1.3 - 0.6 * tt / d)
        car = sosfilt(butter(2, [300 / (SR / 2), 2400 / (SR / 2)], "band", output="sos"), car)
        env = np.exp(-((tt - d / 2) / (d / 4)) ** 2)
        out[i:i + m] += car * env * rng.uniform(0.15, 0.3) * (fc / fc.max())
        t += rng.uniform(1.5, 3.0)
    h = int(2.2 * SR)                                                    # one distant horn
    if n > h + int(5.5 * SR):
        tt = np.arange(int(0.5 * SR)) / SR
        horn = (np.sign(np.sin(2 * np.pi * 330 * tt)) + np.sign(np.sin(2 * np.pi * 415 * tt))) * 0.5
        horn = sosfilt(butter(2, 1500 / (SR / 2), "low", output="sos"), horn) * np.sin(np.pi * tt / 0.5)
        out[int(5.0 * SR):int(5.0 * SR) + len(horn)] += horn * 0.05
    return out


def whoosh(rng, dur=0.6):
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = rng.normal(0, 1, n)
    out = np.zeros(n)
    for k in range(12):
        s, e = k * n // 12, (k + 1) * n // 12
        fc = 600 * 2 ** (k * 0.35)
        out[s:e] = sosfilt(butter(2, [fc * 0.6 / (SR / 2), min(0.99, fc * 1.5 / (SR / 2))], "band", output="sos"), x[s:e])
    return out * np.sin(np.pi * t / dur) ** 2


def chime(m, dur=3.0):
    t = np.arange(int(dur * SR)) / SR
    f = hz(m)
    y = sum(a * np.sin(2 * np.pi * f * r * t) * np.exp(-t / d) for r, a, d in [(1, 1, 1.6), (2.76, 0.4, 0.7), (5.4, 0.15, 0.3)])
    return y * (1 - np.exp(-t / 0.002))


def hall(seed, secs=3.2):
    r = np.random.default_rng(seed)
    t = np.arange(int(secs * SR)) / SR
    ir = r.normal(0, 1, len(t)) * np.exp(-t / 1.0)
    ir = lfilter([0.3], [1, -0.65], ir)
    ir[: int(0.02 * SR)] = 0
    return ir / np.sqrt((ir ** 2).sum())


PROG = [(40, [52, 59, 64, 66, 71]), (36, [52, 55, 59, 62, 67]), (43, [55, 59, 62, 64, 71]), (38, [54, 57, 62, 66, 69])]


def nightcity_bed(path, total, whoosh_at, inside_at, close_at, logo_at, end_at, seed=19):
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

    # guitar arpeggios (8ths), tremolo, chorus on the right channel
    gl, gr = np.zeros(n), np.zeros(n)
    bar = 4 * BEAT
    t, k = 0.0, 0
    while t < total - 1.0:
        root, tones = PROG[k % 4]
        add(pad([root, root + 7, root + 12], bar + 1.5, rng), t, 0, 0.12)
        pat = [0, 2, 3, 4, 3, 2, 1, 3]
        for e in range(8):
            te = t + e * BEAT / 2
            if te >= total - 1.0:
                break
            s = guitar(tones[pat[e]], 2.2, rng) * (0.9 if e % 2 == 0 else 0.7)
            i = int(te * SR)
            j = min(n, i + len(s))
            gl[i:j] += s[: j - i]
        t += bar
        k += 1
    tt = np.arange(n) / SR
    trem = 1 - 0.32 * (0.5 + 0.5 * np.sin(2 * np.pi * 4.8 * tt))
    gl *= trem
    gr = chorus(gl, rng)
    L += gl * 0.16
    R += gr * 0.16
    # final chord ring at the logo
    for j, m in enumerate([40, 52, 59, 64, 66, 71, 76]):
        add(guitar(m, 4.0, rng), logo_at + 0.06 * j, -0.3 + 0.1 * j, 0.14)
    add(chime(88, 3.0), logo_at + 0.35, 0.2, 0.05)
    add(chime(95, 2.5), logo_at + 0.55, -0.2, 0.035)
    # city ambience: open until the blind closes, then muffled and quiet
    c = city(n, rng)
    cut = np.ones(n)
    a0, a1 = int(close_at * SR), int((close_at + 0.7) * SR)
    cut[a0:a1] = np.linspace(1, 0.18, a1 - a0)
    cut[a1:] = 0.18
    fade_in = np.minimum(1, tt / 0.8)
    open_ = sosfilt(butter(2, 6000 / (SR / 2), "low", output="sos"), c)
    muff = sosfilt(butter(2, 280 / (SR / 2), "low", output="sos"), c)
    mix = np.where(tt < close_at, 1.0, np.clip(1 - (tt - close_at) / 0.7, 0, 1))
    amb = (open_ * mix + muff * (1 - mix)) * cut * fade_in
    L += amb * 0.22
    R += np.roll(amb, 900) * 0.22
    add(whoosh(rng), whoosh_at - 0.3, 0, 0.18)

    wl, wr = fftconvolve(L, hall(191))[:n], fftconvolve(R, hall(192))[:n]
    L, R = L * 0.8 + wl * 0.42, R * 0.8 + wr * 0.42
    b_, a_ = butter(2, 30 / (SR / 2), "high")
    L, R = lfilter(b_, a_, L), lfilter(b_, a_, R)
    m = int(total * SR)
    L, R = L[:m], R[:m]
    fi = int(0.3 * SR)
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
    nightcity_bed("/tmp/claude-0/-home-claude/29c18e40-edfd-55e7-a3e1-da5539b3418b/scratchpad/nc_test.wav", 19, 3.8, 3.8,
                  8.6, 10.0, 13.9)
    print("ok", round(time.time() - t0, 1))
