"""Check generated service-access contacts, closed rails and usable gate joints."""
import json
from collections import Counter
from pathlib import Path
from _glessner_lod import _geometry_modules, _triangles, _normal

ROOT=Path(__file__).resolve().parents[1]
d,pm,_=_geometry_modules(ROOT)
from archetypes import masonry_house_v4_service as service
r=json.loads((ROOT/'data/structures/glessner_house.json').read_text())
p=pm.from_phase(r['phases'][0],r)


def triangles(b,material=None):
    for f,m in zip(b.faces,b.mat_index):
        if material is not None and m not in material:continue
        pts=[b.verts[i] for i in f]
        for indices in _triangles(pts,_normal(pts)):
            yield [pts[i] for i in indices]


def hit(t,a,b,axis=2):
    axes=[i for i in range(3) if i!=axis];i,j=axes
    q,s,v=t
    den=(s[j]-v[j])*(q[i]-v[i])+(v[i]-s[i])*(q[j]-v[j])
    if abs(den)<1e-12:return None
    u=((s[j]-v[j])*(a-v[i])+(v[i]-s[i])*(b-v[j]))/den
    w=((v[j]-q[j])*(a-v[i])+(q[i]-v[i])*(b-v[j]))/den
    if min(u,w,1-u-w)<-1e-8:return None
    return u*q[axis]+w*s[axis]+(1-u-w)*v[axis]


def hits(ts,a,b,axis=2):
    return sorted({round(h,8) for t in ts if (h:=hit(t,a,b,axis)) is not None})


for reduced in (False,True):
    b=d.DetailBuilder('service-test',p);b.reduced_service_access=reduced
    original=service._rail;bars=[]
    def capture(builder,*args):
        first=len(builder.faces);original(builder,*args)
        bars.append([[builder.verts[i] for i in f] for f in builder.faces[first:]])
    service._rail=capture
    try:service.build_stair(b,p)
    finally:service._rail=original
    assert set(b.conf)=={1.0},'Reconstruction falsely marked attested'
    stone=list(triangles(b,{d.TRIM}))
    assert len(b.service_posts)==10
    assert len({(q['x'],q['y']) for q in b.service_posts})==10
    for q in b.service_posts:
        # All four plate corners must rest on real stone, not a smooth slope.
        h=q['foot_width']/2-.0001
        for dx,dy in ((-h,-h),(h,-h),(h,h),(-h,h)):
            seats=hits(stone,q['x']+dx,q['y']+dy)
            assert any(abs(z-q['seat'])<1e-7 for z in seats),(q,'unsupported footplate',seats)
    for faces in bars:
        edges=Counter()
        for face in faces:
            pts=[tuple(round(v,8) for v in pt) for pt in face]
            for a,z in zip(pts,pts[1:]+pts[:1]):edges[tuple(sorted((a,z)))]+=1
            assert sum(v*v for v in d.cross(d.sub(face[1],face[0]),d.sub(face[2],face[0])))>1e-15
        assert set(edges.values())=={2},'Open or doubled rail junction'
    stair=p.detail['north_court_service_stair'];spec=p.detail['service_access']['stair']
    side=list(triangles(b,{d.BRICK,d.MORTAR,16,17,18}))
    run=(stair['flight_y'][1]-stair['flight_y'][0])/stair['steps']
    rise=stair['landing_z']/stair['steps']
    for i in range(stair['steps']):
        y=stair['flight_y'][0]+(i+.5)*run;top=rise*(i+1)
        assert hits(side,y,top-spec['nosing_height_m']-.008,0),'Missing stepped cheek below tread'
        assert not hits(side,y,top-spec['nosing_height_m']+.008,0),'Cheek crosses stone nosing'
        underside=hits(stone,stair['flight_x'][0]-spec['nosing_side_m']/2,y)
        assert len(underside)==2 and abs(underside[1]-underside[0]-spec['nosing_height_m'])<1e-7,'Open tread overhang'
    assert len(bars)==6,'Two lower rails and a handrail on each exposed side'
    g=d.DetailBuilder('gate-test',p);g.reduced_service_access=reduced
    original_block=g.block;original_decorate=g.decorate
    for w in p.walls:d.gate_piece(g,w)
    assert g.block==original_block and g.decorate==original_decorate,'Gate changes leaked builder state'
    assert len(g.service_jambs)==2 and len(g.service_gate['hinges'])==4
    wood=list(triangles(g,{d.WOOD}));iron=list(triangles(g,{d.IRON}))
    from archetypes.masonry_house_v4_landscape import _inside
    leaves=g.service_gate['leaves']
    gate_wall=next(w for w in p.walls if w.get('kind')=='gate')
    centre=(gate_wall['at']+.001,(leaves[0]['lo']+leaves[-1]['hi'])/2)
    ground=max(q['lift_m'] for q in p.ground if _inside(centre,q['pts']))
    assert ground<g.service_gate['threshold_top']<ground+.015,'Sill buried in drive or excessive step'
    assert min(q['bottom'] for q in leaves)>g.service_gate['threshold_top'],'Gate cuts its threshold'
    middle=(leaves[0]['hi']+leaves[1]['lo'])/2
    assert not hits(wood,middle,1.6,0),'Gate meeting joint sealed by old panel'
    for leaf in leaves:
        xx=hits(wood,(leaf['lo']+leaf['hi'])/2,1.6,0)
        assert xx and max(xx)-min(xx)>=.039-1e-7,'Gate lacks solid boarded leaf'
    masonry=list(triangles(g,{d.GRANITE,d.MORTAR,*range(12,16)}))
    sill=hits(masonry,*centre)
    assert sill and abs(max(sill)-g.service_gate['threshold_top'])<1e-7,'Generated sill misses its declared top'
    for h in g.service_gate['hinges']:
        x,y,z=h['axis']
        timber=hits(wood,y,z,0);metal=hits(iron,y,z,0)
        assert timber and metal and max(metal)>max(timber)+.02,'Hinge pin is hidden behind its timber ledge'
        assert x-h['radius']>=max(timber)-1e-7,'Hinge barrel intersects solid timber'
        x+=.03
        plates=hits(iron,x,z,1);jambs=hits(masonry,x,z,1)
        assert any(abs(j-h['jamb'])<.013 for j in jambs),'No masonry reveal behind hinge'
        assert any(a<j<q for a,q in zip(plates,plates[1:]) for j in jambs if abs(j-h['jamb'])<.013),'Hinge plate does not meet actual masonry surface'
    latch=g.service_gate['latch']
    crossing=hits(iron,latch['keeper_y'],latch['height'],0)
    # The latch back is seated on timber; its front and both keeper faces
    # bound a genuinely open slot.
    assert len(crossing)==3 and crossing[1]-crossing[0]>.004,'Latch buried in a solid keeper'
    # Preserve the existing package contract's masonry datum while allowing
    # the separate stone stair footings to enter grade.
    tolerance=json.loads((ROOT/'data/components/prairie_1904/k01_contract.json').read_text())['measures']['base_tolerance_m']
    for builder in (b,g):
        walls=list(triangles(builder,{d.GRANITE,d.BRICK,*range(12,19)}))
        assert min(pt[2] for tri in walls for pt in tri)>=-tolerance,'Masonry base exceeds the package datum bound'
print('PASS: Full/Light service posts seated, six closed joined rails, paired boarded gate and four masonry-mounted hinges')
