"""Original anonymous1904 Brougham driver derivative; no saved checkout writes.

Retains the cleared portable-human graphical streams and binds a freshly solved
vehicle-local seated pose. No named resident is cast as a1904 driver.
"""
from pathlib import Path
import argparse, copy, hashlib, json, math, struct
import numpy as np
from scipy.spatial.transform import Rotation

APP = Path(__file__).resolve().parents[1]
HERE = Path('/tmp/chicago4d-working-driver-1904')
OUTPUT = APP
ASSET = 'anonymous_working_driver_1904'
DONOR_ROOT = APP / 'assets/authored/humans/working_driver_1904/ingredients'
PERSON_ID = 'pa1904_otis_f_r_c1900_hans_johnson'
SEAT = np.array([0., 1.77585, .76])
DTYPES = {5120: 'i1', 5121: 'u1', 5122: '<i2', 5123: '<u2', 5125: '<u4', 5126: '<f4'}
WIDTH = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}

def sha(b): return hashlib.sha256(b).hexdigest()
def load(p):
    b = Path(p).read_bytes(); assert struct.unpack_from('<III', b) == (0x46546c67, 2, len(b))
    n, tag = struct.unpack_from('<II', b, 12); assert tag == 0x4e4f534a
    doc = json.loads(b[20:20+n]); size, tag = struct.unpack_from('<II', b, 20+n); assert tag == 0x004e4942
    return doc, bytearray(b[28+n:28+n+size]), sha(b)
def accessor(doc, buf, i):
    a = doc['accessors'][i]; v = doc['bufferViews'][a['bufferView']]
    assert 'byteStride' not in v and 'sparse' not in a
    out = np.frombuffer(buf, dtype=DTYPES[a['componentType']], count=a['count'] * WIDTH[a['type']], offset=v.get('byteOffset', 0) + a.get('byteOffset', 0)).reshape(a['count'], WIDTH[a['type']]).copy()
    if a.get('normalized'):
        assert a['componentType'] in [5121, 5123]; out = out.astype(float) / np.iinfo(np.dtype(DTYPES[a['componentType']])).max
    return out
def pose(doc, buf):
    local = {i: {k: np.array(n.get(k, default), float) for k, default in [('translation', [0,0,0]), ('rotation', [0,0,0,1]), ('scale', [1,1,1])]} for i,n in enumerate(doc['nodes'])}
    clip = next(a for a in doc['animations'] if a['name'] == 'sit_drive')
    for c in clip['channels']:
        s = clip['samplers'][c['sampler']]; assert s.get('interpolation') == 'STEP'
        out = accessor(doc, buf, s['output']); assert np.max(np.abs(out - out[0])) == 0
        local[c['target']['node']][c['target']['path']] = out[0].astype(float)
    return local
def matrices(doc, local):
    parent = {c: i for i,n in enumerate(doc['nodes']) for c in n.get('children', [])}; cache = {}
    def one(i):
        if i in cache: return cache[i]
        p = local[i]; m = np.eye(4); m[:3,:3] = Rotation.from_quat(p['rotation']).as_matrix() @ np.diag(p['scale']); m[:3,3] = p['translation']
        cache[i] = one(parent[i]) @ m if i in parent else m
        return cache[i]
    return {i: one(i) for i in local}, parent
def rotate_between(a, b):
    a = a / np.linalg.norm(a); b = b / np.linalg.norm(b)
    axis = np.cross(a,b); sin = np.linalg.norm(axis); cos = np.clip(a @ b, -1, 1)
    if sin < 1e-12:
        assert cos > 0; return np.eye(3)
    return Rotation.from_rotvec(axis / sin * math.atan2(sin, cos)).as_matrix()
def surface(doc, buf, local):
    glob, _ = matrices(doc, local); skin = doc['skins'][0]
    ibm = accessor(doc, buf, skin['inverseBindMatrices']).reshape(-1,4,4).transpose(0,2,1)
    joint_m = np.stack([glob[i] for i in skin['joints']]) @ ibm
    rows = []
    for i,node in enumerate(doc['nodes']):
        if 'mesh' not in node: continue
        for primitive in doc['meshes'][node['mesh']]['primitives']:
            a = primitive['attributes']; v = accessor(doc, buf, a['POSITION'])
            if 'skin' in node:
                j = accessor(doc, buf, a['JOINTS_0']).astype(int); w = accessor(doc, buf, a['WEIGHTS_0'])
                pv = np.c_[v, np.ones(len(v))]
                v = np.sum(np.einsum('vnij,vj->vni', joint_m[j], pv) * w[:,:,None], axis=1)[:,:3]
            else: v = (np.c_[v,np.ones(len(v))] @ glob[i].T)[:,:3]
            ix = accessor(doc, buf, primitive['indices']).astype(int).ravel() if 'indices' in primitive else np.arange(len(v))
            rows.append(dict(name=node['name'], positions=v, indices=ix, primitive=primitive))
    return rows
