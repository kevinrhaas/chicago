#!/usr/bin/env python3
"""Read the small platted tract north of Kinzie Street — the one lettered Michigan St.

    tools/read_michigan_st_tract.py               print the reading
    tools/read_michigan_st_tract.py --write       write data/traces/michigan_st_tract_grid.json
    tools/read_michigan_st_tract.py --check       re-derive the committed file WITHOUT the raster
    tools/read_michigan_st_tract.py --check-sheet  re-read the raster and compare

WHAT THIS TRACT IS AND WHY IT NEEDED READING. Immediately north of Kinzie Street,
east of the North Branch and west of the open ground that carries the sheet's
title, Wright draws a small square tract unlike anything around it: two columns of
blocks cut into small parcels, a mid-block alley in every block, an east-west
street lettered `Michigan St`, and a wash of its own. Every neighbour is whole
blocks. The project had nothing there under any name (T-0796).

WHAT THE READING SETTLES, and it is not what the ticket expected. Both of the
tract's internal streets are streets the town already has. Its east-west street
carried east on the Addition's own drawn slope lands on Kinzie's Addition's
Michigan Street — the street this project already commits as `michigan_north` —
to within a pixel or two over eight hundred metres. Its north-south street
carried south across Kinzie Street lands on the Original Town's Market Street.
So this is not an alien plat with a street name of its own that happens to
collide: it is ground platted ON the town's grid, extending Market north and
Michigan west, in a parcel module that is its own.

WHAT IT DOES NOT SETTLE. The tract's NAME. The sheet's legend has nine washes and
one of them — an olive — is written `Surveyed ————— 1833` with the name left
blank. The tract's wash is olive and matches that swatch; it also matches
`Part of Canal Sec. No. 9`, and the two swatches do not separate from each other
on this scan. What the wash DOES settle is the five it excludes. The documentary
name is in sources this repository does not hold, and nothing here invents one.

THE SHEET is the National Archives / Historic Urban Plans facsimile registered as
`wright_1834_nara_hup` (5050 x 6628 px at 600 dpi) — the same sheet, frame and
affine `tools/read_kinzie_addition_streets.py` reads, so the two readings compare
directly and the Michigan Street test above is a comparison of pixels rather than
of two differently-registered metres.

THE METHOD is that tool's, unchanged in principle: ink projected onto one axis
over a stated window, sharp narrow peaks taken as ruled lines. One thing is added.
This tract is washed, and a wash is ink to a threshold — it lifted the whole
profile and made the tract's own border a broad mound the width test then threw
away. So the profile is baseline-subtracted against a rolling median before the
peaks are taken: the wash is a slow term, a ruled line is not.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPO = ROOT.parent.parent
GCP = ROOT / "data/traces/gcp/wright_1834_nara_hup_gcps.json"
OUT = ROOT / "data/traces/michigan_st_tract_grid.json"
KINZIE = ROOT / "data/traces/kinzie_addition_street_grid.json"
STREETS = ROOT / "data/streets/1835.json"
FT = 0.3048
MILE_M = 1609.344

# The raster slopes of the tract's own rules, fitted by maximising the variance of
# the projection over the windows below. They are properties of THIS corner of
# THIS sheet and are not the Addition's (0.0176 / -0.0060) — the difference is
# discussed under `identity` in the written file.
SHEAR_EW = 0.024
SHEAR_NS = -0.024

# ------------------------------------------------------------------ windows

EW_COLUMNS = [
    {"id": "col_west", "x": (1815, 1885), "y": (1840, 2115),
     "through": "the tract's western block column, between its west border and its "
                "north-south street"},
    {"id": "col_east", "x": (1965, 2075), "y": (1840, 2115),
     "through": "the tract's eastern block column"},
]

# Slot tables: the pixel a feature is looked for at, per column. They are the
# result of the first read and exist only to attach a name to a detected rule;
# a rule further than `EW_TOL` from its slot is not accepted as that feature.
EW_SLOTS = {
    "col_west": {"north_border": 1864.0, "alley_north_tier": 1914.0,
                 "michigan_st": 1975.5, "alley_south_tier": 2035.0,
                 "south_border": 2080.0},
    "col_east": {"north_border": 1873.0, "alley_north_tier": 1916.0,
                 "michigan_st": 1978.5, "alley_south_tier": 2037.5,
                 "south_border": 2085.0},
}
EW_TOL = 12.0
EW_SINGLE = ("north_border", "south_border")
EW_PAIR_WIDTH = {"alley_north_tier": (5.0, 15.0), "alley_south_tier": (4.0, 13.0),
                 "michigan_st": (28.0, 44.0)}

NS_ROWS = [
    {"id": "tier1_north", "y": (1875, 1905), "through": "the north tier's northern lot row"},
    {"id": "tier1_south", "y": (1925, 1952), "through": "the north tier's southern lot row"},
    {"id": "tier2_north", "y": (2002, 2028), "through": "the south tier's northern lot row"},
    {"id": "tier2_south", "y": (2048, 2076), "through": "the south tier's southern lot row"},
]
NS_X = (1770, 2115)
# The tract's two borders and its north-south street are looked for at slots, the
# same discipline the east-west features use, and for the same reason: in two of
# the four rows a lot line is missing and the widest gap in the row is then not
# the street. Slots are quoted at the first row's reference and carried to the
# others on SHEAR_NS. Everything found BETWEEN a border and the street is a lot
# line and is not looked for at all.
NS_SLOTS = {"west_border": 1797.0, "east_border": 2083.0}
NS_STREET = {"slot": 1912.2, "width": (28.0, 38.0), "tol": 10.0}
NS_BORDER_TOL = 8.0
NS_MERGE_PX = 6.0

# ------------------------------------------------------------------ control
#
# A corridor width read off this sheet by this method is only meaningful beside a
# corridor of KNOWN width read off the same sheet by the same method, and the two
# axes have to be priced separately because the sheet's own fit is 5.2 per cent
# more metres per pixel down the page than across it. So there are two controls,
# each of platted 80 ft corridors (data/traces/vectors/street_corridors_1834.json,
# where 80 ft is adopted and 66 ft excluded):
#
#   x — the Original Town's north-division streets, read in the block row between
#       Kinzie Street and the river, one hundred metres south of the tract;
#   y — Lake, Randolph and Washington, the window tools/read_kinzie_addition_
#       streets.py already uses for the same purpose.

CONTROL_NS = {"window": (1830, 2150, 2470, 2200), "shear": SHEAR_NS,
              "slots": {"market": 1910.0, "franklin": 2078.0,
                        "wells": 2260.0, "lasalle": 2421.0},
              "width": (24.0, 44.0), "tol": 14.0}
CONTROL_EW = {"window": (2380, 2560, 2500, 3080), "shear": 0.0176,
              "slots": {"lake": 2632.0, "randolph": 2826.0, "washington": 3010.0},
              "width": (26.0, 44.0), "tol": 16.0}

# ----------------------------------------------------------------- the wash
#
# Legend swatches, and the patches of map wash tested against them. A wash lies
# OVER aged paper, so the colours are compared as absorbances — -log(patch/paper),
# normalised — which is the one comparison that does not move when a wash is laid
# thin. The School Section's band on the map is measured too, as the control: it
# is a wash whose swatch is known, and it has to come back naming its own swatch.

SWATCH_BOX = {
    "1_us_military_reservation": (3004, 3772, 3040, 3798),
    "2_surveyed_by_canal_comrs_1830": (3004, 3822, 3040, 3846),
    "3_wabansia_surveyed_1831": (3004, 3867, 3040, 3895),
    "4_kinzies_addn_surveyed_1833": (3004, 3917, 3040, 3945),
    "5_school_section_1833": (3004, 3965, 3040, 3995),
    "6_surveyed_blank_1833": (3004, 4010, 3040, 4032),
    "7_fractional_section_15": (3004, 4050, 3040, 4070),
    "8_surveyed_in_1833": (3004, 4096, 3040, 4116),
    "9_part_of_canal_sec_no_9": (3004, 4140, 3040, 4160),
}
PAPER_BOX = (3100, 3760, 3300, 4180)
WASH_BOX = {
    "tract_band_west": (1776, 1890, 1796, 2010),
    "school_section_band": (700, 3200, 1800, 3230),
}

# ------------------------------------------------------------------- the read


def _sheet():
    g = json.loads(GCP.read_text())
    img = REPO / g["raster"]["working_copy"]
    if not img.exists():
        raise SystemExit(f"the registered raster is not in this checkout: {img}")
    return g, img


def _load_px(img):
    from PIL import Image
    Image.MAX_IMAGE_PIXELS = None
    return Image.open(img)


def _profile(im, x0, y0, x1, y1, axis, shear):
    """Mean ink per bin, the band stacked along `shear` so a tilted rule lands in one bin."""
    px = im.convert("L").load()
    if axis == "h":
        n = y1 - y0
        acc = [0.0] * n
        for x in range(x0, x1):
            off = shear * (x - x0)
            for i in range(n):
                y = y0 + i + off
                yi = int(y)
                fr = y - yi
                acc[i] += max(0.0, 150.0 - (px[x, yi] * (1 - fr) + px[x, yi + 1] * fr))
        return [(float(y0 + i), acc[i] / (x1 - x0)) for i in range(n)]
    n = x1 - x0
    acc = [0.0] * n
    for y in range(y0, y1):
        off = shear * (y - y0)
        for i in range(n):
            x = x0 + i + off
            xi = int(x)
            fr = x - xi
            acc[i] += max(0.0, 150.0 - (px[xi, y] * (1 - fr) + px[xi + 1, y] * fr))
    return [(float(x0 + i), acc[i] / (y1 - y0)) for i in range(n)]


def _debase(prof, half=25):
    """Subtract a rolling median. The wash is a slow term; a ruled line is not."""
    vals = [v for _, v in prof]
    out = []
    for i in range(len(prof)):
        w = sorted(vals[max(0, i - half):min(len(vals), i + half + 1)])
        med = w[len(w) // 2]
        out.append((prof[i][0], max(0.0, vals[i] - med)))
    return out


def _rules(prof, minpk=14.0, maxw=9):
    """The sharp narrow peaks of a profile: a ruled line, not a numeral or a wash."""
    vals = [v for _, v in prof]
    out = []
    i = 0
    while i < len(prof):
        if vals[i] >= minpk:
            j = i
            while j + 1 < len(prof) and vals[j + 1] >= 0.30 * max(vals[i:j + 2]):
                j += 1
            seg = prof[i:j + 1]
            pk = max(v for _, v in seg)
            half = [(p, v) for p, v in seg if v >= 0.35 * pk]
            if half[-1][0] - half[0][0] + 1 <= maxw:
                tot = sum(v for _, v in half)
                out.append((round(sum(p * v for p, v in half) / tot, 1), round(pk, 1)))
            i = j + 1
        else:
            i += 1
    return out


def _edge_drop(rules, lo, hi, margin=8.0):
    return [r for r in rules if lo + margin <= r[0] <= hi - margin]


def _merge(rules, gap=NS_MERGE_PX):
    """One ruled line answering twice is one line. Keep the stronger pick."""
    out = []
    for r in sorted(rules):
        if out and r[0] - out[-1][0] < gap:
            if r[1] > out[-1][1]:
                out[-1] = list(r)
        else:
            out.append(list(r))
    return [tuple(r) for r in out]


def _pair(rules, slot, wlo, whi, tol):
    best = None
    for a in range(len(rules)):
        for b in range(a + 1, len(rules)):
            p, q = rules[a][0], rules[b][0]
            w = q - p
            if not (wlo <= w <= whi):
                continue
            d = abs((p + q) / 2.0 - slot)
            if d <= tol and (best is None or d < best[0]):
                best = (d, p, q)
    return None if best is None else (best[1], best[2])


def _single(rules, slot, tol):
    cand = [r for r in rules if abs(r[0] - slot) <= tol]
    if not cand:
        return None
    return max(cand, key=lambda r: r[1])[0]


# -------------------------------------------------------------- the ENU frame


def _frame():
    g = json.loads(GCP.read_text())
    d = json.loads((ROOT / "data/datum.json").read_text())
    # T-1092 re-seated this trace onto the ELEVEN-POINT registration T-1091 adopted,
    # and re-baked what stands on the ground that moved. `fit` IS that registration;
    # the eight-point fit it superseded is kept beside it as `retained_fit` for the
    # adjudication that compares the two. Reading `retained_fit` here would seat the
    # ground on a fit this project no longer holds.
    c = g["fit"]["coefficients"]

    def to_local(px, py):
        return (c["a"] * px + c["b"] * py + c["c"] - d["origin_utm_e"],
                c["d"] * px + c["e"] * py + c["f"] - d["origin_utm_n"])

    return to_local


def _dist(to_local, p, q, horizontal, ref):
    if horizontal:
        e0, n0 = to_local(ref, p)
        e1, n1 = to_local(ref, q)
    else:
        e0, n0 = to_local(p, ref)
        e1, n1 = to_local(q, ref)
    return math.hypot(e1 - e0, n1 - n0), ((e0 + e1) / 2.0, (n0 + n1) / 2.0)


# ------------------------------------------------------------------- reading


def read_sheet():
    g, img = _sheet()
    im = _load_px(img)
    doc = {"windows": [], "east_west": {}, "north_south": {},
           "control": {"north_south_axis": {}, "east_west_axis": {}}, "wash": {}}

    for col in EW_COLUMNS:
        x0, x1 = col["x"]
        y0, y1 = col["y"]
        rules = _edge_drop(_rules(_debase(_profile(im, x0, y0, x1, y1, "h", SHEAR_EW)),
                                  minpk=9.0), y0, y1)
        doc["windows"].append({"id": col["id"], "axis": "east-west rules",
                               "crop_px": [x0, y0, x1, y1], "shear": SHEAR_EW,
                               "ref_px_x": x0, "through": col["through"],
                               "rules_px_y": [r[0] for r in rules]})
        slots = EW_SLOTS[col["id"]]
        for name, slot in slots.items():
            if name in EW_SINGLE:
                got = _single(rules, slot, EW_TOL)
                if got is not None:
                    doc["east_west"].setdefault(name, {})[col["id"]] = {"rule_px_y": [got]}
            else:
                lo, hi = EW_PAIR_WIDTH[name]
                got = _pair(rules, slot, lo, hi, EW_TOL)
                if got is not None:
                    doc["east_west"].setdefault(name, {})[col["id"]] = {
                        "rule_px_y": [got[0], got[1]]}

    base = NS_ROWS[0]["y"][0]
    for row in NS_ROWS:
        y0, y1 = row["y"]
        x0, x1 = NS_X
        rules = _merge(_edge_drop(_rules(_debase(_profile(im, x0, y0, x1, y1, "v", SHEAR_NS)),
                                         minpk=10.0), x0, x1))
        carry = SHEAR_NS * (y0 - base)
        found = {"rules_px_x": [r[0] for r in rules]}
        for name, slot in NS_SLOTS.items():
            got = _single(rules, slot + carry, NS_BORDER_TOL)
            if got is not None:
                found[name + "_px_x"] = got
        st = _pair(rules, NS_STREET["slot"] + carry, NS_STREET["width"][0],
                   NS_STREET["width"][1], NS_STREET["tol"])
        if st is not None:
            found["street_px_x"] = [st[0], st[1]]
        doc["windows"].append({"id": row["id"], "axis": "north-south rules",
                               "crop_px": [x0, y0, x1, y1], "shear": SHEAR_NS,
                               "ref_px_y": y0, "through": row["through"],
                               "slot_carry_px": round(carry, 2),
                               "rules_px_x": [r[0] for r in rules]})
        doc["north_south"][row["id"]] = found

    for key, spec in (("north_south_axis", CONTROL_NS), ("east_west_axis", CONTROL_EW)):
        x0, y0, x1, y1 = spec["window"]
        axis = "v" if key == "north_south_axis" else "h"
        lo, hi = (x0, x1) if axis == "v" else (y0, y1)
        rules = _edge_drop(_rules(_debase(_profile(im, x0, y0, x1, y1, axis, spec["shear"])),
                                  minpk=12.0), lo, hi)
        doc["windows"].append({"id": "control_" + key, "axis": axis,
                               "crop_px": [x0, y0, x1, y1], "shear": spec["shear"],
                               "rules_px": [r[0] for r in rules]})
        for name, slot in spec["slots"].items():
            got = _pair(rules, slot, spec["width"][0], spec["width"][1], spec["tol"])
            if got is not None:
                doc["control"][key][name] = {"rule_px": [got[0], got[1]]}

    doc["wash"] = _read_wash(im)
    return doc


def _median_rgb(im, box):
    crop = im.convert("RGB").crop(box)
    px = list(crop.getdata())
    out = []
    for ch in range(3):
        v = sorted(p[ch] for p in px)
        out.append(float(v[len(v) // 2]))
    return out


def _read_wash(im):
    paper = _median_rgb(im, PAPER_BOX)
    sw = {k: _median_rgb(im, b) for k, b in SWATCH_BOX.items()}
    patch = {k: _median_rgb(im, b) for k, b in WASH_BOX.items()}
    return {"paper_rgb": paper, "swatch_rgb": sw, "patch_rgb": patch,
            "paper_box": list(PAPER_BOX),
            "swatch_box": {k: list(v) for k, v in SWATCH_BOX.items()},
            "patch_box": {k: list(v) for k, v in WASH_BOX.items()}}


# ------------------------------------------------------------- the derivation


def _absorbance(rgb, paper):
    v = []
    for c, p in zip(rgb, paper):
        t = min(0.999, max(0.02, c / p))
        v.append(-math.log(t))
    n = math.sqrt(sum(x * x for x in v))
    return [x / n for x in v]


def _mean(xs):
    return sum(xs) / len(xs)


def _sd(xs):
    if len(xs) < 2:
        return 0.0
    m = _mean(xs)
    return math.sqrt(sum((x - m) ** 2 for x in xs) / (len(xs) - 1))


def derive(doc):
    """Everything metric, from the pixels in `doc` and the committed affine. No raster."""
    to_local = _frame()
    out = {}

    ew = {}
    for name, cols in doc["east_west"].items():
        ew[name] = {}
        for col, r in cols.items():
            ref = dict((c["id"], c["x"][0]) for c in EW_COLUMNS)[col]
            e, n = to_local(ref, r["rule_px_y"][0])
            rec = {"ref_px_x": ref, "rule_px_y": r["rule_px_y"],
                   "local_enu_m": [round(e, 1), round(n, 1)]}
            if len(r["rule_px_y"]) == 2:
                w, c = _dist(to_local, r["rule_px_y"][0], r["rule_px_y"][1], True, ref)
                rec["corridor_m"] = round(w, 2)
                rec["corridor_ft"] = round(w / FT, 1)
                rec["centre_local_enu_m"] = [round(c[0], 1), round(c[1], 1)]
            ew[name][col] = rec
    out["east_west"] = ew

    ns = {}
    for row_id, r in doc["north_south"].items():
        ref = dict((x["id"], x["y"][0]) for x in NS_ROWS)[row_id]
        rules = r["rules_px_x"]
        st = r.get("street_px_x")
        rec = {"ref_px_y": ref, "rules_px_x": rules}
        for k in ("west_border_px_x", "east_border_px_x"):
            if k in r:
                rec[k] = r[k]
        if st:
            w, c = _dist(to_local, st[0], st[1], False, ref)
            rec["north_south_street"] = {
                "rule_px_x": st, "corridor_m": round(w, 2),
                "corridor_ft": round(w / FT, 1),
                "centre_local_enu_m": [round(c[0], 1), round(c[1], 1)]}
            wb = rec.get("west_border_px_x")
            eb = rec.get("east_border_px_x")
            # A column's lots are only countable where its border was found. Where the
            # wash swallows the west border the row says nothing about the west column
            # rather than saying zero.
            if wb is not None:
                west = [x for x in rules if wb <= x <= st[0]]
                rec["west_column_lot_lines_px_x"] = west
                rec["west_column_lots"] = len(west) - 1
                rec["west_lot_front_m"] = [round(_dist(to_local, a, b, False, ref)[0], 2)
                                           for a, b in zip(west, west[1:])]
            if eb is not None:
                east = [x for x in rules if st[1] <= x <= eb]
                rec["east_column_lot_lines_px_x"] = east
                rec["east_column_lots"] = len(east) - 1
                rec["east_lot_front_m"] = [round(_dist(to_local, a, b, False, ref)[0], 2)
                                           for a, b in zip(east, east[1:])]
            if wb is not None and eb is not None:
                rec["tract_width_m"] = round(_dist(to_local, wb, eb, False, ref)[0], 2)
        ns[row_id] = rec
    out["north_south"] = ns

    ctl = {}
    for key, spec in (("north_south_axis", CONTROL_NS), ("east_west_axis", CONTROL_EW)):
        x0, y0, x1, y1 = spec["window"]
        horiz = key == "east_west_axis"
        ref = x0 if horiz else y0
        got = {}
        for name, r in doc["control"][key].items():
            w, _ = _dist(to_local, r["rule_px"][0], r["rule_px"][1], horiz, ref)
            got[name] = {"rule_px": r["rule_px"], "corridor_m": round(w, 2),
                         "corridor_ft": round(w / FT, 1), "platted_ft": 80.0}
        wid = [v["corridor_ft"] for v in got.values()]
        ctl[key] = {"corridors": got,
                    "read_ft": {"mean": round(_mean(wid), 1), "sd": round(_sd(wid), 1),
                                "n": len(wid)},
                    "method_over_platted": round(_mean(wid) / 80.0, 3)}
    out["control"] = ctl
    out["module"] = _module(out)
    out["identity"] = _identity(out, doc)
    out["wash"] = _wash_ruling(doc["wash"])
    out["sections"] = _sections()
    out["extent"] = _extent(out, to_local)
    return out


def _module(out):
    ew, ns = out["east_west"], out["north_south"]
    sx = out["control"]["north_south_axis"]["method_over_platted"]
    sy = out["control"]["east_west_axis"]["method_over_platted"]

    def tier_depth(col):
        nb = ew["north_border"][col]["rule_px_y"][0]
        mn = ew["michigan_st"][col]["rule_px_y"][0]
        ms = ew["michigan_st"][col]["rule_px_y"][1]
        sb = ew["south_border"][col]["rule_px_y"][0]
        to_local = _frame()
        ref = dict((c["id"], c["x"][0]) for c in EW_COLUMNS)[col]
        return (round(_dist(to_local, nb, mn, True, ref)[0], 2),
                round(_dist(to_local, ms, sb, True, ref)[0], 2))

    depths = {c: tier_depth(c) for c in ("col_west", "col_east")}
    alley = [ew[a][c]["corridor_m"] for a in ("alley_north_tier", "alley_south_tier")
             for c in ew[a]]
    mich = [ew["michigan_st"][c]["corridor_m"] for c in ew["michigan_st"]]
    street = [r["north_south_street"]["corridor_m"] for r in ns.values()
              if r.get("north_south_street")]
    wlots = [v for r in ns.values() for v in r.get("west_lot_front_m", [])]
    elots = [v for r in ns.values() for v in r.get("east_lot_front_m", [])]
    width = [r["tract_width_m"] for r in ns.values() if "tract_width_m" in r]
    return {
        "tract_width_m": {"mean": round(_mean(width), 2), "sd": round(_sd(width), 2),
                          "n": len(width)},
        "north_tier_depth_m": depths["col_west"][0],
        "south_tier_depth_m": depths["col_west"][1],
        "tier_depth_by_column_m": {k: list(v) for k, v in depths.items()},
        "michigan_st_corridor": {"read_m": round(_mean(mich), 2),
                                 "read_ft": round(_mean(mich) / FT, 1),
                                 "scaled_ft": round(_mean(mich) / FT / sy, 1),
                                 "n": len(mich)},
        "north_south_street_corridor": {"read_m": round(_mean(street), 2),
                                        "read_ft": round(_mean(street) / FT, 1),
                                        "scaled_ft": round(_mean(street) / FT / sx, 1),
                                        "n": len(street)},
        "alley_width": {"read_m": round(_mean(alley), 2),
                        "read_ft": round(_mean(alley) / FT, 1),
                        "scaled_ft": round(_mean(alley) / FT / sy, 1),
                        "sd_m": round(_sd(alley), 2), "n": len(alley),
                        "note": "reported, NOT settled: the sheets carry 3.7-4.5 per cent "
                                "local scale error, which is large against the 0.6 m "
                                "between a 16 ft and an 18 ft alley — the same refusal "
                                "data/traces/vectors/street_corridors_1834.json makes."},
        "west_column_lot_front_m": {"mean": round(_mean(wlots), 2), "sd": round(_sd(wlots), 2),
                                    "n": len(wlots), "samples": sorted(wlots)},
        "east_column_lot_front_m": {"mean": round(_mean(elots), 2), "sd": round(_sd(elots), 2),
                                    "n": len(elots), "samples": sorted(elots)},
        "lots_per_block_row": {
            "west_column": [r["west_column_lots"] for r in ns.values()
                            if "west_column_lots" in r],
            "east_column": [r["east_column_lots"] for r in ns.values()
                            if "east_column_lots" in r]},
        "reading": "The small parcels are the tract's signature and they are real: the "
                   "west column's lot frontages run well under the Original Town's, and "
                   "every block here carries a mid-block alley, which no Original Town "
                   "block on this sheet does.",
    }


def _identity(out, doc):
    """The two tests that say what the tract's streets ARE."""
    k = json.loads(KINZIE.read_text())
    mich = k["readings"]["east_west"]["michigan"][0]
    k_ref = mich["ref_px_x"]
    k_centre = _mean(mich["rule_px_y"])
    ours = out["east_west"]["michigan_st"]["col_west"]
    o_ref = ours["ref_px_x"]
    o_centre = _mean(ours["rule_px_y"])
    carried = {}
    for tag, shear in (("addition_slope_0.0176", k["windows"][0]["shear"]),
                       ("tract_slope_%.3f" % SHEAR_EW, SHEAR_EW)):
        carried[tag] = round(o_centre + shear * (k_ref - o_ref) - k_centre, 1)

    st = json.loads(STREETS.read_text())["streets"]
    market = [s for s in st if s["id"] == "market_north"][0]
    m_e = _mean([p[0] for p in market["path_local_enu_m"]])
    row = next(r for r in out["north_south"].values() if r.get("north_south_street"))
    ours_e = row["north_south_street"]["centre_local_enu_m"][0]

    return {
        "michigan_st_is_kinzies_addition_michigan_street": {
            "our_corridor_centre_px_y": round(o_centre, 1), "our_ref_px_x": o_ref,
            "addition_corridor_centre_px_y": round(k_centre, 1), "addition_ref_px_x": k_ref,
            "departure_px_when_carried": carried,
            "carry_px": k_ref - o_ref,
            "reading": "Carried east on the slope the Addition's own reading fitted, the "
                       "tract's Michigan St lands within two pixels — about a metre and a "
                       "half of ground — of the corridor centre Kinzie's Addition's "
                       "Michigan Street was read at, eleven hundred pixels away. On this "
                       "tract's own locally fitted slope it lands nine pixels off, which "
                       "is the honest size of the disagreement: the slope, not the "
                       "identification, is what the carry is uncertain in. The two are the "
                       "same street, drawn on either side of ground Wright leaves blank.",
            "caveat": "The ground between is unsurveyed on the sheet and carries no ruled "
                      "line, so this is a carry across 800 m of blank paper and not a "
                      "continuous trace. It is evidence of one street, not proof of one line.",
        },
        "north_south_street_is_market_street": {
            "our_centre_local_e_m": round(ours_e, 1),
            "market_north_local_e_m": round(m_e, 1),
            "departure_m": round(ours_e - m_e, 1),
            "reading": "The tract's north-south street stands 20.5 m east of the easting "
                       "`market_north` already holds in data/streets/1835.json, on the far "
                       "side of Kinzie Street from it. THE FIGURE WAS 16.7 m WHEN THIS "
                       "IDENTIFICATION WAS MADE, and T-0827 moved the other line: `market` "
                       "was re-fitted off the plat's 400 ft module instead of off the modern "
                       "junction on N Wacker Drive it had been hung from, which carried "
                       "`market_north` 3.8 m west with it. So the departure is now OUTSIDE "
                       "the 16.19 m RMS this sheet's own fit carries, by 4.3 m, and inside "
                       "it is no longer the thing to say. What the identification rests on "
                       "instead is unchanged and was always the stronger half: 20.5 m is "
                       "still less than a platted street's 24.38 m width, and there is no "
                       "other north-south street within a hundred metres for this one to be. "
                       "Market Street runs on north into this tract.",
        },
        "consequence": "Wright's second `Michigan St` is not a second street of the same "
                       "name — the premise T-0796 was filed on. The tract is platted on the "
                       "town's own grid lines and only its PARCEL module is its own.",
    }


