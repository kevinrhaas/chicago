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

for label,x,y in [('gate',.013,2.411),('passage',41.06,2.411),
                  ('west walk',11.62,6.71),('stair foot',15.53,9.97),('terrace approach',38.52,6.52)]:
 h=hits(x,y);assert len(h)==1 and h[0][1]==d.DRIVE,(label,h)
 assert .035<h[0][0]<.045,(label,'ground level',h)
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
assert set(b.conf)=={1.0},'Reconstructed paving is falsely marked attested'
print('PASS: disjoint court ground, five access contacts, outward fall and 1500 clear turf blades')
