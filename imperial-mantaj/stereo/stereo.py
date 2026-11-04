"""Reel «Jalyuzi deganda…» — the stereotype (old grey office vertical blinds, AI shot) vs today's blinds at home.

Picture follows the narration (timing.json from vo_sync.py):
  L0 «Jalyuzi… Ko‘z oldingizga, nima keldi?»          black screen, one word
  L1 «Ofis. Kulrang plankalar. Chang… To‘g‘rimi?»      the office in a narrow 4:3 window, cold, flickering
  ── the window opens to full screen, colour and music bloom (signature move #1)
  L2 «Lekin bugungi jalyuzi — bu uy. Bu — qulaylik. Bu — sizning didingiz.»   home / comf / did, cut on the words
  L3 «Plisse… Dikey… Kombo… — har bir derazaga, aniq o‘lchab.»                pl / dk / kb, cut on the words
  L4 «Toshkentda o‘lchov va o‘rnatish — bepul.»                                kb2
  L5 «Narxini bilmoqchimisiz? Izohga — «narx», deb yozing.»                    end card (light sweep over IMPERIAL, move #2)

python3 stereo.py base           -> base.mp4, cuts.json
python3 stereo.py prev 1,5,9     -> overlay previews (frames/)
python3 stereo.py ov             -> ov/*.png
python3 stereo.py audio          -> bed.wav, sfx.wav
"""
import json
import os
import subprocess
import sys
import wave

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, "/home/claude/reels/common")
sys.path.insert(0, "/home/claude/reels/dikey_style")
from compact import alpha, ease  # noqa: E402
from faqat_qarang import (DID, ITA, LAB, RU, blob, grad, put, soft_shadow, sweep, text_img)  # noqa: E402

D = "/home/claude/reels/stereo"
W, H, FPS = 1080, 1920, 30
E = ["-c:v", "libx264", "-preset", "fast", "-crf", "14", "-pix_fmt", "yuv420p", "-r", "30"]
TIM = json.load(open(f"{D}/timing.json"))
LN = TIM["lines"]
CHK = TIM.get("chunks")
TOTAL = TIM["total"]
WIN_Y0, WIN_Y1 = 555, 1365                     # 4:3 window inside 9:16
OPEN = 0.9
OFFICE = f"{D}/src/office_ai.mp4"


def run(a):
    subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y"] + a, check=True)


def dur(p):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p],
                                capture_output=True, text=True).stdout)


PARAS = ["Жалюзи... Кўз олдингизга, нима келди?",
         "Офис. Кулранг планкалар. Чанг... Тўғрими?",
         "Лекин бугунги жалюзи — бу уй. Бу — қулайлик. Бу — сизнинг дидингиз.",
         "Плиссе... Дикей... Комбо... — ҳар бир деразага, аниқ ўлчаб.",
         "Тошкентда ўлчов ва ўрнатиш — бепул.",
         "Нархини билмоқчимисиз? Изоҳга — «нарх», деб ёзинг."]


def frac(i, phrase):
    s = PARAS[i]
    k = s.index(phrase)
    letters = lambda x: sum(c.isalpha() for c in x)
    return letters(s[:k]) / letters(s)


# speech chunk that starts each phrase in this take (line, phrase) -> (chunk index, offset into the chunk)
SENT = {(0, "Кўз"): (1, 0), (1, "Кулранг"): (1, 0), (1, "Чанг"): (2, 0), (1, "Тўғрими"): (3, 0),
        (2, "уй"): (1, 0.38), (2, "Бу — қулайлик"): (2, 0), (2, "Бу — сизнинг"): (4, 0),
        (3, "Дикей"): (1, 0), (3, "Комбо"): (2, 0), (3, "ҳар бир"): (3, 0)}


def at(i, phrase):
    """Start time of the spoken phrase: the mapped speech chunk if the take matches, else the text-proportional time."""
    t = LN[i]["start"] + frac(i, phrase) * LN[i]["len"]
    if not CHK:
        return t
    k = SENT.get((i, phrase))
    if k is not None and k[0] < len(CHK[i]):
        return CHK[i][k[0]][0] + k[1]
    near = min((c[0] for c in CHK[i]), key=lambda s: abs(s - t))
    return near if abs(near - t) < 0.35 else t


