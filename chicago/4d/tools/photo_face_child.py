#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Register a child's photograph to the shared UVs while preserving the child mesh.

The hm08 UV/source-vertex correspondence is shared with the calibrated adult exports.
Only the camera is solved. No adult head morph or age macro is transferred to a child.
This supplies texture correspondence, not an independently calibrated child likeness.
"""
import json
import math

import numpy as np
from scipy.optimize import least_squares
import fit_portrait_face as F

BASE={'male':'child_boy_1812','female':'child_girl_1812'}

def body(entry):
    return 'child_toddler_1812' if entry['age']<5 else BASE[entry['sex']]

def pose(entry,portrait):
    header,refs,axes=F.load_kit()
    rows=np.arange(len(refs));X,_,_,_,_=F.face_base(entry['id'],portrait,header,refs,axes,rows)
    table=json.loads(F.MP_TABLE.read_text())['bodies'][portrait['calibration_body']]
    lm={**F.landmarks(),**{k:v['vertex'] for k,v in table['points'].items()}}
    index=F.kit_index();points=[]
    for mark in portrait['marks']:
        members=lm[mark['landmark']];members=[members] if isinstance(members,int) else members
        points.append(X[[index[v] for v in members]].mean(0))
    points=np.array(points);centre=points.mean(0);points-=centre
    observed=np.array([[m['x'],m['y']] for m in portrait['marks']])
    scale=np.linalg.norm(observed[1]-observed[0])/max(.001,np.linalg.norm(points[1]-points[0]))
    def pixels(camera):
        rotated=points@F.rot(*camera[:3]).T
        return np.stack([camera[4]+camera[3]*rotated[:,0],camera[5]-camera[3]*rotated[:,1]],axis=1)
    def residual(camera):return (pixels(camera)-observed).ravel()
    solutions=[]
    for yaw in [0,-.4,.4]:
        r=least_squares(residual,np.r_[yaw,0,0,scale,observed.mean(0)],x_scale='jac',max_nfev=200,
            bounds=([-1,-.6,-.6,10,-10000,-10000],[1,.6,.6,50000,10000,10000]))
        solutions.append(r)
    r=min(solutions,key=lambda s:np.sum(s.fun**2));c=r.x
    return {'values':{},'projection_centre_m':centre.tolist(),
            'rms_px':round(float(np.sqrt(np.mean(np.sum((pixels(c)-observed)**2,axis=1)))),2),
            'camera':{'yaw_deg':round(math.degrees(c[0]),3),'pitch_deg':round(math.degrees(c[1]),3),
                      'roll_deg':round(math.degrees(c[2]),3),'px_per_m':round(float(c[3]),3),'shift_px':c[4:].round(3).tolist()}}
