#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Register a new photo against an existing, cited portrait fit without changing its shape.

The six camera parameters may move. Curated face axes, including the head-shape choice,
remain the original values. This is a camera registration, not another portrait reading.
"""
import json
import math
import pathlib

import numpy as np
from scipy.optimize import least_squares

import fit_portrait_face as F


def record(entry):
    path=(F.ROOT/entry['shape_from']).resolve()
    if path.parent != F.FITS.resolve() or path.name != entry['id']+'.json':
        raise ValueError('shape_from must be this person’s existing portrait-fit record')
    data=json.loads(path.read_text())
    if data.get('person_id') != entry['id'] or entry.get('reference_source') not in data.get('sources',[]):
        raise ValueError('the historical person and original portrait source must match the fitted head')
    return path,data


def fit(entry,portrait):
    path,data=record(entry)
    header,refs,axes=F.load_kit();rows=np.arange(len(refs))
    body=header['assets'].get(portrait['base_body'],{})
    # Explicit neutral values prevent seeded extra face axes from changing a reviewed head.
    values={a['id']:float(body.get('face_bias',{}).get(a['id'],0)) for a in header['axes']
            if not a.get('drive') and (a.get('scope')=='face' or a['id'] in ('head_shape','forehead_height'))}
    values.update(data['values']);option=int(values.get('head_shape.option',0))
    registered={**portrait,'axes':list(dict.fromkeys([*portrait['axes'],*(k for k in values if k in axes)]))}
    base,_,_,held,_=F.face_base(entry['id'],registered,header,refs,axes,rows)
    for name,value in values.items():
        if name in axes and name not in held:base+=F.delta_at(axes[name],value,option,rows)
    table=json.loads(F.MP_TABLE.read_text())['bodies'][portrait['base_body']]
    lm={**F.landmarks(),**{k:v['vertex'] for k,v in table['points'].items()}}
    index=F.kit_index();positions=[]
    for m in portrait['marks']:
        member=lm[m['landmark']];member=[member] if isinstance(member,int) else member
        positions.append(base[[index[v] for v in member]].mean(0))
    X=np.array(positions);centre=X.mean(0);X-=centre
    observed=np.array([[m['x'],m['y']] for m in portrait['marks']])
    sigma=np.array([m['sigma_px'] for m in portrait['marks']])
    scale=np.linalg.norm(observed[1]-observed[0])/max(.001,np.linalg.norm(X[1]-X[0]))
    def pixels(camera):
        rotated=X@F.rot(*camera[:3]).T
        return np.stack([camera[4]+camera[3]*rotated[:,0],camera[5]-camera[3]*rotated[:,1]],axis=1)
    def residual(camera):return ((pixels(camera)-observed)/sigma[:,None]).ravel()
    candidates=[]
    for yaw in {0.0,-.6,.6,math.radians(data['fit']['camera']['yaw_deg'])}:
        initial=np.r_[yaw,0.0,0.0,scale,observed.mean(0)]
        solution=least_squares(residual,initial,x_scale='jac',max_nfev=250,
            bounds=([-1.3,-.6,-.6,10,-10000,-10000],[1.3,.6,.6,50000,10000,10000]))
        candidates.append(solution)
    solution=min(candidates,key=lambda r:np.sum(r.fun**2));camera=solution.x
    return {'values':values,'projection_centre_m':centre.tolist(),
            'rms_px':round(float(np.sqrt(np.mean(np.sum((pixels(camera)-observed)**2,axis=1)))),2),
            'camera':{'yaw_deg':round(math.degrees(camera[0]),3),'pitch_deg':round(math.degrees(camera[1]),3),
                      'roll_deg':round(math.degrees(camera[2]),3),'px_per_m':round(float(camera[3]),3),
                      'shift_px':camera[4:].round(3).tolist()}}
