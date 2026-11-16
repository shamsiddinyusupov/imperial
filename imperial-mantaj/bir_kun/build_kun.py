"""«Bir deraza — bir kun» (JALYUZI CLASSIC, owner 17.11; reference style like Imperial «Bitta deraza», but from inside
and through a whole day). room.py animation (14 s, the real window IMG_5680 as a plate) -> match dissolve into the
real IMG_5680 (reversed, push-in) -> IMG_6057 pleats -> IMG_6040 slide -> Classic end card.
Text style «A — Quyosh». Music: dutar_bed (#21, dutar + doira + birds).
python3 build_kun.py [base|prev t,t|ov|music|final|cover|all]
"""
import os
import subprocess
import sys
from multiprocessing import Pool

import numpy as np
from PIL import Image

sys.path.insert(0, "/home/claude/reels/common")
sys.path.insert(0, "/home/claude/reels/qora_plisse")
sys.path.insert(0, "/home/claude/reels/common/brand")
from build_b import a_in, a_out, grad, topgrad  # noqa: E402
from brand import LOGO, PHONE  # noqa: E402
from classic_style import CREAM, GOLD, MED, MONO, PAPER, SEMI, SER, SERI, text  # noqa: E402

D = "/home/claude/reels/xtong"
W, H, FPS = 1080, 1920, 30
SUB = (222, 212, 198)
ENC = "-c:v libx264 -preset fast -crf 15 -pix_fmt yuv420p"
# name, file, dur, transition into it, xfade
SC = [("anim", "anim.mp4", 14.0, None, 0),
      ("r5680", "seg/r5680.mp4", 2.033, "fade", 0.8),
      ("p6057", "seg/p6057.mp4", 1.9, "fade", 0.4),
      ("p6040", "seg/p6040.mp4", 1.667, "fade", 0.4),
      ("end", "bo/end.mp4", 5.5, "fade", 0.5)]
ST, _t = [], 0.0
for k, s in enumerate(SC):
    if k:
        _t -= s[4]
    ST.append(_t)
    _t += s[2]
TOTAL = _t
NF = int(round(TOTAL * FPS))
S_REAL, S_END = ST[1], ST[4]
CLOCK = [(0, 400), (6.6, 400), (7.9, 780), (9.9, 780), (11.5, 1170), (13.0, 1198)]   # minutes since midnight


def sh(cmd):
    subprocess.run(cmd, shell=True, check=True)


def base():
    os.makedirs(f"{D}/bo", exist_ok=True)
    nfr = int(round(SC[-1][2] * FPS)) + 2
    sh(f"ffmpeg -nostdin -v error -y -loop 1 -framerate 30 -i {D}/plate.png -vf "
       f"\"zoompan=z='1.10+0.04*on/{nfr}':x='iw*0.55-(iw/zoom*0.55)':y='ih*0.45-(ih/zoom*0.45)':d=1:s=1080x1920:fps=30,"
       f"gblur=sigma=16,eq=brightness=-0.22:saturation=0.8:contrast=0.92,colorbalance=rm=0.04:bm=-0.04,"
       f"setsar=1,format=yuv420p\" -frames:v {nfr} -an {ENC} {D}/bo/end.mp4")
    ins = " ".join(f"-i {D}/{s[1]}" for s in SC)
    f = [f"[{i}:v]fps=30,setpts=PTS-STARTPTS,settb=AVTB,trim=duration={SC[i][2]:.3f}[v{i}]" for i in range(len(SC))]
    prev = "[v0]"
    for i in range(1, len(SC)):
        f.append(f"{prev}[v{i}]xfade=transition={SC[i][3]}:duration={SC[i][4]}:offset={ST[i]:.3f},settb=AVTB[x{i}]")
        prev = f"[x{i}]"
    sh(f"ffmpeg -nostdin -v error -y {ins} -filter_complex \"{';'.join(f)}\" -map \"{prev}\" -r 30 {ENC} {D}/base_kun.mp4")


