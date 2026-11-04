"""Instagram carousel (1080x1350) — Plisse fabrics by thickness + NARX keyword CTA.

Style follows the website: paper background, ink text, brass/gold accent, Inter + mono labels.
Output: /home/claude/reels/narx/carousel/slide_01.jpg … slide_08.jpg
"""
import os
import subprocess
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

W, H = 1080, 1350
OUT = "/home/claude/reels/narx/carousel"
IMG = "/home/claude/reels/site/img"
SEG = "/home/claude/reels/v2/seg"
os.makedirs(OUT, exist_ok=True)

PAPER = (242, 238, 230)
CARD = (255, 255, 255)
INK = (30, 28, 25)
MUTED = (107, 100, 90)
LINE = (221, 213, 200)
GOLD = (176, 138, 62)
BRASS = (160, 124, 51)
DARK = (24, 22, 20)

FI = "/usr/share/fonts/opentype/inter/"
MONO_B = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"


def f(name, size):
    path = name if name.startswith("/") else FI + name
    return ImageFont.truetype(path, size)


H_MED = lambda s: f("InterDisplay-Medium.otf", s)
H_SEMI = lambda s: f("InterDisplay-SemiBold.otf", s)
H_LIGHT = lambda s: f("InterDisplay-Light.otf", s)
B_REG = lambda s: f("Inter-Regular.otf", s)
B_MED = lambda s: f("Inter-Medium.otf", s)
B_SEMI = lambda s: f("Inter-SemiBold.otf", s)


def tracked(d, xy, text, font, fill, track=0.12):
    x, y = xy
    sp = font.size * track
    for ch in text:
        d.text((x, y), ch, font=font, fill=fill)
        x += font.getlength(ch) + sp
    return x


def tracked_w(text, font, track=0.12):
    return sum(font.getlength(c) for c in text) + font.size * track * (len(text) - 1)


def wrap(text, font, width):
    out = []
    for para in text.split("\n"):
        words, line = para.split(" "), ""
        for w in words:
            t = (line + " " + w).strip()
            if font.getlength(t) <= width:
                line = t
            else:
                if line:
                    out.append(line)
                line = w
        out.append(line)
    return out


def draw_lines(d, x, y, lines, font, fill, lh):
    for ln in lines:
        d.text((x, y), ln, font=font, fill=fill)
        y += lh
    return y


def cover_fit(im, w, h, fx=0.5, fy=0.5):
    iw, ih = im.size
    s = max(w / iw, h / ih)
    im = im.resize((round(iw * s), round(ih * s)), Image.LANCZOS)
    x0 = round((im.width - w) * fx)
    y0 = round((im.height - h) * fy)
    return im.crop((x0, y0, x0 + w, y0 + h))


def contain_fit(im, w, h):
    im = im.copy()
    im.thumbnail((w, h), Image.LANCZOS)
    return im


def rounded(im, r):
    m = Image.new("L", im.size, 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, im.width - 1, im.height - 1), r, fill=255)
    out = Image.new("RGBA", im.size, (0, 0, 0, 0))
    out.paste(im.convert("RGBA"), (0, 0), m)
    return out


def shadow(base, box, r, blur=26, alpha=60, dy=14):
    sh = Image.new("RGBA", base.size, (0, 0, 0, 0))
    x0, y0, x1, y1 = box
    ImageDraw.Draw(sh).rounded_rectangle((x0, y0 + dy, x1, y1 + dy), r, fill=(60, 45, 30, alpha))
    base.alpha_composite(sh.filter(ImageFilter.GaussianBlur(blur)))


def logo(base, xy, h=58, dark_bg=False):
    lg = Image.open(f"{IMG}/{'logo_dark' if dark_bg else 'logo'}.png").convert("RGBA")
    lg = lg.resize((round(lg.width * h / lg.height), h), Image.LANCZOS)
    base.alpha_composite(lg, xy)


def meter(d, x, y, n, on=GOLD, off=LINE, label="YORUG‘LIK", lf=None, label_fill=MUTED):
    lf = lf or f(MONO_B, 20)
    x = tracked(d, (x, y), label, lf, label_fill, 0.1) + 14
    for i in range(4):
        d.rounded_rectangle((x, y - 1, x + 11, y + 25), 3, fill=on if i < n else off)
        x += 17
    return x


def pill(d, xy, text, font, fg, bg, pad=(22, 10), outline=None):
    x, y = xy
    w = font.getlength(text)
    bb = font.getbbox("Ag")
    h = bb[3] - bb[1]
    box = (x, y, x + w + 2 * pad[0], y + h + 2 * pad[1])
    d.rounded_rectangle(box, (box[3] - box[1]) // 2, fill=bg, outline=outline, width=2 if outline else 0)
    d.text((x + pad[0], y + pad[1] - bb[1]), text, font=font, fill=fg)
    return box


def frame_from(seg, t):
    p = f"/home/claude/reels/narx/frames/{seg}_{t}.png"
    if not os.path.exists(p):
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(t), "-i", f"{SEG}/{seg}.mp4", "-frames:v", "1", p], check=True)
    return Image.open(p).convert("RGB")


