# SPDX-License-Identifier: CC0-1.0
#!/usr/bin/env python3
"""Original procedural reconstruction fixture. Python stdlib; no photograph inputs."""
import json, math, struct, pathlib, argparse
parser=argparse.ArgumentParser();parser.add_argument("--parameters",type=pathlib.Path,default=pathlib.Path(__file__).with_name("parameters.json"));parser.add_argument("--output-dir",type=pathlib.Path,default=pathlib.Path(__file__).parent);args=parser.parse_args();params=json.loads(args.parameters.read_text())
P=args.output_dir;P.mkdir(parents=True,exist_ok=True)
D={'asset':{'version':'2.0','generator':'original procedural equine fixture'},'scene':0,'scenes':[{'nodes':[0]}],'nodes':[],'meshes':[],'materials':[],'buffers':[],'bufferViews':[],'accessors':[],'animations':[]}
blob=bytearray();mesh_sources={}
def acc(data,typ,comp=5126):
 global blob
 while len(blob)%4:blob.append(0)
 fmt='f' if comp==5126 else 'I'; flat=[v for row in data for v in (row if isinstance(row,(list,tuple)) else [row])]; b=struct.pack('<'+fmt*len(flat),*flat); off=len(blob);blob.extend(b)
 vi=len(D['bufferViews']);D['bufferViews'].append({'buffer':0,'byteOffset':off,'byteLength':len(b)})
 a={'bufferView':vi,'componentType':comp,'count':len(data),'type':typ}
 if typ=='SCALAR':a.update(min=[min(data)],max=[max(data)])
 if typ=='VEC3':a.update(min=[min(r[i] for r in data) for i in range(3)],max=[max(r[i] for r in data) for i in range(3)])
 D['accessors'].append(a);return len(D['accessors'])-1
def mat(name,c,rough=.8):
 D['materials'].append({'name':name,'pbrMetallicRoughness':{'baseColorFactor':[*c,1],'metallicFactor':0,'roughnessFactor':rough}});return len(D['materials'])-1
coat=mat('equine_coat',params['coat_linear_rgb']);dark=mat('equine_mane_tail',[.028,.018,.012]);hoofmat=mat('equine_hooves',[.10,.09,.075]);eye=mat('equine_eyes',[.018,.012,.008],.16);muzzle=mat('equine_muzzle',[.105,.065,.048]);inner=mat('equine_ear_inner',[.16,.085,.060])
def node(name,parent=None,pos=(0,0,0),mesh=None,extras=None):
 n={'name':name,'translation':list(pos)}
 if mesh is not None:n['mesh']=mesh
 if extras:n['extras']=extras
 D['nodes'].append(n);i=len(D['nodes'])-1
 if parent is not None:D['nodes'][parent].setdefault('children',[]).append(i)
 return i
root=node('root',extras={'chicago4d_equine':{'version':'fixture_0.1','status':'original_conjectural_prototype','forward':'+Z','up':'+Y','units':'metres','license':'CC0-1.0','not_production':True}})
def mesh(name,verts,faces,ma):
 # Smooth normals accumulated from outward CCW triangles.
 ns=[[0.,0.,0.] for _ in verts]
 for a,b,c in faces:
  u=[verts[b][j]-verts[a][j] for j in range(3)];v=[verts[c][j]-verts[a][j] for j in range(3)];n=[u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]]
  for k in (a,b,c):
   for j in range(3):ns[k][j]+=n[j]
 ns=[[x/(math.sqrt(sum(t*t for t in n)) or 1) for x in n] for n in ns]
 mi=len(D['meshes']);mesh_sources[mi]=(verts,faces,ma);D['meshes'].append({'name':name,'primitives':[{'attributes':{'POSITION':acc(verts,'VEC3'),'NORMAL':acc(ns,'VEC3')},'indices':acc([x for f in faces for x in f],'SCALAR',5125),'material':ma}]});return mi
