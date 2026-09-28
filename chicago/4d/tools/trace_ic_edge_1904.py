#!/usr/bin/env python3
"""Trace the Illinois Central lake edge the 1904 Prairie Avenue scene stands on (T-1250).

    python3 tools/trace_ic_edge_1904.py                    re-trace and write
    python3 tools/trace_ic_edge_1904.py --check            re-trace and diff (needs Pillow + numpy)
    python3 tools/trace_ic_edge_1904.py --check-properties hold the committed file together,
                                                           no raster, no numpy

Writes data/terrain/epochs/e1871_postfire/shoreline.geojson, the geometry of the
shoreline state `shore_1880s_ic_edge` (data/terrain/shoreline_states.json), which
addresses 1 July 1904 on the owner's ruling of 2026-09-26.

THE SHEETS, AND WHAT EACH ONE IS ALLOWED TO BE
----------------------------------------------
Two dates bracket 1904 and neither is it. Sanborn's 1911 Chicago vol. 3 draws the
water's edge beside the Illinois Central / Michigan Central tracks on sheet 20
(from the 16th Street row south about 60 m) and on sheet 28 (from 40 m north of
18th Street to 80 m south of it) -- as a firm pen line with the lake's blue wash
against its east side, and it stops drawing it there although the tracks run on.
Robinson's 1886 atlas, plate 10, draws the same edge the whole way from above
16th Street to 18th, as the west limit of its water-lining. Both sheets are
georeferenced by tools/georef_prairie_1904.py (GCP files in data/traces/gcp/).

MEASURED, NOT ASSUMED: THE EDGE MOVED EAST BETWEEN 1886 AND 1911. Over both
reaches where the two draw it the 1911 line stands 14-21 m east of the 1886 one,
and the two fits put no more than about 5 m of that in doubt. The Illinois
Central widened its right-of-way into the lake between the two sheets. So the
1904 water's edge stood somewhere in that band, and this file does what the house
rule says (shoreline_states.json, _doc): the spread is kept as a named band and
nothing is averaged.

BOTH SHEETS ARE BOUNDS, AND THE SCENE'S LINE IS A RECONSTRUCTION BETWEEN THEM
------------------------------------------------------------------------------
The house rule (shoreline_states.json, _doc) is that an observation from the wrong
date may bound a state and may not become its adopted line, and the ticket says it
of these two sheets in so many words. So both are written as DATED LINES with a
bounding role: 1886 from before (the 1904 edge stood on it or east of it) and 1911
from after (on it or west of it). The second bound rests on one inference, stated:
the edge beside the railway is a BUILT edge, the breakwater of the right-of-way,
and between two dates a built edge only moves lakeward unless something is taken
out -- and nothing in this corpus records a removal.

A scene still needs one waterline, so `shore_1904_ic_edge` is one, written
RECONSTRUCTED, never attested or inferred, and recorded as a liberty
(docs/LIBERTIES.md). It stands on the band's EASTERN, 1911, bound because:

 1. the 1911 sheets are seven years from the scene; the 1886 plate is eighteen;
 2. Glessner House, who supplied the sheets, reads everything on sheets 20, 28 and
    35 as standing in 1904 except two houses (chicago/reference/prairie-avenue/
    sanborn-1911-and-robinson-1886/README.md) -- attributed guidance about these
    sheets, recorded as such and not checked here;
 3. a midpoint would be an average, which the rule forbids, and the western bound
    would put the scene on an edge eighteen years stale.

Where the 1911 sheets do not draw the edge the line says what stands in, segment by
segment:

  A  north of the sheet 20 run     the 1886 line carried east by the offset the two
                                   sheets measure at the north overlap
  B  sheet 20's own run            on the 1911 bound
  C  between the two 1911 runs     the 1886 line carried east by an offset that
                                   runs linearly from the north overlap's mean to
                                   the south overlap's -- the 1886 PLANFORM, moved
                                   by two measurements, not a midpoint
  D  sheet 28's own run            on the 1911 bound
  E  south of the sheet 28 run     the run carried straight on to where the tracks
     to the neatline               leave the sheet: the easternmost drawn track runs
                                   parallel to the edge at a measured offset the
                                   whole length of the run, and on, straight, to
                                   the paper's edge
  F  on to the box floor           the same bearing, and nothing else: no sheet
                                   held here reaches Cermak Road east of Calumet

WHAT IS REFUSED. The modern Metra / Canadian National corridor is not a proxy for
the 1904 edge and nothing here reads it: at 18th Street its easternmost track
stands 78 m EAST of the 1911 water's edge, on the lakefill of the 1920s.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
RASTERS = REPO / "chicago" / "reference" / "prairie-avenue" / "sanborn-1911-and-robinson-1886"
GCP_DIR = ROOT / "data" / "traces" / "gcp"
OUT = ROOT / "data" / "terrain" / "epochs" / "e1871_postfire" / "shoreline.geojson"
DATUM = json.loads((ROOT / "data" / "datum.json").read_text(encoding="utf-8"))
OE, ON = DATUM["origin_utm_e"], DATUM["origin_utm_n"]

# The reach the 1904 terrain box covers (T-1251's spec states the same box; this
# file only has to span it).
BOX_N = (-3800.0, -2900.0)

# Sanborn: the rows each run is read over, and the column window searched.
SANBORN_RUNS = {
    "sanborn_1911_v3_sheet_20": {"raster": "sanborn_1911_vol3_sheet_20.jpg", "rows": (1120, 3000)},
    "sanborn_1911_v3_sheet_28": {"raster": "sanborn_1911_vol3_sheet_28.jpg", "rows": (150, 3200)},
}
ROW_STEP = 25
COL_FROM = 4400
# Sheet 28: rows at which the easternmost track and the edge are both drawn, and
# the rows below the run at which the track alone is.
TRACK_ROWS_WITH_EDGE = (1200, 1500, 1800, 2100, 2400)
TRACK_ROWS_BELOW = (2900, 3100, 3300, 3500, 3700)
ROBINSON = {"raster": "robinson_1886_plate_10.jpg", "rows": (260, 1790), "step": 10, "col_from": 560}

SOURCES = {
    "sanborn_1911_v3_sheet_20": "sanborn_1911_chicago_v3_sheet_20",
    "sanborn_1911_v3_sheet_28": "sanborn_1911_chicago_v3_sheet_28",
    "robinson_1886_plate_10": "robinson_1886_chicago_plate_10",
}


def fit_of(key: str):
    c = json.loads((GCP_DIR / f"{key}_gcps.json").read_text(encoding="utf-8"))["fit"]["coefficients"]
    return lambda x, y: (c["a"] * x + c["b"] * y + c["c"], c["d"] * x + c["e"] * y + c["f"])


# ---------------------------------------------------------------------------
# reading the rasters

def load_rgb(name: str):
    import numpy as np
    from PIL import Image
    Image.MAX_IMAGE_PIXELS = None
    return np.asarray(Image.open(RASTERS / name).convert("RGB"))     # uint8; rows are widened as read


def trace_sanborn(im, rows: tuple[int, int]) -> list[tuple[float, int]]:
    """The pen line with the lake's blue wash on its east side, row by row."""
    import numpy as np
    pts, miss = [], 0
    for y in range(rows[0], rows[1], ROW_STEP):
        row = im[y - 2:y + 3].astype(float).mean(axis=0)
        blue = row[:, 2] - row[:, 0]
        dark = 255 - row.mean(axis=1)
        x = None
        for c in range(COL_FROM, im.shape[1] - 25):
            # 12 px of pale blue wash, with a dark stroke in the 12 px before it
            if blue[c:c + 12].min() > -22 and dark[c:c + 12].max() < 90 and dark[c - 12:c].max() > 150:
                x = c
                break
        if x is None:
            miss += 1
            if pts and miss > 8:
                break
            continue
        miss = 0
        lo = x - 25
        seg = np.clip(dark[lo:x + 3] - 120, 0, None)
        if seg.sum() == 0:
            continue
        pts.append((round(float((np.arange(lo, x + 3) * seg).sum() / seg.sum()), 1), y))
    return pts


