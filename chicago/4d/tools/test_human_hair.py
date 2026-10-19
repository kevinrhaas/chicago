# SPDX-License-Identifier: GPL-3.0-or-later
import pathlib,sys,json,struct,io,tempfile,copy,unittest
sys.dont_write_bytecode=True
from PIL import Image
P=pathlib.Path(__file__).parent;sys.path.insert(0,str(P));from check_human_hair import check,WEB_SIZES

def fixture(size=(2048,2057),opaque=False):
 im=Image.new('RGBA',size,(20,20,20,255));im.putpixel((0,0),(0,0,0,255 if opaque else 0));out=io.BytesIO();im.save(out,format='PNG');blob=out.getvalue();binary=bytearray(blob);binary+=b'\0'*((-len(binary))%4);views=[{'buffer':0,'byteOffset':0,'byteLength':len(blob)}];access=[]
 for values,fmt,typ,component in [([0,0,0,1,0,0,0,1,0],'f','VEC3',5126),([0,0,1]*3,'f','VEC3',5126),([0,0,1,0,0,1],'f','VEC2',5126),([0]*12,'H','VEC4',5123),([1,0,0,0]*3,'f','VEC4',5126),([0,1,2],'H','SCALAR',5123)]:
  payload=struct.pack('<'+fmt*len(values),*values);views.append({'buffer':0,'byteOffset':len(binary),'byteLength':len(payload)});binary+=payload;binary+=b'\0'*((-len(binary))%4);access.append({'bufferView':len(views)-1,'count':3,'type':typ,'componentType':component})
 g={'asset':{'version':'2.0'},'buffers':[{'byteLength':len(binary)}],'bufferViews':views,'accessors':access,'materials':[{'name':'hair__makehuman_short04','alphaMode':'MASK','alphaCutoff':.4,'doubleSided':True,'pbrMetallicRoughness':{'baseColorTexture':{'index':0},'roughnessFactor':.65,'metallicFactor':0}}],'textures':[{'source':0}],'images':[{'bufferView':0,'mimeType':'image/png'}],'meshes':[{'primitives':[{'material':0,'indices':5,'attributes':dict(zip(['POSITION','NORMAL','TEXCOORD_0','JOINTS_0','WEIGHTS_0'],range(5)))}]}],'nodes':[{'mesh':0,'skin':0},{'name':'head'}],'skins':[{'joints':[1]}]};return g,bytes(binary)
def write(g,b,p):
 j=json.dumps(g).encode();j+=b' '*((-len(j))%4);p.write_bytes(struct.pack('<III',0x46546c67,2,28+len(j)+len(b))+struct.pack('<II',len(j),0x4e4f534a)+j+struct.pack('<II',len(b),0x004e4942)+b)
class Contracts(unittest.TestCase):
 def run_case(self,g,b,web=False,lod=0):
  with tempfile.TemporaryDirectory()as d:p=pathlib.Path(d)/'fixture.glb';write(g,b,p);return check(p,web,lod)
 def test_positive_source_real_embedded_png(self):self.assertEqual(self.run_case(*fixture())['decoded_size'],(2048,2057))
 def test_positive_all_actual_web_resize_sizes(self):
  for lod,size in enumerate(WEB_SIZES):self.assertEqual(self.run_case(*fixture(size),web=True,lod=lod)['decoded_size'],size)
 def test_material_embedding_and_skin_refusals(self):
  mutations=[lambda g:g['materials'][0]['pbrMetallicRoughness'].update(roughnessFactor=.1),lambda g:g['materials'][0]['pbrMetallicRoughness'].update(metallicFactor=1),lambda g:g['materials'][0].update(alphaMode='OPAQUE'),lambda g:g['materials'][0].update(alphaCutoff=.5),lambda g:g['materials'][0].update(doubleSided=False),lambda g:g['images'][0].update(uri='external.png'),lambda g:g['images'][0].update(mimeType='image/jpeg'),lambda g:g['nodes'][0].pop('skin'),lambda g:g['meshes'][0]['primitives'][0]['attributes'].pop('WEIGHTS_0'),lambda g:g['accessors'][2].update(count=2),lambda g:g.update(nodes=[])]
  for mutate in mutations:
   g,b=fixture();mutate(g)
   with self.assertRaises(ValueError):self.run_case(g,b)
 def test_dimensions_alpha_and_corrupt_actual_bytes(self):
  for args in [((2048,2048),False),((2048,2057),True)]:
   with self.assertRaises(ValueError):self.run_case(*fixture(*args))
  g,b=fixture();bad=bytearray(b);bad[1]=0
  with self.assertRaises(Exception):self.run_case(g,bad)
if __name__=='__main__':unittest.main()
