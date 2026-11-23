"""«Oddiy pardalardan charchadingizmi?» (JALYUZI CLASSIC, owner 23.11, dikey, Daniel voice).
Hook: a glowing line drawing of an ordinary curtain; its folds straighten into lamellas that turn open onto real
rooms (zal, bright room, wide window). «Unda — dikey jalyuzi» on the modern room. The drawn curtain returns and
its fabric drops off the rail (to wash a curtain you take it all down); one lamella lifts out of a close-up
(each one comes off on its own). Lamellas turning open, three designs, Classic end card. Music: nay_bed (#27).
python3 build_d7.py [base|prev t,t|ov|music|final|cover|all]
"""
import json
import os
import subprocess
import sys
from multiprocessing import Pool

import numpy as np
from PIL import Image

sys.path.insert(0, "/home/claude/reels/common")
sys.path.insert(0, "/home/claude/reels/common/brand")
sys.path.insert(0, "/home/claude/reels/dikey7")
from classic_style import CREAM, INK, MED, ORANGE, SEMI, SER, SERI, text  # noqa: E402
from brand import LOGO, PHONE  # noqa: E402
import lineart as la  # noqa: E402

D = "/home/claude/reels/dikey7"
W, H, FPS = 1080, 1920, 30
ENC = "-c:v libx264 -preset fast -crf 15 -pix_fmt yuv420p"
XF = 0.3
SC = [("black", "bo/black1.mp4", 0.0), ("zal", "seg/zal.mp4", 2.3), ("bright", "seg/bright.mp4", 6.35),
      ("wide", "seg/wide.mp4", 9.3), ("hero", "seg/hero.mp4", 13.2), ("black2", "bo/black2.mp4", 16.0),
      ("slat", "seg/slat.mp4", 19.45), ("turn", "seg/turn.mp4", 25.75), ("var1", "seg/var1.mp4", 28.1),
      ("var2", "seg/var2.mp4", 29.45), ("var4", "seg/var4.mp4", 30.85), ("end", "bo/end.mp4", 32.4)]
TOTAL = 41.2
NF = int(round(TOTAL * FPS))
S = {k: s for k, _, s in SC}
VT = json.load(open(f"{D}/vo/timing.json"))
# line-art timings
HOOK_MORPH, HOOK_OPEN = 2.15, 2.65
CALL_IN, CALL_DRAW, CALL_DROP, CALL_OUT = 15.85, 16.0, 18.05, 19.6


def sh(cmd):
    subprocess.run(cmd, shell=True, check=True)


def a_in(t, t0, d=0.4):
    u = np.clip((t - t0) / d, 0, 1)
    return float(u * u * (3 - 2 * u))


def a_out(t, t1, d=0.3):
    return 1 - a_in(t, t1, d)


def base():
    os.makedirs(f"{D}/bo", exist_ok=True)
    for name, dur in (("black1", 3.0), ("black2", 4.0)):
        sh(f"ffmpeg -nostdin -v error -y -f lavfi -i color=c=0x1c1612:s=1080x1920:r=30:d={dur} {ENC} {D}/bo/{name}.mp4")
    nfr = int((TOTAL - S["end"] + 0.6) * FPS) + 2
    sh(f"ffmpeg -nostdin -v error -y -ss 1.2 -i {D}/seg/zal.mp4 -frames:v 1 {D}/bo/end_src.png")
    sh(f"ffmpeg -nostdin -v error -y -loop 1 -framerate 30 -i {D}/bo/end_src.png -vf \"zoompan=z='1.05+0.05*on/{nfr}'"
       f":x='iw*0.5-(iw/zoom*0.5)':y='ih*0.35-(ih/zoom*0.35)':d=1:s=1080x1920:fps=30,gblur=sigma=18,"
       f"eq=brightness=-0.30:saturation=0.85,setsar=1,format=yuv420p\" -frames:v {nfr} {ENC} {D}/bo/end.mp4")
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
       f"-t {TOTAL:.3f} {ENC} {D}/base_d7.mp4")


