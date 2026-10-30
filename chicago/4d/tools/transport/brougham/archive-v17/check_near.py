# SPDX-License-Identifier: GPL-3.0-or-later
"""V17 exact NEAR delivery gate with independent additive MID gate. Existing decoded algorithms; no terrain/image/wholeLOD acceptance."""
from pathlib import Path
import argparse,hashlib,json,math,struct
EXPECTED_CONTRACT='860b7df7c8d25e1aa372a0a4250f92e4dfffb2c7cfbd14450b9db329cf5fc910'

def read(path):
    b=path.read_bytes();assert struct.unpack_from('<III',b)==(0x46546c67,2,len(b)), 'Invalid GLB envelope'
    n,t=struct.unpack_from('<II',b,12);assert t==0x4e4f534a
    j=json.loads(b[20:20+n]);m,t=struct.unpack_from('<II',b,20+n);assert t==0x004e4942
    return j,b[28+n:28+n+m]

def values(j,b,i):
    a=j['accessors'][i];v=j['bufferViews'][a['bufferView']];assert not a.get('sparse')
    width={'VEC3':3,'SCALAR':1}[a['type']];fmt={5126:'f',5123:'H',5125:'I'}[a['componentType']];size=struct.calcsize(fmt)*width;off=v.get('byteOffset',0)+a.get('byteOffset',0);stride=v.get('byteStride',size)
    assert off>=0 and off+(a['count']-1)*stride+size<=len(b), 'Accessor outside binary'
    return [struct.unpack_from('<'+fmt*width,b,off+k*stride) for k in range(a['count'])]

def expanded(j,b):
    h=hashlib.sha256();tris=0
    for m in j['meshes']:
        for p in m['primitives']:
            assert p.get('mode',4)==4 and set(p['attributes'])=={'POSITION','NORMAL'}
            pts=values(j,b,p['attributes']['POSITION']);norms=values(j,b,p['attributes']['NORMAL']);assert len(pts)==len(norms)
            ids=[q[0] for q in values(j,b,p['indices'])] if 'indices' in p else list(range(len(pts)))
            assert len(ids)%3==0;tris+=len(ids)//3
            for k in ids:
                assert 0<=k<len(pts)
                assert all(math.isfinite(x) for x in pts[k]+norms[k]);assert abs(math.sqrt(sum(x*x for x in norms[k]))-1)<1e-4
                h.update(struct.pack('<ffffff',*(pts[k]+norms[k])))
            for off in range(0,len(ids),3):
                a,c,d=[pts[i] for i in ids[off:off+3]];u=[c[k]-a[k] for k in range(3)];v=[d[k]-a[k] for k in range(3)];cross=[u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]]
                assert sum(x*x for x in cross)>1e-20, 'Degenerate delivered triangle'
    return h.hexdigest(),tris

def world_nodes(j):
    world={}
    def visit(i,prev):
        n=j['nodes'][i];assert not any(k in n for k in ['scale','rotation','matrix'])
        world[i]=[prev[k]+n.get('translation',[0,0,0])[k] for k in range(3)]
        for c in n.get('children',[]):visit(c,world[i])
    for i in j['scenes'][j.get('scene',0)]['nodes']:visit(i,[0,0,0])
    return world

def decoded_bounds(j,b,world):
    points=[]
    for i,node in enumerate(j['nodes']):
        if 'mesh' not in node:continue
        for prim in j['meshes'][node['mesh']]['primitives']:
            for p in values(j,b,prim['attributes']['POSITION']):points.append([p[k]+world[i][k] for k in range(3)])
    return {'min':[min(p[k] for p in points) for k in range(3)],'max':[max(p[k] for p in points) for k in range(3)]}

def raw_stream(j,b,mesh,kind):
    a=j['accessors'][j['meshes'][mesh]['primitives'][0]['attributes'][kind]];v=j['bufferViews'][a['bufferView']]
    assert a['componentType']==5126 and a['type']=='VEC3' and not v.get('byteStride')
    off=v.get('byteOffset',0)+a.get('byteOffset',0);return b[off:off+a['count']*12]

def component(j,b,part,kind):
    name=f"surface_{part['frame']}_{part['material']}";ids=[i for i,x in enumerate(j['meshes']) if x['name']==name];assert ids
    primitive=j['meshes'][ids[0]]['primitives'][0];stream=raw_stream(j,b,ids[0],kind)
    if 'indices' in primitive:
        vertices=values(j,b,primitive['attributes'][kind]);stream=b''.join(struct.pack('<fff',*vertices[i[0]]) for i in values(j,b,primitive['indices']))
    start=part['triangle_start_in_batch']*36;out=stream[start:start+part['triangles']*36];assert len(out)==part['triangles']*36;return out