def _wash_ruling(w):
    paper = w["paper_rgb"]
    sw = {k: _absorbance(v, paper) for k, v in w["swatch_rgb"].items()}
    out = {"paper_rgb": paper, "swatch_rgb": w["swatch_rgb"], "patch_rgb": w["patch_rgb"],
           "paper_box": w["paper_box"], "swatch_box": w["swatch_box"],
           "patch_box": w["patch_box"], "similarity": {}}
    for name, rgb in w["patch_rgb"].items():
        a = _absorbance(rgb, paper)
        sims = sorted(((round(sum(x * y for x, y in zip(a, sw[k])), 4), k) for k in sw),
                      reverse=True)
        out["similarity"][name] = [{"swatch": k, "cos": s} for s, k in sims]
    pair = round(sum(x * y for x, y in zip(sw["6_surveyed_blank_1833"],
                                           sw["9_part_of_canal_sec_no_9"])), 4)
    out["swatch_6_against_swatch_9"] = pair
    out["ruling"] = (
        "The control works: the School Section's band on the map names its own swatch at "
        "0.99 and nothing else within 0.09. Run on the tract's band, the same measurement "
        "names the OLIVE FAMILY and separates nothing inside it — swatches 4, 6 and 9 all "
        "come back within six thousandths of each other, and 6 and 9 are themselves alike "
        "to %.4f. What it does settle is the six it refuses: the blue Military "
        "Reservation, the Original Town's red, Wabansia's red, Fractional Section 15's "
        "red, the School Section's yellow and the orange are all a tenth away and none of "
        "them is this tract. Of the three olives, 4 is `Kinzie's Addn` and Kinzie's "
        "Addition is a mile east and identified, so what is left is `Surveyed ————— "
        "1833`, the legend entry whose name Wright left blank, or `Part of Canal Sec. No. "
        "9`. The wash cannot choose between those two and this file does not." % pair)
    return out


