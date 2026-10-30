#!/usr/bin/env python3
"""T-2841: a K01 rear wing takes a hipped or gabled roof in K04's slate.

The kit piece 1801 Prairie's move onto K01 needs (T-2789): its gabled section (r3, a
three-storey wall top at about 13.9 m standing over the main block's 8.1 m cornice) and
its east range (r2) are roofed, where a K01 wing was decked flat in tin. No record roofs a
wing so yet, so this builds committed K01 records with their wings' roofs changed — 1604's
two brick wings (the second standing on the first's rear) and 1811's rear range, raised
past its main eave, on an all-stone house as 1801 will be — and holds the assembly to what
the ticket says:

  * slated: the covering is K04 slate, its eave at the overhang's run down the slope and
    its ridge at the pitch over the half-span;
  * the ridge: a gable to the rear and a hip on a wing deeper than it is wide run the ridge
    across the wing into the host wall at its full height; a gable to a flank and a hip on
    a wide wing run it along the wing, the front slope down to the host at the wall top;
  * the gable: its end is the wing's walling from the wall top to the roof, laid where
    the gable faces and nowhere else;
  * the junction closed: above the host's own top, where nothing stands behind it, the
    roof's section in the host wall's plane is walling across the wing and the eave's
    timber past its corners, with the area the section has — and where the wing stands
    over its host, the wing's front wall from the host's top to its own;
  * the host wall: drawn down to the wing's wall top over the junction and not below, so
    the closure and the host wall never share a plane's height; the host's lights under
    the roof's highest point on it are behind the wing;
  * refused: a slate cut for less headlap than the pitch needs, a pitch out of range, a
    hip in tin, a gable facing no side or a hip facing one, two slates on one house;
  * as-was: every committed record still decks its wings flat and lays no wing slate, but
    the records a ticket roofs from a picture (1801's gabled section and east range, T-2843).

    python3 tools/test_k01_wing_roof.py
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

failures = []
SLATE = "slate_pennsylvania"


def check(ok, what):
    print(("ok   " if ok else "FAIL ") + what)
    if not ok:
        failures.append(what)


def roofed(sid, roofs, stone=False, storeys=None):
    """A committed record, its wings' roofs replaced by `roofs` {wing id: roof fields}."""
    st = json.loads((ROOT / "data" / "structures" / f"{sid}.json").read_text())
    phase = copy.deepcopy(st["phases"][-1])
    if stone:   # T-2788: the all-stone house 1801 will be
        phase["form"]["construction"]["value"] = "stone"
    for w in phase["form"]["rear_wings"]["value"]:
        if w["id"] in roofs:
            w["roof"] = {"overhang_m": w["roof"]["overhang_m"], "fascia_m": w["roof"]["fascia_m"],
                         "covering": SLATE, **roofs[w["id"]]}
        if storeys and w["id"] in storeys:
            w["storey_heights_m"] = storeys[w["id"]]
    return st, phase


def tri_area(t):
    u = [t[1][k] - t[0][k] for k in range(3)]
    v = [t[2][k] - t[0][k] for k in range(3)]
    c = (u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0])
    return math.sqrt(sum(x * x for x in c)) / 2


def faces(a, mat, plane=None, facing=None):
    """Triangles of one slot, optionally in a plane (axis, value) and facing (axis, sign)."""
    pr = a.prims.get(mat)
    out = []
    if pr is None:
        return out
    for i in range(0, len(pr.idx), 3):
        tri = [pr.pos[pr.idx[i + j]] for j in range(3)]
        n = pr.nrm[pr.idx[i]]
        if plane and not all(abs(q[plane[0]] - plane[1]) < 1e-4 for q in tri):
            continue
        if facing and n[facing[0]] * facing[1] < 0.99:
            continue
        out.append(tri)
    return out


def within(tris, k, lo, hi):
    return [t for t in tris if all(lo - 1e-4 <= q[k] <= hi + 1e-4 for q in t)]


