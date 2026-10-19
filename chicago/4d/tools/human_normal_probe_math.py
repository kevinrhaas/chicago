# SPDX-License-Identifier: GPL-3.0-or-later
"""Pure mathematical probe recovery. No bpy, files, hidden state or authoring."""
import math
S=32767
PROBES={'zero':(0,0),'alpha':(S,0),'beta':(S,8192),
        'negative_alpha':(-8192,0),'negative_beta':(16384,-16384)}
class Refused(ValueError):pass
def dot(a,b):return math.fsum(x*y for x,y in zip(a,b))
def scale(a,t):return tuple(x*t for x in a)
def add(a,b):return tuple(x+y for x,y in zip(a,b))
def cross(a,b):return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
def norm(a):return math.hypot(*a)
def unit(a,tolerance=1e-5):
 if len(a)!=3 or not all(math.isfinite(x)for x in a):raise Refused('nonfinite/malformed probe')
 length=norm(a)
 if abs(length-1)>tolerance:raise Refused('nonunit/invalid probe')
 return scale(a,1/length)
def distance(a,b):return norm(tuple(x-y for x,y in zip(a,b)))
def decode(frame,code):
 a,b=code
 if any(not isinstance(v,int) or isinstance(v,bool) or not -S<=v<=S for v in code):raise Refused('invalid Short2 code')
 N,R,O,A,B=frame
 if a==0 or A==0 or B==0:return N
 alpha=(A if a>0 else 2*math.pi-A)*a/S
 beta=(B if b>0 else 2*math.pi-B)*b/S
 return add(scale(N,math.cos(alpha)),add(scale(R,math.sin(alpha)*math.cos(beta)),scale(O,math.sin(alpha)*math.sin(beta))))
def recover(probes,heldout_tolerance=2e-5):
 if not math.isfinite(heldout_tolerance)or not 0<heldout_tolerance<=2e-5:raise Refused('invalid held-out tolerance')
 if set(probes)!=set(PROBES):raise Refused('all recovery and signed held-out probes required')
 p={name:unit(value)for name,value in probes.items()};N=p['zero'];pa=p['alpha']
 c=max(-1,min(1,dot(N,pa)));A=math.acos(c);s=math.sin(A)
 if s<.01:raise Refused('alpha probe ill-conditioned: A=%g sinA=%g'%(A,s))
 R=unit(scale(add(pa,scale(N,-c)),1/s));O=unit(cross(N,R))
 pb=p['beta'];x=dot(pb,R);y=dot(pb,O);angle=math.atan2(y,x);B=angle/(8192/S)
 if not .01<=B<=2*math.pi+1e-6:raise Refused('beta reference outside supported/conditioned interval: B=%g'%B)
 B=min(2*math.pi,B)
 if abs(s*math.sin(angle))<1e-4:raise Refused('beta probe ill-conditioned: sinA_sinProbe=%g'%(s*math.sin(angle)))
 frame=(N,R,O,A,B)
 errors={name:distance(decode(frame,code),p[name])for name,code in PROBES.items()}
 if max(errors.values())>heldout_tolerance:raise Refused('held-out/frame residual too large: max=%g'%max(errors.values()))
 return frame,errors
def quantize(value):
 if not math.isfinite(value)or abs(value)>1+1e-10:raise Refused('unrepresentable normalized code')
 value=max(-1,min(1,value));return math.floor(value*S+.5)
def inverse(frame,target):
 target=unit(target,1e-6);N,R,O,A,B=frame
 x,y,z=dot(target,R),dot(target,O),dot(target,N)
 alpha=math.atan2(math.hypot(x,y),z);beta=math.atan2(y,x)%(2*math.pi)
 a=quantize(alpha/A if alpha<=A else -(2*math.pi-alpha)/(2*math.pi-A))
 b=quantize(beta/B if beta<=B else -(2*math.pi-beta)/(2*math.pi-B))
 code=(a,b)
 # Pure model validation; production MUST separately read actual Blender corners.
 if distance(decode(frame,code),target)>1e-3:raise Refused('model target readback exceeds unchanged1e-3 guard')
 return code
