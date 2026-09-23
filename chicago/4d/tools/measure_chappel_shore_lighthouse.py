#!/usr/bin/env python3
"""measure_chappel_shore_lighthouse.py — can the lighthouse settle what the Eliza
Chappel shore drawing depicts?

T-0649. T-0617 deposited a fifth image beside the four attested Sauganash views and
deliberately did NOT spend it, because its subject is unsettled:

  (a) it is Eliza Chappell's FIRST school of September 1833 — the "small log house
      formerly used as a store" that the Beaubien material calls Mark Beaubien's own
      original cabin beside the Sauganash at Lake and Market — in which case the
      drawing is a fifth, nearly square-on view of the Sauganash's log annex; or
  (b) it is some other log schoolhouse and leaves the Sauganash entirely.

The ticket names the control: **the lighthouse is read rather than eyeballed.** The
tower's drawn position and proportions, the bank's bearing and the log building's
orientation, taken together, either say which corner of the town the view stands on
or say — with the number that shows it — that they cannot. This file is that reading,
and `docs/RESEARCH/chappel_shore_lighthouse.md` is where it is graded.

THE TWO SHEETS
--------------
`chicago/reference/images/chicago/eliza-chappel-school/21617595_…_n.jpg`, 640 x 368 —
the drawing under test. A log building at the right with a woman in its doorway,
children on the bank, canoes afloat and hauled up, a white tower on a low point in the
middle distance, and a scatter of small gabled buildings on a flat prairie horizon.

`chicago/reference/images/chicago/chicago_harbor_lighthouse_1838.jpg`, 640 x 361 —
the control: the 1832 tower drawn from the river with Fort Dearborn beside it.

Both are small. The drawn tower is about 13 px across, and every ratio below carries
that: an edge is worth +/- 1 px, so a width ratio is worth +/- 15 %. The file reports
the error band rather than hiding it, because the whole point of T-0197 is that a
number nobody can check is worse than no number.

WHAT IS MEASURED, AND WHY THESE AND NOT OTHERS
----------------------------------------------
The decisive test is FOCAL-FREE, which is what makes it worth running on a sheet this
small. For anything standing on one flat ground plane, seen from one station,

    drawn height / (base depression below the horizon)  =  H / h_eye

and the right-hand side does not depend on the distance, the focal length, or the size
of the sheet. So the ratio r = drawn/(y_base - y_horizon) must be THE SAME for every
adult in the picture, wherever they stand. Measuring r for four adults at four depths
therefore tests the drawing itself, before any question about Chicago is asked.

Given r, every pair of objects fixes a height RATIO: r_i / r_j = H_i / H_j. So the
tower's height follows from an adult's, in metres, with no perspective assumption at
all — and the answer can be compared with the forty feet Andreas gives the 1832 tower
and `data/structures/chicago_lighthouse_1832.json` carries.

The station then needs one more thing the sheet does not give: the focal length. What
the file reports instead is the focal length the Sauganash corner WOULD require, from
the committed coordinates of `sauganash_hotel` and `chicago_lighthouse_1832`, and the
field of view that implies. A reader can then judge it against the picture in front of
them, which is a judgement a detector should not pretend to make.

WHAT IS NOT MEASURED, AND WHY THE FILE SAYS SO
----------------------------------------------
* The tower's TAPER. The shaft is 13 px wide over 20 px of visible height; a taper of
  the size a masonry tower of the period carries is under a pixel across that run, and
  in the control sheet the tower's right edge is lost in foliage below the gallery.
  The comparison is therefore made on the SIGNATURE — railed gallery, domed lantern,
  finial, and the gallery's overhang — and the file states what that can and cannot
  exclude.
* The log building itself. This ticket does not spend the view on the annex; it only
  measures the building's ORIENTATION, because the ticket names it as one of the three
  things read together.
"""


from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
IMAGES = ROOT.parent / "reference" / "images" / "chicago"
DRAWING = IMAGES / "eliza-chappel-school" / "21617595_10203558686525015_5452300313452439832_n.jpg"
CONTROL = IMAGES / "chicago_harbor_lighthouse_1838.jpg"
BASELINE = ROOT / "tools" / "chappel_shore_lighthouse_baseline.json"

# The two records this reading is checked against, so that a later edit to either one
# is caught here rather than in prose.
LIGHTHOUSE_RECORD = ROOT / "data" / "structures" / "chicago_lighthouse_1832.json"
SAUGANASH_RECORD = ROOT / "data" / "structures" / "sauganash_hotel.json"
PALISADE_RECORD = ROOT / "data" / "structures" / "fort_dearborn_palisade.json"

# The stated scale data. An adult of the period at 1.70 m, hat included, which is the
# figure tools/measure_sauganash_plate.py already stands on; a woman at 1.60 m. Both
# are generous, so every metric height derived from them is an UPPER bound on nothing
# and a lower bound on nothing — it is a ratio, and the ratio is what is reported.
ADULT_M = 1.70
WOMAN_M = 1.60
# Andreas, quoted in the record: "Another tower, forty feet high".
TOWER_DOC_M = 40.0 * 0.3048
# A one-storey log dwelling of the period, ground to ridge. NOT a source claim: it is
# the typological band the file tests the drawn cabin against, and it is stated so the
# test can be argued with.
CABIN_RIDGE_BAND_M = (4.0, 5.5)

SKY = 205          # luminance above this is open sky on the drawing
INK = 150          # luminance below this is a drawn line against sky
SOLID = 130        # luminance below this is a filled mass, not a hatched tone

