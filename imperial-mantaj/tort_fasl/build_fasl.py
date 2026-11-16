"""«Bir deraza — to‘rt fasl» (IMPERIAL, owner 17.11; sister of the Classic «Bir deraza — bir kun»).
room4.py animation (14 s: spring -> summer -> autumn -> winter in one real window, IMG_6041 plate) -> match dissolve
into the real IMG_6041 (reversed) -> IMG_6039 room pan -> Imperial end card «To‘rt faslga — 1 yil kafolat».
Music: musette_bed (#22, accordion waltz + seasonal ambience).
python3 build_fasl.py [base|prev t,t|ov|music|final|cover|all]
"""
import os
import subprocess
import sys
from multiprocessing import Pool

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, "/home/claude/reels/common")
sys.path.insert(0, "/home/claude/reels/ref1116")
sys.path.insert(0, "/home/claude/reels/qora_plisse")
import build_bd as B  # noqa: E402  (Imperial fonts, colours, logo, phone, text helpers)
from build_b import a_in, a_out, topgrad  # noqa: E402

D = "/home/claude/reels/fasl"
W, H, FPS = 1080, 1920, 30
ENC = "-c:v libx264 -preset fast -crf 15 -pix_fmt yuv420p"
text, cloud, sweep = B.text, B.cloud, B.sweep
ITA, RU, LAB, LABM, DID = B.ITA, B.RU, B.LAB, B.LABM, B.DID
CREAM, GOLD, SAND = B.CREAM, B.GOLD, B.SAND
SC = [("anim", "anim.mp4", 14.0, None, 0),
      ("r6041", "seg/r6041.mp4", 2.033, "fade", 0.8),
      ("p6039", "seg/p6039.mp4", 1.9, "fade", 0.4),
      ("end", "bo/end.mp4", 5.5, "fade", 0.5)]
ST, _t = [], 0.0
for k, s in enumerate(SC):
    if k:
        _t -= s[4]
    ST.append(_t)
    _t += s[2]
TOTAL = _t
NF = int(round(TOTAL * FPS))
S_REAL, S_END = ST[1], ST[3]
SEASONS = [(0.0, 3.4, "Bahor", "весна"), (3.4, 6.8, "Yoz", "лето"), (6.8, 10.2, "Kuz", "осень"),
           (10.2, 13.3, "Qish", "зима")]


def sh(cmd):
    subprocess.run(cmd, shell=True, check=True)


def base():
    os.makedirs(f"{D}/bo", exist_ok=True)
    nfr = int(round(SC[-1][2] * FPS)) + 2
    sh(f"ffmpeg -nostdin -v error -y -loop 1 -framerate 30 -i {D}/fr/0419.jpg -vf "
       f"\"zoompan=z='1.10+0.04*on/{nfr}':x='iw*0.55-(iw/zoom*0.55)':y='ih*0.42-(ih/zoom*0.42)':d=1:s=1080x1920:fps=30,"
       f"gblur=sigma=16,eq=brightness=-0.16:saturation=0.85:contrast=0.92,setsar=1,format=yuv420p\" "
       f"-frames:v {nfr} -an {ENC} {D}/bo/end.mp4")
    ins = " ".join(f"-i {D}/{s[1]}" for s in SC)
    f = [f"[{i}:v]fps=30,setpts=PTS-STARTPTS,settb=AVTB,trim=duration={SC[i][2]:.3f}[v{i}]" for i in range(len(SC))]
    prev = "[v0]"
    for i in range(1, len(SC)):
        f.append(f"{prev}[v{i}]xfade=transition={SC[i][3]}:duration={SC[i][4]}:offset={ST[i]:.3f},settb=AVTB[x{i}]")
        prev = f"[x{i}]"
    sh(f"ffmpeg -nostdin -v error -y {ins} -filter_complex \"{';'.join(f)}\" -map \"{prev}\" -r 30 {ENC} {D}/base_fasl.mp4")


