"""Qora plisse — «Parda ortida» VOICE version (Daniel, from the owner's screen recording).
Scenes are timed to the narration; voice ducked over the handpan bed.
python3 build_pv.py [vo|base|prev t,t|ov|music|final|all]
"""
import os
import subprocess
import sys
from multiprocessing import Pool

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, "/home/claude/reels/common")
sys.path.insert(0, "/home/claude/reels/qora_plisse")
from build_b import GOLD, INK, LOGO, MED, PAPER, SEMI, SER, SERI, a_in, a_out, check, grad, text, topgrad  # noqa: E402
from build_p import chip  # noqa: E402

D = "/home/claude/reels/qora_plisse"
REC = "/mnt/user-data/attachments/29c18e40-edfd-55e7-a3e1-da5539b3418b/ee2054fc-ScreenRecording_11-09-2026_13-50-41_1.mp4"
W, H, FPS = 1080, 1920, 30
XF = 0.35
SC = [
    ("p1", "st/p_open.mp4", 3.0, 7.5, 0.9),
    ("p2", "st/p_close.mp4", 0.0, 4.6, 0.92),
    ("p3", "st/sash.mp4", 0.0, 2.9, 0.66),
    ("p4", "st/niche2.mp4", 0.6, 1.55, 1.0),
    ("p5", "src/7f2e1bbb-image.jpg", 0, 1.4, "in"),
    ("p6", "src/001448d6-image.jpg", 0, 4.9, "out"),
    ("p7", "st/macro.mp4", 1.0, 5.8, 1.0),
    ("end", "src/05f5857d-image.jpg", 0, 6.9, "blur"),
]


def odur(s):
    return s[3] / s[4] if isinstance(s[4], float) else s[3]


ST, _t = [], 0.0
for s in SC:
    ST.append(_t)
    _t += odur(s) - XF
TOTAL = _t + XF
NF = int(round(TOTAL * FPS))
S = ST
# voice chunks from the recording: (rec_start, rec_end, place_at)
VO = [
    (2.55, 4.00, 0.35),            # Parda ortida nima bor?
    (4.75, 9.90, 2.75),            # Qora romga — mos plisse. Har bir tabaqaga alohida.
    (10.85, 15.25, S[1] + 0.35),   # Parda — chiroy uchun. Plisse — har kuni.
    (16.05, 19.80, S[2] + 0.22),   # Deraza ochilsa — plisse u bilan birga ochiladi.
    (20.55, 26.50, S[3] + 0.08),   # Kabinet, hammom, deraza tokchasi — hammasi bitta uslubda.
    (27.60, 32.60, S[6] + 0.30),   # Toshkentda o'lchov va o'rnatish — bepul. Uch kunda tayyor.
    (33.45, 38.50, S[7] + 0.35),   # Sizga qaysi xona yoqdi? Izohga raqamini yozing.
]
REVEAL = (5.4 - 3.0) / 0.9
W_KAB, W_HAM, W_TOK, W_ALL = (VO[4][2] + x for x in (0.10, 1.10, 2.10, 3.75))
W_BEP, W_3K = VO[5][2], VO[5][2] + 3.8
W_Q, W_IZ = VO[6][2] + 0.1, VO[6][2] + 2.9


def sh(cmd):
    subprocess.run(cmd, shell=True, check=True)


def vo():
    os.makedirs(f"{D}/vo", exist_ok=True)
    sh(f"ffmpeg -nostdin -v error -y -i {REC} -vn -ac 1 -ar 48000 {D}/vo/rec.wav")
    parts, mix = [], []
    for k, (a, b, at) in enumerate(VO):
        parts.append(f"[0:a]atrim={a}:{b},asetpts=PTS-STARTPTS,afade=t=in:d=0.04,afade=t=out:st={b - a - 0.08:.3f}:d=0.08,"
                     f"adelay={int(at * 1000)}|{int(at * 1000)}[c{k}]")
        mix.append(f"[c{k}]")
    fc = ";".join(parts) + f";{''.join(mix)}amix=inputs={len(VO)}:normalize=0,apad,atrim=0:{TOTAL:.3f},"
    fc += "highpass=f=75,lowpass=f=12000,acompressor=threshold=-20dB:ratio=3:attack=8:release=120,loudnorm=I=-16:TP=-2[v]"
    sh(f"ffmpeg -nostdin -v error -y -i {D}/vo/rec.wav -filter_complex \"{fc}\" -map \"[v]\" -ar 48000 {D}/vo/vo_pv.wav")


