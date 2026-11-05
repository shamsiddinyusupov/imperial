"""Two sales Reels from the latest kombo + plisse footage (5.11.2026, owner wants to see both):

A «Olishdan oldin 3 savol» — buyer's checklist: free measuring? ready when? warranty? each answer gets a drawn tick
  and a product shot (kombo / plisse), then «Uchalasiga ham — «ha»», NARX + «yaqiningizga yuboring».
B «Kunduzi / Kechqurun» — an on-screen day/evening switch over the owner's kombo photo (day look: sheer stripes
  lit from behind; evening: the real photo), then plisse, NARX.

python3 build.py segs | ov A|B | music A|B | final A|B
"""
import json
import math
import os
import subprocess
import sys
import wave

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy.signal import butter, lfilter

sys.path.insert(0, "/home/claude/reels/common")
sys.path.insert(0, "/home/claude/reels/dikey_style")
from faqat_qarang import DID, ITA, LAB, LIG, RU, rise, soft_shadow, sweep, text_img  # noqa: E402
from musicbox_bed import musicbox_bed  # noqa: E402
from pizz_bed import BEAT as PBEAT, pizz_bed  # noqa: E402

D = "/home/claude/reels/sotuv"
KR = "/home/claude/reels/kombo_rasm"
W, H, FPS = 1080, 1920, 30
XF = 0.4
PAD = 24
LOOK_N = ("huesaturation=saturation=-0.85:colors=c+b:strength=8,curves=all='0/0.03 0.25/0.245 0.5/0.52 0.75/0.79 1/0.975',"
          "eq=saturation=0.97,vignette=angle=PI/9,noise=alls=4:allf=t")
C = {k: tuple(v) for k, v in json.load(open("/home/claude/reels/ikki_xona/colours.json")).items()}

# timelines: (segment file, start in the final, file holds start..next_start+XF)
A_SC = [("A_h", 0.0), ("A_q1", 3.4), ("A_q2", 9.0), ("A_q3", 14.6), ("A_s", 18.35), ("A_end", 21.8)]
A_TOTAL = 28.0
A_TICK = [5.25, 10.85, 16.15]                     # tick strokes (also the music hits)
B_SC = [("B_k", 0.0), ("B_p", 13.6), ("B_end", 18.4)]
B_TOTAL = 25.0
B_FLIP = 8.2                                       # the switch flips day -> evening
B_TR = 1.2                                         # light change after the flip


def run(a):
    subprocess.run(a, check=True)


def ease(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


def enc(out, vf):
    return subprocess.Popen(["ffmpeg", "-nostdin", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s",
                             f"{W}x{H}", "-r", str(FPS), "-i", "-", "-vf", vf + ",setsar=1", "-c:v", "libx264", "-preset",
                             "fast", "-crf", "14", "-pix_fmt", "yuv420p", "-r", str(FPS), out], stdin=subprocess.PIPE)


def cam(img, s, cx, cy):
    M = np.array([[s, 0, W / 2 - s * cx], [0, s, H / 2 - s * cy]])
    return cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LANCZOS4, borderMode=cv2.BORDER_REFLECT)


def seg_len(sc, total, k):
    return (sc[k + 1][1] + XF if k + 1 < len(sc) else total) - sc[k][1]


# ---------------------------------------------------------------- segments
def endbg(src_mp4, out, n):
    p = subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-sseof", "-0.3", "-i", src_mp4, "-frames:v", "1", "-f",
                        "rawvideo", "-pix_fmt", "bgr24", "-"], capture_output=True, check=True)
    last = np.frombuffer(p.stdout[:W * H * 3], np.uint8).reshape(H, W, 3).astype(np.float32)
    blur = cv2.GaussianBlur(last, (0, 0), 28)
    cocoa = np.array(C["cocoa"][::-1], np.float32)
    ys = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
    shade = 0.30 + 0.10 * np.abs(ys - 0.45) * 2
    e = enc(out, "noise=alls=4:allf=t")
    for i in range(n):
        u = i / max(1, n - 1)
        fr = cam(blur, 1.06 + 0.05 * u, W / 2, H / 2 + 12 * u)
        e.stdin.write(np.clip(fr * shade + cocoa * (1 - shade), 0, 255).astype(np.uint8).tobytes())
    e.stdin.close()
    e.wait()


