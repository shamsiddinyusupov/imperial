"""Dikey Reel «Faqat qarang» — no voice, calm piano, refined type, colours taken from the footage.

Type system (premium, 'did'):
  headline  Didone serif (Latin Modern Roman 17 — high contrast at display size)
  accent    Palatino italic (TeX Gyre Pagella Italic), caramel from the footage
  labels    Inter Display, small tracked capitals
  Russian   Lora Italic (Cyrillic)
Animations: only two — hook words rise from behind a mask after a hairline draws; one light sweep over IMPERIAL on the end card.

python3 faqat_qarang.py base      -> base.mp4 (segments joined with slow dissolves) + cuts.json
python3 faqat_qarang.py prev 1,9  -> preview overlays on base frames into frames/
python3 faqat_qarang.py ov        -> ov/0000.png … + bed.wav
"""
import colorsys
import glob
import json
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, "/home/claude/reels/common")
from compact import alpha, calm_bed, ease  # noqa: E402

D = "/home/claude/reels/dikey_style"
W, H, FPS = 1080, 1920, 30
XF = 0.6                                   # dissolve length
ORDER = ["A", "B", "C", "P2", "F", "P3", "P1"]   # v2: stabilised shots + owner photos (seg2/)
TAIL = 0.7                                 # hold the last frame under the end card


def g(n):
    return glob.glob(f"/usr/share/**/{n}", recursive=True)[0]


_F = {}


def F(path, size):
    k = (path, size)
    if k not in _F:
        _F[k] = ImageFont.truetype(path, size)
    return _F[k]


DID_P = g("lmroman17-regular.otf")
ITA_P = g("texgyrepagella-italic.otf")
LAB_P = "/usr/share/fonts/opentype/inter/InterDisplay-Regular.otf"
LIG_P = "/usr/share/fonts/opentype/inter/InterDisplay-Light.otf"
RU_P = "/usr/share/fonts/truetype/google-fonts/Lora-Italic-Variable.ttf"
DID = lambda s: F(DID_P, s)
ITA = lambda s: F(ITA_P, s)
LAB = lambda s: F(LAB_P, s)
LIG = lambda s: F(LIG_P, s)
RU = lambda s: F(RU_P, s)


def dur(p):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p],
                                capture_output=True, text=True).stdout)


def run(a):
    subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y"] + a, check=True)


# ---------------------------------------------------------------- base
def base():
    ds = [dur(f"{D}/seg2/{s}.mp4") for s in ORDER]
    ins, fc, off, last = [], [], [], "0:v"
    t = 0.0
    for i, s in enumerate(ORDER):
        ins += ["-i", f"{D}/seg2/{s}.mp4"]
    for i in range(1, len(ORDER)):
        t += ds[i - 1] - XF
        off.append(round(t, 3))
        lab = f"x{i}"
        fc.append(f"[{last}][{i}:v]xfade=transition=fade:duration={XF}:offset={t:.3f}[{lab}]")
        last = lab
    total = t + ds[-1] + TAIL
    fc.append(f"[{last}]tpad=stop_mode=clone:stop_duration={TAIL},format=yuv420p[v]")
    run(ins + ["-filter_complex", ";".join(fc), "-map", "[v]", "-t", f"{total:.3f}", "-c:v", "libx264", "-preset", "fast",
               "-crf", "14", "-pix_fmt", "yuv420p", "-r", "30", f"{D}/base.mp4"])
    cuts = {"x": off, "total": round(total, 3), "durs": ds}
    json.dump(cuts, open(f"{D}/cuts.json", "w"), indent=1)
    print(cuts)


# ---------------------------------------------------------------- palette from the footage
def palette_from(path):
    sys.path.insert(0, D)
    from style_test import palette
    return palette(path)


def ui_colours():
    run(["-ss", "1.5", "-i", f"{D}/seg2/A.mp4", "-frames:v", "1", "-q:v", "2", f"{D}/frames/pal_S1.jpg"])
    taken, ui = palette_from(f"{D}/frames/pal_S1.jpg")
    return taken, ui


