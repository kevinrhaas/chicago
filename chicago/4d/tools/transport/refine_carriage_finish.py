# SPDX-License-Identifier: GPL-3.0-or-later
"""Original C02 parked-carriage surface reconstruction, no imported imagery.

Retains all position/normal/index bytes, hierarchy and door/socket transforms.
The existing reviewed cushion model is the exact required input. Painted timber,
leather grain, paint colors and optical values are engineering reconstructions;
this does not attribute an individual carriage, finish or owner to a photograph.
"""
from pathlib import Path
import argparse
import hashlib
import io
import json
import struct

import numpy as np
from PIL import Image

BASE = 'cc469f5bda981e273d3b9a4e1ce72d1186cb9f5ffa9deae5d4af0359a2b64779'


def decode(path):
    data = path.read_bytes()
    magic, version, length = struct.unpack_from('<III', data)
    if (magic, version, length) != (0x46546c67, 2, len(data)):
        raise ValueError('Not a complete binary glTF2 asset')
    jlen, jtype = struct.unpack_from('<II', data, 12)
    if jtype != 0x4e4f534a:
        raise ValueError('Missing JSON chunk')
    doc = json.loads(data[20:20+jlen])
    off = 20+jlen
    blen, btype = struct.unpack_from('<II', data, off)
    if btype != 0x004e4942 or off+8+blen != len(data):
        raise ValueError('Expected exactly one complete binary chunk')
    return data, doc, bytearray(data[off+8:])


def png(array):
    image = Image.fromarray(array.astype(np.uint8), 'RGB')
    data = io.BytesIO()
    image.save(data, format='PNG', optimize=False, compress_level=9)
    return data.getvalue()


