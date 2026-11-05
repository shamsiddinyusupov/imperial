"""Original bed #7 (not used before): music box (steel-comb partials 1 : 3.93 : 9.4, quick decay) over a warm
analogue-style pad, a soft sub, faint vinyl air. Key of E major, 70 BPM. A «switch» can drop the colour:
after `switch_t` the box plays an octave lower, the pad turns to the relative minor and darkens.

musicbox_bed(path, total, plan, seed=7)
  plan = dict(chords=[(t, root, [tones])...], melody=[(t, midi, vel)...], clicks=[t...])
"""
import wave

import numpy as np
from scipy.signal import butter, fftconvolve, lfilter

SR = 48000


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def box(m, vel, dur=2.6):
    t = np.arange(int(dur * SR)) / SR
    f = hz(m)
    y = np.sin(2 * np.pi * f * t) * np.exp(-t / 1.1)
    y += 0.30 * np.sin(2 * np.pi * f * 3.93 * t) * np.exp(-t / 0.25)
    y += 0.10 * np.sin(2 * np.pi * f * 9.4 * t) * np.exp(-t / 0.06)
    y *= 1 - np.exp(-t / 0.001)
    return y * vel


def pad(tones, dur, rng, bright, att=1.1, rel=1.4):
    t = np.arange(int(dur * SR)) / SR
    out = np.zeros_like(t)
    cut = 900 + 1400 * bright
    for m in tones:
        for det in (-0.3, 0.27):
            ph = 2 * np.pi * (hz(m) + det) * t + rng.uniform(0, 6.28)
            for h in range(1, 9):
                out += np.sin(h * ph) / h / (1 + (h * hz(m) / cut) ** 3)
    env = np.minimum(1, t / att) ** 1.6 * np.clip((dur - t) / rel, 0, 1)
    return out * env / (np.abs(out).max() + 1e-9)


def click():
    t = np.arange(int(0.06 * SR)) / SR
    r = np.random.default_rng(3)
    b, a = butter(2, [1800 / (SR / 2), 6000 / (SR / 2)], "band")
    x = lfilter(b, a, r.normal(0, 1, len(t))) * np.exp(-t / 0.004)
    x += 0.6 * np.sin(2 * np.pi * 1100 * t) * np.exp(-t / 0.01)
    return x


def hall(seed, secs=3.2):
    r = np.random.default_rng(seed)
    t = np.arange(int(secs * SR)) / SR
    ir = r.normal(0, 1, len(t)) * np.exp(-t / 0.9)
    ir = lfilter([0.3], [1, -0.72], ir)
    ir[: int(0.02 * SR)] = 0
    return ir / np.sqrt((ir ** 2).sum())


def musicbox_bed(path, total, plan, seed=7):
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
    for k, (t0, root, tones, bright) in enumerate(ch):
        t1 = ch[k + 1][0] if k + 1 < len(ch) else total + 1.5
        add(pad(tones, t1 - t0 + 1.4, rng, bright), t0 - (0 if k == 0 else 0.35), 0, 0.20)
        tt = np.arange(int(min(3.0, t1 - t0 + 0.5) * SR)) / SR
        add(np.sin(2 * np.pi * hz(root) * tt) * np.minimum(1, tt / 0.1) * np.exp(-tt / 2.0), t0, 0, 0.22)
    for i, (t0, m, vel) in enumerate(plan.get("melody", [])):
        add(box(m, vel), t0 + rng.normal(0, 0.004), 0.45 * np.sin(i * 1.7))
    for t0 in plan.get("clicks", []):
        add(click(), t0, 0.0, 0.25)
    air = lfilter([0.02], [1, -0.97], rng.normal(0, 1, n))
    air /= np.abs(air).max() + 1e-9
    L += air * 0.010
    R += air[::-1] * 0.010
    wl, wr = fftconvolve(L, hall(61))[:n], fftconvolve(R, hall(62))[:n]
    L, R = L * 0.74 + wl * 0.55, R * 0.74 + wr * 0.55
    b_, a_ = butter(2, 38 / (SR / 2), "high")
    L, R = lfilter(b_, a_, L), lfilter(b_, a_, R)
    m = int(total * SR)
    L, R = L[:m], R[:m]
    fi = int(0.1 * SR)
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
