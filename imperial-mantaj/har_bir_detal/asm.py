"""«Har bir detal — o‘z joyida» assemblies: each blind type builds itself out of its own real parts in a dark studio
void (idea from a luxury watch film the owner sent: gems and parts land one by one, then the hero).
Plates are stills of the owner's own installs; pieces are cut along the real seams / band edges / pleats.
  dikey  — lamellas drop in from above, left to right, each lands with a click-flash
  kombo  — opaque bands slide in from the left, sheer bands from the right, top to bottom (zebra)
  plisse — pleats flip open one after another from the rail down (domino cascade)
  rollo  — the fabric unrolls from the top: a lit roller runs down the frame
Then a light sweep. Writes seg/a_<type>.mp4 (DUR s) and seg/a_<type>.json (landing times for the sound).
python3 asm.py [dikey kombo plisse rollo] | still <type> <t>
"""
import json
import subprocess
import sys

import cv2
import numpy as np

D = "/home/claude/reels/yigil2"
W, H, FPS = 1080, 1920, 30
DUR = 2.9


def ease_out(u):
    u = np.clip(u, 0, 1)
    return 1 - (1 - u) ** 3


def ease_io(u):
    u = np.clip(u, 0, 1)
    return u * u * (3 - 2 * u)


def void():
    y = np.linspace(-1, 1, H)[:, None]
    x = np.linspace(-1, 1, W)[None, :]
    r = np.sqrt((x * 0.9) ** 2 + ((y + 0.1) * 0.75) ** 2)
    v = 24 * np.exp(-r ** 2 * 1.6) + 6
    return np.repeat(v[..., None], 3, 2).astype(np.float32) * np.array([1.0, 1.02, 1.06], np.float32)


VOID = void()


def grade(im):
    im = im.astype(np.float32)
    im = (im - 128) * 1.08 + 122
    y = np.linspace(-1, 1, H)[:, None]
    x = np.linspace(-1, 1, W)[None, :]
    vig = 1 - 0.28 * np.clip(np.sqrt(x ** 2 * 0.8 + y ** 2 * 0.55), 0, 1.3) ** 2
    return np.clip(im * vig[..., None], 0, 255)


def sweep(img, mask, t, t0, dur=0.65, width=170, gain=0.32):
    u = (t - t0) / dur
    if u <= 0 or u >= 1:
        return img
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    pos = -700 + (W + H + 1400) * u
    d = (xx * 0.9 + yy * 0.45) - pos
    band = np.exp(-(d / width) ** 2) * np.sin(np.pi * u)
    return np.clip(img * (1 + gain * band[..., None] * mask[..., None]), 0, 255)


def poly_mask(pts):
    m = np.zeros((H * 2, W * 2), np.uint8)
    cv2.fillPoly(m, [np.round(np.array(pts) * 2).astype(np.int32)], 255, cv2.LINE_AA)
    return cv2.resize(m, (W, H), interpolation=cv2.INTER_AREA).astype(np.float32) / 255


def place(canvas, plate, mask, dx, dy, alpha=1.0, blur=0):
    M = np.float32([[1, 0, dx], [0, 1, dy]])
    pm = cv2.warpAffine(mask, M, (W, H))
    pp = cv2.warpAffine(plate, M, (W, H))
    if blur > 1:
        k = int(blur) | 1
        kern = np.zeros((k, 1), np.float32) if abs(dy) > abs(dx) else np.zeros((1, k), np.float32)
        kern[:] = 1.0 / k
        pm = cv2.filter2D(pm, -1, kern)
        pp = cv2.filter2D(pp, -1, kern)
    a = (pm * alpha)[..., None]
    return canvas * (1 - a) + pp * a


def flash(canvas, mask, k):
    if k <= 0:
        return canvas
    e = cv2.morphologyEx((mask > 0.5).astype(np.uint8), cv2.MORPH_GRADIENT, np.ones((3, 3), np.uint8)).astype(np.float32)
    e = cv2.GaussianBlur(e, (0, 0), 2.2) * 2.5
    return np.clip(canvas + np.clip(e, 0, 1)[..., None] * 220 * k, 0, 255)


