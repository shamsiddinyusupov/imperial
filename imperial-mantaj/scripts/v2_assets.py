"""Graphics for reel #2 ("VHS before -> 4K after").

OUT/
  vhs_scan.png       scanlines (full frame)
  vhs_band.png       tracking-noise band (1080 x 160)
  vhs_osd.png        PLAY / OLDIN / date OSD (full frame)
  vhs_cap_<n>.png    VHS-style captions (full frame)
  glitch_4k.png      big "4K" for the tape-cut moment (full frame)
  badge_4k.png       small "4K" tag inside the HUD (full frame)
  cap_k<n>/          hi-tech caption reveal frames (reuses assets_ht styling)
"""
import os
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, "/home/claude/reels/scripts")
import assets_ht as h  # noqa: E402  (hi-tech caption renderer the client liked)

OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)
h.OUT = OUT
W, H = 1080, 1920
MONO_B = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
ACC = h.ACC


def f(p, s):
    return ImageFont.truetype(p, s)


def vhs_text(d_layer, xy, text, font, alpha=255, ghost=2, stroke=3, fill=(255, 255, 255),
             stroke_fill=(0, 0, 0)):
    """White OSD text with a stroke and soft red/cyan chroma ghosts, like a VCR overlay."""
    x, y = xy
    ghost_l = Image.new("RGBA", d_layer.size, (0, 0, 0, 0))
    gd = ImageDraw.Draw(ghost_l)
    gd.text((x - ghost, y), text, font=font, fill=(255, 40, 60, int(alpha * 0.4)))
    gd.text((x + ghost, y), text, font=font, fill=(40, 230, 255, int(alpha * 0.4)))
    d_layer.alpha_composite(ghost_l)
    ImageDraw.Draw(d_layer).text((x, y), text, font=font, fill=fill + (alpha,),
                                 stroke_width=stroke, stroke_fill=stroke_fill + (int(alpha * 0.85),))


def scanlines():
    a = np.zeros((H, W, 4), np.uint8)
    a[::3, :, 3] = 26
    Image.fromarray(a, "RGBA").save(f"{OUT}/vhs_scan.png")


def band():
    rng = np.random.default_rng(3)
    bh = 160
    a = np.zeros((bh, W, 4), np.uint8)
    prof = np.exp(-((np.arange(bh) - bh / 2) / (bh / 3.2)) ** 2)
    for y in range(bh):
        streak = rng.random(W) < 0.18 * prof[y]
        a[y, :, :3] = 235
        a[y, :, 3] = (streak * rng.integers(50, 115, W) * prof[y]).astype(np.uint8)
    im = Image.fromarray(a, "RGBA").filter(ImageFilter.BoxBlur(1))
    im = im.resize((W, bh), Image.BILINEAR)
    # horizontal smear
    im = im.filter(ImageFilter.GaussianBlur(0.6))
    im.save(f"{OUT}/vhs_band.png")


def osd():
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    big = f(MONO_B, 46)
    small = f(MONO_B, 34)
    vhs_text(lay, (80, 246), "▶ PLAY", big)
    t = "OLDIN"
    vhs_text(lay, (W - 80 - big.getlength(t), 246), t, big)
    d = "18.07.2026"   # filming date from the clip metadata
    vhs_text(lay, (W - 80 - small.getlength(d), 312), d, small, alpha=235)
    lay.save(f"{OUT}/vhs_osd.png")


def vhs_caption(n, uz, ru):
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    fu, fr = f(MONO_B, 52), f(MONO, 32)
    lines = uz.split("\n")
    lh, rlh = 66, 44
    top = 1480 - (lh * len(lines) + 14 + rlh)
    y = top
    for l in lines:
        vhs_text(lay, (80, y), l, fu)
        y += lh
    y += 14
    vhs_text(lay, (80, y), ru, fr, alpha=235, ghost=2)
    lay.save(f"{OUT}/vhs_cap_{n}.png")


def glitch_4k():
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    fb = f(h.F_HEAD, 300)
    t = "4K"
    w = fb.getlength(t)
    x, y = (W - w) / 2, 760
    ghost = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(ghost)
    gd.text((x - 10, y), t, font=fb, fill=(255, 40, 60, 150))
    gd.text((x + 10, y), t, font=fb, fill=(40, 230, 255, 150))
    lay.alpha_composite(ghost)
    ImageDraw.Draw(lay).text((x, y), t, font=fb, fill=(255, 255, 255, 255))
    fm = f(MONO_B, 34)
    s = "KEYIN · ПОСЛЕ"
    ImageDraw.Draw(lay).text(((W - fm.getlength(s)) / 2, y + 360), s, font=fm, fill=ACC + (255,))
    h.with_shadow(lay, blur=10, alpha=0.6).save(f"{OUT}/glitch_4k.png")


def badge_4k():
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    fm = f(MONO_B, 28)
    s = "4K"
    w = fm.getlength(s)
    x0, y0 = 92, 270
    d.rounded_rectangle((x0, y0, x0 + w + 28, y0 + 44), radius=6, outline=ACC + (230,), width=2,
                        fill=(8, 12, 16, 120))
    d.text((x0 + 14, y0 + 6), s, font=fm, fill=ACC + (255,))
    d.ellipse((x0 + w + 44, y0 + 15, x0 + w + 58, y0 + 29), fill=(255, 70, 70, 235))
    d.text((x0 + w + 68, y0 + 6), "REC", font=fm, fill=(255, 255, 255, 230))
    h.with_shadow(lay, blur=5, alpha=0.5).save(f"{OUT}/badge_4k.png")


