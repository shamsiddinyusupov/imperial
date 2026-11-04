#!/usr/bin/env bash
# Reel #2 segments: VHS "before" (V1-V3), tape glitch (G), clean 4K "after" (K1-K4), end background.
set -euo pipefail
A=/mnt/user-data/attachments/29c18e40-edfd-55e7-a3e1-da5539b3418b
O=/home/claude/reels/v2/seg
mkdir -p "$O"

# 4K HLG -> 1080x1920 SDR (downscale first: the float tone-map is the slow part)
TM="scale=1080:1920:flags=lanczos,zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv,format=yuv420p"
# softened VHS (v2): less blur, noise, chroma bleed and jitter than the first cut
VHS="scale=540:960:flags=bilinear,scale=1080:1920:flags=bicubic,eq=saturation=0.72:contrast=0.94:brightness=0.02:gamma=1.03,colorbalance=rs=0.04:gs=0.02:bs=-0.04:rh=0.02:bh=-0.02,rgbashift=rh=-3:bh=3,noise=alls=11:allf=t+u,vignette=PI/5.5,crop=1068:1900:x='6+1.5*sin(n*2.1)+1*sin(n*5.3)':y='10+1*sin(n*1.7)',scale=1080:1920"
CLEAN="colortemperature=temperature=7600:mix=1:pl=0.5,eq=contrast=1.08:saturation=0.95,unsharp=5:5:0.45:5:5:0"
ENC="-c:v libx264 -preset veryfast -crf 10 -pix_fmt yuv420p -color_primaries bt709 -color_trc bt709 -colorspace bt709 -r 30"
AUD="-c:a aac -b:a 256k -ar 48000 -ac 2"

# seg NAME FILE START END LOOK [EXTRA_VF] [SPEED]
seg () {
  local name=$1 file=$2 ss=$3 to=$4 look=$5 extra=${6:-} sp=${7:-1} hold=${8:-0}
  local len; len=$(python3 -c "print($to-$ss)")
  local dur; dur=$(python3 -c "print(($to-$ss)/$sp+$hold)")
  local look_vf; [ "$look" = vhs ] && look_vf="$VHS" || look_vf="$CLEAN"
  local vf="$TM,$look_vf,fps=30,setpts=(PTS-STARTPTS)/$sp"
  [ -n "$extra" ] && vf="$vf,$extra"
  local af="atrim=0:$len,asetpts=PTS-STARTPTS,highpass=f=90,volume=8dB"
  [ "$sp" != "1" ] && af="$af,atempo=$sp"
  af="$af,apad"
  if [ "$look" = vhs ]; then
    # tape hiss + band-limited "old speaker" sound
    ffmpeg -v error -y -ss "$ss" -t "$len" -i "$A/$file" -f lavfi -t "$dur" -i "anoisesrc=c=pink:a=0.018:r=48000" \
      -filter_complex "[0:v]$vf[v];[0:a]$af,lowpass=f=5000,highpass=f=250[a0];[1:a]aformat=channel_layouts=stereo,highpass=f=400[n];[a0][n]amix=inputs=2:normalize=0,afade=t=in:d=0.03,afade=t=out:st=$(python3 -c "print(max(0,$dur-0.04))"):d=0.04[a]" \
      -map "[v]" -map "[a]" -t "$dur" $ENC $AUD "$O/$name.mp4"
  else
    ffmpeg -v error -y -ss "$ss" -t "$len" -i "$A/$file" -vf "$vf" \
      -af "$af,afade=t=in:d=0.04,afade=t=out:st=$(python3 -c "print(max(0,$dur-0.05))"):d=0.05" \
      -t "$dur" $ENC $AUD "$O/$name.mp4"
  fi
  echo "$name $(ffprobe -v error -show_entries format=duration -of csv=p=0 "$O/$name.mp4")"
}

seg V1 6e16c086-IMG_4824.mov 0.0 2.2 vhs
seg V2 869938e8-IMG_4825.mov 0.25 2.75 vhs
seg V3 6e16c086-IMG_4824.mov 4.7 6.7 vhs
seg K1 99a479b1-IMG_4828.mov 0.0 2.6 clean
seg K2 de40929a-IMG_4829.mov 0.0 3.0 clean
seg K3 0cb70cae-IMG_4831.mov 0.0 2.2 clean
# window opening: 0.6x slow motion with frame blending, then hold the last frame
seg K4 a63b80fd-IMG_4830.mov 3.72 4.72 clean "minterpolate=fps=30:mi_mode=blend,tpad=stop_mode=clone:stop_duration=0.6" 0.6 0.6

# glitch NAME SOURCE DUR STRENGTH(0..1): tape tear built from SOURCE's last frame, with a static burst
glitch () {
  local name=$1 src=$2 d=$3 k=$4
  ffmpeg -v error -y -sseof -0.05 -i "$O/$src.mp4" -frames:v 1 -update 1 "$O/${src}_last.png"
  local nz; nz=$(python3 -c "print(int(30+50*$k))")
  local sh; sh=$(python3 -c "print(int(8+16*$k))")
  ffmpeg -v error -y -loop 1 -framerate 30 -t "$d" -i "$O/${src}_last.png" \
    -f lavfi -t "$d" -i "anoisesrc=c=white:a=$(python3 -c "print(0.06+0.12*$k)"):r=48000" \
    -filter_complex "[0:v]noise=alls=$nz:allf=t+u,rgbashift=rh=-$sh:bh=$sh:gv=3,crop=1056:1920:x='12+10*sin(n*3.7)':y=0,scale=1080:1920,eq=brightness='0.03*sin(n*2)':contrast=1.12,format=yuv420p[v];[1:a]aformat=channel_layouts=stereo,highpass=f=900,lowpass=f=7000,afade=t=in:d=0.02,afade=t=out:st=$(python3 -c "print($d-0.12)"):d=0.12[a]" \
    -map "[v]" -map "[a]" -t "$d" $ENC $AUD "$O/$name.mp4"
  echo "$name $(ffprobe -v error -show_entries format=duration -of csv=p=0 "$O/$name.mp4")"
}
glitch G V3 0.45 0.6     # VHS -> 4K (softened)
glitch G2 K4 0.30 0.35   # 4K -> VCR menu ("rewind?")

# end: VCR blue menu screen, 5.0 s, with soft scanline texture; UI beeps rendered separately in v2_beeps.py
python3 /home/claude/reels/scripts/v2_beeps.py "$O/end_beeps.wav"
ffmpeg -v error -y -f lavfi -t 5.0 -i "color=c=0x1A2FB0:s=1080x1920:r=30" -i "$O/end_beeps.wav" \
  -vf "noise=alls=7:allf=t+u,vignette=PI/4.5,format=yuv420p" -af "aformat=channel_layouts=stereo,apad" -t 5.0 \
  $ENC $AUD "$O/END.mp4"
echo "END $(ffprobe -v error -show_entries format=duration -of csv=p=0 "$O/END.mp4")"
