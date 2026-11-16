"""«Bir deraza — bir kun» (JALYUZI CLASSIC, owner 17.11): one real window (IMG_5680 wide frame used as a plate) lives
through a whole day in 14 s. Pre-dawn blue -> the beige plisse rises sash by sash, the sun comes up in the glass, rays
and dust, the left reveal and the sill catch gold -> timelapse to noon, the plisse comes half down, light softens ->
timelapse to sunset, the sun goes down on the left, the plisse closes over it, a warm lamp comes on.
The real plisse texture of the plate is compressed/expanded for the moving sheets; the sky, sun, skyline and light are
procedural; the last frame equals the plate, so it dissolves into the real clip.
python3 room.py [prev t,t,..|render]
"""
import json
import os
import sys
from multiprocessing import Pool

import cv2
import numpy as np

D = "/home/claude/reels/xtong"
W, H, FPS = 1080, 1920, 30
DUR = 14.0
P = json.load(open(f"{D}/polys.json"))
PLATE = cv2.cvtColor(cv2.imread(f"{D}/plate.png"), cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
LIN = PLATE ** 2.2
HZ = 1470                                              # horizon (screen y) behind the glass
BB = (190, 425, 1050, 1490)                            # bbox of the window panes (x0, y0, x1, y1)


def ease(u):
    u = np.clip(u, 0, 1)
    return u * u * (3 - 2 * u)


def key(t, ks):
    """piecewise smooth interpolation of tuples/numbers over [(t, value), ...]"""
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


# ---- panes: homographies rect <-> screen, the real closed sheets in rect space ----
RECT = {"transom": (810, 232), "left": (310, 658), "right": (420, 750)}
RAIL = {"transom": 12, "left": 16, "right": 16}
PANES = {}
for k, (rw, rh) in RECT.items():
    src = np.float32([[0, 0], [rw, 0], [rw, rh], [0, rh]])
    dst = np.float32(P[k])
    Hm = cv2.getPerspectiveTransform(src, dst)
    sheet = cv2.warpPerspective(LIN, np.linalg.inv(Hm), (rw, rh), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    PANES[k] = dict(H=Hm, sheet=sheet, mask=poly_mask(P[k]))
M_REVL, M_REVR = poly_mask(P["revl"], 1.2), poly_mask(P["revr"], 1.2)
M_SILL, M_SILLF = poly_mask(P["sill"], 1.0), poly_mask(P["sillf"], 1.0)
M_PANES = np.clip(sum(p["mask"] for p in PANES.values()), 0, 1)
_er = cv2.erode(M_PANES, np.ones((3, 3), np.uint8), iterations=6)
GLASS_SH = 0.55 + 0.45 * np.clip(cv2.GaussianBlur(_er, (0, 0), 9) * 1.15, 0, 1)
REFL = (np.clip(1 - (np.mgrid[0:1920, 0:1080][0] / 1920.0 + np.mgrid[0:1920, 0:1080][1] / 2400.0), 0, 1) ** 2)[..., None]
REFL = (REFL * np.array([1.0, 0.95, 0.9])).astype(np.float32)

YY, XX = np.mgrid[0:H, 0:W].astype(np.float32)
# sill coordinates: v = depth (0 at the frame, 1 at the front edge)
_yb = 1518 + (XX - 165) * (1506 - 1518) / (1080 - 165)
_yf = 1585 + (XX - 25) * (1617 - 1585) / (1080 - 25)
SILL_V = np.clip((YY - _yb) / np.maximum(1, _yf - _yb), 0, 1)
# left reveal: v = 0 at the wall corner, 1 at the window frame
_xl0 = 90 + (YY - 405) * (100 - 90) / (1565 - 405)
_xl1 = 163 + (YY - 462) * (170 - 163) / (1515 - 462)
REVL_V = np.clip((XX - _xl0) / np.maximum(1, _xl1 - _xl0), 0, 1)
REVR_V = np.clip((1080 - XX) / 40.0, 0, 1)
_bars = ((YY > 525) & ~((YY > 705) & (YY < 790))).astype(np.float32) * 0.85 + 0.15 * (YY > 525)
REV_BARS = cv2.GaussianBlur(_bars, (0, 0), 14)
LAMP = np.exp(-(((XX + 100) ** 2 + (YY - 1700) ** 2) / 950.0 ** 2))[..., None] * np.array([1.0, 0.64, 0.36], np.float32)

# skyline (static silhouettes inside the pane bbox, screen space): many narrow blocks, two depths
_rng = np.random.default_rng(21)


def _layer(lo, hi, wlo, whi, gap):
    a = np.full(W, HZ + 5, np.float32)
    x = 150
    while x < W:
        w = int(_rng.integers(wlo, whi))
        h = HZ - _rng.integers(lo, hi)
        a[x:x + w] = np.minimum(a[x:x + w], h)
        if _rng.random() < 0.18:                                   # a thin roof antenna now and then
            a[x + w // 2:x + w // 2 + 2] = h - _rng.integers(6, 16)
        x += w + int(_rng.integers(-6, gap))
    return a


SKY_FAR = np.minimum(_layer(18, 62, 10, 34, 8), _layer(8, 30, 20, 60, 12))
SKY_NEAR = _layer(4, 26, 26, 80, 30)
_cl = cv2.resize(np.random.default_rng(8).random((14, 6)).astype(np.float32), (W, H), interpolation=cv2.INTER_CUBIC)
_cl2 = cv2.resize(np.random.default_rng(9).random((60, 10)).astype(np.float32), (W, H), interpolation=cv2.INTER_CUBIC)
CLOUD = np.clip((_cl * 0.65 + _cl2 * 0.35 - 0.52) * 3.2, 0, 1) * np.clip((HZ - 60 - YY) / 300.0, 0, 1)
CLOUD = cv2.GaussianBlur(CLOUD, (0, 0), 3)
_wr = np.random.default_rng(12)
WINS = np.zeros((H, W), np.float32)
for _ in range(260):
    wx, wy = int(_wr.integers(190, 1050)), int(_wr.integers(HZ - 45, HZ))
    WINS[wy:wy + 2, wx:wx + 2] = _wr.uniform(0.4, 1.0)
TOWER = np.zeros((H, W), np.float32)          # TV tower silhouette (thin mast, pod, splayed legs)
cv2.line(TOWER, (905, HZ), (905, 1250), 1.0, 2, cv2.LINE_AA)
cv2.line(TOWER, (905, 1250), (905, 1205), 1.0, 1, cv2.LINE_AA)
cv2.ellipse(TOWER, (905, 1290), (6, 4), 0, 0, 360, 1.0, -1, cv2.LINE_AA)
for dx in (-14, 14, -6, 6):
    cv2.line(TOWER, (905, 1385), (905 + dx, HZ), 1.0, 1, cv2.LINE_AA)
TOWER = cv2.GaussianBlur(TOWER, (0, 0), 0.6)

# ---- the day: keyframes ----
K_ZEN = [(0, (0.010, 0.014, 0.05)), (2.2, (0.03, 0.05, 0.16)), (3.6, (0.12, 0.22, 0.50)), (6.2, (0.15, 0.34, 0.80)),
         (8.0, (0.22, 0.46, 0.92)), (9.8, (0.22, 0.46, 0.92)), (11.0, (0.20, 0.25, 0.55)), (12.0, (0.07, 0.07, 0.22)),
         (13.2, (0.012, 0.016, 0.06)), (14, (0.012, 0.016, 0.06))]
K_HOR = [(0, (0.05, 0.04, 0.10)), (2.2, (0.55, 0.26, 0.22)), (3.6, (1.10, 0.62, 0.36)), (6.2, (0.85, 0.80, 0.76)),
         (8.0, (0.82, 0.90, 1.00)), (9.8, (0.82, 0.90, 1.00)), (11.0, (1.15, 0.55, 0.28)), (12.0, (0.85, 0.30, 0.25)),
         (13.2, (0.10, 0.06, 0.12)), (14, (0.08, 0.05, 0.10))]
K_SUN = [(0, (905, 1600)), (2.9, (905, 1520)), (6.5, (805, 990)), (8.0, (600, -420)), (9.8, (280, -380)),
         (11.6, (330, 1250)), (12.5, (345, 1540)), (14, (345, 1600))]
K_SUNC = [(0, (1.0, 0.45, 0.20)), (3.6, (1.0, 0.60, 0.30)), (6.5, (1.0, 0.88, 0.70)), (8.0, (1.0, 0.97, 0.90)),
          (9.8, (1.0, 0.95, 0.86)), (11.0, (1.0, 0.62, 0.30)), (12.2, (1.0, 0.40, 0.20)), (14, (1.0, 0.40, 0.20))]
K_SUNI = [(0, 0.0), (2.95, 0.0), (3.5, 1.0), (12.0, 1.0), (12.45, 0.0), (14, 0.0)]
K_SIDE = [(0, 0.9), (6.5, 0.75), (8.0, 0.1), (9.8, -0.1), (11.6, -0.8), (14, -0.8)]       # + = light from the right
K_ELEV = [(0, 0.05), (6.5, 0.35), (8.0, 1.0), (9.8, 1.0), (11.6, 0.15), (14, 0.0)]
K_AMB = [(0, (0.075, 0.09, 0.17)), (2.6, (0.20, 0.19, 0.27)), (3.8, (0.55, 0.48, 0.44)), (5.8, (0.88, 0.84, 0.78)),
         (8.0, (1.02, 1.01, 0.98)), (9.3, (0.90, 0.88, 0.84)), (11.0, (0.72, 0.56, 0.44)), (12.6, (0.06, 0.06, 0.09)),
         (14, (0.055, 0.055, 0.085))]
K_LAMP = [(0, 0.0), (12.5, 0.0), (13.1, 0.55), (14, 0.55)]
K_RAYS = [(0, 0.0), (3.0, 0.0), (3.8, 1.0), (6.5, 0.8), (8.0, 0.35), (9.8, 0.3), (11.4, 0.85), (12.4, 0.2), (13, 0)]
COV = {"transom": [(0, 1.0)],
       "left": [(0, 1.0), (2.9, 1.0), (4.3, 0.04), (8.0, 0.04), (9.0, 0.5), (11.4, 0.5), (12.4, 1.0)],
       "right": [(0, 1.0), (3.3, 1.0), (4.7, 0.04), (8.3, 0.04), (9.3, 0.5), (11.8, 0.5), (12.8, 1.0)]}
ZOOM = [(0, 1.07), (13.2, 1.0), (14, 1.0)]
TAU = np.array([1.0, 0.80, 0.58], np.float32) * 0.24       # light through the beige fabric (warm)


def outside(t, sun, sunc, suni):
    """sky + sun + skyline in screen space over BB (linear rgb)"""
    x0, y0, x1, y1 = BB
    yy, xx = YY[y0:y1, x0:x1], XX[y0:y1, x0:x1]
    zen, hor = key(t, K_ZEN), key(t, K_HOR)
    e = np.clip((HZ - yy) / 1050.0, 0, 1) ** 0.55
    sky = hor * (1 - e[..., None]) + zen * e[..., None]
    d = np.sqrt((xx - sun[0]) ** 2 + (yy - sun[1]) ** 2)
    sky += sunc * suni * (0.60 * np.exp(-d / 60.0) + 0.16 * np.exp(-d / 260.0))[..., None]
    cl = CLOUD[y0:y1, x0:x1][..., None]
    cl_col = sunc * suni * 0.55 * np.clip(1 - e[..., None] * 0.4, 0, 1) + hor * 0.45 + zen * 0.3
    sky = sky * (1 - cl * 0.32) + cl_col * cl * 0.32
    disc = np.clip((26 - d) / 2.5, 0, 1) * (yy < SKY_NEAR[x0:x1][None, :] - 1)
    sky += (sunc * 0.6 + 0.4) * 7.0 * suni * disc[..., None]
    # skyline: far (hazy) and near layers, the tower; backlit at dawn/dusk, hazy-lit by day
    dl = float(key(t, [(0, 0.0), (3.0, 0.0), (6.5, 0.8), (8.0, 1.0), (9.8, 1.0), (11.4, 0.2), (12.4, 0.0)]))
    far_col = (hor * 0.30 + zen * 0.22) * (1 - dl) + np.array([0.58, 0.62, 0.70]) * dl
    near_col = (hor * 0.10 + zen * 0.07) * (1 - dl) + np.array([0.36, 0.36, 0.38]) * dl
    far = (yy >= SKY_FAR[x0:x1][None, :]).astype(np.float32)
    near = (yy >= SKY_NEAR[x0:x1][None, :]).astype(np.float32)
    far = cv2.GaussianBlur(far, (0, 0), 1.1)
    near = cv2.GaussianBlur(near, (0, 0), 0.7)
    tw = TOWER[y0:y1, x0:x1] * 0.9
    haze = np.exp(-np.abs(yy - HZ + 20) / 45.0)[..., None] * (hor * 0.25 + 0.05 * dl)
    sky = sky * (1 - far[..., None]) + far_col * far[..., None]
    sky = sky * (1 - tw[..., None]) + far_col * 0.9 * tw[..., None]
    sky = sky + haze * far[..., None] * 0.6
    sky = sky * (1 - near[..., None]) + near_col * (0.85 + 0.15 * np.clip((HZ - yy) / 40.0, 0, 1))[..., None] * near[..., None]
    dusk = float(np.clip((t - 11.2) / 1.2, 0, 1))
    if dusk > 0:
        sky += (WINS[y0:y1, x0:x1] * near * (yy >= SKY_NEAR[x0:x1][None, :] + 3))[..., None] * \
            np.array([1.0, 0.70, 0.40]) * 0.9 * dusk
    out = np.zeros((H, W, 3), np.float32)
    out[y0:y1, x0:x1] = sky
    return out


def sheets(t, back, front):
    """real plisse sheets at their coverage, relit; returns rgb, alpha (screen) and coverage per pane"""
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
        # relight: front (room) + translucent backlight (sky/sun behind the fabric)
        lum = sh.mean(axis=2, keepdims=True)
        b = back[k]
        sh = sh * front * 0.92 + lum * b * 0.95
        w_rgb = cv2.warpPerspective(sh, p["H"], (W, H), flags=cv2.INTER_LINEAR)
        w_a = cv2.warpPerspective(a, p["H"], (W, H), flags=cv2.INTER_LINEAR)
        rgb += w_rgb * w_a[..., None]
        al = np.maximum(al, w_a)
    return rgb, al, covs


def sheet_bottom_y(k, c):
    """screen y of the bottom rail along the pane (approx, at the left edge and right edge)"""
    rw, rh = RECT[k]
    y = RAIL[k] + c * (rh - RAIL[k])
    pts = cv2.perspectiveTransform(np.float32([[[0, y], [rw, y]]]), PANES[k]["H"])[0]
    return pts


def god_rays(src, sun, n=30):
    """radial blur (quarter res) of the bright aperture away from the sun position"""
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
        w = 1.0 - 0.6 * i / n
        acc += cv2.remap(s, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT) * w
        wsum += w
    acc /= wsum
    return cv2.resize(acc, (W, H), interpolation=cv2.INTER_LINEAR)


_DUST = np.random.default_rng(5).uniform(0, 1, (90, 4)).astype(np.float32)


def dust(t, rays):
    img = np.zeros((H, W), np.float32)
    for k, (a, b, c, d) in enumerate(_DUST):
        x = 120 + a * 900 + 40 * np.sin(0.23 * t + 6 * c)
        y = 450 + b * 1200 + 28 * np.sin(0.17 * t + 6 * d) - 9 * t
        r = 1.2 + 2.2 * c
        tw = 0.6 + 0.4 * np.sin(1.3 * t + 9 * d)
        xi, yi = int(x), int(y)
        if 3 <= xi < W - 3 and 3 <= yi < H - 3:
            cv2.circle(img, (xi, yi), max(1, int(r)), float(tw), -1, cv2.LINE_AA)
    img = cv2.GaussianBlur(img, (0, 0), 1.2)
    return img * np.clip(rays.mean(axis=2) * 3.0, 0, 1.5)


def tone(x):
    s = 0.78
    return np.where(x < s, x, s + (1 - s) * (1 - np.exp(-(x - s) / (1 - s))))


def frame(i):
    t = i / FPS
    sun = key(t, K_SUN)
    sunc, suni = key(t, K_SUNC), float(key(t, K_SUNI))
    side, elev = float(key(t, K_SIDE)), float(key(t, K_ELEV))
    amb, lamp, rays_k = key(t, K_AMB), float(key(t, K_LAMP)), float(key(t, K_RAYS))
    out_sky = outside(t, sun, sunc, suni)
    # backlight per pane: mean sky behind it (+ the sun if it sits behind that pane)
    back = {}
    for k, p in PANES.items():
        m = p["mask"]
        avg = (out_sky * m[..., None]).sum((0, 1)) / max(1, m.sum())
        back[k] = np.clip(avg * 0.9, 0, 3)
    front = amb + lamp * np.array([1.0, 0.64, 0.36], np.float32) * 0.55
    sh_rgb, sh_a, covs = sheets(t, back, front)
    glass = out_sky * GLASS_SH[..., None] + REFL * (0.04 + 0.5 * float(np.mean(amb)) * 0.06)
    win = glass * (1 - sh_a[..., None]) + sh_rgb
    win_a = M_PANES
    # room relight
    img = LIN * amb + LIN * LAMP * lamp
    # sunlight on the left reveal (morning, light from the right) and the right reveal (evening)
    tl = 1.0
    ybL = sheet_bottom_y("left", covs["left"])[0][1]
    shift = 70 * (1 - elev) + 20
    yl = YY + shift * 0.0
    open_l = ease((YY - (ybL + 25 * elev)) / 30.0)
    trans_l = (open_l + (1 - open_l) * 0.22) * REV_BARS
    if side > 0:
        vlim = 0.30 + 0.55 * side
        lit = ease((vlim - REVL_V) / 0.08) * trans_l * M_REVL * suni * side * tl
        img += LIN * sunc * lit[..., None] * 2.4
    ybR = sheet_bottom_y("right", covs["right"])[1][1]
    open_r = ease((YY - ybR) / 30.0)
    if side < 0:
        lit = ease((0.5 - REVR_V) / 0.2) * (open_r + (1 - open_r) * 0.22) * M_REVR * suni * (-side) * (YY > 420)
        img += LIN * sunc * lit[..., None] * 1.5
    # sunlight on the sill: pane columns shifted by the slant, frame-bottom shadow near the back
    slant = 170 * side * (1 - 0.6 * elev)
    xg = XX + slant * SILL_V
    inL = ease((xg - 240) / 6) * ease((542 - xg) / 6)
    inR = ease((xg - 635) / 6) * ease((1037 - xg) / 6)
    tL = 1.0 if covs["left"] < 0.97 else 0.22
    tR = 1.0 if covs["right"] < 0.97 else 0.22
    vmin = 0.30 * (1 - elev) + 0.04
    sl = (inL * tL + inR * tR) * ease((SILL_V - vmin) / 0.08) * M_SILL * suni * (0.35 + 0.65 * elev)
    sl = cv2.GaussianBlur(sl, (0, 0), 2.0)
    img += LIN * sunc * sl[..., None] * 2.2
    img += LIN * sunc * (cv2.GaussianBlur(sl, (0, 0), 6) * M_SILLF * 0.25)[..., None]
    # window (sky/sheets) inside the pane masks
    img = img * (1 - win_a[..., None]) + win * win_a[..., None]
    # god rays and dust
    if rays_k > 0.01:
        lum = win.mean(axis=2) * win_a * (1 - sh_a)
        src = np.clip(lum - 0.40, 0, 6)[..., None] * sunc
        src += (sh_rgb.mean(axis=2) * sh_a * win_a * 0.10)[..., None] * sunc
        rays = god_rays(src, sun) * rays_k * suni
        img += rays * 1.1
        img += (dust(t, rays) * 0.55)[..., None] * sunc * rays_k
    out = tone(np.clip(img, 0, None)) ** (1 / 2.2)
    # digital camera: slow pull-back to the plate framing
    z = float(key(t, ZOOM))
    if z > 1.0005:
        M = cv2.getRotationMatrix2D((610, 1010), 0, z)
        out = cv2.warpAffine(out, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    g = np.random.default_rng(i).normal(0, 0.008, (H // 2, W // 2)).astype(np.float32)
    out = out + cv2.resize(g, (W, H))[..., None]
    return (np.clip(out, 0, 1) * 255).astype(np.uint8)


def render():
    os.makedirs(f"{D}/fr", exist_ok=True)
    n = int(round(DUR * FPS))
    with Pool(6) as p:
        for k in range(0, n, 24):
            ch = list(range(k, min(n, k + 24)))
            for i, a in zip(ch, p.map(frame, ch)):
                cv2.imwrite(f"{D}/fr/{i:04d}.jpg", cv2.cvtColor(a, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 96])
    os.system(f"ffmpeg -nostdin -v error -y -framerate 30 -i {D}/fr/%04d.jpg -c:v libx264 -preset fast -crf 14 "
              f"-pix_fmt yuv420p {D}/anim.mp4")


if __name__ == "__main__":
    if sys.argv[1] == "prev":
        ts = [float(v) for v in sys.argv[2].split(",")]
        with Pool(6) as p:
            ims = p.map(frame, [int(round(v * FPS)) for v in ts])
        c = np.full((640, 365 * len(ims), 3), 255, np.uint8)
        for k, a in enumerate(ims):
            c[:, k * 365:k * 365 + 360] = cv2.resize(a, (360, 640), interpolation=cv2.INTER_AREA)
        cv2.imwrite(f"{D}/prev_room.jpg", cv2.cvtColor(c, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 88])
    else:
        render()
