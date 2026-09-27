#!/usr/bin/env python3
"""Does the reconstructed way to the fort run dry, or does it walk into the drain?

T-1637. `fort_road` is this project's largest single invention on the United States
Reservation — eleven vertices nobody traced, drawn because a garrisoned post that
mustered, traded and drew its stores through the town had a way in (L140). Its own
record has always said it is "clipped by the water mask like every other track, so it
makes honest gaps rather than fords where the ground is wet", and that sentence was
written when no water was anywhere near it.

Then T-1629 moved the South Division drain's mouth EAST of State Street on the owner's
ruling of 2026-09-26, and the new reach crossed this line. Nothing anywhere noticed:
`renderers/web/js/streets.js` dutifully clipped the wet panels, the road came out cut in
two, and every check in the gate stayed green. A visitor walking out to the fort met open
water and no crossing, because nothing says the town laid one — and a bridge invented on
an invented line would be two inventions stacked.

So the invented line moved instead. This file is what stops it moving back, and what
stops the next re-carve of the drain severing it again without saying so:

    tools/measure_fort_road_way.py          print the readings
    tools/measure_fort_road_way.py --gate   exit 1 if the way is severed or undeclared
    tools/measure_fort_road_way.py --self-test

WHAT IS ASSERTED, and each one is a way the way can be wrong:

 1. DRY END TO END. Every sample of the DRAWN track — `track_width_m`, which is the
    ribbon `streets.js` actually paints, not the 12 m legal corridor — stands at or
    above the epoch's water surface. One wet sample is a clipped panel, and a clipped
    panel in the middle of a road is a road that stops.
 2. NO WATERCOURSE CROSSED. The centreline crosses no watercourse centreline in the
    epoch's terrain spec. This road carries no crossing record and no source gives it
    one, so a crossing is the thing it may not have.
 3. THE WEST TERMINUS IS DERIVED, NOT TYPED. It is the far end of the `slough_west`
    approach — the toe of the Slough Log Bridge's own southern graded cut — and it lies
    on State Street's committed centreline. That is the whole argument for the move: the
    way leaves the town over the ONE crossing of this drain the town is documented to
    have built, so the terminus has to be readable off the bridge's own geometry rather
    than chosen to look tidy.

REPORTED AND NOT GATED: how close the centreline comes to the drain's axis, the track's
lowest freeboard, and how much of the 12 m CORRIDOR is wet. The corridor is the extent
this record answers "which way am I standing in" with; a way running up a drain's bank
has a wet edge, and gating that would forbid the bank road this one is.

This file holds no number about 1835. Every figure it compares is read out of the
committed records.
"""

from __future__ import annotations

import argparse
import copy
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
sys.path.insert(0, str(ROOT / "tools"))
from heightfield import Heightfield  # noqa: E402

SCENE = "1835"
EPOCH = "e1834_harbor_cut"
ROAD_ID = "fort_road"
# The street the way leaves the town by, and the approach whose toe is its terminus.
JUNCTION_STREET = "state"
JUNCTION_APPROACH = "slough_west"

# The step the ribbon is read at, and how many lanes across it. Finer than the 2.5 m
# heightfield grid on purpose: the field is sampled bilinearly by the renderer, so the
# waterline sits between cells and a grid-step reading would miss a metre of water.
STEP_M = 0.25
LANES = 9

# The terminus has to BE the approach's end, not sit near it. A tenth of a metre is
# below anything this dataset writes a coordinate to.
TERMINUS_TOL_M = 0.1
# And it has to be on the street. State Street's committed line is two vertices 420 m
# apart, so a terminus read off the approach lands a few centimetres off the chord;
# half a metre is far inside the 80-foot corridor and far outside a typed guess.
STREET_TOL_M = 0.5


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _seg_distance(pt, line) -> float:
    e, n = pt
    best = float("inf")
    for a, b in zip(line, line[1:]):
        dx, dy = b[0] - a[0], b[1] - a[1]
        span = dx * dx + dy * dy
        t = 0.0 if span == 0 else max(0.0, min(1.0, ((e - a[0]) * dx + (n - a[1]) * dy) / span))
        best = min(best, math.hypot(e - (a[0] + dx * t), n - (a[1] + dy * t)))
    return best


