"""Cut the scene clips to the lengths the voiceover needs.

Usage: python3 prep_vo.py d0,d1,d2,d3,d4,d5,d6   (seconds per scene, before 0.3 s cross-fades)
Each scene is a list of (clip, start, max_len) pieces; if the pieces are shorter than the target,
the scene is slowed down (up to 1.35x) and then held on its last frame.
"""
import subprocess
import sys

A = "/mnt/user-data/attachments/29c18e40-edfd-55e7-a3e1-da5539b3418b"
U = "/mnt/user-data/uploads"
SEG = "/home/claude/reels/faq/seg"
TM = ("zscale=t=linear:npl=203,format=gbrpf32le,zscale=p=bt709,tonemap=hable:desat=0,"
      "zscale=t=bt709:m=bt709:r=tv,format=yuv420p")
GR = "eq=contrast=1.04:saturation=1.06,unsharp=5:5:0.35"

SCENES = [
    [(f"{U}/IMG_4421.mov", 0.6, 6.0)],                                   # hook: walk-in
    [(f"{A}/cce1314d-IMG_4569.mov", 1.8, 7.4)],                          # Q1: cream plisse, sash opens
    [(f"{A}/677e5385-IMG_4787.mov", 0.2, 9.6),                           # Q2: pleats close-up
     (f"{A}/928a1e6c-IMG_4786.mov", 0.0, 3.5)],                          #     + wooden window pan
    [(f"{A}/1ddf9206-IMG_4418.mov", 0.0, 5.66),                          # Q3: dark plisse (bedroom)
     (f"{A}/a638eb6f-IMG_4427.mov", 0.0, 6.0)],                          #     + light plisse (zal/oshxona)
    [(f"{A}/0568d1d8-IMG_5001.mov", 1.2, 16.0)],                         # Q4: raised -> sky
    [(f"{U}/IMG_4424.mov", 0.3, 6.45),                                   # Q5: wooden window
     (f"{A}/f67d3a7f-IMG_4420.mov", 0.6, 7.7)],                          #     + dark plisse, grey frames
    [(f"{U}/IMG_4421.mov", 6.0, 6.9),                                    # CTA background (blurred later)
     (f"{U}/IMG_4425.mov", 0.0, 6.3)],
]


def run(args):
    subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", *args], check=True)


def scene(i, target):
    pieces = SCENES[i]
    avail = sum(m for _, _, m in pieces)
    need = target
    parts, used = [], 0.0
    for k, (src, st, mx) in enumerate(pieces):
        take = min(mx, max(0.0, need - used)) if avail >= need else mx
        if take <= 0.05:
            break
        out = f"{SEG}/_p{i}_{k}.mp4"
        run(["-ss", str(st), "-t", f"{take:.3f}", "-i", src, "-an", "-vf",
             f"scale=1080:1920:flags=lanczos,{TM},{GR},fps=30,setsar=1",
             "-c:v", "libx264", "-preset", "fast", "-crf", "15", "-pix_fmt", "yuv420p", out])
        parts.append(out)
        used += take
    slow = min(1.35, max(1.0, target / used))
    hold = max(0.0, target - used * slow)
    ins = sum([["-i", p] for p in parts], [])
    fc = "".join(f"[{j}:v]setpts=PTS-STARTPTS[a{j}];" for j in range(len(parts)))
    fc += "".join(f"[a{j}]" for j in range(len(parts))) + f"concat=n={len(parts)}:v=1:a=0[c];"
    fc += f"[c]setpts={slow:.4f}*PTS,fps=30,tpad=stop_mode=clone:stop_duration={hold + 0.1:.3f},trim=duration={target:.4f},setpts=PTS-STARTPTS[v]"
    name = f"S{i}" if i else "S0"
    run([*ins, "-filter_complex", fc, "-map", "[v]", "-c:v", "libx264", "-preset", "fast", "-crf", "15",
         "-pix_fmt", "yuv420p", f"{SEG}/{name}.mp4"])
    print(f"S{i}: target {target:.2f}s  footage {used:.2f}s  slow x{slow:.2f}  hold {hold:.2f}s")


if __name__ == "__main__":
    ds = [float(x) for x in sys.argv[1].split(",")]
    for i, d in enumerate(ds):
        scene(i, d)
