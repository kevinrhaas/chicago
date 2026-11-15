#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""T-3553: a library of faces for the people who have no pictures of their own.

Every drawn person wore one of three skin atlases, so every face had the same lips, lids and
lines under its own shape and complexion. The owner, 2026-11-14, asked for "a library with
variations that will work" and chose "MakeHuman skins only for now": the CC0 skin atlases
MakeHuman and its community publish, no photographs of anybody.

Every hm08 body shares one map, so the face lies at one place on it in every atlas. This tool
cuts that place out of each chosen atlas (data/humans/variation/face_library.json `faces`),
brings each cut to one tone where it meets the skin around it, and lays them side by side:

    assets/authored/humans/face_library/faces/<id>.png   each face as cut, unchanged (--ingest)
    assets/authored/humans/face_library/SOURCE.json      where each atlas came from, and its licence
    assets/humans/web/faces/hm08_faces.jpg               the sheet the app reads

and writes into the record's `texture` what the app needs: each face's place on the sheet and
its own measured tone, and for each body the tone of its own skin and what a face is
multiplied by to meet it. tools/human_variation_kit.py carries that to the kit;
renderers/web/js/human-variation.js hands the faces out (libraryFace) and human-skin.js draws
one under its wearer's complexion (FACE_LIBRARY).

    python3 tools/face_library.py                   # build the sheet and the record's `texture`
    python3 tools/face_library.py --check           # the cuts, the sheet and the record hold
    python3 tools/face_library.py --self-test       # ...and the check refuses a broken copy of them
    python3 tools/face_library.py --ingest PACK=DIR [PACK=DIR ...]
        # authoring, once per atlas: DIR holds PACK's files at their paths in the pack
        # (an unpacked ZIP, or the entries fetched by range); cuts the faces and pins them
    python3 tools/face_library.py --preview OUT.jpg # the faces upright, named, for a look
"""
import argparse, collections, hashlib, io, json, math, pathlib, re, struct, sys, zlib

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[1]
RECORD = ROOT / 'data/humans/variation/face_library.json'
AUTHORED = ROOT / 'assets/authored/humans/face_library'
SOURCE = AUTHORED / 'SOURCE.json'
WEB = ROOT / 'assets/humans/web'
SHEET = WEB / 'faces/hm08_faces.jpg'
LOOKS_JS = ROOT / 'renderers/web/js/human-looks.js'
SKIN_JS = ROOT / 'renderers/web/js/human-skin.js'
REFERENCE = ROOT / 'assets/authored/humans/skin_toigo_bronze/young_lightskinned_male_diffuse_Bronze.png'
AXES = ROOT / 'data/humans/variation/axes.json'   # each body's sex (`assets`), for a person's tone
LUMA = np.array([0.2126, 0.7152, 0.0722])
RING = (0.05, 0.95)     # where a face meets the skin around it: the mask between these
INSIDE = 0.95           # a face's own tone is measured where the mask is at least this
TOLERANCE = 0.01        # a tone or a gain measured again may differ by this share (JPEG decoders differ)
SHEET_TOLERANCE = 1.5   # ...and each tile of the sheet decoded, from that tile built again and put through the same
                        # JPEG, by this (mean, of 255): the sheet as kept reads 0 here; another JPEG library's
                        # rounding is a fraction of one; a tile moved two pixels sideways reads 2.3, three 2.9
SHEET_MEAN = 0.75       # ...and the whole sheet by this: a change over all of it (2 percent darker reads 3)
SHEET_WORST = 16        # ...and no tile's worst thousandth of values by more than this (of 255): a mean over a tile
                        # cannot see a small repaint (a 24 px square painted 120 lighter read 1.0, under the 1.5);
                        # two JPEG libraries differ by a level or two a value
SHEET_BLOCK = 3         # ...and no 8 px block of a tile, in its mean, by more than this (of 255): the worst
                        # thousandth of a 256 px tile is 197 values, and a repaint of 64 px or fewer is 192, so an
                        # 8 px square painted 120 lighter read 1 there; here it reads 30 off the JPEG's grid and
                        # 120 on it. The sheet stored a second time reads 0.5.
BLOCK_PX = 8
# What these four still pass, measured 2026-11-15, and nothing here looks for: one face half a
# part in a hundred darker (mean 1.0, block 2.3); a face softened by a blur of radius 1 (mean
# 0.5, worst thousandth 10, block 1.4); a plain face blended halfway to a freckled one that is
# near it (mean 1.0, worst thousandth 8, block 2.8). Nearer than that a change cannot be told
# from another JPEG library's reading by these measures. The readings are of Pillow's own
# decoder and encoder (libjpeg-turbo, the slow integer transform), which read alike in every
# build tried on 2026-11-15. Under the fast or the floating transform three of --self-test's
# cases that must pass (two rows of faces a level darker, one face half a part in a hundred
# darker, a blur of radius 1) read 3.1 to 3.2 in their worst block, a little over its bound.
SAME_PAINTING = 2.4     # two cuts nearer than this inside the mask (mean, of 255) are one painting: three skins left
                        # out for it read 0.5, 2.3 and 2.0 against a kept one; the nearest two kept read 2.6
LICENCE_LINE = re.compile(r'licen[sc]e|copyright|AGPL|GPL|CC0|CC-BY', re.I)
# What --ingest writes as a face's licence evidence, and --check holds a row to.
EVIDENCE_MATERIAL = 'its material file\'s header: "This asset was explicitly released as CC0 in september 2020. ... The copyright holders at the point of the release to CC0 were: Data Collection AB, Joel Palmius, Jonas Hauquier."'


def evidence_pack(kept_name):
    return f"the pack's own record of the asset in {kept_name} (\"license\": \"CC0\"); its material file is not kept and not used"


def cut_change(width, record):
    """What --ingest writes as done to a cut, by the width of the atlas it was cut from."""
    return 'none: the pixels of the box, as the atlas has them' if width == record['map_px'] else f"the box of a {width} px atlas, resampled to its size on a {record['map_px']} px map"


# SOURCE.json's account of itself, as --ingest writes it.
SOURCE_SAYS = {
    'ticket': 'T-3553',
    'what': "The face of each CC0 MakeHuman skin atlas the face library uses (data/humans/variation/face_library.json), cut from the same box of the hm08 map, and where each atlas came from. The atlases themselves are not kept: each is pinned here by size, CRC-32 and SHA-256 and can be fetched again from its pack.",
    'uv_check': 'Every atlas is laid out on the hm08 base mesh\'s own map, as the three atlases the bodies wear are; each cut was looked at upright (tools/face_library.py --preview) and on built figures.',
}

PACKS = {
    'makehuman_system_assets': {
        'url': 'https://files2.makehumancommunity.org/asset_packs/makehuman_system_assets/makehuman_system_assets_cc0.zip',
        'page': "https://files2.makehumancommunity.org/asset_packs/makehuman_system_assets/ (MakeHuman's own system assets, released CC0)",
        'archive_bytes': 280737770, 'etag': '"10bbb7ea-6160e7c0d7996"', 'archive_sha256': None,
        'fetched': "2026-11-14: the pack's directory and each chosen entry by HTTP range, each entry's size and CRC-32 checked against the directory",
        'licence_evidence': 'the header of each atlas\'s material file, kept unchanged in materials/: "This asset was explicitly released as CC0 in september 2020."',
        'record': "packs/makehuman_system_assets.json, the pack's own list of what it holds, kept as makehuman_system_assets.original.json",
    },
    'skins01': {
        'url': 'https://files2.makehumancommunity.org/asset_packs/skins01/skins01_cc0.zip',
        'page': 'https://files2.makehumancommunity.org/asset_packs/skins01/ ("Natural female skins, shared under CC0")',
        'archive_bytes': 104227958, 'etag': '"6366476-6160e7f028bce"', 'archive_sha256': '7495ab99287053bd19ff1636114e64b608994d9f7437fea6cc75ea387f96dba9',
        'fetched': '2026-11-14: the whole pack, hashed, unpacked',
        'licence_evidence': "the pack's own record of each asset (packs/skins01.json, kept as skins01.original.json): \"license\": \"CC0\"",
    },
    'skins02': {
        'url': 'https://files2.makehumancommunity.org/asset_packs/skins02/skins02_cc0.zip',
        'page': 'https://files2.makehumancommunity.org/asset_packs/skins02/ ("Natural male skins, shared under CC0")',
        'archive_bytes': 76112708, 'etag': '"4896344-6160e7915e6c0"', 'archive_sha256': '1613f1ef3afca53094511d26620ed7cf1d2dedc29ed3d384d60bdebe250698ae',
        'fetched': '2026-11-14: the whole pack, hashed, unpacked',
        'licence_evidence': "the pack's own record of each asset (packs/skins02.json, kept as skins02.original.json): \"license\": \"CC0\"",
    },
}


def sha(b):
    return hashlib.sha256(b).hexdigest()


def linear(srgb8):
    c = np.asarray(srgb8, float) / 255
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def srgb8(lin):
    c = np.clip(lin, 0, 1)
    return np.round(np.where(c <= 0.0031308, c * 12.92, 1.055 * c ** (1 / 2.4) - 0.055) * 255).astype(np.uint8)


def mask_over(record, px):
    """The library's mask over the face's box, `px` square: 1 where the face is whole."""
    u0, v0, u1, v1 = box_uv(record)
    m = record['mask']
    u = u0 + (np.arange(px) + 0.5) / px * (u1 - u0)
    v = v0 + (np.arange(px) + 0.5) / px * (v1 - v0)
    U, V = np.meshgrid(u, v)
    r = m['round']
    qx, qy = np.abs(U - m['centre'][0]) - (m['half'][0] - r), np.abs(V - m['centre'][1]) - (m['half'][1] - r)
    d = np.hypot(np.maximum(qx, 0), np.maximum(qy, 0)) + np.minimum(np.maximum(qx, qy), 0) - r
    t = np.clip((d + m['feather']) / m['feather'], 0, 1)
    return 1 - t * t * (3 - 2 * t)


def box_uv(record):
    return [p / record['map_px'] for p in record['box_px']]


def tones(lin, mask):
    """A face's colour where it meets the skin round it, and its own tone inside (linear RGB)."""
    ring = (mask > RING[0]) & (mask < RING[1])
    return lin[ring].mean(0), lin[mask >= INSIDE].mean(0)


def image():
    try:
        from PIL import Image
    except ImportError:
        return None
    return Image


def cut_of(Image, im, record):
    """The face's box of an atlas of any square size, at the box's own size on a 2048 map."""
    x0, y0, x1, y1 = record['box_px']
    s = im.size[0] / record['map_px']
    if im.size[0] != im.size[1]:
        raise SystemExit(f'an atlas is not square: {im.size}')
    c = im.convert('RGB').crop(tuple(round(p * s) for p in (x0, y0, x1, y1)))
    return c if s == 1 else c.resize((x1 - x0, y1 - y0), Image.LANCZOS)


