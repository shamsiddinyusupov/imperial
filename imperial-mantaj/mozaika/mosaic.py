"""«Quyosh — har bir derazada» (JALYUZI CLASSIC, owner 22.11): one real window (IMG_3416, peach plisse in the sun)
pulls back into a photo-mosaic of ~550 frames of the owner's plisse installs; as the camera rises the tiles take the
tone of their cell and the Jalyuzi Classic emblem (sun over slats) appears, made of windows. A light sweeps the sun,
the mosaic resolves into the crisp logo, end card. Music: steelpan_bed (#24).
python3 mosaic.py [layout|prev t,t,..|frames|music|final|cover|all]
"""
import json
import os
import subprocess
import sys
from multiprocessing import Pool

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, "/home/claude/reels/common")
sys.path.insert(0, "/home/claude/reels/common/brand")
from classic_style import CREAM, INK, MED, ORANGE, SEMI, SER, SERI, text  # noqa: E402
from brand import PHONE  # noqa: E402

D = "/home/claude/reels/mozaika"
W, H, FPS = 1080, 1920, 30
COLS, ROWS = 36, 51
P_END = 30.0                         # pitch (px per cell) when the whole mosaic is visible
GAPF = 0.07
BG = np.array([30, 27, 25], np.float32)
GAPC = np.array([16, 14, 13], np.uint8)
LOGO = Image.open("/home/claude/reels/common/brand/classic_logo.png").convert("RGBA")
EMB_BOX = (423, 1, 836, 426)         # emblem bbox inside the logo png
EMB_COLS = 28
EXCL = {"522_1", "523_0", "523_1", "564_0", "565_0", "611_0", "611_1", "602_1", "717_0", "719_1", "562_0", "315_0",
        "315_1"}
HERO_SRC = 612
# ---- timeline ----
T_Z0, T_Z1 = 2.0, 10.4               # pull back
T_SWEEP = 10.9
T_CRISP0, T_CRISP1 = 13.3, 14.3      # mosaic -> crisp emblem
T_SHR0, T_SHR1 = 14.3, 15.3          # emblem -> logo layout
S_END = 15.2
TOTAL = 21.6
NF = int(round(TOTAL * FPS))
ENC = "-c:v libx264 -preset fast -crf 15 -pix_fmt yuv420p"


def ease(u):
    u = np.clip(u, 0, 1)
    return u * u * (3 - 2 * u)


def ease_io(u):
    u = float(np.clip(u, 0, 1))
    return 4 * u ** 3 if u < 0.5 else 1 - (-2 * u + 2) ** 3 / 2


def a_in(t, t0, d=0.45):
    return float(ease((t - t0) / d))


def a_out(t, t1, d=0.35):
    return float(1 - ease((t - t1) / d))


# ---------------- layout ----------------
def emblem_geom():
    ew = EMB_COLS * P_END
    eh = ew * (EMB_BOX[3] - EMB_BOX[1]) / (EMB_BOX[2] - EMB_BOX[0])
    ex = (W - ew) / 2
    ey = 300
    return ex, ey, ew, eh


