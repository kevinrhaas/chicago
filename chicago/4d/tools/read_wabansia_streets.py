#!/usr/bin/env python3
"""Read Wabansia's streets off Wright's 1834 survey — the seven corridors and the two
names the owner flagged as doubtful.

    tools/read_wabansia_streets.py                print the reading
    tools/read_wabansia_streets.py --write        write data/traces/wabansia_streets.json
    tools/read_wabansia_streets.py --check        re-derive every metre from the committed pixels
    tools/read_wabansia_streets.py --check-sheet  re-measure the rules off the raster
    tools/read_wabansia_streets.py --self-test    break each assertion and watch it fire

WHAT THIS FILE IS. Wabansia — Wright letters it *Wonbonsia*, the Democrat and Andreas
*Wabansia* — is the tract north of Kinzie Street and west of the North Branch, surveyed
in 1831 and the earliest speculative addition laid out at Chicago. The project has had
nothing there: no street, no block, no tract edge. This is the first reading of its
street grid, and it reads the EAST-WEST corridors only. It authors no ground: a corridor
here is a pair of ruled lines on a raster, and where that pair belongs on modern ground
is the seating question T-0790's successor carries.

THE SHEET is the National Archives / Historic Urban Plans facsimile registered as
`wright_1834_nara_hup` (5050 x 6628 px at 600 dpi), the same sheet and the same affine
T-1060 and T-1061 read Kinzie's Addition on, for the same reason: at 600 dpi the ruled
lines separate and the lettering can be read letter by letter.

THE METHOD is T-1060's, imported rather than copied — `_profile` projects a window's ink
onto one axis along a fitted shear, `_rules` takes the sharp narrow peaks as ruled lines,
`_frame` carries a pixel to local ENU through the sheet's own committed affine. What is
new here is the DISCRIMINATION, because Wabansia's does not work the way the Addition's
did. In Kinzie's Addition a street corridor is wider than the gaps around it and a width
test finds it. In Wabansia it is not: the blocks are four lots deep at a 33 px lot pitch
and the corridors run 29-39 px, so a width test cannot tell a street from a lot line and
returned five wrong corridors when it was tried. What settles it is Wright's own
lettering: he writes each name INSIDE its corridor, so the corridor is the rule pair that
brackets the name's glyphs, and every pair below was confirmed against the crop the name
was read in. That is why `label_crop_px` is committed beside `rule_px_y` — the crop is
the evidence for which pair was taken, not decoration.

THE TWO DOUBTS THE OWNER RAISED, both settled here on the registered scan:

  * `Right` or `Hight` — HIGHT. The capital carries a looped ascender and a second
    vertical joined by a mid-height crossbar, and it is the same glyph Wright draws for
    the H of `Hubbard` two corridors south on the same sheet. An R in this hand has a
    bowl; this has none. The two crops are committed side by side so the next reader can
    disagree with the comparison rather than with an assertion.
  * `Kain` or `Kane` — KAIN. The third letter carries a dot and the fourth is an n with
    two shoulders; there is no terminal e. This street is inside the water-lot triangle,
    not in the block grid, and is recorded here as a name only.

WHAT IS NOT READ, and is the next run's, not a gap to be filled by guessing:

  * The NORTH-SOUTH streets. Wright letters none of them in Wabansia, so the lettering
    that disciplines the east-west read has nothing to say about them, and the width test
    that would have to stand in its place is the one this tract defeats.
  * The BLOCK NUMERALS (some 79 of them), the water-lot strip, the tract polygon, and
    who the sources put on the ground. T-0790 was split for them.
  * The SEATING. Wabansia's south line is Kinzie Street, which this project has already
    committed off the Thompson plat, so the sheet can be priced against it: § cross_check
    carries the gap, and it is well inside the 16.19 m RMS this sheet's own registration
    admits. A gap that small is a reason to seat the tract on the committed line rather
    than on the sheet — but a seating is a separate demonstration and is not made here.
"""
from __future__ import annotations

import argparse
import importlib
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
_k = importlib.import_module("read_kinzie_addition_streets")

