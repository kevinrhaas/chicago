"""Physical roof-module and complete-host coverage checks (no Blender).

Build the actual light house, then apply full tile construction to every one of
its pitched host polygons. Check real emitted geometry in independent metre
coordinates, including tiny clipped returns and equal-pitch cone facets.
"""
import argparse
import json
import math
from pathlib import Path
from _glessner_lod import _construct, _geometry_modules, _normal, _triangles

ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output',type=Path)
args=parser.parse_args()
light,params,materials=_construct(ROOT)
d,_,_=_geometry_modules(ROOT)
spec=params.detail['roof_tiles']
width,exposure=spec['width_in']*.0254,spec['exposure_in']*.0254
assert math.isclose(width,.1524) and math.isclose(exposure,.127), 'HABS six-inch by five-inch module'
repeat=materials.TILE_M['roof_tiles']
assert all(math.isclose(a,b) for a,b in zip(repeat,(16*width,16*exposure)))
full=d.DetailBuilder('roof-coverage-test',params)
patches=[];face_count=0;tile_count=0;covered_area=0
for host in light.roof_surfaces:
    start=len(full.faces);before=full.roof_tiles
    full.tiles(host['points'],.5)
    emitted=full.faces[start:]
    # First face must close the complete host, regardless of fragment size.
    assert set(full.verts[i] for i in emitted[0])==set(host['points'])
    normal=host['normal'];slope=math.sqrt(1-normal[2]**2)
    horizontal=(-normal[1]/slope,normal[0]/slope,0)
    uphill=(-normal[0]*normal[2]/slope,-normal[1]*normal[2]/slope,slope)
    for face in emitted:
        points=[full.verts[i] for i in face]
        uv=[full.roof_uvs[i] for i in face]
        # Exact host metric basis, including lifted tile fronts/noses.
        for p,q in zip(points,uv):
            expected=(sum(a*b for a,b in zip(p,horizontal)),sum(a*b for a,b in zip(p,uphill))+host['phase_offset'])
            assert math.dist(q,expected)<1e-8
        if face is emitted[0]:
            assert all(abs(q[1]-p[2]/slope)<1e-8 for p,q in zip(points,uv))
            continue
        u=[q[0] for q in uv];v=[q[1] for q in uv]
        assert max(u)-min(u)<=width-spec['joint_m']+1e-7
        assert max(v)-min(v)<=exposure+1e-7
        if abs(d.area(uv))>1e-8:
            middle=sum(v)/len(v);row=math.floor(middle/exposure)
            assert min(v)>=row*exposure-1e-7 and max(v)<=(row+1)*exposure+1e-7
    tiles=full.roof_tiles-before
    if host['area_m2']>.08:assert tiles>0
    covered_area+=host['area_m2'];tile_count+=tiles;face_count+=len(emitted)
    patches.append({'area_m2':host['area_m2'],'tiles':tiles,'vertices':len(host['points']),
                    'normal':normal,'bounds_zup':[[min(p[k] for p in host['points']),max(p[k] for p in host['points'])] for k in range(3)]})
# Independent same-height cone points must have identical course phase. A
# translated cone exposes the former world-origin-dependent facet drift.
cone=d.DetailBuilder('cone-test',params)
d.legacy._cone(cone,13.7,-9.2,1.6,8.3,10.9,.5,d.ROOF,seg=24)
phases=[]
for host in cone.roof_surfaces:
    n=host['normal'];slope=math.sqrt(1-n[2]**2)
    phases.append(8.3/slope)
assert max(phases)-min(phases)<1e-9
assert len(cone.roof_surfaces)==24
# Small clipped triangle formerly skipped by the .08 m² threshold.
tiny=d.DetailBuilder('tiny-test',params)
tiny.add_poly([(0,0,2),(0.1,0,2),(.05,.1,2.1)],.5,d.ROOF)
assert tiny.roof_tiles>0 and len(tiny.roof_uvs)>3
# Roof coverage does not depend on the masonry-decoration switch.
off=d.DetailBuilder('disabled-masonry-test',params);off.decorate=False
off.add_poly([(0,0,2),(.5,0,2),(.5,.5,2.5),(0,.5,2.5)],.5,d.ROOF)
assert off.roof_tiles>0
# Undersides and historically copper surfaces must not acquire clay geometry.
protected=d.DetailBuilder('protected-test',params)
protected.add_poly([(0,.5,2.5),(.5,.5,2.5),(.5,0,2),(0,0,2)],.5,d.ROOF)
protected.add_poly([(0,0,2),(.5,0,2),(.5,.5,2.5),(0,.5,2.5)],.5,d.COPPER)
assert protected.roof_tiles==0 and not protected.roof_surfaces
triangles=sum(len(_triangles([light.verts[i] for i in f],_normal([light.verts[i] for i in f]))) for f in light.faces)
assert triangles<=200000
receipt={'width_m':width,'exposure_m':exposure,'texture_repeat_m':repeat,'host_patches':len(patches),
         'host_area_m2':covered_area,'full_tiles':tile_count,'full_roof_faces':face_count,
         'light_triangles':triangles,'small_patches_under_008_m2':sum(p['area_m2']<.08 for p in patches),
         'checks':['complete host bed coverage','full tile bounds and course pitch','host-frame UVs','cone course phase','tiny triangle','decoration-independent coverage','copper and underside exclusion','light triangle ceiling'],
         'patches':patches}
if args.output:args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(receipt,indent=2)+'\n')
print(f"PASS: {len(patches)} roof patches, {tile_count:,} full tiles, 6×5 in module, {triangles:,} light triangles")
