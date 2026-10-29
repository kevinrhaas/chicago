"""Source/UV/skin binding helpers; these do NOT perform full qualification."""
import ast,copy,hashlib,importlib.util,json,struct,subprocess
from pathlib import Path
from types import SimpleNamespace
import numpy as np
from socket_geometry import Rejected,need

MODE='canonical_socket_interface_v1'
APP=Path(__file__).resolve().parents[3]
PACKET=Path(__file__).resolve().parent/'fixtures'
SOURCE=APP/'assets/authored/transport/horse_standing'
PARENT=SOURCE/'horse-sevket-anatomy-v2.glb'
CANDIDATE=SOURCE/'horse-sevket-upper-lid-strip-v1.glb'
ORIGINAL=SOURCE/'horse-sevket-v16-planted-standing-eye-uv-v1.glb'
RECIPE=SOURCE/'upper-lid-strip-v1-recipe.json'
KERNEL=PACKET/'crossing_kernel_v2.py'
QUALIFIER=PACKET/'qualify_strip_topology_control_v2.py'
LEDGER=PACKET/'STATIC-BODY-CROSSINGS-v2.json'
PRIOR_TOPOLOGY_CONTROLS=PACKET/'STATIC-TOPOLOGY-SOURCE-V2.json'
STRICT_REJECTION=PACKET/'ACTUAL-STATIC-PATCH-CROSSINGS.json'
CERTIFICATE=APP/'data/transport/parked/standing-horse-planted/upper-lid-strip-v1-qualification-summary.json'
CERTIFICATE_SHA='5fb50fed07a041c76e2a1300a9040600628f59671b8a27d7f4483bc8dc880ca1'
EXPECTED={PARENT:'925fac957110b9b57b95c5abfed17fabf29f868b173f38f0569d984dd9999a48',CANDIDATE:'5a2b2e87c3931e3ab82be3ce3bc69724a0a088aac30920cea9ad348bbaf8fad5',ORIGINAL:'d4544c2845256858dfa614235bcb37cb964ab63095a53a2436225182cefbb914',RECIPE:'f77e115a340a6cbb8d6efb1b7887c8cdba001a47f493b97be6ffb0eee72dd133',KERNEL:'8bf97472ae13d5d6d764ac9f381f0a2bfbf8aea6108932382d705a1372a4ae33',QUALIFIER:'eab41c8a30d7a36b377babc9c3852b4e43a54cb357882d97a8517a5e11d6d21f',LEDGER:'c23d46bc7430a059caca290a09610d78d80c3b15edf3c42596e92daadb2a6da6',PRIOR_TOPOLOGY_CONTROLS:'e2a9bbf6973f32b9442472780feb8043519828f3817ec40a98c4b5f06796d0bd',STRICT_REJECTION:'b335777297a39a6dee1bd2304344df8cdfdb2d00076cf00d132717633a0bc661',CERTIFICATE:CERTIFICATE_SHA}
PARENT_HEAD='db71c0c6d84b17d1bcc3786f872d0b2595a85ce4' # Historical source checkpoint, not the new selected HEAD.
EXPECTED_INTERFACE={-1:{3782,3783,3786,3787,3790,3791,3802,3803,3806,3831},1:{3784,3785,3788,3789,3792,3793,3804,3805,3808,3833}}
PHYSICAL_LOOP_SHA='a8515b35e18a058673fe330a127eba129851f324915858971e3b683bc4d259a1'
QUALIFIED_CAPTURE_MANIFEST_SHA='f5384e8c38c0c1f6e683b8d590260a81d3e3911836024684d368e854cd5673d8'
EXPECTED[APP/'assets/authored/transport/horse_standing/generate_anatomy_v1.py']='3dfba591b0d2fe582b5a85582653118568aa2811549188e78a741bf7f45df614'
EXPECTED[APP/'assets/authored/transport/horse_standing/generate_anatomy_v2.py']='3eba050a3c2f091618b8db15e141cf50e02eb5604ef302fb0f9d7c8fc0342634'
EXPECTED[APP/'assets/authored/transport/horse_standing/anatomy_topology_v2.py']='0d81b65e3cc3a8246467f94f0e8a5a58fa98abae17dc561020d1db7afbd7057c'
EXPECTED[APP/'assets/authored/transport/horse_standing/anatomy-v2-recipe.json']='5009e561a386c2ed5f1a6082f1855a97f22e510f76412f93b8ce65849ddd2887'
EXPECTED[APP/'tools/fixtures/horse-anatomy-parent-sidecar-v1.json']='4ec44024d4fbefae88b8f0a1deb3be92503768b65dba590c5762691ce3b9c924'
EXPECTED[APP/'tools/transport/check_horse_anatomy_crossings.py']='a8590da62511ae7831a6e543d1671b7f7ddb16ca86968637c4bc0136c5c83fed'
EXPECTED[APP/'tools/test_standing_horse_eye_uv_boundary.py']='acfd9b2c2beb7f8941e84edf11bdff58f105a3997e07a8805deacb2c78fba2ee'
EXPECTED[APP/'assets/authored/transport/horse_standing/generate_upper_lid_strip_v1.py']='7e6ed1ca8f03179743d2305dd864769e794ebfa56c2cea082a8da660063bba39'
EXPECTED[APP/'tools/transport/horse_socket_interface_v1/socket_geometry.py']='41c4394cbf3f415c2e7cc4c362b3652d736ba2ccb04a920b4cfb0b3c1a3764a8'
EXPECTED[APP/'tools/transport/horse_socket_interface_v1/fixtures/UNCHANGED-PHYSICAL-METRIC-LOOP.mjs.txt']='a8515b35e18a058673fe330a127eba129851f324915858971e3b683bc4d259a1'
EXPECTED[APP/'tools/transport/horse_socket_interface_v1/fixtures/NATIVE-PRODUCER-readback-socket129.mjs']='80ba11d5f3daa9491e0b83ea49ed20a5d01dacc5580c270d554dac4757af3350'
EXPECTED[APP/'tools/fixtures/horse-anatomy-r3-sidecar-v1.json']='e6e8ea252115f4b1c183eda52ad4f2dd54b4276872034324917592051718a1f7'
EXPECTED[APP/'tools/fixtures/horse-anatomy-r3-placements-v1.json']='e0576d7b3007341db51c1acbd3b698f71360d5bd2bac910c2760baaeb6f3dec1'
EXPECTED[APP/'tools/transport/horse_socket_interface_v1/fixtures/ORIGINAL-PHYSICAL-LIMITS.json']='b64a5784c0b8310b5d0e054d10d9052edb0034938ed61d46e2b819230ff7bb54'
EXPECTED[APP/'data/sources/ellenberger_baum_dittrich_equine_plates.json']='a290feb642ecc07162706d3de10a16283842cf08f811913167c304473aeb1677'
EXPECTED[APP/'data/sources/seton_1892_equine_skeleton.json']='6656abd5b55261c000cce85d1b861ae9cb501b0e6f577bf72934769cefbcf769'
EXPECTED[APP/'data/sources/vassil_2014_konik_horse_anatomy.json']='b3e1d3aedba580f468741460c3fd0c61edab1e701c5c7175d022e0dc51f27902'
EXPECTED[APP/'data/sources/joselodos_2025_horse_anatomy.json']='34c93b53758835d723b0093b2391b33e0bc569c56d263f8c7c475826d4d09ff6'

