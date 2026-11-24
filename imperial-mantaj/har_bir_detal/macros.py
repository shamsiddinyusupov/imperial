"""Macro hero + beauty shots for the premium version: stabilised SDR -> seg/x_<name>.mp4 (stab3), DJI slow-mo."""
import json
import subprocess
import sys
from multiprocessing import Pool

sys.path.insert(0, "/home/claude/reels/deraza")
import stab3  # noqa: E402

M = json.load(open("/home/claude/reels/yigil2/macro_paths.json"))
it = {e["id"]: e for e in json.load(open("/home/claude/baza_work/items.json"))}
stab3.ITEMS = {"x6132": dict(path=M["x6132"], trc="arib-std-b67"), "538": dict(path=M["538"], trc="arib-std-b67"),
               "544": dict(path=M["544"], trc="arib-std-b67"), "539": dict(path=M["539"], trc="arib-std-b67")}
stab3.D = "/home/claude/reels/yigil2"
stab3.SHOTS = {"x_dikey": ("x6132", 2.0, 2.6, ("gauss", 20), None),
               "x_kombo": ("538", 46.5, 2.6, ("gauss", 20), None),
               "x_plisse": ("544", 7.2, 2.6, ("gauss", 20), None),
               "y_kombo": ("539", 26.0, 1.2, ("gauss", 12), None),
               "y_plisse": ("544", 14.8, 1.2, ("gauss", 12), None)}
DJI = "/mnt/user-data/uploads/DJI_20240915_{}_video.mov"


def dji(a):
    name, k, ss, dur, sp = a
    subprocess.run(f"ffmpeg -nostdin -v error -y -ss {ss} -t {dur} -i {DJI.format(k)} -an -vf \"setpts=PTS/{sp},fps=30,"
                   f"scale=1080:1920:flags=lanczos,setsar=1,format=yuv420p\" -c:v libx264 -preset fast -crf 15 "
                   f"/home/claude/reels/yigil2/seg/{name}.mp4", shell=True, check=True)


if __name__ == "__main__":
    with Pool(2) as p:
        p.map(stab3.run, list(stab3.SHOTS))
        p.map(dji, [("x_rollo", "131743_242", 26.0, 1.35, 0.5), ("y_rollo", "131743_242", 38.8, 1.2, 1.0)])
