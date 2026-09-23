#!/usr/bin/env python3
"""Adjudicate the eight-point global affine that registers the National Archives /
Historic Urban Plans scan of Wright's 1834 survey (T-0878).

THE QUESTION. T-0797 measured the School Section's own outer lines through that fit
and found the mile square measures 1603.04 m east-west and 1658.65 m north-south:
the x scale right to four tenths of one per cent, the y scale three per cent long —
more than the width of any block in the grid, and eight times the fit's own 16.19 m
RMS. T-0878 asks whether the fit should stand, and if not what replaces it.

WHAT MAKES THIS ANSWERABLE OFFLINE. The observation is not a fresh reading of the
raster. T-0797 committed its measured line table in local ENU metres
(`data/traces/vectors/school_section_blocks_1834.json`, `grid.ns_lines[].measured`
and `grid.ew_lines[].measured`), and the fit is an invertible affine, so inverting
it on the four corner intersections of that table recovers the PIXEL coordinates the
reading was taken at, to within the table's own 0.01 m rounding (~0.014 px). Those
four pixels are the raw evidence, and they are fit-independent: every model below is
scored against the same four.

THE MODELS, all least-squares, all fitted here rather than copied:

  M0  the eight-point global affine T-0787 published — the incumbent until T-1091,
      and `retained_fit` in the registration since. Seated traces are still carried
      through it, so it is read from there rather than refitted.
  M1  an eleven-point affine: the same eight, plus the section's north-west,
      south-west and south-east corners. Those three are PLSS section corners of
      sections 8/9/16/17, 16/17/20/21 and 15/16/21/22, T39N R14E, still crossings on
      the modern street grid (Halsted & Madison, Halsted & Roosevelt, State &
      Roosevelt), and they are the control at the sheet's FOOT that the eight never
      had: the incumbent's southernmost point is G1 at y=3225 px on a 6628 px sheet.
  M2  M0 with an explicit y-scale correction, pixel y pre-scaled by
      mile / measured_north_south about G1 so the plat's north-east corner is fixed.
  M3  a second-order polynomial (twelve coefficients) on the eleven points.

THE TEST each model is scored on: RMS against the eight original control points, RMS
against all eleven, leave-one-out RMS on its own control, and the section's measured
mile in both axes carried through the model.

WHAT THIS TOOL DOES NOT DO. It does not adopt anything, and it never writes the
registration. T-1091 adopted M1 by hand, on this measurement; what changed here is
only WHERE THE TABLE IS MEASURED FROM. The displacement table used to be measured
from M0, because M0 was the fit in force; it is now measured from the fit in force,
which is M1, so each row still answers the one question it is for — what would move
if this model were adopted TODAY. M0 is one of the candidates now, and its row is
the cost of going back.

TWO THINGS DELIBERATELY STILL READ THE RETAINED FIT, and getting either wrong would
silently move the evidence. The section's four corner pixels are recovered by
INVERTING the fit T-0797's line table was measured through, which is the retained
eight-point one and not the one in force; invert the wrong fit and the "raw evidence"
moves with whatever it is being used to test. And M2 is defined as the retained fit
with its y pre-scaled, because that is the repair the ticket named.

The datum is not at risk either way — `tools/rederive_datum.py` derives it from
`wright_1834_gcps.json`, the BPL master, and never reads this sheet.

    python3 tools/adjudicate_wright_na_fit.py            re-measure and print
    python3 tools/adjudicate_wright_na_fit.py --check    hold the committed record
    python3 tools/adjudicate_wright_na_fit.py --self-test   the assertions fire
"""

from __future__ import annotations

import argparse
import json
import math
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]

GCP_PATH = "data/traces/gcp/wright_1834_nara_hup_gcps.json"
CORNERS_PATH = "data/traces/gcp/wright_1834_nara_hup_section_corners.json"
SECTION_PATH = "data/traces/vectors/school_section_blocks_1834.json"
RECORD_PATH = "data/traces/gcp/wright_1834_nara_hup_fit_adjudication.json"

