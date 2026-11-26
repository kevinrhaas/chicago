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


def portrait(entry, points, size):
    import photo_face_library as P
    p = P.portrait({k:v for k,v in entry.items() if k != 'shape_from'}, points, size)
    h = entry['historical']
    p.update(base_body=h['reference_asset'], calibration_body=P.BASE[entry['sex']],
             age_at_picture_years=h['scene_age'], existing_values=h['before_values'])
    return p


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
    # Keep the complete reviewed runtime shape, including its seeded non-face axes.
    values=dict(entry['historical']['before_values'])
    option=int(values.get('head_shape.option',0))
    registered={**portrait,'axes':list(dict.fromkeys([*portrait['axes'],*(k for k in values if k in axes)]))}
    base,_,_,held,_=F.face_base(entry['id'],registered,header,refs,axes,rows)
    for name,value in values.items():
        if name in axes and name not in held and not axes[name].get('drive'):base+=F.delta_at(axes[name],value,option,rows)
    table=json.loads(F.MP_TABLE.read_text())['bodies'][portrait.get('calibration_body',portrait['base_body'])]
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


def texture_photo(im, entry, points):
    """Reduce baked archive lighting; retain source details, never invent pixels."""
    if not entry['historical'].get('monochrome'):return im
    from PIL import Image
    from scipy.ndimage import gaussian_filter
    import photo_face_library as P
    rgb=P.L.linear(np.asarray(im,dtype=float))
    luminance=np.maximum(.004,rgb.mean(axis=2))
    scale=max(3,np.linalg.norm(np.array(points[468])-points[473])*.28)
    log=np.log(luminance);broad=gaussian_filter(log,scale)
    # Low-frequency side lighting belongs to the photograph's studio, not the
    # moving 3D face's own sun. Keep a quarter of that contrast and the fine detail.
    gain=np.exp(.75*(np.median(broad)-broad))
    return Image.fromarray(P.L.srgb8(rgb*np.clip(gain,.35,3)[...,None]))


def appearance(face, entry, portrait):
    """Exact person references; existing fits and new photo fits are explicit."""
    import photo_face_library as P
    h=entry['historical'];existing=bool(entry.get('shape_from'))
    if existing:face['source_url']=json.loads((P.ROOT/'data/sources'/f"{entry['reference_source']}.json").read_text())['url']
    face.update(historical=h, texture_only=existing, population='person',
                grade='reconstructed' if h.get('stand_in') else 'inferred')
    if existing:face.update(shape_from=entry['shape_from'],reference_source=entry['reference_source'])
    if h.get('monochrome'):
        native=P.native_iris_tone(entry['sex'],portrait['base_body'])
        weight=np.array([.2126,.7152,.0722])
        gain=float(np.clip(np.dot(face['eyes']['iris_linear'],weight)/max(.002,np.dot(native,weight)),.4,3))
        face['eyes']['iris_gain']=[gain]*3
        face['eyes']['iris_linear']=(native*gain).tolist()
        face['hair_rgb']=h['before_hair_rgb']
        face['hair_projection']['fallback_gain']=[1,1,1]
    if existing:
        # Existing heads retain the eyes and resting lid pose already reviewed.
        face['eyes']['centres_uv']=None
        face['eyes']['lid_rest']=.3*min(1,max(0,(h['scene_age']-40)/35))
    else:
        face['eyes']['lid_rest']=max(0,min(.14,face['eyes']['lid_rest']))
        if h.get('iris_rgb_linear'):
            native=P.native_iris_tone(entry['sex'],portrait['base_body'])
            iris=np.array(h['iris_rgb_linear']);face['eyes']['iris_linear']=iris.tolist()
            face['eyes']['iris_gain']=np.clip(iris/np.maximum(native,.002),.1,64).tolist()
    face['limits'].extend(h['limits'])
