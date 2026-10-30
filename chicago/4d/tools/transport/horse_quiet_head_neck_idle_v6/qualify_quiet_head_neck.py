"""First-class exact quiet15 source/static/native+paired925 posed qualification."""
from pathlib import Path
import argparse,copy,json,resource,time,math
import quiet_source as child
import canonical_guard as guard
import head_field_source as head
import runtime_projection
ROOT,APP=child.ROOT,child.APP
sha,need=child.sha,child.need

def source_controls(source):
    master=source.master_raw;paired=source.paired_raw;parent=source.binding_parent_raw;reference=source.original925_raw
    field=(ROOT/'fixtures/EXACT-V4-HEAD-FIELD.json').read_bytes();template=head.exact_head_template(parent,field)
    checks=head.producer.controls(parent,reference,master,paired,template,sha(source.binding_recipe_raw))
    need(len(checks)==18 and all(x['detected'] for x in checks),'all18 meaningful unchanged master source controls')
    runtime=source.raw[source.binding_path];doc,binary=head.producer.read(runtime)
    cases=[]
    def meta(change):
        d=copy.deepcopy(doc);change(d);return head.producer.write(d,binary)
    cases.append(('runtime missing exact quiet name',meta(lambda d:d['animations'][0].__setitem__('name','wrong'))))
    cases.append(('runtime exports failed17 fallback',meta(lambda d:d['animations'].append(head.producer.read(master)[0]['animations'][1]))))
    cases.append(('runtime quiet target replaced by added tail',meta(lambda d:d['animations'][0]['channels'][14]['target'].__setitem__('node',4))))
    b=bytearray(binary);a=doc['accessors'][232];v=doc['bufferViews'][a['bufferView']];b[v.get('byteOffset',0)+a.get('byteOffset',0)]^=1
    cases.append(('actual retained quiet neck quaternion bytes changed',head.producer.write(doc,b)))
    b=bytearray(binary);b[-1]^=1;cases.append(('protected source BIN bytes changed',head.producer.write(doc,b)))
    for label,bad in cases:
        need(bad!=runtime,'meaningful actual runtime mutation')
        try:runtime_projection.inspect(master,bad)
        except (ValueError,KeyError,IndexError)as e:checks.append(dict(control=label,detected=True,reason=str(e),mutant_sha256=sha(bad)))
        else:raise ValueError('Runtime mutation escaped:'+label)
    need(len(checks)==23,'exact source/control inventory')
    return checks

def closed(prefix):
    r=json.loads(Path(str(prefix)+'.result.json').read_bytes());c=json.loads(Path(str(prefix)+'.cleanup.json').read_bytes())
    need(r['returncode']==0 and r['timed_out'] is False,'actual phase supervisor PASS')
    need(c['cleanup_complete'] is True and c['remaining_owned_children']==[],'actual phase cleanup zero')
    return r,c


def same_json(a,b):
    if type(a) is not type(b):return False
    if isinstance(a,dict):return a.keys()==b.keys() and all(same_json(a[k],b[k]) for k in a)
    if isinstance(a,list):return len(a)==len(b) and all(same_json(x,y) for x,y in zip(a,b))
    return a==b

