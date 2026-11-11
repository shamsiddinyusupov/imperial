"""«Qaysi rang sizga yoqdi? 1, 2 yoki 3» — plisse quiz (Jalyuzi Classic, choice/participation, no voice).
hook: three colours side by side -> each colour full screen with a big number -> installation -> end card with
the three colours as tiles and «write the number».
python3 build_pq.py [base|prev t,t|ov|music|final|cover|all]
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
XF = 0.3
OPT = ["st/o1.mp4", "st/o2b.mp4", "st/o3.mp4"]
# name, source, ss, dur(src), speed
SC = [
    ("hk", "trip", 0, 3.3, None),
    ("o1", "st/o1.mp4", 0.0, 4.7, 1.15),
    ("o2", "st/o2b.mp4", 0.0, 4.6, 1.15),
    ("o3", "st/o3.mp4", 0.0, 2.9, 1.05),
    ("op", "st/op.mp4", 2.0, 3.6, 1.35),
    ("ins", "st/ins.mp4", 0.0, 5.0, 1.6),
    ("end", "tiles", 0, 6.0, None),
]
TRANS = {1: "fade", 2: "slideleft", 3: "slideleft", 4: "fade", 5: "fade", 6: "fadeblack"}
SUB = (222, 212, 198)
GAP, SW_ = 12, 352
CROPX = [364, 150, 364]
TX = [80, 395, 710]
TY, TW, TH = 640, 290, 515


def odur(s):
    return s[3] / s[4] if isinstance(s[4], float) else s[3]


ST, _t = [], 0.0
for s in SC:
    ST.append(_t)
    _t += odur(s) - XF
TOTAL = _t + XF
NF = int(round(TOTAL * FPS))
ENC = "-c:v libx264 -preset fast -crf 15 -pix_fmt yuv420p"
S_HK, S_O1, S_O2, S_O3, S_OP, S_INS, S_END = ST
END_OF = dict(zip([s[0] for s in SC], ST[1:] + [TOTAL]))
OPTS = [(1, S_O1, END_OF["o1"]), (2, S_O2, END_OF["o2"]), (3, S_O3, END_OF["op"])]


def sh(cmd):
    subprocess.run(cmd, shell=True, check=True)


def base():
    os.makedirs(f"{D}/bo", exist_ok=True)
    for s in SC:
        name, src, ss, d, sp = s
        out = f"{D}/bo/pq_{name}.mp4"
        od = odur(s)
        if src == "trip":                 # three colour strips side by side, cream gaps
            ins = " ".join(f"-i {D}/{o}" for o in OPT)
            f = []
            for k in range(3):
                f.append(f"[{k}:v]setpts=PTS/0.9,fps=30,tpad=stop_mode=clone:stop_duration=2,trim=duration={od:.3f},"
                         f"setpts=PTS-STARTPTS,crop={SW_}:1920:{CROPX[k]}:0"
                         + (f",pad={SW_ + GAP}:1920:0:0:color=0xFAF3E8" if k < 2 else "") + f"[s{k}]")
            f.append("[s0][s1][s2]hstack=inputs=3,format=yuv420p[v]")
            sh(f"ffmpeg -nostdin -v error -y {ins} -filter_complex \"{';'.join(f)}\" -map \"[v]\" -an {ENC} {out}")
        elif src == "tiles":              # blurred background + three live tiles
            ins = f"-stream_loop 2 -i {D}/st/o3.mp4 " + " ".join(f"-i {D}/{o}" for o in OPT)
            f = [f"[0:v]fps=30,trim=duration={od:.3f},setpts=PTS-STARTPTS,gblur=sigma=18,"
                 f"eq=brightness=-0.32:saturation=0.7[bg]"]
            for k in range(3):
                f.append(f"[{k + 1}:v]setpts=PTS/0.75,fps=30,tpad=stop_mode=clone:stop_duration=3,"
                         f"trim=duration={od:.3f},setpts=PTS-STARTPTS,crop=607:1080:236:420,scale={TW}:{TH}[t{k}]")
            f.append(f"[bg][t0]overlay={TX[0]}:{TY}[b1];[b1][t1]overlay={TX[1]}:{TY}[b2];"
                     f"[b2][t2]overlay={TX[2]}:{TY},format=yuv420p[v]")
            sh(f"ffmpeg -nostdin -v error -y {ins} -filter_complex \"{';'.join(f)}\" -map \"[v]\" -an {ENC} {out}")
        else:
            sh(f"ffmpeg -nostdin -v error -y -ss {ss} -t {d} -i {D}/{src} -an -vf "
               f"\"setpts=PTS/{sp},fps=30,trim=duration={od:.3f},setsar=1,format=yuv420p\" {ENC} {out}")
    ins = " ".join(f"-i {D}/bo/pq_{s[0]}.mp4" for s in SC)
    f = [f"[{i}:v]fps=30,setpts=PTS-STARTPTS,settb=AVTB[v{i}]" for i in range(len(SC))]
    prev = "[v0]"
    for i in range(1, len(SC)):
        f.append(f"{prev}[v{i}]xfade=transition={TRANS[i]}:duration={XF}:offset={ST[i]:.3f},settb=AVTB[x{i}]")
        prev = f"[x{i}]"
    sh(f"ffmpeg -nostdin -v error -y {ins} -filter_complex \"{';'.join(f)}\" -map \"{prev}\" -r 30 {ENC} {D}/base_pq.mp4")


def badge(img, cx, cy, r, n, al, pop=1.0):
    if al <= 0.01:
        return
    r = int(r * pop)
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=GOLD + (int(255 * al),), outline=CREAM + (int(220 * al),), width=5)
    d.text((cx, cy + int(r * 0.05)), str(n), font=SER(int(r * 1.25)), fill=INK + (int(255 * al),), anchor="mm")
    img.alpha_composite(lay)


def frame_box(img, x, y, w, h, al):
    if al <= 0.01:
        return
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(lay).rectangle((x - 6, y - 6, x + w + 5, y + h + 5), outline=CREAM + (int(240 * al),), width=6)
    img.alpha_composite(lay)


def hint(img, t, t0, t1):
    """bottom pill: write the number"""
    al = a_in(t, t0 + 0.4, 0.3) * a_out(t, t1 - 0.2, 0.2)
    if al <= 0.01:
        return
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    d.rounded_rectangle((150, 1560, 930, 1650), 45, fill=(24, 20, 17, int(185 * al)))
    img.alpha_composite(lay)
    text(img, (W // 2, 1578), "Yoqqanining raqamini izohga yozing", MED(34), CREAM, al, 0, anchor="ma")


def frame(i):
    t = i / FPS
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    # hook: question over the three strips + numbers at the bottom of each strip
    if t < S_O1 + 0.3:
        al = a_out(t, S_O1 - 0.15, 0.25)
        lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        dd = ImageDraw.Draw(lay)
        for k in range(2):
            x0 = (k + 1) * (SW_ + GAP) - GAP
            dd.rectangle((x0, 0, x0 + GAP - 1, H), fill=CREAM + (int(255 * al),))
        img.alpha_composite(lay)
        topgrad(img, 900, 0.82 * al)
        grad(img, 1350, 1920, 0.6 * al)
        text(img, (W // 2, 300), NAME + " · PLISSE", MONO(26), GOLD, a_in(t, 0, 0.3) * al, 8, anchor="ma", tracking=6)
        text(img, (W // 2, 360), "Qaysi rang", SER(112), PAPER, a_in(t, 0.0, 0.3) * al, 18, anchor="ma")
        text(img, (W // 2, 480), "sizga yoqdi?", SER(112), PAPER, a_in(t, 0.1, 0.3) * al, 18, anchor="ma")
        text(img, (W // 2, 636), "1, 2 yoki 3?", SERI(86), GOLD, a_in(t, 0.6, 0.35) * al, 14, anchor="ma")
        ar = a_in(t, 0.9) * al
        if ar > 0.01:
            lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
            ImageDraw.Draw(lay).rounded_rectangle((300, 748, 780, 806), 29, fill=(24, 20, 17, int(170 * ar)))
            img.alpha_composite(lay)
        text(img, (W // 2, 756), "Какой цвет вам нравится?", MED(32), CREAM, ar, 0, anchor="ma")
        for k in range(3):
            cx = k * (SW_ + GAP) + SW_ // 2
            badge(img, cx, 1600, 62, k + 1, a_in(t, 0.35 + 0.15 * k, 0.25) * al)
    # each option: big number top-left + label, hint pill at the bottom
    for n, t0, t1 in OPTS:
        if t0 - 0.1 < t < t1 + 0.3:
            al = a_in(t, t0 + 0.1, 0.25) * a_out(t, t1 - 0.15, 0.2)
            pop = 1.0 + 0.25 * max(0.0, 1 - (t - t0 - 0.1) / 0.25) if t > t0 + 0.1 else 1.25
            topgrad(img, 560, 0.6 * al)
            badge(img, 170, 345, 82, n, al, pop)
            text(img, (282, 290), f"{n}-variant", SEMI(60), PAPER, al, 10)
            text(img, (284, 372), f"Вариант {n}", MED(32), SUB, al, 8)
            hint(img, t, t0, t1)
    # installation
    if S_INS - 0.1 < t < S_END + 0.3:
        al = a_in(t, S_INS + 0.12, 0.35) * a_out(t, S_END - 0.2, 0.22)
        grad(img, 1150, 1920, 0.85 * al)
        text(img, (86, 1430), "Rangini tanlang —", SEMI(64), PAPER, al, 14)
        text(img, (98, 1526), "qolganini o‘zimiz qilamiz.", SERI(70), GOLD,
             a_in(t, S_INS + 0.35, 0.35) * a_out(t, S_END - 0.2, 0.22), 14)
        text(img, (90, 1646), "Выберите цвет — остальное сделаем мы.", MED(30), SUB,
             a_in(t, S_INS + 0.55, 0.35) * a_out(t, S_END - 0.2, 0.22), 10)
    # end card
    if t > S_END - 0.2:
        a0 = a_in(t, S_END)
        lg = LOGO.copy()
        lg.thumbnail((380, 200))
        lg.putalpha(lg.split()[3].point(lambda v: int(v * a0)))
        img.alpha_composite(lg, ((W - lg.width) // 2, 175))
        text(img, (W // 2, 395), "Qaysi biri sizga yoqdi?", SER(64), PAPER, a_in(t, S_END + 0.15), 14, anchor="ma")
        text(img, (W // 2, 478), "Izohga raqamini yozing", SERI(64), GOLD, a_in(t, S_END + 0.3), 14, anchor="ma")
        text(img, (W // 2, 580), "Напишите номер в комментариях", MED(28), SUB, a_in(t, S_END + 0.45), 10, anchor="ma")
        for k in range(3):
            ak = a_in(t, S_END + 0.2 + 0.12 * k, 0.3)
            frame_box(img, TX[k], TY, TW, TH, ak)
            hi = t > S_END + 1.4 and int((t - S_END - 1.4) / 0.5) % 3 == k
            badge(img, TX[k] + TW // 2, TY + TH, 50, k + 1, ak, 1.15 if hi else 1.0)
        text(img, (W // 2, 1290), "Yoki deraza rasmini direktga yuboring", MED(34), (236, 228, 214),
             a_in(t, S_END + 1.0), 10, anchor="ma")
        text(img, (W // 2, 1340), "Или пришлите фото окна в директ", MED(28), SUB, a_in(t, S_END + 1.1), 10, anchor="ma")
        text(img, (W // 2, 1490), "Qo‘ng‘iroq qiling · Звоните", MED(30), SUB, a_in(t, S_END + 0.8), 8, anchor="ma")
        text(img, (W // 2, 1540), PHONE, SEMI(58), GOLD, a_in(t, S_END + 0.9), 8, anchor="ma")
    return np.asarray(img)


def render_ov():
    os.makedirs(f"{D}/ov_pq", exist_ok=True)
    idx = list(range(NF))
    with Pool(6) as p:
        for k in range(0, len(idx), 24):
            ch = idx[k:k + 24]
            for i, a in zip(ch, p.map(frame, ch)):
                Image.fromarray(a).save(f"{D}/ov_pq/{i:04d}.png", compress_level=1)


def music():
    from pop_bed import pop_bed
    pop_bed(f"{D}/bed_pq.wav", TOTAL, S_END, [S_O1 + 0.1, S_O2 + 0.1, S_O3 + 0.1])


OUTN = "classic_plisse_qaysi_rang"


def final():
    os.makedirs(f"{D}/out", exist_ok=True)
    sh(f"ffmpeg -nostdin -v error -y -i {D}/base_pq.mp4 -framerate 30 -i {D}/ov_pq/%04d.png -i {D}/bed_pq.wav "
       f"-filter_complex \"[0:v][1:v]overlay=0:0:format=auto,format=yuv420p[v];"
       f"[2:a]loudnorm=I=-15:TP=-1.5:LRA=9[a]\" -map \"[v]\" -map \"[a]\" -t {TOTAL:.3f} "
       f"-c:v libx264 -preset slow -crf 18 -pix_fmt yuv420p -color_primaries bt709 -color_trc bt709 -colorspace bt709 "
       f"-c:a aac -b:a 192k -movflags +faststart {D}/out/{OUTN}.mp4")


def cover():
    tt = 1.8
    sh(f"ffmpeg -v error -y -ss {tt} -i {D}/base_pq.mp4 -frames:v 1 {D}/cs/cb.png")
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
            sh(f"ffmpeg -v error -y -ss {tt} -i {D}/base_pq.mp4 -frames:v 1 {D}/cs/pb.png")
            b = Image.open(f"{D}/cs/pb.png").convert("RGBA")
            b.alpha_composite(Image.fromarray(frame(int(tt * FPS))))
            ims.append(b.convert("RGB").resize((360, 640)))
        c = Image.new("RGB", (365 * len(ims), 640), "white")
        for k, im in enumerate(ims):
            c.paste(im, (k * 365, 0))
        c.save(f"{D}/cs/prev_pq.jpg", quality=85)
    if what in ("ov", "all"):
        render_ov()
    if what in ("music", "all"):
        music()
    if what in ("final", "all"):
        final()
    if what in ("cover", "all"):
        cover()
