# SPDX-License-Identifier: GPL-3.0-or-later
"""V19 exact body/finish delivery and independent V18 physical protection. No terrain/photo/LOD appearance acceptance."""
from pathlib import Path
import argparse,hashlib,json,math,struct

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
    from lamp_geometry import protected_signatures_v18
    return protected_signatures_v18(j,b)

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
EXPECTED_DETAIL_CONTRACTS = {'near': 'c7550592fdb8ee11d44ea1d1f223752555cb8a84007984033c638c8c5fcfb64b', 'mid': '926f8cc8d7b2a53679f40822f8afe691824655a7bb3eade9cf29939e4c3be0b0'}


def check_detail(mode, directory, source_directory):
    from body_geometry import check_preservation, mutation_controls, check_front_curve
    from lamp_geometry import keyed, lamp_surfaces
    from static_master import static_master_contract
    here=Path(__file__).resolve().parent
    contract_path=here/(mode+'-contract.json')
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    assert sha(contract_path)==EXPECTED_DETAIL_CONTRACTS[mode], 'Exact reviewed V19 '+mode+' contract'
    c=json.loads(contract_path.read_text())
    raw=directory/c['raw_file'];indexed=directory/c['indexed_file']
    assert sha(raw)==c['raw_sha256'] and raw.stat().st_size==c['raw_bytes'], 'Exact V19 raw '+mode
    assert sha(indexed)==c['indexed_sha256'] and indexed.stat().st_size==c['indexed_bytes'], 'Exact V19 indexed '+mode
    for name,digest in c['source_files'].items():assert sha(source_directory/name)==digest, 'Exact producer/source/license '+name
    for name,digest in c['delivery_metadata_files'].items():assert sha(directory/name)==digest, 'Exact delivered metadata '+name
    j,b=read(raw);d,db=read(indexed)
    signature,triangles=expanded(j,b);isig,it=expanded(d,db)
    assert triangles==it==c['triangles'] and signature==isig==c['expanded_PN_sha256'], 'Lossless actual indexed triangle/P-N stream'
    for key in ['nodes','materials','scenes','scene','extras','extensionsUsed']:
        assert j.get(key)==d.get(key), 'Raw/indexed semantic preservation '+key
    assert (len(j['nodes']),len(j['meshes']),len(j['materials']),len(j['extras']['parts']))==(c['nodes'],c['meshes'],c['materials'],c['parts'])
    for doc,bin in [(j,b),(d,db)]:
        assert not any(doc.get(k)for k in ['images','textures','skins','animations'])
        assert all('uri'not in q for q in doc['buffers'])
        assert decoded_bounds(doc,bin,world_nodes(doc))==c['bounds_m']
    baseline=json.loads((here/'v18-protected-body-baseline.json').read_text())['details'][mode]
    protected=check_preservation(j,b,baseline)
    assert protected==c['protected']
    assert lamp_surfaces(keyed(j,b),j['extras']['parameters'])==(456 if mode=='near'else 424), 'Actual accepted rounded-lamp apertures/winding/seams'
    assert native_contacts(j,b)==native_contacts(d,db)==c['native_contacts']
    assert j['extras']['parameters']==json.loads((source_directory/'parameters.json').read_text())
    e=j['extras'];assert e['license']=='GPL-3.0-or-later' and e['units']=='m' and e['up_axis']=='+Y' and e['forward_axis']=='+Z'
    assert e['root_datum']=='ground midpoint between axles' and e['scene_year']==1904
    assert e['source_id']=='studebaker_1893_illustrated_souvenir' and e['source_reference']['scan_leaf']=='0095' and e['source_reference']['sha256']==c['reference_sha256']
    assert all(e[k]is False for k in ['door_interaction_enabled','boarding_enabled','traffic_enabled','occupants'])
    actual_static=static_master_contract(j,b,world_nodes(j),c['raw_sha256'])
    assert actual_static==c['static_master'], 'Actual exact current inert interfaces'
    side=json.loads((directory/'brougham.json').read_text())
    assert side['revision']=='v19_catalogue_body_and_finish_near_mid_study'
    assert side['grade']=='reconstructed' and side['license']=='GPL-3.0-or-later'
    assert side['parameters_sha256']==c['source_files']['parameters.json']
    row=side['lods'][0 if mode=='near'else 1]
    assert row['detail']==mode and row['triangles']==triangles and row['source_sha256']==c['raw_sha256'] and row['indexed_sha256']==c['indexed_sha256']
    assert side['lod_runtime_selection_enabled']is True and all(v is False for v in side['lod_appearance_accepted'].values())
    assert side['mid_provenance']['photographic_accepted']is False and side['mid_provenance']['world_budget_accepted']is False
    for anchor in side['anchors']:
        assert anchor['node']==j['nodes'][anchor['node_index']]['name'] and anchor['translation_root_m']==world_nodes(j)[anchor['node_index']]
        assert anchor['rotation_xyzw']==[0,0,0,1] and anchor['scale']==[1,1,1] and anchor['dynamic_binding_supported']is False
    assert len(side['anchors'])==13 and len(actual_static['named_targets'])==8 and all(v is False for v in actual_static['capabilities'].values())
    for report in c['validator_reports']:
        rp=here/'archived-khronos'/report['report'];assert sha(rp)==report['report_sha256']
        r=json.loads(rp.read_text());assert r['validatorVersion']=='2.0.0-dev.3.10'
        assert r['issues']['numErrors']==r['issues']['numWarnings']==0 and r['issues']['truncated']is False
        assert r['info']['totalTriangleCount']==triangles and r['info']['drawCallCount']==c['meshes']
        assert report['actual_input_sha256'] in [c['raw_sha256'],c['indexed_sha256']]
    controls=mutation_controls(j,b,baseline)
    front_curve=check_front_curve(j['extras']['parameters'])
    return {'pass':True,'detail':mode,'triangles':triangles,'raw_sha256':c['raw_sha256'],'indexed_sha256':c['indexed_sha256'],'protected':protected,'negative_controls':controls,'front_curve':front_curve,'photographic_accepted':False,'world_budget_accepted':False}


def check_near(directory,source_directory):
    return check_detail('near',directory,source_directory)


if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--directory',type=Path,required=True);ap.add_argument('--source-directory',type=Path,default=Path(__file__).resolve().parent);a=ap.parse_args();print(json.dumps(check_near(a.directory,a.source_directory)))