def protected_signatures(j,b):
    part=hashlib.sha256();count=0
    original=[p for p in j['extras']['parts'] if p['name']!='rear_quarter_recessed_surface']
    assert len(original)==466
    for i,p in enumerate(original):
        if p['name']=='rear_quarter_panel':continue
        part.update(struct.pack('<I',i));part.update(json.dumps([p['name'],p['frame'],p['material'],p['triangles']],separators=(',',':')).encode())
        for kind in ['POSITION','NORMAL']:part.update(component(j,b,p,kind))
        count+=1
    mesh=hashlib.sha256();streams=0
    original_meshes=[(i,row) for i,row in enumerate(j['meshes']) if row['name']!='surface_vehicle_body_6']
    assert len(original_meshes)==24
    for old_i,(i,row) in enumerate(original_meshes):
        if row['name']=='surface_vehicle_body_0':continue
        mesh.update(struct.pack('<I',old_i));mesh.update(row['name'].encode())
        for kind in ['POSITION','NORMAL']:mesh.update(raw_stream(j,b,i,kind));streams+=1
    return {'parts':count,'protected_part_PN_sha256':part.hexdigest(),'mesh_streams':streams,'protected_mesh_PN_sha256':mesh.hexdigest()}

def subtree(j,i):
    yield i
    for child in j['nodes'][i].get('children',[]):yield from subtree(j,child)

def points(j,b,world,root):
    out=[]
    for i in subtree(j,root):
        node=j['nodes'][i]
        if 'mesh' not in node:continue
        for p in j['meshes'][node['mesh']]['primitives']:
            vs=values(j,b,p['attributes']['POSITION']);ids=[x[0] for x in values(j,b,p['indices'])] if 'indices' in p else range(len(vs))
            out.extend(tuple(vs[k][a]+world[i][a] for a in range(3)) for k in ids)
    return out

def bounds(ps):return {'min':[min(p[k] for p in ps) for k in range(3)],'max':[max(p[k] for p in ps) for k in range(3)]}

def native_contacts(j,b):
    world=world_nodes(j);wheels=[]
    for i,n in enumerate(j['nodes']):
        if not n['name'].startswith('vehicle_wheel_'):continue
        ps=points(j,b,world,i);low=min(p[1] for p in ps);lowpoints=sorted(set(p for p in ps if abs(p[1]-low)<1e-7))
        wheels.append({'node':n['name'],'center_root_m':world[i],'bounds_root_m':bounds(ps),'lowest_points_root_m':[list(q) for q in lowpoints]})
    pole=next(i for i,n in enumerate(j['nodes']) if n['name']=='vehicle_team_pole');hitch=next(i for i,n in enumerate(j['nodes']) if n['name']=='vehicle_hitch_team')
    shoe=next(p for p in j['extras']['parts'] if p['name']=='parked_pole_ground_shoe');ps=list(struct.iter_unpack('<fff',component(j,b,shoe,'POSITION')))
    return {'wheels':wheels,'full_fixed_pole_bounds_root_m':bounds(points(j,b,world,pole)),'shoe_bounds_root_m':bounds(ps),'shoe_bottom_corners_root_m':[list(q) for q in sorted(set(p for p in ps if abs(p[1])<1e-7))],'parked_hitch_root_m':world[hitch],'has_tongue_hinge':any(n['name']=='vehicle_tongue' for n in j['nodes'])}
