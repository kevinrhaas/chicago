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
coat=mat('equine_coat',params['coat_linear_rgb']);dark=mat('equine_mane_tail',[.028,.018,.012]);hoofmat=mat('equine_hooves',[.10,.09,.075]);eye=mat('equine_eyes',[.018,.012,.008],.16);muzzle=mat('equine_muzzle',[.16,.09,.055]);inner=mat('equine_ear_inner',[.16,.085,.060])
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
def loft(name,rings,ma,parent=root,N=24,cap_start=True,cap_end=True):
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
 if cap_start and cap_end:
  vs.extend([rings[0][:3],rings[-1][:3]]);a=len(vs)-2;b=a+1
  for k in range(N):fs.extend([(a,(k+1)%N,k),(b,(len(rings)-1)*N+k,(len(rings)-1)*N+(k+1)%N)])
 else:
  if cap_start:
   a=len(vs);vs.append(rings[0][:3])
   for k in range(N):fs.append((a,(k+1)%N,k))
  if cap_end:
   b=len(vs);vs.append(rings[-1][:3])
   for k in range(N):fs.append((b,(len(rings)-1)*N+k,(len(rings)-1)*N+(k+1)%N))
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
neck_join=loft('continuous_body_neck',[(0,1.19,-.90,.035,.04,0),(0,1.22,-.78,.21,.25,0),(0,1.20,-.55,.27,.32,0),(0,1.16,-.22,.28,.35,0),(0,1.17,.10,.25,.34,-.015),(0,1.25,.34,.25,.31,-.11),(0,1.43,.47,.17,.21,-.14),(0,1.63,.65,.13,.18,-.12),(0,1.80,.70,.10,.15,-.10),(0,1.89,.78,.08,.10,-.07)],coat,cap_end=False)
D['nodes'][neck_join]['extras']={'equine_join':{'role':'neck','interface':list(range(216,240)),'band':list(range(192,216)),'head_weight':.25}}
head=node('head',root,(0,1.88,.80))
# Original continuous cranio-facial contour, not separate spheroidal cheeks. Neck,
# head joint/rest and all bit/socket frames are retained; anatomical fit unaccepted.
head_join=loft('continuous_craniofacial',[(0,.01,-.02,.08,.10,-.07),(0,.015,.02,.107,.145,0),(0,.005,.08,.111,.139,0),(0,-.005,.135,.105,.125,0),(0,-.038,.20,.09,.105,0),(0,-.075,.28,.081,.093,0),(0,-.125,.36,.073,.078,0),(0,-.158,.405,.075,.063,0),(0,-.18,.43,.08,.06,0)],coat,head,N=24,cap_start=False)
D['nodes'][head_join]['extras']={'equine_join':{'role':'head','interface':list(range(24)),'band':list(range(24,48)),'head_weight':.8}}
loft('muzzle',[(0,-.17,.375,.073,.059,0),(0,-.182,.425,.086,.065,0),(0,-.188,.475,.083,.056,0),(0,-.19,.505,.067,.043,0),(0,-.19,.514,.045,.028,0)],muzzle,head)
ell('mouth_crease',(0,-.232,.465),(.070,.004,.036),dark,head)
def pinna(side):
 # Two continuous curved surfaces with a closed coat-colored rim. Scooped front
 # uses the existing inner-ear material, no copied anatomical source or alpha card.
 vs=[];N=9;M=17;faces_front=[];faces_back=[];rim=[]
 for back in [False,True]:
  for j in range(M-1):
   t=j/(M-1);width=.005+.032*math.sin(math.pi*(.12+.88*t));cx=side*(.075+.018*t);yy=.12+.22*t;zz=(-.006 if side>0 else .010)+(-.020 if side>0 else -.032)*t
   for k in range(N):
    u=2*k/(N-1)-1
    depth=(-.021-.007*(1-u*u)*math.sin(math.pi*t)) if back else (.012-.024*(1-u*u)*math.sin(math.pi*t))
    vs.append((cx+width*u,yy,zz+depth))
 # A single closed apex replaces the previous flat 10mm-wide last row.
 # Base and all existing lower rows, head frame and maximum height are retained.
 o=(M-1)*N;apex=len(vs);t=1;cx=side*(.075+.018*t);zz=(-.006 if side>0 else .010)+(-.020 if side>0 else -.032)*t
 vs.append((cx,.12+.22*t,zz-.0045))
 for j in range(M-2):
  for k in range(N-1):
   a=j*N+k;b=a+1;c=b+N;d=a+N
   faces_front.extend([(a,b,c),(a,c,d)]);faces_back.extend([(a+o,c+o,b+o),(a+o,d+o,c+o)])
 for k in range(N-1):
  a=(M-2)*N+k;b=a+1
  faces_front.append((a,b,apex));faces_back.append((a+o,apex,b+o))
 boundary=list(range(N))+[j*N+N-1 for j in range(1,M-1)]+[apex]+[j*N for j in range(M-2,0,-1)]
 for k,a in enumerate(boundary):
  b=boundary[(k+1)%len(boundary)]
  if b==apex:rim.append((a,a+o,apex))
  elif a==apex:rim.append((apex,b+o,b))
  else:rim.extend([(a,a+o,b+o),(a,b+o,b)])
 def ear_surface(name,faces,material):
  used=sorted({i for f in faces for i in f});remap={old:new for new,old in enumerate(used)}
  node(name,head,mesh=mesh(name,[vs[i]for i in used],[tuple(remap[i]for i in f)for f in faces],material))
 ear_surface('ear_outer_'+str(side),faces_back+rim,coat)
 ear_surface('ear_concave_'+str(side),faces_front,inner)
