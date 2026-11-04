"""Kombo montage variants in the latest style (Didone + Palatino italic + Inter Display labels, palette from the frame).

V1 «Kun va tun»     — «Faqat qarang» style: calm, no voice, slow dissolves, title top-left with hairline
V2 «Chiziqlar orasida» — depth effect: KOMBO lives behind the fabric, visible only through the sheer stripes
V3 «Ovozli»          — «Jalyuzi deganda» style: Daniel voice, cuts on words, word-by-word subtitle with a coloured keyword
-> cs/kombo_variantlar.jpg
"""
import colorsys
import subprocess
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, "/home/claude/reels/common")
sys.path.insert(0, "/home/claude/reels/dikey_style")
import grade  # noqa: E402
from faqat_qarang import DID, ITA, LAB, LIG, RU, blob, grad, soft_shadow, text_img  # noqa: E402

D = "/home/claude/reels/kombo4"
W, H = 1080, 1920
NEUTRAL = ("huesaturation=saturation=-0.85:colors=c+b:strength=8,curves=all='0/0.03 0.25/0.245 0.5/0.52 0.75/0.79 1/0.975',"
           "eq=saturation=0.97,vignette=angle=PI/9,noise=alls=4:allf=t")   # grey fabric: no warm shift


def neutral(src, dst):
    g = grade.gains(src)
    g = np.full(3, g.mean())                       # brightness only, keep the grey grey
    subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-i", src, "-vf",
                    f"colorchannelmixer=rr={g[0]:.3f}:gg={g[1]:.3f}:bb={g[2]:.3f},{NEUTRAL}", "-q:v", "2", dst], check=True)


def hls(c, l=None, s=None):
    h, l0, s0 = colorsys.rgb_to_hls(*(np.array(c) / 255))
    return tuple(int(round(v * 255)) for v in colorsys.hls_to_rgb(h, l0 if l is None else l, s0 if s is None else s))


def palette(path):
    px = np.asarray(Image.open(path).convert("RGB").resize((180, 320)), dtype=float).reshape(-1, 3)
    rng = np.random.default_rng(3)
    c = px[rng.choice(len(px), 8, replace=False)]
    for _ in range(40):
        lab = ((px[:, None] - c[None]) ** 2).sum(-1).argmin(1)
        c = np.array([px[lab == i].mean(0) if (lab == i).any() else c[i] for i in range(8)])
    c = sorted([tuple(int(v) for v in x) for x in c], key=sum)
    graphite, silver, light = c[0], c[len(c) // 2], c[-1]
    warm = max(c, key=lambda x: (x[0] - x[2]))     # the wall (cream) — the only warm colour in the frame
    return {"scr": hls(graphite, l=0.08, s=0.06), "txt": hls(light, l=0.95, s=0.05),
            "acc": hls(warm, l=0.74, s=0.32), "dim": hls(silver, l=0.80, s=0.04),
            "taken": [graphite, silver, warm, light]}


def place(L, im, x, y, a=1.0):
    l2 = im.copy()
    l2.putalpha(l2.getchannel("A").point(lambda v: int(v * a)))
    L.alpha_composite(l2, (int(x), int(y)))


# ---------------------------------------------------------------- frames
neutral(f"{D}/frames/raw_a.jpg", f"{D}/frames/n_a.jpg")
neutral(f"{D}/frames/raw_c.jpg", f"{D}/frames/n_c.jpg")
P = palette(f"{D}/frames/n_a.jpg")
ACC, TXT, DIM, SCR = P["acc"], P["txt"], P["dim"], P["scr"]
PAD = 24


def v1():
    f = Image.open(f"{D}/frames/n_a.jpg").convert("RGBA")
    f.alpha_composite(grad(True, 1000, 0.55, SCR))
    f.alpha_composite(blob((10, 200, 960, 560), 0.45, SCR))
    L = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(L)
    X, Y = 112, 280
    d.line([(84, Y + 22), (84, Y + 300)], fill=ACC, width=2)
    place(L, soft_shadow(text_img("IMPERIAL   ·   KOMBO JALYUZI", LAB(21), ACC, 0.46)), X - PAD, Y - PAD)
    w1 = soft_shadow(text_img("Kun va", DID(118), TXT))
    place(L, w1, X - PAD - 4, Y + 30 - PAD)
    dy = DID(118).getmetrics()[0] - ITA(118).getmetrics()[0]
    place(L, soft_shadow(text_img("tun.", ITA(118), ACC)), X - PAD + w1.width - 2 * PAD + 26, Y + 30 - PAD + dy)
    place(L, soft_shadow(text_img("bitta matoda", ITA(46), TXT)), X - PAD, Y + 175 - PAD)
    place(L, soft_shadow(text_img("День и ночь — в одной ткани", RU(28), DIM)), X - PAD, Y + 240 - PAD)
    f.alpha_composite(L)
    return f


def v2():
    img = cv2.imread(f"{D}/src/photo.jpg")
    h, w = img.shape[:2]
    s = max(W / w, H / h) * 1.04
    M = np.array([[s, 0, W / 2 - s * w / 2], [0, s, H * 0.47 - s * h * 0.47]])
    fr = cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)
    tmp = f"{D}/frames/v2_bg.jpg"
    cv2.imwrite(tmp, fr)
    neutral(tmp, f"{D}/frames/n_v2.jpg")
    bg = np.asarray(Image.open(f"{D}/frames/n_v2.jpg").convert("RGB"), dtype=np.float32) / 255
    lum = cv2.cvtColor((bg * 255).astype(np.uint8), cv2.COLOR_RGB2GRAY).astype(np.float32)
    lum = cv2.blur(lum, (151, 3))                                  # stripes are horizontal: smooth along x
    local = cv2.blur(lum, (1, 181))
    sheer = np.clip((local - lum) / 25, 0, 1)                      # darker than its neighbourhood = sheer stripe
    yy, xx = np.mgrid[0:H, 0:W]
    blind = ((yy > 560) & (yy < 1800) & (xx > 70) & (xx < 1010)).astype(np.float32)
    mask = cv2.GaussianBlur(sheer * blind, (0, 0), 1.2)
    T = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    word = text_img("KOMBO", DID(205), (255, 248, 232, 255), 0.10)
    T.alpha_composite(word, (int(W / 2 - word.width / 2), 800))
    glow = T.filter(ImageFilter.GaussianBlur(10))
    t = np.asarray(T, dtype=np.float32) / 255
    g = np.asarray(glow, dtype=np.float32) / 255
    # light behind the blind: strong through the sheer stripes, faint through the dense ones
    through = (0.22 + 0.73 * mask)[..., None] * blind[..., None]
    a = np.clip(t[..., 3:4] * through + g[..., 3:4] * 0.25 * through, 0, 1)
    out = bg * (1 - a) + t[..., :3] * a
    f = Image.fromarray((out * 255).astype(np.uint8)).convert("RGBA")
    L = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    lab = text_img("IMPERIAL  ·  KUN-TUN JALYUZI", LAB(21), (70, 72, 76), 0.46)
    place(L, lab, W / 2 - lab.width / 2, 236)
    sub = text_img("chiziqlar orasidan qarang", ITA(44), (60, 62, 66))
    place(L, sub, W / 2 - sub.width / 2, 290)
    f.alpha_composite(L)
    return f


