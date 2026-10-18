import sys,math
import numpy as np
from PIL import Image
Image.MAX_IMAGE_PIXELS=None
im=np.array(Image.open(sys.argv[1]).convert('L')).astype(float)
NE=np.array([2145,4988.]);NW=np.array([8152,4967.]);SE=np.array([2130,2216.])
A=np.column_stack(((NW-NE)/161.25,(SE-NE)/74))
def ws(p):return np.linalg.solve(A,(np.asarray(p,float)-NE[:,None]))
def px(W,S):return NE+A@np.array([W,S])
lo=px(30,38);hi=px(48,50)
x0,x1=int(min(lo[0],hi[0])),int(max(lo[0],hi[0]));y0,y1=int(min(lo[1],hi[1])),int(max(lo[1],hi[1]))
sub=im[y0:y1,x0:x1];ys,xs=np.nonzero(sub<110)
W,S=ws(np.vstack((xs+x0,ys+y0)))
cx,cy=27.8,28.8
r=np.hypot(W-cx,S-cy);a=np.degrees(np.arctan2(S-cy,W-cx))  # angle measured W/S plane
for band in ((180+50,180+56),(180+56,180+62),(180+62,180+66),(180+66,180+69),(180+69,180+71)):
    pass
th=np.degrees(np.arctan2(S-cy,W-cx))  # 0 = due west, 90 = due south
for t0,t1 in ((40,46),(46,52),(52,58),(58,62),(62,66),(66,69),(69,71.5)):
    m=(th>=t0)&(th<t1)&(r>16.8)&(r<19.8)
    h,e=np.histogram(r[m],bins=np.arange(16.8,19.81,0.1))
    peaks=[(round(e[i]+.05,2),int(h[i])) for i in np.argsort(h)[::-1][:5]]
    print(f'theta {t0}-{t1}:',sorted(peaks))
