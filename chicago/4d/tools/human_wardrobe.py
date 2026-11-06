# SPDX-License-Identifier: GPL-3.0-or-later
"""Dress portable humans from their wardrobe recipes (T-3409, the wardrobe kit).

Each recipe in data/humans/wardrobes/ names a body master, the held pose it is
dressed in, the vehicle it sits on and its garments, each garment with its grade
and its sources or liberty; tools/wardrobe_kit.py cuts, lofts, drapes, fits and
skins them. The renderer binds the file by its sha256 (data/transport/driven/
loops.json) and to the loaded body's bones by name (renderers/web/js/driver-livery.js).

  python3 tools/human_wardrobe.py RECIPE_ID ...   write those wardrobe files
  python3 tools/human_wardrobe.py --all           write every wardrobe file
  python3 tools/human_wardrobe.py --check         hold every committed file to its
                                                  recipe, its inputs and its body

A rerun changes the file's bytes, so rebind the driven row's driver_livery_sha256
afterwards (the check and tools/test_driver_livery.mjs refuse a stale binding).
"""
from __future__ import annotations

import argparse, json, sys
from pathlib import Path

APP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP / 'tools'))
import wardrobe_kit as K  # noqa: E402

DIR = 'data/humans/wardrobes'


def recipes():
    out = {}
    for p in sorted((APP / DIR).glob('*.json')):
        r = json.loads(p.read_text())
        out[r['id']] = (r, f'{DIR}/{p.name}')
    return out


def write(recipe, path):
    errors = K.provenance_errors(recipe)
    if errors: raise SystemExit('wardrobe: ' + '; '.join(errors))
    S, parts, fits, tails = K.build(recipe)
    text = json.dumps(K.document(recipe, path, S, parts, fits, tails), separators=(',', ':')) + '\n'
    (APP / recipe['output']).write_text(text)
    print(recipe['id'], json.dumps({p['name']: [len(p['bind']), len(p['faces'])] for p in parts}),
          f'{len(tails)} tails', f'{len(text) / 1e6:.2f} MB')


def check():
    loops = json.loads((APP / 'data/transport/driven/loops.json').read_text())
    bound = {r['driver_livery_file']: r for r in loops['rows'] if r.get('driver_livery_file')}
    failed = False; lines = []
    all_recipes = recipes()
    outputs = {r['output'] for r, _ in all_recipes.values()}
    for f in bound:
        if f'renderers/web/{f}' not in outputs: print(f'wardrobe: {f} is bound by a driven row but no recipe makes it'); failed = True
    for rid, (r, path) in all_recipes.items():
        errors, worst = K.check(r, path, r['check_tolerance_m'])
        row = bound.get(r['output'].removeprefix('renderers/web/'))
        if row:
            got = K.sha((APP / r['output']).read_bytes())
            if row['driver_livery_sha256'] != got: errors.append('its driven row binds other bytes: rebind driver_livery_sha256')
            if row['driver_asset'] != r['asset_id']: errors.append('its driven row drives another person')
            if row['driver_livery_body_sha256'] != json.loads((APP / r['output']).read_text())['body_master_sha256']: errors.append('its driven row binds another body')
        if errors:
            failed = True; print(f'wardrobe {rid}: FAIL\n  ' + '\n  '.join(errors))
        else:
            n = len(r['garments'])
            lines.append(f'{rid}: {n} garments, each with its source or liberty; nothing inside the dressed body or vehicle '
                         '(worst ' + ', '.join(f'{k} {v * 1000:.1f} mm' for k, v in worst.items()) + ')')
    if failed: sys.exit(1)
    print('wardrobe:\n  ' + '\n  '.join(lines) + '\nwardrobe: every committed file matches its recipe, body and vehicle, and the row that binds it: PASS')


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('ids', nargs='*'); ap.add_argument('--all', action='store_true'); ap.add_argument('--check', action='store_true')
    a = ap.parse_args()
    if a.check: check()
    else:
        rs = recipes()
        ids = list(rs) if a.all else a.ids
        if not ids: ap.error('name a recipe id, or --all')
        for i in ids:
            if i not in rs: raise SystemExit(f'wardrobe: no recipe {i} (have {", ".join(rs)})')
            write(*rs[i])
