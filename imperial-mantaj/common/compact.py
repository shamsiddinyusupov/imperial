"""Compact premium captions for Imperial Reels.

Left-aligned blocks: a thin gold hairline on the left, a small tracked gold label, one short serif line,
an optional italic line and a small Russian line. Each element fades in with a short slide from the left.
"""
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1080, 1920
FI = "/usr/share/fonts/opentype/inter/"
CX = "/usr/share/fonts/truetype/crosextra/"
CREAM, GOLD, DIM, INK = (246, 240, 228), (214, 178, 108), (206, 198, 184), (24, 22, 20)
X_RULE, X0, MAXW = 84, 112, 860
_F = {}


def F(name, size):
    k = (name, size)
    if k not in _F:
        _F[k] = ImageFont.truetype(name if name.startswith("/") else FI + name, size)
    return _F[k]


SER = lambda s: F(CX + "Caladea-Regular.ttf", s)
SERI = lambda s: F(CX + "Caladea-Italic.ttf", s)
MED = lambda s: F("Inter-Medium.otf", s)
SEMI = lambda s: F("Inter-SemiBold.otf", s)
REG = lambda s: F("Inter-Regular.otf", s)
RUF = lambda s: F("Inter-Italic.otf", s)
LIT = lambda s: F("Inter-LightItalic.otf", s)
KIND = {"label": (MED, 0.32), "head": (SER, 0.0), "sub": (SERI, 0.0), "ru": (RUF, 0.0), "big": (SER, 0.0)}
GAP = {"label": 1.9, "head": 1.16, "sub": 1.3, "ru": 1.6, "big": 1.0}


def ease(x):
    x = max(0.0, min(1.0, x))
    return 1 - (1 - x) ** 3


def alpha(layer, a):
    if a >= 1:
        return layer
    l2 = layer.copy()
    l2.putalpha(layer.getchannel("A").point(lambda v: int(v * max(0, a))))
    return l2


def shadow(L, b=12, a=0.55):
    sh = Image.new("RGBA", L.size, (0, 0, 0, 0))
    sh.putalpha(L.getchannel("A").filter(ImageFilter.GaussianBlur(b)).point(lambda v: int(v * a)))
    o = Image.new("RGBA", L.size, (0, 0, 0, 0))
    o.alpha_composite(sh, (0, 3))
    o.alpha_composite(L)
    return o


def tw(t, f, tr=0.0):
    return sum(f.getlength(c) + f.size * tr for c in t)


def tracked(d, xy, t, f, fill, tr):
    x, y = xy
    for c in t:
        d.text((x, y), c, font=f, fill=fill)
        x += f.getlength(c) + f.size * tr
    return x


def text_layer(text, kind, size, fill, x=X0, maxw=MAXW, center=False):
    fn, tr = KIND[kind]
    while tw(text, fn(size), tr) > maxw and size > 18:
        size -= 2
    f = fn(size)
    L = Image.new("RGBA", (W, int(size * 1.5) + 8), (0, 0, 0, 0))
    xx = (W - tw(text, f, tr)) / 2 if center else x
    tracked(ImageDraw.Draw(L), (xx, 2), text, f, fill, tr)
    return shadow(L), size


def block(y, items):
    """items: (text, kind, size, colour, appear_time). Returns [(layer, y, appear)] incl. the hairline."""
    out, yy, first = [], y, min(it[4] for it in items)
    for text, kind, size, col, at in items:
        lay, s = text_layer(text, kind, size, col)
        out.append((lay, yy, at))
        yy += int(s * GAP[kind])
    rule = Image.new("RGBA", (W, yy - y), (0, 0, 0, 0))
    ImageDraw.Draw(rule).line([(X_RULE, 6), (X_RULE, yy - y - 14)], fill=GOLD, width=2)
    out.insert(0, (rule, y, first))
    return out


def draw(L, items, t, t_out, fade=0.45, slide=14):
    """Composite block items at time t; everything fades out over the 0.25 s before t_out."""
    out = 1 - ease((t - (t_out - 0.25)) / 0.25) if t > t_out - 0.25 else 1
    for lay, y, at in items:
        p = (t - at) / fade
        if p <= 0:
            continue
        L.alpha_composite(alpha(lay, ease(p) * out), (-int(slide * (1 - ease(p))), y))


def grad_top(y1, amax):
    import numpy as np
    ys = np.arange(H, dtype=np.float32)
    a = np.clip(1 - ys / y1, 0, 1) ** 1.35 * amax
    img = np.zeros((H, W, 4), np.uint8)
    img[..., :3] = (10, 9, 8)
    img[..., 3] = (np.repeat(a[:, None], W, 1) * 255).astype(np.uint8)
    return Image.fromarray(img, "RGBA")


