"""Exact e49 source selection/derivation/region controls and native static port.

Normal gate validates recorded NEW e49 actual129 receipts, never relabels this
source command as a browser run. Old5a remains a separately checked parent mode.
"""
import argparse,ast,collections,copy,hashlib,json,re,struct,sys,tempfile,time
from pathlib import Path
APP=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(APP/'tools/transport/horse_upper_orbital_transition_v1'))
import upper_orbital_source as boundary
import socket_geometry as geometry

CHILD_LIBERTY='L-horse-upper-eye-contour-3088'
PARENT_LIBERTY='L-horse-anatomy-master-3088'

def check_liberty_provenance(spec, source, text):
    """Use the actual native heading grammar without running its compiler."""
    module=ast.parse((APP/'tools/compile_liberties.py').read_text())
    call=next(n.value for n in module.body if isinstance(n,ast.Assign) and
              any(isinstance(t,ast.Name) and t.id=='HEADING' for t in n.targets))
    grammar=re.compile(ast.literal_eval(call.args[0]),re.MULTILINE)
    counts=collections.Counter(match[0] for match in grammar.findall(text))
    g=boundary.generator
    g.need(not any(value>1 for value in counts.values()),'liberty_duplicate_id')
    g.need(counts[CHILD_LIBERTY]==1 and counts[PARENT_LIBERTY]==1,'liberty_child_or_ancestry_missing')
    g.need(spec['anatomy']['liberty']==CHILD_LIBERTY,'liberty_active_child_reference')
    g.need(all(name in source['historical_evidence_limits'] for name in [CHILD_LIBERTY,PARENT_LIBERTY]),
           'liberty_authored_source_scope')

def check_active_idle_qualification(spec, certificate):
    """Bind active idle provenance to the actual selected asset and locked record."""
    idle=spec['idle'];runtime=spec['runtime_asset'];g=boundary.generator
    g.need(idle['loaded_qualification_asset_sha256']==runtime['sha256']==certificate['candidate_sha256'],
           'idle_selected_asset')
    g.need(idle['loaded_qualification_file']==runtime['qualification_file'] and
           idle['loaded_qualification_sha256']==runtime['qualification_sha256']==boundary.CERTIFICATE_SHA and
           idle['loaded_qualification_status']==certificate['status'],'idle_selected_certificate')
    g.need(idle['loaded_raw_result_sha256']==certificate['actual_receipts']['capture']['sha256'] and
           idle['loaded_capture_manifest_sha256']==certificate['physical_capture_manifest_sha256'] and
           idle['loaded_posed_result_sha256']==certificate['actual_receipts']['posed129']['sha256'],
           'idle_selected_capture')
    g.need(idle['qualification_recorded_on']=='2026-10-27' and
           idle['physical129_rerun_in_current_recovery'] is False and
           idle['external_raw_capture_arrays_available'] is False,'idle_historical_scope')
    parent=idle['historical_upper_lid_qualification']
    g.need(parent['asset_sha256']==certificate['parent5a_sha256'] and
           parent['loaded_qualification_sha256']==boundary.ancestor.CERTIFICATE_SHA,
           'idle_preserved_parent_qualification')

