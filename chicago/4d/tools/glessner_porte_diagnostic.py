"""Export the same carriage leaves in a closed review pose, without changing the scene.

python3 tools/glessner_porte_diagnostic.py --out /tmp/porte
Uses the canonical master's existing oak/iron materials; no source-photo pixels.
The output is a diagnostic, not a published building asset or camera calibration.
"""
import argparse, sys, math, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'generators'))
from archetypes.masonry_house_params import from_phase
from archetypes import masonry_house_v4_porte as m
r=json.loads((ROOT/'data/structures/glessner_house.json').read_text())
p=from_phase(r['phases'][0],r)
o=next(o for o in p.openings if o.get('style')=='porte_cochere')
parser=argparse.ArgumentParser();parser.add_argument('--out',required=True)
args=parser.parse_args();outdir=Path(args.out);outdir.mkdir(parents=True,exist_ok=True)
class B:
 def __init__(self,reduced):self.params=p;self.smooth_rock_faces=not reduced

import struct,copy,os
class Capture(B):
 def __init__(self,reduced):super().__init__(reduced);self.verts=[];self.roof_uvs={};self.faces=[]
 def raw(self,ps,c,mat,want):
  a,b,c=ps[:3];v=[b[i]-a[i] for i in range(3)];w=[c[i]-a[i] for i in range(3)];n=[v[1]*w[2]-v[2]*w[1],v[2]*w[0]-v[0]*w[2],v[0]*w[1]-v[1]*w[0]]
  if sum(n[i]*want[i] for i in range(3))<0:ps=list(reversed(ps))
  ids=list(range(len(self.verts),len(self.verts)+len(ps)));self.verts.extend(ps);self.faces.append((ids,mat));return ids
src=(ROOT/'assets/gltf/glessner_house__as_built_1887.glb').read_bytes();jlen=struct.unpack_from('<I',src,12)[0];doc=json.loads(src[20:20+jlen]);oldbuf=src[28+jlen:]
for reduced in (False,True):
 b=Capture(reduced);m.build(b,o,0)
 out={'asset':{'version':'2.0'},'scenes':[{'nodes':[0]}],'scene':0,'nodes':[{'mesh':0}],'meshes':[{'primitives':[]}],'materials':copy.deepcopy([doc['materials'][6],doc['materials'][10]]),'samplers':doc.get('samplers',[]),'textures':[],'images':[],'accessors':[],'bufferViews':[],'buffers':[{}]};buf=bytearray()
 def view(data,target=None):
  while len(buf)%4:buf.append(0)
  v={'buffer':0,'byteOffset':len(buf),'byteLength':len(data)}
  if target:v['target']=target
  out['bufferViews'].append(v);buf.extend(data);return len(out['bufferViews'])-1
 texmap={}
 def texture(old):
  if old in texmap:return texmap[old]
  t=copy.deepcopy(doc['textures'][old]);im=doc['images'][t['source']];v=doc['bufferViews'][im['bufferView']];off=v.get('byteOffset',0)
  out['images'].append({'bufferView':view(oldbuf[off:off+v['byteLength']]),'mimeType':im['mimeType']})
  t['source']=len(out['images'])-1;out['textures'].append(t);texmap[old]=len(out['textures'])-1;return texmap[old]
 def remap(x):
  for k,v in x.items():
   if k.endswith('Texture') and isinstance(v,dict) and 'index' in v:v['index']=texture(v['index'])
   elif isinstance(v,dict):remap(v)
 for mat in out['materials']:remap(mat)
 for mat in (6,10):
  pos=[];norm=[];uv=[]
  for ids,mi in b.faces:
   if mi!=mat:continue
   for j in range(1,len(ids)-1):
    ix=[ids[0],ids[j],ids[j+1]];ps=[b.verts[i] for i in ix]
    a,c,d=ps;v=[c[i]-a[i] for i in range(3)];w=[d[i]-a[i] for i in range(3)];n=m.unit((v[1]*w[2]-v[2]*w[1],v[2]*w[0]-v[0]*w[2],v[0]*w[1]-v[1]*w[0]))
    for i,(x,y,z) in zip(ix,ps):
     pos.extend([x,z,-y]);norm.extend([n[0],n[2],-n[1]]);u,v=b.roof_uvs.get(i,(y,z));uv.extend([u/.8,1-v/2.4])
  attrs={}
  for name,a,n,type in [('POSITION',pos,3,'VEC3'),('NORMAL',norm,3,'VEC3'),('TEXCOORD_0',uv,2,'VEC2')]:
   acc={'bufferView':view(struct.pack('<'+'f'*len(a),*a),34962),'componentType':5126,'count':len(a)//n,'type':type}
   if name=='POSITION':acc.update(min=[min(a[k::3]) for k in range(3)],max=[max(a[k::3]) for k in range(3)])
   out['accessors'].append(acc);attrs[name]=len(out['accessors'])-1
  out['meshes'][0]['primitives'].append({'attributes':attrs,'material':0 if mat==6 else 1})
 out['buffers'][0]['byteLength']=len(buf);js=json.dumps(out,separators=(',',':')).encode();js+=b' '*((-len(js))%4);buf+=b'\0'*((-len(buf))%4)
 data=struct.pack('<5I',0x46546c67,2,28+len(js)+len(buf),len(js),0x4e4f534a)+js+struct.pack('<II',len(buf),0x004e4942)+buf
 (outdir/('porte-'+('light' if reduced else 'full')+'.glb')).write_bytes(data)
