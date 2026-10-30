# SPDX-License-Identifier: CC0-1.0
"""Original portable eye geometry study: stdlib only, no MakeHuman code copied.

Input positions are the actual prepared body eye helper coordinates in metre/Y-up/
+Z-forward frame. Radius/color/cornea parameters are reconstructed authoring choices.
Output fits the canonical builder object_mesh API; no Blender dependency here.
"""
import math

LOD_SAMPLING = {0:(24,12,4),1:(16,8,3),2:(12,5,0),3:(8,3,0)}
TRIANGLE_CEILINGS = {0:2000,1:1000,2:400,3:200}
MATERIALS = {
 'eyes__sclera':{'base_color':[.82,.79,.72,1],'roughness':.38},
 'eyes__iris':{'base_color':[1,1,1,1],'roughness':.42,'original_iris_image':True},
 'eyes__pupil':{'base_color':[.002,.0015,.001,1],'roughness':.25},
 'eyes__cornea':{'base_color':[1,1,1,.05],'roughness':.045,'alpha_mode':'BLEND'},
}

def _add(a,b):return [x+y for x,y in zip(a,b)]
def _mul(a,w):return [x*w for x in a]
def _cross(a,b):return [a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]]
def _norm(a):
 length=math.sqrt(sum(x*x for x in a))
 if length<1e-10:raise ValueError('eye helper head/tail axis is degenerate')
 return _mul(a,1/length)

def build_eye_components(bones,lod,config=None):
 config=config or {};N,L,C=LOD_SAMPLING[lod];C=0;R=config.get('radius_m',.012);IR=config.get('iris_radius_m',.0055);PR=config.get('pupil_radius_m',.0022);bulge=config.get('corneal_bulge_m',.0021)
 if not(0<PR<IR<R and 0<=bulge<R):raise ValueError('invalid reconstructed eye dimensions')
 names=list(MATERIALS) if C else [n for n in MATERIALS if n!='eyes__cornea']
 meshes={n:{'name':n,'material':n,'positions_m':[],'triangles':[],'uvs':[],'weights':[]} for n in names};eyes=[]
 for side,cell in [('l',0),('r',1)]:
  center=bones['eye_'+side]['head_m'];fwd=_norm([b-a for a,b in zip(center,bones['eye_'+side]['tail_m'])]);right=_norm(_cross([0,1,0],fwd));up=_norm(_cross(fwd,right));eyes.append({'side':side,'center_m':center,'forward':fwd,'radius_m':R,'iris_radius_m':IR,'pupil_radius_m':PR})
  def vertex(material,x,y,z,uv):
   m=meshes[material];i=len(m['positions_m']);m['positions_m'].append(_add(center,_add(_mul(right,x),_add(_mul(up,y),_mul(fwd,z)))));m['uvs'].append(uv);m['weights'].append({'eye_'+side:1.});return i
  def ring(material,r,z,v,radial=False):
   result=[]
   for k in range(N+1):
    angle=2*math.pi*k/N;x=r*math.cos(angle);y=r*math.sin(angle)
    uv=[(cell+.5+.45*x/IR)/2,.5+.45*y/IR] if radial else [(cell+.05+.9*k/N)/2,.05+.9*v]
    result.append(vertex(material,x,y,z,uv))
   return result
  def bridge(material,a,b):
   for k in range(N):meshes[material]['triangles'].extend([[a[k],a[k+1],b[k+1]],[a[k],b[k+1],b[k]]])
  angle0=math.asin(IR/R);previous=None
  for j in range(L):
   angle=angle0+(math.pi-angle0)*j/L
   current=ring('eyes__sclera',R*math.sin(angle),R*math.cos(angle),j/L)
   if previous is not None:bridge('eyes__sclera',previous,current)
   previous=current
  pole=vertex('eyes__sclera',0,0,-R,[(cell+.5)/2,.95])
  for k in range(N):meshes['eyes__sclera']['triangles'].append([previous[k],previous[k+1],pole])
  plane=math.sqrt(R*R-IR*IR)
  inner=ring('eyes__iris',PR,plane-.00008,0,True);outer=ring('eyes__iris',IR,plane-.00008,1,True);bridge('eyes__iris',inner,outer)
  border=ring('eyes__pupil',PR,plane-.00004,1,True);center_index=vertex('eyes__pupil',0,0,plane-.00004,[(cell+.5)/2,.5])
  for k in range(N):meshes['eyes__pupil']['triangles'].append([center_index,border[k],border[k+1]])
  if C:
   middle=vertex('eyes__cornea',0,0,plane+bulge,[(cell+.5)/2,.05]);previous=None
   for j in range(1,C+1):
    r=IR*j/C;current=ring('eyes__cornea',r,plane+bulge*(1-(r/IR)**2),j/C)
    if previous is None:
     for k in range(N):meshes['eyes__cornea']['triangles'].append([middle,current[k],current[k+1]])
    else:bridge('eyes__cornea',previous,current)
    previous=current
 # Fix analytic outward winding, then verify all triangles have actual area.
 for material,m in meshes.items():
  for i,(a,b,c) in enumerate(m['triangles']):
   p,q,r=[m['positions_m'][v] for v in (a,b,c)];normal=_cross([q[j]-p[j] for j in range(3)],[r[j]-p[j] for j in range(3)])
   if math.sqrt(sum(x*x for x in normal))<1e-15:raise ValueError('degenerate eye triangle')
   eye=eyes[0 if p[0]+q[0]+r[0]>0 else 1];expected=eye['forward'] if material!='eyes__sclera' else [(p[j]+q[j]+r[j])/3-eye['center_m'][j] for j in range(3)]
   if sum(normal[j]*expected[j] for j in range(3))<0:m['triangles'][i]=[a,c,b]
  if not all(math.isfinite(v) for p in m['positions_m'] for v in p):raise ValueError('nonfinite eye coordinate')
  if not all(0<=v<=1 for uv in m['uvs'] for v in uv):raise ValueError('eye UV outside 0–1')
 triangles=sum(len(m['triangles']) for m in meshes.values())
 if triangles>TRIANGLE_CEILINGS[lod]:raise ValueError('original eye component triangle budget exceeded')
 return {'license':'CC0-1.0','lod':lod,'eyes':eyes,'meshes':list(meshes.values()),'triangles':triangles,'triangle_ceiling':TRIANGLE_CEILINGS[lod],'status':'original reconstructed eye components; clinical anatomy/fit/PBR not accepted'}

def iris_pixels(width=512,height=256):
 """Original fibers/limbal shading without photographic input or baked highlights."""
 if width!=2*height:raise ValueError('eye atlas uses two square regions')
 pixels=[]
 for yy in range(height):
  for xx in range(width):
   x=((xx%height)/(height-1)-.5)/.45;y=(yy/(height-1)-.5)/.45;r=math.hypot(x,y);a=math.atan2(y,x)
   fibers=.50+.20*math.sin(61*a+18*r)+.12*math.sin(103*a-11*r)+.08*math.sin(157*a+41*r)
   limbus=max(.13,1-.8*math.exp(-((r-.98)/.055)**2));radial=.65+.35*math.sin(min(1,r)*math.pi)
   pixels.extend([c*(.65+.65*fibers)*limbus*radial for c in [.24,.14,.065]]+[1.])
 return pixels