def sha(raw):return hashlib.sha256(raw).hexdigest()

def read_glb(raw):
    need(len(raw)>=28 and struct.unpack_from('<4sII',raw)==(b'glTF',2,len(raw)),'invalid_glb_header')
    n,kind=struct.unpack_from('<II',raw,12);need(kind==0x4e4f534a,'missing_json_chunk')
    doc=json.loads(raw[20:20+n]);m,kind=struct.unpack_from('<II',raw,20+n)
    need(kind==0x004e4942 and 28+n+m==len(raw),'invalid_bin_chunk')
    return doc,raw[28+n:]

def attribute(doc,binary,index):
    a=doc['accessors'][index];v=doc['bufferViews'][a['bufferView']]
    dtype=np.dtype({5126:'<f4',5125:'<u4',5123:'<u2',5121:'u1'}[a['componentType']]);width={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}[a['type']]
    return np.ndarray((a['count'],width),dtype=dtype,buffer=binary,offset=v.get('byteOffset',0)+a.get('byteOffset',0),strides=(v.get('byteStride',width*dtype.itemsize),dtype.itemsize)).copy()

def mesh(doc,binary,index):
    p=doc['meshes'][index]['primitives'][0]
    positions=attribute(doc,binary,p['attributes']['POSITION']).astype(np.float64)
    indices=attribute(doc,binary,p['indices']).reshape(-1,3)
    need(np.isfinite(positions).all(),'nonfinite_source_position')
    return positions,indices,positions[indices]

def byte_offset(doc,index,row):
    a=doc['accessors'][index];v=doc['bufferViews'][a['bufferView']];width={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a['type']];size=width*{5126:4,5125:4,5123:2,5121:1}[a['componentType']]
    return v.get('byteOffset',0)+a.get('byteOffset',0)+row*v.get('byteStride',size)

