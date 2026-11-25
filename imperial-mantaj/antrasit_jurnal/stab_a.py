"""Segments for «Antrasit» (Imperial, owner 25.11): new door clips IMG_6119-6121 + base plisse clips with anthracite frames."""
import json
import sys
from multiprocessing import Pool

sys.path.insert(0, "/home/claude/reels/deraza")
import stab3  # noqa: E402

it = {e["id"]: e for e in json.load(open("/home/claude/baza_work/items.json"))}
U = "/mnt/user-data/uploads"
P = {"6119": f"{U}/b70abeaa-IMG_6119.mov", "6120": f"{U}/dfc0fbdf-IMG_6120.mov", "6121": f"{U}/ef98897d-IMG_6121.mov",
     "541": it[541]["path"], "547": it[547]["path"], "548": it[548]["path"]}
stab3.ITEMS = {k: dict(path=v, trc="arib-std-b67") for k, v in P.items()}
stab3.D = "/home/claude/reels/antrasit"
stab3.SHOTS = {
    "eshik": ("6120", 4.5, 4.6, ("gauss", 20), None),
    "tabaqa": ("6119", 0.2, 4.6, ("gauss", 20), None),
    "macro": ("6121", 0.0, 2.6, ("gauss", 16), None),
    "door2": ("547", 2.6, 4.4, ("gauss", 20), None),
    "deraza": ("541", 0.3, 4.4, ("gauss", 20), None),
    "pleat": ("541", 2.4, 2.6, ("gauss", 16), None),
    "deraza2": ("548", 4.4, 4.6, ("gauss", 20), None),
    "koridor": ("6121", 3.0, 4.6, ("gauss", 20), None),
}

if __name__ == "__main__":
    with Pool(2) as p:
        p.map(stab3.run, sys.argv[1:] or list(stab3.SHOTS))
