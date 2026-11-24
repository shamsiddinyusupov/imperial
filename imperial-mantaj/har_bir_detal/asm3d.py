"""Premium macro version of the assemblies (owner 25.11: «closer and more premium, like the watch film»).
Each blind type still builds itself from its own real parts (cut along the real seams / band edges / pleats of a
4K still of the owner's install), but now on a plane seen in 3D: a macro camera close to the surface, slow
pull-back with a turning angle, shallow depth of field (blur grows with distance from the focus plane, focus racks),
a moving key light, a specular sweep, bloom, split-tone grade, grain, vignette. Writes seg/b_<type>.mp4 (DUR s) and
seg/b_<type>.json (landing times).   python3 asm3d.py [types] | still <type> <t,t,..>
"""
import json
import math
import subprocess
import sys

import cv2
import numpy as np

D = "/home/claude/reels/yigil2"
W, H, FPS = 1080, 1920, 30
PW, PH = 2160, 3840
DUR = 2.9


def ease_out(u):
    u = np.clip(u, 0, 1)
    return 1 - (1 - u) ** 3


def ease_io(u):
    u = np.clip(u, 0, 1)
    return u * u * (3 - 2 * u)


def load(path):
    im = cv2.imread(path)
    if im.shape[1] != PW:
        im = cv2.resize(im, (PW, PH), interpolation=cv2.INTER_CUBIC)
    return im.astype(np.float32)


def poly_mask(pts):
    m = np.zeros((PH, PW), np.uint8)
    cv2.fillPoly(m, [np.round(np.array(pts)).astype(np.int32)], 255, cv2.LINE_AA)
    return m.astype(np.float32) / 255


VOID_P = None


def void_plate():
    global VOID_P
    if VOID_P is None:
        VOID_P = np.full((PH, PW, 3), 7.0, np.float32)
    return VOID_P


def shift(a, dx, dy):
    M = np.float32([[1, 0, dx], [0, 1, dy]])
    return cv2.warpAffine(a, M, (PW, PH), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)


# ------------------------------------------------------------- types (plate space)
def dikey():
    plate = load(f"{D}/src/dikey_plate4k.png")
    seams = [(0, 0), (140, 140), (283, 271), (448, 446), (620, 608), (791, 764), (968, 935), (1080, 1080)]
    pieces = []
    for k in range(len(seams) - 1):
        (a0, a1), (b0, b1) = seams[k], seams[k + 1]
        x = lambda xt, xb, y: 2 * (xt + (xb - xt) * (y / 2 - 250) / 1400)  # noqa: E731
        pts = [(x(a0, a1, -20), -20), (x(b0, b1, -20), -20), (x(b0, b1, PH + 20), PH + 20), (x(a0, a1, PH + 20), PH + 20)]
        pieces.append(dict(mask=poly_mask(pts), t0=0.12 + 0.2 * k, fl=0.55, d=(0, -PH * 0.9)))
    cam = dict(yaw=(28, 18), pitch=(-14, -8), roll=(-8, -4), zoom=(2.3, 1.7), look=((1150, 1700), (1080, 1920)), focus=(0.06, -0.04),
               light=((300, 900), (1700, 2600)))
    return plate, pieces, cam


def kombo():
    plate = load(f"{D}/src/kombo4k.png")
    L = [275, 371, 742, 906, 1365, 1603, 2214, 2566, 3383]
    edges = [-300] + L + [PH + 300]
    pieces = []
    for k in range(len(edges) - 1):
        a, b = edges[k], edges[k + 1]
        ya = lambda y0, x: y0 - 80 * (x - 400) / 1300  # noqa: E731
        pts = [(-20, ya(a, -20)), (PW + 20, ya(a, PW + 20)), (PW + 20, ya(b, PW + 20)), (-20, ya(b, -20))]
        side = -1 if k % 2 == 0 else 1
        pieces.append(dict(mask=poly_mask(pts), t0=0.1 + 0.15 * k, fl=0.6, d=(side * PW * 1.05, 0)))
    cam = dict(yaw=(-16, -8), pitch=(26, 16), roll=(6, 3), zoom=(2.2, 1.65), look=((1200, 1500), (1080, 1900)), focus=(0.05, -0.05),
               light=((1800, 600), (500, 2400)))
    return plate, pieces, cam


