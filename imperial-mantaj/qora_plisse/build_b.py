"""Qora plisse — B «Kechasi» (sales, no voice): scenes -> xfade base, Pillow overlays (batched), Rhodes bed, final.
python3 build_b.py [base|ov|music|final|all]
"""
import os
import subprocess
import sys
from multiprocessing import Pool

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, "/home/claude/reels/common")
D = "/home/claude/reels/qora_plisse"
W, H, FPS = 1080, 1920, 30
XF = 0.35
# name, src, start, dur(src), speed (<1 = slower)
SC = [
    ("s1", "st/nightpull.mp4", 2.9, 2.7, 0.75),
    ("s2", "st/nightpull.mp4", 5.6, 3.8, 1.0),
    ("s3", "st/nightopen.mp4", 0.3, 6.0, 1.0),
    ("s4a", "st/macro.mp4", 1.0, 2.3, 1.0),
    ("s4b", "st/niche1.mp4", 0.0, 2.3, 1.0),
    ("s4c", "st/bath1.mp4", 2.6, 2.3, 1.0),
    ("end", None, 0, 4.8, 1.0),
]
PHOTO = "src/8299d088-image.jpg"


def durs():
    return [d / s for _, _, _, d, s in SC]


def starts():
    t, out = 0.0, []
    for i, d in enumerate(durs()):
        out.append(t)
        t += d - XF
    return out, t + XF


ST, TOTAL = starts()
NF = int(round(TOTAL * FPS))


def sh(cmd):
    subprocess.run(cmd, shell=True, check=True)


def base():
    os.makedirs(f"{D}/bs", exist_ok=True)
    for name, src, ss, d, sp in SC:
        out = f"{D}/bs/{name}.mp4"
        if src is None:
            od = d
            sh(f"ffmpeg -nostdin -v error -y -loop 1 -i {D}/{PHOTO} -filter_complex "
               f"\"[0:v]scale=1188:2112:force_original_aspect_ratio=increase,crop=1188:2112,"
               f"zoompan=z='1.0+0.04*on/({od}*30)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=1080x1920:fps=30,"
               f"gblur=sigma=16,eq=brightness=-0.30:saturation=0.8:contrast=0.9,format=yuv420p\" -t {od} "
               f"-c:v libx264 -preset fast -crf 15 -pix_fmt yuv420p {out}")
        else:
            od = d / sp
            sh(f"ffmpeg -nostdin -v error -y -ss {ss} -t {d} -i {D}/{src} -an -vf "
               f"\"setpts=PTS/{sp},fps=30,trim=duration={od:.3f},setsar=1,format=yuv420p\" "
               f"-c:v libx264 -preset fast -crf 15 -pix_fmt yuv420p {out}")
    ins = " ".join(f"-i {D}/bs/{n}.mp4" for n, *_ in SC)
    f = [f"[{i}:v]fps=30,setpts=PTS-STARTPTS,settb=AVTB[v{i}]" for i in range(len(SC))]
    prev = "[v0]"
    for i in range(1, len(SC)):
        off = ST[i]
        tr = "fade" if i in (1, len(SC) - 1) else ("smoothleft" if i >= 3 else "fade")
        lab = f"[x{i}]"
        f.append(f"{prev}[v{i}]xfade=transition={tr}:duration={XF}:offset={off:.3f},settb=AVTB{lab}")
        prev = lab
    sh(f"ffmpeg -nostdin -v error -y {ins} -filter_complex \"{';'.join(f)}\" -map \"{prev}\" -r 30 "
       f"-c:v libx264 -preset fast -crf 15 -pix_fmt yuv420p {D}/base_b.mp4")


# ---------------- overlays ----------------
FI = "/usr/share/fonts/opentype/inter/"
CX = "/usr/share/fonts/truetype/crosextra/"
_F = {}


def F(name, size):
    k = (name, size)
    if k not in _F:
        _F[k] = ImageFont.truetype(name, size)
    return _F[k]


SER = lambda s: F(CX + "Caladea-Regular.ttf", s)
SERI = lambda s: F(CX + "Caladea-Italic.ttf", s)
SEMI = lambda s: F(FI + "InterDisplay-SemiBold.otf", s) if os.path.exists(FI + "InterDisplay-SemiBold.otf") else F(FI + "Inter-SemiBold.otf", s)
MED = lambda s: F(FI + "Inter-Medium.otf", s)
MONO = lambda s: F("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", s)
PAPER, GOLD, INK = (245, 241, 233), (214, 176, 98), (30, 28, 25)
LOGO = Image.open("/home/claude/imperial/src/img/logo_light.png").convert("RGBA")


def ease(x):
    x = min(1, max(0, x))
    return 1 - (1 - x) ** 3


def a_in(t, t0, d=0.45):
    return ease((t - t0) / d)


def a_out(t, t1, d=0.3):
    return 1 - ease((t - t1) / d)


