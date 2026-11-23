"""«Bu — marmar?» (JALYUZI CLASSIC, owner 23.11, new dikey: white patterned tulle + cream fabric with gold veins).
A still close-up looks like grey-veined marble; liquid gold runs along the veins (gold.py); the still comes alive —
it is fabric. Then the tulle pan, the lamellas turning, the night window, the room from the ceiling down, Classic end
card. Music: glass_bed (#26).
python3 build_d6.py [gold|base|prev t,t|ov|music|final|cover|all]
"""
import os
import subprocess
import sys
from multiprocessing import Pool

import numpy as np
from PIL import Image

sys.path.insert(0, "/home/claude/reels/common")
sys.path.insert(0, "/home/claude/reels/common/brand")
from classic_style import CREAM, INK, MED, ORANGE, SEMI, SER, SERI, text  # noqa: E402
from brand import LOGO, PHONE  # noqa: E402

D = "/home/claude/reels/dikey6"
W, H, FPS = 1080, 1920, 30
ENC = "-c:v libx264 -preset fast -crf 15 -pix_fmt yuv420p"
XF = 0.3
# scene, file, start on timeline
SC = [("still", "seg/still.mp4", 0.0), ("alive", "seg/gold.mp4", 3.3), ("macro", "seg/macro.mp4", 5.7),
      ("pan", "seg/pan.mp4", 8.0), ("wide", "seg/wide.mp4", 11.2), ("turn", "seg/turn.mp4", 14.4),
      ("open", "seg/open.mp4", 17.6), ("night", "seg/night.mp4", 20.8), ("wall", "seg/wall.mp4", 24.0),
      ("reveal", "seg/reveal.mp4", 27.2), ("end", "bo/end.mp4", 31.0)]
TOTAL = 36.6
NF = int(round(TOTAL * FPS))
S = {k: s for k, _, s in SC}


def sh(cmd):
    subprocess.run(cmd, shell=True, check=True)


def a_in(t, t0, d=0.4):
    u = np.clip((t - t0) / d, 0, 1)
    return float(u * u * (3 - 2 * u))


def a_out(t, t1, d=0.3):
    return 1 - a_in(t, t1, d)


def gold():
    sh(f"ffmpeg -nostdin -v error -y -i {D}/seg/gold.mp4 -frames:v 1 {D}/still0.png")
    sh(f"cd {D} && python3 gold.py still0.png goldfr 3.6")
    sh(f"ffmpeg -nostdin -v error -y -framerate 30 -i {D}/goldfr/%04d.jpg {ENC} {D}/seg/still.mp4")


def base():
    os.makedirs(f"{D}/bo", exist_ok=True)
    nfr = int((TOTAL - S["end"] + 0.6) * FPS) + 2
    sh(f"ffmpeg -nostdin -v error -y -sseof -0.2 -i {D}/seg/reveal.mp4 -frames:v 1 {D}/bo/end_src.png")
    sh(f"ffmpeg -nostdin -v error -y -loop 1 -framerate 30 -i {D}/bo/end_src.png -vf \"zoompan=z='1.06+0.05*on/{nfr}'"
       f":x='iw*0.5-(iw/zoom*0.5)':y='ih*0.4-(ih/zoom*0.4)':d=1:s=1080x1920:fps=30,gblur=sigma=16,"
       f"eq=brightness=-0.30:saturation=0.9,setsar=1,format=yuv420p\" -frames:v {nfr} {ENC} {D}/bo/end.mp4")
    starts = [s for _, _, s in SC]
    durs = [(starts[i + 1] + XF if i + 1 < len(SC) else TOTAL) - starts[i] for i in range(len(SC))]
    ins = " ".join(f"-i {D}/{p}" for _, p, _ in SC)
    f = [f"[{i}:v]fps=30,setpts=PTS-STARTPTS,settb=AVTB,tpad=stop_mode=clone:stop_duration=3,"
         f"trim=duration={durs[i]:.3f},setpts=PTS-STARTPTS[v{i}]" for i in range(len(SC))]
    prev = "[v0]"
    for i in range(1, len(SC)):
        f.append(f"{prev}[v{i}]xfade=transition=fade:duration={XF}:offset={starts[i]:.3f},settb=AVTB[x{i}]")
        prev = f"[x{i}]"
    sh(f"ffmpeg -nostdin -v error -y {ins} -filter_complex \"{';'.join(f)}\" -map \"{prev}\" -r 30 "
       f"-t {TOTAL:.3f} {ENC} {D}/base_d6.mp4")