def track_lines(im, y: int, x_lo: int = 3500, x_hi: int = 5800) -> list[int]:
    row = 255 - im[y - 2:y + 3].astype(float).mean(axis=0).mean(axis=1)
    xs = []
    for x in range(x_lo, x_hi):
        if row[x] > 110 and row[x] >= row[x - 1] and row[x] >= row[x + 1]:
            if not xs or x - xs[-1] > 6:
                xs.append(x)
    return xs


def trace_robinson(im) -> list[tuple[float, int]]:
    """The west limit of the water-lining: the first place, scanning east past the
    tracks, where five or more separate pen lines fall inside 22 px with a clear
    6 px west of the first of them. Robust line fit, then a running median."""
    import numpy as np
    g = 255 - im.astype(float).mean(axis=2)
    cands = []
    for y in range(ROBINSON["rows"][0], ROBINSON["rows"][1], ROBINSON["step"]):
        row = g[y - 1:y + 2].mean(axis=0)
        d = row > 50
        starts = [i for i in range(1, len(d)) if d[i] and not d[i - 1]]
        for k, p in enumerate(starts):
            if p < ROBINSON["col_from"]:
                continue
            if len([q for q in starts[k:] if q < p + 22]) >= 5 and not d[max(0, p - 6):p].any():
                e = p
                while e < len(d) and d[e]:
                    e += 1
                seg = row[p:e]
                cands.append(((np.arange(p, e) * seg).sum() / seg.sum(), y))
                break
    arr = np.array(cands)
    keep = np.ones(len(arr), bool)
    for _ in range(5):
        coef = np.polyfit(arr[keep, 1], arr[keep, 0], 1)
        res = arr[:, 0] - np.polyval(coef, arr[:, 1])
        keep = np.abs(res) < max(4.0, 2.5 * float(np.std(res[keep])))
    arr = arr[keep]
    xs = arr[:, 0]
    med = [float(np.median(xs[max(0, i - 2):i + 3])) for i in range(len(xs))]
    return [(round(m, 1), int(y)) for m, y in zip(med, arr[:, 1])]