def _sections():
    """The PLSS numbering, from the committed control, once and in writing."""
    g = json.loads(GCP.read_text())
    d = json.loads((ROOT / "data/datum.json").read_text())
    g1 = [p for p in g["gcps"] if p["id"] == "G1"][0]
    e = g1["modern"]["utm_e"] - d["origin_utm_e"]
    n = g1["modern"]["utm_n"] - d["origin_utm_n"]
    st = json.loads(STREETS.read_text())["streets"]
    kinzie = [s for s in st if s["id"] == "kinzie"][0]
    k_n = _mean([p[1] for p in kinzie["path_local_enu_m"]])
    # Chicago's street numbering runs 800 to the mile from Madison Street.
    kinzie_hundreds = (k_n - n) / MILE_M * 800.0
    return {
        "corner": {"gcp": "G1", "map_feature": g1["map_feature"],
                   "feature_note": g1["feature_note"],
                   "local_enu_m": [round(e, 1), round(n, 1)]},
        "rule": "In T39N R14E the sections of a row run 7-12 west to east and 13-18 east "
                "to west, so at the State/Madison corner section 9 lies north-west, 10 "
                "north-east, 16 south-west and 15 south-east — which is the corner's own "
                "committed description.",
        "section_9": {"east_m": [round(e - MILE_M, 1), round(e, 1)],
                      "north_m": [round(n, 1), round(n + MILE_M, 1)],
                      "note": "Madison Street south, State Street east, one mile each way: "
                              "the canal's section, and the legend's `Part of Canal Sec. No. 9`."},
        "section_16": {"east_m": [round(e - MILE_M, 1), round(e, 1)],
                       "north_m": [round(n - MILE_M, 1), round(n, 1)],
                       "note": "directly south of 9 — the School Section, which the sheet "
                               "letters and washes a mile south of this tract."},
        "check": {"kinzie_street_local_n_m": round(k_n, 1),
                  "derived_hundreds_north": round(kinzie_hundreds),
                  "actual_hundreds_north": 400,
                  "note": "Chicago numbers 800 to the mile from Madison. Run the committed "
                          "section corner and the committed Kinzie Street line through that "
                          "and Kinzie comes out at 390 north against the 400 it carries — "
                          "twenty metres, less than this sheet's own 16.19 m RMS plus half "
                          "a street. The derivation was not fitted to Kinzie Street, so "
                          "that is the check rather than the claim."},
        "answer_to_the_owner": (
            "The tract is in SECTION 9, not fractional section 16. Section 16 is the "
            "School Section a mile south, which this sheet letters, washes and names in "
            "its own legend; no tract north of the river can be in it on the numbering "
            "the project's own ground control carries. What is true of the owner's "
            "reading is the instinct behind it: the tract IS in a named canal section, "
            "and section 9's number is a key into data/research/land_sales/ exactly as "
            "he expected — it is 9."),
    }


