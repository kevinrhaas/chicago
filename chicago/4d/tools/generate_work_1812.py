#!/usr/bin/env python3
"""Generate the original small 1812 work kit from data/humans/work_1812.json.
No Blender, external art or renderer-side geometry. Dimensions are reconstructed.
"""
import json, struct, argparse
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

def generate(data):
    blob = bytearray()
    doc = {'asset': {'version': '2.0', 'generator': 'generate_work_1812.py',
                      'copyright': 'Original reconstructed work kit; CC0-1.0'},
           'scene': 0, 'scenes': [{'nodes': [0]}], 'nodes': [{'name': 'work_1812', 'children': [1, 2]},
             {'name': 'work_chest', 'children': []}, {'name': 'work_hammer', 'children': []}],
           'meshes': [], 'accessors': [], 'bufferViews': [], 'buffers': [],
           'materials': [{'name': 'weathered_wood', 'pbrMetallicRoughness': {'baseColorFactor': [.32,.22,.12,1], 'roughnessFactor': .95, 'metallicFactor': 0}},
             {'name': 'end_grain', 'pbrMetallicRoughness': {'baseColorFactor': [.40,.29,.16,1], 'roughnessFactor': .95, 'metallicFactor': 0}},
             {'name': 'forged_iron', 'pbrMetallicRoughness': {'baseColorFactor': [.12,.13,.14,1], 'roughnessFactor': .72, 'metallicFactor': .6}}]}
    def accessor(values, width, component=5126):
        while len(blob) % 4: blob.append(0)
        start = len(blob); kind = 'f' if component == 5126 else 'H'
        blob.extend(struct.pack('<' + kind * len(values), *values))
        view = len(doc['bufferViews']); doc['bufferViews'].append({'buffer':0,'byteOffset':start,'byteLength':len(blob)-start})
        a = {'bufferView':view,'componentType':component,'count':len(values)//width,'type':{1:'SCALAR',3:'VEC3'}[width]}
        if width == 3:
            a['min'] = [min(values[i::3]) for i in range(3)]; a['max'] = [max(values[i::3]) for i in range(3)]
        idx = len(doc['accessors']); doc['accessors'].append(a); return idx
    buckets = {}
    def box(name, centre, size, material, parent):
        # Four independently normalled vertices per face, outward CCW winding.
        faces = [((1,0,0), [(1,-1,-1),(1,1,-1),(1,1,1),(1,-1,1)]),
                 ((-1,0,0), [(-1,-1,1),(-1,1,1),(-1,1,-1),(-1,-1,-1)]),
                 ((0,1,0), [(-1,1,-1),(-1,1,1),(1,1,1),(1,1,-1)]),
                 ((0,-1,0), [(-1,-1,1),(-1,-1,-1),(1,-1,-1),(1,-1,1)]),
                 ((0,0,1), [(1,-1,1),(1,1,1),(-1,1,1),(-1,-1,1)]),
                 ((0,0,-1), [(-1,-1,-1),(-1,1,-1),(1,1,-1),(1,-1,-1)])]
        pos=[]; normal=[]; indices=[]
        for n, verts in faces:
            i=len(pos)//3
            for v in verts:
                pos.extend(centre[j]+v[j]*size[j]/2 for j in range(3)); normal.extend(n)
            indices.extend([i,i+1,i+2,i,i+2,i+3])
        bucket=buckets.setdefault((parent,material),{'pos':[],'normal':[],'indices':[],'parts':[]})
        offset=len(bucket['pos'])//3;bucket['pos'].extend(pos);bucket['normal'].extend(normal)
        bucket['indices'].extend(i+offset for i in indices);bucket['parts'].append(name)
    g=data['geometry'];c=g['chest'];w,d,h,z,t=(c[k] for k in ['width_m','depth_m','height_m','centre_z_m','board_thickness_m'])
    for j in range(4):
        y=(j+.5)*h/4
        for sign in [-1,1]:
            box(f'wall_front_back_{sign}_{j}',[0,y,z+sign*(d/2-t/2)],[w,h/4-.004,t],j%2,1)
            box(f'wall_end_{sign}_{j}',[sign*(w/2-t/2),y,z],[t,h/4-.004,d-2*t],(j+1)%2,1)
    for j in range(3):
        box(f'lid_plank_{j}',[-w/2+(j+.5)*w/3,h+t/2,z],[w/3-.004,t,d],j%2,1)
    for sign in [-1,1]:
        box(f'underside_batten_{sign}',[sign*w*.32,h-t,z],[.045,t,d-.02],0,1)
    # The target nail is on the visible top, clear of the steadying left hand.
    contact=g['contact_local'];box('target_nail',[contact[0],contact[1]-.0015,contact[2]],[.009,.003,.009],2,1)
    hammer=g['hammer'];length=hammer['handle_m'];width=hammer['handle_width_m']
    box('hammer_handle',[0,length/2,0],[width,length,width*.8],1,2)
    box('hammer_head',[0,length,0],hammer['head_m'],2,2)
    # Five material batches, rather than a draw call for every plank.
    for (parent,material),b in buckets.items():
        name=f"{doc['nodes'][parent]['name']}_{doc['materials'][material]['name']}"
        mesh=len(doc['meshes']);doc['meshes'].append({'name':name,'primitives':[{'attributes':{'POSITION':accessor(b['pos'],3),'NORMAL':accessor(b['normal'],3)},'indices':accessor(b['indices'],1,5123),'material':material}]})
        node=len(doc['nodes']);doc['nodes'].append({'name':name,'mesh':mesh,'extras':{'parts':b['parts']}});doc['nodes'][parent]['children'].append(node)
    # Named measured markers, never rendered proxy sources.
    for name,at,parent in [('work_contact',contact,1),('hammer_strike',hammer['strike_local'],2)]:
        idx=len(doc['nodes']);doc['nodes'].append({'name':name,'translation':at});doc['nodes'][parent]['children'].append(idx)
    while len(blob)%4:blob.append(0)
    doc['buffers']=[{'byteLength':len(blob)}]
    js=json.dumps(doc,separators=(',',':')).encode();js+=b' '*((-len(js))%4)
    return struct.pack('<III',0x46546c67,2,28+len(js)+len(blob))+struct.pack('<II',len(js),0x4e4f534a)+js+struct.pack('<II',len(blob),0x004e4942)+blob

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,default=ROOT/'assets/props/work_1812.glb');args=ap.parse_args()
    data=json.loads((ROOT/'data/humans/work_1812.json').read_text());body=generate(data)
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_bytes(body)
    print(f'work_1812: {len(body)} bytes -> {args.output}')
if __name__=='__main__':main()
