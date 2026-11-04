#!/usr/bin/env python3
"""Generate a reconstructed current26 collar/girth and visible two-horse draft links.

Only this outside-app directory is written. Horse and vehicle assets are inputs.
The source mesh's triangle surfaces, weights and true front-axle hierarchy are read;
no old15-joint tack interface or prospective root-space socket is substituted.
"""
import os
for k in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']: os.environ[k]='1'
import copy,hashlib,json,math,struct,time,importlib.util
from pathlib import Path
import numpy as np

HERE=Path(__file__).parent
HORSE=Path('/workspace/.cloud-setup/transport-T2803-grounded-gait-nextstep-20261031/BARE-CURRENT26-WALK-SPECIMEN-11-BOUNDED-CAREFUL-WALK/candidate-current26-bare-careful-walk-cubic129-smooth-unit.glb')
WAGON=Path('/workspace/chicago-wagon-delivery-20261030/chicago/4d/renderers/web/transport/wagon-driver/wagon-w01.glb')
PARAMETERS=HERE/'team-hitch-parameters.json'
sha=lambda b:hashlib.sha256(b).hexdigest()
def read(raw):
    n=struct.unpack_from('<I',raw,12)[0]
    return json.loads(raw[20:20+n]),raw[28+n:]
def accessor(d,b,i):
    a=d['accessors'][i];v=d['bufferViews'][a['bufferView']]
    count={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}[a['type']]
    dt=np.dtype({5121:'u1',5123:'<u2',5125:'<u4',5126:'<f4'}[a['componentType']])
    if a.get('sparse') or a.get('normalized'):raise ValueError('Explicit unnormalized streams required')
    return np.ndarray((a['count'],count),dt,b,v.get('byteOffset',0)+a.get('byteOffset',0),strides=(v.get('byteStride',count*dt.itemsize),dt.itemsize)).copy()
def pack(d,b):
    j=json.dumps(d,separators=(',',':')).encode();j+=b' '*(-len(j)%4);b+=b'\0'*(-len(b)%4)
    return struct.pack('<5I',0x46546c67,2,28+len(j)+len(b),len(j),0x4e4f534a)+j+struct.pack('<2I',len(b),0x004e4942)+b
def write_glb(path,d,arrays):
    b=bytearray();d['accessors']=[];d['bufferViews']=[]
    for array,kind,component in arrays:
        array=np.ascontiguousarray(array);b.extend(b'\0'*(-len(b)%4));v=len(d['bufferViews'])
        d['bufferViews'].append({'buffer':0,'byteOffset':len(b),'byteLength':array.nbytes})
        d['accessors'].append({'bufferView':v,'componentType':component,'count':len(array),'type':kind})
        if kind=='VEC3' and component==5126:d['accessors'][-1].update(min=array.min(0).tolist(),max=array.max(0).tolist())
        b.extend(array.tobytes())
    d['buffers']=[{'byteLength':len(b)}];path.write_bytes(pack(d,bytes(b)))

def ray_hit(vertices,faces,origin,direction):
    a,b,c=vertices[faces[:,0]],vertices[faces[:,1]],vertices[faces[:,2]]
    ab=b-a;ac=c-a;h=np.cross(np.broadcast_to(direction,ac.shape),ac)
    det=np.einsum('ij,ij->i',ab,h);valid=abs(det)>1e-10;inv=np.zeros_like(det);inv[valid]=1/det[valid]
    s=origin-a;u=inv*np.einsum('ij,ij->i',s,h);q=np.cross(s,ab)
    v=inv*np.einsum('j,ij->i',direction,q);t=inv*np.einsum('ij,ij->i',ac,q)
    keep=valid&(u>=-1e-8)&(v>=-1e-8)&(u+v<=1+1e-8)&(t>1e-7)
    ids=np.flatnonzero(keep)
    if not len(ids):raise ValueError(('No body surface for collar ray',origin.tolist(),direction.tolist()))
    i=int(ids[np.argmin(t[ids])]);return origin+direction*t[i],i,np.array([1-u[i]-v[i],u[i],v[i]])

