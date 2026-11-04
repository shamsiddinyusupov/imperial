"""«Kombo yig‘iladi» — the grey kombo assembles itself on an empty, sun-blown window (reference: facade mouldings flying in).

Work space = seg/wide.png: frame 1.9 s of IMG_5681 at 1296x2304, tone-mapped + neutral gains (no look yet).
Pieces are cut from that plate along the stripe edges (geom.py -> seg/edges_raw.json), so when every piece has landed
and the light has gone from day to evening the picture is the plate again, and the camera ends exactly on frame 0 of
the stabilised real shot (seg/real.mp4, eased start) -> a cut there is invisible.

python3 vfx.py prep      # masks, empty window, day look -> seg/*.npy / *.png
python3 vfx.py still T   # one test frame at T seconds -> frames_test/T.jpg
python3 vfx.py render    # seg/vfx.mp4 (0 .. T_SW)
"""
import json
import math
import os
import subprocess
import sys

import cv2
import numpy as np

D = "/home/claude/reels/kombo_yigil"
WW, WH = 1296, 2304          # work space
OW, OH = 1080, 1920
FPS = 30
T_SW = 10.2                  # cut to the real shot
LOOK_N = ("huesaturation=saturation=-0.85:colors=c+b:strength=8,curves=all='0/0.03 0.25/0.245 0.5/0.52 0.75/0.79 1/0.975',"
          "eq=saturation=0.97,vignette=angle=PI/9,noise=alls=4:allf=t")

E = json.load(open(f"{D}/seg/edges_raw.json"))


def line(key, dy=0.0):
    c = E[key]["c"]
    return lambda x: np.polyval(c, x) + dy


CAS_TOP = line("neg_336", -1)
CUTS = [line(k) for k in ("neg_417", "neg_546", "neg_675", "neg_803", "neg_931", "neg_1060", "neg_1190", "neg_1322",
                          "neg_1456", "neg_1594", "neg_1736", "neg_1881", "neg_2010")]
LIGHT_TOP = [line(k) for k in ("pos_468", "pos_598", "pos_727", "pos_855", "pos_983", "pos_1112", "pos_1243", "pos_1376",
                               "pos_1511", "pos_1651", "pos_1794", "pos_1939")]
BAR_BOT = line("pos_2049", 1)
R = lambda y: 1211.83 + 0.027576 * y + 1.0          # fabric right edge
CAS_R, BAR_R, CHAIN_W = 1257, 1281, 48

X = np.arange(WW, dtype=np.float32)[None, :]
Y = np.arange(WH, dtype=np.float32)[:, None]


def below(f):
    """Coverage (0..1) of 'y is below line f(x)', anti-aliased."""
    return np.clip(Y - f(X) + 0.5, 0, 1)


def left_of(xr):
    return np.clip(xr - X + 0.5, 0, 1)


