"""«Bu rasmni quyosh chizgan» (JALYUZI CLASSIC, rollo, owner 24.11; silent: text + music).
The rollo as a gallery canvas: an orange line traces the sunlit window shape the sun «painted» on the blind;
gallery frame + museum placards («Muallif: quyosh. Kanvas: rollo jalyuzi»); one movement opens the view, another
softens the light; the fabric up close; end card «Rasmni — quyosh chizadi. Rolloni — biz tayyorlaymiz.»
Music: cello_bed (#28, new). python3 build_r1.py [base|prev t,t|ov|music|final|cover|all]
"""
import json
import os
import subprocess
import sys
from multiprocessing import Pool

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, "/home/claude/reels/common")
sys.path.insert(0, "/home/claude/reels/common/brand")
from classic_style import CREAM, INK, MED, ORANGE, SEMI, SER, SERI, text  # noqa: E402
from brand import LOGO, PHONE  # noqa: E402

D = "/home/claude/reels/rollo1"
W, H, FPS = 1080, 1920, 30
ENC = "-c:v libx264 -preset fast -crf 15 -pix_fmt yuv420p"
XF = 0.3
SC = [("trace", "seg/trace.mp4", 0.0), ("gal", "seg/gal.mp4", 3.7), ("rise", "seg/rise.mp4", 7.6),
      ("view", "seg/view.mp4", 12.2), ("down", "seg/down.mp4", 14.2), ("tex", "seg/tex.mp4", 18.2),
      ("wide", "seg/wide.mp4", 21.4), ("end", "bo/end.mp4", 24.2)]
TOTAL = 30.0
NF = int(round(TOTAL * FPS))
S = {k: s for k, _, s in SC}
TR = json.load(open(f"{D}/trace.json"))
LINE = (246, 176, 112)
PEN = (255, 242, 222)
GLOW = (240, 150, 80)


def sh(cmd):
    subprocess.run(cmd, shell=True, check=True)


def a_in(t, t0, d=0.4):
    u = np.clip((t - t0) / d, 0, 1)
    return float(u * u * (3 - 2 * u))


def a_out(t, t1, d=0.3):
    return 1 - a_in(t, t1, d)


def base():
    os.makedirs(f"{D}/bo", exist_ok=True)
    nfr = int((TOTAL - S["end"] + 0.6) * FPS) + 2
    sh(f"ffmpeg -nostdin -v error -y -ss 1.0 -i {D}/seg/trace.mp4 -frames:v 1 {D}/bo/end_src.png")
    sh(f"ffmpeg -nostdin -v error -y -loop 1 -framerate 30 -i {D}/bo/end_src.png -vf \"zoompan=z='1.05+0.05*on/{nfr}'"
       f":x='iw*0.5-(iw/zoom*0.5)':y='ih*0.55-(ih/zoom*0.55)':d=1:s=1080x1920:fps=30,gblur=sigma=20,"
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
       f"-t {TOTAL:.3f} {ENC} {D}/base_r1.mp4")


