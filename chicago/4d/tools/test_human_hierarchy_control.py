#!/usr/bin/env python3
import contextlib,copy,importlib.util,io,runpy,sys,tempfile,types,unittest
from unittest import mock
from pathlib import Path
from types import SimpleNamespace as N
sys.dont_write_bytecode=True
spec=importlib.util.spec_from_file_location('control',Path(__file__).with_name('human_hierarchy_control.py'));control=importlib.util.module_from_spec(spec);spec.loader.exec_module(control)
class Matrix(list):
 def copy(self):return Matrix(copy.deepcopy(list(self)))
def identity():return Matrix([[1 if i==j else 0 for j in range(4)]for i in range(4)])
def fixture():
 rig=N(name='rig',parent=None,matrix_world=identity());data=object();mesh=N(name='body',parent=None,matrix_world=identity(),matrix_parent_inverse=identity(),data=data,modifiers=[N(type='ARMATURE',object=rig)])
 return rig,mesh
class Test(unittest.TestCase):
 def test_actual_helper_parent_only(self):
  rig,mesh=fixture();before=control.matrix_values(mesh.matrix_world);data=mesh.data;mod=mesh.modifiers[0]
  changes=control.reparent_control(rig,[mesh],[])
  self.assertIs(mesh.parent,rig);self.assertIs(mesh.data,data);self.assertIs(mesh.modifiers[0],mod);self.assertEqual(before,control.matrix_values(mesh.matrix_world));self.assertEqual(changes[0]['world_before'],changes[0]['world_after'])
 def test_refuses_nonidentity_existing_parent_unknown_rig_duplicate_names(self):
  for kind in ['rigframe','meshframe','parentinverse','rigparent','meshparent','wrongrig','duplicate','empty']:
   rig,mesh=fixture();meshes=[mesh]
   if kind=='rigframe':rig.matrix_world[0][3]=1
   elif kind=='meshframe':mesh.matrix_world[1][3]=1
   elif kind=='parentinverse':mesh.matrix_parent_inverse[2][3]=1
   elif kind=='rigparent':rig.parent=object()
   elif kind=='meshparent':mesh.parent=rig
   elif kind=='wrongrig':mesh.modifiers[0].object=object()
   elif kind=='duplicate':meshes=[mesh,copy.copy(mesh)]
   elif kind=='empty':meshes=[]
   with self.subTest(kind=kind),self.assertRaises(ValueError):control.reparent_control(rig,meshes,[])
   if kind!='meshparent':self.assertIsNone(mesh.parent,'refusal must precede any hierarchy mutation')
 def test_object_animation_refused_but_pose_bone_animation_allowed(self):
  for layered in [False,True]:
   rig,mesh=fixture();curve=N(data_path='location');action=N(fcurves=[] if layered else [curve],layers=[N(strips=[N(channelbags=[N(fcurves=[curve])])])]if layered else [])
   with self.assertRaises(ValueError):control.reparent_control(rig,[mesh],[action])
  rig,mesh=fixture();control.reparent_control(rig,[mesh],[N(fcurves=[N(data_path='pose.bones["pelvis"].location')],layers=[])])
 def test_cli_requires_explicit_test_mode_before_bpy_import(self):
  # argparse exits before importing bpy. No actual BPy is available/invoked.
  with contextlib.redirect_stderr(io.StringIO()),self.assertRaises(SystemExit):control.main(['--source','a','--output','/tmp/a','--receipt','/tmp/r'])
 def test_cli_distinct_and_tmp_paths_required_before_bpy(self):
  for args in [ ['--source','/tmp/a','--output','/tmp/a','--receipt','/tmp/r'],['--source','/tmp/s','--output','/tmp/a','--receipt','/tmp/a'],['--source','s','--output','/workspace/no','--receipt','/tmp/r'] ]:
   with contextlib.redirect_stderr(io.StringIO()),self.assertRaises(SystemExit):control.main(args+['--test-only-parented-control'])

class ScriptImportTest(unittest.TestCase):
 def test_actual_script_imports_sibling_exporter_without_script_directory(self):
  # Execute the actual entry point with Blender-style sys.path and stub bpy.
  # Abort at the first Blender operation; no verifier/model/export is executed.
  script=Path(__file__).resolve().with_name('human_hierarchy_control.py')
  sibling=script.with_name('human_export.py');tools=script.parent
  class ReachedBlenderOpen(RuntimeError):pass
  def open_mainfile(**kwargs):
   exporter=sys.modules['human_export']
   self.assertEqual(Path(exporter.__file__).resolve(),sibling)
   self.assertTrue(callable(exporter.verified_rigid_frames))
   raise ReachedBlenderOpen('EXPLICIT bpy STUB: sibling import completed')
  bpy_stub=types.ModuleType('bpy');bpy_stub.ops=N(wm=N(open_mainfile=open_mainfile))
  isolated=[entry for entry in sys.path if entry and Path(entry).resolve() not in {tools,tools.parent}]
  self.assertNotIn(str(tools),isolated)
  with tempfile.TemporaryDirectory(dir='/tmp')as tmp:
   directory=Path(tmp);source=directory/'source.blend';source.write_bytes(b'EXPLICIT STUB SAVED MASTER')
   args=['blender','--','--source',str(source),'--output',str(directory/'control.blend'),'--receipt',str(directory/'receipt.json'),'--test-only-parented-control']
   with mock.patch.object(sys,'path',isolated),mock.patch.object(sys,'argv',args),mock.patch.dict(sys.modules,{'bpy':bpy_stub}):
    sys.modules.pop('human_export',None)
    with self.assertRaises(ReachedBlenderOpen):runpy.run_path(str(script),run_name='__main__')
   self.assertEqual(source.read_bytes(),b'EXPLICIT STUB SAVED MASTER')
   self.assertEqual(sorted(p.name for p in directory.iterdir()),['source.blend'])

if __name__=='__main__':unittest.main()
