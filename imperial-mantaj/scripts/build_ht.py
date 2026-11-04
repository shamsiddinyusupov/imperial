"""Assemble the hi-tech variant: no logo, lower captions, animated reveals, sliding transitions."""
import json
import subprocess
import sys

SEG = "/home/claude/reels/seg_ht"
AS = "/home/claude/reels/assets_ht"
OUT = sys.argv[1]
XF = 0.32
XF_END = 0.5
REG_Y = 1040
REVEAL = 20  # frames in each caption reveal sequence
END_FRAMES = 40


def vdur(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-count_frames",
                        "-show_entries", "stream=nb_read_frames", "-of", "json", path],
                       capture_output=True, text=True, check=True)
    return int(json.loads(r.stdout)["streams"][0]["nb_read_frames"]) / 30.0


names = ["A", "B", "C", "D", "E", "F", "G", "H", "END"]
dur = {n: vdur(f"{SEG}/{n}.mp4") for n in names}
t = {"A": 0.0, "B": dur["A"]}
t["C"] = t["B"] + dur["B"]
cursor = t["C"] + dur["C"]
for n in ["D", "E", "F", "G", "H"]:
    t[n] = cursor - XF
    cursor = t[n] + dur[n]
t["END"] = cursor - XF_END
total = t["END"] + dur["END"]

# (kind, src, start, end, y, fade_out)   kind: still | seq
ov = [
    ("still", f"{AS}/scrim.png", 0.0, total, 0, 0),
    ("still", f"{AS}/hud.png", 0.0, total, 0, 0),
    ("still", f"{AS}/cap_hook/000.png", 0.0, t["C"] - 0.12, REG_Y, 0.22),
    ("seq", f"{AS}/cap_keyin", t["C"] + 0.10, t["D"] + 0.12, REG_Y, 0.2),
    ("seq", f"{AS}/cap_mato", t["D"] + 0.22, t["E"] + 0.14, REG_Y, 0.2),
    ("seq", f"{AS}/cap_tyul", t["E"] + 0.22, t["F"] + 0.14, REG_Y, 0.2),
    ("seq", f"{AS}/cap_karniz", t["F"] + 0.22, t["G"] + 0.14, REG_Y, 0.2),
    ("seq", f"{AS}/cap_shift", t["G"] + 0.22, t["H"] + 0.14, REG_Y, 0.2),
    ("seq", f"{AS}/cap_800", t["H"] + 0.22, t["END"] + 0.2, REG_Y, 0.2),
    ("seq", f"{AS}/end", t["END"] + 0.25, total, 0, 0),
]

cmd = ["ffmpeg", "-v", "error", "-y"]
for n in names:
    cmd += ["-i", f"{SEG}/{n}.mp4"]
for kind, src, st, en, *_ in ov:
    if kind == "still":
        cmd += ["-loop", "1", "-framerate", "30", "-t", f"{en - st + 0.1:.3f}", "-i", src]
    else:
        cmd += ["-framerate", "30", "-i", f"{src}/%03d.png"]

fc = []
for i, n in enumerate(names):
    fc.append(f"[{i}:v]fps=30,setpts=PTS-STARTPTS,settb=AVTB,format=yuv420p[v{n}]")
    fc.append(f"[{i}:a]aresample=48000,apad,atrim=0:{dur[n]:.4f},asetpts=PTS-STARTPTS[a{n}]")
fc.append("[vA][vB][vC]concat=n=3:v=1:a=0,settb=AVTB[vabc]")
fc.append("[aA][aB][aC]concat=n=3:v=0:a=1[aabc]")
pv, pa = "vabc", "aabc"
for n in ["D", "E", "F", "G", "H", "END"]:
    tr, d = ("fade", XF_END) if n == "END" else ("smoothleft", XF)
    fc.append(f"[{pv}][v{n}]xfade=transition={tr}:duration={d}:offset={t[n]:.4f}[x{n}]")
    fc.append(f"[{pa}][a{n}]acrossfade=d={d}:c1=tri:c2=tri[y{n}]")
    pv, pa = f"x{n}", f"y{n}"

base = pv
for k, (kind, src, st, en, y, fo) in enumerate(ov):
    idx = len(names) + k
    d = en - st
    ch = f"[{idx}:v]format=rgba"
    if kind == "seq":
        ch += f",tpad=stop_mode=clone:stop_duration={d + 0.2:.3f}"
    ch += f",trim=duration={d:.4f}"
    if fo:
        ch += f",fade=t=out:st={max(0, d - fo):.4f}:d={fo}:alpha=1"
    ch += f",setpts=PTS-STARTPTS+{st:.4f}/TB[o{k}]"
    fc.append(ch)
    fc.append(f"[{base}][o{k}]overlay=x=0:y={y}:eof_action=pass:enable='between(t,{st:.4f},{en:.4f})'[b{k}]")
    base = f"b{k}"

fc.append(f"[{base}]format=yuv420p,trim=duration={total:.4f}[vout]")
fc.append(f"[{pa}]atrim=duration={total:.4f},alimiter=limit=0.85:level=disabled,"
          f"afade=t=out:st={total - 0.6:.4f}:d=0.6[aout]")

cmd += ["-filter_complex", ";".join(fc), "-map", "[vout]", "-map", "[aout]",
        "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-profile:v", "high", "-level", "4.2",
        "-pix_fmt", "yuv420p", "-r", "30", "-g", "60",
        "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", OUT]
print(json.dumps({"starts": t, "total": total}, indent=1))
subprocess.run(cmd, check=True)
print("done", OUT)
