"""T-2470: continuous curved masonry, facade/roof clearance and drainage."""
import json
import math
from pathlib import Path
from _glessner_lod import _geometry_modules
ROOT=Path(__file__).resolve().parents[1]
d,parameters,_=_geometry_modules(ROOT)
from archetypes.masonry_house_v4_north_tower import build,wrapped_stone,clip_host,_join_x
from archetypes.masonry_house_v4_courtyard_roof import north_height
record=json.loads((ROOT/'data/structures/glessner_house.json').read_text())
p=parameters.from_phase(record['phases'][0],record)
t=next(t for t in p.towers if t['name']=='north')
e=next(r for r in p.ranges if r['name']=='east_wing')

class Traced(d.DetailBuilder):
    joints=[]
    def block(self,polygon,point,normal,confidence,mat,rng,holes=None):
        if self.name=='north_tower_unwrapped':
            self.joints.append(d.bounds(polygon))
        return super().block(polygon,point,normal,confidence,mat,rng,holes)

# Use actual Full masonry, including custom normals and UVs. Each physical stone
# is chosen before any angular tessellation; joints must stagger across courses.
b=Traced('curve-test',p);wrapped_stone(b,t,p)
rows={}
for x0,z0,x1,z1 in Traced.joints:rows.setdefault(round(z0,5),set()).add(round(x1,4))
assert len(rows)>5
pairs=list(sorted(rows.items()))
assert sum(a!=c for (_,a),(_,c) in zip(pairs,pairs[1:]))>=len(pairs)-2,'Curved stone joints form a grid'
assert b.rock_normals and all(math.isfinite(v) for pt in b.verts for v in pt)
for i,normal in b.rock_normals.items():
    x,y,z=b.verts[i];radial=d.norm((x-t['cx'],y-t['cy'],0))
    assert d.dot(radial,normal)>.05,'Curved front normal points inward'
    assert abs(math.sqrt(d.dot(normal,normal))-1)<1e-7
    assert i in b.roof_uvs
# Every retained drum facet enters its host roof rather than leaving a bright gap.
assert min(v[2]-north_height(p,v[1]) for v in b.verts)<-.025

class RoofCapture(d.DetailBuilder):
    def wall(self,pts,confidence,mat,custom_holes=None):
        # Roof/drainage perturbations need the envelope, not repeated fracture
        # generation over the entire facade. Actual stone was checked above.
        self.raw(pts,confidence,mat)

# Both roof sampling levels keep their inlet attached and drain onto the host.
# Alter eave height independently: the pipe/soffit must follow geometry, not a
# stale hard-coded datum. Do not alter plan position without updating the facade.
for reduced in (False,True):
    for dz in (0,.15,-.15):
        tower={**t,'wall_top_z':t['wall_top_z']+dz}
        b=RoofCapture('tower-test',p);b.reduced_roof_details=reduced
        build(b,tower,p)
        pipe=b.north_tower_details[0]['pipe'];out=pipe[-1]
        assert abs(out[2]-north_height(p,out[1])-.04)<1e-7
        assert abs(pipe[0][2]-(tower['wall_top_z']-.035))<1e-7
        assert all(a[2]>c[2] for a,c in zip(pipe,pipe[1:]))
        assert b.faces and all(len(f)>=3 for f in b.faces)

# The eave must stop on the tower side of the actual sloping stone gable.
s=p.detail['north_tower_roof'];west=e['north_roof_shoulder']['x'];z=t['wall_top_z']
gable=west+(z-e['parapet_m']['north']-e['eave_lo_z'])*(e['ridge_at']-west)/(e['ridge_z']-e['eave_lo_z'])
assert _join_x(p,z,t['cy']+t['eave_r'])<=gable-.079
# A host-roof patch crossing the upper window plane is entirely removed; a patch
# on the far western range is kept, and uphill roof above the tower stays intact.
def rect(x0,x1,y0,y1,z):return [(x0,y0,z),(x1,y0,z),(x1,y1,z),(x0,y1,z)]
assert not clip_host(rect(t['cx']+.5,e['x1']-.2,e['y1']-.1,e['y1']+.1,7.0),p)
far=rect(t['cx']-t['r']-2,t['cx']-t['r']-1,t['cy'],t['cy']+.2,8.0)
assert clip_host(far,p)
high=rect(t['cx'],t['cx']+1,t['cy'],t['cy']+.2,t['wall_top_z']+.5)
assert clip_host(high,p)==[high]
# No roof sliver may be removed OUTSIDE the curved wall, including the front
# tangent where a convex hull of the combined footprint previously left a gap.
for degrees in range(95,270,5):
    angle=math.radians(degrees)
    x=t['cx']+(t['r']+.04)*math.cos(angle)
    y=t['cy']+(t['r']+.04)*math.sin(angle)
    z=north_height(p,y)
    if z>=t['wall_top_z']:continue
    patch=rect(x-.001,x+.001,y-.001,y+.001,z)
    kept=clip_host(patch,p)
    assert kept and abs(sum(abs(d.area(q)) for q in kept)-.000004)<1e-9,degrees
# Roof changes cannot leave the two main-slope stacks floating. Their feet
# remain 60mm inside the roof at every corner and flashing sees that low datum.
from archetypes.masonry_house_v4_north_tower import chimney_foot
for chimney in p.chimneys:
    if chimney['name'] not in ('middle','south'):continue
    for x in (chimney['x0'],chimney['x1']):
        roof=e['eave_hi_z']+(e['x1']-x)*(e['ridge_z']-e['eave_hi_z'])/(e['x1']-e['ridge_at'])
        assert abs(roof-chimney_foot(p,x)-.06)<1e-8
        assert chimney['z0']<=chimney_foot(p,x)+1e-8
print('PASS: staggered curved stone, outward normals, closed roof contact, gable clearance and Full/Light drainage')