def solve(doc, buf, seat_y_shift=.04, seat_z_shift=.20):
    local = pose(doc, buf); original = copy.deepcopy(local); names = {n['name']: i for i,n in enumerate(doc['nodes'])}
    original_g, parent = matrices(doc, local)
    support_y = 1.765850067138672
    root = names['root']; local[root]['translation'] += np.array([0, support_y - 1.58 + seat_y_shift, seat_z_shift])
    # Neutralize ten degrees of the ingredient's posterior pelvis tilt while
    # keeping its existing upright torso orientation. The pelvis/thigh/feet are
    # solved together; this is not a translated standing body or a lip-only fit.
    pelvis_tilt_degrees = 10.; toe_brace_degrees = 25.
    glob, _ = matrices(doc, local); pelvis = names['pelvis']
    pelvis_world = Rotation.from_rotvec([math.radians(pelvis_tilt_degrees),0,0]).as_matrix() @ glob[pelvis][:3,:3]
    local[pelvis]['rotation'] = Rotation.from_matrix(glob[parent[pelvis]][:3,:3].T @ pelvis_world).as_quat()
    glob, _ = matrices(doc, local); spine = names['spine_01']
    local[spine]['rotation'] = Rotation.from_matrix(glob[parent[spine]][:3,:3].T @ original_g[spine][:3,:3]).as_quat()
    before = surface(doc, buf, original)
    shoes = next(x['positions'] for x in before if 'closed_shoes' in x['name'])
    foot_y = 1.0893750190734863
    pitch = Rotation.from_rotvec([math.radians(toe_brace_degrees),0,0]).as_matrix()
    reports = []
    for side, sign in [('l',1), ('r',-1)]:
        hip, knee, ankle = (names[k+'_'+side] for k in ['thigh','calf','foot'])
        original_foot = shoes[shoes[:,0] * sign > 0]
        relative_shoe = (original_foot-original_g[ankle][:3,3]) @ pitch.T
        # High coach seat: actual toes bear on the unchanged footplate, with
        # heels honestly raised. Fit the COMPLETE shoe XZ extent to the board.
        target = np.array([original_g[ankle][0,3], foot_y-relative_shoe[:,1].min(),
                           1.26-(relative_shoe[:,2].min()+relative_shoe[:,2].max())/2])
        assert relative_shoe[:,2].max()-relative_shoe[:,2].min() < .36
        glob, _ = matrices(doc, local); h = glob[hip][:3,3]; k = glob[knee][:3,3]; a = glob[ankle][:3,3]
        l1, l2 = np.linalg.norm(k-h), np.linalg.norm(a-k)
        delta = target-h; distance = np.linalg.norm(delta); assert abs(l1-l2) < distance < l1+l2
        axis = delta / distance
        pole = np.array([0.,0.,1.]); pole -= axis*(pole@axis); pole /= np.linalg.norm(pole)
        along = (l1*l1-l2*l2+distance*distance)/(2*distance)
        wanted_knee = h+axis*along+pole*math.sqrt(max(0,l1*l1-along*along))
        hip_rot = rotate_between(k-h,wanted_knee-h) @ glob[hip][:3,:3]
        local[hip]['rotation'] = Rotation.from_matrix(glob[parent[hip]][:3,:3].T @ hip_rot).as_quat()
        glob, _ = matrices(doc, local); k = glob[knee][:3,3]; a = glob[ankle][:3,3]
        knee_rot = rotate_between(a-k,target-k) @ glob[knee][:3,:3]
        local[knee]['rotation'] = Rotation.from_matrix(glob[parent[knee]][:3,:3].T @ knee_rot).as_quat()
        glob, _ = matrices(doc, local)
        local[ankle]['rotation'] = Rotation.from_matrix(glob[parent[ankle]][:3,:3].T @ pitch @ original_g[ankle][:3,:3]).as_quat()
        glob, _ = matrices(doc, local); err = np.linalg.norm(glob[ankle][:3,3]-target); assert err < 1e-10
        reports.append(dict(side=side,original_upper_leg_m=l1,original_lower_leg_m=l2,target_ankle_m=target.tolist(),actual_ankle_error_m=float(err),knee_angle_degrees=float(math.degrees(math.acos(np.clip(((h-wanted_knee)@(target-wanted_knee))/(l1*l2),-1,1))))))
    glob, _ = matrices(doc, local)
    return local, dict(actual_cushion_top_m=support_y,seat_reference_node_m=SEAT.tolist(),actual_footboard_top_m=foot_y,seat_y_shift_m=seat_y_shift,seat_z_shift_m=seat_z_shift,pelvis_tilt_delta_degrees=pelvis_tilt_degrees,toe_brace_plantarflexion_degrees=toe_brace_degrees,foot_support='actual toe/forefoot contact; raised heels, not flat soles',pelvis_center_vehicle_local_m=glob[names['pelvis']][:3,3].tolist(),torso_world_orientation_retained=True,legs=reports,rein_binding_validated=False,full_material_visual_review='UNRUN')

