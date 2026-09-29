#!/usr/bin/env python3
"""What Wright's 1834 sheet says about the 288.3 m the corporate boundary extrapolates.

T-1544. The Trustees' walk of 7 November 1833 runs its west leg *"north along said last
mentioned street and its continuation to Ohio street"*, and this repository resolves that
leg on two committed readings of Jefferson Street (T-1490). Both of them stop: the West
Division's reading ends at local north +381.887, on the surviving Hubbard Street
intersection, and **modern Jefferson does not survive north of Hubbard**, so there is no
third node to carry it on. The last 288.3 m to Ohio Street is arithmetic and nothing else,
and the leg's own note says so.

A node is not the only kind of control. The ordinance's "continuation" crosses ground this
project has already READ — Wabansia, surveyed 1831 and drawn whole on J. S. Wright's 1834
survey, whose street corridors (T-0790), block columns (T-1074) and river-front wedge
(T-1077) are committed traces, seated on the committed `kinzie` line by T-1070/T-1086. So
the question this command asks is the one the ticket asks: **does the sheet draw the
continuation?**

## The answer is no, and the refusal is the finding

- **Wright draws no north-south street on Jefferson's line.** Over the four tiers the leg
  crosses, the nearest drawn corridor is the one between Wabansia's middle and east block
  columns, about 81 m west of the extrapolation — five times the 16.02 m RMS this sheet's
  own registration admits. No re-seating of this sheet inside its own error can put a
  street where the leg runs.
- **The leg runs down the middle of Wabansia's easternmost block column**, from Hubbard to
  Ohio, crossing Owen Street and Hight Street and ending on platted ground of an addition
  the ordinance never names.
- **The one drawn line that could be mistaken for the continuation is the tract's east
  boundary against the North Branch**, and this reading refuses that identification on
  BEARING rather than on offset: the two stand 16.0 m apart at Hubbard and 23.1 m apart at
  Ohio. A true identification would close over 288 m; these diverge.

So the leg stays `inferred` and stays an extrapolation. What changes is that it is now
extrapolated across ground that has been looked at: the sheet bounds it instead of saying
nothing about it, and this command is the gate that keeps the bound honest.

    tools/measure_jefferson_continuation.py               the reading
    tools/measure_jefferson_continuation.py --write       write the trace
    tools/measure_jefferson_continuation.py --check       re-derive every metre committed
    tools/measure_jefferson_continuation.py --gate        exit 1 if the refusal stops holding
    tools/measure_jefferson_continuation.py --check-sheet re-measure the rules off the raster
    tools/measure_jefferson_continuation.py --self-test   the assertions, fired

The gate never fails because the leg is an extrapolation — that is a fact about 1833 and
about what survives. It fails when the refusal above stops being true: when a drawn
corridor comes within the sheet's own RMS of the leg, when the leg stops standing on
Wabansia's platted ground, when the tract boundary starts converging on it, or when the
extension grows close enough to a drawn building to decide its side of the line.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUT = DATA / "traces" / "jefferson_continuation.json"
SEATING = DATA / "traces" / "wabansia_seating.json"
NUMBERING = DATA / "traces" / "wabansia_block_numbering.json"
STREETS = DATA / "traces" / "wabansia_streets.json"
GCP = DATA / "traces" / "gcp" / "wright_1834_nara_hup_gcps.json"

sys.path.insert(0, str(ROOT / "tools"))
import measure_corporation_limits as limits  # noqa: E402

#: The label the ring's own reach table gives this leg. Matched rather than re-derived, so
#: a leg renamed or removed upstream fails here loudly instead of measuring some other one.
LEG = "west — Jefferson, north to Ohio"

#: The Wabansia tiers the leg crosses, north to south. Named rather than searched for the
#: same reason: the tiers are Wright's own corridors and their ids are the trace's.
TIERS = ("t4", "t5", "t6", "t7")

#: The block column the leg runs in — Wabansia's easternmost, against the water lots.
COLUMN = "C"


def load(path: Path):
    return json.loads(path.read_text())


# ----------------------------------------------------------------- the sheet's own scale


def sheet_scale_m_per_px(numbering: dict) -> float:
    """Metres per pixel, taken from the sheet reading's own paired px and m figures.

    Never from the registration's scale field: what is wanted here is the number the
    Wabansia reading itself used to turn its rules into metres, so that a width quoted
    below is the same width that trace quotes."""
    ratios = [c["width_m"] / c["width_px"] for c in numbering["columns"]]
    ratios += [s["corridor_m"] / s["corridor_px"] for s in numbering["north_south_streets"]]
    return sum(ratios) / len(ratios)


# ------------------------------------------------------------------- the seated boundary


def east_boundary(seating: dict):
    """The seated east side of Wabansia's block grid, south to north.

    The polygon is committed as one ring; its east side is the run of vertices standing
    within a lot's width of the tract's east rule. Taken by position rather than by index,
    so a polygon re-wound or re-seated does not silently return some other side."""
    poly = seating["block_grid_polygon_local_enu_m"]
    east = [tuple(v) for v in poly if -400.0 <= v[0] <= -388.0]
    return sorted(east, key=lambda v: v[1])


def at_northing(chain, north: float):
    """The easting of a south-to-north chain at a given northing, by interpolation."""
    for (ax, ay), (bx, by) in zip(chain, chain[1:]):
        if ay <= north <= by:
            return ax + (north - ay) * (bx - ax) / (by - ay)
    return None


# -------------------------------------------------------------------------- the geometry


def leg_segment():
    """The extrapolated stretch, straight off the ring's own reach table."""
    _, reach = limits.limits_ring()
    for label, a, b in reach:
        if label == LEG:
            return a, b
    raise SystemExit(f"the ring no longer carries a leg called {LEG!r}; the reach table "
                     "has been renamed or this leg has stopped being extrapolated")


