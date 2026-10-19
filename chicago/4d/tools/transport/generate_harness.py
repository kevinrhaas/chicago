# SPDX-License-Identifier: CC0-1.0
#!/usr/bin/env python3
"""Original parametric harness fixture: no photograph inputs or external geometry. Stdlib only."""
import json,math,pathlib,struct,argparse
parser=argparse.ArgumentParser();parser.add_argument('--parameters',type=pathlib.Path,required=True);parser.add_argument('--output-dir',type=pathlib.Path,required=True);args=parser.parse_args();P=args.output_dir;P.mkdir(parents=True,exist_ok=True)
p=json.loads(args.parameters.read_text())
d={'asset':{'version':'2.0','generator':'original modular breastcollar harness fixture'},'scene':0,'scenes':[{'nodes':[0]}],'nodes':[],'meshes':[],'materials':[],'accessors':[],'bufferViews':[],'buffers':[]}
bin=bytearray();stats={}
def vector(a,b):return [a[i]-b[i] for i in range(3)]
def cross(a,b):return [a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]]
def unit(a):
 n=math.sqrt(sum(v*v for v in a));return [v/n for v in a] if n>1e-9 else [1,0,0]
def accessor(rows,kind,component=5126):
 while len(bin)%4:bin.append(0)
 flat=[v for r in rows for v in (r if isinstance(r,(list,tuple)) else [r])];off=len(bin);bin.extend(struct.pack('<'+('f' if component==5126 else 'I')*len(flat),*flat));vi=len(d['bufferViews']);d['bufferViews'].append({'buffer':0,'byteOffset':off,'byteLength':len(bin)-off});a={'bufferView':vi,'componentType':component,'count':len(rows),'type':kind}
 if kind=='VEC3':a.update(min=[min(r[i] for r in rows) for i in range(3)],max=[max(r[i] for r in rows) for i in range(3)])
 if kind=='SCALAR':a.update(min=[min(rows)],max=[max(rows)])
 d['accessors'].append(a);return len(d['accessors'])-1
def material(name,c,metal=0,rough=.55):
 d['materials'].append({'name':name,'pbrMetallicRoughness':{'baseColorFactor':c+[1],'metallicFactor':metal,'roughnessFactor':rough}});return len(d['materials'])-1
leather=material('tack_leather',p['leather_linear_rgb']);nickel=material('tack_metal_nickel_reconstructed',p['metal_linear_rgb'],1,.27);stitch=material('tack_stitch_reconstructed',[.13,.10,.065],0,.85)
def node(name,parent=0,translation=None,extras=None,mesh=None):
 n={'name':name}
 if translation is not None:n['translation']=translation
 if extras:n['extras']=extras
 if mesh is not None:n['mesh']=mesh
 d['nodes'].append(n);i=len(d['nodes'])-1
 if i: d['nodes'][parent].setdefault('children',[]).append(i)
 return i
node('root',extras={'chicago4d_harness':{'version':'fixture_0.1','license':'CC0-1.0','grade':'reconstructed','not_production':True,'source':'John Moore 1891 catalog No1 text construction facts; no plate-derived geometry'}})
head=node('harness_head',translation=p['head_origin_m'],extras={'bind_to_horse_node':'head','binding_status':'rest_aligned_only'})
def mesh(name,vs,faces,ma,parent=0,extra=None):
 # Flat normals retain the visible thickness of rectangular straps.
 vv=[];nn=[]
 for f in faces:
  n=unit(cross(vector(vs[f[1]],vs[f[0]]),vector(vs[f[2]],vs[f[0]])))
  for k in f:vv.append(vs[k]);nn.append(n)
 mi=len(d['meshes']);d['meshes'].append({'name':name,'primitives':[{'attributes':{'POSITION':accessor(vv,'VEC3'),'NORMAL':accessor(nn,'VEC3')},'material':ma}]});stats[name]={'triangles':len(faces),'material':d['materials'][ma]['name']};return node(name,parent,mesh=mi,extras=extra or {'dimension_grade':'reconstructed'})