def build_layout():
    lib = json.load(open(f"{D}/lib.json"))
    paths = []
    for sid, ps in lib.items():
        if int(sid) == HERO_SRC:
            continue
        for p in ps:
            if os.path.exists(p) and os.path.getsize(p) > 2000 and os.path.basename(p)[:-4] not in EXCL:
                paths.append(p)
    labs, lums = [], []
    for p in paths:
        im = cv2.imread(p)
        lab = cv2.cvtColor(im, cv2.COLOR_BGR2LAB).reshape(-1, 3).astype(np.float32).mean(0)
        labs.append(lab)
        lums.append(float(cv2.cvtColor(im, cv2.COLOR_BGR2GRAY).mean()))
    labs = np.array(labs)
    # target: emblem over a dark ground, sampled per cell at the final pitch
    ex, ey, ew, eh = emblem_geom()
    emb = LOGO.crop(EMB_BOX).resize((int(ew), int(eh)), Image.LANCZOS)
    canvas = Image.new("RGBA", (W, int(ROWS * P_END * 1.25)), tuple(int(v) for v in BG) + (255,))
    canvas.alpha_composite(emb, (int(ex), int(ey)))
    cv = np.asarray(canvas.convert("RGB")).astype(np.float32)
    cov_img = np.zeros(cv.shape[:2], np.float32)
    cov_img[int(ey):int(ey) + emb.height, int(ex):int(ex) + emb.width] = np.asarray(emb)[..., 3] / 255.0
    tgt, cov = np.zeros((ROWS, COLS, 3), np.float32), np.zeros((ROWS, COLS), np.float32)
    ph = P_END * 1.25
    for r in range(ROWS):
        for c in range(COLS):
            y0, y1, x0, x1 = int(r * ph), int((r + 1) * ph), int(c * P_END), int((c + 1) * P_END)
            tgt[r, c] = cv[y0:y1, x0:x1].reshape(-1, 3).mean(0)
            cov[r, c] = cov_img[y0:y1, x0:x1].mean()
    tlab = cv2.cvtColor(np.clip(tgt, 0, 255).astype(np.uint8).reshape(1, -1, 3)[..., ::-1], cv2.COLOR_BGR2LAB)
    tlab = tlab.reshape(ROWS, COLS, 3).astype(np.float32)
    # hero: a sun cell near the disc centre
    sun = [(r, c) for r in range(ROWS) for c in range(COLS) if cov[r, c] > 0.9 and tgt[r, c][0] > 200]
    cy = np.mean([r for r, _ in sun]) - 2
    cx = np.mean([c for _, c in sun])
    hero = min(sun, key=lambda rc: (rc[0] - cy) ** 2 + (rc[1] - cx) ** 2)
    use = np.zeros(len(paths))
    assign = [[None] * COLS for _ in range(ROWS)]
    src_of = lambda p: os.path.basename(p).split("_")[0]
    order = sorted(((r, c) for r in range(ROWS) for c in range(COLS)),
                   key=lambda rc: (-cov[rc], abs(rc[0] - hero[0]) + abs(rc[1] - hero[1])))
    rng = np.random.default_rng(7)
    for r, c in order:
        if (r, c) == hero:
            continue
        d = np.abs(labs[:, 0] - tlab[r, c, 0]) * (1.0 if cov[r, c] > 0.3 else 0.6) + \
            np.hypot(labs[:, 1] - tlab[r, c, 1], labs[:, 2] - tlab[r, c, 2]) * (1.6 if cov[r, c] > 0.3 else 0.3)
        d = d + use * (6.0 if cov[r, c] > 0.3 else 2.5) + rng.uniform(0, 4, len(paths))
        near = {src_of(assign[rr][cc]) for rr in range(max(0, r - 2), min(ROWS, r + 3))
                for cc in range(max(0, c - 2), min(COLS, c + 3)) if assign[rr][cc]}
        for k in np.argsort(d)[:60]:
            if src_of(paths[k]) not in near:
                break
        assign[r][c] = paths[k]
        use[k] += 1
    lay = dict(hero=hero, assign=assign, tgt=tgt.tolist(), cov=cov.tolist(), ex=ex, ey=ey, ew=ew, eh=eh)
    json.dump(lay, open(f"{D}/layout.json", "w"))
    print("hero", hero, "tiles", len(paths), "max reuse", int(use.max()), "unused", int((use == 0).sum()))
    # hi-res neighbours (visible big at the start)
    items = {str(i["id"]): i for i in json.load(open("/home/claude/baza_work/items.json"))}
    os.makedirs(f"{D}/hi", exist_ok=True)
    TM = ("zscale=t=linear:npl=203,format=gbrpf32le,zscale=p=bt709,tonemap=hable:desat=0,"
          "zscale=t=bt709:m=bt709:r=tv,format=yuv420p")
    for r in range(hero[0] - 2, hero[0] + 3):
        for c in range(hero[1] - 2, hero[1] + 3):
            if (r, c) == tuple(hero):
                continue
            p = assign[r][c]
            sid, k = os.path.basename(p)[:-4].split("_")
            it = items[sid]
            out = f"{D}/hi/{sid}_{k}.jpg"
            if os.path.exists(out):
                continue
            vf = ("scale='if(gt(iw,ih),-2,1080)':'if(gt(iw,ih),1080,-2)':flags=lanczos" +
                  ("," + TM if it.get("trc") == "arib-std-b67" else "") +
                  ",crop='min(iw,ih*4/5)':'min(iw,ih*4/5)*5/4',scale=864:1080:flags=lanczos")
            ss = ["-ss", f"{it['dur'] * (0.3 if k == '0' else 0.7):.2f}"] if it["kind"] == "video" else []
            subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y"] + ss + ["-i", it["path"], "-frames:v", "1",
                                                                                "-vf", vf, "-q:v", "2", out])