# ---------------------------------------------------------------- drawing helpers
def tw(t, f, tr=0.0):
    return sum(f.getlength(c) + f.size * tr for c in t) - (f.size * tr if t else 0)


def text_img(text, f, col, tr=0.0, pad=24):
    asc, desc = f.getmetrics()
    L = Image.new("RGBA", (int(tw(text, f, tr)) + 2 * pad, asc + desc + 2 * pad), (0, 0, 0, 0))
    d = ImageDraw.Draw(L)
    x = pad
    for c in text:
        d.text((x, pad), c, font=f, fill=col)
        x += f.getlength(c) + f.size * tr
    return L


def soft_shadow(L, b=14, a=0.5, dy=3):
    sh = Image.new("RGBA", L.size, (0, 0, 0, 0))
    sh.putalpha(L.getchannel("A").filter(ImageFilter.GaussianBlur(b)).point(lambda v: int(v * a)))
    o = Image.new("RGBA", L.size, (0, 0, 0, 0))
    o.alpha_composite(sh, (0, dy))
    o.alpha_composite(L)
    return o


def put(L, img, x, y, a=1.0, dx=0, dy=0):
    if a <= 0:
        return
    L.alpha_composite(alpha(img, min(1.0, a)), (int(x + dx), int(y + dy)))


def rise(L, img, x, y, p, depth=0.9):
    """Word rises from behind its own baseline (mask reveal)."""
    if p <= 0:
        return
    win = Image.new("RGBA", img.size, (0, 0, 0, 0))
    win.alpha_composite(img, (0, int(img.height * depth * (1 - p))))
    L.alpha_composite(win, (int(x), int(y)))


def sweep(img, p, band=150, gain=(255, 250, 238)):
    """Copy of img with one soft diagonal light band at progress p."""
    w, h = img.size
    xs = np.arange(w)[None, :] + 0.4 * np.arange(h)[:, None]
    cx = -band + p * (w + 2 * band + 0.4 * h)
    m = np.clip(1 - np.abs(xs - cx) / band, 0, 1) ** 2 * 0.9
    a = np.asarray(img.getchannel("A"), dtype=np.float32) / 255
    hi = Image.new("RGBA", img.size, gain + (0,))
    hi.putalpha(Image.fromarray((m * a * 255).astype(np.uint8)))
    out = img.copy()
    out.alpha_composite(hi)
    return out


def blob(box, amax, col, blur=70):
    """Soft dark cloud behind a text block, so cream text reads on bright tulle."""
    m = Image.new("L", (W, H), 0)
    ImageDraw.Draw(m).rounded_rectangle(box, 120, fill=int(255 * amax))
    m = m.filter(ImageFilter.GaussianBlur(blur))
    img = Image.new("RGBA", (W, H), col + (0,))
    img.putalpha(m)
    return img


def grad(top, y1, amax, col):
    ys = np.arange(H, dtype=np.float32)
    a = (np.clip(1 - ys / y1, 0, 1) if top else np.clip((ys - y1) / (H - y1), 0, 1)) ** 1.4 * amax
    img = np.zeros((H, W, 4), np.uint8)
    img[..., :3] = col
    img[..., 3] = (np.repeat(a[:, None], W, 1) * 255).astype(np.uint8)
    return Image.fromarray(img, "RGBA")


