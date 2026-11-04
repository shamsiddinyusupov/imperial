"""Lo-fi half-time bed on the 120 BPM grid (feels 60 BPM), cuts at 3/8/13/18 s land on beats."""
import math, wave
import numpy as np

SR = 48000


def music_lofi(path, TOTAL=22.0, SECT=(3.0, 8.0, 13.0), T_END=18.0):
    n = int(SR * (TOTAL + 1.5))
    L = np.zeros(n); R = np.zeros(n)
    rng = np.random.default_rng(17)

    def add(sig, t0, gl=1.0, gr=1.0):
        i = int(t0 * SR)
        if i >= n or i < 0:
            return
        j = min(n, i + len(sig))
        L[i:j] += sig[: j - i] * gl
        R[i:j] += sig[: j - i] * gr

    tt = lambda d: np.arange(int(d * SR)) / SR
    note = lambda m: 440.0 * 2 ** ((m - 69) / 12)

    def lp(x, k):  # cheap low-pass
        return np.convolve(x, np.ones(k) / k, "same")

    def kick(v=0.85):
        t = tt(0.45)
        f = 40 + 70 * np.exp(-t / 0.04)
        return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.18) * v

    def snare(v=0.3):
        t = tt(0.3)
        x = lp(rng.normal(0, 1, len(t)), 3)
        body = np.sin(2 * np.pi * 190 * t) * np.exp(-t / 0.05)
        return (x * np.exp(-t / 0.09) * 0.7 + body * 0.4) * v

    def hat(v=0.05):
        t = tt(0.05)
        x = rng.normal(0, 1, len(t)); x = x - lp(x, 4)
        return x * np.exp(-t / 0.015) * v

    def keys(m, d, v=0.07):  # warm electric-piano tone
        t = tt(d); f = note(m)
        s = np.sin(2 * np.pi * f * t + 1.1 * np.sin(2 * np.pi * f * t) * np.exp(-t / 0.5))
        s += 0.2 * np.sin(2 * np.pi * 2 * f * t) * np.exp(-t / 0.3)
        e = np.minimum(1, t / 0.008) * np.exp(-t / 1.6) * np.minimum(1, (d - t) / 0.1)
        return s * e * (1 + 0.12 * np.sin(2 * np.pi * 5 * t)) * v

    def bass(m, d, v=0.3):
        t = tt(d); f = note(m)
        s = np.sin(2 * np.pi * f * t) + 0.25 * np.sin(2 * np.pi * 2 * f * t)
        return s * np.minimum(1, t / 0.02) * np.exp(-t / 0.9) * np.minimum(1, (d - t) / 0.05) * v

    def bell(m, v=0.04):
        t = tt(1.2); f = note(m)
        s = np.sin(2 * np.pi * f * t) + 0.25 * np.sin(2 * np.pi * 2.76 * f * t) * np.exp(-t / 0.2)
        return s * np.minimum(1, t / 0.003) * np.exp(-t / 0.5) * v

    def swish(t0, d=0.4, v=0.2):
        t = tt(d)
        x = lp(rng.normal(0, 1, len(t)), 6)
        add(x * np.sin(np.pi * t / d) ** 2 * v, t0 - d * 0.6, 0.8, 1.0)

    # Dmaj9 - Bm9 - Gmaj7 - A13sus (one chord per 2 s)
    chords = [(38, [62, 66, 69, 73, 76]), (35, [59, 62, 66, 69, 73]), (31, [55, 59, 62, 66, 69]), (33, [57, 62, 64, 67, 71])]
    for b in range(int(math.ceil(TOTAL / 2)) + 1):
        t0 = b * 2.0
        if t0 >= TOTAL:
            break
        root, tones = chords[b % 4]
        for k, m in enumerate(tones):  # slightly strummed chord
            add(keys(m, 2.1, 0.055), t0 + 0.018 * k, 1.0 - 0.06 * k, 0.76 + 0.06 * k)
        add(keys(tones[2] + 12, 0.9, 0.035), t0 + 1.25, 0.8, 1.0)
        if t0 >= SECT[0] - 0.01:
            add(bass(root, 1.4), t0)
            add(bass(root + 7, 0.5, 0.22), t0 + 1.5)
    melody = [78, 76, 74, 73, 74, 76, 81, 78]
    for k, t0 in enumerate(np.arange(SECT[0], T_END, 1.0)):
        if k % 2 == 0:
            add(bell(melody[(k // 2) % len(melody)]), t0 + 0.5, 0.9, 1.0)
    for i in range(int(TOTAL / 0.5)):
        tb = i * 0.5
        if tb < SECT[0]:
            if i % 4 == 0:
                add(kick(0.6), tb)
            add(hat(0.03), tb + 0.25)
            continue
        soft = tb >= T_END
        pos = i % 4  # half-time: kick on 1, snare on 3 (every 2 s cycle = 4 half-beats)
        if pos == 0:
            add(kick(0.7 if soft else 0.85), tb)
        if pos == 2:
            add(snare(0.22 if soft else 0.3), tb, 0.95, 1.0)
        if pos == 3 and i % 8 == 7:
            add(kick(0.5), tb + 0.25)
        add(hat(0.045), tb, 0.8, 1.0)
        add(hat(0.03), tb + 0.25 + 0.03, 0.8, 1.0)  # lazy swing
    for t0 in [1.0, 2.0] + list(SECT) + [T_END]:
        swish(t0, 0.4, 0.14 if t0 < SECT[0] else 0.2)
    # vinyl crackle
    m = int(TOTAL * SR)
    cr = np.zeros(m)
    idx = rng.integers(0, m, int(TOTAL * 90))
    cr[idx] = rng.normal(0, 1, len(idx)) * 0.12
    hiss = lp(rng.normal(0, 1, m), 2) * 0.004
    L[:m] += cr + hiss; R[:m] += np.roll(cr, 37) + hiss
    L, R = L[:m], R[:m]
    L = 0.85 * L + 0.15 * lp(L, 8); R = 0.85 * R + 0.15 * lp(R, 8)  # soften highs
    for dl, g in ((0.031, 0.22), (0.057, 0.15), (0.091, 0.1)):
        s = int(dl * SR)
        L[s:] += R[:-s] * g; R[s:] += L[:-s] * g * 0.9
    fade = np.minimum(1, (m - np.arange(m)) / (1.0 * SR)) * np.minimum(1, np.arange(m) / (0.03 * SR))
    L, R = L * fade, R * fade
    pk = max(np.abs(L).max(), np.abs(R).max())
    pcm = (np.stack([L, R], 1) / pk * 0.9 * 32767).astype(np.int16)
    with wave.open(path, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())


if __name__ == "__main__":
    music_lofi("/home/claude/reels/mato/music_lofi.wav")
    print("ok")
