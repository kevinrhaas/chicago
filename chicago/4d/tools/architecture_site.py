#!/usr/bin/env python3
"""Write the Architecture site's data beside its page (T-3750).

The owner, 2026-11-26: "Expose the architecture site and building kit to expert users,
separate link/site." Open to anyone with the link, no sign-in (his ruling the same day).

The page is renderers/web/architecture/ (copied into the mirror at walk/architecture/
with the rest of the renderer). This script writes what it reads, all of it DERIVED from
committed records and nothing typed by hand:

  data.json       the sixteen kits (data/components/prairie_1904/k*.json): their rule,
                  every collection of variants, parts, fabrics, recipes or layers with its
                  measured values, confidence and note; and every structure record that
                  names a kit's part, with the 1904 (or its own year's) sidecar's name,
                  grade and published model.
  specimens/      each kit's specimen GLB (docs/RESEARCH/k*-kit/*.glb), the generator's own
                  sample of every variant, copied unchanged.
  studies/        each kit's study picture, downscaled to 1600 px for the web.

A house's published model is NOT copied: the page reads it from ../../data/gltf/, the
same file the town draws, so this adds no second copy of any building.

Which houses use a kit is read from the records, never asserted. A part id with its kit's
prefix (`k06.opening.sash_2over2_flat`) counts wherever it appears; a K02/K03/K04 library
id (`pressed_red`, `slate_pennsylvania`) counts only under a key that names stone, brick
or a roof, because the bare words are not unique; K01, K12, K13 and K16 also count by the
record's archetype, and K14 by a record naming `k14_condition`.

    python3 tools/architecture_site.py OUT_DIR        # write
    python3 tools/architecture_site.py --check        # build to a temp dir and verify
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent          # chicago/4d
KITS_DIR = ROOT / 'data/components/prairie_1904'
RESEARCH = ROOT / 'docs/RESEARCH'
REPO_BLOB = 'https://github.com/kevinrhaas/chicago/blob/main/chicago/4d/'
REPO_TREE = 'https://github.com/kevinrhaas/chicago/tree/main/chicago/4d/'

# The short name and one line for each kit, as the public Technicians page words them.
KITS = {
    'K01': ('Contract', 'The metric rules every part obeys: storey heights, wall depths, openings, the door datum.'),
    'K02': ('Stone', 'Rock-faced, tooled and rubbed stone, with their joint and edge profiles.'),
    'K03': ('Face brick', 'Pressed fronts and common side and rear walls, each a period brick recipe.'),
    'K04': ('Roof coverings', 'Slate, tile, tin and copper, gutters and downpipes.'),
    'K05': ('Roof forms', 'Mansard, hip, gable and tower roofs, built to the plan.'),
    'K06': ('Windows', 'Sash, plate glass and leaded lights, with visible depth behind the glass.'),
    'K07': ('Entrances', 'Stoops, porches, doors and carriage doors.'),
    'K08': ('Bays', 'Bays, oriels and towers.'),
    'K09': ('Trim', 'Carved entrances, classical and Gothic trim.'),
    'K10': ('Cornices', 'Cornices, parapets, dormer faces and cresting.'),
    'K11': ('Ironwork', 'Fences, gates, canopies and boundary walls.'),
    'K12': ('Coach houses', 'Stables, their fittings and the service wings.'),
    'K13': ('Conservatories', 'Glass houses, from a bay to the Pullman range.'),
    'K14': ('Condition', 'Age, soot, weathering and where a wall meets the ground.'),
    'K15': ('Chimneys', 'Stacks, flues, pots and roof services.'),
    'K16': ('Timber', 'Frame cladding and exterior woodwork, painted to period colours.'),
}
# Study pictures for the three libraries whose folder is not `kNN-*-kit/study.jpg`.
STUDY = {
    'K02': 'k02-stone-library-2288/desktop-raking-panel.jpg',
    'K03': 'k03-brick-library-2290/k03_brick_study.jpg',
    'K04': 'k04-roof-library/study.jpg',
}
ARCHETYPE_KIT = {'k01_frontage': 'K01', 'k12_coach_house': 'K12',
                 'k13_conservatories': 'K13', 'k16_timber': 'K16'}
# A bare library id counts only under a key whose name says what it is (see the docstring).
LIBRARY_KEY = {'K02': re.compile(r'stone|plinth|base|step|sill|lintel|trim|coping', re.I),
               'K03': re.compile(r'brick', re.I),
               'K04': re.compile(r'roof|cover|flash|cap|valley|gutter|rain|ridge|deck', re.I)}
# Keys inside an entry that are its words, not its measures.
PROSE = {'id', 'family', 'meaning', 'note', 'confidence', '_doc', 'sources', 'rule_source', 'uses', 'not_for'}
YEARS = ('1904', '1871', '1835', '1812')


def kit_files():
    out = {}
    for f in sorted(KITS_DIR.glob('k[01][0-9]_*.json')):
        out[f.name[:3].upper()] = f
    missing = sorted(set(KITS) - set(out))
    if missing:
        raise SystemExit(f'architecture_site: no kit file for {", ".join(missing)} in {KITS_DIR}')
    return out


def scalar_params(entry, limit=40):
    """An entry's measures as [key, value] pairs: numbers, short words and short lists, flattened
    one level (`module.slate_width_m`). Prose stays in `note`; nothing is reworded."""
    rows = []

    def put(key, v):
        if len(rows) >= limit:
            return
        if isinstance(v, bool) or isinstance(v, (int, float)):
            rows.append([key, v])
        elif isinstance(v, str) and len(v) <= 80:
            rows.append([key, v])
        elif isinstance(v, list) and v and len(v) <= 6 and all(isinstance(x, (int, float, str)) and not isinstance(x, bool) for x in v) \
                and all(len(str(x)) <= 40 for x in v):
            rows.append([key, v])

    for k, v in entry.items():
        if k in PROSE or k.startswith('_'):
            continue
        if isinstance(v, dict):
            for k2, v2 in v.items():
                if k2 not in PROSE and not k2.startswith('_'):
                    put(f'{k}.{k2}', v2)
        else:
            put(k, v)
    return rows


def collections_of(kit):
    """Every list of id'd entries and every table of named entries the kit file holds."""
    out = []
    for key, v in kit.items():
        if key.startswith('_') or key in ('costs',):
            continue
        items = None
        if isinstance(v, list) and v and all(isinstance(x, dict) and ('id' in x or 'family' in x) for x in v):
            items = [(x.get('id') or x['family'], x) for x in v]
        elif isinstance(v, dict) and len(v) >= 3 and all(isinstance(x, dict) for x in v.values()):
            items = list(v.items())
        if not items:
            continue
        rows = []
        for ident, entry in items:
            note = entry.get('note') or entry.get('meaning') or entry.get('_doc') or ''
            rows.append({'id': ident, 'confidence': entry.get('confidence'),
                         'note': note if isinstance(note, str) else '',
                         'params': scalar_params(entry)})
        out.append({'key': key, 'items': rows})
    return out


