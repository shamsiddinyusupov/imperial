"""«Oldin / Keyin» — old blinds due for renewal (removed) -> new Imperial plisse. Sales, no voice.
python3 build_d.py [base|prev t,t|ov|music|final|all]
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

D = "/home/claude/reels/oq_rom"
W, H, FPS = 1080, 1920, 30
XF = 0.35
KP = "src/kombo_photo.jpg"
PP = "src/plisse_photo.jpg"
SC = [
    ("k1", "st/k1.mp4", 0.1, 2.0, 0.8),
    ("k2", "kphoto", 0, 3.3, None),
    ("p1", "st/p1.mp4", 0.0, 1.6, 0.8),
    ("h", "st/h.mp4", 0.0, 2.6, 0.85),
    ("p2", "st/p2.mp4", 0.0, 1.95, 0.85),
    ("p3", "st/p3.mp4", 0.0, 3.0, 1.0),
    ("split", "split", 0, 4.6, None),
    ("end", "endbg", 0, 5.4, None),
]
TRANS = {1: "fade", 2: "wiperight", 3: "smoothleft", 4: "smoothleft", 5: "smoothleft", 6: "fade", 7: "fade"}


def odur(s):
    return s[3] / s[4] if isinstance(s[4], float) else s[3]


ST, _t = [], 0.0
for s in SC:
    ST.append(_t)
    _t += odur(s) - XF
TOTAL = _t + XF
NF = int(round(TOTAL * FPS))
ENC = "-c:v libx264 -preset fast -crf 15 -pix_fmt yuv420p"
GRADE = "eq=contrast=1.04:saturation=1.03,unsharp=5:5:0.3"


def sh(cmd):
    subprocess.run(cmd, shell=True, check=True)


def zp(z0, z1, od, w=1080, h=1920):
    return f"zoompan=z='{z0}+({z1}-{z0})*on/({od}*30)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s={w}x{h}:fps=30"


def base():
    os.makedirs(f"{D}/bd", exist_ok=True)
    for s in SC:
        name, src, ss, d, sp = s
        out = f"{D}/bd/{name}.mp4"
        od = odur(s)
        if src == "kphoto":
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
    ins = " ".join(f"-i {D}/bd/{s[0]}.mp4" for s in SC)
    f = [f"[{i}:v]fps=30,setpts=PTS-STARTPTS,settb=AVTB[v{i}]" for i in range(len(SC))]
    prev = "[v0]"
    for i in range(1, len(SC)):
        dur = 0.6 if TRANS[i] == "wiperight" else XF
        off = ST[i] - (dur - XF)
        f.append(f"{prev}[v{i}]xfade=transition={TRANS[i]}:duration={dur}:offset={off:.3f},settb=AVTB[x{i}]")
        prev = f"[x{i}]"
    sh(f"ffmpeg -nostdin -v error -y {ins} -filter_complex \"{';'.join(f)}\" -map \"{prev}\" -r 30 {ENC} {D}/base_d.mp4")


def tag(img, t, t0, t1, s, x=80, y=290, fill=(20, 18, 16), fg=GOLD):
    al = a_in(t, t0) * a_out(t, t1)
    if al <= 0.01:
        return
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    f = MONO(28)
    w = sum(f.getlength(c) for c in s) + 6 * (len(s) - 1)
    d.rounded_rectangle((x, y, x + w + 52, y + 60), 30, fill=fill + (int(185 * al),), outline=fg + (int(230 * al),), width=2)
    img.alpha_composite(lay)
    text(img, (x + 26, y + 15), s, f, fg, al, 0, tracking=6)


def frame(i):
    t = i / FPS
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    s_k1, s_k2, s_p1, s_h, s_p2, s_p3, s_sp, s_end = ST
    # BEFORE
    if t < s_p1 + 0.3:
        al = a_out(t, s_p1 - 0.3)
        tag(img, t, 0.0, s_p1 - 0.25, "OLDIN · ДО", fg=(225, 218, 205))
        topgrad(img, 1050, 0.8 * al)
        text(img, (86, 380), "Eski jalyuzi", SER(110), PAPER, a_in(t, 0.05) * al, 18)
        text(img, (86, 498), "charchadimi?", SERI(110), GOLD, a_in(t, 0.35) * al, 18)
        text(img, (90, 640), "Старые жалюзи устали?", MED(32), (225, 218, 205), a_in(t, 0.9) * al, 10)
        a2 = a_in(t, s_k2 + 0.3) * al
        grad(img, 1250, 1900, 0.82 * a2)
        text(img, (86, 1480), "Bu derazadagi jalyuzining —", SEMI(60), PAPER, a2, 14)
        text(img, (86, 1556), "yangilanish vaqti kelgan edi.", SEMI(60), PAPER, a_in(t, s_k2 + 0.6) * al, 14)
        text(img, (90, 1650), "Старым жалюзи пришло время обновиться.", MED(30), (215, 208, 196),
             a_in(t, s_k2 + 0.9) * al, 10)
    # AFTER
    if s_p1 - 0.1 < t < s_sp + 0.3:
        al = a_out(t, s_sp - 0.1)
        tag(img, t, s_p1 + 0.15, s_sp - 0.1, "KEYIN · ПОСЛЕ")
        grad(img, 1150, 1900, 0.82 * al)
        text(img, (86, 1380), "Eskisini yechdik —", SEMI(66), PAPER, a_in(t, s_p1 + 0.3) * al, 16)
        text(img, (86, 1462), "yangi plisse.", SERI(110), GOLD, a_in(t, s_p1 + 0.6) * al, 16)
        lines = [(s_h + 0.2, s_p2 - 0.1, "Har bir tabaqaga alohida.", "На каждую створку отдельно."),
                 (s_p2 + 0.2, s_p3 - 0.1, "Deraza bilan birga ochiladi.", "Открывается вместе с окном."),
                 (s_p3 + 0.2, s_sp - 0.1, "Butun xona — bitta uslubda.", "Вся комната — в одном стиле.")]
        for t0, t1, uz, ru in lines:
            a3 = a_in(t, t0) * a_out(t, t1, 0.25)
            text(img, (90, 1610), uz, MED(38), PAPER, a3, 10)
            text(img, (90, 1664), ru, MED(28), (205, 198, 186), a3, 10)
    # split before / after
    if s_sp - 0.1 < t < s_end + 0.3:
        al = a_out(t, s_end - 0.1)
        topgrad(img, 820, 0.85 * al)
        grad(img, 1380, 1920, 0.88 * al)
        lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(lay)
        ad = a_in(t, s_sp + 0.2) * al
        d.rectangle((538, int(1920 * (1 - ad)), 542, 1920), fill=GOLD + (int(255 * ad),))
        img.alpha_composite(lay)
        tag(img, t, s_sp + 0.4, s_end - 0.1, "OLDIN", x=150, y=1440, fg=(225, 218, 205))
        tag(img, t, s_sp + 0.6, s_end - 0.1, "KEYIN", x=690, y=1440)
        text(img, (W // 2, 300), "Oldin va keyin.", SER(92), PAPER, a_in(t, s_sp + 0.1) * al, 14, anchor="ma")
        text(img, (W // 2, 405), "Farqi ko‘rinyaptimi?", SERI(80), GOLD, a_in(t, s_sp + 0.3) * al, 14, anchor="ma")
        text(img, (W // 2, 1580), "Sizda ham eski jalyuzi bormi?", SEMI(50), PAPER, a_in(t, s_sp + 1.1) * al, 10,
             anchor="ma")
        text(img, (W // 2, 1650), "Rasmini direktga yuboring — yangisini taklif qilamiz.", MED(32), (225, 218, 205),
             a_in(t, s_sp + 1.4) * al, 8, anchor="ma")
        text(img, (W // 2, 1700), "Пришлите фото старых жалюзи в директ.", MED(28), (205, 198, 186),
             a_in(t, s_sp + 1.6) * al, 8, anchor="ma")
    # end card
    if t > s_end - 0.2:
        a0 = a_in(t, s_end)
        lg = LOGO.copy()
        lg.thumbnail(LOGO_BOX)
        lg.putalpha(lg.split()[3].point(lambda v: int(v * a0)))
        img.alpha_composite(lg, ((W - lg.width) // 2, 265))
        text(img, (W // 2, 500), "Eskisini yechamiz —", SER(76), PAPER, a_in(t, s_end + 0.15), 14, anchor="ma")
        text(img, (W // 2, 590), "yangisini o‘rnatamiz.", SERI(80), GOLD, a_in(t, s_end + 0.3), 14, anchor="ma")
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
        text(img, (W // 2, 1560), "📞".replace("📞", "") + PHONE, SEMI(46), GOLD, a_in(t, s_end + 0.8), 8,
             anchor="ma")
    return np.asarray(img)


def render_ov():
    os.makedirs(f"{D}/ovd", exist_ok=True)
    idx = list(range(NF))
    with Pool(6) as p:
        for k in range(0, len(idx), 24):
            ch = idx[k:k + 24]
            for i, a in zip(ch, p.map(frame, ch)):
                Image.fromarray(a).save(f"{D}/ovd/{i:04d}.png", compress_level=1)


def music():
    from marimba_bed import marimba_bed, BEAT
    s = ST
    # before: sparse minor colour; after the wipe: bright major with groove
    plan = dict(chords=[(0, 40, [52, 55, 59]), (s[1], 36, [48, 52, 55]), (s[2], 43, [55, 59, 62]),
                        (s[3], 38, [50, 54, 57]), (s[5], 43, [55, 59, 62]), (s[6], 40, [52, 55, 59]),
                        (s[7], 36, [48, 52, 55, 59]), (s[7] + 4 * BEAT, 38, [50, 54, 57, 62])],
                groove=(s[2], s[7] + 3.0), hits=[(s[2], 74), (s[6], 71)])
    marimba_bed(f"{D}/bed_d.wav", TOTAL, plan)


def final():
    os.makedirs(f"{D}/out", exist_ok=True)
    sh(f"ffmpeg -nostdin -v error -y -i {D}/base_d.mp4 -framerate 30 -i {D}/ovd/%04d.png -i {D}/bed_d.wav "
       f"-filter_complex \"[0:v][1:v]overlay=0:0:format=auto,format=yuv420p[v];"
       f"[2:a]loudnorm=I=-15:TP=-1.5:LRA=9[a]\" -map \"[v]\" -map \"[a]\" -t {TOTAL:.3f} "
       f"-c:v libx264 -preset slow -crf 18 -pix_fmt yuv420p -color_primaries bt709 -color_trc bt709 -colorspace bt709 "
       f"-c:a aac -b:a 192k -movflags +faststart {D}/out/classic_oldin_keyin_plisse.mp4")


if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else "all"
    print("starts", [round(x, 2) for x in ST], "total", round(TOTAL, 2))
    if what in ("base", "all"):
        base()
    if what == "prev":
        ims = []
        for tt in map(float, sys.argv[2].split(",")):
            sh(f"ffmpeg -v error -y -ss {tt} -i {D}/base_d.mp4 -frames:v 1 {D}/cs/pb.png")
            b = Image.open(f"{D}/cs/pb.png").convert("RGBA")
            b.alpha_composite(Image.fromarray(frame(int(tt * FPS))))
            ims.append(b.convert("RGB").resize((300, 533)))
        c = Image.new("RGB", (305 * len(ims), 533), "white")
        for k, im in enumerate(ims):
            c.paste(im, (k * 305, 0))
        c.save(f"{D}/cs/prev_d.jpg", quality=85)
    if what in ("ov", "all"):
        render_ov()
    if what in ("music", "all"):
        music()
    if what in ("final", "all"):
        final()
