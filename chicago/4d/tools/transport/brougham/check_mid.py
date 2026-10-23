# SPDX-License-Identifier: GPL-3.0-or-later
"""Exact source-tessellated distance-mid proof; no graphics or world acceptance."""
from pathlib import Path
import collections, copy, hashlib, json, math, struct, sys, time
D=Path(__file__).resolve().parent;ROOT=D.parents[2];ASSET=ROOT/'renderers/web/transport/parked-brougham';sys.path.insert(0,str(D))
from check_near import read, expanded, world_nodes, decoded_bounds, native_contacts
from static_master import static_master_contract
sha=lambda b:hashlib.sha256(b).hexdigest()
def bind_parts(j,b):
    """Resolve all repeated hubcap batches by source order AND complete ranges.
    Never first-match a duplicate mesh name; every native mesh is exhausted once.
    """
    named={};parents={c:i for i,n in enumerate(j['nodes'])for c in n.get('children',[])}
    for i,m in enumerate(j['meshes']):named.setdefault(m['name'],[]).append(i)
    node_for={}
    for i,n in enumerate(j['nodes']):
        if'mesh'in n:assert n['mesh']not in node_for;node_for[n['mesh']]=i
    def path(i):
        return(path(parents[i])if i in parents else[])+[[i,j['nodes'][i]['name']]]
    cursors={};rows=[];exhausted={}
    for pi,p in enumerate(j['extras']['parts']):
        key='surface_'+p['frame']+'_'+str(p['material']);state=cursors.setdefault(key,{'ordinal':0,'next':0})
        if p['triangle_start_in_batch']==0 and state['next']>0:state['ordinal']+=1;state['next']=0
        assert p['triangle_start_in_batch']==state['next'];mi=named[key][state['ordinal']];primitive=j['meshes'][mi]['primitives'][0];assert'indices'not in primitive and primitive['material']==p['material'];chunks={};offsets={}
        for attr in ['POSITION','NORMAL']:
            a=j['accessors'][primitive['attributes'][attr]];v=j['bufferViews'][a['bufferView']];assert a['componentType']==5126 and a['type']=='VEC3'and not v.get('byteStride');off=v.get('byteOffset',0)+a.get('byteOffset',0)+p['triangle_start_in_batch']*36;size=p['triangles']*36;chunk=b[off:off+size];assert len(chunk)==size;chunks[attr]=chunk;offsets[attr]=off
        state['next']+=p['triangles'];exhausted[mi]=state['next'];rows.append({'part_index':pi,'identity':[p['name'],p['frame'],p['material'],p['triangles']],'mesh_index':mi,'node_path':path(node_for[mi]),'chunks':chunks,'offsets':offsets})
    assert len(exhausted)==len(j['meshes'])==25
    for mi,n in exhausted.items():assert j['accessors'][j['meshes'][mi]['primitives'][0]['attributes']['POSITION']]['count']==n*3
    return rows


def contained(outer,inner):
    return all(inner['min'][k]>=outer['min'][k] and inner['max'][k]<=outer['max'][k] for k in range(3))