def add_accessor(doc, buf, values, typ):
    while len(buf)%4: buf.append(0)
    a = np.asarray(values,dtype='<f4').reshape(-1, WIDTH[typ]); start = len(buf); buf.extend(a.tobytes())
    vi = len(doc['bufferViews']); doc['bufferViews'].append(dict(buffer=0,byteOffset=start,byteLength=a.nbytes))
    ai = len(doc['accessors']); row = dict(bufferView=vi,componentType=5126,count=len(a),type=typ)
    if typ == 'SCALAR': row.update(min=[float(a.min())],max=[float(a.max())])
    doc['accessors'].append(row); return ai
def write(p, doc, buf):
    doc['buffers'][0]['byteLength'] = len(buf)
    j = json.dumps(doc,separators=(',',':')).encode(); j += b' ' * (-len(j)%4); buf += b'\0' * (-len(buf)%4)
    data = struct.pack('<III',0x46546c67,2,28+len(j)+len(buf)) + struct.pack('<II',len(j),0x4e4f534a) + j + struct.pack('<II',len(buf),0x004e4942) + buf
    p.parent.mkdir(parents=True,exist_ok=True); p.write_bytes(data); return dict(path=str(p),bytes=len(data),sha256=sha(data))
def graphical_descriptors(doc):
    out=copy.deepcopy({k:doc[k] for k in ['meshes','materials','textures','images','skins']})
    for mesh in out['meshes']: mesh.pop('name',None)
    return out
