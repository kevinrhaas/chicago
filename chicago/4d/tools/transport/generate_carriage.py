#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
import json,math,struct,pathlib
import argparse
cli=argparse.ArgumentParser();cli.add_argument('--parameters',type=pathlib.Path,default=pathlib.Path(__file__).with_name('parameters.json'));cli.add_argument('--output-dir',type=pathlib.Path,default=pathlib.Path(__file__).parent);args=cli.parse_args();P=args.output_dir;P.mkdir(parents=True,exist_ok=True)
params=json.loads(args.parameters.read_text())
# Reject malformed dimensional inputs rather than emitting invalid glTF.
for key in ['wheelbase_m','track_m','wheel_radius_front_m','wheel_radius_rear_m','shaft_length_m','shaft_inner_spacing_tip_m','steering_limit_deg']:
 value=params[key]
 if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or value<=0:raise ValueError(f'{key} must be finite and positive')
limits={'wheelbase_m':(1.6,2.2),'track_m':(1.25,1.6),'wheel_radius_front_m':(.4,.55),'wheel_radius_rear_m':(.5,.65),'shaft_length_m':(1.8,2.6),'steering_limit_deg':(1,12)}
for key,(low,high) in limits.items():
 if not low<=params[key]<=high:raise ValueError(f'{key} outside supported study envelope {low}..{high}')
if params.get('body_envelope_m') != [1.20,2.20]:raise ValueError('body_envelope_m describes fixed study furniture; only [1.2,2.2] supported')
if params['shaft_inner_spacing_tip_m'] != .773:raise ValueError('shaft tip spacing is fixed at .773m in this study')
WB=params['wheelbase_m'];TRACK=params['track_m'];RF=params['wheel_radius_front_m'];RR=params['wheel_radius_rear_m'];SHAFT=params['shaft_length_m']
nodes=[]; meshes=[]; access=[]; views=[]; binary=bytearray(); tris=0
materials=[]
for name,color,metal,rough in [('black_lacquer',[.035,.045,.05,1],.1,.32),('varnished_wood',[.26,.12,.045,1],0,.4),('upholstery',[.16,.055,.035,1],0,.86),('brass',[.55,.32,.07,1],.8,.28),('iron',[.075,.08,.085,1],.8,.45),('lamp_glass',[.75,.64,.38,1],.1,.2)]: materials.append({'name':name,'pbrMetallicRoughness':{'baseColorFactor':color,'metallicFactor':metal,'roughnessFactor':rough}})
def node(name,parent=None,t=(0,0,0),rotation=None):
 n={'name':name,'translation':list(t),'children':[]};
 if rotation:n['rotation']=rotation
 i=len(nodes);nodes.append(n)
 if parent is not None:nodes[parent]['children'].append(i)
 return i
