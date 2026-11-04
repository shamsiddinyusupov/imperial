"""«Kombo yig‘iladi» — grey kombo (IMG_5681) assembles itself on a sun-blown window, light goes day -> evening,
then the real shot; end card NARX. Silent (no voice), new harp bed + assembly sound effects.

Layers:
  V1  seg/vfx.mp4 (vfx.py, 0..10.2 s) + seg/real.mp4 (stab.py, eased start) + seg/endbg.mp4
  V2  ov/O1, O2, O4 (ProRes 4444 alpha)
  A1  out/musiqa.wav (harp_bed) + out/sfx.wav
python3 build.py endbg | overlays | music | final | all
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
sys.path.insert(0, "/home/claude/reels/kombo_yigil")
from faqat_qarang import DID, ITA, LAB, LIG, RU, rise, soft_shadow, sweep, text_img  # noqa: E402
from harp_bed import SR, harp_bed  # noqa: E402
import vfx  # noqa: E402

D = "/home/claude/reels/kombo_yigil"
W, H, FPS = 1080, 1920, 30
T_SW = vfx.T_SW                       # 10.2 — cut to the real shot
N_REAL = 74                           # frames in seg/real.mp4
T_REAL_END = T_SW + N_REAL / FPS      # 12.667
XF_END = 0.6
T_END = T_REAL_END - XF_END           # end card starts (dissolve)
TOTAL = 18.9
OVERLAYS = {"O1": (0.0, 2.75), "O2": (6.95, 12.35), "O4": (T_END + 0.15, TOTAL)}
C = json.load(open("/home/claude/reels/ikki_xona/colours.json"))
C = {k: tuple(v) for k, v in C.items()}
PAD = 24


def run(a):
    subprocess.run(a, check=True)


def ease(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


# ---------------------------------------------------------------- end card background
def endbg():
    p = subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-sseof", "-0.2", "-i", f"{D}/seg/real.mp4", "-frames:v", "1",
                        "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], capture_output=True, check=True)
    last = np.frombuffer(p.stdout[:W * H * 3], np.uint8).reshape(H, W, 3).astype(np.float32)
    blur = cv2.GaussianBlur(last, (0, 0), 28)
    graphite = np.array(C["graphite"][::-1], np.float32)
    ys = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
    shade = 0.26 + 0.10 * np.abs(ys - 0.45) * 2
    n = round((TOTAL - T_END) * FPS) + 2
    out = f"{D}/seg/endbg.mp4"
    enc = subprocess.Popen(["ffmpeg", "-nostdin", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}",
                            "-r", str(FPS), "-i", "-", "-vf", "noise=alls=4:allf=t,setsar=1", "-c:v", "libx264", "-preset",
                            "fast", "-crf", "14", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
    for i in range(n):
        u = i / (n - 1)
        s = 1.06 + 0.05 * u
        M = np.array([[s, 0, W / 2 - s * W / 2], [0, s, H / 2 - s * (H / 2 + 12 * u)]])
        fr = cv2.warpAffine(blur, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        fr = fr * shade + graphite * (1 - shade)
        enc.stdin.write(np.clip(fr, 0, 255).astype(np.uint8).tobytes())
    enc.stdin.close()
    enc.wait()
    print("endbg ok", n)


# ---------------------------------------------------------------- overlays
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


STORY = [  # (from, to) seconds inside O2, title, russian
    (0.0, 1.85, "Kunduzi — yumshoq yorug‘lik.", "Днём — мягкий свет"),
    (1.85, 3.45, "Kechqurun — sokinlik.", "Вечером — тишина и уют"),
    (3.45, 5.40, "Bitta jalyuzi — kun va tun.", "Одна штора — день и ночь"),
]


class Ov:
    def __init__(self):
        c = C
        self.o1 = {
            "lab": text_img("IMPERIAL  ·  KOMBO JALYUZI", LAB(22), c["acc_dark"], 0.46),
            "w1": text_img("Quyosh", DID(118), c["dark"]),
            "w2": text_img("ko‘zni qamashtiryaptimi?", ITA(78), c["acc_dark"]),
            "ru": text_img("Солнце слепит глаза?", RU(32), c["dim_dark"]),
        }
        self.o2_lab = soft_shadow(text_img("KOMBO  ·  KUN-TUN", LAB(22), c["acc_light"], 0.46), 12, 0.35)
        self.o2_t = [(soft_shadow(text_img(t, ITA(64), c["light"]), 12, 0.4),
                      soft_shadow(text_img(r, RU(29), c["dim_light"]), 12, 0.35)) for _, _, t, r in STORY]
        self.o2_cloud = cloud((40, 1290, 900, 1590), 0.58, c["graphite"], 60)
        self.o4 = {
            "lab": text_img("IZOHGA YOZING", LAB(26), c["acc_light"], 0.5),
            "big": soft_shadow(text_img("NARX", DID(168), c["light"]), 16, 0.45),
            "sub": soft_shadow(text_img("narxlarni direktga yuboramiz", ITA(46), c["light"]), 12, 0.4),
            "imp": text_img("IMPERIAL", LAB(40), c["light"], 0.62),
            "f1": text_img("Toshkentda o‘lchov va o‘rnatish bepul  ·  1 yil kafolat", LIG(28), c["dim_light"]),
            "f2": text_img("O‘lchovdan keyin 3 kunda tayyor", LIG(28), c["dim_light"]),
            "ru": text_img("Напишите NARX — пришлём цены в директ", RU(29), c["dim_light"]),
        }
        for k, im in list(self.o1.items()) + [("t", t) for t, _ in self.o2_t]:
            assert im.width - 2 * PAD < 900, (k, im.width)

    def frame(self, name, t):
        a0, a1 = OVERLAYS[name]
        d = a1 - a0
        L = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        if name == "O1":
            o = self.o1
            X, Y = 112, 330
            dr = ImageDraw.Draw(L)
            hl = ease(t / 0.7)
            dr.line([(84, Y + 18), (84, Y + 18 + int(300 * hl))], fill=C["acc_dark"], width=2)
            L.alpha_composite(o["lab"], (X - PAD, Y - PAD))
            rise(L, o["w1"], X - PAD - 4, Y + 34 - PAD, ease((t + 0.18) / 0.75))
            rise(L, o["w2"], X - PAD - 2, Y + 160 - PAD, ease((t - 0.12) / 0.75))
            if t > 0.45:
                L.alpha_composite(fade_layer(o["ru"], ease((t - 0.45) / 0.5)), (X - PAD, Y + 262 - PAD))
            return fade_layer(L, 1 - ease((t - (d - 0.5)) / 0.5))
        if name == "O2":
            y = 1340
            L.alpha_composite(self.o2_cloud)
            ImageDraw.Draw(L).line([(84, y + 18), (84, y + 200)], fill=C["acc_light"], width=2)
            L.alpha_composite(self.o2_lab, (112 - PAD, y - PAD))
            for k, (s0, s1, _, _) in enumerate(STORY):
                a = min(ease((t - s0) / 0.45) if k else ease(t / 0.45), 1 - ease((t - (s1 - 0.35)) / 0.35))
                if k == len(STORY) - 1:
                    a = ease((t - s0) / 0.45)
                if a <= 0:
                    continue
                ti, ru = self.o2_t[k]
                dy = int(10 * (1 - a))
                L.alpha_composite(fade_layer(ti, a), (112 - PAD, y + 44 - PAD + dy))
                L.alpha_composite(fade_layer(ru, a), (112 - PAD, y + 140 - PAD + dy))
            return fade_layer(L, min(ease(t / 0.45), 1 - ease((t - (d - 0.45)) / 0.45)))
        o = self.o4
        Y = 620
        for k, yy in (("lab", Y), ("big", Y + 50), ("sub", Y + 250)):
            im = o[k]
            L.alpha_composite(im, ((W - im.width) // 2, yy - PAD))
        dr = ImageDraw.Draw(L)
        dr.line([(W // 2 - 60, Y + 372), (W // 2 + 60, Y + 372)], fill=C["acc_light"], width=2)
        imp = sweep(o["imp"], (t - 1.4) / 1.1) if 1.4 < t < 2.5 else o["imp"]
        L.alpha_composite(imp, ((W - imp.width) // 2, Y + 410 - PAD))
        for k, yy in (("f1", Y + 490), ("f2", Y + 534), ("ru", Y + 590)):
            im = o[k]
            L.alpha_composite(im, ((W - im.width) // 2, yy - PAD))
        return fade_layer(L, ease(t / 0.5))


def render_overlay(name):
    ov = Ov()
    a0, a1 = OVERLAYS[name]
    n = round((a1 - a0) * FPS)
    out = f"{D}/ov/{name}.mov"
    p = subprocess.Popen(["ffmpeg", "-nostdin", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-c:v", "prores_ks", "-profile:v", "4444", "-pix_fmt", "yuva444p10le",
                          "-vendor", "apl0", out + ".tmp.mov"], stdin=subprocess.PIPE)
    for i in range(n):
        p.stdin.write(ov.frame(name, i / FPS).tobytes())
    p.stdin.close()
    if p.wait() == 0:
        os.replace(out + ".tmp.mov", out)
    return name


def overlays():
    os.makedirs(f"{D}/ov", exist_ok=True)
    Ov()
    from multiprocessing import Pool
    with Pool(3) as p:
        print(p.map(render_overlay, list(OVERLAYS)))


# ---------------------------------------------------------------- sound
def landings():
    """(time, kind, pan) of every landing in the picture (vfx.PIECES)."""
    ev = []
    for idx, t0, dur, dx, dy, sc, rot, ov, shake in vfx.PIECES:
        tl = t0 + dur * (1 / (ov + 1) if ov > 0 else 1.0)
        kind = "cas" if idx == 0 else "bar" if idx == 13 else "chain" if idx == 14 else "band"
        pan = -0.55 if dx < 0 else 0.55 if dx > 0 else 0.0
        ev.append((tl, kind, pan, t0))
    return ev


def music():
    os.makedirs(f"{D}/out", exist_ok=True)
    ev = landings()
    bands = [e for e in ev if e[1] == "band"]
    cas = [e for e in ev if e[1] == "cas"][0]
    bar = [e for e in ev if e[1] == "bar"][0]
    chain = [e for e in ev if e[1] == "chain"][0]
    up = [66, 69, 71, 74, 76, 78, 81, 83, 86, 88, 90, 93]
    plucks = [(0.30, 81, 0.20, 0.3), (1.15, 78, 0.18, -0.3), (2.00, 76, 0.17, 0.2),
              (cas[0], 50, 0.42, 0.0), (bar[0], 45, 0.42, 0.0), (chain[0], 86, 0.16, 0.5),
              (vfx.EVE0 + 0.05, 47, 0.34, 0.0), (vfx.EVE0 + 0.75, 66, 0.18, -0.2),
              (T_SW + 0.05, 78, 0.20, 0.25), (T_SW + 0.88, 76, 0.18, -0.25), (T_SW + 1.71, 74, 0.18, 0.2),
              (T_END + 2.3, 69, 0.15, -0.3), (T_END + 3.2, 74, 0.14, 0.3), (T_END + 4.1, 78, 0.13, 0.0)]
    for k, (tl, _, pan, _) in enumerate(bands):
        plucks.append((tl, up[k], 0.22 + 0.012 * k, pan))
    chords = [(0.0, 38, [62, 66, 69, 76]), (cas[0], 35, [59, 62, 66, 69]), (bands[6][0], 43, [55, 59, 62, 66]),
              (bar[0], 45, [57, 61, 64, 69]), (chain[0], 38, [62, 66, 69, 74]), (vfx.EVE0, 35, [59, 62, 66, 69]),
              (T_SW, 43, [59, 62, 66, 69]), (T_END, 38, [62, 64, 66, 69, 74])]
    gliss = [(vfx.SHEEN0 + 0.05, [74, 76, 78, 81, 83, 86, 88, 90], 0.07, 0.15),
             (T_END + 0.2, [62, 66, 69, 74, 78, 81], 0.14, 0.17)]
    harp_bed(f"{D}/out/bed_raw.wav", TOTAL, dict(chords=chords, plucks=plucks, gliss=gliss))
    run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-i", f"{D}/out/bed_raw.wav", "-af", "loudnorm=I=-15:TP=-1.5:LRA=9",
         "-ar", "48000", f"{D}/out/musiqa.wav"])
    sfx(ev)
    print("music ok")


def sfx(ev):
    n = int(TOTAL * SR)
    L, R = np.zeros(n), np.zeros(n)
    rng = np.random.default_rng(9)

    def add(sig, t0, pan=0.0, g=1.0):
        i = int(round(t0 * SR))
        if i < 0 or i >= n:
            return
        j = min(n, i + len(sig))
        L[i:j] += sig[: j - i] * g * (1 - pan) ** 0.5
        R[i:j] += sig[: j - i] * g * (1 + pan) ** 0.5

    def bp(x, lo, hi):
        b, a = butter(2, [lo / (SR / 2), hi / (SR / 2)], "band")
        return lfilter(b, a, x)

    def whoosh(dur, pan0, g):
        m = int(dur * SR)
        t = np.linspace(0, 1, m)
        x = bp(rng.normal(0, 1, m), 300, 5200)
        env = np.sin(np.pi * np.clip(t, 0, 1)) ** 2 * (0.4 + 0.6 * t)
        sig = x * env
        # pan sweeps from the side it comes from to the centre
        p = pan0 * (1 - t)
        return sig * np.sqrt(1 - p) * g, sig * np.sqrt(1 + p) * g

    def tick(g, low=False):
        m = int(0.09 * SR)
        t = np.arange(m) / SR
        x = bp(rng.normal(0, 1, m), 1800, 7000) * np.exp(-t / 0.006)
        x += np.sin(2 * np.pi * (140 if low else 420) * t) * np.exp(-t / (0.05 if low else 0.018)) * (0.9 if low else 0.35)
        return x * g

    for tl, kind, pan, t0 in ev:
        dur = max(0.2, tl - t0)
        g = {"band": 0.10, "cas": 0.16, "bar": 0.14, "chain": 0.06}[kind]
        wl, wr = whoosh(dur + 0.05, pan, g)
        i = int(round(t0 * SR))
        j = min(n, i + len(wl))
        L[i:j] += wl[: j - i]
        R[i:j] += wr[: j - i]
        if kind == "band":
            add(tick(0.20), tl, pan * 0.3)
        elif kind in ("cas", "bar"):
            add(tick(0.55, low=True), tl, 0.0)
        else:
            add(tick(0.10), tl, 0.4)
    pk = max(np.abs(L).max(), np.abs(R).max()) + 1e-9
    st = (np.stack([L, R], 1) / pk * 0.6 * 32767).astype(np.int16)
    with wave.open(f"{D}/out/sfx.wav", "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(st.tobytes())


# ---------------------------------------------------------------- final
def final():
    out = f"{D}/out/imperial_kombo_yigiladi.mp4"
    ins = ["-i", f"{D}/seg/vfx.mp4", "-i", f"{D}/seg/real.mp4", "-i", f"{D}/seg/endbg.mp4"]
    fl = [f"[0:v]trim=0:{T_SW},setpts=PTS-STARTPTS,settb=AVTB,fps={FPS},format=yuv420p[a]",
          f"[1:v]trim=end_frame={N_REAL},setpts=PTS-STARTPTS,settb=AVTB,fps={FPS},format=yuv420p[b]",
          f"[2:v]setpts=PTS-STARTPTS,settb=AVTB,fps={FPS},format=yuv420p[c]",
          "[a][b]concat=n=2:v=1:a=0,settb=AVTB,fps=30[ab]",
          f"[ab][c]xfade=transition=fade:duration={XF_END}:offset={T_END:.4f}[v0]"]
    cur = "v0"
    for j, (name, (a0, a1)) in enumerate(OVERLAYS.items()):
        ins += ["-i", f"{D}/ov/{name}.mov"]
        fl.append(f"[{3 + j}:v]setpts=PTS-STARTPTS+{a0}/TB,format=yuva420p[o{j}]")
        fl.append(f"[{cur}][o{j}]overlay=0:0:eof_action=pass[y{j}]")
        cur = f"y{j}"
    fl.append(f"[{cur}]trim=0:{TOTAL},format=yuv420p[vout]")
    k = 3 + len(OVERLAYS)
    ins += ["-i", f"{D}/out/musiqa.wav", "-i", f"{D}/out/sfx.wav"]
    fl.append(f"[{k}:a]volume=1.0[m];[{k + 1}:a]volume=0.55[s];[m][s]amix=inputs=2:normalize=0,"
              f"loudnorm=I=-14:TP=-1.5:LRA=9,aresample=48000[aout]")
    run(["ffmpeg", "-nostdin", "-v", "error", "-y"] + ins + ["-filter_complex", ";".join(fl), "-map", "[vout]", "-map",
         "[aout]", "-c:v", "libx264", "-preset", "slow", "-crf", "17", "-pix_fmt", "yuv420p", "-color_primaries", "bt709",
         "-color_trc", "bt709", "-colorspace", "bt709", "-c:a", "aac", "-b:a", "192k", "-t", f"{TOTAL}", "-movflags",
         "+faststart", out + ".tmp.mp4"])
    os.replace(out + ".tmp.mp4", out)
    run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-ss", "1.2", "-i", out, "-frames:v", "1", "-q:v", "2",
         f"{D}/out/imperial_kombo_yigiladi_muqova.jpg"])
    print("final ok")


if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else "all"
    if what in ("endbg", "all"):
        endbg()
    if what in ("overlays", "all"):
        overlays()
    if what in ("music", "all"):
        music()
    if what in ("final", "all"):
        final()
