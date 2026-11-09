"""«Plisse — 0 dan tayyorgacha» (installation, sales, no voice): teaser -> 4 steps with a top progress bar -> reveal -> CTA.
python3 build_o.py [base|prev t,t|ov|music|final|all]
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
sys.path.insert(0, "/home/claude/reels/common/brand")
from brand import LOGO, LOGO_BOX, NAME, PHONE  # noqa: E402,F811

D = "/home/claude/reels/ornatish"
W, H, FPS = 1080, 1920, 30
XF = 0.3
SC = [
    ("hk", "st/hk.mp4", 0.0, 2.0, 1.0),
    ("u1", "st/u1.mp4", 0.2, 3.2, 1.2),
    ("m1", "st/m1.mp4", 0.0, 4.4, 1.2),
    ("m2", "st/m2.mp4", 0.2, 3.4, 1.2),
    ("a1", "st/a1.mp4", 0.0, 3.6, 1.15),
    ("a2", "st/a2.mp4", 0.3, 3.2, 1.15),
    ("f2", "st/f2.mp4", 0.0, 2.6, 0.85),
    ("f3", "st/f3.mp4", 0.0, 3.6, 0.85),
    ("end", "endbg", 0, 5.4, None),
]
TRANS = {1: "fadeblack", 2: "smoothleft", 3: "fade", 4: "smoothleft", 5: "fade", 6: "fadewhite", 7: "fade", 8: "fade"}


def odur(s):
    return s[3] / s[4] if isinstance(s[4], float) else s[3]


ST, _t = [], 0.0
for s in SC:
    ST.append(_t)
    _t += odur(s) - XF
TOTAL = _t + XF
NF = int(round(TOTAL * FPS))
ENC = "-c:v libx264 -preset fast -crf 15 -pix_fmt yuv420p"
S_HK, S_U1, S_M1, S_M2, S_A1, S_A2, S_F2, S_F3, S_END = ST
STEPS = [(S_U1, S_M1, "01", "Qadoqdan chiqaramiz", "Распаковываем"),
         (S_M1, S_A1, "02", "Romga mahkamlaymiz", "Крепим к раме"),
         (S_A1, S_F2, "03", "Pastini sozlaymiz", "Настраиваем низ"),
         (S_F2, S_END, "04", "Tayyor.", "Готово.")]
LABS = ["Qadoq", "Mahkamlash", "Sozlash", "Tayyor"]


def sh(cmd):
    subprocess.run(cmd, shell=True, check=True)


def base():
    os.makedirs(f"{D}/bo", exist_ok=True)
    for s in SC:
        name, src, ss, d, sp = s
        out = f"{D}/bo/{name}.mp4"
        od = odur(s)
        if src == "endbg":
            sh(f"ffmpeg -nostdin -v error -y -ss 9.0 -i {D}/st/f3.mp4 -vf \"tpad=stop_mode=clone:stop_duration={od},"
               f"trim=duration={od:.3f},gblur=sigma=18,eq=brightness=-0.30:saturation=0.75:contrast=0.9,setpts=PTS-STARTPTS,"
               f"fps=30,format=yuv420p\" -an {ENC} {out}" if False else
               f"ffmpeg -nostdin -v error -y -sseof -0.2 -i {D}/st/f3.mp4 -vf \"tpad=stop_mode=clone:stop_duration={od + 1},"
               f"trim=duration={od:.3f},setpts=PTS-STARTPTS,gblur=sigma=18,eq=brightness=-0.30:saturation=0.75:contrast=0.9,"
               f"fps=30,format=yuv420p\" -an {ENC} {out}")
        else:
            sh(f"ffmpeg -nostdin -v error -y -ss {ss} -t {d} -i {D}/{src} -an -vf "
               f"\"setpts=PTS/{sp},fps=30,trim=duration={od:.3f},setsar=1,format=yuv420p\" {ENC} {out}")
    ins = " ".join(f"-i {D}/bo/{s[0]}.mp4" for s in SC)
    f = [f"[{i}:v]fps=30,setpts=PTS-STARTPTS,settb=AVTB[v{i}]" for i in range(len(SC))]
    prev = "[v0]"
    for i in range(1, len(SC)):
        f.append(f"{prev}[v{i}]xfade=transition={TRANS[i]}:duration={XF}:offset={ST[i]:.3f},settb=AVTB[x{i}]")
        prev = f"[x{i}]"
    sh(f"ffmpeg -nostdin -v error -y {ins} -filter_complex \"{';'.join(f)}\" -map \"{prev}\" -r 30 {ENC} {D}/base_o.mp4")


def progress(img, t, al):
    if al <= 0.01:
        return
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    x0, x1, y = 86, 994, 300
    gap = 14
    segw = (x1 - x0 - 3 * gap) / 4
    for k, (t0, t1, *_r) in enumerate(STEPS):
        sx = x0 + k * (segw + gap)
        d.rounded_rectangle((sx, y, sx + segw, y + 10), 5, fill=(255, 255, 255, int(70 * al)))
        fr = min(1, max(0, (t - t0) / max(0.01, (t1 - t0) * (0.25 if k == 3 else 1.0))))
        if fr > 0:
            d.rounded_rectangle((sx, y, sx + segw * fr, y + 10), 5, fill=GOLD + (int(255 * al),))
        cur = t0 <= t < t1
        col = (GOLD if (cur or t >= t1) else (220, 214, 202)) + (int(255 * al * (1 if cur or t >= t1 else 0.65)),)
        f = MONO(22)
        s = f"{k + 1:02d} {LABS[k].upper()}"
        d.text((sx, y + 24), s, font=f, fill=col)
    img.alpha_composite(lay)


def frame(i):
    t = i / FPS
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    # teaser
    if t < S_U1 + 0.3:
        al = a_out(t, S_U1 - 0.15, 0.2)
        topgrad(img, 1000, 0.75 * al)
        text(img, (86, 300), NAME + " · PLISSE", MONO(26), GOLD, a_in(t, 0) * al, 8, tracking=6)
        text(img, (86, 360), "0 dan", SER(130), PAPER, a_in(t, 0.05, 0.35) * al, 18)
        text(img, (86, 495), "tayyorgacha.", SERI(130), GOLD, a_in(t, 0.25, 0.35) * al, 18)
        text(img, (90, 655), "Qanday o‘rnatamiz — oxirigacha ko‘ring.", MED(36), PAPER, a_in(t, 0.7) * al, 10)
        text(img, (90, 705), "Как мы устанавливаем — от нуля до готового.", MED(28), (220, 213, 200), a_in(t, 0.9) * al, 10)
    # steps
    if S_U1 - 0.1 < t < S_END + 0.2:
        al = a_in(t, S_U1, 0.3) * a_out(t, S_END - 0.15)
        topgrad(img, 520, 0.6 * al)
        progress(img, t, al)
        for t0, t1, num, uz, ru in STEPS:
            if t0 - 0.1 < t < t1 + 0.25:
                a2 = a_in(t, t0 + 0.05, 0.35) * a_out(t, t1 - 0.12, 0.22)
                if num == "04":
                    a2 = a_in(t, t0 + 0.15, 0.35) * a_out(t, S_F3 - 0.05, 0.25)
                grad(img, 1200, 1920, (0.92 if num == "04" else 0.8) * a2)
                text(img, (86, 1440), num, MONO(44), GOLD, a2, 12, tracking=4)
                text(img, (86, 1500), uz, SER(96) if num == "04" else SER(84), PAPER, a2, 16)
                text(img, (90, 1615), ru, MED(32), (215, 208, 196), a2, 10)
        if S_F3 - 0.1 < t < S_END + 0.2:
            a3 = a_in(t, S_F3 + 0.1) * a_out(t, S_END - 0.1)
            grad(img, 1250, 1920, 0.8 * a3)
            text(img, (86, 1440), "04 · TAYYOR", MONO(30), GOLD, a3, 10, tracking=5)
            text(img, (86, 1495), "Har bir tabaqaga alohida —", SEMI(58), PAPER, a3, 14)
            text(img, (86, 1570), "deraza bilan birga ochiladi.", SERI(76), GOLD, a_in(t, S_F3 + 0.35) * a_out(t, S_END - 0.1), 14)
            text(img, (90, 1680), "На каждую створку — открывается вместе с окном.", MED(30), (215, 208, 196),
                 a_in(t, S_F3 + 0.6) * a_out(t, S_END - 0.1), 10)
    # end card
    if t > S_END - 0.2:
        a0 = a_in(t, S_END)
        lg = LOGO.copy()
        lg.thumbnail(LOGO_BOX)
        lg.putalpha(lg.split()[3].point(lambda v: int(v * a0)))
        img.alpha_composite(lg, ((W - lg.width) // 2, 265))
        text(img, (W // 2, 500), "Siz faqat tanlaysiz —", SER(76), PAPER, a_in(t, S_END + 0.15), 14, anchor="ma")
        text(img, (W // 2, 590), "qolganini biz qilamiz.", SERI(80), GOLD, a_in(t, S_END + 0.3), 14, anchor="ma")
        check(img, 150, 740, a_in(t, S_END + 0.5), "O‘lchov va o‘rnatish", "bepul · Замер и установка бесплатно")
        check(img, 150, 890, a_in(t, S_END + 0.7), "3 kunda tayyor", "o‘lchovdan keyin · Готово за 3 дня")
        check(img, 150, 1040, a_in(t, S_END + 0.9), "1 yil kafolat", "Гарантия 1 год")
        af = a_in(t, S_END + 1.3)
        if af > 0.01:
            lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
            d = ImageDraw.Draw(lay)
            d.rounded_rectangle((150, 1235, 930, 1345), 55, fill=(255, 255, 255, int(235 * af)))
            n = int(max(0, min(4, (t - S_END - 1.6) / 0.15)))
            word = "NARX"[:n]
            d.text((210, 1290), word, font=SEMI(56), fill=INK + (int(255 * af),), anchor="lm")
            if int(t * 2) % 2 == 0 and n < 4:
                cx = 210 + SEMI(56).getlength(word) + 6
                d.line([(cx, 1260), (cx, 1320)], fill=(214, 140, 60, int(255 * af)), width=4)
            d.rounded_rectangle((780, 1255, 912, 1325), 35, fill=GOLD + (int(255 * af),))
            d.text((846, 1290), "→", font=SEMI(44), fill=INK + (int(255 * af),), anchor="mm")
            img.alpha_composite(lay)
        text(img, (W // 2, 1385), "Narx uchun izohga NARX yozing — direktga yuboramiz", MED(32), (230, 222, 208),
             a_in(t, S_END + 2.2), 10, anchor="ma")
        text(img, (W // 2, 1433), "Напишите NARX — пришлём цены в директ", MED(28), (200, 193, 181),
             a_in(t, S_END + 2.4), 10, anchor="ma")
        text(img, (W // 2, 1560), "📞".replace("📞", "") + PHONE, SEMI(46), GOLD, a_in(t, S_END + 0.8), 8,
             anchor="ma")
    return np.asarray(img)


def render_ov():
    os.makedirs(f"{D}/ovo", exist_ok=True)
    idx = list(range(NF))
    with Pool(6) as p:
        for k in range(0, len(idx), 24):
            ch = idx[k:k + 24]
            for i, a in zip(ch, p.map(frame, ch)):
                Image.fromarray(a).save(f"{D}/ovo/{i:04d}.png", compress_level=1)


def music():
    from tick_bed import tick_bed
    plan = dict(steps=[S_U1, S_M1, S_A1], reveal=S_F2,
                chords=[(0, 45, [57, 60, 64]), (S_M1, 41, [53, 57, 60]), (S_A1, 43, [55, 59, 62]),
                        (S_A2, 40, [52, 55, 59]), (S_F2, 48, [60, 64, 67, 71])])
    tick_bed(f"{D}/bed_o.wav", TOTAL, plan)


def final():
    os.makedirs(f"{D}/out", exist_ok=True)
    sh(f"ffmpeg -nostdin -v error -y -i {D}/base_o.mp4 -framerate 30 -i {D}/ovo/%04d.png -i {D}/bed_o.wav "
       f"-filter_complex \"[0:v][1:v]overlay=0:0:format=auto,format=yuv420p[v];"
       f"[2:a]loudnorm=I=-15:TP=-1.5:LRA=9[a]\" -map \"[v]\" -map \"[a]\" -t {TOTAL:.3f} "
       f"-c:v libx264 -preset slow -crf 18 -pix_fmt yuv420p -color_primaries bt709 -color_trc bt709 -colorspace bt709 "
       f"-c:a aac -b:a 192k -movflags +faststart {D}/out/classic_plisse_0dan_tayyorgacha.mp4")


if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else "all"
    print("starts", [round(x, 2) for x in ST], "total", round(TOTAL, 2))
    if what in ("base", "all"):
        base()
    if what == "prev":
        ims = []
        for tt in map(float, sys.argv[2].split(",")):
            sh(f"ffmpeg -v error -y -ss {tt} -i {D}/base_o.mp4 -frames:v 1 {D}/cs/pb.png")
            b = Image.open(f"{D}/cs/pb.png").convert("RGBA")
            b.alpha_composite(Image.fromarray(frame(int(tt * FPS))))
            ims.append(b.convert("RGB").resize((300, 533)))
        c = Image.new("RGB", (305 * len(ims), 533), "white")
        for k, im in enumerate(ims):
            c.paste(im, (k * 305, 0))
        c.save(f"{D}/cs/prev_o.jpg", quality=85)
    if what in ("ov", "all"):
        render_ov()
    if what in ("music", "all"):
        music()
    if what in ("final", "all"):
        final()
