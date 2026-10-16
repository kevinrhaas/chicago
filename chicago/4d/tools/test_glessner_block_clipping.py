#!/usr/bin/env python3
"""The arch cuts stones; its convex partitions must not invent stone joints.

    python3 tools/test_glessner_block_clipping.py

Exercise the real v4 block/wall methods with a recording builder. Blender is
stubbed only at the unused object-emission boundary. No meshes or maps are read
or changed. Heights/colours outside an aperture must match the original stone;
inside it there must be no faces, including bevels. This reproduces the radial
false-joint defect exposed by the entry's 80-segment semicircular recess.
"""
from __future__ import annotations

import argparse
import importlib.util
import math
from pathlib import Path
import random
import sys
from types import ModuleType, SimpleNamespace
from unittest.mock import patch

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--self-test', action='store_true', help='run the clipping fixtures (also the default)')
parser.parse_args()

ROOT=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/'generators'))
mesh=ModuleType('common.mesh')
mesh.MeshBuilder=object
legacy=ModuleType('archetypes.masonry_house')


def normal(pts):
    a,b,c=pts[:3]
    u=[b[i]-a[i] for i in range(3)];v=[c[i]-a[i] for i in range(3)]
    return (u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0])


legacy._normal=normal
legacy._plane_point=lambda o,u,z,off=0: ((o['at']+o['sign']*off,u,z)
    if o['axis']=='x' else (u,o['at']+o['sign']*off,z))
legacy._plane_dir=lambda o: ((o['sign'],0,0) if o['axis']=='x' else (0,o['sign'],0))
spec=importlib.util.spec_from_file_location('_glessner_clipping',
    ROOT/'generators/archetypes/masonry_house_v4_detail.py')
detail=importlib.util.module_from_spec(spec)
with patch.dict(sys.modules,{'common.mesh':mesh,'archetypes.masonry_house':legacy}):
    spec.loader.exec_module(detail)


class Recorder(detail.DetailBuilder):
    def __init__(self):
        self.params=SimpleNamespace(detail={'ashlar_relief_m':[.025,.070]})
        self.masonry_blocks=0
        self.recorded=[]

    def raw(self, pts, confidence, mat, want=None):
        self.recorded.append((list(pts),mat))

    def raw_with_normals(self, pts, normals, confidence, mat, want=None):
        self.raw(pts,confidence,mat,want)


def point_depth(faces,x,y):
    """Independent barycentric read of the emitted physical surface."""
    found=[]
    for poly,mat in faces:
        for i in range(1,len(poly)-1):
            a,b,c=poly[0],poly[i],poly[i+1]
            det=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
            if abs(det)<1e-13:
                continue
            aa=((b[1]-c[1])*(x-c[0])+(c[0]-b[0])*(y-c[1]))/det
            bb=((c[1]-a[1])*(x-c[0])+(a[0]-c[0])*(y-c[1]))/det
            cc=1-aa-bb
            if min(aa,bb,cc)>-1e-9:
                found.append((aa*a[2]+bb*b[2]+cc*c[2],mat))
    return found


def in_hole(x,y,hole):
    return all((b[0]-a[0])*(y-a[1])-(b[1]-a[1])*(x-a[0])>1e-8
               for a,b in zip(hole,hole[1:]+hole[:1]))