def glb_nodes(path):
    """The specimen's named root nodes, which the generator names after the variant they hold."""
    b = path.read_bytes()
    if b[:4] != b'glTF':
        return []
    n = int.from_bytes(b[12:16], 'little')
    j = json.loads(b[20:20 + n])
    scene = j.get('scenes', [{}])[j.get('scene', 0)]
    nodes = j.get('nodes', [])
    return [nodes[i].get('name') for i in scene.get('nodes', []) if nodes[i].get('name')]


def specimen_of(kit):
    rel = kit.get('specimen')
    if isinstance(rel, str) and rel.endswith('.glb') and (ROOT / rel).is_file():
        return ROOT / rel
    return None


def study_of(code, kit):
    if code in STUDY and (RESEARCH / STUDY[code]).is_file():
        return RESEARCH / STUDY[code]
    for key in ('specimen', 'study'):
        rel = kit.get(key)
        if isinstance(rel, str):
            p = ROOT / rel
            folder = p if p.is_dir() else p.parent
            if (folder / 'study.jpg').is_file():
                return folder / 'study.jpg'
    return None


def walk(o, path=()):
    """Every string value with the keys above it."""
    if isinstance(o, str):
        yield o, path
    elif isinstance(o, dict):
        for k, v in o.items():
            yield from walk(v, path + (str(k),))
    elif isinstance(o, list):
        for v in o:
            yield from walk(v, path)


