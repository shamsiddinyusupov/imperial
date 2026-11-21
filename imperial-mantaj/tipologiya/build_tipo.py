"""«Tipologiya» (IMPERIAL, owner 22.11): a Swiss museum-catalogue Reel built only from the owner's own plisse installs.
One window -> 2x2 -> 3x3 -> 4x4 -> 5x5 -> 6x6 (36 real windows, each a living 4:5 tile, numbered like catalogue
plates) -> the 36 glide into order by fabric tone, light to dark -> one plate (Nº 13) opens to full screen as the
real clip (sashes with their own plisse) -> paper end card with a 36-chip colour strip. Music: spiccato_bed (#23).
python3 build_tipo.py [prev t,t,..|frames|music|final|cover|all]
"""
import json
import os
import subprocess
import sys
from multiprocessing import Pool

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, "/home/claude/reels/tipo")
sys.path.insert(0, "/home/claude/reels/common")
sys.path.insert(0, "/home/claude/reels/ref1116")
sys.path.insert(0, "/home/claude/reels/qora_plisse")
import build_bd as B  # noqa: E402  (Imperial fonts, logo, phone)
from prep import TILES  # noqa: E402

D = "/home/claude/reels/tipo"
W, H, FPS = 1080, 1920, 30
PAPER, INK, GREY, GOLDD, CREAM = (241, 238, 232), (30, 27, 24), (118, 110, 102), (150, 112, 48), (246, 240, 230)
GX0, GW, GY0, GAP = 90, 900, 400, 8
CALM = json.load(open(f"{D}/tiles/calm.json"))
META = json.load(open(f"{D}/tiles/meta.json"))
IDS = [t[0] for t in TILES]
HERO_K = IDS.index(713)
# ---- timeline ----
STEPS = [(2.4, 3.2, 2), (3.9, 4.6, 3), (5.2, 5.9, 4), (6.4, 7.0, 5), (7.5, 8.2, 6)]
SORT0, SORT_D, SORT_STAG = 8.7, 1.15, 0.035
T_SEL, T_Z0, T_Z1, T_FULL = 12.4, 13.2, 14.3, 14.6
HERO_T0 = 9.0                     # hero tile starts playing (clip time 0)
S_END = 19.8
TOTAL = S_END + 6.0
NF = int(round(TOTAL * FPS))
ENC = "-c:v libx264 -preset fast -crf 15 -pix_fmt yuv420p"


def ease(u):
    u = np.clip(u, 0, 1)
    return u * u * (3 - 2 * u)


def ease_io(u):
    u = float(np.clip(u, 0, 1))
    return 4 * u ** 3 if u < 0.5 else 1 - (-2 * u + 2) ** 3 / 2


def a_in(t, t0, d=0.45):
    return float(ease((t - t0) / d))


def a_out(t, t1, d=0.35):
    return float(1 - ease((t - t1) / d))


# ---- slots: tile k lives in the top-left block, new shells grow along the right column and bottom row ----
def shell_slots(n):
    out = []
    for m in range(1, n + 1):
        out += [(r, m - 1) for r in range(m)] + [(m - 1, c) for c in range(m - 1)]
    return out


SLOT = shell_slots(6)                                  # SLOT[k] = (r, c)
ORDER = sorted(range(36), key=lambda k: -CALM[str(IDS[k])]["L"])
TARGET = {k: divmod(j, 6) for j, k in enumerate(ORDER)}   # sorted position (r, c), light -> dark
SHELL = [max(r, c) + 1 for r, c in SLOT]               # grid size at which tile k appears


def grid_n(t):
    n = 1.0
    for t0, t1, m in STEPS:
        if t >= t1:
            n = m
        elif t > t0:
            n = (m - 1) + ease_io((t - t0) / (t1 - t0))
            break
    return n


def cell(n, r, c):
    w = (GW - (n - 1) * GAP) / n
    h = w * 1.25
    return GX0 + c * (w + GAP), GY0 + r * (h + GAP), w, h


def appear_time(k):
    m = SHELL[k]
    if m == 1:
        return -1.0
    t0, t1, _ = STEPS[m - 2]
    idx = [j for j in range(36) if SHELL[j] == m].index(k)
    return t1 - 0.25 + 0.045 * idx


