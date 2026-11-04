#!/bin/bash
# Cut + tone-map the chosen ranges to SDR 1080x1920 30fps (video only; audio is replaced by SFX)
set -e
A=/mnt/user-data/attachments/29c18e40-edfd-55e7-a3e1-da5539b3418b
U=/mnt/user-data/uploads
TM="zscale=t=linear:npl=203,format=gbrpf32le,zscale=p=bt709,tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv,format=yuv420p"
GR="eq=contrast=1.04:saturation=1.06,unsharp=5:5:0.35"
cut () {  # out src start dur
  ffmpeg -nostdin -v error -y -ss "$3" -t "$4" -i "$2" -an \
    -vf "scale=1080:1920:flags=lanczos,$TM,$GR,fps=30,setsar=1" \
    -c:v libx264 -preset fast -crf 15 -pix_fmt yuv420p "seg/$1.mp4"
}
cut S0 $U/IMG_4421.mov 0.6 3.2                               # c08 walk-in, hook
cut S1b $A/cce1314d-IMG_4569.mov 3.0 3.15                    # c01 past the handle
cut S2 $A/677e5385-IMG_4787.mov 0.2 5.6                      # c03 pleats -> window
cut S3 $A/1ddf9206-IMG_4418.mov 0.0 5.6                      # c06 dark plisse lowered
cut S4 $A/0568d1d8-IMG_5001.mov 1.2 5.6                      # c02 raised -> sky
cut S5 $U/IMG_4424.mov 0.6 5.6                               # c09 wooden window pan
cut S6 $U/IMG_4421.mov 6.8 6.0                               # c08 end for CTA background
# Q1 = earlier window-opening clip (already SDR) + c01
ffmpeg -nostdin -v error -y -i /home/claude/reels/v2/seg/K4.mp4 -i seg/S1b.mp4 -filter_complex \
 "[0:v]fps=30,setpts=PTS-STARTPTS,setsar=1,format=yuv420p[a];[1:v]fps=30,setpts=PTS-STARTPTS,setsar=1,format=yuv420p[b];[a][b]concat=n=2:v=1:a=0[v]" \
 -map "[v]" -c:v libx264 -preset fast -crf 15 -pix_fmt yuv420p seg/S1.mp4
for s in S0 S1 S2 S3 S4 S5 S6; do echo "$s $(ffprobe -v error -count_frames -select_streams v:0 -show_entries stream=nb_read_frames -of csv=p=0 seg/$s.mp4)"; done
