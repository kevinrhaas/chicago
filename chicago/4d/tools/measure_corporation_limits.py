#!/usr/bin/env python3
"""Where the Town of Chicago ended, and which of the drawn buildings its by-laws reached.

T-0436. The boundary is authored in `data/reconstruction/1835_corporation_limits.json` as
the Trustees' own survey walk of 7 November 1833, leg by leg; this is the command that
resolves those legs into a ring from the committed streets and the committed shoreline,
and measures the town against it. **Nothing here is hand-typed geometry.** Every vertex
is an intersection of two committed lines or a point on a committed trace, in the same
discipline as `tools/measure_no_build_ground.py` and `data/datum.json`.

## Why it exists

Two ordinances in this corpus bind only *"within the limits of the Corporation"* —
section 18 of 5 August 1835 on stack height, and the fire-brand ordinance of 3 November
1834 — and neither could be scoped, because the line was not in the repository. It is
now, and it is the strongest kind of record this project can hold for it: the corporation
legislating its own bounds, printed three weeks later in the first number of the first
newspaper in Chicago (`chicago_democrat_1833_11_26#c024`, tier 1).

The compilation page this project had been quoting for the same fact
(`chicagology_prefire278`, rung 3 on its own record) is wrong twice against that printing
— it dates the ordinance the 6th and gives the west line as "Jefferson and Cook" — and no
confidence anywhere is graded off it. See the record's own
`the_compilation_page_carries_nothing_here`.

## What it found

- **The ring closes on committed geometry at 215.5 ha, 0.832 square miles.** The
  compilation page's independent "barely seven-eighths of a square mile" is 0.875. Two
  readings two centuries apart agree to 5 per cent, and the resolved one is the smaller,
  which is the direction an extrapolated corner should err in.
- **Twenty-four drawn structures stand OUTSIDE the limits, and every one of them is on
  the United States Reservation** — east of State Street, north of Jackson, south of the
  river channel: exactly the bite the ordinance's river-and-State legs take out of the
  town, and exactly the ground the extension of February 1835 withheld again.
- **Eight of the twenty-four carry chimneys** — the fort's six, the US factor's house and
  J. B. Beaubien's homestead, twelve stacks between them. Section 18's eighteen inches
  never bound one of them. `tools/measure_stack_ordinance.py` says so now rather than
  gating in silence.

    tools/measure_corporation_limits.py           the ring, the legs and the split
    tools/measure_corporation_limits.py --gate    exit 1 if the boundary stops resolving
    tools/measure_corporation_limits.py --self-test   the assertions, fired

The gate is a RE-DERIVATION gate, not a conformance gate. It never moves a building and
it never fails because a building is outside — a building outside the limits is a fact
about 1835, not a defect. It fails when the boundary can no longer be resolved from the
committed geometry it claims to follow: a renamed shoreline feature, a deleted street, a
crossing that stops being unique, a leg whose extrapolation grows long enough to decide a
structure's side of the line.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
LIMITS_PATH = DATA / "reconstruction" / "1835_corporation_limits.json"
SHORELINE = DATA / "terrain" / "epochs" / "e1834_harbor_cut" / "shoreline.geojson"
STREETS_PATH = DATA / "streets" / "1835.json"

sys.path.insert(0, str(ROOT / "tools"))
from plat_occupancy import footprints  # noqa: E402

#: The shoreline feature the ordinance's three eastern legs are all walked on. Matched on
#: `kind` and on the words the trace itself uses, so a renamed feature fails loudly rather
#: than resolving a boundary off some other shore.
SHORE_NAME = "the inner face of the north pier"

#: The project's standing planimetric tolerance for a line resolved off a cadastral plat.
#: Not invented here: the committed shoreline states it of its own traced planform, and
#: every line in this scene is held to it.
TRACE_TOLERANCE_M = 20.0

#: The east-west centrelines whose disagreement measures how far an extrapolated leg can
#: drift. Three surveys, and they do not share a bearing: the Original Town's, Kinzie's
#: Addition's, and the School Section's — whose committed lines are drawn exactly
#: east-west while the other two carry a real one. A leg extended between two of them
#: drifts by their difference in slope times the length of the extension, and that is the
#: whole of the extrapolation's error budget above the trace tolerance.
BEARING_WITNESSES = ("lake", "ohio_north", "madison")


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def street(sid: str):
    """A committed centreline's two ends, in local ENU."""
    for s in load(STREETS_PATH)["streets"]:
        if s["id"] == sid:
            path = s["path_local_enu_m"]
            return tuple(path[0]), tuple(path[-1])
    raise SystemExit(f"data/streets/1835.json no longer carries {sid!r}")


