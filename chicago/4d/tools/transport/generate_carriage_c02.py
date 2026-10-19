#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
import json,math,struct,pathlib
import argparse
cli=argparse.ArgumentParser();cli.add_argument('--parameters',type=pathlib.Path,default=pathlib.Path(__file__).resolve().parents[2]/'data/transport/studies/carriage-c02.json');cli.add_argument('--output-dir',type=pathlib.Path,default=pathlib.Path(__file__).resolve().parents[2]/'renderers/web/transport/carriage-c02');cli.add_argument('--door-angle-deg',type=float,default=0);args=cli.parse_args();P=args.output_dir;P.mkdir(parents=True,exist_ok=True)
params=json.loads(args.parameters.read_text())
# Reject malformed dimensional inputs rather than emitting invalid glTF.
for key in ['wheelbase_m','track_m','wheel_radius_front_m','wheel_radius_rear_m','shaft_length_m','shaft_inner_spacing_tip_m','steering_limit_deg']:
 value=params[key]
 if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or value<=0:raise ValueError(f'{key} must be finite and positive')
limits={'wheelbase_m':(1.6,2.2),'track_m':(1.25,1.6),'wheel_radius_front_m':(.4,.55),'wheel_radius_rear_m':(.5,.65),'shaft_length_m':(1.8,2.6),'steering_limit_deg':(1,12)}
for key,(low,high) in limits.items():
 if not low<=params[key]<=high:raise ValueError(f'{key} outside supported study envelope {low}..{high}')
if params.get('cabin_envelope_m') != [1.32,1.70,1.44]:raise ValueError('cabin_envelope_m is the fixed original C02 study envelope')
if params['shaft_inner_spacing_tip_m'] != .773:raise ValueError('shaft tip spacing is fixed at .773m in this study')
WB=params['wheelbase_m'];TRACK=params['track_m'];RF=params['wheel_radius_front_m'];RR=params['wheel_radius_rear_m'];SHAFT=params['shaft_length_m']
nodes=[]; meshes=[]; access=[]; views=[]; binary=bytearray(); tris=0
materials=[]
for name,color,metal,rough in [('black_lacquer',[.035,.045,.05,1],.1,.32),('varnished_wood',[.26,.12,.045,1],0,.4),('upholstery',[.16,.055,.035,1],0,.86),('brass',[.55,.32,.07,1],.8,.28),('iron',[.075,.08,.085,1],.8,.45),('lamp_glass',[.35,.34,.29,1],.1,.2),('provisional_dark_glazing',[.035,.055,.06,1],0,.18)]: materials.append({'name':name,'pbrMetallicRoughness':{'baseColorFactor':color,'metallicFactor':metal,'roughnessFactor':rough}})
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
def chamfered_rail(name,parent,size,t,mat=0,bevel=.008):
 x,y,z=[v/2 for v in size];b=min(bevel,x*.45,y*.45)
 section=[(-x+b,-y),(x-b,-y),(x,-y+b),(x,y-b),(x-b,y),(-x+b,y),(-x,y-b),(-x,-y+b)]
 vs=[[a,c,d] for d in [-z,z] for a,c in section]
 fs=[list(range(7,-1,-1)),list(range(8,16))]+[[i,(i+1)%8,(i+1)%8+8,i+8] for i in range(8)]
 return geom(name,parent,vs,fs,mat,t)