# ---------------------------------------------------------------------------
# The stated search windows on the DRAWING. Every one is a box round a PART OF THE
# PICTURE, never round the feature itself: the detector finds the feature inside it.
# They are quoted in docs/RESEARCH/chappel_shore_lighthouse.md so a reader can lay
# them back on the sheet.
# ---------------------------------------------------------------------------
TOWER = (119, 139, 180, 236)          # the tower, sky to bank
HORIZON_BAND = (220, 432, 195, 245)   # open prairie: no tree, no building
# The two buildings that stand on the tower's own ground, either hand of it. Their
# feet ARE drawn where the tower's is not, which is the only reason the tower gets a
# ground line at all.
GROUND_L = (103, 119, 216, 242)
GROUND_R = (140, 153, 216, 244)
# The water's edge, left of the tower, fitted and then carried across to the tower's
# own column: the tower stands on land, so its foot cannot be below this line.
WATERLINE_BAND = (72, 120, 205, 275)
# What flanks the tower. Fort Dearborn's palisade is 53 m square on the committed
# footprint and stands about 40 m from the light, so from any station up the river it
# is drawn AT the tower's foot, and these are the boxes it would have to be in.
TOWER_FLANK_L = (78, 119, 200, 244)
TOWER_FLANK_R = (139, 196, 200, 244)

CABIN_ROOF = (500, 640, 140, 232)     # the log building's silhouette against sky
LINTEL = (550, 583, 213, 221)         # the band the doorcase's head lies in
CABIN_FACE_L = (510, 516, 228, 272)   # blank log wall left of the left window
CABIN_FACE_R = (543, 549, 228, 272)   # blank log wall between window and doorcase

# Four adults, at four depths, each box drawn round the FIGURE'S COLUMN of the
# picture. The detector finds the head and the feet inside the box.
ADULTS = {
    "doorway_woman": (562, 578, 222, 282),    # in the doorway, on the cabin floor
    "bank_hatted_man": (372, 386, 232, 296),  # mid-ground, at the fence
    "shore_man_left": (318, 340, 288, 360),   # foreground, hauling the canoe
    "shore_man_right": (386, 420, 288, 356),  # foreground, leading a child
}
# The doorway woman stands on the cabin FLOOR, which the drawn steps raise above the
# ground, so she is reported and then set aside rather than averaged in.
FLOOR_IS_RAISED = "doorway_woman"

# The control sheet. The tower's right edge is lost in foliage below the gallery, so
# the window stops at the gallery and no taper is reported.
CTL_TOWER = (584, 620, 44, 130)


class NoReader(Exception):
    pass


class SheetError(Exception):
    pass


def _load(path):
    try:
        from PIL import Image  # noqa: WPS433
        import numpy as np     # noqa: WPS433
    except ImportError as exc:
        raise NoReader(str(exc))
    if not path.exists():
        raise SheetError(f"{path.name} is not in the tree")
    import numpy as np
    from PIL import Image
    return np.asarray(Image.open(path).convert("L"), dtype=float)


def _dark_extent(a, y, x0, x1, thr):
    row = a[y, x0:x1]
    idx = [i for i, v in enumerate(row) if v < thr]
    return (x0 + idx[0], x0 + idx[-1]) if idx else None


def _topmost(a, x, y0, y1, thr, run=2):
    col = a[y0:y1, x]
    for i in range(len(col) - run):
        if all(col[i + k] < thr for k in range(run)):
            return y0 + i
    return None


def _fit(xs, ys):
    n = len(xs)
    if n < 2:
        raise SheetError("a line was fitted to fewer than two points")
    mx, my = sum(xs) / n, sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    m = sxy / sxx if sxx else 0.0
    b = my - m * mx
    resid = math.sqrt(sum((y - (m * x + b)) ** 2 for x, y in zip(xs, ys)) / n)
    return m, b, resid