def _extent(out, to_local):
    ns = out["north_south"]["tier1_north"]
    ew = out["east_west"]
    corners = {}
    for tag, x, y in (("nw", ns["west_border_px_x"], ew["north_border"]["col_west"]["rule_px_y"][0]),
                      ("ne", ns["east_border_px_x"], ew["north_border"]["col_east"]["rule_px_y"][0]),
                      ("sw", ns["west_border_px_x"], ew["south_border"]["col_west"]["rule_px_y"][0]),
                      ("se", ns["east_border_px_x"], ew["south_border"]["col_east"]["rule_px_y"][0])):
        e, n = to_local(x, y)
        corners[tag] = {"px": [x, y], "local_enu_m": [round(e, 1), round(n, 1)]}
    return {
        "_doc": "The tract's four corners, read as the crossing of its committed border "
                "rules. Read through the sheet's own fit, which carries 16.19 m RMS — this "
                "is where the sheet puts the tract, not where the town's committed grid "
                "would seat it. Seating is the second piece of T-0796 and is not done here.",
        "corners": corners,
        "south_border_note": "The tract's south border is its own rule, north of Kinzie "
                             "Street's north rule by about 25 px — the tract fronts on "
                             "Kinzie rather than being bounded by its centre line.",
    }


# ------------------------------------------------------------------ document


