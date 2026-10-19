#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Actual decoded GLB bind-pose regression; stdlib, no cached pose/green receipt."""
import json,struct,math,pathlib,tempfile,gzip,sys,hashlib,itertools
ROOT=pathlib.Path(__file__).resolve().parents[2]
PARTS={'breastcollar','breastcollar_support_l','breastcollar_support_r','harness_saddle_pad'}
def sub(a,b):return tuple(x-y for x,y in zip(a,b))
def dot(a,b):return sum(x*y for x,y in zip(a,b))
def cross(a,b):return(a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
def identity():return [[float(i==j)for j in range(4)]for i in range(4)]
def mm(a,b):return [[sum(a[i][k]*b[k][j]for k in range(4))for j in range(4)]for i in range(4)]
def point(m,p):return tuple(sum(m[i][j]*p[j]for j in range(3))+m[i][3]for i in range(3))
def local(n):
 if 'matrix'in n:return [[n['matrix'][j*4+i]for j in range(4)]for i in range(4)]
 x,y,z,w=n.get('rotation',[0,0,0,1]);s=n.get('scale',[1,1,1]);t=n.get('translation',[0,0,0]);r=[[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],[2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],[2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]];m=identity()
 for i in range(3):
  for j in range(3):m[i][j]=r[i][j]*s[j]
  m[i][3]=t[i]
 return m
def load(path):
 raw=path.read_bytes();assert raw[:4]==b'glTF';n=struct.unpack_from('<I',raw,12)[0];g=json.loads(raw[20:20+n]);binary=raw[28+n:]
 def values(i):
  a=g['accessors'][i];v=g['bufferViews'][a['bufferView']];fmt,size={5126:('f',4),5125:('I',4),5123:('H',2),5121:('B',1)}[a['componentType']];width={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}[a['type']];stride=v.get('byteStride',width*size);off=v.get('byteOffset',0)+a.get('byteOffset',0);return [struct.unpack_from('<'+fmt*width,binary,off+k*stride)for k in range(a['count'])]
 parents={c:i for i,n in enumerate(g['nodes'])for c in n.get('children',[])};worlds={}
 def world(i):
  if i not in worlds:worlds[i]=mm(world(parents[i]),local(g['nodes'][i]))if i in parents else local(g['nodes'][i])
  return worlds[i]
 active=set()
 def visit(i):
  assert i not in active,'Repeated node in active scene'
  active.add(i)
  for child in g['nodes'][i].get('children',[]):visit(child)
 for i in g['scenes'][g.get('scene',0)]['nodes']:visit(i)
 triangles=[]
 for i,n in enumerate(g['nodes']):
  if i not in active or 'mesh'not in n:continue
  mesh=g['meshes'][n['mesh']]
  for q in mesh['primitives']:
   pos=values(q['attributes']['POSITION'])
   if'skin'in n:
    skin=g['skins'][n['skin']];ib=values(skin['inverseBindMatrices']);matrices=[mm(world(j),[[ib[k][col*4+row]for col in range(4)]for row in range(4)])for k,j in enumerate(skin['joints'])];js=values(q['attributes']['JOINTS_0']);ws=values(q['attributes']['WEIGHTS_0']);pos=[tuple(sum(point(matrices[j],v)[axis]*w for j,w in zip(joints,weights))for axis in range(3))for v,joints,weights in zip(pos,js,ws)]
   else:pos=[point(world(i),v)for v in pos]
   ix=[v[0]for v in values(q['indices'])]if'indices'in q else list(range(len(pos)))
   for j in range(0,len(ix),3):triangles.append((mesh['name'],j//3,tuple(pos[ix[j+k]]for k in range(3))))
 return triangles

def sat(a,b):
 ea=[sub(a[(i+1)%3],a[i])for i in range(3)];eb=[sub(b[(i+1)%3],b[i])for i in range(3)];na=cross(ea[0],ea[1]);nb=cross(eb[0],eb[1]);axes=[na,nb]+[cross(x,y)for x in ea for y in eb]+[cross(na,x)for x in ea]+[cross(nb,x)for x in eb]
 for axis in axes:
  length=math.sqrt(dot(axis,axis))
  if length<1e-14:continue
  axis=tuple(x/length for x in axis);aa=[dot(p,axis)for p in a];bb=[dot(p,axis)for p in b]
  if max(aa)<min(bb)-1e-8 or max(bb)<min(aa)-1e-8:return False
 return True

def proper(a,b):
 for source,target in[(a,b),(b,a)]:
  normal=cross(sub(target[1],target[0]),sub(target[2],target[0]));l=math.sqrt(dot(normal,normal))
  if l<1e-15:continue
  normal=tuple(x/l for x in normal);ds=[dot(sub(p,target[0]),normal)for p in source]
  for i in range(3):
   j=(i+1)%3;da,db=ds[i],ds[j]
   if not((da>1e-8 and db< -1e-8)or(da< -1e-8 and db>1e-8)):continue
   t=da/(da-db);p=tuple(source[i][k]*(1-t)+source[j][k]*t for k in range(3));u=sub(target[1],target[0]);v=sub(target[2],target[0]);w=sub(p,target[0]);uu=dot(u,u);uv=dot(u,v);vv=dot(v,v);wu=dot(w,u);wv=dot(w,v);den=uu*vv-uv*uv
   if abs(den)<1e-20:continue
   y=(vv*wu-uv*wv)/den;z=(uu*wv-uv*wu)/den
   if min(1-y-z,y,z)>1e-8:return {'point_m':p,'edge_signed_distances_m':[da,db],'face_barycentric':[1-y-z,y,z]}
 return None


def point_segment(p,a,b):
 u=sub(b,a);d=dot(u,u);t=max(0,min(1,dot(sub(p,a),u)/d))if d>1e-30 else 0
 return math.sqrt(dot(sub(p,tuple(a[k]+t*u[k]for k in range(3))),sub(p,tuple(a[k]+t*u[k]for k in range(3)))))
def point_triangle(p,t):
 a,b,c=t;u=sub(b,a);v=sub(c,a);n=cross(u,v);nn=dot(n,n)
 if nn>1e-30:
  signed=dot(sub(p,a),n);q=tuple(p[k]-signed*n[k]/nn for k in range(3));w=sub(q,a);uu=dot(u,u);uv=dot(u,v);vv=dot(v,v);den=uu*vv-uv*uv
  if den>1e-30:
   y=(vv*dot(w,u)-uv*dot(w,v))/den;z=(uu*dot(w,v)-uv*dot(w,u))/den
   if y>=0 and z>=0 and y+z<=1:return abs(signed)/math.sqrt(nn)
 return min(point_segment(p,t[k],t[(k+1)%3])for k in range(3))
def segment_distance(a,b,c,d):
 u=sub(b,a);v=sub(d,c);w=sub(a,c);A=dot(u,u);B=dot(u,v);C=dot(v,v);D=dot(u,w);E=dot(v,w);den=A*C-B*B
 best=min(point_segment(a,c,d),point_segment(b,c,d),point_segment(c,a,b),point_segment(d,a,b))
 if den>1e-24:
  s=(B*E-C*D)/den;t=(A*E-B*D)/den
  if 0<=s<=1 and 0<=t<=1:
   q=tuple(w[k]+s*u[k]-t*v[k]for k in range(3));best=min(best,math.sqrt(dot(q,q)))
 return best
def triangle_distance(a,b):
 if sat(a,b):return 0.0
 return min([point_triangle(p,b)for p in a]+[point_triangle(p,a)for p in b]+[segment_distance(a[i],a[(i+1)%3],b[j],b[(j+1)%3])for i in range(3)for j in range(3)])
def predicate_controls():
 a=((0.,0.,0.),(2.,0.,0.),(0.,2.,0.));b=((.2,.2,1.),(.5,.2,1.),(.2,.5,1.));assert abs(triangle_distance(a,b)-1)<1e-12
 assert triangle_distance(a,((.2,.2,0.),(.5,.2,0.),(.2,.5,0.)))==0
 crossface=((.5,.5,-1.),(.5,.5,1.),(1.,.5,1.));assert proper(a,crossface)is not None and triangle_distance(a,crossface)==0
 disjoint=((1.8,1.8,0.),(2.,1.8,0.),(1.8,2.,0.));assert not sat(a,disjoint) and triangle_distance(a,disjoint)>0
 assert abs(segment_distance((0,0,0),(1,0,0),(.5,-1,.3),(.5,1,.3))-.3)<1e-12
 assert abs(segment_distance((0,0,0),(1,0,0),(0,1,0),(1,1,0))-1)<1e-12
 assert abs(segment_distance((0,0,0),(0,0,0),(1,0,0),(2,0,0))-1)<1e-12

def bounds(t):return [tuple(min(v[k]for v in t)for k in range(3)),tuple(max(v[k]for v in t)for k in range(3))]
def cells(b):return itertools.product(*(range(math.floor(b[0][k]/.1),math.floor(b[1][k]/.1)+1)for k in range(3)))
def measure(gear,horse,required_clearance=0):
 part_counts={name:sum(row[0]==name for row in gear)for name in sorted(PARTS)}
 grid={};hb=[bounds(t[2])for t in horse]
 for i,b in enumerate(hb):
  for cell in cells(b):grid.setdefault(cell,[]).append(i)
 hits=[];proper_count=0;violations=[];near_pairs=0
 for name,fi,a in gear:
  if name not in PARTS:continue
  box=bounds(a);search=[tuple(v-required_clearance-1e-8 for v in box[0]),tuple(v+required_clearance+1e-8 for v in box[1])];candidates={i for cell in cells(search)for i in grid.get(cell,[])}
  for i in candidates:
   bb=hb[i]
   lower=math.sqrt(sum(max(0,box[0][k]-bb[1][k],bb[0][k]-box[1][k])**2 for k in range(3)))
   if required_clearance and lower<required_clearance:
    near_pairs+=1;distance=triangle_distance(a,horse[i][2])
    if distance<required_clearance:violations.append({'part':name,'gear_triangle':fi,'horse_triangle':horse[i][1],'distance_m':distance})
   if lower>1e-8:continue
   if sat(a,horse[i][2]):
    strict=proper(a,horse[i][2]);proper_count+=strict is not None;hits.append({'part':name,'gear_triangle':fi,'horse_mesh':horse[i][0],'horse_triangle':horse[i][1],'proper':strict})
 return {'active_part_triangles':part_counts,'active_horse_triangles':len(horse),'surface_pairs':len(hits),'proper_crossings':proper_count,'pairs':hits,'required_clearance_m':required_clearance,'exact_distance_candidates':near_pairs,'clearance_violations':violations}

def main():
 predicate_controls()
 horse_path=ROOT/'renderers/web/transport/horse/equine_light_harness_skinned_prototype_01.glb';gear_path=ROOT/'renderers/web/transport/harness/light_breastcollar_harness_reconstructed_01.glb'
 # Historical input identity is explicit; a later horse revision requires fresh allpose qualification.
 horse_hash=hashlib.sha256(horse_path.read_bytes()).hexdigest();assert horse_hash=='89b048b7cda748e6f3a7111aa8e4f3198b01fabf6015cae644c78ed02d385bc6','Horse baseline changed: rerun mechanical fit qualification'
 horse=load(horse_path)
 original_archive=ROOT/'tools/transport/fixtures/harness-before-body-fit.glb.gz'
 assert hashlib.sha256(original_archive.read_bytes()).hexdigest()=='cce8c06f3ff46346c133bdc4954546aa7533febd645bff61e6db5a2a11b5ebf9'
 original_bytes=gzip.decompress(original_archive.read_bytes());assert hashlib.sha256(original_bytes).hexdigest()=='b4a7318053e8508617a24fff64f02beb7eee77684db689dc04771d209a54fa8b'
 with tempfile.TemporaryDirectory(prefix='harness-bindpose-')as temp:
  original=pathlib.Path(temp)/'original.glb';original.write_bytes(original_bytes);before=measure(load(original),horse)
 after=measure(load(gear_path),horse,required_clearance=.005);receipt={'scope':'ActualGLB decoded skin-bindpose, wholeactivehorse versus4changedgearparts; no cachedgeometry/green, no animated/continuous/inside/pressureacceptance','horse_sha256':horse_hash,'gear_sha256':hashlib.sha256(gear_path.read_bytes()).hexdigest(),'baseline':before,'repaired':after}
 if len(sys.argv)>1:pathlib.Path(sys.argv[1]).write_text(json.dumps(receipt,indent=2)+'\n')
 assert before['proper_crossings']>0,'Original failure control no longer reproduced'
 assert after['active_horse_triangles'] and all(after['active_part_triangles'].values()),'Missing active horse or one of four harness parts'
 assert after['surface_pairs']==0,'Repaired bind-pose surface interference'
 assert not after['clearance_violations'],'Repaired bind-pose below declared 5 mm clearance'
 print('PASS actualbindpose originalproper='+str(before['proper_crossings'])+' repairedsurface=0;63animatedsamples separately qualified')
if __name__=='__main__':main()
