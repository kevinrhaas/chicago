# SPDX-License-Identifier: GPL-3.0-or-later
import copy
import hashlib
import json
import math
import pathlib
import sys
import unittest

P = pathlib.Path(__file__).resolve().parent
sys.dont_write_bytecode = True
sys.path.insert(0, str(P))
from human_source_normals import source_shared_normals


class Analytical(unittest.TestCase):
    def fixture(self):
        return (
            [[0, 0, 0], [2, 0, 0], [0, 1, 0], [0, 0, 0], [0, 0, 1], [1, 0, 0]],
            [[0, 1, 2], [3, 4, 5]],
            [0, 1, 2, 0, 3, 4],
        )

    def test_oriented_area_weighted_union(self):
        p, t, ids = self.fixture()
        before = copy.deepcopy((p, t, ids))
        n = source_shared_normals(p, t, ids)
        self.assertEqual((p, t, ids), before)
        self.assertEqual(n[0], n[3])
        expected = [0, 1 / math.sqrt(5), 2 / math.sqrt(5)]
        for a, b in zip(n[0], expected):
            self.assertAlmostEqual(a, b)
        self.assertEqual(n[1], [0, 0, 1])
        self.assertEqual(n[4], [0, 1, 0])

    def test_winding_and_repeatability(self):
        p, t, ids = self.fixture()
        n = source_shared_normals(p, t, ids)
        r = source_shared_normals(p, [list(reversed(f)) for f in t], ids)
        self.assertEqual(n, source_shared_normals(p, t, ids))
        for a, b in zip(n, r):
            for x, y in zip(a, b):
                self.assertAlmostEqual(x, -y)

    def test_same_position_different_id_not_merged(self):
        p, t, ids = self.fixture()
        ids[3] = 5
        n = source_shared_normals(p, t, ids)
        self.assertEqual(n[0], [0, 0, 1])
        self.assertEqual(n[3], [0, 1, 0])

    def test_noncoincident_and_bad_face_rejected(self):
        p, t, ids = self.fixture()
        p[3][0] = 0.001
        with self.assertRaisesRegex(ValueError, 'noncoincident'):
            source_shared_normals(p, t, ids)
        p, t, ids = self.fixture()
        with self.assertRaisesRegex(ValueError, 'invalid triangle'):
            source_shared_normals(p, [[0, 1, 99]], ids)
        with self.assertRaisesRegex(ValueError, 'degenerate'):
            source_shared_normals(p, [[0, 0, 1]], ids)


class ActualSource(unittest.TestCase):
    def test_both_frozen_bodies(self):
        report = []
        for age in [25, 35]:
            raw = (
                P.parent
                / f'assets/authored/humans/makehuman_hm08/prepared_adult_{age}.json'
            ).read_bytes()
            m = json.loads(raw)['meshes'][0]
            before = json.dumps(m, sort_keys=True)
            n = source_shared_normals(m['positions_m'], m['triangles'], m['source_vertex_indices'])
            seen = {}
            for sid, v in zip(m['source_vertex_indices'], n):
                if sid in seen:
                    self.assertEqual(seen[sid], v)
                seen[sid] = v
                self.assertAlmostEqual(math.hypot(*v), 1, places=12)
            self.assertEqual(before, json.dumps(m, sort_keys=True))
            self.assertEqual(
                n,
                source_shared_normals(
                    m['positions_m'], m['triangles'], m['source_vertex_indices']
                ),
            )
            report.append(
                {
                    'age': age,
                    'frozen_body_sha256': hashlib.sha256(raw).hexdigest(),
                    'vertices': len(n),
                    'unique_source_vertices': len(seen),
                    'UV_duplicates_identical_normals': True,
                    'input_unchanged': True,
                }
            )
        self.assertEqual(len(report), 2)


if __name__ == '__main__':
    unittest.main()
