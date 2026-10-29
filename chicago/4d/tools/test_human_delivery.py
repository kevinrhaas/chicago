#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Small negative/positive trust-boundary tests; no native asset generation.

Synthetic files exercise only path/container/manifest rejection. They are not
Blender, visual, fit, export or full-preflight evidence.
"""
import copy
import hashlib
import json
import os
from pathlib import Path
import struct
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import human_delivery as delivery


def trusted():
    return dict(event='workflow_dispatch', repository=delivery.REPOSITORY,
                ref=delivery.REF, workflow_ref=delivery.WORKFLOW,
                source='a' * 40, definition='a' * 40, run_id='123', attempt='2',
                deliver=True, seated=False, dress=True, teamsters=False, source_ref='', family='dress')


class TrustTests(unittest.TestCase):
    def test_manual_owned_source_only(self):
        c = trusted()
        self.assertEqual(delivery.validate_context(c), 'dress')
        c.update(dress=False, teamsters=True)
        self.assertEqual(delivery.validate_context(c), 'teamsters')
        for field, values in {
            'event': ['push', 'pull_request', 'workflow_run'],
            'repository': ['other/chicago', 'kevinrhaas/chicago-fork'],
            'ref': ['refs/heads/main', 'refs/heads/dev', 'refs/tags/' + delivery.BRANCH, 'refs/heads/other'],
            'workflow_ref': [delivery.WORKFLOW + '-other'],
            'definition': ['b' * 40, 'main'], 'source': ['main', delivery.LEGACY, 'A' * 40],
            'source_ref': [delivery.LEGACY, 'refs/heads/dev', 'b' * 40],
            'deliver': [False], 'seated': [True], 'run_id': ['0', '../1', '1;echo bad'], 'attempt': ['0', '01'],
        }.items():
            for value in values:
                with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                    candidate = trusted(); candidate[field] = value
                    delivery.validate_context(candidate)
        for dress, teamsters in [(False, False), (True, True)]:
            with self.assertRaises(ValueError):
                candidate = trusted(); candidate.update(dress=dress, teamsters=teamsters)
                delivery.validate_context(candidate)

    def test_fixed_family_has_exact_masters_lods_and_three_male_stills(self):
        for family, count in [('dress', 1), ('teamsters', 3)]:
            targets = [target for _, target in delivery.spec(family)]
            self.assertEqual(len(targets), len(set(targets)))
            self.assertEqual(sum(x.endswith('.blend') for x in targets), count)
            self.assertEqual(sum(x.endswith('.glb') for x in targets), count * 8)
            self.assertEqual(sum(x.endswith('.png') for x in targets), 0 if family == 'dress' else 3)
            self.assertTrue(all('..' not in Path(x).parts and not x.startswith('/') for x in targets))
        with self.assertRaises(ValueError):
            delivery.assets('other')

    def test_paths_symlinks_and_hardlinks(self):
        with tempfile.TemporaryDirectory(prefix='human-delivery-path-test-') as directory:
            root = Path(directory); (root / 'good').write_bytes(b'proof')
            self.assertEqual(delivery.regular_under(root, 'good'), root / 'good')
            for value in ['/etc/passwd', '../good', 'a/../good', 'a//b', 'a\\b', './good']:
                with self.subTest(value=value), self.assertRaises(ValueError):
                    delivery.regular_under(root, value)
            (root / 'link').symlink_to(root / 'good')
            with self.assertRaises(ValueError):
                delivery.regular_under(root, 'link')
            (root / 'parent').symlink_to(root, target_is_directory=True)
            with self.assertRaises(ValueError):
                delivery.regular_under(root, 'parent/good')
            os.link(root / 'good', root / 'hardlink')
            with self.assertRaises(ValueError):
                delivery.regular_under(root, 'hardlink')

    def test_glb_rejects_external_or_data_uri_and_wrong_identity(self):
        with tempfile.TemporaryDirectory(prefix='human-delivery-container-test-') as directory:
            path = Path(directory) / 'synthetic-security-fixture.glb'
            document = dict(scenes=[dict(extras=dict(chicago4d_human=dict(asset_id=delivery.FEMALE,
                             grade='reconstructed')))], buffers=[dict(byteLength=0)], images=[])
            def write(value):
                raw = json.dumps(value).encode(); raw += b' ' * (-len(raw) % 4)
                path.write_bytes(struct.pack('<5I', 0x46546C67, 2, 20 + len(raw), len(raw), 0x4E4F534A) + raw)
            write(document); delivery.glb_container(path, delivery.FEMALE)
            for uri in ['https://example.invalid/image.png', 'file:///tmp/file', '../image.png', 'data:image/png;base64,AA==']:
                for key in ['images', 'buffers']:
                    candidate = copy.deepcopy(document); candidate[key] = [dict(uri=uri)]
                    write(candidate)
                    with self.subTest(uri=uri, key=key), self.assertRaises(ValueError):
                        delivery.glb_container(path, delivery.FEMALE)
            write(document)
            with self.assertRaises(ValueError):
                delivery.glb_container(path, delivery.MALES[0])
            path.write_bytes(b'not a GLB')
            with self.assertRaises(ValueError):
                delivery.glb_container(path, delivery.FEMALE)

    def test_remote_branch_race_and_wrong_origin_refused(self):
        for url, head in [('https://github.com/kevinrhaas/chicago', 'a' * 40),
                          ('https://github.com/kevinrhaas/chicago.git', 'a' * 40)]:
            with patch.object(delivery, 'git', side_effect=[url, url, head + '\t' + delivery.REF]):
                delivery.remote_source(trusted())
        for output in ['b' * 40 + '\t' + delivery.REF, 'a' * 40 + '\trefs/heads/dev', '']:
            with patch.object(delivery, 'git', side_effect=['https://github.com/kevinrhaas/chicago',
                 'https://github.com/kevinrhaas/chicago', output]), self.assertRaises(ValueError):
                delivery.remote_source(trusted())
        with patch.object(delivery, 'git', return_value='https://other.invalid/kevinrhaas/chicago'), self.assertRaises(ValueError):
            delivery.remote_source(trusted())
        for push in ['https://other.invalid/repo', 'https://github.com/kevinrhaas/chicago\nhttps://other.invalid/repo']:
            with patch.object(delivery, 'git', side_effect=['https://github.com/kevinrhaas/chicago', push]), self.assertRaises(ValueError):
                delivery.remote_source(trusted())

    def test_male_write_requires_prior_equivalent_verified_female_delivery(self):
        with tempfile.TemporaryDirectory(prefix='human-delivery-sequence-test-') as directory:
            root = Path(directory); p = root / 'data/humans/canonical-deliveries/dress.json'
            with patch.object(delivery, 'APP', root), self.assertRaises(ValueError):
                delivery.require_female_delivery(trusted())
            record = dict(family='dress', repository=delivery.REPOSITORY, branch=delivery.BRANCH,
                          source_sha='b' * 40, definition_sha='b' * 40,
                          source_files={'recipe': 'unchanged'}, photographic_accepted=False, files=[])
            delivery.dump(p, record)
            with patch.object(delivery, 'APP', root), patch.object(delivery, 'source_binding', return_value={'recipe': 'changed'}), self.assertRaises(ValueError):
                delivery.require_female_delivery(trusted())
            with patch.object(delivery, 'APP', root), patch.object(delivery, 'source_binding', return_value={'recipe': 'unchanged'}), \
                 patch.object(delivery, 'git', return_value=''), patch.object(delivery.subprocess, 'run'), self.assertRaises(ValueError):
                delivery.require_female_delivery(trusted())
            with patch.object(delivery, 'APP', root):
                for _, target in delivery.spec('dress'):
                    path = root / target; path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_bytes(b'SYNTHETIC prior female member for source-path guard')
                    record['files'].append(dict(path=target, bytes=path.stat().st_size, sha256=delivery.digest(path)))
            delivery.dump(p, record)
            # These real shared inputs were intentionally outside SOURCE_FILES;
            # the native Git path guard must still refuse their changed bytes.
            changed_paths = ['chicago/4d/tools/human_hair_short04.py',
                             'chicago/4d/tools/human_source_normals.py',
                             'chicago/4d/assets/authored/humans/makehuman_hm08/prepared.json',
                             'chicago/4d/data/humans/contract.json']
            for changed in changed_paths:
                with self.subTest(changed=changed), patch.object(delivery, 'APP', root), \
                     patch.object(delivery, 'source_binding', return_value={'recipe': 'unchanged'}), \
                     patch.object(delivery, 'git', return_value=changed), \
                     patch.object(delivery.subprocess, 'run'), self.assertRaises(ValueError):
                    delivery.require_female_delivery(trusted())
            with patch.object(delivery, 'APP', root), patch.object(delivery, 'source_binding', return_value={'recipe': 'unchanged'}), \
                 patch.object(delivery, 'git', return_value='\n'.join(sorted(delivery.allowed({'family': 'dress'})))), \
                 patch.object(delivery.subprocess, 'run'):
                delivery.require_female_delivery(trusted())

    def test_male_source_guard_requires_real_prior_history_and_rejects_later_edits(self):
        """Real shallow/full Git history; synthetic member bytes are not assets."""
        with tempfile.TemporaryDirectory(prefix='human-delivery-history-test-') as directory:
            base = Path(directory); full = base / 'full'; full.mkdir()
            def native(repo, *args):
                return subprocess.check_output(['git', *args], cwd=repo, text=True,
                                               stderr=subprocess.PIPE).strip()
            native(full, 'init', '-q', '-b', 'main')
            native(full, 'config', 'user.name', 'Human delivery fixture')
            native(full, 'config', 'user.email', 'fixture@example.invalid')
            app = full / 'chicago/4d'; app.mkdir(parents=True)
            (app / 'source.txt').write_text('unchanged authoring source\n')
            native(full, 'add', '.'); native(full, 'commit', '-qm', 'source')
            prior = native(full, 'rev-parse', 'HEAD'); rows = []
            for _, target in delivery.spec('dress'):
                path = app / target; path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b'SYNTHETIC history guard fixture; not a model')
                rows.append(dict(path=target, bytes=path.stat().st_size, sha256=delivery.digest(path)))
            delivery.dump(app / 'data/humans/canonical-deliveries/dress.json',
                          dict(family='dress', repository=delivery.REPOSITORY, branch=delivery.BRANCH,
                               source_sha=prior, definition_sha=prior, source_files={'fixed': 'source'},
                               photographic_accepted=False, files=rows))
            native(full, 'add', '.'); native(full, 'commit', '-qm', 'female delivery')
            native(full, 'commit', '--allow-empty', '-qm', 'same-tree authenticated followup')
            source = native(full, 'rev-parse', 'HEAD'); shallow = base / 'shallow'
            subprocess.run(['git', 'clone', '-q', '--depth', '1', full.as_uri(), str(shallow)],
                           check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            c = trusted(); c.update(dress=False, teamsters=True, family='teamsters', source=source)
            def guard(repo):
                with patch.object(delivery, 'APP', repo / 'chicago/4d'), \
                     patch.object(delivery, 'REPO', repo), \
                     patch.object(delivery, 'source_binding', return_value={'fixed': 'source'}):
                    delivery.require_female_delivery(c)
            with self.assertRaises(subprocess.CalledProcessError):
                guard(shallow)
            native(shallow, 'fetch', '-q', '--unshallow')
            guard(shallow)
            native(shallow, 'config', 'user.name', 'Human delivery fixture')
            native(shallow, 'config', 'user.email', 'fixture@example.invalid')
            changed = shallow / 'chicago/4d/tools/human_hair_short04.py'
            changed.parent.mkdir(parents=True, exist_ok=True)
            changed.write_text('# changed authoring dependency\n')
            native(shallow, 'add', '.'); native(shallow, 'commit', '-qm', 'forbidden later source edit')
            c['source'] = native(shallow, 'rev-parse', 'HEAD')
            with self.assertRaisesRegex(ValueError, 'authoring/shared input changed after female generation'):
                guard(shallow)

    def test_same_run_artifact_id_attempt_source_and_success_required(self):
        with tempfile.TemporaryDirectory(prefix='human-delivery-artifact-test-') as directory:
            root = Path(directory); event = root / 'event.json'
            event.write_text(json.dumps(dict(repository=dict(id=7))))
            record = dict(id=99, name='human-delivery-dress-123-2', expired=False,
                          digest='sha256:' + 'c' * 64, size_in_bytes=100,
                          workflow_run=dict(id=123, head_sha='a' * 40, head_branch=delivery.BRANCH,
                                            repository_id=7, head_repository_id=7))
            env = dict(DELIVERY_ARTIFACT_ID='99', FIXTURE_RESULT='success', PRODUCER_RESULT='success',
                       GITHUB_EVENT_PATH=str(event))
            def run(candidate, changes=None):
                with patch.dict(os.environ, dict(env, **(changes or {}))), patch.object(delivery, 'STATE', root), \
                     patch.object(delivery.subprocess, 'check_output', return_value=json.dumps(candidate)), \
                     patch.object(delivery, 'remote_source'):
                    delivery.artifact(trusted())
            run(record)
            for key, value in [('id', 100), ('name', 'human-delivery-dress-123-1'), ('expired', True), ('digest', '')]:
                candidate = copy.deepcopy(record); candidate[key] = value
                with self.subTest(key=key), self.assertRaises(ValueError):
                    run(candidate)
            for key, value in [('id', 124), ('head_sha', 'b' * 40), ('head_branch', 'dev'),
                               ('repository_id', 8), ('head_repository_id', 8)]:
                candidate = copy.deepcopy(record); candidate['workflow_run'][key] = value
                with self.subTest(key=key), self.assertRaises(ValueError):
                    run(candidate)
            for key in ['FIXTURE_RESULT', 'PRODUCER_RESULT']:
                for value in ['failure', 'cancelled', 'skipped']:
                    with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                        run(record, {key: value})

    def test_manifest_member_source_hash_and_fixed_family_rejections(self):
        with tempfile.TemporaryDirectory(prefix='human-delivery-manifest-test-') as directory:
            root = Path(directory); c = trusted(); rows = []
            for _, target in delivery.spec('dress'):
                path = root / target; path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(b'synthetic boundary test')
                rows.append(dict(path=target, bytes=path.stat().st_size, sha256=delivery.digest(path)))
            original = dict(format='canonical_human_delivery_v1', repository=delivery.REPOSITORY,
                branch=delivery.BRANCH, source_sha=c['source'], definition_sha=c['definition'], source_tree='d' * 40,
                family='dress', run_id='123', run_attempt='2', source_files={'bound': 'value'},
                photographic_accepted=False, production_eligibility_changed=False, files=rows)
            def run(candidate):
                delivery.dump(root / 'delivery-manifest.json', candidate)
                with patch.object(delivery, 'DOWNLOAD', root), patch.object(delivery, 'git', return_value='d' * 40), \
                     patch.object(delivery, 'source_binding', return_value={'bound': 'value'}), \
                     patch.object(delivery, 'glb_container'), patch.object(delivery, 'verify_reports'), \
                     patch.dict(os.environ, EXPECTED_MANIFEST_SHA256=delivery.digest(root / 'delivery-manifest.json')):
                    delivery.verify_bundle(c)
            run(original)
            for key, value in [('source_sha', 'b' * 40), ('definition_sha', 'b' * 40), ('run_id', '124'),
                ('run_attempt', '1'), ('family', 'teamsters'), ('source_tree', 'e' * 40),
                ('branch', 'dev'), ('source_files', {}), ('photographic_accepted', True),
                ('production_eligibility_changed', True)]:
                candidate = copy.deepcopy(original); candidate[key] = value
                with self.subTest(key=key), self.assertRaises(ValueError):
                    run(candidate)
            for mutation in ['missing', 'duplicate', 'escape', 'sha', 'size']:
                candidate = copy.deepcopy(original)
                if mutation == 'missing': candidate['files'].pop()
                if mutation == 'duplicate': candidate['files'].append(candidate['files'][0])
                if mutation == 'escape': candidate['files'][0]['path'] = '../untrusted'
                if mutation == 'sha': candidate['files'][0]['sha256'] = '0' * 64
                if mutation == 'size': candidate['files'][0]['bytes'] += 1
                with self.subTest(mutation=mutation), self.assertRaises(ValueError): run(candidate)
            (root / 'unexpected').write_bytes(b'x')
            with self.assertRaises(ValueError): run(original)
            (root / 'unexpected').unlink(); (root / 'unexpected').symlink_to(root / rows[0]['path'])
            with self.assertRaises(ValueError): run(original)

    def test_unsealed_or_changed_tree_cannot_reach_commit(self):
        with tempfile.TemporaryDirectory(prefix='human-delivery-seal-test-') as directory:
            root = Path(directory); delivery.dump(root / 'GATED-TREE.json', {'returncode': 1})
            with patch.object(delivery, 'STATE', root), patch.object(delivery, 'git') as git, self.assertRaises(ValueError):
                delivery.commit(trusted())
            git.assert_not_called()

    def test_metadata_uses_existing_native_schema_and_only_fixed_allowed_paths(self):
        """Actual current schema shapes, tiny SYNTHETIC bytes; no asset qualification.

        The retained cost record provides exactly the fields emitted by the
        native human_teamster inspection. The combined registry retains the
        current human_fixture schema. This catches execution-time key mistakes
        without pretending to rebuild or measure a model.
        """
        original_app = delivery.APP
        fixture = json.loads((original_app / 'data/humans/fixture.measure.json').read_text())
        costs = json.loads((original_app / 'data/humans/bardwell_otis_1835.measure.json').read_text())
        instance = json.loads((original_app / 'data/humans/instances/1835/hi_rc_bardwell_otis_1835.json').read_text())
        change = json.loads((original_app / 'changelog.d/T-1789.json').read_text())
        for family in ('dress', 'teamsters'):
            with self.subTest(family=family), tempfile.TemporaryDirectory(prefix='human-delivery-native-schema-test-') as directory:
                root = Path(directory); state = root / '.unit-state'; state.mkdir()
                c = trusted(); c.update(family=family, dress=family == 'dress', teamsters=family == 'teamsters')
                delivery.dump(state / 'artifact.json', dict(id=99, digest='sha256:' + 'c' * 64))
                ids = ('c4d_fixture', delivery.MALES[0], delivery.FEMALE)
                if family == 'teamsters': ids += delivery.MALES[1:]
                measured = copy.deepcopy(fixture); measured['files'] = []
                for asset in ids:
                    for web in ('', 'web/'):
                        for lod in range(4):
                            name = f'assets/humans/{web}{asset}.lod{lod}.glb'; path = root / name
                            path.parent.mkdir(parents=True, exist_ok=True)
                            path.write_bytes(('SYNTHETIC schema test ' + name).encode())
                            row = copy.deepcopy(fixture['files'][0])
                            row.update(file=name, lod=lod, sha256=delivery.digest(path), bytes=path.stat().st_size)
                            measured['files'].append(row)
                delivery.dump(root / 'data/humans/fixture.measure.json', measured)
                delivery.dump(root / 'data/humans/bardwell_otis_1835.measure.json', costs)
                ipath = root / 'data/humans/instances/1835/hi_rc_bardwell_otis_1835.json'
                delivery.dump(ipath, instance)
                delivery.dump(root / 'changelog.d/T-1789.json', change)
                (root / 'assets/LICENSES.md').write_text('Original rights notices retained.\n')
                rows = []
                with patch.object(delivery, 'APP', root):
                    for _, target in delivery.spec(family):
                        p = root / target
                        if not p.exists():
                            p.parent.mkdir(parents=True, exist_ok=True); p.write_bytes(b'SYNTHETIC schema fixture')
                        rows.append(dict(path=target, bytes=p.stat().st_size, sha256=delivery.digest(p)))
                # Shape is the native report's material/name/textures and desktop
                # fields, translated from the actual retained native cost record.
                for mode in ('source', 'web'):
                    reports = []
                    for old in costs['assets']:
                        if ('/web/' in old['file']) != (mode == 'web'): continue
                        row = {k: copy.deepcopy(old[k]) for k in ('file', 'triangles', 'skinned_meshes',
                               'bone_count', 'standing_frame', 'footwear_min_y_m')}
                        row.update(viewport_name='desktop', materials=[dict(name=m['material'], textures=m['textures'])
                                                                      for m in old['decoded_images']])
                        reports.append(row)
                    delivery.dump(root / delivery.PROOF / family / f'{mode}-inspection.json', dict(runs=reports))
                manifest = dict(family=family, source_sha=c['source'], definition_sha=c['definition'],
                                files=rows, photographic_accepted=False, production_eligibility_changed=False)
                before = {p.relative_to(root).as_posix(): delivery.digest(p) for p in root.rglob('*') if p.is_file()}
                with patch.object(delivery, 'APP', root), patch.object(delivery, 'STATE', state), \
                     patch.object(delivery, 'verify_bundle', return_value=manifest), \
                     patch.dict(os.environ, EXPECTED_MANIFEST_SHA256='d' * 64):
                    delivery.metadata(c)
                after = {p.relative_to(root).as_posix(): delivery.digest(p) for p in root.rglob('*') if p.is_file()}
                changed = {'chicago/4d/' + p for p, h in after.items() if before.get(p) != h}
                self.assertTrue(changed <= delivery.allowed(c), changed - delivery.allowed(c))
                self.assertEqual(len(measured['files']), 24 if family == 'dress' else 40)
                self.assertTrue((root / 'assets/LICENSES.md').read_text().startswith('Original rights notices retained.\n'))
                self.assertFalse(any('role_profiles/' in p or 'instances/1835/index.json' in p for p in delivery.allowed(c)))
                updated = json.loads(ipath.read_text())
                if family == 'dress':
                    self.assertEqual(updated, instance)
                    self.assertEqual(json.loads((root / 'changelog.d/T-1789.json').read_text()), change)
                else:
                    before_basis = copy.deepcopy(instance); after_basis = copy.deepcopy(updated)
                    del before_basis['provenance']['basis']; del after_basis['provenance']['basis']
                    self.assertEqual(before_basis, after_basis)
                    qualified = json.loads((root / 'data/humans/bardwell_otis_1835.measure.json').read_text())
                    self.assertEqual(set(qualified), set(costs))
                    self.assertEqual(len(qualified['assets']), 8)
                    for row in qualified['assets']:
                        self.assertEqual(set(row), set(costs['assets'][0]))
                        self.assertEqual(row['sha256'], delivery.digest(root / row['file']))
                    self.assertFalse(qualified['photographic_accepted'])
                    self.assertIn('published scene/photo/occupied acceptance remain open', qualified['scope'])
                # A stale ALL-asset registry must fail before rights/provenance writes.
                measured['files'][0]['sha256'] = '0' * 64
                delivery.dump(root / 'data/humans/fixture.measure.json', measured)
                license_before = (root / 'assets/LICENSES.md').read_bytes()
                with patch.object(delivery, 'APP', root), patch.object(delivery, 'STATE', state), \
                     patch.object(delivery, 'verify_bundle', return_value=manifest), self.assertRaises(ValueError):
                    delivery.metadata(c)
                self.assertEqual((root / 'assets/LICENSES.md').read_bytes(), license_before)
                # The native registry emits a verdict LIST, never a keyed map or
                # truthy scalars. Reject malformed/failed rows before any write.
                first = measured['files'][0]
                first['sha256'] = delivery.digest(root / first['file'])
                original_verdicts = copy.deepcopy(first['verdicts'])
                invalid = [{}, {'check': {'ok': True}}, [], [True],
                           [{'ok': True, 'got': 'missing label'}],
                           [{'check': 'x', 'ok': 1, 'got': 'non-boolean'}],
                           [{'check': 'x', 'ok': False, 'got': 'failed'}]]
                for verdicts in invalid:
                    first['verdicts'] = verdicts
                    delivery.dump(root / 'data/humans/fixture.measure.json', measured)
                    with self.subTest(family=family, verdicts=verdicts), \
                         patch.object(delivery, 'APP', root), patch.object(delivery, 'STATE', state), \
                         patch.object(delivery, 'verify_bundle', return_value=manifest), \
                         self.assertRaisesRegex(ValueError, 'native measurement verdict list'):
                        delivery.metadata(c)
                    self.assertEqual((root / 'assets/LICENSES.md').read_bytes(), license_before)
                first['verdicts'] = original_verdicts


if __name__ == '__main__':
    unittest.main(verbosity=2)
