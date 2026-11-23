"""Stabilised SDR segments for «Oddiy pardalardan charchadingizmi?» (Classic dikey, owner 23.11)."""
import json
import sys
from multiprocessing import Pool

sys.path.insert(0, "/home/claude/reels/deraza")
import stab3  # noqa: E402

P = json.load(open("/home/claude/reels/dikey7/paths.json"))
stab3.ITEMS = {k: dict(path=v, trc="arib-std-b67") for k, v in P.items()}
stab3.D = "/home/claude/reels/dikey7"
stab3.SHOTS = {
    "zal": ("82", 7.0, 4.6, ("gauss", 20), None),
    "bright": ("276", 12.0, 4.0, ("gauss", 20), None),
    "wide": ("372", 7.8, 4.0, ("gauss", 20), None),
    "hero": ("x6136", 2.3, 4.5, ("gauss", 20), None),
    "turn": ("372", 3.0, 3.6, ("gauss", 16), None),
    "turn2": ("462", 0.6, 3.6, ("gauss", 16), None),
    "close": ("247", 3.0, 5.0, ("gauss", 18), None),
    "var1": ("68", 0.0, 2.2, ("gauss", 14), None),
    "var2": ("143", 9.6, 2.2, ("gauss", 14), None),
    "var3": ("x6124", 3.3, 2.6, ("gauss", 14), None),
    "var4": ("x6132", 3.2, 2.0, ("gauss", 14), None),
}

if __name__ == "__main__":
    names = sys.argv[1:] or list(stab3.SHOTS)
    with Pool(2) as p:
        p.map(stab3.run, names)
