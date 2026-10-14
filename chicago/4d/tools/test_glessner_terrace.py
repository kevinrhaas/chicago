"""T-2218: real tread/landing rays and a closed rounded stone terminal."""
import sys,json,types,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'generators'))
sys.modules.setdefault('bpy',types.ModuleType('bpy'))
from archetypes.masonry_house_params import from_phase
from archetypes.masonry_house_v4_detail import DetailBuilder
from archetypes import masonry_house_v4_terrace as m
record=json.loads((ROOT/'data/structures/glessner_house.json').read_text())
p=from_phase(record['phases'][0],record)
bt=p.detail['bow_terrace']
class B(DetailBuilder):
    def wall(self,pts,confidence,mat,custom_holes=None):
        return self.raw(pts,confidence,mat)
from collections import Counter
def rays(b,x,y,material):
 hits=[]
 for face,mat in zip(b.faces,b.mat_index):
  if mat!=material:continue
  for j in range(1,len(face)-1):
   a,c,d=[b.verts[k] for k in (face[0],face[j],face[j+1])]
   det=(c[1]-d[1])*(a[0]-d[0])+(d[0]-c[0])*(a[1]-d[1])
   if abs(det)<1e-12:continue
   u=((c[1]-d[1])*(x-d[0])+(d[0]-c[0])*(y-d[1]))/det
   v=((d[1]-a[1])*(x-d[0])+(a[0]-d[0])*(y-d[1]))/det
   if min(u,v,1-u-v)>=-1e-8:hits.append(u*a[2]+v*c[2]+(1-u-v)*d[2])
 return hits
for reduced in (False,True):
 b=B('terrace',p);b.decorate=False;b.smooth_rock_faces=not reduced;m.build(b,p)
 heights=[]
 for i,(edge,nxt) in enumerate(zip(bt['stair_boundaries'],bt['stair_boundaries'][1:])):
  x,y=[sum(q[k] for q in edge+nxt)/4 for k in range(2)]
  hit=rays(b,x,y,2)
  assert hit,('missing tread',i)
  heights.append(max(hit))
  if i>0:assert not rays(b,x,y,8),('landing protrudes over tread',i)
 expected=[1.68,1.49,1.31,1.12,.93,.75,.56,.37,.19]
 assert all(abs(a-c)<.015 for a,c in zip(heights,expected)),heights
 print('nine independent walk-line ray heights',reduced,[round(h,3) for h in heights])
 for face,mat in zip(b.faces,b.mat_index):
  if mat!=m.BRICK:continue
  c=[sum(b.verts[i][k] for i in face)/len(face) for k in range(3)]
  angle=math.atan2(c[1]-bt['cy'],c[0]-bt['cx'])%(2*math.pi)
  if not bt['window_z'][0]+.04<c[2]<bt['window_z'][1]-.04:continue
  for near,far in bt['window_distance']:
   lo=math.pi+math.asin(near/bt['r']);hi=math.pi+math.asin(far/bt['r'])
   assert not lo+.025<angle<hi-.025,('brick blocks a grille',reduced,c)
 print('paired grille openings clear through both wall faces',reduced)
 bow=p.bows[0];a0,a1=sorted((bow['a0'],bow['a1']))
 if a1-a0>math.pi:a0,a1=a1,a0+2*math.pi
 angle=(a0+a1)/2
 # The leaf is recessed behind the opening's straight chord, not its outer arc.
 half=(a1-a0)/bow['lights_per_row']*.28
 radius=bow['r']*math.cos(half)-.25
 for delta in (-half*.8,0,half*.8):
  x=bow['cx']+radius*math.cos(angle+delta);y=bow['cy']+radius*math.sin(angle+delta)
  hit=rays(b,x,y,8)
  assert hit and abs(max(hit)-(bt['z1']-.18))<.002,('gap at recessed door threshold',reduced,delta)
 print('landing meets the recessed door threshold across the leaf',reduced)
 # The retained reveal/sill share the deck height. The visible stone threshold
 # must cover them with a real depth separation, including the jamb ends.
 normal=(math.cos(angle),math.sin(angle));tangent=(-normal[1],normal[0])
 width=2*bow['r']*math.sin(half);chord=bow['r']*math.cos(half)
 for u in (-width/2-.19,0,width/2+.19):
  for off in (-.28,-.01,.05):
   x=bow['cx']+(chord+off)*normal[0]+u*tangent[0]
   y=bow['cy']+(chord+off)*normal[1]+u*tangent[1]
   hit=rays(b,x,y,2)
   assert hit and abs(max(hit)-(bt['z1']-.18+.006))<.0001,('threshold depth separation',reduced,u,off,hit)
 print('stone threshold covers the coplanar reveal and sill',reduced)
 # Independently read section ordinates, metres over grade, on the exposed cap.
 for south,upper,lower in ((43,2.52,2.30),(44,2.32,1.98),(44.5,2.13,1.46),(45,1.78,1.22)):
  a=math.pi+math.asin((south-28.8)*.3048/(bt['r']+.055))
  x=bt['cx']+(bt['r']+.054)*math.cos(a);y=bt['cy']+(bt['r']+.054)*math.sin(a)
  hits=rays(b,x,y,2)
  assert hits and abs(max(hits)-upper)<.04 and abs(min(hits)-lower)<.04,('coping section edges',reduced,south,hits)
 print('both coping edges follow independent section ordinates',reduced)



 post=B('post',p);post.smooth_rock_faces=not reduced;m._newel(post,bt,1,reduced)
 edges=Counter()
 for f in post.faces:
  vs=[tuple(round(q,7) for q in post.verts[i]) for i in f]
  for a,c in zip(vs,vs[1:]+vs[:1]):edges[tuple(sorted((a,c)))]+=1
 assert set(edges.values())=={2},Counter(edges.values())
 print('closed post, below grade to rounded crown',min(v[2] for v in post.verts),max(v[2] for v in post.verts))
