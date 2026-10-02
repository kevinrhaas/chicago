"""Independent spatial checks for the stable roof's union, without Blender."""
import json
from pathlib import Path
import random
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'generators'))
from archetypes.masonry_house_params import from_phase
from archetypes.masonry_house_v4_west_roof import components, patches, height, z, bounds_planes, profile

record=json.loads((ROOT/'data/structures/glessner_house.json').read_text())
p=from_phase(record['phases'][0],record)
r=next(r for r in p.ranges if r.get('stable_roof'))
patch=patches(r)
def contains(poly,x,y):
    return all((b[0]-a[0])*(y-a[1])-(b[1]-a[1])*(x-a[0])>=-1e-9 for a,b in zip(poly,poly[1:]+poly[:1]))
rng=random.Random(1830)
for i in range(1800):
    x=rng.uniform(r['x0']-.55,r['x1']+.20);y=rng.uniform(r['y0']-.15,r['y1'])
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
# Owner's rear correction: equal shoulders, centered solid gable, no rear hip,
# and an unbroken level ridge from the front gable to the rear wall.
g=r['stable_roof'];mid=(r['x0']+r['x1'])/2
assert r['conf_roof']==r['conf_plan']==1.0
assert abs(g['rear_x']-mid)<1e-4
for y in [r['y0'],(74-40)*.3048,g['north_range']['y0']]:
    assert abs(height(r,mid,y)-38.6*.3048)<1e-4
    for offset in [0,1,2,3,4]:
        assert abs(height(r,mid-offset,y)-height(r,mid+offset,y))<1e-4
for i in range(41):
    t=i/40;lo,hi=g['north_range']['y0'],g['cross_y']
    x=g['rear_x']+(r['ridge_at']-g['rear_x'])*t
    assert abs(height(r,x,lo+(hi-lo)*t)-38.6*.3048)<1e-4
assert abs(height(r,r['x0'],r['y0'])-26.5*.3048)<1e-4
assert abs(height(r,r['x1'],r['y0'])-g['north_range']['eave_lo_z'])<1e-4
for W in [139,144,149]:assert height(r,(161.25-W)*.3048,r['y0'])>=23*.3048
for face in ['west','east','south']:
    for a,b in zip(profile(r,face),profile(r,face)[1:]):
        assert b[0]>a[0]
        for t in [.1,.5,.9]:
            u=a[0]+(b[0]-a[0])*t
            expected=height(r,r['x0'] if face=='west' else r['x1'],u) if face!='south' else height(r,u,r['y0'])
            assert abs(expected-(a[1]+(b[1]-a[1])*t))<1e-5,(face,u,expected)
d=p.detail['west_dormer']
for y in [d['u0'],(d['u0']+d['u1'])/2,d['u1']]:
    assert d['eave_z']-1.35>height(r,d['front'],y)
    assert d['eave_z']>height(r,d['back'],y)
entry=p.detail['north_entry_alcove']
assert entry['east_x']>entry['x'][1]
assert entry['threshold_z']>entry['landing_z']>0
assert any(o.get('style')=='north_entry_alcove' for o in p.openings)
print('PASS: 1800 independent roof rays see exactly one planar envelope; balanced south gable, continuous ridge, matching court eave and left-turn porch dimensions hold.')
