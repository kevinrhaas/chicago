#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Authored-only float32 joint-scale residue repair; never a general asset importer."""
import copy,hashlib,json,math,pathlib,struct
CAP=32*2**-23
class Rejected(ValueError):pass
def sha(b):return hashlib.sha256(b).hexdigest()
def parse(raw):
 if len(raw)<20 or struct.unpack_from('<III',raw)!=(0x46546c67,2,len(raw)):raise Rejected('invalid GLB header')
 chunks=[];off=12
 while off<len(raw):
  if off+8>len(raw):raise Rejected('short chunk')
  n,kind=struct.unpack_from('<II',raw,off);off+=8
  if n%4 or off+n>len(raw):raise Rejected('invalid chunk length')
  chunks.append((kind,raw[off:off+n]));off+=n
 if not chunks or chunks[0][0]!=0x4e4f534a:raise Rejected('JSON first required')
 try:d=json.loads(chunks[0][1])
 except Exception as e:raise Rejected('bad JSON') from e
 return d,chunks
def number(x):return isinstance(x,(int,float)) and not isinstance(x,bool) and math.isfinite(x)
def uint(x):return isinstance(x,int) and not isinstance(x,bool) and x>=0
def index(x,seq,label):
 if not uint(x) or x>=len(seq):raise Rejected('invalid '+label+' index')
 return seq[x]
def unit_scale(s):
 if not isinstance(s,list) or len(s)!=3 or not all(number(x) for x in s):raise Rejected('nonfinite/malformed scale')
 if max(abs(x-1) for x in s)>CAP:raise Rejected('scale exceeds float32 residue cap')
def identity():return [[float(i==j) for j in range(4)]for i in range(4)]
def mul(a,b):return [[sum(a[i][k]*b[k][j] for k in range(4))for j in range(4)]for i in range(4)]
def local(n):
 if 'matrix'in n:
  a=n['matrix']
  if len(a)!=16 or not all(number(x)for x in a):raise Rejected('bad matrix')
  return [[a[j*4+i]for j in range(4)]for i in range(4)]
 t=n.get('translation',[0,0,0]);q=n.get('rotation',[0,0,0,1]);s=n.get('scale',[1,1,1])
 if len(t)!=3 or len(q)!=4 or len(s)!=3 or not all(number(v)for v in t+q+s):raise Rejected('malformed TRS')
 x,y,z,w=q;m=identity();r=[[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],[2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],[2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]]
 for i in range(3):
  for j in range(3):m[i][j]=r[i][j]*s[j]
  m[i][3]=t[i]
 return m
def worlds(d):
 nodes=d.get('nodes',[]);parents={}
 for i,n in enumerate(nodes):
  for c in n.get('children',[]):
   if not uint(c) or c>=len(nodes) or c in parents:raise Rejected('invalid node hierarchy')
   parents[c]=i
 out={};busy=set()
 def visit(i):
  if i in busy:raise Rejected('cyclic node graph')
  if i in out:return out[i]
  busy.add(i);out[i]=mul(visit(parents[i]),local(nodes[i])) if i in parents else local(nodes[i]);busy.remove(i);return out[i]
 for i in range(len(nodes)):visit(i)
 return out
