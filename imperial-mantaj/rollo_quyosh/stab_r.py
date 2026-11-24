"""Stabilised slow-motion (0.5x: 60 fps source frames written at 30 fps) for the gallery and texture shots."""
import sys
from multiprocessing import Pool

sys.path.insert(0, "/home/claude/reels/deraza")
import stab3  # noqa: E402

U = "/mnt/user-data/uploads/DJI_20240915_{}_video.mov"
stab3.ITEMS = {k: dict(path=U.format(k), trc="bt709") for k in ("131743_242", "131703_957", "131623_412")}
stab3.D = "/home/claude/reels/rollo1"
stab3.SHOTS = {"gal": ("131703_957", 5.0, 2.1, ("gauss", 30), None),
               "tex": ("131743_242", 27.0, 1.75, ("gauss", 30), None)}

if __name__ == "__main__":
    with Pool(2) as p:
        p.map(stab3.run, sys.argv[1:] or list(stab3.SHOTS))