def kit_ids(kits):
    """{code: {prefixed ids}}, {code: {bare library ids}} from the kit files themselves."""
    prefixed, bare = defaultdict(set), defaultdict(set)
    for code, kit in kits.items():
        for col in collections_of(kit):
            for item in col['items']:
                ident = item['id']
                if re.match(r'^k\d\d\.', ident):
                    prefixed[code].add(ident)
                elif code in LIBRARY_KEY:
                    bare[code].add(ident)
    return prefixed, bare


def sidecar_for(sid):
    for y in YEARS:
        p = ROOT / 'data/sidecars' / y / f'{sid}.json'
        if p.is_file():
            return y, json.loads(p.read_text())
    return None, None


def houses_of(kits):
    prefixed, bare = kit_ids(kits)
    prefix_owner = {i: c for c, s in prefixed.items() for i in s}
    houses = []
    for f in sorted((ROOT / 'data/structures').glob('*.json')):
        rec = json.loads(f.read_text())
        used = defaultdict(set)
        code = ARCHETYPE_KIT.get(rec.get('archetype'))
        if code:
            used[code]
        for s, path in walk(rec):
            if s in prefix_owner:
                used[prefix_owner[s]].add(s)
            elif s == 'k14_condition':
                used['K14']
            else:
                for c, ids in bare.items():
                    if s in ids and any(LIBRARY_KEY[c].search(k) for k in path):
                        used[c].add(s)
        if not used:
            continue
        year, side = sidecar_for(rec['id'])
        if not side or not side.get('asset'):
            continue                       # a record no scene draws is not shown as a model
        asset = side['asset']
        if not (ROOT / 'assets/web' / Path(asset).name).is_file():
            continue
        grade = side.get('grade') or {}
        houses.append({
            'id': rec['id'], 'year': year,
            'name': side.get('called') or side.get('name') or rec.get('name') or rec['id'],
            'aka': side.get('aka') or [],
            'archetype': rec.get('archetype'),
            'asset': asset,
            'grade': grade.get('value'), 'grade_why': grade.get('why'),
            'kits': sorted(used),
            'parts': {c: sorted(v) for c, v in sorted(used.items()) if v},
            'record': REPO_BLOB + f'data/structures/{f.name}',
        })
    houses.sort(key=lambda h: (YEARS.index(h['year']), h['name']))
    return houses


