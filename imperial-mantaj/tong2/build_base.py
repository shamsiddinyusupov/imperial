"""Assemble base.mp4 (picture only) from the graded cuts in seg/, timed by timing.json.

Beats: 0 renovated room · 1–2 one continuous close-up→wide shot that is black-and-white until the
"we renew the fabric" line and then fades into colour · 3 colour montage · 4 hand + sunlit fabric ·
5 wide window · 6 end card background.
"""
import json
import subprocess

D = "/home/claude/reels/tong2"
X = 0.3                       # dissolve length between beats
E = ["-c:v", "libx264", "-preset", "fast", "-crf", "14", "-pix_fmt", "yuv420p", "-r", "30"]
tim = json.load(open(f"{D}/timing.json"))
B = tim["beats"]
L = tim["lines"]
TOTAL = tim["total"]


def run(args):
    subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y"] + args, check=True)


def dur(p):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p],
                                capture_output=True, text=True).stdout)


def piece(name, src, length, vf="null", start=0.0):
    """Trim src from start to `length` seconds (freeze the last frame if the source is short)."""
    have = dur(f"{D}/seg/{src}.mp4") - start
    slow = 1.0
    if have < length:                      # short source: slow it down a little (max 0.8x), freeze only the rest
        slow = max(0.8, have / length)
        vf = f"setpts=PTS/{slow:.4f},fps=30,{vf}"
    pad = max(0.0, length - have / slow + 0.05)
    f = f"{vf},tpad=stop_mode=clone:stop_duration={pad:.3f}" if pad > 0 else vf
    run(["-ss", f"{start:.3f}", "-i", f"{D}/seg/{src}.mp4", "-t", f"{length:.3f}", "-vf", f + ",setpts=PTS-STARTPTS"] + E + [f"{D}/seg/P_{name}.mp4"])


blen = [b[1] - b[0] for b in B]

# P0: renovated room
piece("0", "R1", blen[0] + X / 2)

# P1: beats 1+2. The plisse is black-and-white ("the old blind") until the word "Plisse", then colour pops in;
# on "kombo" it cuts to kombo stripes, on "yangilaymiz" to a kombo window in a renovated room.
CH = tim["chunks"][2]                          # line 3: "Uni tashlamang" | "Plisse va kombo … matosini" | "yangilaymiz"
p0 = B[1][0] - X / 2                           # P1 starts here on the output timeline
plisse_on = CH[1][0]
kombo_on = CH[1][0] + 0.27 * (CH[1][1] - CH[1][0])
yangi_on = CH[2][0]
c0 = plisse_on - p0
c1 = c0 + 0.6
k = f"clip((t-{c0:.3f})/{c1 - c0:.3f},0,1)"
bw = (f"hue=s='{k}',eq=eval=frame:brightness='-0.05*(1-{k})':contrast='1+0.08*(1-{k})',"
      f"noise=alls=7:allf=t")
piece("1a", "R2", kombo_on - p0, bw)
piece("1b", "K1", yangi_on - kombo_on)
piece("1c", "K2", B[3][0] + X / 2 - yangi_on, start=0.3)
with open(f"{D}/seg/p1.txt", "w") as f:
    f.write("file 'P_1a.mp4'\nfile 'P_1b.mp4'\nfile 'P_1c.mp4'\n")
run(["-f", "concat", "-safe", "0", "-i", f"{D}/seg/p1.txt"] + E + [f"{D}/seg/P_1.mp4"])

# P3: colour montage, six equal hard cuts
mont = ["M1", "M2", "M3", "M4", "M5", "M6"]
m_len = blen[3] + X
each = m_len / len(mont)
for i, m in enumerate(mont):
    piece(f"m{i}", m, each + (0.02 if i == len(mont) - 1 else 0), start=0.15)
with open(f"{D}/seg/mont.txt", "w") as f:
    f.write("".join(f"file 'P_m{i}.mp4'\n" for i in range(len(mont))))
run(["-f", "concat", "-safe", "0", "-i", f"{D}/seg/mont.txt"] + E + [f"{D}/seg/P_3.mp4"])

# P4: hand (H1) then sunlit fabric (H2) with a short internal dissolve
h_len = blen[4] + X
h1 = h_len * 0.56
h2 = h_len - h1 + 0.25
piece("h1", "H1", h1, start=0.4)
piece("h2", "H2", h2)
run(["-i", f"{D}/seg/P_h1.mp4", "-i", f"{D}/seg/P_h2.mp4", "-filter_complex",
     f"[0:v][1:v]xfade=transition=fade:duration=0.25:offset={h1 - 0.25:.3f},format=yuv420p[v]", "-map", "[v]"] + E + [f"{D}/seg/P_4.mp4"])

# P5: wide window; P6: end card background
piece("5", "W1", blen[5] + X)
piece("6", "W2", blen[6] + X / 2 + 0.2, start=0.4)

# chain with dissolves at each beat boundary (beats 1|2 are one piece)
pieces = ["P_0", "P_1", "P_3", "P_4", "P_5", "P_6"]
bounds = [B[1][0], B[3][0], B[4][0], B[5][0], B[6][0]]
inputs = sum([["-i", f"{D}/seg/{p}.mp4"] for p in pieces], [])
fc, last = [], "[0:v]"
for i, b in enumerate(bounds):
    out = f"[x{i}]"
    fc.append(f"{last}[{i + 1}:v]xfade=transition=fade:duration={X}:offset={b - X / 2:.3f}{out}")
    last = out
fc.append(f"{last}trim=duration={TOTAL:.3f},format=yuv420p[v]")
run(inputs + ["-filter_complex", ";".join(fc), "-map", "[v]"] + E + [f"{D}/base.mp4"])
print("base.mp4", round(dur(f"{D}/base.mp4"), 2), "target", TOTAL)