def _crosses(a, b, c, d) -> bool:
    """Do segments ab and cd properly cross? Collinear touching does not count."""
    def side(p, q, r):
        return (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])
    d1, d2 = side(a, b, c), side(a, b, d)
    d3, d4 = side(c, d, a), side(c, d, b)
    return ((d1 > 0) != (d2 > 0)) and ((d3 > 0) != (d4 > 0))


def watercourses(epoch_dir: Path, spec: dict):
    """Every watercourse centreline in the epoch, in local ENU metres.

    `swales` entries carry their own `line`; a `watercourses` entry names a GeoJSON file
    in EPSG:26916 instead. Both are read here so the assertion does not care which kind
    of record drew the water.
    """
    out = {}
    for entry in spec.get("swales") or []:
        if entry.get("line"):
            out[entry["id"]] = [(float(p[0]), float(p[1])) for p in entry["line"]]
    datum = load(DATA / "datum.json")
    oe, on = float(datum["origin_utm_e"]), float(datum["origin_utm_n"])
    for entry in spec.get("watercourses") or []:
        src = entry.get("from")
        if not src or not (epoch_dir / src).exists():
            continue
        for feature in load(epoch_dir / src).get("features", []):
            geom = feature.get("geometry") or {}
            if geom.get("type") != "LineString":
                continue
            out[entry["id"]] = [(float(e) - oe, float(n) - on)
                                for e, n in geom["coordinates"]]
    return out


