#!/usr/bin/env python3
"""census_pair_geometry.py — the geometry of a two-stroke figure in one cell of an
1840 continuation sheet, measured rather than described.

## Why this exists

`33S7-9YYJ-24`'s TOTAL column closes exactly against its own printed 201 over 31
lines, so every figure on it is labelled by arithmetic and not by opinion. Three
of those labels are a **4**, and each 4 is two strokes. `33S7-9YYJ-5V` carries
six two-stroke figures that a pass read as **11**, calling one of them "the
sheet's reference pair". Both readings describe their strokes in prose — "set
below and right", "tops level" — and prose is exactly where two readers of the
same ink disagree without either being able to show it. `33S7-9YYJ-6H` says so
outright: "the pitch test does not separate them on this sheet".

So this tool measures the three quantities the prose was reaching for, on the
same ink mask and the same component finder `read_census_continuation.py`
already defines (imported, never re-implemented):

  X OVERLAP     min(x1) - max(x0) of the two strokes' boxes. POSITIVE means the
                strokes stand over one another in x; NEGATIVE means one is
                wholly to the right of the other. This is the one that separates,
                and the reason is the form and not the hand: two digits written
                side by side occupy two x slots, and one numeral's two strokes
                share a slot however far apart their feet drift.
  FOOT OFFSET   the x of the lower stroke's lowest ink minus the other's. Prose
                about "set below and right" is reaching for this. Reported
                because it is what the earlier readings argued from - and it
                does NOT separate, which is worth being able to see.
  WEIGHT RATIO  ink pixels of the fainter stroke over the bolder, and the same
                for height. Also reported, also does not separate: 33S7-9YYJ-24
                line 21 is a 4 by arithmetic and its two strokes are twins.

WHAT THE CLASSES MEASURE, on nine figures whose value is fixed by a column or a
footing that closes and not by anyone's eye (see 33S7-9YYJ-5V's page file,
total_column.stroke_overlap_test, which lists them one by one):

    one numeral (a 4)   x overlap +10 to +18
    two digits          x overlap -13 to +5

It reads no digits. The numbers are the measurement and a human reads the figure.

    tools/census_pair_geometry.py 33S7-9YYJ-24 --box 1424 1026 1486 1074
    tools/census_pair_geometry.py 33S7-9YYJ-5V --boxes /tmp/boxes.json --json /tmp/out.json

Needs numpy + Pillow, like the module it borrows from. It is a research
instrument run by hand, not part of the per-commit gate.
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import read_census_continuation as rc


def strokes(a, box):
    """The ink components inside one box, largest first, each with its geometry."""
    np = rc._np()
    x0, y0, x1, y1 = box
    mask = rc.ink_mask(a, x0, y0, x1, y1)
    cs = rc.components(mask, x0, y0)
    out = []
    for c in cs:
        cx0, cy0, cx1, cy1 = c["x0"], c["y0"], c["x1"] - 1, c["y1"] - 1
        sub = mask[cy0 - y0:cy1 - y0 + 1, cx0 - x0:cx1 - x0 + 1]
        ys, xs = np.nonzero(sub)
        if len(ys) == 0:
            continue
        foot = int(xs[ys == ys.max()].mean()) + cx0
        head = int(xs[ys == ys.min()].mean()) + cx0
        out.append({
            "box": [int(cx0), int(cy0), int(cx1), int(cy1)],
            "ink_px": int(len(ys)),
            "height": int(cy1 - cy0 + 1),
            "foot_x": foot,
            "foot_y": int(cy1),
            "head_x": head,
            "head_y": int(cy0),
        })
    out.sort(key=lambda s: -s["ink_px"])
    return out, mask


def measure(fsid, box):
    a = rc.load(os.path.join(rc.DEPOSIT, fsid + ".jpg"))
    ss, _ = strokes(a, box)
    r = {"sheet": fsid, "box": list(box), "strokes": len(ss), "detail": ss}
    if len(ss) >= 2:
        bold, other = ss[0], ss[1]
        b1, b2 = bold["box"], other["box"]
        lower = bold if bold["foot_y"] >= other["foot_y"] else other
        upper = other if lower is bold else bold
        r["x_overlap_px"] = min(b1[2], b2[2]) - max(b1[0], b2[0])
        r["y_overlap_px"] = min(b1[3], b2[3]) - max(b1[1], b2[1])
        r["foot_offset_px"] = lower["foot_x"] - upper["foot_x"]
        r["weight_ratio"] = round(other["ink_px"] / bold["ink_px"], 3)
        r["height_ratio"] = round(other["height"] / bold["height"], 3)
    return r


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("sheet", nargs="?")
    ap.add_argument("--box", nargs=4, type=int, metavar=("X0", "Y0", "X1", "Y1"))
    ap.add_argument("--boxes", help="JSON list of {sheet, label, box:[x0,y0,x1,y1]}")
    ap.add_argument("--json")
    args = ap.parse_args()

    jobs = []
    if args.boxes:
        jobs = json.load(open(args.boxes))
    elif args.sheet and args.box:
        jobs = [{"sheet": args.sheet, "label": args.sheet, "box": args.box}]
    else:
        ap.error("give --box with a sheet, or --boxes")

    out = []
    for j in jobs:
        m = measure(j["sheet"], j["box"])
        m["label"] = j.get("label", j["sheet"])
        out.append(m)
        print("%-26s strokes=%d  x_overlap=%5s  foot_offset=%5s  weight=%5s  height=%5s" % (
            m["label"], m["strokes"], m.get("x_overlap_px", "-"),
            m.get("foot_offset_px", "-"), m.get("weight_ratio", "-"),
            m.get("height_ratio", "-")))
    if args.json:
        json.dump(out, open(args.json, "w"), indent=1)
        print("wrote", args.json)


if __name__ == "__main__":
    main()
