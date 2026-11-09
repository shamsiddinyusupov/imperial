#!/bin/bash
# Cut 1080x1920 SDR segments (iPhone HLG, rotated). name clip start dur [reverse]
set -e
cd /home/claude/reels/qora_plisse
TM="zscale=t=linear:npl=203,format=gbrpf32le,zscale=p=bt709,tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv,format=yuv420p"
GR="eq=contrast=1.05:saturation=1.02:gamma=1.0,colorbalance=rs=0.01:bs=-0.01:rh=0.02:bh=-0.02,unsharp=5:5:0.3"
cut(){ R=""; [ "$5" = rev ] && R=",reverse"; ffmpeg -nostdin -v error -y -ss $3 -t $4 -i src/IMG_$2.mov -an -vf "scale=1080:1920:flags=lanczos,$TM,$GR,fps=30,setsar=1$R" -c:v libx264 -preset fast -crf 15 -pix_fmt yuv420p seg/$1.mp4; }
cut c_open   6005 0.0 7.0 &      # curtain drawn: plisse revealed
cut c_rev    6004 6.0 6.0 &      # curtain slides to reveal window
cut niche1   6013 0.0 4.3 &
cut niche2   6012 1.6 3.9 &
wait
cut desk     6029 0.0 1.8 &
cut desk2    6030 0.0 2.1 &
cut bath1    6020 0.0 5.8 &
cut bath2    6025 0.0 3.3 &
wait
cut sash     6026 0.0 2.9 &
cut nightopen 6027 0.0 7.4 &
cut nightpull 6028 0.0 9.7 &
cut macro    6006 18.0 8.0 &
wait
cut detail   6015 0.0 3.3 &
cut bathup   6023 1.2 5.5 &
wait
for s in seg/*.mp4; do echo -n "$(basename $s) "; ffprobe -v error -show_entries format=duration -of csv=p=0 $s; done
