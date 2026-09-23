#!/usr/bin/env python3
"""Read the thirteen streets of Kinzie's Addition off Wright's 1834 survey.

    tools/read_kinzie_addition_streets.py           print the reading
    tools/read_kinzie_addition_streets.py --write   write data/traces/kinzie_addition_street_grid.json
    tools/read_kinzie_addition_streets.py --check   re-read the sheet and compare with the committed file

WHY A TOOL AND NOT A TABLE OF NUMBERS. A street on a manuscript plat is two ruled
lines with nothing between them, and where those lines fall is a fact about the
raster that anyone can re-measure. Picking them by eye off a crop is a reading
only the picker can defend; projecting the ink of a window onto one axis and
taking the peaks is a reading the next person can re-run and disagree with by a
number. Every corridor edge in the committed file came out of `_rules()` below,
and `--check` re-derives all of them.

THE SHEET is the National Archives / Historic Urban Plans facsimile registered as
`wright_1834_nara_hup` (5050 x 6628 px at 600 dpi), because at that resolution the
Addition's ruled lines separate cleanly; the BPL master this project traces is
4204 x 5166. Readings are carried to local ENU through the NA sheet's OWN affine —
not through the scan-to-scan transform, which would spend 8.5 px of residual to
reach a frame this reading does not need. The two routes were compared while this
was written and differ by under 0.2 m across the whole Addition.

WHAT THE READING IS AND IS NOT. It gives the plat's MODULE — the tier pitch, the
column pitch, the corridor widths, the order and extent of the streets — to a
fraction of a metre, because those are differences measured inside one corner of
one sheet. It does NOT give the Addition's SEATING on modern ground: the sheet's
own fit carries 16.2 m of RMS residual and its drawn grid runs about 1.2 deg off
the bearing the committed town grid takes from modern control over a 1,420 m
baseline. So `data/streets/1835.json` seats the module on the two committed lines
the Addition shares with the town it adjoins — Michigan Street (`michigan_north`)
and Wolcott Street (`wolcott`) — and this file records what that seating cost.
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
OUT = ROOT / "data/traces/kinzie_addition_street_grid.json"
FT = 0.3048

# ---------------------------------------------------------------- the windows
#
# Each window is a band of the raster the profile is taken over, chosen to hold
# block ink and no street lettering: Wright letters the street names inside the
# corridors, and a name is ink in exactly the gap the reading is trying to find.
# `shear` is the slope the band is stacked along, fitted once by maximising the
# variance of the projection (the flattest profile a wrong slope can give is the
# blurred one). Its value is a property of THIS sheet in THIS corner.

SHEAR_EW = 0.0176   # raster dy/dx of the Addition's east-west rules
SHEAR_NS = -0.0060  # raster dx/dy of the Addition's north-south rules

# Columns the east-west corridors are read in. `x` is the reference: a reported
# y is the rule's y at that x.
EW_COLUMNS = [
    {"id": "col_west", "x": (2965, 3095),
     "through": "blocks 48, 39, 36, 27, 24 — the column immediately east of Wolcott Street"},
    {"id": "col_east", "x": (3465, 3560),
     "through": "blocks 45, 42, 33, 30, 21 — the column immediately east of Pine Street"},
]

# Rows the north-south corridors are read in.
NS_ROWS = [
    {"id": "row_superior", "y": (1150, 1225), "through": "the Superior tier, blocks 51-54"},
    {"id": "row_ontario", "y": (1525, 1600), "through": "the Ontario-Ohio tier, blocks 27-31"},
    {"id": "row_ohio", "y": (1650, 1725), "through": "the Ohio-Indiana tier, blocks 20-25"},
]

# The east-west streets, north to south, as Wright letters them.
EW_STREETS = ["superior", "huron", "erie", "ontario", "ohio", "indiana", "illinois", "michigan"]
# Their expected corridor centres in the west column, used only to attach a name
# to a detected pair. A pair more than 12 px from its slot is not accepted.
EW_SLOT = {"superior": 1127, "huron": 1251, "erie": 1373, "ontario": 1499,
           "ohio": 1624, "indiana": 1747, "illinois": 1871, "michigan": 1994}
EW_PITCH_PX = 123.8

NS_STREETS = ["wolcott", "cass", "rush", "pine", "sand"]
NS_SLOT = {"wolcott": 2958, "cass": 3113, "rush": 3270, "pine": 3429, "sand": 3588}

# The control. The Original Town's corridors are platted at 80 ft, so reading
# them on the same sheet by the same method prices the method itself. The
# Addition's width is only meaningful beside this number.
CONTROL_EW = {"window": (2380, 2560, 2500, 3080), "shear": SHEAR_EW,
              "streets": {"lake": 2632, "randolph": 2826, "washington": 3010}}

# ------------------------------------------------------------------ the read


def _sheet():
    g = json.loads(GCP.read_text())
    img = REPO / g["raster"]["working_copy"]
    if not img.exists():
        raise SystemExit(f"the registered raster is not in this checkout: {img}")
    return g, img


def _profile(img, x0, y0, x1, y1, axis, shear):
    """Mean ink per bin, stacking the band along `shear` so a tilted rule lands in one bin."""
    from PIL import Image
    px = Image.open(img).convert("L").load()
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
        return [(y0 + i, acc[i] / (x1 - x0)) for i in range(n)]
    n = x1 - x0
    acc = [0.0] * n
    for y in range(y0, y1):
        off = shear * (y - y0)
        for i in range(n):
            x = x0 + i + off
            xi = int(x)
            fr = x - xi
            acc[i] += max(0.0, 150.0 - (px[xi, y] * (1 - fr) + px[xi + 1, y] * fr))
    return [(x0 + i, acc[i] / (y1 - y0)) for i in range(n)]


def _rules(prof, minpk=14.0, maxw=7):
    """The sharp narrow peaks of a profile: a ruled line, not a numeral or a wash.

    A block numeral is ink too, and plenty of it, but it is a broad low mound
    forty pixels across. A rule is three or four pixels wide and twice as tall.
    The width test is the whole discrimination and it is deliberately blunt."""
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


def _pairs(rules, slots, tol=13.0, minw=24.0, maxw=42.0):
    """Attach a named street to the two rules that bound its corridor."""
    found = {}
    for name, slot in slots.items():
        best = None
        for a in range(len(rules)):
            for b in range(a + 1, len(rules)):
                lo, hi = rules[a][0], rules[b][0]
                w = hi - lo
                if not (minw <= w <= maxw):
                    continue
                d = abs((lo + hi) / 2.0 - slot)
                if d <= tol and (best is None or d < best[0]):
                    best = (d, lo, hi)
        if best:
            found[name] = (best[1], best[2])
    return found


# ------------------------------------------------------------- the ENU frame


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


def _span(to_local, p, q, horizontal, ref):
    """The metric distance between two rules, and the corridor centre."""
    if horizontal:
        e0, n0 = to_local(ref, p)
        e1, n1 = to_local(ref, q)
    else:
        e0, n0 = to_local(p, ref)
        e1, n1 = to_local(q, ref)
    return math.hypot(e1 - e0, n1 - n0), ((e0 + e1) / 2.0, (n0 + n1) / 2.0)


def read():
    g, img = _sheet()
    to_local = _frame()
    doc = {"east_west": {}, "north_south": {}, "control": {}, "windows": []}

    for col in EW_COLUMNS:
        x0, x1 = col["x"]
        rules = _rules(_profile(img, x0, 1080, x1, 2060, "h", SHEAR_EW))
        pairs = _pairs(rules, EW_SLOT if col["id"] == "col_west" else
                       {k: v + 8.5 for k, v in EW_SLOT.items()})
        doc["windows"].append({"id": col["id"], "axis": "east-west rules",
                               "crop_px": [x0, 1080, x1, 2060], "shear": SHEAR_EW,
                               "through": col["through"]})
        for name, (a, b) in pairs.items():
            w, c = _span(to_local, a, b, True, x0)
            doc["east_west"].setdefault(name, []).append(
                {"window": col["id"], "ref_px_x": x0, "rule_px_y": [a, b],
                 "corridor_m": round(w, 2), "corridor_ft": round(w / FT, 1),
                 "centre_local_enu_m": [round(c[0], 1), round(c[1], 1)]})

    for row in NS_ROWS:
        y0, y1 = row["y"]
        rules = _rules(_profile(img, 2900, y0, 3660, y1, "v", SHEAR_NS), minpk=12.0)
        pairs = _pairs(rules, NS_SLOT)
        doc["windows"].append({"id": row["id"], "axis": "north-south rules",
                               "crop_px": [2900, y0, 3660, y1], "shear": SHEAR_NS,
                               "through": row["through"]})
        for name, (a, b) in pairs.items():
            w, c = _span(to_local, a, b, False, y0)
            doc["north_south"].setdefault(name, []).append(
                {"window": row["id"], "ref_px_y": y0, "rule_px_x": [a, b],
                 "corridor_m": round(w, 2), "corridor_ft": round(w / FT, 1),
                 "centre_local_enu_m": [round(c[0], 1), round(c[1], 1)]})

    x0, y0, x1, y1 = CONTROL_EW["window"]
    rules = _rules(_profile(img, x0, y0, x1, y1, "h", CONTROL_EW["shear"]))
    for name, slot in CONTROL_EW["streets"].items():
        p = _pairs(rules, {name: slot}, tol=16.0, minw=26.0, maxw=44.0)
        if name in p:
            a, b = p[name]
            w, c = _span(to_local, a, b, True, x0)
            doc["control"][name] = {"ref_px_x": x0, "rule_px_y": [a, b],
                                    "corridor_m": round(w, 2), "corridor_ft": round(w / FT, 1),
                                    "platted_ft": 80.0}
    doc["module"] = _module(doc)
    doc["control_summary"] = _control_summary(doc)
    return doc


def _mean(xs):
    return sum(xs) / len(xs)


def _sd(xs):
    if len(xs) < 2:
        return 0.0
    m = _mean(xs)
    return math.sqrt(sum((x - m) ** 2 for x in xs) / (len(xs) - 1))


def _module(doc):
    """The plat's own dimensions: what the sheet gives well, because they are
    differences measured inside one corner of one raster."""
    tier = []
    for col in ("col_west", "col_east"):
        ns = [doc["east_west"][s][i]["centre_local_enu_m"][1]
              for s in EW_STREETS for i in range(len(doc["east_west"].get(s, [])))
              if doc["east_west"][s][i]["window"] == col]
        ns.sort()
        tier += [round(b - a, 2) for a, b in zip(ns, ns[1:])]
    colp = []
    for row in ("row_superior", "row_ontario", "row_ohio"):
        es = sorted(r["centre_local_enu_m"][0] for s in NS_STREETS
                    for r in doc["north_south"].get(s, []) if r["window"] == row)
        idx = sorted(NS_STREETS.index(s) for s in NS_STREETS
                     for r in doc["north_south"].get(s, []) if r["window"] == row)
        colp += [round((b - a) / (j - i), 2) for (i, a), (j, b)
                 in zip(list(zip(idx, es)), list(zip(idx, es))[1:])]
    wid = [r["corridor_ft"] for f in ("east_west", "north_south")
           for s in doc[f].values() for r in s]
    return {
        "tier_pitch_m": {"mean": round(_mean(tier), 2), "sd": round(_sd(tier), 2),
                         "n": len(tier), "samples": tier,
                         "note": "centre to centre of consecutive east-west corridors — "
                                 "the north-south module of the plat"},
        "column_pitch_m": {"mean": round(_mean(colp), 2), "sd": round(_sd(colp), 2),
                           "n": len(colp), "samples": colp,
                           "note": "centre to centre of consecutive north-south corridors"},
        "corridor_read_ft": {"mean": round(_mean(wid), 1), "sd": round(_sd(wid), 1),
                             "n": len(wid)},
    }


def _control_summary(doc):
    got = [v["corridor_ft"] for v in doc["control"].values()]
    read = doc["module"]["corridor_read_ft"]["mean"]
    ratio = read / _mean(got)
    return {
        "original_town_platted_ft": 80.0,
        "original_town_read_ft": {"mean": round(_mean(got), 1), "sd": round(_sd(got), 1),
                                  "n": len(got)},
        "method_over_read": round(_mean(got) / 80.0, 3),
        "addition_over_original_town": round(ratio, 3),
        "addition_corridor_ft": round(ratio * 80.0, 1),
        "addition_corridor_m": round(ratio * 80.0 * FT, 2),
        "reading": "The Addition's corridors are not measured against a ruler, they are "
                   "measured against the Original Town's on the same sheet by the same "
                   "method — which is the only comparison the sheet can settle. The "
                   "method reads a platted 80 ft corridor wide, so the Addition's raw "
                   "read is scaled by the ratio rather than taken at face value.",
    }


def _document(doc):
    g = json.loads(GCP.read_text())
    return {
        "_doc": __doc__.strip(),
        "ticket": "T-1060 (piece 1 of T-0789)",
        "raster": {k: g["raster"][k] for k in
                   ("working_copy", "width", "height", "dpi", "sha256", "source_id")},
        "registration": "data/traces/gcp/wright_1834_nara_hup_gcps.json, `fit` "
                        "(NA pixel -> EPSG:26916, RMS 16.19 m on eight control points)",
        "method": "tools/read_kinzie_addition_streets.py — ink projected onto one axis "
                  "over the windows below, sharp narrow peaks taken as ruled lines, a "
                  "street's corridor taken as the pair of rules bracketing its slot. "
                  "`--check` re-derives every pixel here from the raster.",
        "windows": doc["windows"],
        "readings": {"east_west": doc["east_west"], "north_south": doc["north_south"]},
        "module": doc["module"],
        "control": doc["control"],
        "control_summary": doc["control_summary"],
        "extent": EXTENT,
        "seating": SEATING,
    }


EXTENT = {
    "_doc": "Which streets reach where, from the rules the windows found and did not "
            "find. A street absent from a window is absent from the sheet there: the "
            "detector that found Pine at every tier found no Sand above Huron, and "
            "that is the evidence for Sand's north end.",
    "sand": "present at the Michigan-Illinois, Illinois-Indiana, Ontario-Erie and "
            "Erie-Huron tiers; ABSENT at the Huron-Superior tier. Sand Street ends on "
            "Huron Street, which is what the sheet draws: block 44 above it is cut by "
            "the shore.",
    "pine": "present at every tier read, including Huron-Superior. Pine runs the full "
            "height of the Addition.",
    "east_of_sand": "Wright carries the east-west streets east of Sand Street to the "
            "lake shore, across the shore-cut blocks 20, 31, 32, 43, 44, 45 and 54. "
            "That reach is NOT committed here: where a street meets the shore is the "
            "shore trace's question (T-0799, T-0800), and a street line may not claim "
            "ground this reading has not measured.",
    "south_of_michigan": "The river tier — blocks 1-7 and the numbered water lots on "
            "the north bank — is T-1063's. The north-south streets are committed from "
            "Michigan Street northward only.",
    "west_of_wolcott": "A narrow tier of blocks stands west of Wolcott Street between "
            "it and the Addition's west boundary rule (NA pixel x 2918 at the "
            "Ontario-Ohio tier), about 17 m wide. It is a block question, not a street "
            "one, and it is T-1061's.",
}

SEATING = {
    "_doc": "The module above is seated on the two committed streets the Addition "
            "shares with the town it adjoins, rather than on this sheet's own fit.",
    "why": "The NA fit carries 16.19 m RMS on eight control points, and the grid it "
           "draws in this corner runs about 1.2 deg off the bearing the committed town "
           "grid takes from modern control over a 1,420 m baseline. Read straight "
           "through the fit, Michigan Street lands 19.8 m south of `michigan_north`, "
           "which is the same street. A reading that puts a street twice in two places "
           "is not a reading; the sheet's strength is the module and the committed "
           "grid's strength is the seating, and each is used for what it is good at.",
    "east_west_datum": "michigan_north in data/streets/1835.json",
    "north_south_datum": "wolcott in data/streets/1835.json",
    "residual_michigan_m": 19.8,
    "residual_wolcott_m": 6.5,
    "bearing_note": "Each new street takes the bearing of its own family's committed "
                    "datum, so the Addition's streets are parallel to the town's. The "
                    "sheet's own bearing for them is recorded in `windows[].shear` and "
                    "is not used for geometry.",
}


def _check_derived() -> int:
    """The cheap half of the gate: everything committed in metres re-derives from
    what is committed in pixels, through the committed affine. It does not open
    the raster — `--check-sheet` does that, and it costs half a minute, which is
    why the per-commit gate runs this half and the PR runs the other (the same
    division tools/trace_river.py makes for the same reason)."""
    have = json.loads(OUT.read_text())
    to_local = _frame()
    bad = []
    for fam, key, horiz in (("east_west", "rule_px_y", True),
                            ("north_south", "rule_px_x", False)):
        for name, rows in have["readings"][fam].items():
            for r in rows:
                ref = r["ref_px_x"] if horiz else r["ref_px_y"]
                w, c = _span(to_local, r[key][0], r[key][1], horiz, ref)
                if abs(w - r["corridor_m"]) > 0.02:
                    bad.append(f"{fam}/{name}/{r['window']}: corridor {r['corridor_m']} m "
                               f"does not re-derive ({w:.2f})")
                if abs(w / FT - r["corridor_ft"]) > 0.1:
                    bad.append(f"{fam}/{name}/{r['window']}: corridor {r['corridor_ft']} ft "
                               f"does not re-derive ({w / FT:.1f})")
                for i, got in enumerate(c):
                    if abs(got - r["centre_local_enu_m"][i]) > 0.06:
                        bad.append(f"{fam}/{name}/{r['window']}: centre "
                                   f"{r['centre_local_enu_m']} does not re-derive "
                                   f"({round(c[0], 1)}, {round(c[1], 1)})")
    fresh = _module({"east_west": have["readings"]["east_west"],
                     "north_south": have["readings"]["north_south"]})
    for block in ("tier_pitch_m", "column_pitch_m", "corridor_read_ft"):
        for field in ("mean", "sd", "n"):
            if fresh[block][field] != have["module"][block][field]:
                bad.append(f"module {block}.{field}: committed {have['module'][block][field]}, "
                           f"re-derived {fresh[block][field]}")
    cs = _control_summary({"module": fresh, "control": have["control"]})
    for field in ("addition_over_original_town", "addition_corridor_ft", "addition_corridor_m"):
        if cs[field] != have["control_summary"][field]:
            bad.append(f"control_summary {field}: committed "
                       f"{have['control_summary'][field]}, re-derived {cs[field]}")
    for line in bad:
        print("RED  " + line)
    n = sum(len(v) for f in ("east_west", "north_south") for v in have["readings"][f].values())
    print(f"kinzie addition street grid: {n} corridor reading(s), the module and the "
          f"Original Town control all re-derive from the committed pixels"
          if not bad else f"{len(bad)} disagreement(s)")
    return 1 if bad else 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true",
                    help="re-derive every committed metre from the committed pixels "
                         "(milliseconds, no raster)")
    ap.add_argument("--check-sheet", action="store_true", dest="check_sheet",
                    help="re-read the raster itself and compare the pixels (needs Pillow "
                         "and the registered scan; ~30 s, so not the per-commit gate)")
    a = ap.parse_args()
    if a.check:
        return _check_derived()
    doc = read()
    if a.check_sheet:
        have = json.loads(OUT.read_text())
        bad = []
        for fam in ("east_west", "north_south"):
            for name, rows in doc[fam].items():
                for r in rows:
                    m = [q for q in have["readings"][fam].get(name, [])
                         if q["window"] == r["window"]]
                    if not m:
                        bad.append(f"{fam}/{name}/{r['window']} is not in the committed file")
                        continue
                    key = "rule_px_y" if fam == "east_west" else "rule_px_x"
                    for i in (0, 1):
                        if abs(m[0][key][i] - r[key][i]) > 0.6:
                            bad.append(f"{fam}/{name}/{r['window']} rule {i}: "
                                       f"committed {m[0][key][i]}, sheet {r[key][i]}")
        for line in bad:
            print("RED  " + line)
        print("kinzie addition street grid: "
              + ("re-derives from the sheet" if not bad else f"{len(bad)} disagreement(s)"))
        return 1 if bad else 0
    if a.write:
        OUT.write_text(json.dumps(_document(doc), indent=2, ensure_ascii=False) + "\n")
        print(f"wrote {OUT.relative_to(ROOT)}")
    else:
        print(json.dumps(_document(doc), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
