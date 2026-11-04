"""Ad versions of two Reels: the comment call («Izohga NARX yozing») becomes «press the button below»,
because in a Meta ad the person writes through the ad's button (Direct message or lead form), not in comments.

  ikki_yol  — «Derazangizga — ikki yo‘l»: CTA pill + end card replaced, the spoken comment call
              (last voice line) removed, video ends 4 s after the end card opens.
  dikey     — «Bu deraza 3 kunda o‘zgardi»: CTA pill replaced.

python3 make_ad_versions.py prev     -> preview frames
python3 make_ad_versions.py render   -> out/*.mp4
"""
import os
import subprocess
import sys
from multiprocessing import Pool

import numpy as np
from PIL import Image, ImageDraw

D = "/home/claude/reels/ads"
os.makedirs(f"{D}/out", exist_ok=True)
os.makedirs(f"{D}/frames", exist_ok=True)


def run(a):
    subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y"] + a, check=True)


# ---------------------------------------------------------------- «Ikki yo‘l»
sys.path.insert(0, "/home/claude/reels/tong3")
import tong3_compact as T  # noqa: E402

IY_END = T.CUT["t4"]
IY_TOTAL = round(IY_END + 4.2, 2)


def iy_cta():
    L = Image.new("RGBA", (T.W, 90), (0, 0, 0, 0))
    d = ImageDraw.Draw(L)
    f1, f2 = T.MED(26), T.SEMI(26)
    parts = [("Narxini bilish uchun — ", f1, T.CREAM), ("pastdagi tugmani", f2, T.GOLD), (" bosing", f1, T.CREAM)]
    w = sum(f.getlength(t) for t, f, _ in parts) + 34
    x = (T.W - w) / 2
    d.rounded_rectangle((x - 30, 8, x + w + 30, 70), 31, fill=(14, 12, 10, 200), outline=T.GOLD, width=1)
    for t, f, c in parts:
        d.text((x, 22), t, font=f, fill=c)
        x += f.getlength(t)
    ax, ay = x + 20, 39                                     # small down chevron towards Meta's button
    d.line([(ax - 8, ay - 4), (ax, ay + 4), (ax + 8, ay - 4)], fill=T.GOLD, width=3)
    return L


def iy_end():
    L = Image.new("RGBA", (T.W, T.H), (0, 0, 0, 0))
    d = ImageDraw.Draw(L)

    def ctr(text, f, y, col, tr=0.0):
        T.tracked(d, ((T.W - T.tw(text, f, tr)) / 2, y), text, f, col, tr)

    ctr("PASTDAGI TUGMANI BOSING", T.MED(22), 600, T.GOLD, 0.34)
    ctr("Bepul o‘lchovga yoziling.", T.SER(64), 640, T.CREAM)
    ctr("01 · Yangi jalyuzi — narx va bepul o‘lchov", T.SER(34), 742, T.CREAM)
    ctr("02 · Eski jalyuzi — yangilash bo‘yicha javob", T.SER(34), 792, T.CREAM)
    d.line([(T.W / 2 - 50, 880), (T.W / 2 + 50, 880)], fill=T.GOLD, width=2)
    ctr("IMPERIAL", T.SER(56), 912, T.CREAM, 0.22)
    ctr("PLISSE  ·  KOMBO  ·  TOSHKENT", T.MED(20), 986, T.GOLD, 0.34)
    ctr("Toshkentda o‘lchov va o‘rnatish bepul  ·  3 kunda tayyor  ·  1 yil kafolat", T.LIT(23), 1036, T.DIM)
    ctr("Нажмите кнопку ниже — бесплатный замер  ·  @imperial_jalyuzi_uz", T.LIT(22), 1074, T.DIM)
    cx, cy = T.W / 2, 1150
    d.line([(cx - 16, cy - 7), (cx, cy + 7), (cx + 16, cy - 7)], fill=T.GOLD, width=3)
    return T.shadow(L)


T.CTA = iy_cta()
T.END = iy_end()


def iy_job(i):
    T.overlay(i / 30).save(f"{D}/ov_iy/{i:04d}.png", compress_level=1)


