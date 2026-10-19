# SPDX-License-Identifier: GPL-3.0-or-later
"""UNEXECUTED BPy mesh adapter prototype. Explicit isolated-CI experiment only.
No bpy import; callers supply a real Mesh only after the ordinary custom setter.
"""
import collections,hashlib,json,math
from pathlib import Path
from human_normal_probe_math import Refused,S,distance,prototype_transaction
class CornerAdapter:
 def __init__(self,mesh):
  self.mesh=mesh;self.count=len(mesh.loops);self.attribute=mesh.attributes.get('custom_normal')
  if not self.count or not mesh.has_custom_normals or self.attribute is None:raise Refused('existing custom normals required')
  valence=collections.Counter(v.vertex_index for v in mesh.loops)
  if max(valence.values())>65535:raise Refused('corner valence exceeds safe uniform int32 averaging budget')
  if self.attribute.data_type!='INT16_2D' or self.attribute.domain!='CORNER' or len(self.attribute.data)!=self.count:raise Refused('custom_normal must be existing INT16_2D CORNER attribute')
 def read_codes(self):return [tuple(v.value) for v in self.attribute.data]
 def write_codes(self,codes):
  if len(codes)!=self.count:raise Refused('Short2 corner count differs')
  if any(len(code)!=2 or any(not isinstance(v,int)or isinstance(v,bool)or not -S<=v<=S for v in code)for code in codes):raise Refused('Short2 range/type invalid')
  self.attribute.data.foreach_set('value',[v for code in codes for v in code])
 def update(self):self.mesh.update()
 def read_normals(self):return [tuple(n.vector) for n in self.mesh.corner_normals]
 def invariant_digest(self):
  m=self.mesh
  payload={'name':m.name,'vertices':[(tuple(v.co),[(g.group,g.weight)for g in v.groups])for v in m.vertices],
   'edges':[(tuple(e.vertices),e.use_edge_sharp)for e in m.edges],
   'loops':[(v.vertex_index,v.edge_index)for v in m.loops],
   'polygons':[(tuple(p.vertices),p.material_index,p.use_smooth,p.loop_start,p.loop_total)for p in m.polygons],
   'uv_layers':[(layer.name,[tuple(v.uv)for v in layer.data])for layer in m.uv_layers],
   'shape_keys':[(key.name,[tuple(v.co)for v in key.data])for key in m.shape_keys.key_blocks]if m.shape_keys else [],
   'material_names':[mat.name if mat else None for mat in m.materials]}
  return hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def bounded_readback(mesh,actual,targets,source_ids):
 if len(actual)!=len(targets):raise Refused('normal audit count mismatch')
 deltas=[distance(tuple(a),tuple(b))for a,b in zip(actual,targets)]
 if not deltas or not all(math.isfinite(d)for d in deltas):raise Refused('normal audit is empty/nonfinite')
 top=sorted(range(len(deltas)),key=lambda i:deltas[i],reverse=True)[:5]
 return {'corners':len(deltas),'maximum_raw_vector_delta':max(deltas),'mean_raw_vector_delta':math.fsum(deltas)/len(deltas),'bad_corner_count':sum(d>1e-3 for d in deltas),'tolerance':1e-3,
  'top_corners':[{'loop_index':i,'vertex_index':mesh.loops[i].vertex_index,'source_vertex_id':source_ids[mesh.loops[i].vertex_index],'raw_vector_delta':deltas[i],'expected_normal':tuple(targets[i]),'actual_normal':tuple(actual[i])}for i in top]}
def experiment(mesh,converted_point_normals,source_ids,receipt_path,context=None):
 """No acceptance claim until this real-adapter path executes in pinned CI.
 All failure paths after probing restore packed values and invalidate caches.
 The existing caller MUST still run its unchanged raw1e-3 readback guard.
 """
 path=Path(receipt_path).resolve()
 if not path.is_relative_to(Path('/tmp')):raise Refused('experiment receipts must remain under /tmp')
 if len(source_ids)!=len(mesh.vertices)or len(converted_point_normals)!=len(mesh.vertices):raise Refused('source/normal vertex count mismatch')
 if any(not isinstance(v,int)or isinstance(v,bool)or v<0 for v in source_ids):raise Refused('invalid source IDs')
 adapter=CornerAdapter(mesh);adapter.update();original=adapter.read_codes();before_vectors=adapter.read_normals();baseline=adapter.invariant_digest()
 targets=[tuple(converted_point_normals[loop.vertex_index])for loop in mesh.loops]
 receipt={'scope':'EXPERIMENTAL packed-normal Mesh API probe authoring; caller/CI must identify real versus mock execution, not photographic acceptance','execution_context':context or {'status':'unspecified; no actual BPy evidence claimed'},'mesh_invariant_digest':baseline,'mesh':mesh.name,'before':bounded_readback(mesh,before_vectors,targets,source_ids),'status':'failed'}
 try:
  result=prototype_transaction(adapter,[v.vertex_index for v in mesh.loops],[source_ids[v.vertex_index]for v in mesh.loops],targets)
  after=adapter.read_normals();receipt['after']=bounded_readback(mesh,after,targets,source_ids)
  if receipt['after']['maximum_raw_vector_delta']>1e-3:raise Refused('raw final guard exceeds1e-3')
  if adapter.invariant_digest()!=baseline:raise Refused('mesh invariant changed')
  receipt.update(status='passed',result=result,mesh_invariant_unchanged=True)
  path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(receipt,indent=2,allow_nan=False)+'\n')
 except Exception as error:
  # Also covers failures after the inner transaction completed but later audits failed.
  adapter.write_codes(original);adapter.update()
  restored=adapter.read_codes()==original and adapter.invariant_digest()==baseline
  vectors=adapter.read_normals();restored=restored and len(vectors)==len(before_vectors) and max((distance(a,b)for a,b in zip(vectors,before_vectors)),default=0)<=1e-7
  receipt.update(error=str(error)[:1000],original_codes_and_mesh_invariants_restored=restored)
  # Bounded failure record, never packed arrays/mesh payloads; never suppress.
  print(json.dumps({'normal_probe_failure':receipt},allow_nan=False),flush=True)
  path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(receipt,indent=2,allow_nan=False)+'\n')
  if not restored:raise Refused('normal probe restoration could not be verified')from error
  raise
 return receipt
