"""Place the Uzbek narration lines on the premium mosquito-net Reel's sections and mix.

python3 vo_sync.py voiceover.mp3
Splits the narration at its 6 longest pauses (7 lines), puts each line at its section start,
speeds a line up (max 1.15x) only if it would overrun its slot, then mixes under/over sound_prem.wav.
"""
import subprocess
import sys
import wave

import numpy as np

D = "/home/claude/reels/setka"
SR = 48000
TOTAL = 30.0
# (start, latest end) per line: hook over the buzz (must end before the cut at 4.0), five sections, end card
SLOTS = [(0.45, 3.85), (5.2, 8.95), (9.2, 12.95), (13.2, 16.95), (17.2, 20.95), (21.2, 24.95), (25.4, 29.7)]


def load(path):
    raw = subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-i", path, "-ac", "1", "-ar", str(SR), "-f", "s16le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.int16).astype(np.float32) / 32768


def save(path, x, ch=1):
    pcm = (np.clip(x, -1, 1) * 32767).astype(np.int16)
    with wave.open(path, "wb") as w:
        w.setnchannels(ch)
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
    """Shorten long pauses inside one line (a colon or dash read as a long breath)."""
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


def split_lines(x, n_lines):
    runs, first, last = silences(x)
    breaks = [r for r in runs if r[0] > first and r[1] < last and (r[1] - r[0]) / SR >= 0.8]
    pad = int(0.04 * SR)
    segs, s0 = [], first
    for a, b in breaks:
        segs.append([max(0, s0 - pad), min(len(x), a + pad)])
        s0 = b
    segs.append([max(0, s0 - pad), min(len(x), last + pad)])
    while len(segs) > n_lines:          # a colon read as a paragraph break: join the shortest piece with the next one
        k = min(range(len(segs) - 1), key=lambda i: segs[i][1] - segs[i][0])
        segs[k] = [segs[k][0], segs[k + 1][1]]
        del segs[k + 1]
    return [tighten(x[a:b]) for a, b in segs]


def tempo(seg, k):
    if k <= 1.001:
        return seg
    save(f"{D}/_t_in.wav", seg)
    subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-i", f"{D}/_t_in.wav", "-af", f"atempo={k:.3f}", f"{D}/_t_out.wav"], check=True)
    return load(f"{D}/_t_out.wav")


def main(vo_path):
    x = load(vo_path)
    lines = split_lines(x, len(SLOTS))
    track = np.zeros(int(TOTAL * SR), np.float32)
    report = []
    for (t0, t1), seg in zip(SLOTS, lines):
        dur = len(seg) / SR
        k = min(1.12, max(1.0, dur / (t1 - t0)))
        seg = tempo(seg, k)
        i = int(t0 * SR)
        j = min(len(track), i + len(seg))
        fade = np.minimum(1, np.arange(j - i) / (0.01 * SR)) * np.minimum(1, (j - i - np.arange(j - i)) / (0.03 * SR))
        track[i:j] += seg[: j - i] * fade
        report.append((t0, round(dur, 2), round(k, 3), round(t0 + len(seg) / SR, 2), t1))
    save(f"{D}/vo_track.wav", track)
    for r in report:
        print("start %.2f  len %.2f  tempo %.3f  ends %.2f  (limit %.2f)" % r)


if __name__ == "__main__":
    main(sys.argv[1])