def check_source_selection():
    source=boundary.Sources();source.cheap_tables();spec=json.loads((APP/'data/transport/parked/horse-sevket-sidecar.json').read_bytes());old=json.loads((APP/'tools/fixtures/horse-anatomy-r3-sidecar-v1.json').read_bytes());runtime=spec['runtime_asset']
    geometry.need(runtime['source_qualification_mode']==boundary.MODE and runtime['sha256']==boundary.generator.CANDIDATE_SHA and runtime['bytes']==4159196,'orbital_selected_source_identity')
    geometry.need(runtime['file']=='transport/standing-horse/horse-sevket-upper-orbital-transition-v1.glb'and runtime['orbital_parent5a_sha256']==boundary.generator.PARENT_SHA,'orbital_selected_parent_path')
    geometry.need(runtime['qualification_sha256']==boundary.CERTIFICATE_SHA and runtime['qualification_file']=='transport/parked/standing-horse-planted/upper-orbital-transition-v1-qualification-summary.json','orbital_selected_certificate')
    geometry.need((APP/'renderers/web'/runtime['file']).read_bytes()==source.raw[boundary.CANDIDATE],'orbital_exact_runtime_copy')
    for k in ['source','contacts','contact_mesh','ground_support','proposed_static_support_pose','runtime_scale_m_per_unit','runtime_origin_m','source_inventory']:geometry.need(spec[k]==old[k],'orbital_unchanged_foot_frame_credit',k)
    geometry.need(spec['preserved_anatomy_r3_runtime_asset']==old['runtime_asset'],'orbital_preserved925_contract')
    legacy=spec['preserved_upper_lid_runtime_asset'];geometry.need(legacy['sha256']==boundary.generator.PARENT_SHA and legacy['source_qualification_mode']==boundary.ancestor.MODE and (APP/'renderers/web'/legacy['file']).read_bytes()==source.base.raw[boundary.ancestor.CANDIDATE],'orbital_preserved5a_mode')
    authored=json.loads((boundary.SOURCE/'SOURCE.json').read_bytes());geometry.need(authored['runtime_derivative']==runtime and authored['preserved_upper_lid_parent_derivative']==legacy,'orbital_authored_provenance')
    placement=json.loads((APP/'data/transport/parked/standing-horses.json').read_bytes());original=json.loads((APP/'tools/fixtures/horse-anatomy-r3-placements-v1.json').read_bytes());geometry.need(placement['models']['sevket_horse_standing_development_01']['file']==runtime['file'],'orbital_placement_path');placement['models']['sevket_horse_standing_development_01']['file']=original['models']['sevket_horse_standing_development_01']['file'];placement['status']=original['status'];geometry.need(placement==original,'orbital_placement_support_capability')
    check_active_idle_qualification(spec,source.certificate)
    check_liberty_provenance(spec,authored,(APP/'docs/LIBERTIES.md').read_text())
    source.unchanged();return source

def source_controls(source):
    g=boundary.generator;data=source.raw[boundary.CANDIDATE];d,b=g.decode(data);pr=d['meshes'][1]['primitives'][0];a=pr['attributes'];eye=d['meshes'][2]['primitives'][0];hair=d['meshes'][0]['primitives'][0];checks=[]
    def inspect(bad):return g.inspect(source.base.raw[boundary.ancestor.CANDIDATE],bad,source.raw[boundary.RECIPE],source.raw[boundary.ancestor.ORIGINAL],source.raw[boundary.ancestor.PARENT])
    def mutate(index,row,k,delta):
        bb=bytearray(b);at=g.offset(d,index,row)+4*k;old=struct.unpack_from('<f',bb,at)[0];struct.pack_into('<f',bb,at,old+delta);return g.encode(d,bytes(bb))
    def refused(name,bad,code):
        try:inspect(bad)
        except g.Rejected as e:assert str(e)==code,(name,str(e),code);checks.append(name);return
        raise AssertionError('Actual corruption accepted: '+name)
    for name,index,row,k,delta,code in [('outside_POSITION',a['POSITION'],392,0,.003,'outside_POSITION_region'),('changed_Y',a['POSITION'],403,1,.001,'protected_POSITION_YZ'),('outside_NORMAL',a['NORMAL'],100,0,.01,'outside_NORMAL_region'),('EYE_position',eye['attributes']['POSITION'],0,0,.002,'protected_mesh2_POSITION'),('HAIR_position',hair['attributes']['POSITION'],0,0,.002,'protected_mesh0_POSITION'),('EYE_UV',eye['attributes']['TEXCOORD_0'],0,0,.01,'protected_mesh2_TEXCOORD_0'),('BODY_UV_exact403',a['TEXCOORD_0'],403,0,.001,'protected_BODY_TEXCOORD_0'),('BODY_skin_exact403',a['WEIGHTS_0'],403,0,.02,'protected_BODY_WEIGHTS_0'),('over20mm',a['POSITION'],403,0,.032,'original_20mm_caps')]:refused(name,mutate(index,row,k,delta),code)
    bb=bytearray(b);ac=d['accessors'][pr['indices']];assert ac['componentType']==5123;at=d['bufferViews'][ac['bufferView']]['byteOffset']+ac.get('byteOffset',0);bb[at:at+2],bb[at+2:at+4]=bb[at+2:at+4],bb[at:at+2];refused('index_winding',g.encode(d,bytes(bb)),'protected_BODY_indices')
    bb=bytearray(b);bb[d['bufferViews'][d['images'][0]['bufferView']]['byteOffset']+30]^=1;refused('original_embedded_image',g.encode(d,bytes(bb)),'immutable_d454_prefix')
    doc=copy.deepcopy(d);doc['materials'][1]['doubleSided']=False;refused('protected_material',g.encode(doc,b),'unrelated_JSON_document')
    doc=copy.deepcopy(d);doc['asset']['extras']['upper_orbital_transition_v1']['recipe_sha256']='0'*64;refused('recipe_metadata',g.encode(doc,b),'child_recipe_metadata')
    return checks