def check_near(directory,source_directory):
    here=Path(__file__).resolve().parent;contract_path=here/'near-contract.json'
    assert hashlib.sha256(contract_path.read_bytes()).hexdigest()==EXPECTED_CONTRACT,'Exact reviewed near contract changed'
    c=json.loads(contract_path.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    master=directory/'brougham-source.glb';near=directory/'brougham-near.glb'
    assert sha(master)==c['raw_sha256'] and master.stat().st_size==c['raw_bytes'],'Exact V17 rawmaster'
    assert sha(near)==c['near_sha256'] and near.stat().st_size==c['near_bytes'],'Exact V17 indexednear'
    for name,digest in c['source_files'].items():assert sha(source_directory/name)==digest,'Exact reviewed producer/source/recipe/license '+name
    for name,digest in c['delivery_metadata_files'].items():assert sha(directory/name)==digest,'Exact delivery metadata/license '+name
    j,b=read(master);d,db=read(near);signature,tri=expanded(j,b);near_signature,near_tri=expanded(d,db)
    assert tri==near_tri==c['triangles']==33502 and signature==near_signature==c['expanded_PN_sha256'],'Actual near expanded triangles/P-N'
    for key in ['nodes','materials','scenes','scene','extras','extensionsUsed']:assert j.get(key)==d.get(key),'Preserved raw/near '+key
    assert len(j['nodes'])==42 and len(j['meshes'])==25 and len(j['materials'])==7 and len(j['extras']['parts'])==468
    assert not any(j.get(k) or d.get(k) for k in ['images','textures','skins','animations']) and all('uri' not in q for doc in [j,d] for q in doc['buffers'])
    for doc,bin in [(j,b),(d,db)]:assert decoded_bounds(doc,bin,world_nodes(doc))==c['bounds_m'],'Actual full native envelope'
    assert protected_signatures(j,b)==c['protected_V15_streams'],'464part/46stream role-mapped V15 baseline'
    params=json.loads((source_directory/'parameters.json').read_text());extra=j['extras'];assert extra['parameters']==params
    assert extra['license']=='GPL-3.0-or-later' and extra['units']=='m' and extra['up_axis']=='+Y' and extra['forward_axis']=='+Z' and extra['root_datum']=='ground midpoint between axles'
    assert extra['source_id']=='studebaker_1893_illustrated_souvenir' and extra['source_reference']['scan_leaf']=='0095' and extra['source_reference']['sha256']==c['reference_sha256']
    assert all(extra[k] is False for k in ['door_interaction_enabled','boarding_enabled','traffic_enabled','occupants'])
    side=json.loads((directory/'brougham.json').read_text());assert side['source_master_sha256']==c['raw_sha256'] and side['parameters_sha256']==c['source_files']['parameters.json']
    assert side['grade']=='reconstructed' and side['license']=='GPL-3.0-or-later' and side['scene_eligibility']==c['scene_eligibility'] and extra['scene_year']==1904
    assert len(side['lods'])==2 and [r['detail'] for r in side['lods']]==['near','mid'] and side['lods'][0]['indexed_sha256']==c['near_sha256'] and side['lod_runtime_selection_enabled'] is True
    world=world_nodes(j);assert len(side['anchors'])==13
    for anchor in side['anchors']:assert anchor['node']==j['nodes'][anchor['node_index']]['name'] and anchor['translation_root_m']==world[anchor['node_index']] and anchor['rotation_xyzw']==[0,0,0,1] and anchor['scale']==[1,1,1] and anchor['dynamic_binding_supported'] is False
    assert side['static_master']['frame']=={'units':'m','up':'+Y','forward':'+Z','root':'vehicle_root'} and all(x is False for x in side['static_master']['capabilities'].values())
    assert len(side['static_master']['named_targets'])==8 and len(side['static_master']['collision_proxy']['components'])==9 and side['static_master']['collision_proxy']['runtime_enabled'] is False
    assert side['static_master']==c['static_master'], 'Exact inert V17 interfaces'
    for entry in side['static_master']['entries']:
        for role,index_key,bounds_key in [('deep_U_closed_door','door_part_index','closed_door_bounds_root_m'),('door_step','step_part_index','step_bounds_root_m')]:
            part=j['extras']['parts'][entry[index_key]]
            assert part['name']==role and part['frame']=='vehicle_body', 'Actual source part-index role'
            ps=list(struct.iter_unpack('<fff',component(j,b,part,'POSITION')))
            assert bounds(ps)==entry[bounds_key], 'Actual static source part-index bounds'
    measured=native_contacts(j,b);assert measured==native_contacts(d,db)==c['native_contacts'],'Actual complete wheel/shoe/pole/hitch readback'
    assert len(measured['wheels'])==4 and measured['has_tongue_hinge'] is False
    for wheel in measured['wheels']:
        center=wheel['center_root_m'];assert len(wheel['lowest_points_root_m'])==1 and abs(wheel['lowest_points_root_m'][0][1])<1e-6
        assert abs(wheel['lowest_points_root_m'][0][0]-center[0])<1e-6 and abs(wheel['lowest_points_root_m'][0][2]-center[2])<1e-6
    assert side['wheel_contacts_root_m']==[[-.67,0,-1.15],[.67,0,-1.15],[-.67,0,1.15],[.67,0,1.15]]
    assert len(measured['shoe_bottom_corners_root_m'])==4
    for point in side['static_pole_ground_shoe_contact_root_m']:assert any(max(abs(a-b) for a,b in zip(point,q))<1e-6 for q in measured['shoe_bottom_corners_root_m'])
    conformance=[]
    for row in c['archived_khronos']:
        report=here/'archived-khronos'/row['report'];assert sha(report)==row['report_sha256'] and sha(directory/row['bound_file'])==row['actual_input_sha256']
        report=json.loads(report.read_text());issues=report['issues'];assert report['validatorVersion']=='2.0.0-dev.3.10' and issues['numErrors']==issues['numWarnings']==0 and issues['numInfos']==4 and not issues['truncated']
        assert sorted((x['code'],x['pointer']) for x in issues['messages'])==[('NODE_EMPTY','/nodes/'+str(i)) for i in [13,14,15,16]]
        assert report['info']['totalTriangleCount']==33502 and report['info']['drawCallCount']==25 and report['info']['hasSkins'] is False and report['info']['hasTextures'] is False
        conformance.append({'file':row['bound_file'],'archived_conformance':'PASS','fresh_execution':False})
    return {'pass':True,'scope':c['scope'],'raw_sha256':c['raw_sha256'],'near_sha256':c['near_sha256'],'triangles':tri,'protected_baseline_streams':c['protected_V15_streams'],'native_contacts':measured,'archived_khronos':conformance,'terrain_world_clearance_verified':False,'visual_or_photographic_acceptance':False}

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--directory',type=Path,required=True);ap.add_argument('--source-directory',type=Path,default=Path(__file__).resolve().parent);a=ap.parse_args();print(json.dumps(check_near(a.directory,a.source_directory)))
