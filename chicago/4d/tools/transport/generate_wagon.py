#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
# Original procedural prototype; reconstruction parameters follow kevinrhaas/chicago yard.js.
import json,math,struct,pathlib
import argparse
cli=argparse.ArgumentParser();cli.add_argument('--parameters',type=pathlib.Path,default=pathlib.Path(__file__).with_name('parameters.json'));cli.add_argument('--output-dir',type=pathlib.Path,default=pathlib.Path(__file__).parent);args=cli.parse_args()
P=args.output_dir;P.mkdir(parents=True,exist_ok=True)
params=json.loads(args.parameters.read_text())
L,W,H=params['body_m'];BED=params['bed_top_m'];RF=params['wheel_diameter_front_m']/2;RR=params['wheel_diameter_rear_m']/2;ZR,ZF=params['axle_stations_z_m'];HALFTRACK=params['wheel_center_track_m']/2;TL=params['tongue_length_m']
nodes=[]; meshes=[]; access=[]; views=[]; binary=bytearray(); tris=0
geometry=[]
materials=[]
for name,color,metal,rough in [('paint',[.23,.29,.20,1],0,.75),('timber',[.42,.26,.12,1],0,.85),('plank_a',[.50,.33,.18,1],0,.85),('plank_b',[.39,.24,.11,1],0,.87),('iron',[.12,.13,.12,1],.75,.65),('end_grain',[.30,.18,.08,1],0,.92)]: materials.append({'name':name,'pbrMetallicRoughness':{'baseColorFactor':color,'metallicFactor':metal,'roughnessFactor':rough}})
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
 i=node(name,parent,t,rotation);geometry.append((i,pos,norm,mat));return i

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
root=node('vehicle_root');body=node('vehicle_body',root)
# Individual floor planks, side courses and staves, with small visible board seams.
for i in range(8):box(f'floor_plank_{i:02}',body,(W/8-.003,.07,L),(-W/2+(i+.5)*W/8,(BED-.035),0),2+i%2)
for side in [-1,1]:
 for j in range(4):box(f'side_{side}_course_{j}',body,(.035,H/4-.003,L),(side*(W/2),BED+(j+.5)*H/4,0),2+j%2)
 for k,z in enumerate([f*L/3.05 for f in [-1.4,-.5,.5,1.4]]):
  box(f'stake_{side}_{k}',body,(.045,H+.11,.055),(side*(W/2+.03),(BED+H/2-.025),z),0)
  for y in [BED+.09,BED+H-.1]:box(f'stake_bolt_{side}_{k}_{y}',body,(.010,.017,.017),(side*(W/2+.057),y,z),4)
 box(f'top_rail_{side}',body,(.055,.04,L+.05),(side*(W/2),(BED+H+.01),0),0)
for z in [-(L/2),(L/2)]:
 for j in range(4):box(f'end_{z}_course_{j}',body,(W,H/4-.003,.035),(0,BED+(j+.5)*H/4,z),2+j%2)
# Rear running gear and box-bearing bolsters fixed in vehicle frame.
rear=node('vehicle_running_gear_rear',root,t=(0,RR,ZR));box('rear_axle',rear,(2*HALFTRACK+.14,.05,.05),(0,0,0),0)
for z in [ZR,ZF]:box('bolster_rear' if z<0 else 'bolster_front_fixed',root,(W+.12,BED-.035-(RR+.025),.11),(0,((BED-.035)+(RR+.025))/2,z),0)
box('reach',root,(.09,max(.03,RR-RF-.05),ZF-ZR+.18),(0,(RF+.025+RR-.025)/2,(ZF+ZR)/2-.09),0)
front=node('vehicle_steer_front',root,t=(0,RF,ZF));box('front_axle',front,(2*HALFTRACK+.14,.05,.05),(0,0,0),0)
for s in [-1,1]:box('hound_'+str(s),front,(.07,.15,.86),(s*.08,.10,-.02),0)
box('kingbolt',front,(.035,.44,.035),(0,.12,0),4)
for parent,r,label in [(rear,RR,'rear'),(front,RF,'front')]:
 for s,side in [(1,'left'),(-1,'right')]:
  w=node(f'vehicle_wheel_{label}_{side}',parent,t=(s*HALFTRACK,0,0));ring('iron_tyre_'+label+side,w,r,r-.018,.07,4);ring('wood_felloe_'+label+side,w,r-.018,r-.065,.062,1);ring('hub_'+label+side,w,.095,.018,.22,0)
  for k in range(12):
   a=k*math.tau/12;rr=(r-.07+.08)/2;box(f'spoke_{label}_{side}_{k}',w,(.035,r-.15,.032),(0,rr*math.cos(a),rr*math.sin(a)),1,rx=a)
  for x in [-.10,.10]:
   cap=node('hub_band_'+str(x),w,t=(x,0,0));ring('band',cap,.099,.085,.018,4)
