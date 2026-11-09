"""Jalyuzi Classic text style «A — Quyosh» (owner chose 10.11.2026).
Poppins Bold headlines, accent line on an orange ribbon (ink text), Poppins Medium labels, Cyrillic falls back to Inter.
Drop-in replacement for the Imperial names used by the build scripts:
    from classic_style import GOLD, PAPER, INK, SER, SERI, SEMI, MED, MONO, text, check
"""
import re

from PIL import Image, ImageDraw, ImageFont

G = "/usr/share/fonts/truetype/google-fonts/"
IN = "/usr/share/fonts/opentype/inter/"
W = 1080
ORANGE, CORAL, GREEN = (240, 150, 80), (226, 96, 58), (160, 200, 70)
CREAM, INK = (250, 243, 232), (34, 26, 20)
GOLD, PAPER = ORANGE, CREAM
CYR = re.compile("[Ѐ-ӿ]")
_C = {}


def _mk(path, size, cyr, ribbon=False):
    k = (path, size, ribbon)
    if k not in _C:
        f = ImageFont.truetype(path, size)
        f._path, f._size, f._cyr, f._ribbon = path, size, cyr, ribbon
        _C[k] = f
    return _C[k]


def _resize(f, size):
    return _mk(f._path, size, f._cyr, f._ribbon)


SER = lambda s: _mk(G + "Poppins-Bold.ttf", int(s * 0.95), IN + "Inter-Bold.otf")
SERI = lambda s: _mk(G + "Poppins-Bold.ttf", int(s * 0.9), IN + "Inter-Bold.otf", ribbon=True)
SEMI = lambda s: _mk(G + "Poppins-Bold.ttf", int(s * 0.92), IN + "Inter-SemiBold.otf")
MED = lambda s: _mk(G + "Poppins-Medium.ttf", s, IN + "Inter-Medium.otf")
MONO = lambda s: _mk(G + "Poppins-Bold.ttf", int(s * 0.95), IN + "Inter-Bold.otf")


def _font_for(s, font):
    if getattr(font, "_cyr", None) and CYR.search(s):
        f = ImageFont.truetype(font._cyr, font.size)
        f._path, f._size, f._cyr, f._ribbon = font._cyr, font.size, None, font._ribbon
        return f
    return font


def text(img, xy, s, font, fill, alpha, rise=0, anchor="la", tracking=0):
    if alpha <= 0.01 or not s:
        return
    font = _font_for(s, font)
    x, y = xy
    y += rise * (1 - alpha)
    trk = tracking
    width = lambda f: (sum(f.getlength(c) for c in s) + trk * (len(s) - 1)) if trk else f.getlength(s)
    maxw = (W - 2 * 70) if anchor[0] == "m" else (W - x - 70)
    if hasattr(font, "_path") and width(font) > maxw:
        size = int(font.size * maxw / width(font))
        font = _mk(font._path, size, font._cyr, font._ribbon) if font._cyr else ImageFont.truetype(font._path, size)
        if not hasattr(font, "_ribbon"):
            font._ribbon = False
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    a = int(255 * alpha)
    ribbon = getattr(font, "_ribbon", False)
    col = INK if ribbon else fill
    if ribbon:
        l, t, r, b = d.textbbox((x, y), s, font=font, anchor=anchor)
        ph, pv = 0.18 * font.size, 0.14 * font.size
        d.rounded_rectangle((l - ph, t - pv, r + ph, b + pv), int(0.2 * font.size), fill=ORANGE + (a,))
    if trk:
        if anchor[0] == "m":
            x -= width(font) / 2
        for c in s:
            d.text((x, y), c, font=font, fill=col + (a,))
            x += font.getlength(c) + trk
    else:
        d.text((x, y), s, font=font, fill=col + (a,), anchor=anchor)
    img.alpha_composite(lay)


def check(img, x, y, al, s, sub):
    if al <= 0.01:
        return
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    r = 30
    d.ellipse((x, y, x + 2 * r, y + 2 * r), fill=ORANGE + (int(255 * al),))
    d.line([(x + 17, y + 31), (x + 27, y + 41), (x + 44, y + 21)], fill=INK + (int(255 * al),), width=6, joint="curve")
    img.alpha_composite(lay)
    text(img, (x + 84, y - 4), s, SEMI(54), CREAM, al, 14)
    text(img, (x + 86, y + 60), sub, MED(28), (225, 215, 200), al, 14)


ARROW = ImageFont.truetype(IN + "Inter-SemiBold.otf", 44)


def font_for(s, font):
    """Font that will actually draw s (Cyrillic -> Inter)."""
    return _font_for(s, font)
