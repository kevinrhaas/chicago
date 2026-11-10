#!/usr/bin/env python3
"""Named1855 A gallery, adopted as RECON continuity: actual support/deck controls."""
from dataclasses import replace
import json
from pathlib import Path
import sys
from types import ModuleType
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'generators'))
class NoBlender(ModuleType):
    def __getattr__(self,name):
        raise AssertionError('CPU gallery test reached Blender '+name)
sys.modules['bpy']=NoBlender('bpy')
from archetypes.fort_structure_params import from_phase
from archetypes import fort_structure as fort
from common.mesh import MeshBuilder
record=json.loads((ROOT/'data/structures/fort_dearborn_commandants_quarters.json').read_text())
phase=record['phases'][0];p=from_phase(phase,record);p.validate()
assert p.gallery and p.gallery_storeys==2 and p.gallery_stair_side=='none'
assert phase['form']['gallery']['confidence']=='reconstructed'
assert phase['form']['gallery_storeys']['confidence']=='reconstructed'
assert (p.width_m,p.depth_m,p.wall_height_m,p.storey_height_m,p.chimneys)==(15.24,7.62,5.4,2.7,2)
# Read both actual builder paths, proving explicit support clearance did not move
# a window/door or invent a historic bay count.
def emitted_openings(params):
    out=[]
    def capture(b,axis,plane,u0,u1,z0,z1,outward,conf,kind='window',**kw):
        out.append((axis,plane,u0,u1,z0,z1,outward,conf,kind))
    original=fort._opening;fort._opening=capture
    try:fort._openings(None,params,params.wall_height_m,0.)
    finally:fort._opening=original
    return sorted(out)
legacy=replace(p,gallery=False,gallery_storeys=1,face_openings=None)
assert emitted_openings(p)==emitted_openings(legacy)
assert len(emitted_openings(p))==15
centres=fort._gallery_post_centres(p,.14)
front=[o for o in p.face_openings if o['face']=='front']
margin=.07+fort.openings.CASING_W_M+fort.openings.SILL_HORN_M
clear=lambda x:all(x<=o['u0']-margin+1e-9 or x>=o['u1']+margin-1e-9 for o in front)
assert len(centres)==6 and all(clear(x) for x in centres)
assert any(not clear(p.width_m*i/5) for i in range(1,5)), 'old grid must expose the genuine trim collision'
b=MeshBuilder('commandants-gallery');fort._gallery_two_storeys(b,p,1.)
faces=[[b.verts[i] for i in f] for f in b.faces]
# One full upper deck at the original storey line and an open lower post level.
assert any(set(f)=={(0.,7.62,2.7),(15.24,7.62,2.7),(15.24,9.72,2.7),(0.,9.72,2.7)} for f in faces)
assert abs(max(v[1] for v in b.verts)-9.87)<1e-9
assert min(v[2] for v in b.verts)==0
assert all(v==1.0 for v in b.conf)
# The actual beam's top meets the independent canopy plane at both edge lines.
roof=faces[-1];a,bb,c=roof[:3]
u=[bb[i]-a[i] for i in range(3)];v=[c[i]-a[i] for i in range(3)]
n=[u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]]
residual=lambda q:sum(n[i]*(q[i]-a[i]) for i in range(3))/n[2]
start=len(centres)*5
beam=faces[start:start+5];bottom=5.4-.45-.14
top={v for f in beam for v in f if v[2]>bottom+1e-9}
assert len(top)==4 and max(abs(residual(q)) for q in top)<1e-12
print('PASS commandants gallery: RECON two levels; original15 openings exact;6 supports clear both-storey trim; full15.24x2.1m deck at2.7m; native canopy contact; no extra stairs/producer change')
