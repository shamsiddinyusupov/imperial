"""Dikey style test: light grade + 'Iliq krem' filter, palette taken from the frame, sparse premium animation.

python3 style_test.py board   -> out/dikey_uslub_namunasi.jpg
python3 style_test.py video   -> ov/*.png (then ffmpeg composite, see bottom)
"""
import colorsys
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, "/home/claude/reels/common")
from compact import MED, RUF, SER, SERI, SEMI, W, H, alpha, ease, shadow, tracked, tw  # noqa: E402

D = "/home/claude/reels/dikey_style"


def hx(c):
    return "#%02X%02X%02X" % tuple(int(v) for v in c)


def hls(c, l=None, s=None):
    h, l0, s0 = colorsys.rgb_to_hls(*(np.array(c) / 255))
    r = colorsys.hls_to_rgb(h, l0 if l is None else l, s0 if s is None else s)
    return tuple(int(round(v * 255)) for v in r)


def kmeans(px, k, it=40, seed=3):
    rng = np.random.default_rng(seed)
    c = px[rng.choice(len(px), k, replace=False)]
    for _ in range(it):
        lab = ((px[:, None, :] - c[None]) ** 2).sum(-1).argmin(1)
        c = np.array([px[lab == i].mean(0) if (lab == i).any() else c[i] for i in range(k)])
    return c, np.bincount(lab, minlength=k) / len(lab)


def palette(path):
    """5 colours from the frame: shadow, cocoa (curtain), caramel (lit curtain), sand (mid), cream (tulle)."""
    px = np.asarray(Image.open(path).convert("RGB").resize((180, 320)), dtype=float).reshape(-1, 3)
    c, w = kmeans(px, 10)
    info = []
    for ci, wi in zip(c, w):
        h, l, s = colorsys.rgb_to_hls(*(ci / 255))
        info.append((l, s, wi, tuple(int(round(v)) for v in ci)))
    info.sort()
    cocoa = max((i for i in info if i[0] < 0.3), key=lambda i: i[1] * i[2])[3]          # most saturated dark = curtain
    caramel = max((i for i in info if 0.25 <= i[0] < 0.5), key=lambda i: i[1])[3]      # lit curtain
    sand = min((i for i in info if 0.55 <= i[0] < 0.72), key=lambda i: abs(i[0] - 0.65))[3]
    cream = max(info, key=lambda i: i[0])[3]                                          # tulle highlight
    shade = hls(cocoa, l=0.06)
    taken = [("Soya", shade), ("Kakao", cocoa), ("Yong‘oq", caramel), ("Qum", sand), ("Krem", cream)]
    # the same hues, lightness set for legible text / UI on footage
    ui = {"scrim": hls(cocoa, l=0.07, s=0.35), "accent": hls(caramel, l=0.66, s=0.42),
          "text": hls(cream, l=0.93, s=0.35), "dim": hls(sand, l=0.78, s=0.14), "pill": hls(cocoa, l=0.11, s=0.4)}
    return taken, ui


TAKEN, UI = palette(f"{D}/frames/grd_n2.jpg")
ACC, TXT, DIMC, SCR, PILL = UI["accent"], UI["text"], UI["dim"], UI["scrim"], UI["pill"]


def scrim_top(y1=1000, amax=0.7):
    ys = np.arange(H, dtype=np.float32)
    a = np.clip(1 - ys / y1, 0, 1) ** 1.35 * amax
    img = np.zeros((H, W, 4), np.uint8)
    img[..., :3] = SCR
    img[..., 3] = (np.repeat(a[:, None], W, 1) * 255).astype(np.uint8)
    return Image.fromarray(img, "RGBA")


SCRIM = scrim_top()
Y0, XR, X0 = 300, 84, 112
HEAD = "Yorug‘lik — siz xohlagancha."
LABEL = "IMPERIAL  ·  DIKEY JALYUZI"
RU = "Свет — так, как вам нужно"


def text_img(text, f, col, tr=0.0):
    L = Image.new("RGBA", (int(tw(text, f, tr)) + 40, int(f.size * 1.45)), (0, 0, 0, 0))
    tracked(ImageDraw.Draw(L), (0, 2), text, f, col, tr)
    return L


FH = SER(66)
while tw(HEAD, FH) > 860:
    FH = SER(FH.size - 2)
HEAD_I = text_img(HEAD, FH, TXT)
HEAD_HI = text_img(HEAD, FH, (255, 250, 238))
LAB_I = text_img(LABEL, MED(22), ACC, 0.32)
RU_I = text_img(RU, RUF(26), DIMC)
Y_LAB, Y_HEAD, Y_RU = Y0, Y0 + 44, Y0 + 44 + int(FH.size * 1.2)
Y_END = Y_RU + 40