def ease(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


def ease5(x):
    x = min(1.0, max(0.0, x))
    return x * x * x * (x * (6 * x - 15) + 10)


def out_back(p, s):
    p = min(1.0, max(0.0, p))
    q = p - 1
    return 1 + (s + 1) * q ** 3 + s * q ** 2


# ------------------------------------------------------------------ prep
def prep():
    plate = cv2.imread(f"{D}/seg/wide.png").astype(np.float32)
    Rx = R(Y) * np.ones_like(X)
    rows_cas = below(CAS_TOP) - below(CUTS[0])
    m_cas = rows_cas * left_of(CAS_R)
    bands = [(below(CUTS[k]) - below(CUTS[k + 1])) * left_of(Rx) for k in range(12)]
    rows_bar = below(CUTS[12]) - below(BAR_BOT)
    m_bar = rows_bar * left_of(BAR_R)
    chain_rows = below(CUTS[0]) - below(CUTS[12])
    m_chain = chain_rows * np.clip(X - Rx + 0.5, 0, 1) * left_of(np.minimum(Rx + CHAIN_W, WW))
    M = np.clip(m_cas + sum(bands) + m_bar + m_chain, 0, 1)

    # window area: left of the fabric edge, from the cassette top to the bar's shadow
    win = (below(CAS_TOP) - below(BAR_BOT)) * left_of(Rx)
    # wall to rebuild: inside M but right of the fabric edge
    wall = np.clip(M - win, 0, 1)
    hole = (wall > 0.02).astype(np.uint8) * 255
    hole = cv2.dilate(hole, np.ones((5, 5), np.uint8))
    hm = (hole > 0).astype(np.float32)
    # low frequencies: normalised convolution from the wall only (never from the blind)
    valid = (1 - hm) * (1 - (cv2.dilate((M > 0.02).astype(np.uint8), np.ones((7, 7), np.uint8)) > 0))
    valid = valid.astype(np.float32)
    low = None
    for sg in (240, 90, 26):                       # coarse first, finer where there is enough wall nearby
        num = cv2.GaussianBlur(plate * valid[..., None], (0, 0), sg)
        den = cv2.GaussianBlur(valid, (0, 0), sg)[..., None]
        est = num / np.maximum(den, 1e-4)
        w = np.clip((den - 0.02) / 0.10, 0, 1)
        low = est if low is None else est * w + low * (1 - w)
    # high frequencies: the brick wallpaper from under the sill, laid in courses with a half-brick offset
    row = plate[2168:2286, 990:1240]
    hp = row - cv2.GaussianBlur(row, (0, 0), 7)
    courses = []
    for k in range(WH // hp.shape[0] + 1):
        courses.append(np.roll(hp, 95 * (k % 2), axis=1))
    tex = np.tile(np.concatenate(courses, 0), (1, 6, 1))[:WH, :WW]
    filled = plate * (1 - hm[..., None]) + (low + tex * 0.8) * hm[..., None]
    filled = cv2.GaussianBlur(filled, (0, 0), 0.6) * hm[..., None] + filled * (1 - hm[..., None])

    # --- the empty window, blown out by the sun
    xm = lambda y: 612 + 0.027576 * (y - 1300)                 # mullion centre, same lean as the fabric edge
    dt = Y - CAS_TOP(X)
    db = BAR_BOT(X) - Y
    dr = Rx - X
    dm = np.abs(X - xm(Y) * np.ones_like(X))
    d_frame = np.minimum(np.minimum(dt - 64, db - 54), np.minimum(dr - 62, dm - 50))   # <0 -> frame, >0 -> glass
    glass = np.clip(d_frame + 0.5, 0, 1) * win
    frame = win - glass
    # frame shading: light PVC seen against the light, bead shadow on the glass edge, sash line inside
    fr = np.full((WH, WW, 3), (186, 189, 192), np.float32)
    fr += ((Y / WH) * -10)[..., None]
    edge_hi = np.exp(-((d_frame + 60.0) ** 2) / 40.0)[..., None]
    bead = np.exp(-((d_frame + 2.5) ** 2) / 5.0)[..., None]
    sash = np.exp(-((d_frame + 34.0) ** 2) / 4.0)[..., None]
    seam = np.exp(-(((X - xm(Y)) ** 2) / 1.5))[..., None]
    fr = fr + edge_hi * 10 - bead * 58 - sash * 22 - seam * 50 * (frame[..., None] > 0.5)
    # a window handle on the right sash, by the mullion
    hx, hy = xm(1300.0) + 72, 1240.0
    handle = np.zeros((WH, WW), np.uint8)
    cv2.ellipse(handle, (int(hx), int(hy)), (13, 34), 0, 0, 360, 255, -1, cv2.LINE_AA)
    cv2.rectangle(handle, (int(hx - 9), int(hy)), (int(hx + 9), int(hy + 150)), 255, -1, cv2.LINE_AA)
    handle = cv2.GaussianBlur(handle.astype(np.float32) / 255, (0, 0), 1.2)
    hsh = cv2.GaussianBlur(np.roll(np.roll(handle, 10, 0), 7, 1), (0, 0), 6)
    # glass: blown-out sky, a pale soft skyline far away
    gl = np.empty((WH, WW, 3), np.float32)
    v = np.clip((Y - 300) / 1700, 0, 1) * np.ones_like(X)
    gl[..., 0] = 251 + 4 * v
    gl[..., 1] = 249 + 6 * v
    gl[..., 2] = 246 + 9 * v
    xs = X[0]
    sky = 1450 + 70 * np.sin(xs / 97.0) + 45 * np.sin(xs / 41.0 + 1.3) + 30 * np.sin(xs / 23.0 + 0.4)
    trees = np.clip((Y - sky[None, :]) / 40.0, 0, 1)
    trees = cv2.GaussianBlur(trees.astype(np.float32), (0, 0), 14)
    rng2 = np.random.default_rng(11)
    leaf = cv2.GaussianBlur(rng2.normal(0, 1, (WH, WW)).astype(np.float32), (0, 0), 9) * 40
    trees = np.clip(trees + leaf * trees * (1 - trees) * 0.02, 0, 1)
    gl = gl - (trees * 22)[..., None] * np.array((0.9, 1.0, 1.05), np.float32)
    gl = gl - (np.exp(-np.maximum(d_frame, 0) / 22.0) * 14)[..., None]       # a little shade by the frame
    gl = gl * (1 - 0.5 * hsh[..., None])
    fr = fr * (1 - handle[..., None]) + np.array((200, 202, 204), np.float32) * handle[..., None]
    glass = glass * (1 - handle)
    frame = win - glass
    empty = filled * (1 - win[..., None]) + fr * frame[..., None] + gl * glass[..., None]

    # --- day look of the fabric: the sheer stripes lit from behind
    sheer = np.zeros((WH, WW), np.float32)
    for k in range(12):
        sheer += (below(CUTS[k]) - below(LIGHT_TOP[k]))
    sheer = np.clip(sheer, 0, 1) * left_of(Rx)
    tint = np.array((0.985, 0.995, 1.0), np.float32)       # BGR: a touch warm
    day = plate.copy()
    lit = (255 - (255 - plate) * 0.34) * tint
    day = day * (1 - sheer[..., None]) + lit * sheer[..., None]
    opaque = np.clip(sum(bands) - sheer, 0, 1)
    day = day * (1 - 0.08 * opaque[..., None])

    os.makedirs(f"{D}/seg/prep", exist_ok=True)
    np.save(f"{D}/seg/prep/plate.npy", plate)
    np.save(f"{D}/seg/prep/empty.npy", np.clip(empty, 0, 255).astype(np.float32))
    np.save(f"{D}/seg/prep/day.npy", np.clip(day, 0, 255).astype(np.float32))
    np.save(f"{D}/seg/prep/masks.npy", np.stack([m_cas] + bands + [m_bar, m_chain]).astype(np.float32))
    np.save(f"{D}/seg/prep/glass.npy", glass.astype(np.float32))
    np.save(f"{D}/seg/prep/sheer.npy", sheer.astype(np.float32))
    np.save(f"{D}/seg/prep/M.npy", M.astype(np.float32))
    cv2.imwrite(f"{D}/seg/prep/empty.jpg", np.clip(empty, 0, 255).astype(np.uint8))
    cv2.imwrite(f"{D}/seg/prep/day.jpg", np.clip(day, 0, 255).astype(np.uint8))
    print("prep ok, M sum", float(M.sum()), "chain px", float(m_chain.sum()))


# ------------------------------------------------------------------ timeline of pieces
# (index into masks, t0, dur, start offset dx, dy, start scale, start rotation deg, overshoot, landing shake px)
PIECES = [(0, 2.35, 0.80, 0, -560, 1.10, 0.0, 0.55, 5.0)]
for k in range(12):
    side = -1 if k % 2 == 0 else 1
    PIECES.append((1 + k, 3.25 + 0.22 * k, 0.62, side * 1480, -40, 1.10, side * 3.0, 0.45, 0.0))
PIECES.append((13, 6.15, 0.70, 0, 540, 1.08, 0.0, 0.55, 3.0))
PIECES.append((14, 6.60, 0.60, 0, -1750, 1.00, 0.0, 0.0, 0.0))     # chain + its shadow slides down
EVE0, EVE1 = 8.55, 9.95                                              # day -> evening
SHEEN0, SHEEN1 = 7.05, 7.95


class Scene:
    def __init__(self):
        P = f"{D}/seg/prep"
        self.plate = np.load(f"{P}/plate.npy")
        self.empty = np.load(f"{P}/empty.npy")
        self.day = np.load(f"{P}/day.npy")
        self.masks = np.load(f"{P}/masks.npy")
        self.glass = np.load(f"{P}/glass.npy")
        self.sheer = np.load(f"{P}/sheer.npy")
        self.M = np.load(f"{P}/M.npy")
        diff = np.abs(self.plate - self.empty).max(-1)
        self.chain_soft = np.clip((diff - 6) / 30, 0, 1) * self.masks[14]
        self.boxes = []
        for m in self.masks:
            ys, xs = np.where(m > 0.001)
            self.boxes.append((max(0, xs.min() - 2), max(0, ys.min() - 2), min(WW, xs.max() + 3), min(WH, ys.max() + 3)))
        W0 = np.load(f"{D}/seg/real_W0.npy")
        self.C_end = np.array([[1, 0, -(WW - OW) / 2], [0, 1, -(WH - OH) / 2], [0, 0, 1]]) @ W0

    # camera: wide (a hair pushed) -> exactly the real shot's first frame
    def camera(self, t):
        s0, a0, c0 = (OW / WW) * 1.035, 0.0, np.array([WW / 2, WH / 2])
        Ce = self.C_end
        s1 = math.hypot(Ce[0, 0], Ce[1, 0])
        a1 = math.atan2(Ce[1, 0], Ce[0, 0])
        c1 = np.linalg.solve(Ce[:2, :2], np.array([OW / 2, OH / 2]) - Ce[:2, 2])
        u = ease5(t / T_SW) * 0.85 + ease(t / T_SW) * 0.15
        s = s0 * (s1 / s0) ** u
        a = a0 + (a1 - a0) * u
        c = c0 + (c1 - c0) * u
        sh = 0.0
        for (_, t0, dur, *_rest, shake) in PIECES:
            tl = t0 + dur * 0.62
            if shake and t > tl:
                sh += shake * math.exp(-(t - tl) / 0.11) * math.sin(2 * math.pi * 13 * (t - tl))
        ca, sa = math.cos(a) * s, math.sin(a) * s
        M = np.array([[ca, -sa, 0], [sa, ca, 0]], np.float64)
        M[:, 2] = np.array([OW / 2, OH / 2 + sh]) - M[:, :2] @ c
        return M

    def blind(self, t):
        e = ease((t - EVE0) / (EVE1 - EVE0))
        return self.day * (1 - e) + self.plate * e, e

    def piece_state(self, i, t):
        idx, t0, dur, dx, dy, sc, rot, ov, _ = PIECES[i]
        p = (t - t0) / dur
        if p <= 0:
            return None
        f = out_back(p, ov) if ov > 0 else 1 - (1 - min(1.0, p)) ** 3
        g = 1 - f
        return dict(dx=dx * g, dy=dy * g, s=1 + (sc - 1) * max(0.0, g), r=rot * g, a=min(1.0, p / 0.12), landed=p >= 1)

    def frame(self, t):
        src, e = self.blind(t)
        out = self.empty.copy()
        land_c = np.zeros_like(out)
        land_a = np.zeros(out.shape[:2], np.float32)
        flying = []
        cover = np.zeros(out.shape[:2], np.float32)
        for i, P in enumerate(PIECES):
            idx = P[0]
            st = self.piece_state(i, t)
            if st is None:
                continue
            m = self.chain_soft if idx == 14 and not st["landed"] else self.masks[idx]
            if idx == 14 and st["landed"]:
                k = ease((t - P[1] - P[2]) / 0.3)
                m = self.chain_soft * (1 - k) + self.masks[idx] * k
            img = self.plate if idx in (0, 13, 14) else src
            if st["landed"]:
                x0, y0, x1, y1 = self.boxes[idx]
                land_c[y0:y1, x0:x1] += img[y0:y1, x0:x1] * m[y0:y1, x0:x1, None]
                land_a[y0:y1, x0:x1] += m[y0:y1, x0:x1]
            else:
                flying.append((i, idx, img, m))
        land_a = np.clip(land_a, 0, 1)
        out = out * (1 - land_a[..., None]) + land_c
        cover += land_a
        for i, idx, img, m in flying:
            out, cov = self.draw_flying(out, i, idx, img, m, t)
            cover = np.maximum(cover, cov)
        # sheen across the finished blind
        if SHEEN0 < t < SHEEN1:
            p = (t - SHEEN0) / (SHEEN1 - SHEEN0)
            xc = -500 + 2400 * ease(p)
            band = np.exp(-(((X + (Y - 1200) * 0.45) - xc) ** 2) / (2 * 140 ** 2))
            out += (band * self.M * 26 * math.sin(math.pi * p))[..., None]
        # sun: bloom from whatever glass is still visible + the sheer stripes glowing in the day
        gv = self.glass * (1 - np.clip(cover, 0, 1))
        vis = float(gv.sum() / (self.glass.sum() + 1e-6))
        # the phone exposes for the bright window: the room sinks while the glass is open, comes back as it is covered
        out = out * (1 - 0.26 * vis * (1 - gv))[..., None] + (np.array((246, 252, 255), np.float32) - out) * \
            (gv * 0.9)[..., None]
        light = gv + self.sheer * np.clip(cover, 0, 1) * 0.20 * (1 - e)
        small = cv2.resize(light, (WW // 4, WH // 4), interpolation=cv2.INTER_AREA)
        b = cv2.GaussianBlur(small, (0, 0), 6) * 0.12 + cv2.GaussianBlur(small, (0, 0), 30) * 0.30 + \
            cv2.GaussianBlur(small, (0, 0), 90) * 0.28
        b = cv2.resize(b, (WW, WH), interpolation=cv2.INTER_CUBIC)
        b = np.clip(b, 0, 1)[..., None]
        tintb = np.array((236, 246, 255), np.float32)      # BGR warm sunlight
        out = out + b * (tintb - out * 0.6) * 0.85
        return np.clip(out, 0, 255)

    def draw_flying(self, out, i, idx, img, m, t):
        x0, y0, x1, y1 = self.boxes[idx]
        crop = np.concatenate([img[y0:y1, x0:x1] * m[y0:y1, x0:x1, None], m[y0:y1, x0:x1, None]], -1).astype(np.float32)
        acc = np.zeros((WH, WW, 4), np.float32)
        shadow = np.zeros((WH, WW), np.float32)
        st_a = self.piece_state(i, t - 0.275 / FPS)
        st_b = self.piece_state(i, t + 0.275 / FPS)
        if st_a is None:
            st_a = st_b
        travel = math.hypot(st_b["dx"] - st_a["dx"], st_b["dy"] - st_a["dy"]) if st_b else 0.0
        N = int(min(40, max(3, travel / 6)))
        depth = 0.0
        for j in range(N):
            ts = t + (j / (N - 1) - 0.5) * 0.55 / FPS
            st = self.piece_state(i, ts)
            if st is None:
                continue
            cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
            a = math.radians(st["r"])
            ca, sa = math.cos(a) * st["s"], math.sin(a) * st["s"]
            A = np.array([[ca, -sa, 0], [sa, ca, 0]], np.float64)
            # crop coords -> work: about the piece centre, then offset
            A[:, 2] = np.array([cx + st["dx"], cy + st["dy"]]) - A[:, :2] @ np.array([cx - x0, cy - y0])
            w = cv2.warpAffine(crop, A, (WW, WH), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
            acc += w * st["a"]
            depth = max(depth, (st["s"] - 1) / 0.10)
            As = A.copy()
            As[:, 2] += (8 * depth, 30 * depth + 6)
            shadow += cv2.warpAffine(np.ascontiguousarray(crop[..., 3]), As, (WW, WH), flags=cv2.INTER_LINEAR) * st["a"]
        acc /= N
        shadow /= N
        if depth > 0.01:
            sm = cv2.resize(shadow, (WW // 4, WH // 4), interpolation=cv2.INTER_AREA)
            sm = cv2.resize(cv2.GaussianBlur(sm, (0, 0), 3 + 4 * depth), (WW, WH), interpolation=cv2.INTER_LINEAR)
            out = out * (1 - (0.30 * min(1.0, depth) * sm)[..., None])
        al = np.clip(acc[..., 3], 0, 1)
        out = out * (1 - al[..., None]) + acc[..., :3]
        return out, al

    def output(self, t):
        fr = self.frame(t)
        Mc = self.camera(t)
        return cv2.warpAffine(fr.astype(np.float32), Mc, (OW, OH), flags=cv2.INTER_LANCZOS4,
                              borderMode=cv2.BORDER_REFLECT)


SC = None


def _init():
    global SC
    SC = Scene()


def _job(n):
    return np.clip(SC.output(n / FPS), 0, 255).astype(np.uint8).tobytes()


def render():
    n = round(T_SW * FPS)
    vf = f"{LOOK_N},unsharp=5:5:0.3,setsar=1"
    out = f"{D}/seg/vfx.mp4"
    enc = subprocess.Popen(["ffmpeg", "-nostdin", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s",
                            f"{OW}x{OH}", "-r", str(FPS), "-i", "-", "-vf", vf, "-c:v", "libx264", "-preset", "fast",
                            "-crf", "14", "-pix_fmt", "yuv420p", "-r", str(FPS), out + ".tmp.mp4"], stdin=subprocess.PIPE)
    from multiprocessing import Pool
    with Pool(4, initializer=_init) as p:
        for k, b in enumerate(p.imap(_job, range(n), chunksize=2)):
            enc.stdin.write(b)
            if k % 60 == 0:
                print("frame", k, flush=True)
    enc.stdin.close()
    if enc.wait() == 0:
        os.replace(out + ".tmp.mp4", out)
    print("vfx ok", n)


def still(ts):
    sc = Scene()
    os.makedirs(f"{D}/frames_test", exist_ok=True)
    for t in ts:
        cv2.imwrite(f"{D}/frames_test/{t:05.2f}.jpg", np.clip(sc.output(t), 0, 255).astype(np.uint8), [cv2.IMWRITE_JPEG_QUALITY, 90])


if __name__ == "__main__":
    what = sys.argv[1]
    if what == "prep":
        prep()
    elif what == "still":
        still([float(v) for v in sys.argv[2:]])
    elif what == "render":
        render()
