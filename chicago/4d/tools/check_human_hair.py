# SPDX-License-Identifier: GPL-3.0-or-later
"""Actual embedded hair source/web export checks; no photographic acceptance.

Container/image proof complements loaded Three skin/attribute proof; it does not
pretend to decode Meshopt attributes. All24 expected files are mandatory by default.
"""
import argparse,hashlib,io,json,math,pathlib,struct
from PIL import Image
IDS=('bardwell_otis_1835','dufresne_joseph_1835','flynn_martin_1835')
NAME='hair__makehuman_short04'
# Existing authored pipeline caps2048/1024/512/256 using glTFTransform4.5.0
# fitWithin's sequential flooring; these are not guessed nearest aspect sizes.
WEB_SIZES=((2039,2048),(1020,1024),(510,512),(255,256))

def check(path,web=False,lod=0):
 raw=pathlib.Path(path).read_bytes()
 if len(raw)<20 or struct.unpack_from('<III',raw)!=(0x46546c67,2,len(raw)):raise ValueError('invalid GLB header')
 length,kind=struct.unpack_from('<II',raw,12)
 if kind!=0x4e4f534a:raise ValueError('missing JSON chunk')
 g=json.loads(raw[20:20+length]);offset=20+length
 if offset+8>len(raw):raise ValueError('missing BIN chunk')
 size,kind=struct.unpack_from('<II',raw,offset)
 if kind!=0x004e4942 or offset+8+size!=len(raw):raise ValueError('invalid BIN chunk')
 binary=raw[offset+8:];matches=[i for i,m in enumerate(g.get('materials',[]))if m.get('name')==NAME]
 if len(matches)!=1:raise ValueError('exactly one hair material required')
 mi=matches[0];mat=g['materials'][mi]
 if mat.get('alphaMode')!='MASK' or (not math.isfinite(mat.get('alphaCutoff',.5)) or abs(mat.get('alphaCutoff',.5)-.4)>1e-6) or mat.get('doubleSided')is not True:raise ValueError('hair needs MASK/cutoff.4/doubleSided')
 base=mat.get('pbrMetallicRoughness',{});binding=base.get('baseColorTexture',{})
 if not math.isfinite(base.get('roughnessFactor',1)) or abs(base.get('roughnessFactor',1)-.65)>1e-6 or base.get('metallicFactor',1)!=0 or base.get('baseColorFactor',[1,1,1,1])!=[1,1,1,1]:raise ValueError('hair needs reconstructed roughness.65, metallic0 and white color factor')
 if 'index'not in binding or binding.get('texCoord',0)!=0:raise ValueError('hair base color must use bound TEXCOORD_0')
 tex=g['textures'][binding['index']]
 if 'source'not in tex:raise ValueError('hair image needs actual core source')
 image=g['images'][tex['source']]
 if image.get('mimeType')!='image/png' or 'uri'in image or 'bufferView'not in image:raise ValueError('hair alpha must remain embedded PNG, never JPEG/external')
 view=g['bufferViews'][image['bufferView']]
 if view.get('buffer',0)!=0 or view.get('extensions'):raise ValueError('hair image needs directly embedded audited bytes')
 start=view.get('byteOffset',0);end=start+view['byteLength']
 if start<0 or end>len(binary):raise ValueError('hair image out of bounds')
 payload=binary[start:end]
 with Image.open(io.BytesIO(payload))as decoded:
  decoded.load()
  if decoded.format!='PNG' or 'A'not in decoded.getbands():raise ValueError('hair image must decode actual PNG alpha')
  actual=decoded.size;alpha=decoded.getchannel('A').getextrema()
 if actual!=(WEB_SIZES[lod]if web else(2048,2057)):raise ValueError('hair decoded dimensions do not match source or actual authored LOD resize')
 if not alpha[0]<102 or not alpha[1]>=102:raise ValueError('hair texture lacks both cutout and visible alpha')
 prims=[]
 for ni,node in enumerate(g.get('nodes',[])):
  if 'mesh'not in node:continue
  for prim in g['meshes'][node['mesh']]['primitives']:
   if prim.get('material')!=mi:continue
   if 'skin'not in node or not g['skins'][node['skin']].get('joints'):raise ValueError('hair primitive is not attached to actual skin')
   attrs=prim.get('attributes',{})
   if not {'POSITION','NORMAL','TEXCOORD_0','JOINTS_0','WEIGHTS_0'}<=attrs.keys():raise ValueError('hair missing actual normal/UV/skin attributes')
   access=[g['accessors'][attrs[k]]for k in ['POSITION','NORMAL','TEXCOORD_0','JOINTS_0','WEIGHTS_0']]
   if len({a['count']for a in access})!=1 or access[0]['count']<=0:raise ValueError('hair attribute counts disagree')
   if access[2]['type']!='VEC2' or access[3]['type']!='VEC4' or access[4]['type']!='VEC4':raise ValueError('invalid hair attribute shape')
   if prim.get('mode',4)!=4:raise ValueError('hair must draw actual triangles')
   if 'indices'not in prim or g['accessors'][prim['indices']]['count']<3:raise ValueError('hair triangle index data missing')
   prims.append({'node':ni,'vertices':access[0]['count'],'indices':g['accessors'][prim['indices']]['count']})
 if not prims:raise ValueError('hair material has no actual drawable skinned primitive')
 return {'file':str(path),'sha256':hashlib.sha256(raw).hexdigest(),'hair_primitives':prims,'decoded_size':actual,'alpha_extrema':alpha,'embedded_image_sha256':hashlib.sha256(payload).hexdigest(),'scope':'container + actual PNG decode; loaded skin/UV/weight decoding remains separate runtime check; photographic open'}

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--assets',type=pathlib.Path,default=pathlib.Path('assets/humans'));args=ap.parse_args();fail=[]
 for asset in IDS:
  for web in [False,True]:
   for lod in range(4):
    file=args.assets/('web'if web else'')/f'{asset}.lod{lod}.glb'
    try:print(json.dumps(check(file,web,lod)))
    except Exception as e:fail.append({'file':str(file),'error':str(e)})
 if fail:
  print(json.dumps({'failures':fail}));raise SystemExit(1)
if __name__=='__main__':main()
