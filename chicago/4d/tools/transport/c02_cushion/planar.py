# SPDX-License-Identifier: CC0-1.0
"""Original constrained planar arrangement and simple-polygon triangulation."""
import math

def need(c,m):
 if not c:raise ValueError(m)
def cross(a,b,c):return(b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
def area(p):return sum(a[0]*b[1]-a[1]*b[0]for a,b in zip(p,p[1:]+p[:1]))/2

def triangulate(loop,points):
 """Ear clipping retains ALL constrained boundary knots, including collinear."""
 ids=list(loop);need(len(ids)==len(set(ids))and len(ids)>=3,'Repeated/short polygon')
 if area([points[i]for i in ids])<0:ids.reverse()
 result=[]
 while len(ids)>3:
  found=False
  for k,b in enumerate(ids):
   a=ids[k-1];c=ids[(k+1)%len(ids)];A,B,C=points[a],points[b],points[c]
   if cross(A,B,C)<=1e-16:continue
   blocked=False
   for j in ids:
    if j in[a,b,c]:continue
    q=points[j]
    if min(cross(A,B,q),cross(B,C,q),cross(C,A,q))>=-1e-16:blocked=True;break
   if blocked:continue
   result.append([a,b,c]);ids.pop(k);found=True;break
  need(found,'No valid constrained ear; self fold/degenerate arrangement')
 need(abs(cross(*[points[i]for i in ids]))>1e-16,'Degenerate final triangle');result.append(ids)
 return result

def bounded_faces(points,edges):
 """Enumerate bounded faces of a noncrossing straight-line graph.
 Every constraint endpoint must already split EVERY incident segment.
 """
 adj={i:set()for i in points}
 for a,b in edges:need(a!=b,'Zero graph edge');adj[a].add(b);adj[b].add(a)
 order={i:sorted(js,key=lambda j:math.atan2(points[j][1]-points[i][1],points[j][0]-points[i][0]))for i,js in adj.items()};seen=set();loops=[]
 for a in order:
  for b in order[a]:
   if(a,b)in seen:continue
   start=(a,b);loop=[];x,y=a,b
   for _ in range(2*len(edges)+1):
    need((x,y)not in seen,'Graph face repeats before closure');seen.add((x,y));loop.append(x);ne=order[y];z=ne[(ne.index(x)-1)%len(ne)];x,y=y,z
    if(x,y)==start:break
   else:raise ValueError('Open/branched constraint walk')
   need(len(loop)==len(set(loop)),'Non-simple graph face; hole requires explicit bridge')
   if area([points[i]for i in loop])>1e-16:loops.append(loop)
 need(len(seen)==2*len(edges),'Incomplete half-edge ownership');return loops

def point_in_polygon(q,poly):
 yes=False
 for a,b in zip(poly,poly[1:]+poly[:1]):
  if(a[1]>q[1])!=(b[1]>q[1])and q[0]<(b[0]-a[0])*(q[1]-a[1])/(b[1]-a[1])+a[0]:yes=not yes
 return yes

def clip_polygon(poly,triangle):
 poly=[list(p)for p in poly];t=[list(p)for p in triangle]
 if area(t)<0:t.reverse()
 for a,b in zip(t,t[1:]+t[:1]):
  old=poly;poly=[]
  if not old:break
  for p,q in zip(old,old[1:]+old[:1]):
   cp=cross(a,b,p);cq=cross(a,b,q)
   if cp>=0:poly.append(p)
   if cp*cq<0:
    f=cp/(cp-cq);poly.append([p[k]+f*(q[k]-p[k])for k in range(2)])
 return poly

def coverage(triangles,points,expected_loop):
 """Reject overlapping, inverted, outside or incompletely covered triangles."""
 polys=[[points[i]for i in t]for t in triangles];target=abs(area([points[i]for i in expected_loop]));total=sum(abs(area(p))for p in polys);need(abs(total-target)<1e-12,'Incomplete/duplicate patch area')
 for i,a in enumerate(polys):
  need(area(a)>1e-16,'Inverted/zero planar triangle')
  for b in polys[i+1:]:need(abs(area(clip_polygon(a,b)))<=1e-15,'Overlapping planar triangle interiors')
 # Triangulated simple loop is the containing region; test exact intersection
 # area of each output with that independently triangulated region.
 region=triangulate(expected_loop,points)
 for a in polys:
  covered=sum(abs(area(clip_polygon(a,[points[i]for i in t])))for t in region);need(abs(covered-abs(area(a)))<1e-12,'Triangle escapes planar patch')
 return{'triangles':len(triangles),'area':target,'max_pair_overlap_area_threshold':1e-15}