def text(img, xy, s, font, fill, alpha, rise=0, anchor="la", tracking=0):
    if alpha <= 0.01:
        return
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    x, y = xy
    y += rise * (1 - alpha)
    if tracking:
        w = sum(font.getlength(c) for c in s) + tracking * (len(s) - 1)
        if anchor[0] == "m":
            x -= w / 2
        for c in s:
            d.text((x, y), c, font=font, fill=fill + (int(255 * alpha),))
            x += font.getlength(c) + tracking
    else:
        d.text((x, y), s, font=font, fill=fill + (int(255 * alpha),), anchor=anchor)
    img.alpha_composite(lay)


def grad(img, y0, y1, a=0.75):
    g = np.zeros((H, W, 4), np.uint8)
    yy = np.arange(H)
    v = np.clip((yy - y0) / max(1, (y1 - y0)), 0, 1) ** 1.3 * a
    g[..., 3] = (v[:, None] * 255).astype(np.uint8)
    img.alpha_composite(Image.fromarray(g))


def topgrad(img, y1, a=0.6):
    g = np.zeros((H, W, 4), np.uint8)
    yy = np.arange(H)
    v = np.clip(1 - yy / y1, 0, 1) ** 1.4 * a
    g[..., 3] = (v[:, None] * 255).astype(np.uint8)
    img.alpha_composite(Image.fromarray(g))


def label(img, t, t0, s="IMPERIAL · PLISSE"):
    al = a_in(t, t0)
    text(img, (86, 300), s, MONO(26), GOLD, al, 10, tracking=6)


def check(img, x, y, al, s, sub):
    if al <= 0.01:
        return
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    r = 30
    d.ellipse((x, y, x + 2 * r, y + 2 * r), fill=GOLD + (int(255 * al),))
    d.line([(x + 17, y + 31), (x + 27, y + 41), (x + 44, y + 21)], fill=INK + (int(255 * al),), width=6, joint="curve")
    img.alpha_composite(lay)
    text(img, (x + 84, y - 2), s, SEMI(54), PAPER, al, 14)
    text(img, (x + 86, y + 62), sub, MED(30), (215, 208, 196), al, 14)


