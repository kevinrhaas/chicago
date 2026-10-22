"""Append ONLY pinned quaternion streams to the separately qualified normalized derivative.
Source proposal; execute only after coordinator release. No geometry generation/re-rig.
"""
import argparse,copy,hashlib,json,pathlib,struct,math,re
UPSTREAM='41acd9bee7bf05fbcdd813fad965027b01b8801d6a21ca1c22eb2178c8842988'
SOURCE='ceefa279b1602b97eac707cec19b2fbbb25c4442788981d82b20ac99ca205afc'
BUNDLE='a759bf114a84a94f067fc50003473527677082dd6a4c6337bdff39babc7e73ba'
NORMALIZATION_RECEIPT='7b7c75927a760e08b8d1ebce56ac6fb3081460b96e3c22811afb6bffd1714329'
HERE=pathlib.Path(__file__).resolve().parent

def require_parity(path,expected_sha):
 assert re.fullmatch('[a-f0-9]{64}',expected_sha),'Actual parity receipt SHA required'
 assert path.resolve()==pathlib.Path('/workspace/shared/T2803-PORTABLE-NORMALIZER-V3-MIXER-PARITY-ACTUAL-20261022/ACTUAL-LOADED-PARITY.json')
 raw=path.read_bytes();assert hashlib.sha256(raw).hexdigest()==expected_sha
 r=json.loads(raw);assert r['status']=='ACTUAL_LOADED_FULL_SURFACE_PARITY_PASS'
 assert r['source_sha256']==UPSTREAM and r['normalized_sha256']==SOURCE
 assert r['decoded_key_equivalence'] is True and r['maps_decoded_equivalent'] is True and r['poses_complete'] is True
 assert r['pose_count']==199 and len(r['poses'])==199
 for key,limit,field in [('positions',1e-5,'maximum_delta_m'),('normals',.01,'maximum_angle_degrees')]:
  q=r[key];assert q['complete'] is True and isinstance(q['evaluations'],int) and q['evaluations']>0
  tolerance='tolerance_m' if key=='positions' else 'tolerance_degrees'
  assert q[tolerance]==limit and math.isfinite(q[field]) and 0<=q[field]<=limit
 return r

