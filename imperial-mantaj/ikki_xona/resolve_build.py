# «Ikki xona» — DaVinci Resolve timeline (Claude tayyorlagan).
# Resolve'da: Workspace -> Console -> Py3, keyin:
#   exec(open(r"C:\Users\shams\Videos\Imperial\07_Resolve\ikki_xona\resolve_build.py", encoding="utf-8").read())
# Yangi loyiha ochadi (Imperial_Ikki_xona, 1080x1920, 30 fps), fayllarni import qiladi va timeline yig'adi:
#   V1 — sahnalar (har birida 0,5 s zaxira: Ctrl+T bilan o'tish qo'yish uchun), V2 — matnlar (shaffof), A1 — musiqa.
import os

BASE = r"C:\Users\shams\Videos\Imperial\07_Resolve\ikki_xona"
MEDIA = os.path.join(BASE, "media")
FPS = 30
# (file, head frames, body frames)
V1 = [("V1_s1.mp4", 0, 108), ("V1_k2.mp4", 15, 129), ("V1_k3.mp4", 15, 90), ("V1_p4.mp4", 15, 132),
      ("V1_p5.mp4", 15, 96), ("V1_p6.mp4", 15, 72), ("V1_s7.mp4", 15, 168)]
# (file, record frame, frames)
V2 = [("V2_O1.mov", 0, 117), ("V2_O2.mov", 135, 87), ("V2_O3.mov", 348, 90), ("V2_O4.mov", 633, 162)]
A1 = ("A1_musiqa.wav", 0, 795)
END_INCLUSIVE = globals().get("END_INCLUSIVE", True)

try:
    resolve
except NameError:
    resolve = bmd.scriptapp("Resolve")  # noqa: F821

pm = resolve.GetProjectManager()
NAME = "Imperial_Ikki_xona"
proj = pm.LoadProject(NAME) or pm.CreateProject(NAME)
print("project:", proj.GetName())
for k, v in {"timelineResolutionWidth": "1080", "timelineResolutionHeight": "1920", "timelineFrameRate": "30",
             "timelinePlaybackFrameRate": "30"}.items():
    print(" set", k, v, proj.SetSetting(k, v))

mp = proj.GetMediaPool()
root = mp.GetRootFolder()
mp.SetCurrentFolder(root)
have = {c.GetName(): c for c in root.GetClipList()}
need = [f for f, *_ in V1] + [f for f, *_ in V2] + [A1[0]]
new = [os.path.join(MEDIA, f) for f in need if f not in have]
if new:
    for it in mp.ImportMedia(new) or []:
        have[it.GetName()] = it
missing = [f for f in need if f not in have]
print("media:", len(have), "missing:", missing)

TL = "Ikki xona"
for i in range(1, proj.GetTimelineCount() + 1):
    t = proj.GetTimelineByIndex(i)
    if t and t.GetName() == TL:
        mp.DeleteTimelines([t])
        break
tl = mp.CreateEmptyTimeline(TL)
proj.SetCurrentTimeline(tl)
while tl.GetTrackCount("video") < 2:
    tl.AddTrack("video")
start = tl.GetStartFrame()
e = 1 if END_INCLUSIVE else 0

v1, rec = [], start
for f, h, n in V1:
    v1.append({"mediaPoolItem": have[f], "startFrame": h, "endFrame": h + n - e, "trackIndex": 1,
               "recordFrame": rec, "mediaType": 1})
    rec += n
r1 = mp.AppendToTimeline(v1)
r2 = mp.AppendToTimeline([{"mediaPoolItem": have[f], "startFrame": 0, "endFrame": n - e, "trackIndex": 2,
                           "recordFrame": start + r, "mediaType": 1} for f, r, n in V2])
f, r, n = A1
r3 = mp.AppendToTimeline([{"mediaPoolItem": have[f], "startFrame": 0, "endFrame": n - e, "trackIndex": 1,
                           "recordFrame": start + r, "mediaType": 2}])
print("appended:", len(r1 or []), len(r2 or []), len(r3 or []))
for kind, idx in (("video", 1), ("video", 2), ("audio", 1)):
    items = tl.GetItemListInTrack(kind, idx) or []
    print(kind, idx, [(it.GetName(), it.GetStart() - start, it.GetDuration()) for it in items])
print("timeline end:", tl.GetEndFrame() - start, "(kerak: 795)")

proj.SetCurrentRenderFormatAndCodec("mp4", "H264")
proj.SetRenderSettings({"SelectAllFrames": True, "TargetDir": BASE, "CustomName": "ikki_xona_resolve",
                        "FormatWidth": 1080, "FormatHeight": 1920, "FrameRate": 30})
print("render job:", proj.AddRenderJob(), "(render boshlanmadi)")
pm.SaveProject()
print("TAYYOR")
