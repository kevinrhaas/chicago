"""T-2470: project each actual finial tip through two fixed photographic cameras.

A dated comparison, not a per-commit gate or a replacement for T-2200's baseline.
Run with --before SAVED_MASTER.glb --after CURRENT_MASTER.glb --out REPORT.json.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import numpy as np
from glessner_camera_baseline import metric, mesh_trees
ROOT=Path(__file__).resolve().parents[1]
ap=argparse.ArgumentParser(description=__doc__)
ap.add_argument('--before',type=Path,required=True)
ap.add_argument('--after',type=Path,required=True)
ap.add_argument('--out',type=Path,required=True)
a=ap.parse_args()
form=json.loads((ROOT/'data/structures/glessner_house.json').read_text())['phases'][0]['form']
t,plan=form['tower_north']['value'],form['tower_north_plan']['value']
assert t['apex'][1]=='ng'
coordinates=[[35.,8.6,45.9],[plan['centre_W'],plan['centre_S'],t['apex'][0]+t['finial_ft']]]
assets=[];points=[]
for path,ft in zip((a.before,a.after),coordinates):
    xyz,tree=mesh_trees(path)['copper']
    distance,index=tree.query(metric(ft));point=xyz[int(index)]
    assert distance<.002, f'{path}: no finial-tip vertex at the semantic tower centre/top'
    points.append(point)
    assets.append({'file':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                   'semantic_tip_WS_ng_ft':ft,'actual_tip_xyz_m':point.tolist(),
                   'vertex_distance_m':float(distance)})
camera_file=ROOT/'data/reference_views/glessner_house/habs-01-northwest.json'
c=json.loads(camera_file.read_text());angle=math.radians(c['yaw_deg'])
basis=np.array([[math.cos(angle),-math.sin(angle),0],[0,0,1],[math.sin(angle),math.cos(angle),0]])
nw={'position_m':c['eye'],'basis_right_up_forward':basis.tolist(),
    'focal_px':c['focal_px'],'principal_px':c['principal_px']}
frozen_file=ROOT/'data/comparisons/glessner/report.json'
inclined=next(v['camera'] for v in json.loads(frozen_file.read_text())['views'] if v['id']=='north-inclined')
new_file=ROOT/'data/reference_views/glessner_house/habs-14-north-inclined.json'
c14=json.loads(new_file.read_text())
new_inclined={k:c14[k] for k in ('basis_right_up_forward','focal_px','principal_px')}
new_inclined['position_m']=c14['eye']
views=[]
for name,cam,observed in [('habs-01-northwest',nw,[428,460]),('habs-14-reconciled',new_inclined,[1304,355]),('habs-14-frozen-T2200',inclined,[1304,355])]:
    q=(np.array(points)-cam['position_m'])@np.array(cam['basis_right_up_forward']).T
    assert np.all(q[:,2]>0)
    uv=np.c_[cam['principal_px'][0]+cam['focal_px']*q[:,0]/q[:,2],
             cam['principal_px'][1]-cam['focal_px']*q[:,1]/q[:,2]]
    errors=np.linalg.norm(uv-observed,axis=1)
    if name!='habs-14-frozen-T2200':assert errors[1]<errors[0],(name,errors)
    views.append({'view':name,'observed_px':observed,'camera':cam,
                  'predicted_before_after_px':uv.tolist(),'residual_before_after_px':errors.tolist()})
report={'ticket':'T-2470','not_a_reading':'A bounded re-reading of catalogued photographs and generated geometry; no new archival reading.',
        'method':'Actual copper vertex within2mm of each model-specific finial tip. Reconciled cameras and source picks held fixed across before/after; original T2200 camera also reported without requiring an improvement. No old-coordinate nearest-vertex reassociation.',
        'camera_sha256':hashlib.sha256(camera_file.read_bytes()).hexdigest(),
        'inclined_camera_sha256':hashlib.sha256(new_file.read_bytes()).hexdigest(),
        'frozen_camera_report_sha256':hashlib.sha256(frozen_file.read_bytes()).hexdigest(),
        'assets':assets,'views':views,'whole_house_matches':False,
        'limitations':'HABS01 control RMS2.60px; reconciled HABS14 coordinate RMS5.68px, but model-derived controls and free principal point limit independence. The frozen T2200 camera worsens after the corrected facade/plan; it is retained as a limitation, not hidden. This report is not whole-house photographic acceptance. Other house differences remain with T-2228.'}
a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(report,indent=2)+'\n')
for v in views:print(v['view'],v['residual_before_after_px'])