def loft(name,rings,ma,parent=root,N=24):
 # rings: center x,y,z; radius along x; radial direction vector (yz).
 vs=[]
 for x,y,z,rx,ry,rz in rings:
  for k in range(N):
   t=k*2*math.pi/N;vs.append((x+rx*math.cos(t),y+ry*math.sin(t),z+rz*math.sin(t)))
 fs=[]
 for j in range(len(rings)-1):
  for k in range(N):
   a=j*N+k;b=j*N+(k+1)%N;c=b+N;d=a+N;fs.extend([(a,b,c),(a,c,d)])
 # choose winding based on actual signed volume
 vs.extend([rings[0][:3],rings[-1][:3]]);a=len(vs)-2;b=a+1
 for k in range(N):fs.extend([(a,(k+1)%N,k),(b,(len(rings)-1)*N+k,(len(rings)-1)*N+(k+1)%N)])
 vol=sum(sum(vs[a][i]*([vs[b][1]*vs[c][2]-vs[b][2]*vs[c][1],vs[b][2]*vs[c][0]-vs[b][0]*vs[c][2],vs[b][0]*vs[c][1]-vs[b][1]*vs[c][0]][i]) for i in range(3)) for a,b,c in fs)
 if vol<0:fs=[(a,c,b) for a,b,c in fs]
 return node(name,parent,mesh=mesh(name,vs,fs,ma))
def ell(name,p,r,ma,parent=root):
 # rings along z, elliptical latitude
 rings=[]
 for j in range(17):
  t=math.pi*j/16;s=max(.002,math.sin(t));rings.append((p[0],p[1],p[2]-r[2]*math.cos(t),r[0]*s,r[1]*s,0))
 return loft(name,rings,ma,parent)
# Barrel, croup, shoulders, rising neck and refined head are original independent geometric forms.
loft('continuous_body_neck',[(0,1.19,-.90,.035,.04,0),(0,1.22,-.78,.21,.25,0),(0,1.20,-.55,.27,.32,0),(0,1.16,-.22,.28,.35,0),(0,1.17,.10,.25,.34,-.015),(0,1.25,.34,.25,.31,-.11),(0,1.43,.47,.17,.21,-.14),(0,1.63,.65,.13,.18,-.12),(0,1.80,.70,.10,.15,-.10),(0,1.89,.78,.08,.10,-.07)],coat)
head=node('head',root,(0,1.88,.80));ell('cranium',(0,0,.065),(.115,.16,.19),coat,head)
loft('face',[(0,.03,.12,.10,.13,0),(0,-.04,.24,.085,.105,0),(0,-.14,.36,.075,.085,0),(0,-.18,.43,.08,.065,0)],coat,head)
ell('muzzle',(0,-.185,.435),(.095,.075,.095),muzzle,head)
for s in [-1,1]:
 ell('eye_'+('l' if s==1 else 'r'),(s*.108,.025,.13),(.010,.016,.025),eye,head)
 ell('nostril_'+str(s),(s*.079,-.185,.465),(.004,.013,.017),dark,head)
 loft('ear_'+str(s),[(s*.075,.12,0,.043,.018,0),(s*.09,.25,-.018,.033,.018,0),(s*.09,.27,-.025,.002,.002,0)],coat,head)
 ell('cheek_'+str(s),(s*.052,-.06,.10),(.055,.085,.10),coat,head)
# Narrow crest mane and tapered hanging tail, without alpha cards.
loft('mane',[(0,1.41,.28,.026,.025,-.03),(0,1.65,.36,.035,.04,-.03),(0,1.77,.55,.03,.04,-.03),(0,1.96,.70,.018,.025,-.02)],dark)
tail=node('tail_base',root,(0,1.38,-.88));loft('tail',[(0,0,0,.065,.02,-.02),(0,-.20,-.10,.075,.02,-.03),(0,-.48,-.15,.065,.02,-.03),(0,-.82,-.13,.025,.01,-.01),(0,-.94,-.10,.002,.002,-.002)],dark,tail)
def segment(name,L,ra,rb,ma,parent):
 return loft(name,[(0,0,0,ra,.001,ra),(0,-L*.18,0,ra,0,ra),(0,-L*.82,0,rb,0,rb),(0,-L,0,rb*.85,0,rb*.85)],ma,parent)