def lower(img, t, t0, t1, top, rib, ru, y=1430, g=0.62):
    al = a_in(t, t0 + 0.12, 0.35) * a_out(t, t1 - 0.25, 0.25)
    if al <= 0.01:
        return
    grad(img, 1180, 1920, g * al)
    text(img, (86, y), top, SEMI(64), PAPER, al, 14)
    a2 = a_in(t, t0 + 0.32, 0.35) * a_out(t, t1 - 0.25, 0.25)
    text(img, (98, y + 96), rib, SERI(76), GOLD, a2, 14)
    text(img, (90, y + 222), ru, MED(30), SUB, a_in(t, t0 + 0.55, 0.35) * a_out(t, t1 - 0.25, 0.25), 10)


def clock_str(t):
    ts = [c[0] for c in CLOCK]
    m = CLOCK[-1][1]
    for (t0, m0), (t1, m1) in zip(CLOCK, CLOCK[1:]):
        if t0 <= t <= t1:
            u = np.clip((t - t0) / max(1e-6, t1 - t0), 0, 1)
            u = u * u * (3 - 2 * u)
            m = m0 + (m1 - m0) * u
            break
        if t < ts[0]:
            m = CLOCK[0][1]
    m = int(m)
    return f"{m // 60:02d}:{m % 60:02d}"