for s in [-1,1]:
 ell('eye_'+('l' if s==1 else 'r'),(s*.106,.025,.13),(.009,.010,.018),eye,head)
 # Coat rim follows side skull around the exposed eye rather than a detached bead.
 verts=[];faces=[];N=32;K=8
 for j in range(N):
  t=2*math.pi*j/N
  for k in range(K):
   q=2*math.pi*k/K;tube=.0022;verts.append((s*(.109+tube*math.cos(q)),.025+(.011+tube*math.sin(q))*math.sin(t),.13+(.020+tube*math.sin(q))*math.cos(t)))
 for j in range(N):
  for k in range(K):
   a=j*K+k;b=((j+1)%N)*K+k;c=((j+1)%N)*K+(k+1)%K;d=j*K+(k+1)%K;faces.extend([(a,b,c),(a,c,d)] if s>0 else[(a,c,b),(a,d,c)])
 node('eyelid_rim_'+str(s),head,mesh=mesh('eyelid_rim_'+str(s),verts,faces,coat))
 ell('nostril_'+str(s),(s*.081,-.172,.462),(.004,.017,.026),dark,head)
 pinna(s)
# Narrow crest mane and tapered hanging tail, without alpha cards.
loft('mane',[(0,1.39,.30,.009,.015,-.025),(0,1.48,.33,.035,.045,-.055),(0,1.65,.48,.034,.045,-.05),(0,1.80,.59,.028,.04,-.045),(0,1.93,.71,.016,.025,-.035)],dark)
tail=node('tail_base',root,(0,1.38,-.88));loft('tail',[(0,0,0,.065,.02,-.02),(0,-.20,-.10,.075,.02,-.03),(0,-.48,-.15,.065,.02,-.03),(0,-.82,-.13,.025,.01,-.01),(0,-.94,-.10,.002,.002,-.002)],dark,tail)
def segment(name,L,ra,rb,ma,parent):
 return loft(name,[(0,0,0,ra,.001,ra),(0,-L*.18,0,ra,0,ra),(0,-L*.82,0,rb,0,rb),(0,-L,0,rb*.85,0,rb*.85)],ma,parent)
limbs=[]
for fore in [True,False]:
 for s in [1,-1]:
  label=('fore' if fore else 'hind')+('_l' if s==1 else '_r');x=s*params['limb_lateral_offset_m'];z=.43 if fore else -.63;y=1.24
  a=node(label+'_upper',root,(x,y,z));segment(label+'_upper_mesh',.65,.11 if fore else .125,.047,coat,a)
  b=node(label+('_carpus' if fore else '_hock'),a,(0,-.65,0));segment(label+'_cannon',.55,.045,.032,coat,b)
  c=node(label+'_fetlock',b,(0,-.55,0));ell(label+'_fetlock_mesh',(0,-.006,-.012),(.036,.046,.044),coat,c)
  segment(label+'_pastern',.06,.032,.039,coat,c)
  # Sloping hoof wall: narrow coronet, fuller toe and flat authored sole.
  loft(label+'_hoof',[(0,-.048,.004,.038,0,.050),(0,-.062,.008,.044,0,.060),(0,-.092,.022,.057,0,.082),(0,-.10,.025,.060,0,.090)],hoofmat,c)
  contact=node(label+'_contact',c,(0,-.10,.025),extras={'role':'hoof_ground_contact'})
  limbs.append((label,a,b,c,x,y,z,fore))
