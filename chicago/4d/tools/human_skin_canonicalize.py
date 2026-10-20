#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Consolidate exactly equivalent skins in authored GLB exports. Stdlib only.
No bone transform, inverse bind matrix, vertex, weight or animation is repaired.
Default single-skin requirement rejects distinct palettes instead of guessing.
"""
import argparse,copy,json,math,pathlib,struct
IDENTITY=tuple(1.0 if i%5==0 else 0.0 for i in range(16))
def nonnegative(value,label):
    if not isinstance(value,int) or isinstance(value,bool) or value<0:raise ValueError('invalid '+label)
    return value
def item(items,index,label):
    index=nonnegative(index,label)
    if index>=len(items):raise ValueError('invalid '+label)
    return items[index]
def read_glb(raw):
    if len(raw)<28 or struct.unpack_from('<III',raw)!=(0x46546c67,2,len(raw)):
        raise ValueError('invalid GLB header')
    length,kind=struct.unpack_from('<II',raw,12)
    if kind!=0x4e4f534a or 20+length+8>len(raw):raise ValueError('invalid JSON chunk')
    doc=json.loads(raw[20:20+length]);tail=raw[20+length:]
    size,kind=struct.unpack_from('<II',tail)
    if kind!=0x004e4942 or size+8!=len(tail):raise ValueError('expected one complete embedded BIN chunk')
    return doc,tail

def inverse_bind_matrices(doc,binary,skin):
    count=len(skin['joints'])
    if 'inverseBindMatrices' not in skin:return (IDENTITY,)*count
    a=item(doc['accessors'],skin['inverseBindMatrices'],'IBM accessor')
    if a.get('type')!='MAT4' or a.get('componentType')!=5126 or nonnegative(a.get('count'),'IBM count')!=count or 'sparse' in a or a.get('normalized') or a.get('extensions'):
        raise ValueError('IBM must be finite embedded nonsparse float32 MAT4, one per ordered joint')
    view=item(doc['bufferViews'],a['bufferView'],'IBM buffer view')
    buffer=item(doc['buffers'],view.get('buffer',0),'IBM buffer')
    if view.get('buffer',0)!=0 or 'uri' in buffer or view.get('extensions') or buffer.get('extensions'):raise ValueError('external or extended IBM buffer is unsupported')
    stride=nonnegative(view.get('byteStride',64),'IBM stride');start=nonnegative(view.get('byteOffset',0),'IBM view offset');offset=start+nonnegative(a.get('byteOffset',0),'IBM accessor offset')
    view_end=start+nonnegative(view['byteLength'],'IBM view length');buffer_end=nonnegative(buffer['byteLength'],'IBM buffer length')
    if stride<64 or stride%4 or offset%4:raise ValueError('invalid IBM stride or alignment')
    if offset+max(0,count-1)*stride+64>min(view_end,buffer_end,len(binary)):raise ValueError('IBM escapes buffer view')
    result=tuple(struct.unpack_from('<16f',binary,offset+i*stride) for i in range(count))
    if not all(math.isfinite(v) for row in result for v in row):raise ValueError('non-finite IBM')
    return result

def binding(doc,binary,skin):
    # Keep ordered NODE identities, skeleton root, name and any extras/extensions.
    # Differing names are not required for rendering, but refusing avoids losing metadata.
    metadata={k:v for k,v in skin.items() if k!='inverseBindMatrices'}
    return metadata,inverse_bind_matrices(doc,binary,skin)

def encode(doc,tail):
    j=json.dumps(doc,separators=(',',':')).encode();j+=b' '*((-len(j))%4)
    return struct.pack('<III',0x46546c67,2,20+len(j)+len(tail))+struct.pack('<II',len(j),0x4e4f534a)+j+tail

def diagnostics(raw):
    doc,tail=read_glb(raw);nodes=doc.get('nodes',[]);scales=[]
    for i,node in enumerate(nodes):
        if 'matrix' in node:
            m=node['matrix'];scale=[math.sqrt(sum(m[c*4+r]**2 for r in range(3))) for c in range(3)]
        else:scale=node.get('scale',[1,1,1])
        residual=max(abs(v-1) for v in scale)
        if residual:scales.append({'node_index':i,'node':node.get('name'),'scale':scale,'max_unit_scale_residual':residual})
    skins=[]
    for i,skin in enumerate(doc.get('skins',[])):
        skins.append({'skin_index':i,'name':skin.get('name'),'skeleton':skin.get('skeleton'),'joint_indices':skin['joints'],'joint_names':[nodes[j].get('name') for j in skin['joints']],'inverse_bind_matrices_accessor':skin.get('inverseBindMatrices'),'inverse_bind_matrices':inverse_bind_matrices(doc,tail[8:],skin)})
    return {'skin_count':len(skins),'skins':skins,'nonunit_node_scales':scales,'maximum_unit_scale_residual':max((r['max_unit_scale_residual'] for r in scales),default=0),'mesh_skin_references':[{'node_index':i,'name':n.get('name'),'mesh':n.get('mesh'),'skin':n['skin']} for i,n in enumerate(nodes) if 'skin'in n]}

def consolidate(raw,require_single_skin=True):
    doc,tail=read_glb(raw);original=doc.get('skins',[])
    if not original:raise ValueError('no skins')
    palettes=[];unique=[];remap={}
    for i,skin in enumerate(original):
        joints=skin.get('joints')
        if not isinstance(joints,list) or not joints or any(not isinstance(j,int) or isinstance(j,bool) or j<0 or j>=len(doc.get('nodes',[])) for j in joints):raise ValueError('invalid joint node references')
        candidate=binding(doc,tail[8:],skin)
        match=next((j for j,p in enumerate(palettes) if p==candidate),None)
        if match is None:match=len(unique);unique.append(skin);palettes.append(candidate)
        remap[i]=match
    if require_single_skin and len(unique)!=1:
        raise ValueError(f'{len(unique)} distinct skin palettes remain: ordered joint nodes, skin properties or actual inverse bind matrices differ; refusing single-skin normalization')
    for node in doc.get('nodes',[]):
        if 'skin'in node:
            if node['skin'] not in remap:raise ValueError('invalid mesh skin reference')
            node['skin']=remap[node['skin']]
    doc['skins']=unique
    return encode(doc,tail),{'input_skin_count':len(original),'output_skin_count':len(unique),'skin_reference_remap':remap,'comparison':'exact ordered actual joint node identities, all skin metadata, decoded IBM values','binary_bytes_preserved':True}

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('input',type=pathlib.Path);parser.add_argument('output',type=pathlib.Path,nargs='?');parser.add_argument('--diagnostics',type=pathlib.Path);args=parser.parse_args();raw=args.input.read_bytes()
    if args.output:
        if args.output.resolve()==args.input.resolve():parser.error('input/output must differ; do not overwrite before review')
        result,receipt=consolidate(raw);args.output.write_bytes(result)
    else:receipt={'diagnostics_only':True}
    if args.diagnostics:args.diagnostics.write_text(json.dumps({'before':diagnostics(raw),'after':diagnostics(result) if args.output else None,'receipt':receipt},indent=2)+'\n')
    print(json.dumps(receipt))
if __name__=='__main__':main()
