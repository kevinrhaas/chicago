"""EXTERNAL opt-in source socket proof. Full phases require root's heavy slot.

Importing this file performs no qualification. Old recipes/checkers are read-only.
"""
import argparse,ast,datetime,hashlib,json,time
from pathlib import Path
import numpy as np
import socket_geometry as g
import socket_sources as s

ROOT=Path(__file__).resolve().parent
POLICY=ROOT/'POLICY-DECLARATION.json'
PRODUCTION=('socket_geometry.py','socket_sources.py','socket_qualification.py')

def code_pins():
    return {name:s.sha((ROOT/name).read_bytes())for name in PRODUCTION}

def policy_expected(faces):
    return {'mode':s.MODE,'source_parent_sha256':s.EXPECTED[s.PARENT],'unchanged_original_interface_faces':{str(k):sorted(v)for k,v in faces.items()},'body_locus_limit_m':.014,'globe_contact_limit_m':.007,'replacement_faces_inherit_no_crossing_ancestry':True}

def verify_policy(declared,derived):
    forbidden={'inherited_pairs','face_ancestry','exempt_pairs','allow_new_crossings','ignore_exterior'}
    g.need(not(forbidden&set(declared)),'forbidden_replacement_face_ancestry_declaration')
    g.need(declared==policy_expected(derived),'source_interface_policy_mismatch')
    return True

def proper_pairs(body,patch,kernel):
    lo,hi=body.min(axis=1),body.max(axis=1);pairs=[]
    for i in sorted(patch):
        for j in np.flatnonzero(np.all(lo<=hi[i]+1e-9,axis=1)&np.all(hi>=lo[i]-1e-9,axis=1)):
            j=int(j)
            if j==i or(j in patch and j<i):continue
            if kernel(body[i],body[j]):pairs.append((i,j))
    return pairs

def globe_pairs(body,patch,eye,kernel):
    lo,hi=eye.min(axis=1),eye.max(axis=1);pairs=[]
    for i in sorted(patch):
        t=body[i]
        for j in np.flatnonzero(np.all(lo<=t.max(axis=0)+1e-9,axis=1)&np.all(hi>=t.min(axis=0)-1e-9,axis=1)):
            if kernel(t,eye[j]):pairs.append((i,int(j)))
    return pairs

def components(source,eye):
    return {side:g.ClosedComponent(eye[ids],side,'immutable-source-Eye_brown-'+str(side),ids)for side,ids in source.component_faces.items()}

def source_interface_faces(source,comp):
    """Derive from authenticated old source geometry, never candidate face pairs."""
    faces={-1:set(),1:set()};pieces=[]
    old_checker=s.APP/'tools/transport/check_horse_anatomy_crossings.py'
    g.need(s.sha(old_checker.read_bytes())==source.ledger['checker_sha256'],'original_checker_binding')
    ast_function=lambda p:ast.dump(next(n for n in ast.parse(p.read_text()).body if isinstance(n,ast.FunctionDef)and n.name=='crosses'),include_attributes=False)
    g.need(ast_function(old_checker)==ast_function(s.KERNEL),'original_crossing_predicate_drift')
    for pair in source.ledger['candidate_proper_crossings']:
        if sum(i in source.patch for i in pair)!=1:continue
        i=next(i for i in pair if i in source.patch);j=next(j for j in pair if j not in source.patch);side=source.side_for[i]
        g.need(source.crosses(source.old_body[i],source.old_body[j]),'authenticated_source_pair_not_proper',pair)
        segment=g.intersection_segment(source.old_body[i],source.old_body[j])
        for piece in comp[side].clipped_inside(segment):
            faces[side].add(j);pieces.append({'source_pair':[i,j],'original_unchanged_face':j,'side':side,'segment':piece.data()})
    g.need(faces==s.EXPECTED_INTERFACE,'source_derived_interface_set_drift',{k:sorted(v)for k,v in faces.items()})
    verify_policy(json.loads(POLICY.read_text()),faces)
    return faces,pieces

def source_curves(source,old_body,eye,comp,allowed):
    """Recompute every frame: old patch participants are not all rigid head3."""
    body_curves={-1:{},1:{}};contact_curves={-1:[],1:[]};records=[];contacts=[]
    for side in(-1,1):
        for i in sorted(k for k,v in source.side_for.items()if v==side):
            a=old_body[i]
            for j in sorted(allowed[side]):
                b=old_body[j]
                if not(np.all(a.min(axis=0)<=b.max(axis=0)+1e-9)and np.all(a.max(axis=0)>=b.min(axis=0)-1e-9)):continue
                if not source.crosses(a,b):continue
                cut=g.intersection_segment(a,b)
                for piece in comp[side].clipped_inside(cut):
                    body_curves[side].setdefault(j,[]).append(piece)
                    records.append({'source_pair':[i,j],'side':side,'inside_segment':piece.data()})
    for i,j in globe_pairs(old_body,source.patch,eye,source.crosses):
        side=source.side_for[i];g.need(j in comp[side].local_index,'source_wrong_side_globe_contact')
        cut=g.intersection_segment(old_body[i],eye[j]);contact_curves[side].append(cut);contacts.append({'source_pair':[i,j],'side':side,'segment':cut.data()})
    return body_curves,contact_curves,records,contacts