def straight(sid: str):
    """(at_x, at_y, span) for a committed centreline read as the straight line it is."""
    (ax, ay), (bx, by) = street(sid)
    if bx == ax:                                    # due north-south
        at_x = None
    else:
        at_x = lambda x: ay + (by - ay) * (x - ax) / (bx - ax)   # noqa: E731
    at_y = lambda y: ax + (bx - ax) * (y - ay) / (by - ay)       # noqa: E731
    return at_x, at_y, ((min(ax, bx), max(ax, bx)), (min(ay, by), max(ay, by)))


def shore() -> list[tuple[float, float]]:
    datum = load(DATA / "datum.json")
    for feature in load(SHORELINE)["features"]:
        props = feature["properties"]
        if props.get("kind") == "shore" and SHORE_NAME in props.get("name", ""):
            return [(x - datum["origin_utm_e"], y - datum["origin_utm_n"])
                    for x, y in feature["geometry"]["coordinates"]]
    raise SystemExit(f"no shoreline feature names {SHORE_NAME!r}; the ordinance's lake, "
                     "pier and river legs are all walked on that one trace")


def limits_ring():
    """The ring, and the report of how far each leg had to be extended to close it.

    Walked in the ordinance's own order and no other: Jackson and Jefferson, north to
    Ohio, east to the lake, south round the pier, west up the river to the Canal
    Commissioners' east line, south to Jackson, home.
    """
    jefferson_at_x, jefferson_at_y, jeff_span = straight("jefferson_school_section")
    ohio_at_x, _, ohio_span = straight("ohio_north")
    jackson_at_x, _, jack_span = straight("jackson")
    state_at_x, state_at_y, state_span = straight("state")

    jx = street("jefferson_school_section")[0][0]
    if street("jefferson_school_section")[1][0] != jx:
        raise SystemExit("Jefferson's committed centreline is no longer due north-south; "
                         "the west leg cannot be extended along its own bearing")

    corner_jackson = (jx, jackson_at_x(jx))
    corner_ohio = (jx, ohio_at_x(jx))

    line = shore()

    def crossings(f):
        return [i for i in range(len(line) - 1) if f(line[i]) * f(line[i + 1]) < 0]

    def cut(index, f):
        a, b = line[index], line[index + 1]
        t = f(a) / (f(a) - f(b))
        return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)

    on_ohio = lambda p: p[1] - ohio_at_x(p[0])          # noqa: E731
    on_state = lambda p: p[0] - state_at_y(p[1])        # noqa: E731
    co, cs = crossings(on_ohio), crossings(on_state)
    if len(co) != 1 or len(cs) != 1:
        raise SystemExit(f"the traced shore crosses Ohio's line {len(co)} time(s) and "
                         f"State's {len(cs)} time(s); the corporate boundary is only "
                         "readable when each crossing is unique")
    corner_lake, corner_state = cut(co[0], on_ohio), cut(cs[0], on_state)
    if cs[0] >= co[0]:
        raise SystemExit("the shore trace no longer runs from the river mouth eastward "
                         "and then north; the ordinance's walk cannot be read off it")

    ring = ([corner_jackson, corner_ohio, corner_lake]
            + [line[i] for i in range(co[0], cs[0], -1)]
            + [corner_state, (state_at_y(corner_jackson[1]), corner_jackson[1])])

    # The five stretches where a committed centreline is carried past its own end. Each
    # is (label, from the committed end, to the resolved corner) — the base of every one
    # of them is a point ON the committed line, so the drift is zero there and grows
    # along the extension. That is why an extrapolation is measured along its own length
    # and not as a flat clearance.
    reach = [
        ("west — Jefferson, north to Ohio",
         (jx, jeff_span[1][1]), corner_ohio),
        ("north — Ohio, west to Jefferson",
         (ohio_span[0][0], ohio_at_x(ohio_span[0][0])), corner_ohio),
        ("north — Ohio, east to the lake shore",
         (ohio_span[0][1], ohio_at_x(ohio_span[0][1])), corner_lake),
        ("east — State, north to the river",
         (state_at_y(state_span[1][1]), state_span[1][1]), corner_state),
        ("east — State, south to Jackson",
         (state_at_y(state_span[1][0]), state_span[1][0]), ring[-1]),
    ]
    return ring, reach


