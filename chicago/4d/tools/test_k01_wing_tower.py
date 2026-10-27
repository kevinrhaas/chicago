#!/usr/bin/env python3
"""T-2842: a K08 tower stands on a K01 rear wing's wall, past the wing's own eave.

The kit piece 1801 Prairie's north-east turret needs (T-2789): it stands on the east
range (r2), a two-storey wing, not on the main walls T-2787's tower stands on. No record
carries one yet, so this builds committed K01 records with one added — 1604's brick rear
range under its flat deck, and 1811 as an all-stone house with its rear section hipped
in slate, as 1801's range will be — and holds the assembly to what the ticket says:

  * the tower is built on k01.wall.wing.<id>.north (and south): its wall top stands past
    the wing's wall top by TOWER_PAST_EAVE_M and its cap over the wing's roof;
  * its ring is closed above the wing's wall top, in the wing wall's plane, facing the
    wing behind it, from that wall top to the tower's own;
  * the wing's wall is open behind it — no walling, string course or sill inside its
    junctions under the wing's wall top — and the wing's lights there are dropped;
  * refused: a tower under the wing's eave, a bay on a wing's wall, an oriel there whose wall
    top is not a metre under the wing's eave (T-1890: an oriel may stand on a wing, under a
    main-wall oriel's rules), a tower on a gable end, one where a later wing stands on the
    wall, one nearer a corner than the kit's pier, and a wall no wing has.

    python3 tools/test_k01_wing_tower.py
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

SLATE = "slate_pennsylvania"
failures = []


def check(ok, what):
    print(("ok   " if ok else "FAIL ") + what)
    if not ok:
        failures.append(what)


def record(sid, tower, stone=False, roofs=None):
    """A committed record with `tower` added to its bays, its wings' roofs replaced by `roofs`."""
    st = copy.deepcopy(json.loads((ROOT / "data" / "structures" / f"{sid}.json").read_text()))
    phase = st["phases"][-1]
    if stone:   # T-2788: the all-stone house 1801 will be
        phase["form"]["construction"]["value"] = "stone"
    for w in phase["form"]["rear_wings"]["value"]:
        if w["id"] in (roofs or {}):
            w["roof"] = {"overhang_m": w["roof"]["overhang_m"], "fascia_m": w["roof"]["fascia_m"],
                         "covering": SLATE, **roofs[w["id"]]}
    bays = phase["form"].setdefault("bays", {"value": [], "confidence": "reconstructed"})
    bays["value"] = list(bays["value"]) + [tower]
    return st, phase


def tower(wall, s, variant="k08.tower.round", **extra):
    return {"id": "test_tower", "variant": variant, "wall": wall, "s_m": s, **extra}


SMALL = {"radius_m": 1.2, "centre_proud_m": 0.5}


def refused(sid, t, why, says, **kw):
    """Refused, and for the reason named: `says` is in the refusal's words."""
    st, phase = record(sid, t, **kw)
    try:
        KP.from_phase(phase, st)
    except KP.ParamError as e:
        check(says in str(e), f"{why}: refused ({str(e)[:90]}...)")
        return
    check(False, f"{why}: refused")


