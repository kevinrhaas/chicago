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

import importlib.util
import math
from pathlib import Path
import random
import sys
from types import ModuleType, SimpleNamespace
from unittest.mock import patch

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
