#!/usr/bin/env python3
"""T-2787: a K01 frontage carries a K08 tower that stands past its main eave.

The kit piece 1801 Prairie's move onto K01 needs (T-2789): its round tower on the 18th
Street flank and its north-east turret rise past the eave with their cones over the main
roof. No house in the scene carries a tower yet, so this builds two committed K01 records
with one added — a hipped brick house (1600) and a mansard (1637) — and holds the
assembly to what the ticket says:

  * the tower is built: its cap stands over the main roof, its wall top over the eave;
  * its ring is closed above the eave, in the wall's plane, facing the roof behind it,
    from the wall head to its wall top and on to its eave;
  * the K10 wall head stops at it: no bracket stands in its span and the bed moulding
    has no length inside it;
  * the host openings behind it are dropped, and a door behind one is refused;
  * a tower whose wall top is under the eave, a tower sized past its kit range, and a
    plan sized by anything but its radius and centre are refused.

    python3 tools/test_k01_tower.py
"""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "generators"))

from archetypes import k01_frontage as K1  # noqa: E402
from archetypes import k01_frontage_params as KP  # noqa: E402

NORTH = "k01.wall.side.north"
failures = []


def check(ok, what):
    print(("ok   " if ok else "FAIL ") + what)
    if not ok:
        failures.append(what)


def record(sid, tower):
    st = json.loads((ROOT / "data" / "structures" / f"{sid}.json").read_text())
    st = copy.deepcopy(st)
    phase = st["phases"][-1]
    bays = phase["form"].setdefault("bays", {"value": [], "confidence": "reconstructed"})
    bays["value"] = list(bays["value"]) + [tower]
    return st, phase


def tower(variant="k08.tower.round", s=9.5, wall=NORTH, **extra):
    return {"id": "test_tower", "variant": variant, "wall": wall, "s_m": s, **extra}


def storeys(*heights):
    win = {"opening": "k06.opening.sash_2over2_flat", "clear_width_m": 0.8, "clear_height_m": 1.6,
           "sill_m": 0.8, "at_deg": [-50, 0, 50]}
    return [{"height_m": h, "windows": [win]} for h in heights]


def refused(sid, t, why):
    st, phase = record(sid, t)
    try:
        KP.from_phase(phase, st)
    except KP.ParamError as e:
        check(True, f"{why}: refused ({str(e)[:90]}...)")
        return
    check(False, f"{why}: refused")


def built(sid, t, label):
    st, phase = record(sid, t)
    p = KP.from_phase(phase, st)
    a = K1.build(p, st["id"])
    K1.to_glb(a, st["id"], phase["id"], ["1904"], {})      # it writes
    b = next(x for x in p.bays if x["id"].endswith("test_tower"))
    s0, s1 = b["span_m"]
    E = p.eave_m
    wall_top = sum(x["height_m"] for x in b["variant"]["storeys"])
    check(wall_top >= E + KP.TOWER_PAST_EAVE_M, f"{label}: wall top {wall_top:.2f} m stands over the eave {E:.2f} m")

    # the cap: copper over the main roof, its apex over the main ridge
    cap = a.prims["bay_copper"].pos if "bay_copper" in a.prims else []
    check(bool(cap) and max(q[1] for q in cap) > p.ridge_m,
          f"{label}: the cap stands over the main roof (apex {max((q[1] for q in cap), default=0):.2f} m, "
          f"ridge {p.ridge_m:.2f} m)")
    # the north wall's frame: O at (D, 0, -W), R = -X, outward normal -Z; a point at s on it
    # has x = D - s, z = -W
    D, W = p.depth_m, p.width_m
    body = a.prims["bay_stone"]

    def back_faces(y_lo, y_hi):
        out = []
        for t in range(0, len(body.idx), 3):
            tri = [body.pos[i] for i in body.idx[t:t + 3]]
            n = body.nrm[body.idx[t]]
            if n[2] > 0.99 and all(abs(q[2] - (-W + 0.001)) < 1e-6 for q in tri) \
                    and all(y_lo - 1e-6 <= q[1] <= y_hi + 1e-6 for q in tri):
                out.append(tri)
        return out

    lower = back_faces(E, wall_top)
    area = sum(abs((t[1][0] - t[0][0]) * (t[2][1] - t[0][1]) - (t[2][0] - t[0][0]) * (t[1][1] - t[0][1])) / 2
               for t in lower)
    want = (s1 - s0) * (wall_top - E)
    check(abs(area - want) < 0.02 * want,
          f"{label}: the ring is closed above the wall head, facing the roof ({area:.2f} of {want:.2f} m2)")
    xs = [q[0] for t in lower for q in t]
    check(bool(xs) and abs(min(xs) - (D - s1)) < 0.002 and abs(max(xs) - (D - s0)) < 0.002,
          f"{label}: ...across the ring's junctions at s {s0:.3f}..{s1:.3f}")
    upper = back_faces(wall_top, wall_top + 0.6)
    check(len(upper) >= 2, f"{label}: ...and on from its wall top to its eave")

    # the wall head: no bracket in the tower's span, no bed moulding inside it
    wh = getattr(a, "wall_head", None) or {}
    north = wh.get("bracket_runs", {}).get(NORTH, [])
    check(not [s for s in north if s0 - 0.01 < s < s1 + 0.01],
          f"{label}: no bracket stands in the tower's span ({len(north)} on the north wall)")
    return a, p, b


