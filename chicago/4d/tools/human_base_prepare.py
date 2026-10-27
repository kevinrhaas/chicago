#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Prepare verified CC0 hm08 graphical data for a canonical Blender authoring step.

Original stdlib-only implementation. No MakeHuman application code is imported.
This emits geometry/rig JSON, never glTF or a claim of an authored master.
"""
import argparse, collections, gzip, hashlib, json, math, pathlib, statistics
ROOT=pathlib.Path(__file__).resolve().parents[1]
DEFAULT=ROOT/'assets/authored/humans/makehuman_hm08'
def add(a,b):return [x+y for x,y in zip(a,b)]
def sub(a,b):return [x-y for x,y in zip(a,b)]
def mul(a,s):return [x*s for x in a]
# Python 3.12 changed builtin sum's float reduction. Explicit fsum keeps the
# source-derived JSON byte-identical on the 3.11 CI worker and newer runtimes.
def dot(a,b):return math.fsum(x*y for x,y in zip(a,b))
def cross(a,b):return [a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]]
def norm(a):return math.sqrt(dot(a,a))
def unit(a):
 n=norm(a)
 if n<1e-10:raise ValueError('degenerate direction')
 return mul(a,1/n)
def avg(v):return [math.fsum(x[k] for x in v)/len(v) for k in range(3)]
def rotate(v,a,b):
 """Shortest-arc rotation taking nonzero a to b, including antiparallel case."""
 a,b=unit(a),unit(b);c=max(-1,min(1,dot(a,b)));axis=cross(a,b);s=norm(axis)
 if s<1e-10:
  if c>0:return list(v)
  axis=unit(cross(a,[1,0,0] if abs(a[0])<.9 else [0,1,0]));return sub(mul(axis,2*dot(axis,v)),v)
 axis=mul(axis,1/s);return add(add(mul(v,c),mul(cross(axis,v),s)),mul(axis,dot(axis,v)*(1-c)))
def read_obj(path):
 vertices=[];uvs=[];faces=[];group='';groups=collections.Counter()
 for line in path.read_text().splitlines():
  fields=line.split()
  if not fields:continue
  if fields[0]=='v':vertices.append(list(map(float,fields[1:4])))
  elif fields[0]=='vt':uvs.append(list(map(float,fields[1:3])))
  elif fields[0]=='g':group=fields[1]
  elif fields[0]=='f':
   groups[group]+=1
   if group!='body':continue
   corners=[]
   for item in fields[1:]:
    bits=item.split('/');vi=int(bits[0]);ti=int(bits[1]);corners.append((vi-1 if vi>0 else len(vertices)+vi,ti-1 if ti>0 else len(uvs)+ti))
   if len(corners)<3:raise ValueError('face has fewer than three corners')
   faces.append(corners)
 return vertices,uvs,faces,groups

def source_map(bones):
 """Explicit collapse policy, emitted for every source bone including zero-weight bones."""
 result={};reason={}
 fixed={'root':'pelvis','spine05':'pelvis','spine04':'spine_01','spine03':'spine_02','spine02':'spine_03','spine01':'spine_03','head':'head','jaw':'jaw'}
 for name in bones:
  side='l' if name.endswith('.L') else 'r' if name.endswith('.R') else None;base=name[:-2] if side else name
  target=fixed.get(name);why='spine/pelvis chain collapsed to contract length'
  if name.startswith('neck'):target='neck_01';why='three source neck segments collapsed'
  elif side:
   direct={'breast':'spine_03','clavicle':'clavicle','shoulder01':'upperarm','upperarm01':'upperarm','upperarm02':'upperarm','lowerarm01':'lowerarm','lowerarm02':'lowerarm','wrist':'hand','pelvis':'pelvis','upperleg01':'thigh','upperleg02':'thigh','lowerleg01':'calf','lowerleg02':'calf','foot':'foot','eye':'eye'}
   if base in direct:
    t=direct[base];target=t if t in ['spine_03','pelvis'] else t+'_'+side;why='paired/twist/helper segment merged into anatomical contract bone'
   elif base.startswith('finger'):
    finger,segment=map(int,base[6:].split('-'));target=f"{['thumb','index','middle','ring','pinky'][finger-1]}_{segment:02}_{side}";why='digit identity/segment mapped explicitly'
   elif base.startswith('metacarpal'):target='hand_'+side;why='metacarpal weights merged to palm'
   elif base.startswith('toe'):target='ball_'+side;why='individual toes collapsed to shared forefoot'
  if target is None:
   # Facial extensions follow the closest surviving source ancestor. This is a
   # documented loss of facial articulation, not a fabricated ARKit face rig.
   ancestor=name
   while ancestor and ancestor not in ['head','jaw']:ancestor=bones[ancestor]['parent']
   if ancestor is None:raise ValueError('unmapped nonfacial bone '+name)
   target=ancestor;why='facial/tongue extension collapsed to surviving head/jaw ancestor; expression detail lost'
  result[name]=target;reason[name]=why
 return result,reason

def apply_graphical_targets(raw,source_dir,provenance,recipe_path):
 if recipe_path is None:return {'status':'unmodified hm08 neutral source; no adult target recipe applied'}
 recipe_bytes=pathlib.Path(recipe_path).read_bytes();recipe=json.loads(recipe_bytes)
 if recipe.get('format')!='chicago4d_human_graphical_target_recipe_v1':raise ValueError('unknown target recipe format')
 phenotype=recipe['phenotype'];age=phenotype['chosen_age_years'];band=phenotype['age_band_years']
 if not isinstance(age,(int,float)) or not math.isfinite(age) or len(band)!=2 or not band[0]<=age<=band[1]:raise ValueError('chosen age must lie within declared band')
 verified={row['path']:row for row in provenance['files']};applied=[];baseline=[list(v) for v in raw];seen_paths=set();total=0
 for row in recipe['targets']:
  name=row['path'];rel=pathlib.PurePosixPath(name)
  if rel.is_absolute()or '..'in rel.parts or rel.suffix!='.target':raise ValueError('target path must be relative graphical.target')
  if name in seen_paths:raise ValueError('duplicate target recipe path')
  seen_paths.add(name);coefficient=row['coefficient']
  if isinstance(coefficient,bool)or not isinstance(coefficient,(int,float))or not math.isfinite(coefficient)or not 0<=coefficient<=1:raise ValueError('target coefficient must be finite 0..1')
  if name not in verified or verified[name]['sha256']!=row['sha256']:raise ValueError('target must be in verified graphical source manifest')
  payload=(source_dir/name).read_bytes()
  if hashlib.sha256(payload).hexdigest()!=row['sha256']:raise ValueError('target checksum mismatch')
  text=payload.decode();header='\n'.join(line for line in text.splitlines()if line.lstrip().startswith('#'))
  if 'explicitly released as CC0'not in header:raise ValueError('target lacks explicit CC0 graphical asset header')
  indices=set()
  for line in text.splitlines():
   if not line.strip()or line.lstrip().startswith('#'):continue
   fields=line.split()
   if len(fields)!=4:raise ValueError('malformed graphical target row')
   index=int(fields[0]);delta=list(map(float,fields[1:]))
   if not 0<=index<len(raw)or index in indices or not all(math.isfinite(x)for x in delta):raise ValueError('invalid/duplicate graphical target vertex')
   indices.add(index);raw[index]=add(raw[index],mul(delta,coefficient))
  total+=coefficient;applied.append({'path':name,'sha256':row['sha256'],'coefficient':coefficient,'delta_rows':len(indices)})
 if not applied or not math.isclose(total,1,abs_tol=1e-10):raise ValueError('macro target blend must have coefficients summing to1')
 return {'status':'original linear blend of verified CC0 graphical target deltas','recipe_sha256':hashlib.sha256(recipe_bytes).hexdigest(),'phenotype':phenotype,'applied_targets':applied,'coefficient_sum':total,'max_vertex_delta_source_units':max(norm(sub(a,b))for a,b in zip(raw,baseline)),'changed_vertex_count':sum(norm(sub(a,b))>1e-12 for a,b in zip(raw,baseline)),'_baseline':baseline}

def verify_source_row(source_dir,row):
 """Verify stored bytes and, for transport-packed notices, verbatim upstream bytes."""
 payload=(source_dir/row['path']).read_bytes()
 if row.get('compression')=='gzip':
  if hashlib.sha256(payload).hexdigest()!=row['stored_sha256']:raise ValueError('stored source checksum mismatch: '+row['path'])
  try:decoded=gzip.decompress(payload)
  except (OSError,EOFError)as exc:raise ValueError('invalid gzip source: '+row['path'])from exc
  if hashlib.sha256(decoded).hexdigest()!=row['decompressed_sha256']or hashlib.sha256(decoded).hexdigest()!=row['sha256']:raise ValueError('decoded source checksum mismatch: '+row['path'])
  if len(decoded)!=row['decompressed_bytes']or len(payload)!=row['stored_bytes']:raise ValueError('source size mismatch: '+row['path'])
  return decoded
 if row.get('compression'):raise ValueError('unsupported source compression')
 if hashlib.sha256(payload).hexdigest()!=row['sha256']:raise ValueError('source checksum mismatch: '+row['path'])
 return payload

def prepare(source_dir,height,target_recipe=None,source_manifest='SOURCE.json'):
 if not math.isfinite(height) or not .9<=height<=2.3:raise ValueError('chosen adult height must be finite, .9–2.3m')
 manifest_name=pathlib.PurePosixPath(source_manifest)
 if manifest_name.is_absolute() or len(manifest_name.parts)!=1 or manifest_name.suffix!='.json' or not (source_dir/manifest_name).resolve().is_relative_to(source_dir.resolve()):raise ValueError('source manifest must be one local JSON filename')
 provenance=json.loads((source_dir/manifest_name).read_text())
 for row in provenance['files']:
  verify_source_row(source_dir,row)
 raw,uvs,faces,groups=read_obj(source_dir/'makehuman/data/3dobjs/base.obj')
 target_blend=apply_graphical_targets(raw,source_dir,provenance,target_recipe)
 rig=json.loads((source_dir/'makehuman/data/rigs/default.mhskel').read_text());original_weights=json.loads((source_dir/'makehuman/data/rigs/default_weights.mhw').read_text())
 if rig['license']!='CC0' or original_weights['license']!='CC0':raise ValueError('CC0 source license changed')
 joints={name:avg([raw[i] for i in ids]) for name,ids in rig['joints'].items()}
 if '_baseline'in target_blend:
  baseline=target_blend.pop('_baseline');helpers={vi for ids in rig['joints'].values()for vi in ids};target_blend['helper_vertex_count']=len(helpers);target_blend['changed_helper_vertices']=sum(norm(sub(raw[i],baseline[i]))>1e-12 for i in helpers);target_blend['max_joint_anchor_delta_source_units']=max(norm(sub(joints[name],avg([baseline[i]for i in ids])))for name,ids in rig['joints'].items())
 def endpoint(bone,end='head'):return joints[rig['bones'][bone][end]]
 used=sorted({i for face in faces for i,t in face});min_y=min(raw[i][1] for i in used);max_y=max(raw[i][1] for i in used);scale=height/(max_y-min_y)
 ankle_mid=avg([endpoint('foot.L'),endpoint('foot.R')]);origin=[ankle_mid[0],min_y,ankle_mid[2]]
 def metric(v):return mul(sub(v,origin),scale)
 source={};source_anchors={}
 def anchor(name,head,tail,basis):source[name]=[metric(head),metric(tail)];source_anchors[name]=basis
 anchor('root',origin,endpoint('root','tail'),'constructed ground midpoint to source pelvis')
 anchor('pelvis',endpoint('root','tail'),endpoint('spine04'),'root tail to spine04 head')
 for target,start,end in [('spine_01','spine04','spine03'),('spine_02','spine03','spine02'),('spine_03','spine02','neck01'),('neck_01','neck01','head')]:anchor(target,endpoint(start),endpoint(end),start+' head to '+end+' head')
 for n in ['head','jaw']:anchor(n,endpoint(n),endpoint(n,'tail'),n+' helper head/tail')
 for side,source_side in [('l','L'),('r','R')]:
  for target,start,end in [('clavicle','clavicle','upperarm01'),('upperarm','upperarm01','lowerarm01'),('lowerarm','lowerarm01','wrist'),('hand','wrist','finger3-1'),('thigh','upperleg01','lowerleg01'),('calf','lowerleg01','foot'),('foot','foot','toe2-1')]:anchor(target+'_'+side,endpoint(start+'.'+source_side),endpoint(end+'.'+source_side),start+' to '+end+' source heads')
  anchor('ball_'+side,endpoint('toe2-1.'+source_side),endpoint('toe2-3.'+source_side,'tail'),'central toe head to distal toe tail')
  anchor('eye_'+side,endpoint('eye.'+source_side),endpoint('eye.'+source_side,'tail'),'actual eye helpers')
  for digit,family in enumerate(['thumb','index','middle','ring','pinky'],1):
   for segment in [1,2,3]:
    n=f'finger{digit}-{segment}.{source_side}';anchor(f'{family}_{segment:02}_{side}',endpoint(n),endpoint(n,'tail'),n+' helper head/tail')
 contract=json.loads((ROOT/'data/humans/contract.json').read_text())['skeleton']['bones'];names=[row[0] for row in contract]
 if set(names)!=set(source):raise ValueError('source anchor table does not match 56-joint contract')
 mapping,reasons=source_map(rig['bones']);assert set(mapping.values())<=set(names)
 # Construct a deliberate T pose. Torso/head retained; bilateral arm chains made
 # horizontal and digit planes flattened; legs made straight with source lengths.
 target={n:[list(h),list(t)] for n,(h,t) in source.items()}
 for side,sign in [('l',1),('r',-1)]:
  for family in ['upperarm','lowerarm','hand']:
   n=family+'_'+side
   if family!='upperarm':target[n][0]=target[('upperarm' if family=='lowerarm' else 'lowerarm')+'_'+side][1][:]
   target[n][1]=add(target[n][0],[sign*norm(sub(source[n][1],source[n][0])),0,0])
  # Finger-root fan positions are rotated with the source palm, then projected
  # onto the horizontal palm plane; each segment extends straight, thumb forward.
  hand='hand_'+side
  for family in ['thumb','index','middle','ring','pinky']:
   for segment in [1,2,3]:
    n=f'{family}_{segment:02}_{side}'
    if segment==1:
     v=rotate(sub(source[n][0],source[hand][0]),sub(source[hand][1],source[hand][0]),[sign,0,0]);v[1]=0;target[n][0]=add(target[hand][0],v)
    else:target[n][0]=target[f'{family}_{segment-1:02}_{side}'][1][:]
    direction=unit([sign*.4,0,.916515]) if family=='thumb' else [sign,0,0];target[n][1]=add(target[n][0],mul(direction,norm(sub(source[n][1],source[n][0]))))
  for family in ['thigh','calf']:
   n=family+'_'+side
   if family=='calf':target[n][0]=target['thigh_'+side][1][:]
   target[n][1]=add(target[n][0],[0,-norm(sub(source[n][1],source[n][0])),0])
  shift=sub(target['calf_'+side][1],source['foot_'+side][0])
  for family in ['foot','ball']:
   n=family+'_'+side;target[n]=[add(p,shift) for p in source[n]]
 # Collapse source weights, normalize source rounding, then prune to strongest4.
 accum=collections.defaultdict(lambda:collections.defaultdict(float));source_counts=collections.Counter()
 for bone,entries in original_weights['weights'].items():
  for vi,w in entries:
   if w<0 or not math.isfinite(w):raise ValueError('invalid source weight')
   if w>0:accum[vi][mapping[bone]]+=w;source_counts[vi]+=1
 weights={};discarded={};unpruned={};source_sum_errors=[]
 for vi in used:
  row=accum[vi];total=math.fsum(row.values())
  if total<=0:raise ValueError('unweighted body vertex '+str(vi))
  source_sum_errors.append(abs(total-1));normalized={n:w/total for n,w in row.items()};unpruned[vi]=normalized
  ranked=sorted(normalized.items(),key=lambda x:(-x[1],x[0]));discarded[vi]=math.fsum(w for n,w in ranked[4:]);kept=ranked[:4];keep_total=math.fsum(w for n,w in kept);weights[vi]={n:w/keep_total for n,w in kept}
 def deform(vi,row):
  v=metric(raw[vi]);out=[0,0,0]
  for n,w in row.items():
   sh,st=source[n];th,tt=target[n];out=add(out,mul(add(th,rotate(sub(v,sh),sub(st,sh),sub(tt,th))),w))
  return out
 posed={vi:deform(vi,weights[vi]) for vi in used};full={vi:deform(vi,unpruned[vi]) for vi in used};prune_errors=[norm(sub(posed[vi],full[vi])) for vi in used]
 # Final common metric registration uses actual posed body bounds. Chosen height
 # is exact for this mesh; ground support and root sit at y=0 after deformation.
 bottom=min(v[1] for v in posed.values());top=max(v[1] for v in posed.values());final_scale=height/(top-bottom)
 def finish(v):return [v[0]*final_scale,(v[1]-bottom)*final_scale,v[2]*final_scale]
 posed={vi:finish(v) for vi,v in posed.items()};target={n:[finish(h),finish(t)] for n,(h,t) in target.items()};target['root'][0]=[0,0,0]
 vertices=[];texcoords=[];out_weights=[];source_vertex=[];indices={};triangles=[];zero_area=0;face_area_error=0
 for face in faces:
  fi=[]
  for vi,ti in face:
   if (vi,ti) not in indices:
    indices[(vi,ti)]=len(vertices);vertices.append(posed[vi]);texcoords.append(uvs[ti]);out_weights.append(weights[vi]);source_vertex.append(vi)
   fi.append(indices[(vi,ti)])
  # hm08 body has triangles/quads. Fan triangulation keeps source winding and
  # cornerUVs; no welding or invented topology beyond each original polygon.
  for k in range(1,len(fi)-1):
   tri=[fi[0],fi[k],fi[k+1]];area=norm(cross(sub(vertices[tri[1]],vertices[tri[0]]),sub(vertices[tri[2]],vertices[tri[0]])))/2
   if area<1e-12:zero_area+=1
   triangles.append(tri)
 seam_sources=collections.Counter(source_vertex);all_disc=list(discarded.values());all_disc.sort();symmetry=max(abs(target['hand_l'][0][0]+target['hand_r'][0][0]),abs(target['hand_l'][0][1]-target['hand_r'][0][1]));report={'status':'engineering source/rebind preparation; not canonical Blender master or photographic adult','target_blend':target_blend,'body_source_vertices':len(used),'output_vertices_uv_split':len(vertices),'source_uv_seam_vertices':sum(n>1 for n in seam_sources.values()),'triangles':len(triangles),'source_polygons':len(faces),'source_face_arities':dict(collections.Counter(len(f) for f in faces)),'helper_groups_excluded':len(groups)-1,'source_bones':len(rig['bones']),'target_bones':len(names),'max_source_influences':max(source_counts[vi] for vi in used),'max_output_influences':max(map(len,out_weights)),'source_weight_sum_error_max':max(source_sum_errors),'pruned_vertices':sum(v>1e-12 for v in all_disc),'pruning_review_vertices':[{'source_vertex_index':vi,'discarded_weight_fraction':discarded[vi],'pruned_vs_unpruned_tpose_error_m':norm(sub(posed[vi],finish(full[vi]))),'retained_weights':weights[vi]} for vi in sorted(used,key=lambda vi:(-discarded[vi],vi))[:20]],'discarded_weight_max':max(all_disc),'discarded_weight_mean':statistics.mean(all_disc),'discarded_weight_p95':all_disc[int(.95*(len(all_disc)-1))],'pruning_pose_displacement_max_m':max(prune_errors)*final_scale,'pruning_pose_displacement_mean_m':statistics.mean(prune_errors)*final_scale,'zero_area_triangles':zero_area,'height_m':max(v[1] for v in vertices)-min(v[1] for v in vertices),'ground_min_y_m':min(v[1] for v in vertices),'chosen_height_m':height,'initial_source_scale':scale,'final_registration_scale':final_scale,'hand_head_bilateral_error_m':symmetry,'arm_horizontal_error_m':max(abs(target[n][1][1]-target[n][0][1]) for n in ['upperarm_l','upperarm_r','lowerarm_l','lowerarm_r','hand_l','hand_r']),'thumb_forward_z_delta_m':{s:target['thumb_01_'+s][1][2]-target['thumb_01_'+s][0][2] for s in ['l','r']},'gaps':['Body shape uses a recorded graphical target recipe when supplied; still not an attested phenotype or period-clothed photographic asset','Engineering LBS A-to-T correction needs visual shoulder/elbow/wrist/hip corrective sculpt review; positions alone do not prove a good deformation rig','Shortest-arc hand/finger transforms do not fully constrain bone roll or prove palms-down skin orientation; canonical Blender author must solve roll from anatomical landmarks','Source facial/tongue bones collapsed to head/jaw; no ARKit morphs or expression quality supplied','No skin photographic texture, eyes/teeth/hair/clothing, LODs, seated/walking clips or canonical .blend provided']}
 return {'license':'CC0-1.0','format':'chicago4d_human_base_preparation_v1','units':'m','up_axis':'+Y','forward_axis':'+Z','rest_pose':'engineering T-pose candidate; roll/deformation review pending','meshes':[{'name':'body','material':'skin','positions_m':vertices,'triangles':triangles,'uvs':texcoords,'weights':out_weights,'source_vertex_indices':source_vertex,'morphs':{}}],'skeleton':[{'name':n,'parent':parent,'head_m':target[n][0],'tail_m':target[n][1],'source_anchor_basis':source_anchors[n],'source_head_m':finish(source[n][0]),'source_tail_m':finish(source[n][1])} for n,parent in contract],'source_bone_map':{n:{'target':mapping[n],'reason':reasons[n]} for n in sorted(mapping)},'source':provenance,'target_blend':target_blend,'liberties':['Chosen adult height and skeletal chain collapse are reconstructed engineering choices','Arm/leg straightening, finger flattening and skinning transfer are original provisional adaptations, not anatomical source measurements'],'report':report}

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--source-dir',type=pathlib.Path,default=DEFAULT);ap.add_argument('--source-manifest',default='SOURCE.json',help='Explicit local alternative source manifest; default preserves original source provenance');ap.add_argument('--height-m',type=float,default=1.75);ap.add_argument('--target-recipe',type=pathlib.Path);ap.add_argument('--output',type=pathlib.Path,default=DEFAULT/'prepared.json');args=ap.parse_args();data=prepare(args.source_dir,args.height_m,args.target_recipe,args.source_manifest);args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(data,separators=(',',':'))+'\n');args.output.with_suffix('.report.json').write_text(json.dumps(data['report'],indent=2)+'\n');print(json.dumps(data['report'],indent=2))
if __name__=='__main__':main()
