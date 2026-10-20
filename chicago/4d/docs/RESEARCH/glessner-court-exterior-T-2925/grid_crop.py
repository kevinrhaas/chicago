# T-2925: crop native HABS sheet 4 with a grid of S (red) and height above north grade (blue), in feet,
# on T-2228's section controls (north wall x 1165, grade y 5858, 100.6 / 97.7 px per ft). The readings in
# README.md were taken off these crops. Run from chicago/:
#   python3 4d/docs/RESEARCH/glessner-court-exterior-T-2925/grid_crop.py prairie_1904_v1/research/public/glessner-habs-sheet-4.png out.png S0 S1 Z0 Z1 [step] [scale]
import sys
from PIL import Image, ImageDraw
Image.MAX_IMAGE_PIXELS=None
NX,GY,PX,PY=1165,5858,100.6,97.7
src,out,s0,s1,z0,z1=sys.argv[1],sys.argv[2],*map(float,sys.argv[3:7])
step=float(sys.argv[7]) if len(sys.argv)>7 else 0.5
scale=float(sys.argv[8]) if len(sys.argv)>8 else 1.0
im=Image.open(src)
x0,x1=int(NX+s0*PX),int(NX+s1*PX); y0,y1=int(GY-z1*PY),int(GY-z0*PY)
c=im.crop((x0,y0,x1,y1)).convert('RGB')
c=c.resize((int(c.width*scale),int(c.height*scale)))
d=ImageDraw.Draw(c)
import math
s=math.ceil(s0/step)*step
while s<=s1:
    x=(NX+s*PX-x0)*scale; major=abs(s-round(s))<1e-6
    d.line([(x,0),(x,c.height)],fill=(255,0,0) if major else (255,170,170),width=1)
    if major: d.text((x+2,2),f"{s:.0f}",fill=(255,0,0))
    s+=step
z=math.ceil(z0/step)*step
while z<=z1:
    y=(GY-z*PY-y0)*scale; major=abs(z-round(z))<1e-6
    d.line([(0,y),(c.width,y)],fill=(0,0,255) if major else (170,170,255),width=1)
    if major: d.text((2,y+2),f"{z:.0f}",fill=(0,0,255))
    z+=step
c.save(out)
print(c.size)
