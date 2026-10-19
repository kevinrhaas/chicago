"""Tests execute actual proposed helper, never duplicated validator logic."""
import copy,importlib.util,json,struct,subprocess,sys,tempfile,unittest
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('audit',HERE/'audit_human_animation_times.py');audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)
def document():
 return {'accessors':[{'componentType':5126,'type':'SCALAR','count':37,'min':[0],'max':[1.2]}],'animations':[{'name':'walk','extras':{'speed_m_s':.6,'stance_fraction':.62,'cycle_duration_s':1.2},'samplers':[{'input':0}]}]}
def glb(doc):
 data=json.dumps(doc).encode();data+=b' '*((-len(data))%4);return struct.pack('<IIIII',0x46546c67,2,20+len(data),len(data),0x4e4f534a)+data
class Audit(unittest.TestCase):
 def test_valid_declared_metadata_only(self):
  r=audit.audit_document(document());self.assertEqual(r[0]['serialized_bounds_unique'],[(0,1.2)]);self.assertIn('NOT decoded',audit.SCOPE)
 def test_malformed_missing_bounds(self):
  for key in ['min','max']:
   for value in [None,[],[0,1],True,'1',[True],[None],[float('nan')],[float('inf')],[10**1000]]:
    d=document();d['accessors'][0][key]=value
    with self.subTest(key=key,value=str(value)[:40]),self.assertRaises(ValueError):audit.audit_document(d)
   d=document();del d['accessors'][0][key]
   with self.assertRaises(ValueError):audit.audit_document(d)
 def test_nonzero_origin_wrongend_reversed_negative(self):
  for lo,hi in [(1/30,37/30),(0,2),(.2,.1),(-1,1.2),(0,0)]:
   d=document();d['accessors'][0].update(min=[lo],max=[hi])
   with self.assertRaises(ValueError):audit.audit_document(d)
 def test_empty_missing_bad_samplers_and_indices(self):
  for value in [None,[],{},[None],[{}],[{'input':True}],[{'input':-1}],[{'input':1}],[{'input':0.0}]]:
   d=document();d['animations'][0]['samplers']=value
   with self.assertRaises(ValueError):audit.audit_document(d)
 def test_time_accessor_shape_and_count(self):
  for key,value in [('type','VEC3'),('componentType',5123),('componentType',5126.0),('count',0),('count',True),('count',1.2)]:
   d=document();d['accessors'][0][key]=value
   with self.assertRaises(ValueError):audit.audit_document(d)
 def test_motion_extras_missing_malformed_wrong_nonfinite_bool(self):
  for key in ['speed_m_s','stance_fraction','cycle_duration_s']:
   for value in [None,True,'0.6',float('nan'),float('inf'),.1]:
    d=document();d['animations'][0]['extras'][key]=value
    with self.assertRaises(ValueError):audit.audit_document(d)
  for value in [None,[],True]:
   d=document();d['animations'][0]['extras']=value
   with self.assertRaises(ValueError):audit.audit_document(d)
 def test_duplicate_walk_empty_animation_or_accessors(self):
  for mutate in [lambda d:d['animations'].append(copy.deepcopy(d['animations'][0])),lambda d:d.update(animations=[]),lambda d:d.update(accessors=[]),lambda d:d.update(animations=[None])]:
   d=document();mutate(d)
   with self.assertRaises(ValueError):audit.audit_document(d)
 def test_cli_actual_source_valid_and_invalid_and_no_writes(self):
  with tempfile.TemporaryDirectory() as tmp:
   good=Path(tmp)/'good.glb';good.write_bytes(glb(document()));bad=Path(tmp)/'bad.glb';bad.write_bytes(b'truncated');before={p.name:p.read_bytes() for p in Path(tmp).iterdir()}
   p=subprocess.run([sys.executable,str(HERE/'audit_human_animation_times.py'),str(good),str(bad)],capture_output=True,text=True)
   self.assertEqual(p.returncode,1);rows=[json.loads(v) for v in p.stdout.splitlines()];self.assertTrue(rows[0]['passed']);self.assertFalse(rows[1]['passed']);self.assertNotIn('Traceback',p.stderr)
   self.assertEqual(before,{p.name:p.read_bytes() for p in Path(tmp).iterdir()})
 def test_noargs_and_missing_file(self):
  p=subprocess.run([sys.executable,str(HERE/'audit_human_animation_times.py')],capture_output=True,text=True);self.assertEqual(p.returncode,2);self.assertIn('usage:',p.stderr)
  self.assertFalse(audit.inspect_file(HERE/'nonexistent.glb')['passed'])
 def test_json_nonfinite_and_bad_container_refuse(self):
  with tempfile.TemporaryDirectory() as tmp:
   f=Path(tmp)/'bad.glb';d=document();d['accessors'][0]['max']=[float('nan')];f.write_bytes(glb(d));self.assertIn('nonfinite JSON',audit.inspect_file(f)['error'])
   raw=bytearray(glb(document()));struct.pack_into('<I',raw,12,0x7fffffff);f.write_bytes(raw);self.assertIn('JSON chunk',audit.inspect_file(f)['error'])
if __name__=='__main__':unittest.main()
