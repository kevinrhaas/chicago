#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Exercise the animation-only derivation against real canonical parent bytes."""
import copy
import json
import math
from pathlib import Path
import unittest

import human_natural_idle as idle
import human_seated_look as seated


class NaturalStanding(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.recipe = json.loads(idle.RECIPE.read_text())
        cls.row = cls.recipe['parents'][0]
        cls.raw = idle.parent_bytes(cls.row, cls.recipe)
        cls.doc, cls.binary = idle.parse(cls.raw)
        cls.bases = idle.source_pose(cls.doc, cls.binary)

    def test_real_parent_protected_and_deterministic(self):
        out, proof = idle.append_clip(self.raw, self.row['sha256'], self.bases, self.recipe)
        repeated, _ = idle.append_clip(self.raw, self.row['sha256'], self.bases, self.recipe)
        self.assertEqual(out, repeated)
        doc, binary = idle.parse(out)
        self.assertEqual(binary[:len(self.binary)], self.binary)
        for key in ('nodes', 'meshes', 'skins', 'images', 'materials', 'textures', 'scenes'):
            self.assertEqual(doc.get(key), self.doc.get(key), key)
        self.assertEqual(doc['animations'][:-1], self.doc['animations'])
        new = doc['animations'][-1]
        self.assertEqual(new['name'], idle.CLIP)
        for old, now in zip(self.doc['animations'][0]['channels'], new['channels']):
            name = self.doc['nodes'][old['target']['node']].get('name')
            if name not in idle.TARGETS or old['target']['path'] != 'rotation':
                self.assertEqual(new['samplers'][now['sampler']], self.doc['animations'][0]['samplers'][old['sampler']])
        self.assertTrue(proof['lower_body_channels_unchanged'])

    def test_exact_loop_and_real_upper_body_motion(self):
        for name in idle.TARGETS:
            rows = idle.authored_rows(name, self.bases, self.recipe)
            self.assertEqual(rows[0], rows[-1])
            self.assertTrue(all(abs(sum(x*x for x in row)-1) < 1e-12 for row in rows))
            self.assertGreater(max(math.dist(rows[0], row) for row in rows), .001, name)

    def test_master_web_clip_metadata_share_actual_pose_source(self):
        # All authored curves use the master-LOD0 rig pose. Per-file source
        # identity belongs in the derivation receipt, not shared clip metadata.
        master, master_proof = idle.append_clip(self.raw, self.row['sha256'], self.bases, self.recipe)
        row = self.recipe['parents'][4]
        web, web_proof = idle.append_clip(idle.parent_bytes(row, self.recipe), row['sha256'], self.bases, self.recipe)
        master_extras = idle.parse(master)[0]['animations'][-1]['extras']
        self.assertEqual(master_extras, idle.parse(web)[0]['animations'][-1]['extras'])
        self.assertEqual(master_extras['canonical_rig_pose_parent_sha256'], self.row['sha256'])
        self.assertNotIn('canonical_parent_sha256', master_extras)
        self.assertEqual(master_proof['parent_sha256'], self.row['sha256'])
        self.assertEqual(web_proof['parent_sha256'], row['sha256'])

    def test_changed_parent_refused(self):
        changed = bytearray(self.raw)
        changed[-1] ^= 1
        with self.assertRaisesRegex(ValueError, 'parent SHA'):
            idle.append_clip(bytes(changed), self.row['sha256'], self.bases, self.recipe)

    def test_wrong_parent_identity_refused(self):
        with self.assertRaisesRegex(ValueError, 'parent SHA'):
            idle.append_clip(self.raw, '0'*64, self.bases, self.recipe)

    def test_missing_head_channel_refused(self):
        doc = copy.deepcopy(self.doc)
        ni = next(i for i, n in enumerate(doc['nodes']) if n.get('name') == 'head')
        doc['animations'][0]['channels'] = [c for c in doc['animations'][0]['channels'] if c['target'] != {'node': ni, 'path': 'rotation'}]
        with self.assertRaisesRegex(ValueError, 'missing'):
            idle.source_pose(doc, self.binary)

    def test_compressed_master_channel_refused(self):
        doc = copy.deepcopy(self.doc)
        c = next(c for c in doc['animations'][0]['channels'] if c['target']['path'] == 'rotation')
        acc = doc['accessors'][doc['animations'][0]['samplers'][c['sampler']]['output']]
        doc['bufferViews'][acc['bufferView']]['extensions'] = {'EXT_meshopt_compression': {}}
        with self.assertRaisesRegex(ValueError, 'uncompressed'):
            idle.source_pose(doc, self.binary)

    def test_incomplete_glb_refused(self):
        with self.assertRaisesRegex(ValueError, 'complete GLB'):
            idle.parse(self.raw[:-4])

    def test_duplicate_derivation_refused(self):
        out, _ = idle.append_clip(self.raw, self.row['sha256'], self.bases, self.recipe)
        with self.assertRaisesRegex(ValueError, 'already installed'):
            idle.append_clip(out, idle.sha(out), self.bases, self.recipe)


class SeatedLooking(unittest.TestCase):
    def test_standing_reproduction_remains_exact_seated_parent(self):
        recipe = json.loads(idle.RECIPE.read_text())
        row = recipe['parents'][0]
        raw = idle.parent_bytes(row, recipe)
        original, _ = idle.append_clip(raw, row['sha256'], idle.source_pose(*idle.parse(raw)), recipe)
        seated_recipe = seated.read_recipe()
        selected = next(p for p in seated_recipe['parents'] if p['file'] == row['file'])
        self.assertEqual(idle.sha(original), selected['sha256'])
        chained = seated.chained_active_derivative(row['file'], original)
        self.assertEqual(chained, seated.derive(selected, seated_recipe)[0])
        changed = bytearray(original)
        changed[-1] ^= 1
        with self.assertRaisesRegex(ValueError, 'exact standing-to-seated parent chain'):
            seated.chained_active_derivative(row['file'], bytes(changed))
        with self.assertRaisesRegex(ValueError, 'exact standing-to-seated parent chain'):
            seated.chained_active_derivative('assets/humans/bardwell_otis_1835.lod1.glb', original)

    def test_actual_seated_parents_and_protected_channels(self):
        recipe = seated.read_recipe()
        masters = [row for row in recipe['parents'] if not row['web']]
        self.assertEqual(len(masters), 4)
        for row in masters:
            raw = seated.parent_bytes(row, recipe)
            doc, binary = seated.parse(raw)
            bases = seated.seated_pose(raw)
            result, proof = seated.append_clip(raw, row['sha256'], bases, recipe)
            repeated, _ = seated.append_clip(raw, row['sha256'], bases, recipe)
            self.assertEqual(result, repeated)
            child, child_bin = seated.parse(result)
            self.assertEqual(child_bin[:len(binary)], binary)
            self.assertEqual(child['animations'][:-1], doc['animations'])
            old = next(a for a in doc['animations'] if a['name'] == 'sit_drive')
            new = child['animations'][-1]
            self.assertEqual(len(new['channels']), len(old['channels']))
            self.assertEqual(new['channels'], old['channels'])
            changed = []
            for channel in old['channels']:
                target = channel['target']
                name = doc['nodes'][target['node']].get('name')
                if target['path'] == 'rotation' and name in seated.TARGETS:
                    changed.append(name)
                    sampler = new['samplers'][channel['sampler']]
                    rows = idle.float_rows(child, child_bin, sampler['output'], 'VEC4')
                    self.assertEqual(len(rows), 65)
                    self.assertEqual(rows[0], rows[-1])
                    self.assertGreater(max(math.dist(rows[0], r) for r in rows), .001)
                else:
                    self.assertEqual(new['samplers'][channel['sampler']], old['samplers'][channel['sampler']])
            self.assertEqual(sorted(changed), sorted(seated.TARGETS))
            self.assertTrue(proof['non_head_neck_channels_unchanged'])

    def test_invalid_timing_or_angles_refused_before_derivation(self):
        for field, value in [('duration_s', 0), ('samples', 64), ('motion_degrees', {})]:
            recipe = copy.deepcopy(seated.read_recipe())
            recipe[field] = value
            with self.assertRaisesRegex(ValueError, 'reviewed'):
                seated.validate_recipe(recipe)

    def test_wrong_or_changed_parent_refused(self):
        recipe = seated.read_recipe()
        row = recipe['parents'][0]
        raw = seated.parent_bytes(row, recipe)
        bases = seated.seated_pose(raw)
        with self.assertRaisesRegex(ValueError, 'parent SHA'):
            seated.append_clip(raw, '0'*64, bases, recipe)
        changed = bytearray(raw)
        changed[-1] ^= 1
        with self.assertRaisesRegex(ValueError, 'parent SHA'):
            seated.append_clip(bytes(changed), row['sha256'], bases, recipe)


if __name__ == '__main__':
    unittest.main()
