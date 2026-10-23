#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Fresh original W01 pipeline plus portable project charts and CC0 timber pixels.
No cached GLB input; no external model geometry. Photographic acceptance is open.
"""
from pathlib import Path
import argparse,copy,hashlib,json,struct,subprocess,sys,tempfile
ROOT=Path(__file__).resolve().parents[2]
AUTHORED=ROOT/'assets/authored/transport/wagon_parked_fine_wood'
PARENT='274e737b51872983df792d0b24de8e75de8631890a8d586a32d9c6f0066484fb'
EXPECTED='e1e5b4f1d7dfe6bf08cca21e8cfae2e88748a3f6e6c6959753334ae2b0c84dd8'
def need(ok,msg):
 if not ok:raise ValueError(msg)
def sha(x):return hashlib.sha256(x).hexdigest()
def unpack(raw):
 need(struct.unpack_from('<III',raw)==(0x46546c67,2,len(raw)),'Invalid GLB2')
 n,k=struct.unpack_from('<II',raw,12);need(k==0x4e4f534a,'JSON missing');g=json.loads(raw[20:20+n]);sz,k=struct.unpack_from('<II',raw,20+n);need(k==0x004e4942 and 28+n+sz==len(raw),'BIN bounds');return g,raw[28+n:]
def bind_surface(raw,authored=AUTHORED):
 need(sha(raw)==PARENT,'Fresh original baseline differs');g,b=unpack(raw);before=copy.deepcopy(g)
 s=json.loads((authored/'surface.json').read_text());payload=(authored/'surface.bin').read_bytes()
 need(s['schema']=='w01_fine_wood_surface_append_v1'and s['parent_sha256']==PARENT and s['expected_glb_sha256']==EXPECTED,'Unexpected binding');need(sha(payload)==s['payload_sha256'],'Changed payload');need(len(b)==s['parent_binary_bytes'],'Changed prefix length')
 views=s['append_buffer_views'];acc=s['append_accessors'];need(len(views)==38 and len(acc)==32 and len(g['accessors'])==92 and len(g['bufferViews'])==110,'Unexpected append counts')
 image_views={s['images'][i]['bufferView']for i in (0,1,2,9,10,11)};chart_views={a['bufferView']for a in acc}
 need(image_views.isdisjoint(chart_views)and image_views|chart_views==set(range(110,148)),'Unowned append')
 need(all(a['type']in ('VEC2','VEC4','SCALAR')and a['componentType']in (5126,5125)for a in acc),'Only UV/tangent/index chart arrays allowed')
 for v in views:need(v['buffer']==0 and v['byteOffset']>=len(b)and v['byteOffset']+v['byteLength']<=len(b)+len(payload),'Append escapes payload')
 for vi in image_views:
  v=views[vi-110];start=v['byteOffset']-len(b);need(payload[start:start+8]==b'\x89PNG\r\n\x1a\n','Non-PNG image')
 g['bufferViews'].extend(views);g['accessors'].extend(acc);data=b+payload
 need(len(s['meshes'])==len(before['meshes']),'Mesh count changed')
 for original,new in zip(before['meshes'],s['meshes']):
  p=original['primitives'][0];need({k:v for k,v in original.items()if k!='primitives'}=={k:v for k,v in new.items()if k!='primitives'},'Mesh metadata changed')
  if new==original:continue
  need(p['material']in (1,2,3)and len(new['primitives'])==2,'Only wood face ownership may split');indices=[]
  for q in new['primitives']:
   need(q['attributes']['POSITION']==p['attributes']['POSITION']and q['attributes']['NORMAL']==p['attributes']['NORMAL'],'Position/normal reference changed');need(q['material']in (p['material'],p['material']+5),'Changed face material family')
   need(set(q)-{'attributes','indices','material'}==set(p)-{'attributes','indices','material'},'Primitive shape changed')
   ai=q['indices'];need(92<=ai<124,'New project index required');a=g['accessors'][ai];v=g['bufferViews'][a['bufferView']];need(a['type']=='SCALAR'and a['componentType']==5125,'Index type');start=v['byteOffset']+a.get('byteOffset',0);indices+=struct.unpack_from('<'+'I'*a['count'],data,start)
  need(sorted(indices)==list(range(g['accessors'][p['attributes']['POSITION']]['count'])),'Missing/duplicated original rendered vertices')
 for i in (0,4,5):need(s['materials'][i]==before['materials'][i],'Paint/iron changed')
 for i in range(3,9):need(s['images'][i]==before['images'][i],'Paint/iron images changed')
 g['meshes']=s['meshes'];g['textures']=s['textures'];g['materials']=s['materials'];g['images']=s['images'];g['asset']['copyright']=s['asset_copyright'];g['extras']=s['extras'];g['buffers'][0]['byteLength']=len(data)
 for key in ('nodes','skins','animations','scene','scenes','samplers'):need(g.get(key)==before.get(key),'Protected '+key+' changed')
 head=json.dumps(g,separators=(',',':')).encode();head+=b' '*((-len(head))%4);out=struct.pack('<III',0x46546c67,2,28+len(head)+len(data))+struct.pack('<II',len(head),0x4e4f534a)+head+struct.pack('<II',len(data),0x004e4942)+data;need(sha(out)==EXPECTED,'Not exact reviewed material candidate');return out

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--parameters',type=Path,required=True);p.add_argument('--output-dir',type=Path,required=True);p.add_argument('--verify',action='store_true');a=p.parse_args()
 with tempfile.TemporaryDirectory(prefix='w01-fine-wood-source-')as temp:
  subprocess.run([sys.executable,str(ROOT/'tools/transport/generate_parked_wagon.py'),'--parameters',str(a.parameters),'--output-dir',temp],check=True)
  raw=bind_surface((Path(temp)/'wagon-w01.glb').read_bytes())
 target=a.output_dir/'wagon-w01.glb'
 if a.verify:need(target.is_file()and target.read_bytes()==raw,'Stale/missing fine wood output')
 else:target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
 print(json.dumps({'source_regenerated':True,'sha256':sha(raw),'verified':a.verify,'photographic_acceptance':False}))
if __name__=='__main__':main()
