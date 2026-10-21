"""T-2217: source pattern, real recesses and usable carriage-door swing.

Ray tests inspect emitted faces; clearance reads the approved passage outline.
The UV test includes reversed face winding and intermediate operating angles.
"""
import sys, math, json, collections
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'generators'))
from archetypes.masonry_house_params import from_phase
from archetypes import masonry_house_v4_porte as m
r=json.loads((ROOT/'data/structures/glessner_house.json').read_text())
p=from_phase(r['phases'][0],r)
o=next(o for o in p.openings if o.get('style')=='porte_cochere')
class B:
 def __init__(self,reduced):self.params=p;self.smooth_rock_faces=not reduced;self.polys=[]
 def raw(self,ps,c,mat,want):self.polys.append((ps,mat,want))
for reduced in (False,True):
 b=B(reduced);m.build(b,o);print('reduced',reduced,'triangles',sum(len(a)-2 for a,_,_ in b.polys),collections.Counter(mat for _,mat,_ in b.polys))
 for angle in (0,10,30,50,65,82):
  b=B(reduced)
  for side in (0,1):
   leaf=m.Leaf(b,o,side,math.radians(angle));leaf.body();leaf.hardware()
  pts=[p for poly,_,_ in b.polys for p in poly]
  # Both reveal boundaries as drawn in HABS plan, interpolated beyond mouth.
  def walls(x):
   f=(o['at']-x)/(o['at']-41.0718)
   return o['u0']+f*(.3353-o['u0']),o['u1']+f*(3.2614-o['u1'])
  clearance=min(min(y-walls(x)[0],walls(x)[1]-y) for x,y,z in pts)
  zf,zc=p.detail['prairie_frontage']['passage_front_z'],p.detail['prairie_frontage']['passage_court_z']
  floor=min(z-(zf+max(0,o['at']-x)/(o['at']-41.0718)*(zc-zf)) for x,y,z in pts)
  print(angle,'wall clearance',round(clearance,4),'floor',round(floor,4))
  assert clearance>=.01 and floor>=.01
  assert not any(o['at']-.286<x<o['at']-.169 and (y<o['u0']+.05 or y>o['u1']-.05) for x,y,z in pts), 'Moving leaf clips fixed oak lining'

def hits(polys,y,z):
 found=[]
 for poly,mat,_ in polys:
  if mat!=6:continue
  for i in range(1,len(poly)-1):
   a,c,d=poly[0],poly[i],poly[i+1]
   den=(c[2]-d[2])*(a[1]-d[1])+(d[1]-c[1])*(a[2]-d[2])
   if abs(den)<1e-12:continue
   wa=((c[2]-d[2])*(y-d[1])+(d[1]-c[1])*(z-d[2]))/den
   wb=((d[2]-a[2])*(y-d[1])+(a[1]-d[1])*(z-d[2]))/den
   wc=1-wa-wb
   if min(wa,wb,wc)>=-1e-8:found.append(wa*a[0]+wb*c[0]+wc*d[0])
 return found
for reduced in (False,True):
 b=B(reduced);m.build(b,o,0)
 for side in (0,1):
  leaf=m.Leaf(b,o,side,0)
  for f in (.15,.44,.73):
   for t in (.12,.26,.40,.54,.74,.88):
    y,z,_=leaf.local(f,t,0);h=hits(b.polys,y,z)
    assert abs(max(h)-(o['at']-.215))<1e-7,'Square field is not actually recessed'
    assert abs(min(h)-(o['at']-.27))<1e-7,'Unseen face is open'
    y,z,_=leaf.local(f+.13,t,0);h=hits(b.polys,y,z)
    assert abs(max(h)-(o['at']-.18))<1e-7,'Continuous oak missing outside circular recess'
 print('PASS field-depth rays, continuous surrounds and closed backs:', 'Light' if reduced else 'Full')

class Capture(B):
 def __init__(self,reduced):super().__init__(reduced);self.verts=[];self.roof_uvs={};self.faces=[]
 def raw(self,ps,c,mat,want):
  a,b,c=ps[:3];v=[b[i]-a[i] for i in range(3)];w=[c[i]-a[i] for i in range(3)];n=[v[1]*w[2]-v[2]*w[1],v[2]*w[0]-v[0]*w[2],v[0]*w[1]-v[1]*w[0]]
  if sum(n[i]*want[i] for i in range(3))<0:ps=list(reversed(ps))
  ids=list(range(len(self.verts),len(self.verts)+len(ps)));self.verts.extend(ps);self.faces.append((ids,mat));return ids

for angle in (0,37,82):
 b=Capture(False);m.build(b,o,angle)
 checked=0
 for ix,mat in b.faces:
  if mat!=6:continue
  assert all(i in b.roof_uvs for i in ix)
  pts=[b.roof_uvs[i] for i in ix]
  area=abs(sum(p[0]*q[1]-q[0]*p[1] for p,q in zip(pts,pts[1:]+pts[:1]))/2)
  assert area>1e-12,('collapsed wood UV',angle,ix,pts)
  checked+=1
 print('PASS wood metric UVs, including narrow edges and reversed winding',angle,checked,'faces')

# The closed pose must leave only the narrow meeting joint, not half a leaf.
a,c=(m.Leaf(B(False),o,side,0) for side in (0,1))
assert .008 < c.meeting-a.meeting < .018
assert abs(a.w-c.w)<1e-8
print('PASS: symmetric meeting stiles with a 12-mm operating joint')
