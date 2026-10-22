"""Spatial checks for connected drainage, unobstructed openings and open stock."""
import json
import math
import copy
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'generators'))
from archetypes.masonry_house_params import from_phase
from archetypes.masonry_house_v4_drainage import layout, build, _gutter

record=json.loads((ROOT/'data/structures/glessner_house.json').read_text())
p=from_phase(record['phases'][0],record)
cfg=p.detail['rainwater']

# Rainwater details remain optional: older v4 records use the legacy builder.
# Explicit courtyard anchors must not make parameter resolution require them.
without_rainwater=copy.deepcopy(record['phases'][0])
without_rainwater['form'].pop('rainwater_details')
assert from_phase(without_rainwater,record).detail['rainwater'] is None


def distance_to_segment(q,a,c):
    d=tuple(c[k]-a[k] for k in range(3))
    t=max(0,min(1,sum((q[k]-a[k])*d[k] for k in range(3))/sum(v*v for v in d)))
    return math.dist(q,tuple(a[k]+t*d[k] for k in range(3)))


class Capture:
    def __init__(self,reduced):self.reduced_roof_details=reduced;self.faces=[]
    def raw(self,pts,confidence,material,want):
        assert confidence==p.conf('rainwater_details')==1.0 and material==28
        assert len(pts)>=3 and all(math.isfinite(v) for q in pts for v in q)
        self.faces.append((pts,want))