PER = 153.6


def plisse():
    plate = load(f"{D}/src/c548_0.0.png") * 0.8
    n = int(math.ceil(PH / PER)) + 1
    pieces = [dict(y0=k * PER, t0=0.12 + 0.07 * k, fl=0.36) for k in range(n)]
    cam = dict(yaw=(-20, -10), pitch=(22, 12), roll=(-6, -2), zoom=(2.2, 1.6), look=((1000, 1300), (1080, 1900)), focus=(0.05, -0.04),
               light=((400, 500), (1600, 2800)))
    return plate, pieces, cam


def rollo():
    plate = load(f"{D}/src/rollo_plate.png")
    cam = dict(yaw=(-24, -14), pitch=(12, 6), roll=(5, 2), zoom=(1.7, 1.35), look=((1000, 1500), (1080, 1900)), focus=(0.04, -0.03),
               light=((1700, 700), (600, 2500)))
    return plate, None, cam


def flat_slide(t, plate, pieces):
    c = void_plate().copy()
    done = np.zeros((PH, PW), np.float32)
    for p in pieces:
        u = (t - p["t0"]) / p["fl"]
        if u <= 0:
            continue
        if u >= 1:
            done = np.maximum(done, p["mask"])
            continue
        e = ease_out(u)
        dx, dy = p["d"][0] * (1 - e), p["d"][1] * (1 - e)
        m = shift(p["mask"], dx, dy) * min(1.0, u * 4)
        pp = shift(plate, dx, dy)
        c = c * (1 - m[..., None]) + pp * m[..., None]
    c = c * (1 - done[..., None]) + plate * done[..., None]
    # click flash on edges of pieces that just landed
    for p in pieces:
        k = 1 - (t - p["t0"] - p["fl"]) / 0.22
        if 0 < k <= 1:
            e = cv2.morphologyEx((p["mask"] > 0.5).astype(np.uint8), cv2.MORPH_GRADIENT, np.ones((5, 5), np.uint8))
            e = cv2.GaussianBlur(e.astype(np.float32), (0, 0), 4) * 2.5
            c = c + np.clip(e, 0, 1)[..., None] * 200 * k
    return c, done


def flat_plisse(t, plate, pieces):
    c = void_plate().copy()
    done = 0
    for p in pieces:
        u = (t - p["t0"]) / p["fl"]
        if u <= 0:
            continue
        y0, y1 = int(round(p["y0"])), int(round(min(PH, p["y0"] + PER)))
        if y1 <= y0:
            continue
        e = ease_out(u)
        hh = max(1, int(round((y1 - y0) * e)))
        sq = cv2.resize(plate[y0:y1], (PW, hh), interpolation=cv2.INTER_AREA)
        sh = (0.4 + 0.6 * e) * (np.linspace(1.2, 0.75, hh)[:, None, None] if u < 1 else 1.0)
        c[y0:y0 + hh] = sq * sh
        if 0.6 < u < 1.6:
            k = max(0, 1 - abs(u - 1) / 0.6)
            yb = min(PH - 1, y0 + hh - 1)
            c[max(0, yb - 2):yb + 3] += 150 * k
        if u >= 1:
            done = max(done, y1)
    m = np.zeros((PH, PW), np.float32)
    m[:done] = 1
    return c, m


def flat_rollo(t, plate, _):
    c = void_plate().copy()
    u = ease_io((t - 0.12) / 1.75)
    R = 92
    front = int(round(-2 * R + (PH + 2 * R) * u))
    if front > 0:
        c[:min(PH, front)] = plate[:min(PH, front)]
    y0, y1 = front, front + 2 * R
    if y1 > 0 and y0 < PH:
        s0 = max(0, min(PH - 2 * R, front))
        src = plate[s0:s0 + 2 * R]
        yy = np.linspace(-1, 1, 2 * R)
        shade = (0.3 + 0.8 * np.sqrt(np.clip(1 - yy ** 2, 0, 1)))[:, None, None]
        spec = (np.exp(-((yy + 0.35) / 0.1) ** 2) * 80)[:, None, None]
        cyl = src * shade + spec
        a, b = max(0, y0), min(PH, y1)
        c[a:b] = cyl[a - y0:b - y0]
        e0, e1 = min(PH, y1), min(PH, y1 + 70)
        if e1 > e0:
            c[e0:e1] *= np.linspace(0.5, 1, e1 - e0)[:, None, None]
    m = np.zeros((PH, PW), np.float32)
    m[:max(0, min(PH, front))] = 1
    return c, m


