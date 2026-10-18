#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Portable unittest; no filesystem writes and no Blender or third-party packages."""
import ast,copy,hashlib,json,os,pathlib,struct,types,unittest
from human_frame_residue import CAP,Rejected,parse,repair,sha

def pack(d,chunks):
 j=json.dumps(d,separators=(',',':')).encode();j+=b' '*((-len(j))%4)
 body=b''.join(struct.pack('<II',len(b),k)+b for k,b in [(0x4e4f534a,j)]+chunks[1:])
 return struct.pack('<III',0x46546c67,2,len(body)+12)+body

def proof(b):
 return dict(input_sha256=sha(b),verified_by='unit-test mutation harness, NOT authored Blender verification',verification_reference='Actual committed CI fixture plus explicit test mutation. Production caller must independently verify bpy state.',**{k:True for k in ['rig_object_scales_unit','pose_bone_scales_unit','no_constraints','no_drivers','no_scale_fcurves','authored_rigid_rig']})

class FrameResidueTest(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.source=pathlib.Path(os.environ.get('C4D_HUMAN_FRAME_FIXTURE',pathlib.Path(__file__).resolve().parents[1]/'assets/humans/c4d_fixture.lod0.glb'))
  cls.raw=cls.source.read_bytes();cls.d,cls.chunks=parse(cls.raw);cls.joints=set(cls.d['skins'][0]['joints'])
  cls.target=next(i for i in cls.joints if cls.d['nodes'][i].get('name')=='thigh_l')
  cls.non=next(i for i in range(len(cls.d['nodes']))if i not in cls.joints)
 def tearDown(self):self.assertEqual(self.source.read_bytes(),self.raw,'existing source fixture changed')
 def accepted(self,b):
  out,r=repair(b,proof(b));self.assertEqual(parse(out)[1][1:],parse(b)[1][1:]);self.assertTrue(r['binary_bytes_preserved']);self.assertTrue(r['meshes_skins_ibm_accessors_unchanged']);return parse(out)[0],r
 def mutation(self,edit):
  d=copy.deepcopy(self.d);c=copy.deepcopy(self.chunks);edit(d,c);return pack(d,c)
 def animation(self):
  d=copy.deepcopy(self.d);c=copy.deepcopy(self.chunks);a=d['animations'][0];inp=a['samplers'][0]['input'];count=d['accessors'][inp]['count'];blob=bytearray(c[1][1]);off=len(blob);blob.extend(b''.join(struct.pack('<fff',1,1+2**-23,1-2**-23)for _ in range(count)))
  vi=len(d['bufferViews']);d['bufferViews'].append({'buffer':0,'byteOffset':off,'byteLength':count*12});ai=len(d['accessors']);d['accessors'].append({'bufferView':vi,'componentType':5126,'type':'VEC3','count':count});d['buffers'][0]['byteLength']=len(blob);c[1]=(c[1][0],bytes(blob));si=len(a['samplers']);a['samplers'].append({'input':inp,'output':ai,'interpolation':'LINEAR'});a['channels'].append({'sampler':si,'target':{'node':self.target,'path':'scale'}})
  return d,c,ai,vi,si,off
 def source_verifier_fixture(self):
  # Extract the ACTUAL verifier, without importing bpy or executing exporter main.
  # The GLB fixture path stands in for a saved file ONLY in this explicit stub.
  exporter=pathlib.Path(__file__).resolve().parents[1]/'tools/human_export.py'
  tree=ast.parse(exporter.read_text())
  function=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='verified_rigid_frames')
  def obj():return types.SimpleNamespace(scale=[1,1,1],delta_scale=[1,1,1],matrix_world=types.SimpleNamespace(to_scale=lambda:[1,1,1]),constraints=[],animation_data=types.SimpleNamespace(drivers=[]))
  rig=obj();rig.parent=None;rig.pose=types.SimpleNamespace(bones=[types.SimpleNamespace(scale=[1,1,1],constraints=[])]);rig.data=types.SimpleNamespace(animation_data=None)
  mesh=obj();bpy_stub=types.SimpleNamespace(data=types.SimpleNamespace(filepath=str(self.source),actions=[]),app=types.SimpleNamespace(version_string='EXPLICIT TEST STUB, not Blender'))
  namespace={'bpy':bpy_stub,'Path':pathlib.Path,'hashlib':hashlib,'json':json}
  exec(compile(ast.fix_missing_locations(ast.Module(body=[function],type_ignores=[])),str(exporter),'exec'),namespace)
  return namespace['verified_rigid_frames'],bpy_stub,rig,mesh
 def test_actual_source_verifier_proof_wires_to_residue_helper(self):
  verify,bpy_stub,rig,mesh=self.source_verifier_fixture()
  source=self.mutation(lambda d,c:d['nodes'][self.target].update(scale=[1,.9999999403953552,.9999979734420776]))
  actual=verify(rig,[mesh]);actual['input_sha256']=sha(source)
  self.assertIsInstance(actual['verification_reference'],str,'actual caller proof must serialize its saved-master reference')
  reference=json.loads(actual['verification_reference']);self.assertEqual(reference['sha256'],sha(self.raw));self.assertEqual(reference['master'],str(self.source))
  out,receipt=repair(source,actual)
  self.assertTrue(receipt['binary_bytes_preserved']);self.assertTrue(receipt['meshes_skins_ibm_accessors_unchanged']);self.assertEqual(parse(source)[1][1:],parse(out)[1][1:])
 def test_actual_source_verifier_refuses_authored_nonrigid_state(self):
  def action(curves=(),layers=()):return types.SimpleNamespace(fcurves=list(curves),layers=list(layers))
  def curve(path):return types.SimpleNamespace(data_path=path)
  def layered_scale(bpy_stub):bpy_stub.data.actions=[action(layers=[types.SimpleNamespace(strips=[types.SimpleNamespace(channelbags=[types.SimpleNamespace(fcurves=[curve('pose.bones["thigh_l"].scale')])])])])]
  cases=[
   ('legacy scale curve',lambda b,r,m:setattr(b.data,'actions',[action([curve('scale')])])),
   ('layered scale curve',lambda b,r,m:layered_scale(b)),
   ('object scale',lambda b,r,m:setattr(m,'scale',[1,1,1.01])),
   ('delta scale',lambda b,r,m:setattr(r,'delta_scale',[1,.99,1])),
   ('world scale',lambda b,r,m:setattr(r,'matrix_world',types.SimpleNamespace(to_scale=lambda:[1,1,1.01]))),
   ('pose scale',lambda b,r,m:setattr(r.pose.bones[0],'scale',[1,1,1.01])),
   ('object constraint',lambda b,r,m:setattr(r,'constraints',[object()])),
   ('pose constraint',lambda b,r,m:setattr(r.pose.bones[0],'constraints',[object()])),
   ('object driver',lambda b,r,m:setattr(r.animation_data,'drivers',[object()])),
   ('armature-data driver',lambda b,r,m:setattr(r.data,'animation_data',types.SimpleNamespace(drivers=[object()]))),
  ]
  for label,mutate in cases:
   with self.subTest(label=label):
    verify,bpy_stub,rig,mesh=self.source_verifier_fixture();mutate(bpy_stub,rig,mesh)
    with self.assertRaises(ValueError):verify(rig,[mesh])

 def test_actual_fixture_preserves_all_binary_and_nonjoint_nodes(self):
  out,r=self.accepted(self.raw)
  for i,n in enumerate(self.d['nodes']):
   if i not in self.joints:self.assertEqual(n,out['nodes'][i])
  self.assertLess(r['max_rest_translation_delta_m'],1e-6)
 def test_actual_fixture_with_exact_reported_ci_residue(self):
  b=self.mutation(lambda d,c:d['nodes'][self.target].update(scale=[1,.9999999404,.9999979734]));out,r=self.accepted(b)
  self.assertNotIn('scale',out['nodes'][self.target]);self.assertLess(r['max_rest_translation_delta_m'],1e-6);self.assertLess(r['max_rest_1m_point_bound_m'],1e-5)
 def test_requires_explicit_input_bound_proof(self):
  for bad in [{},{**proof(self.raw),'input_sha256':'0'*64},{**proof(self.raw),'no_drivers':False},{**proof(self.raw),'verified_by':' '}]:
   with self.subTest(bad=bad),self.assertRaises(Rejected):repair(self.raw,bad)
 def test_rejects_large_nonfinite_malformed_joint_scales(self):
  for scale in [[1,1.01,1],[1,1+CAP+1e-9,1],[1,float('inf'),1],[1,float('nan'),1],[True,1,1],[1,1]]:
   with self.subTest(scale=scale):
    b=self.mutation(lambda d,c:d['nodes'][self.target].update(scale=scale))
    with self.assertRaises(Rejected):repair(b,proof(b))
 def test_rejects_joint_matrix(self):
  b=self.mutation(lambda d,c:d['nodes'][self.target].update(matrix=[1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1]))
  with self.assertRaises(Rejected):repair(b,proof(b))
 def test_nonjoint_trs_scales_preserved_with_unchanged_guard(self):
  b=self.mutation(lambda d,c:d['nodes'][self.non].update(scale=[1,1+2**-23,1]));out,_=self.accepted(b);self.assertEqual(out['nodes'][self.non]['scale'],[1,1+2**-23,1])
  for scale in [[1,1.000002,1],[1,float('inf'),1]]:
   b=self.mutation(lambda d,c:d['nodes'][self.non].update(scale=scale))
   with self.subTest(scale=scale),self.assertRaises(Rejected):repair(b,proof(b))
 def test_nonjoint_matrix_scale_preserved_or_refused(self):
  for s,allowed in [(1+2**-23,True),(1.000002,False),(float('nan'),False)]:
   def edit(d,c):
    n=d['nodes'][self.non]
    for k in ['translation','rotation','scale']:n.pop(k,None)
    n['matrix']=[s,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1]
   b=self.mutation(edit)
   if allowed:
    out,_=self.accepted(b);self.assertEqual(out['nodes'][self.non],parse(b)[0]['nodes'][self.non])
   else:
    with self.subTest(s=s),self.assertRaises(Rejected):repair(b,proof(b))
 def test_linear_and_step_scale_channels_preserve_binary(self):
  for interpolation in ['LINEAR','STEP']:
   d,c,ai,vi,si,off=self.animation();d['animations'][0]['samplers'][si]['interpolation']=interpolation;out,r=self.accepted(pack(d,c));self.assertTrue(any(x['kind']=='joint_scale_channel_removed'for x in r['changes']));self.assertFalse(any(ch['target']['path']=='scale'for ch in out['animations'][0]['channels']))
 def test_rejects_cubic_sparse_and_nonjoint_animation_scale(self):
  for kind in ['cubic','sparse','nonjoint']:
   d,c,ai,vi,si,off=self.animation()
   if kind=='cubic':d['animations'][0]['samplers'][si]['interpolation']='CUBICSPLINE'
   if kind=='sparse':d['accessors'][ai]['sparse']={}
   if kind=='nonjoint':d['animations'][0]['channels'][-1]['target']['node']=self.non
   b=pack(d,c)
   with self.subTest(kind=kind),self.assertRaises(Rejected):repair(b,proof(b))
 def test_rejects_accessor_view_and_buffer_extensions(self):
  for kind in ['accessor','view','buffer']:
   d,c,ai,vi,si,off=self.animation();obj=d['accessors'][ai]if kind=='accessor'else d['bufferViews'][vi]if kind=='view'else d['buffers'][0];obj['extensions']={'unsupported_fixture':{}};b=pack(d,c)
   with self.subTest(kind=kind),self.assertRaises(Rejected):repair(b,proof(b))
 def test_rejects_invalid_indices_counts_offsets_and_stride(self):
  for kind,val in [('accessor',-1),('accessor',True),('view',-1),('view',True),('buffer',-1),('buffer',True),('count',-1),('count',True),('offset',-1),('offset',True),('offset',10**12),('viewoffset',-1),('viewlength',True),('bufferlength',-1),('stride',True),('stride',-4),('stride',256),('sampler',-1),('sampler',True),('target',True),('joint',True)]:
   d,c,ai,vi,si,off=self.animation()
   if kind=='accessor':d['animations'][0]['samplers'][si]['output']=val
   elif kind=='view':d['accessors'][ai]['bufferView']=val
   elif kind=='buffer':d['bufferViews'][vi]['buffer']=val
   elif kind=='count':d['accessors'][ai]['count']=val
   elif kind=='offset':d['accessors'][ai]['byteOffset']=val
   elif kind=='viewoffset':d['bufferViews'][vi]['byteOffset']=val
   elif kind=='viewlength':d['bufferViews'][vi]['byteLength']=val
   elif kind=='bufferlength':d['buffers'][0]['byteLength']=val
   elif kind=='stride':d['bufferViews'][vi]['byteStride']=val
   elif kind=='sampler':d['animations'][0]['channels'][-1]['sampler']=val
   elif kind=='target':d['animations'][0]['channels'][-1]['target']['node']=val
   elif kind=='joint':d['skins'][0]['joints'][0]=val
   b=pack(d,c)
   with self.subTest(kind=kind,val=val),self.assertRaises(Rejected):repair(b,proof(b))
 def test_rejects_large_animation_scale_samples(self):
  d,c,ai,vi,si,off=self.animation();blob=bytearray(c[1][1]);struct.pack_into('<f',blob,off+4,1.01);c[1]=(c[1][0],bytes(blob));b=pack(d,c)
  with self.assertRaises(Rejected):repair(b,proof(b))

if __name__=='__main__':unittest.main()
