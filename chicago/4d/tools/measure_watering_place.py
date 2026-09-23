#!/usr/bin/env python3
"""Andreas says the watermen drove into the lake. Where, on this model's own
surfaces, could a cart actually do that?

T-0886. `data/yard/town_water_cart.json` stands one water cart at the foot of
Randolph Street because that is the only place Andreas's sentence names, and the
record's `the_water_is_not_the_lake` block then reports a contradiction it
refuses to settle: the water at that point is the old southward channel behind
the sand bar, and the open lake is a quarter of a kilometre further east across
dry sand. Three readings were left open and nothing measured any of them.

    tools/measure_watering_place.py             print the readings
    tools/measure_watering_place.py --gate      exit 1 if the ruling has rotted
    tools/measure_watering_place.py --self-test the classifier, on a made profile

WHAT THIS FILE ADDED TO THE QUESTION is the fourth reading, and it is a distance
rather than a date: the bar the carts would have had to cross is a traced island
with a traced SOUTH END, and from the foot of Randolph that end is a short walk
along the same bank. So Andreas's *"generally at the foot of Randolph Street"* —
a word that concedes a stretch and not a point — reaches open lake water without
a ford, without dating the channel, and without moving the cart off the one place
the source names. The ruling is argued in `docs/RESEARCH/wells.md` § 5; this file
is the measurement it rests on, and the gate is what stops that measurement going
quietly out of date when the terrain is next re-carved.

FOUR READINGS, and each is a way the ruling can be wrong:

 1. THE CART STANDS AT WATER. The committed heightfield at the cart's own point
    must be below the epoch's water surface. If a re-carve moves the waterline
    east, the cart is parked on dry sand and the whole record is about nothing.
 2. THE CONTRADICTION IS STILL TRUE. East along Randolph's extended centreline
    the field must give water, then a DRY run — the bar — then water again. That
    ordering is the contradiction the record reports; if the bar ever drowns, the
    water at Randolph's foot IS the lake and the ruling is not needed.
 3. THE WAY ROUND EXISTS AND IS SHORT. The traced sand bar must end SOUTH of the
    foot of Randolph and NORTH of the trace's own southern limit — a terminus the
    trace draws rather than one the window cuts — and the walk to it along the
    committed south shore must be under `MAX_WALK_M`. That walk is the number the
    ruling rests on and the one a re-trace could move.
 4. THE PROSE QUOTES THE MEASUREMENT. The cart record's own block must name the
    adopted reading and carry this walk, to the metre printed here. Two files, one
    number, and nothing but this check holding them together.

No number about 1835 is stated in this file. The cart, the street, the bar and
the shore are all read out of the committed record.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
sys.path.insert(0, str(ROOT / "tools"))
from heightfield import Heightfield  # noqa: E402

EPOCH_DIR = DATA / "terrain" / "epochs" / "e1834_harbor_cut"
CART_PATH = DATA / "yard" / "town_water_cart.json"
STREETS_PATH = DATA / "streets" / "1835.json"
DATUM_PATH = DATA / "datum.json"
SHORELINE_PATH = EPOCH_DIR / "shoreline.geojson"

STREET_ID = "randolph"

# The transect step. Finer than the 2.5 m grid on purpose, for the reason
# measure_slough_crossing.py gives: the field is sampled bilinearly by the walker
# and by the renderer, so the waterline sits between cells and a grid-step reading
# would round an 80 m channel to the nearest 2.5 m.
STEP_M = 0.25
# A run shorter than this is sampling noise at a waterline, not a feature. The bar
# is 160 m of dry ground on this transect and the channel 80 m of water, so the
# threshold is nowhere near either; it is here so a single cell straddling z = 0
# cannot be read as a fourth shore.
MIN_RUN_M = 5.0
# The walk the ruling rests on: from the foot of Randolph south along the committed
# bank to the latitude of the bar's traced south tip. Set at a quarter of a
# kilometre because that is the distance ACROSS the bar on the transect, the
# obstacle the walk exists to avoid — a way round that is longer than the way
# through is not a way round, and the ruling would have to be re-argued.
MAX_WALK_M = 250.0
# The prose and the measurement agree to the metre or one of them was hand-edited.
QUOTE_TOL_M = 0.5
# The reading adopted in docs/RESEARCH/wells.md § 5. The gate looks for this string
# in the record so a later run cannot quietly adopt a different one in one file.
ADOPTED_READING = "the_phrase_names_a_stretch"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def street_bearing(streets: dict, street_id: str):
    """The unit vector of the street's last committed segment, and its east end."""
    rows = streets["streets"] if isinstance(streets, dict) else streets
    row = next(r for r in rows if r.get("id") == street_id)
    path = [(float(e), float(n)) for e, n in row["path_local_enu_m"]]
    (e0, n0), (e1, n1) = path[-2], path[-1]
    length = math.hypot(e1 - e0, n1 - n0)
    return (e1, n1), ((e1 - e0) / length, (n1 - n0) / length)


