#!/usr/bin/env python3
"""read_census_continuation.py — the row grid and the glyph boxes of an 1840
continuation sheet, measured off the image rather than judged by eye.

## Why this exists

The right-hand (continuation) sheet of the 1840 population schedule carries the
numbers rather than the names: twelve slave columns, the family TOTAL, seven
industry columns, pensioners, ten deaf/dumb/blind/insane columns and seven
schools columns. T-0535's reading of `33S7-9YYJ-24` closed against all five of
that sheet's printed column totals in four passes and was taken as the price of
a sheet. It was not: T-0538 and T-0541 were both split when the estimate broke,
and the reason T-0541 recorded is the one this file answers.

**These sheets are not ruled across.** The reading of `33S7-9YYJ-5V` measured it:
a row-darkness profile taken through the empty slaves block finds exactly two
strong horizontal rules on the leaf — under the printed heading and above the
enumerator's footer — and the largest excess over local background anywhere
between them is 4 grey levels, against 77 to 211 for those two. The printed form
rules the page vertically only. So there is no grid to count rows against, and
every row assignment has to come from the enumerator's own ink.

Which made the reading a matter of opinion, sheet after sheet, and produced the
disagreement this tool exists to end: the ink of one sheet's TOTAL column
clusters into 31 groups at one threshold and 28 at another, and `coverage.json`
had 28 "to the nearest line" from an inventory pass. Nothing said which was
right, because nothing was reproducible.

## What it measures, and what it refuses to do

It measures three things and prints them, and every one of them is re-derivable
from the committed image with no numbers typed in:

1. **The column geometry.** Vertical printed rules, found as a column-darkness
   profile over the body band. The eight single-width columns of the middle of
   the form — TOTAL and the seven industry columns — are then named off the
   pitch of those rules and the wide cells that bracket the run; pitch alone is
   not enough, and locate_columns() records why.
2. **The ink of each column**, as a local-background-subtracted mask. A flat
   global threshold does not work on these leaves: the exposure falls off two
   grey levels per hundred pixels toward the gutter, so ink at the right edge is
   paler than paper at the left. The background is a 25-pixel Gaussian of the
   crop itself and the mask is what stands 45 levels darker than it.
3. **The glyph components** of each column: 8-connected components of that mask,
   after a 5x5 closing to join a stroke a scan has broken, filtered to those at
   least 40 pixels in area and 12 pixels tall. Each is reported as a box.

**It does not read digits, and it must not.** A tool that guessed at a `4` that
is two strokes reading as `11`, or at a `7` and a `9` that differ by a loop,
would launder a guess into a measurement — which is the one thing this project's
provenance rule forbids. The boxes are the measurement; a human reads the digit
in the box, at magnification, against the glyph forms the sheet's own footer
row calibrates.

## The grouping rule, which is the actual finding

A number is one line's entry. Two components belong to the same number when the
hand has not gone back to the left of the cell for a new one: the y centres are
within `--group-dy` (55 px, against a line pitch measured at 58-90 on 5V) AND x
does not step back. That rule, and nothing else, produces the group count. The
count it produces is reported WITH the alternatives at the neighbouring
thresholds, because a count that changes with the threshold is a range and
saying so is the honest form of the answer.

Row identity is then ANCHORED, where it can be, by cross-column coincidence: an
entry in the commerce, manufactures or learned-professions column sits on the
same line as the TOTAL group it coincides with in y, and those coincidences are
independent of any threshold. On 5V, 22 lines are anchored that way. They are
the committed part of the row grid; the bands between them are named as open.

    tools/read_census_continuation.py 33S7-9YYJ-5V
    tools/read_census_continuation.py 33S7-9YYJ-5V --json /tmp/5v.json
    tools/read_census_continuation.py --self-test

Needs numpy and Pillow (`pip install numpy pillow`). Neither is in the per-commit
gate's install list and this tool is not in the gate: it is a research
instrument, run by hand, whose OUTPUT is committed under
`data/research/census_1840/pages/`.
"""
import argparse
import json
import os
import sys

