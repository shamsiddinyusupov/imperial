import cv2, numpy as np
from PIL import Image, ImageFilter
from lines import A, FILES
from lines2 import get_lines
OUT='/home/claude/reels/site/img'
NAMES={1:'st_standart',2:'st_petlya',3:'st_uni',4:'st_surma_oyna',5:'st_surma_eshik'}
CLIP={}
MANUAL={1:[((186,375),(352,372))], 5:[((184,172.8),(301,116.9))]}   # hand-read where the search drifted
EXT=6
EXTRA={3:[((180.2,615.3),(341,659))]}
HW=3.2                           # half-width of the band painted over each callout
def period(patch, axis):
    p=patch.astype(np.float32)-patch.mean()
    prof=p.mean(axis=1-axis)     # axis0 -> vertical profile
    ac=np.correlate(prof,prof,'full')[len(prof)-1:]
    for k in range(2,12):
        if ac[k]>ac[k-1] and ac[k]>=ac[k+1] and ac[k]>0: return k
    return 3
def clean(n):
    im=cv2.imread(A+FILES[n-1]+'-image.jpg'); g=cv2.cvtColor(im,cv2.COLOR_BGR2GRAY)
    H,W=g.shape
    lines=get_lines_cache[n]
    if n in MANUAL: lines=[(np.array(p_,float),np.array(q_,float)) for p_,q_ in MANUAL[n]]
    if n in EXTRA: lines=list(lines)+[(np.array(p_,float),np.array(q_,float)) for p_,q_ in EXTRA[n]]
    ext=[]
    for p_,q_ in lines:
        u_=(q_-p_)/np.linalg.norm(q_-p_); ext.append((p_-u_*EXT, q_+u_*EXT))
    lines=ext
    if False and n in CLIP:
        nl=[]
        for (p,q),(_,xmax) in zip(lines,CLIP[n]):
            if xmax is not None and q[0]>xmax:
                t=(xmax-p[0])/(q[0]-p[0]); q=p+(q-p)*t
            nl.append((p,q))
        lines=nl
    frame=(g<110)
    frame=cv2.dilate(frame.astype(np.uint8),np.ones((3,3),np.uint8))>0
    yy,xx=np.mgrid[0:H,0:W]
    res=im.copy()
    for p,q in lines:
        v=q-p; L=np.linalg.norm(v); u=v/L; nrm=np.array([-u[1],u[0]])
        rel_x=xx-p[0]; rel_y=yy-p[1]
        along=rel_x*u[0]+rel_y*u[1]; dist=rel_x*nrm[0]+rel_y*nrm[1]
        band=(np.abs(dist)<=HW)&(along>=-2)&(along<=L+2)&(~frame)
        ang=abs(np.degrees(np.arctan2(v[1],v[0])))%180
        ang=min(ang,180-ang)
        # local mesh period from a clean patch near the line middle, offset away from the band
        mid=(p+q)/2+nrm*14
        cx,cy=int(np.clip(mid[0],20,W-21)),int(np.clip(mid[1],20,H-21))
        patch=g[cy-16:cy+16,cx-16:cx+16]
        if ang<45: axis=0; per=period(patch,0)      # shift vertically
        else: axis=1; per=period(patch,1)           # shift horizontally
        ys,xs=np.where(band)
        for y,x in zip(ys,xs):
            done=False
            for k in range(1,10):
                for sgn in (1,-1):
                    s=sgn*k*per
                    sy,sx=(y+s,x) if axis==0 else (y,x+s)
                    if not(0<=sy<H and 0<=sx<W): continue
                    d2=(sx-p[0])*nrm[0]+(sy-p[1])*nrm[1]
                    if abs(d2)>HW+0.8 and not frame[sy,sx]:
                        res[y,x]=im[sy,sx]; done=True; break
                if done: break
        print(n,'line ang',round(ang,1),'axis',axis,'period',per,'px',len(ys))
    # frame interior mask (row-wise span of dark frame pixels)
    dark=(g<110); dark[:85]=False; dark[690:]=False
    # keep only the frame: largest dark component + parts touching its bounding box (handles, hinges)
    nlab,lab,st,_=cv2.connectedComponentsWithStats(dark.astype(np.uint8),connectivity=8)
    big=1+int(np.argmax(st[1:,cv2.CC_STAT_AREA]))
    bx,by,bw,bh_=st[big,0],st[big,1],st[big,2],st[big,3]
    keep=np.zeros(nlab,bool); keep[big]=True
    for i in range(1,nlab):
        x,y,w,h=st[i,0],st[i,1],st[i,2],st[i,3]
        if x>=bx-4 and x+w<=bx+bw+14 and y>=by-4 and y+h<=by+bh_+4: keep[i]=True
    dark=keep[lab]
    rows=np.where(dark.any(1))[0]; top,bot=rows.min(),rows.max()
    Lc=np.full(H,-1); Rc=np.full(H,-1)
    for y in range(top,bot+1):
        xsr=np.where(dark[y])[0]
        if len(xsr): Lc[y]=xsr.min(); Rc[y]=xsr.max()
    # fill gaps by interpolation, then smooth
    idx=np.arange(H); ok=Lc>=0
    Lc=np.interp(idx,idx[ok],Lc[ok]); Rc=np.interp(idx,idx[ok],Rc[ok])
    mask=np.zeros((H,W),np.uint8)
    for y in range(top,bot+1): mask[y,int(Lc[y]):int(Rc[y])+1]=255
    return res,mask,(top,bot,int(Lc[top:bot+1].min()),int(Rc[top:bot+1].max()))
