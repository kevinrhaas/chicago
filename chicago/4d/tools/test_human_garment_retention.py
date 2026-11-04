#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Exact regeneration and negative controls for the explicit terminal chain.

Prepared outside APP. Requires the real, fully bound recipe before execution.
"""
import copy
from pathlib import Path

import human_garment_retention as stage


def rejects(label, operation):
    try:
        operation()
    except (ValueError, AssertionError):
        return
    raise AssertionError(label + ' unexpectedly accepted')


def main():
    recipe = stage.read_recipe()
    parent_by_file = {}
    for row in recipe['terminals'] + recipe['passthrough']:
        parent = stage.reproduce_seated(row['file'])
        expected_parent = row.get('parent_sha256', row.get('sha256'))
        assert stage.sha(parent) == expected_parent
        child = stage.apply(row['file'], parent, recipe)
        assert (stage.APP / row['file']).read_bytes() == child
        parent_by_file[row['file']] = parent
        if 'output_sha256' in row:
            assert child != parent
            rejects('already transformed input', lambda: stage.apply(row['file'], child, recipe))
        else:
            assert child == parent
        # The first byte is inside the GLB magic, so corruption is not an
        # incidental geometry difference. It must be refused before derivation.
        broken = bytes([parent[0] ^ 1]) + parent[1:]
        rejects('wrong exact input', lambda: stage.apply(row['file'], broken, recipe))

    duplicate = copy.deepcopy(recipe)
    duplicate['terminals'][1] = copy.deepcopy(duplicate['terminals'][0])
    rejects('duplicate terminal', lambda: stage.validate_recipe(duplicate))
    foreign = copy.deepcopy(recipe)
    foreign['terminals'][0]['file'] = 'assets/humans/unlisted_person.lod3.glb'
    rejects('unlisted parent', lambda: stage.validate_recipe(foreign))
    row = recipe['terminals'][0]
    rejects('unlisted direct transform', lambda: stage.apply('assets/humans/unlisted_person.lod3.glb', parent_by_file[row['file']], recipe))
    wrong_donor = copy.deepcopy(recipe)
    wrong_donor['terminals'][0]['donor_sha256'] = '0' * 64
    rejects('wrong donor', lambda: stage.apply(row['file'], parent_by_file[row['file']], wrong_donor))
    wrong_child = copy.deepcopy(recipe)
    wrong_child['terminals'][0]['output_sha256'] = row['parent_sha256']
    rejects('expected-hash-only waiver', lambda: stage.apply(row['file'], parent_by_file[row['file']], wrong_child))
    wrong_route = copy.deepcopy(recipe)
    wrong_route['web_transform'] = 'raw_copy_v1'
    rejects('rejected raw-copy route', lambda: stage.validate_recipe(wrong_route))
    unbound = copy.deepcopy(recipe)
    unbound['installed'] = False
    rejects('unbound preparation', lambda: stage.validate_recipe(unbound))
    print('terminal garment chain: exact historical standing/seated regeneration, four real derivatives, four exact no-ops, corruption/duplicate/unlisted/wrong-donor/wrong-output/double-apply controls PASS')


if __name__ == '__main__':
    main()
