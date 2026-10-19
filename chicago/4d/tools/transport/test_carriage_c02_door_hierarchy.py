# SPDX-License-Identifier: GPL-3.0-or-later
from pathlib import Path
import copy, importlib.util, json, struct, hashlib, subprocess, sys, math
import numpy as np
import argparse,tempfile
ROOT=Path(__file__).resolve().parents[2]
cli=argparse.ArgumentParser(description='Actual C02 closed-preserving hierarchy negatives; optional complete positive pose controls')
cli.add_argument('--checker',type=Path,default=Path(__file__).with_name('test_carriage_c02_door.py'))
cli.add_argument('--root',type=Path,default=ROOT)
cli.add_argument('--output-dir',type=Path)
cli.add_argument('--legacy-checker',type=Path)
cli.add_argument('--full-positive',action='store_true')
args=cli.parse_args()
owned=tempfile.TemporaryDirectory(prefix='c02-hierarchy-controls-')
P=args.output_dir or Path(owned.name);P.mkdir(parents=True,exist_ok=True);S=args.root;asset=S/'renderers/web/transport/carriage-c02/carriage-c02.glb';raw=asset.read_bytes();size=struct.unpack_from('<I',raw,12)[0];original=json.loads(raw[20:20+size]);binary=raw[28+size:]
sys.dont_write_bytecode=True
spec=importlib.util.spec_from_file_location('check',args.checker);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
parents,active=module.active_hierarchy(original);door=next(i for i in active if original['nodes'][i].get('name')=='vehicle_door_left');body=parents[door];moving=[i for i in active if 'mesh'in original['nodes'][i]and module.descendant(i,door,parents)]
fixtures={}
def emit(name,g,binpart=binary):
 j=json.dumps(g,separators=(',',':')).encode();j+=b' '*((-len(j))%4);data=struct.pack('<III',0x46546c67,2,12+8+len(j)+8+len(binpart))+struct.pack('<II',len(j),0x4e4f534a)+j+struct.pack('<II',len(binpart),0x004e4942)+binpart;f=P/(name+'.glb');f.write_bytes(data);fixtures[name]={'path':str(f),'sha256':hashlib.sha256(data).hexdigest()};return f

def reparent(g,indices):
 for i in indices:
  matrix=np.linalg.inv(module.world(original['nodes'],parents,body))@module.world(original['nodes'],parents,i)
  for node in g['nodes']:
   if 'children'in node:node['children']=[c for c in node['children']if c!=i]
  g['nodes'][body].setdefault('children',[]).append(i)
  for k in['translation','rotation','scale']:g['nodes'][i].pop(k,None)
  g['nodes'][i]['matrix']=matrix.flatten(order='F').tolist()

g=copy.deepcopy(original);reparent(g,moving);emit('reparent-all-door-geometry',g)
g=copy.deepcopy(original);reparent(g,[moving[0]]);emit('reparent-one-door-part',g)
g=copy.deepcopy(original)
for node in g['nodes']:
 if 'children'in node:node['children']=[i for i in node['children']if i!=moving[0]]
emit('orphan-door-part',g)
g=copy.deepcopy(original);g['nodes'].append({'name':'vehicle_door_left','translation':[0,0,0]});g['scenes'][g.get('scene',0)]['nodes'].append(len(g['nodes'])-1);emit('duplicate-active-pivot',g)
g=copy.deepcopy(original);g['scenes'].append({'nodes':[]});g['scene']=len(g['scenes'])-1;emit('selected-empty-scene',g)
g=copy.deepcopy(original)
for i,node in enumerate(g['nodes']):
 matrix=module.local(node)
 for k in['translation','rotation','scale']:node.pop(k,None)
 node['matrix']=matrix.flatten(order='F').tolist()