def strap(name,points,width=None,thick=None,parent=0,ma=leather,width_axis=(1,0,0),extra=None,surface_normals=None):
 w=width or p['strap_width_m'];t=thick or p['strap_thickness_m'];vs=[]
 for j,c in enumerate(points):
  tangent=unit(vector(points[min(len(points)-1,j+1)],points[max(0,j-1)]));side=unit(vector(width_axis,[tangent[k]*sum(width_axis[i]*tangent[i] for i in range(3)) for k in range(3)]));normal=unit(cross(tangent,side))
  if surface_normals:
   side=unit(cross(surface_normals[j],tangent))
   if side[1]<0:side=[-v for v in side]
   normal=unit(cross(tangent,side))
  for sw,st in [(-1,-1),(1,-1),(1,1),(-1,1)]:vs.append([c[k]+side[k]*sw*w/2+normal[k]*st*t/2 for k in range(3)])
 fs=[]
 for j in range(len(points)-1):
  for k in range(4):a=j*4+k;b=j*4+(k+1)%4;c=b+4;e=a+4;fs.extend([(a,b,c),(a,c,e)])
 fs.extend([(0,2,1),(0,3,2)]);k=len(vs)-4;fs.extend([(k,k+1,k+2),(k,k+2,k+3)]);return mesh(name,vs,fs,ma,parent,extra)
def tube(name,points,r=.004,parent=0,ma=leather,N=8):
 vs=[]
 for j,c in enumerate(points):
  tan=unit(vector(points[min(j+1,len(points)-1)],points[max(0,j-1)]));a=unit(cross(tan,[0,1,0] if abs(tan[1])<.95 else [1,0,0]));b=cross(tan,a)
  for k in range(N):v=k*2*math.pi/N;vs.append([c[i]+r*(a[i]*math.cos(v)+b[i]*math.sin(v)) for i in range(3)])
 fs=[]
 for j in range(len(points)-1):
  for k in range(N):a=j*N+k;b=j*N+(k+1)%N;c=b+N;e=a+N;fs.extend([(a,b,c),(a,c,e)])
 return mesh(name,vs,fs,ma,parent)
def arc_xy(cx,cy,z,rx,ry,start=0,end=2*math.pi,N=36):return [[cx+rx*math.cos(start+(end-start)*i/N),cy+ry*math.sin(start+(end-start)*i/N),z] for i in range(N+1)]
def ring(name,c,rx=.028,ry=.028,parent=0):tube(name,arc_xy(c[0],c[1],c[2],rx,ry),.003,parent,nickel)

def smooth_route(points):
 out=[]
 for i in range(len(points)-1):
  a=points[max(0,i-1)];b=points[i];c=points[i+1];e=points[min(len(points)-1,i+2)]
  for j in range(4):
   t=j/4;out.append([.5*((2*b[k])+(-a[k]+c[k])*t+(2*a[k]-5*b[k]+4*c[k]-e[k])*t*t+(-a[k]+3*b[k]-3*c[k]+e[k])*t*t*t) for k in range(3)])
 out.append(points[-1]);return out
