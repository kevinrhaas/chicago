#!/usr/bin/env python3
"""What stands on ground that was never open to a private builder.

ROADMAP T-E2. The refusal is authored in
`data/reconstruction/1835_no_build_ground.json`; this is the command that resolves its
boundaries from the committed traces and measures them. Nothing here is hand-typed
geometry — the reservation's two survey lines come out of one ground-control point and
the plat's own bearing, and its third side is the traced waterline. Re-deriving rather
than storing is the same discipline `data/datum.json` is held to, and for the same
reason: a stored vertex cannot be wrong loudly.

The companion for platted blocks is `tools/measure_reserved_ground.py` (T-A16), which
answers the question for ground the plat DID subdivide. This one answers it for ground
the plat never reached.

    tools/measure_no_build_ground.py          print the table
    tools/measure_no_build_ground.py --gate   exit 1 if anything unpermitted stands there

Three things fail the gate, and the third is the one worth having:

1. A structure standing on refused ground that the region does not permit.
2. A permitted entry naming a record that is not there — a permission list that can go
   stale in silence is a way of turning the gate off.
3. UNDER-COVERAGE. Every cell of the committed heightfield above the water surface,
   east of the reservation's west line, north of Madison's line and south of the main
   stem, must fall inside one of the polygons. It does today, exactly: the count is
   zero. T-E3 extends the terrain east and south, and when it does, this is the
   assertion that will notice that the polygons no longer reach the ground.

A fourth, since T-0891: a region whose ring this tool cannot RESOLVE cannot enter the
file at all. Two of the three rings are bespoke — the reservation's two survey lines and
the traced waterline, and the bar's committed polygon. The third method is general:
`plate_reading` rebuilds a ring from the corner pixels and the transform a committed
trace of a raster records, and fails if the ground corners that trace also carries have
stopped agreeing with them. That is what let the Fort Cemetery in: it is two boundary
lines and a name on the 1830 Harrison plan, and until there was a resolver for a ring
read off a plate, putting it here would have meant hand-typing the one thing this file
exists to forbid.

The regions may OVERLAP — the cemetery stands wholly inside the reservation — so the
total refused area is their UNION and never the sum of their parts.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
NO_BUILD_PATH = DATA / "reconstruction" / "1835_no_build_ground.json"
EPOCH = DATA / "terrain" / "epochs" / "e1834_harbor_cut"
SHORELINE = EPOCH / "shoreline.geojson"
GCP_PATH = DATA / "traces" / "gcp" / "wright_1834_gcps.json"
STREETS_PATH = DATA / "streets" / "1835.json"

sys.path.insert(0, str(ROOT / "tools"))
from plat_occupancy import footprints  # noqa: E402
from heightfield import Heightfield  # noqa: E402

# The shore feature the reservation's third side is walked along. Matched on the `kind`
# and on the words the trace itself uses, so a renamed feature fails loudly.
SHORE_NAME = "the Fort Dearborn reservation's lake shore"
# Ground north of this is the North Division, across the main stem, and is not the
# reservation however far east it lies. Only the under-coverage count uses it.
SOUTH_BANK_N = 40.0
WATER_SURFACE_M = 0.0
# The largest disagreement ROUNDING alone can produce between a plate reading's
# committed ground corners and the ones its own pixels and transform give back. The
# traces print those corners to one or two decimal places; anything past this is an
# edit, not a rounding. It is not a statement about the accuracy of a plate reading.
PLATE_ROUNDING_M = 0.05


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


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


def plat_bearing() -> float:
    """The plat's east-west slope in local ENU, read off the committed centrelines.

    Lake, Randolph and Washington are three straight committed lines of the same grid.
    They agree exactly, and the agreement is asserted rather than assumed: a grid whose
    own streets disagree is a finding, not a number to average away.
    """
    slopes = []
    for street in load(STREETS_PATH)["streets"]:
        if street["id"] not in {"lake", "randolph", "washington"}:
            continue
        path = street["path_local_enu_m"]
        (ax, ay), (bx, by) = path[0], path[-1]
        slopes.append(round((by - ay) / (bx - ax), 6))
    if len(slopes) != 3:
        raise SystemExit("the plat bearing needs Lake, Randolph and Washington")
    if len(set(slopes)) != 1:
        raise SystemExit(f"the plat's own east-west streets disagree on bearing: {slopes}")
    return slopes[0]


def section_corner() -> tuple[float, float]:
    """G1 — State & Madison — in local ENU. The PLSS corner both lines run from."""
    datum = load(DATA / "datum.json")
    points = load(GCP_PATH)
    points = points.get("points") or points.get("gcps")
    g1 = next((p for p in points if p["id"] == "G1"), None)
    if g1 is None:
        raise SystemExit("wright_1834_gcps.json no longer carries G1")
    if "Madison" not in g1["map_feature"]:
        raise SystemExit(f"G1 is no longer State & Madison but {g1['map_feature']!r}")
    return (g1["modern"]["utm_e"] - datum["origin_utm_e"],
            g1["modern"]["utm_n"] - datum["origin_utm_n"])


def shore_line() -> list[tuple[float, float]]:
    datum = load(DATA / "datum.json")
    for feature in load(SHORELINE)["features"]:
        props = feature["properties"]
        if props.get("kind") == "shore" and SHORE_NAME in props.get("name", ""):
            return [(x - datum["origin_utm_e"], y - datum["origin_utm_n"])
                    for x, y in feature["geometry"]["coordinates"]]
    raise SystemExit(f"no shoreline feature names {SHORE_NAME!r}")


def bar_ring() -> list[tuple[float, float]]:
    datum = load(DATA / "datum.json")
    for feature in load(SHORELINE)["features"]:
        if feature["properties"].get("kind") == "bar":
            return [(x - datum["origin_utm_e"], y - datum["origin_utm_n"])
                    for x, y in feature["geometry"]["coordinates"][0]]
    raise SystemExit("no `bar` feature in the committed shoreline")


def reservation_ring():
    """The reservation polygon, and the two lines it was resolved from.

    West: the section line north from G1. South: Madison's line east from G1. The rest
    is the traced waterline, walked from where the west line meets it round to where
    Madison's does. Both crossings must be unique — a shore that crosses either line
    twice is a shore this construction cannot read, and it says so rather than picking
    one.
    """
    ge, gn = section_corner()
    slope = plat_bearing()
    madison = lambda e: gn + (e - ge) * slope                      # noqa: E731
    section = lambda n: ge + (n - gn) * (-slope)                   # noqa: E731
    shore = shore_line()

    def crossings(f):
        return [i for i in range(len(shore) - 1) if f(shore[i]) * f(shore[i + 1]) < 0]

    def cut(index, f):
        a, b = shore[index], shore[index + 1]
        t = f(a) / (f(a) - f(b))
        return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)

    on_madison = lambda p: p[1] - madison(p[0])                    # noqa: E731
    on_section = lambda p: p[0] - section(p[1])                    # noqa: E731
    cm, cs = crossings(on_madison), crossings(on_section)
    if len(cm) != 1 or len(cs) != 1:
        raise SystemExit(f"the traced shore crosses Madison {len(cm)} time(s) and the "
                         f"section line {len(cs)} time(s); the reservation boundary is "
                         "only readable when each crossing is unique")
    ring = ([(ge, gn), cut(cs[0], on_section)]
            + [shore[i] for i in range(cs[0], cm[0], -1)]
            + [cut(cm[0], on_madison)])
    return ring, madison, section


def plate_ring(region) -> list[tuple[float, float]]:
    """A ring READ OFF A PLATE — rebuilt here from the plate's own pixels.

    The two rings above are resolved from survey lines and from a committed trace, and
    that is why this file may author no vertex: the polygon is recomputed every time the
    gate runs, so it cannot drift away from the geometry it claims to follow. A parcel
    that exists only as ink on a sheet has no such line to be resolved from. The Fort
    Cemetery is two boundary lines and a name on the 1830 Harrison plan, and nothing else
    in this project states where it is.

    The discipline still holds, one step further back. The trace records the plate's own
    transform — an anchor pixel, the ground point that pixel is hung on, and a scale —
    and the corner PIXELS it measured; the ground corners it also carries are a
    derivative of those two, not an independent reading. So the ring is rebuilt here from
    the pixels and the transform, and the trace's own ground corners are checked against
    it. A corner edited without its pixel, or a transform that moves under a reading taken
    before it, fails loudly instead of quietly re-siting a parcel. That is the same bargain
    `data/datum.json` is held to, made against a raster instead of against ground control.

    The tolerance is ROUNDING, not slack. The trace prints its ground corners to two
    decimal places and one of them to one, so 0.05 m is the largest disagreement that
    rounding alone can produce; anything above it is an edit. It is not, and must not be
    read as, the record's accuracy — the plate carries no scale bar, and this reading
    carries the +/-25 m on position that every plate-derived record in this dataset does.
    """
    boundary = region["boundary"]
    trace_path = ROOT / boundary["control"]
    if not trace_path.exists():
        raise SystemExit(f"{region['id']} cites {boundary['control']}, which is not there")
    return ring_from_plate(load(trace_path), boundary["ring"], boundary["control"])


def ring_from_plate(trace, ring_name: str, where: str) -> list[tuple[float, float]]:
    """The re-derivation itself, over a loaded trace. Separated from the file handling so
    `--self-test` can prove each refusal below actually fires — an assertion nothing
    exercises is an assertion that can rot into a pass."""
    member = trace.get(ring_name)
    if member is None:
        raise SystemExit(f"{where} carries no {ring_name!r} reading for a region to "
                         "resolve its boundary from")
    transform = trace.get("the_transform")
    if transform is None:
        raise SystemExit(f"{where} states no transform, so the ring it carries cannot "
                         "be re-derived and may not be trusted")
    if "+x east and +y south" not in transform.get("orientation", ""):
        raise SystemExit(f"{where} no longer states the pixel axes this resolver "
                         "assumes (+x east, +y south); re-derive or state them")
    (anchor_x, anchor_y) = transform["anchor_px"]
    (anchor_e, anchor_n) = transform["anchor_local_enu_m"]
    scale = transform["scale_m_per_px"]
    pixels, committed = member["corners_px"], member["corners_local_enu_m"]
    if len(pixels) != len(committed) or len(pixels) < 3:
        raise SystemExit(f"{ring_name} in {where} reads {len(pixels)} corner "
                         f"pixel(s) and carries {len(committed)} ground corner(s); the "
                         "two must be the same ring")
    ring = [(anchor_e + (x - anchor_x) * scale, anchor_n - (y - anchor_y) * scale)
            for x, y in pixels]
    drift = max(max(abs(e - ce), abs(n - cn))
                for (e, n), (ce, cn) in zip(ring, committed))
    if drift > PLATE_ROUNDING_M:
        raise SystemExit(
            f"{ring_name} in {where} no longer re-derives: its "
            f"committed ground corners stand {drift:.3f} m from what its own corner "
            f"pixels and transform give, past the {PLATE_ROUNDING_M} m that rounding "
            "can account for. One of the two was edited without the other.")
    return ring


# One resolver per region, and the asymmetry is the point. The first two are bespoke,
# because each is resolved from a different committed geometry and there is exactly one
# of each. `plate_reading` is NOT bespoke: it is the general case, and any region whose
# boundary states that method resolves through the same code — which is what T-0891
# asked for, and what kept the Fort Cemetery's polygon out of this file until now.
BESPOKE_RINGS = {
    "fort_dearborn_reservation": lambda region: reservation_ring()[0],
    "river_mouth_sand_bar": lambda region: bar_ring(),
}


def region_ring(region) -> list[tuple[float, float]]:
    """The polygon for one authored region, resolved rather than read out of the file."""
    if region["boundary"]["method"] == "plate_reading":
        return plate_ring(region)
    resolver = BESPOKE_RINGS.get(region["id"])
    if resolver is None:
        raise SystemExit(
            f"{region['id']} states boundary method "
            f"{region['boundary']['method']!r} and this tool cannot resolve it. A region "
            f"whose ring cannot be re-derived may not enter {NO_BUILD_PATH.name}: give it "
            "a resolver here, or author it as a `plate_reading` off a committed trace.")
    return resolver(region)


def measure():
    """(regions, problems). One row per structure touching refused ground."""
    authored = load(NO_BUILD_PATH)["regions"]
    # Every ring comes from the authored list, so the two can no longer disagree about
    # which regions exist — the symmetric-difference check this replaced is now a thing
    # the structure of the code forbids. What CAN still fail is a region this tool has no
    # way to resolve, and `region_ring` says so by name.
    rings = {region["id"]: region_ring(region) for region in authored}
    _, madison, section = reservation_ring()

    placed = footprints(load(DATA / "datum.json"))
    field = Heightfield.load(EPOCH)
    if field is None:
        raise SystemExit("cannot measure refused ground: the committed heightfield is missing")
    cell = field.cell_m

    # The heightfield is walked ONCE and every region asked of each cell, for two
    # reasons. It is cheaper than a pass per region, and — the one that matters — the
    # regions may OVERLAP: the Fort Cemetery stands wholly inside the reservation, so a
    # sum of their areas would count the same square metre twice and overstate how much
    # of the scene is refused. Each region still reports its own extent; the total is the
    # union.
    cells = {region_id: 0 for region_id in rings}
    union_cells = 0
    scene_land = 0
    outside = 0
    for r in range(field.rows):
        n = field.origin_n + r * cell
        for c in range(field.cols):
            e = field.origin_e + c * cell
            height = field.height(e, n)
            if height is None or height <= WATER_SURFACE_M:
                continue
            scene_land += 1
            hits = [region_id for region_id, polygon in rings.items()
                    if inside((e, n), polygon)]
            for region_id in hits:
                cells[region_id] += 1
            if hits:
                union_cells += 1
            # Under-coverage: land above the water surface that ought to be inside one of
            # them. T-E3 extends the terrain east and south; this is the count that
            # notices when the polygons no longer reach the ground the terrain models.
            elif n < SOUTH_BANK_N and e >= section(n) and n >= madison(e):
                outside += 1

    regions, problems = [], []
    for region in authored:
        region_id = region["id"]
        polygon = rings[region_id]
        permitted = {p["structure_id"]: p["why"]
                     for p in region["what_may_stand_here"]["permitted"]}
        rows, seen = [], set()
        for sid, world in placed:
            corners = sum(1 for p in world if inside(p, polygon))
            if not corners:
                continue
            seen.add(sid)
            rows.append({"structure": sid, "corners_in": corners, "of": len(world),
                         "permitted": sid in permitted})
            if sid not in permitted:
                problems.append(
                    f"{sid} stands on {region['name']} with {corners} of {len(world)} "
                    f"footprint corners inside it, and {NO_BUILD_PATH.name} does not "
                    "permit it there")
        for sid in sorted(set(permitted) - seen):
            problems.append(
                f"{region['name']} permits {sid} and no committed footprint of {sid} "
                "touches it — a permission for a record that is not there")
        regions.append({
            "id": region_id, "name": region["name"], "rows": rows,
            "acres": ring_area(polygon) / 4046.8564,
            "land_ha": cells[region_id] * cell * cell / 10_000,
            # Which other refused regions already cover all of this one. Printed because
            # a region that adds no ground is not a fault — the cemetery's worth is that
            # the refusal is named and separately graded, not that it refuses more — but
            # it would read as one if the table let it look like new acreage.
            "wholly_inside": sorted(
                other["id"] for other in authored if other["id"] != region_id
                and all(inside(p, rings[other["id"]]) for p in polygon)),
        })

    if outside:
        problems.append(
            f"{outside} cell(s) of modelled ground above the water surface stand east "
            "of the reservation's west line, north of Madison and south of the main "
            "stem, and inside none of the refused regions — the polygons no longer "
            "reach the ground the terrain models")
    refused_ha = union_cells * cell * cell / 10_000
    return regions, problems, outside, scene_land, cell, refused_ha


def self_test() -> int:
    """Prove every refusal in `ring_from_plate` fires, and that the real trace re-derives.

    T-0891 added a resolver whose whole worth is what it REFUSES — a ground corner edited
    without its pixel, a transform swapped under a reading taken before it, a ring whose
    two halves are different lengths. None of those is reachable from the committed data,
    so nothing would ever run them, and an assertion nothing runs is one that can rot into
    a pass unnoticed. These fabricate each case against a copy of the real reading.
    """
    import copy

    ASSERTIONS = 9
    real = load(DATA / "traces" / "harrison_1830_fort_burial_ground.json")
    here = "harrison_1830_fort_burial_ground.json"
    failures = []

    def refuses(what: str, mangle) -> None:
        trace = copy.deepcopy(real)
        mangle(trace)
        try:
            ring_from_plate(trace, "fort_cemetery", here)
        except SystemExit as refusal:
            print(f"   FAIL as designed: {what} — {refusal}")
            return
        failures.append(what)

    # It accepts the reading as committed, and the ring closes on the stated area.
    ring = ring_from_plate(real, "fort_cemetery", here)
    stated = real["fort_cemetery"]["extent"]["area_m2"]
    if abs(ring_area(ring) - stated) > 1.0:
        failures.append(f"the committed ring encloses {ring_area(ring):.1f} m2, not {stated}")
    else:
        print(f"   ok: the committed reading re-derives and encloses {stated} m2")

    refuses("a ground corner edited without its pixel",
            lambda t: t["fort_cemetery"]["corners_local_enu_m"][0].__setitem__(0, 1058.5))
    refuses("a corner pixel edited without its ground corner",
            lambda t: t["fort_cemetery"]["corners_px"][2].__setitem__(1, 1770.0))
    refuses("a transform moved under a reading taken before it",
            lambda t: t["the_transform"].__setitem__("scale_m_per_px", 0.34))
    refuses("a ring whose pixels and ground corners are different lengths",
            lambda t: t["fort_cemetery"]["corners_px"].pop())
    refuses("a trace that states no transform",
            lambda t: t.pop("the_transform"))
    refuses("a trace whose pixel axes are no longer the ones assumed",
            lambda t: t["the_transform"].__setitem__("orientation", "north up, +y north"))
    refuses("a ring name the trace does not carry",
            lambda t: t.pop("fort_cemetery"))

    # The 0.05 m tolerance is rounding, not slack: 0.04 m of drift must still pass.
    nudged = copy.deepcopy(real)
    corner = nudged["fort_cemetery"]["corners_local_enu_m"][1]
    corner[1] = round(corner[1] - 0.04, 4)
    try:
        ring_from_plate(nudged, "fort_cemetery", here)
    except SystemExit:
        failures.append("0.04 m of drift is refused, so the tolerance is not rounding")
    else:
        print("   ok: 0.04 m of drift still passes — the tolerance is rounding, not slack")

    for failure in failures:
        print(f"   SELF-TEST DID NOT FIRE — it accepted {failure}")
    print(f"   self-test: {ASSERTIONS - len(failures)} of {ASSERTIONS} assertions hold")
    return 1 if failures else 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gate", action="store_true",
                        help="exit 1 when something unpermitted stands on refused ground")
    parser.add_argument("--self-test", action="store_true",
                        help="prove the plate-reading resolver's refusals still fire")
    args = parser.parse_args()

    if args.self_test:
        return self_test()

    regions, problems, outside, scene_land, cell, refused_ha = measure()
    for region in regions:
        shared = ""
        if region["wholly_inside"]:
            shared = " — wholly inside " + ", ".join(region["wholly_inside"])
        print(f"   {region['name']} — {region['acres']:.2f} acres enclosed, "
              f"{region['land_ha']:.2f} ha of it modelled land{shared}")
        for row in region["rows"]:
            mark = "ok " if row["permitted"] else "REFUSED"
            print(f"      {mark:>7}  {row['structure']}  "
                  f"{row['corners_in']}/{row['of']} corners in")
        if not region["rows"]:
            print("      nothing stands here")
    scene_ha = scene_land * cell * cell / 10_000
    print(f"   {refused_ha:.2f} ha refused of {scene_ha:.2f} ha of modelled land "
          f"above the water surface — {100 * refused_ha / scene_ha:.1f} % "
          "(the union: the regions overlap and are not summed)")
    print(f"   under-coverage: {outside} cell(s) of modelled land outside every region")
    for problem in problems:
        print(f"   {problem}")
    return 1 if (problems and args.gate) else 0


if __name__ == "__main__":
    raise SystemExit(main())
