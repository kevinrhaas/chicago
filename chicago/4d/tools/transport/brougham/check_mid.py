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
    assert len(exhausted)==len(j['meshes']) # exhaust every real batch; count is pinned by the current contract
    for mi,n in exhausted.items():assert j['accessors'][j['meshes'][mi]['primitives'][0]['attributes']['POSITION']]['count']==n*3
    return rows


def contained(outer,inner):
    return all(inner['min'][k]>=outer['min'][k] and inner['max'][k]<=outer['max'][k] for k in range(3))

def check_mid_provenance(side,near,mid):
    p=side['mid_provenance']
    assert side['revision']=='v19_catalogue_body_and_finish_near_mid_study'
    assert p['source_master_near_sha256']==near['raw_sha256']
    assert p['distance_lod_native_appearance_accepted']is side['lod_appearance_accepted']['mid']is False
    assert p['photographic_accepted']is False and p['world_budget_accepted']is False
    assert p['current_near_triangles']==near['triangles'] and p['current_mid_triangles']==mid['triangles']


def verify():
    from check_near import check_detail
    from body_geometry import part_rows
    near=json.loads((D/'near-contract.json').read_text());mid=json.loads((D/'mid-contract.json').read_text())
    result=check_detail('mid',ASSET,D)
    a,ab=read(ASSET/near['raw_file']);b,bb=read(ASSET/mid['raw_file'])
    side=json.loads((ASSET/'brougham.json').read_text());check_mid_provenance(side,near,mid)
    assert side['source_master_sha256']==near['raw_sha256']
    assert side['mid_provenance']['build_receipt_sha256']==sha((ASSET/'MID-BUILD-RECEIPT.json').read_bytes())
    assert side['mid_provenance']['recipe_sha256']==sha((D/'ring16-mid-lods.json').read_bytes())
    assert a['materials']==b['materials'] and a['extensionsUsed']==b['extensionsUsed']
    before,after=part_rows(a,ab),part_rows(b,bb)
    categories=lambda rows:collections.Counter(key[0]for key in rows)
    bc,nc=categories(before),categories(after)
    assert set(bc)==set(nc), 'Every physical feature family retained'
    assert {name:(bc[name],nc[name])for name in bc if bc[name]!=nc[name]}=={'leaf_spring':(160,64),'roof_edge_fascia':(110,40)}, 'Only original tessellation-record count changes'
    totals=lambda rows:dict(sum((collections.Counter({key[0]:row['triangles']})for key,row in rows.items()),collections.Counter()))
    bt,nt=totals(before),totals(after)
    changed_categories={name for name in bt if bt[name]!=nt[name]}
    protected=lambda rows:{key:row for key,row in rows.items()if key[0]not in changed_categories}
    assert protected(before)==protected(after), 'Exact P/N for every unchanged physical occurrence'
    assert near['triangles']>mid['triangles'] and near['expanded_PN_sha256']!=mid['expanded_PN_sha256'], 'Near copy cannot stand in for real mid'
    def counts(doc):return dict(sum((collections.Counter({p['name']:p['triangles']})for p in doc['extras']['parts']),collections.Counter()))
    assert counts(a)==near['physical_category_triangle_counts'] and counts(b)==mid['physical_category_triangle_counts']
    assert native_contacts(a,ab)==native_contacts(b,bb)
    assert bc['tapered_rounded_spoke']==nc['tapered_rounded_spoke']==64, 'All64 original spoke occurrences retained; only their original tessellation differs'
    assert len(a['extras']['parts'])==481 and len(b['extras']['parts'])==315
    outer=near['static_master']['collision_proxy']['components'];inner=mid['static_master']['collision_proxy']['components']
    assert len(outer)==len(inner)==9
    contractions=[]
    for i,(a,b)in enumerate(zip(outer,inner)):
        assert a['source_frame']==b['source_frame'] and contained(a['bounds_root_m'],b['bounds_root_m']), 'Mid stays in original near proxy'
        for bound in ['min','max']:
            for axis in range(3):
                delta=b['bounds_root_m'][bound][axis]-a['bounds_root_m'][bound][axis]
                if delta:contractions.append((i,bound,axis,delta))
    assert contractions==[(1,'max',1,-0.005755186080932617)], 'Only original V18 tight mudguard contraction'
    result.update(near_triangles=near['triangles'],mid_triangles=mid['triangles'],all_physical_occurrences_preserved=True,strict_mid_proxy_containment=True)
    return result


if __name__=='__main__':print(json.dumps(verify(),indent=2))
