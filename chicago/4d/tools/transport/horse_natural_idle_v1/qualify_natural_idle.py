"""First-class new17track natural planted idle qualification; no application adoption.

Source controls may run LIGHT. Static and fresh posed129 geometry phases require
root's resource GO. A new native capture is mandatory; no historical certificate
or raw129 manifest is accepted as proof for new8ea motion.
"""
import argparse,copy,hashlib,json,pathlib,struct,sys,time
import numpy as np
import natural_idle_source as child
ROOT=pathlib.Path(__file__).resolve().parent
APP=ROOT.parents[2]
STUDY=APP/'assets/authored/transport/horse_standing'
SHA=child.sha;need=child.need

def code_pins():
 declared=json.loads((ROOT/'CODE-PIN-PATHS.json').read_text())
 pins={name:SHA((APP/relative).read_bytes())for name,relative in declared['paths'].items()}
 for name,expected in declared['preserved_old14_expected_sha256'].items():need(pins[name]==expected,'Immutable original qualifying14 changed: '+name)
 return pins

def source_controls(source):
 return child.source_controls(source)

def verify_native(source,manifest_path,supervisor_prefix,expected_code_pins):
 import socket_qualification as q
 import socket_geometry as g
 import socket_sources as original
 base=manifest_path.parent.resolve();raw=manifest_path.read_bytes();manifest=json.loads(raw)
 need(manifest['schema']=='NEW_natural_idle_native129_capture_v1','New child capture schema required')
 need(manifest['candidate_sha256']==child.CANDIDATE_SHA and manifest['motion_parent_bd443_sha256']==child.PARENT_SHA,'New child and actual parent capture binding')
 need(manifest['parent_sha256']==original.EXPECTED[original.PARENT] and manifest['physical_loop_sha256']==child.PHYSICAL_LOOP_SHA,'Unchanged collision reference and physical loop required')
 need(manifest['code_pins']==expected_code_pins==code_pins(),'Exact reviewed NEW implementation pins required')
 need(manifest['coordinate_frame']=='native_getVertexPosition_identity_mesh_bind_canonical_metres','Actual native canonical capture frame')
 frames=manifest['frames'];need(len(frames)==129,'All129 actual captured frames required')
 for i,row in enumerate(frames):
  need(type(row['index'])is int and row['index']==i and row['time_s']==i*3/32 and row['key']==(i//2 if i%2==0 else None),'Exact65key64midpoint timeline')
 result_row=manifest['capture_result'];result_path=(base/result_row['path']).resolve();need(result_path.is_relative_to(base),'Capture result containment')
 result_raw=result_path.read_bytes();need(SHA(result_raw)==result_row['sha256'],'Actual capture RESULT digest')
 result=json.loads(result_raw)
 need(result['status']=='NEW_NATURAL_IDLE_NATIVE129_CAPTURE_ONLY_COMPLETE','Fresh actual native capture must pass')
 need(result['code_pins']==expected_code_pins==code_pins() and result['candidate_sha256']==child.CANDIDATE_SHA,'Actual result implementation and new source')
 for key in ['pageerrors','consoleerrors','http_errors','request_failed','closure_errors','integrity_errors']:need(result[key]==[],'Actual native capture error '+key)
 for key in ['context_closed','browser_closed','server_closed','inputs_unchanged']:need(result[key]is True,'Actual native capture closure '+key)
 need(result['WebGL_contexts_created']==0 and result['WebGL_context_requests']==0 and result['socket_frames']==129,'Zero actual WebGL requests/contexts and129 inventory')
 physical=result['actual_physical'];need(physical['status']=='LOADED_STANDING65_KEYS64_MIDPOINTS_PASS_ONLY' and physical['key_count']==65 and physical['midpoint_count']==64 and physical['failures']==[],'Actual unchanged physical129 PASS required')
 need(physical['original_physical_limits']==json.loads((original.PACKET/'ORIGINAL-PHYSICAL-LIMITS.json').read_bytes()),'Every unchanged original physical limit')
 need(len(physical['poses'])==129 and physical['WebGL_contexts_created']==0 and physical['renderers_created']==0,'Actual original-loop sample count and no renderer')
 need(physical['selected_exported_clip_index']==1 and physical['selected_exported_track_count']==17 and physical['selected_exported_clip']=='sevket_reconstructed_natural_planted_idle_v1' and physical['head_tail_composed'] is True,'Actual explicitly selected second exported17track clip')
 need(physical['old_certificate_transferred']is False and physical['scope'].startswith('Actual native GLTFLoader/SkeletonUtils/AnimationMixer second exported17track'),'Truthful new motion scope with no old verdict transfer')
 for joint in [2,3,4,5]:
  first=physical['poses'][0]['world_matrices'][joint]
  change=max(abs(p['world_matrices'][joint][k]-first[k])for p in physical['poses']for k in [0,1,2,4,5,6,8,9,10])
  need(change>.02,'Actual new selected joint rotation must advance materially: '+str(joint))
 for suffix in ['.result.json','.cleanup.json']:
  closed=json.loads(pathlib.Path(str(supervisor_prefix)+suffix).read_text())
  if suffix=='.result.json':
   need(closed['returncode']==0 and closed['timed_out']is False,'Native supervisor must actually pass')
   command=closed['command'];need(len(command)==4 and pathlib.Path(command[0]).name=='node' and pathlib.Path(command[1]).resolve()==ROOT/'run_natural_idle129.cjs' and pathlib.Path(command[3]).resolve()==base and pathlib.Path(closed['cwd']).resolve()==APP,'Actual native supervisor command/cwd must bind THIS capture')
   static_path=pathlib.Path(command[2]).resolve();static_raw=static_path.read_bytes()
   need(result['static_proof']=={'path':str(static_path),'sha256':SHA(static_raw),'bytes':len(static_raw)},'Actual source-static proof and command binding')
   static=json.loads(static_raw);need(static['status']=='NATURAL_IDLE_CURRENT_SOURCE_STATIC_ONLY_PASS' and static['candidate_sha256']==child.CANDIDATE_SHA and static['code_pins']==expected_code_pins,'Actual same-code exact-child static proof required')
  else:need(closed['cleanup_complete']is True and closed['remaining_owned_children']==[],'Zero remaining owned native descendants')
 comp=q.components(source,source.eye);allowed,ledger=q.source_interface_faces(source,comp)
 baseline={j for i,j in q.globe_pairs(source.old_body,set(range(len(source.old_body))),source.eye,source.crosses)}
 posed=q.traverse_pose_frames(source,frames,base,allowed,baseline,physical['poses'])
 source.unchanged()
 return {'status':'NEW_NATURAL_IDLE_ACTUAL_NATIVE_PHYSICAL_SOCKET129_ONLY_PASS','source_admission':child.MODE,'candidate_sha256':child.CANDIDATE_SHA,'motion_parent_bd443_sha256':child.PARENT_SHA,'collision_reference925_sha256':original.EXPECTED[original.PARENT],'physical_loop_sha256':child.PHYSICAL_LOOP_SHA,'original_physical_limits':physical['original_physical_limits'],'actual_physical':physical,'all129_posed_frames':posed,'capture_manifest_sha256':SHA(raw),'capture_result_sha256':SHA(result_raw),'code_pins':code_pins(),'old_certificate_transferred':False,'new_child129_actually_executed':True,'source_adoption':False,'photographic_acceptance':False}

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--phase',choices=['source','static','posed'],required=True);p.add_argument('--out',type=pathlib.Path,required=True);p.add_argument('--poses',type=pathlib.Path);p.add_argument('--supervisor-prefix',type=pathlib.Path);args=p.parse_args()
 need(not args.out.exists() and not args.out.resolve().is_relative_to(APP.parent.parent),'Fresh outside-application output required')
 started=time.monotonic()
 try:
  initial_code_pins=code_pins()
  source=child.Sources()
  if args.phase=='source':result={'status':'NEW_NATURAL_IDLE_SOURCE_CONTROLS_ONLY_PASS','source_admission':child.MODE,'candidate_sha256':child.CANDIDATE_SHA,'motion_parent_bd443_sha256':child.PARENT_SHA,'controls':source_controls(source),'structure':source.motion_structure,'native129':'UNRUN','posed129':'UNRUN','source_adoption':False,'photographic_acceptance':False}
  elif args.phase=='static':result=child.static(source)
  else:
   need(args.poses is not None and args.supervisor_prefix is not None,'Actual new129 capture and closed supervisor required')
   result=verify_native(source,args.poses,args.supervisor_prefix,initial_code_pins)
  source.unchanged();need(code_pins()==initial_code_pins,'Executing NEW and immutable ancestor implementation changed during proof');result.update(code_pins=initial_code_pins,seconds=time.monotonic()-started)
  args.out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'status':result['status'],'seconds':result['seconds'],'output':str(args.out)}))
 except Exception as error:
  if not args.out.exists():args.out.write_text(json.dumps({'status':'FAILED_NEW_CHILD_NO_ADOPTION','phase':args.phase,'error':str(error),'type':type(error).__name__,'source_adoption':False,'photographic_acceptance':False},indent=2)+'\n')
  raise