def geom(name,parent,vertices,faces,mat,t=(0,0,0),rotation=None):
 global tris
 pos=[];norm=[]
 for face in faces:
  for j in range(1,len(face)-1):
   a,b,c=[vertices[k] for k in (face[0],face[j],face[j+1])];u=[b[k]-a[k] for k in range(3)];v=[c[k]-a[k] for k in range(3)];n=[u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]];l=math.sqrt(sum(q*q for q in n));n=[q/l for q in n] if l else [0,1,0]
   pos.extend(a+b+c);norm.extend(n*3);tris+=1
 def buf(values):
  off=len(binary);binary.extend(struct.pack('<%sf'%len(values),*values));vi=len(views);views.append({'buffer':0,'byteOffset':off,'byteLength':len(values)*4,'target':34962});ai=len(access); access.append({'bufferView':vi,'componentType':5126,'count':len(values)//3,'type':'VEC3','min':[min(values[k::3]) for k in range(3)],'max':[max(values[k::3]) for k in range(3)]});return ai
 a=buf(pos);b=buf(norm);mi=len(meshes);meshes.append({'name':name,'primitives':[{'attributes':{'POSITION':a,'NORMAL':b},'material':mat}]});i=node(name,parent,t,rotation);nodes[i]['mesh']=mi;return i
def box(name,parent,size,t,mat=0,rx=0):
 x,y,z=[v/2 for v in size];vs=[[-x,-y,-z],[x,-y,-z],[x,y,-z],[-x,y,-z],[-x,-y,z],[x,-y,z],[x,y,z],[-x,y,z]];fs=[[0,3,2,1],[4,5,6,7],[0,4,7,3],[1,2,6,5],[3,7,6,2],[0,1,5,4]];return geom(name,parent,vs,fs,mat,t,[math.sin(rx/2),0,0,math.cos(rx/2)] if rx else None)
def ring(name,parent,outer,inner,width,mat):
 vs=[];fs=[];N=48
 for x,r in [(-width/2,outer),(width/2,outer),(-width/2,inner),(width/2,inner)]:
  for i in range(N):a=2*math.pi*i/N;vs.append([x,r*math.cos(a),r*math.sin(a)])
 for i in range(N):
  j=(i+1)%N
  fs.extend([[i,j,N+j,N+i],[2*N+j,2*N+i,3*N+i,3*N+j],[j,i,2*N+i,2*N+j],[N+i,N+j,3*N+j,3*N+i]])
 return geom(name,parent,vs,fs,mat)
# All proportions are original engineering choices; no image-derived geometry.
def beam(name,parent,a,b,width,mat=4):
 d=[b[k]-a[k] for k in range(3)];length=math.sqrt(sum(v*v for v in d));u=[v/length for v in d];ref=[0,1,0] if abs(u[1])<.9 else [1,0,0];v=[u[1]*ref[2]-u[2]*ref[1],u[2]*ref[0]-u[0]*ref[2],u[0]*ref[1]-u[1]*ref[0]];l=math.sqrt(sum(x*x for x in v));v=[x/l*width/2 for x in v];q=[u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]];vs=[]
 for p in [a,b]:
  for x,y in [(-1,-1),(1,-1),(1,1),(-1,1)]:vs.append([p[k]+x*v[k]+y*q[k] for k in range(3)])
 return geom(name,parent,vs,[[0,3,2,1],[4,5,6,7],[0,4,7,3],[1,2,6,5],[3,7,6,2],[0,1,5,4]],mat)
root=node('vehicle_root');body=node('vehicle_body',root)
# Tapered passenger tub: rear/body flare toward armrest, open front footwell.
box('floor',body,(1.10,.08,2.20),(0,.59,0),1)
for side in [-1,1]:
 x=side*.57
 vs=[[x*.87,.63,-1.08],[x*.87,.63,.25],[x,1.22,.15],[x,1.30,-1.00],[x+side*.045,.63,-1.08],[x+side*.045,.63,.25],[x+side*.045,1.22,.15],[x+side*.045,1.30,-1.00]]
 geom('shaped_body_side_'+str(side),body,vs,[[0,3,2,1],[4,5,6,7],[0,4,7,3],[1,2,6,5],[3,7,6,2],[0,1,5,4]],0)
 beam('armrest_'+str(side),body,(x,1.31,-1),(x,1.23,.16),.045,1)
 box('step_'+str(side),body,(.25,.035,.45),(side*.73,.35,.35),4)
 for z in [.15,.55]:beam('step_bracket',body,(side*.48,.59,z),(side*.73,.35,z),.025)
 # Curved wheel guards, separated from wheels.
 for k in range(18):
  a=math.pi*(.06+.88*k/18);b=math.pi*(.06+.88*(k+1)/18)
  beam('rear_mudguard',body,(side*.70,.55+.61*math.sin(a),-.95+.61*math.cos(a)),(side*.70,.55+.61*math.sin(b),-.95+.61*math.cos(b)),.055,0)
box('rear_panel',body,(1.16,.64,.06),(0,.97,-1.04),0)
box('passenger_cushion',body,(1.00,.13,.45),(0,1.00,-.52),2)
box('passenger_back_cushion',body,(1.00,.42,.09),(0,1.25,-.84),2,rx=-.10)
for x in [-.33,0,.33]:box('cushion_seam',body,(.009,.003,.40),(x,1.067,-.52),1)
# Elevated driver perch and forward footboard.
for x in [-.37,.37]:beam('driver_seat_support',body,(x,.65,.58),(x,1.21,.64),.045)
box('driver_seat',body,(.92,.11,.40),(0,1.25,.60),2)
box('driver_back',body,(.92,.22,.06),(0,1.40,.39),0)
box('driver_footboard',body,(.90,.04,.35),(0,.80,1.00),1)
for x in [-.54,.54]:
 beam('lamp_stalk',body,(x,.72,.87),(x,1.38,.87),.022,3)
 box('lamp_glass',body,(.12,.17,.12),(x,1.40,.87),5)
 for y in [1.30,1.50]:box('lamp_cap',body,(.15,.035,.15),(x,y,.87),3)
# Running gear, articulated front turntable, and visible multi-leaf springs.
rear=node('vehicle_running_gear_rear',root,t=(0,RR,-WB/2));front=node('vehicle_steer_front',root,t=(0,RF,WB/2))
for name,parent in [('rear',rear),('front',front)]:box(name+'_axle',parent,(1.56,.055,.06),(0,0,0),4)
box('longitudinal_reach',root,(.07,.07,1.90),(0,.40,0),4)
turn=node('turntable',front);ring('kingpin_bearing',turn,.20,.12,.035,4)
nodes[turn]['rotation']=[0,0,math.sin(math.pi/4),math.cos(math.pi/4)]
box('kingpin',front,(.035,.23,.035),(0,.10,0),4)
for z,r in [(-.95,.55),(.95,.45)]:
 for x in [-.43,.43]:
  for layer in range(4):
   extent=.39-layer*.06
   for k in range(8):
    a=-extent+2*extent*k/8;b=-extent+2*extent*(k+1)/8
    beam('leaf_spring',root,(x,r+.075+layer*.012+.13*(a/.39)**2,z+a),(x,r+.075+layer*.012+.13*(b/.39)**2,z+b),.022,4)
  beam('spring_hanger',root,(x,r+.20,z-.39),(x,.64,z-.39),.025)
  beam('spring_hanger',root,(x,r+.20,z+.39),(x,.64,z+.39),.025)
for parent,r,label in [(rear,RR,'rear'),(front,RF,'front')]:
 for s,side in [(1,'left'),(-1,'right')]:
  w=node(f'vehicle_wheel_{label}_{side}',parent,t=(s*TRACK/2,0,0));ring('iron_tyre',w,r,r-.012,.045,4);ring('felloe',w,r-.012,r-.046,.042,1);ring('hub',w,.075,.012,.18,0)
  for k in range(14):
   a=k*math.tau/14;rr=(r-.046+.06)/2;box('spoke',w,(.025,r-.11,.025),(0,rr*math.cos(a),rr*math.sin(a)),1,rx=a)
  cap=node('hub_cap',w,t=(s*.10,0,0));ring('brass_cap',cap,.057,.01,.018,3)
draw=node('vehicle_drawgear',front)
# Shafts rise toward single-horse flank; forward ends are +3.15 from root.
for s in [-1,1]:
 for a,b in [((s*.48,.04,.0),(s*.46,.23,.9)),((s*.46,.23,.9),(s*.405,.30,SHAFT))]:beam('shaft',draw,a,b,.037,1)
 beam('shaft_tip',draw,(s*.405,.30,SHAFT-.10),(s*.405,.30,SHAFT),.043,3)
node('vehicle_hitch_single',draw,t=(0,.30,SHAFT))
for name,t in [('vehicle_seat_driver',(0,1.31,.60)),('vehicle_seat_passenger_01',(.25,1.07,-.52)),('vehicle_seat_passenger_02',(-.25,1.07,-.52)),('vehicle_board_left',(.85,.35,.35)),('vehicle_board_right',(-.85,.35,.35)),('vehicle_camera_ride',(0,1.80,-.45))]:node(name,body,t=t)
node('vehicle_collision',root)
# Merge original surface primitives by material within each articulated frame.
import numpy as np
oldnodes=nodes;oldmeshes=meshes;oldaccess=access;oldviews=views;oldbinary=binary
parents={c:i for i,n in enumerate(nodes) for c in n['children']}
frames={i for i,n in enumerate(nodes) if n['name'] in ['vehicle_root','vehicle_body','vehicle_running_gear_rear','vehicle_steer_front','vehicle_drawgear'] or n['name'].startswith('vehicle_wheel_')}
def local(n):
 m=np.eye(4);x,y,z,w=n.get('rotation',[0,0,0,1]);m[:3,:3]=[[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],[2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],[2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]];m[:3,3]=n['translation'];return m
def values(ai):
 a=oldaccess[ai];v=oldviews[a['bufferView']];return np.array(struct.unpack_from('<%sf'%(a['count']*3),oldbinary,v['byteOffset'])).reshape(-1,3)
batches={}
for i,n in enumerate(oldnodes):
 if 'mesh' not in n:continue
 j=i;m=np.eye(4)
 while j not in frames:m=local(oldnodes[j])@m;j=parents[j]
 for prim in oldmeshes[n['mesh']]['primitives']:
  vs=values(prim['attributes']['POSITION']);vs=vs@m[:3,:3].T+m[:3,3];key=(j,prim['material']);batches.setdefault(key,[]).extend(vs.tolist())
# Keep pivots/socket transforms, drop original surface nodes.
keep=[i for i,n in enumerate(oldnodes) if 'mesh' not in n];mapping={j:i for i,j in enumerate(keep)}
nodes=[{**oldnodes[j],'children':[mapping[c] for c in oldnodes[j]['children'] if c in mapping]} for j in keep];root=mapping[root]
meshes=[];access=[];views=[];binary=bytearray();tris=0
for (frame,mat),vs in batches.items():geom('surface_'+str(frame)+'_'+str(mat),mapping[frame],vs,[list(range(i,i+3)) for i in range(0,len(vs),3)],mat)
sidecar={'asset_id':'carriage_c01_study','revision':1,'units':'m','up_axis':'+Y','forward_axis':'+Z','root_datum':'ground midpoint between axles','status':'original engineering study; unverified historical subtype; no photographic quality claim','scene_eligibility':'1904 development study only; not 1835 deployment','parameters':params,'wheel_roll_axis':'+X','wheel_roll_sign_forward':1,'socket_policy':'proposed empty boarding/seat/hitch transforms; no occupant or harness validated','license':'GPL-3.0-or-later','source_attributes':[{'attributes':'all geometry, proportions, materials','tier':'reconstructed','basis':'vehicle-master-spec.md engineering envelope; independently authored, no source image tracing','source_ids':[]}],'liberties':['Original open carriage family study, not a named manufacturer or owner replica','Spring forms, bodywork, brass lamps and upholstery are unmeasured engineering approximations','No brake, reins, harness, horse, doors, cloth hood or physics','Steering bound provisional; swept collision and coupling remain integration gates'],'statistics':{'triangles':tris,'meshes':len(meshes),'nodes':len(nodes)}}

for exported_node in nodes:
 if not exported_node.get('children'):exported_node.pop('children',None)
g={'asset':{'version':'2.0','generator':'Original C01 Python geometry','copyright':'GPL-3.0-or-later'},'scene':0,'scenes':[{'nodes':[root]}],'nodes':nodes,'meshes':meshes,'materials':materials,'accessors':access,'bufferViews':views,'buffers':[{'byteLength':len(binary)}],'extras':sidecar}
j=json.dumps(g,separators=(',',':')).encode();j+=b' '*((-len(j))%4);binary+=b'\0'*((-len(binary))%4);glb=struct.pack('<III',0x46546c67,2,12+8+len(j)+8+len(binary))+struct.pack('<II',len(j),0x4e4f534a)+j+struct.pack('<II',len(binary),0x004e4942)+binary
(P/'carriage-c01.glb').write_bytes(glb);(P/'carriage-c01.json').write_text(json.dumps(sidecar,indent=2)+'\n');(P/'parameters.json').write_text(json.dumps(params,indent=2)+'\n');print(json.dumps({**sidecar['statistics'],'bytes':len(glb)}))