def built(sid, t, label, **kw):
    st, phase = record(sid, t, **kw)
    p = KP.from_phase(phase, st)
    a = K1.build(p, st["id"])
    K1.to_glb(a, st["id"], phase["id"], ["1904"], {})      # it writes
    b = next(x for x in p.bays if x["id"] == "test_tower")
    w = next(x for x in p.rear_wings if x["id"] == b["wing"])
    side = b["wall"].rsplit(".", 1)[1]
    (O, R, _length) = KP.wing_walls(w)[side]
    N = (-R[2], 0.0, R[0])   # cross(R, Y) for a level R: the wall's outward normal
    s0, s1 = b["span_m"]
    top = w["top_m"]
    wall_top = sum(x["height_m"] for x in b["variant"]["storeys"])
    check(b["eave_m"] == top and wall_top >= top + KP.TOWER_PAST_EAVE_M - 1e-9,
          f"{label}: wall top {wall_top:.2f} m stands {KP.TOWER_PAST_EAVE_M} m past the wing's {top:.2f} m")

    # the cap: copper over the wing's roof — its deck, or its slate's ridge
    roof_hi = w["roof"]["ridge_m"] if w["roof"]["kind"] != "flat" else w["deck_m"]
    cap = a.prims["bay_copper"].pos if "bay_copper" in a.prims else []
    apex = max((q[1] for q in cap), default=0.0)
    check(apex > roof_hi + 1.0, f"{label}: the cap stands over the wing's roof (apex {apex:.2f} m, roof {roof_hi:.2f} m)")

    def along(q):   # a world point's s along the wing's wall and its distance out of it
        d = [q[k] - O[k] for k in range(3)]
        return d[0] * R[0] + d[2] * R[2], d[0] * N[0] + d[2] * N[2]

    # the ring's back above the wing's wall top: in the wall's plane, facing the wing
    body = a.prims["bay_stone"]
    back = []
    for t_ in range(0, len(body.idx), 3):
        tri = [body.pos[i] for i in body.idx[t_:t_ + 3]]
        n = body.nrm[body.idx[t_]]
        if n[0] * N[0] + n[2] * N[2] < -0.99 and all(abs(along(q)[1] + 0.001) < 5e-4 for q in tri) \
                and all(top - 1e-6 <= q[1] <= wall_top + 1e-6 for q in tri):
            back.append(tri)
    area = 0.0
    for t_ in back:
        (a0, y0), (a1, y1), (a2, y2) = [(along(q)[0], q[1]) for q in t_]
        area += abs((a1 - a0) * (y2 - y0) - (a2 - a0) * (y1 - y0)) / 2
    want = (s1 - s0) * (wall_top - top)
    check(abs(area - want) < 0.02 * want,
          f"{label}: the ring is closed over the wing's wall top, facing the wing ({area:.2f} of {want:.2f} m2)")
    ss = [along(q)[0] for t_ in back for q in t_]
    check(bool(ss) and abs(min(ss) - s0) < 0.003 and abs(max(ss) - s1) < 0.003,
          f"{label}: ...across the ring's junctions at s {s0:.3f}..{s1:.3f}")

    # the wing's wall open behind it: nothing of the wing in the junctions under its eave (the
    # eave is not cut for the tower and runs into its ring, as the main eave does, T-2787)
    drop = 0.0 if w["roof"]["kind"] == "flat" else \
        w["overhang_m"] * math.tan(math.radians(w["roof"]["pitch_deg"])) + w["fascia_m"]
    eave_foot = top - drop - 0.05     # a deck stands on the wall top; a slope's eave hangs under it
    inside = []
    for name, pr in a.prims.items():
        if name.startswith("bay_"):
            continue
        for t_ in range(0, len(pr.idx), 3):
            tri = [pr.pos[i] for i in pr.idx[t_:t_ + 3]]
            c = [sum(q[k] for q in tri) / 3 for k in range(3)]
            s_, d_ = along(c)
            if s0 + 0.05 < s_ < s1 - 0.05 and -0.05 < d_ < 0.3 and 0.3 < c[1] < eave_foot:
                inside.append(name)
    check(not inside, f"{label}: the wing's wall is open behind the tower "
                      f"({len(inside)} triangle(s) inside it: {sorted(set(inside))[:4]})")
    left = [o for o in w["openings"] if o.wall == b["wall"] and s0 - 0.12 < o.s_m < s1 + 0.12]
    check(not left, f"{label}: the wing's lights behind it are dropped ({len(left)} left)")
    return p, b, w


def pavilion_on_wing():
    """T-3001: a full-height projection on a wing's wall (1801's gabled section on 18th Street:
    a shallow pavilion under a coped gable, with a balcony, on r3's south wall), and the wing's
    front closed where the wing stands taller than its host under a ridge along it."""
    st = json.loads((ROOT / "data" / "structures" / "kimball_house_1801_prairie.json").read_text())
    p = KP.from_phase(st["phases"][-1], st)
    b = next(x for x in p.bays if x["id"] == "p_gable")
    w = next(x for x in p.rear_wings if x["id"] == "r3")
    check(b.get("wing") == "r3" and b["eave_m"] == w["top_m"] and b["variant"]["kind"] == "projection",
          "1801: p_gable is a projection on r3's wall, read against r3's wall top")
    check(not [o for o in w["openings"] if o.wall == b["wall"]], "1801: r3's lights behind p_gable are dropped")
    check(w["roof"]["axis"] == "v" and w["top_m"] > p.eave_m, "1801: r3 is hipped along v and stands past the cornice")
    a = K1.build(p, st["id"])
    # r3's front, in the host plane u = 0 over v 0..6, from the host's top to r3's wall top
    u1, v0, v1 = w["rect"][1], w["rect"][2], w["rect"][3]
    area = 0.0
    for name, pr in a.prims.items():
        for t_ in range(0, len(pr.idx), 3):
            tri = [pr.pos[i] for i in pr.idx[t_:t_ + 3]]
            if all(abs(q[0] - u1) < 0.01 and -v1 - 0.01 < q[2] < -v0 + 0.01 and q[1] > p.eave_m - 0.01 for q in tri):
                e1 = [tri[1][k] - tri[0][k] for k in range(3)]
                e2 = [tri[2][k] - tri[0][k] for k in range(3)]
                c = [e1[1] * e2[2] - e1[2] * e2[1], e1[2] * e2[0] - e1[0] * e2[2], e1[0] * e2[1] - e1[1] * e2[0]]
                if c[0] > 0:   # facing out of the wing, toward the host's side
                    area += math.hypot(*c) / 2
    want = (v1 - v0) * (w["top_m"] - p.eave_m)
    check(area > 0.9 * want, f"1801: r3's front is closed over the host's {p.eave_m} m top ({area:.2f} of {want:.2f} m2)")
    refused("kimball_house_1801_prairie", {**next(x for x in st["phases"][-1]["form"]["bays"]["value"]
                                                  if x["id"] == "p_gable"), "id": "test_bow",
                                           "variant": "k08.bay.bowed", "plan": {"kind": "bow", "chord_m": 2.0, "rise_m": 0.5}},
            "a bow on a wing's wall", "carries a K08 tower")