def built(sid, roofs, label, stone=False, storeys=None):
    st, phase = roofed(sid, roofs, stone, storeys)
    p = KP.from_phase(phase, st)
    a = K1.build(p, st["id"])
    K1.to_glb(a, st["id"], phase["id"], ["1904"], {})      # it writes
    return a, p


def section(top, ridge, half, t, floor, axis_u, z_len):
    """The area of a roof's section in the host wall's plane above `floor`, across the
    wing's wall line: a triangle over the wall top where the ridge runs into the wall, a
    band to the wall top where a slope comes down to it."""
    if not axis_u:
        return z_len * max(0.0, top - floor)
    band = z_len * max(0.0, top - floor)
    peak = ridge - max(top, floor)          # the triangle (or its tip) over the band
    if peak <= 0:
        return band
    w = 2 * peak / t                        # its base at max(top, floor)
    return band + w * peak / 2


def wing_checks(a, p, wid, label, walling):
    w = next(x for x in p.rear_wings if x["id"] == wid)
    r = w["roof"]
    u0, u1, v0, v1 = w["rect"]
    z0, z1 = -v1, -v0
    top, o, ridge = w["top_m"], w["overhang_m"], r["ridge_m"]
    t = math.tan(math.radians(r["pitch_deg"]))
    host = next((x for x in p.rear_wings if w["host_wall"] == f"k01.wall.wing.{x['id']}.rear"), None)
    host_top = p.eave_m if host is None else host["top_m"]
    params = a.components[f"k01.roof.wing.{wid}"]["instances"][0]["params"]
    check(params["kind"] == r["kind"] and params["covering"] == SLATE and params["construction"] == "k05",
          f"{label}: the roof is registered a {r['kind']} in {SLATE} ({params['kind']}, {params['covering']})")
    check(a.fabric["wing_slate"] == SLATE, f"{label}: the wing slate is K04's {SLATE}")

    # the covering over this wing's plan
    cov = [q for tri in within(within(faces(a, "wing_slate"), 0, u0 - o - 0.01, u1 + 0.01), 2, z0 - o - 0.01, z1 + o + 0.01)
           for q in tri]
    hi_ = max(q[1] for q in cov)
    lo = min(q[1] for q in cov)
    check(abs(hi_ - ridge) < 0.01, f"{label}: the slate's ridge stands at {hi_:.3f} m (pitch over half-span: {ridge:.3f})")
    check(abs(lo - (top - o * t)) < 0.01, f"{label}: its eave at {lo:.3f} m, the overhang's run down the slope")
    at_host = [q for q in cov if abs(q[0] - u1) < 1e-4]
    reach = max((q[1] for q in at_host), default=-1)
    if r["axis"] == "u":
        check(abs(reach - ridge) < 0.01, f"{label}: the ridge runs across the wing into the host wall at "
                                          f"{reach:.3f} m, its full height")
    else:
        check(abs(reach - top) < 0.01, f"{label}: the ridge runs along the wing; its front slope meets the host "
                                        f"wall at {reach:.3f} m, the wall top")
    # the junction: the cut drawn above the host's top, across the wing in its walling
    closure = within(faces(a, walling, (0, u1), (0, 1)), 2, z0, z1)
    got = sum(tri_area(x) for x in closure)
    want = section(top, ridge, (v1 - v0) / 2, t, host_top, r["axis"] == "u", v1 - v0)
    check(abs(got - want) < 0.01 + 0.01 * want,
          f"{label}: the junction over the host's top ({host_top:.2f} m) is closed in {walling}: "
          f"{got:.3f} of {want:.3f} m2")
    check(not closure or min(q[1] for tri in closure for q in tri) >= host_top - 1e-4,
          f"{label}: ...and nothing of it is drawn below the host's top")
    eave_ends = [x for x in faces(a, "fascia", (0, u1), (0, 1))
                 if all(q[2] <= z0 + 1e-4 or q[2] >= z1 - 1e-4 for q in x)
                 and all(z0 - o - 1e-4 <= q[2] <= z1 + o + 1e-4 for q in x)]
    if host_top < top - o * t - w["fascia_m"]:
        check(bool(eave_ends), f"{label}: the eaves' ends past its corners are closed in the eave's timber "
                               f"({len(eave_ends)} faces)")
    return w, host_top


