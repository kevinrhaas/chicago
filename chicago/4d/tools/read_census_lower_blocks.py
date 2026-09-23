#!/usr/bin/env python3
"""read_census_lower_blocks.py — the four blocks of an 1840 continuation sheet
that `read_census_continuation.py` leaves unnamed, swept for the enumerator's ink.

## Why this exists

`read_census_continuation.py` names eight columns — TOTAL and the seven industry
columns — because the printed run between the TOTAL rule and the PENSIONERS rule
is the one stretch of the form whose columns can be named off pitch alone. The
other thirty-one columns of the sheet (twelve SLAVES, PENSIONERS names and ages,
six DEAF AND DUMB / BLIND AND INSANE white, four of the same for coloured
persons, seven SCHOOLS, &c.) are wide blocks of unequal pitch, and the tool
records their ink as one lump per block with a note saying the lump is dominated
by printed rules and is not evidence either way.

That left `33S7-9YYJ-6H` with the reading T-0629 owed: whether those blocks carry
anything, and what the 1 and the 40 at the head of its SCHOOLS block are.

## What it does

1. Takes the vertical printed rules at a stated coverage threshold, and NAMES the
   columns of the four blocks off them. The naming is checked by eye against the
   printed heading once, at magnification, and the check is what the block tables
   below record; the tool does not read print.
2. Sweeps each named column with the same instrument the industry columns were
   read with — `ink_mask` then `components` — INSET 9 px from each printed rule,
   so a rule's own scan shadow cannot register as ink.
3. Prints every surviving component with its box, its area, and two measurements
   that separate a written numeral from show-through and from a blot:
     * **solid fraction** — the share of the box's pixels standing 120 or more
       grey levels below the local background. A pen stroke has a solid core; the
       feathered ghost of writing on the other side of the leaf does not.
     * **enclosed paper** — paper the ink shuts in, found by flooding the box's
       background from its border. A bowl (0, 6, 8, 9) encloses; a slash does not.
   and the distance from the nearest printed rule, because the ink that survives
   an inset sweep and stands zero px off the rule is the rule's own clipped shadow.
4. Reads nothing. A digit is read by a person looking at the image; this file
   says where to look and what the ink is like when you get there.

## The pale-rule problem

6H is a pale exposure — `read_census_continuation.py` already needs `--cover 0.50`
on it where 5V takes the 0.6 default. The six DEAF AND DUMB / BLIND AND INSANE
white columns are paler still: at 0.50 only their outer rules stand, and the four
interior ones need 0.30. So the coverage threshold is per block, stated, and
printed with the result rather than buried.

    python3 tools/read_census_lower_blocks.py 33S7-9YYJ-6H
    python3 tools/read_census_lower_blocks.py --self-test
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import read_census_continuation as rc  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Inset from each printed rule, in px. A rule's scan shadow reaches about 7 px on
# this leaf (read_census_continuation records one 7 px off the rule at x1561), so
# 9 is that plus a margin.
INSET = 9

# Blocks, as printed left to right, for the RIGHT (continuation) sheet of the
# 1840 population schedule. `rules` are the x of the printed rules that bound the
# block's columns, measured on the leaf at `cover`; `names` are the printed heads
# those bounds were checked against by eye at magnification.
BLOCKS_6H = [
    {
        "block": "slaves",
        "cover": 0.50,
        "rules": [224, 309, 386, 464, 541, 620, 701, 780, 856, 935, 1014, 1087, 1169],
        "names": [
            "slaves_male_under_10", "slaves_male_10_under_24", "slaves_male_24_under_36",
            "slaves_male_36_under_55", "slaves_male_55_under_100", "slaves_male_100_and_upwards",
            "slaves_female_under_10", "slaves_female_10_under_24", "slaves_female_24_under_36",
            "slaves_female_36_under_55", "slaves_female_55_under_100", "slaves_female_100_and_upwards",
        ],
    },
    {
        "block": "pensioners",
        "cover": 0.50,
        "rules": [1865, 2300, 2380],
        "names": ["pensioners_names", "pensioners_ages"],
    },
    {
        "block": "deaf_dumb_blind_insane_white",
        "cover": 0.30,
        "rules": [2380, 2460, 2538, 2617, 2692, 2769, 2857],
        "names": [
            "ddbi_white_deaf_and_dumb_under_14", "ddbi_white_deaf_and_dumb_14_under_25",
            "ddbi_white_deaf_and_dumb_25_and_upwards", "ddbi_white_blind",
            "ddbi_white_insane_at_public_charge", "ddbi_white_insane_at_private_charge",
        ],
    },
    {
        "block": "deaf_dumb_blind_insane_colored",
        "cover": 0.50,
        "rules": [2858, 2937, 3020, 3107, 3192],
        "names": [
            "ddbi_colored_deaf_and_dumb", "ddbi_colored_blind",
            "ddbi_colored_insane_at_private_charge", "ddbi_colored_insane_at_public_charge",
        ],
    },
    {
        "block": "schools",
        "cover": 0.50,
        "rules": [3192, 3260, 3325, 3390, 3474, 3534, 3602],
        "names": [
            "schools_universities_or_colleges", "schools_number_of_students",
            "schools_academies_and_grammar_schools", "schools_no_of_scholars_academies",
            "schools_primary_and_common_schools", "schools_no_of_scholars_primary",
        ],
        "note": (
            "the seventh column, No. of Scholars at public charge, is bounded on the left "
            "at x3602 and has NO right-hand rule at any threshold down to 0.30: the leaf "
            "curls into the binding at about x3640 and the gutter takes it. It is not swept."
        ),
    },
]

BODY = {"33S7-9YYJ-6H": (619, 2959)}
FOOTER = {"33S7-9YYJ-6H": (2962, 3016)}


def solid_fraction(a, x0, y0, x1, y1, depth=120.0):
    np = rc._np()
    box = a[y0:y1, x0:x1].astype(float)
    ring = a[max(0, y0 - 40):y1 + 40, max(0, x0 - 40):x1 + 40].astype(float)
    bg = np.percentile(ring, 80)
    return float((box < bg - depth).sum()) / float(box.size)


def enclosed_paper(g, x0, y0, x1, y1):
    """Paper the ink shuts in, flooding the background from the box border."""
    np = rc._np()
    m = rc._close(rc.ink_mask(g, x0, y0, x1, y1), 5)
    h, w = m.shape
    free = ~m
    seen = np.zeros_like(free)
    stack = [(y, x) for x in range(w) for y in (0, h - 1) if free[y, x]]
    stack += [(y, x) for y in range(h) for x in (0, w - 1) if free[y, x]]
    while stack:
        y, x = stack.pop()
        if seen[y, x] or not free[y, x]:
            continue
        seen[y, x] = True
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            yy, xx = y + dy, x + dx
            if 0 <= yy < h and 0 <= xx < w and free[yy, xx] and not seen[yy, xx]:
                stack.append((yy, xx))
    return int((free & ~seen).sum()), int(m.sum())


def sweep(sheet, blocks=None, band=None, inset=INSET):
    blocks = blocks or BLOCKS_6H
    y0, y1 = band or BODY[sheet]
    path = os.path.join(ROOT, "chicago", "reference", "census1840", sheet + ".jpg")
    if not os.path.exists(path):
        path = os.path.join(os.path.dirname(ROOT), "reference", "census1840", sheet + ".jpg")
    g = rc.load(path)
    out = []
    for blk in blocks:
        rules, names = blk["rules"], blk["names"]
        for i, name in enumerate(names):
            bx0, bx1 = rules[i], rules[i + 1]
            m = rc.ink_mask(g, bx0 + inset, y0, bx1 - inset, y1)
            cs = [c for c in rc.components(m, bx0 + inset, y0)
                  if c["area"] >= 40 and (c["x1"] - c["x0"]) >= 8
                  and (c["y1"] - c["y0"]) <= 4 * (c["x1"] - c["x0"])
                  and c["x0"] >= bx0 + inset and c["x1"] <= bx1 - inset]
            for c in cs:
                holes, ink = enclosed_paper(g, c["x0"] - 3, c["y0"] - 3, c["x1"] + 3, c["y1"] + 3)
                c["solid_fraction"] = round(solid_fraction(g, c["x0"], c["y0"], c["x1"], c["y1"]), 3)
                c["enclosed_paper_px"] = holes
                c["px_from_nearest_rule"] = min(c["x0"] - bx0, bx1 - c["x1"])
            out.append({"block": blk["block"], "column": name,
                        "bounds_px": [bx0, bx1], "components": cs})
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("sheet", nargs="?", default="33S7-9YYJ-6H")
    ap.add_argument("--footer", action="store_true", help="sweep the footing band instead of the body")
    ap.add_argument("--inset", type=int, default=INSET,
                    help="px to stand off each printed rule (default 9, which is the rule's own "
                         "scan shadow plus a margin; this hand writes hard against the left rule, "
                         "so --inset 2 is what brings the SCHOOLS figures inside the window)")
    ap.add_argument("--json", help="write the sweep here")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    if args.sheet not in BODY:
        print(f"no block table for {args.sheet} — add one, measured, before sweeping it", file=sys.stderr)
        return 2
    band = FOOTER[args.sheet] if args.footer else BODY[args.sheet]
    rows = sweep(args.sheet, band=band, inset=args.inset)
    n = 0
    for r in rows:
        if not r["components"]:
            print(f"  {r['column']:42s} x{r['bounds_px'][0]}-{r['bounds_px'][1]}   —")
            continue
        print(f"  {r['column']:42s} x{r['bounds_px'][0]}-{r['bounds_px'][1]}")
        for c in r["components"]:
            n += 1
            print(f"      y{c['y0']}-{c['y1']} x{c['x0']}-{c['x1']}  "
                  f"{c['x1']-c['x0']}x{c['y1']-c['y0']} area {c['area']}  "
                  f"solid {c['solid_fraction']:.2f}  encloses {c['enclosed_paper_px']} px  "
                  f"{c['px_from_nearest_rule']} px off the rule")
    print(f"\n{n} component(s) survive the sweep in "
          f"{'the footing band' if args.footer else 'the body'} of {args.sheet}")
    if args.json:
        with open(args.json, "w") as fh:
            json.dump(rows, fh, indent=1)
    return 0


def self_test():
    """The block tables must partition the sheet without overlapping the columns
    read_census_continuation already names, and every block must be contiguous."""
    ok = True
    named = (1169, 1865)  # TOTAL through learned professions
    for blk in BLOCKS_6H:
        rules, names = blk["rules"], blk["names"]
        if len(rules) != len(names) + 1:
            print(f"FAIL {blk['block']}: {len(rules)} rules cannot bound {len(names)} columns")
            ok = False
        if rules != sorted(rules):
            print(f"FAIL {blk['block']}: rules are not in order")
            ok = False
        for i in range(len(names)):
            if rules[i + 1] - rules[i] < 2 * INSET + 8:
                print(f"FAIL {blk['block']}/{names[i]}: {rules[i+1]-rules[i]} px cannot hold a glyph after inset")
                ok = False
            if named[0] < rules[i] < named[1]:
                print(f"FAIL {blk['block']}/{names[i]}: overlaps the industry run")
                ok = False
    total = sum(len(b["names"]) for b in BLOCKS_6H)
    if total != 30:
        print(f"FAIL 6H: {total} columns named, and the printed form carries 30 outside the industry run "
              f"(12 slaves + 2 pensioners + 6 + 4 deaf/dumb/blind/insane + 6 of 7 schools)")
        ok = False
    print("self-test OK" if ok else "self-test FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
