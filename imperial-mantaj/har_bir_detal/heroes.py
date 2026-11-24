"""Hero and montage shots (own footage), stabilised SDR 1080x1920 30 fps -> seg/<name>.mp4"""
import json
import subprocess
import sys
from multiprocessing import Pool

sys.path.insert(0, "/home/claude/reels/deraza")
import stab3  # noqa: E402

it = {e["id"]: e for e in json.load(open("/home/claude/baza_work/items.json"))}
DJI = "/mnt/user-data/uploads/DJI_20240915_{}_video.mov"
stab3.ITEMS = {i: dict(path=it[i]["path"], trc="arib-std-b67") for i in (247, 539, 521, 241, 82, 557)}
stab3.D = "/home/claude/reels/yigil2"
stab3.SHOTS = {
    "h_dikey": (247, 9.6, 2.5, ("gauss", 18), None),
    "h_kombo": (241, 1.0, 2.5, ("gauss", 18), None),
    "h_plisse": (521, 0.6, 2.5, ("gauss", 18), None),
            "m_plisse": (557, 1.2, 0.9, ("gauss", 10), None),
}
G = "eq=contrast=1.05:saturation=1.06,unsharp=5:5:0.3"


def dji(args):
    name, k, ss, dur = args
    subprocess.run(f"ffmpeg -nostdin -v error -y -ss {ss} -t {dur} -i {DJI.format(k)} -an -vf \"fps=30,scale=1080:1920:"
                   f"flags=lanczos,{G},setsar=1,format=yuv420p\" -c:v libx264 -preset fast -crf 15 seg/{name}.mp4",
                   shell=True, check=True)


if __name__ == "__main__":
    with Pool(2) as p:
        p.map(stab3.run, list(stab3.SHOTS))
        p.map(dji, [("h_rollo", "131743_242", 1.6, 2.6), ("m_rollo", "131623_412", 4.0, 0.9)])
