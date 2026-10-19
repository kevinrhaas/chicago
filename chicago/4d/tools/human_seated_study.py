# SPDX-License-Identifier: GPL-3.0-or-later
"""Original opt-in global-source pose conversion. No bpy dependency."""
import json,hashlib,math
from pathlib import Path

def mm(a,b):return [[math.fsum(a[i][k]*b[k][j] for k in range(4)) for j in range(4)] for i in range(4)]
def inverse_rigid(a):
 r=[[a[j][i] for j in range(3)] for i in range(3)]
 return [r[i]+[-math.fsum(r[i][k]*a[k][3] for k in range(3))] for i in range(3)]+[[0,0,0,1]]
def transform(rotation,head):return [list(rotation[i])+[head[i]] for i in range(3)]+[[0,0,0,1]]
def source_pose_to_blender(entry):
 # C maps source(x,y,z) -> Blender(x,-z,y), positive determinant.
 c=[[1,0,0,0],[0,0,-1,0],[0,1,0,0],[0,0,0,1]]
 r=mm(mm(c,transform(entry['rotation_3x3'],[0,0,0])),inverse_rigid(c))
 r[0][3],r[1][3],r[2][3]=entry['head_m'][0],-entry['head_m'][2],entry['head_m'][1]
 return r

def local_basis(rest,desired,parent_rest=None,parent_desired=None):
 """M = B^-1 Bparent Pparent^-1 P, or B^-1 P for root.

 B and P are armature-space actual bone rest/desired matrices; P includes
 rotated ACTUAL rest orientation, not just deformation rotation.
 """
 if parent_rest is None:return mm(inverse_rigid(rest),desired)
 return mm(mm(mm(inverse_rigid(rest),parent_rest),inverse_rigid(parent_desired)),desired)

def load_study(profile_path,variant,body_path,scale,vehicle_path):
 if scale!=1:raise ValueError('reviewed seated study requires unscaled metre body')
 if str(variant.get('person_reference_scene'))!='1835':raise ValueError('wrong variant scene; no1835pose on another date')
 p=Path(profile_path);d=json.loads(p.read_text())
 if d.get('scene')!='1835' or d.get('vehicle_variant')!='wagon_w01_driver_bench_study':raise ValueError('wrong scene/physical bench variant')
 vehicle=json.loads(Path(vehicle_path).read_text())
 furniture=vehicle.get('driver_furniture',{})
 if vehicle.get('asset_id')!=d['vehicle_variant'] or furniture.get('variant')!='removable_bench_study':raise ValueError('actual exported physical bench variant required')
 if furniture.get('seat_surface_m')!=[0,1.58,.65] or furniture.get('footboard_bounds_xz_m')!=[-.425,.425,1.12,1.42] or furniture.get('footboard_top_m')!=1.12:raise ValueError('seated furniture dimensions changed; re-solve contact')
 rows=[r for r in d['resident_bindings'] if r['asset_id']==variant['id'] and r['person_reference_id']==variant['person_reference_id']]
 if len(rows)!=1:raise ValueError('explicit matching existing resident binding required')
 row=rows[0]
 if hashlib.sha256(Path(body_path).read_bytes()).hexdigest()!=row['body_sha256']:raise ValueError('seated pose body hash stale')
 path=p.parent/row['pose_draft_file']
 if hashlib.sha256(path.read_bytes()).hexdigest()!=row['pose_draft_sha256']:raise ValueError('seated pose hash stale')
 pose=json.loads(path.read_text())['bone_global_head_rotation']
 for e in pose.values():
  if len(e.get('head_m',[]))!=3 or len(e.get('rotation_3x3',[]))!=3 or any(len(row)!=3 for row in e['rotation_3x3']):raise ValueError('invalid seated rigid matrix shape')
  if not all(math.isfinite(x) for x in e['head_m']+sum(e['rotation_3x3'],[])):raise ValueError('nonfinite seated transform')
  r=e['rotation_3x3']
  if any(abs(math.fsum(r[i][k]*r[j][k] for k in range(3))-(1 if i==j else 0))>1e-8 for i in range(3) for j in range(3)):raise ValueError('nonrigid seated rotation')
  determinant=r[0][0]*(r[1][1]*r[2][2]-r[1][2]*r[2][1])-r[0][1]*(r[1][0]*r[2][2]-r[1][2]*r[2][0])+r[0][2]*(r[1][0]*r[2][1]-r[1][1]*r[2][0])
  if abs(determinant-1)>1e-8:raise ValueError('seated reflection is not a rigid rotation')
 rest={b['name']:b for b in json.loads(Path(body_path).read_text())['skeleton']}
 if set(pose)!=set(rest):raise ValueError('seated joint set differs from source body')
 for name,bone in rest.items():
  parent=bone['parent']
  if parent is None:continue
  local=[bone['head_m'][k]-rest[parent]['head_m'][k] for k in range(3)]
  expected=[pose[parent]['head_m'][i]+math.fsum(pose[parent]['rotation_3x3'][i][k]*local[k] for k in range(3)) for i in range(3)]
  if math.dist(expected,pose[name]['head_m'])>1e-8:raise ValueError('seated pose stretches a source bone chain')
 return pose,dict(variant=d['vehicle_variant'],scene='1835',grade='reconstructed',person_reference_id=row['person_reference_id'],body_sha256=row['body_sha256'],vehicle_sidecar_sha256=hashlib.sha256(Path(vehicle_path).read_bytes()).hexdigest(),status='Source LBS mechanical fit; canonical export, garment contact and palm grips pending')

def desired_matrix(entry,rest):
 deformation=source_pose_to_blender(entry)
 desired=mm(deformation,rest)
 # Deformation translation is the desired head, not an affine skinning offset.
 for i in range(3):desired[i][3]=deformation[i][3]
 return desired
