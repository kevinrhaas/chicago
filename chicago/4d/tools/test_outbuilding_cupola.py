#!/usr/bin/env python3
"""Hold the explicit reconstructed cupola boundary without importing Blender.

Occurrence-only records must not activate a shape; an opted-in head must seat
through both slopes and remain reconstructed even when occurrence is attested.
This exercises actual producer geometry, not a native-export or image verdict.
"""
from __future__ import annotations

import copy
import math
from pathlib import Path
import sys
import types

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "generators"))
sys.modules.setdefault("bpy", types.ModuleType("bpy"))
from archetypes import outbuilding as builder  # noqa: E402
from archetypes.outbuilding_params import ParamError, from_phase  # noqa: E402
from common.mesh import MeshBuilder  # noqa: E402


def main() -> None:
    phase = {"footprint": {"polygon": [[0, 0], [14.4, 0], [14.4, 9.4], [0, 9.4]]},
             "form": {"roof_type": {"value": "gable"},
                      "roof_pitch_deg": {"value": 32.0},
                      "cupola": {"value": True, "confidence": "attested",
                                 "geometry": "absent"}}}
    p = from_phase(phase)
    assert p.cupola_shape is None, "historical occurrence must not activate geometry"
    old_capture, old_material = MeshBuilder.to_object, builder.simple_material
    MeshBuilder.to_object = lambda self, mats: (self.verts, self.faces, self.conf,
                                               self.mat_index, mats)
    builder.simple_material = lambda *args, **kwargs: (args, kwargs)
    try:
        a = builder.build(p, "control")
        no_occurrence = copy.deepcopy(phase)
        del no_occurrence["form"]["cupola"]
        assert a == builder.build(from_phase(no_occurrence), "control")
    finally:
        MeshBuilder.to_object, builder.simple_material = old_capture, old_material
    form = phase["form"]
    for name, value in {"cupola_shape": "box_pyramid", "cupola_width_m": 1.2,
                        "cupola_body_height_m": 1.0, "cupola_roof_rise_m": 0.45}.items():
        form[name] = {"value": value, "confidence": "reconstructed"}
    p = from_phase(phase)
    mesh = MeshBuilder("cupola-control")
    builder._cupola(mesh, p)
    assert mesh.verts and set(mesh.conf) == {1.0}
    assert all(math.isfinite(c) for vertex in mesh.verts for c in vertex)
    roof_at_side = p.apex_z_m - 0.6 * math.tan(math.radians(p.roof_pitch_deg))
    assert min(v[2] for v in mesh.verts) < roof_at_side - 0.07
    assert abs(max(v[2] for v in mesh.verts) - (p.apex_z_m + 1.45)) < 1e-6
    assert {builder.M_BOARD, builder.M_ROOF} == set(mesh.mat_index)
    for changes in ({"cupola_shape": "unknown"}, {"cupola_width_m": None},
                    {"cupola_width_m": float("nan")}, {"cupola_width_m": True},
                    {"cupola_body_height_m": 0.1}, {"cupola_roof_rise_m": 2.0},
                    {"cupola_shape": None}, {"roof_type": "shed"}):
        bad = copy.deepcopy(p)
        for key, value in changes.items():
            setattr(bad, key, value)
        try:
            bad.validate()
        except ParamError:
            pass
        else:
            raise AssertionError(f"invalid cupola accepted: {changes}")
    print(f"PASS cupola: occurrence-only exact, {len(mesh.verts)} reconstructed "
          "vertices, seated cap, eight invalid variants refused")


if __name__ == "__main__":
    main()