ROOT = Path(__file__).resolve().parents[1]
GCP = ROOT / "data/traces/gcp/wright_1834_nara_hup_gcps.json"
ADDITION = ROOT / "data/traces/kinzie_addition_street_grid.json"
OUT = ROOT / "data/traces/wabansia_streets.json"
FT = 0.3048

# The raster dy/dx of Wabansia's east-west rules, fitted the way T-1060 fitted the
# Addition's: the slope that maximises the variance of the projection, because the
# flattest profile a wrong slope can give is the blurred one. Scanned over
# +/-0.040 in 0.001 steps on the window x 700-1220, y 960-2100.
SHEAR_EW = 0.019

# The columns the corridors are read in. None of them holds lettering, which is the
# whole requirement: Wright letters the names in the corridors and a name is ink in
# exactly the gap the reading is trying to find. `col_west` carries five of the seven;
# it cannot reach north of Trade Street because the tract's west boundary slants away
# from it there, which is why the other two have windows of their own.
WINDOWS = {
    "col_west": {"x": (700, 790), "y": (1000, 2110),
                 "through": "the westernmost block column, Trade Street to Kinzie Street"},
    "col_east": {"x": (990, 1050), "y": (1040, 1125),
                 "through": "the column east of Wright's `Free` and west of his `St`"},
    "col_trade": {"x": (880, 980), "y": (1150, 1340),
                  "through": "the gap between Wright's `Trade` and his `St`"},
}

# THE READING. `rule_px_y` is the corridor's two ruled edges in NA raster pixels;
# `label_crop_px` is the crop Wright's name for it was read in, and the crop is what
# says this pair is a street and not a lot line.
STREETS = [
    {"id": "free", "name_on_sheet": "Free", "order": 1, "window": "col_east",
     "rule_px_y": [1064.5, 1096.4], "label_crop_px": [770, 1055, 1060, 1110],
     "name_confidence": "documented"},
    {"id": "trade", "name_on_sheet": "Trade", "order": 2, "window": "col_trade",
     "rule_px_y": [1235.4, 1264.3], "label_crop_px": [700, 1215, 1100, 1320],
     "name_confidence": "documented"},
    {"id": "sailors", "name_on_sheet": "Sailors", "order": 3, "window": "col_west",
     "rule_px_y": [1393.3, 1427.4], "label_crop_px": [690, 1380, 1200, 1450],
     "name_confidence": "documented"},
    {"id": "hight", "name_on_sheet": "Hight", "order": 4, "window": "col_west",
     "rule_px_y": [1556.6, 1595.8], "label_crop_px": [780, 1530, 1220, 1610],
     "name_confidence": "documented",
     "note": "The owner's crop read this as `Right or Hight`; see § adjudications. "
             "Its corridor is the widest of the seven at 39.2 px against a 33.9 px "
             "mean, and the excess is one rule-width: the south edge is drawn twice "
             "here, a kerb line beside the rule, and the outer of the two is taken."},
    {"id": "owen", "name_on_sheet": "Owen", "order": 5, "window": "col_west",
     "rule_px_y": [1725.6, 1760.8], "label_crop_px": [690, 1700, 1200, 1780],
     "name_confidence": "documented"},
    {"id": "hubbard", "name_on_sheet": "Hubbard", "order": 6, "window": "col_west",
     "rule_px_y": [1889.2, 1924.1], "label_crop_px": [840, 1890, 1090, 1950],
     "name_confidence": "documented"},
    {"id": "kinzie", "name_on_sheet": "Kinzie", "order": 7, "window": "col_west",
     "rule_px_y": [2061.3, 2095.8], "label_crop_px": [1150, 2060, 1450, 2110],
     "name_confidence": "documented",
     "note": "The tract's south line, and the one street here the project already "
             "carries: `kinzie` in data/streets/1835.json, committed off the Thompson "
             "plat. It is read again on this sheet as the tract's own southern bound."},
]

