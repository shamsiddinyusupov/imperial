"""Render overlay graphics (PNG with alpha) for the Imperial Jalyuzi reel."""
import sys
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageChops
import numpy as np

OUT = sys.argv[1] if __name__ == "__main__" else None
LOGO_SRC = sys.argv[2] if __name__ == "__main__" else None
W, H = 1080, 1920

FD = "/usr/share/fonts/opentype/inter/"
F_UZ = FD + "InterDisplay-SemiBold.otf"
F_RU = FD + "Inter-Regular.otf"
F_PILL = FD + "InterDisplay-Bold.otf"
F_MED = FD + "InterDisplay-Medium.otf"

INK = (255, 255, 255, 255)
CHAMPAGNE = (236, 222, 186, 255)
CARD = (30, 27, 24)
GOLD_A = (222, 189, 112)
GOLD_B = (178, 140, 62)
DARK = (42, 38, 33, 255)
CREAM = (251, 248, 242)


def font(path, size):
    return ImageFont.truetype(path, size)


def text_w(f, s, spacing=0):
    if spacing:
        return sum(f.getlength(c) for c in s) + spacing * (len(s) - 1)
    return f.getlength(s)


def wrap(f, s, maxw):
    words, lines, cur = s.split(" "), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if text_w(f, t) <= maxw or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = w
    lines.append(cur)
    return lines


def gold_gradient(size):
    w, h = size
    a = np.array(GOLD_A, dtype=float)
    b = np.array(GOLD_B, dtype=float)
    t = np.linspace(0, 1, w)[None, :, None]
    diag = (np.linspace(0, 1, h)[:, None, None] * 0.35)
    k = np.clip(t * 0.8 + diag, 0, 1)
    arr = a * (1 - k) + b * k
    return Image.fromarray(arr.astype(np.uint8), "RGB")


def shadow(layer, blur=22, alpha=0.28, dy=8):
    a = layer.split()[-1].point(lambda v: int(v * alpha))
    sh = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    sh.putalpha(a)
    sh = sh.filter(ImageFilter.GaussianBlur(blur))
    base = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    base.alpha_composite(sh, (0, dy))
    base.alpha_composite(layer)
    return base


