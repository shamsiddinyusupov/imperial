"""«Tipologiya» (IMPERIAL, owner 22.11): prepare 36 window tiles (4:5) from the owner's plisse clips/photos.
For each video: find the calmest segment (phase correlation on a tiny grey copy), HLG->SDR, crop 4:5, 448x560 JPEG
frames. Photos: one 448x560 still. Hook tile and hero tile also at larger sizes.
python3 prep.py [tiles|hero|real]
"""
import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

import cv2
import numpy as np

D = "/home/claude/reels/tipo"
ITEMS = {i["id"]: i for i in json.load(open("/home/claude/baza_work/items.json"))}
TM = ("zscale=t=linear:npl=203,format=gbrpf32le,zscale=p=bt709,tonemap=hable:desat=0,"
      "zscale=t=bt709:m=bt709:r=tv,format=yuv420p")
TW, TH = 448, 560
# id, frame label, fabric label, crop (cx, cy, scale of full width)
TILES = [
    (574, "yong‘oq", "krem", (0.5, 0.5, 1.0)), (699, "oq ravoq", "oq", (0.5, 0.5, 1.0)),
    (577, "oq", "shaftoli", (0.40, 0.52, 0.92)), (746, "antrasit", "kulrang", (0.5, 0.5, 1.0)),
    (623, "eman", "oq", (0.5, 0.5, 1.0)), (706, "qora", "pushti", (0.5, 0.5, 1.0)),
    (645, "antrasit", "grafit", (0.5, 0.5, 1.0)), (725, "yong‘oq", "krem", (0.5, 0.5, 1.0)),
    (598, "antrasit", "binafsha", (0.5, 0.5, 1.0)), (619, "eman", "qum", (0.5, 0.5, 1.0)),
    (655, "oq", "mis", (0.5, 0.5, 1.0)), (488, "antrasit", "oq", (0.5, 0.5, 1.0)),
    (713, "yong‘oq", "pushti", (0.5, 0.48, 1.0)), (669, "oq", "kulrang", (0.5, 0.5, 1.0)),
    (385, "yong‘oq", "olxo‘ri", (0.5, 0.5, 1.0)), (736, "oq", "bej", (0.5, 0.5, 1.0)),
    (753, "antrasit", "lila", (0.5, 0.5, 1.0)), (607, "yong‘oq", "qum", (0.5, 0.5, 1.0)),
    (654, "antrasit", "grafit", (0.5, 0.5, 1.0)), (752, "yong‘oq", "krem", (0.5, 0.5, 1.0)),
    (36, "qora", "pushti", (0.5, 0.5, 1.0)), (691, "oq", "kulrang", (0.5, 0.5, 1.0)),
    (680, "yong‘oq", "atirgul", (0.5, 0.5, 1.0)), (459, "yong‘oq", "oq", (0.5, 0.5, 1.0)),
    (762, "antrasit", "lila", (0.5, 0.5, 1.0)), (658, "eman", "bej", (0.5, 0.5, 1.0)),
    (770, "antrasit", "grafit", (0.5, 0.5, 1.0)), (639, "yong‘oq", "krem", (0.5, 0.5, 1.0)),
    (730, "eman", "bej", (0.5, 0.5, 1.0)), (585, "antrasit", "kulrang", (0.5, 0.5, 1.0)),
    (494, "qora", "pushti", (0.5, 0.5, 1.0)), (581, "oq", "grafit", (0.5, 0.5, 1.0)),
    (763, "antrasit", "grafit", (0.5, 0.5, 1.0)), (660, "eman", "qum", (0.5, 0.5, 1.0)),
    (138, "antrasit", "grafit", (0.5, 0.48, 0.85)), (0, "antrasit", "grafit", (0.5, 0.5, 1.0)),
]
SEG = 8.0                    # seconds of footage per tile (ping-pong in the compositor)
HERO = 713


def portrait_vf(it):
    hdr = it.get("trc") == "arib-std-b67"
    return "scale='if(gt(iw,ih),-2,1080)':'if(gt(iw,ih),1080,-2)':flags=lanczos" + ("," + TM if hdr else "")


