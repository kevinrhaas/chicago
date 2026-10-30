"""T-2470: continuous curved masonry, facade/roof clearance and drainage."""
import json
import math
from copy import deepcopy
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
    def block(self,polygon,point,normal,confidence,mat,rng,holes=None,course=None):
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

# Both roof sampling levels keep their inlet attached and feed the lower bowl.
# Alter eave height independently: the pipe/soffit must follow geometry, not a
# stale hard-coded datum. Do not alter plan position without updating the facade.
for reduced in (False,True):
    for dz in (0,.15,-.15):
        tower={**t,'wall_top_z':t['wall_top_z']+dz}
        recipe=deepcopy(p)
        recipe.towers=[tower if q['name']=='north' else q for q in recipe.towers]
        b=RoofCapture('tower-test',recipe);b.reduced_roof_details=reduced
        build(b,tower,recipe)
        if recipe.detail.get('rainwater'):
            assert b.north_tower_details[0]['pipe']==[],'Legacy rod must not coexist with the new network'
            from archetypes.masonry_house_v4_drainage import build as rainwater
            rainwater(b,recipe)
        pipe=b.north_tower_details[0]['pipe'];out=pipe[-1]
        if recipe.detail.get('rainwater'):
            head=next(r for r in b.rainwater_network['leaders'] if r['name']=='north-tower')
            assert math.dist(out[:2],head['inlet'][:2])<1e-8
            assert abs(out[2]-(head['mouth']-.09))<1e-8
            assert abs(pipe[0][2]-(tower['wall_top_z']-recipe.detail['rainwater']['gutter_depth_m']-.012))<1e-8
            assert b.north_tower_details[0]['discharge']=='north-tower-bowl'
        else:
            assert abs(out[2]-north_height(p,out[1])-.04)<1e-7
            assert abs(pipe[0][2]-(tower['wall_top_z']-.035))<1e-7
        assert all(a[2]>c[2] for a,c in zip(pipe,pipe[1:]))
        assert b.faces and all(len(f)>=3 for f in b.faces)

# The eave must stop on the tower side of the actual sloping stone gable.
s=p.detail['north_tower_roof'];west=e['north_roof_shoulder']['x'];z=t['wall_top_z']
# The street facade retains its approved26.5ft shoulder independently of
# the corrected courtyard wall-plane eave.
face_z=26.5*.3048
gable=west+(z-e['parapet_m']['north']-face_z)*(e['ridge_at']-west)/(e['ridge_z']-face_z)
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
        if x<e['ridge_at']:
            roof=e['eave_lo_z']+(x-e['x0'])*(e['ridge_z']-e['eave_lo_z'])/(e['ridge_at']-e['x0'])
        else:
            roof=e['eave_hi_z']+(e['x1']-x)*(e['ridge_z']-e['eave_hi_z'])/(e['x1']-e['ridge_at'])
        assert abs(roof-chimney_foot(p,x)-.06)<1e-8
        assert chimney['z0']<=chimney_foot(p,x)+1e-8
# T-2228: test the complete upper roof independently as a height field. An
# extruded apex, a missing connector wedge, or overlapping roof fragments all
# fail this, including where the eastern host changes its pitch.
import random
from archetypes.masonry_house_v4_north_tower import upper_roof,_upper_profile,_join_boundary
def roof_hit(poly,x,y):
    sign=1 if d.area(poly)>0 else -1
    if any(sign*((q[0]-v[0])*(y-v[1])-(q[1]-v[1])*(x-v[0])) < -1e-9
           for v,q in zip(poly,poly[1:]+poly[:1])):return None
    n=d.legacy._normal(poly);v=poly[0]
    return v[2]-(n[0]*(x-v[0])+n[1]*(y-v[1]))/n[2]

for segments in (32,48):
    for change in (-.15,0,.15):
        recipe=deepcopy(p)
        recipe.detail['north_tower_roof']['connector_ridge_z']+=change
        radius,base,ridge=_upper_profile(t,recipe);cx,cy=t['cx'],t['cy']
        cone,connector=upper_roof(t,recipe,segments);surfaces=cone+connector
        west=[(cx+radius*math.cos(math.pi/2+2*math.pi*i/segments),
               cy+radius*math.sin(math.pi/2+2*math.pi*i/segments))
              for i in range(segments//2+1)]
        south=_join_boundary(recipe,cy-radius,base,cy,ridge)
        north=_join_boundary(recipe,cy+radius,base,cy,ridge)
        outline=west+[q[:2] for q in south]+[q[:2] for q in north[-2::-1]]
        assert abs(sum(abs(d.area(q)) for q in surfaces)-abs(d.area(outline)))<1e-7
        assert all(math.dist(v,(cx,cy,t['apex_z']))<1e-7
                   for poly in surfaces for v in poly if abs(v[2]-t['apex_z'])<1e-7), 'Extruded tower apex'
        # Use the analytic regular-cone planes, not the emitted polygons, as
        # the oracle. Sampling includes empty space outside the roof footprint.
        normals=[(math.cos(math.pi/2+2*math.pi*(i+.5)/segments),
                  math.sin(math.pi/2+2*math.pi*(i+.5)/segments)) for i in range(segments)]
        pitch=(t['apex_z']-base)/(radius*math.cos(math.pi/segments))
        rng=random.Random(2228)
        for _ in range(300):
            x=cx+rng.uniform(-radius-.1,7);y=cy+rng.uniform(-radius-.1,radius+.1)
            hcone=t['apex_z']-pitch*max(nx*(x-cx)+ny*(y-cy) for nx,ny in normals)
            hjoin=ridge-(ridge-base)*abs(y-cy)/radius
            expected=[]
            if hcone>=base:expected.append(hcone)
            if x>=cx and abs(y-cy)<=radius and x<=_join_x(recipe,hjoin,y):expected.append(hjoin)
            hits=[z for poly in surfaces if (z:=roof_hit(poly,x,y)) is not None]
            assert len(hits)==bool(expected), ('Roof hole or overlap',segments,change,x,y,hits,expected)
            if hits:assert abs(hits[0]-max(expected))<1e-7
        # Every interior cone/connector join ends on the same lower roof plane.
        for poly in cone:
            for v in poly:
                if v[0]<=cx+1e-7 or abs(v[2]-t['apex_z'])<1e-7:continue
                hjoin=ridge-(ridge-base)*abs(v[1]-cy)/radius
                assert abs(v[2]-hjoin)<1e-7

print('PASS: staggered curved stone, drainage, pointed cone and closed Full/Light roof intersections')

# Probe the connector boundary against the roof fragments actually emitted by
# the host builder, not a second copy of the join helper's plane equations.
host=[];original_roof=d.legacy._two_sided_roof
try:
    d.legacy._two_sided_roof=lambda builder,points,*args:host.append(points)
    capture=RoofCapture('host-roof',p)
    d.legacy._range(capture,e)
finally:d.legacy._two_sided_roof=original_roof
radius,base,ridge=_upper_profile(t,p)
for i in range(1,38):
    y=t['cy']-radius+2*radius*i/38
    if y>=e['y1']-.08:continue # coping conceals the deliberate80mm tuck
    z=ridge-(ridge-base)*abs(y-t['cy'])/radius
    x=_join_x(p,z,y)
    heights=[v for face in host if (v:=roof_hit(face,x,y)) is not None]
    assert heights and min(abs(v-z) for v in heights)<1e-6,('connector misses actual shoulder roof',x,y,z,heights)
print('PASS: connector meets actual emitted north shoulder and courtyard host planes')
