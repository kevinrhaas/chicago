#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Actual canonical Charles parents, explicit metadata exclusions, no BPy."""
import copy
import json
from pathlib import Path
import struct
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import human_charles_coat as C


def encode(doc, binary):
    text = json.dumps(doc, separators=(',', ':'), allow_nan=False).encode()
    text += b' '*(-len(text) % 4)
    return (struct.pack('<III', 0x46546c67, 2, 28+len(text)+len(binary))
            + struct.pack('<II', len(text), 0x4e4f534a)+text
            + struct.pack('<II', len(binary), 0x004e4942)+binary)


class Regeneration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.recipe, cls.admission = C.load(require_implementation=False)
        cls.row = next(r for r in cls.recipe['parents'] if r['lod'] == 0 and '/web/' not in r['file'])
        cls.raw = C.parent_bytes(cls.row, cls.recipe)

    def mutate(self, fn):
        doc, binary = C.parse(self.raw)
        fn(doc)
        return encode(doc, binary)

    def test_only_enumerated_absolute_master_path_may_change(self):
        fresh = self.mutate(lambda d: d['scenes'][0]['extras']['chicago4d_human'].__setitem__('master', '/fresh-build/charles.blend'))
        proof = C.compatible(self.raw, fresh)
        self.assertNotEqual(proof['fresh_sha256'], proof['canonical_sha256'])
        self.assertTrue(proof['exact_full_BIN_and_all_nonvolatile_JSON'])

    def test_versions_rig_false_identity_hashes_license_and_unknown_proofs_refuse(self):
        mutations = [
            lambda d: d['asset'].__setitem__('generator', 'changed exporter version'),
            lambda d: d['scenes'][0]['extras']['chicago4d_human'].__setitem__('rigid_bone_frame_export', False),
            lambda d: d['scenes'][0]['extras']['chicago4d_human'].__setitem__('sources', ['invented_source']),
            lambda d: d['scenes'][0]['extras']['chicago4d_human'].__setitem__('license', 'different'),
            lambda d: d['scenes'][0]['extras']['chicago4d_human'].__setitem__('skin_source_json', '{"sha256":"changed"}'),
            lambda d: d['scenes'][0]['extras']['chicago4d_human'].__setitem__('verification_reference', '{"master":"/another/path","sha256":"changed"}'),
            lambda d: d['nodes'][0].__setitem__('translation', [0, .001, 0]),
            lambda d: d['animations'][0].__setitem__('name', 'changed_idle'),
        ]
        for mutation in mutations:
            with self.subTest(mutation=mutations.index(mutation)):
                with self.assertRaises(ValueError):
                    C.compatible(self.raw, self.mutate(mutation))

    def test_null_relative_and_new_unenumerated_path_refuse(self):
        for value in (None, 'relative.blend', 123):
            with self.subTest(value=value), self.assertRaises(ValueError):
                C.compatible(self.raw, self.mutate(lambda d: d['scenes'][0]['extras']['chicago4d_human'].__setitem__('master', value)))
        with self.assertRaises(ValueError):
            C.compatible(self.raw, self.mutate(lambda d: d['scenes'][0]['extras']['chicago4d_human'].__setitem__('other_proof_path', '/unlisted/path')))

    def test_real_PN_UV_JW_morph_and_IBM_stream_bytes_refuse(self):
        doc, binary = C.parse(self.raw)
        indices = {k: i for m in doc['meshes'] for p in m['primitives'] for k, i in p['attributes'].items()}
        indices.update({'morph_'+k: i for m in doc['meshes'] for p in m['primitives'] for t in p.get('targets', []) for k, i in t.items()})
        indices['IBM'] = doc['skins'][0]['inverseBindMatrices']
        for name, i in indices.items():
            changed = copy.deepcopy(doc); accessor = changed['accessors'][i]
            mutated = bytearray(binary)
            if 'bufferView' in accessor:
                view = changed['bufferViews'][accessor['bufferView']]
                at = view.get('byteOffset', 0)+accessor.get('byteOffset', 0)
            elif accessor.get('sparse'):
                value = accessor['sparse']['values']; view = changed['bufferViews'][value['bufferView']]
                at = view.get('byteOffset', 0)+value.get('byteOffset', 0)
            else:
                # An actual all-zero morph accessor has no stored view. Make
                # one formerly implicit zero nonzero, preserving its domain.
                self.assertEqual(accessor['componentType'], 5126)
                width = {'VEC3': 3, 'VEC4': 4}[accessor['type']]
                at = len(mutated); size = accessor['count']*width*4
                accessor['bufferView'] = len(changed['bufferViews'])
                changed['bufferViews'].append({'buffer': 0, 'byteOffset': at, 'byteLength': size})
                mutated.extend(b'\0'*size); changed['buffers'][0]['byteLength'] = len(mutated)
            mutated[at] ^= 1
            with self.subTest(stream=name), self.assertRaises(ValueError):
                C.compatible(self.raw, encode(changed, bytes(mutated)))

    def test_complete_real_family_required_and_unknown_active_body_never_reverted(self):
        # Exercise the REAL installed eight-file family: current admitted near
        # children and unchanged FAR. Historical WEB blobs are not inputs to
        # this active-family guard and need not be fetched on blobless CI.
        wanted = {r['file']: r for r in self.admission['outputs']}
        parents = [(r, (C.APP/r['file']).read_bytes()) for r in self.recipe['parents']]
        for row, raw in parents:
            expected = wanted.get(row['file'], row)
            self.assertEqual(C.sha(raw), expected['sha256'])
            self.assertEqual(len(raw), expected['bytes'])
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.assertEqual(C.active_state(root, parents, self.admission['outputs']), 'fresh')
            first, raw = parents[0]; dest = root/first['file'].removeprefix('assets/humans/'); dest.write_bytes(raw)
            with self.assertRaises(ValueError):
                C.active_state(root, parents, self.admission['outputs'])
            for row, raw in parents:
                path = root/row['file'].removeprefix('assets/humans/'); path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(raw)
            self.assertEqual(C.active_state(root, parents, self.admission['outputs']), 'bound')
            dest.write_bytes(dest.read_bytes()+b'changed-body')
            before = {str(f.relative_to(root)): C.sha(f.read_bytes()) for f in root.rglob('*.glb')}
            with self.assertRaises(ValueError):
                C.active_state(root, parents, self.admission['outputs'])
            self.assertEqual(before, {str(f.relative_to(root)): C.sha(f.read_bytes()) for f in root.rglob('*.glb')})

    def test_missing_offline_immutable_parent_fails_without_any_output(self):
        bad = copy.deepcopy(self.row); bad['gitBlob'] = '0'*40; bad['sha256'] = '0'*64
        with self.assertRaises(ValueError):
            C.parent_bytes(bad, self.recipe)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run(['git', 'init', '-q', str(root)], check=True)
            with self.assertRaisesRegex(ValueError, 'shallow/offline'):
                C.require_parent_tree(self.recipe, root)
            self.assertEqual(list(root.glob('*.glb')), [])

    def test_IO_failure_restores_existing_files_and_removes_new_outputs(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); a, b = root/'old.glb', root/'new.glb'; a.write_bytes(self.raw)
            original = C.os.replace; calls = []
            def fail_second(src, dst):
                calls.append(dst)
                if len(calls) == 2:
                    raise OSError('injected second replacement failure')
                return original(src, dst)
            with patch.object(C.os, 'replace', side_effect=fail_second), self.assertRaises(OSError):
                C.install_files([(a, b'new'), (b, b'new')])
            self.assertEqual(a.read_bytes(), self.raw)
            self.assertFalse(b.exists())
            self.assertEqual(list(root.glob('*.charles-pending')), [])

    def test_real_fixture_and_other_resident_export_stay_outside_coat_hook(self):
        text = (C.APP/'tools/human_export.sh').read_text()
        self.assertIn('[ "$MODE" = master ] && [ -f "$SCRATCH/lods/nelson_charles_1904_coachman.lod0.glb" ]', text)
        self.assertLess(text.index('OUT="$SCRATCH/charles-canonical"'), text.index('for f in "$SCRATCH"/lods/*.glb'))
        self.assertIn('--package "mikktspace@1.1.1"', text)
        self.assertNotIn('human_charles_coat', text[:text.index('CHARLES_TARGET=""')])


if __name__ == '__main__':
    unittest.main()