def calm_start(it, seg):
    """start time of the calmest `seg` seconds (least camera motion)"""
    dur = it["dur"]
    if dur <= seg + 0.6:
        return max(0.0, (dur - seg) / 2) if dur > seg else 0.15
    cmd = ["ffmpeg", "-nostdin", "-v", "error", "-i", it["path"], "-vf", "fps=6,scale=96:170,format=gray", "-f",
           "rawvideo", "-"]
    raw = subprocess.run(cmd, capture_output=True).stdout
    fr = np.frombuffer(raw, np.uint8)
    n = len(fr) // (96 * 170)
    fr = fr[: n * 96 * 170].reshape(n, 170, 96).astype(np.float32)
    win = np.hanning(96)[None, :] * np.hanning(170)[:, None]
    mot = np.zeros(n)
    for k in range(1, n):
        (dx, dy), _ = cv2.phaseCorrelate(fr[k - 1] * win, fr[k] * win)
        mot[k] = min(8.0, np.hypot(dx, dy))
    w = int(seg * 6)
    best, bi = 1e9, 0
    for s in range(1, max(2, n - w)):
        v = mot[s:s + w].sum()
        if v < best:
            best, bi = v, s
    return bi / 6.0


def crop_box(W, H, c):
    cx, cy, s = c
    cw = int(min(W, H * 4 / 5) * s) // 2 * 2
    ch = int(cw * 5 / 4) // 2 * 2
    x0 = int(np.clip(cx * W - cw / 2, 0, W - cw))
    y0 = int(np.clip(cy * H - ch / 2, 0, H - ch))
    return cw, ch, x0, y0


def tile(t):
    i, fl, fb, c = t
    it = ITEMS[i]
    out = f"{D}/tiles/{i}"
    os.makedirs(out, exist_ok=True)
    if it["kind"] == "image":
        im = cv2.imread(it["path"])
        H, W = im.shape[:2]
        if W > H:
            pass
        cw, ch, x0, y0 = crop_box(W, H, c)
        crop = im[y0:y0 + ch, x0:x0 + cw]
        cv2.imwrite(f"{out}/0000.jpg", cv2.resize(crop, (TW, TH), interpolation=cv2.INTER_AREA),
                    [cv2.IMWRITE_JPEG_QUALITY, 93])
        big = cv2.resize(crop, (720, 900), interpolation=cv2.INTER_AREA)
        cv2.imwrite(f"{out}/big.jpg", big, [cv2.IMWRITE_JPEG_QUALITY, 93])
        return i, 1, 0.0
    ss = calm_start(it, SEG)
    W, H = 1080, 1920
    cw, ch, x0, y0 = crop_box(W, H, c)
    vf = (portrait_vf(it) + f",crop={cw}:{ch}:{x0}:{y0},eq=contrast=1.03:saturation=1.04,fps=30,"
          f"scale={TW}:{TH}:flags=lanczos")
    subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-ss", f"{ss:.2f}", "-t", f"{SEG}", "-i", it["path"],
                    "-an", "-vf", vf, "-q:v", "3", f"{out}/%04d.jpg"], check=True)
    n = len([f for f in os.listdir(out) if f[0].isdigit()])
    if i == TILES[0][0]:
        vf2 = (portrait_vf(it) + f",crop={cw}:{ch}:{x0}:{y0},eq=contrast=1.03:saturation=1.04,fps=30,"
               f"scale=720:900:flags=lanczos")
        os.makedirs(f"{D}/tiles/hook", exist_ok=True)
        subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-ss", f"{ss:.2f}", "-t", f"{SEG}", "-i",
                        it["path"], "-an", "-vf", vf2, "-q:v", "3", f"{D}/tiles/hook/%04d.jpg"], check=True)
    return i, n, ss


if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else "tiles"
    if what == "tiles":
        with ThreadPoolExecutor(2) as ex:
            res = list(ex.map(tile, TILES))
        meta = {str(i): dict(n=n, ss=ss) for i, n, ss in res}
        json.dump(meta, open(f"{D}/tiles/meta.json", "w"), indent=1)
        print(res)
