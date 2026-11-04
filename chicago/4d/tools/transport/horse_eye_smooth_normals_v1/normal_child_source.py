"""EXTERNAL eye-normal child source adapter; no active app selection or certificate.

Compose the immutable exact-e49 source admission with the independently checked
NORMAL-only bd443 child. Old constants, source receipts and collision policy are
not reassigned. Static/posed phases require the root-owned heavy slot.
"""
import hashlib,importlib.util,json,sys
from pathlib import Path
import numpy as np
MODE='eye_smooth_normals_v1'
PARENT_SHA='e49b6f1c9f7b70f1fcdf19fa7f6dddf54048b32256b4d8030d6238d6dfe79d49'
CANDIDATE_SHA='bd443df87b92d19266284cb9b52d30e791215cddf099876c774e9cfb5f5a79b6'
RECIPE_SHA='9a6c38e01c81ffd0d5ae262008e80fa3227fc5ab974bbfa66252ca0521717911'
GENERATOR_SHA='b174f165545f3c5eeb98e31dbc7b50637330d4eeeaa5e00ae9e6b9c45de343c8'
PHYSICAL_LOOP_SHA='a8515b35e18a058673fe330a127eba129851f324915858971e3b683bc4d259a1'
sha=lambda b:hashlib.sha256(b).hexdigest()

def need(ok,message):
 if not ok:raise ValueError(message)

def load_module(path,name):
 spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

class Sources:
 def __init__(self,app,study):
  self.app=Path(app).resolve();self.study=Path(study).resolve()
  sys.path.insert(0,str(self.app/'tools/transport/horse_upper_orbital_transition_v1'))
  import upper_orbital_source as parent
  need(parent.APP==self.app,'Actual parent source module must resolve to requested app')
  self.parent_mode=parent;self.parent=parent.Sources();self.__dict__.update({k:v for k,v in self.parent.__dict__.items() if k not in ('app','study')});self.raw=dict(self.parent.raw)
  generator_path=self.study/'generate_eye_smooth_normals_v1.py';recipe_path=self.study/'eye-smooth-normals-v1-recipe.json';candidate_path=self.study/'horse-sevket-eye-smooth-normals-v1.glb'
  generator_raw=generator_path.read_bytes();recipe_raw=recipe_path.read_bytes();child=candidate_path.read_bytes()
  need(sha(generator_raw)==GENERATOR_SHA and sha(recipe_raw)==RECIPE_SHA,'Exact reviewed child generator and recipe required')
  need(sha(child)==CANDIDATE_SHA and len(child)==4159196,'Exact bd443 NORMAL-only child required')
  self.generator=load_module(generator_path,'external_eye_normal_generator');self.recipe=json.loads(recipe_raw)
  self.raw.update({generator_path:generator_raw,recipe_path:recipe_raw,candidate_path:child})
  self.normal_parent_raw=self.parent.raw[parent.CANDIDATE];need(sha(self.normal_parent_raw)==PARENT_SHA,'Exact e49 source parent required')
  self.normal_structure=self.generator.inspect(self.normal_parent_raw,child,self.recipe)
  need(self.generator.derive(self.normal_parent_raw,self.recipe)==child,'Exact deterministic normal child derivation')
  self.doc,self.binary=parent.ancestor.read_glb(child)
  self.body_positions,self.body_indices,self.body=parent.ancestor.mesh(self.doc,self.binary,1)
  self.eye_positions,self.eye_indices,self.eye=parent.ancestor.mesh(self.doc,self.binary,2)
  need(np.array_equal(self.body,self.parent.body) and np.array_equal(self.eye,self.parent.eye),'Normal child cannot alter BODY or globe geometry')
  self.child_path=candidate_path
 def cheap_tables(self):
  self.parent.cheap_tables()
  return self.generator.inspect(self.normal_parent_raw,self.raw[self.child_path],self.recipe)
 def full_frozen_structure(self):
  return {'source_admission':MODE,'parent_exact_e49_ONLY':self.parent.full_frozen_structure(),'child_NORMAL_only':self.normal_structure,'old_certificate_transferred':False,'new_child_native129':'REQUIRED_UNRUN'}
 def unchanged(self):
  self.parent.unchanged()
  for p,b in self.raw.items():need(p.read_bytes()==b,'Protected source changed during new child proof: '+str(p))
  return True

def static(source):
 original=source.parent_mode.ancestor
 import socket_qualification as q
 import socket_geometry as g
 structure=source.full_frozen_structure();source.cheap_tables()
 comp=q.components(source,source.eye);allowed,ledger=q.source_interface_faces(source,comp)
 for side,c in comp.items():g.need(not q.proper_pairs(c.triangles,set(range(len(c.triangles))),source.crosses),'source_globe_self_intersection',side)
 baseline={j for i,j in q.globe_pairs(source.old_body,set(range(len(source.old_body))),source.eye,source.crosses)}
 rest=q.evaluate_frame(source,source.body,source.old_body,source.eye,source.eye,allowed,{'kind':'rest'},baseline)
 source.unchanged()
 return {'status':'NORMAL_CHILD_CURRENT_SOURCE_STATIC_ONLY_PASS','source_admission':MODE,'collision_mode':original.MODE,'candidate_sha256':CANDIDATE_SHA,'normal_parent_e49_sha256':PARENT_SHA,'collision_reference925_sha256':original.EXPECTED[original.PARENT],'recipe_sha256':RECIPE_SHA,'structure':structure,'rest':rest,'source_interface_faces':{str(k):sorted(v) for k,v in allowed.items()},'source_interface_ledger':ledger,'physical129':'UNRUN','posed129':'UNRUN','old_certificate_transferred':False,'source_adoption':False,'photographic_acceptance':False}
