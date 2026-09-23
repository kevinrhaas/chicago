#!/usr/bin/env python3
"""measure_sauganash_plate.py — what Braunhold's plate of the Sauganash actually says.

T-0617. The owner deposited four views of the Sauganash on 2026-09-03 and asked for
the building to be read off them: *"missing a fair amount of detail, like the door,
the windows, the roof, etc."* T-0616 filed the brief, this file is the reading, and
`docs/RESEARCH/sauganash_image_accuracy.md` is where the numbers are graded.

WHY THERE IS A DETECTOR HERE AT ALL, and it is the whole lesson of T-0197. Eight rows
of the Fort Dearborn image table were written by eye; three were struck as wrong
inside a week, and two of those had already become tickets whose runs were spent
proving the ticket wrong. The standing rule that came out of it: **a row states a
measurement, names the tool that made it, and prints the number.** So every figure in
the research note is produced here, and banked, so that a later edit to this file
cannot move the reading in silence.

THE PLATE
---------
`chicago/reference/images/chicago/chicago_sauganash_hotel_1831.jpg`, 2017 x 1296 —
F. Braunhold's pen engraving, "Copyright secured by A. T. Andreas, 1884", the
highest-resolution and cleanest-line of the four views the owner deposited. It is
ink on white paper, so a single luminance threshold segments it; the three other
views (Petford's watercolour, the Trowbridge drawing, the Alamy colour thumbnail)
are the SAME COMPOSITION and are not independent witnesses of it —
`data/sources/trowbridge_sauganash_hotel.json` and
`docs/RESEARCH/sauganash_hotel.md` § 4 both say so already, and this reading does
not pretend otherwise. Two of the measures below (bay count, chimney count) are
re-run on Petford as a copying check, not as corroboration.

WHAT IS MEASURED, AND WHAT MAKES IT A MEASUREMENT RATHER THAN AN IMPRESSION
--------------------------------------------------------------------------
The building is drawn in a two-point perspective, so nothing on it can be read with
a ruler laid on the sheet. Two things make the numbers below real:

 1. **The facade's own horizontals are the ruler.** Each storey's window HEADS lie on
    one world-horizontal line and its SILLS on another. Four such lines are detected
    on the south-east face and two on the gable end. Each face's lines meet at that
    face's vanishing point, and with the vanishing point known, ratios of distances
    along the wall follow from the cross-ratio exactly — no assumption about the
    camera at all. Bay rhythm is therefore reported RECTIFIED.
 2. **The scale datum is stated and is a person.** A standing adult is taken at
    1.70 m. The figures at the main door stand at the facade, and the ratio of their
    drawn height to the drawn wall height at their own column converts the whole
    face to metres. They stand a little FORWARD of the wall, so they are drawn a
    little large for their plane, so **every metric length below is a lower bound**.
    That bias is stated rather than corrected, because correcting it would mean
    claiming a depth the plate does not give.

The two faces' vanishing points also test the plate itself. Two orthogonal
horizontal vanishing points of one real camera satisfy
`(v1 - p) . (v2 - p) = -f^2` for principal point p and focal length f, so a
retrospective engraving that was composed by eye rather than constructed will fail
it with a NEGATIVE f^2. That test is run and its result is reported either way: it
decides whether the plate's plan proportions are evidence or are draughtsmanship.

WHAT IS NOT MEASURED, AND WHY THE FILE SAYS SO
----------------------------------------------
The roof PITCH is reported as the apparent rake of the near gable and as the apex's
rise in wall-heights. Turning that into a true pitch needs the gable's true width —
the depth of the building — and depth is exactly what one plate cannot give. The
number is reported for what it is and graded accordingly; T-0626 is where the plan
is decided, and it may not be decided from here.
"""


from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLATE = ROOT.parent / "reference" / "images" / "chicago" / "chicago_sauganash_hotel_1831.jpg"
BASELINE = ROOT / "tools" / "sauganash_plate_baseline.json"

# The stated scale datum. A standing adult of the period, hat included, because the
# hat is what the detector measures to; 1.70 m is therefore generous, which is the
# first of the two reasons every metric length below is a LOWER BOUND.
ADULT_M = 1.70

INK = 110         # luminance below this is ink
VRUN = 7          # px; ink this tall in a column is a vertical stroke, not clapboard

