#!/usr/bin/env python3
"""Derive the site of Lee's Place (later Hardscrabble) from its readings.

T-2501, the first piece of T-2488. Charles Lee's farm on the South Branch, where Liberty
White and a Canadian named Debou were killed on 6 April 1812, has no survey, plat or
marker. Five printed statements place it, and they place it by four different measures.
So the site is DERIVED, in the open, from exactly these committed things:

* `data/terrain/1812_hardscrabble_readings.json`: the statements, their sources, their
  grades, and this project's reading of each one's "about" or "some";
* the river they are measured along. That is the 1812 old channel and the main stem's
  south bank (`tools/derive_shore_1812.py`), then the South Branch's committed centre down
  to the box floor (Wright 1834, then Rees 1849), then T-2501's trace from the box floor to
  the canal at Bridgeport (`tools/trace_south_branch_bridgeport_rees_1849.py`);
* the fort anchor that the 1812 evacuation route and Swearingen's half mile are measured
  from.

What it writes, to `data/terrain/1812_hardscrabble_site.json`:

1. Bridgeport, the forks and the river distance of each from the mouth;
2. one test per placing, each saying where the placing falls and whether the adopted
   station lies inside its band;
3. THE SITE: Hubbard's half mile below Bridgeport, on the north-west bank. It is a STATION
   with a REACH of that bank, the stretch his "about" allows, and never a pin.

Usage:  derive_hardscrabble_1812.py [--check]
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TERRAIN = ROOT / "data" / "terrain"
READINGS = TERRAIN / "1812_hardscrabble_readings.json"
TRACE = TERRAIN / "1812_south_branch_to_bridgeport.geojson"
SHORE_1812 = TERRAIN / "epochs" / "e1830_natural" / "shoreline.geojson"
BRANCHES = TERRAIN / "epochs" / "e1834_harbor_cut" / "branches.geojson"
BELOW_TWELFTH = TERRAIN / "epochs" / "e1834_harbor_cut" / "south_branch_below_twelfth.geojson"
DATUM = ROOT / "data" / "datum.json"
OUT = TERRAIN / "1812_hardscrabble_site.json"

SPLICE_N = -2110.0       # the row the Wright and Rees South Branch traces abut on
STEP_M = 10.0            # resampling step for the School Section centre


def load(p: Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8"))


def dist(a, b) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def cumulative(pts) -> list[float]:
    out = [0.0]
    for i in range(1, len(pts)):
        out.append(out[-1] + dist(pts[i - 1], pts[i]))
    return out


def point_at(pts, cum, target: float):
    """The point `target` metres along the polyline, and the index of the segment it is on."""
    for i in range(1, len(pts)):
        if cum[i] >= target:
            t = (target - cum[i - 1]) / ((cum[i] - cum[i - 1]) or 1.0)
            return ((pts[i - 1][0] + t * (pts[i][0] - pts[i - 1][0]),
                     pts[i - 1][1] + t * (pts[i][1] - pts[i - 1][1])), i - 1, t)
    return (pts[-1], len(pts) - 2, 1.0)


def bank_at_north(bank, northing: float) -> float:
    """Easting of a north-south bank line at a northing, by linear interpolation."""
    for i in range(1, len(bank)):
        (e0, n0), (e1, n1) = bank[i - 1], bank[i]
        if min(n0, n1) <= northing <= max(n0, n1) and n0 != n1:
            return e0 + (northing - n0) / (n1 - n0) * (e1 - e0)
    raise SystemExit(f"a School Section bank line does not reach N {northing}")


def r1(x: float) -> float:
    return round(x, 1)


def miles(m: float, mile: float) -> float:
    return round(m / mile, 2)


def bearing(a, b) -> float:
    return round(math.degrees(math.atan2(b[0] - a[0], b[1] - a[1])) % 360.0, 1)


def build_river(datum: dict):
    """The river from the 1812 mouth to Bridgeport, in local metres, with its named legs."""
    oe, on = datum["origin_utm_e"], datum["origin_utm_n"]

    def local(c):
        return [(p[0] - oe, p[1] - on) for p in c]

    shore = {f["id"]: f for f in load(SHORE_1812)["features"]}
    anchor = tuple(shore["mouth_outlet_reading_band_1812"]["properties"]["fort_anchor_local"])
    bank = local(shore["channel_west_bank_1812"]["geometry"]["coordinates"])
    outlet = tuple(shore["channel_west_bank_1812"]["properties"]["outlet_station_local"])
    if dist(bank[-1], outlet) > 0.05:
        raise SystemExit("the 1812 west bank no longer ends on its outlet station")
    if min(dist(p, anchor) for p in bank) > 0.05:
        raise SystemExit("the fort anchor is no longer a vertex of the 1812 west bank")
    mouth_leg = bank[::-1]                            # outlet -> up the channel -> main stem
    chord = [(0.0, 0.0)]                              # across the forks window to the datum

    br = {f["id"]: f for f in load(BRANCHES)["features"]}
    wb = local(br["south_branch_west_bank"]["geometry"]["coordinates"])
    eb = local(br["south_branch_east_bank"]["geometry"]["coordinates"])
    n_top = min(max(p[1] for p in wb), max(p[1] for p in eb))
    school = []
    n = n_top
    while n > SPLICE_N:
        school.append(((bank_at_north(wb, n) + bank_at_north(eb, n)) / 2.0, n))
        n -= STEP_M

    feats = {f["properties"]["name"]: f for f in load(BELOW_TWELFTH)["features"]}
    bw = local(feats["West bank of the South Branch below Twelfth Street"]["geometry"]["coordinates"])
    be = local(feats["East bank of the South Branch below Twelfth Street"]["geometry"]["coordinates"])
    if len(bw) != len(be):
        raise SystemExit("the Rees 1849 bank runs no longer pair vertex for vertex")
    below = [((w[0] + e[0]) / 2.0, (w[1] + e[1]) / 2.0) for w, e in zip(bw, be)]
    if abs(below[0][1] - SPLICE_N) > 1.0:
        raise SystemExit(f"the Rees 1849 reach no longer starts on the splice row N {SPLICE_N}")

    tr = load(TRACE)
    tf = {f["id"]: f for f in tr["features"]}
    cen_f = tf["south_branch_to_bridgeport_centreline"]
    trace = local(cen_f["geometry"]["coordinates"])
    nw = local(tf["south_branch_to_forks_nw_bank"]["geometry"]["coordinates"])
    k_forks = cen_f["properties"]["forks_vertex"]
    if dist(trace[0], below[-1]) > 0.05:
        raise SystemExit("T-2501's trace no longer starts on the Rees 1849 reach's last vertex")

    pts = mouth_leg + chord + school + below[:-1] + trace
    cum = cumulative(pts)
    i_anchor = min(range(len(mouth_leg)), key=lambda k: dist(mouth_leg[k], anchor))
    i_trace = len(mouth_leg) + len(chord) + len(school) + len(below) - 1
    legs = {
        "mouth_to_fort_anchor_m": r1(cum[i_anchor]),
        "mouth_to_main_stem_west_end_m": r1(cum[len(mouth_leg) - 1]),
        "chord_across_the_forks_window_m": r1(dist(mouth_leg[-1], chord[0])),
        "mouth_to_box_floor_trace_start_m": r1(cum[i_trace]),
        "mouth_to_south_branch_forks_m": r1(cum[i_trace + k_forks]),
        "mouth_to_bridgeport_m": r1(cum[-1]),
    }
    return {"pts": pts, "cum": cum, "anchor": anchor, "outlet": outlet,
            "i_trace": i_trace, "k_forks": k_forks, "trace": trace, "nw": nw, "legs": legs}


def build(readings: dict, datum: dict) -> dict:
    oe, on = datum["origin_utm_e"], datum["origin_utm_n"]
    mile = readings["mile_m"]
    rv = build_river(datum)
    pts, cum, anchor = rv["pts"], rv["cum"], rv["anchor"]
    L = cum[-1]
    bridgeport = pts[-1]
    forks = pts[rv["i_trace"] + rv["k_forks"]]
    along_forks = cum[rv["i_trace"] + rv["k_forks"]]

    def utm(p):
        return [round(p[0] + oe, 2), round(p[1] + on, 2)]

    def loc(p):
        return [round(p[0], 2), round(p[1], 2)]

    P = {p["id"]: p for p in readings["placings"]}
    hub = P["hubbard_half_mile_below_bridgeport"]

    # THE STATION, and the bank point opposite it. The trace's banks pair vertex for vertex
    # with its centreline up to the forks, so the bank point uses the same segment and fraction.
    def on_bank(along_from_mouth: float):
        c, seg, t = point_at(pts, cum, along_from_mouth)
        k = seg - rv["i_trace"]
        nw = rv["nw"]
        if k < 0 or k + 1 >= len(nw):
            raise SystemExit("the station falls outside the traced reach that carries banks")
        b = (nw[k][0] + t * (nw[k + 1][0] - nw[k][0]), nw[k][1] + t * (nw[k + 1][1] - nw[k][1]))
        return c, b

    s_along = L - hub["value_m"]
    centre, site = on_bank(s_along)
    lo_along, hi_along = L - (hub["value_m"] + hub["band_m"]), L - (hub["value_m"] - hub["band_m"])
    reach = [loc(on_bank(lo_along)[1])]
    seg_lo = point_at(pts, cum, lo_along)[1]
    seg_hi = point_at(pts, cum, hi_along)[1]
    for k in range(seg_lo + 1, seg_hi + 1):
        reach.append(loc(rv["nw"][k - rv["i_trace"]]))
    reach.append(loc(on_bank(hi_along)[1]))

    fort_site = math.hypot(site[0] - anchor[0], site[1] - anchor[1])
    tests = []

    h = P["heald_three_miles_from_the_garrison"]
    tests.append({
        "placing": h["id"], "source_id": h["source_id"],
        "says": "about three miles from the garrison",
        "straight_line_fort_to_site_m": r1(fort_site),
        "straight_line_fort_to_site_mi": miles(fort_site, mile),
        "by_river_fort_to_site_m": r1(s_along - rv["legs"]["mouth_to_fort_anchor_m"]),
        "by_river_fort_to_site_mi": miles(s_along - rv["legs"]["mouth_to_fort_anchor_m"], mile),
        "band_mi": [miles(h["value_m"] - h["band_m"], mile), miles(h["value_m"] + h["band_m"], mile)],
        "site_inside_band": abs(fort_site - h["value_m"]) <= h["band_m"],
        "verdict": "agrees" if abs(fort_site - h["value_m"]) <= h["band_m"] else "differs",
        "reading": "Read as a straight line. The river route from the fort is printed beside it "
                   "and is longer, because it goes round by the forks.",
    })

    c = P["currey_at_the_canal_mouth"]
    fb = dist(anchor, bridgeport)
    tests.append({
        "placing": c["id"], "source_id": c["source_id"],
        "says": "some four miles southwest of the fort ... about where ... the canal opens into that stream",
        "straight_line_fort_to_bridgeport_m": r1(fb),
        "straight_line_fort_to_bridgeport_mi": miles(fb, mile),
        "bearing_fort_to_bridgeport_deg": bearing(anchor, bridgeport),
        "bridgeport_inside_band": abs(fb - c["value_m"]) <= c["band_m"],
        "site_from_currey_point_m": r1(dist(site, bridgeport)),
        "site_from_currey_point_by_river_m": r1(L - s_along),
        "verdict": "differs",
        "reading": "Currey's point is the canal's mouth itself. His four miles south-west of "
                   "the fort agrees with it (the bearing is the compass's south-west quadrant), "
                   "so this placing and Hubbard's differ by Hubbard's half mile, measured along the "
                   "river. That gap is the disagreement, and 'about where' is Currey's own hedge.",
    })

    m = P["currey_four_miles_from_the_mouth"]
    at4, _, _ = point_at(pts, cum, min(m["value_m"], L))
    tests.append({
        "placing": m["id"], "source_id": m["source_id"],
        "says": "some four miles from the mouth of the river",
        "by_river_mouth_to_site_m": r1(s_along),
        "by_river_mouth_to_site_mi": miles(s_along, mile),
        "by_river_mouth_to_bridgeport_mi": miles(L, mile),
        "band_mi": [miles(m["value_m"] - m["band_m"], mile), miles(m["value_m"] + m["band_m"], mile)],
        "site_inside_band": abs(s_along - m["value_m"]) <= m["band_m"],
        "four_miles_falls_at_local": loc(at4),
        "four_miles_falls_short_of_site_m": r1(s_along - m["value_m"]),
        "straight_line_mouth_to_site_mi": miles(dist(rv["outlet"], site), mile),
        "straight_line_mouth_to_bridgeport_mi": miles(dist(rv["outlet"], bridgeport), mile),
        "verdict": "agrees" if abs(s_along - m["value_m"]) <= m["band_m"] else "differs",
        "reading": "Measured along the river from the 1812 outlet, up the old channel, along the "
                   "main stem and down the South Branch. The chord across the forks window makes "
                   "this a slight under-measure, so the true river distance is a little longer "
                   "still. By river, four miles from the mouth does not reach the site, nor "
                   "Currey's own canal mouth: it falls at the box floor, about a mile short of "
                   "both. In a straight line from the outlet, the site is under three miles and "
                   "the canal's mouth about three and a half. So the caption's four miles fits "
                   "neither measure of either point, and the reading most like it is the text's "
                   "own four miles from the fort, repeated with a different starting point. "
                   "This is recorded as a disagreement and not resolved.",
    })

    k = P["moses_kirkland_near_the_forks"]
    tests.append({
        "placing": k["id"], "source_id": k["source_id"],
        "says": "on the northwestern side of the South branch, near its forks",
        "site_below_forks_by_river_m": r1(along_forks - s_along),
        "site_from_forks_straight_m": r1(dist(site, forks)),
        "side_agrees": True,
        "verdict": "agrees",
        "reading": "The site is on the north-west bank by construction, because it is Hubbard's "
                   "'north side', and this is that same bank. 'Near its forks' sets no distance; "
                   "the figure above is how far from the traced forks the station lies.",
    })

    return {
        "_doc": "GENERATED by tools/derive_hardscrabble_1812.py from data/terrain/1812_hardscrabble_readings.json "
                "and the committed river lines it names - do not hand-edit; --check re-derives it. Lee's Place "
                "(later Hardscrabble) is placed here as a STATION and a REACH of the South Branch's north-west "
                "bank, never as a point claimed for the cabin. T-2503 builds on this reach, and T-2502 carries "
                "the 1812 ground down to it.",
        "ticket": "T-2501",
        "parent": "T-2488",
        "address_date": readings["address_date"],
        "river": {
            "legs_m": rv["legs"],
            "length_mouth_to_bridgeport_m": r1(L),
            "length_mouth_to_bridgeport_mi": miles(L, mile),
            "note": "Along the old channel's west bank and the main stem's south bank from the 1812 "
                    "outlet, across the forks window on a straight chord, then down the South "
                    "Branch's centre. The South Branch is Wright 1834 to N -2110, then Rees 1849 to "
                    "40 m below the box floor, then T-2501's Rees 1849 trace to the canal.",
        },
        "bridgeport": {"local": loc(bridgeport), "utm": utm(bridgeport),
                       "note": "Where the canal opens into the river's south fork on Rees & Rucker "
                               "1849. That is the trace's last vertex, picked by eye to +/-8 px "
                               "(about 16 m)."},
        "forks": {"local": loc(forks), "utm": utm(forks),
                  "below_bridgeport_by_river_m": r1(L - along_forks),
                  "note": "The trace's vertex nearest the picked junction of the west and south forks."},
        "site": {
            "station": "half a mile below Bridgeport by river, on the north-west bank",
            "along_river_below_bridgeport_m": r1(L - s_along),
            "along_river_from_mouth_m": r1(s_along),
            "centreline_local": loc(centre),
            "local": loc(site),
            "utm": utm(site),
            "reach_nw_bank_local": reach,
            "reach_below_bridgeport_m": [r1(L - hi_along), r1(L - lo_along)],
            "confidence": "inferred",
            "adopted_from": hub["id"],
            "uncertainty": "The reach is the stretch of bank that Hubbard's 'about half a mile' "
                           "allows: 0.25 to 0.75 mi below Bridgeport. Beyond it, the Rees 1849 "
                           "georeference carries 25.0 m RMS (35.7 m worst), and the sheet is 37 "
                           "years after the farm.",
            "note": "The station is the river point half a mile downstream of the canal's mouth, "
                    "carried across to the north-west bank along the trace's own normal. The "
                    "field lay back from that bank, and the cabin's place on it is T-2503's.",
        },
        "tests": tests,
        "agreement": {
            "agree": [t["placing"] for t in tests if t["verdict"] == "agrees"],
            "differ": [t["placing"] for t in tests if t["verdict"] == "differs"],
            "disagreement": "Currey's text puts the farm AT the canal's mouth, and Hubbard puts it "
                            "half a mile below. The reach adopted is Hubbard's. It comes no "
                            "closer to the canal than a quarter mile, so Currey's point lies "
                            "outside it. Currey's caption measures four miles from the mouth, and "
                            "by river that falls about a mile short of both points. Heald's three "
                            "miles from the garrison, and Moses and Kirkland's north-west bank near "
                            "the forks, both agree with the adopted site. No placing puts the farm "
                            "on the other bank.",
        },
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
                  "run tools/derive_hardscrabble_1812.py")
            return 1
        print(f"ok: {OUT.relative_to(ROOT)} re-derives from its readings")
        return 0
    OUT.write_text(text, encoding="utf-8")
    d = json.loads(text)
    print(f"wrote {OUT.relative_to(ROOT)}: site {d['site']['local']} local, "
          f"{d['site']['along_river_below_bridgeport_m']} m below Bridgeport; "
          f"river mouth->Bridgeport {d['river']['length_mouth_to_bridgeport_mi']} mi")
    for t in d["tests"]:
        print("  ", json.dumps(t)[:400])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