def check_stone(material):
    polygon=[(-1,0),(1,0),(1,1),(-1,1)]
    arch=[(.72*math.cos(math.pi*i/80),.72*math.sin(math.pi*i/80))
          for i in range(81)]
    # A second aperture exercises repeated cuts of the same finished surface.
    rectangle=[(.80,.72),(.94,.72),(.94,.91),(.80,.91)]
    holes=[arch,rectangle]
    whole,cut=Recorder(),Recorder()
    point=lambda q,d:(q[0],q[1],d)
    whole.block(polygon,point,(0,0,1),.75,material,random.Random(123))
    cut.block(polygon,point,(0,0,1),.75,material,random.Random(123),holes=holes)
    assert whole.masonry_blocks==cut.masonry_blocks==1
    assert {m for _,m in cut.recorded}=={m for _,m in whole.recorded}, 'clipping repainted the stone'
    outside=inside=0
    for ix in range(49):
        for iy in range(29):
            x=-.985+1.97*(ix+.37)/49;y=.006+.985*(iy+.23)/29
            before=point_depth(whole.recorded,x,y)
            after=point_depth(cut.recorded,x,y)
            if any(in_hole(x,y,h) for h in holes):
                inside+=1
                assert not after, f'a block/bevel face crosses the aperture at {(x,y)}'
            else:
                outside+=1
                assert before and after, f'a false open joint at {(x,y)}'
                assert abs(max(d for d,_ in before)-max(d for d,_ in after))<1e-8, \
                    f'clipping changed the stone relief at {(x,y)}'
    assert outside>500 and inside>300
    print(f'PASS {"brick" if material==detail.BRICK else "ashlar"}: '
          f'{outside} unchanged surface samples; {inside} empty aperture samples')


check_stone(detail.GRANITE)
check_stone(detail.BRICK)

# The caller itself must pass the complete physical stone, rather than asking
# block() to decorate each computational remnant of an arch cut independently.
class WallRecorder(Recorder):
    def __init__(self):
        super().__init__()
        self.openings=[{'kind':'fan','axis':'y','sign':1,'at':0,'face':'north',
                        'u0':.5,'u1':1.5,'spring_z':0,'r_out':.72}]
        self.course_schedule=[.4]
        self.stones=[]

    def block(self, polygon, point, normal, confidence, mat, rng, holes=None):
        self.stones.append((polygon,holes))


wall=WallRecorder()
wall.wall([(0,0,0),(0,0,1.2),(2,0,1.2),(2,0,0)],.75,detail.GRANITE)
assert wall.stones and all(len(poly)==4 and holes for poly,holes in wall.stones), \
    'wall() decorated aperture-decomposition fragments as new stones'
print(f'PASS wall: {len(wall.stones)} complete stones forwarded with aperture masks')

# Shallow split-face facets share area-weighted normals only within this stone;
# steep chips and side/reveal faces retain their original hard normals.
front=[(0,0,0),(1,0,0),(0,1,0)]
side=[(0,0,0),(0,0,-.03),(1,0,-.03),(1,0,0)]
for degrees in (20,75):
    tilted=[(1,0,0),(0,0,0),(0,-2,2*math.tan(math.radians(degrees)))]
    softened=list(detail.stone_corner_normals([(front,True),(tilted,True),(side,False)]))
    assert softened[2]==(side,False), 'smoothing altered a stone side/reveal'
    assert [[p[:3] for p in poly] for poly,_ in softened[:2]]==[front,tilted], \
        'normal blending moved a physical stone vertex'
    a,b=softened[0][0][0][3:],softened[1][0][1][3:]
    if degrees==20:
        expected=detail.norm((0,2*math.tan(math.radians(20)),3))
        assert math.dist(a,expected)<1e-10 and math.dist(a,b)<1e-10, \
            'shallow fracture normals were not area weighted'
    else:
        assert math.dist(a,(0,0,1))<1e-10
        assert detail.dot(a,b)<math.cos(math.radians(detail.ROCK_SMOOTH_DEGREES)), \
            'a steep fracture was rounded across its hard ridge'
separate=list(detail.stone_corner_normals([(front,True)]))
assert all(math.dist(p[3:],(0,0,1))<1e-10 for p in separate[0][0]), \
    'normal sharing crossed between separate physical stones'
print('PASS rock normals: area-weighted shallow facets; hard steep chips/sides; exact positions; separate stones')