APP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # chicago/4d
REPO = os.path.dirname(os.path.dirname(APP))                        # the repo root
DEPOSIT = os.path.join(REPO, "chicago", "reference", "census1840")

# The body band of a continuation leaf, as a fraction of image height: below the
# heading rule and above the footer rule. Deliberately generous — the two rules
# are then LOCATED inside it rather than assumed at these fractions.
BODY_FRAC = (0.13, 0.95)

# The eight single-width columns of the middle of the form, in printed order.
# Named here, but their x bounds are measured; see locate_columns().
MIDDLE_COLUMNS = [
    "total",
    "mining",
    "agriculture",
    "commerce",
    "manufactures_and_trades",
    "navigation_ocean",
    "navigation_canals_lakes_rivers",
    "learned_professions_and_engineers",
]

INK_BELOW_BACKGROUND = 45   # grey levels darker than local background
BACKGROUND_BLUR = 25        # px, the Gaussian that defines "local background"
MIN_AREA = 40               # px, below which a component is a speck
MIN_HEIGHT = 12             # px, below which a component is a speck
GROUP_DY = 55               # px, within which two components are one number
# The printed rules are 4-6 px of solid ink and a crop that includes one breaks
# into dozens of components that are not writing. Measured on 5V: 9 px of
# clearance either side is the first inset at which every column's component
# count stops changing (6 and 8 px still catch rule fragments in agriculture and
# the canals column), and it costs nothing — the entries stand mid-cell.
RULE_CLEARANCE = 9          # px, cleared either side of a column's own rules
RULE_COVER = 0.60           # fraction of body rows a printed rule must darken
RULE_MERGE_PX = 12          # px, within which two candidates are one rule + its shadow
RULE_MIN_DEPTH = 20.0       # grey levels of mean darkness a rule must carry
# A paper crease that survives the ink mask arrives as a sliver: 1 to 10 px wide
# and 27 to 270 px tall on 33S7-9YYJ-6H, which is 8 to 84 times as tall as it is
# wide. No number written by this hand is anything like that shape. Measured over
# every group both sheets put in the seven industry columns, the tallest real one
# stands at 3.0 (a `1`, 8x24 px on 5V; 10x30 on 6H), so a floor at 4.0 sits above
# every entry either sheet has and below every crease 6H has.
MAX_ASPECT = 4.0            # height/width, above which a component is a crease


def _np():
    try:
        import numpy as np
        return np
    except ImportError:  # pragma: no cover - environment guard
        sys.exit("read_census_continuation.py needs numpy: pip install numpy pillow")


def _pil():
    try:
        from PIL import Image, ImageFilter
        return Image, ImageFilter
    except ImportError:  # pragma: no cover - environment guard
        sys.exit("read_census_continuation.py needs Pillow: pip install numpy pillow")


def load(path):
    np = _np()
    Image, _ = _pil()
    im = Image.open(path).convert("L")
    return np.asarray(im).astype("float32")


def horizontal_rules(a, x0, x1, thr=20.0):
    """The strong horizontal rules of the leaf, found through a band of the page
    that carries no writing. Returns (top, bottom) of the body."""
    np = _np()
    h = a.shape[0]
    band = a[:, x0:x1]
    row = band.mean(axis=1)
    lo, hi = int(h * BODY_FRAC[0]), int(h * BODY_FRAC[1])
    bg = float(np.percentile(row[lo:hi], 75))
    dark = bg - row
    hits = [y for y in range(int(h * 0.10), int(h * 0.99)) if dark[y] > thr]
    if not hits:
        raise SystemExit("no horizontal rule found: is this a continuation sheet?")
    groups = []
    cur = [hits[0]]
    for y in hits[1:]:
        if y - cur[-1] <= 5:
            cur.append(y)
        else:
            groups.append(cur)
            cur = [y]
    groups.append(cur)
    # The body is between the LAST rule of the heading block and the first rule
    # of the footer block: the widest empty span between consecutive groups.
    best = None
    for g0, g1 in zip(groups, groups[1:]):
        span = g1[0] - g0[-1]
        if best is None or span > best[0]:
            best = (span, g0[-1], g1[0])
    return best[1], best[2]


