"""«Ekranni bosib turing — qaysi raqam chiqdi?» kombo pause-game (Jalyuzi Classic). New format: 12 numbered kombo
variants flash in the same rounded «slot window» (0.33 s each, 27 flashes); the viewer holds the screen to stop on
one and comments the number. Then two slow close-ups (classic / geometric pattern) and an end card with all 12 as a
numbered grid. Source: the owner's two Telegram showroom videos (cards.py).
python3 build_slot.py [game|base|prev t,t|ov|music|final|cover|all]
"""
import os
import subprocess
import sys
from multiprocessing import Pool

import cv2
import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, "/home/claude/reels/kombo_tg")
sys.path.insert(0, "/home/claude/reels/common")
sys.path.insert(0, "/home/claude/reels/qora_plisse")
import cards as C  # noqa: E402
from build_b import a_in, a_out, grad, topgrad  # noqa: E402
sys.path.insert(0, "/home/claude/reels/common/brand")
from brand import LOGO, NAME, PHONE  # noqa: E402
from classic_style import CREAM, GOLD, INK, MED, PAPER, SEMI, SER, SERI, font_for, text  # noqa: E402

D = C.D
W, H, FPS = 1080, 1920, 30
FL = 10                                              # frames per flash (0.333 s)
ORDER = [0, 6, 3, 9, 1, 7, 4, 10, 2, 8, 5, 11, 7, 2, 11, 4, 8, 0, 10, 5, 6, 1, 9, 3, 5, 9, 1]
GAME = len(ORDER) * FL / FPS                         # 9.0 s
SC = [("game", GAME), ("b1", 2.6), ("b2", 2.6), ("end", 7.4)]
XFS = {1: 0.2, 2: 0.3, 3: 0.3}
TRANS = {1: "fadewhite", 2: "slideleft", 3: "fade"}
ST = [0.0]
for i in range(1, len(SC)):
    ST.append(ST[-1] + SC[i - 1][1] - XFS[i])
TOTAL = ST[-1] + SC[-1][1]
NF = int(round(TOTAL * FPS))
S_B1, S_B2, S_END = ST[1:]
SUB = (222, 212, 198)
FAM = {"klassik": ("Klassik naqsh", "Классический узор"), "geometrik": ("Geometrik naqsh", "Геометрия")}
ENC = "-c:v libx264 -preset fast -crf 15 -pix_fmt yuv420p"
# grid on the end card: 4 columns x 3 rows
GW, GH, GX0, GY0, GGAP = 200, 242, 110, 590, 20


def sh(cmd):
    subprocess.run(cmd, shell=True, check=True)


def flash_at(t):
    k = int(t * FPS) // FL
    return ORDER[k] if 0 <= k < len(ORDER) else None


def game():
    """compose the flash section frame by frame (slot window) -> bo/game.mp4"""
    os.makedirs(f"{D}/bo", exist_ok=True)
    cache, seen = {}, {}
    enc = subprocess.Popen(["ffmpeg", "-nostdin", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s",
                            f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "fast", "-crf", "14",
                            "-pix_fmt", "yuv420p", f"{D}/bo/game.mp4"], stdin=subprocess.PIPE)
    for v in ORDER:
        c = seen.get(v, 0)
        seen[v] = c + 1
        vid, ss, dur, *_ = C.VAR[v]
        off = min(max(0.0, dur - 0.4), 0.15 + c * 0.45)
        key = (v, c)
        if key not in cache:
            cache[key] = C.frames(vid, ss + off, FL / FPS + 0.1)
        frs = cache[key]
        for j in range(FL):
            enc.stdin.write(C.compose(frs[min(j, len(frs) - 1)], v).tobytes())
    enc.stdin.close()
    enc.wait()


