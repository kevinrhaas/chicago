#!/usr/bin/env python3
"""T-2200: repeatable pinhole comparison of fixed GLB landmarks and dated photographs.
Fits pose only to named controls. Never fits house geometry, check points, principal
point or distortion. Focal/crop perturbations are sensitivity cases, not a confidence
interval. --check re-derives the report; --strict additionally requires the 1% target.
"""
from pathlib import Path
import argparse, hashlib, json, math, struct
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial import cKDTree
ROOT=Path(__file__).resolve().parents[1]
DIRECTORY=ROOT/'data/comparisons/glessner'

def metric(p):
    w,s,z=p
    return np.array([(161.25-w)*.3048,(74-s)*.3048,z*.3048])

def basis(yaw,pitch,roll):
    f=np.array([math.cos(pitch)*math.cos(yaw),math.cos(pitch)*math.sin(yaw),math.sin(pitch)])
    r=np.array([math.sin(yaw),-math.cos(yaw),0.]);u=np.cross(r,f)
    return np.array([r*math.cos(roll)+u*math.sin(roll),u*math.cos(roll)-r*math.sin(roll),f])

def project(points,pose,f,c):
    q=(np.asarray(points)-pose[:3])@basis(*pose[3:]).T
    z=np.maximum(q[:,2],.05)
    return np.column_stack((c[0]+f*q[:,0]/z,c[1]-f*q[:,1]/z)),q[:,2]

def mesh_trees(path):
    b=path.read_bytes();n=struct.unpack_from('<I',b,12)[0];g=json.loads(b[20:20+n]);binary=memoryview(b)[28+n:]
    assert len(g['nodes'])==1 and not any(k in g['nodes'][0] for k in ['matrix','translation','rotation','scale']), 'Revisit frame for transformed asset'
    groups={}
    for p in g['meshes'][0]['primitives']:
        a=g['accessors'][p['attributes']['POSITION']];bv=g['bufferViews'][a['bufferView']]
        assert a['componentType']==5126 and a['type']=='VEC3'
        raw=np.ndarray((a['count'],3),dtype='<f4',buffer=binary,offset=bv.get('byteOffset',0)+a.get('byteOffset',0),strides=(bv.get('byteStride',12),4))
        xyz=raw[:,[0,2,1]].astype(float);xyz[:,1]*=-1
        name=g['materials'][p['material']]['name'];groups.setdefault(name,[]).append(xyz)
    result={}
    for key in ['granite','brick','roof_plane','copper','glass','glass_dark','oak']:
        parts=[a for name,arrays in groups.items() if name==key or (name.startswith(key+'_') and not(key=='glass' and name=='glass_dark')) for a in arrays]
        xyz=np.unique(np.vstack(parts),axis=0);result[key]=(xyz,cKDTree(xyz))
    return result

def validate(d, check_assets=True):
    assert d['target_date']=='1904-07-01' and d['target_fraction']==.01
    ids=set();suitable=0
    for v in d['views']:
        assert v['id'] not in ids;ids.add(v['id'])
        points=v['landmarks'];assert len({p['id'] for p in points})==len(points)
        assert len({tuple(p['observed_px']) for p in points})==len(points),'Repeated source picks cannot inflate coverage'
        assert all(p['role'] in {'fit','check'} and p['tier_1904'] in {'attested','inferred','reconstructed'} for p in points)
        if not v['limited']:
            assert len(points)>=8 and sum(p['role']=='check' for p in points)>=2
            suitable+=1
        assert sum(p['role']=='fit' for p in points)>=4
        assert all(0<=p['observed_px'][i]<=v['image_size'][i] for p in points for i in [0,1])
        assert v['limitations'] and v['rights'] and v['source_date'] and v['image_sha256']
    assert suitable>=8
    if not check_assets:return
    for name,meta in d['assets'].items():
        b=(ROOT/name).read_bytes();assert hashlib.sha256(b).hexdigest()==meta['sha256'],f'Baseline asset drift: {name}; explicitly establish a new baseline'

def associate(v, trees):
    pts=[];dist=[]
    for p in v['landmarks']:
        xyz,tree=trees[p['material']];nominal=metric(p['building_ft']);w0,s0,_=p['building_ft'];recess=p.get('recess_ft',0)*.3048
        if w0==0:nominal[0]-=recess
        elif s0==0:nominal[1]-=recess
        elif w0==26.5:nominal[0]+=recess
        elif w0==125.75:nominal[0]-=recess
        distance,i=tree.query(nominal);pts.append(xyz[i]);dist.append(float(distance))
    return np.array(pts),dist

