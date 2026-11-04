"""Assemble the final reel: concat + crossfades + animated overlays + audio."""
import json
import subprocess
import sys

SEG = "/home/claude/reels/seg"
AS = "/home/claude/reels/assets"
OUT = sys.argv[1]
XF = 0.35      # crossfade between scenes
XF_END = 0.5   # crossfade into the end card


def vdur(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-count_frames",
                        "-show_entries", "stream=nb_read_frames", "-of", "json", path],
                       capture_output=True, text=True, check=True)
    return int(json.loads(r.stdout)["streams"][0]["nb_read_frames"]) / 30.0


names = ["A", "B", "C", "D", "E", "F", "G", "H", "END"]
dur = {n: vdur(f"{SEG}/{n}.mp4") for n in names}

# timeline: A,B,C hard-cut (continuous take), then crossfades
t = {}
t["A"] = 0.0
t["B"] = dur["A"]
t["C"] = t["B"] + dur["B"]
end_abc = t["C"] + dur["C"]
cursor = end_abc
for n in ["D", "E", "F", "G", "H"]:
    t[n] = cursor - XF
    cursor = t[n] + dur[n]
t["END"] = cursor - XF_END
total = t["END"] + dur["END"]

# overlays: (png, start, end, slide_px, fade_in, fade_out)
ov = [
    # first frame must already carry the hook (feed preview / first impression)
    ("watermark", 0.0, t["END"] + 0.25, 0, 0, 0.35),
    ("pill_oldin", 0.0, t["B"] + 0.05, 0, 0, 0.18),
    ("cap_hook", 0.0, t["C"] - 0.15, 0, 0, 0.25),
    ("pill_keyin", t["C"] + 0.10, t["D"] + 0.10, 22, 0.25, 0.22),
    ("cap_keyin", t["C"] + 0.20, t["D"] + 0.10, 28, 0.35, 0.22),
    ("cap_mato", t["D"] + 0.25, t["E"] + 0.20, 28, 0.35, 0.22),
    ("cap_tyul", t["E"] + 0.25, t["F"] + 0.20, 28, 0.35, 0.22),
    ("cap_karniz", t["F"] + 0.25, t["G"] + 0.20, 28, 0.35, 0.22),
    ("cap_shift", t["G"] + 0.25, t["H"] + 0.20, 28, 0.35, 0.22),
    ("cap_800", t["H"] + 0.25, t["END"] + 0.20, 28, 0.35, 0.22),
    ("endcard", t["END"] + 0.30, total, 40, 0.50, 0.0),
]

cmd = ["ffmpeg", "-v", "error", "-y"]
for n in names:
    cmd += ["-i", f"{SEG}/{n}.mp4"]
for png, st, en, *_ in ov:
    cmd += ["-loop", "1", "-framerate", "30", "-t", f"{en - st + 0.1:.3f}", "-i", f"{AS}/{png}.png"]

fc = []
for i, n in enumerate(names):
    fc.append(f"[{i}:v]fps=30,setpts=PTS-STARTPTS,settb=AVTB,format=yuv420p[v{n}]")
    fc.append(f"[{i}:a]aresample=48000,apad,atrim=0:{dur[n]:.4f},asetpts=PTS-STARTPTS[a{n}]")
fc.append("[vA][vB][vC]concat=n=3:v=1:a=0,settb=AVTB[vabc]")
fc.append("[aA][aB][aC]concat=n=3:v=0:a=1[aabc]")
prev_v, prev_a = "vabc", "aabc"
for n in ["D", "E", "F", "G", "H", "END"]:
    d = XF_END if n == "END" else XF
    fc.append(f"[{prev_v}][v{n}]xfade=transition=fade:duration={d}:offset={t[n]:.4f}[x{n}]")
    fc.append(f"[{prev_a}][a{n}]acrossfade=d={d}:c1=tri:c2=tri[y{n}]")
    prev_v, prev_a = f"x{n}", f"y{n}"

base = prev_v
for k, (png, st, en, slide, fi, fo) in enumerate(ov):
    idx = len(names) + k
    d = en - st
    chain = f"[{idx}:v]format=rgba,trim=duration={d:.4f}"
    if fi:
        chain += f",fade=t=in:st=0:d={fi}:alpha=1"
    if fo:
        chain += f",fade=t=out:st={max(0, d - fo):.4f}:d={fo}:alpha=1"
    chain += f",setpts=PTS-STARTPTS+{st:.4f}/TB[o{k}]"
    fc.append(chain)
    y = f"{slide}*pow(max(0\\,1-(t-{st:.4f})/0.45)\\,2)" if slide else "0"
    fc.append(f"[{base}][o{k}]overlay=x=0:y='{y}':eval=frame:eof_action=pass:"
              f"enable='between(t,{st:.4f},{en:.4f})'[b{k}]")
    base = f"b{k}"

fc.append(f"[{base}]format=yuv420p,trim=duration={total:.4f}[vout]")
fc.append(f"[{prev_a}]atrim=duration={total:.4f},alimiter=limit=0.85:level=disabled,"
          f"afade=t=out:st={total - 0.6:.4f}:d=0.6[aout]")

cmd += ["-filter_complex", ";".join(fc), "-map", "[vout]", "-map", "[aout]",
        "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-profile:v", "high", "-level", "4.2",
        "-pix_fmt", "yuv420p", "-r", "30", "-g", "60",
        "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", OUT]

print(json.dumps({"durations": dur, "starts": t, "total": total}, indent=1))
subprocess.run(cmd, check=True)
print("done", OUT)
