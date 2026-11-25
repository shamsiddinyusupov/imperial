"""«Antrasit» — IMPERIAL JALYUZI, owner 25.11 (silent: text + music). New style: an interior magazine.
Cover (owner's photo IMG_6122, masthead IMPERIAL, «Antrasit.»), four spreads with the owner's anthracite-frame plisse
installs in different layouts (big frame, diptych, full-bleed with paper panel, tall column with a vertical
headline), pages turn over the spine with shadow and a paper sound, back cover with Imperial conditions and NARX.
Music: flugel_bed (#30, new). python3 mag.py [prev t,t|frames|music|final|cover|all]
"""
import math
import os
import subprocess
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, "/home/claude/reels/common")
D = "/home/claude/reels/antrasit"
W, H, FPS = 1080, 1920, 30
PAPER = (244, 239, 230)
INK = (30, 28, 25)
GREY = (118, 110, 100)
GOLD = (214, 176, 98)
GOLDD = (160, 120, 52)
CREAM = (246, 240, 230)
PHONE = "+998 33 751 11 88"
S = [0.0, 3.9, 7.9, 11.9, 15.9, 19.9]     # page i fully shown at S[i]; the turn runs S[i]-FLIP .. S[i]
FLIP = 0.7
TOTAL = 25.9
NF = int(round(TOTAL * FPS))


def g(n):
    import glob
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
DID = lambda s: F(DID_P, s)  # noqa: E731
ITA = lambda s: F(ITA_P, s)  # noqa: E731
LAB = lambda s: F(LAB_P, s)  # noqa: E731
LABM = lambda s: F(LABM_P, s)  # noqa: E731
RU = lambda s: F(RU_P, s)  # noqa: E731
LOGO = Image.open("/home/claude/imperial/src/img/logo.png").convert("RGBA")


def ease(u):
    u = min(1.0, max(0.0, u))
    return u * u * (3 - 2 * u)


def a_in(t, t0, d=0.45):
    return ease((t - t0) / d)


def txt(d, xy, s, font, fill, al, anchor="la", tracking=0, rise=18, t_al=None):
    if al <= 0.01:
        return
    x, y = xy
    y += rise * (1 - al)
    a = int(255 * al)
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


class Reader:
    def __init__(self, path, w, h):
        self.w, self.h = w, h
        self.p = subprocess.Popen(["ffmpeg", "-nostdin", "-v", "error", "-i", path, "-f", "rawvideo", "-pix_fmt", "rgb24",
                                   "-"], stdout=subprocess.PIPE)
        self.i, self.last = -1, np.zeros((h, w, 3), np.uint8)

    def get(self, k):
        k = max(0, k)
        while self.i < k:
            buf = self.p.stdout.read(self.w * self.h * 3)
            if len(buf) < self.w * self.h * 3:
                break
            self.last = np.frombuffer(buf, np.uint8).reshape(self.h, self.w, 3)
            self.i += 1
        return self.last


_PAPER = None


def paper():
    global _PAPER
    if _PAPER is None:
        rng = np.random.default_rng(7)
        p = np.ones((H, W, 3), np.float32) * np.array(PAPER, np.float32)
        p += rng.normal(0, 2.2, (H, W, 1))
        y = np.linspace(-1, 1, H)[:, None]
        x = np.linspace(-1, 1, W)[None, :]
        p *= (1 - 0.06 * (x ** 2 + y ** 2))[..., None]
        _PAPER = np.clip(p, 0, 255).astype(np.uint8)
    return _PAPER.copy()


def chrome(d, n, al=1.0):
    """running header and folio"""
    txt(d, (90, 150), "IMPERIAL", LABM(24), INK, al, "lm", 7, 0)
    txt(d, (990, 150), "INTERYER · Nº 01 · ANTRASIT", LAB(20), GREY, al, "rm", 3, 0)
    d.line([(90, 182), (990, 182)], fill=INK + (int(70 * al),), width=1)
    d.line([(90, 1772), (990, 1772)], fill=INK + (int(70 * al),), width=1)
    txt(d, (90, 1806), f"0{n}", LABM(22), INK, al, "lm", 2, 0)
    txt(d, (990, 1806), "imperial_jalyuzi_uz", LAB(20), GREY, al, "rm", 1, 0)


def paste(img, arr, x, y):
    h, w = arr.shape[:2]
    img[y:y + h, x:x + w] = arr


# ------------------------------------------------------------------ pages
COVER = None