limbs=[]
for fore in [True,False]:
 for s in [1,-1]:
  label=('fore' if fore else 'hind')+('_l' if s==1 else '_r');x=s*params['limb_lateral_offset_m'];z=.43 if fore else -.63;y=1.24
  a=node(label+'_upper',root,(x,y,z));segment(label+'_upper_mesh',.65,.11 if fore else .125,.047,coat,a)
  b=node(label+('_carpus' if fore else '_hock'),a,(0,-.65,0));segment(label+'_cannon',.55,.045,.032,coat,b)
  c=node(label+'_fetlock',b,(0,-.55,0));ell(label+'_fetlock_mesh',(0,0,0),(.038,.041,.044),coat,c)
  segment(label+'_pastern',.06,.032,.039,coat,c)
  loft(label+'_hoof',[(0,-.055,.01,.043,0,.062),(0,-.10,.025,.058,0,.085)],hoofmat,c)
  contact=node(label+'_contact',c,(0,-.10,.025),extras={'role':'hoof_ground_contact'})
  limbs.append((label,a,b,c,x,y,z,fore))
# Prototype sockets only: position deliberately explicit; no fitted harness or saddle is claimed.
for name,p in [('saddle',(0,1.48,-.12)),('rider_seat',(0,1.60,-.12)),('trace_l',(.28,1.17,.20)),('trace_r',(-.28,1.17,.20)),('breeching_l',(.28,1.1,-.7)),('breeching_r',(-.28,1.1,-.7)),('shaft_l',(.36,1.0,.05)),('shaft_r',(-.36,1.0,.05))]:node('socket_equine_'+name,root,p,extras={'status':'provisional_unfitted','role':name})
for s in [1,-1]:node('socket_equine_bit_'+('l' if s==1 else 'r'),head,(s*.095,-.20,.39),extras={'status':'provisional_unfitted'})
def rz(a):return [0,0,math.sin(a/2),math.cos(a/2)]
# Rotations are around local X: forward axis +Z; v=(0,-L*cos(a),-L*sin(a)).
def rx(a):return [math.sin(a/2),0,0,math.cos(a/2)]
def ik(y,z,fore):
 L1=.65;L2=.55;r=math.hypot(y,z);co=max(-1,min(1,(r*r-L1*L1-L2*L2)/(2*L1*L2)));bend=math.acos(co)*(1 if fore else -1)
 theta=math.atan2(-z,-y)-math.atan2(L2*math.sin(bend),L1+L2*math.cos(bend));return theta,bend
contacts={};K=97;T=params['walk_cycle_duration_s'];stride=params['stance_sweep_m']
for clip in ['idle','walk']:
 sam=[];chan=[];times=[i*T/(K-1) for i in range(K)];ti=acc(times,'SCALAR')
 def track(n,path,vals,typ='VEC4'):
  sam.append({'input':ti,'output':acc(vals,typ),'interpolation':'LINEAR'});chan.append({'sampler':len(sam)-1,'target':{'node':n,'path':path}})
 for j,(label,a,b,c,x,y,z,fore) in enumerate(limbs):
  A=[];B=[];C=[];off={'hind_l':0,'fore_l':.25,'hind_r':.5,'fore_r':.75}[label]
  for t in times:
   phase=(t/T+off)%1
   if clip=='idle':dz=0;lift=0
   elif phase<.62:dz=stride*(.5-phase/.62);lift=0
   else:q=(phase-.62)/.38;dz=stride*(-.5+q);lift=params['hoof_lift_m']*math.sin(math.pi*q)
   aa,bb=ik(.10+lift-y,dz,fore);A.append(rx(aa));B.append(rx(bb));C.append(rx(-aa-bb))
  track(a,'rotation',A);track(b,'rotation',B);track(c,'rotation',C)
  contacts[label]={'phase_offset':off,'stance':[0,.62]}
 track(tail,'rotation',[rx(.045*math.sin(2*math.pi*t/T)) for t in times])
 track(head,'rotation',[rx((.015 if clip=='idle' else .025)*math.sin(2*math.pi*t/T)) for t in times])
 D['animations'].append({'name':clip,'samplers':sam,'channels':chan,'extras':{'in_place':True,'cycle_duration_s':T,'speed_m_s':stride/(.62*T) if clip=='walk' else 0,'stride_m':stride/.62 if clip=='walk' else 0,'foot_contacts':contacts if clip=='walk' else 'all','status':'synthetic_kinematic_fixture_not_measured_motion'}})
