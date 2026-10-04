#!/usr/bin/env python3
"""Derive the 15 August 1812 evacuation route and battle zone from their readings.

T-0470. The column that left the first Fort Dearborn on 15 August 1812 went down the
river to its natural mouth and then south along the beach, and was attacked from
behind the bank "about a mile and a half" from the fort. A tradition put the place at
two cottonwoods later standing in Eighteenth Street. No survey, map or marker of 1812
places it, so the place is DERIVED, in the open, from exactly three committed things:

* `data/terrain/1812_evacuation_readings.json` -- the statements, with their sources,
  their grades and this project's reading of each;
* the 1812 shore `tools/derive_shore_1812.py` writes (the old channel's west bank and
  the lake shore south of the natural outlet), and the Rees 1849 shore below Twelfth
  Street that the 1812 terrain spec carries;
* the Eighteenth Street row in `data/traces/south_anchor_control.json`.

What it writes, to `data/terrain/1812_evacuation_route.geojson`:

1. the route: the fort anchor, down the west bank to the outlet, then along the
   waterline; every distance below is measured along it;
2. one station per distance reading, adopted or not, and the Eighteenth Street row;
3. the battle zone: the strip between the waterline and the ridge line, from the
   north end of Heald's band to Eighteenth Street's south line. It spans the
   disagreement between the distance and the tradition rather than choosing;
   NO POINT INSIDE IT IS CLAIMED and none is drawn;
4. the Eighteenth Street trees' locus: a line along the street, not a point.

Usage:  derive_evacuation_1812.py [--check]
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TERRAIN = ROOT / "data" / "terrain"
READINGS = TERRAIN / "1812_evacuation_readings.json"
SHORE_1812 = TERRAIN / "epochs" / "e1830_natural" / "shoreline.geojson"
BELOW_TWELFTH = TERRAIN / "epochs" / "e1834_harbor_cut" / "lake_shore_below_twelfth.geojson"
ANCHORS = ROOT / "data" / "traces" / "south_anchor_control.json"
DATUM = ROOT / "data" / "datum.json"
OUT = TERRAIN / "1812_evacuation_route.geojson"

# Half of East Eighteenth Street's 66 ft right of way (data/street_grid/1904.json
# § streets.e18th): the trees stood "between its curb stones", so the zone runs to the
# street's south line and not to its centre.
HALF_ROW_18TH_M = 66 * 0.3048 / 2
SAMPLE_M = 10.0

PROVENANCE = {
    "derived_by": "tools/derive_evacuation_1812.py",
    "readings": "data/terrain/1812_evacuation_readings.json",
    "lines": [
        "data/terrain/epochs/e1830_natural/shoreline.geojson",
        "data/terrain/epochs/e1834_harbor_cut/lake_shore_below_twelfth.geojson",
        "data/traces/south_anchor_control.json",
    ],
    "rule": "generated — do not hand-edit; tools/derive_evacuation_1812.py --check re-derives this file",
}


def load(p: Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8"))


def dist(a, b) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def cumulative(pts: list) -> list[float]:
    out = [0.0]
    for i in range(1, len(pts)):
        out.append(out[-1] + dist(pts[i - 1], pts[i]))
    return out


def point_at(pts, cum, target: float):
    """The point `target` metres along `pts` from its first vertex."""
    for i in range(1, len(pts)):
        if cum[i] >= target:
            span = cum[i] - cum[i - 1]
            t = (target - cum[i - 1]) / span if span else 0.0
            return (pts[i - 1][0] + t * (pts[i][0] - pts[i - 1][0]),
                    pts[i - 1][1] + t * (pts[i][1] - pts[i - 1][1]))
    raise SystemExit(f"the route is {cum[-1]:.1f} m long and a reading asks for {target:.1f} m")


def along_at_north(pts, cum, northing: float) -> float:
    """Distance along `pts` at its first southward crossing of `northing`."""
    for i in range(1, len(pts)):
        a, b = pts[i - 1], pts[i]
        if a[1] >= northing >= b[1] and a[1] != b[1]:
            t = (a[1] - northing) / (a[1] - b[1])
            return cum[i - 1] + t * (cum[i] - cum[i - 1])
    raise SystemExit(f"the route never crosses N {northing}")


def slice_between(pts, cum, a_m: float, b_m: float, step: float) -> list:
    """Points along `pts` from a_m to b_m: every vertex between, plus a sample every
    `step` metres, so a straight offset of the run keeps its shape."""
    marks = {a_m, b_m}
    m = a_m
    while m < b_m:
        marks.add(m)
        m += step
    marks.update(c for c in cum if a_m < c < b_m)
    return [point_at(pts, cum, x) for x in sorted(marks)]


def build_route(datum: dict) -> tuple[list, dict]:
    oe, on = datum["origin_utm_e"], datum["origin_utm_n"]
    shore = {f["id"]: f for f in load(SHORE_1812)["features"]}
    band = shore["mouth_outlet_reading_band_1812"]["properties"]
    anchor = tuple(band["fort_anchor_local"])
    readings = load(READINGS)
    seam_n = readings["lines_used"]["seam_row_local_n"]

    def local(c):
        return [(p[0] - oe, p[1] - on) for p in c]

    bank = local(shore["channel_west_bank_1812"]["geometry"]["coordinates"])
    i0 = min(range(len(bank)), key=lambda k: dist(bank[k], anchor))
    if dist(bank[i0], anchor) > 0.05:
        raise SystemExit("the fort anchor is no longer a vertex of the 1812 west bank")
    river_leg = bank[i0:]

    lake = local(shore["lake_shore_south_of_outlet_1812"]["geometry"]["coordinates"])
    if dist(lake[0], river_leg[-1]) > 0.05:
        raise SystemExit("the 1812 lake shore no longer starts at the west bank's outlet")
    cut = next((k for k, p in enumerate(lake) if p[1] <= seam_n + 0.05), None)
    if cut is None:
        raise SystemExit(f"the 1812 lake shore never reaches the seam row N {seam_n}")
    shore_leg = lake[1:cut + 1]

    below = local(load(BELOW_TWELFTH)["features"][0]["geometry"]["coordinates"])
    if abs(below[0][1] - seam_n) > 1.0:
        raise SystemExit(f"the Rees 1849 shore no longer starts on the seam row N {seam_n}")

    pts = river_leg + shore_leg + below
    cum = cumulative(pts)
    legs = {
        "outlet_m": round(cum[len(river_leg) - 1], 1),
        "seam_north_m": round(cum[len(river_leg) + len(shore_leg) - 1], 1),
        "seam_south_m": round(cum[len(river_leg) + len(shore_leg)], 1),
        "seam_step_m": round(dist(shore_leg[-1], below[0]), 1),
    }
    return pts, legs


def build(readings: dict, datum: dict) -> dict:
    oe, on = datum["origin_utm_e"], datum["origin_utm_n"]

    def utm(p):
        return [round(p[0] + oe, 2), round(p[1] + on, 2)]

    def loc(p):
        return [round(p[0], 2), round(p[1], 2)]

    pts, legs = build_route(datum)
    cum = cumulative(pts)

    row = load(ANCHORS)["control"]["eighteenth_prairie"]
    row_n, row_e = row["local_n"], row["local_e"]
    row_along = along_at_north(pts, cum, row_n)
    row_straight = dist(pts[0], (point_at(pts, cum, row_along)[0], row_n))
    legs_run = legs["seam_north_m"] - legs["outlet_m"]
    legs_chord = dist(point_at(pts, cum, legs["outlet_m"]), point_at(pts, cum, legs["seam_north_m"]))
    zone_south_along = along_at_north(pts, cum, row_n - HALF_ROW_18TH_M)

    adopted = [r for r in readings["readings"] if r["role"] == "primary_adopted"]
    if len(adopted) != 1:
        raise SystemExit("exactly one distance reading must be primary_adopted")
    heald = adopted[0]
    lo = heald["value_m"] - heald["band_m"]
    hi = heald["value_m"] + heald["band_m"]
    route_end_along = max(zone_south_along, hi)
    if row_straight - hi <= 0:
        raise SystemExit("Eighteenth Street now falls inside Heald's band in a straight line: "
                         "the zone's note and the evidence_limit no longer say what is true")

    width = readings["landform"]["ridge_back_from_beach_m"]
    features = []
    route_pts = [p for p, c in zip(pts, cum) if c < route_end_along] + [point_at(pts, cum, route_end_along)]
    features.append({
        "type": "Feature", "id": "evacuation_route_1812",
        "properties": {
            "kind": "route",
            "name": "The evacuation route of 15 August 1812, fort to Eighteenth Street",
            "length_m": round(cumulative(route_pts)[-1], 1),
            "legs": legs,
            "confidence": readings["route"]["confidence"],
            "note": ("From the fort anchor down the old channel's west bank to the natural "
                     "outlet, then south along the waterline: the derived 1812 shore to "
                     "the seam row, a step of the stated length across the two traces' "
                     "disagreement there, and the carried Rees 1849 shore below it. This is "
                     "the line every distance below is measured along, and it is drawn on "
                     "the reconstructed 1812 shore, not on modern streets. " +
                     readings["route"]["confidence_note"]),
            "sources": sorted({r["source_id"] for r in readings["route"]["readings"]}),
            "provenance": PROVENANCE,
        },
        "geometry": {"type": "LineString", "coordinates": [utm(p) for p in route_pts]},
    })

    def station(fid, name, along, confidence, note, sources, extra=None):
        p = point_at(pts, cum, along)
        props = {"kind": "station", "name": name, "along_m": round(along, 1),
                 "straight_m": round(dist(pts[0], p), 1), "local": loc(p), "confidence": confidence, "note": note,
                 "sources": sources, "provenance": PROVENANCE}
        props.update(extra or {})
        features.append({"type": "Feature", "id": fid, "properties": props,
                         "geometry": {"type": "Point", "coordinates": utm(p)}})

    for r in readings["readings"]:
        if r["kind"] != "distance_from_fort" or r["role"] == "corroborating_not_independent":
            continue
        extra = {"reading": r["id"], "role": r["role"]}
        if r["role"] == "primary_adopted":
            station(f"station_{r['id']}_north", "North end of Heald's band (1.25 mi)", lo,
                    r["confidence"], r["band_note"], [r["source_id"]], extra)
            station(f"station_{r['id']}", "About a mile and a half (Heald)", r["value_m"],
                    r["confidence"], r["confidence_note"], [r["source_id"]], extra)
            station(f"station_{r['id']}_south", "South end of Heald's band (1.75 mi)", hi,
                    r["confidence"], r["band_note"], [r["source_id"]], extra)
        else:
            station(f"station_{r['id']}", "Half a mile (Jordan, not adopted)", r["value_m"],
                    r["confidence"], r["confidence_note"], [r["source_id"]], extra)

    trees = next(r for r in readings["readings"] if r["id"] == "eighteenth_street_trees")
    station("station_eighteenth_street_row", "Eighteenth Street's row on the shore", row_along,
            trees["confidence"],
            "Where the route crosses Eighteenth Street's row. A modern locator for the "
            "tradition's place, not a location of the battle.",
            [trees["source_id"], "osm_streets_2026"], {"reading": trees["id"], "role": trees["role"]})

    shore_e = point_at(pts, cum, row_along)[0]
    if shore_e <= row_e:
        raise SystemExit("the shore at Eighteenth Street is no longer east of Prairie's crossing")
    features.append({
        "type": "Feature", "id": "eighteenth_street_trees_locus",
        "properties": {
            "kind": "landmark_locus",
            "name": "The Eighteenth Street cottonwoods (tradition)",
            "length_m": round(shore_e - row_e, 1),
            "confidence": trees["confidence"],
            "note": (trees["where_on_the_ground"] + " Drawn along the row's northing; the "
                     "street's small departure from due east is not modelled. " +
                     trees["confidence_note"]),
            "sources": [trees["source_id"], "osm_streets_2026"],
            "provenance": PROVENANCE,
        },
        "geometry": {"type": "LineString",
                     "coordinates": [utm((row_e, row_n)), utm((shore_e, row_n))]},
    })

    water = slice_between(pts, cum, lo, zone_south_along, SAMPLE_M)
    ridge = [(p[0] - width, p[1]) for p in water]
    ring = water + ridge[::-1] + [water[0]]
    disagreement = round(row_along - heald["value_m"], 1)
    features.append({
        "type": "Feature", "id": "battle_zone_1812",
        "properties": {
            "kind": "confidence_zone",
            "name": "Where the accounts place the attack of 15 August 1812",
            "along_m": [round(lo, 1), round(zone_south_along, 1)],
            "width_m": width,
            "confidence": "inferred",
            "precision": "zone",
            "note": ("The strip between the waterline and the ridge line, from the north "
                     "end of Heald's band to Eighteenth Street's south line. Its north part "
                     f"is the distance reading ({round(lo)}-{round(hi)} m along the route); "
                     f"its south end is the tradition ({round(row_along)} m along). They "
                     f"disagree by {disagreement} m, so the zone spans both and prefers "
                     "neither, and NO POINT INSIDE IT IS CLAIMED. The fight round the "
                     "wagons in the rear, the charge up the bank and the parley all fall "
                     "within it on the accounts read; Heald's withdrawal 'out of shot of "
                     "the bank' lay inland of it at no stated distance and is not drawn. "
                     + readings["landform"]["zone_width_rule"]),
            "sources": sorted({readings["landform"]["bank_source_id"],
                               readings["landform"]["ridge_source_id"], heald["source_id"],
                               trees["source_id"]}),
            "review_required": True,
            "review_note": readings["review_note"],
            "provenance": PROVENANCE,
        },
        "geometry": {"type": "Polygon", "coordinates": [[utm(p) for p in ring]]},
    })

    return {
        "type": "FeatureCollection",
        "name": "evacuation_1812",
        "crs": {"type": "name", "properties": {"name": "urn:ogc:def:crs:EPSG::26916"}},
        "_doc": ("The 15 August 1812 evacuation route and the zone the accounts place the "
                 "attack in (T-0470). GENERATED by tools/derive_evacuation_1812.py from "
                 "data/terrain/1812_evacuation_readings.json and three committed lines - do "
                 "not hand-edit; --check re-derives it. Coordinates are EPSG:26916 metres; "
                 "local ENU is these minus data/datum.json origin_utm_e / origin_utm_n. "
                 "Documentary geography only: no figure, camp or event is staged by it."),
        "address_date": readings["address_date"],
        "review_required": True,
        "review_note": readings["review_note"],
        "evidence_limit": ("No survey, map or marker of 1812 places the attack. The one "
                           "distance is the commander's 'about a mile and a half', reached "
                           "through a compilation's OCR; the one named place is a tradition "
                           "recorded seventy years on. Measured along the reconstructed shore "
                           f"they disagree by {disagreement} m: Eighteenth Street lies "
                           f"{round(row_along - hi, 1)} m beyond the south end of the band "
                           "that rounds to Heald's figure. That disagreement is drawn, "
                           "not resolved."),
        "disagreement": {
            "heald_m": heald["value_m"],
            "heald_band_m": [round(lo, 1), round(hi, 1)],
            "eighteenth_street_m": round(row_along, 1),
            "eighteenth_street_minus_heald_m": disagreement,
            "eighteenth_street_beyond_band_m": round(row_along - hi, 1),
            "eighteenth_street_miles": round(row_along / 1609.344, 2),
            "eighteenth_street_straight_m": round(row_straight, 1),
            "eighteenth_street_straight_miles": round(row_straight / 1609.344, 2),
            "measure_note": ("Distances are measured along the traced waterline, as the "
                             "mouth readings measure Swearingen's half mile. The trace "
                             "wiggles: between the outlet and the seam row it is "
                             f"{round(100 * (legs_run / legs_chord - 1))} per cent longer "
                             "than its chord, so a distance walked on the beach lies "
                             "between the along and straight figures. Eighteenth Street is "
                             "beyond Heald's band on either measure."),
        },
        "features": features,
    }


def render(doc: dict) -> str:
    return json.dumps(doc, indent=1, ensure_ascii=False) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true",
                    help="re-derive and fail if the committed file differs")
    args = ap.parse_args()
    text = render(build(load(READINGS), load(DATUM)))
    if args.check:
        have = OUT.read_text(encoding="utf-8") if OUT.exists() else ""
        if have != text:
            print(f"DRIFT: {OUT.relative_to(ROOT)} is not what its readings derive - "
                  "run tools/derive_evacuation_1812.py")
            return 1
        print(f"ok: {OUT.relative_to(ROOT)} re-derives from its readings")
        return 0
    OUT.write_text(text, encoding="utf-8")
    d = json.loads(text)["disagreement"]
    print(f"wrote {OUT.relative_to(ROOT)}: Heald {d['heald_band_m']} m, Eighteenth Street "
          f"{d['eighteenth_street_m']} m ({d['eighteenth_street_miles']} mi), "
          f"{d['eighteenth_street_beyond_band_m']} m beyond the band")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