def inside(point, polygon) -> bool:
    x, y = point
    hit = False
    j = len(polygon) - 1
    for i in range(len(polygon)):
        xi, yi = polygon[i]
        xj, yj = polygon[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
            hit = not hit
        j = i
    return hit


def ring_area(polygon) -> float:
    total = 0.0
    for i in range(len(polygon)):
        x1, y1 = polygon[i]
        x2, y2 = polygon[(i + 1) % len(polygon)]
        total += x1 * y2 - x2 * y1
    return abs(total) / 2


def bearing_spread() -> float:
    """How far the committed surveys disagree on which way east is, in slope.

    Measured, never assumed. Three east-west centrelines, one per survey the ordinance's
    legs run between, and the widest pair of them is the error a leg carries when it is
    extended from one survey into another.
    """
    slopes = {}
    for sid in BEARING_WITNESSES:
        (ax, ay), (bx, by) = street(sid)
        if bx == ax:
            raise SystemExit(f"{sid} is no longer an east-west line and cannot witness "
                             "the survey bearing")
        slopes[sid] = (by - ay) / (bx - ax)
    return max(slopes.values()) - min(slopes.values())


def drift_m(along_m: float) -> float:
    """The uncertainty of an extrapolated leg `along_m` past the end of its own line."""
    return TRACE_TOLERANCE_M + along_m * bearing_spread()


def beside(segment, polygon):
    """(perpendicular clearance, distance along) for the footprint vertex nearest a leg.

    Only vertices whose foot of perpendicular falls ON the extension count: a building
    standing off the END of an extension is beside the committed line instead, where
    there is no extrapolation to be wrong about.
    """
    (ax, ay), (bx, by) = segment
    dx, dy = bx - ax, by - ay
    span = dx * dx + dy * dy
    if span == 0:
        return None
    length = span ** 0.5
    best = None
    for px, py in polygon:
        t = ((px - ax) * dx + (py - ay) * dy) / span
        if not 0.0 <= t <= 1.0:
            continue
        perpendicular = abs((px - ax) * dy - (py - ay) * dx) / length
        if best is None or perpendicular < best[0]:
            best = (perpendicular, t * length)
    return best


def clearances(reach):
    """One row per extrapolated leg: how long it is, and what stands closest beside it."""
    datum = load(DATA / "datum.json")
    placed = footprints(datum)
    rows = []
    for label, a, b in reach:
        length = ((b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2) ** 0.5
        nearest = None
        for sid, polygon in placed:
            hit = beside((a, b), polygon)
            if hit and (nearest is None or hit[0] < nearest[0]):
                nearest = (hit[0], hit[1], sid)
        rows.append({"leg": label, "length_m": length, "nearest": nearest,
                     "drift_m": drift_m(nearest[1]) if nearest else None})
    return rows


def split(ring=None):
    """(inside, outside) structure ids. A structure is outside only if every phase is."""
    if ring is None:
        ring, _ = limits_ring()
    datum = load(DATA / "datum.json")
    verdict: dict[str, bool] = {}
    for sid, polygon in footprints(datum):
        cx = sum(p[0] for p in polygon) / len(polygon)
        cy = sum(p[1] for p in polygon) / len(polygon)
        verdict[sid] = verdict.get(sid, True) and inside((cx, cy), ring)
    return (sorted(s for s, ok in verdict.items() if ok),
            sorted(s for s, ok in verdict.items() if not ok))


def problems(ring, reach) -> list[str]:
    """What must hold for this boundary to keep meaning what it says.

    None of these fails because a building stands outside the limits. A building outside
    the limits is a fact about 1835. They fail when the boundary stops being READABLE off
    the committed geometry — or when an extrapolated leg comes close enough to a drawn
    building that the extension, rather than the ordinance, is what decides its side.
    """
    found = []
    if len(ring) < 8:
        found.append(f"the ring resolved to {len(ring)} vertices, which is fewer than "
                     "the ordinance's own six legs can produce")
    area_ha = ring_area(ring) / 1e4
    if not 150.0 < area_ha < 300.0:
        found.append(f"the ring measures {area_ha:.1f} ha; the corporation's own extent "
                     "was near seven-eighths of a square mile (226.6 ha), and a ring "
                     "this far from it is a resolution fault, not a finding")
    for row in clearances(reach):
        near = row["nearest"]
        if near and near[0] < row["drift_m"]:
            found.append(
                f"{near[2]} stands {near[0]:.1f} m from '{row['leg']}', which at "
                f"{near[1]:.0f} m past the end of its own committed centreline is "
                f"uncertain by {row['drift_m']:.1f} m. The extension, not the ordinance, "
                f"is deciding which side of the corporate boundary that building is on. "
                f"Trace the street, or leave the structure's side unstated — do not "
                f"widen the tolerance.")
    return found


def report(quiet=False) -> int:
    record = load(LIMITS_PATH)
    ring, reach = limits_ring()
    ins, out = split(ring)
    found = problems(ring, reach)

    if not quiet:
        ordinance = record["ordinance"]
        print("THE LIMITS OF THE CORPORATION, as the Trustees of the Town of Chicago "
              "walked them on 7 November 1833")
        print(f"  {ordinance['id']} — tier {ordinance['source_tier']}, printed "
              f"{ordinance['printed']}\n")
        print(f"  {'leg':<14} {'confidence':<11} resolves on")
        for leg in record["legs"]:
            print(f"  {leg['id']:<14} {leg['confidence']:<11} "
                  f"{', '.join(s.split('/')[-1] for s in leg['resolves_on'])}")

        spread = bearing_spread()
        print(f"\nthe three surveys disagree on the bearing of east by {spread:.6f} in "
              f"slope, measured off {', '.join(BEARING_WITNESSES)}. A leg carried past "
              f"the end of\nits own committed centreline is uncertain by "
              f"{TRACE_TOLERANCE_M:.0f} m plus that slope times the length of the "
              f"extension:\n")
        print(f"  {'leg':<38} {'extended':>10} {'nearest building beside it':>30}")
        for row in clearances(reach):
            near = row["nearest"]
            if near is None:
                stands = "nothing stands beside it"
            else:
                verdict = "decided" if near[0] >= row["drift_m"] else "NOT DECIDED"
                stands = (f"{near[0]:7.1f} m vs {row['drift_m']:5.1f} m of drift  "
                          f"{verdict}  {near[2]}")
            print(f"  {row['leg']:<38} {row['length_m']:>8.1f} m  {stands}")

        area_ha = ring_area(ring) / 1e4
        print(f"\nthe ring closes on {len(ring)} vertices, {area_ha:.1f} ha "
              f"({area_ha * 1e4 / 2589988.11:.3f} square miles) — against the "
              f"'barely seven-eighths of a\nsquare mile' (0.875) of "
              f"chicagology_prefire278, which grades nothing here and checks this.\n")
        print(f"INSIDE the limits: {len(ins)} structure(s)")
        print(f"OUTSIDE them: {len(out)} structure(s). The by-laws of the Town of "
              f"Chicago reached none of these:")
        for sid in out:
            print(f"    {sid}")
        print()

    if found:
        for line in found:
            print(f"FAIL: {line}")
        return 1
    print(f"OK: the corporate boundary of 7 November 1833 re-derives from the committed "
          f"streets and the committed shoreline — {len(ring)} vertices, "
          f"{ring_area(ring) / 1e4:.1f} ha, {len(ins)} structure(s) inside it and "
          f"{len(out)} outside, and no extrapolated leg decides one of them.")
    return 0


def self_test() -> int:
    """The four ways this could resolve a boundary it should refuse."""
    ring, reach = limits_ring()
    cases = []

    # 1. A ring that has collapsed must fail rather than report a small town.
    cases.append(("a collapsed ring is refused",
                  bool(problems(ring[:4], []))))
    # 2. The area assertion must actually bite. Halve the ring about its centroid.
    cx = sum(p[0] for p in ring) / len(ring)
    cy = sum(p[1] for p in ring) / len(ring)
    shrunk = [(cx + (x - cx) * 0.5, cy + (y - cy) * 0.5) for x, y in ring]
    cases.append(("a ring at a quarter of the corporation's extent is refused",
                  bool(problems(shrunk, []))))
    # 3. The fort must be outside and the Sauganash inside — the two ends of the finding.
    ins, out = split(ring)
    cases.append(("the fort stands outside the limits",
                  "fort_dearborn_barracks" in out))
    cases.append(("the Sauganash stands inside them",
                  "sauganash_hotel" in ins))
    # 4. A renamed shoreline feature must fail loudly rather than resolve on some other
    #    shore. Fired by asking for a name the trace does not carry.
    global SHORE_NAME
    keep, SHORE_NAME = SHORE_NAME, "a shore this project does not hold"
    try:
        shore()
        raised = False
    except SystemExit:
        raised = True
    finally:
        SHORE_NAME = keep
    cases.append(("a renamed shoreline feature is refused, not resolved past", raised))

    # 5. The drift check must BITE. Widen the trace tolerance past every clearance in
    #    the table and the extrapolated legs must start refusing to decide.
    global TRACE_TOLERANCE_M
    keep, TRACE_TOLERANCE_M = TRACE_TOLERANCE_M, 400.0
    try:
        cases.append(("an extrapolated leg that reaches a building refuses to decide it",
                      bool(problems(ring, reach))))
    finally:
        TRACE_TOLERANCE_M = keep

    bad = [name for name, ok in cases if not ok]
    for name, ok in cases:
        print(f"  {'ok  ' if ok else 'FAIL'}  {name}")
    if bad:
        print(f"FAIL: {len(bad)} assertion(s) no longer fire: {', '.join(bad)}")
        return 1
    print(f"OK: all {len(cases)} assertions fire.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--gate", action="store_true",
                    help="exit 1 if the boundary no longer re-derives")
    ap.add_argument("--quiet", action="store_true", help="one line of output")
    ap.add_argument("--self-test", action="store_true", dest="selftest")
    args = ap.parse_args()
    if args.selftest:
        return self_test()
    return report(quiet=args.quiet)


if __name__ == "__main__":
    raise SystemExit(main())
