#!/bin/bash
# cut + HLG->SDR + grade + vidstab. usage: segs.sh NAME CLIP SS DUR [extra grade]
TM="zscale=t=linear:npl=203,format=gbrpf32le,zscale=p=bt709,tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv,format=yuv420p"
E="-c:v libx264 -preset veryfast -crf 14 -pix_fmt yuv420p -an"
n=$1; c=$2; ss=$3; d=$4; g=${5:-"eq=contrast=1.05:saturation=1.05"}
ffmpeg -nostdin -v error -y -ss $ss -t $d -i src/$c.mov -an -vf "scale=1080:1920:flags=lanczos,$TM,$g,unsharp=5:5:0.3,fps=30,setsar=1" $E seg/$n.mp4
ffmpeg -nostdin -v error -y -i seg/$n.mp4 -vf "vidstabdetect=shakiness=7:accuracy=12:result=seg/$n.trf" -f null -
ffmpeg -nostdin -v error -y -i seg/$n.mp4 -vf "vidstabtransform=input=seg/$n.trf:smoothing=40:zoom=6:optzoom=0,unsharp=5:5:0.2" $E st/$n.mp4
echo done $n
