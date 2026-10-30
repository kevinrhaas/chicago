"""Meaningful NORMAL-child source controls; no native qualification inheritance.

This source test checks the exact newly qualified canonical child and explicitly
preserved e49 parent. Native129 commands live in the portable package; routine
source checks validate the bound record without pretending to rerun a browser.
"""
import ast,copy,hashlib,json,struct,sys,unittest
from pathlib import Path
APP=Path(__file__).resolve().parents[1]
PACKAGE=APP/'tools/transport/horse_eye_smooth_normals_v1'
SOURCE=APP/'assets/authored/transport/horse_standing'
sys.path.insert(0,str(PACKAGE))
import recorded_qualification as record
import normal_child_source as child
import qualify_normal_child as qualify

class EyeSmoothNormalsSource(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.source=child.Sources(APP,SOURCE)
 def test_exact_deterministic_source_and_seven_actual_corruptions(self):
  self.assertEqual(qualify.source_controls(self.source),['EYE_POSITION','BODY_NORMAL','BODY_POSITION','EYE_UV','material_change','false_NORMAL_extrema','nonunit_eye_NORMAL'])
  self.assertEqual(self.source.normal_structure['candidate_sha256'],child.CANDIDATE_SHA)
  self.assertEqual(self.source.normal_structure['actual_changed_BIN_bytes'],37722)
  self.assertEqual(self.source.normal_structure['rows_changed'],3968)
 def test_actual_weights_indices_and_animation_corruptions_rejected(self):
  s=self.source;g=s.generator;d,b=g.decode(s.raw[s.child_path]);eye=d['meshes'][2]['primitives'][0]
  for semantic in ['WEIGHTS_0','indices']:
   ai=eye['indices']if semantic=='indices'else eye['attributes'][semantic];a,offset,stride,width=g.layout(d,ai);bad=bytearray(b)
   if semantic=='indices':
    fmt={5121:'<B',5123:'<H',5125:'<I'}[a['componentType']];old=struct.unpack_from(fmt,bad,offset)[0];struct.pack_into(fmt,bad,offset,(old+1)%d['accessors'][eye['attributes']['POSITION']]['count'])
   else:struct.pack_into('<f',bad,offset,struct.unpack_from('<f',bad,offset)[0]+.01)
   self.assertNotEqual(bytes(bad),b,'Each negative control must actually alter source bytes')
   with self.subTest(semantic=semantic),self.assertRaises(ValueError):g.inspect(s.normal_parent_raw,g.encode(d,bytes(bad)),s.recipe)
  doc=copy.deepcopy(d);doc['animations'][0]['channels'][0]['target']['node']=0
  with self.assertRaises(ValueError):g.inspect(s.normal_parent_raw,g.encode(doc,b),s.recipe)
 def test_firstclass_fixture_and_prototype_recipe_bindings(self):
  spec=json.loads((PACKAGE/'INPUTS.json').read_text())
  for name,row in spec['inputs'].items():
   base=APP if row['base']=='app'else PACKAGE;path=(base/row['path']).resolve();self.assertTrue(path.is_relative_to(base));raw=path.read_bytes()
   with self.subTest(name=name):self.assertEqual(len(raw),row['bytes']);self.assertEqual(hashlib.sha256(raw).hexdigest(),row['sha256'])
  self.assertEqual(self.source.recipe['state'],'UNADOPTED_UNQUALIFIED_SOURCE_STUDY')
  self.assertEqual(self.source.recipe['qualification'].split(':')[0],'NONE')
  matrices=json.loads((PACKAGE/'fixtures/accepted-stationary65-matrices.json').read_text())['frames']
  self.assertEqual([row['time_s']for row in matrices],[i*3/16 for i in range(65)])
  known=json.loads((PACKAGE/'fixtures/accepted-phasea-known.json').read_text());self.assertEqual(known['phase_a_arrays_sha256'],spec['inputs']['phase_a_arrays']['sha256'])
 def test_qualified_child_actual_selection_and_exact_preserved_parent(self):
  spec_now=json.loads((APP/'data/transport/parked/horse-sevket-sidecar.json').read_bytes())
  if spec_now['runtime_asset'].get('source_qualification_mode')=='quiet_head_neck_idle_v6':
   from test_standing_horse_quiet_head_neck import preserved_normal_source
   source=preserved_normal_source()
  else:source=record.check_source_selection()
  self.assertEqual(source.normal_structure['candidate_sha256'],child.CANDIDATE_SHA)
  authored=json.loads((SOURCE/'SOURCE.json').read_text());spec=json.loads((APP/'data/transport/parked/horse-sevket-sidecar.json').read_text())
  self.assertEqual(authored['preserved_upper_orbital_parent_derivative'],spec['preserved_upper_orbital_runtime_asset'])
  self.assertEqual(spec['preserved_upper_orbital_runtime_asset']['sha256'],child.PARENT_SHA)
  runtime=spec['preserved_eye_smooth_normals_runtime_asset']if spec['runtime_asset'].get('source_qualification_mode')=='quiet_head_neck_idle_v6'else spec['runtime_asset']
  self.assertEqual(runtime['sha256'],child.CANDIDATE_SHA)
  creation=authored['preserved_creation_candidate_record'];self.assertFalse(creation['runtime_selected']);self.assertFalse(creation['photographic_acceptance']);self.assertEqual(creation['state'],'PENDING_CANONICAL_SOURCE_QUALIFICATION_NOT_SELECTED')
 def test_actual_new_certificate_rejects_old_parent_and_real_record_corruptions(self):
  actual=record.read_certificate()
  old=json.loads((APP/'data/transport/parked/standing-horse-planted/upper-orbital-transition-v1-qualification-summary.json').read_text())
  with self.assertRaises(ValueError):record.verify_recorded_certificate(old)
  controls=[('wrong_asset',lambda c:c.__setitem__('candidate_sha256',child.PARENT_SHA)),('wrong_code',lambda c:c['actual_code_pins'].__setitem__('NEW/run_normal_child129.cjs','0'*64)),('nonrest_replay',lambda c:c['all129_socket_samples'][37].__setitem__('time_s',0)),('nonrest_violation',lambda c:c['all129_socket_samples'][37].__setitem__('BODY_max_upper_m',.015)),('raised_limit',lambda c:c['limits_m'].__setitem__('BODY_locus',.0141)),('parent_transfer',lambda c:c.__setitem__('old_certificate_transferred',True)),('native129_not_run',lambda c:c.__setitem__('new_bd443_129_actually_executed',False)),('photo_overclaim',lambda c:c.__setitem__('photographic_acceptance',True)),('owned_child_remaining',lambda c:c['closed_runs']['native129'].__setitem__('remaining_owned_children',[123])),('WebGL_attempt',lambda c:c.__setitem__('actual_WebGL_context_requests',1)),('missing_raw',lambda c:c.__setitem__('actual_Float64_raw_bytes',0))]
  for name,mutate in controls:
   bad=copy.deepcopy(actual);mutate(bad)
   with self.subTest(control=name),self.assertRaises(ValueError):record.verify_recorded_certificate(bad)
 def test_original_physical_loop_capture_and_all_old_modes_unchanged(self):
  frozen=APP/'tools/transport/horse_socket_interface_v1/fixtures';loop=(frozen/'UNCHANGED-PHYSICAL-METRIC-LOOP.mjs.txt').read_bytes();old=(frozen/'NATIVE-PRODUCER-readback-socket129.mjs').read_bytes();producer=(PACKAGE/'native_normal_child129.mjs').read_bytes()
  self.assertEqual(len(loop),9176);self.assertEqual(hashlib.sha256(loop).hexdigest(),child.PHYSICAL_LOOP_SHA);self.assertEqual(producer.count(loop),1)
  capture=old[old.index(b'// Distinct external capture only.'):];self.assertTrue(producer.endswith(capture))
  idle=(APP/'renderers/web/js/standing-horse-planted-idle.js').read_text();self.assertIn("export const PLANTED_MODE = 'upper_orbital_transition_v1';",idle);self.assertIn(child.PARENT_SHA,idle);self.assertIn(child.CANDIDATE_SHA,idle);self.assertIn('72506859017d1f1aea57ad248d877a88bb07e701d4ec82c31e509dbb97e8d7a0',idle);self.assertIn(record.CERTIFICATE_SHA,idle)
 def test_qualifying_implementation_has_no_external_runtime_dependency(self):
  for name in ['normal_child_source.py','qualify_normal_child.py','run_normal_child129.cjs','INPUTS.json']:
   text=(PACKAGE/name).read_text();self.assertNotIn('/workspace',text);self.assertNotIn('/tmp/chicago',text);self.assertNotIn('HORSE-EYE-NORMALS-STUDY-',text)
  self.assertEqual(len(qualify.code_pins()),14)
 @classmethod
 def tearDownClass(cls):cls.source.unchanged()

if __name__=='__main__':unittest.main()
