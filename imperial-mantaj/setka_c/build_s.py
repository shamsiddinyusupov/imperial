"""«Kechasi derazani ochib uxlaysizmi?» — moskit setka (Jalyuzi Classic, sales + poll, no voice).
Night story, centred captions; differs from the Imperial net Reels (no mosquito drawing, no type list, new clip order).
python3 build_s.py [base|prev t,t|ov|music|final|cover|all]
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

D = "/home/claude/reels/setka_c"
W, H, FPS = 1080, 1920, 30
XF = 0.3
# name, source, ss, dur(src), speed, reverse
SC = [
    ("hk", "st/hk.mp4", 0.0, 3.45, 1.0, False),
    ("pull", "st/pull.mp4", 0.2, 3.9, 1.1, True),
    ("door", "st/door.mp4", 0.0, 4.5, 1.25, False),
    ("sash", "st/sash.mp4", 0.0, 5.35, 1.3, False),
    ("day", "st/day.mp4", 0.0, 3.0, 1.0, False),
    ("end", "endbg", 0, 5.9, None, False),
]
TRANS = {1: "fade", 2: "slideleft", 3: "fade", 4: "slideleft", 5: "fadeblack"}
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
S_HK, S_PULL, S_DOOR, S_SASH, S_DAY, S_END = ST
END_OF = dict(zip([s[0] for s in SC], ST[1:] + [TOTAL]))


def sh(cmd):
    subprocess.run(cmd, shell=True, check=True)


def base():
    os.makedirs(f"{D}/bo", exist_ok=True)
    for s in SC:
        name, src, ss, d, sp, rev = s
        out = f"{D}/bo/{name}.mp4"
        od = odur(s)
        if src == "endbg":
            sh(f"ffmpeg -nostdin -v error -y -ss 0.5 -i {D}/st/city.mp4 -an -vf \"setpts=PTS/0.8,fps=30,"
               f"tpad=stop_mode=clone:stop_duration=3,trim=duration={od:.3f},setpts=PTS-STARTPTS,"
               f"gblur=sigma=14,eq=brightness=-0.12:saturation=0.9:contrast=0.95,setsar=1,format=yuv420p\" {ENC} {out}")
        else:
            r = "reverse," if rev else ""
            sh(f"ffmpeg -nostdin -v error -y -ss {ss} -t {d} -i {D}/{src} -an -vf "
               f"\"{r}setpts=PTS/{sp},fps=30,trim=duration={od:.3f},setsar=1,format=yuv420p\" {ENC} {out}")
    ins = " ".join(f"-i {D}/bo/{s[0]}.mp4" for s in SC)
    f = [f"[{i}:v]fps=30,setpts=PTS-STARTPTS,settb=AVTB[v{i}]" for i in range(len(SC))]
    prev = "[v0]"
    for i in range(1, len(SC)):
        f.append(f"{prev}[v{i}]xfade=transition={TRANS[i]}:duration={XF}:offset={ST[i]:.3f},settb=AVTB[x{i}]")
        prev = f"[x{i}]"
    sh(f"ffmpeg -nostdin -v error -y {ins} -filter_complex \"{';'.join(f)}\" -map \"{prev}\" -r 30 {ENC} {D}/base_s.mp4")


def pill(img, cx, cy, s, al, filled, pulse=0.0, w=230):
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
    d.text((cx, cy + 2), s, font=SEMI(46), fill=(INK if filled else CREAM) + (int(255 * al),), anchor="mm")
    img.alpha_composite(lay)


def accent(img, cx, y, al, w=70):
    if al <= 0.01:
        return
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(lay).rounded_rectangle((cx - w // 2, y, cx + w // 2, y + 8), 4, fill=GOLD + (int(255 * al),))
    img.alpha_composite(lay)


def cap(img, t, t0, t1, top, rib, ru, y=1420):
    """Centred caption: short orange bar, Poppins line, orange ribbon, Russian line."""
    al = a_in(t, t0 + 0.12, 0.35) * a_out(t, t1 - 0.2, 0.22)
    if al <= 0.01:
        return
    grad(img, 1100, 1920, 0.85 * al)
    accent(img, W // 2, y - 46, al * a_in(t, t0 + 0.05, 0.3))
    text(img, (W // 2, y), top, SEMI(66), PAPER, al, 14, anchor="ma")
    a2 = a_in(t, t0 + 0.32, 0.35) * a_out(t, t1 - 0.2, 0.22)
    text(img, (W // 2, y + 100), rib, SERI(80), GOLD, a2, 14, anchor="ma")
    text(img, (W // 2, y + 228), ru, MED(30), SUB, a_in(t, t0 + 0.5, 0.35) * a_out(t, t1 - 0.2, 0.22), 10, anchor="ma")


def frame(i):
    t = i / FPS
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    # 1. hook: the poll question
    if t < S_PULL + 0.3:
        al = a_out(t, S_PULL - 0.15, 0.25)
        topgrad(img, 1100, 0.82 * al)
        text(img, (W // 2, 300), NAME + " · MOSKIT SETKA", MONO(26), GOLD, a_in(t, 0, 0.3) * al, 8, anchor="ma",
             tracking=5)
        text(img, (W // 2, 362), "Kechasi derazani", SER(100), PAPER, a_in(t, 0.0, 0.3) * al, 18, anchor="ma")
        text(img, (W // 2, 488), "ochib uxlaysizmi?", SERI(94), GOLD, a_in(t, 0.2, 0.3) * al, 18, anchor="ma")
        text(img, (W // 2, 630), "Спите с открытым окном?", MED(34), SUB, a_in(t, 0.5) * al, 10, anchor="ma")
        ap = a_in(t, 0.8, 0.3) * al
        pu = ((t - 1.7) % 1.0) if t > 1.7 else 0.0
        pill(img, W // 2 - 140, 760, "HA", ap, True, pu if t > 1.7 else 0.0)
        pill(img, W // 2 + 140, 760, "YO‘Q", ap, False)
        text(img, (W // 2, 840), "Izohga yozing · Ответьте в комментариях", MED(28), SUB, a_in(t, 1.1) * al, 8,
             anchor="ma")
    # 2-5. captions
    cap(img, t, S_PULL, END_OF["pull"], "Bir harakat —", "setka yopiq.", "Одно движение — сетка закрыта.")
    cap(img, t, S_DOOR, END_OF["door"], "Derazaga ham,", "eshikka ham.", "И на окно, и на балконную дверь.")
    cap(img, t, S_SASH, END_OF["sash"], "Havo kiradi —", "chivin kirmaydi.", "Воздух — да, комары — нет.")
    cap(img, t, S_DAY, END_OF["day"], "Panjarali derazaga", "ham mos.", "Подходит и для окон с решёткой.")
    # 6. end card
    if t > S_END - 0.2:
        a0 = a_in(t, S_END)
        lg = LOGO.copy()
        lg.thumbnail((440, 230))
        lg.putalpha(lg.split()[3].point(lambda v: int(v * a0)))
        img.alpha_composite(lg, ((W - lg.width) // 2, 215))
        text(img, (W // 2, 480), "Deraza rasmini direktga yuboring —", SER(54), PAPER, a_in(t, S_END + 0.15), 14,
             anchor="ma")
        text(img, (W // 2, 560), "mos setkani aytamiz.", SERI(70), GOLD, a_in(t, S_END + 0.3), 14, anchor="ma")
        text(img, (W // 2, 672), "Пришлите фото окна — подскажем сетку.", MED(28), SUB, a_in(t, S_END + 0.45), 10,
             anchor="ma")
        ap = a_in(t, S_END + 0.9, 0.3)
        pu = ((t - S_END - 1.6) % 1.0) if t > S_END + 1.6 else 0.0
        pill(img, W // 2 - 150, 850, "HA", ap, True, pu, w=250)
        pill(img, W // 2 + 150, 850, "YO‘Q", ap, False, 0.0, w=250)
        text(img, (W // 2 - 150, 912), "ochiq uxlayman", MED(26), SUB, ap, 6, anchor="ma")
        text(img, (W // 2 + 150, 912), "chivin qo‘ymaydi", MED(26), SUB, ap, 6, anchor="ma")
        text(img, (W // 2, 990), "Izohga yozing · Ответьте в комментариях", MED(30), (236, 228, 214),
             a_in(t, S_END + 1.2), 8, anchor="ma")
        text(img, (W // 2, 1490), "Qo‘ng‘iroq qiling · Звоните", MED(30), SUB, a_in(t, S_END + 0.8), 8, anchor="ma")
        text(img, (W // 2, 1540), PHONE, SEMI(58), GOLD, a_in(t, S_END + 0.95), 8, anchor="ma")
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
    from night_bed import night_bed
    night_bed(f"{D}/bed_s.wav", TOTAL, S_END)


OUTN = "classic_setka_kechasi"


def final():
    os.makedirs(f"{D}/out", exist_ok=True)
    sh(f"ffmpeg -nostdin -v error -y -i {D}/base_s.mp4 -framerate 30 -i {D}/ovo/%04d.png -i {D}/bed_s.wav "
       f"-filter_complex \"[0:v][1:v]overlay=0:0:format=auto,format=yuv420p[v];"
       f"[2:a]loudnorm=I=-15:TP=-1.5:LRA=9[a]\" -map \"[v]\" -map \"[a]\" -t {TOTAL:.3f} "
       f"-c:v libx264 -preset slow -crf 18 -pix_fmt yuv420p -color_primaries bt709 -color_trc bt709 -colorspace bt709 "
       f"-c:a aac -b:a 192k -movflags +faststart {D}/out/{OUTN}.mp4")


def cover():
    tt = 2.0
    sh(f"ffmpeg -v error -y -ss {tt} -i {D}/base_s.mp4 -frames:v 1 {D}/cs/cb.png")
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
            sh(f"ffmpeg -v error -y -ss {tt} -i {D}/base_s.mp4 -frames:v 1 {D}/cs/pb.png")
            b = Image.open(f"{D}/cs/pb.png").convert("RGBA")
            b.alpha_composite(Image.fromarray(frame(int(tt * FPS))))
            ims.append(b.convert("RGB").resize((360, 640)))
        c = Image.new("RGB", (365 * len(ims), 640), "white")
        for k, im in enumerate(ims):
            c.paste(im, (k * 365, 0))
        c.save(f"{D}/cs/prev_s.jpg", quality=85)
    if what in ("ov", "all"):
        render_ov()
    if what in ("music", "all"):
        music()
    if what in ("final", "all"):
        final()
    if what in ("cover", "all"):
        cover()
