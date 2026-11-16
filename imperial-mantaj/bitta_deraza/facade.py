"""Evening facade push-in for «Bitta deraza» (Imperial): a procedural dusk apartment block whose lit windows glow
with REAL fabrics from our own footage (plisse, kombo, dikey, curtains: tex/*.png), two lights switch on, and the
camera pushes into one dark window and through the glass. Rendered straight to bo/facade.mp4 (1080x1920, 30 fps).
"""
import math
import subprocess

import cv2
import numpy as np

D = "/home/claude/reels/ref1116"
W, H, FPS = 1080, 1920, 30
DUR = 3.8
UW, UH = 2400, 4800                   # facade units
K = 2                                 # canvas px per unit
COLS, ROWS = 4, 7
WX0, WY0, WSTEP, FSTEP = 220, 900, 520, 520
WW_, WH_ = 380, 430
TARGET = (2, 3)                       # col, row of the window we enter
SWITCH = {(0, 2): 1.1, (3, 4): 1.9}   # windows whose light turns on at t
DARK = {(1, 0), (3, 1), (0, 4), (2, 5), (1, 6), (3, 6), (0, 1)}
CROPS = {0: (60, 100, 760, 1300), 1: (360, 200, 960, 1500), 2: (120, 700, 700, 1500), 3: (90, 600, 470, 1400),
         4: (380, 480, 1000, 1350), 5: (100, 200, 1000, 1700), 6: (0, 300, 1080, 1700), 7: (0, 200, 1080, 1700),
         8: (0, 0, 1080, 1700), 9: (100, 200, 1000, 1700), 10: (60, 200, 760, 1400), 11: (250, 300, 560, 1400)}


def wrect(c, r):
    x, y = WX0 + c * WSTEP, WY0 + r * FSTEP
    return x, y, x + WW_, y + WH_


def fabric(i, w, h, lit=1.0):
    x0, y0, x1, y1 = CROPS[i]
    im = cv2.imread(f"{D}/tex/t{i:02d}.png")[y0:y1, x0:x1].astype(np.float32) / 255
    s = max(w / im.shape[1], h / im.shape[0])
    im = cv2.resize(im, (max(w, int(im.shape[1] * s + 1)), max(h, int(im.shape[0] * s + 1))), interpolation=cv2.INTER_AREA)
    oy, ox = (im.shape[0] - h) // 2, (im.shape[1] - w) // 2
    im = im[oy:oy + h, ox:ox + w]
    g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)[..., None]
    im = 0.55 * im + 0.45 * g                                       # backlit: colours wash toward warm light
    warm = np.array([0.55, 0.80, 1.0], np.float32)                  # BGR
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    lamp = 0.65 + 0.55 * np.exp(-(((xx - w * 0.5) / (w * 0.7)) ** 2 + ((yy - h * 0.35) / (h * 0.8)) ** 2))
    out = (im ** 0.85) * warm * lamp[..., None] * 1.15 * lit
    return np.clip(out, 0, 1)


