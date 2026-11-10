"""Original bed #13 (not used before): warm jazz-lounge trio — archtop-guitar comping (Karplus-Strong strums),
walking upright bass, brushes on a swung ride pattern. ii-V-I in C, 88 BPM, swing. Ends on a ringing Cmaj9.

lounge_bed(path, total, end_at, seed=13)
  end_at = end-card start (groove softens there); the final Cmaj9 rings out 2.7 s before the end
"""
import wave

import numpy as np
from scipy.signal import butter, fftconvolve, lfilter

SR = 48000
BPM = 88
BEAT = 60 / BPM
SW = 0.62          # swing ratio for off-beats


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def ks(f, dur, rng, bright=0.55, decay=0.996, pick=0.0):
    """Karplus-Strong string, vectorised one period at a time."""
    N = max(2, int(round(SR / f)))
    n = int(dur * SR)
    ex = rng.uniform(-1, 1, N)
    a = np.exp(-2 * np.pi * (300 + 6000 * bright) / SR)          # soften the pluck
    ex = lfilter([1 - a], [1, -a], ex)
    if pick:                                                      # pick position comb
        k = max(1, int(N * pick))
        ex = ex - np.roll(ex, k)
    out = np.zeros(n + 2 * N)
    out[:N] = ex - ex.mean()
    for k in range(N, n + N, N):
        prev = out[k - N:k]
        sh = out[k - N - 1:k - 1] if k - N - 1 >= 0 else np.concatenate([[0.0], prev[:-1]])
        out[k:k + N] = decay * 0.5 * (prev + sh)
    y = out[:n]
    return y / (np.abs(y).max() + 1e-9)


def env_tail(sig, rel=0.08):
    r = int(rel * SR)
    if len(sig) > r:
        sig[-r:] *= np.linspace(1, 0, r)
    return sig


VOICINGS = {   # archtop shell voicings (midi) for each chord symbol
    "Dm9": [50, 53, 57, 60, 64],
    "G13": [43, 53, 59, 64],
    "Cmaj9": [48, 52, 55, 59, 62],
    "A7b13": [45, 55, 61, 65],
    "Fmaj7": [41, 52, 57, 60],
    "E7": [40, 50, 56, 59],
}
ROOT = {"Dm9": 38, "G13": 43, "Cmaj9": 36, "A7b13": 45, "Fmaj7": 41, "E7": 40}
TONES = {"Dm9": [0, 3, 7, 10], "G13": [0, 4, 7, 10], "Cmaj9": [0, 4, 7, 11], "A7b13": [0, 4, 7, 10],
         "Fmaj7": [0, 4, 7, 11], "E7": [0, 4, 7, 10]}
PROG = ["Dm9", "G13", "Cmaj9", "A7b13", "Fmaj7", "E7", "Dm9", "G13"]


def hall(seed, secs=2.2):
    r = np.random.default_rng(seed)
    t = np.arange(int(secs * SR)) / SR
    ir = r.normal(0, 1, len(t)) * np.exp(-t / 0.55)
    ir = lfilter([0.35], [1, -0.6], ir)
    ir[: int(0.012 * SR)] = 0
    return ir / np.sqrt((ir ** 2).sum())


