"""Hi-tech overlay pack for the Imperial reel (no logo, captions lower, animated reveals).

Outputs (in OUT):
  scrim.png, hud.png                full-frame static layers
  cap_<id>/000..NNN.png             caption reveal frames, region 1080 x REG_H placed at y=REG_Y
  end/000..NNN.png                  end-card reveal frames, full frame
"""
import os
import sys
from PIL import Image, ImageDraw, ImageFilter, ImageFont

MAIN = __name__ == "__main__"
OUT = sys.argv[1] if MAIN else None
ACC = tuple(int(v) for v in (sys.argv[2] if MAIN and len(sys.argv) > 2 else "140,228,255").split(","))
W, H = 1080, 1920
X0 = 80
MAXW = 860
REG_Y, REG_H = 1040, 560          # caption region (y 1040..1600)
LINE_Y = 1500                     # progress line, bottom anchor of caption block
N_REVEAL = 20                     # frames of reveal animation (30 fps)

FD = "/usr/share/fonts/opentype/inter/"
F_HEAD = FD + "InterDisplay-Light.otf"
F_RU = FD + "Inter-Light.otf"
F_CTA = FD + "InterDisplay-Medium.otf"
F_MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
F_MONO_B = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
WHITE = (255, 255, 255)


def font(p, s):
    return ImageFont.truetype(p, s)


def tw(f, s, sp=0):
    return sum(f.getlength(c) for c in s) + sp * max(0, len(s) - 1) if sp else f.getlength(s)


def draw_tracked(d, xy, s, f, fill, sp):
    x, y = xy
    for c in s:
        d.text((x, y), c, font=f, fill=fill)
        x += f.getlength(c) + sp


def wrap(f, s, maxw, sp=0):
    out = []
    for part in s.split("\n"):
        cur = ""
        for w in part.split(" "):
            t = (cur + " " + w).strip()
            if tw(f, t, sp) <= maxw or not cur:
                cur = t
            else:
                out.append(cur)
                cur = w
        out.append(cur)
    return out


def clamp(v):
    return max(0.0, min(1.0, v))


def ease(v):
    v = clamp(v)
    return 1 - (1 - v) ** 3


def with_shadow(layer, blur=6, alpha=0.65):
    a = layer.split()[-1].point(lambda v: int(v * alpha))
    sh = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    sh.putalpha(a)
    sh = sh.filter(ImageFilter.GaussianBlur(blur))
    base = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    base.alpha_composite(sh, (0, 2))
    base.alpha_composite(layer)
    return base


# ---------- static layers ----------
def scrim():
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    px = im.load()
    for y in range(H):
        if y >= 860:
            a = clamp((y - 860) / (H - 860)) ** 1.15 * 0.80
        elif y <= 360:
            a = (1 - y / 360) ** 1.6 * 0.30
        else:
            a = 0
        for x in range(W):
            px[x, y] = (8, 12, 16, int(a * 255))
    im.save(f"{OUT}/scrim.png")


def hud():
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    L, T, R, B, arm, wdt = 56, 236, 1024, 1568, 44, 3
    c = WHITE + (215,)
    for (x, y, dx, dy) in [(L, T, 1, 1), (R, T, -1, 1), (L, B, 1, -1), (R, B, -1, -1)]:
        d.line([(x, y), (x + dx * arm, y)], fill=c, width=wdt)
        d.line([(x, y), (x, y + dy * arm)], fill=c, width=wdt)
    # small accent ticks on the top edge centre
    for i in range(-2, 3):
        x = W // 2 + i * 14
        d.line([(x, T - 2), (x, T + (10 if i == 0 else 6))], fill=ACC + (200,), width=2)
    with_shadow(im, blur=5, alpha=0.5).save(f"{OUT}/hud.png")