def evaluate_frame(source,body,old_body,eye,old_eye,allowed,frame,all_body_rest_contact_faces):
    for data in(body,old_body,eye,old_eye):g.need(np.isfinite(data).all(),'nonfinite_posed_geometry')
    exterior=sorted(set(range(len(body)))-source.patch)
    g.need(np.array_equal(body[exterior],old_body[exterior]),'posed_exterior_geometry_changed')
    g.need(np.array_equal(eye,old_eye),'posed_globe_geometry_changed')
    comp=components(source,eye);refs,contact_refs,source_records,contact_records=source_curves(source,old_body,eye,comp,allowed)
    admitted=[];contacts=[]
    for i,j in proper_pairs(body,source.patch,source.crosses):
        side=source.side_for[i]
        g.need(j not in source.patch,'patch_patch_crossing_forbidden',[i,j])
        segment=g.intersection_segment(body[i],body[j])
        record=g.admit_body_crossing(segment,side,j,body[j],old_body[j],comp[side],allowed[side],refs[side].get(j,[]))
        admitted.append({'replacement_slot':i,'source_unchanged_face':j,'segment':segment.data(),**record})
    for i,j in globe_pairs(body,source.patch,eye,source.crosses):
        side=source.side_for[i];g.need(j in comp[side].local_index,'wrong_side_globe_contact',[i,j])
        cut=g.intersection_segment(body[i],eye[j]);record=g.admit_globe_contact(cut,side,comp[side],contact_refs[side],j)
        contacts.append({'replacement_slot':i,'immutable_globe_face':j,'segment':cut.data(),**record})
    original_contact_faces={r['source_pair'][1]for r in contact_records};new_contact_faces=sorted({r['immutable_globe_face']for r in contacts}-original_contact_faces)
    return {'frame':frame,'state':'SOURCE_SOCKET_FRAME_ONLY_PASS','components':{k:v.topology for k,v in comp.items()},'original_interface_curves':source_records,'original_globe_contact_curves':contact_records,'admitted_embedded_pairs':admitted,'surface_contacts':contacts,'globe_faces_not_in_same_pose_original_patch_contact_reference':new_contact_faces,'globe_faces_not_contacted_by_ANY_source925_BODY_triangle_at_rest':sorted({r['immutable_globe_face']for r in contacts}-all_body_rest_contact_faces),'all_body_rest_baseline_is_disclosure_only_not_admission':True,'maximum_body_locus_upper_m':max((r['locus_certificate']['upper_m']for r in admitted),default=0),'maximum_contact_locus_upper_m':max((r['locus_certificate']['upper_m']for r in contacts),default=0),'new_exterior_or_undeclared_or_patch_patch_crossings':0}

def fresh_array(base,row,shape):
    g.need(row['dtype']=='<f8'and row['shape']==list(shape),'posed_array_precision_or_shape')
    p=(base/row['path']).resolve();g.need(p.is_relative_to(base.resolve()),'posed_array_path_escape')
    raw=p.read_bytes();g.need(len(raw)==int(np.prod(shape))*8 and s.sha(raw)==row['sha256'],'posed_array_binding')
    array=np.frombuffer(raw,dtype='<f8').reshape(shape);g.need(np.isfinite(array).all(),'posed_array_nonfinite');return array

