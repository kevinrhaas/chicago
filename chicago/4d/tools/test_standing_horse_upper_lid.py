"""Current or preserved-parent upper-lid mode checks, static proof and controls.

Recorded actual native129 evidence is byte-bound, never relabelled as a browser
run by this source gate. --source-only is explicitly a partial development check.
"""
import argparse,copy,hashlib,json,sys,tempfile,time
from pathlib import Path
import numpy as np
APP=Path(__file__).resolve().parents[1]
SOURCE=APP/'assets/authored/transport/horse_standing'
PACKAGE=APP/'tools/transport/horse_socket_interface_v1'
sys.path.insert(0,str(PACKAGE));sys.path.insert(0,str(SOURCE))
import socket_sources as boundary
import socket_geometry as geometry
import generate_upper_lid_strip_v1 as generator


def check_source_selection():
    source=boundary.Sources();source.cheap_tables()
    spec=json.loads((APP/'data/transport/parked/horse-sevket-sidecar.json').read_bytes())
    old=json.loads((APP/'tools/fixtures/horse-anatomy-r3-sidecar-v1.json').read_bytes())
    selected=spec['runtime_asset']
    runtime=spec['preserved_upper_lid_runtime_asset']if selected.get('source_qualification_mode')in('upper_orbital_transition_v1','eye_smooth_normals_v1','quiet_head_neck_idle_v6')else selected
    geometry.need(runtime['source_qualification_mode']==boundary.MODE and runtime['sha256']==boundary.EXPECTED[boundary.CANDIDATE]and runtime['bytes']==4158848,'selected_socket_mode_identity')
    geometry.need(runtime['file']=='transport/standing-horse/horse-sevket-upper-lid-strip-v1.glb'and runtime['upper_lid_parent_sha256']==boundary.EXPECTED[boundary.PARENT],'selected_socket_parent_or_path')
    geometry.need(runtime['qualification_sha256']==boundary.CERTIFICATE_SHA and runtime['qualification_file']=='transport/parked/standing-horse-planted/upper-lid-strip-v1-qualification-summary.json','selected_socket_qualification_binding')
    geometry.need((APP/'renderers/web'/runtime['file']).read_bytes()==source.raw[boundary.CANDIDATE],'selected_runtime_not_exact_authored_source')
    geometry.need((APP/'renderers/web/transport/standing-horse/horse-sevket-anatomy-v2.glb').read_bytes()==source.raw[boundary.PARENT],'legacy925_runtime_changed')
    for key in ['source','contacts','contact_mesh','ground_support','proposed_static_support_pose','runtime_scale_m_per_unit','runtime_origin_m','source_inventory']:
        geometry.need(spec[key]==old[key],'unchanged_foot_frame_or_credit_contract',key)
    geometry.need(spec['preserved_anatomy_r3_runtime_asset']==old['runtime_asset'],'legacy925_runtime_provenance_changed')
    placement=json.loads((APP/'data/transport/parked/standing-horses.json').read_bytes())
    legacy=json.loads((APP/'tools/fixtures/horse-anatomy-r3-placements-v1.json').read_bytes())
    geometry.need(placement['models']['sevket_horse_standing_development_01']['file']==selected['file'],'selected_placement_asset_mismatch')
    placement['models']['sevket_horse_standing_development_01']['file']=legacy['models']['sevket_horse_standing_development_01']['file'];placement['status']=legacy['status']
    if selected.get('source_qualification_mode')=='quiet_head_neck_idle_v6':
        geometry.need(placement['scenes']['1835'][0]['animation']['clip']=='sevket_reconstructed_quiet_head_neck_idle_v1','quiet_selected_clip')
        placement['scenes']['1835'][0]['animation']['clip']=legacy['scenes']['1835'][0]['animation']['clip']
    geometry.need(placement==legacy,'placement_support_material_or_capability_changed')
    source.unchanged();return source


def run(source_only=False):
    started=time.monotonic();source=check_source_selection()
    raw,receipt=generator.derive(source.raw[boundary.PARENT],source.raw[boundary.ORIGINAL],source.raw[boundary.RECIPE],APP/'data/sources')
    geometry.need(raw==source.raw[boundary.CANDIDATE],'repeatable_source_not_exact_qualified5a')
    controls=[]
    def refuse(name,reason,fn):
        try:fn()
        except geometry.Rejected as error:
            assert error.code==reason,(name,error.code,reason);controls.append(name)
        else:raise AssertionError('Meaningful control incorrectly accepted: '+name)
    changed=copy.deepcopy(source.certificate);changed['all129_socket_samples'][37]['time_s']=0
    refuse('recorded_nonrest_time_replay','recorded_pose_grid',lambda:boundary.verify_recorded_certificate(changed))
    changed=copy.deepcopy(source.certificate);changed['limits_m']['BODY_locus']=.01401
    refuse('recorded_cap_increase','recorded_certificate_limits',lambda:boundary.verify_recorded_certificate(changed))
    changed=copy.deepcopy(source.certificate);changed['all129_socket_samples'][37]['BODY_max_upper_m']=.015
    refuse('recorded_nonrest_bound_violation','recorded_pose_limits',lambda:boundary.verify_recorded_certificate(changed))
    changed=copy.deepcopy(source.certificate);changed['photographic_acceptance']=True
    refuse('recorded_photo_overclaim','recorded_certificate_overclaim',lambda:boundary.verify_recorded_certificate(changed))
    if not source_only:
        import socket_controls,socket_orchestration_controls,socket_traversal_control,socket_qualification
        with tempfile.TemporaryDirectory(prefix='horse-lid-native-source-')as td:
            root=Path(td)
            socket_controls.run(root/'geometry-source-controls.json')
            socket_orchestration_controls.run(root/'policy-grid-state-controls.json')
            socket_traversal_control.run(root/'production-traversal-control.json')
            socket_qualification.run('static',root/'actual-static-socket.json')
    source.unchanged()
    print(json.dumps({'status':'PARTIAL_SOURCE_ONLY_PASS_STATIC_UNRUN'if source_only else'PRESERVED5A_SOURCE_AND_STATIC_PASS_WITH_RECORDED_EXACT_NATIVE129','candidate_sha256':hashlib.sha256(raw).hexdigest(),'source_controls':controls,'recorded_actual_keys':65,'recorded_actual_midpoints':64,'native129_rerun_by_this_command':False,'photographic_acceptance':False,'whole_app_gate_acceptance':False,'seconds':time.monotonic()-started}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source-only',action='store_true');run(p.parse_args().source_only)