def build(out: Path):
    kits = {c: json.loads(p.read_text()) for c, p in kit_files().items()}
    files = kit_files()
    houses = houses_of(kits)
    (out / 'specimens').mkdir(parents=True, exist_ok=True)
    (out / 'studies').mkdir(parents=True, exist_ok=True)
    rows = []
    for code in sorted(KITS):
        kit = kits[code]
        short, line = KITS[code]
        spec = specimen_of(kit)
        spec_rel = None
        nodes = []
        if spec:
            spec_rel = f'specimens/{spec.name}'
            shutil.copyfile(spec, out / spec_rel)
            nodes = glb_nodes(spec)
        study = study_of(code, kit)
        study_rel = None
        if study:
            study_rel = f'studies/{code.lower()}.jpg'
            write_study(study, out / study_rel)
        users = [h['id'] for h in houses if code in h['kits']]
        part_users = defaultdict(list)
        for h in houses:
            for p in h['parts'].get(code, []):
                part_users[p].append(h['id'])
        readme = None
        for key in ('specimen', 'study'):
            rel = kit.get(key)
            if isinstance(rel, str):
                folder = (ROOT / rel) if (ROOT / rel).is_dir() else (ROOT / rel).parent
                if (folder / 'README.md').is_file():
                    readme = REPO_BLOB + str((folder / 'README.md').relative_to(ROOT))
        if not readme and code in STUDY and (RESEARCH / STUDY[code]).parent.joinpath('README.md').is_file():
            readme = REPO_BLOB + str((RESEARCH / STUDY[code]).parent.joinpath('README.md').relative_to(ROOT))
        gen = kit.get('generator') if isinstance(kit.get('generator'), str) else None
        rows.append({
            'code': code, 'name': short, 'line': line,
            'title': kit.get('title', ''), 'ticket': kit.get('ticket'),
            'rule': kit.get('rule') if isinstance(kit.get('rule'), str) else '',
            'file': REPO_BLOB + str(files[code].relative_to(ROOT)),
            'generator': REPO_BLOB + gen if gen and (ROOT / gen).is_file() else None,
            'readme': readme,
            'specimen': spec_rel, 'specimen_bytes': spec.stat().st_size if spec else 0,
            'specimen_nodes': nodes,
            'study': study_rel,
            'collections': collections_of(kit),
            'houses': users,
            'part_houses': dict(sorted(part_users.items())),
        })
    data = {
        'schema': 1,
        'ticket': 'T-3750',
        'note': 'Derived by tools/architecture_site.py from data/components/prairie_1904/k*.json, '
                'data/structures/ and data/sidecars/. Nothing here is typed by hand.',
        'commit': commit(),
        'kits': rows,
        'houses': houses,
    }
    (out / 'data.json').write_text(json.dumps(data, separators=(',', ':'), ensure_ascii=False) + '\n')
    return data


def write_study(src: Path, dst: Path):
    try:
        from PIL import Image
    except ImportError:                    # no Pillow: ship the committed picture as it is
        shutil.copyfile(src, dst)
        return
    with Image.open(src) as im:
        im = im.convert('RGB')
        if im.width > 1600:
            im = im.resize((1600, round(im.height * 1600 / im.width)), Image.LANCZOS)
        im.save(dst, 'JPEG', quality=82, optimize=True, progressive=True)


def commit():
    try:
        return subprocess.run(['git', '-C', str(ROOT), 'rev-parse', '--short', 'HEAD'],
                              capture_output=True, text=True, check=True).stdout.strip()
    except Exception:
        return ''


def check():
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        data = build(out)
        problems = []
        if [k['code'] for k in data['kits']] != sorted(KITS):
            problems.append('kits are not K01..K16 in order')
        for k in data['kits']:
            if k['specimen'] and not (out / k['specimen']).is_file():
                problems.append(f"{k['code']}: specimen {k['specimen']} not written")
            if k['specimen'] and not k['specimen_nodes']:
                problems.append(f"{k['code']}: specimen has no named nodes to pick")
            if not k['collections'] and k['code'] != 'K01':
                problems.append(f"{k['code']}: no collection of parts read")
            for h in k['houses']:
                if not any(x['id'] == h for x in data['houses']):
                    problems.append(f"{k['code']}: house {h} not in the house list")
        for h in data['houses']:
            if not (ROOT / 'assets/web' / Path(h['asset']).name).is_file():
                problems.append(f"{h['id']}: model {h['asset']} not in assets/web")
        if len(data['houses']) < 50:
            problems.append(f"only {len(data['houses'])} houses read as kit-built; expected the Prairie Avenue programme")
        size = sum(p.stat().st_size for p in out.rglob('*') if p.is_file())
        print(f"architecture site: {len(data['kits'])} kits, {len(data['houses'])} houses, "
              f"{sum(1 for k in data['kits'] if k['specimen'])} specimens, {size / 1048576:.2f} MiB")
        for p in problems:
            print('architecture site: ' + p, file=sys.stderr)
        return 1 if problems else 0


if __name__ == '__main__':
    args = sys.argv[1:]
    if args == ['--check']:
        sys.exit(check())
    if len(args) != 1:
        print('\n'.join(__doc__.strip().splitlines()[-2:]), file=sys.stderr)
        sys.exit(2)
    d = build(Path(args[0]))
    print(f"   architecture: {len(d['kits'])} kits, {len(d['houses'])} houses -> {args[0]}")