def cta():
    f1, f2 = MED(26), SEMI(26)
    parts = [("Izohga ", f1, TXT), ("NARX", f2, ACC), (" yozing", f1, TXT)]
    w = sum(f.getlength(t) for t, f, _ in parts)
    L = Image.new("RGBA", (W, 90), (0, 0, 0, 0))
    d = ImageDraw.Draw(L)
    x = (W - w) / 2
    d.rounded_rectangle((x - 30, 8, x + w + 30, 70), 31, fill=PILL + (215,), outline=ACC, width=1)
    for t, f, c in parts:
        d.text((x, 22), t, font=f, fill=c)
        x += f.getlength(t)
    return L


CTA = cta()


def sweep_mask(size, p, band=170):
    """Soft diagonal light band crossing the headline, p 0→1."""
    w, h = size
    xs = np.arange(w)[None, :] + 0.35 * np.arange(h)[:, None]
    cx = -band + p * (w + 2 * band + 0.35 * h)
    a = np.clip(1 - np.abs(xs - cx) / band, 0, 1) ** 2 * 0.85
    return Image.fromarray((a * 255).astype(np.uint8), "L")


def overlay(t, T=6.0):
    L = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    out = 1 - ease((t - (T - 0.45)) / 0.45) if t > T - 0.45 else 1
    L.alpha_composite(alpha(SCRIM, ease(t / 0.4)))
    T_ = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(T_)
    # 1) hairline draws down
    p = ease((t - 0.15) / 0.55)
    if p > 0:
        d.line([(XR, Y_LAB + 4), (XR, Y_LAB + 4 + (Y_END - Y_LAB) * p)], fill=ACC, width=2)
    # 2) label fades in, tracking settles
    p = ease((t - 0.35) / 0.5)
    if p > 0:
        T_.alpha_composite(alpha(LAB_I, p), (X0 + int(10 * (1 - p)), Y_LAB))
    # 3) headline mask reveal: rises from behind its own baseline
    p = ease((t - 0.6) / 0.7)
    if p > 0:
        hh = HEAD_I.height
        win = Image.new("RGBA", (HEAD_I.width, hh), (0, 0, 0, 0))
        head = HEAD_I.copy()
        # 4) one light sweep across the headline
        q = (t - 2.4) / 0.9
        if 0 < q < 1:
            hi = HEAD_HI.copy()
            hi.putalpha(Image.fromarray(np.minimum(np.asarray(HEAD_HI.getchannel("A")), np.asarray(sweep_mask(HEAD_HI.size, q)))))
            head.alpha_composite(hi)
        win.alpha_composite(head, (0, int(hh * 0.85 * (1 - p))))
        T_.alpha_composite(win, (X0, Y_HEAD))
    # 5) Russian line
    p = ease((t - 1.35) / 0.5)
    if p > 0:
        T_.alpha_composite(alpha(RU_I, p), (X0, Y_RU))
    L.alpha_composite(alpha(shadow(T_, 10, 0.5), out))
    # 6) CTA pill late, quiet
    p = ease((t - 3.6) / 0.5)
    if p > 0:
        L.alpha_composite(alpha(CTA, p * out), (0, 1540 + int(12 * (1 - p))))
    return L