def vertical_rules(a, y0, y1, cover=RULE_COVER, merge=RULE_MERGE_PX,
                   min_depth=RULE_MIN_DEPTH):
    """Vertical printed rules through the body band, as x centres.

    Found by CONTINUITY, not by mean darkness. A column of mean darkness picks up
    the enumerator's own ink: on 33S7-9YYJ-5V a mean profile reports rules at
    x 1441 and x 1719, which are a family total and a `2`, and those two false
    rules are enough to make the column naming below lock onto the wrong block
    of the form. A printed rule runs the whole height of the table; a pen stroke
    does not. So a rule is an x where at least `cover` of the body's rows stand
    darker than their own local background.

    Continuity alone is not sufficient on every leaf, and 33S7-9YYJ-6H is the one
    that showed it. That exposure is paler than 5V's: at the default cover only
    26 rules survive and the industry run has a hole in it, so `locate_columns`
    refuses the sheet outright — and its fallback below cannot help, because that
    fallback removes a rule and this leaf is missing one. Dropping the cover
    recovers the run and brings two things with it that are NOT printed rules —

      * a rule's own scan shadow, 7 px off it (x 1561 beside the true rule at
        1554), and
      * a paper crease at x 1833, in the learned-professions cell, which a crop
        at magnification shows as a pale streak with no ink in it.

    Two measured filters remove both without touching what the default already
    found. `merge` folds candidates within that many px into one centre: a printed
    rule is 4-6 px of solid ink and its shadow sits inside 12. `min_depth` drops a
    candidate whose mean darkness below local background is under that many grey
    levels: measured on this leaf the crease stands at 15.2 against 25.1 to 48.6
    for the seven true rules of the industry run, and on 5V every true rule of that
    run stands at 29.3 or more. Both are floors well under the weakest real rule
    measured on either sheet, so they cut artefacts rather than evidence.
    """
    np = _np()
    Image, ImageFilter = _pil()
    sub = a[y0:y1, :]
    blur = Image.fromarray(sub.astype("uint8")).filter(ImageFilter.GaussianBlur(BACKGROUND_BLUR))
    bg = np.asarray(blur).astype("float32")
    excess = bg - sub
    dark = excess > 6.0
    frac = dark.mean(axis=0)
    depth = excess.mean(axis=0)
    hits = np.where(frac >= cover)[0]
    if len(hits) == 0:
        raise SystemExit("no continuous vertical rule found in the body band")
    groups = []
    cur = [int(hits[0])]
    for x in hits[1:]:
        x = int(x)
        if x - cur[-1] <= 4:
            cur.append(x)
        else:
            groups.append(cur)
            cur = [x]
    groups.append(cur)
    out = []
    for g in groups:
        if len(g) > 40:
            continue  # the leaf's dark edge / gutter, not a rule
        w = frac[g]
        cx = int(round(float((np.asarray(g) * w).sum() / w.sum())))
        if float(depth[max(0, cx - 2):cx + 3].max()) < min_depth:
            continue    # a crease: continuous, but there is no ink in it
        if out and cx - out[-1] <= merge:
            continue    # a printed rule's own scan shadow, not a second rule
        out.append(cx)
    return out