def v3():
    f = Image.open(f"{D}/frames/n_c.jpg").convert("RGBA")
    f.alpha_composite(grad(True, 700, 0.4, SCR))
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle((90, 1330, 990, 1500), 40, fill=SCR + (150,))
    f.alpha_composite(sh.filter(ImageFilter.GaussianBlur(18)))
    L = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    place(L, soft_shadow(text_img("IMPERIAL  ·  01 / 04", LAB(20), ACC, 0.46)), 112 - PAD, 260 - PAD)
    parts = [("Ochiq chiziqlar — ", LIG(52), TXT), ("yorug‘lik.", ITA(60), ACC)]
    wsum = sum(fn.getlength(t) for t, fn, _ in parts)
    x = W / 2 - wsum / 2
    for t, fn, c in parts:
        im = soft_shadow(text_img(t, fn, c))
        dy = 0 if fn is not ITA(60) else -6
        place(L, im, x - PAD, 1372 - PAD + dy)
        x += fn.getlength(t)
    ru = soft_shadow(text_img("Прозрачные полосы — свет", RU(28), DIM))
    place(L, ru, W / 2 - ru.width / 2, 1450 - PAD)
    f.alpha_composite(L)
    return f


if __name__ == "__main__":
    from compact import MED
    tiles = [(v1(), "V1 — «Kun va tun»", "ovozsiz · sekin eritish · ~20 s"),
             (v2(), "V2 — «Chiziqlar orasida»", "KOMBO mato ortida · chuqurlik effekti"),
             (v3(), "V3 — Ovozli", "Daniel ovozi · so‘zma-so‘z subtitr · ~25 s")]
    B = Image.new("RGB", (540 * 3 + 40, 1110), (22, 23, 25))
    d = ImageDraw.Draw(B)
    for i, (im, t1, t2) in enumerate(tiles):
        B.paste(im.convert("RGB").resize((540, 960), Image.LANCZOS), (10 + i * 550, 70))
        d.text((20 + i * 550, 14), t1, font=MED(28), fill=ACC)
        d.text((20 + i * 550, 1040), t2, font=LIG(24), fill=DIM)
    x = 20
    for c in P["taken"]:
        d.rounded_rectangle((x, 1078, x + 60, 1100), 8, fill=tuple(c))
        x += 70
    B.save(f"{D}/cs/kombo_variantlar.jpg", quality=92)
    print({k: v for k, v in P.items()})