def board():
    BW, PAD = 1080, 40
    BG = hls(TAKEN[1][1], l=0.07, s=0.3)
    raw = Image.open(f"{D}/frames/raw_n1.jpg").convert("RGB")
    grd = Image.open(f"{D}/frames/grd_n1.jpg").convert("RGBA")
    mock = Image.open(f"{D}/frames/grd_n2.jpg").convert("RGBA")
    mock.alpha_composite(overlay(4.2))
    pw, ph = 480, 853
    B = Image.new("RGB", (BW, 3020), BG)
    d = ImageDraw.Draw(B)

    def lab(x, y, s, col=ACC, f=None):
        tracked(d, (x, y), s, f or MED(20), col, 0.3)

    lab(PAD + 20, 56, "IMPERIAL  ·  DIKEY  ·  USLUB NAMUNASI")
    d.text((PAD + 20, 92), "Ranglar kadrning o‘zidan.", font=SER(58), fill=TXT)
    d.text((PAD + 20, 168), "Ozgina bo‘yash + «Iliq krem» filtri + shu kadrdan olingan palitra", font=SERI(30), fill=DIMC)
    y = 250
    for i, (im, name) in enumerate(((raw, "OLDIN  ·  telefon kadri"), (grd.convert("RGB"), "KEYIN  ·  «Iliq krem» filtri"))):
        x = PAD + 20 + i * (pw + 40)
        B.paste(im.resize((pw, ph), Image.LANCZOS), (x, y + 40))
        lab(x, y, name, ACC if i else DIMC)
    y += 40 + ph + 70
    lab(PAD + 20, y, "1.  KADRDAN OLINGAN RANGLAR")
    y += 46
    sw = (BW - 2 * (PAD + 20) - 4 * 18) // 5
    for i, (name, c) in enumerate(TAKEN):
        x = PAD + 20 + i * (sw + 18)
        d.rounded_rectangle((x, y, x + sw, y + 150), 14, fill=c, outline=hls(c, l=min(0.9, colorsys.rgb_to_hls(*(np.array(c) / 255))[1] + 0.12)), width=1)
        d.text((x, y + 164), name, font=SER(30), fill=TXT)
        d.text((x, y + 204), hx(c), font=MED(20), fill=DIMC)
    y += 270
    lab(PAD + 20, y, "2.  MATN VA TUGMALARDA")
    d.text((PAD + 20, y + 34), "o‘sha ranglar — o‘qilishi uchun ochroq yoki to‘qroq qilingan", font=SERI(26), fill=DIMC)
    y += 84
    roles = [("Fon / parda", SCR), ("Tugma", PILL), ("Urg‘u", ACC), ("Ikkinchi matn", DIMC), ("Asosiy matn", TXT)]
    for i, (name, c) in enumerate(roles):
        x = PAD + 20 + i * (sw + 18)
        d.rounded_rectangle((x, y, x + sw, y + 90), 45, fill=c, outline=ACC if i < 2 else None, width=1)
        d.text((x, y + 104), name, font=SER(26), fill=TXT)
        d.text((x, y + 140), hx(c), font=MED(20), fill=DIMC)
    y += 210
    lab(PAD + 20, y, "3.  REELS KADRIDA")
    y += 46
    B.paste(mock.convert("RGB").resize((pw, ph), Image.LANCZOS), (PAD + 20, y))
    tx = PAD + 20 + pw + 40
    notes = [("Animatsiya — faqat 2 ta", ACC),
             ("• chiziq pastga chiziladi,", TXT), ("  sarlavha «tagidan» ko‘tariladi", TXT),
             ("• sarlavha ustidan bir marta", TXT), ("  yengil yorug‘lik o‘tadi", TXT),
             ("", TXT), ("Qolgani — tinch", ACC),
             ("• sakrash, aylanish, emoji yo‘q", TXT), ("• kesish — so‘z ustida", TXT),
             ("• fon qora emas, kakao rangda", TXT), ("• tugma: kakao + karamel chiziq", TXT)]
    yy = y + 10
    for s, c in notes:
        if c == ACC and s:
            tracked(d, (tx, yy), s.upper(), MED(20), ACC, 0.3)
            yy += 44
        else:
            d.text((tx, yy), s, font=SER(28), fill=c)
            yy += 40
    y += ph + 50
    d.line([(PAD + 20, y), (BW - PAD - 20, y)], fill=hls(ACC, l=0.35), width=1)
    for k, s in enumerate(("Namuna bugungi kadrlarda (IMG_3959, IMG_3967). Har bir klipning oq rangi alohida to‘g‘rilanadi,",
                           "keyin hammasiga bitta umumiy filtr. Mato rangi haqiqiydek qoladi — mijoz aynan shuni oladi.")):
        d.text((PAD + 20, y + 20 + k * 32), s, font=RUF(21), fill=DIMC)
    B = B.crop((0, 0, BW, y + 100))
    os.makedirs(f"{D}/out", exist_ok=True)
    B.save(f"{D}/out/dikey_uslub_namunasi.jpg", quality=92)
    print("board", B.size, [hx(c) for _, c in TAKEN], {k: hx(v) for k, v in UI.items()})


if __name__ == "__main__":
    if sys.argv[1] == "board":
        board()
    elif sys.argv[1] == "prev":
        g = Image.open(f"{D}/frames/grd_n2.jpg").convert("RGBA")
        for s in sys.argv[2].split(","):
            f = g.copy()
            f.alpha_composite(overlay(float(s)))
            f.convert("RGB").save(f"{D}/frames/prev_{s}.jpg")
    else:
        os.makedirs(f"{D}/ov", exist_ok=True)
        for i in range(180):
            overlay(i / 30).save(f"{D}/ov/{i:04d}.png", compress_level=1)
        print("frames 180")