# ---------------------------------------------------------------- overlay
class Overlay:
    def __init__(self):
        self.c = json.load(open(f"{D}/cuts.json"))
        _, ui = ui_colours()
        self.ACC, self.TXT, self.DIM, self.SCR = ui["accent"], ui["text"], ui["dim"], ui["scrim"]
        self.HAIR = self.ACC
        x = self.c["x"]
        self.T = self.c["total"]
        self.hook_out = x[0] + 1.3                                            # hook text stays into the opening shot
        self.ch = [(x[2] + 0.45, x[3] + 0.15), (x[3] + 0.5, x[5] + 0.15)]     # 01 on P2, 02 on F + P3
        self.end_in = x[5] + 0.3
        self.SCRIM = grad(True, 1000, 0.5, self.SCR)
        self.BLOB_H = blob((10, 200, 960, 560), 0.5, self.SCR)
        self.BLOB_C = blob((10, 230, 900, 520), 0.5, self.SCR)
        self.DARK = Image.new("RGBA", (W, H), self.SCR + (178,))
        A, T_, Dm = self.ACC, self.TXT, self.DIM
        # hook
        self.h_lab = soft_shadow(text_img("IMPERIAL   ·   DIKEY JALYUZI", LAB(21), A, 0.46))
        self.h_w1 = soft_shadow(text_img("Faqat", DID(124), T_))
        self.h_w2 = soft_shadow(text_img("qarang.", ITA(124), A))
        self.h_ru = soft_shadow(text_img("Просто посмотрите", RU(30), Dm))
        # chapters
        self.chap = []
        for num, lab, line, ru in (("01", "TYUL", "Oq naqshli tyul", "Белый тюль с узором"),
                                   ("02", "BARXAT", "Jigarrang barxat", "Коричневый бархат")):
            self.chap.append((soft_shadow(text_img(num, ITA(46), A)), soft_shadow(text_img(lab, LAB(21), A, 0.46)),
                              soft_shadow(text_img(line, DID(76), T_)), soft_shadow(text_img(ru, RU(28), Dm))))
        # end card
        self.e_lab = soft_shadow(text_img("IZOHGA YOZING", LAB(21), A, 0.5))
        self.e_key = text_img("NARX", DID(150), T_, 0.08)
        self.e_sub = soft_shadow(text_img("narxlarni direktga yuboramiz", ITA(44), A))
        self.e_brand = text_img("IMPERIAL", DID(64), T_, 0.32)
        self.e_tag = soft_shadow(text_img("DIKEY  ·  PLISSE  ·  KOMBO  ·  TOSHKENT", LAB(19), A, 0.42))
        self.e_fact = soft_shadow(text_img("Toshkentda o‘lchov va o‘rnatish bepul  ·  1 yil kafolat", LIG(27), Dm))
        self.e_ru = soft_shadow(text_img("Напишите NARX — пришлём цены в директ", RU(27), Dm))

    def hook(self, L, t):
        out = 1 - ease((t - (self.hook_out - 0.4)) / 0.4)
        if out <= 0:
            return
        X, Y, PAD = 112, 270, 24
        Hl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(Hl)
        p = ease((t - 0.1) / 0.6)                                  # hairline draws down
        if p > 0:
            d.line([(84, Y + 22), (84, Y + 22 + 300 * p)], fill=self.HAIR, width=2)
        put(Hl, self.h_lab, X - PAD, Y - PAD, ease((t - 0.25) / 0.5), dx=-10 * (1 - ease((t - 0.25) / 0.5)))
        rise(Hl, self.h_w1, X - PAD - 4, Y + 30 - PAD, ease((t - 0.45) / 0.75))
        dyb = DID(124).getmetrics()[0] - ITA(124).getmetrics()[0]
        rise(Hl, self.h_w2, X - PAD + self.h_w1.width - 2 * PAD + 26, Y + 30 - PAD + dyb, ease((t - 0.8) / 0.75))
        put(Hl, self.h_ru, X - PAD, Y + 205 - PAD, ease((t - 1.5) / 0.6))
        L.alpha_composite(alpha(Hl, out))

    def chapter(self, L, t, k):
        t0, t1 = self.ch[k]
        if not (t0 - 0.1 < t < t1):
            return
        out = 1 - ease((t - (t1 - 0.4)) / 0.4)
        num, lab, line, ru = self.chap[k]
        X, Y, PAD = 112, 290, 24
        Cl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(Cl)
        p = ease((t - t0) / 0.6)
        d.line([(84, Y + 12), (84, Y + 12 + 196 * p)], fill=self.HAIR, width=2)
        q = ease((t - t0 - 0.1) / 0.6)
        put(Cl, num, X - PAD, Y - PAD - 8, q, dx=-10 * (1 - q))
        put(Cl, lab, X - PAD + num.width - 2 * PAD + 22, Y - PAD + 8 + 6, q, dx=-10 * (1 - q))
        r = ease((t - t0 - 0.3) / 0.7)
        put(Cl, line, X - PAD - 3, Y + 52 - PAD, r, dx=-14 * (1 - r))
        s = ease((t - t0 - 0.7) / 0.6)
        put(Cl, ru, X - PAD, Y + 152 - PAD, s)
        L.alpha_composite(alpha(Cl, out))

    def end(self, L, t):
        if t < self.end_in:
            return
        L.alpha_composite(alpha(self.DARK, ease((t - self.end_in) / 0.7)))
        E = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(E)
        cx = W / 2
        a = lambda d0, dd=0.6: ease((t - self.end_in - d0) / dd)
        put(E, self.e_lab, cx - self.e_lab.width / 2, 610, a(0.35), dy=8 * (1 - a(0.35)))
        k = self.e_key
        rise(E, soft_shadow(k), cx - k.width / 2, 640, a(0.5, 0.8), depth=0.7)
        put(E, self.e_sub, cx - self.e_sub.width / 2, 835, a(0.95))
        p = a(1.2, 0.7)
        if p > 0:
            d.line([(cx - 60 * p, 960), (cx + 60 * p, 960)], fill=self.HAIR, width=2)
        b = self.e_brand
        sp = (t - self.end_in - 1.9) / 1.1                               # one light sweep over IMPERIAL
        bb = sweep(b, sp) if 0 < sp < 1 else b
        put(E, soft_shadow(bb), cx - b.width / 2, 980, a(1.35, 0.7))
        put(E, self.e_tag, cx - self.e_tag.width / 2, 1080, a(1.5))
        put(E, self.e_fact, cx - self.e_fact.width / 2, 1140, a(1.7))
        put(E, self.e_ru, cx - self.e_ru.width / 2, 1186, a(1.85))
        L.alpha_composite(E)

    def __call__(self, t):
        L = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        top = 0.0
        if t < self.hook_out:
            top = 1 - ease((t - (self.hook_out - 0.4)) / 0.4)
        for t0, t1 in self.ch:
            if t0 - 0.4 < t < t1:
                top = max(top, ease((t - (t0 - 0.4)) / 0.4) * (1 - ease((t - (t1 - 0.4)) / 0.4)))
        if top > 0:
            L.alpha_composite(alpha(self.SCRIM, top))
            L.alpha_composite(alpha(self.BLOB_H if t < self.hook_out else self.BLOB_C, top))
        self.hook(L, t)
        self.chapter(L, t, 0)
        self.chapter(L, t, 1)
        self.end(L, t)
        return L


