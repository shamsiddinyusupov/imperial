"""IMG_4056 insert: closed plisse -> raised -> (idle hand at top, sped up smoothly) -> pulled down.
Smooth speed ramp by picking source frames along an integrated speed curve. python3 remap.py [warm]"""
import os, subprocess, sys
import numpy as np
FPS = 30
SRC0, SRC1 = 0.9, 6.43
def speed(s):
    def sm(x):
        x = np.clip(x, 0, 1); return x * x * (3 - 2 * x)
    up = sm((s - 3.05) / 0.35); dn = sm((s - 4.55) / 0.35)
    return 1.0 + 1.1 * (up - dn)
s, src = SRC0, []
while s < SRC1:
    src.append(s); s += speed(s) / FPS
os.makedirs("rm", exist_ok=True)
for f in os.listdir("rm"): os.remove("rm/" + f)
for k, t in enumerate(src):
    i = min(193, int(round(t * FPS))) + 1
    os.symlink(os.path.abspath(f"fr/{i:04d}.jpg"), f"rm/{k:04d}.jpg")
grade = sys.argv[1] if len(sys.argv) > 1 else "colortemperature=temperature=5600:mix=0.6,eq=contrast=1.05:saturation=1.04:gamma=0.97"
subprocess.run(f"ffmpeg -nostdin -v error -y -framerate 30 -i rm/%04d.jpg -vf \"{grade},format=yuv420p\" "
               f"-c:v libx264 -preset fast -crf 15 -pix_fmt yuv420p real3.mp4", shell=True, check=True)
print("frames", len(src), "dur", round(len(src) / FPS, 2))