TYPES = {"dikey": (dikey, flat_slide), "kombo": (kombo, flat_slide), "plisse": (plisse, flat_plisse),
         "rollo": (rollo, flat_rollo)}


# ------------------------------------------------------------- light, camera, look
def lighting(c, t, cam, done):
    u = t / DUR
    (lx0, ly0), (lx1, ly1) = cam["light"]
    lx, ly = lx0 + (lx1 - lx0) * u, ly0 + (ly1 - ly0) * u
    yy, xx = np.ogrid[0:PH:8, 0:PW:8]
    key = 0.45 + 0.75 * np.exp(-(((xx - lx) / 1100.0) ** 2 + ((yy - ly) / 1500.0) ** 2))
    key = cv2.resize(key.astype(np.float32), (PW, PH), interpolation=cv2.INTER_LINEAR)
    c = c * key[..., None]
    # specular sweep across the finished surface
    su = (t - (DUR - 1.05)) / 0.8
    if 0 < su < 1:
        pos = -1500 + (PW + PH + 3000) * su
        d = (xx * 0.9 + yy * 0.5) - pos
        band = (np.exp(-(d / 260.0) ** 2) * math.sin(math.pi * su)).astype(np.float32)
        band = cv2.resize(band, (PW, PH), interpolation=cv2.INTER_LINEAR)
        c = c * (1 + 0.45 * (band * done)[..., None])
    return c


def rot(yaw, pitch, roll=0.0):
    a, b, g = math.radians(yaw), math.radians(pitch), math.radians(roll)
    Ry = np.array([[math.cos(a), 0, math.sin(a)], [0, 1, 0], [-math.sin(a), 0, math.cos(a)]])
    Rx = np.array([[1, 0, 0], [0, math.cos(b), -math.sin(b)], [0, math.sin(b), math.cos(b)]])
    Rz = np.array([[math.cos(g), -math.sin(g), 0], [math.sin(g), math.cos(g), 0], [0, 0, 1]])
    return Rz @ Rx @ Ry


def camera(t, cam):
    u = ease_io(t / DUR) * 0.85 + 0.15 * (t / DUR)
    lerp = lambda ab: ab[0] + (ab[1] - ab[0]) * u  # noqa: E731
    yaw, pitch, zoom = lerp(cam["yaw"]), lerp(cam["pitch"]), lerp(cam["zoom"])
    (cx0, cy0), (cx1, cy1) = cam["look"]
    cx, cy = cx0 + (cx1 - cx0) * u, cy0 + (cy1 - cy0) * u
    R = rot(yaw, pitch, lerp(cam.get("roll", (0, 0))))
    dist = 0.5
    f = W * zoom * dist

    def proj(px, py):
        X = np.array([(px - cx) / PW, (py - cy) / PW, 0.0])
        P = R @ X + np.array([0, 0, dist])
        return [f * P[0] / P[2] + W / 2, f * P[1] / P[2] + H / 2], P[2]
    src = np.float32([[0, 0], [PW, 0], [PW, PH], [0, PH]])
    dst, zs = zip(*[proj(*p) for p in src])
    Hm = cv2.getPerspectiveTransform(src, np.float32(dst))
    # depth of each plate point is linear in (px, py): z = dist + R[2,0]*X + R[2,1]*Y
    return Hm, R, cx, cy, dist


