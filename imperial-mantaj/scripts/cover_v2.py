"""Cover for reel #2: VHS 'before' half | clean 4K 'after' half, key content inside the 3:4 grid crop."""
import sys
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, "/home/claude/reels/scripts")
import assets_ht as h  # noqa: E402

vhs_frame, k_frame, out = sys.argv[1], sys.argv[2], sys.argv[3]
W, H = 1080, 1920
MONO_B = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
ACC = h.ACC
HT = "/home/claude/reels/assets_ht"
V2A = "/home/claude/reels/v2/assets"


def vhs_text(layer, xy, text, font, alpha=255, ghost=3):
    x, y = xy
    g = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    gd = ImageDraw.Draw(g)
    gd.text((x - ghost, y), text, font=font, fill=(255, 40, 60, int(alpha * 0.55)))
    gd.text((x + ghost, y), text, font=font, fill=(40, 230, 255, int(alpha * 0.55)))
    layer.alpha_composite(g)
    ImageDraw.Draw(layer).text((x, y), text, font=font, fill=(255, 255, 255, alpha),
                               stroke_width=3, stroke_fill=(0, 0, 0, int(alpha * 0.85)))


v = Image.open(vhs_frame).convert("RGB")
k = Image.open(k_frame).convert("RGB")
im = Image.new("RGB", (W, H))
im.paste(v.crop((180, 0, 720, H)), (0, 0))
im.paste(k.crop((300, 0, 840, H)), (540, 0))
im = im.convert("RGBA")
# scanlines only on the VHS half
scan = Image.open(f"{V2A}/vhs_scan.png").crop((0, 0, 540, H))
im.alpha_composite(scan, (0, 0))
im.alpha_composite(Image.open(f"{HT}/scrim.png"))

band = Image.new("RGBA", (W, H), (0, 0, 0, 0))
bd = ImageDraw.Draw(band)
for yy in range(1020, 1640):
    a = 0.32 * min(1, (yy - 1020) / 160) * min(1, (1640 - yy) / 160)
    bd.line([(0, yy), (W, yy)], fill=(8, 12, 16, int(255 * a)))
im.alpha_composite(band)

lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
d = ImageDraw.Draw(lay)
d.line([(540, 0), (540, H)], fill=(255, 255, 255, 200), width=3)
fm = ImageFont.truetype(MONO_B, 40)
vhs_text(lay, (64, 300), "▶ PLAY", fm)
vhs_text(lay, (64, 356), "OLDIN", ImageFont.truetype(MONO_B, 34), alpha=240)
# right half: 4K tag + KEYIN
f4 = ImageFont.truetype(MONO_B, 34)
x0, y0 = 600, 298
w4 = f4.getlength("4K")
d.rounded_rectangle((x0, y0, x0 + w4 + 30, y0 + 50), radius=6, outline=ACC + (240,), width=2, fill=(8, 12, 16, 140))
d.text((x0 + 15, y0 + 6), "4K", font=f4, fill=ACC + (255,))
d.ellipse((x0 + w4 + 48, y0 + 17, x0 + w4 + 64, y0 + 33), fill=(255, 70, 70, 240))
d.text((x0 + w4 + 74, y0 + 6), "REC", font=f4, fill=(255, 255, 255, 235))
fk = ImageFont.truetype(MONO_B, 34)
kw = h.tw(fk, "KEYIN", 3)
d.rounded_rectangle((x0 - 12, 358, x0 + kw + 12, 406), radius=6, fill=(8, 12, 16, 170))
h.draw_tracked(d, (x0, 362), "KEYIN", fk, ACC + (255,), 3)

fl, fh, fr = h.font(h.F_MONO_B, 28), h.font(h.F_HEAD, 74), h.font(h.F_RU, 36)
h.draw_tracked(d, (80, 1130), "PLISSE JALYUZI · ПЛИССЕ", fl, ACC + (255,), 3)
y = 1180
for line in ["QUYOSH TO‘G‘RI", "TUSHSA — QAYSI", "JALYUZI?"]:
    h.draw_tracked(d, (80, y), line, fh, (255, 255, 255, 255), 4)
    y += 88
d.text((80, y + 14), "Окно на солнечной стороне", font=fr, fill=(255, 255, 255, 230))
im.alpha_composite(h.with_shadow(lay))
im.convert("RGB").save(out, quality=95)
print("ok", out)