def cuts():
    c = {}
    c["office"] = LN[1]["start"] - 0.4
    c["open"] = LN[1]["start"] + LN[1]["len"] + 0.12
    c["w_ofis"] = LN[1]["start"]
    c["w_kul"] = at(1, "Кулранг")
    c["w_chang"] = at(1, "Чанг")
    c["w_tog"] = at(1, "Тўғрими")
    c["hook2"] = at(0, "Кўз")
    c["uy"] = at(2, "уй")
    c["comf"] = at(2, "Бу — қулайлик") - 0.06
    c["did"] = at(2, "Бу — сизнинг") - 0.06
    c["pl"] = LN[3]["start"] - 0.06
    c["dk"] = at(3, "Дикей") - 0.06
    c["kb"] = at(3, "Комбо") - 0.06
    c["har"] = at(3, "ҳар бир")
    c["kb2"] = LN[4]["start"] - 0.08
    c["bepul"] = at(4, "бепул")
    c["end"] = LN[5]["start"] - 0.1
    c["total"] = TOTAL
    return c


C = cuts()


# ---------------------------------------------------------------- base
OLD = ("crop=iw:iw*0.75:0:ih*0.10,scale=1080:810:flags=lanczos,fps=30,"            # lamp + blinds fill the 4:3 window
       "hue=s=0.22,colorbalance=rs=-0.03:gs=0.03:bs=0.01:rm=-0.02:gm=0.035:bm=0.0:rh=-0.02:gh=0.02:bh=0.01,"
       "eq=contrast=0.86:gamma=1.04:brightness='-0.015+0.02*sin(2*PI*t*9.7)*sin(2*PI*t*1.3)':eval=frame,"
       "gblur=sigma=0.9,noise=alls=16:allf=t,vignette=angle=PI/4.5,pad=1080:1920:0:555:black")


def piece(name, src, length, start=0.0, vf="null"):
    have = dur(src) - start
    pad = max(0.0, length - have + 0.05)
    f = f"{vf},tpad=stop_mode=clone:stop_duration={pad:.3f}" if pad > 0 else vf
    out = f"{D}/seg/P_{name}.mp4"
    run(["-ss", f"{start:.3f}", "-i", src, "-t", f"{length:.3f}", "-an", "-vf", f + ",fps=30,settb=AVTB,setpts=PTS-STARTPTS,format=yuv420p"] + E + [out])
    return out


def base():
    if not os.path.exists(OFFICE):            # placeholder until the AI clip arrives
        run(["-f", "lavfi", "-i", "color=c=0x8c918b:s=1080x1920:d=6,format=gray,geq=lum='128+38*sin(X/22+0.3*sin(Y/200+T))':cb=128:cr=128",
             "-t", "6", "-pix_fmt", "yuv420p", f"{D}/seg/office_placeholder.mp4"])
        osrc = f"{D}/seg/office_placeholder.mp4"
    else:
        osrc = OFFICE
    seq = [("black", None, C["office"]),
           ("office", osrc, C["open"] + OPEN - C["office"]),
           ("home", f"{D}/seg/home.mp4", C["comf"] - C["open"]),
           ("comf", f"{D}/seg/comf.mp4", C["did"] - C["comf"]),
           ("did", f"{D}/seg/did.mp4", C["pl"] - C["did"]),
           ("pl", f"{D}/seg/pl.mp4", C["dk"] - C["pl"]),
           ("dk", f"{D}/seg/dk.mp4", C["kb"] - C["dk"]),
           ("kb", f"{D}/seg/kb.mp4", C["kb2"] - C["kb"]),
           ("kb2", f"{D}/seg/kb2.mp4", C["end"] + 0.25 - C["kb2"]),
           ("end", f"{D}/seg/end.mp4", TOTAL - (C["end"] - 0.25))]
    files = []
    for name, src, L in seq:
        if name == "black":
            out = f"{D}/seg/P_black.mp4"
            run(["-f", "lavfi", "-i", f"color=c=black:s=1080x1920:r=30:d={L:.3f}", "-vf", "settb=AVTB,format=yuv420p"] + E + [out])
            files.append(out)
        elif name == "office":
            files.append(piece(name, src, L, 0.0, OLD))
        else:
            files.append(piece(name, src, L))
    ins = sum((["-i", f] for f in files), [])
    tb = ",settb=AVTB,fps=30"
    fc = [";".join(f"[{i}:v]null{tb}[i{i}]" for i in range(10)),
          f"[i0][i1]concat=n=2:v=1{tb}[a]",
          f"[a][i2]xfade=transition=fade:duration={OPEN}:offset={C['open']:.3f}{tb}[b]",
          f"[b][i3][i4][i5][i6][i7][i8]concat=n=7:v=1{tb}[c]",
          f"[c][i9]xfade=transition=fade:duration=0.5:offset={C['end'] - 0.25:.3f},format=yuv420p[v]"]
    run(ins + ["-filter_complex", ";".join(fc), "-map", "[v]", "-t", f"{TOTAL:.3f}"] + E + [f"{D}/base.mp4"])
    json.dump(C, open(f"{D}/cuts.json", "w"), indent=1)
    print({k: round(v, 2) for k, v in C.items()}, "base", round(dur(f"{D}/base.mp4"), 2))


