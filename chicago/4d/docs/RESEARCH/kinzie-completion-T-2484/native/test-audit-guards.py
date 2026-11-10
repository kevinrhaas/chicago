#!/usr/bin/env python3
"""Break actual audit readers and the narrow Kinzie door allowance; no native acceptance."""
import copy,importlib.util,json,struct,sys,hashlib
from pathlib import Path
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
spec=importlib.util.spec_from_file_location('audit',HERE/'audit-retained.py');a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
from kinzie_checks import classify_cache_hash_change,validate_height_change
b=json.loads((HERE/'BEFORE-BINDING.json').read_bytes());ctrl=next(x for x in b['affected']if not x['intentional_geometry_target']);base=Path(ctrl['before_master']['actual_read_path']).read_bytes();web=Path(ctrl['before_web_outputs'][0]['actual_read_path']).read_bytes();rows=[]
def test(name,fn,refuses=False):
 try:r=fn()
 except(AssertionError,ValueError,KeyError)as e:
  if not refuses:raise
  rows.append({'case':name,'expected':'REFUSE','result':'PASS','reason':str(e)});return
 if refuses:raise AssertionError('Failed to refuse '+name)
 rows.append({'case':name,'expected':'ACCEPT','result':'PASS'})
def pack(doc,bin):
 j=json.dumps(doc,separators=(',',':')).encode();j+=b' '*( -len(j)%4);bin+=b'\0'*(-len(bin)%4);body=struct.pack('<II',len(j),0x4e4f534a)+j+struct.pack('<II',len(bin),0x004e4942)+bin;return struct.pack('<4sII',b'glTF',2,len(body)+12)+body
def mutate(raw,role=None,docfn=None):
 d,bb,access=a.parse(raw);d=copy.deepcopy(d);binary=bytearray(bb)
 if role:
  pr=next(p for me in d['meshes']for p in me['primitives']if role=='INDICES'or role in p['attributes']);ai=pr['indices']if role=='INDICES'else pr['attributes'][role];aa=d['accessors'][ai];code,size=a.CT[aa['componentType']];off=access(ai)[2][0][0];v=struct.unpack_from('<'+code,binary,off)[0];struct.pack_into('<'+code,binary,off,(v+1)if code!='f'else(v+.03125))
 if docfn:docfn(d)
 return pack(d,bytes(binary))
test('actual genuine control identity',lambda:a.compare_control(ctrl['asset_key'],base,base,web))
for role in ['POSITION','NORMAL','_CONFIDENCE','INDICES']:
 test('changed control '+role,lambda role=role:a.compare_control(ctrl['asset_key'],base,mutate(base,role=role),web),True)
test('changed control material',lambda:a.compare_control(ctrl['asset_key'],base,mutate(base,docfn=lambda d:d['materials'][0].update(doubleSided=not d['materials'][0].get('doubleSided',False))),web),True)
test('changed control node',lambda:a.compare_control(ctrl['asset_key'],base,mutate(base,docfn=lambda d:d['nodes'][0].update(translation=[1,0,0])),web),True)
uvrole=next(k for me in a.parse(base)[0]['meshes']for p in me['primitives']for k in p['attributes']if k.startswith('TEXCOORD_'))
test('actual unused UV-only change remains bounded',lambda:a.compare_control(ctrl['asset_key'],base,mutate(base,role=uvrole),web))
def textured(d,override=False):
 p=next(p for me in d['meshes']for p in me['primitives']if uvrole in p['attributes']);d['images']=[{'uri':'data:image/png;base64,iVBORw0KGgo='}];d['textures']=[{'source':0}];info={'index':0}
 if override:info.update(texCoord=1,extensions={'KHR_texture_transform':{'texCoord':int(uvrole.split('_')[-1])}})
 else:info['texCoord']=int(uvrole.split('_')[-1])
 d['materials'][p['material']]['normalTexture']=info
for override in [False,True]:
 r=mutate(base,docfn=lambda d:textured(d,override));test('consumed UV refuses including transform='+str(override),lambda r=r:a.compare_control(ctrl['asset_key'],r,mutate(r,role=uvrole),web),True)
