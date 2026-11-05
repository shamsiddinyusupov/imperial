"""«Derazaning gapi bor» — 1-qism «Kechqurun» (rasmli serial). The window narrates (Daniel), AI stills move with
slow camera, the product is shown only in real footage (the kombo assembling + day -> evening, the owner's photo).

Inputs (serial1/):
  ai/s1.png s2.png s3.png      full-res ElevenLabs stills (fallback: ai/s*_preview.jpg)
  vo/narration.mp3             Daniel, 7 paragraphs
python3 build.py vo | segs | ov | music | final | all        (vo --dummy: estimated timing for a preview)
"""
import json
import os
import subprocess
import sys
import wave

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, "/home/claude/reels/common")
sys.path.insert(0, "/home/claude/reels/dikey_style")
from faqat_qarang import DID, ITA, LAB, LIG, RU, rise, soft_shadow, sweep, text_img  # noqa: E402
from kalimba_bed import kalimba_bed  # noqa: E402

D = "/home/claude/reels/serial1"
W, H, FPS, SR = 1080, 1920, 30, 48000
XF = 0.5
PAD = 24
C = {k: tuple(v) for k, v in json.load(open("/home/claude/reels/ikki_xona/colours.json")).items()}
KR_VFX = "/home/claude/reels/kombo_rasm/seg/vfx.mp4"            # graded, 0..10.2 s
EVE_PUSH = "/home/claude/reels/sotuv/seg/A_h.mp4"              # owner's kombo photo, evening, slow push (3.8 s)
SUBS = [
    ["Salom. Men — deraza.", "Va menda… bitta muammo bor."],
    ["Har kech chiroq yoqilganda…", "meni hamma ko‘radi.", "Ko‘chadagilar ham… qarshidagi qo‘shnilar ham."],
    ["Aziza buni yoqtirmaydi. Jasur esa:", "«Parda ilsak, kunduzi qorong‘i bo‘ladi», — deydi."],
    ["Shunda… menga kombo tanlashdi."],
    ["Kunduzi — yumshoq yorug‘lik.", "Kechqurun — sokinlik. Bitta jalyuzida."],
    ["Endi kechqurun… faqat ular uchun."],
    ["Keyingi qismda — ertalabki quyosh.", "Narxini bilmoqchimisiz? Izohga «narx» deb yozing."],
]
EST = [4.6, 8.4, 8.6, 3.2, 6.4, 3.6, 7.0]
SCENES = ["s1", "s2", "s3", "r1", "r2", "r3", "end"]
MIN = {"s1": 5.0, "r1": 4.8, "r2": 3.4, "end": 6.5}
LEAD = {0: 1.4}
GAP = 0.55
TEMPO = 1.04


def run(a):
    subprocess.run(a, check=True)