def locate_columns(rules, continuity=None):
    """Name the eight single-width columns off the rule pitch.

    Two blocks of this form stand at a near-constant narrow pitch: the seven
    industry columns, and the deaf/dumb/blind/insane and schools columns at the
    right of the leaf. Pitch alone cannot tell them apart, and a first cut of
    this function locked onto the wrong one. What separates them is what stands
    on either side: the industry run is bracketed by TOTAL, a cell 2 to 4
    pitches wide, and on the right by the pensioners AGES column, which is wider
    than an industry column. The right-hand blocks have no such bracket — every
    run inside them has a one-pitch cell on its left — so the test picks out the
    industry run and nothing else. The pensioners block is NOT tested as one wide
    cell, because its own AGES rule divides it and an earlier cut of this
    function failed on 5V for assuming otherwise.

    ONE FALLBACK, and it only fires when the strict test above finds nothing, so
    no sheet that already passes can be moved by it. Measured on 33S7-9YYJ-6Q:
    the strict test finds no candidate because a rule is reported at x1267, in
    the MIDDLE of the TOTAL cell, which leaves TOTAL 117 px wide against a 68 px
    industry pitch — 1.7 pitches, under the 1.8 the bracket demands. It is not a
    printed rule. It is the enumerator's own column of family totals standing one
    under another, and `cover` cannot reject it: it covers 0.765 of the body's
    rows against 0.769 for the true rule at x1190. What separates them is
    CONTINUITY OF A SINGLE STROKE rather than coverage — the longest UNBROKEN run
    of dark rows at x1267 is 164 px, 0.07 of the body, while the true rules that
    bracket it run 0.27 and 0.47 unbroken; a printed rule is one line, a stack of
    digits is thirty short ones. So when the strict test fails, the run is
    retried with the weakest-by-continuity rule dropped from the candidate left
    bracket, and the drop is accepted only if the merged TOTAL cell then lands in
    the same 2.0-4.0 pitch window every other sheet's does AND the dropped rule's
    unbroken run is under half that of BOTH rules bracketing it. On 6Q the merged
    cell is x1190-1384, 194 px, 2.5 pitches — the same 2.47 pitches 5V's TOTAL
    measures — and the slaves block to its left comes out at twelve columns, as
    the form has. Without `continuity` (which `read()` always supplies) the
    fallback is not attempted at all.
    """
    if len(rules) < 10:
        raise SystemExit("too few vertical rules to name the middle columns")
    best = None
    for i in range(1, len(rules) - 8):
        gaps = [rules[j + 1] - rules[j] for j in range(i, i + 7)]
        med = sorted(gaps)[len(gaps) // 2]
        if med <= 0:
            continue
        spread = max(abs(g - med) / med for g in gaps)
        if spread > 0.35:
            continue
        left = rules[i] - rules[i - 1]
        right = (rules[i + 8] - rules[i + 7]) if i + 8 < len(rules) else 0
        if left < 1.8 * med or right < 1.25 * med:
            continue
        if not (2.0 * med <= left <= 4.0 * med):
            continue        # TOTAL is a wide cell, but not as wide as a block
        if best is None or -spread > best[0]:
            best = (-spread, i, med)
    if best is not None:
        _, i, med = best
        run = rules[i:i + 8]
        bounds = {"total": (rules[i - 1], run[0])}
        for n, name in enumerate(MIDDLE_COLUMNS[1:]):
            bounds[name] = (run[n], run[n + 1])
        return bounds, med

    dropped = _drop_a_pen_stroke(rules, continuity)
    if dropped is not None:
        thinned, gone = dropped
        bounds, med = locate_columns(thinned)
        bounds["_total_left_rule_dropped"] = (gone, gone)
        return bounds, med
    raise SystemExit("no industry run bracketed by TOTAL and PENSIONERS: "
                     "the form is not as expected")


def _drop_a_pen_stroke(rules, continuity):
    """The fallback described in locate_columns(): try dropping one reported rule
    that is a stack of digits rather than a printed line, and say so.

    Returns (rules without it, its x) or None. Every candidate must satisfy both
    measured conditions — its unbroken run is under half of BOTH its neighbours',
    and removing it makes the strict bracket test pass — so a sheet where no such
    rule exists falls through to the SystemExit unchanged.
    """
    if not continuity:
        return None
    for k in range(1, len(rules) - 1):
        run, left, right = continuity[k], continuity[k - 1], continuity[k + 1]
        if run >= 0.5 * min(left, right):
            continue
        thinned = rules[:k] + rules[k + 1:]
        try:
            locate_columns(thinned)
        except SystemExit:
            continue
        return thinned, rules[k]
    return None


def rule_continuity(a, y0, y1, rules):
    """For each reported rule, the LONGEST UNBROKEN run of dark rows at its x, as
    a fraction of the body height. A printed rule is one continuous line and
    scores high; a column of the enumerator's digits covers as many rows in total
    but in thirty short pieces, and scores low. Measured through the same local
    background the rule finder uses, and searched +/-3 px either side of the
    reported centre so a rule 1 px off centre is not penalised.
    """
    np = _np()
    Image, ImageFilter = _pil()
    sub = a[y0:y1, :]
    blur = Image.fromarray(sub.astype("uint8")).filter(ImageFilter.GaussianBlur(BACKGROUND_BLUR))
    dark = (np.asarray(blur).astype("float32") - sub) > 6.0
    height = max(1, sub.shape[0])
    out = []
    for x in rules:
        best = 0
        for xx in range(max(0, x - 3), min(dark.shape[1], x + 4)):
            cur = 0
            for v in dark[:, xx]:
                cur = cur + 1 if v else 0
                if cur > best:
                    best = cur
        out.append(round(best / height, 3))
    return out


def ink_mask(a, x0, y0, x1, y1):
    np = _np()
    Image, ImageFilter = _pil()
    sub = a[y0:y1, x0:x1]
    blur = Image.fromarray(sub.astype("uint8")).filter(ImageFilter.GaussianBlur(BACKGROUND_BLUR))
    bg = np.asarray(blur).astype("float32")
    return (np.clip(bg - sub, 0, None) > INK_BELOW_BACKGROUND)


def _close(mask, k=5):
    """5x5 binary closing, in numpy alone: dilate then erode by max/min filters."""
    np = _np()
    def shift_or(m, fn):
        out = m.copy()
        r = k // 2
        for dy in range(-r, r + 1):
            for dx in range(-r, r + 1):
                out = fn(out, np.roll(np.roll(m, dy, 0), dx, 1))
        return out
    dil = shift_or(mask, np.logical_or)
    ero = shift_or(dil, np.logical_and)
    return ero


def components(mask, x0, y0):
    """8-connected components of a boolean mask, as boxes, in numpy alone.

    Two-pass union-find over rows. Written out rather than imported so the tool
    keeps to numpy + Pillow: scipy is not installed anywhere in this project.
    """
    np = _np()
    h, w = mask.shape
    labels = np.zeros((h, w), dtype="int32")
    parent = [0]

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(x, y):
        rx, ry = find(x), find(y)
        if rx != ry:
            parent[max(rx, ry)] = min(rx, ry)

    nxt = 1
    for y in range(h):
        row = mask[y]
        for x in np.flatnonzero(row):
            neigh = []
            for dy, dx in ((-1, -1), (-1, 0), (-1, 1), (0, -1)):
                yy, xx = y + dy, x + dx
                if 0 <= yy < h and 0 <= xx < w and labels[yy, xx]:
                    neigh.append(int(labels[yy, xx]))
            if not neigh:
                labels[y, x] = nxt
                parent.append(nxt)
                nxt += 1
            else:
                m = min(find(n) for n in neigh)
                labels[y, x] = m
                for n in neigh:
                    union(m, n)

    boxes = {}
    for y in range(h):
        for x in np.flatnonzero(labels[y]):
            r = find(int(labels[y, x]))
            b = boxes.get(r)
            if b is None:
                boxes[r] = [y, y + 1, int(x), int(x) + 1, 1]
            else:
                b[1] = y + 1
                b[2] = min(b[2], int(x))
                b[3] = max(b[3], int(x) + 1)
                b[4] += 1
    out = []
    for y0_, y1_, xa, xb, area in boxes.values():
        if area < MIN_AREA or (y1_ - y0_) < MIN_HEIGHT:
            continue
        out.append({"y0": y0_ + y0, "y1": y1_ + y0, "x0": xa + x0, "x1": xb + x0, "area": area})
    out.sort(key=lambda c: ((c["y0"] + c["y1"]) / 2, c["x0"]))
    return out


def group(cs, dy=GROUP_DY):
    """Components to numbers. A new number starts when the hand goes back to the
    left of the cell, or when the y centre steps more than `dy`."""
    rows = []
    for c in cs:
        cy = (c["y0"] + c["y1"]) / 2
        if rows and cy - rows[-1]["cy"] <= dy and c["x0"] >= rows[-1]["parts"][-1]["x0"]:
            r = rows[-1]
            r["parts"].append(c)
            r["y0"] = min(r["y0"], c["y0"])
            r["y1"] = max(r["y1"], c["y1"])
            r["x0"] = min(r["x0"], c["x0"])
            r["x1"] = max(r["x1"], c["x1"])
            r["cy"] = sum((p["y0"] + p["y1"]) / 2 for p in r["parts"]) / len(r["parts"])
        else:
            rows.append({"parts": [c], "y0": c["y0"], "y1": c["y1"],
                         "x0": c["x0"], "x1": c["x1"], "cy": cy})
    return rows


def anchors(groups_by_column, tol=30):
    """Lines a written industry column puts beyond argument.

    An entry in commerce, manufactures or learned professions coincides in y with
    the TOTAL group of its own line. That coincidence needs no threshold and no
    grid, so the lines it names are the committed part of the row grid.
    """
    out = []
    for t in groups_by_column.get("total", []):
        hits = []
        for name in ("commerce", "manufactures_and_trades",
                     "learned_professions_and_engineers", "agriculture", "mining",
                     "navigation_ocean", "navigation_canals_lakes_rivers"):
            for g in groups_by_column.get(name, []):
                if abs(g["cy"] - t["cy"]) <= tol:
                    hits.append({"column": name, "cy": round(g["cy"], 1),
                                 "box": [g["x0"], g["y0"], g["x1"], g["y1"]]})
        if hits:
            out.append({"total_cy": round(t["cy"], 1),
                        "total_box": [t["x0"], t["y0"], t["x1"], t["y1"]],
                        "coincident": hits})
    return out


def read(path, cover=RULE_COVER):
    a = load(path)
    y0, y1 = horizontal_rules(a, int(a.shape[1] * 0.07), int(a.shape[1] * 0.30))
    rules = vertical_rules(a, y0, y1, cover=cover)
    cont = rule_continuity(a, y0, y1, rules)
    bounds, pitch = locate_columns(rules, cont)
    dropped = bounds.pop("_total_left_rule_dropped", None)
    comps, groups = {}, {}
    for name, (cx0, cx1) in bounds.items():
        ix0, ix1 = cx0 + RULE_CLEARANCE, cx1 - RULE_CLEARANCE
        m = _close(ink_mask(a, ix0, y0, ix1, y1))
        comps[name] = [c for c in components(m, ix0, y0)
                       if (c["y1"] - c["y0"]) <= MAX_ASPECT * max(c["x1"] - c["x0"], 1)]
        groups[name] = group(comps[name])
    out = {
        "image": os.path.relpath(path, REPO),
        "image_size": [int(a.shape[1]), int(a.shape[0])],
        "body_between_rules": [int(y0), int(y1)],
        "vertical_rules": rules,
        "column_pitch_px": int(pitch),
        "column_bounds": {k: [int(v[0]), int(v[1])] for k, v in bounds.items()},
        "rule_continuity": dict(zip((str(r) for r in rules), cont)),
        "rule_cover": cover,
        "pen_stroke_rule_dropped": (None if dropped is None else {
            "x": int(dropped[0]),
            "why": "reported as a vertical rule by coverage, but its longest UNBROKEN "
                   "dark run is under half that of both rules bracketing it: a stack of "
                   "the enumerator's family totals, not a printed line. Dropping it is "
                   "what makes the TOTAL cell measure 2-4 industry pitches, as it does "
                   "on every other sheet. See locate_columns().",
        }),
        "method": {
            "ink": f"local background = {BACKGROUND_BLUR}px Gaussian of the crop; "
                   f"ink = {INK_BELOW_BACKGROUND} grey levels darker",
            "components": f"8-connected after 5x5 closing, area>={MIN_AREA}, "
                          f"height>={MIN_HEIGHT}, height/width<={MAX_ASPECT}",
            "grouping": f"one number while dy<={GROUP_DY} and x does not step back",
            "digits": "NOT READ — this tool measures boxes, a human reads the digit",
        },
        "columns": {},
    }
    for name in bounds:
        gs = groups[name]
        out["columns"][name] = {
            "components": len(comps[name]),
            "groups": len(gs),
            "group_boxes": [[g["x0"], g["y0"], g["x1"], g["y1"], len(g["parts"])] for g in gs],
            "group_centres": [round(g["cy"], 1) for g in gs],
        }
    out["group_count_sensitivity"] = {
        str(d): len(group(comps["total"], d)) for d in (35, 45, 55, 65, 75)
    }
    out["anchored_lines"] = anchors(groups)
    return out


def self_test():
    """The assertions this tool would fail if its own machinery broke."""
    np = _np()
    Image, _ = _pil()
    # components(): what the 5x5 closing must and must not join, and what the
    # speck filter must drop. The gap that matters is 5 px: a closing of radius 2
    # bridges 4 and leaves 5 alone, which is why two adjacent pen strokes 5 px
    # apart stay two numbers and a stroke a scan broke by 2 px becomes one.
    m = np.zeros((80, 80), dtype=bool)
    m[5:25, 5:12] = True                    # a tall stroke
    m[5:25, 17:24] = True                   # a second, 5 px clear of it
    m[34:37, 40:43] = True                  # a speck: too small, must be dropped
    m[45:58, 50:56] = True
    m[60:72, 50:56] = True                  # broken by 2 px: closing must join it
    cs = components(_close(m), 0, 0)
    assert len(cs) == 3, [len(cs), cs]
    assert cs[-1]["y1"] - cs[-1]["y0"] > 25, cs[-1]   # the two halves are one glyph
    # group(): x stepping back starts a new number even inside dy.
    cs = [{"y0": 0, "y1": 30, "x0": 100, "x1": 120, "area": 200},
          {"y0": 10, "y1": 40, "x0": 118, "x1": 140, "area": 200},
          {"y0": 30, "y1": 60, "x0": 90, "x1": 110, "area": 200}]
    gs = group(cs)
    assert [len(g["parts"]) for g in gs] == [2, 1], [len(g["parts"]) for g in gs]
    # determinism: the same mask twice is the same answer.
    assert components(_close(m), 0, 0) == components(_close(m), 0, 0)
    print("self-test ok: components, grouping, x-step-back rule, determinism")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("sheet", nargs="?", help="familysearch id, e.g. 33S7-9YYJ-5V")
    ap.add_argument("--json", help="write the inventory here")
    ap.add_argument("--cover", type=float, default=RULE_COVER,
                    help="fraction of body rows a printed rule must darken "
                         f"(default {RULE_COVER}; 33S7-9YYJ-6H is a pale exposure "
                         "and needs 0.50)")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        self_test()
        return
    if not args.sheet:
        ap.error("give a familysearch id, or --self-test")
    path = args.sheet if os.path.exists(args.sheet) else os.path.join(DEPOSIT, args.sheet + ".jpg")
    if not os.path.exists(path):
        sys.exit(f"no such image: {path}")
    out = read(path, cover=args.cover)
    if args.json:
        with open(args.json, "w") as fh:
            json.dump(out, fh, indent=1, sort_keys=True)
            fh.write("\n")
    print(f"{out['image']}  {out['image_size'][0]}x{out['image_size'][1]}")
    print(f"body between horizontal rules: y {out['body_between_rules'][0]}-{out['body_between_rules'][1]}")
    print(f"column pitch {out['column_pitch_px']} px; {len(out['vertical_rules'])} vertical rules")
    for name, (bx0, bx1) in out["column_bounds"].items():
        c = out["columns"][name]
        print(f"  {name:38s} x {bx0}-{bx1}  components {c['components']:3d}  numbers {c['groups']:3d}")
    print(f"TOTAL group count by dy threshold: {out['group_count_sensitivity']}")
    print(f"lines anchored by a coincident industry entry: {len(out['anchored_lines'])}")


if __name__ == "__main__":
    main()
