"""«Oq tyul, chetida — to‘q tyul» (Jalyuzi Classic, dikey kombinatsiya). v2 (owner 11.11: more shots; the dark side
panels are dark tulle, not curtains — the message is the white + dark tulle combination).
wide: the tulle closes -> native-4K detail of white + dark tulle -> detail of the white tulle with light ->
wide: it opens -> end card with an open/closed poll.
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
# name, source, ss, dur, speed
SC = [
    ("close", "st/dk.mp4", 0.0, 4.3, 1.0),
    ("d1", "st/dd1.mp4", 0.0, 3.5, 1.0),
    ("d2", "st/dd2.mp4", 0.0, 3.1, 1.0),
    ("open", "st/dk.mp4", 14.6, 4.75, 1.0),
    ("end", "endbg", 0, 5.8, None),
]
TRANS = {1: "fade", 2: "slideleft", 3: "fade", 4: "fadeblack"}
XFS = {1: 0.3, 2: 0.3, 3: 0.3, 4: 0.4}
ENC = "-c:v libx264 -preset fast -crf 15 -pix_fmt yuv420p"
SUB = (222, 212, 198)

ST, _t = [0.0], 0.0
for i in range(1, len(SC)):
    _t += SC[i - 1][3] - XFS[i]
    ST.append(_t)
TOTAL = ST[-1] + SC[-1][3]
NF = int(round(TOTAL * FPS))
S_CL, S_D1, S_D2, S_OP, S_END = ST
CHIMES = [(0.1, SC[0][3] - 0.2), (S_D2 + 0.3, S_D2 + 2.6), (S_OP + 0.1, S_END - 0.2)]


def sh(cmd):
    subprocess.run(cmd, shell=True, check=True)


def base():
    os.makedirs(f"{D}/bo", exist_ok=True)
    for name, src, ss, d, sp in SC:
        out = f"{D}/bo/dk_{name}.mp4"
        if src == "endbg":
            sh(f"ffmpeg -nostdin -v error -y -ss 17.6 -i {D}/st/dk.mp4 -an -vf \"setpts=PTS/0.45,fps=30,"
               f"tpad=stop_mode=clone:stop_duration=4,trim=duration={d + 0.1:.2f},setpts=PTS-STARTPTS,gblur=sigma=16,"
               f"eq=brightness=-0.2:saturation=0.85,format=yuv420p\" {ENC} {out}")
        else:
            sh(f"ffmpeg -nostdin -v error -y -ss {ss} -t {d / sp + 0.05:.3f} -i {D}/{src} -an -vf "
               f"\"setpts=PTS/{sp},fps=30,trim=duration={d / sp:.3f},setsar=1,format=yuv420p\" {ENC} {out}")
    ins = " ".join(f"-i {D}/bo/dk_{s[0]}.mp4" for s in SC)
    f = [f"[{i}:v]fps=30,setpts=PTS-STARTPTS,settb=AVTB[v{i}]" for i in range(len(SC))]
    prev = "[v0]"
    for i in range(1, len(SC)):
        f.append(f"{prev}[v{i}]xfade=transition={TRANS[i]}:duration={XFS[i]}:offset={ST[i]:.3f},settb=AVTB[x{i}]")
        prev = f"[x{i}]"
    sh(f"ffmpeg -nostdin -v error -y {ins} -filter_complex \"{';'.join(f)}\" -map \"{prev}\" -r 30 {ENC} {D}/base_dk.mp4")


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
    al = a_in(t, t0 + 0.12, 0.35) * a_out(t, t1 - 0.2, 0.22)
    if al <= 0.01:
        return
    grad(img, 1150, 1920, 0.8 * al)
    text(img, (86, y), top, SEMI(62), PAPER, al, 14)
    text(img, (98, y + 94), rib, SERI(76), GOLD, a_in(t, t0 + 0.3, 0.35) * a_out(t, t1 - 0.2, 0.22), 14)
    text(img, (90, y + 218), ru, MED(30), SUB, a_in(t, t0 + 0.5, 0.35) * a_out(t, t1 - 0.2, 0.22), 10)


def frame(i):
    t = i / FPS
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if t < S_D1 + 0.3:                                        # title while the tulle closes
        al = a_out(t, S_D1 - 0.15, 0.25)
        topgrad(img, 900, 0.72 * al)
        text(img, (86, 300), NAME + " · DIKEY", MONO(26), GOLD, a_in(t, 0, 0.3) * al, 8, tracking=6)
        text(img, (86, 362), "Oq tyul,", SER(112), PAPER, a_in(t, 0.0, 0.3) * al, 18)
        text(img, (100, 504), "chetida — to‘q tyul.", SERI(82), GOLD, a_in(t, 0.5, 0.35) * al, 16)
        text(img, (90, 630), "Белый тюль, по краям — тёмный.", MED(32), SUB, a_in(t, 0.9) * al, 10)
    lower(img, t, S_D1, S_D2 + 0.1, "Ikki rang —", "bitta kombinatsiya.", "Два цвета — одна комбинация.")
    lower(img, t, S_D2, S_OP + 0.1, "Oq tyul —", "mayin yorug‘lik.", "Белый тюль — мягкий свет.")
    lower(img, t, S_OP, S_END + 0.1, "Ochiq ham chiroyli,", "yopiq ham.", "Красиво — и открытым, и закрытым.")
    if t > S_END - 0.2:
        a0 = a_in(t, S_END + 0.1)
        lg = LOGO.copy()
        lg.thumbnail((440, 230))
        lg.putalpha(lg.split()[3].point(lambda v: int(v * a0)))
        img.alpha_composite(lg, ((W - lg.width) // 2, 215))
        text(img, (W // 2, 480), "Derazangizga ham", SER(66), PAPER, a_in(t, S_END + 0.25), 14, anchor="ma")
        text(img, (W // 2, 570), "shunday kombinatsiya?", SERI(70), GOLD, a_in(t, S_END + 0.4), 14, anchor="ma")
        text(img, (W // 2, 690), "Хотите такую же комбинацию на своё окно?", MED(30), SUB, a_in(t, S_END + 0.55), 10,
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
    for f in os.listdir(f"{D}/ov_dk"):
        os.remove(f"{D}/ov_dk/{f}")
    idx = list(range(NF))
    with Pool(6) as p:
        for k in range(0, len(idx), 24):
            ch = idx[k:k + 24]
            for i, a in zip(ch, p.map(frame, ch)):
                Image.fromarray(a).save(f"{D}/ov_dk/{i:04d}.png", compress_level=1)


def music():
    from airy_bed import airy_bed
    airy_bed(f"{D}/bed_dk.wav", TOTAL, S_END, CHIMES)


OUTN = "classic_dikey_kombinatsiya"


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
    print("starts", [round(x, 2) for x in ST], "total", round(TOTAL, 2))
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