emit('positive-matrix-encoding',g)
# Actual local TRS on a moving exported primitive, inverse-baked source positions.
g=copy.deepcopy(original);i=moving[0];node=g['nodes'][i];angle=.31;node.update(translation=[.03,-.02,.04],rotation=[0,math.sin(angle/2),0,math.cos(angle/2)],scale=[1.1,.9,1.05]);M=module.local(node);oldM=module.local(original['nodes'][i]);inv=np.linalg.inv(M);changed=bytearray(binary)
for q in g['meshes'][node['mesh']]['primitives']:
 a=g['accessors'][q['attributes']['POSITION']];v=g['bufferViews'][a['bufferView']];off=v.get('byteOffset',0)+a.get('byteOffset',0);xyz=np.asarray(struct.unpack_from('<%sf'%(a['count']*3),changed,off)).reshape(-1,3);points=module.transformed(module.transformed(xyz,oldM),inv);struct.pack_into('<%sf'%(a['count']*3),changed,off,*points.flatten())
emit('positive-moving-child-TRS',g,changed)
rows=[]
def require(condition,message):
 if not condition:raise ValueError(str(message))
reasons={
 'reparent-all-door-geometry':('closed_geometry_and_actual_ancestry_binding','Actual door ancestry mismatch'),
 'reparent-one-door-part':('closed_geometry_and_actual_ancestry_binding','Actual door ancestry mismatch'),
 'orphan-door-part':('closed_geometry_and_actual_ancestry_binding','Active exported triangle missing'),
 'duplicate-active-pivot':('active_export_decode','One active exported door pivot required'),
 'selected-empty-scene':('active_export_decode','One active exported door pivot required')}
def run(name,checker,expected):
 f=P/(name+'.glb');receipt=P/(name+('-old'if checker.name.startswith('old')else'')+'-receipt.json');receipt.unlink(missing_ok=True);r=subprocess.run([sys.executable,str(checker),'--generator',str(S/'tools/transport/generate_carriage_c02.py'),'--parameters',str(S/'data/transport/studies/carriage-c02.json'),'--asset',str(f),'--receipt',str(receipt)],capture_output=True,text=True,cwd='/tmp');log=P/(name+('-old'if checker.name.startswith('old')else'')+'.log');log.write_text(r.stdout+r.stderr);row={'name':name,'checker':checker.name,'returncode':r.returncode,'expected_success':expected,'receipt_survives':receipt.exists(),'receipt':receipt.name,'log':log.name};rows.append(row);(P/'controls-progress.json').write_text(json.dumps({'rows':rows,'fixtures':fixtures},indent=2)+'\n');require((r.returncode==0)==expected,row);require(receipt.exists(),row)
 data=json.loads(receipt.read_text())
 require(data.get('input_sha256')==hashlib.sha256(f.read_bytes()).hexdigest(),'Receipt must bind current actual fixture')
 if not expected:
  stage,error=reasons[name]
  require(data.get('passed')is False and data.get('stage')==stage and data.get('error','').startswith(error),{'unrelated_failure_cannot_pass':name,'receipt':data})
 elif not checker.name.startswith('old'):
  require(data.get('passed')is True and data.get('stage')=='complete','Positive control must pass actual complete checker')
 row['verified_receipt_stage']=data.get('stage');row['verified_rejection_reason']=data.get('error')
 (P/'controls-progress.json').write_text(json.dumps({'rows':rows,'fixtures':fixtures},indent=2)+'\n')
# Demonstrate original false positive against identical synthetic closed geometry.
if args.legacy_checker:
 old=P/'old-checker.py';old.write_bytes(args.legacy_checker.read_bytes());run('reparent-all-door-geometry',old,True)
for name in['reparent-all-door-geometry','reparent-one-door-part','orphan-door-part','duplicate-active-pivot','selected-empty-scene']:run(name,args.checker,False)
if args.full_positive:
 for name in['positive-matrix-encoding','positive-moving-child-TRS']:run(name,args.checker,True)
report={'rows':rows,'fixtures':fixtures,'baseline_sha256':hashlib.sha256(raw).hexdigest(),'new_checker_sha256':hashlib.sha256((args.checker).read_bytes()).hexdigest(),'original_false_positive_reproduced':bool(args.legacy_checker),'changed_asset_geometry':'Only synthetic controls; baseline production bytes untouched','one_checker_process_at_a_time':True};(P/'controls.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(rows,indent=2))

owned.cleanup()
