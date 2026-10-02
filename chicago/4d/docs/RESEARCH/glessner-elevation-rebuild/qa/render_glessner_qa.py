"""Scratch-only actual GLB review. No geometry/material changes.
Coordinates after glTF import are X east, Y north, Z up, metres.
West orthographic shows north/front on LEFT, south/rear on RIGHT.
"""
import bpy,sys,json,hashlib,time,argparse
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,'/workspace/scratch/61c0efdafb0a/chicago/chicago/4d/tools')
import render_structure_review as base
p=argparse.ArgumentParser();p.add_argument('--glb',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--views',default='west,north,northwest,south,courtyard');p.add_argument('--size',type=int,default=1200);p.add_argument('--samples',type=int,default=32);p.add_argument('--threads',type=int,default=4)
a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);a.out.mkdir(parents=True,exist_ok=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=str(a.glb.resolve()))
imported=list(bpy.context.scene.objects);model=base.model_description(imported)
# Refuse a normalized/rotated GLB to stop a misleading camera setup.
lo,hi=model['bounds_m']['min'],model['bounds_m']['max']
assert 48<hi[0]-lo[0]<52 and 22<hi[1]-lo[1]<26 and 13<hi[2]-lo[2]<18,model['bounds_m']
a.sky='overcast';a.exposure=-1.5;a.look='AgX - Base Contrast';a.sun_elevation=32;a.sun_azimuth=45
sc=bpy.context.scene;base.scene_settings(sc,a);base.configure_daylight(sc,a);base.neutral_ground()
bpy.ops.object.camera_add();cam=bpy.context.object;cam.name='REVIEW_ONLY_camera';sc.camera=cam;cam.data.clip_end=2000
views={
 'west':dict(position=(-40,11.70,7.10),target=(0,11.70,7.10),ortho=27.5,ratio=.69),
 'north':dict(position=(24.5,70,7.2),target=(24.5,22.55,7.2),ortho=54,ratio=.37),
 'north-detail':dict(position=(10,60,6.8),target=(10,22.55,6.8),ortho=27,ratio=.68),
 'northwest':dict(position=(-18,46,7.0),target=(9,16,5.8),lens=43,ratio=.80),
 'south':dict(position=(5.6,-35,7),target=(5.6,4.3,7),ortho=15.8,ratio=1.12),
 'courtyard':dict(position=(34,-5,10.8),target=(10.5,14,6.0),lens=32,ratio=.80),
 'west-roof':dict(position=(-25,-8,15),target=(5,12,8),lens=43,ratio=.80),
}
report=dict(glb=str(a.glb.resolve()),sha256=hashlib.sha256(a.glb.read_bytes()).hexdigest(),model=model,settings={'samples':a.samples,'seed':1904,'sky':'CIE mathematical overcast','exposure':-1.5,'coordinateFrame':'X east Y north Z up (metres), SW origin'},review_additions=['Neutral plane','CIE overcast lighting','Review camera'],renders=[])
for name in a.views.split(','):
 v=views[name];cam.location=v['position'];cam.rotation_euler=(Vector(v['target'])-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO' if 'ortho' in v else 'PERSP';cam.data.ortho_scale=v.get('ortho',25);cam.data.lens=v.get('lens',40);cam.data.sensor_width=36
 sc.render.resolution_x=a.size;sc.render.resolution_y=round(a.size*v['ratio']);sc.render.filepath=str(a.out/(name+'.png'))
 t=time.monotonic();bpy.ops.render.render(write_still=True);report['renders'].append(dict(name=name,path=sc.render.filepath,seconds=round(time.monotonic()-t,2),**v));(a.out/'review.json').write_text(json.dumps(report,indent=2));print('QA_RENDER',name,flush=True)
print('QA_COMPLETE',a.out,flush=True)
