"""NEW external exact eye-NORMAL child qualification; no application adoption.

Source controls may run LIGHT. Static and fresh posed129 geometry phases require
root's resource GO. A new native capture is mandatory; no historical certificate
or raw129 manifest is accepted as proof for bd443.
"""
import argparse,copy,hashlib,json,pathlib,struct,sys,time
import numpy as np
import normal_child_source as child
ROOT=pathlib.Path(__file__).resolve().parent
APP=ROOT.parents[2]
STUDY=APP/'assets/authored/transport/horse_standing'
SHA=child.sha;need=child.need

def code_pins():
 old=APP/'tools/transport/horse_socket_interface_v1'
 pins={name:SHA((old/name).read_bytes()) for name in ['socket_geometry.py','socket_sources.py','socket_qualification.py','POLICY-DECLARATION.json','fixtures/UNCHANGED-PHYSICAL-METRIC-LOOP.mjs.txt']}
 for name in ['tools/transport/horse_upper_orbital_transition_v1/upper_orbital_source.py','assets/authored/transport/horse_standing/generate_upper_orbital_transition_v1.py','assets/authored/transport/horse_standing/generate_upper_lid_strip_v1.py']:
  pins['PARENT/'+name]=SHA((APP/name).read_bytes())
 for name in ['generate_eye_smooth_normals_v1.py','eye-smooth-normals-v1-recipe.json']:
  pins['CHILD/'+name]=SHA((STUDY/name).read_bytes())
 for name in ['normal_child_source.py','qualify_normal_child.py','native_normal_child129.mjs','run_normal_child129.cjs']:
  pins['NEW/'+name]=SHA((ROOT/name).read_bytes())
 return pins

def source_controls(source):
 parent=source.normal_parent_raw;candidate=source.raw[source.child_path];recipe=source.recipe;g=source.generator
 d,b=g.decode(candidate);pd,pb=g.decode(parent);checks=[]
 def refused(name,bad):
  try:g.inspect(parent,bad,recipe)
  except (ValueError,KeyError,IndexError,struct.error):checks.append(name);return
  raise AssertionError('Meaningful source corruption accepted: '+name)
 def changed_at(accessor,row,k,delta):
  doc,bb=g.decode(candidate);a,at,stride,width=g.layout(doc,accessor);bb=bytearray(bb);offset=at+row*stride+k*4;value=struct.unpack_from('<f',bb,offset)[0];struct.pack_into('<f',bb,offset,value+delta);return g.encode(doc,bytes(bb))
 for name,accessor in [('EYE_POSITION',207),('BODY_NORMAL',d['meshes'][1]['primitives'][0]['attributes']['NORMAL']),('BODY_POSITION',d['meshes'][1]['primitives'][0]['attributes']['POSITION']),('EYE_UV',d['meshes'][2]['primitives'][0]['attributes']['TEXCOORD_0'])]:refused(name,changed_at(accessor,0,0,.001))
 bad=copy.deepcopy(d);bad['materials'][0]['doubleSided']=not bad['materials'][0]['doubleSided'];refused('material_change',g.encode(bad,b))
 bad=copy.deepcopy(d);bad['accessors'][208]['min'][0]+=.01;refused('false_NORMAL_extrema',g.encode(bad,b))
 refused('nonunit_eye_NORMAL',changed_at(208,0,0,.1))
 # Child identity is a separate admission check, never an assertion that the old
 # parent must pass this NORMAL-only operation.
 need(SHA(candidate)==child.CANDIDATE_SHA and SHA(parent)==child.PARENT_SHA,'Source identity controls')
 return checks

