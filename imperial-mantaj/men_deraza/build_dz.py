"""«Men — derazangizman» (JALYUZI CLASSIC, owner 22.11, voiced): the window speaks (Daniel). Every word appears as it
is said (Classic «Quyosh» style, key word on the orange ribbon), cuts land on the words: «ertalab / tushda /
kechqurun» are three hard cuts, «quyosh juda ko‘p» burns to white, «plisse kiydirishdi» comes out of the white,
«butunlay» dims the room. Music: chang_bed (#25), ducked under the voice.
python3 build_dz.py [base|prev t,t|ov|music|final|cover|all]
"""
import json
import os
import subprocess
import sys
from multiprocessing import Pool

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, "/home/claude/reels/common")
sys.path.insert(0, "/home/claude/reels/common/brand")
from classic_style import CREAM, INK, MED, ORANGE, SEMI, SER, SERI, font_for, text  # noqa: E402
from brand import LOGO, PHONE  # noqa: E402

D = "/home/claude/reels/deraza"
W, H, FPS = 1080, 1920, 30
TIM = json.load(open(f"{D}/vo/timing.json"))
T = [c["start"] for c in TIM]
E = [c["end"] for c in TIM]
ENC = "-c:v libx264 -preset fast -crf 15 -pix_fmt yuv420p"
PHOTO = "/mnt/user-data/uploads/a584eea7-image.jpg"          # IMG_5486, white frame, beige plisse
# scene cut points (start of each scene on the timeline)
C = dict(s1=0.0, room=T[1] - 0.15, morn=T[2] - 0.1, noon=T[3] - 0.08, eve=T[4] - 0.08, me=T[5] - 0.2,
         sun=T[6] - 0.25, dress=T[8] - 0.35, choose=T[9] - 0.3, sash=T[12] - 0.35, yours=T[14] - 0.35,
         end=T[15] - 0.3)
TOTAL = round(E[-1] + 1.6, 2)
NF = int(round(TOTAL * FPS))
# scene -> (clip, source offset, transition into it, xfade)
SC = [("s1", "seg/s1.mp4", 0.0, None, 0), ("room", "seg/s2b.mp4", 0.0, None, 0), ("morn", "seg/m704.mp4", 0.2, None, 0),
      ("noon", "seg/noon.mp4", 0.6, None, 0), ("eve", "seg/s2c.mp4", 0.5, None, 0),
      ("me", "seg/w619.mp4", 0.0, "fade", 0.3), ("sun", "seg/s4.mp4", 0.0, None, 0),
      ("dress", "seg/s5.mp4", 0.6, None, 0), ("choose", "seg/s6.mp4", 0.6, "fade", 0.3),
      ("sash", "seg/photo.mp4", 0.0, "fade", 0.4), ("yours", "seg/s8.mp4", 0.0, "fade", 0.4),
      ("end", "bo/end.mp4", 0.0, "fade", 0.5)]


def sh(cmd):
    subprocess.run(cmd, shell=True, check=True)


def a_in(t, t0, d=0.3):
    u = np.clip((t - t0) / d, 0, 1)
    return float(u * u * (3 - 2 * u))


def a_out(t, t1, d=0.25):
    return 1 - a_in(t, t1, d)


