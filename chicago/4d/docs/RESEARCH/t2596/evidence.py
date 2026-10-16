import hashlib, json, os, pathlib, shutil, struct
import numpy as np
from PIL import Image

tmp = pathlib.Path(os.environ['RUNNER_TEMP'])
views = os.environ['VIEWS'].split()
light_view = os.environ['LIGHT_VIEW']

def sha(p): return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def size(p): return pathlib.Path(p).stat().st_size

def ktx2_scan(glb):
    b = pathlib.Path(glb).read_bytes()
    jl = struct.unpack('<I', b[12:16])[0]
    doc = json.loads(b[20:20 + jl])
    off = 20 + jl
    bl, _kind = struct.unpack('<II', b[off:off + 8])
    bin_ = b[off + 8:off + 8 + bl]
    imgs = doc.get('images', [])
    sides, mimes = [], sorted({i.get('mimeType') for i in imgs})
    for i in imgs:
        v = doc['bufferViews'][i['bufferView']]
        o = v.get('byteOffset', 0)
        blob = bin_[o:o + 28]
        assert blob[:12] == b'\xabKTX 20\xbb\r\n\x1a\n', f'{glb}: an image is not KTX2'
        # KTX2 header: 12 B identifier, vkFormat, typeSize, then pixelWidth/pixelHeight.
        w, h = struct.unpack('<II', blob[20:28])
        sides.append(max(w, h))
    req = doc.get('extensionsRequired', [])
    return {'images': len(imgs), 'mime_types': mimes,
            'max_side': max(sides) if sides else 0,
            'requires_basisu': 'KHR_texture_basisu' in req}

def psnr(a, b):
    xa = np.asarray(Image.open(a).convert('RGB'), dtype=np.float64)
    xb = np.asarray(Image.open(b).convert('RGB'), dtype=np.float64)
    assert xa.shape == xb.shape, f'shape mismatch {xa.shape} vs {xb.shape}'
    mse = float(np.mean((xa - xb) ** 2))
    return None if mse == 0 else round(10 * np.log10(255.0 ** 2 / mse), 2)

old_pkg = json.loads((tmp / 'old/package.json').read_text())
rec = pathlib.Path('docs/RESEARCH/glessner-v4-recovery')
parts = sorted(rec.glob('part-*'))
evidence = {
    'ticket': 'T-2596',
    'run': f"{os.environ['GITHUB_SERVER_URL']}/{os.environ['GITHUB_REPOSITORY']}/actions/runs/{os.environ['GITHUB_RUN_ID']}",
    'producer': 'tools/web_derivatives.sh --only glessner_house__as_built_1887.glb (KTX2 cap 2048; light via produce_light_version cap 1024)',
    'master': {'path': 'assets/gltf/glessner_house__as_built_1887.glb',
               'sha256': sha('assets/gltf/glessner_house__as_built_1887.glb'),
               'bytes': size('assets/gltf/glessner_house__as_built_1887.glb'),
               'unchanged': sha('assets/gltf/glessner_house__as_built_1887.glb') == sha(tmp / 'old/master.glb')},
    'files': {
        'assets/web/glessner_house__as_built_1887.glb': {
            'old': {'sha256': sha(tmp / 'old/full.glb'), 'bytes': size(tmp / 'old/full.glb')},
            'new': {'sha256': sha('assets/web/glessner_house__as_built_1887.glb'),
                    'bytes': size('assets/web/glessner_house__as_built_1887.glb')}},
        'assets/web/glessner_house__as_built_1887.light.glb': {
            'old': {'sha256': sha(tmp / 'old/light.glb'), 'bytes': size(tmp / 'old/light.glb')},
            'new': {'sha256': sha('assets/web/glessner_house__as_built_1887.light.glb'),
                    'bytes': size('assets/web/glessner_house__as_built_1887.light.glb')}},
    },
    'textures': {
        'full': {'cap': 2048, **ktx2_scan('assets/web/glessner_house__as_built_1887.glb')},
        'light': {'cap': 1024, **ktx2_scan('assets/web/glessner_house__as_built_1887.light.glb')},
    },
    'package': {
        'old': old_pkg,
        'new': {'parts': len(parts), 'bytes': sum(p.stat().st_size for p in parts),
                'manifest_sha256': sha(rec / 'manifest.json')},
    },
    'renders': {},
    'match_records': 'untouched — photo_match rewrites were restored with git checkout; verdicts stay human review state',
}
assert evidence['master']['unchanged'], 'the master moved — this ticket encodes derivatives only'
assert evidence['textures']['full']['requires_basisu'] and evidence['textures']['light']['requires_basisu']
assert evidence['textures']['full']['max_side'] <= 2048, evidence['textures']['full']
assert evidence['textures']['light']['max_side'] <= 1024, evidence['textures']['light']
assert evidence['textures']['full']['mime_types'] == ['image/ktx2']
assert evidence['textures']['light']['mime_types'] == ['image/ktx2']
for v in views + [light_view + ' (light)']:
    suffix = '.light' if v.endswith('(light)') else ''
    name = v.replace(' (light)', '')
    a, b = tmp / f'renders/old/{name}{suffix}.png', tmp / f'renders/new/{name}{suffix}.png'
    evidence['renders'][v] = {'old_render_sha256': sha(a), 'new_render_sha256': sha(b),
                              'psnr_db': psnr(a, b)}
out = pathlib.Path('docs/RESEARCH/ktx2-v4')
(out / 'glessner').mkdir(parents=True, exist_ok=True)
(out / 'glessner-v4-ktx2.json').write_text(json.dumps(evidence, indent=1) + '\n', encoding='utf-8')
for v in views:
    shutil.copy(tmp / f'sbs/old/{v}-side-by-side.jpg', out / f'glessner/{v}-old.jpg')
    shutil.copy(tmp / f'sbs/new/{v}-side-by-side.jpg', out / f'glessner/{v}-new.jpg')
shutil.copy(tmp / f'sbs/old/{light_view}-side-by-side.jpg', out / f'glessner/{light_view}-light-old.jpg')
shutil.copy(tmp / f'sbs/new/{light_view}-side-by-side.jpg', out / f'glessner/{light_view}-light-new.jpg')
print(json.dumps({k: evidence[k] for k in ('files', 'textures', 'package')}, indent=1))
print(json.dumps(evidence['renders'], indent=1))