def noise(seed, size=256):
    """Periodic multiscale original noise; no downloaded texture or image input."""
    rng = np.random.default_rng(seed)
    raw = rng.standard_normal((size, size))
    f = np.fft.fftfreq(size)
    radius = np.sqrt(f[:, None]**2+f[None, :]**2)
    field = np.fft.ifft2(np.fft.fft2(raw)/(1+(radius/.075)**2)).real
    return field / field.std()


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--input', required=True, type=Path)
    p.add_argument('--output', required=True, type=Path)
    a = p.parse_args()
    source, doc, binary = decode(a.input)
    if hashlib.sha256(source).hexdigest() != BASE:
        raise ValueError('Requires exact reviewed cc469 cushion source')
    if a.output.exists():
        raise ValueError('Fresh output directory required')
    a.output.mkdir(parents=True)
    before = json.loads(json.dumps(doc))
    old_binary = bytes(binary)
    views, accessors = doc['bufferViews'], doc['accessors']
    images, textures = doc.setdefault('images', []), doc.setdefault('textures', [])
    sampler = len(doc.setdefault('samplers', []))
    doc['samplers'].append({'magFilter': 9729, 'minFilter': 9987, 'wrapS':10497, 'wrapT':10497})
    added_images = []

    def append(data, target=None):
        while len(binary) % 4:
            binary.append(0)
        view = {'buffer':0, 'byteOffset':len(binary), 'byteLength':len(data)}
        if target is not None:
            view['target'] = target
        index = len(views)
        views.append(view)
        binary.extend(data)
        return index

    def texture(name, rgb):
        data = png(rgb)
        (a.output/name).write_bytes(data)
        vi = append(data)
        ii = len(images)
        images.append({'name':name, 'bufferView':vi, 'mimeType':'image/png'})
        ti = len(textures)
        textures.append({'source':ii, 'sampler':sampler})
        added_images.append({'file':name, 'sha256':hashlib.sha256(data).hexdigest(), 'width':256, 'height':256})
        return {'index':ti}

    # Three painted/leather surface families, all author-generated. Base maps
    # stay near white so the exact original reconstructed colors remain explicit.
    for mat, label, seed, rough, color, metal, scale in [
        (0,'paint',4021,.31,[.028,.047,.038,1],0,.11),
        (1,'painted_running_gear',4022,.37,[.120,.032,.021,1],0,.13),
        (2,'leather',4023,.69,[.090,.034,.017,1],0,.28),
    ]:
        field = noise(seed)
        fine = noise(seed+21)
        base = np.clip(243+field*2.1, 232, 251)
        base_rgb = np.stack([base]*3, axis=-1)
        roughness = np.clip(rough+field*.025+fine*.009, .05, .95)
        orm = np.empty((256,256,3)); orm[:,:,0] = 255
        orm[:,:,1] = roughness*255; orm[:,:,2] = metal*255
        # Derivative normal of an original periodic microscopic height field.
        # Leather uses shallow irregular cells, not an invented measured hide.
        height = field + (.45*np.abs(fine) if mat == 2 else .12*fine)
        dx = (np.roll(height,-1,axis=1)-np.roll(height,1,axis=1))*.5
        dy = (np.roll(height,-1,axis=0)-np.roll(height,1,axis=0))*.5
        n = np.stack([-dx*scale,-dy*scale,np.ones_like(dx)],axis=-1)
        n /= np.linalg.norm(n,axis=-1,keepdims=True)
        normal = (n*.5+.5)*255
        m = doc['materials'][mat]
        m['name'] = 'reconstructed_'+label
        m['pbrMetallicRoughness'] = {'baseColorFactor':color,'metallicFactor':metal,'roughnessFactor':1,
            'baseColorTexture':texture(label+'-color.png',base_rgb),
            'metallicRoughnessTexture':texture(label+'-roughness.png',orm)}
        m['normalTexture'] = {**texture(label+'-normal.png',normal), 'scale':1}
        if mat != 2:
            m['extensions'] = {'KHR_materials_clearcoat':{'clearcoatFactor':.24,'clearcoatRoughnessFactor':.23}}

    # Preserve brass/iron as the original materials with less uniform optics.
    # No geometry or allocation/draw-call increase is introduced.
    doc['materials'][3]['pbrMetallicRoughness'].update(baseColorFactor=[.56,.32,.10,1],metallicFactor=.92,roughnessFactor=.25)
    doc['materials'][4]['pbrMetallicRoughness'].update(baseColorFactor=[.027,.030,.032,1],metallicFactor=.86,roughnessFactor=.42)
    # Reconstructed tinted glazing exposes the already modeled empty cabin.
    # This is an explicit optical material choice, not measured window glass.
    doc['materials'][6]['pbrMetallicRoughness'].update(baseColorFactor=[.090,.140,.160,.30],metallicFactor=0,roughnessFactor=.12)
    doc['materials'][6]['alphaMode']='BLEND'
    used = doc.setdefault('extensionsUsed', [])
    if 'KHR_materials_clearcoat' not in used:
        used.append('KHR_materials_clearcoat')

    # Original UV coordinates are based only on the immutable mesh positions and
    # face normals. Paint .125m / leather .25m tiles bound the visible grain scale.
    uv_count = 0
    for mesh in doc['meshes']:
        for prim in mesh['primitives']:
            material = prim.get('material')
            if material not in (0,1,2):
                continue
            attrs = prim['attributes']
            if 'TEXCOORD_0' in attrs:
                raise ValueError('Unexpected original UV stream')
            def triples(ai):
                acc = before['accessors'][ai]; view = before['bufferViews'][acc['bufferView']]
                if acc['componentType'] != 5126 or acc['type'] != 'VEC3' or 'byteStride' in view:
                    raise ValueError('Unexpected source vertex layout')
                return np.frombuffer(old_binary,dtype='<f4',count=acc['count']*3,
                    offset=view.get('byteOffset',0)+acc.get('byteOffset',0)).reshape((-1,3))
            positions, normals = triples(attrs['POSITION']), triples(attrs['NORMAL'])
            if len(positions) % 3:
                raise ValueError('Expected original unindexed triangle surfaces')
            faces=positions.astype(np.float64).reshape((-1,3,3))
            face_normals=np.cross(faces[:,1]-faces[:,0],faces[:,2]-faces[:,0])
            if np.any(np.linalg.norm(face_normals,axis=1)<1e-15):
                raise ValueError('Degenerate source triangle')
            axis = np.repeat(np.argmax(np.abs(face_normals),axis=1),3)
            uv = np.empty((len(positions),2),dtype='<f4')
            rate = 4 if material == 2 else 8
            for dim, pair in [(0,(2,1)),(1,(0,2)),(2,(0,1))]:
                selected = axis == dim
                uv[selected] = positions[selected][:,pair]*rate
            ai = len(accessors)
            vi = append(uv.tobytes(),34962)
            accessors.append({'bufferView':vi,'componentType':5126,'count':len(uv),'type':'VEC2',
                'min':uv.min(axis=0).tolist(),'max':uv.max(axis=0).tolist()})
            attrs['TEXCOORD_0'] = ai
            # Explicit portable tangent frames, derived from actual immutable
            # triangle edges and these exact UV coordinates, no runtime warning.
            tu=uv.astype(np.float64).reshape((-1,3,2))
            dp1=faces[:,1]-faces[:,0]; dp2=faces[:,2]-faces[:,0]
            du1=tu[:,1]-tu[:,0]; du2=tu[:,2]-tu[:,0]
            det=du1[:,0]*du2[:,1]-du1[:,1]*du2[:,0]
            if np.any(np.abs(det)<1e-15):
                raise ValueError('Degenerate authored UV triangle')
            raw_t=(dp1*du2[:,1,None]-dp2*du1[:,1,None])/det[:,None]
            raw_b=(dp2*du1[:,0,None]-dp1*du2[:,0,None])/det[:,None]
            raw_t=np.repeat(raw_t,3,axis=0); raw_b=np.repeat(raw_b,3,axis=0)
            nn=normals.astype(np.float64)
            tt=raw_t-nn*np.sum(nn*raw_t,axis=1)[:,None]
            tt/=np.linalg.norm(tt,axis=1)[:,None]
            sign=np.where(np.sum(np.cross(nn,tt)*raw_b,axis=1)<0,-1.,1.)
            tangents=np.column_stack((tt,sign)).astype('<f4')
            assert np.isfinite(tangents).all()
            assert np.max(np.abs(np.sum(nn*tangents[:,:3],axis=1)))<1e-5
            vi=append(tangents.tobytes(),34962)
            ai=len(accessors)
            accessors.append({'bufferView':vi,'componentType':5126,'count':len(tangents),'type':'VEC4'})
            attrs['TANGENT']=ai
            uv_count += 1
    doc['buffers'][0]['byteLength'] = len(binary)
    doc['extras']['asset_id']='carriage_c02_parked_1904_reconstructed_01'
    doc['extras']['status']='Original parked town-carriage reconstruction; maker, subtype and owner unknown; photographic quality remains unaccepted'
    doc['extras']['scene_eligibility']='1904 parked reconstructed example only; no exact recorded carriage presence or ownership asserted'
    doc['extras']['reference_scope']['scene_eligibility']='1904 period analogy only; no specific vehicle presence, date or ownership inferred'
    doc['extras']['driver_cushion_study']['period']='1904 reconstructed example'
    doc['extras']['parked_display']={'year':1904,'confidence':'reconstructed','owner':'unknown','maker':'unknown','subtype':'unknown',
        'door_interaction_enabled':False,'boarding_enabled':False,'occupants':False,'traffic_enabled':False,
        'note':'Closed empty carriage displayed as a declared period reconstruction; reference photographs are not exact replicas.'}
    doc['extras']['surface_refinement'] = {
        'scope':'Original reconstructed painted timber and leather microfinish; parked 1904 demonstration',
        'source_images':'none; algorithmically authored original maps',
        'historical_limits':'No specific carriage, paint color, chemistry, hide, owner or measured optical property is attested',
        'baseline_sha256':BASE, 'geometry_nodes_rig_doors_sockets':'unchanged',
        'source_faces':doc['extras']['statistics']['triangles'], 'photographic_acceptance':False,
        'tile_m':{'paint':.125,'leather':.25}, 'native_texture_resolution':256,
    }
    # Assert protected data before writing. Extra UV streams and images are the
    # complete geometry-buffer delta; none of the old bytes is regenerated.
    assert bytes(binary[:len(old_binary)]) == old_binary
    for key in ['nodes','scenes','scene','asset']:
        assert doc.get(key) == before.get(key), key
    for old,new in zip(before['meshes'],doc['meshes']):
        newcopy=json.loads(json.dumps(new))
        for prim in newcopy['primitives']:
            prim['attributes'].pop('TEXCOORD_0',None)
            prim['attributes'].pop('TANGENT',None)
        assert old == newcopy
    j = json.dumps(doc,separators=(',',':')).encode()
    j += b' '*((-len(j))%4)
    binary += b'\0'*((-len(binary))%4)
    out=struct.pack('<III',0x46546c67,2,12+8+len(j)+8+len(binary))
    out+=struct.pack('<II',len(j),0x4e4f534a)+j+struct.pack('<II',len(binary),0x004e4942)+binary
    (a.output/'carriage-c02.glb').write_bytes(out)
    (a.output/'carriage-c02.json').write_text(json.dumps(doc['extras'],indent=2)+'\n')
    receipt={'baseline_sha256':BASE,'output_sha256':hashlib.sha256(out).hexdigest(),
        'old_binary_prefix_exact':True,'nodes_doors_sockets_exact':True,'positions_normals_indices_exact':True,
        'triangles':doc['extras']['statistics']['triangles'],'uv_streams_added':uv_count,
        'textures':added_images,'output_bytes':len(out),'geometry_acceptance':'inherited only; no new model/fit qualification',
        'appearance_acceptance':'UNREVIEWED; actual images required','glazing':'reconstructed tinted alpha-blended glass, original pane geometry retained',
        'scene_eligibility':'1904 parked reconstruction only, owner/maker/subtype unknown; door/boarding/traffic interactions disabled'}
    (a.output/'recipe.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt))


if __name__=='__main__':
    main()
