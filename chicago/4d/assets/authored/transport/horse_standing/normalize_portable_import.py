"""SOURCE PROPOSAL, not executed. Separate lossless-content import derivative.
Original licensed GLB remains untouched. New export requires root release.
"""
import argparse,copy,hashlib,json,pathlib,struct
import numpy as np
ORIGINAL='41acd9bee7bf05fbcdd813fad965027b01b8801d6a21ca1c22eb2178c8842988'
SOURCE=pathlib.Path('/workspace/shared/horse-public-base-search-20261022/horse-53a6eb7ccf054aa2a378dd7ec08f88fe.glb')
DT={5120:'i1',5121:'u1',5122:'<i2',5123:'<u2',5125:'<u4',5126:'<f4'}
WIDTH={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}
def build(out):
 assert out.resolve().is_relative_to(pathlib.Path('/workspace/shared')) and not out.exists()
 raw=SOURCE.read_bytes();assert hashlib.sha256(raw).hexdigest()==ORIGINAL
 n=struct.unpack_from('<I',raw,12)[0];old=json.loads(raw[20:20+n]);oldbin=raw[28+n:];doc=copy.deepcopy(old);binary=bytearray(oldbin)
 def decoded(i):
  a=old['accessors'][i];v=old['bufferViews'][a['bufferView']];d=np.dtype(DT[a['componentType']]);w=WIDTH[a['type']];assert not a.get('sparse')
  return np.ndarray((a['count'],w),dtype=d,buffer=oldbin,offset=v.get('byteOffset',0)+a.get('byteOffset',0),strides=(v.get('byteStride',w*d.itemsize),d.itemsize)).copy()
 def appended_accessor(original_id,values,target=None):
  a=copy.deepcopy(old['accessors'][original_id]);assert values.shape==(a['count'],WIDTH[a['type']]);assert values.dtype==np.dtype(DT[a['componentType']])
  while len(binary)%4:binary.append(0)
  bv=len(doc['bufferViews']);data=values.tobytes(order='C');doc['bufferViews'].append({'buffer':0,'byteOffset':len(binary),'byteLength':len(data)});binary.extend(data)
  if target is not None:doc['bufferViews'][bv]['target']=target
  a['bufferView']=bv;a.pop('byteOffset',None);doc['accessors'].append(a);return len(doc['accessors'])-1
 # glTF forbids byteStride on animation accessors, even when it equals packed width.
 remapped={};sampler_changes=[]
 for ai,a in enumerate(doc['animations']):
  for si,s in enumerate(a['samplers']):
   for field in ['input','output']:
    original_id=s[field];view=old['bufferViews'][old['accessors'][original_id]['bufferView']]
    if 'byteStride' not in view:continue
    if original_id not in remapped:remapped[original_id]=appended_accessor(original_id,decoded(original_id))
    s[field]=remapped[original_id];sampler_changes.append([ai,si,field,original_id,s[field]])
 # JOINTS_i components with exactly zero WEIGHTS_i contribute exactly zero to LBS.
 joints_changes=[]
 for mi,m in enumerate(doc['meshes']):
  for pi,p in enumerate(m['primitives']):
   at=p['attributes']
   for joint_key in [k for k in at if k.startswith('JOINTS_')]:
    weight_key='WEIGHTS_'+joint_key.split('_')[1];ji=at[joint_key];wi=at[weight_key];j=decoded(ji);w=decoded(wi);assert j.shape==w.shape
    mask=w==0;modified=j.copy();modified[mask]=0;assert np.array_equal(modified[~mask],j[~mask])
    count=int(np.count_nonzero(modified!=j))
    if count:at[joint_key]=appended_accessor(ji,modified,target=34962);joints_changes.append({'mesh':mi,'primitive':pi,'joint_key':joint_key,'old_accessor':ji,'new_accessor':at[joint_key],'zero_weight_components_changed':count})
 # Retain actual one-key Armature rotation overrides exactly, including 1-Float32-ULP rest delta.
 armature_tracks=[]
 for ai,a in enumerate(old['animations']):
  channels=[c for c in a['channels']if c['target']['node']==4];assert len(channels)==1 and channels[0]['target']['path']=='rotation'
  sampler=a['samplers'][channels[0]['sampler']];times=decoded(sampler['input']);qs=decoded(sampler['output']);rest=np.asarray(old['nodes'][4]['rotation'],dtype='<f4')
  assert times.shape==(1,1) and qs.shape==(1,4)
  ulps=(qs[0].view(np.int32).astype(np.int64)-rest.view(np.int32).astype(np.int64)).tolist();assert ulps==[-1,0,0,0]
  armature_tracks.append({'clip_index':ai,'key_count':1,'within_clip_constant':True,'key_quaternion':qs[0].tolist(),'default_quaternion':rest.tolist(),'float32_ulp_delta':ulps})
 # Promote only the three skinned mesh nodes; skeleton/hierarchy/animation targets stay put.
 # IMPORTANT: original Armature4 has six one-key constant rotation tracks, each1Float32ULP
 # from default. It remains an animated target. World-position invariance relies on
 # glTF skinning + Three attached bind(identity), NOT on a falsely constant ancestor.
 parents={c:i for i,node in enumerate(old['nodes'])for c in node.get('children',[])}
 def matrix(node):
  if 'matrix'in node:return np.array(node['matrix'],float).reshape(4,4,order='F')
  x,y,z,w=node.get('rotation',[0,0,0,1]);r=np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],[2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],[2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])
  m=np.eye(4);m[:3,:3]=r@np.diag(node.get('scale',[1,1,1]));m[:3,3]=node.get('translation',[0,0,0]);return m
 def world(i):return (world(parents[i])if i in parents else np.eye(4))@matrix(old['nodes'][i])
 promoted=[]
 for i,node in enumerate(old['nodes']):
  if 'mesh'not in node:continue
  assert i in [21,22,23] and 'skin'in node and not node.get('children')
  assert all(c['target']['node']!=i for a in old['animations']for c in a['channels'])
  parent=parents[i];doc['nodes'][parent]['children'].remove(i)
  candidate=doc['nodes'][i]
  for key in ['translation','rotation','scale','matrix']:candidate.pop(key,None)
  # glTF validator requires skinned root nodes to have identity local transforms.
  # Do not preserve old mesh world matrix here: the skin formula must supply final world pose.
  original_rest_world_matrix=world(i).reshape(16,order='F').tolist()
  assert all(key not in candidate for key in ['matrix','translation','rotation','scale'])
  memberships=[]
  for si,scene in enumerate(doc['scenes']):
   original_roots=set(old['scenes'][si]['nodes']);ancestor=i
   while ancestor in parents:ancestor=parents[ancestor]
   if ancestor in original_roots:scene['nodes'].append(i);memberships.append(si)
  assert memberships
  promoted.append({'node':i,'original_parent':parent,'scene_membership':memberships,'new_local_transform':'identity; matrix/TRS omitted','original_default_mesh_world_matrix':original_rest_world_matrix,'mesh_world_basis_changed':True,'parent4_has_animation_tracks':True,'parent4_each_native_clip_one_constant_key':True,'parent4_key_vs_default_float32_ulp_delta':[-1,0,0,0],'pose_parity':'UNPROVEN pending actual loaded Mixer full-surface position/normal comparison'})
 assert promoted and len(promoted)==3
 assert doc['skins']==old['skins'] and doc['materials']==old['materials'] and doc['images']==old['images']
 for i,node in enumerate(old['nodes']):
  if i not in [4,21,22,23]:assert doc['nodes'][i]==node
 # Every original buffer byte remains as an exact prefix; references change only as declared.
 assert binary[:len(oldbin)]==oldbin
 doc['buffers'][0]['byteLength']=len(binary)
 notice={'original_source_sha256':ORIGINAL,'license':'CC-BY-4.0','credit':'Horse by sevketkabatas, https://sketchfab.com/3d-models/horse-53a6eb7ccf054aa2a378dd7ec08f88fe ; CC BY4.0. Declared portable import adaptation: repacked original animation views; zeroed only zero-weight joint components; promoted three mesh nodes with identity local transforms (matrix/TRS omitted), changing mesh world basis while preserving skeleton world transforms. No geometry/UV/texture/key-value/positive-weight alteration. Native old-clip and idle full-surface parity NOT yet accepted.'}
 doc['asset'].setdefault('extras',{})['portable_import_adaptation']=notice
 encoded=json.dumps(doc,ensure_ascii=False,separators=(',',':')).encode();encoded+=b' '*((-len(encoded))%4)
 while len(binary)%4:binary.append(0)
 result=struct.pack('<III',0x46546c67,2,28+len(encoded)+len(binary))+struct.pack('<II',len(encoded),0x4e4f534a)+encoded+struct.pack('<II',len(binary),0x004e4942)+binary
 out.mkdir();f=out/'horse-sevket-portable-import-v3.glb';f.write_bytes(result)
 receipt={'status':'ACTUAL IMPORT DERIVATIVE ONLY; validator/Mixer/position-normal parity pending','source_sha256':ORIGINAL,'derived_sha256':hashlib.sha256(result).hexdigest(),'derived_bytes':len(result),'original_bin_prefix_exact':True,'animation_reference_changes':sampler_changes,'original_armature4_tracks_preserved':armature_tracks,'zero_weight_joint_changes':joints_changes,'promoted_mesh_nodes':promoted,'source_unchanged_after':hashlib.sha256(SOURCE.read_bytes()).hexdigest()==ORIGINAL,'adaptation':notice}
 (out/'NORMALIZATION-RECEIPT.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--lane-released',required=True,action='store_true');p.add_argument('--output-dir',required=True,type=pathlib.Path);a=p.parse_args();build(a.output_dir)