def run(source_only=False):
    start=time.monotonic();source=check_source_selection();checks=source_controls(source)
    actual=json.loads((APP/'data/transport/parked/horse-sevket-sidecar.json').read_bytes())
    authored=json.loads((boundary.SOURCE/'SOURCE.json').read_bytes())
    liberties=(APP/'docs/LIBERTIES.md').read_text()
    for name,document,text,reason in [
        ('duplicate_child_liberty',actual,liberties+'\n### '+CHILD_LIBERTY+' — duplicate control\n','liberty_duplicate_id'),
        ('missing_child_liberty',actual,liberties.replace('### '+CHILD_LIBERTY+' —','### L-control-missing-child —'),'liberty_child_or_ancestry_missing'),
        ('stale_parent_active_liberty',copy.deepcopy(actual),liberties,'liberty_active_child_reference')]:
        if name=='stale_parent_active_liberty':document['anatomy']['liberty']=PARENT_LIBERTY
        try:check_liberty_provenance(document,authored,text)
        except boundary.generator.Rejected as e:assert str(e)==reason;checks.append(name)
        else:raise AssertionError('Invalid Liberty provenance accepted: '+name)
    parent=actual['idle']['historical_upper_lid_qualification']
    for name,key,value,reason in [
        ('stale_parent_idle_asset','loaded_qualification_asset_sha256',parent['asset_sha256'],'idle_selected_asset'),
        ('stale_parent_idle_file','loaded_qualification_file',parent['loaded_qualification_file'],'idle_selected_certificate'),
        ('stale_parent_idle_certificate','loaded_qualification_sha256',parent['loaded_qualification_sha256'],'idle_selected_certificate'),
        ('stale_parent_idle_capture','loaded_raw_result_sha256',parent['loaded_raw_result_sha256'],'idle_selected_capture')]:
        corrupted=copy.deepcopy(actual);corrupted['idle'][key]=value
        try:check_active_idle_qualification(corrupted,source.certificate)
        except boundary.generator.Rejected as e:assert str(e)==reason;checks.append(name)
        else:raise AssertionError('Stale parent idle provenance accepted: '+name)
    for name,key,value,reason in [('replayed_nonrest','time_s',0,'orbital_recorded_pose_grid'),('new_bound_violation','BODY_max_upper_m',.015,'orbital_recorded_pose_limits')]:
        c=copy.deepcopy(source.certificate);c['all129_socket_samples'][37][key]=value
        try:boundary.verify_recorded_certificate(c)
        except geometry.Rejected as e:assert e.code==reason;checks.append(name)
        else:raise AssertionError(name+' accepted')
    for name,mutate,reason in [('raised_limit',lambda c:c['limits_m'].__setitem__('BODY_locus',.01401),'orbital_recorded_limits'),('photo_overclaim',lambda c:c.__setitem__('photographic_acceptance',True),'orbital_recorded_overclaim')]:
        c=copy.deepcopy(source.certificate);mutate(c)
        try:boundary.verify_recorded_certificate(c)
        except geometry.Rejected as e:assert e.code==reason;checks.append(name)
        else:raise AssertionError(name+' accepted')
    if not source_only:
        import static_source
        with tempfile.TemporaryDirectory(prefix='horse-orbital-native-source-') as td:static_source.run(Path(td)/'actual-static.json')
    source.unchanged();print(json.dumps({'status':'PARTIAL_SOURCE_ONLY_STATIC_UNRUN'if source_only else'CURRENT_E49_SOURCE_NATIVE_STATIC_PASS_WITH_RECORDED_NEW129','candidate_sha256':boundary.generator.CANDIDATE_SHA,'meaningful_controls':checks,'actual_recorded_keys':65,'actual_recorded_midpoints':64,'native129_rerun_by_this_command':False,'photographic_acceptance':False,'whole_app_gate':False,'seconds':time.monotonic()-start}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source-only',action='store_true');run(p.parse_args().source_only)
