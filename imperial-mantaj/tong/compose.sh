#!/bin/bash
# Final encode: base video (blurred under the end card) + overlay PNGs + sound, two versions.
set -e
cd /home/claude/reels/tong
enc(){ # $1 sound wav, $2 output
ffmpeg -nostdin -v error -y -i base.mp4 -framerate 30 -i ov/%04d.png -i "$1" -filter_complex \
 "[0:v]split[a][b];[b]gblur=sigma=26[bl];[a][bl]blend=all_expr='A*(1-clip((T-12.8)/0.6,0,1))+B*clip((T-12.8)/0.6,0,1)'[bg];[bg][1:v]overlay=0:0:format=auto,format=yuv420p[v];[2:a]loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000[a]" \
 -map "[v]" -map "[a]" -t 16.5 -c:v libx264 -preset slow -crf 17 -pix_fmt yuv420p -color_primaries bt709 -color_trc bt709 -colorspace bt709 \
 -c:a aac -b:a 192k -movflags +faststart "$2"
}
enc sound_tong.wav out/imperial_plisse_birinchi_tong.mp4
enc sound_tong_nomusic.wav out/imperial_plisse_birinchi_tong_musiqasiz.mp4
ls -la out/