# ---- tile frames ----
def tile_frame(k, t):
    i = IDS[k]
    if k == HERO_K:
        f = int(np.clip((t - HERO_T0) * FPS, 0, 299)) + 1
        return f"{D}/tiles/h713/{f:04d}.jpg"
    c = CALM[str(i)]
    s, e = c["s"], c["e"]
    if e - s <= 1:
        return f"{D}/tiles/{i}/0000.jpg"
    L = e - s
    ph = int(t * FPS + 17 * k) % (2 * L)
    f = s + (ph if ph < L else 2 * L - 1 - ph)
    return f"{D}/tiles/{i}/{f:04d}.jpg"


_PAPER = None


def paper():
    global _PAPER
    if _PAPER is None:
        rng = np.random.default_rng(3)
        p = np.ones((H, W, 3), np.float32) * np.array(PAPER, np.float32)
        g = cv2.GaussianBlur(rng.normal(0, 1, (H, W)).astype(np.float32), (0, 0), 0.7) * 2.2
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        v = 1 - 0.05 * (((xx - W / 2) / W) ** 2 + ((yy - H / 2) / H) ** 2) * 4
        _PAPER = np.clip((p + g[..., None]) * v[..., None], 0, 255).astype(np.uint8)
    return _PAPER.copy()


F = {}


def font(path, size):
    k = (path, size)
    if k not in F:
        F[k] = ImageFont.truetype(path, size)
    return F[k]


def DID(s): return font(B.DID_P, s)
def ITA(s): return font(B.ITA_P, s)
def LAB(s): return font(B.LAB_P, s)
def LABM(s): return font(B.LABM_P, s)
def RU(s): return font(B.RU_P, s)


def txt(d, xy, s, f, col, al, anchor="la", tracking=0):
    if al <= 0.01:
        return
    a = int(255 * al)
    if tracking:
        x, y = xy
        wtot = sum(f.getlength(ch) for ch in s) + tracking * (len(s) - 1)
        if anchor[0] == "r":
            x -= wtot
        elif anchor[0] == "m":
            x -= wtot / 2
        for ch in s:
            d.text((x, y), ch, font=f, fill=col + (a,), anchor="l" + anchor[1])
            x += f.getlength(ch) + tracking
    else:
        d.text(xy, s, font=f, fill=col + (a,), anchor=anchor)


def put(img, tile, x, y, w, h, al=1.0):
    """paste tile (BGR->RGB np) resized to w x h at float x,y onto img (RGB np)"""
    wi, hi = int(round(w)), int(round(h))
    if wi < 2 or hi < 2 or al <= 0.01:
        return
    t = cv2.resize(tile, (wi, hi), interpolation=cv2.INTER_AREA if wi < tile.shape[1] else cv2.INTER_CUBIC)
    x0, y0 = int(round(x)), int(round(y))
    xa, ya, xb, yb = max(0, x0), max(0, y0), min(W, x0 + wi), min(H, y0 + hi)
    if xb <= xa or yb <= ya:
        return
    src = t[ya - y0:yb - y0, xa - x0:xb - x0]
    if al >= 0.999:
        img[ya:yb, xa:xb] = src
    else:
        img[ya:yb, xa:xb] = (img[ya:yb, xa:xb] * (1 - al) + src * al).astype(np.uint8)


def tile_rect(k, t):
    """current rect (x, y, w, h), alpha, scale-in for tile k"""
    if t < SORT0:
        n = grid_n(t)
        r, c = SLOT[k]
        x, y, w, h = cell(n, r, c)
        ta = appear_time(k)
        al = 1.0 if ta < 0 else a_in(t, ta, 0.4)
        sc = 0.86 + 0.14 * al
        return (x + w * (1 - sc) / 2, y + h * (1 - sc) / 2, w * sc, h * sc), al
    j = ORDER.index(k)
    u = ease_io((t - SORT0 - SORT_STAG * j) / SORT_D)
    r0, c0 = SLOT[k]
    r1, c1 = TARGET[k]
    xa, ya, w, h = cell(6, r0, c0)
    xb, yb, _, _ = cell(6, r1, c1)
    dip = 1 - 0.12 * np.sin(np.pi * u)
    x, y = xa + (xb - xa) * u, ya + (yb - ya) * u
    return (x + w * (1 - dip) / 2, y + h * (1 - dip) / 2, w * dip, h * dip), 1.0


CHIPS = [tuple(CALM[str(IDS[k])]["col"]) for k in ORDER]


