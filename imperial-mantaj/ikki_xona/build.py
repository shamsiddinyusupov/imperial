"""«Ikki xona» — grey kombo + light-beige plisse, silent, new vibraphone/cello bed.

Layers (also what DaVinci Resolve gets):
  V1  scene clips with 0.5 s handles  -> seg/*.mp4 (stab.py) + seg/s1.mp4 (split hook) + seg/s7.mp4 (end-card bg)
  V2  text overlays with alpha         -> ov/O1..O4.mov (ProRes 4444)
  A1  music                            -> out/musiqa.wav
and a finished MP4 composited here     -> out/imperial_ikki_xona.mp4

python3 build.py clips | overlays | music | final | all
"""
import colorsys
import json
import os
import subprocess
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, "/home/claude/reels/common")
sys.path.insert(0, "/home/claude/reels/dikey_style")
import grade  # noqa: E402
from faqat_qarang import DID, ITA, LAB, LIG, RU, rise, soft_shadow, sweep, text_img  # noqa: E402
from vibe_bed import vibe_bed  # noqa: E402

D = "/home/claude/reels/ikki_xona"
W, H, FPS = 1080, 1920, 30
HANDLE, XF = 0.5, 0.6
LOOK_N = ("huesaturation=saturation=-0.85:colors=c+b:strength=8,curves=all='0/0.03 0.25/0.245 0.5/0.52 0.75/0.79 1/0.975',"
          "eq=saturation=0.97,vignette=angle=PI/9,noise=alls=4:allf=t")

# timeline: (name, cut-in, cut-out, head handle in the media)
SCENES = [("s1", 0.0, 3.6, 0.0), ("k2", 3.6, 7.9, 0.5), ("k3", 7.9, 10.9, 0.5), ("p4", 10.9, 15.3, 0.5),
          ("p5", 15.3, 18.5, 0.5), ("p6", 18.5, 20.9, 0.5), ("s7", 20.9, 26.5, 0.5)]
TOTAL = SCENES[-1][2]
OVERLAYS = {"O1": (0.0, 3.9), "O2": (4.5, 7.4), "O3": (11.6, 14.6), "O4": (21.1, TOTAL)}
ENC = ["-c:v", "libx264", "-preset", "fast", "-crf", "14", "-pix_fmt", "yuv420p", "-r", str(FPS)]


def run(a):
    subprocess.run(a, check=True)


