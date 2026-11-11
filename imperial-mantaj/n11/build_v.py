"""Voiced versions (Daniel) of the two 11.11 Classic Reels, re-timed to the voice.
Re-uses build_dk.py / build_pq.py unchanged: their module globals (SC, ST, TOTAL, S_*, D ...) are overridden, and the
working dir D points to n11v/ (symlinks to the shared clips) so the silent versions' files stay untouched.
Voice comes from vo/vo.py (cut from the owner's screen recordings); music bed is re-rendered for the new length and
ducked under the voice.
python3 build_v.py dk|pq [base|prev t,t|ov|music|final|cover|all]
"""
import os
import subprocess
import sys

sys.path.insert(0, "/home/claude/reels/n11")
sys.path.insert(0, "/home/claude/reels/n11/vo")
import vo  # noqa: E402

N11 = "/home/claude/reels/n11"
DV = "/home/claude/reels/n11v"
GAP, LEAD = 0.55, 0.3


def sh(cmd):
    subprocess.run(cmd, shell=True, check=True)


def prep_dir():
    os.makedirs(DV, exist_ok=True)
    for sub in ("st", "st2", "src"):
        if not os.path.exists(f"{DV}/{sub}"):
            os.symlink(f"{N11}/{sub}", f"{DV}/{sub}")
    for sub in ("cs", "bo", "out"):
        os.makedirs(f"{DV}/{sub}", exist_ok=True)


def timeline(lens, first=0.3, tail=1.6):
    """paragraph starts p_i and scene starts S_i (scene i+1 starts so that its paragraph begins LEAD after it)."""
    p, S = [first], [0.0]
    for i in range(len(lens) - 1):
        s_next = p[i] + lens[i] + GAP - LEAD
        S.append(s_next)
        p.append(s_next + LEAD)
    total = p[-1] + lens[-1] + tail
    return p, S, total


def setup_dk():
    import build_dk as B
    lens = vo.lengths("dk")
    p, S, total = timeline(lens, first=0.35)
    xfs = B.XFS
    names = [s[0] for s in B.SC]
    src = {s[0]: s for s in B.SC}
    SC = []
    for i, nm in enumerate(names):
        od = (S[i + 1] - S[i] + xfs[i + 1]) if i + 1 < len(names) else total - S[i]
        _, path, ss, sdur, _sp = src[nm]
        if path == "endbg":
            SC.append((nm, path, 0, od, None))
        else:
            avail = {"close": 4.4, "d1": 3.6, "d2": 3.2, "open": 4.8}[nm] - ss
            SC.append((nm, path, ss, avail, avail / od))
    B.D = DV
    B.SC, B.ST, B.TOTAL = SC, S, total
    B.NF = int(round(total * B.FPS))
    B.S_CL, B.S_D1, B.S_D2, B.S_OP, B.S_END = S
    B.CHIMES = [(0.1, S[1] - 0.2), (S[2] + 0.3, S[3] - 0.3), (S[3] + 0.1, S[4] - 0.2)]
    B.OUTN = "classic_dikey_kombinatsiya_ovozli"
    return B, p, total


NAMES_PQ = {"1-variant": "Krem", "2-variant": "Kapuchino", "3-variant": "Oq-kulrang",
            "Вариант 1": "Крем", "Вариант 2": "Капучино", "Вариант 3": "Бело-серый"}


def setup_pq():
    import build_pq as B
    lens = vo.lengths("pq")
    p, S6, total = timeline(lens, first=0.3)
    # scenes: hk o1 o2 o3 op ins end ; paragraph 3 covers o3 + op
    S = [S6[0], S6[1], S6[2], S6[3], S6[3] + 2.3, S6[4], S6[5]]
    XF = B.XF
    od = [S[i + 1] - S[i] + XF for i in range(6)] + [total - S[6]]
    srcdur = {"o1": (0.0, 4.7), "o2": (0.0, 4.6), "o3": (0.0, 2.9), "op": (2.0, 2.7), "ins": (0.0, 5.0)}
    SC = []
    for (nm, path, ss, d, sp), o in zip(B.SC, od):
        if path in ("trip", "tiles"):
            SC.append((nm, path, 0, o, None))
        else:
            s0, dd = srcdur[nm]
            SC.append((nm, path, s0, dd, dd / o))
    B.D = DV
    B.SC, B.ST, B.TOTAL = SC, S, total
    B.NF = int(round(total * B.FPS))
    B.S_HK, B.S_O1, B.S_O2, B.S_O3, B.S_OP, B.S_INS, B.S_END = S
    B.END_OF = dict(zip([s[0] for s in SC], S[1:] + [total]))
    B.OPTS = [(1, S[1], B.END_OF["o1"]), (2, S[2], B.END_OF["o2"]), (3, S[3], B.END_OF["op"])]
    _text = B.text

    def text(img, xy, s, *a, **k):                       # colour names instead of «1-variant» (the voice says them)
        return _text(img, xy, NAMES_PQ.get(s, s), *a, **k)
    B.text = text
    B.OUTN = "classic_plisse_qaysi_rang_ovozli"
    return B, p, total


