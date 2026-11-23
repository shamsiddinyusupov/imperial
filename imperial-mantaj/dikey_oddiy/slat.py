"""«Har bir plastinka alohida»: a 4K still of patterned white lamellas (clip 536 at 15.5 s, own footage) with a slow
push-in; the neighbours dim, one lamella gets a drawn orange outline and lifts slightly towards the viewer with a
soft shadow. Writes seg/slat.mp4 (DUR s, 30 fps). Times are seconds from the start of the segment.
python3 slat.py"""
import subprocess

import cv2
import numpy as np

D = "/home/claude/reels/dikey7"
W, H, FPS = 1080, 1920, 30
DUR = 6.6
T_DIM, T_LINE, T_LIFT = 0.75, 0.95, 1.9
LINE = np.array([112, 176, 246], np.float32)   # BGR of the orange-gold line
GLOW = np.array([80, 150, 240], np.float32)


def ease(u):
    u = np.clip(u, 0.0, 1.0)
    return u * u * (3 - 2 * u)


def main():
    src = cv2.imread(f"{D}/src/s536_15.5.png")
    k0 = 0.55
    sm = cv2.resize(src, None, fx=k0, fy=k0, interpolation=cv2.INTER_AREA)
    c4 = np.array([1110.0, 1920.0])
    # lamella edges in 4K coords: x = a + b*y
    ys = np.array([0.0, 3840.0])
    poly4 = np.array([[988 - 0.0077 * y, y] for y in ys] + [[1254 - 0.0110 * y, y] for y in ys[::-1]])
    p = subprocess.Popen(f"ffmpeg -nostdin -v error -y -f rawvideo -pix_fmt bgr24 -s {W}x{H} -r {FPS} -i - "
                         f"-c:v libx264 -preset fast -crf 15 -pix_fmt yuv420p {D}/seg/slat.mp4", shell=True,
                         stdin=subprocess.PIPE)
    n = int(round(DUR * FPS))
    for i in range(n):
        t = i / FPS
        z = 1.0 + 0.10 * ease(t / DUR)
        s = 0.5 * z / k0
        cx, cy = c4 * k0
        dx = -6 * t
        M = np.array([[s, 0, W / 2 - s * cx + dx], [0, s, H / 2 - s * cy]], np.float32)
        bg = cv2.warpAffine(sm, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT).astype(np.float32)
        # lamella polygon in output coords
        pts = poly4 * k0
        po = np.c_[pts, np.ones(len(pts))] @ M.T
        lift = float(ease((t - T_LIFT) / 0.8))
        ls = 1 + 0.06 * lift
        mc = po.mean(0)
        L = np.array([[ls, 0, mc[0] * (1 - ls) - 6 * lift], [0, ls, mc[1] * (1 - ls) - 14 * lift]], np.float32)
        mask = np.zeros((H * 2, W * 2), np.uint8)
        cv2.fillPoly(mask, [np.round(po * 2).astype(np.int32)], 255, lineType=cv2.LINE_AA)
        mask = cv2.resize(mask, (W, H), interpolation=cv2.INTER_AREA).astype(np.float32) / 255
        mask_l = cv2.warpAffine(mask, L, (W, H), flags=cv2.INTER_LINEAR)
        slat_img = cv2.warpAffine(bg, L, (W, H), flags=cv2.INTER_LINEAR)
        dim = float(ease((t - T_DIM) / 0.7))
        grey = bg.mean(2, keepdims=True)
        back = (bg * (1 - 0.25 * dim) + grey * (0.25 * dim)) * (1 - 0.45 * dim)
        back *= 1 + dim * np.array([-0.05, 0.0, 0.06], np.float32)
        if lift > 0:
            sh = cv2.GaussianBlur(mask_l, (0, 0), 14)
            sh = np.roll(np.roll(sh, 16, 1), 22, 0)
            back *= (1 - 0.6 * lift * sh)[..., None]
        out = back * (1 - mask_l[..., None]) + slat_img * (1.0 + 0.04 * dim) * mask_l[..., None]
        # outline: the two long edges, drawn top -> bottom
        fr = float(ease((t - T_LINE) / 0.8))
        if fr > 0:
            pl = np.c_[po, np.ones(len(po))] @ L.T
            canvas = np.zeros((H, W), np.float32)
            for a, b in ((pl[0], pl[1]), (pl[3], pl[2])):
                e = a + (b - a) * fr
                cv2.line(canvas, tuple(np.round(a * 4).astype(int)), tuple(np.round(e * 4).astype(int)), 1.0, 4,
                         lineType=cv2.LINE_AA, shift=2)
            if fr >= 1:
                cv2.line(canvas, tuple(np.round(pl[0] * 4).astype(int)), tuple(np.round(pl[3] * 4).astype(int)), 1.0,
                         4, lineType=cv2.LINE_AA, shift=2)
            glow = cv2.GaussianBlur(canvas, (0, 0), 9) * 2.2
            out = out * (1 - np.clip(glow, 0, 1)[..., None] * 0.35) + GLOW * np.clip(glow, 0, 1)[..., None] * 0.35
            out = out * (1 - canvas[..., None]) + LINE * canvas[..., None]
        p.stdin.write(np.clip(out, 0, 255).astype(np.uint8).tobytes())
    p.stdin.close()
    p.wait()
    print("slat", n, "frames")


if __name__ == "__main__":
    main()