# ---------------------------------------------------------------------------
# The stated search windows. Every one is a box drawn round a PART OF THE BUILDING,
# never round a feature: the detector finds the feature inside it. They are quoted in
# docs/RESEARCH/sauganash_image_accuracy.md so a reader can lay them back on the sheet.
# ---------------------------------------------------------------------------
SE_UPPER = (915, 1645, 520, 712)      # the upper storey of the south-east face
SE_LOWER = (915, 1645, 745, 975)      # its ground storey
END_UPPER = (465, 865, 555, 700)      # the gable end's upper storey
ATTIC = (590, 720, 400, 545)          # the gable's own window

# Blank wall, between the openings, where the siding may be read. Four along the
# south-east face so its horizontals can be followed across the run, two on the gable
# end so that face gets its own.
SE_SIDING = {
    "se_1": (1035, 1105, 555, 700),
    "se_2": (1190, 1265, 560, 720),
    "se_3": (1400, 1470, 570, 730),
    "se_4": (1630, 1690, 590, 740),
}
END_SIDING = {
    "end_1": (600, 740, 580, 700),
    "end_2": (470, 530, 600, 690),
}
ANNEX_LOGS = {
    "annex_face_east": (760, 860, 830, 1005),
    "annex_face_west": (520, 640, 835, 1010),
    "annex_return": (280, 460, 830, 1000),
}
# The two men on the walk in front of bays 1 and 2. They stand on light siding, which
# is why the datum is taken from them and not from the pair in the dark doorway.
FIGURES = {
    "walk_left": (888, 936, 880, 1062),
    "walk_right": (938, 986, 880, 1062),
}
ROOF_BAND = (430, 1720, 250, 520)

SLOPES = [round(-0.20 + 0.002 * i, 4) for i in range(201)]


class NoReader(Exception):
    """Pillow or numpy is absent, so the plate cannot be re-read here."""


class PlateError(Exception):
    """The plate is present and the detector could not read it. Never swallowed."""