def crossed_streets(a, b):
    """The committed streets the leg crosses, with the crossing point on each."""
    (ax, ay), (bx, by) = a, b
    out = []
    for s in load(DATA / "streets" / "1835.json")["streets"]:
        path = s["path_local_enu_m"]
        for (px, py), (qx, qy) in zip(path, path[1:]):
            d1 = (bx - ax) * (py - ay) - (by - ay) * (px - ax)
            d2 = (bx - ax) * (qy - ay) - (by - ay) * (qx - ax)
            e1 = (qx - px) * (ay - py) - (qy - py) * (ax - px)
            e2 = (qx - px) * (by - py) - (qy - py) * (bx - px)
            if d1 * d2 < 0 and e1 * e2 < 0:
                t = e1 / (e1 - e2)
                out.append({"street": s["id"],
                            "at_local_enu_m": [round(ax + t * (bx - ax), 3),
                                               round(ay + t * (by - ay), 3)]})
                break
    return sorted(out, key=lambda r: r["at_local_enu_m"][1])


def read():
    a, b = leg_segment()
    seating, numbering = load(SEATING), load(NUMBERING)
    scale = sheet_scale_m_per_px(numbering)
    east = east_boundary(seating)

    # The one drawn line the leg could be confused with: the tract's east rule.
    boundary = []
    for label, p in (("south end, on Hubbard's line", a), ("north end, on Ohio's line", b)):
        e = at_northing(east, p[1])
        boundary.append({"where": label,
                         "leg_local_enu_m": [round(p[0], 3), round(p[1], 3)],
                         "tract_east_boundary_e_m": round(e, 3),
                         "leg_west_of_boundary_m": round(e - p[0], 3)})
    divergence = boundary[1]["leg_west_of_boundary_m"] - boundary[0]["leg_west_of_boundary_m"]
    length = math.hypot(b[0] - a[0], b[1] - a[1])

    # The nearest drawn north-south STREET, measured the way the sheet measures: column C's
    # width and the corridor west of it, carried west from the seated tract boundary.
    cols = [c for c in numbering["columns"] if c["column"] == COLUMN and c["tier"] in TIERS]
    corridors = [s for s in numbering["north_south_streets"]
                 if s["between"] == "B|C" and s["tier"] in TIERS]
    column_w = sum(c["width_px"] for c in cols) / len(cols) * scale
    corridor_w = sum(s["corridor_m"] for s in corridors) / len(corridors)
    corridor_centre_west_of_boundary = column_w + corridor_w / 2.0
    nearest_corridor = []
    for row in boundary:
        centre = row["tract_east_boundary_e_m"] - corridor_centre_west_of_boundary
        nearest_corridor.append({
            "where": row["where"],
            "corridor_centre_e_m": round(centre, 3),
            "leg_east_of_corridor_centre_m": round(row["leg_local_enu_m"][0] - centre, 3),
            "leg_east_of_corridor_east_rule_m": round(
                row["leg_local_enu_m"][0] - centre - corridor_w / 2.0, 3)}) 

    # Does the leg stand on Wabansia's platted ground the whole way?
    poly = seating["block_grid_polygon_local_enu_m"]
    stations = [(a[0] + (b[0] - a[0]) * i / 24.0, a[1] + (b[1] - a[1]) * i / 24.0)
                for i in range(25)]
    off = [i for i, p in enumerate(stations) if not limits.inside(p, poly)]
    # How much platted ground is left north of the corner before the grid's east side
    # ends and the North Branch takes over. The claim "it ends on platted ground" is
    # worth exactly this margin and no more.
    margin = east[-1][1] - b[1]

    # And does it decide a building?
    datum = load(DATA / "datum.json")
    nearest = None
    for sid, polygon in limits.footprints(datum):
        hit = limits.beside((a, b), polygon)
        if hit and (nearest is None or hit[0] < nearest[0]):
            nearest = (hit[0], hit[1], sid)

    return {
        "leg": LEG,
        "length_m": round(length, 2),
        "sheet": {"source_id": load(GCP)["raster"]["source_id"],
                  "registration_rms_m": load(GCP)["fit"]["rms_m"],
                  "m_per_px": round(scale, 5),
                  "readings": ["data/traces/wabansia_streets.json",
                               "data/traces/wabansia_block_numbering.json",
                               "data/traces/wabansia_seating.json"]},
        "the_ground_it_crosses": {
            "tract": "Wabansia, surveyed 1831, drawn whole on Wright's 1834 survey",
            "column": f"the easternmost block column ({COLUMN}) of tiers "
                      + ", ".join(TIERS),
            "column_width_m": round(column_w, 2),
            "stations_off_the_platted_grid": off,
            "corner_south_of_the_grid_east_side_end_m": round(margin, 2),
            "streets_crossed": crossed_streets(a, b)},
        "no_corridor_is_drawn_here": {
            "nearest_drawn_north_south_corridor": "the street between Wabansia's middle "
                                                  "and east block columns",
            "corridor_width_m": round(corridor_w, 2),
            "measured": nearest_corridor,
            "reading": "Wright draws no north-south street on the leg's line. The nearest "
                       "one is about "
                       f"{abs(nearest_corridor[0]['leg_east_of_corridor_east_rule_m']):.0f}"
                       " m west of it, which is more than five times the "
                       f"{load(GCP)['fit']['rms_m']} m RMS this sheet's registration "
                       "admits, so no re-seating inside the sheet's own error puts a "
                       "corridor where the leg runs."},
        "the_tract_boundary_is_not_the_continuation": {
            "candidate": "the east rule of Wabansia's block grid — the west line of the "
                         "water-lot wedge on the North Branch",
            "measured": boundary,
            "divergence_over_the_leg_m": round(divergence, 3),
            "bearing_difference_deg": round(math.degrees(math.atan2(divergence, length)), 3),
            "refused": "The two are 16 m apart at Hubbard and 23 m apart at Ohio. An "
                       "identification would CLOSE over 288 m; these diverge, so the "
                       "refusal rests on bearing and not on an offset that could be "
                       "argued away inside the registration's RMS."},
        "it_decides_no_building": {
            "nearest_structure": nearest[2] if nearest else None,
            "clearance_m": round(nearest[0], 2) if nearest else None,
            "along_the_leg_m": round(nearest[1], 2) if nearest else None,
            "drift_at_that_point_m": round(limits.drift_m(nearest[1]), 2) if nearest else None},
        "what_would_change_this": "A north-south rule read on Jefferson's line on some "
                                  "other sheet, or a surviving intersection north of "
                                  "Hubbard. Neither exists in this corpus: modern "
                                  "Jefferson does not survive north of Hubbard Street, "
                                  "and Wright is the only surveyor in this corpus who "
                                  "draws this ground at all.",
    }


