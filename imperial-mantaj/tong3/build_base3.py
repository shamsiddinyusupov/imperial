"""Sales Reel picture: «Derazangizga — ikki yo‘l» (new kombo / renew the old one). Hard cuts on the spoken words.

Shots follow the narration from timing.json (lines + speech chunks):
  hook      split screen: kombo (top, colour) / old plisse (bottom, black-and-white)
  line 2    "Birinchisi — yangi kombo" → roll-up reveal | "Toshkentda … bepul" → wide room | "… 3 kunda tayyor" → photo
  line 3    "Ikkinchisi — eskisini yangilash" → plisse b/w → colour | "… matosini almashtiramiz" → kombo close-up | "Yoki — yuvib beramiz" → white plisse
  line 4    "Bir yil kafolat" → diagonal kombo stripes
  line 5    end card background (photo; blurred in the final mix)
"""
import json
import subprocess

D = "/home/claude/reels/tong3"
E = ["-c:v", "libx264", "-preset", "fast", "-crf", "14", "-pix_fmt", "yuv420p", "-r", "30"]
tim = json.load(open(f"{D}/timing.json"))
L = tim["lines"]
CH = tim.get("chunks")
TOTAL = tim["total"]
LEADCUT = 0.08          # cut a hair before the word starts


def run(args):
    subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y"] + args, check=True)


def dur(p):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p],
                                capture_output=True, text=True).stdout)


SENT = {(1, 0.27): 2, (1, 0.66): 4, (2, 0.34): 2, (2, 0.80): -1}   # sentence-start chunk per (line, frac), mapped from this take's pause pattern


def at(i, frac):
    """Start of the sentence inside line i: a known chunk index if the take matches, else the chunk nearest to frac."""
    t = L[i]["start"] + frac * L[i]["len"]
    if not CH:
        return t
    k = SENT.get((i, frac))
    if k is not None and -len(CH[i]) <= k < len(CH[i]):
        return CH[i][k][0]
    return min((c[0] for c in CH[i]), key=lambda s: abs(s - t))


def piece(name, src, length, vf="null", start=0.0):
    have = dur(f"{D}/seg/{src}.mp4") - start
    slow = 1.0
    if have < length:
        slow = max(0.8, have / length)
        vf = f"setpts=PTS/{slow:.4f},fps=30,{vf}"
    pad = max(0.0, length - have / slow + 0.05)
    f = f"{vf},tpad=stop_mode=clone:stop_duration={pad:.3f}" if pad > 0 else vf
    run(["-ss", f"{start:.3f}", "-i", f"{D}/seg/{src}.mp4", "-t", f"{length:.3f}", "-vf", f + ",setpts=PTS-STARTPTS"] + E + [f"{D}/seg/P_{name}.mp4"])
    return f"P_{name}.mp4"


BW = "hue=s=0,eq=brightness=-0.05:contrast=1.08,noise=alls=7:allf=t"

# cut points on the output timeline
t1 = L[1]["start"] - 0.1
l2b, l2c = at(1, 0.27) - LEADCUT, at(1, 0.66) - LEADCUT
t2 = L[2]["start"] - 0.1
l3b, l3c = at(2, 0.34) - LEADCUT, at(2, 0.80) - LEADCUT
t3 = L[3]["start"] - 0.1
t4 = L[4]["start"] - 0.1
print("cuts", [round(v, 2) for v in (t1, l2b, l2c, t2, l3b, l3c, t3, t4, TOTAL)])

out = []
# hook: split screen 1080x960 halves
run(["-i", f"{D}/seg/F2.mp4", "-i", f"{D}/seg/P1.mp4", "-filter_complex",
     f"[0:v]crop=1080:960:0:420,setpts=PTS-STARTPTS[a];[1:v]crop=1080:960:0:520,{BW},setpts=PTS-STARTPTS[b];"
     f"[a][b]vstack,tpad=stop_mode=clone:stop_duration=2,trim=duration={t1:.3f},format=yuv420p[v]",
     "-map", "[v]"] + E + [f"{D}/seg/P_hook.mp4"])
out.append("P_hook.mp4")
out.append(piece("k2", "K2", l2b - t1))
out.append(piece("w1", "W1", l2c - l2b))
out.append(piece("f1", "F1", t2 - l2c))
# plisse: black-and-white, colour returns over the end of "…eskisini yangilash"
plen = l3b - t2
c0, c1 = plen * 0.45, plen * 0.85
k = f"clip((t-{c0:.3f})/{c1 - c0:.3f},0,1)"
out.append(piece("p1", "P1", plen, f"hue=s='{k}',eq=eval=frame:brightness='-0.05*(1-{k})':contrast='1+0.08*(1-{k})',noise=alls=7:allf=t", start=0.4))
out.append(piece("c1", "C1", l3c - l3b))
out.append(piece("w2", "W2", t3 - l3c))
out.append(piece("g1", "G1", t4 - t3))
out.append(piece("f2", "F2", TOTAL - t4 + 0.1))
with open(f"{D}/seg/list.txt", "w") as f:
    f.write("".join(f"file '{p}'\n" for p in out))
run(["-f", "concat", "-safe", "0", "-i", f"{D}/seg/list.txt", "-t", f"{TOTAL:.3f}"] + E + [f"{D}/base.mp4"])
print("base.mp4", round(dur(f"{D}/base.mp4"), 2), "target", TOTAL)
json.dump({"t1": t1, "l2b": l2b, "l2c": l2c, "t2": t2, "l3b": l3b, "l3c": l3c, "t3": t3, "t4": t4}, open(f"{D}/cuts.json", "w"), indent=1)
