"""«Bir deraza — to‘rt fasl» (IMPERIAL, owner 17.11; sister of the Classic «Bir deraza — bir kun»): one real window
(IMG_6041 frame 288 as a plate: cream PVC, taupe plisse on three panes, a downlight) lives through a whole year in 14 s.
Spring: the plisse rises, a blossoming branch and petals in the morning sun. Summer: high sun, the plisse comes half
down, green leaves. Autumn: golden low sun from the left, the plisse rises again, leaves fall. Winter: overcast, snow,
the plisse closes, the downlight warms the room. The real plisse texture is compressed/expanded for the moving sheets;
sky, sun, branch, leaves, snow and skyline are procedural (no AI). The last frame equals the plate -> real clip.
python3 room4.py [prev t,t,..|render]
"""
import json
import os
import sys
from multiprocessing import Pool

import cv2
import numpy as np

D = "/home/claude/reels/fasl"
W, H, FPS = 1080, 1920, 30
DUR = 14.0
P = json.load(open(f"{D}/polys.json"))
PLATE = cv2.cvtColor(cv2.imread(f"{D}/plate.png"), cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
LIN = PLATE ** 2.2
HZ = 1338
BB = (100, 325, 1080, 1380)


def ease(u):
    u = np.clip(u, 0, 1)
    return u * u * (3 - 2 * u)


def key(t, ks):
    ts = [k[0] for k in ks]
    if t <= ts[0]:
        return np.array(ks[0][1], np.float32)
    for (t0, v0), (t1, v1) in zip(ks, ks[1:]):
        if t <= t1:
            u = ease((t - t0) / max(1e-6, t1 - t0))
            return (np.array(v0, np.float32) * (1 - u) + np.array(v1, np.float32) * u).astype(np.float32)
    return np.array(ks[-1][1], np.float32)


def poly_mask(pts, blur=0):
    m = np.zeros((H, W), np.float32)
    cv2.fillPoly(m, [np.array(pts, np.int32)], 1.0, lineType=cv2.LINE_AA)
    if blur:
        m = cv2.GaussianBlur(m, (0, 0), blur)
    return m


RECT = {"transom": (294, 225), "left": (300, 676), "right": (510, 1036)}
RAIL = {"transom": 14, "left": 16, "right": 18}
PANES = {}
for k, (rw, rh) in RECT.items():
    src = np.float32([[0, 0], [rw, 0], [rw, rh], [0, rh]])
    Hm = cv2.getPerspectiveTransform(src, np.float32(P[k]))
    sheet = cv2.warpPerspective(LIN, np.linalg.inv(Hm), (rw, rh), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    PANES[k] = dict(H=Hm, sheet=sheet, mask=poly_mask(P[k]))
M_PANES = np.clip(sum(p["mask"] for p in PANES.values()), 0, 1)
M_SILL, M_SILLF = poly_mask(P["sill"], 1.0), poly_mask(P["sillf"], 1.0)
_er = cv2.erode(M_PANES, np.ones((3, 3), np.uint8), iterations=6)
GLASS_SH = 0.6 + 0.4 * np.clip(cv2.GaussianBlur(_er, (0, 0), 9) * 1.15, 0, 1)
YY, XX = np.mgrid[0:H, 0:W].astype(np.float32)
REFL = (np.clip(1 - (YY / 1920.0 + XX / 2400.0), 0, 1) ** 2)[..., None] * np.array([1.0, 0.96, 0.92], np.float32)
_yb = 1442 + XX * (1455 - 1442) / 1080
_yf = 1490 + XX * (1505 - 1490) / 1080
SILL_V = np.clip((YY - _yb) / np.maximum(1, _yf - _yb), 0, 1)
DLIGHT = (np.exp(-(((XX - 660) ** 2) + (YY - 92) ** 2) / 70.0 ** 2) * 1.2
          + np.exp(-(((XX - 700) ** 2) / 330.0 ** 2 + ((YY - 520) ** 2) / 420.0 ** 2)) * 0.55)[..., None] * \
    np.array([1.0, 0.78, 0.52], np.float32)

# ---- outside: skyline, branch, leaves, particles ----
_rng = np.random.default_rng(31)


def _layer(lo, hi, wlo, whi, gap):
    a = np.full(W, HZ + 5, np.float32)
    x = 90
    while x < W:
        w = int(_rng.integers(wlo, whi))
        h = HZ - _rng.integers(lo, hi)
        a[x:x + w] = np.minimum(a[x:x + w], h)
        x += w + int(_rng.integers(-6, gap))
    return a


SKY_FAR = np.minimum(_layer(20, 85, 12, 40, 8), _layer(8, 36, 20, 70, 12))
SKY_NEAR = _layer(2, 16, 30, 90, 26)

BRANCH = np.zeros((H, W), np.float32)
LEAVES = []                       # (x, y, size, angle, rank, variant)


def _grow(x, y, ang, ln, th, depth):
    if depth > 6 or ln < 16 or th < 0.8:
        return
    segs = max(2, int(ln / 18))
    for _ in range(segs):
        ang += _rng.normal(0, 0.16)
        nx, ny = x + np.cos(ang) * ln / segs, y + np.sin(ang) * ln / segs
        cv2.line(BRANCH, (int(x), int(y)), (int(nx), int(ny)), 1.0, max(1, int(round(th))), cv2.LINE_AA)
        if depth >= 1:
            for _k in range(int(_rng.integers(2, 6 + depth))):
                LEAVES.append((nx + _rng.normal(0, 26), ny + _rng.normal(0, 22), _rng.uniform(9, 20),
                               _rng.uniform(0, 180), _rng.random(), _rng.random()))
        x, y = nx, ny
        th *= 0.93
    for _ in range(int(_rng.integers(2, 4))):
        _grow(x, y, ang + _rng.uniform(-0.75, 0.75), ln * _rng.uniform(0.55, 0.78), th * 0.66, depth + 1)


_grow(1130, 400, np.pi + 0.10, 470, 26, 0)
_grow(1130, 620, np.pi - 0.20, 330, 18, 0)
_grow(1130, 860, np.pi - 0.30, 260, 13, 1)
_grow(980, 300, np.pi / 2 + 0.35, 280, 14, 1)
_grow(760, 300, np.pi / 2 + 0.15, 200, 10, 2)
_grow(560, 300, np.pi / 2 - 0.2, 160, 8, 2)
BRANCH = cv2.GaussianBlur(BRANCH, (0, 0), 1.0)
_sh = np.zeros_like(BRANCH)
_sh[4:] = BRANCH[:-4]
SNOWCAP = cv2.GaussianBlur(np.clip(BRANCH - _sh, 0, 1), (0, 0), 1.0)
LEAVES = np.array(LEAVES, np.float32)

PAL = {"spring": [(1.00, 0.80, 0.86), (0.98, 0.92, 0.94), (0.55, 0.78, 0.36)],
       "summer": [(0.16, 0.34, 0.09), (0.26, 0.48, 0.13), (0.20, 0.40, 0.12)],
       "autumn": [(0.95, 0.48, 0.10), (0.82, 0.28, 0.07), (0.98, 0.74, 0.22)]}
K_SEASON = [(0, (1, 0, 0)), (3.0, (1, 0, 0)), (3.9, (0, 1, 0)), (6.4, (0, 1, 0)), (7.3, (0, 0, 1)), (14, (0, 0, 1))]
K_FDENS = [(0, 0.72), (3.0, 0.78), (3.9, 1.0), (6.4, 1.0), (7.3, 0.85), (9.8, 0.30), (10.6, 0.0), (14, 0.0)]
K_FLUM = [(0, 0.95), (3.0, 0.95), (3.9, 0.72), (6.4, 0.72), (7.3, 0.85), (14, 0.85)]
_pr = np.random.default_rng(77)
PETALS = _pr.uniform(0, 1, (16, 5)).astype(np.float32)
FALL = _pr.uniform(0, 1, (26, 5)).astype(np.float32)
SNOW = _pr.uniform(0, 1, (340, 4)).astype(np.float32)

# ---- the year: keyframes ----
K_ZEN = [(0, (0.20, 0.36, 0.72)), (3.0, (0.20, 0.36, 0.72)), (3.9, (0.08, 0.28, 0.85)), (6.4, (0.08, 0.28, 0.85)),
         (7.3, (0.16, 0.24, 0.55)), (9.8, (0.16, 0.24, 0.55)), (10.7, (0.40, 0.45, 0.56)), (12.4, (0.28, 0.32, 0.44)),
         (13.6, (0.10, 0.12, 0.20)), (14, (0.10, 0.12, 0.20))]
K_HOR = [(0, (0.84, 0.88, 0.92)), (3.0, (0.84, 0.88, 0.92)), (3.9, (0.72, 0.84, 0.98)), (6.4, (0.72, 0.84, 0.98)),
         (7.3, (1.05, 0.70, 0.40)), (9.8, (1.05, 0.70, 0.40)), (10.7, (0.64, 0.67, 0.73)), (12.4, (0.48, 0.50, 0.58)),
         (13.6, (0.22, 0.22, 0.30)), (14, (0.22, 0.22, 0.30))]
K_SUN = [(0, (905, 660)), (3.0, (880, 520)), (3.9, (760, -350)), (6.4, (700, -350)), (7.3, (230, 1020)),
         (9.8, (250, 1160)), (10.6, (300, 1420)), (14, (300, 1420))]
K_SUNC = [(0, (1.0, 0.92, 0.80)), (3.0, (1.0, 0.92, 0.80)), (3.9, (1.0, 0.98, 0.92)), (6.4, (1.0, 0.98, 0.92)),
          (7.3, (1.0, 0.64, 0.30)), (14, (1.0, 0.60, 0.28))]
K_SUNI = [(0, 0.0), (0.5, 0.9), (3.0, 0.9), (3.9, 1.0), (9.8, 1.0), (10.6, 0.0), (14, 0.0)]
K_SIDE = [(0, 0.6), (3.0, 0.6), (3.9, 0.1), (6.4, 0.1), (7.3, -0.85), (14, -0.85)]
K_ELEV = [(0, 0.45), (3.0, 0.45), (3.9, 1.0), (6.4, 1.0), (7.3, 0.15), (14, 0.15)]
K_AMB = [(0, (0.50, 0.52, 0.60)), (1.6, (0.80, 0.80, 0.82)), (3.0, (0.90, 0.90, 0.90)), (3.9, (1.07, 1.05, 1.01)),
         (5.4, (0.95, 0.93, 0.90)), (6.4, (0.95, 0.93, 0.90)), (7.3, (0.92, 0.78, 0.60)), (9.8, (0.95, 0.80, 0.62)),
         (10.7, (0.64, 0.68, 0.78)), (11.6, (0.58, 0.62, 0.72)), (12.8, (0.30, 0.30, 0.37)), (14, (0.27, 0.27, 0.34))]
K_DL = [(0, 0.0), (12.0, 0.0), (12.7, 0.75), (14, 0.75)]
K_RAYS = [(0, 0.0), (1.2, 0.0), (2.2, 0.6), (3.0, 0.55), (3.9, 0.3), (6.4, 0.25), (7.3, 0.9), (9.8, 0.85), (10.6, 0.0)]
COV = {"transom": [(0, 1.0), (0.8, 1.0), (1.9, 0.06), (4.0, 0.06), (4.9, 1.0), (7.4, 1.0), (8.3, 0.06), (11.2, 0.06),
                   (12.2, 1.0)],
       "left": [(0, 1.0), (0.6, 1.0), (1.8, 0.05), (4.3, 0.05), (5.3, 0.55), (7.3, 0.55), (8.3, 0.05), (11.4, 0.05),
                (12.4, 1.0)],
       "right": [(0, 1.0), (1.0, 1.0), (2.3, 0.05), (4.5, 0.05), (5.5, 0.55), (7.5, 0.55), (8.5, 0.05), (11.7, 0.05),
                 (12.8, 1.0)]}
ZOOM = [(0, 1.06), (13.2, 1.0), (14, 1.0)]


def foliage(t):
    """branch + leaves + snow cap (premultiplied rgb, alpha), full frame, slightly out of focus"""
    w = key(t, K_SEASON)
    dens, flum = float(key(t, K_FDENS)), float(key(t, K_FLUM))
    winter = float(np.clip((t - 10.2) / 0.8, 0, 1))
    rgb = np.zeros((H, W, 3), np.float32)
    al = np.zeros((H, W), np.float32)
    bcol = np.array([0.075, 0.062, 0.05]) * (1 + 0.6 * winter)
    rgb += BRANCH[..., None] * bcol
    al = np.maximum(al, BRANCH)
    if dens > 0.01:
        lay = np.zeros((H, W, 3), np.float32)
        la = np.zeros((H, W), np.float32)
        for x, y, s, a, r, v in LEAVES:
            if r > dens:
                continue
            pi = min(2, int(v * 3))
            col = sum(np.array(PAL[n][pi]) * w[j] for j, n in enumerate(("spring", "summer", "autumn")))
            col = col * flum * (0.75 + 0.5 * ((v * 7.3) % 1))
            sz = s * (0.8 + 0.4 * w[1])
            cv2.ellipse(lay, (int(x), int(y)), (int(sz), int(sz * 0.62)), float(a), 0, 360, [float(v_) for v_ in col], -1, cv2.LINE_AA)
            cv2.ellipse(la, (int(x), int(y)), (int(sz), int(sz * 0.62)), float(a), 0, 360, 1.0, -1, cv2.LINE_AA)
        rgb = rgb * (1 - la[..., None]) + lay
        al = np.maximum(al, la)
    if winter > 0:
        rgb = rgb * (1 - SNOWCAP[..., None] * winter) + SNOWCAP[..., None] * winter * np.array([0.80, 0.83, 0.88])
    rgb = cv2.GaussianBlur(rgb, (0, 0), 3.0)
    al = cv2.GaussianBlur(al, (0, 0), 3.0)
    return rgb, al


def particles(t):
    lay = np.zeros((H, W, 3), np.float32)
    la = np.zeros((H, W), np.float32)
    # spring petals 0.4..3.6
    a_sp = float(np.clip((t - 0.4) / 0.6, 0, 1) * np.clip((3.8 - t) / 0.5, 0, 1))
    if a_sp > 0:
        for a, b, c, d, e in PETALS:
            x = 1080 - ((a * 900 + 70 * t * (0.6 + c)) % 1000)
            y = 330 + ((b * 1050 + 55 * t * (0.6 + d)) % 1050)
            sz = 3 + 4 * c
            cv2.ellipse(lay, (int(x), int(y)), (int(sz), int(sz * 0.55)), float(180 * e + 90 * t), 0, 360,
                        (float(a_sp), float(0.86 * a_sp), float(0.90 * a_sp)), -1, cv2.LINE_AA)
            cv2.ellipse(la, (int(x), int(y)), (int(sz), int(sz * 0.55)), float(180 * e + 90 * t), 0, 360, float(a_sp), -1,
                        cv2.LINE_AA)
    # autumn falling leaves 7.0..10.6
    a_au = float(np.clip((t - 7.0) / 0.6, 0, 1) * np.clip((10.8 - t) / 0.6, 0, 1))
    if a_au > 0:
        for a, b, c, d, e in FALL:
            sp = 70 + 90 * c
            y = 330 + ((b * 1100 + sp * t) % 1100)
            x = 140 + a * 920 + 35 * np.sin(1.4 * t + 6 * d)
            sz = 7 + 7 * c
            col = [float(v_) for v_ in np.array(PAL["autumn"][int(e * 2.99)]) * 0.9 * a_au]
            ang = float(60 * np.sin(2.0 * t + 5 * e) + 360 * d)
            cv2.ellipse(lay, (int(x), int(y)), (int(sz), int(sz * (0.35 + 0.3 * abs(np.sin(2.3 * t + 4 * d))))), ang,
                        0, 360, col, -1, cv2.LINE_AA)
            cv2.ellipse(la, (int(x), int(y)), (int(sz), int(sz * (0.35 + 0.3 * abs(np.sin(2.3 * t + 4 * d))))), ang,
                        0, 360, float(a_au), -1, cv2.LINE_AA)
    # winter snow 10.3..14
    a_sn = float(np.clip((t - 10.3) / 0.8, 0, 1))
    if a_sn > 0:
        for a, b, c, d in SNOW:
            sz = 1.2 + 3.8 * c ** 2
            sp = 60 + 140 * c
            y = 320 + ((b * 1080 + sp * t) % 1080)
            x = 100 + ((a * 990 + 25 * t + 18 * np.sin(0.9 * t + 7 * d)) % 990)
            v = float(a_sn * (0.55 + 0.45 * c))
            cv2.circle(lay, (int(x), int(y)), max(1, int(round(sz))), (0.93 * v, 0.95 * v, 1.0 * v), -1, cv2.LINE_AA)
            cv2.circle(la, (int(x), int(y)), max(1, int(round(sz))), v, -1, cv2.LINE_AA)
    lay = cv2.GaussianBlur(lay, (0, 0), 1.3)
    la = cv2.GaussianBlur(la, (0, 0), 1.3)
    return lay, la


def outside(t, sun, sunc, suni):
    x0, y0, x1, y1 = BB
    yy, xx = YY[y0:y1, x0:x1], XX[y0:y1, x0:x1]
    zen, hor = key(t, K_ZEN), key(t, K_HOR)
    e = np.clip((HZ - yy) / 1000.0, 0, 1) ** 0.55
    sky = hor * (1 - e[..., None]) + zen * e[..., None]
    d = np.sqrt((xx - sun[0]) ** 2 + (yy - sun[1]) ** 2)
    sky += sunc * suni * (0.55 * np.exp(-d / 60.0) + 0.16 * np.exp(-d / 260.0))[..., None]
    disc = np.clip((24 - d) / 2.5, 0, 1) * (yy < SKY_NEAR[x0:x1][None, :] - 1)
    sky += (sunc * 0.6 + 0.4) * 6.0 * suni * disc[..., None]
    dl = float(key(t, [(0, 0.85), (3.0, 0.85), (3.9, 1.0), (6.4, 1.0), (7.3, 0.55), (9.8, 0.55), (10.7, 0.6),
                       (13.6, 0.15), (14, 0.15)]))
    far_col = (hor * 0.32 + zen * 0.22) * (1 - dl) + np.array([0.58, 0.62, 0.70]) * dl * (0.6 + 0.4 * dl)
    near_col = (hor * 0.10 + zen * 0.07) * (1 - dl) + np.array([0.20, 0.21, 0.22]) * dl
    winter = float(np.clip((t - 10.3) / 0.8, 0, 1))
    far_col = far_col * (1 - 0.4 * winter) + np.array([0.62, 0.64, 0.68]) * 0.4 * winter * dl
    far = cv2.GaussianBlur((yy >= SKY_FAR[x0:x1][None, :]).astype(np.float32), (0, 0), 1.1)
    near = cv2.GaussianBlur((yy >= SKY_NEAR[x0:x1][None, :]).astype(np.float32), (0, 0), 0.8)
    sky = sky * (1 - far[..., None]) + far_col * far[..., None]
    sky = sky * (1 - near[..., None]) + near_col * near[..., None]
    out = np.zeros((H, W, 3), np.float32)
    out[y0:y1, x0:x1] = sky
    # winter haze (overcast) softens everything outside
    if winter > 0:
        out[y0:y1, x0:x1] = out[y0:y1, x0:x1] * (1 - 0.18 * winter) + hor * 0.18 * winter
    fr, fa = foliage(t)
    out = out * (1 - fa[..., None]) + fr
    pr, pa = particles(t)
    out = out * (1 - pa[..., None]) + pr
    return out


def sheets(t, back, front):
    rgb = np.zeros((H, W, 3), np.float32)
    al = np.zeros((H, W), np.float32)
    covs = {}
    for k, p in PANES.items():
        rw, rh = RECT[k]
        c = float(key(t, COV[k]))
        covs[k] = c
        rail = RAIL[k]
        body = p["sheet"][rail:]
        nh = max(8, int(round(c * (rh - rail))))
        sh = np.zeros((rh, rw, 3), np.float32)
        a = np.zeros((rh, rw), np.float32)
        sh[:rail] = p["sheet"][:rail]
        sh[rail:rail + nh] = cv2.resize(body, (rw, nh), interpolation=cv2.INTER_AREA)
        a[:rail + nh] = 1
        lum = sh.mean(axis=2, keepdims=True)
        sh = sh * front * 0.92 + lum * back[k] * 0.55
        w_rgb = cv2.warpPerspective(sh, p["H"], (W, H), flags=cv2.INTER_LINEAR)
        w_a = cv2.warpPerspective(a, p["H"], (W, H), flags=cv2.INTER_LINEAR)
        rgb += w_rgb * w_a[..., None]
        al = np.maximum(al, w_a)
    return rgb, al, covs


def god_rays(src, sun, n=30):
    q = 4
    s = cv2.resize(src, (W // q, H // q), interpolation=cv2.INTER_AREA)
    cx, cy = sun[0] / q, sun[1] / q
    gy, gx = np.mgrid[0:H // q, 0:W // q].astype(np.float32)
    acc = np.zeros_like(s)
    wsum = 0.0
    for i in range(n):
        k = 1.0 - 0.55 * i / (n - 1)
        mx = (cx + (gx - cx) * k).astype(np.float32)
        my = (cy + (gy - cy) * k).astype(np.float32)
        wgt = 1.0 - 0.6 * i / n
        acc += cv2.remap(s, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT) * wgt
        wsum += wgt
    return cv2.resize(acc / wsum, (W, H), interpolation=cv2.INTER_LINEAR)


_DUST = np.random.default_rng(5).uniform(0, 1, (80, 4)).astype(np.float32)


def dust(t, rays):
    img = np.zeros((H, W), np.float32)
    for a, b, c, d in _DUST:
        x = 100 + a * 960 + 40 * np.sin(0.23 * t + 6 * c)
        y = 380 + b * 1150 + 28 * np.sin(0.17 * t + 6 * d) - 9 * t
        tw = 0.6 + 0.4 * np.sin(1.3 * t + 9 * d)
        xi, yi = int(x), int(y)
        if 3 <= xi < W - 3 and 3 <= yi < H - 3:
            cv2.circle(img, (xi, yi), max(1, int(1.2 + 2.2 * c)), float(tw), -1, cv2.LINE_AA)
    return cv2.GaussianBlur(img, (0, 0), 1.2) * np.clip(rays.mean(axis=2) * 3.0, 0, 1.5)


def tone(x):
    s = 0.78
    return np.where(x < s, x, s + (1 - s) * (1 - np.exp(-(x - s) / (1 - s))))


def frame(i):
    t = i / FPS
    sun = key(t, K_SUN)
    sunc, suni = key(t, K_SUNC), float(key(t, K_SUNI))
    side, elev = float(key(t, K_SIDE)), float(key(t, K_ELEV))
    amb, dlt, rays_k = key(t, K_AMB), float(key(t, K_DL)), float(key(t, K_RAYS))
    out_sky = outside(t, sun, sunc, suni)
    back = {}
    for k, p in PANES.items():
        m = p["mask"]
        back[k] = np.clip((out_sky * m[..., None]).sum((0, 1)) / max(1, m.sum()) * 0.9, 0, 3)
    front = amb + dlt * np.array([1.0, 0.78, 0.52], np.float32) * 0.35
    sh_rgb, sh_a, covs = sheets(t, back, front)
    glass = out_sky * GLASS_SH[..., None] + REFL * (0.03 + 0.04 * float(np.mean(amb)))
    win = glass * (1 - sh_a[..., None]) + sh_rgb
    img = LIN * amb + LIN * DLIGHT * dlt
    img += DLIGHT * dlt * 0.10
    # sunlight on the sill: pane columns shifted by the slant
    slant = 160 * side * (1 - 0.6 * elev)
    xg = XX + slant * SILL_V
    inL = ease((xg - 110) / 6) * ease((402 - xg) / 6)
    inR = ease((xg - 576) / 6) * ease((1080 - xg) / 6)
    tL = 1.0 if covs["left"] < 0.97 else 0.15
    tR = 1.0 if covs["right"] < 0.97 else 0.15
    vmin = 0.30 * (1 - elev) + 0.04
    sl = (inL * tL + inR * tR) * ease((SILL_V - vmin) / 0.08) * M_SILL * suni * (0.30 + 0.70 * elev)
    sl = cv2.GaussianBlur(sl, (0, 0), 2.0)
    img += LIN * sunc * sl[..., None] * 1.6
    img += LIN * sunc * (cv2.GaussianBlur(sl, (0, 0), 6) * M_SILLF * 0.22)[..., None]
    img = img * (1 - M_PANES[..., None]) + win * M_PANES[..., None]
    if rays_k > 0.01 and suni > 0.01:
        lum = win.mean(axis=2) * M_PANES * (1 - sh_a)
        src = np.clip(lum - 0.45, 0, 6)[..., None] * sunc
        rays = god_rays(src, sun) * rays_k * suni
        img += rays * 1.0
        img += (dust(t, rays) * 0.5)[..., None] * sunc * rays_k
    out = tone(np.clip(img, 0, None)) ** (1 / 2.2)
    z = float(key(t, ZOOM))
    if z > 1.0005:
        M = cv2.getRotationMatrix2D((600, 860), 0, z)
        out = cv2.warpAffine(out, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    g = np.random.default_rng(i).normal(0, 0.008, (H // 2, W // 2)).astype(np.float32)
    out = out + cv2.resize(g, (W, H))[..., None]
    return (np.clip(out, 0, 1) * 255).astype(np.uint8)


def render():
    os.makedirs(f"{D}/fr", exist_ok=True)
    n = int(round(DUR * FPS))
    with Pool(2) as p:
        for k in range(0, n, 12):
            ch = list(range(k, min(n, k + 12)))
            for i, a in zip(ch, p.map(frame, ch)):
                cv2.imwrite(f"{D}/fr/{i:04d}.jpg", cv2.cvtColor(a, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 96])
    os.system(f"ffmpeg -nostdin -v error -y -framerate 30 -i {D}/fr/%04d.jpg -c:v libx264 -preset fast -crf 14 "
              f"-pix_fmt yuv420p {D}/anim.mp4")


if __name__ == "__main__":
    if sys.argv[1] == "prev":
        ts = [float(v) for v in sys.argv[2].split(",")]
        with Pool(2) as p:
            ims = p.map(frame, [int(round(v * FPS)) for v in ts])
        c = np.full((640, 365 * len(ims), 3), 255, np.uint8)
        for k, a in enumerate(ims):
            c[:, k * 365:k * 365 + 360] = cv2.resize(a, (360, 640), interpolation=cv2.INTER_AREA)
        cv2.imwrite(f"{D}/prev_room.jpg", cv2.cvtColor(c, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 88])
    else:
        render()
