"""«Bitta deraza» v2 — the whole story OUTSIDE, in one continuous camera move (owner 16.11):
a dusk block of flats; one window (ours) glows with a cream PLISSE parked at the top of each sash, clearly visible
from frame 0; the camera drifts closer, the plisse slowly comes down sash by sash and the window closes from the
street; the city's other windows go dark one by one; a person's shadow walks behind the glowing fabric; the
IMPERIAL mark appears printed on the left sash; the camera pulls back — ours is the warm window in a sleeping
house. Renders bo/facade2.mp4 (1080x1920, 30 fps). The other windows show real fabric frames from our footage.
"""
import math
import subprocess

import cv2
import numpy as np
from PIL import Image

import facade as F0                                  # shared: wrect, fabric(), dark_glass(), CROPS, layout

D = F0.D
W, H, FPS = 1080, 1920, 30
DUR = 12.6
K = F0.K
UW, UH = F0.UW, F0.UH
HERO = (1, 3)
HX0, HY0, HX1, HY1 = F0.wrect(*HERO)
KW = 2.7                                             # hero window image px per unit
WIW, WIH = int((HX1 - HX0) * KW), int((HY1 - HY0) * KW)
MUL = int(8 * KW)                                    # mullion width (px)
SW = (WIW - MUL) // 2                                # sash width
DARK0 = {(1, 0), (3, 1), (0, 4), (2, 5), (1, 6), (3, 6), (0, 1)}
OFF = {(0, 0): 4.9, (2, 1): 5.3, (3, 2): 5.7, (0, 3): 6.1, (2, 2): 6.5, (3, 4): 6.9, (1, 5): 7.3, (0, 6): 7.7,
       (2, 4): 8.1, (3, 0): 8.5, (1, 2): 8.9, (0, 5): 9.3, (2, 3): 9.7, (1, 1): 10.1, (2, 6): 10.5, (3, 5): 10.9,
       (0, 2): 11.2, (3, 3): 11.4, (1, 4): -1.0, (2, 0): 11.8}
LOGO = Image.open("/home/claude/imperial/src/img/logo_light.png").convert("RGBA")
T_LEFT, T_RIGHT, T_DOWN = 3.6, 4.5, 2.6              # sash plisse start times, descent duration
T_WALK, T_LOGO, T_BACK = 7.4, 8.3, 10.4


def ease(u):
    u = min(1.0, max(0.0, u))
    return u * u * (3 - 2 * u)


def ease_io(u):
    u = min(1.0, max(0.0, u))
    return 0.5 - 0.5 * math.cos(math.pi * u)


