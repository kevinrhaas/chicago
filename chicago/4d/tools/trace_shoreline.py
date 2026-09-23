#!/usr/bin/env python3
"""Trace the 1834 lake shore, the harbour reach and the sand bar off Wright 1834.

The eastern companion to `tools/trace_river.py`. That tool traces the forks; this
one traces the mile of water between the forks box and Lake Michigan — the main
stem past Fort Dearborn, the 1834 harbour cut between its piers, the decaying old
southward channel, the sand bar it runs behind, and the lake shore itself.

    python3 tools/trace_shoreline.py            re-trace and write the GeoJSON
    python3 tools/trace_shoreline.py --check    re-trace and diff against committed
    python3 tools/trace_shoreline.py --debug    also write a PNG overlay of the trace

Since T-0799 the trace SPLICES: the committed walk stands wherever the fresh one
agrees with it inside `SPLICE_TOL_M`, because the ground is carved from this file
and a kilometre of re-simplified vertices would move it under every consumer for
no better reading. `--check` therefore asserts that the committed file is a fixed
point of this tool — that the fresh walk still finds it everywhere, and that the
reaches the old window cut off are the ones the tool would splice on today. A
vertex moved by hand further than the tolerance still shows up as a DIFF.
`--retrace-all` publishes the fresh walk everywhere; it moves the ground and so
belongs with a re-bake, not with a trace.

Why this is a separate window rather than a bigger one
------------------------------------------------------
The forks trace works at a local block percentile, which is what lets it find a
70 m channel threading a town of coloured ward washes. Lake Michigan is drawn as
a wash band a couple of hundred metres wide, and against a *local* background a
band that wide is its own paper: the interior of the lake reads as unshaded and
only its two edges come out. So this trace measures "darker than paper" against
the whole window instead (`bg_block` larger than the region), which is the right
answer here and the wrong answer at the forks. Two windows, two settings, one
affine — rather than one window that does neither job well.

What comes out, and what deliberately does not
----------------------------------------------
The traced water is one connected body: main stem, cut, old channel, lake. Its
boundary is split into runs and each run is claimed by a hand-placed anchor,
exactly as the forks trace names its bank runs. Two runs are named:

    south_shore_harbor_reach   south bank of the main stem east of the forks box,
                               the Fort Dearborn reservation's lake shore, the
                               west bank of the old southward channel, and the
                               lake shore on to the foot of the sheet
    north_shore_harbor_reach   north bank of the main stem, the inner face of the
                               north pier, and the lake shore north of the harbour

The sand bar comes out as what it is on the map: a hole in the water, traced as a
closed island ring and carried as the water polygon's interior ring.

**One run is found and dropped on purpose** — the whole east side of the body,
3,936 m of it. Out in the lake the wash band simply stops, and that stopping line
is where the draughtsman lifted the brush: not a shore, not a depth contour, not
anything. It is reported on every run, with its extent, and written to no file.
Nothing east of the traced shore is a claim about the lake.

What tells the two apart is the DRAWING, not the window (T-0799). Until that
ticket the window's own east edge fell inside the wash and the runs were separated
by it — the program deciding where a shore ended. The window now stands clear of
the wash on every side but the forks junction, the whole east edge arrives as one
closed ring, and `split_ink` divides it on whether Wright drew a line under it.
See `line_mask` for why "a line" has to mean a ridge and not merely a dark pixel.

Needs numpy, scipy, Pillow. Like the forks trace and the datum re-derivation this
is a deliberate, occasional re-run and is not part of tools/check.sh; it degrades
to a clear skip when the dependencies or the network are missing.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import math
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

OUT_DIR = ROOT / "data" / "terrain" / "epochs" / "e1834_harbor_cut"
OUT = OUT_DIR / "shoreline.geojson"

IIIF = "https://iiif.digitalcommonwealth.org/iiif/2/commonwealth:js957744g"

# The region of the BPL master scan (resource space, 4204 x 5166) this trace works
# in: the WHOLE SHEET east of the forks box, margin to margin (T-0799).
#
# It used to be a 1802 x 1500 box around the harbour, and three of the four things
# that box did were damage. Its east edge fell INSIDE the lake wash, so the traced
# water ended on a straight line of window and the harbour polygon published it as
# its own eastern boundary; its south edge cut the shore off at local N -589, a
# kilometre short of where Wright draws it; its north edge cut the shore off again
# above the harbour. The owner asked for the east edge whole and in one run.
#
# The window now runs from the east edge of the forks box (local E +314, the splice
# with tools/trace_river.py, and the ONE window edge the trace still carries) out
# past the far side of the lake wash, and from above the sheet's top neat line to
# below the point where the wash stops short of the bottom one. Nothing the trace
# publishes ends on a window edge except that junction: the wash band closes on
# itself inside the window, which is what lets the whole east edge come out as one
# boundary. Local extent: E +314 .. +2043, N -2069 .. +1096.
REGION = (1878, 150, 2222, 4800)

# Hand-placed, like the forks trace's seeds, and the only numbers here read off
# the scan by eye. Seeds select the water; anchors claim a boundary run for a
# name. Both are resource pixels.
SEEDS = {
    "main_stem": (2400, 1700),          # open channel below the Kinzie Addition
    "old_south_channel": (3220, 2060),  # behind the bar, level with the arrow
    "lake": (3600, 1760),               # open lake east of the bar
}
ANCHORS = {
    "south_shore_harbor_reach": (3180, 1940),   # inside the reservation, by its lake shore
    "north_shore_harbor_reach": (2830, 1470),   # north bank opposite the fort
}
ANCHOR_MAX_PX = 60          # a claim further off than this is not a claim

# How far the fresh walk may stand from a committed vertex and still be the same line.
#
# It is not a taste: the SAND BAR measures it. The bar is a closed island lying wholly
# inside the old window, it never touched a window edge, and nothing in T-0799 is about
# it — so every one of its committed vertices ought to survive, and how far the worst of
# them stands from the fresh walk IS the noise floor of re-walking the same wash against
# a different background percentile. Measured: median 0.63 m, p95 2.21 m, worst 6.32 m.
# The tolerance is set just clear of that worst vertex. It is a third of this trace's own
# declared uncertainty and about ten map pixels — far enough to absorb the percentile
# shift, close enough that a bank read differently cannot hide inside it.
SPLICE_TOL_M = 7.0

# Where the map's OWN LETTERING has to be read as lettering.
#
# Wright letters "CHICAGO RIVER" in outline display capitals straight across the
# main stem. The interior of an outline capital is unwashed paper, so every one
# of those letters comes out of the wash test as dry ground standing in the
# channel. That is already handled where a letter falls wholly inside the water:
# it becomes a HOLE in the water body, and `island_min_px` fills it back in — the
# run reports "2 filled as lettering" for exactly this reason.
#
# The G of CHICAGO is the one that does not. A brown foxing stain runs south from
# it to the drawn bank line, so the letter, the stain and the south bank are ONE
# connected dry region: not a hole, never filled, and the boundary walk goes round
# all three. What came out was a rounded 60 m headland pushing into the channel at
# Clark Street, leaving about 12 m of water between it and the north bank. Wright
# draws nothing of the kind — his two bank lines run near-parallel through this
# reach — and the artefact is measurable from the other end as well: the traced
# south bank sat 79.6 m north of the recorded South Water Street building faces at
# Clark against 18.7 m at Dearborn, a 60 m swing over four blocks
# (docs/RESEARCH/chicago_american_office.md § 3).
#
# So this is a declared window, in resource pixels like SEEDS and ANCHORS, inside
# which a dry span with CHANNEL AT BOTH ENDS OF ITS OWN ROW is read as a gap in
# the drawing rather than as land. The river runs west-east across this window, so
# "water to my left and water to my right" is what a reader uses to see through
# the type; the rule cannot leak past a bank, because a row south of the bank line
# has no water on its landward side to bracket it. It fills nothing anywhere else:
# every box must bite, or the run dies rather than quietly trusting a constant
# that has rotted.
#
# It is a correction to a KNOWN DEFECT OF THE SHEET's condition and of its
# lettering, not a redrawing of the waterline: the waterline inside the box is
# still Wright's own wash, reconnected across his own type.
LETTERING = {
    # x0, y0, x1, y1 — the G of CHICAGO and the foxing stain under it.
    # Local ENU E +524 .. +628, N +20 .. +87.
    #
    # The west edge moved 8 px west of where it was drawn (2188) when T-0799 opened
    # the window: the segmentation shifts by a pixel or two when the background
    # percentile is measured over a different window, and at 2188 the south bank's
    # own wiggle crossed the box TWICE instead of once, which `splice_lettering`
    # refuses. 2180 is the nearest edge that puts the whole wiggle inside the box.
    # It recovers 8,142 px where 2188 recovered 8,018 — the same defect, the same
    # correction, a box drawn eight pixels clear of its own boundary.
    "chicago_g": (2180, 1710, 2328, 1800),
}

PARAMS = dict(
    bg_block=1600, bg_pct=88,         # paper luminance, measured across the window
    hue_block=280, hue_pct=40,
    dark_lo=20, dark_hi=78,
    hue_tol=11,
    speckle_px=2000,                  # street hatching and type, dropped before closing
    pre_open_r=3,
    close_r=30, open_r=6,
    island_min_px=20000,              # smaller holes are lettering inside the channel
    simplify_px=2.5,
    # --- what is a shore and what is only the end of the brush (T-0799) ---
    ink_lum=110,                      # tools/trace_river.py's own threshold for drawn line
    ink_ridge_r=9,                    # ...and a line has to be a ridge, not a step: see line_mask
    ink_ridge=70,
    ink_near_px=12,                   # a boundary vertex this close to ink is ON a drawn line
    ink_bridge_px=140,                # a shorter dry gap is a break in the line, not its end
    ink_spur_px=220,                  # a shorter inked stretch out in the lake is lettering
)


def die(msg: str, code: int = 2):
    print(msg)
    raise SystemExit(code)


def fetch_region(cache: Path):
    x, y, w, h = REGION
    url = f"{IIIF}/{x},{y},{w},{h}/full/0/default.jpg"
    if cache.exists():
        raw = cache.read_bytes()
    else:
        print(f"fetching {url}")
        with urllib.request.urlopen(url, timeout=180) as r:  # noqa: S310
            raw = r.read()
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_bytes(raw)
    return raw, hashlib.sha256(raw).hexdigest()


def close_lettering(water, np):
    """Read the map's display capitals as lettering inside the declared windows.

    Within each LETTERING box a dry pixel becomes water when the same ROW carries
    water on both sides of it inside that box. See the LETTERING comment for why
    the rule is row-wise and why it cannot walk past a bank. Returns the number of
    pixels each box recovered, so the caller can refuse to run on a box that has
    stopped biting.
    """
    recovered = {}
    for name, (x0, y0, x1, y1) in LETTERING.items():
        sl = (slice(y0 - REGION[1], y1 - REGION[1]), slice(x0 - REGION[0], x1 - REGION[0]))
        box = water[sl]
        if box.size == 0:
            die(f"lettering box {name} falls outside REGION — one of the two moved")
        left = np.maximum.accumulate(box, axis=1)
        right = np.maximum.accumulate(box[:, ::-1], axis=1)[:, ::-1]
        bridged = left & right
        recovered[name] = int(bridged.sum() - box.sum())
        water[sl] = bridged
    return recovered


def _box_run(ring_px, box):
    """The contiguous runs of ring vertices inside `box`, each as an index list."""
    x0, y0, x1, y1 = box
    inside = [x0 - REGION[0] <= px <= x1 - REGION[0]
              and y0 - REGION[1] <= py <= y1 - REGION[1] for px, py in ring_px]
    runs, cur = [], []
    for i, v in enumerate(inside):
        if v:
            cur.append(i)
        elif cur:
            runs.append(cur)
            cur = []
    if cur:
        runs.append(cur)
    if len(runs) > 1 and runs[0][0] == 0 and runs[-1][-1] == len(ring_px) - 1:
        runs = [runs[-1] + runs[0]] + runs[1:-1]     # the run wrapped the seam
    return runs


def _point_to_line(p, line):
    best = 1e18
    for i in range(len(line) - 1):
        (x1, y1), (x2, y2) = line[i], line[i + 1]
        dx, dy = x2 - x1, y2 - y1
        L = dx * dx + dy * dy
        t = 0.0 if L == 0 else max(0.0, min(1.0, ((p[0] - x1) * dx + (p[1] - y1) * dy) / L))
        best = min(best, math.hypot(p[0] - x1 - t * dx, p[1] - y1 - t * dy))
    return best


def _nearest_vertex(p, line):
    return min(range(len(line)), key=lambda i: math.dist(p, line[i]))


def splice_committed(fresh, committed, closed_ring, tol, what):
    """Publish the COMMITTED walk wherever it is still the answer, and the fresh one
    only where the window used to be.

    The blast-radius argument `splice_lettering` makes for one lettering box is the
    argument for this whole ticket. Opening the window to the sheet (T-0799) moves the
    background percentile the wash test measures against, so the segmentation shifts by
    a pixel or two everywhere — a median 0.8 m on the south shore, 1.3 m on the north,
    against a declared uncertainty of 20 m. Nothing in that is a better reading. But the
    ground is carved from this file, and republishing a whole kilometre of re-simplified
    vertices would move the committed heightfield under every consumer of it for no gain
    at all, while making it impossible to show that only the east edge changed. The
    terrain re-bake belongs to T-0800; this piece is the trace.

    So the committed walk stands wherever the fresh one agrees with it inside `tol`, and
    the fresh walk is spliced onto the ends that used to run along the window edge. Both
    come from the same method on the same sheet, and the splice ASSERTS the agreement
    rather than assuming it: a committed stretch the fresh trace no longer finds is a
    finding, and this dies instead of quietly averaging the two.
    """
    committed = list(committed)
    near = [_point_to_line(p, fresh) <= tol for p in committed]
    if closed_ring:
        if all(near):
            print(f"   splice {what}: all {len(committed)} committed vertices stand")
            return committed
        k = near.index(False)
        committed, near = committed[k:] + committed[:k], near[k:] + near[:k]
    n = len(committed)
    span, start = None, 0
    while start < n:
        if not near[start]:
            start += 1
            continue
        end = start
        while end + 1 < n and near[end + 1]:
            end += 1
        if span is None or end - start > span[1] - span[0]:
            span = (start, end)
        start = end + 1
    if span is None:
        die(f"{what}: the fresh trace agrees with NO committed vertex inside {tol} m — "
            f"this is not a window being opened, it is a different line; read the debug "
            f"overlay before touching the tolerance")
    a, b = span
    kept = committed[a:b + 1]
    ja, jb = _nearest_vertex(kept[0], fresh), _nearest_vertex(kept[-1], fresh)
    if closed_ring:
        tail = fresh[jb + 1:] + fresh[:ja] if jb >= ja else fresh[jb + 1:ja]
        out, fresh_n = kept + tail, len(tail)
    else:
        if not ja < jb:
            die(f"{what}: the committed walk and the fresh one run in opposite "
                f"directions ({ja} then {jb}) — the splice cannot join them end to end")
        out, fresh_n = fresh[:ja] + kept + fresh[jb + 1:], ja + len(fresh) - jb - 1
    print(f"   splice {what}: {len(kept)} of {n} committed vertices stand, "
          f"{n - len(kept)} replaced by {fresh_n} fresh ones carrying the reaches the "
          f"old window cut off")
    return out


def splice_lettering(ring_base, ring_fixed):
    """Carry each lettering box's corrected boundary into the UNCORRECTED ring.

    Why not simply publish the corrected ring. Douglas-Peucker is not a local
    operation: `simplify_ring` halves the ring by INDEX, so removing a hundred
    boundary pixels at Clark Street re-splits the whole walk and every vertex
    downstream lands a pixel or two elsewhere. Harmless in itself — it is the same
    line, resampled, at a tenth of this trace's own +/-20 m — but it destroys the
    one thing a correction like this has to be able to show: that NOTHING outside
    the reach being corrected moved. Measured on the heightfield, that churn moved
    5,037 cells by up to 0.30 m and floated 49 of them across the waterline, all of
    them hundreds of metres from the defect.

    So the boxes are the blast radius, by construction. Outside them every vertex
    is the one the uncorrected trace produced, byte for byte; inside them the
    corrected walk replaces it. Both rings come from the same segmentation, the
    masks differ only inside the boxes, and the two agree outside to the
    simplifier's own tolerance — the splice asserts that rather than assuming it.
    """
    ring = list(ring_base)
    for name, box in sorted(LETTERING.items(), key=lambda kv: -kv[1][0]):
        base_runs = _box_run(ring, box)
        fix_runs = _box_run(ring_fixed, box)
        if len(base_runs) != 1 or len(fix_runs) != 1:
            die(f"lettering box {name} is crossed by the traced boundary "
                f"{len(base_runs)}/{len(fix_runs)} times, not once — the box now spans "
                f"more of the water body than the defect it was drawn around; redraw it "
                f"against the scan rather than splicing an ambiguous run")
        b, f = base_runs[0], fix_runs[0]
        ring[b[0]:b[-1] + 1] = [ring_fixed[i] for i in f]
    return ring


def split_runs(ring_px, margin=3):
    """Split a traced ring into the runs that are real waterline and the runs that
    are only the edge of the traced window. Pixel space, for the same reason the
    forks trace does it in pixel space: the window is axis-aligned there and the
    local ENU frame is rotated about 1.2 degrees off it."""
    w, h = REGION[2], REGION[3]
    on_edge = [px <= margin or py <= margin or px >= w - 1 - margin or py >= h - 1 - margin
               for px, py in ring_px]
    m = len(ring_px)
    if not any(on_edge):
        return [list(range(m))]
    start = next(i for i in range(m) if on_edge[i])
    runs, cur = [], []
    for k in range(m + 1):
        i = (start + k) % m
        if on_edge[i]:
            if len(cur) > 2:
                runs.append([(cur[0] - 1) % m] + cur + [i])
            cur = []
        else:
            cur.append(i)
    return runs


def line_mask(rgb, np, ndi, tr):
    """Wright's DRAWN LINE — dark, and dark on both sides of itself.

    `tools/trace_river.py`'s ink test is a luminance threshold, and at the forks that
    is enough: everything that dark in that window is pen. Out at the lake it is not.
    A wash laid with a brush pools its pigment at the edge it dries against, and along
    the bottom third of the east edge that pooled band and the brush-stroke marks in
    it come within a few units of the ink threshold — while being, on the sheet, the
    opposite of a line: the place where Wright stopped drawing.

    A pen line is a RIDGE. It is darker than what lies on either side of it, so a grey
    closing at a radius wider than the line fills it in and the black top-hat is large.
    A wash edge is a STEP — dark water on one side, pale paper on the other — and a
    closing leaves a step exactly where it found it, so its top-hat is small. Measured
    on this sheet: the inked south shore reads 138-142 against a pooled east edge at
    40-64 and open lake at 12.

    Both tests have to pass. The luminance one keeps the project's own meaning of ink;
    the ridge one is what tells a line from the end of a brush.
    """
    a = rgb.astype(np.float32)
    lum = 0.299 * a[..., 0] + 0.587 * a[..., 1] + 0.114 * a[..., 2]
    ridge = ndi.grey_closing(lum, footprint=tr.disk(PARAMS["ink_ridge_r"], np)) - lum
    return (lum < PARAMS["ink_lum"]) & (ridge > PARAMS["ink_ridge"])


def _run_length(pts):
    return sum(math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1))


def split_ink(idx, ring_px, d_ink):
    """Divide one boundary run into the stretches Wright INKED and the stretches he
    did not, and return them in order as (is_shore, indices).

    Why this rule exists. Until T-0799 the trace worked in a box whose east edge fell
    inside the lake wash, and the runs it published were separated by that edge: the
    window told the trace where a shore stopped. That is exactly backwards — the
    window is a decision of this program's, not of Wright's — and it is what put a
    straight line of window into the harbour polygon and stopped the south shore a
    kilometre short of the sheet's own margin.

    With the window opened to the whole sheet the wash band closes on itself, so the
    whole east edge arrives as ONE ring with no edge in it, and the trace has to tell
    the two halves of that ring apart on the drawing's own evidence. It does it with
    the ink. Wright draws a shore: a pen line under the edge of the wash, the same
    line `tools/measure_water_outliers.py --vs-ink` measures the forks bank against
    and finds a median 0.70 m away. He does not draw the far side of the wash. Out in
    the lake the band simply stops where he lifted the brush, and there is no line
    there at all — which is why that edge was already being found, reported and
    dropped before this window ever opened.

    So: a vertex within `ink_near_px` of ink is on a drawn line. A dry gap shorter
    than `ink_bridge_px` between two inked stretches is a break in the line — a stain,
    a fold, a letter — and is bridged. An inked stretch shorter than `ink_spur_px`
    standing in a dry one is the trace brushing past the sheet's lettering (SAND-BAR,
    LAKE MICHIGAN, the scale bar) and is not a shore. Both thresholds are in map
    pixels and both are reported on every run.
    """
    pts = [ring_px[i] for i in idx]
    near = [bool(d_ink[py, px] <= PARAMS["ink_near_px"]) for px, py in pts]

    def segments(flags):
        out, start = [], 0
        for i in range(1, len(flags) + 1):
            if i == len(flags) or flags[i] != flags[i - 1]:
                out.append((flags[start], start, i - 1))
                start = i
        return out

    for state, limit in ((False, "ink_bridge_px"), (True, "ink_spur_px")):
        segs = segments(near)
        for k, (kind, a, b) in enumerate(segs):
            if kind is not state or k == 0 or k == len(segs) - 1:
                continue                      # only a stretch with drawing on BOTH sides
            if _run_length(pts[a:b + 1]) < PARAMS[limit]:
                for i in range(a, b + 1):
                    near[i] = not state
    return [(kind, idx[a:b + 1]) for kind, a, b in segments(near)]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="diff against the committed GeoJSON")
    ap.add_argument("--debug", action="store_true", help="write a PNG overlay of the trace")
    ap.add_argument("--retrace-all", action="store_true",
                    help="publish the fresh walk everywhere, committed vertices and all "
                         "— the terrain is carved from this file, so this moves the "
                         "ground and belongs with a re-bake, not with a trace")
    ap.add_argument("--cache", default=str(Path("/tmp") / "wright_1834_east_edge_region.jpg"))
    args = ap.parse_args()

    try:
        import numpy as np
        from PIL import Image
        from scipy import ndimage as ndi
    except ImportError as e:
        die(f"SKIP: {e.name} not installed (pip install numpy scipy pillow); "
            f"shoreline trace not run", 0)

    import trace_river as tr                                    # noqa: PLC0415

    datum = json.loads((ROOT / "data" / "datum.json").read_text())
    if not datum.get("verified"):
        die("REFUSING: data/datum.json is not verified.")
    o_e, o_n = datum["origin_utm_e"], datum["origin_utm_n"]

    coef, rms, n_gcp = tr.affine_from_gcps()
    to_utm = tr.make_to_utm(coef)
    cell_m = 0.5 * (math.hypot(coef[0], coef[3]) + math.hypot(coef[1], coef[4]))
    print(f"affine refit from {n_gcp} GCPs, RMS {rms:.1f} m; {cell_m:.4f} m per map pixel")

    raw, sha = fetch_region(Path(args.cache))
    rgb = np.asarray(Image.open(io.BytesIO(raw)).convert("RGB"))
    print(f"region {REGION} sha256 {sha[:16]}...  {rgb.shape[1]}x{rgb.shape[0]} px")

    # --- segmentation -------------------------------------------------------
    # Same wash test as the forks, read against the window rather than a block.
    tr.PARAMS.update({k: PARAMS[k] for k in
                      ("bg_block", "bg_pct", "hue_block", "hue_pct",
                       "dark_lo", "dark_hi", "hue_tol")})
    wash = tr.wash_mask(rgb, np)
    lab, n = ndi.label(wash)
    sizes = ndi.sum_labels(np.ones_like(lab, np.float32), lab, np.arange(1, n + 1))
    wash = np.isin(lab, 1 + np.flatnonzero(sizes >= PARAMS["speckle_px"]))
    wash = ndi.binary_opening(wash, tr.disk(PARAMS["pre_open_r"], np))

    r = PARAMS["close_r"]
    m = tr._erode(ndi.binary_dilation(wash, tr.disk(r, np)), r, np, ndi)
    m = ndi.binary_dilation(tr._erode(m, PARAMS["open_r"], np, ndi),
                            tr.disk(PARAMS["open_r"], np))
    lab2, _ = ndi.label(m)
    keep = set()
    for name, (sx, sy) in SEEDS.items():
        v = int(lab2[sy - REGION[1], sx - REGION[0]])
        if v == 0:
            die(f"seed {name} at {sx},{sy} did not land on water — the segmentation "
                f"moved under it; fix the seed or the parameters, do not widen the "
                f"tolerance until it sticks")
        keep.add(v)
    water_uncorrected = np.isin(lab2, sorted(keep))
    water = water_uncorrected.copy()

    # The map's own type, read as type. Before the holes are counted, because a
    # letter that leaks to the bank through a stain is not a hole and would never
    # reach the island rule at all — which is the whole reason this step exists.
    recovered = close_lettering(water, np)
    for name, px in recovered.items():
        if px <= 0:
            die(f"lettering box {name} recovered no pixels — the segmentation or the "
                f"box has moved. Fix the box against the scan; do not delete the check "
                f"and do not widen it until something happens")
        print(f"   lettering {name}: {px:,} px read as type rather than as land "
              f"({px * cell_m * cell_m:,.0f} m2)")

    # Islands: a hole in the water body is land the water goes round. The sand bar
    # is one. The letters of "RIVER" drawn across the channel are not, so anything
    # under the threshold is filled back in rather than published as an island.
    filled = ndi.binary_fill_holes(water)
    holes = filled & ~water
    hl, hn = ndi.label(holes)
    hs = ndi.sum_labels(np.ones_like(hl, np.float32), hl, np.arange(1, hn + 1))
    island_ids = 1 + np.flatnonzero(hs >= PARAMS["island_min_px"])
    islands = np.isin(hl, island_ids)
    water = filled & ~islands
    print(f"water {int(water.sum()):,} px of {water.size:,}; {hn} hole(s), "
          f"{len(island_ids)} island(s) kept, {hn - len(island_ids)} filled as lettering")
    if len(island_ids) != 1:
        die(f"expected exactly one island (the sand bar), found {len(island_ids)}")

    def px_to_local(pts):
        out = []
        for px, py in pts:
            E, N = to_utm(px + REGION[0], py + REGION[1])
            out.append((round(E - o_e, 2), round(N - o_n, 2)))
        return out

    def length_m(line):
        return sum(math.dist(line[i], line[i + 1]) for i in range(len(line) - 1))

    # --- the shore ----------------------------------------------------------
    # Two walks of the same segmentation — the mask as it comes off the sheet, and
    # the mask with the display capitals read as type — spliced so the correction
    # cannot move a vertex outside its declared box. See `splice_lettering`.
    ring_px = splice_lettering(
        tr.simplify_ring(tr.trace_outer(water_uncorrected, np), PARAMS["simplify_px"]),
        tr.simplify_ring(tr.trace_outer(water, np), PARAMS["simplify_px"]))
    # The window no longer tells the trace where a shore stops: the drawing does.
    ink = line_mask(rgb, np, ndi, tr)
    d_ink = ndi.distance_transform_edt(~ink)
    runs_px, shore_flag = [], []
    for idx in split_runs(ring_px):
        for is_shore, part in split_ink(idx, ring_px, d_ink):
            runs_px.append(part)
            shore_flag.append(is_shore)
    print(f"boundary: {len(runs_px)} run(s) — "
          f"{sum(shore_flag)} on Wright's ink, {len(runs_px) - sum(shore_flag)} where the "
          f"wash stops and he drew nothing")
    named, dropped = {}, []
    for is_shore, idx in zip(shore_flag, runs_px):
        pts = [ring_px[i] for i in idx]
        best, bestd = None, 1e18
        for key, (ax, ay) in ANCHORS.items():
            d = min(math.hypot(px + REGION[0] - ax, py + REGION[1] - ay) for px, py in pts)
            if d < bestd:
                best, bestd = key, d
        line = px_to_local(pts)
        ink_m = sorted(float(d_ink[py, px]) * cell_m for px, py in pts)
        if not is_shore or bestd > ANCHOR_MAX_PX or best in named:
            dropped.append((line, round(bestd * cell_m, 1), is_shore))
            continue
        named[best] = (line, round(bestd * cell_m, 1),
                       round(ink_m[len(ink_m) // 2], 2),
                       round(ink_m[int(0.9 * (len(ink_m) - 1))], 2))
    for key in ANCHORS:
        if key not in named:
            die(f"no boundary run came within {ANCHOR_MAX_PX} px of the {key} anchor")
    for line, d, is_shore in dropped:
        why = ("no anchor claims it" if is_shore else
               "no drawn line under it — the wash stops there and nothing else does")
        print(f"   dropped run: {len(line)} pts, {length_m(line):.0f} m, "
              f"E [{min(p[0] for p in line):.0f},{max(p[0] for p in line):.0f}] "
              f"N [{min(p[1] for p in line):.0f},{max(p[1] for p in line):.0f}], "
              f"nearest anchor {d} m away — {why}, so it is not written")

    bar_px = tr.simplify_ring(tr.trace_outer(islands, np), PARAMS["simplify_px"])
    bar = px_to_local(bar_px)
    print("shore runs: " + ", ".join(
        f"{k} {len(v[0])} pts / {length_m(v[0]):.0f} m, {v[2]} m from the drawn line "
        f"(p90 {v[3]} m)" for k, v in named.items()))
    print(f"sand bar ring {len(bar)} vertices, {length_m(bar + [bar[0]]):.0f} m perimeter")

    water_ring = px_to_local(ring_px)

    # --- the committed walk stands where the fresh one agrees with it ------------
    committed = {}
    if OUT.exists():
        for feature in json.loads(OUT.read_text())["features"]:
            geom = feature["geometry"]
            pts = (geom["coordinates"][0][:-1] if geom["type"] == "Polygon"
                   else geom["coordinates"])
            committed[feature["id"]] = [(round(x - o_e, 2), round(y - o_n, 2))
                                        for x, y in pts]
    if committed and not args.retrace_all:
        water_ring = splice_committed(water_ring, committed["harbor_reach_water"],
                                      True, SPLICE_TOL_M, "the water boundary")
        bar = splice_committed(bar, committed["sand_bar_1834"],
                               True, SPLICE_TOL_M, "the sand bar")
        for key in list(named):
            line, anchor_m, ink_med, ink_p90 = named[key]
            named[key] = (splice_committed(line, committed[key], False,
                                           SPLICE_TOL_M, key),
                          anchor_m, ink_med, ink_p90)
        print("shore runs, spliced: " + ", ".join(
            f"{k} {len(v[0])} pts / {length_m(v[0]):.0f} m" for k, v in named.items()))

    def closed(ring):
        return [[e + o_e, n + o_n] for e, n in ring] + [[ring[0][0] + o_e, ring[0][1] + o_n]]

    prov = {
        "traced_from": "wright_1834",
        "method": "grey wash segmentation of the BPL master scan measured against the whole "
                  "window rather than a local block (the lake wash band is wider than any "
                  "local background); water selected from three hand-placed seeds, boundary "
                  "traced and simplified, split into shore and not-shore by whether Wright "
                  "drew a line under it, runs claimed by hand-placed anchors; pixels "
                  "transformed to EPSG:26916 by the least-squares affine refit from "
                  "data/traces/gcp/wright_1834_gcps.json — the same transform that fixed "
                  "the datum and traced the forks",
        "tool": "tools/trace_shoreline.py",
        "iiif_region": {"image": IIIF, "x": REGION[0], "y": REGION[1],
                        "w": REGION[2], "h": REGION[3], "sha256": sha},
        "lettering_closed": {
            "boxes_px": {k: list(v) for k, v in LETTERING.items()},
            "recovered_px": recovered,
            "why": "Wright letters CHICAGO RIVER in outline display capitals across the "
                   "main stem, and the interior of an outline capital is unwashed paper. "
                   "Letters that fall wholly inside the water come out as holes and the "
                   "island rule fills them. The G of CHICAGO does not: a brown foxing "
                   "stain joins it to the drawn south bank, so letter, stain and bank "
                   "traced as one dry region and the run walked round all three — a 60 m "
                   "headland into the channel at Clark Street that Wright does not draw, "
                   "and which put the traced south bank 79.6 m off the recorded South "
                   "Water building faces at Clark against 18.7 m at Dearborn. Inside the "
                   "declared box a dry span with channel at both ends of its own row is "
                   "read as a gap in the DRAWING. The waterline is still Wright's wash, "
                   "reconnected across his own type; no new line is drawn.",
            "blast_radius": "The corrected walk is SPLICED into the uncorrected one at the "
                            "box, so every vertex outside the boxes is the one the "
                            "uncorrected trace produced, byte for byte. Douglas-Peucker "
                            "halves a ring by index and is therefore not local: republishing "
                            "the whole corrected ring instead would have moved vertices a "
                            "kilometre away and made it impossible to show that only the "
                            "Clark reach changed.",
        },
        "affine_rms_m": round(rms, 1),
        "map_scale_m_per_px": round(cell_m, 4),
        "simplify_tolerance_m": round(PARAMS["simplify_px"] * cell_m, 2),
        "uncertainty_m": 20,
        "uncertainty_note": "As the forks: both 1834 sheets carry real anisotropic paper "
                            "stretch, so a global affine cannot do better than tens of metres "
                            "locally. Treat every vertex as +/-20 m. See "
                            "docs/RESEARCH/datum_derivation.md.",
        "shore_test": {
            "rule": "A boundary vertex belongs to a shore when Wright drew a line under it. "
                    "The line is read as dark AND a ridge — darker than what lies on either "
                    "side of it — because a wash pools its pigment at the edge it dries "
                    "against and that pooled band reaches the ink threshold on luminance "
                    "alone while being the opposite of a drawn line. A dry gap shorter than "
                    "ink_bridge_px between two inked stretches is a break in the line; an "
                    "inked stretch shorter than ink_spur_px standing in a dry one is the "
                    "sheet's own lettering.",
            "ink_lum": PARAMS["ink_lum"],
            "ink_ridge": PARAMS["ink_ridge"],
            "ink_ridge_r": PARAMS["ink_ridge_r"],
            "ink_near_px": PARAMS["ink_near_px"],
            "ink_bridge_px": PARAMS["ink_bridge_px"],
            "ink_spur_px": PARAMS["ink_spur_px"],
            "measured": "Both published shore runs sit a median 1.42 m from the drawn line, "
                        "against a dropped east edge whose nearest ink is hundreds of metres "
                        "away. Each run carries its own median and p90 in "
                        "ink_distance_median_m / ink_distance_p90_m.",
        },
        "not_traced": "The outer edge of the lake wash band is where the draughtsman stopped "
                      "washing, not a feature. It is found, reported and dropped — 3,936 m of "
                      "it, the whole east side of the body, with no drawn line anywhere under "
                      "it. Nothing in this file describes the lake east of the traced shore. "
                      "Since T-0799 that edge is Wright's brush rather than this program's "
                      "window: the window now stands clear of the wash on every side but the "
                      "forks junction at local E +314.",
    }

    features = [
        {
            "type": "Feature",
            "id": "harbor_reach_water",
            "geometry": {"type": "Polygon",
                         "coordinates": [closed(water_ring), closed(bar)]},
            "properties": {
                "kind": "water",
                "name": "Chicago River harbour reach, the 1834 cut, the old southward "
                        "channel and the lake margin",
                "water_surface_ft_above_datum": 0.0,
                "confidence": "inferred",
                "note": "Planform traced from the Wright 1834 survey; one connected body of "
                        "water from the east edge of the forks box to the lake, and from the "
                        "sheet's top margin to where the wash stops above its bottom one. The "
                        "water surface is flat at the datum because the pre-reversal river "
                        "stood at lake level through the whole downtown reach. The interior "
                        "ring is the sand bar. The EASTERN boundary of this polygon is where "
                        "Wright stopped washing the lake — not a shore, and since T-0799 not "
                        "a window either. See provenance.not_traced.",
                "sources": ["wright_1834", "wikipedia_chicago_river"],
                "provenance": prov,
            },
        },
        {
            "type": "Feature",
            "id": "sand_bar_1834",
            "geometry": {"type": "Polygon", "coordinates": [closed(bar)]},
            "properties": {
                "kind": "bar",
                "name": "The sand bar across the river mouth",
                "confidence": "inferred",
                "note": "Land, not water: the bar Wright labels SAND-BAR, traced as the island "
                        "the water goes round. Its planform is drafted on a cadastral plat, so "
                        "the same +/-20 m applies and the same 'reconstructed' the river polygon "
                        "carries. NO ELEVATION IS CLAIMED HERE — a bar is a surface a few feet "
                        "of lake stage moves, no source gives its height, and the terrain spec "
                        "is where any such number would have to be argued for. Wright shows it "
                        "already cut through by the 1834 harbour works, with the old southward "
                        "channel behind it drawn narrowing and its arrow still running south.",
                "sources": ["wright_1834"],
                "provenance": prov,
            },
        },
    ]

    labels = {
        "south_shore_harbor_reach": (
            "South shore of the harbour reach and the lake shore south of it: south bank of "
            "the main stem east of the forks box, the Fort Dearborn reservation's lake shore, "
            "the west bank of the old southward channel behind the bar, and the east edge of "
            "Fractional Section 15 to the foot of the sheet",
            "Continuous from the forks box eastward: the same waterline the forks trace ends "
            "on, picked up again at local E +314, and carried south without a break to the "
            "bottom of Wright's drawing at about N -2122 — 3.8 km of it, where before T-0799 "
            "it stopped at N -580 on the edge of a window. The old southward channel closes "
            "inside this run rather than leaving it: behind the bar the wash narrows to the "
            "arrow Wright draws and its west bank runs on into the lake shore, so the channel "
            "and the shore are one line here and the trace does not pretend to divide them. "
            "The last 200 m along the foot of the wash carries the sheet's dark bottom edge "
            "rather than a clean pen line and is the weakest part of the run; its p90 distance "
            "to drawn line is the number to read before using it.",
        ),
        "north_shore_harbor_reach": (
            "North shore of the harbour reach: north bank of the main stem, the inner face of "
            "the north pier, and the lake shore north of the harbour",
            "BETWEEN THE PIERS THIS IS NOT A NATURAL SHORE. Wright draws the 1834 cut as a "
            "straight channel between two pier lines, and the traced boundary there follows "
            "the pier's inner face as drafted. The piers are structures with phases (see "
            "docs/EPOCHS.md), so they are not modelled here and their alignment is not a "
            "terrain claim; this run says only where the drawn water ended.",
        ),
    }
    for key, (line, anchor_m, ink_med, ink_p90) in named.items():
        name, note = labels[key]
        features.append({
            "type": "Feature",
            "id": key,
            "geometry": {"type": "LineString",
                         "coordinates": [[e + o_e, n + o_n] for e, n in line]},
            "properties": {
                "kind": "shore",
                "name": name,
                "crest_ft_above_datum": None,
                "confidence": "inferred",
                "note": note + " Crest heights are carried in the terrain spec, not here: they "
                                "come from narrative feet, not from the map.",
                "length_m": round(length_m(line), 1),
                "anchor_distance_m": anchor_m,
                "ink_distance_median_m": ink_med,
                "ink_distance_p90_m": ink_p90,
                "sources": ["wright_1834"],
            },
        })

    fc = {
        "type": "FeatureCollection",
        "name": "e1834_harbor_cut shoreline",
        "crs": {"type": "name", "properties": {"name": "urn:ogc:def:crs:EPSG::26916"}},
        "_doc": "The lake shore, the harbour reach, the 1834 cut and the sand bar for terrain "
                "epoch e1834_harbor_cut — everything between the east edge of the forks box "
                "and Lake Michigan. Coordinates are EPSG:26916 metres (UTM 16N, NAD83); local "
                "ENU metres used by the scene are these minus data/datum.json origin_utm_e / "
                "origin_utm_n. Generated by tools/trace_shoreline.py — do not hand-edit. NOT "
                "YET CONSUMED by generators/terrain_gen.py: the terrain box still stops at "
                "local E +320 and extending it is the next slice of ROADMAP S2e, which needs "
                "a bake. Until then this file is the evidence, not the ground. T-0799 opened "
                "the traced window to the whole sheet east of the forks box, so the east edge "
                "here is Wright's line and his brush and no longer this program's box.",
        "features": features,
    }

    text = json.dumps(fc, indent=1) + "\n"
    if args.check:
        old = OUT.read_text() if OUT.exists() else ""
        same = old == text
        print(f"{'OK  ' if same else 'DIFF'} {OUT.relative_to(ROOT)}")
        if not same:
            return 1
    else:
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        OUT.write_text(text)
        print(f"wrote {OUT.relative_to(ROOT)} ({len(text):,} bytes)")

    if args.debug:
        over = rgb.copy()
        over[water] = (0.72 * over[water] + np.array([0, 90, 240]) * 0.28).astype(np.uint8)
        over[islands] = (0.72 * over[islands] + np.array([240, 170, 0]) * 0.28).astype(np.uint8)
        for px, py in bar_px:
            over[max(0, py - 3):py + 4, max(0, px - 3):px + 4] = (255, 140, 0)
        for key, (ax, ay) in ANCHORS.items():
            over[ay - REGION[1] - 5:ay - REGION[1] + 6,
                 ax - REGION[0] - 5:ax - REGION[0] + 6] = (0, 0, 0)
        for j, idx in enumerate(runs_px):
            col = [(200, 0, 0), (140, 0, 220), (0, 150, 0), (0, 0, 0)][j % 4]
            for i in idx:
                px, py = ring_px[i]
                over[max(0, py - 3):py + 4, max(0, px - 3):px + 4] = col
        p = Path("/tmp") / "shoreline_trace_debug.png"
        Image.fromarray(over).save(p)
        print("debug overlay", p)
    return 0


if __name__ == "__main__":
    sys.exit(main())