# ---------------------------------------------------------------------------
# geometry in the local frame

def to_local(key: str, pts: list[tuple[float, float]]) -> list[tuple[float, float]]:
    f = fit_of(key)
    return [f(x, y) for x, y in pts]


def e_at(line: list[tuple[float, float]], n: float) -> float | None:
    for (e1, n1), (e2, n2) in zip(line, line[1:]):
        if (n1 - n) * (n2 - n) <= 0 and n1 != n2:
            return e1 + (e2 - e1) * (n - n1) / (n2 - n1)
    return None


def stations(lo: float, hi: float, step: float = 10.0) -> list[float]:
    """N stations from hi (north) down to lo, on a 10 m grid."""
    out, n = [], math.floor(hi / step) * step
    while n >= lo:
        out.append(round(n, 1))
        n -= step
    return out


def r1(v: float) -> float:
    return round(v + 0.0, 1)


def utm(e: float, n: float) -> list[float]:
    return [round(OE + e, 2), round(ON + n, 2)]


def build(readings: dict) -> dict:
    """Everything below is arithmetic on the readings; no raster is touched."""
    l20 = to_local("sanborn_1911_v3_sheet_20", readings["sanborn_1911_v3_sheet_20"])
    l28 = to_local("sanborn_1911_v3_sheet_28", readings["sanborn_1911_v3_sheet_28"])
    l86 = to_local("robinson_1886_plate_10", readings["robinson_1886_plate_10"])

    def overlap(l11):
        n_hi, n_lo = min(l11[0][1], l86[0][1]), max(l11[-1][1], l86[-1][1])
        st = [n for n in stations(n_lo, n_hi) if e_at(l11, n) is not None and e_at(l86, n) is not None]
        e11 = [r1(e_at(l11, n)) for n in st]
        e86 = [r1(e_at(l86, n)) for n in st]
        off = [r1(a - b) for a, b in zip(e11, e86)]
        return {"stations_n_m": st, "e_1911_m": e11, "e_1886_m": e86, "offset_m": off,
                "mean_offset_m": r1(sum(off) / len(off)), "min_offset_m": min(off), "max_offset_m": max(off)}

    ov_n, ov_s = overlap(l20), overlap(l28)
    off_n, off_s = ov_n["mean_offset_m"], ov_s["mean_offset_m"]
    n20_s, n28_n = l20[-1][1], l28[0][1]

    # E: sheet 28's run carried straight on -- the least-squares line through its
    # southern half, which is where it is parallel to the drawn track
    half = [p for p in l28 if p[1] <= (l28[0][1] + l28[-1][1]) / 2]
    mn = sum(p[1] for p in half) / len(half)
    me = sum(p[0] for p in half) / len(half)
    slope = sum((p[1] - mn) * (p[0] - me) for p in half) / sum((p[1] - mn) ** 2 for p in half)   # dE/dN
    f28 = fit_of("sanborn_1911_v3_sheet_28")
    n_neat = f28(readings["track"]["neatline_px"][0], readings["track"]["neatline_px"][1])[1]

    segs = []
    coords: list[tuple[float, float]] = []

    def add(e, n):
        if not coords or abs(coords[-1][1] - n) > 0.05:
            coords.append((r1(e), r1(n)))

    # A
    for n in stations(l20[0][1] + 0.05, BOX_N[1]):
        add(e_at(l86, n) + off_n, n)
    segs.append({"id": "A", "n_from": BOX_N[1], "n_to": r1(l20[0][1]), "confidence": "reconstructed",
                 "basis": f"Robinson 1886's line carried {off_n} m east, the mean offset between the two sheets over "
                          "sheet 20's run; the 1911 sheet draws nothing north of the 16th Street row"})
    # B
    for e, n in l20:
        add(e, n)
    segs.append({"id": "B", "n_from": r1(l20[0][1]), "n_to": r1(n20_s), "confidence": "reconstructed",
                 "basis": "on the band's eastern bound: the 1911 edge traced off Sanborn sheet 20",
                 "source_id": SOURCES["sanborn_1911_v3_sheet_20"]})
    # C
    for n in stations(n28_n + 0.05, n20_s - 0.05):
        t = (n - n20_s) / (n28_n - n20_s)
        add(e_at(l86, n) + off_n + t * (off_s - off_n), n)
    segs.append({"id": "C", "n_from": r1(n20_s), "n_to": r1(n28_n), "confidence": "reconstructed",
                 "basis": f"neither 1911 sheet draws the edge here. Robinson 1886's planform, carried east by an offset "
                          f"running linearly from {off_n} m (the north overlap's mean) to {off_s} m (the south's)"})
    # D
    for e, n in l28:
        add(e, n)
    segs.append({"id": "D", "n_from": r1(n28_n), "n_to": r1(l28[-1][1]), "confidence": "reconstructed",
                 "basis": "on the band's eastern bound: the 1911 edge traced off Sanborn sheet 28",
                 "source_id": SOURCES["sanborn_1911_v3_sheet_28"]})
    # E
    e_end, n_end = l28[-1]
    for n in stations(n_neat, n_end - 0.05) + [r1(n_neat)]:
        add(e_end + slope * (n - n_end), n)
    segs.append({"id": "E", "n_from": r1(n_end), "n_to": r1(n_neat), "confidence": "reconstructed",
                 "basis": "sheet 28's run carried straight on to where its easternmost drawn track reaches the paper's "
                          "edge: that track runs parallel to the edge at the measured offset the whole length of the "
                          "run and straight on below it (see measured.track_parallel)"})
    # F
    for n in stations(BOX_N[0], n_neat - 0.05) + [BOX_N[0]]:
        add(e_end + slope * (n - n_end), n)
    segs.append({"id": "F", "n_from": r1(n_neat), "n_to": BOX_N[0], "confidence": "reconstructed",
                 "unbounded": True,
                 "basis": "the same bearing to the box floor and nothing else: no sheet this project holds draws the "
                          "lake east of Calumet Avenue between 20th Street and Cermak Road, so no band bounds it"})

    tp = readings["track"]
    band_rings = []
    for ov in (ov_n, ov_s):
        west = [utm(e, n) for n, e in zip(ov["stations_n_m"], ov["e_1886_m"])]
        east = [utm(e, n) for n, e in reversed(list(zip(ov["stations_n_m"], ov["e_1911_m"])))]
        band_rings.append([west + east + [west[0]]])

    def line_feature(fid, name, key, local, observed, note):
        return {"type": "Feature", "id": fid,
                "properties": {"kind": "lake_edge_observation", "name": name, "observed_date": observed,
                               "confidence": "attested",
                               "confidence_note": f"attested for {observed[:4]}, the date of the sheet it is traced off; "
                                                  "for 1904 it is an observation from the wrong date, and a bound",
                               "sources": [SOURCES[key]], "gcp_file": f"data/traces/gcp/{key}_gcps.json",
                               "note": note},
                "geometry": {"type": "LineString", "coordinates": [utm(e, n) for e, n in local]}}

    feats = [
        {"type": "Feature", "id": "shore_1904_ic_edge",
         "properties": {"kind": "shore", "role": "scene_line",
                        "name": "Lake Michigan's edge beside the Illinois Central, 1 July 1904",
                        "address_date": "1904-07-01", "confidence": "reconstructed",
                        "confidence_note": ("reconstructed inside the band the 1886 and 1911 sheets bound (segments "
                                            "A-E) and past the last sheet on a bearing alone (F, unbounded)"),
                        "liberty": "L287",
                        "segments": segs,
                        "sources": sorted(SOURCES.values()),
                        "note": ("The waterline the 1904 scene renders. On the band's eastern (1911) bound where "
                                 "either 1911 sheet draws the edge, and elsewhere the 1886 planform moved by the offsets "
                                 "the two sheets measure where both draw it -- see the tool's docstring for why the "
                                 "eastern bound, and ic_edge_1886_1911_band for how far apart the bounds are.")},
         "geometry": {"type": "LineString", "coordinates": [utm(e, n) for e, n in coords]}},
        line_feature("ic_edge_1911_sheet_20", "Lake edge, Sanborn 1911 sheet 20", "sanborn_1911_v3_sheet_20", l20,
                     "1911-01-01", "the pen line with the lake's blue wash east of it, from the ruled line on the 16th "
                     "Street row -- which this trace does not read as shore -- south until the sheet stops drawing it"),
        line_feature("ic_edge_1911_sheet_28", "Lake edge, Sanborn 1911 sheet 28", "sanborn_1911_v3_sheet_28", l28,
                     "1911-01-01", "the same pen line and wash, from near the top of the sheet until it stops"),
        line_feature("ic_edge_1886_plate_10", "Lake edge, Robinson 1886 plate 10", "robinson_1886_plate_10", l86,
                     "1886-01-01", "the west limit of the plate's water-lining. It BOUNDS the 1904 edge from before; "
                     "its planform, moved east, stands in for the 1911 bound in segments A and C"),
        {"type": "Feature", "id": "ic_edge_1886_1911_band",
         "properties": {"kind": "shoreline_source_disagreement_band", "state_id": "shore_1880s_ic_edge",
                        "resolution": "scene_line_on_eastern_bound", "adopted_line": None, "adopted_midpoint": None,
                        "eastern_bound": ["ic_edge_1911_sheet_20", "ic_edge_1911_sheet_28"],
                        "western_bound": "ic_edge_1886_plate_10",
                        "sources": sorted(SOURCES.values()),
                        "spread_m": {"north_overlap": {k: ov_n[k] for k in ("min_offset_m", "mean_offset_m", "max_offset_m")},
                                     "south_overlap": {k: ov_s[k] for k in ("min_offset_m", "mean_offset_m", "max_offset_m")}},
                        "note": ("Everything between the 1886 and the 1911 water's edge over the two reaches where both "
                                 "draw it. The 1904 edge stood inside it. Kept as a band; not averaged.")},
         "geometry": {"type": "MultiPolygon", "coordinates": band_rings}},
    ]
    return {
        "type": "FeatureCollection",
        "name": "e1871_postfire_shoreline",
        "crs": {"type": "name", "properties": {"name": "urn:ogc:def:crs:EPSG::26916"}},
        "_doc": ("GENERATED by tools/trace_ic_edge_1904.py -- do not hand-edit. The lake edge the 1904 Prairie Avenue "
                 "scene stands on (shoreline state shore_1880s_ic_edge, T-1250), traced off Sanborn 1911 vol. 3 sheets 20 "
                 "and 28 and Robinson 1886 plate 10, each georeferenced by tools/georef_prairie_1904.py. The tool's "
                 "docstring carries the argument; `measured` carries the numbers it rests on."),
        "measured": {
            "north_overlap_sheet_20_vs_1886": ov_n,
            "south_overlap_sheet_28_vs_1886": ov_s,
            "track_parallel": {
                "what": ("sheet 28: the edge's column minus the easternmost drawn track's, at rows where both are drawn, "
                         "and the track's column below the run against the run's straight continuation less that "
                         "mean offset"),
                "rows_with_edge": list(TRACK_ROWS_WITH_EDGE), "offset_px": tp["offset_px"],
                "mean_offset_px": r1(sum(tp["offset_px"]) / len(tp["offset_px"])),
                "rows_below_run": list(TRACK_ROWS_BELOW), "track_departure_px": tp["departure_px"],
                "neatline_px": tp["neatline_px"],
            },
            "segment_E_bearing_deg_east_of_south": r1(math.degrees(math.atan(-slope))),
            "refused_proxy": ("the modern Metra / Canadian National corridor's easternmost track stands 78 m east of "
                              "the 1911 edge at 18th Street (OpenStreetMap, 2026), on the 1920s lakefill; it is read "
                              "for nothing here"),
        },
        "features": feats,
    }


