set -e
cd /home/claude/reels/faq
# CTA background: blurred + darkened
ffmpeg -nostdin -v error -y -i seg/S6.mp4 -vf "gblur=sigma=14,eq=brightness=-0.16:saturation=0.85" -c:v libx264 -preset fast -crf 15 -pix_fmt yuv420p seg/S6b.mp4
ffmpeg -nostdin -v error -y -i seg/S0.mp4 -i seg/S1.mp4 -i seg/S2.mp4 -i seg/S3.mp4 -i seg/S4.mp4 -i seg/S5.mp4 -i seg/S6b.mp4 -filter_complex "
[0:v]settb=AVTB,setpts=PTS-STARTPTS[v0];[1:v]settb=AVTB,setpts=PTS-STARTPTS[v1];[2:v]settb=AVTB,setpts=PTS-STARTPTS[v2];
[3:v]settb=AVTB,setpts=PTS-STARTPTS[v3];[4:v]settb=AVTB,setpts=PTS-STARTPTS[v4];[5:v]settb=AVTB,setpts=PTS-STARTPTS[v5];[6:v]settb=AVTB,setpts=PTS-STARTPTS[v6];
[v0][v1]xfade=transition=fade:duration=0.3:offset=2.9[x1];
[x1][v2]xfade=transition=smoothleft:duration=0.3:offset=8.0333[x2];
[x2][v3]xfade=transition=smoothleft:duration=0.3:offset=13.3333[x3];
[x3][v4]xfade=transition=smoothleft:duration=0.3:offset=18.6333[x4];
[x4][v5]xfade=transition=smoothleft:duration=0.3:offset=23.9333[x5];
[x5][v6]xfade=transition=fade:duration=0.3:offset=29.2333,format=yuv420p[out]" -map "[out]" -r 30 -c:v libx264 -preset fast -crf 14 -pix_fmt yuv420p base.mp4
ffprobe -v error -count_frames -select_streams v -show_entries stream=nb_read_frames,duration -of csv=p=0 base.mp4
