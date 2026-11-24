import json, subprocess, sys, io
from PIL import Image, ImageDraw
from concurrent.futures import ThreadPoolExecutor
P = json.load(open("macro_paths.json")); P["242"] = "/mnt/user-data/uploads/DJI_20240915_131743_242_video.mov"
TM = "zscale=t=linear:npl=203,format=gbrpf32le,zscale=p=bt709,tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv,format=yuv420p"
def one(job):
    k, s, e, step = job
    hdr = k != "242"
    raw = subprocess.run(["ffmpeg","-nostdin","-v","error","-ss",str(s),"-t",str(e-s),"-i",P[k],"-vf",f"fps={1/step},scale=144:256," + (TM + "," if hdr else "") + "format=rgb24","-f","rawvideo","-"],capture_output=True).stdout
    n = len(raw)//(144*256*3); cols = 14
    c = Image.new("RGB",(cols*146,((n+cols-1)//cols)*258),"black"); dr = ImageDraw.Draw(c)
    for i in range(n):
        im = Image.frombytes("RGB",(144,256),raw[i*144*256*3:(i+1)*144*256*3]); x,y=(i%cols)*146,(i//cols)*258
        c.paste(im,(x,y)); dr.text((x+3,y+3),f"{k} {s+i*step:.1f}",fill="yellow")
    c.save(f"sh/m_{k}.jpg",quality=78); return k, n
jobs = [tuple([a[0], float(a[1]), float(a[2]), float(a[3])]) for a in (x.split(":") for x in sys.argv[1:])]
with ThreadPoolExecutor(3) as ex:
    print(list(ex.map(one, jobs)))