def read_all() -> dict:
    out = {}
    for key, spec in SANBORN_RUNS.items():
        im = load_rgb(spec["raster"])
        out[key] = trace_sanborn(im, spec["rows"])
        if key == "sanborn_1911_v3_sheet_28":
            edge = {y: x for x, y in out[key]}
            offs = []
            for y in TRACK_ROWS_WITH_EDGE:
                ex = min(edge.items(), key=lambda kv: abs(kv[0] - y))
                ex_x = ex[1] + (y - ex[0]) * 0.297          # carry the edge to the row at its own slope
                tr = [x for x in track_lines(im, y) if x < ex_x - 15]
                offs.append(r1(ex_x - tr[-1]))
            mean_off = sum(offs) / len(offs)
            xs = [p[0] for p in out[key] if p[1] >= (out[key][0][1] + out[key][-1][1]) / 2]
            ys = [p[1] for p in out[key] if p[1] >= (out[key][0][1] + out[key][-1][1]) / 2]
            my, mx = sum(ys) / len(ys), sum(xs) / len(xs)
            k = sum((a - my) * (b - mx) for a, b in zip(ys, xs)) / sum((a - my) ** 2 for a in ys)
            dep = []
            for y in TRACK_ROWS_BELOW:
                want = mx + k * (y - my) - mean_off
                tr = track_lines(im, y, 4800, 5800)
                near = min(tr, key=lambda x: abs(x - want))
                dep.append(r1(near - want))
            # the row at which the easternmost track, carried on, meets the paper's edge (the neatline
            # column, read off the sheet), and where the carried EDGE stands on that row
            neat_x = 5829.0
            edge_x = neat_x + mean_off
            neat_y = my + (edge_x - mx) / k
            out["track"] = {"offset_px": offs, "departure_px": dep,
                            "neatline_px": [round(edge_x, 1), round(neat_y, 1)]}
    out["robinson_1886_plate_10"] = trace_robinson(load_rgb(ROBINSON["raster"]))
    return out