# Rounded front breast collar with load paths leading aft along both shoulders.
strap('breastcollar',p['breastcollar_route_m'],p['breastcollar_width_m'],p['breastcollar_thickness_m'],width_axis=p['breastcollar_width_axis'],surface_normals=p['breastcollar_surface_normals'])
# Girth is circumferential; harness pad is short and distinct from a riding seat.
strap('girth',arc_xy(0,1.16,-.08,.31,.395),.046,.006,width_axis=(0,0,1))
strap('harness_saddle_pad',arc_xy(0,1.16,-.08,*p.get('harness_pad_radii_xy_m',[.325,.415]),.10,math.pi-.10,22),.15,.016,width_axis=(0,0,1))
# Breeching passes behind hindquarters, with separate hip support straps.
strap('breeching',[[.30,1.10,-.34],[.31,1.09,-.61],[.27,1.075,-.84],[.15,1.06,-.98],[0,1.06,-1.00],[-.15,1.06,-.98],[-.27,1.075,-.84],[-.31,1.09,-.61],[-.30,1.10,-.34]],.052,.007,width_axis=(0,1,0))
for side,s in [('l',1),('r',-1)]:
 # Reconstructed shaft tugs: actual open loops, not empty attachment markers.
 # The bore admits C01's square tip without changing the horse scale.
 tc=p['shaft_tug_center_m'];cx=s*tc[0];cy=tc[1];cz=tc[2]
 tube('shaft_tug_'+side,arc_xy(cx,cy,cz,p['shaft_tug_bore_radius_m']+p['shaft_tug_section_radius_m'],p['shaft_tug_bore_radius_m']+p['shaft_tug_section_radius_m'],N=48),p['shaft_tug_section_radius_m'],N=12)
 strap('shaft_tug_support_'+side,[[s*.32,1.36,-.08],[s*.35,1.24,-.015],[cx,cy+p['shaft_tug_bore_radius_m']+p['shaft_tug_section_radius_m'],cz]],.028,.006,width_axis=(0,0,1))
 strap('hip_support_'+side,[[s*.29,1.09,-.66],[s*.27,1.36,-.64],[s*.13,1.50,-.54],[0,1.525,-.48]],.023,.004,width_axis=(0,0,1))
 strap('longitudinal_support_'+side,[[s*.13,1.51,-.52],[s*.14,1.55,-.20],[s*.15,1.54,.03]],.020,.004)
 if p.get('breastcollar_support_route_m'):
  strap('breastcollar_support_'+side,smooth_route([[s*v[0],v[1],v[2]] for v in p['breastcollar_support_route_m']]),.023,.004,width_axis=(0,0,1))
 else:
  strap('breastcollar_support_'+side,[[s*p['breastcollar_route_m'][1][0],*p['breastcollar_route_m'][1][1:]],[s*.20,1.44,.38],[s*.09,1.57,.32],[0,1.585,.27]],.023,.004)
 strap('trace_'+side,[[s*p['breastcollar_route_m'][0][0],*p['breastcollar_route_m'][0][1:]],[s*.355,1.10,-.18],[s*.37,1.045,-.90],[s*.39,1.04,p['trace_tail_z_m']]],p['trace_width_m'],.005,width_axis=(0,1,0),extra={'width_m':p['trace_width_m'],'width_grade':'text_attested','route_and_length_grade':'reconstructed','source_locator':'Moore 1891 printed p1 Buggy Harness No1'})
 ring('trace_end_'+side,[s*.39,1.04,p['trace_tail_z_m']],.02,.024)
 ring('rein_terret_'+side,[s*.14,1.59,-.08],.020,.022)
 # Original dimensional bridle route local to horse head, not plate tracing.
 strap('cheekpiece_'+side,[[s*p['headstrap_reconstruction_trial']['cheekpiece_top_m'][0],*p['headstrap_reconstruction_trial']['cheekpiece_top_m'][1:]],[s*p['headstrap_reconstruction_trial']['cheekpiece_poll_m'][0],*p['headstrap_reconstruction_trial']['cheekpiece_poll_m'][1:]],[s*p['headstrap_reconstruction_trial']['cheekpiece_middle_m'][0],*p['headstrap_reconstruction_trial']['cheekpiece_middle_m'][1:]],[s*p['headstrap_reconstruction_trial']['cheekpiece_lower_m'][0],*p['headstrap_reconstruction_trial']['cheekpiece_lower_m'][1:]],[s*.095,-.20,.39]],p['bridle_width_m'],.003,parent=head,width_axis=(0,1,0))
 ring('bit_ring_'+side,[s*.105,-.20,.39],.026,.026,head)
 strap('rein_'+side,[[s*.095,1.68,1.19],[s*.15,1.66,.77],[s*.14,1.59,-.08],[s*.16,1.49,-.8],p['driver_hands_m'][0 if s==1 else 1]],p['rein_width_m'],p['rein_thickness_m'],width_axis=(0,1,0),extra={'status':'rest_pose_only_not_dynamic','shape':'flat_rein','dimensions':'reconstructed'})
 tube('round_check_rein_'+side,[[s*.10,1.70,1.18],[s*.15,1.93,.92],[s*.14,1.87,.63],[s*.14,1.59,-.08]],p['check_rein_radius_m'])
 strap('girth_billet_'+side,[[s*.32,1.30,-.08],[s*.32,1.10,-.08],[s*.27,.91,-.08]],.025,.005,width_axis=(0,0,1))
 # Rectangular nickel buckle frames use actual strips, not decals.
 x=s*.325;y=1.21;z=-.08
 tube('girth_buckle_'+side,[[x,y-.022,z-.018],[x,y+.022,z-.018],[x,y+.022,z+.018],[x,y-.022,z+.018],[x,y-.022,z-.018]],.003,ma=nickel)
