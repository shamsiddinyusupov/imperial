"""Find the cut lines of the kombo in the wide plate (seg/wide.png, 1296x2304): light->dark edges tracked across x."""
import json
import cv2
import numpy as np

im = cv2.imread("seg/wide.png")
g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY).astype(np.float32)
gs = cv2.GaussianBlur(g, (0, 0), sigmaX=6, sigmaY=1.2)
dy = np.diff(gs, axis=0)          # dy[y] = g[y+1]-g[y]
XS = list(range(16, 1240, 8))


def cands(x, sign, thr):
    col = dy[:, x] * sign
    return [y for y in range(3, len(col) - 3) if col[y] > thr and col[y] == col[y - 3:y + 4].max()]


def track(y0, sign, thr, x0=640, tol=5):
    pts = {}
    for direction in (1, -1):
        y, slope = y0, 0.0
        xs = [x for x in XS if (x >= x0 if direction == 1 else x < x0)]
        xs = xs if direction == 1 else xs[::-1]
        prev = x0
        for x in xs:
            pred = y + slope * (x - prev)
            c = [v for v in cands(x, sign, thr) if abs(v - pred) <= tol]
            if c:
                v = min(c, key=lambda v: abs(v - pred))
                if x != prev:
                    slope = 0.7 * slope + 0.3 * (v - y) / (x - prev)
                y, prev = v, x
                pts[x] = v
    return pts


def fitq(pts):
    x = np.array(sorted(pts)); y = np.array([pts[k] for k in x])
    c = np.polyfit(x, y, 2)
    r = y - np.polyval(c, x)
    keep = np.abs(r) < 2.5
    c = np.polyfit(x[keep], y[keep], 2)
    return c.tolist(), int(keep.sum()), float(np.abs(y[keep] - np.polyval(c, x[keep])).max())


out = {}
for name, sign, thr in (("neg", -1, 5), ("pos", 1, 5)):
    seeds = cands(640, sign, thr)
    for s in seeds:
        pts = track(s, sign, thr)
        if len(pts) > 60:
            c, n, err = fitq(pts)
            out[f"{name}_{s}"] = {"c": c, "n": n, "err": round(err, 2), "y640": s,
                                  "y_left": round(np.polyval(c, 16), 1), "y_right": round(np.polyval(c, 1230), 1)}
for k, v in sorted(out.items(), key=lambda kv: kv[1]["y640"]):
    print(k, v["n"], v["err"], v["y_left"], v["y640"], v["y_right"])
json.dump(out, open("seg/edges_raw.json", "w"), indent=1)
