# SPDX-License-Identifier: CC0-1.0
"""Original dimensional fiber/pores/pits, no external imagery or photomeasurement."""
import numpy as np,json,io,hashlib,math
from scipy.special import erf
from PIL import Image
from pathlib import Path

def gaussian_cell(delta,width,cell):
 # Exact cell average of exp(-2*(distance/width)^2), periodic delta supplied.
 k=math.sqrt(2)/width;return math.sqrt(math.pi)/(2*k*cell)*(erf(k*(delta+cell/2))-erf(k*(delta-cell/2)))
def make_tiles(recipe,output):
 output=Path(output);output.mkdir();reports={}
 for fi,family in enumerate(['wood','paint','iron']):
  p=recipe[family];w,h=p['pixels'];sx,sy=p['tile_m'];rng=np.random.default_rng(recipe['seed']+fi);x=np.arange(w)[None,:]*sx/w;y=np.arange(h)[:,None]*sy/h;height=np.zeros((h,w));field=np.zeros((h,w))
  if family!='iron':
   # A periodic longitudinal fiber coordinate, sparse elongated pore cavities.
   # Irregular independent fiber/ring bundles: no equally spaced sinusoidal comb.
   # Gaussian strips have varying width/spacing/amplitude and slow longitudinal wander.
   nodes,weights=np.polynomial.legendre.leggauss(4)
   for bundle in range(p['fiber_count']):
    cy=rng.uniform(0,sy);width=rng.uniform(.0008,.0035);amplitude=rng.uniform(.25,1.0)*rng.choice([-1,1]);freq=int(rng.integers(1,7));phase=rng.uniform(0,2*np.pi);wander=rng.uniform(.0004,.003);integrated=np.zeros((h,w))
    for node,weight in zip(nodes,weights):
     xx=x+node*sx/w/2;center=cy+wander*np.sin(2*np.pi*freq*xx/sx+phase)+.0004*np.sin(2*np.pi*(freq+3)*xx/sx+phase*.7);localwidth=width*(1+.30*np.sin(2*np.pi*xx/sx*2+phase));delta=(y-center+sy/2)%sy-sy/2;envelope=.65+.35*np.sin(2*np.pi*xx/sx*3+phase);integrated+=weight/2*gaussian_cell(delta,localwidth,sy/h)*envelope
    field+=amplitude*integrated
   for layer in range(7):
    cy=rng.uniform(0,sy);width=rng.uniform(.004,.014);phase=rng.uniform(0,2*np.pi);center=cy+.003*np.sin(2*np.pi*x/sx*2+phase);delta=(y-center+sy/2)%sy-sy/2;field+=rng.uniform(-.2,.2)*gaussian_cell(delta,width,sy/h)
   height=p['fiber_height_m']*field
   ff={'resolved':'not uniform harmonic','individual_width_m':[.0008,.0035],'count':p['fiber_count'],'sampling':'GaussianY exactcellaverage,4pointXquadrature; widths/spacing/amplitude/wander vary'};hf={'second_harmonic':'REMOVED; no fixedfrequencycomb'}
   nodes,weights=np.polynomial.legendre.leggauss(8)
   for _ in range(p['pore_count']):
    cx=rng.uniform(0,sx);cy=rng.uniform(0,sy);lx=rng.uniform(.003,.014);ly=rng.uniform(.0006,.0011);qx=np.zeros((1,w))
    for node,weight in zip(nodes,weights):
     delta=(x+node*sx/w/2-cx+sx/2)%sx-sx/2;qx+=weight/2*np.exp(-2*(delta/lx)**4)
    dy=(y-cy+sy/2)%sy-sy/2;qy=gaussian_cell(dy,ly,sy/h);pore=qy*qx;field-=.65*pore;height-=.000020*pore
  else:
   for _ in range(p['pit_count']):
    cx=rng.uniform(0,sx);cy=rng.uniform(0,sy);r=rng.uniform(.001,.003);dx=(x-cx+sx/2)%sx-sx/2;dy=(y-cy+sy/2)%sy-sy/2;pit=gaussian_cell(dx,r*math.sqrt(2),sx/w)*gaussian_cell(dy,r*math.sqrt(2),sy/h);field-=pit;height-=.000035*pit
   field-=field.mean();field/=max(float(abs(field).max()),1)
  field-=field.mean();field/=max(float(abs(field).max()),1);albedo=.5*(1+p['color_contrast']*field);rough=np.clip(p['roughness']+.04*field,0,1)
  # Physical derivatives: normal intensity comes from micron height/metre spacing.
  dzdx=(np.roll(height,-1,1)-np.roll(height,1,1))/(2*sx/w);dzdy=(np.roll(height,-1,0)-np.roll(height,1,0))/(2*sy/h);normal=np.stack([-dzdx,-dzdy,np.ones_like(field)],axis=2);normal/=np.linalg.norm(normal,axis=2,keepdims=True)
  # Explicit neutral 4x4 texels are a declared constant-material chart for cutends/hubs.
  albedo[:4,:4]=.5;normal[:4,:4]=[0,0,1];rough[:4,:4]=p['roughness']
  srgb=np.where(albedo<=.0031308,albedo*12.92,1.055*albedo**(1/2.4)-.055);color=np.repeat(np.round(srgb*255).astype('uint8')[:,:,None],3,axis=2);nn=np.round((normal*.5+.5)*255).astype('uint8');orm=np.stack([np.full_like(field,255),np.round(rough*255),np.full_like(field,255 if family=='iron'else 0)],2).astype('uint8')
  hashes={}
  for kind,array in [('color',color),('normal',nn),('orm',orm)]:
   f=output/(family+'_'+kind+'.png');Image.fromarray(array).save(f,compress_level=9);hashes[kind]=hashlib.sha256(f.read_bytes()).hexdigest()
  reports[family]={'pixels':[w,h],'tile_m':[sx,sy],'px_per_m':[w/sx,h/sy],'decoded_RGBA8_mips_bytes_estimate':w*h*4*4/3*3,'mean_linear_albedo':float(albedo.mean()),'height_range_m':[float(height.min()),float(height.max())],'map_sha256':hashes,'flat_chart_uv':[2/w,2/h],'flat_chart_scope':'neutral4x4 atbaselevel; highermips/forcedLOD maybleedsurroundingpattern, no allmipsflatguarantee','bandlimit':{'fundamental':ff,'second_harmonic':hf}if family!='iron'else{'pits':'exactGaussianpixelcellaverageXY'},'note':'original analytic fibers/pores/pits; unmeasured optical design, no sourcephoto'}
 return reports
