"""«Bitta uy — ikki xil jalyuzi» (kombo + plisse, sales, no voice): choice format, comment 1 or 2.
python3 build_c.py [base|prev t,t|ov|music|final|all]
"""
import os
import subprocess
import sys
from multiprocessing import Pool

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, "/home/claude/reels/common")
sys.path.insert(0, "/home/claude/reels/qora_plisse")
from build_b import GOLD, INK, LOGO, MED, MONO, PAPER, SEMI, SER, SERI, a_in, a_out, check, grad, text, topgrad  # noqa: E402
from build_p import chip  # noqa: E402

D = "/home/claude/reels/oq_rom"
W, H, FPS = 1080, 1920, 30
XF = 0.35
KP = "src/kombo_photo.jpg"
PP = "src/plisse_photo.jpg"
SC = [
    ("h", "st/h.mp4", 0.0, 2.6, 0.85),
    ("k1", "st/k1.mp4", 0.1, 2.0, 0.8),
    ("k2", "kphoto", 0, 3.3, None),
    ("p1", "st/p1.mp4", 0.0, 1.6, 0.8),
    ("p2", "st/p2.mp4", 0.0, 1.95, 0.85),
    ("p3", "st/p3.mp4", 0.0, 3.0, 1.0),
    ("split", "split", 0, 4.4, None),
    ("end", "endbg", 0, 5.4, None),
]


def odur(s):
    return s[3] / s[4] if isinstance(s[4], float) else s[3]


ST, _t = [], 0.0
for s in SC:
    ST.append(_t)
    _t += odur(s) - XF
TOTAL = _t + XF
NF = int(round(TOTAL * FPS))
ENC = "-c:v libx264 -preset fast -crf 15 -pix_fmt yuv420p"


def sh(cmd):
    subprocess.run(cmd, shell=True, check=True)


def zp(z0, z1, od, w=1080, h=1920):
    return (f"zoompan=z='{z0}+({z1}-{z0})*on/({od}*30)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s={w}x{h}:fps=30")


GRADE = "eq=contrast=1.04:saturation=1.03,unsharp=5:5:0.3"


def base():
    os.makedirs(f"{D}/bc", exist_ok=True)
    for s in SC:
        name, src, ss, d, sp = s
        out = f"{D}/bc/{name}.mp4"
        od = odur(s)
        if src == "kphoto":      # crop out the cluttered sill, slow push-in
            vf = f"crop=810:1440:345:150,scale=2160:3840,{zp(1.0, 1.08, od)},{GRADE}"
            sh(f"ffmpeg -nostdin -v error -y -loop 1 -i {D}/{KP} -vf \"{vf},format=yuv420p\" -t {od:.3f} {ENC} {out}")
        elif src == "split":
            fc = (f"[0:v]crop=405:1440:547:150,scale=1080:3840,{zp(1.0, 1.05, od, 540, 1920)},{GRADE}[l];"
                  f"[1:v]crop=430:1530:700:250,scale=1080:3840,{zp(1.05, 1.0, od, 540, 1920)},{GRADE}[r];"
                  f"[l][r]hstack=inputs=2,format=yuv420p[v]")
            sh(f"ffmpeg -nostdin -v error -y -loop 1 -i {D}/{KP} -loop 1 -i {D}/{PP} -filter_complex \"{fc}\" "
               f"-map \"[v]\" -t {od:.3f} {ENC} {out}")
        elif src == "endbg":
            vf = (f"crop=956:1700:85:0,scale=1188:2112,{zp(1.0, 1.03, od)},gblur=sigma=18,"
                  f"eq=brightness=-0.30:saturation=0.75:contrast=0.9")
            sh(f"ffmpeg -nostdin -v error -y -loop 1 -i {D}/{PP} -vf \"{vf},format=yuv420p\" -t {od:.3f} {ENC} {out}")
        else:
            sh(f"ffmpeg -nostdin -v error -y -ss {ss} -t {d} -i {D}/{src} -an -vf "
               f"\"setpts=PTS/{sp},fps=30,trim=duration={od:.3f},setsar=1,format=yuv420p\" {ENC} {out}")
    ins = " ".join(f"-i {D}/bc/{s[0]}.mp4" for s in SC)
    f = [f"[{i}:v]fps=30,setpts=PTS-STARTPTS,settb=AVTB[v{i}]" for i in range(len(SC))]
    prev = "[v0]"
    trans = {1: "fade", 2: "smoothleft", 3: "fade", 4: "smoothleft", 5: "smoothleft", 6: "fade", 7: "fade"}
    for i in range(1, len(SC)):
        f.append(f"{prev}[v{i}]xfade=transition={trans[i]}:duration={XF}:offset={ST[i]:.3f},settb=AVTB[x{i}]")
        prev = f"[x{i}]"
    sh(f"ffmpeg -nostdin -v error -y {ins} -filter_complex \"{';'.join(f)}\" -map \"{prev}\" -r 30 {ENC} {D}/base_c.mp4")