def decode_float_accessor(d,chunks,idx,kind):
 a=index(idx,d.get('accessors',[]),'accessor')
 if a.get('componentType')!=5126 or a.get('type')!=kind or 'sparse' in a or a.get('normalized') or 'extensions' in a:
  raise Rejected('only nonsparse unextended FLOAT '+kind+' accessor supported')
 v=index(a.get('bufferView'),d.get('bufferViews',[]),'bufferView')
 buffer=index(v.get('buffer'),d.get('buffers',[]),'buffer')
 if v['buffer']!=0 or 'uri' in buffer:raise Rejected('only embedded buffer0 supported')
 if 'extensions' in v or 'extensions' in buffer:raise Rejected('extended scale buffer/views unsupported')
 bins=[b for k,b in chunks if k==0x004e4942]
 if len(bins)!=1:raise Rejected('one BIN required')
 blob=bins[0];width={'VEC3':3,'SCALAR':1}[kind];item_bytes=width*4
 stride=v.get('byteStride',item_bytes);voff=v.get('byteOffset',0);aoff=a.get('byteOffset',0)
 count=a.get('count');vlen=v.get('byteLength');blen=buffer.get('byteLength')
 if not all(uint(x)for x in [stride,voff,aoff,count,vlen,blen]) or count==0:
  raise Rejected('nonnegative nonbool integer buffer layout required')
 if stride<item_bytes or stride%4 or ('byteStride' in v and not 4<=stride<=252):
  raise Rejected('invalid accessor stride')
 start=voff+aoff;end=start+(count-1)*stride+item_bytes
 if start%4 or voff+vlen>blen or blen>len(blob) or aoff>vlen or end>min(blen,voff+vlen):
  raise Rejected('out of bounds or unaligned accessor')
 rows=[list(struct.unpack_from('<'+'f'*width,blob,start+i*stride))for i in range(count)]
 if not all(number(x)for row in rows for x in row):raise Rejected('nonfinite accessor sample')
 return rows

def decoded_scales(d,chunks,idx):
 values=decode_float_accessor(d,chunks,idx,'VEC3')
 for s in values:unit_scale(s)
 return values