def segs():
    plate = np.load(f"{KR}/seg/prep/plate.npy")
    # A hook: the owner's kombo photo (evening, as it is), slow push
    n = round(seg_len(A_SC, A_TOTAL, 0) * FPS)
    e = enc(f"{D}/seg/A_h.mp4", LOOK_N + ",unsharp=5:5:0.3")
    for i in range(n):
        u = ease(i / (n - 1)) * 0.5 + (i / (n - 1)) * 0.5
        s = (W / 1296) * (1.03 + 0.06 * u)
        e.stdin.write(np.clip(cam(plate, s, 655, 1190 + 30 * u), 0, 255).astype(np.uint8).tobytes())
    e.stdin.close()
    e.wait()
    # B kombo: day look -> switch -> evening (the kombo_rasm scene, all pieces landed)
    sys.path.insert(0, KR)
    import vfx  # noqa: E402
    sc = vfx.Scene()
    day = sc.frame(8.0)
    eve = sc.frame(10.2)
    n = round(seg_len(B_SC, B_TOTAL, 0) * FPS)
    e = enc(f"{D}/seg/B_k.mp4", LOOK_N + ",unsharp=5:5:0.3")
    for i in range(n):
        t = i / FPS
        if t < B_FLIP:
            fr = day
        elif t < B_FLIP + B_TR:
            fr = sc.frame(vfx.EVE0 + (vfx.EVE1 - vfx.EVE0) * ((t - B_FLIP) / B_TR))
        else:
            fr = eve
        u = ease(t / (n / FPS)) * 0.6 + (t / (n / FPS)) * 0.4
        s = (W / 1296) * (1.04 * (1.15 / 1.04) ** u)
        e.stdin.write(np.clip(cam(fr, s, 650 + 5 * u, 1180 + 55 * u), 0, 255).astype(np.uint8).tobytes())
    e.stdin.close()
    e.wait()
    endbg(f"{D}/seg/A_s.mp4", f"{D}/seg/A_end.mp4", round(seg_len(A_SC, A_TOTAL, 5) * FPS) + 2)
    endbg(f"{D}/seg/B_p.mp4", f"{D}/seg/B_end.mp4", round(seg_len(B_SC, B_TOTAL, 2) * FPS) + 2)
    print("segs ok")


# ---------------------------------------------------------------- overlays
def cloud(box, amax, col, blur=60):
    m = Image.new("L", (W, H), 0)
    ImageDraw.Draw(m).rounded_rectangle(box, 120, fill=int(255 * amax))
    m = m.filter(ImageFilter.GaussianBlur(blur))
    img = Image.new("RGBA", (W, H), col + (0,))
    img.putalpha(m)
    return img


def fade(L, a):
    if a >= 1:
        return L
    out = L.copy()
    out.putalpha(L.getchannel("A").point(lambda v: int(v * max(0.0, a))))
    return out


def win(t, a, b, fi=0.45, fo=0.45):
    return min(ease((t - a) / fi), 1 - ease((t - (b - fo)) / fo))


def hook(lab, w1, w2, ru, ink=True):
    c = C
    col = (c["acc_dark"], c["dark"], c["acc_dark"], c["dim_dark"]) if ink else (c["acc_light"], c["light"], c["acc_light"], c["dim_light"])
    return {"lab": text_img(lab, LAB(22), col[0], 0.46), "w1": text_img(w1, DID(104), col[1]),
            "w2": text_img(w2, ITA(84), col[2]), "ru": text_img(ru, RU(31), col[3]),
            "cloud": cloud((50, 250, 820, 700), 0.62, c["cream_cloud"], 60)}