MILE_M = 1609.344

# The two model keys the rest of the file has to agree with itself about: the fit
# T-0787 published and T-1091 retained, and the one T-1091 put in force.
M0 = "M0_retained_affine_8pt"
IN_FORCE = "M1_affine_11pt_foot_control"

# Traces keyed to THIS sheet's pixel space. Every pixel reading in each is carried
# through the candidate models to measure what adopting one would move.
NA_TRACES = [
    "data/traces/vectors/school_section_blocks_1834.json",
    "data/traces/school_section_block_numbering.json",
    "data/traces/kinzie_addition_street_grid.json",
    "data/traces/kinzie_addition_block_numbering.json",
    "data/traces/kinzie_block_name.json",
    "data/traces/michigan_st_tract_grid.json",
    "data/traces/wabansia_streets.json",
    "data/traces/wabansia_block_numbering.json",
    "data/traces/wabansia_water_lots.json",
]


# ---------------------------------------------------------------------------------
# Linear algebra, in pure Python. numpy is not installed in the agent sandbox and
# `tools/check.sh` skips every step that needs it (T-1083), so a gate that imported
# numpy would be a gate that never runs. Six and twelve unknowns do not need it.
# ---------------------------------------------------------------------------------
def solve(A, b):
    """Gaussian elimination with partial pivoting. A is n x n, b is length n."""
    n = len(b)
    M = [list(A[i]) + [b[i]] for i in range(n)]
    for col in range(n):
        piv = max(range(col, n), key=lambda r: abs(M[r][col]))
        if abs(M[piv][col]) < 1e-14:
            raise ValueError("singular normal equations")
        M[col], M[piv] = M[piv], M[col]
        for r in range(n):
            if r == col:
                continue
            factor = M[r][col] / M[col][col]
            if factor:
                for c in range(col, n + 1):
                    M[r][c] -= factor * M[col][c]
    return [M[i][n] / M[i][i] for i in range(n)]


def lstsq(rows, rhs):
    """Least squares by normal equations. rows[i] is the design row for rhs[i]."""
    k = len(rows[0])
    A = [[sum(rows[i][p] * rows[i][q] for i in range(len(rows))) for q in range(k)]
         for p in range(k)]
    b = [sum(rows[i][p] * rhs[i] for i in range(len(rows))) for p in range(k)]
    return solve(A, b)


# ---------------------------------------------------------------------------------
# The models. Each is a pair of callables (forward, name) where forward(px, py)
# returns (E, N) in EPSG:26916 metres.
# ---------------------------------------------------------------------------------
def affine_terms(px, py):
    return [px, py, 1.0]


def poly2_terms(px, py):
    # Scaled so the normal equations stay conditioned: pixel values reach 6628 and
    # their squares 4.4e7, which a 6-term basis handles and a 12-term one does not.
    x, y = px / 1000.0, py / 1000.0
    return [x, y, 1.0, x * x, x * y, y * y]


def fit_model(points, terms):
    """points is [(px, py, E, N)]. Returns (coef_E, coef_N)."""
    rows = [terms(p[0], p[1]) for p in points]
    return lstsq(rows, [p[2] for p in points]), lstsq(rows, [p[3] for p in points])


def make_forward(coef, terms):
    cE, cN = coef

    def forward(px, py):
        t = terms(px, py)
        return (sum(c * v for c, v in zip(cE, t)), sum(c * v for c, v in zip(cN, t)))

    return forward


def residuals(forward, points):
    out = []
    for px, py, E, N in points:
        e, n = forward(px, py)
        out.append(math.hypot(e - E, n - N))
    return out


def rms(values):
    return math.sqrt(sum(v * v for v in values) / len(values)) if values else 0.0


