"""UI sound for the VCR menu end screen (5.0 s): typing ticks, cursor beep, select chirps."""
import sys
import wave
import numpy as np

SR = 48000
DUR = 5.0
out = np.zeros(int(SR * DUR))


def tone(t0, f, d, a, shape="sine"):
    n = int(SR * d)
    tt = np.arange(n) / SR
    w = np.sin(2 * np.pi * f * tt) if shape == "sine" else np.sign(np.sin(2 * np.pi * f * tt)) * 0.6
    env = np.minimum(1, tt / 0.004) * np.exp(-tt / (d * 0.45))
    i0 = int(SR * t0)
    out[i0:i0 + n] += a * w * env


def ticks(f0, f1, step=2):
    for f in range(f0, f1, step):
        tone(f / 30, 2400, 0.012, 0.05, "square")


ticks(6, 31)            # question typing
tone(46 / 30, 880, 0.08, 0.22)        # cursor HA -> YO'Q
tone(60 / 30, 1320, 0.09, 0.24)       # select
tone(68 / 30, 1320, 0.07, 0.2)        # confirm chirp (two-tone up)
tone(68 / 30 + 0.08, 1760, 0.12, 0.22)
ticks(76, 101)          # CTA typing
ticks(108, 123)

out = np.clip(out, -0.95, 0.95)
pcm = (out * 32767).astype(np.int16)
stereo = np.repeat(pcm[:, None], 2, axis=1)
with wave.open(sys.argv[1], "wb") as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(stereo.tobytes())
print("ok", sys.argv[1])
