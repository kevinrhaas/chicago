#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Original EMPTY covered W01 derivative; no renderer, Blender, network or app writes."""
import argparse,copy,hashlib,json,math,struct
from pathlib import Path
from PIL import Image,ImageStat
PARENT='274e737b51872983df792d0b24de8e75de8631890a8d586a32d9c6f0066484fb'
DIM={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}
def need(c,m):
 if not c:raise ValueError(m)
def sha(b):return hashlib.sha256(b).hexdigest()
def unit(v):
 d=math.sqrt(math.fsum(x*x for x in v));need(d>1e-12,'Degenerate vector');return [x/d for x in v]
def cross(a,b):return [a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]]
def sub(a,b):return [x-y for x,y in zip(a,b)]
def dot(a,b):return math.fsum(x*y for x,y in zip(a,b))
def srgb(hexvalue):
 v=int(hexvalue.lstrip('#'),16);o=[]
 for shift in [16,8,0]:
  c=((v>>shift)&255)/255;o.append(c/12.92 if c<=.04045 else ((c+.055)/1.055)**2.4)
 return o
class Asset:
 def __init__(self,raw):
  n=struct.unpack_from('<I',raw,12)[0];self.g=json.loads(raw[20:20+n]);self.old=copy.deepcopy(self.g);self.binary=bytearray(raw[28+n:]);self.oldbin=bytes(self.binary)
 def view(self,data,target=None):
  self.binary.extend(b'\0'*((-len(self.binary))%4));v={'buffer':0,'byteOffset':len(self.binary),'byteLength':len(data)}
  if target:v['target']=target
  i=len(self.g['bufferViews']);self.g['bufferViews'].append(v);self.binary.extend(data);return i
 def read(self,index):
  a=self.old['accessors'][index];need(a['componentType']==5126 and 'sparse' not in a,'Pinned float accessor required');v=self.old['bufferViews'][a['bufferView']];n=DIM[a['type']];need('byteStride' not in v,'Pinned contiguous stream required');off=v.get('byteOffset',0)+a.get('byteOffset',0);flat=struct.unpack_from('<'+'f'*(a['count']*n),self.oldbin,off);return [list(flat[i:i+n]) for i in range(0,len(flat),n)]
 def attr(self,values):
  need(values and all(math.isfinite(x) for p in values for x in p),'Finite nonempty attributes');n=len(values[0]);need(n in [2,3,4] and all(len(v)==n for v in values),'Attribute shape');raw=struct.pack('<'+'f'*(len(values)*n),*(x for p in values for x in p));vi=self.view(raw,34962);i=len(self.g['accessors']);self.g['accessors'].append({'bufferView':vi,'componentType':5126,'count':len(values),'type':'VEC'+str(n),'min':[min(p[k] for p in values) for k in range(n)],'max':[max(p[k] for p in values) for k in range(n)]});return i
 def mesh(self,name,data,material,parent):
  need(len(data['POSITION'])%3==0,'Triangle list');attrs={k:self.attr(v) for k,v in data.items()};mi=len(self.g['meshes']);self.g['meshes'].append({'name':name,'primitives':[{'attributes':attrs,'material':material}]});ni=len(self.g['nodes']);self.g['nodes'].append({'name':name,'mesh':mi});self.g['nodes'][parent].setdefault('children',[]).append(ni)
 def finish(self):
  self.binary.extend(b'\0'*((-len(self.binary))%4));self.g['buffers'][0]['byteLength']=len(self.binary);j=json.dumps(self.g,separators=(',',':')).encode();j+=b' '*((-len(j))%4);return struct.pack('<III',0x46546c67,2,28+len(j)+len(self.binary))+struct.pack('<II',len(j),0x4e4f534a)+j+struct.pack('<II',len(self.binary),0x004e4942)+self.binary
