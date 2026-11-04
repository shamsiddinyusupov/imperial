"""Hi-tech Reels cover (no logo): before | after split, content inside the 3:4 grid crop."""
import sys
from PIL import Image, ImageDraw
sys.path.insert(0, "/home/claude/reels/scripts")
import assets_ht as h


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


before, after, out = sys.argv[1], sys.argv[2], sys.argv[3]
W, H = 1080, 1920
ACC = (140, 228, 255)
b = clean_pane(Image.open(before).convert("RGB"))
c = Image.open(after).convert("RGB")
im = Image.new("RGB", (W, H))
im.paste(b.crop((0, 0, 540, H)), (0, 0))
im.paste(c.crop((540, 0, W, H)), (540, 0))
im = im.convert("RGBA")
im.alpha_composite(Image.open("/home/claude/reels/assets_ht/scrim.png"))
im.alpha_composite(Image.open("/home/claude/reels/assets_ht/hud.png"))

band = Image.new("RGBA", (W, H), (0, 0, 0, 0))
bd = ImageDraw.Draw(band)
for yy in range(1040, 1640):
    a = 0.30 * min(1, (yy - 1040) / 160) * min(1, (1640 - yy) / 160)
    bd.line([(0, yy), (W, yy)], fill=(8, 12, 16, int(255 * a)))
im.alpha_composite(band)
lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
d = ImageDraw.Draw(lay)
# split line with accent
d.line([(540, 260), (540, 1540)], fill=(255, 255, 255, 170), width=2)
d.rectangle((538, 620, 542, 760), fill=ACC + (255,))
fm = h.font(h.F_MONO_B, 30)
for lab, right in [("OLDIN", False), ("KEYIN", True)]:
    kw = h.tw(fm, lab, 4)
    x = 1000 - kw - 28 if right else 108
    d.rounded_rectangle((x - 28, 382, x + kw + 28, 446), radius=8, fill=(10, 14, 18, 165),
                        outline=ACC + (200,), width=2)
    h.draw_tracked(d, (x, 396), lab, fm, ACC + (255,), 4)
# headline block, lower area
fl, fh, fr = h.font(h.F_MONO_B, 28), h.font(h.F_HEAD, 74), h.font(h.F_RU, 36)
h.draw_tracked(d, (80, 1150), "PARDA · ШТОРЫ", fl, ACC + (255,), 3)
y = 1200
for l in ["PARDA XONANI", "QANDAY", "O‘ZGARTIRADI?"]:
    h.draw_tracked(d, (80, y), l, fh, (255, 255, 255, 255), 4)
    y += 88
d.text((80, y + 14), "Как шторы меняют комнату", font=fr, fill=(255, 255, 255, 230))
im.alpha_composite(h.with_shadow(lay))
im.convert("RGB").save(out, quality=95)
print("ok", out)