def glb_skin(path):
    """The bytes of a web body's skin map (its `skin` material's base colour image)."""
    b = path.read_bytes()
    n = struct.unpack('<I', b[12:16])[0]
    doc = json.loads(b[20:20 + n])
    mat = next((m for m in doc['materials'] if m['name'].split('__')[0] == 'skin'), None)
    tex = (mat or {}).get('pbrMetallicRoughness', {}).get('baseColorTexture')
    if tex is None:
        return None
    view = doc['bufferViews'][doc['images'][doc['textures'][tex['index']]['source']]['bufferView']]
    at = 28 + n + view.get('byteOffset', 0)
    return b[at:at + view['byteLength']]


def complexions():
    """The complexion tints the app multiplies a skin by (human-looks.js COMPLEXION_TINT), read from it."""
    js = LOOKS_JS.read_text()
    block = re.search(r'export const COMPLEXION_TINT = Object\.freeze\(\{(.*?)\n\}\);', js, re.S)
    if not block:
        raise SystemExit('renderers/web/js/human-looks.js: COMPLEXION_TINT not found as this tool reads it')
    out = {k: [float(x) for x in v.split(',')] for k, v in re.findall(r'^\s*(\w+): Object\.freeze\(\[([^\]]+)\]\)', block.group(1), re.M)}
    if len(out) < 5:
        raise SystemExit('renderers/web/js/human-looks.js: COMPLEXION_TINT read short')
    return out


_BODY_TONES = {}    # a body's skin read once a run, by its bytes and the box and mask it is read under