# ---------------------------------------------------------------- overlay
class Overlay:
    def __init__(self):
        from style_test import palette
        run(["-ss", "1.5", "-i", f"{D}/seg/home.mp4", "-frames:v", "1", "-q:v", "2", f"{D}/frames/pal.jpg"])
        _, ui = palette(f"{D}/frames/pal.jpg")
        self.ACC, self.TXT, self.DIM, self.SCR = ui["accent"], ui["text"], ui["dim"], ui["scrim"]
        A, T_, Dm = self.ACC, self.TXT, self.DIM
        COLD, COLD2 = (176, 184, 180), (214, 218, 214)
        self.SCRIM = grad(True, 1000, 0.5, self.SCR)
        self.BLOB = blob((10, 220, 980, 600), 0.5, self.SCR)
        self.DARK = Image.new("RGBA", (W, H), self.SCR + (182,))
        # hook on black
        self.h1 = soft_shadow(text_img("Jalyuzi.", DID(150), T_))
        self.h2 = soft_shadow(text_img("Ko‘z oldingizga nima keldi?", ITA(56), A))
        self.h3 = soft_shadow(text_img("Что вы сейчас представили?", RU(30), Dm))
        # office words (cold, under the window)
        self.o_words = [text_img(w, LAB(24), COLD, 0.42) for w in ("OFIS", "·  KULRANG PLANKALAR", "·  CHANG")]
        self.o_tog = text_img("To‘g‘rimi?", ITA(64), COLD2)
        self.o_ru = text_img("Офис. Серые ламели. Пыль. Верно?", RU(28), COLD)
        # L2
        self.l_lab = soft_shadow(text_img("IMPERIAL   ·   BUGUN", LAB(21), A, 0.46))
        self.l_head = soft_shadow(text_img("Bugungi jalyuzi —", DID(88), T_))
        self.l_acc = [soft_shadow(text_img(w, ITA(96), A)) for w in ("uy.", "qulaylik.", "sizning didingiz.")]
        self.l_ru = soft_shadow(text_img("Сегодня жалюзи — это дом, уют и ваш вкус", RU(28), Dm))
        # L3
        self.t_lab = soft_shadow(text_img("IMPERIAL   ·   TURLAR", LAB(21), A, 0.46))
        self.t_word = [soft_shadow(text_img(w, DID(118), T_)) for w in ("Plisse.", "Dikey.", "Kombo.")]
        self.t_sub = soft_shadow(text_img("har bir derazaga — aniq o‘lchab", ITA(50), A))
        self.t_ru = soft_shadow(text_img("Точно по размеру каждого окна", RU(28), Dm))
        # L4
        self.b_lab = soft_shadow(text_img("TOSHKENT", LAB(21), A, 0.46))
        self.b_h1 = soft_shadow(text_img("O‘lchov va o‘rnatish —", DID(80), T_))
        self.b_acc = soft_shadow(text_img("bepul.", ITA(110), A))
        self.b_ru = soft_shadow(text_img("Замер и установка по Ташкенту — бесплатно", RU(28), Dm))
        # end card
        self.e_lab = soft_shadow(text_img("IZOHGA YOZING", LAB(21), A, 0.5))
        self.e_key = soft_shadow(text_img("NARX", DID(150), T_, 0.08))
        self.e_sub = soft_shadow(text_img("narxlarni direktga yuboramiz", ITA(44), A))
        self.e_brand = text_img("IMPERIAL", DID(64), T_, 0.32)
        from faqat_qarang import LIG
        self.e_tag = soft_shadow(text_img("PLISSE  ·  DIKEY  ·  KOMBO  ·  TOSHKENT", LAB(19), A, 0.42))
        self.e_fact = soft_shadow(text_img("Toshkentda o‘lchov va o‘rnatish bepul  ·  1 yil kafolat", LIG(27), Dm))
        self.e_ru = soft_shadow(text_img("Напишите NARX — пришлём цены в директ", RU(27), Dm))

    # -- pieces
    def hook(self, L, t):
        out = 1 - ease((t - (C["office"] - 0.35)) / 0.3)
        if out <= 0:
            return
        X, PAD = 112, 24
        a1 = ease((t - LN[0]["start"] + 0.1) / 0.8)
        put(L, alpha(self.h1, out), X - PAD - 4, 760 - PAD, a1, dy=10 * (1 - a1))
        a2 = ease((t - C["hook2"]) / 0.6)
        put(L, alpha(self.h2, out), X - PAD, 1010 - PAD, a2, dx=-12 * (1 - a2))
        a3 = ease((t - C["hook2"] - 0.5) / 0.6)
        put(L, alpha(self.h3, out), X - PAD, 1100 - PAD, a3)

    def office(self, L, t):
        t0, to = C["office"], C["open"]
        if t < t0 - 0.05 or t > to + OPEN:
            return
        # bars around the 4:3 window; they slide away when the window opens
        p = ease((t - to) / OPEN) if t > to else 0
        top = int(WIN_Y0 * (1 - p))
        bot = int(WIN_Y1 + (H - WIN_Y1) * p)
        d = ImageDraw.Draw(L)
        if top > 0:
            d.rectangle((0, 0, W, top), fill=(0, 0, 0, 255))
        if bot < H:
            d.rectangle((0, bot, W, H), fill=(0, 0, 0, 255))
        # tube-light start: the window flickers on
        k = int((t - t0) / 0.07)
        if 0 <= k < 6:
            a = [1.0, 0.15, 1.0, 0.45, 0.85, 0.0][k]
            if a > 0:
                d.rectangle((0, WIN_Y0, W, WIN_Y1), fill=(0, 0, 0, int(255 * a)))
        elif t < t0:
            d.rectangle((0, WIN_Y0, W, WIN_Y1), fill=(0, 0, 0, 255))
        # words under the window
        wout = 1 - ease((t - to) / 0.35)
        if wout <= 0:
            return
        x, y, PAD = 112, WIN_Y1 + 40, 24
        for w_img, key in zip(self.o_words, ("w_ofis", "w_kul", "w_chang")):
            a = ease((t - C[key]) / 0.35) * wout
            put(L, w_img, x - PAD, y - PAD, a)
            x += w_img.width - 2 * PAD + 22
        a = ease((t - C["w_tog"]) / 0.45) * wout
        put(L, self.o_tog, 112 - PAD, y + 50 - PAD, a, dx=-10 * (1 - a))
        a = ease((t - C["w_ofis"] - 0.4) / 0.6) * wout
        put(L, self.o_ru, 112 - PAD, WIN_Y0 - 70 - PAD, a)

    def block_scrim(self, L, t):
        s0, s1 = C["open"] + 0.3, C["end"]
        if not (s0 < t < s1 + 0.3):
            return
        a = ease((t - s0) / 0.5) * (1 - ease((t - (s1 - 0.2)) / 0.4))
        L.alpha_composite(alpha(self.SCRIM, a))
        L.alpha_composite(alpha(self.BLOB, a))

    def rule(self, L, t, t0, t1, y, hgt):
        p = ease((t - t0) / 0.6) * (1 - ease((t - (t1 - 0.3)) / 0.3))
        if p > 0:
            ImageDraw.Draw(L).line([(84, y), (84, y + hgt * ease((t - t0) / 0.6))], fill=self.ACC + (int(255 * p),), width=2)

    def l2(self, L, t):
        t0, t1 = C["open"] + 0.45, C["pl"]
        if not (t0 - 0.05 < t < t1):
            return
        out = 1 - ease((t - (t1 - 0.3)) / 0.3)
        X, Y, PAD = 112, 290, 24
        self.rule(L, t, t0, t1, Y + 10, 300)
        a = ease((t - t0) / 0.5) * out
        put(L, self.l_lab, X - PAD, Y - PAD, a, dx=-10 * (1 - a))
        a = ease((t - t0 - 0.15) / 0.6) * out
        put(L, self.l_head, X - PAD - 3, Y + 40 - PAD, a, dx=-12 * (1 - a))
        keys = ["uy", "comf", "did"]
        for k, img in enumerate(self.l_acc):
            ta = C[keys[k]]
            tb = C[keys[k + 1]] if k < 2 else t1
            if ta - 0.05 < t < tb:
                a = ease((t - ta) / 0.4) * (1 - ease((t - (tb - 0.18)) / 0.18) if k < 2 else out)
                put(L, img, X - PAD - 3, Y + 140 - PAD, a, dy=10 * (1 - ease((t - ta) / 0.4)))
        a = ease((t - t0 - 0.6) / 0.6) * out
        put(L, self.l_ru, X - PAD, Y + 270 - PAD, a)

    def l3(self, L, t):
        t0, t1 = C["pl"], C["kb2"]
        if not (t0 - 0.05 < t < t1):
            return
        out = 1 - ease((t - (t1 - 0.3)) / 0.3)
        X, Y, PAD = 112, 290, 24
        self.rule(L, t, t0, t1, Y + 10, 290)
        a = ease((t - t0) / 0.5) * out
        put(L, self.t_lab, X - PAD, Y - PAD, a, dx=-10 * (1 - a))
        keys = ["pl", "dk", "kb"]
        for k, img in enumerate(self.t_word):
            ta = C[keys[k]] + 0.04
            tb = C[keys[k + 1]] if k < 2 else t1
            if ta - 0.05 < t < tb:
                a = ease((t - ta) / 0.35) * (1 - ease((t - (tb - 0.15)) / 0.15) if k < 2 else out)
                put(L, img, X - PAD - 4, Y + 36 - PAD, a, dy=10 * (1 - ease((t - ta) / 0.35)))
        a = ease((t - C["har"]) / 0.5) * out
        put(L, self.t_sub, X - PAD, Y + 190 - PAD, a, dx=-12 * (1 - a))
        a = ease((t - C["har"] - 0.35) / 0.6) * out
        put(L, self.t_ru, X - PAD, Y + 262 - PAD, a)

    def l4(self, L, t):
        t0, t1 = C["kb2"] + 0.05, C["end"] + 0.1
        if not (t0 - 0.05 < t < t1):
            return
        out = 1 - ease((t - (t1 - 0.35)) / 0.35)
        X, Y, PAD = 112, 290, 24
        self.rule(L, t, t0, t1, Y + 10, 300)
        a = ease((t - t0) / 0.5) * out
        put(L, self.b_lab, X - PAD, Y - PAD, a, dx=-10 * (1 - a))
        a = ease((t - t0 - 0.1) / 0.6) * out
        put(L, self.b_h1, X - PAD - 3, Y + 40 - PAD, a, dx=-12 * (1 - a))
        a = ease((t - C["bepul"]) / 0.45) * out
        put(L, self.b_acc, X - PAD - 3, Y + 130 - PAD, a, dy=10 * (1 - ease((t - C["bepul"]) / 0.45)))
        a = ease((t - C["bepul"] - 0.35) / 0.6) * out
        put(L, self.b_ru, X - PAD, Y + 270 - PAD, a)

    def end(self, L, t):
        ti = C["end"]
        if t < ti:
            return
        L.alpha_composite(alpha(self.DARK, ease((t - ti) / 0.7)))
        cx = W / 2
        a = lambda d0, dd=0.6: ease((t - ti - d0) / dd)
        put(L, self.e_lab, cx - self.e_lab.width / 2, 610, a(0.3), dy=8 * (1 - a(0.3)))
        put(L, self.e_key, cx - self.e_key.width / 2, 640, a(0.45, 0.7), dy=14 * (1 - a(0.45, 0.7)))
        put(L, self.e_sub, cx - self.e_sub.width / 2, 835, a(0.9))
        p = a(1.1, 0.7)
        if p > 0:
            ImageDraw.Draw(L).line([(cx - 60 * p, 960), (cx + 60 * p, 960)], fill=self.ACC + (255,), width=2)
        sp = (t - ti - 1.8) / 1.1
        b = sweep(self.e_brand, sp) if 0 < sp < 1 else self.e_brand
        put(L, soft_shadow(b), cx - self.e_brand.width / 2, 980, a(1.25, 0.7))
        put(L, self.e_tag, cx - self.e_tag.width / 2, 1080, a(1.4))
        put(L, self.e_fact, cx - self.e_fact.width / 2, 1140, a(1.6))
        put(L, self.e_ru, cx - self.e_ru.width / 2, 1186, a(1.75))

    def __call__(self, t):
        L = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        self.office(L, t)
        self.hook(L, t)
        self.block_scrim(L, t)
        self.l2(L, t)
        self.l3(L, t)
        self.l4(L, t)
        self.end(L, t)
        return L