for reduced in (False,True):
    net=layout(p,reduced)
    leaders={r['name']:r for r in net['leaders']}
    branches={r['name']:r for r in net['branches']}
    # T-2928: a gutter that runs on into the bow's trough has no leader of its own.
    fed=len(cfg.get('court_east_into_bow',()))
    assert len(leaders)==12-fed and len(net['gutters'])==12
    assert leaders['prairie-north']['head']==leaders['prairie-south']['head']=='panel'
    assert leaders['north-tower']['head']=='bowl' and leaders['north-service']['head']=='plain'
    assert leaders['alley-north']['normal']==(0,1,0),'Alley corner leader belongs on the north face'
    for row in net['leaders']+net['branches']:
        assert all(a[2]>=c[2] for a,c in zip(row['path'],row['path'][1:])),(row['name'],'uphill drainage')
    for row in net['gutters']:
        assert row['drains'] or row.get('branch') or row.get('feeds'),(row['name'],'no outlet')
        if row.get('feeds'):
            # It ends against the trough it feeds, level with that trough's floor: no gutter here is
            # modelled with a fall, and sheet 4 draws both feet at about 27.0 ft.
            target=next(r for r in net['gutters'] if r['name']==row['feeds'])
            tip=row['edge'][-1]
            reach=min(math.dist(tip[:2],q[:2]) for q in target['edge'])
            floor=min(q[2] for q in target['edge'])-target.get('section',{}).get('depth_m',cfg['gutter_depth_m'])
            assert reach<.10 and abs(tip[2]-cfg['gutter_depth_m']-floor)<.03,(row['name'],'does not reach its trough',reach)
        destinations=[leaders[k]['inlet'] for k in row['drains']]
        if row.get('branch'):
            q=branches[row['branch']]['path'][0]
            destinations.append((q[0],q[1],q[2]+cfg['gutter_depth_m']+.012))
        for q in destinations:
            # Outlet centre is inside a 180 mm trough or its end receiver;
            # branch start is lowered exactly to its floor, not left in air.
            gap=min(distance_to_segment(q,a,c) for a,c in zip(row['edge'],row['edge'][1:]))
            assert gap<.095,(row['name'],'outlet misses its gutter',gap)
    for row in branches.values():
        target=leaders[row['target']];q=row['path'][-1]
        if target['head']!='none':
            assert math.dist(q[:2],target['inlet'][:2])<.001
            assert target['mouth']-cfg['heads'][target['head']]['height_m']<q[2]<target['mouth']
        else:
            assert min(distance_to_segment(q,a,c) for a,c in zip(target['path'],target['path'][1:]))<.001
    # T-2861: a trough with its own section (the bow's, off sheet 4) keeps its own floor.
    trough={k:r.get('section',{}) for r in net['gutters'] for k in r['drains']}
    if cfg.get('bow_leader'):
        # T-2939: sheet 4 draws the court-bow leader side-on: its back on the north range's court
        # face, 0.10 m deep, under a head hung from the trough's floor, and neither in the bow.
        row=leaders['court-bow'];h=row['hopper'];north=next(r for r in p.ranges if r['name']=='north_range')['y0']
        bow=next(t for t in p.bows if t['name']=='hall_bow')
        assert row['normal']==(0,-1,0) and abs(row['mount'][1]+row['depth_m']/2-north)<.005
        assert abs(h['centre'][2]-row['mouth'])<1e-9 and h['neck']==row['depth_m']
        for y in (north-h['depth'],row['mount'][1]-row['depth_m']/2):
            assert h['centre'][0]+h['width']/2<bow['cx']-math.sqrt(bow['r']**2-(y-bow['cy'])**2),'court-bow head in the bow'
    for row in leaders.values():
        assert row['spout'][0][2]>row['spout'][1][2]
        floor=row['inlet'][2]-trough.get(row['name'],{}).get('depth_m',cfg['gutter_depth_m'])-.012
        if trough.get(row['name']):
            # The outlet stands wholly inside the trough, between its back and its face.
            u=math.dist(row['inlet'][:2],next(r for r in net['gutters'] if row['name'] in r['drains'])['edge'][0][:2])
            reach=row.get('depth_m',row.get('width_m',cfg['pipe_width_m']))/2
            assert -.035<u-reach and u+reach<trough[row['name']]['width_m']-.035,(row['name'],'outlet overhangs its trough')
        assert row['spout'][0][2]>floor>row['spout'][1][2]
        assert row['path'][-1][2]<=.07,(row['name'],'floating discharge')
        if isinstance(row['wall'],dict):continue
        nx,ny,_=row['normal'];face=('east' if nx>0 else 'west') if nx else ('north' if ny>0 else 'south')
        assert distance_to_segment(row['spout'][-1],row['path'][0],row['path'][1])<.001 or row['head']!='none'
        x,y,top=row['mount'];u=y if nx else x
        half=row.get('width_m',cfg['pipe_width_m'])/2+.008
        strap_span=row.get('strap_span_m',.17)/2+.014
        strap_height=row.get('strap_height_m',.05)/2
        strap_z=row.get('strap_z_m',[.18+(top-.18)*f for f in row.get('strap_fractions',(.18,.48,.78))])
        assert all(.07<z<top for z in strap_z),(row['name'],'strap outside straight wall run')
        for opening in p.openings:
            if opening['face']!=face or abs(opening['at']-row['wall'])>.01:continue
            # T-2926: a stone course is wall, not a hole in it; sheet 4 runs the south court
            # leader down over the underpass's lintel course.
            if opening.get('style')=='rough_course':continue
            overlaps=opening['u0']-half<u<opening['u1']+half and opening['z0']<top and opening['z1']>0
            assert not overlaps,(row['name'],'leader crosses opening',opening)
            for z in strap_z:
                overlaps=(opening['u0']-strap_span<u<opening['u1']+strap_span and
                          opening['z0']-strap_height<z<opening['z1']+strap_height)
                assert not overlaps,(row['name'],'wall strap crosses opening',opening)
    emitted=Capture(reduced);build(emitted,p)
    # Every floor opening remains a real hole in both Full and Light. Check a
    # simple straight trough independent of the building's placement details.
    stock=Capture(reduced)
    _gutter(stock,{'edge':[(0,0,2),(2,0,2)],'normals':[(0,-1,0)]*2,'open_ends':[]},
            cfg,[{'point':(1,-.045,2),'normal':(0,-1,0)}])
    def contains(poly,x,y):
        signs=[(c[0]-a[0])*(y-a[1])-(c[1]-a[1])*(x-a[0]) for a,c in zip(poly,poly[1:]+poly[:1])]
        return all(v>=-1e-10 for v in signs) or all(v<=1e-10 for v in signs)
    floors=[pts for pts,want in stock.faces if abs(want[2])>.1 and max(q[2] for q in pts)-min(q[2] for q in pts)<1e-7
            and abs(pts[0][2]-(2-cfg['gutter_depth_m']-.012))<.004]
    assert floors
    assert not any(contains(f,1,-.045) for f in floors),'Sealed gutter floor above outlet'
    assert any(contains(f,.5,-.045) for f in floors),'Missing gutter floor away from outlet'
    print(f'PASS {"Light" if reduced else "Full"}: 12 collectors, {len(leaders)} leaders, 2 descending connections; openings clear; open gutter stock ({sum(len(f)-2 for f,_ in emitted.faces)} nominal triangles)')
