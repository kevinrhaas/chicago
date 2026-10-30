# T-2928: profile native HABS sheet 4 across a band, on T-2228's section controls (north wall x 1165,
# grade y 5858, 100.6 / 97.7 px per ft). Prints each dark line as S or height above north grade, in feet.
# Run from chicago/:  python3 4d/docs/RESEARCH/glessner-court-strip-T-2928/line_profile.py LABEL rows|cols A0 A1 B0 B1 THRESHOLD [...]
#   rows: A = S band, B = height range;  cols: A = height band, B = S range
from PIL import Image; import numpy as np, sys
Image.MAX_IMAGE_PIXELS=None
im=np.array(Image.open('prairie_1904_v1/research/public/glessner-habs-sheet-4.png').convert('L'))
NX,GY,PX,PY=1165,5858,100.6,97.7
X=lambda s:int(round(NX+s*PX))
def run(mode,a0,a1,b0,b1,thr):
    if mode=='rows':  # a=S band, b=z range
        x0,x1=X(a0),X(a1); y0,y1=int(GY-b1*PY),int(GY-b0*PY); f=(im[y0:y1,x0:x1]<128).mean(1)
        out=[(round((GY-(y0+i))/PY,2),round(v,2)) for i,v in enumerate(f) if v>thr]
    else:  # a=z band, b=S range
        x0,x1=X(b0),X(b1); y0,y1=int(GY-a1*PY),int(GY-a0*PY); f=(im[y0:y1,x0:x1]<128).mean(0)
        out=[(round((x0+i-NX)/PX,2),round(v,2)) for i,v in enumerate(f) if v>thr]
    # merge adjacent
    grp=[];
    for p,v in out:
        if grp and abs(p-grp[-1][-1][0])<=0.03: grp[-1].append((p,v))
        else: grp.append([(p,v)])
    return ' | '.join(f"{g[0][0]}..{g[-1][0]}({max(v for _,v in g)})" for g in grp)
args=sys.argv[1:]
while args:
    lab,mode,*nums=args[:7]; args=args[7:]
    print(lab, mode, run(mode,*map(float,nums[:4]),float(nums[4])))