def frame(i):
    t = i / FPS
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    s1, s2, s3, s4, s5, s6, s7 = ST
    # S1 hook
    if t < s2 + 0.4:
        al = a_out(t, s2 - 0.1)
        topgrad(img, 900, 0.55 * al)
        label(img, t, 0.0)
        text(img, (86, 360), "Kechasi chiroq", SER(104), PAPER, a_in(t, 0.05) * al, 18)
        text(img, (86, 475), "yoqasiz…", SERI(104), GOLD, a_in(t, 0.25) * al, 18)
        text(img, (88, 612), "…va butun ko‘cha sizni ko‘radi.", MED(40), PAPER, a_in(t, 1.3) * al, 12)
        text(img, (88, 664), "Вечером включаете свет — и вас видит вся улица.", MED(28), (205, 198, 186), a_in(t, 1.5) * al, 12)
    # S2 one move
    if s2 - 0.1 < t < s3 + 0.3:
        al = a_out(t, s3 - 0.1)
        grad(img, 1150, 1900, 0.8 * al)
        text(img, (86, 1420), "Bitta harakat —", SER(92), PAPER, a_in(t, s2 + 0.2) * al, 18)
        text(img, (86, 1522), "xona faqat sizniki.", SERI(92), GOLD, a_in(t, s2 + 1.6) * al, 18)
        text(img, (88, 1640), "Одно движение — комната только ваша.", MED(30), (215, 208, 196), a_in(t, s2 + 1.8) * al, 10)
    # S3 sash
    if s3 - 0.1 < t < s4 + 0.3:
        al = a_out(t, s4 - 0.1)
        grad(img, 1120, 1900, 0.82 * al)
        text(img, (86, 1400), "Deraza ochilsa ham —", SEMI(64), PAPER, a_in(t, s3 + 0.4) * al, 16)
        text(img, (86, 1482), "plisse u bilan birga.", SERI(86), GOLD, a_in(t, s3 + 0.7) * al, 16)
        text(img, (88, 1600), "Плиссе на каждой створке — открывается вместе с окном.", MED(28), (215, 208, 196), a_in(t, s3 + 1.0) * al, 10)
    # S4 benefits (stacked, one per shot)
    if s4 - 0.1 < t < s7 + 0.2:
        al = a_out(t, s7 - 0.15)
        grad(img, 1000, 1900, 0.85 * al)
        text(img, (86, 1090), "IMPERIAL · TOSHKENT", MONO(26), GOLD, a_in(t, s4) * al, 8, tracking=6)
        check(img, 86, 1170, a_in(t, s4 + 0.25) * al, "O‘lchov va o‘rnatish", "bepul · Замер и установка бесплатно")
        check(img, 86, 1330, a_in(t, s5 + 0.25) * al, "3 kunda tayyor", "o‘lchovdan keyin · Готово за 3 дня")
        check(img, 86, 1490, a_in(t, s6 + 0.25) * al, "1 yil kafolat", "Гарантия 1 год")
    # S5 end card
    if t > s7 - 0.2:
        a0 = a_in(t, s7)
        lg = LOGO.copy()
        lg.thumbnail((420, 200))
        la = lg.split()[3].point(lambda v: int(v * a0))
        lg.putalpha(la)
        img.alpha_composite(lg, ((W - lg.width) // 2, 330))
        text(img, (W // 2, 560), "Deraza rasmini", SER(84), PAPER, a_in(t, s7 + 0.2), 14, anchor="ma")
        text(img, (W // 2, 660), "direktga yuboring", SERI(84), GOLD, a_in(t, s7 + 0.35), 14, anchor="ma")
        text(img, (W // 2, 800), "yoki izohga yozing:", MED(40), PAPER, a_in(t, s7 + 0.8), 10, anchor="ma")
        # comment field typing NARX
        af = a_in(t, s7 + 1.0)
        if af > 0.01:
            lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
            d = ImageDraw.Draw(lay)
            d.rounded_rectangle((170, 880, 910, 990), 55, fill=(255, 255, 255, int(235 * af)))
            n = int(max(0, min(4, (t - s7 - 1.3) / 0.15)))
            word = "NARX"[:n]
            d.text((230, 935), word, font=SEMI(56), fill=INK + (int(255 * af),), anchor="lm")
            if int(t * 2) % 2 == 0 and n < 4:
                cx = 230 + SEMI(56).getlength(word) + 6
                d.line([(cx, 905), (cx, 965)], fill=(214, 140, 60, int(255 * af)), width=4)
            d.rounded_rectangle((760, 900, 892, 970), 35, fill=GOLD + (int(255 * af),))
            d.text((826, 935), "➤" if False else "→", font=SEMI(44), fill=INK + (int(255 * af),), anchor="mm")
            img.alpha_composite(lay)
        text(img, (W // 2, 1060), "— narxlarni direktga yuboramiz", MED(34), (225, 218, 205), a_in(t, s7 + 2.0), 10, anchor="ma")
        text(img, (W // 2, 1110), "Пришлите фото окна или напишите NARX", MED(28), (200, 193, 181), a_in(t, s7 + 2.2), 10, anchor="ma")
        text(img, (W // 2, 1500), "Toshkentda o‘lchov va o‘rnatish bepul · 1 yil kafolat", MED(30), PAPER, a_in(t, s7 + 0.6), 8, anchor="ma")
        text(img, (W // 2, 1550), "+998 33 751 11 88  ·  @imperial_jalyuzi_uz", MED(28), GOLD, a_in(t, s7 + 0.8), 8, anchor="ma")
    return np.asarray(img)


def render_ov(sel=None):
    os.makedirs(f"{D}/ovb", exist_ok=True)
    idx = sel if sel else list(range(NF))
    with Pool(6) as p:
        for k in range(0, len(idx), 24):
            ch = idx[k:k + 24]
            for i, a in zip(ch, p.map(frame, ch)):
                Image.fromarray(a).save(f"{D}/ovb/{i:04d}.png", compress_level=1)


def music():
    from rhodes_bed import rhodes_bed, BEAT
    s = ST
    plan = dict(chords=[(0, 48, [60, 63, 67, 70]), (s[1], 44, [56, 60, 63, 67]), (s[2], 51, [58, 63, 67, 70]),
                        (s[3], 46, [58, 62, 65, 69]), (s[5], 44, [60, 63, 68, 72]), (s[6], 48, [60, 63, 67, 72])],
                hats=(s[1], s[6] + 1.5), hits=[s[1]])
    rhodes_bed(f"{D}/bed_b.wav", TOTAL, plan)


def final():
    os.makedirs(f"{D}/out", exist_ok=True)
    sh(f"ffmpeg -nostdin -v error -y -i {D}/base_b.mp4 -framerate 30 -i {D}/ovb/%04d.png -i {D}/bed_b.wav "
       f"-filter_complex \"[0:v][1:v]overlay=0:0:format=auto,format=yuv420p[v];"
       f"[2:a]loudnorm=I=-15:TP=-1.5:LRA=9[a]\" -map \"[v]\" -map \"[a]\" -t {TOTAL:.3f} "
       f"-c:v libx264 -preset slow -crf 18 -pix_fmt yuv420p -color_primaries bt709 -color_trc bt709 -colorspace bt709 "
       f"-c:a aac -b:a 192k -movflags +faststart {D}/out/imperial_kechasi_ovozsiz.mp4")


if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else "all"
    print("starts", [round(x, 2) for x in ST], "total", round(TOTAL, 2))
    if what in ("base", "all"):
        base()
    if what == "prev":
        for t in map(float, sys.argv[2].split(",")):
            Image.fromarray(frame(int(t * FPS))).save(f"{D}/cs/ov_{t}.png")
    if what in ("ov", "all"):
        render_ov()
    if what in ("music", "all"):
        music()
    if what in ("final", "all"):
        final()