# Rest pose is the exact neutral IK stance.
for label,a,b,c,x,y,z,fore in limbs:
 aa,bb=ik(.10-y,0,fore);D['nodes'][a]['rotation']=rx(aa);D['nodes'][b]['rotation']=rx(bb);D['nodes'][c]['rotation']=rx(-aa-bb)
# Merge leaf mesh siblings by material; semantic joint/socket nodes stay intact.
groups={}
for pi,pn in enumerate(D['nodes'][:]):
 for ni in pn.get('children',[]):
  n=D['nodes'][ni]
  if 'mesh' in n and not n.get('children') and n.get('translation',[0,0,0])==[0,0,0] and 'rotation' not in n:
   mi=n['mesh'];groups.setdefault((pi,mesh_sources[mi][2]),[]).append(ni)
for (parent,ma),indices in groups.items():
 if len(indices)<2:continue
 vs=[];fs=[]
 for ni in indices:
  vv,ff,_=mesh_sources[D['nodes'][ni].pop('mesh')];offset=len(vs);vs.extend(vv);fs.extend(tuple(x+offset for x in f) for f in ff)
 node(D['nodes'][parent]['name']+'_material_'+D['materials'][ma]['name'],parent,mesh=mesh('merged_semantic_group',vs,fs,ma))
used=sorted({n['mesh'] for n in D['nodes'] if 'mesh'in n});mapping={old:new for new,old in enumerate(used)};D['meshes']=[D['meshes'][i] for i in used]
for n in D['nodes']:
 if 'mesh'in n:n['mesh']=mapping[n['mesh']]
D['buffers']=[{'byteLength':len(blob)}];jb=json.dumps(D,separators=(',',':')).encode();jb+=b' '*((-len(jb))%4);blob+=b'\0'*((-len(blob))%4)
out=struct.pack('<III',0x46546c67,2,12+8+len(jb)+8+len(blob))+struct.pack('<II',len(jb),0x4e4f534a)+jb+struct.pack('<II',len(blob),0x004e4942)+blob
(P/'equine_light_harness_reconstructed_01.glb').write_bytes(out)
tri=sum(D['accessors'][m['primitives'][0]['indices']]['count']//3 for m in D['meshes'])
(P/'manifest.json').write_text(json.dumps({'asset_id':'equine_light_harness_reconstructed_01','status':'original conjectural articulated fixture; not production photographic model','license':'CC0-1.0','bytes':len(out),'triangles':tri,'meshes':len(D['meshes']),'nodes':len(D['nodes']),'animations':['idle','walk'],'withers_target_m':1.55,'frame':{'units':'metres','up':'+Y','forward':'+Z'},'missing':['continuous watertight anatomical topology','skinned deformation and full semantic equine skeleton','anatomy image/landmark comparison','sourced motion and start/stop/trot clips','fitted tack','authored Blender master','UV/PBR texture sets','LOD derivatives','rider and vehicle coupling integration']},indent=2)+'\n')
print(json.dumps({'bytes':len(out),'triangles':tri,'nodes':len(D['nodes'])}))