def verify_native(source,manifest_path,supervisor_prefix,expected_code_pins):
 import socket_qualification as q
 import socket_geometry as g
 import socket_sources as original
 base=manifest_path.parent.resolve();raw=manifest_path.read_bytes();manifest=json.loads(raw)
 need(manifest['schema']=='NEW_normal_child_native129_capture_v1','New child capture schema required')
 need(manifest['candidate_sha256']==child.CANDIDATE_SHA and manifest['normal_parent_e49_sha256']==child.PARENT_SHA,'New child and actual parent capture binding')
 need(manifest['parent_sha256']==original.EXPECTED[original.PARENT] and manifest['physical_loop_sha256']==child.PHYSICAL_LOOP_SHA,'Unchanged collision reference and physical loop required')
 need(manifest['code_pins']==expected_code_pins==code_pins(),'Exact reviewed NEW implementation pins required')
 need(manifest['coordinate_frame']=='native_getVertexPosition_identity_mesh_bind_canonical_metres','Actual native canonical capture frame')
 frames=manifest['frames'];need(len(frames)==129,'All129 actual captured frames required')
 for i,row in enumerate(frames):
  need(type(row['index'])is int and row['index']==i and row['time_s']==i*3/32 and row['key']==(i//2 if i%2==0 else None),'Exact65key64midpoint timeline')
 result_row=manifest['capture_result'];result_path=(base/result_row['path']).resolve();need(result_path.is_relative_to(base),'Capture result containment')
 result_raw=result_path.read_bytes();need(SHA(result_raw)==result_row['sha256'],'Actual capture RESULT digest')
 result=json.loads(result_raw)
 need(result['status']=='NEW_NORMAL_CHILD_NATIVE129_CAPTURE_ONLY_COMPLETE','Fresh actual native capture must pass')
 need(result['code_pins']==expected_code_pins==code_pins() and result['candidate_sha256']==child.CANDIDATE_SHA,'Actual result implementation and new source')
 for key in ['pageerrors','consoleerrors','http_errors','request_failed','closure_errors','integrity_errors']:need(result[key]==[],'Actual native capture error '+key)
 for key in ['context_closed','browser_closed','server_closed','inputs_unchanged']:need(result[key]is True,'Actual native capture closure '+key)
 need(result['WebGL_contexts_created']==0 and result['WebGL_context_requests']==0 and result['socket_frames']==129,'Zero actual WebGL requests/contexts and129 inventory')
 physical=result['actual_physical'];need(physical['status']=='LOADED_STANDING65_KEYS64_MIDPOINTS_PASS_ONLY' and physical['key_count']==65 and physical['midpoint_count']==64 and physical['failures']==[],'Actual unchanged physical129 PASS required')
 need(physical['original_physical_limits']==json.loads((original.PACKET/'ORIGINAL-PHYSICAL-LIMITS.json').read_bytes()),'Every unchanged original physical limit')
 need(len(physical['poses'])==129 and physical['WebGL_contexts_created']==0 and physical['renderers_created']==0,'Actual original-loop sample count and no renderer')
 for suffix in ['.result.json','.cleanup.json']:
  closed=json.loads(pathlib.Path(str(supervisor_prefix)+suffix).read_text())
  if suffix=='.result.json':
   need(closed['returncode']==0 and closed['timed_out']is False,'Native supervisor must actually pass')
   command=closed['command'];need(len(command)==4 and pathlib.Path(command[0]).name=='node' and pathlib.Path(command[1]).resolve()==ROOT/'run_normal_child129.cjs' and pathlib.Path(command[3]).resolve()==base and pathlib.Path(closed['cwd']).resolve()==APP,'Actual native supervisor command/cwd must bind THIS capture')
   static_path=pathlib.Path(command[2]).resolve();static_raw=static_path.read_bytes()
   need(result['static_proof']=={'path':str(static_path),'sha256':SHA(static_raw),'bytes':len(static_raw)},'Actual source-static proof and command binding')
   static=json.loads(static_raw);need(static['status']=='NORMAL_CHILD_CURRENT_SOURCE_STATIC_ONLY_PASS' and static['candidate_sha256']==child.CANDIDATE_SHA and static['code_pins']==expected_code_pins,'Actual same-code exact-child static proof required')
  else:need(closed['cleanup_complete']is True and closed['remaining_owned_children']==[],'Zero remaining owned native descendants')
 comp=q.components(source,source.eye);allowed,ledger=q.source_interface_faces(source,comp)
 baseline={j for i,j in q.globe_pairs(source.old_body,set(range(len(source.old_body))),source.eye,source.crosses)}
 posed=q.traverse_pose_frames(source,frames,base,allowed,baseline,physical['poses'])
 source.unchanged()
 return {'status':'NEW_NORMAL_CHILD_ACTUAL_NATIVE_PHYSICAL_SOCKET129_ONLY_PASS','source_admission':child.MODE,'candidate_sha256':child.CANDIDATE_SHA,'normal_parent_e49_sha256':child.PARENT_SHA,'collision_reference925_sha256':original.EXPECTED[original.PARENT],'physical_loop_sha256':child.PHYSICAL_LOOP_SHA,'original_physical_limits':physical['original_physical_limits'],'actual_physical':physical,'all129_posed_frames':posed,'capture_manifest_sha256':SHA(raw),'capture_result_sha256':SHA(result_raw),'code_pins':code_pins(),'old_certificate_transferred':False,'new_child129_actually_executed':True,'source_adoption':False,'photographic_acceptance':False}

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--phase',choices=['source','static','posed'],required=True);p.add_argument('--out',type=pathlib.Path,required=True);p.add_argument('--poses',type=pathlib.Path);p.add_argument('--supervisor-prefix',type=pathlib.Path);args=p.parse_args()
 need(not args.out.exists() and not args.out.resolve().is_relative_to(APP.parent.parent),'Fresh outside-application output required')
 started=time.monotonic()
 try:
  initial_code_pins=code_pins()
  source=child.Sources(APP,STUDY)
  if args.phase=='source':result={'status':'NEW_NORMAL_CHILD_SOURCE_CONTROLS_ONLY_PASS','source_admission':child.MODE,'candidate_sha256':child.CANDIDATE_SHA,'normal_parent_e49_sha256':child.PARENT_SHA,'controls':source_controls(source),'structure':source.normal_structure,'native129':'UNRUN','posed129':'UNRUN','source_adoption':False,'photographic_acceptance':False}
  elif args.phase=='static':result=child.static(source)
  else:
   need(args.poses is not None and args.supervisor_prefix is not None,'Actual new129 capture and closed supervisor required')
   result=verify_native(source,args.poses,args.supervisor_prefix,initial_code_pins)
  source.unchanged();need(code_pins()==initial_code_pins,'Executing NEW and immutable ancestor implementation changed during proof');result.update(code_pins=initial_code_pins,seconds=time.monotonic()-started)
  args.out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'status':result['status'],'seconds':result['seconds'],'output':str(args.out)}))
 except Exception as error:
  if not args.out.exists():args.out.write_text(json.dumps({'status':'FAILED_NEW_CHILD_NO_ADOPTION','phase':args.phase,'error':str(error),'type':type(error).__name__,'source_adoption':False,'photographic_acceptance':False},indent=2)+'\n')
  raise
