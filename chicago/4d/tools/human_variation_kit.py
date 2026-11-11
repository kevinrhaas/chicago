#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""T-3412: one shared kit of body and face deltas from pinned CC0 MakeHuman targets.

Every drawn person shares one hm08 body, so before this they shared one face. The axes in
data/humans/variation/axes.json name MakeHuman's own graphical targets (nose length, jaw,
weight, macro age...). This tool carries each target's per-vertex deltas from MakeHuman's
source pose onto the engineering T-pose every web body is bound in, and writes them, sparse
and quantised, over the 14,517 UV-split body vertices of prepared.json:

    assets/humans/web/hm08_variation_kit.bin    reference positions + every axis half
    assets/humans/web/hm08_variation_kit.json   the table of contents the renderer reads

The renderer (renderers/web/js/human-variation.js) maps any LOD's body, garments, hair and
eyes onto those reference vertices at load and adds a person's seeded weights of each axis.

Carrying a delta to the T-pose. prepare() bends the arms and legs of the source pose by a
blend of rigid bone rotations, then scales to metres. The per-vertex linear part of that map
is recovered here as the similarity transform (rotation and scale) that best takes each
source vertex's two-ring neighbourhood onto the same neighbourhood in prepared.json, so a
delta on a straightened arm turns with the arm. No MakeHuman program logic is used.

    python3 tools/human_variation_kit.py            # write the kit
    python3 tools/human_variation_kit.py --check    # rebuild in memory, compare bytes
    python3 tools/human_variation_kit.py --vendor DIR   # copy the targets from a MakeHuman
                                                        # checkout at the pinned commit