# ---------------------------------------------------------------------------
# The horizon. On a flat prairie the drawn sky/ground boundary IS the eye-level
# horizon, because the plane runs to infinity. That is the one assumption every
# focal-free number below rests on, and it is stated here rather than buried.
# ---------------------------------------------------------------------------
def read_horizon(a):
    x0, x1, y0, y1 = HORIZON_BAND
    xs, ys = [], []
    for x in range(x0, x1, 3):
        y = _topmost(a, x, y0, y1, thr=200, run=4)
        if y is not None:
            xs.append(x)
            ys.append(y)
    if len(ys) < 8:
        raise SheetError("the prairie horizon did not resolve in HORIZON_BAND")
    srt = sorted(ys)
    med = srt[len(srt) // 2]
    keep = [(x, y) for x, y in zip(xs, ys) if abs(y - med) <= 6]
    m, b, resid = _fit([p[0] for p in keep], [p[1] for p in keep])
    return {
        "window": HORIZON_BAND,
        "samples": len(xs),
        "kept": len(keep),
        "y": med,
        "fit_slope": round(m, 5),
        "fit_residual_px": round(resid, 2),
        "y_uncertainty_px": 3,
    }


# ---------------------------------------------------------------------------
# The ground the tower stands on, which the tower itself does not give.
# ---------------------------------------------------------------------------
def read_ground_line(a):
    out = {}
    for name, (x0, x1, y0, y1) in (("left", GROUND_L), ("right", GROUND_R)):
        # A building's foot is the last row of a RUN of filled rows, never the
        # lowest filled row anywhere: a tuft of bank grass is one row and a wall is
        # several. The lowest such run in the window is the one standing on ground.
        foot, run, seen = None, 0, []
        for y in range(y0, y1 + 1):
            frac = (float(sum(1 for v in a[y, x0:x1] if v < SOLID)) / (x1 - x0)
                    if y < y1 else 0.0)
            if frac >= 0.45:
                run += 1
            else:
                if run >= 2:
                    seen.append(y - 1)
                run = 0
        if not seen:
            raise SheetError(f"the {name} building beside the tower has no drawn foot")
        foot = max(seen)
        out[name] = {"window": [x0, x1, y0, y1], "foot_y": foot, "runs": len(seen)}
    out["ground_y"] = min(out["left"]["foot_y"], out["right"]["foot_y"])
    out["$note"] = ("the two feet are measured independently and the HIGHER "
                    "is taken, because a foot can only be drawn too low by "
                    "grass and never too high by anything")
    return out


def read_waterline(a, tower_x):
    x0, x1, y0, y1 = WATERLINE_BAND
    xs, ys = [], []
    for x in range(x0, x1, 2):
        last = None
        for y in range(y0, y1):
            if float(a[y - 2:y + 3, x - 2:x + 3].std()) > 28:
                last = y
        if last is not None:
            xs.append(x)
            ys.append(last)
    if len(xs) < 6:
        raise SheetError("the water's edge did not resolve in WATERLINE_BAND")
    m, b, resid = _fit(xs, ys)
    return {
        "window": WATERLINE_BAND,
        "samples": len(xs),
        "slope": round(m, 4),
        "residual_px": round(resid, 2),
        "y_at_tower": int(round(m * tower_x + b)),
    }


# ---------------------------------------------------------------------------
# The tower on the drawing.
# ---------------------------------------------------------------------------
def read_tower(a):
    x0, x1, y0, y1 = TOWER
    rows = {}
    for y in range(y0, y1):
        e = _dark_extent(a, y, x0, x1, INK)
        if e:
            rows[y] = e
    if not rows:
        raise SheetError("no tower ink inside TOWER")
    ys = sorted(rows)
    finial = ys[0]
    widths = {y: rows[y][1] - rows[y][0] + 1 for y in ys}

    # The bands are found, not declared: the gallery is the widest run in the tower's
    # upper fifth, the lantern is what stands above it, the shaft is what hangs below.
    upper = [y for y in ys if y <= finial + 20]
    gy = max(upper, key=lambda y: widths[y])
    gallery = [y for y in upper if widths[y] >= widths[gy] - 2 and abs(y - gy) <= 5]
    gband = (min(gallery), max(gallery))
    shaft_ys = [y for y in ys if gband[1] + 2 <= y <= gband[1] + 20]
    sw = sorted(widths[y] for y in shaft_ys)
    shaft_med = sw[len(sw) // 2] if sw else None
    gallery_w = max(widths[y] for y in gallery)

    # The shaft's own foot is NOT drawn: the bank's grass takes the window over. The
    # last row that still carries the shaft's lit interior is therefore the least
    # depression the tower can have, and it is reported as such.
    axis = (rows[gy][0] + rows[gy][1]) // 2
    lit = None
    for y in range(gband[1] + 4, y1):
        run, best = 0, 0
        for v in a[y, axis - 6:axis + 7]:
            run = run + 1 if v >= 185 else 0
            best = max(best, run)
        if best >= 4:
            lit = y
    return {
        "window": TOWER,
        "axis_x": axis,
        "finial_y": finial,
        "gallery_band": list(gband),
        "gallery_width_px": gallery_w,
        "shaft_width_px": shaft_med,
        "shaft_rows": [min(shaft_ys), max(shaft_ys)] if shaft_ys else None,
        "last_lit_row": lit,
        "foot_is_drawn": False,
        "gallery_overhang": round(gallery_w / shaft_med, 3) if shaft_med else None,
        "edge_error_px": 1,
    }


def read_control_tower(a):
    x0, x1, y0, y1 = CTL_TOWER
    rows = {}
    for y in range(y0, y1):
        e = _dark_extent(a, y, x0, x1, 170)
        if e:
            rows[y] = e
    if not rows:
        raise SheetError("no tower ink inside CTL_TOWER")
    ys = sorted(rows)
    finial = ys[0]
    widths = {y: rows[y][1] - rows[y][0] + 1 for y in ys}
    upper = [y for y in ys if y <= finial + 55]
    gy = max(upper, key=lambda y: widths[y])
    gallery = [y for y in upper if widths[y] >= widths[gy] - 2 and abs(y - gy) <= 8]
    gband = (min(gallery), max(gallery))
    shaft_ys = [y for y in ys if gband[1] + 3 <= y <= gband[1] + 20]
    sw = sorted(widths[y] for y in shaft_ys)
    shaft_med = sw[len(sw) // 2] if sw else None
    gw = max(widths[y] for y in gallery)
    return {
        "window": CTL_TOWER,
        "finial_y": finial,
        "gallery_band": list(gband),
        "gallery_width_px": gw,
        "shaft_width_px": shaft_med,
        "gallery_overhang": round(gw / shaft_med, 3) if shaft_med else None,
        "occluded_below_gallery": True,
        "why_no_taper": "the tower's right edge runs into foliage below the gallery on "
                        "this sheet, so no width below the gallery is a tower width",
    }


# ---------------------------------------------------------------------------
# The figures, and the focal-free test that is the point of the file.
# ---------------------------------------------------------------------------
def read_adults(a):
    out = {}
    for name, (x0, x1, y0, y1) in ADULTS.items():
        tops, feet = [], []
        for x in range(x0, x1):
            t = _topmost(a, x, y0, y1, thr=120, run=2)
            if t is not None:
                tops.append(t)
            col = a[y0:y1, x]
            last = [y0 + i for i, v in enumerate(col) if v < 120]
            if last:
                feet.append(last[-1])
        if not tops or not feet:
            raise SheetError(f"{name} did not resolve inside its window")
        tops.sort()
        feet.sort()
        top = tops[len(tops) // 4]        # lower quartile: the crown, not a stray
        foot = feet[3 * len(feet) // 4]   # upper quartile: the sole, not the grass
        out[name] = {
            "window": [x0, x1, y0, y1],
            "top_y": top,
            "foot_y": foot,
            "drawn_height_px": foot - top,
        }
    return out


def read_cabin(a):
    x0, x1, y0, y1 = CABIN_ROOF
    sil = {}
    for x in range(x0, x1):
        y = _topmost(a, x, y0, y1, thr=INK, run=2)
        if y is not None:
            sil[x] = y
    if not sil:
        raise SheetError("no cabin silhouette inside CABIN_ROOF")
    # The tree that overhangs the top-right corner reaches the window's own ceiling,
    # so the apex is looked for LEFT of it, in a stated band, and the ridge is
    # followed only as far as the column where the tree's ink begins.
    left = {x: y for x, y in sil.items() if 520 <= x <= 585}
    apex_x = min(left, key=lambda x: left[x])
    apex_y = left[apex_x]
    tree_x = min((x for x in sorted(sil) if x > apex_x + 6 and sil[x] <= y0 + 2),
                 default=x1)
    ridge = [(x, sil[x]) for x in range(apex_x + 4, min(tree_x, x1)) if x in sil]
    rm, rb, rres = _fit([p[0] for p in ridge], [p[1] for p in ridge])
    rake = [(x, sil[x]) for x in range(514, apex_x - 3) if x in sil]
    km, kb, kres = _fit([p[0] for p in rake], [p[1] for p in rake])
    return {
        "window": CABIN_ROOF,
        "apex": [apex_x, apex_y],
        "ridge_slope": round(rm, 4),
        "ridge_residual_px": round(rres, 2),
        "ridge_samples": len(ridge),
        "rake_slope": round(km, 4),
        "rake_residual_px": round(kres, 2),
    }


def read_lintel(a):
    """the doorcase's head: the one long, unambiguous world-horizontal on the face."""
    x0, x1, y0, y1 = LINTEL
    xs, ys = [], []
    for x in range(x0, x1):
        seg = list(a[y0:y1, x])
        i = min(range(len(seg)), key=lambda k: seg[k])
        if i in (0, len(seg) - 1):
            continue
        # a parabola through the darkest sample and its two neighbours, so the head
        # is located to a fraction of a pixel rather than to the nearest row
        lft, mid, rgt = seg[i - 1], seg[i], seg[i + 1]
        den = lft - 2 * mid + rgt
        off = 0.0 if den == 0 else 0.5 * (lft - rgt) / den
        xs.append(x)
        ys.append(y0 + i + max(-1.0, min(1.0, off)))
    if len(xs) < 20:
        raise SheetError("the doorcase head did not resolve in LINTEL")
    m, b, resid = _fit(xs, ys)
    return {
        "window": LINTEL,
        "samples": len(xs),
        "slope": round(m, 5),
        "residual_px": round(resid, 3),
        "y_at_door_centre": round(m * ((x0 + x1) / 2) + b, 2),
        "run_px": x1 - x0,
    }


def read_face_courses(a):
    """a second, independent look at the same question: do the log courses tilt?"""
    import numpy as np

    def strip(win):
        wx0, wx1, wy0, wy1 = win
        s = a[wy0:wy1, wx0:wx1].mean(axis=1)
        return s - s.mean()

    A, B = strip(CABIN_FACE_L), strip(CABIN_FACE_R)
    best = (0.0, -2.0)
    for sft in [i / 4 for i in range(-40, 41)]:
        idx = np.arange(len(B)) + sft
        Bi = np.interp(idx, np.arange(len(B)), B, left=0.0, right=0.0)
        den = math.sqrt(float((A * A).sum()) * float((Bi * Bi).sum())) + 1e-9
        c = float((A * Bi).sum()) / den
        if c > best[1]:
            best = (sft, c)
    dx = CABIN_FACE_R[0] - CABIN_FACE_L[0]
    return {
        "left_window": CABIN_FACE_L,
        "right_window": CABIN_FACE_R,
        "baseline_px": dx,
        "shift_px": best[0],
        "correlation": round(best[1], 3),
        "slope": round(best[0] / dx, 5),
        "shift_resolution_px": 0.25,
    }


def read_tower_flanks(a, ground_y, tall_px):
    """what is drawn beside the tower — the Fort Dearborn test."""
    out = {}
    for name, (x0, x1, y0, y1) in (("left", TOWER_FLANK_L), ("right", TOWER_FLANK_R)):
        per = []
        for x in range(x0, x1):
            t = _topmost(a, x, y0, y1, thr=SOLID, run=3)
            per.append(0 if t is None or t >= ground_y - 2 else ground_y - t)
        # A fort is a WIDE thing, so what is measured is the longest unbroken run of
        # columns standing at least a third of the tower's height above its ground,
        # not the one tallest column, which any tree supplies.
        floor_px = max(1, int(round(tall_px / 3.0)))
        best, run = 0, 0
        for v in per:
            run = run + 1 if v >= floor_px else 0
            best = max(best, run)
        out[name] = {
            "window": [x0, x1, y0, y1],
            "columns_in_window": x1 - x0,
            "columns_with_built_ink": sum(1 for v in per if v > 0),
            "tallest_rise_px": max(per),
            "sustained_floor_px": floor_px,
            "longest_sustained_run_px": best,
        }
    return out


# ---------------------------------------------------------------------------
# The town's own coordinates: what the Sauganash station would require, and how big
# the fort would have to be drawn at it.
# ---------------------------------------------------------------------------
def town_geometry():
    lh = json.loads(LIGHTHOUSE_RECORD.read_text(encoding="utf-8"))
    sg = json.loads(SAUGANASH_RECORD.read_text(encoding="utf-8"))
    fd = json.loads(PALISADE_RECORD.read_text(encoding="utf-8"))
    lp = lh["phases"][0]["position"]
    # The Sauganash's first phase is the 1829 log house, whose point is still null;
    # the corner the caption puts the school on is the 1831 frame house's, so the
    # station is taken from the first phase that carries a point rather than from [0].
    sp = next(ph["position"] for ph in sg["phases"]
              if (ph.get("position") or {}).get("utm_e") is not None)
    fp = fd["phases"][0]
    poly = fp["footprint"]["polygon"]
    span = max(max(p[0] for p in poly) - min(p[0] for p in poly),
               max(p[1] for p in poly) - min(p[1] for p in poly))
    fq = fp["position"]
    dx, dy = lp["utm_e"] - sp["utm_e"], lp["utm_n"] - sp["utm_n"]
    fx, fy = lp["utm_e"] - fq["utm_e"], lp["utm_n"] - fq["utm_n"]
    return {
        "lighthouse_utm": [lp["utm_e"], lp["utm_n"]],
        "sauganash_utm": [sp["utm_e"], sp["utm_n"]],
        "sauganash_range_m": round(math.hypot(dx, dy), 1),
        "sauganash_bearing_to_light_deg": round(math.degrees(math.atan2(dx, dy)) % 360, 1),
        "palisade_span_m": round(span, 1),
        "palisade_to_light_m": round(math.hypot(fx, fy), 1),
        "tower_documented_m": round(TOWER_DOC_M, 2),
    }


def read_sheets():
    a = _load(DRAWING)
    c = _load(CONTROL)
    if a.shape != (368, 640):
        raise SheetError(f"the drawing is {a.shape[1]}x{a.shape[0]}, not 640x368")
    tower = read_tower(a)
    ground = read_ground_line(a)
    water = read_waterline(a, tower["axis_x"])
    return {
        "horizon": read_horizon(a),
        "tower": tower,
        "ground_line": ground,
        "waterline": water,
        "control_tower": read_control_tower(c),
        "adults": read_adults(a),
        "cabin": read_cabin(a),
        "lintel": read_lintel(a),
        "face_courses": read_face_courses(a),
        "tower_flanks": read_tower_flanks(a, ground["ground_y"],
                                         ground["ground_y"] - tower["finial_y"]),
        "town": town_geometry(),
    }


def banked(live_town=False):
    """the banked reading — with its `town` block re-derived, not replayed.

    T-1083. Bare, this returns the baseline verbatim — that is the DRIFT BASE, and
    it has to be what was banked or there is nothing to drift from. With
    `live_town=True` the `town` block is recomputed instead, which is what the
    no-reader path stands on.

    Everything else in this reading comes off two committed rasters and
    cannot move, which is why banking it is honest. The `town` block is different
    in kind: it is arithmetic over `data/structures/*.json`, it needs no image
    library at all, and those records DO move. Replaying a banked copy of it made
    the drift check compare the baseline with itself, so when T-1065 put the
    lighthouse on Wright's glyph and the Sauganash range went 1066.3 -> 1001.2,
    CI — which installs no image library — read the step as green.
    """
    if not BASELINE.exists():
        raise SheetError(f"{BASELINE.name} is not in the tree")
    r = json.loads(BASELINE.read_text(encoding="utf-8"))["reading"]
    if live_town:
        r = dict(r, town=town_geometry())
    return r


# ---------------------------------------------------------------------------
# The arithmetic. For anything standing on one flat plane seen from one station,
#     r = drawn height / (base depression below the horizon) = H / h_eye,
# and nothing in that line knows the focal length, the distance, or the size of the
# sheet. So r must be the SAME for every adult in the picture; and for any two
# objects, H_i / H_j = r_i / r_j.
# ---------------------------------------------------------------------------
def derive(r):
    yh = r["horizon"]["y"]
    tw, gl, wl = r["tower"], r["ground_line"], r["waterline"]

    def ratio(drawn, foot):
        dep = foot - yh
        return None if dep <= 0 else drawn / dep

    people = {}
    for name, f in r["adults"].items():
        people[name] = {
            "depression_px": f["foot_y"] - yh,
            "drawn_px": f["drawn_height_px"],
            "r": round(ratio(f["drawn_height_px"], f["foot_y"]), 4),
        }
    # The three adults who stand on the GROUND. The doorway woman stands on a floor
    # the steps raise, so she is reported and set aside rather than averaged in.
    rs = {n: v["r"] for n, v in people.items() if n != FLOOR_IS_RAISED}
    lo, hi = min(rs.values()), max(rs.values())

    # The tower's base is a BAND, because its foot is not drawn: it cannot be higher
    # than the last row still carrying the shaft's lit interior, and it cannot be
    # lower than the water's edge at its own column. The buildings either side of it
    # stand on its ground and their feet ARE drawn, so their line is the estimate.
    base_hi, base_lo = tw["last_lit_row"], wl["y_at_tower"]
    base_est = gl["ground_y"]
    bases = {"least_depression": base_hi, "estimate": base_est, "most_depression": base_lo}
    r_tower = {k: round(ratio(v - tw["finial_y"], v), 4) for k, v in bases.items()}

    # What the tower's height comes out as, in metres, scaled from each adult in turn.
    tower_m = {}
    for bn, rt in r_tower.items():
        tower_m[bn] = {n: round((rt / v) * ADULT_M, 2) for n, v in rs.items()}
    flat = [v for d in tower_m.values() for v in d.values()]

    cabin_base_y = r["adults"]["bank_hatted_man"]["foot_y"]
    r_cabin = ratio(cabin_base_y - r["cabin"]["apex"][1], cabin_base_y)
    cabin_m = {n: round((r_cabin / v) * ADULT_M, 2) for n, v in rs.items()}

    # The falloff. Two adults at two depths must be drawn in the ratio of their
    # depressions. This is the whole test in one number, and it uses no tower at all.
    near = max(rs, key=lambda n: people[n]["depression_px"])
    far = min(rs, key=lambda n: people[n]["depression_px"])
    demanded = people[near]["depression_px"] / people[far]["depression_px"]
    drawn = people[near]["drawn_px"] / people[far]["drawn_px"]

    # What the Sauganash corner would require of the sheet.
    t = r["town"]
    req = {}
    for n, v in rs.items():
        eye = ADULT_M / v
        f_px = t["sauganash_range_m"] * (base_est - yh) / eye
        req[n] = {
            "eye_m": round(eye, 2),
            "focal_px": round(f_px, 0),
            "hfov_deg": round(2 * math.degrees(math.atan(320.0 / f_px)), 2),
            "that_adult_stands_m_away": round(f_px * eye / people[n]["depression_px"], 1),
        }

    # The fort test, which needs neither horizon nor focal length: two things at the
    # same distance are drawn in the ratio of their real sizes.
    tower_drawn = base_est - tw["finial_y"]
    fort_px = tower_drawn * t["palisade_span_m"] / TOWER_DOC_M
    fl = r["tower_flanks"]
    return {
        "horizon_y": yh,
        "people": people,
        "adult_r_low": round(lo, 4),
        "adult_r_high": round(hi, 4),
        "adult_r_spread": round(hi / lo, 3),
        "tower_bases": bases,
        "r_tower": r_tower,
        "tower_height_m": tower_m,
        "tower_height_band_m": [min(flat), max(flat)],
        "tower_height_band_ft": [round(min(flat) / 0.3048), round(max(flat) / 0.3048)],
        "documented_tower_m": round(TOWER_DOC_M, 2),
        "band_contains_forty_feet": min(flat) <= TOWER_DOC_M <= max(flat),
        "r_cabin": round(r_cabin, 4),
        "cabin_ridge_m": cabin_m,
        "falloff": {
            "near": near, "far": far,
            "depression_ratio_demanded": round(demanded, 3),
            "drawn_height_ratio_observed": round(drawn, 3),
            "shortfall": round(demanded / drawn, 3),
        },
        "sauganash_station_requires": req,
        "fort_test": {
            "tower_drawn_px": tower_drawn,
            "palisade_would_be_drawn_px": round(fort_px),
            "sheet_width_px": 640,
            "palisade_as_fraction_of_sheet": round(fort_px / 640.0, 3),
            "built_columns_beside_the_tower":
                fl["left"]["columns_with_built_ink"] + fl["right"]["columns_with_built_ink"],
            "widest_sustained_mass_px": max(fl["left"]["longest_sustained_run_px"],
                                            fl["right"]["longest_sustained_run_px"]),
            "mass_as_fraction_of_a_palisade":
                round(max(fl["left"]["longest_sustained_run_px"],
                          fl["right"]["longest_sustained_run_px"]) / fort_px, 3),
            "tallest_flank_in_tower_heights":
                round(max(fl["left"]["tallest_rise_px"],
                          fl["right"]["tallest_rise_px"]) / tower_drawn, 3),
        },
    }


def assess(r, d):
    band = CABIN_RIDGE_BAND_M
    cb = d["cabin_ridge_m"]
    ft = d["fort_test"]
    return {
        "horizon_is_straight": r["horizon"]["fit_residual_px"] <= 2.5,
        # the three ground-standing adults do NOT share one r, and that is the finding
        "adults_disagree": d["adult_r_spread"] >= 1.3,
        "falloff_is_short": d["falloff"]["shortfall"] >= 1.2,
        # the tower's foot is not drawn, so its height is a band, and the band is wide
        "tower_height_is_a_band": (d["tower_height_band_m"][1]
                                   / d["tower_height_band_m"][0]) >= 2.0,
        "band_contains_forty_feet": d["band_contains_forty_feet"],
        # the tower carries the control's signature and nothing sharper than that
        "gallery_overhangs_shaft": (r["tower"]["gallery_overhang"] or 0) > 1.0,
        "control_gallery_overhangs_shaft":
            (r["control_tower"]["gallery_overhang"] or 0) > 1.0,
        # the gable face is drawn square-on
        "face_is_square_on": abs(r["lintel"]["slope"]) <= 0.03,
        # nothing of fort scale stands at the tower's foot
        "no_fort_scale_mass_at_the_tower": ft["mass_as_fraction_of_a_palisade"] < 0.25,
        "fort_would_have_been_conspicuous": ft["palisade_as_fraction_of_sheet"] >= 0.20,
        "cabin_ridge_straddles_typology": min(cb.values()) <= band[1]
                                          and max(cb.values()) >= band[0],
        # and therefore
        "station_not_recoverable": d["adult_r_spread"] >= 1.3,
    }


def findings(r, d, a):
    bad = []
    if not a["horizon_is_straight"]:
        bad.append("the prairie horizon no longer fits a straight line: residual "
                   f"{r['horizon']['fit_residual_px']} px")
    if not a["adults_disagree"]:
        bad.append("the three ground-standing adults now share one ground plane "
                   f"(spread {d['adult_r_spread']}x) — the reading in "
                   "docs/RESEARCH/chappel_shore_lighthouse.md rests on their not doing so")
    if not a["falloff_is_short"]:
        bad.append("the figure scale now falls off with depth the way a single station "
                   f"demands: shortfall {d['falloff']['shortfall']}x")
    if not a["tower_height_is_a_band"]:
        bad.append("the tower's height is no longer a band: "
                   f"{d['tower_height_band_m']} m")
    if not a["gallery_overhangs_shaft"]:
        bad.append("the drawn tower no longer carries a gallery wider than its shaft: "
                   f"{r['tower']['gallery_width_px']} px over "
                   f"{r['tower']['shaft_width_px']} px")
    if not a["control_gallery_overhangs_shaft"]:
        bad.append("the control tower no longer carries a gallery wider than its shaft")
    if not a["face_is_square_on"]:
        bad.append(f"the doorcase head is no longer horizontal: slope "
                   f"{r['lintel']['slope']} over {r['lintel']['run_px']} px")
    if not a["no_fort_scale_mass_at_the_tower"]:
        bad.append("something of fort scale now stands at the tower's foot: a mass "
                   f"{d['fort_test']['widest_sustained_mass_px']} px wide against the "
                   f"{d['fort_test']['palisade_would_be_drawn_px']} px a palisade needs")
    if not a["fort_would_have_been_conspicuous"]:
        bad.append("the fort would no longer have been conspicuous at the Sauganash "
                   f"station: {d['fort_test']['palisade_as_fraction_of_sheet']} of the sheet")
    return bad


# The two checks that stand on committed records rather than on the rasters, so
# they are answerable whether or not an image library is installed (T-1083).
TOWN_CHECKS = (("sauganash_range_m", 1.0), ("palisade_span_m", 0.5),
               ("palisade_to_light_m", 0.5))


def _report(checks):
    out = []
    for name, f, b, tol in checks:
        if f is None or b is None:
            if f != b:
                out.append(f"{name} moved from {b} to {f}")
            continue
        if abs(f - b) > tol:
            out.append(f"{name} moved from {b} to {f} (tolerance {tol})")
    return out


def town_drift(fresh, base):
    """record drift, with no raster read — what CI was blind to before T-1083."""
    return _report([(n, fresh["town"][n], base["town"][n], tol)
                    for n, tol in TOWN_CHECKS])


def drift(fresh, base):
    fd, bd = derive(fresh), derive(base)
    out = []
    checks = [
        ("horizon_y", fresh["horizon"]["y"], base["horizon"]["y"], 0),
        ("tower_finial_y", fresh["tower"]["finial_y"], base["tower"]["finial_y"], 0),
        ("tower_shaft_px", fresh["tower"]["shaft_width_px"],
         base["tower"]["shaft_width_px"], 0),
        ("tower_gallery_px", fresh["tower"]["gallery_width_px"],
         base["tower"]["gallery_width_px"], 0),
        ("tower_last_lit_row", fresh["tower"]["last_lit_row"],
         base["tower"]["last_lit_row"], 0),
        ("ground_y", fresh["ground_line"]["ground_y"], base["ground_line"]["ground_y"], 0),
        ("waterline_at_tower", fresh["waterline"]["y_at_tower"],
         base["waterline"]["y_at_tower"], 0),
        ("control_gallery_px", fresh["control_tower"]["gallery_width_px"],
         base["control_tower"]["gallery_width_px"], 0),
        ("cabin_apex_y", fresh["cabin"]["apex"][1], base["cabin"]["apex"][1], 0),
        ("lintel_slope", fresh["lintel"]["slope"], base["lintel"]["slope"], 0.004),
        ("adult_r_spread", fd["adult_r_spread"], bd["adult_r_spread"], 0.05),
        ("falloff_shortfall", fd["falloff"]["shortfall"], bd["falloff"]["shortfall"], 0.05),
        ("sauganash_range_m", fresh["town"]["sauganash_range_m"],
         base["town"]["sauganash_range_m"], 1.0),
        ("palisade_span_m", fresh["town"]["palisade_span_m"],
         base["town"]["palisade_span_m"], 0.5),
        ("palisade_to_light_m", fresh["town"]["palisade_to_light_m"],
         base["town"]["palisade_to_light_m"], 0.5),
    ]
    return out + _report(checks)


def show(r, d, a):
    h, tw, ct = r["horizon"], r["tower"], r["control_tower"]
    print("   The Chappel shore drawing, read against the harbour light")
    print(f"     horizon         y={h['y']} +/-{h['y_uncertainty_px']} px, straight to "
          f"{h['fit_residual_px']} px over {h['kept']} prairie columns")
    print(f"     the tower       finial y={tw['finial_y']}, gallery {tw['gallery_band']}, "
          f"shaft {tw['shaft_width_px']} px wide; ITS FOOT IS NOT DRAWN")
    print(f"     its ground      buildings either side stand at y={r['ground_line']['ground_y']}; "
          f"lit shaft ends y={tw['last_lit_row']}, water's edge y={r['waterline']['y_at_tower']}")
    print(f"     its signature   gallery overhang {tw['gallery_overhang']} "
          f"(+/-{tw['edge_error_px']} px on a {tw['shaft_width_px']} px shaft is "
          f"+/-{round(1.0 / tw['shaft_width_px'], 2)}); the 1838 tower's is "
          f"{ct['gallery_overhang']}")
    print("     four adults, who must share one r = drawn / depression:")
    for n, v in d["people"].items():
        note = "  (on the cabin floor, set aside)" if n == FLOOR_IS_RAISED else ""
        print(f"       {n:<18} depression {v['depression_px']:>3} px, drawn "
              f"{v['drawn_px']:>3} px   r = {v['r']}{note}")
    fo = d["falloff"]
    print(f"     the falloff     {fo['near']} is {fo['depression_ratio_demanded']}x deeper "
          f"than {fo['far']} and is drawn only {fo['drawn_height_ratio_observed']}x "
          f"larger — SHORT BY {fo['shortfall']}x")
    print(f"     adult r spread  {d['adult_r_spread']}x ({d['adult_r_low']} to "
          f"{d['adult_r_high']}) where a single station demands 1.000x")
    print(f"     so the tower is {d['tower_height_band_m'][0]}-{d['tower_height_band_m'][1]} m "
          f"({d['tower_height_band_ft'][0]}-{d['tower_height_band_ft'][1]} ft); Andreas "
          f"gives the 1832 tower {d['documented_tower_m']} m (40 ft), which the band "
          + ("CONTAINS" if d["band_contains_forty_feet"] else "EXCLUDES"))
    print(f"     and the cabin   {d['cabin_ridge_m']} m to the ridge, against "
          f"{CABIN_RIDGE_BAND_M[0]}-{CABIN_RIDGE_BAND_M[1]} m for a one-storey log dwelling")
    t = r["town"]
    print(f"     the station     the Sauganash corner is {t['sauganash_range_m']} m from "
          f"the light, bearing {t['sauganash_bearing_to_light_deg']} deg, on the "
          "committed coordinates")
    for n, v in d["sauganash_station_requires"].items():
        print(f"       scaled from {n:<16} f={v['focal_px']} px "
              f"({v['hfov_deg']} deg of field), that adult {v['that_adult_stands_m_away']} m off")
    ft = d["fort_test"]
    print(f"     the fort test   the palisade is {t['palisade_span_m']} m square and "
          f"{t['palisade_to_light_m']} m from the light, so beside a "
          f"{ft['tower_drawn_px']} px tower it is {ft['palisade_would_be_drawn_px']} px "
          f"wide — {ft['palisade_as_fraction_of_sheet']} of the sheet")
    print(f"                     drawn instead: the widest unbroken mass flanking it is "
          f"{ft['widest_sustained_mass_px']} px, {ft['mass_as_fraction_of_a_palisade']} "
          f"of a palisade; tallest flank {ft['tallest_flank_in_tower_heights']} tower-heights")
    print(f"     the log face    doorcase head slope {r['lintel']['slope']} over "
          f"{r['lintel']['run_px']} px (residual {r['lintel']['residual_px']} px): "
          "drawn square-on")
    print(f"     the cabin roof  ridge slope {r['cabin']['ridge_slope']}, rake "
          f"{r['cabin']['rake_slope']}, apex {r['cabin']['apex']}")
    print("     THE VERDICT     the adults do not share a ground plane, the tower's foot "
          "is not drawn, and no fort stands beside it. The lighthouse does NOT settle "
          "what this drawing depicts.")


def self_test(r, d, a):
    ok = True
    for name in ("horizon_is_straight", "adults_disagree", "falloff_is_short",
                 "tower_height_is_a_band", "gallery_overhangs_shaft",
                 "control_gallery_overhangs_shaft", "face_is_square_on",
                 "no_fort_scale_mass_at_the_tower", "fort_would_have_been_conspicuous",
                 "station_not_recoverable"):
        if not a[name]:
            print(f"   FAIL self-test {name} is false")
            ok = False
    if min(d["tower_height_band_m"]) <= 0:
        print("   FAIL self-test the tower's height band is not positive")
        ok = False
    if ok:
        print("   self-test: the ten claims docs/RESEARCH/chappel_shore_lighthouse.md "
              "rests on hold")
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--gate", action="store_true")
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--write-baseline", action="store_true")
    args = ap.parse_args()

    live = True
    try:
        reading = read_sheets()
    except NoReader:
        try:
            reading, live = banked(live_town=True), False
        except SheetError as exc:
            print(f"   FAIL {exc}")
            return 1
    except SheetError as exc:
        print(f"   FAIL {exc}")
        return 1

    d = derive(reading)
    a = assess(reading, d)

    if args.self_test:
        return self_test(reading, d, a)
    if args.json:
        print(json.dumps({"reading": reading, "derived": d, "assessed": a},
                         indent=2, sort_keys=True))
        return 0
    if args.write_baseline:
        if not live:
            print("   FAIL cannot bank a baseline without Pillow and numpy")
            return 1
        BASELINE.write_text(json.dumps({
            "$note": "T-0649. The banked reading of the Eliza Chappel shore drawing and "
                     "of the 1838 harbour-light plate by "
                     "tools/measure_chappel_shore_lighthouse.py. Both sheets are "
                     "committed and cannot change, so this exists for two reasons: CI "
                     "installs no image library and would otherwise skip the reading in "
                     "silence, and a detector edit that quietly moves a reading is a "
                     "thing this project has been bitten by (T-0197). Regenerate with "
                     "--write-baseline, and only ever with the reason in the commit. "
                     "T-1083: the `town` block here is the drift BASE only. It is "
                     "arithmetic over data/structures/*.json, not over either raster, "
                     "and the tool re-derives it live on every run — so a record that "
                     "moves is caught with or without an image library. Re-derived "
                     "2026-09-12 because T-1065 (#1189) put the lighthouse on Wright's "
                     "own glyph and nothing re-banked this with it.",
            "reading": reading,
        }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        show(reading, d, a)
        print(f"\n   wrote {BASELINE.name}")
        return 0

    bad = findings(reading, d, a)
    if BASELINE.exists():
        # T-1083. The raster half of the drift needs a reader; the town half never
        # did, and running it here is what stops a no-reader gate counting its own
        # skip as a pass.
        bad += drift(reading, banked()) if live else town_drift(reading, banked())
    if not live:
        print("   Pillow or numpy is absent, so THE TWO SHEETS WERE NOT RE-READ. "
              f"Standing on the banked reading in {BASELINE.name}; the town "
              "geometry below is still derived live from the committed records, "
              "and is gated.")
    if not args.quiet or bad:
        show(reading, d, a)
    for g in bad:
        print(f"   FAIL {g}")
    if not bad and not args.quiet:
        print("   the sheets still say what docs/RESEARCH/chappel_shore_lighthouse.md "
              "says they say")
    return 1 if (bad and args.gate) else 0


if __name__ == "__main__":
    sys.exit(main())
