#!/usr/bin/env python3
"""Does the Slough Log Bridge span open water, or does it span solid ground?

T-0109. The question is the ticket's title and it was a real fault for two
months: the crossing stood at its attested place on Water Street with the South
Division's drain unmodelled beneath it, so a visitor walked a timber deck laid
over prairie. `data/structures/slough_log_bridge.json` said so in its own words,
`docs/LIBERTIES.md` L69 said so, and nothing measured it.

    tools/measure_slough_crossing.py          print the readings
    tools/measure_slough_crossing.py --gate   exit 1 if the crossing spans dry ground

THE CUT LANDED WITHOUT THIS GATE AND THAT IS THE POINT. T-0005 carved zone 14
into the terrain epoch (changelog v204) and T-0118 straightened its last reach
under this very deck (v210) — both AFTER T-0109 was filed, neither aimed at it,
and no check anywhere would have noticed if the channel had come back a metre
west and left the deck over dry bank again. A terrain spec is a stack of swale
entries with hand-written lines and half-widths, and a bridge is a placement in
a different file; nothing but this reading joins them.

WHAT IS ASSERTED, and each one is a way the crossing can be wrong:

 1. OPEN WATER UNDER THE DECK. Along the deck's own span, the committed
    heightfield must fall below the epoch's water surface in one continuous run.
    A run of less than `MIN_OPEN_WATER_M` is a damp swale, not a stream a town
    would bridge, and this is the assertion that fails if the channel moves out
    from under the deck.
 2. THE ABUTMENTS STAND ON BANK. That run must not reach either end of the span:
    a log crossing lands on dry ground at both ends, and a deck whose ends are in
    the water is a raft. `MIN_BANK_SEAT_M` is the seat each end must keep.
 3. THE DRAIN REACHES THE RIVER. From the deck to the watercourse's mouth, every
    sample along the spec's own centreline must be below the water surface —
    otherwise the crossing spans a puddle rather than a watercourse, which is the
    same fault wearing a different face. Upstream is NOT asserted: the record
    reads the July drain above its backed-up pool as a damp swale standing above
    the water, so a dry reading there is the claim and not a failure.
 4. THE RECORD'S CLEARANCE IS THE SCENE'S. `clearance_m` is the one flatly
    conjectural dimension on the crossing, and the deck it describes is built
    from `walk_surface_m` less the stringer and the plank. Those three numbers
    live in three places and nothing held them together.
 5. NOTHING ELSE STANDS IN THE CUT. Inside the crossing's reach, anything rooted
    on ground below the water surface must either BE the crossing or declare that
    it rides it (`rides`), the way the river walk's crossing footway does.

The deck is not described here. Its span, its width, its bearing and its
clearance are read out of the committed record, so this file holds one number
about 1835 and it is zero: everything else is the dataset's own.
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

SCENE = "1835"

# THE CROSSINGS THIS FILE READS. It measured one until 2026-08-24 and the module
# names still say so; T-0129 built a second crossing over the second of the three
# Main Branch sloughs, whose record and whose liberty both promise these same
# readings, and a near-identical second file would have been two gates to keep in
# step instead of one. Each entry is a committed bridge record and the swale entry
# whose water it is supposed to span — nothing else about a crossing is stated
# here, because everything else is read out of the records themselves.
# `downstream` is which way the river is FROM THE DECK, and it has to be stated because
# assertion 3 walks only the reach below the crossing. Both South Division drains run
# NORTH into the main stem; T-0254's crossing is on the other bank and its slough runs
# SOUTH into the same river. Reading the direction off the geometry would have meant
# guessing which end of a centreline is the mouth, which is a record's business.
CROSSINGS = [
    {"bridge": "slough_log_bridge", "watercourse": "state_slough_mouth",
     "downstream": "north",
     "label": "The Slough Log Bridge, Water Street"},
    {"bridge": "lasalle_slough_crossing", "watercourse": "lasalle_slough_lower",
     "downstream": "north",
     "label": "The La Salle Slough Crossing, South Water Street"},
    {"bridge": "north_water_slough_crossing", "watercourse": "north_side_slough",
     "downstream": "south",
     "label": "The North Water Street Slough Crossing"},
]

# The step the transects are read at. Finer than the 2.5 m grid on purpose: the
# field is sampled bilinearly by the walker and by the renderer, so the waterline
# sits between samples and a grid-step reading would round a 3 m stream to one
# cell or to none.
STEP_M = 0.05

# A stream a town builds and maintains a timber crossing over, rather than a wet
# patch it walks through. One metre is deliberately far below anything the
# hydrology dossier reads for zone 14 (15-40 ft) — the gate is here to catch the
# channel LEAVING, not to re-argue its width, and a threshold set near the built
# figure would fail on any honest re-carve.
MIN_OPEN_WATER_M = 1.0
# The dry seat each abutment keeps. Half a metre is one course of log; below that
# the end of the deck is standing in the stream whatever the record says.
MIN_BANK_SEAT_M = 0.5
# Deck thickness against the record's own clearance: the two are computed from
# the same three attributes, so they agree exactly or one of them was hand-edited.
CLEARANCE_TOL_M = 0.01
# The crossing's reach — how far the census for assertion 5 looks. Forty metres
# either way covers the graded approaches, the backed-up pool the deck sits over
# and the run down to the river, which is the whole of what a visitor takes in
# standing on the planks.
REACH_M = 40.0


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def course_line(course: dict, epoch_dir: Path):
    """The watercourse's centreline in local ENU metres, or None.

    A `swales` entry states its own `line` in local metres. A `watercourses` entry
    states `from: <file>` instead and the line lives in that file, in EPSG:26916 —
    T-0254's slough is the first crossing whose stream is one of those. Both are read
    here rather than in the caller so assertion 3 does not care which kind it got.
    """
    if course.get("line"):
        return [(float(p[0]), float(p[1])) for p in course["line"]]
    src = course.get("from")
    if not src or not (epoch_dir / src).exists():
        return None
    datum = load(DATA / "datum.json")
    oe, on = float(datum["origin_utm_e"]), float(datum["origin_utm_n"])
    doc = load(epoch_dir / src)
    for feature in doc.get("features", []):
        if feature.get("id") != course["id"]:
            continue
        geom = feature.get("geometry") or {}
        if geom.get("type") != "LineString":
            return None
        return [(float(e) - oe, float(n) - on) for e, n in geom["coordinates"]]
    return None


def deck_geometry(sidecar: dict) -> dict:
    """The deck's span axis, width axis and world extent, from the record.

    The footprint polygon IS the deck: its u extent is the span and its v extent
    the width, laid at `rotation_deg` about the placement. Read rather than
    restated so a moved or re-sized deck is measured where it now is.
    """
    place = sidecar["placement"]
    poly = [(float(p[0]), float(p[1])) for p in sidecar["footprint"]["polygon"]]
    us = [p[0] for p in poly]
    vs = [p[1] for p in poly]
    span = max(us) - min(us)
    width = max(vs) - min(vs)
    rot = math.radians(float(place.get("rotation_deg", 0.0)))
    cos_r, sin_r = math.cos(rot), math.sin(rot)

    def to_world(u: float, v: float) -> tuple[float, float]:
        return (float(place["local_e"]) + u * cos_r - v * sin_r,
                float(place["local_n"]) + u * sin_r + v * cos_r)

    return {
        "span_m": span,
        "width_m": width,
        "u0": min(us), "v_mid": 0.5 * (min(vs) + max(vs)),
        "to_world": to_world,
        "centre": to_world(0.5 * (min(us) + max(us)), 0.5 * (min(vs) + max(vs))),
    }


def longest_wet_run(samples: list[tuple[float, float]], water_y: float):
    """(start_along, end_along, deepest) of the longest below-water run, or None."""
    best = None
    run_start = None
    deepest = 0.0
    for along, y in samples + [(None, water_y + 1.0)]:
        if along is not None and y < water_y:
            if run_start is None:
                run_start, deepest = along, y
            deepest = min(deepest, y)
            last = along
            continue
        if run_start is not None:
            length = last - run_start
            if best is None or length > best[1] - best[0]:
                best = (run_start, last, deepest)
            run_start = None
    return best


def measure(crossing: dict) -> tuple[dict, list[str]]:
    BRIDGE = crossing["bridge"]
    WATERCOURSE = crossing["watercourse"]
    problems: list[str] = []
    rec = load(DATA / "structures" / f"{BRIDGE}.json")
    side = load(DATA / "sidecars" / SCENE / f"{BRIDGE}.json")
    epoch_dir = DATA / "terrain" / "epochs" / load(
        DATA / "scenes" / f"{SCENE}.json")["terrain_epoch"]
    hf = Heightfield.load(epoch_dir)
    if hf is None:
        return {}, [f"no committed heightfield in {epoch_dir.relative_to(ROOT)}"]
    water_y = float(hf.meta.get("water_surface_m", 0.0))
    deck = deck_geometry(side)

    # --- 1 and 2: the transect along the span ------------------------------
    n_steps = int(round(deck["span_m"] / STEP_M))
    transect = []
    for k in range(n_steps + 1):
        u = deck["u0"] + k * STEP_M
        e, n = deck["to_world"](u, deck["v_mid"])
        transect.append((k * STEP_M, hf.height(e, n)))
    run = longest_wet_run(transect, water_y)
    reading = {
        "span_m": round(deck["span_m"], 2),
        "deck_e": [round(deck["to_world"](deck["u0"], deck["v_mid"])[0], 2),
                   round(deck["to_world"](deck["u0"] + deck["span_m"],
                                          deck["v_mid"])[0], 2)],
        "water_surface_m": water_y,
        "open_water_m": round(run[1] - run[0], 2) if run else 0.0,
        "deepest_m": round(run[2], 3) if run else None,
        "west_seat_m": round(run[0], 2) if run else None,
        "east_seat_m": round(deck["span_m"] - run[1], 2) if run else None,
    }
    if run is None:
        problems.append(
            "the deck spans SOLID GROUND: no sample along its span is below the "
            f"{water_y:+.2f} m water surface. This is T-0109's fault, and the fix "
            "is the watercourse in data/terrain/epochs/*/terrain_spec.json, not "
            "this threshold.")
    else:
        if reading["open_water_m"] < MIN_OPEN_WATER_M:
            problems.append(
                f"the deck spans {reading['open_water_m']:.2f} m of open water, "
                f"under the {MIN_OPEN_WATER_M:.2f} m a bridged stream needs — a "
                f"damp swale, not a watercourse")
        for side_name, seat in (("west", reading["west_seat_m"]),
                                ("east", reading["east_seat_m"])):
            if seat < MIN_BANK_SEAT_M:
                problems.append(
                    f"the deck's {side_name} end keeps {seat:.2f} m of dry seat, "
                    f"under the {MIN_BANK_SEAT_M:.2f} m an abutment needs: that end "
                    f"stands in the stream")

    # --- 3: down the watercourse to the river ------------------------------
    spec = load(epoch_dir / "terrain_spec.json")
    course = next((s for s in spec.get("swales", []) + spec.get("watercourses", [])
                   if s.get("id") == WATERCOURSE), None)
    mouth = []
    if course is None:
        problems.append(f"the terrain spec carries no swale or watercourse "
                        f"'{WATERCOURSE}', so the reach from the crossing to the river "
                        f"cannot be walked")
    else:
        line = course_line(course, epoch_dir)
        if line is None:
            problems.append(f"'{WATERCOURSE}' states neither its own `line` nor a "
                            f"`from` file this tool can read, so its course cannot be "
                            f"walked")
            return reading, problems
        deck_n = deck["centre"][1]
        below = (lambda n: n < deck_n) if crossing["downstream"] == "north" \
            else (lambda n: n > deck_n)
        walked, dry = 0, []
        for i in range(len(line) - 1):
            (ae, an), (be, bn) = line[i], line[i + 1]
            length = math.hypot(be - ae, bn - an)
            for k in range(int(length / STEP_M) + 1):
                t = k * STEP_M / length
                e, n = ae + (be - ae) * t, an + (bn - an) * t
                if below(n):
                    continue          # upstream of the deck: not asserted, see the docstring
                walked += 1
                if hf.height(e, n) >= water_y:
                    dry.append((round(e, 2), round(n, 2)))
        mouth = dry
        reading["mouth_reach_samples"] = walked
        reading["mouth_reach_dry"] = len(dry)
        if dry:
            problems.append(
                f"the reach from the deck to the river is broken: {len(dry)} of "
                f"{walked} samples along '{WATERCOURSE}' stand above the water "
                f"surface, first at E {dry[0][0]} N {dry[0][1]}")

        # --- 3b: AND NOTHING DAMS IT ANYWHERE ALONG ITS LENGTH -------------
        # T-0129. Assertion 3 asks about the reach BELOW the deck, because a
        # drain's inland course is read here as a damp swale standing above the
        # water and a dry reading up there is the claim rather than a failure.
        # What that cannot catch is a bar of land sitting BETWEEN two pools —
        # dry cells with water on both sides of them — which is exactly what the
        # owner reported on 2026-08-21 at the La Salle drain: "this slough has
        # kind of a bulge of land... it would not have that and be a continous
        # water drain into the river". A watercourse may END. It may not be
        # INTERRUPTED, and the difference is what this clause reads.
        along = []
        for i in range(len(line) - 1):
            (ae, an), (be, bn) = line[i], line[i + 1]
            length = math.hypot(be - ae, bn - an)
            for k in range(int(length / STEP_M) + 1):
                t_ = k * STEP_M / length
                e, n = ae + (be - ae) * t_, an + (bn - an) * t_
                along.append((e, n, hf.height(e, n) < water_y))
        wet_ix = [i for i, s in enumerate(along) if s[2]]
        bars = []
        if wet_ix:
            run_start = None
            for i in range(wet_ix[0], wet_ix[-1] + 1):
                if not along[i][2]:
                    if run_start is None:
                        run_start = i
                elif run_start is not None:
                    bars.append((run_start, i - 1))
                    run_start = None
        reading["interruptions"] = len(bars)
        reading["longest_bar_m"] = (round(max(b[1] - b[0] + 1 for b in bars) * STEP_M, 2)
                                    if bars else 0.0)
        if bars:
            first = along[bars[0][0]]
            problems.append(
                f"'{WATERCOURSE}' is DAMMED: {len(bars)} bar(s) of dry ground sit "
                f"between two pools along its own centreline, the longest "
                f"{reading['longest_bar_m']:.2f} m, the first at E {first[0]:.1f} "
                f"N {first[1]:.1f}. A watercourse may end; it may not be interrupted")

    # --- 4: the record's own deck ------------------------------------------
    attrs = side["attributes"]
    thickness = float(attrs["stringer_d_m"]["value"]) + float(attrs["plank_t_m"]["value"])
    soffit = float(side["placement"]["walk_surface_m"]) - thickness
    stated = float(attrs["clearance_m"]["value"])
    reading["deck_walk_m"] = float(side["placement"]["walk_surface_m"])
    reading["deck_soffit_m"] = round(soffit, 3)
    reading["clearance_stated_m"] = stated
    if abs(soffit - water_y - stated) > CLEARANCE_TOL_M:
        problems.append(
            f"the record's clearance_m is {stated:.2f} m, but its own deck stands "
            f"{soffit - water_y:.3f} m over the water (walk surface "
            f"{side['placement']['walk_surface_m']:.2f} m less {thickness:.2f} m of "
            f"stringer and plank)")

    # --- 5: what else is rooted in the cut ---------------------------------
    cx, cy = deck["centre"]
    intruders = []
    index = load(DATA / "sidecars" / SCENE / "index.json")
    for ent in index["structures"]:
        if ent["id"] == BRIDGE:
            continue
        place = load(DATA / ent["sidecar"]).get("placement") or {}
        e, n = place.get("local_e"), place.get("local_n")
        if e is None or math.hypot(e - cx, n - cy) > REACH_M:
            continue
        if hf.covers(e, n) and hf.height(e, n) < water_y:
            intruders.append(f"structure {ent['id']} at E {e:.1f} N {n:.1f}")
    for frontage in sorted((DATA / "frontage").glob("*.json")):
        doc = load(frontage)
        if not isinstance(doc, dict):
            continue
        for key, coords in (("walks", "centreline_local_enu_m"),
                            ("fences", "path_local_enu_m")):
            for item in doc.get(key) or []:
                if item.get("rides") == BRIDGE:
                    continue
                for p in item.get(coords) or []:
                    e, n = float(p[0]), float(p[1])
                    if math.hypot(e - cx, n - cy) > REACH_M:
                        continue
                    if hf.covers(e, n) and hf.height(e, n) < water_y:
                        intruders.append(f"{key[:-1]} {item['id']} at E {e:.1f} N {n:.1f}")
                        break
    reading["intruders"] = intruders
    if intruders:
        problems.append(
            "something other than the crossing is rooted in the cut, and nothing "
            "declares it rides the deck: " + "; ".join(intruders))

    return reading, problems


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--gate", action="store_true",
                    help="exit 1 if any crossing does not span open water")
    ap.add_argument("--crossing", help="one bridge id; the default reads them all")
    args = ap.parse_args()

    wanted = [c for c in CROSSINGS
              if args.crossing in (None, c["bridge"])]
    if not wanted:
        print(f"no crossing '{args.crossing}' — this file reads "
              + ", ".join(c["bridge"] for c in CROSSINGS), file=sys.stderr)
        return 2

    failed = False
    for crossing in wanted:
        r, problems = measure(crossing)

        if not args.gate and r:
            print(f"{crossing['label']} — deck E {r['deck_e'][0]} .. "
                  f"{r['deck_e'][1]}, span {r['span_m']} m, water surface "
                  f"{r['water_surface_m']:+.2f} m")
            print(f"  open water under the deck   {r['open_water_m']:.2f} m "
                  f"({100 * r['open_water_m'] / r['span_m']:.0f}% of the span), "
                  f"bed {r['deepest_m']:+.3f} m")
            print(f"  dry abutment seats          west {r['west_seat_m']:.2f} m, "
                  f"east {r['east_seat_m']:.2f} m")
            print(f"  deck                        walk {r['deck_walk_m']:.2f} m, soffit "
                  f"{r['deck_soffit_m']:+.2f} m, clearance stated "
                  f"{r['clearance_stated_m']:.2f} m")
            print(f"  reach to the river          {r.get('mouth_reach_samples', 0)} samples, "
                  f"{r.get('mouth_reach_dry', 0)} above the water surface")
            print(f"  bars of land in the course  {r.get('interruptions', 0)} "
                  f"(longest {r.get('longest_bar_m', 0.0):.2f} m)")
            print(f"  rooted in the cut           "
                  f"{', '.join(r['intruders']) if r['intruders'] else 'nothing but the crossing'}")

        for p in problems:
            print(f"FAIL  {crossing['bridge']}: {p}", file=sys.stderr)
        if problems:
            failed = True
            continue
        if args.gate:
            print(f"{crossing['bridge']}: {r['open_water_m']:.2f} m of open water "
                  f"under an {r['span_m']:.1f} m span, abutments dry, the reach to "
                  f"the river unbroken, nothing damming the course, nothing else "
                  f"rooted in the cut")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