def save(base, n):
    base.convert("RGB").save(f"{OUT}/slide_{n:02d}.jpg", quality=93, subsampling=0)
    print("slide", n)


# ---------------------------------------------------------------- 1. cover
def s1():
    base = Image.new("RGBA", (W, H), PAPER + (255,))
    ph = cover_fit(frame_from("K2", 1.2), W, 900, 0.5, 0.45)
    base.paste(ph, (0, 0))
    g = Image.new("RGBA", (W, 260), (0, 0, 0, 0))
    gd = ImageDraw.Draw(g)
    for yy in range(260):
        gd.line([(0, yy), (W, yy)], fill=(14, 12, 10, int(150 * (1 - yy / 260) ** 1.6)))
    base.alpha_composite(g, (0, 0))
    logo(base, (64, 56), 62, dark_bg=True)
    d = ImageDraw.Draw(base)
    # paper panel
    d.rectangle((0, 900, W, H), fill=PAPER)
    tracked(d, (72, 958), "PLISSE JALYUZI · ПЛИССЕ", f(MONO_B, 24), BRASS, 0.14)
    y = draw_lines(d, 70, 1004, ["Qaysi mato", "sizga mos?"], H_MED(92), INK, 100)
    d.text((72, y + 18), "4 ta mato — qalinligi va narxi bilan", font=B_REG(34), fill=MUTED)
    pill(d, (W - 72 - 236, 1218), "Suring  →", B_SEMI(32), CARD, INK, pad=(30, 16))
    # price teaser badge on the photo
    bx, by = 72, 760
    badge = "1 m² — 100 000 so‘mdan"
    bf = B_SEMI(36)
    box = pill(d, (bx, by), badge, bf, INK, (255, 255, 255), pad=(26, 16))
    save(base, 1)


# ---------------------------------------------------------------- 2. why plisse
def s2():
    base = Image.new("RGBA", (W, H), PAPER + (255,))
    d = ImageDraw.Draw(base)
    logo(base, (64, 56), 50)
    tracked(d, (72, 150), "NEGA AYNAN PLISSE?", f(MONO_B, 24), BRASS, 0.14)
    draw_lines(d, 70, 192, ["Har bir tabaqaga —", "alohida plisse"], H_MED(64), INK, 74)
    ph = rounded(cover_fit(Image.open(f"{IMG}/g_plisse_7.jpg").convert("RGB"), 936, 520, 0.5, 0.42), 28)
    shadow(base, (72, 372, 72 + 936, 372 + 520), 28)
    base.alpha_composite(ph, (72, 372))
    d = ImageDraw.Draw(base)
    pts = [("Derazangiz o‘lchamida:", "har bir tabaqa aniq o‘lchab tayyorlanadi"),
           ("Tabaqa ochilganda", "jalyuzi u bilan birga yuradi"),
           ("Nurni o‘zingiz boshqarasiz:", "kerakli balandlikda to‘xtaydi")]
    y = 940
    for i, (a, b) in enumerate(pts):
        cx, cy = 102, y + 30
        d.ellipse((cx - 28, cy - 28, cx + 28, cy + 28), fill=INK)
        n = str(i + 1)
        nf = f(MONO_B, 28)
        d.text((cx - nf.getlength(n) / 2, cy - 18), n, font=nf, fill=GOLD)
        d.text((156, y), a, font=B_SEMI(34), fill=INK)
        d.text((156, y + 44), b, font=B_REG(30), fill=MUTED)
        y += 120
    save(base, 2)


# ---------------------------------------------------------------- 3-6. fabrics
FABRICS = [
    dict(n=3, name="Screen", lv="SHAFFOF", lv_ru="Прозрачная", light=4, gsm=247, colors=4, price="100 000",
         src="p_screen.jpg", fit="Oshxona va mehmonxona", note="Yorug‘likni yumshoq tarqatadi, xona yorug‘ qoladi."),
    dict(n=4, name="Lezbon", lv="YARIM SHAFFOF", lv_ru="Полупрозрачная", light=3, gsm=98, colors=15, price="130 000",
         src="p_lezbon.jpg", fit="Zal va bolalar xonasi", note="Quyoshni yumshatadi, xona yorug‘ligicha qoladi."),
    dict(n=5, name="Roma", lv="DIMOUT", lv_ru="Димаут", light=2, gsm=103, colors=9, price="170 000",
         src="p_roma.jpg", fit="Yotoqxona va ofis", note="Zich mato: xonani sezilarli qorong‘ilatadi."),
    dict(n=6, name="Blackout", lv="BLACKOUT", lv_ru="Блэкаут", light=1, gsm=206, colors=8, price="200 000",
         src="p_blackout.jpg", fit="Yotoqxona, quyoshli tomon", note="Eng qalin mato: nurni deyarli o‘tkazmaydi."),
]


