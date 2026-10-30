#!/usr/bin/env python3
"""CPU regression checks for T-2376/T-2383/T-2385 pictured frame-tavern forms.

These inspect the real accumulator and opening kit, without Blender/exporting.
They protect opt-in geometry, materials and confidence, not image-match verdicts.
The same-camera preview receipts separately cover actual Blender/glTF treatment.
"""
from __future__ import annotations

import collections
import copy
import dataclasses
import json
import inspect
import math
from pathlib import Path
import ast
import sys
import types
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "generators"))
sys.modules.setdefault("bpy", types.ModuleType("bpy"))
from archetypes import frame_tavern as builder  # noqa: E402
from archetypes.frame_tavern_params import (  # noqa: E402
    CONSUMED, FrameTavernParams, ParamError, from_phase,
)
from common.mesh import MeshBuilder  # noqa: E402


def record_params(structure_id, phase_id, version=None):
    path = ROOT / "data/structures" / f"{structure_id}.json"
    if version is not None:
        path = ROOT / "data/structures/versions" / structure_id / f"{version}.json"
    record = json.loads(path.read_text())
    phase = next(p for p in record["phases"] if p["id"] == phase_id)
    return record, phase, from_phase(phase, record)


def signature(result):
    mesh, materials = result
    return (mesh.verts, mesh.faces, mesh.conf, mesh.mat_index, mesh.named, materials)


def normal(mesh, face):
    a, b, c = (mesh.verts[i] for i in face[:3])
    u = [b[i] - a[i] for i in range(3)]
    v = [c[i] - a[i] for i in range(3)]
    return (u[1]*v[2]-u[2]*v[1], u[2]*v[0]-u[0]*v[2], u[0]*v[1]-u[1]*v[0])