def base():
    os.makedirs(f"{D}/bpv", exist_ok=True)
    for s in SC:
        name, src, ss, d, sp = s
        out = f"{D}/bpv/{name}.mp4"
        od = odur(s)
        if src.endswith(".jpg"):
            if sp == "blur":
                vf = (f"scale=1188:2112:force_original_aspect_ratio=increase,crop=1188:2112,"
                      f"zoompan=z='1.0+0.03*on/({od}*30)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=1080x1920:fps=30,"
                      f"gblur=sigma=18,eq=brightness=-0.32:saturation=0.75:contrast=0.9")
            else:
                z = f"1.0+0.06*on/({od}*30)" if sp == "in" else f"1.07-0.07*on/({od}*30)"
                vf = (f"scale=2160:3840:force_original_aspect_ratio=increase,crop=2160:3840,"
                      f"zoompan=z='{z}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=1080x1920:fps=30,"
                      f"eq=contrast=1.04:saturation=1.02,unsharp=5:5:0.3")
            sh(f"ffmpeg -nostdin -v error -y -loop 1 -i {D}/{src} -vf \"{vf},format=yuv420p\" -t {od:.3f} "
               f"-c:v libx264 -preset fast -crf 15 -pix_fmt yuv420p {out}")
        else:
            interp = ",minterpolate=fps=30:mi_mode=blend" if sp < 0.8 else ""
            sh(f"ffmpeg -nostdin -v error -y -ss {ss} -t {d} -i {D}/{src} -an -vf "
               f"\"setpts=PTS/{sp}{interp},fps=30,trim=duration={od:.3f},setsar=1,format=yuv420p\" "
               f"-c:v libx264 -preset fast -crf 15 -pix_fmt yuv420p {out}")
    ins = " ".join(f"-i {D}/bpv/{s[0]}.mp4" for s in SC)
    f = [f"[{i}:v]fps=30,setpts=PTS-STARTPTS,settb=AVTB[v{i}]" for i in range(len(SC))]
    prev = "[v0]"
    trans = {1: "fade", 2: "fade", 3: "smoothleft", 4: "smoothleft", 5: "smoothleft", 6: "fade", 7: "fade"}
    for i in range(1, len(SC)):
        f.append(f"{prev}[v{i}]xfade=transition={trans[i]}:duration={XF}:offset={ST[i]:.3f},settb=AVTB[x{i}]")
        prev = f"[x{i}]"
    sh(f"ffmpeg -nostdin -v error -y {ins} -filter_complex \"{';'.join(f)}\" -map \"{prev}\" -r 30 "
       f"-c:v libx264 -preset fast -crf 15 -pix_fmt yuv420p {D}/base_pv.mp4")