def s_fabric(fb, idx):
    base = Image.new("RGBA", (W, H), PAPER + (255,))
    d = ImageDraw.Draw(base)
    logo(base, (64, 56), 50)
    lab = f"MATO {idx}/4"
    lf = f(MONO_B, 22)
    tracked(d, (W - 72 - tracked_w(lab, lf, 0.14), 70), lab, lf, MUTED, 0.14)
    # catalog photo card
    cx0, cy0, cx1, cy1 = 72, 150, W - 72, 790
    shadow(base, (cx0, cy0, cx1, cy1), 28, alpha=45)
    d.rounded_rectangle((cx0, cy0, cx1, cy1), 28, fill=(246, 245, 242))
    ph = Image.open(f"{IMG}/{fb['src']}").convert("RGB")
    ph = contain_fit(ph, cx1 - cx0 - 48, cy1 - cy0 - 48)
    base.alpha_composite(rounded(ph, 10), (cx0 + (cx1 - cx0 - ph.width) // 2, cy0 + (cy1 - cy0 - ph.height) // 2))
    d = ImageDraw.Draw(base)
    # level + meter
    y = 838
    x = tracked(d, (72, y), fb["lv"], f(MONO_B, 26), BRASS, 0.14)
    d.text((x + 16, y + 1), "· " + fb["lv_ru"], font=f(MONO, 24), fill=MUTED)
    meter(d, W - 72 - 236, y + 2, fb["light"], lf=f(MONO_B, 19))
    d.text((70, 880), fb["name"], font=H_MED(112), fill=INK)
    d.text((72, 1012), fb["note"], font=B_REG(32), fill=MUTED)
    meta = f"Zichligi {fb['gsm']} g/m²  ·  katalogda {fb['colors']} rang"
    d.text((72, 1062), meta, font=B_MED(30), fill=INK)
    # price bar
    d.rounded_rectangle((72, 1140, W - 72, 1280), 24, fill=INK)
    d.text((112, 1166), fb["price"], font=H_SEMI(76), fill=(242, 238, 230))
    pw = H_SEMI(76).getlength(fb["price"])
    d.text((112 + pw + 18, 1196), "so‘m / m²", font=B_MED(32), fill=GOLD)
    ff = f(MONO_B, 20)
    fit = "UCHUN: " + fb["fit"].upper()
    lines = wrap(fit, ff, 330)
    yy = 1210 - (len(lines) - 1) * 14
    for ln in lines:
        tracked(d, (W - 112 - tracked_w(ln, ff, 0.08), yy - 12), ln, ff, (200, 192, 178), 0.08)
        yy += 28
    save(base, fb["n"])


# ---------------------------------------------------------------- 7. how price is counted
def s7():
    base = Image.new("RGBA", (W, H), PAPER + (255,))
    d = ImageDraw.Draw(base)
    logo(base, (64, 56), 50)
    tracked(d, (72, 150), "NARX QANDAY HISOBLANADI?", f(MONO_B, 24), BRASS, 0.14)
    draw_lines(d, 70, 192, ["Eni × bo‘yi = m²"], H_MED(84), INK, 90)
    d.text((72, 300), "Har bir tabaqa alohida hisoblanadi.", font=B_REG(34), fill=MUTED)

    def card(y, title, w_cm, h_cm, area, billed, total, hl=False):
        x0, x1 = 72, W - 72
        d.rounded_rectangle((x0, y, x1, y + 300), 26, fill=CARD, outline=GOLD if hl else LINE, width=3 if hl else 2)
        # window sketch
        sx, sy = x0 + 40, y + 30
        sc = min(170 / w_cm, 196 / h_cm)
        ww, hh = w_cm * sc, h_cm * sc
        ox, oy = sx + (170 - ww) / 2, sy + (196 - hh) / 2
        d.rectangle((ox, oy, ox + ww, oy + hh), outline=INK, width=4)
        for k in range(1, 12):
            yy = oy + hh * k / 12
            d.line((ox + 4, yy, ox + ww - 4, yy), fill=(200, 190, 172), width=2)
        tf = f(MONO, 20)
        t = f"{w_cm} sm"
        d.text((ox + ww / 2 - tf.getlength(t) / 2, oy + hh + 8), t, font=tf, fill=MUTED)
        tx = x0 + 260
        d.text((tx, y + 40), title, font=f(MONO_B, 22), fill=BRASS)
        d.text((tx, y + 78), f"{w_cm} × {h_cm} sm = {area} m²", font=B_SEMI(40), fill=INK)
        d.text((tx, y + 134), billed, font=B_MED(30), fill=GOLD if hl else MUTED)
        d.text((tx, y + 196), total, font=H_SEMI(52), fill=INK)

    card(378, "KICHIK TABAQA", 60, 120, "0,72", "1 m² dan kichik → 1 m² hisoblanadi", "Lezbon: 130 000 so‘m", hl=True)
    card(710, "KATTA TABAQA", 140, 160, "2,24", "Haqiqiy maydon bo‘yicha", "Lezbon: ≈ 291 000 so‘m")
    d.text((72, 1050), "Nega kichigi ham 1 m²? Mexanizm bir xil —", font=B_REG(32), fill=MUTED)
    d.text((72, 1094), "o‘lchamdan qat’i nazar bir xil ishlatiladi.", font=B_REG(32), fill=MUTED)
    d.rounded_rectangle((72, 1170, W - 72, 1270), 50, fill=(232, 223, 205))
    msg = "O‘lchov, yetkazish va o‘rnatish — bepul"
    mf = B_SEMI(34)
    d.text(((W - mf.getlength(msg)) / 2, 1198), msg, font=mf, fill=INK)
    save(base, 7)


# ---------------------------------------------------------------- 8. CTA (NARX)
def s8():
    base = Image.new("RGBA", (W, H), DARK + (255,))
    ph = cover_fit(frame_from("K1", 1.0), W, H, 0.5, 0.5).filter(ImageFilter.GaussianBlur(18))
    ph = Image.blend(ph, Image.new("RGB", ph.size, DARK), 0.72)
    base.paste(ph, (0, 0))
    logo(base, (64, 56), 56, dark_bg=True)
    d = ImageDraw.Draw(base)
    tracked(d, (72, 220), "NARXLAR DIREKTDA", f(MONO_B, 26), GOLD, 0.14)
    draw_lines(d, 68, 266, ["Izohga", "NARX deb", "yozing"], H_SEMI(124), (245, 241, 233), 132)
    d.text((72, 690), "Hamma matolar narxi va bepul o‘lchov —", font=B_REG(34), fill=(205, 198, 186))
    d.text((72, 736), "darhol direktingizga keladi.", font=B_REG(34), fill=(205, 198, 186))
    # mock comment field
    y0 = 840
    d.rounded_rectangle((72, y0, W - 72, y0 + 112), 56, fill=(255, 255, 255))
    d.ellipse((96, y0 + 22, 164, y0 + 90), fill=(225, 215, 196))
    d.ellipse((118, y0 + 36, 142, y0 + 60), fill=(176, 160, 132))
    d.pieslice((106, y0 + 58, 154, y0 + 106), 180, 360, fill=(176, 160, 132))
    d.text((190, y0 + 30), "NARX", font=B_SEMI(46), fill=INK)
    cx = 190 + B_SEMI(46).getlength("NARX") + 6
    d.rectangle((cx, y0 + 30, cx + 4, y0 + 84), fill=GOLD)
    sb = (W - 72 - 100, y0 + 20, W - 72 - 28, y0 + 92)
    d.ellipse(sb, fill=GOLD)
    ax, ay = (sb[0] + sb[2]) / 2 + 3, (sb[1] + sb[3]) / 2
    d.polygon([(ax - 16, ay - 18), (ax + 20, ay), (ax - 16, ay + 18), (ax - 8, ay)], fill=INK)
    # bot reply bubble
    by = y0 + 150
    bub = (300, by, W - 72, by + 104)
    d.rounded_rectangle(bub, 30, fill=(48, 44, 38))
    # paper-plane icon
    px, py = bub[0] + 34, by + 30
    d.polygon([(px, py + 22), (px + 44, py), (px + 30, py + 46), (px + 22, py + 30)], fill=GOLD)
    d.text((bub[0] + 100, by + 18), "Imperial Jalyuzi", font=B_SEMI(26), fill=GOLD)
    d.text((bub[0] + 100, by + 54), "Narxlarni direktga yubordik", font=B_REG(30), fill=(235, 230, 220))
    d.text((72, 1200), "Напишите «NARX» в комментариях — цены придут в директ", font=B_REG(27), fill=(170, 162, 150))
    d.text((72, 1250), "t.me/jalyuzi_imperial  ·  +998 33 751 11 88", font=f(MONO_B, 24), fill=(205, 198, 186))
    save(base, 8)


if __name__ == "__main__":
    s1()
    s2()
    for i, fb in enumerate(FABRICS):
        s_fabric(fb, i + 1)
    s7()
    s8()
