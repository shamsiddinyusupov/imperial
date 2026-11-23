"""Line-art curtain for «Oddiy pardalardan charchadingizmi?» (Classic): warm orange-gold strokes draw a classic
curtain (rail, rings, two draped panels with tie-backs, swags); then the folds straighten into evenly spaced
vertical lines and the gaps open like turning lamellas onto the real footage (hook). Later the same curtain is
drawn again and its fabric drops off the rail («to wash it, take it all down»).
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

W, H = 1080, 1920
SS = 2
LINE = (246, 176, 112)
GLOW = (240, 150, 80)
RAIL_Y, TOP_Y, TIE_Y, BOT_Y = 288, 300, 860, 1270
NS = 90


def ease(u):
    u = np.clip(u, 0.0, 1.0)
    return u * u * (3 - 2 * u)


def bez(p0, p1, p2, p3, s):
    s = s[:, None]
    return ((1 - s) ** 3) * p0 + 3 * ((1 - s) ** 2) * s * p1 + 3 * (1 - s) * s * s * p2 + s ** 3 * p3


def _fold(u, i):
    xt, xm, xb = 120 + u * 410, 150 + u * 115, 108 + u * 300
    s = np.linspace(0, 1, NS // 2)
    up = bez(np.array([xt, TOP_Y]), np.array([xt, 520]), np.array([xm + (xt - xm) * 0.25, 700]),
             np.array([xm, TIE_Y]), s)
    lo = bez(np.array([xm, TIE_Y]), np.array([xm, 960]), np.array([xb, 1120]), np.array([xb, BOT_Y]), s)
    p = np.vstack([up, lo[1:]])
    k = np.linspace(0, 1, len(p))
    p[:, 0] += 5 * np.sin(k * np.pi * 3 + i * 1.7) * (1 - abs(2 * u - 1)) * np.sin(np.pi * k)
    return p


def _geom():
    folds, tops = [], []
    for side in (0, 1):
        for i in range(6):
            p = _fold(i / 5, i)
            if side:
                p = p.copy()
                p[:, 0] = W - p[:, 0]
            folds.append(p)
            tops.append(p[0].copy())
    # targets: 12 evenly spaced verticals; left panel -> left half, right panel mirrored
    xs = [(k + 0.5) * W / 12 for k in range(12)]
    targets = [xs[i] for i in range(6)] + [xs[11 - i] for i in range(6)]
    swags = []
    for x0, x1 in ((120, 540), (540, 960)):
        for dep, pad in ((95, 0), (70, 26), (46, 52)):
            v = np.linspace(0, 1, 60)
            swags.append(np.stack([x0 + pad + (x1 - x0 - 2 * pad) * v, TOP_Y + 4 + dep * np.sin(np.pi * v)], 1))
    ties, tass = [], []
    for side in (0, 1):
        a, b = 150 - 24, 265 + 24
        v = np.linspace(0, 1, 40)
        for off in (0, 15):
            p = np.stack([a + (b - a) * v, TIE_Y - 14 + off + 18 * np.sin(np.pi * v) + 12 * v], 1)
            if side:
                p[:, 0] = W - p[:, 0]
            ties.append(p)
        tx = b if not side else W - b
        tass.append((tx, TIE_Y + 13))
    return folds, tops, targets, swags, ties, tass


FOLDS, TOPS, TARGETS, SWAGS, TIES, TASS = _geom()


def _poly(d, p, frac, width, alpha, dy=0.0):
    if frac <= 0 or alpha <= 0.01:
        return
    n = max(2, int(round(len(p) * min(1.0, frac))))
    q = [(float(x) * SS, float(y + dy) * SS) for x, y in p[:n]]
    d.line(q, fill=LINE + (int(255 * alpha),), width=int(width * SS), joint="curve")


def curtain_layer(tl, speed=1.0, morph=0.0, drop_t=None, extras=1.0, line_alpha=1.0, rail_alpha=1.0):
    """tl: seconds since the drawing started. morph 0..1 straightens the folds; drop_t: seconds since the fabric
    started to fall (None = still on the rail). Returns an RGBA layer (W x H) with glow."""
    lay = Image.new("RGBA", (W * SS, H * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    tt = tl * speed
    dy, fa = 0.0, 1.0
    if drop_t is not None and drop_t > 0:
        dy = 0.5 * 2600 * drop_t ** 2 + 40 * drop_t
        fa = float(1 - ease(drop_t / 0.75))
    m = float(ease(morph))
    ra = rail_alpha * line_alpha
    # rail + finials
    fr = float(ease(tt / 0.4))
    if fr > 0 and ra > 0.01:
        x0, x1 = 90, 90 + (990 - 90) * fr
        d.line([(x0 * SS, RAIL_Y * SS), (x1 * SS, RAIL_Y * SS)], fill=LINE + (int(255 * ra),), width=5 * SS)
        for x in (90, 990):
            if x <= x1 + 1:
                d.ellipse([((x - 12) * SS, (RAIL_Y - 12) * SS), ((x + 12) * SS, (RAIL_Y + 12) * SS)],
                          outline=LINE + (int(255 * ra),), width=3 * SS)
    # rings
    ea = extras * fa * line_alpha
    for k, (x, y) in enumerate(TOPS):
        a = float(ease((tt - 0.3 - 0.015 * k) / 0.2)) * ea * (1 - m)
        if a > 0.01:
            d.ellipse([((x - 8) * SS, (RAIL_Y - 2 + dy) * SS), ((x + 8) * SS, (RAIL_Y + 14 + dy) * SS)],
                      outline=LINE + (int(255 * a),), width=2 * SS)
    # folds (with morph to straight verticals)
    for k, p in enumerate(FOLDS):
        i = k % 6
        fr = float(ease((tt - 0.35 - 0.05 * abs(i - 2.5)) / 0.95))
        if m > 0:
            # straight target: a full-height vertical at an even spacing
            st = np.stack([np.full(len(p), TARGETS[k]), np.linspace(-30, H + 30, len(p))], 1)
            q = (1 - m) * p + m * st
        else:
            q = p
        w = 3.0 if i in (0, 5) else 2.2
        _poly(d, q, fr, w, line_alpha * (fa if m == 0 else 1.0), dy if m == 0 else 0.0)
    # swags, tie-backs, tassels
    for k, p in enumerate(SWAGS):
        fr = float(ease((tt - 0.55 - 0.05 * (k % 3)) / 0.55))
        _poly(d, p, fr, 2.0, ea * (1 - m) * 0.85, dy)
    for k, p in enumerate(TIES):
        fr = float(ease((tt - 1.15) / 0.3))
        _poly(d, p, fr, 2.6, ea * (1 - m), dy)
    for (x, y) in TASS:
        a = float(ease((tt - 1.3) / 0.3)) * ea * (1 - m)
        if a > 0.01:
            c = LINE + (int(255 * a),)
            d.line([(x * SS, (y + dy) * SS), (x * SS, (y + 62 + dy) * SS)], fill=c, width=2 * SS)
            d.ellipse([((x - 9) * SS, (y + 62 + dy) * SS), ((x + 9) * SS, (y + 96 + dy) * SS)], outline=c,
                      width=2 * SS)
    lay = lay.reduce(SS)
    glow = lay.filter(ImageFilter.GaussianBlur(9))
    ga = np.asarray(glow).astype(np.float32)
    ga[..., :3] = GLOW
    ga[..., 3] *= 0.9
    out = Image.fromarray(np.clip(ga, 0, 255).astype(np.uint8))
    out.alpha_composite(lay)
    return out


_BG = None


def background():
    global _BG
    if _BG is None:
        y = np.linspace(0, 1, H)[:, None]
        x = np.linspace(-1, 1, W)[None, :]
        top, bot = np.array([44, 34, 27]), np.array([16, 12, 10])
        g = top * (1 - y[..., None]) + bot * y[..., None]
        r = np.sqrt(x ** 2 + ((y - 0.42) * 1.6) ** 2)
        g = g * (1.12 - 0.45 * np.clip(r, 0, 1.4)[..., None] / 1.4)
        g = g + np.array([22, 12, 4]) * np.exp(-((x * 1.1) ** 2 + ((y - 0.38) * 2.2) ** 2))[..., None]
        _BG = np.clip(g, 0, 255).astype(np.float32)
    return _BG


def grain(i):
    r = np.random.default_rng(1000 + i % 6)
    return r.normal(0, 3.0, (H, W, 1)).astype(np.float32)


def reveal_alpha(tr):
    """Overlay alpha (H x W, 0..1) while the 13 columns between the straightened lines open. tr: seconds since the
    opening started (<0: closed)."""
    xs = [0.0] + [(k + 0.5) * W / 12 for k in range(12)] + [float(W)]
    a = np.ones((H, W), np.float32)
    edges = np.zeros((H, W), np.float32)
    for c in range(13):
        x0, x1 = xs[c], xs[c + 1]
        e = float(ease((tr - 0.04 * abs(c - 6)) / 0.5))
        if e <= 0:
            continue
        cx, hw = (x0 + x1) / 2, (x1 - x0) / 2 * e
        l, r = int(round(cx - hw)), int(round(cx + hw))
        a[:, max(0, l):min(W, r)] = 0
        if e < 1:
            for xe in (l, r - 1):
                if 0 <= xe < W:
                    edges[:, max(0, xe - 1):min(W, xe + 2)] = 1 - e
    return a, edges