"""
import argparse, hashlib, json, pathlib, sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[1]
MH = ROOT / 'assets/authored/humans/makehuman_hm08'
AXES = ROOT / 'data/humans/variation/axes.json'
MANIFEST = MH / 'SOURCE-variation.json'
OUT_BIN = ROOT / 'assets/humans/web/hm08_variation_kit.bin'
OUT_JSON = ROOT / 'assets/humans/web/hm08_variation_kit.json'
PERSONS = ROOT / 'assets/humans/web/hm08_variation_persons.json'  # beside the kit: humans.js reads both from its asset base
FITS = ROOT / 'data/humans/variation/fits'
LOOKS = ROOT / 'data/humans/variation/looks'   # T-3491: complexion, hair, eyes, stature
DRESS = ROOT / 'data/humans/variation'   # T-3506/T-3522: dress_1812_*.json, each person's own dress, hat and hair
RESIDENTS = {'1812': ROOT / 'data/residents_1812', '1835': ROOT / 'data/residents', '1904': ROOT / 'data/residents_1904'}
COMMIT = 'a8bc2d54ff0ac92e78ff71431b1023eda42bf482'
RAW = f'https://raw.githubusercontent.com/makehumancommunity/makehuman/{COMMIT}/makehuman/data/targets/'
REF_UNIT_M = 1e-4      # reference positions: int16 tenths of a millimetre (|x| < 3.2 m)
DELTA_UNIT_M = 1e-5    # deltas: int16 hundredths of a millimetre (|d| < 0.32 m)
DROP_M = 2e-5          # a vertex an axis moves less than 0.02 mm is left out of that half


def target_files(axes):
    files = []
    for a in axes['axes']:
        for k in ('pos', 'neg', 'young', 'old'):
            files += a.get(k, [])
        for o in a.get('options', []):
            files += o
    return sorted(set(files))


def vendor(src_dir, axes):
    """Copy each target named by axes.json from a MakeHuman checkout and record its pin."""
    src = pathlib.Path(src_dir) / 'makehuman/data/targets'
    base = json.loads((MH / 'SOURCE.json').read_text())
    pinned = {r['path']: r for r in base['files']}
    rows = []
    for rel in target_files(axes):
        path = f'makehuman/data/targets/{rel}'
        data = (src / rel).read_bytes()
        if 'explicitly released as CC0' not in data.decode():
            raise SystemExit(f'{rel}: no CC0 header')
        if path in pinned:
            if pinned[path]['sha256'] != hashlib.sha256(data).hexdigest():
                raise SystemExit(f'{rel}: differs from the copy SOURCE.json already pins')
        else:
            dest = MH / path
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(data)
        rows.append({'path': path, 'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data),
                     'url': RAW + rel})
    MANIFEST.write_text(json.dumps({
        'repository': 'https://github.com/makehumancommunity/makehuman', 'commit': COMMIT,
        'asset_license': 'CC0-1.0', 'code_copied': False, 'ticket': 'T-3412',
        'notes': ['Graphical target files only, each carrying its own CC0 header; read by tools/human_variation_kit.py',
                  'Files SOURCE.json already pins (the macro age targets) are listed here again, unchanged, so one manifest names every input of the kit'],
        'files': rows}, indent=1) + '\n')
    print(f'vendored {len(rows)} targets into {MH.relative_to(ROOT)}')


def read_obj(path):
    verts, faces = [], []
    group = ''
    for line in path.read_text().splitlines():
        f = line.split()
        if not f:
            continue
        if f[0] == 'v':
            verts.append([float(x) for x in f[1:4]])
        elif f[0] == 'g':
            group = f[1]
        elif f[0] == 'f' and group == 'body':
            faces.append([int(x.split('/')[0]) - 1 for x in f[1:]])
    return np.array(verts), faces


def read_target(path, n):
    d = np.zeros((n, 3))
    for line in path.read_text().splitlines():
        if not line.strip() or line.lstrip().startswith('#'):
            continue
        i, x, y, z = line.split()
        d[int(i)] = (float(x), float(y), float(z))
    return d


def local_frames(src, posed_by_source, faces):
    """Per source vertex: the similarity (s, R) taking its 2-ring in the source pose to the T-pose."""
    used = sorted(posed_by_source)
    ring = {v: set() for v in used}
    for f in faces:
        for a in f:
            ring[a].update(f)
    two = {v: set().union(*(ring[u] for u in ring[v])) - {v} for v in used}
    width = max(len(s) for s in two.values())
    idx = np.array(used)
    nb = np.full((len(used), width), -1)
    for k, v in enumerate(used):
        row = sorted(two[v]); nb[k, :len(row)] = row
    P = np.zeros((len(src), 3))
    for v, p in posed_by_source.items():
        P[v] = p
    mask = (nb >= 0)[..., None]
    A = (src[np.where(nb >= 0, nb, 0)] - src[idx][:, None]) * mask
    B = (P[np.where(nb >= 0, nb, 0)] - P[idx][:, None]) * mask
    H = np.einsum('kni,knj->kij', A, B)
    U, S, Vt = np.linalg.svd(H)
    D = np.ones((len(used), 3)); D[:, 2] = np.sign(np.linalg.det(np.einsum('kji,klj->kil', Vt, U)))
    R = np.einsum('kji,kj,klj->kil', Vt, D, U)      # R = V diag(D) U^T
    s = (S * D).sum(1) / (A * A).sum((1, 2))
    frames = {}
    for k, v in enumerate(used):
        frames[v] = (s[k], R[k])
    return frames


def build():
    axes = json.loads(AXES.read_text())
    manifest = json.loads(MANIFEST.read_text())
    pins = {r['path']: r for r in manifest['files']}
    src, faces = read_obj(MH / 'makehuman/data/3dobjs/base.obj')
    prepared = json.loads((MH / 'prepared.json').read_text())['meshes'][0]
    positions = np.array(prepared['positions_m'])
    source_of = np.array(prepared['source_vertex_indices'])
    posed = {int(v): positions[k] for k, v in enumerate(source_of)}
    frames = local_frames(src, posed, faces)
    # prepare() scales uniformly; only its rotations blend, so one scale serves every vertex
    # (a 2-ring's own fit wanders +-10 % where the bend shears it).
    S = np.full(len(source_of), float(np.median([s for s, _ in frames.values()])))
    R = np.array([frames[int(v)][1] for v in source_of])

    cache = {}

    def delta(files):
        total = np.zeros((len(src), 3))
        for rel in files:
            path = f'makehuman/data/targets/{rel}'
            if path not in pins:
                raise SystemExit(f'{rel}: not pinned in {MANIFEST.name}; run --vendor')
            if path not in cache:
                data = (MH / path).read_bytes()
                if hashlib.sha256(data).hexdigest() != pins[path]['sha256']:
                    raise SystemExit(f'{rel}: checksum differs from its pin')
                cache[path] = read_target(MH / path, len(src))
            total += cache[path]
        # into the T-pose, metres, over the UV-split vertices
        return S[:, None] * np.einsum('kij,kj->ki', R, total[source_of])

    chunks, offset = [], 0

    def put(arr):
        nonlocal offset
        b = arr.tobytes(); start = offset
        chunks.append(b); offset += len(b)
        return start

    ref = np.round(positions / REF_UNIT_M).astype('<i2')
    if np.abs(positions / REF_UNIT_M).max() >= 32767:
        raise SystemExit('reference positions overflow int16')
    # Texture coordinates in glTF's convention (v down), as every web export carries them: a
    # LOD's body vertex is matched to the kit by its UV, which survives the exporter's vertex
    # reordering and the simplifier (positions alone confuse lips and eyelids).
    uvs = np.array(prepared['uvs'])
    uvq = np.round(np.stack([uvs[:, 0], 1 - uvs[:, 1]], 1) * 65535).astype('<u2')
    toc = {'refs': {'offset': put(ref), 'count': len(positions)}, 'uvs': {'offset': put(uvq), 'count': len(uvs)}}

    def half(d):
        n = np.linalg.norm(d, axis=1)
        keep = np.nonzero(n >= DROP_M)[0]
        q = np.round(d[keep] / DELTA_UNIT_M)
        if np.abs(q).max(initial=0) >= 32767:
            raise SystemExit('a delta overflows int16')
        return {'count': int(len(keep)), 'index': put(keep.astype('<u2')), 'delta': put(q.astype('<i2')),
                'max_m': round(float(n.max(initial=0)), 5)}

    out_axes = []
    for a in axes['axes']:
        row = {k: a[k] for k in ('id', 'scope', 'spread', 'drive', 'sex', 'draw_as', 'rest') if k in a}
        row['kind'] = a.get('kind', 'signed')
        if row['kind'] == 'one_of':
            row['options'] = [half(delta(o)) for o in a['options']]
        elif row['kind'] == 'age_macro':
            # old minus young, the three upstream categories equally
            row['pos'] = half((delta(a['old']) - delta(a['young'])) / len(a['old']))
        else:
            row['pos'] = half(delta(a['pos']))
            if 'neg' in a:
                row['neg'] = half(delta(a['neg']))
        out_axes.append(row)
    blob = b''.join(chunks)
    header = {
        'format': 'chicago4d_human_variation_kit_v1', 'ticket': 'T-3412', 'liberty': axes['liberty'],
        'license': 'CC0-1.0', 'generated_by': 'tools/human_variation_kit.py',
        'basis': 'Deltas of pinned CC0 MakeHuman hm08 graphical targets carried onto the engineering T-pose of prepared.json; quantised and sparse. A depiction ingredient, not a measurement of any person.',
        'vertex_count': len(positions), 'ref_unit_m': REF_UNIT_M, 'delta_unit_m': DELTA_UNIT_M,
        'bin': OUT_BIN.name, 'bin_bytes': len(blob), 'bin_sha256': hashlib.sha256(blob).hexdigest(),
        'axes_sha256': hashlib.sha256(AXES.read_bytes()).hexdigest(),
        'manifest_sha256': hashlib.sha256(MANIFEST.read_bytes()).hexdigest(),
        'limit': axes['limit'], 'height': axes['height'], 'age': {k: v for k, v in axes['age'].items() if k != 'basis'},
        'assets': {k: {kk: vv for kk, vv in v.items() if kk != 'basis'} for k, v in axes['assets'].items()},
        **toc, 'axes': out_axes,
    }
    return blob, (json.dumps(header, indent=1) + '\n').encode()


def drawn_people():
    """Every person a figure is drawn for: standing instances and driven loops."""
    out = {}
    for path in sorted((ROOT / 'data/humans/instances').glob('*/hi_*.json')):
        inst = json.loads(path.read_text())
        if inst.get('person_id'):
            out.setdefault(inst['person_id'], {'scene': str(inst['scene']), 'drawn_as': []})['drawn_as'].append(str(path.relative_to(ROOT)))
    loops = json.loads((ROOT / 'data/transport/driven/loops.json').read_text())
    for row in loops.get('rows', []):
        if row.get('person_id'):
            out.setdefault(row['person_id'], {'scene': str(row['scene']), 'drawn_as': []})['drawn_as'].append(f"data/transport/driven/loops.json#{row['id']}")
    # Carded people drawn only when asked for at their door (T-3500): their figure is built
    # then, from the same row as anyone's.
    for scene in RESIDENTS:
        inside = ROOT / f'data/humans/inside_{scene}.json'
        for row in json.loads(inside.read_text()).get('people', []) if inside.exists() else []:
            out.setdefault(row['person'], {'scene': scene, 'drawn_as': []})['drawn_as'].append(f"data/humans/inside_{scene}.json#{row['person']}")
    for path in sorted(FITS.glob('*.json')) if FITS.exists() else []:
        fit = json.loads(path.read_text())
        # A fitted face is carried for the person whether or not a figure draws them yet.
        out.setdefault(fit['person_id'], {'scene': str(fit['scene']), 'drawn_as': []})
    # Former residents keep their researched appearance on the card, without an actor
    # in a year in which they no longer lived here.
    prairie = ROOT / 'data/humans/prairie_1904.json'
    if prairie.exists():
        for row in json.loads(prairie.read_text())['people']:
            if row.get('asset_id'):
                out.setdefault(row['person'], {'scene': '1904', 'drawn_as': []})
    return out


def person_record(pid, scene):
    people = json.loads((ROOT / f'data/sidecars/{scene}/people.json').read_text())
    rows = people['people'] if isinstance(people, dict) else people
    row = next((r for r in rows if r['id'] == pid), None)
    if row is None:
        raise SystemExit(f'{pid}: not in data/sidecars/{scene}/people.json')
    hh = json.loads((RESIDENTS[scene] / row['file']).read_text())
    return next(p for p in hh['persons'] if p['id'] == pid), row['file']


_DRESSES = None


def dresses():
    global _DRESSES
    if _DRESSES is None:
        # T-3522: every dress file of the scene (the camps T-3506, the townspeople T-3522, and any
        # later one), sorted; a person dressed by two files is refused, not silently overlaid.
        _DRESSES = {}
        for f in sorted(DRESS.glob('dress_[0-9][0-9][0-9][0-9]_*.json')):
            for pid, rec in json.loads(f.read_text())['persons'].items():
                if pid in _DRESSES:
                    raise SystemExit(f'{pid} is dressed by two files ({f.name} and another dress file)')
                _DRESSES[pid] = rec
    return _DRESSES


def persons():
    """Age and sex of each drawn person as their own record states them, and any fitted face."""
    out = {}
    for pid, drawn in sorted(drawn_people().items()):
        person, file = person_record(pid, drawn['scene'])
        year = int(drawn['scene'])
        rec = {'scene': drawn['scene'], 'record': f"{RESIDENTS[drawn['scene']].relative_to(ROOT)}/{file}", 'drawn_as': drawn['drawn_as']}
        born = person.get('born') or {}
        band = person.get('age_band') or {}
        if str(born.get('value', ''))[:4].isdigit():
            b = int(str(born['value'])[:4])
            # The scene is 1 July; a birthday later in the year is not yet reached. A year
            # alone is read as the middle of it.
            rec['age'] = {'years': year - b - (1 if str(born['value'])[5:7] > '06' else 0) if len(str(born['value'])) >= 7 else year - b,
                          'grade': born.get('confidence', 'inferred'), 'sources': born.get('sources', []),
                          'basis': f"born {born['value']} (the person's record)"}
        elif isinstance(band.get('low'), int) and isinstance(band.get('high'), int):
            rec['age'] = {'band': [band['low'], band['high']], 'grade': band.get('tier', band.get('confidence', 'reconstructed')),
                          'basis': f"age band {band['value']} (the person's record); the year inside it is seeded"}
        if person.get('sex') in ('male', 'female'):
            rec['sex'] = person['sex']
        fit = FITS / f'{pid}.json'
        if fit.exists():
            f = json.loads(fit.read_text())
            rec['face'] = {k: f[k] for k in ('grade', 'sources', 'basis', 'values', 'liberty', 'not_modelled', 'card') if f.get(k) is not None}
            rec['face']['fit'] = str(fit.relative_to(ROOT))
        looks = LOOKS / f'{pid}.json'
        if looks.exists():
            lk = json.loads(looks.read_text())
            rec['looks'] = {k: lk[k] for k in ('complexion', 'hair', 'eyes', 'stature', 'height_scale', 'build', 'heritage', 'basis',
                                               'reference', 'grade', 'liberty') if lk.get(k) is not None}
            rec['looks']['heritage'] = {'origin': lk['heritage']['origin']}
            rec['looks']['file'] = str(looks.relative_to(ROOT))
        dress = dresses().get(pid)
        if dress:
            # T-3506: their own cloth colours and pieces worn, and their hair's tie and colour.
            rec['dress'] = {k: dress[k] for k in ('colours', 'hide', 'pieces', 'hat', 'worn', 'garrison') if dress.get(k)}
            rec['dress']['grade'] = 'reconstructed'
            # T-3522: a townsperson's handkerchief round the head is their dress's, not their hair's.
            if isinstance(dress.get('headcloth'), list):
                rec['dress']['headcloth'] = dress['headcloth']
            hair = dress.get('hair') or {}
            if hair.get('tail_cm'):
                rec['dress']['tail_cm'] = hair['tail_cm']
            if hair.get('headcloth'):
                rec['dress']['headcloth'] = hair['headcloth']['rgb']
            if rec.get('looks', {}).get('hair'):
                rec['looks']['hair'] = {**rec['looks']['hair'], **{k: hair[k] for k in ('cut', 'drawn') if hair.get(k)}}
        out[pid] = rec
    return (json.dumps({'format': 'chicago4d_human_variation_persons_v1', 'ticket': 'T-3412',
                        'generated_by': 'tools/human_variation_kit.py',
                        '_doc': 'Each drawn person\'s age (from their own record: a birth date, else an age band), any face fitted to a picture of them, and any looks (complexion, hair, eyes, stature; T-3491). renderers/web/js/human-variation.js seeds everything else from the person id. Regenerate; never edit by hand.',
                        'persons': out}, indent=1) + '\n').encode()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--check', action='store_true')
    ap.add_argument('--vendor', metavar='MAKEHUMAN_CHECKOUT')
    args = ap.parse_args()
    if args.vendor:
        vendor(args.vendor, json.loads(AXES.read_text()))
        return 0
    blob, header = build()
    people = persons()
    if args.check:
        bad = [p.relative_to(ROOT) for p, b in ((OUT_BIN, blob), (OUT_JSON, header), (PERSONS, people)) if not p.exists() or p.read_bytes() != b]
        if bad:
            print('FAIL human variation kit is stale:', *bad, '— run python3 tools/human_variation_kit.py')
            return 1
        print(f'ok human variation kit reproduces ({len(blob)} bytes, {len(json.loads(header)["axes"])} axes)')
        return 0
    OUT_BIN.write_bytes(blob)
    OUT_JSON.write_bytes(header)
    PERSONS.write_bytes(people)
    print(f'wrote {OUT_BIN.relative_to(ROOT)} ({len(blob)} bytes) and {OUT_JSON.name}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
