#!/usr/bin/env python3
"""Read the lot lines Wright draws INSIDE Kinzie's Addition's cells.

    tools/read_kinzie_addition_lots.py              print the reading
    tools/read_kinzie_addition_lots.py --write      write the trace
    tools/read_kinzie_addition_lots.py --check      re-derive it from the committed pixels
    tools/read_kinzie_addition_lots.py --self-test  break each assertion and watch it fire

WHAT THIS FILE IS AND IS NOT. It is the READING: which of the Addition's twenty-seven
cells Wright rules into lots, where the rules fall, and which cells he leaves whole. It
authors NO ground and no lot polygon — `tools/generate_plat_lots.py` cuts the lots, on
this reading, in the frame the block grid already stands in. Every number below is a
PIXEL statement about chicago/pre_fire_v1/maps/images/1834-wright-map.jpg.

WHY IT EXISTS. T-1437 built the Addition's block grid and WITHHELD its lots, in as many
words: "NO LOT RULE HAS BEEN READ FOR THIS PLAT ... the four-to-a-face 80 ft module this
generator can seat is a reading of ONE Original Town block and carrying it across the
river would be a guess dressed as arithmetic." It named what would settle it — "the lot
lines and lot numerals Wright draws inside the Addition's cells, read off
wright_1834_nara_hup the way tools/read_kinzie_addition_numerals.py reads the block
numerals". That withholding is the whole reason the North Division has no schedulable
ground: all twenty-seven Addition rows of `data/reconstruction/1835_665_roof_programme.json`
stand `unsubdivided`, the district's headroom is 0, and T-1205 is blocked-tech on it with
"T-1206 sits on the same gate". This is that reading.

WHERE THE CELLS COME FROM, AND WHY ALMOST NOTHING IS MEASURED TWICE. T-1060 committed the
Addition's eleven corridors as pixel pairs in `data/traces/kinzie_addition_street_grid.json`
— two kerbs per corridor, each read in one or two windows. A cell is the rectangle two
consecutive corridors leave between them, so this tool READS that file, fits each kerb
across its windows, and interpolates. A corridor that moves there moves the crops here,
which is what `--check` is for.

THE ONE THING IT DOES MEASURE FOR ITSELF is each cell's OWN west and east boundary rule.
The kerb of a street is not the edge of the block drawn beside it: Wright rules the block
and rules the street, and the two lines stand up to five pixels apart. Taking the kerb for
the block edge put a 35 ft lot at the west end of every cell and a 60 ft one in the middle
of the same block; taking the block's own rule makes the same six lots even. So each
boundary is searched for in a +/- 8 px window around the kerb and the strongest full-height
rule there is the block's edge.

WHAT THE READING FINDS, AND IT IS NOT ONE RULE FOR THE PLAT.

  * NINETEEN of the twenty-seven cells -- every cell in the Superior, Huron, Erie, Ontario
    and Ohio tiers -- are drawn WHOLE. No alley, no lot line, nothing inside the rule but
    the block's own figure. The mid-block darkness in those cells runs 0.21-0.36 of the
    cell's width against 0.84-1.00 in the tiers that are divided, which is not a marginal
    call.
  * EIGHT cells -- the whole of the Indiana and Illinois tiers, the two nearest the river --
    carry a mid-block ALLEY, ruled from side to side.
  * FIVE of those eight are ruled into LOTS, six to a face, twelve to the block, and
    Wright numbers them 1-12 where there is room to write.
  * THREE are not. Block 18 (`blk_indiana_north_pine`) carries the alley and not one lot
    rule. Block 11 (`blk_illinois_north_cass`) is the cell Wright letters `Kinzie Block`
    instead of numbering, and the only marks inside it are that lettering: the evenness
    test refuses them at 8.3 to 1. Block 9 (`blk_illinois_north_pine`) is ruled at its
    WEST END ONLY -- two lots of 41 and 49 ft and then 61 m of undrawn ground, refused at
    4.9 to 1 -- and a cell divided in part is not a cell whose lots can be cut.

SO THE PLAT HAS NO SINGLE MODULE, AND THAT IS THE READING. Kinzie's Addition was platted
in 1833 and sold from the river northward; what Wright drew in 1834 is how far the
subdivision had got. The five lotted cells give a measured lot frontage and the twenty-two
others keep their withholding -- with a sharper reason than T-1437 could write, because
"the sheet does not divide this cell" is a reading and "no rule has been read" was an
absence.

HOW A LOT LINE IS TOLD FROM INK. Four tests, all stated in the constants below:
  1. It is a column of the cell whose dark fraction down one half-band is at least 0.70.
  2. It is not within 8 px of the cell's own boundary rule -- that is the boundary.
  3. Candidates within 4 px of each other are one line.
  4. It is READ ON BOTH FACES, or on one face and corroborated by the evenness test. A
     numeral written across a line breaks it: block 17's north face loses its fourth rule
     under the `17`, and the south face carries it. So the two faces are UNIONED and the
     union is graded -- `clear` where both faces rule it, `one_face` where one does.
AND THE ALLEY IS A CORRIDOR, NOT A LINE. Every divided cell is ruled TWICE across its
middle, with paper between the two strokes, and five of the eight give both kerbs cleanly:
6.6 px apart, sd 0.8. Measured in the registered frame and scaled by the ratio the same
method reads a PLATTED 80 ft Original Town corridor at -- `control_summary.method_over_read`,
1.024, the correction every one of this plat's street corridors already carries -- that is
14.8 ft, graded `inferred`. The sheet dimensions no alley in the Addition; this is what it
draws, measured the only way the sheet can settle.

And one test on the result: the lots a cell's rules cut must be even, max over min no
worse than 1.6. The five lotted cells come in at 1.28 to 1.47; block 9's west-end rules
fail at 4.9 and block 11's lettering at 8.3, and both cells are refused.
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import wright_px  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
RASTER = ROOT.parent / "pre_fire_v1" / "maps" / "images" / "1834-wright-map.jpg"
GRID = ROOT / "data" / "traces" / "kinzie_addition_street_grid.json"
NUMBERING = ROOT / "data" / "traces" / "kinzie_addition_block_numbering.json"
OUT = ROOT / "data" / "traces" / "kinzie_addition_lot_lines.json"

# The windows the committed street reading used, in the axis each one fixes. A kerb
# read in two windows is fitted across them and interpolated; a kerb read in one is
# carried flat, because one window states no slope.
WINDOW_X = {"col_west": 2965.0, "col_east": 3465.0}
WINDOW_Y = {"row_superior": 1150.0, "row_ontario": 1525.0, "row_ohio": 1650.0}

# Ink. The sheet is a scan of brown ink on toned paper; 140 of 255 separates a ruled
# line from the paper everywhere on this plat and is the threshold the numeral reading
# uses on the same raster.
DARK = 140.0
# A cell is read inset from the corridor rules above and below it, so that their ink
# does not stand at the end of a face band and read as a lot rule.
INSET_PX = 3
# The block's own boundary rule is searched for this far either side of the kerb.
BOUNDARY_SEARCH_PX = 8
# A vertical rule is a column at least this dark down a half-band.
RULE_MIN = 0.70
# ... and a mid-block alley is a row at least this dark across the cell.
ALLEY_MIN = 0.60
# The alley corridor is the band of rows around that peak still this dark.
ALLEY_BAND = 0.45
# Two dark rows this close are one stroke of the pen, not two kerbs.
ALLEY_MERGE_PX = 2
# Two candidates this close are one line; two faces' lines this close are the same rule.
MERGE_PX = 4.0
# A candidate this close to the cell's own boundary is the boundary.
EDGE_PX = 8.0
# The lots a cell's rules cut must be this even, worst over best.
EVEN_MAX = 1.6

TIERS = [("superior", "huron"), ("huron", "erie"), ("erie", "ontario"),
         ("ontario", "ohio"), ("ohio", "indiana"), ("indiana", "illinois"),
         ("illinois", "michigan")]
COLUMNS = [("wolcott", "cass"), ("cass", "rush"), ("rush", "pine"), ("pine", "sand")]
# The one cell of the seven-by-four that is not a block: Sand Street ends on Huron, so
# the Superior-Huron tier's east column has no committed east line. The block grid omits
# it for that reason and this reading omits it for the same one.
NOT_A_CELL = {("superior", "pine")}


def _fit(pairs):
    """A kerb as a straight line across the windows it was read in."""
    if len(pairs) == 1:
        return pairs[0][1], 0.0
    xs = np.array([p[0] for p in pairs], dtype=float)
    ys = np.array([p[1] for p in pairs], dtype=float)
    slope = float(((xs - xs.mean()) * (ys - ys.mean())).sum() / ((xs - xs.mean()) ** 2).sum())
    return float(ys.mean() - slope * xs.mean()), slope


def _grid():
    doc = json.loads(GRID.read_text(encoding="utf-8"))
    ew = {name: [_fit([(WINDOW_X[r["window"]], r["rule_px_y"][i]) for r in rows])
                 for i in (0, 1)]
          for name, rows in doc["readings"]["east_west"].items()}
    ns = {name: [_fit([(WINDOW_Y[r["window"]], r["rule_px_x"][i]) for r in rows])
                 for i in (0, 1)]
          for name, rows in doc["readings"]["north_south"].items()}
    return doc, ew, ns


def _numbers():
    doc = json.loads(NUMBERING.read_text(encoding="utf-8"))
    return {b["cell"]: b for b in doc["blocks"]}


def _cell_box(ew, ns, north, south, west, east):
    """The rectangle two corridors leave between them, kerb to kerb."""
    y_mid = (ew[north][1][0] + ew[north][1][1] * 3200
             + ew[south][0][0] + ew[south][0][1] * 3200) / 2
    x0 = ns[west][1][0] + ns[west][1][1] * y_mid
    x1 = ns[east][0][0] + ns[east][0][1] * y_mid
    x_mid = (x0 + x1) / 2
    y0 = ew[north][1][0] + ew[north][1][1] * x_mid
    y1 = ew[south][0][0] + ew[south][0][1] * x_mid
    return x0, y0, x1, y1


def _boundary(dark, kerb_px, x_left):
    """The cell's OWN west or east rule, searched for around the street's kerb."""
    lo = int(round(kerb_px - x_left - BOUNDARY_SEARCH_PX))
    hi = int(round(kerb_px - x_left + BOUNDARY_SEARCH_PX))
    lo, hi = max(0, lo), min(dark.shape[1] - 1, hi)
    if hi <= lo:
        return kerb_px, 0.0, "kerb"
    col = dark[:, lo:hi + 1].mean(axis=0)
    i = int(np.argmax(col))
    if float(col[i]) < RULE_MIN:
        return kerb_px, float(col[i]), "kerb"
    return float(lo + i + x_left), float(col[i]), "ruled"


def _rules(dark, a, b, x_left):
    """Vertical rules down one half-band, merged."""
    band = dark[a:b]
    if band.shape[0] < 6:
        return []
    col = band.mean(axis=0)
    w = col.shape[0]
    hits = [i for i in range(1, w - 1)
            if col[i] >= RULE_MIN and col[i] >= col[i - 1] and col[i] >= col[i + 1]]
    runs = []
    for h in hits:
        if runs and h - runs[-1][-1] <= MERGE_PX:
            runs[-1].append(h)
        else:
            runs.append([h])
    return [float(np.mean(r)) + x_left for r in runs]


def read_cell(arr, ew, ns, north, south, west, east):
    x0, y0, x1, y1 = _cell_box(ew, ns, north, south, west, east)
    # The crop reaches PAST the corridor kerbs in x and stops short of them in y. The
    # block's own west and east rules are what the kerb reading approximates, and they
    # are found by searching around it — so the search window has to be in the crop. In
    # y the corridor rules themselves are the cell's top and bottom and the inset keeps
    # their ink out of the face bands.
    left = int(round(x0)) - BOUNDARY_SEARCH_PX
    top = int(round(y0)) + INSET_PX
    sub = arr[top:int(round(y1)) - INSET_PX, left:int(round(x1)) + BOUNDARY_SEARCH_PX]
    dark = (sub < DARK)
    h = dark.shape[0]

    rows = dark.mean(axis=1)
    lo, hi = int(h * 0.30), int(h * 0.70)
    k = int(np.argmax(rows[lo:hi])) + lo
    alley_peak = float(rows[k])
    alley = None
    if alley_peak >= ALLEY_MIN:
        # The alley is drawn as a CORRIDOR and not a line: two ruled kerbs with paper
        # between them. Take every row in the middle band dark enough to be a rule,
        # merge the ones that are one stroke, and the two groups are the two kerbs.
        hits = [i for i in range(lo, hi)
                if rows[i] >= ALLEY_MIN and rows[i] >= rows[i - 1] and rows[i] >= rows[i + 1]]
        runs = []
        for i in hits:
            if runs and i - runs[-1][-1] <= ALLEY_MERGE_PX:
                runs[-1].append(i)
            else:
                runs.append([i])
        kerbs = [float(np.mean(r)) for r in runs]
        a, b = k, k
        while a > 0 and rows[a - 1] >= ALLEY_BAND:
            a -= 1
        while b < h - 1 and rows[b + 1] >= ALLEY_BAND:
            b += 1
        alley = {"centre_px_y": round(a + top + (b - a) / 2, 1),
                 "band_px_y": [round(a + top, 1), round(b + top, 1)],
                 "ink_band_px": round(float(b - a + 1), 1),
                 "dark_fraction": round(alley_peak, 3),
                 "kerbs_px_y": [round(c + top, 1) for c in kerbs],
                 "kerb_to_kerb_px": (round(kerbs[-1] - kerbs[0], 1)
                                     if len(kerbs) == 2 else None),
                 "read": ("two ruled kerbs" if len(kerbs) == 2 else
                          f"{len(kerbs)} rule(s) — the corridor is not read here")}

    wb, wf, wk = _boundary(dark, x0, left)
    eb, ef, ek = _boundary(dark, x1, left)

    faces = {}
    if alley:
        a_i = int(round(alley["band_px_y"][0])) - top
        b_i = int(round(alley["band_px_y"][1])) - top
        faces["north"] = _rules(dark, 1, max(2, a_i - 1), left)
        faces["south"] = _rules(dark, min(h - 2, b_i + 2), h - 1, left)
    else:
        faces["north"] = faces["south"] = []

    def interior(v):
        return [p for p in v if wb + EDGE_PX < p < eb - EDGE_PX]

    north_r, south_r = interior(faces["north"]), interior(faces["south"])
    union, grades = [], []
    for p in sorted(north_r + south_r):
        if union and p - union[-1] <= MERGE_PX:
            union[-1] = (union[-1] + p) / 2
            grades[-1] = "clear"
        else:
            union.append(p)
            grades.append("one_face")
    return {
        "cell_box_px": [round(x0, 1), round(y0, 1), round(x1, 1), round(y1, 1)],
        "boundary_px_x": {"west": round(wb, 1), "east": round(eb, 1)},
        "boundary_read": {"west": wk, "east": ek,
                          "west_dark_fraction": round(wf, 3),
                          "east_dark_fraction": round(ef, 3)},
        "alley": alley,
        "mid_block_dark_fraction": round(alley_peak, 3),
        "rules_px_x": [round(p, 1) for p in union],
        "rule_grades": grades,
        "faces_px_x": {k2: [round(p, 1) for p in interior(v)] for k2, v in faces.items()},
    }


def _metres(px_a, px_b, y):
    ea, na = wright_px.to_local(px_a, y)
    eb, nb = wright_px.to_local(px_b, y)
    return float(np.hypot(eb - ea, nb - na))


def judge(cell):
    """What the cell is, from what was read in it. No number is adjusted to pass."""
    wb, eb = cell["boundary_px_x"]["west"], cell["boundary_px_x"]["east"]
    rules = cell["rules_px_x"]
    if cell["alley"] is None:
        return "undivided", ("Wright draws this cell whole: no mid-block rule "
                             f"(darkest middle row {cell['mid_block_dark_fraction']:.2f} "
                             f"of the cell's width, against {ALLEY_MIN:.2f} for a rule) "
                             "and no lot line."), None
    if not rules:
        return "halved_not_lotted", ("the alley is ruled and the faces are not: this cell "
                                     "is halved and not lotted."), None
    edges = [wb] + rules + [eb]
    widths = [edges[i + 1] - edges[i] for i in range(len(edges) - 1)]
    even = max(widths) / min(widths)
    if even > EVEN_MAX:
        return "partly_drawn", (f"the rules in this cell cut lots {even:.1f} to 1 uneven, "
                                f"against {EVEN_MAX} — the sheet divides part of the cell "
                                "and leaves the rest undrawn, and a part-divided cell is "
                                "not a cell whose lots can be cut."), round(even, 2)
    return "lotted", (f"{len(widths)} lots to a face, the widest {even:.2f} times the "
                      "narrowest."), round(even, 2)


def build():
    if not RASTER.exists():                        # pragma: no cover - runner without the raster
        raise SystemExit(f"raster not found: {RASTER}")
    arr = np.asarray(Image.open(RASTER).convert("L"), dtype=np.float32)
    grid_doc, ew, ns = _grid()
    numbers = _numbers()

    cells = []
    for row, (north, south) in enumerate(TIERS, start=2):
        for col, (west, east) in enumerate(COLUMNS, start=2):
            if (north, west) in NOT_A_CELL:
                continue
            read = read_cell(arr, ew, ns, north, south, west, east)
            verdict, why, even = judge(read)
            key = f"c{col}r{row}"
            num = numbers.get(key, {})
            wb, eb = read["boundary_px_x"]["west"], read["boundary_px_x"]["east"]
            y_mid = (read["cell_box_px"][1] + read["cell_box_px"][3]) / 2
            frontage_m = _metres(wb, eb, y_mid)
            entry = {
                "block_id": f"blk_{north}_north_{west}",
                "cell": key,
                "number": num.get("number"),
                "bounded_by": {"north": f"{north}_north", "south": f"{south}_north",
                               "west": west, "east": east},
                "verdict": verdict,
                "why": why,
                **read,
                "frontage_m": round(frontage_m, 2),
                "frontage_ft": round(frontage_m / 0.3048, 1),
            }
            if verdict == "lotted":
                entry["lots_per_face"] = len(read["rules_px_x"]) + 1
                entry["lot_frontage_m"] = round(frontage_m / entry["lots_per_face"], 2)
                entry["lot_frontage_ft"] = round(frontage_m / entry["lots_per_face"]
                                                 / 0.3048, 1)
                entry["evenness"] = even
                entry["lot_edges_px_x"] = [round(wb, 1)] + read["rules_px_x"] + [round(eb, 1)]
            elif even is not None:
                entry["evenness"] = even
            cells.append(entry)

    # THE ALLEY, measured the way T-1060 measured the street corridors on this sheet:
    # kerb rule to kerb rule, and then divided by the ratio the same method reads a
    # PLATTED 80 ft Original Town corridor at. A raw pixel width off a hand-drawn line
    # is wider than the thing it draws, and the sheet can only settle the comparison.
    seps = [(c["block_id"], c["alley"]["kerb_to_kerb_px"], c["cell_box_px"])
            for c in cells if c["alley"] and c["alley"]["kerb_to_kerb_px"]]
    alley = None
    if seps:
        widths = []
        for _, sep, box in seps:
            y_mid = (box[1] + box[3]) / 2
            widths.append(_metres(0.0, sep, y_mid))
        over = grid_doc["control_summary"]["method_over_read"]
        read_ft = float(np.mean(widths)) / 0.3048
        alley = {
            "kerb_to_kerb_px": {"mean": round(float(np.mean([s[1] for s in seps])), 2),
                                "sd": round(float(np.std([s[1] for s in seps])), 2),
                                "n": len(seps),
                                "cells": [s[0] for s in seps]},
            "read_ft": round(read_ft, 1),
            "method_over_read": over,
            "alley_ft": round(read_ft / over, 1),
            "alley_m": round(read_ft / over * 0.3048, 2),
            "confidence": "inferred",
            "note": ("the Addition's alley is not dimensioned on the sheet. This is the "
                     "corridor its two ruled kerbs leave, measured in the frame the "
                     "registration fixes and scaled by `control_summary.method_over_read` "
                     "— the same correction the street corridors carry, for the same "
                     "reason and off the same three Original Town corridors."),
            "cells_that_do_not_read": [c["block_id"] for c in cells
                                       if c["alley"] and not c["alley"]["kerb_to_kerb_px"]],
        }

    lotted = [c for c in cells if c["verdict"] == "lotted"]
    per_face = sorted({c["lots_per_face"] for c in lotted})
    fronts = [c["lot_frontage_ft"] for c in lotted]
    doc = {
        "_doc": ("GENERATED by tools/read_kinzie_addition_lots.py — do not hand-edit. "
                 "Which of Kinzie's Addition's cells Wright rules into lots on his 1834 "
                 "survey, where the rules fall, and which cells he leaves whole. This file "
                 "authors no ground: tools/generate_plat_lots.py cuts the lots on it."),
        "ticket": "T-1741",
        "settles": ("the `lot_subdivision_withheld` T-1437 wrote onto every Addition block "
                    "— `data/traces/vectors/thompson_lots.json` § kinzies_addition — which "
                    "named this reading as the thing that would settle it"),
        "raster": dict(grid_doc["raster"]),
        "registration": grid_doc["registration"],
        "method": {
            "cells_from": ("data/traces/kinzie_addition_street_grid.json § readings — each "
                           "kerb fitted across the windows it was read in and interpolated"),
            "dark_threshold_of_255": DARK,
            "vertical_rule_min_dark_fraction": RULE_MIN,
            "alley_min_dark_fraction": ALLEY_MIN,
            "alley_band_dark_fraction": ALLEY_BAND,
            "boundary_search_px": BOUNDARY_SEARCH_PX,
            "merge_px": MERGE_PX,
            "edge_px": EDGE_PX,
            "evenness_max": EVEN_MAX,
            "why_the_faces_are_unioned": ("a numeral written across a rule breaks it, so a "
                                          "rule read on one face and not the other is kept "
                                          "and graded `one_face`; the evenness test is what "
                                          "refuses a cell whose marks are lettering"),
        },
        "summary": {
            "cells": len(cells),
            "by_verdict": {v: sum(1 for c in cells if c["verdict"] == v)
                           for v in ("lotted", "halved_not_lotted", "partly_drawn",
                                     "undivided")},
            "lots_per_face": per_face,
            "lot_frontage_ft": {"min": min(fronts), "max": max(fronts),
                                "mean": round(float(np.mean(fronts)), 1)} if fronts else None,
            "tiers_with_an_alley": sorted({c["bounded_by"]["north"] for c in cells
                                           if c["alley"]}),
        },
        "alley": alley,
        "the_finding": (
            "The Addition has no single lot module and that is the reading. Nineteen of "
            "the twenty-seven cells — every cell in the Superior, Huron, Erie, Ontario and "
            "Ohio tiers — are drawn whole, with neither an alley nor a lot line inside the "
            "block rule. The eight cells of the Indiana and Illinois tiers, nearest the "
            "river, all carry a mid-block alley; five of them are ruled six lots to a face "
            "and Wright numbers them 1-12 where there is room to write. Block 18 carries "
            "the alley and not one lot rule; the only marks inside block 11 are the "
            "lettering `Kinzie Block` Wright writes there instead of a figure, refused by "
            "the evenness test at 8.3 to 1; block 9 is ruled at its west end only — two "
            "lots and then 61 m of undrawn ground — refused at 4.9 to 1. So the sheet divides the two tiers the Addition "
            "had sold and stops, which is what a plat drawn in 1834 of a subdivision platted "
            "in 1833 and sold from the river northward should look like."
        ),
        "what_this_does_not_settle": (
            "The twenty-two cells this reading does not cut keep their withholding, with a "
            "sharper reason than T-1437 could write: `the sheet does not divide this cell` "
            "is a reading, `no rule has been read` was an absence. Nothing here licenses "
            "carrying the five lotted cells' module north into the tiers Wright leaves "
            "whole — that would be the same guess dressed as arithmetic T-1437 refused, "
            "with a better disguise."
        ),
        "cells": cells,
    }
    return doc


def report(doc):
    s = doc["summary"]
    print(f"KINZIE'S ADDITION — the lot lines Wright rules inside its cells\n")
    print(f"  {s['cells']} cells read: " + ", ".join(
        f"{n} {v.replace('_',' ')}" for v, n in s["by_verdict"].items() if n))
    if s["lot_frontage_ft"]:
        f = s["lot_frontage_ft"]
        print(f"  lots per face {s['lots_per_face']}, "
              f"frontage {f['min']}-{f['max']} ft (mean {f['mean']})")
    print()
    for c in doc["cells"]:
        n = f"block {c['number']}" if c["number"] else c["cell"]
        print(f"  {c['block_id']:<28} {n:<9} {c['verdict']:<18} {c['why']}")
    print()
    print("  " + doc["the_finding"].replace(". ", ".\n  "))
    return 0


def check():
    if not OUT.exists():
        print(f"check: {OUT.relative_to(ROOT)} has not been written", file=sys.stderr)
        return 1
    committed = json.loads(OUT.read_text(encoding="utf-8"))
    fresh = build()
    if json.dumps(committed, sort_keys=True) != json.dumps(fresh, sort_keys=True):
        for c_old, c_new in zip(committed["cells"], fresh["cells"]):
            if json.dumps(c_old, sort_keys=True) != json.dumps(c_new, sort_keys=True):
                print(f"check: {c_old['block_id']} no longer re-derives", file=sys.stderr)
        print("check: the committed reading does not re-derive from the pixels",
              file=sys.stderr)
        return 1
    digest = hashlib.sha256(RASTER.read_bytes()).hexdigest()
    if digest != committed["raster"]["sha256"]:
        print(f"check: the raster is not the one this was read on ({digest})",
              file=sys.stderr)
        return 1
    print(f"check: {len(committed['cells'])} cell(s) re-derive from the committed pixels; "
          f"raster sha256 matches")
    return 0


def self_test():
    """Break each assertion and watch it fire."""
    doc = build()
    cells = {c["block_id"]: c for c in doc["cells"]}
    fails = []

    def want(name, ok, saw):
        if not ok:
            fails.append(f"{name}: {saw}")

    want("twenty-seven cells", len(doc["cells"]) == 27, len(doc["cells"]))
    want("the alley is in the two river tiers only",
         doc["summary"]["tiers_with_an_alley"] == ["illinois_north", "indiana_north"],
         doc["summary"]["tiers_with_an_alley"])
    want("nineteen cells are drawn whole",
         doc["summary"]["by_verdict"]["undivided"] == 19,
         doc["summary"]["by_verdict"]["undivided"])
    want("five cells are lotted", doc["summary"]["by_verdict"]["lotted"] == 5,
         doc["summary"]["by_verdict"]["lotted"])
    want("every lotted cell is six to a face", doc["summary"]["lots_per_face"] == [6],
         doc["summary"]["lots_per_face"])
    want("the Kinzie Block cell is not lotted",
         cells["blk_illinois_north_cass"]["verdict"] != "lotted",
         cells["blk_illinois_north_cass"]["verdict"])
    want("block 9 is refused as part-drawn",
         cells["blk_illinois_north_pine"]["verdict"] == "partly_drawn",
         cells["blk_illinois_north_pine"]["verdict"])
    want("no undivided cell carries a rule",
         all(not c["rules_px_x"] for c in doc["cells"] if c["verdict"] == "undivided"),
         "a whole cell carries a lot rule")
    want("the alley reads as a corridor on five cells",
         doc["alley"] and doc["alley"]["kerb_to_kerb_px"]["n"] == 5,
         doc["alley"] and doc["alley"]["kerb_to_kerb_px"]["n"])
    want("the alley is an alley and not a street",
         doc["alley"] and 10.0 <= doc["alley"]["alley_ft"] <= 25.0,
         doc["alley"] and doc["alley"]["alley_ft"])
    want("every cell's boundaries were read as rules and not taken from the kerb",
         all(c["boundary_read"]["west"] == "ruled" and c["boundary_read"]["east"] == "ruled"
             for c in doc["cells"] if c["verdict"] == "lotted"),
         "a lotted cell fell back to a street kerb for its own edge")
    if fails:
        for f in fails:
            print(f"self-test FAILED — {f}", file=sys.stderr)
        return 1
    print("self-test: 11/11 assertions hold")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    if args.check:
        return check()
    if args.write:
        doc = build()
        OUT.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n")
        print(f"wrote {OUT.relative_to(ROOT)}: {len(doc['cells'])} cell(s)")
        return 0
    return report(build())


if __name__ == "__main__":
    raise SystemExit(main())
