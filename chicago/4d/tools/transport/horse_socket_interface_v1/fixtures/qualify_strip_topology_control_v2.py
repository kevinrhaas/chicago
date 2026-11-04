"""Serialized topology/source qualification for the one unqualified strip draft.

No intersection, deformation, or photographic acceptance is implied.
"""
import argparse
from collections import Counter, defaultdict
import copy
import hashlib
import json
import math
from pathlib import Path
import struct
import sys
import numpy as np


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def cross(a, b):
    return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])


def sub(a, b):
    return tuple(x-y for x,y in zip(a,b))


def area2(a,b,c):
    return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])


def offset(doc, accessor, row):
    a=doc['accessors'][accessor];v=doc['bufferViews'][a['bufferView']]
    components={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a['type']]
    size=components*{5126:4,5123:2,5121:1}[a['componentType']]
    return v.get('byteOffset',0)+a.get('byteOffset',0)+row*v.get('byteStride',size),size


def inspect(doc, binary, parent_doc, parent_binary, original_positions, recipe, anatomy):
    primitive=doc['meshes'][1]['primitives'][0];attrs=primitive['attributes']
    base_primitive=parent_doc['meshes'][1]['primitives'][0]
    p=anatomy.read_attribute(doc,binary,attrs['POSITION'])
    normals=anatomy.read_attribute(doc,binary,attrs['NORMAL'])
    pp=anatomy.read_attribute(parent_doc,parent_binary,attrs['POSITION'])
    uv=anatomy.read_attribute(doc,binary,attrs['TEXCOORD_0'])
    parent_uv=anatomy.read_attribute(parent_doc,parent_binary,base_primitive['attributes']['TEXCOORD_0'])
    repairs=recipe.get('internal_BODY_UV_repairs',[])
    if repairs:
        require(digest(recipe_raw)=='f77e115a340a6cbb8d6efb1b7887c8cdba001a47f493b97be6ffb0eee72dd133','Unsupported chart amendment')
        require(attrs['TEXCOORD_0']==attrs['TEXCOORD_1'],'BODY aliases diverged')
        require(len(repairs)==2 and {r['row']for r in repairs}=={2410,2412},'Unexpected UV repair row')
        require(recipe['maximum_internal_BODY_UV_displacement']==.00030,'UV cap changed')
        for repair in repairs:
            row=repair['row'];parents={2410:[2372,2373,2411],2412:[2374,2375,2413]}[row]
            expected=anatomy.f32([tuple(sum(parent_uv[i][k]for i in parents)/3 for k in range(2))])[0]
            require(repair['preserved_boundary_interpolation_rows']==parents and repair['weights']==[1/3]*3,'Wrong UV interpolation ancestry')
            require(list(parent_uv[row])==repair['old_UV']and list(expected)==repair['new_UV'],'False UV repair declaration')
            require(uv[row]==expected and math.dist(uv[row],parent_uv[row])<=.00030,'Wrong or excessive serialized UV repair')
    require(all(q==parent_uv[i]for i,q in enumerate(uv)if i not in {r['row']for r in repairs}),'Unexpected third BODY UV row changed')
    indices=[r[0]for r in anatomy.read_attribute(doc,binary,primitive['indices'])]
    old_indices=[r[0]for r in anatomy.read_attribute(parent_doc,parent_binary,base_primitive['indices'])]
    triangles=[tuple(indices[i:i+3])for i in range(0,len(indices),3)]
    old_triangles=[tuple(old_indices[i:i+3])for i in range(0,len(old_indices),3)]
    require(len(p)==5595 and len(triangles)==9794,'Body counts changed')
    require(all(all(math.isfinite(x)for x in q)for q in p+normals),'Nonfinite position/normal')
    require(max(math.dist(a,b)for a,b in zip(p,pp))<=.02,'925 displacement cap exceeded')
    require(max(math.dist(a,b)for a,b in zip(p,original_positions))<=.02,'d454 displacement cap exceeded')
    owned=set();removed=set();patches=[];allowed=[]
    weld=lambda q:tuple(round(x,7)for x in q)
    for patch in recipe['patches']:
        faces=set(patch['removed_parent_925_faces']);boundary=patch['boundary_parent_rows']
        used={i for face in faces for i in old_triangles[face]}
        boundary_keys={weld(pp[i])for i in boundary}
        interior={i for i in used if weld(pp[i])not in boundary_keys}
        require(not(removed&faces)and not(owned&interior),'Patch ownership overlap')
        outside={i for f,t in enumerate(old_triangles)if f not in faces for i in t}
        require(not(interior&outside),'An interior row belongs to exterior geometry')
        for repair in repairs:
            if repair['row']in used:
                require(repair['row']in interior and set(repair['preserved_boundary_interpolation_rows'])<=set(boundary),'UV repair escaped its interior/fixed-boundary domain')
        require(all(set(triangles[f])<=used for f in faces),'Replacement references an unowned row')
        require({i for f in faces for i in triangles[f]}==used,'Original source sites were lost')
        edges=defaultdict(list)
        area=0
        for face in faces:
            tri=triangles[face]
            require(len(set(tri))==3,'Repeated vertex in patch triangle')
            signed=area2(*(uv[i]for i in tri))
            require(signed>1e-14,'Patch UV winding/collapse failed')
            area+=signed/2
            for a,b in zip(tri,tri[1:]+tri[:1]):edges[tuple(sorted((a,b)))].append((a,b))
        edge_boundary={e for e,owners in edges.items()if len(owners)==1}
        expected={tuple(sorted((a,b)))for a,b in zip(boundary,boundary[1:]+boundary[:1])}
        require(edge_boundary==expected,'Fixed skin-strip boundary changed')
        require(all(len(owners)in(1,2)for owners in edges.values()),'Nonmanifold patch edge')
        require(all(len(o)==1 or o[0]==o[1][::-1]for o in edges.values()),'Inconsistent patch edge winding')
        require(len(used)-len(edges)+len(faces)==1,'Patch is not a topological disk')
        polygon=sum(uv[a][0]*uv[b][1]-uv[a][1]*uv[b][0]for a,b in zip(boundary,boundary[1:]+boundary[:1]))/2
        require(abs(area-polygon)<1e-12,'Patch UV chart coverage changed')
        for i in interior:
            require(abs(math.sqrt(sum(x*x for x in normals[i]))-1)<1e-5,'Interior normal is not unit length')
            allowed.extend([offset(doc,attrs['POSITION'],i),offset(doc,attrs['NORMAL'],i)])
        for face in faces:
            allowed.extend(offset(doc,primitive['indices'],face*3+k)for k in range(3))
        removed.update(faces);owned.update(interior)
        patches.append({'id':patch['id'],'faces':len(faces),'boundary_rows':len(boundary),'interior_rows':len(interior),'Euler_characteristic':1,'UV_area':area})
    require(len(binary)==len(parent_binary),'Buffer allocation changed')
    allowed.extend(offset(doc,attrs['TEXCOORD_0'],r['row'])for r in repairs)
    mask=bytearray(len(binary))
    for start,size in allowed:mask[start:start+size]=b'\1'*size
    require(all(a==b or mask[i]for i,(a,b)in enumerate(zip(binary,parent_binary))),'Protected exterior/UV/skin/rig/globe/foot bytes changed')
    restored=copy.deepcopy(doc)
    notice=restored['asset']['extras'].pop('chicago4d_upper_lid_strip_v1')
    require(notice['parent_sha256']==digest(parent_raw),'Notice parent binding differs')
    require(notice['recipe_sha256']==digest(recipe_raw),'Notice recipe binding differs')
    for semantic in ('POSITION','NORMAL'):
        i=attrs[semantic]
        for field in ('min','max'):
            require(doc['accessors'][i][field]==[min(row[k]for row in(p if semantic=='POSITION'else normals))if field=='min'else max(row[k]for row in(p if semantic=='POSITION'else normals))for k in range(3)],'Accessor bound does not describe serialized rows')
            restored['accessors'][i][field]=parent_doc['accessors'][i][field]
    require(restored==parent_doc,'Protected JSON/material/rig/metadata changed')
    baseline_edges=defaultdict(list)
    for face,tri in enumerate(old_triangles):
        w=[weld(pp[i])for i in tri]
        for a,b in zip(w,w[1:]+w[:1]):baseline_edges[tuple(sorted((a,b)))].append((face,a,b))
    baseline_exceptions={key:owners for key,owners in baseline_edges.items()if len(owners)!=2 or owners[0][1:]!=owners[1][1:][::-1]}
    edges=defaultdict(list);minimum_area=float('inf')
    for face,tri in enumerate(triangles):
        require(all(0<=i<len(p)for i in tri),'Invalid index')
        q=[p[i]for i in tri];minimum_area=min(minimum_area,math.sqrt(sum(x*x for x in cross(sub(q[1],q[0]),sub(q[2],q[0])))))
        w=[weld(qi)for qi in q]
        require(len(set(w))==3,'Collapsed geometric triangle')
        for a,b in zip(w,w[1:]+w[:1]):edges[tuple(sorted((a,b)))].append((face,a,b))
    require(minimum_area>1e-14,'Collapsed face area')
    exceptions={key:owners for key,owners in edges.items()if len(owners)!=2 or owners[0][1:]!=owners[1][1:][::-1]}
    require(exceptions==baseline_exceptions,'New nonmanifold or incorrectly stitched geometric edge')
    require(not any(face in removed for owners in exceptions.values()for face,_,_ in owners),'Replacement touches a pre-existing exceptional edge')
    points=np.asarray(p);patch_edges={tuple(sorted((a,b)))for face in removed for a,b in zip(triangles[face],triangles[face][1:]+triangles[face][:1])}
    for a,b in patch_edges:
        origin=points[a];direction=points[b]-origin;length2=float(np.dot(direction,direction));parameters=(points-origin)@direction/length2
        distances=np.linalg.norm(points-(origin+parameters[:,None]*direction),axis=1)
        hits=np.where((parameters>1e-6)&(parameters<1-1e-6)&(distances<=1e-8))[0]
        require(not len(hits),'Geometric T-junction on replacement edge '+str((a,b,hits.tolist())))
    return {'patches':patches,'owned_rows':sorted(owned),'removed_faces':sorted(removed),'geometric_edge_incidence':dict(Counter(len(o)for o in edges.values())),'preserved_parent_edge_exceptions':[{'endpoints':key,'source_faces':[o[0]for o in owners]}for key,owners in baseline_exceptions.items()],'minimum_body_double_area_m2':minimum_area,'boundary_exterior_BIN_and_JSON_exact':True,'boundary_exterior_BODY_and_all_EYE_UV_skin_exact':True,'internal_BODY_UV_repairs':repairs,'geometric_T_junctions':0,'T_junction_tolerance_m':1e-8}


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--app-root',type=Path,required=True);parser.add_argument('--recipe',type=Path,required=True);parser.add_argument('--candidate',type=Path,required=True);parser.add_argument('--out',type=Path,required=True);args=parser.parse_args()
    source=args.app_root/'assets/authored/transport/horse_standing';sys.path.insert(0,str(source));import generate_anatomy_v2 as anatomy
    recipe_raw=args.recipe.read_bytes();recipe=json.loads(recipe_raw)
    parent_raw=(source/'horse-sevket-anatomy-v2.glb').read_bytes();parent_doc,parent_binary=anatomy.base.read_glb(parent_raw)
    original_raw=(source/anatomy.base.PARENT_FILE).read_bytes();original_doc,original_binary=anatomy.base.read_glb(original_raw)
    require(digest(parent_raw)==recipe['parent_sha256']and digest(original_raw)==recipe['preserved_original_container_sha256'],'Source binding failed')
    raw=args.candidate.read_bytes();doc,binary=anatomy.base.read_glb(raw)
    require(len(raw)<=4*1024*1024,'4 MiB cap exceeded')
    original_positions=anatomy.read_attribute(original_doc,original_binary,203)
    result=inspect(doc,binary,parent_doc,parent_binary,original_positions,recipe,anatomy)
    result.update(state='STATIC_TOPOLOGY_SOURCE_ONLY_PASS',candidate_sha256=digest(raw),recipe_sha256=digest(recipe_raw),qualifier_sha256=digest(Path(__file__).read_bytes()),proper_crossings='UNRUN',fresh129='UNRUN',images='UNRUN',corruption_controls={})
    attrs=doc['meshes'][1]['primitives'][0]['attributes'];index=doc['meshes'][1]['primitives'][0]['indices']
    controls={}
    tri=min(result['removed_faces']);owned=result['owned_rows'][0]
    reverse=bytearray(binary);start,_=offset(doc,index,tri*3);a,b,c=struct.unpack_from('<HHH',reverse,start);struct.pack_into('<HHH',reverse,start,a,c,b);controls['reversed_owned_triangle']=(doc,reverse)
    flat=[r[0]for r in anatomy.read_attribute(doc,binary,index)];positions=anatomy.read_attribute(doc,binary,attrs['POSITION']);parent_positions=anatomy.read_attribute(parent_doc,parent_binary,attrs['POSITION'])
    eligible=[]
    for start in range(0,len(flat),3):
        t=flat[start:start+3]
        for row in t:
            if row not in result['owned_rows']:continue
            for neighbor in t:
                if row==neighbor:continue
                if math.dist(positions[neighbor],parent_positions[row])<.02 and math.dist(positions[neighbor],original_positions[row])<.02:
                    eligible.append((math.dist(positions[row],positions[neighbor]),row,neighbor))
    require(eligible,'No bounded local collapse control is available')
    _,collapsed_row,other=min(eligible)
    collapse=bytearray(binary);pos_start,_=offset(doc,attrs['POSITION'],collapsed_row);other_start,_=offset(doc,attrs['POSITION'],other);collapse[pos_start:pos_start+12]=binary[other_start:other_start+12];controls['collapsed_owned_position']=(doc,collapse)
    for name,accessor,row in [('outside_position',attrs['POSITION'],0),('source_UV',attrs['TEXCOORD_0'],owned),('source_skin',attrs['WEIGHTS_0'],owned),('foot_position',attrs['POSITION'],5594)]:
        modified=bytearray(binary);start,_=offset(doc,accessor,row);modified[start]^=1;controls[name]=(doc,modified)
    rig=copy.deepcopy(doc);rig['nodes'][0]['name']=rig['nodes'][0].get('name','')+' corrupted';controls['rig_JSON']=(rig,binary)
    dropped=copy.deepcopy(doc);dropped['accessors'][index]['count']-=3;controls['dropped_triangle']=(dropped,binary)
    for name,delta in [('wrong_barycentric_internal_UV',.00001),('excessive_internal_UV',.001)]:
        modified=bytearray(binary);start,_=offset(doc,attrs['TEXCOORD_0'],2410);u,v=struct.unpack_from('<ff',modified,start);struct.pack_into('<ff',modified,start,u+delta,v);controls[name]=(doc,modified)
    eye=bytearray(binary);eye_accessor=doc['meshes'][2]['primitives'][0]['attributes']['TEXCOORD_0'];start,_=offset(doc,eye_accessor,0);eye[start]^=1;controls['separate_EYE_UV']=(doc,eye)
    for name,(test_doc,test_binary)in controls.items():
        try:inspect(test_doc,test_binary,parent_doc,parent_binary,original_positions,recipe,anatomy)
        except (ValueError,IndexError,KeyError)as error:result['corruption_controls'][name]={'refused':True,'reason':str(error)}
        else:raise ValueError('Corruption control was not refused: '+name)
    require((source/'horse-sevket-anatomy-v2.glb').read_bytes()==parent_raw,'App source changed during review')
    args.out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items()if k not in('removed_faces','owned_rows')},indent=2))