# Inside the water-lot triangle between the block grid and the North Branch. Names
# only: the triangle's lots are T-0790's successor's, and a street with no measured
# corridor is not given one here.
TRACT_STREETS = [
    {"id": "kain", "name_on_sheet": "Kain", "label_crop_px": [1250, 1700, 1500, 1790],
     "name_confidence": "documented",
     "note": "The owner's crop read this as `Kain` or `Kane`; see § adjudications."},
    {"id": "water", "name_on_sheet": "Water", "label_crop_px": [1290, 1880, 1520, 1990],
     "name_confidence": "documented",
     "note": "Wright letters a Water Street inside the triangle. This reading first "
             "glossed it as fronting the North Branch, as he does on both banks "
             "downstream; T-1077 measured the strip and refused that. Both names sit in "
             "corridors that CROSS the lots, square to the ranks, from the block grid to "
             "the water — see data/traces/wabansia_water_lots.json § corridors. The name "
             "is this reading's and stands; what it is a name of is that one's."},
]

ADJUDICATIONS = [
    {"id": "hight_not_right", "reading": "Hight", "refused": "Right",
     "crop_px": [780, 1530, 1220, 1610],
     "comparison_crop_px": [840, 1890, 1090, 1950],
     "comparison": "the H of `Hubbard`, two corridors south on the same sheet",
     "confidence": "documented",
     "argument": "The capital is a looped ascender and a second vertical joined by a "
                 "mid-height crossbar, with no bowl. It is stroke for stroke Wright's H "
                 "in `Hubbard`. An R in this hand closes a bowl against the stem."},
    {"id": "kain_not_kane", "reading": "Kain", "refused": "Kane",
     "crop_px": [1250, 1700, 1500, 1790],
     "comparison_crop_px": None,
     "comparison": "read letter by letter at 4x; no comparison glyph needed",
     "confidence": "documented",
     "argument": "K-a-i-n. The third letter carries its dot and the fourth is an n with "
                 "two shoulders. There is no terminal e."},
]

# What the width test would have produced, kept because the negative is the finding:
# a run that reaches for T-1060's discrimination here should see why it fails.
WIDTH_TEST_REFUSED = {
    "lot_pitch_px": 33.0,
    "corridor_px_range": [28.9, 39.2],
    "why": "Wabansia's blocks are four lots deep at a 33 px lot pitch and its corridors "
           "run 28.9-39.2 px, so the two populations overlap and a width test cannot "
           "separate them. Run against the label slots it returned corridors for five "
           "of the seven streets and four of those five were wrong by a rule.",
}


# ------------------------------------------------------------------ the read

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


def _control():
    """The price of this method on this sheet, borrowed from T-1060 rather than re-run.

    The Original Town's corridors are platted at 80 ft and T-1060 read three of them on
    this sheet by this method at 83.6 ft mean. A corridor measured here is only
    meaningful beside that number, so every foot figure is reported raw AND divided by
    the ratio."""
    a = json.loads(ADDITION.read_text())["control_summary"]
    return a["method_over_read"], a["original_town_read_ft"]


def _span(to_local, a, b, ref_x):
    e0, n0 = to_local(ref_x, a)
    e1, n1 = to_local(ref_x, b)
    return math.hypot(e1 - e0, n1 - n0), ((e0 + e1) / 2.0, (n0 + n1) / 2.0)


def read():
    to_local = _frame()
    ratio, control_read = _control()
    doc = {"streets": [], "water_lot_tract_streets": TRACT_STREETS,
           "adjudications": ADJUDICATIONS}

    for s in STREETS:
        a, b = s["rule_px_y"]
        ref_x = WINDOWS[s["window"]]["x"][0]
        w, centre = _span(to_local, a, b, ref_x)
        r = dict(s)
        r["ref_px_x"] = ref_x
        r["corridor_px"] = round(b - a, 1)
        r["corridor_m"] = round(w, 2)
        r["corridor_ft_raw"] = round(w / FT, 1)
        r["corridor_ft_controlled"] = round(w / FT / ratio, 1)
        r["centre_px_y"] = round((a + b) / 2.0, 2)
        r["centre_local_enu_m"] = [round(centre[0], 1), round(centre[1], 1)]
        r["geometry_confidence"] = "inferred"
        r.setdefault("note", None)
        doc["streets"].append(r)

    doc["module"] = _module(doc, to_local, ratio)
    doc["control"] = {"original_town_platted_ft": 80.0,
                      "original_town_read_ft": control_read,
                      "method_over_read": ratio,
                      "source": "data/traces/kinzie_addition_street_grid.json § control_summary",
                      "reading": "A corridor on this sheet is not measured against a "
                                 "ruler; it is measured against the Original Town's "
                                 "platted 80 ft on the same sheet by the same method."}
    doc["width_test_refused"] = WIDTH_TEST_REFUSED
    doc["cross_check"] = _cross_check(doc)
    return doc