# ---------------------------------------------------------------- sound design
SR = 48000


def sfx(path):
    rng = np.random.default_rng(4)
    n = int((TOTAL + 1) * SR)
    x = np.zeros(n)
    t0, to = C["office"], C["open"]
    # fluorescent starter: three ticks as the window flickers on
    for k, dt in enumerate((0.0, 0.14, 0.27)):
        i = int((t0 + dt) * SR)
        click = rng.normal(0, 1, 260) * np.exp(-np.arange(260) / 40) * (0.5 - 0.1 * k)
        x[i:i + 260] += click
    # hum: 100 Hz mains buzz with harmonics, slow wobble; dies with a falling pitch when the window opens
    a, b = int(t0 * SR), int((to + 0.45) * SR)
    tt = np.arange(b - a) / SR
    f = 100 * (1 - 0.25 * np.clip((tt - (to - t0)) / 0.45, 0, 1) ** 2)
    ph = 2 * np.pi * np.cumsum(f) / SR
    hum = sum(np.sin(h * ph) / h ** 0.8 for h in (1, 2, 3, 5, 7)) * (1 + 0.15 * np.sin(2 * np.pi * 0.7 * tt))
    env = np.minimum(1, tt / 0.25) * np.clip(1 - (tt - (to - t0)) / 0.45, 0, 1)
    x[a:b] += hum * env * 0.035
    # slats knocking softly in the draft
    for tk in (t0 + 1.1, t0 + 1.9, t0 + 2.35, t0 + 3.6):
        if tk < to:
            i = int(tk * SR)
            m = int(0.05 * SR)
            k = rng.normal(0, 1, m) * np.exp(-np.arange(m) / (0.008 * SR))
            k = np.convolve(k, np.ones(6) / 6, "same")
            x[i:i + m] += k * 0.22
    # opening: soft air swell
    i = int((to - 0.2) * SR)
    m = int(1.3 * SR)
    sw = rng.normal(0, 1, m)
    sw = np.convolve(sw, np.ones(40) / 40, "same")
    sw *= np.sin(np.linspace(0, np.pi, m)) ** 2
    x[i:i + m] += sw * 0.12
    x = x[: int(TOTAL * SR)]
    pcm = (np.clip(x / (np.abs(x).max() + 1e-9) * 0.5, -1, 1) * 32767).astype(np.int16)
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


