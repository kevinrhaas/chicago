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
                        # rounding is a fraction of one; a tile blurred, or moved three pixels, reads 2 and over
SHEET_MEAN = 0.75       # ...and the whole sheet by this: a change over all of it (2 percent darker reads 3)
SHEET_WORST = 16        # ...and no tile's worst thousandth of values by more than this (of 255): a mean over a tile
                        # cannot see a small repaint (a 24 px square painted 120 lighter read 1.0, under the 1.5);
                        # two JPEG libraries differ by a level or two a value
SAME_PAINTING = 2.4     # two cuts nearer than this inside the mask (mean, of 255) are one painting: three skins left
                        # out for it read 0.5, 2.3 and 2.0 against a kept one; the nearest two kept read 2.6
LICENCE_LINE = re.compile(r'licen[sc]e|copyright|AGPL|GPL|CC0|CC-BY', re.I)

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
        ring, inside = tones(linear(np.asarray(cut_of(Image, Image.open(io.BytesIO(raw)), record))), m_full)
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


def ingest(record, pairs):
    Image = image()
    if Image is None:
        raise SystemExit('tools/face_library.py --ingest needs Pillow')
    dirs = dict(p.split('=', 1) for p in pairs)
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
                       'change': 'none: the pixels of the box, as the atlas has them' if im.size[0] == record['map_px'] else f"the box of a {im.size[0]} px atlas, resampled to its size on a {record['map_px']} px map"}}
        if f.get('material'):
            mh = root / f['material']
            kept = AUTHORED / 'materials' / mh.name
            kept.write_bytes(mh.read_bytes())
            row['material'] = {'path': f['material'], 'sha256': sha(mh.read_bytes()), 'kept_in_repo': str(kept.relative_to(AUTHORED)) + ' (unchanged)'}
            row['license'] = 'CC0-1.0'
            row['license_evidence'] = 'its material file\'s header: "This asset was explicitly released as CC0 in september 2020. ... The copyright holders at the point of the release to CC0 were: Data Collection AB, Joel Palmius, Jonas Hauquier."'
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
            row['license_evidence'] = f"the pack's own record of the asset in {kept.name} (\"license\": \"CC0\"); its material file is not kept and not used"
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
        'ticket': 'T-3553',
        'what': "The face of each CC0 MakeHuman skin atlas the face library uses (data/humans/variation/face_library.json), cut from the same box of the hm08 map, and where each atlas came from. The atlases themselves are not kept: each is pinned here by size, CRC-32 and SHA-256 and can be fetched again from its pack.",
        'packs': PACKS,
        'uv_check': 'Every atlas is laid out on the hm08 base mesh\'s own map, as the three atlases the bodies wear are; each cut was looked at upright (tools/face_library.py --preview) and on built figures.',
        'pack_records': records,
        'not_used': f'The other {out_of} skins of these packs, each with its reason in the record\'s `left_out`; and each pack\'s name for an atlas as a fact about its wearer.',
        'faces': {f['id']: source['faces'][f['id']] for f in record['faces'] if f['id'] in source['faces']},
    }
    SOURCE.write_text(json.dumps(source, indent=1) + '\n')
    RECORD.write_text(json.dumps(record, indent=1) + '\n')