def iy_render():
    os.makedirs(f"{D}/ov_iy", exist_ok=True)
    n = round(IY_TOTAL * 30)
    with Pool(2) as p:
        p.map(iy_job, range(n), chunksize=20)
    # voice: drop the spoken comment call (last line) — keep everything before it
    cut = T.LN[-1]["start"] - 0.08
    vf = (f"{D}/vo_iy.wav")
    run(["-i", "/home/claude/reels/tong3/vo_track.wav", "-af", f"volume=enable='gte(t,{cut:.2f})':volume=0", vf])
    TE = IY_END
    voice = "highpass=f=70,lowpass=f=12000,acompressor=threshold=-20dB:ratio=3:attack=8:release=120:makeup=2,aformat=channel_layouts=stereo"
    run(["-i", "/home/claude/reels/tong3/base.mp4", "-framerate", "30", "-i", f"{D}/ov_iy/%04d.png",
         "-i", "/home/claude/reels/tong3/bed.wav", "-i", vf, "-filter_complex",
         f"[0:v]split[a][b];[b]gblur=sigma=26[bl];[a][bl]blend=all_expr='A*(1-clip((T-{TE})/0.6,0,1))+B*clip((T-{TE})/0.6,0,1)'[bg];"
         f"[bg][1:v]overlay=0:0:format=auto,format=yuv420p[v];"
         f"[3:a]{voice},asplit=2[vo][sc];[2:a]volume=0.6[bed];[bed][sc]sidechaincompress=threshold=0.02:ratio=8:attack=15:release=400:makeup=1[duck];"
         f"[duck][vo]amix=inputs=2:weights='1 1.3':normalize=0,afade=t=out:st={IY_TOTAL - 1.2}:d=1.2,loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000[a]",
         "-map", "[v]", "-map", "[a]", "-t", f"{IY_TOTAL}", "-c:v", "libx264", "-preset", "slow", "-crf", "20",
         "-maxrate", "8M", "-bufsize", "16M", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart",
         f"{D}/out/reklama_ikki_yol.mp4"])


# ---------------------------------------------------------------- «Bu deraza 3 kunda o‘zgardi»
sys.path.insert(0, "/home/claude/reels/ba")
import ba_reel as B  # noqa: E402


def ba_cta():
    L = Image.new("RGBA", (B.W, B.H), (0, 0, 0, 0))
    d = ImageDraw.Draw(L)
    f = B.SEMI(50)
    t = "Bepul o‘lchovga yoziling"
    w = f.getlength(t)
    x0, y0 = 84, 1438
    d.rounded_rectangle((x0, y0, x0 + w + 150, y0 + 104), 52, fill=B.GOLD)
    d.text((x0 + 40, y0 + 24), t, font=f, fill=B.INK)
    ax, ay = x0 + w + 92, y0 + 52
    d.polygon([(ax - 18, ay - 12), (ax + 18, ay - 12), (ax, ay + 14)], fill=B.INK)
    d.text((88, y0 + 128), "Pastdagi tugmani bosing · Нажмите кнопку ниже", font=B.REG(32), fill=(214, 206, 192))
    d.text((88, y0 + 176), "@imperial_jalyuzi_uz", font=B.MED(32), fill=B.GOLD)
    return B.shadow(L, 12, 0.5)


B.CTA = ba_cta()


def ba_job(i):
    B.overlay(i / B.FPS).save(f"{D}/ov_ba/{i:04d}.png", compress_level=1)


def ba_render():
    os.makedirs(f"{D}/ov_ba", exist_ok=True)
    with Pool(2) as p:
        p.map(ba_job, range(B.NF), chunksize=10)
    run(["-i", "/home/claude/reels/ba/base.mp4", "-framerate", "30", "-i", f"{D}/ov_ba/%04d.png",
         "-i", "/home/claude/reels/ba/music_ba.wav", "-filter_complex",
         "[0:v][1:v]overlay=0:0:format=auto,format=yuv420p[v];[2:a]loudnorm=I=-14:TP=-1.5,aresample=48000[a]",
         "-map", "[v]", "-map", "[a]", "-t", f"{B.TOTAL}", "-c:v", "libx264", "-preset", "slow", "-crf", "20",
         "-maxrate", "8M", "-bufsize", "16M", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart",
         f"{D}/out/reklama_dikey_3_kun.mp4"])


if __name__ == "__main__":
    if sys.argv[1] == "prev":
        for t in (5.0, IY_END + 2.5):
            fr = Image.open("/home/claude/reels/ads/frames/iy_bg.jpg").convert("RGBA") if False else None
        subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-ss", "8", "-i", "/home/claude/reels/tong3/base.mp4",
                        "-frames:v", "1", f"{D}/frames/iy_a.jpg"], check=True)
        subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-ss", "25", "-i", "/home/claude/reels/tong3/base.mp4",
                        "-vf", "gblur=sigma=26", "-frames:v", "1", f"{D}/frames/iy_b.jpg"], check=True)
        subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-ss", "13.5", "-i", "/home/claude/reels/ba/base.mp4",
                        "-frames:v", "1", f"{D}/frames/ba_a.jpg"], check=True)
        out = []
        for bg, ov in (("iy_a.jpg", T.overlay(8.0)), ("iy_b.jpg", T.overlay(IY_END + 2.5)), ("ba_a.jpg", B.overlay(13.5))):
            im = Image.open(f"{D}/frames/{bg}").convert("RGBA").resize((1080, 1920))
            im.alpha_composite(ov)
            out.append(im.convert("RGB").resize((360, 640)))
        S = Image.new("RGB", (370 * 3, 640), "white")
        for i, im in enumerate(out):
            S.paste(im, (i * 370, 0))
        S.save(f"{D}/frames/prev.jpg", quality=90)
    else:
        iy_render()
        ba_render()
        print("ok", IY_TOTAL)
