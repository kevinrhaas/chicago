"""Independent allowed-change boundary check with destructive in-memory controls only."""
from pathlib import Path
import copy,hashlib,json,math,struct
D=Path(__file__).resolve().parent.parent;BASE=D/'assets/authored/transport/horse_standing/horse-sevket-v16-planted-standing-v1.glb';CAND=D/'renderers/web/transport/standing-horse/horse-sevket-v16-planted-standing-eye-uv-v1.glb'

def decode(b):
 assert b[:4]==b'glTF' and struct.unpack_from('<II',b,4)==(2,len(b))
 n,t=struct.unpack_from('<II',b,12);assert t==0x4e4f534a
 j=json.loads(b[20:20+n]);length,t=struct.unpack_from('<II',b,20+n);assert t==0x004e4942 and len(b)==28+n+length
 return j,b[28+n:]
baseraw=BASE.read_bytes();candraw=CAND.read_bytes();assert hashlib.sha256(baseraw).hexdigest()=='b479442cb03ac46eb13c19da15a79cdfaf28dbdf356b116f78de7ce7ecdc60be';assert hashlib.sha256(candraw).hexdigest()=='d4544c2845256858dfa614235bcb37cb964ab63095a53a2436225182cefbb914';bj,bb=decode(baseraw);cj,cb=decode(candraw)
START=332984;LENGTH=31744

def check(j,b):
 assert len(b)==len(bb),'BIN length'
 assert b[:START]==bb[:START] and b[START+LENGTH:]==bb[START+LENGTH:],'Protected binary bytes'
 compare=copy.deepcopy(j);notice=compare['asset']['extras'].pop('chicago4d_ocular_uv_derivative');assert notice['baseline_sha256']==hashlib.sha256(baseraw).hexdigest() and notice['texture_pixels_unchanged'] is True
 compare['accessors'][10]=copy.deepcopy(bj['accessors'][10]);assert compare==bj,'Protected semantic JSON'
 a=j['accessors'][10];v=j['bufferViews'][a['bufferView']];assert v.get('byteOffset',0)+a.get('byteOffset',0)==START and a['count']*8==LENGTH
 uvs=[struct.unpack_from('<ff',b,START+i*8)for i in range(a['count'])];assert all(math.isfinite(x)and 0<=x<=1 for uv in uvs for x in uv),'Finite bounded UVs'
 assert a['min']==[min(u[k]for u in uvs)for k in range(2)] and a['max']==[max(u[k]for u in uvs)for k in range(2)],'Actual bounds'
 return True
assert check(cj,cb)
controls=[]
def reject(name,j,b):
 try:check(j,b)
 except AssertionError as e:controls.append({'case':name,'rejected':True,'reason':str(e)});return
 raise AssertionError('Negative control accepted:'+name)
m=bytearray(cb);m[0]^=1;reject('protected_position_byte',cj,m)
j=copy.deepcopy(cj);j['materials'][2]['pbrMetallicRoughness']['roughnessFactor']=.25;reject('material_change',j,cb)
j=copy.deepcopy(cj);j['animations'][0]['name']='fake_clip';reject('animation_change',j,cb)
j=copy.deepcopy(cj);j['accessors'][10]['min'][0]-=.01;reject('false_uv_bounds',j,cb)
m=bytearray(cb);struct.pack_into('<f',m,START,float('nan'));reject('nonfinite_uv',cj,m)
assert hashlib.sha256(BASE.read_bytes()).hexdigest()==hashlib.sha256(baseraw).hexdigest()
report={'status':'PASS_INDEPENDENT_UV_ONLY_CHANGE_BOUNDARY','baseline_sha256':hashlib.sha256(baseraw).hexdigest(),'candidate_sha256':hashlib.sha256(candraw).hexdigest(),'candidate_bytes':len(candraw),'UV10_changed_values':sum(struct.unpack_from('<f',bb,START+i)[0]!=struct.unpack_from('<f',cb,START+i)[0]for i in range(0,LENGTH,4)),'non_UV_BIN_exact':True,'JSON_except_UVbounds_and_explicit_derivative_notice_exact':True,'six_image_payloads_materials_26rig_weights_inversebind_nodes_animation_indices_body_hair_UVs_exact':True,'negative_controls':controls,'source_baseline_unchanged_after':True,'scope':'Source-data equivalence only; not a new actual loader/Mixer/world/photographic pass. Original b479 loaded65keys64midpoints proof remains historically labelled.'}
print(json.dumps(report,indent=2))