def _cross_check(doc):
    """Kinzie Street is on this sheet AND already committed off the Thompson plat, so the
    two can be put beside one another — the only check this reading can make against
    ground the project already holds."""
    k = [s for s in doc["streets"] if s["id"] == "kinzie"][0]
    e, n = k["centre_local_enu_m"]
    path = [s for s in json.loads((ROOT / "data/streets/1835.json").read_text())["streets"]
            if s["id"] == "kinzie"][0]["path_local_enu_m"]
    (e0, n0), (e1, n1) = path[0], path[-1]
    committed_n = n0 + (n1 - n0) * (e - e0) / (e1 - e0)
    gap = abs(committed_n - n)
    # The RMS of the registration this reading is carried through, READ from it rather
    # than written down here: T-1091 changed the fit and T-1092 re-seated this reading
    # onto it, and a figure typed into a tool does not follow.
    rms = json.loads(GCP.read_text())["fit"]["rms_m"]
    inside = gap <= rms
    return {
        "street": "kinzie",
        "sheet_centre_local_enu_m": [e, n],
        "committed_line": "data/streets/1835.json § kinzie (Thompson plat, T-0713)",
        "committed_n_at_same_e_m": round(committed_n, 1),
        "extrapolated_west_of_committed_end_m": round(e0 - e, 1),
        "gap_m": round(gap, 1),
        "sheet_registration_rms_m": rms,
        "gap_inside_registration_rms": inside,
        "reading": "The sheet puts Kinzie Street "
                   f"{round(gap, 1)} m south of where the committed line runs at the same "
                   f"easting, against a registration that admits {rms} m RMS — "
                   + ("inside it. " if inside else
                      "OUTSIDE it, by "
                      f"{round(gap - rms, 1)} m. Under the eight-point fit T-1091 "
                      "superseded the same gap was 8.8 m and inside; the eleven-point "
                      "fit that replaced it is the better registration over the sheet as "
                      "a whole and the worse one here, which is what a fit refitted at "
                      "the sheet's foot does to its north-west corner. ") +
                   "THE IDENTIFICATION DOES NOT REST ON THIS GAP: Wright letters "
                   "`Kinzie` inside this corridor, which is why Wabansia's south line "
                   "and the town's Kinzie Street are read as the same street. The gap "
                   "measures how well the registration carries that reading onto the "
                   "committed line, and nothing else. Note the committed line is "
                   f"extrapolated {round(e0 - e, 1)} m west of its own west end to meet "
                   "this tract, so it is a consistency check and not a control point.",
    }


