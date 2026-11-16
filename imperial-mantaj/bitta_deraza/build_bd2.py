"""«Bitta deraza» v2 (IMPERIAL, owner 16.11): one continuous outside shot (facade2.py) — our window with a cream plisse
clearly installed from frame 0, the plisse comes down sash by sash, the house goes to sleep, a shadow behind the
fabric, the IMPERIAL mark printed on the plisse, pull-back — then a short REAL shot from inside (the dark plisse
closing over the night city, «Haqiqiy kadr») and the end card. New music: analog_bed (#20).
python3 build_bd2.py [base|prev t,t|ov|music|final|cover|all]
"""
import os
import subprocess
import sys
from multiprocessing import Pool

import numpy as np
from PIL import Image

sys.path.insert(0, "/home/claude/reels/ref1116")
sys.path.insert(0, "/home/claude/reels/common")
import build_bd as B  # noqa: E402  (fonts, text helpers, colours, logo, phone)
import facade2 as F2  # noqa: E402
from build_b import a_in, a_out  # noqa: E402

D = B.D
W, H, FPS = 1080, 1920, 30
FAC_D = F2.DUR
REAL_SS, REAL_D, END_D = 4.2, 3.2, 5.5
XF = 0.5
S_REAL = FAC_D - XF
S_END = S_REAL + REAL_D - XF
TOTAL = S_END + END_D
NF = int(round(TOTAL * FPS))
ENC = "-c:v libx264 -preset fast -crf 15 -pix_fmt yuv420p"
text, cloud, sweep = B.text, B.cloud, B.sweep
ITA, RU, LAB, LABM, DID = B.ITA, B.RU, B.LAB, B.LABM, B.DID
CREAM, GOLD, SAND = B.CREAM, B.GOLD, B.SAND


def sh(cmd):
    subprocess.run(cmd, shell=True, check=True)


def base():
    if not os.path.exists(f"{D}/bo/facade2.mp4"):
        sh(f"cd {D} && python3 facade2.py")
    sh(f"ffmpeg -nostdin -v error -y -ss {REAL_SS} -t {REAL_D} -i {B.Q}/st/nightpull.mp4 -an -vf \"fps=30,"
       f"eq=contrast=1.04:saturation=1.05,format=yuv420p\" {ENC} {D}/bo/real2.mp4")
    if not os.path.exists(f"{D}/bo/end.mp4"):
        B.base()
    f = ("[0:v]fps=30,setpts=PTS-STARTPTS,settb=AVTB[a];[1:v]fps=30,setpts=PTS-STARTPTS,settb=AVTB[b];"
         "[2:v]fps=30,setpts=PTS-STARTPTS,settb=AVTB[c];"
         f"[a][b]xfade=transition=fade:duration={XF}:offset={S_REAL:.3f},settb=AVTB[ab];"
         f"[ab][c]xfade=transition=fade:duration={XF}:offset={S_END:.3f},settb=AVTB[v]")
    sh(f"ffmpeg -nostdin -v error -y -i {D}/bo/facade2.mp4 -i {D}/bo/real2.mp4 -i {D}/bo/end.mp4 "
       f"-filter_complex \"{f}\" -map \"[v]\" -r 30 {ENC} {D}/base_bd2.mp4")