# ---------------------------------------------------------------- dikey
def dikey_setup():
    plate = grade(cv2.imread(f"{D}/src/dikey_plate.png"))
    seams = [(0, 0), (140, 140), (283, 271), (448, 446), (620, 608), (791, 764), (968, 935), (W, W)]
    pieces = []
    for k in range(len(seams) - 1):
        (a0, a1), (b0, b1) = seams[k], seams[k + 1]
        x = lambda xt, xb, y: xt + (xb - xt) * (y - 250) / 1400  # noqa: E731
        pts = [(x(a0, a1, -10), -10), (x(b0, b1, -10), -10), (x(b0, b1, H + 10), H + 10), (x(a0, a1, H + 10), H + 10)]
        pieces.append(dict(mask=poly_mask(pts), t0=0.12 + 0.2 * k, fl=0.5))
    return plate, pieces


def dikey_frame(t, plate, pieces):
    c = VOID.copy()
    full = np.zeros((H, W), np.float32)
    for p in pieces:
        u = (t - p["t0"]) / p["fl"]
        if u <= 0:
            continue
        e = ease_out(u)
        dy = -(H + 80) * (1 - e)
        vel = (H + 80) * 3 * (1 - min(u, 1)) ** 2 / p["fl"] / FPS
        c = place(c, plate, p["mask"], 0, dy, alpha=min(1, u * 4), blur=min(vel * 0.5, 61) if u < 1 else 0)
        c = flash(c, p["mask"], max(0, 1 - (t - p["t0"] - p["fl"] * 0.75) / 0.25) if u > 0.75 else 0)
        if u >= 1:
            full = np.maximum(full, p["mask"])
    return sweep(c, full, t, 1.85)


# ---------------------------------------------------------------- kombo
KE = [(86, 180), (250, 330), (442, 505), (603, 643), (804, 827), (950, 962), (1152, 1146), (1302, 1282), (1508, 1472),
      (1660, 1615), (1855, 1804)]


def kombo_setup():
    plate = grade(cv2.imread(f"{D}/src/kombo_plate.png"))
    ys = lambda e, x: e[0] + (e[1] - e[0]) * (x - 210) / 640  # noqa: E731
    edges = [(-400, -400)] + KE + [(H + 400, H + 400)]
    pieces = []
    for k in range(len(edges) - 1):
        a, b = edges[k], edges[k + 1]
        pts = [(-10, ys(a, -10)), (W + 10, ys(a, W + 10)), (W + 10, ys(b, W + 10)), (-10, ys(b, -10))]
        dark = k % 2 == 0
        pieces.append(dict(mask=poly_mask(pts), t0=0.1 + 0.13 * k, fl=0.55, side=-1 if dark else 1))
    return plate, pieces


def kombo_frame(t, plate, pieces):
    c = VOID.copy()
    full = np.zeros((H, W), np.float32)
    for p in pieces:
        u = (t - p["t0"]) / p["fl"]
        if u <= 0:
            continue
        e = ease_out(u)
        dx = p["side"] * (W + 60) * (1 - e)
        vel = (W + 60) * 3 * (1 - min(u, 1)) ** 2 / p["fl"] / FPS
        c = place(c, plate, p["mask"], dx, 0, alpha=min(1, u * 4), blur=min(vel * 0.5, 61) if u < 1 else 0)
        c = flash(c, p["mask"], max(0, 1 - (t - p["t0"] - p["fl"] * 0.75) / 0.25) if u > 0.75 else 0)
        if u >= 1:
            full = np.maximum(full, p["mask"])
    return sweep(c, full, t, 1.95)


# ---------------------------------------------------------------- plisse
PER = 76.8


def plisse_setup():
    plate = grade(cv2.imread(f"{D}/src/plisse_plate.png"))
    n = int(np.ceil(H / PER)) + 1
    return plate, [dict(y0=k * PER, t0=0.12 + 0.062 * k, fl=0.32) for k in range(n)]


