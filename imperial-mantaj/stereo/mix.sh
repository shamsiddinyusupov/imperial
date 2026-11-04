#!/bin/bash
# Final encode «Jalyuzi deganda…»: base (soft blur under the end card) + overlays + voice ducking the new bed + office sfx.
set -e
cd /home/claude/reels/stereo
T=$(python3 -c "import json;print(json.load(open('timing.json'))['total'])")
TE=$(python3 -c "import json;print(json.load(open('cuts.json'))['end'])")
VOICE="highpass=f=70,lowpass=f=12000,acompressor=threshold=-20dB:ratio=3:attack=8:release=120:makeup=2,aformat=channel_layouts=stereo"
ffmpeg -nostdin -v error -y -i base.mp4 -framerate 30 -i ov/%04d.png -i bed.wav -i vo_track.wav -i sfx.wav -filter_complex \
 "[0:v]split[a][b];[b]gblur=sigma=22[bl];[a][bl]blend=all_expr='A*(1-clip((T-$TE)/0.6,0,1))+B*clip((T-$TE)/0.6,0,1)'[bg];[bg][1:v]overlay=0:0:format=auto,format=yuv420p[v];\
[3:a]${VOICE},asplit=2[vo][sc];[2:a]volume=0.62[bed];[bed][sc]sidechaincompress=threshold=0.02:ratio=7:attack=15:release=450:makeup=1[duck];\
[4:a]volume=0.55,aformat=channel_layouts=stereo[fx];\
[duck][vo][fx]amix=inputs=3:weights='1 1.3 1':normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000[a]" \
 -map "[v]" -map "[a]" -t $T -c:v libx264 -preset slow -crf 18 -pix_fmt yuv420p -color_primaries bt709 -color_trc bt709 -colorspace bt709 \
 -c:a aac -b:a 192k -movflags +faststart out/imperial_jalyuzi_deganda.mp4
ffmpeg -nostdin -v error -y -ss 3.3 -i out/imperial_jalyuzi_deganda.mp4 -frames:v 1 -q:v 2 out/imperial_jalyuzi_deganda_cover.jpg
ffprobe -v error -show_entries format=duration -of csv=p=0 out/imperial_jalyuzi_deganda.mp4