def music(name, B, total):
    if name == "dk":
        from airy_bed import airy_bed
        airy_bed(f"{DV}/bed_{name}.wav", total, B.S_END, B.CHIMES)
    else:
        from pop_bed import pop_bed
        pop_bed(f"{DV}/bed_{name}.wav", total, B.S_END, [B.S_O1 + 0.1, B.S_O2 + 0.1, B.S_O3 + 0.1])


def final(name, B, p, total):
    vo.place(name, p, total, f"{DV}/voice_{name}.wav")
    base = f"{DV}/base_{name}.mp4"
    ov = f"{DV}/ov_{name}/%04d.png"
    out = f"{DV}/out/{B.OUTN}.mp4"
    music_db = -15 if name == "dk" else -17
    af = (f"[2:a]highpass=f=70,acompressor=threshold=-20dB:ratio=2.5:attack=8:release=120:makeup=2,"
          f"equalizer=f=3200:t=q:w=1:g=2,aresample=48000,asplit=2[vo][key];"
          f"[3:a]volume={music_db}dB[mu];"
          f"[mu][key]sidechaincompress=threshold=0.03:ratio=6:attack=25:release=350[mud];"
          f"[vo][mud]amix=inputs=2:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=9[a]")
    sh(f"ffmpeg -nostdin -v error -y -i {base} -framerate 30 -i {ov} -i {DV}/voice_{name}.wav -i {DV}/bed_{name}.wav "
       f"-filter_complex \"[0:v][1:v]overlay=0:0:format=auto,format=yuv420p[v];{af}\" -map \"[v]\" -map \"[a]\" "
       f"-t {total:.3f} -c:v libx264 -preset slow -crf 18 -pix_fmt yuv420p -color_primaries bt709 -color_trc bt709 "
       f"-colorspace bt709 -c:a aac -b:a 192k -ar 48000 -movflags +faststart {out}")


if __name__ == "__main__":
    name = sys.argv[1]
    what = sys.argv[2] if len(sys.argv) > 2 else "all"
    prep_dir()
    B, p, total = setup_dk() if name == "dk" else setup_pq()
    print("scene starts", [round(x, 2) for x in B.ST], "voice", [round(x, 2) for x in p], "total", round(total, 2))
    print("speeds", [(s[0], round(s[4], 2)) for s in B.SC if s[4]])
    # base/ov file names inside the original modules are fixed; they land in DV because B.D = DV
    if what in ("base", "all"):
        B.base()
    if what == "prev":
        sys.argv = ["x", "prev", sys.argv[3]]
        import runpy  # noqa: F401
        ims = []
        from PIL import Image
        import numpy as np  # noqa: F401
        tag = "dk" if name == "dk" else "pq"
        for tt in map(float, sys.argv[2].split(",")):
            sh(f"ffmpeg -v error -y -ss {tt} -i {DV}/base_{tag}.mp4 -frames:v 1 {DV}/cs/pb.png")
            b = Image.open(f"{DV}/cs/pb.png").convert("RGBA")
            b.alpha_composite(Image.fromarray(B.frame(int(tt * B.FPS))))
            ims.append(b.convert("RGB").resize((360, 640)))
        c = Image.new("RGB", (365 * len(ims), 640), "white")
        for k, im in enumerate(ims):
            c.paste(im, (k * 365, 0))
        c.save(f"{DV}/cs/prev_{name}.jpg", quality=85)
    if what in ("ov", "all"):
        B.render_ov()
    if what in ("music", "all"):
        music(name, B, total)
    if what in ("final", "all"):
        final(name, B, p, total)
    if what in ("cover", "all"):
        B.cover()