def caption(img, t, t0, t1, top, rib, ru, y=1400, big=1.0, grad=True):
    al = a_in(t, t0, 0.35) * a_out(t, t1, 0.3)
    if al <= 0.01:
        return
    if grad:
        g = np.zeros((H, W, 4), np.uint8)
        v = np.clip((np.arange(H) - (y - 300)) / 440, 0, 1) ** 1.3 * 0.80 * al
        g[..., 3] = (v[:, None] * 255).astype(np.uint8)
        img.alpha_composite(Image.fromarray(g))
    text(img, (W // 2, y), top, SER(int(72 * big)), CREAM, al, 16, anchor="ma")
    text(img, (W // 2, y + int(114 * big)), rib, SERI(int(74 * big)), INK,
         a_in(t, t0 + 0.25, 0.35) * a_out(t, t1, 0.3), 14, anchor="ma")
    if ru:
        text(img, (W // 2, y + int(240 * big)), ru, MED(30), (238, 230, 216),
             a_in(t, t0 + 0.45, 0.35) * a_out(t, t1, 0.3), 10, anchor="ma")


def vs(k):
    return VT[k]["start"]


def ve(k):
    return VT[k]["end"]


# (t0, t1, top, ribbon, ru, kw)
CAPS = [(-1.0, 2.25, "Oddiy pardalardan", "charchadingizmi?", "Устали от обычных штор?", dict(grad=False)),
        (vs(1) - 0.05, vs(2) - 0.2, "Zal va yotoqxona uchun —", "qulay va chiroyli", "Удобно и красиво — для зала и спальни",
         {}),
        (vs(2) - 0.1, vs(3) - 0.15, "Boshqaruvi —", "sodda", "Простое управление", {}),
        (vs(3) - 0.1, ve(4) + 0.2, "Dizayni —", "har qanday interyerga mos", "Дизайн — под любой интерьер", {}),
        (vs(5) - 0.1, S["black2"] - 0.05, "Unda —", "dikey jalyuzi.", "Тогда — вертикальные жалюзи.", dict(big=1.18)),
        (vs(7) - 0.1, CALL_OUT - 0.3, "Pardani yuvish uchun —", "butunlay yechish kerak",
         "Штору для стирки приходится снимать целиком", dict(grad=False)),
        (vs(8) - 0.05, vs(8) + 3.25, "Dikey jalyuzida esa —", "har bir plastinka", "А у вертикальных жалюзи каждая ламель",
         {}),
        (vs(8) + 3.38, S["turn"] - 0.05, "Alohida yechiladi", "va yuviladi", "снимается и стирается отдельно", {}),
        (vs(9) - 0.1, S["var1"] - 0.05, "Ishlatish —", "juda qulay", "Пользоваться очень удобно", {}),
        (vs(10) - 0.1, S["end"] - 0.05, "Istagingizga qarab —", "tayyorlab beramiz", "Изготовим по вашему желанию", {})]


def bg_layer(i, alpha_map):
    bg = la.background() + la.grain(i)
    a = np.clip(alpha_map * 255, 0, 255).astype(np.uint8)
    return Image.fromarray(np.dstack([np.clip(bg, 0, 255).astype(np.uint8), a]))


def frame(i):
    t = i / FPS
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    # hook: drawn curtain -> lamellas open onto the rooms
    if t < HOOK_OPEN + 0.9:
        tr = t - HOOK_OPEN
        a, edges = la.reveal_alpha(tr) if tr > 0 else (np.ones((H, W), np.float32), None)
        img.alpha_composite(bg_layer(i, a))
        if edges is not None:
            e = np.zeros((H, W, 4), np.uint8)
            e[..., :3] = (250, 230, 205)
            e[..., 3] = (edges * 200).astype(np.uint8)
            img.alpha_composite(Image.fromarray(e))
        lal = a_out(t, HOOK_OPEN + 0.3, 0.5)
        if lal > 0.01:
            img.alpha_composite(la.curtain_layer(t + 0.25, morph=a_in(t, HOOK_MORPH, 0.55), line_alpha=lal,
                                                 rail_alpha=a_out(t, HOOK_MORPH, 0.35)))
    # call-back: the curtain again, its fabric drops off the rail
    if CALL_IN <= t < CALL_OUT + 0.45:
        ab = a_in(t, CALL_IN, 0.35) * a_out(t, CALL_OUT, 0.4)
        img.alpha_composite(bg_layer(i, np.full((H, W), ab, np.float32)))
        if t >= CALL_DRAW:
            dt = t - CALL_DROP if t >= CALL_DROP else None
            img.alpha_composite(la.curtain_layer(t - CALL_DRAW, speed=1.7, drop_t=dt,
                                                 line_alpha=a_out(t, CALL_OUT - 0.1, 0.35),
                                                 rail_alpha=a_out(t, CALL_DROP + 0.9, 0.4)))
    for t0, t1, top, rib, ru, kw in CAPS:
        caption(img, t, t0, t1, top, rib, ru, **kw)
    if t > S["end"] - 0.1:
        s0 = vs(11) - 0.15            # «Jalyuzi Classic»
        s1 = vs(12) - 0.1             # «Narxini bilish uchun qo‘ng‘iroq qiling»
        s2 = vs(13) - 0.1             # «yoki deraza rasmini direktga yuboring»
        lg = LOGO.copy()
        lg.thumbnail((560, 300))
        a0 = a_in(t, s0, 0.4)
        lg.putalpha(lg.split()[3].point(lambda v: int(v * a0)))
        img.alpha_composite(lg, ((W - lg.width) // 2, 300))
        text(img, (W // 2, 640), "Dikey jalyuzi", SER(84), CREAM, a_in(t, s0 + 0.2), 14, anchor="ma")
        text(img, (W // 2, 760), "istagingizga qarab", SERI(66), INK, a_in(t, s0 + 0.4), 14, anchor="ma")
        text(img, (W // 2, 870), "Вертикальные жалюзи — по вашему желанию", MED(28), (232, 222, 206),
             a_in(t, s0 + 0.6), 10, anchor="ma")
        text(img, (W // 2, 1050), "Narxini bilish uchun", MED(42), CREAM, a_in(t, s1), 10, anchor="ma")
        text(img, (W // 2, 1110), "qo‘ng‘iroq qiling:", MED(42), CREAM, a_in(t, s1 + 0.1), 10, anchor="ma")
        text(img, (W // 2, 1190), PHONE, SEMI(80), ORANGE, a_in(t, s1 + 0.3), 10, anchor="ma")
        text(img, (W // 2, 1350), "Yoki deraza rasmini", MED(40), CREAM, a_in(t, s2), 10, anchor="ma")
        text(img, (W // 2, 1408), "direktga yuboring", SERI(54), INK, a_in(t, s2 + 0.2), 10, anchor="ma")
        text(img, (W // 2, 1520), "Цены — по телефону или пришлите фото окна в директ", MED(26), (225, 215, 200),
             a_in(t, s2 + 0.4), 10, anchor="ma")
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
    from nay_bed import nay_bed
    nay_bed(f"{D}/bed.wav", TOTAL, dict(reveal=HOOK_OPEN, call=CALL_IN + 0.1, slat=S["slat"] + 0.15, go=S["turn"],
                                        end=S["end"]))


OUTN = "classic_dikey_oddiy_parda"


def final():
    os.makedirs(f"{D}/out", exist_ok=True)
    sh(f"ffmpeg -nostdin -v error -y -i {D}/base_d7.mp4 -framerate 30 -i {D}/ov/%04d.png -i {D}/vo/voice.wav "
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
    tt = 1.9
    sh(f"ffmpeg -v error -y -ss {tt} -i {D}/base_d7.mp4 -frames:v 1 {D}/cb.png")
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
            sh(f"ffmpeg -v error -y -ss {tt} -i {D}/base_d7.mp4 -frames:v 1 {D}/pb.png")
            b = Image.open(f"{D}/pb.png").convert("RGBA")
            b.alpha_composite(Image.fromarray(frame(int(round(tt * FPS)))))
            ims.append(b.convert("RGB").resize((360, 640)))
        c = Image.new("RGB", (365 * len(ims), 640), "white")
        for k, im in enumerate(ims):
            c.paste(im, (k * 365, 0))
        c.save(f"{D}/prev_d7.jpg", quality=85)
    if what in ("ov", "all"):
        render_ov()
    if what in ("music", "all"):
        music()
    if what in ("final", "all"):
        final()
    if what in ("cover", "all"):
        cover()