def measure(road_override=None, water_override=None):
    """Every finding this file can make, plus the problems the gate reads."""
    epoch_dir = DATA / "terrain" / "epochs" / EPOCH
    spec = load(epoch_dir / "terrain_spec.json")
    hf = Heightfield.load(epoch_dir)
    streets = {s["id"]: s
               for s in load(DATA / "streets" / f"{SCENE}.json")["streets"]}
    road = copy.deepcopy(streets[ROAD_ID])
    if road_override is not None:
        road["path_local_enu_m"] = road_override
    path = [(float(p[0]), float(p[1])) for p in road["path_local_enu_m"]]
    water_y = float(water_override if water_override is not None
                    else spec["water"]["surface_ft"]) * 0.3048

    courses = watercourses(epoch_dir, spec)
    reading = {
        "vertices": len(path),
        "length_m": round(math.fsum(math.dist(path[i], path[i + 1])
                                    for i in range(len(path) - 1)), 2),
        "track_width_m": float(road["track_width_m"]),
        "corridor_width_m": float(road["corridor_width_m"]),
        "water_surface_m": round(water_y, 3),
        "terminus": [round(path[0][0], 3), round(path[0][1], 3)],
    }
    problems = []

    # --- 1 and the corridor's report: the ribbon against the waterline -------
    def ribbon(half):
        wet, total, lowest, lowest_at = 0, 0, float("inf"), None
        for a, b in zip(path, path[1:]):
            length = math.dist(a, b)
            if length == 0:
                continue
            ux, uy = (b[0] - a[0]) / length, (b[1] - a[1]) / length
            px, py = -uy, ux
            steps = int(length / STEP_M) + 1
            for k in range(steps + 1):
                along = min(k * STEP_M, length)
                e, n = a[0] + ux * along, a[1] + uy * along
                for lane in range(LANES):
                    off = -half + lane * (2 * half) / (LANES - 1)
                    ee, nn = e + px * off, n + py * off
                    if not hf.covers(ee, nn):
                        continue
                    z = hf.height(ee, nn)
                    total += 1
                    if z < lowest:
                        lowest, lowest_at = z, (ee, nn)
                    if z < water_y:
                        wet += 1
        return wet, total, lowest, lowest_at

    wet, total, lowest, lowest_at = ribbon(reading["track_width_m"] * 0.5)
    reading.update(track_samples=total, track_wet=wet,
                   track_lowest_m=round(lowest, 3),
                   track_lowest_at=[round(lowest_at[0], 1), round(lowest_at[1], 1)]
                   if lowest_at else None)
    if wet:
        problems.append(
            f"{wet} of the drawn track's {total} samples stand below the water surface, "
            f"the lowest {lowest - water_y:+.3f} m at E {lowest_at[0]:.1f} "
            f"N {lowest_at[1]:.1f}. streets.js clips those panels, so the way to the "
            f"fort is cut in two and no record says the town laid anything over it")

    corridor_wet, corridor_total, _, _ = ribbon(reading["corridor_width_m"] * 0.5)
    reading.update(corridor_samples=corridor_total, corridor_wet=corridor_wet)

    # --- 2: the road crosses no watercourse ---------------------------------
    crossed = []
    nearest = (float("inf"), None)
    for cid, line in sorted(courses.items()):
        for a, b in zip(path, path[1:]):
            for c, d in zip(line, line[1:]):
                if _crosses(a, b, c, d) and cid not in crossed:
                    crossed.append(cid)
        for a, b in zip(path, path[1:]):
            length = math.dist(a, b)
            steps = max(1, int(length / STEP_M))
            for k in range(steps + 1):
                t = min(1.0, k * STEP_M / length) if length else 0.0
                pt = (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
                gap = _seg_distance(pt, line)
                if gap < nearest[0]:
                    nearest = (gap, cid)
    reading["watercourses_crossed"] = crossed
    reading["nearest_watercourse"] = nearest[1]
    reading["nearest_watercourse_m"] = round(nearest[0], 2)
    if crossed:
        problems.append(
            "the way crosses " + ", ".join(crossed) + " and carries no crossing record. "
            "The one sentence this project has about bridging this drain puts a log "
            "bridge where the town's GRADED STREET met it, and slough_log_bridge is "
            "that crossing; a second one here would be invented outright")

    # --- 3: the terminus is read off the bridge's own approach ---------------
    approach = next((a for a in spec.get("approaches") or []
                     if a.get("id") == JUNCTION_APPROACH), None)
    if approach is None:
        problems.append(f"approach '{JUNCTION_APPROACH}' is gone from the epoch's terrain "
                        f"spec, so the terminus this road is seated on cannot be read")
    else:
        toe = (float(approach["line"][-1][0]), float(approach["line"][-1][1]))
        off_toe = math.dist(path[0], toe)
        reading["approach_toe"] = [round(toe[0], 3), round(toe[1], 3)]
        reading["terminus_off_toe_m"] = round(off_toe, 3)
        if off_toe > TERMINUS_TOL_M:
            problems.append(
                f"the west terminus is E {path[0][0]:.2f} N {path[0][1]:.2f}, "
                f"{off_toe:.2f} m from the toe of the log bridge's southern approach at "
                f"E {toe[0]:.2f} N {toe[1]:.2f}. The move that took this road out of the "
                f"water rests on the terminus being READ off that crossing; a terminus "
                f"chosen freehand is back to a figure nobody can check")
    street = streets.get(JUNCTION_STREET)
    if street is None:
        problems.append(f"street '{JUNCTION_STREET}' is gone from data/streets/{SCENE}.json")
    else:
        line = [(float(p[0]), float(p[1])) for p in street["path_local_enu_m"]]
        off_street = _seg_distance(path[0], line)
        reading["terminus_off_street_m"] = round(off_street, 3)
        if off_street > STREET_TOL_M:
            problems.append(
                f"the west terminus stands {off_street:.2f} m off {JUNCTION_STREET}'s "
                f"committed centreline. The way leaves the town BY that street and over "
                f"its bridge; a terminus in the prairie beside it joins nothing")

    return reading, problems


def report(r) -> None:
    print(f"The fort road — {r['vertices']} vertices, {r['length_m']} m, a "
          f"{r['track_width_m']} m track inside a {r['corridor_width_m']} m corridor, "
          f"water surface {r['water_surface_m']:+.2f} m")
    print(f"  drawn track vs the waterline   {r['track_wet']} of {r['track_samples']} "
          f"samples wet, lowest {r['track_lowest_m']:+.3f} m"
          + (f" at E {r['track_lowest_at'][0]} N {r['track_lowest_at'][1]}"
             if r.get("track_lowest_at") else ""))
    print(f"  the 12 m corridor, reported    {r['corridor_wet']} of "
          f"{r['corridor_samples']} samples wet — a bank road has a wet edge")
    print(f"  watercourses crossed           "
          f"{', '.join(r['watercourses_crossed']) if r['watercourses_crossed'] else 'none'}"
          f" (nearest {r['nearest_watercourse']} at "
          f"{r['nearest_watercourse_m']} m)")
    print(f"  west terminus                  E {r['terminus'][0]} N {r['terminus'][1]}, "
          f"{r.get('terminus_off_toe_m')} m off the log bridge's southern approach toe, "
          f"{r.get('terminus_off_street_m')} m off State Street's centreline")


def self_test() -> int:
    """Break the record three ways and require each assertion to fire."""
    streets = {s["id"]: s for s in load(DATA / "streets" / f"{SCENE}.json")["streets"]}
    good = [[float(p[0]), float(p[1])] for p in streets[ROAD_ID]["path_local_enu_m"]]
    cases = []

    # The alignment T-1637 withdrew: straight out of South Water Street's committed end
    # and across the drain's mouth. All three assertions have something to say about it.
    old = [[805.0, 4.0]] + good[1:]
    cases.append(("the withdrawn alignment is wet, crosses the drain and joins no street",
                  old, None, ("below the water surface", "crosses", "off")))
    # A terminus five metres into the prairie beside State Street: dry, crosses nothing,
    # and unreadable off the bridge — assertion 3 alone.
    adrift = [[good[0][0] - 5.0, good[0][1] - 5.0]] + good[1:]
    cases.append(("a freehand terminus beside the street is caught by the seating "
                  "assertion, on both halves of it", adrift, None,
                  ("from the toe", "off state's committed centreline")))
    # And the water itself rising: the same road, a metre more water, and the dryness
    # assertion has to fire on ground it passed a moment ago.
    cases.append(("a metre more water severs the way the gate just passed",
                  None, 3.281, ("below the water surface",)))

    failed = 0
    fresh, problems = measure()
    if problems:
        print("   the committed record does not pass, so a self-test proves nothing:")
        for p in problems:
            print(f"     {p}")
        return 1
    print(f"   the committed record passes: {fresh['track_wet']} wet samples, "
          f"{len(fresh['watercourses_crossed'])} watercourses crossed, terminus "
          f"{fresh.get('terminus_off_toe_m')} m off the approach toe")
    for label, road, water, wants in cases:
        _, got = measure(road_override=road, water_override=water)
        joined = " | ".join(got)
        missing = [w for w in wants if w not in joined]
        if not got or missing:
            print(f"   FAIL  {label} — expected {wants}, got: {joined or 'nothing'}")
            failed += 1
        else:
            print(f"   ok    {label} ({len(got)} assertion(s) fired)")
    return 1 if failed else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--gate", action="store_true",
                    help="exit 1 if the way is severed, crosses water, or is not seated")
    ap.add_argument("--self-test", action="store_true",
                    help="break the record and require every assertion to fire")
    args = ap.parse_args()

    if args.self_test:
        return self_test()

    reading, problems = measure()
    if not args.gate:
        report(reading)
    for p in problems:
        print(f"FAIL  {ROAD_ID}: {p}", file=sys.stderr)
    if problems:
        return 1
    if args.gate:
        print(f"{ROAD_ID}: {reading['length_m']} m of track, none of its "
              f"{reading['track_samples']} samples below the water surface, no "
              f"watercourse crossed, terminus on the log bridge's southern approach toe")
    return 0


if __name__ == "__main__":
    sys.exit(main())
