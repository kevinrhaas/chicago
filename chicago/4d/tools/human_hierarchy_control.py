#!/usr/bin/env python3
"""Pinned-CI-only clone control; never publish this parented test master."""
import argparse,hashlib,json,math,sys
from pathlib import Path

def identity(matrix):
 return all(math.isfinite(matrix[i][j]) and abs(matrix[i][j]-(1 if i==j else 0))<=1e-9 for i in range(4) for j in range(4))
def matrix_values(matrix):return [[float(matrix[i][j]) for j in range(4)] for i in range(4)]
def reparent_control(rig,meshes,actions):
 if rig.parent is not None or not identity(rig.matrix_world):raise ValueError('control requires fresh root identity rig')
 forbidden={'location','rotation_euler','rotation_quaternion','rotation_axis_angle','scale','delta_location','delta_rotation_euler','delta_rotation_quaternion','delta_scale'}
 for action in actions:
  curves=list(getattr(action,'fcurves',()))
  for layer in getattr(action,'layers',()):
   for strip in getattr(layer,'strips',()):
    for bag in getattr(strip,'channelbags',()):curves.extend(bag.fcurves)
  if any(c.data_path in forbidden for c in curves):raise ValueError('control refuses object transform animation')
 if not meshes or len({m.name for m in meshes})!=len(meshes):raise ValueError('unique named skinned meshes required')
 for mesh in meshes:
  if not mesh.name or mesh.parent is not None or not identity(mesh.matrix_world) or not identity(mesh.matrix_parent_inverse):raise ValueError('control requires fresh root identity meshes')
  modifiers=[m for m in mesh.modifiers if m.type=='ARMATURE']
  if len(modifiers)!=1 or modifiers[0].object is not rig:raise ValueError('mesh must reference same rig by exactly one Armature modifier')
 changes=[]
 for mesh in meshes:
  before=matrix_values(mesh.matrix_world);world=mesh.matrix_world.copy();data=mesh.data
  mesh.parent=rig;mesh.matrix_world=world
  if mesh.data is not data or matrix_values(mesh.matrix_world)!=before:raise ValueError('control changed source mesh data or world transform')
  changes.append({'mesh':mesh.name,'old_parent':None,'new_parent':rig.name,'world_before':before,'world_after':matrix_values(mesh.matrix_world)})
 return changes

def main(argv):
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',required=True,type=Path);p.add_argument('--output',required=True,type=Path);p.add_argument('--receipt',required=True,type=Path);p.add_argument('--test-only-parented-control',required=True,action='store_true');args=p.parse_args(argv)
 args.source=args.source.resolve();args.output=args.output.resolve();args.receipt=args.receipt.resolve()
 for path in [args.output,args.receipt]:
  if not path.resolve().is_relative_to(Path('/tmp')):p.error('test control outputs must be under /tmp')
 if len({args.output.resolve(),args.source.resolve(),args.receipt.resolve()})!=3:p.error('source, control and receipt paths must be distinct')
 import bpy
 # Blender --python does not guarantee that this script directory is on sys.path.
 sys.path.insert(0,str(Path(__file__).resolve().parent))
 from human_export import verified_rigid_frames
 source_hash=hashlib.sha256(args.source.read_bytes()).hexdigest();bpy.ops.wm.open_mainfile(filepath=str(args.source.resolve()))
 scene=bpy.context.scene;prov=scene.get('chicago4d_human');prov=prov.to_dict() if hasattr(prov,'to_dict') else prov
 if not isinstance(prov,dict) or prov.get('rigid_bone_frame_export') is not True:raise ValueError('only newly authored verified-rig master is eligible')
 before_prov=json.dumps(prov,sort_keys=True);rigs=[o for o in scene.objects if o.type=='ARMATURE'];meshes=[o for o in scene.objects if o.type=='MESH']
 if len(rigs)!=1:raise ValueError('one authored rig required')
 proof=verified_rigid_frames(rigs[0],meshes);changes=reparent_control(rigs[0],meshes,bpy.data.actions);bpy.context.view_layer.update()
 for mesh in meshes:
  if not identity(mesh.matrix_world):raise ValueError('evaluated control mesh world frame changed')
 after=scene['chicago4d_human'];after=after.to_dict() if hasattr(after,'to_dict') else after
 if json.dumps(after,sort_keys=True)!=before_prov:raise ValueError('embedded provenance changed')
 verified_rigid_frames(rigs[0],meshes)
 args.output.parent.mkdir(parents=True,exist_ok=True);args.receipt.parent.mkdir(parents=True,exist_ok=True);bpy.ops.wm.save_as_mainfile(filepath=str(args.output.resolve()),compress=True)
 # Verify persisted metadata, not only the pre-save scene dictionary.
 bpy.ops.wm.open_mainfile(filepath=str(args.output))
 persisted=bpy.context.scene.get('chicago4d_human');persisted=persisted.to_dict() if hasattr(persisted,'to_dict') else persisted
 if json.dumps(persisted,sort_keys=True)!=before_prov:raise ValueError('serialized control provenance changed')
 if hashlib.sha256(args.source.read_bytes()).hexdigest()!=source_hash:raise ValueError('original master bytes changed')
 receipt={'scope':'TEST ARTIFACT: newly built same-master parented hierarchy control; not historical CI45 artifact or production asset','source':str(args.source),'source_sha256':source_hash,'control':str(args.output),'control_sha256':hashlib.sha256(args.output.read_bytes()).hexdigest(),'embedded_provenance_unchanged':True,'serialized_provenance_reloaded_and_equal':True,'source_bytes_unchanged':True,'source_verification':proof,'changes':changes}
 args.receipt.write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({'test_control':str(args.output),'mesh_names':[c['mesh'] for c in changes],'source_sha256':source_hash,'provenance_unchanged':True}))
if __name__=='__main__':raise SystemExit(main(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else sys.argv[1:]))
