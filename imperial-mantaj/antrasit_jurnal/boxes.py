"""Pre-render each page's video into its frame box (crop to the box aspect, scale, light grade). box/<name>.mp4"""
import subprocess
from multiprocessing import Pool

D = "/home/claude/reels/antrasit"
G = "eq=contrast=1.05:saturation=0.94"
# name: (segment, box w, box h, speed, pingpong)
BOX = {"p1": ("eshik", 900, 1080, 1.0, False),
       "p2a": ("tabaqa", 440, 1000, 1.0, False), "p2b": ("macro", 440, 1000, 0.9, True),
       "p3": ("deraza2", 1080, 1500, 1.0, False),
       "p4": ("door2", 620, 1340, 1.0, False)}


def run(name):
    seg, w, h, sp, pp = BOX[name]
    crop = f"crop='min(iw,ih*{w}/{h})':'min(ih,iw*{h}/{w})'"
    pre = f"[0:v]setpts=PTS/{sp},{crop},scale={w}:{h}:flags=lanczos,{G},setsar=1"
    if pp:
        fc = f"{pre},split[a][b];[b]reverse[r];[a][r]concat=n=2:v=1:a=0,fps=30,format=yuv420p[v]"
    else:
        fc = f"{pre},fps=30,format=yuv420p[v]"
    subprocess.run(f"ffmpeg -nostdin -v error -y -i {D}/seg/{seg}.mp4 -filter_complex \"{fc}\" -map \"[v]\" -c:v libx264 "
                   f"-preset fast -crf 14 {D}/box/{name}.mp4", shell=True, check=True)
    return name


if __name__ == "__main__":
    with Pool(3) as p:
        print(p.map(run, list(BOX)))