def caption(img, t, t0, t1, top, rib, ru, y=1400, up=False):
    al = a_in(t, t0, 0.35) * a_out(t, t1, 0.3)
    if al <= 0.01:
        return
    g = np.zeros((H, W, 4), np.uint8)
    if up:
        v = np.clip(((y + 560) - np.arange(H)) / 480, 0, 1) ** 1.3 * 0.72 * al
    else:
        v = np.clip((np.arange(H) - (y - 300)) / 440, 0, 1) ** 1.3 * 0.78 * al
    g[..., 3] = (v[:, None] * 255).astype(np.uint8)
    img.alpha_composite(Image.fromarray(g))
    text(img, (W // 2, y), top, SER(72), CREAM, al, 16, anchor="ma")
    text(img, (W // 2, y + 114), rib, SERI(74), INK, a_in(t, t0 + 0.25, 0.35) * a_out(t, t1, 0.3), 14, anchor="ma")
    if ru:
        text(img, (W // 2, y + 240), ru, MED(30), (238, 230, 216), a_in(t, t0 + 0.45, 0.35) * a_out(t, t1, 0.3), 10,
             anchor="ma")


def frame_rect(img, t, t0, t1, inset=46):
    """thin cream gallery frame that draws itself clockwise"""
    al = a_out(t, t1, 0.3)
    fr = a_in(t, t0, 0.7)
    if fr <= 0 or al <= 0.01:
        return
    x0, y0, x1, y1 = inset, inset + 150, W - inset, H - inset - 120
    pts = [(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)]
    seg = [np.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]) for i in range(4)]
    tot, goal = sum(seg), sum(seg) * fr
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    acc = 0.0
    for i in range(4):
        if goal <= acc:
            break
        u = min(1.0, (goal - acc) / seg[i])
        (ax, ay), (bx, by) = pts[i], pts[i + 1]
        d.line([(ax, ay), (ax + (bx - ax) * u, ay + (by - ay) * u)], fill=(250, 243, 232, int(220 * al)), width=3)
        acc += seg[i]
    img.alpha_composite(lay)


def placard(img, t, t0, t1, title, lines):
    al = a_in(t, t0, 0.45) * a_out(t, t1, 0.3)
    if al <= 0.01:
        return
    dy = int(24 * (1 - a_in(t, t0, 0.45)))
    ft, fl = SER(54), MED(34)
    wmax = max([ft.getlength(title)] + [fl.getlength(s) for s in lines])
    cw, chh = int(wmax + 100), 62 + 54 + 50 * len(lines) + 30
    x, y = 96, 1640 - chh + dy
    sh_ = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(sh_).rounded_rectangle([x + 6, y + 12, x + cw + 6, y + chh + 12], 8, fill=(0, 0, 0, int(110 * al)))
    img.alpha_composite(sh_.filter(ImageFilter.GaussianBlur(14)))
    card = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(card)
    d.rounded_rectangle([x, y, x + cw, y + chh], 8, fill=(248, 243, 234, int(246 * al)))
    d.rectangle([x, y + 22, x + 7, y + chh - 22], fill=ORANGE + (int(255 * al),))
    img.alpha_composite(card)
    d = ImageDraw.Draw(img)
    d.text((x + 50, y + 40), title, font=ft, fill=(34, 30, 27, int(255 * al)))
    for k, s in enumerate(lines):
        d.text((x + 50, y + 42 + 76 + 50 * k), s, font=fl, fill=(92, 82, 72, int(255 * al)))


def trace_layer(i, t):
    """orange line drawing the sunlit window shape, with a spark at the pen tip"""
    k = min(i, TR["n"] - 1)
    p = np.array(TR["paths"][k], np.float32)
    fr = a_in(t, 0.15, 1.9)
    al = a_out(t, 3.15, 0.45)
    if fr <= 0 or al <= 0.01:
        return None
    m = max(2, int(len(p) * fr))
    q = p[:m] if fr < 1 else np.vstack([p, p[:1]])
    cv_ = np.zeros((H, W), np.float32)
    cv2.polylines(cv_, [np.round(q * 4).astype(np.int32)], False, 1.0, 6, cv2.LINE_AA, shift=2)
    glow = np.clip(cv2.GaussianBlur(cv_, (0, 0), 12) * 2.6, 0, 1)
    fill = np.zeros((H, W), np.float32)
    cv2.fillPoly(fill, [np.round(p).astype(np.int32)], 1.0, cv2.LINE_AA)
    dark = (1 - cv2.GaussianBlur(fill, (0, 0), 25)) * 0.32 * a_in(t, 0.1, 0.8)
    spark = np.zeros((H, W), np.float32)
    if fr < 1:
        hx, hy = q[-1]
        cv2.circle(spark, (int(hx), int(hy)), 9, 1.0, -1, cv2.LINE_AA)
        spark = np.clip(cv2.GaussianBlur(spark, (0, 0), 7) * 3, 0, 1)
    rgba = np.zeros((H, W, 4), np.float32)
    a_line = np.clip(cv_ + spark, 0, 1)
    a_glow = glow * 0.85
    a = a_line + a_glow * (1 - a_line)
    col = (np.array(PEN) * a_line[..., None] + np.array(GLOW) * (a_glow * (1 - a_line))[..., None]) / np.maximum(a, 1e-6)[..., None]
    col = col * (1 - spark[..., None]) + np.array([255, 236, 200]) * spark[..., None]
    a_all = a + dark * (1 - a)
    col = (col * a[..., None]) / np.maximum(a_all, 1e-6)[..., None]
    rgba[..., :3] = col
    rgba[..., 3] = a_all * 255 * al
    return Image.fromarray(np.clip(rgba, 0, 255).astype(np.uint8))


CAPS = [(-1.0, S["gal"] - 0.1, "Bu rasmni", "quyosh chizgan", "Эту картину нарисовало солнце", dict(y=300, up=True)),
        (S["rise"] + 0.3, S["view"] - 0.1, "Bir harakat —", "manzara ochiladi", "Одно движение — и открывается вид", {}),
        (S["down"] + 0.3, S["tex"] - 0.1, "Yana bir harakat —", "yorug‘lik yumshaydi", "Ещё одно — и свет мягче", {}),
        (S["tex"] + 0.3, S["wide"] - 0.1, "Yaqindan qarang —", "mato teksturasi", "Фактура ткани — вблизи", {})]
PLAQ = [(S["gal"] + 0.45, S["rise"] - 0.05, "«Tush payti»", ["Muallif: quyosh", "Kanvas: rollo jalyuzi"]),
        (S["view"] + 0.2, S["down"] - 0.05, "«Manzara»", ["Muallif: shahar", "Ramka: derazangiz"]),
        (S["wide"] + 0.3, S["end"] - 0.05, "«Har kuni — yangi asar»", ["Muallif: quyosh", "Kanvas: rollo jalyuzi"])]
FRAMES = [(S["gal"] + 0.15, S["rise"] - 0.05), (S["view"] + 0.05, S["down"] - 0.05), (S["wide"] + 0.1, S["end"] - 0.05)]


def frame(i):
    t = i / FPS
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if t < 3.7:
        lay = trace_layer(i, t)
        if lay is not None:
            img.alpha_composite(lay)
    for t0, t1 in FRAMES:
        frame_rect(img, t, t0, t1)
    for t0, t1, top, rib, ru, kw in CAPS:
        caption(img, t, t0, t1, top, rib, ru, **kw)
    for t0, t1, title, lines in PLAQ:
        placard(img, t, t0, t1, title, lines)
    if t > S["end"] - 0.1:
        s0 = S["end"] + 0.2
        lg = LOGO.copy()
        lg.thumbnail((520, 280))
        a0 = a_in(t, s0, 0.4)
        lg.putalpha(lg.split()[3].point(lambda v: int(v * a0)))
        img.alpha_composite(lg, ((W - lg.width) // 2, 290))
        text(img, (W // 2, 620), "Rasmni — quyosh chizadi.", SER(62), CREAM, a_in(t, s0 + 0.3), 14, anchor="ma")
        text(img, (W // 2, 726), "Rolloni — biz tayyorlaymiz", SERI(60), INK, a_in(t, s0 + 0.6), 14, anchor="ma")
        text(img, (W // 2, 836), "Картину рисует солнце. Рулонные шторы — мы.", MED(28), (232, 222, 206),
             a_in(t, s0 + 0.8), 10, anchor="ma")
        text(img, (W // 2, 1010), "Rollo jalyuzi", SER(56), CREAM, a_in(t, s0 + 1.1), 12, anchor="ma")
        text(img, (W // 2, 1100), "Narxini bilish uchun qo‘ng‘iroq qiling:", MED(38), CREAM, a_in(t, s0 + 1.4), 10,
             anchor="ma")
        text(img, (W // 2, 1170), PHONE, SEMI(80), ORANGE, a_in(t, s0 + 1.6), 10, anchor="ma")
        text(img, (W // 2, 1330), "Yoki deraza rasmini", MED(40), CREAM, a_in(t, s0 + 2.0), 10, anchor="ma")
        text(img, (W // 2, 1388), "direktga yuboring", SERI(54), INK, a_in(t, s0 + 2.2), 10, anchor="ma")
        text(img, (W // 2, 1500), "Цены — по телефону или пришлите фото окна в директ", MED(26), (225, 215, 200),
             a_in(t, s0 + 2.4), 10, anchor="ma")
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
    from cello_bed import cello_bed
    cello_bed(f"{D}/bed.wav", TOTAL, dict(cello=S["gal"], lift=S["rise"], soft=S["down"], end=S["end"]))


OUTN = "classic_rollo_quyosh_rasmi"


def final():
    os.makedirs(f"{D}/out", exist_ok=True)
    sh(f"ffmpeg -nostdin -v error -y -i {D}/base_r1.mp4 -framerate 30 -i {D}/ov/%04d.png -i {D}/bed.wav "
       f"-filter_complex \"[0:v][1:v]overlay=0:0:format=auto,format=yuv420p[v];"
       f"[2:a]aresample=48000,loudnorm=I=-15:TP=-1.5:LRA=11[a]\" -map \"[v]\" -map \"[a]\" -t {TOTAL:.3f} "
       f"-c:v libx264 -preset slow -crf 19 -maxrate 9M -bufsize 18M -pix_fmt yuv420p -color_primaries bt709 "
       f"-color_trc bt709 -colorspace bt709 -c:a aac -b:a 192k -movflags +faststart {D}/out/{OUTN}.mp4")


def cover():
    tt = 2.4
    sh(f"ffmpeg -v error -y -ss {tt} -i {D}/base_r1.mp4 -frames:v 1 {D}/cb.png")
    b = Image.open(f"{D}/cb.png").convert("RGBA")
    b.alpha_composite(Image.fromarray(frame(int(tt * FPS))))
    b.convert("RGB").save(f"{D}/out/{OUTN}_muqova.jpg", quality=92)


if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else "all"
    if what in ("base", "all"):
        base()
    if what == "prev":
        ims = []
        for tt in map(float, sys.argv[2].split(",")):
            sh(f"ffmpeg -v error -y -ss {tt} -i {D}/base_r1.mp4 -frames:v 1 {D}/pb.png")
            b = Image.open(f"{D}/pb.png").convert("RGBA")
            b.alpha_composite(Image.fromarray(frame(int(round(tt * FPS)))))
            ims.append(b.convert("RGB").resize((360, 640)))
        c = Image.new("RGB", (365 * len(ims), 640), "white")
        for k, im in enumerate(ims):
            c.paste(im, (k * 365, 0))
        c.save(f"{D}/prev_r1.jpg", quality=85)
    if what in ("ov", "all"):
        render_ov()
    if what in ("music", "all"):
        music()
    if what in ("final", "all"):
        final()
    if what in ("cover", "all"):
        cover()