BLUE = (26, 47, 176)


def endmenu(nf=150):
    """VCR blue-screen menu: 'Back to the old blinds?' -> cursor picks NO -> CTA. Frames timed with v2_beeps.py."""
    d_dir = f"{OUT}/endmenu"
    os.makedirs(d_dir, exist_ok=True)
    fq, fr, fo = f(MONO_B, 64), f(MONO, 32), f(MONO_B, 58)
    fc1, fcr, fcta, ftg = f(MONO_B, 50), f(MONO, 30), f(MONO_B, 50), f(MONO_B, 36)
    fosd = f(MONO_B, 46)
    q1, q2 = "ESKI JALYUZIGA", "QAYTAMIZMI?"
    tg = "t.me/imperialjalyuzi1"

    def typed(s, f0, f1, fr_):
        n = round(len(s) * max(0.0, min(1.0, (fr_ - f0) / max(1, f1 - f0))))
        return s[:n]

    def option(lay, x, y, label, selected, visible=True):
        if not visible:
            return
        d = ImageDraw.Draw(lay)
        tw_ = fo.getlength(label)
        if selected:
            d.rectangle((x - 20, y - 8, x + tw_ + 20, y + 74), fill=(255, 255, 255, 255))
            d.text((x, y), label, font=fo, fill=BLUE + (255,))
            d.text((x - 62, y), "▶", font=fo, fill=(255, 255, 255, 255))
        else:
            vhs_text(lay, (x, y), label, fo, stroke=0)

    for fr_ in range(nf):
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(lay)
        vhs_text(lay, (80, 246), "◀◀ REW", fosd, stroke=0)
        vhs_text(lay, (W - 80 - fosd.getlength("MENU"), 246), "MENU", fosd, stroke=0)
        if fr_ < 68:
            vhs_text(lay, (80, 640), typed(q1, 6, 19, fr_), fq, stroke=0)
            vhs_text(lay, (80, 724), typed(q2, 19, 30, fr_), fq, stroke=0)
            ra = max(0.0, min(1.0, (fr_ - 26) / 8))
            if ra > 0:
                d.text((80, 818), "Вернуться к старым жалюзи?", font=fr, fill=(255, 255, 255, int(225 * ra)))
            if fr_ >= 34:
                on_no = fr_ >= 46
                blink_off = 58 <= fr_ < 62
                option(lay, 160, 930, "HA", selected=not on_no)
                option(lay, 470, 930, "YO‘Q", selected=on_no and not blink_off)
                if blink_off:
                    vhs_text(lay, (470, 930), "YO‘Q", fo, stroke=0)
                d.text((160, 1022), "ДА", font=fr, fill=(255, 255, 255, 170))
                d.text((470, 1022), "НЕТ", font=fr, fill=(255, 255, 255, 170))
        else:
            vhs_text(lay, (80, 640), "✓ TO‘G‘RI TANLOV", fq, stroke=0)
            d.text((80, 734), "Правильный выбор", font=fr, fill=(255, 255, 255, 225))
            vhs_text(lay, (80, 880), typed("BEPUL O‘LCHOV,", 76, 88, fr_), fc1, stroke=0)
            vhs_text(lay, (80, 946), typed("YETKAZISH VA O‘RNATISH", 86, 100, fr_), fc1, stroke=0)
            ra = max(0.0, min(1.0, (fr_ - 98) / 8))
            if ra > 0:
                d.text((80, 1026), "Замер, доставка и установка — бесплатно", font=fcr,
                       fill=(255, 255, 255, int(220 * ra)))
            if fr_ >= 104:
                lab = "▶ DIREKTGA YOZING"
                tw_ = fcta.getlength(lab)
                d.rectangle((80 - 18, 1104, 80 + tw_ + 18, 1180), fill=(255, 255, 255, 255))
                d.text((80, 1112), lab, font=fcta, fill=BLUE + (255,))
            shown = typed(tg, 108, 122, fr_)
            if shown:
                vhs_text(lay, (80, 1226), shown, ftg, stroke=0)
                if fr_ >= 122 and (fr_ // 8) % 2 == 0:
                    cx = 80 + ftg.getlength(shown) + 8
                    d.rectangle((cx, 1230, cx + 22, 1268), fill=(255, 255, 255, 230))
        lay.save(f"{d_dir}/{fr_:03d}.png")


if __name__ == "__main__":
    scanlines()
    band()
    osd()
    vhs_caption(1, "QUYOSH TO‘G‘RI\nTUSHADIGAN DERAZA", "Окно на солнечной стороне")
    vhs_caption(2, "QUYOSH MATO ORASIDAN\nO‘TIB KETADI", "Солнце проходит сквозь ткань")
    vhs_caption(3, "JALYUZI OSILIB,\nQIYSHAYIB QOLGAN", "Жалюзи провисли и перекосились")
    glitch_4k()
    badge_4k()
    endmenu()
    h.caption("k1", "01/04 — KEYIN · ПОСЛЕ", "Plisse jalyuzi", "Жалюзи плиссе", 1, total=4)
    h.caption("k2", "02/04 — TABAQA", "Har bir tabaqaga\nalohida", "Отдельно на каждую створку", 2, total=4)
    h.caption("k3", "03/04 — QUYOSH", "Nurni o‘zingiz\nboshqarasiz", "Свет под вашим контролем", 3, total=4)
    h.caption("k4", "04/04 — OCHILISH", "Deraza bemalol\nochiladi", "Окно открывается свободно", 4, total=4)
    print("ok")