def verify():
    start=time.monotonic();mcpath=D/'mid-contract.json'
    assert sha(mcpath.read_bytes())=='9f094861d08398d4a2a5e6bba3611c23af98d8db7c73554df1df1ec4950fcab4','Exact reviewed distance-mid contract'
    mc=json.loads(mcpath.read_bytes());c=json.loads((D/'near-contract.json').read_bytes())
    assert sha((ASSET/'MID-BUILD-RECEIPT.json').read_bytes())==mc['build_receipt_sha256']
    assert sha((D/mc['recipe']).read_bytes())==mc['recipe_sha256']=='89a82aac7baf965ab905ca25e7a286129bde1e36f297050bafc65fec6db97159'
    for name,digest in c['source_files'].items():assert sha((D/name).read_bytes())==digest,'Producer/source pin '+name
    for filename,digest,size in [(mc['raw_file'],mc['raw_sha256'],mc['raw_bytes']),(mc['indexed_file'],mc['indexed_sha256'],mc['indexed_bytes'])]:
        raw=(ASSET/filename).read_bytes();assert sha(raw)==digest and len(raw)==size,'Exact reviewed mid '+filename
    for name,digest in mc['archived_current_validator_reports'].items():
        raw=(D/'archived-khronos'/name).read_bytes();assert sha(raw)==digest
        report=json.loads(raw);issues=report['issues'];assert issues['numErrors']==issues['numWarnings']==0 and issues['numInfos']==4 and not issues['truncated']
        assert report['info']['totalTriangleCount']==11706 and report['info']['drawCallCount']==25
    assert sha((ASSET/'brougham-source.glb').read_bytes())==c['raw_sha256']
    assert sha((ASSET/'brougham-near.glb').read_bytes())==c['near_sha256']==mc['unchanged_near_sha256']
    old,ob=read(ASSET/'brougham-source.glb');new,nb=read(ASSET/'brougham-mid-source.glb');indexed,ib=read(ASSET/'brougham-mid.glb');side=json.loads((ASSET/'brougham.json').read_bytes())
    signature,triangles=expanded(new,nb);isig,it=expanded(indexed,ib)
    assert triangles==it==mc['triangles']==11706 and signature==isig==mc['expanded_triangle_PN_sha256']
    row=side['lods'][1];assert row['source_bytes']==mc['raw_bytes'] and row['indexed_bytes']==mc['indexed_bytes'] and row['expanded_triangle_PN_sha256']==signature
    assert row['detail']=='mid' and row['triangles']==11706 and row['source_sha256']==mc['raw_sha256'] and row['indexed_sha256']==mc['indexed_sha256']
    for key in ['nodes','materials','scenes','scene','extensionsUsed']:assert old.get(key)==new.get(key)==indexed.get(key),key
    assert len(new['nodes'])==42 and len(new['materials'])==7 and len(new['meshes'])==25
    for key in old['extras']:
        if key not in ['statistics','parts']:assert old['extras'][key]==new['extras'][key],key
    assert new['extras']['statistics']['triangles']==11706
    for doc in [old,new,indexed]:
        assert not any(doc.get(k) for k in ['images','textures','skins','animations'])
        assert all(set(p['attributes'])=={'POSITION','NORMAL'} for m in doc['meshes'] for p in m['primitives'])
    before=bind_parts(old,ob);after=bind_parts(new,nb);assert len(before)==468 and len(after)==302
    categories=lambda rows:collections.Counter(r['identity'][0] for r in rows)
    bc,nc=categories(before),categories(after);assert set(bc)==set(nc)
    assert {k:(bc[k],nc[k]) for k in bc if bc[k]!=nc[k]}=={'leaf_spring':(160,64),'roof_edge_fascia':(110,40)}
    assert nc['tapered_rounded_spoke']==64 and bc['leaf_spring']//10==nc['leaf_spring']//4==16
    counts=lambda doc:dict(sum((collections.Counter({p['name']:p['triangles']}) for p in doc['extras']['parts']),collections.Counter()))
    actual=counts(new);assert actual==mc['physical_category_triangle_counts'],'Every physical category has its exact reviewed triangle count'
    near_counts=counts(old);changed={name for name,n in actual.items() if near_counts[name]!=n}
    def protected(rows):
        return [(r['identity'],r['node_path'],r['chunks']) for r in rows if r['identity'][0] not in changed]
    assert protected(before)==protected(after),'Unchanged physical feature P/N role streams'
    ow,nw=world_nodes(old),world_nodes(new);assert ow==nw
    assert len(side['anchors'])==13
    for anchor in side['anchors']:assert anchor['node']==new['nodes'][anchor['node_index']]['name'] and anchor['translation_root_m']==nw[anchor['node_index']]
    assert decoded_bounds(old,ob,ow)==decoded_bounds(new,nb,nw)==decoded_bounds(indexed,ib,world_nodes(indexed)),'Exact complete outer bounds'
    assert native_contacts(old,ob)==native_contacts(new,nb)==native_contacts(indexed,ib),'Exact wheel, full pole and shoe contacts'
    near_static=static_master_contract(old,ob,ow,c['raw_sha256']);mid_static=static_master_contract(new,nb,nw,mc['raw_sha256'])
    assert near_static==side['static_master']==c['static_master'],'Production retains original near static interfaces and conservative proxy'
    assert len(near_static['named_targets'])==8 and near_static['named_targets']==mid_static['named_targets']
    outer=near_static['collision_proxy']['components'];inner=mid_static['collision_proxy']['components'];assert len(outer)==len(inner)==9
    changes=[]
    for i,(a,b) in enumerate(zip(outer,inner)):
        assert {k:v for k,v in a.items() if k!='bounds_root_m'}=={k:v for k,v in b.items() if k!='bounds_root_m'}
        assert contained(a['bounds_root_m'],b['bounds_root_m']),'Mid escapes original conservative proxy'
        for bound in ['min','max']:
            for axis in range(3):
                delta=b['bounds_root_m'][bound][axis]-a['bounds_root_m'][bound][axis]
                if delta:changes.append((i,bound,axis,delta))
    assert changes==[(1,'max',1,-0.005755186080932617)],'Only exact reviewed mudguard tight-bound contraction allowed'
    assert -.69*(1-math.cos((math.pi-.2)/(2*(12-1))))<=changes[0][3]<0
    normalized=copy.deepcopy(mid_static);normalized['source_master_sha256']=near_static['source_master_sha256'];normalized['collision_proxy']=copy.deepcopy(near_static['collision_proxy'])
    assert normalized==near_static,'All nonproxy static interface values exact'
    # Controls exercise actual geometry, hierarchy and strict containment without file writes.
    button=next(r for r in reversed(after) if r['identity'][0]=='solid_bright_hub_button');mut=bytearray(nb);off=button['offsets']['POSITION'];struct.pack_into('<f',mut,off,struct.unpack_from('<f',mut,off)[0]+.001)
    mutrows=bind_parts(new,mut);assert [r['part_index'] for a,r in zip(after,mutrows) if a['chunks']!=r['chunks']]==[button['part_index']], 'Repeated hubcap mutation stays bound to its exact final role'
    assert expanded(new,mut)[0]!=signature, 'Actual final repeated hubcap P/N mutation must change geometry signature'
    stable=next(r for r in reversed(after) if r['identity'][0] not in changed);stablemut=bytearray(nb);off=stable['offsets']['POSITION'];struct.pack_into('<f',stablemut,off,struct.unpack_from('<f',stablemut,off)[0]+.001)
    assert protected(bind_parts(new,stablemut))!=protected(before), 'Actual unchanged-category P/N mutation must be detected'
    shifted=copy.deepcopy(new);i=side['anchors'][-1]['node_index'];shifted['nodes'][i]['translation'][0]+=.001;assert world_nodes(shifted)!=nw
    growth=copy.deepcopy(inner[1]['bounds_root_m']);growth['max'][1]=outer[1]['bounds_root_m']['max'][1]+.001;assert not contained(outer[1]['bounds_root_m'],growth)
    assert expanded(old,ob)[1]!=11706,'Near copy cannot pass as distance mid'
    return {'pass':True,'seconds':round(time.monotonic()-start,3),'triangles_before':33502,'triangles_after':triangles,'triangles_saved':33502-triangles,'subdivision_records_before':468,'subdivision_records_after':302,'physical_category_count':len(actual),'materials_exact':7,'nodes_exact':42,'runtime_anchors_exact':13,'static_targets_exact':8,'original_near_proxy_preserved':True,'strict_mid_containment':True,'only_tight_bound_contraction_m':changes[0][3],'candidate_raw_sha256':mc['raw_sha256'],'candidate_indexed_sha256':mc['indexed_sha256'],'negative_controls':{'repeated_hubcap_PN_mutation':True,'unchanged_feature_PN_mutation':True,'anchor_shift':True,'proxy_growth':True,'near_copy_as_mid':True},'world_budget_accepted':False,'photographic_accepted':False}

if __name__=='__main__':print(json.dumps(verify(),indent=2))