def recover_group_codes(vertex_indices,per_corner_probes,targets):
 if not targets or not(len(vertex_indices)==len(per_corner_probes)==len(targets)):raise Refused('corner arrays differ')
 groups={};codes=[None]*len(targets)
 for i,(vertex,p)in enumerate(zip(vertex_indices,per_corner_probes)):
  if not isinstance(vertex,int)or isinstance(vertex,bool)or vertex<0:raise Refused('invalid corner vertex')
  # Actual decoder copies ONE fan_normal to every fan corner. Uniform probes
  # therefore give identical signatures within each real fan. Equivalent frames
  # in separate fans may safely share a code only for matching desired normals.
  if set(p)!=set(PROBES):raise Refused('incomplete corner probes')
  key=(vertex,tuple((name,tuple(p[name]))for name in PROBES))
  groups.setdefault(key,[]).append(i)
 for members in groups.values():
  first=members[0];target=unit(targets[first],1e-6)
  if any(distance(target,unit(targets[i],1e-6))>1e-12 for i in members):raise Refused('probe-equivalent fan has incoherent targets')
  try:
   frame,_=recover(per_corner_probes[first]);code=inverse(frame,target)
  except Refused as error:raise Refused('probe group loop=%d vertex=%d corners=%d: %s'%(first,vertex_indices[first],len(members),error))from error
  for i in members:codes[i]=code
 return codes

def prototype_transaction(adapter,vertex_indices,source_ids,targets):
 """Adapter protocol experiment; actual Mesh execution still requires pinned CI.
 Adapter MUST write only Short2 codes and explicitly invalidate caches in update.
 """
 count=len(targets)
 if not count or not(count==len(vertex_indices)==len(source_ids)):raise Refused('nonempty equal corner arrays required')
 original=list(adapter.read_codes());invariant=adapter.invariant_digest();complete=False
 if len(original)!=count:raise Refused('original code count differs')
 for code in original:
  if len(code)!=2 or any(not isinstance(v,int)or isinstance(v,bool)or not -S<=v<=S for v in code):raise Refused('original Short2 codes invalid')
 try:
  by_corner=[{}for _ in targets]
  for name,code in PROBES.items():
   adapter.write_codes([code]*count);adapter.update();normals=adapter.read_normals()
   if len(normals)!=count:raise Refused('probe corner count changed')
   for i,normal in enumerate(normals):by_corner[i][name]=tuple(normal)
  codes=recover_group_codes(vertex_indices,by_corner,targets)
  adapter.write_codes(codes);adapter.update();actual=adapter.read_normals()
  if len(actual)!=count:raise Refused('final corner count changed')
  for a,b in zip(actual,targets):unit(a);unit(b,1e-6)
  # Preserve the current guard's RAW vectors; never normalize away output error.
  errors=[distance(tuple(a),tuple(b))for a,b in zip(actual,targets)]
  if max(errors)>1e-3:raise Refused('ACTUAL adapter target readback exceeds unchanged1e-3 guard')
  seams={}
  for sid,point in zip(source_ids,actual):
   if not isinstance(sid,int)or isinstance(sid,bool)or sid<0:raise Refused('invalid source ID')
   seams.setdefault(sid,set()).add(tuple(point))
  spread=max((distance(a,b)for values in seams.values()for a in values for b in values),default=0.0)
  if spread>1e-3:raise Refused('actual adapter seam spread exceeds prototype1e-3 gate')
  if adapter.invariant_digest()!=invariant:raise Refused('geometry/UV/weights/metadata invariant changed')
  complete=True
  return {'scope':'supplied adapter protocol measurement; caller must identify real versus mock execution','maximum_target_delta':max(errors),'maximum_seam_spread':spread,'corner_count':count,'code_pair_variants':len(set(codes))}
 finally:
  if not complete:
   adapter.write_codes(original);adapter.update()
   if list(adapter.read_codes())!=original:raise Refused('original Short2 restoration failed')
