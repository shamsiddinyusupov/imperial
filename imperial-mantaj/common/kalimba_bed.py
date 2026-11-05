"""Original bed #8 (not used before): kalimba (thumb piano: fundamental + 5.4x and 13x tine partials, soft click),
dark warm pad and a quiet sub, slow tape wow. Key of D minor -> F major, ~64 BPM. Made to sit under a narrator
(leave room in 200–3000 Hz; mix it low and duck it with the voice).

kalimba_bed(path, total, plan, seed=8)
  plan = dict(chords=[(t, root, [tones])...], notes=[(t, midi, vel)...])
"""
import wave

import numpy as np
from scipy.signal import butter, fftconvolve, lfilter

SR = 48000


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def tine(m, vel, rng, dur=2.4):
    t = np.arange(int(dur * SR)) / SR
    f = hz(m) * (1 + rng.normal(0, 0.0015))
    y = np.sin(2 * np.pi * f * t) * np.exp(-t / 0.9)
    y += 0.18 * np.sin(2 * np.pi * f * 5.4 * t) * np.exp(-t / 0.12)
    y += 0.05 * np.sin(2 * np.pi * f * 13.0 * t) * np.exp(-t / 0.03)
    clk = rng.normal(0, 1, int(0.004 * SR)) * 0.15
    y[:len(clk)] += clk
    return y * (1 - np.exp(-t / 0.0015)) * vel


def pad(tones, dur, rng, att=1.6, rel=1.8):
    t = np.arange(int(dur * SR)) / SR
    out = np.zeros_like(t)
    for m in tones:
        for det in (-0.2, 0.18):
            ph = 2 * np.pi * (hz(m) + det) * t + rng.uniform(0, 6.28)
            for h in range(1, 7):
                out += np.sin(h * ph) / h / (1 + (h * hz(m) / 700) ** 3)
    env = np.minimum(1, t / att) ** 1.8 * np.clip((dur - t) / rel, 0, 1)
    return out * env / (np.abs(out).max() + 1e-9)


def hall(seed, secs=3.4):
    r = np.random.default_rng(seed)
    t = np.arange(int(secs * SR)) / SR
    ir = r.normal(0, 1, len(t)) * np.exp(-t / 1.0)
    ir = lfilter([0.3], [1, -0.74], ir)
    ir[: int(0.02 * SR)] = 0
    return ir / np.sqrt((ir ** 2).sum())


def kalimba_bed(path, total, plan, seed=8):
    rng = np.random.default_rng(seed)
    n = int((total + 3.5) * SR)
    L, R = np.zeros(n), np.zeros(n)

    def add(sig, t0, pan=0.0, g=1.0):
        i = int(round(t0 * SR))
        if i >= n:
            return
        if i < 0:
            sig, i = sig[-i:], 0
        j = min(n, i + len(sig))
        L[i:j] += sig[: j - i] * g * (1 - pan) ** 0.5
        R[i:j] += sig[: j - i] * g * (1 + pan) ** 0.5

    ch = plan["chords"]
    for k, (t0, root, tones) in enumerate(ch):
        t1 = ch[k + 1][0] if k + 1 < len(ch) else total + 1.5
        add(pad(tones, t1 - t0 + 1.8, rng), t0 - (0 if k == 0 else 0.5), 0, 0.22)
        tt = np.arange(int(min(4.0, t1 - t0 + 0.6) * SR)) / SR
        add(np.sin(2 * np.pi * hz(root) * tt) * np.minimum(1, tt / 0.2) * np.exp(-tt / 2.6), t0, 0, 0.20)
    for i, (t0, m, vel) in enumerate(plan.get("notes", [])):
        add(tine(m, vel, rng), t0 + rng.normal(0, 0.006), 0.5 * np.sin(i * 1.3))
    # slow tape wow on the whole bed
    tt = np.arange(n) / SR
    idx = np.clip(np.arange(n) + (0.0009 * SR) * np.sin(2 * np.pi * 0.35 * tt), 0, n - 1)
    L, R = np.interp(idx, np.arange(n), L), np.interp(idx, np.arange(n), R)
    wl, wr = fftconvolve(L, hall(71))[:n], fftconvolve(R, hall(72))[:n]
    L, R = L * 0.72 + wl * 0.6, R * 0.72 + wr * 0.6
    b_, a_ = butter(2, 40 / (SR / 2), "high")
    L, R = lfilter(b_, a_, L), lfilter(b_, a_, R)
    m = int(total * SR)
    L, R = L[:m], R[:m]
    fi = int(0.4 * SR)
    L[:fi] *= np.linspace(0, 1, fi)
    R[:fi] *= np.linspace(0, 1, fi)
    fade = int(2.2 * SR)
    L[-fade:] *= np.linspace(1, 0, fade) ** 1.5
    R[-fade:] *= np.linspace(1, 0, fade) ** 1.5
    pk = max(np.abs(L).max(), np.abs(R).max()) + 1e-9
    st = (np.stack([L, R], 1) / pk * 0.7 * 32767).astype(np.int16)
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(st.tobytes())
