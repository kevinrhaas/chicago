# SPDX-License-Identifier: GPL-3.0-or-later
"""Compact original W01 optical study; original batches/geometry preserved."""
import argparse,json,hashlib,struct,copy,math
from pathlib import Path
import numpy as np
from generate_tiles import make_tiles
from authored_charts import load_original_charts
ap=argparse.ArgumentParser();ap.add_argument('--vehicle',type=Path,required=True);ap.add_argument('--parts',type=Path,required=True);ap.add_argument('--parameters',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);ap.add_argument('--numerical-chart-authoring',action='store_true',help='Explicit original numerical chart authoring; output may differ across BLAS backends and remains subject to downstream exact-product guards');a=ap.parse_args();recipe=json.loads(a.parameters.read_text())
def require(c,s):
 if not c:raise ValueError(s)
raw=a.vehicle.read_bytes();require(recipe['input_sha256']=='04820fc15b16c6f1b9b12487c2d6ceb3500d03c94094d84c73554f2b2d1f5709','Explicit reviewed hardware study input only');require(hashlib.sha256(raw).hexdigest()==recipe['input_sha256'],'hardware input hash');require(hashlib.sha256(a.parts.read_bytes()).hexdigest()==recipe['authored_parts_sha256'],'Exact recaptured authored parts required');parts=json.loads(a.parts.read_text());charts=None if a.numerical_chart_authoring else load_original_charts(raw,a.parts.read_bytes(),a.parameters.read_bytes());a.output.mkdir(exist_ok=False);n=struct.unpack_from('<I',raw,12)[0];g=json.loads(raw[20:20+n]);original=copy.deepcopy(g);b=bytearray(raw[28+n:]);oldbin=bytes(b);reports=make_tiles(recipe,a.output/'textures');mapping=copy.deepcopy(charts.mapping) if charts else []
def view(data,target=None):
 b.extend(b'\0'*((-len(b))%4));v={'buffer':0,'byteOffset':len(b),'byteLength':len(data)}
 if target:v['target']=target
 i=len(g['bufferViews']);g['bufferViews'].append(v);b.extend(data);return i
def attr(data):
 arr=np.array(data,dtype='<f4');require(arr.ndim==2 and np.isfinite(arr).all(),'finiteattributes');vi=view(arr.tobytes(),34962);i=len(g['accessors']);g['accessors'].append({'bufferView':vi,'componentType':5126,'count':len(arr),'type':'VEC'+str(arr.shape[1]),'min':arr.min(0).tolist(),'max':arr.max(0).tolist()});return i
def original_attr(batch,semantic):
 data,metadata=charts.attribute(batch,semantic);vi=view(data,34962);i=len(g['accessors']);g['accessors'].append({'bufferView':vi,**metadata});return i
g['images']=[];g['textures']=[];g['samplers']=[{'wrapS':10497,'wrapT':10497,'magFilter':9729,'minFilter':9987}];refs={}
for family in reports:
 refs[family]={}
 for kind in ['color','normal','orm']:
  vi=view((a.output/'textures'/(family+'_'+kind+'.png')).read_bytes());ii=len(g['images']);g['images'].append({'bufferView':vi,'mimeType':'image/png'});ti=len(g['textures']);g['textures'].append({'source':ii,'sampler':0});refs[family][kind]=ti
for mi,m in enumerate(g['materials']):
 if mi==5:continue
 family='paint'if mi==0 else'iron'if mi==4 else'wood';pbr=m['pbrMetallicRoughness'];pbr['baseColorFactor']=[c*2 for c in pbr['baseColorFactor'][:3]]+[1];require(max(pbr['baseColorFactor'])<=1,'outofrangefactor');pbr['baseColorTexture']={'index':refs[family]['color']};pbr['metallicRoughnessTexture']={'index':refs[family]['orm']};pbr['roughnessFactor']=1;pbr['metallicFactor']=1 if family=='iron'else 0;m['normalTexture']={'index':refs[family]['normal']};m['extras']={'grade':recipe['grade'],'original_source':'generate_tiles.py analytic dimensional surfaces; no photographs','cut_end_chart':'constant neutral sample; no claimed endgrain anatomy'}
