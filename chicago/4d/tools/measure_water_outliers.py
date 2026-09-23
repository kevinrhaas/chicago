#!/usr/bin/env python3
"""Every vertex of every water feature, measured against its own neighbours —
and, where the source raster is to hand, against the bank Wright actually inked.

T-0684 (T-0453 piece 1). The owner marked a bump on the South Branch's east bank
that "sticks out" and should not be there, and it is in the committed geometry:
`river.geojson`, *South Division shore*, local ENU (87.2, -96.8), standing 9.4 m
off the straight line between its own two neighbours — the largest such departure
in that feature. The ticket asked for two things and this tool is both of them:
the vertex resolved against the SOURCE rather than against the polyline, and the
same scan run over every other water feature so that one is not fixed while its
siblings survive.

    python3 tools/measure_water_outliers.py             the departure scan
    python3 tools/measure_water_outliers.py --vs-ink    also measure the three bank
                                                        lines against Wright's ink
    python3 tools/measure_water_outliers.py --json out.json

## The two measurements are not the same question, and that is the finding

A **neighbour departure** asks whether a vertex agrees with the polyline around
it. It is cheap, it needs nothing but the committed GeoJSON, and it is what the
ticket's 9.4 m is. But it is a *relative* measure: three vertices displaced
together read as smooth, and the single vertex that comes back to the truth reads
as the spike. Which is exactly what happened here.

A **distance to inked bank** asks whether a vertex is on the line Wright drew. It
needs the georeferenced scan, and it is absolute. Run over all 69 bank vertices it
says: the traced boundary sits a median 0.70 m from inked bank, and 66 of the 69
are within 5 m — well inside the ±20 m the file declares for the planform. The
three that are not are `south_division_shore` 8, 9 and 10, at 11.9, 14.7 and
12.4 m. Vertex 11 — the ticket's spike — is 0.99 m from the ink. **It is standing
on the bank.** Its neighbours are the ones off it.

So the answer to "is the bump real?" is neither of the two the ticket offered. The
vertex is not deleted, because there is nothing wrong with it; and the bank is not
re-traced in this ticket, because T-0453 acceptance 4 says nothing moves and the
repair belongs where the trace lives. What the bump is, is the far side of a
30-metre stretch where the traced channel leaves the inked bank and follows the
east edge of Wright's grey wash instead — see docs/RESEARCH/water_outlier_scan.md.

Needs nothing for the departure scan. `--vs-ink` needs numpy, scipy, Pillow and
pyproj and the Wright region raster, and degrades to a clear skip without them.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EPOCH = ROOT / "data" / "terrain" / "epochs" / "e1834_harbor_cut"
FILES = ("river.geojson", "shoreline.geojson", "hydrology.geojson")

# The planform tolerance the dataset itself declares: river.geojson says the
# planform is "as drafted on a cadastral plat, not a hydrographic survey", and
# data/traces/README.md puts the working uncertainty for anything traced off the
# 1834 sheets at about +/-20 m. NOTHING in this scan is outside that. The listing
# threshold below is therefore about SHAPE, not about tolerance: a smoothly
# displaced line is what a drafting tolerance explains, and a single vertex
# stepping out and back is not.
DECLARED_TOLERANCE_M = 20.0
LIST_THRESHOLD_M = 5.0
LIST_MAX = 20

# Bank lines carried by the Wright trace, and their vertex counts, so --vs-ink
# can refuse a file that has moved under it.
BANKS = ("north_division_shore", "west_division_shore", "south_division_shore")

# The reach the owner marked, in region pixels: rows 600-820 of the trace window,
# with the bank ink searched in columns 620-760. That band contains the South
# Branch's east bank and no other inked line — the lot lines east of it start at
# column 780, and the channel west of it carries no ink at all.
SOUTH_BRANCH_REACH = (600, 820, 620, 760)


def rings(feature):
    """(label, coords, closed) for each ring or line the feature carries."""
    g = feature["geometry"]
    t = g["type"]
    if t == "Polygon":
        for i, ring in enumerate(g["coordinates"]):
            yield (f"ring {i}" if i else "outer ring"), ring, True
    elif t == "LineString":
        yield "line", g["coordinates"], False
    elif t == "MultiLineString":
        for i, ln in enumerate(g["coordinates"]):
            yield f"part {i}", ln, False
    else:
        raise SystemExit(f"unhandled geometry {t}")


def departure(prev, here, nxt):
    """Perpendicular distance from `here` to the chord prev->nxt, in metres."""
    (ax, ay), (px, py), (bx, by) = prev, here, nxt
    dx, dy = bx - ax, by - ay
    n = math.hypot(dx, dy)
    if n < 1e-9:
        return math.hypot(px - ax, py - ay)
    return abs(dy * px - dx * py + bx * ay - by * ax) / n


def scan(origin):
    """Every vertex of every water feature, with its departure from the chord of
    its own neighbours and the length of that chord.

    A polygon here is bounded partly by drawn bank and partly by the artificial
    edge where the trace window or the terrain box closes it, and the drawn parts
    are exactly the sibling LineStrings — `river.geojson`'s three division shores,
    `shoreline.geojson`'s two harbour shores. So each polygon vertex is labelled
    `bank` when the same coordinate stands in a sibling line (the line already
    carries it, and it is listed there) and `closing` when it does not, which is
    the artificial edge. Nothing is dropped; the label says which is which.
    """
    o_e, o_n = origin
    out = []
    for name in FILES:
        doc = json.loads((EPOCH / name).read_text())
        drawn, ends = set(), set()
        for ft in doc["features"]:
            if ft["geometry"]["type"] in ("LineString", "MultiLineString"):
                for _lab, coords, _c in rings(ft):
                    drawn.update((round(e, 3), round(n_, 3)) for e, n_ in coords)
                    ends.update((round(c[0], 3), round(c[1], 3)) for c in (coords[0], coords[-1]))
        for ft in doc["features"]:
            poly = ft["geometry"]["type"] == "Polygon"
            for label, coords, closed in rings(ft):
                pts = coords[:-1] if closed and coords[0] == coords[-1] else coords
                m = len(pts)
                rows = []
                span = range(m) if closed else range(1, m - 1)
                for i in span:
                    a, b = pts[(i - 1) % m], pts[(i + 1) % m]
                    d = departure(a, pts[i], b)
                    e, n_ = pts[i]
                    kind = "line"
                    if poly:
                        key = (round(e, 3), round(n_, 3))
                        kind = ("corner" if key in ends else
                                "bank" if key in drawn else "closing")
                    rows.append({"i": i, "departure_m": round(d, 2),
                                 "chord_m": round(math.hypot(b[0] - a[0], b[1] - a[1]), 1),
                                 "kind": kind,
                                 "local_e": round(e - o_e, 1), "local_n": round(n_ - o_n, 1)})
                # A polygon no sibling line covers at all — the sand bar — is a
                # drawn edge in its own right, not a closing edge.
                if poly and rows and not any(r["kind"] != "closing" for r in rows):
                    for r in rows:
                        r["kind"] = "line"
                out.append({"file": name, "id": ft["id"], "part": label,
                            "vertices": m, "endpoints_skipped": 0 if closed else 2,
                            "duplicate_of": "sand_bar_1834" if (poly and label == "ring 1"
                                                                and ft["id"] != "sand_bar_1834")
                                            else None,
                            "rows": rows})
    return out


def quantile(v, q):
    if not v:
        return 0.0
    s = sorted(v)
    k = (len(s) - 1) * q
    lo, hi = math.floor(k), math.ceil(k)
    return s[lo] if lo == hi else s[lo] + (s[hi] - s[lo]) * (k - lo)


def report(groups):
    print("DEPARTURE FROM OWN NEIGHBOURS — every water vertex of e1834_harbor_cut")
    print(f"  declared planform tolerance {DECLARED_TOLERANCE_M:.0f} m (data/traces/README.md);"
          f" listing at or above {LIST_THRESHOLD_M:.0f} m\n")
    print(f"  {'feature':<26} {'part':<11} {'n':>4} {'median':>7} {'p90':>7} {'max':>7}  drawn")
    drawn, closing, corners = [], [], []
    for g in groups:
        v = [r["departure_m"] for r in g["rows"]]
        nb = sum(1 for r in g["rows"] if r["kind"] != "closing")
        print(f"  {g['id']:<26} {g['part']:<11} {g['vertices']:>4} "
              f"{quantile(v, 0.5):>7.2f} {quantile(v, 0.9):>7.2f} {max(v or [0]):>7.2f}"
              f"  {nb}/{len(g['rows'])}")
        if g.get("duplicate_of"):
            continue                        # the same ring, listed under its own feature
        for r in g["rows"]:
            if r["departure_m"] < LIST_THRESHOLD_M:
                continue
            if r["kind"] == "closing":
                closing.append((r["departure_m"], g["id"], g["part"], r))
            elif r["kind"] == "corner":
                corners.append((r["departure_m"], g["id"], g["part"], r))
            elif r["kind"] == "bank":
                continue                    # the sibling line carries this vertex
            else:
                drawn.append((r["departure_m"], g["id"], g["part"], r))

    over = [x for x in drawn if x[0] > DECLARED_TOLERANCE_M]
    print(f"\n  DRAWN EDGES — {len(drawn)} vertices at or above {LIST_THRESHOLD_M:.0f} m."
          f" A polygon vertex that stands in a sibling bank line is listed on the line,"
          f" not twice.")
    print(f"  A long chord with a large departure is a BEND. A short chord with a large"
          f" departure is a SPIKE, and that is what a trace artefact looks like.\n")
    print(f"  {'departure':>9}  {'chord':>7}  {'feature':<26} {'idx':>4}  local ENU")
    for d, fid, _part, r in sorted(drawn, key=lambda x: -x[0])[:LIST_MAX]:
        print(f"  {d:>7.2f} m  {r['chord_m']:>5.1f} m  {fid:<26} {r['i']:>4}  "
              f"({r['local_e']:>8.1f}, {r['local_n']:>8.1f})")
    if len(drawn) > LIST_MAX:
        print(f"  … and {len(drawn) - LIST_MAX} more between {LIST_THRESHOLD_M:.0f} m and "
              f"{sorted(drawn, key=lambda x: -x[0])[LIST_MAX][0]:.2f} m")

    print(f"\n  CLOSING EDGES — {len(closing)} vertices at or above {LIST_THRESHOLD_M:.0f} m"
          f" on the artificial edge where a water polygon shuts against the trace window"
          f" or the terrain box. Not drawn bank; not a defect.")
    for d, fid, _part, r in sorted(closing, key=lambda x: -x[0])[:8]:
        print(f"  {d:>7.2f} m  {r['chord_m']:>5.1f} m  {fid:<26} {r['i']:>4}  "
              f"({r['local_e']:>8.1f}, {r['local_n']:>8.1f})")

    print(f"\n  WINDOW CORNERS — {len(corners)} vertices at or above "
          f"{LIST_THRESHOLD_M:.0f} m where a water polygon turns the corner at a bank"
          f" line's own endpoint, i.e. where the trace window cuts the water. The bank"
          f" lines skip their endpoints for the same reason; these are those vertices,"
          f" shown rather than dropped.")
    for d, fid, _part, r in sorted(corners, key=lambda x: -x[0])[:8]:
        print(f"  {d:>7.2f} m  {r['chord_m']:>5.1f} m  {fid:<26} {r['i']:>4}  "
              f"({r['local_e']:>8.1f}, {r['local_n']:>8.1f})")

    print(f"\n  {len(over)} drawn-edge vertices outside the declared "
          f"{DECLARED_TOLERANCE_M:.0f} m planform tolerance: "
          + (", ".join(f"{x[1]} {x[3]['i']}" for x in over) or "none"))
    return drawn


# ---------------------------------------------------------------------------
# --vs-ink: the absolute measurement
# ---------------------------------------------------------------------------

def vs_ink(origin, cache: Path, ink_l: int):
    """Distance from every bank vertex to the nearest inked bank pixel, and to
    the nearest grey wash pixel, on the Wright 1834 region the trace works in."""
    try:
        import numpy as np
        import scipy.ndimage as ndi
        from PIL import Image
    except ImportError as exc:
        print(f"\nSKIP --vs-ink: {exc.name} not installed (pip install numpy scipy Pillow)")
        return None
    if not cache.exists():
        print(f"\nSKIP --vs-ink: no cached Wright region at {cache} — "
              f"run `python3 tools/trace_river.py --check` first, which fetches it")
        return None
    sys.path.insert(0, str(ROOT / "tools"))
    from trace_river import REGION, affine_from_gcps, wash_mask  # noqa: PLC0415

    rgb = np.asarray(Image.open(cache).convert("RGB"))
    a = rgb.astype(np.float32)
    lum = 0.299 * a[..., 0] + 0.587 * a[..., 1] + 0.114 * a[..., 2]
    ink = lum < ink_l                       # the drawn bank line, not the wash
    wash = wash_mask(rgb, np)
    d_ink = ndi.distance_transform_edt(~ink)
    d_wash = ndi.distance_transform_edt(~wash)

    coef, rms, ngcp = affine_from_gcps()
    c0, c1, c2, c3, c4, c5 = coef
    inv = np.linalg.inv(np.array([[c0, c1], [c3, c4]]))
    cell = math.hypot(c0, c3)
    h, w = ink.shape

    def to_px(e, n):
        v = inv @ np.array([e - c2, n - c5])
        return float(v[0]) - REGION[0], float(v[1]) - REGION[1]

    print(f"\nDISTANCE TO THE INKED BANK — Wright 1834, region {REGION}, "
          f"{cell:.4f} m/px")
    print(f"  affine refit from {ngcp} GCPs, RMS {rms:.1f} m; "
          f"ink is luminance < {ink_l} ({int(ink.sum()):,} px), "
          f"wash mask {int(wash.sum()):,} px\n")
    print(f"  {'feature':<26} {'idx':>4}  {'local ENU':<22} {'to ink':>8} {'to wash':>8}")
    o_e, o_n = origin
    riv = json.loads((EPOCH / "river.geojson").read_text())
    rows, off = [], []
    for fid in BANKS:
        ft = next(f for f in riv["features"] if f["id"] == fid)
        for i, (e, n_) in enumerate(ft["geometry"]["coordinates"]):
            px, py = to_px(e, n_)
            xi, yi = int(round(px)), int(round(py))
            if not (0 <= xi < w and 0 <= yi < h):
                continue                    # a vertex on the trace window's edge
            di = float(d_ink[yi, xi]) * cell
            dw = float(d_wash[yi, xi]) * cell
            rows.append({"id": fid, "i": i, "local_e": round(e - o_e, 1),
                         "local_n": round(n_ - o_n, 1),
                         "to_ink_m": round(di, 2), "to_wash_m": round(dw, 2)})
            if di >= LIST_THRESHOLD_M:
                off.append(rows[-1])
    for r in sorted(rows, key=lambda r: -r["to_ink_m"])[:8]:
        loc = f"({r['local_e']:>8.1f}, {r['local_n']:>8.1f})"
        print(f"  {r['id']:<26} {r['i']:>4}  {loc:<22} {r['to_ink_m']:>6.2f} m "
              f"{r['to_wash_m']:>6.2f} m")
    v = [r["to_ink_m"] for r in rows]
    print(f"\n  {len(rows)} bank vertices inside the window: median {quantile(v, 0.5):.2f} m "
          f"from inked bank, p90 {quantile(v, 0.9):.2f} m, max {max(v):.2f} m")
    print(f"  {len(off)} at or above {LIST_THRESHOLD_M:.0f} m: "
          + (", ".join(f"{r['id']} {r['i']}" for r in off) or "none"))
    return rows


def bank_profile(cache: Path, ink_l: int, y0: int, y1: int, x0: int, x1: int):
    """Is the drawn bank itself smooth through the South Branch reach?

    The acceptance question is about WRIGHT'S LINE, not about the polyline traced
    off it: a bank that really steps out and back has an inked edge that steps out
    and back. So this walks the scan row by row through the reach and reports the
    westernmost inked pixel in a band that contains the bank and nothing else. A
    monotone column is a smooth bank; a reversal is a step.
    """
    try:
        import numpy as np
        from scipy import ndimage as ndi
        from PIL import Image
    except ImportError as exc:
        print(f"\nSKIP --bank-profile: {exc.name} not installed")
        return None
    if not cache.exists():
        print(f"\nSKIP --bank-profile: no cached Wright region at {cache}")
        return None
    sys.path.insert(0, str(ROOT / "tools"))
    from trace_river import affine_from_gcps, wash_mask  # noqa: PLC0415

    rgb = np.asarray(Image.open(cache).convert("RGB"))
    a = rgb.astype(np.float32)
    lum = 0.299 * a[..., 0] + 0.587 * a[..., 1] + 0.114 * a[..., 2]
    ink = lum < ink_l
    d_wash = ndi.distance_transform_edt(~wash_mask(rgb, np))
    coef, _rms, _n = affine_from_gcps()
    cell = math.hypot(coef[0], coef[3])
    print(f"\nTHE DRAWN BANK ITSELF — South Branch east bank, Wright 1834, region "
          f"rows {y0}-{y1}, ink searched in columns {x0}-{x1}")
    print("  westernmost inked pixel per row, and how far that pixel is from washed")
    print("  water. Monotone west = a smooth bank; a small wash gap = a continuous wash.\n")
    prev, rows, reversals = None, [], []
    for y in range(y0, y1 + 1):
        xs = np.flatnonzero(ink[y, x0:x1])
        if not xs.size:
            continue
        x = int(xs[0]) + x0
        rows.append((y, x))
        if prev is not None and x > prev:
            reversals.append((y, x - prev))
        prev = x
    for y, x in rows[::10]:
        print(f"  row {y:>4}   ink x {x:>4}   wash {d_wash[y, x] * cell:>5.2f} m away")
    gaps = [d_wash[y, x] * cell for y, x in rows]
    back = [r for r in reversals if r[1] > 2]
    print(f"\n  {len(rows)} rows read, x from {rows[0][1]} to {rows[-1][1]}; "
          f"{len(reversals)} single-row reversals, largest {max([r[1] for r in reversals] or [0])} px; "
          f"{len(back)} of more than 2 px")
    print("  A bank that steps out and back would show a sustained reversal here. "
          + ("It does not." if not back else f"It shows: {back}"))
    print(f"  Wash reaches the inked bank throughout: worst gap {max(gaps):.2f} m, "
          f"median {quantile(gaps, 0.5):.2f} m.")
    return rows


def lobe_map(cache: Path, ink_l: int, y0: int, y1: int, x0: int, x1: int, step: int):
    """Print the trace's own four-way classification across the reach.

    W traced water · w wash the trace did not take into the channel · I inked bank
    · . dry paper. It reproduces the segmentation rather than reading the debug
    overlay, so what is printed is what the committed GeoJSON came out of.
    """
    try:
        import numpy as np
        from scipy import ndimage as ndi
        from PIL import Image
    except ImportError as exc:
        print(f"\nSKIP --lobe-map: {exc.name} not installed")
        return None
    if not cache.exists():
        print(f"\nSKIP --lobe-map: no cached Wright region at {cache}")
        return None
    sys.path.insert(0, str(ROOT / "tools"))
    from trace_river import PARAMS, SEEDS, channel_from, wash_mask  # noqa: PLC0415

    rgb = np.asarray(Image.open(cache).convert("RGB"))
    wash = wash_mask(rgb, np)
    river = channel_from(wash, SEEDS, PARAMS["close_r"], PARAMS["open_r"],
                         PARAMS["fill_r"], np, ndi, speckle=PARAMS["speckle_px"])
    a = rgb.astype(np.float32)
    lum = 0.299 * a[..., 0] + 0.587 * a[..., 1] + 0.114 * a[..., 2]
    ink = lum < ink_l
    print(f"\nWHAT THE TRACE SAW — region rows {y0}-{y1}, columns {x0}-{x1}")
    print("  W traced water · w wash NOT taken into the channel · I inked bank · . dry\n")
    stranded = 0
    for y in range(y0, y1 + 1, step):
        row = ""
        for x in range(x0, x1):
            row += ("W" if river[y, x] else "I" if ink[y, x] else "w" if wash[y, x] else ".")
        print(f"  {y:>4} {row}")
    for y in range(y0, y1 + 1):
        seg = [x for x in range(x0, x1) if wash[y, x] and not river[y, x] and not ink[y, x]]
        stranded += len(seg)
    print(f"\n  {stranded} px of wash in this window stand outside the traced channel"
          f" — the strip between the traced boundary and the bank Wright inked.")
    return stranded


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--vs-ink", action="store_true",
                    help="also measure the bank lines against Wright's inked bank")
    ap.add_argument("--cache", default=str(Path("/tmp") / "wright_1834_forks_region.jpg"),
                    help="the Wright region raster tools/trace_river.py caches")
    ap.add_argument("--ink-luminance", type=int, default=110)
    ap.add_argument("--bank-profile", action="store_true",
                    help="walk the South Branch reach row by row on the scan")
    ap.add_argument("--lobe-map", action="store_true",
                    help="print the trace's own classification across the marked reach")
    ap.add_argument("--json", help="write the full per-vertex scan here")
    args = ap.parse_args()

    datum = json.loads((ROOT / "data" / "datum.json").read_text())
    origin = (datum["origin_utm_e"], datum["origin_utm_n"])
    groups = scan(origin)
    listed = report(groups)
    ink_rows = vs_ink(origin, Path(args.cache), args.ink_luminance) if args.vs_ink else None
    if args.bank_profile:
        bank_profile(Path(args.cache), args.ink_luminance, *SOUTH_BRANCH_REACH)
    if args.lobe_map:
        lobe_map(Path(args.cache), args.ink_luminance, 640, 706, 650, 715, 2)

    if args.json:
        Path(args.json).write_text(json.dumps(
            {"origin_utm": origin, "declared_tolerance_m": DECLARED_TOLERANCE_M,
             "list_threshold_m": LIST_THRESHOLD_M, "groups": groups,
             "vs_ink": ink_rows}, indent=1) + "\n")
        print(f"\nwrote {args.json}")
    if any(d > DECLARED_TOLERANCE_M for d, *_ in listed):
        print("\nA drawn-edge vertex departs its neighbours by more than the "
              "declared planform tolerance.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