def build(record):
    """The sheet's bytes and the record's `texture`. Needs Pillow."""
    Image = image()
    if Image is None:
        raise SystemExit('tools/face_library.py needs Pillow to build the sheet')
    tile, cols, head = record['tile_px'], record['cols'], record['headroom']
    faces = record['faces']
    rows = math.ceil(len(faces) / cols)
    full = record['box_px'][2] - record['box_px'][0]
    m_full, m_tile = mask_over(record, full), mask_over(record, tile)
    ref_ring, _ = tones(linear(np.asarray(cut_of(Image, Image.open(REFERENCE), record))), m_full)
    sheet = np.zeros((rows * tile, cols * tile, 3), np.uint8)
    listed = []
    for i, f in enumerate(faces):
        cut = Image.open(AUTHORED / 'faces' / f"{f['id']}.png").convert('RGB')
        ring, inside = tones(linear(np.asarray(cut)), m_full)
        small = linear(np.asarray(cut.resize((tile, tile), Image.LANCZOS)))
        # Brought to the reference skin's colour where the two meet, with room left above white.
        sheet[(i // cols) * tile:(i // cols + 1) * tile, (i % cols) * tile:(i % cols + 1) * tile] = srgb8(small * (ref_ring / ring) * head)
        listed.append({'id': f['id'], 'sex': f['sex'], 'age': f['age'], 'tone': round(float(inside @ LUMA), 4),
                       **({'light_only': True} if f.get('light_only') else {})})
    out = io.BytesIO()
    Image.fromarray(sheet).save(out, 'JPEG', quality=record['jpeg_quality'], subsampling=0)
    bodies = {}
    for glb in sorted(WEB.glob('*.lod0.glb')):
        raw = glb_skin(glb)
        if raw is None:
            continue
        key = (sha(raw), json.dumps([record['map_px'], record['box_px'], record['mask']], sort_keys=True))
        if key not in _BODY_TONES:
            _BODY_TONES[key] = tones(linear(np.asarray(cut_of(Image, Image.open(io.BytesIO(raw)), record))), m_full)
        ring, inside = _BODY_TONES[key]
        bodies[glb.name[:-len('.lod0.glb')]] = {'gain': [round(float(x), 4) for x in ring / ref_ring / head],
                                                'tone_rgb': [round(float(x), 4) for x in inside]}
    texture = {'file': str(SHEET.relative_to(ROOT)), 'size_px': [cols * tile, rows * tile], 'sha256': sha(out.getvalue()),
               'built_with': built_with(record), 'faces': listed, 'bodies': bodies, 'person_tone': person_tone(bodies),
               'complexions': complexions(),
               'reference': {'file': str(REFERENCE.relative_to(ROOT)), 'meets_rgb': [round(float(x), 4) for x in ref_ring]}}
    return out.getvalue(), texture, sheet


def person_tone(bodies):
    """The skin a person's tone is read from: the one most bodies of their sex wear.

    Not the body the person happens to be drawn on. Three coachmen of 1904 are drawn on two
    bodies, as the driver of a carriage and at their own door, and a tone read from the body
    gave one of them two faces. A body's sex is the kit's (`axes.json` assets; one it does not
    list is a man's, as the app takes it); a body for either sex counts for neither.
    """
    sexes = {k: v.get('sex', 'male') for k, v in json.loads(AXES.read_text())['assets'].items()}
    out = {}
    for sex in ('male', 'female'):
        count = collections.Counter(tuple(b['tone_rgb']) for k, b in bodies.items() if sexes.get(k, 'male') == sex)
        top = count.most_common(2)
        if not top or (len(top) > 1 and top[0][1] == top[1][1]):
            raise SystemExit(f"no one skin is worn by most {sex} bodies: say in the record which a person's tone is read from")
        out[sex] = {'tone_rgb': list(top[0][0]), 'bodies': top[0][1], 'of': sum(count.values())}
    return out


def built_with(record):
    """The editorial figures a sheet is built from: a change to one wants the sheet built again."""
    return {**{k: record[k] for k in ('map_px', 'box_px', 'tile_px', 'cols', 'headroom', 'jpeg_quality')},
            'mask': {k: record['mask'][k] for k in ('centre', 'half', 'round', 'feather')}}


def listed_of(faces):
    """Who may wear each face, as the editorial list or the built one has it."""
    return [{'id': f['id'], 'sex': f['sex'], 'age': f['age'], 'light_only': bool(f.get('light_only'))} for f in faces]


def kit_block(record=None):
    """What the kit carries of the library for the app (tools/human_variation_kit.py), or None."""
    record = record or (json.loads(RECORD.read_text()) if RECORD.exists() else None)
    t = (record or {}).get('texture')
    if not t:
        return None
    r = record['rule']
    return {'map': str((ROOT / t['file']).relative_to(WEB)), 'size_px': t['size_px'], 'tile_px': record['tile_px'], 'cols': record['cols'],
            'box': box_uv(record), 'mask': {k: record['mask'][k] for k in ('centre', 'half', 'round', 'feather')},
            'ages': r['ages'], 'lines': r['lines'], 'younger_likelier': r['younger_likelier'], 'nearer_tone_likelier': r['nearer_tone_likelier'], 'never_darker_than': r['never_darker_than'],
            'light_only_for': r['light_only_for'], 'seed': r['seed'], 'liberty': record['liberty'],
            'faces': t['faces'], 'bodies': t['bodies'], 'complexions': t['complexions'],
            **({'person_tone_rgb': {sex: v['tone_rgb'] for sex, v in t['person_tone'].items()}} if t.get('person_tone') else {})}


def crc_of(path):
    return zlib.crc32(path.read_bytes()) & 0xffffffff


def pinned(record, pin):
    """The record with SOURCE.json's hash beside its path. Only --ingest writes either.

    SOURCE.json is what --ingest read in the packs: an atlas's size and CRC-32 there, the
    pack's own row for it, the licence lines of its material file. Most of that has nothing
    in the repository to be compared with, so the record pins the file as --ingest wrote it,
    and building the sheet does not take the pin again (it did, for a day: a SOURCE.json
    changed by hand was then made good by the command its refusal named).
    """
    out = {}
    for k, v in record.items():
        if k != 'source_sha256':
            out[k] = v
        if k == 'sources':
            out['source_sha256'] = pin
    return out


def ingest(record, pairs):
    Image = image()
    if Image is None:
        raise SystemExit('tools/face_library.py --ingest needs Pillow')
    dirs = dict(p.split('=', 1) for p in pairs)
    # Rows of a pack not named here are carried over from the SOURCE.json that is there: only
    # from one --ingest wrote, or a changed row would be pinned as if it had been read in a pack.
    if SOURCE.exists() and record.get('source_sha256') not in (None, sha(SOURCE.read_bytes())) and not ({f['pack'] for f in record['faces']} | set(PACKS)) <= set(dirs):
        raise SystemExit(f"{SOURCE.relative_to(ROOT)} is not the one --ingest last wrote (the record's `source_sha256`): name every pack's DIR, so that no row is carried over from it")
    source = json.loads(SOURCE.read_text()) if SOURCE.exists() else {'faces': {}}
    (AUTHORED / 'faces').mkdir(parents=True, exist_ok=True)
    (AUTHORED / 'materials').mkdir(parents=True, exist_ok=True)
    for f in record['faces']:
        if f['pack'] not in dirs:
            continue
        root = pathlib.Path(dirs[f['pack']])
        entry = f['entry']
        if entry.endswith('/None'):
            # A community atlas is named by its material file: find the diffuse texture it names.
            folder = root / pathlib.Path(entry).parent
            mh = next(folder.glob('*.mhmat'))
            tex = next(line.split(None, 1)[1].strip() for line in mh.read_text(errors='replace').splitlines() if line.startswith('diffuseTexture'))
            entry = f"{pathlib.Path(entry).parent}/{tex}"
            f['entry'] = entry
        atlas = root / entry
        raw = atlas.read_bytes()
        im = Image.open(io.BytesIO(raw))
        cut = cut_of(Image, im, record)
        out = AUTHORED / 'faces' / f"{f['id']}.png"
        cut.save(out, 'PNG', optimize=True)
        row = {'pack': f['pack'], 'entry': {'path': entry, 'size': len(raw), 'crc32': zlib.crc32(raw) & 0xffffffff, 'sha256': sha(raw),
                                            'image': {'width': im.size[0], 'height': im.size[1], 'mode': im.mode}, 'kept_in_repo': False},
               'cut': {'file': str(out.relative_to(AUTHORED)), 'box_px': record['box_px'], 'of_map_px': record['map_px'], 'sha256': sha(out.read_bytes()),
                       'change': cut_change(im.size[0], record)}}
        if f.get('material'):
            mh = root / f['material']
            kept = AUTHORED / 'materials' / mh.name
            kept.write_bytes(mh.read_bytes())
            row['material'] = {'path': f['material'], 'sha256': sha(mh.read_bytes()), 'kept_in_repo': str(kept.relative_to(AUTHORED)) + ' (unchanged)'}
            row['license'] = 'CC0-1.0'
            row['license_evidence'] = EVIDENCE_MATERIAL
            if 'explicitly released as CC0' not in mh.read_text(errors='replace'):
                raise SystemExit(f'{mh}: no CC0 statement in its header')
        else:
            pack_json = root / 'packs' / f"{f['pack']}.json"
            kept = AUTHORED / f"{f['pack']}.original.json"
            kept.write_bytes(pack_json.read_bytes())
            meta = json.loads(pack_json.read_text())[f['pack_record']]
            if meta.get('license') != 'CC0':
                raise SystemExit(f"{f['id']}: the pack records its licence as {meta.get('license')!r}")
            row['pack_record'] = {'key': f['pack_record'], 'in': kept.name, 'sha256': sha(pack_json.read_bytes()),
                                  **{k: meta[k] for k in ('author', 'license', 'source', 'description', 'created', 'changed') if k in meta}}
            row['license'] = 'CC0-1.0'
            row['license_evidence'] = evidence_pack(kept.name)
            # ...but it is read: a licence line of its own that is not the pack's is a disagreement
            # between two statements about one asset, and is recorded with why CC0 is still read.
            mh = next((root / pathlib.Path(entry).parent).glob('*.mhmat'), None)
            lines = [l.strip() for l in mh.read_text(errors='replace').splitlines() if LICENCE_LINE.search(l)] if mh else []
            row['pack_material'] = {'path': str(mh.relative_to(root)) if mh else None, 'sha256': sha(mh.read_bytes()) if mh else None,
                                    'kept_in_repo': False, 'licence_lines': lines}
            if lines:
                if not f.get('licence_note'):
                    raise SystemExit(f"{f['id']}: its material file in the pack carries a licence line of its own ({lines[0]!r}); give the face a `licence_note` in the record saying why CC0 is still read, or leave it out")
                row['licence_note'] = f['licence_note']
                # What the note rests on is kept beside the cuts, so the note can be read against it.
                ev = f.get('licence_note_evidence')
                if ev:
                    if ev['pack'] not in dirs:
                        raise SystemExit(f"{f['id']}: its licence note cites {ev['path']} of {ev['pack']}: name that pack's DIR too")
                    raw_ev = (pathlib.Path(dirs[ev['pack']]) / ev['path']).read_bytes()
                    if ev['says'].encode() not in raw_ev:
                        raise SystemExit(f"{f['id']}: {ev['path']} does not say {ev['says']!r}")
                    (AUTHORED / 'evidence').mkdir(exist_ok=True)
                    kept_ev = AUTHORED / 'evidence' / pathlib.Path(ev['path']).name
                    kept_ev.write_bytes(raw_ev)
                    row['licence_note_evidence'] = {**ev, 'sha256': sha(raw_ev), 'kept_in_repo': str(kept_ev.relative_to(AUTHORED)) + ' (unchanged)'}
        source['faces'][f['id']] = row
        print('cut', f['id'], out.stat().st_size)
    # Each pack's own record of what it holds, kept unchanged and pinned: the count of skins rests on them.
    records = dict(source.get('pack_records', {}))
    for pack in PACKS:
        if pack in dirs:
            raw_record = (pathlib.Path(dirs[pack]) / 'packs' / f'{pack}.json').read_bytes()
            (AUTHORED / f'{pack}.original.json').write_bytes(raw_record)
            records[pack] = {'in': f'{pack}.original.json', 'sha256': sha(raw_record)}
    out_of = sum(len(row['skins']) for row in record.get('left_out', {}).get('skins', []))
    source = {
        'ticket': SOURCE_SAYS['ticket'],
        'what': SOURCE_SAYS['what'],
        'packs': PACKS,
        'uv_check': SOURCE_SAYS['uv_check'],
        'pack_records': records,
        'not_used': f'The other {out_of} skins of these packs, each with its reason in the record\'s `left_out`; and each pack\'s name for an atlas as a fact about its wearer.',
        'faces': {f['id']: source['faces'][f['id']] for f in record['faces'] if f['id'] in source['faces']},
    }
    blob = (json.dumps(source, indent=1) + '\n').encode()
    SOURCE.write_bytes(blob)
    RECORD.write_text(json.dumps(pinned(record, sha(blob)), indent=1) + '\n')


def check(record):
    bad = []
    source = json.loads(SOURCE.read_text()) if SOURCE.exists() else {'faces': {}}
    ids = [f['id'] for f in record['faces']]
    if len(set(ids)) != len(ids):
        bad.append('a face is listed twice')
    for k in sorted(set(source['faces']) - set(ids)):
        bad.append(f"SOURCE.json pins a face {k} the record does not keep: run --ingest")
    # The record names the files this tool reads, and pins SOURCE.json as --ingest wrote it:
    # what that file alone holds of an atlas (its size and CRC-32 in the pack, the licence
    # lines of its material file) has nothing else here to be compared with.
    if record.get('sources') != str(SOURCE.relative_to(ROOT)):
        bad.append(f"the record's `sources` is not {SOURCE.relative_to(ROOT)}, the file this tool reads")
    if record.get('source_sha256') != (sha(SOURCE.read_bytes()) if SOURCE.exists() else None):
        bad.append(f"{SOURCE.relative_to(ROOT)} is not the one --ingest wrote (the record's `source_sha256` pins it): it is written from the unpacked packs by --ingest, not by hand and not by building the sheet")
    # Where each pack is, its size and its hash, are this tool's own figures.
    if source.get('packs') != json.loads(json.dumps(PACKS)):
        bad.append("SOURCE.json's `packs` are not the packs this tool names (address, size, hash): run --ingest")
    if {k: source.get(k) for k in SOURCE_SAYS} != SOURCE_SAYS:
        bad.append("SOURCE.json's account of itself (`ticket`, `what`, `uv_check`) is not in the words this tool writes: run --ingest")
    for f in record['faces']:
        row = source['faces'].get(f['id'])
        cut = AUTHORED / 'faces' / f"{f['id']}.png"
        if not row or not cut.exists():
            bad.append(f"{f['id']}: no cut or no source row: run --ingest")
            continue
        if sha(cut.read_bytes()) != row['cut']['sha256']:
            bad.append(f"{f['id']}: the cut is not the bytes SOURCE.json pins")
        if row['cut']['box_px'] != record['box_px'] or row['entry']['path'] != f['entry'] or row['pack'] != f['pack']:
            bad.append(f"{f['id']}: cut from another box or atlas than the record names: run --ingest")
        if (row['cut'].get('file') != f"faces/{f['id']}.png" or row['cut'].get('of_map_px') != record['map_px']
                or row['cut'].get('change') != cut_change((row['entry'].get('image') or {}).get('width'), record)):
            bad.append(f"{f['id']}: SOURCE.json's row for its cut (the file, the map's size, what was done to it) is not what this tool writes of it: run --ingest")
        # ...and what stands behind its licence there is what the record names for it.
        behind = ({'material': row['material'].get('path')} if row.get('material') else
                  {k: (row.get('pack_record') or {}).get(k) for k in ('key', 'in')})
        named = {'material': f['material']} if f.get('material') else {'key': f.get('pack_record'), 'in': f"{f['pack']}.original.json"}
        if behind != named:
            bad.append(f"{f['id']}: what stands behind its licence in SOURCE.json (a material file, or a row of its pack's own record) is not the one the record names for it: run --ingest")
        if row.get('license') != 'CC0-1.0' or not row.get('license_evidence'):
            bad.append(f"{f['id']}: no CC0 licence evidence")
        elif row['license_evidence'] != (EVIDENCE_MATERIAL if row.get('material') else evidence_pack((row.get('pack_record') or {}).get('in'))):
            bad.append(f"{f['id']}: its licence evidence is not in the words this tool writes for what stands behind it: run --ingest")
        # The evidence itself is read, not only named: a system skin's kept material file says
        # CC0 in its own words; a community skin's row in the pack's kept record does.
        if row.get('material'):
            kept = (AUTHORED / 'materials' / pathlib.Path(row['material']['path']).name).read_bytes()
            if sha(kept) != row['material']['sha256']:
                bad.append(f"{f['id']}: its kept material file changed")
            if b'explicitly released as CC0' not in kept or pathlib.Path(f['entry']).name.encode() not in kept:
                bad.append(f"{f['id']}: its kept material file does not say CC0 of this atlas in its own words")
        elif row.get('pack_record'):
            pr = row['pack_record']
            kept = AUTHORED / pr.get('in', '')
            meta = None
            if not kept.is_file() or sha(kept.read_bytes()) != pr.get('sha256'):
                bad.append(f"{f['id']}: the pack's record it rests on ({pr.get('in')}) is not the bytes SOURCE.json pins")
            else:
                meta = json.loads(kept.read_text()).get(pr.get('key'))
            if meta is not None and (meta.get('license') != 'CC0' or any(meta.get(k) != pr.get(k) for k in ('author', 'source') if k in meta or k in pr)):
                bad.append(f"{f['id']}: the pack's kept record does not say CC0 of it, by the author and source SOURCE.json gives")
            elif meta is None and kept.is_file() and sha(kept.read_bytes()) == pr.get('sha256'):
                bad.append(f"{f['id']}: the pack's kept record has no row {pr.get('key')!r}")
            pm = row.get('pack_material')
            if pm is None:
                bad.append(f"{f['id']}: its material file in the pack was not read for a licence line: run --ingest")
            elif pm.get('licence_lines') and (not row.get('licence_note') or row.get('licence_note') != f.get('licence_note')):
                bad.append(f"{f['id']}: its material file in the pack carries a licence line of its own and no `licence_note` says why CC0 is still read")
            elif not pm.get('licence_lines') and (row.get('licence_note') or f.get('licence_note')):
                bad.append(f"{f['id']}: it has a `licence_note`, and SOURCE.json holds no licence line of its material file for the note to answer: run --ingest")
            # What a note cites is kept, is the bytes pinned, says what the note says it says, and is named in the note by its hash.
            ev, want = row.get('licence_note_evidence'), f.get('licence_note_evidence')
            if f.get('licence_note') and not want:
                bad.append(f"{f['id']}: its licence note cites no kept file (`licence_note_evidence`)")
            if (ev is None) != (want is None) or (ev and {k: ev.get(k) for k in want} != want):
                bad.append(f"{f['id']}: the evidence its licence note cites is not what SOURCE.json holds: run --ingest")
            elif ev:
                kept_ev = AUTHORED / 'evidence' / pathlib.Path(ev['path']).name
                raw_ev = kept_ev.read_bytes() if kept_ev.is_file() else b''
                if sha(raw_ev) != ev.get('sha256') or ev['says'].encode() not in raw_ev:
                    bad.append(f"{f['id']}: the file its licence note cites ({kept_ev.relative_to(ROOT)}) is not kept as pinned, or does not say {ev['says']!r}")
                if ev.get('sha256', '') not in (f.get('licence_note') or ''):
                    bad.append(f"{f['id']}: its licence note does not name the file it cites by its SHA-256")
        else:
            bad.append(f"{f['id']}: neither a kept material file nor a pack record stands behind its licence")
        if f['sex'] not in ('male', 'female') or f['age'] not in ('young', 'middle', 'old'):
            bad.append(f"{f['id']}: sex or age not one the rule knows")
    # Every skin the three packs hold is kept or left out with a reason, by the packs' own records.
    held = {}
    for pack in PACKS:
        kept = AUTHORED / f'{pack}.original.json'
        if not kept.is_file():
            bad.append(f"{kept.relative_to(ROOT)} is missing: the pack's own list of its skins")
            continue
        if sha(kept.read_bytes()) != source.get('pack_records', {}).get(pack, {}).get('sha256'):
            bad.append(f"{kept.relative_to(ROOT)} is not the bytes SOURCE.json pins as the pack's own record: run --ingest")
        if source.get('pack_records', {}).get(pack, {}).get('in') != kept.name:
            bad.append(f"SOURCE.json does not name {kept.name} as {pack}'s own record: run --ingest")
        held[pack] = {k for k, v in json.loads(kept.read_text()).items() if isinstance(v, dict) and v.get('type') in ('skin', 'skins')}
    used = {}
    for f in record['faces']:
        used.setdefault(f['pack'], set()).add(f.get('pack_record') or pathlib.Path(f['entry']).parent.name)
    left = {}
    for row in record.get('left_out', {}).get('skins', []):
        seen = left.setdefault(row['pack'], set())
        for n in row['skins']:
            if n in seen:
                bad.append(f"left_out: {row['pack']}'s skin {n} is listed twice")
            seen.add(n)
        if not row.get('why'):
            bad.append(f"left_out: no reason given for {row['skins']}")
    for pack, names in held.items():
        kept_here, left_here = used.get(pack, set()), left.get(pack, set())
        for n in sorted(names - kept_here - left_here):
            bad.append(f"{pack}: its skin {n} is neither kept nor in the record's left_out")
        for n in sorted((kept_here | left_here) - names):
            bad.append(f"{pack}: the record names a skin {n} the pack's own record does not list")
        for n in sorted(kept_here & left_here):
            bad.append(f"{pack}: {n} is both kept and left out")
    total, out = sum(len(v) for v in held.values()), sum(len(v) for v in left.values())
    said = record.get('left_out', {}).get('basis', '')
    if held and (f'hold {total} skins' not in said or f'other {out} ' not in said or f'{len(ids)} are kept' not in said):
        bad.append(f"left_out.basis does not say what the packs hold ({total} skins, {len(ids)} kept, {out} left out)")
    if f'The other {out} skins' not in source.get('not_used', ''):
        bad.append(f'SOURCE.json `not_used` does not say {out} skins are left out: run --ingest')
    licences = (ROOT / 'assets/LICENSES.md').read_text()
    for p in sorted(AUTHORED.rglob('*')) + [SHEET]:
        if p.is_file() and str(p.relative_to(ROOT / 'assets')) not in licences:
            bad.append(f'assets/LICENSES.md does not list {p.relative_to(ROOT / "assets")}')
    # The register's row for each face names the atlas it was cut from and CC0, and its section the count.
    for f in record['faces']:
        row, line = source['faces'].get(f['id']), next((l for l in licences.splitlines() if f"faces/{f['id']}.png`" in l), '')
        cells = [c.strip() for c in line.split('|')]     # | the file | what it is | its licence, and by what | ...
        if row and (row['entry']['sha256'] not in line or len(cells) < 4 or not re.match(r'CC0-1\.0( |$)', cells[3])):
            bad.append(f"assets/LICENSES.md: the row for faces/{f['id']}.png does not give CC0-1.0 and the atlas's SHA-256 as SOURCE.json has it")
    if held and f"{total} skins can be counted against the {len(ids)} kept and the {out} left out" not in ' '.join(licences.split()):
        bad.append(f"assets/LICENSES.md does not say the packs' {total} skins can be counted against the {len(ids)} kept and the {out} left out")
    # ...and wherever else the register and the folder's own page give the counts.
    flat = ' '.join(licences.split())
    if f"The face of each of {len(ids)} skin atlases" not in flat or f"those {len(ids)} cuts" not in flat:
        bad.append(f"assets/LICENSES.md does not say the folder holds the faces of {len(ids)} skin atlases, {len(ids)} cuts")
    readme = ' '.join((AUTHORED / 'README.md').read_text().split()) if (AUTHORED / 'README.md').is_file() else ''
    if held and (f"the face of each of {len(ids)} more" not in readme or f"{total}, of which {len(ids)} are kept" not in readme or f"other {out} skins" not in readme):
        bad.append(f"{(AUTHORED / 'README.md').relative_to(ROOT)} does not give the counts ({len(ids)} faces; {total} skins, {len(ids)} kept, {out} left out)")
    # The gate may not stand on a banked reading: the readers' register names the step that runs this.
    # (The self-test's step too: without Pillow it skips the cases that read the sheet.)
    gate, readers = (ROOT / 'tools/check.sh').read_text(), (ROOT / 'tools/check_gate_readers.py').read_text()
    for kind, flag, what in (('step', '--check', 'this step'), ('selftest', '--self-test', "the self-test's step")):
        step = re.search(kind + r' "([^"]+)" \\\n\s*python3 tools/face_library\.py ' + flag + r'\n', gate)
        if not step:
            bad.append(f'tools/check.sh does not run {what} (python3 tools/face_library.py {flag})')
        elif readers.count(f'"{step.group(1)}"') < 2:
            bad.append(f'tools/check_gate_readers.py does not name {what} under both Pillow and numpy')
    t = record.get('texture')
    if not t:
        bad.append('no sheet built: run tools/face_library.py')
    else:
        tile, cols = record['tile_px'], record['cols']
        # The app loads the sheet the record names (through the kit): the one measured here.
        if t.get('file') != str(SHEET.relative_to(ROOT)):
            bad.append(f'the record names another sheet than {SHEET.relative_to(ROOT)}, the one this tool writes and measures')
        if (t.get('reference') or {}).get('file') != str(REFERENCE.relative_to(ROOT)):
            bad.append(f'the record names another reference skin than {REFERENCE.relative_to(ROOT)}, the one this tool brings the faces to')
        if not SHEET.exists() or sha(SHEET.read_bytes()) != t['sha256']:
            bad.append(f'{SHEET.relative_to(ROOT)} is not the bytes the record names: run tools/face_library.py')
        if [x['id'] for x in t['faces']] != ids or t['size_px'] != [cols * tile, math.ceil(len(ids) / cols) * tile]:
            bad.append('the sheet was built for another list of faces: run tools/face_library.py')
        elif listed_of(t['faces']) != listed_of(record['faces']):
            bad.append('who may wear a face (sex, age, light_only) changed since the sheet was built: run tools/face_library.py')
        if t.get('built_with') != built_with(record):
            bad.append('the box, mask, tile size, headroom or JPEG quality changed since the sheet was built: run tools/face_library.py')
        if t['complexions'] != complexions():
            bad.append('the complexions changed since the sheet was built: run tools/face_library.py')
        on_disk = sorted(g.name[:-len('.lod0.glb')] for g in WEB.glob('*.lod0.glb') if glb_skin(g) is not None)
        if sorted(t['bodies']) != on_disk:
            bad.append('the bodies changed since the sheet was built: run tools/face_library.py')
        # A person's tone is read from the skin most bodies of their sex wear, as the record holds
        # it (read from the record and the kit's list of bodies: no picture is opened for it).
        try:
            if t.get('person_tone') != person_tone(t['bodies']):
                bad.append("`person_tone` is not the skin most bodies of each sex wear: run tools/face_library.py")
        except SystemExit as e:
            bad.append(str(e))
        if image() is None:
            # Not a pass: tools/check_gate_readers.py names this step, and CI is red without Pillow.
            print('   skip: Pillow is not installed, so the tones, the gains and the sheet were not measured again (check_gate_readers.py names this)')
        elif not bad:
            coded_bytes, again, built = build(record)
            near = lambda a, b: all(abs(x - y) <= TOLERANCE * max(abs(x), abs(y), 0.02) for x, y in zip(a, b))
            for a, b in zip(t['faces'], again['faces']):
                if not near([a['tone']], [b['tone']]):
                    bad.append(f"{a['id']}: its tone is not what the record holds: run tools/face_library.py")
            for k, b in again['bodies'].items():
                if not near(t['bodies'][k]['gain'], b['gain']) or not near(t['bodies'][k]['tone_rgb'], b['tone_rgb']):
                    bad.append(f'{k}: its skin changed since the sheet was built: run tools/face_library.py')
            if len(t['reference'].get('meets_rgb', [])) != 3 or not near(t['reference']['meets_rgb'], again['reference']['meets_rgb']):
                bad.append("the reference skin's colour where a face meets it is not what the record holds: run tools/face_library.py")
            Image = image()
            # No two faces are one painting (the record's `left_out` tells of three that were).
            inside = mask_over(record, record['box_px'][2] - record['box_px'][0]) >= INSIDE
            cuts = {f['id']: np.asarray(Image.open(AUTHORED / 'faces' / f"{f['id']}.png").convert('RGB'), float)[inside] for f in record['faces']}
            for i, a in enumerate(ids):
                for b in ids[i + 1:]:
                    apart = float(np.abs(cuts[a] - cuts[b]).mean())
                    if apart < SAME_PAINTING:
                        bad.append(f'{a} and {b} are one painting (they differ by {apart:.2f} of 255 inside the mask): leave one out, with its reason')
            # The sheet as kept against the sheet built again and put through the same JPEG. Tile by
            # tile (one wrong face is lost in a mean over all of them), and each tile must be nearer
            # its own face built again than any other's: two faces may differ by less than a
            # tolerance can allow, and who may wear each is not the same.
            kept_px = np.asarray(Image.open(SHEET).convert('RGB'), float)
            coded = np.asarray(Image.open(io.BytesIO(coded_bytes)).convert('RGB'), float)
            built = built.astype(float)
            # The sheet keeps its colour at full size, as this tool writes it (a sheet stored
            # again with its colour halved is softer at every lip and lid, and reads within
            # the tolerances below).
            from PIL import JpegImagePlugin
            with Image.open(SHEET) as kept_im:
                if kept_im.format != 'JPEG' or JpegImagePlugin.get_sampling(kept_im) != 0:
                    bad.append("the sheet does not keep its colour at full size (JPEG 4:4:4), as this tool writes it: run tools/face_library.py")
                # ...and carries nothing that tells a reader to turn or recolour it: the measures
                # below read its pixels as stored, and would not see either.
                if kept_im.info.get('icc_profile') or len(kept_im.getexif()):
                    bad.append('the sheet carries a colour profile or EXIF data, which this tool never writes and the measures here do not read: run tools/face_library.py')
            at = lambda px, i: px[(i // cols) * tile:(i // cols + 1) * tile, (i % cols) * tile:(i % cols + 1) * tile]
            if kept_px.shape != coded.shape:
                bad.append('the sheet is not the size the record builds: run tools/face_library.py')
            else:
                if np.abs(kept_px - coded).mean() > SHEET_MEAN:
                    bad.append(f'the sheet as a whole is not the cuts laid out as the record says (mean difference {np.abs(kept_px - coded).mean():.2f} of 255): run tools/face_library.py')
                for i, f in enumerate(record['faces']):
                    signed = at(kept_px, i) - at(coded, i)
                    apart, whole = np.abs(signed), tile // BLOCK_PX * BLOCK_PX
                    err, worst = apart.mean(), float(np.quantile(apart, 0.999))
                    block = float(np.abs(signed[:whole, :whole].reshape(whole // BLOCK_PX, BLOCK_PX, whole // BLOCK_PX, BLOCK_PX, 3).mean((1, 3))).max())
                    # Each on its own: one refusal does not hide another.
                    if err > SHEET_TOLERANCE:
                        bad.append(f"{f['id']}: its tile of the sheet is not its cut laid out as the record says (mean difference {err:.2f} of 255): run tools/face_library.py")
                    if worst > SHEET_WORST:
                        bad.append(f"{f['id']}: a part of its tile of the sheet is not its cut laid out as the record says (its worst thousandth differs by {worst:.0f} of 255): run tools/face_library.py")
                    if block > SHEET_BLOCK:
                        bad.append(f"{f['id']}: a small part of its tile of the sheet is not its cut laid out as the record says (an {BLOCK_PX} px block differs by {block:.1f} of 255 in its mean): run tools/face_library.py")
                    nearest = min(range(len(record['faces'])), key=lambda j: float(((at(kept_px, i) - at(built, j)) ** 2).mean()))
                    if nearest != i:
                        bad.append(f"{f['id']}: its tile of the sheet is nearer {record['faces'][nearest]['id']}'s cut than its own: run tools/face_library.py")
    # The app draws the mask this tool measured under, and reads the kit's block as this tool writes it.
    m = record['mask']
    u0, v0, u1, v1 = box_uv(record)
    js = SKIN_JS.read_text()
    needs = f"FACE_LIBRARY = Object.freeze({{ box: Object.freeze([{u0}, {v0}, {u1}, {v1}]), centre: Object.freeze([{m['centre'][0]}, {m['centre'][1]}]), half: Object.freeze([{m['half'][0]}, {m['half'][1]}]), round: {m['round']}, feather: {m['feather']} }})"
    if needs not in js:
        bad.append(f'renderers/web/js/human-skin.js does not draw the mask this tool measures under: {needs}')
    kit = json.loads((WEB / 'hm08_variation_kit.json').read_text()).get('faces')
    if kit != kit_block(record):
        bad.append('the kit does not carry this library: run python3 tools/human_variation_kit.py')
    for b in bad:
        print('FAIL', b)
    if bad:
        return 1
    print(f"face library: {len(ids)} faces hold, for {len(t['bodies'])} bodies")
    return 0


# What --check reads, for --self-test's copy of it. These are copied, so a case can break
# its own; `LINKED` and every body's *.lod0.glb are only read by any case, and are linked.
COPIED = ('data/humans/variation/face_library.json', 'assets/authored/humans/face_library', 'assets/humans/web/faces/hm08_faces.jpg',
          'assets/humans/web/hm08_variation_kit.json', 'assets/LICENSES.md', 'tools/check.sh', 'tools/check_gate_readers.py',
          'renderers/web/js/human-skin.js')
LINKED = ('data/humans/variation/axes.json', 'renderers/web/js/human-looks.js',
          'assets/authored/humans/skin_toigo_bronze/young_lightskinned_male_diffuse_Bronze.png')


def _rebase(root):
    """Point every path this tool reads at another copy of the tree (--self-test's)."""
    g = globals()
    for k in ('RECORD', 'AUTHORED', 'SOURCE', 'WEB', 'SHEET', 'LOOKS_JS', 'SKIN_JS', 'REFERENCE', 'AXES'):
        g[k] = root / g[k].relative_to(g['ROOT'])
    g['ROOT'] = root


class _Stopped(BaseException):
    """The self-test was told to stop (SIGTERM as `timeout` sends, or SIGHUP): its copy is cleared away first."""


def self_test():
    """Breaks a copy of the library each way the check must refuse, and sees each refused.

    The check passed a broken library more than once before a reviewer broke one on purpose
    (2026-11-14 and 15): two cuts that were one painting, a tile repainted in part, a count in
    the register, a licence note with nothing behind it. Each is a case here, with the plainer
    ones, and each refusal the check can give has a case that draws it. Where the check
    stands on a bound, one case lies a little beyond it and is refused, and where a library
    that is whole could be told from a broken one only by that bound, one lies a little within
    and passes: a bound loosened or tightened by much is seen here. The copy is made in the
    system's temporary folder, which must lie outside the repository, and nothing in the tree
    is written; stopped by SIGTERM or SIGHUP (or from the keyboard), the copy is cleared away
    first; SIGQUIT and SIGKILL leave it in the temporary folder. Without Pillow the cases that
    need the sheet read are skipped, and named, and the last line says how many
    (tools/check_gate_readers.py names this step, so CI is red without it).
    """
    import contextlib, os, shutil, signal, tempfile
    real, Image = ROOT, image()
    # The repository's top: where .git is, or in a tree with none (an export) two folders up
    # from chicago/4d. A copy of this tool's own folders laid out some other way guards itself only.
    top = next((d for d in (real, *real.parents) if (d / '.git').exists()), None)
    if top is None:
        top = real.parents[1] if (real.parent.name, real.name) == ('chicago', '4d') else real
    base = pathlib.Path(tempfile.gettempdir()).resolve()
    if base == top or top in base.parents:
        print(f'FAIL the temporary folder ({base}) is inside the repository ({top}): the self-test would write its copy into the tree; set TMPDIR elsewhere')
        return 1

    def stopped(signum, _frame):
        raise _Stopped(signum)
    before = {s: signal.signal(s, stopped) for s in (signal.SIGTERM, getattr(signal, 'SIGHUP', None)) if s is not None}
    try:
        with tempfile.TemporaryDirectory(prefix='face_library_self_test_') as tmp:
            return _self_test_in(pathlib.Path(tmp), real, Image, contextlib, os, shutil)
    except _Stopped as stop:
        print('   self-test: stopped before its end; its copy is cleared away')
        return 128 + int(stop.args[0])
    finally:
        _rebase(real)
        for s, was in before.items():
            signal.signal(s, was)


def _self_test_in(root, real, Image, contextlib, os, shutil):
    def fresh(rel):
        src, dst = real / rel, root / rel
        if dst.is_dir():
            shutil.rmtree(dst)
        elif dst.exists():
            dst.unlink()
        dst.parent.mkdir(parents=True, exist_ok=True)
        (shutil.copytree if src.is_dir() else shutil.copyfile)(src, dst)

    for src in [real / rel for rel in LINKED] + sorted(WEB.glob('*.lod0.glb')):
        dst = root / src.relative_to(real)
        dst.parent.mkdir(parents=True, exist_ok=True)
        os.symlink(src, dst)
    _rebase(root)
    for rel in COPIED:
        fresh(rel)
    record, source = json.loads(RECORD.read_text()), json.loads(SOURCE.read_text())
    ids, tile, cols = [f['id'] for f in record['faces']], record['tile_px'], record['cols']
    noted = next(f['id'] for f in record['faces'] if f.get('licence_note'))
    freckled = next(f['id'] for f in record['faces'] if f.get('light_only'))
    of_system = next(k for k in ids if source['faces'][k].get('material'))
    of_pack = next(k for k in ids if source['faces'][k].get('pack_record') and k != noted)
    minor = next(k for k in sorted(record['texture']['bodies']) for sex in [json.loads(AXES.read_text())['assets'].get(k, {}).get('sex', 'male')]
                 if sex in ('male', 'female') and record['texture']['bodies'][k]['tone_rgb'] != record['texture']['person_tone'][sex]['tone_rgb'])
    pack = next(iter(PACKS))
    n, out = len(ids), sum(len(row['skins']) for row in record['left_out']['skins'])
    rec, auth, kit, register = 'data/humans/variation/face_library.json', 'assets/authored/humans/face_library', 'assets/humans/web/hm08_variation_kit.json', 'assets/LICENSES.md'
    src = f'{auth}/SOURCE.json'
    body = sorted(record['texture']['bodies'])[0]

    def data(rel, change):
        p = root / rel
        d = json.loads(p.read_text())
        change(d)
        p.write_text(json.dumps(d, indent=1) + '\n')

    def text(rel, old, new):
        p = root / rel
        s = p.read_text()
        if old not in s:
            raise SystemExit(f'self-test: {rel} no longer holds {old!r}; bring the case up to date')
        p.write_text(s.replace(old, new, 1))

    def sourced(change):
        """SOURCE.json changed, and pinned again as it now is: for a case the check must refuse further on."""
        data(src, change)
        data(rec, lambda d: d.__setitem__('source_sha256', sha(SOURCE.read_bytes())))

    def both(change):
        """The record's `texture` and the kit's copy of it changed alike."""
        data(rec, lambda d: change(d['texture']))
        data(kit, lambda d: change(d['faces']))

    def resheet(change=lambda px: px, subsampling=0, **carrying):
        """The sheet decoded, changed, stored again as the tool stores it, and named by the record."""
        px = change(np.asarray(Image.open(SHEET).convert('RGB')).astype(float))
        blob = io.BytesIO()
        Image.fromarray(np.clip(np.rint(px), 0, 255).astype(np.uint8)).save(blob, 'JPEG', quality=record['jpeg_quality'], subsampling=subsampling, **carrying)
        SHEET.write_bytes(blob.getvalue())
        data(rec, lambda d: d['texture'].__setitem__('sha256', sha(blob.getvalue())))

    def place(i):
        return slice((i // cols) * tile, (i // cols + 1) * tile), slice((i % cols) * tile, (i % cols + 1) * tile)

    def swapped(px):
        a, b = px[place(0)].copy(), px[place(1)].copy()
        px[place(0)], px[place(1)] = b, a
        return px

    def square(side, lighter, of=3, channels=slice(None)):
        def change(px):
            rows, across = place(of)
            px[rows.start + 116:rows.start + 116 + side, across.start + 116:across.start + 116 + side, channels] += lighter
            return px
        return change

    def moved(pixels):
        def change(px):
            px[place(3)] = np.roll(px[place(3)], pixels, axis=1)
            return px
        return change

    def halves(px):
        """The upper half a level lighter and the lower a level darker: over the whole sheet, next to nothing."""
        px[:px.shape[0] // 2] += 1
        px[px.shape[0] // 2:] -= 1
        return px

    def turn():
        ex = Image.Exif()
        ex[0x0112] = 3      # Orientation: upside down
        return ex.tobytes()

    def darker(levels):
        def change(px):
            px[place(3)] -= levels
            return px
        return change

    def upper(levels):
        def change(px):
            px[:2 * tile] -= levels
            return px
        return change

    def dimmed(px):
        px[place(3)] *= 0.995
        return px

    def softened(px):
        from PIL import ImageFilter
        soft = Image.fromarray(px[place(3)].astype(np.uint8)).filter(ImageFilter.GaussianBlur(1))
        px[place(3)] = np.asarray(soft, float)
        return px

    def recut(make):
        """The second cut made from the first by `make`, and pinned as it now is."""
        def change():
            px = np.asarray(Image.open(AUTHORED / 'faces' / f'{ids[0]}.png').convert('RGB')).astype(int)
            Image.fromarray(make(px).astype(np.uint8)).save(AUTHORED / 'faces' / f'{ids[1]}.png', 'PNG')
            pin = sha((AUTHORED / 'faces' / f'{ids[1]}.png').read_bytes())
            sourced(lambda d: d['faces'][ids[1]]['cut'].__setitem__('sha256', pin))
        return change

    def near_copy(levels):
        """...`levels` of 255 lighter all over: another file, the same painting or not."""
        return recut(lambda px: np.where(px + levels > 255, px - levels, px + levels))

    def outside(px):
        """...the same inside the mask, where a face is whole, and its negative outside it."""
        return np.where((mask_over(record, px.shape[0]) >= INSIDE)[..., None], px, 255 - px)

    def twice(d):
        row = d['left_out']['skins'][0]
        row['skins'].append(row['skins'][0])

    def turned(d):
        t = d['texture']['person_tone']
        t['male'], t['female'] = t['female'], t['male']

    def alone(sex):
        """One sex's tone changed, the other's as it was."""
        def change(d):
            t = d['texture']['person_tone'][sex]['tone_rgb']
            t[0] = round(t[0] + 0.01, 4)
        return lambda: data(rec, change)

    def tied(d):
        """As many women's bodies on one skin as on another."""
        sexes = {k: v.get('sex', 'male') for k, v in json.loads(AXES.read_text())['assets'].items()}
        bodies = d['texture']['bodies']
        women = [k for k in sorted(bodies) if sexes.get(k, 'male') == 'female']
        count = collections.Counter(tuple(bodies[k]['tone_rgb']) for k in women).most_common()
        (most, many), (other, few) = count[0], count[1]
        if (many - few) % 2:
            bodies.pop(next(k for k in women if tuple(bodies[k]['tone_rgb']) == most))
            many -= 1
        for k in [k for k in women if k in bodies and tuple(bodies[k]['tone_rgb']) == most][:(many - few) // 2]:
            bodies[k]['tone_rgb'] = list(other)

    def unsaid():
        """A kept material file that no longer says CC0, pinned again as it now is."""
        kept = AUTHORED / 'materials' / pathlib.Path(source['faces'][of_system]['material']['path']).name
        kept.write_bytes(kept.read_bytes().replace(b'explicitly released as CC0', b'explicitly released as CC9'))
        sourced(lambda d: d['faces'][of_system]['material'].__setitem__('sha256', sha(kept.read_bytes())))

    def unlicensed():
        """A pack's kept record that says another licence of one cut, pinned again as it now is."""
        pr = source['faces'][of_pack]['pack_record']
        kept = AUTHORED / pr['in']
        d = json.loads(kept.read_text())
        d[pr['key']]['license'] = 'CC-BY'
        kept.write_text(json.dumps(d, indent=1))
        pin = sha(kept.read_bytes())

        def repin(s):
            s['pack_records'][source['faces'][of_pack]['pack']]['sha256'] = pin
            for row in s['faces'].values():
                if (row.get('pack_record') or {}).get('in') == pr['in']:
                    row['pack_record']['sha256'] = pin
        sourced(repin)

    def another_pack(d):
        """One community cut's licence resting on another pack's own record, as SOURCE.json pins that one."""
        mine = d['faces'][of_pack]['pack']
        other = next(k for k in d['pack_records'] if k != mine and any(v['pack'] == k and v.get('pack_record') for v in d['faces'].values()))
        d['faces'][of_pack]['pack_record'].update(d['pack_records'][other])

    def rested(d):
        """One community cut's licence resting on the next one's row of the pack's record."""
        other = next(k for k in ids if k not in (of_pack, noted) and d['faces'][k]['pack'] == d['faces'][of_pack]['pack'])
        d['faces'][of_pack]['pack_record'].update({k: d['faces'][other]['pack_record'][k] for k in ('key', 'author', 'source')})

    def lent(d):
        """One system cut's licence resting on the next one's kept material file."""
        other = next(k for k in ids if k != of_system and d['faces'][k].get('material') and d['faces'][k]['material']['path'] != d['faces'][of_system]['material']['path'])
        d['faces'][of_system]['material'] = dict(d['faces'][other]['material'])

    def unstepped(flag):
        """The gate no longer running this tool with `flag`."""
        def change():
            p = root / 'tools/check.sh'
            lines = p.read_text().split('\n')
            at = next(i for i, l in enumerate(lines) if l.strip() == f'python3 tools/face_library.py {flag}')
            del lines[at - 1:at + 1]
            p.write_text('\n'.join(lines))
        return change

    def everywhere(rel, old, new):
        p = root / rel
        if old not in p.read_text():
            raise SystemExit(f'self-test: {rel} no longer holds {old!r}; bring the case up to date')
        p.write_text(p.read_text().replace(old, new))

    def cited():
        kept = AUTHORED / 'evidence' / pathlib.Path(source['faces'][noted]['licence_note_evidence']['path']).name
        kept.write_bytes(kept.read_bytes() + b' ')

    def material():
        return AUTHORED / 'materials' / pathlib.Path(source['faces'][of_system]['material']['path']).name

    def renamed():
        """A kept material file that says CC0 of another atlas, pinned again as it now is."""
        atlas = pathlib.Path(next(f for f in record['faces'] if f['id'] == of_system)['entry']).name.encode()
        if atlas not in material().read_bytes():
            raise SystemExit(f'self-test: {material().name} no longer names its atlas; bring the case up to date')
        material().write_bytes(material().read_bytes().replace(atlas, b'another_atlas.png'))
        sourced(lambda d: d['faces'][of_system]['material'].__setitem__('sha256', sha(material().read_bytes())))

    def noting(change):
        """The noted face's row changed alike in the record and in SOURCE.json."""
        data(rec, lambda d: change(next(f for f in d['faces'] if f['id'] == noted)))
        data(src, lambda d: change(d['faces'][noted]))

    def unhashed(row):
        row['licence_note'] = row['licence_note'].replace(source['faces'][noted]['licence_note_evidence']['sha256'], 'its hash')

    def kept_and_left(d):
        for row in d['left_out']['skins']:
            name = next((f.get('pack_record') or pathlib.Path(f['entry']).parent.name for f in d['faces'] if f['pack'] == row['pack']), None)
            if name:
                row['skins'].append(name)
                return

    def basis(old, new):
        def change(d):
            if old not in d['left_out']['basis']:
                raise SystemExit(f'self-test: left_out.basis no longer holds {old!r}; bring the case up to date')
            d['left_out']['basis'] = d['left_out']['basis'].replace(old, new, 1)
        return lambda: data(rec, change)

    def reordered(d):
        f = d['texture']['faces']
        f[0], f[1] = f[1], f[0]

    def row_of_register(old, new):
        """The register's row for one cut, with `old` made `new`."""
        def change():
            p = root / register
            lines = p.read_text().split('\n')
            at = next(i for i, l in enumerate(lines) if f'faces/{ids[2]}.png`' in l)
            if old not in lines[at]:
                raise SystemExit(f"self-test: the register's row for faces/{ids[2]}.png no longer holds {old!r}; bring the case up to date")
            lines[at] = lines[at].replace(old, new)
            p.write_text('\n'.join(lines))
        return change
    atlas_hash = source['faces'][ids[2]]['entry']['sha256']

    def gain(share):
        def change(t):
            t['bodies'][body]['gain'] = [round(g * (1 + share), 4) for g in t['bodies'][body]['gain']]
        return lambda: both(change)

    def tone(share):
        def change(t):
            t['faces'][2]['tone'] = round(t['faces'][2]['tone'] * (1 + share), 4)
        return lambda: both(change)

    def own_tone(share):
        """Of a body not on the skin most of its sex wear, so the person's tone stands as it was."""
        def change(t):
            t['bodies'][minor]['tone_rgb'] = [round(x * (1 + share), 4) for x in t['bodies'][minor]['tone_rgb']]
        return lambda: both(change)

    def meets(share):
        def change(d):
            r = d['texture']['reference']
            r['meets_rgb'] = [round(x * (1 + share), 4) for x in r['meets_rgb']]
        return lambda: data(rec, change)

    m = record['mask']
    skin_js = 'renderers/web/js/human-skin.js'
    sheet_row = str(SHEET.relative_to(ROOT / 'assets'))
    hashed = next(k for k, v in PACKS.items() if v['archive_sha256'])

    cut = AUTHORED / 'faces' / f'{ids[2]}.png'
    # (what is broken, the refusal meant for it or None for a copy that must pass, how)
    plain = [
        ('a cut changed by one byte', 'the cut is not the bytes SOURCE.json pins', lambda: cut.write_bytes(cut.read_bytes() + b'\0')),
        ('a cut gone from the folder', 'no cut or no source row', cut.unlink),
        ('the sheet changed by one byte', 'is not the bytes the record names', lambda: SHEET.write_bytes(SHEET.read_bytes() + b'\0')),
        ("a pack's own record changed by one byte", "is not the bytes SOURCE.json pins as the pack's own record",
         lambda: (AUTHORED / f'{pack}.original.json').write_bytes((AUTHORED / f'{pack}.original.json').read_bytes() + b' ')),
        ('a face listed twice', 'a face is listed twice', lambda: data(rec, lambda d: d['faces'].append(dict(d['faces'][0])))),
        ('a face pinned in SOURCE.json that the record does not keep', 'SOURCE.json pins a face stray the record does not keep',
         lambda: data(src, lambda d: d['faces'].__setitem__('stray', d['faces'][ids[0]]))),
        ("a pack's address changed in SOURCE.json", "SOURCE.json's `packs` are not the packs this tool names",
         lambda: data(src, lambda d: d['packs'][pack].__setitem__('url', d['packs'][pack]['url'] + '.old'))),
        ("a pack's hash changed in SOURCE.json", "SOURCE.json's `packs` are not the packs this tool names",
         lambda: data(src, lambda d: d['packs'][hashed].__setitem__('archive_sha256', '0' * 64))),
        ("an atlas's size in its pack changed in SOURCE.json", 'SOURCE.json is not the one --ingest wrote',
         lambda: data(src, lambda d: d['faces'][ids[2]]['entry'].__setitem__('size', d['faces'][ids[2]]['entry']['size'] + 1))),
        ('the record with no pin of SOURCE.json', 'SOURCE.json is not the one --ingest wrote', lambda: data(rec, lambda d: d.pop('source_sha256'))),
        ('the record naming another SOURCE.json', "the record's `sources` is not",
         lambda: data(rec, lambda d: d.__setitem__('sources', d['sources'].replace('SOURCE.json', 'SOURCE_old.json')))),
        ("a cut's source row naming another box", 'cut from another box or atlas than the record names',
         lambda: data(src, lambda d: d['faces'][ids[2]]['cut']['box_px'].__setitem__(0, d['faces'][ids[2]]['cut']['box_px'][0] + 1))),
        ("a cut's source row naming another atlas", 'cut from another box or atlas than the record names',
         lambda: data(src, lambda d: d['faces'][ids[2]]['entry'].__setitem__('path', d['faces'][ids[2]]['entry']['path'] + '.other'))),
        ("a cut's source row naming another pack", 'cut from another box or atlas than the record names',
         lambda: data(src, lambda d: d['faces'][ids[2]].__setitem__('pack', 'another_pack'))),
        ("a cut's source row naming another file as the cut", "SOURCE.json's row for its cut",
         lambda: sourced(lambda d: d['faces'][ids[2]]['cut'].__setitem__('file', 'faces/other.png'))),
        ("a cut's source row giving its map another size", "SOURCE.json's row for its cut",
         lambda: sourced(lambda d: d['faces'][ids[2]]['cut'].__setitem__('of_map_px', 4096))),
        ("a cut's source row saying something else was done to it", "SOURCE.json's row for its cut",
         lambda: sourced(lambda d: d['faces'][ids[2]]['cut'].__setitem__('change', 'resampled from somewhere'))),
        ("SOURCE.json's account of what it is, rewritten", "SOURCE.json's account of itself", lambda: sourced(lambda d: d.__setitem__('what', 'x'))),
        ("SOURCE.json's account of how the cuts were looked at, rewritten", "SOURCE.json's account of itself", lambda: sourced(lambda d: d.__setitem__('uv_check', 'not checked'))),
        ("SOURCE.json naming another file as a pack's own record", f"SOURCE.json does not name {pack}.original.json as {pack}'s own record",
         lambda: sourced(lambda d: d['pack_records'][pack].__setitem__('in', 'elsewhere.json'))),
        ("a cut's licence no longer CC0", 'no CC0 licence evidence', lambda: data(src, lambda d: d['faces'][ids[2]].__setitem__('license', 'CC-BY-4.0'))),
        ("a cut's licence evidence emptied", 'no CC0 licence evidence', lambda: data(src, lambda d: d['faces'][ids[2]].__setitem__('license_evidence', ''))),
        ("a cut's licence evidence in somebody's own words", 'its licence evidence is not in the words this tool writes',
         lambda: data(src, lambda d: d['faces'][ids[2]].__setitem__('license_evidence', 'somebody said so'))),
        ("a community cut's licence evidence in somebody's own words", 'its licence evidence is not in the words this tool writes',
         lambda: data(src, lambda d: d['faces'][of_pack].__setitem__('license_evidence', 'somebody said so'))),
        ("a community cut's licence resting on another skin's row of its pack's record", 'is not the one the record names for it', lambda: sourced(rested)),
        ("a community cut's licence resting on another pack's record", 'is not the one the record names for it', lambda: sourced(another_pack)),
        ("a system cut's licence resting on another cut's kept material file", 'is not the one the record names for it', lambda: sourced(lent)),
        ('a kept material file changed by one byte', 'its kept material file changed', lambda: material().write_bytes(material().read_bytes() + b' ')),
        ('a kept material file that no longer says CC0', 'its kept material file does not say CC0 of this atlas', unsaid),
        ('a kept material file that says CC0 of another atlas', 'its kept material file does not say CC0 of this atlas', renamed),
        ('a system cut with no material file behind it', 'neither a kept material file nor a pack record stands behind its licence',
         lambda: data(src, lambda d: d['faces'][of_system].pop('material'))),
        ("a community pack's own record changed by one byte", "the pack's record it rests on",
         lambda: (AUTHORED / source['faces'][of_pack]['pack_record']['in']).write_bytes((AUTHORED / source['faces'][of_pack]['pack_record']['in']).read_bytes() + b' ')),
        ("a cut's source row giving another author than its pack's record", "the pack's kept record does not say CC0 of it, by the author and source",
         lambda: data(src, lambda d: d['faces'][of_pack]['pack_record'].__setitem__('author', 'somebody else'))),
        ("a cut's source row giving another source than its pack's record", "the pack's kept record does not say CC0 of it, by the author and source",
         lambda: data(src, lambda d: d['faces'][of_pack]['pack_record'].__setitem__('source', 'http://example.invalid/'))),
        ("a pack's kept record saying another licence of a cut", "the pack's kept record does not say CC0 of it, by the author and source", unlicensed),
        ("a cut's source row naming a skin its pack's record does not hold", "the pack's kept record has no row",
         lambda: data(src, lambda d: d['faces'][of_pack]['pack_record'].__setitem__('key', 'no_such_skin'))),
        ("a cut's source row with its pack's material file unread", 'was not read for a licence line', lambda: data(src, lambda d: d['faces'][of_pack].pop('pack_material'))),
        ("a licence note, and no licence line in SOURCE.json for it to answer", 'holds no licence line of its material file for the note to answer',
         lambda: sourced(lambda d: d['faces'][noted]['pack_material'].__setitem__('licence_lines', []))),
        ('a licence note changed in the record alone', 'carries a licence line of its own and no `licence_note`',
         lambda: data(rec, lambda d: next(f for f in d['faces'] if f['id'] == noted).__setitem__('licence_note', next(f for f in d['faces'] if f['id'] == noted)['licence_note'] + ' (altered)'))),
        ('the evidence a licence note cites changed in SOURCE.json alone', 'the evidence its licence note cites is not what SOURCE.json holds',
         lambda: data(src, lambda d: d['faces'][noted]['licence_note_evidence'].__setitem__('says', 'something else'))),
        ('a licence note citing words its file does not say', 'is not kept as pinned, or does not say',
         lambda: noting(lambda row: row['licence_note_evidence'].__setitem__('says', 'released under no licence at all'))),
        ('a licence note that no longer names its file by its hash', 'does not name the file it cites by its SHA-256', lambda: noting(unhashed)),
        ('a face of an age the rule does not know', 'sex or age not one the rule knows', lambda: data(rec, lambda d: d['faces'][2].__setitem__('age', 'ancient'))),
        ('a face of a sex the rule does not know', 'sex or age not one the rule knows', lambda: data(rec, lambda d: d['faces'][2].__setitem__('sex', 'either'))),
        ("a pack's own record gone", "is missing: the pack's own list of its skins", (AUTHORED / f'{pack}.original.json').unlink),
        ('a licence note with no kept file behind it', 'its licence note cites no kept file',
         lambda: data(rec, lambda d: next(f for f in d['faces'] if f['id'] == noted).pop('licence_note_evidence'))),
        ('the file a licence note cites changed by one byte', 'is not kept as pinned, or does not say', cited),
        ('a skin left out twice', 'is listed twice', lambda: data(rec, twice)),
        ('a skin left out with no reason', 'no reason given', lambda: data(rec, lambda d: d['left_out']['skins'][0].__setitem__('why', ''))),
        ("a pack's skin neither kept nor left out", "is neither kept nor in the record's left_out", lambda: data(rec, lambda d: d['left_out']['skins'][0]['skins'].pop())),
        ("a skin left out that no pack's record lists", 'the record names a skin no_such_skin', lambda: data(rec, lambda d: d['left_out']['skins'][0]['skins'].append('no_such_skin'))),
        ('a skin both kept and left out', 'is both kept and left out', lambda: data(rec, kept_and_left)),
        ("the record's count of the packs' skins changed", 'left_out.basis does not say what the packs hold', basis(f'hold {n + out} skins', f'hold {n + out + 1} skins')),
        ("the record's count of the faces kept changed", 'left_out.basis does not say what the packs hold', basis(f'{n} are kept', f'{n + 1} are kept')),
        ("the record's count of the skins left out changed", 'left_out.basis does not say what the packs hold', basis(f'other {out} ', f'other {out + 1} ')),
        ("SOURCE.json's count of the skins left out changed", 'SOURCE.json `not_used` does not say',
         lambda: data(src, lambda d: d.__setitem__('not_used', d['not_used'].replace(f'The other {out} skins', f'The other {out + 1} skins')))),
        ("a cut's row dropped from the register", f'{register} does not list authored/humans/face_library/faces/{ids[2]}.png',
         lambda: text(register, f'faces/{ids[2]}.png`', f'faces/{ids[2]}_gone.png`')),
        ("the sheet's own row dropped from the register", f'{register} does not list {sheet_row}',
         lambda: everywhere(register, sheet_row, sheet_row.replace('.jpg', '_gone.jpg'))),
        ("a register row with another hash for its atlas", "does not give CC0-1.0 and the atlas's SHA-256",
         row_of_register(atlas_hash, ('0' if atlas_hash[0] != '0' else '1') + atlas_hash[1:])),
        ('a register row no longer saying CC0-1.0', "does not give CC0-1.0 and the atlas's SHA-256", row_of_register('CC0-1.0', 'CC-BY-4.0')),
        ('a register row naming CC0-1.0 only to say it is not that', "does not give CC0-1.0 and the atlas's SHA-256", row_of_register('CC0-1.0 by', 'CC-BY-NC-4.0 (not CC0-1.0) by')),
        ("the register's count of the packs' skins changed", f"does not say the packs' {n + out} skins can be counted against",
         lambda: text(register, f'{n + out} skins can be counted against', f'{n + out + 1} skins can be counted against')),
        ("the register's count of the faces kept, where it counts the packs' skins, changed", f"does not say the packs' {n + out} skins can be counted against",
         lambda: text(register, f'the {n} kept and the {out} left out', f'the {n + 3} kept and the {out} left out')),
        ("the register's count of the skins left out, where it counts the packs' skins, changed", f"does not say the packs' {n + out} skins can be counted against",
         lambda: text(register, f'the {n} kept and the {out} left out', f'the {n} kept and the {out + 3} left out')),
        ("the register's count of the faces changed", f'does not say the folder holds the faces of {n} skin atlases',
         lambda: text(register, f'The face of each of {n} skin atlases', f'The face of each of {n + 3} skin atlases')),
        ("the register's count of the cuts changed", f'does not say the folder holds the faces of {n} skin atlases',
         lambda: text(register, f'those {n} cuts', f'those {n + 3} cuts')),
        ("the folder's page's count of the faces changed", 'README.md does not give the counts',
         lambda: text(f'{auth}/README.md', f'the face of each of {n} more', f'the face of each of {n + 3} more')),
        ("the folder's page's count of the faces kept changed", 'README.md does not give the counts',
         lambda: text(f'{auth}/README.md', f'of which {n} are', f'of which {n + 3} are')),
        ("the folder's page's count of the skins left out changed", 'README.md does not give the counts',
         lambda: text(f'{auth}/README.md', f'other {out} skins', f'other {out + 3} skins')),
        ('the record with no sheet built', 'no sheet built', lambda: data(rec, lambda d: d.pop('texture'))),
        ('the record naming another sheet', 'the record names another sheet',
         lambda: data(rec, lambda d: d['texture'].__setitem__('file', d['texture']['file'].replace('.jpg', '_old.jpg')))),
        ('the record naming another reference skin', 'the record names another reference skin',
         lambda: data(rec, lambda d: d['texture']['reference'].__setitem__('file', d['texture']['reference']['file'] + '.old'))),
        ('the sheet built at another size', 'the sheet was built for another list of faces',
         lambda: data(rec, lambda d: d['texture']['size_px'].__setitem__(1, d['texture']['size_px'][1] + record['tile_px']))),
        ('the sheet built for the faces in another order', 'the sheet was built for another list of faces', lambda: data(rec, reordered)),
        ('a freckled face no longer marked for light complexions only', 'who may wear a face (sex, age, light_only) changed',
         lambda: data(rec, lambda d: next(f for f in d['faces'] if f['id'] == freckled).pop('light_only'))),
        ('the JPEG quality changed since the sheet was built', 'the box, mask, tile size, headroom or JPEG quality changed',
         lambda: data(rec, lambda d: d.__setitem__('jpeg_quality', d['jpeg_quality'] - 1))),
        ('a complexion changed since the sheet was built', 'the complexions changed since the sheet was built',
         lambda: data(rec, lambda d: d['texture']['complexions'][sorted(d['texture']['complexions'])[0]].__setitem__(0, 0.5))),
        ('a body gone from the record', 'the bodies changed since the sheet was built', lambda: data(rec, lambda d: d['texture']['bodies'].pop(body))),
        ("the mask's feather changed in the record", 'does not draw the mask this tool measures under',
         lambda: data(rec, lambda d: d['mask'].__setitem__('feather', d['mask']['feather'] * 2))),
        ("the app's mask moved, in human-skin.js", 'does not draw the mask this tool measures under',
         lambda: text(skin_js, f"centre: Object.freeze([{m['centre'][0]}, ", f"centre: Object.freeze([{round(m['centre'][0] + 0.01, 6)}, ")),
        ("a person's tone read from the other sex's bodies", '`person_tone` is not the skin most bodies of each sex wear', lambda: data(rec, turned)),
        ("a woman's tone changed, a man's as it was", '`person_tone` is not the skin most bodies of each sex wear', alone('female')),
        ("a man's tone changed, a woman's as it was", '`person_tone` is not the skin most bodies of each sex wear', alone('male')),
        ("as many women's bodies on one skin as on another", 'no one skin is worn by most female bodies', lambda: data(rec, tied)),
        ("the kit's copy of the library altered", 'the kit does not carry this library',
         lambda: data(kit, lambda d: d['faces']['person_tone_rgb']['male'].__setitem__(0, 0.5))),
        ('the gate no longer running the check', 'tools/check.sh does not run this step', unstepped('--check')),
        ('the gate no longer running the self-test', "tools/check.sh does not run the self-test's step", unstepped('--self-test')),
        ("the readers' register no longer naming the check's step", 'does not name this step under both Pillow and numpy',
         lambda: text('tools/check_gate_readers.py', "The face library's cuts", "The face library's cut")),
        ("the readers' register no longer naming the self-test's step", "does not name the self-test's step under both Pillow and numpy",
         lambda: text('tools/check_gate_readers.py', "the face library's check refuses", "the face library's check refused")),
    ]
    # These need the sheet read. Each bound has a case a little beyond it, refused by that bound
    # alone, and a case a little within it that passes; the figures are what each read on
    # 2026-11-15 against the bound, and a sheet decoded by the same JPEG library reads the same.
    read = [
        ('the sheet stored a second time, unchanged', None, resheet),
        # SAME_PAINTING, 2.4: 2.0 and 3.0
        ('two kept cuts two levels of 255 apart', 'are one painting', near_copy(2)),
        ('two kept cuts three levels apart', ('not', 'are one painting'), near_copy(3)),
        ('two kept cuts alike inside the mask and unlike outside it', 'are one painting', recut(outside)),
        ('two faces of the sheet changed places', "cut than its own", lambda: resheet(swapped)),
        # SHEET_MEAN, 0.75: 0.97 and 0.44
        ('the whole sheet one level darker', 'the sheet as a whole is not the cuts laid out', lambda: resheet(lambda px: px - 1)),
        ('the two upper rows of faces one level darker', None, lambda: resheet(upper(1))),
        # ...by how far, not which way: lighter above and darker below reads 0.97, and 0.14 with the ways set against each other
        ('the upper half of the sheet one level lighter, the lower one level darker', 'the sheet as a whole is not the cuts laid out', lambda: resheet(halves)),
        # SHEET_TOLERANCE, 1.5: 1.89 and 0.99
        ('one face of the sheet two levels darker', 'its tile of the sheet is not its cut laid out as the record says (mean difference', lambda: resheet(darker(2))),
        ('one face of the sheet half a part in a hundred darker', None, lambda: resheet(dimmed)),   # ...and its worst block 2.3 of 3
        # ...by how far, not which way: a face moved three pixels reads 2.87, and 0.01 with the ways set against each other
        ('one face of the sheet moved three pixels sideways', 'its tile of the sheet is not its cut laid out as the record says (mean difference', lambda: resheet(moved(3))),
        # SHEET_WORST, 16: 20 and 10
        ('a 24 pixel square of one face painted 20 lighter', 'its worst thousandth differs by', lambda: resheet(square(24, 20))),
        ('one face of the sheet softened, a blur of radius 1', None, lambda: resheet(softened)),
        ('a 24 pixel square of the last face painted 20 lighter', 'its worst thousandth differs by', lambda: resheet(square(24, 20, of=n - 1))),
        # ...each colour on its own: 30 in the red alone reads 30, and 12 over the three colours together
        ('a 24 pixel square of one face painted 30 redder', 'its worst thousandth differs by', lambda: resheet(square(24, 30, channels=0))),
        # SHEET_BLOCK, 3: 4.9 (and 2.3, above); and the small repaint the worst thousandth cannot see
        ('a 24 pixel square of one face painted 5 lighter', 'px block differs by', lambda: resheet(square(24, 5))),
        ('an 8 pixel square of one face painted 120 lighter', 'px block differs by', lambda: resheet(square(8, 120))),
        # ...each colour on its own: 6 in the red alone reads 6.1, and 2.3 over the three colours together
        ('a 24 pixel square of one face painted 6 redder', 'px block differs by', lambda: resheet(square(24, 6, channels=0))),
        ('the sheet stored with its colour at half size', 'does not keep its colour at full size', lambda: resheet(subsampling=2)),
        ('the sheet stored with its colour at half width', 'does not keep its colour at full size', lambda: resheet(subsampling=1)),
        ('the sheet stored with a colour profile', 'carries a colour profile or EXIF data', lambda: resheet(icc_profile=b'bytes in the place of a colour profile')),
        ('the sheet stored with EXIF data that turns it upside down', 'carries a colour profile or EXIF data', lambda: resheet(exif=turn())),
        # TOLERANCE, one part in a hundred: three and one in two hundred
        ("a body's gain three parts in two hundred up", 'its skin changed since the sheet was built', gain(0.015)),
        ("a body's gain one part in two hundred up", None, gain(0.005)),
        ("a face's tone three parts in two hundred up", 'its tone is not what the record holds', tone(0.015)),
        ("a body's own tone three parts in two hundred up", 'its skin changed since the sheet was built', own_tone(0.015)),
        ("the reference skin's colour three parts in two hundred up", "the reference skin's colour where a face meets it is not what the record holds", meets(0.015)),
        ("the reference skin's colour gone from the record", "the reference skin's colour where a face meets it is not what the record holds",
         lambda: data(rec, lambda d: d['texture']['reference'].__setitem__('meets_rgb', []))),
        # ...the worst thousandth is a thousandth: 147 values of a tile's 196,608 are under it (and the block's test sees them)
        ('a 7 pixel square of one face painted 20 lighter', ('not', 'its worst thousandth differs by'), lambda: resheet(square(7, 20))),
        ('the sheet stored one row of pixels taller', 'the sheet is not the size the record builds', lambda: resheet(lambda px: np.concatenate([px, px[-1:]]))),
    ]
    if Image is None:
        print(f'   skip: Pillow is not installed, so {len(read)} cases that read the sheet were not tried:')
        for name, _, _ in read:
            print(f'   skip   {name}')
    cases = [('the copy as it stands', None, lambda: None)] + plain + (read if Image is not None else [])
    failed = 0
    for name, expect, breaking in cases:
        breaking()
        said = io.StringIO()
        with contextlib.redirect_stdout(said):
            try:
                rc = check(json.loads(RECORD.read_text()))
            except SystemExit as e:
                rc = 1
                print(f'FAIL {e}')
        said = said.getvalue()
        first = ' / '.join(said.strip().splitlines()[:3])
        if expect is None:
            ok = rc == 0
            print(f"   {'ok  ' if ok else 'FAIL'} {name}: {'passes' if ok else 'is refused: ' + first}")
        elif isinstance(expect, tuple):
            ok = expect[1] not in said
            print(f"   {'ok  ' if ok else 'FAIL'} {name}: {'not' if ok else 'wrongly'} refused as ({expect[1]})")
        else:
            ok = rc == 1 and expect in said
            print(f"   {'ok  ' if ok else 'FAIL'} {name}: {'refused' if ok else 'not refused'} ({expect}){'' if ok or rc == 0 else '; it said: ' + first}")
        failed += not ok
        for rel in COPIED:
            fresh(rel)
    tried = f'{len(cases)} of {1 + len(plain) + len(read)} cases tried'
    if failed:
        print(f'   self-test: FAILED: {failed} case(s), {tried}')
    elif Image is None:
        print(f'   self-test: {tried}, each as it should be; the {len(read)} that read the sheet were NOT tried (no Pillow)')
    else:
        print(f'   self-test: {tried}: the face library check refuses every broken copy and passes the whole ones')
    return 1 if failed else 0


def preview(record, out):
    Image = image()
    from PIL import ImageDraw
    cols = 8
    faces = record['faces']
    px = 256
    sheet = Image.new('RGB', (cols * px, math.ceil(len(faces) / cols) * px))
    for i, f in enumerate(faces):
        t = Image.open(AUTHORED / 'faces' / f"{f['id']}.png").convert('RGB').transpose(Image.ROTATE_270).resize((px, px))
        ImageDraw.Draw(t).text((3, 3), f"{f['id']}"[:40], fill=(255, 255, 0))
        sheet.paste(t, ((i % cols) * px, (i // cols) * px))
    sheet.save(out, quality=88)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--check', action='store_true')
    ap.add_argument('--self-test', action='store_true')
    ap.add_argument('--ingest', nargs='+', metavar='PACK=DIR')
    ap.add_argument('--preview', metavar='OUT')
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    record = json.loads(RECORD.read_text())
    if args.ingest:
        ingest(record, args.ingest)
        return 0
    if args.preview:
        preview(record, args.preview)
        return 0
    if args.check:
        return check(record)
    blob, texture, _ = build(record)
    SHEET.parent.mkdir(parents=True, exist_ok=True)
    SHEET.write_bytes(blob)
    record['texture'] = texture
    RECORD.write_text(json.dumps(record, indent=1) + '\n')
    print(f"wrote {SHEET.relative_to(ROOT)} ({len(blob)} bytes, {len(texture['faces'])} faces, {len(texture['bodies'])} bodies); now run python3 tools/human_variation_kit.py")
    return 0


if __name__ == '__main__':
    sys.exit(main())
