"""Independent spatial checks for the low courtyard hood and its two roof joins."""
import json
import math
from pathlib import Path
import random
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'generators'))
from archetypes.masonry_house_params import from_phase
from archetypes.masonry_house_v4_copper import patches, surface, add_hood
from archetypes.masonry_house_v4_west_roof import area, clip, z

record=json.loads((ROOT/'data/structures/glessner_house.json').read_text())
p=from_phase(record['phases'][0],record)
bow=p.bows[0]
n=next(r for r in p.ranges if r['name']=='north_range')
e=next(r for r in p.ranges if r['name']=='east_wing')
parts=patches(p);faces,holes=surface(p)
assert len(holes)==1
assert 1.6<bow['roof_rise_m']/.3048<2.,'HABS low hood replaced by a high canopy'
apex=(e['x0'],n['y0'],bow['wall_top_z']+bow['roof_rise_m'])
radius=bow['r']+.20

def contains(poly,x,y):
    return all((b[0]-a[0])*(y-a[1])-(b[1]-a[1])*(x-a[0])>=-1e-8
               for a,b in zip(poly,poly[1:]+poly[:1]))

def north_height(y):
    return n['eave_lo_z']+(n['ridge_z']-n['eave_lo_z'])*(y-n['y0'])/(n['ridge_at']-n['y0'])

def east_height(x):
    return e['eave_lo_z']+(e['ridge_z']-e['eave_lo_z'])*(x-e['x0'])/(e['ridge_at']-e['x0'])

for part in parts:
    poly=part['points'];plane=part['plane']
    assert area(poly)>1e-8,'Reversed/interleaved fan'
    for x,y,h in poly:
        assert abs(h-z(plane,x,y))<1e-7,'Twisted sheet'
        assert h>=north_height(y)-1e-7 and h>=east_height(x)-1e-7,'Sheet passes through host'
        if math.dist((x,y,h),apex)<1e-7:continue
        on_eave=abs(h-bow['wall_top_z'])<1e-7
        assert on_eave or min(abs(h-north_height(y)),abs(h-east_height(x)))<1e-7,'Floating cut edge'
    for other in parts[:parts.index(part)]:
        overlap=[q[:2] for q in poly]
        op=other['points']
        for a,b in zip(op,op[1:]+op[:1]):
            overlap=clip(overlap,(-(b[1]-a[1]),b[0]-a[0],(b[1]-a[1])*a[0]-(b[0]-a[0])*a[1]))
        assert not overlap or abs(area(overlap))<1e-7,'Overlapping copper sheets'

# The footprint used to remove tile must equal the emitted copper, once only.
rng=random.Random(2220)
for _ in range(2400):
    x=rng.uniform(bow['cx']-radius-.5,bow['cx']+radius+.5)
    y=rng.uniform(bow['cy']-radius-.5,bow['cy']+radius+.5)
    hits=[f for f in faces if contains(f,x,y)]
    assert len(hits)==int(contains(holes[0],x,y)),(x,y,'host hole differs from copper',len(hits))

# The short visible north-wall shoulder must support the hood, including its
# ell endpoint. Omitting an endpoint can leave a slit despite perfect roof cuts.
from archetypes.masonry_house_v4_courtyard_roof import wall_profile
profile=wall_profile(p,n['x0'],n['x1'],n['eave_lo_z'])
for j in range(161):
    x=36.+(n['x1']-36.)*j/160
    roof=max(n['eave_lo_z'],min(z(part['plane'],x,n['y0']) for part in parts)) if contains(holes[0],x,n['y0']) else n['eave_lo_z']
    for a,c in zip(profile,profile[1:]):
        if c[0]-a[0]<1e-9:continue
        if a[0]-1e-8<=x<=c[0]+1e-8:
            actual=a[1]+(c[1]-a[1])*(x-a[0])/(c[0]-a[0])
            assert abs(actual-roof)<1e-6,(x,'wall-to-roof slit',actual,roof)
            break

# Seams, low laps, apron and soffit are actual emitted stock. They may tuck
# below a higher adjoining roof, but cannot float above the local roof solid.
class Capture:
    def __init__(self,reduced):
        self.verts=[];self.faces=[];self.roof_uvs={};self.reduced_roof_details=reduced
    def raw(self,pts,*args):
        indices=list(range(len(self.verts),len(self.verts)+len(pts)))
        self.verts.extend(pts);self.faces.append(pts);return indices

for reduced in (False,True):
    b=Capture(reduced);add_hood(b,p)
    for x,y,h in b.verts:
        hood=min(z(part['plane'],x,y) for part in parts)
        supporting=max(hood,north_height(y),east_height(x))
        assert h-supporting<.018,(reduced,'stock floats above the roof',h-supporting)
    assert all(math.isfinite(v) for pair in b.roof_uvs.values() for v in pair)

print(f'PASS: {len(parts)} planar nonoverlapping hood facets; exact shared roof edges; host cut coverage; attached Full/Light stock')
