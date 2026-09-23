#!/usr/bin/env python3
"""census_total_column.py — the entry count and the footer figure position of ONE
column of an 1840 continuation sheet, on an explicitly given x window.

## Why this exists beside read_census_continuation.py

`read_census_continuation.py` names the eight middle columns off the printed
rules and refuses the sheet when it cannot: on four of the nine continuation
sheets of image group 26-50 it prints `no industry run bracketed by TOTAL and
PENSIONERS: the form is not as expected`, and on `33SQ-GYYJ-5H` it finds too few
rules to name anything. The refusal is right — a tool that guessed at which
column was TOTAL would launder a guess into a measurement — but it leaves the
one number the PAIRING needs unmeasured: how many ruled lines of the sheet carry
an entry.

That number does not need the whole form named. It needs one column's x window,
which a human reads off the printed rules at magnification, and then exactly the
grouping rule `read_census_continuation.py` already defines. So this tool takes
the window as an argument, RECORDS it in its output, and applies that module's
own ink mask, component filter and grouping — no second definition of any of
them. The window is the human judgement; everything after it is measured.

    tools/census_total_column.py 33S7-9YYJ-V4 --x0 0.300 --x1 0.360
    tools/census_total_column.py 33S7-9YYJ-V4 --x0 0.300 --x1 0.360 --json /tmp/v4.json

It reads no digits, for the same reason the module it borrows from does not: the
boxes are the measurement and a human reads the figure in the box.
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import read_census_continuation as rc


def measure(fsid, xf0, xf1, yf0=None, yf1=None):
    path = os.path.join(rc.DEPOSIT, fsid + ".jpg")
    a = rc.load(path)
    h, w = a.shape[0], a.shape[1]
    if yf0 is None or yf1 is None:
        y0, y1 = rc.horizontal_rules(a, int(w * 0.07), int(w * 0.30))
        band = "located by read_census_continuation.horizontal_rules()"
    else:
        y0, y1 = int(yf0 * h), int(yf1 * h)
        band = ("GIVEN. horizontal_rules() finds the strongest pair of rules in the "
                "leaf, and on a sheet whose entries stop part way down that pair can "
                "close above the enumerator's footer rule. Where that happens the band "
                "is read off the leaf at magnification and stated here.")
    x0, x1 = int(xf0 * w), int(xf1 * w)
    ix0, ix1 = x0 + rc.RULE_CLEARANCE, x1 - rc.RULE_CLEARANCE
    m = rc._close(rc.ink_mask(a, ix0, y0, ix1, y1))
    comps = [c for c in rc.components(m, ix0, y0)
             if (c["y1"] - c["y0"]) <= rc.MAX_ASPECT * max(c["x1"] - c["x0"], 1)]
    groups = rc.group(comps)
    return {
        "image": os.path.relpath(path, rc.REPO),
        "image_size": [int(w), int(h)],
        "body_between_rules": [int(y0), int(y1)],
        "body_band_how": band,
        "window_given": {"x0_fraction": xf0, "x1_fraction": xf1,
                         "x0_px": x0, "x1_px": x1,
                         "why": "read off the printed rules at magnification; this is the "
                                "human judgement the rest of the measurement rests on"},
        "components": len(comps),
        "groups": len(groups),
        "group_centres": [round(g["cy"], 1) for g in groups],
        "group_boxes": [[g["x0"], g["y0"], g["x1"], g["y1"], len(g["parts"])] for g in groups],
        "group_count_sensitivity": {str(d): len(rc.group(comps, d)) for d in (35, 45, 55, 65, 75)},
        "method": "read_census_continuation.py's own ink mask, component filter and "
                  "grouping rule, applied to the given window. Digits NOT read.",
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("sheet")
    ap.add_argument("--x0", type=float, required=True, help="left of the window, as a fraction of image width")
    ap.add_argument("--x1", type=float, required=True, help="right of the window, as a fraction of image width")
    ap.add_argument("--y0", type=float, help="top of the body band, as a fraction of image height")
    ap.add_argument("--y1", type=float, help="bottom of the body band, as a fraction of image height")
    ap.add_argument("--json")
    a = ap.parse_args()
    out = measure(a.sheet, a.x0, a.x1, a.y0, a.y1)
    print(f"{out['image']}  {out['image_size'][0]}x{out['image_size'][1]}")
    print(f"body between horizontal rules: y {out['body_between_rules'][0]}-{out['body_between_rules'][1]}")
    print(f"window x {out['window_given']['x0_px']}-{out['window_given']['x1_px']} px")
    print(f"{out['components']} components -> {out['groups']} groups")
    print("group count by grouping dy: " + ", ".join(f"{k}:{v}" for k, v in out["group_count_sensitivity"].items()))
    if a.json:
        with open(a.json, "w") as f:
            json.dump(out, f, indent=1)
        print(f"wrote {a.json}")


if __name__ == "__main__":
    main()