def ring(name,parent,outer,inner,width,mat,segments=48):
 vs=[];fs=[];N=segments
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
DOOR=params.get('operable_door_study',False)
if not isinstance(DOOR,bool):raise ValueError('operable_door_study must be boolean')
if not math.isfinite(args.door_angle_deg) or not 0<=args.door_angle_deg<=70:raise ValueError('door angle must be finite0..70degrees')
if args.door_angle_deg and not DOOR:raise ValueError('door angle requires explicit door study')
door=node('vehicle_door_left',body,t=(.655,.82,-.28),rotation=[0,math.sin(math.radians(args.door_angle_deg)/2),0,math.cos(math.radians(args.door_angle_deg)/2)]) if DOOR else None
# C02: separate enclosed town-carriage silhouette, not a diagnosed subtype.
# Photograph supports only coarse dark roofed cell and exposed running gear.
# ALL dimensions, glass/door divisions and furniture below are reconstructed.
box('cabin_floor',body,(1.16,.08,1.62),(0,.74,-.25),1)
# Sloping lower side panels narrow toward the exposed underbody.
for side in [-1,1]:
 x=side
 vs=[[x*.50,.78,-1.04],[x*.50,.78,.50],[x*.60,1.30,.50],[x*.60,1.30,-1.04],[x*.54,.78,-1.04],[x*.54,.78,.50],[x*.62,1.30,.50],[x*.62,1.30,-1.04]]
 faces=[[0,3,2,1],[4,5,6,7],[0,4,7,3],[1,2,6,5],[3,7,6,2],[0,1,5,4]]
 center=[sum(v[k] for v in vs)/len(vs) for k in range(3)]
 for face in faces:
  p,q,r=[vs[i] for i in face[:3]];u=[q[k]-p[k] for k in range(3)];v=[r[k]-p[k] for k in range(3)];normal=[u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]];d=[sum(vs[i][k] for i in face)/len(face)-center[k] for k in range(3)]
  if sum(a*b for a,b in zip(normal,d))<0:face.reverse()
 if DOOR and side==1:
  # Original lower fixed wall retains the full silhouette but stops beneath leaf.
  for label,zlo,zhi in [('rear',-1.04,-.32),('front',.47,.50)]:
   lowvs=[[v[0],v[1],min(zhi,max(zlo,v[2]))] for v in vs]
   geom('cabin_lower_fixed_door_'+label,body,lowvs,faces,0)
  box('cabin_lower_fixed_door_sill',body,(.07,.025,.79),(.60,.79,.065),0)
  # Leaf lower panel and fixed end jambs fill the former upper lower-wall band.
  box('door_lower_panel',door,(.045,.52,.71),(-.055,.26,.355),0)
  for z in [-.38,.51]:box('cabin_door_jamb_lower_'+str(z),body,(.07,.22,.04),(.60,1.23,z),0)
 else:geom('cabin_lower_side_'+str(side),body,vs,faces,0)
 # Closed independent window/pillar treatment, not read from tiny source pixels.
 if not(DOOR and side==1):box('waist_rail_'+str(side),body,(.055,.055,1.62),(side*.60,1.325,-.25),0)
 if DOOR and side==1:
  box('door_glazing',door,(.025,.54,.65),(-.055,.815,.355),6)
  for z in [0,.71]:box('door_vertical_stile',door,(.065,1.08,.065),(-.055,.54,z),0)
  for y in [.025,.535,1.075]:chamfered_rail('door_horizontal_rail',door,(.065,.065,.75),(-.055,y,.355),0)
  box('side_glazing_fixed_rear',body,(.025,.66,.665),(.595,1.67,-.655),6)
  chamfered_rail('window_fixed_rear_waist',body,(.075,.08,.69),(.60,1.33,-.675),0)
  box('cabin_door_transom',body,(.065,.025,.79),(.60,1.94,.065),0)
  for z in [-.335,.49]:box('cabin_window_jamb_trim',body,(.065,.61,.025),(.60,1.645,z),0)
  # Original engineering hinge: two fixed knuckles alternate around one moving
  # knuckle. Pin radius5mm/bore6mm leaves1mm radial running gap, no contact waiver.
  for hy in [1.30,1.80]:
   for dy in [-.04,.04]:
    kn=node('door_fixed_knuckle',body,t=(.655,hy+dy,-.28),rotation=[0,0,math.sin(math.pi/4),math.cos(math.pi/4)])
    ring('hinge_fixed_knuckle',kn,.014,.006,.03,3,16)
    beam('hinge_fixed_arm',body,(.655,hy+dy,-.28),(.655,hy+dy,-.36),.008,3)
    beam('hinge_fixed_arm_rear',body,(.655,hy+dy,-.36),(.60,hy+dy,-.36),.008,3)
   pin=node('door_pin_frame',body,t=(.655,hy,-.28),rotation=[0,0,math.sin(math.pi/4),math.cos(math.pi/4)])
   ring('hinge_pin_tube',pin,.005,.001,.13,3,16)
   kn=node('door_moving_knuckle',door,t=(0,hy-.82,0),rotation=[0,0,math.sin(math.pi/4),math.cos(math.pi/4)])
   ring('hinge_moving_knuckle',kn,.014,.006,.03,3,16)
   beam('hinge_moving_arm',door,(-.0108,hy-.82,.0132),(-.055,hy-.82,.055),.008,3)
  box('door_handle',door,(.055,.018,.09),(.005,.70,.62),3)
  # Wider tread and two supports remain stationary below the swing.
  box('door_step_tread',body,(.34,.055,.62),(.80,.38,-.25),4)
  for z in [-.48,-.02]:beam('door_step_support',body,(.49,.74,z),(.80,.38,z),.032,4)
 else:box('side_glazing_'+str(side),body,(.025,.66,1.50),(side*.595,1.67,-.25),6)
 chamfered_rail('window_roof_rail_'+str(side),body,(.075,.085,1.62),(side*.595,1.995,-.25),0)
 if not(DOOR and side==1):chamfered_rail('window_sill_rail_'+str(side),body,(.075,.065,1.62),(side*.595,1.34,-.25),0)
 for z in [-1.025,.525]:box('cabin_corner_pillar_'+str(side)+'_'+str(z),body,(.075,.75,.075),(side*.595,1.665,z),0)
 if not(DOOR and side==1):box('window_lower_frame_'+str(side),body,(.045,.025,1.52),(side*.612,1.36,-.25),0)
 if not(DOOR and side==1):box('window_upper_frame_'+str(side),body,(.045,.025,1.52),(side*.612,1.98,-.25),0)
 # No hinges, handles or working door falsely inferred from the photograph.
 if not(DOOR and side==1):box('step_'+str(side),body,(.24,.04,.44),(side*.76,.36,-.12),4)
 for z in [-.29,.05]:beam('step_bracket_'+str(side),body,(side*.49,.74,z),(side*.76,.36,z),.025,4)
 for k in range(18):
  a=math.pi*(.06+.88*k/18);b=math.pi*(.06+.88*(k+1)/18)
  beam('rear_mudguard',body,(side*.70,RR+.61*math.sin(a),-WB/2+.61*math.cos(a)),(side*.70,RR+.61*math.sin(b),-WB/2+.61*math.cos(b)),.045,0)