# ------------------------------------------------------------------------------ the gate


def problems(r: dict) -> list[str]:
    found = []
    if r["the_ground_it_crosses"]["stations_off_the_platted_grid"]:
        found.append("the leg no longer stands on Wabansia's platted ground the whole "
                     "way: stations "
                     f"{r['the_ground_it_crosses']['stations_off_the_platted_grid']} of 24 "
                     "fall outside the seated block grid, so the record's account of what "
                     "it crosses has stopped being true")
    rms = r["sheet"]["registration_rms_m"]
    for row in r["no_corridor_is_drawn_here"]["measured"]:
        if abs(row["leg_east_of_corridor_east_rule_m"]) <= rms:
            found.append(f"a drawn north-south corridor now stands "
                         f"{row['leg_east_of_corridor_east_rule_m']:.1f} m from the leg at "
                         f"{row['where']}, inside the sheet's own {rms} m RMS — the "
                         "refusal above rests on that corridor being far outside it")
    margin = r["the_ground_it_crosses"]["corner_south_of_the_grid_east_side_end_m"]
    if margin <= 0.0:
        found.append(f"the corner at Ohio now stands {abs(margin):.1f} m NORTH of where "
                     "Wabansia's block grid ends on its east side, so it no longer lands "
                     "on the platted ground this record says it lands on")
    if r["the_tract_boundary_is_not_the_continuation"]["divergence_over_the_leg_m"] <= 0.0:
        found.append("the tract's east boundary now CONVERGES on the leg; the refusal of "
                     "the identification rests on the two diverging and must be re-argued")
    decides = r["it_decides_no_building"]
    if decides["clearance_m"] is not None and decides["clearance_m"] <= decides["drift_at_that_point_m"]:
        found.append(f"{decides['nearest_structure']} stands {decides['clearance_m']} m "
                     f"from the extension against {decides['drift_at_that_point_m']} m of "
                     "drift, so the extrapolation and not the ordinance decides its side")
    return found