# ---------------- render ----------------
LAY = json.load(open(f"{D}/layout.json")) if os.path.exists(f"{D}/layout.json") else None
_CACHE = {}


def tile_img(p, need_w):
    """RGB float tile at a resolution >= need_w (hi-res for the hero's neighbours)"""
    base = os.path.basename(p)
    hi = f"{D}/hi/{base}"
    use_hi = need_w > 300 and os.path.exists(hi)
    key = (p, use_hi, need_w <= 90)
    if key not in _CACHE:
        im = cv2.cvtColor(cv2.imread(hi if use_hi else p), cv2.COLOR_BGR2RGB)
        if need_w <= 90:
            im = cv2.resize(im, (96, 120), interpolation=cv2.INTER_AREA)
        _CACHE[key] = im
        if len(_CACHE) > 2500:
            _CACHE.clear()
    return _CACHE[key]


def pitch_center(t):
    """pitch (px per cell) and canvas centre (cell units) at time t"""
    hr, hc = LAY["hero"]
    p0 = W                                   # hero tile exactly the screen width
    u = ease_io((t - T_Z0) / (T_Z1 - T_Z0))
    p = p0 * (P_END / p0) ** u
    hero_c = np.array([hc + 0.5, (hr + 0.5)])
    full_c = np.array([COLS / 2, (H / P_END / 1.25) / 2])
    wgt = (1 / p - 1 / p0) / (1 / P_END - 1 / p0)
    return p, hero_c + (full_c - hero_c) * wgt


def tint_k(t):
    u = ease_io((t - T_Z0) / (T_Z1 - T_Z0))
    return float(np.clip((u - 0.35) / 0.55, 0, 1))


def hero_frame(t):
    f = int(np.clip(t * FPS, 0, 257)) + 1
    return cv2.cvtColor(cv2.imread(f"{D}/hero/{f:04d}.jpg"), cv2.COLOR_BGR2RGB)


