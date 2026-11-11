"""«Oq dikey tyul — mayin yorug‘lik» (Jalyuzi Classic, dikey). Calm one-take formula: the tulle closes, stays,
opens again (middle sped up), short title from frame 0, end card with an open/closed poll.
python3 build_dk.py [base|prev t,t|ov|music|final|cover|all]
"""
import os
import subprocess
import sys
from multiprocessing import Pool

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, "/home/claude/reels/common")
sys.path.insert(0, "/home/claude/reels/qora_plisse")
from build_b import a_in, a_out, grad, topgrad  # noqa: E402
sys.path.insert(0, "/home/claude/reels/common/brand")
from brand import LOGO, NAME, PHONE  # noqa: E402
from classic_style import CREAM, GOLD, INK, MED, MONO, PAPER, SEMI, SER, SERI, text  # noqa: E402

D = "/home/claude/reels/n11"
W, H, FPS = 1080, 1920, 30
A_END, B_END, MID_SP = 4.3, 14.6, 1.6
LA, LB, LC = A_END, (B_END - A_END) / MID_SP, 19.35 - B_END
VID = LA + LB + LC
XF = 0.4
S_END = VID - XF
END_D = 5.8
TOTAL = S_END + END_D
NF = int(round(TOTAL * FPS))
ENC = "-c:v libx264 -preset fast -crf 15 -pix_fmt yuv420p"
SUB = (222, 212, 198)
CHIMES = [(0.1, LA - 0.1), (LA + LB - 0.1, VID - 0.4)]


def sh(cmd):
    subprocess.run(cmd, shell=True, check=True)


def base():
    os.makedirs(f"{D}/bo", exist_ok=True)
    src = f"{D}/st/dk.mp4"
    f = (f"[0:v]split=3[a0][b0][c0];"
         f"[a0]trim=0:{A_END},setpts=PTS-STARTPTS[a];"
         f"[b0]trim={A_END}:{B_END},setpts=(PTS-STARTPTS)/{MID_SP}[b];"
         f"[c0]trim={B_END}:19.35,setpts=PTS-STARTPTS[c];"
         f"[a][b][c]concat=n=3:v=1:a=0,fps=30,format=yuv420p[v]")
    sh(f"ffmpeg -nostdin -v error -y -i {src} -filter_complex \"{f}\" -map \"[v]\" -an {ENC} {D}/bo/dk_v.mp4")
    sh(f"ffmpeg -nostdin -v error -y -ss 17.6 -i {src} -an -vf \"setpts=PTS/0.45,fps=30,tpad=stop_mode=clone:stop_duration=4,"
       f"trim=duration={END_D + 0.1:.2f},setpts=PTS-STARTPTS,gblur=sigma=16,eq=brightness=-0.2:saturation=0.85,"
       f"format=yuv420p\" {ENC} {D}/bo/dk_end.mp4")
    sh(f"ffmpeg -nostdin -v error -y -i {D}/bo/dk_v.mp4 -i {D}/bo/dk_end.mp4 -filter_complex "
       f"\"[0:v]fps=30,setpts=PTS-STARTPTS,settb=AVTB[x];[1:v]fps=30,setpts=PTS-STARTPTS,settb=AVTB[y];"
       f"[x][y]xfade=transition=fadeblack:duration={XF}:offset={S_END:.3f},settb=AVTB[v]\" -map \"[v]\" -r 30 {ENC} "
       f"{D}/base_dk.mp4")


