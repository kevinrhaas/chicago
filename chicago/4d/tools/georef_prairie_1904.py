#!/usr/bin/env python3
"""Georeference the four Prairie Avenue sheets (T-1250) and publish their GCP files.

    python3 tools/georef_prairie_1904.py            # (re)write the four GCP files
    python3 tools/georef_prairie_1904.py --check    # re-derive, change nothing
    python3 tools/georef_prairie_1904.py --self-test

The sheets are the ones Glessner House supplied for the 1904 Prairie Avenue model,
committed at chicago/reference/prairie-avenue/sanborn-1911-and-robinson-1886/:

    Sanborn, Chicago vol. 3 (1911), sheets 20, 28 and 35
    Robinson's Atlas of the City of Chicago (1886), plate 10

and the outputs sit beside every other fitted sheet in this corpus, in
data/traces/gcp/, so the streets (T-0474), the Glessner House (T-1729) and anything
else that later reads a footprint off these sheets starts from the same transform:

    data/traces/gcp/sanborn_1911_v3_sheet_20_gcps.json
    data/traces/gcp/sanborn_1911_v3_sheet_28_gcps.json
    data/traces/gcp/sanborn_1911_v3_sheet_35_gcps.json
    data/traces/gcp/robinson_1886_plate_10_gcps.json

What is the same as rees_rucker_1849_gcps.json, and what is not
----------------------------------------------------------------
The same: pixel control picked on the sheet, modern control from OpenStreetMap
crossings reduced to EPSG:26916 and the local frame (data/traces/prairie_1904_control.json),
a least-squares fit, coefficients in the same a..f form, a residual per point and an
RMS. The four rasters ARE committed here (the Rees sheet is not), so every pixel
below can be re-read, and --check verifies their sha256 before it trusts a pick.

NOT the same: THE ADOPTED TRANSFORM IS A SIMILARITY AT THE SHEET'S OWN PRINTED SCALE,
not a free affine, and the free affine is fitted and printed beside it so the reason
is on the page. On sheet 20 the free affine comes out with a 5.6 per cent difference
between its two axis scales. The sheet itself says that is false twice over: its
printed Scale of Feet and its 66-ft street bands, measured in both directions, agree
to about one per cent. What the affine is reading as paper stretch is the modern
street net: South Indiana Avenue's modern centreline stands 5-8 m EAST of the
Indiana Avenue both the 1886 plate and the 1911 sheet draw (Indiana to Prairie is
442 ft on the Sanborn -- two 178-ft lot tiers, a 20-ft alley and two half-streets --
and 126.8-129.4 m in OpenStreetMap), and Cermak Road today, a divided carriageway,
stands about 10 m SOUTH of the Twenty-Second Street sheet 35 draws. A four-point
affine cannot tell a displaced street from a stretched sheet, so it bends the sheet
to fit the street, and 200 m east of Prairie -- where the Illinois Central lake edge
is -- that bend is 11 m. So each crossing is used ONLY for the component that is
still where the sheets draw it: Prairie Avenue at 16th, 18th and 21st for both
(the same corridor, 66 ft, the same houses standing on it at the same setbacks);
Indiana and Calumet crossings for their NORTHING only (the street they cross); the
Cermak crossing for its EASTING only (the street it is on). Scale comes from the
printed bar, rotation and translation from those components by least squares.

Sheet 28 has one crossing whose modern street survives on both axes (Prairie & 18th):
Twentieth Street is vacated between Indiana and Calumet, and Calumet was re-laid
north of Twenty-First. Its second control point is Prairie & Twentieth, northing
TRANSFERRED from sheet 35's fit (which is anchored 120 m away at Twenty-First) and
easting on the modern Prairie centreline at that northing. Sheet 28 is the Glessner
House sheet, and it is also the one checked hardest: three houses standing today on
both the 1911 sheet and the OpenStreetMap map (1800, 1801 and 1900 Prairie) are read
off the sheet and compared, and the georeference was never fitted to any of them.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]
RASTERS = REPO / "chicago" / "reference" / "prairie-avenue" / "sanborn-1911-and-robinson-1886"
RASTERS_REL = "chicago/reference/prairie-avenue/sanborn-1911-and-robinson-1886"
GCP_DIR = ROOT / "data" / "traces" / "gcp"
CONTROL_PATH = ROOT / "data" / "traces" / "prairie_1904_control.json"
DATUM_PATH = ROOT / "data" / "datum.json"
FT = 0.3048
FITTED_ON = "2026-09-28"

# ---------------------------------------------------------------------------
# The picks. A line is a drawn property line (a block edge), given as points on
# it; x is fitted as a function of y for a 'v' line and y of x for an 'h' line.
# A street centreline is the mean of its two bounding lines, or -- where the
# sheet draws only one side -- that line moved by half the street's annotated
# width at the sheet's printed scale.

SHEETS: dict[str, dict] = {
    "sanborn_1911_v3_sheet_20": {
        "source": "sanborn_1911_chicago_v3_sheet_20",
        "raster": "sanborn_1911_vol3_sheet_20.jpg",
        "size": [5879, 7323],
        "sha256": "ef40d3f20f166d41d029e8b3a7fd8fc0ee60b0dc489c386d95b1603ad21f7d26",
        "title": "Sanborn Map Company, Chicago vol. 3 (1911), sheet 20: E. 16th to E. 18th St., Indiana Av. to the Illinois Central tracks",
        "scale_bar": {"feet": [-50, 0, 150], "px": [3908.5, 4207.75, 5109.0], "row_px": 6745,
                      "note": "the printed 'Scale of Feet' at the foot of the sheet, its 50-ft left extension, zero and 150-ft ends read at the bar's centre row"},
        "pick_method": "each line is the peak of a 5-px-smoothed MEDIAN darkness profile taken across a window of 300 rows (vertical lines) or 350-500 columns (horizontal lines), so lettering inside the window contributes nothing; each line is read at two stations about 4200 px (vertical) or 1475 px (horizontal) apart",
        "lines": {
            "indiana_w": ("v", [[638.2, 1550], [622.9, 5750]]),
            "indiana_e": ("v", [[1043.9, 1550], [1026.0, 5750]]),
            "prairie_w": ("v", [[3322.9, 1550], [3310.1, 5750]]),
            "prairie_e": ("v", [[3721.1, 1550], [3713.3, 5750]]),
            "s16_n": ("h", [[1325, 950.0], [2800, 960.7]]),
            "s16_s": ("h", [[1325, 1251.0], [2800, 1259.0]]),
            "s18_n": ("h", [[1325, 6052.1], [2800, 6061.9]]),
            "s18_s": ("h", [[1325, 6447.8], [2800, 6462.1]]),
        },
        "streets": {
            "indiana": {"pair": ["indiana_w", "indiana_e"]},
            "prairie": {"pair": ["prairie_w", "prairie_e"]},
            "16th": {"pair": ["s16_n", "s16_s"], "width_ft": 50},
            "18th": {"pair": ["s18_n", "s18_s"]},
        },
        "band_tolerance_pct": 4.0,
        "crossings": [
            ("prairie_16th", "prairie", "16th", "EN"),
            ("prairie_18th", "prairie", "18th", "EN"),
            ("indiana_16th", "indiana", "16th", "N"),
            ("indiana_18th", "indiana", "18th", "N"),
        ],
    },
    "sanborn_1911_v3_sheet_35": {
        "source": "sanborn_1911_chicago_v3_sheet_35",
        "raster": "sanborn_1911_vol3_sheet_35.jpg",
        "size": [1602, 2000],
        "sha256": "af57faae39f46cd5fea07a5e0fdecf1512fad5e89878f14de9a8fdd23ef77cc2",
        "title": "Sanborn Map Company, Chicago vol. 3 (1911), sheet 35: E. 20th to E. 22nd St., Indiana Av. to Calumet Av.",
        "scale_bar": {"feet": [-50, 0, 150], "px": [1061.0, 1144.0, 1389.0], "row_px": 1790,
                      "note": "the printed 'Scale of Feet'; this copy is 1602 x 2000 px as the owner attached it, so one pixel is about 0.6 ft and every pick below carries about +/- 1 px"},
        "pick_method": "block corners read by eye on 5x nearest-neighbour enlargements with a 10-px grid, about +/- 1 px; this copy is too coarse for the profile peak the full-resolution sheets use",
        "lines": {
            "indiana_e": ("v", [[145.0, 893.6], [145.6, 997.6], [147.0, 1704.0]]),
            "prairie_w": ("v", [[765.6, 160.6], [767.4, 268.4], [769.0, 887.4], [768.4, 997.0], [770.6, 1700.0], [770.6, 1810.0]]),
            "prairie_e": ("v", [[877.6, 160.0], [878.6, 268.4], [877.0, 886.4], [876.8, 996.0], [879.6, 1699.4], [880.0, 1810.0]]),
            "calumet_w": ("v", [[1495.6, 165.0], [1495.0, 273.0], [1496.6, 887.0], [1496.6, 993.6], [1497.0, 1693.4], [1497.6, 1804.6]]),
            "s20_n": ("h", [[765.6, 160.6], [877.6, 160.0], [1495.6, 165.0]]),
            "s20_s": ("h", [[767.4, 268.4], [878.6, 268.4], [1495.0, 273.0]]),
            "s21_n": ("h", [[145.0, 893.6], [769.0, 887.4], [877.0, 886.4], [1496.6, 887.0]]),
            "s21_s": ("h", [[145.6, 997.6], [768.4, 997.0], [876.8, 996.0], [1496.6, 993.6]]),
            "s22_n": ("h", [[147.0, 1704.0], [770.6, 1700.0], [879.6, 1699.4], [1497.0, 1693.4]]),
            "s22_s": ("h", [[770.6, 1810.0], [880.0, 1810.0], [1497.6, 1804.6]]),
        },
        "streets": {
            "indiana": {"one_side": "indiana_e", "half_width_ft": -33.0,
                        "why": "the sheet stops at Indiana Avenue's east line; 66 ft is printed at the crossing"},
            "prairie": {"pair": ["prairie_w", "prairie_e"]},
            "calumet": {"one_side": "calumet_w", "half_width_ft": 33.0,
                        "why": "the sheet stops at Calumet Avenue's west line; 66 ft is printed at the crossing"},
            "20th": {"pair": ["s20_n", "s20_s"]},
            "21st": {"pair": ["s21_n", "s21_s"]},
            "22nd": {"pair": ["s22_n", "s22_s"]},
        },
        "band_tolerance_pct": 4.0,
        "crossings": [
            ("prairie_21st", "prairie", "21st", "EN"),
            ("indiana_21st", "indiana", "21st", "N"),
            ("calumet_21st", "calumet", "21st", "N"),
            ("prairie_cermak", "prairie", "22nd", "E"),
        ],
        "transfers": [("prairie_20th", "prairie", "20th"), ("calumet_20th", "calumet", "20th")],
    },
    "sanborn_1911_v3_sheet_28": {
        "source": "sanborn_1911_chicago_v3_sheet_28",
        "raster": "sanborn_1911_vol3_sheet_28.jpg",
        "size": [5873, 7323],
        "sha256": "766a7de6708bb2a4784c145da31d4e439d3aaf34935a89fbcb25ee0b17c0e094",
        "title": "Sanborn Map Company, Chicago vol. 3 (1911), sheet 28: E. 18th to E. 20th St., Prairie Av. and Calumet Av. to the Illinois Central tracks",
        "scale_bar": {"feet": [-50, 0, 150], "px": [3333.0, 3634.0, 4538.75], "row_px": 6900,
                      "note": "the printed 'Scale of Feet', its 50-ft left extension, zero and 150-ft ends"},
        "pick_method": "as sheet 20: median darkness profile peaks, each line read at two or three stations",
        "lines": {
            "prairie_w": ("v", [[1652.1, 1450], [1619.9, 5650]]),
            "prairie_e": ("v", [[2044.1, 1450], [2012.1, 5650]]),
            "s18_n": ("h", [[950, 787.7], [2500, 785.0]]),
            "s18_s": ("h", [[950, 1191.3], [2500, 1190.1]]),
            "s20_n": ("h", [[950, 6031.2], [2500, 6043.8], [3550, 6051.1]]),
            "s20_s": ("h", [[950, 6433.0], [2500, 6445.7], [3550, 6452.8]]),
        },
        "streets": {
            "prairie": {"pair": ["prairie_w", "prairie_e"]},
            "18th": {"pair": ["s18_n", "s18_s"]},
            "20th": {"pair": ["s20_n", "s20_s"]},
        },
        "band_tolerance_pct": 4.0,
        "crossings": [
            ("prairie_18th", "prairie", "18th", "EN"),
        ],
        "transferred_control": [("prairie_20th", "prairie", "20th", "sanborn_1911_v3_sheet_35")],
        "checks": [
            {"id": "glessner_house_east_wall", "building": "glessner_house", "pixel": [1566.0, 1250.0], "component": "E",
             "osm": "mean easting of the ring's two east-wall vertices",
             "sheet": "the stone house's east wall line, read at row 1250 on a 3.3x enlargement"},
            {"id": "glessner_house_north_wall", "building": "glessner_house", "pixel": [1500.0, 1194.5], "component": "N",
             "osm": "mean northing of the ring's two north-wall vertices",
             "sheet": "the house's north wall, which the sheet draws ON the 18th Street lot line"},
            {"id": "kimball_house_west_wall", "building": "kimball_house", "pixel": [2195.5, 1250.0], "component": "E",
             "osm": "the main west wall (vertices 1 and 17 of the ring)",
             "sheet": "the stone house's main west wall, read at row 1250"},
            {"id": "keith_house_1900_ne_corner", "building": "keith_house_1900", "pixel": [1471.0, 3651.0], "component": "EN",
             "osm": "the ring's north-east vertex",
             "sheet": "the north-east corner of the brick house's main block at 1900 Prairie"},
        ],
    },
    "robinson_1886_plate_10": {
        "source": "robinson_1886_chicago_plate_10",
        "raster": "robinson_1886_plate_10.jpg",
        "size": [1467, 2000],
        "sha256": "1f4a523e9afe1e6b2bc50e70a00a7976c3ac7f75879189d4043d9b79586ec977",
        "title": "Robinson's Atlas of the City of Chicago (1886), plate 10: 16th to 18th St., Indiana Av. to Lake Michigan",
        "scale_bar": {"feet": [0, 100, 200], "px": [937.5, 1026.4, 1113.7], "row_px": 1815,
                      "note": "the printed bar under 'Scale 100 feet to One inch', its zero, 100-ft and 200-ft ticks"},
        "pick_method": "block corners read by eye on 5x enlargements with a 10-px grid, about +/- 1 px. The copy is a photograph of a bound atlas page, 1467 x 2000 px as the owner attached it, and the page is visibly rotated and curved toward the binding at the left edge",
        "lines": {
            "indiana_w": ("v", [[116.0, 972.0], [116.0, 1009.4], [126.0, 1699.4], [126.0, 1751.6]]),
            "indiana_e": ("v", [[173.0, 971.0], [173.6, 1009.0], [181.4, 1696.6], [182.0, 1750.0]]),
            "prairie_w": ("v", [[499.1, 1010.0], [499.1, 1130.0], [506.6, 1690.0], [507.0, 1744.0]]),
            "prairie_e": ("v", [[550.0, 970.0], [550.0, 1035.0], [560.6, 1688.6], [560.6, 1743.0]]),
            "s16_n": ("h", [[116.0, 972.0], [173.0, 971.0], [300.0, 967.8], [490.0, 967.8]]),
            "s16_s": ("h", [[116.0, 1009.4], [173.6, 1009.0], [340.0, 1003.5], [490.0, 1003.5]]),
            "s18_n": ("h", [[126.0, 1699.4], [181.4, 1696.6], [506.6, 1690.0], [560.6, 1688.6]]),
            "s18_s": ("h", [[126.0, 1751.6], [182.0, 1750.0], [507.0, 1744.0], [560.6, 1743.0]]),
        },
        "streets": {
            "indiana": {"pair": ["indiana_w", "indiana_e"]},
            "prairie": {"pair": ["prairie_w", "prairie_e"]},
            "16th": {"pair": ["s16_n", "s16_s"], "width_ft": None},
            "18th": {"pair": ["s18_n", "s18_s"]},
        },
        "band_tolerance_pct": None,
        "band_note": ("NOT a test on this plate: its street bands are not drawn to its printed widths. Indiana and "
                      "Prairie are both printed '66' and read 67 and 55 ft at the plate's own bar; 16th Street, which "
                      "the 1911 sheet prints as 50 ft, reads 44. The bands are the engraver's, the bar is the scale, "
                      "and the fit uses only the bar and the crossings' centres"),
        "crossings": [
            ("prairie_16th", "prairie", "16th", "EN"),
            ("prairie_18th", "prairie", "18th", "EN"),
            ("indiana_16th", "indiana", "16th", "N"),
            ("indiana_18th", "indiana", "18th", "N"),
        ],
    },
}
ORDER = ["sanborn_1911_v3_sheet_20", "sanborn_1911_v3_sheet_35",
         "sanborn_1911_v3_sheet_28", "robinson_1886_plate_10"]

WHY_COMPONENT = {
    "EN": "both: Prairie Avenue is the 1886 and 1911 corridor, 66 ft wide, with houses standing on it today at the setbacks the sheets draw",
    "N": "northing only: the modern centreline of the avenue this crossing is ON is displaced from the one the sheet draws (Indiana 5-8 m east of it; Calumet re-laid north of Twenty-First), so only the street it CROSSES is control",
    "E": "easting only: Cermak Road is a divided carriageway today (two OpenStreetMap nodes 16.1 m apart at Prairie) and stands about 10 m south of the Twenty-Second Street sheet 35 draws, so only Prairie Avenue is control here",
}


# ---------------------------------------------------------------------------
# geometry

def line_fit(axis: str, pts: list[list[float]]) -> tuple[str, float, float]:
    """Least-squares line. 'v': x = p + q*y ; 'h': y = p + q*x."""
    if axis == "v":
        xs, ys = [p[1] for p in pts], [p[0] for p in pts]
    else:
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    q = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sxx
    return axis, my - q * mx, q


def street_line(sheet: dict, name: str, px_per_ft: float) -> tuple[str, float, float]:
    spec = sheet["streets"][name]
    if "pair" in spec:
        a = line_fit(*sheet["lines"][spec["pair"][0]])
        b = line_fit(*sheet["lines"][spec["pair"][1]])
        return a[0], (a[1] + b[1]) / 2, (a[2] + b[2]) / 2
    ax, p, q = line_fit(*sheet["lines"][spec["one_side"]])
    return ax, p + spec["half_width_ft"] * px_per_ft, q


def crossing_px(v: tuple, h: tuple) -> tuple[float, float]:
    _, pv, qv = v   # x = pv + qv*y
    _, ph, qh = h   # y = ph + qh*x
    x = (pv + qv * ph) / (1 - qv * qh)
    return x, ph + qh * x


def px_per_ft(sheet: dict) -> float:
    bar = sheet["scale_bar"]
    return (bar["px"][-1] - bar["px"][0]) / (bar["feet"][-1] - bar["feet"][0])


def band_width_ft(sheet: dict, name: str, ppf: float) -> float | None:
    spec = sheet["streets"][name]
    if "pair" not in spec:
        return None
    a = line_fit(*sheet["lines"][spec["pair"][0]])
    b = line_fit(*sheet["lines"][spec["pair"][1]])
    return abs(b[1] - a[1]) / ppf


# ---------------------------------------------------------------------------
# fits

def sim_apply(s: float, th: float, c: float, d: float, px: float, py: float) -> tuple[float, float]:
    return (s * (math.cos(th) * px + math.sin(th) * py) + c,
            s * (math.sin(th) * px - math.cos(th) * py) + d)


def fit_fixed_scale(obs: list[dict], s: float) -> tuple[float, float, float]:
    """Rotation + translation at a fixed scale, least squares over the observed components."""
    def solve(th: float) -> tuple[float, float, float]:
        es = [o["E"] - s * (math.cos(th) * o["px"][0] + math.sin(th) * o["px"][1]) for o in obs if o.get("E") is not None]
        ns = [o["N"] - s * (math.sin(th) * o["px"][0] - math.cos(th) * o["px"][1]) for o in obs if o.get("N") is not None]
        c, d = sum(es) / len(es), sum(ns) / len(ns)
        sse = sum((e - c) ** 2 for e in es) + sum((n - d) ** 2 for n in ns)
        return sse, c, d

    lo, hi = math.radians(-6.0), math.radians(6.0)
    # coarse scan, then golden section around the best cell
    best = min((solve(lo + (hi - lo) * i / 2400)[0], i) for i in range(2401))[1]
    a, b = lo + (hi - lo) * (best - 1) / 2400, lo + (hi - lo) * (best + 1) / 2400
    g = (math.sqrt(5) - 1) / 2
    for _ in range(200):
        x1, x2 = b - g * (b - a), a + g * (b - a)
        if solve(x1)[0] < solve(x2)[0]:
            b = x2
        else:
            a = x1
    th = (a + b) / 2
    _, c, d = solve(th)
    return th, c, d


def fit_affine(pairs: list[tuple[tuple[float, float], tuple[float, float]]]) -> list[float] | None:
    """Free six-parameter affine, pixel -> local, by normal equations (no numpy)."""
    if len(pairs) < 3:
        return None

    def lsq(rows, rhs):
        m = [[sum(r[i] * r[j] for r in rows) for j in range(3)] for i in range(3)]
        v = [sum(r[i] * y for r, y in zip(rows, rhs)) for i in range(3)]
        for i in range(3):                       # Gauss-Jordan, 3x3
            piv = max(range(i, 3), key=lambda k: abs(m[k][i]))
            m[i], m[piv], v[i], v[piv] = m[piv], m[i], v[piv], v[i]
            for k in range(3):
                if k != i:
                    f = m[k][i] / m[i][i]
                    m[k] = [a - f * b for a, b in zip(m[k], m[i])]
                    v[k] -= f * v[i]
        return [v[i] / m[i][i] for i in range(3)]

    rows = [[p[0], p[1], 1.0] for p, _ in pairs]
    ae = lsq(rows, [t[0] for _, t in pairs])
    an = lsq(rows, [t[1] for _, t in pairs])
    return ae + an


def r2(x: float) -> float:
    return round(x + 0.0, 2)


# ---------------------------------------------------------------------------

def modern(control: dict, cid: str) -> dict:
    c = control["crossings"][cid]
    return {"streets": c["streets"], "osm_node_ids": c["osm_node_ids"],
            "osm_node_spread_m": c["node_spread_m"], "lon": c["lon"], "lat": c["lat"],
            "local_e": c["local_e"], "local_n": c["local_n"]}


def prairie_e_at(control: dict, n: float) -> float:
    a, b = control["crossings"]["prairie_18th"], control["crossings"]["prairie_21st"]
    return a["local_e"] + (b["local_e"] - a["local_e"]) * (n - a["local_n"]) / (b["local_n"] - a["local_n"])


def check_value(control: dict, chk: dict) -> tuple[float | None, float | None]:
    ring = control["check_buildings"][chk["building"]]["ring_local"]
    if chk["id"] == "glessner_house_east_wall":
        return (ring[1][0] + ring[2][0]) / 2, None
    if chk["id"] == "glessner_house_north_wall":
        return None, (ring[0][1] + ring[1][1]) / 2
    if chk["id"] == "kimball_house_west_wall":
        return (ring[1][0] + ring[17][0]) / 2, None
    if chk["id"] == "keith_house_1900_ne_corner":
        v = max(ring, key=lambda p: p[0] + p[1])
        return v[0], v[1]
    raise KeyError(chk["id"])


def derive(control: dict) -> dict[str, dict]:
    out: dict[str, dict] = {}
    fits: dict[str, tuple] = {}
    for key in ORDER:
        sh = SHEETS[key]
        ppf = px_per_ft(sh)
        s = FT / ppf
        streets = {n: street_line(sh, n, ppf) for n in sh["streets"]}
        obs = []
        for cid, ns, ew, comp in sh["crossings"]:
            px = crossing_px(streets[ns], streets[ew])
            m = modern(control, cid)
            obs.append({"id": cid, "px": px, "comp": comp,
                        "E": m["local_e"] if "E" in comp else None,
                        "N": m["local_n"] if "N" in comp else None,
                        "modern": m, "why": WHY_COMPONENT[comp], "transferred": None})
        for cid, ns, ew, frm in sh.get("transferred_control", []):
            px = crossing_px(streets[ns], streets[ew])
            f = fits[frm]
            src_px = out[frm]["transfer_points"][cid]["pixel"]
            _, n_t = sim_apply(*f, *src_px)
            e_t = prairie_e_at(control, n_t)
            obs.append({"id": cid, "px": px, "comp": "EN", "E": e_t, "N": n_t, "modern": None,
                        "why": ("both, and neither is a modern crossing: Twentieth Street is vacated between Indiana "
                                "and Calumet today. The NORTHING is transferred from " + frm + "'s fit, which is "
                                "anchored at Twenty-First Street 120 m away; the EASTING is the modern Prairie "
                                "Avenue centreline (the line through the 18th and 21st crossing nodes) at that northing."),
                        "transferred": {"from": frm, "pixel_on_that_sheet": src_px}})
        th, c, d = fit_fixed_scale(obs, s)
        fits[key] = (s, th, c, d)

        gcps, sq_e, sq_n, n_comp = [], [], [], 0
        for o in obs:
            e, n = sim_apply(s, th, c, d, *o["px"])
            re = None if o["E"] is None else e - o["E"]
            rn = None if o["N"] is None else n - o["N"]
            if re is not None:
                sq_e.append(re * re)
            if rn is not None:
                sq_n.append(rn * rn)
            # leave-one-out, for the components this point carries
            rest = [p for p in obs if p is not o]
            loo = None
            if sum((p["E"] is not None) + (p["N"] is not None) for p in rest) >= 3 and \
               any(p["E"] is not None for p in rest) and any(p["N"] is not None for p in rest):
                t2, c2, d2 = fit_fixed_scale(rest, s)
                e2, n2 = sim_apply(s, t2, c2, d2, *o["px"])
                loo = {"e_m": None if o["E"] is None else r2(e2 - o["E"]),
                       "n_m": None if o["N"] is None else r2(n2 - o["N"])}
            g = {"id": o["id"], "pixel": [round(o["px"][0], 1), round(o["px"][1], 1)],
                 "pixel_note": "crossing of the two street centrelines; each centreline is the mean of its two drawn "
                               "property lines, or one drawn line moved half its printed width",
                 "components_used": o["comp"], "why_these_components": o["why"]}
            if o["modern"]:
                g["modern"] = o["modern"]
            if o["transferred"]:
                g["transferred"] = dict(o["transferred"], local_e=r2(o["E"]), local_n=r2(o["N"]))
            g["residual_e_m"] = None if re is None else r2(re)
            g["residual_n_m"] = None if rn is None else r2(rn)
            g["leave_one_out_m"] = loo
            gcps.append(g)
        n_comp = len(sq_e) + len(sq_n)
        rms_comp = math.sqrt((sum(sq_e) + sum(sq_n)) / n_comp)
        dof = n_comp - 3

        # the free fits, as diagnostics
        full = [o for o in obs if o["modern"]]
        pairs = [(o["px"], (o["modern"]["local_e"], o["modern"]["local_n"])) for o in full]
        aff = fit_affine(pairs) if len(pairs) >= 3 else None
        diag = None
        if aff:
            sx, sy = math.hypot(aff[0], aff[3]), math.hypot(aff[1], aff[4])
            res = [math.hypot(aff[0] * p[0] + aff[1] * p[1] + aff[2] - t[0],
                              aff[3] * p[0] + aff[4] * p[1] + aff[5] - t[1]) for p, t in pairs]
            diag = {
                "what": "the free six-parameter affine on every crossing's full modern position -- the fit "
                        "rees_rucker_1849_gcps.json adopts -- fitted and NOT adopted",
                "n": len(pairs),
                "coefficients": dict(zip("abcdef", [round(v, 9) for v in aff])),
                "scale_m_per_px": {"x": round(sx, 5), "y": round(sy, 5)},
                "axis_scale_difference_pct": round(100 * abs(sx - sy) / min(sx, sy), 2),
                "printed_scale_m_per_px": round(s, 5),
                "rms_m": r2(math.sqrt(sum(r * r for r in res) / len(res))),
                "why_not": ("its two axis scales disagree by far more than the sheet's own printed scale and its 66-ft "
                            "street bands allow (see scale_evidence), because it reads a displaced modern street as "
                            "paper stretch; with as few crossings as this it has only 2 degrees of freedom to spend "
                            "and it spends them bending the sheet to the street"),
            }
        ew_bands = {n: band_width_ft(sh, n, ppf) for n in sh["streets"]}
        doc = {
            "_doc": ("Ground control and fitted transform for " + sh["title"] + ". GENERATED by "
                     "tools/georef_prairie_1904.py from the picks written in that tool and the modern control in "
                     "data/traces/prairie_1904_control.json -- do not hand-edit; re-run the tool. Pixel coordinates "
                     "are on the committed raster named below. T-1250."),
            "source": sh["source"],
            "raster": {"path": RASTERS_REL + "/" + sh["raster"], "width": sh["size"][0], "height": sh["size"][1],
                       "sha256": sh["sha256"]},
            "fitted_on": FITTED_ON,
            "control_source": ("data/traces/prairie_1904_control.json: OpenStreetMap crossings (node rule of "
                               "data/traces/street_control.json) in EPSG:26916, carried to the local frame of "
                               "data/datum.json. OpenStreetMap data (c) OpenStreetMap contributors, ODbL."),
            "pick_method": sh["pick_method"],
            "fit": {
                "type": ("similarity at the sheet's printed scale: scale from the printed bar, rotation and "
                         "translation by least squares over the control components named per point, pixel -> "
                         "local ENU of data/datum.json"),
                "coefficients": {"a": round(s * math.cos(th), 10), "b": round(s * math.sin(th), 10), "c": round(c, 4),
                                 "d": round(s * math.sin(th), 10), "e": round(-s * math.cos(th), 10), "f": round(d, 4)},
                "formula": "local_e = a*px + b*py + c ; local_n = d*px + e*py + f ; utm = local + data/datum.json origin",
                "scale_m_per_px": round(s, 6),
                "rotation_deg": round(math.degrees(th), 3),
                "components": n_comp,
                "degrees_of_freedom": dof,
                "rms_component_m": r2(rms_comp),
                "rms_m": r2(rms_comp * math.sqrt(2)),
                "rms_note": ("rms_component_m is the root mean square over every control COMPONENT used (an easting "
                             "or a northing); rms_m is its two-dimensional equivalent, the figure comparable with the "
                             "rms_m other GCP files in this directory state."),
                "max_component_m": r2(max(math.sqrt(v) for v in sq_e + sq_n)),
            },
            "scale_evidence": {
                "printed_scale_bar": dict(sh["scale_bar"], px_per_ft=round(ppf, 4)),
                "street_band_widths_ft_at_printed_scale": {k: round(v, 1) for k, v in ew_bands.items() if v is not None},
                "street_band_widths_ft_printed": {k: v.get("width_ft", 66) for k, v in sh["streets"].items()
                                              if "pair" in v and v.get("width_ft", 66) is not None},
            "tolerance_pct": sh["band_tolerance_pct"],
            "note": sh.get("band_note", "the printed bar is the sheet's own statement of its scale; the street bands, "
                           "at the widths the sheet prints on them, test it in both directions, and "
                           "tools/georef_prairie_1904.py holds every band to tolerance_pct of its printed width"),
            },
            "affine_diagnostic": diag,
            "gcps": gcps,
        }
        if key == "sanborn_1911_v3_sheet_28":
            chks = []
            for chk in sh["checks"]:
                e, n = sim_apply(s, th, c, d, *chk["pixel"])
                we, wn = check_value(control, chk)
                chks.append({"id": chk["id"], "pixel": chk["pixel"], "components": chk["component"],
                             "sheet_reading": chk["sheet"], "osm_reading": chk["osm"],
                             "osm_way_id": control["check_buildings"][chk["building"]]["osm_way_id"],
                             "residual_e_m": None if we is None else r2(e - we),
                             "residual_n_m": None if wn is None else r2(n - wn)})
            vals = [abs(v) for x in chks for v in (x["residual_e_m"], x["residual_n_m"]) if v is not None]
            doc["independent_checks"] = {
                "what": ("three houses that stand today on the same lots the 1911 sheet draws them on, read off the "
                         "sheet and compared with their OpenStreetMap outlines. The fit never saw them. OSM building "
                         "outlines are traced from imagery and are good to a metre or two, so a residual of that size "
                         "is the check's own noise."),
                "checks": chks,
                "rms_component_m": r2(math.sqrt(sum(v * v for v in vals) / len(vals))),
                "max_component_m": r2(max(vals)),
            }
        if sh.get("transfers"):
            doc["transfer_points"] = {}
            for cid, ns, ew in sh["transfers"]:
                px = crossing_px(streets[ns], streets[ew])
                e, n = sim_apply(s, th, c, d, *px)
                doc["transfer_points"][cid] = {"pixel": [round(px[0], 1), round(px[1], 1)],
                                               "local_e": r2(e), "local_n": r2(n),
                                               "read_by": "sanborn_1911_v3_sheet_28 (its second control point)"}
        out[key] = doc
    return out


def extra_notes(docs: dict[str, dict]) -> None:
    """The prose that depends on the numbers, written from them."""
    d20 = docs["sanborn_1911_v3_sheet_20"]
    a20 = d20["affine_diagnostic"]
    d20["use"] = (
        "For reading the 1911 Illinois Central right-of-way and lake edge between 16th and 18th Streets "
        "(tools/trace_ic_edge_1904.py, T-1250), and for the Prairie Avenue footprints, lots and street edges "
        "later tickets read off this sheet (streets T-0474, the district's buildings). Within the four crossings "
        f"the fit holds {d20['fit']['rms_m']} m RMS; the free affine would have held {a20['rms_m']} m on the same "
        f"points and been wrong by its {a20['axis_scale_difference_pct']} % axis-scale difference everywhere else.")
    d28 = docs["sanborn_1911_v3_sheet_28"]
    ic = d28["independent_checks"]
    d28["use"] = (
        "The Glessner House sheet. For the lake edge between 18th and 20th Streets (tools/trace_ic_edge_1904.py), "
        "for the 1904 scene's spawn at Prairie & 18th facing 1800 Prairie (T-1252), and for the footprints T-1729 "
        "and T-0474 read off it. The fit has one degree of freedom, so its own RMS says little; what it is worth "
        f"is the independent check: three standing houses read off the sheet land {ic['rms_component_m']} m RMS "
        f"(worst {ic['max_component_m']} m) from their OpenStreetMap outlines.")
    docs["sanborn_1911_v3_sheet_35"]["use"] = (
        "For the blocks from 20th to 22nd Street and, now, for one thing more: its Prairie & Twentieth crossing is "
        "sheet 28's second control point. No lake edge is drawn on it -- the sheet stops at Calumet Avenue.")
    docs["robinson_1886_plate_10"]["use"] = (
        "For the 1886 lake edge between 16th and 18th Streets, which BOUNDS the 1904 edge from before "
        "(tools/trace_ic_edge_1904.py), and for the outlines of the two houses Glessner House names as standing "
        "in 1904 and gone by 1911 (1609-1611 and 1620 Prairie), which later tickets read off it. A photographed "
        "page with a curved gutter: trust it least toward the left edge.")


def dumps(doc: dict) -> str:
    return json.dumps(doc, indent=1, ensure_ascii=False) + "\n"


def out_path(key: str) -> Path:
    return GCP_DIR / f"{key}_gcps.json"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def build(control: dict) -> dict[str, dict]:
    docs = derive(control)
    extra_notes(docs)
    return docs


def check(control: dict) -> list[str]:
    bad = []
    for key, sh in SHEETS.items():
        p = RASTERS / sh["raster"]
        if not p.exists():
            bad.append(f"{key}: raster {p.relative_to(REPO)} is missing")
        elif sha256(p) != sh["sha256"]:
            bad.append(f"{key}: raster sha256 changed -- every pick on it is now unverified")
    docs = build(control)
    for key, doc in docs.items():
        p = out_path(key)
        if not p.exists():
            bad.append(f"{p.relative_to(ROOT)} is missing; run tools/georef_prairie_1904.py")
        elif p.read_text(encoding="utf-8") != dumps(doc):
            bad.append(f"{p.relative_to(ROOT)} is not what the tool derives; re-run it (or revert a hand edit)")
    return bad + contract(docs)


# The ceilings a fit has to stay under, and why. They are not tuned to pass: each is
# the size the sheet itself makes plausible, written before the numbers were read.
CEILINGS = {
    "sanborn_1911_v3_sheet_20": 4.0,    # 1 px = 5 cm; the crossings and the modern nodes are good to ~2 m
    "sanborn_1911_v3_sheet_28": 4.0,
    "sanborn_1911_v3_sheet_35": 4.0,    # 1 px = 19 cm, picks +/- 1 px
    "robinson_1886_plate_10": 6.0,      # a photographed, curved page
}


def contract(docs: dict[str, dict]) -> list[str]:
    bad = []
    for key, doc in docs.items():
        f = doc["fit"]
        if f["rms_m"] > CEILINGS[key]:
            bad.append(f"{key}: fit RMS {f['rms_m']} m is over its {CEILINGS[key]} m ceiling")
        if f["degrees_of_freedom"] < 1:
            bad.append(f"{key}: the fit has no redundancy, so its RMS states nothing")
        bar_ppf = doc["scale_evidence"]["printed_scale_bar"]["px_per_ft"]
        if abs(f["scale_m_per_px"] - FT / bar_ppf) > 1e-6:
            bad.append(f"{key}: the fit's scale is not the printed bar's")
        tol = SHEETS[key]["band_tolerance_pct"]
        if tol is not None:
            for name, w in doc["scale_evidence"]["street_band_widths_ft_at_printed_scale"].items():
                want = SHEETS[key]["streets"][name].get("width_ft", 66)
                if abs(w - want) > want * tol / 100:
                    bad.append(f"{key}: the {name} band reads {w} ft at the printed scale against {want} ft "
                               "printed; the bar or the pick is wrong")
        for g in doc["gcps"]:
            if g["components_used"] not in WHY_COMPONENT:
                bad.append(f"{key}: {g['id']} uses {g['components_used']!r}, which says nothing about why")
    ic = docs["sanborn_1911_v3_sheet_28"]["independent_checks"]
    if ic["max_component_m"] > 5.0:
        bad.append(f"sheet 28's independent building check is {ic['max_component_m']} m out; the Glessner lot "
                   "cannot be placed from this fit")
    a20 = docs["sanborn_1911_v3_sheet_20"]["affine_diagnostic"]
    if a20 is None or a20["axis_scale_difference_pct"] < 2.0:
        bad.append("sheet 20's free affine no longer disagrees with the printed scale; the argument for the "
                   "similarity in this tool's docstring has to be re-made")
    return bad


def self_test(control: dict) -> int:
    base = build(control)
    cases = []

    c = copy.deepcopy(control)
    c["crossings"]["prairie_18th"]["local_e"] += 12.0
    cases.append(("moving the Prairie & 18th control 12 m raises the sheet 20 RMS over its ceiling",
                  any("sanborn_1911_v3_sheet_20: fit RMS" in b for b in contract(build(c)))))

    saved = copy.deepcopy(SHEETS["sanborn_1911_v3_sheet_28"]["checks"])
    SHEETS["sanborn_1911_v3_sheet_28"]["checks"][0]["pixel"] = [1566.0 - 150.0, 1250.0]
    cases.append(("a Glessner wall read 150 px (7.6 m) off fails the independent check",
                  any("independent building check" in b for b in contract(build(control)))))
    SHEETS["sanborn_1911_v3_sheet_28"]["checks"] = saved

    saved = copy.deepcopy(SHEETS["sanborn_1911_v3_sheet_20"]["scale_bar"])
    SHEETS["sanborn_1911_v3_sheet_20"]["scale_bar"]["px"] = [3908.5, 4207.75, 5409.0]
    cases.append(("a misread scale bar shows up in the street bands",
                  any("band reads" in b for b in contract(build(control)))))
    SHEETS["sanborn_1911_v3_sheet_20"]["scale_bar"] = saved

    doc = copy.deepcopy(base)
    doc["sanborn_1911_v3_sheet_20"]["fit"]["scale_m_per_px"] *= 1.03
    cases.append(("a fit scale that is not the printed bar's fails", bool(contract(doc))))

    doc = copy.deepcopy(base)
    doc["sanborn_1911_v3_sheet_20"]["gcps"][2]["components_used"] = "EN?"
    cases.append(("a control point that does not say which component it is control for fails", bool(contract(doc))))

    cases.append(("the committed files are what the tool derives", not check(control)))
    for label, ok in cases:
        print(("   ok   " if ok else "   FAIL ") + label)
    return 0 if all(ok for _, ok in cases) else 1


def short(key: str) -> str:
    return key.replace("sanborn_1911_v3_", "").replace("_", " ").replace("robinson 1886 plate 10", "robinson plate 10")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    control = json.loads(CONTROL_PATH.read_text(encoding="utf-8"))
    if args.self_test:
        return self_test(control)
    if args.check:
        bad = check(control)
        for b in bad:
            print("FAIL", b)
        if not bad:
            docs = build(control)
            print("OK four Prairie Avenue sheets re-derive: " + "; ".join(
                f"{short(k)} {d['fit']['rms_m']} m" for k, d in docs.items())
                + f"; sheet 28 checks {docs['sanborn_1911_v3_sheet_28']['independent_checks']['rms_component_m']} m"
                " on three standing houses")
        return 1 if bad else 0
    docs = build(control)
    for key, doc in docs.items():
        out_path(key).write_text(dumps(doc), encoding="utf-8")
        f = doc["fit"]
        print(f"{key}: scale {f['scale_m_per_px']} m/px rot {f['rotation_deg']} deg  RMS {f['rms_m']} m "
              f"(component {f['rms_component_m']} m, {f['components']} comps, dof {f['degrees_of_freedom']})")
        for g in doc["gcps"]:
            print(f"    {g['id']:16s} {g['components_used']:3s} e {g['residual_e_m']} n {g['residual_n_m']}  loo {g['leave_one_out_m']}")
        if doc.get("affine_diagnostic"):
            a = doc["affine_diagnostic"]
            print(f"    affine diag: axis diff {a['axis_scale_difference_pct']}% rms {a['rms_m']}")
        print(f"    bands ft: {doc['scale_evidence']['street_band_widths_ft_at_printed_scale']}")
        if doc.get("independent_checks"):
            for x in doc["independent_checks"]["checks"]:
                print(f"    CHECK {x['id']}: e {x['residual_e_m']} n {x['residual_n_m']}")
    bad = contract(docs)
    for b in bad:
        print("FAIL", b)
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
