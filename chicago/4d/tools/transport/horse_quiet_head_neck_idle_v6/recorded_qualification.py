"""Build/read fresh V6 finite qualification records; never embed own future hash."""
from pathlib import Path
import argparse,datetime,json
import quiet_source as child
import qualify_quiet_head_neck as qualification
import canonical_guard as guard
ROOT,APP=child.ROOT,child.APP
sha,need=child.sha,child.need
SCHEMA='standing-horse-quiet-head-neck-v6-qualification-summary-v1'
STATUS='EXACT_QUIET15_STATIC_NATIVE_PHYSICAL_PAIRED_SOCKET129_ONLY_PASS'
RUNTIME_FILE='transport/standing-horse/horse-sevket-quiet-head-neck-idle-v6.glb'
CERTIFICATE=APP/'data/transport/parked/standing-horse-planted/quiet-head-neck-v6-qualification-summary.json'

def receipt(path):
    path=Path(path);need(path.is_file() and not path.is_symlink(),'ordinary actual receipt');path=path.resolve()
    b=path.read_bytes();return dict(path=str(path),bytes=len(b),sha256=sha(b))

def verify_recorded_certificate(c):
    need(c['schema']==SCHEMA and c['status']==STATUS and c['source_admission']==child.MODE,'exact bounded quiet15 qualification scope')
    need(c['authored_master_sha256']==child.MASTER_SHA and c['runtime_candidate_sha256']==child.CANDIDATE_SHA and c['runtime_candidate_bytes']==4165556 and c['paired925_sha256']==child.PAIRED_SHA,'exact separately versioned master/runtime/pair')
    need(c['immutable_original925_sha256']==child.ORIGINAL925_SHA and c['immutable_motion_source_sha256']==child.ORIGINAL_MOTION_SHA,'original source lineage')
    need(c['selected_clip']=='sevket_reconstructed_quiet_head_neck_idle_v1' and c['runtime_exported_clip_count']==1 and c['selected_track_count']==15 and c['tail_gesture_enabled'] is False,'explicit quiet15 runtime, no failed17 fallback')
    need(c['actual_code_pins']==guard.code_pins() and c['physical_loop_bytes']==9176 and c['physical_loop_sha256']==child.PHYSICAL_LOOP_SHA,'exact current qualifying code and original physical loop')
    limits=json.loads((APP/'tools/transport/horse_socket_interface_v1/fixtures/ORIGINAL-PHYSICAL-LIMITS.json').read_bytes())
    need(c['limits_m']=={'BODY_locus':.014,'globe_contact_locus':.007,'source_and_parent_displacement':.020} and c['original_physical_limits']==limits,'every original physical/socket acceptance retained')
    for p,mode in [(c['actual_old13_physical'],'old13'),(c['actual_master_quiet15_physical'],'quiet15'),(c['actual_runtime_physical'],'runtime15')]:
        need(p['status']=='LOADED_STANDING65_KEYS64_MIDPOINTS_PASS_ONLY' and p['binding_mode']==mode and p['key_count']==65 and p['midpoint_count']==64 and len(p['poses'])==129 and p['failures']==[] and p['original_physical_limits']==limits and p['WebGL_contexts_created']==p['renderers_created']==0,'fresh actual original physical129 '+mode)
    old=c['actual_old13_physical']['old13_parity'];runtime=c['actual_runtime_master_parity129']
    for p in [old,runtime]:need(p['samples']==129 and p['vertices_per_sample']==12838 and p['maximum_position_m']<=1e-5 and p['maximum_shader_normal_degrees']<=.01 and p['maximum_bone_world_component']==0,'fresh actual allvertex/shadernormal/bone parity129')
    cross=c['actual_quiet15_cross129'];need(cross['samples']==129 and cross['actual_quiet_tail_vertices']==969 and cross['maximum_tail_position_delta_m']==cross['maximum_tail_relative_bone_component']==cross['maximum_head_neck_vs_source17_component']==0 and cross['maximum_all129_literal_reference_component']<=1e-5 and cross['maximum_actual_head_motion_component']>.02 and cross['maximum_actual_neck_motion_component']>.02,'fresh actual quiet motion/tail/source literal proof')
    samples=c['all129_socket_samples'];need(len(samples)==129,'all129 actual posed socket samples')
    for i,row in enumerate(samples):
        need(type(row['index']) is int and row['index']==i and type(row['time_s']) in (int,float) and row['time_s']==i*3/32 and ((type(row['key']) is int and row['key']==i//2) if i%2==0 else row['key'] is None),'exact recorded129 pose grid')
        need(type(row['BODY_pairs']) is int and row['BODY_pairs']>=0 and type(row['globe_contacts']) is int and row['globe_contacts']>=0 and 0<=row['BODY_max_upper_m']<=.014 and 0<=row['CONTACT_max_upper_m']<=.007 and row['new_exterior_or_undeclared_or_patch_patch_crossings']==0,'actual recomputed source interface/socket bounds; actual counts disclosed')
    need(c['actual_capture_inventory']['frames']==129 and c['actual_capture_inventory']['unique_RAW_files']==516 and c['actual_capture_inventory']['RAW_bytes']==59214096,'complete RESULT-bound real Float64 capture')
    need(len(c['actual_capture_inventory_mutation_controls'])==5 and all(x['detected'] for x in c['actual_capture_inventory_mutation_controls']),'actual postcapture replay/state/path controls executed')
    need(c['actual_WebGL_context_requests']==c['actual_WebGL_contexts_created']==0 and c['actual_Float64_raw_bytes']==59214096,'zero native WebGL/full raw output')
    need(set(c['closed_runs'])=={'source','static','native129','posed129'},'actual complete canonical phase inventory')
    for phase,r in c['closed_runs'].items():need(type(r['returncode']) is int and r['returncode']==0 and r['timed_out'] is False and r['cleanup_complete'] is True and r['remaining_owned_children']==[],'actual owned phase closure '+phase)
    for r in c['actual_receipts'].values():need(type(r['bytes']) is int and r['bytes']>0 and type(r['sha256']) is str and len(r['sha256'])==64 and set(r['sha256'])<=set('0123456789abcdef'),'actual receipt length/SHA binding')
    need(c['old_certificate_transferred'] is False and c['photographic_acceptance'] is False and c['whole_T2803_closed'] is False and c['whole_T3088_closed'] is False and c['whole_app_gate_acceptance'] is False and c['published_unheld_world_acceptance']=='UNRUN' and c['runtime_adoption'] is False,'no old verdict transfer or world/gait/adoption overclaim')
    return True

def build_summary(source_path,source_prefix,static_path,static_prefix,manifest_path,native_prefix,posed_path,posed_prefix):
    actual={};closed_runs={}
    for name,path,prefix,status in [('source',source_path,source_prefix,'QUIET_HEAD_NECK_V6_SOURCE_CONTROLS_ONLY_PASS'),('static',static_path,static_prefix,'QUIET_HEAD_NECK_V6_CURRENT_SOURCE_STATIC_ONLY_PASS'),('posed129',posed_path,posed_prefix,'QUIET_HEAD_NECK_V6_ACTUAL_MASTER_RUNTIME_PHYSICAL_PAIRED_SOCKET129_ONLY_PASS')]:
        raw=Path(path).read_bytes();value=json.loads(raw);need(value['status']==status and value['code_pins']==guard.code_pins(),'actual same-code completed phase '+name)
        run,cleanup=qualification.closed(prefix);command=run['command'];expected_phase='posed' if name=='posed129' else name
        need(len(command)>=6 and Path(command[0]).name in {'python','python3','python3.11'} and Path(command[1]).resolve()==ROOT/'qualify_quiet_head_neck.py' and command[2:5]==['--phase',expected_phase,'--out'] and Path(command[5]).resolve()==Path(path).resolve() and Path(run['cwd']).resolve()==APP,'actual canonical completed phase command '+name)
        need(len(command)==(10 if name=='posed129' else 6),'exact canonical phase argument inventory '+name)
        if name=='posed129':need(command[6:7]==['--poses'] and Path(command[7]).resolve()==Path(manifest_path).resolve() and command[8:9]==['--supervisor-prefix'] and Path(command[9]).resolve()==Path(native_prefix).resolve(),'posed command binds exact actual native manifest/supervisor')
        closed_runs[name]=dict(returncode=0,timed_out=False,cleanup_complete=True,remaining_owned_children=[],supervisor_result=receipt(str(prefix)+'.result.json'),supervisor_cleanup=receipt(str(prefix)+'.cleanup.json'))
        actual[name]=value
    manifest_path=Path(manifest_path);manifest=json.loads(manifest_path.read_bytes());result_path=manifest_path.parent/manifest['capture_result']['path'];native=json.loads(result_path.read_bytes());need(receipt(result_path)['sha256']==manifest['capture_result']['sha256'],'actual native result bound by manifest')
    run,cleanup=qualification.closed(native_prefix);native_command=run['command'];need(len(native_command)==5 and Path(native_command[0]).name=='node' and Path(native_command[1]).resolve()==ROOT/'run_quiet_head_neck129.cjs' and Path(native_command[2]).resolve()==Path(static_path).resolve() and Path(native_command[3]).resolve()==Path(static_prefix).resolve() and Path(native_command[4]).resolve()==manifest_path.parent.resolve() and Path(run['cwd']).resolve()==APP and run['requested_timeout_seconds']==run['effective_timeout_seconds']==600 and run.get('timeout_override_reason') is None,'exact actual native command/current static/output/original600s')
    need(native['status']=='QUIET_HEAD_NECK_V6_NATIVE_MASTER_RUNTIME129_CAPTURE_ONLY_COMPLETE' and native['code_pins']==guard.code_pins(),'actual new canonical native capture')
    need(actual['posed129']['capture_manifest_sha256']==receipt(manifest_path)['sha256'] and actual['posed129']['capture_result_sha256']==receipt(result_path)['sha256'],'posed phase actually traversed these native receipts')
    need(Path(native['static_proof']['path']).resolve()==Path(static_path).resolve() and native['static_proof']['sha256']==receipt(static_path)['sha256'] and Path(native['static_supervisor']['prefix']).resolve()==Path(static_prefix).resolve(),'native consumed this actually closed static phase')
    closed_runs['native129']=dict(returncode=0,timed_out=False,cleanup_complete=True,remaining_owned_children=[],supervisor_result=receipt(str(native_prefix)+'.result.json'),supervisor_cleanup=receipt(str(native_prefix)+'.cleanup.json'))
    posed=actual['posed129'];need(Path(posed['native_supervisor']['prefix']).resolve()==Path(native_prefix).resolve(),'posed result actually used recorded native supervisor')
    need(qualification.same_json(actual['source']['source_binding'],actual['static']['source_binding']) and qualification.same_json(actual['posed129']['source_binding'],actual['static']['source_binding']),'one unchanged historical PhaseA source binding throughout canonical source/static/native/posed')
    samples=[]
    for x in posed['all129_paired925_posed_frames']:
        f=x['frame'];samples.append(dict(index=f['index'],time_s=f['time_s'],key=f['key'],BODY_pairs=len(x['admitted_embedded_pairs']),globe_contacts=len(x['surface_contacts']),BODY_max_upper_m=x['maximum_body_locus_upper_m'],CONTACT_max_upper_m=x['maximum_contact_locus_upper_m'],new_exterior_or_undeclared_or_patch_patch_crossings=x['new_exterior_or_undeclared_or_patch_patch_crossings']))
    summary=dict(schema=SCHEMA,status=STATUS,recorded_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),source_admission=child.MODE,collision_mode='canonical_socket_interface_v1',authored_master_sha256=child.MASTER_SHA,runtime_candidate_sha256=child.CANDIDATE_SHA,runtime_candidate_bytes=4165556,paired925_sha256=child.PAIRED_SHA,immutable_original925_sha256=child.ORIGINAL925_SHA,immutable_motion_source_sha256=child.ORIGINAL_MOTION_SHA,selected_clip='sevket_reconstructed_quiet_head_neck_idle_v1',selected_track_count=15,runtime_exported_clip_count=1,tail_gesture_enabled=False,actual_code_pins=guard.code_pins(),physical_loop_bytes=9176,physical_loop_sha256=child.PHYSICAL_LOOP_SHA,limits_m=dict(BODY_locus=.014,globe_contact_locus=.007,source_and_parent_displacement=.020),original_physical_limits=posed['original_physical_limits'],actual_old13_physical=posed['actual_old13_physical'],actual_master_quiet15_physical=posed['actual_master_quiet15_physical'],actual_runtime_physical=posed['actual_runtime_physical'],actual_runtime_master_parity129=posed['actual_runtime_master_parity129'],actual_quiet15_cross129=posed['actual_quiet15_cross129'],all129_socket_samples=samples,actual_capture_inventory=posed['actual_capture_inventory'],actual_capture_inventory_mutation_controls=posed['actual_capture_inventory_mutation_controls'],actual_WebGL_context_requests=native['WebGL_context_requests'],actual_WebGL_contexts_created=native['WebGL_contexts_created'],actual_Float64_raw_bytes=native['raw_Float64_bytes'],closed_runs=closed_runs,actual_receipts={name:receipt(path) for name,path in [('source',source_path),('static',static_path),('capture',result_path),('capture_manifest',manifest_path),('captured_frames',manifest_path.parent/native['captured_frames']['path']),('posed129',posed_path)]},phaseA_source_binding=actual['static']['source_binding'],old_certificate_transferred=False,photographic_acceptance=False,whole_T2803_closed=False,whole_T3088_closed=False,whole_app_gate_acceptance=False,published_unheld_world_acceptance='UNRUN',runtime_adoption=False)
    verify_recorded_certificate(summary);return summary

def read_certificate(path=CERTIFICATE,expected_sha256=None):
    raw=Path(path).read_bytes();need(expected_sha256 is not None and sha(raw)==expected_sha256,'explicit selected certificate SHA required');c=json.loads(raw);verify_recorded_certificate(c);return c

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['source','source-prefix','static','static-prefix','manifest','native-prefix','posed','posed-prefix','out']:p.add_argument('--'+name,required=True,type=Path)
    a=p.parse_args();need(not a.out.exists() and not a.out.resolve().is_relative_to(APP.parents[1]),'fresh outside-app record output')
    value=build_summary(a.source,a.source_prefix,a.static,a.static_prefix,a.manifest,a.native_prefix,a.posed,a.posed_prefix);a.out.write_text(json.dumps(value,indent=2)+'\n');print(json.dumps(dict(status=value['status'],path=str(a.out),sha256=sha(a.out.read_bytes()))))
if __name__=='__main__':main()
