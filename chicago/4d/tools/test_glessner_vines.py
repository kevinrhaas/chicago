"""Exercise vine clearance, support, connected stems and the actual reduced mesh."""
import copy
import json
import math
from pathlib import Path
from _glessner_lod import _geometry_modules,_triangles,_normal

ROOT=Path(__file__).resolve().parents[1]
d,pm,_=_geometry_modules(ROOT)
from archetypes.masonry_house_v4_vines import make_layout,add_vines,frame
r=json.loads((ROOT/'data/structures/glessner_house.json').read_text())
p=pm.from_phase(r['phases'][0],r);layout=make_layout(p,p.detail['vines'])


def fixture():
    b=d.DetailBuilder('vine-contact-fixture',p)
    for plant in layout:
        axis,along,sign=frame(plant);normal=tuple(sign if k==axis else 0 for k in range(3))
        lo,z0,hi,z1=plant['bounds']
        def plane(rect,depth):
            a,c,e,f=rect;points=[]
            for u,z in [(a,c),(e,c),(e,f),(a,f)]:
                q=[0,0,z];q[axis]=plant['at']+sign*depth;q[along]=u;points.append(q)
            b.raw(points,1.,0,normal)
        plane((lo-.1,z0-.1,hi+.1,z1+.1),0)
        if plant['id']=='front-south':
            plane((plant['root_u']-.15,.5,plant['root_u']+.15,1.5),.06)
        if plant['id']=='west-court':
            # Sub-mm relief changes used to create overlapping compound petioles.
            for ix in range(math.ceil((hi-lo)/.1)):
                for iz in range(math.ceil((z1-z0)/.1)):
                    a,c=lo+ix*.1,z0+iz*.1;points=[]
                    for u,z in [(a,c),(a+.1,c),(a+.1,c+.1),(a,c+.1)]:
                        q=[0,0,z];q[axis]=plant['at']+sign*(.01+.0003*(u-lo));q[along]=u;points.append(q)
                    b.raw(points,1.,0,normal)
    return b


# Every branch and leaf attachment can be reached from the buried root.
for plant in layout:
    reached={(plant['root_u'],plant['root_z']-.025)}
    for branch in plant['branches']:
        assert branch['a'] in reached,('Detached stem',plant['id'],branch)
        reached.add(branch['b'])
    assert all(leaf['base'] in reached for leaf in plant['leaves'])

b=fixture();start=len(b.faces);result=add_vines(b,p)
seen=set();grid_seen=set();triangles=0
for face,mat in zip(b.faces[start:],b.mat_index[start:]):
    points=[b.verts[i] for i in face]
    assert all(b.conf[i]==1 for i in face),'Plant confidence is not reconstructed'
    for inds in _triangles(points,_normal(points)):
        tri=[points[i] for i in inds];triangles+=1
        assert sum(x*x for x in d.cross(d.sub(tri[1],tri[0]),d.sub(tri[2],tri[0])))>1e-20,'Degenerate vine triangle'
        key=tuple(sorted(tuple(round(v,9) for v in q) for q in tri))
        assert key not in seen,'Coincident vine faces';seen.add(key)
        # Match K01: distinct raw faces may still coincide on its 1 mm grid.
        grid=tuple(sorted(tuple(math.floor(v*1000+.5) for v in q) for q in tri))
        if len(set(grid))==3:
            assert grid not in grid_seen,'Coincident vine faces on K01 1 mm grid'
            grid_seen.add(grid)
    if mat==29:
        # UV seams may duplicate vertices, but a curled leaf's fan cannot split
        # into separately shaded triangular facets in the Full export.
        assert all(i in b.rock_normals for i in face),'Full leaf lacks explicit smooth corner normals'
        assert all(abs(sum(v*v for v in b.rock_normals[i])-1)<1e-8 for i in face),'Invalid leaf normal'
        # Check actual emitted leaf triangles with the existing wall clipper.
        for plant in layout:
            axis,along,sign=frame(plant)
            if not all(0<sign*(q[axis]-plant['at'])<.25 for q in points):continue
            coords=[(q[along],q[2]) for q in points]
            if not all(plant['bounds'][0]-.01<=u<=plant['bounds'][2]+.01 for u,z in coords):continue
            for opening in p.openings:
                if opening['face']!=plant['face'] or abs(opening['at']-plant['at'])>.01 or opening['kind']=='band':continue
                clipped=d.rect_clip(coords,opening['u0']-.22,opening['z0']-.22,opening['u1']+.22,opening['z1']+.22)
                area=abs(sum(a[0]*c[1]-c[0]*a[1] for a,c in zip(clipped,clipped[1:]+clipped[:1])))/2 if clipped else 0
                assert area<1e-10,('Leaf crosses an opening surround',plant['id'])
            if plant['id']=='front-south':
                for q in points:
                    if abs(q[along]-plant['root_u'])<.15 and .5<q[2]<1.5:
                        assert sign*(q[axis]-plant['at'])>.081,'Leaf intersects raised masonry'
assert triangles<80000,triangles

light=fixture();start=len(light.faces);reduced=add_vines(light,p,reduced=True)
assert sum(len(f)-2 for f in light.faces[start:])==56
at_uv={}
for face in light.faces[start:]:
    for index in face:
        uv=tuple(round(v,10) for v in light.roof_uvs[index]);point=tuple(round(v,10) for v in light.verts[index])
        assert uv not in at_uv or at_uv[uv]==point,'Light atlas has a split panel seam'
        at_uv[uv]=point
assert [(s['id'],s['leaves']) for s in result['plants']]==[(s['id'],s['leaves']) for s in reduced['plants']]
legacy=copy.deepcopy(p);legacy.detail.pop('vines')
assert add_vines(light,legacy)['added_faces']==0,'Earlier house versions gained planting'
print(f'PASS: connected roots/stems, clear openings, raised-wall support, no duplicate/degenerate faces; Full {triangles}, Light 56 added triangles')