def draw_hook(L, o, t, d, Y=300):
    X = 112
    L.alpha_composite(fade(o["cloud"], 1 - ease((t - (d - 0.5)) / 0.5)))
    K = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(K).line([(84, Y + 18), (84, Y + 18 + int(300 * ease(t / 0.7)))], fill=C["acc_dark"], width=2)
    K.alpha_composite(o["lab"], (X - PAD, Y - PAD))
    rise(K, o["w1"], X - PAD - 4, Y + 34 - PAD, ease((t + 0.18) / 0.75))
    rise(K, o["w2"], X - PAD - 2, Y + 148 - PAD, ease((t - 0.12) / 0.75))
    if t > 0.45:
        K.alpha_composite(fade(o["ru"], ease((t - 0.45) / 0.5)), (X - PAD, Y + 252 - PAD))
    L.alpha_composite(fade(K, 1 - ease((t - (d - 0.5)) / 0.5)))


def end_card(lines_extra):
    c = C
    o = {"lab": text_img("IZOHGA YOZING", LAB(26), c["acc_light"], 0.5),
         "big": soft_shadow(text_img("NARX", DID(168), c["light"]), 16, 0.45),
         "sub": soft_shadow(text_img("narxlarni direktga yuboramiz", ITA(46), c["light"]), 12, 0.4),
         "imp": text_img("IMPERIAL", LAB(40), c["light"], 0.62),
         "f1": text_img("Toshkentda o‘lchov va o‘rnatish bepul  ·  1 yil kafolat", LIG(28), c["dim_light"]),
         "f2": text_img("O‘lchovdan keyin 3 kunda tayyor", LIG(28), c["dim_light"])}
    o["extra"] = [text_img(s, f, col) for s, f, col in lines_extra]
    return o


