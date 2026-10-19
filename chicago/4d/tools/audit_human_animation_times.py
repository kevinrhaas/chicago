#!/usr/bin/env python3
"""Validate DECLARED GLB animation time bounds, not decoded samples or motion."""
import hashlib,json,math,struct,sys
from pathlib import Path
SCOPE='serialized animation time accessor min/max metadata, NOT decoded loaded motion/contact'
def finite(value):
 try:return isinstance(value,(float,int)) and not isinstance(value,bool) and math.isfinite(value)
 except OverflowError:return False
def require(ok,message):
 if not ok:raise ValueError(message)
def index(value,length):
 require(isinstance(value,int) and not isinstance(value,bool) and 0<=value<length,'invalid input accessor index')
 return value
def audit_document(doc):
 require(isinstance(doc,dict),'GLB JSON must be object')
 accessors=doc.get('accessors');animations=doc.get('animations')
 require(isinstance(accessors,list),'accessors must be array')
 require(isinstance(animations,list) and bool(animations),'animations must be nonempty array')
 clips=[]
 for anim in animations:
  require(isinstance(anim,dict),'animation must be object')
  name=anim.get('name');require(isinstance(name,str) and bool(name),'animation name required')
  samplers=anim.get('samplers');require(isinstance(samplers,list) and bool(samplers),'animation samplers must be nonempty array')
  ids=set()
  for sampler in samplers:
   require(isinstance(sampler,dict),'sampler must be object');ids.add(index(sampler.get('input'),len(accessors)))
  pairs=[]
  for i in sorted(ids):
   ac=accessors[i];require(isinstance(ac,dict),'accessor must be object')
   require(isinstance(ac.get('componentType'),int) and ac.get('componentType')==5126 and not isinstance(ac.get('componentType'),bool) and ac.get('type')=='SCALAR','time accessor must be FLOAT SCALAR')
   count=ac.get('count');require(isinstance(count,int) and not isinstance(count,bool) and count>0,'time accessor count must be positive integer')
   bounds=[]
   for key in ['min','max']:
    a=ac.get(key);require(isinstance(a,list) and len(a)==1 and finite(a[0]),'time accessor '+key+' must be singleton finite numeric array');bounds.append(a[0])
   lo,hi=bounds;require(0<=lo<=hi,'time accessor bounds must be nonnegative and ordered');pairs.append((lo,hi))
  extras=anim.get('extras',{});require(isinstance(extras,dict),'animation extras must be object')
  clips.append({'name':name,'extras':{k:extras.get(k) for k in ['speed_m_s','stance_fraction','cycle_duration_s']},'input_accessor_count':len(ids),'serialized_bounds_unique':sorted(set(pairs))})
 walks=[c for c in clips if c['name']=='walk'];require(len(walks)==1,'exactly one named walk required: '+repr([c['name'] for c in clips]))
 w=walks[0];pairs=w['serialized_bounds_unique']
 require(all(abs(lo)<=1e-6 and hi<=1.2+1e-5 for lo,hi in pairs) and abs(max(hi for lo,hi in pairs)-1.2)<=1e-5,'walk declared time bounds must start0 and end1.2: '+json.dumps(w,allow_nan=False))
 for k,v in [('speed_m_s',.6),('stance_fraction',.62),('cycle_duration_s',1.2)]:
  actual=w['extras'][k];require(finite(actual) and abs(actual-v)<=1e-6,'walk declared '+k+' mismatch or missing')
 return clips
def reject_constant(value):raise ValueError('nonfinite JSON constant '+value)
def inspect_file(path):
 result={'file':str(path),'sha256':None,'scope':SCOPE,'passed':False}
 try:
  data=Path(path).read_bytes();result['sha256']=hashlib.sha256(data).hexdigest()
  require(len(data)>=20,'truncated GLB header')
  require(struct.unpack_from('<III',data)==(0x46546c67,2,len(data)),'invalid GLB magic/version/length')
  size,kind=struct.unpack_from('<II',data,12);require(kind==0x4e4f534a and size%4==0 and 20+size<=len(data),'invalid GLB JSON chunk')
  doc=json.loads(data[20:20+size],parse_constant=reject_constant)
  result['clips']=audit_document(doc);result['passed']=True
 except (ValueError,TypeError,KeyError,IndexError,struct.error,OSError) as error:result['error']=str(error)
 return result
def main(args):
 if not args:
  print('usage: audit_human_animation_times.py resident.glb [...]',file=sys.stderr);return 2
 failed=False
 for path in args:
  result=inspect_file(path);print(json.dumps(result,separators=(',',':'),allow_nan=False));failed|=not result['passed']
 return int(failed)
if __name__=='__main__':raise SystemExit(main(sys.argv[1:]))
