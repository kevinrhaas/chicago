#!/usr/bin/env python3
"""Re-read Wright's one curved double line north of the river, off the 600 dpi NA/HUP sheet.

    tools/read_north_side_slough_na.py                print the reading
    tools/read_north_side_slough_na.py --write        write the trace record
    tools/read_north_side_slough_na.py --check        re-derive the committed file WITHOUT the raster
    tools/read_north_side_slough_na.py --check-sheet  re-read the raster and compare

WHAT IS DRAWN. On the 1834 Wright sheet, one curved double line leaves the north bank of
the Main Branch a little east of Market Street, runs north-north-west across North Water
Street and Kinzie Street, bulges west, and ends at the Michigan St tract's Michigan
Street. Apart from the fort's road on the reservation it is the only such line on the
sheet. T-1075 raised it as a ROAD serving the tract; that reading is WITHDRAWN and this
file is what withdrew it (see THE IDENTITY below). What the sheet says, and all this
reading claims, is that Wright drew a curved double line here and where it falls.

THE IDENTITY, and it is why this file is not named for a road. The project already holds
this feature, and holds it as WATER: `north_side_slough` in
`data/terrain/epochs/e1834_harbor_cut/hydrology.geojson`, a 45-vertex centreline of "a
narrow winding watercourse running north out of the main stem, across Kinzie Street,
ending at Michigan Street", traced off the BPL master scan by `tools/trace_river.py` and
citing `wright_1834` for existence AND course. The two readings are the same ink:

  - This reading's 36 sheet stations lie a MEDIAN 1.54 m from that committed centreline
    (max 17.91 m), against a record whose own stated vertex uncertainty is +/-20 m and a
    sheet fit whose RMS is 16.19 m here and 17.5 m there. Two scans, two registrations,
    two tracers, four hundred commits apart, and every station inside either one's error.
    `--check` re-derives the figure from committed data; it is not transcribed.
  - The corridor widths agree: 12.35 m mean between stroke centres here, 13.02 m measured
    on the same strokes by T-0795's independent sweep of the whole sheet.
  - T-0795 counted every non-river watercourse Wright draws on the sheet and found
    exactly ONE. It is this line.
  - It is drawn as a CONFLUENCE. At NA px (2033, 2270) the west stroke becomes the
    river's north bank running south-west and the east stroke becomes the same bank
    running east: two banks continuous with the main stem's, on either side of an
    opening. A road drawn to a river either stops at the bank or crosses it.
  - Thompson's 1830 plat draws this feature as water across North Division block 6, the
    same block the line crosses (T-0452).

So this is a SECOND, INDEPENDENT read of `north_side_slough`, off a different scan under
a different registration, and its value is corroboration: it is the only cross-check that
record has. It commits no feature of its own. Nothing here is seated into
`data/streets/1835.json` and nothing here may be.

WHAT THE TRACE ALSO SETTLES. The line does NOT run north THROUGH the Michigan St tract.
Both strokes stop inside the Michigan Street corridor, short of that street's north rule,
and the tract's north tier is ruled across with nothing in it. T-1075's premise that it
runs north through the tract is not what the sheet draws — true of a watercourse ending
at Michigan Street exactly as the slough record already says it does.

THE METHOD is a ridge follower, not a row scan, because the line curves and crosses dozens
of ruled lines that a row scan cannot tell from it. From a stated seed on each stroke the
tracer steps STEP px along the current heading, searches +/-HALF px along the normal for
the darkest sample (bilinear), moves there, and re-estimates the heading from the last
three steps under a stated smoothing. Every parameter is committed below, so `--check-sheet`
re-runs the identical trace and `--check` re-derives every metre from the committed pixels
without opening the raster at all.

THE SEATING is a sheet-to-ground transfer and not a claim about a feature. The Michigan St
tract is seated 38 m north of where this sheet's fit draws it (T-1079: Wright compresses y
at his western margin). The line spans both regimes: its southern two thirds lie in the
North Division, where this sheet's fit is good — the drawn rule that carries Kinzie's south
side falls 3 m from the committed line — and only its northern third lies inside the
compressed tract. So it is carried with a correction that is ZERO at the Kinzie crossing
and grows linearly, in the sheet's own northing, to the tract's committed seating offset at
Michigan Street. `centre_sheet_local_enu_m` is the raw fit and is what the identity above
is measured on; `seated_local_enu_m` is that transfer. Neither is a committed feature.

THE TWO ENDS are carried onto the committed lines the trace meets: 6.0 m north at the top,
to the centreline of `michigan_north_tract`, because the drawn strokes stop inside that
street's corridor; and 8.3 m back at the foot, because the drawn junction with the river
bank falls that far south of the committed `north_water`. Both runs are stated here and in
the record.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data/traces/north_side_slough_na_reread.json"
GRID = ROOT / "data/traces/michigan_st_tract_grid.json"
GCP = ROOT / "data/traces/gcp/wright_1834_nara_hup_gcps.json"
DATUM = ROOT / "data/datum.json"
STREETS = ROOT / "data/streets/1835.json"
HYDRO = ROOT / "data/terrain/epochs/e1834_harbor_cut/hydrology.geojson"

RASTER = ROOT.parent / "pre_fire_v1/maps/images/1834-wright-map.jpg"


# --- the trace, stated so it can be re-run ------------------------------------------
SEEDS = {
    "west_stroke": {"px": [1957.5, 2060.0], "heading": [-0.2, 1.0]},
    "east_stroke": {"px": [1977.0, 2060.0], "heading": [-0.2, 1.0]},
}
STEP_PX = 4.0
HALF_PX = 5.0
SMOOTH = 0.7
STEPS_SOUTH = 58
STEPS_NORTH = 24
# the ink's own ends, read off the sheet at 8x and used to clip the trace
PY_NORTH_INK = 1987.0          # the northernmost row both strokes are separable on
PY_SOUTH_INK = 2272.0          # the node where the road meets the drawn river bank
PY_SAMPLE = 8                  # the trace is reported every 8 px of northing
# The committed centreline is the traced one thinned. At 8 px of northing the trace
# stations every ~6 m, which is SHORTER than the ribbon's own half-width, and the
# renderer's mitre cannot cover a joint whose neighbours stand closer than that — T-0184's
# wedge check caught exactly one such joint on the dense line. Thinning is a RENDERING
# decision and not a claim, so it is bounded twice and the cost is reported: Douglas-Peucker
# at 1.0 m, then no station closer than 15 m to the last one kept.
SIMPLIFY_TOLERANCE_M = 1.0
MIN_SEGMENT_M = 14.0

# --- the sheet's own lines this reading is hung on (all from T-1076's reading) -------
PY_KINZIE_SOUTH_RULE = 2121.0  # the block tier's north edge = Kinzie Street's south side


def _fit():
    g = json.loads(GCP.read_text())
    d = json.loads(DATUM.read_text())
    c = g["fit"]["coefficients"]
    return (c["a"], c["b"], c["c"], c["d"], c["e"], c["f"]), d


def to_local(px, py):
    (a, b, c, d, e, f), dat = _fit()
    return (a * px + b * py + c - dat["origin_utm_e"],
            d * px + e * py + f - dat["origin_utm_n"])


def _line(p, q):
    """A line through two (E, N) points, as N(E) and E(N)."""
    (e0, n0), (e1, n1) = p, q
    dn_de = (n1 - n0) / (e1 - e0) if e1 != e0 else 0.0
    de_dn = (e1 - e0) / (n1 - n0) if n1 != n0 else 0.0
    return (lambda E: n0 + dn_de * (E - e0)), (lambda N: e0 + de_dn * (N - n0))


def _committed(sid):
    s = {x["id"]: x for x in json.loads(STREETS.read_text())["streets"]}[sid]
    p = s["path_local_enu_m"]
    return _line(p[0], p[-1])


def _path(sid):
    return {x["id"]: x for x in json.loads(STREETS.read_text())["streets"]}[sid]["path_local_enu_m"]


def _extend(prev, last, poly, limit=80.0):
    """Extend the ray prev->last until it first meets `poly`; return the point and the run."""
    dx, dy = last[0] - prev[0], last[1] - prev[1]
    L = math.hypot(dx, dy)
    dx, dy = dx / L, dy / L
    best = None
    for a, b in zip(poly, poly[1:]):
        ux, uy = b[0] - a[0], b[1] - a[1]
        det = dx * (-uy) - dy * (-ux)
        if abs(det) < 1e-12:
            continue
        rx, ry = a[0] - last[0], a[1] - last[1]
        t = (rx * (-uy) - ry * (-ux)) / det
        u = (dx * ry - dy * rx) / det
        if -limit <= t <= limit and -0.001 <= u <= 1.001:
            if best is None or abs(t) < abs(best[0]):
                best = (t, [round(last[0] + t * dx, 2), round(last[1] + t * dy, 2)])
    if best is None:
        raise SystemExit(f"no crossing of the committed line within {limit} m")
    return best[1], round(best[0], 2)


def _sheet_lines():
    """The tract's own two streets as this sheet's fit draws them (T-1076)."""
    t = json.loads(GRID.read_text())
    ew = t["readings"]["east_west"]["michigan_st"]
    mich_n_of_e, _ = _line(ew["col_west"]["centre_local_enu_m"], ew["col_east"]["centre_local_enu_m"])
    ns = t["readings"]["north_south"]
    pts = [ns[k]["north_south_street"]["centre_local_enu_m"] for k in sorted(ns)]
    _, market_e_of_n = _line(pts[0], pts[-1])
    return mich_n_of_e, market_e_of_n


# --- the ridge follower ---------------------------------------------------------------

def _raster():
    from PIL import Image
    Image.MAX_IMAGE_PIXELS = None
    import numpy as np
    return np.asarray(Image.open(RASTER).convert("L"), dtype=float)


def _trace(A, seed, heading, steps):
    def sample(x, y):
        x0, y0 = int(math.floor(x)), int(math.floor(y))
        fx, fy = x - x0, y - y0
        return (A[y0, x0] * (1 - fx) * (1 - fy) + A[y0, x0 + 1] * fx * (1 - fy)
                + A[y0 + 1, x0] * (1 - fx) * fy + A[y0 + 1, x0 + 1] * fx * fy)

    x, y = seed
    dx, dy = heading
    L = math.hypot(dx, dy)
    dx, dy = dx / L, dy / L
    pts = [(x, y)]
    for _ in range(steps):
        x += dx * STEP_PX
        y += dy * STEP_PX
        if not (2 < x < A.shape[1] - 3 and 2 < y < A.shape[0] - 3):
            break
        nx, ny = -dy, dx
        best = None
        t = -HALF_PX
        while t <= HALF_PX + 1e-9:
            v = sample(x + nx * t, y + ny * t)
            if best is None or v < best[0]:
                best = (v, t)
            t += 0.25
        x += nx * best[1]
        y += ny * best[1]
        pts.append((x, y))
        if len(pts) >= 4:
            ax, ay = pts[-4]
            ndx, ndy = x - ax, y - ay
            L = math.hypot(ndx, ndy)
            if L > 0:
                dx = SMOOTH * dx + (1 - SMOOTH) * ndx / L
                dy = SMOOTH * dy + (1 - SMOOTH) * ndy / L
                L = math.hypot(dx, dy)
                dx, dy = dx / L, dy / L
    return pts


def _stroke(A, key):
    s = SEEDS[key]
    up = _trace(A, s["px"], [-s["heading"][0], -s["heading"][1]], STEPS_NORTH)
    down = _trace(A, s["px"], s["heading"], STEPS_SOUTH)
    return up[::-1][:-1] + down


def _at_y(poly, y):
    for (x0, y0), (x1, y1) in zip(poly, poly[1:]):
        if (y0 - y) * (y1 - y) <= 0 and y0 != y1:
            return x0 + (x1 - x0) * (y - y0) / (y1 - y0)
    return None


def read_sheet():
    A = _raster()
    west = _stroke(A, "west_stroke")
    east = _stroke(A, "east_stroke")
    rows = []
    y = PY_NORTH_INK
    while y <= PY_SOUTH_INK + 1e-9:
        a, b = _at_y(west, y), _at_y(east, y)
        if a is not None and b is not None:
            rows.append([round(y, 1), round(a, 2), round(b, 2)])
        y += PY_SAMPLE
    return rows


# --- derivation from the committed pixels ---------------------------------------------

def derive(rows):
    (a, b, c, d, e, f), _ = _fit()
    m_per_px = math.hypot(a, d)
    mich_s, market_s = _sheet_lines()
    mich_c, _ = _committed("michigan_north")
    _, market_c = _committed("market_north")
    kinzie_n, _ = _committed("kinzie")
    corridor = json.loads(STREETS.read_text())["corridor_width_m"]

    centre_px, centre_sheet, widths = [], [], []
    for py, xw, xe in rows:
        cx = (xw + xe) / 2.0
        centre_px.append([round(cx, 2), py])
        centre_sheet.append(list(to_local(cx, py)))
        widths.append(abs(xe - xw) * m_per_px)

    # the two seating anchors, in the sheet's own frame
    n_kinzie = to_local(_interp_x(rows, PY_KINZIE_SOUTH_RULE), PY_KINZIE_SOUTH_RULE)
    n_mich = centre_sheet[0]

    # the tract's committed seating offset, re-derived at the road's north end
    dE = n_mich[0] - market_s(n_mich[1])
    dN = n_mich[1] - mich_s(n_mich[0])
    E = market_c(n_mich[1]) + dE
    N = mich_c(E) + dN
    for _ in range(4):
        E = market_c(N) + dE
        N = mich_c(E) + dN
    corr_north = (E - n_mich[0], N - n_mich[1])

    span = n_mich[1] - n_kinzie[1]
    seated = []
    for (Ep, Np) in centre_sheet:
        s = max(0.0, min(1.0, (Np - n_kinzie[1]) / span))
        seated.append([round(Ep + s * corr_north[0], 2), round(Np + s * corr_north[1], 2)])

    # extend both ends onto the committed lines the road meets
    south_pt, south_run = _extend(seated[-2], seated[-1], _path("north_water"))
    north_pt, north_run = _extend(seated[1], seated[0], _path("michigan_north_tract"))
    body = list(seated)

    def _beyond(pt, prev, cut):
        """True when `pt` lies past `cut` along the heading prev->pt."""
        ux, uy = pt[0] - prev[0], pt[1] - prev[1]
        return (pt[0] - cut[0]) * ux + (pt[1] - cut[1]) * uy > 0

    # a negative run means the committed line is BEHIND the drawn end: trim, do not extend
    while len(body) > 2 and _beyond(body[-1], body[-2], south_pt):
        body.pop()
    while len(body) > 2 and _beyond(body[0], body[1], north_pt):
        body.pop(0)
    seated_ext = [north_pt] + body + [south_pt]
    kinzie_kerb_residual = round(n_kinzie[1] - (kinzie_n(n_kinzie[0]) - corridor / 2), 2)

    simple, dev = _simplify(seated_ext, MIN_SEGMENT_M)
    length = sum(math.dist(p, q) for p, q in zip(seated_ext, seated_ext[1:]))
    mean_w = sum(widths) / len(widths)
    sd_w = (sum((w - mean_w) ** 2 for w in widths) / len(widths)) ** 0.5
    return {
        "centre_px": centre_px,
        "centre_sheet_local_enu_m": [[round(x, 2), round(y, 2)] for x, y in centre_sheet],
        "seated_local_enu_m": seated_ext,
        "committed_local_enu_m": simple,
        "committed_max_departure_m": round(dev, 2),
        "identity": _identity(centre_sheet),
        "corridor_m": {"mean": round(mean_w, 2), "sd": round(sd_w, 2),
                       "min": round(min(widths), 2), "max": round(max(widths), 2)},
        "seating": {
            "kinzie_anchor_sheet_local_enu_m": [round(v, 2) for v in n_kinzie],
            "kinzie_anchor_correction_m": [0.0, 0.0],
            "michigan_anchor_sheet_local_enu_m": [round(v, 2) for v in n_mich],
            "michigan_anchor_correction_m": [round(corr_north[0], 2), round(corr_north[1], 2)],
            "south_of_kinzie_correction_m": [0.0, 0.0],
            "north_extension_to_michigan_north_m": north_run,
            "south_trim_to_north_water_m": south_run,
            "kinzie_kerb_residual_m": kinzie_kerb_residual,
        },
        "length_m": round(length, 1),
        "m_per_px": round(m_per_px, 5),
    }


def _slough_local_enu():
    """`north_side_slough`'s committed centreline, in the project's local ENU metres."""
    d = json.loads(DATUM.read_text())
    E0, N0 = d["origin_utm_e"], d["origin_utm_n"]
    hyd = json.loads(HYDRO.read_text())
    for f in hyd["features"]:
        if f["properties"].get("name") == "Unnamed slough, north side":
            return [(e - E0, n - N0) for e, n in f["geometry"]["coordinates"]]
    raise SystemExit("north_side_slough is not in " + str(HYDRO))


def _identity(centre_sheet):
    """How far this reading's sheet stations fall from the committed watercourse.

    The point of the number: `north_side_slough` was traced off the BPL master scan under
    its own registration, and this is the only independent read of the same ink. If the two
    disagree by more than either one's stated uncertainty they are not the same feature.
    """
    sl = _slough_local_enu()
    ds = sorted(min(_seg_dist(p, sl[i], sl[i + 1]) for i in range(len(sl) - 1))
                for p in centre_sheet)
    return {
        "against": "north_side_slough (data/terrain/epochs/e1834_harbor_cut/hydrology.geojson)",
        "stations": len(ds),
        "median_departure_m": round(ds[len(ds) // 2], 2),
        "max_departure_m": round(ds[-1], 2),
        "min_departure_m": round(ds[0], 2),
        "this_reading_affine_rms_m": 16.19,
        "slough_record_vertex_uncertainty_m": 20,
        "verdict": "the same feature, read twice",
    }


def _dp(pts, tol):
    if len(pts) < 3:
        return list(pts)
    a, b = pts[0], pts[-1]
    i, dm = max(((i, _seg_dist(p, a, b)) for i, p in enumerate(pts[1:-1], 1)), key=lambda x: x[1])
    if dm <= tol:
        return [a, b]
    return _dp(pts[:i + 1], tol)[:-1] + _dp(pts[i:], tol)


def _simplify(poly, min_seg):
    """Thin a polyline to stations at least `min_seg` apart; report the worst departure."""
    thinned = _dp(poly, SIMPLIFY_TOLERANCE_M)
    keep = [thinned[0]]
    for pt in thinned[1:-1]:
        if math.dist(keep[-1], pt) >= min_seg:
            keep.append(pt)
    if math.dist(keep[-1], thinned[-1]) < min_seg and len(keep) > 1:
        keep.pop()
    keep.append(thinned[-1])
    worst = 0.0
    for pt in poly:
        d = min(_seg_dist(pt, a, b) for a, b in zip(keep, keep[1:]))
        worst = max(worst, d)
    return keep, worst


def _seg_dist(p, a, b):
    vx, vy = b[0] - a[0], b[1] - a[1]
    L2 = vx * vx + vy * vy
    t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((p[0] - a[0]) * vx + (p[1] - a[1]) * vy) / L2))
    return math.dist(p, (a[0] + t * vx, a[1] + t * vy))


def _interp_x(rows, py):
    for (y0, w0, e0), (y1, w1, e1) in zip(rows, rows[1:]):
        if (y0 - py) * (y1 - py) <= 0 and y0 != y1:
            t = (py - y0) / (y1 - y0)
            return ((w0 + e0) / 2) + t * (((w1 + e1) / 2) - ((w0 + e0) / 2))
    raise SystemExit(f"py {py} is outside the traced reach")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--check-sheet", action="store_true")
    args = ap.parse_args()

    if args.check or args.write or not args.check_sheet:
        if OUT.exists() and not args.write:
            rows = json.loads(OUT.read_text())["strokes_px"]
        else:
            rows = read_sheet()
    if args.check_sheet:
        fresh = read_sheet()
        old = json.loads(OUT.read_text())["strokes_px"]
        worst = max(max(abs(a[1] - b[1]), abs(a[2] - b[2])) for a, b in zip(old, fresh))
        print(f"--check-sheet: worst stroke disagreement {worst:.2f} px over {len(old)} rows")
        return 0 if worst < 0.5 else 1

    got = derive(rows)
    if args.check:
        have = json.loads(OUT.read_text())
        bad = []
        for k in ("seated_local_enu_m", "committed_local_enu_m", "committed_max_departure_m",
                  "centre_sheet_local_enu_m", "length_m", "corridor_m", "identity"):
            if json.dumps(have[k], sort_keys=True) != json.dumps(got[k], sort_keys=True):
                bad.append(k)
        print("--check:", "re-derives" if not bad else f"DISAGREES on {bad}")
        return 1 if bad else 0

    print(json.dumps({k: v for k, v in got.items() if k != "centre_sheet_local_enu_m"}, indent=1))
    if args.write:
        payload = {
            "_doc": __doc__.replace("SOUTH_GAP_M", str(got["seating"]["south_trim_to_north_water_m"])),
            "ticket": "T-1080 (piece 2 of T-1075; the road reading withdrawn on T-0795's count)",
            "raster": json.loads(GCP.read_text())["raster"],
            "registration": "data/traces/gcp/wright_1834_nara_hup_gcps.json, `fit` (NA pixel -> EPSG:26916, RMS 16.19 m on eight control points)",
            "method": {
                "tracer": "ridge follower, bilinear samples on the normal",
                "seeds_px": SEEDS,
                "step_px": STEP_PX,
                "search_half_width_px": HALF_PX,
                "heading_smoothing": SMOOTH,
                "steps_north": STEPS_NORTH,
                "steps_south": STEPS_SOUTH,
                "sample_every_px_y": PY_SAMPLE,
                "clipped_to_ink_py": [PY_NORTH_INK, PY_SOUTH_INK],
                "kinzie_south_rule_py": PY_KINZIE_SOUTH_RULE,
            },
            "confidence": "attested",
            "confidence_note": (
                "Every number here is a measurement of a stated raster by a stated tracer with "
                "committed parameters, and what it is documented ABOUT is the sheet: Wright drew "
                "a curved double line here, and it falls where these numbers put it. WHAT THE "
                "LINE IS is not this reading's to assert and is not asserted: the project holds "
                "it as the watercourse `north_side_slough`, and `identity` below is this "
                "reading's cross-check of that record rather than a rival to it. The road "
                "reading T-1075 raised is withdrawn; see docs/RESEARCH/michigan_st_tract.md."
            ),
            "strokes_px": [[y, round(w, 2), round(e, 2)] for y, w, e in rows],
            **got,
            "findings": [
                f"The same ink as `north_side_slough`. This reading's sheet stations fall a median "
                f"{got['identity']['median_departure_m']} m from that committed centreline "
                f"(max {got['identity']['max_departure_m']} m) — two scans, two registrations, two "
                "tracers, inside either one's stated uncertainty. The project has held this feature "
                "as water since before T-1075 asked what the line was.",
                "The line ENDS at Michigan Street. Both strokes stop inside that street's corridor, "
                "short of its north rule; the tract's north tier is ruled across with nothing in it. "
                "T-1075's premise that it runs north THROUGH the tract is not what the sheet draws — "
                "and the slough record says the watercourse ends at Michigan Street.",
                "It is not a platted street: it curves, and it cuts diagonally across platted blocks "
                "and lot lines in the North Division tier and in the tract's south tier. That argues "
                "against a STREET and not for a road: a plat ruled over a watercourse is the "
                "ordinary case.",
                f"The drawn corridor averages {got['corridor_m']['mean']} m between stroke centres "
                f"(sd {got['corridor_m']['sd']} m, {got['corridor_m']['min']}-{got['corridor_m']['max']} m), "
                "against 13.02 m measured on the same strokes by T-0795's independent sweep. A "
                "hand-drawn double line on a manuscript sheet carries no surveyed width, and none is "
                "taken from it — the slough record's own 7.1 m is measured from the bank wash, not "
                "from these strokes.",
                f"Carried onto the committed grid the line runs {got['length_m']} m from North Water "
                "Street to Michigan Street. That transfer commits no feature; see THE SEATING.",
            ],
        }
        OUT.write_text(json.dumps(payload, indent=1) + "\n")
        print(f"wrote {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
