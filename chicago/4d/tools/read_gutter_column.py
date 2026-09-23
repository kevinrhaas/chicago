#!/usr/bin/env python3
"""read_gutter_column.py — the last column of a leaf that curls into the binding:
is it bounded, how much of it survived the exposure, and is anything written in it.

## Why this exists

`read_census_lower_blocks.py` bounded thirty of `33S7-9YYJ-6H`'s thirty-one lower
columns off the vertical printed rules and swept them. It could not bound the
thirty-first — No. of Scholars at public charge — and said so:

    "bounded on the left at x3602 and has no right-hand rule at any threshold
     down to 0.30: the leaf curls into the binding at about x3640 and the gutter
     takes both the rule and the cell."

That was T-0755, and the refusal rested on two instrument properties rather than
on the leaf:

1. **The rule profile is measured in grey levels below background.** Down the
   gutter the paper itself falls from 207 to 177 to 4, so a rule that is a
   perfectly ordinary 35 per cent darker than its own paper stops clearing an
   absolute threshold tuned on paper at 207. This tool measures RELATIVE
   darkness — `(paper - ink) / paper`, against a per-row local paper level — and
   a printed rule then reads the same strength wherever it stands.
2. **The profile is taken over the whole body at once.** These rules LEAN: on 6H
   the rule committed at x3602 stands at x3586 under the heading and x3603 at the
   foot, seventeen px of drift. A rule near the edge is smeared over its own lean
   until it sinks into the noise, which is the same fault T-0761 filed against
   `read_census_continuation.py`. This tool TRACKS a rule down the leaf in y
   bands and reports the lean rather than averaging it away.

## What it does

1. `contrast(a, y0, y1, x0, x1)` — relative darkness below the local paper level,
   where the paper level is the 85th percentile over a +/- 40 px window IN X, so
   it follows the gutter falloff and steps over a narrow rule.
2. `track(...)` — the strongest contrast peak inside a search window, band by
   band down the leaf, with a least-squares lean fitted through the bands that
   are not swallowed by the gutter.
3. `edge(...)` — the first x, per band, at which contrast saturates: the visible
   edge of the leaf. It is not vertical, and how far the column survived depends
   on where you are down the page.
4. `centring(...)` — the arbiter. On this form a column's printed heading is set
   CENTRED between its own two rules. Measure the heading ink's x midpoint, and
   a candidate right rule is confirmed or refused by how far it puts the column
   midpoint from it. On 6H the six bounded SCHOOLS columns centre to within 1 px,
   which is what makes the test admissible on the seventh.
5. Then the cell between the tracked rules is swept with the instrument
   `read_census_lower_blocks.py` sweeps every other column with — `ink_mask`,
   `components`, solid fraction, enclosed paper — inset from each rule.

It reads no digits, like its two parents. It says whether there is a cell, how
much of it the exposure holds, and what ink stands in it; a person reads the
figure off the image.

    tools/read_gutter_column.py 33S7-9YYJ-6H --left 3602 --search 3625,3672
    tools/read_gutter_column.py --self-test

Needs numpy and Pillow. A research instrument run by hand, not in the gate.
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import read_census_continuation as rc  # noqa: E402
import read_census_lower_blocks as lb  # noqa: E402
from read_glyph_box import leaf_path  # noqa: E402

# The paper level a rule is measured against: a high percentile over a window in
# X, wide enough to step over a 4-6 px rule and narrow enough to follow the
# gutter's own falloff. 40 px and the 85th percentile hold both on 6H and 5V.
PAPER_HALF = 40
PAPER_PCT = 85
# Contrast at which the exposure has nothing left: the gutter, not a rule.
SATURATED = 0.95
# Bands the leaf is tracked in. 200 rows carries 2-3 written lines, which is
# short enough that a rule leaning 17 px over the leaf moves under 2 px inside one.
BAND = 200
# Clearance either side of a tracked rule before the cell is swept. Wider than
# read_census_lower_blocks' 9 px, because a rule standing in the gutter's own
# shading throws a wider skirt: measured on 6H, 9 px still returns nine
# components that are all fragments of the x3654 rule and 14 px returns none.
RULE_CLEARANCE = 14


def contrast(a, y0, y1, x0, x1):
    """Relative darkness below the local paper level, over a band of the leaf.

    Absolute darkness is the wrong instrument down a gutter: the paper falls with
    the ink. This returns (paper - value) / paper, which a printed rule holds at
    roughly the same value wherever on the leaf it stands.
    """
    np = rc._np()
    sub = a[y0:y1, x0:x1].astype("float32")
    n = sub.shape[1]
    paper = np.empty_like(sub)
    for i in range(n):
        lo = max(0, i - PAPER_HALF)
        hi = min(n, i + PAPER_HALF + 1)
        paper[:, i] = np.percentile(sub[:, lo:hi], PAPER_PCT, axis=1)
    paper = np.maximum(paper, 4.0)
    return np.clip((paper - sub) / paper, -1.0, 1.0), paper


def profile(a, y0, y1, x0, x1):
    """Mean relative darkness per x over one band, and the median paper level."""
    np = rc._np()
    c, paper = contrast(a, y0, y1, x0, x1)
    return c.mean(axis=0), np.median(paper, axis=0)


def edge(a, y0, y1, x0, x1):
    """The first x at which the band saturates — the visible edge of the leaf."""
    m, _ = profile(a, y0, y1, x0, x1)
    for i, v in enumerate(m):
        if v > SATURATED:
            return x0 + i
    return None


def track(a, body, search, x0, x1, band=BAND):
    """The strongest contrast peak in `search`, band by band down the leaf.

    A band whose peak stands at or past the saturated edge is reported and marked
    `at_edge`: there the gutter is the strongest thing in the window and the peak
    is not a rule. The lean is fitted through the rest.
    """
    np = rc._np()
    lo, hi = search
    rows = []
    y = body[0]
    while y < body[1]:
        y2 = min(y + band, body[1])
        if y2 - y < band // 2:
            break
        m, paper = profile(a, y, y2, x0, x1)
        e = edge(a, y, y2, x0, x1)
        seg = m[lo - x0:hi - x0]
        j = int(np.argmax(seg)) + (lo - x0)
        px = x0 + j
        rows.append({"y0": y, "y1": y2, "x": px, "strength": round(float(m[j]), 3),
                     "paper": int(paper[j]), "edge": e,
                     "at_edge": e is not None and px >= e - 2})
        y = y2
    good = [r for r in rows if not r["at_edge"]]
    lean = None
    if len(good) >= 3:
        ys = np.array([(r["y0"] + r["y1"]) / 2.0 for r in good])
        xs = np.array([float(r["x"]) for r in good])
        slope, intercept = np.polyfit(ys, xs, 1)
        lean = {"slope_px_per_row": round(float(slope), 5),
                "intercept_px": round(float(intercept), 1),
                "bands_fitted": len(good),
                "rms_px": round(float(np.sqrt(((xs - (slope * ys + intercept)) ** 2).mean())), 2)}
    return {"bands": rows, "lean": lean}


def at_y(lean, y):
    """Where a fitted rule stands at one y."""
    return lean["slope_px_per_row"] * y + lean["intercept_px"]


def heading_ink(a, y0, y1, x0, x1, thr=0.50):
    """The x stretches the printed heading's type occupies, in one heading band.

    Reported as runs of x whose contrast clears `thr` on at least a quarter of the
    band's rows. On this form each rotated heading line is one such run.
    """
    c, _ = contrast(a, y0, y1, x0, x1)
    f = (c > thr).mean(axis=0)
    runs, start = [], None
    for i, v in enumerate(f):
        if v >= 0.25 and start is None:
            start = i
        elif v < 0.25 and start is not None:
            if i - start >= 4:
                runs.append((x0 + start, x0 + i - 1))
            start = None
    if start is not None and len(f) - start >= 4:
        runs.append((x0 + start, x1 - 1))
    return runs


def centring(heading_runs, left_rule, right_rule):
    """How far a candidate right rule puts the column's midpoint from its heading's.

    The printed headings of this form are set centred in their columns. The test
    is only admissible where it has been shown to hold on columns already bounded,
    so `run()` measures it on every bounded column of the block first.
    """
    if not heading_runs:
        return None
    a0 = min(r[0] for r in heading_runs)
    a1 = max(r[1] for r in heading_runs)
    heading_mid = (a0 + a1) / 2.0
    column_mid = (left_rule + right_rule) / 2.0
    return {"heading_ink": [a0, a1], "heading_mid": round(heading_mid, 1),
            "column_mid": round(column_mid, 1),
            "offset_px": round(column_mid - heading_mid, 1)}


def rule_in_band(a, y0, y1, guess, window, half=10):
    """Where a rule actually stands inside one band, searched around a guess.

    The lean is fitted over the body and the heading is 150 rows above it, so
    extrapolating the fit that far overshoots by up to 5 px — measured on
    no_of_scholars_primary, whose heading then fails a test it should pass. The
    fit is used to say WHERE TO LOOK; the band itself says where the rule is.

    The window is +/-10 px and not wider: at +/-14 the search around the sixth
    SCHOOLS column's right rule reaches the SEVENTH column's heading type, which
    is darker than the rule and wins the argmax.
    """
    np = rc._np()
    x0, x1 = window
    m, _ = profile(a, y0, y1, x0, x1)
    lo = max(0, int(guess) - half - x0)
    hi = min(len(m), int(guess) + half + 1 - x0)
    j = int(np.argmax(m[lo:hi])) + lo
    return x0 + j, float(m[j])


def centring_at_heading(a, left, right, body, heading, window):
    """Track both of a column's rules, carry them up to the heading's own y, and
    measure the heading's type against the column they bound there.

    Both rules are tracked, never assumed: at the heading a rule stands up to
    17 px left of where the body commits it, and a column measured with body
    bounds against heading ink would fail the test on the lean alone.
    """
    x0, x1 = window
    lt = track(a, body, (left - 22, left + 22), x0, x1)
    rt = track(a, body, (right - 22, right + 22), x0, x1)
    if not (lt["lean"] and rt["lean"]):
        return None
    hy = (heading[0] + heading[1]) / 2.0
    l_at_h, sl = rule_in_band(a, heading[0], heading[1], at_y(lt["lean"], hy), window)
    r_at_h, sr = rule_in_band(a, heading[0], heading[1], at_y(rt["lean"], hy), window)
    runs = [q for q in heading_ink(a, heading[0], heading[1],
                                   int(l_at_h) - 4, int(r_at_h) + 4)
            if q[0] > l_at_h + 4 and q[1] < r_at_h - 4]
    c = centring(runs, l_at_h, r_at_h)
    if c:
        c["rules_at_heading"] = [l_at_h, r_at_h]
        c["rule_strength"] = [round(sl, 3), round(sr, 3)]
        c["rules_predicted"] = [round(at_y(lt["lean"], hy), 1), round(at_y(rt["lean"], hy), 1)]
        c["at_y"] = round(hy)
    return c


def sweep(a, x0, y0, x1, y1, thr=None):
    """The cell, swept with read_census_lower_blocks' own instrument."""
    keep = rc.INK_BELOW_BACKGROUND
    if thr is not None:
        rc.INK_BELOW_BACKGROUND = thr
    try:
        mask = rc.ink_mask(a, x0, y0, x1, y1)
        cs = rc.components(mask, x0, y0)
        out = []
        for c in cs:
            w = c["x1"] - c["x0"]
            h = c["y1"] - c["y0"]
            if c["area"] < rc.MIN_AREA or w < 8 or h < rc.MIN_HEIGHT:
                continue
            holes, ink = lb.enclosed_paper(a, c["x0"] - 3, c["y0"] - 3,
                                           c["x1"] + 3, c["y1"] + 3)
            out.append({"x0": c["x0"], "x1": c["x1"], "y0": c["y0"], "y1": c["y1"],
                        "w": w, "h": h, "area": c["area"],
                        "aspect_h_over_w": round(h / max(w, 1), 2),
                        "solid_fraction": round(lb.solid_fraction(a, c["x0"], c["y0"],
                                                                 c["x1"], c["y1"]), 3),
                        "enclosed_paper_px": holes, "mask_px": ink})
        out.sort(key=lambda c: -c["area"])
        return out
    finally:
        rc.INK_BELOW_BACKGROUND = keep