def committed_matches(r: dict) -> list[str]:
    if not OUT.exists():
        return [f"{OUT.relative_to(ROOT)} is not committed"]
    was, now = load(OUT), r
    out = []
    for key in sorted(k for k in now if not k.startswith("_")):
        if json.dumps(was.get(key), sort_keys=True) != json.dumps(now[key], sort_keys=True):
            out.append(f"{key} no longer re-derives from the committed geometry")
    return out


def check_sheet() -> int:
    """Re-measure column C's two rules off the raster, in the tiers the leg crosses.

    THE EAST RULE IS READ IN THE SOUTHERN HALF OF EACH TIER and the west rule over the
    whole of it, because the North Branch cuts the grid's north-east corner: in t4 —
    the tier Ohio Street's northing falls in — column C's east rule runs out before the
    tier does, which is the same fact that stops the committed `sailors` line at local
    east -511 while `hight` below it reaches -393. Profiling the whole tier for that
    rule reads a band that is half river, and finds nothing."""
    sys.path.insert(0, str(ROOT / "tools"))
    import importlib
    k = importlib.import_module("read_kinzie_addition_streets")
    _, img = k._sheet()
    numbering, tiers = load(NUMBERING), {t["id"]: t for t in load(NUMBERING)["tiers"]}
    bad = 0
    for tier in TIERS:
        y0, y1 = tiers[tier]["y_px"]
        col = [c for c in numbering["columns"]
               if c["column"] == COLUMN and c["tier"] == tier][0]
        for name, want in (("west", col["west_px"]), ("east", col["east_px"])):
            hit = None
            for b1 in range(int(y1) - 2, int(y0) + 30, -12):
                prof = k._profile(img, 640, b1 - 30, 1300, b1, "v", 0.0)
                rules = [x for x, _ in k._rules(prof)]
                near = min(rules, key=lambda x: abs(x - want)) if rules else None
                if near is None or abs(near - want) > 4.0:
                    break
                hit = (near, b1 - 30, b1)
            bad += 0 if hit else 1
            if hit:
                print(f"  {tier} column {COLUMN} {name} rule: committed {want:8.1f} px, "
                      f"re-measured {hit[0]:8.1f} px, surviving north to px row "
                      f"{hit[1]} of the tier's {int(y0)}-{int(y1)}")
            else:
                print(f"  {tier} column {COLUMN} {name} rule: committed {want:8.1f} px, "
                      "NOT FOUND in the tier's own rows   MISMATCH")
    print("\nthe raster still carries the rules the committed reading was taken from"
          if not bad else f"\n{bad} rule(s) no longer re-measure off the raster")
    return 1 if bad else 0