def derive(d):
    validate(d);trees=mesh_trees(ROOT/'assets/gltf/glessner_house__as_built_1887.glb');reports=[]
    for v in d['views']:
        pts,dist=associate(v,trees)
        pts=np.array(pts);obs=np.array([p['observed_px'] for p in v['landmarks']]);mask=np.array([p['role']=='fit' for p in v['landmarks']]);cam,target=np.array(v['seed_camera_m']);delta=target-cam
        seed=np.r_[cam,math.atan2(delta[1],delta[0]),math.atan2(delta[2],np.hypot(*delta[:2])),0.]
        x,y,w,h=v['photo_rectangle'];center=np.array([x+w/2,y+h/2]);f=w*v['nominal_lens_mm']/v['sensor_width_mm']
        lower=seed-np.array([150,150,50,1.0,.8,.18]);upper=seed+np.array([150,150,50,1.0,.8,.18]);lower[2],upper[2]=v['camera_height_assumption_m']
        if v['id'] in ['prairie-front','taylor-ne','habs-ne']:lower[0]=49.3
        if v['id'] in ['taylor-ne','habs-ne','north-level','north-inclined','stable-detail','northwest-stable']:lower[1]=22.7
        if v['id']=='northwest-stable':upper[0]=-.3
        if v['id'].startswith('courtyard'):
            lower[:2]=[11,-5];upper[:2]=[41,14]
        def solve(focal,principal):
            def fun(pose):
                uv,depth=project(pts[mask],pose,focal,principal)
                return np.r_[(uv-obs[mask]).ravel(),np.minimum(depth-.5,0)*100]
            opt=least_squares(fun,np.clip(seed,lower+1e-6,upper-1e-6),bounds=(lower,upper),max_nfev=3000,xtol=1e-11,ftol=1e-11,gtol=1e-9)
            uv,depth=project(pts,opt.x,focal,principal)
            return opt,uv,depth
        opt,uv,depth=solve(f,center);error=np.linalg.norm(uv-obs,axis=1);span=float(np.ptp(obs[:,0]));bounds=[]
        for factor,offset in [(.8,[0,0]),(1.2,[0,0]),(1,[-w*.05,0]),(1,[w*.05,0]),(1,[0,-h*.05]),(1,[0,h*.05])]:
            alt,pred,_=solve(f*factor,center+offset);bounds.append(pred)
        sensitivity=np.max(np.linalg.norm(np.array(bounds)-uv,axis=2),axis=0)
        ids=[p['id'] for p in v['landmarks']]
        # Full building face width can be outside a cropped image. Retain the stricter
        # observed-span metric and identify the extrapolation; do not make it invisible.
        if v['id'].startswith('courtyard'):
            segment=[[125.75,59.75,0],[125.75,26.83,0]] if v['id']=='courtyard-west' else [[80.3,26.83,0],[26.5,74,0]]
        elif v['id'] in ['prairie-front','taylor-ne','habs-ne']:segment=[[0,74,0],[0,0,0]]
        else:segment=[[0,0,0],[161.25,0,0]]
        end,_=project([metric(p) for p in segment],opt.x,f,center);projected_width=abs(float(end[1,0]-end[0,0]))
        rows=[]
        for i,p in enumerate(v['landmarks']):
            rows.append({'id':p['id'],'role':p['role'],'nominal_m':metric(p['building_ft']).round(6).tolist(),'mesh_vertex_m':pts[i].round(6).tolist(),'association_distance_m':round(dist[i],6),'observed_px':p['observed_px'],'predicted_px':uv[i].round(4).tolist(),'residual_px':round(float(error[i]),4),'fraction_projected_width':round(float(error[i]/projected_width),7),'fraction_observed_span':round(float(error[i]/span),7),'sensitivity_px':round(float(sensitivity[i]),4),'target_met':bool(depth[i]>0 and error[i]<=.01*projected_width and error[i]<=.01*span and dist[i]<=.3),'association_warning':bool(dist[i]>.3)})
        check=~mask
        reports.append({'id':v['id'],'camera':{'position_m':opt.x[:3].round(8).tolist(),'basis_right_up_forward':basis(*opt.x[3:]).round(10).tolist(),'focal_px':round(f,8),'principal_px':center.tolist(),'image_size':v['image_size'],'near':.05,'far':2000},'fit_controls':int(mask.sum()),'check_points':int(check.sum()),'fit_rms_px':round(float(np.sqrt(np.mean(error[mask]**2))),4),'check_rms_px':round(float(np.sqrt(np.mean(error[check]**2))),4),'max_residual_px':round(float(error.max()),4),'observed_span_px':span,'projected_width_px':round(projected_width,4),'normalization_segment_building_ft':segment,'positive_depth':bool(np.all(depth>0)),'converged':bool(opt.success),'focal_sensitivity_factors':[.8,1.2],'principal_sensitivity_fraction':.05,'pose_is_surveyed':False,'pose_bounds_active':[name for i,name in enumerate(['x','y','height','yaw','pitch','roll']) if min(abs(opt.x[i]-lower[i]),abs(opt.x[i]-upper[i]))<1e-4],'status':'limited reference — no acceptance verdict' if v['limited'] else 'exceptions remain' if any(not r['target_met'] or r['association_warning'] for r in rows) else 'within both width targets; calibration uncertainty still applies','landmarks':rows})
    return {'ticket':'T-2200','method':'Fixed master mesh, fixed named observations. Least-squares pinhole pose uses fit controls only; all withheld checks and association distances remain in the report. ±20% focal and ±5% principal-point trials quantify sensitivity, not a statistical confidence interval.','geometry_changed':False,'views':reports}