def mosaic(t, sweep=0.0, dim=0.0, notint=False):
    img = np.empty((H, W, 3), np.uint8)
    img[:] = GAPC
    p, (cx, cy) = pitch_center(t)
    ph = p * 1.25
    uz = ease_io((t - T_Z0) / (T_Z1 - T_Z0))
    gap = max(1.0, p * (0.022 + 0.048 * uz))
    k = 0.0 if notint else tint_k(t)
    tgt, cov = np.array(LAY["tgt"], np.float32), np.array(LAY["cov"], np.float32)
    hr, hc = LAY["hero"]
    c0 = int(np.floor(cx - W / 2 / p)) - 1
    c1 = int(np.ceil(cx + W / 2 / p)) + 1
    r0 = int(np.floor(cy - H / 2 / ph)) - 1
    r1 = int(np.ceil(cy + H / 2 / ph)) + 1
    for r in range(max(0, r0), min(ROWS, r1 + 1)):
        for c in range(max(0, c0), min(COLS, c1 + 1)):
            x = W / 2 + (c - cx) * p + gap / 2
            y = H / 2 + (r - cy) * ph + gap / 2
            w, h = p - gap, ph - gap
            xi, yi, wi, hi = int(round(x)), int(round(y)), int(round(x + w)) - int(round(x)), \
                int(round(y + h)) - int(round(y))
            if wi < 2 or hi < 2 or xi >= W or yi >= H or xi + wi <= 0 or yi + hi <= 0:
                continue
            if (r, c) == (hr, hc):
                fr = hero_frame(t)
                src = fr[285:285 + 1350]                    # the 4:5 centre crop of the portrait frame
            else:
                src = tile_img(LAY["assign"][r][c], wi)
            tl = cv2.resize(src, (wi, hi), interpolation=cv2.INTER_AREA if wi < src.shape[1] else cv2.INTER_CUBIC)
            tl = tl.astype(np.float32)
            kk = k * (0.62 if cov[r, c] > 0.3 else 0.5)
            if kk > 0.005 or sweep > 0 or dim > 0:
                y_ = tl.mean(axis=2, keepdims=True)
                tg = tgt[r, c][None, None, :]
                colz = tg * (y_ / max(8.0, float(y_.mean())))
                if cov[r, c] <= 0.3:
                    colz = colz * 0.75
                tl = tl * (1 - kk) + colz * kk
                if sweep > 0 and cov[r, c] > 0.3:
                    tl *= 1 + sweep * float(np.exp(-((c + 0.6 * r - (T_SWEEP_POS(t))) / 3.0) ** 2))
                if dim > 0:
                    tl *= 1 - dim
            tl = np.clip(tl, 0, 255).astype(np.uint8)
            xa, ya, xb, yb = max(0, xi), max(0, yi), min(W, xi + wi), min(H, yi + hi)
            img[ya:yb, xa:xb] = tl[ya - yi:yb - yi, xa - xi:xb - xi]
    return img


def T_SWEEP_POS(t):
    return -10 + (t - T_SWEEP) / 1.8 * 80


def logo_layer(t):
    """crisp emblem crossfading over the mosaic emblem, then shrinking into the full logo at the top"""
    ex, ey, ew, eh = LAY["ex"], LAY["ey"], LAY["ew"], LAY["eh"]
    # mosaic emblem screen rect at the end of the pull back
    p, (cx, cy) = pitch_center(TOTAL)
    sx = W / 2 + (0 - cx) * p
    sy = H / 2 + (0 - cy) * p * 1.25
    a = a_in(t, T_CRISP0, T_CRISP1 - T_CRISP0)
    if a <= 0.01:
        return None
    u = ease_io((t - T_SHR0) / (T_SHR1 - T_SHR0))
    lw_final = 640
    s_final = lw_final / LOGO.width
    fx = (W - lw_final) / 2
    fy = 230
    e0 = (sx + ex, sy + ey, ew)                                    # emblem rect start (x, y, w)
    e1 = (fx + EMB_BOX[0] * s_final, fy + EMB_BOX[1] * s_final, (EMB_BOX[2] - EMB_BOX[0]) * s_final)
    x = e0[0] + (e1[0] - e0[0]) * u
    y = e0[1] + (e1[1] - e0[1]) * u
    w = e0[2] + (e1[2] - e0[2]) * u
    s = w / (EMB_BOX[2] - EMB_BOX[0])
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    full = LOGO.resize((max(1, int(LOGO.width * s)), max(1, int(LOGO.height * s))), Image.LANCZOS)
    # emblem part always, text part fades in at the end of the shrink
    emb = full.crop((int(EMB_BOX[0] * s), 0, int(EMB_BOX[2] * s), int(EMB_BOX[3] * s)))
    emb.putalpha(emb.split()[3].point(lambda v: int(v * a)))
    lay.alpha_composite(emb, (int(x), int(y)))
    at = a_in(t, T_SHR1 - 0.25, 0.5)
    if at > 0.01:
        txt = full.crop((0, int(EMB_BOX[3] * s) + 1, full.width, full.height))
        txt.putalpha(txt.split()[3].point(lambda v: int(v * at)))
        lay.alpha_composite(txt, (int(x - EMB_BOX[0] * s), int(y + EMB_BOX[3] * s) + 1))
    return lay