def load():
    try:
        from PIL import Image
        import numpy as np
    except Exception as exc:  # pragma: no cover - environment dependent
        raise NoReader(str(exc))
    if not PLATE.exists():
        raise PlateError(f"{PLATE} is missing")
    grey = np.asarray(Image.open(PLATE).convert("L")).astype(float)
    ink = (grey < INK).astype(float)
    h, w = ink.shape
    tall = np.ones((h - VRUN + 1, w))
    for k in range(VRUN):
        tall = np.minimum(tall, ink[k:h - VRUN + 1 + k, :])
    vert = np.zeros_like(ink)
    vert[VRUN // 2:VRUN // 2 + tall.shape[0], :] = tall
    return np, ink, vert


# ---------------------------------------------------------------------------
# primitives
# ---------------------------------------------------------------------------
def runs(profile, thr, min_len, gap):
    out, start = [], None
    for i, v in enumerate(profile):
        if v >= thr and start is None:
            start = i
        elif v < thr and start is not None:
            out.append([start, i])
            start = None
    if start is not None:
        out.append([start, len(profile)])
    merged = []
    for r in out:
        if merged and r[0] - merged[-1][1] <= gap:
            merged[-1][1] = r[1]
        else:
            merged.append(r)
    return [tuple(r) for r in merged if r[1] - r[0] >= min_len]


def siding(np, ink, box):
    """The slope and the course pitch of a wall's own horizontals, by shear search.

    A clapboard wall and a log wall are both a stack of world-horizontal lines at one
    pitch. Shear the patch by a candidate slope, project onto rows, and take the
    variance of that profile: the true slope is the one that stacks every line on
    itself and maximises it. The pitch then falls out of the profile's own
    autocorrelation. Nothing here assumes where a window is, which is why it works on
    plain siding and on logs with the same code.
    """
    x0, x1, y0, y1 = box
    cx = (x0 + x1) / 2.0
    best = None
    for s in SLOPES:
        acc = {}
        for x in range(x0, x1):
            off = s * (x - cx)
            for y in range(y0, y1):
                yy = int(round(y - off))
                a = acc.setdefault(yy, [0.0, 0])
                a[0] += ink[y, x]
                a[1] += 1
        ys = sorted(k for k, v in acc.items() if v[1] >= 0.9 * (x1 - x0))
        if len(ys) < 20:
            continue
        prof = np.array([acc[k][0] / acc[k][1] for k in ys])
        v = float(prof.var())
        if best is None or v > best[1]:
            best = (s, v, prof)
    if best is None:
        raise PlateError(f"no siding slope in {box}")
    s, v, prof = best
    q = prof - prof.mean()
    den = float((q * q).sum()) or 1.0
    lag, corr = None, -2.0
    for k in range(8, min(40, len(q))):
        c = float((q[:-k] * q[k:]).sum()) / den
        if c > corr:
            lag, corr = k, c
    return {"slope": s, "contrast": round(v, 5), "course_px": lag,
            "autocorr": round(corr, 3), "cx": cx,
            "cy": (y0 + y1) / 2.0}


def meet(p1, m1, p2, m2):
    """Where two lines, each a point and a slope, cross."""
    if abs(m1 - m2) < 1e-9:
        raise PlateError("parallel lines have no crossing")
    x = (p2[1] - m2 * p2[0] - p1[1] + m1 * p1[0]) / (m1 - m2)
    return x, m1 * (x - p1[0]) + p1[1]


def vanishing(lines):
    """The least-squares crossing of a pencil of world-horizontals, each given as
    ((x, y), slope). Ill-conditioned when the lines are nearly parallel, which is why
    the caller is required to hand in one line of markedly different slope — on this
    plate, the RIDGE, which runs the same world direction as the siding and is drawn
    high above it."""
    import numpy as np
    A = np.array([[-m, 1.0] for _, m in lines])
    b = np.array([p[1] - m * p[0] for p, m in lines])
    sol, *_ = np.linalg.lstsq(A, b, rcond=None)
    resid = float(np.abs(A @ sol - b).max())
    return {"x": round(float(sol[0]), 1), "y": round(float(sol[1]), 1),
            "max_residual_px": round(resid, 2), "lines": len(lines)}


def equal_bay_station(centres):
    """The vanishing column that would make the drawn bays EQUAL on the ground.

    If the five bays are one rhythm, their rectified coordinates 1/(V - x) are an
    arithmetic progression; the V that makes them so is found by minimising the
    spread of their differences. Comparing it with the vanishing point the BUILDING's
    own lines give is the test of whether the sheet was constructed or composed."""
    best = None
    for k in range(200, 60000):
        V = centres[-1] + k * 1.0
        u = [1.0 / (V - c) for c in centres]
        d = [u[i + 1] - u[i] for i in range(len(u) - 1)]
        mean = sum(d) / len(d)
        cost = (max(d) - min(d)) / mean
        if best is None or cost < best[1]:
            best = (V, cost)
        if k > 400 and cost > best[1] * 4:
            break
    return {"x": round(best[0], 1), "residual_spread": round(best[1], 4)}


def openings(np, ink, vert, box, thr=0.10, min_len=26, gap=8, pool=3):
    """Openings in a wall, found by the one thing that separates them from siding.

    A clapboard or log wall is horizontal ink; a window is a frame, stiles, muntins
    and shutter leaves, and it is the only VERTICAL ink on the face. `vert` keeps ink
    only where it runs VRUN pixels down a column, which deletes the siding outright.
    The column profile is dilated by `pool` so a stroke a pixel off vertical still
    counts, and the opening's centre is that profile's own centroid rather than the
    midpoint of the run, which would move with the detector's edges.

    The vertical extent is then read by DIFFERENCE against blank wall: the same
    number of columns of siding beside the opening, subtracted row by row. What is
    left is the window and nothing else, and it needs no threshold on the wall's ink.
    """
    x0, x1, y0, y1 = box
    col = vert[y0:y1, x0:x1].sum(axis=0) / float(y1 - y0)
    pooled = np.array([col[max(0, i - pool):i + pool + 1].max() for i in range(col.size)])
    found = []
    for a, b in runs(pooled, thr, min_len, gap):
        w = pooled[a:b]
        cx = x0 + a + float((w * np.arange(len(w))).sum() / max(w.sum(), 1e-9))
        span = b - a
        # blank wall to whichever side has room for it
        ref = None
        for dx in (span + 12, -(span + 12), span + 40, -(span + 40)):
            if 0 <= x0 + a + dx and x0 + b + dx < ink.shape[1]:
                ref = dx
                break
        y_lo, y_hi = y0, y1
        if ref is not None:
            here = ink[y_lo:y_hi, x0 + a:x0 + b].sum(axis=1) / span
            there = ink[y_lo:y_hi, x0 + a + ref:x0 + b + ref].sum(axis=1) / span
            d = np.convolve(here - there, np.ones(7) / 7.0, mode="same")
            rr = runs(d, 0.25 * float(d.max()), 18, 14)
        else:
            rr = []
        if rr:
            ry0, ry1 = max(rr, key=lambda r: r[1] - r[0])
        else:
            ry0, ry1 = 0, y_hi - y_lo
        found.append({"x0": x0 + a, "x1": x0 + b, "y0": y_lo + ry0, "y1": y_lo + ry1,
                      "cx": round(cx, 1),
                      "ink": round(float(ink[y_lo + ry0:y_lo + ry1,
                                             x0 + a:x0 + b].mean()), 4)})
    return found


def figure(np, ink, box):
    """A standing figure is the tallest dense row-run in its own box: hat to heel."""
    x0, x1, y0, y1 = box
    row = ink[y0:y1, x0:x1].sum(axis=1) / float(x1 - x0)
    rr = runs(row, 0.45 * float(row.max()), 40, 14)
    if not rr:
        raise PlateError(f"no figure in {box}")
    a, b = max(rr, key=lambda r: r[1] - r[0])
    return {"top": y0 + a, "foot": y0 + b, "px": b - a, "cx": (x0 + x1) / 2.0}


def skyline(np, ink, box, min_mass=9):
    """The topmost ink of a MASS, not of a line. The sky is cloud hatching and the
    roof is shingle hatching, both of them strokes a few pixels wide; eroding by a
    horizontal window `min_mass` wide deletes every stroke and leaves chimneys,
    ridges and walls."""
    x0, x1, y0, y1 = box
    sub = ink[y0:y1, x0:x1]
    h, w = sub.shape
    keep = np.ones((h, w - min_mass + 1))
    for k in range(min_mass):
        keep = np.minimum(keep, sub[:, k:w - min_mass + 1 + k])
    tops = []
    for j in range(keep.shape[1]):
        nz = np.nonzero(keep[:, j])[0]
        tops.append((x0 + min_mass // 2 + j, int(nz[0]) + y0) if nz.size else None)
    return [t for t in tops if t]


def fit(points):
    n = len(points)
    sx = sum(p[0] for p in points)
    sy = sum(p[1] for p in points)
    sxx = sum(p[0] * p[0] for p in points)
    sxy = sum(p[0] * p[1] for p in points)
    den = n * sxx - sx * sx
    if abs(den) < 1e-9:
        raise PlateError("degenerate line fit")
    m = (n * sxy - sx * sy) / den
    c = (sy - m * sx) / n
    rms = math.sqrt(sum((m * x + c - y) ** 2 for x, y in points) / n)
    return m, c, rms


# ---------------------------------------------------------------------------
# the reading
# ---------------------------------------------------------------------------
def read_plate():
    np, ink, vert = load()
    out = {}

    # --- the siding: every face's own ruler ---------------------------------
    out["siding"] = {k: siding(np, ink, b) for k, b in SE_SIDING.items()}
    out["siding"].update({k: siding(np, ink, b) for k, b in END_SIDING.items()})
    out["logs"] = {k: siding(np, ink, b) for k, b in ANNEX_LOGS.items()}

    # --- the openings --------------------------------------------------------
    up = openings(np, ink, vert, SE_UPPER)
    lo = openings(np, ink, vert, SE_LOWER)
    if not up or not lo:
        raise PlateError(f"south-east face: {len(up)} upper, {len(lo)} lower openings")
    door = max(lo, key=lambda o: o["ink"])
    out["se_face"] = {
        "upper": up, "lower": lo,
        "bays_upper": len(up), "bays_lower": len(lo),
        "door_index_1based": lo.index(door) + 1,
        "door": door,
    }
    out["end_face"] = {"upper": openings(np, ink, vert, END_UPPER),
                       "attic": openings(np, ink, vert, ATTIC)}

    # --- the scale datum ------------------------------------------------------
    figs = {k: figure(np, ink, b) for k, b in FIGURES.items()}
    px = sum(f["px"] for f in figs.values()) / len(figs)
    mpp = ADULT_M / px
    out["scale"] = {
        "adult_m": ADULT_M,
        "figures": figs,
        "figure_px_mean": round(px, 1),
        "figure_px_spread": max(f["px"] for f in figs.values()) - min(f["px"] for f in figs.values()),
        "m_per_px": round(mpp, 6),
        "note": "the two men on the walk stand a pace forward of the wall, so they are "
                "drawn a shade large for the facade plane: every metre below is a lower bound",
    }

    def m(v):
        return round(v * mpp, 3)

    # --- what the siding is ---------------------------------------------------
    se_courses = [out["siding"][k]["course_px"] for k in SE_SIDING
                  if out["siding"][k]["autocorr"] > 0.15]
    out["clapboard"] = {
        "course_px": se_courses,
        "median_px": sorted(se_courses)[len(se_courses) // 2] if se_courses else None,
        "exposure_m": m(sorted(se_courses)[len(se_courses) // 2]) if se_courses else None,
    }
    log_courses = [v["course_px"] for v in out["logs"].values() if v["autocorr"] > 0.15]
    out["annex"] = {
        "course_px": log_courses,
        "median_px": sorted(log_courses)[len(log_courses) // 2] if log_courses else None,
        "course_m": m(sorted(log_courses)[len(log_courses) // 2]) if log_courses else None,
        "autocorr": {k: v["autocorr"] for k, v in out["logs"].items()},
    }

    # --- the door -------------------------------------------------------------
    d = door
    # The doorcase run includes the jambs and the sidelights; the transom sits over
    # the LEAF, so the core is the 70-column window inside the doorcase with the most
    # ink at door-leaf height — the unlit room behind the open door and nothing else.
    best_c, best_v = d["x0"], -1.0
    for c in range(d["x0"], d["x1"] - 70):
        v = float(ink[840:940, c:c + 70].mean())
        if v > best_v:
            best_c, best_v = c, v
    core0, core1 = best_c, best_c + 70
    rowp = ink[740:1000, core0:core1].sum(axis=1) / float(core1 - core0)
    # The head of the OPENING is the top of the longest solid-dark run: the doorcase
    # cornice is solid too, and is fifteen rows deep against the opening's two hundred.
    solid = runs(rowp, 0.80, 25, 6)
    transom = None
    if solid:
        head = max(solid, key=lambda r: r[1] - r[0])[0]
        above = rowp[max(0, head - 45):head]
        if len(above) > 10:
            mean_ink = float(above.mean())
            transom = {"rows": [740 + head - len(above), 740 + head],
                       "px": len(above), "mean_ink": round(mean_ink, 3),
                       "glazed": bool(0.20 < mean_ink < 0.80)}
        threshold_row = 740 + head
    else:
        threshold_row = None
    out["door_detail"] = {
        "doorcase_px": d["x1"] - d["x0"], "doorcase_m": m(d["x1"] - d["x0"]),
        "opening_px": d["y1"] - d["y0"], "opening_m": m(d["y1"] - d["y0"]),
        "door_head_row": threshold_row,
        "leaf_core": [core0, core1], "leaf_core_ink": round(best_v, 3),
        "transom": transom,
    }

    # --- window proportions ---------------------------------------------------
    def prop(items):
        """Widths are the detector's own column runs and are steady. HEIGHTS are only
        reported when the storey's own windows agree: the sash extents come from
        differencing against blank wall, and where a bay's neighbour is a doorway or
        a corner board there is no blank wall to difference against. A storey whose
        windows disagree by more than a quarter of their height is reported as NOT
        RESOLVED, with the spread, rather than averaged into a number."""
        if not items:
            return None
        w = [o["x1"] - o["x0"] for o in items]
        h = [o["y1"] - o["y0"] for o in items]
        spread = (max(h) - min(h)) / (sum(h) / len(h))
        resolved = spread <= 0.25
        return {"width_px": w, "height_px": h,
                "mean_width_m": m(sum(w) / len(w)),
                "height_spread": round(spread, 3),
                "height_resolved": bool(resolved),
                "mean_height_m": m(sum(h) / len(h)) if resolved else None}
    out["windows"] = {"upper": prop(up), "lower": prop([o for o in lo if o is not door])}

    # --- the storeys ----------------------------------------------------------
    if up and lo:
        upper_sill = sum(o["y1"] for o in up) / len(up)
        lower_head = sum(o["y0"] for o in lo if o is not door) / max(1, len(lo) - 1)
        upper_head = sum(o["y0"] for o in up) / len(up)
        out["storeys"] = {
            "upper_head_to_lower_head_px": round(lower_head - upper_head, 1),
            "storey_pitch_m": m(lower_head - upper_head),
            "spandrel_px": round(lower_head - upper_sill, 1),
            "spandrel_m": m(lower_head - upper_sill),
        }

    # --- the roof -------------------------------------------------------------
    pts = skyline(np, ink, ROOF_BAND)
    out["roof"] = {"sampled_columns": len(pts)}
    if pts:
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        # The running median of the skyline IS the roof: it steps over every chimney
        # and every finial, because none of them is 90 columns wide.
        med = []
        for i in range(len(ys)):
            w = sorted(ys[max(0, i - 90):i + 90])
            med.append(w[len(w) // 2])
        apex_i = min(range(len(med)), key=lambda i: med[i])
        apex = (xs[apex_i], med[apex_i])
        out["roof"]["apex"] = list(apex)
        left = [(xs[i], med[i]) for i in range(len(xs))
                if apex[0] - 200 <= xs[i] < apex[0] - 45]
        right = [(xs[i], med[i]) for i in range(len(xs))
                 if apex[0] + 45 < xs[i] <= apex[0] + 245]
        if len(left) > 20 and len(right) > 20:
            ml, _, rl = fit(left)
            mr, _, rr = fit(right)
            out["roof"].update({
                "left_rake_slope": round(ml, 4), "left_rake_rms": round(rl, 2),
                "right_rake_slope": round(mr, 4), "right_rake_rms": round(rr, 2),
                "rake_asymmetry": round(abs(abs(ml) - abs(mr)), 4),
            })
        # A chimney is a NARROW mass standing clear above that roof line. A gable
        # beyond the ridge is wide and is deliberately not counted here.
        flag = [1.0 if med[i] - ys[i] > 30 else 0.0 for i in range(len(ys))]
        stacks = []
        for a, b in runs(flag, 0.5, 20, 6):
            if xs[b - 1] - xs[a] > 95:
                continue
            stacks.append({"x0": xs[a], "x1": xs[b - 1], "top": min(ys[a:b]),
                           "rise_px": round(med[a + (b - a) // 2] - min(ys[a:b]), 1)})
        out["chimneys"] = {"count": len(stacks), "stacks": stacks}

    # --- where the building's own lines say the eye stood ---------------------
    # The south-east face's horizontals converge too weakly among themselves to fix a
    # vanishing point — four patches of siding 600 px apart differ by 0.016 in slope,
    # which is inside this detector's own noise. The RIDGE is the line that fixes it:
    # same world direction, drawn 300 px higher, and therefore a slope that is
    # genuinely different. Without it the crossing lands inside the wall it belongs
    # to, which is the arithmetic telling you it has no answer.
    good = [k for k in SE_SIDING if out["siding"][k]["autocorr"] >= 0.20]
    lines = [((out["siding"][k]["cx"], out["siding"][k]["cy"]), out["siding"][k]["slope"])
             for k in good]
    ridge = out.get("roof", {}).get("right_rake_slope")
    if ridge is not None and out["roof"].get("apex"):
        ax, ay = out["roof"]["apex"]
        lines.append(((ax + 140, ay + 140 * ridge), ridge))
    out["se_vanishing"] = vanishing(lines) if len(lines) >= 2 else None
    out["se_vanishing_inputs"] = {"siding_patches": good, "ridge_slope": ridge}

    # Both faces are horizontal directions on one ground plane, so they share a
    # horizon: the gable end's vanishing point is where its own siding meets it.
    end_slope = sum(out["siding"][k]["slope"] for k in END_SIDING) / len(END_SIDING)
    end_pt = (sum(out["siding"][k]["cx"] for k in END_SIDING) / len(END_SIDING),
              sum(out["siding"][k]["cy"] for k in END_SIDING) / len(END_SIDING))
    out["end_vanishing"] = None
    if out["se_vanishing"]:
        horizon = out["se_vanishing"]["y"]
        ex = end_pt[0] + (horizon - end_pt[1]) / end_slope
        out["end_vanishing"] = {"x": round(ex, 1), "y": round(horizon, 1),
                                "slope": round(end_slope, 4)}

    # --- the bay rhythm -------------------------------------------------------
    cx = [o["cx"] for o in lo]
    gaps = [cx[i + 1] - cx[i] for i in range(len(cx) - 1)]
    vx = (out.get("se_vanishing") or {}).get("x")
    rect = None
    if vx and vx > cx[-1] + 50:
        u = [1.0 / (vx - c) for c in cx]
        rg = [u[i + 1] - u[i] for i in range(len(u) - 1)]
        mn = sum(rg) / len(rg)
        rect = [round(g / mn, 3) for g in rg]
    mean_gap = sum(gaps) / len(gaps)
    station = equal_bay_station(cx)
    out["bay_rhythm"] = {
        "image_centres": [round(c, 1) for c in cx],
        "image_gaps": [round(g, 1) for g in gaps],
        "rectified_gaps": rect,
        "rectified_spread_pct": round(100.0 * (max(rect) - min(rect)), 1) if rect else None,
        "spread_pct": round(100.0 * (max(gaps) - min(gaps)) / mean_gap, 1),
        "near_bay_m": m(gaps[0]),
        "equal_bay_station": station,
        "station_disagreement": round(station["x"] / vx, 2) if vx else None,
    }

    # --- the plate itself ------------------------------------------------------
    px_, py_ = 2017 / 2.0, 1296 / 2.0
    v1, v2 = out.get("se_vanishing"), out.get("end_vanishing")
    out["perspective_test"] = None
    if not (v1 and v2):
        return out
    dot = (v1["x"] - px_) * (v2["x"] - px_) + (v1["y"] - py_) * (v2["y"] - py_)
    out["perspective_test"] = {
        "f_squared": round(-dot, 1), "consistent": bool(-dot > 0),
        "focal_px": round(math.sqrt(-dot), 1) if -dot > 0 else None,
        "horizon_y": v1["y"],
        "note": "two orthogonal horizontal vanishing points of ONE real camera give "
                "f^2 = -(v1-p).(v2-p) > 0. A negative value says the sheet was composed "
                "by eye, and its plan proportions are draughtsmanship rather than survey.",
    }
    return out


# ---------------------------------------------------------------------------
# assertions, banking, reporting
# ---------------------------------------------------------------------------
def banked():
    if not BASELINE.exists():
        raise PlateError(f"{BASELINE.name} is missing")
    return json.loads(BASELINE.read_text(encoding="utf-8"))["reading"]


def assess(r):
    return {
        "five_bays": r["se_face"]["bays_upper"] == 5 and r["se_face"]["bays_lower"] == 5,
        "door_is_middle_bay": r["se_face"]["door_index_1based"] == 3,
        "door_has_transom": bool((r.get("door_detail") or {}).get("transom")
                                 and r["door_detail"]["transom"]["glazed"]),
        "annex_is_log_coursed": bool(r["annex"]["median_px"]),
        "logs_coarser_than_clapboard": bool(
            r["annex"]["median_px"] and r["clapboard"]["median_px"]
            and r["annex"]["median_px"] > r["clapboard"]["median_px"]),
        "two_chimneys_or_more": r.get("chimneys", {}).get("count", 0) >= 2,
        "rhythm_is_irregular": r["bay_rhythm"]["spread_pct"] > 8.0,
        "perspective_consistent": bool((r.get("perspective_test") or {}).get("consistent")),
    }


def findings(r, a):
    bad = []
    if not a["five_bays"]:
        bad.append("the south-east face no longer reads five bays over five: "
                   f"{r['se_face']['bays_upper']} upper, {r['se_face']['bays_lower']} lower")
    if not a["door_is_middle_bay"]:
        bad.append("the door is no longer the middle bay: it is bay "
                   f"{r['se_face']['door_index_1based']} of {r['se_face']['bays_lower']}")
    if not a["annex_is_log_coursed"]:
        bad.append("the annex no longer reads as a coursed log wall: "
                   f"{r['annex']['autocorr']}")
    if not a["logs_coarser_than_clapboard"]:
        bad.append("the annex's courses are no longer coarser than the block's siding: "
                   f"{r['annex']['median_px']} px against {r['clapboard']['median_px']} px")
    return bad


def drift(fresh, base):
    out = []
    checks = [
        ("bays_upper", fresh["se_face"]["bays_upper"], base["se_face"]["bays_upper"], 0),
        ("bays_lower", fresh["se_face"]["bays_lower"], base["se_face"]["bays_lower"], 0),
        ("door_index", fresh["se_face"]["door_index_1based"],
         base["se_face"]["door_index_1based"], 0),
        ("clapboard_px", fresh["clapboard"]["median_px"], base["clapboard"]["median_px"], 1),
        ("log_course_px", fresh["annex"]["median_px"], base["annex"]["median_px"], 1),
        ("figure_px", fresh["scale"]["figure_px_mean"], base["scale"]["figure_px_mean"], 3),
        ("bay_spread_pct", fresh["bay_rhythm"]["spread_pct"],
         base["bay_rhythm"]["spread_pct"], 2.0),
        ("se_vanishing_x", (fresh.get("se_vanishing") or {}).get("x"),
         (base.get("se_vanishing") or {}).get("x"), 900),
        ("chimney_count", fresh.get("chimneys", {}).get("count"),
         base.get("chimneys", {}).get("count"), 0),
    ]
    for name, f, b, tol in checks:
        if f is None or b is None:
            if f != b:
                out.append(f"{name} moved from {b} to {f}")
            continue
        if abs(f - b) > tol:
            out.append(f"{name} moved from {b} to {f} (tolerance {tol})")
    return out


def show(r, a):
    se = r["se_face"]
    print("   Braunhold's Sauganash, measured")
    print(f"     south-east face   {se['bays_upper']} bays over {se['bays_lower']}, "
          f"door in bay {se['door_index_1based']} of {se['bays_lower']}")
    br = r["bay_rhythm"]
    print(f"     bay rhythm        image gaps {br['image_gaps']} px, near bay "
          f"{br['near_bay_m']} m; rectified {br['rectified_gaps']}")
    print(f"     the station       building's lines say x={(r.get('se_vanishing') or {}).get('x')}, "
          f"equal bays would need x={br['equal_bay_station']['x']} "
          f"({br['station_disagreement']}x)")
    sc = r["scale"]
    print(f"     scale datum       adult {sc['adult_m']} m = {sc['figure_px_mean']} px "
          f"(spread {sc['figure_px_spread']}) -> {sc['m_per_px']} m/px, a lower bound")
    cl = r["clapboard"]
    print(f"     siding            clapboard course {cl['median_px']} px = "
          f"{cl['exposure_m']} m of exposure")
    an = r["annex"]
    print(f"     the log annex     course {an['median_px']} px = {an['course_m']} m, "
          f"autocorrelation {an['autocorr']}")
    dd = r["door_detail"]
    print(f"     the door          {dd['doorcase_m']} m over the doorcase, "
          f"{dd['opening_m']} m of opening, transom "
          + ("glazed and drawn" if a["door_has_transom"] else "not resolved"))
    w = r["windows"]
    print(f"     windows           upper {w['upper']['mean_width_m']} m wide, ground "
          f"{w['lower']['mean_width_m']} m wide; sash heights "
          + ("resolved" if w['lower']['height_resolved'] else
             f"NOT resolved (spread {w['lower']['height_spread']})"))
    st = r.get("storeys", {})
    print(f"     storeys           {st.get('storey_pitch_m')} m head to head")
    ch = r.get("chimneys", {})
    print(f"     chimneys          {ch.get('count')} clear of the roof at "
          f"{[s['x0'] for s in ch.get('stacks', [])]}")
    rf = r.get("roof", {})
    print(f"     roof              apex {rf.get('apex')}, rakes "
          f"{rf.get('left_rake_slope')} / {rf.get('right_rake_slope')}, "
          f"asymmetry {rf.get('rake_asymmetry')}")
    pt = r.get("perspective_test") or {}
    print(f"     the plate itself  f^2 = {pt.get('f_squared')} — "
          + ("a consistent single-station perspective" if pt["consistent"]
             else "NOT a consistent perspective: composed by eye"))


def self_test(r, a):
    ok = True
    for name in ("five_bays", "door_is_middle_bay", "annex_is_log_coursed",
                 "logs_coarser_than_clapboard"):
        if not a[name]:
            print(f"   FAIL self-test {name} is false")
            ok = False
    if r["bay_rhythm"]["spread_pct"] < 0:
        print("   FAIL self-test bay spread is negative")
        ok = False
    if ok:
        print("   self-test: the four claims the research note rests on hold")
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
        reading = read_plate()
    except NoReader:
        try:
            reading, live = banked(), False
        except PlateError as exc:
            print(f"   FAIL {exc}")
            return 1
    except PlateError as exc:
        print(f"   FAIL {exc}")
        return 1

    a = assess(reading)
    if args.self_test:
        return self_test(reading, a)
    if args.json:
        print(json.dumps(reading, indent=2, sort_keys=True))
        return 0
    if args.write_baseline:
        if not live:
            print("   FAIL cannot bank a baseline without Pillow and numpy")
            return 1
        BASELINE.write_text(json.dumps({
            "$note": "T-0617. The banked reading of Braunhold's Sauganash engraving by "
                     "tools/measure_sauganash_plate.py. The plate is committed and cannot "
                     "change, so this exists for two reasons: CI installs no image library "
                     "and would otherwise skip the plate half in silence, and a detector "
                     "edit that quietly moves the reading is a thing this project has been "
                     "bitten by (T-0197). Regenerate with --write-baseline, and only ever "
                     "with the reason in the commit.",
            "reading": reading,
        }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        show(reading, a)
        print(f"\n   wrote {BASELINE.name}")
        return 0

    bad = findings(reading, a)
    if live and BASELINE.exists():
        bad += drift(reading, banked())
    if not live and not args.quiet:
        print("   Pillow or numpy is absent, so THE PLATE WAS NOT RE-READ. Standing on the "
              f"banked reading in {BASELINE.name}.")
    if not args.quiet or bad:
        show(reading, a)
    for g in bad:
        print(f"   FAIL {g}")
    if not bad and not args.quiet:
        print("   the plate still says what docs/RESEARCH/sauganash_image_accuracy.md "
              "says it says")
    return 1 if (bad and args.gate) else 0


if __name__ == "__main__":
    sys.exit(main())
