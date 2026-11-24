"""«Har bir detal — o‘z joyida» v2 PREMIUM (owner 25.11: «closer and more premium, like the watch film»).
Assemblies in 3D macro with depth of field (asm3d.py), macro hero shots with the same grade (lookpass.py),
beauty shots at the end. Same text, music engine cine_bed (#29) re-timed.
(v1 notes:) «Har bir detal — o‘z joyida» (JALYUZI CLASSIC, owner 24.11; silent: text + music + sound design).
Idea from a luxury watch film the owner sent (parts land one by one in a dark studio, then the hero): four blind
types build themselves from their own real parts (asm.py), each followed by its finished room; a fast montage of
all four; the Classic logo is «engraved» by light; contacts. Music + parts sounds: cine_bed (#29, new).
python3 build_y2.py [base|prev t,t|ov|music|final|cover|all]
"""
import json
import os
import subprocess
import sys
from multiprocessing import Pool

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, "/home/claude/reels/common")
sys.path.insert(0, "/home/claude/reels/common/brand")
from classic_style import CREAM, INK, MED, ORANGE, SEMI, SER, SERI, text  # noqa: E402
from brand import LOGO, PHONE  # noqa: E402

D = "/home/claude/reels/yigil2"
W, H, FPS = 1080, 1920, 30
ENC = "-c:v libx264 -preset fast -crf 15 -pix_fmt yuv420p"
# name, file, start, transition into it, transition length
SC = [("a_dikey", "seg/b_dikey.mp4", 0.0, None, 0), ("h_dikey", "seg/L_x_dikey.mp4", 2.6, "fade", 0.3),
      ("a_kombo", "seg/b_kombo.mp4", 4.7, "fadeblack", 0.4), ("h_kombo", "seg/L_x_kombo.mp4", 7.3, "fade", 0.3),
      ("a_plisse", "seg/b_plisse.mp4", 9.4, "fadeblack", 0.4), ("h_plisse", "seg/L_x_plisse.mp4", 12.0, "fade", 0.3),
      ("a_rollo", "seg/b_rollo.mp4", 13.8, "fadeblack", 0.4), ("h_rollo", "seg/L_x_rollo.mp4", 16.4, "fade", 0.3),
      ("m_rollo", "seg/L_y_rollo.mp4", 18.5, "fade", 0.15), ("m_kombo", "seg/L_y_kombo.mp4", 19.25, "fade", 0.15),
      ("m_plisse", "seg/L_y_plisse.mp4", 20.0, "fade", 0.15), ("m_dikey", "seg/L_y_dikey.mp4", 20.75, "fade", 0.15),
      ("end", "bo/end.mp4", 21.5, "fadeblack", 0.4)]
TOTAL = 27.5
NF = int(round(TOTAL * FPS))
S = {k: s for k, _, s, _, _ in SC}
TYPES = [("a_dikey", "a_kombo", "01", "DIKEY", "Вертикальные"), ("a_kombo", "a_plisse", "02", "KOMBO", "День — ночь"),
         ("a_plisse", "a_rollo", "03", "PLISSE", "Плиссе"), ("a_rollo", "m_rollo", "04", "ROLLO", "Рулонные")]
SWEEP = {"a_dikey": 1.85, "a_kombo": 1.85, "a_plisse": 1.85, "a_rollo": 1.85}


def sh(cmd):
    subprocess.run(cmd, shell=True, check=True)


def a_in(t, t0, d=0.4):
    u = np.clip((t - t0) / d, 0, 1)
    return float(u * u * (3 - 2 * u))


def a_out(t, t1, d=0.3):
    return 1 - a_in(t, t1, d)


def base():
    os.makedirs(f"{D}/bo", exist_ok=True)
    sys.path.insert(0, D)
    import asm
    Image.fromarray(np.clip(asm.VOID[..., ::-1], 0, 255).astype(np.uint8)).save(f"{D}/bo/void.png")
    nfr = int((TOTAL - S["end"] + 0.6) * FPS) + 2
    sh(f"ffmpeg -nostdin -v error -y -loop 1 -framerate 30 -i {D}/bo/void.png -frames:v {nfr} -vf format=yuv420p {ENC} "
       f"{D}/bo/end.mp4")
    starts = [s for _, _, s, _, _ in SC]
    xfs = [x for _, _, _, _, x in SC]
    durs = [(starts[i + 1] + xfs[i + 1] if i + 1 < len(SC) else TOTAL) - starts[i] for i in range(len(SC))]
    ins = " ".join(f"-i {D}/{p}" for _, p, _, _, _ in SC)
    f = [f"[{i}:v]fps=30,setpts=PTS-STARTPTS,settb=AVTB,tpad=stop_mode=clone:stop_duration=3,"
         f"trim=duration={durs[i]:.3f},setpts=PTS-STARTPTS[v{i}]" for i in range(len(SC))]
    prev = "[v0]"
    for i in range(1, len(SC)):
        f.append(f"{prev}[v{i}]xfade=transition={SC[i][3]}:duration={SC[i][4]}:offset={starts[i]:.3f},settb=AVTB[x{i}]")
        prev = f"[x{i}]"
    sh(f"ffmpeg -nostdin -v error -y {ins} -filter_complex \"{';'.join(f)}\" -map \"{prev}\" -r 30 "
       f"-t {TOTAL:.3f} {ENC} {D}/base_y3.mp4")