def _module(doc, to_local, ratio):
    ws = [s["corridor_px"] for s in doc["streets"]]
    ms = [s["corridor_m"] for s in doc["streets"]]
    ctr = [s["centre_px_y"] for s in doc["streets"]]
    tiers = [round(b - a, 2) for a, b in zip(ctr, ctr[1:])]
    ref_x = WINDOWS["col_west"]["x"][0]
    tier_m = [round(_span(to_local, a, b, ref_x)[0], 2) for a, b in zip(ctr, ctr[1:])]
    mean_tier_m = sum(tier_m) / len(tier_m)
    mean_corr_m = sum(ms) / len(ms)
    block_m = mean_tier_m - mean_corr_m
    return {
        "corridor_px": {"mean": round(sum(ws) / len(ws), 2), "sd": round(_sd(ws), 2),
                        "n": len(ws), "min": min(ws), "max": max(ws)},
        "corridor_m": {"mean": round(mean_corr_m, 2), "sd": round(_sd(ms), 2)},
        "corridor_ft_raw": round(mean_corr_m / FT, 1),
        "corridor_ft_controlled": round(mean_corr_m / FT / ratio, 1),
        "tier_pitch_px": tiers,
        "tier_pitch_m": {"mean": round(mean_tier_m, 2), "sd": round(_sd(tier_m), 2),
                         "n": len(tier_m), "each": tier_m},
        "tier_pitch_ft_raw": round(mean_tier_m / FT, 1),
        "tier_pitch_ft_controlled": round(mean_tier_m / FT / ratio, 1),
        "block_depth_m": round(block_m, 2),
        "block_depth_ft_raw": round(block_m / FT, 1),
        "block_depth_ft_controlled": round(block_m / FT / ratio, 1),
        "lots_per_block": 4,
        "lot_depth_ft_raw": round(block_m / 4 / FT, 1),
        "reading": (
            f"Seven corridors at a {sum(ws)/len(ws):.1f} px mean and six tiers at a "
            f"{sum(tiers)/len(tiers):.1f} px mean: Wabansia is laid out as a block four "
            f"lots deep plus a street, repeated. The corridor reads "
            f"{mean_corr_m / FT:.1f} ft raw and {mean_corr_m / FT / ratio:.1f} ft against "
            f"the Original Town's platted 80 ft read on this sheet by this method — which "
            f"is to say Wabansia is platted on the town's own street width, inside a "
            f"control that itself spreads 5.2 ft. The block runs {block_m / FT:.0f} ft raw "
            f"on four lots of {block_m / 4 / FT:.0f} ft. The regularity is the finding: the "
            f"six tiers scatter {_sd(tiers):.1f} px, about {_sd(tier_m):.0f} m, over a "
            f"1,000 px run."),
    }


def _sd(xs):
    if len(xs) < 2:
        return 0.0
    m = sum(xs) / len(xs)
    return math.sqrt(sum((x - m) ** 2 for x in xs) / (len(xs) - 1))


def _wrap(doc):
    g = json.loads(GCP.read_text())
    return {
        "_doc": __doc__,
        "ticket": "T-0790",
        "raster": {k: g["raster"][k] for k in
                   ("working_copy", "width", "height", "dpi", "sha256", "source_id")},
        # The RMS of the fit THIS READING IS CARRIED THROUGH — the eleven-point one in
        # force since T-1091, onto which T-1092 re-seated this reading. See _frame above.
        "registration": {"gcp_file": "data/traces/gcp/wright_1834_nara_hup_gcps.json",
                         "fit": "fit — the eleven-point registration in force (T-1091), "
                                "re-seated onto it by T-1092",
                         "rms_m": g["fit"].get("rms_m")},
        "method": {"shear_ew": SHEAR_EW, "windows": WINDOWS,
                   "discrimination": "the corridor is the rule pair bracketing Wright's "
                                     "own lettering; see § width_test_refused"},
        **doc,
    }


# ----------------------------------------------------------------- the gates

def check():
    """The cheap half: every metre in the committed file re-derives from the pixels
    committed beside it, through the committed affine. No raster is opened."""
    if not OUT.exists():
        raise SystemExit(f"{OUT} is not committed")
    have = json.loads(OUT.read_text())
    want = _wrap(read())
    bad = []

    for a, b in zip(have["streets"], want["streets"]):
        if a["id"] != b["id"]:
            bad.append(f"street order moved: {a['id']} where {b['id']} is read")
            continue
        for k in ("corridor_m", "corridor_ft_raw", "corridor_ft_controlled",
                  "centre_px_y", "corridor_px", "name_on_sheet", "order"):
            if a[k] != b[k]:
                bad.append(f"{a['id']}.{k}: committed {a[k]}, re-derives {b[k]}")
        if [round(v, 1) for v in a["centre_local_enu_m"]] != b["centre_local_enu_m"]:
            bad.append(f"{a['id']}.centre_local_enu_m: committed "
                       f"{a['centre_local_enu_m']}, re-derives {b['centre_local_enu_m']}")

    if have.get("cross_check") != want["cross_check"]:
        for k, v in want["cross_check"].items():
            if have.get("cross_check", {}).get(k) != v:
                bad.append(f"cross_check.{k}: committed "
                           f"{have.get('cross_check', {}).get(k)}, re-derives {v}")

    if have["module"] != want["module"]:
        for k, v in want["module"].items():
            if have["module"].get(k) != v:
                bad.append(f"module.{k}: committed {have['module'].get(k)}, re-derives {v}")

    ids = [s["id"] for s in have["streets"]]
    if ids != sorted(ids, key=lambda i: [s["order"] for s in have["streets"]
                                         if s["id"] == i][0]):
        bad.append("the streets are not committed in Wright's north-to-south order")
    for s in have["streets"]:
        if s["rule_px_y"][0] >= s["rule_px_y"][1]:
            bad.append(f"{s['id']}: corridor edges are not north-then-south")
        x0, y0, x1, y1 = s["label_crop_px"]
        c = s["centre_px_y"]
        if not (y0 <= c <= y1):
            bad.append(f"{s['id']}: the committed corridor centre {c} is outside the "
                       f"crop {s['label_crop_px']} its name was read in")
    for a in have["adjudications"]:
        if a["confidence"] == "documented" and not a.get("argument"):
            bad.append(f"adjudication {a['id']} is documented with no argument")

    if bad:
        print("wabansia street reading FAILED", file=sys.stderr)
        for b in bad:
            print("  " + b, file=sys.stderr)
        raise SystemExit(1)
    print(f"wabansia streets: {len(have['streets'])} corridors re-derive from their "
          f"committed pixels; {len(have['adjudications'])} adjudications carry arguments")


