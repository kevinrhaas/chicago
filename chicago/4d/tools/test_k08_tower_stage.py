#!/usr/bin/env python3
"""T-1890: a K08 round tower may carry a corbelled upper stage, and a record sizes its finial.

1801 Prairie's 18th Street tower, read off the Taylor print and HABS photograph 2, is a plain
shaft about 2.2 m across under a corbel table carrying a stage about 3.7 m across, its cornice
and cone the stage's. The kit built a tower on one ring, so the record's tower stood 2.9 m
across from grade to cone. This holds the kit and the K01 frontage to what the ticket says:

  * the shaft stands on its own ring up to the stage's storey line, capped: no eaves, no roof;
  * the stage stands on the wider ring from that line, its eaves and cone over it;
  * its corbel courses step from the stage's face back to the shaft's, each oversailing the
    one under it by no more than the kit's ratio, the lowest bearing on the shaft;
  * on a K01 frontage the ring is closed in the wall's plane above the wall head: across the
    shaft's junctions up to the lowest corbel course, across the stage's above it;
  * a record's `finial` sizes the cap's own spike;
  * a stage on an octagonal or corner tower, on no storey line, too wide, or on corbel courses
    that cannot carry it, and a finial on a cap that has none, are refused.

    python3 tools/test_k08_tower_stage.py
"""

from __future__ import annotations

import copy
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "generators"))

from archetypes import k01_frontage as K1  # noqa: E402
from archetypes import k01_frontage_params as KP  # noqa: E402
from archetypes import k08_bays as K8  # noqa: E402

NORTH = "k01.wall.side.north"
failures = []


def check(ok, what):
    print(("ok   " if ok else "FAIL ") + what)
    if not ok:
        failures.append(what)


def storeys(*heights):
    win = {"opening": "k06.opening.sash_2over2_flat", "clear_width_m": 0.8, "clear_height_m": 1.6,
           "sill_m": 0.8, "at_deg": [-50, 0, 50]}
    return [{"height_m": h, "windows": [win]} for h in heights]


def kit_tower(R1=1.1, R2=1.85, k=2, K=5, heights=(5.0, 3.9, 2.0)):
    data = K8.load()
    v = copy.deepcopy(next(x for x in data["variants"] if x["id"] == "k08.tower.round"))
    v["id"] = "test|staged"
    v["plan"] = {**v["plan"], "radius_m": R1, "centre_proud_m": 0.15}
    v["storeys"] = storeys(*heights)
    v["stage"] = {"from_storey": k, "radius_m": R2, "corbel_courses": K}
    return v, data


def radius(q, cz=0.15):
    return math.hypot(q[0], q[2] - cz)


def kit_checks():
    v, data = kit_tower()
    b = K8.Bay(v, data, "full").build(board=False)
    m = b.meta
    check(m["levels_m"] == [0.0, 5.0, 8.9, 10.9] and m["wall_top_m"] == 10.9,
          f"the staged tower's storey lines run on through its stage ({m['levels_m']})")
    wall = b.prims["wall"].pos
    shaft = [radius(q) for q in wall if 1.0 < q[1] < 7.5 and q[2] > 0.5]
    stage = [radius(q) for q in wall if 9.2 < q[1] < 10.6 and q[2] > 0.5]
    check(bool(shaft) and max(abs(r - 1.1) for r in shaft) < 0.02,
          f"the shaft stands on its own ring ({min(shaft):.3f}-{max(shaft):.3f} m against 1.1)")
    check(bool(stage) and max(abs(r - 1.85) for r in stage) < 0.02,
          f"the stage stands on the wider ring ({min(stage):.3f}-{max(stage):.3f} m against 1.85)")
    st = m["stage"]
    cb = K8.part(v, data, "corbel")
    check(st["courses"] == 5 and abs(st["reach_m"] - 0.75) < 1e-9
          and st["step_m"] <= cb["max_oversail_ratio"] * cb["course_height_m"] + 1e-9,
          f"five corbel courses step 0.75 m back to the shaft, {st['step_m']} m each "
          f"(at most {cb['max_oversail_ratio'] * cb['course_height_m']:.3f})")
    check(abs(st["bottom_m"] - 7.9) < 1e-9 and 1.1 < 1.85 - 5 * st["step_m"] < 1.1 + st["step_m"] + 1e-9,
          f"the lowest course at {st['bottom_m']} m bears on the shaft")
    corbel = b.prims["corbel"].pos
    check(bool(corbel) and min(q[1] for q in corbel) >= 7.9 - 1e-6 and max(q[1] for q in corbel) <= 8.9 + 1e-6,
          "the corbel courses stand between the lowest course and the stage's floor")
    soffit_y = [q[1] for q in b.prims.get("soffit", K8.Prim("soffit")).pos]
    check(not [y for y in soffit_y if y < 10.0], "the shaft is capped: no eaves at its top")
    roof = b.prims["roof"].pos
    check(min(q[1] for q in roof) > 10.9 - 1e-6 and abs(m["roof"]["eave_radius_m"] - (1.85 + m["overhang_m"])) < 1e-6,
          f"the cone is the stage's: its eaves {m['roof']['eave_radius_m']} m out, none under the stage's wall top")

    for why, kw in (("a stage on corbel courses that cannot carry it (2 courses for 0.75 m)", {"K": 2}),
                    ("a stage narrower than its shaft", {"R2": 1.0}),
                    ("a stage on no storey line", {"k": 3})):
        v, data = kit_tower(**kw)
        try:
            K8.Bay(v, data, "full").build(board=False)
            check(False, f"{why}: refused")
        except ValueError as e:
            check(True, f"{why}: refused ({str(e)[:80]}...)")


