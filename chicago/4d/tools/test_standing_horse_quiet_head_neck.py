"""Exact quiet15 current selection and preserved normal-child lineage, source only."""
from pathlib import Path
import base64,copy,hashlib,json,sys
APP=Path(__file__).resolve().parents[1];REPO=APP.parents[1];PACKAGE=APP/'tools/transport/horse_quiet_head_neck_idle_v6'
SHA='badca71fb2ab7596be9447adaf01b3d035d5a59c7b844bc27b500d0a004d78a6';MODE='quiet_head_neck_idle_v6';CLIP='sevket_reconstructed_quiet_head_neck_idle_v1'
def old_json(relative):
    fixture=json.loads((APP/'tools/fixtures/horse-before-quiet-v6-selection.json').read_bytes());cert_raw=(APP/'data/transport/parked/standing-horse-planted/quiet-head-neck-v6-qualification-summary.json').read_bytes();assert hashlib.sha256(cert_raw).hexdigest()==SHA;cert=json.loads(cert_raw)
    assert fixture['phaseA_TREE']==cert['phaseA_source_binding']['TREE'];row=next(x for x in fixture['records']if x['path']==relative);expected=next(x for x in cert['phaseA_source_binding']['source_files']if x['path']=='chicago/4d/'+relative);raw=base64.b64decode(row['original_bytes_base64'],validate=True);assert len(raw)==row['bytes']==expected['bytes'] and hashlib.sha256(raw).hexdigest()==row['sha256']==expected['sha256'];return json.loads(raw)

def check_source_selection():
    import importlib.util
    sys.path.insert(0,str(PACKAGE))
    # Keep qualifier imports separate from historical recorded_qualification modules.
    for name in ['quiet_source','canonical_guard','qualify_quiet_head_neck']:
        if name not in sys.modules:
            spec=importlib.util.spec_from_file_location(name,PACKAGE/(name+'.py'));m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m)
    spec=importlib.util.spec_from_file_location('quiet_recorded_qualification',PACKAGE/'recorded_qualification.py');record=importlib.util.module_from_spec(spec);spec.loader.exec_module(record)
    c=record.read_certificate(expected_sha256=SHA);s=json.loads((APP/'data/transport/parked/horse-sevket-sidecar.json').read_bytes());a=json.loads((APP/'assets/authored/transport/horse_standing/SOURCE.json').read_bytes());p=json.loads((APP/'data/transport/parked/standing-horses.json').read_bytes());r=s['runtime_asset']
    assert r['source_qualification_mode']==MODE and r['sha256']==c['runtime_candidate_sha256'] and r['bytes']==4165556 and r['file']==record.RUNTIME_FILE and r['qualification_sha256']==SHA and r['qualification_file']=='transport/parked/standing-horse-planted/quiet-head-neck-v6-qualification-summary.json' and r['animation_count']==1 and r['declared_idle_clip']==CLIP and r['old_certificate_transferred'] is False
    raw=(APP/'renderers/web'/r['file']).read_bytes();assert len(raw)==r['bytes'] and hashlib.sha256(raw).hexdigest()==r['sha256'];assert a['runtime_derivative']==r
    old=old_json('data/transport/parked/horse-sevket-sidecar.json');assert s['preserved_eye_smooth_normals_runtime_asset']==old['runtime_asset'] and s['preserved_eye_smooth_normals_idle']==old['idle']
    restored=copy.deepcopy(s);restored['runtime_asset']=restored.pop('preserved_eye_smooth_normals_runtime_asset');restored['idle']=restored.pop('preserved_eye_smooth_normals_idle');restored['status']=old['status'];assert restored==old,'All original contact/scale/material/credit/source data and preserved lineage unchanged'
    olda=old_json('assets/authored/transport/horse_standing/SOURCE.json');assert a['preserved_eye_smooth_normals_parent_derivative']==olda['runtime_derivative'];restored=copy.deepcopy(a);restored['runtime_derivative']=restored.pop('preserved_eye_smooth_normals_parent_derivative');assert restored['runtime_adaptations'][:len(olda['runtime_adaptations'])]==olda['runtime_adaptations'];restored['runtime_adaptations']=olda['runtime_adaptations'];assert restored==olda
    oldp=old_json('data/transport/parked/standing-horses.json');assert p['models']['sevket_horse_standing_development_01']['file']==r['file'];assert p['scenes']['1835'][0]['animation']['clip']==CLIP;restored=copy.deepcopy(p);restored['models']['sevket_horse_standing_development_01']['file']=oldp['models']['sevket_horse_standing_development_01']['file'];restored['scenes']['1835'][0]['animation']['clip']=oldp['scenes']['1835'][0]['animation']['clip'];restored['status']=oldp['status'];assert restored==oldp,'All actual placement/support/material/capabilities unchanged'
    idle=s['idle'];assert idle['loaded_qualification_asset_sha256']==r['sha256'] and idle['loaded_qualification_sha256']==SHA and idle['loaded_qualification_status']==c['status'] and idle['loaded_raw_result_sha256']==c['actual_receipts']['capture']['sha256'] and idle['loaded_capture_manifest_sha256']==c['actual_receipts']['capture_manifest']['sha256'] and idle['loaded_posed_result_sha256']==c['actual_receipts']['posed129']['sha256'] and idle['actual_yard_native_visual_world_GPU_qualified'] is False
    for change in [lambda x:x.__setitem__('old_certificate_transferred',True),lambda x:x.__setitem__('tail_gesture_enabled',True),lambda x:x['actual_code_pins'].__setitem__(next(iter(x['actual_code_pins'])),'0'*64),lambda x:x['all129_socket_samples'][37].__setitem__('time_s',0)]:
        bad=copy.deepcopy(c);change(bad)
        try:record.verify_recorded_certificate(bad)
        except (ValueError,AssertionError):pass
        else:raise AssertionError('Actual bounded certificate corruption accepted')
    return c

def preserved_normal_source():
    check_source_selection();sys.path.insert(0,str(APP/'tools/transport/horse_eye_smooth_normals_v1'));import normal_child_source as child
    source=child.Sources(APP,APP/'assets/authored/transport/horse_standing');source.cheap_tables();source.unchanged();return source
if __name__=='__main__':
    check_source_selection();print('PASS exact quiet15 selected source, actual finite129 certificate, four corruption controls, preserved complete bd443 metadata; world/photo/app acceptance separate')
