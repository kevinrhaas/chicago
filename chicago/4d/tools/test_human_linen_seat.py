# SPDX-License-Identifier: GPL-3.0-or-later
"""Source geometry controls; not native LOD, posed or photographic acceptance."""
import copy
import hashlib
import json
import math
from pathlib import Path
import sys
import unittest

sys.dont_write_bytecode = True
from human_linen_seat import linen_seat_ease
import human_settler_1812 as S
import human_labourer_1835 as L
import human_coachman_1904 as C

ROOT = Path(__file__).resolve().parent.parent


def rear_surface(mesh, x, y):
    """Independent ray/triangle sample through the actual generated surface."""
    hits = []
    for face in mesh['triangles']:
        a, b, c = [mesh['positions_m'][i] for i in face]
        den = (b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
        if abs(den) < 1e-14:
            continue
        u = ((b[1]-c[1])*(x-c[0])+(c[0]-b[0])*(y-c[1]))/den
        v = ((c[1]-a[1])*(x-c[0])+(a[0]-c[0])*(y-c[1]))/den
        w = 1.-u-v
        if min(u, v, w) >= -1e-10:
            hits.append(u*a[2]+v*b[2]+w*c[2])
    if not hits:
        raise AssertionError('probe has no actual trouser triangle')
    return -min(hits)


def triangle_normal(mesh, face):
    a, b, c = [mesh['positions_m'][i] for i in face]
    u = [b[i]-a[i] for i in range(3)]
    v = [c[i]-a[i] for i in range(3)]
    return [u[1]*v[2]-u[2]*v[1], u[2]*v[0]-u[0]*v[2], u[0]*v[1]-u[1]*v[0]]


class LinenSeat(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        raw = (ROOT/'assets/authored/humans/makehuman_hm08/prepared_adult_35.json').read_bytes()
        assert hashlib.sha256(raw).hexdigest() == S.BODY_SHA256
        cls.body = json.loads(raw)
        cls.bones = {b['name']: b for b in cls.body['skeleton']}
        cls.height = max(p[1] for m in cls.body['meshes'] for p in m['positions_m'])
        cls.spec = S.TAILORING['trousers']['seat_ease']
        with C._lent(L, trousers=S.TAILORING['trousers']):
            cls.previous = L.trousers(cls.body, cls.bones, cls.height)
        cls.bundle = S.construct(cls.body)
        cls.current = next(m for m in cls.bundle['meshes'] if m['name'] == 'loose_trousers')

    def test_known_body_cleft_is_covered_by_actual_source_triangles(self):
        # The unmodified shell is the negative control: every probe shows a
        # visible anatomical depression. The new cut bridges that depression.
        for y in (.83, .85, .87, .89, .91, .94, .97):
            with self.subTest(y=y):
                old = [rear_surface(self.previous, x, y) for x in (-.06, 0., .06)]
                new = [rear_surface(self.current, x, y) for x in (-.06, 0., .06)]
                self.assertGreater((old[0]+old[2])/2-old[1], .005)
                self.assertLess((new[0]+new[2])/2-new[1], .003)
        self.assertFalse(self.current['receipt']['linen_seat_ease']['native_lod_and_posed_clearance_accepted'])

    def test_only_seat_positions_change(self):
        old, new = self.previous, self.current
        for key in ('triangles', 'uvs', 'corner_uvs', 'weights'):
            self.assertEqual(old[key], new[key], key)
        waist = self.height*S.TAILORING['trousers']['waist_height_fraction']
        lo = self.bones['pelvis']['head_m'][1]-self.spec['lower_below_pelvis_m']
        hi = waist-self.spec['upper_below_waist_m']
        for a, b in zip(old['positions_m'], new['positions_m']):
            self.assertEqual(a[:2], b[:2])
            self.assertLessEqual(b[2], a[2])
            if (a[1] <= lo or a[1] >= hi or abs(a[0]) >= self.spec['half_width_m']
                    or a[2] >= self.bones['pelvis']['head_m'][2]):
                self.assertEqual(a, b)

    def test_no_source_triangle_collapse_or_normal_reversal(self):
        for face in self.previous['triangles']:
            before = triangle_normal(self.previous, face)
            after = triangle_normal(self.current, face)
            self.assertGreater(math.hypot(*after), 1e-12)
            self.assertGreaterEqual(math.fsum(a*b for a, b in zip(before, after)), 0.)

    def test_inputs_and_other_garment_parameters_are_not_mutated(self):
        mesh = copy.deepcopy(self.previous)
        bones = copy.deepcopy(self.bones)
        spec = copy.deepcopy(self.spec)
        linen_seat_ease(mesh, bones, self.height, .585, spec)
        self.assertEqual(mesh, self.previous)
        self.assertEqual(bones, self.bones)
        self.assertEqual(spec, self.spec)
        self.assertNotIn('seat_ease', L.TAILORING['trousers'])
        recipe = json.loads((ROOT/S.RECIPE).read_text())
        self.assertEqual(recipe['settler_components']['tailoring']['trousers']['seat_ease'], spec)

    def test_unknown_or_invalid_patterns_are_refused(self):
        cases = [dict(self.spec, id='unknown'), dict(self.spec, extra_rear_ease_m=-.1),
                 dict(self.spec, extra_rear_ease_m=float('nan')),
                 dict(self.spec, full_half_width_m=.2), dict(self.spec, section_rows=True)]
        for spec in cases:
            with self.subTest(spec=spec):
                with self.assertRaises(ValueError):
                    linen_seat_ease(self.previous, self.bones, self.height, .585, spec)


if __name__ == '__main__':
    unittest.main(verbosity=1)
