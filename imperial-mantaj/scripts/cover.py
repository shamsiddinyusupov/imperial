"""Reels cover: before | after split, key content inside the 3:4 grid crop (y 240-1680)."""
import sys
from PIL import Image, ImageDraw
sys.path.insert(0, "/home/claude/reels/scripts")
import assets as a  # reuse fonts, colours, gold gradient, shadow

before, after, out = sys.argv[1], sys.argv[2], sys.argv[3]
W, H = 1080, 1920
b = Image.open(before).convert("RGB")
c = Image.open(after).convert("RGB")


def clean_pane(img, box=(403, 793, 496, 1128)):
    """Replace the camera operator's reflection in the night window pane with plain dark glass."""
    import numpy as np
    from PIL import ImageFilter
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    region = img.crop(box)
    soft = np.asarray(region.filter(ImageFilter.GaussianBlur(30))).astype(float)
    t = np.linspace(0, 1, h)[:, None, None]
    top, bot = np.array([46, 47, 52.0]), np.array([30, 31, 35.0])
    glass = top * (1 - t) + bot * t
    glass = glass * np.ones((h, w, 3))
    rng = np.random.default_rng(7)
    glass += rng.normal(0, 1.6, glass.shape)
    out = np.clip(glass * 0.88 + soft * 0.12, 0, 255).astype(np.uint8)
    patch = Image.fromarray(out)
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).rectangle((2, 2, w - 3, h - 3), fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(1.5))
    img.paste(patch, (x0, y0), mask)
    return img


b = clean_pane(b)
im = Image.new("RGB", (W, H))
im.paste(b.crop((0, 0, 540, H)), (0, 0))
im.paste(c.crop((540, 0, W, H)), (540, 0))
im = im.convert("RGBA")

# divider: thin gold line with soft shadow
div = Image.new("RGBA", (W, H), (0, 0, 0, 0))
div.paste(a.gold_gradient((6, H)).convert("RGBA"), (537, 0))
im.alpha_composite(a.shadow(div, blur=10, alpha=0.35, dy=0))


def pill_at(label, cx, cy, size=40):
    f = a.font(a.F_PILL, size)
    sp = 5
    tw = a.text_w(f, label, sp)
    pw, ph = int(tw + 72), 84
    g = a.gold_gradient((pw, ph)).convert("RGBA")
    m = Image.new("L", (pw, ph), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, pw - 1, ph - 1), radius=ph // 2, fill=255)
    g.putalpha(m)
    d = ImageDraw.Draw(g)
    asc, desc = f.getmetrics()
    x, y = (pw - tw) / 2, (ph - asc - desc) / 2 + 1
    for ch in label:
        d.text((x, y), ch, font=f, fill=a.DARK)
        x += f.getlength(ch) + sp
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    layer.alpha_composite(g, (int(cx - pw / 2), int(cy - ph / 2)))
    return a.shadow(layer, blur=14, alpha=0.3, dy=5)


im.alpha_composite(pill_at("OLDIN", 270, 735))
im.alpha_composite(pill_at("KEYIN", 810, 735))

# title card
fu, fr = a.font(a.F_UZ, 66), a.font(a.F_RU, 38)
lines_u = ["Parda xonani qanday", "o‘zgartiradi?"]
line_r = "Как шторы меняют комнату"
tw = max(max(a.text_w(fu, l) for l in lines_u), a.text_w(fr, line_r))
cw, ch = int(tw + 110), 290
card = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
d = ImageDraw.Draw(card)
d.rounded_rectangle((0, 0, cw - 1, ch - 1), radius=34, fill=a.CARD + (205,))
card.paste(a.gold_gradient((72, 4)), ((cw - 72) // 2, 32))
y = 52
for l in lines_u:
    d.text(((cw - a.text_w(fu, l)) / 2, y), l, font=fu, fill=a.INK)
    y += 80
d.text(((cw - a.text_w(fr, line_r)) / 2, y + 14), line_r, font=fr, fill=a.CHAMPAGNE)
layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
layer.alpha_composite(card, ((W - cw) // 2, 300))
im.alpha_composite(a.shadow(layer))

# logo pill near the bottom of the 3:4 crop
logo = Image.open("/home/claude/reels/assets/logo_clean.png")
lw = 380
lg = logo.resize((lw, int(logo.height * lw / logo.width)), Image.LANCZOS)
pw, ph = lw + 64, lg.height + 40
p = Image.new("RGBA", (pw, ph), (0, 0, 0, 0))
ImageDraw.Draw(p).rounded_rectangle((0, 0, pw - 1, ph - 1), radius=30, fill=a.CREAM + (238,))
p.alpha_composite(lg, (32, 20))
layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
layer.alpha_composite(p, ((W - pw) // 2, 1500))
im.alpha_composite(a.shadow(layer, blur=18, alpha=0.25, dy=6))

im.convert("RGB").save(out, quality=95)
print("ok", out)