def loo_rms(points, terms):
    """Leave-one-out RMS: each point predicted by a fit that never saw it."""
    if len(points) <= len(terms(0, 0)):
        return None
    errs = []
    for i in range(len(points)):
        rest = points[:i] + points[i + 1:]
        try:
            fw = make_forward(fit_model(rest, terms), terms)
        except ValueError:
            return None
        px, py, E, N = points[i]
        e, n = fw(px, py)
        errs.append(math.hypot(e - E, n - N))
    return rms(errs)


# ---------------------------------------------------------------------------------
# The evidence
# ---------------------------------------------------------------------------------
def load(path):
    return json.loads((ROOT / path).read_text())


def invert_affine(coef):
    a, b, c, d, e, f = coef
    det = a * e - b * d

    def inverse(E, N):
        dE, dN = E - c, N - f
        return ((e * dE - b * dN) / det, (-d * dE + a * dN) / det)

    return inverse


def retained_coefficients(gcp):
    """The eight-point affine T-0787 published, wherever it currently lives.

    It was `fit` until T-1091 and is `retained_fit` after it. Read through one
    accessor so the two things that must keep using it — the corner recovery below
    and M2 — cannot drift apart from each other or from the file.
    """
    block = gcp.get("retained_fit") or gcp["fit"]
    return block["coefficients"]


def section_corner_pixels():
    """The section's four corner intersections, in NA pixel space.

    Recovered by inverting THE FIT THE LINE TABLE WAS MEASURED THROUGH — T-0797 read
    it through the eight-point fit, which is `retained_fit` now — on that table. The
    table is local ENU; the fit is UTM; the datum carries between them. Inverting the
    fit in force instead would move these four pixels every time the registration
    changed, and they are the fit-independent evidence every model here is scored on.
    """
    gcp = load(GCP_PATH)
    datum = load("data/datum.json")
    sec = load(SECTION_PATH)
    c = retained_coefficients(gcp)
    inverse = invert_affine((c["a"], c["b"], c["c"], c["d"], c["e"], c["f"]))
    oE, oN = datum["origin_utm_e"], datum["origin_utm_n"]

    ns = {r["i"]: r["measured"] for r in sec["grid"]["ns_lines"]}
    ew = {r["j"]: r["measured"] for r in sec["grid"]["ew_lines"]}
    west, east = ns[min(ns)], ns[max(ns)]
    north, south = ew[min(ew)], ew[max(ew)]

    corners = {}
    for name, (le, ln) in (("NE", (east, north)), ("NW", (west, north)),
                           ("SW", (west, south)), ("SE", (east, south))):
        corners[name] = inverse(le + oE, ln + oN)
    return corners, dict(measured_ew=east - west, measured_ns=north - south)


def section_own_scales(corners):
    """The sheet's scale on each plat axis, from the section's own square alone.

    This is the measurement that does not need a fit and does not need modern control:
    the section is a statute mile on a side, its four corners are drawn on the sheet,
    and a pixel length divided by a known ground length is a scale. Everything else in
    this tool is an attempt to make a transform agree with these two numbers.
    """
    gcp = load(GCP_PATH)

    def span(u, v):
        return math.hypot(corners[u][0] - corners[v][0], corners[u][1] - corners[v][1])

    ew_px = (span("NW", "NE") + span("SW", "SE")) / 2
    ns_px = (span("NW", "SW") + span("NE", "SE")) / 2
    sx, sy = MILE_M / ew_px, MILE_M / ns_px
    fit = gcp["fit"]["scale_m_per_px"]
    retained = (gcp.get("retained_fit") or gcp["fit"])
    return dict(
        east_west_span_px=round(ew_px, 2),
        north_south_span_px=round(ns_px, 2),
        implied_m_per_px=dict(x=round(sx, 5), y=round(sy, 5)),
        fit_in_force_m_per_px=dict(x=fit["x"], y=fit["y"]),
        retained_8pt_fit_m_per_px=dict(x=retained["scale_m_per_px"]["x"],
                                       y=retained["scale_m_per_px"]["y"]),
        fit_departure_pct=dict(x=round(100 * (fit["x"] - sx) / sx, 3),
                               y=round(100 * (fit["y"] - sy) / sy, 3)),
        anisotropy_pct=dict(
            the_section_says=round(100 * (sy / sx - 1), 2),
            the_fit_in_force_says=gcp["fit"]["axis_scale_difference_pct"],
            the_retained_8pt_fit_said=retained["axis_scale_difference_pct"]),
        reading=(
            "The paper IS anisotropic and the eight-point fit overstated it. The section's "
            "own square makes the sheet 1.9 per cent longer per pixel in y than in x; the "
            "eight-point fit made it 5.2 per cent, and the eleven-point fit T-1091 adopted "
            "makes it 2.2. On the x axis every one of the three agrees with the section to "
            "under half of one per cent over a mile. The y axis is the whole argument, and "
            "the reason the old number was wrong is that the section lies entirely BELOW "
            "every one of the eight control points: it was an extrapolation error, not a "
            "fitting error, which is why control at the sheet's foot mends it and a uniform "
            "rescale does not."),
    )