def audio():
    from bloom_bed import bloom_bed
    secs = [C["open"] + 0.2, C["pl"], C["kb2"]]
    bloom_bed(f"{D}/bed.wav", TOTAL, C["open"] + 0.15, secs, C["end"] + 0.05, seed=9)
    sfx(f"{D}/sfx.wav")


OV = None


def job(i):
    OV(i / FPS).save(f"{D}/ov/{i:04d}.png", compress_level=1)


if __name__ == "__main__":
    os.makedirs(f"{D}/ov", exist_ok=True)
    os.makedirs(f"{D}/frames", exist_ok=True)
    cmd = sys.argv[1]
    if cmd == "base":
        base()
    elif cmd == "audio":
        audio()
    elif cmd == "prev":
        OV = Overlay()
        for s in sys.argv[2].split(","):
            t = float(s)
            run(["-ss", f"{t:.3f}", "-i", f"{D}/base.mp4", "-frames:v", "1", "-q:v", "2", f"{D}/frames/b_{s}.jpg"])
            f = Image.open(f"{D}/frames/b_{s}.jpg").convert("RGBA")
            f.alpha_composite(OV(t))
            f.convert("RGB").save(f"{D}/frames/p_{s}.jpg", quality=90)
    elif cmd == "ov":
        OV = Overlay()
        for f in os.listdir(f"{D}/ov"):
            os.remove(f"{D}/ov/{f}")
        n = round(TOTAL * FPS)
        from multiprocessing import Pool
        with Pool(2) as p:
            p.map(job, range(n), chunksize=20)
        print("frames", n)