def check_sheet():
    """The raster half: the rules this reading committed are still where the sheet puts
    them. Opens the 5050 x 6628 scan, so the PR runs it and check.sh does not."""
    img = _k._sheet()[1]
    bad = []
    for s in STREETS:
        w = WINDOWS[s["window"]]
        prof = _k._profile(img, w["x"][0], w["y"][0], w["x"][1], w["y"][1], "h", SHEAR_EW)
        rules = [p for p, _ in _k._rules(prof, minpk=8.0)]
        for want in s["rule_px_y"]:
            near = min(rules, key=lambda p: abs(p - want)) if rules else None
            if near is None or abs(near - want) > 2.0:
                bad.append(f"{s['id']}: no rule within 2 px of {want} in "
                           f"{s['window']} (nearest {near})")
    if bad:
        print("wabansia street reading FAILED against the sheet", file=sys.stderr)
        for b in bad:
            print("  " + b, file=sys.stderr)
        raise SystemExit(1)
    print(f"wabansia streets: all {2 * len(STREETS)} committed rules re-measure off the "
          f"raster within 2 px")


def self_test():
    """Break each assertion and watch it fire."""
    import copy
    good = _wrap(read())
    fired = 0
    for label, mutate in (
        ("a corridor width moved", lambda d: d["streets"][2].__setitem__("corridor_m", 99.0)),
        ("a street changed name", lambda d: d["streets"][3].__setitem__("name_on_sheet", "Right")),
        ("the order was shuffled", lambda d: d["streets"].reverse()),
        ("a corridor was inverted", lambda d: d["streets"][0].__setitem__("rule_px_y", [1096.4, 1064.5])),
        ("a centre left its crop", lambda d: d["streets"][1].__setitem__("centre_px_y", 9999.0)),
        ("the module drifted", lambda d: d["module"].__setitem__("corridor_ft_raw", 1.0)),
        ("the Kinzie cross-check moved", lambda d: d["cross_check"].__setitem__("gap_m", 0.0)),
        ("an adjudication lost its argument", lambda d: d["adjudications"][0].__setitem__("argument", "")),
    ):
        broken = copy.deepcopy(good)
        mutate(broken)
        OUT.write_text(json.dumps(broken, indent=2) + "\n")
        try:
            check()
        except SystemExit:
            fired += 1
            print(f"  fired: {label}")
        else:
            print(f"  DID NOT FIRE: {label}", file=sys.stderr)
    OUT.write_text(json.dumps(good, indent=2) + "\n")
    if fired != 8:
        raise SystemExit(f"only {fired} of 8 assertions fired")
    print("all 8 assertions fire")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--check-sheet", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.check:
        return check()
    if a.check_sheet:
        return check_sheet()
    if a.self_test:
        return self_test()
    doc = _wrap(read())
    if a.write:
        OUT.write_text(json.dumps(doc, indent=2) + "\n")
        print(f"wrote {OUT.relative_to(ROOT)}")
    else:
        print(json.dumps(doc, indent=2))


if __name__ == "__main__":
    main()
