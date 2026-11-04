#!/bin/bash
# Final encode: base (blurred under the end card) + overlays + voice ducking the music bed. Two versions.
set -e
cd /home/claude/reels/tong2
T=$(python3 -c "import json;print(json.load(open('timing.json'))['total'])")
TE=$(python3 -c "import json;print(json.load(open('timing.json'))['beats'][6][0])")
VOICE="highpass=f=70,lowpass=f=12000,acompressor=threshold=-20dB:ratio=3:attack=8:release=120:makeup=2,aformat=channel_layouts=stereo"
enc(){ # $1 bed wav, $2 output
ffmpeg -nostdin -v error -y -i base.mp4 -framerate 30 -i ov/%04d.png -i "$1" -i vo_track.wav -filter_complex \
 "[0:v]split[a][b];[b]gblur=sigma=26[bl];[a][bl]blend=all_expr='A*(1-clip((T-$TE)/0.6,0,1))+B*clip((T-$TE)/0.6,0,1)'[bg];[bg][1:v]overlay=0:0:format=auto,format=yuv420p[v];\
[3:a]${VOICE},asplit=2[vo][sc];[2:a]volume=0.6[bed];[bed][sc]sidechaincompress=threshold=0.02:ratio=8:attack=15:release=400:makeup=1[duck];\
[duck][vo]amix=inputs=2:weights='1 1.3':normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000[a]" \
 -map "[v]" -map "[a]" -t $T -c:v libx264 -preset slow -crf 18 -pix_fmt yuv420p -color_primaries bt709 -color_trc bt709 -colorspace bt709 \
 -c:a aac -b:a 192k -movflags +faststart "$2"
}
enc bed.wav out/imperial_eski_jalyuzi_yangilash.mp4
enc bed_nomusic.wav out/imperial_eski_jalyuzi_yangilash_musiqasiz.mp4
ls -la out