def runs_along(hf: Heightfield, start, unit, water_m: float, step: float = STEP_M):
    """Classify the field east along a bearing into wet and dry runs.

    Returns [(wet, from_m, to_m, min_h, max_h)] in metres from `start`, with runs
    shorter than MIN_RUN_M folded into their neighbour rather than reported: a
    waterline is a crossing, not a feature.
    """
    (e0, n0), (ue, un) = start, unit
    raw = []
    t = 0.0
    while True:
        e, n = e0 + ue * t, n0 + un * t
        if not hf.covers(e, n):
            break
        h = hf.height(e, n)
        wet = h < water_m
        if raw and raw[-1][0] == wet:
            raw[-1][2] = t
            raw[-1][3] = min(raw[-1][3], h)
            raw[-1][4] = max(raw[-1][4], h)
        else:
            raw.append([wet, t, t, h, h])
        t += step
    out = []
    for run in raw:
        if out and (run[2] - run[1]) < MIN_RUN_M:
            out[-1][2] = run[2]
            out[-1][3] = min(out[-1][3], run[3])
            out[-1][4] = max(out[-1][4], run[4])
        elif out and out[-1][0] == run[0]:
            out[-1][2] = run[2]
            out[-1][3] = min(out[-1][3], run[3])
            out[-1][4] = max(out[-1][4], run[4])
        else:
            out.append(list(run))
    return [tuple(r) for r in out]


def local(datum: dict, coords):
    oe, on = float(datum["origin_utm_e"]), float(datum["origin_utm_n"])
    return [(float(x) - oe, float(y) - on) for x, y in coords]


def shoreline_parts(datum: dict):
    """The traced bar's outline and the traced south shore, in local ENU metres.

    Picked by geometry rather than by a name match: the bar is the only polygon
    the water polygon does not contain, and the south shore is the LineString whose
    `name` the file itself begins with "South shore". A regex over a prose note is
    the class of bug the terrain dating file warns about, so the polygon is chosen
    by extent and the line by its own declared name field.
    """
    gj = load(SHORELINE_PATH)
    polys, lines = [], []
    for feat in gj["features"]:
        geom, props = feat["geometry"], feat.get("properties", {})
        if geom["type"] == "Polygon":
            polys.append((props, local(datum, geom["coordinates"][0])))
        elif geom["type"] == "LineString":
            lines.append((props, local(datum, geom["coordinates"])))
    # The water body is the polygon of greatest extent; the bar is the other one.
    if len(polys) != 2:
        raise SystemExit(f"shoreline.geojson: expected two polygons, the water and the bar; got {len(polys)}")
    polys.sort(key=lambda p: max(x for x, _ in p[1]) - min(x for x, _ in p[1]))
    bar, water = polys[0][1], polys[-1][1]
    south = next(ln for props, ln in lines if str(props.get("name", "")).startswith("South shore"))
    return bar, south, water


