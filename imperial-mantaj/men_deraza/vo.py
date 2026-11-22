"""Voice for «Men — derazangizman» (Classic, owner 22.11): Daniel take from the owner's screen recording.
Cut the speech into chunks at the pauses, speed up slightly, re-join with set gaps, write vo/voice.wav + vo/timing.json
(start/end of every chunk on the voice timeline, which starts at LEAD)."""
import json
import subprocess

import numpy as np
import wave

D = "/home/claude/reels/deraza"
SR = 48000
LEAD = 0.35
TEMPO = 1.06
# chunks from silencedetect (-38 dB, 0.25 s) on vo/rec.wav
CH = [(0.93, 3.42), (3.98, 6.10), (6.45, 7.01), (7.38, 7.86), (8.20, 8.74), (9.35, 11.01), (11.29, 12.49),
      (13.15, 14.32), (14.98, 17.50), (18.03, 20.37), (20.76, 21.35), (21.97, 22.94), (23.59, 25.35), (25.63, 26.26),
      (26.95, 30.27), (31.04, 33.40), (33.84, 35.95), (36.36, 37.61)]
GAP = [0.35, 0.18, 0.16, 0.16, 0.40, 0.45, 0.42, 0.40, 0.35, 0.18, 0.35, 0.35, 0.12, 0.45, 0.50, 0.25, 0.18]
PRE, POST = 0.05, 0.10


def main():
    subprocess.run(f"ffmpeg -nostdin -v error -y -i {D}/vo/rec.wav -af \"highpass=f=70,atempo={TEMPO}\" -ar {SR} "
                   f"-ac 1 {D}/vo/rec_t.wav", shell=True, check=True)
    w = wave.open(f"{D}/vo/rec_t.wav")
    a = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
    out, tim, t = [np.zeros(int(LEAD * SR))], [], LEAD
    for k, (s, e) in enumerate(CH):
        s2, e2 = (s - PRE) / TEMPO, (e + POST) / TEMPO
        seg = a[int(s2 * SR):int(e2 * SR)].copy()
        f = int(0.012 * SR)
        seg[:f] *= np.linspace(0, 1, f)
        seg[-f:] *= np.linspace(1, 0, f)
        tim.append(dict(k=k, start=round(t + PRE / TEMPO, 3), end=round(t + len(seg) / SR - POST / TEMPO, 3)))
        out.append(seg)
        t += len(seg) / SR
        if k < len(GAP):
            out.append(np.zeros(int(GAP[k] * SR)))
            t += GAP[k]
    v = np.concatenate(out)
    with wave.open(f"{D}/vo/voice.wav", "wb") as o:
        o.setnchannels(1)
        o.setsampwidth(2)
        o.setframerate(SR)
        o.writeframes((np.clip(v, -1, 1) * 32767).astype(np.int16).tobytes())
    json.dump(tim, open(f"{D}/vo/timing.json", "w"), indent=0)
    print("voice", round(len(v) / SR, 2), [(x["start"], x["end"]) for x in tim])


if __name__ == "__main__":
    main()
