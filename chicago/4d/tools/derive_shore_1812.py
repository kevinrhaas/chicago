#!/usr/bin/env python3
"""Derive the 1812 pre-cut shore from the committed readings and the 1834 trace.

`shore_1812_pre_cut` may not borrow the 1835 coast (docs/EPOCHS.md), and no survey
of the pre-cut mouth exists.  So the 1812 state is DERIVED, in the open, from two
committed things and nothing else:

* `data/terrain/1812_mouth_readings.json` — the statements: Swearingen's half mile
  of 1803, the compilation's Madison Street, and where the drafted piers begin; and
* the Wright 1834 trace — the only instrument reading of this landform, twenty-two
  years late and cut through at its north end.

Every departure from Wright is stated here rather than drawn by hand, which is what
lets `tools/check_shoreline_states.py` re-derive the file and refuse a hand edit.
What the 1812 state changes from 1834, and why:

1. **The cut and the piers are gone.**  The north shore stops at the last vertex
   that is a shore rather than a drafted pier face; the pier face and the accreting
   shore behind it are not carried.
2. **The spit is continuous.**  Wright's bar is an island because the 1833-34 cut
   made it one.  In 1812 it ran to the mainland, and the run between its north-west
   corner and the pier root is emitted as an explicit unmodelled gap: the attachment
   is inferred, the isthmus's width and lake face are NOT claimed.
3. **The mouth is at Swearingen's half mile.**  The tier-1 eyewitness distance is
   adopted; the tier-2 Madison reading is kept as the alternative, 111 m further
   south, and NOTHING IS AVERAGED between them.

Usage:  derive_shore_1812.py [--check]
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TERRAIN = ROOT / "data" / "terrain"
READINGS = TERRAIN / "1812_mouth_readings.json"
BASE = TERRAIN / "epochs" / "e1834_harbor_cut" / "shoreline.geojson"
OUT = TERRAIN / "epochs" / "e1830_natural" / "shoreline.geojson"
DATUM = ROOT / "data" / "datum.json"
STREETS = ROOT / "data" / "streets" / "1835.json"

PROVENANCE = {
    "derived_by": "tools/derive_shore_1812.py",
    "base_trace": "data/terrain/epochs/e1834_harbor_cut/shoreline.geojson",
    "readings": "data/terrain/1812_mouth_readings.json",
    "rule": "generated — do not hand-edit; tools/check_shoreline_states.py re-derives this file",
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


def point_at(pts, cum, start_i: int, target: float):
    """The point `target` metres along `pts` from vertex `start_i`, forward."""
    base = cum[start_i]
    for i in range(start_i + 1, len(pts)):
        if cum[i] - base >= target:
            span = cum[i] - cum[i - 1]
            t = (target - (cum[i - 1] - base)) / span if span else 0.0
            return i, (pts[i - 1][0] + t * (pts[i][0] - pts[i - 1][0]),
                       pts[i - 1][1] + t * (pts[i][1] - pts[i - 1][1]))
    raise SystemExit("the trace is shorter than the distance asked of it")


def crossing_north(pts, cum, start_i: int, northing: float):
    """Where `pts` first crosses a given local northing, walking forward."""
    for i in range(start_i + 1, len(pts)):
        a, b = pts[i - 1], pts[i]
        if (a[1] - northing) * (b[1] - northing) <= 0 and a[1] != b[1]:
            t = (northing - a[1]) / (b[1] - a[1])
            along = (cum[i - 1] + t * (cum[i] - cum[i - 1])) - cum[start_i]
            return i, (a[0] + t * (b[0] - a[0]), northing), along
    raise SystemExit(f"the trace never reaches local N {northing}")


def r2(p) -> list[float]:
    return [round(p[0], 2), round(p[1], 2)]


def derive() -> dict:
    readings = load(READINGS)
    base = load(BASE)
    datum = load(DATUM)
    oe, on = datum["origin_utm_e"], datum["origin_utm_n"]
    feats = {f["id"]: f for f in base["features"]}

    def local(coords):
        return [(x - oe, y - on) for x, y in coords]

    # The traced south shore runs south-to-north in the file; walk it from the
    # forks box eastward and then southward, which is the direction Swearingen
    # travelled and the direction the distance below is measured in.
    west = local(feats["south_shore_harbor_reach"]["geometry"]["coordinates"])[::-1]
    north = local(feats["north_shore_harbor_reach"]["geometry"]["coordinates"])
    bar = local(feats["sand_bar_1834"]["geometry"]["coordinates"][0])

    anchor_cfg = readings["fort_anchor"]
    fort = (anchor_cfg["flagstaff_utm_e"] - oe, anchor_cfg["flagstaff_utm_n"] - on)
    ai = min(range(len(west)), key=lambda i: dist(west[i], fort))
    anchor_offset = dist(west[ai], fort)

    cum = cumulative(west)
    by_id = {r["id"]: r for r in readings["readings"]}

    half = by_id["swearingen_1803_half_mile"]
    oi, outlet = point_at(west, cum, ai, half["value_m"])

    mad = by_id["madison_street_compilation"]
    madison_n = mad["value_local_n_m"]
    mi, madison_pt, madison_along = crossing_north(west, cum, ai, madison_n)

    # The bar tip is compared to the adopted station by NORTHING, not by distance
    # along the west bank: the tip stands on the bar's own side of the channel, so
    # a path measured up the opposite bank would not be measuring the same thing.
    tip = min(bar, key=lambda p: p[1])
    tip_south_of_adopted = outlet[1] - tip[1]

    last_natural = readings["cut_and_piers"]["north_shore_last_natural_vertex_index"]
    accretion_from = readings["cut_and_piers"]["accretion_bound_first_index"]
    attach = north[last_natural]
    # The corner the cut left standing closest to the mainland, taken as the bar
    # vertex nearest the attachment rather than by eye.
    nw = min(bar, key=lambda p: dist(p, attach))

    spread = madison_along - half["value_m"]

    src_w = feats["south_shore_harbor_reach"]["properties"]["sources"]
    src_n = feats["north_shore_harbor_reach"]["properties"]["sources"]
    src_b = feats["sand_bar_1834"]["properties"]["sources"]

    features = [
        {
            "type": "Feature", "id": "north_shore_pre_cut_1812",
            "properties": {
                "kind": "shore",
                "name": "North bank of the main stem, east to the point where the north pier was later built out from it",
                "confidence": "inferred",
                "derivation": f"Wright 1834 north_shore_harbor_reach vertices 0-{last_natural}",
                "note": (
                    "THE PIERS ARE NOT HERE, AND THAT IS THE POINT. The 1834 line carries the "
                    f"drafted inner face of the north pier from vertex {last_natural + 1} east to "
                    "the pier head, and a lake shore north of the pier that the 1834 epoch's own "
                    "note says is accreting. Neither is a shore of 1812: one is a structure and "
                    "the other is sand the structure caught. This line therefore ends where the "
                    "shore ends, at the pier root, and the 1812 shore north of that point is not "
                    "claimed by this file - the 1834 line stands as an EASTWARD BOUND on it and "
                    "is recorded as one in data/terrain/shoreline_states.json."),
                "sources": src_n,
                "provenance": PROVENANCE,
            },
            "geometry": {"type": "LineString",
                         "coordinates": [[round(x + oe, 2), round(y + on, 2)] for x, y in north[:last_natural + 1]]},
        },
        {
            "type": "Feature", "id": "spit_attachment_gap_1812",
            "properties": {
                "kind": "unmodelled_gap",
                "name": "Where the baymouth spit met the mainland before the cut",
                "confidence": "inferred",
                "claims": "the attachment only",
                "does_not_claim": "the isthmus's width, its lake face, or its height - no ground is asserted between these two points",
                "length_m": round(dist(attach, nw), 1),
                "derivation": "north_shore_harbor_reach vertex %d to the north-west corner of sand_bar_1834" % last_natural,
                "note": (
                    "Wright draws the bar as an ISLAND because the 1833-34 cut had made it one. "
                    "In 1812 there was no cut, the spit ran to the mainland, and the river was "
                    "deflected south behind it - which is the whole reason the mouth stood where "
                    "Swearingen found it. So the attachment is a deduction from the landform's "
                    "own behaviour and is graded inferred. The STRAIGHT LINE between the two "
                    "points is a convenience and not a reading: nothing says the isthmus ran "
                    "straight, how wide it was, or where its lake face lay. Drawing it is "
                    "T-1243's problem, in the terrain spec, where an elevation would have to be "
                    "argued for. See docs/LIBERTIES.md L240."),
                "sources": sorted(set(src_n) | set(src_b)),
                "provenance": PROVENANCE,
            },
            "geometry": {"type": "LineString",
                         "coordinates": [[round(attach[0] + oe, 2), round(attach[1] + on, 2)],
                                         [round(nw[0] + oe, 2), round(nw[1] + on, 2)]]},
        },
        {
            "type": "Feature", "id": "baymouth_bar_1812",
            "properties": {
                "kind": "bar",
                "name": "The baymouth bar that deflected the river south",
                "confidence": "inferred",
                "derivation": "sand_bar_1834 ring, carried whole",
                "south_tip_local": r2(tip),
                "note": (
                    "Wright's 1834 planform, carried WHOLE and not re-cut, because the two things "
                    "that could have moved it are measured and both are inside the trace's own "
                    "+/-20 m: the tip stands %.1f m of northing south of the station Swearingen's "
                    "half mile lands on, and its north face is the cut's south side, which the "
                    "gap feature above accounts for rather than redraws. Twenty-two years and a "
                    "harbour works separate this drawing from the scene date; no elevation is "
                    "claimed here, as none is claimed for 1834." % tip_south_of_adopted),
                "sources": src_b,
                "provenance": PROVENANCE,
            },
            "geometry": {"type": "Polygon",
                         "coordinates": [[[round(x + oe, 2), round(y + on, 2)] for x, y in bar]]},
        },
        {
            "type": "Feature", "id": "channel_west_bank_1812",
            "properties": {
                "kind": "shore",
                "name": "West bank of the southward channel, from the forks box to the mouth",
                "confidence": "inferred",
                "derivation": "Wright 1834 south_shore_harbor_reach, reversed, to the adopted outlet station",
                "outlet_station_local": r2(outlet),
                "length_m": round(cum[oi - 1] + dist(west[oi - 1], outlet), 1),
                "note": (
                    "The same line the 1834 epoch carries, ended at the adopted 1812 mouth "
                    "instead of running on to the foot of Wright's sheet. Nothing about this "
                    "bank is an 1812 reading; it is the only measured reading of it, and the "
                    "1834 feature's own quality figures (median 1.42 m, p90 7.43 m to drawn "
                    "line) are the tightest thing that can be said about it."),
                "sources": src_w,
                "provenance": PROVENANCE,
            },
            "geometry": {"type": "LineString",
                         "coordinates": [[round(x + oe, 2), round(y + on, 2)] for x, y in west[:oi]]
                                        + [[round(outlet[0] + oe, 2), round(outlet[1] + on, 2)]]},
        },
        {
            "type": "Feature", "id": "lake_shore_south_of_outlet_1812",
            "properties": {
                "kind": "shore",
                "name": "Lake shore south of the natural mouth, to the foot of Wright's sheet",
                "confidence": "inferred",
                "derivation": "Wright 1834 south_shore_harbor_reach, reversed, from the adopted outlet station on",
                "note": (
                    "South of the mouth the harbour works did not reach, so the 1834 line is "
                    "carried as the 1812 one with no change beyond where it starts. That is an "
                    "assumption about twenty-two years of a lake shore and it is graded inferred "
                    "for exactly that reason. The last 200 m of the 1834 run follows the sheet's "
                    "dark bottom edge rather than a pen line and is the weakest part of it; that "
                    "weakness is inherited here in full."),
                "sources": src_w,
                "provenance": PROVENANCE,
            },
            "geometry": {"type": "LineString",
                         "coordinates": [[round(outlet[0] + oe, 2), round(outlet[1] + on, 2)]]
                                        + [[round(x + oe, 2), round(y + on, 2)] for x, y in west[oi:]]},
        },
        {
            "type": "Feature", "id": "mouth_outlet_reading_band_1812",
            "properties": {
                "kind": "mouth_outlet_reading_band",
                "state_id": "shore_1812_pre_cut",
                "resolution": "primary_reading_adopted",
                "adopted": "swearingen_1803_half_mile",
                "alternative": "madison_street_compilation",
                "adopted_midpoint": None,
                "spread_m": round(spread, 1),
                "stations": {
                    "swearingen_1803_half_mile": {"along_m": round(half["value_m"], 1), "local": r2(outlet)},
                    "madison_street_compilation": {"along_m": round(madison_along, 1), "local": r2(madison_pt)},
                    "wright_1834_bar_tip": {"south_of_adopted_m": round(tip_south_of_adopted, 1),
                                            "local": r2(tip)},
                },
                "fort_anchor_local": r2(west[ai]),
                "fort_anchor_offset_m": round(anchor_offset, 2),
                "note": (
                    "The run of bank the mouth stood somewhere along, and the reason the adopted "
                    "end of it was adopted. Swearingen walked the distance in 1803 and wrote it "
                    "down that day (tier 1); the Madison Street reading is a tier-2 compilation "
                    "saying 'near', %.1f m further south. The tier-1 reading is taken and the "
                    "tier-2 one is kept beside it. NO MIDPOINT IS ADOPTED - the 1835 state's "
                    "Wright/Rees band is the precedent and the rule. The third station is "
                    "Wright's own bar tip of 1834: twenty-two years later than the scene, and "
                    "only %.1f m of northing south of the adopted station - inside this trace's "
                    "own +/-20 m. An 1803 distance walked on foot and an 1834 instrument survey "
                    "put the natural mouth within ten metres of each other, and that convergence "
                    "is the strongest thing this project can say about where it was."
                    % (spread, tip_south_of_adopted)),
                "sources": ["quaife_1913_swearingen", "chicagology_prefire274", "wright_1834"],
                "provenance": PROVENANCE,
            },
            "geometry": {"type": "LineString",
                         "coordinates": [[round(outlet[0] + oe, 2), round(outlet[1] + on, 2)]]
                                        + [[round(x + oe, 2), round(y + on, 2)] for x, y in west[oi:mi]]
                                        + [[round(madison_pt[0] + oe, 2), round(madison_pt[1] + on, 2)]]},
        },
    ]

    return {
        "type": "FeatureCollection",
        "name": "e1830_natural shoreline (shore_1812_pre_cut)",
        "crs": {"type": "name", "properties": {"name": "urn:ogc:def:crs:EPSG::26916"}},
        "_doc": (
            "The 1812 pre-cut shore, river mouth and baymouth bar for terrain epoch "
            "e1830_natural, shoreline state shore_1812_pre_cut. GENERATED by "
            "tools/derive_shore_1812.py from data/terrain/1812_mouth_readings.json and the "
            "Wright 1834 trace - do not hand-edit; tools/check_shoreline_states.py re-derives "
            "it. Coordinates are EPSG:26916 metres; local ENU is these minus data/datum.json "
            "origin_utm_e / origin_utm_n. NO ELEVATION IS CLAIMED BY ANY FEATURE HERE: this is "
            "the planform only, and the ground it implies is T-1243's terrain spec."),
        "evidence_limit": (
            "No survey of the 1812 mouth exists and this file does not pretend one does. Every "
            "line here is Wright's 1834 instrument reading of the same landform, taken twenty-two "
            "years late, with the cut and the piers removed and the mouth set by a distance an "
            "eyewitness stated in 1803. Nothing here is graded better than inferred."),
        "features": features,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true",
                    help="re-derive and compare with the committed file instead of writing it")
    args = ap.parse_args()
    doc = derive()
    text = json.dumps(doc, indent=2, ensure_ascii=True) + "\n"
    if args.check:
        if not OUT.exists():
            print("FAIL", OUT.relative_to(ROOT), "does not exist")
            return 1
        if OUT.read_text(encoding="utf-8") != text:
            print("FAIL", OUT.relative_to(ROOT),
                  "does not match its derivation from the committed readings")
            return 1
        print("OK the 1812 shore re-derives from its readings and the 1834 trace")
        return 0
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text, encoding="utf-8")
    print("wrote", OUT.relative_to(ROOT), f"({len(doc['features'])} features)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
