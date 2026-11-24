import json, subprocess, sys
from PIL import Image, ImageDraw
from concurrent.futures import ThreadPoolExecutor
it = {e["id"]: e for e in json.load(open("/home/claude/baza_work/items.json"))}
TM = "zscale=t=linear:npl=203,format=gbrpf32le,zscale=p=bt709,tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv,format=yuv420p"
def row(i, n=6, hh=180):
    e = it[i]; p = e["path"]
    d = float(subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",p],capture_output=True,text=True).stdout)
    trc = subprocess.run(["ffprobe","-v","error","-select_streams","v:0","-show_entries","stream=color_transfer","-of","csv=p=0",p],capture_output=True,text=True).stdout.strip()
    ims = []
    for k in range(n):
        t = d * (k + 0.5) / n
        vf = f"scale=-2:{hh}" + ("," + TM if trc == "arib-std-b67" else "") + ",format=rgb24"
        raw = subprocess.run(["ffmpeg","-nostdin","-v","error","-ss",f"{t:.2f}","-i",p,"-frames:v","1","-vf",vf,"-f","image2pipe","-vcodec","png","-"],capture_output=True).stdout
        import io
        ims.append(Image.open(io.BytesIO(raw)).convert("RGB"))
    w = sum(im.width + 2 for im in ims) + 70
    r = Image.new("RGB", (w, hh), "black"); dr = ImageDraw.Draw(r); dr.text((3, 5), f"{i}\n{d:.0f}s", fill="yellow")
    x = 70
    for k, im in enumerate(ims):
        r.paste(im, (x, 0)); ImageDraw.Draw(r).text((x + 2, hh - 12), f"{d*(k+0.5)/n:.1f}", fill="yellow"); x += im.width + 2
    return r
ids = [int(a) for a in sys.argv[2:]]
with ThreadPoolExecutor(4) as ex:
    rows = list(ex.map(row, ids))
W = max(r.width for r in rows)
c = Image.new("RGB", (W, sum(r.height + 3 for r in rows)), "white"); y = 0
for r in rows: c.paste(r, (0, y)); y += r.height + 3
c.save(sys.argv[1], quality=80); print(c.size)