# Prototype sockets only: position deliberately explicit; no fitted harness or saddle is claimed.
for name,p in [('saddle',(0,1.48,-.12)),('rider_seat',(0,1.60,-.12)),('trace_l',(.28,1.17,.20)),('trace_r',(-.28,1.17,.20)),('breeching_l',(.28,1.1,-.7)),('breeching_r',(-.28,1.1,-.7)),('shaft_l',(params.get('shaft_lateral_offset_m',.405),1.0,.05)),('shaft_r',(-params.get('shaft_lateral_offset_m',.405),1.0,.05))]:node('socket_equine_'+name,root,p,extras={'status':'provisional_unfitted','role':name})
for s in [1,-1]:node('socket_equine_bit_'+('l' if s==1 else 'r'),head,(s*.095,-.20,.39),extras={'status':'provisional_unfitted'})
def rz(a):return [0,0,math.sin(a/2),math.cos(a/2)]
# Rotations are around local X: forward axis +Z; v=(0,-L*cos(a),-L*sin(a)).
def rx(a):return [math.sin(a/2),0,0,math.cos(a/2)]
def ik(y,z,fore):
 L1=.65;L2=.55;r=math.hypot(y,z);co=max(-1,min(1,(r*r-L1*L1-L2*L2)/(2*L1*L2)));bend=math.acos(co)*(1 if fore else -1)
 theta=math.atan2(-z,-y)-math.atan2(L2*math.sin(bend),L1+L2*math.cos(bend));return theta,bend
contacts={};K=193;T=params['walk_cycle_duration_s'];stride=params['stance_sweep_m'];S=params.get('stance_fraction',.62)
assert 0<S<1 and T>0 and stride>0
phase_offsets={'hind_l':0,'fore_l':.25,'hind_r':.5,'fore_r':.75}
def qmul(a,b):
 x,y,z,w=a;X,Y,Z,W=b
 return [w*X+x*W+y*Z-z*Y,w*Y-x*Z+y*W+z*X,w*Z+x*Y-y*X+z*W,w*W-x*X-y*Y-z*Z]
def qinv(q):return [-q[0],-q[1],-q[2],q[3]]
def qrotate(q,v):return qmul(qmul(q,[*v,0]),qinv(q))[:3]
def from_down(v):
 # Original shortest-arc quaternion maps actual rest bone direction -Y to v.
 n=math.sqrt(sum(x*x for x in v));v=[x/n for x in v];q=[-v[2],0,v[0],1-v[1]];n=math.sqrt(sum(x*x for x in q))
 if n<1e-10:raise ValueError('Antiparallel target requires explicit bend frame')
 return [x/n for x in q]
def solve_limb_3d(target,fore):
 # Sphere-intersection knee solve in an explicit reconstructed anatomical bend plane.
 # target is ankle relative to hip, metres; no endpoint clipping or marker motion.
 L1=.65;L2=.55;r=math.sqrt(sum(x*x for x in target))
 if not abs(L1-L2)<r<L1+L2:raise ValueError('Unreachable ankle target')
 d=[x/r for x in target];axis=[1.,0.,0.];projection=sum(axis[i]*d[i] for i in range(3));axis=[axis[i]-projection*d[i] for i in range(3)];n=math.sqrt(sum(x*x for x in axis));axis=[x/n for x in axis]
 perp=[axis[1]*d[2]-axis[2]*d[1],axis[2]*d[0]-axis[0]*d[2],axis[0]*d[1]-axis[1]*d[0]]
 sign=-1 if fore else 1;distance=(L1*L1-L2*L2+r*r)/(2*r);height=math.sqrt(max(0,L1*L1-distance*distance));knee=[distance*d[i]+sign*height*perp[i] for i in range(3)]
 upper=from_down(knee);lower_vector=[target[i]-knee[i] for i in range(3)];lower=from_down(qrotate(qinv(upper),lower_vector));fetlock=qinv(qmul(upper,lower))
 return upper,lower,fetlock
