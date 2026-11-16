"""«Bitta deraza» (IMPERIAL) — inspired by the owner's reference (camera flies from a dusk facade into one lit window,
the curtain closes, the brand appears on the fabric). Our version for blinds, own footage only:
1 facade.py: dusk apartment block whose lit windows glow with OUR fabrics; push-in through one dark window
2 inside (qora_plisse nightpull): a hand closes the dark plisse over the night city; the city sound gets muffled
3 the closed plisse (owner's photo 05f5857d), slow push-in, the IMPERIAL logo appears ON the pleats + light pass
4 dark end card: plisse, free measuring in Tashkent, 3 days, NARX, contacts.
python3 build_bd.py [base|prev t,t|ov|music|final|cover|all]
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

D = "/home/claude/reels/ref1116"
Q = "/home/claude/reels/qora_plisse"
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
CREAM, GOLD, INKC, COCOA, SAND = (246, 240, 230), (214, 176, 98), (40, 32, 26), (96, 66, 46), (214, 196, 172)
BACK = (40, 30, 24)
PHONE = "+998 33 751 11 88"
LOGO = Image.open("/home/claude/imperial/src/img/logo_light.png").convert("RGBA")
PHOTO = f"{Q}/src/05f5857d-image.jpg"

FAC_D, IN_D, LOGO_D, END_D = 3.8, 6.2, 4.6, 5.5
IN_SS = 2.5
XF2, XF3 = 0.6, 0.5
S_IN = FAC_D
S_LOGO = S_IN + IN_D - XF2
S_END = S_LOGO + LOGO_D - XF3
TOTAL = S_END + END_D
NF = int(round(TOTAL * FPS))
CLOSE_AT = S_IN + 5.5                       # plisse fully down
ENC = "-c:v libx264 -preset fast -crf 15 -pix_fmt yuv420p"


def sh(cmd):
    subprocess.run(cmd, shell=True, check=True)


def logo_segment():
    """closed plisse photo, slow push-in, logo printed on the lower panel with a left->right reveal and a light pass"""
    ph = cv2.imread(PHOTO).astype(np.float32) / 255                # 1512x2016 BGR
    ph = cv2.cvtColor(np.clip((ph - 0.5) * 1.04 + 0.5, 0, 1), cv2.COLOR_BGR2BGR555 if False else cv2.COLOR_BGR2RGB)
    Hh, Ww = ph.shape[:2]
    lum = cv2.cvtColor(ph, cv2.COLOR_RGB2GRAY)
    hp = lum - cv2.GaussianBlur(lum, (0, 0), 6)                       # pleat ridges
    ridge = np.clip(0.5 + hp * 6, 0, 1)
    lw = 680
    lg = LOGO.resize((lw, int(LOGO.height * lw / LOGO.width)), Image.LANCZOS)
    la = np.asarray(lg).astype(np.float32) / 255
    lx, ly = 860 - lw // 2, 1228 - lg.height // 2
    col = la[..., :3] * np.array([1.0, 0.97, 0.92]) + 0.05
    A = np.zeros((Hh, Ww), np.float32)
    C = np.zeros((Hh, Ww, 3), np.float32)
    A[ly:ly + lg.height, lx:lx + lw] = la[..., 3]
    C[ly:ly + lg.height, lx:lx + lw] = col
    glow = cv2.GaussianBlur(A, (0, 0), 22)
    xs = np.arange(Ww, dtype=np.float32)[None, :]
    enc = subprocess.Popen(["ffmpeg", "-nostdin", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s",
                            f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "fast", "-crf", "14",
                            "-pix_fmt", "yuv420p", f"{D}/bo/logo.mp4"], stdin=subprocess.PIPE)
    rng = np.random.default_rng(5)
    n = int(LOGO_D * FPS)
    for i in range(n):
        t = i / FPS
        rv = np.clip((t - 0.9) / 1.3, 0, 1)                          # reveal progress
        edge = lx - 120 + (lw + 240) * rv
        wipe = np.clip((edge - xs) / 120, 0, 1)
        sw = np.exp(-((xs - (lx - 200 + (lw + 400) * np.clip((t - 2.4) / 1.1, 0, 1))) / 70) ** 2) if 2.4 < t < 3.6 else 0
        a = A * wipe * (0.5 + 0.5 * ridge) * 0.92
        img = ph * (1 - a[..., None]) + C * a[..., None]
        img += (glow * wipe)[..., None] * np.array([0.10, 0.08, 0.05]) * 1.4
        if not np.isscalar(sw):
            img += (A * sw)[..., None] * 0.35
        z = 1.0 + 0.07 * (t / LOGO_D)
        cw, chh = 1134 / z, 2016 / z
        cx, cy = 790, 1080
        M = np.array([[W / cw, 0, W / 2 - W / cw * cx], [0, H / chh, H / 2 - H / chh * cy]], np.float32)
        fr = cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_AREA, borderMode=cv2.BORDER_REPLICATE)
        fr = fr * 255 + rng.normal(0, 2.0, (H, W, 1))
        enc.stdin.write(np.clip(fr, 0, 255).astype(np.uint8).tobytes())
    enc.stdin.close()
    enc.wait()


def base():
    os.makedirs(f"{D}/bo", exist_ok=True)
    if not os.path.exists(f"{D}/bo/facade.mp4"):
        sh(f"python3 {D}/facade.py")
    sh(f"ffmpeg -nostdin -v error -y -ss {IN_SS} -t {IN_D} -i {Q}/st/nightpull.mp4 -an -vf \"fps=30,"
       f"eq=contrast=1.04:saturation=1.05,fade=t=in:st=0:d=0.4,format=yuv420p\" {ENC} {D}/bo/inside.mp4")
    logo_segment()
    bg = np.zeros((H, W, 3), np.float32) + np.array(BACK, np.float32)
    yy, xx = np.mgrid[0:H, 0:W]
    bg *= (1 - 0.25 * (((xx - W / 2) / (W / 2)) ** 2 + ((yy - H * 0.45) / (H / 2)) ** 2))[..., None]
    bg += np.random.default_rng(2).normal(0, 2.0, (H, W, 1))
    Image.fromarray(np.clip(bg, 0, 255).astype(np.uint8)).save(f"{D}/bo/back.png")
    sh(f"ffmpeg -nostdin -v error -y -loop 1 -framerate 30 -i {D}/bo/back.png -t {END_D} -vf format=yuv420p {ENC} "
       f"{D}/bo/end.mp4")
    f = ("[0:v]fps=30,setpts=PTS-STARTPTS,settb=AVTB[a];[1:v]fps=30,setpts=PTS-STARTPTS,settb=AVTB[b];"
         "[2:v]fps=30,setpts=PTS-STARTPTS,settb=AVTB[c];[3:v]fps=30,setpts=PTS-STARTPTS,settb=AVTB[d];"
         "[a][b]concat=n=2:v=1:a=0,settb=AVTB[ab];"
         f"[ab][c]xfade=transition=fade:duration={XF2}:offset={S_LOGO:.3f},settb=AVTB[abc];"
         f"[abc][d]xfade=transition=fade:duration={XF3}:offset={S_END:.3f},settb=AVTB[v]")
    sh(f"ffmpeg -nostdin -v error -y -i {D}/bo/facade.mp4 -i {D}/bo/inside.mp4 -i {D}/bo/logo.mp4 -i {D}/bo/end.mp4 "
       f"-filter_complex \"{f}\" -map \"[v]\" -r 30 {ENC} {D}/base_bd.mp4")


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
        for c in s:
            d.text((x, y), c, font=font, fill=tuple(fill) + (a,), anchor="l" + anchor[1])
            x += font.getlength(c) + tracking
    else:
        d.text((x, y), s, font=font, fill=tuple(fill) + (a,), anchor=anchor)
    img.alpha_composite(lay)


def cloud(img, box, al, col=(20, 14, 10), a=150, blur=45):
    if al <= 0.01:
        return
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(lay).ellipse(box, fill=col + (int(a * al),))
    img.alpha_composite(lay.filter(ImageFilter.GaussianBlur(blur)))


def sweep(img, box, t, t0, dur=0.9):
    u = (t - t0) / dur
    if not 0 < u < 1:
        return
    x0, y0, x1, y1 = box
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    cx = x0 - 120 + (x1 - x0 + 240) * u
    for k in range(40):
        d.line([(cx + k - 20 + 60, y0), (cx + k - 20, y1)], fill=(255, 245, 225, int(70 * (1 - abs(k - 20) / 20))), width=1)
    img.alpha_composite(lay)


def frame(i):
    t = i / FPS
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    # 1 facade
    if t < FAC_D:
        al = a_out(t, FAC_D - 0.7, 0.4)
        text(img, (90, 262), "TOSHKENT · 22:40", LAB(26), CREAM, a_in(t, 0.2, 0.4) * al, 0, tracking=6)
        a1 = a_in(t, 0.6, 0.5) * al
        cloud(img, (60, 1360, 1020, 1700), a1)
        text(img, (W // 2, 1410), "Har bir derazaning ortida —", ITA(62), CREAM, a1, 18, anchor="ma")
        text(img, (W // 2, 1490), "bir hayot.", ITA(70), GOLD, a_in(t, 0.9, 0.5) * al, 18, anchor="ma")
        text(img, (W // 2, 1590), "За каждым окном — своя жизнь.", RU(30), SAND, a_in(t, 1.2, 0.5) * al, 10, anchor="ma")
    # 2 inside: one line while the city is still visible
    if S_IN < t < S_LOGO:
        al = a_in(t, S_IN + 0.6, 0.5) * a_out(t, S_IN + 3.6, 0.5)
        cloud(img, (100, 1380, 980, 1680), al, a=120)
        text(img, (W // 2, 1440), "Shahar hali uyg‘oq…", ITA(66), CREAM, al, 16, anchor="ma")
        text(img, (W // 2, 1530), "Город ещё не спит…", RU(30), SAND, al, 10, anchor="ma")
    # 3 logo on the fabric: tagline on the wooden shelf
    if S_LOGO < t < S_END + 0.2:
        al = a_in(t, S_LOGO + 2.6, 0.6) * a_out(t, S_END - 0.1, 0.4)
        text(img, (W // 2, 1480), "Dunyo — tashqarida qolsin.", ITA(66), INKC, al, 16, anchor="ma")
        text(img, (W // 2, 1568), "Пусть мир останется снаружи.", RU(30), COCOA, al, 10, anchor="ma")
    # 4 end card
    if t > S_END - 0.2:
        a0 = a_in(t, S_END + 0.1, 0.4)
        lg = LOGO.copy()
        lg.thumbnail((420, 170))
        lg.putalpha(lg.split()[3].point(lambda x: int(x * a0)))
        lx = (W - lg.width) // 2
        img.alpha_composite(lg, (lx, 300))
        sweep(img, (lx, 300, lx + lg.width, 300 + lg.height), t, S_END + 3.6)
        text(img, (W // 2, 560), "Plisse jalyuzi", DID(84), CREAM, a_in(t, S_END + 0.3, 0.4), 18, anchor="ma")
        text(img, (W // 2, 668), "har bir derazaga — aniq o‘lchab.", ITA(56), GOLD, a_in(t, S_END + 0.5, 0.4), 14,
             anchor="ma")
        text(img, (W // 2, 770), "Плиссе — точно по размеру каждого окна.", RU(30), SAND, a_in(t, S_END + 0.7), 10,
             anchor="ma")
        for k, s in enumerate(["Toshkentda o‘lchov va o‘rnatish — bepul", "O‘lchovdan keyin 3 kunda tayyor",
                               "1 yil kafolat"]):
            ak = a_in(t, S_END + 0.9 + 0.15 * k, 0.4)
            text(img, (W // 2, 900 + 62 * k), s, LAB(32), CREAM, ak, 8, anchor="ma")
        text(img, (W // 2, 1150), "Narxi uchun — izohga «NARX» deb yozing", ITA(48), GOLD, a_in(t, S_END + 1.5), 10,
             anchor="ma")
        text(img, (W // 2, 1236), "Цены — напишите NARX в комментариях", RU(28), SAND, a_in(t, S_END + 1.6), 8,
             anchor="ma")
        text(img, (W // 2, 1400), PHONE, LABM(54), CREAM, a_in(t, S_END + 1.8), 8, anchor="ma", tracking=2)
        text(img, (W // 2, 1484), "t.me/jalyuzi_imperial · @imperial_jalyuzi_uz", LAB(28), (190, 172, 150),
             a_in(t, S_END + 1.9), 8, anchor="ma")
    return np.asarray(img)


def render_ov():
    os.makedirs(f"{D}/ov", exist_ok=True)
    idx = list(range(NF))
    with Pool(6) as p:
        for k in range(0, len(idx), 24):
            ch = idx[k:k + 24]
            for i, a in zip(ch, p.map(frame, ch)):
                Image.fromarray(a).save(f"{D}/ov/{i:04d}.png", compress_level=1)


def music():
    from nightcity_bed import nightcity_bed
    nightcity_bed(f"{D}/bed_bd.wav", TOTAL, FAC_D - 0.05, S_IN, CLOSE_AT, S_LOGO + 0.6, S_END)


OUTN = "imperial_bitta_deraza"


def final():
    os.makedirs(f"{D}/out", exist_ok=True)
    sh(f"ffmpeg -nostdin -v error -y -i {D}/base_bd.mp4 -framerate 30 -i {D}/ov/%04d.png -i {D}/bed_bd.wav "
       f"-filter_complex \"[0:v][1:v]overlay=0:0:format=auto,format=yuv420p[v];"
       f"[2:a]loudnorm=I=-15:TP=-1.5:LRA=11[a]\" -map \"[v]\" -map \"[a]\" -t {TOTAL:.3f} "
       f"-c:v libx264 -preset slow -crf 18 -pix_fmt yuv420p -color_primaries bt709 -color_trc bt709 -colorspace bt709 "
       f"-c:a aac -b:a 192k -movflags +faststart {D}/out/{OUTN}.mp4")


def cover():
    tt = 1.6
    sh(f"ffmpeg -v error -y -ss {tt} -i {D}/base_bd.mp4 -frames:v 1 {D}/cb.png")
    b = Image.open(f"{D}/cb.png").convert("RGBA")
    b.alpha_composite(Image.fromarray(frame(int(tt * FPS))))
    b.convert("RGB").save(f"{D}/out/{OUTN}_muqova.jpg", quality=92)


if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else "all"
    print("in", S_IN, "logo", round(S_LOGO, 2), "end", round(S_END, 2), "total", round(TOTAL, 2), "close", CLOSE_AT)
    if what in ("base", "all"):
        base()
    if what == "prev":
        ims = []
        for tt in map(float, sys.argv[2].split(",")):
            sh(f"ffmpeg -v error -y -ss {tt} -i {D}/base_bd.mp4 -frames:v 1 {D}/pb.png")
            b = Image.open(f"{D}/pb.png").convert("RGBA")
            b.alpha_composite(Image.fromarray(frame(int(tt * FPS))))
            ims.append(b.convert("RGB").resize((360, 640)))
        c = Image.new("RGB", (365 * len(ims), 640), "white")
        for k, im in enumerate(ims):
            c.paste(im, (k * 365, 0))
        c.save(f"{D}/prev_bd.jpg", quality=85)
    if what in ("ov", "all"):
        render_ov()
    if what in ("music", "all"):
        music()
    if what in ("final", "all"):
        final()
    if what in ("cover", "all"):
        cover()
