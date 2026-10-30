# SPDX-License-Identifier: GPL-3.0-or-later
"""Original recessed opaque quarter hypothesis; no IO/model evaluation at import.
No glass, curtain, historical upholstery or actual specimen identification.
"""
import math

def need(q,m):
 if not q:raise ValueError(m)
def quarter_surface(profile,side,half,thickness,recipe,triangulate):
 need(recipe.get('schema')==1 and recipe.get('enabled') is True and recipe.get('production_accepted') is False,'Explicit unaccepted study')
 scale=recipe['inner_profile_scale'];recess=recipe['recess_m']
 need(type(scale)in(int,float) and math.isfinite(scale) and .9<=scale<1,'Bounded original reveal width')
 need(type(recess)in(int,float) and math.isfinite(recess) and 0<recess<thickness,'Inset inside original quarter thickness')
 need(side in(-1,1) and len(profile)>=3 and all(len(p)==2 and all(math.isfinite(x)for x in p)for p in profile),'Finite original source profile')
 material=recipe['material'];need(set(material)=={'name','pbrMetallicRoughness'},'Opaque scalar study material only')
 pbr=material['pbrMetallicRoughness'];need(set(pbr)=={'baseColorFactor','metallicFactor','roughnessFactor'} and len(pbr['baseColorFactor'])==4 and pbr['baseColorFactor'][3]==1,'No fabricated optical transmission')
 need(all(type(x)in(int,float)and math.isfinite(x)and 0<=x<=1 for x in pbr['baseColorFactor']+[pbr['metallicFactor'],pbr['roughnessFactor']]),'Finite optical coefficients')
 n=len(profile);cz=math.fsum(p[0]for p in profile)/n;cy=math.fsum(p[1]for p in profile)/n
 area=math.fsum(a[0]*b[1]-b[0]*a[1]for a,b in zip(profile,profile[1:]+profile[:1]));need(area!=0,'Nonzero source profile area')
 inner=[(cz+scale*(z-cz),cy+scale*(y-cy))for z,y in profile]
 # Original exterior profile and back plane retained. Only inside original solid.
 outer_x=side*(half+thickness);inset_x=side*(half+thickness-recess);back_x=side*half
 v=[[outer_x,y,z]for z,y in profile]+[[inset_x,y,z]for z,y in inner]+[[back_x,y,z]for z,y in profile]
 faces=[]
 for i in range(n):
  j=(i+1)%n;faces.extend([[i,j,n+j,n+i],[i,2*n+i,2*n+j,j]])
 # Back is original closed outline. It remains opaque: no fake see-through cabin.
 faces.extend([[2*n+i for i in reversed(f)]for f in triangulate(profile)])
 # Profile CCW(z,y) normal is -X; reverse front/rim for positive-X exterior.
 if side*(1 if area>0 else -1)>0:faces=[list(reversed(f))for f in faces]
 iv=[[inset_x,y,z]for z,y in inner]
 iff=[list(reversed(f))for f in triangulate(inner)] if side>0 else triangulate(inner)
 return v,faces,iv,iff