# ---------------------------------------------------------------- facade canvases (lit / all-dark / window ids)
def build():
    lit = F0.build_canvas(set(F0.SWITCH))                           # all switchable windows on
    cw, ch = UW * K, UH * K
    dark = lit.copy()
    ids = np.full((ch // 4, cw // 4), -1, np.int16)                 # quarter-res id map (window + glow halo)
    for c in range(F0.COLS):
        for r in range(F0.ROWS):
            x0, y0, x1, y1 = [v * K for v in F0.wrect(c, r)]
            dark[y0:y1, x0:x1] = F0.dark_glass(x1 - x0, y1 - y0, c * 10 + r)
            idx = c * F0.ROWS + r
            ids[max(0, (y0 - 120 * K) // 4):(y1 + 160 * K) // 4, max(0, (x0 - 90 * K) // 4):(x1 + 90 * K) // 4] = idx
    top = 640 * K
    dark[top:] = np.minimum(dark[top:], lit[top:])                   # dark canvas keeps the wall without glow
    wall = F0.build_canvas(set())                                   # recompute wall without glow for dark windows
    for c in range(F0.COLS):
        for r in range(F0.ROWS):
            x0, y0, x1, y1 = [v * K for v in F0.wrect(c, r)]
            wall[y0:y1, x0:x1] = dark[y0:y1, x0:x1]
    return (lit * 255).astype(np.uint8), (wall * 255).astype(np.uint8), ids


# ---------------------------------------------------------------- the hero window, drawn in its own pixel space
def interior():
    w, h = WIW, WIH
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    v = yy / h
    img = np.zeros((h, w, 3), np.float32)
    img[..., 0] = 0.22 + 0.50 * np.clip(v * 1.4, 0, 1)              # R
    img[..., 1] = 0.14 + 0.34 * np.clip(v * 1.4, 0, 1)
    img[..., 2] = 0.09 + 0.20 * np.clip(v * 1.4, 0, 1)
    lamp = np.exp(-(((xx - w * 0.24) / (w * 0.30)) ** 2 + ((yy - h * 0.55) / (h * 0.32)) ** 2))
    img += lamp[..., None] * np.array([0.75, 0.52, 0.28])
    img = np.clip(img, 0, 1)
    over = np.zeros_like(img)
    cv2.rectangle(over, (int(w * 0.36), int(h * 0.80)), (w, h), (0.16, 0.11, 0.08), -1)        # sofa
    cv2.ellipse(over, (int(w * 0.62), int(h * 0.80)), (int(w * 0.28), int(h * 0.05)), 0, 180, 360, (0.16, 0.11, 0.08), -1)
    cv2.line(over, (int(w * 0.24), int(h * 0.58)), (int(w * 0.24), h), (0.10, 0.07, 0.05), max(3, w // 160))  # lamp pole
    pts = np.array([[w * 0.17, h * 0.58], [w * 0.31, h * 0.58], [w * 0.28, h * 0.48], [w * 0.20, h * 0.48]], np.int32)
    cv2.fillPoly(over, [pts], (1.0, 0.86, 0.62))                                                  # lamp shade
    cv2.rectangle(over, (int(w * 0.48), int(h * 0.30)), (int(w * 0.70), int(h * 0.44)), (0.30, 0.22, 0.16), -1)  # picture
    m = over.sum(-1, keepdims=True) > 0
    img = np.where(m, over, img)
    img = cv2.GaussianBlur(img, (0, 0), 7)                                                           # depth of field
    refl = cv2.GaussianBlur(F0.dark_glass(w, h, 7), (0, 0), 40) * 0.25                               # soft reflection
    return np.clip(img * 0.92 + refl, 0, 1)


def silhouette(h):
    """a standing person, normalised polygon -> filled mask of height h"""
    pts = [(0.0, 0.0)]
    w = int(h * 0.42)
    m = np.zeros((h, w), np.float32)
    s = lambda x, y: (int(w / 2 + x * h), int(y * h))
    cv2.ellipse(m, s(0, 0.075), (int(0.055 * h), int(0.068 * h)), 0, 0, 360, 1, -1)
    body = [(-0.03, 0.14), (0.03, 0.14), (0.13, 0.19), (0.12, 0.36), (0.105, 0.55), (0.09, 0.56), (0.085, 0.58),
            (0.075, 0.99), (0.025, 0.99), (0.005, 0.62), (-0.005, 0.62), (-0.025, 0.99), (-0.075, 0.99),
            (-0.085, 0.58), (-0.09, 0.56), (-0.105, 0.55), (-0.12, 0.36), (-0.13, 0.19)]
    cv2.fillPoly(m, [np.array([s(x, y) for x, y in body], np.int32)], 1)
    return m


_FIB = cv2.resize(np.random.default_rng(11).normal(0, 1, (400, 120)).astype(np.float32), (WIW, WIH * 2 // 2))


def pleats(w, h, b, rail, t_off=0.0):
    """backlit plisse sheet from the head rail down to the bottom rail at b (px); returns rgb, coverage mask"""
    rgb = np.zeros((h, w, 3), np.float32)
    cov = np.zeros((h, w), np.float32)
    top = rail
    b = int(max(top + 18, min(h, b)))
    n = 64
    ys = np.arange(top, b, dtype=np.float32)
    per = max(1e-3, (b - top) / n)
    ph = ((ys - top) / per) % 1.0
    amp = min(1.0, per / 7.0)
    lum = 0.84 + amp * (0.13 * np.cos(2 * np.pi * ph) - 0.14 * np.exp(-(ph / 0.07) ** 2)) - (1 - amp) * 0.12
    rgb[top:b] = lum[:, None, None] * np.array([1.0, 0.88, 0.70], np.float32)
    rgb[top:b] *= 1 + _FIB[: b - top, :w, None] * 0.035                     # fabric fibre texture
    cov[top:b] = 1
    return rgb, cov, b


def hero_image(t, inter, glowmap, logo_a, sil, rng):
    w, h = WIW, WIH
    img = inter.copy()
    rail = int(16 * KW / 2.7 * 1.0) + 10
    for k, (x0, t0) in enumerate([(0, T_LEFT), (SW + MUL, T_RIGHT)]):
        u = 0.30 + 0.70 * ease_io((t - t0) / T_DOWN)            # installed, a third down from frame 0
        stack = int(h * 0.04)
        b = rail + stack + int((h - rail - stack - 6) * u)
        rgb, cov, bb = pleats(SW, h, b, rail)
        glow = glowmap[:, x0:x0 + SW]
        fab = rgb * (0.55 + 0.55 * glow[..., None])
        fab *= 1 - 0.18 * np.exp(-(np.minimum(np.arange(SW), SW - 1 - np.arange(SW)) / 22.0) ** 2)[None, :, None]
        # person's shadow (only once both sashes are down)
        if t > T_WALK and sil is not None:
            walk = ease_io((t - T_WALK) / 1.8)
            px = int(w * (0.98 - 0.30 * walk) + 6 * math.sin(t * 1.3))
            sh_ = np.zeros((h, w), np.float32)
            sy = h - sil.shape[0] - int(h * 0.02)
            xa, xb = px - sil.shape[1] // 2, px + sil.shape[1] // 2
            sx0, sx1 = max(0, xa), min(w, xb)
            if sx1 > sx0:
                sh_[sy:sy + sil.shape[0], sx0:sx1] = sil[:, sx0 - xa:sx1 - xa]
            sh_ = cv2.GaussianBlur(sh_, (0, 0), 16) * 0.55 * ease((t - T_WALK) / 0.6)
            fab *= (1 - sh_[:, x0:x0 + SW])[..., None]
        # IMPERIAL mark printed on the left sash
        if k == 0 and t > T_LOGO:
            rv = ease((t - T_LOGO) / 1.4)
            la = logo_a.copy()
            lw = la.shape[1]
            edge = (lw + 160) * rv - 80
            wipe = np.clip((edge - np.arange(lw)) / 80.0, 0, 1)[None, :]
            ly = int(h * 0.40)
            lx = (SW - lw) // 2
            a = la * wipe * 0.85
            ink = np.array([0.30, 0.20, 0.13], np.float32)
            region = fab[ly:ly + la.shape[0], lx:lx + lw]
            lumr = region.mean(-1, keepdims=True)
            region[:] = region * (1 - a[..., None]) + (ink * (0.8 + 0.4 * lumr)) * a[..., None]
            if T_LOGO + 1.6 < t < T_LOGO + 2.8:                      # gold sheen pass
                sx = (t - T_LOGO - 1.6) / 1.2 * (lw + 200) - 100
                sw = np.exp(-((np.arange(lw) - sx) / 40.0) ** 2)[None, :]
                region[:] += (la * sw)[..., None] * np.array([0.35, 0.26, 0.08])
        sash = img[:, x0:x0 + SW]
        sash[:] = sash * (1 - cov[..., None]) + fab * cov[..., None]
        # head rail and bottom rail with a small handle
        sash[: rail] = np.array([0.20, 0.20, 0.21])
        sash[: rail // 3] = np.array([0.30, 0.30, 0.31])
        sash[bb - 10:bb + 2] = np.array([0.24, 0.24, 0.25])
        sash[bb - 10:bb - 7] = np.array([0.40, 0.40, 0.41])
        cx = SW // 2
        sash[bb + 2:bb + 9, cx - 22:cx + 22] = np.array([0.15, 0.15, 0.16])
    img[:, SW:SW + MUL] = np.array([0.09, 0.09, 0.09])               # mullion
    return np.clip(img, 0, 1)


# ---------------------------------------------------------------- camera
def camera(t):
    hc = ((HX0 + HX1) / 2, (HY0 + HY1) / 2)
    k0 = (0.95, hc[0] + 40, hc[1] + 170)
    k1 = (2.55, hc[0], hc[1] + 60)
    k2 = (2.64, hc[0] - 4, hc[1] + 58)
    k3 = (0.78, hc[0] + 60, hc[1] + 120)
    if t < T_LOGO:
        u = ease_io(t / T_LOGO)
        a, b = k0, k1
    elif t < T_BACK:
        u = (t - T_LOGO) / (T_BACK - T_LOGO)
        a, b = k1, k2
    else:
        u = ease_io((t - T_BACK) / (DUR - T_BACK - 0.2))
        a, b = k2, k3
    s = math.exp(math.log(a[0]) + (math.log(b[0]) - math.log(a[0])) * u)
    return s, a[1] + (b[1] - a[1]) * u, a[2] + (b[2] - a[2]) * u


def render():
    lit, wall, ids = build()
    inter = interior()
    lum = cv2.cvtColor(inter.astype(np.float32), cv2.COLOR_RGB2GRAY)
    glowmap = cv2.GaussianBlur(lum, (0, 0), 60)
    glowmap = (glowmap - glowmap.min()) / (glowmap.max() - glowmap.min() + 1e-6)
    lw = int(SW * 0.74)
    lg = LOGO.resize((lw, int(LOGO.height * lw / LOGO.width)), Image.LANCZOS)
    la_ = np.asarray(lg).astype(np.float32) / 255
    logo_a = la_[..., 3] * (la_[..., :3] @ np.array([0.3, 0.59, 0.11], np.float32))
    sil = silhouette(int(WIH * 0.78))
    enc = subprocess.Popen(["ffmpeg", "-nostdin", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s",
                            f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "fast", "-crf", "14",
                            "-pix_fmt", "yuv420p", f"{D}/bo/facade2.mp4"], stdin=subprocess.PIPE)
    rng = np.random.default_rng(1)
    n = int(DUR * FPS)
    hero_id = HERO[0] * F0.ROWS + HERO[1]
    for i in range(n):
        t = i / FPS
        s, cx, cy = camera(t)
        sc = s / K
        M = np.array([[sc, 0, W / 2 - sc * cx * K], [0, sc, H / 2 - sc * cy * K]], np.float32)
        fl = cv2.INTER_LINEAR if sc > 1 else cv2.INTER_AREA
        a = cv2.warpAffine(lit, M, (W, H), flags=fl, borderMode=cv2.BORDER_REPLICATE).astype(np.float32)
        b = cv2.warpAffine(wall, M, (W, H), flags=fl, borderMode=cv2.BORDER_REPLICATE).astype(np.float32)
        Mi = M.copy()
        Mi[:, :2] *= 4
        idm = cv2.warpAffine(ids, Mi, (W, H), flags=cv2.INTER_NEAREST, borderMode=cv2.BORDER_CONSTANT, borderValue=-1)
        off = np.zeros(F0.COLS * F0.ROWS + 1, np.float32)
        for (c, r), ts in OFF.items():
            off[c * F0.ROWS + r] = ease((t - ts) / 0.25)
        f = off[np.where(idm >= 0, idm, F0.COLS * F0.ROWS)][..., None]
        fr = a * (1 - f) + b * f
        # sky deepens toward night
        sky = (idm < 0) & (np.arange(H)[:, None] < H)
        night = 1 - 0.35 * ease(t / DUR)
        fr[sky] *= night
        # the hero window
        hi = hero_image(t, inter, glowmap, logo_a, sil, rng)
        Mh = np.array([[s / KW, 0, W / 2 + s * (HX0 - cx)], [0, s / KW, H / 2 + s * (HY0 - cy)]], np.float32)
        hw = cv2.warpAffine((hi * 255).astype(np.float32)[..., ::-1], Mh, (W, H), flags=cv2.INTER_LINEAR,
                            borderMode=cv2.BORDER_CONSTANT, borderValue=0)
        hm = cv2.warpAffine(np.ones((WIH, WIW), np.float32), Mh, (W, H), flags=cv2.INTER_LINEAR,
                            borderMode=cv2.BORDER_CONSTANT, borderValue=0)[..., None]
        fr = fr * (1 - hm) + hw * hm
        # warm spill on the wall under our window, stronger as the others go dark
        gx, gy = W / 2 + s * ((HX0 + HX1) / 2 - cx), H / 2 + s * (HY1 + 40 - cy)
        yy, xx = np.ogrid[0:H, 0:W]
        spill = np.exp(-(((xx - gx) / (s * 320)) ** 2 + ((yy - gy) / (s * 180)) ** 2)).astype(np.float32)
        fr += spill[..., None] * np.array([18, 34, 60], np.float32) * (0.6 + 0.4 * ease((t - 5) / 5))
        # cinematic focus: soft vignette around our window
        vg = 1 - 0.30 * np.clip((((xx - gx) / (W * 0.75)) ** 2 + ((yy - (gy - s * 220)) / (H * 0.62)) ** 2), 0, 1)
        fr *= vg[..., None]
        fr += rng.normal(0, 3.0, (H, W, 1))
        if t < 0.3:
            fr *= t / 0.3
        enc.stdin.write(np.clip(fr, 0, 255).astype(np.uint8).tobytes())
    enc.stdin.close()
    enc.wait()


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        inter = interior()
        lum = cv2.cvtColor(inter.astype(np.float32), cv2.COLOR_RGB2GRAY)
        glowmap = cv2.GaussianBlur(lum, (0, 0), 60)
        glowmap = (glowmap - glowmap.min()) / (glowmap.max() - glowmap.min() + 1e-6)
        lw = int(SW * 0.74)
        lg = LOGO.resize((lw, int(LOGO.height * lw / LOGO.width)), Image.LANCZOS)
        la_ = np.asarray(lg).astype(np.float32) / 255
        la = la_[..., 3] * (la_[..., :3] @ np.array([0.3, 0.59, 0.11], np.float32))
        sil = silhouette(int(WIH * 0.78))
        ims = []
        for t in [0.5, 4.2, 5.4, 7.0, 8.6, 9.6, 10.2]:
            hi = hero_image(t, inter, glowmap, la, sil, np.random.default_rng(0))
            ims.append(Image.fromarray((hi * 255).astype(np.uint8)).resize((WIW // 3, WIH // 3)))
        c = Image.new("RGB", ((WIW // 3 + 4) * len(ims), WIH // 3), "white")
        for k, im in enumerate(ims):
            c.paste(im, (k * (WIW // 3 + 4), 0))
        c.save(f"{D}/hero_test.jpg", quality=88)
    else:
        render()
