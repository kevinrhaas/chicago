# SPDX-License-Identifier: GPL-3.0-or-later
"""SOURCE ONLY until independent review. Original bounded C02 upholstery parcel."""
from pathlib import Path
import json,hashlib,copy,traceback
import numpy as np
from glb_data import parse,read,append,encode
from cushion_shapes import proposed_driver_cushion,require
INPUT_SHA='93d4020036e5c685ce95010fe64b26c55a1561db4517405f0590f7a398253331'

def propose_once(raw):
 require(hashlib.sha256(raw).hexdigest()==INPUT_SHA,'Exact current C02 input required; do not rebase silently')
 d,blob=parse(raw);require(d['extras']['license']=='GPL-3.0-or-later'and d['extras']['parameters']['operable_door_study']is True,'existing license/framed door required')
 prim=d['meshes'][8]['primitives'][0];require(d['meshes'][8]['name']=='surface_1_2'and len(d['meshes'][8]['primitives'])==1 and'indices'not in prim and set(prim['attributes'])=={'POSITION','NORMAL'},'exact original upholstery surface owner')
 require(d['materials'][prim['material']]['name']=='upholstery','existing material identity')
 old={k:read(d,blob,a)for k,a in prim['attributes'].items()};require(old['POSITION'].shape==(108,3),'exact36source triangles')
 faces=old['POSITION'].reshape(-1,3,3);inside=lambda p:-.460001<=p[0]<=.460001 and 1.204999<=p[1]<=1.315001 and .669999<=p[2]<=1.050001
 selected=[i for i,f in enumerate(faces)if all(inside(p)for p in f)];require(selected==list(range(24,36)),'exact12 original driver-seat triangles; no passenger material removed')
 # Only here, after all exact input/owner checks, would the original shape run.
 parts=proposed_driver_cushion();kept=np.arange(72);pos=[old['POSITION'][kept]];normal=[old['NORMAL'][kept]];parts_receipt=[];triangle_start=24
 for part in parts:
  vertices=np.asarray(part['vertices'],dtype='<f4');normals=np.asarray(part['normals'],dtype='<f4');idx=np.asarray(part['triangles'],dtype=int);expanded=vertices[idx].reshape(-1,3);expanded+=np.asarray([0,1.26,.86],dtype='<f4');nn=normals[idx].reshape(-1,3)
  require(np.isfinite(expanded).all()and np.isfinite(nn).all()and np.all(np.abs(np.linalg.norm(nn,axis=1)-1)<1e-5),'finite authored normals/positions')
  require(np.all(expanded[:,0]>=-.460001)and np.all(expanded[:,0]<=.460001)and np.all(expanded[:,1]>=1.204999)and np.all(expanded[:,1]<=1.315001)and np.all(expanded[:,2]>=.669999)and np.all(expanded[:,2]<=1.050001),'unchanged old seat prism')
  pos.append(expanded);normal.append(nn);parts_receipt.append({'name':part['name'],'triangle_start':triangle_start,'triangle_count':len(idx),'material_index':prim['material'],'grade':'reconstructed'});triangle_start+=len(idx)
 pos=np.concatenate(pos);normal=np.concatenate(normal);require(len(pos)==752*3,'source-proposed752 upholstery triangles')
 new=copy.deepcopy(d);newblob=bytearray(blob)
 for k,a in [('POSITION',pos),('NORMAL',normal)]:new['meshes'][8]['primitives'][0]['attributes'][k]=append(new,newblob,a,'VEC3')
 new['extras']['asset_id']='carriage_c02_driver_cushion_study';new['extras']['driver_cushion_study']={'status':'original bounded stuffed-cushion and sewn-welt reconstruction; not photographic/subtype/occupant acceptance','removed_driver_box_triangles':12,'authored_parts':parts_receipt,'outer_prism_m':[.92,.11,.38],'same_socket_transforms':True,'period':'1904development only','source_analogy':'Ware1875printed326 trimming construction; exact C02design/colors/dimensions not attested'};new['extras']['statistics']['triangles']=12228
 exported=encode(new,newblob);rd,rb=parse(exported)
 require(bytes(rb[:len(blob)])==bytes(blob),'originalBINprefix unchanged')
 require(len(rd['accessors'])==len(d['accessors'])+2 and len(rd['bufferViews'])==len(d['bufferViews'])+2,'exactlytwo storage appends')
 require(rd['accessors'][:len(d['accessors'])]==d['accessors']and rd['bufferViews'][:len(d['bufferViews'])]==d['bufferViews'],'original storage metadata unchanged')
 refs=rd['meshes'][8]['primitives'][0]['attributes'];require(refs['POSITION']==len(d['accessors'])and refs['NORMAL']==len(d['accessors'])+1,'actual ordered new attribute refs')
 for k,a in [('POSITION',pos),('NORMAL',normal)]:require(np.array_equal(read(rd,rb,refs[k]),a),'exact intended readback:'+k)
 old_extra=copy.deepcopy(d['extras']);new_extra=copy.deepcopy(rd['extras']);new_extra.pop('driver_cushion_study');new_extra['asset_id']=old_extra['asset_id'];new_extra['statistics']['triangles']=old_extra['statistics']['triangles'];require(new_extra==old_extra,'unauthorized old metadata changed')
 original_buffer=copy.deepcopy(rd['buffers']);original_buffer[0]['byteLength']=d['buffers'][0]['byteLength'];require(original_buffer==d['buffers'],'original buffer metadata changed')
 a=copy.deepcopy(d);b=copy.deepcopy(rd)
 for document in[a,b]:
  document.pop('accessors');document.pop('bufferViews');document.pop('buffers');document.pop('extras');document['meshes'][8]['primitives'][0]['attributes'].pop('POSITION');document['meshes'][8]['primitives'][0]['attributes'].pop('NORMAL')
 require(a==b,'protected door/nodes/rig/materials/geometryrefs/document changed')
 require(np.array_equal(pos[:72],old['POSITION'][:72])and np.array_equal(normal[:72],old['NORMAL'][:72]),'passenger upholstery unchanged')
 return exported,{'status':'UNACCEPTED candidate only; exact preservation source guards, no actual render/door/occupant/photo acceptance','input_sha256':INPUT_SHA,'output_sha256':hashlib.sha256(exported).hexdigest(),'original_triangle_count':11512,'new_triangle_count':12228,'added_triangles':716,'changed_mesh':8,'changed_material':'existing upholstery unchanged','authored_parts':parts_receipt,'all_nodes_materials_and_other_mesh_refs_exact':True,'passenger_upholstery_exact':True,'new_parts_within_old_driver_box':True,'license':'GPL-3.0-or-later','scene_eligibility':'1904development only'}

def run_once(source,outdir):
 out=Path(outdir);require(not out.exists(),'fresh output only');out.mkdir(parents=True);receipt={'status':'STARTED UNACCEPTED','input_sha256_expected':INPUT_SHA}
 def save():(out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
 try:
  save();candidate,proof=propose_once(Path(source).read_bytes());(out/'carriage-c02.glb').write_bytes(candidate);receipt.update(proof);save()
 except BaseException as e:receipt.update(status='FIRST FAILURE STOP',error=str(e),traceback=traceback.format_exc());save();raise
# No command line or automatic generation entrypoint in this source-review parcel.
