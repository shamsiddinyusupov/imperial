"""tile library for the Classic mosaic: 1-2 SDR frames per plisse source, centre-cropped 4:5, 320x400"""
import json, os, subprocess
from concurrent.futures import ThreadPoolExecutor
items = json.load(open('/home/claude/baza_work/items.json'))
cat = {int(k): v for k, v in json.load(open('/home/claude/baza_work/cats.json')).items()}
TM = ("zscale=t=linear:npl=203,format=gbrpf32le,zscale=p=bt709,tonemap=hable:desat=0,"
      "zscale=t=bt709:m=bt709:r=tv,format=yuv420p")
src = [i for i in items if (cat.get(i['id']) == 'P' or i['id'] >= 579)
       and not i['name'].lower().startswith(('copy_', 'screen', 'dji'))]
def crop_vf(hdr):
    return ("scale='if(gt(iw,ih),-2,1080)':'if(gt(iw,ih),1080,-2)':flags=bicubic" + (',' + TM if hdr else '') +
            ",crop='min(iw,ih*4/5)':'min(iw,ih*4/5)*5/4',scale=320:400:flags=lanczos")
def go(it):
    out = []
    if it['kind'] == 'video':
        for k, fr in enumerate((0.3, 0.7)):
            p = f"lib/{it['id']}_{k}.jpg"
            if not os.path.exists(p):
                subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-ss', f"{it['dur'] * fr:.2f}", '-i', it['path'],
                                '-frames:v', '1', '-vf', crop_vf(it.get('trc') == 'arib-std-b67'), '-q:v', '3', p])
            out.append(p)
    else:
        p = f"lib/{it['id']}_0.jpg"
        if not os.path.exists(p):
            subprocess.run(['ffmpeg', '-nostdin', '-v', 'error', '-y', '-i', it['path'], '-frames:v', '1', '-vf',
                            crop_vf(False), '-q:v', '3', p])
        out.append(p)
    return it['id'], out
with ThreadPoolExecutor(2) as ex:
    res = list(ex.map(go, src))
json.dump({str(i): o for i, o in res}, open('lib.json', 'w'))
print(len(src), sum(len(o) for _, o in res))