def host_wall(a, p, w, host_top, walling):
    """The host wall over the junction: drawn from the wing's wall top, never below it."""
    u0, u1, v0, v1 = w["rect"]
    z0, z1 = -v1, -v0
    behind = within(faces(a, walling, (0, u1), (0, -1)), 2, z0, z1)
    if host_top > w["top_m"] + 0.05:
        return bool(behind) and min(q[1] for t in behind for q in t) >= w["top_m"] - 1e-4
    return not [t for t in behind if min(q[1] for q in t) < host_top - 1e-4]


def gable_end(a, w, walling):
    """The gable's walling: the rear wall's plane (axis u) or both flanks' (axis v), from the
    wall top to the verge's soffit, which runs the fascia's depth under the slate: a triangle
    (half - f / t) wide each side of the ridge and (half - f / t) t high."""
    r = w["roof"]
    u0, u1, v0, v1 = w["rect"]
    t = math.tan(math.radians(r["pitch_deg"]))
    if r["axis"] == "u":
        planes = [((0, u0), (0, -1), 2, -v1, -v0)]
        half = (v1 - v0) / 2
    else:
        planes = [((2, -v1), (2, -1), 0, u0, u1), ((2, -v0), (2, 1), 0, u0, u1)]
        half = (u1 - u0) / 2
    out = []
    for plane, facing, k, lo, hi in planes:
        tris = [x for x in within(faces(a, walling, plane, facing), k, lo, hi)
                if min(q[1] for q in x) >= w["top_m"] - 1e-4]
        out.append(sum(tri_area(x) for x in tris))
    return out, (half - w["fascia_m"] / t) ** 2 * t


