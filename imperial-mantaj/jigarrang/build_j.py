"""«Jigarrang romga — plisse ham shu tonda» (Jalyuzi Classic, sales + participation, no voice).
hook question -> colour palette (rom / plisse / tutqich) -> 4 benefit shots -> question -> end card with colour poll.
python3 build_j.py [base|prev t,t|ov|music|final|cover|all]
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
from brand import LOGO, LOGO_BOX, NAME, PHONE  # noqa: E402
from classic_style import ARROW, CREAM, GOLD, INK, MED, MONO, PAPER, SEMI, SER, SERI, text  # noqa: E402

D = "/home/claude/reels/jigarrang"
W, H, FPS = 1080, 1920, 30
XF = 0.3
# name, source, ss, dur(src), speed
SC = [
    ("hk", "st/hk.mp4", 0.0, 5.2, 1.4),
    ("pal", "st/pal.mp4", 0.0, 1.9, 0.7),
    ("w1", "st/w1.mp4", 0.0, 3.85, 1.1),
    ("ph2", "photo2", 0, 2.7, None),
    ("w3", "st/w3.mp4", 0.0, 3.9, 1.2),
    ("w2", "st/w2.mp4", 0.0, 5.2, 1.5),
    ("w4", "st/w4.mp4", 0.6, 4.2, 1.3),
    ("end", "endbg", 0, 5.8, None),
]
TRANS = {1: "fade", 2: "smoothleft", 3: "fade", 4: "smoothleft", 5: "smoothleft", 6: "fade", 7: "fadeblack"}
WOOD, PLISSE, HANDLE = (162, 115, 81), (84, 62, 58), (209, 179, 77)
SUB = (222, 212, 198)


def odur(s):
    return s[3] / s[4] if isinstance(s[4], float) else s[3]


ST, _t = [], 0.0
for s in SC:
    ST.append(_t)
    _t += odur(s) - XF
TOTAL = _t + XF
NF = int(round(TOTAL * FPS))
ENC = "-c:v libx264 -preset fast -crf 15 -pix_fmt yuv420p"
S_HK, S_PAL, S_W1, S_PH, S_W3, S_W2, S_W4, S_END = ST
END_OF = dict(zip([s[0] for s in SC], ST[1:] + [TOTAL]))


def sh(cmd):
    subprocess.run(cmd, shell=True, check=True)


def base():
    os.makedirs(f"{D}/bo", exist_ok=True)
    for s in SC:
        name, src, ss, d, sp = s
        out = f"{D}/bo/{name}.mp4"
        od = odur(s)
        nfr = int(round(od * FPS)) + 2
        if src == "photo2":   # crop away the table at the bottom, slow push-in
            sh(f"ffmpeg -nostdin -v error -y -loop 1 -framerate 30 -i {D}/src/photo2.jpg -vf "
               f"\"crop=1260:2240:95:150,scale=2160:3840:flags=lanczos,"
               f"zoompan=z='1.0+0.07*on/{nfr}':x='iw/2-(iw/zoom/2)':y='ih*0.46-(ih/zoom*0.46)':d=1:s=1080x1920:fps=30,"
               f"eq=contrast=1.04:saturation=1.04,unsharp=5:5:0.25,setsar=1,format=yuv420p\" -frames:v {nfr} -an {ENC} {out}")
        elif src == "endbg":
            sh(f"ffmpeg -nostdin -v error -y -loop 1 -framerate 30 -i {D}/src/photo1.jpg -vf "
               f"\"crop=1209:2150:120:0,scale=1080:1920:flags=lanczos,"
               f"zoompan=z='1.04+0.03*on/{nfr}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=1080x1920:fps=30,"
               f"gblur=sigma=14,eq=brightness=-0.15:saturation=0.85:contrast=0.95,setsar=1,format=yuv420p\" "
               f"-frames:v {nfr} -an {ENC} {out}")
        else:
            sh(f"ffmpeg -nostdin -v error -y -ss {ss} -t {d} -i {D}/{src} -an -vf "
               f"\"setpts=PTS/{sp},fps=30,trim=duration={od:.3f},setsar=1,format=yuv420p\" {ENC} {out}")
    ins = " ".join(f"-i {D}/bo/{s[0]}.mp4" for s in SC)
    f = [f"[{i}:v]fps=30,setpts=PTS-STARTPTS,settb=AVTB[v{i}]" for i in range(len(SC))]
    prev = "[v0]"
    for i in range(1, len(SC)):
        f.append(f"{prev}[v{i}]xfade=transition={TRANS[i]}:duration={XF}:offset={ST[i]:.3f},settb=AVTB[x{i}]")
        prev = f"[x{i}]"
    sh(f"ffmpeg -nostdin -v error -y {ins} -filter_complex \"{';'.join(f)}\" -map \"{prev}\" -r 30 {ENC} {D}/base_j.mp4")


def swatch(img, cx, cy, r, col, al, ring=0.0):
    if al <= 0.01:
        return
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    if ring > 0.01:
        rr = r + 12
        d.ellipse((cx - rr, cy - rr, cx + rr, cy + rr), outline=GOLD + (int(255 * al * ring),), width=6)
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=tuple(col) + (int(255 * al),),
              outline=CREAM + (int(200 * al),), width=4)
    img.alpha_composite(lay)


def lower(img, t, t0, t1, top, rib, ru, y=1430):
    """Lower-third caption: Poppins line + orange ribbon line + Russian line."""
    al = a_in(t, t0 + 0.12, 0.35) * a_out(t, t1 - 0.2, 0.22)
    if al <= 0.01:
        return
    grad(img, 1150, 1920, 0.82 * al)
    text(img, (86, y), top, SEMI(64), PAPER, al, 14)
    text(img, (98, y + 96), rib, SERI(78), GOLD, a_in(t, t0 + 0.3, 0.35) * a_out(t, t1 - 0.2, 0.22), 14)
    text(img, (90, y + 222), ru, MED(30), SUB, a_in(t, t0 + 0.5, 0.35) * a_out(t, t1 - 0.2, 0.22), 10)


def frame(i):
    t = i / FPS
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    # 1. hook question (top)
    if t < S_PAL + 0.3:
        al = a_out(t, S_PAL - 0.15, 0.25)
        topgrad(img, 1000, 0.78 * al)
        text(img, (86, 300), NAME + " · PLISSE", MONO(26), GOLD, a_in(t, 0, 0.3) * al, 8, tracking=6)
        text(img, (86, 362), "Romingiz", SER(112), PAPER, a_in(t, 0.0, 0.3) * al, 18)
        text(img, (86, 482), "jigarrangmi?", SER(112), PAPER, a_in(t, 0.12, 0.3) * al, 18)
        text(img, (102, 640), "Plisse — shu tonda.", SERI(84), GOLD, a_in(t, 1.0, 0.35) * al, 16)
        text(img, (90, 770), "Коричневые рамы? Плиссе — в тон.", MED(32), SUB, a_in(t, 1.3) * al, 10)
    # 2. palette: rom / plisse / tutqich
    if S_PAL - 0.1 < t < S_W1 + 0.3:
        al = a_in(t, S_PAL + 0.05, 0.3) * a_out(t, S_W1 - 0.2, 0.25)
        grad(img, 1000, 1920, 0.85 * al)
        text(img, (86, 1150), "RANG UYG‘UNLIGI · ЦВЕТ В ТОН", MONO(26), GOLD, al, 8, tracking=5)
        rows = [(WOOD, "Rom", "yong‘oq rang · рама"), (PLISSE, "Plisse", "shokolad rang · плиссе"),
                (HANDLE, "Tutqich", "oltin rang · ручка")]
        for k, (col, uz, sub) in enumerate(rows):
            a2 = a_in(t, S_PAL + 0.25 + 0.35 * k, 0.35) * a_out(t, S_W1 - 0.2, 0.25)
            y = 1235 + 150 * k
            swatch(img, 140, y + 44, 46, col, a2)
            text(img, (218, y - 4), uz, SEMI(60), PAPER, a2, 12)
            text(img, (220, y + 74), sub, MED(30), SUB, a2, 10)
    # 3-6. benefit captions
    lower(img, t, S_W1, END_OF["w1"], "Deraza bilan", "bir butun.", "Смотрится как часть окна.")
    lower(img, t, S_PH, END_OF["ph2"], "Klassik interyerga —", "klassik rang.", "К классике — классический цвет.")
    lower(img, t, S_W3, END_OF["w3"], "Tor derazaga ham", "mos keladi.", "Подходит и для узких окон.")
    lower(img, t, S_W2, END_OF["w2"], "Har bir tabaqaga —", "alohida.", "На каждую створку — отдельно.")
    # 7. question
    if S_W4 - 0.1 < t < S_END + 0.3:
        al = a_in(t, S_W4 + 0.1, 0.35) * a_out(t, S_END - 0.15, 0.25)
        grad(img, 1150, 1920, 0.85 * al)
        text(img, (86, 1440), "Sizning romingiz", SER(84), PAPER, al, 16)
        text(img, (100, 1548), "qaysi rangda?", SERI(92), GOLD, a_in(t, S_W4 + 0.35, 0.35) * a_out(t, S_END - 0.15, 0.25), 16)
        text(img, (90, 1690), "А какого цвета ваши рамы?", MED(32), SUB, a_in(t, S_W4 + 0.6) * a_out(t, S_END - 0.15), 10)
    # 8. end card: logo, colour poll, typed comment, phone
    if t > S_END - 0.2:
        a0 = a_in(t, S_END)
        lg = LOGO.copy()
        lg.thumbnail((440, 230))
        lg.putalpha(lg.split()[3].point(lambda v: int(v * a0)))
        img.alpha_composite(lg, ((W - lg.width) // 2, 215))
        text(img, (W // 2, 480), "Rom rangini izohga yozing —", SER(60), PAPER, a_in(t, S_END + 0.15), 14, anchor="ma")
        text(img, (W // 2, 565), "mos plisseni tavsiya qilamiz.", SERI(62), GOLD, a_in(t, S_END + 0.3), 14, anchor="ma")
        text(img, (W // 2, 668), "Напишите цвет рам — подскажем плиссе в тон.", MED(28), SUB, a_in(t, S_END + 0.45), 10,
             anchor="ma")
        opts = [((246, 244, 240), "Oq", "белый"), (WOOD, "Jigarrang", "коричневый"),
                ((112, 116, 120), "Kulrang", "серый"), ((30, 30, 32), "Qora", "чёрный")]
        hi = 1 if t > S_END + 2.0 else int(((t - S_END - 0.6) / 0.35)) % 4
        for k, (col, uz, ru) in enumerate(opts):
            a2 = a_in(t, S_END + 0.55 + 0.12 * k, 0.3)
            cx = 195 + 230 * k
            ring = 1.0 if (k == hi and t > S_END + 0.6) else 0.0
            swatch(img, cx, 830, 58, col, a2, ring)
            text(img, (cx, 912), uz, SEMI(36), PAPER, a2, 8, anchor="ma")
            text(img, (cx, 960), ru, MED(24), SUB, a2, 8, anchor="ma")
        af = a_in(t, S_END + 1.6)
        if af > 0.01:
            lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
            d = ImageDraw.Draw(lay)
            d.rounded_rectangle((150, 1060, 930, 1170), 55, fill=(255, 255, 255, int(235 * af)))
            word = "Jigarrang"
            n = int(max(0, min(len(word), (t - S_END - 2.0) / 0.09)))
            f = SEMI(52)
            d.text((210, 1115), word[:n], font=f, fill=INK + (int(255 * af),), anchor="lm")
            if int(t * 2) % 2 == 0 and n < len(word):
                cx = 210 + f.getlength(word[:n]) + 6
                d.line([(cx, 1085), (cx, 1145)], fill=(214, 140, 60, int(255 * af)), width=4)
            d.rounded_rectangle((780, 1080, 912, 1150), 35, fill=GOLD + (int(255 * af),))
            d.text((846, 1115), "→", font=ARROW, fill=INK + (int(255 * af),), anchor="mm")
            img.alpha_composite(lay)
        text(img, (W // 2, 1215), "Yoki deraza rasmini direktga yuboring", MED(34), (236, 228, 214),
             a_in(t, S_END + 2.9), 10, anchor="ma")
        text(img, (W // 2, 1265), "Или пришлите фото окна в директ", MED(28), SUB, a_in(t, S_END + 3.05), 10, anchor="ma")
        text(img, (W // 2, 1490), "Qo‘ng‘iroq qiling · Звоните", MED(30), SUB, a_in(t, S_END + 0.9), 8, anchor="ma")
        text(img, (W // 2, 1540), PHONE, SEMI(58), GOLD, a_in(t, S_END + 1.0), 8, anchor="ma")
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
    from lounge_bed import lounge_bed
    lounge_bed(f"{D}/bed_j.wav", TOTAL, S_END)


OUTN = "classic_jigarrang_plisse"


def final():
    os.makedirs(f"{D}/out", exist_ok=True)
    sh(f"ffmpeg -nostdin -v error -y -i {D}/base_j.mp4 -framerate 30 -i {D}/ovo/%04d.png -i {D}/bed_j.wav "
       f"-filter_complex \"[0:v][1:v]overlay=0:0:format=auto,format=yuv420p[v];"
       f"[2:a]loudnorm=I=-15:TP=-1.5:LRA=9[a]\" -map \"[v]\" -map \"[a]\" -t {TOTAL:.3f} "
       f"-c:v libx264 -preset slow -crf 18 -pix_fmt yuv420p -color_primaries bt709 -color_trc bt709 -colorspace bt709 "
       f"-c:a aac -b:a 192k -movflags +faststart {D}/out/{OUTN}.mp4")


def cover():
    tt = 1.9
    sh(f"ffmpeg -v error -y -ss {tt} -i {D}/base_j.mp4 -frames:v 1 {D}/cs/cb.png")
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
            sh(f"ffmpeg -v error -y -ss {tt} -i {D}/base_j.mp4 -frames:v 1 {D}/cs/pb.png")
            b = Image.open(f"{D}/cs/pb.png").convert("RGBA")
            b.alpha_composite(Image.fromarray(frame(int(tt * FPS))))
            ims.append(b.convert("RGB").resize((360, 640)))
        c = Image.new("RGB", (365 * len(ims), 640), "white")
        for k, im in enumerate(ims):
            c.paste(im, (k * 365, 0))
        c.save(f"{D}/cs/prev_j.jpg", quality=85)
    if what in ("ov", "all"):
        render_ov()
    if what in ("music", "all"):
        music()
    if what in ("final", "all"):
        final()
    if what in ("cover", "all"):
        cover()
