#!/usr/bin/env python3
"""CPU geometry check: the exterior flight actually connects ground and piazza."""
from dataclasses import replace
import json
from pathlib import Path
import sys
from types import ModuleType
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'generators'))
class NoBlender(ModuleType):
    def __getattr__(self, name):
        raise AssertionError('CPU stair test reached Blender: '+name)
sys.modules['bpy'] = NoBlender('bpy')
from archetypes.fort_structure_params import from_phase
from archetypes import fort_structure as fort
from common.mesh import MeshBuilder
record=json.loads((ROOT/'data/structures/fort_dearborn_officers_quarters.json').read_text())
p=replace(from_phase(record['phases'][0],record), gallery_stair_side='right')
p.validate()
assert p.gallery_stair_side == 'right'
b=MeshBuilder('outside-stair')
fort._gallery_stair(b,p,1.)
# Read the actual tread top faces, independent of the step-count implementation:
# broad horizontal rectangles, one metre across, thinner than their run.
tops=[]
for face in b.faces:
    points=[b.verts[i] for i in face]
    if len({round(v[2],9) for v in points}) != 1: continue
    xs=[v[0] for v in points]; ys=[v[1] for v in points]
    if abs(max(ys)-min(ys)-1.2)<1e-9 and .2<max(xs)-min(xs)<.4:
        tops.append((round(points[0][2],8),min(xs),max(xs)))
# Both top and underside rectangles appear: select the 70 mm-separated top.
levels=sorted({z for z,_,_ in tops})
levels=[z for z in levels if any(abs(z-other-.07)<1e-7 for other in levels)]
assert len(levels)==13
walk_levels=[0.,*levels,p.storey_height_m]
assert max(b-a for a,b in zip(walk_levels,walk_levels[1:]))<.18
assert min(v[0] for v in b.verts)>=p.width_m-1e-9
assert abs(max(v[0] for v in b.verts)-p.width_m-3.6)<1e-9
assert abs(max(v[2] for v in b.verts)-p.storey_height_m-.95)<1e-9
# The landing end is actually open across the clear stair throat at floor+0.5m.
gallery=MeshBuilder('stair-gallery')
fort._gallery_two_storeys(gallery,p,1.)
for face in gallery.faces:
    points=[gallery.verts[i] for i in face]
    if not all(p.width_m-.14-1e-8<=v[0]<=p.width_m+1e-8 for v in points): continue
    ys=[v[1] for v in points]; zs=[v[2] for v in points]
    assert not (min(ys)<p.depth_m+1.85 and max(ys)>p.depth_m+.85
                and min(zs)<p.storey_height_m+.5<max(zs)), 'rail blocks stair landing'
for invalid in (replace(p,gallery_stair_side='spiral'),
                replace(p,gallery_storeys=1),replace(p,gallery=False)):
    try: invalid.validate()
    except ValueError: pass
    else: raise AssertionError('invalid stair combination accepted')
replace(p,gallery_stair_side='none').validate()
# New Lake House opt-in is default-safe on this unrelated record.
assert p.construction_site is False
for invalid in (replace(p,construction_site=True),replace(p,construction_site=1)):
    try: invalid.validate()
    except ValueError: pass
    else: raise AssertionError('invalid construction-site combination accepted')
print('PASS outside piazza stair: 13 timber treads connect ground to2.4m floor; '
      'rise<0.18m, landing open, 3.6m run,1m clear width,0.95m rails; guarded default-off controls')