fields=next(x for x in b['affected']if x['structure_id']=='kinzie_house_1812')['current_inputs_doc']['params']['fields']
def door_glb(head=2.52,sill=.02,front=1.95,shift=0,width=1.04):
 W,D=fields['width_m'],fields['depth_m'];V=D*.63+shift;verts=[(W+.039,sill,-V-width/2),(W+.039,sill,-V+width/2),(W+.039,head,-V+width/2),(W+.039,head,-V-width/2),(W/2-.52,.02,-D-.039),(W/2+.52,.02,-D-.039),(W/2+.52,front,-D-.039),(W/2-.52,front,-D-.039)];binary=struct.pack('<24f',*(v for p in verts for v in p))+struct.pack('<12H',0,1,2,0,2,3,4,5,6,4,6,7);doc={'asset':{'version':'2.0'},'buffers':[{'byteLength':len(binary)}],'bufferViews':[{'buffer':0,'byteOffset':0,'byteLength':96},{'buffer':0,'byteOffset':96,'byteLength':24}],'accessors':[{'bufferView':0,'componentType':5126,'count':8,'type':'VEC3'},{'bufferView':1,'componentType':5123,'count':12,'type':'SCALAR'}],'materials':[{'name':'door'}],'meshes':[{'primitives':[{'attributes':{'POSITION':0},'indices':1,'material':0}]}],'nodes':[{'mesh':0}]};return pack(doc,binary)
old=door_glb(head=1.95);new=door_glb()
test('actual clear-end-door extent2.50m plus sill',lambda:validate_height_change(old,new,fields,a.parse))
for name,kwargs in [('unraised',{'head':1.95}),('clear-height mistaken for top',{'head':2.50}),('shifted sill',{'sill':.12}),('other front door changed',{'front':2.1}),('end door moved',{'shift':.2}),('door width changed',{'width':1.14})]:
 test('target '+name,lambda kwargs=kwargs:validate_height_change(old,door_glb(**kwargs),fields,a.parse),True)
oldrow={'structure':'kinzie_house_1812','name':'unchanged','placement':{'e':1},'doors':[{'leaf':[1,2]}],'asset_sha256':'old'};newrow=dict(oldrow,asset_sha256='new');target={'kind':'default','structure_id':'kinzie_house_1812','asset_key':'house.glb','before_master_sha256':'old','after_master_sha256':'new','intentional_geometry_target':True}
test('exact bound physical-target hash-only cache',lambda:classify_cache_hash_change(oldrow,newrow,[target],{}))
for name,changes in [('cache geometry',{'doors':[{'leaf':[2,2]}]}),('cache name',{'name':'wrong'}),('wrong asset hash',{'asset_sha256':'wrong'}),('cache walls',{'walls':[]})]:
 test(name,lambda changes=changes:classify_cache_hash_change(oldrow,dict(newrow,**changes),[target],{}),True)
cold=dict(oldrow,structure='control');cnew=dict(cold,asset_sha256='new');crow=dict(target,structure_id='control',asset_key='control.glb',intentional_geometry_target=False)
test('control hash requires UV proof',lambda:classify_cache_hash_change(cold,cnew,[crow],{'control.glb':{'unused_uv_only_exception':False}}),True)
test('proved UV-only control hash still accepted',lambda:classify_cache_hash_change(cold,cnew,[crow],{'control.glb':{'unused_uv_only_exception':True}}))
receipt={'status':'PASS_AUDIT_NEGATIVE_GUARDS_NOT_NATIVE_ACCEPTANCE','cases':rows,'actual_control_fixture':ctrl['asset_key'],'pinned_source':b['captured_HEAD'],'binding_sha256':hashlib.sha256((HERE/'BEFORE-BINDING.json').read_bytes()).hexdigest(),'claim_limit':'Actual readers and allowances exercised with deliberately damaged native inputs and synthetic door leaves. Not rebuilt control equality, target native existence, image/UI acceptance, or a dispatch receipt.'};(HERE/'AUDIT-NEGATIVE-FIXTURES.json').write_text(json.dumps(receipt,indent=2)+'\n');print('PASS',len(rows),'meaningful audit/door guard cases')
