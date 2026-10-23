"""Bounded native proof for this one ring16 candidate; no app writes or graphics."""
from pathlib import Path
import copy, datetime, hashlib, json, struct, sys, time
D=Path(__file__).resolve().parent; ROOT=D.parents[2]; ASSET=ROOT/'renderers/web/transport/parked-brougham';sys.path.insert(0,str(D))
from check_near import read, values, expanded, world_nodes, decoded_bounds, native_contacts
from static_master import static_master_contract
OWNED={'rounded_iron_tire','slender_painted_felloe','rounded_hub','bright_hubcap_rim'}
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

def protected(rows):
    h=hashlib.sha256();count=0
    for row in rows:
        if row['identity'][0]in OWNED:continue
        h.update(json.dumps([row['part_index'],row['identity'],row['node_path']],separators=(',',':')).encode())
        for attr in ['POSITION','NORMAL']:h.update(row['chunks'][attr])
        count+=1
    assert count==452
    return h.hexdigest()

def verify():
    mid_contract=D/'mid-contract.json';assert sha(mid_contract.read_bytes())=='308d2774e5dbfaf0835a0a11f0c05f07e350632c5863311c7e519d09eb175960'
    mc=json.loads(mid_contract.read_bytes())
    assert sha((ASSET/'MID-BUILD-RECEIPT.json').read_bytes())==mc['build_receipt_sha256']
    for filename,digest,size in [(mc['raw_file'],mc['raw_sha256'],mc['raw_bytes']),(mc['indexed_file'],mc['indexed_sha256'],mc['indexed_bytes'])]:
        p=ASSET/filename;assert sha(p.read_bytes())==digest and p.stat().st_size==size
    for name,digest in mc['archived_current_validator_reports'].items():assert sha((D/'archived-khronos'/name).read_bytes())==digest
    start=time.monotonic();old,ob=read(ASSET/'brougham-source.glb');new,nb=read(ASSET/'brougham-mid-source.glb');indexed,ib=read(ASSET/'brougham-mid.glb');side=json.loads((ASSET/'brougham.json').read_bytes());c=json.loads((D/'near-contract.json').read_bytes())
    assert sha((ASSET/'brougham-source.glb').read_bytes())==c['raw_sha256']
    assert sha((ASSET/'brougham-near.glb').read_bytes())==c['near_sha256']
    midrow=side['lods'][1]; assert midrow['detail']=='mid' and midrow['triangles']==22238
    assert midrow['source_sha256']==sha((ASSET/'brougham-mid-source.glb').read_bytes())
    assert midrow['indexed_sha256']==sha((ASSET/'brougham-mid.glb').read_bytes())
    assert sha((D/'ring16-mid-lods.json').read_bytes())=='d7dd2cc647ad095c4fef148e5f8db88ddeb1b74fab7878dc547f8e4a30b5100d'
    for name in ['KHRONOS-MID-RAW.json','KHRONOS-MID.json']:
        report=json.loads((D/'archived-khronos'/name).read_bytes()); issues=report['issues']
        assert issues['numErrors']==issues['numWarnings']==0 and issues['numInfos']==4 and not issues['truncated']
        assert report['info']['totalTriangleCount']==22238

    sig,t=expanded(new,nb);isig,it=expanded(indexed,ib);assert t==it==22238 and sig==isig
    for key in ['nodes','materials','scenes','scene','extensionsUsed']:assert old.get(key)==new.get(key)==indexed.get(key),key
    assert len(new['nodes'])==42 and len(new['materials'])==7 and len(new['meshes'])==25
    for key in old['extras']:
        if key not in ['statistics','parts']:assert old['extras'][key]==new['extras'][key],key
    assert new['extras']['statistics']['triangles']==22238
    for doc in [old,new,indexed]:
        assert not any(doc.get(k)for k in ['images','textures','skins','animations'])
        assert all(set(p['attributes'])=={'POSITION','NORMAL'}for m in doc['meshes']for p in m['primitives'])
    before=bind_parts(old,ob);after=bind_parts(new,nb);assert len(before)==len(after)==468
    owned=[]
    for a,b in zip(before,after):
        assert a['part_index']==b['part_index']and a['identity'][:3]==b['identity'][:3]and a['node_path']==b['node_path']
        if a['identity'][0]in OWNED:
            assert b['identity'][3]==256 and a['identity'][3]in[640,1280];assert any(a['chunks'][k]!=b['chunks'][k]for k in ['POSITION','NORMAL']);owned.append({'part_index':a['part_index'],'identity':a['identity'][:3],'before':a['identity'][3],'after':b['identity'][3],'node_path':a['node_path']})
        else:assert a['identity']==b['identity']and a['chunks']==b['chunks'],'Protected actual part changed'
    assert len(owned)==16 and sum(p['before']for p in owned)==15360 and sum(p['after']for p in owned)==4096
    assert protected(before)==protected(after)
    ow,nw=world_nodes(old),world_nodes(new);assert ow==nw
    for anchor in side['anchors']:assert anchor['node']==new['nodes'][anchor['node_index']]['name']and anchor['translation_root_m']==nw[anchor['node_index']]
    assert len(side['anchors'])==13
    before_bounds=decoded_bounds(old,ob,ow);after_bounds=decoded_bounds(new,nb,nw);assert before_bounds==after_bounds==decoded_bounds(indexed,ib,world_nodes(indexed))
    contacts=native_contacts(new,nb);assert contacts==native_contacts(old,ob)==native_contacts(indexed,ib)
    contract=static_master_contract(new,nb,nw,sha((ASSET/'brougham-mid-source.glb').read_bytes()));oldcontract=copy.deepcopy(side['static_master']);oldcontract['source_master_sha256']=contract['source_master_sha256'];assert contract==oldcontract
    # Actual controls use only in-memory copies. Last repeated hubcap must be
    # read through its own role, not through the first duplicate mesh name.
    button=next(p for p in reversed(after)if p['identity'][0]=='solid_bright_hub_button');mut=bytearray(nb);off=button['offsets']['POSITION'];value=struct.unpack_from('<f',mut,off)[0];struct.pack_into('<f',mut,off,value+.001);assert protected(bind_parts(new,mut))!=protected(before)
    anchor_doc=copy.deepcopy(new);anchor_index=side['anchors'][-1]['node_index'];anchor_doc['nodes'][anchor_index]['translation'][0]+=.001;assert world_nodes(anchor_doc)!=nw
    assert expanded(old,ob)[1]!=22238,'A near copy cannot satisfy the genuine mid count'
    result={'pass':True,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'seconds':round(time.monotonic()-start,3),'scope':'Native generated ring16 source/indexed candidate only; not appearance/runtime/half-pixel/world/budget acceptance','baseline_raw_sha256':c['raw_sha256'],'baseline_near_sha256':c['near_sha256'],'candidate_raw_sha256':sha((ASSET/'brougham-mid-source.glb').read_bytes()),'candidate_indexed_sha256':sha((ASSET/'brougham-mid.glb').read_bytes()),'candidate_expanded_PN_sha256':sig,'triangles_before':33502,'triangles_after':t,'triangles_saved':33502-t,'changed_parts':owned,'protected_other_parts':452,'protected_nonring_PN_role_mapped_sha256':protected(after),'duplicate_hubcap_batches_bound_by_role_and_fully_exhausted':True,'materials_exact':7,'hierarchy_nodes_exact':42,'native_meshes':25,'anchors_exact':13,'UV_status':'No UV/texture streams exist in either asset; exact P/N-only attribute sets retained','full_bounds_exact':after_bounds,'native_contacts_exact':contacts,'static_master_only_source_hash_changes':True,'negative_controls':{'actual_last_hubcap_nonring_position_mutation_detected':True,'actual_anchor_translation_mutation_detected':True,'unchanged_near_rejected_as_mid':True},'near_geometry_or_active_app_edits':0,'browser_launched':False,'photographic_acceptance':False,'runtime_budget_acceptance':False,'half_pixel_policy_accepted':False}
    return result
if __name__=='__main__':
 r=verify();print(json.dumps({k:r[k]for k in ['pass','seconds','triangles_before','triangles_after','triangles_saved','protected_other_parts','materials_exact','anchors_exact','candidate_raw_sha256','candidate_indexed_sha256']},indent=2))