def bed_inside(a, p, b):
    """The K10 bed moulding's triangles on the north wall's face that reach into the tower's
    span. A straight run of it has vertices only at its ends, so a run straight through the
    tower is found by its triangles' extent, not by a vertex inside."""
    from archetypes import k10_frontage as K10
    D, W = p.depth_m, p.width_m
    s0, s1 = b["span_m"]
    lo, hi = D - s1 + 0.05, D - s0 - 0.05
    pr = a.prims[K10.ROLE_MATERIAL["timber"]]
    out = []
    for t in range(0, len(pr.idx), 3):
        tri = [pr.pos[i] for i in pr.idx[t:t + 3]]
        if all(abs(q[2] + W) < 0.25 and a.soffit_m - 0.5 < q[1] < a.soffit_m + 1e-3 for q in tri) \
                and min(q[0] for q in tri) < hi and max(q[0] for q in tri) > lo:
            out.append(tri)
    return out


def main() -> int:
    tall = storeys(3.8, 3.4, 3.6)                       # wall top 10.8 m over 1600's 8.9 m eave
    a, p, b = built("house_1600_prairie", tower(storeys=tall), "1600 (hip), round tower")
    check(not bed_inside(a, p, b), "1600 (hip): the bed moulding stops at the tower's junctions")
    check(not [o for o in p.openings if o.wall == NORTH and b["span_m"][0] < o.s_m < b["span_m"][1]],
          "1600 (hip): the north lights behind the tower are dropped")
    built("house_1600_prairie", tower("k08.tower.octagonal", storeys=tall), "1600 (hip), octagonal tower")
    built("house_1600_prairie", tower(storeys=tall, plan={"radius_m": 2.2, "centre_proud_m": 1.0}, s=9.0),
          "1600 (hip), a tower sized by its record")
    a, p, b = built("spalding_house_1637_prairie", tower(s=5.5, storeys=storeys(4.4, 4.2, 4.4)),
                    "1637 (mansard), round tower")
    check(not bed_inside(a, p, b), "1637 (mansard): the bed moulding stops at the tower's junctions")

    refused("house_1600_prairie", tower(storeys=storeys(3.6, 3.4, 2.5)),
            "a tower whose wall top (9.5 m) is not 1 m over 1600's 8.9 m eave")
    refused("house_1600_prairie", tower(storeys=tall, plan={"radius_m": 5.0, "centre_proud_m": 1.0}),
            "a tower 5 m in radius")
    refused("house_1600_prairie", tower(storeys=tall, plan={"radius_m": 1.6, "centre_proud_m": 1.5}),
            "a tower standing all but clear of its wall")
    refused("house_1600_prairie", tower(storeys=tall, plan={"chord_m": 3.0, "rise_m": 1.0}),
            "a tower sized as a bow")
    refused("house_1600_prairie", tower(storeys=tall, wall="k01.wall.street_front", s=1.8),
            "a tower in front of 1600's entrance")
    if failures:
        print(f"test_k01_tower: {len(failures)} failed")
        return 1
    print("test_k01_tower: all passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
