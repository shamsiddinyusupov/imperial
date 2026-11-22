import json, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
items = {i['id']: i for i in json.load(open('/home/claude/baza_work/items.json'))}
TM = "zscale=t=linear:npl=203,format=gbrpf32le,zscale=p=bt709,tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv,format=yuv420p"
SEG = {"noon": (595, 1.0, 3.8), "m704": (704, 0.2, 2.6), "w619": (619, 5.0, 3.6), "s4": (705, 2.0, 4.0),
       "s5": (650, 0.0, 6.0), "s6": (705, 8.5, 8.0), "s8": (751, 4.5, 5.0)}
def go(kv):
    k, (i, ss, d) = kv
    it = items[i]; hdr = it.get('trc') == 'arib-std-b67'
    vf = "scale=1080:1920:force_original_aspect_ratio=increase:flags=lanczos,crop=1080:1920" + (','+TM if hdr else '') + ",eq=contrast=1.04:saturation=1.05,fps=30"
    raw = f"seg/{k}_raw.mp4"
    subprocess.run(['ffmpeg','-nostdin','-v','error','-y','-ss',str(ss),'-t',str(d),'-i',it['path'],'-an','-vf',vf,'-c:v','libx264','-preset','fast','-crf','14','-pix_fmt','yuv420p',raw], check=True)
    subprocess.run(['ffmpeg','-nostdin','-v','error','-y','-i',raw,'-vf',f'vidstabdetect=shakiness=6:accuracy=15:result=seg/{k}.trf','-f','null','-'], check=True)
    subprocess.run(['ffmpeg','-nostdin','-v','error','-y','-i',raw,'-vf',f'vidstabtransform=input=seg/{k}.trf:smoothing=40:zoom=5:optzoom=0:interpol=bicubic,unsharp=5:5:0.3','-c:v','libx264','-preset','fast','-crf','14','-pix_fmt','yuv420p',f'seg/{k}.mp4'], check=True)
    return k
with ThreadPoolExecutor(2) as ex: print(list(ex.map(go, SEG.items())))