def base():
    os.makedirs(f"{D}/bo", exist_ok=True)
    d_sash = C["yours"] - C["sash"] + 0.6
    nfr = int(d_sash * FPS) + 2
    sh(f"ffmpeg -nostdin -v error -y -loop 1 -framerate 30 -i {PHOTO} -vf \"scale=1620:-2,"
       f"zoompan=z='1.12-0.10*on/{nfr}':x='iw*0.5-(iw/zoom*0.5)':y='ih*0.42-(ih/zoom*0.42)':d=1:s=1080x1920:fps=30,"
       f"eq=contrast=1.04:saturation=1.05,setsar=1,format=yuv420p\" -frames:v {nfr} {ENC} {D}/seg/photo.mp4")
    d_end = TOTAL - C["end"] + 0.6
    nfr = int(d_end * FPS) + 2
    sh(f"ffmpeg -nostdin -v error -y -sseof -0.2 -i {D}/seg/s8.mp4 -frames:v 1 {D}/bo/end_src.png")
    sh(f"ffmpeg -nostdin -v error -y -loop 1 -framerate 30 -i {D}/bo/end_src.png -vf \"zoompan=z='1.08+0.04*on/{nfr}'"
       f":x='iw*0.5-(iw/zoom*0.5)':y='ih*0.5-(ih/zoom*0.5)':d=1:s=1080x1920:fps=30,gblur=sigma=18,"
       f"eq=brightness=-0.24:saturation=0.85,setsar=1,format=yuv420p\" -frames:v {nfr} {ENC} {D}/bo/end.mp4")
    starts = [C[k] for k, *_ in SC]
    durs = [(starts[i + 1] if i + 1 < len(SC) else TOTAL) - starts[i] + (SC[i + 1][4] if i + 1 < len(SC) else 0)
            for i in range(len(SC))]
    ins, f = [], []
    for i, (k, path, off, tr, xf) in enumerate(SC):
        ins.append(f"-ss {off} -i {D}/{path}" if off else f"-i {D}/{path}")
        f.append(f"[{i}:v]fps=30,setpts=PTS-STARTPTS,settb=AVTB,trim=duration={durs[i]:.3f},"
                 f"tpad=stop_mode=clone:stop_duration=3,trim=duration={durs[i]:.3f},setpts=PTS-STARTPTS[v{i}]")
    prev, acc = "[v0]", durs[0]
    for i in range(1, len(SC)):
        k, path, off, tr, xf = SC[i]
        if tr:
            f.append(f"{prev}[v{i}]xfade=transition={tr}:duration={xf}:offset={starts[i]:.3f},settb=AVTB[x{i}]")
        else:
            f.append(f"{prev}[v{i}]concat=n=2:v=1:a=0,settb=AVTB[x{i}]")
        prev = f"[x{i}]"
    sh(f"ffmpeg -nostdin -v error -y {' '.join(ins)} -filter_complex \"{';'.join(f)}\" -map \"{prev}\" -r 30 "
       f"-t {TOTAL:.3f} {ENC} {D}/base_dz.mp4")


# ---- captions: words revealed in time ----
# (chunk ids, lines of (word, ribbon?), ru, y)
G = [([0], [[("Kuniga", 0), ("necha", 0), ("marta", 0)], [("derazaga", 1), ("qaraysiz?", 0)]],
      "Сколько раз в день вы смотрите в окно?", 1300),
     ([1], [[("Men", 0), ("esa", 0), ("sizni", 0)], [("har", 0), ("kuni", 0), ("ko‘raman:", 0)]],
      "А я вижу вас каждый день:", 1300),
     ([5], [[("Men", 0), ("—", 0)], [("derazangizman.", 1)]], "Я — ваше окно.", 1300),
     ([6, 7], [[("Lekin", 0), ("ba’zan...", 0)], [("quyosh", 0), ("juda ko‘p.", 1)]],
      "Но иногда солнца слишком много.", 1300),
     ([8], [[("Shunda", 0), ("menga", 0)], [("plisse", 1), ("kiydirishdi.", 0)]], "И тогда мне надели плиссе.", 1300),
     ([9, 10, 11], [[("Endi", 0), ("yorug‘likni", 0)], [("o‘zim", 1), ("tanlayman:", 0)], [("bir", 0), ("oz...", 0),
                                                                                           ("yoki", 0),
                                                                                           ("butunlay.", 1)]],
      "Теперь свет выбираю я: немного — или полностью.", 1240),
     ([12, 13], [[("Har", 0), ("bir", 0), ("tabaqamga", 0), ("—", 0)], [("alohida.", 1)]], "Каждой створке — отдельно.",
      1300),
     ([14], [[("Sizning", 0), ("derazangiz", 0), ("ham", 0)], [("shunday", 1), ("bo‘lishni", 0)], [("xohlaydi.", 0)]],
      "Ваше окно тоже этого хочет.", 1240)]
SZ = 74


def word_times(chunks, nwords):
    """spread the group's words over its chunks by character length"""
    segs = [(TIM[c]["start"], TIM[c]["end"]) for c in chunks]
    tot = sum(e - s for s, e in segs)
    out = []
    for k in range(nwords):
        u = k / nwords * tot
        for s, e in segs:
            if u <= (e - s) + 1e-6:
                out.append(s + u - 0.06)
                break
            u -= (e - s)
    return out