def compose(n,res,mask,bbox,CW=600,CH=1000):
    top,bot,l,r=bbox
    m=6
    crop=cv2.cvtColor(res[top-m:bot+m+1,l-m:r+m+1],cv2.COLOR_BGR2RGB)
    mk=mask[top-m:bot+m+1,l-m:r+m+1]
    ci=Image.fromarray(crop); mi=Image.fromarray(mk).filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.GaussianBlur(0.8))
    sc=CH*0.86/ci.height
    nw,nh=round(ci.width*sc),round(ci.height*sc)
    ci=ci.resize((nw,nh),Image.LANCZOS).filter(ImageFilter.UnsharpMask(radius=1.2,percent=60,threshold=2))
    mi=mi.resize((nw,nh),Image.LANCZOS)
    # studio background: soft vertical gradient + vignette, plus contact shadow
    ys=np.linspace(0,1,CH)[:,None]; xs=np.linspace(-1,1,CW)[None,:]
    bgv=(226-14*ys)-10*(xs**2)
    bg=np.repeat(np.clip(bgv,0,255)[...,None],3,2).astype(np.uint8)
    canvas=Image.fromarray(bg)
    ox,oy=(CW-nw)//2,int(CH*0.06)
    sh=Image.new('L',(CW,CH),0); sh.paste(mi,(ox+10,oy+16))
    sh=sh.filter(ImageFilter.GaussianBlur(18)).point(lambda v:int(v*0.32))
    dark_layer=Image.new('RGB',(CW,CH),(60,60,62))
    canvas=Image.composite(dark_layer,canvas,sh)
    canvas.paste(ci,(ox,oy),mi)
    canvas.save(f'{OUT}/{NAMES[n]}.jpg',quality=88,optimize=True,progressive=True)
    return canvas
get_lines_cache=get_lines()
if __name__=='__main__':
    S='/tmp/claude-0/-home-claude/29c18e40-edfd-55e7-a3e1-da5539b3418b/scratchpad'
    outs=[]
    for n in range(1,6):
        res,mask,bbox=clean(n); outs.append(compose(n,res,mask,bbox))
        cv2.imwrite(f'{S}/clean_{n}.png',res[80:665,150:380])
    sheet=Image.new('RGB',(5*310,520),'white')
    for i,c in enumerate(outs): sheet.paste(c.resize((300,500)),(i*310,0))
    sheet.save(S+'/setka_out.jpg',quality=88)
    z=[cv2.resize(cv2.imread(f'{S}/clean_{n}.png'),None,fx=2,fy=2,interpolation=cv2.INTER_NEAREST) for n in range(1,6)]
    o=np.full((z[0].shape[0],sum(t.shape[1] for t in z)+40,3),255,np.uint8); x=0
    for t in z: o[:,x:x+t.shape[1]]=t; x+=t.shape[1]+10
    cv2.imwrite(S+'/clean_zoom.png',o)