_VIG = None


def vignette():
    global _VIG
    if _VIG is None:
        y = np.linspace(-1, 1, H)[:, None]
        x = np.linspace(-1, 1, W)[None, :]
        r = np.clip(np.sqrt(x ** 2 * 0.85 + y ** 2 * 0.6), 0, 1.4)
        a = (np.clip((r - 0.55) / 0.8, 0, 1) ** 1.6 * 150).astype(np.uint8)
        v = np.zeros((H, W, 4), np.uint8)
        v[..., 3] = a
        _VIG = Image.fromarray(v)
    return _VIG


def caption(img, t, t0, t1, top, rib, ru, y=1440):
    al = a_in(t, t0, 0.35) * a_out(t, t1, 0.3)
    if al <= 0.01:
        return
    g = np.zeros((H, W, 4), np.uint8)
    v = np.clip((np.arange(H) - (y - 300)) / 440, 0, 1) ** 1.3 * 0.8 * al
    g[..., 3] = (v[:, None] * 255).astype(np.uint8)
    img.alpha_composite(Image.fromarray(g))
    text(img, (W // 2, y), top, SER(72), CREAM, al, 16, anchor="ma")
    text(img, (W // 2, y + 114), rib, SERI(74), INK, a_in(t, t0 + 0.2, 0.35) * a_out(t, t1, 0.3), 14, anchor="ma")
    text(img, (W // 2, y + 240), ru, MED(30), (238, 230, 216), a_in(t, t0 + 0.4, 0.35) * a_out(t, t1, 0.3), 10,
         anchor="ma")


def label(img, t, t0, t1, num, name, ru):
    al = a_in(t, t0, 0.3) * a_out(t, t1, 0.25)
    if al <= 0.01:
        return
    g = np.zeros((H, W, 4), np.uint8)
    v = np.clip((560 - np.arange(H)) / 420, 0, 1) ** 1.4 * 0.55 * al
    g[..., 3] = (v[:, None] * 255).astype(np.uint8)
    img.alpha_composite(Image.fromarray(g))
    x0, y0 = 84, 300
    text(img, (x0, y0), num, SEMI(40), ORANGE, al, 8)
    ln = a_in(t, t0 + 0.1, 0.5)
    d = ImageDraw.Draw(img)
    d.line([(x0 + 70, y0 + 24), (x0 + 70 + 150 * ln, y0 + 24)], fill=CREAM + (int(220 * al),), width=2)
    sp = " ".join(name)
    text(img, (x0, y0 + 62), sp, SER(66), CREAM, a_in(t, t0 + 0.15, 0.35) * a_out(t, t1, 0.25), 12)
    text(img, (x0, y0 + 150), ru, MED(28), (226, 216, 200), a_in(t, t0 + 0.3, 0.35) * a_out(t, t1, 0.25), 8)


def engraved_logo(img, t, t0):
    """logo revealed by a moving diagonal light: a bright edge runs across and leaves the logo behind"""
    u = (t - t0) / 1.1
    if u <= 0:
        return
    lg = LOGO.copy()
    lg.thumbnail((560, 300))
    a = np.asarray(lg).astype(np.float32)
    h, w = a.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    pos = -0.2 * (w + h) + 1.4 * (w + h) * min(u, 1.0)
    d = xx + yy * 0.6 - pos
    reveal = np.clip(-d / 40 + 0.5, 0, 1)
    edge = np.exp(-(d / 22) ** 2) * (1 if u < 1 else max(0, 1 - (u - 1) * 3))
    rgb = a[..., :3] * reveal[..., None] + np.array([255, 240, 214]) * edge[..., None]
    al = np.clip(a[..., 3] / 255 * (reveal + edge * 0.9), 0, 1)
    out = np.dstack([np.clip(rgb, 0, 255), al * 255]).astype(np.uint8)
    img.alpha_composite(Image.fromarray(out), ((W - w) // 2, 290))


def frame(i):
    t = i / FPS
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if t < S["end"] + 0.2:
        img.alpha_composite(vignette())
    caption(img, t, -1.0, S["h_dikey"] - 0.15, "Har bir detal —", "o‘z joyida", "Каждая деталь — на своём месте")
    for a, b, num, name, ru in TYPES:
        t0 = S[a] + (0.25 if a != "a_dikey" else 0.05)
        label(img, t, t0, S[b] - 0.05, num, name, ru)
    if t > S["end"] - 0.1:
        s0 = S["end"] + 0.15
        engraved_logo(img, t, s0)
        text(img, (W // 2, 640), "Har bir detal —", SER(70), CREAM, a_in(t, s0 + 1.0), 14, anchor="ma")
        text(img, (W // 2, 752), "o‘z joyida", SERI(70), INK, a_in(t, s0 + 1.25), 14, anchor="ma")
        text(img, (W // 2, 866), "Каждая деталь — на своём месте", MED(28), (232, 222, 206), a_in(t, s0 + 1.45), 10,
             anchor="ma")
        text(img, (W // 2, 990), "Dikey  ·  Kombo  ·  Plisse  ·  Rollo", MED(38), CREAM, a_in(t, s0 + 1.7), 10,
             anchor="ma")
        text(img, (W // 2, 1110), "Narxini bilish uchun qo‘ng‘iroq qiling:", MED(38), CREAM, a_in(t, s0 + 2.0), 10,
             anchor="ma")
        text(img, (W // 2, 1180), PHONE, SEMI(80), ORANGE, a_in(t, s0 + 2.2), 10, anchor="ma")
        text(img, (W // 2, 1340), "Yoki deraza rasmini", MED(40), CREAM, a_in(t, s0 + 2.6), 10, anchor="ma")
        text(img, (W // 2, 1398), "direktga yuboring", SERI(54), INK, a_in(t, s0 + 2.8), 10, anchor="ma")
        text(img, (W // 2, 1510), "Цены — по телефону или пришлите фото окна в директ", MED(26), (225, 215, 200),
             a_in(t, s0 + 3.0), 10, anchor="ma")
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
    from cine_bed import cine_bed
    ev = dict(clicks=[], ticks=[], rolls=[], sweeps=[], hits=[], risers=[(S["m_rollo"] - 1.4, S["m_rollo"])],
              end=S["end"] + 0.15)
    for a in ("a_dikey", "a_kombo", "a_plisse", "a_rollo"):
        land = json.load(open(f"{D}/seg/b_{a[2:]}.json"))["land"]
        if a == "a_plisse":
            ev["ticks"] += [S[a] + x for x in land]
        elif a == "a_rollo":
            ev["rolls"].append((S[a] + land[0], S[a] + land[1]))
        else:
            ev["clicks"] += [S[a] + x for x in land]
        ev["sweeps"].append(S[a] + SWEEP[a])
    ev["hits"] = [S[h] for h in ("h_dikey", "h_kombo", "h_plisse", "h_rollo", "m_rollo", "m_kombo", "m_plisse",
                                 "m_dikey")]
    cine_bed(f"{D}/bed3.wav", TOTAL, ev)


OUTN = "classic_har_bir_detal_premium"


def final():
    os.makedirs(f"{D}/out", exist_ok=True)
    sh(f"ffmpeg -nostdin -v error -y -i {D}/base_y3.mp4 -framerate 30 -i {D}/ov/%04d.png -i {D}/bed.wav "
       f"-filter_complex \"[0:v][1:v]overlay=0:0:format=auto,format=yuv420p[v];"
       f"[2:a]aresample=48000,loudnorm=I=-14:TP=-1.5:LRA=11[a]\" -map \"[v]\" -map \"[a]\" -t {TOTAL:.3f} "
       f"-c:v libx264 -preset slow -crf 19 -maxrate 9M -bufsize 18M -pix_fmt yuv420p -color_primaries bt709 "
       f"-color_trc bt709 -colorspace bt709 -c:a aac -b:a 192k -movflags +faststart {D}/out/{OUTN}.mp4")


def cover():
    tt = 2.2
    sh(f"ffmpeg -v error -y -ss {tt} -i {D}/base_y3.mp4 -frames:v 1 {D}/cb.png")
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
            sh(f"ffmpeg -v error -y -ss {tt} -i {D}/base_y3.mp4 -frames:v 1 {D}/pb.png")
            b = Image.open(f"{D}/pb.png").convert("RGBA")
            b.alpha_composite(Image.fromarray(frame(int(round(tt * FPS)))))
            ims.append(b.convert("RGB").resize((360, 640)))
        c = Image.new("RGB", (365 * len(ims), 640), "white")
        for k, im in enumerate(ims):
            c.paste(im, (k * 365, 0))
        c.save(f"{D}/prev_y3.jpg", quality=85)
    if what in ("ov", "all"):
        render_ov()
    if what in ("music", "all"):
        music()
    if what in ("final", "all"):
        final()
    if what in ("cover", "all"):
        cover()
