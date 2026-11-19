#!/usr/bin/env python3
"""Reproduce the 1870 Mitchell registration audit (numpy/scipy/pyproj required).

The 28 fit and 8 check roles are fixed in the reviewed control file. Candidate
selection uses fit-control leave-one-out and district blocks only. The separate
check controls evaluate the selected affine; they never influence coefficients.
Run python3 tools/audit_1871_city_map.py [--write | --check] from any directory.
--check compares the stored audit without writing any file; numeric values use
absolute and relative tolerances of 1e-6 for platform differences. Projective
candidate statistics allow 0.001 m absolute tolerance because SciPy finite-
difference optimizer versions differ slightly; that rejected model is not shipped.
"""
import argparse, hashlib, json, math
from pathlib import Path
import numpy as np
from scipy.interpolate import RBFInterpolator, LinearNDInterpolator
from scipy.optimize import least_squares
from fit_1871_city_map import verify_modern_targets
ROOT=Path(__file__).resolve().parents[1]
CONTROL=ROOT/'data/traces/gcp/mitchell_1870_controls.json'
OUT=ROOT/'data/traces/mitchell_1870_fit_audit.json'
parser = argparse.ArgumentParser(description=__doc__)
mode = parser.add_mutually_exclusive_group()
mode.add_argument('--write', action='store_true', help='regenerate the stored audit')
mode.add_argument('--check', action='store_true', help='compare the stored audit without writing files')
args = parser.parse_args()


def compare_audit(expected, actual, path='$'):
    """Return precise JSON paths that differ beyond numeric platform tolerance."""
    if isinstance(expected, dict) and isinstance(actual, dict):
        if expected.keys() != actual.keys():
            return [f'{path}: object keys differ']
        return [message for key in expected
                for message in compare_audit(expected[key], actual[key], f'{path}.{key}')]
    if isinstance(expected, list) and isinstance(actual, list):
        if len(expected) != len(actual):
            return [f'{path}: list lengths differ']
        return [message for index, (left, right) in enumerate(zip(expected, actual))
                for message in compare_audit(left, right, f'{path}[{index}]')]
    numeric = (int, float)
    if (isinstance(expected, numeric) and not isinstance(expected, bool)
            and isinstance(actual, numeric) and not isinstance(actual, bool)):
        # SciPy versions differ by up to 0.0004 m in this rejected candidate.
        absolute_tolerance = 1e-3 if path.startswith('$.candidate_results.projective.') else 1e-6
        if (math.isfinite(expected) and math.isfinite(actual)
                and math.isclose(expected, actual, abs_tol=absolute_tolerance, rel_tol=1e-6)):
            return []
        return [f'{path}: stored {actual!r}, recomputed {expected!r}']
    if type(expected) is not type(actual) or expected != actual:
        return [f'{path}: stored {actual!r}, recomputed {expected!r}']
    return []

obj=json.loads(CONTROL.read_text());c=obj['controls']
p=np.array([x['pixel'] for x in c]);t=np.array([x['local'] for x in c]);p=(p-[1000,1500])/1000
def design(p,kind):
 x,y=p.T
 return np.array([x,y,np.ones(len(x))]).T if kind=='affine' else np.array([x,y,np.ones(len(x)),x*x,x*y,y*y]).T

def model(p,t,kind):
 if kind in ['affine','quadratic']:
  a=np.linalg.lstsq(design(p,kind),t,rcond=None)[0];return lambda q:design(q,kind)@a
 if kind=='projective':
  a=np.linalg.lstsq(design(p,'affine'),t,rcond=None)[0].T.flatten();initial=np.r_[a,0.,0.]
  def f(a,q):return design(q,'affine')@a[:6].reshape(2,3).T/(q@a[6:8]+1)[:,None]
  a=least_squares(lambda a:(f(a,p)-t).flatten(),initial).x;return lambda q:f(a,q)
 if kind.startswith('tps'):
  smooth=float(kind.split('_')[1]);return RBFInterpolator(p,t,kernel='thin_plate_spline',smoothing=smooth,degree=1)
 if kind=='piecewise':
  interp=LinearNDInterpolator(p,t);base=model(p,t,'affine')
  def f(q):
   z=interp(q);nan=np.isnan(z).any(axis=1);z[nan]=base(q[nan]);return z
  return f

def stats(z):
 r=np.linalg.norm(z,axis=1);return {'rmse_m':float(np.sqrt(np.mean(r*r))),'median_m':float(np.median(r)),'p95_m':float(np.percentile(r,95)),'max_m':float(r.max())}