def verify_pose_grid(manifest):
    g.need(manifest['schema']=='canonical_socket_native129_capture_v1','pose_manifest_schema')
    g.need(manifest['physical_loop_sha256']==s.PHYSICAL_LOOP_SHA,'physical_loop_changed')
    g.need(manifest['parent_sha256']==s.EXPECTED[s.PARENT]and manifest['candidate_sha256']==s.EXPECTED[s.CANDIDATE],'pose_source_binding')
    frames=manifest['frames'];g.need(len(frames)==129,'pose_grid_incomplete')
    for i,row in enumerate(frames):
        g.need(row['index']==i and row['time_s']==i*3/32 and row['key']==(i//2 if i%2==0 else None),'actual_pose_grid_changed',i)
    g.need(all(type(r['index'])is int and type(r['time_s'])in(int,float)and(r['key']is None or type(r['key'])is int)for r in frames),'pose_grid_value_types')
    g.need(manifest['coordinate_frame']=='native_getVertexPosition_identity_mesh_bind_canonical_metres','pose_coordinate_frame')
    return frames

def verify_capture_result(base,manifest):
    result_row=manifest['capture_result'];p=base/result_row['path'];raw=p.read_bytes();g.need(s.sha(raw)==result_row['sha256'],'native_capture_result_binding');result=json.loads(raw)
    g.need(result['status']=='SOCKET_NATIVE129_CAPTURE_ONLY_COMPLETE','native_capture_not_complete')
    g.need(result['physical_loop_sha256']==s.PHYSICAL_LOOP_SHA and result['actual_physical']['status']=='LOADED_STANDING65_KEYS64_MIDPOINTS_PASS_ONLY','original_physical_129_not_pass')
    g.need(result['actual_physical']['key_count']==65 and result['actual_physical']['midpoint_count']==64 and result['actual_physical']['failures']==[],'original_physical_samples_missing')
    for key in('pageerrors','consoleerrors','http_errors','request_failed','closure_errors','integrity_errors'):g.need(result[key]==[],'native_capture_errors',key)
    for key in('context_closed','browser_closed','server_closed','inputs_unchanged'):g.need(result[key]is True,'native_capture_closure_or_source',key)
    producer=json.loads(s.CERTIFICATE.read_bytes())['producer_code_pins']
    g.need(result['code_pins']==producer and manifest['code_pins']==producer,'recorded_capture_implementation_changed')
    g.need(s.sha((ROOT/'socket_geometry.py').read_bytes())==producer['socket_geometry.py'],'native_geometry_core_changed_since_actual_proof')
    g.need(result['socket_frames']==129 and result['WebGL_contexts_created']==0,'native_socket_capture_inventory')
    for key in('supervisor_result','supervisor_cleanup'):
        r=manifest[key];raw=(base/r['path']).read_bytes();g.need(s.sha(raw)==r['sha256'],'capture_supervisor_binding');r=json.loads(raw)
        if key=='supervisor_result':g.need(type(r['returncode'])is int and r['returncode']==0 and r['timed_out']is False,'capture_supervisor_failed')
        else:g.need(r['cleanup_complete']is True and r['remaining_owned_children']==[],'capture_owned_children_remaining')
    return result

def verify_frame_state(row,physical_pose):
    for key in('bone_states_identical','skeletons_updated','mesh_bind_bases_identity'):g.need(row[key]is True,'native_pose_state_mismatch',key)
    def numeric_tree(value):
        if isinstance(value,list):return bool(value)and all(numeric_tree(v)for v in value)
        return type(value)in(int,float)and np.isfinite(value)
    c,p=row['candidate_node_states'],row['parent_node_states']
    g.need(len(c)==len(p)>=26 and all(len(v)==26 for v in c+p)and numeric_tree(c)and numeric_tree(p)and c==p,'native_actual_node_state_mismatch')
    c,p=row['candidate_skeleton_matrices'],row['parent_skeleton_matrices']
    g.need(len(c)==len(p)==3 and all(len(v)==26*16 for v in c+p)and numeric_tree(c)and numeric_tree(p)and c==p,'native_actual_skeleton_state_mismatch')
    g.need(row['time_s']==physical_pose['time']and row['key']==physical_pose['key'],'native_physical_pose_grid_mismatch')
    matrices=row['candidate_bone_world_matrices'];parent_matrices=row['parent_bone_world_matrices'];physical_matrices=physical_pose['world_matrices']
    g.need(len(matrices)==len(parent_matrices)==len(physical_matrices)==26 and all(len(m)==16 for m in matrices+parent_matrices+physical_matrices)and numeric_tree(matrices)and numeric_tree(parent_matrices)and numeric_tree(physical_matrices)and matrices==parent_matrices==physical_matrices,'native_actual_pose_differs_from_independent_physical_loop')
    bases=row['actual_mesh_bind_bases'];identity=[int(i%5==0)for i in range(16)]
    g.need(len(bases)==4 and all(len(mesh)==3 and all(matrix==identity for matrix in mesh)for mesh in bases),'native_actual_mesh_basis_mismatch')
    return True

def traverse_pose_frames(source,frames,base,allowed,all_body_rest_contact_faces,physical_poses,*,array_reader=fresh_array,frame_evaluator=evaluate_frame):
    """Production traversal; callbacks exist only for tiny focused control fixtures."""
    g.need(len(frames)==len(physical_poses)==129,'posed_interface_samples_incomplete');results=[]
    for row in frames:
        arrays={key:array_reader(base,row[key],shape)for key,shape in [('candidate_body',(5595,3)),('parent_body',(5595,3)),('candidate_eye',(3968,3)),('parent_eye',(3968,3))]}
        verify_frame_state(row,physical_poses[row['index']])
        results.append(frame_evaluator(source,arrays['candidate_body'][source.body_indices],arrays['parent_body'][source.old_indices],arrays['candidate_eye'][source.eye_indices],arrays['parent_eye'][source.eye_indices],allowed,{'index':row['index'],'time_s':row['time_s'],'key':row['key']},all_body_rest_contact_faces))
    g.need(len(results)==129,'posed_interface_samples_incomplete');return results

def run(phase,out,poses=None):
    started=time.monotonic();g.need(not out.exists(),'fresh_output_required');g.need(not out.resolve().is_relative_to(s.APP.parent.parent.resolve()),'output_inside_application_forbidden')
    source=s.Sources();pins=code_pins();source.cheap_tables();structure=source.full_frozen_structure()
    total=sum(len(s.attribute(source.doc,source.binary,p['indices']))//3 for mesh in source.doc['meshes']for p in mesh['primitives']);g.need(total==17390 and total<=20000,'total_triangle_cap')
    base_components=components(source,source.eye);allowed,ledger=source_interface_faces(source,base_components)
    # Source globe is immutable; explicitly reject proper self-intersections once.
    for side,c in base_components.items():g.need(not proper_pairs(c.triangles,set(range(len(c.triangles))),source.crosses),'source_globe_self_intersection',side)
    all_body_rest_pairs=globe_pairs(source.old_body,set(range(len(source.old_body))),source.eye,source.crosses);all_body_rest_contact_faces={j for i,j in all_body_rest_pairs}
    rest=evaluate_frame(source,source.body,source.old_body,source.eye,source.eye,allowed,{'kind':'rest'},all_body_rest_contact_faces)
    result={'mode':s.MODE,'phase':phase,'parent_sha256':s.EXPECTED[s.PARENT],'candidate_sha256':s.EXPECTED[s.CANDIDATE],'recipe_sha256':s.EXPECTED[s.RECIPE],'kernel_sha256':s.EXPECTED[s.KERNEL],'code_pins':pins,'policy_sha256':s.sha(POLICY.read_bytes()),'structure':structure,'prior11_corruption_controls':{'receipt_sha256':s.EXPECTED[s.PRIOR_TOPOLOGY_CONTROLS],'identical_source_candidate_recipe_qualifier_pins':True,'actually_rerun_by_this_phase':False},'triangles':total,'source_interface_faces':{k:sorted(v)for k,v in allowed.items()},'source_interface_ledger':ledger,'source925_all_BODY_globe_rest_pairs':all_body_rest_pairs,'source925_all_BODY_globe_rest_contact_faces':sorted(all_body_rest_contact_faces),'rest':rest,'posed129':'UNRUN','old_modes_and_frozen_rejection_unchanged':True,'source_adoption':False,'photographic_acceptance':False}
    if phase=='posed':
        g.need(poses is not None,'native_pose_capture_required');raw=poses.read_bytes();g.need(s.sha(raw)==s.QUALIFIED_CAPTURE_MANIFEST_SHA,'exact_qualified_capture_manifest_required');manifest=json.loads(raw);frames=verify_pose_grid(manifest);capture_result=verify_capture_result(poses.parent,manifest);physical_poses=capture_result['actual_physical']['poses'];g.need(len(physical_poses)==129,'actual_physical_pose_inventory');result['pose_capture_manifest_sha256']=s.sha(raw);result['posed_frames']=[]
        result['posed_frames']=traverse_pose_frames(source,frames,poses.parent,allowed,all_body_rest_contact_faces,physical_poses);result['posed129']='ALL129_SOCKET_INTERFACE_SAMPLES_PASS_ONLY'
    source.unchanged();g.need(code_pins()==pins,'qualification_code_changed_during_run')
    result.update(status='EXTERNAL_SOCKET_STATIC_ONLY_PASS'if phase=='static'else'EXTERNAL_SOCKET_STATIC_AND_NATIVE129_ONLY_PASS',seconds=time.monotonic()-started,scope='Exact source-bound socket qualification only; no whole app/photo/continuous motion/canonical adoption verdict.')
    out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'status':result['status'],'seconds':result['seconds'],'out':str(out)}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--mode',required=True,choices=[s.MODE]);p.add_argument('--phase',required=True,choices=['static','posed']);p.add_argument('--out',required=True,type=Path);p.add_argument('--poses',type=Path);a=p.parse_args()
    try:run(a.phase,a.out,a.poses)
    except Exception as error:
        if not a.out.exists()and a.out.parent.is_dir()and not a.out.resolve().is_relative_to(s.APP.parent.parent.resolve()):a.out.write_text(json.dumps({'mode':s.MODE,'phase':a.phase,'status':'FAILED_NO_ADOPTION','error':str(error),'error_type':type(error).__name__,'source_adoption':False,'photographic_acceptance':False},indent=2)+'\n')
        raise
