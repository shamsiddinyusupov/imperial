"""Split the 7-line narration, build the timeline from it and write timing.json + vo_track.wav.

python3 vo2_sync.py voiceover.mp3 [--breaks 4.6,9.7,...]   (times of the paragraph pauses in the source, optional)
Without an mp3 (python3 vo2_sync.py --dummy) it writes a timing.json from estimated line lengths, for previews.
"""
import json
import subprocess
import sys
import wave

import numpy as np

D = "/home/claude/reels/tong2"
SR = 48000
N_LINES = 7
EST = [1.4, 2.9, 3.9, 1.9, 4.3, 2.5, 4.3]          # estimated line lengths (s) for --dummy
LEAD = 0.25
GAP = [0.6, 0.35, 0.3, 0.4, 0.35, 0.45]            # pause after line i (hook gets a longer, dramatic pause)
TEMPO = 1.04                                        # the expressive take is slow; a touch faster keeps it under ~33 s
INNER_MAX = 0.55                                    # longest pause kept inside a line (the voice's own breaths)
MIN_BEAT = {3: 3.1}                                 # beat 4 (colour montage, index 3) needs room for 6 shots
TAIL = 1.1                                          # end card stays after the last word


def load(path):
    raw = subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-i", path, "-af", f"atempo={TEMPO}", "-ac", "1", "-ar", str(SR), "-f", "s16le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.int16).astype(np.float32) / 32768


def save(path, x):
    pcm = (np.clip(x, -1, 1) * 32767).astype(np.int16)
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


def silences(x, thr_db=-35):
    hop = int(0.01 * SR)
    env = np.sqrt(np.convolve(x ** 2, np.ones(hop) / hop, "same"))[::hop]
    v = env > 10 ** (thr_db / 20)
    runs, i = [], 0
    while i < len(v):
        if not v[i]:
            j = i
            while j < len(v) and not v[j]:
                j += 1
            runs.append((i * hop, j * hop))
            i = j
        else:
            i += 1
    first = int(np.argmax(v)) * hop
    last = (len(v) - int(np.argmax(v[::-1]))) * hop
    return runs, first, last


