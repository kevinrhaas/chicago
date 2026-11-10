#!/usr/bin/env python3
"""Partial compound siding keeps the existing union, openings and exposed logs.

These are actual pre-export mesh checks, not native or photographic acceptance.
"""
from __future__ import annotations

import dataclasses
import json
import math
from pathlib import Path
import sys
import types
import unittest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "generators"))
sys.modules.setdefault("bpy", types.ModuleType("bpy"))
from archetypes import log_dwelling as builder  # noqa: E402
from archetypes.log_dwelling_params import LogDwellingParams, ParamError, from_phase  # noqa: E402
from common.mesh import MeshBuilder  # noqa: E402


def current():
    record = json.loads((ROOT / "data/structures/cobweb_castle.json").read_text())
    return record, from_phase(record["phases"][0], record)


def normal(verts):
    a, b, c = verts[:3]
    u, v = [b[i] - a[i] for i in range(3)], [c[i] - a[i] for i in range(3)]
    return (u[1]*v[2]-u[2]*v[1], u[2]*v[0]-u[0]*v[2], u[0]*v[1]-u[1]*v[0])


class PartialCompoundBoards(unittest.TestCase):
    def test_keyword_only_default_and_invalid_partial_extents(self):
        _, p = current()
        self.assertEqual(p.compound_clapboard_height_m, 1.3)
        f = next(f for f in dataclasses.fields(p) if f.name == "compound_clapboard_height_m")
        self.assertTrue(f.kw_only)
        self.assertIsNone(f.default)
        legacy = LogDwellingParams(13, 9, 1, 2.6, "gable", 35, "log")
        self.assertEqual((legacy.width_m, legacy.depth_m, legacy.stories,
                          legacy.wall_height_m, legacy.roof_type, legacy.roof_pitch_deg,
                          legacy.construction), (13, 9, 1, 2.6, "gable", 35, "log"))
        self.assertIsNone(legacy.compound_clapboard_height_m)
        for height in (True, "1.3", math.nan, math.inf, 0, -1, .13, 2.6, 3):
            with self.subTest(height=height), self.assertRaises(ParamError):
                dataclasses.replace(p, compound_clapboard_height_m=height).validate()
        with self.assertRaises(ParamError):
            dataclasses.replace(legacy, compound_clapboard_height_m=1.3).validate()
        record = json.loads((ROOT / "data/structures/wolf_point_tavern.json").read_text())
        elbow = from_phase(record["phases"][0], record)
        with self.assertRaises(ParamError):
            dataclasses.replace(elbow, compound_clapboard_height_m=1.3).validate()

    def test_only_union_boundary_is_boarded(self):
        record, p = current()
        runs = list(builder._compound_exterior_runs(p))
        outline = record["phases"][0]["footprint"]["polygon"]
        perimeter = sum(math.dist(a, z) for a, z in zip(outline, outline[1:] + outline[:1]))
        self.assertAlmostEqual(sum(high - low for _, _, _, low, high in runs), perimeter)
        def inside(x, y):
            return any(r[0] < x < r[2] and r[1] < y < r[3]
                       for r, *_ in p.compound_parts)
        for axis, plane, outward, low, high in runs:
            mid = (low + high) / 2
            a, z = plane - outward * 1e-5, plane + outward * 1e-5
            self.assertTrue(inside(a, mid) if axis == "x" else inside(mid, a))
            self.assertFalse(inside(z, mid) if axis == "x" else inside(mid, z))

    def test_actual_panels_leave_both_grounded_apertures_and_windows_clear(self):
        _, p = current()
        mesh = MeshBuilder("partial-boards")
        builder._compound_clapboards(mesh, p)
        self.assertGreater(len(mesh.faces), 100)
        self.assertEqual(set(mesh.mat_index), {builder.M_FRAME})
        self.assertEqual(set(mesh.conf), {1})
        self.assertEqual(min(v[2] for v in mesh.verts), 0)
        self.assertAlmostEqual(max(v[2] for v in mesh.verts), 1.3)
        holes = builder.compound_front_rects(p)
        checked = 0
        for face in mesh.faces:
            verts = [mesh.verts[i] for i in face]
            n = normal(verts)
            self.assertGreater(sum(v*v for v in n), 0)
            if max(v[2] for v in verts) - min(v[2] for v in verts) < 1e-9:
                if abs(verts[0][2] - 1.3) < 1e-9:
                    self.assertGreater(n[2], 0)
                else:
                    self.assertLess(n[2], 0)
                continue
            for plane, _kind, a, z, lo, hi in holes:
                if all(plane < v[1] < plane + .07 for v in verts):
                    checked += 1
                    overlap_u = max(0, min(max(v[0] for v in verts), z) - max(min(v[0] for v in verts), a))
                    overlap_z = max(0, min(max(v[2] for v in verts), hi) - max(min(v[2] for v in verts), lo))
                    self.assertAlmostEqual(overlap_u * overlap_z, 0)
                    self.assertGreater(n[1], 0)
        self.assertGreater(checked, 20)

    def test_existing_body_roofs_stacks_and_dark_faces_are_preserved(self):
        _, p = current()
        before, after = MeshBuilder("cobweb_castle__log_1820"), MeshBuilder("cobweb_castle__log_1820")
        builder._compound(before, dataclasses.replace(p, compound_clapboard_height_m=None))
        builder._compound(after, p)
        self.assertGreater(len(after.verts), len(before.verts))
        self.assertEqual(after.verts[:len(before.verts)], before.verts)
        self.assertEqual(after.faces[:len(before.faces)], before.faces)
        self.assertEqual(after.mat_index[:len(before.mat_index)], before.mat_index)
        self.assertEqual(after.conf[:len(before.conf)], before.conf)
        self.assertEqual(after.named, before.named)
        for axis in range(3):
            self.assertEqual(min(v[axis] for v in before.verts), min(v[axis] for v in after.verts))
            self.assertEqual(max(v[axis] for v in before.verts), max(v[axis] for v in after.verts))


if __name__ == "__main__":
    unittest.main()
