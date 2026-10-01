"""Independent spatial checks for the stable roof's union, without Blender."""
import json
from pathlib import Path
import random
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'generators'))
from archetypes.masonry_house_params import from_phase
from archetypes.masonry_house_west_roof import components, patches, height, z, bounds_planes, profile

record=json.loads((ROOT/'data/structures/glessner_house.json').read_text())
p=from_phase(record['phases'][0],record)
r=next(r for r in p.ranges if r.get('stable_roof'))
patch=patches(r)
def contains(poly,x,y):
    return all((b[0]-a[0])*(y-a[1])-(b[1]-a[1])*(x-a[0])>=-1e-9 for a,b in zip(poly,poly[1:]+poly[:1]))
rng=random.Random(1830)
for i in range(1800):
    x=rng.uniform(r['x0']-.55,r['x1']);y=rng.uniform(r['y0']-.15,r['y1'])
    expected=[min(z(v,x,y) for v in ps) for _,box,ps in components(r)
              if all(z(b,x,y)>=0 for b in bounds_planes(box))]
    hits=[pts for _,pts in patch if contains(pts,x,y)]
    assert len(hits)==int(bool(expected)), (i,x,y,len(hits))
    if hits:
        a,b,c=hits[0][:3];v=[b[k]-a[k] for k in range(3)];w=[c[k]-a[k] for k in range(3)]
        n=[v[1]*w[2]-v[2]*w[1],v[2]*w[0]-v[0]*w[2],v[0]*w[1]-v[1]*w[0]]
        assert abs(n[2])>1e-10
        actual=a[2]-(n[0]*(x-a[0])+n[1]*(y-a[1]))/n[2]
        assert abs(actual-max(expected))<1e-6,(i,actual,max(expected))
# The lower rear eave is continuous and the sheet-3 south openings remain clear.
assert abs(height(r,r['x0'],(74-40)*.3048)-15.5*.3048)<1e-4
for W in [139,144,149]:assert height(r,(161.25-W)*.3048,r['y0'])>=23*.3048
for face in ['west','east','south']:
    for a,b in zip(profile(r,face),profile(r,face)[1:]):assert b[0]>a[0]
entry=p.detail['north_entry_alcove']
assert entry['east_x']>entry['x'][1]
assert entry['threshold_z']>entry['landing_z']>0
assert any(o.get('style')=='north_entry_alcove' for o in p.openings)
print('PASS: 1800 independent roof rays see exactly one planar envelope; rear/east/south eaves and left-turn porch dimensions hold.')
