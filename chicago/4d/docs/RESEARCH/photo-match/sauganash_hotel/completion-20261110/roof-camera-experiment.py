import numpy as np,math,json
from scipy.optimize import least_squares
from pathlib import Path
c=json.load(open(Path(__file__).resolve().parents[5]/'data/reference_views/sauganash_hotel/andreas-1884.json'))
# Approximate manual broad wall-corner points, 15-25px uncertainty. No roof controls.
world=np.array([[9.92,8,0],[0,8,0],[9.92,8,5.5],[0,8,5.5],[9.92,0,5.5]])
obs=np.array([[900,1040],[1685,980],[900,525],[1690,555],[410,570]])
def project(v,p):
 e,n,z,yaw,cx,cy,f=p;t=np.deg2rad(yaw);diff=v-np.array([e,n,z]);dep=diff[:,0]*np.sin(t)+diff[:,1]*np.cos(t);hor=diff[:,0]*np.cos(t)-diff[:,1]*np.sin(t);return np.column_stack((cx+f*hor/dep,cy-f*diff[:,2]/dep))
p=[*c['eye'],c['yaw_deg'],*c['principal_px'],c['focal_px']]
# fixed inherited focal; no physical inference from this camera experiment
fit=least_squares(lambda q:(project(world,[*q,c['focal_px']])-obs).flatten(),p[:-1],max_nfev=20000)
q=[*fit.x,c['focal_px']];apex=[[9.92,4,5.5+4.25*math.tan(math.radians(25.2))],[5.92,-8,5.5+4.25*math.tan(math.radians(25.2))]]
out={'status':'analytical_diagnostic_only_not_render_or_match','controls':{'world_uvz':world.tolist(),'image_px':obs.tolist(),'uncertainty_px':'approx15-25; handpicked obscured wall feet'},'existing':{'camera':p,'control_projection':project(world,p).tolist(),'roof_projection':project(np.array(apex),p).tolist()},'wall_fit':{'camera':q,'control_projection':project(world,q).tolist(),'roof_projection':project(np.array(apex),q).tolist(),'rms_px':float(np.sqrt(np.mean((project(world,q)-obs)**2)))},'limits':'Roof points withheld. Fixed current geometry and inherited focal. Wall fit is another weak camera hypothesis, not historical or published. Roof-exposure residual cannot alone establish different wing dimensions.'}
Path(__file__).with_name('roof-camera-experiment.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
