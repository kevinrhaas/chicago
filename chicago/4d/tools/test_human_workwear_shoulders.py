#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Connected shoulder topology on real frozen source; no Blender/export/browser."""
import collections,copy,hashlib,json,math,pathlib,sys,unittest
sys.dont_write_bytecode=True
from human_workwear_fit import garment_shell, standing_collar_extension
from human_period_wardrobe import (resolve_wardrobe, finish_edges, waistcoat_buttons,
                                  round_jacket, work_hat)
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


class PeriodWardrobeConstruction(unittest.TestCase):
 """Real adult25/35 assemblies; source construction is not export/photo proof."""
 @classmethod
 def setUpClass(cls):
  from human_hair_short04 import fit
  cls.recipe=json.loads((ROOT/'data/humans/recipes/worker_1835.json').read_bytes())
  cls.rows=[]
  for variant in cls.recipe['proof_variants']:
   raw=(ROOT/variant['body_input']).read_bytes();body=json.loads(raw)
   before=copy.deepcopy(body);bones={b['name']:b for b in body['skeleton']}
   recipe,profile=resolve_wardrobe(cls.recipe,variant)
   profile['body_height_m']=variant['body_parameters']['chosen_height_m']
   hair,_,_=fit(body,recipe['hair_component'],ROOT)
   vest=garment_shell(body['meshes'][0],'waistcoat',recipe['waistcoat_offset_m'],recipe,bones,profile['body_height_m'])
   finished=finish_edges(vest,recipe['modular_wardrobe']['edge_thickness_m'])
   jacket=round_jacket(body['meshes'][0],bones,recipe,profile['body_height_m'],profile)
   if jacket:jacket=finish_edges(jacket,recipe['modular_wardrobe']['edge_thickness_m'])
   shirt=garment_shell(body['meshes'][0],'shirt',recipe['shirt_offset_m'],recipe,bones,profile['body_height_m'])
   shirt=standing_collar_extension(shirt,body['meshes'][0],bones,recipe)
   trousers=garment_shell(body['meshes'][0],'trousers',recipe['trouser_offset_m'],recipe,bones,profile['body_height_m'])
   garments=[finish_edges(g,recipe['modular_wardrobe']['edge_thickness_m']) for g in (shirt,trousers)]
   cls.rows.append(dict(variant=variant,body=body,before=before,bones=bones,recipe=recipe,
                        profile=profile,hair=hair,vest=vest,finished=finished,jacket=jacket,garments=garments))
 @staticmethod
 def uv_area(uv):
  a,b,c=uv;return abs((b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0]))
 def assert_component(self,mesh,closed=False):
  self.assertTrue(mesh['triangles']);self.assertEqual(len(mesh['triangles']),len(mesh['corner_uvs']))
  for face,uv in zip(mesh['triangles'],mesh['corner_uvs']):
   self.assertEqual(len(set(face)),3)
   a,b,c=[mesh['positions_m'][i] for i in face]
   u=[b[i]-a[i] for i in range(3)];v=[c[i]-a[i] for i in range(3)]
   self.assertGreater(math.hypot(u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]),1e-16)
   self.assertGreater(self.uv_area(uv),1e-18)
   self.assertTrue(all(math.isfinite(x) and -1e-12<=x<=1+1e-12 for p in uv for x in p))
  for weight in mesh['weights']:
   self.assertLessEqual(len(weight),4);self.assertAlmostEqual(math.fsum(weight.values()),1,places=12)
  if closed:
   edges=collections.Counter(tuple(sorted((a,b))) for face in mesh['triangles'] for a,b in zip(face,face[1:]+face[:1]))
   self.assertEqual(set(edges.values()),{2})
 def test_three_distinct_existing_resident_assemblies_and_unchanged_anatomy(self):
  self.assertEqual(len({r['variant']['wardrobe_assembly'] for r in self.rows}),3)
  self.assertEqual({r['variant']['person_reference_id'] for r in self.rows},
                   {'rc_bardwell_otis','rc_dufresne_joseph','rc_flynn_martin'})
  for r in self.rows:
   self.assertEqual(r['body'],r['before']);self.assertEqual(r['profile']['grade'],'reconstructed')
 def test_actual_return_geometry_keeps_original_vertices_faces_weights_and_corner_uvs(self):
  for r in self.rows:
   old,new=r['vest'],r['finished'];n=len(old['positions_m']);f=len(old['triangles'])
   for key in ['positions_m','weights','uvs','source_basis']:self.assertEqual(new[key][:n],old[key])
   for key in ['triangles','corner_uvs']:self.assertEqual(new[key][:f],old[key])
   self.assertGreater(len(new['triangles']),f);self.assert_component(new)
   for garment in r['garments']:self.assert_component(garment)
 def test_adult35_original_clamped_hem_fails_return_and_continuous_ease_repairs_it(self):
  r=self.rows[1];legacy={k:v for k,v in r['recipe'].items() if k!='modular_wardrobe'}
  old=garment_shell(r['body']['meshes'][0],'waistcoat',legacy['waistcoat_offset_m'],legacy,r['bones'],r['profile']['body_height_m'])
  with self.assertRaisesRegex(ValueError,'undefined garment edge normal'):finish_edges(old,.0015)
  self.assert_component(r['finished'])
 def test_closed_buttons_and_hats_all_four_lods(self):
  for r in self.rows:
   for lod in range(4):
    buttons=waistcoat_buttons(r['vest'],r['bones'],r['recipe'],r['profile'],lod)
    self.assert_component(buttons,closed=True)
    hat=work_hat(r['hair'],r['bones'],r['profile'],lod)
    if hat:
     self.assert_component(hat,closed=True)
     self.assertTrue(all(w=={'head':1.} for w in hat['weights']))
 def test_jackets_have_connected_folded_lapels_and_actual_uv_surfaces(self):
  jackets=[r['jacket'] for r in self.rows if r['jacket']]
  self.assertEqual(len(jackets),2)
  for jacket in jackets:
   self.assertGreater(jacket['receipt']['connected_lapel_edges'],0)
   self.assert_component(jacket)
 def test_bad_thickness_degenerate_source_uv_and_detached_button_negative_controls(self):
  r=self.rows[0]
  for thickness in [0,-.001,.01]:
   with self.assertRaises(ValueError):finish_edges(r['vest'],thickness)
  bad=copy.deepcopy(r['vest']);bad['corner_uvs']=[[[.5,.5]]*3 for _ in bad['triangles']]
  with self.assertRaisesRegex(ValueError,'degenerate UV'):finish_edges(bad,.0015)
  bad=copy.deepcopy(r['vest'])
  for p in bad['positions_m']:p[1]+=3
  with self.assertRaisesRegex(ValueError,'no actual garment surface'):
   waistcoat_buttons(bad,r['bones'],r['recipe'],r['profile'],0)
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
