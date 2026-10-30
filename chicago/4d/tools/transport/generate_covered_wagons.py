#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Rebuild only the two reviewed EMPTY covered W01 variants from original source."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / 'tools/transport'


def need(ok, message):
    if not ok:
        raise ValueError(message)


def run(script, *args):
    result = subprocess.run([sys.executable, str(script), *map(str, args)],
                            capture_output=True, text=True)
    need(result.returncode == 0, result.stderr[-6000:])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--parameters', type=Path, default=ROOT/'data/transport/parked/covered-w01.json')
    parser.add_argument('--output-dir', type=Path, default=ROOT/'renderers/web/transport/covered-wagon')
    parser.add_argument('--texture-output-dir', type=Path,
                        default=ROOT/'assets/authored/transport/wagon_covered/textures')
    parser.add_argument('--verify', action='store_true')
    args = parser.parse_args()
    recipe = json.loads(args.parameters.read_text())
    source = json.loads((ROOT/'assets/authored/transport/wagon_covered/SOURCE.json').read_text())
    need(len(recipe['variants']) == 2, 'Only the two reviewed variants are supported')
    core = TOOLS/'wagon_covered/build.py'
    need(hashlib.sha256(core.read_bytes()).hexdigest() == source['core_source_sha256'],
         'Covered source differs from reviewed producer')
    with tempfile.TemporaryDirectory(prefix='covered-w01-') as directory:
        tmp = Path(directory)
        # Rebuild the parent; a cached exported parent is never a production input.
        parent_recipe = ROOT/'data/transport/parked/wagon-w01.json'
        run(TOOLS/'generate_parked_wagon.py', '--parameters', parent_recipe,
            '--output-dir', tmp/'parent')
        hardware = json.loads(parent_recipe.read_text())['base_study']['hardware_parameters']
        (tmp/'hardware.json').write_text(json.dumps(hardware))
        run(TOOLS/'wagon_parked/generate_wagon_hardware.py', '--parameters', tmp/'hardware.json',
            '--output-dir', tmp/'hardware')
        run(core, '--parent', tmp/'parent/wagon-w01.glb', '--authored-parts',
            tmp/'hardware/authored-parts.json', '--parameters', args.parameters,
            '--output', tmp/'covered')
        products = []
        for variant in source['variants']:
            folder = tmp/'covered'/variant['model']
            for filename, expected in [('covered-w01.glb', variant['glb_sha256']),
                                       ('covered-w01.json', variant['sidecar_sha256'])]:
                raw = (folder/filename).read_bytes()
                need(hashlib.sha256(raw).hexdigest() == expected, 'Reviewed product changed: '+filename)
                products.append((args.output_dir/variant['model']/filename, raw))
        products.extend((args.texture_output_dir/p.name, p.read_bytes())
                        for p in sorted((tmp/'covered/original-canvas-textures').glob('*.png')))
        for target, raw in products:
            if args.verify:
                need(target.is_file() and target.read_bytes() == raw, 'Stale or missing '+str(target))
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(raw)
        print(json.dumps({'verified': args.verify, 'variants': len(source['variants']),
                          'products': len(products), 'mapped_RGBA8_mips_bytes_each': 8388608,
                          'scope': 'Original empty source reproduction, not placement or photographic acceptance'}))


if __name__ == '__main__':
    main()
