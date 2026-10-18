# SPDX-License-Identifier: CC0-1.0
#!/usr/bin/env python3
"""Original CC0 prototype: bind procedural rest vertices to an equine joint fixture."""
import argparse,json,pathlib,subprocess,struct,math,sys
import numpy as np
P=pathlib.Path(__file__).parent
ap=argparse.ArgumentParser();ap.add_argument('--parameters',type=pathlib.Path,default=P/'parameters.json');ap.add_argument('--output-dir',type=pathlib.Path,default=P);args=ap.parse_args();out=args.output_dir;out.mkdir(parents=True,exist_ok=True)
subprocess.run([sys.executable,str(P/'horse_geometry.py'),'--parameters',str(args.parameters),'--output-dir',str(out)],check=True,capture_output=True)
f=out/'equine_light_harness_reconstructed_01.glb';raw=f.read_bytes();jl=struct.unpack_from('<I',raw,12)[0];d=json.loads(raw[20:20+jl]);old=raw[28+jl:];oa=d['accessors'];ov=d['bufferViews'];blob=bytearray();d['accessors']=[];d['bufferViews']=[]
NC={'SCALAR':1,'VEC3':3,'VEC4':4,'MAT4':16}
def read(i):
 a=oa[i];v=ov[a['bufferView']];dt={5126:'<f4',5125:'<u4',5123:'<u2'}[a['componentType']];return np.frombuffer(old,dtype=dt,count=a['count']*NC[a['type']],offset=v.get('byteOffset',0)+a.get('byteOffset',0)).reshape(a['count'],NC[a['type']]).copy()
def acc(vals,typ,comp=5126):
 while len(blob)%4:blob.append(0)
 a=np.asarray(vals,dtype={5126:'<f4',5125:'<u4',5123:'<u2'}[comp]).reshape(-1,NC[typ]);b=a.tobytes();v=len(d['bufferViews']);d['bufferViews'].append({'buffer':0,'byteOffset':len(blob),'byteLength':len(b)});blob.extend(b);entry={'bufferView':v,'componentType':comp,'count':len(a),'type':typ}
 if typ in ('VEC3','SCALAR'):entry.update(min=a.min(axis=0).tolist(),max=a.max(axis=0).tolist())
 d['accessors'].append(entry);return len(d['accessors'])-1
nodes=d['nodes'];parent={c:i for i,n in enumerate(nodes) for c in n.get('children',[])}
def local(n):
 x,y,z,w=n.get('rotation',[0,0,0,1]);m=np.eye(4);m[:3,:3]=[[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],[2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],[2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]];m[:3,3]=n.get('translation',[0,0,0]);return m
world={}
def W(i):
 if i not in world:world[i]=(W(parent[i]) if i in parent else np.eye(4))@local(nodes[i])
 return world[i]
animnodes={c['target']['node'] for a in d['animations'] for c in a['channels']};joints=sorted({0}|animnodes);ji={n:i for i,n in enumerate(joints)};jpos={n:W(n)[:3,3] for n in joints}
def owner(i):
 while i not in ji:i=parent[i]
 return i
# Neighboring joints share weight exactly at the joint plane; hoof vertices remain rigidly bound to their fetlock.
neighbors={j:[] for j in joints}
for j in joints:
 if j==0:continue
 p=owner(parent[j]);neighbors[j].append((p,jpos[j]));neighbors[p].append((j,jpos[j]))
