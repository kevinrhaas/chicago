#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Source-to-preparation invariants on the real pinned hm08 body, not a fake mesh."""
import math,unittest,json,pathlib,tempfile,gzip,hashlib,io
import human_base_prepare as prep
from unittest import mock
class SourcePreparation(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.data=prep.prepare(prep.DEFAULT,1.75);cls.mesh=cls.data['meshes'][0]
 def test_body_corner_uv_correspondence(self):
  # Check every output face corner against the actual original polygon's vertex
  # and UV IDs. This catches helper leakage, UV welding and triangle winding drift.
  raw,uvs,faces,groups=prep.read_obj(prep.DEFAULT/'makehuman/data/3dobjs/base.obj');m=self.mesh;cursor=0
  for face in faces:
   for j in range(1,len(face)-1):
    tri=m['triangles'][cursor];cursor+=1
    for out_index,(vi,ti) in zip(tri,[face[0],face[j],face[j+1]]):
     self.assertEqual(m['source_vertex_indices'][out_index],vi);self.assertEqual(m['uvs'][out_index],uvs[ti])
  self.assertEqual(cursor,len(m['triangles']));self.assertEqual(cursor,26756)
  self.assertGreater(self.data['report']['source_uv_seam_vertices'],1000)
 def test_metric_frame_and_joint_contract(self):
  m=self.mesh;p=m['positions_m'];self.assertAlmostEqual(min(v[1] for v in p),0,places=12);self.assertAlmostEqual(max(v[1] for v in p),1.75,places=12)
  bones={b['name']:b for b in self.data['skeleton']};self.assertEqual(len(bones),56);self.assertEqual(bones['root']['head_m'],[0,0,0])
  for side,sign in [('l',1),('r',-1)]:
   for family in ['upperarm','lowerarm','hand']:
    b=bones[family+'_'+side];d=prep.sub(b['tail_m'],b['head_m']);self.assertLess(abs(d[1])+abs(d[2]),1e-10);self.assertGreater(sign*d[0],0)
   for family in ['thigh','calf']:
    b=bones[family+'_'+side];d=prep.sub(b['tail_m'],b['head_m']);self.assertLess(abs(d[0])+abs(d[2]),1e-10);self.assertLess(d[1],0)
   self.assertGreater(bones['ball_'+side]['tail_m'][2],bones['foot_'+side]['head_m'][2])
  for b in bones.values():
   self.assertGreater(prep.norm(prep.sub(b['tail_m'],b['head_m'])),1e-6)
 def test_weight_integrity_and_quantified_loss(self):
  allowed={b['name'] for b in self.data['skeleton']}
  for p,w in zip(self.mesh['positions_m'],self.mesh['weights']):
   self.assertTrue(all(math.isfinite(v) for v in p));self.assertLessEqual(len(w),4);self.assertTrue(set(w)<=allowed);self.assertAlmostEqual(sum(w.values()),1,places=12);self.assertTrue(all(v>0 for v in w.values()))
  r=self.data['report'];self.assertGreater(r['pruned_vertices'],0);self.assertGreater(r['discarded_weight_max'],0);self.assertGreater(r['pruning_pose_displacement_max_m'],0);self.assertEqual(len(self.data['source_bone_map']),163)
 def test_height_sensitivity_and_repeatability(self):
  other=prep.prepare(prep.DEFAULT,1.85);self.assertAlmostEqual(other['report']['height_m'],1.85,places=12)
  self.assertEqual(prep.prepare(prep.DEFAULT,1.75),self.data)
  for a,b in zip(self.mesh['positions_m'][::200],other['meshes'][0]['positions_m'][::200]):
   for av,bv in zip(a,b):self.assertAlmostEqual(av*1.85/1.75,bv,places=10)
 def test_prepared_bytes_are_independent_of_legacy_float_sum(self):
  # The first real CI run failed neutral byte 40084 on Python 3.11. Emulate
  # its left-fold sum and require all actual pinned body recipes to retain
  # their exact committed bytes, rather than accepting a geometry tolerance.
  def legacy_sum(values,start=0):
   total=start
   for value in values:total+=value
   return total
  for age in [None,25,35]:
   stem='prepared' if age is None else 'prepared_adult_'+str(age)
   recipe=None if age is None else prep.DEFAULT/('adult_'+str(age)+'.recipe.json')
   with mock.patch.object(prep,'sum',legacy_sum,create=True):
    actual=prep.prepare(prep.DEFAULT,1.75,recipe)
   encoded=(json.dumps(actual,separators=(',',':'))+'\n').encode()
   self.assertEqual(encoded,(prep.DEFAULT/(stem+'.json')).read_bytes(),stem)
class TargetPreparation(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  global P
  P=prep.DEFAULT
  cls.a=json.loads((P/'prepared_adult_25.json').read_text());cls.b=json.loads((P/'prepared_adult_35.json').read_text());cls.base=json.loads((P/'prepared.json').read_text())
 def test_helpers_recomputed_from_actual_blended_graphical_data(self):
  recipe=json.loads((P/'adult_25.recipe.json').read_text());raw,uv,faces,groups=prep.read_obj(P/'makehuman/data/3dobjs/base.obj')
  # Independent sparse-delta application and helper averaging; compare the actual
  # authored upper/lower arm anchor separation, which cancels ground translation.
  for row in recipe['targets']:
   for line in (P/row['path']).read_text().splitlines():
    if not line.strip()or line.startswith('#'):continue
    fields=line.split();i=int(fields[0]);raw[i]=[raw[i][k]+float(fields[k+1])*row['coefficient']for k in range(3)]
  rig=json.loads((P/'makehuman/data/rigs/default.mhskel').read_text())
  def head(n):
   ids=rig['joints'][rig['bones'][n]['head']];return [sum(raw[i][k]for i in ids)/len(ids)for k in range(3)]
  expected=prep.sub(head('lowerarm01.L'),head('upperarm01.L'));scale=self.a['report']['initial_source_scale']*self.a['report']['final_registration_scale'];bones={b['name']:b for b in self.a['skeleton']};actual=prep.sub(bones['lowerarm_l']['source_head_m'],bones['upperarm_l']['source_head_m'])
  for a,b in zip(actual,expected):self.assertAlmostEqual(a,b*scale,places=10)
  self.assertEqual(self.a['target_blend']['changed_helper_vertices'],1117)
 def test_ages_are_distinct_without_topology_uv_or_weight_drift(self):
  a,b,base=[j['meshes'][0]for j in [self.a,self.b,self.base]]
  for field in ['triangles','uvs','weights','source_vertex_indices']:self.assertEqual(a[field],base[field]);self.assertEqual(b[field],base[field])
  self.assertGreater(max(math.dist(x,y)for x,y in zip(a['positions_m'],base['positions_m'])),.05)
  self.assertGreater(max(math.dist(x,y)for x,y in zip(a['positions_m'],b['positions_m'])),.005)
  for j in [self.a,self.b]:self.assertAlmostEqual(j['report']['height_m'],1.75);self.assertEqual(j['report']['ground_min_y_m'],0);self.assertEqual(j['report']['zero_area_triangles'],0)
 def test_recipe_hash_and_band_are_required(self):
  r=json.loads((P/'adult_25.recipe.json').read_text())
  with tempfile.TemporaryDirectory()as d:
   f=pathlib.Path(d)/'bad.json';r['targets'][0]['sha256']='0'*64;f.write_text(json.dumps(r))
   with self.assertRaises(ValueError):prep.prepare(P,1.75,f)
   r=json.loads((P/'adult_25.recipe.json').read_text());r['phenotype']['chosen_age_years']=45;f.write_text(json.dumps(r))
   with self.assertRaises(ValueError):prep.prepare(P,1.75,f)
 def test_target_bytes_are_rehashed_before_applying(self):
  recipe=json.loads((P/'adult_25.recipe.json').read_text());provenance=json.loads((P/'SOURCE.json').read_text());raw,_,_,_=prep.read_obj(P/'makehuman/data/3dobjs/base.obj')
  with tempfile.TemporaryDirectory()as d:
   source=pathlib.Path(d);row=recipe['targets'][0];target=source/row['path'];target.parent.mkdir(parents=True);target.write_bytes((P/row['path']).read_bytes()+b'\n# tampered bytes\n')
   with self.assertRaisesRegex(ValueError,'target checksum mismatch'):prep.apply_graphical_targets(raw,source,provenance,P/'adult_25.recipe.json')

class PackedSourceNotice(unittest.TestCase):
 def test_verbatim_pinned_notice_and_deterministic_archive(self):
  manifest=json.loads((prep.DEFAULT/'SOURCE.json').read_text());row=next(r for r in manifest['files']if r.get('upstream_path')=='LICENSE.md')if any('upstream_path'in r for r in manifest['files'])else None
  self.assertIsNotNone(row);decoded=prep.verify_source_row(prep.DEFAULT,row)
  self.assertEqual(hashlib.sha256(decoded).hexdigest(),'edd99571ca62698f78c943fd4fffb159a413c315fa0d4819d3cec5cadaf8b4f1')
  self.assertTrue(decoded.startswith(b'LICENSE\n=======\n'));out=io.BytesIO()
  with gzip.GzipFile(filename='',mode='wb',fileobj=out,mtime=0)as f:f.write(decoded)
  self.assertEqual(out.getvalue(),(prep.DEFAULT/row['path']).read_bytes())
 def test_stored_and_decoded_tampering_rejected(self):
  manifest=json.loads((prep.DEFAULT/'SOURCE.json').read_text());row=dict(next(r for r in manifest['files']if r.get('compression')=='gzip'));original=(prep.DEFAULT/row['path']).read_bytes()
  with tempfile.TemporaryDirectory()as d:
   folder=pathlib.Path(d);f=folder/row['path'];f.write_bytes(original+b'tamper')
   with self.assertRaisesRegex(ValueError,'stored source checksum mismatch'):prep.verify_source_row(folder,row)
   modified=gzip.compress(gzip.decompress(original)+b'changed upstream notice',mtime=0);f.write_bytes(modified);row['stored_sha256']=hashlib.sha256(modified).hexdigest();row['stored_bytes']=len(modified)
   with self.assertRaisesRegex(ValueError,'decoded source checksum mismatch'):prep.verify_source_row(folder,row)

if __name__=='__main__':unittest.main()
