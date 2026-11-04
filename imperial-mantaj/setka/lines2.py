import cv2, numpy as np
from lines import A, FILES, sample
APPROX={1:[((203,374),(343,372))],
        2:[((197,344),(339,159)),((196,396),(340,551))],
        3:[((178,147),(340,116)),((178,487),(263,628))],
        4:[((188,248),(300,546))],
        5:[((183,182),(345,121))]}
FIXED={1}   # near-horizontal line along the mesh: keep the hand-read position
def find(bh,p,q,r=12,step=0.5):
    p=np.array(p,float); q=np.array(q,float); v=q-p; nrm=np.array([-v[1],v[0]])/np.linalg.norm(v)
    best=None
    for d1 in np.arange(-r,r+step,step):
        for d2 in np.arange(-r,r+step,step):
            pp=p+nrm*d1; qq=q+nrm*d2
            m=sample(bh,pp,qq).mean()
            if best is None or m>best[0]: best=(m,pp,qq)
    return best
def get_lines():
    out={}
    for n,f in enumerate(FILES,1):
        g=cv2.imread(A+f+'-image.jpg',0)
        bh=cv2.morphologyEx(g,cv2.MORPH_BLACKHAT,cv2.getStructuringElement(cv2.MORPH_ELLIPSE,(7,7))).astype(np.float32)
        out[n]=[]
        for p,q in APPROX[n]:
            if n in FIXED: out[n].append((np.array(p,float),np.array(q,float))); continue
            m,pp,qq=find(bh,p,q)
            base=np.median([sample(bh,np.array(p)+np.array([0,k]),np.array(q)+np.array([0,k])).mean() for k in range(-20,21,5)])
            print(n,'found',pp.round(1),qq.round(1),'resp',round(m,2),'typical',round(base,2))
            out[n].append((pp,qq))
    return out
if __name__=='__main__':
    S='/tmp/claude-0/-home-claude/29c18e40-edfd-55e7-a3e1-da5539b3418b/scratchpad'
    L=get_lines(); tiles=[]
    for n,f in enumerate(FILES,1):
        im=cv2.imread(A+f+'-image.jpg'); vis=im.copy()
        for pp,qq in L[n]:
            v=qq-pp; nrm=np.array([-v[1],v[0]])/np.linalg.norm(v)*6
            for s,c in ((nrm,(0,160,0)),(-nrm,(0,160,0))):
                a=(pp+s).astype(int); b=(qq+s).astype(int); cv2.line(vis,tuple(int(x) for x in a),tuple(int(x) for x in b),c,1)
        tiles.append(cv2.resize(vis[80:665,150:380],None,fx=2,fy=2,interpolation=cv2.INTER_NEAREST))
    o=np.full((tiles[0].shape[0],sum(t.shape[1] for t in tiles)+40,3),255,np.uint8); x=0
    for t in tiles: o[:,x:x+t.shape[1]]=t; x+=t.shape[1]+10
    cv2.imwrite(S+'/lines_found2.png',o)