def uv_skin_guard(doc,binary,parent_doc,parent_binary,recipe):
    """Cheap actual source-table controls; full frozen structural inspect is separate."""
    p=doc['meshes'][1]['primitives'][0];pp=parent_doc['meshes'][1]['primitives'][0];attrs=p['attributes'];pa=pp['attributes']
    need(attrs['TEXCOORD_0']==attrs['TEXCOORD_1'],'BODY_UV_alias_divergence')
    uv=attribute(doc,binary,attrs['TEXCOORD_0']);old=attribute(parent_doc,parent_binary,pa['TEXCOORD_0']);need(uv.shape==old.shape==(5595,2),'BODY_UV_count')
    rows={2410:[2372,2373,2411],2412:[2374,2375,2413]}
    need(recipe['maximum_internal_BODY_UV_displacement']==.00030 and {r['row']for r in recipe['internal_BODY_UV_repairs']}==set(rows),'unsupported_BODY_UV_policy')
    for row,parents in rows.items():
        expected=np.asarray(old[parents].astype(np.float64).sum(axis=0)/3,dtype='<f4')
        need(np.array_equal(uv[row],expected),'wrong_declared_BODY_UV_repair',row)
        need(float(np.linalg.norm(uv[row].astype(float)-old[row]))<=.00030,'BODY_UV_displacement')
    keep=np.ones(len(uv),dtype=bool);keep[list(rows)]=False
    need(np.array_equal(uv[keep],old[keep]),'undeclared_BODY_UV_mutation')
    for key in ['JOINTS_0','WEIGHTS_0']:
        need(np.array_equal(attribute(doc,binary,attrs[key]),attribute(parent_doc,parent_binary,pa[key])),'BODY_skin_mutation',key)
    e=doc['meshes'][2]['primitives'][0];pe=parent_doc['meshes'][2]['primitives'][0]
    need(e==pe,'globe_accessor_or_primitive_mutation')
    for key,index in e['attributes'].items():
        need(np.array_equal(attribute(doc,binary,index),attribute(parent_doc,parent_binary,pe['attributes'][key])),'globe_'+key+'_mutation')
    need(np.array_equal(attribute(doc,binary,e['indices']),attribute(parent_doc,parent_binary,pe['indices'])),'globe_index_mutation')
    need(doc['nodes']==parent_doc['nodes']and doc['skins']==parent_doc['skins'],'rig_or_skin_structure_mutation')
    return {'BODY_UV_exact_except_two_bound_repairs':True,'all_skin_and_globe_tables_exact':True,'scope':'Source tables only; no full topology or crossing verdict.'}

def original_prefix_guard(binary,original_binary):
    need(binary[:len(original_binary)]==original_binary,'original_d454_BIN_prefix_mutation')