def draw_group(img, t, g, t_end):
    chunks, lines, ru, y0 = g
    words = [w for ln in lines for w in ln]
    wt = word_times(chunks, len(words))
    al_g = a_out(t, t_end, 0.25)
    if t < wt[0] - 0.05 or al_g <= 0.01:
        return
    # gradient
    gr = np.zeros((H, W, 4), np.uint8)
    v = np.clip((np.arange(H) - (y0 - 300)) / 460, 0, 1) ** 1.3 * 0.78 * a_in(t, wt[0] - 0.2, 0.3) * al_g
    gr[..., 3] = (v[:, None] * 255).astype(np.uint8)
    img.alpha_composite(Image.fromarray(gr))
    k = 0
    y = y0
    for ln in lines:
        fonts = [SERI(SZ) if rb else SER(SZ) for _, rb in ln]
        widths = [font_for(w, f).getlength(w) + (0.36 * f.size if rb else 0) for (w, rb), f in zip(ln, fonts)]
        sp = 22
        x = (W - (sum(widths) + sp * (len(ln) - 1))) / 2
        for (w, rb), f, wd in zip(ln, fonts, widths):
            a = a_in(t, wt[k], 0.18) * al_g
            text(img, (x + (0.18 * f.size if rb else 0), y), w, f, CREAM, a, 18)
            x += wd + sp
            k += 1
        y += int(SZ * 1.42)
    text(img, (W // 2, y + 6), ru, MED(30), (232, 222, 206), a_in(t, wt[0] + 0.3, 0.4) * al_g, 10, anchor="ma")


def chips(img, t):
    """ertalab / tushda / kechqurun: one big ribbon word per cut"""
    for k, (w, ru) in enumerate([("ertalab", "утром"), ("tushda", "днём"), ("kechqurun", "вечером")]):
        t0 = T[2 + k] - 0.06
        t1 = (T[3 + k] - 0.1) if k < 2 else (C["me"] - 0.05)
        if t0 - 0.05 < t < t1 + 0.2:
            a = a_in(t, t0, 0.12) * a_out(t, t1, 0.15)
            cl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            ImageDraw.Draw(cl).ellipse((140, 780, 940, 1110), fill=(15, 10, 6, int(150 * a)))
            img.alpha_composite(cl.filter(ImageFilter.GaussianBlur(60)))
            text(img, (W // 2, 860), w, SERI(130), CREAM, a, 30, anchor="ma")
            text(img, (W // 2, 1030), ru, MED(36), CREAM, a, 10, anchor="ma")


def frame(i):
    t = i / FPS
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ends = [T[1] - 0.15, E[1] + 0.25, T[6] - 0.3, T[8] - 0.4, T[9] - 0.35, T[12] - 0.4, T[14] - 0.4, C["end"] - 0.1]
    for g, te in zip(G, ends):
        draw_group(img, t, g, te)
    if C["morn"] - 0.2 < t < C["me"] + 0.2:
        chips(img, t)
    # «quyosh juda ko‘p»: burn to white, then «plisse» comes out of the white
    wb = a_in(t, T[7] - 0.2, E[7] - T[7] + 0.3) * a_out(t, C["dress"] + 0.05, 0.45)
    if wb > 0.01:
        lay = Image.new("RGBA", (W, H), (255, 250, 238, int(255 * 0.92 * wb)))
        img = Image.alpha_composite(lay, img)
    # «butunlay»: the room dims
    dm = a_in(t, T[11], 0.6) * a_out(t, C["sash"] + 0.1, 0.4) * 0.45
    if dm > 0.01:
        img = Image.alpha_composite(Image.new("RGBA", (W, H), (10, 8, 6, int(255 * dm))), img)
    # end card
    if t > C["end"] - 0.1:
        s0 = C["end"] + 0.2
        lg = LOGO.copy()
        lg.thumbnail((560, 300))
        a0 = a_in(t, s0, 0.4)
        lg.putalpha(lg.split()[3].point(lambda v: int(v * a0)))
        img.alpha_composite(lg, ((W - lg.width) // 2, 300))
        text(img, (W // 2, 640), "Plisse jalyuzi", SER(84), CREAM, a_in(t, s0 + 0.2), 14, anchor="ma")
        text(img, (W // 2, 760), "har bir derazaga", SERI(66), INK, a_in(t, s0 + 0.4), 14, anchor="ma")
        text(img, (W // 2, 1000), "Narxini bilish uchun", MED(42), CREAM, a_in(t, T[15] - 0.05), 10, anchor="ma")
        text(img, (W // 2, 1060), "qo‘ng‘iroq qiling:", MED(42), CREAM, a_in(t, T[15] + 0.8), 10, anchor="ma")
        text(img, (W // 2, 1140), PHONE, SEMI(80), ORANGE, a_in(t, T[15] + 1.2), 10, anchor="ma")
        text(img, (W // 2, 1300), "Yoki derazangiz rasmini", MED(40), CREAM, a_in(t, T[16] - 0.05), 10, anchor="ma")
        text(img, (W // 2, 1358), "direktga yuboring", SERI(54), INK, a_in(t, T[17] - 0.05), 10, anchor="ma")
        text(img, (W // 2, 1470), "Цены — по телефону или пришлите фото окна в директ", MED(26), (225, 215, 200),
             a_in(t, T[17] + 0.4), 10, anchor="ma")
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
    from chang_bed import chang_bed
    chang_bed(f"{D}/bed.wav", TOTAL, dict(sun=C["sun"], dress=C["dress"], choose=C["choose"], end=C["end"]))


OUTN = "classic_men_derazangizman"


def final():
    os.makedirs(f"{D}/out", exist_ok=True)
    sh(f"ffmpeg -nostdin -v error -y -i {D}/base_dz.mp4 -framerate 30 -i {D}/ov/%04d.png -i {D}/vo/voice.wav "
       f"-i {D}/bed.wav -filter_complex \""
       f"[0:v][1:v]overlay=0:0:format=auto,format=yuv420p[v];"
       f"[2:a]aresample=48000,highpass=f=70,acompressor=threshold=-20dB:ratio=3:attack=5:release=120,"
       f"volume=1.0,asplit=2[vo][key];"
       f"[3:a]aresample=48000,volume=0.20[mu];"
       f"[mu][key]sidechaincompress=threshold=0.03:ratio=6:attack=20:release=350[duck];"
       f"[vo][duck]amix=inputs=2:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11[a]\" "
       f"-map \"[v]\" -map \"[a]\" -t {TOTAL:.3f} -c:v libx264 -preset slow -crf 18 -pix_fmt yuv420p "
       f"-color_primaries bt709 -color_trc bt709 -colorspace bt709 -c:a aac -b:a 192k -movflags +faststart "
       f"{D}/out/{OUTN}.mp4")


def cover():
    tt = 9.0
    sh(f"ffmpeg -v error -y -ss {tt} -i {D}/base_dz.mp4 -frames:v 1 {D}/cb.png")
    b = Image.open(f"{D}/cb.png").convert("RGBA")
    b.alpha_composite(Image.fromarray(frame(int(tt * FPS))))
    b.convert("RGB").save(f"{D}/out/{OUTN}_muqova.jpg", quality=92)


if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else "all"
    print("cuts", {k: round(v, 2) for k, v in C.items()}, "total", TOTAL)
    if what in ("base", "all"):
        base()
    if what == "prev":
        ims = []
        for tt in map(float, sys.argv[2].split(",")):
            sh(f"ffmpeg -v error -y -ss {tt} -i {D}/base_dz.mp4 -frames:v 1 {D}/pb.png")
            b = Image.open(f"{D}/pb.png").convert("RGBA")
            b.alpha_composite(Image.fromarray(frame(int(tt * FPS))))
            ims.append(b.convert("RGB").resize((360, 640)))
        c = Image.new("RGB", (365 * len(ims), 640), "white")
        for k, im in enumerate(ims):
            c.paste(im, (k * 365, 0))
        c.save(f"{D}/prev_dz.jpg", quality=85)
    if what in ("ov", "all"):
        render_ov()
    if what in ("music", "all"):
        music()
    if what in ("final", "all"):
        final()
    if what in ("cover", "all"):
        cover()