def frame(i):
    t = i / FPS
    img = paper()
    full = t >= T_FULL - 0.3 and t < S_END + 0.6
    # ---- grid / sort / zoom ----
    if t < T_FULL + 0.1:
        n_now = grid_n(t) if t < SORT0 else 6
        zoom = ease_io((t - T_Z0) / (T_Z1 - T_Z0)) if t > T_Z0 else 0.0
        dim = a_in(t, T_SEL + 0.2, 0.6)
        order = list(range(36))
        if t >= SORT0:
            order.sort(key=lambda k: abs(ORDER.index(k) * SORT_STAG + SORT0 - t))
            order = order[::-1]
        order = [k for k in order if k != HERO_K] + [HERO_K]
        for k in order:
            if t < SORT0 and SHELL[k] > np.ceil(n_now - 1e-6):
                continue
            (x, y, w, h), al = tile_rect(k, t)
            if al <= 0.01:
                continue
            if k == HERO_K and zoom > 0:
                x, y, w, h = x + (0 - x) * zoom, y + (272 - y) * zoom, w + (W - w) * zoom, h + (1350 - h) * zoom
            tl = cv2.cvtColor(cv2.imread(tile_frame(k, t)), cv2.COLOR_BGR2RGB)
            a2 = al
            if k != HERO_K:
                a2 *= 1 - 0.55 * dim * (1 - zoom) - zoom
            put(img, tl, x, y, w, h, a2)
    if full:
        f = int(np.clip((t - HERO_T0) * FPS, 0, 299)) + 1
        fr = cv2.cvtColor(cv2.imread(f"{D}/hero_full/{f:04d}.jpg"), cv2.COLOR_BGR2RGB)
        af = a_in(t, T_FULL - 0.3, 0.4) * a_out(t, S_END, 0.6)
        img = (img * (1 - af) + fr * af).astype(np.uint8)
    pil = Image.fromarray(img).convert("RGBA")
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    # ---- catalogue chrome (header, plate numbers, captions) ----
    ah = a_in(t, 0.0, 0.2) * a_out(t, T_Z0, 0.5) if t > 0.05 else 1.0
    if ah > 0.01:
        txt(d, (GX0, 182), "IMPERIAL — TIPOLOGIYA", LABM(24), INK, ah, "ls", 6)
        txt(d, (GX0 + GW, 182), "PLISSE · ПЛИССЕ", LABM(24), INK, ah, "rs", 6)
        d.line([(GX0, 200), (GX0 + GW, 200)], fill=INK + (int(200 * ah),), width=2)
        n_vis = 1 if t < STEPS[0][0] + 0.4 else min(36, round(grid_n(t)) ** 2) if t < SORT0 else 36
        txt(d, (GX0 - 6, 220), f"{n_vis:02d}", DID(132), INK, ah, "la")
        txt(d, (GX0 + 186, 252), "deraza", ITA(40), INK, ah, "la")
        txt(d, (GX0 + 186, 302), "haqiqiy ishlar · реальные работы", RU(26), GREY, ah, "la")
        txt(d, (GX0 + GW, 252), "Katalog Nº 1", LABM(26), GOLDD, ah, "ra")
        txt(d, (GX0 + GW, 290), "Каталог № 1", LAB(24), GREY, ah, "ra")
        d.line([(GX0, 372), (GX0 + GW, 372)], fill=INK + (int(90 * ah),), width=1)
    # plate numbers
    if t < T_Z0 + 0.2:
        ap = a_out(t, T_SEL + 0.3, 0.4)
        n_now = grid_n(t) if t < SORT0 else 6
        for k in range(36):
            if t < SORT0 and SHELL[k] > np.ceil(n_now - 1e-6):
                continue
            (x, y, w, h), al = tile_rect(k, t)
            if t < STEPS[0][0]:
                continue
            sz = int(np.clip(w * 0.11, 15, 26))
            a = al * ap * a_in(t, STEPS[0][0] + 0.3, 0.4)
            if k == HERO_K and t > T_SEL:
                a = al * a_out(t, T_Z0, 0.3)
            if a <= 0.01:
                continue
            s = f"{k + 1:02d}"
            tw = LABM(sz).getlength(s)
            d.rectangle((x + 5, y + h - sz - 13, x + 15 + tw, y + h - 5), fill=PAPER + (int(235 * a),))
            txt(d, (x + 10, y + h - 9), s, LABM(sz), INK, a, "ls")
    # hook plate caption
    if t < STEPS[0][0] + 0.3:
        a = a_out(t, STEPS[0][0] - 0.1, 0.3)
        d.rectangle((GX0 + 14, GY0 + 1125 - 64, GX0 + 150, GY0 + 1125 - 14), fill=PAPER + (int(235 * a),))
        txt(d, (GX0 + 26, GY0 + 1125 - 26), "Nº 01", LABM(30), INK, a, "ls")
    # selection outline on Nº 13
    if T_SEL < t < T_Z0 + 0.3:
        (x, y, w, h), _ = tile_rect(HERO_K, t)
        a = a_in(t, T_SEL, 0.4) * a_out(t, T_Z0, 0.25)
        d.rectangle((x - 5, y - 5, x + w + 5, y + h + 5), outline=GOLDD + (int(255 * a),), width=4)
    # captions under the grid (paper)
    caps = [(-1.0, STEPS[0][0] - 0.15, "Ikki bir xil deraza yo‘q.", "Двух одинаковых окон не бывает."),
            (STEPS[0][0] + 0.3, SORT0 - 0.2, "Barchasi — haqiqiy ishlar.", "Всё это — реальные работы."),
            (SORT0 + 0.2, 11.3, "Oqdan — qoragacha.", "От белого до графита."),
            (11.5, T_Z0 - 0.1, "36 deraza — 36 xil yechim.", "36 окон — 36 решений.")]
    for t0, t1, uz, ru in caps:
        a = a_in(t, t0, 0.4) * a_out(t, t1, 0.3)
        if a > 0.01:
            txt(d, (GX0, 1590), uz, ITA(50), INK, a, "ls")
            txt(d, (GX0, 1636), ru, RU(28), GREY, a_in(t, t0 + 0.2, 0.4) * a_out(t, t1, 0.3), "ls")
    # colour strip under the grid while sorting
    if SORT0 - 0.2 < t < T_Z0 + 0.2:
        a = a_in(t, SORT0 + 0.6, 0.6) * a_out(t, T_Z0 - 0.2, 0.3)
        cw = GW / 36
        for j, col in enumerate(CHIPS):
            aj = a * a_in(t, SORT0 + 0.6 + 0.02 * j, 0.3)
            d.rectangle((GX0 + j * cw, 1536, GX0 + (j + 1) * cw - 1, 1550), fill=col + (int(255 * aj),))
    # full-screen hero captions
    if T_FULL - 0.2 < t < S_END + 0.3:
        g = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        gd = np.zeros((H, W, 4), np.uint8)
        yy = np.arange(H)
        v = np.clip((yy - 1150) / 520, 0, 1) ** 1.4 * 0.78 * a_in(t, T_FULL, 0.5) * a_out(t, S_END - 0.1, 0.4)
        gd[..., 3] = (v[:, None] * 255).astype(np.uint8)
        pil.alpha_composite(Image.fromarray(gd))
        at = a_in(t, T_FULL + 0.2, 0.4) * a_out(t, S_END - 0.2, 0.3)
        tg = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        tdd = ImageDraw.Draw(tg)
        tdd.rectangle((GX0 - 10, 230, GX0 + 140, 282), fill=(20, 16, 12, int(150 * at)))
        txt(tdd, (GX0 + 2, 268), "Nº 13", LABM(30), CREAM, at, "ls")
        for t0, t1, uz, gold, ru in [(T_FULL + 0.4, 17.1, "Plisse —", "har bir tabaqaga alohida.",
                                      "Плиссе — на каждую створку отдельно."),
                                     (17.3, S_END - 0.2, "Har bir deraza —", "o‘z o‘lchamida.",
                                      "Каждое окно — по своей мерке.")]:
            a = a_in(t, t0, 0.45) * a_out(t, t1, 0.35)
            if a > 0.01:
                txt(tdd, (W // 2, 1430), uz, ITA(60), CREAM, a, "ma")
                txt(tdd, (W // 2, 1508), gold, ITA(70), B.GOLD, a_in(t, t0 + 0.25, 0.45) * a_out(t, t1, 0.35), "ma")
                txt(tdd, (W // 2, 1612), ru, RU(30), CREAM, a_in(t, t0 + 0.45, 0.45) * a_out(t, t1, 0.35), "ma")
        lay.alpha_composite(tg)
    # ---- end card ----
    if t > S_END - 0.1:
        a0 = a_in(t, S_END + 0.15, 0.45)
        lg = B.LOGO.copy() if False else Image.open("/home/claude/imperial/src/img/logo.png").convert("RGBA")
        lg.thumbnail((470, 160))
        lg.putalpha(lg.split()[3].point(lambda v: int(v * a0)))
        lx = (W - lg.width) // 2
        lay.alpha_composite(lg, (lx, 250))
        txt(d, (W // 2, 520), "Plisse jalyuzi", DID(88), INK, a_in(t, S_END + 0.35), "ma")
        txt(d, (W // 2, 628), "har bir derazaga — aniq o‘lchab.", ITA(54), GOLDD, a_in(t, S_END + 0.55), "ma")
        txt(d, (W // 2, 712), "Плиссе — точно по размеру каждого окна.", RU(29), GREY, a_in(t, S_END + 0.7), "ma")
        cw = GW / 36
        for j, col in enumerate(CHIPS):
            aj = a_in(t, S_END + 0.8 + 0.018 * j, 0.25)
            d.rectangle((GX0 + j * cw, 790, GX0 + (j + 1) * cw - 1, 806), fill=col + (int(255 * aj),))
        for k, s in enumerate(["Toshkentda o‘lchov va o‘rnatish — bepul", "O‘lchovdan keyin 3 kunda tayyor",
                               "1 yil kafolat"]):
            txt(d, (W // 2, 860 + 58 * k), s, LAB(32), INK, a_in(t, S_END + 1.0 + 0.15 * k), "ma")
        d.line([(GX0, 1062), (GX0 + GW, 1062)], fill=INK + (int(90 * a_in(t, S_END + 1.3)),), width=1)
        txt(d, (W // 2, 1100), "Narxi uchun — izohga «NARX» deb yozing", ITA(48), INK, a_in(t, S_END + 1.5), "ma")
        txt(d, (W // 2, 1176), "Цены — напишите NARX в комментариях", RU(28), GREY, a_in(t, S_END + 1.6), "ma")
        txt(d, (W // 2, 1300), B.PHONE, LABM(56), INK, a_in(t, S_END + 1.8), "ma", 2)
        txt(d, (W // 2, 1384), "t.me/jalyuzi_imperial · @imperial_jalyuzi_uz", LAB(28), GREY, a_in(t, S_END + 1.9),
            "ma")
    pil.alpha_composite(lay)
    return np.asarray(pil.convert("RGB"))


def render_frames():
    os.makedirs(f"{D}/fr", exist_ok=True)
    idx = [i for i in range(NF) if not os.path.exists(f"{D}/fr/{i:04d}.jpg")]
    with Pool(2) as p:
        for k in range(0, len(idx), 12):
            ch = idx[k:k + 12]
            for i, a in zip(ch, p.map(frame, ch)):
                cv2.imwrite(f"{D}/fr/{i:04d}.jpg", cv2.cvtColor(a, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 95])


def music():
    from spiccato_bed import spiccato_bed
    spiccato_bed(f"{D}/bed_tipo.wav", TOTAL, dict(steps=[s[0] for s in STEPS], sort=SORT0, sel=T_SEL, zoom=T_Z0,
                                                  full=T_FULL, end=S_END))


OUTN = "imperial_tipologiya_plisse"


def sh(cmd):
    subprocess.run(cmd, shell=True, check=True)


def final():
    os.makedirs(f"{D}/out", exist_ok=True)
    sh(f"ffmpeg -nostdin -v error -y -framerate 30 -i {D}/fr/%04d.jpg -i {D}/bed_tipo.wav "
       f"-filter_complex \"[1:a]loudnorm=I=-15:TP=-1.5:LRA=11[a]\" -map 0:v -map \"[a]\" -t {TOTAL:.3f} "
       f"-c:v libx264 -preset slow -crf 18 -pix_fmt yuv420p -color_primaries bt709 -color_trc bt709 -colorspace bt709 "
       f"-c:a aac -b:a 192k -movflags +faststart {D}/out/{OUTN}.mp4")


def cover():
    a = frame(int(12.2 * FPS))
    Image.fromarray(a).save(f"{D}/out/{OUTN}_muqova.jpg", quality=92)


if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else "all"
    print("total", TOTAL, "frames", NF, "hero sorted slot", TARGET[HERO_K])
    if what == "prev":
        ts = [float(v) for v in sys.argv[2].split(",")]
        with Pool(2) as p:
            ims = p.map(frame, [int(round(v * FPS)) for v in ts])
        c = np.full((640, 365 * len(ims), 3), 255, np.uint8)
        for k, a in enumerate(ims):
            c[:, k * 365:k * 365 + 360] = cv2.resize(a, (360, 640), interpolation=cv2.INTER_AREA)
        cv2.imwrite(f"{D}/prev_tipo.jpg", cv2.cvtColor(c, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 88])
    if what in ("frames", "all"):
        render_frames()
    if what in ("music", "all"):
        music()
    if what in ("final", "all"):
        final()
    if what in ("cover", "all"):
        cover()
