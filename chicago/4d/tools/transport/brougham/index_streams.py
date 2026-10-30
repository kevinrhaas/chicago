# SPDX-License-Identifier: GPL-3.0-or-later
"""Lossless native glTF indexing. No quantization, omitted triangles or external codec."""
from pathlib import Path
import copy,hashlib,json,struct

def read_glb(path):
    raw=Path(path).read_bytes();magic,version,total=struct.unpack_from('<III',raw)
    if (magic,version,total)!=(0x46546c67,2,len(raw)):raise ValueError('Invalid GLB envelope')
    size,kind=struct.unpack_from('<II',raw,12)
    if kind!=0x4e4f534a:raise ValueError('Missing JSON chunk')
    doc=json.loads(raw[20:20+size]);off=20+size;length,kind=struct.unpack_from('<II',raw,off)
    if kind!=0x004e4942:raise ValueError('Missing binary chunk')
    return doc,raw[off+8:off+8+length]

def attribute_rows(doc,binary,index):
    a=doc['accessors'][index];view=doc['bufferViews'][a['bufferView']]
    if a['componentType']!=5126 or a['type']!='VEC3' or a.get('sparse') or view.get('byteStride') not in (None,12):raise ValueError('Expected original packed Float32 VEC3')
    off=view.get('byteOffset',0)+a.get('byteOffset',0)
    return [binary[off+i*12:off+(i+1)*12] for i in range(a['count'])]

def expanded_signature(doc,binary):
    h=hashlib.sha256()
    for mesh in doc['meshes']:
        for prim in mesh['primitives']:
            rows=[attribute_rows(doc,binary,prim['attributes'][k]) for k in ['POSITION','NORMAL']]
            if 'indices' in prim:
                a=doc['accessors'][prim['indices']];v=doc['bufferViews'][a['bufferView']];fmt={5123:'H',5125:'I'}[a['componentType']];off=v.get('byteOffset',0)+a.get('byteOffset',0)
                idx=struct.unpack_from('<'+fmt*a['count'],binary,off)
            else:idx=range(len(rows[0]))
            for i in idx:h.update(rows[0][i]);h.update(rows[1][i])
    return h.hexdigest()

def write_indexed(source,destination):
    original,binary=read_glb(source);doc=copy.deepcopy(original);views=[];access=[];out=bytearray();before=expanded_signature(original,binary)
    def append(data,target):
        out.extend(b'\0'*((-len(out))%4));i=len(views);views.append({'buffer':0,'byteOffset':len(out),'byteLength':len(data),'target':target});out.extend(data);return i
    for mesh in doc['meshes']:
        for prim in mesh['primitives']:
            if 'indices' in prim or set(prim['attributes'])!={'POSITION','NORMAL'}:raise ValueError('Only original nonindexed P/N primitives accepted')
            p=attribute_rows(original,binary,prim['attributes']['POSITION']);n=attribute_rows(original,binary,prim['attributes']['NORMAL'])
            unique={};positions=[];normals=[];indices=[]
            for pp,nn in zip(p,n):
                key=pp+nn
                if key not in unique:unique[key]=len(unique);positions.append(pp);normals.append(nn)
                indices.append(unique[key])
            for key,rows in [('POSITION',positions),('NORMAL',normals)]:
                a=copy.deepcopy(original['accessors'][prim['attributes'][key]]);a['count']=len(rows);a['bufferView']=append(b''.join(rows),34962);a.pop('byteOffset',None);prim['attributes'][key]=len(access);access.append(a)
            fmt,ctype=('H',5123) if len(unique)<=65536 else ('I',5125)
            prim['indices']=len(access);access.append({'bufferView':append(struct.pack('<'+fmt*len(indices),*indices),34963),'componentType':ctype,'count':len(indices),'type':'SCALAR','min':[min(indices)],'max':[max(indices)]})
    doc['bufferViews']=views;doc['accessors']=access;doc['buffers']=[{'byteLength':len(out)}]
    if expanded_signature(doc,out)!=before:raise ValueError('Indexed triangle P/N stream drift')
    encoded=json.dumps(doc,separators=(',',':')).encode();encoded+=b' '*((-len(encoded))%4);out+=b'\0'*((-len(out))%4)
    raw=struct.pack('<III',0x46546c67,2,28+len(encoded)+len(out))+struct.pack('<II',len(encoded),0x4e4f534a)+encoded+struct.pack('<II',len(out),0x004e4942)+out
    Path(destination).write_bytes(raw)
    return {'source_bytes':Path(source).stat().st_size,'indexed_bytes':len(raw),'expanded_triangle_PN_sha256':before,'source_sha256':hashlib.sha256(Path(source).read_bytes()).hexdigest(),'indexed_sha256':hashlib.sha256(raw).hexdigest(),'lossless_indexing':True,'meshopt_or_quantization':False}
