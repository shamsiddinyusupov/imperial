"""«Marmar?» opening: a still close-up of the gold-veined fabric looks like grey-veined marble; liquid gold flows
along the veins (geodesic distance inside the vein mask from each vein's upper-left end), with a glowing front and a
soft bloom; ends exactly on the real frame, which then comes alive. python3 gold.py [still.png] [out_dir] [secs]"""
import os
import sys

import cv2
import numpy as np
from skimage.graph import MCP_Geometric

FPS = 30


def vein_mask(im):
    hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV).astype(np.float32)
    h, s, v = hsv[..., 0], hsv[..., 1], hsv[..., 2]
    lum = cv2.GaussianBlur(v, (0, 0), 25)
    gold = (h > 8) & (h < 38) & (s > 45) & (v > 50)
    dark = (v < lum - 38) & (s > 22) & (h > 5) & (h < 40)
    m = (gold | dark).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(m, 8)
    keep = np.zeros_like(m)
    for k in range(1, n):
        if st[k, cv2.CC_STAT_AREA] >= 40:
            keep[lab == k] = 1
    return keep


def flow_distance(m):
    """geodesic distance from each component's upper-left end; components start with small random delays"""
    dil = cv2.dilate(m, np.ones((5, 5), np.uint8))
    cost = np.where(dil > 0, 1.0, 60.0)
    n, lab = cv2.connectedComponents(dil, connectivity=8)
    rng = np.random.default_rng(4)
    dist = np.full(m.shape, np.inf, np.float32)
    starts = []
    for k in range(1, n):
        ys, xs = np.where(lab == k)
        if len(xs) < 40:
            continue
        i = np.argmin(xs * 1.0 + ys * 0.35)
        starts.append((ys[i], xs[i], rng.uniform(0, 160)))
    mcp = MCP_Geometric(cost)
    for y, x, delay in starts:
        pass
    # one pass with all seeds; delays added via per-component offsets
    cum, _ = mcp.find_costs([(y, x) for y, x, _ in starts])
    comp_delay = {}
    for (y, x, d) in starts:
        comp_delay[lab[y, x]] = d
    off = np.zeros(m.shape, np.float32)
    for k, d in comp_delay.items():
        off[lab == k] = d
    dist = cum.astype(np.float32) + off
    dist[dil == 0] = np.inf
    return dist


def render(still_path, out_dir, secs):
    os.makedirs(out_dir, exist_ok=True)
    im = cv2.imread(still_path)
    m = vein_mask(im)
    dist = flow_distance(m)
    finite = dist[np.isfinite(dist)]
    dmax = np.percentile(finite, 99.5)
    soft = cv2.GaussianBlur(cv2.dilate(m, np.ones((3, 3), np.uint8)).astype(np.float32), (0, 0), 1.2)
    f = im.astype(np.float32)
    grey = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY).astype(np.float32)[..., None]
    marble = np.repeat(grey * 0.78 + 20, 3, axis=2) * np.array([1.0, 1.0, 1.02])      # cool grey veins
    before = f * (1 - soft[..., None]) + marble * soft[..., None]
    hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV).astype(np.float32)
    hsv[..., 1] = np.clip(hsv[..., 1] * 1.18, 0, 255)
    hsv[..., 2] = np.clip(hsv[..., 2] * 1.06, 0, 255)
    goldi = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR).astype(np.float32)
    after = f * (1 - soft[..., None]) + goldi * soft[..., None]
    n = int(round(secs * FPS))
    t_fill = secs - 0.55
    dd = np.where(np.isfinite(dist), dist, 1e9).astype(np.float32)
    for i in range(n):
        t = i / FPS
        u = min(1.0, t / t_fill)
        u = 1 - (1 - u) ** 1.6                                       # pour starts fast, settles
        front = dmax * u * 1.02
        a = np.clip((front - dd) / 22.0, 0, 1) * soft
        out = before * (1 - a[..., None]) + after * a[..., None]
        if u < 1.0:
            band = np.exp(-((dd - front) / 18.0) ** 2) * soft
            glow = cv2.GaussianBlur(band, (0, 0), 9) * 1.6 + band * 0.9
            out += glow[..., None] * np.array([40, 150, 230], np.float32)            # warm gold light (BGR)
        else:
            k = (t - t_fill) / 0.55
            sweep = np.exp(-((np.arange(im.shape[1])[None, :] + np.arange(im.shape[0])[:, None] * 0.5
                              - (-400 + k * 2200)) / 140.0) ** 2) * soft
            out += cv2.GaussianBlur(sweep, (0, 0), 6)[..., None] * np.array([30, 110, 170], np.float32)
        cv2.imwrite(f"{out_dir}/{i:04d}.jpg", np.clip(out, 0, 255).astype(np.uint8), [cv2.IMWRITE_JPEG_QUALITY, 95])
    cv2.imwrite(f"{out_dir}/mask.png", m * 255)


if __name__ == "__main__":
    still = sys.argv[1] if len(sys.argv) > 1 else "/home/claude/reels/dikey6/probe_gold.png"
    out = sys.argv[2] if len(sys.argv) > 2 else "/home/claude/reels/dikey6/goldfr"
    secs = float(sys.argv[3]) if len(sys.argv) > 3 else 3.3
    render(still, out, secs)
