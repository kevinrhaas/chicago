#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Prepare photographs as shared, review-only hm08 faces. See docs/PHOTO-FACE-PILOT.md.

No resident, shipped kit, or existing portrait is written. Detection and fitting happen
offline; the renderer consumes JPEG + JSON and the existing portable-human meshes.
"""
import argparse
import hashlib
import json
import math
import pathlib
import re
import sys
import time
import struct
from functools import lru_cache
from concurrent.futures import ProcessPoolExecutor

import numpy as np
from PIL import Image, ImageOps, ImageDraw
from scipy.interpolate import LinearNDInterpolator, NearestNDInterpolator
from scipy.ndimage import distance_transform_edt, gaussian_filter

import face_library as L
import fit_portrait_face as F
import bake_likeness_skin as B

ROOT = F.ROOT
PILOT = ROOT / 'data/humans/variation/photo_face_pilot.json'
FORMAT = 'chicago4d_photo_face_review_v2'
BASE = {'male': 'glessner_john_j_1904', 'female': 'glessner_frances_m_1904'}
TILE = 256
PAD = 8  # duplicated texels: bilinear filtering and the near mip levels stay inside a face
LIMIT = 256
PAGE_FACES = 16
CROWD_EDGE = 1024


def digest(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def relative(path, base=ROOT):
    return pathlib.Path(path).resolve().relative_to(base.resolve()).as_posix()


def source_record(source):
    if not re.fullmatch(r'[a-zA-Z0-9_-]+', source):
        raise ValueError('source must be a data/sources record id')
    path = ROOT / 'data/sources' / f'{source}.json'
    rec = json.loads(path.read_text())
    if rec.get('rights_status') != 'cleared' or rec.get('asset_use') != 'texture':
        raise ValueError(f'{source}: texture use must be cleared in the source record')
    if not str(rec.get('url', '')).startswith('https://'):
        raise ValueError(f'{source}: the source record needs its https locator')
    return rec


def read_photo(path, crop=None):
    with Image.open(path) as opened:
        if opened.width * opened.height > 40_000_000:
            raise ValueError('photo exceeds 40 megapixels; export a smaller copy first')
        im = ImageOps.exif_transpose(opened).convert('RGB')
    if crop is not None:
        if (len(crop) != 4 or any(not isinstance(x, int) for x in crop)
                or not (0 <= crop[0] < crop[2] <= im.width and 0 <= crop[1] < crop[3] <= im.height)):
            raise ValueError('crop must be an integer rectangle inside the oriented photo')
        im = im.crop(tuple(crop))
    if min(im.size) < 160:
        raise ValueError('photo crop must be at least 160 pixels on both sides')
    return im


def detect(im, model):
    import mediapipe as mp
    from mediapipe.tasks import python
    from mediapipe.tasks.python import vision
    large = im.resize((im.width * 2, im.height * 2), Image.Resampling.LANCZOS)
    options = vision.FaceLandmarkerOptions(base_options=python.BaseOptions(model_asset_path=str(model)), num_faces=2)
    with vision.FaceLandmarker.create_from_options(options) as detector:
        result = detector.detect(mp.Image(image_format=mp.ImageFormat.SRGB, data=np.asarray(large)))
    if len(result.face_landmarks) != 1:
        raise ValueError(f'crop must contain exactly one detectable face; found {len(result.face_landmarks)}')
    return [[round(p.x * im.width, 4), round(p.y * im.height, 4)] for p in result.face_landmarks[0]]


def portrait(entry, points, size):
    if entry.get('shape_from'):
        import historical_photo_shape as H
        return H.portrait(entry, points, size)
    base = BASE[entry['sex']]
    table = json.loads(F.MP_TABLE.read_text())['bodies'][base]
    axes = json.loads((F.PORTRAITS / ('pa1904_grey_w_l.json' if entry['sex'] == 'male' else 'pa1904_grey_mrs_w_l.json')).read_text())['axes']
    marks = [{'landmark': k, 'x': points[i][0], 'y': points[i][1], 'sigma_px': 3.5}
             for k, i in [('pupil_r', 468), ('pupil_l', 473)]]
    marks += [{'landmark': k, 'x': points[int(k[3:])][0], 'y': points[int(k[3:])][1], 'sigma_px': 3.5}
              for k in table['points']]
    outline_fields={}
    if entry.get('historical',{}).get('shape_mode')=='new_photo_fit':
        outline=min(table['outline'],key=lambda o:abs(o['solved_yaw_deg']))
        marks += [{'landmark':k,'x':points[int(k[4:])][0],'y':points[int(k[4:])][1],'sigma_px':5.0} for k in outline['points']]
        outline_fields={'outline_yaw_deg':outline['solved_yaw_deg']}
    child=entry.get('population')=='child'
    if child:
        import photo_face_child as C
        actual=C.body(entry)
        reference_age=json.loads(F.KIT_JSON.read_text())['assets'][actual]['base_age_years']
    else:actual,reference_age=base,entry['age']
    return {'base_body': actual, **({'calibration_body':base} if child else {}),
            'sex': entry['sex'], 'age_at_picture_years': reference_age,
            'axes': axes, 'marks': marks, 'scan_size_px': list(size), **outline_fields,
            **({'read_by_eye':entry['historical']['fit_controls']} if entry.get('historical',{}).get('fit_controls') else {}),
            'grade': 'reconstructed', 'source': entry['source'],
            'not_modelled': ['profile depth from a single front photograph', 'ears and hair outside the face patch']}


def blend_face_photo(photo, fallback, covered):
    """Join a measured photo to the existing skin without a lighting band.

    The calibrated landmark hull stops below the hairline. A narrow alpha fade
    put the photograph's lighting change into six texels across the forehead.
    Keep fine photo detail at that boundary, but blend progressively broader
    colour/lighting over broader distances. This is baked into the same RGB
    tile; it adds no texture, geometry or work to the renderer.
    """
    alpha = np.minimum(1, distance_transform_edt(covered) / 6)[..., None]
    front, back = L.linear(photo), L.linear(fallback)
    joined = np.zeros_like(front)
    for sigma in (2, 8, 24):
        low_front = gaussian_filter(front, (sigma, sigma, 0), mode='nearest')
        low_back = gaussian_filter(back, (sigma, sigma, 0), mode='nearest')
        weight = gaussian_filter(alpha, (sigma, sigma, 0), mode='nearest')
        joined += (front - low_front) * weight + (back - low_back) * (1 - weight)
        front, back = low_front, low_back
    return L.srgb8(joined + front * weight + back * (1 - weight))


def bake_face(im, points, sex, size=TILE - PAD * 2, body=None):
    """Landmark correspondence warps a front photo onto the existing hm08 UV island.

    The measured hull supplies the facial detail. Its broad lighting joins the
    existing skin outside that hull; no additional photographic view is invented.
    """
    header, _, _ = F.load_kit()
    blob = (F.KIT_JSON.parent / header['bin']).read_bytes()
    uvs = np.frombuffer(blob, dtype='<u2', count=header['vertex_count'] * 2,
                        offset=header['uvs']['offset']).reshape(-1, 2) / 65535
    index = F.kit_index()
    table = json.loads(F.MP_TABLE.read_text())['bodies'][BASE[sex]]
    correspond = [(int(k[3:]), v['vertex']) for k, v in table['points'].items()]
    outline = min(table['outline'], key=lambda x: abs(x['solved_yaw_deg']))
    correspond += [(int(k[4:]), v['vertex']) for k, v in outline['points'].items()]
    groups = {}
    for landmark, vertex in correspond:
        groups.setdefault(index[vertex], []).append(points[landmark])
    target = np.array([uvs[i] for i in groups])
    photo = np.array([np.mean(p, axis=0) for p in groups.values()])
    box = np.array(L.box_uv(json.loads(L.RECORD.read_text())))
    u, v = np.meshgrid(box[0] + (np.arange(size) + .5) / size * (box[2] - box[0]),
                       box[1] + (np.arange(size) + .5) / size * (box[3] - box[1]))
    query = np.stack([u, v], -1)
    mapped = LinearNDInterpolator(target, photo)(query)
    covered = np.isfinite(mapped).all(axis=2)
    if covered.mean() < .15:
        raise ValueError('too little of the face could be mapped to the head')
    mapped[~covered] = NearestNDInterpolator(target, photo)(query[~covered])
    from scipy.ndimage import map_coordinates
    rgb = np.asarray(im, dtype=float).copy()
    # The portable head has separate eyeballs. Painting the photograph's pupils
    # onto the skin as well leaves dark crescents on the lids when their openings
    # differ. Keep the photographic lid/brow surround, and fill only the opening
    # from the skin immediately above and below it. The existing eyes stay visible.
    for ring in [(33,7,163,144,145,153,154,155,133,173,157,158,159,160,161,246),
                 (263,249,390,373,374,380,381,382,362,398,384,385,386,387,388,466)]:
        mask = Image.new('1', im.size)
        ImageDraw.Draw(mask).polygon([tuple(points[i]) for i in ring], fill=1)
        opening = np.asarray(mask)
        for x in np.where(opening.any(axis=0))[0]:
            ys = np.where(opening[:,x])[0]
            top, bottom = max(0,ys[0]-1), min(im.height-1,ys[-1]+1)
            a, b = rgb[max(0,top-2),x].copy(), rgb[min(im.height-1,bottom+2),x].copy()
            rgb[top:bottom+1,x] = np.linspace(a,b,bottom-top+1)
    warped = np.stack([map_coordinates(rgb[:, :, c], [mapped[:, :, 1], mapped[:, :, 0]], order=1, mode='nearest') for c in range(3)], -1)
    # Both cheeks, away from the lips, eyebrows and nose, measure the photo's skin.
    cheeks = np.array([points[i] for i in (50, 101, 118, 205, 280, 330, 347, 425)])
    samples = []
    for x, y in cheeks:
        x, y = round(x), round(y)
        samples.extend(rgb[max(0,y-3):min(im.height,y+4), max(0,x-3):min(im.width,x+4)].reshape(-1,3))
    tone = np.median(L.linear(np.array(samples)), axis=0)
    record = json.loads(L.RECORD.read_text())
    from io import BytesIO
    fallback = Image.open(BytesIO(L.glb_skin(ROOT / 'assets/humans/web' / f'{body or BASE[sex]}.lod0.glb')))
    fallback = np.asarray(L.cut_of(Image, fallback, record).resize((size,size)), dtype=float)
    mask = L.mask_over(record, size)
    ring = (mask > .05) & (mask < .95)
    original = L.linear(fallback)
    base_tone = original[ring].mean(axis=0)
    fallback = L.srgb8(original * (tone / np.maximum(base_tone, .001)))
    tile = blend_face_photo(warped, fallback, covered)
    return np.pad(tile, ((PAD,PAD),(PAD,PAD),(0,0)), mode='edge'), tone.tolist(), base_tone.tolist()


def validate_entry(entry):
    if not re.fullmatch(r'[a-zA-Z0-9_-]{1,96}', entry['id']):
        raise ValueError('face id must contain only letters, digits, underscores and hyphens')
    child=entry.get('population')=='child'
    if entry['sex'] not in BASE or not (2 <= entry['age'] < 18 if child else 18 <= entry['age'] <= 100):
        raise ValueError('the pilot supports adult male/female calibrated bodies, age 18 to 100')
    if child and entry.get('texture_only') is not True:
        raise ValueError('child photos transfer texture only; preserve the child head geometry')
    if child and entry.get('fitted',{}).get('values'):
        raise ValueError('a cached child photo cannot transfer head morphs')
    source_record(entry['source'])
    if entry.get('shape_from'):
        import historical_photo_shape as H
        H.record(entry)


@lru_cache(maxsize=2)
def native_iris_tone(sex,body=None):
    from io import BytesIO
    blob=(ROOT/'assets/humans'/f'{body or BASE[sex]}.lod0.glb').read_bytes()
    n=struct.unpack('<I',blob[12:16])[0];doc=json.loads(blob[20:20+n]);binary=blob[28+n:]
    primitive=next(p for m in doc['meshes'] for p in m['primitives'] if doc['materials'][p['material']]['name']=='eyes__iris')
    mat=doc['materials'][primitive['material']]
    texture=doc['textures'][mat['pbrMetallicRoughness']['baseColorTexture']['index']]
    view=doc['bufferViews'][doc['images'][texture['source']]['bufferView']]
    im=Image.open(BytesIO(binary[view.get('byteOffset',0):view.get('byteOffset',0)+view['byteLength']])).convert('RGB')
    a=doc['accessors'][primitive['attributes']['TEXCOORD_0']];v=doc['bufferViews'][a['bufferView']]
    uv=np.frombuffer(binary,dtype='<f4',count=a['count']*2,offset=v.get('byteOffset',0)+a.get('byteOffset',0)).reshape(-1,2)
    xy=np.int64(np.clip(uv,0,.999)*im.size)
    return L.linear(np.percentile(np.asarray(im)[xy[:,1],xy[:,0]],75,axis=0))


def measured_lid_rest(portrait_record, fit, points):
    """Fit the opening of the actual mesh, rather than guessing it from an age."""
    header,refs,axes=F.load_kit();asset=portrait_record['base_body'];rest=F.body_rest(asset)
    rows=np.arange(len(rest));X,_,_,held,_=F.face_base('photo-review',portrait_record,header,refs,axes,rows)
    option=int(fit['values'].get('head_shape.option',0))
    for aid,value in fit['values'].items():
        if aid in axes and aid not in held:X+=F.delta_at(axes[aid],value,option,rows)
    index=F.kit_index();table=json.loads(F.MP_TABLE.read_text())['bodies'][portrait_record.get('calibration_body',asset)]
    mp={int(k[3:]):index[v['vertex']] for k,v in table['points'].items()}
    head={'X':X,'rest':rest,'tri':F.body_triangles(asset),'mp':mp,'asset':asset}
    camera=fit['camera'];cam=np.r_[np.radians([camera['yaw_deg'],camera['pitch_deg'],camera['roll_deg']]),camera['px_per_m'],camera['shift_px']]
    centre=np.array(fit['projection_centre_m']);front={'pts':np.array(points),'cam':cam}
    found=B.rest_lids(head,front,centre)
    if found is None:return None
    if found['rest']>0:return {'rest':found['rest'],'picture_open_mm':found['picture_open_mm'],'fitted_open_mm':found['fitted_open_mm']}
    rim=np.unique(np.array(B.open_edges(head['tri'])));edges=[]
    for up,lo in B.LID_PAIRS:
        if up not in mp or lo not in mp:continue
        mid=(X[mp[up]]+X[mp[lo]])/2
        near=rim[(np.abs(X[rim,0]-mid[0])<B.LID_EDGE_M[0])&(np.abs(X[rim,1]-mid[1])<B.LID_EDGE_M[1])&(X[rim,2]>mid[2]-B.LID_EDGE_M[2])]
        if len(near)<2:return None
        edges.append((int(near[np.argmax(X[near,1])]),int(near[np.argmin(X[near,1])])))
    target=float(np.mean(found['picture_open_mm']));shut=found['shut']
    def opening(weight):
        P,_=B.project(X+shut*weight,cam,centre)
        return float(np.mean([np.linalg.norm(P[a]-P[b])*1000/cam[3] for a,b in edges]))
    low,high=-.35,0.0
    for _ in range(24):
        mid=(low+high)/2
        if opening(mid)>target:low=mid
        else:high=mid
    return {'rest':round(high,3),'picture_open_mm':found['picture_open_mm'],'fitted_open_mm':found['fitted_open_mm']}


def eye_appearance(im, points, sex, fit, portrait_record):
    """Read sclera and iris tone away from catchlights; record the visible lid aperture."""
    from scipy.ndimage import map_coordinates
    rgb=np.asarray(im,dtype=float)
    whites=[];irises=[];apertures=[]
    for outer,inner,upper,lower,centre in [(33,133,159,145,468),(263,362,386,374,473)]:
        a,b=np.array(points[outer]),np.array(points[inner]);c=np.array(points[centre])
        for t in (.18,.82):
            xy=a*(1-t)+b*t
            whites.append([map_coordinates(rgb[:,:,channel],[[xy[1]],[xy[0]]],order=1)[0] for channel in range(3)])
        radius=max(1,np.linalg.norm(a-b)*.12)
        for angle in np.linspace(0,2*math.pi,16,endpoint=False):
            xy=c+radius*np.array([math.cos(angle),math.sin(angle)])
            irises.append([map_coordinates(rgb[:,:,channel],[[xy[1]],[xy[0]]],order=1)[0] for channel in range(3)])
        apertures.append(np.linalg.norm(np.array(points[upper])-points[lower])/max(1,np.linalg.norm(a-b)))
    white=L.linear(np.percentile(whites,65,axis=0))
    iris=L.linear(np.percentile(irises,45,axis=0))
    # Avoid extrapolating white from a clipped studio catchlight or dark lashes.
    # Corner samples include some vascular lid colour. Keep their measured
    # brightness with a mildly warm neutral sclera, rather than painting it pink.
    brightness=float(np.clip(np.dot(white,[.2126,.7152,.0722]),.18,.52))
    white=brightness*np.array([1.04,1,.96])
    iris=np.clip(iris,.003,.28)
    # Use a conservative closure when no fitted aperture can be measured.
    # A measured aperture can also open lids that start narrower than the source.
    rest=float(np.clip((.36-float(np.mean(apertures)))/.36,0,.42))
    gain=np.clip(iris/np.maximum(native_iris_tone(sex,portrait_record['base_body']),.002),.4,3)
    measured=measured_lid_rest(portrait_record,fit,points)
    if measured is not None:rest=measured['rest']
    centres=[np.array(points[mid]) for mid in (468,473)]
    radii=[float(np.mean([np.linalg.norm(np.array(points[i])-c) for i in ring]))/fit['camera']['px_per_m']
           for c,ring in zip(centres,[(469,470,471,472),(474,475,476,477)])]
    return {'sclera_linear':white.tolist(),'iris_linear':iris.tolist(),'iris_gain':gain.tolist(),'lid_rest':rest,
            'centres_uv':[(c/np.array(im.size)).tolist() for c in centres], 'iris_radius_m':radii,
            'aperture_ratio':float(np.mean(apertures)), 'opening_fit':measured}


def bake_hair(im, points, sex, fit, size=TILE-PAD*2, body=None):
    """Keep the source hair in a shared photo atlas, projected in bind space.

    The stock cap repeats UVs between strand cards, so baking a different photo
    into those UVs repeats and smears it. Object-space projection keeps every
    point on every card at its actual place in the same source photograph.
    """
    from io import BytesIO
    blob=(ROOT/'assets/humans'/f'{body or BASE[sex]}.lod0.glb').read_bytes()
    n=struct.unpack('<I',blob[12:16])[0];doc=json.loads(blob[20:20+n]);binary=blob[28+n:]
    primitive=next(m['primitives'][0] for m in doc['meshes'] if 'hair' in m['name'])
    a=doc['accessors'][primitive['attributes']['POSITION']];v=doc['bufferViews'][a['bufferView']]
    X=np.frombuffer(binary,dtype='<f4',count=a['count']*3,offset=v.get('byteOffset',0)+a.get('byteOffset',0)).reshape(-1,3).astype(float)
    material=doc['materials'][primitive['material']]
    texture=doc['textures'][material['pbrMetallicRoughness']['baseColorTexture']['index']]
    image=doc['images'][texture['source']];view=doc['bufferViews'][image['bufferView']]
    original=Image.open(BytesIO(binary[view.get('byteOffset',0):view.get('byteOffset',0)+view['byteLength']])).convert('RGBA')
    rgb=np.asarray(im,dtype=float)
    bg=np.median(np.array([rgb[2,2],rgb[2,-3],rgb[-3,2],rgb[-3,-3]]),axis=0)
    top=rgb[:max(4,round(points[10][1]))]
    fg=np.linalg.norm(top-bg,axis=2)>22
    candidates=top[fg]
    hair=np.median(candidates,axis=0) if len(candidates)>20 else np.array([65,48,35])
    hair_lin=L.linear(hair)
    rgba=np.asarray(original)
    was=np.median(L.linear(rgba[:,:,:3][rgba[:,:,3]>128]),axis=0)
    gain=(hair_lin/np.maximum(was,.003)).tolist()
    cam=fit['camera'];rot=F.rot(*np.radians([cam['yaw_deg'],cam['pitch_deg'],cam['roll_deg']]))
    centre=np.array(fit['projection_centre_m'])
    projected=(X-centre)@rot.T
    projected=np.stack([cam['shift_px'][0]+cam['px_per_m']*projected[:,0],cam['shift_px'][1]-cam['px_per_m']*projected[:,1]],axis=1)
    yy,xx=np.where(fg)
    visible_top=int(yy.min()) if len(yy) else 0
    width=float(np.percentile(xx,99)-np.percentile(xx,1)) if len(xx)>20 else float(np.ptp(projected[:,0]))
    sx=float(np.clip(width/max(1,np.ptp(projected[:,0])),.85,1.35))
    up=float(np.clip((projected[:,1].min()-visible_top)/cam['px_per_m'],0,.05))
    pivot=float(np.quantile(X[:,1],.25));height=float(X[:,1].max()-pivot)
    lo,hi=X.min(axis=0),X.max(axis=0)
    shell={'centre_m':[(lo[0]+hi[0])/2,(lo[1]+hi[1]+up)/2,(lo[2]+hi[2])/2],
           'radius_m':[(hi[0]-lo[0])*sx*.53,(hi[1]-lo[1]+up)*.53,(hi[2]-lo[2])*.52],
           'base_centre_m':((lo+hi)/2).tolist(),'base_radius_m':((hi-lo)/2).tolist(),
           'bone':'head'}
    u=np.r_[cam['px_per_m']*rot[0]/im.width,(cam['shift_px'][0]-cam['px_per_m']*np.dot(rot[0],centre))/im.width]
    v=np.r_[-cam['px_per_m']*rot[1]/im.height,(cam['shift_px'][1]+cam['px_per_m']*np.dot(rot[1],centre))/im.height]
    projection={'u':u.tolist(),'v':v.tolist(),'toward':rot[2].tolist(),'fallback_gain':gain,'hairline_v':points[10][1]/im.height}
    oval=(10,338,297,332,284,251,389,356,454,323,361,288,397,365,379,378,400,377,152,148,176,149,150,136,172,58,132,93,234,127,162,21,54,103,67,109)
    face_mask=Image.new('L',im.size)
    ImageDraw.Draw(face_mask).polygon([tuple(points[i]) for i in oval],fill=255)
    head=np.clip((np.linalg.norm(rgb-bg,axis=2)-12)/18,0,1)
    matte=head*(1-np.asarray(face_mask)/255)
    source=np.dstack([np.uint8(rgb),np.uint8(np.clip(matte*255,0,255))])
    source[source[:,:,3]==0,:3]=0
    photo=np.asarray(Image.fromarray(source).resize((size,size),Image.Resampling.LANCZOS))
    return np.pad(photo,((PAD,PAD),(PAD,PAD),(0,0)),mode='edge'),hair_lin.tolist(),shell,projection


def write_hair_shell(path, longitude, latitude):
    """Portable unit scalp, generated once per LOD; source-bounded dimensions are JSON."""
    positions=[];uv=[];tri=[]
    for j in range(latitude+1):
        angle=math.pi*j/latitude
        for i in range(longitude+1):
            around=2*math.pi*i/longitude
            positions.append([math.sin(angle)*math.cos(around),math.cos(angle),math.sin(angle)*math.sin(around)])
            uv.append([i/longitude,j/latitude])
    for j in range(latitude):
        for i in range(longitude):
            a=j*(longitude+1)+i;b=a+longitude+1
            if j:tri.extend([a,a+1,b])
            if j<latitude-1:tri.extend([a+1,b+1,b])
    arrays=[np.array(positions,dtype='<f4'),np.array(positions,dtype='<f4'),np.array(uv,dtype='<f4'),np.array(tri,dtype='<u2')]
    binary=bytearray();views=[];accessors=[]
    for index,a in enumerate(arrays):
        while len(binary)%4:binary.append(0)
        views.append({'buffer':0,'byteOffset':len(binary),'byteLength':a.nbytes})
        binary.extend(a.tobytes())
        accessors.append({'bufferView':index,'componentType':5123 if index==3 else 5126,
                          'count':len(a),'type':'SCALAR' if index==3 else ('VEC2' if index==2 else 'VEC3')})
    accessors[0].update(min=[-1,-1,-1],max=[1,1,1])
    doc={'asset':{'version':'2.0','generator':'tools/photo_face_library.py'},'buffers':[{'byteLength':len(binary)}],
         'bufferViews':views,'accessors':accessors,'meshes':[{'name':'photo_hair_scalp','primitives':[{'attributes':{'POSITION':0,'NORMAL':1,'TEXCOORD_0':2},'indices':3}]}],
         'nodes':[{'mesh':0}],'scenes':[{'nodes':[0]}],'scene':0}
    encoded=json.dumps(doc,separators=(',',':')).encode()
    encoded+=b' '*((-len(encoded))%4);binary+=b'\0'*((-len(binary))%4)
    data=struct.pack('<III',0x46546c67,2,12+8+len(encoded)+8+len(binary))+struct.pack('<II',len(encoded),0x4e4f534a)+encoded+struct.pack('<II',len(binary),0x004e4942)+binary
    path.write_bytes(data)
    return {'file':path.name,'sha256':digest(path),'bytes':len(data),'triangles':len(tri)//3,'vertices':len(positions)}


def prepare_face(task):
    i, e, im, inputs, frontal, model = task
    began = time.monotonic()
    if e.get('landmarks') is None and model is None:
        raise ValueError('first import needs --model face_landmarker.task; rebuilds use pinned landmarks')
    points = e.get('landmarks') or detect(im, model)
    if len(points) != 478 or not np.isfinite(points).all():
        raise ValueError(f"{e['id']}: expected 478 finite detected landmarks")
    p = portrait(e, points, im.size)
    fit_inputs = {k:v for k,v in inputs.items() if k not in (relative(pathlib.Path(__file__)),relative(pathlib.Path(L.__file__)),relative(pathlib.Path(B.__file__)),relative(L.SKIN_JS),relative(L.RECORD))}
    signature = hashlib.sha256(json.dumps({'portrait':p,'inputs':fit_inputs,'frontal':frontal},sort_keys=True).encode()).hexdigest()
    fit = e.get('fitted') if e.get('fit_signature') == signature else None
    if fit is None and e.get('shape_from'):
        import historical_photo_shape as H
        fit = H.fit(e, p)
    if fit is None and e.get('population')=='child':
        import photo_face_child as C
        fit=C.pose(e,p)
    fit = fit or F.fit(e['id'], p, **({'yaw_starts': (0.0,)} if frontal else {}))
    skin_photo=im
    if e.get('historical'):
        import historical_photo_shape as H
        skin_photo=H.texture_photo(im,e,points)
    tile, tone, base_tone = bake_face(skin_photo, points, e['sex'],body=p['base_body'])
    hair_tile, hair_rgb, hair_shell, hair_projection = bake_hair(im,points,e['sex'],fit,body=p['base_body'])
    face = {'id': e['id'], 'sex': e['sex'], 'age': e['age'], 'label': e.get('label', e['id']),
            'source': e['source'], 'source_url': source_record(e['source'])['url'],
            'synthetic': bool(e.get('synthetic') or source_record(e['source']).get('synthetic')), 'grade': 'reconstructed',
            'base_body': p['base_body'], 'index': i, 'page':i//PAGE_FACES, 'page_index':i%PAGE_FACES,
            'photo':f"{e['id']}_source.jpg", 'values':fit['values'], 'fit_rms_px':fit['rms_px'], 'camera':fit['camera'],
            'tone_rgb':tone, 'body_gain':(np.array(tone)/np.maximum(base_tone,.001)).tolist(),
            'hair_rgb':hair_rgb, 'hair_shell':hair_shell, 'hair_projection':hair_projection,
            'eyes':eye_appearance(im,points,e['sex'],fit,p), 'limits':p['not_modelled']}
    if e.get('population')=='child':
        face.update(population='child',texture_only=True)
        face['eyes']['centres_uv']=None
        face['limits'].append('Shared hm08 UV correspondence; the child head shape and eye geometry are preserved, not fitted from adult morphs.')
    if e.get('historical'):
        import historical_photo_shape as H
        H.appearance(face, e, p)
    e.update(landmarks=points, fitted={k:fit[k] for k in ('values','rms_px','camera','projection_centre_m')},
             fit_signature=signature, photo_sha256=digest(ROOT/e['photo']))
    return face, tile, hair_tile, e, round(time.monotonic()-began,1)


def save_texture(image, output, name, shared=None):
    if name.endswith('.png'): image.save(output/name,optimize=True)
    else: image.save(output/name,quality=92,subsampling=0,optimize=True)
    result={'file':name,'size_px':list(image.size),'bytes':(output/name).stat().st_size,
            'sha256':digest(output/name),'gpu_bytes_rgba8_mipmaps':math.ceil(image.width*image.height*4*4/3)}
    if shared is not None:
        prior=shared.get(result['sha256'])
        if prior:
            # A sixteen-face library's crowd and Light review sheets coincide.
            # Keep one canonical file, including when upgrading an existing output.
            if prior['file']!=name:(output/name).unlink()
            return dict(prior)
        shared[result['sha256']]=result
    return result


def build(recipe, output, model=None, fast=False, jobs=1):
    entries = recipe['faces']
    if not 1 <= len(entries) <= LIMIT or len({e['id'] for e in entries}) != len(entries):
        raise ValueError(f'use 1 to {LIMIT} unique face ids')
    if not isinstance(jobs,int) or not 1 <= jobs <= 8:
        raise ValueError('offline jobs must be between 1 and 8')
    # Validate the entire batch before writing any result.
    for e in entries:
        validate_entry(e)
    activation=recipe.get('activation')
    if activation and (activation.get('requested_by')!='owner' or activation.get('tier')!='dev'
            or activation.get('years')!=['1812','1835','1871','1904']):
        raise ValueError('activation must record the owner’s dev rollout across the four supported years')
    photos = []
    for e in entries:
        p = ROOT / e['photo']
        if e.get('photo_sha256') and digest(p) != e['photo_sha256']:
            raise ValueError(f"{e['id']}: source photo changed; refusing a silent replacement")
        photos.append(read_photo(p, e.get('crop_px')))
    recipe['frontal'] = bool(fast or recipe.get('frontal'))
    dependencies = [pathlib.Path(__file__), pathlib.Path(F.__file__), pathlib.Path(L.__file__), pathlib.Path(B.__file__), L.SKIN_JS, F.KIT_JSON,
                    F.KIT_JSON.parent/json.loads(F.KIT_JSON.read_text())['bin'], F.AXES, F.MP_TABLE, L.RECORD]
    dependencies += [ROOT/'assets/humans'/f'{b}.lod0.glb' for b in BASE.values()]
    dependencies += [ROOT/'assets/humans/web'/f'{b}.lod0.glb' for b in BASE.values()]
    dependencies += [F.PORTRAITS/f'{p}.json' for p in ('pa1904_grey_w_l','pa1904_grey_mrs_w_l')]
    dependencies += [F.MH/'makehuman/data/3dobjs/base.obj', F.MH/'prepared.json']
    if any(e.get('population')=='child' for e in entries):
        import photo_face_child as C
        dependencies.append(pathlib.Path(C.__file__))
        for asset in sorted({C.body(e) for e in entries}):
            dependencies.extend([ROOT/'assets/humans'/f'{asset}.lod0.glb',ROOT/'assets/humans/web'/f'{asset}.lod0.glb'])
    if any(e.get('historical') for e in entries):
        dependencies += [ROOT/'tools/historical_photo_shape.py',ROOT/'tools/historical_photo_faces.py',ROOT/'data/humans/variation/person_photo_references.json']
    for e in entries:
        if e.get('shape_from'):
            import historical_photo_shape as H
            dependencies.extend([pathlib.Path(H.__file__), H.record(e)[0], F.PORTRAITS/f"{e['id']}.json",
                                 ROOT/'tools/historical_photo_state.mjs', ROOT/'renderers/web/js/human-variation.js',
                                 ROOT/'assets/humans/web/hm08_variation_persons.json'])
            asset=e['historical']['reference_asset']
            dependencies.extend([ROOT/'assets/humans'/f'{asset}.lod0.glb',ROOT/'assets/humans/web'/f'{asset}.lod0.glb'])
    inputs = {relative(p):digest(p) for p in dependencies}
    output.mkdir(parents=True, exist_ok=True)
    faces = []
    cols = math.ceil(math.sqrt(len(entries)))
    rows = math.ceil(len(entries) / cols)
    atlas = Image.new('RGB', (cols*TILE, rows*TILE))
    pages = []
    for first in range(0,len(entries),PAGE_FACES):
        n=min(PAGE_FACES,len(entries)-first);pc=math.ceil(math.sqrt(n));pr=math.ceil(n/pc)
        pages.append({'first':first,'count':n,'cols':pc,'size_px':[pc*TILE,pr*TILE],
                      'face_image':Image.new('RGB',(pc*TILE,pr*TILE)), 'hair_image':Image.new('RGBA',(pc*TILE,pr*TILE))})
    tasks=((i,e,im,inputs,recipe['frontal'],model) for i,(e,im) in enumerate(zip(entries,photos)))
    pool=ProcessPoolExecutor(max_workers=jobs) if jobs>1 else None
    try:
        results=pool.map(prepare_face,tasks,chunksize=1) if pool else map(prepare_face,tasks)
        for i,(face,tile,hair_tile,pinned,elapsed) in enumerate(results):
            entries[i].update(pinned);faces.append(face)
            atlas.paste(Image.fromarray(tile),((i%cols)*TILE,(i//cols)*TILE))
            page=pages[face['page']];at=face['page_index'];xy=((at%page['cols'])*TILE,(at//page['cols'])*TILE)
            page['face_image'].paste(Image.fromarray(tile),xy);page['hair_image'].paste(Image.fromarray(hair_tile),xy)
            photos[i].save(output/face['photo'],quality=94,subsampling=0)
            print(f"{i+1}/{len(entries)} {face['id']}: fitted {face['fit_rms_px']} px, {elapsed}s",flush=True)
    finally:
        if pool:pool.shutdown(cancel_futures=True)
    crowd_edge = 256 if all(e.get('historical') for e in entries) else CROWD_EDGE
    scale=min(.5,crowd_edge/max(atlas.size))
    crowd=atlas.resize((round(atlas.width*scale),round(atlas.height*scale)),Image.Resampling.LANCZOS)
    shared={}
    textures={'light':save_texture(crowd,output,'faces_light.jpg',shared)}
    for index,page in enumerate(pages):
        for kind,prefix in [('textures','face'),('hair_textures','hair')]:
            sheet=page.pop('face_image' if kind=='textures' else 'hair_image');page[kind]={}
            for tier,scale in [('full',1),('light',.5)]:
                image=sheet if scale==1 else sheet.resize((sheet.width//2,sheet.height//2),Image.Resampling.LANCZOS)
                name=f'page_{index:02d}_{prefix}_{tier}'+('.png' if prefix=='hair' else '.jpg')
                page[kind][tier]=save_texture(image,output,name,shared)
    shells={tier:write_hair_shell(output/f'hair_shell_{tier}.glb',*segments) for tier,segments in [('light',(20,12)),('full',(32,20))]}
    result = {'format':FORMAT, 'review_only':not bool(activation),
              'rollout':('Registered person photographs on dev.' if all(e.get('historical') for e in entries)
                         else 'Default generic faces on dev in all four years.') if activation else 'No population assignments; review the renders first.',
              'tile_px':TILE, 'padding_px':PAD, 'cols':cols, 'size_px':list(atlas.size),
              'textures':textures, 'pages':pages, 'hair_shells':shells, 'faces':faces, 'capacity':LIMIT, 'inputs_sha256':inputs,
              'budget':{'crowd_edge_px':crowd_edge,'resident_detail_pages':1,'detail_page_faces':PAGE_FACES,
                        'town_face_gpu_bytes':textures['light']['gpu_bytes_rgba8_mipmaps']+max(p['textures']['full']['gpu_bytes_rgba8_mipmaps'] for p in pages)},
              'limits':['Front photo fits do not establish profile depth.', 'Hair, ears, bodies and dress are reconstructed.',
                        'Texture budget is additional atlas memory, not whole-scene memory or a hardware performance pass.']}
    if activation:result['activation']=activation
    (output/'recipe.json').write_text(json.dumps(recipe,indent=1)+'\n')
    result['recipe_sha256'] = digest(output/'recipe.json')
    (output/'review.json').write_text(json.dumps(result,indent=1)+'\n')
    print(f'Review: tools/photo_face_review.html?library={relative(output/"review.json") if output.is_relative_to(ROOT) else output/"review.json"}')
    return result


def check(manifest):
    result = json.loads(manifest.read_text())
    assert result['format'] == FORMAT and isinstance(result['review_only'],bool)
    assert 1 <= len(result['faces']) <= LIMIT
    assert len({f['id'] for f in result['faces']}) == len(result['faces'])
    for shell in result['hair_shells'].values():
        assert digest(manifest.parent/shell['file'])==shell['sha256'], 'scalp mesh changed'
    assert result['hair_shells']['light']['triangles']<=450
    assert digest(manifest.parent/'recipe.json') == result['recipe_sha256'], 'review recipe changed'
    recipe = json.loads((manifest.parent/'recipe.json').read_text())
    assert result['review_only'] is (not bool(recipe.get('activation')))
    if not result['review_only']:
        assert result['activation']==recipe['activation'] and result['activation']['requested_by']=='owner'
        assert result['activation']['tier']=='dev' and result['activation']['years']==['1812','1835','1871','1904']
    for e in recipe['faces']:
        assert digest(ROOT/e['photo']) == e['photo_sha256'], f"{e['id']}: source photo changed"
    for name, sha in result['inputs_sha256'].items():
        assert digest(ROOT/name) == sha, f'stale generator input: {name}; rebuild the review library'
    texture_records=list(result['textures'].values())
    assert len(result['pages'])==math.ceil(len(result['faces'])/PAGE_FACES)
    for i,page in enumerate(result['pages']):
        assert page['first']==i*PAGE_FACES and 1<=page['count']<=PAGE_FACES
        assert page['textures']['full']['gpu_bytes_rgba8_mipmaps']<=5_600_000
        assert sum(page[k]['light']['gpu_bytes_rgba8_mipmaps'] for k in ('textures','hair_textures'))<=2_800_000
        texture_records.extend(page['textures'].values());texture_records.extend(page['hair_textures'].values())
    for t in texture_records:
        file = manifest.parent/t['file']
        assert digest(file)==t['sha256'] and file.stat().st_size==t['bytes'], f'stale atlas: {file}'
        with Image.open(file) as image:
            assert list(image.size)==t['size_px']
        assert t['gpu_bytes_rgba8_mipmaps']==math.ceil(math.prod(t['size_px'])*4*4/3)
    for i,f in enumerate(result['faces']):
        source_record(f['source'])
        assert np.isfinite(list(f['values'].values())).all()
        assert (manifest.parent/f['photo']).exists()
        assert f['index']==i and f['page']==i//PAGE_FACES and f['page_index']==i%PAGE_FACES
        if f.get('population')=='child':
            assert 2<=f['age']<18 and f['texture_only'] is True and f['values']=={}
            assert f['base_body'].startswith('child_') and f['eyes']['centres_uv'] is None
    assert max(result['textures']['light']['size_px'])<=CROWD_EDGE
    assert result['textures']['light']['gpu_bytes_rgba8_mipmaps']<=5_600_000
    assert result['budget']['resident_detail_pages']==1
    assert result['budget']['town_face_gpu_bytes']<=11_200_000
    print(f"PASS: {len(result['faces'])} review faces; source rights, atlas hashes, dimensions and texture budgets")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--batch', type=pathlib.Path, help='recipe JSON (paths relative to chicago/4d)')
    ap.add_argument('--photo', type=pathlib.Path, help='one front or three-quarter historical photograph')
    ap.add_argument('--id', help='stable face id; may be the intended historical person id')
    ap.add_argument('--source', help='cleared data/sources id; never invented by the importer')
    ap.add_argument('--sex', choices=BASE)
    ap.add_argument('--age', type=int, help='apparent age in the photograph')
    ap.add_argument('--population',choices=['adult','child'],default='adult',help='child keeps its existing head and transfers photographic texture only')
    ap.add_argument('--model', type=pathlib.Path, help='MediaPipe face_landmarker.task, needed only on first import')
    ap.add_argument('--output', type=pathlib.Path, help='review directory, default work/photo-faces/<id>')
    ap.add_argument('--check', type=pathlib.Path, metavar='REVIEW_JSON')
    ap.add_argument('--frontal', action='store_true', help='one camera start for a known frontal source batch')
    ap.add_argument('--synthetic', action='store_true', help='label a generated source as fictional, never archival')
    ap.add_argument('--jobs',type=int,default=1,help='offline workers, 1–8; never used by the app')
    args = ap.parse_args()
    try:
        if args.check:
            check(args.check)
            return
        if bool(args.batch) == bool(args.photo):
            ap.error('choose --batch RECIPE or --photo PHOTO')
        if args.batch:
            recipe = json.loads(args.batch.read_text())
        else:
            if not all([args.id,args.source,args.sex,args.age]):
                ap.error('--photo requires --id, --source, --sex and --age')
            recipe = {'faces':[{'id':args.id, 'photo':str(args.photo.resolve()), 'source':args.source,
                                'sex':args.sex, 'age':args.age, 'synthetic':args.synthetic}]}
            if args.population=='child':recipe['faces'][0].update(population='child',texture_only=True)
        out = (args.output or ROOT/'work/photo-faces'/recipe['faces'][0]['id']).resolve()
        # Review work cannot overwrite the existing production library or resident records.
        protected = [ROOT/'data', ROOT/'assets/humans/web/likeness', ROOT/'assets/authored']
        if any(out.is_relative_to(p) for p in protected):
            raise ValueError('output must be a review directory, not source records or existing likenesses')
        build(recipe,out,args.model,args.frontal,args.jobs)
        check(out/'review.json')
    except (ValueError, AssertionError, FileNotFoundError, KeyError) as error:
        sys.exit(f'photo face: {error}')


if __name__ == '__main__':
    main()