def main() -> int:
    north = "k01.wall.wing.rear_range.north"
    p, b, w = built("house_1604_prairie", tower(north, 6.0, plan=SMALL), "1604 rear range (flat deck), round tower, north")
    raw = json.loads((ROOT / "data" / "structures" / "house_1604_prairie.json").read_text())
    ops0 = KP.from_phase(raw["phases"][-1], raw)
    w0 = next(x for x in ops0.rear_wings if x["id"] == "rear_range")
    check(len(w0["openings"]) - len(w["openings"]) == 2,
          f"1604: the two north lights at s 6.0 are dropped ({len(w0['openings'])} -> {len(w['openings'])})")
    check(not [x for x in p.bays if x.get("wing") and x["id"] != "test_tower"] and len(p.openings) == len(ops0.openings),
          "1604: the main walls keep every light")
    built("house_1604_prairie", tower("k01.wall.wing.rear_range.south", 5.4, plan=SMALL),
          "1604 rear range, round tower, south (its string course stopped)")
    built("house_1604_prairie", tower(north, 6.0, variant="k08.tower.octagonal", plan=SMALL),
          "1604 rear range, octagonal tower, north")
    built("coleman_ames_house_1811_prairie", tower("k01.wall.wing.rear_section.north", 2.15, plan=SMALL),
          "1811 rear section (stone, slated hip), round tower", stone=True,
          roofs={"rear_section": {"kind": "hip", "pitch_deg": 45}})

    def storeys(*heights):
        win = {"opening": "k06.opening.sash_2over2_flat", "clear_width_m": 0.8, "clear_height_m": 1.6,
               "sill_m": 0.8, "at_deg": [-50, 0, 50]}
        return [{"height_m": h, "windows": [win]} for h in heights]
    refused("house_1604_prairie", tower(north, 6.0, plan=SMALL, storeys=storeys(3.6, 3.4, 2.0)),
            "a tower whose wall top (9.0 m) is not 1 m past the wing's 8.8 m", "not 1.0 m over the eave (8.80 m)")
    refused("house_1604_prairie", tower(north, 4.2, variant="k08.bay.canted"), "a canted bay on a wing's wall", "carries a K08 tower")
    refused("house_1604_prairie", {**tower(north, 4.2, variant="k08.oriel.canted_corbelled"), "base_m": 5.3},
            "an oriel on a wing's wall whose wall top is not a metre under its eave", "a metre under the eave")
    refused("house_1604_prairie", tower(north, 6.0, plan=SMALL), "a tower on a gable end", "a gable end",
            roofs={"rear_range": {"kind": "gable", "pitch_deg": 50, "gable_to": "north"}})
    refused("house_1604_prairie", tower("k01.wall.wing.rear_range.rear", 2.0, plan=SMALL),
            "a tower where the west block stands on the range's rear", "where west_block stands on it")
    refused("house_1604_prairie", tower(north, 1.0, plan=SMALL), "a tower nearer the wing's corner than the pier",
            "closer than 0.3 m to a corner")
    refused("house_1604_prairie", tower("k01.wall.wing.east_range.north", 3.0, plan=SMALL), "a wall no wing has", "not a wall of one of")
    pavilion_on_wing()
    if failures:
        print(f"test_k01_wing_tower: {len(failures)} failed")
        return 1
    print("test_k01_wing_tower: all passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