# ---------- captions ----------
def caption(cid, label, head, ru, k, total=7, static=False):
    fl, fh, fr = font(F_MONO_B, 26), font(F_HEAD, 58), font(F_RU, 33)
    hs = 3
    hl = wrap(fh, head.upper(), MAXW, hs)
    rl = wrap(fr, ru, MAXW)
    lab_h, gap1, lh, gap2, rlh, gap3 = 34, 22, 70, 10, 42, 30
    block = lab_h + gap1 + lh * len(hl) + gap2 + rlh * len(rl) + gap3
    top = LINE_Y - block
    y_lab = top
    y_head = y_lab + lab_h + gap1
    y_ru = y_head + lh * len(hl) + gap2
    head_w = max(tw(fh, l, hs) for l in hl)
    d_dir = f"{OUT}/cap_{cid}"
    os.makedirs(d_dir, exist_ok=True)
    frames = [N_REVEAL - 1] if static else range(N_REVEAL)
    for f in frames:
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(lay)
        # label: typewriter + cursor
        n = round(len(label) * clamp(f / 10))
        shown = label[:n]
        draw_tracked(d, (X0, y_lab), shown, fl, ACC + (255,), 2)
        if f < 13 and (f // 3) % 2 == 0:
            cx = X0 + tw(fl, shown, 2) + 4
            d.rectangle((cx, y_lab + 4, cx + 12, y_lab + 30), fill=ACC + (230,))
        # headline: wipe reveal left -> right with scanner bar
        wp = ease((f - 3) / 12)
        if wp > 0:
            hl_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            hd = ImageDraw.Draw(hl_layer)
            for i, l in enumerate(hl):
                draw_tracked(hd, (X0, y_head + i * lh), l, fh, WHITE + (255,), hs)
            edge = X0 + wp * (head_w + 30)
            m = Image.new("L", (W, H), 0)
            ImageDraw.Draw(m).rectangle((0, 0, int(edge), H), fill=255)
            hl_layer.putalpha(Image.composite(hl_layer.split()[-1], Image.new("L", (W, H), 0), m))
            lay.alpha_composite(hl_layer)
            bar_a = 1 - clamp((f - 12) / 5)
            if bar_a > 0:
                d.rectangle((int(edge), y_head - 6, int(edge) + 3, y_head + lh * len(hl) - 8),
                            fill=ACC + (int(255 * bar_a),))
        # russian line: fade
        ra = clamp((f - 9) / 8)
        if ra > 0:
            for i, l in enumerate(rl):
                d.text((X0, y_ru + i * rlh), l, font=fr, fill=WHITE + (int(230 * ra),))
        # (progress line removed at the client's request; LINE_Y still anchors the block)
        lay = with_shadow(lay)
        lay.crop((0, REG_Y, W, REG_Y + REG_H)).save(f"{d_dir}/{f:03d}.png" if not static else f"{d_dir}/000.png")


# ---------- end card ----------
def endcard(nf=40):
    d_dir = f"{OUT}/end"
    os.makedirs(d_dir, exist_ok=True)
    fl, fr = font(F_MONO, 28), font(F_RU, 34)
    fbig = font(F_HEAD, 80)
    fcta = font(F_CTA, 38)
    fidx = font(F_MONO, 30)
    rows = ["O‘LCHOV", "YETKAZISH", "O‘RNATISH"]
    label = "BEPUL XIZMAT · БЕСПЛАТНО"
    tg = "t.me/imperialjalyuzi1"
    y_lab, y_rows, row_h = 640, 712, 128
    y_ru = y_rows + row_h * 3 + 34
    y_cta = y_ru + 92
    y_tg = y_cta + 140
    for f in range(nf):
        lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(lay)
        n = round(len(label) * clamp(f / 12))
        draw_tracked(d, (X0, y_lab), label[:n], fl, ACC + (255,), 3)
        for i, r in enumerate(rows):
            p = ease((f - 4 - 5 * i) / 12)
            y = y_rows + i * row_h
            d.line([(X0, y), (X0 + int(920 * p), y)], fill=WHITE + (110,), width=2)
            if p > 0:
                d.text((X0, y + 42), f"0{i + 1}", font=fidx, fill=ACC + (int(255 * p),))
                tl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
                draw_tracked(ImageDraw.Draw(tl), (X0 + 96, y + 20), r, fbig, WHITE + (255,), 4)
                m = Image.new("L", (W, H), 0)
                ImageDraw.Draw(m).rectangle((0, 0, X0 + 96 + int(p * 760), H), fill=255)
                tl.putalpha(Image.composite(tl.split()[-1], Image.new("L", (W, H), 0), m))
                lay.alpha_composite(tl)
        p = ease((f - 19) / 10)
        d.line([(X0, y_rows + 3 * row_h), (X0 + int(920 * p), y_rows + 3 * row_h)], fill=WHITE + (110,), width=2)
        ra = clamp((f - 20) / 8)
        d.text((X0, y_ru), "Замер · доставка · установка", font=fr, fill=WHITE + (int(190 * ra),))
        ca = ease((f - 24) / 9)
        if ca > 0:
            lab = "DIREKTGA YOZING"
            w_txt = tw(fcta, lab, 4)
            pw, ph = int(w_txt + 150), 100
            yy = y_cta + int((1 - ca) * 24)
            d.rounded_rectangle((X0, yy, X0 + pw, yy + ph), radius=ph // 2,
                                outline=WHITE + (int(235 * ca),), width=2)
            asc, desc = fcta.getmetrics()
            draw_tracked(d, (X0 + 46, yy + (ph - asc - desc) / 2), lab, fcta, WHITE + (int(255 * ca),), 4)
            ax = X0 + 46 + w_txt + 26
            ay = yy + ph // 2
            d.line([(ax, ay), (ax + 40, ay)], fill=ACC + (int(255 * ca),), width=3)
            d.line([(ax + 28, ay - 12), (ax + 40, ay), (ax + 28, ay + 12)], fill=ACC + (int(255 * ca),), width=3)
        n2 = round(len(tg) * clamp((f - 27) / 10))
        draw_tracked(d, (X0, y_tg), tg[:n2], font(F_MONO, 30), WHITE + (225,), 1)
        with_shadow(lay, blur=8, alpha=0.4).save(f"{d_dir}/{f:03d}.png")


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    scrim()
    hud()
    caption("hook", "01/07 — OLDIN · ДО", "Parda xonani qanday o‘zgartiradi?", "Как шторы меняют комнату?", 1, static=True)
    caption("keyin", "02/07 — KEYIN · ПОСЛЕ", "Shinam, yorug‘ va nafis", "Уютно, светло и элегантно", 2)
    caption("mato", "03/07 — MATO", "Tilla naqshli\npremium mato", "Премиальная ткань с золотым узором", 3)
    caption("tyul", "04/07 — QATLAMLAR", "Nafis tyul + qalin parda", "Лёгкий тюль + плотные шторы", 4)
    caption("karniz", "05/07 — KARNIZ", "Karniz bo‘ylab\nyengil suriladi", "Легко скользят по карнизу", 5)
    caption("shift", "06/07 — O‘LCHAM", "Shiftdan polgacha", "От потолка до пола", 6)
    caption("800", "07/07 — TANLOV", "800+ turdagi mato\nTurkiya va Xitoydan", "800+ видов тканей из Турции и Китая", 7)
    endcard()
    print("ok", ACC)