def pill(img, cx, cy, s, al, filled, pulse=0.0, w=250):
    if al <= 0.01:
        return
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    h = 92
    box = (cx - w // 2, cy - h // 2, cx + w // 2, cy + h // 2)
    if pulse > 0.01:
        e = 10 + 26 * pulse
        d.rounded_rectangle((box[0] - e, box[1] - e, box[2] + e, box[3] + e), int(h / 2 + e),
                            outline=GOLD + (int(200 * al * (1 - pulse)),), width=5)
    if filled:
        d.rounded_rectangle(box, h // 2, fill=GOLD + (int(255 * al),))
    else:
        d.rounded_rectangle(box, h // 2, fill=(20, 18, 16, int(120 * al)), outline=CREAM + (int(235 * al),), width=4)
    d.text((cx, cy + 2), s, font=SEMI(44), fill=(INK if filled else CREAM) + (int(255 * al),), anchor="mm")
    img.alpha_composite(lay)


def lower(img, t, t0, t1, top, rib, ru, y=1440):
    al = a_in(t, t0 + 0.12, 0.4) * a_out(t, t1 - 0.25, 0.25)
    if al <= 0.01:
        return
    grad(img, 1150, 1920, 0.8 * al)
    text(img, (86, y), top, SEMI(62), PAPER, al, 14)
    text(img, (98, y + 94), rib, SERI(76), GOLD, a_in(t, t0 + 0.35, 0.4) * a_out(t, t1 - 0.25, 0.25), 14)
    text(img, (90, y + 218), ru, MED(30), SUB, a_in(t, t0 + 0.55, 0.4) * a_out(t, t1 - 0.25, 0.25), 10)


def frame(i):
    t = i / FPS
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if t < LA + 0.3:                                          # title while the tulle closes
        al = a_out(t, LA - 0.3, 0.3)
        topgrad(img, 900, 0.7 * al)
        text(img, (86, 300), NAME + " · DIKEY", MONO(26), GOLD, a_in(t, 0, 0.3) * al, 8, tracking=6)
        text(img, (86, 362), "Oq dikey tyul", SER(108), PAPER, a_in(t, 0.0, 0.3) * al, 18)
        text(img, (100, 500), "mayin yorug‘lik.", SERI(88), GOLD, a_in(t, 0.5, 0.35) * al, 16)
        text(img, (90, 630), "Белый вертикальный тюль — мягкий свет.", MED(32), SUB, a_in(t, 0.9) * al, 10)
    lower(img, t, LA + 0.1, LA + LB - 0.1, "Oq tyul va to‘q parda —", "klassik juftlik.",
          "Белый тюль и тёмные шторы — классика.")
    lower(img, t, LA + LB + 0.2, S_END + 0.1, "Ochiq ham chiroyli,", "yopiq ham.", "Красиво — и открытым, и закрытым.")
    if t > S_END - 0.2:
        a0 = a_in(t, S_END + 0.1)
        lg = LOGO.copy()
        lg.thumbnail((440, 230))
        lg.putalpha(lg.split()[3].point(lambda v: int(v * a0)))
        img.alpha_composite(lg, ((W - lg.width) // 2, 215))
        text(img, (W // 2, 480), "Derazangizga ham", SER(66), PAPER, a_in(t, S_END + 0.25), 14, anchor="ma")
        text(img, (W // 2, 570), "dikey tyul kerakmi?", SERI(72), GOLD, a_in(t, S_END + 0.4), 14, anchor="ma")
        text(img, (W // 2, 690), "Нужен вертикальный тюль на ваше окно?", MED(30), SUB, a_in(t, S_END + 0.55), 10,
             anchor="ma")
        text(img, (W // 2, 800), "Deraza rasmini direktga yuboring", SEMI(42), PAPER, a_in(t, S_END + 0.8), 10,
             anchor="ma")
        text(img, (W // 2, 860), "Пришлите фото окна в директ", MED(30), SUB, a_in(t, S_END + 0.95), 10, anchor="ma")
        ap = a_in(t, S_END + 1.4, 0.3)
        pu = ((t - S_END - 2.0) % 1.0) if t > S_END + 2.0 else 0.0
        text(img, (W // 2, 990), "Sizga qaysi biri yoqadi? · Как вам больше нравится?", MED(28), (236, 228, 214), ap, 8,
             anchor="ma")
        pill(img, W // 2 - 150, 1100, "OCHIQ", ap, True, pu)
        pill(img, W // 2 + 150, 1100, "YOPIQ", ap, False)
        text(img, (W // 2, 1170), "Izohga yozing · Ответьте в комментариях", MED(26), SUB, ap, 6, anchor="ma")
        text(img, (W // 2, 1490), "Qo‘ng‘iroq qiling · Звоните", MED(30), SUB, a_in(t, S_END + 1.0), 8, anchor="ma")
        text(img, (W // 2, 1540), PHONE, SEMI(58), GOLD, a_in(t, S_END + 1.1), 8, anchor="ma")
    return np.asarray(img)


def render_ov():
    os.makedirs(f"{D}/ov_dk", exist_ok=True)
    idx = list(range(NF))
    with Pool(6) as p:
        for k in range(0, len(idx), 24):
            ch = idx[k:k + 24]
            for i, a in zip(ch, p.map(frame, ch)):
                Image.fromarray(a).save(f"{D}/ov_dk/{i:04d}.png", compress_level=1)


def music():
    from airy_bed import airy_bed
    airy_bed(f"{D}/bed_dk.wav", TOTAL, S_END, CHIMES)


OUTN = "classic_dikey_oq_tyul"


def final():
    os.makedirs(f"{D}/out", exist_ok=True)
    sh(f"ffmpeg -nostdin -v error -y -i {D}/base_dk.mp4 -framerate 30 -i {D}/ov_dk/%04d.png -i {D}/bed_dk.wav "
       f"-filter_complex \"[0:v][1:v]overlay=0:0:format=auto,format=yuv420p[v];"
       f"[2:a]loudnorm=I=-15:TP=-1.5:LRA=9[a]\" -map \"[v]\" -map \"[a]\" -t {TOTAL:.3f} "
       f"-c:v libx264 -preset slow -crf 18 -pix_fmt yuv420p -color_primaries bt709 -color_trc bt709 -colorspace bt709 "
       f"-c:a aac -b:a 192k -movflags +faststart {D}/out/{OUTN}.mp4")


def cover():
    tt = 2.2
    sh(f"ffmpeg -v error -y -ss {tt} -i {D}/base_dk.mp4 -frames:v 1 {D}/cs/cb.png")
    b = Image.open(f"{D}/cs/cb.png").convert("RGBA")
    b.alpha_composite(Image.fromarray(frame(int(tt * FPS))))
    b.convert("RGB").save(f"{D}/out/{OUTN}_muqova.jpg", quality=92)


if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else "all"
    print("A/B/C", round(LA, 2), round(LB, 2), round(LC, 2), "end", round(S_END, 2), "total", round(TOTAL, 2))
    if what in ("base", "all"):
        base()
    if what == "prev":
        ims = []
        for tt in map(float, sys.argv[2].split(",")):
            sh(f"ffmpeg -v error -y -ss {tt} -i {D}/base_dk.mp4 -frames:v 1 {D}/cs/pb.png")
            b = Image.open(f"{D}/cs/pb.png").convert("RGBA")
            b.alpha_composite(Image.fromarray(frame(int(tt * FPS))))
            ims.append(b.convert("RGB").resize((360, 640)))
        c = Image.new("RGB", (365 * len(ims), 640), "white")
        for k, im in enumerate(ims):
            c.paste(im, (k * 365, 0))
        c.save(f"{D}/cs/prev_dk.jpg", quality=85)
    if what in ("ov", "all"):
        render_ov()
    if what in ("music", "all"):
        music()
    if what in ("final", "all"):
        final()
    if what in ("cover", "all"):
        cover()
