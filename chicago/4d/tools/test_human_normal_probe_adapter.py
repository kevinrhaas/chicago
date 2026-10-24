"""Actual adapter functions with explicit API mocks. No import bpy/execution."""
import contextlib,io,json,math,sys,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace as N
sys.dont_write_bytecode=True
from human_normal_probe import CornerAdapter,experiment
from human_normal_probe_math import decode,S,Refused
class Codes(list):
 def foreach_set(self,name,values):
  assert name=='value'and len(values)==2*len(self)
  for i,item in enumerate(self):item.value=tuple(values[2*i:2*i+2])
class Mesh:
 def __init__(self,stale=False,fail_after_probe=False):
  self.name='EXPLICIT MOCK body';self.frames=[((0,0,1),(1,0,0),(0,1,0),math.pi/2,math.pi/2),((0,0,1),(math.cos(.4),math.sin(.4),0),(-math.sin(.4),math.cos(.4),0),math.pi/2,math.pi/2)]
  self.loops=[N(vertex_index=i//2,edge_index=i)for i in range(4)];self.vertices=[N(co=(0,0,0),groups=[N(group=0,weight=1)])for _ in range(2)];self.edges=[N(vertices=(0,1),use_edge_sharp=False)];self.polygons=[N(vertices=(0,1),material_index=0,use_smooth=True,loop_start=0,loop_total=4)]
  self.uv_layers=[N(name='UVMap',data=[N(uv=(i/4,0))for i in range(4)])];self.shape_keys=None;self.materials=[];self.has_custom_normals=True
  self.codes=Codes([N(value=(S,0))for _ in range(4)]);self.attributes={'custom_normal':N(data_type='INT16_2D',domain='CORNER',data=self.codes)};self.updates=0;self.stale=stale;self.fail_after_probe=fail_after_probe;self._normals=[]
 def update(self):
  self.updates+=1
  if self.stale and self._normals:return
  self._normals=[]
  for fan,f in enumerate(self.frames):
   codes=self.codes[2*fan:2*fan+2];code=tuple(int(sum(c.value[a]for c in codes)/2)for a in [0,1]);normal=decode(f,code)
   if self.fail_after_probe and self.updates==7:normal=(0,1,0)
   self._normals.extend([N(vector=normal),N(vector=normal)])
 @property
 def corner_normals(self):return self._normals
class Tests(unittest.TestCase):
 def run_experiment(self,mesh,path):
  target=(math.cos(.01),math.sin(.01),0)
  return experiment(mesh,[target,target],[10,10],path)
 def test_api_adapter_success_raw_guard_and_bounded_receipt(self):
  mesh=Mesh();original=CornerAdapter(mesh).read_codes();invariant=CornerAdapter(mesh).invariant_digest()
  with tempfile.TemporaryDirectory(dir='/tmp')as tmp:
   p=Path(tmp)/'receipt.json';r=self.run_experiment(mesh,p);self.assertEqual(r['status'],'passed');self.assertLess(r['after']['maximum_raw_vector_delta'],1e-3);self.assertEqual(json.loads(p.read_text())['status'],'passed');self.assertNotIn('codes',r['result'])
  self.assertNotEqual(CornerAdapter(mesh).read_codes(),original);self.assertEqual(CornerAdapter(mesh).invariant_digest(),invariant)
 def test_stale_cache_and_bad_actual_output_restore_original(self):
  for mesh in [Mesh(stale=True),Mesh(fail_after_probe=True)]:
   original=CornerAdapter(mesh).read_codes()
   with tempfile.TemporaryDirectory(dir='/tmp')as tmp,contextlib.redirect_stdout(io.StringIO()):
    p=Path(tmp)/'receipt.json'
    with self.assertRaises(Refused):self.run_experiment(mesh,p)
    self.assertTrue(json.loads(p.read_text())['original_codes_and_mesh_invariants_restored']);self.assertEqual(CornerAdapter(mesh).read_codes(),original)
 def test_raw_range_type_and_attribute_guards(self):
  mesh=Mesh();a=CornerAdapter(mesh)
  for bad in [[(True,0)]*4,[(-32768,0)]*4,[(0,32768)]*4]:
   with self.assertRaises(Refused):a.write_codes(bad)
  mesh.attributes['custom_normal'].data_type='FLOAT_VECTOR'
  with self.assertRaises(Refused):CornerAdapter(mesh)
 def test_receipt_io_failure_also_restores(self):
  mesh=Mesh();original=CornerAdapter(mesh).read_codes()
  with tempfile.TemporaryDirectory(dir='/tmp')as tmp,contextlib.redirect_stdout(io.StringIO()):
   bad=Path(tmp)/'file';bad.write_text('parent is a file')
   with self.assertRaises(OSError):self.run_experiment(mesh,bad/'receipt.json')
  self.assertEqual(CornerAdapter(mesh).read_codes(),original)
if __name__=='__main__':unittest.main()