class Surface:
 def __init__(self):self.d={k:[] for k in ['POSITION','NORMAL','TEXCOORD_0','TANGENT']}
 def tri(self,points,normals,uvs):
  e1=sub(points[1],points[0]);e2=sub(points[2],points[0]);du1=uvs[1][0]-uvs[0][0];dv1=uvs[1][1]-uvs[0][1];du2=uvs[2][0]-uvs[0][0];dv2=uvs[2][1]-uvs[0][1];det=du1*dv2-dv1*du2;need(abs(det)>1e-15,'NonzeroUV triangle');t=[(a*dv2-b*dv1)/det for a,b in zip(e1,e2)];b=[(-a*du2+c*du1)/det for a,c in zip(e1,e2)]
  for p,n,uv in zip(points,normals,uvs):
   n=unit(n);tt=unit([x-n[k]*dot(t,n) for k,x in enumerate(t)]);w=1 if dot(cross(n,tt),b)>=0 else -1
   self.d['POSITION'].append(p);self.d['NORMAL'].append(n);self.d['TEXCOORD_0'].append(uv);self.d['TANGENT'].append([*tt,w])
 def quad(self,p,n,uv):
  for ii in [(0,1,2),(0,2,3)]:self.tri([p[i] for i in ii],[n[i] for i in ii],[uv[i] for i in ii])
 def box(self,center,size):
  for axis in range(3):
   other=[k for k in range(3) if k!=axis]
   for sign in [-1,1]:
    pp=[];nn=[];uv=[]
    for u,v in [(-1,-1),(1,-1),(1,1),(-1,1)]:
     q=list(center);q[axis]+=sign*size[axis]/2;q[other[0]]+=u*size[other[0]]/2;q[other[1]]+=v*size[other[1]]/2;pp.append(q);n=[0,0,0];n[axis]=sign;nn.append(n);uv.append([u*size[other[0]]/2/2.24,v*size[other[1]]/2/.14])
    if dot(cross(sub(pp[1],pp[0]),sub(pp[2],pp[0])),nn[0])<0:pp.reverse();nn.reverse();uv.reverse()
    self.quad(pp,nn,uv)