def ease(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


def hls(c, l=None, s=None):
    h, l0, s0 = colorsys.rgb_to_hls(*(np.array(c) / 255))
    return tuple(int(round(v * 255)) for v in colorsys.hls_to_rgb(h, l0 if l is None else l, s0 if s is None else s))


# ---------------------------------------------------------------- graded stills
def graded_still(src, dst, kind):
    img = cv2.imread(src)
    h, w = img.shape[:2]
    base = max(W / w, H / h)
    tmp = dst.replace(".png", "_raw.png")
    cv2.imwrite(tmp, cv2.resize(img, (round(w * base), round(h * base)), interpolation=cv2.INTER_AREA))
    g = grade.gains(tmp)
    if kind == "n":
        g = np.full(3, g.mean())
        vf = f"colorchannelmixer=rr={g[0]:.3f}:gg={g[1]:.3f}:bb={g[2]:.3f},{LOOK_N.replace(',noise=alls=4:allf=t', '')}"
    else:
        vf = grade.vf(g).replace(",noise=alls=4:allf=t", "")
    run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-i", src, "-vf", vf, dst])
    return cv2.imread(dst)


def palette(path, k=8):
    px = np.asarray(Image.open(path).convert("RGB").resize((180, 320)), dtype=float).reshape(-1, 3)
    rng = np.random.default_rng(3)
    c = px[rng.choice(len(px), k, replace=False)]
    for _ in range(40):
        lab = ((px[:, None] - c[None]) ** 2).sum(-1).argmin(1)
        c = np.array([px[lab == i].mean(0) if (lab == i).any() else c[i] for i in range(k)])
    return sorted([tuple(int(v) for v in x) for x in c], key=sum)


def encode_frames(frames, n, out):
    tmp = out.replace(".mp4", ".tmp.mp4")
    p = subprocess.Popen(["ffmpeg", "-nostdin", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-vf", "noise=alls=4:allf=t,setsar=1"] + ENC + [tmp], stdin=subprocess.PIPE)
    for i in range(n):
        p.stdin.write(np.ascontiguousarray(frames(i)).tobytes())
    p.stdin.close()
    if p.wait() == 0:
        os.replace(tmp, out)


def warp(img, scale, cx, cy, ow, oh):
    M = np.array([[scale, 0, ow / 2 - scale * cx], [0, scale, oh / 2 - scale * cy]])
    return cv2.warpAffine(img, M, (ow, oh), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)


def clips():
    os.makedirs(f"{D}/stills", exist_ok=True)
    K = graded_still(f"{D}/src/photo.jpg", f"{D}/stills/kombo.png", "n")
    P = graded_still(f"{D}/src/photo_plisse.jpg", f"{D}/stills/plisse.png", "w")
    # s1: split hook — kombo left, plisse right, slow opposite drift, a thin cream seam
    n1 = round((3.6 + HANDLE) * FPS)
    seam = (226, 232, 238)

    def f1(i):
        u = ease(i / (n1 - 1)) * 0.4 + (i / (n1 - 1)) * 0.6
        out = np.empty((H, W, 3), np.uint8)
        hk, wk = K.shape[:2]
        sk = 1.0 * (1.035 - 0.035 * u)
        out[:, :540] = warp(K, sk, wk * 0.50, hk * 0.47 + 26 * u / sk, 540, H)
        hp, wp = P.shape[:2]
        sp = 1.0 * (1.035 - 0.035 * u)
        out[:, 540:] = warp(P, sp, wp * 0.50, hp * 0.47 - 26 * u / sp, 540, H)
        out[:, 539:541] = (np.array(seam[::-1]) * 0.9 + out[:, 539:541] * 0.1).astype(np.uint8)
        return out

    encode_frames(f1, n1, f"{D}/seg/s1.mp4")
    # s7: end-card background — the plisse photo, blurred and warmed down to cocoa, still drifting
    n7 = round((HANDLE + 5.6) * FPS)
    hp, wp = P.shape[:2]
    blur = cv2.GaussianBlur(P, (0, 0), 26)
    cocoa = np.array((26, 33, 44), np.float32)            # BGR of a deep cocoa
    ys = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
    shade = 0.30 + 0.10 * np.abs(ys - 0.45) * 2            # a touch darker at top and bottom

    def f7(i):
        u = i / (n7 - 1)
        fr = warp(blur, 1.06 + 0.04 * u, wp / 2, hp / 2 + 10, W, H).astype(np.float32)
        out = fr * shade + cocoa * (1 - shade)
        return np.clip(out, 0, 255).astype(np.uint8)

    encode_frames(f7, n7, f"{D}/seg/s7.mp4")
    print("clips ok")


# ---------------------------------------------------------------- overlays
def colours():
    pk = palette(f"{D}/stills/kombo.png")
    pp = palette(f"{D}/stills/plisse.png")
    walnut = min(pp, key=lambda c: sum(c))                       # darkest warm = the window frame
    warm = max(pp, key=lambda c: c[0] - c[2])
    graphite = pk[0]
    C = {
        "dark": hls(walnut, l=0.15, s=0.30), "acc_dark": hls(warm, l=0.40, s=0.42), "dim_dark": hls(walnut, l=0.38, s=0.10),
        "cream_cloud": hls(pp[-1], l=0.95, s=0.30),
        "light": hls(pk[-1], l=0.965, s=0.04), "acc_light": hls(warm, l=0.74, s=0.34), "dim_light": hls(pk[len(pk) // 2], l=0.82, s=0.04),
        "graphite": hls(graphite, l=0.10, s=0.06), "cocoa": hls(walnut, l=0.10, s=0.22),
    }
    json.dump(C, open(f"{D}/colours.json", "w"))
    return C


def cloud(box, amax, col, blur=70):
    m = Image.new("L", (W, H), 0)
    ImageDraw.Draw(m).rounded_rectangle(box, 120, fill=int(255 * amax))
    m = m.filter(ImageFilter.GaussianBlur(blur))
    img = Image.new("RGBA", (W, H), col + (0,))
    img.putalpha(m)
    return img


def fade_layer(L, a):
    if a >= 1:
        return L
    out = L.copy()
    out.putalpha(L.getchannel("A").point(lambda v: int(v * max(0.0, a))))
    return out


PAD = 24


class Ov:
    def __init__(self, C):
        self.C = C
        c = C
        # O1 hook (dark type on the light ceilings, cream cloud behind)
        self.o1 = {
            "lab": text_img("IMPERIAL  ·  KOMBO VA PLISSE", LAB(22), c["acc_dark"], 0.46),
            "w1": text_img("Ikki xona —", DID(108), c["dark"]),
            "w2": text_img("ikki kayfiyat.", ITA(100), c["acc_dark"]),
            "ru": text_img("Две комнаты — два настроения", RU(30), c["dim_dark"]),
            "cloud": cloud((50, 210, 760, 640), 0.62, c["cream_cloud"], 60),
        }
        # O2 kombo (light type on grey stripes, graphite cloud)
        self.o2 = self.label("01 — KOMBO JALYUZI", "Kulrang. Kun va tun.", "Комбо — серый, день и ночь",
                             c["acc_light"], c["light"], c["dim_light"], c["graphite"], 0.50, shadow=True)
        # O3 plisse (dark type on cream slats, cream cloud)
        self.o3 = self.label("02 — PLISSE JALYUZI", "Och bej. Iliq va sokin.", "Плиссе — светлый беж",
                             c["acc_dark"], c["dark"], c["dim_dark"], c["cream_cloud"], 0.62, shadow=False)
        # O4 end card (cream type on the cocoa blur)
        self.o4 = {
            "lab": text_img("IZOHGA YOZING", LAB(26), c["acc_light"], 0.5),
            "big": soft_shadow(text_img("NARX", DID(168), c["light"]), 16, 0.45),
            "sub": soft_shadow(text_img("narxlarni direktga yuboramiz", ITA(46), c["light"]), 12, 0.4),
            "imp": text_img("IMPERIAL", LAB(40), c["light"], 0.62),
            "f1": text_img("Toshkentda o‘lchov va o‘rnatish bepul  ·  1 yil kafolat", LIG(28), c["dim_light"]),
            "ru": text_img("Напишите NARX — пришлём цены в директ", RU(29), c["dim_light"]),
        }

    def label(self, lab, title, ru, acc, txt, dim, cl, ca, shadow):
        y = 1330
        L = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        L.alpha_composite(cloud((50, y - 30, 820, y + 250), ca, cl, 60))
        d = ImageDraw.Draw(L)
        d.line([(84, y + 18), (84, y + 200)], fill=acc, width=2)
        items = [(text_img(lab, LAB(22), acc, 0.46), y), (text_img(title, ITA(66), txt), y + 44),
                 (text_img(ru, RU(29), dim), y + 140)]
        for im, yy in items:
            im = soft_shadow(im, 12, 0.35) if shadow else im
            L.alpha_composite(im, (112 - PAD, yy - PAD))
        return L

    def frame(self, name, t):
        """t = seconds from the overlay's own start."""
        a0, a1 = OVERLAYS[name]
        d = a1 - a0
        L = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        if name == "O1":
            o = self.o1
            L.alpha_composite(o["cloud"])
            X, Y = 112, 290
            dr = ImageDraw.Draw(L)
            hl = ease(t / 0.7)
            dr.line([(84, Y + 18), (84, Y + 18 + int(300 * hl))], fill=self.C["acc_dark"], width=2)
            L.alpha_composite(o["lab"], (X - PAD, Y - PAD))
            rise(L, o["w1"], X - PAD - 4, Y + 36 - PAD, ease((t + 0.18) / 0.75))
            rise(L, o["w2"], X - PAD - 2, Y + 150 - PAD, ease((t - 0.15) / 0.75))
            if t > 0.5:
                L.alpha_composite(fade_layer(o["ru"], ease((t - 0.5) / 0.5)), (X - PAD, Y + 262 - PAD))
            return fade_layer(L, 1 - ease((t - (d - 0.6)) / 0.6))
        if name in ("O2", "O3"):
            L = self.o2 if name == "O2" else self.o3
            return fade_layer(L, min(ease(t / 0.45), 1 - ease((t - (d - 0.45)) / 0.45)))
        o = self.o4
        Y = 640
        lay = [("lab", Y), ("big", Y + 50), ("sub", Y + 250)]
        for k, yy in lay:
            im = o[k]
            L.alpha_composite(im, ((W - im.width) // 2, yy - PAD))
        dr = ImageDraw.Draw(L)
        dr.line([(W // 2 - 60, Y + 372), (W // 2 + 60, Y + 372)], fill=self.C["acc_light"], width=2)
        imp = sweep(o["imp"], (t - 1.4) / 1.1) if 1.4 < t < 2.5 else o["imp"]
        L.alpha_composite(imp, ((W - imp.width) // 2, Y + 410 - PAD))
        for k, yy in (("f1", Y + 490), ("ru", Y + 540)):
            im = o[k]
            L.alpha_composite(im, ((W - im.width) // 2, yy - PAD))
        return fade_layer(L, ease(t / 0.5))


def render_overlay(args):
    name, C = args
    ov = Ov(C)
    a0, a1 = OVERLAYS[name]
    n = round((a1 - a0) * FPS)
    out = f"{D}/ov/{name}.mov"
    tmp = f"{D}/ov/{name}.tmp.mov"
    p = subprocess.Popen(["ffmpeg", "-nostdin", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-c:v", "prores_ks", "-profile:v", "4444", "-pix_fmt", "yuva444p10le",
                          "-vendor", "apl0", tmp], stdin=subprocess.PIPE)
    for i in range(n):
        p.stdin.write(ov.frame(name, i / FPS).tobytes())
    p.stdin.close()
    if p.wait() == 0:
        os.replace(tmp, out)
    return name


def overlays():
    os.makedirs(f"{D}/ov", exist_ok=True)
    C = colours()
    from multiprocessing import Pool
    with Pool(4) as p:
        print(p.map(render_overlay, [(k, C) for k in OVERLAYS]))


def music():
    os.makedirs(f"{D}/out", exist_ok=True)
    vibe_bed(f"{D}/out/bed_raw.wav", TOTAL, [s[1] for s in SCENES[1:]], SCENES[-1][1])
    run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-i", f"{D}/out/bed_raw.wav", "-af", "loudnorm=I=-15:TP=-1.5:LRA=9",
         "-ar", "48000", f"{D}/out/musiqa.wav"])
    print("music ok")


def final():
    ins, fl = [], []
    for k, (name, t0, t1, head) in enumerate(SCENES):
        first, last = k == 0, k == len(SCENES) - 1
        a = head - (0 if first else XF / 2)
        b = head + (t1 - t0) + (0 if last else XF / 2)
        ins += ["-i", f"{D}/seg/{name}.mp4"]
        fl.append(f"[{k}:v]trim={a:.4f}:{b:.4f},setpts=PTS-STARTPTS,settb=AVTB,fps={FPS},format=yuv420p[v{k}]")
    cur = "v0"
    for k in range(1, len(SCENES)):
        off = SCENES[k][1] - XF / 2
        fl.append(f"[{cur}][v{k}]xfade=transition=fade:duration={XF}:offset={off:.4f}[x{k}]")
        cur = f"x{k}"
    n = len(SCENES)
    for j, (name, (a0, a1)) in enumerate(OVERLAYS.items()):
        ins += ["-i", f"{D}/ov/{name}.mov"]
        fl.append(f"[{n + j}:v]setpts=PTS-STARTPTS+{a0}/TB,format=yuva420p[o{j}]")
        fl.append(f"[{cur}][o{j}]overlay=0:0:eof_action=pass[y{j}]")
        cur = f"y{j}"
    fl.append(f"[{cur}]trim=0:{TOTAL},format=yuv420p[vout]")
    ins += ["-i", f"{D}/out/musiqa.wav"]
    out = f"{D}/out/imperial_ikki_xona.mp4"
    run(["ffmpeg", "-nostdin", "-v", "error", "-y"] + ins + ["-filter_complex", ";".join(fl), "-map", "[vout]", "-map",
         f"{n + len(OVERLAYS)}:a", "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-pix_fmt", "yuv420p",
         "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709", "-c:a", "aac", "-b:a", "192k",
         "-t", f"{TOTAL}", "-movflags", "+faststart", out + ".tmp.mp4"])
    os.replace(out + ".tmp.mp4", out)
    run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-ss", "1.6", "-i", out, "-frames:v", "1", "-q:v", "2",
         f"{D}/out/imperial_ikki_xona_muqova.jpg"])
    print("final ok")


if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else "all"
    if what in ("clips", "all"):
        clips()
    if what in ("overlays", "all"):
        overlays()
    if what in ("music", "all"):
        music()
    if what in ("final", "all"):
        final()