for mesh in g['meshes']:
 p=mesh['primitives'][0];mat=p['material'];family='paint'if mat==0 else'iron'if mat==4 else'wood';cfg=recipe[family];sx,sy=cfg['tile_m'];matches=[r for r in parts if r['frame']+'_'+original['materials'][r['material']]['name']==mesh['name']];require(matches,'sourcepartbatch');allp=np.array([v for r in matches for v in r['positions']],dtype='<f4');pa=original['accessors'][p['attributes']['POSITION']];pv=original['bufferViews'][pa['bufferView']];actual=np.frombuffer(oldbin,dtype='<f4',count=pa['count']*3,offset=pv['byteOffset']).reshape(-1,3);require(np.array_equal(allp,actual),'sourcepartactualmapping');uvs=[];tangents=[]
 if mat==5:continue
 if charts is not None:
  p['attributes']['TEXCOORD_0']=original_attr(mesh['name'],'TEXCOORD_0');p['attributes']['TANGENT']=original_attr(mesh['name'],'TANGENT');continue
 for r in matches:
  lp=np.array(r['local_positions']);ln=np.array(r['local_normals']);pos=np.array(r['positions']);ns=np.array(r['normals']);center=(lp.min(0)+lp.max(0))/2;vals,axes=np.linalg.eigh(np.cov((lp-center).T));axes=axes[:,np.argsort(vals)[::-1]]
  for k in range(3):
   if axes[np.argmax(abs(axes[:,k])),k]<0:axes[:,k]*=-1
  grain=axes[:,0];ring=r['name'].startswith(('wood_felloe','iron_tyre'));hub=r['name'].startswith('hub_')or r['name']=='band';flatcount=0;anisotropy=1
  offset=int(hashlib.sha256(r['name'].encode()).hexdigest()[:8],16)/2**32
  for i in range(0,len(lp),3):
   q=lp[i:i+3];nlocal=ln[i];flat=hub or(abs(nlocal@grain)>.8 and not ring)
   if flat:
    uv=np.tile(np.array(reports[family]['flat_chart_uv']),(3,1));ts=[]
    for normal in ns[i:i+3]:
     axis=np.array([1.,0,0])if abs(normal[0])<.9 else np.array([0.,1,0]);t=axis-normal*np.dot(axis,normal);t/=np.linalg.norm(t);ts.append([*t,1])
    flatcount+=1
   else:
    if ring:
     rad=np.sqrt(lp[:,1]**2+lp[:,2]**2).mean();u=np.unwrap(np.arctan2(q[:,2],q[:,1]))*rad/sx+offset;v=(q[:,0]if abs(nlocal[0])<.8 else np.sqrt(q[:,1]**2+q[:,2]**2))/sy;uv=np.stack([u,v],1)
    else:
     transverse=min([axes[:,1],axes[:,2]],key=lambda q:abs(q@nlocal));uv=np.stack([q@grain/sx+offset,q@transverse/sy+.19],1)
    e=np.stack([pos[i+1]-pos[i],pos[i+2]-pos[i]]);du=np.stack([uv[1]-uv[0],uv[2]-uv[0]]);require(abs(np.linalg.det(du))>1e-14,'zeroUV');der=np.linalg.solve(du,e);ts=[]
    for normal in ns[i:i+3]:
     t=der[0]-normal*np.dot(normal,der[0]);t/=np.linalg.norm(t);w=1 if np.dot(np.cross(normal,t),der[1])>0 else-1;ts.append([*t,w])
    # Compare derivatives after converting UV coordinateunits back to metres.
    world_per_m=der/np.array([[sx],[sy]]);sing=np.linalg.svd(world_per_m,compute_uv=False);anisotropy=max(anisotropy,float(sing[0]/sing[-1]))
   uvs.extend(uv);tangents.extend(ts)
  mapping.append({'part':r['name'],'batch':mesh['name'],'triangles':len(lp)//3,'flat_constant_neutral_chart_triangles':flatcount,'physical_chart_anisotropy':anisotropy,'grain':'authored localmajoraxis; ringscircumferential; hubs/cutends intentionallyflat','tile_m':[sx,sy]})
 p['attributes']['TEXCOORD_0']=attr(uvs);p['attributes']['TANGENT']=attr(tangents)
b.extend(b'\0'*((-len(b))%4));g['buffers'][0]['byteLength']=len(b);g['extras']['material_study']={'grade':recipe['grade'],'endfaces':recipe['endfaces'],'images':'original dimensional procedural surfaces; not photographs','draw_batches_unchanged':23};j=json.dumps(g,separators=(',',':')).encode();j+=b' '*((-len(j))%4);out=struct.pack('<III',0x46546c67,2,28+len(j)+len(b))+struct.pack('<II',len(j),0x4e4f534a)+j+struct.pack('<II',len(b),0x004e4942)+b;(a.output/'wagon-w01.glb').write_bytes(out);receipt={'sha256':hashlib.sha256(out).hexdigest(),'status':'UNACCEPTED opticalstudy; no photographic/periodfinishclaim','source_mapping':mapping,'tiles':reports,'decoded_RGBA8_mips_total_bytes_estimate':sum(x['decoded_RGBA8_mips_bytes_estimate']for x in reports.values()),'draws':sum(len(m['primitives'])for m in g['meshes']),'oldBINprefix_exact':bytes(b[:len(oldbin)])==oldbin,'default_geometry_accessor_refs_exact':all(a['primitives'][0]['attributes']['POSITION']==z['primitives'][0]['attributes']['POSITION']and a['primitives'][0]['attributes']['NORMAL']==z['primitives'][0]['attributes']['NORMAL']for a,z in zip(g['meshes'],original['meshes']))};receipt['chart_source']=charts.receipt if charts else {'mode':'explicit numerical authoring','scope':'Current numerical author-time measurements; no portable chart or product equality is implied'};(a.output/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({k:v for k,v in receipt.items()if k not in['tiles','source_mapping']}))
