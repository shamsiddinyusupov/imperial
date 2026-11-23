"""Voice for «Oddiy pardalardan charchadingizmi?» (Classic dikey, owner 23.11, Daniel eleven_v3).
a1 = full take; a0 = re-recorded sentence 2 («dizayni» instead of «ko‘rinishi», owner approved 23.11).
Cut chunks at the pauses, speed up slightly, re-join with set gaps -> voice.wav + timing.json."""
import json
import subprocess
import wave

import numpy as np

D = "/home/claude/reels/dikey7/vo"
SR = 48000
LEAD = 0.35
TEMPO = 1.07
PRE, POST = 0.04, 0.10
# source, start, end (s, at 1.0x), gap after (s, final timeline), paragraph id
CH = [("a1", 0.000, 2.195, 0.45, "p1"),
      ("a0", 0.000, 3.452, 0.30, "p2"), ("a0", 4.011, 5.231, 0.28, "p2"), ("a0", 5.762, 6.772, 0.24, "p2"),
      ("a0", 7.175, 10.849, 0.45, "p2"),
      ("a1", 14.445, 14.922, 0.42, "p3"), ("a1", 15.552, 16.730, 0.55, "p3"),
      ("a1", 17.350, 20.745, 0.40, "p4"),
      ("a1", 21.396, 27.157, 0.45, "p5"),
      ("a1", 27.834, 29.681, 0.40, "p6"),
      ("a1", 30.609, 34.790, 0.50, "p7"),
      ("a1", 35.686, 37.139, 0.40, "p8"), ("a1", 37.877, 40.061, 0.25, "p8"), ("a1", 40.387, 43.367, 0.0, "p8")]


def load(name):
    subprocess.run(f"ffmpeg -nostdin -v error -y -i {D}/{name}.wav -af \"highpass=f=70,atempo={TEMPO}\" -ar {SR} -ac 1 "
                   f"{D}/{name}_t.wav", shell=True, check=True)
    w = wave.open(f"{D}/{name}_t.wav")
    return np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768


def main():
    src = {k: load(k) for k in ("a0", "a1")}
    out, tim, t = [np.zeros(int(LEAD * SR))], [], LEAD
    for k, (s_, s, e, gap, pid) in enumerate(CH):
        pre = min(PRE, s)
        s2, e2 = (s - pre) / TEMPO, (e + POST) / TEMPO
        seg = src[s_][int(s2 * SR):int(e2 * SR)].copy()
        f = int(0.012 * SR)
        seg[:f] *= np.linspace(0, 1, f)
        seg[-f:] *= np.linspace(1, 0, f)
        tim.append(dict(k=k, p=pid, start=round(t + pre / TEMPO, 3), end=round(t + len(seg) / SR - POST / TEMPO, 3)))
        out.append(seg)
        t += len(seg) / SR
        if gap:
            out.append(np.zeros(int(gap * SR)))
            t += gap
    v = np.concatenate(out)
    with wave.open(f"{D}/voice.wav", "wb") as o:
        o.setnchannels(1)
        o.setsampwidth(2)
        o.setframerate(SR)
        o.writeframes((np.clip(v, -1, 1) * 32767).astype(np.int16).tobytes())
    json.dump(tim, open(f"{D}/timing.json", "w"), indent=0)
    print("voice", round(len(v) / SR, 2))
    for x in tim:
        print(x["p"], x["start"], x["end"])


if __name__ == "__main__":
    main()