def repair(raw,proof):
 required=['rig_object_scales_unit','pose_bone_scales_unit','no_constraints','no_drivers','no_scale_fcurves','authored_rigid_rig']
 if not isinstance(proof,dict)or proof.get('input_sha256')!=sha(raw)or any(not isinstance(proof.get(k),str)or not proof[k].strip()for k in ['verified_by','verification_reference'])or any(proof.get(k)is not True for k in required):raise Rejected('explicit input-bound verified-rigid-rig proof required')
 d,chunks=parse(raw);original=copy.deepcopy(d);nodes=d.get('nodes',[]);joints=set()
 for skin in d.get('skins',[]):
  for i in skin.get('joints',[]):
   if not isinstance(i,int)or isinstance(i,bool)or not 0<=i<len(nodes):raise Rejected('invalid joint index')
   joints.add(i)
 if not joints:raise Rejected('skin joint set required')
 changes=[]
 for i,n in enumerate(nodes):
  if 'matrix'in n:
   if i in joints:raise Rejected('joint matrix transforms unsupported')
   if any(k in n for k in ['translation','rotation','scale']):raise Rejected('matrix mixed with TRS')
   m=local(n)
   norms=[math.hypot(*(m[r][c] for r in range(3)))for c in range(3)]
   if max(abs(x-1)for x in norms)>1e-6:raise Rejected('nonjoint matrix scale exceeds unchanged 1e-6 frame guard')
  if 'scale'in n:
   unit_scale(n['scale'])
   if i not in joints:
    if max(abs(x-1)for x in n['scale'])>1e-6:raise Rejected('nonjoint scale exceeds unchanged 1e-6 frame guard')
   else:
    changes.append({'kind':'joint_scale_removed','node':i,'name':n.get('name'),'before':n['scale'],'after':[1,1,1]});del n['scale']
 for ai,anim in enumerate(d.get('animations',[])):
  keep=[];removed=[]
  for ci,c in enumerate(anim.get('channels',[])):
   if c.get('target',{}).get('path')!='scale':keep.append(c);continue
   ni=c['target'].get('node')
   if not uint(ni) or ni not in joints:raise Rejected('nonjoint animation scale not authorized')
   sampler=index(c.get('sampler'),anim.get('samplers',[]),'scale sampler')
   if sampler.get('interpolation','LINEAR')not in ('LINEAR','STEP'):raise Rejected('CUBICSPLINE/unknown scale interpolation unsupported')
   values=decoded_scales(d,chunks,sampler.get('output'))
   times=[row[0] for row in decode_float_accessor(d,chunks,sampler.get('input'),'SCALAR')]
   if len(times)!=len(values):raise Rejected('scale input/output counts differ')
   if times[0]<0 or any(b<=a for a,b in zip(times,times[1:])):raise Rejected('invalid scale sample times')
   removed.append(ci);changes.append({'kind':'joint_scale_channel_removed','animation':ai,'clip':anim.get('name'),'channel':ci,'node':ni,'samples':len(values),'max_abs_residue':max(abs(x-1)for s in values for x in s),'output_accessor':sampler.get('output')})
  if removed:
   anim['channels']=keep
   if not keep:raise Rejected('repair would leave empty animation; unsupported')
   used=sorted({c['sampler']for c in keep});mapping={old:new for new,old in enumerate(used)};anim['samplers']=[anim['samplers'][i]for i in used]
   for c in keep:c['sampler']=mapping[c['sampler']]
 before=worlds(original);after=worlds(d);delta=[]
 for i in sorted(joints):
  a,b=before[i],after[i];translation=math.sqrt(sum((a[j][3]-b[j][3])**2 for j in range(3)));linear=math.sqrt(sum((a[j][k]-b[j][k])**2 for j in range(3)for k in range(3)))
  delta.append({'node':i,'name':nodes[i].get('name'),'translation_delta_m':translation,'linear_delta_frobenius':linear,'bound_for_point_within_1m_of_joint_m':translation+linear})
 # Retain every binary and unknown chunk byte exactly; only JSON is reserialized.
 encoded=json.dumps(d,separators=(',',':'),allow_nan=False).encode();encoded+=b' '*((-len(encoded))%4);parts=[(chunks[0][0],encoded)]+chunks[1:];body=b''.join(struct.pack('<II',len(b),k)+b for k,b in parts);output=struct.pack('<III',0x46546c67,2,12+len(body))+body
 nonjson_before=[{'type':k,'bytes':len(b),'sha256':sha(b)}for k,b in chunks[1:]];nonjson_after=[{'type':k,'bytes':len(b),'sha256':sha(b)}for k,b in parse(output)[1][1:]]
 assert nonjson_before==nonjson_after
 for field in ['meshes','skins','accessors','bufferViews','buffers']:assert original.get(field)==d.get(field),field
 receipt={'input_sha256':sha(raw),'output_sha256':sha(output),'cap':CAP,'cap_basis':'32 * 2**-23 absolute unit-scale residue','proof':proof,'changes':changes,'nonjson_chunks':nonjson_before,'binary_bytes_preserved':True,'meshes_skins_ibm_accessors_unchanged':True,'rest_joint_deltas':delta,'max_rest_translation_delta_m':max(x['translation_delta_m']for x in delta),'max_rest_1m_point_bound_m':max(x['bound_for_point_within_1m_of_joint_m']for x in delta),'clip_world_deltas':'not evaluated; LINEAR unit-near sample bounds validated, STEP likewise; animation removing tiny scale is intentional, not exact visual equivalence','warnings':['Only caller-verified original rigid-rig export residue qualifies. This is not source-asset normalization.','No change to contract frame tolerance; validate repaired output using unchanged frame guard.','Rest bound is on joint frame points <=1m, not a proof of skinned surface equivalence with unchanged inverse bind matrices.']}
 return output,receipt
if __name__=='__main__':
 import argparse
 ap=argparse.ArgumentParser();ap.add_argument('input',type=pathlib.Path);ap.add_argument('output',type=pathlib.Path);ap.add_argument('--proof',type=pathlib.Path,required=True);ap.add_argument('--receipt',type=pathlib.Path,required=True);a=ap.parse_args();out,r=repair(a.input.read_bytes(),json.loads(a.proof.read_text()));a.output.write_bytes(out);a.receipt.write_text(json.dumps(r,indent=2)+'\n')