def plisse_frame(t, plate, pieces):
    c = VOID.copy()
    done = 0.0
    for p in pieces:
        u = (t - p["t0"]) / p["fl"]
        if u <= 0:
            continue
        y0 = int(round(p["y0"]))
        y1 = int(round(min(H, p["y0"] + PER)))
        if y1 <= y0:
            continue
        e = ease_out(u)
        hh = max(1, int(round((y1 - y0) * e)))
        band = plate[y0:y1]
        sq = cv2.resize(band, (W, hh), interpolation=cv2.INTER_AREA)
        shade = 0.45 + 0.55 * e
        grad = np.linspace(1.15, 0.8, hh)[:, None, None] if u < 1 else 1.0
        c[y0:y0 + hh] = np.clip(sq * shade * grad, 0, 255)
        if 0.6 < u < 1.6:
            k = max(0, 1 - abs(u - 1.0) / 0.6)
            yb = min(H - 1, y0 + hh - 1)
            c[max(0, yb - 1):yb + 2] = np.clip(c[max(0, yb - 1):yb + 2] + 160 * k, 0, 255)
        if u >= 1:
            done = max(done, y1)
    full = np.zeros((H, W), np.float32)
    full[: int(done)] = 1
    return sweep(c, full, t, 2.05)


# ---------------------------------------------------------------- rollo
def rollo_setup():
    return grade(cv2.imread(f"{D}/src/rollo_plate.png")), None


def rollo_frame(t, plate, _):
    c = VOID.copy()
    u = ease_io((t - 0.12) / 1.75)
    front = int(round(-90 + (H + 90) * u))
    R = 46
    if front > 0:
        c[:min(H, front)] = plate[:min(H, front)]
    # roller: a cylinder of rolled fabric at the front
    y0, y1 = front, front + 2 * R
    if y1 > 0 and y0 < H:
        src = plate[max(0, min(H - 2 * R, front)):max(0, min(H - 2 * R, front)) + 2 * R]
        if len(src) == 2 * R:
            yy = np.linspace(-1, 1, 2 * R)
            shade = (0.35 + 0.75 * np.sqrt(np.clip(1 - yy ** 2, 0, 1)))[:, None, None]
            spec = (np.exp(-((yy + 0.35) / 0.12) ** 2) * 70)[:, None, None]
            cyl = np.clip(src * shade + spec, 0, 255)
            a, b = max(0, y0), min(H, y1)
            c[a:b] = cyl[a - y0:b - y0]
            sh = slice(min(H, y1), min(H, y1 + 40))
            c[sh] = c[sh] * np.linspace(0.55, 1, sh.stop - sh.start)[:, None, None]
    full = np.zeros((H, W), np.float32)
    full[: max(0, min(H, front))] = 1
    return sweep(c, full, t, 2.0)


TYPES = {"dikey": (dikey_setup, dikey_frame), "kombo": (kombo_setup, kombo_frame),
         "plisse": (plisse_setup, plisse_frame), "rollo": (rollo_setup, rollo_frame)}


def events(name, pieces):
    if name in ("dikey", "kombo"):
        return [round(p["t0"] + p["fl"] * 0.8, 3) for p in pieces]
    if name == "plisse":
        return [round(p["t0"] + p["fl"], 3) for p in pieces if p["y0"] < H]
    return [0.12, 1.87]


def render(name):
    setup, fn = TYPES[name]
    plate, pieces = setup()
    p = subprocess.Popen(f"ffmpeg -nostdin -v error -y -f rawvideo -pix_fmt bgr24 -s {W}x{H} -r {FPS} -i - "
                         f"-c:v libx264 -preset fast -crf 15 -pix_fmt yuv420p {D}/seg/a_{name}.mp4", shell=True,
                         stdin=subprocess.PIPE)
    for i in range(int(round(DUR * FPS))):
        p.stdin.write(np.clip(fn(i / FPS, plate, pieces), 0, 255).astype(np.uint8).tobytes())
    p.stdin.close()
    p.wait()
    json.dump(dict(land=events(name, pieces) if pieces else events(name, None)), open(f"{D}/seg/a_{name}.json", "w"))
    return name


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "still":
        name = sys.argv[2]
        setup, fn = TYPES[name]
        plate, pieces = setup()
        ims = [cv2.resize(np.clip(fn(float(t), plate, pieces), 0, 255).astype(np.uint8), (270, 480))
               for t in sys.argv[3].split(",")]
        cv2.imwrite(f"/tmp/st_{name}.jpg", np.hstack(ims))
    else:
        from multiprocessing import Pool
        with Pool(2) as pool:
            print(pool.map(render, sys.argv[1:] or list(TYPES)))