def walk_south(shore, foot, target_n: float):
    """Metres along the committed shore from `foot` south to latitude `target_n`.

    The shore is a traced polyline that runs west-to-east down the main stem and
    then SOUTH behind the bar, so the walk is measured along it rather than as a
    straight line — which is what a cart on a bank would do.
    """
    cum = [0.0]
    for i in range(1, len(shore)):
        cum.append(cum[-1] + math.hypot(shore[i][0] - shore[i - 1][0], shore[i][1] - shore[i - 1][1]))
    # Where the foot of Randolph meets the line: the nearest vertex, plus the
    # offset from it, so an 18 m gap between a derived point and a traced vertex
    # is carried rather than rounded away.
    dists = [(math.hypot(x - foot[0], y - foot[1]), i) for i, (x, y) in enumerate(shore)]
    foot_gap, foot_i = min(dists)
    crossings = []
    for i in range(1, len(shore)):
        y0, y1 = shore[i - 1][1], shore[i][1]
        if (y0 - target_n) * (y1 - target_n) < 0:
            t = (target_n - y0) / (y1 - y0)
            crossings.append((cum[i - 1] + t * (cum[i] - cum[i - 1]),
                              shore[i - 1][0] + t * (shore[i][0] - shore[i - 1][0])))
    if not crossings:
        return None
    # The crossing nearest the foot along the line — the shore doubles back around
    # the reservation, and the walk a cart takes is the short way.
    walk, east = min(crossings, key=lambda c: abs(c[0] - cum[foot_i]))
    return {"walk_m": abs(walk - cum[foot_i]), "shore_east_m": east,
            "foot_gap_m": foot_gap, "shore_length_m": cum[-1]}


def read(quiet: bool = False):
    hf = Heightfield.load(EPOCH_DIR)
    if hf is None:
        raise SystemExit("no committed heightfield for e1834_harbor_cut")
    meta = load(EPOCH_DIR / "heightfield.json")
    water_m = float(meta.get("water_surface_m", 0.0))
    datum = load(DATUM_PATH)
    cart = load(CART_PATH)
    place = cart["the_place"]["at_local_enu_m"]
    end, unit = street_bearing(load(STREETS_PATH), STREET_ID)

    profile = runs_along(hf, end, unit, water_m)
    wet = [r for r in profile if r[0]]
    dry = [r for r in profile if not r[0]]
    bar_outline, south_shore, _water = shoreline_parts(datum)
    bar_south_n = min(y for _, y in bar_outline)
    bar_south_e = min(x for x, y in bar_outline if abs(y - bar_south_n) < 1e-6)
    bar_north_n = max(y for _, y in bar_outline)
    trace_south_n = min(y for _, y in south_shore)
    way = walk_south(south_shore, (place[0], place[1]), bar_south_n)

    r = {
        "water_surface_m": water_m,
        "cart_at": place,
        "cart_height_m": hf.height(place[0], place[1]),
        "transect_from": end,
        "profile": profile,
        "channel": wet[0] if wet else None,
        "bar_on_transect": dry[1] if len(dry) > 1 else None,
        "lake_on_transect": wet[1] if len(wet) > 1 else None,
        "bar_south_n": bar_south_n,
        "bar_south_e": bar_south_e,
        "bar_north_n": bar_north_n,
        "trace_south_limit_n": trace_south_n,
        "box_south_n": float(meta["box_local_enu_m"]["n"][0]),
        "way_round": way,
        "block": cart.get("the_water_is_not_the_lake", {}),
    }
    if not quiet:
        print("THE WATERING PLACE AT THE FOOT OF RANDOLPH STREET — T-0886\n")
        print(f"  the cart stands at east {place[0]:.1f} north {place[1]:.1f}, "
              f"where the committed field is {r['cart_height_m']:+.2f} m "
              f"(water surface {water_m:+.2f} m)\n")
        print("  1 · EAST ALONG RANDOLPH'S OWN BEARING, from its last committed vertex")
        for w, a, b, mn, mx in profile:
            print(f"      {'water' if w else 'LAND ':<5}  east {end[0]+a:8.1f} .. {end[0]+b:8.1f}"
                  f"   {b-a:7.1f} m   {mn:+.2f} .. {mx:+.2f} m")
        if r["channel"] and r["bar_on_transect"]:
            print(f"\n  2 · THE FORD: {r['channel'][2]-r['channel'][1]:.1f} m of water, "
                  f"{-r['channel'][3]:.2f} m at its deepest, then "
                  f"{r['bar_on_transect'][2]-r['bar_on_transect'][1]:.1f} m of dry bar "
                  f"standing to {r['bar_on_transect'][4]:+.2f} m, before the lake.")
        if way:
            print(f"\n  3 · THE WAY ROUND: the traced bar ends at north {bar_south_n:.1f} "
                  f"(east {bar_south_e:.1f}), {abs(bar_south_n - place[1]):.1f} m south of the cart.")
            print(f"      Along the committed south shore that is a walk of {way['walk_m']:.1f} m, "
                  f"reaching the bank at east {way['shore_east_m']:.1f}.")
            print(f"      The trace runs on to north {trace_south_n:.1f}, so the bar's end is "
                  f"drawn and not cut by the window.")
        print(f"\n  4 · NOT MEASURABLE HERE: the heightfield's box stops at north "
              f"{r['box_south_n']:.0f}, north of the bar's end, so the ground and the depth at "
              f"the way round are traced but not modelled. Stated, not estimated.")
    return r


