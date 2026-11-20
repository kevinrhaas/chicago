#!/usr/bin/env python3
"""A new date must not silently backcast another scene's reconstructed buildings."""

from __future__ import annotations

import ast
import contextlib
import datetime as dt
import importlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import compile_scene as C
import validate as V
from scene_selection import selection_errors, structure_is_selected

ROOT = Path(__file__).resolve().parent.parent
EMITTERS = ("k01_emit", "k12_emit", "k13_emit", "k16_emit", "draft_emit",
            "haystack_emit", "monument_emit", "lodge_camp_emit",
            "landmark_1871_emit")


def scene(selected=None, *, explicit=False):
    result = {"id": "1871", "target_date": "1871-10-08", "terrain_epoch": "e1871_prefire",
              "layers": ["terrain", "context"]}
    if explicit:
        result["structure_ids"] = selected
    return result


def record():
    return {"id": "later_reconstruction", "name": "Later reconstruction", "phases": [{
        "id": "later_form", "documented_range": {"from": "1868-01-01", "to": "1944-01-01"}}]}


class SceneSelectionTests(unittest.TestCase):
    def test_absent_preserves_legacy_and_empty_selects_nothing(self):
        self.assertTrue(structure_is_selected(scene(), "later_reconstruction"))
        self.assertFalse(structure_is_selected(scene([], explicit=True), "later_reconstruction"))
        self.assertTrue(structure_is_selected(scene(["later_reconstruction"], explicit=True),
                                             "later_reconstruction"))

    def test_invalid_selection_is_refused(self):
        for selected in (None, "later_reconstruction", [None], ["unknown"],
                         ["later_reconstruction", "later_reconstruction"]):
            with self.subTest(selected=selected):
                self.assertTrue(selection_errors(scene(selected, explicit=True),
                                                 ["later_reconstruction"]))
        self.assertEqual([], selection_errors(scene([], explicit=True), []))

    def test_validator_requires_selected_id_and_date(self):
        epochs = {"e1871_prefire": {"from": "1871-10-08", "to": "1871-10-08"}}
        records = {"later_reconstruction.json": record()}
        rep = V.Report()
        V.validate_scene(scene([], explicit=True), records, epochs, {}, rep)
        self.assertFalse(rep.errors)
        self.assertIn("0 structure(s) included", " ".join(rep.notes))
        rep = V.Report()
        V.validate_scene(scene(["unknown"], explicit=True), records, epochs, {}, rep)
        self.assertTrue(any("does not resolve" in e for e in rep.errors))
        records["later_reconstruction.json"]["phases"][0]["documented_range"]["from"] = "1880-01-01"
        rep = V.Report()
        V.validate_scene(scene(["later_reconstruction"], explicit=True), records, epochs, {}, rep)
        self.assertTrue(any("no phase covering" in e for e in rep.errors))

    def test_blender_orchestrator_respects_membership(self):
        # Execute the real bpy-free nested selector, rather than mocking Blender's
        # geometry engine or duplicating the selector in this test.
        tree = ast.parse((ROOT / "generators" / "build.py").read_text())
        function = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)
                        and n.name == "phases_in_scenes")
        namespace = {"structure_is_selected": structure_is_selected,
                     "resolve_phase": C.resolve_phase,
                     "scenes": [scene([], explicit=True)],
                     "targets": [dt.date(1871, 10, 8)]}
        exec(compile(ast.Module(body=[function], type_ignores=[]), "build.py", "exec"), namespace)
        self.assertEqual([], namespace["phases_in_scenes"](record()))
        namespace["scenes"] = [scene()]
        self.assertEqual(["later_form"], [p["id"] for p in namespace["phases_in_scenes"](record())])

    def test_ground_contact_uses_the_first_selected_scene(self):
        building = record()
        building["archetype"] = "fixture"
        building["phases"][0].update({"position": {"utm_e": 0, "utm_n": 0},
                                     "footprint": {"polygon": [[0, 0], [1, 0], [1, 1], [0, 1]]}})
        early = scene([], explicit=True)
        late = {**scene(), "id": "1904", "target_date": "1904-07-01", "terrain_epoch": "late"}
        missing = SimpleNamespace(covers=lambda e, n: False, height=lambda e, n: 0)
        land = SimpleNamespace(covers=lambda e, n: True, height=lambda e, n: 0)
        contacts = {"fixture": {"mode": "perimeter", "anchor": None, "contact_z": None}}
        args = ({"later_reconstruction": building}, {"1871": early, "1904": late},
                V.Report(), land, (0, 0), contacts)
        kwargs = {"resolvers": {"fixture": lambda phase: object()},
                  "fields": {"e1871_prefire": missing, "late": land}}
        self.assertEqual([], V.unlanded_values(*args, **kwargs))
        del early["structure_ids"]
        self.assertEqual(1, len(V.unlanded_values(*args, **kwargs)))

    def test_bake_reach_cannot_be_satisfied_by_an_excluded_scene(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "assets").mkdir()
            (root / "assets" / "manifest.json").write_text(json.dumps({"assets": {
                "later.glb": {"structure_id": "later_reconstruction", "phase_id": "later_form"}}}))
            with patch.object(V, "ROOT", root):
                rep = V.Report()
                V.run_bake_reach_check({"later_reconstruction": record()},
                                       {"1871": scene([], explicit=True)}, rep)
                self.assertTrue(any("no scene" in e for e in rep.errors))
                rep = V.Report()
                V.run_bake_reach_check({"later_reconstruction": record()}, {"1871": scene()}, rep)
                self.assertFalse(rep.errors)

    def test_every_pure_emitter_keeps_scene_metadata_scoped(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            scenes = root / "data" / "scenes"
            scenes.mkdir(parents=True)
            (scenes / "1871.json").write_text(json.dumps(scene([], explicit=True)))
            legacy = {**scene(), "id": "1904", "target_date": "1904-07-01"}
            (scenes / "1904.json").write_text(json.dumps(legacy))
            for name in EMITTERS:
                with self.subTest(emitter=name):
                    module = importlib.import_module(name)
                    with patch.object(module, "ROOT", root):
                        self.assertEqual(["1904"], [sid for sid, _ in module._scenes(record())])

    def test_empty_scene_compiles_without_importing_named_structures(self):
        with tempfile.TemporaryDirectory() as directory, contextlib.ExitStack() as stack:
            data = Path(directory)
            for folder in ("scenes", "structures"):
                (data / folder).mkdir()
            (data / "scenes" / "1871.json").write_text(json.dumps(scene([], explicit=True)))
            (data / "structures" / "later_reconstruction.json").write_text(json.dumps(record()))
            (data / "datum.json").write_text("{}")
            stack.enter_context(patch.object(C, "DATA", data))
            for name in ("compile_residents", "compile_lodging"):
                stack.enter_context(patch.object(C, name, return_value={}))
            for name in ("compile_versions", "compile_exclusions", "compile_ground",
                         "compile_fauna_sources", "compile_flora_sources", "compile_flora_clamp",
                         "compile_residents_sources"):
                stack.enter_context(patch.object(C, name, return_value=0))
            stack.enter_context(patch.object(C, "has_own_people", return_value=False))
            stack.enter_context(patch.object(C, "compile_streets", return_value=(None, [])))
            stack.enter_context(patch.object(C, "compile_intersections", return_value=[]))
            stack.enter_context(patch.object(C, "on_the_ground", return_value=[]))
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(0, C.compile_scene("1871", {}, {}))
            index = json.loads((data / "sidecars" / "1871" / "index.json").read_text())
            self.assertEqual([], index["structures"])
            self.assertEqual([], index["excluded_by_date"])
            self.assertEqual(["later_reconstruction"], index["excluded_by_scope"])

    def test_zero_named_sidecars_is_a_successful_cli_compile(self):
        with patch.object(sys, "argv", ["compile_scene.py", "--scene", "1871"]), \
                patch.object(C, "compile_scene", return_value=0):
            self.assertEqual(0, C.main())


if __name__ == "__main__":
    unittest.main()
