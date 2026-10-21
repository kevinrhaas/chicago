#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Deterministic original finish variant; no geometry or historical claims."""
from pathlib import Path
import argparse, hashlib, json, struct, copy
from generate_tiles import make_tiles

PARENT_SHA = '0138ad2565f3e8b08029ef788c5196c65c80c79643313e944c726b993ff31ee4'
def need(value, message):
    if not value:
        raise ValueError(message)
def sha(data):
    return hashlib.sha256(data).hexdigest()
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--parent',type=Path,required=True)
    parser.add_argument('--parameters',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    raw=args.parent.read_bytes(); need(sha(raw)==PARENT_SHA,'Exact parent required')
    config=json.loads(args.parameters.read_text())
    args.output.mkdir(exist_ok=False)
    size=struct.unpack_from('<I',raw,12)[0]
    g=json.loads(raw[20:20+size]); original=copy.deepcopy(g)
    oldbin=raw[28+size:]; binary=bytearray(oldbin)
    reports=make_tiles(config['tiles'],args.output/'textures')
    for family in ['wood','paint','iron']:
        for kind in ['color','normal','orm']:
            data=(args.output/'textures'/(family+'_'+kind+'.png')).read_bytes()
            binary.extend(b'\0'*((-len(binary))%4))
            view=len(g['bufferViews']);g['bufferViews'].append({'buffer':0,'byteOffset':len(binary),'byteLength':len(data)})
            binary.extend(data)
            image=next(t['source'] for i,t in enumerate(g['textures']) if i==(['wood','paint','iron'].index(family)*3+['color','normal','orm'].index(kind)))
            g['images'][image]={'bufferView':view,'mimeType':'image/png'}
    for material in g['materials']:
        name=material['name']
        material['pbrMetallicRoughness']['baseColorFactor']=config['base_color_factors'][name]
        material['extras']={**material.get('extras',{}),'finish_grade':'Original reconstructed weathering/color; no identified Chicago specimen or measured finish', 'finish_variant':'parked_weathered_v1'}
    # Same metric grain UVs, normals, positions, indices, nodes, sockets and rig.
    for mesh, before in zip(g['meshes'],original['meshes']):
        need(mesh==before,'Geometry/accessor references must remain exact')
    for key in ['accessors','nodes','skins','animations','scenes']:
        need(g.get(key)==original.get(key),'Protected '+key+' changed')
    need(bytes(binary[:len(oldbin)])==oldbin,'Protected old binary changed')
    g['extras']['finish_variant']={'id':'parked_weathered_v1','scope':'Original optical reconstruction; no photographic or period-finish acceptance', 'parent_sha256':PARENT_SHA,'recipe_sha256':sha(args.parameters.read_bytes())}
    binary.extend(b'\0'*((-len(binary))%4));g['buffers'][0]['byteLength']=len(binary)
    head=json.dumps(g,separators=(',',':')).encode();head+=b' '*((-len(head))%4)
    out=struct.pack('<III',0x46546c67,2,28+len(head)+len(binary))+struct.pack('<II',len(head),0x4e4f534a)+head+struct.pack('<II',len(binary),0x004e4942)+binary
    (args.output/'wagon-w01.glb').write_bytes(out)
    receipt={'parent_sha256':PARENT_SHA,'sha256':sha(out),'old_binary_prefix_exact':True,'protected_geometry_accessors_nodes_skins_animations_exact':True,'textures':reports,'triangles':12104,'draw_batches':23,'estimated_texture_RGBA8_mips_bytes':sum(v['decoded_RGBA8_mips_bytes_estimate'] for v in reports.values()),'status':'unaccepted original finish variant; actual comparison required'}
    (args.output/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps({k:v for k,v in receipt.items() if k!='textures'}))
if __name__=='__main__':
    main()