def dark_glass(w, h, seed, interior=0.0):
    r = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    g = np.zeros((h, w, 3), np.float32)
    g[..., 0] = 0.10 + 0.10 * (1 - yy / h)                          # sky reflection, bluish
    g[..., 1] = 0.07 + 0.06 * (1 - yy / h)
    g[..., 2] = 0.05 + 0.04 * (1 - yy / h)
    band = np.exp(-((xx - yy * 0.35 - w * 0.2) / (w * 0.12)) ** 2) * 0.05
    g += band[..., None]
    for _ in range(int(w * h / 9000)):                              # reflected city lights
        x, y = r.integers(0, w), r.integers(int(h * 0.55), h)
        c = (0.5, 0.75, 1.0) if r.random() < 0.7 else (1.0, 0.9, 0.7)
        cv2.circle(g, (int(x), int(y)), max(1, w // 160), c, -1, cv2.LINE_AA)
    g = cv2.GaussianBlur(g, (0, 0), max(1, w / 300))
    if interior > 0:                                                # a dim warm lamp deep inside
        lamp = np.exp(-(((xx - w * 0.3) / (w * 0.35)) ** 2 + ((yy - h * 0.62) / (h * 0.3)) ** 2))
        g += interior * lamp[..., None] * np.array([0.25, 0.45, 0.75], np.float32)
    return np.clip(g, 0, 1)


def build_canvas(on_set):
    cw, ch = UW * K, UH * K
    r = np.random.default_rng(7)
    yy = np.arange(ch, dtype=np.float32)[:, None] / ch
    can = np.zeros((ch, cw, 3), np.float32)
    sky = np.stack([0.32 - 0.18 * yy * 6, 0.20 - 0.12 * yy * 6, 0.14 - 0.08 * yy * 6], -1)   # BGR dusk blue
    can[:] = np.clip(sky, 0.03, 1) * np.ones((1, cw, 1), np.float32)
    top = 640 * K
    noise = cv2.resize(r.normal(0, 1, (ch // 16, cw // 16)).astype(np.float32), (cw, ch))
    wall = np.array([0.215, 0.205, 0.20], np.float32)[None, None, :] * (1 + 0.05 * noise[..., None])
    wall = wall * (1 - 0.25 * ((np.arange(ch, dtype=np.float32)[:, None, None] - top) / ch))
    can[top:] = wall[top:]
    for k in range(ROWS + 1):                                      # slab bands
        y = (WY0 - 80 + k * FSTEP) * K
        can[y:y + 34 * K] *= 1.18
    for c in range(COLS + 1):                                      # pilasters
        x = (WX0 - 70 + c * WSTEP) * K
        can[top:, x:x + 30 * K] *= 0.86
    can[top - 30 * K:top] = np.array([0.12, 0.12, 0.13], np.float32)   # roof edge
    glow = np.zeros((ch // 4, cw // 4), np.float32)
    for c in range(COLS):
        for rr in range(ROWS):
            x0, y0, x1, y1 = [v * K for v in wrect(c, rr)]
            ww, hh = x1 - x0, y1 - y0
            lit = (c, rr) not in DARK and ((c, rr) not in SWITCH or (c, rr) in on_set)
            if (c, rr) == TARGET:
                img = dark_glass(ww, hh, 99, interior=0.6)
            elif lit:
                img = fabric((c * 7 + rr * 3) % 12, ww, hh)
                cv2.rectangle(glow, (x0 // 4, y0 // 4), (x1 // 4, y1 // 4), 1.0, -1)
            else:
                img = dark_glass(ww, hh, c * 10 + rr)
            can[y0:y1, x0:x1] = img
            f = 12 * K                                              # dark aluminium frame + mullion
            can[y0 - f:y0, x0 - f:x1 + f] = 0.09
            can[y1:y1 + f, x0 - f:x1 + f] = 0.09
            can[y0:y1, x0 - f:x0] = 0.09
            can[y0:y1, x1:x1 + f] = 0.09
            xm = (x0 + x1) // 2
            can[y0:y1, xm - 4 * K:xm + 4 * K] = 0.09
            can[y1 + f:y1 + f + 10 * K, x0 - 2 * f:x1 + 2 * f] = 0.30  # sill
    glow = cv2.GaussianBlur(glow, (0, 0), 30)
    glow = cv2.resize(glow, (cw, ch))[..., None] * np.array([0.10, 0.17, 0.26], np.float32)
    can[top:] += glow[top:]
    return np.clip(can, 0, 1)


def ease(u):
    return u * u * (3 - 2 * u)


def camera(t):
    u = min(1.0, t / (DUR - 0.25))
    e = ease(u) ** 1.35
    s0 = W / UW * 1.02
    x0, y0, x1, y1 = wrect(*TARGET)
    s1 = H / (y1 - y0) * 1.6                                        # deep inside the glass at the end
    s = math.exp(math.log(s0) + (math.log(s1) - math.log(s0)) * e)
    px = x0 + (x1 - x0) * 0.27                                      # centre of the left pane, not the mullion
    cx = UW / 2 + (px - UW / 2) * ease(min(1, u * 1.1))
    cy = UH * 0.52 + ((y0 + y1) / 2 - UH * 0.52) * ease(min(1, u * 1.1))
    cy -= 40 * math.sin(u * math.pi)                                # slight crane
    return s, cx, cy


def render():
    states = {}
    order = sorted(SWITCH.items(), key=lambda kv: kv[1])
    sets = [set()]
    for k, _ in order:
        sets.append(sets[-1] | {k})
    for s_ in sets:
        states[frozenset(s_)] = (build_canvas(s_) * 255).astype(np.uint8)
    enc = subprocess.Popen(["ffmpeg", "-nostdin", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s",
                            f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "fast", "-crf", "14",
                            "-pix_fmt", "yuv420p", f"{D}/bo/facade.mp4"], stdin=subprocess.PIPE)
    rng = np.random.default_rng(1)
    n = int(DUR * FPS)
    for i in range(n):
        t = i / FPS
        on = frozenset(k for k, ts in SWITCH.items() if t >= ts)
        can = states[on]
        s, cx, cy = camera(t)
        sc = s / K
        M = np.array([[sc, 0, W / 2 - sc * cx * K], [0, sc, H / 2 - sc * cy * K]], np.float32)
        fr = cv2.warpAffine(can, M, (W, H), flags=cv2.INTER_LINEAR if sc > 1 else cv2.INTER_AREA,
                            borderMode=cv2.BORDER_REPLICATE).astype(np.float32)
        # flicker on the window that just switched on
        for k, ts in SWITCH.items():
            if ts <= t < ts + 0.25:
                fr *= 1.0 + 0.02 * rng.normal()
        u = min(1.0, t / 1.8)                                       # foreground building edge, faster parallax
        fx = int(230 * (1 - ease(u)) - 40)
        if fx > 0:
            fg = np.zeros((H, W), np.float32)
            fg[:, :fx] = 1.0
            fg = cv2.GaussianBlur(fg, (0, 0), 6)[..., None]
            edge = np.full((H, W, 3), (12, 10, 10), np.float32)
            cv2.line(edge, (fx - 3, 0), (fx - 3, H), (46, 34, 30), 3)  # faint cool rim light on the corner
            edge = cv2.GaussianBlur(edge, (0, 0), 3)
            fr = fr * (1 - fg) + edge * fg
        fr += rng.normal(0, 3.0, (H, W, 1))                         # film grain
        if t > DUR - 0.35:                                          # through the glass -> black
            fr *= max(0.0, (DUR - t) / 0.35) ** 1.5
        enc.stdin.write(np.clip(fr, 0, 255).astype(np.uint8).tobytes())
    enc.stdin.close()
    enc.wait()


if __name__ == "__main__":
    import os
    os.makedirs(f"{D}/bo", exist_ok=True)
    render()