def export(lod):
    source = DONOR_ROOT/f'dufresne_joseph_1835.lod{lod}.glb'; doc, buf, source_sha = load(source)
    solved, report = solve(doc, buf, seat_y_shift=(.052 if lod == 2 else .04))
    by_name = {n['name']: solved[i] for i,n in enumerate(doc['nodes']) if i in doc['skins'][0]['joints']}
    rows = []
    for web in [False,True]:
        src = DONOR_ROOT/('web' if web else '')/f'dufresne_joseph_1835.lod{lod}.glb'
        d,b,original_sha = load(src)
        original_graphics = sha(json.dumps(graphical_descriptors(d),sort_keys=True).encode())
        times = add_accessor(d,b,[[0],[1]],'SCALAR'); samplers=[];channels=[]
        for i,node in enumerate(d['nodes']):
            if node['name'] in by_name:
                p = by_name[node['name']]
                for path,typ in [('translation','VEC3'),('rotation','VEC4')]:
                    ai = add_accessor(d,b,[p[path],p[path]],typ); si=len(samplers)
                    samplers.append(dict(input=times,output=ai,interpolation='STEP')); channels.append(dict(sampler=si,target=dict(node=i,path=path)))
            if 'dufresne_joseph_1835' in node.get('name',''): node['name']=node['name'].replace('dufresne_joseph_1835',ASSET)
        seated=dict(name='sit_drive',channels=channels,samplers=samplers)
        d['animations']=[seated if clip['name']=='sit_drive' else clip for clip in d['animations']]
        for mesh in d['meshes']:
            if 'dufresne_joseph_1835' in mesh.get('name',''): mesh['name']=mesh['name'].replace('dufresne_joseph_1835',ASSET)
        metadata = dict(contract_version=1,rigid_bone_frame_export=True,kind='body',asset_id=ASSET,lod=lod,skeleton='c4d_humanoid_v1',grade='reconstructed',identity_kind='generic_depiction_ingredient',person_reference_id=PERSON_ID,person_reference_grade='inferred',person_reference_scene='1904',license='CC0-1.0',master='assets/authored/humans/working_driver_1904/POSE-MASTER.json',authored_by='Chicago4D original1904 driver derivative (T-2804)',recipe='data/humans/recipes/working_driver_1904.json',liberty='L418',basis='Reconstructed appearance ingredient for existing inferred1904 coachman Hans Johnson, not an archival likeness. Reuses cleared generic CC0 adult35 anatomy/skin/hair and original plain shirt, waistcoat, trousers and closed shoes. The census documents Hans as a coachman in1900; his continued1904 presence follows the existing project inference. Height, complexion, clothing, seated action, vehicle and journey remain reconstructed. No household carriage ownership or documented trip is asserted; original1835 garment analogies do not attest a1904 outfit.',sources=['census_1900_chicago_t623_roll245'],source_scope='Resident identity/occupation reference only; no face, outfit, vehicle ownership or1904 journey derived from census.',review_required=False,touches_removal=False)
        # Original identity metadata is kept only in the provenance document;
        # a scene/mesh/node must never misidentify the anonymous1904actor.
        for scene in d['scenes']:
            scene['name']=ASSET
            scene['extras']=dict(chicago4d_human=metadata,driver_study_json=json.dumps(dict(scene='1904',identity_kind='person',person_reference_id=PERSON_ID,person_reference_grade='inferred',appearance_grade='reconstructed',variant='studebaker_1893_brougham_reconstruction_01',vehicle_sidecar_sha256=sha((APP/'renderers/web/transport/parked-brougham/brougham.json').read_bytes()),vehicle_glb_sha256=sha((APP/'renderers/web/transport/parked-brougham/brougham-near.glb').read_bytes()),clip='sit_drive',fit_scope='fresh source-model rigid IK and real sole/footboard triangles; browser/occupied world proof pending',**report),sort_keys=True))
        d['asset']['generator']='Chicago4D original anonymous1904 driver derivative v1; source geometry export retained in provenance'
        assert original_graphics == sha(json.dumps(graphical_descriptors(d),sort_keys=True).encode())
        assert 'dufresne_joseph' not in json.dumps(d) and 'glessner_john' not in json.dumps(d)
        out=OUTPUT/'assets/humans'/('web' if web else '')/f'{ASSET}.lod{lod}.glb'
        row=write(out,d,b); row.update(source_file=str(src),source_sha256=original_sha,graphics_descriptors_exact=True,web=web,lod=lod); rows.append(row)
    (HERE/f'LOD{lod}-EXPORT.json').write_text(json.dumps(dict(lod=lod,source_sha256=source_sha,pose=report,outputs=rows),indent=2)+'\n')
    if lod==0:
        master=OUTPUT/'assets/authored/humans/working_driver_1904/POSE-MASTER.json';master.parent.mkdir(parents=True,exist_ok=True)
        master.write_text(json.dumps(dict(format='chicago4d_anonymous_driver_pose_master_v1',grade='reconstructed',license='CC0-1.0',asset_id=ASSET,scene='1904',vehicle='studebaker_1893_brougham_reconstruction_01',pose_parameters=report,local_bone_transforms={n:{k:v.tolist()for k,v in p.items()}for n,p in by_name.items()},graphical_ingredients_recipe='data/humans/recipes/working_driver_1904.json'),indent=2)+'\n')
    print(json.dumps(dict(lod=lod,outputs=rows,pose=report)))

if __name__ == '__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--lod',required=True,type=int,choices=range(4));ap.add_argument('--root',type=Path,default=APP);ap.add_argument('--donor-root',type=Path,default=DONOR_ROOT);ap.add_argument('--output-root',type=Path,default=OUTPUT);ap.add_argument('--receipts-root',type=Path,default=HERE);args=ap.parse_args()
    APP=args.root.resolve();DONOR_ROOT=args.donor_root.resolve();OUTPUT=args.output_root.resolve();HERE=args.receipts_root.resolve();HERE.mkdir(parents=True,exist_ok=True);export(args.lod)
