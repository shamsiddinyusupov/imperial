"""Per-clip white balance to a warm cream white, then the shared 'Iliq krem' look."""
import subprocess, sys
import numpy as np
from PIL import Image
TARGET = np.array([234, 228, 216.0])          # warm cream for the brightest 15 % (tulle)
LOOK = ("huesaturation=saturation=-0.85:colors=c+b:strength=8,curves=all='0/0.03 0.25/0.245 0.5/0.52 0.75/0.79 1/0.975',eq=saturation=0.97,"
        "colorbalance=rs=-0.01:bs=0.012:rm=0.025:bm=-0.02:rh=0.01:bh=-0.012,vignette=angle=PI/9,noise=alls=4:allf=t")
def gains(path):
    a = np.asarray(Image.open(path).convert("RGB"), dtype=float)
    l = a.mean(2)
    hi = a[l > np.percentile(l, 85)].mean(0)
    g = TARGET / hi
    m = g.mean()
    return np.clip(g / m, 0.97, 1.03) * min(m, 1.25)      # limit the colour shift so browns stay chocolate, not copper
def vf(g):
    return f"colorchannelmixer=rr={g[0]:.3f}:gg={g[1]:.3f}:bb={g[2]:.3f},{LOOK}"
if __name__ == "__main__":
    for x in sys.argv[1:]:
        g = gains(f"frames/raw_{x}.jpg")
        subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-i", f"frames/raw_{x}.jpg", "-vf", vf(g), "-q:v", "2", f"frames/grd_{x}.jpg"], check=True)
        print(x, g.round(3))