def cloth_textures(folder):
 folder.mkdir(parents=True,exist_ok=True);w,h=512,256;channels={k:Image.new('RGB',(w,h)) for k in ['color','normal','orm']};pix={k:v.load() for k,v in channels.items()}
 for y in range(h):
  for x in range(w):
   u=x/w;v=y/h;warp=math.sin(x*math.tau/4);weft=math.sin(y*math.tau/4);crossing=math.sin(x*math.tau/8)*math.sin(y*math.tau/8);long=math.sin(math.tau*(u*3+v*2))*.35+math.sin(math.tau*(u*7-v*5))*.15
   c=max(0,min(255,round(194+2.3*warp+2.0*weft+2.0*crossing+1.3*long)));pix['color'][x,y]=(c,c,c)
   nx=.075*math.cos(x*math.tau/4);ny=.075*math.cos(y*math.tau/4);nz=math.sqrt(1-nx*nx-ny*ny);pix['normal'][x,y]=tuple(round(127.5*(q+1)) for q in [nx,ny,nz]);pix['orm'][x,y]=(255,round(227+3*crossing),0)
 for k,im in channels.items():im.save(folder/('canvas_'+k+'.png'),compress_level=9)
 return {'size':[w,h],'tile_m':[.28,.14],'RGBA8_mip_bytes_estimate':w*h*4*3*4//3,'grade':'Original analytic woven-surface reconstruction; not a photograph/scan or dated textile weave measurement'}
def material_mean(a,mat):
 tex=mat.get('pbrMetallicRoughness',{}).get('baseColorTexture')
 if not tex:return [1,1,1]
 image=a.old['images'][a.old['textures'][tex['index']]['source']];v=a.old['bufferViews'][image['bufferView']];data=a.oldbin[v.get('byteOffset',0):v.get('byteOffset',0)+v['byteLength']]
 import io
 im=Image.open(io.BytesIO(data)).convert('RGB');sums=[0.,0.,0.]
 for pixel in im.getdata():
  for k,c in enumerate(pixel):
   q=c/255;sums[k]+=q/12.92 if q<=.04045 else ((q+.055)/1.055)**2.4
 return [v/(im.width*im.height) for v in sums]
def build(base,parts,variant,parameters,folder,textures):
 a=Asset(base);g=a.g;coat=variant['coat'];color={k:[v*coat[scalar] for v in srgb(coat['baseSrgb'][k])] for k,scalar in [('body','ageScalar'),('gear','gearScalar'),('canvas','canvasScalar')]}
 means={i:material_mean(a,m) for i,m in enumerate(a.old['materials'])};body=g['nodes'].index(next(n for n in g['nodes'] if n['name']=='vehicle_body'));root=g['scenes'][g.get('scene',0)]['nodes'][0]
 # Recolor coherent wood/paint groups; preserve original image/normal/UV binding.
 def tint(mi,target,mul=1):
  factor=[v*mul/means[mi][k] for k,v in enumerate(target)];need(min(factor)>=0 and max(factor)<=1,'Color factor exceeds glTF range');g['materials'][mi]['pbrMetallicRoughness']['baseColorFactor']=[*factor,1]
 tint(0,color['gear']);tint(1,color['gear'])
 clones={}
 for mi,target in [(0,color['gear']),(2,color['body']),(3,color['body'])]:
  new=copy.deepcopy(a.old['materials'][mi]);new['name']='covered_seeded_'+new['name'];new['pbrMetallicRoughness']['baseColorFactor']=[*(v*1.1/means[mi][k] for k,v in enumerate(target)),1];need(max(new['pbrMetallicRoughness']['baseColorFactor'])<=1,'Covered vertex multiplier range');clones[mi]=len(g['materials']);g['materials'].append(new)
 groups={}
 for p in parts:groups.setdefault(p['frame']+'_'+a.old['materials'][p['material']]['name'],[]).append(p)
 removed=[];protected=[];part_colors=[];retired_meshes=[]
 for mesh_index,(mesh,oldmesh) in enumerate(zip(g['meshes'],a.old['meshes'])):
  prim=mesh['primitives'][0];oldprim=oldmesh['primitives'][0];need('indices' not in prim,'Pinned nonindexed parent');owned=groups[mesh['name']];actual=a.read(oldprim['attributes']['POSITION']);source=[v for p in owned for v in p['positions']];need(struct.pack('<'+'f'*len(source)*3,*(x for p in source for x in p))==struct.pack('<'+'f'*len(actual)*3,*(x for p in actual for x in p)),'Exact authored-part mapping '+mesh['name'])
  keep=[];colors=[];offset=0
  for p in owned:
   size=len(p['positions']);furniture=p['name'].startswith(('driver_bench_','driver_footboard'))
   if furniture:removed.append({'part':p['name'],'triangles':size//3,'batch':mesh['name']});offset+=size;continue
   keep.extend(range(offset,offset+size));offset+=size;factor=1.;name=p['name'];board=coat['boardVariation']
   if name.startswith('floor_plank_'):factor=board['floorScalar']
   elif name.startswith('side_') and '_course_' in name:
    side=int(name.split('_')[1]);course=int(name.rsplit('_',1)[1]);factor=board['sideAndEndBoardScalars'][(0 if side>0 else 4)+(0 if course<2 else 2)]
   elif name.startswith('end_') and '_course_' in name:
    along=float(name.split('_')[1]);course=int(name.rsplit('_',1)[1]);factor=board['sideAndEndBoardScalars'][(1 if along<0 else 5)+(0 if course<2 else 2)]
   elif name.startswith('stake_') and not name.startswith('stake_bolt_'):
    _,side,k=name.split('_');factor=board['stakeScalars'][(0 if int(side)>0 else 3)+[0,1,1,2][int(k)]]
   colors.extend([[factor/1.1]*3 for _ in range(size)]);part_colors.append({'part':name,'oldSeedScalar':factor})
  if not keep:
   need(all(p['name'].startswith(('driver_bench_','driver_footboard')) for p in owned),'Empty batch must be wholly source-owned furniture');retired_meshes.append(mesh_index);protected.append({'batch':mesh['name'],'originalVertices':len(actual),'retainedVertices':0,'retiredOnlySourceOwnedFurnitureBatch':True});continue
  if len(keep)!=len(actual):
   for name,index in oldprim['attributes'].items():prim['attributes'][name]=a.attr([a.read(index)[i] for i in keep])
  if mesh['name'].startswith('vehicle_body_') and oldprim['material'] in clones:
   prim['material']=clones[oldprim['material']];prim['attributes']['COLOR_0']=a.attr(colors)
  protected.append({'batch':mesh['name'],'originalVertices':len(actual),'retainedVertices':len(keep),'retainedOriginalVertexOrder':True,'positionNormalUvTangentChangedOnlyByListedFurnitureRemoval':True})
 remap={old:new for new,old in enumerate(i for i in range(len(g['meshes'])) if i not in retired_meshes)}
 for node in g['nodes']:
  if 'mesh' in node:
   if node['mesh'] in retired_meshes:del node['mesh']
   else:node['mesh']=remap[node['mesh']]
 g['meshes']=[m for i,m in enumerate(g['meshes']) if i not in retired_meshes]
 # New steam-bent-bow appearance is original engineering reconstruction, not source tracing.
 bowmat=copy.deepcopy(a.old['materials'][1]);bowmat['name']='covered_original_bow_wood';bow_index=len(g['materials']);g['materials'].append(bowmat)
 refs={};reports=parameters['clothTexture'];sampler=0
 for kind in ['color','normal','orm']:
  raw=(textures/('canvas_'+kind+'.png')).read_bytes();iv=len(g['images']);g['images'].append({'bufferView':a.view(raw),'mimeType':'image/png','name':'covered_original_canvas_'+kind});ti=len(g['textures']);g['textures'].append({'source':iv,'sampler':sampler});refs[kind]=ti
 import io
 mean=math.fsum((c/255/12.92 if c/255<=.04045 else ((c/255+.055)/1.055)**2.4) for p in Image.open(textures/'canvas_color.png').getdata() for c in p)/(512*256*3)
 fac=[c/mean for c in color['canvas']];need(max(fac)<=1,'Canvas mean normalization exceeds1')
 canvas={'name':'covered_original_canvas','doubleSided':True,'pbrMetallicRoughness':{'baseColorFactor':[*fac,1],'baseColorTexture':{'index':refs['color']},'metallicFactor':0,'roughnessFactor':1,'metallicRoughnessTexture':{'index':refs['orm']}},'normalTexture':{'index':refs['normal'],'scale':.6},'extras':{'grade':'reconstructed','original_pixels':'CC0-1.0; source-generated analytic weave; no external pixels'}}
 canvas_index=len(g['materials']);g['materials'].append(canvas);seam=copy.deepcopy(canvas);seam['name']='covered_original_folded_seams';seam['pbrMetallicRoughness']['baseColorFactor']=[v*.94 for v in fac]+[1];seam_index=len(g['materials']);g['materials'].append(seam)
 w=.535;rise=1.10;cy=1.50;length=3.29;zbow=[-1.5,-.75,0,.75,1.5];phase=(coat['seedUint32']/2**32)*math.tau
 def ellipse(t,z):return [w*math.cos(t),cy+rise*math.sin(t),z]
 def en(t):return unit([math.cos(t)/w,math.sin(t)/rise,0])
 def cloth(t,z):
  j=max(0,min(3,int((z+1.5)/.75)));q=max(0,min(1,(z-zbow[j])/.75));between=math.sin(math.pi*q)**2;sag=(.024+.004*math.sin(phase+j))*between*(.2+.8*math.sin(t));fold=.0012*math.sin(6*t+phase+.4*z)**2*between;normal=en(t);return [v-normal[k]*(sag+fold) for k,v in enumerate(ellipse(t,z))]
 def raised(t,z,amount):return [v+en(t)[k]*amount for k,v in enumerate(cloth(t,z))]
 def patch(surface,point,umin,umax,vmin,vmax,nu,nv,uvfn):
  def at(u,v):
   q=point(u,v);du=sub(point(u+1e-5,v),point(u-1e-5,v));dv=sub(point(u,v+1e-5),point(u,v-1e-5));return q,unit(cross(du,dv)),uvfn(u,v)
  for i in range(nu):
   for j in range(nv):
    q=[at(umin+(umax-umin)*u/nu,vmin+(vmax-vmin)*v/nv) for u,v in [(i,j),(i+1,j),(i+1,j+1),(i,j+1)]];surface.quad([v[0] for v in q],[v[1] for v in q],[v[2] for v in q])
 cloth_surface=Surface();patch(cloth_surface,cloth,0,math.pi,-length/2,length/2,32,48,lambda t,z:[z/.28,t*.75/.14]);a.mesh('covered_original_canvas_sheet',cloth_surface.d,canvas_index,body)
 seams=Surface()
 for t in [math.pi/3,2*math.pi/3]:
  half=.007/math.hypot(w*math.sin(t),rise*math.cos(t));patch(seams,lambda theta,z,t=t,h=half:raised(theta,z,.0012*math.sin(math.pi*(theta-(t-h))/(2*h))**2),t-half,t+half,-1.645,1.645,3,48,lambda theta,z:[z/.28,theta*.75/.14])
 for end in [-1,1]:
  center=end*1.631;patch(seams,lambda t,z,c=center:raised(t,z,.0015*math.sin(math.pi*(z-(c-.010))/.020)**2),0,math.pi,center-.010,center+.010,32,3,lambda t,z:[z/.28,t*.75/.14])
 a.mesh('covered_original_sewn_and_folded_hems',seams.d,seam_index,body)
 bows=Surface()
 for z in zbow:
  def bow(t,p,z=z):
   n=en(t);center=[v-n[k]*.014 for k,v in enumerate(ellipse(t,z))];return [center[k]+.012*(math.cos(p)*n[k]+math.sin(p)*(1 if k==2 else 0)) for k in range(3)]
  # Ellipse tangent crossed with positive tube angle points outward.
  patch(bows,bow,0,math.pi,0,math.tau,32,6,lambda t,p:[t*.75/2.24,p*.012/.14])
 a.mesh('covered_original_five_bows',bows.d,bow_index,body)
 if variant['yoke']:
  yoke=Surface();yoke.box([-1.35,.06,2.075],[1.42,.12,.12])
  for sign in [-1,1]:yoke.box([-1.35+sign*.66,.19,2.075],[.05,.34,.05])
  a.mesh('covered_preserved_laid_by_yoke',yoke.d,1,root)
 # All original node transforms/pivots remain exact; only append child meshes.
 for i,n in enumerate(a.old['nodes']):
  for k,v in n.items():
   if k=='mesh' and v in retired_meshes:need('mesh' not in g['nodes'][i],'Source-owned empty furniture batch removed')
   elif k=='mesh':need(g['nodes'][i].get(k)==remap[v],'Protected original mesh ownership')
   elif k!='children':need(g['nodes'][i].get(k)==v,'Protected node field '+n['name']+' '+k)
  need(g['nodes'][i].get('children',[])[:len(n.get('children',[]))]==n.get('children',[]),'Protected child prefix')
 unsupported=[n['name'] for n in a.old['nodes'] if any(k in n['name'] for k in ['vehicle_seat_','vehicle_board_','vehicle_camera_','vehicle_driver_foot_','vehicle_hitch_','vehicle_collision'])]
 for node in g['nodes']:
  if node.get('name') in unsupported:node.setdefault('extras',{})['covered_empty_interface_supported']=False
 need(bytes(a.binary[:len(a.oldbin)])==a.oldbin,'Protected oldBIN prefix')
 tri=sum(g['accessors'][p['attributes']['POSITION']]['count']//3 for m in g['meshes'] for p in m['primitives'])
 g['asset']['generator']='Original covered W01 derivative from pinned reviewed project W01; no Blender claim'
 g['extras'].update(asset_id=variant['asset_id'],status='Unaccepted EMPTY covered prototype; no photographic, occupied or placement acceptance',socket_policy='Inherited seat/board/camera sockets are NOT supported occupied interfaces in this empty covered derivative',driver_furniture={'status':'Source-owned removable bench and footboard deliberately omitted to avoid1.18m seat penetrating1.07m cover; no physical seat remains','removed_parts':removed},statistics={'triangles':tri,'meshes':len(g['meshes']),'nodes':len(g['nodes'])},covered_derivative={'parent_sha256':PARENT,'legacy_record_id':variant['id'],'grade':'reconstructed','canvas_m':{'width':1.07,'length':3.29,'rise':1.10,'crown_above_base':2.60},'folds':'Original reconstructed 20-28mm maximum inter-bow drape over750mm spans plus1.2mm creases; stable seed; no measured historic canvas form','yoke':variant['yoke'],'no_occupant_horse_hitch_motion_boarding_claim':True,'unsupported_inherited_sockets':unsupported,'sourceOwnedRetiredMeshIndices':retired_meshes})
 raw=a.finish();folder.mkdir(parents=True,exist_ok=False);(folder/'covered-w01.glb').write_bytes(raw)
 receipt={'asset_id':variant['asset_id'],'legacy_record_id':variant['id'],'original_coordinates':variant['at_local_enu_m'],'original_bearing_deg':variant['bearing_deg'],'glb_sha256':sha(raw),'bytes':len(raw),'triangles':tri,'primitives':sum(len(m['primitives']) for m in g['meshes']),'materialGroupsReferenced':len({p['material'] for m in g['meshes'] for p in m['primitives']}),'parent_sha256':PARENT,'source_sha256':sha(Path(__file__).read_bytes()),'parameters_sha256':parameters['parametersSha256'],'authored_parts_sha256':parameters['authoredPartsSha256'],'parentBINprefixExact':True,'originalNodeTransformsPivotsAndChildPrefixesExact':True,'retiredOnlySourceOwnedFurniture':removed,'retiredSourceOwnedFurnitureMeshIndices':retired_meshes,'unsupportedInheritedSockets':unsupported,'retainedBatchReceipt':protected,'seeded_coat':coat,'bodyPartColorMapping':part_colors,'canvasTexture':reports,'estimatedActiveMappedRGBA8MipsBytes':6291456+reports['RGBA8_mip_bytes_estimate'],'limitations':['No actual ground qualification or main-scene placement','All new bows,seams,folds,weave,wear and cloth construction are original reconstruction','No manufacturer,owner,historical load or Dearborn identity','No occupied socket,driver,horse,hitch,forces,animation,riding or boarding support','Actual appearance,GLTF validation and matched comparisons remain separate required evidence']}
 (folder/'covered-w01.json').write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n');return receipt

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--parent',type=Path,required=True);ap.add_argument('--authored-parts',type=Path,required=True);ap.add_argument('--parameters',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);args=ap.parse_args();raw=args.parent.read_bytes();need(sha(raw)==PARENT,'Exact reviewed parentGLB required');params=json.loads(args.parameters.read_text());need(sha(args.authored_parts.read_bytes())==params['authoredPartsSha256'],'Exact canonical source ownership map required');parts=json.loads(args.authored_parts.read_text());need(len(params['variants'])==2,'Bounded two-variant study only');need(not args.output.exists(),'Fresh output only');args.output.mkdir(parents=True);params['parametersSha256']=sha(args.parameters.read_bytes());params['clothTexture']=cloth_textures(args.output/'original-canvas-textures');receipts=[]
 for variant in params['variants']:receipts.append(build(raw,parts,variant,params,args.output/variant['asset_id'],args.output/'original-canvas-textures'))
 (args.output/'receipt.json').write_text(json.dumps({'scope':'Unaccepted original two-variant EMPTY covered study','variants':receipts},indent=2)+'\n');print(json.dumps([{'asset_id':r['asset_id'],'sha256':r['glb_sha256'],'triangles':r['triangles'],'bytes':r['bytes'],'materials':r['materialGroupsReferenced']} for r in receipts]))
if __name__=='__main__':main()