def lounge_bed(path, total, end_at, seed=13):
    rng = np.random.default_rng(seed)
    n = int((total + 3) * SR)
    L, R = np.zeros(n), np.zeros(n)

    def add(sig, t0, p=0.0, g=1.0):
        i = int(round(t0 * SR))
        if i >= n or i < 0:
            return
        j = min(n, i + len(sig))
        L[i:j] += sig[: j - i] * g * (1 - p) ** 0.5
        R[i:j] += sig[: j - i] * g * (1 + p) ** 0.5

    def guitar_strum(sym, t0, g, length=0.42, down=True):
        v = VOICINGS[sym]
        order = v if down else v[::-1]
        for k, m in enumerate(order):
            s = ks(hz(m), length + 0.6, rng, bright=0.35, decay=0.9975, pick=0.18)
            s *= np.minimum(1, (len(s) - np.arange(len(s))) / (0.06 * SR))
            s[int(length * SR):] *= np.exp(-np.arange(len(s) - int(length * SR)) / (0.05 * SR))
            add(s, t0 + 0.012 * k, -0.25 + 0.1 * k, g * (0.9 if k else 1.0))

    def bass(m, t0, dur, g=0.55):
        s = ks(hz(m), dur + 0.25, rng, bright=0.05, decay=0.9985)
        t = np.arange(len(s)) / SR
        s = s * 0.7 + 0.5 * np.sin(2 * np.pi * hz(m) * t) * np.exp(-t / 0.6)
        s *= np.exp(-t / 0.9)
        add(env_tail(s, 0.06), t0, 0.0, g)

    def brush_swish(t0, g):
        d = 0.32
        x = rng.normal(0, 1, int(d * SR))
        b, a = butter(2, [1800 / (SR / 2), 7500 / (SR / 2)], "band")
        x = lfilter(b, a, x)
        t = np.arange(len(x)) / SR
        x *= np.minimum(1, t / 0.07) * np.exp(-t / 0.12)
        add(x, t0, 0.15, g)

    def tap(t0, g):
        d = 0.08
        x = rng.normal(0, 1, int(d * SR))
        b, a = butter(2, 5000 / (SR / 2), "high")
        x = lfilter(b, a, x) * np.exp(-np.arange(int(d * SR)) / (0.012 * SR))
        add(x, t0, 0.35, g)

    bar = 4 * BEAT
    t, k = 0.0, 0
    tf = total - 2.7                       # final chord
    stop = tf
    while t < stop - 0.05:
        gf = 1.0 if t < end_at - 0.1 else 0.75
        sym = PROG[k % len(PROG)]
        nxt = PROG[(k + 1) % len(PROG)]
        # comping: beat 1 short, "and of 2" push, beat 4 light
        guitar_strum(sym, t, 0.16 * gf, 0.30)
        if t + BEAT * (1 + SW) < stop:
            guitar_strum(sym, t + BEAT * (1 + SW), 0.13 * gf, 0.22, down=False)
        if t + 3 * BEAT < stop:
            guitar_strum(sym, t + 3 * BEAT, 0.09 * gf, 0.16)
        # walking bass: root, chord tone, chord tone, chromatic approach to next root
        r = ROOT[sym]
        tn = TONES[sym]
        line = [r, r + tn[1 + (k % 2)], r + tn[2], ROOT[nxt] + (1 if k % 2 else -1)]
        for b_, m in enumerate(line):
            tb = t + b_ * BEAT
            if tb < stop - 0.05:
                bass(m, tb, BEAT * 0.95, (0.5 if b_ == 0 else 0.42) * gf)
        # brushes: swish on 2 & 4, swung ride taps
        for b_ in range(4):
            tb = t + b_ * BEAT
            if tb >= stop - 0.05:
                break
            if b_ in (1, 3):
                brush_swish(tb, 0.05 * gf)
            tap(tb, (0.035 if b_ % 2 == 0 else 0.028) * gf)
            if b_ in (1, 3) and tb + BEAT * SW < stop:
                tap(tb + BEAT * SW, 0.022)
        t += bar
        k += 1
    # resolution on the end card: slow rolled Cmaj9, bass C, a last soft swish
    for kk, m in enumerate([36, 43, 52, 55, 59, 62, 67]):
        s = ks(hz(m), 4.5, rng, bright=0.3, decay=0.9992, pick=0.2)
        s *= np.exp(-np.arange(len(s)) / (2.0 * SR))
        add(s, tf + 0.05 * kk, -0.3 + 0.1 * kk, 0.22)
    bass(36, tf, 3.0, 0.55)
    brush_swish(tf, 0.05)

    wl, wr = fftconvolve(L, hall(131))[:n], fftconvolve(R, hall(132))[:n]
    L, R = L * 0.85 + wl * 0.3, R * 0.85 + wr * 0.3
    b_, a_ = butter(2, 35 / (SR / 2), "high")
    L, R = lfilter(b_, a_, L), lfilter(b_, a_, R)
    b_, a_ = butter(2, 9000 / (SR / 2), "low")
    L, R = lfilter(b_, a_, L), lfilter(b_, a_, R)
    m = int(total * SR)
    L, R = L[:m], R[:m]
    fi = int(0.02 * SR)
    L[:fi] *= np.linspace(0, 1, fi)
    R[:fi] *= np.linspace(0, 1, fi)
    fade = int(1.8 * SR)
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
    lounge_bed("/tmp/claude-0/-home-claude/29c18e40-edfd-55e7-a3e1-da5539b3418b/scratchpad/lounge_test.wav", 26, 20.5)
    print("ok", time.time() - t0)
