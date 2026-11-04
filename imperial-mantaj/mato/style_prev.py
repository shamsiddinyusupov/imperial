import math
from PIL import Image, ImageDraw, ImageFilter, ImageFont
FI="/usr/share/fonts/opentype/inter/"; CX="/usr/share/fonts/truetype/crosextra/"
F=lambda n,s: ImageFont.truetype(n if n.startswith("/") else FI+n, s)
MONO="/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
PAPER,GOLD,INK=(245,241,233),(214,176,98),(30,28,25)
W,H=1080,1920
NAME,ROOM,LINE,RU="Yarim shaffof","Mehmonxona uchun","Yorug‘ va shinam, kunduzi ko‘zdan pana","Полупрозрачная — для гостиной"
SCALE=["Shaffof","Yarim shaffof","Dimout","Blackout"]; IDX=1

def shadow(L,blur=14,a=0.5,dy=8):
    sh=Image.new("RGBA",L.size,(0,0,0,0)); sh.putalpha(L.getchannel("A").filter(ImageFilter.GaussianBlur(blur)).point(lambda v:int(v*a)))
    o=Image.new("RGBA",L.size,(0,0,0,0)); o.alpha_composite(sh,(0,dy)); o.alpha_composite(L); return o
def tracked(d,xy,t,f,fill,tr=0.14):
    x,y=xy
    for c in t: d.text((x,y),c,font=f,fill=fill); x+=f.getlength(c)+f.size*tr
    return x

def style_a():  # catalogue card
    L=Image.new("RGBA",(W,H),(0,0,0,0)); d=ImageDraw.Draw(L)
    x0,y0,x1,y1=56,1210,1024,1600
    d.rounded_rectangle((x0,y0,x1,y1),34,fill=(250,248,243,245))
    tracked(d,(x0+44,y0+36),"01 · PLISSE MATOSI",F(MONO,26),(170,135,62))
    d.text((x0+40,y0+74),NAME,font=F("InterDisplay-SemiBold.otf",86),fill=INK)
    d.text((x0+44,y0+180),ROOM,font=F("Inter-SemiBold.otf",40),fill=(150,112,40))
    d.text((x0+44,y0+232),LINE,font=F("Inter-Regular.otf",34),fill=(80,74,66))
    sx,sy=x0+44,y0+300
    for k,lab in enumerate(SCALE):
        on=k==IDX; cx=sx+k*226
        d.ellipse((cx,sy,cx+22,sy+22),fill=(170,135,62) if on else (214,208,196))
        d.text((cx+32,sy-3),lab,font=F("Inter-Medium.otf" if on else "Inter-Regular.otf",24),fill=INK if on else (140,134,124))
    d.text((x0+44,y0+340),RU,font=F("Inter-Regular.otf",26),fill=(130,124,116))
    return shadow(L,20,0.45,10)

def style_b():  # oversized number, editorial
    L=Image.new("RGBA",(W,H),(0,0,0,0)); d=ImageDraw.Draw(L)
    g=Image.new("RGBA",(W,H),(0,0,0,0)); gd=ImageDraw.Draw(g)
    for y in range(900,1920):
        a=min(1,(y-900)/700)**1.3*0.82; gd.line([(0,y),(W,y)],fill=(8,8,10,int(a*255)))
    L.alpha_composite(g)
    d.text((54,930),"01",font=F("InterDisplay-Black.otf",330),fill=(255,255,255,0),stroke_width=4,stroke_fill=GOLD+(255,))
    tracked(d,(84,1300),"YARIM SHAFFOF",F("InterDisplay-ExtraBold.otf",76),PAPER,0.04)
    d.rectangle((84,1400,84+140,1408),fill=GOLD)
    d.text((84,1432),ROOM,font=F("InterDisplay-SemiBold.otf",48),fill=GOLD)
    d.text((86,1494),LINE,font=F("Inter-Regular.otf",34),fill=(228,222,212))
    d.text((86,1544),RU,font=F("Inter-Regular.otf",28),fill=(190,184,174))
    return shadow(L,10,0.4,4)

def style_c():  # fabric tag / swatch label
    T=Image.new("RGBA",(760,470),(0,0,0,0)); d=ImageDraw.Draw(T)
    d.rounded_rectangle((0,0,760,470),26,fill=(246,240,228,250))
    for x in range(28,732,22): d.line([(x,18),(x+11,18)],fill=(190,160,110),width=3); d.line([(x,452),(x+11,452)],fill=(190,160,110),width=3)
    for y in range(28,442,22): d.line([(18,y),(18,y+11)],fill=(190,160,110),width=3); d.line([(742,y),(742,y+11)],fill=(190,160,110),width=3)
    d.ellipse((662,46,712,96),fill=(60,52,44)); d.ellipse((672,56,702,86),fill=(0,0,0,0))
    serif=CX+"Caladea-Bold.ttf"
    tracked(d,(52,52),"MATO № 1",F(MONO,26),(150,112,40))
    d.text((48,92),NAME,font=F(serif,84),fill=INK)
    d.line([(52,200),(560,200)],fill=(190,160,110),width=2)
    d.text((52,220),ROOM,font=F("Inter-SemiBold.otf",40),fill=(150,112,40))
    d.text((52,276),"Yorug‘ va shinam,",font=F("Inter-Regular.otf",34),fill=(80,74,66))
    d.text((52,318),"kunduzi ko‘zdan pana",font=F("Inter-Regular.otf",34),fill=(80,74,66))
    d.text((52,378),RU,font=F("Inter-Regular.otf",26),fill=(130,124,116))
    T=T.rotate(3.5,resample=Image.BICUBIC,expand=True)
    L=Image.new("RGBA",(W,H),(0,0,0,0)); L.alpha_composite(T,(70,1140))
    # string from tag hole up to the blind
    d2=ImageDraw.Draw(L); d2.line([(760,1170),(820,1020)],fill=(240,236,228,230),width=3)
    return shadow(L,18,0.5,10)

base=Image.open("frames/st_5.0.png").convert("RGBA")
out=[]
for i,fn in enumerate((style_a,style_b,style_c)):
    b=base.copy(); b.alpha_composite(fn()); im=b.convert("RGB").resize((540,960))
    lab=ImageDraw.Draw(im); lab.rounded_rectangle((16,16,96,80),20,fill=GOLD); lab.text((40,20),"ABC"[i],font=F("InterDisplay-Bold.otf",48),fill=INK)
    out.append(im)
sheet=Image.new("RGB",(540*3+40,960),(24,24,28))
for i,im in enumerate(out): sheet.paste(im,(i*560,0))
sheet.save("out/uslublar_A-B-C.jpg",quality=90); print("ok")
