# SPDX-License-Identifier: GPL-3.0-or-later
"""Pure named/date/physical-seat/rigid-frame refusal tests; no BPy or asset writes."""
from pathlib import Path
import argparse
import copy
import hashlib
import json
import tempfile
import unittest
from human_seated_study import load_study, local_basis, desired_matrix, mm, inverse_rigid, transform

PARSER=argparse.ArgumentParser();PARSER.add_argument('--source-root',type=Path,default=Path(__file__).resolve().parents[1]);PARSER.add_argument('--proposal-root',type=Path,default=Path(__file__).resolve().parents[1]);PARSER.add_argument('--vehicle',type=Path,required=True);ARGS,EXTRA=PARSER.parse_known_args()
PROFILE=ARGS.proposal_root/'data/humans/poses/w01/resident-driver-bindings.json'
RECIPE=json.loads((ARGS.source_root/'data/humans/recipes/worker_1835.json').read_text())
class Seated(unittest.TestCase):
 def setUp(self):
  self.variant=RECIPE['proof_variants'][0];self.body=ARGS.source_root/self.variant['body_input']
 def test_actual_named_body_and_physical_vehicle(self):
  for variant in RECIPE['proof_variants']:
   pose,metadata=load_study(PROFILE,variant,ARGS.source_root/variant['body_input'],1,ARGS.vehicle)
   self.assertEqual(metadata['person_reference_id'],variant['person_reference_id']);self.assertEqual(metadata['scene'],'1835');self.assertEqual(len(pose),56)
 def test_wrong_resident_refused(self):
  wrong={**self.variant,'person_reference_id':'invented_driver'}
  with self.assertRaisesRegex(ValueError,'matching'):load_study(PROFILE,wrong,self.body,1,ARGS.vehicle)
 def test_scaled_body_refused(self):
  with self.assertRaisesRegex(ValueError,'unscaled'):load_study(PROFILE,self.variant,self.body,1.1,ARGS.vehicle)
 def test_wrong_date_refused(self):
  with tempfile.TemporaryDirectory()as folder:
   wrong=json.loads(PROFILE.read_text());wrong['scene']='1904';p=Path(folder)/'profile.json';p.write_text(json.dumps(wrong))
   with self.assertRaisesRegex(ValueError,'wrong scene'):load_study(p,self.variant,self.body,1,ARGS.vehicle)
 def test_wrong_variant_scene_refused(self):
  with self.assertRaisesRegex(ValueError,'wrong variant scene'):load_study(PROFILE,{**self.variant,'person_reference_scene':'1904'},self.body,1,ARGS.vehicle)
 def test_empty_wagon_not_a_seat(self):
  with tempfile.TemporaryDirectory()as folder:
   p=Path(folder)/'wagon.json';p.write_text(json.dumps({'asset_id':'wagon_w01'}))
   with self.assertRaisesRegex(ValueError,'physical bench'):load_study(PROFILE,self.variant,self.body,1,p)
 def test_changed_source_body_refused(self):
  with tempfile.TemporaryDirectory()as folder:
   p=Path(folder)/'body.json';p.write_text('{}')
   with self.assertRaisesRegex(ValueError,'body hash'):load_study(PROFILE,self.variant,p,1,ARGS.vehicle)
 def test_nonrigid_pose_refused_even_with_matching_data_hash(self):
  with tempfile.TemporaryDirectory()as folder:
   folder=Path(folder);profile=json.loads(PROFILE.read_text());row=profile['resident_bindings'][0];pose=json.loads((PROFILE.parent/row['pose_draft_file']).read_text());first=next(iter(pose['bone_global_head_rotation'].values()));first['rotation_3x3'][0][0]=2
   f=folder/row['pose_draft_file'];f.write_text(json.dumps(pose));row['pose_draft_sha256']=hashlib.sha256(f.read_bytes()).hexdigest();p=folder/'profile.json';p.write_text(json.dumps(profile))
   with self.assertRaisesRegex(ValueError,'nonrigid'):load_study(p,self.variant,self.body,1,ARGS.vehicle)
 def test_translated_child_stretch_refused(self):
  with tempfile.TemporaryDirectory()as folder:
   folder=Path(folder);profile=json.loads(PROFILE.read_text());row=profile['resident_bindings'][0];pose=json.loads((PROFILE.parent/row['pose_draft_file']).read_text());pose['bone_global_head_rotation']['calf_l']['head_m'][1]+=.05
   f=folder/row['pose_draft_file'];f.write_text(json.dumps(pose));row['pose_draft_sha256']=hashlib.sha256(f.read_bytes()).hexdigest();p=folder/'profile.json';p.write_text(json.dumps(profile))
   with self.assertRaisesRegex(ValueError,'stretches'):load_study(p,self.variant,self.body,1,ARGS.vehicle)
 def test_parent_rest_basis_roundtrip(self):
  rest=transform([[0,-1,0],[1,0,0],[0,0,1]],[.1,.2,.3]);parent_rest=transform([[1,0,0],[0,0,-1],[0,1,0]],[.4,.5,.6]);desired=transform([[1,0,0],[0,1,0],[0,0,1]],[.7,.8,.9]);parent_desired=transform([[0,0,1],[0,1,0],[-1,0,0]],[.2,.3,.4]);basis=local_basis(rest,desired,parent_rest,parent_desired);recovered=mm(mm(mm(parent_desired,inverse_rigid(parent_rest)),rest),basis)
  self.assertLess(max(abs(recovered[i][j]-desired[i][j])for i in range(4)for j in range(4)),1e-12)
if __name__=='__main__':unittest.main(argv=[__file__,*EXTRA])