def caption(img, t, t0, t1, top, rib, ru, y=1420):
    al = a_in(t, t0, 0.4) * a_out(t, t1, 0.3)
    if al <= 0.01:
        return
    g = np.zeros((H, W, 4), np.uint8)
    v = np.clip((np.arange(H) - (y - 260)) / 420, 0, 1) ** 1.3 * 0.82 * al
    g[..., 3] = (v[:, None] * 255).astype(np.uint8)
    img.alpha_composite(Image.fromarray(g))
    text(img, (W // 2, y), top, SER(70), CREAM, al, 14, anchor="ma")
    text(img, (W // 2, y + 112), rib, SERI(74), INK, a_in(t, t0 + 0.2, 0.4) * a_out(t, t1, 0.3), 14, anchor="ma")
    text(img, (W // 2, y + 236), ru, MED(30), (235, 225, 210), a_in(t, t0 + 0.4, 0.4) * a_out(t, t1, 0.3), 10,
         anchor="ma")


_END_BG = None


def end_bg():
    global _END_BG
    if _END_BG is None:
        m = mosaic(T_Z1 + 0.5, notint=True)
        m = cv2.GaussianBlur(m, (0, 0), 10).astype(np.float32) * 0.36
        _END_BG = m.astype(np.uint8)
    return _END_BG


def frame(i):
    t = i / FPS
    sweep = 0.35 * a_in(t, T_SWEEP, 0.3) * a_out(t, T_CRISP0, 0.4) if t > T_SWEEP else 0.0
    if t < T_CRISP0 + 0.05:
        base = mosaic(t, sweep=sweep)
    else:
        u = ease((t - T_CRISP0) / (S_END + 0.3 - T_CRISP0))
        base = (mosaic(min(t, TOTAL), dim=0.0).astype(np.float32) * (1 - u) + end_bg().astype(np.float32) * u)
        base = base.astype(np.uint8) if u < 1 else end_bg().copy()
        if t < S_END + 0.3:
            dimv = 0.55 * a_in(t, T_CRISP0, 0.8)
            base = (base.astype(np.float32) * (1 - dimv * (1 - u))).astype(np.uint8)
    # the first seconds: the full portrait hero over the tile grid (tile = its 4:5 centre crop)
    af = a_out(t, T_Z0 - 0.1, 0.6)
    if af > 0.01:
        fr = hero_frame(t)
        base = (base.astype(np.float32) * (1 - af) + fr.astype(np.float32) * af).astype(np.uint8)
    img = Image.fromarray(base).convert("RGBA")
    lg = logo_layer(t)
    if lg is not None:
        img.alpha_composite(lg)
    caption(img, t, -1, 1.9, "Bu —", "bitta deraza.", "Это — одно окно.")
    caption(img, t, 4.4, 7.6, "Har bir katakcha —", "haqiqiy deraza.", "Каждая клетка — реальное окно.")
    caption(img, t, 10.7, 13.1, "Quyosh —", "har bir derazada.", "Солнце — в каждом окне.", y=1480)
    if t > S_END - 0.1:
        s0 = S_END
        text(img, (W // 2, 640), "Plisse jalyuzi", SER(84), CREAM, a_in(t, s0 + 0.2), 14, anchor="ma")
        text(img, (W // 2, 760), "har bir derazaga", SERI(66), INK, a_in(t, s0 + 0.4), 14, anchor="ma")
        text(img, (W // 2, 870), "Плиссе — на каждое окно", MED(30), (230, 220, 205), a_in(t, s0 + 0.6), 10,
             anchor="ma")
        text(img, (W // 2, 1050), "Narxini bilish uchun", MED(40), CREAM, a_in(t, s0 + 0.9), 10, anchor="ma")
        text(img, (W // 2, 1108), "qo‘ng‘iroq qiling:", MED(40), CREAM, a_in(t, s0 + 1.0), 10, anchor="ma")
        text(img, (W // 2, 1186), PHONE, SEMI(78), ORANGE, a_in(t, s0 + 1.2), 10, anchor="ma")
        text(img, (W // 2, 1340), "Yoki deraza rasmini direktga yuboring", MED(36), (240, 232, 218),
             a_in(t, s0 + 1.6), 10, anchor="ma")
        text(img, (W // 2, 1396), "Цены — по телефону или пришлите фото окна в директ", MED(26), (210, 200, 186),
             a_in(t, s0 + 1.75), 10, anchor="ma")
    g = np.random.default_rng(i).normal(0, 2.2, (H // 2, W // 2)).astype(np.float32)
    out = np.asarray(img.convert("RGB")).astype(np.float32) + cv2.resize(g, (W, H))[..., None]
    return np.clip(out, 0, 255).astype(np.uint8)


def render_frames():
    os.makedirs(f"{D}/fr", exist_ok=True)
    idx = [i for i in range(NF) if not os.path.exists(f"{D}/fr/{i:04d}.jpg")]
    with Pool(2) as p:
        for k in range(0, len(idx), 12):
            ch = idx[k:k + 12]
            for i, a in zip(ch, p.map(frame, ch)):
                cv2.imwrite(f"{D}/fr/{i:04d}.jpg", cv2.cvtColor(a, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 95])


def music():
    from steelpan_bed import steelpan_bed
    steelpan_bed(f"{D}/bed.wav", TOTAL, dict(zoom0=T_Z0, zoom1=T_Z1, sweep=T_SWEEP, crisp=T_CRISP0, end=S_END))


OUTN = "classic_quyosh_har_derazada"


def final():
    os.makedirs(f"{D}/out", exist_ok=True)
    subprocess.run(f"ffmpeg -nostdin -v error -y -framerate 30 -i {D}/fr/%04d.jpg -i {D}/bed.wav "
                   f"-filter_complex \"[1:a]loudnorm=I=-15:TP=-1.5:LRA=11[a]\" -map 0:v -map \"[a]\" -t {TOTAL:.3f} "
                   f"-c:v libx264 -preset slow -crf 18 -pix_fmt yuv420p -color_primaries bt709 -color_trc bt709 "
                   f"-colorspace bt709 -c:a aac -b:a 192k -movflags +faststart {D}/out/{OUTN}.mp4", shell=True,
                   check=True)


def cover():
    a = frame(int(12.3 * FPS))
    Image.fromarray(a).save(f"{D}/out/{OUTN}_muqova.jpg", quality=92)


if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else "all"
    if what == "layout":
        build_layout()
    if what == "prev":
        ts = [float(v) for v in sys.argv[2].split(",")]
        with Pool(2) as p:
            ims = p.map(frame, [int(round(v * FPS)) for v in ts])
        c = np.full((640, 365 * len(ims), 3), 255, np.uint8)
        for k, a in enumerate(ims):
            c[:, k * 365:k * 365 + 360] = cv2.resize(a, (360, 640), interpolation=cv2.INTER_AREA)
        cv2.imwrite(f"{D}/prev.jpg", cv2.cvtColor(c, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 88])
    if what in ("frames", "all"):
        render_frames()
    if what in ("music", "all"):
        music()
    if what in ("final", "all"):
        final()
    if what in ("cover", "all"):
        cover()