# Curved belts wrap horizontal coordinates and compress relief by4/7. Their
# normals must rotate at each stone and use the inverse scale, including values
# on the clamped outer envelope. The old planar origin-basis failed this probe.
from archetypes.masonry_house_v4_rough_bands import add_rough_band
class CurvedProbe:
    checked=0
    def raw(self,*args,**kwargs):pass
    def block(self,polygon,point,normal,confidence,mat,rng,holes=None):
        u=sum(p[0] for p in polygon)/len(polygon)
        for depth in (.006,.035,.070):
            angle=u/1.96;radial=(math.cos(angle),math.sin(angle),0)
            q=(u,.2,depth,0,0,1)
            assert math.dist(point.normal(q),radial)<1e-10, 'belt normal did not rotate around the drum'
            radius=1.96+depth*(.040/.070)
            expected=detail.norm(tuple((-math.sin(angle),math.cos(angle),0)[k]/(radius/1.96)+
                                       radial[k]/(.040/.070) for k in range(3)))
            assert math.dist(point.normal((u,.2,depth,1,0,1)),expected)<1e-10, \
                'belt normal did not account for compressed relief'
            self.checked+=1
probe=CurvedProbe();add_rough_band(probe,3,4,2,0,.4,.75)
assert probe.checked>=24
print(f'PASS curved rock normals: {probe.checked} rotated/compressed/clamped-envelope probes')


# Optical surfaces need a closed dielectric volume. Load only the real legacy
# mesh primitives used below, without importing Blender or its material system.
# This also lets the louvre fixture compare the exact inherited turret envelope.
import ast
from collections import Counter
legacy_tree=ast.parse((ROOT/'generators/archetypes/masonry_house.py').read_text())
primitive_names={'_normal','_poly_facing','_up','_finial','_box','_cone','_turret','_panel'}
legacy.__dict__.update(math=math,MeshBuilder=object,WOOD=detail.WOOD,GLASS=detail.GLASS,
                       ROOF=detail.ROOF,COPPER=detail.COPPER,PANEL_PROUD=.03)
exec(compile(ast.Module(body=[node for node in legacy_tree.body
                              if isinstance(node,ast.FunctionDef) and node.name in primitive_names],
                        type_ignores=[]),'legacy-physical-primitives','exec'),legacy.__dict__)


class PhysicalRecorder:
    """Record generated faces, including the normal correction of raw()."""
    def __init__(self):
        self.faces=[]

    def raw(self,pts,confidence,mat,want=None):
        if want is not None and detail.dot(legacy._normal(pts),want)<0:
            pts=list(reversed(pts))
        self.faces.append((list(pts),confidence,mat))

    add_poly=raw
    add_box=detail.DetailBuilder.add_box


