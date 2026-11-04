#!/bin/bash
# Final encode: base + overlay PNGs + calm piano bed (no voice).
set -e
D=/home/claude/reels/dikey_style
T=$(python3 -c "import json;print(json.load(open('$D/cuts.json'))['total'])")
FO=$(python3 -c "print(round($T-1.2,2))")
ffmpeg -nostdin -v error -y -i $D/base.mp4 -framerate 30 -i $D/ov/%04d.png -i $D/bed.wav -filter_complex \
 "[0:v][1:v]overlay=0:0:format=auto,format=yuv420p[v];[2:a]atrim=0:$T,asetpts=PTS-STARTPTS,afade=t=in:d=0.6,afade=t=out:st=$FO:d=1.2,loudnorm=I=-15:TP=-1.5:LRA=9[a]" \
 -map "[v]" -map "[a]" -t $T -c:v libx264 -preset slow -crf 17 -pix_fmt yuv420p \
 -color_primaries bt709 -color_trc bt709 -colorspace bt709 -c:a aac -b:a 192k -ar 48000 -movflags +faststart \
 $D/out/imperial_dikey_faqat_qarang.mp4
ffmpeg -nostdin -v error -y -ss 2.8 -i $D/out/imperial_dikey_faqat_qarang.mp4 -frames:v 1 -q:v 2 $D/out/imperial_dikey_faqat_qarang_cover.jpg
ffprobe -v error -show_entries format=duration -of csv=p=0 $D/out/imperial_dikey_faqat_qarang.mp4