def render_frame(t, plate, pieces, cam, flat_fn, grain_seed):
    flat, done = flat_fn(t, plate, pieces)
    flat = lighting(flat, t, cam, done)
    Hm, R, cx, cy, dist = camera(t, cam)
    sharp = cv2.warpPerspective(flat, Hm, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT,
                                borderValue=(7, 7, 7))
    # depth map in screen space
    yy, xx = np.mgrid[0:PH:16, 0:PW:16].astype(np.float32)
    z = dist + R[2, 0] * (xx - cx) / PW + R[2, 1] * (yy - cy) / PW
    zf = dist + cam["focus"][0] + (cam["focus"][1] - cam["focus"][0]) * ease_io(t / DUR)
    zfull = cv2.resize(z, (PW, PH), interpolation=cv2.INTER_LINEAR)
    zs = cv2.warpPerspective(zfull, Hm, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    m = np.clip(np.abs(zs - zf) * 7.0, 0, 1) ** 1.2
    blur1 = cv2.GaussianBlur(sharp, (0, 0), 4)
    blur2 = cv2.GaussianBlur(sharp, (0, 0), 11)
    m3 = m[..., None]
    out = np.where(m3 < 0.5, sharp * (1 - 2 * m3) + blur1 * 2 * m3, blur1 * (2 - 2 * m3) + blur2 * (2 * m3 - 1))
    return look(out, grain_seed)


def look(img, seed):
    lum = img.mean(2, keepdims=True)
    x = np.clip(img / 255, 0, 1)
    x = x ** 1.08
    x = x * x * (3 - 2 * x) * 0.35 + x * 0.65           # gentle S-curve
    img = x * 255
    w = np.clip(lum / 255, 0, 1)
    img = img + (1 - w) * np.array([7, 1, -4], np.float32) + w * np.array([-6, 0, 6], np.float32)  # BGR: cool shadows, warm highs
    hl = np.clip(img.max(2) - 185, 0, None)
    bloom = cv2.GaussianBlur(hl, (0, 0), 22)
    img = img + bloom[..., None] * np.array([0.30, 0.42, 0.55], np.float32)
    yy = np.linspace(-1, 1, H)[:, None]
    xx = np.linspace(-1, 1, W)[None, :]
    vig = 1 - 0.42 * np.clip(np.sqrt(xx ** 2 * 0.9 + yy ** 2 * 0.55), 0, 1.4) ** 2.2
    img = img * vig[..., None]
    rng = np.random.default_rng(seed)
    img = img + rng.normal(0, 3.2, (H, W, 1)).astype(np.float32)
    return np.clip(img, 0, 255)


def events(name, pieces):
    if name in ("dikey", "kombo"):
        return [round(p["t0"] + p["fl"], 3) for p in pieces]
    if name == "plisse":
        return [round(p["t0"] + p["fl"], 3) for p in pieces if p["y0"] < PH]
    return [0.12, 1.87]


def render(name):
    setup, flat_fn = TYPES[name]
    plate, pieces, cam = setup()
    p = subprocess.Popen(f"ffmpeg -nostdin -v error -y -f rawvideo -pix_fmt bgr24 -s {W}x{H} -r {FPS} -i - "
                         f"-c:v libx264 -preset fast -crf 15 -pix_fmt yuv420p {D}/seg/b_{name}.mp4", shell=True,
                         stdin=subprocess.PIPE)
    for i in range(int(round(DUR * FPS))):
        fr = render_frame(i / FPS, plate, pieces, cam, flat_fn, i)
        p.stdin.write(fr.astype(np.uint8).tobytes())
    p.stdin.close()
    p.wait()
    json.dump(dict(land=events(name, pieces)), open(f"{D}/seg/b_{name}.json", "w"))
    return name


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "still":
        name = sys.argv[2]
        setup, flat_fn = TYPES[name]
        plate, pieces, cam = setup()
        ims = [cv2.resize(render_frame(float(t), plate, pieces, cam, flat_fn, 0).astype(np.uint8), (270, 480))
               for t in sys.argv[3].split(",")]
        cv2.imwrite(f"/tmp/b_{name}.jpg", np.hstack(ims))
    else:
        from multiprocessing import Pool
        with Pool(2) as pool:
            print(pool.map(render, sys.argv[1:] or list(TYPES)))