# Rear and front panel frames with provisional dark glass rather than false detailed doors.
for label,z in [('rear',-1.045),('front',.535)]:
 box(label+'_lower_panel',body,(1.18,.55,.055),(0,1.055,z),0)
 box(label+'_window_panel',body,(1.16,.60,.03),(0,1.64,z),0)
 box(label+'_dark_glass',body,(.58,.38,.012),(0,1.68,z+(-.023 if label=='rear' else .023)),6)
 box(label+'_upper_header',body,(1.22,.09,.065),(0,1.98,z),0)
# Shallow crowned closed roof, explicitly invented contour/thickness.
profile=[(-.66,2.025),(-.53,2.075),(-.30,2.122),(0,2.14),(.30,2.122),(.53,2.075),(.66,2.025)]
# Continuous invented crown fascia seals the former end gap to roof underside.
# Not an inferred historical construction or door/window arrangement.
for label,z in [('rear',-1.045),('front',.535)]:
 top=[(max(-.62,min(.62,x)),y-.044) for x,y in profile]
 # Retain monotonic x and close a thin solid between upper panel and crown.
 cross=[(-.62,1.92),(.62,1.92)]+list(reversed(top))
 vs_f=[[x,y,z+d] for d in [-.033,.033] for x,y in cross];n=len(cross)
 fs_f=[list(range(n-1,-1,-1)),list(range(n,2*n))]+[[i,(i+1)%n,(i+1)%n+n,i+n] for i in range(n)]
 geom(label+'_upper_crown_fascia',body,vs_f,fs_f,0)
vs=[]
for z in [-1.10,.60]:
 for depth in [0,-.045]:
  for x,y in profile:vs.append([x,y+depth,z])
N=len(profile);faces=[]
for k in range(N-1):faces.extend([[k,k+1,2*N+k+1,2*N+k],[N+k+1,N+k,3*N+k,3*N+k+1],[k,N+k,N+k+1,k+1],[2*N+k+1,3*N+k+1,3*N+k,2*N+k]])
faces.extend([[0,2*N,3*N,N],[N-1,2*N-1,4*N-1,3*N-1]])
# Explicit consistent winding: top/up, underside/down, rear/front/endcaps outward.
for face in faces:face.reverse()
geom('crowned_cabin_roof',body,vs,faces,0)
# Empty internal bench and external perch are original fit candidates, not sourced furniture.
box('passenger_bench_base',body,(1.00,.25,.43),(0,.905,-.68),0)
box('passenger_cushion',body,(1.00,.12,.43),(0,1.09,-.68),2)
box('passenger_back',body,(1.00,.45,.06),(0,1.39,-.94),2)
for x in [-.37,.37]:beam('driver_perch_support',body,(x,.74,.79),(x,1.22,.86),.045,4)
box('driver_seat',body,(.92,.11,.38),(0,1.26,.86),2)
box('driver_back',body,(.92,.20,.055),(0,1.40,.66),0)
box('driver_footboard',body,(.90,.04,.40),(0,.83,1.20),1)
for x in [-.53,.53]:
 beam('lamp_bracket',body,(x,.90,.76),(x,1.45,.76),.020,4)
 box('lamp_body',body,(.11,.15,.11),(x,1.48,.76),5)
 for y in [1.39,1.57]:box('lamp_cap',body,(.14,.025,.14),(x,y,.76),4)
