# SPDX-License-Identifier: GPL-3.0-or-later
"""Original geometry proposal, not executed on C02. No image-derived vertices."""
import math

def require(ok,message):
 if not ok:raise ValueError(message)
def cross(a,b):return[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]]
def subtract(a,b):return[x-y for x,y in zip(a,b)]
def normalized(a):
 length=math.sqrt(sum(x*x for x in a));require(length>1e-12,'zero normal');return[x/length for x in a]
def perimeter(hx,hz,corner=.04,steps=6):
 require(hx>corner and hz>corner and steps==6,'fixed reviewed cushion profile')
 result=[]
 for cx,cz,start in[(hx-corner,hz-corner,0),(-hx+corner,hz-corner,math.pi/2),(-hx+corner,-hz+corner,math.pi),(hx-corner,-hz+corner,3*math.pi/2)]:
  for i in range(steps+1):
   a=start+i*math.pi/(2*steps);result.append([cx+corner*math.cos(a),cz+corner*math.sin(a)])
 return result

def finish(name,verts,faces,references=None):
 tris=[]
 for face in faces:
  for j in range(1,len(face)-1):
   t=[face[0],face[j],face[j+1]];a,b,c=[verts[i]for i in t];n=cross(subtract(b,a),subtract(c,a));require(sum(x*x for x in n)>1e-20,'degenerate authored triangle')
   ref=[sum((references[i][k]if references else verts[i][k])for i in t)for k in range(3)]
   if sum(n[k]*ref[k]for k in range(3))<0:t.reverse()
   tris.append(t)
 # Accumulate each authored polygon once per corner, independent of its
 # serialization diagonal. Triangle-area accumulation biases curved quad
 # corners toward whichever diagonal happens to own two incident triangles.
 normals=[[0.,0.,0.]for v in verts]
 if references is not None:
  normals=[normalized(n)for n in references]
 else:
  for face in faces:
   area=[0.,0.,0.]
   for j in range(1,len(face)-1):
    n=cross(subtract(verts[face[j]],verts[face[0]]),subtract(verts[face[j+1]],verts[face[0]]))
    for k in range(3):area[k]+=n[k]
   ref=[sum(verts[i][k]for i in face)for k in range(3)]
   if sum(area[k]*ref[k]for k in range(3))<0:area=[-v for v in area]
   for i in face:
    for k in range(3):normals[i][k]+=area[k]
  normals=[normalized(n)for n in normals]
 return{'name':name,'vertices':verts,'triangles':tris,'normals':normals}

def proposed_driver_cushion():
 """280cushion+448welt triangles, wholly inside old .92x.11x.38m box."""
 profiles=[(-.055,.44,.17),(-.04,.46,.19),(0,.46,.19),(.04,.45,.18),(.05,.42,.15)]
 verts=[[x,y,z]for y,hx,hz in profiles for x,z in perimeter(hx,hz)];N=28;faces=[]
 for level in range(4):
  for i in range(N):j=(i+1)%N;faces.append([level*N+i,level*N+j,(level+1)*N+j,(level+1)*N+i])
 bottom=len(verts);verts.append([0,-.055,0]);top=len(verts);verts.append([0,.055,0])
 for i in range(N):j=(i+1)%N;faces.extend([[bottom,j,i],[top,4*N+i,4*N+j]])
 cushion=finish('driver_cushion_crowned',verts,faces)
 line=perimeter(.453,.183);tube=[];references=[];radial=8;faces=[]
 for i,(x,z)in enumerate(line):
  a=line[(i-1)%N];b=line[(i+1)%N];dx,dz=b[0]-a[0],b[1]-a[1];length=math.hypot(dx,dz);out=[dz/length,0,-dx/length]
  for j in range(radial):
   angle=j*math.tau/radial;normal=[out[0]*math.cos(angle),math.sin(angle),out[2]*math.cos(angle)];tube.append([x+.0025*normal[0],.025+.0025*normal[1],z+.0025*normal[2]]);references.append(normal)
 for i in range(N):
  for j in range(radial):faces.append([i*radial+j,((i+1)%N)*radial+j,((i+1)%N)*radial+(j+1)%radial,i*radial+(j+1)%radial])
 welt=finish('driver_cushion_sewn_welt',tube,faces,references)
 for part in[cushion,welt]:
  for p in part['vertices']:require(all(math.isfinite(v)for v in p)and abs(p[0])<=.46+1e-12 and abs(p[1])<=.055+1e-12 and abs(p[2])<=.19+1e-12,'old cushion envelope exceeded')
 require(len(cushion['triangles'])==280 and len(welt['triangles'])==448,'reviewed topology count changed')
 return[cushion,welt]