def dumps(doc: dict) -> str:
    return json.dumps(doc, indent=1, ensure_ascii=False) + "\n"


def check_properties(doc: dict) -> list[str]:
    """Offline: the committed file holds together without a raster."""
    bad = []
    feats = {f["id"]: f for f in doc.get("features", [])}
    need = {"shore_1904_ic_edge", "ic_edge_1911_sheet_20", "ic_edge_1911_sheet_28", "ic_edge_1886_plate_10",
            "ic_edge_1886_1911_band"}
    if set(feats) != need:
        return [f"features are {sorted(feats)}, expected {sorted(need)}"]
    line = feats["shore_1904_ic_edge"]
    coords = line["geometry"]["coordinates"]
    ns = [c[1] - ON for c in coords]
    if any(b >= a for a, b in zip(ns, ns[1:])):
        bad.append("the adopted line does not run strictly north to south")
    if abs(ns[0] - BOX_N[1]) > 0.06 or abs(ns[-1] - BOX_N[0]) > 0.06:
        bad.append("the adopted line does not span the box from N -2900 to N -3800")
    segs = line["properties"]["segments"]
    if [s["id"] for s in segs] != list("ABCDEF"):
        bad.append("the adopted line's segments are not A-F in order")
    for a, b in zip(segs, segs[1:]):
        if a["n_to"] != b["n_from"]:
            bad.append(f"segments {a['id']} and {b['id']} do not abut")
    if not segs[-1].get("unbounded"):
        bad.append("segment F, which no sheet reaches, does not say it is unbounded")
    if any(s["confidence"] != "reconstructed" for s in segs) or line["properties"].get("confidence") != "reconstructed":
        bad.append("the 1904 scene line claims more than reconstructed; both sheets are of the wrong date and bound it")
    if not line["properties"].get("liberty"):
        bad.append("the 1904 scene line names no liberty")
    band = feats["ic_edge_1886_1911_band"]["properties"]
    if band.get("adopted_midpoint") is not None or band.get("adopted_line") is not None:
        bad.append("the 1886/1911 spread was resolved to a midpoint or to one of its readings")
    for k in ("north_overlap", "south_overlap"):
        sp = band["spread_m"][k]
        if not 0 < sp["min_offset_m"] <= sp["mean_offset_m"] <= sp["max_offset_m"] < 40:
            bad.append(f"the {k} spread {sp} is not a positive eastward shift of plausible size")
    # every vertex of the adopted line on segments B and D is a vertex of the traced 1911 line
    for fid, seg in (("ic_edge_1911_sheet_20", "B"), ("ic_edge_1911_sheet_28", "D")):
        traced = {tuple(c) for c in feats[fid]["geometry"]["coordinates"]}
        s = next(x for x in segs if x["id"] == seg)
        on = [tuple(c) for c in coords if s["n_to"] <= c[1] - ON <= s["n_from"]]
        # the adopted line is rounded to 0.1 m in the local frame; compare within 0.1 m
        for c in on[1:-1]:
            if not any(abs(c[0] - t[0]) < 0.11 and abs(c[1] - t[1]) < 0.11 for t in traced):
                bad.append(f"segment {seg} carries a vertex that is not on {fid}")
                break
    return bad


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--check-properties", action="store_true")
    args = ap.parse_args()
    if args.check_properties or args.check:
        if not OUT.exists():
            print(f"FAIL {OUT.relative_to(ROOT)} is missing")
            return 1
        doc = json.loads(OUT.read_text(encoding="utf-8"))
        bad = check_properties(doc)
        if args.check:
            try:
                import numpy  # noqa: F401
                from PIL import Image  # noqa: F401
            except ImportError:
                print("WARN Pillow/numpy absent: the sheets were not re-read; holding the committed file together only")
            else:
                if OUT.read_text(encoding="utf-8") != dumps(build(read_all())):
                    bad.append("the committed shoreline is not what a re-trace of the three sheets writes")
        for b in bad:
            print("FAIL", b)
        if not bad:
            m = doc["measured"]
            print(f"OK the 1904 IC edge holds: 1911 stands {m['north_overlap_sheet_20_vs_1886']['mean_offset_m']} m / "
                  f"{m['south_overlap_sheet_28_vs_1886']['mean_offset_m']} m east of 1886 at the two overlaps; "
                  "the scene line is reconstructed inside that band" + (", re-traced from the sheets" if args.check else ""))
        return 1 if bad else 0
    doc = build(read_all())
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(dumps(doc), encoding="utf-8")
    m = doc["measured"]
    print(json.dumps({k: v for k, v in m.items() if k != "refused_proxy"}, indent=1))
    for s in doc["features"][0]["properties"]["segments"]:
        print(s["id"], s["n_from"], s["n_to"], s["confidence"])
    bad = check_properties(doc)
    for b in bad:
        print("FAIL", b)
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
