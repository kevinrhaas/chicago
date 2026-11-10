#!/usr/bin/env python3
"""First-fort mixed gates: pure parameter and emitted cut/frame regression checks.

No Blender or image-match verdict: native exports and picture acceptance are separate.
"""
from __future__ import annotations

import dataclasses
import json
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "generators"))
sys.modules.setdefault("bpy", types.ModuleType("bpy"))
from archetypes import palisade as builder  # noqa: E402
from archetypes.palisade_params import PalisadeParams, ParamError, from_phase  # noqa: E402
from common.mesh import MeshBuilder  # noqa: E402


def current(row):
    record = json.loads((ROOT / "data/structures" / f"first_fort_dearborn_pickets_{row}.json").read_text())
    return from_phase(record["phases"][0], record)


class SideGates(unittest.TestCase):
    def test_legacy_positional_constructor_keeps_every_station(self):
        params = PalisadeParams(30, 32, "picket_stockade", "log", 3.7, 0.24, 0.3,
                               None, ("s",), 1.89, -2.62, "gateway", (), 7, 3,
                               1.3, 3, 3, 0.9, {"gate_sides": "attested"})
        params.validate()
        self.assertEqual(params.gate("s"), {"width_m": 1.89, "offset_m": -2.62, "kind": "gateway"})
        self.assertEqual(params.gate_overrides, {})
        self.assertTrue(next(f for f in dataclasses.fields(params) if f.name == "gate_overrides").kw_only)
        self.assertEqual(params.confidence, {"gate_sides": "attested"})

    def test_explicit_overrides_and_scalar_fallback_are_independent(self):
        for row, offset, south_offset, grade in [("inner", 10.53, -2.62, 0), ("outer", 10.49, -2.83, 0.5)]:
            with self.subTest(row=row):
                p = current(row)
                self.assertEqual(p.gate("s"), {"width_m": 1.89, "offset_m": south_offset, "kind": "gateway"})
                self.assertEqual(p.gate("w"), {"width_m": 1.5, "offset_m": offset, "kind": "wicket"})
                self.assertEqual(p.gate_conf("s"), grade)
                self.assertEqual(p.gate_conf("w"), 1)

    def test_override_errors_are_not_silently_dropped(self):
        p = current("inner")
        invalid = [[], {"q": {}}, {"e": {}}, {"w": None}, {"w": {"offest_m": 2}},
                   {"w": {"width_m": 1.49}}, {"w": {"width_m": 9}},
                   {"w": {"width_m": float("nan")}}, {"w": {"width_m": True}},
                   {"w": {"offset_m": float("inf")}}, {"w": {"offset_m": "10.53"}},
                   {"w": {"offset_m": 14}}, {"w": {"kind": "door"}}]
        for override in invalid:
            with self.subTest(override=override), self.assertRaises(ParamError):
                dataclasses.replace(p, gate_overrides=override).validate()
        with self.assertRaises(ParamError):
            dataclasses.replace(p, width_m=3, gate_sides=("n",), gate_overrides={}).validate()
        with self.assertRaises(ParamError):
            dataclasses.replace(p, wall_kind="worm_fence").validate()

    def test_actual_producer_cuts_and_posts_share_the_side_settings(self):
        for row in ("inner", "outer"):
            p = current(row)
            runs = []
            with patch.object(builder, "_picket_run", lambda b, p, a, z, c: runs.append((a, z))), \
                    patch.object(builder, "_gate"):
                builder._stockade(MeshBuilder("cut-test"), p)
            west = [sorted([a[1], z[1]]) for a, z in runs if a[0] == z[0] == 0]
            middle = p.depth_m / 2 + p.gate("w")["offset_m"]
            self.assertEqual(sorted(west), [[0, middle - 0.75], [middle + 0.75, p.depth_m]])
            self.assertEqual(builder._gate_shift(p, "w"), -p.gate("w")["offset_m"])
            self.assertEqual(builder._gate_shift(p, "s"), p.gate("s")["offset_m"])
            mesh = MeshBuilder("west-posts")
            builder._gate(mesh, p, "w", p.gate_conf("w"))
            # Two jambs, no baked shut leaf/lintel. The live renderer hangs one leaf.
            self.assertEqual(len(mesh.faces), 10)
            self.assertEqual(set(mesh.mat_index), {builder.M_PICKET})
            self.assertEqual(set(mesh.conf), {1})
            self.assertAlmostEqual(min(v[1] for v in mesh.verts), middle - 0.75)
            self.assertAlmostEqual(max(v[1] for v in mesh.verts), middle + 0.75)
            self.assertAlmostEqual(max(v[2] for v in mesh.verts), p.picket_height_m + builder.WICKET_POST_RISE_M)


if __name__ == "__main__":
    unittest.main()