groups={};ranges=[]
for ni,n in enumerate(nodes):
 if 'mesh' not in n:continue
 mat=d['meshes'][n['mesh']]['primitives'][0]['material'];g=groups.setdefault(mat,{'p':[],'n':[],'j':[],'w':[],'i':[]});p=d['meshes'][n['mesh']]['primitives'][0];vv=read(p['attributes']['POSITION']);nn=read(p['attributes']['NORMAL']);tr=W(ni);vv=(tr[:3,:3]@vv.T).T+tr[:3,3];nn=(tr[:3,:3]@nn.T).T;idx=read(p['indices']).ravel();offset=len(g['p']);own=owner(ni);jw=[];ww=[]
 for vertex in vv:
  weights={own:1.}
  if mat!=2:
   candidates=[]
   for other,pivot in neighbors[own]:
    dist=np.linalg.norm(vertex-pivot)
    if dist<.17:candidates.append((dist,other))
   if candidates:
    dist,other=min(candidates);fraction=.5*max(0,1-dist/.17)**2;weights={own:1-fraction,other:fraction}
  ids=[ji[x] for x in weights];ws=list(weights.values());jw.append(ids+[0]*(4-len(ids)));ww.append(ws+[0]*(4-len(ws)))
 g['p'].extend(vv.tolist());g['n'].extend(nn.tolist());g['j'].extend(jw);g['w'].extend(ww);g['i'].extend((idx+offset).tolist());ranges.append({'original_node':n['name'],'material':mat,'vertex_start':offset,'vertex_count':len(vv),'joint':nodes[own]['name']});del n['mesh']
newmeshes=[]
for mat,g in sorted(groups.items()):
 attrs={'POSITION':acc(g['p'],'VEC3'),'NORMAL':acc(g['n'],'VEC3'),'JOINTS_0':acc(g['j'],'VEC4',5123),'WEIGHTS_0':acc(g['w'],'VEC4')};newmeshes.append({'name':'skinned_'+d['materials'][mat]['name'],'primitives':[{'attributes':attrs,'indices':acc(g['i'],'SCALAR',5125),'material':mat}]});idx=len(nodes);nodes.append({'name':'skinned_'+d['materials'][mat]['name'],'mesh':len(newmeshes)-1,'skin':0});d['scenes'][0]['nodes'].append(idx)
d['meshes']=newmeshes
for m in newmeshes:
 for p in m['primitives']:
  for i in p['attributes'].values():d['bufferViews'][d['accessors'][i]['bufferView']]['target']=34962
  d['bufferViews'][d['accessors'][p['indices']]['bufferView']]['target']=34963
ibm=[np.linalg.inv(W(j)).flatten(order='F').tolist() for j in joints];d['skins']=[{'name':'c4d_equine_prototype_skin','joints':joints,'skeleton':0,'inverseBindMatrices':acc(ibm,'MAT4')}]
for animation in d['animations']:
 for sampler in animation['samplers']:
  for key in ('input','output'):
   oldid=sampler[key];sampler[key]=acc(read(oldid),oa[oldid]['type'],oa[oldid]['componentType'])
 animation['extras']['status']='synthetic_skinned_fixture_not_measured_motion'
d['asset']['generator']='original procedural equine skinned fixture';d['nodes'][0]['extras']['chicago4d_equine'].update(status='original_conjectural_skinned_prototype',version='fixture_0.2');d['buffers']=[{'byteLength':len(blob)}];jb=json.dumps(d,separators=(',',':')).encode();jb+=b' '*((-len(jb))%4);blob+=b'\0'*((-len(blob))%4);encoded=struct.pack('<III',0x46546c67,2,28+len(jb)+len(blob))+struct.pack('<II',len(jb),0x4e4f534a)+jb+struct.pack('<II',len(blob),0x004e4942)+blob
file=out/'equine_light_harness_skinned_prototype_01.glb';file.write_bytes(encoded);f.unlink();(out/'manifest.json').write_text(json.dumps({'asset_id':'equine_light_harness_skinned_prototype_01','license':'CC0-1.0','bytes':len(encoded),'triangles':sum(len(g['i'])//3 for g in groups.values()),'mesh_draws':len(newmeshes),'skin_joints':len(joints),'joint_table':[{'index':ji[j],'node':j,'name':nodes[j]['name'],'parent_joint':nodes[owner(parent[j])]['name'] if j in parent else None,'world_rest_m':jpos[j].tolist()} for j in joints],'vertex_ranges':ranges,'status':'prototype smooth-weighted skin; anatomical topology/rig/photographic acceptance outstanding'},indent=2)+'\n');print(file)