def check_closed_glass():
    checked=0
    for normal in ((1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(.6,.8,0)):
        tangent=(-normal[1],normal[0],0)
        front=[(tangent[0]*u,tangent[1]*u,z)
               for u,z in ((0,0),(1.1,0),(1.1,1.8),(0,1.8))]
        for outline in (front,list(reversed(front))):
            b=PhysicalRecorder();detail.glass_pane(b,outline,normal,.5)
            assert len(b.faces)==6, 'pane is missing its rear or an edge face'
            assert all(mat==detail.GLASS for _,_,mat in b.faces)
            points={tuple(round(v,7) for v in p) for face,_,_ in b.faces for p in face}
            assert len(points)==8, 'pane contains duplicated or displaced surfaces'
            centre=tuple(sum(p[k] for p in points)/8 for k in range(3))
            edges=Counter();volume=0
            for face,_,_ in b.faces:
                midpoint=tuple(sum(p[k] for p in face)/4 for k in range(3))
                assert detail.dot(legacy._normal(face),detail.sub(midpoint,centre))>0, \
                    'pane has an inward-facing surface'
                for p,q in zip(face,face[1:]+face[:1]):
                    edge=tuple(sorted((tuple(round(v,7) for v in p),
                                       tuple(round(v,7) for v in q))))
                    edges[edge]+=1
                for i in range(1,len(face)-1):
                    volume+=detail.dot(face[0],detail.cross(face[i],face[i+1]))/6
            assert len(edges)==12 and set(edges.values())=={2}, \
                'pane has an open or overlapping boundary'
            assert math.isclose(volume,1.1*1.8*.004,abs_tol=1e-9), \
                'pane does not enclose the reconstructed 4 mm stock'
            assert b.faces[0][1]==.5 and all(conf==1.0 for _,conf,_ in b.faces[1:]), \
                'new glass stock lost reconstructed confidence or changed the original front'
            checked+=1
    print(f'PASS glass: {checked} direction/winding cases; closed 4 mm volume; '
          'outward normals; source front and reconstructed rear/edges')


def physical_ray_hits(face,y,z):
    """Independent triangle projection along the opening's X normal."""
    for i in range(1,len(face)-1):
        a,b,c=face[0],face[i],face[i+1]
        determinant=(b[2]-c[2])*(a[1]-c[1])+(c[1]-b[1])*(a[2]-c[2])
        if abs(determinant)<1e-12:
            continue
        wa=((b[2]-c[2])*(y-c[1])+(c[1]-b[1])*(z-c[2]))/determinant
        wb=((c[2]-a[2])*(y-c[1])+(a[1]-c[1])*(z-c[2]))/determinant
        if min(wa,wb,1-wa-wb)>1e-8:
            return True
    return False


def check_prairie_door_cutout():
    opening={'axis':'x','sign':1,'at':0,'u0':0,'u1':1.5,'z0':0,'z1':2.5,'conf':.5}
    b=PhysicalRecorder();detail.detailed_door(b,opening,'prairie_front_door')
    # T-2216: the glazing is sheet No. 95's square grille, 0.23-0.78 of the leaf across
    # and 0.13-0.49 of it down, so the rays stand inside that square.
    for y,z in ((.45,1.35),(.70,1.75),(.95,2.0),(1.10,2.1)):
        assert not any(physical_ray_hits(face,y,z) for face,_,mat in b.faces if mat==detail.WOOD), \
            'opaque wood still backs the Prairie upper glazing'
        assert any(physical_ray_hits(face,y,z) for face,_,mat in b.faces if mat==detail.GLASS), \
            'the Prairie cutout lost its glass'
    assert any(physical_ray_hits(face,.7,.6) for face,_,mat in b.faces if mat==detail.WOOD), \
        'making the upper cutout removed the lower wood panel'
    print('PASS Prairie door: four upper-pane rays clear of wood; glass and lower wood panel retained')


def check_turret_louvres():
    turret={'x0':0,'x1':1.8288,'y0':0,'y1':1.8288,'z0':10.9728,'top_z':12.5273,
            'louvre':[11.857,12.436],'apex_z':14.234,'finial_m':.4572,'conf':.5}
    before,after=PhysicalRecorder(),PhysicalRecorder()
    legacy._turret(before,turret);detail.louvred_turret(after,turret)
    assert sum(mat==detail.GLASS for _,_,mat in before.faces)==4, \
        'the legacy comparison fixture no longer represents four false glass panels'
    assert not any(mat==detail.GLASS for _,_,mat in after.faces), \
        'the louvred vent still contains transmitting glass'
    assert sum(mat==detail.DARK_GLASS for _,_,mat in after.faces)==4, \
        'one of the four louvred faces lost its recessed backing'
    def envelope(recorder):
        points=[p for face,_,_ in recorder.faces for p in face]
        return (tuple(min(p[k] for p in points) for k in range(3)),
                tuple(max(p[k] for p in points) for k in range(3)))
    assert envelope(before)==envelope(after), 'louvres changed the recorded turret envelope'
    lo,hi=turret['louvre'];pitch=(hi-lo)/round((hi-lo)/.145)
    near_faces=[face for face,_,mat in after.faces
                if mat==detail.WOOD and min(p[0] for p in face)>turret['x1']-.15]
    assert not any(physical_ray_hits(face,.9,lo+pitch) for face in near_faces), \
        'the gap between louvre blades is filled with wood'
    assert any(physical_ray_hits(face,.9,lo+pitch/2) for face in near_faces), \
        'the louvre band is empty of real timber blades'
    print('PASS turret: four false glass panels removed; real blades/gaps; exact inherited envelope')


def check_turret_dovecote():
    """T-2207: the record's vent turns the band into arched holes on perches."""
    turret={'x0':0,'x1':1.8288,'y0':0,'y1':1.8288,'z0':10.9728,'top_z':11.8567,
            'louvre':[11.2166,11.7348],'apex_z':13.1978,'finial_m':.1676,'conf':1.0,
            'vent':{'tiers':2,'per_face':3,'opening_width_m':.2286,'perch_projection_m':.0914},
            'eave':{'overhang_m':.381,'drop_m':.0305,'flare_run_m':.2286,'flare_pitch':.55}}
    b=PhysicalRecorder();detail.louvred_turret(b,turret)
    assert not any(mat==detail.GLASS for _,_,mat in b.faces), 'the cote carries glass'
    assert sum(mat==detail.DARK_GLASS for _,_,mat in b.faces)==4, 'a face lost its dark cote'
    lo,hi=turret['louvre'];step=(hi-lo)/2;ua,uc=.12,1.8288-.12
    near=[face for face,_,mat in b.faces if mat==detail.WOOD and min(p[0] for p in face)>turret['x1']-.09]
    for tier in range(2):
        hole=lo+tier*step+step*.45
        for k in range(3):
            y=ua+(uc-ua)*(k+.5)/3
            assert not any(physical_ray_hits(face,y,hole) for face in near), 'a pigeon hole is filled'
        between=ua+(uc-ua)/3
        assert any(physical_ray_hits(face,between,hole) for face in near), 'the pier between holes is gone'
    perches=[face for face,_,mat in b.faces if mat==detail.WOOD and max(p[0] for p in face)>turret['x1']+.05]
    assert perches, 'no landing board projects from the face'
    points=[p for face,_,_ in b.faces for p in face]
    assert abs(max(p[2] for p in points)-(turret['apex_z']+turret['finial_m']))<.05, 'the apex moved'
    assert abs(min(p[0] for p in points)-(-.381))<1e-6, 'the eave does not overhang as recorded'
    print('PASS turret dovecote: two tiers of open arched holes, piers and perches, apex kept')


check_closed_glass()
check_prairie_door_cutout()
check_turret_louvres()
check_turret_dovecote()


# The engine-neutral light writer must preserve concave roof/ground/aperture
# silhouettes, including a reflex corner exactly on a proposed ear diagonal.
sys.path.insert(0,str(ROOT/'tools'))
from _glessner_lod import _triangles
notches=[([(0,0),(4,0),(4,4),(2,2),(0,4)],12),
         ([(0,0),(3,0),(3,1),(1,1),(1,3),(0,3)],5),
         ([(0,0),(3,0),(3,3),(2,3),(2,1),(1,1),(1,3),(0,3)],7),
         ([(0,0),(1,0),(2,0),(2,2),(0,2)],4)]
for polygon,expected in notches:
    for poly in (polygon,list(reversed(polygon))):
        points=[(x,y,0) for x,y in poly]
        triangles=_triangles(points,(0,0,1))
        measured=sum(abs(detail.area([points[i] for i in triangle])) for triangle in triangles)
        assert abs(measured-expected)<1e-10, 'light triangulation filled a concave notch'
print('PASS light triangulation: diagonal-boundary notch, L/U outlines and collinear edges in both windings')


# T-2311: the light tier is built with Python 3.11's sum() on every interpreter.
# 1e16 + 1.0 rounds back to 1e16 in plain addition, so the 3.11 answer is 0.0; a
# compensated 3.12 sum() says 1.0, which is the drift that redded every bake.
import builtins
from _glessner_lod import _blender_arithmetic, _left_to_right_sum
assert _left_to_right_sum([1e16,1.0,-1e16])==0.0 and _left_to_right_sum([],5)==5
native=builtins.sum
seen=_blender_arithmetic(lambda:sum([1e16,1.0,-1e16]))()
assert seen==0.0, 'the light build summed with the interpreter, not the 3.11 rule'
assert builtins.sum is native, 'the pinned sum leaked out of the light build'
def failing():raise RuntimeError('fixture')
try:_blender_arithmetic(failing)()
except RuntimeError:pass
assert builtins.sum is native, 'a failed light build left the pinned sum installed'
print('PASS light arithmetic: 3.11 left-to-right sum inside the build, the native one restored after, even on failure')


# T-2202: test the generated surfaces, including their joints, rather than a
# boolean saying a frontage was requested. Both detail levels must leave the
# two access gaps traversable and cover the complete passage with mineral paving.
def check_frontage_ground():
    import json
    from archetypes.masonry_house_params import from_phase
    from archetypes.masonry_house_v4_frontage import add_frontage, passage_floor, LAWN
    record=json.loads((ROOT/'data/structures/glessner_house.json').read_text())
    params=from_phase(record['phases'][0],record)
    f=params.detail['prairie_frontage']
    class Surfaces:
        def __init__(self): self.faces=[]
        def raw(self,points,confidence,material,*_):
            assert confidence==1.0, 'frontage reconstruction was promoted to attested'
            self.faces.append((points,material))
    def height(surfaces,x,y):
        hits=[]
        for points,material in surfaces.faces:
            for i in range(1,len(points)-1):
                a,b,c=points[0],points[i],points[i+1]
                den=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
                if abs(den)<1e-10:continue
                u=((b[1]-c[1])*(x-c[0])+(c[0]-b[0])*(y-c[1]))/den
                v=((c[1]-a[1])*(x-c[0])+(a[0]-c[0])*(y-c[1]))/den
                if min(u,v,1-u-v)>=-1e-8:
                    hits.append((u*a[2]+v*b[2]+(1-u-v)*c[2],material))
        return max(hits,default=(-99,-1))
    for reduced in (False,True):
        surfaces=Surfaces();add_frontage(surfaces,params,reduced);assert passage_floor(surfaces,params)
        # One inset tread meets the sill, without a curb across the approach.
        y=sum(f['door_y'])/2
        for i in range(101):
            x=f['wall_x']+(f['walk_x']-f['wall_x'])*i/100
            z,mat=height(surfaces,x,y)
            assert f['walk_z']-.004<=z<=f['door_z']+1e-8 and mat!=LAWN,(reduced,x,z,mat)
        assert abs(height(surfaces,params.width_m+.017,y)[0]-f['door_z'])<1e-8
        # HABS5's broad inset tread now owns the bottom reveal. It continues
        # behind the facade; the old narrow opening-floor face is omitted by
        # the entry builder, whose emitted mesh is checked separately.
        entry=params.detail['prairie_entry']
        for x in (params.width_m,entry['threshold_back_x']+.01):
            assert abs(height(surfaces,x,y)[0]-f['door_z'])<1e-8
        assert abs(height(surfaces,entry['threshold_front_x']+.01,y)[0]-f['walk_z'])<1e-8
        # Three longitudinal lanes through the approach and splayed passage.
        p,q,r,s=params.detail['underpass']['pts']
        for lane in (.1,.5,.9):
            for i in range(151):
                t=i/150;x=f['walk_x']+(s[0]-f['walk_x'])*t
                if x>=p[0]:
                    k=(f['walk_x']-x)/(f['walk_x']-p[0])
                    low=f['porte_y'][0]+(q[1]-f['porte_y'][0])*k
                    high=f['porte_y'][1]+(p[1]-f['porte_y'][1])*k
                else:
                    k=(p[0]-x)/(p[0]-s[0]);low=q[1]+(r[1]-q[1])*k;high=p[1]+(s[1]-p[1])*k
                z,mat=height(surfaces,x,low+(high-low)*lane)
                assert f['passage_court_z']-.004<=z<=f['passage_front_z']+1e-8 and mat!=LAWN,(reduced,x,z,mat)
        z,_=height(surfaces,s[0],(s[1]+r[1])/2)
        assert abs(z-f['passage_court_z'])<1e-8, 'passage does not meet courtyard drive datum'
        for low,high in f['lawns']:
            z=max(height(surfaces,f['outer_x']-f['curb_width_m']/2,(low+high)/2+offset)[0] for offset in (-.012,0,.012))
            assert abs(z-f['walk_z']-f['curb_height_m'])<1e-8,'curb lost its upper silhouette'
    print('PASS frontage: both LODs, 1,108 access samples; no lawn/curb obstruction; sill and drive datums meet')


check_frontage_ground()


# T-2208: a straight jamb ends whole stones (no sliver, no joint against the
# reveal); each run alternates long/short end stones by course so joints never
# stack at a corner or jamb; and every rock face falls to its 16 mm pitch line
# at the stone's edge while the interior keeps its full relief.
def check_coursing():
    class Coursing(Recorder):
        def __init__(self):
            super().__init__()
            # A second, shorter window lands in the middle of the run beside the
            # first: that run must still be laid (it once came out bare bed).
            self.openings=[{'kind':'window','axis':'y','sign':1,'at':0,'face':'north',
                            'u0':2.3,'u1':3.5,'z0':.9,'z1':2.6},
                           {'kind':'window','axis':'y','sign':1,'at':0,'face':'north',
                            'u0':4.55,'u1':4.95,'z0':1.1,'z1':1.5}]
            self.course_schedule=[.4572,.2413,.3429,.1905]
            self.stones=[]
        def block(self, polygon, point, normal, confidence, mat, rng, holes=None):
            self.stones.append(detail.bounds(polygon))
    w=Coursing();w.wall([(0,0,0),(0,0,3.2),(6,0,3.2),(6,0,0)],.75,detail.GRANITE)
    rows={}
    # This wall's local u runs west (-x); read the spans in metres along x.
    for x0,z0,x1,z1 in w.stones:rows.setdefault(round(z0,4),[]).append((-x1,-x0))
    for z in rows:
        if .9<=z<=2.3:
            laid=sum(min(b,6)-max(a,3.5) for a,b in rows[z] if b>3.5)
            assert laid>2.3, f'the run beside the window at {z} is bare bed ({laid:.2f} m laid)'
    jambed=0
    for z,spans in rows.items():
        spans.sort()
        assert min(b-a for a,b in spans)>.25 or len(spans)<3, f'a sliver stone in the course at {z}'
        if .9<=z<=2.3:
            assert all(b<=2.3+1e-9 or a>=3.5-1e-9 for a,b in spans), \
                'a stone face crosses the jamb of a whole course'
        if any(abs(b-2.3)<1e-9 for a,b in spans) and any(abs(a-3.5)<1e-9 for a,b in spans):
            jambed+=1
    assert jambed>=3, f'only {jambed} courses end flush on both jambs'
    order=sorted(rows)
    firsts=[rows[z][0][1]-rows[z][0][0] for z in order]
    assert all(abs(a-b)>.2 for a,b in zip(firsts,firsts[1:])), 'corner joints stack over each other'
    stone=[(0,0),(1.2,0),(1.2,.4),(0,.4)]
    facets=list(detail.fractured_stone(stone,.04,random.Random(7)))
    edge=[q[2] for poly,front in facets if front for q in poly
          if min(q[0],1.2-q[0],q[1],.4-q[1])<.012]
    inner=[q[2] for poly,front in facets if front for q in poly
           if min(q[0],1.2-q[0],q[1],.4-q[1])>detail.PITCH_MARGIN]
    assert edge and max(abs(v-detail.PITCH_LINE) for v in edge)<.004, 'a rock face overruns its pitched arris'
    assert inner and sum(inner)/len(inner)>detail.PITCH_LINE+.015, 'the rock face lost its projection'
    print(f'PASS coursing: {jambed} courses end flush on both jambs; {len(order)} alternating corner stones; '
          f'{len(edge)} arris samples on the pitch line, interior mean {1000*sum(inner)/len(inner):.0f} mm proud')


check_coursing()


def check_rock_shading():
    """T-2209: the lattice's random diagonals do not shade as hard creases.

    A corner shared by several finished facets of one stone carries one normal
    unless a real steep chip meets it. At the old 35 degree limit 21 % of those
    corners lit with a jump of more than 5 degrees, the triangle mosaic seen in
    sun; the gate holds the share under 1 % on forty seeded ashlar stones.
    """
    jumps=[]
    for seed in range(40):
        stone=[(0,0),(1.0,0),(1.0,.39),(0,.39)]
        at={}
        for poly,front in detail.stone_corner_normals(detail.fractured_stone(stone,.03,random.Random(seed))):
            if not front:continue
            for q in poly:at.setdefault(tuple(round(c,9) for c in q[:3]),[]).append(q[3:])
        for normals in at.values():
            if len(normals)>1:
                jumps.append(max(math.degrees(math.acos(max(-1.0,min(1.0,detail.dot(a,b)))))
                                 for a in normals for b in normals))
    share=sum(j>5 for j in jumps)/len(jumps)
    assert share<.01, f'{100*share:.1f}% of shared rock-face corners shade as a hard crease'
    print(f'PASS rock shading: {100*share:.2f}% of {len(jumps)} shared facet corners crease (>5 degrees); limit 1%')


check_rock_shading()


def check_rock_uv_frame():
    """T-2209: every facet of one rock face reads its grain in the wall's plane.

    A face projected on its OWN normal shifts the albedo by |position| x the tilt,
    which, 30 m from the origin, is metres per lattice triangle: the triangle
    mosaic of the GA-09 audit. Shared corners must carry one UV, and that UV is
    the corner's projection on the wall frame.
    """
    class UVProbe(detail.DetailBuilder):
        def __init__(self):
            self.params=SimpleNamespace(detail={'ashlar_relief_m':[.025,.070]})
            self.masonry_blocks=0;self.verts=[];self.roof_uvs={};self.rock_normals={}
            self.smooth_rock_faces=True;self.fronts=[]
        def raw(self, pts, confidence, mat, want=None):
            base=len(self.verts);self.verts.extend(tuple(p) for p in pts)
            return list(range(base,len(self.verts)))
    probe=UVProbe()
    wall=(0.0,-1.0,0.0)
    point=lambda q,off=0:(31.0+q[0],-22.5-off,q[1]+4.0)
    probe.block([(0,0),(1.1,0),(1.1,.39),(0,.39)],point,wall,1.0,detail.GRANITE,random.Random(11))
    assert probe.roof_uvs, 'no rock facet received a wall-frame UV'
    at={}
    for index,uv in probe.roof_uvs.items():
        x,y,z=probe.verts[index]
        assert abs(uv[0]-x)<1e-9 and abs(uv[1]-z)<1e-9, 'a rock facet UV left the wall frame'
        at.setdefault(tuple(round(c,9) for c in probe.verts[index]),set()).add(tuple(round(c,9) for c in uv))
    shared=[k for k,v in at.items() if len(v)>1]
    assert not shared, f'{len(shared)} shared rock corners carry two UVs'
    print(f'PASS rock UV frame: {len(probe.roof_uvs)} facet corners on the wall plane, 0 seams')


check_rock_uv_frame()