def frame(i):
    t = i / FPS
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    s1, s2, s3, s4, s5, s6, s7, s8 = ST
    # 1 hook + reveal
    if t < s2 + 0.3:
        al = a_out(t, REVEAL - 0.4)
        topgrad(img, 820, 0.5 * al)
        chip(img, t, 0.0, s2 - 0.2, "01 · YOTOQXONA")
        text(img, (86, 390), "Parda ortida", SER(108), PAPER, a_in(t, 0.3) * al, 18)
        text(img, (86, 505), "nima bor?", SERI(108), GOLD, a_in(t, 0.9) * al, 18)
        text(img, (90, 640), "Что за шторой?", MED(32), (220, 213, 200), a_in(t, 1.1) * al, 10)
        a2 = a_in(t, VO[1][2]) * a_out(t, s2 - 0.1)
        grad(img, 1150, 1900, 0.8 * a2)
        text(img, (86, 1420), "Qora romga —", SER(96), PAPER, a2, 18)
        text(img, (86, 1528), "mos plisse.", SERI(96), GOLD, a_in(t, VO[1][2] + 0.9) * a_out(t, s2 - 0.1), 18)
        text(img, (90, 1650), "Har bir tabaqaga alohida · На каждую створку", MED(30), (215, 208, 196),
             a_in(t, VO[1][2] + 2.9) * a_out(t, s2 - 0.1), 10)
    # 2 curtain closes
    if s2 - 0.1 < t < s3 + 0.3:
        al = a_out(t, s3 - 0.25)
        grad(img, 1150, 1900, 0.8 * al)
        text(img, (86, 1410), "Parda — chiroy uchun.", SEMI(66), PAPER, a_in(t, VO[2][2] + 0.05) * al, 16)
        text(img, (86, 1500), "Plisse — har kuni.", SERI(92), GOLD, a_in(t, VO[2][2] + 2.5) * al, 16)
        text(img, (90, 1622), "Шторы — для красоты, плиссе — на каждый день.", MED(30), (215, 208, 196),
             a_in(t, VO[2][2] + 2.7) * al, 10)
    # 3 sash
    if s3 - 0.1 < t < s4 + 0.3:
        al = a_out(t, s4 - 0.1)
        grad(img, 1180, 1900, 0.82 * al)
        text(img, (86, 1440), "Deraza ochilsa —", SEMI(66), PAPER, a_in(t, VO[3][2] + 0.05) * al, 16)
        text(img, (86, 1528), "plisse u bilan birga.", SERI(88), GOLD, a_in(t, VO[3][2] + 1.3) * al, 16)
        text(img, (90, 1645), "Открывается вместе с окном.", MED(30), (215, 208, 196), a_in(t, VO[3][2] + 1.5) * al, 10)
    # 4-6 rooms on the spoken words
    rooms = [(W_KAB, s5, "02 · KABINET", "Kabinet", "Кабинет"),
             (W_HAM, s6, "03 · HAMMOM", "Hammom", "Ванная"),
             (W_TOK, W_ALL - 0.1, "04 · DERAZA TOKCHASI", "Deraza tokchasi", "Уголок у окна")]
    for (t0, t1, lab, big, ru) in rooms:
        if t0 - 0.2 < t < t1 + 0.3:
            al = a_out(t, t1 - 0.15, 0.2)
            chip(img, t, t0 - 0.15, t1 - 0.1, lab)
            grad(img, 1350, 1900, 0.7 * al)
            text(img, (86, 1560), big, SERI(92), PAPER, a_in(t, t0 - 0.05, 0.3) * al, 14)
            text(img, (90, 1680), ru, MED(30), (215, 208, 196), a_in(t, t0 + 0.1, 0.3) * al, 8)
    if W_ALL - 0.2 < t < s7 + 0.3:
        al = a_out(t, s7 - 0.1)
        grad(img, 1300, 1900, 0.75 * al)
        text(img, (86, 1500), "Hammasi —", SER(84), PAPER, a_in(t, W_ALL) * al, 16)
        text(img, (86, 1596), "bitta uslubda.", SERI(92), GOLD, a_in(t, W_ALL + 0.5) * al, 16)
        text(img, (90, 1716), "Всё — в одном стиле.", MED(30), (215, 208, 196), a_in(t, W_ALL + 0.7) * al, 10)
    # 7 benefits on the close-up
    if s7 - 0.1 < t < s8 + 0.3:
        al = a_out(t, s8 - 0.1)
        grad(img, 1000, 1900, 0.86 * al)
        text(img, (86, 1090), "IMPERIAL · TOSHKENT", F_MONO(), GOLD, a_in(t, s7 + 0.1) * al, 8, tracking=6)
        check(img, 86, 1170, a_in(t, W_BEP) * al, "O‘lchov va o‘rnatish", "bepul · Замер и установка бесплатно")
        check(img, 86, 1330, a_in(t, W_3K) * al, "3 kunda tayyor", "o‘lchovdan keyin · Готово за 3 дня")
        check(img, 86, 1490, a_in(t, W_3K + 0.6) * al, "1 yil kafolat", "Гарантия 1 год")
    # end card
    if t > s8 - 0.2:
        a0 = a_in(t, s8)
        lg = LOGO.copy()
        lg.thumbnail((380, 180))
        lg.putalpha(lg.split()[3].point(lambda v: int(v * a0)))
        img.alpha_composite(lg, ((W - lg.width) // 2, 320))
        text(img, (W // 2, 540), "Sizga qaysi xona", SER(88), PAPER, a_in(t, W_Q), 14, anchor="ma")
        text(img, (W // 2, 645), "yoqdi?", SERI(96), GOLD, a_in(t, W_Q + 0.35), 14, anchor="ma")
        text(img, (W // 2, 790), "Izohga raqamini yozing", MED(40), PAPER, a_in(t, W_IZ), 10, anchor="ma")
        # four numbered chips
        for k in range(4):
            ak = a_in(t, W_IZ + 0.15 + 0.12 * k)
            if ak > 0.01:
                lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
                d = ImageDraw.Draw(lay)
                cx = 255 + k * 190
                d.ellipse((cx - 62, 870 - 8 * (1 - ak), cx + 62, 994 - 8 * (1 - ak)), outline=GOLD + (int(255 * ak),), width=3,
                          fill=(20, 18, 16, int(150 * ak)))
                d.text((cx, 932 - 8 * (1 - ak)), str(k + 1), font=SER(70), fill=PAPER + (int(255 * ak),), anchor="mm")
                img.alpha_composite(lay)
        labs = ["Yotoqxona", "Kabinet", "Hammom", "Tokcha"]
        for k, l in enumerate(labs):
            text(img, (255 + k * 190, 1012), l, MED(26), (215, 208, 196), a_in(t, W_IZ + 0.5 + 0.1 * k), 6, anchor="ma")
        text(img, (W // 2, 1180), "Narx uchun — izohga NARX yozing", SEMI(44), GOLD, a_in(t, W_IZ + 1.3), 10, anchor="ma")
        text(img, (W // 2, 1245), "Номер комнаты — в комментарии, цены — словом NARX", MED(28), (200, 193, 181),
             a_in(t, W_IZ + 1.5), 8, anchor="ma")
        text(img, (W // 2, 1520), "+998 33 751 11 88  ·  @imperial_jalyuzi_uz", MED(28), GOLD, a_in(t, s8 + 0.6), 8,
             anchor="ma")
    return np.asarray(img)


def F_MONO():
    from build_b import MONO
    return MONO(26)


def render_ov():
    os.makedirs(f"{D}/ovpv", exist_ok=True)
    idx = list(range(NF))
    with Pool(6) as p:
        for k in range(0, len(idx), 24):
            ch = idx[k:k + 24]
            for i, a in zip(ch, p.map(frame, ch)):
                Image.fromarray(a).save(f"{D}/ovpv/{i:04d}.png", compress_level=1)


def music():
    from handpan_bed import handpan_bed
    beat = 0.75
    prog = [[50, 57, 62, 65, 69], [46, 58, 62, 65, 70], [48, 60, 64, 67, 72], [45, 57, 61, 64, 69]]
    pads, notes = [], []
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
    plan = dict(notes=notes, pads=pads, ding=[REVEAL, ST[7]], whoosh=[(0.8, 3.0), (ST[1] + 0.6, 3.6)])
    handpan_bed(f"{D}/bed_pv.wav", TOTAL, plan)


def final():
    os.makedirs(f"{D}/out", exist_ok=True)
    fc = ("[0:v][1:v]overlay=0:0:format=auto,format=yuv420p[v];"
          "[3:a]asplit=2[vo1][vo2];"
          "[2:a]volume=-14dB[bed];[bed][vo1]sidechaincompress=threshold=0.03:ratio=6:attack=20:release=350[duck];"
          "[duck][vo2]amix=inputs=2:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=9[a]")
    sh(f"ffmpeg -nostdin -v error -y -i {D}/base_pv.mp4 -framerate 30 -i {D}/ovpv/%04d.png -i {D}/bed_pv.wav "
       f"-i {D}/vo/vo_pv.wav -filter_complex \"{fc}\" -map \"[v]\" -map \"[a]\" -t {TOTAL:.3f} "
       f"-c:v libx264 -preset slow -crf 18 -pix_fmt yuv420p -color_primaries bt709 -color_trc bt709 -colorspace bt709 "
       f"-c:a aac -b:a 192k -movflags +faststart {D}/out/imperial_parda_ortida_ovozli.mp4")


if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else "all"
    print("starts", [round(x, 2) for x in ST], "total", round(TOTAL, 2), "vo", [round(v[2], 2) for v in VO])
    if what in ("vo", "all"):
        vo()
    if what in ("base", "all"):
        base()
    if what == "prev":
        ims = []
        for tt in map(float, sys.argv[2].split(",")):
            sh(f"ffmpeg -v error -y -ss {tt} -i {D}/base_pv.mp4 -frames:v 1 {D}/cs/pb.png")
            b = Image.open(f"{D}/cs/pb.png").convert("RGBA")
            b.alpha_composite(Image.fromarray(frame(int(tt * FPS))))
            ims.append(b.convert("RGB").resize((300, 533)))
        c = Image.new("RGB", (305 * len(ims), 533), "white")
        for k, im in enumerate(ims):
            c.paste(im, (k * 305, 0))
        c.save(f"{D}/cs/prev_pv.jpg", quality=85)
    if what in ("ov", "all"):
        render_ov()
    if what in ("music", "all"):
        music()
    if what in ("final", "all"):
        final()