def run(sheet, left, search, body, heading, window, controls):
    a = rc.load(leaf_path(sheet))
    x0, x1 = window
    tracked_left = track(a, body, (left - 22, left + 22), x0, x1)
    tracked_right = track(a, body, search, x0, x1)
    result = {"sheet": sheet, "window": list(window), "body": list(body),
              "heading_band": list(heading),
              "left_rule": {"quoted": left, "tracked": tracked_left},
              "right_rule": {"searched": list(search), "tracked": tracked_right}}

    runs = heading_ink(a, heading[0], heading[1], x0, x1)
    result["heading_runs"] = [list(r) for r in runs]

    # The centring test, first on columns already bounded, then on this one.
    ctrl = []
    for name, (l, r) in controls:
        # each control gets a window that contains its own rules: rule_in_band
        # searches inside the window it is given, and a guess outside it silently
        # returns the strongest thing in the window instead.
        c = centring_at_heading(a, l, r, body, heading, (l - 70, r + 70))
        if c:
            c["column"] = name
            ctrl.append(c)
    result["centring_controls"] = ctrl

    lean_l = tracked_left["lean"]
    lean_r = tracked_right["lean"]
    if lean_l and lean_r:
        hy = (heading[0] + heading[1]) / 2.0
        l_at_h = at_y(lean_l, hy)
        r_at_h = at_y(lean_r, hy)
        hr = [q for q in runs if q[0] > l_at_h + 4 and q[1] < r_at_h - 2]
        c = centring(hr, l_at_h, r_at_h)
        if c:
            c["column"] = "candidate"
            c["at_y"] = round(hy)
        result["centring_candidate"] = c
        # THE WIDTH TEST, which is what the centring actually establishes. The
        # right rule is measurable only in the bands where the gutter has receded,
        # so carrying it up to the heading is a 1,700-row extrapolation and its
        # ABSOLUTE position there is worth little. Its WIDTH is not: the heading's
        # own midpoint fixes the column's width at the heading without any
        # extrapolation at all, and the tracked rules fix it again lower down.
        l_h, _ = rule_in_band(a, heading[0], heading[1], l_at_h, window)
        if c:
            demanded = 2.0 * c["heading_mid"] - l_h
            result["width_test"] = {
                "left_rule_at_heading": l_h,
                "heading_mid": c["heading_mid"],
                "right_rule_the_heading_demands": round(demanded, 1),
                "width_at_heading": round(demanded - l_h, 1),
                "width_where_both_rules_are_measurable": [
                    {"y0": b["y0"], "y1": b["y1"],
                     "width": round(at_y(lean_r, (b["y0"] + b["y1"]) / 2.0)
                                    - at_y(lean_l, (b["y0"] + b["y1"]) / 2.0), 1)}
                    for b in tracked_right["bands"] if not b["at_edge"]],
            }
        # and the cell, swept between the two tracked rules
        cells = []
        y = body[0]
        while y < body[1]:
            y2 = min(y + BAND, body[1])
            lx = int(round(at_y(lean_l, (y + y2) / 2.0))) + RULE_CLEARANCE
            rx = int(round(at_y(lean_r, (y + y2) / 2.0))) - RULE_CLEARANCE
            if rx - lx >= 8:
                cells.append({"y0": y, "y1": y2, "x0": lx, "x1": rx,
                              "components": sweep(a, lx, y, rx, y2)})
            y = y2
        result["cell_sweep"] = cells
    return result