def frame(i, force_hook=False):
    t = i / FPS
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    # clock (the day passes)
    ac = a_in(t, 0.2, 0.4) * a_out(t, S_REAL - 0.1, 0.4)
    if force_hook:
        ac = 1.0
    if ac > 0.01:
        topgrad(img, 430, 0.55 * ac)
        text(img, (86, 150), "TOSHKENT · ТАШКЕНТ", MONO(24), GOLD, ac, 0, tracking=6)
        text(img, (86, 186), clock_str(t if not force_hook else 0.0), SEMI(84), PAPER, ac, 0)
    th = 1.5 if force_hook else t
    lower(img, th, 0.4, 2.85, "Bir deraza.", "Bir kun.", "Одно окно. Один день.")
    if not force_hook:
        lower(img, t, 3.6, 6.45, "Ertalab —", "quyoshga ochiq.", "Утром — навстречу солнцу.")
        lower(img, t, 8.25, 9.95, "Tushda —", "yumshoq yorug‘lik.", "Днём — мягкий свет.")
        lower(img, t, 11.7, 13.15, "Kechqurun —", "sokin va iliq.", "Вечером — тихо и уютно.")
        # real shots
        if S_REAL < t < S_END + 0.3:
            al = a_in(t, S_REAL + 0.5, 0.4) * a_out(t, S_END - 0.1, 0.3)
            topgrad(img, 420, 0.75 * al)
            text(img, (86, 170), "HAQIQIY KADR · РЕАЛЬНЫЕ КАДРЫ", MONO(27), GOLD, al, 0, tracking=5)
        lower(img, t, S_REAL + 0.5, S_END + 0.15, "Plisse —", "kun bo‘yi siz bilan.", "Плиссе — с вами весь день.",
              g=0.75)
        # end card
        if t > S_END - 0.1:
            a0 = a_in(t, S_END + 0.1)
            lg = LOGO.copy()
            lg.thumbnail((470, 250))
            lg.putalpha(lg.split()[3].point(lambda v: int(v * a0)))
            img.alpha_composite(lg, ((W - lg.width) // 2, 300))
            text(img, (W // 2, 640), "Plisse jalyuzi", SER(92), PAPER, a_in(t, S_END + 0.3), 16, anchor="ma")
            text(img, (W // 2, 770), "ertalabdan kechgacha.", SERI(70), GOLD, a_in(t, S_END + 0.5), 14, anchor="ma")
            text(img, (W // 2, 905), "Плиссе — с утра до вечера.", MED(30), SUB, a_in(t, S_END + 0.7), 10, anchor="ma")
            text(img, (W // 2, 1130), "Narxini bilish uchun", MED(40), CREAM, a_in(t, S_END + 1.0), 10, anchor="ma")
            text(img, (W // 2, 1190), "qo‘ng‘iroq qiling:", MED(40), CREAM, a_in(t, S_END + 1.1), 10, anchor="ma")
            text(img, (W // 2, 1270), PHONE, SEMI(72), GOLD, a_in(t, S_END + 1.3), 10, anchor="ma")
            text(img, (W // 2, 1400), "Yoki deraza rasmini direktga yuboring", MED(34), (236, 228, 214),
                 a_in(t, S_END + 1.7), 10, anchor="ma")
            text(img, (W // 2, 1450), "Цены — по телефону или пришлите фото окна в директ", MED(26), SUB,
                 a_in(t, S_END + 1.85), 10, anchor="ma")
    return np.asarray(img)


def render_ov():
    os.makedirs(f"{D}/ov", exist_ok=True)
    idx = list(range(NF))
    with Pool(6) as p:
        for k in range(0, len(idx), 24):
            ch = idx[k:k + 24]
            for i, a in zip(ch, p.map(frame, ch)):
                Image.fromarray(a).save(f"{D}/ov/{i:04d}.png", compress_level=1)


def music():
    from dutar_bed import dutar_bed
    dutar_bed(f"{D}/bed_kun.wav", TOTAL, dict(rise=2.9, tl1=6.5, noon=8.0, tl2=9.8, close=11.6, lamp=12.6,
                                               real=S_REAL, end=S_END))


OUTN = "classic_bir_deraza_bir_kun"


def final():
    os.makedirs(f"{D}/out", exist_ok=True)
    sh(f"ffmpeg -nostdin -v error -y -i {D}/base_kun.mp4 -framerate 30 -i {D}/ov/%04d.png -i {D}/bed_kun.wav "
       f"-filter_complex \"[0:v][1:v]overlay=0:0:format=auto,format=yuv420p[v];"
       f"[2:a]loudnorm=I=-15:TP=-1.5:LRA=11[a]\" -map \"[v]\" -map \"[a]\" -t {TOTAL:.3f} "
       f"-c:v libx264 -preset slow -crf 18 -pix_fmt yuv420p -color_primaries bt709 -color_trc bt709 -colorspace bt709 "
       f"-c:a aac -b:a 192k -movflags +faststart {D}/out/{OUTN}.mp4")


def cover():
    tt = 4.9
    sh(f"ffmpeg -v error -y -ss {tt} -i {D}/base_kun.mp4 -frames:v 1 {D}/cb.png")
    b = Image.open(f"{D}/cb.png").convert("RGBA")
    b.alpha_composite(Image.fromarray(frame(int(tt * FPS), force_hook=True)))
    b.convert("RGB").save(f"{D}/out/{OUTN}_muqova.jpg", quality=92)


if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else "all"
    print("starts", [round(s, 2) for s in ST], "total", round(TOTAL, 2))
    if what in ("base", "all"):
        base()
    if what == "prev":
        ims = []
        for tt in map(float, sys.argv[2].split(",")):
            sh(f"ffmpeg -v error -y -ss {tt} -i {D}/base_kun.mp4 -frames:v 1 {D}/pb.png")
            b = Image.open(f"{D}/pb.png").convert("RGBA")
            b.alpha_composite(Image.fromarray(frame(int(tt * FPS))))
            ims.append(b.convert("RGB").resize((360, 640)))
        c = Image.new("RGB", (365 * len(ims), 640), "white")
        for k, im in enumerate(ims):
            c.paste(im, (k * 365, 0))
        c.save(f"{D}/prev_kun.jpg", quality=85)
    if what in ("ov", "all"):
        render_ov()
    if what in ("music", "all"):
        music()
    if what in ("final", "all"):
        final()
    if what in ("cover", "all"):
        cover()