def frame(i):
    t = i / FPS
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    s_h, s_k1, s_k2, s_p1, s_p2, s_p3, s_sp, s_end = ST
    # hook
    if t < s_k1 + 0.3:
        al = a_out(t, s_k1 - 0.1)
        topgrad(img, 1050, 0.8 * al)
        text(img, (86, 300), "IMPERIAL · TOSHKENT", MONO(26), GOLD, a_in(t, 0) * al, 8, tracking=6)
        text(img, (86, 360), "Bitta uy —", SER(110), PAPER, a_in(t, 0.05) * al, 18)
        text(img, (86, 478), "ikki xil jalyuzi.", SERI(110), GOLD, a_in(t, 0.3) * al, 18)
        text(img, (90, 620), "Qaysi biri sizga mos? · Одна квартира — два решения", MED(32), (225, 218, 205),
             a_in(t, 0.9) * al, 10)
    # 01 kombo
    if s_k1 - 0.1 < t < s_p1 + 0.3:
        al = a_out(t, s_p1 - 0.1)
        chip(img, t, s_k1 + 0.1, s_p1 - 0.1, "01 · KOMBO (KUN-TUN)")
        grad(img, 1150, 1900, 0.82 * al)
        text(img, (86, 1380), "Katta derazaga —", SEMI(66), PAPER, a_in(t, s_k1 + 0.3) * al, 16)
        text(img, (86, 1462), "kombo.", SERI(110), GOLD, a_in(t, s_k1 + 0.6) * al, 16)
        text(img, (90, 1610), "Yorug‘likni bir harakatda sozlaysiz.", MED(36), PAPER, a_in(t, s_k2 + 0.2) * al, 10)
        text(img, (90, 1662), "Зебра «день-ночь» — свет одним движением.", MED(28), (205, 198, 186),
             a_in(t, s_k2 + 0.4) * al, 10)
    # 02 plisse
    if s_p1 - 0.1 < t < s_sp + 0.3:
        al = a_out(t, s_sp - 0.1)
        chip(img, t, s_p1 + 0.1, s_sp - 0.1, "02 · PLISSE")
        grad(img, 1150, 1900, 0.82 * al)
        text(img, (86, 1380), "Ochiladigan tabaqaga —", SEMI(66), PAPER, a_in(t, s_p1 + 0.3) * al, 16)
        text(img, (86, 1462), "plisse.", SERI(110), GOLD, a_in(t, s_p1 + 0.6) * al, 16)
        text(img, (90, 1610), "Har bir tabaqaga alohida — deraza bilan birga ochiladi.", MED(32), PAPER,
             a_in(t, s_p2 + 0.2) * al, 10)
        text(img, (90, 1660), "Плиссе на каждую створку — открывается вместе с окном.", MED(28), (205, 198, 186),
             a_in(t, s_p2 + 0.4) * al, 10)
    # split choice
    if s_sp - 0.1 < t < s_end + 0.3:
        al = a_out(t, s_end - 0.1)
        topgrad(img, 820, 0.85 * al)
        grad(img, 1380, 1920, 0.85 * al)
        lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(lay)
        ad = a_in(t, s_sp + 0.2) * al
        d.rectangle((538, int(1920 * (1 - ad)), 542, 1920), fill=GOLD + (int(255 * ad),))
        for k, (cx, num, lab) in enumerate([(270, "1", "KOMBO"), (810, "2", "PLISSE")]):
            ak = a_in(t, s_sp + 0.5 + 0.2 * k) * al
            if ak > 0.01:
                yo = 10 * (1 - ak)
                d.ellipse((cx - 70, 1420 + yo, cx + 70, 1560 + yo), fill=(20, 18, 16, int(170 * ak)),
                          outline=GOLD + (int(255 * ak),), width=4)
                d.text((cx, 1490 + yo), num, font=SER(92), fill=PAPER + (int(255 * ak),), anchor="mm")
                d.text((cx, 1600 + yo), lab, font=MONO(34), fill=GOLD + (int(255 * ak),), anchor="mt")
        img.alpha_composite(lay)
        text(img, (W // 2, 300), "Sizga qaysi biri", SER(92), PAPER, a_in(t, s_sp + 0.1) * al, 14, anchor="ma")
        text(img, (W // 2, 405), "yoqdi?", SERI(104), GOLD, a_in(t, s_sp + 0.3) * al, 14, anchor="ma")
        text(img, (W // 2, 1700), "Izohga 1 yoki 2 yozing 👇".replace(" 👇", ""), SEMI(50), PAPER,
             a_in(t, s_sp + 1.0) * al, 10, anchor="ma")
        text(img, (W // 2, 1770), "Напишите 1 или 2 в комментариях", MED(30), (215, 208, 196),
             a_in(t, s_sp + 1.2) * al, 8, anchor="ma")
    # end card
    if t > s_end - 0.2:
        a0 = a_in(t, s_end)
        lg = LOGO.copy()
        lg.thumbnail((380, 180))
        lg.putalpha(lg.split()[3].point(lambda v: int(v * a0)))
        img.alpha_composite(lg, ((W - lg.width) // 2, 300))
        text(img, (W // 2, 500), "Kombo yoki plisse —", SER(76), PAPER, a_in(t, s_end + 0.15), 14, anchor="ma")
        text(img, (W // 2, 590), "derazangizga o‘lchab.", SERI(80), GOLD, a_in(t, s_end + 0.3), 14, anchor="ma")
        check(img, 150, 740, a_in(t, s_end + 0.5), "O‘lchov va o‘rnatish", "bepul · Замер и установка бесплатно")
        check(img, 150, 890, a_in(t, s_end + 0.7), "3 kunda tayyor", "o‘lchovdan keyin · Готово за 3 дня")
        check(img, 150, 1040, a_in(t, s_end + 0.9), "1 yil kafolat", "Гарантия 1 год")
        af = a_in(t, s_end + 1.3)
        if af > 0.01:
            lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
            d = ImageDraw.Draw(lay)
            d.rounded_rectangle((150, 1235, 930, 1345), 55, fill=(255, 255, 255, int(235 * af)))
            n = int(max(0, min(4, (t - s_end - 1.6) / 0.15)))
            word = "NARX"[:n]
            d.text((210, 1290), word, font=SEMI(56), fill=INK + (int(255 * af),), anchor="lm")
            if int(t * 2) % 2 == 0 and n < 4:
                cx = 210 + SEMI(56).getlength(word) + 6
                d.line([(cx, 1260), (cx, 1320)], fill=(214, 140, 60, int(255 * af)), width=4)
            d.rounded_rectangle((780, 1255, 912, 1325), 35, fill=GOLD + (int(255 * af),))
            d.text((846, 1290), "→", font=SEMI(44), fill=INK + (int(255 * af),), anchor="mm")
            img.alpha_composite(lay)
        text(img, (W // 2, 1385), "Narx uchun izohga NARX yozing — direktga yuboramiz", MED(32), (230, 222, 208),
             a_in(t, s_end + 2.2), 10, anchor="ma")
        text(img, (W // 2, 1433), "Напишите NARX — пришлём цены в директ", MED(28), (200, 193, 181),
             a_in(t, s_end + 2.4), 10, anchor="ma")
        text(img, (W // 2, 1580), "+998 33 751 11 88  ·  @imperial_jalyuzi_uz", MED(28), GOLD, a_in(t, s_end + 0.8), 8,
             anchor="ma")
    return np.asarray(img)


def render_ov():
    os.makedirs(f"{D}/ovc", exist_ok=True)
    idx = list(range(NF))
    with Pool(6) as p:
        for k in range(0, len(idx), 24):
            ch = idx[k:k + 24]
            for i, a in zip(ch, p.map(frame, ch)):
                Image.fromarray(a).save(f"{D}/ovc/{i:04d}.png", compress_level=1)


def music():
    from marimba_bed import marimba_bed, BEAT
    s = ST
    plan = dict(chords=[(0, 43, [55, 59, 62]), (s[1], 40, [52, 55, 59]), (s[2], 36, [48, 52, 55]),
                        (s[3], 38, [50, 54, 57]), (s[5], 43, [55, 59, 62]), (s[6], 40, [52, 55, 59]),
                        (s[7], 36, [48, 52, 55, 59]), (s[7] + 4 * BEAT, 38, [50, 54, 57, 62])],
                groove=(s[1], s[7] + 3.0), hits=[(s[1], 67), (s[3], 71), (s[6], 74)])
    marimba_bed(f"{D}/bed_c.wav", TOTAL, plan)


def final():
    os.makedirs(f"{D}/out", exist_ok=True)
    sh(f"ffmpeg -nostdin -v error -y -i {D}/base_c.mp4 -framerate 30 -i {D}/ovc/%04d.png -i {D}/bed_c.wav "
       f"-filter_complex \"[0:v][1:v]overlay=0:0:format=auto,format=yuv420p[v];"
       f"[2:a]loudnorm=I=-15:TP=-1.5:LRA=9[a]\" -map \"[v]\" -map \"[a]\" -t {TOTAL:.3f} "
       f"-c:v libx264 -preset slow -crf 18 -pix_fmt yuv420p -color_primaries bt709 -color_trc bt709 -colorspace bt709 "
       f"-c:a aac -b:a 192k -movflags +faststart {D}/out/imperial_kombo_yoki_plisse.mp4")


if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else "all"
    print("starts", [round(x, 2) for x in ST], "total", round(TOTAL, 2))
    if what in ("base", "all"):
        base()
    if what == "prev":
        ims = []
        for tt in map(float, sys.argv[2].split(",")):
            sh(f"ffmpeg -v error -y -ss {tt} -i {D}/base_c.mp4 -frames:v 1 {D}/cs/pb.png")
            b = Image.open(f"{D}/cs/pb.png").convert("RGBA")
            b.alpha_composite(Image.fromarray(frame(int(tt * FPS))))
            ims.append(b.convert("RGB").resize((300, 533)))
        c = Image.new("RGB", (305 * len(ims), 533), "white")
        for k, im in enumerate(ims):
            c.paste(im, (k * 305, 0))
        c.save(f"{D}/cs/prev_c.jpg", quality=85)
    if what in ("ov", "all"):
        render_ov()
    if what in ("music", "all"):
        music()
    if what in ("final", "all"):
        final()
