"""Qora plisse — «Parda ortida» (sales, no voice): curtain opens -> plisse, curtain closes -> other rooms -> CTA.
python3 build_p.py [base|prev t,t|ov|music|final|all]
"""
import os
import subprocess
import sys
from multiprocessing import Pool

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, "/home/claude/reels/common")
sys.path.insert(0, "/home/claude/reels/qora_plisse")
from build_b import (GOLD, INK, LOGO, MED, MONO, PAPER, SEMI, SER, SERI, a_in, a_out, check, grad,  # noqa: E402
                     text, topgrad)

D = "/home/claude/reels/qora_plisse"
W, H, FPS = 1080, 1920, 30
XF = 0.35
# name, src (video or photo), start, dur(src), speed / zoom dir for photos
SC = [
    ("p1", "st/p_open.mp4", 2.0, 8.5, 1.25),
    ("p2", "st/p_close.mp4", 0.0, 4.6, 1.0),
    ("p3", "st/sash.mp4", 0.0, 2.9, 1.0),
    ("p4", "st/niche2.mp4", 0.6, 3.0, 1.0),
    ("p5", "src/7f2e1bbb-image.jpg", 0, 2.9, "in"),
    ("p6", "src/001448d6-image.jpg", 0, 2.9, "out"),
    ("end", "src/05f5857d-image.jpg", 0, 5.4, "blur"),
]


def odur(s):
    _, src, _, d, sp = s
    return d / sp if isinstance(sp, float) else d


ST, t = [], 0.0
for s in SC:
    ST.append(t)
    t += odur(s) - XF
TOTAL = t + XF
NF = int(round(TOTAL * FPS))
REVEAL = ST[0] + (7.0 - 2.0) / 1.25 - 0.9      # curtain mostly open in p1


def sh(cmd):
    subprocess.run(cmd, shell=True, check=True)


def base():
    os.makedirs(f"{D}/bp", exist_ok=True)
    for s in SC:
        name, src, ss, d, sp = s
        out = f"{D}/bp/{name}.mp4"
        od = odur(s)
        if src.endswith(".jpg"):
            if sp == "blur":
                vf = (f"scale=1188:2112:force_original_aspect_ratio=increase,crop=1188:2112,"
                      f"zoompan=z='1.0+0.03*on/({od}*30)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=1080x1920:fps=30,"
                      f"gblur=sigma=18,eq=brightness=-0.32:saturation=0.75:contrast=0.9")
            else:
                z = f"1.0+0.07*on/({od}*30)" if sp == "in" else f"1.07-0.07*on/({od}*30)"
                vf = (f"scale=2160:3840:force_original_aspect_ratio=increase,crop=2160:3840,"
                      f"zoompan=z='{z}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=1080x1920:fps=30,"
                      f"eq=contrast=1.04:saturation=1.02,unsharp=5:5:0.3")
            sh(f"ffmpeg -nostdin -v error -y -loop 1 -i {D}/{src} -vf \"{vf},format=yuv420p\" -t {od:.3f} "
               f"-c:v libx264 -preset fast -crf 15 -pix_fmt yuv420p {out}")
        else:
            sh(f"ffmpeg -nostdin -v error -y -ss {ss} -t {d} -i {D}/{src} -an -vf "
               f"\"setpts=PTS/{sp},fps=30,trim=duration={od:.3f},setsar=1,format=yuv420p\" "
               f"-c:v libx264 -preset fast -crf 15 -pix_fmt yuv420p {out}")
    ins = " ".join(f"-i {D}/bp/{s[0]}.mp4" for s in SC)
    f = [f"[{i}:v]fps=30,setpts=PTS-STARTPTS,settb=AVTB[v{i}]" for i in range(len(SC))]
    prev = "[v0]"
    trans = {1: "fade", 2: "fade", 3: "smoothleft", 4: "smoothleft", 5: "smoothleft", 6: "fade"}
    for i in range(1, len(SC)):
        f.append(f"{prev}[v{i}]xfade=transition={trans[i]}:duration={XF}:offset={ST[i]:.3f},settb=AVTB[x{i}]")
        prev = f"[x{i}]"
    sh(f"ffmpeg -nostdin -v error -y {ins} -filter_complex \"{';'.join(f)}\" -map \"{prev}\" -r 30 "
       f"-c:v libx264 -preset fast -crf 15 -pix_fmt yuv420p {D}/base_p.mp4")


def chip(img, t, t0, t1, s):
    al = a_in(t, t0) * a_out(t, t1)
    if al <= 0.01:
        return
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    f = MONO(26)
    w = sum(f.getlength(c) for c in s) + 5 * (len(s) - 1)
    d.rounded_rectangle((80, 290, 80 + w + 48, 346), 28, fill=(20, 18, 16, int(170 * al)),
                        outline=GOLD + (int(220 * al),), width=2)
    img.alpha_composite(lay)
    text(img, (104, 304), s, f, GOLD, al, 0, tracking=5)