def caption(img, t, t0, t1, top, rib, ru, y=1400):
    al = a_in(t, t0, 0.35) * a_out(t, t1, 0.3)
    if al <= 0.01:
        return
    g = np.zeros((H, W, 4), np.uint8)
    v = np.clip((np.arange(H) - (y - 300)) / 440, 0, 1) ** 1.3 * 0.80 * al
    g[..., 3] = (v[:, None] * 255).astype(np.uint8)
    img.alpha_composite(Image.fromarray(g))
    text(img, (W // 2, y), top, SER(72), CREAM, al, 16, anchor="ma")
    text(img, (W // 2, y + 114), rib, SERI(74), INK, a_in(t, t0 + 0.25, 0.35) * a_out(t, t1, 0.3), 14, anchor="ma")
    if ru:
        text(img, (W // 2, y + 240), ru, MED(30), (238, 230, 216), a_in(t, t0 + 0.45, 0.35) * a_out(t, t1, 0.3),
             10, anchor="ma")


CAPS = [(-1.0, 3.1, "Bu —", "marmarmi?", "Это — мрамор?"),
        (3.45, 5.5, "Yo‘q.", "Bu — mato.", "Нет. Это ткань."),
        (5.85, 7.8, "Har bir tomir —", "oltin rangda.", "Каждая прожилка — цвета золота."),
        (8.15, 11.0, "Oltin tomirli mato", "+ naqshli tyul", "Ткань с золотыми прожилками и узорный тюль"),
        (11.35, 14.2, "O‘rtada —", "oq naqshli tyul.", "В центре — белый узорный тюль."),
        (14.55, 17.4, "Dikey jalyuzi —", "tyul va mato birga", "Вертикальные жалюзи: тюль и ткань вместе"),
        (18.4, 20.6, "Bir harakat —", "deraza ochiq.", "Одно движение — и окно открыто."),
        (20.95, 23.8, "Kechasi —", "yopiq va sokin.", "Ночью — закрыто и спокойно."),
        (24.15, 27.0, "Butun devor —", "bitta kompozitsiya.", "Вся стена — одна композиция."),
        (27.35, 30.8, "Xonangizga —", "oltin tafsil.", "Золотая деталь для вашего дома.")]


def frame(i):
    t = i / FPS
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    for t0, t1, top, rib, ru in CAPS:
        caption(img, t, t0, t1, top, rib, ru)
    if t > S["end"] - 0.1:
        s0 = S["end"] + 0.2
        lg = LOGO.copy()
        lg.thumbnail((560, 300))
        a0 = a_in(t, s0, 0.4)
        lg.putalpha(lg.split()[3].point(lambda v: int(v * a0)))
        img.alpha_composite(lg, ((W - lg.width) // 2, 300))
        text(img, (W // 2, 640), "Dikey jalyuzi", SER(84), CREAM, a_in(t, s0 + 0.2), 14, anchor="ma")
        text(img, (W // 2, 760), "oltin tomirli", SERI(66), INK, a_in(t, s0 + 0.4), 14, anchor="ma")
        text(img, (W // 2, 870), "Вертикальные жалюзи с золотыми прожилками", MED(28), (232, 222, 206),
             a_in(t, s0 + 0.6), 10, anchor="ma")
        text(img, (W // 2, 1050), "Narxini bilish uchun", MED(42), CREAM, a_in(t, s0 + 0.9), 10, anchor="ma")
        text(img, (W // 2, 1110), "qo‘ng‘iroq qiling:", MED(42), CREAM, a_in(t, s0 + 1.0), 10, anchor="ma")
        text(img, (W // 2, 1190), PHONE, SEMI(80), ORANGE, a_in(t, s0 + 1.2), 10, anchor="ma")
        text(img, (W // 2, 1350), "Yoki deraza rasmini", MED(40), CREAM, a_in(t, s0 + 1.6), 10, anchor="ma")
        text(img, (W // 2, 1408), "direktga yuboring", SERI(54), INK, a_in(t, s0 + 1.8), 10, anchor="ma")
        text(img, (W // 2, 1520), "Цены — по телефону или пришлите фото окна в директ", MED(26), (225, 215, 200),
             a_in(t, s0 + 2.0), 10, anchor="ma")
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
    from glass_bed import glass_bed
    glass_bed(f"{D}/bed.wav", TOTAL, [S[k] for k in ("macro", "pan", "wide", "turn", "open", "night", "wall",
                                                    "reveal")], S["alive"], S["end"])


OUTN = "classic_dikey_marmarmi_v2"


def final():
    os.makedirs(f"{D}/out", exist_ok=True)
    sh(f"ffmpeg -nostdin -v error -y -i {D}/base_d6.mp4 -framerate 30 -i {D}/ov/%04d.png -i {D}/bed.wav "
       f"-filter_complex \"[0:v][1:v]overlay=0:0:format=auto,format=yuv420p[v];"
       f"[2:a]loudnorm=I=-15:TP=-1.5:LRA=11[a]\" -map \"[v]\" -map \"[a]\" -t {TOTAL:.3f} "
       f"-c:v libx264 -preset slow -crf 18 -pix_fmt yuv420p -color_primaries bt709 -color_trc bt709 -colorspace bt709 "
       f"-c:a aac -b:a 192k -movflags +faststart {D}/out/{OUTN}.mp4")


def cover():
    tt = 2.2
    sh(f"ffmpeg -v error -y -ss {tt} -i {D}/base_d6.mp4 -frames:v 1 {D}/cb.png")
    b = Image.open(f"{D}/cb.png").convert("RGBA")
    b.alpha_composite(Image.fromarray(frame(int(tt * FPS))))
    b.convert("RGB").save(f"{D}/out/{OUTN}_muqova.jpg", quality=92)


if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else "all"
    if what in ("gold", "all"):
        gold()
    if what in ("base", "all"):
        base()
    if what == "prev":
        ims = []
        for tt in map(float, sys.argv[2].split(",")):
            sh(f"ffmpeg -v error -y -ss {tt} -i {D}/base_d6.mp4 -frames:v 1 {D}/pb.png")
            b = Image.open(f"{D}/pb.png").convert("RGBA")
            b.alpha_composite(Image.fromarray(frame(int(tt * FPS))))
            ims.append(b.convert("RGB").resize((360, 640)))
        c = Image.new("RGB", (365 * len(ims), 640), "white")
        for k, im in enumerate(ims):
            c.paste(im, (k * 365, 0))
        c.save(f"{D}/prev_d6.jpg", quality=85)
    if what in ("ov", "all"):
        render_ov()
    if what in ("music", "all"):
        music()
    if what in ("final", "all"):
        final()
    if what in ("cover", "all"):
        cover()