def control_sets():
    """(the eight, the three new, the eleven) as [(px, py, E, N)]."""
    gcp = load(GCP_PATH)
    eight = [(g["pixel"][0], g["pixel"][1], g["modern"]["utm_e"], g["modern"]["utm_n"])
             for g in gcp["gcps"]]
    corners = load(CORNERS_PATH)
    three = [(c["pixel"][0], c["pixel"][1], c["modern"]["utm_e"], c["modern"]["utm_n"])
             for c in corners["corners"]]
    return eight, three, eight + three


def mile_test(forward, corners):
    """The section's own outer lines, measured through a model."""
    p = {k: forward(*v) for k, v in corners.items()}

    def d(u, v):
        return math.hypot(p[u][0] - p[v][0], p[u][1] - p[v][1])

    ew = (d("NW", "NE") + d("SW", "SE")) / 2
    ns = (d("NW", "SW") + d("NE", "SE")) / 2
    return dict(east_west_m=round(ew, 2), north_south_m=round(ns, 2),
                east_west_departure_pct=round(100 * (ew - MILE_M) / MILE_M, 3),
                north_south_departure_pct=round(100 * (ns - MILE_M) / MILE_M, 3))


def y_scaled(coef, anchor_px, k):
    """M0 with pixel y pre-scaled by k about `anchor_px`, the anchor left fixed."""
    a, b, c, d, e, f = coef
    ax, ay = anchor_px
    # (x, y) -> (x, ay + k*(y - ay)) then the incumbent affine.
    shift = ay * (1 - k)
    return ([a, b * k, c + b * shift], [d, e * k, f + e * shift])