def render(r):
    out = [f"{r['sheet']}  window x{r['window'][0]}-{r['window'][1]}", ""]
    for side in ("left_rule", "right_rule"):
        t = r[side]["tracked"]
        out.append(f"{side}:")
        for b in t["bands"]:
            flag = "  (at the edge — gutter, not a rule)" if b["at_edge"] else ""
            out.append(f"    y{b['y0']:>5}-{b['y1']:<5} x{b['x']}  "
                       f"strength {b['strength']:.3f}  paper {b['paper']:>3}  "
                       f"leaf edge x{b['edge']}{flag}")
        if t["lean"]:
            L = t["lean"]
            out.append(f"    lean {L['slope_px_per_row']:+.5f} px/row over "
                       f"{L['bands_fitted']} bands, rms {L['rms_px']} px")
        out.append("")
    out.append("centring — the printed heading against the column it stands in:")
    for c in r.get("centring_controls", []):
        out.append(f"    {c['column']:<44} heading mid {c['heading_mid']:>7}  "
                   f"column mid {c['column_mid']:>7}  off {c['offset_px']:+.1f}")
    c = r.get("centring_candidate")
    if c:
        out.append(f"    {'CANDIDATE at y' + str(c['at_y']):<44} heading mid "
                   f"{c['heading_mid']:>7}  column mid {c['column_mid']:>7}  "
                   f"off {c['offset_px']:+.1f}")
    w = r.get("width_test")
    if w:
        out.append("")
        out.append("the width test — no extrapolation on either side:")
        out.append(f"    left rule at the heading  x{w['left_rule_at_heading']}, "
                   f"heading type centred on x{w['heading_mid']}")
        out.append(f"    -> the heading demands a right rule at "
                   f"x{w['right_rule_the_heading_demands']}, a column "
                   f"{w['width_at_heading']} px wide")
        for b in w["width_where_both_rules_are_measurable"]:
            out.append(f"    tracked rules give   y{b['y0']}-{b['y1']}  {b['width']} px")
    out.append("")
    if r.get("cell_sweep"):
        out.append("the cell, swept between the tracked rules:")
        for b in r["cell_sweep"]:
            out.append(f"    y{b['y0']}-{b['y1']}  x{b['x0']}-{b['x1']}  "
                       f"{len(b['components'])} component(s)")
            for c in b["components"]:
                out.append(f"        x{c['x0']}-{c['x1']} y{c['y0']}-{c['y1']}  "
                           f"{c['w']}x{c['h']}  area {c['area']}  "
                           f"aspect {c['aspect_h_over_w']}  "
                           f"solid {c['solid_fraction']}  "
                           f"encloses {c['enclosed_paper_px']} px")
    return "\n".join(out)


