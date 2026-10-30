"""Exercise emitted courtyard surfaces, actual access contacts and turf clearance."""
import json
from pathlib import Path
from _glessner_lod import _geometry_modules,_triangles,_normal
ROOT=Path(__file__).resolve().parents[1]
d,pm,_=_geometry_modules(ROOT)
from archetypes.masonry_house_v4_ground import build,layout
from archetypes.masonry_house_v4_landscape import _inside,add_lawn_blades
r=json.loads((ROOT/'data/structures/glessner_house.json').read_text());p=pm.from_phase(r['phases'][0],r)
b=d.DetailBuilder('ground-test',p);sample=build(b,p);plan=layout(p)
ts=[]
for face,mat in zip(b.faces,b.mat_index):
 pts=[b.verts[i] for i in face];n=_normal(pts)
 for inds in _triangles(pts,n):
  tri=[pts[i] for i in inds]
  assert sum(x*x for x in d.cross(d.sub(tri[1],tri[0]),d.sub(tri[2],tri[0])))>1e-18,'Degenerate ground triangle'
  if n[2]>.5:ts.append((tri,mat))

def hits(x,y):
 result=[]
 for tri,mat in ts:
  a,c,e=tri;den=(c[1]-e[1])*(a[0]-e[0])+(e[0]-c[0])*(a[1]-e[1])
  if abs(den)<1e-12:continue
  u=((c[1]-e[1])*(x-e[0])+(e[0]-c[0])*(y-e[1]))/den
  v=((e[1]-a[1])*(x-e[0])+(a[0]-e[0])*(y-e[1]))/den
  if min(u,v,1-u-v)>1e-7:result.append((u*a[2]+v*c[2]+(1-u-v)*e[2],mat))
 return result

from archetypes.masonry_house_v4_frontage import court_ramp
from archetypes.masonry_house_v4_ground import fall_height
ramp=court_ramp(p);fall=fall_height(p)
# T-2978: sheet 4's fall, lawn to passage mouth. The bank's top is at the court's level,
# the drive and lawn before the mouth 1.32 ft down, and the strip behind the drive's
# south edge keeps the court's level (1808's wall stands on it).
mf=p.detail['court_ground']['mouth_fall']
assert abs(fall(mf['x'][0]-.5,mf['y'][0]+.2))<1e-9 and abs(fall(mf['x'][0]-.5,2.0)+mf['depth_m'])<1e-6
assert abs(fall(mf['x'][0]-.5,.3))<1e-9 and abs(fall(mf['x'][2]-.2,2.0))<1e-9
lawn_low=hits(mf['x'][0]-1.0,3.42)
assert lawn_low and abs(lawn_low[0][0]-(.0152-mf['depth_m']))<.003,('lawn before the mouth',lawn_low)
strip=hits(mf['x'][0]-3.0,.3)
assert strip and abs(strip[0][0]-.0152)<.003,('strip behind the drive',strip)
for label,x,y in [('gate',.013,2.411),('passage',41.06,2.411),('ramp top',ramp['pts'][1][0]-.01,2.411),
                  ('west walk',11.62,6.71),('stair foot',15.53,9.97),('terrace approach',38.52,6.52)]:
 h=hits(x,y);assert len(h)==1 and h[0][1]==d.DRIVE,(label,h)
 if label=='passage':
  # T-2976: the court mouth is sunk; the ramp rises from it toward the drive.
  run=ramp['pts'][0][0]-ramp['pts'][1][0];want=ramp['z'][0]+(ramp['z'][1]-ramp['z'][0])*(ramp['pts'][0][0]-x)/run
  assert abs(h[0][0]-want)<.002,(label,'ramp level',h,want)
 else:
  # T-2978: the court ground falls to the passage mouth; the drive follows it.
  want=.0366+fall(x,y)
  assert abs(h[0][0]-want)<.005,(label,'ground level',h,want)
# Probe just outside the actual lowest terrace tread across its entire width.
a,c=p.detail['bow_terrace']['stair_boundaries'][-1][-2:]
import math
length=math.dist(a,c);nx,ny=-(c[1]-a[1])/length,(c[0]-a[0])/length
for t in (.1,.5,.9):
 x=a[0]+t*(c[0]-a[0])+.02*nx;y=a[1]+t*(c[1]-a[1])+.02*ny
 h=hits(x,y);assert len(h)==1 and h[0][1]==d.DRIVE,('Unpaved terrace tread foot',t,h)
# West wall sheds into the court, not toward masonry.
assert hits(10.86,6.71)[0][0]>hits(11.99,6.71)[0][0]
# Do not merely hide the old lawn under a second surface.
for ix in range(1,83):
 for iy in range(1,29):
  x=ix*.493+.00317;y=iy*.493+.00671
  h=hits(x,y)
  assert len(h)<=1,('Overlapping ground layers',x,y,h)
# Small deterministic sample checks actual emitted blade vertices, not just roots.
g=d.DetailBuilder('grass-test',p);count=add_lawn_blades(g,sample,max_blades=1500)
assert count==1500
for point in g.verts:
 assert all(not _inside(point[:2],mask) for mask in plan['grass_masks']),'Grass intrudes into hard/occupied surface'
roots=[v for v in g.verts if fall(v[0],v[1])<-.05]
assert roots,'no blades on the sunk lawn before the mouth'
assert all(v[2]<.06+fall(v[0],v[1]) for v in roots),'blades float over the sunk lawn'
assert set(b.conf)=={1.0},'Reconstructed paving is falsely marked attested'
print('PASS: disjoint court ground, five access contacts, outward fall and 1500 clear turf blades')