def base():
    os.makedirs(f"{D}/bo", exist_ok=True)
    if not os.path.exists(f"{D}/bo/game.mp4"):
        game()
    G = "eq=contrast=1.05:saturation=1.08,unsharp=5:5:0.4"
    sh(f"ffmpeg -nostdin -v error -y -ss 44.5 -t 2.7 -i {D}/src/tg1.mp4 -an -vf \"scale=1188:2112:flags=lanczos,"
       f"crop=1080:1920:'54-30*t/2.6':96,fps=30,{G},trim=duration=2.6,format=yuv420p\" {ENC} {D}/bo/b1.mp4")
    sh(f"ffmpeg -nostdin -v error -y -ss 11.0 -t 2.7 -i {D}/src/tg2.mp4 -an -vf \"scale=1080:1920:flags=lanczos,fps=30,"
       f"{G},trim=duration=2.6,format=yuv420p\" {ENC} {D}/bo/b2.mp4")
    v, ss, *_ = C.VAR[3]
    sh(f"ffmpeg -nostdin -v error -y -ss {ss} -i {D}/src/{v}.mp4 -an -vf \"scale=1080:1920,setpts=PTS/0.25,fps=30,"
       f"tpad=stop_mode=clone:stop_duration=8,trim=duration=7.5,setpts=PTS-STARTPTS,gblur=sigma=22,"
       f"eq=brightness=-0.36:saturation=0.75,format=yuv420p\" {ENC} {D}/bo/end.mp4")
    ins = " ".join(f"-i {D}/bo/{s[0]}.mp4" for s in SC)
    f = [f"[{i}:v]fps=30,setpts=PTS-STARTPTS,settb=AVTB[v{i}]" for i in range(len(SC))]
    prev = "[v0]"
    for i in range(1, len(SC)):
        f.append(f"{prev}[v{i}]xfade=transition={TRANS[i]}:duration={XFS[i]}:offset={ST[i]:.3f},settb=AVTB[x{i}]")
        prev = f"[x{i}]"
    sh(f"ffmpeg -nostdin -v error -y {ins} -filter_complex \"{';'.join(f)}\" -map \"{prev}\" -r 30 {ENC} "
       f"{D}/base_slot.mp4")


_thumbs = None


def thumbs():
    global _thumbs
    if _thumbs is None:
        _thumbs = []
        for i in range(12):
            im = Image.fromarray(C.still(i)).resize((GW, GH), Image.LANCZOS).convert("RGBA")
            m = Image.new("L", (GW, GH), 0)
            ImageDraw.Draw(m).rounded_rectangle((0, 0, GW - 1, GH - 1), 16, fill=255)
            im.putalpha(m)
            _thumbs.append(im)
    return _thumbs


def badge(img, cx, cy, r, n, al, pop=1.0):
    if al <= 0.01:
        return
    r = int(r * pop)
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=GOLD + (int(255 * al),), outline=CREAM + (int(230 * al),), width=5)
    d.text((cx, cy + int(r * 0.04)), str(n), font=SER(int(r * (1.2 if n < 10 else 1.0))), fill=INK + (int(255 * al),),
           anchor="mm")
    img.alpha_composite(lay)


def pill_text(img, xy, s, font, al, anchor="la", pad=(22, 12), fill=(24, 20, 17), a=170, col=CREAM):
    if al <= 0.01:
        return
    f = font_for(s, font)
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    l, t, r, b = d.textbbox(xy, s, font=f, anchor=anchor)
    d.rounded_rectangle((l - pad[0], t - pad[1], r + pad[0], b + pad[1]), (b - t) // 2 + pad[1],
                        fill=fill + (int(a * al),))
    img.alpha_composite(lay)
    text(img, xy, s, font, col, al, 0, anchor=anchor)