def caption(uz, ru, name, cy=1300):
    """Dark translucent card, Uzbek line(s) white, Russian line champagne."""
    fu, fr = font(F_UZ, 60), font(F_RU, 36)
    maxw = 860
    ul = [l for part in uz.split("\n") for l in wrap(fu, part, maxw)]
    rl = wrap(fr, ru, maxw)
    lh_u, lh_r = 74, 46
    tw = max([text_w(fu, l) for l in ul] + [text_w(fr, l) for l in rl])
    padx, pady, gap = 52, 38, 14
    cw = int(tw + 2 * padx)
    ch = int(pady * 2 + lh_u * len(ul) + gap + lh_r * len(rl) + 18)
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    card = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    d = ImageDraw.Draw(card)
    d.rounded_rectangle((0, 0, cw - 1, ch - 1), radius=30, fill=CARD + (190,))
    # thin gold rule
    rule = gold_gradient((64, 4))
    card.paste(rule, ((cw - 64) // 2, pady - 6))
    y = pady + 12
    for l in ul:
        d.text(((cw - text_w(fu, l)) / 2, y), l, font=fu, fill=INK)
        y += lh_u
    y += gap
    for l in rl:
        d.text(((cw - text_w(fr, l)) / 2, y), l, font=fr, fill=CHAMPAGNE)
        y += lh_r
    x0, y0 = (W - cw) // 2, cy - ch // 2
    layer.alpha_composite(card, (x0, y0))
    layer = shadow(layer)
    layer.save(f"{OUT}/{name}.png")


def pill(label, name, cy=378):
    f = font(F_PILL, 44)
    sp = 6
    tw = text_w(f, label, sp)
    pw, ph = int(tw + 84), 92
    grad = gold_gradient((pw, ph)).convert("RGBA")
    mask = Image.new("L", (pw, ph), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, pw - 1, ph - 1), radius=ph // 2, fill=255)
    grad.putalpha(mask)
    d = ImageDraw.Draw(grad)
    x = (pw - tw) / 2
    asc, desc = f.getmetrics()
    y = (ph - (asc + desc)) / 2 + 1
    for c in label:
        d.text((x, y), c, font=f, fill=DARK)
        x += f.getlength(c) + sp
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    layer.alpha_composite(grad, ((W - pw) // 2, cy - ph // 2))
    layer = shadow(layer, blur=16, alpha=0.25, dy=6)
    layer.save(f"{OUT}/{name}.png")


def clean_logo():
    # the supplied PNG already has a transparent background: just trim it
    logo = Image.open(LOGO_SRC).convert("RGBA")
    logo = logo.crop(logo.getbbox())
    logo.save(f"{OUT}/logo_clean.png")
    return logo


def watermark(logo):
    lw = 250
    lg = logo.resize((lw, int(logo.height * lw / logo.width)), Image.LANCZOS)
    pw, ph = lw + 44, lg.height + 26
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    pillimg = Image.new("RGBA", (pw, ph), (0, 0, 0, 0))
    ImageDraw.Draw(pillimg).rounded_rectangle((0, 0, pw - 1, ph - 1), radius=22, fill=CREAM + (225,))
    pillimg.alpha_composite(lg, (22, 13))
    layer.alpha_composite(pillimg, ((W - pw) // 2, 176))
    layer = shadow(layer, blur=14, alpha=0.18, dy=4)
    layer.save(f"{OUT}/watermark.png")


def endcard(logo):
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    cw, chh = 900, 1040
    card = Image.new("RGBA", (cw, chh), (0, 0, 0, 0))
    d = ImageDraw.Draw(card)
    d.rounded_rectangle((0, 0, cw - 1, chh - 1), radius=44, fill=CREAM + (244,))
    lw = 600
    lg = logo.resize((lw, int(logo.height * lw / logo.width)), Image.LANCZOS)
    y = 84
    card.alpha_composite(lg, ((cw - lw) // 2, y))
    y += lg.height + 52
    card.paste(gold_gradient((120, 4)), ((cw - 120) // 2, y))
    y += 50
    f1, f2 = font(F_UZ, 50), font(F_RU, 34)
    for l in ["Bepul o‘lchov,", "yetkazish va o‘rnatish"]:
        d.text(((cw - text_w(f1, l)) / 2, y), l, font=f1, fill=DARK)
        y += 64
    y += 10
    l = "Замер, доставка и установка — бесплатно"
    d.text(((cw - text_w(f2, l)) / 2, y), l, font=f2, fill=(120, 108, 92, 255))
    y += 92
    # CTA pill
    fp = font(F_PILL, 46)
    lab = "Direktga yozing"
    tw = text_w(fp, lab)
    pw, ph = int(tw + 120), 104
    g = gold_gradient((pw, ph)).convert("RGBA")
    m = Image.new("L", (pw, ph), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, pw - 1, ph - 1), radius=ph // 2, fill=255)
    g.putalpha(m)
    asc, desc = fp.getmetrics()
    ImageDraw.Draw(g).text(((pw - tw) / 2, (ph - asc - desc) / 2 + 1), lab, font=fp, fill=DARK)
    card.alpha_composite(g, ((cw - pw) // 2, y))
    y += ph + 44
    f3 = font(F_MED, 36)
    l = "Telegram: t.me/imperialjalyuzi1"
    d.text(((cw - text_w(f3, l)) / 2, y), l, font=f3, fill=DARK)
    y += 56
    f4 = font(F_RU, 30)
    l = "Toshkent · Ташкент"
    d.text(((cw - text_w(f4, l)) / 2, y), l, font=f4, fill=(120, 108, 92, 255))
    y += 40
    # trim card height to content
    final_h = y + 70
    card = card.crop((0, 0, cw, final_h))
    m2 = Image.new("L", (cw, final_h), 0)
    ImageDraw.Draw(m2).rounded_rectangle((0, 0, cw - 1, final_h - 1), radius=44, fill=255)
    card.putalpha(ImageChops.multiply(card.split()[-1], m2))
    layer.alpha_composite(card, ((W - cw) // 2, (H - final_h) // 2 - 40))
    layer = shadow(layer, blur=40, alpha=0.30, dy=14)
    layer.save(f"{OUT}/endcard.png")


if __name__ == "__main__":
    logo = clean_logo()
    watermark(logo)
    endcard(logo)
    pill("OLDIN · ДО", "pill_oldin")
    pill("KEYIN · ПОСЛЕ", "pill_keyin")
    caption("Parda xonani qanday o‘zgartiradi?", "Как шторы меняют комнату?", "cap_hook")
    caption("Shinam, yorug‘ va nafis", "Уютно, светло и элегантно", "cap_keyin")
    caption("Tilla naqshli premium mato", "Премиальная ткань с золотым узором", "cap_mato")
    caption("Nafis tyul + qalin parda", "Лёгкий тюль + плотные шторы", "cap_tyul")
    caption("Karniz bo‘ylab yengil suriladi", "Легко скользят по карнизу", "cap_karniz")
    caption("Shiftdan polgacha", "От потолка до пола", "cap_shift")
    caption("800+ turdagi mato\nTurkiya va Xitoydan", "800+ видов тканей из Турции и Китая", "cap_800")
    print("ok")