# Running gear, articulated front turntable, and visible multi-leaf springs.
rear=node('vehicle_running_gear_rear',root,t=(0,RR,-WB/2));front=node('vehicle_steer_front',root,t=(0,RF,WB/2))
for name,parent in [('rear',rear),('front',front)]:box(name+'_axle',parent,(1.56,.055,.06),(0,0,0),4)
box('longitudinal_reach',root,(.07,.07,1.90),(0,.40,0),4)
turn=node('turntable',front);ring('kingpin_bearing',turn,.20,.12,.035,4)
nodes[turn]['rotation']=[0,0,math.sin(math.pi/4),math.cos(math.pi/4)]
box('kingpin',front,(.035,.23,.035),(0,.10,0),4)
for z,r in [(-WB/2,RR),(WB/2,RF)]:
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
for name,t in [('vehicle_seat_driver',(0,1.32,.86)),('vehicle_seat_passenger_01',(.24,1.155,-.68)),('vehicle_seat_passenger_02',(-.24,1.155,-.68)),('vehicle_board_left',(.85,.38,-.12)),('vehicle_board_right',(-.85,.38,-.12)),('vehicle_camera_ride',(0,1.82,-.60))]:node(name,body,t=t)
node('vehicle_collision',root)
# Merge original surface primitives by material within each articulated frame.
import numpy as np
oldnodes=nodes;oldmeshes=meshes;oldaccess=access;oldviews=views;oldbinary=binary
parents={c:i for i,n in enumerate(nodes) for c in n['children']}
frames={i for i,n in enumerate(nodes) if n['name']=='vehicle_door_left' or n['name'] in ['vehicle_root','vehicle_body','vehicle_running_gear_rear','vehicle_steer_front','vehicle_drawgear'] or n['name'].startswith('vehicle_wheel_')}
def local(n):
 m=np.eye(4);x,y,z,w=n.get('rotation',[0,0,0,1]);m[:3,:3]=[[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],[2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],[2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]];m[:3,3]=n['translation'];return m
def values(ai):
 a=oldaccess[ai];v=oldviews[a['bufferView']];return np.array(struct.unpack_from('<%sf'%(a['count']*3),oldbinary,v['byteOffset'])).reshape(-1,3)
batches={};cabin_components={}
for i,n in enumerate(oldnodes):
 if 'mesh' not in n:continue
 j=i;m=np.eye(4)
 while j not in frames:m=local(oldnodes[j])@m;j=parents[j]
 for prim in oldmeshes[n['mesh']]['primitives']:
  vs=values(prim['attributes']['POSITION']);vs=vs@m[:3,:3].T+m[:3,3];key=(j,prim['material']);
  if n['name'].startswith(('cabin_','crowned_cabin_','waist_rail_','side_glazing_','window_','rear_lower_','rear_window_','rear_dark_','rear_upper_','front_lower_','front_window_','front_dark_','front_upper_')):cabin_components[n['name']]={'min_m':vs.min(axis=0).tolist(),'max_m':vs.max(axis=0).tolist()}
  batches.setdefault(key,[]).extend(vs.tolist())
# Keep pivots/socket transforms, drop original surface nodes.
keep=[i for i,n in enumerate(oldnodes) if 'mesh' not in n];mapping={j:i for i,j in enumerate(keep)}
nodes=[{**oldnodes[j],'children':[mapping[c] for c in oldnodes[j]['children'] if c in mapping]} for j in keep];root=mapping[root]
meshes=[];access=[];views=[];binary=bytearray();tris=0
for (frame,mat),vs in batches.items():geom('surface_'+str(frame)+'_'+str(mat),mapping[frame],vs,[list(range(i,i+3)) for i in range(0,len(vs),3)],mat)
sidecar={'asset_id':'carriage_c02_enclosed_study','revision':2,'units':'m','up_axis':'+Y','forward_axis':'+Z','root_datum':'ground midpoint between axles','status':'original engineering study; unverified historical subtype; no photographic quality claim','scene_eligibility':'1904 development study only; not 1835 deployment','parameters':params,'wheel_roll_axis':'+X','wheel_roll_sign_forward':1,'socket_policy':'new C02 empty boarding/seat/hitch transforms; no door traversal, occupant, gear fit or camera validated; do not reuse C01fit','license':'GPL-3.0-or-later','source_attributes':[{'attributes':'all geometry, proportions, materials','tier':'reconstructed','basis':'vehicle-master-spec.md engineering envelope; independently authored, no source image tracing','source_ids':[]}],'liberties':['Separate enclosed roofed town-carriage silhouette study, not a named owner, manufacturer or diagnosed subtype','Spring forms, bodywork, simple lamps and upholstery are unmeasured engineering approximations','No working door/hinge, brake, horse/team, rider, reins, harness or physics; cabin openings and furniture are unproven independent reconstruction','Steering bound provisional; swept collision and coupling remain integration gates'],'statistics':{'triangles':tris,'meshes':len(meshes),'nodes':len(nodes)}}

