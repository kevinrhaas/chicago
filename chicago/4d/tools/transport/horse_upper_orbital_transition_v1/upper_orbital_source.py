"""Distinct explicit BODY ridge admission, composed with frozen5a source proof.

The unchanged collision policy remains canonical_socket_interface_v1. Old5a
frozen-boundary checks apply ONLY to the parent, never to the expanded child.
"""
import json,sys
from pathlib import Path
import numpy as np
APP=Path(__file__).resolve().parents[3]
SOURCE=APP/'assets/authored/transport/horse_standing'
OLD=APP/'tools/transport/horse_socket_interface_v1'
sys.path.insert(0,str(OLD));sys.path.insert(0,str(SOURCE))
import socket_sources as ancestor
import socket_geometry as g
import generate_upper_orbital_transition_v1 as generator
MODE='upper_orbital_transition_v1'
CANDIDATE=SOURCE/'horse-sevket-upper-orbital-transition-v1.glb'
RECIPE=SOURCE/'upper-orbital-transition-v1-recipe.json'
CERTIFICATE=APP/'data/transport/parked/standing-horse-planted/upper-orbital-transition-v1-qualification-summary.json'
CERTIFICATE_SHA='72506859017d1f1aea57ad248d877a88bb07e701d4ec82c31e509dbb97e8d7a0'

def verify_recorded_certificate(c):
    g.need(c['schema']=='standing-horse-upper-orbital-qualification-summary-v1'and c['status']=='RECORDED_EXACT_E49B_STATIC_NATIVE_PHYSICAL_SOCKET129_ONLY_PASS','orbital_recorded_scope')
    g.need(c['source_admission']==MODE and c['collision_mode']==ancestor.MODE and c['candidate_sha256']==generator.CANDIDATE_SHA and c['parent5a_sha256']==generator.PARENT_SHA and c['recipe_sha256']==generator.RECIPE_SHA,'orbital_recorded_source')
    g.need(c['candidate_bytes']==4159196 and c['physical_loop_bytes']==9176 and c['physical_loop_sha256']==ancestor.PHYSICAL_LOOP_SHA and c['limits_m']=={'BODY_locus':.014,'globe_contact_locus':.007,'source_and_parent_displacement':.020},'orbital_recorded_limits')
    limits=json.loads((ancestor.PACKET/'ORIGINAL-PHYSICAL-LIMITS.json').read_bytes())
    g.need(c['original_physical_limits']==limits and c['actual_native_physical']['original_physical_limits']==limits,'orbital_original_physical_limits')
    rows=c['all129_socket_samples'];g.need(len(rows)==129,'orbital_recorded_pose_inventory')
    for i,r in enumerate(rows):
        g.need(r['index']==i and r['time_s']==i*3/32 and r['key']==(i//2 if i%2==0 else None),'orbital_recorded_pose_grid')
        g.need(r['BODY_pairs']==24 and r['globe_contacts']==82 and 0<=r['BODY_max_upper_m']<=.014 and 0<=r['CONTACT_max_upper_m']<=.007 and r['new_exterior_or_undeclared_or_patch_patch_crossings']==0,'orbital_recorded_pose_limits')
    p=c['actual_native_physical'];g.need(p['status']=='LOADED_STANDING65_KEYS64_MIDPOINTS_PASS_ONLY'and p['key_count']==65 and p['midpoint_count']==64 and p['failures']==[],'orbital_recorded_physical')
    g.need(c['actual_Float64_raw_bytes']==59214096 and c['actual_Float64_values']==7401762 and c['actual_code_pins']['socket_geometry.py']=='41c4394cbf3f415c2e7cc4c362b3652d736ba2ccb04a920b4cfb0b3c1a3764a8','orbital_recorded_precision_or_geometry')
    g.need(set(c['closed_runs'])=={'static','native129','posed129'},'orbital_recorded_closure_inventory')
    for r in c['closed_runs'].values():g.need(type(r['returncode'])is int and r['returncode']==0 and r['cleanup_complete']is True and r['remaining_owned_children']==[],'orbital_recorded_closure')
    g.need(c['old_strict_rejection_remains_rejected']is True and c['old5a129_not_transferred']is True and c['new_e49b129_actually_executed']is True and c['photographic_acceptance']is False and c['whole_T3088_closed']is False and c['whole_app_gate_acceptance']is False,'orbital_recorded_overclaim')
    return True

class Sources:
    def __init__(self):
        self.base=ancestor.Sources();self.__dict__.update(self.base.__dict__);self.raw=dict(self.base.raw)
        for p,h in [(CANDIDATE,generator.CANDIDATE_SHA),(RECIPE,generator.RECIPE_SHA),(CERTIFICATE,CERTIFICATE_SHA)]:
            self.raw[p]=p.read_bytes();g.need(ancestor.sha(self.raw[p])==h,'orbital_source_binding',str(p))
        self.certificate=json.loads(self.raw[CERTIFICATE]);verify_recorded_certificate(self.certificate)
        self.brow_recipe=json.loads(self.raw[RECIPE]);self.doc,self.binary=ancestor.read_glb(self.raw[CANDIDATE]);self.child_structure=generator.inspect(self.base.raw[ancestor.CANDIDATE],self.raw[CANDIDATE],self.raw[RECIPE],self.raw[ancestor.ORIGINAL],self.raw[ancestor.PARENT])
        self.body_positions,self.body_indices,self.body=ancestor.mesh(self.doc,self.binary,1);self.eye_positions,self.eye_indices,self.eye=ancestor.mesh(self.doc,self.binary,2)
        self.side_for=dict(self.base.side_for)
        for face in self.brow_recipe['affected_faces']:
            if face not in self.side_for:
                side=1 if self.old_body[face,:,0].mean()>0 else -1;g.need(np.all(self.old_body[face,:,0]*side>0),'orbital_original_face_side');self.side_for[face]=side
        self.patch=set(self.side_for);g.need(len(self.patch)==178,'orbital_exact178_scan_faces')
        outside=sorted(set(range(len(self.body)))-self.patch);g.need(np.array_equal(self.body[outside],self.old_body[outside]),'orbital_outside_positions')
        protected=sorted(set().union(*ancestor.EXPECTED_INTERFACE.values()));g.need(np.array_equal(self.body[protected],self.old_body[protected]),'orbital_original20_interface_faces')
        self.cheap_tables()
    def cheap_tables(self):
        result=ancestor.uv_skin_guard(self.doc,self.binary,self.parent_doc,self.parent_bin,self.recipe);ancestor.original_prefix_guard(self.binary,self.original_bin)
        generator.inspect(self.base.raw[ancestor.CANDIDATE],self.raw[CANDIDATE],self.raw[RECIPE],self.raw[ancestor.ORIGINAL],self.raw[ancestor.PARENT]);return result
    def full_frozen_structure(self):
        return {'source_admission':MODE,'parent5a_frozen_structure_ONLY':self.base.full_frozen_structure(),'child_explicit_region':self.child_structure,'old_frozen_boundary_not_applied_to_child':True,'recorded_exact_new_child129':True,'native129_rerun_by_source_check':False}
    def unchanged(self):
        self.base.unchanged()
        for p,raw in self.raw.items():g.need(p.read_bytes()==raw,'orbital_source_changed',str(p))
        return True