strap('crownpiece',arc_xy(0,p['headstrap_reconstruction_trial']['crownpiece_center_y_m'],p['headstrap_reconstruction_trial']['crownpiece_z_m'],*p['headstrap_reconstruction_trial']['crownpiece_radii_xy_m'],0,math.pi,20),p['bridle_width_m'],.003,parent=head,width_axis=(0,0,1))
strap('browband',p['headstrap_reconstruction_trial']['browband_route_m'],p['bridle_width_m'],.003,parent=head,width_axis=(0,1,0))
strap('noseband',arc_xy(0,p['headstrap_reconstruction_trial']['noseband_center_y_m'],.36,*p['headstrap_reconstruction_trial']['noseband_radii_xy_m']),p['bridle_width_m'],.003,parent=head,width_axis=(0,0,1))
# Bit is a reconstruction fixture bar; no historically specific mouthpiece is asserted.
tube('bit_bar',[[-.105,-.20,.39],[0,-.205,.40],[.105,-.20,.39]],.006,head,nickel)
anchors={}
for side,s in [('l',1),('r',-1)]:
 for role,v in [('trace',[s*p['breastcollar_route_m'][0][0],*p['breastcollar_route_m'][0][1:]]),('trace_end',[s*.39,1.04,p['trace_tail_z_m']]),('breeching',[s*.28,1.10,-.70]),('shaft',[s*p['shaft_tug_center_m'][0],*p['shaft_tug_center_m'][1:]]),('rein_hand',p['driver_hands_m'][0 if s==1 else 1])]:
  nm='socket_harness_'+role+'_'+side;node(nm,translation=v,extras={'role':role,'fit':'unpassed'});anchors[nm]={'translation_m':v,'rotation_xyzw':[0,0,0,1],'horse_socket':('socket_equine_'+role+'_'+side) if role in ['trace','breeching','shaft'] else None}
 nm='socket_harness_bit_'+side;v=[s*.095,-.20,.39];node(nm,parent=head,translation=v,extras={'horse_socket':'socket_equine_bit_'+side,'fit':'unpassed'});anchors[nm]={'translation_m':v,'parent':'harness_head','horse_socket':'socket_equine_bit_'+side,'rotation_xyzw':[0,0,0,1]}
while len(bin)%4:bin.append(0)
d['buffers']=[{'byteLength':len(bin)}];j=json.dumps(d,separators=(',',':')).encode();j+=b' '*((-len(j))%4);raw=struct.pack('<III',0x46546c67,2,12+8+len(j)+8+len(bin))+struct.pack('<II',len(j),0x4e4f534a)+j+struct.pack('<II',len(bin),0x004e4942)+bin
(P/(p['asset_id']+'.glb')).write_bytes(raw)
side={'asset_id':p['asset_id'],'version':'fixture_0.1','frame':{'units':'metres','up':'+Y','forward':'+Z','left':'+X','origin':'horse fixture ground root'},'license':'CC0-1.0','grade':'reconstructed','source':{'source_id':'john_moore_harness_catalog_1891','verification':'OCR-read; original page and plate verification outstanding','title':'John Moore Fine harness saddlery & horse clothing','year':1891,'url':'https://archive.org/stream/fineharnesssaddl1891john/fineharnesssaddl1891john_djvu.txt','locator':'printed p1 Buggy Harness No1','rights_basis':'Reasoned US public domain: published New York 1891; IA metadata contains no explicit rights statement. Construction text read; plates not read or traced.'},'bindings':[{'harness_node':'root','horse_node':'root','operation':'copy actor root world transform','status':'proposed_not_runtime_bound'},{'harness_node':'harness_head','horse_node':'head','operation':'copy current head world transform after actor animation; harness geometry is authored head-local','status':'proposed_not_runtime_bound'}],'anchors':anchors,'head_relative_components':['cheekpiece_l','cheekpiece_r','bit_ring_l','bit_ring_r','crownpiece','browband','noseband','bit_bar'],'dynamic_components_unbound':['rein_l','rein_r','round_check_rein_l','round_check_rein_r','trace_l','trace_r'],'missing':['source plate verification','photographic comparison','correct fitted clearances','rein and trace tension','breeching force behavior','bits/bridle pressure suitability','riding tack','collar and hames variants','LOD derivatives','Blender authored master','sourced buckle and mouthpiece shapes'],'triangles':sum(v['triangles'] for v in stats.values()),'mesh_count':len(stats),'glb_bytes':len(raw)}
side['shaft_tugs']={'center_m':p['shaft_tug_center_m'],'bore_radius_m':p['shaft_tug_bore_radius_m'],'section_radius_m':p['shaft_tug_section_radius_m'],'grade':'reconstructed','geometry':'open round-section loop in local XY plane; support webbing to girth/saddle; no source-plate or force qualification','mesh_names':['shaft_tug_l','shaft_tug_r','shaft_tug_support_l','shaft_tug_support_r']}
if p.get('breastcollar_routing_study'):side['breastcollar_routing_study']=p['breastcollar_routing_study']
(P/'manifest.json').write_text(json.dumps(side,indent=2)+'\n');(P/'geometry-stats.json').write_text(json.dumps(stats,indent=2)+'\n');print(json.dumps({'glb_bytes':len(raw),'triangles':side['triangles'],'meshes':len(stats),'anchors':len(anchors)}))