sidecar['reference_scope']={'reference_record_id':'a16-pullman-det-4a08065','registry':'prairie_1904_v1/research/images/stream-1600-1700.json','catalog_url':'https://www.loc.gov/item/2016801921/','date_bounds':[1890,1901],'rights':'No known restrictions on publication, existing catalog record; not an unconditional license','actually_viewed':True,'used':'Coarse roofed dark cabin and open underbody silhouette only; no pixels/textures/tracing or physical dimensions extracted','unresolved':['vehicle ownership','manufacturer/subtype','door/window layout','wheel count/radii from photograph','horses/team','lamp construction','absolute dimensions'],'scene_eligibility':'1904 development-only period analogy; no specific carriage presence/date/ownership inferred'}
sidecar['boarding_enabled']=False
if DOOR:sidecar['door_study']={'node':'vehicle_door_left','hinge_axis':'+Y','closed_angle_deg':0,'open_angle_deg':70,'exported_angle_deg':args.door_angle_deg,'hinge_parent_translation_m':[.655,.82,-.28],'status':'original reconstructed rigid door/hinge/step layout; no sourced design or occupant acceptance','production_enabled':False}
if DOOR:
 # Preserve the pre-door PROJECT source wording as history, never as a period quotation.
 sidecar['pre_door_source_scope_history']={
  'quotation':sidecar['liberties'][2],
  'quotation_origin':'Original project C02 pre-operable-door generator sidecar; not historical source text',
  'applies_to':'Earlier C02 branch without reconstructed operable door',
  'superseded_by':'operable_door_study=true adds original rigid door/hinge geometry and endpoint transforms only',
  'not_attested':'historical door hardware, dimensions, ownership, forces, passenger passage and photographic quality'}
 sidecar['liberties'][2]='The enabled operable-door study adds independently reconstructed rigid door/hinge geometry and closed/open endpoint transforms. No brake, horse/team, rider, reins, fitted harness, hinge forces or passenger passage is supplied; cabin openings and furniture remain unverified independent reconstruction.'
sidecar['enclosure_repair']={'status':'independently reconstructed continuous roof rails, sill rails, full side panes and crown fascia; historical layout unproven','side_pane_y_bounds_m':[1.34,2.0],'side_pane_z_bounds_m':[-1.0,.5],'roof_rail_y_bounds_m':[1.9525,2.0375],'sill_rail_y_bounds_m':[1.3075,1.3725],'fascia_lower_y_m':1.92,'rail_edge_chamfer_m':.008}
sidecar['cabin_component_bounds']=cabin_components
sidecar['cabin_geometry_subset']='Cabin floor, sidewalls, pillars, glass/frame and roof; excludes steps, driverfurniture, lamps and runninggear'
sidecar['cabin_bounds_basis']='All dimensions, roof/window/seat/step construction independently reconstructed; fixed envelope, not measured photograph'

for exported_node in nodes:
 if not exported_node.get('children'):exported_node.pop('children',None)
g={'asset':{'version':'2.0','generator':'Original separate C02 Python geometry','copyright':'GPL-3.0-or-later'},'scene':0,'scenes':[{'nodes':[root]}],'nodes':nodes,'meshes':meshes,'materials':materials,'accessors':access,'bufferViews':views,'buffers':[{'byteLength':len(binary)}],'extras':sidecar}
j=json.dumps(g,separators=(',',':')).encode();j+=b' '*((-len(j))%4);binary+=b'\0'*((-len(binary))%4);glb=struct.pack('<III',0x46546c67,2,12+8+len(j)+8+len(binary))+struct.pack('<II',len(j),0x4e4f534a)+j+struct.pack('<II',len(binary),0x004e4942)+binary
(P/'carriage-c02.glb').write_bytes(glb);(P/'carriage-c02.json').write_text(json.dumps(sidecar,indent=2)+'\n');(P/'parameters.json').write_text(json.dumps(params,indent=2)+'\n');print(json.dumps({**sidecar['statistics'],'bytes':len(glb)}))
