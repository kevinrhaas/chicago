import sys,math
import numpy as np
from PIL import Image
Image.MAX_IMAGE_PIXELS=None
im=np.array(Image.open(sys.argv[1]).convert('L')).astype(float)
NE=np.array([2145,4988.]);NW=np.array([8152,4967.]);SE=np.array([2130,2216.])
A=np.column_stack(((NW-NE)/161.25,(SE-NE)/74))
def px(W,S):return NE+A@np.array([W,S])
def ws(p):return np.linalg.solve(A,np.asarray(p,float)-NE)
c0=px(33.7,46.2)
H=70
x0,y0=int(c0[0])-H,int(c0[1])-H
sub=im[y0:y0+2*H,x0:x0+2*H]
ys,xs=np.nonzero(sub<110)
pts=np.column_stack((xs+x0,ys+y0)).astype(float)
best=None
rng=np.random.default_rng(1)
for it in range(4000):
    s=pts[rng.choice(len(pts),3,replace=False)]
    (ax,ay),(bx,by),(cx,cy)=s
    d=2*(ax*(by-cy)+bx*(cy-ay)+cx*(ay-by))
    if abs(d)<1e-6:continue
    ux=((ax*ax+ay*ay)*(by-cy)+(bx*bx+by*by)*(cy-ay)+(cx*cx+cy*cy)*(ay-by))/d
    uy=((ax*ax+ay*ay)*(cx-bx)+(bx*bx+by*by)*(ax-cx)+(cx*cx+cy*cy)*(bx-ax))/d
    r=math.hypot(ax-ux,ay-uy)
    if not 20<r<45:continue
    if math.dist((ux,uy),c0)>30:continue
    dist=np.abs(np.hypot(pts[:,0]-ux,pts[:,1]-uy)-r)
    n=(dist<1.5).sum()
    if best is None or n>best[0]:best=(n,ux,uy,r)
n,ux,uy,r=best
inl=pts[np.abs(np.hypot(pts[:,0]-ux,pts[:,1]-uy)-r)<3]
# algebraic refit on inliers
M=np.column_stack((inl[:,0],inl[:,1],np.ones(len(inl))));b=-(inl[:,0]**2+inl[:,1]**2)
D,E,F=np.linalg.lstsq(M,b,rcond=None)[0];ux,uy=-D/2,-E/2;r=math.sqrt(ux*ux+uy*uy-F)
# ink thickness: radial spread of inliers
rad=np.hypot(inl[:,0]-ux,inl[:,1]-uy)
pxft=np.linalg.norm(A[:,0])
print('inliers',len(inl),'centre WS',ws((ux,uy)).round(3),'r_ft centreline',round(r/pxft,3),'ink inner/outer r_ft',round(np.percentile(rad,5)/pxft,3),round(np.percentile(rad,95)/pxft,3),'px/ft',round(pxft,2))
# angular coverage
ang=np.degrees(np.arctan2(inl[:,1]-uy,inl[:,0]-ux))
h,_=np.histogram(ang,bins=12,range=(-180,180));print('coverage by 30deg',h.tolist())