def build(source_file,bundle_file,out,parity_file,parity_sha256):
 parity=require_parity(parity_file,parity_sha256)
 normalization_path=source_file.parent/'NORMALIZATION-RECEIPT.json';assert hashlib.sha256(normalization_path.read_bytes()).hexdigest()==NORMALIZATION_RECEIPT
 normalization=json.loads(normalization_path.read_text());assert normalization['source_sha256']==UPSTREAM and normalization['derived_sha256']==SOURCE
 out=out.resolve();assert out.is_relative_to(pathlib.Path('/workspace/shared')),'Outside-app fresh output required'
 assert not out.exists(),'Refuse existing output; no automatic retry'
 raw=source_file.read_bytes();assert hashlib.sha256(raw).hexdigest()==SOURCE and len(raw)==3356764
 magic,version,total=struct.unpack_from('<III',raw);assert(magic,version,total)==(0x46546c67,2,len(raw))
 n,kind=struct.unpack_from('<II',raw,12);assert kind==0x4e4f534a
 original=json.loads(raw[20:20+n]);bn,btype=struct.unpack_from('<II',raw,20+n);assert btype==0x004e4942 and 28+n+bn==len(raw)
 oldbin=raw[28+n:];assert len(original['buffers'])==1 and'uri'not in original['buffers'][0]
 doc=copy.deepcopy(original);binary=bytearray(oldbin);assert hashlib.sha256(bundle_file.read_bytes()).hexdigest()==BUNDLE
 bundle=json.loads(bundle_file.read_text());assert bundle['source_sha256']==UPSTREAM
 animation={'name':bundle['animation']['name'],'extras':bundle['animation']['extras'],'channels':[],'samplers':[]}
 def append(values,width,kind,minimum=None,maximum=None):
  while len(binary)%4:binary.append(0)
  offset=len(binary);data=struct.pack('<'+'f'*len(values),*values);binary.extend(data)
  bv=len(doc['bufferViews']);doc['bufferViews'].append({'buffer':0,'byteOffset':offset,'byteLength':len(data)})
  aid=len(doc['accessors']);acc={'bufferView':bv,'componentType':5126,'count':len(values)//width,'type':kind}
  if minimum is not None:acc['min']=minimum;acc['max']=maximum
  doc['accessors'].append(acc);return aid
 tracks=bundle['animation']['tracks'];assert len(tracks)==2 and{t['target']['node']for t in tracks}=={17,19}
 times=tracks[0]['sampler']['input_times_s'];assert len(times)==193 and times[0]==0 and times[-1]==12 and all(a<b for a,b in zip(times,times[1:]))
 input_id=append(times,1,'SCALAR',[0],[12])
 for track in tracks:
  assert track['target']['path']=='rotation'and track['sampler']['interpolation']=='CUBICSPLINE'and track['sampler']['input_times_s']==times
  values=track['sampler']['output_in_value_out_quaternions_xyzw'];assert len(values)==193*12
  output_id=append(values,4,'VEC4');si=len(animation['samplers']);animation['samplers'].append({'input':input_id,'output':output_id,'interpolation':'CUBICSPLINE'});animation['channels'].append({'sampler':si,'target':track['target']})
 assert len(doc['animations'])==6;doc['animations'].append(animation);doc['buffers'][0]['byteLength']=len(binary)
 for key,value in original.items():
  if key not in ['buffers','bufferViews','accessors','animations']:assert doc[key]==value,key
 for key in ['bufferViews','accessors','animations']:assert doc[key][:len(original[key])]==original[key],key
 assert binary[:len(oldbin)]==oldbin
 # Every original embedded image and all geometry/old animation buffer slices remain in the exact old prefix.
 for view in original['bufferViews']:
  start=view.get('byteOffset',0);end=start+view['byteLength'];assert bytes(binary[start:end])==oldbin[start:end]
 encoded=json.dumps(doc,ensure_ascii=False,separators=(',',':')).encode();encoded+=b' '*((-len(encoded))%4)
 while len(binary)%4:binary.append(0)
 result=struct.pack('<III',magic,2,28+len(encoded)+len(binary))+struct.pack('<II',len(encoded),0x4e4f534a)+encoded+struct.pack('<II',len(binary),0x004e4942)+binary
 out.mkdir();model=out/'horse-sevket-portable-filtered-idle-v1.glb';model.write_bytes(result)
 receipt={'schema':'sevket_normalized_lineage_idle_append_v1','status':'ACTUAL_APPEND_EXPORT_ONLY; idle Mixer/fullsurface/neck-tail selfcontact/native visuals/production acceptance still open','normalized_input_file':str(source_file),'normalized_input_sha256':SOURCE,'normalized_input_bytes':len(raw),'upstream_original_sha256':UPSTREAM,'normalization_receipt_sha256':NORMALIZATION_RECEIPT,'normalization_exceptions':{'old_animation_accessors_repacked_reference_only':True,'exact_zero_weight_joint_components_zeroed':15897,'mesh_nodes_21_22_23_promoted_with_identity_local_transform':True,'original_six_decoded_animation_keys_exact':True,'mesh_basis_change_parity_receipt_sha256':parity_sha256},'normalization_parity_receipt_file':str(parity_file),'normalization_parity_receipt_sha256':parity_sha256,'derived_file':model.name,'derived_bytes':len(result),'derived_sha256':hashlib.sha256(result).hexdigest(),'bundle_sha256':BUNDLE,'generator_sha256':hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),'normalized_buffer_prefix_exact':True,'every_normalized_buffer_view_exact':True,'normalized_nodes_skins_meshes_materials_images_asset_exact':True,'normalized_accessors_and_six_animations_exact':True,'new_animation':animation['name'],'new_channels':[17,19],'new_interpolation':'CUBICSPLINE','new_duration_s':12,'animation_count':7,'skin_joints':15,'license':'CC-BY-4.0','source_credit':'Horse by sevketkabatas, CC BY4.0, https://sketchfab.com/3d-models/horse-53a6eb7ccf054aa2a378dd7ec08f88fe . Prior normalization repacked key references, zeroed exact-zero-weight JOINTS and promoted three mesh roots with identity transforms. This append adds unchanged reviewed reconstructed head/tail-only curves; no additional geometry/texture/skin/nativeclip change.','normalized_input_unchanged_after':hashlib.sha256(source_file.read_bytes()).hexdigest()==SOURCE}
 assert receipt['normalized_input_unchanged_after']
 (out/'APPEND-RECEIPT.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--lane-released',action='store_true',required=True);p.add_argument('--output-dir',type=pathlib.Path,required=True);p.add_argument('--parity-receipt',type=pathlib.Path,required=True);p.add_argument('--parity-sha256',required=True);a=p.parse_args()
 build(pathlib.Path('/workspace/shared/T2803-PORTABLE-NORMALIZER-V3-ACTUAL-20261022/horse-sevket-portable-import-v3.glb'),pathlib.Path('/workspace/shared/T2803-sevket-native-clips-20261022/engine-neutral-idle-clip.json'),a.output_dir,a.parity_receipt,a.parity_sha256)
