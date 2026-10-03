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
# The active reconstruction has a lower rear gable. Test its silhouette against
# explicit owner-reference proportions, not merely the implementation's planes.
g=r['stable_roof'];mid=(r['x0']+r['x1'])/2
assert r['conf_roof']==r['conf_plan']==1.0
if g.get('lower_rear_gable'):
    assert not g.get('continuous_south_gable')
    assert abs(g['cross_y']-(74-18.4)*.3048)<1e-4
    assert abs(height(r,r['x0'],g['cross_y'])-38.6*.3048)<1e-4
    assert abs(height(r,r['x0'],r['y1'])-23.1*.3048)<1e-4
    for south in [35,40,50,59.75]:
        y=(74-south)*.3048
        assert abs(height(r,r['x0'],y)-16.5*.3048)<1e-4
        assert abs(height(r,g['rear_x'],y)-25.5*.3048)<1e-4
        assert abs(height(r,r['x1'],y)-23.1*.3048)<1e-4
    # The east edge must meet the independent, measured north-range section.
    # Roof-wall rays alone could pass while leaving a vertical gap at this join.
    import math
    n=g['north_range'];run=n['kick']['run_m'];yk=n['y0']+run
    rise=math.tan(math.radians(n['kick']['pitch_deg']))
    zk=n['eave_lo_z']+run*rise
    for i in range(81):
        y=n['y0']-.20+(n['y1']-n['y0']+.20)*i/80
        if y<=yk:expected=n['eave_lo_z']+(y-n['y0'])*rise
        elif y<=n['ridge_at']:expected=zk+(n['ridge_z']-zk)*(y-yk)/(n['ridge_at']-yk)
        else:expected=n['ridge_z']+(n['eave_hi_z']-n['ridge_z'])*(y-n['ridge_at'])/(n['y1']-n['ridge_at'])
        assert abs(height(r,r['x1'],y)-expected)<1e-5,(y,expected)
    # Every internal envelope edge meets its neighbour. A cover-count test alone
    # cannot detect an abrupt height step between two nonoverlapping patches.
    for _,pts in patches(r,False):
        for a,b in zip(pts,pts[1:]+pts[:1]):
            dx,dy=b[0]-a[0],b[1]-a[1];length=math.hypot(dx,dy)
            if length<1e-8:continue
            for t in [.2,.5,.8]:
                x=a[0]+dx*t;y=a[1]+dy*t
                if not (r['x0']-.15+1e-5<x<r['x1']-1e-5 and r['y0']-.20+1e-5<y<r['y1']-1e-5):continue
                xx,yy=-dy/length*1e-6,dx/length*1e-6
                assert abs(height(r,x+xx,y+yy)-height(r,x-xx,y-yy))<1e-4,(x,y)
    # Upper court/south windows remain below the actual roof, including reveals.
    for o in p.openings:
        if o['face']=='south' and abs(o['at']-r['y0'])<1e-5:
            for x in (o['u0']-.24,o['u1']+.24):
                assert height(r,x,r['y0'])>=o['z1']+.21+.06,(o,x,height(r,x,r['y0']))
else:
    assert abs(g['rear_x']-mid)<1e-4
    # Retain T-1833's prior mode contract; a record selecting that historical
    # reconstruction must still get its balanced, level-ridge south gable.
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
# Inspect emitted light geometry against the independent host-roof envelope.
# The reduced cap once ignored the descending crest and floated horizontally.
if g.get('lower_rear_gable'):
    from types import SimpleNamespace
    from _glessner_lod import _ridges
    from archetypes.masonry_house_v4_west_roof import ridge_ranges
    class Capture:
        def __init__(self):self.vertices=[]
        def raw(self,points,*args):self.vertices.extend(points)
    captured=Capture();_ridges(captured,SimpleNamespace(ranges=[r]),None)
    measured=0
    for run,lo,hi in ridge_ranges(r):
        if not run.get('ridge_slope'):continue
        for x,y,h in captured.vertices:
            along,across=(y,x) if run['axis']=='y' else (x,y)
            center=run['ridge_at']+run.get('ridge_skew',0)*(along-run.get('ridge_origin',0))
            if lo<along<hi and abs(across-center)<1e-7:
                clearance=h-height(r,x,y)
                assert min(abs(clearance-v) for v in [.193,.195,.250])<1e-6,(x,y,h,clearance)
                measured+=1
    assert measured>=20,measured
entry=p.detail['north_entry_alcove']
assert entry['east_x']>entry['x'][1]
assert entry['threshold_z']>entry['landing_z']>0
assert any(o.get('style')=='north_entry_alcove' for o in p.openings)
print('PASS: 1800 independent roof rays see one planar envelope; west silhouette, solid south gable, continuous joins, matching court roof and left-turn porch dimensions hold.')