def record(sid, tower):
    st = copy.deepcopy(json.loads((ROOT / "data" / "structures" / f"{sid}.json").read_text()))
    phase = st["phases"][-1]
    bays = phase["form"].setdefault("bays", {"value": [], "confidence": "reconstructed"})
    bays["value"] = list(bays["value"]) + [tower]
    return st, phase


def tower(**extra):
    return {"id": "test_tower", "variant": "k08.tower.round", "wall": NORTH, "s_m": 9.5,
            "plan": {"radius_m": 1.1, "centre_proud_m": 0.15}, "storeys": storeys(3.8, 6.4, 2.0),
            "stage": {"from_storey": 2, "radius_m": 1.85, "corbel_courses": 5}, **extra}


def refused(t, why):
    st, phase = record("house_1600_prairie", t)
    try:
        KP.from_phase(phase, st)
    except KP.ParamError as e:
        check(True, f"{why}: refused ({str(e)[:80]}...)")
        return
    check(False, f"{why}: refused")


def frontage_checks():
    t = tower(finial={"height_m": 2.4, "radius_m": 0.15},
              roof={"kind": "cone", "pitch": 2.5, "covering": "slate_pennsylvania", "finial": True})
    st, phase = record("house_1600_prairie", t)
    p = KP.from_phase(phase, st)
    a = K1.build(p, st["id"])
    b = next(x for x in p.bays if x["id"].endswith("test_tower"))
    built = K8.Bay(b["variant"], K8.load(), "full").build(board=False)
    E, sg = p.eave_m, built.meta["stage"]
    check(abs(built.meta["finial"]["top_m"] - built.meta["roof"]["apex"][1] - 2.4) < 1e-6,
          f"the record's finial stands 2.4 m over the cone's apex (to {built.meta['finial']['top_m']} m)")
    D, W = p.depth_m, p.width_m
    body = a.prims["bay_stone"]
    s0, s1 = b["span_m"]
    j0, j1 = (b["s_m"] + x for x in sg["junctions_x"])

    def back(y_lo, y_hi):
        out = []
        for i in range(0, len(body.idx), 3):
            tri = [body.pos[j] for j in body.idx[i:i + 3]]
            if body.nrm[body.idx[i]][2] > 0.99 and all(abs(q[2] - (-W + 0.001)) < 1e-6 for q in tri) \
                    and all(y_lo - 1e-6 <= q[1] <= y_hi + 1e-6 for q in tri):
                out.append(tri)
        return out

    def extent(tris):
        xs = [q[0] for t in tris for q in t]
        return (D - max(xs), D - min(xs)) if xs else (None, None)

    lo = back(E, sg["bottom_m"])
    hi = back(sg["bottom_m"], built.meta["wall_top_m"])
    e_lo, e_hi = extent(lo), extent(hi)
    check(bool(lo) and abs(e_lo[0] - s0) < 0.002 and abs(e_lo[1] - s1) < 0.002,
          f"under the corbel the ring is closed across the shaft's junctions (s {s0:.3f}..{s1:.3f})")
    check(bool(hi) and abs(e_hi[0] - j0) < 0.002 and abs(e_hi[1] - j1) < 0.002,
          f"over it, across the stage's (s {j0:.3f}..{j1:.3f})")

    refused(tower(stage={"from_storey": 2, "radius_m": 3.0, "corbel_courses": 5}),
            "a stage 1.9 m wider than its shaft")
    refused(tower(stage={"from_storey": 0, "radius_m": 1.85, "corbel_courses": 5}),
            "a stage from grade")
    refused(tower(variant="k08.tower.octagonal", plan={"radius_m": 1.6, "centre_proud_m": 0.6123}),
            "a stage on an octagonal tower")
    refused(tower(finial={"height_m": 5.0, "radius_m": 0.15}), "a finial 5 m tall")
    refused(tower(finial={"height_m": 2.0, "radius_m": 0.15},
                  roof={"kind": "cone", "pitch": 2.5, "covering": "slate_pennsylvania"}),
            "a finial on a cap that has none")


def main() -> int:
    kit_checks()
    frontage_checks()
    if failures:
        print(f"test_k08_tower_stage: {len(failures)} failed")
        return 1
    print("test_k08_tower_stage: all passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
