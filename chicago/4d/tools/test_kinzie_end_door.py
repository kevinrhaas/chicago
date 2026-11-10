#!/usr/bin/env python3
"""T-2484: a taller pictured end door is opt-in and stays below its wall plate."""
import dataclasses
import json
from pathlib import Path
import sys
import types
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'generators'))
sys.modules.setdefault('bpy', types.ModuleType('bpy'))
from archetypes import log_dwelling as builder
from archetypes.log_dwelling_params import from_phase, ParamError
from common.mesh import MeshBuilder


def current():
    record = json.loads((ROOT / 'data/structures/kinzie_house_1812.json').read_text())
    return from_phase(record['phases'][0], record)


def end_mesh(params):
    mesh = MeshBuilder('kinzie_end_review')
    builder._end_openings(mesh, params, 0, 0, params.width_m, params.depth_m,
                          params.wall_height_m)
    return mesh


class EndDoor(unittest.TestCase):
    def test_default_is_keyword_only_and_off(self):
        field = next(f for f in dataclasses.fields(current())
                     if f.name == 'end_door_height_m')
        self.assertTrue(field.kw_only)
        self.assertIsNone(field.default)

    def test_record_states_finish_and_bounded_height(self):
        params = current()
        self.assertEqual(params.log_finish, 'whitewash')
        self.assertEqual(params.end_door_height_m, 2.5)
        params.validate()

    def test_refuses_impossible_heights(self):
        params = current()
        for value in (True, False, float('nan'), float('inf'), -1, 1.59,
                      params.wall_height_m, '2.5'):
            with self.subTest(value=value), self.assertRaises(ParamError):
                dataclasses.replace(params, end_door_height_m=value).validate()

    def test_requires_a_stated_end_door(self):
        params = current()
        for openings in ((), tuple(o for o in params.end_openings if o[1] != 'door')):
            with self.assertRaises(ParamError):
                dataclasses.replace(params, end_openings=openings).validate()

    def test_actual_door_rises_without_changing_its_plan_or_topology(self):
        params = current()
        door = next(o for o in params.end_openings if o[1] == 'door')
        params = dataclasses.replace(params, end_openings=(door,))
        before = end_mesh(dataclasses.replace(params, end_door_height_m=None))
        after = end_mesh(params)
        self.assertEqual(len(before.verts), len(after.verts))
        self.assertEqual(before.faces, after.faces)
        self.assertEqual(before.mat_index, after.mat_index)
        self.assertEqual([v[:2] for v in before.verts], [v[:2] for v in after.verts])
        self.assertAlmostEqual(min(v[2] for v in before.verts),
                               min(v[2] for v in after.verts))
        self.assertAlmostEqual(max(v[2] for v in after.verts)
                               - max(v[2] for v in before.verts), 2.5 - 1.93)
        self.assertLess(max(v[2] for v in after.verts), params.wall_height_m)
        self.assertEqual(set(after.conf), {1.0})

    def test_other_end_openings_keep_exact_vertices_and_grades(self):
        params = current()
        for opening in params.end_openings:
            if opening[1] == 'door':
                continue
            selected = dataclasses.replace(params, end_openings=(opening,))
            before = end_mesh(dataclasses.replace(selected, end_door_height_m=None))
            after = end_mesh(selected)
            self.assertEqual(before.verts, after.verts)
            self.assertEqual(before.faces, after.faces)
            self.assertEqual(before.mat_index, after.mat_index)
            self.assertEqual(before.conf, after.conf)


if __name__ == '__main__':
    unittest.main()