def line(img, t, t0, t1, uz, gold, ru, y=1405):
    al = a_in(t, t0, 0.5) * a_out(t, t1, 0.45)
    if al <= 0.01:
        return
    cloud(img, (20, y - 110, 1060, y + 290), al, a=190, blur=55)
    text(img, (W // 2, y), uz, ITA(60), CREAM, al, 16, anchor="ma")
    text(img, (W // 2, y + 80), gold, ITA(76), GOLD, a_in(t, t0 + 0.3, 0.5) * a_out(t, t1, 0.45), 16, anchor="ma")
    text(img, (W // 2, y + 190), ru, RU(31), CREAM, a_in(t, t0 + 0.5, 0.5) * a_out(t, t1, 0.45), 10, anchor="ma")


def frame(i, cover_mode=False):
    t = i / FPS
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if t < S_REAL + 0.4 and not cover_mode:
        ag = a_in(t, 0.2, 0.4) * a_out(t, S_REAL - 0.1, 0.4)
        topgrad(img, 430, 0.45 * ag)
        text(img, (90, 148), "BIR DERAZA · TO‘RT FASL", LAB(24), GOLD, ag, 0, tracking=6)
        for t0, t1, uz, ru in SEASONS:
            al = a_in(t, t0 + (0.25 if t0 else 0.3), 0.45) * a_out(t, t1 - 0.25, 0.35) * ag
            text(img, (88, 182), uz, ITA(96), CREAM, al, 18)
            text(img, (92, 298), ru, RU(32), SAND, al, 10)
        line(img, t, 0.6, 3.1, "Bahorda —", "yorug‘likka ochiq.", "Весной — навстречу свету.")
        line(img, t, 3.9, 6.5, "Yozda —", "quyosh yumshoq.", "Летом — мягкое солнце.")
        line(img, t, 7.3, 9.9, "Kuzda —", "oltin nur.", "Осенью — золотой свет.")
        line(img, t, 10.7, 13.1, "Qishda —", "shinam oqshomlar.", "Зимой — уютные вечера.")
    if not cover_mode and S_REAL < t < S_END + 0.3:
        al = a_in(t, S_REAL + 0.5, 0.4) * a_out(t, S_END - 0.1, 0.3)
        topgrad(img, 400, 0.6 * al)
        text(img, (90, 170), "HAQIQIY KADR · РЕАЛЬНЫЕ КАДРЫ", LAB(26), CREAM, al, 0, tracking=5)
        line(img, t, S_REAL + 0.6, S_END + 0.1, "To‘rt fasl —", "bitta plisse.", "Четыре сезона — одно плиссе.")
    if not cover_mode and t > S_END - 0.1:
        a0 = a_in(t, S_END + 0.1, 0.4)
        lg = B.LOGO.copy()
        lg.thumbnail((420, 170))
        lg.putalpha(lg.split()[3].point(lambda x: int(x * a0)))
        lx = (W - lg.width) // 2
        img.alpha_composite(lg, (lx, 300))
        sweep(img, (lx, 300, lx + lg.width, 300 + lg.height), t, S_END + 3.4)
        text(img, (W // 2, 560), "To‘rt faslga —", DID(86), CREAM, a_in(t, S_END + 0.3, 0.4), 18, anchor="ma")
        text(img, (W // 2, 668), "1 yil kafolat.", ITA(70), GOLD, a_in(t, S_END + 0.5, 0.4), 14, anchor="ma")
        text(img, (W // 2, 778), "Гарантия 1 год — на все четыре сезона.", RU(30), SAND, a_in(t, S_END + 0.7), 10,
             anchor="ma")
        for k, s in enumerate(["Plisse jalyuzi — har bir tabaqaga alohida", "Toshkentda o‘lchov va o‘rnatish — bepul",
                               "O‘lchovdan keyin 3 kunda tayyor"]):
            text(img, (W // 2, 900 + 62 * k), s, LAB(32), CREAM, a_in(t, S_END + 0.9 + 0.15 * k, 0.4), 8, anchor="ma")
        text(img, (W // 2, 1150), "Narxi uchun — izohga «NARX» deb yozing", ITA(48), GOLD, a_in(t, S_END + 1.5), 10,
             anchor="ma")
        text(img, (W // 2, 1236), "Цены — напишите NARX в комментариях", RU(28), SAND, a_in(t, S_END + 1.6), 8,
             anchor="ma")
        text(img, (W // 2, 1400), B.PHONE, LABM(54), CREAM, a_in(t, S_END + 1.8), 8, anchor="ma", tracking=2)
        text(img, (W // 2, 1484), "t.me/jalyuzi_imperial · @imperial_jalyuzi_uz", LAB(28), (190, 172, 150),
             a_in(t, S_END + 1.9), 8, anchor="ma")
    return np.asarray(img)


def render_ov():
    os.makedirs(f"{D}/ov", exist_ok=True)
    idx = list(range(NF))
    with Pool(2) as p:
        for k in range(0, len(idx), 12):
            ch = idx[k:k + 12]
            for i, a in zip(ch, p.map(frame, ch)):
                Image.fromarray(a).save(f"{D}/ov/{i:04d}.png", compress_level=1)


def music():
    from musette_bed import musette_bed
    musette_bed(f"{D}/bed_fasl.wav", TOTAL, 1.7, S_REAL, S_END)


OUTN = "imperial_bir_deraza_tort_fasl"


def final():
    os.makedirs(f"{D}/out", exist_ok=True)
    sh(f"ffmpeg -nostdin -v error -y -i {D}/base_fasl.mp4 -framerate 30 -i {D}/ov/%04d.png -i {D}/bed_fasl.wav "
       f"-filter_complex \"[0:v][1:v]overlay=0:0:format=auto,format=yuv420p[v];"
       f"[2:a]loudnorm=I=-15:TP=-1.5:LRA=11[a]\" -map \"[v]\" -map \"[a]\" -t {TOTAL:.3f} "
       f"-c:v libx264 -preset slow -crf 18 -pix_fmt yuv420p -color_primaries bt709 -color_trc bt709 -colorspace bt709 "
       f"-c:a aac -b:a 192k -movflags +faststart {D}/out/{OUTN}.mp4")


def cover():
    """2x2: the same window in four seasons, title in the middle"""
    picks = [(2.7, "Bahor"), (5.9, "Yoz"), (8.8, "Kuz"), (11.0, "Qish")]
    c = Image.new("RGB", (W, H), (20, 16, 12))
    for k, (tt, name) in enumerate(picks):
        im = Image.open(f"{D}/fr/{int(tt * FPS):04d}.jpg").convert("RGB")
        im = im.crop((60, 250, 1080, 1560)).resize((540, 694), Image.LANCZOS)
        x, y = (k % 2) * 540, 266 + (k // 2) * 694
        c.paste(im, (x, y))
        ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        text(ov, (x + 30, y + 22 if k < 2 else y + 600), name, ITA(56), CREAM, 1.0, 0)
        c = Image.alpha_composite(c.convert("RGBA"), ov).convert("RGB")
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    d.line([(540, 266), (540, 266 + 2 * 694)], fill=(20, 16, 12, 255), width=6)
    d.line([(0, 266 + 694), (W, 266 + 694)], fill=(20, 16, 12, 255), width=6)
    c = Image.alpha_composite(c.convert("RGBA"), lay)
    t2 = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(t2).rounded_rectangle((150, 866, 930, 1056), 40, fill=(24, 18, 14, 225))
    t2 = t2.filter(ImageFilter.GaussianBlur(2))
    text(t2, (W // 2, 878), "Bir deraza —", ITA(66), CREAM, 1.0, 0, anchor="ma")
    text(t2, (W // 2, 952), "to‘rt fasl.", ITA(78), GOLD, 1.0, 0, anchor="ma")
    c = Image.alpha_composite(c, t2)
    t3 = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    lg = B.LOGO.copy()
    lg.thumbnail((360, 140))
    t3.alpha_composite(lg, ((W - lg.width) // 2, 70))
    text(t3, (W // 2, 1700), "Одно окно — четыре сезона", RU(34), SAND, 1.0, 0, anchor="ma")
    c = Image.alpha_composite(c, t3)
    c.convert("RGB").save(f"{D}/out/{OUTN}_muqova.jpg", quality=92)


if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else "all"
    print("starts", [round(s, 2) for s in ST], "total", round(TOTAL, 2))
    if what in ("base", "all"):
        base()
    if what == "prev":
        ims = []
        for tt in map(float, sys.argv[2].split(",")):
            sh(f"ffmpeg -v error -y -ss {tt} -i {D}/base_fasl.mp4 -frames:v 1 {D}/pb.png")
            b = Image.open(f"{D}/pb.png").convert("RGBA")
            b.alpha_composite(Image.fromarray(frame(int(tt * FPS))))
            ims.append(b.convert("RGB").resize((360, 640)))
        c = Image.new("RGB", (365 * len(ims), 640), "white")
        for k, im in enumerate(ims):
            c.paste(im, (k * 365, 0))
        c.save(f"{D}/prev_fasl.jpg", quality=85)
    if what in ("ov", "all"):
        render_ov()
    if what in ("music", "all"):
        music()
    if what in ("final", "all"):
        final()
    if what in ("cover", "all"):
        cover()