def report(r: dict, quiet=False) -> int:
    found = problems(r)
    if not quiet:
        print(f"THE WEST LEG'S LAST {r['length_m']} m — what Wright's 1834 sheet says\n")
        g = r["the_ground_it_crosses"]
        print(f"  it crosses  {g['tract']}")
        print(f"              {g['column']}, {g['column_width_m']} m wide")
        print("              crossing " + ", ".join(s["street"] for s in g["streets_crossed"])
              + " and nothing else")
        print(f"              the corner at Ohio standing "
              f"{g['corner_south_of_the_grid_east_side_end_m']} m south of where that "
              "column's east side ends\n")
        print("  no corridor is drawn on its line:")
        for row in r["no_corridor_is_drawn_here"]["measured"]:
            print(f"     {row['where']:<28} nearest drawn corridor "
                  f"{abs(row['leg_east_of_corridor_east_rule_m']):7.1f} m west "
                  f"(sheet RMS {r['sheet']['registration_rms_m']} m)")
        print("\n  and the tract boundary is not it:")
        for row in r["the_tract_boundary_is_not_the_continuation"]["measured"]:
            print(f"     {row['where']:<28} {row['leg_west_of_boundary_m']:7.2f} m west "
                  "of the tract's east rule")
        t = r["the_tract_boundary_is_not_the_continuation"]
        print(f"     diverging by {t['divergence_over_the_leg_m']} m over the leg "
              f"({t['bearing_difference_deg']} deg)\n")
        d = r["it_decides_no_building"]
        print(f"  nearest drawn structure {d['nearest_structure']} at {d['clearance_m']} m, "
              f"against {d['drift_at_that_point_m']} m of drift\n")
    for line in found:
        print(f"FAIL  {line}")
    if not found and not quiet:
        print("the refusal holds: the sheet bounds this leg and does not draw it")
    return 1 if found else 0


def self_test() -> int:
    r = read()
    cases = []
    broken = json.loads(json.dumps(r))
    broken["the_ground_it_crosses"]["stations_off_the_platted_grid"] = [0, 1]
    cases.append(("a leg that has left Wabansia's platted ground", broken))
    broken = json.loads(json.dumps(r))
    for row in broken["no_corridor_is_drawn_here"]["measured"]:
        row["leg_east_of_corridor_east_rule_m"] = 3.0
    cases.append(("a drawn corridor inside the sheet's own RMS of the leg", broken))
    broken = json.loads(json.dumps(r))
    broken["the_ground_it_crosses"]["corner_south_of_the_grid_east_side_end_m"] = -5.0
    cases.append(("a corner that has run off the north end of the platted grid", broken))
    broken = json.loads(json.dumps(r))
    broken["the_tract_boundary_is_not_the_continuation"]["divergence_over_the_leg_m"] = -1.0
    cases.append(("a tract boundary that converges on the leg", broken))
    broken = json.loads(json.dumps(r))
    broken["it_decides_no_building"]["clearance_m"] = 1.0
    cases.append(("an extension that reaches a drawn building", broken))
    bad = 0
    for label, case in cases:
        found = problems(case)
        print(f"  self-test | {label}: {'FAIL fired' if found else 'NOTHING FIRED'}")
        if not found:
            bad += 1
    print("\n  self-test | every assertion fires when broken" if not bad
          else f"\n{bad} assertion(s) did not fire")
    return 1 if bad else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--check-sheet", action="store_true")
    ap.add_argument("--gate", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    if args.check_sheet:
        return check_sheet()
    r = read()
    if args.write:
        OUT.write_text(json.dumps({"_doc": __doc__, "ticket": "T-1544", **r},
                                  indent=1, ensure_ascii=False) + "\n")
        print(f"wrote {OUT.relative_to(ROOT)}")
        return 0
    if args.check:
        drifted = committed_matches(r)
        for line in drifted:
            print(f"FAIL  {line}")
        if not drifted:
            print("the committed reading re-derives from the committed geometry")
        return 1 if drifted else 0
    return report(r, quiet=args.quiet and args.gate)


if __name__ == "__main__":
    raise SystemExit(main())