def gate(quiet: bool = False) -> int:
    r = read(quiet=quiet)
    bad = []
    if r["cart_height_m"] >= r["water_surface_m"]:
        bad.append(f"1 · the cart stands on dry ground ({r['cart_height_m']:+.2f} m): "
                   "the waterline has moved and the record is about nothing")
    if not (r["channel"] and r["bar_on_transect"] and r["lake_on_transect"]):
        bad.append("2 · the transect no longer gives water, then dry bar, then water — "
                   "the contradiction the cart record reports is not what the field says")
    if r["way_round"] is None:
        bad.append("3 · the committed south shore never reaches the latitude of the bar's end")
    else:
        walk = r["way_round"]["walk_m"]
        if walk > MAX_WALK_M:
            bad.append(f"3 · the way round is {walk:.1f} m, over the {MAX_WALK_M:.0f} m ceiling")
        if r["bar_south_n"] >= r["cart_at"][1]:
            bad.append("3 · the bar's traced end is not south of the cart")
        if r["bar_south_n"] <= r["trace_south_limit_n"]:
            bad.append("3 · the bar's end sits at the trace's own southern limit — it is cut "
                       "by the window, not drawn, and the way round is not evidence")
        block = r["block"]
        if block.get("ruling", {}).get("reading") != ADOPTED_READING:
            bad.append(f"4 · town_water_cart.json's the_water_is_not_the_lake block does not "
                       f"adopt `{ADOPTED_READING}`")
        quoted = block.get("ruling", {}).get("way_round_m")
        if quoted is None or abs(float(quoted) - walk) > QUOTE_TOL_M:
            bad.append(f"4 · the record quotes way_round_m {quoted} against a measured "
                       f"{walk:.1f} m")
    if bad:
        print("\nTHE WATERING PLACE RULING HAS ROTTED:", file=sys.stderr)
        for b in bad:
            print(f"  - {b}", file=sys.stderr)
        return 1
    if not quiet:
        print("\n  the ruling stands on what the committed surfaces still say.")
    return 0


def self_test() -> int:
    """The classifier, on a profile with a known shape and a one-cell wobble in it."""
    class Fake:
        def covers(self, e, n):
            return e <= 100.0
        def height(self, e, n):
            if e < 20.0:
                return 1.0
            if e < 20.5:          # a single sample straddling the waterline
                return -0.01
            if e < 21.0:
                return 1.0
            if e < 60.0:
                return -1.0
            if e < 80.0:
                return 0.5
            return -2.0
    runs = runs_along(Fake(), (0.0, 0.0), (1.0, 0.0), 0.0)
    shape = [(w, round(a), round(b)) for w, a, b, _, _ in runs]
    want = [(False, 0, 21), (True, 21, 60), (False, 60, 80), (True, 80, 100)]
    if shape != want:
        print(f"self-test FAILED: {shape} != {want}", file=sys.stderr)
        return 1
    print("self-test ok: the wobble at the waterline is folded, the four runs survive")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--gate", action="store_true", help="exit 1 if the ruling has rotted")
    ap.add_argument("--self-test", action="store_true", help="check the run classifier")
    ap.add_argument("--quiet", action="store_true", help="print only failures")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if a.gate:
        return gate(quiet=a.quiet)
    read()
    return 0


if __name__ == "__main__":
    sys.exit(main())