for clip in ['idle','walk','trot']:
 contacts={} # Clip-local metadata; later trot must not mutate saved walk contact offsets.
 T=params['walk_cycle_duration_s'];stride=params['stance_sweep_m'];S=params.get('stance_fraction',.62);lift_height=params['hoof_lift_m'];phase_offsets={'hind_l':0,'fore_l':.25,'hind_r':.5,'fore_r':.75}
 if clip=='trot':
  config=params['trot_reconstruction'];T=config['cycle_duration_s'];stride=config['stance_sweep_m'];S=config['stance_fraction'];lift_height=config['hoof_lift_m'];phase_offsets={'fore_l':0,'hind_r':0,'fore_r':.5,'hind_l':.5}
 assert 0<S<1 and T>0 and stride>0
 sam=[];chan=[];times=sorted({i*T/(K-1) for i in range(K)}|{((S-off)%1)*T for off in phase_offsets.values()});ti=acc(times,'SCALAR')
 def track(n,path,vals,typ='VEC4'):
  sam.append({'input':ti,'output':acc(vals,typ),'interpolation':'LINEAR'});chan.append({'sampler':len(sam)-1,'target':{'node':n,'path':path}})
 for j,(label,a,b,c,x,y,z,fore) in enumerate(limbs):
  A=[];B=[];C=[];off=phase_offsets[label]
  for t in times:
   phase=(t/T+off)%1
   if clip=='idle':dz=0;lift=0
   elif phase<S:dz=stride*(.5-phase/S);lift=0
   else:
    # Hermite swing matches planted-foot travel velocity at lift-off/touchdown.
    # Quartic lift has zero endpoint velocity: a synthetic engineering choice.
    q=(phase-S)/(1-S);m=-stride*(1-S)/S
    dz=(2*q**3-3*q*q+1)*(-stride/2)+(q**3-2*q*q+q)*m+(-2*q**3+3*q*q)*(stride/2)+(q**3-q*q)*m
    lift=lift_height*16*q*q*(1-q)*(1-q)
   if clip=='trot':
    qa,qb,qc=solve_limb_3d([0,.10+lift-y,dz],fore);A.append(qa);B.append(qb);C.append(qc)
   else:
    aa,bb=ik(.10+lift-y,dz,fore);A.append(rx(aa));B.append(rx(bb));C.append(rx(-aa-bb))
  track(a,'rotation',A);track(b,'rotation',B);track(c,'rotation',C)
  contacts[label]={'phase_offset':off,'stance':[0,S]}
 track(tail,'rotation',[rx(.045*math.sin(2*math.pi*t/T)) for t in times])
 track(head,'rotation',[rx((.015 if clip=='idle' else .025)*math.sin(2*math.pi*t/T)) for t in times])
 D['animations'].append({'name':clip,'samplers':sam,'channels':chan,'extras':{'in_place':True,'cycle_duration_s':T,'speed_m_s':stride/(S*T) if clip!='idle' else 0,'stride_m':stride/S if clip!='idle' else 0,'stance_fraction':S if clip!='idle' else 1,'foot_contacts':contacts if clip!='idle' else 'all','phase_offsets':phase_offsets if clip!='idle' else {},'motion_basis':'synthetic contact-continuous Hermite swing; not measured motion','status':'synthetic_kinematic_fixture_not_measured_motion'}})
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
 vs=[];fs=[];join=None
 for ni in indices:
  vv,ff,_=mesh_sources[D['nodes'][ni].pop('mesh')];offset=len(vs);vs.extend(vv);fs.extend(tuple(x+offset for x in f) for f in ff)
  if 'equine_join' in D['nodes'][ni].get('extras',{}):
   join=dict(D['nodes'][ni]['extras']['equine_join']);join['interface']=[x+offset for x in join['interface']];join['band']=[x+offset for x in join['band']]
 node(D['nodes'][parent]['name']+'_material_'+D['materials'][ma]['name'],parent,mesh=mesh('merged_semantic_group',vs,fs,ma),extras={'equine_join':join} if join else None)
used=sorted({n['mesh'] for n in D['nodes'] if 'mesh'in n});mapping={old:new for new,old in enumerate(used)};D['meshes']=[D['meshes'][i] for i in used]
for n in D['nodes']:
 if 'mesh'in n:n['mesh']=mapping[n['mesh']]
D['buffers']=[{'byteLength':len(blob)}];jb=json.dumps(D,separators=(',',':')).encode();jb+=b' '*((-len(jb))%4);blob+=b'\0'*((-len(blob))%4)
out=struct.pack('<III',0x46546c67,2,12+8+len(jb)+8+len(blob))+struct.pack('<II',len(jb),0x4e4f534a)+jb+struct.pack('<II',len(blob),0x004e4942)+blob
(P/'equine_light_harness_reconstructed_01.glb').write_bytes(out)
tri=sum(D['accessors'][m['primitives'][0]['indices']]['count']//3 for m in D['meshes'])
(P/'manifest.json').write_text(json.dumps({'asset_id':'equine_light_harness_reconstructed_01','status':'original conjectural articulated fixture; not production photographic model','license':'CC0-1.0','bytes':len(out),'triangles':tri,'meshes':len(D['meshes']),'nodes':len(D['nodes']),'animations':['idle','walk','trot'],'withers_target_m':1.55,'frame':{'units':'metres','up':'+Y','forward':'+Z'},'missing':['continuous watertight anatomical topology','skinned deformation and full semantic equine skeleton','anatomy image/landmark comparison','sourced motion and start/stop/trot clips','fitted tack','authored Blender master','UV/PBR texture sets','LOD derivatives','rider and vehicle coupling integration']},indent=2)+'\n')
print(json.dumps({'bytes':len(out),'triangles':tri,'nodes':len(D['nodes'])}))