def evaluate_candidate(d, baseline, path):
    """Measure changed geometry through FROZEN cameras; no optimizer is called."""
    validate(d,check_assets=False);trees=mesh_trees(path);views=[]
    for v,old in zip(d['views'],baseline['views']):
        assert v['id']==old['id'],'Baseline/observation view mismatch'
        points,distances=associate(v,trees);c=old['camera']
        q=(points-np.array(c['position_m']))@np.array(c['basis_right_up_forward']).T
        uv=np.column_stack((c['principal_px'][0]+c['focal_px']*q[:,0]/np.maximum(q[:,2],.05),c['principal_px'][1]-c['focal_px']*q[:,1]/np.maximum(q[:,2],.05)))
        rows=[]
        for i,p in enumerate(v['landmarks']):
            assert old['landmarks'][i]['id']==p['id']
            error=float(np.linalg.norm(uv[i]-p['observed_px']))
            rows.append({'id':p['id'],'role':p['role'],'observed_px':p['observed_px'],'predicted_px':uv[i].round(4).tolist(),'mesh_vertex_m':points[i].round(6).tolist(),'association_distance_m':round(distances[i],6),'residual_px':round(error,4),'baseline_residual_px':old['landmarks'][i]['residual_px'],'fraction_baseline_projected_width':round(error/old['projected_width_px'],7),'fraction_observed_span':round(error/old['observed_span_px'],7),'target_met':bool(q[i,2]>0 and error<=.01*old['projected_width_px'] and error<=.01*old['observed_span_px'] and distances[i]<=.3)})
        views.append({'id':v['id'],'camera':c,'limited':v['limited'],'landmarks':rows})
    return {'ticket':'T-2200','candidate_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'camera_refitted':False,'method':'Frozen baseline cameras and width denominators. Re-associated candidate vertices remain reviewable; no camera or geometry optimization. Limited views still have no acceptance verdict.','views':views}

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--check',action='store_true');ap.add_argument('--strict',action='store_true');ap.add_argument('--candidate',type=Path,help='Measure a master GLB through frozen cameras without refitting');ap.add_argument('--output',type=Path,help='Candidate report destination (required with --candidate)');args=ap.parse_args()
    d=json.loads((DIRECTORY/'observations.json').read_text())
    if args.candidate:
        assert args.output and not args.check and not args.strict,'Use --candidate MASTER.glb --output /tmp/candidate.json'
        assert not args.output.resolve().is_relative_to(DIRECTORY.resolve()),'Candidate must not overwrite the frozen baseline'
        result=evaluate_candidate(d,json.loads((DIRECTORY/'report.json').read_text()),args.candidate)
        args.output.write_text(json.dumps(result,indent=2)+'\n');print(f'Candidate measured with frozen cameras: {args.output}');return
    assert not args.output,'--output is for candidate evaluation only'
    result=derive(d);p=DIRECTORY/'report.json';s=json.dumps(result,indent=2)+'\n'
    if args.check:
        assert p.read_text()==s,'Camera report stale; run python3 tools/glessner_camera_baseline.py'
    else:p.write_text(s)
    for v in result['views']:print(f"{v['id']}: {v['fit_controls']} controls / {v['check_points']} checks; fit RMS {v['fit_rms_px']}px, check RMS {v['check_rms_px']}px; {v['status']}")
    if args.strict:assert all(v['status'].startswith('within') for v in result['views']),'Photographic acceptance not met; baseline exceptions are explicit'
    print('PASS: reproducible baseline; this is not photographic acceptance of the house')
if __name__=='__main__':main()
