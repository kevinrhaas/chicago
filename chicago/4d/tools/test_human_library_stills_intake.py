# SPDX-License-Identifier: GPL-3.0-or-later
"""Exercise source binding and safe extraction without credentials or Blender."""
import copy
import hashlib
import io
from pathlib import Path
import stat
import tempfile
import unittest
import zipfile

from human_library_stills_intake import (ASSETS, WORKFLOW, extract_masters,
                                        select_artifact, selected_members, verify_archive)


class IntakeTest(unittest.TestCase):
    def setUp(self):
        self.run = {'id': 7, 'path': WORKFLOW, 'event': 'workflow_dispatch', 'status': 'completed',
                    'conclusion': 'success', 'head_repository': {'full_name': 'owner/repo'}, 'head_sha': 'a'*40}
        self.jobs = [{'name': name, 'status': 'completed', 'conclusion': 'success'}
                     for name in ('humans', 'teamster-studies')]
        self.artifact = {'id': 3, 'name': 'resident-teamster-studies-'+'a'*40,
                         'expired': False, 'size_in_bytes': 123, 'digest': 'sha256:'+'b'*64}

    def test_successful_source_and_required_prerequisites(self):
        self.assertEqual(select_artifact('owner/repo', '7', self.run, self.jobs, [self.artifact]), self.artifact)
        for key, value in [('path', 'other.yml'), ('event', 'pull_request'), ('status', 'in_progress'),
                           ('conclusion', 'failure'), ('head_repository', {'full_name': 'fork/repo'}), ('head_sha', 'main')]:
            with self.subTest(key=key), self.assertRaises(ValueError):
                select_artifact('owner/repo', '7', {**self.run, key: value}, self.jobs, [self.artifact])
        for index in (0, 1):
            jobs = copy.deepcopy(self.jobs)
            jobs[index]['conclusion'] = 'failure'
            with self.assertRaises(ValueError):
                select_artifact('owner/repo', '7', self.run, jobs, [self.artifact])

    def test_missing_duplicate_expired_or_unbound_artifact(self):
        for artifacts in ([], [self.artifact]*2, [{**self.artifact, 'expired': True}],
                          [{**self.artifact, 'digest': None}], [{**self.artifact, 'size_in_bytes': 2**31}]):
            with self.subTest(artifacts=artifacts), self.assertRaises(ValueError):
                select_artifact('owner/repo', '7', self.run, self.jobs, artifacts)

    def test_archive_digest_requires_actual_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'archive.zip'
            path.write_bytes(b'actual archive')
            verify_archive(path, 'sha256:'+hashlib.sha256(path.read_bytes()).hexdigest())
            with self.assertRaises(ValueError):
                verify_archive(path, 'sha256:'+'a'*64)

    def archive(self, extra=None, omit=None, duplicate=False):
        stream = io.BytesIO()
        with zipfile.ZipFile(stream, 'w') as archive:
            for asset in ASSETS:
                if asset != omit:
                    archive.writestr('home/runner/work/chicago/chicago/chicago/4d/assets/authored/humans/teamsters/'+asset+'/canonical.blend', asset.encode())
            if duplicate:
                archive.writestr('other/assets/authored/humans/teamsters/'+ASSETS[0]+'/canonical.blend', b'duplicate')
            if extra:
                archive.writestr(extra, b'unsafe')
        stream.seek(0)
        return stream

    def test_exact_three_masters_extract_without_unselected_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'source.zip'
            path.write_bytes(self.archive(extra='review/other.png').getvalue())
            output = Path(tmp)/'output'
            records = extract_masters(path, output)
            self.assertEqual({r['asset_id'] for r in records}, set(ASSETS))
            self.assertEqual(len(list(output.rglob('*.blend'))), 3)
            self.assertFalse((output/'review').exists())
            for record in records:
                self.assertEqual((output/record['path']).read_bytes(), record['asset_id'].encode())
            with self.assertRaises(ValueError):
                extract_masters(path, output)

    def test_traversal_duplicate_missing_symlink_refused_before_extraction(self):
        link = zipfile.ZipInfo('link')
        link.external_attr = (stat.S_IFLNK | 0o777) << 16
        for stream in [self.archive(extra='../escape'), self.archive(extra='/absolute'),
                       self.archive(extra='a/./b'), self.archive(extra='a\\b'),
                       self.archive(extra=link), self.archive(omit=ASSETS[0]), self.archive(duplicate=True)]:
            with zipfile.ZipFile(stream) as archive, self.assertRaises(ValueError):
                selected_members(archive)


if __name__ == '__main__':
    unittest.main()
