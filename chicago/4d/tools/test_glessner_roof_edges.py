"""Check actual Glessner stock, roof preservation and the Light ceiling."""
import argparse
from collections import Counter
import json
import math
from pathlib import Path

from _glessner_lod import _construct, _normal, _triangles

ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--baseline',type=Path)
parser.add_argument('--output',type=Path)
args=parser.parse_args()
light,params,_=_construct(ROOT)
full_roofs,_,_=_construct(ROOT,roof_details_reduced=False)
from archetypes.masonry_house_v4_roof_edges import _solid, ridge_chain

class Capture:
    def __init__(self):self.faces=[]
    def raw(self,points,confidence,material):self.faces.append(points)

# Stock must intersect the host ridge at its centre, rather than becoming a
# closed but floating barrel. Exercise both emitted profiles independently of
# the main building and its roof bed.
from types import SimpleNamespace
for reduced in (False,True):
    stock=Capture();stock.reduced_roof_details=reduced
    recipe=SimpleNamespace(detail=params.detail,chimneys=[],turrets=[])
    ridge_chain(stock,recipe,{'axis':'y','ridge_at':0.,'ridge_z':10.},0.,1.)
    floor=min(p[2] for face in stock.faces for p in face)
    crown=max(p[2] for face in stock.faces for p in face)
    assert floor<10.<crown,(reduced,'ridge stock floats above its host',floor)

# A concave flashing section cannot use centroid-based face winding. Its
# signed volume and every edge prove the actual swept stock is closed/outward.
c=Capture();profile=[(0,0),(2,0),(2,1),(1,1),(1,2),(0,2)]
_solid(c,[(x,y,0) for x,y in profile],[(x,y,2) for x,y in profile],4)
edges=Counter();volume=0
for face in c.faces:
    for a,b in zip(face,face[1:]+face[:1]):edges[tuple(sorted((tuple(a),tuple(b))))]+=1
    for a,b,d in _triangles(face,_normal(face)):
        p,q,r=face[a],face[b],face[d]
        cross=(q[1]*r[2]-q[2]*r[1],q[2]*r[0]-q[0]*r[2],q[0]*r[1]-q[1]*r[0])
        volume+=sum(p[i]*cross[i] for i in range(3))/6
assert all(n==2 for n in edges.values())
assert math.isclose(volume,6.,abs_tol=1e-8),volume

triangles=sum(len(_triangles([light.verts[i] for i in f],_normal([light.verts[i] for i in f]))) for f in light.faces)
assert triangles<=200000,triangles
counts=Counter(x['kind'] for x in light.roof_edge_details)
assert counts['finial']==len(params.towers)+len(params.dormers)+len(params.turrets)+int(bool(params.detail.get('west_dormer')))
assert counts['hip']==8*len(params.dormers)
assert counts['eave']>20 and counts['valley']>0 and counts['abutment']>=4*len(params.chimneys)
for item in light.roof_edge_details:
    if item['kind']=='ridge':
        assert item['end']>item['start']
        assert math.isclose(item['spacing_m'],1.16*.3048)
        assert item['crest_width_m']>0 and item['crest_rise_m']>0
        for c in params.chimneys:
            ca,cb=(c['x0'],c['x1']) if item['axis']=='y' else (c['y0'],c['y1'])
            lo,hi=(c['y0'],c['y1']) if item['axis']=='y' else (c['x0'],c['x1'])
            if c['z1']>=item['z']+.025 and ca-.14<item['at']<cb+.14:
                assert item['end']<=lo-.011 or item['start']>=hi+.011
    if item['kind']=='eave':assert math.isclose(item['depth_m'],.06)

def host_key(s):return tuple(sorted(tuple(round(v,6) for v in p) for p in s['points']))
comparison=None
if args.baseline:
    baseline=json.loads(args.baseline.read_text())['surfaces']
    before={host_key(s):s for s in baseline};after={host_key(s):s for s in full_roofs.roof_surfaces}
    assert after.keys()<=before.keys(),'A retained Full roof plane moved or a new slope appeared'
    removed=[before[k] for k in before.keys()-after.keys()]
    # The only removed tile hosts are four hidden duplicate ridge-roll faces
    # and six cone facets on each old dormer finial, now replaced by raw stock.
    assert len(removed)==4+6*len(params.dormers)
    for s in removed:
        centre=[sum(p[k] for p in s['points'])/len(s['points']) for k in range(3)]
        ornament=any(abs(centre[0]-(d['front']+d['back'])/2)<.14
                     and abs(centre[1]-(d['u0']+d['u1'])/2)<.14
                     and d['apex_z']<centre[2]<d['apex_z']+.36 for d in params.dormers)
        old_roll=any(abs(centre[0 if r['axis']=='y' else 1]-r['ridge_at'])<.121
                     and r['ridge_z']<centre[2]<r['ridge_z']+.17
                     for r in params.ranges if not r.get('stable_roof'))
        assert ornament or old_roll,'Removed a real roof plane'
    comparison={'baseline_hosts':len(before),'retained_full_hosts':len(after),
                'retained_hosts_match':True,'removed_hidden_roll_and_finial_hosts':len(removed)}

report={'light_triangles':triangles,'light_ceiling':200000,
        'light_features':dict(counts),'full_features':dict(Counter(d['kind'] for d in full_roofs.roof_edge_details)),
        'full_roof_preservation':comparison,'closed_concave_prism_volume':volume,
        'details':light.roof_edge_details,
        'checks':['Full and Light ridge bases intersect their host','outward and closed concave stock','Light ceiling','finial and hip counts',
                  'physical ridge spacing','chimney termination clearance','eave thickness',
                  'existing Full roof hosts unchanged except replaced ornament']}
if args.output:
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2)+'\n')
print(f'PASS: {triangles:,} Light triangles; {dict(counts)}; roof planes preserved')