# Pitchable tongue, integral to swivel gear, not a horizontal floating plank.
tongue=node('vehicle_tongue',front,t=(0,0,.35));box('tongue_timber',tongue,(.055,.055,TL),(0,0,TL/2),1)
for z in [.10,.30,TL-.10]:box('tongue_strap_'+str(z),tongue,(.062,.063,.025),(0,0,z),4)
hitch=node('vehicle_hitch_team',tongue,t=(0,0,TL));node('vehicle_hitch_single',front,t=(0,0,.35));node('vehicle_seat_driver',body,t=(0,1.15,1.10));node('vehicle_seat_passenger_01',body,t=(0,1.15,-.45));node('vehicle_board_left',body,t=(.85,0,.5));node('vehicle_board_right',body,t=(-.85,0,.5));node('vehicle_camera_ride',body,t=(0,1.8,.2));node('vehicle_collision',root)
# Merge by material inside each articulation frame, retaining wheel/steer/tongue pivots.
def rotate(v,q):
 x,y,z,w=q;vx,vy,vz=v;tx=2*(y*vz-z*vy);ty=2*(z*vx-x*vz);tz=2*(x*vy-y*vx)
 return [vx+w*tx+y*tz-z*ty,vy+w*ty+z*tx-x*tz,vz+w*tz+x*ty-y*tx]
parents={c:i for i,n in enumerate(nodes) for c in n['children']}
articulated={i for i,n in enumerate(nodes) if n['name'] in ['vehicle_root','vehicle_body','vehicle_running_gear_rear','vehicle_steer_front','vehicle_tongue'] or n['name'].startswith('vehicle_wheel_')}
batches={}
for index,pos,norm,material in geometry:
 chain=[];current=index
 while current not in articulated:
  chain.append(current);current=parents[current]
 key=(current,material);pp,nn=batches.setdefault(key,([],[]))
 for k in range(0,len(pos),3):
  point=pos[k:k+3];normal=norm[k:k+3]
  for transform in chain:
   n=nodes[transform];q=n.get('rotation',[0,0,0,1]);point=rotate(point,q);normal=rotate(normal,q);point=[v+t for v,t in zip(point,n['translation'])]
  pp.extend(point);nn.extend(normal)
def attribute(values):
 off=len(binary);binary.extend(struct.pack('<%sf'%len(values),*values));vi=len(views);views.append({'buffer':0,'byteOffset':off,'byteLength':len(values)*4,'target':34962});ai=len(access);access.append({'bufferView':vi,'componentType':5126,'count':len(values)//3,'type':'VEC3','min':[min(values[k::3]) for k in range(3)],'max':[max(values[k::3]) for k in range(3)]});return ai
for (frame,material),(pos,norm) in batches.items():
 mesh={'name':nodes[frame]['name']+'_'+materials[material]['name'],'primitives':[{'attributes':{'POSITION':attribute(pos),'NORMAL':attribute(norm)},'material':material}]};mi=len(meshes);meshes.append(mesh);i=node(mesh['name'],frame);nodes[i]['mesh']=mi
# Sockets represent proposed interfaces, NOT evidence for physical seats on farm wagon.
sidecar={'asset_id':'wagon_w01_prototype','status':'engineering prototype; not photographically matched','units':'m','forward_axis':'+Z','up_axis':'+Y','parameters':params,'wheel_radius_m':{'rear':RR,'front':RF},'steering_limit_deg':8,'socket_policy':'empty proposed transforms, not attested installed hardware or seating','license':'GPL-3.0-or-later','liberties':['All geometry and colors reconstructed, original procedural surfaces; no reference-photo pixels or tracing','No brake, suspension, horse, harness, seated humans, historical load or named owner','Steering limited to ±8 degrees for this box clearance; not historical limit','Tongue resting pitch optional; no hitch or load physics','Floor, bolsters, hounds, reach and kingbolt are engineering visual approximations'],'provenance':{'basis':'Existing declared reconstruction: kevinrhaas/chicago chicago/4d/renderers/web/js/yard.js and data/yard/town_trade_goods.json; vehicle-master-spec.md 2026-10-18','source_ids':[]},'statistics':{'triangles':tris,'meshes':len(meshes),'nodes':len(nodes)}}

# Discard surface placeholders left by material batching; retain sockets and pivots.
surface_nodes={entry[0] for entry in geometry}
keep=[i for i in range(len(nodes)) if i not in surface_nodes]
remap={old:new for new,old in enumerate(keep)}
nodes=[{**nodes[i], 'children':[remap[c] for c in nodes[i]['children'] if c in remap]} for i in keep]
root=remap[root]
sidecar['statistics']['nodes']=len(nodes)

for exported_node in nodes:
 if not exported_node.get('children'):exported_node.pop('children',None)
g={'asset':{'version':'2.0','generator':'Original W01 procedural Python generator','copyright':'GPL-3.0-or-later; kevinrhaas/chicago reconstruction parameters, original prototype geometry'},'scene':0,'scenes':[{'nodes':[root]}],'nodes':nodes,'meshes':meshes,'materials':materials,'accessors':access,'bufferViews':views,'buffers':[{'byteLength':len(binary)}],'extras':sidecar}
j=json.dumps(g,separators=(',',':')).encode();j+=b' '*((-len(j))%4);binary+=b'\0'*((-len(binary))%4);glb=struct.pack('<III',0x46546c67,2,12+8+len(j)+8+len(binary))+struct.pack('<II',len(j),0x4e4f534a)+j+struct.pack('<II',len(binary),0x004e4942)+binary
(P/'wagon-w01.glb').write_bytes(glb);(P/'wagon-w01.json').write_text(json.dumps(sidecar,indent=2)+'\n');print(json.dumps({**sidecar['statistics'],'bytes':len(glb)}))
