"""Fit the reel to the voiceover.

python3 sync.py voiceover.mp3 [tempo]
 1. splits the narration into 7 paragraphs (hook, Q1..Q5, CTA) at the 6 longest pauses
 2. finds the answer start inside each Q (pause nearest to where the question ends, by text share),
    the "Qiynalsangiz" start in Q2 and the CTA anchors
 3. writes timing.json (scene lengths + anchors) and vo_track.wav (voice placed on the timeline)
"""
import json
import re
import subprocess
import sys
import wave

import numpy as np

D = "/home/claude/reels/faq"
SRC = sys.argv[1]
TEMPO = float(sys.argv[2]) if len(sys.argv) > 2 else 1.0
SR = 48000
XF, LEAD, GAP = 0.3, 0.3, 0.55

PARAS = [l.strip() for l in open(f"{D}/vo/script.txt", encoding="utf-8").read().split("\n\n") if l.strip()]
assert len(PARAS) == 7

# analyse the original-speed voice (pauses are clearer); place the tempo-adjusted one
af = f"atempo={TEMPO}," if TEMPO != 1.0 else ""
for name, filt in (("vo1", f"aresample={SR}"), ("vo", f"{af}aresample={SR}")):
    subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-i", SRC, "-af", filt, "-ac", "1",
                    f"{D}/vo/{name}.wav"], check=True)


def load(name):
    w = wave.open(f"{D}/vo/{name}.wav")
    return np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32767


x = load("vo1")
xt = load("vo")
dur = len(x) / SR

# frame energy -> silence intervals
hop = int(0.01 * SR)
e = np.sqrt(np.convolve(x ** 2, np.ones(hop * 2) / (hop * 2), "same")[::hop] + 1e-12)
db = 20 * np.log10(e)
thr = max(-45.0, np.percentile(db, 90) - 30)
quiet = db < thr
sil = []
i = 0
while i < len(quiet):
    if quiet[i]:
        j = i
        while j < len(quiet) and quiet[j]:
            j += 1
        sil.append((i * 0.01, j * 0.01))
        i = j
    else:
        i += 1
speech_start = next(b for a, b in sil if a < 0.05) if sil and sil[0][0] < 0.05 else 0.0
speech_end = sil[-1][0] if sil and sil[-1][1] >= dur - 0.05 else dur
inner = [(a, b) for a, b in sil if a > speech_start + 0.05 and b < speech_end - 0.05 and b - a >= 0.12]

# 6 paragraph breaks = longest pauses, but keep them in proportion to text length
chars = np.cumsum([len(p) for p in PARAS])
exp_breaks = speech_start + (speech_end - speech_start) * chars[:-1] / chars[-1]
cands = sorted(inner, key=lambda s: -(s[1] - s[0]))[:14]
breaks = []
for eb in exp_breaks:
    best = min((c for c in cands if c not in breaks), key=lambda c: abs((c[0] + c[1]) / 2 - eb) - 2.0 * (c[1] - c[0]))
    breaks.append(best)
breaks.sort()
bounds = [speech_start] + [v for a, b in breaks for v in (a, b)] + [speech_end]
chunks = [(bounds[2 * k], bounds[2 * k + 1]) for k in range(7)]


def anchor(k, text_before):
    """time (relative to chunk start) of the pause closest to where `text_before` ends."""
    a0, a1 = chunks[k]
    share = len(text_before) / len(PARAS[k])
    target = a0 + (a1 - a0) * share
    ps = [(a, b) for a, b in inner if a0 < a < a1]
    if not ps:
        return target - a0
    a, b = min(ps, key=lambda s: abs((s[0] + s[1]) / 2 - target))
    return b - a0


ans = []
for q in range(5):
    k = q + 1
    qtext = PARAS[k][: PARAS[k].index("?") + 1]
    ans.append(anchor(k, qtext))
help_rel = anchor(2, PARAS[2][: PARAS[2].index("Qiynalsangiz")])
cta = PARAS[6]
cta_q = anchor(6, cta[: cta.index("?") + 1])
cta_dm = anchor(6, cta[: cta.index("narxlarni")])
cta_foot = anchor(6, cta[: cta.index("Yoki")])

# move everything to the tempo-adjusted time base
chunks = [(a / TEMPO, b / TEMPO) for a, b in chunks]
ans = [a / TEMPO for a in ans]
help_rel, cta_q, cta_dm, cta_foot = (v / TEMPO for v in (help_rel, cta_q, cta_dm, cta_foot))
x = xt
lens = [b - a for a, b in chunks]
dur_s = [0.25 + lens[0] + GAP]
for k in range(1, 6):
    dur_s.append(LEAD + lens[k] + GAP)
dur_s.append(LEAD + lens[6] + 1.9)
start = [0.0]
for d in dur_s[:-1]:
    start.append(start[-1] + d - XF)
voice_at = [0.25] + [start[k] + LEAD for k in range(1, 7)]

tim = {
    "dur": dur_s,
    "ans": [LEAD + a - 0.1 for a in ans],
    "help": LEAD + help_rel - 0.1,
    "cta": {"type": LEAD + cta_q, "dm": LEAD + cta_dm, "foot": LEAD + cta_foot - 0.05},
    "voice_at": voice_at,
    "chunks": chunks,
}
json.dump(tim, open(f"{D}/timing.json", "w"), indent=1)

total = start[-1] + dur_s[-1]
track = np.zeros(int((total + 1) * SR), np.float32)
for k, (a, b) in enumerate(chunks):
    seg = x[int(a * SR): int(b * SR)].copy()
    f = int(0.012 * SR)
    seg[:f] *= np.linspace(0, 1, f)
    seg[-f:] *= np.linspace(1, 0, f)
    i0 = int(voice_at[k] * SR)
    track[i0:i0 + len(seg)] += seg
track = track[: int(total * SR)]
with wave.open(f"{D}/vo/vo_track.wav", "wb") as o:
    o.setnchannels(1)
    o.setsampwidth(2)
    o.setframerate(SR)
    o.writeframes((np.clip(track, -1, 1) * 32767).astype(np.int16).tobytes())

print(f"voice {dur:.2f}s (tempo {TEMPO}) | speech {speech_start:.2f}-{speech_end:.2f} | reel {total:.2f}s")
for k, (a, b) in enumerate(chunks):
    print(f" P{k}: {a:6.2f}-{b:6.2f} ({b - a:5.2f}s)  scene {dur_s[k]:5.2f}s  | {PARAS[k][:42]}")
print(" answers at", [round(v, 2) for v in tim["ans"]], "help", round(tim["help"], 2), "cta", {k: round(v, 2) for k, v in tim["cta"].items()})