def page0(t):
    global COVER
    if COVER is None:
        im = Image.open(f"{D}/src/cover.jpg").convert("RGB")
        s = 1920 / im.height * 1.08
        im = im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS)
        COVER = np.asarray(im).astype(np.float32)
    z = 1.0 + 0.06 * ease(t / 4.6)
    ch, cw = int(1920 / z), int(1080 / z)
    hh, ww = COVER.shape[:2]
    y0, x0 = (hh - ch) // 2 + int(20 * t), (ww - cw) // 2
    crop = COVER[y0:y0 + ch, x0:x0 + cw]
    base = cv2.resize(crop, (W, H), interpolation=cv2.INTER_AREA)
    y = np.linspace(0, 1, H)[:, None, None]
    base = base * (1 - 0.62 * np.clip((0.30 - y) / 0.30, 0, 1)) * (1 - 0.72 * np.clip((y - 0.55) / 0.45, 0, 1) ** 1.2)
    img = Image.fromarray(np.clip(base, 0, 255).astype(np.uint8)).convert("RGBA")
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    txt(d, (W // 2, 120), "IMPERIAL", DID(150), CREAM, 1.0, "mt", 16, 0)
    txt(d, (W // 2, 300), "INTERYER JURNALI  ·  Nº 01  ·  2026", LAB(24), CREAM, a_in(t, 0.1), "mt", 4, 0)
    d.line([(150, 345), (930, 345)], fill=CREAM + (int(120 * a_in(t, 0.1)),), width=1)
    txt(d, (84, 1250), "Antrasit.", DID(190), CREAM, 1.0, "ls", 0, 0)
    txt(d, (90, 1360), "Rom va plisse —", ITA(58), GOLD, a_in(t, 0.25), "la")
    txt(d, (90, 1430), "bir ohangda.", ITA(58), GOLD, a_in(t, 0.4), "la")
    txt(d, (92, 1520), "Антрацит: рама и плиссе в одном тоне", RU(30), CREAM, a_in(t, 0.55), "la")
    txt(d, (92, 1600), "ESHIK  ·  DERAZA  ·  DETAL", LABM(24), CREAM, a_in(t, 0.7), "la", 5)
    img.alpha_composite(lay)
    return np.asarray(img.convert("RGB"))


R = {}


def video(name, t_local):
    if name not in R:
        w, h = {"p1": (900, 1080), "p2a": (440, 1000), "p2b": (440, 1000), "p3": (1080, 1500), "p4": (620, 1340)}[name]
        R[name] = Reader(f"{D}/box/{name}.mp4", w, h)
    return R[name].get(int(t_local * FPS))


def text_page(img, t, n, kicker, lines, ru, body=None, y0=1395, big=96, gold_last=False):
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    chrome(d, n)
    txt(d, (90, y0), kicker, LABM(26), GOLDD, a_in(t, 0.05), "la", 4)
    y = y0 + 44
    for k, s in enumerate(lines):
        col = GOLDD if (gold_last and k == len(lines) - 1) else INK
        txt(d, (86, y), s, DID(big), col, a_in(t, 0.2 + 0.12 * k), "la")
        y += int(big * 1.22)
    if body:
        txt(d, (90, y + 40), body, ITA(40), INK, a_in(t, 0.45), "la")
        y += 84
    txt(d, (90, y + 26), ru, RU(28), GREY, a_in(t, 0.6), "la")
    img.alpha_composite(lay)


def page1(t):
    a = paper()
    paste(a, video("p1", t), 90, 230)
    img = Image.fromarray(a).convert("RGBA")
    text_page(img, t, 1, "01 — ESHIK", ["Ikki tabaqa."], "Рама — антрацит. Плиссе — в тон.",
              "Rom — antrasit. Plisse — unga mos ohangda.", y0=1360)
    return np.asarray(img.convert("RGB"))


def page2(t):
    a = paper()
    paste(a, video("p2a", t), 90, 230)
    paste(a, video("p2b", t), 550, 230)
    img = Image.fromarray(a).convert("RGBA")
    d = ImageDraw.Draw(img)
    txt(d, (90, 1252), "a — tabaqa", LAB(22), GREY, a_in(t, 0.1), "la", 1, 0)
    txt(d, (550, 1252), "b — burmalar", LAB(22), GREY, a_in(t, 0.1), "la", 1, 0)
    text_page(img, t, 2, "02 — DETAL", ["Har bir tabaqaga —", "alohida."], "Плиссе — на каждую створку отдельно.",
              y0=1320, big=84, gold_last=True)
    return np.asarray(img.convert("RGB"))


def page3(t):
    a = paper()
    paste(a, video("p3", t), 0, 0)
    img = Image.fromarray(a).convert("RGBA")
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    txt(d, (90, 1540), "03 — DERAZA", LABM(26), GOLDD, a_in(t, 0.05), "la", 4)
    txt(d, (86, 1586), "Derazada ham —", DID(78), INK, a_in(t, 0.2), "la")
    txt(d, (86, 1670), "shu ohang.", DID(78), GOLDD, a_in(t, 0.32), "la")
    txt(d, (600, 1700), "И на окнах — тот же тон.", RU(28), GREY, a_in(t, 0.5), "la")
    d.line([(90, 1772), (990, 1772)], fill=INK + (70,), width=1)
    txt(d, (90, 1806), "03", LABM(22), INK, 1, "lm", 2, 0)
    txt(d, (990, 1806), "imperial_jalyuzi_uz", LAB(20), GREY, 1, "rm", 1, 0)
    img.alpha_composite(lay)
    # masthead strip over the photo
    d2 = ImageDraw.Draw(img)
    txt(d2, (90, 150), "IMPERIAL", LABM(24), CREAM, 1, "lm", 7, 0)
    return np.asarray(img.convert("RGB"))


def page4(t):
    a = paper()
    paste(a, video("p4", t), 370, 230)
    img = Image.fromarray(a).convert("RGBA")
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    chrome(d, 4)
    txt(d, (90, 240), "04 — YORUG‘LIK", LABM(24), GOLDD, a_in(t, 0.05), "la", 3)
    # vertical headline in the left column
    v = Image.new("RGBA", (1240, 300), (0, 0, 0, 0))
    dv = ImageDraw.Draw(v)
    al = a_in(t, 0.2)
    txt(dv, (0, 40), "Yorug‘lik —", DID(110), INK, al, "la", 0, 0)
    txt(dv, (620, 40), "yumshoq.", DID(110), GOLDD, a_in(t, 0.35), "la", 0, 0)
    v = v.rotate(90, expand=True)
    lay.alpha_composite(v, (110, 1580 - v.height))
    txt(d, (90, 1615), "Kun yorug‘i burmalardan yumshoq o‘tadi.", ITA(40), INK, a_in(t, 0.5), "la")
    txt(d, (90, 1680), "Свет мягко проходит через складки.", RU(28), GREY, a_in(t, 0.62), "la")
    img.alpha_composite(lay)
    return np.asarray(img.convert("RGB"))


def page5(t):
    a = paper()
    img = Image.fromarray(a).convert("RGBA")
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    lg = LOGO.copy()
    lg.thumbnail((470, 160))
    a0 = a_in(t, 0.1)
    lg.putalpha(lg.split()[3].point(lambda v: int(v * a0)))
    lay.alpha_composite(lg, ((W - lg.width) // 2, 250))
    txt(d, (W // 2, 520), "Plisse jalyuzi", DID(88), INK, a_in(t, 0.3), "ma")
    txt(d, (W // 2, 628), "antrasit romga — bir ohangda.", ITA(54), GOLDD, a_in(t, 0.5), "ma")
    txt(d, (W // 2, 712), "Плиссе — в тон антрацитовой раме.", RU(29), GREY, a_in(t, 0.65), "ma")
    for k, s in enumerate(["Toshkentda o‘lchov va o‘rnatish — bepul", "O‘lchovdan keyin 3 kunda tayyor",
                           "1 yil kafolat"]):
        txt(d, (W // 2, 860 + 58 * k), s, LAB(32), INK, a_in(t, 0.9 + 0.15 * k), "ma")
    d.line([(90, 1062), (990, 1062)], fill=INK + (int(90 * a_in(t, 1.3)),), width=1)
    txt(d, (W // 2, 1100), "Narxi uchun — izohga «NARX» deb yozing", ITA(48), INK, a_in(t, 1.5), "ma")
    txt(d, (W // 2, 1176), "Цены — напишите NARX в комментариях", RU(28), GREY, a_in(t, 1.6), "ma")
    txt(d, (W // 2, 1300), PHONE, LABM(56), INK, a_in(t, 1.8), "ma", 2)
    txt(d, (W // 2, 1384), "t.me/jalyuzi_imperial · @imperial_jalyuzi_uz", LAB(28), GREY, a_in(t, 1.9), "ma")
    img.alpha_composite(lay)
    return np.asarray(img.convert("RGB"))


PAGES = [page0, page1, page2, page3, page4, page5]


def turn(cur, nxt, u):
    """cur page turns over the left spine (right edge lifts towards the viewer and swings left); nxt lies below"""
    th = ease(u) * math.radians(100)
    out = nxt.astype(np.float32)
    # shadow of the lifting page on the page below, near the spine
    sw = 60 + 520 * math.sin(th)
    x = np.arange(W)[None, :, None]
    sh = 1 - 0.38 * math.sin(th) * np.exp(-x / sw)
    out = out * sh
    if th < math.radians(90):
        f = 2600.0
        xs = W * math.cos(th)
        z = W * math.sin(th)
        sc = f / (f - z)
        cy = H / 2
        src = np.float32([[0, 0], [W, 0], [W, H], [0, H]])
        dst = np.float32([[0, 0], [xs * sc, cy - cy * sc], [xs * sc, cy + (H - cy) * sc], [0, H]])
        M = cv2.getPerspectiveTransform(src, dst)
        shade = 1 - 0.35 * math.sin(th)
        pg = cv2.warpPerspective(cur.astype(np.float32) * shade, M, (W, H), flags=cv2.INTER_LINEAR)
        mk = cv2.warpPerspective(np.ones((H, W), np.float32), M, (W, H), flags=cv2.INTER_LINEAR)[..., None]
        # bright edge highlight on the turning page
        out = out * (1 - mk) + pg * mk
    return np.clip(out, 0, 255).astype(np.uint8)


def frame_at(t):
    i = max(k for k in range(len(S)) if S[k] - FLIP <= t) if t >= 0 else 0
    # page i is shown from S[i]-FLIP (under the turning page i-1)
    loc = lambda k: t - (S[k] - FLIP)  # noqa: E731
    if i >= 1 and t < S[i]:
        u = (t - (S[i] - FLIP)) / FLIP
        cur = PAGES[i - 1](loc(i - 1) if i - 1 > 0 else t)
        nxt = PAGES[i](loc(i))
        return turn(cur, nxt, u)
    return PAGES[i](loc(i) if i > 0 else t)


def frames():
    os.makedirs(f"{D}/out", exist_ok=True)
    p = subprocess.Popen(f"ffmpeg -nostdin -v error -y -f rawvideo -pix_fmt rgb24 -s {W}x{H} -r {FPS} -i - "
                         f"-c:v libx264 -preset fast -crf 14 -pix_fmt yuv420p {D}/video_a.mp4", shell=True,
                         stdin=subprocess.PIPE)
    for n in range(NF):
        p.stdin.write(frame_at(n / FPS).tobytes())
    p.stdin.close()
    p.wait()


def music():
    from flugel_bed import flugel_bed
    flugel_bed(f"{D}/bed.wav", TOTAL, dict(flips=[s - FLIP for s in S[1:]], end=S[5] + 0.2))


OUTN = "imperial_antrasit_jurnal"


def final():
    subprocess.run(f"ffmpeg -nostdin -v error -y -i {D}/video_a.mp4 -i {D}/bed.wav -filter_complex "
                   f"\"[1:a]aresample=48000,loudnorm=I=-15:TP=-1.5:LRA=11[a]\" -map 0:v -map \"[a]\" -t {TOTAL:.3f} "
                   f"-c:v libx264 -preset slow -crf 19 -maxrate 9M -bufsize 18M -pix_fmt yuv420p -color_primaries bt709 "
                   f"-color_trc bt709 -colorspace bt709 -c:a aac -b:a 192k -movflags +faststart {D}/out/{OUTN}.mp4",
                   shell=True, check=True)


def cover():
    Image.fromarray(page0(1.6)).save(f"{D}/out/{OUTN}_muqova.jpg", quality=92)


if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else "all"
    if what == "prev":
        ts = list(map(float, sys.argv[2].split(",")))
        ims = []
        for tt in ts:
            R.clear()
            ims.append(Image.fromarray(frame_at(tt)).resize((360, 640)))
        c = Image.new("RGB", (365 * len(ims), 640), "white")
        for k, im in enumerate(ims):
            c.paste(im, (k * 365, 0))
        c.save(f"{D}/prev_m.jpg", quality=85)
    if what in ("frames", "all"):
        frames()
    if what in ("music", "all"):
        music()
    if what in ("final", "all"):
        final()
    if what in ("cover", "all"):
        cover()
