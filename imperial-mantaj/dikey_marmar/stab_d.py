"""stabilise the dikey (IMG_61xx) shots with the stab3 method (4K, LK+RANSAC, smooth path, single warp)"""
import sys
sys.path.insert(0, "/home/claude/reels/deraza")
import stab3  # noqa: E402

U = "/mnt/user-data/uploads"
P = {6132: f"{U}/96761be9-IMG_6132.mov", 6128: f"{U}/575d285d-IMG_6128.mov", 6131: f"{U}/33d9a12a-IMG_6131.mov",
     6134: f"{U}/1f41f341-IMG_6134.mov", 6125: f"{U}/25ebd970-IMG_6125.mov", 6130: f"{U}/6fe219d3-IMG_6130.mov"}
stab3.ITEMS = {k: dict(path=v, trc="arib-std-b67") for k, v in P.items()}
stab3.D = "/home/claude/reels/dikey6"
stab3.SHOTS = {
    "gold": (6132, 0.0, 3.0, ("gauss", 14), None),
    "pan": (6128, 0.3, 3.8, ("gauss", 18), None),
    "turn": (6131, 6.0, 3.8, ("gauss", 18), None),
    "night": (6134, 5.0, 3.8, ("gauss", 18), None),
    "reveal": (6125, 0.0, 4.6, ("gauss", 20), None),
}
if __name__ == "__main__":
    from multiprocessing import Pool
    names = sys.argv[1:] or list(stab3.SHOTS)
    with Pool(2) as p:
        p.map(stab3.run, names, chunksize=1)
