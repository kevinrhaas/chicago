"""Hold geometry/contact parity while plain joints and member UVs change."""
import copy
import json
import math
from pathlib import Path
from _glessner_lod import _geometry_modules

ROOT=Path(__file__).resolve().parents[1]
d,pm,materials=_geometry_modules(ROOT)
from archetypes import masonry_house_v4_service as service
from archetypes.masonry_house_v4_finish import FLAT_BRICK,validate,grain_members,maps
r=json.loads((ROOT/'data/structures/glessner_house.json').read_text())
p=pm.from_phase(r['phases'][0],r);validate(p.detail['surface_finish'])
legacy=copy.deepcopy(p);legacy.detail.pop('surface_finish')


def fixture(params,reduced):
    b=d.DetailBuilder('finish-contact-fixture',params);b.reduced_service_access=reduced
    service.build_stair(b,params)
    for w in params.walls:
        b.decorate=not (reduced and 'ends' in w)
        d.gate_piece(b,w)
    # The reduced service/boundary pieces are all plain by design. Include an
    # ordinary coursed wall too, so this fixture can detect double-gridding it.
    b.decorate=True
    b.wall([(0,0,0),(1,0,0),(1,0,1),(0,0,1)],1.0,d.BRICK)
    return b


for reduced in (False,True):
    old=fixture(legacy,reduced);new=fixture(p,reduced)
    assert old.verts==new.verts and old.faces==new.faces,'A surface change moved geometry or contacts'
    assert old.conf==new.conf,'Surface finish falsely changed historical confidence'
    assert old.service_posts==new.service_posts and old.service_piers==new.service_piers
    assert old.service_gate==new.service_gate and old.service_rails==new.service_rails
    changes=[(a,b) for a,b in zip(old.mat_index,new.mat_index) if a!=b]
    assert changes and set(changes)=={(d.BRICK,FLAT_BRICK)},'Unexpected material retint'
    assert d.BRICK in new.mat_index and d.MORTAR in new.mat_index,'Modeled bricks lost their separate joints'
    assert FLAT_BRICK not in old.mat_index,'Earlier profile acquired a new surface'
    assert new.wood_grain_members
    changed=set(new.roof_uvs)-set(old.roof_uvs)
    wanted={i for m in new.wood_grain_members for i in m['indices']}
    assert changed==wanted,'Member UV change leaked beyond gate timber'
    assert all(new.roof_uvs[i]==uv for i,uv in old.roof_uvs.items()),'Existing metric UVs changed'
    assert any(m['end'] for m in new.wood_grain_members),'Cut-end basis was not exercised'
    for m in new.wood_grain_members:
        face=m['indices'];uv=[new.roof_uvs[i] for i in face]
        area=abs(sum(a[0]*z[1]-z[0]*a[1] for a,z in zip(uv,uv[1:]+uv[:1])))/2
        assert area>1e-9,'Collapsed grain on an end or side face'
        for i,j in zip(face,face[1:]+face[:1]):
            physical=math.sqrt(sum((new.verts[j][k]-new.verts[i][k])**2 for k in range(3)))
            mapped=math.dist(new.roof_uvs[i],new.roof_uvs[j])
            assert abs(physical-mapped)<1e-8,'Grain stretches per member rather than using metres'
        if not m['end']:
            assert d.dot(m['axis'],m['v'])>1-1e-8,'Grain crosses the timber axis'
            assert abs(d.dot(m['axis'],m['u']))<1e-8
    assert not hasattr(old,'wood_grain_members')

# A joint map must be deterministic and encode recess direction in OpenGL +V.
import numpy as np
images=maps(ROOT/'assets/textures/glessner-v4',p.detail['surface_finish'])
again=maps(ROOT/'assets/textures/glessner-v4',p.detail['surface_finish'])
assert all(a.tobytes()==again[k].tobytes() for k,a in images.items())
normal=np.asarray(images['normal'],float)/255*2-1
assert np.max(np.abs(np.linalg.norm(normal,axis=-1)-1))<.007,'Invalid tangent normals'
assert np.min(normal[...,2])>0,'Inverted brick surface normals'
# Near the tile bottom, increasing world +V climbs from joint to brick.
# The surface normal must point toward -V there, not flip into a groove crown.
centre=1024//16
assert normal[-4,centre,1]<-.25,'Brick joint has the wrong vertical normal convention'
assert materials.TILE_M['flat_brick']==materials.TILE_M['brick'],'Joint repeat changed physical brick scale'
assert materials.SLOT_FABRIC[FLAT_BRICK]=='flat_brick'
print('PASS: Full/Light geometry and contacts identical; only plain brick roles change; gate grain follows timber at metric scale with valid ends; deterministic joint maps and +V normals')
