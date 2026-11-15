"""«Kombo kolleksiyasi — jurnal» (IMPERIAL). New format for Imperial: a fashion-magazine lookbook. Cover (full-bleed
macro, «KOMBO» masthead, cover lines) -> 6 paper pages turning like a magazine, each with a framed close-up of one
kombo, a big Didone number, a poetic name, RU name, pattern family and 3 colour chips taken from the fabric ->
dark back cover: «Qaysi sahifa sizga yoqdi?» with the 6 pages as thumbnails, NARX, free measuring in Tashkent, contacts.
Imperial editorial type: Latin Modern (Didone) + Pagella italic + Inter Display + Lora italic (RU).
Footage: unused close-up parts of the owner's two Telegram showroom videos (the Classic «To‘xtating» Reels used the
frontal shots). Music: clavecin_bed (#18).
python3 build_mag.py [base|prev t,t|ov|music|final|cover|all]
"""
import glob
import os
import subprocess
import sys
from multiprocessing import Pool

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, "/home/claude/reels/common")
sys.path.insert(0, "/home/claude/reels/qora_plisse")
from build_b import a_in, a_out, grad, topgrad  # noqa: E402

D = "/home/claude/reels/kombo_tg"
W, H, FPS = 1080, 1920, 30


def g(n):
    return glob.glob(f"/usr/share/**/{n}", recursive=True)[0]


_F = {}


def F(path, size):
    k = (path, size)
    if k not in _F:
        _F[k] = ImageFont.truetype(path, size)
    return _F[k]


DID_P, ITA_P = g("lmroman17-regular.otf"), g("texgyrepagella-italic.otf")
LAB_P = "/usr/share/fonts/opentype/inter/InterDisplay-Regular.otf"
LABM_P = "/usr/share/fonts/opentype/inter/InterDisplay-Medium.otf"
RU_P = "/usr/share/fonts/truetype/google-fonts/Lora-Italic-Variable.ttf"
DID, ITA, LAB, RU = (lambda s: F(DID_P, s)), (lambda s: F(ITA_P, s)), (lambda s: F(LAB_P, s)), (lambda s: F(RU_P, s))
LABM = (lambda s: F(LABM_P, s)) if os.path.exists(LABM_P) else LAB

PAPER = (243, 237, 226)
INKC = (40, 32, 26)
COCOA = (74, 52, 40)
CARAMEL = (160, 112, 70)
GREY = (122, 112, 102)
CREAM = (246, 240, 230)
GOLD = (214, 176, 98)
BACK = (46, 34, 27)
PHONE = "+998 33 751 11 88"
LOGO = Image.open("/home/claude/imperial/src/img/logo_light.png").convert("RGBA")

# inset photo on the paper pages
IX0, IY0, IW, IH = 90, 360, 900, 1010
PAGES = [  # src, start, uz name, ru name, family
    ("tg1", 33.6, "Tungi saroy", "Ночной дворец", "KLASSIK NAQSH"),
    ("tg1", 50.45, "Samarqand ko‘ki", "Самаркандская лазурь", "KLASSIK NAQSH"),
    ("tg1", 55.6, "Sut va asal", "Молоко и мёд", "KLASSIK NAQSH"),
    ("tg2", 0.2, "Grafit", "Графит", "GEOMETRIK NAQSH"),
    ("tg2", 4.0, "Oltin ip", "Золотая нить", "GEOMETRIK NAQSH"),
    ("tg2", 18.8, "Shahar oqshomi", "Вечерний город", "GEOMETRIK NAQSH"),
]
PAGE_D, COVER_D, END_D, XF, XF_END = 2.9, 3.4, 6.5, 0.4, 0.5
SC = [("cover", COVER_D)] + [(f"p{i + 1}", PAGE_D) for i in range(6)] + [("end", END_D)]
ST = [0.0]
for i in range(1, len(SC)):
    ST.append(ST[-1] + SC[i - 1][1] - (XF_END if i == len(SC) - 1 else XF))
TOTAL = ST[-1] + END_D
NF = int(round(TOTAL * FPS))
S_END = ST[-1]
ENC = "-c:v libx264 -preset fast -crf 15 -pix_fmt yuv420p"
GRADE = "eq=contrast=1.05:saturation=1.06,unsharp=5:5:0.35"


def sh(cmd):
    subprocess.run(cmd, shell=True, check=True)


