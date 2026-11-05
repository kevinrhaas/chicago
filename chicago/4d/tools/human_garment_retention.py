#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Reproduce four explicit garment terminals after exact standing/seated stages.

This transform retains the LOD0 shirt and trousers on LOD3. It does not establish
native garment fit, contacts, world cost or photographic acceptance.
"""
import argparse
import functools
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tempfile

if not __debug__:
    raise RuntimeError('Garment invariant assertions require ordinary Python execution')

APP = Path(__file__).resolve().parents[1]
RECIPE = APP / 'data/humans/animations/driver-garment-retention-v2.json'
PARENT_REVISION = 'edfc3edc60cf00a8cf2376419d0df8fc3cd8b0a3'
ASSETS = ('bardwell_otis_1835', 'anonymous_working_driver_1904')
MATERIALS = ['garment_upper__shirt_linen', 'garment_lower__highwaist_pantaloons']
FILES = {f'assets/humans/{web}{asset}.lod{lod}.glb'
         for web in ('', 'web/') for asset in ASSETS for lod in (0, 3)}


def require(value, message):
    if not value:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def validate_recipe(recipe):
    require(recipe.get('schema') == 'portable_driver_terminal_garments_v2', 'explicit terminal recipe required')
    require(recipe.get('installed') is True, 'prepared/unbound garment recipe cannot execute')
    require(recipe.get('parent_revision') == PARENT_REVISION, 'exact immutable seated parent revision required')
    require(recipe.get('materials') == MATERIALS, 'exact two reviewed garments required')
    require(recipe.get('encoding') == {
        'master': 'python_json_compact_utf8_glb_padding_v1',
        'web': 'javascript_JSON_stringify_glb_padding_v1'}, 'explicit domain-specific GLB encoding required')
    require(recipe.get('web_transform') == 'single_skin_weighted_rebind_v3'
            and recipe.get('maximum_web_position_residual_m') == 1e-6,
            'fixed admitted one-skin rebind route and residual required')
    require(set(recipe['admission_evidence_sha256']) == {
        'master_prototype', 'master_native_render',
        'web_single_skin_rebind_v3', 'web_native_render_v3'}, 'all finite input admission receipts must be recorded')
    require(all(isinstance(digest, str) and re.fullmatch('[0-9a-f]{64}', digest)
                for digest in recipe['admission_evidence_sha256'].values()),
            'unbound input admission receipt refused')
    terminals, passthrough = recipe['terminals'], recipe['passthrough']
    require(len(terminals) == len(passthrough) == 4, 'four LOD3 terminals and four LOD0 passthroughs required')
    paths = [row['file'] for row in terminals + passthrough]
    require(len(set(paths)) == len(paths) and set(paths) == FILES, 'duplicate or unlisted terminal path refused')
    for row in terminals:
        require(row['file'].endswith('.lod3.glb'), 'only current LOD3 may be changed')
        require(row['asset_id'] in ASSETS and row['file'] ==
                f"assets/humans/{'web/' if row['domain'] == 'web' else ''}{row['asset_id']}.lod3.glb",
                'terminal identity and path must agree')
        require(row['donor_file'] == row['file'].replace('.lod3.glb', '.lod0.glb'), 'same WEB/MASTER resident LOD0 donor required')
        require(row['domain'] == ('web' if '/web/' in row['file'] else 'master'), 'explicit matching data domain required')
        for key in ('parent_sha256', 'donor_sha256', 'output_sha256'):
            require(isinstance(row[key], str) and re.fullmatch('[0-9a-f]{64}', row[key]), 'bound exact digest required: ' + key)
    for row in passthrough:
        require(row['file'].endswith('.lod0.glb') and re.fullmatch('[0-9a-f]{64}', row['sha256']), 'exact LOD0 passthrough required')
    require(set(recipe['implementation_sha256']) == {
        'tools/human_garment_retention_master.py',
        'tools/human_garment_retention_web.mjs',
        'tools/human_garment_retention_web_helpers.mjs',
        'tools/human_garment_retention_rebind_math.mjs'}, 'explicit copier implementation pins required')
    for path, digest in recipe['implementation_sha256'].items():
        require(sha((APP / path).read_bytes()) == digest, 'garment implementation changed: ' + path)
    runtime_files = {
        'renderers/web/vendor/three-0.185.1/three.module.js',
        'renderers/web/vendor/three-0.185.1/three.core.js',
        'renderers/web/vendor/three-0.185.1/addons/loaders/GLTFLoader.js',
        'renderers/web/vendor/three-0.185.1/addons/libs/meshopt_decoder.module.js',
        'renderers/web/vendor/three-0.185.1/addons/utils/BufferGeometryUtils.js',
        'renderers/web/vendor/three-0.185.1/addons/utils/SkeletonUtils.js'}
    require(set(recipe['runtime_sha256']) == runtime_files, 'exact repo-relative native runtime pins required')
    for path, digest in recipe['runtime_sha256'].items():
        require(sha((APP / path).read_bytes()) == digest, 'native reproduction runtime changed: ' + path)
    for path, digest in recipe['historical_recipe_sha256'].items():
        require(path in ('data/humans/animations/natural-standing-v1.json',
                         'data/humans/animations/seated-driver-look-v2.json'), 'unlisted historical recipe refused')
        require(sha((APP / path).read_bytes()) == digest, 'historical animation recipe changed: ' + path)
    require(len(recipe['historical_recipe_sha256']) == 2, 'both historical animation recipes required')


def read_recipe():
    recipe = json.loads(RECIPE.read_text())
    validate_recipe(recipe)
    return recipe


@functools.lru_cache(maxsize=8)
def reproduce_seated(file):
    """Rebuild each recorded animation lineage from immutable inputs, not active files."""
    import human_natural_idle as standing
    import human_seated_look as seated
    standing_recipe = json.loads(standing.RECIPE.read_text())
    seated_recipe = seated.read_recipe()
    standing_rows = [r for r in standing_recipe['parents'] if r['file'] == file]
    seated_rows = [r for r in seated_recipe['parents'] if r['file'] == file]
    require(len(seated_rows) == 1, 'one exact historical seated parent required')
    if not standing_rows:
        # Hans was already a canonical seated actor. Do not invent the Otis-only
        # natural-standing stage or change any historical parent/recipe value.
        canonical_seated = {f'assets/humans/{prefix}anonymous_working_driver_1904.lod{lod}.glb'
                            for prefix in ('', 'web/') for lod in (0, 3)}
        require(file in canonical_seated, 'unlisted historical animation lineage refused')
        return seated.derive(seated_rows[0], seated_recipe)[0]
    require(len(standing_rows) == 1, 'one exact historical standing parent required')
    row, next_row = standing_rows[0], seated_rows[0]
    master = standing_recipe['parents'][0]
    bases = standing.source_pose(*standing.parse(standing.parent_bytes(master, standing_recipe)))
    original, _ = standing.append_clip(standing.parent_bytes(row, standing_recipe), row['sha256'], bases, standing_recipe)
    require(sha(original) == next_row['sha256'], 'exact standing-to-seated bridge failed')
    pose_row = next(r for r in standing_recipe['parents'] if r['file'] == next_row['pose_parent_file'])
    pose_raw, _ = standing.append_clip(standing.parent_bytes(pose_row, standing_recipe), pose_row['sha256'], bases, standing_recipe)
    expected_pose = next(r for r in seated_recipe['parents'] if r['file'] == next_row['pose_parent_file'])
    require(sha(pose_raw) == expected_pose['sha256'], 'exact reconstructed seated pose parent failed')
    result, _ = seated.append_clip(original, next_row['sha256'], seated.seated_pose(pose_raw), seated_recipe)
    return result


def apply(file, original, recipe=None):
    recipe = read_recipe() if recipe is None else recipe
    validate_recipe(recipe)
    matches = [row for row in recipe['terminals'] if row['file'] == file]
    unchanged = [row for row in recipe['passthrough'] if row['file'] == file]
    if unchanged:
        require(len(unchanged) == 1 and not matches and sha(original) == unchanged[0]['sha256'], 'wrong no-op input refused')
        return original
    require(len(matches) == 1, 'unlisted terminal input refused')
    row = matches[0]
    require(sha(original) == row['parent_sha256'], 'wrong or already transformed seated parent refused')
    donor = reproduce_seated(row['donor_file'])
    require(sha(donor) == row['donor_sha256'], 'immutable donor does not reproduce')
    with tempfile.TemporaryDirectory(prefix='human-garment-retention-') as scratch:
        scratch = Path(scratch)
        parent_path, donor_path, output_path = scratch / 'parent.glb', scratch / 'donor.glb', scratch / 'child.glb'
        parent_path.write_bytes(original)
        donor_path.write_bytes(donor)
        if row['domain'] == 'master':
            from human_garment_retention_master import candidate
            result, _ = candidate(dict(asset=row['asset_id'], lod0_master=str(donor_path),
                lod0_master_SHA256=row['donor_sha256'], lod3_master=str(parent_path),
                lod3_master_SHA256=row['parent_sha256']), recipe['materials'])
        else:
            subprocess.run(['node', str(APP / 'tools/human_garment_retention_web.mjs'), str(APP),
                str(parent_path), str(donor_path), row['parent_sha256'], row['donor_sha256'], str(output_path)],
                check=True, timeout=60)
            result = output_path.read_bytes()
    require(sha(result) == row['output_sha256'], 'terminal garment output does not reproduce')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--check', action='store_true')
    mode.add_argument('--output', type=Path)
    args = parser.parse_args()
    recipe = read_recipe()
    if not args.check:
        out = args.output.resolve()
        require(not out.exists() and not out.is_relative_to(APP), 'fresh separate output directory required')
    results = []
    for row in recipe['terminals'] + recipe['passthrough']:
        parent = reproduce_seated(row['file'])
        expected_parent = row.get('parent_sha256', row.get('sha256'))
        require(sha(parent) == expected_parent, 'historical seated parent does not reproduce: ' + row['file'])
        result = apply(row['file'], parent, recipe)
        if args.check:
            require((APP / row['file']).read_bytes() == result, 'active garment terminal does not reproduce: ' + row['file'])
        results.append((row['file'], result))
    if not args.check:
        out.mkdir(parents=True, exist_ok=False)
        for file, result in results:
            destination = out / file
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(result)
        inputs = {row['file']: row.get('parent_sha256', row.get('sha256'))
                  for row in recipe['terminals'] + recipe['passthrough']}
        receipt = dict(schema='human_garment_retention_derivation_v1',
            recipe_sha256=sha(RECIPE.read_bytes()), generator_sha256=sha(Path(__file__).read_bytes()),
            implementation_sha256=recipe['implementation_sha256'], parent_revision=PARENT_REVISION,
            files=[dict(file=file, parent_sha256=inputs[file], sha256=sha(result),
                        bytes=len(result), changed=file.endswith('.lod3.glb'))
                   for file, result in results],
            native_garment_fit_or_contact_or_world_qualified=False, photographic_accepted=False)
        (out / 'DERIVATION.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(dict(reproduced=len(results), changed=4, checked=args.check,
        native_garment_fit_or_contact_or_world_qualified=False, photographic_accepted=False)))


if __name__ == '__main__':
    main()
