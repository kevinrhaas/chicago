"""Read exact newly executed canonical NORMAL-child proof; no external files.

This separate record reader is outside the fourteen qualifying executables to
avoid embedding a future certificate self-hash into its own producer code pins.
"""
from pathlib import Path
import hashlib,json
import normal_child_source as child
import qualify_normal_child as qualification
APP=Path(__file__).resolve().parents[3]
SOURCE=APP/'assets/authored/transport/horse_standing'
CERTIFICATE=APP/'data/transport/parked/standing-horse-planted/eye-smooth-normals-v1-qualification-summary.json'
CERTIFICATE_SHA='e730f59fdbf32db6a02270b62b96c2f0d75b4f465cdbe1fda4a957cfa8530342'
RUNTIME_FILE='transport/standing-horse/horse-sevket-eye-smooth-normals-v1.glb'
MODE=child.MODE
need=child.need

def verify_recorded_certificate(c):
 need(c['schema']=='standing-horse-eye-smooth-normals-qualification-summary-v1'and c['status']=='EXACT_BD443_STATIC_NATIVE_PHYSICAL_SOCKET129_ONLY_PASS','normal_certificate_scope')
 need(c['source_admission']==MODE and c['collision_mode']=='canonical_socket_interface_v1','normal_certificate_mode')
 need(c['candidate_sha256']==child.CANDIDATE_SHA and c['candidate_bytes']==4159196 and c['normal_parent_e49_sha256']==child.PARENT_SHA and c['recipe_sha256']==child.RECIPE_SHA and c['generator_sha256']==child.GENERATOR_SHA,'normal_certificate_source')
 need(c['actual_code_pins']==qualification.code_pins(),'normal_certificate_executing_canonical14')
 need(c['physical_loop_bytes']==9176 and c['physical_loop_sha256']==child.PHYSICAL_LOOP_SHA,'normal_certificate_original_loop')
 limits=json.loads((APP/'tools/transport/horse_socket_interface_v1/fixtures/ORIGINAL-PHYSICAL-LIMITS.json').read_bytes())
 need(c['limits_m']=={'BODY_locus':.014,'globe_contact_locus':.007,'source_and_parent_displacement':.020}and c['original_physical_limits']==limits,'normal_certificate_fixed_limits')
 rows=c['all129_socket_samples'];need(len(rows)==129,'normal_certificate_complete129')
 for i,row in enumerate(rows):
  need(type(row['index'])is int and row['index']==i and row['time_s']==i*3/32 and row['key']==(i//2 if i%2==0 else None),'normal_certificate_pose_grid')
  need(row['BODY_pairs']==24 and row['globe_contacts']==82 and 0<=row['BODY_max_upper_m']<=.014 and 0<=row['CONTACT_max_upper_m']<=.007 and row['new_exterior_or_undeclared_or_patch_patch_crossings']==0,'normal_certificate_pose_limits')
 p=c['actual_native_physical'];need(p['status']=='LOADED_STANDING65_KEYS64_MIDPOINTS_PASS_ONLY'and p['key_count']==65 and p['midpoint_count']==64 and p['failures']==[] and p['original_physical_limits']==limits,'normal_certificate_actual_physical129')
 need(p['WebGL_contexts_created']==0 and p['renderers_created']==0 and c['actual_WebGL_context_requests']==0 and c['actual_WebGL_contexts_created']==0,'normal_certificate_no_WebGL')
 need(c['actual_Float64_raw_bytes']==59214096 and c['actual_Float64_values']==7401762,'normal_certificate_Float64_inventory')
 need(set(c['closed_runs'])=={'static','native129','posed129'},'normal_certificate_phase_inventory')
 for r in c['closed_runs'].values():need(type(r['returncode'])is int and r['returncode']==0 and r['cleanup_complete']is True and r['remaining_owned_children']==[],'normal_certificate_owned_closure')
 for name in ['static','capture','capture_manifest','posed129','outer_guards']:
  r=c['actual_receipts'][name];need(type(r['bytes'])is int and r['bytes']>0 and len(r['sha256'])==64 and set(r['sha256'])<=set('0123456789abcdef'),'normal_certificate_receipt_binding')
 need(c['old_certificate_transferred']is False and c['new_bd443_129_actually_executed']is True and c['old_e49_and_5a_source_and_proofs_unchanged']is True,'normal_certificate_no_parent_transfer')
 need(c['photographic_acceptance']is False and c['whole_T3088_closed']is False and c['whole_app_gate_acceptance']is False and c['native_organic_world_comparison']=='UNRUN','normal_certificate_no_visual_overclaim')
 return True

def read_certificate():
 raw=CERTIFICATE.read_bytes();need(hashlib.sha256(raw).hexdigest()==CERTIFICATE_SHA,'normal_certificate_exact_record');c=json.loads(raw);verify_recorded_certificate(c);return c

def check_source_selection():
 source=child.Sources(APP,SOURCE);source.cheap_tables();cert=read_certificate();spec=json.loads((APP/'data/transport/parked/horse-sevket-sidecar.json').read_bytes());runtime=spec['runtime_asset']
 need(runtime['file']==RUNTIME_FILE and runtime['sha256']==child.CANDIDATE_SHA and runtime['bytes']==4159196 and runtime['source_qualification_mode']==MODE,'normal_selected_source_identity')
 need(runtime['qualification_sha256']==CERTIFICATE_SHA and runtime['qualification_file']=='transport/parked/standing-horse-planted/eye-smooth-normals-v1-qualification-summary.json','normal_selected_certificate')
 need(runtime['normal_parent_e49_sha256']==child.PARENT_SHA and (APP/'renderers/web'/runtime['file']).read_bytes()==source.raw[source.child_path],'normal_selected_runtime_copy')
 authored=json.loads((SOURCE/'SOURCE.json').read_bytes());need(authored['runtime_derivative']==runtime,'normal_authored_active_binding')
 parent=spec['preserved_upper_orbital_runtime_asset'];need(parent['sha256']==child.PARENT_SHA and parent['source_qualification_mode']=='upper_orbital_transition_v1'and authored['preserved_upper_orbital_parent_derivative']==parent,'normal_preserved_actual_e49_parent')
 need(spec['surface_refinement']['liberty']=='L-horse-eye-smooth-normals-3088'and spec['surface_refinement']['normal_rows']==3968,'normal_active_surface_liberty')
 idle=spec['idle'];need(idle['loaded_qualification_asset_sha256']==child.CANDIDATE_SHA and idle['loaded_qualification_sha256']==CERTIFICATE_SHA and idle['loaded_qualification_file']==runtime['qualification_file']and idle['loaded_qualification_status']==cert['status'],'normal_active_idle_record')
 need(idle['loaded_raw_result_sha256']==cert['actual_receipts']['capture']['sha256']and idle['loaded_capture_manifest_sha256']==cert['physical_capture_manifest_sha256']and idle['loaded_posed_result_sha256']==cert['actual_receipts']['posed129']['sha256'],'normal_active_idle_actual_capture')
 need(idle['physical129_rerun_in_current_recovery']is True and idle['external_raw_capture_arrays_available']is True and idle['qualification_recorded_on']=='2026-10-29','normal_active_idle_current_scope')
 placements=json.loads((APP/'data/transport/parked/standing-horses.json').read_bytes());need(placements['models']['sevket_horse_standing_development_01']['file']==RUNTIME_FILE,'normal_actual_placement_model')
 source.unchanged();return source
