from PIL import Image, ImageDraw, ImageFilter, ImageFont
import numpy as np
FI="/usr/share/fonts/opentype/inter/"; CX="/usr/share/fonts/truetype/crosextra/"
F=lambda n,s: ImageFont.truetype(n if n.startswith("/") else FI+n, s)
SER=lambda s: F(CX+"Caladea-Regular.ttf",s); SERI=lambda s: F(CX+"Caladea-Italic.ttf",s)
CREAM,GOLD=(244,238,226),(205,170,105)
W,H=1080,1920
def tracked(d,xy,t,f,fill,tr):
    x,y=xy
    for c in t: d.text((x,y),c,font=f,fill=fill); x+=f.getlength(c)+f.size*tr
    return x
def tw(t,f,tr): return sum(f.getlength(c)+f.size*tr for c in t)
def ctext(d,y,t,f,fill,tr=0.0): d.text if tr==0 else None; x=(W-tw(t,f,tr))/2; tracked(d,(x,y),t,f,fill,tr)
def shadow(L,b=12,a=0.5):
    sh=Image.new("RGBA",L.size,(0,0,0,0)); sh.putalpha(L.getchannel("A").filter(ImageFilter.GaussianBlur(b)).point(lambda v:int(v*a)))
    o=Image.new("RGBA",L.size,(0,0,0,0)); o.alpha_composite(sh,(0,3)); o.alpha_composite(L); return o
def grad(y0,y1,amax):
    ys=np.arange(H,dtype=np.float32); a=np.clip((ys-y0)/(y1-y0),0,1)**1.4*amax
    img=np.zeros((H,W,4),np.uint8); img[...,3]=(np.repeat(a[:,None],W,1)*255).astype(np.uint8); return Image.fromarray(img,"RGBA")
# hook
b=Image.open("frames/p_hook.png").convert("RGBA"); L=Image.new("RGBA",(W,H),(0,0,0,0)); d=ImageDraw.Draw(L)
for k,t in enumerate(("Bu ovozni","oxirgi marta","eshityapsiz.")): ctext(d,760+k*110,t,SER(96),CREAM)
bars=[10,26,44,30,58,36,20,48,28,14]; x0=W/2-len(bars)*14/2
for k,h in enumerate(bars): d.rounded_rectangle((x0+k*14,1150-h/2,x0+k*14+6,1150+h/2),3,fill=GOLD)
ctext(d,1210,"OVOZNI YOQING",F("Inter-Medium.otf",26),(200,192,178),0.32)
ctext(d,1262,"Вы слышите этот звук в последний раз",F("Inter-LightItalic.otf",30),(190,182,170))
b.alpha_composite(shadow(L)); A=b
# section
b=Image.open("frames/p_sec.png").convert("RGBA"); b.alpha_composite(grad(1150,1750,0.75)); L=Image.new("RGBA",(W,H),(0,0,0,0)); d=ImageDraw.Draw(L)
d.line([(90,1440),(170,1440)],fill=GOLD,width=2); tracked(d,(190,1424),"01 · SURMA SETKA",F("Inter-Medium.otf",28),GOLD,0.3)
d.text((88,1470),"Eshik uchun",font=SERI(70),fill=CREAM)
d.text((90,1570),"Shabada kiradi. Chivin — yo‘q.",font=SER(40),fill=(222,214,200))
d.text((90,1622),"Ветер — да. Комары — нет.",font=F("Inter-LightItalic.otf",28),fill=(185,178,166))
b.alpha_composite(shadow(L)); B=b
# end
b=Image.open("frames/p_end.png").convert("RGBA"); ov=Image.new("RGBA",(W,H),(8,8,10,150)); b.alpha_composite(ov); L=Image.new("RGBA",(W,H),(0,0,0,0)); d=ImageDraw.Draw(L)
ctext(d,760,"IMPERIAL",SER(120),CREAM,0.22)
ctext(d,905,"MOSKIT SETKALAR",F("Inter-Medium.otf",30),GOLD,0.34)
d.line([(W/2-60,960),(W/2+60,960)],fill=GOLD,width=2)
ctext(d,990,"Surma · Petlyali · Standart · Uni",SERI(44),CREAM)
ctext(d,1060,"Toshkent shahrida bepul o‘lchov va o‘rnatish · 1 yil kafolat",F("Inter-Regular.otf",28),(205,198,186))
t="Direktga yozing — mosini tanlab beramiz"; f=F("Inter-Medium.otf",34); w=f.getlength(t)
d.rounded_rectangle((W/2-w/2-40,1130,W/2+w/2+40,1200),35,outline=GOLD,width=2); d.text((W/2-w/2,1145),t,font=f,fill=CREAM)
ctext(d,1230,"@imperial_jalyuzi_uz",F("Inter-Regular.otf",28),(190,182,170))
b.alpha_composite(shadow(L)); C=b
sheet=Image.new("RGB",(540*3+40,960),(20,20,22))
for i,im in enumerate((A,B,C)): sheet.paste(im.convert("RGB").resize((540,960)),(i*560,0))
sheet.save("out/premium_namuna.jpg",quality=90); print("ok")