def main():
    start=time.monotonic();raw=HORSE.read_bytes();assert sha(raw)=='bf519adae76693c5e2b8c18bfe9bbaea8a7c83c523b502ca748df2dd7251241e'
    d,b=read(raw);prim=d['meshes'][1]['primitives'][0];P=accessor(d,b,prim['attributes']['POSITION']).astype(float)
    J=accessor(d,b,prim['attributes']['JOINTS_0']).astype(int);W=accessor(d,b,prim['attributes']['WEIGHTS_0']).astype(float);W/=W.sum(1)[:,None]
    F=accessor(d,b,prim['indices']).reshape(-1,3).astype(int)
    params={'schema':'current26_two_horse_draft_hitch_prototype_v1','scope':'Bounded original reconstructed engineering prototype; actual native motion/contact/render acceptance unrun',
        'source_horse_sha256':sha(raw),'source_wagon_sha256':sha(WAGON.read_bytes()),'units':'m','up':'+Y','forward':'+Z','segments':48,
        'bands':[{'name':'full_collar','center_y_m':1.24,'center_z_m':.75,'width_z_m':.05},{'name':'girth','center_y_m':1.18,'center_z_m':0.,'width_z_m':.035},{'name':'noseband','center_y_m':1.43,'center_z_m':1.40,'width_z_m':.035},{'name':'pollstrap','center_y_m':1.48,'center_z_m':1.05,'width_z_m':.035}],
        'surface_inner_clearance_m':.008,'surface_outer_clearance_m':.012,'horse_center_half_track_m':.65,
        'front_axle_root_m':[0,.535,1.175],'tongue_pivot_in_front_axle_m':[0,0,.35],'tongue_length_m':2.75,
        'singletree_root_y_m':.72,'singletree_root_z_m':1.9,'singletree_halfwidth_m':.45,'trace_width_m':.025,'trace_thickness_m':.004,
        'policy':'Horse source streams remain exact. New collars interpolate the actual intersected BODY triangle skin weights into the same26 joints. Visible links are new portable geometry. No historical owner, exact harness construction, force physics, accepted tack sockets or rein grip is asserted.'}
    if PARAMETERS.exists():assert json.loads(PARAMETERS.read_text())==params
    else:PARAMETERS.write_text(json.dumps(params,indent=2)+'\n')
    outP=[];outJ=[];outW=[];outN=[];outUV=[];triangles=[];bindings=[];ranges=[]
    for band in params['bands']:
        first=len(outP);num=params['segments']
        # Four rings: inner/outer surfaces at both axial edges. Every ring is
        # fitted independently to its actual triangle, so a guessed ellipse
        # cannot put the lower collar through the chest.
        for clearance,zsign in [(params['surface_inner_clearance_m'],-1),(params['surface_inner_clearance_m'],1),(params['surface_outer_clearance_m'],-1),(params['surface_outer_clearance_m'],1)]:
            z=band['center_z_m']+zsign*band['width_z_m']/2
            for i in range(num):
                angle=2*math.pi*i/num;direction=np.array([math.cos(angle),math.sin(angle),0.])
                hit,face,bary=ray_hit(P,F,np.array([0.,band['center_y_m'],z]),direction)
                pos=hit+direction*clearance;weights=np.zeros(26)
                for corner,coefficient in zip(F[face],bary):
                    for joint,w in zip(J[corner],W[corner]):weights[joint]+=coefficient*w
                order=np.argsort(-weights,kind='stable')[:4];selected=weights[order];selected/=selected.sum()
                outP.append(pos);outJ.append(order);outW.append(selected);outN.append(direction if clearance>params['surface_inner_clearance_m'] else -direction);outUV.append([i/num,(zsign+1)/2])
                bindings.append({'body_face':int(face),'barycentric':bary.tolist(),'rest_outward':direction.tolist(),'rest_surface_point_m':hit.tolist(),'clearance_m':clearance,'band':band['name']})
        for ringA,ringB in [(0,1),(2,3),(0,2),(1,3)]:
            for i in range(num):
                a=first+ringA*num+i;an=first+ringA*num+(i+1)%num;c=first+ringB*num+i;cn=first+ringB*num+(i+1)%num
                triangles.extend([[a,an,cn],[a,cn,c]])
        ranges.append({'name':band['name'],'first_vertex':first,'vertex_count':4*num,'triangle_count':8*num})
    Pout=np.array(outP,dtype='<f4');Jout=np.array(outJ,dtype='<u2');Wout=np.array(outW,dtype='<f4');Nout=np.array(outN,dtype='<f4');UVout=np.array(outUV,dtype='<f4');Tout=np.array(triangles,dtype='<u2').reshape(-1,1)
    nodes=copy.deepcopy(d['nodes'][:26]);nodes.append({'name':'current26_reconstructed_draft_harness','mesh':0,'skin':0})
    harness={'asset':{'version':'2.0','generator':'build_hitch_prototype.py','copyright':'Original reconstructed harness geometry; GPL-3.0-or-later','extras':{'source_horse_sha256':sha(raw),'qualification':'SOURCE_PROTOTYPE_ONLY_NATIVE_CONTACT_RENDER_UNRUN'}},'scene':0,'scenes':[{'nodes':[0,26]}],'nodes':nodes,
        'skins':[{'name':'same_current26_source_rig','skeleton':0,'joints':list(range(26)),'inverseBindMatrices':6}],
        'meshes':[{'name':'surface_fitted_collar_and_girth','primitives':[{'attributes':{'POSITION':0,'NORMAL':1,'TEXCOORD_0':2,'JOINTS_0':3,'WEIGHTS_0':4},'indices':5,'material':0,'mode':4}]}],
        'materials':[{'name':'reconstructed_brown_draft_leather','pbrMetallicRoughness':{'baseColorFactor':[.12,.065,.032,1],'metallicFactor':0,'roughnessFactor':.8},'doubleSided':True}]}
    arrays=[(Pout,'VEC3',5126),(Nout,'VEC3',5126),(UVout,'VEC2',5126),(Jout,'VEC4',5123),(Wout,'VEC4',5126),(Tout,'SCALAR',5123),(accessor(d,b,d['skins'][0]['inverseBindMatrices']).astype('<f4'),'MAT4',5126)]
    asset=HERE/'current26-surface-fitted-collar-girth-SOURCE-PROTOTYPE.glb';write_glb(asset,harness,arrays)
    # Two collars' true lower points determine yoke height and the existing
    # pole's pitch/fore-aft team position. The 2.75m value is local to the tongue,
    # which itself starts .35m ahead of the steering axle at rootZ1.175m.
    low=next(i for i,row in enumerate(bindings) if row['band']=='full_collar' and abs(row['rest_outward'][1]+1)<1e-8)
    yokeY=float(Pout[low,1]);height=yokeY-params['front_axle_root_m'][1];length=params['tongue_length_m']
    if not 0<height<length:raise ValueError('No real pole pitch can reach fitted collar underside')
    pitch=-math.asin(height/length);tipZ=.35+length*math.cos(pitch);horseZ=tipZ-params['bands'][0]['center_z_m']
    # Clear space for a live two-horse pair and true primitive dimensions; these
    # are construction targets, not already certified rig sockets.
    construction={'frame':'vehicle_steer_front local axes, metres','horse_centres_m':[[side*.65,-.535,horseZ]for side in [-1,1]],
        'tongue_pitch_rad':pitch,'tongue_tip_m':[0,height,tipZ],'collar_lower_vertex_index':low,
        'neck_yoke_endpoints_m':[[-.65,height,tipZ],[.65,height,tipZ]],
        'singletree_centres_m':[[side*.65,.72-.535,1.9-1.175]for side in [-1,1]],'singletree_halfwidth_m':.45,
        'evener_endpoints_m':[[-.65,.145,.62],[.65,.145,.62]],'evener_anchor_m':[0,0,0],
        'trace_surface_binding':'full_collar and girth outer-side vertices, live source BODY barycentric field; dynamic segments to corresponding singletree ends',
        'rein_binding':'UNRUN actual palm and mouth/bit geometry; prospective wrist sockets refused',
        'steering_limit_deg_unchanged':8,'old_tongue_source_vertices_changed':False,'horse_source_vertices_or_rig_changed':False}
    (HERE/'fitted-team-construction-SOURCE-PROTOTYPE.json').write_text(json.dumps(construction,indent=2)+'\n')
    (HERE/'collar-surface-bindings.json').write_text(json.dumps({'horse_sha256':sha(raw),'BODY_mesh_index':1,'ranges':ranges,'vertices':bindings},indent=2)+'\n')
    report={'status':'GENERATED_SOURCE_HITCH_PROTOTYPE_NOT_NATIVE_OR_WORLD_ACCEPTANCE','seconds':time.monotonic()-start,'horse_input_sha256':sha(raw),'horse_source_unchanged':sha(HORSE.read_bytes())==sha(raw),'wagon_source_unchanged':sha(WAGON.read_bytes())==params['source_wagon_sha256'],
        'harness':{'path':str(asset),'sha256':sha(asset.read_bytes()),'bytes':asset.stat().st_size,'vertices':len(Pout),'triangles':len(triangles),'materials':1,'images':0,'skinned_joints':26},'construction':construction,
        'actual_native_physical_contact':'UNRUN','actual_browser_render':'UNRUN','historical_harness_attestation':False,'certified_hitch_sockets':False,'pole_load_physics':False,'reins_accepted':False}
    (HERE/'GENERATED-SOURCE-PROTOTYPE.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:report[k]for k in ['status','seconds','harness']}))

if __name__=='__main__':main()