def frozen_module(path,name):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def verify_recorded_certificate(cert):
    need(cert['schema']=='standing-horse-canonical-socket-qualification-summary-v1'and cert['mode']==MODE and cert['status']=='RECORDED_EXACT_SOURCE_STATIC_AND_NATIVE129_SOCKET_ONLY_PASS','recorded_certificate_scope')
    need(cert['candidate_sha256']==EXPECTED[CANDIDATE]and cert['parent925_sha256']==EXPECTED[PARENT]and cert['original_d454_sha256']==EXPECTED[ORIGINAL]and cert['recipe_sha256']==EXPECTED[RECIPE],'recorded_certificate_source')
    need(cert['physical_loop_bytes']==9176 and cert['physical_loop_sha256']==PHYSICAL_LOOP_SHA and cert['limits_m']=={'BODY_locus':.014,'globe_contact_locus':.007,'source_and_parent_displacement':.020},'recorded_certificate_limits')
    frames=cert['all129_socket_samples'];need(len(frames)==129,'recorded_pose_inventory')
    for i,r in enumerate(frames):
        need(r['index']==i and r['time_s']==i*3/32 and r['key']==(i//2 if i%2==0 else None),'recorded_pose_grid')
        need(r['BODY_pairs']==24 and r['globe_contacts']==82 and 0<=r['BODY_max_upper_m']<=.014 and 0<=r['CONTACT_max_upper_m']<=.007 and r['new_exterior_or_undeclared_or_patch_patch_crossings']==0,'recorded_pose_limits')
    physical=cert['actual_native_physical'];need(physical['status']=='LOADED_STANDING65_KEYS64_MIDPOINTS_PASS_ONLY'and physical['key_count']==65 and physical['midpoint_count']==64 and physical['failures']==[],'recorded_physical129')
    need(physical['original_physical_limits']['stance_patch_drift_m']==1e-5 and physical['original_physical_limits']['minimum_all_surface_y_m']==-1e-5,'recorded_original_physical_limits')
    need(physical['original_physical_limits']==json.loads((PACKET/'ORIGINAL-PHYSICAL-LIMITS.json').read_bytes()),'recorded_all_original_physical_limits')
    need(set(cert['closed_runs'])=={'static','native129','posed129'},'recorded_closed_phase_inventory')
    for r in cert['closed_runs'].values():need(type(r['returncode'])is int and r['returncode']==0 and r['cleanup_complete']is True and r['remaining_owned_children']==[],'recorded_owned_closure')
    need(cert['old_strict_rejection_remains_rejected']is True and cert['photographic_acceptance']is False and cert['whole_app_gate_acceptance']is False,'recorded_certificate_overclaim')
    return True

class Sources:
    def __init__(self):
        self.raw={p:p.read_bytes()for p in EXPECTED}
        for p,digest in EXPECTED.items():need(sha(self.raw[p])==digest,'source_hash_mismatch',str(p))
        self.parent_doc,self.parent_bin=read_glb(self.raw[PARENT]);self.doc,self.binary=read_glb(self.raw[CANDIDATE]);self.original_doc,self.original_bin=read_glb(self.raw[ORIGINAL])
        self.strict_rejection=json.loads(self.raw[STRICT_REJECTION]);need(self.strict_rejection['status']=='REPLACEMENT_PATCH_PROPER_CROSSINGS_REJECTED'and len(self.strict_rejection['patch_body_proper_crossings'])==24 and len(self.strict_rejection['patch_globe_proper_crossings'])==82,'frozen_rejection_changed')
        prior=json.loads(self.raw[PRIOR_TOPOLOGY_CONTROLS]);need(prior['state']=='STATIC_TOPOLOGY_SOURCE_ONLY_PASS'and prior['candidate_sha256']==EXPECTED[CANDIDATE]and prior['recipe_sha256']==EXPECTED[RECIPE]and prior['qualifier_sha256']==EXPECTED[QUALIFIER]and len(prior['corruption_controls'])==11 and all(r['refused']is True for r in prior['corruption_controls'].values()),'prior11_source_bound_topology_controls_changed')
        self.recipe=json.loads(self.raw[RECIPE]);self.ledger=json.loads(self.raw[LEDGER]);self.certificate=json.loads(self.raw[CERTIFICATE]);verify_recorded_certificate(self.certificate)
        need(len(self.raw[CANDIDATE])<=4194304,'source_byte_cap')
        need(self.recipe['maximum_original_source_displacement_m']==.02 and self.recipe['maximum_parent_displacement_m']==.02 and self.recipe['maximum_source_bytes']==4194304 and self.recipe['maximum_triangles']==20000,'frozen_caps_changed')
        self.side_for={int(i):p['side']for p in self.recipe['patches']for i in p['removed_parent_925_faces']};self.patch=set(self.side_for)
        need(len(self.patch)==142,'patch_slot_count')
        need(self.ledger['candidate_sha256']==EXPECTED[PARENT]and self.ledger['tolerance_m']==1e-9,'source_ledger_binding')
        text=self.raw[KERNEL].decode();fn=next(n for n in ast.parse(text).body if isinstance(n,ast.FunctionDef)and n.name=='crosses');namespace={'np':np,'TOL':1e-9}
        exec(compile(ast.Module(body=[fn],type_ignores=[]),str(KERNEL),'exec'),namespace)
        self.crosses=namespace['crosses']
        self.body_positions,self.body_indices,self.body=mesh(self.doc,self.binary,1);self.old_positions,self.old_indices,self.old_body=mesh(self.parent_doc,self.parent_bin,1);self.eye_positions,self.eye_indices,self.eye=mesh(self.doc,self.binary,2)
        _,_,old_eye=mesh(self.parent_doc,self.parent_bin,2);need(np.array_equal(self.eye,old_eye),'globe_geometry_drift')
        self.component_faces={side:np.flatnonzero(self.eye[:,:,0].mean(axis=1)*side>0).tolist()for side in(-1,1)}
        need(all(len(v)==960 for v in self.component_faces.values()),'same_side_globe_partition')

    def cheap_tables(self):
        r=uv_skin_guard(self.doc,self.binary,self.parent_doc,self.parent_bin,self.recipe);original_prefix_guard(self.binary,self.original_bin);return r

    def full_frozen_structure(self):
        """Heavy-slot-only: original serialized inspect, unmodified and hash-bound."""
        import sys
        sys.path.insert(0,str(SOURCE));import generate_anatomy_v2 as anatomy
        q=frozen_module(QUALIFIER,'unchanged_strip_topology_qualification');q.parent_raw=self.raw[PARENT];q.recipe_raw=self.raw[RECIPE]
        original_positions=anatomy.read_attribute(self.original_doc,self.original_bin,203)
        return q.inspect(self.doc,self.binary,self.parent_doc,self.parent_bin,original_positions,self.recipe,anatomy)

    def unchanged(self):
        for p,raw in self.raw.items():need(p.read_bytes()==raw,'source_changed_during_qualification',str(p))
        return True
