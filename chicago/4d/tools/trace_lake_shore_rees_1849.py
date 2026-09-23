#!/usr/bin/env python3
"""Trace the PRE-FILL LAKE SHORE below Twelfth Street, off Rees & Rucker 1849.

The fifth tracing window, and the second one taken from this sheet.
`tools/trace_shoreline.py` holds the harbour and the lake off Wright 1834 and
stops where Wright stops -- its `south_shore_harbor_reach` run ends at
(E +1347.4, N -2159.9), the foot of Wright's sheet. Below that vertex the
committed field answered the lake the way it answered the river before T-1150:
with a HELD EASTING. `southern_lake.beyond_the_trace` in the epoch's terrain
spec carried E +1347.4 due south for 1 640 m to the box floor, because without
it every row below the trace had no lake edge at all and 355 x 1 640 m of Lake
Michigan came out as dry prairie. It was tagged conjectural and recorded as the
lake's half of L239.

    python3 tools/trace_lake_shore_rees_1849.py            re-trace and write
    python3 tools/trace_lake_shore_rees_1849.py --check    re-trace and diff
    python3 tools/trace_lake_shore_rees_1849.py --check-properties
                                                  hold the committed file to
                                                  this file's literals: no
                                                  numpy, no network, no raster.

THE SOURCE, and what it is asked for
------------------------------------
REES & RUCKER, MAP OF CHICAGO AND VICINITY, 1849 -- the sheet T-1150 acquired
and georeferenced for the river, pinned as `rees_rucker_1849` with the raster's
sha256 and fitted affine against fourteen section corners of the Chicago mile
grid at RMS 25.0 m (`data/traces/gcp/rees_rucker_1849_gcps.json`). Its `use`
field named this trace before it existed. It is the only sheet in this corpus
that reaches Cermak Road.

Asked for: WHERE THE WATER'S EDGE RUNS between Twelfth Street and the box floor.
The sheet draws it unambiguously -- a single firm pen line with the lake's wave
hatching banked against its east side and platted lake-front acreage (Laffin,
Garrett, Scammon, Peck, the heirs of D. Lee) named against its west.

Not asked for: the modern lakefront, which is landfill here and would be a
fabrication -- the ticket says so and it is the one substitution this trace must
never make. Not asked for either: any street, lot or block on this sheet; the
GCP file's `use` forbids it.

THE FOURTEEN YEARS ARE NOT NEUTRAL HERE, AND THAT IS THE FINDING
---------------------------------------------------------------
For the river T-1150 could argue the interval away: a natural channel's planform,
and every work that straightened this reach is later than the sheet. THE SHORE
CANNOT BE ARGUED AWAY. `docs/research/01-terrain-hydrology.md` sec 4 states the
mechanism and the magnitude: net littoral drift on this coast runs south, the
1833-35 piers trapped it on their north side and starved the south side, the
1836 I&M Canal Commissioners map put the shore about 400 ft east of Michigan
Avenue, and by the 1850s it had cut back to within about 50 ft of it. That is
roughly 350 ft -- 107 m -- of shore lost between the scene year and the decade
this sheet was drawn in, on the reach immediately downdrift of the piers.

So the trace was checked against that before it was committed, over the 860 m
where this sheet and Wright's overlap (N -1300 to the splice). The 1849 line
reads WEST of Wright's 1834 line at every station: 134 m at N -1300, tapering to
50 m at N -2000 -- mean 93 m. THE DOCUMENTED EROSION IS 107 M AND THE MEASURED
OFFSET IS 93 M. Nothing here was tuned to make that happen; the fit is
T-1150's, unaltered, and the comparison was run after the trace. Two independent
statements of the same coastal history, fourteen metres apart -- and the
measurement is the smaller of the two, so the bound below is the conservative
one.

The taper is the second half of it, and it is why the committed reach is the
right reach to take from this sheet. Erosion downdrift of a littoral barrier is
worst against the structure and dies away with distance from it, and the
measured offset does exactly that -- 134 m at 1.3 km south of the piers, 50 m at
2.2 km. The window this file COMMITS begins at 2.16 km and runs to 3.8 km, which
is the far end of that decay: the sheet's own disagreement with Wright is 49 m
at the top of the committed run and falling. The trace is therefore a lower
bound on the 1835 shore's easting -- the 1835 water's edge stood at or east of
this line -- and the bound tightens southward.

None of which upgrades anything. Every vertex is `inferred`, never `documented`,
and every vertex is also below `evidence_limit` at N -2149.4, which writes it
CONF_CONJECTURAL; the field carries the more conservative of the two.

THE SEAM, and the 49 m step in it
---------------------------------
The two runs abut on a DECLARED ROW -- N -2159.9, Wright's last shore vertex and
the row the deleted rule held from -- the same construction T-1150 used at
N -2110. They do not agree on it: Wright stands the water's edge at E +1347.5
and this sheet at E +1298.9, a step of 49 m to the WEST across one row. That is
not inside the fit's 25.0 m RMS and it is not claimed to be. It is the erosion
above, measured at the one row where the two sources touch, and it is left in
the data rather than blended out: a blend would be geometry from neither survey.
It is recorded in docs/LIBERTIES.md under L239 and in the spec's own note.

How the shore is found
----------------------
The lake hatching is a band of parallel wavy strokes with paper between them, so
the shore is not a darkness boundary but a DENSITY STEP: paper to the west, ink
to the east. The ink mask is a 41 px high-pass thresholded at 7, averaged over
9 px and again over 5, and the shore score at a column is the mean density in
the 24 px EAST of it minus the mean in the 24 px WEST. A step detector and not a
darkness test is what survives the two things on this window that would break
one: the platted acreage west of the line, whose lot rules and engraved owner
names are ink on the land side, and the sheet's FOLDS. A fold lays grey across
both windows equally and subtracts out; the horizontal crease at y 4397 crosses
this reach and is invisible to the score.

The path is a DYNAMIC PROGRAMME down the rows -- at most 3 px of lateral step
per row, a small penalty on stepping, greatest total score -- seeded inside the
reach at the top of the window, then smoothed over 25 rows. It is then SNAPPED
to the drawn line: within +/- 7 px of the smoothed path, the ink-weighted
centroid of the row, smoothed over 15. The snap moves the line 4.0 px east on
average (8.1 m), because the score's step sits at the west edge of the 24 px
window and the pen stroke sits at the east edge of it; after the snap the line
lies on the ink.

Where it starts and where it stops
----------------------------------
Traced from y 3650 (about N -1300) so the overlap with Wright can be measured,
and COMMITTED from N -2159.9 -- Wright's last vertex -- south. It is carried
10 m past the box floor at N -3800 so the floor row falls inside a segment
rather than on the run's last vertex: `southern_lake` interpolates its per-row
edge along segments, and a run that ends ON the floor leaves the floor row to a
degenerate one. The sheet itself runs on another mile and a quarter.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GCP = ROOT / "data" / "traces" / "gcp" / "rees_rucker_1849_gcps.json"
EPOCH = ROOT / "data" / "terrain" / "epochs" / "e1834_harbor_cut"
OUT = EPOCH / "lake_shore_below_twelfth.geojson"
WRIGHT = EPOCH / "shoreline.geojson"
WRIGHT_RUN = "south_shore_harbor_reach"

# The tracing window and its settings, in the raster's own pixels.
Y_TOP, Y_BOT = 3650, 4915          # rows scanned; the top 400 are the overlap
X_LO, X_HI = 3380, 3790            # the column band the programme may wander in
SEED_X = 3521                      # the shore at Y_TOP, +/- 25 px
HP_BOX, HP_THR = 41, 7             # high-pass window, ink threshold
DENS_A, DENS_B = 9, 5              # the two density averages
EDGE = 24                          # the step detector's half-window, px
STEP = 3                           # max px of lateral step per row
STEP_PEN = 0.004                   # cost per px of step
SMOOTH = 25                        # path moving average, rows
SNAP, SNAP_SMOOTH = 7, 15          # ink-centroid snap window and its average
N_SPLICE = -2159.9                 # Wright's last shore vertex: the declared row
N_FLOOR = -3800.0                  # the box floor
CARRY = 10.0                       # metres the run is taken past the floor
SAMPLE = 10                        # one vertex per 10 rows, about 20 m
OVERLAP_FROM, OVERLAP_TO = -1300.0, -2000.0   # the stations compared to Wright

# The literals --check-properties holds the committed file to. They are
# measurements of this trace, not settings of it: if the trace is re-run and
# they move, the docstring above is wrong about the shore and has to be
# rewritten.
EXPECT = {
    "vertices": 82,
    "n_splice_m": -2159.9,
    "n_floor_m": -3800.0,
    "e_at_splice_m": 1298.9,
    "e_at_floor_m": 1689.6,
    "e_min_m": 1298.9,
    "e_max_m": 1689.2,
    "seam_step_m": -48.6,
    "overlap_mean_m": -92.6,
    "documented_erosion_m": 107.0,
}
TOL = {"e": 2.0, "seam": 3.0, "overlap": 3.0}


def raster_path() -> Path:
    p = Path(os.environ.get("REES_1849_RASTER", "/tmp/rees_rucker_1849.jpg"))
    gcp = json.loads(GCP.read_text())
    want = gcp["raster"]["sha256"]
    if not p.exists():
        p.parent.mkdir(parents=True, exist_ok=True)
        req = urllib.request.Request(
            gcp["raster"]["url"],
            headers={"User-Agent": "chicago4d-trace/1.0 (+kevinrhaas/custom)"})
        with urllib.request.urlopen(req, timeout=300) as r, p.open("wb") as f:
            f.write(r.read())
    got = hashlib.sha256(p.read_bytes()).hexdigest()
    if got != want:
        sys.exit(f"raster sha256 {got} != {want} recorded in {GCP.name}; "
                 f"refusing to trace a sheet that is not the one that was fitted")
    return p


def wright_edge(n_at: float) -> float:
    """Wright's committed lake edge at a northing, the way `southern_lake` reads
    it: the easternmost crossing of the run by that row."""
    datum = json.loads((ROOT / "data" / "datum.json").read_text())
    o_e, o_n = datum["origin_utm_e"], datum["origin_utm_n"]
    d = json.loads(WRIGHT.read_text())
    f = next(f for f in d["features"] if f["id"] == WRIGHT_RUN)
    pts = [(c[0] - o_e, c[1] - o_n) for c in f["geometry"]["coordinates"]]
    best = None
    for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
        if y1 == y2:
            continue
        lo, hi = (y1, y2) if y1 < y2 else (y2, y1)
        # the epsilon is for the run's own end vertices: N_SPLICE is that
        # vertex's northing written down to a tenth, and the stored coordinate
        # is a UTM easting/northing pair minus the datum origin.
        if not (lo - 0.05 <= n_at <= hi + 0.05):
            continue
        x = x1 + (n_at - y1) / (y2 - y1) * (x2 - x1)
        best = x if best is None else max(best, x)
    return best


def trace():
    import numpy as np
    from scipy import ndimage
    from PIL import Image

    gcp = json.loads(GCP.read_text())
    c = gcp["fit"]["coefficients"]

    def to_local(px, py):
        return (c["a"] * px + c["b"] * py + c["c"],
                c["d"] * px + c["e"] * py + c["f"])

    a = np.asarray(Image.open(raster_path()).convert("L"), dtype=np.float32)
    sub = a[Y_TOP:Y_BOT, X_LO:X_HI]
    hp = ndimage.uniform_filter(sub, size=HP_BOX) - sub
    ink = (hp > HP_THR).astype(np.float32)
    dens = ndimage.uniform_filter(ndimage.uniform_filter(ink, size=DENS_A),
                                  size=DENS_B)
    H, W = dens.shape

    # The step detector: mean density EAST of a column minus mean density WEST.
    cum = np.cumsum(np.pad(dens, ((0, 0), (1, 0))), axis=1).astype(np.float64)
    score = np.full((H, W), -9.0)
    xs = np.arange(EDGE, W - EDGE)
    score[:, EDGE:W - EDGE] = ((cum[:, xs + EDGE] - cum[:, xs])
                               - (cum[:, xs] - cum[:, xs - EDGE])) / EDGE

    INF = 1e9
    cost = np.full((H, W), INF)
    back = np.zeros((H, W), dtype=np.int32)
    s = SEED_X - X_LO
    cost[0, s - 25:s + 25] = -score[0, s - 25:s + 25]
    for y in range(1, H):
        best = np.full(W, INF)
        arg = np.zeros(W, dtype=np.int32)
        prev = cost[y - 1]
        for d in range(-STEP, STEP + 1):
            sh = np.roll(prev, d)
            if d > 0:
                sh[:d] = INF
            elif d < 0:
                sh[d:] = INF
            cand = sh + abs(d) * STEP_PEN
            upd = cand < best
            best[upd] = cand[upd]
            arg[upd] = np.arange(W)[upd] - d
        cost[y] = best - score[y]
        back[y] = arg
    path = np.zeros(H, dtype=np.int32)
    path[-1] = int(np.argmin(cost[-1]))
    for y in range(H - 1, 0, -1):
        path[y - 1] = back[y, path[y]]
    line = ndimage.uniform_filter1d(path.astype(float), SMOOTH)

    # snap to the drawn stroke: ink-weighted centroid within +/- SNAP px
    snapped = np.zeros(H)
    for y in range(H):
        k = int(round(line[y]))
        lo, hi = max(0, k - SNAP), min(W, k + SNAP + 1)
        w = hp[y, lo:hi].astype(np.float64).copy()
        w[w < 0] = 0.0
        snapped[y] = (lo + (np.arange(len(w)) * w).sum() / w.sum()
                      if w.sum() > 0 else line[y])
    snap_shift_px = float(np.mean(snapped - line))
    snapped = ndimage.uniform_filter1d(snapped, SNAP_SMOOTH)

    rows = [to_local(snapped[y] + X_LO, y + Y_TOP)[::-1] for y in range(H)]
    rows = [(n, e) for n, e in rows]          # (northing, easting)
    rows.sort()
    ns = [r[0] for r in rows]
    es = [r[1] for r in rows]

    def at(n_at):
        return float(np.interp(n_at, ns, es))

    # THE OVERLAP against Wright, measured after the trace and not before it.
    overlap = []
    n_at = OVERLAP_FROM
    while n_at >= OVERLAP_TO:
        w = wright_edge(n_at)
        if w is not None:
            overlap.append((n_at, w, at(n_at), at(n_at) - w))
        n_at -= 100.0

    keep = [r for r in rows if N_FLOOR - CARRY <= r[0] <= N_SPLICE]
    keep = keep[::SAMPLE] + ([keep[-1]] if (len(keep) - 1) % SAMPLE else [])
    keep.sort(key=lambda r: -r[0])
    return keep, overlap, at, snap_shift_px


SPLICE = (
    "The run's north end is N -2159.9, the declared row at which "
    "tools/trace_shoreline.py's Wright 1834 run `south_shore_harbor_reach` "
    "ends and the row terrain_spec's deleted `southern_lake.beyond_the_trace` "
    "held its easting from. The two runs abut on that row rather than within a "
    "tolerance, and they DISAGREE ON IT by 49 m -- see `measured.seam` and the "
    "tool's docstring: the step is the documented post-pier erosion of this "
    "shore between 1835 and 1849, left in the data rather than blended out. "
    "The south end is 10 m past the box floor at N -3800.0, which is the box "
    "and not the shore: the sheet runs on another mile and a quarter.")


def build():
    keep, overlap, at, snap_shift_px = trace()
    datum = json.loads((ROOT / "data" / "datum.json").read_text())
    o_e, o_n = datum["origin_utm_e"], datum["origin_utm_n"]
    coords = [[round(e + o_e, 2), round(n + o_n, 2)] for n, e in keep]
    es = [e for n, e in keep]
    seam = keep[0][1] - wright_edge(N_SPLICE)
    mean_off = sum(r[3] for r in overlap) / len(overlap)
    doc = {
        "type": "FeatureCollection",
        "name": "lake_shore_below_twelfth",
        "crs": {"type": "name",
                "properties": {"name": "urn:ogc:def:crs:EPSG::26916"}},
        "_doc": (
            "The PRE-FILL shore of Lake Michigan from Twelfth Street to the "
            "terrain box's south wall, traced from REES & RUCKER, MAP OF "
            "CHICAGO AND VICINITY, 1849 by tools/trace_lake_shore_rees_1849.py. "
            "The second geometry taken from the one sheet in this corpus that "
            "reaches Cermak Road; see data/traces/gcp/rees_rucker_1849_gcps.json "
            "for the fit (14 section corners, RMS 25.0 m). THIS IS NOT THE "
            "MODERN LAKEFRONT, which is landfill along the whole of this reach. "
            "The sheet is fourteen years later than the scene and on a SHORE "
            "that interval is not neutral: the 1833-35 piers starved this coast "
            "of littoral drift and it eroded westward, so this line is a LOWER "
            "BOUND on the 1835 shore's easting -- the water's edge of 1835 "
            "stood at or east of it. The bound is measured, not asserted: see "
            "`measured.overlap`. Every vertex is INFERRED and every vertex is "
            "also south of `evidence_limit`, which writes it CONF_CONJECTURAL; "
            "the field carries the more conservative of the two. This replaces "
            "the held easting recorded as the lake's half of L239."),
        "measured": {
            "easting_m": {"at_splice": round(keep[0][1], 1),
                          "at_floor": round(at(N_FLOOR), 1),
                          "min": round(min(es), 1), "max": round(max(es), 1)},
            "trend": ("the shore falls away to the SOUTH-EAST: it gains "
                      f"{round(max(es) - min(es))} m of easting over the "
                      f"{round(N_SPLICE - N_FLOOR)} m from the splice to the "
                      "box floor, a bearing about 13 degrees east of south. The "
                      "held easting this replaces claimed a shore that ran dead "
                      "straight down a single easting for the whole of it, and "
                      f"at the floor it stood the water {round(at(N_FLOOR) - 1347.4)} m "
                      "west of where this sheet draws it."),
            "method": ("the west edge of the lake's wave hatching, found as a "
                       "density STEP -- mean ink density 24 px east of a column "
                       "minus mean density 24 px west -- carried down the rows "
                       "by a dynamic programme at most 3 px wide a row, then "
                       "snapped to the drawn pen stroke by the ink-weighted "
                       "centroid within 7 px. The snap moved the line "
                       f"{round(snap_shift_px, 1)} px east on average."),
            "seam": {
                "at_n_m": N_SPLICE,
                "wright_1834_e_m": round(wright_edge(N_SPLICE), 1),
                "rees_1849_e_m": round(keep[0][1], 1),
                "step_m": round(seam, 1),
                "note": ("the two surveys do NOT meet inside the fit's 25.0 m "
                         "RMS here, and are not claimed to. The step is west, "
                         "which is the direction the erosion runs, and its size "
                         "is what the overlap below measures at this station."),
            },
            "overlap": {
                "stations_n_m": [r[0] for r in overlap],
                "wright_1834_e_m": [round(r[1], 1) for r in overlap],
                "rees_1849_e_m": [round(r[2], 1) for r in overlap],
                "offset_m": [round(r[3], 1) for r in overlap],
                "mean_offset_m": round(mean_off, 1),
                "note": ("the 860 m where this sheet and Wright's overlap, "
                         "measured after the trace was run and with the fit "
                         "untouched. The 1849 line reads WEST of the 1834 line "
                         "at every station, by 134 m at N -1300 tapering to "
                         "50 m at N -2000. docs/research/01-terrain-hydrology.md "
                         "sec 4 documents why and by how much: the piers trapped "
                         "the southward littoral drift, the 1836 canal "
                         "commissioners' map put this shore about 400 ft east of "
                         "Michigan Avenue and by the 1850s it had cut back to "
                         "within about 50 ft of it -- roughly 350 ft, 107 m. The "
                         f"measured mean is {round(mean_off, 1)} m. The taper is "
                         "the signature of erosion downdrift of a barrier, worst "
                         "against the structure and dying away with distance, "
                         "and it is why the committed reach -- which begins "
                         "further south again -- carries the smaller bound."),
            },
        },
        "features": [{
            "type": "Feature",
            "id": "lake_shore_below_twelfth",
            "properties": {
                "kind": "shore",
                "name": "Pre-fill Lake Michigan shore below Twelfth Street",
                "crest_ft_above_datum": None,
                "confidence": "inferred",
                "note": ("The west edge of the lake's wave hatching on Rees & "
                         "Rucker 1849, snapped to the drawn stroke. " + SPLICE),
                "sources": ["rees_rucker_1849"],
            },
            "geometry": {"type": "LineString", "coordinates": coords},
        }],
    }
    return doc


def check_properties() -> int:
    """Offline. No numpy, no raster, no network -- this one runs in check.sh."""
    if not OUT.exists():
        print(f"FAIL {OUT.name} is missing")
        return 1
    d = json.loads(OUT.read_text())
    bad = []
    ids = [f["id"] for f in d["features"]]
    if ids != ["lake_shore_below_twelfth"]:
        bad.append(f"feature ids are {ids}")
    f = d["features"][0]
    if f["properties"]["kind"] != "shore":
        bad.append("the run is not kind=shore")
    if f["properties"]["confidence"] != "inferred":
        bad.append("the run is not inferred")
    if f["properties"]["sources"] != ["rees_rucker_1849"]:
        bad.append("the run does not cite rees_rucker_1849 alone")
    cs = f["geometry"]["coordinates"]
    if len(cs) != EXPECT["vertices"]:
        bad.append(f"{len(cs)} vertices, expected {EXPECT['vertices']}")
    datum = json.loads((ROOT / "data" / "datum.json").read_text())
    o_e, o_n = datum["origin_utm_e"], datum["origin_utm_n"]
    ns = [c[1] - o_n for c in cs]
    es = [c[0] - o_e for c in cs]
    # It must MEET the Wright run's last row at the top and CROSS the box floor
    # at the bottom: a run that stops on the floor leaves the floor row to a
    # degenerate segment and `southern_lake` reads nothing there.
    if abs(max(ns) - EXPECT["n_splice_m"]) > 2.5:
        bad.append(f"starts at N {max(ns):.1f}, not on the splice row "
                   f"{EXPECT['n_splice_m']}")
    if min(ns) > EXPECT["n_floor_m"]:
        bad.append(f"ends at N {min(ns):.1f}, short of the box floor "
                   f"{EXPECT['n_floor_m']} -- the floor row would have no lake "
                   f"edge and 355 m of lake would come out as dry land")
    if abs(es[0] - EXPECT["e_at_splice_m"]) > TOL["e"]:
        bad.append(f"the splice easting is {es[0]:.1f}, expected "
                   f"{EXPECT['e_at_splice_m']}")
    for k, want in (("min", EXPECT["e_min_m"]), ("max", EXPECT["e_max_m"])):
        got = min(es) if k == "min" else max(es)
        if abs(got - want) > TOL["e"]:
            bad.append(f"easting {k} is {got:.1f} m, expected {want} m")
    m = d["measured"]
    if abs(m["seam"]["step_m"] - EXPECT["seam_step_m"]) > TOL["seam"]:
        bad.append(f"the seam step is {m['seam']['step_m']} m, expected "
                   f"{EXPECT['seam_step_m']} m")
    if abs(m["overlap"]["mean_offset_m"] - EXPECT["overlap_mean_m"]) > TOL["overlap"]:
        bad.append(f"the overlap mean is {m['overlap']['mean_offset_m']} m, "
                   f"expected {EXPECT['overlap_mean_m']} m")
    if not all(o < 0 for o in m["overlap"]["offset_m"]):
        bad.append("an overlap station reads the 1849 shore EAST of the 1834 "
                   "one, which the erosion this trace is bounded by forbids")
    for b in bad:
        print("FAIL", b)
    if not bad:
        print(f"OK {OUT.name}: {EXPECT['vertices']} vertices, N "
              f"{EXPECT['n_splice_m']} to past {EXPECT['n_floor_m']}, E "
              f"{EXPECT['e_min_m']}-{EXPECT['e_max_m']}, seam step "
              f"{EXPECT['seam_step_m']} m against "
              f"{EXPECT['documented_erosion_m']} m of documented erosion")
    return 1 if bad else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--check-properties", action="store_true")
    args = ap.parse_args()
    if args.check_properties:
        return check_properties()
    doc = build()
    text = json.dumps(doc, indent=1) + "\n"
    if args.check:
        if not OUT.exists():
            print("FAIL committed file missing")
            return 1
        same = OUT.read_text() == text
        print("OK re-trace matches committed" if same
              else "FAIL re-trace differs from committed")
        return 0 if same else 1
    OUT.write_text(text)
    m = doc["measured"]
    print(f"wrote {OUT.relative_to(ROOT)}: "
          f"{len(doc['features'][0]['geometry']['coordinates'])} vertices, "
          f"E {m['easting_m']['min']}-{m['easting_m']['max']} m, seam step "
          f"{m['seam']['step_m']} m, overlap mean "
          f"{m['overlap']['mean_offset_m']} m")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
