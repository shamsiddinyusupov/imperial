"""Assemble reel #2: VHS 'before' -> tape glitch -> clean 4K 'after' -> hi-tech end card."""
import json
import subprocess
import sys

SEG = "/home/claude/reels/v2/seg"
AS = "/home/claude/reels/v2/assets"
HT = "/home/claude/reels/assets_ht"
OUT = sys.argv[1]
FONT_MONO_B = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
XF_WHITE, XF, XF_END = 0.25, 0.30, 0.5
REG_Y = 1040


def vdur(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-count_frames",
                        "-show_entries", "stream=nb_read_frames", "-of", "json", path],
                       capture_output=True, text=True, check=True)
    return int(json.loads(r.stdout)["streams"][0]["nb_read_frames"]) / 30.0


names = ["V1", "V2", "V3", "G", "K1", "K2", "K3", "K4", "G2", "END"]
dur = {n: vdur(f"{SEG}/{n}.mp4") for n in names}
t = {"V1": 0.0}
t["V2"] = dur["V1"]
t["V3"] = t["V2"] + dur["V2"]
t["G"] = t["V3"] + dur["V3"]
end_vhs = t["G"] + dur["G"]
t["K1"] = end_vhs - XF_WHITE
cur = t["K1"] + dur["K1"]
for n in ["K2", "K3", "K4"]:
    t[n] = cur - XF
    cur = t[n] + dur[n]
t["G2"] = cur                      # hard cut into the "rewind" tear
t["END"] = t["G2"] + dur["G2"]     # hard cut onto the VCR blue menu
total = t["END"] + dur["END"]

# overlays: (kind, src, start, end, y, fade_in, fade_out, y_expr)
band_y = "mod(t*420\\,2300)-220"
ov = [
    ("still", f"{AS}/vhs_scan.png", 0.0, t["G"], 0, 0, 0, None),
    ("still", f"{AS}/vhs_band.png", 0.0, end_vhs, 0, 0, 0, band_y),
    ("still", f"{AS}/vhs_osd.png", 0.0, t["G"], 0, 0, 0, None),
    ("still", f"{AS}/vhs_cap_1.png", 0.0, t["V2"], 0, 0, 0, None),
    ("still", f"{AS}/vhs_cap_2.png", t["V2"], t["V3"], 0, 0, 0, None),
    ("still", f"{AS}/vhs_cap_3.png", t["V3"], t["G"], 0, 0, 0, None),
    ("still", f"{AS}/glitch_4k.png", t["G"] + 0.05, t["K1"] + 0.45, 0, 0, 0.2, None),
    ("still", f"{HT}/scrim.png", t["K1"], t["G2"], 0, 0.25, 0, None),
    ("still", f"{HT}/hud.png", t["K1"], t["G2"], 0, 0.25, 0, None),
    ("still", f"{AS}/badge_4k.png", t["K1"], t["G2"], 0, 0.25, 0, None),
    ("seq", f"{AS}/cap_k1", t["K1"] + 0.30, t["K2"] + 0.12, REG_Y, 0, 0.2, None),
    ("seq", f"{AS}/cap_k2", t["K2"] + 0.22, t["K3"] + 0.12, REG_Y, 0, 0.2, None),
    ("seq", f"{AS}/cap_k3", t["K3"] + 0.22, t["K4"] + 0.12, REG_Y, 0, 0.2, None),
    ("seq", f"{AS}/cap_k4", t["K4"] + 0.22, t["G2"], REG_Y, 0, 0, None),
    ("still", f"{AS}/vhs_band.png", t["G2"], total, 0, 0, 0, band_y),
    ("still", f"{AS}/vhs_scan.png", t["END"], total, 0, 0, 0, None),
    ("seq", f"{AS}/endmenu", t["END"], total, 0, 0, 0, None),
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
    fc.append(f"[{i}:a]aresample=48000,aformat=channel_layouts=stereo,apad,atrim=0:{dur[n]:.4f},"
              f"asetpts=PTS-STARTPTS[a{n}]")
fc.append("[vV1][vV2][vV3][vG]concat=n=4:v=1:a=0,settb=AVTB[vvhs]")
fc.append("[aV1][aV2][aV3][aG]concat=n=4:v=0:a=1[avhs]")
pv, pa = "vvhs", "avhs"
for n in ["K1", "K2", "K3", "K4"]:
    tr, d = ("fadewhite", XF_WHITE) if n == "K1" else ("smoothleft", XF)
    fc.append(f"[{pv}][v{n}]xfade=transition={tr}:duration={d}:offset={t[n]:.4f}[x{n}]")
    fc.append(f"[{pa}][a{n}]acrossfade=d={d}:c1=tri:c2=tri[y{n}]")
    pv, pa = f"x{n}", f"y{n}"
fc.append(f"[{pv}][vG2][vEND]concat=n=3:v=1:a=0,settb=AVTB[xtail]")
fc.append(f"[{pa}][aG2][aEND]concat=n=3:v=0:a=1[ytail]")
pv, pa = "xtail", "ytail"

# running VHS tape counter (drawn on the composite timeline so it never resets between cuts)
fc.append(f"[{pv}]drawtext=fontfile={FONT_MONO_B}:text='SP %{{pts\\:hms}}':x=80:y=316:fontsize=34:"
          f"fontcolor=white:borderw=3:bordercolor=black@0.85:enable='lt(t,{t['G']:.4f})'[vtc]")
base = "vtc"
for k, (kind, src, st, en, y, fi, fo, yexpr) in enumerate(ov):
    idx = len(names) + k
    d = en - st
    ch = f"[{idx}:v]format=rgba"
    if kind == "seq":
        ch += f",tpad=stop_mode=clone:stop_duration={d + 0.2:.3f}"
    ch += f",trim=duration={d:.4f}"
    if fi:
        ch += f",fade=t=in:st=0:d={fi}:alpha=1"
    if fo:
        ch += f",fade=t=out:st={max(0, d - fo):.4f}:d={fo}:alpha=1"
    ch += f",setpts=PTS-STARTPTS+{st:.4f}/TB[o{k}]"
    fc.append(ch)
    yy = f"'{yexpr}'" if yexpr else str(y)
    fc.append(f"[{base}][o{k}]overlay=x=0:y={yy}:eval=frame:eof_action=pass:"
              f"enable='between(t,{st:.4f},{en:.4f})'[b{k}]")
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
