"""Join seg/S0..S6 (S6 blurred for the CTA) with offsets taken from faq_reel.START."""
import subprocess, sys, importlib.util
sys.argv = ["x", "/home/claude/reels/faq/prev"]
spec = importlib.util.spec_from_file_location("fr", "/home/claude/reels/faq/faq_reel.py")
fr = importlib.util.module_from_spec(spec); spec.loader.exec_module(fr)
D = "/home/claude/reels/faq"
subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-i", f"{D}/seg/S6.mp4", "-vf",
                "gblur=sigma=14,eq=brightness=-0.16:saturation=0.85", "-c:v", "libx264", "-preset", "fast",
                "-crf", "15", "-pix_fmt", "yuv420p", f"{D}/seg/S6b.mp4"], check=True)
segs = ["S0", "S1", "S2", "S3", "S4", "S5", "S6b"]
ins = sum([["-i", f"{D}/seg/{s}.mp4"] for s in segs], [])
fc = ";".join(f"[{i}:v]settb=AVTB,setpts=PTS-STARTPTS,fps=30[v{i}]" for i in range(7))
prev = "v0"
for i in range(1, 7):
    tr = "fade" if i in (1, 6) else "smoothleft"
    out = f"x{i}" if i < 6 else "out"
    fc += f";[{prev}][v{i}]xfade=transition={tr}:duration={fr.XF}:offset={fr.START[i]:.4f}[{out}]"
    prev = out
subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", *ins, "-filter_complex", fc + ";[out]format=yuv420p[o]",
                "-map", "[o]", "-r", "30", "-c:v", "libx264", "-preset", "fast", "-crf", "14", "-pix_fmt", "yuv420p",
                f"{D}/base.mp4"], check=True)
print("total", round(fr.TOTAL, 3), "frames", fr.NF)