def ease(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


# ---------------------------------------------------------------- voice + timeline
def load(path):
    raw = subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-i", path, "-af", f"atempo={TEMPO}", "-ac", "1", "-ar",
                          str(SR), "-f", "s16le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.int16).astype(np.float32) / 32768


def voiced(x, thr_db=-38):
    hop = int(0.01 * SR)
    env = np.sqrt(np.convolve(x ** 2, np.ones(hop) / hop, "same"))[::hop]
    return env > 10 ** (thr_db / 20), hop


def split(x, n):
    v, hop = voiced(x)
    runs, i = [], 0
    while i < len(v):
        if not v[i]:
            j = i
            while j < len(v) and not v[j]:
                j += 1
            runs.append((i, j))
            i = j
        else:
            i += 1
    first = int(np.argmax(v))
    last = len(v) - int(np.argmax(v[::-1]))
    inner = [(a, b) for a, b in runs if a > first and b < last]
    total_chars = [sum(len(s) for s in p) for p in SUBS[:n]]
    cum = np.cumsum(total_chars)[:-1] / sum(total_chars)
    span = last - first
    breaks = []
    for c in cum:                                    # the longest pause near each text-proportional position
        target = first + c * span
        cand = [r for r in inner if abs((r[0] + r[1]) / 2 - target) < 0.12 * span and r not in breaks]
        r = max(cand, key=lambda r: (r[1] - r[0]) - 0.02 * abs((r[0] + r[1]) / 2 - target)) if cand else \
            min(inner, key=lambda r: abs((r[0] + r[1]) / 2 - target))
        breaks.append(r)
    breaks.sort()
    edges = [first] + [b for r in breaks for b in r] + [last]
    paras = [(edges[2 * k] * hop, edges[2 * k + 1] * hop) for k in range(n)]
    return paras


def vo(dummy=False):
    os.makedirs(f"{D}/vo", exist_ok=True)
    if dummy:
        paras = None
        lens = EST
    else:
        x = load(f"{D}/vo/narration.mp3")
        paras = split(x, len(SUBS))
        lens = [(b - a) / SR for a, b in paras]
    t, tl = 0.0, []
    for k, name in enumerate(SCENES):
        lead = LEAD.get(k, 0.35)
        d = max(MIN.get(name, 0), lead + lens[k] + GAP)
        tl.append({"scene": name, "start": round(t, 3), "len": round(d, 3), "vo": round(t + lead, 3), "vo_len": round(lens[k], 3)})
        t += d
    total = round(t, 3)
    json.dump({"total": total, "scenes": tl}, open(f"{D}/timing.json", "w"), indent=1)
    if paras is not None:
        out = np.zeros(int((total + 1) * SR), np.float32)
        for k, (a, b) in enumerate(paras):
            i = int(tl[k]["vo"] * SR)
            out[i:i + (b - a)] += x[a:b]
        pcm = (np.clip(out, -1, 1) * 32767).astype(np.int16)
        with wave.open(f"{D}/vo/vo_track.wav", "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(SR)
            w.writeframes(pcm.tobytes())
    print("total", total, [(s["scene"], s["start"], s["len"]) for s in tl])


def T():
    return json.load(open(f"{D}/timing.json"))


# ---------------------------------------------------------------- segments
def enc(out, vf):
    return subprocess.Popen(["ffmpeg", "-nostdin", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s",
                             f"{W}x{H}", "-r", str(FPS), "-i", "-", "-vf", vf + ",setsar=1", "-c:v", "libx264", "-preset",
                             "fast", "-crf", "15", "-pix_fmt", "yuv420p", "-r", str(FPS), out], stdin=subprocess.PIPE)


def still(name, dur, z0, z1, c0, c1):
    src = f"{D}/ai/{name}.png" if os.path.exists(f"{D}/ai/{name}.png") else f"{D}/ai/{name}_preview.jpg"
    img = cv2.imread(src).astype(np.float32)
    h, w = img.shape[:2]
    base = max(W / w, H / h)
    n = round(dur * FPS)
    e = enc(f"{D}/seg/{name}.mp4", "eq=saturation=0.96:contrast=1.02,vignette=angle=PI/8,noise=alls=3:allf=t")
    for i in range(n):
        u = i / max(1, n - 1)
        u = ease(u) * 0.35 + u * 0.65
        s = base * (z0 + (z1 - z0) * u)
        cx = (c0[0] + (c1[0] - c0[0]) * u) * w
        cy = (c0[1] + (c1[1] - c0[1]) * u) * h
        M = np.array([[s, 0, W / 2 - s * cx], [0, s, H / 2 - s * cy]])
        fr = cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LANCZOS4, borderMode=cv2.BORDER_REFLECT)
        e.stdin.write(np.clip(fr, 0, 255).astype(np.uint8).tobytes())
    e.stdin.close()
    e.wait()


def clip(src, ss, dur, out, speed=1.0):
    vf = f"trim=start={ss}:duration={dur * speed:.3f},setpts=(PTS-STARTPTS)/{speed}," \
         f"fps={FPS},scale={W}:{H},setsar=1" if speed != 1.0 else \
         f"trim=start={ss}:duration={dur:.3f},setpts=PTS-STARTPTS,fps={FPS},scale={W}:{H},setsar=1"
    run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-i", src, "-vf", vf, "-an", "-c:v", "libx264", "-preset", "fast",
         "-crf", "15", "-pix_fmt", "yuv420p", out])


