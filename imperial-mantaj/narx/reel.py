"""NARX launch reel (1080x1920, 30 fps, ~14.2 s).

Timeline (base video built by reel.sh):
  K1 0.000–2.600 | K2 2.300–5.300 | K3 5.000–7.200 | K4 6.900–9.167 (smoothleft 0.3 s)
  END card (blurred freeze) 8.867–14.167 (fade 0.3 s)
This script renders the full-length RGBA overlay sequence + the UI sound effects.
"""
import math
import os
import sys
import wave

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H, FPS = 1080, 1920, 30
T_K2, T_K4, T_END = 2.3, 6.9, 8.867
TOTAL = 14.167
NF = math.ceil(TOTAL * FPS)
OUT = sys.argv[1] if len(sys.argv) > 1 else "/home/claude/reels/narx/ov"
os.makedirs(OUT, exist_ok=True)

FI = "/usr/share/fonts/opentype/inter/"
MONO_B = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
F = {}


def font(name, size):
    k = (name, size)
    if k not in F:
        F[k] = ImageFont.truetype(name if name.startswith("/") else FI + name, size)
    return F[k]


SEMI = lambda s: font("InterDisplay-SemiBold.otf", s)
MED = lambda s: font("InterDisplay-Medium.otf", s)
REG = lambda s: font("Inter-Regular.otf", s)
BMED = lambda s: font("Inter-Medium.otf", s)
BSEMI = lambda s: font("Inter-SemiBold.otf", s)
MONO = lambda s: font(MONO_B, s)

PAPER = (245, 241, 233)
GOLD = (214, 176, 98)
INK = (30, 28, 25)
CARD = (20, 18, 16)


def ease(x):
    x = max(0.0, min(1.0, x))
    return 1 - (1 - x) ** 3


def tracked(d, xy, text, f, fill, track=0.12):
    x, y = xy
    for ch in text:
        d.text((x, y), ch, font=f, fill=fill)
        x += f.getlength(ch) + f.size * track
    return x


def shadowed(layer, blur=10, alpha=0.55):
    a = layer.getchannel("A").filter(ImageFilter.GaussianBlur(blur))
    sh = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    sh.putalpha(a.point(lambda v: int(v * alpha)))
    out = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    out.alpha_composite(sh, (0, 6))
    out.alpha_composite(layer)
    return out


def with_alpha(layer, a):
    if a >= 1:
        return layer
    l2 = layer.copy()
    l2.putalpha(layer.getchannel("A").point(lambda v: int(v * a)))
    return l2


# ---------------------------------------------------------------- static layers
def scrim(top=560, strength=0.76):
    a = np.zeros((H, W), np.float32)
    ys = np.arange(H)
    ramp = np.clip((ys - top) / 640.0, 0, 1) ** 1.15 * strength
    a[:] = ramp[:, None]
    img = np.zeros((H, W, 4), np.uint8)
    img[..., :3] = (10, 9, 8)
    img[..., 3] = (a * 255).astype(np.uint8)
    return Image.fromarray(img, "RGBA")


SCRIM = scrim()


def hook_layer():
    L = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(L)
    tracked(d, (84, 1100), "PLISSE JALYUZI  ·  1 m²", MONO(30), GOLD, 0.14)
    d.text((78, 1146), "100 000", font=SEMI(200), fill=PAPER)
    d.text((86, 1372), "so‘mdan", font=MED(86), fill=PAPER)
    d.text((86, 1486), "Плиссе — от 100 000 сум за м²", font=REG(34), fill=(225, 219, 208))
    # chip
    t = "4 xil mato  ·  o‘lchov bepul"
    f = BSEMI(34)
    w = f.getlength(t)
    d.rounded_rectangle((84, 1560, 84 + w + 56, 1632), 36, fill=GOLD)
    d.text((112, 1574), t, font=f, fill=INK)
    return shadowed(L)


FABS = [("SHAFFOF", "Screen", "100 000", 4), ("YARIM SHAFFOF", "Lezbon", "130 000", 3),
        ("DIMOUT", "Roma", "170 000", 2), ("BLACKOUT", "Blackout", "200 000", 1)]
CHIP_T = [2.62, 3.32, 4.02, 4.72]   # appear times
CHIP_Y0 = 1010


def chips_head():
    L = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(L)
    d.text((84, 846), "Matoni tanlang", font=SEMI(84), fill=PAPER)
    d.text((88, 948), "qalinligiga qarab  ·  so‘m / m²", font=BMED(36), fill=(236, 230, 219))
    return shadowed(L)