def line(img, t, t0, t1, uz, ru, y=1452, col=CREAM, big=66, gold=None):
    al = a_in(t, t0, 0.5) * a_out(t, t1, 0.5)
    if al <= 0.01:
        return
    cloud(img, (30, y - 100, 1050, y + 260), al, a=200, blur=55)
    text(img, (W // 2, y), uz, ITA(big), col, al, 16, anchor="ma")
    if gold:
        text(img, (W // 2, y + 82), gold, ITA(big + 6), GOLD, a_in(t, t0 + 0.3, 0.5) * a_out(t, t1, 0.5), 16,
             anchor="ma")
    text(img, (W // 2, y + (180 if gold else 96)), ru, RU(30), CREAM, a_in(t, t0 + 0.5, 0.5) * a_out(t, t1, 0.5), 10,
         anchor="ma")


def frame(i):
    t = i / FPS
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if t < S_REAL + 0.3:
        text(img, (90, 262), "TOSHKENT · 22:40", LAB(26), CREAM, a_in(t, 0.2, 0.4) * a_out(t, 3.4, 0.5), 0, tracking=6)
        line(img, t, 0.3, 3.3, "Har bir derazaning ortida —", "За каждым окном — своя жизнь.", gold="bir hayot.")
        line(img, t, 3.9, 7.0, "Plisse —", "Плиссе — на каждую створку отдельно.", gold="har bir tabaqaga alohida.")
        line(img, t, 8.6, 10.5, "Dunyo — tashqarida qolsin.", "Пусть мир останется снаружи.", y=1500)
        line(img, t, 10.9, FAC_D - 0.3, "Xayrli tun, Toshkent.", "Спокойной ночи, Ташкент.", y=1500)
    if S_REAL - 0.1 < t < S_END + 0.3:
        al = a_in(t, S_REAL + 0.3, 0.4) * a_out(t, S_END - 0.1, 0.4)
        text(img, (90, 262), "HAQIQIY KADR · РЕАЛЬНЫЕ КАДРЫ", LAB(24), CREAM, al, 0, tracking=5)
        line(img, t, S_REAL + 0.4, S_END - 0.1, "Ichkaridan — shunday.", "Изнутри — вот так.", y=1500)
    if t > S_END - 0.2:
        img.alpha_composite(Image.fromarray(B.frame(int(round((t - S_END + B.S_END) * FPS)))))
    return np.asarray(img)


def render_ov():
    os.makedirs(f"{D}/ov2", exist_ok=True)
    idx = list(range(NF))
    with Pool(6) as p:
        for k in range(0, len(idx), 24):
            ch = idx[k:k + 24]
            for i, a in zip(ch, p.map(frame, ch)):
                Image.fromarray(a).save(f"{D}/ov2/{i:04d}.png", compress_level=1)


def music():
    from analog_bed import analog_bed
    analog_bed(f"{D}/bed_bd2.wav", TOTAL, F2.T_LEFT, F2.T_RIGHT + F2.T_DOWN - F2.T_LEFT, F2.T_LOGO, F2.T_BACK, S_END)


OUTN = "imperial_bitta_deraza_v2"


def final():
    os.makedirs(f"{D}/out", exist_ok=True)
    sh(f"ffmpeg -nostdin -v error -y -i {D}/base_bd2.mp4 -framerate 30 -i {D}/ov2/%04d.png -i {D}/bed_bd2.wav "
       f"-filter_complex \"[0:v][1:v]overlay=0:0:format=auto,format=yuv420p[v];"
       f"[2:a]loudnorm=I=-15:TP=-1.5:LRA=11[a]\" -map \"[v]\" -map \"[a]\" -t {TOTAL:.3f} "
       f"-c:v libx264 -preset slow -crf 18 -pix_fmt yuv420p -color_primaries bt709 -color_trc bt709 -colorspace bt709 "
       f"-c:a aac -b:a 192k -movflags +faststart {D}/out/{OUTN}.mp4")


def cover():
    tt = 1.8
    sh(f"ffmpeg -v error -y -ss {tt} -i {D}/base_bd2.mp4 -frames:v 1 {D}/cb2.png")
    b = Image.open(f"{D}/cb2.png").convert("RGBA")
    b.alpha_composite(Image.fromarray(frame(int(tt * FPS))))
    b.convert("RGB").save(f"{D}/out/{OUTN}_muqova.jpg", quality=92)


if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else "all"
    print("real", S_REAL, "end", S_END, "total", round(TOTAL, 2))
    if what in ("base", "all"):
        base()
    if what == "prev":
        ims = []
        for tt in map(float, sys.argv[2].split(",")):
            sh(f"ffmpeg -v error -y -ss {tt} -i {D}/base_bd2.mp4 -frames:v 1 {D}/pb.png")
            b = Image.open(f"{D}/pb.png").convert("RGBA")
            b.alpha_composite(Image.fromarray(frame(int(tt * FPS))))
            ims.append(b.convert("RGB").resize((360, 640)))
        c = Image.new("RGB", (365 * len(ims), 640), "white")
        for k, im in enumerate(ims):
            c.paste(im, (k * 365, 0))
        c.save(f"{D}/prev_bd2.jpg", quality=85)
    if what in ("ov", "all"):
        render_ov()
    if what in ("music", "all"):
        music()
    if what in ("final", "all"):
        final()
    if what in ("cover", "all"):
        cover()