def paper_png():
    rng = np.random.default_rng(3)
    a = np.ones((H, W, 3), np.float32) * np.array(PAPER, np.float32)
    a += rng.normal(0, 3.2, (H, W, 1))
    yy, xx = np.mgrid[0:H, 0:W]
    v = 1 - 0.07 * (((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
    a *= v[..., None]
    im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA")
    sh_ = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(sh_).rectangle((IX0 + 10, IY0 + 18, IX0 + IW + 10, IY0 + IH + 18), fill=(60, 40, 25, 95))
    im.alpha_composite(sh_.filter(ImageFilter.GaussianBlur(16)))
    im.convert("RGB").save(f"{D}/bo/paper.png")
    rng = np.random.default_rng(4)
    b = np.ones((H, W, 3), np.float32) * np.array(BACK, np.float32) + rng.normal(0, 2.5, (H, W, 1))
    b *= (1 - 0.18 * (((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2))[..., None]
    Image.fromarray(np.clip(b, 0, 255).astype(np.uint8)).save(f"{D}/bo/back.png")


def base():
    os.makedirs(f"{D}/bo", exist_ok=True)
    paper_png()
    sh(f"ffmpeg -nostdin -v error -y -ss 39.6 -t {COVER_D + 0.1} -i {D}/src/tg1.mp4 -an -vf \"scale=1080:1920:flags=lanczos,"
       f"fps=30,{GRADE},trim=duration={COVER_D},format=yuv420p\" {ENC} {D}/bo/m_cover.mp4")
    for i, (v, ss, *_r) in enumerate(PAGES):
        sh(f"ffmpeg -nostdin -v error -y -loop 1 -framerate 30 -i {D}/bo/paper.png -ss {ss} -t {PAGE_D + 0.1} "
           f"-i {D}/src/{v}.mp4 -filter_complex \"[1:v]scale=1080:1920:flags=lanczos,fps=30,{GRADE},"
           f"crop=1080:1212:0:354,scale={IW}:{IH}:flags=lanczos[ph];[0:v][ph]overlay={IX0}:{IY0}:shortest=1,"
           f"trim=duration={PAGE_D},format=yuv420p[v]\" -map \"[v]\" -an {ENC} {D}/bo/m_p{i + 1}.mp4")
    sh(f"ffmpeg -nostdin -v error -y -loop 1 -framerate 30 -i {D}/bo/back.png -t {END_D} -vf format=yuv420p {ENC} "
       f"{D}/bo/m_end.mp4")
    ins = " ".join(f"-i {D}/bo/m_{s[0]}.mp4" for s in SC)
    f = [f"[{i}:v]fps=30,setpts=PTS-STARTPTS,settb=AVTB[v{i}]" for i in range(len(SC))]
    prev = "[v0]"
    for i in range(1, len(SC)):
        last = i == len(SC) - 1
        f.append(f"{prev}[v{i}]xfade=transition={'fade' if last else 'coverleft'}:duration={XF_END if last else XF}:"
                 f"offset={ST[i]:.3f},settb=AVTB[x{i}]")
        prev = f"[x{i}]"
    sh(f"ffmpeg -nostdin -v error -y {ins} -filter_complex \"{';'.join(f)}\" -map \"{prev}\" -r 30 {ENC} {D}/base_mag.mp4")


_cache = {}


def page_still(i):
    """mid-page inset (RGB) for chips and back-cover thumbs"""
    if i not in _cache:
        v, ss, *_r = PAGES[i]
        p = subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-ss", f"{ss + 1.2}", "-i", f"{D}/src/{v}.mp4",
                            "-frames:v", "1", "-vf", f"scale=1080:1920,{GRADE},crop=1080:1212:0:354,scale={IW}:{IH}",
                            "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, check=True)
        _cache[i] = np.frombuffer(p.stdout, np.uint8).reshape(IH, IW, 3)
    return _cache[i]


_chips = {}


def chips(i):
    if i not in _chips:
        a = page_still(i)[::6, ::6].reshape(-1, 3).astype(np.float32)
        crit = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.5)
        _, lab, cen = cv2.kmeans(a, 3, None, crit, 4, cv2.KMEANS_PP_CENTERS)
        order = np.argsort(cen.sum(1))                      # dark -> light
        _chips[i] = [tuple(int(x) for x in cen[k]) for k in order]
    return _chips[i]


def text(img, xy, s, font, fill, alpha, rise=0, anchor="la", tracking=0):
    if alpha <= 0.01 or not s:
        return
    x, y = xy
    y += rise * (1 - alpha)
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    a = int(255 * alpha)
    if tracking:
        wdt = sum(font.getlength(c) for c in s) + tracking * (len(s) - 1)
        if anchor[0] == "m":
            x -= wdt / 2
        elif anchor[0] == "r":
            x -= wdt
        for c in s:
            d.text((x, y), c, font=font, fill=tuple(fill) + (a,), anchor="l" + anchor[1])
            x += font.getlength(c) + tracking
    else:
        d.text((x, y), s, font=font, fill=tuple(fill) + (a,), anchor=anchor)
    img.alpha_composite(lay)


def hair(img, x0, y, x1, col, al, w=2):
    if al <= 0.01:
        return
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(lay).line([(x0, y), (x1, y)], fill=tuple(col) + (int(255 * al),), width=w)
    img.alpha_composite(lay)


def page(img, t, i):
    t0 = ST[i + 1]
    al = 1.0
    uz, ru, fam = PAGES[i][2], PAGES[i][3], PAGES[i][4]
    # masthead (static, on the paper)
    text(img, (IX0, 268), "IMPERIAL", DID(46), INKC, al, 0, anchor="ls", tracking=12)
    text(img, (IX0 + IW, 268), "KOMBO · KOLLEKSIYA", LAB(22), GREY, al, 0, anchor="rs", tracking=5)
    hair(img, IX0, 300, IX0 + IW, INKC, 0.55, 2)
    text(img, (IX0 + IW, 336), f"{i + 1:02d} / 06", LAB(20), GREY, al, 0, anchor="rs", tracking=4)
    # frame line around the photo
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(lay).rectangle((IX0 - 1, IY0 - 1, IX0 + IW, IY0 + IH), outline=INKC + (150,), width=2)
    img.alpha_composite(lay)
    # caption: number, name, RU, family + chips (words rise once, then stay)
    a1 = a_in(t, t0 + 0.25, 0.4)
    text(img, (IX0 - 6, 1395), f"{i + 1:02d}", DID(150), COCOA, a1, 24, anchor="la")
    text(img, (300, 1412), uz, ITA(74), INKC, a_in(t, t0 + 0.35, 0.4), 24)
    text(img, (304, 1508), ru, RU(32), CARAMEL, a_in(t, t0 + 0.5, 0.4), 16)
    a2 = a_in(t, t0 + 0.65, 0.4)
    text(img, (304, 1590), fam, LAB(22), GREY, a2, 0, anchor="ls", tracking=4)
    fw = sum(LAB(22).getlength(c) for c in fam) + 4 * (len(fam) - 1)
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    for k, c in enumerate(chips(i)):
        cx = 304 + fw + 34 + k * 38
        d.ellipse((cx - 14, 1568, cx + 14, 1596), fill=c + (int(255 * a2),), outline=INKC + (int(120 * a2),), width=1)
    img.alpha_composite(lay)


_thumbs = None


def thumbs():
    global _thumbs
    if _thumbs is None:
        _thumbs = [Image.fromarray(page_still(i)).resize((270, 303), Image.LANCZOS).convert("RGBA") for i in range(6)]
    return _thumbs


def sweep(img, box, t, t0, dur=0.9):
    """one soft light pass over the logo (Imperial signature)"""
    u = (t - t0) / dur
    if not 0 < u < 1:
        return
    x0, y0, x1, y1 = box
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    cx = x0 - 120 + (x1 - x0 + 240) * u
    for k in range(40):
        a = int(70 * (1 - abs(k - 20) / 20))
        d.line([(cx + k - 20 + 60, y0), (cx + k - 20, y1)], fill=(255, 245, 225, a), width=1)
    img.alpha_composite(lay)


def layer(j, t):
    """overlay of scene j (0 cover, 1..6 pages, 7 back cover) at time t, unshifted"""
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if j == 0:
        cover_layer(img, t)
    elif j <= 6:
        page(img, t, j - 1)
    else:
        end_layer(img, t)
    return np.asarray(img).copy()


def frame(i):
    t = i / FPS
    c = max(j for j in range(len(ST)) if ST[j] <= t + 1e-6)
    if 1 <= c <= 6 and t < ST[c] + XF:                 # page turn: new page slides in from the right over the old
        e = (t - ST[c]) / XF
        dx = int(round(W * (1 - e)))
        prev, new = layer(c - 1, t), layer(c, t)
        prev[:, dx:] = 0
        out = np.zeros_like(new)
        if dx < W:
            out[:, dx:] = new[:, :W - dx]
        prev[:, dx:] = out[:, dx:]
        return prev
    if c == 7 and t < S_END + XF_END:                  # fade to the back cover
        e = (t - S_END) / XF_END
        a = layer(6, t).astype(np.float32)
        a[..., 3] *= (1 - e)
        b = layer(7, t).astype(np.float32)
        al_b = b[..., 3:4] / 255.0
        al_a = a[..., 3:4] / 255.0
        out_a = al_b + al_a * (1 - al_b)
        rgb = (b[..., :3] * al_b + a[..., :3] * al_a * (1 - al_b)) / np.maximum(out_a, 1e-6)
        return np.concatenate([rgb, out_a * 255], -1).clip(0, 255).astype(np.uint8)
    return layer(c, t)


def cover_layer(img, t):
    if True:
        al = 1.0
        topgrad(img, 980, 0.62)
        grad(img, 1250, 1920, 0.72)
        text(img, (W // 2, 250), "IMPERIAL JALYUZI · KOLLEKSIYA", LAB(24), CREAM, al, 0, anchor="ma", tracking=7)
        text(img, (W // 2, 200), "KOMBO", DID(220), CREAM, a_in(t, -0.3, 0.3), 0, anchor="ma", tracking=8)
        ac = a_in(t, 0.2, 0.4)
        if ac > 0.01:
            cl = Image.new("RGBA", img.size, (0, 0, 0, 0))
            ImageDraw.Draw(cl).ellipse((170, 470, 910, 760), fill=(40, 28, 20, int(150 * ac)))
            img.alpha_composite(cl.filter(ImageFilter.GaussianBlur(50)))
        text(img, (W // 2, 500), "6 ta obraz —", ITA(70), CREAM, a_in(t, 0.25, 0.4), 22, anchor="ma")
        text(img, (W // 2, 582), "qaysi biri sizniki?", ITA(70), GOLD, a_in(t, 0.45, 0.4), 22, anchor="ma")
        text(img, (W // 2, 686), "6 образов — какой ваш?", RU(34), CREAM, a_in(t, 0.7, 0.4), 12, anchor="ma")
        for k, s in enumerate(["KLASSIK NAQSH", "GEOMETRIK NAQSH", "TOSHKENTDA O‘LCHOV — BEPUL"]):
            ak = a_in(t, 0.9 + 0.15 * k, 0.35)
            hair(img, 90, 1418 + 64 * k, 130, GOLD, ak, 3)
            text(img, (148, 1430 + 64 * k), s, LABM(28), CREAM, ak, 10, anchor="ls", tracking=4)


def end_layer(img, t):
    if True:
        a0 = a_in(t, S_END + 0.05, 0.4)
        lg = LOGO.copy()
        lg.thumbnail((380, 150))
        lg.putalpha(lg.split()[3].point(lambda x: int(x * a0)))
        lx = (W - lg.width) // 2
        img.alpha_composite(lg, (lx, 200))
        sweep(img, (lx, 200, lx + lg.width, 200 + lg.height), t, S_END + 4.2)
        text(img, (W // 2, 392), "Qaysi sahifa", DID(76), CREAM, a_in(t, S_END + 0.2, 0.4), 22, anchor="ma")
        text(img, (W // 2, 478), "sizga yoqdi?", ITA(76), GOLD, a_in(t, S_END + 0.35, 0.4), 22, anchor="ma")
        text(img, (W // 2, 586), "Какая страница вам понравилась?", RU(30), (214, 196, 172), a_in(t, S_END + 0.5), 10,
             anchor="ma")
        th = thumbs()
        for k in range(6):
            r_, c_ = divmod(k, 3)
            x, y = 111 + c_ * 294, 650 + r_ * 327
            ak = a_in(t, S_END + 0.4 + 0.08 * k, 0.35)
            if ak <= 0.01:
                continue
            im = th[k].copy()
            im.putalpha(int(255 * ak))
            img.alpha_composite(im, (x, y))
            lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
            dd = ImageDraw.Draw(lay)
            dd.rectangle((x - 1, y - 1, x + 270, y + 303), outline=CREAM + (int(170 * ak),), width=2)
            dd.rectangle((x, y, x + 70, y + 46), fill=PAPER + (int(240 * ak),))
            img.alpha_composite(lay)
            text(img, (x + 35, y + 23), f"{k + 1:02d}", DID(34), COCOA, ak, 0, anchor="mm")
        text(img, (W // 2, 1335), "Izohga sahifa raqamini yozing", LABM(34), CREAM, a_in(t, S_END + 1.0), 10, anchor="ma")
        text(img, (W // 2, 1392), "Narxi uchun — izohga «NARX» deb yozing", ITA(44), GOLD, a_in(t, S_END + 1.3), 10,
             anchor="ma")
        text(img, (W // 2, 1466), "Toshkentda o‘lchov va o‘rnatish — bepul", LAB(28), (214, 196, 172),
             a_in(t, S_END + 1.6), 8, anchor="ma")
        text(img, (W // 2, 1522), PHONE, LABM(46), CREAM, a_in(t, S_END + 1.8), 8, anchor="ma", tracking=2)
        text(img, (W // 2, 1590), "t.me/jalyuzi_imperial · @imperial_jalyuzi_uz", LAB(26), (190, 172, 150),
             a_in(t, S_END + 1.9), 8, anchor="ma")


def render_ov():
    os.makedirs(f"{D}/ov_mag", exist_ok=True)
    for i in range(6):
        chips(i)
    thumbs()
    idx = list(range(NF))
    with Pool(6) as p:
        for k in range(0, len(idx), 24):
            ch = idx[k:k + 24]
            for i, a in zip(ch, p.map(frame, ch)):
                Image.fromarray(a).save(f"{D}/ov_mag/{i:04d}.png", compress_level=1)


def music():
    from clavecin_bed import clavecin_bed
    clavecin_bed(f"{D}/bed_mag.wav", TOTAL, S_END, ST[4], ST[1:7])


OUTN = "imperial_kombo_jurnal"


def final():
    os.makedirs(f"{D}/out", exist_ok=True)
    sh(f"ffmpeg -nostdin -v error -y -i {D}/base_mag.mp4 -framerate 30 -i {D}/ov_mag/%04d.png -i {D}/bed_mag.wav "
       f"-filter_complex \"[0:v][1:v]overlay=0:0:format=auto,format=yuv420p[v];"
       f"[2:a]loudnorm=I=-15:TP=-1.5:LRA=9[a]\" -map \"[v]\" -map \"[a]\" -t {TOTAL:.3f} "
       f"-c:v libx264 -preset slow -crf 18 -pix_fmt yuv420p -color_primaries bt709 -color_trc bt709 -colorspace bt709 "
       f"-c:a aac -b:a 192k -movflags +faststart {D}/out/{OUTN}.mp4")


def cover():
    tt = 1.6
    sh(f"ffmpeg -v error -y -ss {tt} -i {D}/base_mag.mp4 -frames:v 1 {D}/cs/cb.png")
    b = Image.open(f"{D}/cs/cb.png").convert("RGBA")
    b.alpha_composite(Image.fromarray(frame(int(tt * FPS))))
    b.convert("RGB").save(f"{D}/out/{OUTN}_muqova.jpg", quality=92)


if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else "all"
    print("starts", [round(x, 2) for x in ST], "total", round(TOTAL, 2))
    if what in ("base", "all"):
        base()
    if what == "prev":
        ims = []
        for tt in map(float, sys.argv[2].split(",")):
            sh(f"ffmpeg -v error -y -ss {tt} -i {D}/base_mag.mp4 -frames:v 1 {D}/cs/pb.png")
            b = Image.open(f"{D}/cs/pb.png").convert("RGBA")
            b.alpha_composite(Image.fromarray(frame(int(tt * FPS))))
            ims.append(b.convert("RGB").resize((360, 640)))
        c = Image.new("RGB", (365 * len(ims), 640), "white")
        for k, im in enumerate(ims):
            c.paste(im, (k * 365, 0))
        c.save(f"{D}/cs/prev_mag.jpg", quality=85)
    if what in ("ov", "all"):
        render_ov()
    if what in ("music", "all"):
        music()
    if what in ("final", "all"):
        final()
    if what in ("cover", "all"):
        cover()