def chip(i):
    lv, name, price, light = FABS[i]
    L = Image.new("RGBA", (W, 136), (0, 0, 0, 0))
    d = ImageDraw.Draw(L)
    d.rounded_rectangle((84, 6, W - 84, 126), 28, fill=CARD + (205,))
    tracked(d, (120, 24), lv, MONO(25), GOLD, 0.12)
    x = 120
    for k in range(4):
        d.rounded_rectangle((x, 86, x + 10, 108), 3, fill=GOLD if k < light else (90, 84, 76))
        x += 16
    d.text((206, 64), name, font=BSEMI(44), fill=PAPER)
    pf = SEMI(64)
    d.text((W - 120 - pf.getlength(price), 28), price, font=pf, fill=PAPER)
    return L


CHIPS = [chip(i) for i in range(4)]
HEAD = chips_head()


def free_layer():
    L = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(L)
    tracked(d, (84, 1170), "TOSHKENT BO‘YLAB", MONO(30), GOLD, 0.14)
    d.text((80, 1216), "O‘lchov, yetkazish", font=SEMI(92), fill=PAPER)
    d.text((80, 1320), "va o‘rnatish — bepul", font=SEMI(92), fill=PAPER)
    d.text((86, 1446), "Замер, доставка и установка — бесплатно", font=REG(34), fill=(225, 219, 208))
    return shadowed(L)


HOOK = hook_layer()
FREE = free_layer()

# ---------------------------------------------------------------- CTA (end card) — animated
CTA_TYPE = [0.62, 0.80, 0.98, 1.16]   # letter times (s after T_END)
CTA_SEND = 1.55
CTA_REPLY = 1.85
CTA_DM = 2.55
CTA_FOOT = 3.0


def cta_frame(t):
    L = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(L)
    a0 = ease(t / 0.35)
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dl = ImageDraw.Draw(lay)
    tracked(dl, (84, 330), "NARXLAR DIREKTDA", MONO(32), GOLD, 0.14)
    y = 384
    for ln in ["Izohga", "NARX deb", "yozing"]:
        dl.text((76, y), ln, font=SEMI(150), fill=PAPER)
        y += 160
    dl.text((86, 884), "Hamma matolar narxi — darhol direktga", font=REG(36), fill=(214, 206, 192))
    L.alpha_composite(with_alpha(lay, a0))
    # comment field
    fy = 990
    fa = ease((t - 0.25) / 0.3)
    if fa > 0:
        fl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        fd = ImageDraw.Draw(fl)
        fd.rounded_rectangle((84, fy, W - 84, fy + 132), 66, fill=(255, 255, 255, 255))
        fd.ellipse((110, fy + 26, 190, fy + 106), fill=(226, 216, 197))
        fd.ellipse((136, fy + 42, 164, fy + 70), fill=(176, 160, 132))
        fd.pieslice((122, fy + 68, 178, fy + 124), 180, 360, fill=(176, 160, 132))
        n = sum(1 for tt in CTA_TYPE if t >= tt)
        txt = "NARX"[:n]
        tf = BSEMI(56)
        if txt:
            fd.text((216, fy + 34), txt, font=tf, fill=INK)
        else:
            fd.text((216, fy + 38), "Izoh qoldiring…", font=REG(44), fill=(160, 152, 140))
        if t < CTA_SEND and (int(t * 2.4) % 2 == 0):
            cx = 216 + (tf.getlength(txt) + 6 if txt else 0)
            fd.rectangle((cx, fy + 34, cx + 5, fy + 98), fill=(176, 138, 62))
        # send button (pressed at CTA_SEND)
        pr = 1.0 - 0.12 * max(0.0, 1 - abs(t - CTA_SEND) / 0.12)
        bx, by = W - 84 - 74, fy + 66
        r = 46 * pr
        fd.ellipse((bx - r, by - r, bx + r, by + r), fill=(214, 176, 98) if n == 4 else (222, 214, 200))
        s = 20 * pr
        fd.polygon([(bx - s * .8, by - s), (bx + s, by), (bx - s * .8, by + s), (bx - s * .4, by)], fill=INK)
        L.alpha_composite(with_alpha(fl, fa))
    # bot reply under the comment
    ra = ease((t - CTA_REPLY) / 0.3)
    if ra > 0:
        rl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        rd = ImageDraw.Draw(rl)
        oy = int(30 * (1 - ra))
        bx0, by0 = 250, fy + 168 + oy
        rd.rounded_rectangle((bx0, by0, W - 84, by0 + 128), 36, fill=(44, 40, 35, 240))
        px, py = bx0 + 36, by0 + 40
        rd.polygon([(px, py + 24), (px + 50, py), (px + 34, py + 52), (px + 25, py + 33)], fill=GOLD)
        rd.text((bx0 + 112, by0 + 22), "imperial_jalyuzi_uz", font=BSEMI(30), fill=GOLD)
        rd.text((bx0 + 112, by0 + 64), "Narxlarni direktga yubordik", font=REG(36), fill=(238, 233, 224))
        L.alpha_composite(with_alpha(rl, ra))
    # DM notification card
    da = ease((t - CTA_DM) / 0.35)
    if da > 0:
        nl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        nd = ImageDraw.Draw(nl)
        oy = int(-40 * (1 - da))
        x0, y0 = 84, 1366 + oy
        nd.rounded_rectangle((x0, y0, W - 84, y0 + 168), 34, fill=(255, 255, 255, 250))
        nd.rounded_rectangle((x0 + 28, y0 + 30, x0 + 108, y0 + 110), 22, fill=INK)
        nd.text((x0 + 44, y0 + 44), "IJ", font=SEMI(44), fill=GOLD)
        nd.text((x0 + 134, y0 + 26), "Direkt  ·  hozir", font=BMED(28), fill=(120, 112, 100))
        nd.text((x0 + 134, y0 + 64), "Plisse: 100 000 – 200 000 so‘m/m²", font=BSEMI(36), fill=INK)
        nd.text((x0 + 134, y0 + 110), "Bepul o‘lchovga yozilish →", font=REG(32), fill=(176, 138, 62))
        L.alpha_composite(with_alpha(nl, da))
    fa2 = ease((t - CTA_FOOT) / 0.4)
    if fa2 > 0:
        fl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        fd = ImageDraw.Draw(fl)
        fd.text((86, 1580), "Напишите «NARX» в комментариях", font=REG(34), fill=(200, 192, 178))
        L.alpha_composite(with_alpha(fl, fa2))
    return shadowed(L, blur=12, alpha=0.5)