OV = None


def job(i):
    OV(i / FPS).save(f"{D}/ov/{i:04d}.png", compress_level=1)


def bed():
    c = json.load(open(f"{D}/cuts.json"))
    x, T = c["x"], c["total"]
    from nylon_bed import nylon_bed                  # new track (nylon guitar + strings), not used in earlier Reels
    nylon_bed(f"{D}/bed.wav", T, x, x[5] + 0.3, seed=5)


if __name__ == "__main__":
    os.makedirs(f"{D}/ov", exist_ok=True)
    os.makedirs(f"{D}/frames", exist_ok=True)
    cmd = sys.argv[1]
    if cmd == "base":
        base()
    elif cmd == "prev":
        OV = Overlay()
        for s in sys.argv[2].split(","):
            t = float(s)
            run(["-ss", f"{t:.3f}", "-i", f"{D}/base.mp4", "-frames:v", "1", "-q:v", "2", f"{D}/frames/b_{s}.jpg"])
            f = Image.open(f"{D}/frames/b_{s}.jpg").convert("RGBA")
            f.alpha_composite(OV(t))
            f.convert("RGB").save(f"{D}/frames/p_{s}.jpg", quality=90)
    elif cmd == "ov":
        OV = Overlay()
        for f in os.listdir(f"{D}/ov"):
            os.remove(f"{D}/ov/{f}")
        n = round(OV.T * FPS)
        from multiprocessing import Pool
        with Pool(2) as p:
            p.map(job, range(n), chunksize=20)
        bed()
        print("frames", n)
