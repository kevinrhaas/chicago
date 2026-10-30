# SPDX-License-Identifier: GPL-3.0-or-later
"""Original bounded bearing washer helper; SOURCE ONLY, no calls/model export."""
import math

def washer_y(outer_radius,bore_radius,thickness,segments=12):
 if type(segments)is not int or segments<8 or not all(math.isfinite(x)and x>0 for x in [outer_radius,bore_radius,thickness])or bore_radius>=outer_radius:raise ValueError('Invalid annularwasher')
 vertices=[]
 for y,r in [(-thickness/2,outer_radius),(thickness/2,outer_radius),(-thickness/2,bore_radius),(thickness/2,bore_radius)]:
  for k in range(segments):
   theta=2*math.pi*k/segments;vertices.append([r*math.cos(theta),y,r*math.sin(theta)])
 faces=[];n=segments
 for i in range(n):
  j=(i+1)%n
  faces.extend([[i,j,n+j,n+i],[2*n+j,2*n+i,3*n+i,3*n+j],[j,i,2*n+i,2*n+j],[n+i,n+j,3*n+j,3*n+i]])
 # Explicit outward orientation (all quads planar, annulus has no center fan).
 for f in faces:
  p,q,r=[vertices[k]for k in f[:3]];u=[q[k]-p[k]for k in range(3)];v=[r[k]-p[k]for k in range(3)];normal=[u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]];c=[math.fsum(vertices[i][k]for i in f)/4 for k in range(3)]
  radial=math.hypot(c[0],c[2]);desired=[0,1 if c[1]>0 else-1,0]if abs(normal[1])>abs(normal[0])+abs(normal[2])else[c[0]/radial,0,c[2]/radial]
  if radial<(outer_radius+bore_radius)/2 and abs(normal[1])<abs(normal[0])+abs(normal[2]):desired=[-x for x in desired]
  if math.fsum(a*b for a,b in zip(normal,desired))<0:f.reverse()
 return vertices,faces