def self_test():
    """Three properties, each measured on 6H, whose answers are already known.

    1. Relative contrast finds the three SCHOOLS rules the page file commits.
    2. Tracking a rule down the leaf recovers its lean, and the lean is the
       reason a whole-body profile loses a rule near the edge.
    3. The centring test holds on columns that are already bounded, which is the
       only thing that makes it admissible on one that is not.
    """
    ok = True
    a = rc.load(leaf_path("33S7-9YYJ-6H"))
    body = (619, 2940)
    for quoted in (3474, 3534, 3602):
        t = track(a, body, (quoted - 22, quoted + 22), 3440, 3700)
        if not t["lean"]:
            print(f"FAIL no lean fitted for the rule at x{quoted}")
            ok = False
            continue
        got = at_y(t["lean"], 2400)
        if abs(got - quoted) > 6:
            print(f"FAIL rule x{quoted} tracked to {got:.0f} at y2400")
            ok = False
        if t["lean"]["slope_px_per_row"] <= 0:
            print(f"FAIL rule x{quoted} does not lean right down the leaf")
            ok = False
    t = track(a, body, (3580, 3624), 3440, 3700)
    span = at_y(t["lean"], 2900) - at_y(t["lean"], 619)
    if span < 8:
        print(f"FAIL the x3602 rule's lean measures {span:.1f} px; T-0761 says these lean")
        ok = False
    controls = [("primary_and_common_schools", (3474, 3534)),
                ("no_of_scholars_primary", (3534, 3602))]
    for name, (l, r) in controls:
        c = centring_at_heading(a, l, r, body, (370, 575), (3440, 3700))
        if c is None or abs(c["offset_px"]) > 3:
            print(f"FAIL heading of {name} is not centred in its column: {c}")
            ok = False
    print("read_gutter_column self-test:", "ok" if ok else "FAILED")
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("sheet", nargs="?")
    ap.add_argument("--left", type=int, help="x of the column's committed left rule")
    ap.add_argument("--search", help="x0,x1 to search for the right rule in")
    ap.add_argument("--body", default="619,2940")
    ap.add_argument("--heading", default="370,575")
    ap.add_argument("--window", default="3440,3700")
    ap.add_argument("--control", action="append", default=[],
                    metavar="NAME=x0,x1", help="a column already bounded, for the centring test")
    ap.add_argument("--json", metavar="PATH")
    ap.add_argument("--self-test", action="store_true")
    o = ap.parse_args()
    if o.self_test:
        return self_test()
    if not o.sheet or o.left is None or not o.search:
        ap.error("a sheet, --left and --search are required")
    pair = lambda s: tuple(int(v) for v in s.split(","))  # noqa: E731
    controls = []
    for spec in o.control:
        name, _, nums = spec.partition("=")
        controls.append((name, pair(nums)))
    r = run(o.sheet, o.left, pair(o.search), pair(o.body), pair(o.heading),
            pair(o.window), controls)
    print(render(r))
    if o.json:
        with open(o.json, "w") as f:
            json.dump(r, f, indent=1)
        print("json ->", o.json)
    return 0


if __name__ == "__main__":
    sys.exit(main())