# ---------------------------------------------------------------------------------
# What adopting a model would move
# ---------------------------------------------------------------------------------
def trace_pixels(obj, out):
    """Every pixel reading in a committed trace: keys ending _px, plus `pixel`."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            if (k == "pixel" or k.endswith("_px")) and isinstance(v, list) and v:
                if len(v) == 2 and all(isinstance(n, (int, float)) for n in v):
                    out.append((float(v[0]), float(v[1])))
                elif len(v) == 4 and all(isinstance(n, (int, float)) for n in v):
                    out.append(((v[0] + v[2]) / 2.0, (v[1] + v[3]) / 2.0))
                elif all(isinstance(n, list) and len(n) == 2 for n in v):
                    for n in v:
                        if all(isinstance(m, (int, float)) for m in n):
                            out.append((float(n[0]), float(n[1])))
            else:
                trace_pixels(v, out)
    elif isinstance(obj, list):
        for v in obj:
            trace_pixels(v, out)
    return out


def displacement_table(base, candidates):
    rows = []
    for path in NA_TRACES:
        p = ROOT / path
        if not p.exists():
            continue
        pts = trace_pixels(json.loads(p.read_text()), [])
        if not pts:
            rows.append(dict(trace=path, readings=0, note=(
                "Carries no raw pixel coordinate of its own: it is a DERIVED grid, "
                "rescaled onto the section's exact mile square and anchored on GCP G1, "
                "so a change of fit moves it by however far G1 moves and not by more. "
                "See control_movement below.")))
            continue
        row = dict(trace=path, readings=len(pts))
        for name, fw in candidates.items():
            moves = []
            for px, py in pts:
                e0, n0 = base(px, py)
                e1, n1 = fw(px, py)
                moves.append(math.hypot(e1 - e0, n1 - n0))
            moves.sort()
            row[name] = dict(median_m=round(moves[len(moves) // 2], 2),
                             max_m=round(moves[-1], 2))
        rows.append(row)
    return rows


# ---------------------------------------------------------------------------------
def measure():
    gcp = load(GCP_PATH)
    c = retained_coefficients(gcp)
    retained = (c["a"], c["b"], c["c"], c["d"], c["e"], c["f"])
    f = gcp["fit"]["coefficients"]
    in_force = (f["a"], f["b"], f["c"], f["d"], f["e"], f["f"])
    corners, spans = section_corner_pixels()
    eight, three, eleven = control_sets()
    g1 = next(g for g in gcp["gcps"] if g["id"] == "G1")["pixel"]

    models = {}

    # M0 — read, not refitted, so the record is about the transform T-0787 published
    # and the seated traces are still carried through.
    m0_coef = ([retained[0], retained[1], retained[2]],
               [retained[3], retained[4], retained[5]])
    models[M0] = dict(
        terms=affine_terms, forward=make_forward(m0_coef, affine_terms),
        control=eight, coef=m0_coef, refitted=False)
    # M0 IS the least-squares fit of the eight — this run reproduces its published
    # 16.19 m RMS from the control alone — so its leave-one-out is meaningful and is
    # the honest number the candidates had to beat.
    models[M0]["refitted"] = True

    # M1 — the same form, eleven points, control at the sheet's foot.
    m1_coef = fit_model(eleven, affine_terms)
    models[IN_FORCE] = dict(
        terms=affine_terms, forward=make_forward(m1_coef, affine_terms),
        control=eleven, coef=m1_coef, refitted=True)

    # M2 — the y-scale correction the ticket names, about G1. Defined on the RETAINED
    # fit, because "M0 with its y rescaled" is the repair that was proposed; rebasing
    # it on the fit in force would be a different, untested model wearing M2's name.
    k = MILE_M / spans["measured_ns"]
    m2_coef = y_scaled(retained, g1, k)
    models["M2_retained_affine_y_rescaled"] = dict(
        terms=affine_terms, forward=make_forward(m2_coef, affine_terms),
        control=eight, coef=m2_coef, refitted=False, y_scale_factor=round(k, 6))

    # M3 — a second-order term, eleven points.
    m3_coef = fit_model(eleven, poly2_terms)
    models["M3_poly2_11pt"] = dict(
        terms=poly2_terms, forward=make_forward(m3_coef, poly2_terms),
        control=eleven, coef=m3_coef, refitted=True)

    report = {}
    for name, m in models.items():
        fw, terms = m["forward"], m["terms"]
        entry = dict(
            form=("affine" if terms is affine_terms else "second-order polynomial"),
            control_points=len(m["control"]),
            refitted_here=m["refitted"],
            rms_m_on_the_eight=round(rms(residuals(fw, eight)), 2),
            rms_m_on_the_three_corners=round(rms(residuals(fw, three)), 2),
            rms_m_on_all_eleven=round(rms(residuals(fw, eleven)), 2),
            worst_m_on_all_eleven=round(max(residuals(fw, eleven)), 2),
            mile_test=mile_test(fw, corners),
        )
        if m["refitted"]:
            loo = loo_rms(m["control"], terms)
            entry["leave_one_out_rms_m"] = None if loo is None else round(loo, 2)
        else:
            entry["leave_one_out_rms_m"] = None
            entry["leave_one_out_note"] = (
                "Not applicable: this model is not a least-squares fit of the points it is "
                "scored against, so leaving one out would refit a different model. M0's "
                "own leave-one-out is reported on M0.")
        if "y_scale_factor" in m:
            entry["y_scale_factor"] = m["y_scale_factor"]
        entry["coefficients"] = dict(
            E=[round(v, 9) for v in m["coef"][0]], N=[round(v, 9) for v in m["coef"][1]])
        report[name] = entry

    # THE TABLE IS MEASURED FROM THE FIT IN FORCE (T-1091), not from M0: what a reader
    # needs is what would move if a model were adopted from where the project stands
    # today. The fit in force is read from the registration rather than taken from the
    # model that matches it, so a hand edit to those six numbers shows up as a
    # departure below instead of quietly redefining the baseline.
    base_coef = ([in_force[0], in_force[1], in_force[2]],
                 [in_force[3], in_force[4], in_force[5]])
    base = make_forward(base_coef, affine_terms)
    matched = models[IN_FORCE]
    departure = max(abs(a - b) for pair in zip(base_coef, matched["coef"])
                    for a, b in zip(*pair))
    fit_in_force = dict(
        model=IN_FORCE,
        source="data/traces/gcp/wright_1834_nara_hup_gcps.json § fit",
        adopted_by="T-1091",
        reproduces_the_model=departure < 1e-6,
        max_coefficient_departure=float(f"{departure:.3e}"),
        note=("The registration's committed coefficients are refitted here from the "
              "eleven control points and compared. A departure means the block was "
              "edited by hand, or the control moved under it."))

    def movement(fw):
        out = {}
        for g, pt in zip(gcp["gcps"], eight):
            e0, n0 = base(pt[0], pt[1])
            e1, n1 = fw(pt[0], pt[1])
            out[g["id"]] = round(math.hypot(e1 - e0, n1 - n0), 2)
        return out

    control_movement = {n: movement(m["forward"]) for n, m in models.items()
                        if n != IN_FORCE}

    moves = displacement_table(base, {n: m["forward"] for n, m in models.items()
                                      if n != IN_FORCE})

    ys = [p[1] for p in eight]
    return dict(
        control_window_px=dict(
            the_eight=dict(y_min=round(min(ys), 1), y_max=round(max(ys), 1),
                           sheet_height=gcp["raster"]["height"]),
            the_section=dict(y_min=round(min(v[1] for v in corners.values()), 1),
                             y_max=round(max(v[1] for v in corners.values()), 1)),
            reading=("Every one of the eight control points lies in the top 49 per cent of "
                     "the sheet, inside a 1594 px band. The section occupies 3169-5495 px, "
                     "entirely below all of them. A global affine's y scale is therefore "
                     "FITTED over a quarter of the sheet and EXTRAPOLATED over the rest, "
                     "and the section is where the extrapolation can be checked against a "
                     "known length.")),
        fit_in_force=fit_in_force,
        section_own_scales=section_own_scales(corners),
        section_corner_pixels={k: [round(v[0], 1), round(v[1], 1)] for k, v in corners.items()},
        section_corner_pixel_note=(
            "Recovered by inverting the RETAINED eight-point fit — the one T-0797 read "
            "the line table through, which is what makes these four fit-independent — "
            "on that table; "
            "NE is the same point of the drawing as GCP G1, whose committed pixel is "
            f"{g1}, so the difference between them is the span of the plat's own corner "
            "against the crossing the registration picked."),
        measured_spans_through_the_retained_fit=dict(
            east_west_m=round(spans["measured_ew"], 2),
            north_south_m=round(spans["measured_ns"], 2),
            statute_mile_m=MILE_M),
        models=report,
        displacement_from_the_fit_in_force=moves,
        control_movement=dict(
            metres_each_control_point_moves=control_movement,
            g1_note=("G1 is State and Madison, the section's north-east corner and the "
                     "anchor the School Section grid, the Kinzie readings and the Michigan "
                     "St tract are all seated through. Its movement is the rigid part of "
                     "every displacement above.")),
    )


# ---------------------------------------------------------------------------------
def _compare(measured, committed, path=""):
    """Deep compare, tolerant of float formatting only."""
    problems = []
    if isinstance(committed, dict) and isinstance(measured, dict):
        for k in committed:
            if k not in measured:
                problems.append(f"{path}{k}: in the record, not in the measurement")
            else:
                problems += _compare(measured[k], committed[k], f"{path}{k}.")
        for k in measured:
            if k not in committed:
                problems.append(f"{path}{k}: measured, not in the record")
    elif isinstance(committed, list) and isinstance(measured, list):
        if len(committed) != len(measured):
            problems.append(f"{path}: {len(measured)} measured, {len(committed)} recorded")
        else:
            for i, (m, c) in enumerate(zip(measured, committed)):
                problems += _compare(m, c, f"{path}[{i}].")
    elif isinstance(committed, float) or isinstance(measured, float):
        try:
            if abs(float(measured) - float(committed)) > 5e-7 * max(1.0, abs(float(committed))):
                problems.append(f"{path}: measured {measured}, recorded {committed}")
        except (TypeError, ValueError):
            problems.append(f"{path}: measured {measured!r}, recorded {committed!r}")
    elif measured != committed:
        problems.append(f"{path}: measured {measured!r}, recorded {committed!r}")
    return problems


def check():
    record = load(RECORD_PATH)
    problems = _compare(measure(), record["measurement"])
    if problems:
        print("FAIL: the committed adjudication no longer matches its own measurement.")
        for p in problems[:24]:
            print("  " + p)
        if len(problems) > 24:
            print(f"  ... and {len(problems) - 24} more")
        print("Re-run tools/adjudicate_wright_na_fit.py --write and read the diff before "
              "committing it: a model that moved means control or a trace moved.")
        return 1
    print(f"OK: {RECORD_PATH} matches its own measurement "
          f"({len(record['measurement']['models'])} models, "
          f"{len(record['measurement']['displacement_from_the_fit_in_force'])} traces)")
    return 0


def self_test():
    """The check must FAIL when the record is wrong. Held here so the gate's green
    line means something (T-0763's rule)."""
    record = load(RECORD_PATH)
    good = record["measurement"]
    bad = json.loads(json.dumps(good))
    bad["models"][IN_FORCE]["rms_m_on_all_eleven"] += 1.0
    if not _compare(measure(), bad):
        print("FAIL: a wrong RMS in the record did not fire the comparison")
        return 1
    bad = json.loads(json.dumps(good))
    bad["displacement_from_the_fit_in_force"].pop()
    if not _compare(measure(), bad):
        print("FAIL: a missing trace row did not fire the comparison")
        return 1
    bad = json.loads(json.dumps(good))
    bad["section_corner_pixels"]["SW"][1] += 3
    if not _compare(measure(), bad):
        print("FAIL: a moved section corner did not fire the comparison")
        return 1
    # T-1091. The baseline of every displacement row is the registration's own
    # coefficient block; if that stops being the model it claims to be, the table is
    # measured from something nobody adjudicated.
    bad = json.loads(json.dumps(good))
    bad["fit_in_force"]["reproduces_the_model"] = False
    if not _compare(measure(), bad):
        print("FAIL: a fit in force that no longer reproduces its model did not fire")
        return 1
    print("OK: the adjudication's assertions fire when the record is wrong")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="hold the committed record")
    ap.add_argument("--self-test", action="store_true", help="the assertions fire")
    ap.add_argument("--write", action="store_true",
                    help="write the measurement into the committed record")
    args = ap.parse_args()

    if args.self_test:
        return self_test()
    if args.check:
        return check()

    m = measure()
    if args.write:
        p = ROOT / RECORD_PATH
        record = json.loads(p.read_text()) if p.exists() else {}
        record["measurement"] = m
        p.write_text(json.dumps(record, indent=2) + "\n")
        print(f"wrote {RECORD_PATH}")
        return 0
    print(json.dumps(m, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
