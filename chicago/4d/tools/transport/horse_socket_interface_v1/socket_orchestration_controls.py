"""Focused authorizer/grid/precision controls. No fullmesh or browser execution."""
import argparse,copy,json,tempfile,time
from pathlib import Path
import socket_geometry as g
import socket_sources as s
import socket_qualification as q
ROOT=Path(__file__).resolve().parent

def run(out):
 started=time.monotonic();g.need(not out.exists(),'fresh_control_output_required');results={}
 def refused(name,reason,fn):
  try:fn()
  except g.Rejected as error:
   assert error.code==reason,(name,error.code,reason);results[name]={'actually_rejected':True,'reason':error.code}
  else:raise AssertionError('Corruption unexpectedly accepted: '+name)
 policy=q.policy_expected(s.EXPECTED_INTERFACE);assert q.verify_policy(policy,s.EXPECTED_INTERFACE);results['bound_policy_positive']={'passed':True}
 fake=copy.deepcopy(policy);fake['inherited_pairs']=[[3782,999]]
 refused('actual_fake_inherited_pair_entry_injected','forbidden_replacement_face_ancestry_declaration',lambda:q.verify_policy(fake,s.EXPECTED_INTERFACE))
 fake=copy.deepcopy(policy);fake['face_ancestry']={'new_slot_1':'old3782'}
 refused('actual_fictitious_replacement_face_ancestry_injected','forbidden_replacement_face_ancestry_declaration',lambda:q.verify_policy(fake,s.EXPECTED_INTERFACE))
 fake=copy.deepcopy(policy);fake['unchanged_original_interface_faces']['1'].append(999)
 refused('additional_undeclared_interface_face','source_interface_policy_mismatch',lambda:q.verify_policy(fake,s.EXPECTED_INTERFACE))
 fake=copy.deepcopy(policy);fake['unchanged_original_interface_faces']['1'][0]=3782
 refused('wrong_side_original_interface_face','source_interface_policy_mismatch',lambda:q.verify_policy(fake,s.EXPECTED_INTERFACE))
 fake=copy.deepcopy(policy);fake['body_locus_limit_m']=.0140001
 refused('automatic_bound_increase','source_interface_policy_mismatch',lambda:q.verify_policy(fake,s.EXPECTED_INTERFACE))
 manifest={'schema':'canonical_socket_native129_capture_v1','physical_loop_sha256':s.PHYSICAL_LOOP_SHA,'parent_sha256':s.EXPECTED[s.PARENT],'candidate_sha256':s.EXPECTED[s.CANDIDATE],'coordinate_frame':'native_getVertexPosition_identity_mesh_bind_canonical_metres','frames':[{'index':i,'time_s':i*3/32,'key':i//2 if i%2==0 else None}for i in range(129)]}
 assert len(q.verify_pose_grid(manifest))==129;results['exact129_grid_positive']={'passed':True,'keys':65,'midpoints':64,'scope':'Manifest traversal/precision controls, not actual native capture or posed mesh qualification.'}
 corrupt=copy.deepcopy(manifest);corrupt['frames'].pop(37)
 refused('missing_nonrest_midpoint','pose_grid_incomplete',lambda:q.verify_pose_grid(corrupt))
 corrupt=copy.deepcopy(manifest);corrupt['frames'][37]=copy.deepcopy(corrupt['frames'][0])
 refused('rest_repeated_in_nonrest_slot','actual_pose_grid_changed',lambda:q.verify_pose_grid(corrupt))
 corrupt=copy.deepcopy(manifest);corrupt['frames'][37]['time_s']+=.00001
 refused('changed_nonrest_time','actual_pose_grid_changed',lambda:q.verify_pose_grid(corrupt))
 corrupt=copy.deepcopy(manifest);corrupt['physical_loop_sha256']='0'*64
 refused('changed_original_physical_loop','physical_loop_changed',lambda:q.verify_pose_grid(corrupt))
 corrupt=copy.deepcopy(manifest);corrupt['candidate_sha256']='0'*64
 refused('wrong_candidate_capture','pose_source_binding',lambda:q.verify_pose_grid(corrupt))
 with tempfile.TemporaryDirectory(prefix='t3088-socket-tiny-controls-',dir='/tmp')as td:
  base=Path(td);raw=__import__('struct').pack('<3d',1+2**-30,2,3);p=base/'tiny.f64';p.write_bytes(raw);row={'path':p.name,'dtype':'<f8','shape':[1,3],'sha256':s.sha(raw)}
  actual=q.fresh_array(base,row,(1,3));assert actual[0,0]==1+2**-30;results['Float64_below_Float32_resolution_retained']={'passed':True,'actual':actual.tolist()}
  f32=copy.deepcopy(row);f32['dtype']='<f4'
  refused('added_Float32_pose_snapshot','posed_array_precision_or_shape',lambda:q.fresh_array(base,f32,(1,3)))
  damaged=copy.deepcopy(row);damaged['sha256']='0'*64
  refused('pose_coordinate_byte_mutation','posed_array_binding',lambda:q.fresh_array(base,damaged,(1,3)))
  escape=copy.deepcopy(row);escape['path']='../unowned.f64'
  refused('pose_path_escape','posed_array_path_escape',lambda:q.fresh_array(base,escape,(1,3)))
 identity=[int(i%5==0)for i in range(16)]
 state={'bone_states_identical':True,'skeletons_updated':True,'mesh_bind_bases_identity':True,'candidate_node_states':[[0.0]*26 for _ in range(29)],'parent_node_states':[[0.0]*26 for _ in range(29)],'candidate_skeleton_matrices':[[0.0]*(26*16)for _ in range(3)],'parent_skeleton_matrices':[[0.0]*(26*16)for _ in range(3)],'actual_mesh_bind_bases':[[identity.copy()for _ in range(3)]for _ in range(4)]}
 state.update(time_s=3/32,key=None,candidate_bone_world_matrices=[identity.copy()for _ in range(26)],parent_bone_world_matrices=[identity.copy()for _ in range(26)])
 physical_pose={'time':3/32,'key':None,'world_matrices':[identity.copy()for _ in range(26)]}
 assert q.verify_frame_state(state,physical_pose);results['strict_actual_state_positive']={'passed':True}
 for key in('bone_states_identical','skeletons_updated','mesh_bind_bases_identity'):
  corrupt=copy.deepcopy(state);corrupt[key]='false'
  refused('truthy_false_string_'+key,'native_pose_state_mismatch',lambda c=corrupt:q.verify_frame_state(c,physical_pose))
 corrupt=copy.deepcopy(state);corrupt['parent_node_states'][3][0]=1e-12
 refused('actual_hidden_parent_transform_mismatch','native_actual_node_state_mismatch',lambda:q.verify_frame_state(corrupt,physical_pose))
 corrupt=copy.deepcopy(state);corrupt['parent_skeleton_matrices'][1][0]=1e-12
 refused('actual_stale_hidden_skeleton_matrix','native_actual_skeleton_state_mismatch',lambda:q.verify_frame_state(corrupt,physical_pose))
 corrupt=copy.deepcopy(state);corrupt['actual_mesh_bind_bases'][0][0][0]+=1e-12
 refused('actual_noncanonical_mesh_basis','native_actual_mesh_basis_mismatch',lambda:q.verify_frame_state(corrupt,physical_pose))
 nonrest_physical=copy.deepcopy(physical_pose);nonrest_physical['world_matrices'][7][12]=.000123
 refused('correctly_indexed_nonrest_state_replayed_from_rest','native_actual_pose_differs_from_independent_physical_loop',lambda:q.verify_frame_state(state,nonrest_physical))
 results['nonrest_replay_control_details']={'actual_index':1,'time_s':3/32,'key':None,'grid_labels_remain_correct':True,'physical_loop_bone_world_disagrees_with_replayed_state':True,'native_browser_execution':'UNRUN'}
 old=(ROOT/'fixtures/UNCHANGED-PHYSICAL-METRIC-LOOP.mjs.txt').read_bytes();script=(ROOT/'fixtures/NATIVE-PRODUCER-readback-socket129.mjs').read_bytes();assert s.sha(old)==s.PHYSICAL_LOOP_SHA and script.count(old)==1
 results['original_metric_and_limit_loop_byte_exact']={'passed':True,'sha256':s.sha(old),'bytes':len(old),'occurrences':script.count(old)}
 # These are static review aids, not evidence of native execution.
 assert b'mesh.getVertexPosition(i,p)'in script and b'rows.push(p.x,p.y,p.z)'in script
 append=script[script.index(b'let socketState=null;'):]
 assert b'Float32Array'not in append and b'.scene.updateMatrixWorld(true)'in append and b'mesh.skeleton.update()'in append
 results['capture_precision_and_hidden_skeleton_source_structure']={'passed':True,'scope':'Source structure only; browser execution remains UNRUN.'}
 result={'status':'FOCUSED_ORCHESTRATION_CONTROLS_ONLY_PASS','results':results,'controls':len(results),'code_pins':q.code_pins(),'seconds':time.monotonic()-started,'full_horse_static':'UNRUN','native129_capture':'UNRUN','native129_interface':'UNRUN','source_adoption':False,'photographic_acceptance':False}
 out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'status':result['status'],'controls':len(results),'seconds':result['seconds'],'out':str(out)}))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);run(p.parse_args().out)