# ---------------------------------------------------------------- frame composer
def overlay(t):
    L = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if t < T_END:
        L.alpha_composite(SCRIM)
    if t < T_K2 + 0.15:                                  # hook: static from frame 0
        a = 1 - ease((t - T_K2) / 0.15) if t > T_K2 else 1
        L.alpha_composite(with_alpha(HOOK, a))
    elif t < T_K4 + 0.1:                                  # fabrics
        out = 1 - ease((t - T_K4) / 0.1) if t > T_K4 else 1
        ha = ease((t - (T_K2 + 0.12)) / 0.25) * out
        L.alpha_composite(with_alpha(HEAD, ha))
        for i, ct in enumerate(CHIP_T):
            p = ease((t - ct) / 0.28)
            if p <= 0:
                continue
            c = with_alpha(CHIPS[i], p * out)
            L.alpha_composite(c, (int(-70 * (1 - p)), CHIP_Y0 + i * 142))
    elif t < T_END + 0.05:                                # free measuring
        a = ease((t - (T_K4 + 0.15)) / 0.25)
        a *= 1 - ease((t - (T_END - 0.15)) / 0.2)
        L.alpha_composite(with_alpha(FREE, a))
    if t >= T_END:
        L.alpha_composite(cta_frame(t - T_END))
    return L


def sfx(path):
    sr = 48000
    out = np.zeros(int(sr * TOTAL) + sr)

    def tone(t0, f, d, a, shape="sine", f2=None):
        n = int(sr * d)
        tt = np.arange(n) / sr
        fr = f if f2 is None else np.linspace(f, f2, n)
        ph = 2 * np.pi * np.cumsum(fr) / sr
        w = np.sin(ph) if shape == "sine" else np.sign(np.sin(ph)) * 0.5
        env = np.minimum(1, tt / 0.004) * np.exp(-tt / (d * 0.4))
        i0 = int(sr * t0)
        out[i0:i0 + n] += a * w * env

    for i, ct in enumerate(CHIP_T):               # chip ticks
        tone(ct, 1250 + i * 120, 0.06, 0.16)
    for tt in CTA_TYPE:                           # typing
        tone(T_END + tt, 2600, 0.014, 0.07, "square")
    tone(T_END + CTA_SEND, 500, 0.18, 0.22, f2=1400)   # send swoosh
    tone(T_END + CTA_REPLY, 1320, 0.08, 0.2)          # reply pop
    tone(T_END + CTA_REPLY + 0.07, 1760, 0.12, 0.2)
    tone(T_END + CTA_DM, 1046, 0.16, 0.2)             # DM ding (two-tone)
    tone(T_END + CTA_DM + 0.12, 1568, 0.3, 0.18)
    out = np.clip(out, -0.95, 0.95)
    pcm = (out * 32767).astype(np.int16)
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(np.repeat(pcm[:, None], 2, axis=1).tobytes())


if __name__ == "__main__":
    only = sys.argv[2] if len(sys.argv) > 2 else None
    if only:   # preview single times: comma list of seconds
        for s in only.split(","):
            overlay(float(s)).save(f"{OUT}/prev_{s}.png")
        sys.exit()
    sfx("/home/claude/reels/narx/sfx.wav")
    for fr in range(NF):
        overlay(fr / FPS).save(f"{OUT}/{fr:04d}.png", compress_level=1)
    print("frames", NF)
