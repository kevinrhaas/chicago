#!/usr/bin/env python3
"""read_glyph_box.py — one named box of a census leaf, measured across an ink
threshold ladder, with controls measured the same way in the same call.

## Why this exists

`read_census_lower_blocks.py` sweeps a column at ONE ink threshold (45 grey
levels below local background) and reports the components that survive. That is
the right instrument for finding ink. It is the wrong instrument for arguing
about a figure written with a dry pen, because a stroke that is real but pale
simply does not appear, and its absence then reads as evidence that the figure
is not there.

The temptation at that point is to lower the threshold until the figure appears,
which is how a reading gets manufactured. This tool exists so that the lowering
is done in the open and never done alone: every box is measured at EVERY step of
a stated ladder, and the boxes are given in one call so that CONTROLS — a figure
already read, a mark already rejected as show-through — walk down the same ladder
beside the one in question. A threshold that brings out the disputed stroke and
also brings out the show-through has proved nothing; a threshold that brings out
the disputed stroke while the show-through stays absent has.

It reads no digits, for the same reason its parent module does not. It reports
where the ink is, how solid it is, and what paper it shuts in. A person reads the
digit off the image.

    tools/read_glyph_box.py 33S7-9YYJ-6H \
        --box "no_of_scholars_footing=3536,2958,3600,3014" \
        --box "total_footing_144=1205,2975,1340,3032" \
        --ladder 45,35,28,22

Needs Pillow and numpy, like `read_census_lower_blocks.py`. It is a research
instrument run by hand, whose OUTPUT is a human's reading; it is not in the gate.
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import read_census_continuation as rc  # noqa: E402
import read_census_lower_blocks as lb  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_LADDER = (45, 35, 28, 22)


def leaf_path(sheet):
    p = os.path.join(ROOT, "chicago", "reference", "census1840", sheet + ".jpg")
    if not os.path.exists(p):
        p = os.path.join(os.path.dirname(ROOT), "reference", "census1840", sheet + ".jpg")
    return p


def measure(g, box, thr, min_area, min_height):
    """Components of one box at one ink threshold, with solid and bowl for each."""
    x0, y0, x1, y1 = box
    keep_thr, keep_area, keep_h = rc.INK_BELOW_BACKGROUND, rc.MIN_AREA, rc.MIN_HEIGHT
    rc.INK_BELOW_BACKGROUND, rc.MIN_AREA, rc.MIN_HEIGHT = thr, min_area, min_height
    try:
        mask = rc.ink_mask(g, x0, y0, x1, y1)
        cs = rc.components(mask, x0, y0)
        for c in cs:
            holes, ink = lb.enclosed_paper(g, c["x0"] - 3, c["y0"] - 3,
                                           c["x1"] + 3, c["y1"] + 3)
            c["solid_fraction"] = round(lb.solid_fraction(g, c["x0"], c["y0"],
                                                          c["x1"], c["y1"]), 3)
            c["enclosed_paper_px"] = holes
            c["mask_px"] = ink
            c["w"] = c["x1"] - c["x0"]
            c["h"] = c["y1"] - c["y0"]
        return {"ink_px": int(mask.sum()), "components": cs}
    finally:
        rc.INK_BELOW_BACKGROUND, rc.MIN_AREA, rc.MIN_HEIGHT = keep_thr, keep_area, keep_h


def run(sheet, boxes, ladder, min_area, min_height):
    g = rc.load(leaf_path(sheet))
    out = {"sheet": sheet, "ladder": list(ladder),
           "filters": {"min_area": min_area, "min_height": min_height},
           "boxes": {}}
    for name, box in boxes:
        out["boxes"][name] = {"box": list(box),
                              "at": {str(t): measure(g, box, t, min_area, min_height)
                                     for t in ladder}}
    return out


def render(result):
    lines = []
    for name, b in result["boxes"].items():
        x0, y0, x1, y1 = b["box"]
        lines.append(f"{name}  x{x0}-{x1} y{y0}-{y1}")
        for t in result["ladder"]:
            r = b["at"][str(t)]
            lines.append(f"    ink>{t:>3}  mask {r['ink_px']:>5} px  "
                         f"{len(r['components'])} component(s)")
            for c in r["components"]:
                lines.append(f"        x{c['x0']}-{c['x1']} y{c['y0']}-{c['y1']}  "
                             f"{c['w']}x{c['h']}  area {c['area']}  "
                             f"solid {c['solid_fraction']}  "
                             f"encloses {c['enclosed_paper_px']} px")
        lines.append("")
    return "\n".join(lines)


def self_test():
    """The ladder must be monotone: lowering the threshold can only add ink."""
    ok = True
    g = rc.load(leaf_path("33S7-9YYJ-6H"))
    box = (3536, 2958, 3600, 3014)
    prev = -1
    for t in (45, 35, 28, 22):
        n = measure(g, box, t, rc.MIN_AREA, rc.MIN_HEIGHT)["ink_px"]
        if n < prev:
            print(f"FAIL ladder not monotone at {t}: {n} < {prev}")
            ok = False
        prev = n
    if rc.INK_BELOW_BACKGROUND != 45 or rc.MIN_AREA != 40 or rc.MIN_HEIGHT != 12:
        print("FAIL module constants not restored after measure()")
        ok = False
    print("read_glyph_box self-test:", "ok" if ok else "FAILED")
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("sheet", nargs="?")
    ap.add_argument("--box", action="append", default=[],
                    metavar="NAME=x0,y0,x1,y1")
    ap.add_argument("--ladder", default=",".join(str(t) for t in DEFAULT_LADDER))
    ap.add_argument("--min-area", type=int, default=rc.MIN_AREA)
    ap.add_argument("--min-height", type=int, default=rc.MIN_HEIGHT)
    ap.add_argument("--json", metavar="PATH")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if not a.sheet or not a.box:
        ap.error("a sheet and at least one --box are required")
    boxes = []
    for spec in a.box:
        name, _, nums = spec.partition("=")
        boxes.append((name, tuple(int(v) for v in nums.split(","))))
    ladder = tuple(int(v) for v in a.ladder.split(","))
    result = run(a.sheet, boxes, ladder, a.min_area, a.min_height)
    print(render(result))
    if a.json:
        with open(a.json, "w") as f:
            json.dump(result, f, indent=1)
        print("json ->", a.json)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