def calm_bed(path, total, sections, accents, end_t, sr=48000, music=True, seed=3, tone="piano", step=0.84):
    """Calm ambient bed: soft pad per section, sparse felt piano (or e-piano), long airy reverb, soft swishes.

    sections: [(start, end, [midi notes], root)], accents: times for soft swishes (cuts)."""
    import wave

    import numpy as np
    n = int(sr * (total + 2.0))
    Lc, Rc = np.zeros(n), np.zeros(n)
    rng = np.random.default_rng(seed)

    def add(sig, t0, gl=1.0, gr=1.0):
        i = int(t0 * sr)
        if i >= n or i < 0:
            return
        j = min(n, i + len(sig))
        Lc[i:j] += sig[: j - i] * gl
        Rc[i:j] += sig[: j - i] * gr

    tt = lambda d: np.arange(int(d * sr)) / sr
    note = lambda m: 440.0 * 2 ** ((m - 69) / 12)
    lp = lambda x, k: np.convolve(x, np.ones(k) / k, "same")
    x = lp(lp(rng.normal(0, 1, n), 60), 30)
    x /= np.abs(x).max()
    Lc += x * 0.007
    Rc += np.roll(x, 900) * 0.007

    def swish(t0, dur=0.4, v=0.022):
        t = tt(dur)
        nz = rng.normal(0, 1, len(t))
        add((lp(nz, 4) - lp(nz, 30)) * np.sin(np.pi * t / dur) ** 2 * v, t0, 0.9, 1.0)

    def key(m, dur, v):
        t = tt(dur)
        fr = note(m)
        if tone == "epiano":      # soft electric piano: sine + gentle bell partial + slow tremolo
            s = (np.sin(2 * np.pi * fr * t) + 0.18 * np.sin(2 * np.pi * fr * 3.01 * t) * np.exp(-t * 3)) * np.exp(-t * 0.9)
            s *= 1 + 0.12 * np.sin(2 * np.pi * 4.5 * t)
        else:                     # felt piano
            s = sum(np.sin(2 * np.pi * fr * k * t) * np.exp(-t * (0.7 + 1.1 * k)) / k ** 1.5 for k in range(1, 6))
            s = lp(s, 4)
        return s * np.minimum(1, t / 0.01) * np.minimum(1, (dur - t) / 0.4) * v

    def pad(ms, dur, v):
        t = tt(dur)
        s = sum(np.sin(2 * np.pi * note(m) * t + k) + 0.5 * np.sin(2 * np.pi * note(m) * 1.003 * t) for k, m in enumerate(ms))
        s = lp(s, 6)
        return s * np.minimum(1, t / 1.2) * np.minimum(1, (dur - t) / 1.2) / len(ms) * v

    for a in accents:
        swish(a - 0.08)
    if music:
        order = [0, 2, 1, 3]
        for si, (a, b, chd, root) in enumerate(sections):
            d = b - a
            add(pad([m - 12 for m in chd], d + 1.4, 0.05), max(0, a - 0.3))
            add(pad([root], d + 1.2, 0.03), max(0, a - 0.2))                 # soft low drone
            add(key(root + 12, 4.0, 0.07), a)
            for k in range(int(d / step)):
                if si == len(sections) - 1 and k > 3:
                    break
                add(key(chd[order[k % 4]] + 12, 2.6, 0.034 + 0.006 * (k % 2 == 0)), a + 0.1 + k * step,
                    1.0 - 0.2 * (k % 2), 0.8 + 0.2 * (k % 2))
    add(key(88, 3.0, 0.035), end_t + 0.4, 0.85, 1.0)
    m = int(total * sr)
    Lc, Rc = Lc[:m], Rc[:m]
    wl, wr = np.zeros(m), np.zeros(m)
    for dl, g in ((0.051, 0.32), (0.089, 0.27), (0.137, 0.22), (0.197, 0.17), (0.283, 0.12), (0.401, 0.08), (0.563, 0.05)):
        s_ = int(dl * sr)
        wl[s_:] += Rc[:-s_] * g
        wr[s_:] += Lc[:-s_] * g
    Lc += wl
    Rc += wr
    fv = np.minimum(1, (m - np.arange(m)) / (1.4 * sr)) * np.minimum(1, np.arange(m) / (0.08 * sr))
    Lc, Rc = Lc * fv, Rc * fv
    pk = max(np.abs(Lc).max(), np.abs(Rc).max())
    pcm = (np.stack([Lc, Rc], 1) / pk * 0.9 * 32767).astype(np.int16)
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(pcm.tobytes())
