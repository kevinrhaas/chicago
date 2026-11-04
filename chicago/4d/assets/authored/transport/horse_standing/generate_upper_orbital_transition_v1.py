"""Repeat the bounded BODY orbital transition from exact qualified5a.

The original5a source/recipe/modes remain immutable ancestors. This recipe openly
expands six formerly fixed boundary rows, with no collision-policy exemption.
The creation-time unqualified GLB flags remain historical; later proof is separate.
"""
import argparse,copy,hashlib,json,struct
from pathlib import Path
import numpy as np
PARENT_SHA='5a2b2e87c3931e3ab82be3ce3bc69724a0a088aac30920cea9ad348bbaf8fad5'
RECIPE_SHA='23850a915289ac7d73ea6619a7b68d07c9c240e177917f10f4488f996f66db70'
CANDIDATE_SHA='e49b6f1c9f7b70f1fcdf19fa7f6dddf54048b32256b4d8030d6238d6dfe79d49'
PREFIX_BYTES=3727644
POSITIONS={402,403,411,412,967,969,972,976,1360,1363}
NORMALS={392,393,399,400,401,402,403,404,409,410,411,412,413,414,415,416,965,966,967,968,969,970,971,972,973,975,976,977,979,980,981,984,1360,1361,1362,1363,1364,1365}
sha=lambda raw:hashlib.sha256(raw).hexdigest()
class Rejected(ValueError):pass
def need(ok,code):
    if not ok:raise Rejected(code)
def decode(raw):
    need(len(raw)>=28 and struct.unpack_from('<4sII',raw)==(b'glTF',2,len(raw)),'GLB_header')
    n,kind=struct.unpack_from('<II',raw,12);need(kind==0x4e4f534a,'GLB_JSON');m,kind=struct.unpack_from('<II',raw,20+n);need(kind==0x004e4942 and len(raw)==28+n+m,'GLB_BIN')
    return json.loads(raw[20:20+n]),raw[28+n:]
def encode(doc,binary):
    j=json.dumps(doc,separators=(',',':'),ensure_ascii=False).encode();j+=b' '*((-len(j))%4);binary+=b'\0'*((-len(binary))%4)
    return struct.pack('<4sII',b'glTF',2,28+len(j)+len(binary))+struct.pack('<II',len(j),0x4e4f534a)+j+struct.pack('<II',len(binary),0x004e4942)+binary
def width(a):return {'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}[a['type']]
def attribute(doc,binary,index):
    a=doc['accessors'][index];v=doc['bufferViews'][a['bufferView']];dt=np.dtype({5126:'<f4',5125:'<u4',5123:'<u2',5121:'u1'}[a['componentType']]);w=width(a)
    return np.ndarray((a['count'],w),dtype=dt,buffer=binary,offset=v.get('byteOffset',0)+a.get('byteOffset',0),strides=(v.get('byteStride',w*dt.itemsize),dt.itemsize)).copy()
def offset(doc,index,row):
    a=doc['accessors'][index];v=doc['bufferViews'][a['bufferView']];size=width(a)*{5126:4,5125:4,5123:2,5121:1}[a['componentType']]
    return v.get('byteOffset',0)+a.get('byteOffset',0)+row*v.get('byteStride',size)
def derive(parent_raw,recipe_raw):
    need(sha(parent_raw)==PARENT_SHA,'exact_parent5a');need(sha(recipe_raw)==RECIPE_SHA,'exact_regional_recipe')
    recipe=json.loads(recipe_raw);need(set(recipe['position_rows'])==POSITIONS and set(recipe['normal_rows'])==NORMALS and len(recipe['affected_faces'])==44,'explicit_region')
    need(recipe['limits']=={'original_d454_max_m':.02,'immutable925_max_m':.02,'qualified5a_parent_max_m':.02,'bytes':4194304,'triangles':20000},'original_limits')
    d,b=decode(parent_raw);p=d['meshes'][1]['primitives'][0];a=p['attributes'];pos=attribute(d,b,a['POSITION']);norm=attribute(d,b,a['NORMAL']);idx=attribute(d,b,p['indices']).reshape(-1,3).astype(int)
    need(len(pos)==5595 and len(idx)==9794 and np.flatnonzero(np.isin(idx,list(POSITIONS)).any(1)).tolist()==recipe['affected_faces'],'actual_region_faces')
    new=pos.copy()
    for row in recipe['position_rows']:
        upper,lower=recipe['fixed_anchor_pairs'][str(row)];t=(float(pos[row,1])-float(pos[lower,1]))/(float(pos[upper,1])-float(pos[lower,1]));need(0<t<1,'fixed_anchor_order')
        target=(1-t)*float(pos[lower,0])+t*float(pos[upper,0]);new[row,0]=np.float32(float(pos[row,0])+.5*(target-float(pos[row,0])))
        need(abs(float(new[row,0]))<abs(float(pos[row,0])),'lateral_ridge_reduction')
    tri=new.astype(float)[idx];areas=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);nn=norm.copy()
    for row in recipe['normal_rows']:
        fan=np.flatnonzero(np.any(idx==row,axis=1));v=areas[fan].sum(0);need(np.linalg.norm(v)>1e-14,'normal_fan');nn[row]=v/np.linalg.norm(v)
    binary=bytearray(b)
    for index,rows,values in [(a['POSITION'],recipe['position_rows'],new),(a['NORMAL'],recipe['normal_rows'],nn)]:
        for row in rows:at=offset(d,index,row);binary[at:at+12]=values[row].astype('<f4').tobytes()
        need(np.array_equal(values.min(0),np.asarray(d['accessors'][index]['min'],dtype='<f4'))and np.array_equal(values.max(0),np.asarray(d['accessors'][index]['max'],dtype='<f4')),'source_accessor_extrema')
    d['asset'].setdefault('extras',{})['upper_orbital_transition_v1']={'state':'EXTERNAL_UNQUALIFIED_NOT_ADOPTED','parent_sha256':PARENT_SHA,'recipe_sha256':RECIPE_SHA,'position_rows':10,'affected_faces':44,'physical129':'UNRUN','posed_interface129':'UNRUN','visual':'UNRUN'}
    raw=encode(d,bytes(binary));need(sha(raw)==CANDIDATE_SHA,'repeatable_exact_e49b');return raw