def draw_end(L, o, t):
    Y = 560
    K = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    for k, yy in (("lab", Y), ("big", Y + 50), ("sub", Y + 250)):
        K.alpha_composite(o[k], ((W - o[k].width) // 2, yy - PAD))
    ImageDraw.Draw(K).line([(W // 2 - 60, Y + 372), (W // 2 + 60, Y + 372)], fill=C["acc_light"], width=2)
    imp = sweep(o["imp"], (t - 1.4) / 1.1) if 1.4 < t < 2.5 else o["imp"]
    K.alpha_composite(imp, ((W - imp.width) // 2, Y + 410 - PAD))
    yy = Y + 490
    for k in ("f1", "f2"):
        K.alpha_composite(o[k], ((W - o[k].width) // 2, yy - PAD))
        yy += 44
    yy += 22
    for im in o["extra"]:
        K.alpha_composite(im, ((W - im.width) // 2, yy - PAD))
        yy += im.height - 2 * PAD + 14
    L.alpha_composite(fade(K, ease(t / 0.5)))


class OvA:
    Q = [("01  ·  SAVOL", "O‘lchovchi bepul keladimi?", "Toshkentda — bepul.", "Замер по Ташкенту — бесплатно"),
         ("02  ·  SAVOL", "Qachon tayyor bo‘ladi?", "O‘lchovdan keyin — 3 kunda.", "Готово через 3 дня после замера"),
         ("03  ·  SAVOL", "Kafolat bormi?", "Ha — 1 yil.", "Гарантия — 1 год на всё")]
    QT = [(3.65, 8.85), (9.25, 14.45), (14.85, 18.2)]

    def __init__(self):
        c = C
        self.h = hook("IMPERIAL  ·  XARIDORGA ESLATMA", "Olishdan oldin —", "3 ta savol bering.",
                      "Перед покупкой — задайте 3 вопроса")
        self.q = [(text_img(a, LAB(22), c["acc_light"], 0.46), soft_shadow(text_img(b, ITA(60), c["light"]), 12, 0.4),
                   soft_shadow(text_img(x, DID(54), c["light"]), 12, 0.4), soft_shadow(text_img(r, RU(28), c["dim_light"]), 10, 0.35))
                  for a, b, x, r in self.Q]
        self.qcloud = cloud((40, 1240, 960, 1650), 0.60, c["graphite"])
        self.s = (soft_shadow(text_img("Uchalasiga ham —", DID(78), c["light"]), 14, 0.45),
                  soft_shadow(text_img("«ha».", ITA(96), c["acc_light"]), 14, 0.45),
                  soft_shadow(text_img("O‘rnatish ham bepul  ·  Click, Payme, karta, naqd", LIG(29), c["light"]), 10, 0.4),
                  soft_shadow(text_img("Установка бесплатно · любая оплата", RU(28), c["dim_light"]), 10, 0.35))
        self.scloud = cloud((40, 1180, 980, 1660), 0.55, c["cocoa"])
        self.e = end_card([("Jalyuzi olmoqchi bo‘lgan yaqiningizga yuboring", ITA(36), c["light"]),
                           ("Напишите NARX — пришлём цены в директ", RU(28), c["dim_light"])])
        for _, b, x, _r in self.q:
            assert b.width - 2 * PAD < 880 and x.width - 2 * PAD < 760, (b.width, x.width)

    def tick(self, L, x, y, p, col):
        pts = [(x, y + 26), (x + 22, y + 50), (x + 64, y)]
        segs = [(pts[0], pts[1]), (pts[1], pts[2])]
        lens = [math.dist(*s) for s in segs]
        tot = sum(lens) * ease(p)
        d = ImageDraw.Draw(L)
        for (a, b), ln in zip(segs, lens):
            if tot <= 0:
                break
            f = min(1.0, tot / ln)
            e = (a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f)
            d.line([a, e], fill=col, width=8, joint="curve")
            d.ellipse([a[0] - 4, a[1] - 4, a[0] + 4, a[1] + 4], fill=col)
            d.ellipse([e[0] - 4, e[1] - 4, e[0] + 4, e[1] + 4], fill=col)
            tot -= ln

    def __call__(self, t):
        L = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        if t < 3.3:
            draw_hook(L, self.h, t, 3.3)
        for k, (a, b) in enumerate(self.QT):
            if a <= t < b:
                aa = win(t, a, b)
                y0 = 1290
                K = Image.new("RGBA", (W, H), (0, 0, 0, 0))
                K.alpha_composite(self.qcloud)
                ImageDraw.Draw(K).line([(84, y0 + 18), (84, y0 + 300)], fill=C["acc_light"], width=2)
                lab, q, ans, ru = self.q[k]
                K.alpha_composite(lab, (112 - PAD, y0 - PAD))
                K.alpha_composite(q, (112 - PAD, y0 + 38 - PAD))
                tk = A_TICK[k]
                if t > tk - 0.05:
                    self.tick(K, 116, y0 + 142, (t - tk) / 0.35, C["acc_light"])
                if t > tk + 0.25:
                    p = ease((t - tk - 0.25) / 0.5)
                    K.alpha_composite(fade(ans, p), (204 - PAD, y0 + 128 - PAD + int(8 * (1 - p))))
                    K.alpha_composite(fade(ru, p), (112 - PAD, y0 + 222 - PAD))
                L.alpha_composite(fade(K, aa))
        if 18.75 <= t < 21.75:
            aa = win(t, 18.75, 21.75)
            K = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            K.alpha_composite(self.scloud)
            y0 = 1260
            a1, a2, f1, r1 = self.s
            K.alpha_composite(a1, (112 - PAD, y0 - PAD))
            p = ease((t - 19.15) / 0.5)
            if p > 0:
                K.alpha_composite(fade(a2, p), (112 - PAD + a1.width - 2 * PAD + 18, y0 - 14 - PAD))
            p2 = ease((t - 19.6) / 0.5)
            if p2 > 0:
                K.alpha_composite(fade(f1, p2), (112 - PAD, y0 + 120 - PAD))
                K.alpha_composite(fade(r1, p2), (112 - PAD, y0 + 172 - PAD))
            L.alpha_composite(fade(K, aa))
        if t >= 22.15:
            draw_end(L, self.e, t - 22.15)
        return L


class OvB:
    CARDS = [((3.35, 8.05), "KUNDUZI", "Yumshoq yorug‘lik.", "Днём — мягкий свет"),
             ((9.45, 13.4), "KECHQURUN", "Sokinlik.", "Вечером — тишина и уют"),
             ((14.0, 18.15), "YOKI  —  PLISSE", "Iliq va sokin xona uchun.", "Или плиссе — тепло и тихо")]

    def __init__(self):
        c = C
        self.h = hook("IMPERIAL  ·  KOMBO (KUN-TUN)", "Bitta jalyuzi.", "Ikki kayfiyat.", "Одни жалюзи — два настроения")
        self.cards = [(text_img(a, LAB(22), c["acc_light"], 0.46), soft_shadow(text_img(b, ITA(66), c["light"]), 12, 0.4),
                       soft_shadow(text_img(r, RU(29), c["dim_light"]), 10, 0.35)) for _, a, b, r in self.CARDS]
        self.ccloud = cloud((40, 1260, 900, 1580), 0.58, c["graphite"])
        self.lab_d = text_img("KUNDUZI", LAB(22), c["dark"], 0.4)
        self.lab_n = text_img("KECHQURUN", LAB(22), c["dark"], 0.4)
        self.e = end_card([("Sizga qaysi biri yoqdi — kunduzi yoki kechqurun?", ITA(34), c["light"]),
                           ("Напишите NARX — пришлём цены в директ", RU(28), c["dim_light"])])

    def toggle(self, L, t):
        p = ease((t - B_FLIP) / 0.4)
        cx, cy, tw_, th = W // 2, 360, 196, 92
        sand, night = np.array((214, 186, 140)), np.array((44, 48, 58))
        col = tuple(int(v) for v in sand * (1 - p) + night * p)
        K = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        sh = Image.new("L", (W, H), 0)
        ImageDraw.Draw(sh).rounded_rectangle([cx - tw_ // 2, cy - th // 2 + 8, cx + tw_ // 2, cy + th // 2 + 8], th // 2, fill=110)
        sh = sh.filter(ImageFilter.GaussianBlur(14))
        shade = Image.new("RGBA", (W, H), (20, 18, 16, 0))
        shade.putalpha(sh)
        K.alpha_composite(shade)
        d = ImageDraw.Draw(K)
        d.rounded_rectangle([cx - tw_ // 2, cy - th // 2, cx + tw_ // 2, cy + th // 2], th // 2, fill=col + (255,),
                            outline=(255, 255, 255, 120), width=2)
        r = th // 2 - 8
        kx = cx - tw_ // 2 + th // 2 + (tw_ - th) * p
        d.ellipse([kx - r, cy - r, kx + r, cy + r], fill=(250, 248, 242, 255))
        ic = (196, 150, 70) if p < 0.5 else (90, 98, 120)
        if p < 0.5:      # sun
            d.ellipse([kx - 11, cy - 11, kx + 11, cy + 11], fill=ic)
            for k in range(8):
                a = k * math.pi / 4
                d.line([(kx + 16 * math.cos(a), cy + 16 * math.sin(a)), (kx + 23 * math.cos(a), cy + 23 * math.sin(a))],
                       fill=ic, width=4)
        else:            # moon
            d.ellipse([kx - 18, cy - 18, kx + 18, cy + 18], fill=ic)
            d.ellipse([kx - 9, cy - 24, kx + 23, cy + 10], fill=(250, 248, 242, 255))
        # labels under the switch, the active one bright
        ld = fade(self.lab_d, 1.0 - 0.6 * p)
        ln = fade(self.lab_n, 0.4 + 0.6 * p)
        K.alpha_composite(ld, (cx - tw_ // 2 - 22 - (ld.width - PAD), cy - ld.height // 2))
        K.alpha_composite(ln, (cx + tw_ // 2 + 22 - PAD, cy - ln.height // 2))
        a = min(ease((t - 3.0) / 0.5), 1 - ease((t - 13.0) / 0.4))
        L.alpha_composite(fade(K, a))

    def __call__(self, t):
        L = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        if t < 3.2:
            draw_hook(L, self.h, t, 3.2)
        if 2.9 < t < 13.5:
            self.toggle(L, t)
        for k, ((a, b), *_r) in enumerate(self.CARDS):
            if a <= t < b:
                y0 = 1330
                K = Image.new("RGBA", (W, H), (0, 0, 0, 0))
                K.alpha_composite(self.ccloud)
                ImageDraw.Draw(K).line([(84, y0 + 18), (84, y0 + 200)], fill=C["acc_light"], width=2)
                lab, ti, ru = self.cards[k]
                K.alpha_composite(lab, (112 - PAD, y0 - PAD))
                K.alpha_composite(ti, (112 - PAD, y0 + 42 - PAD))
                K.alpha_composite(ru, (112 - PAD, y0 + 140 - PAD))
                L.alpha_composite(fade(K, win(t, a, b)))
        if t >= 18.75:
            draw_end(L, self.e, t - 18.75)
        return L


_OV = None


def _init(which):
    global _OV
    _OV = OvA() if which == "A" else OvB()


def _job(i):
    return _OV(i / FPS).tobytes()


def ov(which):
    total = A_TOTAL if which == "A" else B_TOTAL
    n = round(total * FPS)
    out = f"{D}/ov/{which}.mov"
    p = subprocess.Popen(["ffmpeg", "-nostdin", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-c:v", "prores_ks", "-profile:v", "4444", "-pix_fmt", "yuva444p10le",
                          "-vendor", "apl0", out + ".tmp.mov"], stdin=subprocess.PIPE)
    from multiprocessing import Pool
    with Pool(4, initializer=_init, initargs=(which,)) as pool:
        for b in pool.imap(_job, range(n), chunksize=4):
            p.stdin.write(b)
    p.stdin.close()
    if p.wait() == 0:
        os.replace(out + ".tmp.mov", out)
    print("ov", which, n)


# ---------------------------------------------------------------- sound
SR = 48000


def sfx(path, total, events):
    n = int(total * SR)
    L, R = np.zeros(n), np.zeros(n)
    rng = np.random.default_rng(12)
    for t0, kind in events:
        i = int(t0 * SR)
        if kind == "pen":            # a short felt-pen stroke for the tick
            m = int(0.36 * SR)
            tt = np.arange(m) / SR
            b, a = butter(2, [2500 / (SR / 2), 9000 / (SR / 2)], "band")
            x = lfilter(b, a, rng.normal(0, 1, m)) * np.sin(np.pi * np.clip(tt / 0.36, 0, 1)) ** 0.7 * 0.25
        else:                        # the switch: two soft clicks
            m = int(0.12 * SR)
            tt = np.arange(m) / SR
            x = np.zeros(m)
            for d0 in (0.0, 0.07):
                k = int(d0 * SR)
                b, a = butter(2, [1500 / (SR / 2), 7000 / (SR / 2)], "band")
                c = lfilter(b, a, rng.normal(0, 1, m - k)) * np.exp(-tt[: m - k] / 0.004)
                x[k:] += c * (1.0 if d0 == 0 else 0.6)
        j = min(n, i + len(x))
        L[i:j] += x[: j - i]
        R[i:j] += x[: j - i]
    pk = max(np.abs(L).max(), 1e-9)
    st = (np.stack([L, R], 1) / pk * 0.5 * 32767).astype(np.int16)
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(st.tobytes())


def music(which):
    os.makedirs(f"{D}/out", exist_ok=True)
    if which == "A":
        # G major: G - Em - C - D ... resolve G on the end card
        ch = [(0.0, 43, [59, 62, 67]), (A_SC[1][1], 40, [59, 64, 67]), (A_SC[2][1], 36, [60, 64, 67]),
              (A_SC[3][1], 38, [62, 66, 69]), (A_SC[4][1], 40, [59, 64, 67]), (A_SC[5][1], 43, [59, 62, 67, 71])]
        hits = [(t, m, 0.42, 0.0) for t, m in zip(A_TICK, (79, 83, 86))] + [(19.15, 91, 0.38, 0.0)]
        pizz_bed(f"{D}/out/A_bed.wav", A_TOTAL, dict(chords=ch, hits=hits, groove=(A_SC[1][1], A_SC[5][1])))
        sfx(f"{D}/out/A_sfx.wav", A_TOTAL, [(t, "pen") for t in A_TICK])
    else:
        # E major, bright by day; after the switch C#m (darker), plisse A, end E
        ch = [(0.0, 40, [56, 59, 63, 68], 1.0), (B_FLIP, 37, [56, 61, 64, 68], 0.25), (B_SC[1][1], 45, [57, 61, 64, 69], 0.6),
              (B_SC[2][1], 40, [56, 59, 63, 66, 71], 0.8)]
        mel = []
        day = [76, 80, 83, 88, 87, 83, 80, 83]
        t, i = 0.35, 0
        while t < B_FLIP - 0.2:
            mel.append((t, day[i % len(day)], 0.20))
            i += 1
            t += 60 / 70
        night = [64, 68, 71, 73, 71, 68]
        t, i = B_FLIP + 0.5, 0
        while t < B_SC[1][1] - 0.2:
            mel.append((t, night[i % len(night)], 0.18))
            i += 1
            t += 60 / 70
        pl = [69, 73, 76, 81, 80, 76]
        t, i = B_SC[1][1] + 0.3, 0
        while t < B_SC[2][1] - 0.2:
            mel.append((t, pl[i % len(pl)], 0.17))
            i += 1
            t += 60 / 70
        for k, m in enumerate([64, 68, 71, 76, 80, 83]):
            mel.append((B_SC[2][1] + 0.25 + 0.14 * k, m, 0.15))
        musicbox_bed(f"{D}/out/B_bed.wav", B_TOTAL, dict(chords=ch, melody=mel, clicks=[]))
        sfx(f"{D}/out/B_sfx.wav", B_TOTAL, [(B_FLIP, "switch")])
    run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-i", f"{D}/out/{which}_bed.wav", "-af", "loudnorm=I=-15:TP=-1.5:LRA=9",
         "-ar", "48000", f"{D}/out/{which}_musiqa.wav"])
    print("music", which)


# ---------------------------------------------------------------- final
def final(which):
    sc, total = (A_SC, A_TOTAL) if which == "A" else (B_SC, B_TOTAL)
    name = {"A": "imperial_3_savol", "B": "imperial_kunduzi_kechqurun"}[which]
    ins, fl = [], []
    for k, (s, t0) in enumerate(sc):
        ins += ["-i", f"{D}/seg/{s}.mp4"]
        fl.append(f"[{k}:v]trim=0:{seg_len(sc, total, k):.4f},setpts=PTS-STARTPTS,settb=AVTB,fps={FPS},format=yuv420p[v{k}]")
    cur = "v0"
    for k in range(1, len(sc)):
        fl.append(f"[{cur}][v{k}]xfade=transition=fade:duration={XF}:offset={sc[k][1]:.4f}[x{k}]")
        cur = f"x{k}"
    n = len(sc)
    ins += ["-i", f"{D}/ov/{which}.mov", "-i", f"{D}/out/{which}_musiqa.wav", "-i", f"{D}/out/{which}_sfx.wav"]
    fl.append(f"[{n}:v]format=yuva420p[o]")
    fl.append(f"[{cur}][o]overlay=0:0:eof_action=pass,trim=0:{total},format=yuv420p[vout]")
    fl.append(f"[{n + 1}:a][{n + 2}:a]amix=inputs=2:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=9,aresample=48000[aout]")
    out = f"{D}/out/{name}.mp4"
    run(["ffmpeg", "-nostdin", "-v", "error", "-y"] + ins + ["-filter_complex", ";".join(fl), "-map", "[vout]", "-map",
         "[aout]", "-c:v", "libx264", "-preset", "slow", "-crf", "20", "-pix_fmt", "yuv420p", "-color_primaries", "bt709",
         "-color_trc", "bt709", "-colorspace", "bt709", "-c:a", "aac", "-b:a", "192k", "-t", f"{total}", "-movflags",
         "+faststart", out + ".tmp.mp4"])
    os.replace(out + ".tmp.mp4", out)
    run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-ss", "1.3", "-i", out, "-frames:v", "1", "-q:v", "2",
         f"{D}/out/{name}_muqova.jpg"])
    print("final", which)


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "segs":
        segs()
    elif cmd == "ov":
        ov(sys.argv[2])
    elif cmd == "music":
        music(sys.argv[2])
    elif cmd == "final":
        final(sys.argv[2])
