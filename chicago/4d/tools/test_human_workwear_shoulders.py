#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Connected shoulder topology on real frozen source; no Blender/export/browser."""
import collections,copy,hashlib,json,math,pathlib,sys,unittest
sys.dont_write_bytecode=True
from human_workwear_fit import garment_shell
ROOT=pathlib.Path(__file__).resolve().parent.parent
class ConnectedShoulders(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.body=json.loads((ROOT/'assets/authored/humans/makehuman_hm08/prepared_adult_25.json').read_bytes())
  cls.mesh=cls.body['meshes'][0];cls.bones={b['name']:b for b in cls.body['skeleton']}
  cls.recipe=json.loads((ROOT/'data/humans/recipes/worker_1835.json').read_bytes())
  cls.pattern=cls.recipe['proof_variants'][0]['waistcoat_shoulder_pattern']
  cls.before=copy.deepcopy(cls.body)
  cls.default=garment_shell(cls.mesh,'waistcoat',cls.recipe['waistcoat_offset_m'],cls.recipe,cls.bones,1.75)
  cls.configured={**cls.recipe,'waistcoat_shoulder_pattern':cls.pattern}
  cls.proposed=garment_shell(cls.mesh,'waistcoat',cls.recipe['waistcoat_offset_m'],cls.configured,cls.bones,1.75)
 def test_original_absence_and_connected_repair(self):
  global src
  src={sid:p for sid,p in zip(self.mesh['source_vertex_indices'],self.mesh['positions_m'])}
  self.assertTrue(all(not r['path_above1_38m'] for r in bridges(self.default)))
  self.assertTrue(all(r['path_above1_38m'] for r in bridges(self.proposed)))
 def test_variant_scope_and_input_preservation(self):
  variants=self.recipe['proof_variants']
  self.assertEqual([v['id'] for v in variants if 'waistcoat_shoulder_pattern' in v],['bardwell_otis_1835'])
  self.assertNotIn('waistcoat_shoulder_pattern',self.default['receipt'])
  self.assertEqual(self.body,self.before)
  self.assertFalse(self.proposed['receipt']['body_mutated'])
  self.assertFalse(self.proposed['receipt']['fit_accepted'])
 def test_original_uv_and_bounded_skin_contract(self):
  g=self.proposed
  self.assertEqual(len(g['corner_uvs']),len(g['triangles']))
  self.assertLessEqual(g['receipt']['maximum_discarded_cut_weight'],.025)
  self.assertLess(max(sum(w.get(b,0) for b in ('head','jaw')) for w in g['weights']),.025)
  for weight in g['weights']:
   self.assertLessEqual(len(weight),4);self.assertAlmostEqual(sum(weight.values()),1,places=12)
 def test_bad_pattern_refused(self):
  for change in [{'id':'unsupported'},{'neckline_drop_m':-1}]:
   recipe={**self.recipe,'waistcoat_shoulder_pattern':{**self.pattern,**change}}
   with self.assertRaises(ValueError):garment_shell(self.mesh,'waistcoat',self.recipe['waistcoat_offset_m'],recipe,self.bones,1.75)
def raw_positions(g):return [[math.fsum(src[sid][a]*w for sid,w in basis.items()) for a in range(3)] for basis in g['source_basis']]
def bridges(g):
 raw=raw_positions(g);adj=collections.defaultdict(set)
 for face in g['triangles']:
  for a,b in zip(face,face[1:]+face[:1]):adj[a].add(b);adj[b].add(a)
 rows=[]
 for side in [-1,1]:
  allowed={i for i,p in enumerate(raw) if p[1]>=1.38 and .04<=side*p[0]<=.18}
  front={i for i in allowed if raw[i][2]>.005 and raw[i][1]>=1.41}
  back={i for i in allowed if raw[i][2]<-.015 and raw[i][1]>=1.41}
  visited=set(front);todo=collections.deque(front)
  while todo:
   i=todo.popleft()
   for j in adj[i]&allowed:
    if j not in visited:visited.add(j);todo.append(j)
  rows.append({'side':side,'front_upper_vertices':len(front),'back_upper_vertices':len(back),'path_above1_38m':bool(visited&back),'upper_allowed_vertices':len(allowed)})
 return rows

if __name__=='__main__':unittest.main()
