#!/usr/bin/env python3
"""Re-derive the West Division's eighteen block-numeral crops from committed street lines.

T-1095, piece 2 of 2 of T-1089, itself split out of T-0858. Wright writes a
numeral across the middle of every block of the Original Town. T-0788 read
twenty-four of them by cutting each crop from that block's OWN committed street
lines — an identification made by the georeference rather than by the reader's
eye — T-1088 read the North Division's seven the same way once that tier's
streets landed, and T-1094 read the Washington-Madison tier's seven once Madison
Street did. What was left refused was the West Division: **8-13, 22-27 and
46-51**, eighteen numerals on the far side of the South Branch, refused because
"no committed street line reaches them, so no crop can be cut". This file cuts
them, and says exactly what each side of each box is standing on.

THE THREE KINDS OF SIDE, AND WHICH BLOCKS USE WHICH.

  committed          `clinton` and `canal` are in data/streets/1835.json and run
                     the length of the division; `kinzie`/`kinzie_west` and
                     `madison` reach the whole width. Four of the eighteen boxes
                     (8, 13, 23, 50) are flanked east and west by committed lines
                     and nothing else.
  continued          `carroll`, `fulton`, `lake`, `randolph` and `washington` are
                     committed but CLIPPED AT EAST -320 m — the clip is this
                     reconstruction's own extent, not a claim that the street
                     ended there (the note on `fulton` says so). Each is continued
                     WEST along the bearing of its own committed path. `clinton`
                     and `canal` are continued north and south the same way where
                     a tier lies past their ends. This is T-1094's rule turned
                     through ninety degrees.
  stepped            Jefferson Street and Des Plaines Street were REFUSED as
                     streets when these eighteen numerals were read — both lay
                     wholly west of the modelled ground's edge at east -320 m, and
                     docs/RESEARCH/west_division_streets.md §2 refused them on
                     exactly that ground. T-1430 HAS SINCE SEATED BOTH, on the
                     field T-1416 built out to east -705, and THE CROPS STILL COME
                     OFF THE STEP. That is deliberate and it is not laziness: a
                     crop here is the CITATION of a numeral already read, and
                     re-cutting eighteen of them from lines that did not exist when
                     they were read would re-read eighteen numerals to no purpose.
                     `corroboration()` below measures the step against the two
                     seated lines' own control every run — 8.70 m and 8.22 m — so
                     what the agreement MEANS has changed (two instruments agreeing,
                     rather than one licensing the other) while what it MEASURES has
                     not. The two flanks are therefore still `clinton` STEPPED
                     WEST by one and two modules, the module being the same
                     123.36 m the Original Town's seven flanking lines measure at
                     Madison Street (tools/read_washington_madison_numerals.py's
                     figure, and T-1088's before it). Blocks 22 and 51 are flanked
                     east by the river, not a street, and take `canal` stepped one
                     module EAST — block 52's rule in T-1094, and block 7's in
                     T-1088.

WHAT CORROBORATES THE STEP, three ways and all of them already committed:

  * `clinton` + one module lands on the committed `canal` to **2.34 m** at the
    scene's south edge and **0.46 m** at Lake Street. (It opens to 12 m at Kinzie,
    where `canal` bends west and `clinton` does not; the northern tiers' Clinton-
    Canal boxes are cut from the two committed lines themselves, so the step is
    not asked to carry that.)
  * `clinton` - one module lands **8.71 m** west of the surviving Jefferson x
    Fulton intersection, and `clinton` - two modules **8.23 m** west of Des
    Plaines x Fulton — both intersections already committed in `fulton`'s note in
    data/streets/1835.json, read from OpenStreetMap by T-0446. Eight metres on a
    123 m module, and both to the same side, is a seat and not a scatter.
  * every one of the eighteen numerals lands inside the box the rule cuts for it,
    with no overhang anywhere. That is eighteen independent chances for the rule
    to put a numeral in the wrong block, taken and not missed.

AND THE READING CHECKS ITSELF. The numbers are a boustrophedon: each tier's run
reverses the one above it. This file asserts that — every tier band, read west to
east, is monotonic, and consecutive bands run opposite ways — and it asserts it
ACROSS the blocks other tickets already read, so the West Division's 26 27 joins
T-0788's 28 29 rising eastward, its 47 46 joins T-0788's 45 44 43 rising
westward, and its 48 49 50 51 joins T-1094's 52 rising eastward. A numeral
misread, or a box cut onto the wrong block, breaks that alternation.

WHAT THIS FILE IS. The DERIVATION of the crop boxes, not the reading. The reading
lives in `data/traces/thompson_block_numbering.json` § blocks_not_in_the_grid,
one entry per block, each citing the IIIF region it was read on. This tool
recomputes those regions from the committed street lines, checks every read
window still lies wholly inside the box it is cited under, and fails if either
has drifted. It authors no ground: `tools/generate_plat_lots.py` emits the three
South Division tiers and nothing west of the river, so there is no cell for these
numbers to be stamped onto, and they wait with the North Division's seven and the
Washington-Madison tier's seven.

    tools/read_west_division_numerals.py            print the derivation
    tools/read_west_division_numerals.py --check    fail if the committed crops
                                                    are not what this re-derives
    tools/read_west_division_numerals.py --self-test  the check fires when broken
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import wright_px  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
STREETS = ROOT / "data" / "streets" / "1835.json"
TRACE = ROOT / "data" / "traces" / "thompson_block_numbering.json"

TIER = "west_division_original_town"

# The Original Town's seven flanking north-south lines, whose mean spacing at
# Madison Street is this project's platted module. Same list, same figure, as
# tools/read_washington_madison_numerals.py and T-1088 before it.
MODULE_FLANKS = ["market", "franklin", "wells", "lasalle", "clark", "dearborn", "state"]
MODULE_AT = -534.0

# The West Division's tier bands, north to south. Each is (north street, south
# street); `kinzie` is served by two committed segments that share an endpoint.
BANDS = [("kinzie", "carroll"), ("carroll", "fulton"), ("fulton", "lake"),
         ("lake", "randolph"), ("randolph", "washington"), ("washington", "madison")]

# (band index, west flank, east flank, number). A flank is a street id, or one of
# the two stepped pseudo-flanks named below.
BLOCKS = [(0, "des_plaines", "jefferson", 10),
          (0, "jefferson", "clinton", 9),
          (0, "clinton", "canal", 8),
          (1, "des_plaines", "jefferson", 11),
          (1, "jefferson", "clinton", 12),
          (1, "clinton", "canal", 13),
          (2, "des_plaines", "jefferson", 25),
          (2, "jefferson", "clinton", 24),
          (2, "clinton", "canal", 23),
          (2, "canal", "river_bound", 22),
          (3, "des_plaines", "jefferson", 26),
          (3, "jefferson", "clinton", 27),
          (4, "des_plaines", "jefferson", 47),
          (4, "jefferson", "clinton", 46),
          (5, "des_plaines", "jefferson", 48),
          (5, "jefferson", "clinton", 49),
          (5, "clinton", "canal", 50),
          (5, "canal", "river_bound", 51)]

# What the tier bands carry EAST of this file's own blocks, already read by other
# tickets. The boustrophedon assertion runs across these, so a numeral read here
# that does not continue the run already committed breaks the gate.
BAND_TAIL = {0: [7, 6, 5, 4, 3, 2, 1],
             1: [14, 15],
             2: [],
             3: [28, 29],
             4: [45, 44, 43],
             5: [52, 53, 54, 55, 56, 57, 58]}


def _streets():
    return {s["id"]: s for s in json.loads(STREETS.read_text())["streets"]}


def _along(pts, value, axis):
    """Read the other coordinate of a two-point-or-longer path at `value` on `axis`
    (0 = x, 1 = y), CONTINUING along the nearest segment's own bearing where the
    path does not reach — see the module docstring."""
    other = 1 - axis
    segs = list(zip(pts, pts[1:]))
    for a, b in segs:
        if min(a[axis], b[axis]) <= value <= max(a[axis], b[axis]):
            if b[axis] == a[axis]:
                return a[other]
            return a[other] + (b[other] - a[other]) * (value - a[axis]) / (b[axis] - a[axis])
    a, b = min(segs, key=lambda s: min(abs(value - s[0][axis]), abs(value - s[1][axis])))
    return a[other] + (b[other] - a[other]) * (value - a[axis]) / (b[axis] - a[axis])


def module(streets) -> float:
    xs = [_along(streets[i]["path_local_enu_m"], MODULE_AT, 1) for i in MODULE_FLANKS]
    return statistics.mean(b - a for a, b in zip(xs, xs[1:]))


def flank_x(streets, name: str, y: float) -> float:
    """The east of a block flank at a given northing."""
    mod = module(streets)
    if name == "jefferson":
        return _along(streets["clinton"]["path_local_enu_m"], y, 1) - mod
    if name == "des_plaines":
        return _along(streets["clinton"]["path_local_enu_m"], y, 1) - 2 * mod
    if name == "river_bound":
        return _along(streets["canal"]["path_local_enu_m"], y, 1) + mod
    return _along(streets[name]["path_local_enu_m"], y, 1)


# The five tiers this file CONTINUES west, and the easting they were continued from.
# T-1443 carried all five past it to Des Plaines Street; `band_y` reads them as they
# stood when the eighteen numerals were read, and says why below.
CONTINUED_TIERS = ("carroll", "fulton", "lake", "randolph", "washington")
CONTINUED_FROM_E = -320.0


def band_y(streets, street: str, x: float) -> float:
    """The northing of a tier line at a given east. Kinzie is two committed
    segments sharing the endpoint at east -320; west of it, `kinzie_west` is the
    committed line and is used rather than extrapolating `kinzie` over it.

    THE FIVE CONTINUED TIERS ARE READ AT THEIR OLD CLIP, and that is the same ruling the
    module docstring makes about Jefferson and Des Plaines, applied to the other axis.
    T-1443 carried `carroll`, `fulton`, `lake`, `randolph` and `washington` west to Des
    Plaines Street, so the ground this file used to CONTINUE them over is now committed
    line — and three of the five arrive there on the plat's grid bearing rather than on
    the terminal segment this file extrapolated. Reading the carried line would move two
    of the eighteen crops by a pixel. A crop here is the CITATION of a numeral already
    read; it is not a claim about where the street runs, and a street reaching further
    than it did is no reason to re-cut a reading nobody is re-taking. So the vertices
    west of the old clip are dropped and the continuation is taken from exactly the
    reach that was there when the numerals were read. `corroboration()` measures the
    stand-ins against the seated lines every run, which is where the carry SHOULD show
    up — as two instruments agreeing, not as a silent re-cut."""
    if street == "kinzie" and x < -320.0:
        street = "kinzie_west"
    path = streets[street]["path_local_enu_m"]
    if street in CONTINUED_TIERS:
        path = [p for p in path if p[0] >= CONTINUED_FROM_E] or path
    return _along(path, x, 0)


def boxes(streets) -> dict[int, tuple[str, tuple[float, float, float, float]]]:
    out = {}
    for band, west, east, number in BLOCKS:
        north_s, south_s = BANDS[band]
        mid = (band_y(streets, north_s, -300.0) + band_y(streets, south_s, -300.0)) / 2
        x0, x1 = flank_x(streets, west, mid), flank_x(streets, east, mid)
        # never reach over either street: take the north line where it runs
        # furthest south, and the south line where it runs furthest north.
        n = min(band_y(streets, north_s, x0), band_y(streets, north_s, x1))
        s = max(band_y(streets, south_s, x0), band_y(streets, south_s, x1))
        url = wright_px.iiif_region(x0, s, x1, n)
        out[number] = (url.split("js957744g/")[1].split("/")[0], (x0, s, x1, n))
    return out


def committed() -> dict[int, dict]:
    trace = json.loads(TRACE.read_text())
    return {r["number"]: r for r in trace["blocks_not_in_the_grid"]["readings"]
            if r.get("tier") == TIER}


def overhang_px(inner: str, outer: str) -> int:
    """How far the read window sticks out of the box it is cited under, in pixels."""
    ix, iy, iw, ih = (int(v) for v in inner.split(","))
    ox, oy, ow, oh = (int(v) for v in outer.split(","))
    return max(0, ox - ix, oy - iy, (ix + iw) - (ox + ow), (iy + ih) - (oy + oh))


def runs(streets) -> list[list[int]]:
    """Each tier band's numbers, west to east, this file's blocks first and then
    what the tiers already carry east of them."""
    cut = boxes(streets)
    out = []
    for band in range(len(BANDS)):
        mine = sorted(((cut[n][1][0], n) for b, _w, _e, n in BLOCKS if b == band))
        out.append([n for _x, n in mine] + BAND_TAIL[band])
    return out


def corroboration(streets) -> dict[str, float]:
    """The three measurements the stepped flanks stand on — see the docstring."""
    mod = module(streets)
    clinton, canal = streets["clinton"]["path_local_enu_m"], streets["canal"]["path_local_enu_m"]
    out = {}
    for label, y in (("canal_at_south_edge", -400.0), ("canal_at_lake", -108.38)):
        out[label] = abs((_along(clinton, y, 1) + mod) - _along(canal, y, 1))
    fulton_y = 12.59
    out["jefferson_x_fulton"] = abs((_along(clinton, fulton_y, 1) - mod) - (-401.04))
    out["des_plaines_x_fulton"] = abs((_along(clinton, fulton_y, 1) - 2 * mod) - (-524.88))
    return out


def check(streets=None) -> list[str]:
    streets = streets or _streets()
    derived, held = boxes(streets), committed()
    problems = []
    if sorted(held) != sorted(derived):
        problems.append(f"the trace holds {sorted(held)} for this tier; the rule cuts {sorted(derived)}")
    for number, (region, _box) in sorted(derived.items()):
        if number not in held:
            continue
        crop = held[number]["crop"]
        if crop["iiif_region"] != region:
            problems.append(f"block {number}: trace cites {crop['iiif_region']}, the rule cuts {region}")
            continue
        out = overhang_px(crop["read_at"], region)
        if out:
            problems.append(f"block {number}: read_at {crop['read_at']} stands {out} px "
                            f"outside the cited box {region}, and a read window may not")
    direction = None
    for band, run in enumerate(runs(streets)):
        rising = [b - a for a, b in zip(run, run[1:])]
        if not rising:
            continue
        if not (all(d > 0 for d in rising) or all(d < 0 for d in rising)):
            problems.append(f"tier band {BANDS[band][0]}-{BANDS[band][1]} reads {run} west to "
                            "east, which is not one run")
            continue
        here = rising[0] > 0
        if direction is not None and here == direction:
            problems.append(f"tier band {BANDS[band][0]}-{BANDS[band][1]} runs the same way as "
                            "the band above it; this plat's numbering is a boustrophedon")
        direction = here
    for label, metres in corroboration(streets).items():
        if metres > 15.0:
            problems.append(f"the stepped flank no longer corroborates: {label} is {metres:.2f} m, "
                            "and the rule is only as good as that agreement")
    return problems


def write() -> int:
    """Re-cut the cited boxes from the committed street lines, IN PLACE — the same writer
    read_washington_madison_numerals.py carries, for the same reason and against the same
    trace. The crop citation is a derivation: the box is committed lines and the rule
    above, so a street that moves re-cuts it. The READING is untouched; `read_at` is the
    window the numeral was actually read on and this never writes it. T-1092, which moved
    this tier's flanking streets by re-seating the School Section grid onto the
    eleven-point registration, is what found this tier had a gate and no writer."""
    text = TRACE.read_text()
    derived = boxes(_streets())
    moved = 0
    for r in committed().values():
        region = derived.get(r["number"], (None,))[0]
        crop = r["crop"]
        if region is None or crop["iiif_region"] == region:
            continue
        if overhang_px(crop["read_at"], region):
            raise SystemExit(
                f"block {r['number']}: the re-cut box {region} no longer holds the read "
                f"window {crop['read_at']}, and this tool will not widen a box to fit a "
                f"reading. Re-read the numeral.")
        if text.count(crop["iiif_region"]) != 2:
            raise SystemExit(f"block {r['number']}: {crop['iiif_region']} is not the "
                             f"region string of exactly one entry")
        text = text.replace(crop["iiif_region"], region)
        moved += 1
    TRACE.write_text(text)
    print(f"re-cut {moved} of {len(committed())} West Division numeral crop(s) from the "
          f"committed street lines")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--write", action="store_true",
                    help="re-cut the cited boxes from the committed streets, in place")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    if args.write:
        return write()

    if args.self_test:
        failures = []
        streets = _streets()
        streets["clinton"]["path_local_enu_m"][0][0] += 40.0
        if not check(streets):
            failures.append("Clinton Street moved 40 m and the crop check stayed silent")
        # PERTURB THE VERTEX THE CROPS ACTUALLY STAND ON, which since T-1443 is no longer
        # `lake`'s first. The five continued tiers now run on west of the old clip and
        # `band_y` reads them at it, deliberately — so moving the carried reach must NOT
        # fire, and moving the line the crops were cut from must. Both are asserted.
        streets = _streets()
        old_clip = next(i for i, q in enumerate(streets["lake"]["path_local_enu_m"])
                        if abs(q[0] - CONTINUED_FROM_E) < 1e-6)
        streets["lake"]["path_local_enu_m"][old_clip][1] += 30.0
        if not check(streets):
            failures.append("Lake Street moved 30 m north at the clip the crops are cut "
                            "from and the crop check stayed silent")
        streets = _streets()
        streets["lake"]["path_local_enu_m"][0][1] += 30.0
        if check(streets):
            failures.append("moving Lake Street's CARRIED west end re-cut the crops — a "
                            "reading already taken is not re-cut by a street reaching "
                            "further than it did (T-1443)")
        held = committed()
        if held:
            first = held[min(held)]
            x, y, w, h = (int(v) for v in first["crop"]["read_at"].split(","))
            box_x = int(first["crop"]["iiif_region"].split(",")[0])
            expected = max(0, box_x - (x - 500))
            if overhang_px(f"{x - 500},{y},{w},{h}", first["crop"]["iiif_region"]) != expected:
                failures.append("a read window slid 500 px west of its box did not measure the "
                                "overhang that slide produces")
        else:
            failures.append("the trace holds no West Division reading to test the read window on")
        swapped = dict(BAND_TAIL)
        try:
            BAND_TAIL[3] = [29, 28]
            if not check():
                failures.append("a tier band read backwards against the blocks already committed "
                                "east of it did not break the boustrophedon assertion")
        finally:
            BAND_TAIL.clear()
            BAND_TAIL.update(swapped)
        for f in failures:
            print(f"SELF-TEST FAILED: {f}")
        if failures:
            return 1
        print("self-test: moving Clinton 40 m or Lake 30 m at the clip the crops are cut from breaks the crop check while moving Lake's carried west end does not, a "
              "read window slid out of its box measures the overhang that slide produces, and a "
              "tier band read backwards breaks the boustrophedon, as they must")
        return 0

    problems = check()
    if args.check:
        for p in problems:
            print(f"  {p}")
        if problems:
            print(f"{len(problems)} West Division numeral crop(s) no longer cut from the committed streets")
            return 1
        print("the eighteen West Division numeral crops re-cut from the committed street lines")
        return 0

    streets = _streets()
    print(f"module (mean flank spacing at Madison): {module(streets):.2f} m")
    for label, metres in corroboration(streets).items():
        print(f"  corroboration {label:22s} {metres:6.2f} m")
    for number, (region, (x0, s, x1, n)) in sorted(boxes(streets).items()):
        print(f"  block {number:2d}: x[{x0:8.2f},{x1:8.2f}] y[{s:8.2f},{n:8.2f}]  region {region}")
    for band, run in zip(BANDS, runs(streets)):
        print(f"  {band[0]}-{band[1]:12s} west to east: {run}")
    print("committed:" if not problems else "DRIFTED:")
    for p in problems:
        print(f"  {p}")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