def tighten(seg, max_gap=0.4):
    runs, first, last = silences(seg)
    out, pos = [], 0
    for a, b in runs:
        if a <= first or b >= last or (b - a) / SR <= max_gap:
            continue
        keep = int(max_gap * SR)
        out.append(seg[pos: a + keep // 2])
        pos = b - keep // 2
    out.append(seg[pos:])
    return np.concatenate(out)


PARAS = [  # narration paragraphs (as sent to the voice), used to place the breaks
    "Ҳамма нарса... янги.",
    "Биттасидан ташқари. Деразадаги — эски жалюзи.",
    "Уни ташламанг. Плиссе ва комбо жалюзининг матосини — янгилаймиз.",
    "Сиз ёқтирган рангда. Сиз ёқтирган услубда.",
    "Матоси жойида, фақат кир бўлса? Ечиб, ювиб, қайта ўрнатамиз.",
    "Янгиланган хонага... янгиланган дераза.",
    "Империал. Эски жалюзингиз расмини, директга юборинг. Кўриб, айтиб берамиз.",
]


def choose_breaks(runs, first, last, n_lines):
    """Pick n-1 pauses: near the text-proportional boundary times, preferring long pauses (DP keeps order)."""
    cand = [r for r in runs if r[0] > first and r[1] < last and (r[1] - r[0]) / SR >= 0.18]
    w = [sum(ch.isalpha() for ch in p) for p in PARAS[:n_lines]]
    cum = np.cumsum(w)[:-1] / sum(w)
    exp_t = [first / SR + c * (last - first) / SR for c in cum]
    INF = 1e9
    K, M = len(exp_t), len(cand)
    cost = [[INF] * M for _ in range(K)]
    back = [[-1] * M for _ in range(K)]
    for k in range(K):
        for j in range(M):
            mid = (cand[j][0] + cand[j][1]) / 2 / SR
            plen = (cand[j][1] - cand[j][0]) / SR
            c = ((mid - exp_t[k]) / 0.9) ** 2 - 2.5 * plen
            if k == 0:
                cost[k][j] = c
            else:
                best, bi = INF, -1
                for i in range(j):
                    if cost[k - 1][i] < best:
                        best, bi = cost[k - 1][i], i
                if bi >= 0:
                    cost[k][j] = best + c
                    back[k][j] = bi
    j = int(np.argmin(cost[K - 1]))
    picks = []
    for k in range(K - 1, -1, -1):
        picks.append(cand[j])
        j = back[k][j]
    return sorted(picks)


def split_lines(x, n_lines, manual=None):
    runs, first, last = silences(x)
    if manual:      # pauses containing the given source times (seconds, before tempo)
        breaks = []
        for t in manual:
            ts = t / TEMPO * SR
            r = min((r for r in runs if r[0] > first and r[1] < last), key=lambda r: 0 if r[0] <= ts <= r[1] else min(abs(r[0] - ts), abs(r[1] - ts)))
            breaks.append(r)
        breaks = sorted(breaks)
    else:
        breaks = choose_breaks(runs, first, last, n_lines)
    pad = int(0.04 * SR)
    segs, s0 = [], first
    for a, b in breaks:
        segs.append(x[max(0, s0 - pad): min(len(x), a + pad)])
        s0 = b
    segs.append(x[max(0, s0 - pad): min(len(x), last + pad)])
    return [tighten(s, INNER_MAX) for s in segs], [(b - a) / SR for a, b in breaks]


def timeline(lens):
    starts, t = [], LEAD
    for i, L in enumerate(lens):
        starts.append(round(t, 3))
        if i < len(lens) - 1:
            t = t + L + GAP[i]
            beat = t - starts[i]
            if i in MIN_BEAT and beat < MIN_BEAT[i]:
                t = starts[i] + MIN_BEAT[i]
    total = round(starts[-1] + lens[-1] + TAIL, 2)
    return starts, total


def main():
    dummy = len(sys.argv) > 1 and sys.argv[1] == "--dummy"
    if dummy:
        lens, segs = EST, None
    else:
        x = load(sys.argv[1])
        manual = [float(v) for v in sys.argv[sys.argv.index("--breaks") + 1].split(",")] if "--breaks" in sys.argv else None
        segs, pauses = split_lines(x, N_LINES, manual)
        lens = [len(s) / SR for s in segs]
        print("pauses used as breaks:", [round(p, 2) for p in pauses])
    starts, total = timeline(lens)
    beats = [[round(max(0, s - 0.15), 3), round((starts[i + 1] - 0.15) if i + 1 < len(starts) else total, 3)] for i, s in enumerate(starts)]
    beats[0][0] = 0.0
    tim = {"total": total, "lines": [{"start": s, "len": round(L, 3)} for s, L in zip(starts, lens)], "beats": beats, "dummy": dummy}
    json.dump(tim, open(f"{D}/timing.json", "w"), indent=1)
    for i, (s, L) in enumerate(zip(starts, lens)):
        print(f"line {i + 1}: start {s:6.2f}  len {L:5.2f}  beat {beats[i][0]:6.2f}–{beats[i][1]:6.2f}")
    print("total", total)
    if segs:
        track = np.zeros(int((total + 0.5) * SR), np.float32)
        for s, seg in zip(starts, segs):
            i = int(s * SR)
            j = min(len(track), i + len(seg))
            n = j - i
            fade = np.minimum(1, np.arange(n) / (0.01 * SR)) * np.minimum(1, (n - np.arange(n)) / (0.03 * SR))
            track[i:j] += seg[:n] * fade
        save(f"{D}/vo_track.wav", track)


if __name__ == "__main__":
    main()
