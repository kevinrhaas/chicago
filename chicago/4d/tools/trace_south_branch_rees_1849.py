#!/usr/bin/env python3
"""Trace the South Branch BELOW TWELFTH STREET, off Rees & Rucker 1849.

The fourth tracing window, and the first one that is not Wright's sheet.
`tools/trace_river.py` holds the forks, `tools/trace_shoreline.py` the harbour
and the lake, `tools/trace_south_branch.py` the reach down through the School
Section -- and that third one stops on the section's south line because WRIGHT
STOPS THERE. docs/RESEARCH/south_branch_school_section.md sec 6 calls that edge
"the limit of the survey, not a river end", and until T-1150 the committed field
answered it with a HELD EASTING: `southern_branch` in the epoch's terrain_spec
carried a 45.3 m channel due south from N -2110 to the box floor, 1 690 m of
constant-width river running dead straight down a valley that in fact bends west
toward the portage. It was tagged conjectural and recorded as L239, and its own
note said where the answer was: "a source this corpus does not hold".

    python3 tools/trace_south_branch_rees_1849.py            re-trace and write
    python3 tools/trace_south_branch_rees_1849.py --check    re-trace and diff
    python3 tools/trace_south_branch_rees_1849.py --check-properties
                                                  hold the committed file to
                                                  this file's literals: no
                                                  numpy, no network, no raster.

THE SOURCE, and why a sheet fourteen years late is the right one
---------------------------------------------------------------
Three georeferenced sheets exist in this corpus -- Wright 1834, Hathaway 1834,
the Thompson 1830 plat -- and all three end on the School Section's south line,
which is why `evidence_limit` sits at N -2149.4. The obvious acquisition, the
1821 GLO township plat of T39N R14E, is served from glorecords.blm.gov behind a
login and an unattended run cannot fetch it (measured under T-1149, and measured
again here). REES & RUCKER 1849 is reachable, public domain, 4973 x 6601 px, and
covers North Avenue to below Thirty-First Street and the lake to Western Avenue
-- a mile and a quarter past Cermak Road, which is the box floor.

It is FOURTEEN YEARS LATE and that is a real claim, not a rounding. What is
being read off it is the PLANFORM of a natural channel, and the works that
straightened this reach are all later than the sheet: the Illinois & Michigan
Canal (opened 1848) is drawn on this sheet as a separate line that meets the
river at Bridgeport, well south of the box, and the South Branch's own
straightening between Eighteenth and Twenty-Second Streets is 1928-30. No
channel work between Twelfth Street and Cermak Road is documented in the
1835-1849 interval. The trace is therefore INFERRED, never documented, and the
whole of it lies below `evidence_limit`, which writes every vertex south of
N -2149.4 CONF_CONJECTURAL regardless. The confidence the data carries is the
more conservative of the two.

What the sheet is asked for, and what it is not asked for
--------------------------------------------------------
Asked for: WHERE THE CHANNEL RUNS. That is the whole of L239's complaint and it
is the one thing this sheet draws unambiguously -- a hatched band, 15 to 34 px
wide, continuous from the forks to Bridgeport.

Not asked for: anything else on the sheet. The lake shore beside this reach is
T-1151's and is not traced here. No street, lot or block is derived from this
transform; data/traces/gcp/rees_rucker_1849_gcps.json says so in its `use`.

How the channel is found
------------------------
The band is a HATCH -- parallel pen strokes with paper between them -- so it is
not found by darkness but by the LOCAL DENSITY of ink: a 41 px high-pass of the
grey plate, thresholded at 7, then averaged over 9 px and again over 5. On that
field the river is a plateau near 0.7 and the platted lot lines either side of
it are thin ridges that the averaging flattens.

The centreline is a DYNAMIC PROGRAMME down the rows, not a flood fill, and that
is deliberate: a flood fill leaks through the block hatching wherever a lot line
touches the bank, which it does at Bridge Street, at Cross Street and along the
Lumber Street wharves. The programme is seeded at the top of the reach inside
the channel, steps at most 3 px per row with a small penalty on stepping, and
takes the path of greatest density. It crosses the y 4397 FOLD -- 16 rows where
the sheet's crease has erased the hatch entirely and the density falls to 0.05 --
because the smoothness term carries it across; nothing else in the window would.

The WIDTH is read per row as the full width at half the local peak density, then
rows whose reading exceeds 1.6 x the 51-row median are REJECTED as leaks into the
adjoining lot hatching (47 rows of 860) and interpolated across, the profile
smoothed over 61 rows, and the horizontal cut converted to a perpendicular width
by the centreline's own slope. What comes out is 23.4 to 67.2 m, median 49.9 m.

THE CROSS-CHECK THAT MATTERS is not the width, it is the splice. At N -2110 the
committed Wright trace stands its two banks at E +293.2 and +338.5. This sheet,
drawn fifteen years later by different men, scanned by a different institution
and georeferenced against different control, puts them at E +287.1 and +319.1 --
6.1 m and 19.4 m away, on a fit whose own RMS is 25.0 m. Two surveys, two fits,
one river, and they meet inside their own uncertainty. Nothing in this file was
tuned to make that happen; the seam row was chosen before the trace was run,
because it is the row the deleted rule held from.

The banks are the centreline offset by half that width along its own normal, in
metres, in the local frame -- not in pixels, because the fit's two axis scales
differ by 0.66 per cent and a pixel offset would put that difference into the
channel.

Where it starts and where it stops
----------------------------------
It starts at N -2110.0, which is the row `southern_branch` held from and the last
row at which the Wright trace still draws two banks rather than its closing hook.
The two windows therefore ABUT ON A DECLARED ROW, the same construction
tools/trace_south_branch.py uses at map row 2372, rather than on a tolerance.
It stops 40 m past N -3800.0, the box floor, which is 35 m below Cermak Road:
the sheet runs on for another mile and a quarter and the box does not, and the
centreline is carried past the wall so that both offset banks cross it.
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
OUT = (ROOT / "data" / "terrain" / "epochs" / "e1834_harbor_cut"
       / "south_branch_below_twelfth.geojson")

# The tracing window and its settings, in the raster's own pixels.
Y_TOP, Y_BOT = 4040, 4900          # rows scanned
X_LO, X_HI = 2600, 3260            # the column band the programme may wander in
SEED_X = 3033                      # the channel at Y_TOP, +/- 18 px
HP_BOX, HP_THR = 41, 7             # high-pass window, ink threshold
DENS_A, DENS_B = 9, 5              # the two density averages
STEP = 3                           # max px of lateral step per row
STEP_PEN = 0.004                   # cost per px of step
SMOOTH = 25                        # centreline moving average, rows
WIDTH_SMOOTH = 61                  # width profile moving average, rows
LEAK = 1.6                         # width rejection, x the 51-row median
N_START, N_FLOOR = -2110.0, -3800.0
SAMPLE = 10                        # one vertex per 10 rows, about 20 m

# The literals --check-properties holds the committed file to. They are
# measurements of this trace, not settings of it: if the trace is re-run and
# they move, the note above is wrong about the river and has to be rewritten.
EXPECT = {
    "vertices": 85,
    "n_start_m": -2110.0,
    "n_floor_m": -3800.0,
    "width_min_m": 23.4,
    "width_max_m": 67.2,
    "width_median_m": 49.9,
    "width_at_splice_m": 32.5,
    "rejected_rows": 47,
    "scanned_rows": 860,
}
TOL = {"width": 1.5, "splice": 40.0}


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


def trace():
    import numpy as np
    from scipy import ndimage
    from PIL import Image

    gcp = json.loads(GCP.read_text())
    c = gcp["fit"]["coefficients"]
    datum = json.loads((ROOT / "data" / "datum.json").read_text())
    o_e, o_n = datum["origin_utm_e"], datum["origin_utm_n"]

    def to_local(px, py):
        return (c["a"] * px + c["b"] * py + c["c"],
                c["d"] * px + c["e"] * py + c["f"])

    a = np.asarray(Image.open(raster_path()).convert("L"), dtype=np.float32)
    sub = a[Y_TOP:Y_BOT, X_LO:X_HI]
    ink = ((ndimage.uniform_filter(sub, size=HP_BOX) - sub) > HP_THR).astype(np.float32)
    dens = ndimage.uniform_filter(ndimage.uniform_filter(ink, size=DENS_A), size=DENS_B)
    H, W = dens.shape

    INF = 1e9
    cost = np.full((H, W), INF)
    back = np.zeros((H, W), dtype=np.int32)
    s = SEED_X - X_LO
    cost[0, max(0, s - 18):min(W, s + 18)] = -dens[0, max(0, s - 18):min(W, s + 18)]
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
        cost[y] = best - dens[y]
        back[y] = arg
    path = np.zeros(H, dtype=np.int32)
    path[-1] = int(np.argmin(cost[-1]))
    for y in range(H - 1, 0, -1):
        path[y - 1] = back[y, path[y]]
    centre = ndimage.uniform_filter1d(path.astype(float), SMOOTH)

    # width: full width at half the local peak density, leaks rejected
    half = np.zeros((H, 2))
    for y in range(H):
        k = int(round(centre[y]))
        k = min(max(k, 1), W - 2)
        row = dens[y]
        t = 0.5 * row[max(0, k - 8):k + 9].max()
        i = k
        while i > max(0, k - 40) and row[i] > t:
            i -= 1
        j = k
        while j < min(W - 1, k + 40) and row[j] > t:
            j += 1
        half[y] = (i, j)
    w = half[:, 1] - half[:, 0]
    med = ndimage.median_filter(w, 51)
    bad = (w > LEAK * med) | (w < 6)
    wc = w.astype(float).copy()
    wc[bad] = np.nan
    idx = np.arange(H)
    good = ~np.isnan(wc)
    wc = np.interp(idx, idx[good], wc[good])
    wc = ndimage.uniform_filter1d(wc, WIDTH_SMOOTH)
    wperp_px = wc * np.cos(np.arctan(np.abs(np.gradient(centre))))

    # to local metres, then the banks as a perpendicular offset in METRES
    rows = []
    for y in range(H):
        e, n = to_local(centre[y] + X_LO, y + Y_TOP)
        e2, n2 = to_local(centre[y] + X_LO + wperp_px[y], y + Y_TOP)
        rows.append((n, e, np.hypot(e2 - e, n2 - n)))
    # the centreline is carried 40 m PAST the floor so both banks cross it:
    # the offset is perpendicular, so a run cut at the floor leaves the west
    # bank short of it and the east bank past it, and a sliver of dry channel
    # against the box wall.
    keep = [r for r in rows if N_FLOOR - 40.0 <= r[0] <= N_START]
    keep = keep[::SAMPLE] + ([keep[-1]] if (len(keep) - 1) % SAMPLE else [])
    keep.sort(key=lambda r: -r[0])

    cen = [(r[1], r[0]) for r in keep]
    wid = [r[2] for r in keep]
    west, east = [], []
    for i, (e, n) in enumerate(cen):
        if i == 0:
            de, dn = cen[1][0] - e, cen[1][1] - n
        elif i == len(cen) - 1:
            de, dn = e - cen[-2][0], n - cen[-2][1]
        else:
            de, dn = cen[i + 1][0] - cen[i - 1][0], cen[i + 1][1] - cen[i - 1][1]
        L = (de * de + dn * dn) ** 0.5 or 1.0
        nx, ny = dn / L, -de / L          # unit normal, pointing west when running south
        h = wid[i] / 2.0
        west.append((round(e + nx * h + o_e, 2), round(n + ny * h + o_n, 2)))
        east.append((round(e - nx * h + o_e, 2), round(n - ny * h + o_n, 2)))
    ring = west + east[::-1] + [west[0]]
    return cen, wid, west, east, ring, int(bad.sum()), H


def feature(fid, kind, geom, coords, name, note):
    return {"type": "Feature", "id": fid,
            "properties": {"kind": kind, "name": name,
                           "crest_ft_above_datum": None,
                           "confidence": "inferred", "note": note,
                           "sources": ["rees_rucker_1849"]},
            "geometry": {"type": geom, "coordinates": coords}}


SPLICE = ("The window's north edge is N -2110.0, the declared row "
          "tools/trace_south_branch.py's Wright trace last draws two banks on "
          "and the row terrain_spec's deleted `southern_branch` rule held from. "
          "The two windows abut on that row rather than within a tolerance. The "
          "south edge is the box floor at N -3800.0, which is the box and not "
          "the river: the sheet runs on another mile and a quarter.")


def build():
    cen, wid, west, east, ring, rejected, scanned = trace()
    wmin, wmax = min(wid), max(wid)
    wmed = sorted(wid)[len(wid) // 2]
    doc = {
        "type": "FeatureCollection",
        "name": "south_branch_below_twelfth",
        "crs": {"type": "name", "properties": {"name": "urn:ogc:def:crs:EPSG::26916"}},
        "_doc": (
            "The South Branch of the Chicago River from Twelfth Street to the "
            "terrain box's south wall, traced from REES & RUCKER, MAP OF CHICAGO "
            "AND VICINITY, 1849 by tools/trace_south_branch_rees_1849.py. The "
            "first geometry in this project taken from a sheet that reaches "
            "Cermak Road; see data/traces/gcp/rees_rucker_1849_gcps.json for the "
            "fit (14 section corners, RMS 25.0 m) and the tool's docstring for "
            "why a sheet fourteen years after the scene is the right one for a "
            "natural channel whose straightening is 1928-30. Every vertex here "
            "is INFERRED and every vertex here is also south of "
            "`evidence_limit`, which writes it CONF_CONJECTURAL; the field "
            "carries the more conservative of the two. This replaces the held "
            "easting recorded as L239."),
        "measured": {
            "channel_width_m": {"min": round(wmin, 1), "median": round(wmed, 1),
                                "max": round(wmax, 1)},
            "width_method": ("full width at half the local peak ink density, per "
                             "row, converted to a perpendicular width by the "
                             "centreline's slope; rows reading more than 1.6x "
                             "the 51-row median are rejected as leaks into the "
                             "adjoining lot hatching and interpolated across"),
            "width_at_splice_m": round(wid[0], 1),
            "rows_rejected": rejected, "rows_scanned": scanned,
            "cross_check": ("the committed Wright 1834 trace measures this "
                            "channel at 45.3 m at the splice row N -2110 and "
                            "stands its two banks at E +293.2 and +338.5; this "
                            "sheet, independently drawn and independently "
                            "georeferenced, puts them at E +287.1 and +319.1 -- "
                            "6.1 m and 19.4 m from Wright's, on a fit whose own "
                            "RMS is 25.0 m. The two windows meet inside their "
                            "own uncertainty. The channel reads narrower here "
                            "than Wright's 45.3 m, which is the half-maximum "
                            "rule being strict at a station where the hatch is "
                            "light, not a river that steps in."),
        },
        "features": [
            feature("south_branch_below_twelfth_water", "water", "Polygon", [ring],
                    "The South Branch between Twelfth Street and the box floor",
                    "The band between the two bank runs below. " + SPLICE),
            feature("south_branch_west_bank_below_twelfth", "bank", "LineString", west,
                    "West bank of the South Branch below Twelfth Street",
                    "The traced centreline offset west by half the measured "
                    "channel width along its own normal, in metres. " + SPLICE),
            feature("south_branch_east_bank_below_twelfth", "bank", "LineString", east,
                    "East bank of the South Branch below Twelfth Street",
                    "The traced centreline offset east by half the measured "
                    "channel width along its own normal, in metres. " + SPLICE),
        ],
    }
    return doc


def check_properties() -> int:
    """Offline. No numpy, no raster, no network -- this one can run in check.sh."""
    if not OUT.exists():
        print(f"FAIL {OUT.name} is missing")
        return 1
    d = json.loads(OUT.read_text())
    bad = []
    ids = [f["id"] for f in d["features"]]
    if ids != ["south_branch_below_twelfth_water",
               "south_branch_west_bank_below_twelfth",
               "south_branch_east_bank_below_twelfth"]:
        bad.append(f"feature ids are {ids}")
    banks = {f["id"]: f for f in d["features"] if f["properties"]["kind"] == "bank"}
    for fid, f in banks.items():
        cs = f["geometry"]["coordinates"]
        if len(cs) != EXPECT["vertices"]:
            bad.append(f"{fid} has {len(cs)} vertices, expected {EXPECT['vertices']}")
        if f["properties"]["confidence"] != "inferred":
            bad.append(f"{fid} is not inferred")
        if f["properties"]["sources"] != ["rees_rucker_1849"]:
            bad.append(f"{fid} does not cite rees_rucker_1849 alone")
    datum = json.loads((ROOT / "data" / "datum.json").read_text())
    o_n = datum["origin_utm_n"]
    for fid, f in banks.items():
        ns = [c[1] - o_n for c in f["geometry"]["coordinates"]]
        # A bank is the centreline offset PERPENDICULARLY, so its own end rows
        # straddle the declared row by up to half a channel. What has to hold is
        # that it meets the Wright window at the top and crosses the box floor
        # at the bottom -- not that it stops on either line.
        if abs(max(ns) - EXPECT["n_start_m"]) > TOL["splice"]:
            bad.append(f"{fid} starts at N {max(ns):.1f}, more than "
                       f"{TOL['splice']} m from the splice row "
                       f"{EXPECT['n_start_m']}")
        if min(ns) > EXPECT["n_floor_m"]:
            bad.append(f"{fid} ends at N {min(ns):.1f}, short of the box floor "
                       f"{EXPECT['n_floor_m']} -- it would leave dry channel "
                       f"against the south wall")
    m = d["measured"]["channel_width_m"]
    for k, want in (("min", EXPECT["width_min_m"]), ("max", EXPECT["width_max_m"]),
                    ("median", EXPECT["width_median_m"])):
        if abs(m[k] - want) > TOL["width"]:
            bad.append(f"width {k} is {m[k]} m, expected {want} m")
    if abs(d["measured"]["width_at_splice_m"] - EXPECT["width_at_splice_m"]) > TOL["width"]:
        bad.append(f"splice width is {d['measured']['width_at_splice_m']} m, "
                   f"expected {EXPECT['width_at_splice_m']} m")
    if d["measured"]["rows_rejected"] != EXPECT["rejected_rows"]:
        bad.append(f"{d['measured']['rows_rejected']} rows rejected, "
                   f"expected {EXPECT['rejected_rows']}")
    for b in bad:
        print("FAIL", b)
    if not bad:
        print(f"OK {OUT.name}: {EXPECT['vertices']} vertices a bank, "
              f"N {EXPECT['n_start_m']} to past {EXPECT['n_floor_m']}, "
              f"channel {EXPECT['width_min_m']}-{EXPECT['width_max_m']} m")
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
    m = doc["measured"]["channel_width_m"]
    print(f"wrote {OUT.relative_to(ROOT)}: "
          f"{len(doc['features'][1]['geometry']['coordinates'])} vertices a bank, "
          f"channel {m['min']}-{m['max']} m, median {m['median']} m")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