def verify_capture_inventory(root,result,frames,*,read_bytes=None):
    descriptor=result['captured_frames'];p=(root/descriptor['path']).resolve()
    need(descriptor['path']=='CAPTURE-FRAMES.json' and p.is_relative_to(root) and not (root/descriptor['path']).is_symlink(),'ordinary contained actual frame inventory')
    raw=p.read_bytes();need(type(descriptor['bytes']) is int and len(raw)==descriptor['bytes'] and sha(raw)==descriptor['sha256'],'actual captured inventory bytes bound into native RESULT')
    inventory=json.loads(raw);need(inventory['schema']=='quiet_head_neck_v6_exact_actual_captured_frames_v1' and same_json(inventory['frames'],frames),'manifest frames exactly equal native RESULT-bound actual captured states and RAW descriptors')
    need(descriptor['frame_count']==129 and descriptor['raw_file_count']==516 and len(frames)==129,'exact captured129/516 inventory')
    need((root/'frames').is_dir() and not (root/'frames').is_symlink(),'ordinary native frames directory')
    paths=set();total=0
    for i,row in enumerate(frames):
        need(type(row['index']) is int and row['index']==i and type(row['time_s']) in (int,float) and math.isfinite(row['time_s']) and row['time_s']==i*3/32,'strict actual ordered index/time types')
        need((type(row['key']) is int and row['key']==i//2) if i%2==0 else row['key'] is None,'strict actual key/midpoint types')
        for role,count in [('candidate_body',5595),('parent_body',5595),('candidate_eye',3968),('parent_eye',3968)]:
            d=row[role];expected=f'frames/{i:03d}-{role}.f64le'
            need(set(d)=={'path','dtype','shape','bytes','sha256'} and d['path']==expected and d['path'] not in paths,'unique canonical actual frame/role RAW path')
            need(d['dtype']=='<f8' and type(d['shape']) is list and all(type(x) is int for x in d['shape']) and d['shape']==[count,3] and type(d['bytes']) is int and d['bytes']==count*3*8,'exact actual Float64 shape and byte count')
            need(type(d['sha256']) is str and len(d['sha256'])==64 and set(d['sha256'])<=set('0123456789abcdef'),'actual RAW SHA256 syntax')
            actual_path=root/d['path'];need(actual_path.is_file() and not actual_path.is_symlink() and actual_path.resolve().is_relative_to(root),'ordinary contained actual RAW file')
            b=actual_path.read_bytes() if read_bytes is None else read_bytes(actual_path)
            need(len(b)==d['bytes'] and sha(b)==d['sha256'],'actual original per-frame RAW bytes, no copied rest array')
            paths.add(d['path']);total+=len(b)
    need(len(paths)==516 and total==59214096,'complete unique actual RAW inventory')
    return dict(path=descriptor['path'],bytes=len(raw),sha256=sha(raw),frames=129,unique_RAW_files=516,RAW_bytes=total)

def actual_inventory_mutation_controls(root,result,frames):
    cases=[]
    bad=copy.deepcopy(frames)
    for k in ['candidate_body','parent_body','candidate_eye','parent_eye']:bad[1][k]=copy.deepcopy(frames[0][k])
    cases.append(('duplicate rest-frame RAW descriptors under later time/state',bad,None))
    bad=copy.deepcopy(frames);bad[0],bad[1]=bad[1],bad[0];cases.append(('reordered actual captured frame records',bad,None))
    bad=copy.deepcopy(frames);bad[1]['candidate_body']['path']='frames/001-renamed-candidate_body.f64le';cases.append(('renamed actual RAW path',bad,None))
    bad=copy.deepcopy(frames);bad[1]['candidate_bone_world_matrices'][3][0]+=.001;cases.append(('actual captured bone-state metadata altered',bad,None))
    target=root/frames[1]['candidate_body']['path'];rest=(root/frames[0]['candidate_body']['path']).read_bytes();need(sha(rest)!=frames[1]['candidate_body']['sha256'],'actual nonidentity rest-array replay mutation')
    cases.append(('copied actual rest RAW bytes returned for moving later frame',frames,lambda p:rest if p==target else p.read_bytes()))
    checks=[]
    for label,bad,reader in cases:
        try:verify_capture_inventory(root,result,bad,read_bytes=reader)
        except (ValueError,KeyError,IndexError)as e:checks.append(dict(control=label,detected=True,reason=str(e)))
        else:raise ValueError('Actual captured inventory mutation escaped:'+label)
    need(len(checks)==5,'all five actual postcapture replay/state/path controls')
    return checks

def verify_native(source,manifest_path,supervisor_prefix,pins):
    import socket_qualification as q
    root=manifest_path.parent.resolve();manifest_raw=manifest_path.read_bytes();manifest=json.loads(manifest_raw)
    need(manifest['schema']=='quiet_head_neck_v6_actual_master_runtime_native129_capture_v1','new exact native capture schema')
    need(manifest['authored_master_sha256']==child.MASTER_SHA and manifest['candidate_sha256']==child.CANDIDATE_SHA and manifest['parent_sha256']==child.PAIRED_SHA,'actual new master/runtime/pair lineage')
    need(manifest['immutable_original925_sha256']==child.ORIGINAL925_SHA and manifest['immutable_motion_source_sha256']==child.ORIGINAL_MOTION_SHA,'immutable original ancestry')
    need(manifest['code_pins']==pins==guard.code_pins() and manifest['physical_loop_sha256']==child.PHYSICAL_LOOP_SHA,'actual unchanged original physical loop and current qualifying code')
    need(manifest['coordinate_frame']=='native_getVertexPosition_identity_mesh_bind_canonical_metres' and manifest['reference_pose_method']=='separate_native_AnimationMixer_actual_runtime_clip','actual native basis and independent paired925 Mixer')
    frames=manifest['frames'];need(len(frames)==129 and manifest['raw_Float64_bytes']==59214096,'complete129/516 actual Float64 inventory')
    for i,row in enumerate(frames):
        need(type(row['index']) is int and row['index']==i and type(row['time_s']) in (int,float) and math.isfinite(row['time_s']) and row['time_s']==i*3/32 and ((type(row['key']) is int and row['key']==i//2) if i%2==0 else row['key'] is None),'strict exact ordered65keys/64midpoints')
        need(row['reference_pose_method']=='separate_native_AnimationMixer_actual_runtime_clip','each actual independent pair925 Mixer frame')
    rr=manifest['capture_result'];result_path=(root/rr['path']).resolve();need(result_path.is_relative_to(root),'result containment');result_raw=result_path.read_bytes();need(len(result_raw)==rr['bytes'] and sha(result_raw)==rr['sha256'],'actual result exact bytes')
    result=json.loads(result_raw);need(result['status']=='QUIET_HEAD_NECK_V6_NATIVE_MASTER_RUNTIME129_CAPTURE_ONLY_COMPLETE','actual fresh native capture PASS')
    need(result['authored_master_sha256']==child.MASTER_SHA and result['runtime_candidate_sha256']==child.CANDIDATE_SHA and result['paired925_reference_sha256']==child.PAIRED_SHA and result['code_pins']==pins,'exact current result model/code binding')
    need(result['immutable_motion_source_sha256']==child.ORIGINAL_MOTION_SHA and result['immutable_original925_sha256']==child.ORIGINAL925_SHA,'actual result original source lineage')
    need(result['selected_clip']==head.producer.NAME and result['runtime_exported_clip_count']==1 and result['reference_pose_method']==manifest['reference_pose_method'],'one exact named quiet15, no failed17 fallback')
    for key in ['pageerrors','consoleerrors','http_errors','request_failed','closure_errors','integrity_errors']:need(result[key]==[],'strict actual native error '+key)
    for key in ['context_closed','browser_closed','server_closed','inputs_unchanged']:need(result[key] is True,'actual closed resource '+key)
    need(result['WebGL_context_requests']==result['WebGL_contexts_created']==0 and result['socket_frames']==129 and result['raw_Float64_bytes']==59214096,'zero WebGL requests/contexts and complete raw capture')
    need(same_json(manifest['captured_frames'],result['captured_frames']),'manifest and actual RESULT bind same captured frame file')
    inventory=verify_capture_inventory(root,result,frames)
    inventory_controls=actual_inventory_mutation_controls(root,result,frames)
    limits=json.loads((APP/'tools/transport/horse_socket_interface_v1/fixtures/ORIGINAL-PHYSICAL-LIMITS.json').read_bytes())
    for key,mode in [('actual_old13_physical','old13'),('actual_master_quiet15_physical','quiet15'),('actual_physical','runtime15')]:
        p=result[key];need(p['status']=='LOADED_STANDING65_KEYS64_MIDPOINTS_PASS_ONLY' and p['binding_mode']==mode and p['key_count']==65 and p['midpoint_count']==64 and len(p['poses'])==129 and p['failures']==[],'fresh actual physical129 '+mode)
        need(p['original_physical_limits']==limits and p['WebGL_contexts_created']==p['renderers_created']==0,'original physical limits/no renderer '+mode)
    old=result['actual_old13_physical']['old13_parity'];parity=result['actual_runtime_master_parity129']
    for p in [old,parity]:
        need(p['samples']==129 and p['vertices_per_sample']==12838 and p['tolerance_m']==1e-5 and p['tolerance_degrees']==.01 and p['maximum_position_m']<=1e-5 and p['maximum_shader_normal_degrees']<=.01 and p['maximum_bone_world_component']==0,'actual all-vertex/shadernormal/bone parity129')
    need(parity['status']=='ACTUAL_RUNTIME_MASTER_QUIET15_PARITY129_ONLY_PASS','actual runtime versus master quiet15 parity')
    cross=result['actual_quiet15_cross129'];need(cross['status']=='ACTUAL_QUIET15_CROSSCHECK129_ONLY_PASS' and cross['samples']==129 and len(cross['poses'])==129 and cross['actual_quiet_tail_vertices']==969,'actual all129 quiet crosscheck')
    need(cross['maximum_tail_position_delta_m']==cross['maximum_tail_relative_bone_component']==cross['maximum_head_neck_vs_source17_component']==0 and cross['maximum_all129_literal_reference_component']<=1e-5,'original quiet tail/unchanged full head17 curves and independent literal reference')
    need(cross['maximum_actual_head_motion_component']>.02 and cross['maximum_actual_neck_motion_component']>.02,'actual nonzero material head and neck rotation')
    supervisor,cleanup=closed(supervisor_prefix);command=supervisor['command']
    need(len(command)==5 and Path(command[0]).name=='node' and Path(command[1]).resolve()==ROOT/'run_quiet_head_neck129.cjs' and Path(command[4]).resolve()==root and Path(supervisor['cwd']).resolve()==APP,'actual canonical native command/cwd/output binding')
    need(supervisor['requested_timeout_seconds']==supervisor['effective_timeout_seconds']==600 and supervisor.get('timeout_override_reason') is None,'original600s native timeout retained')
    static_path=Path(command[2]).resolve();static_raw=static_path.read_bytes();need(result['static_proof']==dict(path=str(static_path),bytes=len(static_raw),sha256=sha(static_raw)),'exact actual static command/input receipt')
    static_supervisor=result['static_supervisor'];static_prefix=Path(static_supervisor['prefix']).resolve();need(Path(command[3]).resolve()==static_prefix,'actual native command binds closed static supervisor prefix')
    for name,suffix in [('result','.result.json'),('cleanup','.cleanup.json')]:
        p=Path(str(static_prefix)+suffix);b=p.read_bytes();need(static_supervisor[name]==dict(path=str(p),bytes=len(b),sha256=sha(b)),'exact actually closed static supervisor '+name)
    sr,sc=closed(static_prefix);static_command=sr['command'];need(len(static_command)==6 and Path(static_command[0]).name in {'python','python3','python3.11'} and Path(static_command[1]).resolve()==ROOT/'qualify_quiet_head_neck.py' and static_command[2:5]==['--phase','static','--out'] and Path(static_command[5]).resolve()==static_path and Path(sr['cwd']).resolve()==APP,'actual canonical static command/cwd/output closure')
    need(sr['requested_timeout_seconds']==sr['effective_timeout_seconds'] and sr['requested_timeout_seconds']>0 and sr.get('timeout_override_reason') is None,'actual static original timeout retained')
    static=json.loads(static_raw);need(static['status']=='QUIET_HEAD_NECK_V6_CURRENT_SOURCE_STATIC_ONLY_PASS' and static['authored_master_sha256']==child.MASTER_SHA and static['runtime_candidate_sha256']==child.CANDIDATE_SHA and static['paired925_sha256']==child.PAIRED_SHA and static['code_pins']==pins,'fresh same-code static receipt')
    need(static['source_binding']==guard.snapshot(),'exact unchanged current canonical source/index/mirror still matches static')
    components=q.components(source,source.eye);allowed,ledger=q.source_interface_faces(source,components)
    baseline={j for i,j in q.globe_pairs(source.old_body,set(range(len(source.old_body))),source.eye,source.crosses)}
    posed=q.traverse_pose_frames(source,frames,root,allowed,baseline,result['actual_physical']['poses'])
    need(verify_capture_inventory(root,result,frames)==inventory,'all actual RAW/inventory bytes unchanged through posed traversal')
    source.unchanged()
    return dict(status='QUIET_HEAD_NECK_V6_ACTUAL_MASTER_RUNTIME_PHYSICAL_PAIRED_SOCKET129_ONLY_PASS',source_admission=child.MODE,authored_master_sha256=child.MASTER_SHA,runtime_candidate_sha256=child.CANDIDATE_SHA,paired925_sha256=child.PAIRED_SHA,immutable_original925_sha256=child.ORIGINAL925_SHA,immutable_motion_source_sha256=child.ORIGINAL_MOTION_SHA,physical_loop_sha256=child.PHYSICAL_LOOP_SHA,original_physical_limits=limits,actual_old13_physical=result['actual_old13_physical'],actual_master_quiet15_physical=result['actual_master_quiet15_physical'],actual_runtime_physical=result['actual_physical'],actual_runtime_master_parity129=parity,actual_quiet15_cross129=cross,all129_paired925_posed_frames=posed,actual_capture_inventory=inventory,actual_capture_inventory_mutation_controls=inventory_controls,capture_manifest_sha256=sha(manifest_raw),capture_result_sha256=sha(result_raw),native_supervisor=dict(prefix=str(supervisor_prefix),returncode=0,timed_out=False,cleanup_complete=True,remaining_owned_children=[]),old_certificate_transferred=False,runtime_adoption=False,photographic_acceptance=False)

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--phase',choices=['source','static','posed'],required=True);parser.add_argument('--out',required=True,type=Path);parser.add_argument('--poses',type=Path);parser.add_argument('--supervisor-prefix',type=Path);args=parser.parse_args()
    need(not args.out.exists() and not args.out.resolve().is_relative_to(APP.parents[1]),'fresh outside-app phase output')
    if args.phase=='source':resource.setrlimit(resource.RLIMIT_CPU,(10,11))
    start=time.monotonic();before=guard.snapshot();pins=before['code_pins']
    try:
        source=child.Sources();checks=source_controls(source)
        if args.phase=='source':result=dict(status='QUIET_HEAD_NECK_V6_SOURCE_CONTROLS_ONLY_PASS',source_controls=checks,structure=source.structure,canonical_static='UNRUN',canonical_native='UNRUN',paired925_socket129='UNRUN')
        elif args.phase=='static':result=child.static(source);result['source_controls']=checks
        else:
            need(args.poses is not None and args.supervisor_prefix is not None,'actual closed native129 manifest and supervisor required')
            result=verify_native(source,args.poses,args.supervisor_prefix,pins)
        source.unchanged();need(guard.snapshot()==before,'complete staged source/index/mirror/code unchanged during actual phase')
        result.update(code_pins=pins,source_binding=before,seconds=time.monotonic()-start,runtime_adoption=False)
        args.out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(status=result['status'],seconds=result['seconds'],output=str(args.out))))
    except Exception as e:
        if not args.out.exists():args.out.write_text(json.dumps(dict(status='QUIET_HEAD_NECK_V6_PHASE_NONPASS_NO_ADOPTION',phase=args.phase,error=str(e),type=type(e).__name__,runtime_adoption=False),indent=2)+'\n')
        raise
if __name__=='__main__':main()
