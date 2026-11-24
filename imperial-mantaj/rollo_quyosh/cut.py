"""Segments for the Classic rollo «galereya» video (DJI clips, owner 24.11). SDR bt709, 60 fps sources.
(name, clip, start, source seconds, speed)"""
import subprocess
import sys

U = "/mnt/user-data/uploads/DJI_20240915_{}_video.mov"
SEG = [("trace", "131743_242", 38.3, 4.4, 1.0),
       ("gal", "131703_957", 5.0, 3.0, 0.75),
       ("rise", "131743_242", 1.0, 4.9, 1.0),
       ("view", "131743_242", 6.0, 2.6, 1.0),
       ("down", "131743_242", 10.6, 5.3, 1.25),
       ("tex", "131743_242", 27.0, 2.7, 0.8),
       ("wide", "131623_412", 3.0, 3.2, 1.0)]
G = "eq=contrast=1.05:saturation=1.06,unsharp=5:5:0.3"


def cut(s):
    name, k, ss, dur, sp = s
    vf = f"setpts=PTS/{sp},fps=30,scale=1080:1920:flags=lanczos,{G},setsar=1,format=yuv420p"
    subprocess.run(f"ffmpeg -nostdin -v error -y -ss {ss} -t {dur} -i {U.format(k)} -an -vf \"{vf}\" -c:v libx264 "
                   f"-preset fast -crf 15 -pix_fmt yuv420p seg/{name}.mp4", shell=True, check=True)
    return name


if __name__ == "__main__":
    from multiprocessing import Pool
    names = sys.argv[1:]
    todo = [s for s in SEG if not names or s[0] in names]
    with Pool(3) as p:
        print(p.map(cut, todo))
