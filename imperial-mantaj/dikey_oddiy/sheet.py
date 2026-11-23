import json, subprocess, sys
from PIL import Image, ImageDraw
from concurrent.futures import ThreadPoolExecutor
P = json.load(open("paths.json"))
TM = "zscale=t=linear:npl=203,format=gbrpf32le,zscale=p=bt709,tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv,format=yuv420p"
def one(k, step=0.5, cols=12, hh=240):
    p = P[k]
    d = float(subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",p],capture_output=True,text=True).stdout)
    raw = subprocess.run(["ffmpeg","-nostdin","-v","error","-i",p,"-vf",f"fps={1/step},scale=-2:{hh},{TM},format=rgb24","-f","rawvideo","-"],capture_output=True).stdout
    w = len(raw) // (hh * 3)
    # width per frame unknown -> compute from probe of first frame size
    fw = int(round(hh * 1080 / 1920 / 2) * 2)
    n = len(raw) // (fw * hh * 3)
    ims = [Image.frombytes("RGB", (fw, hh), raw[i*fw*hh*3:(i+1)*fw*hh*3]) for i in range(n)]
    rows = (n + cols - 1) // cols
    c = Image.new("RGB", (cols * (fw + 2), rows * (hh + 2)), "black"); dr = ImageDraw.Draw(c)
    for i, im in enumerate(ims):
        x, y = (i % cols) * (fw + 2), (i // cols) * (hh + 2)
        c.paste(im, (x, y)); dr.text((x + 3, y + 3), f"{i*step:.1f}", fill="yellow")
    c.save(f"sh/{k}.jpg", quality=80)
    return k, n, round(d, 1)
with ThreadPoolExecutor(3) as ex:
    for r in ex.map(one, sys.argv[1:]): print(r)