def main() -> int:
    # 1604: the rear range (8.33 deep by 8.2 wide, under the 12.1 m main eave) hipped, so its
    # ridge (12.9 m) runs across it into the main rear wall and stands 0.8 m over the eave;
    # the west block on its rear gabled to the rear
    a, p = built("house_1604_prairie", {"rear_range": {"kind": "hip", "pitch_deg": 45},
                                        "west_block": {"kind": "gable", "pitch_deg": 45, "gable_to": "rear"}},
                 "1604")
    w, ht = wing_checks(a, p, "rear_range", "1604 rear range (hip, ridge across)", "brick")
    check(host_wall(a, p, w, ht, "brick"), "1604 rear range: the main rear wall is drawn over it from its wall top")
    w2, ht2 = wing_checks(a, p, "west_block", "1604 west block (gable to the rear, on the range's rear)", "brick")
    check(ht2 == w["top_m"], f"1604 west block: its host's top is the range's wall top ({ht2})")
    got, want = gable_end(a, w2, "brick")
    check(abs(got[0] - want) < 0.01 * want + 0.01, f"1604 west block: the gable's walling over the wall top "
                                                     f"({got[0]:.3f} of {want:.3f} m2)")
    hip_end, _ = gable_end(a, dict(w, roof=dict(w["roof"], axis="u")), "brick")
    check(hip_end[0] < 1e-6, f"1604 rear range: a hip lays no gable on its rear wall ({hip_end[0]:.3f} m2)")
    check(not [o for o in p.openings if o.wall == "k01.wall.rear_service"
               and w["host_span_m"][0] < o.s_m < w["host_span_m"][1] and o.sill_m < w["roof"]["ridge_m"] - 0.15],
          "1604: no main rear light stands under the range's ridge behind it")

    # 1604 again: the range gabled to the north (the ridge along it, a gable on each flank)
    a, p = built("house_1604_prairie", {"rear_range": {"kind": "gable", "pitch_deg": 50, "gable_to": "north"}},
                 "1604 north")
    w, ht = wing_checks(a, p, "rear_range", "1604 rear range (gable to the north, ridge along)", "brick")
    got, want = gable_end(a, w, "brick")
    check(all(abs(g - want) < 0.01 * want + 0.01 for g in got),
          f"1604 rear range: a gable on each flank ({', '.join(f'{g:.3f}' for g in got)} of {want:.3f} m2)")
    check(host_wall(a, p, w, ht, "brick"), "1604 rear range: the main rear wall is drawn over it from its wall top")

    # 1811 as an all-stone house, its rear range raised to a three-storey 13.9 m wall top over
    # the 11.7 m main eave, as 1801's gabled section stands over its main cornice
    a, p = built("coleman_ames_house_1811_prairie",
                 {"rear_range": {"kind": "gable", "pitch_deg": 45, "gable_to": "rear"}}, "1811",
                 stone=True, storeys={"rear_range": [4.6, 4.6, 3.25]})
    w, ht = wing_checks(a, p, "rear_range", "1811 rear range (stone, over the main eave, gable to the rear)",
                        "rough_stone_trim")
    check(w["top_m"] > ht + 2.0, f"1811: the range's wall top {w['top_m']} m stands over the main eave {ht} m")
    got, want = gable_end(a, w, "rough_stone_trim")
    check(abs(got[0] - want) < 0.01 * want + 0.01, f"1811 rear range: its gable is stone ({got[0]:.3f} of {want:.3f} m2)")
    a, p = built("coleman_ames_house_1811_prairie",
                 {"rear_range": {"kind": "hip", "pitch_deg": 45}}, "1811 hip",
                 stone=True, storeys={"rear_range": [4.6, 4.6, 3.25]})
    wing_checks(a, p, "rear_range", "1811 rear range (stone, over the main eave, hip along a deep wing)",
                "rough_stone_trim")

    # refused
    def refused(roofs, why, sid="house_1604_prairie"):
        st, phase = roofed(sid, roofs)
        try:
            KP.from_phase(phase, st)
        except KP.ParamError as e:
            check(True, f"{why}: refused ({str(e)[:90]}...)")
            return
        check(False, f"{why}: refused")
    refused({"rear_range": {"kind": "hip", "pitch_deg": 40}}, "a 40 deg slate on a slate cut for 45")
    refused({"rear_range": {"kind": "hip", "pitch_deg": 65}}, "a 65 deg wing roof")
    refused({"rear_range": {"kind": "hip", "pitch_deg": 45, "covering": "painted_tin_sheet"}}, "a hip in tin")
    refused({"rear_range": {"kind": "gable", "pitch_deg": 45, "gable_to": "east"}}, "a gable facing the host")
    refused({"rear_range": {"kind": "gable", "pitch_deg": 45}}, "a gable facing no side")
    refused({"rear_range": {"kind": "hip", "pitch_deg": 45, "gable_to": "rear"}}, "a hip with a gable")
    refused({"rear_range": {"kind": "mansard", "pitch_deg": 45}}, "a mansard wing")
    refused({"rear_range": {"kind": "hip", "pitch_deg": 45},
             "west_block": {"kind": "hip", "pitch_deg": 45, "covering": "slate_vermont"}}, "two slates on one house")

    # as-was: every committed K01 wing is still decked flat in tin, no wing slate laid, but
    # those a building's own ticket roofs from its picture (T-2843: 1801's, the Taylor photograph;
    # T-3001: and r3b, the part of the sheet's rectangle the print shows at the east range's height)
    import k01_emit
    pictured = {"kimball_house_1801_prairie": {"r3", "r3b", "r2"}}
    n = 0
    for st, phase, _ in k01_emit.records():
        for w in (phase["form"].get("rear_wings") or {}).get("value", ()):
            if w["id"] in pictured.get(st["id"], ()):
                continue
            n += 1
            if w["roof"]["kind"] != "flat":
                check(False, f"as-was: {st['id']}'s {w['id']} is roofed {w['roof']['kind']}")
    check(n > 0, f"as-was: the {n} committed K01 wings are decked flat")
    if failures:
        print(f"test_k01_wing_roof: {len(failures)} failed")
        return 1
    print("test_k01_wing_roof: all passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
