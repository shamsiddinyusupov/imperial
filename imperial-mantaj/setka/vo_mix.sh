#!/bin/bash
# Mix the placed narration (vo_track.wav) with the Reel's sound and mux onto the finished picture.
set -e
cd /home/claude/reels/setka
VOICE="highpass=f=70,lowpass=f=12000,acompressor=threshold=-20dB:ratio=3:attack=8:release=120:makeup=2,aformat=channel_layouts=stereo"
mix() {   # $1 = bed wav, $2 = output mp4
  ffmpeg -nostdin -v error -y -i out/imperial_setka_oxirgi_marta.mp4 -i "$1" -i vo_track.wav -filter_complex \
    "[2:a]${VOICE},asplit=2[v][sc];[1:a]volume=0.8[bed];[bed][sc]sidechaincompress=threshold=0.02:ratio=8:attack=15:release=400:makeup=1[duck];[duck][v]amix=inputs=2:weights='1 1.25':normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000[a]" \
    -map 0:v -map "[a]" -c:v copy -c:a aac -b:a 192k -t 30 -movflags +faststart "$2"
}
mix sound_prem.wav out/imperial_setka_oxirgi_marta_ovozli.mp4
mix sound_prem_nomusic.wav out/imperial_setka_oxirgi_marta_ovozli_musiqasiz.mp4
ls -la out/imperial_setka_oxirgi_marta_ovozli*.mp4
