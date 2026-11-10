"""Narrow Kinzie target allowances; all unrelated cache/door properties stay exact."""
import math,os,contextlib
from pathlib import Path
HOUSE='kinzie_house_1812'
GREEN='kinzie_house_1812_green'
def need(ok,message):
 if not ok:raise AssertionError(message)
def classify_cache_hash_change(old,new,affected,controls):
 need(old['structure']==new['structure'],'1812 door cache membership/order drift')
 need({k:v for k,v in old.items()if k!='asset_sha256'}=={k:v for k,v in new.items()if k!='asset_sha256'},'1812 actual door/name/placement/wall fields changed '+old['structure'])
 matches=[r for r in affected if r['kind']=='default'and r['structure_id']==old['structure']and r['before_master_sha256']==old['asset_sha256']and r['after_master_sha256']==new['asset_sha256']]
 need(len(matches)==1,'1812 hash change lacks an exact bound selected MASTER')
 row=matches[0]
 if old['structure']==HOUSE:
  need(row['intentional_geometry_target'],'Kinzie door hash change is not the explicit physical target')
  return row,'explicit_Kinzie_whitewash_and_end_door_geometry_target'
 need(not row['intentional_geometry_target'],'Non-house target cannot waive 1812 door hash change')
 control=controls.get(row['asset_key'])
 need(control is not None and control['unused_uv_only_exception'],'Control door hash change lacks proven unused-UV-only explanation')
 return row,'selected_control_proven_unused_UV_only'
def door_profile(raw,fields,parse):
 doc,_binary,access=parse(raw)
 need(all(not any(k in n for k in ['matrix','translation','rotation','scale'])for n in doc['nodes']),'Kinzie probe requires the actual identity native nodes')
 tris=[];leaf_faces={}
 for mesh in doc['meshes']:
  for p in mesh['primitives']:
   name=doc['materials'][p['material']]['name'].lower()
   if name not in {'door','door_panel','board_door','board_door_panel'}:continue
   points=access(p['attributes']['POSITION'])[1];idx=[r[0]for r in access(p['indices'])[1]]
   for i in range(0,len(idx),3):
    tri=tuple(points[int(j)]for j in idx[i:i+3])
    if min(p[1]for p in tri)<0.3:tris.append(tri)
    # The generic 'door' material ALSO colours casing/jambs. Select actual
    # full leaf faces by ground sill + broad planar rectangle, not the outer
    # casing envelope, which stands0.12m above the clear head.
    if name=='door':
     mn=[min(q[k]for q in tri)for k in range(3)];mx=[max(q[k]for q in tri)for k in range(3)]
     for normal,along in [(0,2),(2,0)]:
      if mx[normal]-mn[normal]<1e-6 and mx[along]-mn[along]>.5 and abs(mn[1]-.02)<1e-4 and mx[1]>1.6:
       key=(normal,round(mn[normal],6),round(mn[along],6),round(mx[along],6));leaf_faces.setdefault(key,[]).extend(tri)
 centres=[(sum(p[0]for p in t)/3,-sum(p[2]for p in t)/3)for t in tris];left=set(range(len(tris)));groups=[]
 while left:
  todo=[left.pop()];group=[]
  while todo:
   i=todo.pop();group.append(i);near=[j for j in left if math.dist(centres[i],centres[j])<0.6]
   left.difference_update(near);todo.extend(near)
  pts=[p for i in group for p in tris[i]];mins=[min(p[k]for p in pts)for k in range(3)];maxs=[max(p[k]for p in pts)for k in range(3)];width=max(maxs[0]-mins[0],maxs[2]-mins[2])
  if width>=0.5:groups.append({'u':(mins[0]+maxs[0])/2,'v':-(mins[2]+maxs[2])/2,'width':width,'bottom':mins[1],'top':maxs[1]})
 cache_envelopes=groups;groups=[]
 for key,pts in leaf_faces.items():
  mn=[min(p[k]for p in pts)for k in range(3)];mx=[max(p[k]for p in pts)for k in range(3)]
  groups.append({'u':(mn[0]+mx[0])/2,'v':-(mn[2]+mx[2])/2,'width':max(mx[0]-mn[0],mx[2]-mn[2]),'bottom':mn[1],'top':mx[1]})
 end=[r for r in fields['end_openings']if r[1]=='door'];need(len(end)==1 and end[0][0]=='+x','Frozen Kinzie source must retain its single +x end door')
 width,depth=fields['width_m'],fields['depth_m'];v=depth*end[0][2];matches=[r for r in groups if abs(r['u']-width)<0.15 and abs(r['v']-v)<0.025]
 need(len(matches)==1,'Native Kinzie end door missing, moved, or ambiguous')
 target=matches[0];others=[r for r in groups if r is not target];others.sort(key=lambda r:(r['u'],r['v']))
 return {'target':target,'other_ground_doors':others,'ground_door_count':len(groups),'owner_low_sill_casing_envelopes':cache_envelopes,'coordinate_claim':'Uncompressed native GLB local frame; identity node transforms; actual broad ground-sill leaf faces measured separately from owner casing envelopes.'}
def validate_height_change(old,new,fields,parse):
 need(fields.get('end_door_height_m')==2.5,'Frozen target end-door selector is not the intended2.50m')
 a,b=door_profile(old,fields,parse),door_profile(new,fields,parse)
 need(a['ground_door_count']==b['ground_door_count']==2,'Kinzie ground door count changed')
 for label,row,top in [('before',a['target'],1.95),('after',b['target'],2.52)]:
  need(abs(row['bottom']-.02)<1e-4,label+' Kinzie door sill is not0.02m')
  need(abs(row['top']-top)<1e-4,label+' Kinzie door head is not expected '+str(top))
 for key in ['u','v','width','bottom']:need(abs(a['target'][key]-b['target'][key])<1e-6,'Kinzie target horizontal/width/sill drift '+key)
 for x,y in zip(a['other_ground_doors'],b['other_ground_doors']):
  need(all(abs(x[k]-y[k])<1e-6 for k in x),'Non-target front-door geometry drift')
 return {'status':'PASS_ACTUAL_KINZIE_2_50M_CLEAR_END_DOOR','before':a,'after':b,'frozen_clear_height_m':2.5,'expected_sill_m':.02,'expected_head_m':2.52,'other_ground_door_geometry_exact':True,'claim_limit':'Independent native vertical extent probe; not a historical height or visual/picture acceptance.'}

@contextlib.contextmanager
def immutable_master_path(raw):
 """Expose immutable bytes through an anonymous RAM fd, never a disk model copy."""
 need(hasattr(os,'memfd_create'),'RAM-only pinned recipe audit requires Linux memfd_create')
 fd=os.memfd_create('immutable-kinzie-native-master.glb',flags=os.MFD_CLOEXEC)
 try:
  view=memoryview(raw)
  while view:
   n=os.write(fd,view);need(n>0,'Short RAM fd write');view=view[n:]
  os.lseek(fd,0,os.SEEK_SET)
  yield Path('/proc/self/fd')/str(fd)
 finally:os.close(fd)
