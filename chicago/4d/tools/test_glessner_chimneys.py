"""Check real stack geometry: roof contact, open deep flues and masonry caps."""
import json
import math
from pathlib import Path
from collections import Counter

from _glessner_lod import _geometry_modules, _triangles, _normal

ROOT=Path(__file__).resolve().parents[1]
d,param_module,_=_geometry_modules(ROOT)
from archetypes.masonry_house_v4_chimneys import shaft_faces
record=json.loads((ROOT/'data/structures/glessner_house.json').read_text())
p=param_module.from_phase(record['phases'][0],record)
e=next(r for r in p.ranges if r['name']=='east_wing')
assert {c['name'] for c in p.chimneys}=={'north_gable','middle','south','great','dining_room','service_east','service_west'}


def height_hit(triangle,x,y):
    a,b,c=triangle
    den=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
    if abs(den)<1e-12:return None
    u=((b[1]-c[1])*(x-c[0])+(c[0]-b[0])*(y-c[1]))/den
    v=((c[1]-a[1])*(x-c[0])+(a[0]-c[0])*(y-c[1]))/den
    if min(u,v,1-u-v)<-1e-8:return None
    return u*a[2]+v*b[2]+(1-u-v)*c[2]


for reduced in (False,True):
    for c in p.chimneys:
        b=d.DetailBuilder('stack-check',p);b.reduced_roof_details=reduced
        d.chimney(b,c);r=b.stack_details[0]
        assert set(b.conf)=={p.conf('stack_finish')}=={1.0},'Reconstructed stack finish falsely tagged attested'
        assert not hasattr(b,'course_origin'),'Stack course origin leaked to another component'
        assert b.course_schedule==p.detail['ashlar_courses_m']
        service=c['name'].startswith('service_')
        assert r['body_material']==('brick' if service else 'granite')
        assert math.isclose(r['cap_top']-r['cap_base'],.22 if service else .448)
        triangles=[];seen=Counter()
        for face in b.faces:
            pts=[b.verts[i] for i in face]
            for a,z,q in _triangles(pts,_normal(pts)):
                tri=[pts[i] for i in (a,z,q)]
                cross=d.cross(d.sub(tri[1],tri[0]),d.sub(tri[2],tri[0]))
                assert sum(v*v for v in cross)>1e-18,(c['name'],'zero-area triangle')
                key=tuple(sorted(tuple(round(v,7) for v in pt) for pt in tri));seen[key]+=1
                triangles.append(tri)
        assert max(seen.values())==1,(c['name'],'coincident triangles')
        # Triangles entirely below the flue floor cannot be the required top
        # hit. Filter them once, preserving the same ray-intersection verdict.
        cap_triangles=[t for t in triangles if max(v[2] for v in t)>=r['floor']-1e-7]
        for h in r['holes']:
            x=sum(v[0] for v in h)/4;y=sum(v[1] for v in h)/4
            hits=[z for t in cap_triangles if (z:=height_hit(t,x,y)) is not None]
            assert hits and abs(max(hits)-r['floor'])<1e-7,(c['name'],'flue mouth sealed or shallow')
            assert c['z1']-max(hits)>.5,'A flue must have actual masonry depth'
        # A cap stone beside the first corner reaches the preserved top, with
        # only the declared shallow drainage fall; no projecting slab or pot.
        x=c['x0']+.025;y=c['y0']+.025
        hits=[z for t in cap_triangles if (z:=height_hit(t,x,y)) is not None]
        want=c['z1']-.012*(y-c['y0'])/(c['y1']-c['y0'])
        assert hits and abs(max(hits)-want)<1e-7,(c['name'],'cap lacks solid masonry')
        assert max(v[2] for v in b.verts)<=c['z1']+1e-7,'Cap exceeded the retained stack top'
        if c['name'] in ('middle','south'):
            assert c['x0']<e['ridge_at']<c['x1'],'Stack fails to straddle the main ridge'
            faces=list(shaft_faces(p,c,r['cap_base']-.229))
            assert len(faces)==6,'Cross-ridge faces were not split'
            for face in faces:
                for x,y,z in face[:2]:
                    # The retained roof has two independent eave controls.
                    end,ez=(e['x0'],e['eave_lo_z']) if x<e['ridge_at'] else (e['x1'],e['eave_hi_z'])
                    roof=e['ridge_z']+(x-e['ridge_at'])*(ez-e['ridge_z'])/(end-e['ridge_at'])
                    assert abs(roof-z-.06)<1e-7,(c['name'],'shaft floats off host roof')
                    assert c['z0']<=z,'Buried base prevents reverse-pitch flashing'
            # No single face bridges a high ridge with a lower chord.
            assert all(not(min(v[0] for v in face)<e['ridge_at']<max(v[0] for v in face)) for face in faces)
print('PASS: seven retained stacks, two roof pitches, jointed masonry caps and open deep flues in Full/Light')
