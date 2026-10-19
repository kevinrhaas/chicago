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

# Owner's overhead return: one roof surface at each sampled plan point, with
# replacement copper exactly on the original slope. A raised rectangle or an
# uncut tile layer fails independently of the producer's subdivision choices.
from archetypes.masonry_house_v4_copper import north_cladding, add_north_cladding
from archetypes.masonry_house_v4_courtyard_roof import clip_host
from _glessner_lod import _geometry_modules
d,_,_=_geometry_modules(ROOT)
return_faces = north_cladding(p)
assert return_faces
for face in return_faces:
    assert area(face)>1e-8
    assert all(abs(h-north_height(y))<1e-8 for x,y,h in face), 'floating copper return'
host = [(x,y,north_height(y)) for x,y in
        [(31,13),(n['x1'],13),(n['x1'],18.1),(31,18.1)]]
tiles = clip_host(host,p)
assert any(contains(face,33,16) for face in return_faces), 'west copper extent omitted'
assert not any(contains(face,33,18) for face in return_faces), 'return reached the ridge'
rng=random.Random(102228)
for i in range(2000):
    x,y=rng.uniform(31,n['x1']),rng.uniform(13,18.1)
    copper_hits=sum(contains(face,x,y) for face in return_faces)
    hood_hits=sum(contains(face,x,y) for face in faces)
    tile_hits=sum(contains(face,x,y) for face in tiles)
    assert copper_hits+hood_hits+tile_hits==1, ('copper return hole/overlap',x,y,copper_hits,hood_hits,tile_hits)
for reduced in (False,True):
    emitted=Capture(reduced);add_north_cladding(emitted,p)
    assert emitted.verts
    for x,y,h in emitted.verts:
        assert -.013<h-north_height(y)<.018, ('unseated return stock',reduced,x,y,h)
    assert all(math.isfinite(v) for pair in emitted.roof_uvs.values() for v in pair)
print('PASS: 2000 independent copper-return rays; no overlapping tiles/hood, no lifted sheet; Full/Light stock seated on host')

# T-2228: the three dormers replace only enclosed host roof below their roofs.
# An independent analytic height field probes emitted host fragments, including
# the rear valley and the intact roof under the overhanging soffit.
from archetypes.masonry_house_v4_court import dormer_host,dormer_roof,above_host,court_finial
from archetypes.masonry_house_v4_detail import area as signed_area

def inside_face(poly,x,y):
    sign=1 if signed_area(poly)>0 else -1
    return all(sign*((q[0]-v[0])*(y-v[1])-(q[1]-v[1])*(x-v[0]))>=-1e-9
               for v,q in zip(poly,poly[1:]+poly[:1]))

probe_count=0
for dm in p.dormers:
    f,bk=dm['front'],dm['back'];a,c=dm['u0'],dm['u1']
    xa,xb=f-.30,bk+.10;ya,yb=a-.144,c+.144
    cx,cy=(f+bk)/2,(a+c)/2;ze,za=dm['eave_z'],dm['apex_z']
    # Apex is centred on BODY, not on the asymmetric overhang.
    def envelope(x,y):
        if not xa<=x<=xb or not ya<=y<=yb:return -math.inf
        if xa+.18<=x<=xb-.18 and ya+.085<=y<=yb-.085:
            fraction=max((cx-x)/(cx-xa-.18),(x-cx)/(xb-.18-cx),
                         (cy-y)/(cy-ya-.085),(y-cy)/(yb-.085-cy))
            return za-(za-ze-.13)*fraction
        return ze+.13*min((x-xa)/.18,(xb-x)/.18,(y-ya)/.085,(yb-y)/.085)
    host=[(x,y,east_height(x)) for x,y in ((xa-.1,ya-.1),(xb+.1,ya-.1),(xb+.1,yb+.1),(xa-.1,yb+.1))]
    kept=dormer_host(host,p)
    rng=random.Random(2228)
    for i in range(500):
        x=rng.uniform(xa-.1,xb+.1);y=rng.uniform(ya-.1,yb+.1)
        removed=f<x<bk and a<y<c and east_height(x)<envelope(x,y)
        hits=sum(inside_face(face,x,y) for face in kept)
        assert hits==int(not removed),('dormer roof hole/overlap',x,y,hits,removed)
        probe_count+=1
    # Roof behind the glazing is absent throughout its width and rear recess.
    for depth in (.20,.35,.55):
        x=f+depth
        for fraction in (.25,.5,.75):
            y=a+(c-a)*fraction
            assert not any(inside_face(face,x,y) for face in kept),('roof blocks dormer glass',depth,fraction)
    for face in dormer_roof(dm)[3]:
        exposed=above_host(face,p)
        assert all(v[2]>=east_height(v[0])-1e-8 for v in exposed)
    assert abs(dm['light'][0]/.3048-30.63)<.005
    assert abs(dm['light'][1]/.3048-32.87)<.005
    assert abs((c-a)*(1-2*dm['light_margin_fraction'])/.3048-2.94)<.02
    ring,kick,apex,_=dormer_roof(dm)
    # Native HABS4 roof width540px at100.6px/ft, read independently of stock.
    span=max(v[1] for v in ring)-min(v[1] for v in ring)
    assert abs(span-540/100.6*.3048)<.03,('section dormer roof width',span)
    lower_slope=(kick[0][2]-ring[0][2])/(kick[0][1]-ring[0][1])
    upper_slope=(apex[2]-kick[0][2])/(apex[1]-kick[0][1])
    assert 0<lower_slope<upper_slope,('reversed dormer flare',lower_slope,upper_slope)
assert abs(east_height(e['x0']-.20)/.3048-27.33)<.015
for reduced in (False,True):
    b=d.DetailBuilder('court-finial',p);b.reduced_sash=reduced
    court_finial(b,0,0,'dormer',3)
    # T-2859: the dormer bell is re-read on native HABS4 at its own grain - foot 37.03,
    # cap top 38.80-38.90 ft (was 36.99/38.83) - and carries its own drawn profile.
    assert abs(max(v[2] for v in b.verts)/.3048-38.90)<1e-7
    assert all(math.isfinite(v) for pt in b.verts for v in pt)
print('PASS:',probe_count,'independent dormer host samples, clear glazing, section eave and Full/Light bell silhouette')