def inspect(parent_raw,child_raw,recipe_raw,original_raw,reference925_raw):
    expected=derive(parent_raw,recipe_raw);pd,pb=decode(parent_raw);d,b=decode(child_raw);ed,_=decode(expected);clean=copy.deepcopy(d);tag=clean['asset']['extras'].pop('upper_orbital_transition_v1',None)
    need(tag==ed['asset']['extras']['upper_orbital_transition_v1'],'child_recipe_metadata');need(clean==pd,'unrelated_JSON_document')
    need(len(child_raw)<=4194304,'4MiB_cap');p=d['meshes'][1]['primitives'][0];a=p['attributes'];oldp=attribute(pd,pb,a['POSITION']);oldn=attribute(pd,pb,a['NORMAL']);pos=attribute(d,b,a['POSITION']);normal=attribute(d,b,a['NORMAL']);idx=attribute(d,b,p['indices']).reshape(-1,3).astype(int)
    for mi in [0,2]:
        q=d['meshes'][mi]['primitives'][0]
        for k,i in q['attributes'].items():need(np.array_equal(attribute(d,b,i),attribute(pd,pb,i)),f'protected_mesh{mi}_{k}')
        need(np.array_equal(attribute(d,b,q['indices']),attribute(pd,pb,q['indices'])),f'protected_mesh{mi}_indices')
    for k,i in a.items():
        if k not in ['POSITION','NORMAL']:need(np.array_equal(attribute(d,b,i),attribute(pd,pb,i)),f'protected_BODY_{k}')
    need(np.array_equal(idx,attribute(pd,pb,p['indices']).reshape(-1,3)),'protected_BODY_indices')
    need(np.isfinite(pos).all()and np.isfinite(normal).all(),'nonfinite_source')
    changedp=set(np.flatnonzero(np.any(pos!=oldp,1)).tolist());changedn=set(np.flatnonzero(np.any(normal!=oldn,1)).tolist());need(changedp<=POSITIONS,'outside_POSITION_region');need(changedn<=NORMALS,'outside_NORMAL_region');need(np.array_equal(pos[:,1:],oldp[:,1:]),'protected_POSITION_YZ')
    od,ob=decode(original_raw);rd,rb=decode(reference925_raw);op=attribute(od,ob,od['meshes'][1]['primitives'][0]['attributes']['POSITION']);rp=attribute(rd,rb,rd['meshes'][1]['primitives'][0]['attributes']['POSITION'])
    delta=np.linalg.norm(pos.astype(float)-oldp.astype(float),axis=1);d925=np.linalg.norm(pos.astype(float)-rp.astype(float),axis=1);d0=np.linalg.norm(pos[:len(op)].astype(float)-op.astype(float),axis=1)
    need(max(float(delta.max()),float(d925.max()),float(d0.max()))<=.02,'original_20mm_caps');need(b[:PREFIX_BYTES]==ob,'immutable_d454_prefix')
    allowed=np.zeros(len(b),dtype=bool)
    for i,rows in [(a['POSITION'],POSITIONS),(a['NORMAL'],NORMALS)]:
        for row in rows:at=offset(d,i,row);allowed[at:at+12]=True
    need(len(b)==len(pb),'BIN_length');need(not np.any((np.frombuffer(b,np.uint8)!=np.frombuffer(pb,np.uint8))&~allowed),'outside_BIN_region')
    need(child_raw==expected,'repeatable_source_bytes')
    tri=pos.astype(float)[idx];oldtri=oldp.astype(float)[idx];cross=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);oldcross=np.cross(oldtri[:,1]-oldtri[:,0],oldtri[:,2]-oldtri[:,0]);need(np.all(np.linalg.norm(cross,axis=1)>1e-14),'degenerate_BODY_face')
    faces=json.loads(recipe_raw)['affected_faces'];cos=(cross[faces]*oldcross[faces]).sum(1)/(np.linalg.norm(cross[faces],axis=1)*np.linalg.norm(oldcross[faces],axis=1));need(np.all(cos>0),'new_face_orientation_flip')
    triangles=sum(len(attribute(d,b,q['indices']))//3 for m in d['meshes']for q in m['primitives']);need(triangles==17390 and triangles<=20000,'20k_triangle_cap')
    return {'status':'EXPLICIT10_POSITION38_NORMAL_SOURCE_STRUCTURE_ONLY_PASS','positions':sorted(changedp),'normals':sorted(changedn),'faces':faces,'triangles':triangles,'bytes':len(child_raw),'max5a_m':float(delta.max()),'max925_m':float(d925.max()),'max_d454_original_rows_m':float(d0.max()),'minimum_face_normal_cosine':float(cos.min()),'new_physical129_required_for_new_bytes':True}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--parent',type=Path,required=True);p.add_argument('--recipe',type=Path,required=True);p.add_argument('--out',type=Path,required=True);args=p.parse_args();raw=derive(args.parent.read_bytes(),args.recipe.read_bytes());need(not args.out.exists(),'fresh_output_required');args.out.write_bytes(raw);print(sha(raw))