def frame(i):
    t = i / FPS
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    s1, s2, s3, s4, s5, s6, s7 = ST
    # P1 hook on closed curtain, then reveal line
    if t < s2 + 0.3:
        al = a_out(t, REVEAL - 0.5)
        topgrad(img, 820, 0.5 * al)
        chip(img, t, 0.0, s2 - 0.2, "01 · YOTOQXONA")
        text(img, (86, 390), "Parda ortida", SER(108), PAPER, a_in(t, 0.05) * al, 18)
        text(img, (86, 505), "nima bor?", SERI(108), GOLD, a_in(t, 0.3) * al, 18)
        text(img, (90, 640), "Что за шторой?", MED(32), (220, 213, 200), a_in(t, 0.6) * al, 10)
        a2 = a_in(t, REVEAL) * a_out(t, s2 - 0.1)
        grad(img, 1150, 1900, 0.8 * a2)
        text(img, (86, 1420), "Qora romga —", SER(96), PAPER, a2, 18)
        text(img, (86, 1528), "mos plisse.", SERI(96), GOLD, a_in(t, REVEAL + 0.25) * a_out(t, s2 - 0.1), 18)
        text(img, (90, 1650), "Har bir tabaqaga alohida · На каждую створку", MED(30), (215, 208, 196),
             a_in(t, REVEAL + 0.5) * a_out(t, s2 - 0.1), 10)
    # P2 curtain closes
    if s2 - 0.1 < t < s3 + 0.3:
        al = a_out(t, s3 - 0.25)
        grad(img, 1150, 1900, 0.8 * al)
        text(img, (86, 1410), "Parda — chiroy uchun.", SEMI(66), PAPER, a_in(t, s2 + 0.3) * al, 16)
        text(img, (86, 1500), "Plisse — har kuni.", SERI(92), GOLD, a_in(t, s2 + 1.4) * al, 16)
        text(img, (90, 1622), "Шторы — для красоты, плиссе — на каждый день.", MED(30), (215, 208, 196),
             a_in(t, s2 + 1.6) * al, 10)
    # P3 sash opens with plisse
    if s3 - 0.1 < t < s4 + 0.3:
        al = a_out(t, s4 - 0.1)
        grad(img, 1180, 1900, 0.82 * al)
        text(img, (86, 1440), "Deraza ochilsa —", SEMI(66), PAPER, a_in(t, s3 + 0.25) * al, 16)
        text(img, (86, 1528), "plisse u bilan birga.", SERI(88), GOLD, a_in(t, s3 + 0.5) * al, 16)
        text(img, (90, 1645), "Открывается вместе с окном.", MED(30), (215, 208, 196), a_in(t, s3 + 0.7) * al, 10)
    # P4-P6 rooms
    for (t0, t1, lab, big, ru) in [(s4, s5, "02 · KABINET", "Ish stoli yonida", "Кабинет"),
                                   (s5, s6, "03 · HAMMOM", "Hammomda ham", "Ванная"),
                                   (s6, s7, "04 · DERAZA TOKCHASI", "Dam olish burchagi", "Уголок у окна")]:
        if t0 - 0.1 < t < t1 + 0.3:
            al = a_out(t, t1 - 0.1)
            chip(img, t, t0 + 0.1, t1 - 0.1, lab)
            grad(img, 1350, 1900, 0.7 * al)
            text(img, (86, 1560), big, SERI(84), PAPER, a_in(t, t0 + 0.25) * al, 16)
            text(img, (90, 1670), ru, MED(30), (215, 208, 196), a_in(t, t0 + 0.45) * al, 10)
    # END card
    if t > s7 - 0.2:
        a0 = a_in(t, s7)
        lg = LOGO.copy()
        lg.thumbnail((380, 180))
        lg.putalpha(lg.split()[3].point(lambda v: int(v * a0)))
        img.alpha_composite(lg, ((W - lg.width) // 2, 300))
        text(img, (W // 2, 500), "Sizga qaysi xona yoqdi?", SER(70), PAPER, a_in(t, s7 + 0.15), 14, anchor="ma")
        text(img, (W // 2, 590), "Izohga raqamini yozing: 1 · 2 · 3 · 4", MED(36), GOLD, a_in(t, s7 + 0.35), 10, anchor="ma")
        check(img, 150, 720, a_in(t, s7 + 0.6), "O‘lchov va o‘rnatish", "bepul · Замер и установка бесплатно")
        check(img, 150, 870, a_in(t, s7 + 0.8), "3 kunda tayyor", "o‘lchovdan keyin · Готово за 3 дня")
        check(img, 150, 1020, a_in(t, s7 + 1.0), "1 yil kafolat", "Гарантия 1 год")
        af = a_in(t, s7 + 1.4)
        if af > 0.01:
            lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
            d = ImageDraw.Draw(lay)
            d.rounded_rectangle((150, 1215, 930, 1325), 55, fill=(255, 255, 255, int(235 * af)))
            n = int(max(0, min(4, (t - s7 - 1.7) / 0.15)))
            word = "NARX"[:n]
            d.text((210, 1270), word, font=SEMI(56), fill=INK + (int(255 * af),), anchor="lm")
            if int(t * 2) % 2 == 0 and n < 4:
                cx = 210 + SEMI(56).getlength(word) + 6
                d.line([(cx, 1240), (cx, 1300)], fill=(214, 140, 60, int(255 * af)), width=4)
            d.rounded_rectangle((780, 1235, 912, 1305), 35, fill=GOLD + (int(255 * af),))
            d.text((846, 1270), "→", font=SEMI(44), fill=INK + (int(255 * af),), anchor="mm")
            img.alpha_composite(lay)
        text(img, (W // 2, 1360), "Narx uchun izohga NARX yozing — direktga yuboramiz", MED(32), (230, 222, 208),
             a_in(t, s7 + 2.3), 10, anchor="ma")
        text(img, (W // 2, 1408), "Напишите NARX — пришлём цены в директ", MED(28), (200, 193, 181),
             a_in(t, s7 + 2.5), 10, anchor="ma")
        text(img, (W // 2, 1560), "+998 33 751 11 88  ·  @imperial_jalyuzi_uz", MED(28), GOLD, a_in(t, s7 + 0.8), 8,
             anchor="ma")
    return np.asarray(img)


def render_ov():
    os.makedirs(f"{D}/ovp", exist_ok=True)
    idx = list(range(NF))
    with Pool(6) as p:
        for k in range(0, len(idx), 24):
            ch = idx[k:k + 24]
            for i, a in zip(ch, p.map(frame, ch)):
                Image.fromarray(a).save(f"{D}/ovp/{i:04d}.png", compress_level=1)


def music():
    from handpan_bed import handpan_bed
    beat = 0.75
    prog = [[50, 57, 62, 65, 69], [46, 58, 62, 65, 70], [48, 60, 64, 67, 72], [45, 57, 61, 64, 69]]
    pads = []
    notes = []
    t, k = 0.0, 0
    patt = [(0, 1, 0.55), (0.75, 2, 0.38), (1.125, 3, 0.30), (1.5, 4, 0.42), (2.25, 3, 0.32), (2.625, 2, 0.28)]
    while t < TOTAL - 1.0:
        ch = prog[k % 4]
        pads.append((t, [ch[0] + 12, ch[2], ch[3]]))
        for dt, idx, v in patt:
            if t + dt < TOTAL - 1.2:
                notes.append((t + dt, ch[idx], v))
        t += 4 * beat
        k += 1
    plan = dict(notes=notes, pads=pads, ding=[REVEAL, ST[6]], whoosh=[(0.9, 3.2), (ST[1] + 0.4, 3.6)])
    handpan_bed(f"{D}/bed_p.wav", TOTAL, plan)


def final():
    os.makedirs(f"{D}/out", exist_ok=True)
    sh(f"ffmpeg -nostdin -v error -y -i {D}/base_p.mp4 -framerate 30 -i {D}/ovp/%04d.png -i {D}/bed_p.wav "
       f"-filter_complex \"[0:v][1:v]overlay=0:0:format=auto,format=yuv420p[v];"
       f"[2:a]loudnorm=I=-15:TP=-1.5:LRA=9[a]\" -map \"[v]\" -map \"[a]\" -t {TOTAL:.3f} "
       f"-c:v libx264 -preset slow -crf 18 -pix_fmt yuv420p -color_primaries bt709 -color_trc bt709 -colorspace bt709 "
       f"-c:a aac -b:a 192k -movflags +faststart {D}/out/imperial_parda_ortida.mp4")


if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else "all"
    print("starts", [round(x, 2) for x in ST], "reveal", round(REVEAL, 2), "total", round(TOTAL, 2))
    if what in ("base", "all"):
        base()
    if what == "prev":
        ims = []
        for tt in map(float, sys.argv[2].split(",")):
            sh(f"ffmpeg -v error -y -ss {tt} -i {D}/base_p.mp4 -frames:v 1 {D}/cs/pb.png")
            b = Image.open(f"{D}/cs/pb.png").convert("RGBA")
            b.alpha_composite(Image.fromarray(frame(int(tt * FPS))))
            ims.append(b.convert("RGB").resize((360, 640)))
        c = Image.new("RGB", (365 * len(ims), 640), "white")
        for k, im in enumerate(ims):
            c.paste(im, (k * 365, 0))
        c.save(f"{D}/cs/prev_p.jpg", quality=85)
    if what in ("ov", "all"):
        render_ov()
    if what in ("music", "all"):
        music()
    if what in ("final", "all"):
        final()