dev=np.array([i for i,x in enumerate(c) if x['role']=='fit']);held=np.array([i for i,x in enumerate(c) if x['role']=='check']);allidx=np.arange(len(c));results={}
for kind in ['affine','projective','quadratic','tps_0.0','tps_0.01','tps_0.1','piecewise']:
 loo=[]
 for i in dev:
  train=dev[dev!=i];loo.append(model(p[train],t[train],kind)(p[i:i+1])[0]-t[i])
 blocked={}
 for group in ['core','north','south','central_west']:
  test=np.array([i for i in dev if c[i]['group']==group]);train=np.array([i for i in dev if c[i]['group']!=group]);blocked[group]=stats(model(p[train],t[train],kind)(p[test])-t[test])
 results[kind]={'training':stats(model(p[dev],t[dev],kind)(p[dev])-t[dev]),'development_loo':stats(loo),'development_spatial_holdout':blocked}
 if not args.check: print(kind,'train',round(results[kind]['training']['rmse_m'],2),'LOO',round(results[kind]['development_loo']['rmse_m'],2),'blocks',{k:round(v['rmse_m'],1) for k,v in blocked.items()})

selected='affine'
shipped=model(p[dev],t[dev],selected)
held_residual=shipped(p[held])-t[held]
old=json.loads((ROOT/'data/traces/mitchell_1870_original_registration.json').read_text())['map_control']['coefficients']
orig=np.array([[old['a'],old['d']],[old['b'],old['e']],[old['c'],old['f']]])
oldheld=np.column_stack((p[held]*1000+[1000,1500],np.ones(len(held))))@orig-t[held]
coef=np.linalg.lstsq(np.column_stack((p[dev]*1000+[1000,1500],np.ones(len(dev)))),t[dev],rcond=None)[0]
all_residual=shipped(p)-t
result={
 'id':'mitchell_1870_registration_audit',
 'controls_file':'data/traces/gcp/mitchell_1870_controls.json',
 'controls_sha256':hashlib.sha256(CONTROL.read_bytes()).hexdigest(),
 'raster_sha256':obj['raster_sha256'],
 'selected_model':selected,
 'portable_target_check':verify_modern_targets(),
 'selection_policy':'Compare fixed candidates on 28 development controls using leave-one-out checks and omission of each whole district. Prefer the lowest RMSE in the worst-performing district over improvements confined to the densely sampled core. Reserve 8 checks until the model is chosen. Do not tune to their errors.',
 'selection_reason':'The affine model has a worst-district RMSE of 28.4 m, compared with 75.8 m for the projective model, 111.5 m for the quadratic model and 37.7–58.1 m for the thin-plate spline candidates. Exact interpolators have zero training error by construction; this does not establish geographical accuracy. Piecewise affine interpolation does not improve cross-validation. The simpler affine model is shipped.',
 'fit_ids':[c[i]['id'] for i in dev], 'reserved_check_ids':[c[i]['id'] for i in held],
 'candidate_results':results,
 'shipped_coefficients':dict(zip('abcdef',coef.T.flatten().tolist())),
 'shipped_training':stats(shipped(p[dev])-t[dev]),
 'reserved_validation':stats(held_residual),
 'original_transform_reserved_validation':stats(oldheld),
 'residuals':[{'id':x['id'],'role':x['role'],'district':x['group'],'error_enu_m':r.tolist(),'error_m':float(np.linalg.norm(r))} for x,r in zip(c,all_residual)],
 'reserved_validation_by_district':{g:stats(np.array([r for i,r in zip(held,held_residual) if c[i]['group']==g])) for g in sorted(set(c[i]['group'] for i in held))},
 'uncertainties':{
  'registration':'The 8 reserved checks have RMSE 15.62 m and maximum error 25.65 m. Leave-one-out RMSE among the 28 fit controls is 21.49 m. Whole-district holdout RMSE ranges from 13.5 to 28.4 m. Use 30 m as a planning allowance within the mapped coverage; it is not a statistical confidence bound.',
  'pixel_reading':'Manual street-centre picks typically have reading uncertainty of 1.5–2 pixels (about 6–8 m). Raster geometry, engraved line width and original surveying remain independent limits.',
  'modern_target_continuity':'Modern intersections may have widened or shifted since 1870. Independent reprojection of the retained latitude/longitude values finds less than 0.007 m of rounding discrepancy. This does not establish that historical and modern street centrelines coincide.',
  'map_feature_generalization':'Bank widths, rail and shore envelopes, and park edges retain a context allowance of roughly 40–80 m. Registration residuals do not establish the accuracy of actual 1871 banks.',
  'outside_mapped_coverage':'Areas west of Western Avenue and south of Thirty-first Street are editorial reconstructions. Their planning allowance is 150–300 m or greater; they have no validation from this map registration.'},
 'not_a_claim':'These errors describe street intersections in a printed city map. They do not establish survey precision for building footprints, banks, the 1871 shoreline or individual properties.'}
if args.check:
    try:
        stored = json.loads(OUT.read_text())
    except (OSError, json.JSONDecodeError) as error:
        parser.exit(1, f'FAIL: cannot read stored audit: {error}\n')
    differences = compare_audit(result, stored)
    if differences:
        detail = '\n'.join(differences[:12])
        parser.exit(1, f'FAIL: stored audit differs in {len(differences)} value(s):\n{detail}\n')
    print('PASS: stored audit matches the recomputed models, checks, provenance and narrative. No files written.')
else:
    if args.write:
        OUT.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({key: result[key] for key in ['shipped_coefficients', 'shipped_training',
                     'reserved_validation', 'original_transform_reserved_validation']}, indent=2))