class PictureFeatures(unittest.TestCase):
    def setUp(self):
        # Preserve named-kit material specifications and original accumulator indices.
        self.emit = patch.object(MeshBuilder, "to_object", lambda b, mats=None: (b, mats))
        self.material = patch.object(builder, "simple_material", lambda n, *a, **kw: (n, a, kw))
        self.emit.start()
        self.material.start()
        self.addCleanup(self.emit.stop)
        self.addCleanup(self.material.stop)

    def assert_valid_mesh(self, mesh):
        self.assertTrue(all(math.isfinite(c) for v in mesh.verts for c in v))
        self.assertTrue(all(0 <= c <= 1 for c in mesh.conf))
        for face in mesh.faces:
            self.assertGreater(sum(c*c for c in normal(mesh, face)), 1e-14)

    def test_reconstructed_dark_stock_roof_colour_changes_only_material_and_roof_confidence(self):
        from common import materials
        _, _, p = record_params("tremont_house_1", "frame_1833")
        p = dataclasses.replace(p,confidence={**p.confidence,"roof_type":"attested","roof_pitch_deg":"attested"})
        p = dataclasses.replace(p, roof_colour="dark_brown")
        baseline = dataclasses.replace(p, roof_colour=None)
        before, bm = builder.build(baseline, "tone")
        after, am = builder.build(p, "tone")
        self.assertEqual((before.verts,before.faces,before.mat_index,before.named),
                         (after.verts,after.faces,after.mat_index,after.named))
        self.assertEqual(bm[:1]+bm[2:],am[:1]+am[2:])
        self.assertEqual(am[builder.M_ROOF][1][0],materials.roof_finish("darkened").rgba)
        roof_vertices={i for face,mat in zip(after.faces,after.mat_index)
                       if mat==builder.M_ROOF for i in face}
        self.assertTrue(roof_vertices)
        self.assertTrue(any(before.conf[i]<1 for i in roof_vertices))
        self.assertTrue(all(after.conf[i]==1 for i in roof_vertices))
        self.assertTrue(all(a==b for i,(a,b) in enumerate(zip(before.conf,after.conf))
                            if i not in roof_vertices))
        for grade in ("attested","inferred"):
            with self.assertRaises(ParamError):
                dataclasses.replace(p,confidence={**p.confidence,"roof_colour":grade}).validate()
        with self.assertRaises(ParamError):
            dataclasses.replace(p,roof_colour="imaginary_black").validate()

    def test_deep_roof_changes_only_selected_stock_linear_rgb(self):
        from common import materials
        _, _, p = record_params("tremont_house_1", "frame_1833")
        before, bm = builder.build(dataclasses.replace(p, roof_colour="dark_brown"), "tone")
        after, am = builder.build(dataclasses.replace(p, roof_colour="deep_brown"), "tone")
        self.assertEqual((before.verts, before.faces, before.mat_index, before.named, before.conf),
                         (after.verts, after.faces, after.mat_index, after.named, after.conf))
        self.assertEqual(bm[:1] + bm[2:], am[:1] + am[2:])
        stock = materials.roof_finish("darkened").rgba
        self.assertEqual(am[builder.M_ROOF][1][0], tuple(c * 0.25 for c in stock[:3]) + (stock[3],))
        self.assertEqual(bm[builder.M_ROOF][2], am[builder.M_ROOF][2])
        for grade in ("attested", "inferred"):
            with self.assertRaises(ParamError):
                dataclasses.replace(p, roof_colour="deep_brown",
                                    confidence={**p.confidence, "roof_colour": grade}).validate()

    def test_original_positional_constructor_and_defaults_are_preserved(self):
        # These are the original forty positional parameters, before picture
        # opt-ins. A new field inserted among them must not change caller meaning.
        legacy = (
            "width_m", "depth_m", "stories", "wall_height_m", "roof_type",
            "roof_pitch_deg", "construction", "paint", "shutters", "shutter_type",
            "gallery", "entrance_frontispiece", "siding_exposure_m", "chimneys",
            "elevation_scheme", "chimney_material", "roof_colour", "chimney_placement",
            "side_entrance_face", "rear_ell", "rear_ell_width_m", "rear_ell_depth_m",
            "rear_ell_wall_m", "rear_ell_door", "upper_windows", "stovepipes",
            "log_wing", "log_wing_width_m", "log_wing_depth_m", "log_wing_height_m",
            "log_wing_door", "log_wing_porch_hood", "cross_wing", "cross_wing_depth_m",
            "cross_wing_end", "finish_key", "roof_condition", "siding_lay_m",
            "siding_seed", "confidence",
        )
        signature = inspect.signature(FrameTavernParams)
        positional = tuple(name for name, p in signature.parameters.items()
                           if p.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD)
        self.assertEqual(positional, legacy)
        self.assertTrue(all(p.kind == inspect.Parameter.KEYWORD_ONLY
                            for name, p in signature.parameters.items() if name not in legacy))
        values = (
            12., 8., 2, 5.5, "gable", 37., "braced_frame", "unpainted", "green", None,
            False, False, .127, 2, "frontage", "brick", None, "frontage", None,
            False, 4., 3., 2.4, "carriage", 4, 1, False, 4., 3., 2.35, False, False,
            False, 7., "x_max", None, None, .002, "legacy-positional", {"stories": "attested"},
        )
        p = FrameTavernParams(*values)
        p.validate()
        self.assertEqual(tuple(getattr(p, name) for name in legacy), values)
        defaults = FrameTavernParams(12., 8., 2, 5.5)
        expected = {"paint": "white", "chimney_material": None, "stovepipes": 0,
                    "siding_seed": "", "confidence": {}, "gable_wall_cladding": False,
                    "first_story_height_m": None, "entry_raise_m": 0., "gable_lunette": False,
                    "gable_arch_treatment": "fanlight", "gable_arch_text": "", "corner_entry_surround": False,
                    "flagstaff": False, "flagstaff_height_m": 4.25,
                    "eaves_bays": {}, "end_windows": ()}
        for name, value in expected.items():
            self.assertEqual(getattr(defaults, name), value)
        with self.assertRaises(TypeError):
            FrameTavernParams(*values, True)  # a new opt-in cannot occupy slot41

    def test_small_legacy_fixture_keeps_old_roof_and_empty_opt_ins(self):
        p = FrameTavernParams(12.0, 8.0, 2, 5.5)
        p.validate()
        self.assertEqual((p.eaves_bays, p.end_windows, p.gable_wall_cladding), ({}, (), False))
        explicit = dataclasses.replace(p, eaves_bays={}, end_windows=(),
            gable_wall_cladding=False, first_story_height_m=None, entry_raise_m=0,
            gable_lunette=False, flagstaff=False)
        with patch.object(builder, "_win", wraps=builder._win) as windows, \
             patch.object(builder, "_door", wraps=builder._door) as doors, \
             patch.object(MeshBuilder, "add_gable_roof", autospec=True,
                          side_effect=MeshBuilder.add_gable_roof) as roof:
            result = builder.build(p, "legacy_fixture__frame")
        self.assertEqual(len(windows.call_args_list), 18)
        self.assertEqual(len(doors.call_args_list), 1)
        self.assertEqual(roof.call_count, 1)
        self.assertEqual(signature(result), signature(builder.build(explicit, "legacy_fixture__frame")))
        # The unchanged common helper closes the default roof with roof-material
        # triangles. A new opt-in must not silently repaint every legacy building.
        mesh, _ = result
        triangles = [(f, m) for f, m in zip(mesh.faces, mesh.mat_index) if len(f) == 3]
        self.assertEqual(len(triangles), 2)
        self.assertTrue(all(m == builder.M_ROOF for _, m in triangles))
        self.assertFalse(any(m == builder.M_SHUTTER for m in mesh.mat_index))
        self.assert_valid_mesh(mesh)

    def test_gable_wall_cladding_both_axes_preserves_roof_planes(self):
        for width, depth in ((12., 8.), (8., 12.)):
            with self.subTest(width=width):
                p = FrameTavernParams(width, depth, 2, 5.5, gable_wall_cladding=True)
                p.validate()
                legacy, after = MeshBuilder("legacy_roof"), MeshBuilder("wall_gables")
                expected_ridge = legacy.add_gable_roof(0, 0, width, depth, 5.5,
                    p.roof_pitch_deg, .5, builder.M_ROOF, ridge_along_x=width >= depth)
                ridge = builder._wall_clad_gable_roof(after, p, width, depth, 5.5, .5,
                                                     ridge_along_x=width >= depth)
                self.assertEqual(ridge, expected_ridge)
                points = lambda mesh, face: frozenset(tuple(round(c, 9) for c in mesh.verts[i]) for i in face)
                self.assertEqual({points(legacy, f) for f in legacy.faces[:2]},
                                 {points(after, f) for f in after.faces[:2]})
                self.assertEqual(after.mat_index[:2], [builder.M_ROOF]*2)
                self.assertTrue(all(after.conf[i] == .5 for f in after.faces[:2] for i in f))
                gables = [f for f, m in zip(after.faces, after.mat_index) if len(f) == 3 and m == builder.M_WALL]
                self.assertEqual(len(gables), 2)
                axis = 0 if width >= depth else 1
                for face in gables:
                    outward = -1 if after.verts[face[0]][axis] < 0 else 1
                    self.assertGreater(normal(after, face)[axis] * outward, 0)
                self.assertTrue(all(m == builder.M_WALL for m in after.mat_index[2:]))
                self.assertTrue(all(after.conf[i] == 1 for f in after.faces[2:] for i in f))
                self.assertGreater(len(after.faces), 4)  # relief, not just a repaint
                self.assert_valid_mesh(after)

    def test_pictured_records_use_wall_gables_in_actual_build(self):
        for structure, phase in (("green_tree_tavern", "frame_1833"),
                                 ("sauganash_hotel", "frame_1831")):
            with self.subTest(structure=structure):
                _, _, p = record_params(structure, phase)
                self.assertTrue(p.gable_wall_cladding)
                with patch.object(builder, "_wall_clad_gable_roof",
                                  wraps=builder._wall_clad_gable_roof) as roof:
                    mesh, _ = builder.build(p, structure + "__" + phase)
                self.assertEqual(roof.call_count, 1)
                triangles = [m for f, m in zip(mesh.faces, mesh.mat_index) if len(f) == 3]
                self.assertGreaterEqual(triangles.count(builder.M_WALL), 2)

    def test_tremont_openings_shutters_and_raised_entries(self):
        # Preserve the pictured canonical form and the optional Gale text reading.
        # Keep every strict opening, storey, shutter and entry regression below;
        # neither structural count alone is an image-match verdict.
        for version, stories, count, short, long, leaves in (
                (None, 3, 44, 8, 14, 88),
                ("gale-reading", 2, 28, 5, 9, 0)):
            with self.subTest(version=version or "default"):
                _, _, p = record_params("tremont_house_1", "frame_1833", version)
                self.assertEqual((p.stories, p.elevation_scheme), (stories, "corner_gable"))
                with patch.object(builder, "_win", wraps=builder._win) as windows, \
                     patch.object(builder, "_door", wraps=builder._door) as doors, \
                     patch.object(builder, "_corner_landing", wraps=builder._corner_landing) as landings, \
                     patch.object(builder, "_corner_lunettes", wraps=builder._corner_lunettes) as lunettes, \
                     patch.object(builder, "_corner_entry_surround", wraps=builder._corner_entry_surround) as surrounds:
                    mesh, _ = builder.build(p, "tremont_house_1__frame_1833")
                self.assertEqual((landings.call_count, lunettes.call_count, surrounds.call_count), (4, 1, 4))
                self.assertEqual(len(windows.call_args_list), count)
                self.assertEqual(len(doors.call_args_list), 4)
                by_face = collections.Counter(tuple(c.args[2:4]) for c in windows.call_args_list)
                self.assertEqual(by_face, {("x", 0.): short, ("x", p.width_m): short,
                                           ("y", 0.): long, ("y", p.depth_m): long})
                first = p.first_story_height_m
                self.assertIsNotNone(first)
                upper = (p.wall_height_m - first) / (stories - 1)
                levels = sorted({round(c.args[7], 9) for c in windows.call_args_list})
                expected = [first*.3] + [first + (i+.3)*upper for i in range(stories-1)]
                self.assertEqual(len(levels), stories)
                for actual, wanted in zip(levels, expected):
                    self.assertAlmostEqual(actual, wanted)
                for call in doors.call_args_list:
                    self.assertEqual(call.args[7], p.entry_raise_m)
                shutter_faces = [f for f, m in zip(mesh.faces, mesh.mat_index) if m == builder.M_SHUTTER]
                self.assertEqual(len(shutter_faces), leaves*6)
                self.assertTrue(all(mesh.conf[i] == 1 for f in shutter_faces for i in f))
                bare, _ = builder.build(dataclasses.replace(p, shutters=None), "tremont_house_1__frame_1833")
                self.assertNotIn(builder.M_SHUTTER, bare.mat_index)
                self.assert_valid_mesh(mesh)

    def test_tremont_lunette_staff_and_stack_occurrences(self):
        _, _, p = record_params("tremont_house_1", "frame_1833")
        lunette = MeshBuilder("lunette")
        # The legacy optional fanlight remains a supported default treatment.
        fanlight = dataclasses.replace(p, gable_arch_treatment="fanlight")
        builder._corner_lunettes(lunette, fanlight, p.width_m, p.depth_m, p.wall_height_m)
        glass = [f for f, m in zip(lunette.faces, lunette.mat_index) if m == builder.M_GLASS]
        self.assertTrue(glass)
        for face in glass:
            outward = -1 if lunette.verts[face[0]][0] < 0 else 1
            self.assertGreater(normal(lunette, face)[0] * outward, 0)
            self.assertTrue(all(lunette.conf[i] == 1 for i in face))
        self.assert_valid_mesh(lunette)
        with patch.object(builder, "_corner_roof_staff", wraps=builder._corner_roof_staff) as staff, \
             patch.object(builder, "_corner_slope_stacks", wraps=builder._corner_slope_stacks) as stacks:
            builder.build(p, "tremont_house_1__frame_1833")
        self.assertEqual((staff.call_count, stacks.call_count), (1, 1))
        ridge = staff.call_args.args[-1]
        spar = MeshBuilder("roof_spar")
        builder._corner_roof_staff(spar, p, p.width_m, p.depth_m, ridge)
        self.assertAlmostEqual(max(v[2] for v in spar.verts), ridge + p.flagstaff_height_m)
        self.assertTrue(all(c == 1 for c in spar.conf))
        self.assert_valid_mesh(spar)
        stack_mesh = MeshBuilder("stacks")
        builder._corner_slope_stacks(stack_mesh, p, p.width_m, p.depth_m, p.wall_height_m, builder.M_BRICK)
        self.assertEqual(len(stack_mesh.faces), 4*2*5)  # four capped shafts, undersides omitted
        self.assertTrue(all(m == builder.M_BRICK for m in stack_mesh.mat_index))
        self.assertTrue(all(c == 1 for c in stack_mesh.conf))
        self.assert_valid_mesh(stack_mesh)
        off = dataclasses.replace(p, flagstaff=False)
        self.assertEqual(signature(builder.build(off, "staff_off__frame")),
                         signature(builder.build(dataclasses.replace(off, flagstaff_height_m=7.), "staff_off__frame")))

    def test_tremont_opaque_arch_does_not_invent_glass_or_radial_bars(self):
        _, _, p = record_params("tremont_house_1", "frame_1833")
        self.assertEqual(p.gable_arch_treatment, "opaque_panel")
        mesh = MeshBuilder("opaque_arch")
        builder._corner_lunettes(mesh, p, p.width_m, p.depth_m, p.wall_height_m)
        self.assertNotIn(builder.M_GLASS, mesh.mat_index)
        self.assertIn("gable_panel", mesh.named)
        self.assertEqual(mesh.named["gable_panel"][2], .95)
        self.assertTrue(all(c == 1 for c in mesh.conf))
        fan = MeshBuilder("old_fanlight")
        builder._corner_lunettes(fan, dataclasses.replace(p, gable_arch_treatment="fanlight"),
                                 p.width_m, p.depth_m, p.wall_height_m)
        self.assertEqual(len(fan.faces)-len(mesh.faces), 6)
        self.assert_valid_mesh(mesh)

    def test_reconstructed_arch_word_is_inside_panel_and_only_pictured_gable(self):
        _, _, p = record_params("tremont_house_1", "frame_1833")
        self.assertEqual(p.gable_arch_text, "TREMONT")
        mesh = MeshBuilder("arch_name")
        builder._corner_arch_letters(mesh, p, p.depth_m, p.wall_height_m)
        self.assertEqual((len(mesh.faces), len(mesh.verts)), (24, 96))
        self.assertTrue(all(c == 1.0 for c in mesh.conf))
        self.assertTrue(all(abs(v[0] + builder.ROOF_OVERHANG + .030) < 1e-9 for v in mesh.verts))
        self.assertTrue(all(normal(mesh, face)[0] < 0 for face in mesh.faces))
        # From the x_min face, viewer-right is local negative-v: text must not mirror.
        first_t=sum(v[1] for v in mesh.verts[:8])/8
        last_t=sum(v[1] for v in mesh.verts[-8:])/8
        self.assertGreater(first_t,last_t)
        for _, u, z in mesh.verts:
            x = abs(u-p.depth_m/2)
            half = p.depth_m*.20-.09
            top = p.wall_height_m+.64+.56*math.sqrt(1-(x/half)**2)
            self.assertGreaterEqual(z, p.wall_height_m+.64)
            self.assertLess(z, top)
        self.assertEqual(mesh.named["gable_letter_paint"][1:], ((.65,.62,.55,1.),.95))
        self.assert_valid_mesh(mesh)

    def test_arch_name_default_is_off_and_invalid_claims_are_refused(self):
        _, _, p = record_params("tremont_house_1", "frame_1833")
        blank = MeshBuilder("no_arch_name")
        builder._corner_arch_letters(blank, dataclasses.replace(p,gable_arch_text=""),p.depth_m,p.wall_height_m)
        self.assertFalse(blank.verts)
        for value in (None,True,1,"TREMONT HOUSE","OTHER"):
            with self.subTest(value=value), self.assertRaises(ParamError):
                dataclasses.replace(p,gable_arch_text=value).validate()
        for change in ({"gable_arch_treatment":"fanlight"},{"gable_lunette":False},
                       {"confidence":{**p.confidence,"gable_arch_text":"attested"}},
                       {"confidence":{**p.confidence,"gable_arch_text":"inferred"}}):
            with self.subTest(change=change), self.assertRaises(ParamError):
                dataclasses.replace(p,**change).validate()

    def test_arch_name_is_consumed_as_exact_keyword_only_record_value(self):
        self.assertIn("gable_arch_text",CONSUMED)
        parameter=inspect.signature(FrameTavernParams).parameters["gable_arch_text"]
        self.assertEqual(parameter.kind,inspect.Parameter.KEYWORD_ONLY)
        self.assertEqual(parameter.default,"")
        record, phase, p = record_params("tremont_house_1","frame_1833")
        self.assertEqual(p.gable_arch_text,phase["form"]["gable_arch_text"]["value"])
        bad=copy.deepcopy(phase);bad["form"]["gable_arch_text"]["confidence"]="attested"
        with self.assertRaises(ParamError):from_phase(bad,record)

    def test_green_tree_front_ground_layout_is_sparse_and_reconstructed(self):
        record, phase, p = record_params("green_tree_tavern", "frame_1833")
        self.assertEqual(p.front_ground_layout, [.20, .50, .78])
        self.assertIn("front_ground_layout", CONSUMED)
        signature = inspect.signature(FrameTavernParams)
        self.assertEqual(signature.parameters["front_ground_layout"].kind,
                         inspect.Parameter.KEYWORD_ONLY)
        calls = []
        with patch.object(builder, "_win", lambda *a, **k: calls.append(("win", a[2:]))),              patch.object(builder, "_door", lambda *a, **k: calls.append(("door", a[2:]))):
            builder._fenestration_gable_front(MeshBuilder("layout"), p, p.width_m,
                                              p.depth_m, p.wall_height_m, 8., .5)
        front_ground = [(kind, a) for kind, a in calls
                        if a[0] == "y" and a[1] == p.depth_m and a[2] == 1
                        and a[5] < p.wall_height_m / p.stories]
        self.assertEqual([kind for kind, _ in front_ground], ["door", "win", "win"])
        for (_, a), at, width in zip(front_ground, (.20, .50, .78), (1.20, .85, .85)):
            self.assertEqual(a[3:5], (p.width_m*at-width/2, p.width_m*at+width/2))
            self.assertEqual(a[-1], 1.)
        # Exterior +y view, yaw180: camera-right is -u. Physical screen order
        # must be two sash then the door, not merely ascending local stations.
        screen_order = [kind for kind, a in sorted(front_ground,
                        key=lambda call: -(call[1][3]+call[1][4])/2)]
        self.assertEqual(screen_order, ["win", "win", "door"])
        legacy = copy.deepcopy(record)
        del legacy["phases"][0]["form"]["front_ground_layout"]
        self.assertIsNone(from_phase(legacy["phases"][0], legacy).front_ground_layout)

    def test_front_ground_layout_refuses_bad_shape_spacing_or_grade(self):
        _, _, p = record_params("green_tree_tavern", "frame_1833")
        for bad in (False, (), [], [.2, .8], [True, .5, .8], [math.nan, .5, .8],
                    [.2, math.inf, .8], [".2", .5, .8], [.5, .2, .8],
                    [-.1, .5, .8], [.2, .5, 1.], [.2, .22, .8]):
            with self.subTest(bad=bad), self.assertRaises(ParamError):
                dataclasses.replace(p, front_ground_layout=bad).validate()
        for grade in ("attested", "inferred"):
            with self.subTest(grade=grade), self.assertRaises(ParamError):
                dataclasses.replace(p, confidence={**p.confidence,
                                      "front_ground_layout": grade}).validate()
        with self.assertRaises(ParamError):
            dataclasses.replace(p, elevation_scheme="frontage").validate()

    def test_front_ground_actual_geometry_stations_are_native_hashed_property(self):
        from mesh_inputs import _params_doc
        _, _, p = record_params("green_tree_tavern", "frame_1833")
        self.assertIsInstance(FrameTavernParams.resolved_front_ground_stations, property)
        self.assertEqual(_params_doc(p)["inferred"]["resolved_front_ground_stations"],
                         p.resolved_front_ground_stations)
        self.assertEqual(p.resolved_front_ground_stations,
                         (p.width_m*.20, (p.width_m*.50, p.width_m*.78)))

    def test_front_ground_access_reads_exact_phase_not_sidecar_form(self):
        record, phase, p = record_params("green_tree_tavern", "frame_1833")
        decoy = copy.deepcopy(phase)
        decoy["id"] = "other_phase_first"
        del decoy["form"]["front_ground_layout"]
        record = {**record, "phases": [decoy, phase]}
        tree = ast.parse((ROOT / "tools/generate_entrances.py").read_text())
        node = next(n for n in tree.body if isinstance(n, ast.FunctionDef)
                    and n.name == "front_doors")
        fake = types.SimpleNamespace(STRUCTURES=ROOT / "data/structures",
            _load=lambda path: record,
            _front_edge=lambda poly: (0., p.width_m, p.depth_m))
        ns = {"gbs": fake, "_frame_tavern_params": from_phase,
              "TAVERN_DOOR_W_M": 1.2}
        exec(compile(ast.Module(body=[node], type_ignores=[]), "actual_front_doors", "exec"), ns)
        sc = {"id": record["id"], "archetype": "frame_tavern", "phase": phase["id"],
              "footprint": phase["footprint"], "form": {"front_ground_layout": {"value": [.8,.9,.95]}}}
        doors, reader = ns["front_doors"](sc)
        c, _ = p.resolved_front_ground_stations
        self.assertEqual(doors, [{"kind": "door", "u0": c-.6, "u1": c+.6}])
        self.assertIn("selected phase", reader)
        with self.assertRaises(ValueError):
            ns["front_doors"]({**sc, "phase": "nonexistent"})

    def test_green_tree_override_changes_only_named_eaves_face(self):
        _, _, p = record_params("green_tree_tavern", "frame_1833")
        self.assertEqual(p.eaves_bays, {"x_min": 7})
        captures = []
        # An attested fenestration fixture isolates the weaker override's tint.
        p = dataclasses.replace(p, confidence={**p.confidence, "fenestration": "attested",
            "elevation_scheme": "attested", "eaves_bays": "inferred"})
        for current in (p, dataclasses.replace(p, eaves_bays={})):
            with patch.object(builder, "_win", wraps=builder._win) as windows:
                builder.build(current, "green_tree_tavern__frame_1833")
            captures.append([c.args[2:] for c in windows.call_args_list])
        after, before = captures
        upper = lambda seq, plane: [c for c in seq if c[0] == "x" and c[1] == plane and c[5] > 2.5]
        self.assertEqual((len(upper(after, 0)), len(upper(before, 0))), (7, 6))
        self.assertEqual(upper(after, p.width_m), upper(before, p.width_m))
        self.assertEqual([c for c in after if c[0] == "y"], [c for c in before if c[0] == "y"])
        self.assertTrue(all(c[-1] == .5 for c in upper(after, 0)))
        self.assertTrue(all(c[-1] == 0 for c in upper(after, p.width_m)))

    def test_sauganash_only_states_three_main_end_sash(self):
        _, _, p = record_params("sauganash_hotel", "frame_1831")
        self.assertEqual(len(p.end_windows), 3)
        with patch.object(builder, "_end_windows", wraps=builder._end_windows) as ends:
            builder.build(p, "sauganash_hotel__frame_1831")
        self.assertEqual(ends.call_count, 1)
        with patch.object(builder, "_win", wraps=builder._win) as windows:
            mesh = MeshBuilder("end_sash")
            builder._end_windows(mesh, p, p.width_m, p.depth_m, p.wall_height_m)
        calls = windows.call_args_list
        self.assertEqual(len(calls), 3)
        self.assertEqual([c.args[3] for c in calls], [p.width_m, p.width_m, p.width_m + builder.ROOF_OVERHANG])
        self.assertTrue(all(c.args[2] == "x" and c.args[4] == 1 for c in calls))
        self.assertEqual(calls[-1].kwargs["skin"], 0.)
        self.assert_valid_mesh(mesh)
        blank = MeshBuilder("blank_end")
        builder._end_windows(blank, dataclasses.replace(p, end_windows=()), p.width_m, p.depth_m, p.wall_height_m)
        self.assertFalse(blank.verts)

    def test_opt_in_invalid_configurations_are_refused(self):
        _, _, corner = record_params("tremont_house_1", "frame_1833")
        _, _, green = record_params("green_tree_tavern", "frame_1833")
        _, _, hotel = record_params("sauganash_hotel", "frame_1831")
        cases = [(corner, d) for d in ({"width_m": 5.5}, {"depth_m": 16.},
            {"entry_raise_m": float("nan")}, {"entry_raise_m": True},
            {"first_story_height_m": 4.}, {"first_story_height_m": True},
            {"flagstaff_height_m": float("inf")}, {"flagstaff_height_m": True},
            {"entry_raise_m": 1.21},
            {"flagstaff": 1}, {"gable_lunette": "true"}, {"roof_pitch_deg": 10.},
            {"gable_arch_treatment": "text"}, {"gable_lunette": False},
            {"corner_entry_surround": 1},
            {"chimneys": 3}, {"roof_type": "hip"}, {"log_wing": True})]
        cases += [(green, {"eaves_bays": d}) for d in ({"x_min": True}, {"y_min": 7}, {"x_min": 20})]
        cases += [(hotel, {"end_windows": d}) for d in (
            (("+z", .5, 4., .7, 1.),), (("+x", .5, 20., .7, 1.),),
            (("+x", .5, 5.5, .7, 1.),), (("+x", .5, float("nan"), .7, 1.),))]
        cases += [(hotel, {"gable_wall_cladding": v}) for v in (1, "true", None)]
        cases += [(FrameTavernParams(12., 8., 2, 5.5),
                   {"gable_wall_cladding": True, "roof_type": "hip"})]
        for p, changes in cases:
            with self.subTest(changes=changes), self.assertRaises(ParamError):
                dataclasses.replace(p, **changes).validate()

    def test_record_values_are_consumed_and_not_truthy_coerced(self):
        fields = {"eaves_bays", "end_windows", "first_story_height_m", "entry_raise_m",
                  "gable_lunette", "flagstaff", "flagstaff_height_m", "gable_wall_cladding",
                  "gable_arch_treatment", "corner_entry_surround", "gable_arch_text"}
        self.assertTrue(fields <= CONSUMED)
        record, phase, _ = record_params("green_tree_tavern", "frame_1833")
        for value in (1, "false", None):
            bad = copy.deepcopy(phase)
            bad["form"]["gable_wall_cladding"]["value"] = value
            with self.subTest(value=value), self.assertRaises(ParamError):
                from_phase(bad, record)


if __name__ == "__main__":
    unittest.main()