def _document(doc, out):
    g = json.loads(GCP.read_text())
    return {
        "_doc": __doc__.strip(),
        "ticket": "T-1076 (piece 1 of T-0796: the reading)",
        "raster": {k: g["raster"][k] for k in
                   ("working_copy", "width", "height", "dpi", "sha256", "source_id")},
        "registration": "data/traces/gcp/wright_1834_nara_hup_gcps.json, `fit` "
                        "(NA pixel -> EPSG:26916, RMS 16.19 m on eight control points)",
        "method": "tools/read_michigan_st_tract.py — ink projected onto one axis over the "
                  "windows below, the profile baseline-subtracted against a rolling median "
                  "so the tract's wash cannot pass for ink, sharp narrow peaks taken as "
                  "ruled lines. `--check` re-derives every metre here from the pixels "
                  "beside it without opening the raster; `--check-sheet` re-reads the sheet.",
        "confidence": "attested",
        "confidence_note": "Every number here is a measurement of a stated raster at a "
                           "stated window by a stated method, and what it is documented "
                           "ABOUT is the sheet. The identifications under `identity` are "
                           "readings of the sheet too. The tract's NAME is not here, "
                           "because no source in this repository gives one.",
        "windows": doc["windows"],
        "readings": {"east_west": out["east_west"], "north_south": out["north_south"]},
        "module": out["module"],
        "control": out["control"],
        "identity": out["identity"],
        "wash": out["wash"],
        "sections": out["sections"],
        "extent": out["extent"],
        "open": [
            "The tract's NAME, and who platted it: not in this repository's corpus. "
            "Andreas on the additions north of the river, the Democrat's 1834-35 land "
            "notices and the canal commissioners' own sales are where it will be.",
            "The curved road that leaves the Kinzie/North Water corner and runs north "
            "through this tract is drawn and unread. It belongs with the seating.",
            "Seating: the street, the alley, the parcels and the road into "
            "data/streets/1835.json and a tract layer. The Addition's precedent is to "
            "seat the module on committed lines rather than on this sheet's fit "
            "(tools/seat_kinzie_addition_streets.py); the lines to seat on here are "
            "`michigan_north` and `market_north`, which is exactly what `identity` "
            "above says these two streets are.",
        ],
    }


