#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Label opaque embedded images in a SCRATCH GLB for safe native-JPEG conversion.
Canonical source bytes are never rewritten. Alpha-bearing images keep PNG even if
an exporter accidentally labels their material opaque. No geometry is changed.
"""
import io,json,pathlib,struct,sys
from PIL import Image
src,out=map(pathlib.Path,sys.argv[1:3]);raw=src.read_bytes()
assert struct.unpack_from('<III',raw)==(0x46546c67,2,len(raw)), 'invalid GLB'
n,t=struct.unpack_from('<II',raw,12);assert t==0x4e4f534a
doc=json.loads(raw[20:20+n]);tail=raw[20+n:];assert struct.unpack_from('<I',tail,4)[0]==0x004e4942
binary=tail[8:];audit=[]
color_images=set();data_images=set()
def scan_slots(value):
 if isinstance(value,dict):
  for key,child in value.items():
   if key.endswith('Texture') and isinstance(child,dict) and isinstance(child.get('index'),int):
    tex=doc['textures'][child['index']];source=tex.get('source')
    if source is not None:
     (color_images if key in ('baseColorTexture','emissiveTexture') else data_images).add(source)
   scan_slots(child)
 elif isinstance(value,list):
  for child in value:scan_slots(child)
scan_slots(doc.get('materials',[]))
for i,image in enumerate(doc.get('images',[])):
 if 'bufferView' not in image: raise ValueError('authored web path requires embedded images; external image URI is not audited')
 view=doc['bufferViews'][image['bufferView']];a=view.get('byteOffset',0);blob=binary[a:a+view['byteLength']]
 with Image.open(io.BytesIO(blob)) as decoded:
  alpha=decoded.convert('RGBA').getextrema()[3];opaque=alpha==(255,255)
  eligible=opaque and i in color_images and i not in data_images
  image['name']=f'c4d_web_opaque_{i:03d}' if eligible else f'c4d_web_alpha_preserve_{i:03d}'
  audit.append({'image':i,'size':list(decoded.size),'alpha_extrema':list(alpha),'opaque':opaque,'jpeg_color_eligible':eligible,'scratch_name':image['name']})
j=json.dumps(doc,separators=(',',':')).encode();j+=b' '*((-len(j))%4)
encoded=struct.pack('<III',0x46546c67,2,20+len(j)+len(tail))+struct.pack('<II',len(j),0x4e4f534a)+j+tail
out.write_bytes(encoded);print(json.dumps({'source':str(src),'images':audit}))