def check(record):
    bad = []
    source = json.loads(SOURCE.read_text()) if SOURCE.exists() else {'faces': {}}
    ids = [f['id'] for f in record['faces']]
    if len(set(ids)) != len(ids):
        bad.append('a face is listed twice')
    for k in sorted(set(source['faces']) - set(ids)):
        bad.append(f"SOURCE.json pins a face {k} the record does not keep: run --ingest")
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
        if row.get('license') != 'CC0-1.0' or not row.get('license_evidence'):
            bad.append(f"{f['id']}: no CC0 licence evidence")
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
        if row and (row['entry']['sha256'] not in line or 'CC0-1.0' not in line):
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
    step = re.search(r'step "([^"]+)" \\\n\s*python3 tools/face_library\.py --check', (ROOT / 'tools/check.sh').read_text())
    if not step or (ROOT / 'tools/check_gate_readers.py').read_text().count(f'"{step.group(1)}"') < 2:
        bad.append('tools/check_gate_readers.py does not name this step under both Pillow and numpy')
    t = record.get('texture')
    if not t:
        bad.append('no sheet built: run tools/face_library.py')
    else:
        tile, cols = record['tile_px'], record['cols']
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
            # A person's tone is read from the skin most bodies of their sex wear, as the record holds it.
            mine = person_tone(t['bodies'])
            if t.get('person_tone') != mine:
                bad.append("`person_tone` is not the skin most bodies of each sex wear: run tools/face_library.py")
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
            at = lambda px, i: px[(i // cols) * tile:(i // cols + 1) * tile, (i % cols) * tile:(i % cols + 1) * tile]
            if kept_px.shape != coded.shape:
                bad.append('the sheet is not the size the record builds: run tools/face_library.py')
            else:
                if np.abs(kept_px - coded).mean() > SHEET_MEAN:
                    bad.append(f'the sheet as a whole is not the cuts laid out as the record says (mean difference {np.abs(kept_px - coded).mean():.2f} of 255): run tools/face_library.py')
                for i, f in enumerate(record['faces']):
                    apart = np.abs(at(kept_px, i) - at(coded, i))
                    err, worst = apart.mean(), float(np.quantile(apart, 0.999))
                    if err > SHEET_TOLERANCE:
                        bad.append(f"{f['id']}: its tile of the sheet is not its cut laid out as the record says (mean difference {err:.2f} of 255): run tools/face_library.py")
                    elif worst > SHEET_WORST:
                        bad.append(f"{f['id']}: a part of its tile of the sheet is not its cut laid out as the record says (its worst thousandth differs by {worst:.0f} of 255): run tools/face_library.py")
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
          'assets/humans/web/hm08_variation_kit.json', 'assets/LICENSES.md', 'tools/check.sh', 'tools/check_gate_readers.py')
LINKED = ('data/humans/variation/axes.json', 'renderers/web/js/human-looks.js', 'renderers/web/js/human-skin.js',
          'assets/authored/humans/skin_toigo_bronze/young_lightskinned_male_diffuse_Bronze.png')


def _rebase(root):
    """Point every path this tool reads at another copy of the tree (--self-test's)."""
    g = globals()
    for k in ('RECORD', 'AUTHORED', 'SOURCE', 'WEB', 'SHEET', 'LOOKS_JS', 'SKIN_JS', 'REFERENCE', 'AXES'):
        g[k] = root / g[k].relative_to(g['ROOT'])
    g['ROOT'] = root


def self_test():
    """Breaks a copy of the library each way the check must refuse, and sees each refused.

    The check passed a broken library more than once before a reviewer broke one on purpose
    (2026-11-14 and 15): two cuts that were one painting, a tile repainted in part, a count in
    the register, a licence note with nothing behind it. Each is a case here, with the plainer
    ones. The copy is made in a temporary folder outside the tree and nothing in the tree is
    written. Without Pillow the cases that need the sheet read are skipped, and said so
    (tools/check_gate_readers.py makes CI red without it).
    """
    import contextlib, os, shutil, tempfile
    real, Image = ROOT, image()
    with tempfile.TemporaryDirectory(prefix='face_library_self_test_') as tmp:
        root = pathlib.Path(tmp)

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
        try:
            for rel in COPIED:
                fresh(rel)
            record = json.loads(RECORD.read_text())
            ids, tile, cols = [f['id'] for f in record['faces']], record['tile_px'], record['cols']
            noted = next(f['id'] for f in record['faces'] if f.get('licence_note'))
            freckled = next(f['id'] for f in record['faces'] if f.get('light_only'))
            pack = next(iter(PACKS))

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

            def resheet(change=lambda px: px, subsampling=0):
                """The sheet decoded, changed, stored again as the tool stores it, and named by the record."""
                px = change(np.asarray(Image.open(SHEET).convert('RGB')).astype(float))
                out = io.BytesIO()
                Image.fromarray(np.clip(np.rint(px), 0, 255).astype(np.uint8)).save(out, 'JPEG', quality=record['jpeg_quality'], subsampling=subsampling)
                SHEET.write_bytes(out.getvalue())
                data('data/humans/variation/face_library.json', lambda d: d['texture'].__setitem__('sha256', sha(out.getvalue())))

            def place(i):
                return slice((i // cols) * tile, (i // cols + 1) * tile), slice((i % cols) * tile, (i % cols + 1) * tile)

            def swapped(px):
                a, b = px[place(0)].copy(), px[place(1)].copy()
                px[place(0)], px[place(1)] = b, a
                return px

            def repainted(px):
                rows, across = place(3)
                px[rows.start + 116:rows.start + 140, across.start + 116:across.start + 140] += 120
                return px

            def one_painting():
                px = np.asarray(Image.open(AUTHORED / 'faces' / f'{ids[0]}.png').convert('RGB')).copy()
                px[:4, :4] ^= 1     # another file, the same painting
                Image.fromarray(px).save(AUTHORED / 'faces' / f'{ids[1]}.png', 'PNG')
                pin = sha((AUTHORED / 'faces' / f'{ids[1]}.png').read_bytes())
                data('assets/authored/humans/face_library/SOURCE.json', lambda d: d['faces'][ids[1]]['cut'].__setitem__('sha256', pin))

            def twice(d):
                row = d['left_out']['skins'][0]
                row['skins'].append(row['skins'][0])

            def turned(d):
                t = d['texture']['person_tone']
                t['male'], t['female'] = t['female'], t['male']

            n, rec, auth = len(ids), 'data/humans/variation/face_library.json', 'assets/authored/humans/face_library'
            cut = AUTHORED / 'faces' / f'{ids[2]}.png'
            plain = [
                ('a cut changed by one byte', 'the cut is not the bytes SOURCE.json pins', lambda: cut.write_bytes(cut.read_bytes() + b'\0')),
                ('the sheet changed by one byte', 'is not the bytes the record names', lambda: SHEET.write_bytes(SHEET.read_bytes() + b'\0')),
                ("a pack's own record changed by one byte", "is not the bytes SOURCE.json pins as the pack's own record",
                 lambda: (AUTHORED / f'{pack}.original.json').write_bytes((AUTHORED / f'{pack}.original.json').read_bytes() + b' ')),
                ('a face pinned in SOURCE.json that the record does not keep', 'SOURCE.json pins a face stray the record does not keep',
                 lambda: data(f'{auth}/SOURCE.json', lambda d: d['faces'].__setitem__('stray', d['faces'][ids[0]]))),
                ('a skin left out twice', 'is listed twice', lambda: data(rec, twice)),
                ('a skin left out with no reason', 'no reason given', lambda: data(rec, lambda d: d['left_out']['skins'][0].__setitem__('why', ''))),
                ('a licence note with no kept file behind it', 'its licence note cites no kept file',
                 lambda: data(rec, lambda d: next(f for f in d['faces'] if f['id'] == noted).pop('licence_note_evidence'))),
                ("a cut's row dropped from the register", f'assets/LICENSES.md does not list authored/humans/face_library/faces/{ids[2]}.png',
                 lambda: text('assets/LICENSES.md', f'faces/{ids[2]}.png`', f'faces/{ids[2]}_gone.png`')),
                ("the register's count of the faces changed", f'does not say the folder holds the faces of {n} skin atlases',
                 lambda: text('assets/LICENSES.md', f'The face of each of {n} skin atlases', f'The face of each of {n + 3} skin atlases')),
                ("the folder's page's count of the faces changed", 'README.md does not give the counts',
                 lambda: text(f'{auth}/README.md', f'of which {n} are', f'of which {n + 3} are')),
                ('a freckled face no longer marked for light complexions only', 'who may wear a face (sex, age, light_only) changed',
                 lambda: data(rec, lambda d: next(f for f in d['faces'] if f['id'] == freckled).pop('light_only'))),
                ("the kit's copy of the library altered", 'the kit does not carry this library',
                 lambda: data('assets/humans/web/hm08_variation_kit.json', lambda d: d['faces']['person_tone_rgb']['male'].__setitem__(0, 0.5))),
                ("the readers' register no longer naming the step", 'does not name this step under both Pillow and numpy',
                 lambda: text('tools/check_gate_readers.py', "The face library's cuts", "The face library's cut")),
            ]
            read = [
                ('the sheet stored a second time, unchanged', None, resheet),
                ('two kept cuts that are one painting', 'are one painting', one_painting),
                ('two faces of the sheet changed places', "cut than its own", lambda: resheet(swapped)),
                ('the sheet two parts in a hundred darker', 'the sheet as a whole is not the cuts laid out', lambda: resheet(lambda px: px * 0.98)),
                ('a 24 pixel square of one face painted 120 lighter', 'a part of its tile of the sheet is not its cut', lambda: resheet(repainted)),
                ('the sheet stored with its colour at half size', 'does not keep its colour at full size', lambda: resheet(subsampling=2)),
                ("a person's tone read from the other sex's bodies", '`person_tone` is not the skin most bodies of each sex wear', lambda: data(rec, turned)),
            ]
            if Image is None:
                print(f'   skip: Pillow is not installed, so {len(read)} cases that read the sheet were not tried')
            failed = 0
            for name, expect, breaking in [('the copy as it stands', None, lambda: None)] + plain + (read if Image is not None else []):
                breaking()
                out = io.StringIO()
                with contextlib.redirect_stdout(out):
                    try:
                        rc = check(json.loads(RECORD.read_text()))
                    except SystemExit as e:
                        rc = 1
                        print(f'FAIL {e}')
                said = out.getvalue()
                ok = (rc == 0) if expect is None else (rc == 1 and expect in said)
                failed += not ok
                if expect is None:
                    print(f"   {'ok  ' if ok else 'FAIL'} {name}: {'passes' if ok else 'is refused: ' + ' / '.join(said.strip().splitlines()[:3])}")
                else:
                    print(f"   {'ok  ' if ok else 'FAIL'} {name}: {'refused' if ok else 'not refused'} ({expect})")
                for rel in COPIED:
                    fresh(rel)
        finally:
            _rebase(real)
    print(f"   self-test: {'FAILED: ' + str(failed) + ' case(s)' if failed else 'the face library check refuses every broken copy and passes the whole ones'}")
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