def pause_icon(img, t):
    al = a_out(t, 1.3, 0.3)
    if al <= 0.01:
        return
    s = 1 + 0.08 * np.sin(t * 9)
    cx, cy, r = 540, 970, int(120 * s)
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(20, 18, 16, int(165 * al)), outline=GOLD + (int(255 * al),),
              width=6)
    bw, bh, gap = int(26 * s), int(100 * s), int(22 * s)
    for x in (cx - gap - bw, cx + gap):
        d.rounded_rectangle((x, cy - bh // 2, x + bw, cy + bh // 2), 8, fill=CREAM + (int(255 * al),))
    img.alpha_composite(lay)


def lower(img, t, t0, t1, top, rib, ru, y=1440):
    al = a_in(t, t0 + 0.12, 0.3) * a_out(t, t1 - 0.2, 0.22)
    if al <= 0.01:
        return
    grad(img, 1150, 1920, 0.82 * al)
    text(img, (86, y), top, SEMI(62), PAPER, al, 14)
    text(img, (98, y + 94), rib, SERI(76), GOLD, a_in(t, t0 + 0.3, 0.3) * a_out(t, t1 - 0.2, 0.22), 14)
    text(img, (90, y + 218), ru, MED(30), SUB, a_in(t, t0 + 0.45, 0.3) * a_out(t, t1 - 0.2, 0.22), 10)


def frame(i):
    t = i / FPS
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if t < GAME + 0.1:
        al = a_out(t, GAME - 0.15, 0.2)
        topgrad(img, 420, 0.6 * al)
        text(img, (W // 2, 248), "Ekranni bosib turing —", SEMI(50), PAPER, al, 0, anchor="ma")
        text(img, (W // 2, 318), "qaysi raqam chiqdi?", SERI(62), GOLD, al, 0, anchor="ma")
        v = flash_at(t)
        if v is not None:
            k = int(t * FPS) % FL
            pop = 1.18 - 0.18 * min(1, k / 3)
            badge(img, 150, 470, 64, v + 1, al, pop)
            uz, ru = FAM[C.FAMILY[v]]
            pill_text(img, (112, 1468), uz, MED(30), al, anchor="ls")
        pause_icon(img, t)
        text(img, (W // 2, 1572), "Удерживайте экран — какой номер выпал?", MED(30), CREAM, al, 0, anchor="ma")
        text(img, (W // 2, 1622), "Izohga yozing: «Menga 7 chiqdi»", MED(28), SUB, a_in(t, 1.5, 0.3) * al, 0,
             anchor="ma")
    lower(img, t, S_B1, S_B2 + 0.1, "Klassik naqsh —", "hashamatli.", "Классический узор — роскошно.")
    lower(img, t, S_B2, S_END + 0.1, "Geometrik naqsh —", "zamonaviy.", "Геометрия — современно.")
    if t > S_END - 0.2:
        a0 = a_in(t, S_END + 0.05)
        lg = LOGO.copy()
        lg.thumbnail((330, 170))
        lg.putalpha(lg.split()[3].point(lambda x: int(x * a0)))
        img.alpha_composite(lg, ((W - lg.width) // 2, 160))
        text(img, (W // 2, 345), "Qaysi raqam chiqdi?", SER(66), PAPER, a_in(t, S_END + 0.15), 14, anchor="ma")
        text(img, (W // 2, 428), "Izohga yozing", SERI(64), GOLD, a_in(t, S_END + 0.3), 14, anchor="ma")
        text(img, (W // 2, 528), "Какой номер выпал? Напишите в комментариях", MED(28), SUB, a_in(t, S_END + 0.45), 10,
             anchor="ma")
        th = thumbs()
        hi = int((t - S_END - 1.6) / 0.28) % 12 if t > S_END + 1.6 else -1
        for k in range(12):
            r_, c_ = divmod(k, 4)
            x = GX0 + c_ * (GW + GGAP)
            y = GY0 + r_ * (GH + GGAP)
            ak = a_in(t, S_END + 0.35 + 0.05 * k, 0.25)
            if ak <= 0.01:
                continue
            im = th[k].copy()
            im.putalpha(im.split()[3].point(lambda p: int(p * ak)))
            img.alpha_composite(im, (x, y))
            if k == hi:
                lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
                ImageDraw.Draw(lay).rounded_rectangle((x - 6, y - 6, x + GW + 5, y + GH + 5), 20, outline=GOLD + (255,),
                                                      width=6)
                img.alpha_composite(lay)
            badge(img, x + 34, y + 34, 28, k + 1, ak, 1.15 if k == hi else 1.0)
        text(img, (W // 2, 1388), "Yoqqanining raqamini direktga yuboring", MED(34), (236, 228, 214),
             a_in(t, S_END + 1.2), 10, anchor="ma")
        text(img, (W // 2, 1436), "Пришлите номер в директ", MED(28), SUB, a_in(t, S_END + 1.3), 10, anchor="ma")
        text(img, (W // 2, 1500), "Qo‘ng‘iroq qiling · Звоните", MED(30), SUB, a_in(t, S_END + 0.9), 8, anchor="ma")
        text(img, (W // 2, 1548), PHONE, SEMI(58), GOLD, a_in(t, S_END + 1.0), 8, anchor="ma")
    return np.asarray(img)


def render_ov():
    os.makedirs(f"{D}/ov_slot", exist_ok=True)
    thumbs()
    idx = list(range(NF))
    with Pool(6) as p:
        for k in range(0, len(idx), 24):
            ch = idx[k:k + 24]
            for i, a in zip(ch, p.map(frame, ch)):
                Image.fromarray(a).save(f"{D}/ov_slot/{i:04d}.png", compress_level=1)


def music():
    from gameshow_bed import gameshow_bed
    ft = [k * FL / FPS for k in range(len(ORDER))]
    gameshow_bed(f"{D}/bed_slot.wav", TOTAL, ft, GAME - 0.1)


OUTN = "classic_kombo_toxtating"


def final():
    os.makedirs(f"{D}/out", exist_ok=True)
    sh(f"ffmpeg -nostdin -v error -y -i {D}/base_slot.mp4 -framerate 30 -i {D}/ov_slot/%04d.png -i {D}/bed_slot.wav "
       f"-filter_complex \"[0:v][1:v]overlay=0:0:format=auto,format=yuv420p[v];"
       f"[2:a]loudnorm=I=-14:TP=-1.5:LRA=9[a]\" -map \"[v]\" -map \"[a]\" -t {TOTAL:.3f} "
       f"-c:v libx264 -preset slow -crf 18 -pix_fmt yuv420p -color_primaries bt709 -color_trc bt709 -colorspace bt709 "
       f"-c:a aac -b:a 192k -movflags +faststart {D}/out/{OUTN}.mp4")


def cover():
    tt = 0.6
    sh(f"ffmpeg -v error -y -ss {tt} -i {D}/base_slot.mp4 -frames:v 1 {D}/cs/cb.png")
    b = Image.open(f"{D}/cs/cb.png").convert("RGBA")
    b.alpha_composite(Image.fromarray(frame(int(tt * FPS))))
    b.convert("RGB").save(f"{D}/out/{OUTN}_muqova.jpg", quality=92)


if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else "all"
    print("starts", [round(x, 2) for x in ST], "total", round(TOTAL, 2), "game", GAME)
    if what == "game":
        game()
    if what in ("base", "all"):
        base()
    if what == "prev":
        ims = []
        for tt in map(float, sys.argv[2].split(",")):
            sh(f"ffmpeg -v error -y -ss {tt} -i {D}/base_slot.mp4 -frames:v 1 {D}/cs/pb.png")
            b = Image.open(f"{D}/cs/pb.png").convert("RGBA")
            b.alpha_composite(Image.fromarray(frame(int(tt * FPS))))
            ims.append(b.convert("RGB").resize((360, 640)))
        c = Image.new("RGB", (365 * len(ims), 640), "white")
        for k, im in enumerate(ims):
            c.paste(im, (k * 365, 0))
        c.save(f"{D}/cs/prev_slot.jpg", quality=85)
    if what in ("ov", "all"):
        render_ov()
    if what in ("music", "all"):
        music()
    if what in ("final", "all"):
        final()
    if what in ("cover", "all"):
        cover()