# --------------------------------------------------------------------- entry


def _pixels_only(written):
    """The committed pixel evidence, in the shape read_sheet() returns it."""
    doc = {"windows": written["windows"], "east_west": {}, "north_south": {},
           "control": {"north_south_axis": {}, "east_west_axis": {}},
           "wash": {"paper_rgb": written["wash"]["paper_rgb"],
                    "swatch_rgb": written["wash"]["swatch_rgb"],
                    "patch_rgb": written["wash"]["patch_rgb"],
                    "paper_box": written["wash"]["paper_box"],
                    "swatch_box": written["wash"]["swatch_box"],
                    "patch_box": written["wash"]["patch_box"]}}
    for name, cols in written["readings"]["east_west"].items():
        doc["east_west"][name] = {c: {"rule_px_y": v["rule_px_y"]} for c, v in cols.items()}
    for row, v in written["readings"]["north_south"].items():
        keep = {"rules_px_x": v["rules_px_x"]}
        for k in ("west_border_px_x", "east_border_px_x"):
            if k in v:
                keep[k] = v[k]
        if v.get("north_south_street"):
            keep["street_px_x"] = v["north_south_street"]["rule_px_x"]
        doc["north_south"][row] = keep
    for key in ("north_south_axis", "east_west_axis"):
        for name, v in written["control"][key]["corridors"].items():
            doc["control"][key][name] = {"rule_px": v["rule_px"]}
    return doc


