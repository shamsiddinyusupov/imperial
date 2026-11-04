import cv2, numpy as np
A='/mnt/user-data/attachments/29c18e40-edfd-55e7-a3e1-da5539b3418b/'
FILES=['cf92a1b7','c707ce63','ca3bc306','2193799d','bbf7d7d0']
# approximate callout segments inside the frame (original image coords)
APPROX={1:[((198,382),(338,377))],
        2:[((200,348),(343,160)),((198,398),(343,553))],
        3:[((180,144),(345,113)),((180,488),(265,627))],
        4:[((190,250),(300,546))],
        5:[((185,176),(345,119))]}
def sample(g,p,q,n=None):
    n=n or int(np.hypot(q[0]-p[0],q[1]-p[1]))
    t=np.linspace(0,1,n); xs=p[0]+(q[0]-p[0])*t; ys=p[1]+(q[1]-p[1])*t
    return cv2.remap(g.astype(np.float32),xs.astype(np.float32).reshape(1,-1),ys.astype(np.float32).reshape(1,-1),cv2.INTER_LINEAR)[0]
def refine(g,p,q,r=7):
    best=None
    for d1 in range(-r,r+1):
        for d2 in range(-r,r+1):
            # shift endpoints along the segment normal
            v=np.array(q,float)-np.array(p,float); nrm=np.array([-v[1],v[0]])/np.linalg.norm(v)
            pp=np.array(p)+nrm*d1*0.5; qq=np.array(q)+nrm*d2*0.5
            m=sample(g,pp,qq).mean()
            if best is None or m<best[0]: best=(m,tuple(pp),tuple(qq))
    # contrast vs. parallel neighbours
    v=np.array(best[2])-np.array(best[1]); nrm=np.array([-v[1],v[0]])/np.linalg.norm(v)
    side=np.mean([sample(g,np.array(best[1])+nrm*k,np.array(best[2])+nrm*k).mean() for k in (-4,-3,3,4)])
    return best[1],best[2],best[0],side
if __name__=='__main__':
    S='/tmp/claude-0/-home-claude/29c18e40-edfd-55e7-a3e1-da5539b3418b/scratchpad'
    tiles=[]
    for n,f in enumerate(FILES,1):
        im=cv2.imread(A+f+'-image.jpg'); g=cv2.cvtColor(im,cv2.COLOR_BGR2GRAY)
        vis=im.copy()
        for p,q in APPROX[n]:
            pp,qq,m,side=refine(g,p,q)
            print(n,'line',tuple(round(x,1) for x in pp),tuple(round(x,1) for x in qq),'mean',round(m,1),'side',round(side,1))
            cv2.line(vis,(int(pp[0]),int(pp[1])),(int(qq[0]),int(qq[1])),(0,0,255),1)
        tiles.append(cv2.resize(vis[80:665,150:380],None,fx=2,fy=2,interpolation=cv2.INTER_NEAREST))
    out=np.full((tiles[0].shape[0],sum(t.shape[1] for t in tiles)+40,3),255,np.uint8); x=0
    for t in tiles: out[:,x:x+t.shape[1]]=t; x+=t.shape[1]+10
    cv2.imwrite(S+'/lines_found.png',out)