def segs():
    os.makedirs(f"{D}/seg", exist_ok=True)
    tl = {s["scene"]: s for s in T()["scenes"]}
    L = {k: v["len"] + XF for k, v in tl.items()}
    still("s1", L["s1"], 1.00, 1.10, (0.50, 0.50), (0.50, 0.47))        # push in to the lit window
    still("s2", L["s2"], 1.08, 1.00, (0.50, 0.52), (0.50, 0.50))        # slow pull back: the room, the black glass
    still("s3", L["s3"], 1.02, 1.10, (0.40, 0.50), (0.36, 0.46))        # drift to Aziza
    # r1: the kombo assembling (vfx 2.2 s ..), r2: day -> evening (vfx .. 10.2), r3: the owner's photo at evening
    r1 = L["r1"]
    clip(KR_VFX, max(0.0, 7.2 - r1), r1, f"{D}/seg/r1.mp4")
    r2 = L["r2"]
    sp = min(1.0, 3.0 / r2) if r2 > 3.0 else 1.0
    clip(KR_VFX, 10.2 - 3.0, r2, f"{D}/seg/r2.mp4", speed=sp)
    r3 = L["r3"]
    sp3 = min(1.0, 3.8 / r3)
    clip(EVE_PUSH, 0.0, r3, f"{D}/seg/r3.mp4", speed=sp3)
    # end card background: the evening photo blurred into cocoa
    p = subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-sseof", "-0.3", "-i", f"{D}/seg/r3.mp4", "-frames:v", "1",
                        "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], capture_output=True, check=True)
    last = np.frombuffer(p.stdout[:W * H * 3], np.uint8).reshape(H, W, 3).astype(np.float32)
    blur = cv2.GaussianBlur(last, (0, 0), 28)
    cocoa = np.array(C["cocoa"][::-1], np.float32)
    ys = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
    shade = 0.30 + 0.10 * np.abs(ys - 0.45) * 2
    n = round(tl["end"]["len"] * FPS) + 2
    e = enc(f"{D}/seg/end.mp4", "noise=alls=4:allf=t")
    for i in range(n):
        u = i / max(1, n - 1)
        s = 1.06 + 0.05 * u
        M = np.array([[s, 0, W / 2 - s * W / 2], [0, s, H / 2 - s * (H / 2 + 12 * u)]])
        fr = cv2.warpAffine(blur, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        e.stdin.write(np.clip(fr * shade + cocoa * (1 - shade), 0, 255).astype(np.uint8).tobytes())
    e.stdin.close()
    e.wait()
    print("segs ok")


# ---------------------------------------------------------------- overlays
def fade(L, a):
    if a >= 1:
        return L
    out = L.copy()
    out.putalpha(L.getchannel("A").point(lambda v: int(v * max(0.0, a))))
    return out


def cloud(box, amax, col, blur=60):
    m = Image.new("L", (W, H), 0)
    ImageDraw.Draw(m).rounded_rectangle(box, 100, fill=int(255 * amax))
    m = m.filter(ImageFilter.GaussianBlur(blur))
    img = Image.new("RGBA", (W, H), col + (0,))
    img.putalpha(m)
    return img


class Ov:
    def __init__(self):
        c = C
        self.t = T()
        self.title = {"lab": text_img("IMPERIAL  ·  SERIAL", LAB(22), c["acc_light"], 0.46),
                      "w1": soft_shadow(text_img("Derazaning", DID(112), c["light"]), 16, 0.5),
                      "w2": soft_shadow(text_img("gapi bor.", ITA(100), c["acc_light"]), 16, 0.5),
                      "ep": soft_shadow(text_img("1-qism  ·  Kechqurun", RU(34), c["light"]), 12, 0.45)}
        self.subs = [[soft_shadow(text_img(s, ITA(42), c["light"]), 10, 0.55) for s in p] for p in SUBS]
        for p in self.subs:
            for im in p:
                assert im.width - 2 * PAD < 960, im.width
        self.end = {"lab": text_img("IZOHGA YOZING", LAB(26), c["acc_light"], 0.5),
                    "big": soft_shadow(text_img("NARX", DID(160), c["light"]), 16, 0.45),
                    "sub": soft_shadow(text_img("narxlarni direktga yuboramiz", ITA(44), c["light"]), 12, 0.4),
                    "imp": text_img("IMPERIAL", LAB(40), c["light"], 0.62),
                    "f1": text_img("Toshkentda o‘lchov va o‘rnatish bepul  ·  1 yil kafolat", LIG(28), c["dim_light"]),
                    "nx": soft_shadow(text_img("Davomi bor…  2-qism: Ertalab", ITA(38), c["acc_light"]), 10, 0.4),
                    "ru": text_img("Напишите NARX — пришлём цены в директ", RU(28), c["dim_light"])}
        self.sc = cloud((60, 1380, 1020, 1700), 0.55, (12, 12, 14), 55)

    def __call__(self, t):
        L = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        sc = self.t["scenes"]
        # title over the first scene
        d0 = sc[0]["len"]
        if t < d0 - 0.2:
            a = 1 - ease((t - (d0 - 0.9)) / 0.6)
            K = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            X, Y = 112, 300
            ImageDraw.Draw(K).line([(84, Y + 18), (84, Y + 18 + int(300 * ease(t / 0.8)))], fill=C["acc_light"], width=2)
            K.alpha_composite(self.title["lab"], (X - PAD, Y - PAD))
            rise(K, self.title["w1"], X - PAD - 4, Y + 34 - PAD, ease((t + 0.1) / 0.8))
            rise(K, self.title["w2"], X - PAD - 2, Y + 152 - PAD, ease((t - 0.2) / 0.8))
            if t > 0.6:
                K.alpha_composite(fade(self.title["ep"], ease((t - 0.6) / 0.5)), (X - PAD, Y + 262 - PAD))
            L.alpha_composite(fade(K, a))
        # subtitles, one paragraph at a time
        for k, s in enumerate(sc):
            a0, a1 = s["vo"] - 0.1, s["vo"] + s["vo_len"] + 0.25
            if s["scene"] == "end" or not (a0 <= t < a1):
                continue
            a = min(ease((t - a0) / 0.25), 1 - ease((t - (a1 - 0.25)) / 0.25))
            K = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            K.alpha_composite(self.sc)
            lines = self.subs[k]
            y = 1560 - (len(lines) - 1) * 30 - (len(lines)) * 26
            for im in lines:
                K.alpha_composite(im, ((W - im.width) // 2, y - PAD))
                y += 60
            L.alpha_composite(fade(K, a))
        # end card
        es = sc[-1]
        if t >= es["start"] + 0.3:
            te = t - es["start"] - 0.3
            o = self.end
            K = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            Y = 540
            for kk, yy in (("lab", Y), ("big", Y + 50), ("sub", Y + 240)):
                K.alpha_composite(o[kk], ((W - o[kk].width) // 2, yy - PAD))
            ImageDraw.Draw(K).line([(W // 2 - 60, Y + 356), (W // 2 + 60, Y + 356)], fill=C["acc_light"], width=2)
            imp = sweep(o["imp"], (te - 1.4) / 1.1) if 1.4 < te < 2.5 else o["imp"]
            K.alpha_composite(imp, ((W - imp.width) // 2, Y + 392 - PAD))
            K.alpha_composite(o["f1"], ((W - o["f1"].width) // 2, Y + 470 - PAD))
            K.alpha_composite(o["nx"], ((W - o["nx"].width) // 2, Y + 540 - PAD))
            K.alpha_composite(o["ru"], ((W - o["ru"].width) // 2, Y + 610 - PAD))
            L.alpha_composite(fade(K, ease(te / 0.5)))
            # the CTA paragraph is spoken over the card: show its words small under it
            s = es
            if s["vo"] - 0.1 <= t < s["vo"] + s["vo_len"] + 0.3:
                pass
        return L


_OV = None


def _init():
    global _OV
    _OV = Ov()


def _job(i):
    return _OV(i / FPS).tobytes()


def ov():
    os.makedirs(f"{D}/ov", exist_ok=True)
    total = T()["total"]
    n = round(total * FPS)
    out = f"{D}/ov/ov.mov"
    p = subprocess.Popen(["ffmpeg", "-nostdin", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-c:v", "prores_ks", "-profile:v", "4444", "-pix_fmt", "yuva444p10le",
                          "-vendor", "apl0", out + ".tmp.mov"], stdin=subprocess.PIPE)
    from multiprocessing import Pool
    with Pool(3, initializer=_init) as pool:
        for b in pool.imap(_job, range(n), chunksize=4):
            p.stdin.write(b)
    p.stdin.close()
    if p.wait() == 0:
        os.replace(out + ".tmp.mov", out)
    print("ov", n)


# ---------------------------------------------------------------- music + final
def music():
    tl = T()
    sc = {s["scene"]: s for s in tl["scenes"]}
    total = tl["total"]
    # D minor while the window is «exposed», F major once the kombo arrives, D minor-add9 -> F on the card
    ch = [(0.0, 38, [57, 62, 65, 69]), (sc["s2"]["start"], 34, [58, 62, 65, 69]), (sc["s3"]["start"], 36, [57, 60, 64, 67]),
          (sc["r1"]["start"], 41, [57, 60, 65, 69]), (sc["r2"]["start"], 36, [55, 60, 64, 67]),
          (sc["r3"]["start"], 41, [57, 60, 65, 72]), (sc["end"]["start"], 41, [57, 60, 64, 65, 69])]
    notes = []
    mot = [74, 77, 81, 79, 77, 74, 72, 74]
    t, i = 0.6, 0
    while t < sc["r1"]["start"] - 0.3:
        notes.append((t, mot[i % len(mot)], 0.16))
        i += 1
        t += 60 / 64 * 2
    for k, m in enumerate([72, 77, 81, 84, 89]):                     # the kombo arrives: a rising handful
        notes.append((sc["r1"]["start"] + 0.2 + 0.22 * k, m, 0.17))
    mot2 = [77, 81, 84, 81, 79, 77]
    t, i = sc["r2"]["start"] + 0.4, 0
    while t < sc["end"]["start"]:
        notes.append((t, mot2[i % len(mot2)], 0.15))
        i += 1
        t += 60 / 64 * 2
    for k, m in enumerate([65, 69, 72, 77, 81]):
        notes.append((sc["end"]["start"] + 0.3 + 0.18 * k, m, 0.14))
    kalimba_bed(f"{D}/out/bed_raw.wav", total, dict(chords=ch, notes=notes))
    print("music ok")


def final():
    tl = T()
    sc, total = tl["scenes"], tl["total"]
    ins, fl = [], []
    for k, s in enumerate(sc):
        ins += ["-i", f"{D}/seg/{s['scene']}.mp4"]
        ln = s["len"] + (XF if k < len(sc) - 1 else 0)
        fl.append(f"[{k}:v]trim=0:{ln:.4f},setpts=PTS-STARTPTS,settb=AVTB,fps={FPS},format=yuv420p[v{k}]")
    cur = "v0"
    for k in range(1, len(sc)):
        fl.append(f"[{cur}][v{k}]xfade=transition=fade:duration={XF}:offset={sc[k]['start']:.4f}[x{k}]")
        cur = f"x{k}"
    n = len(sc)
    ins += ["-i", f"{D}/ov/ov.mov", "-i", f"{D}/vo/vo_track.wav", "-i", f"{D}/out/bed_raw.wav"]
    fl.append(f"[{n}:v]format=yuva420p[o]")
    fl.append(f"[{cur}][o]overlay=0:0:eof_action=pass,trim=0:{total},format=yuv420p[vout]")
    fl.append(f"[{n + 1}:a]highpass=f=70,acompressor=threshold=-20dB:ratio=2.5:attack=5:release=120,"
              f"loudnorm=I=-16:TP=-2,aresample=48000,asplit=2[vo][key]")
    fl.append(f"[{n + 2}:a]volume=-15.5dB,aresample=48000[m]")
    fl.append("[m][key]sidechaincompress=threshold=0.03:ratio=6:attack=20:release=400[md]")
    fl.append("[vo][md]amix=inputs=2:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=9,aresample=48000[aout]")
    out = f"{D}/out/imperial_deraza_1qism.mp4"
    os.makedirs(f"{D}/out", exist_ok=True)
    run(["ffmpeg", "-nostdin", "-v", "error", "-y"] + ins + ["-filter_complex", ";".join(fl), "-map", "[vout]", "-map",
         "[aout]", "-c:v", "libx264", "-preset", "slow", "-crf", "20", "-pix_fmt", "yuv420p", "-color_primaries", "bt709",
         "-color_trc", "bt709", "-colorspace", "bt709", "-c:a", "aac", "-b:a", "192k", "-t", f"{total}", "-movflags",
         "+faststart", out + ".tmp.mp4"])
    os.replace(out + ".tmp.mp4", out)
    run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-ss", "1.6", "-i", out, "-frames:v", "1", "-q:v", "2",
         f"{D}/out/imperial_deraza_1qism_muqova.jpg"])
    print("final ok")


if __name__ == "__main__":
    cmd = sys.argv[1]
    os.makedirs(f"{D}/out", exist_ok=True)
    if cmd == "vo":
        vo(dummy="--dummy" in sys.argv)
    elif cmd == "segs":
        segs()
    elif cmd == "ov":
        ov()
    elif cmd == "music":
        music()
    elif cmd == "final":
        final()
    elif cmd == "all":
        vo()
        segs()
        ov()
        music()
        final()