def _diff(a, b, path="", bad=None):
    bad = [] if bad is None else bad
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b)):
            if k == "_doc" or k.endswith("note") or k in ("reading", "ruling", "caveat",
                                                          "consequence", "rule",
                                                          "answer_to_the_owner"):
                continue
            _diff(a.get(k, "<missing>"), b.get(k, "<missing>"), f"{path}.{k}", bad)
    elif isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            bad.append(f"{path}: length {len(a)} vs {len(b)}")
        else:
            for i, (x, y) in enumerate(zip(a, b)):
                _diff(x, y, f"{path}[{i}]", bad)
    elif isinstance(a, float) or isinstance(b, float):
        try:
            if abs(float(a) - float(b)) > 0.051:
                bad.append(f"{path}: {a} vs {b}")
        except (TypeError, ValueError):
            bad.append(f"{path}: {a!r} vs {b!r}")
    elif a != b:
        bad.append(f"{path}: {a!r} vs {b!r}")
    return bad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--check-sheet", action="store_true")
    a = ap.parse_args()

    if a.check:
        written = json.loads(OUT.read_text())
        again = _document(_pixels_only(written), derive(_pixels_only(written)))
        bad = _diff(written, again)
        if bad:
            print("the committed reading does not re-derive from its own pixels:")
            for b in bad[:40]:
                print("   ", b)
            return 1
        print(f"{OUT.name}: re-derives from its own pixels through the committed affine")
        return 0

    doc = read_sheet()
    out = derive(doc)
    written = _document(doc, out)

    if a.check_sheet:
        prev = json.loads(OUT.read_text())
        bad = _diff(prev, written)
        if bad:
            print("the sheet does not re-read as committed:")
            for b in bad[:40]:
                print("   ", b)
            return 1
        print(f"{OUT.name}: re-reads identically from {written['raster']['working_copy']}")
        return 0

    if a.write:
        OUT.write_text(json.dumps(written, indent=1, ensure_ascii=False) + "\n")
        print(f"wrote {OUT.relative_to(ROOT)}")
        return 0

    print(json.dumps({"module": out["module"], "control": out["control"],
                      "identity": out["identity"], "sections": out["sections"]},
                     indent=1, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
