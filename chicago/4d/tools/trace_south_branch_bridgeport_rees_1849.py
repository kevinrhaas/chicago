#!/usr/bin/env python3
"""Trace the South Branch from the box floor to the forks at BRIDGEPORT, off Rees & Rucker 1849.

T-2501, the first piece of T-2488 (Lee's Place, later Hardscrabble). The farm stood
on the South Branch "near its forks", "about half a mile below Bridgeport", and every
one of those words is measured along a reach of river this project had never traced:
`tools/trace_south_branch_rees_1849.py` stops 40 m past the box floor at N -3800,
because the box stops there, and says in its own docstring that "the sheet runs on
for another mile and a quarter". This is that mile and a quarter, read off the same
sheet, through the same georeference, by the same ink-density field.

    python3 tools/trace_south_branch_bridgeport_rees_1849.py            re-trace and write
    python3 tools/trace_south_branch_bridgeport_rees_1849.py --check    re-trace and diff
    python3 tools/trace_south_branch_bridgeport_rees_1849.py --check-properties
                                                  hold the committed file to this
                                                  file's literals: no numpy, no
                                                  network, no raster.

WHAT IT IS FOR, AND WHAT IT IS NOT
----------------------------------
For MEASURING: `tools/derive_hardscrabble_1812.py` reads distances along this
centreline, and T-2502 will carry the 1812 ground down it. It is NOT yet a layer of
any epoch. No terrain spec reads it, no heightfield is built from it, and nothing in
the scene moves when it changes. It is written to `data/terrain/`, beside the other
1812 readings, and not under `epochs/`, for that reason.

The sheet is 1849, thirty-seven years after the farm, and the reading is the same one
the reach above makes: the PLANFORM of a natural channel. No work straightened this
reach before the sheet was drawn. The Illinois & Michigan Canal (opened 1848) is drawn
as its own channel, labelled CANAL, meeting the river's south fork at Bridgeport, and
it is read here as a POINT on the river and never as a change to it. Everything is
`inferred`. It all lies south of `evidence_limit` too, and anything that later carries
it into a ground is graded conjectural there.

HOW THE CHANNEL IS FOUND
------------------------
The density field is the committed tracer's own: a 41 px high-pass of the grey plate,
thresholded at 7, then averaged over 9 px and again over 5. The parameters are imported
from that file and not copied, so the two readings cannot drift apart. Below Cermak Road
the channel turns WEST, so a programme that steps down the rows (the committed tracer's
method) cannot follow it. This one is a least-cost path over the window instead, with
each pixel costing 1 / (density + 0.05), from a seed to a goal:

* THE SEED is the committed trace's own last centreline vertex, the midpoint of its two
  banks' last vertices, 40 m below the box floor. So the two traces abut on a vertex and
  not on a tolerance.
* THE GOAL is the point where the canal meets the river (Bridgeport), picked by eye
  off the sheet. It is a read pixel with a stated precision, not a fitted one, and it is
  stored in `PICKS` below.
* THE FORKS, where the west fork leaves the channel and the south fork carries on to the
  canal, are picked the same way. The station is the centreline vertex nearest the pick.

The path crosses two of the sheet's fold columns, near x 2470 and x 1860, where the crease
erases a few pixels of hatch. The least-cost path crosses a gap that narrow with no help,
because going round it costs more.

THE BANKS are read the way the committed tracer reads them: the full width at half the
local peak density, here along each vertex's own normal (the channel is no longer running
down the rows). Readings over 1.6 times the running median are rejected as leaks into the
lot lines and the two small inlets on the north bank, then filled by interpolation and
smoothed. Each bank is the centreline offset by half that width, in metres in the local
frame. They stop at the forks. Below the forks the channel splits, and a half-width means
nothing there, so the 130 m from the forks to the canal junction is a measuring line
(centreline) only.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import trace_south_branch_rees_1849 as above  # noqa: E402  (the reach above, and its field)

GCP = above.GCP
ABOVE = above.OUT
OUT = ROOT / "data" / "terrain" / "1812_south_branch_to_bridgeport.geojson"

# The window, in the raster's own pixels: from just above the seed down to below the canal.
X_LO, X_HI, Y_LO, Y_HI = 1650, 2900, 4800, 5450
COST_EPS = 0.05                    # cost of a pixel = 1 / (density + COST_EPS)
SMOOTH = 25                        # centreline moving average, path pixels
SAMPLE = 10                        # one vertex per 10 path pixels, about 20 m
NORMAL_HALF = 40                   # px either side of the centre a width reading looks
LEAK, LEAK_WIN = 1.6, 7            # reject width > LEAK x the running median of LEAK_WIN vertices
WIDTH_SMOOTH = 5                   # width profile moving average, vertices

# Read by eye off the sheet (T-2501, 2026-10-15), each with the precision of the reading.
PICKS = {
    "bridgeport": {
        "px": [1762.0, 5350.0],
        "what": "Where the canal, drawn as a hatched channel and lettered CANAL along it, "
                "opens into the river's south fork from the south-west. The pick is on the "
                "river's centreline at the canal's mouth.",
        "precision_px": 8,
    },
    "forks": {
        "px": [1797.0, 5288.0],
        "what": "The junction where the west fork leaves the channel westward and the south "
                "fork carries on south to the canal: the centre of the widened water there.",
        "precision_px": 10,
    },
}

# The literals --check-properties holds the committed file to. These are measurements of
# this trace, not settings for it. If the trace is re-run and they move, the notes below
# say the wrong thing about the river and have to be rewritten.
EXPECT = {
    "vertices": 107,
    "bank_vertices": 101,
    "length_m": 2416.9,
    "forks_along_m": 2269.2,
    "width_min_m": 30.1,
    "width_median_m": 57.6,
    "width_max_m": 87.1,
    "rejected": 4,
}
TOL = {"length": 5.0, "width": 1.5}


def load(p: Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8"))


def seed_local(datum: dict) -> tuple[float, float]:
    """The committed reach's last centreline vertex: the midpoint of its banks' ends."""
    feats = {f["properties"]["name"]: f for f in load(ABOVE)["features"]}
    w = feats["West bank of the South Branch below Twelfth Street"]["geometry"]["coordinates"][-1]
    e = feats["East bank of the South Branch below Twelfth Street"]["geometry"]["coordinates"][-1]
    oe, on = datum["origin_utm_e"], datum["origin_utm_n"]
    return ((w[0] + e[0]) / 2 - oe, (w[1] + e[1]) / 2 - on)


def trace():
    import numpy as np
    from scipy import ndimage
    from scipy.sparse import coo_matrix
    from scipy.sparse.csgraph import dijkstra
    from PIL import Image

    gcp = load(GCP)
    c = gcp["fit"]["coefficients"]
    datum = load(ROOT / "data" / "datum.json")
    A = np.array([[c["a"], c["b"]], [c["d"], c["e"]]])
    off = np.array([c["c"], c["f"]])

    def to_local(px, py):
        return (c["a"] * px + c["b"] * py + c["c"], c["d"] * px + c["e"] * py + c["f"])

    def to_px(e, n):
        return np.linalg.solve(A, np.array([e, n]) - off)

    Image.MAX_IMAGE_PIXELS = None
    a = np.asarray(Image.open(above.raster_path()).convert("L"), dtype=np.float32)
    sub = a[Y_LO:Y_HI, X_LO:X_HI]
    ink = ((ndimage.uniform_filter(sub, size=above.HP_BOX) - sub) > above.HP_THR).astype(np.float32)
    dens = ndimage.uniform_filter(ndimage.uniform_filter(ink, size=above.DENS_A), size=above.DENS_B)
    H, W = dens.shape

    # least-cost path, 8-connected, edge weight = mean node cost x step length
    node = 1.0 / (dens + COST_EPS)
    idx = np.arange(H * W).reshape(H, W)
    rows, cols, wts = [], [], []
    for dy, dx in ((0, 1), (1, 0), (1, 1), (1, -1)):
        ys, ys2 = slice(0, H - dy), slice(dy, H)
        xs = slice(max(0, -dx), W - max(0, dx))
        xs2 = slice(max(0, -dx) + dx, W - max(0, dx) + dx)
        u = idx[ys, xs].ravel()
        v = idx[ys2, xs2].ravel()
        w = 0.5 * (node[ys, xs].ravel() + node[ys2, xs2].ravel()) * math.hypot(dx, dy)
        rows += [u, v]
        cols += [v, u]
        wts += [w, w]
    G = coo_matrix((np.concatenate(wts), (np.concatenate(rows), np.concatenate(cols))),
                   shape=(H * W, H * W)).tocsr()

    sx, sy = to_px(*seed_local(datum))
    gx, gy = PICKS["bridgeport"]["px"]
    s = int(round(sy - Y_LO)) * W + int(round(sx - X_LO))
    g = int(round(gy - Y_LO)) * W + int(round(gx - X_LO))
    _, pred = dijkstra(G, indices=s, return_predecessors=True)
    path = [g]
    while path[-1] != s:
        p = pred[path[-1]]
        if p < 0:
            raise SystemExit("no path from the seed to Bridgeport inside the window")
        path.append(int(p))
    path.reverse()
    py = np.array([p // W for p in path], dtype=float) + Y_LO
    px = np.array([p % W for p in path], dtype=float) + X_LO
    # pin the ends to the seed and the pick exactly before smoothing
    px[0], py[0], px[-1], py[-1] = sx, sy, gx, gy
    spx = ndimage.uniform_filter1d(px, SMOOTH, mode="nearest")
    spy = ndimage.uniform_filter1d(py, SMOOTH, mode="nearest")
    spx[0], spy[0], spx[-1], spy[-1] = sx, sy, gx, gy
    keep = list(range(0, len(spx), SAMPLE))
    if keep[-1] != len(spx) - 1:
        keep.append(len(spx) - 1)
    vx, vy = spx[keep], spy[keep]

    # the forks station: the vertex nearest the pick
    fx, fy = PICKS["forks"]["px"]
    k_forks = int(np.argmin((vx - fx) ** 2 + (vy - fy) ** 2))

    # width along each vertex's normal, at half the local peak
    n = len(vx)
    widths = np.zeros(n)
    for i in range(n):
        j0, j1 = max(0, i - 1), min(n - 1, i + 1)
        tx, ty = vx[j1] - vx[j0], vy[j1] - vy[j0]
        L = math.hypot(tx, ty) or 1.0
        nx, ny = -ty / L, tx / L
        t = np.arange(-NORMAL_HALF, NORMAL_HALF + 1, dtype=float)
        prof = ndimage.map_coordinates(dens, [vy[i] - Y_LO + t * ny, vx[i] - X_LO + t * nx],
                                       order=1, mode="nearest")
        k = NORMAL_HALF
        thr = 0.5 * prof[k - 8:k + 9].max()
        lo = k
        while lo > 0 and prof[lo] > thr:
            lo -= 1
        hi = k
        while hi < len(prof) - 1 and prof[hi] > thr:
            hi += 1
        widths[i] = hi - lo
    reach = slice(0, k_forks + 1)
    wr = widths[reach].copy()
    med = ndimage.median_filter(wr, LEAK_WIN, mode="nearest")
    bad = (wr > LEAK * med) | (wr < 6)
    ii = np.arange(len(wr))
    wr[bad] = np.interp(ii[bad], ii[~bad], wr[~bad])
    wr = ndimage.uniform_filter1d(wr, WIDTH_SMOOTH, mode="nearest")

    oe, on = datum["origin_utm_e"], datum["origin_utm_n"]
    cen = [to_local(x, y) for x, y in zip(vx, vy)]
    wid_m = []
    for i in range(len(wr)):
        e0, n0 = to_local(vx[i], vy[i])
        e1, n1 = to_local(vx[i] + wr[i], vy[i])
        wid_m.append(math.hypot(e1 - e0, n1 - n0))
    west, east = [], []
    for i in range(len(wr)):
        j0, j1 = max(0, i - 1), min(len(cen) - 1, i + 1)
        de, dn = cen[j1][0] - cen[j0][0], cen[j1][1] - cen[j0][1]
        L = math.hypot(de, dn) or 1.0
        # running downstream-to-upstream means heading south-west then west; the normal
        # to the RIGHT of travel (dn, -de) points north-west, onto the north-west bank
        rx, ry = dn / L, -de / L
        h = wid_m[i] / 2.0
        e, nn = cen[i]
        west.append((round(e + rx * h + oe, 2), round(nn + ry * h + on, 2)))
        east.append((round(e - rx * h + oe, 2), round(nn - ry * h + on, 2)))
    return {
        "centreline": [(round(e + oe, 2), round(nn + on, 2)) for e, nn in cen],
        "k_forks": k_forks,
        "nw_bank": west,
        "se_bank": east,
        "widths_m": [round(x, 1) for x in wid_m],
        "rejected": int(bad.sum()),
        "seed_px": [round(float(sx), 1), round(float(sy), 1)],
    }


def length(pts) -> float:
    return sum(math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1))


def feature(fid, kind, geom, coords, name, note, extra=None):
    props = {"kind": kind, "name": name, "confidence": "inferred", "note": note,
             "sources": ["rees_rucker_1849"]}
    props.update(extra or {})
    return {"type": "Feature", "id": fid, "properties": props,
            "geometry": {"type": geom, "coordinates": coords}}


def build() -> dict:
    t = trace()
    cen, k = t["centreline"], t["k_forks"]
    reach = cen[:k + 1]
    ring = [list(p) for p in t["nw_bank"]] + [list(p) for p in t["se_bank"][::-1]]
    ring.append(ring[0])
    w = sorted(t["widths_m"])
    measured = {
        "vertices": len(cen),
        "bank_vertices": len(t["nw_bank"]),
        "length_m": round(length(cen), 1),
        "forks_along_m": round(length(reach), 1),
        "width_min_m": w[0],
        "width_median_m": w[len(w) // 2],
        "width_max_m": w[-1],
        "rejected": t["rejected"],
    }
    win = ("The window starts at the committed reach's last centreline vertex, 40 m below "
           "the box floor, so the two traces abut on a vertex.")
    feats = [
        feature("south_branch_to_bridgeport_centreline", "centreline", "LineString",
                [list(p) for p in cen],
                "The South Branch's centreline from the box floor to the canal at Bridgeport",
                "A least-cost path over the sheet's ink-density field, from the seed to the "
                "canal's mouth, smoothed and sampled every 10 px (about 20 m). It runs "
                "downstream to upstream: south-west, then west through the forks, then 130 m up "
                "the south fork to the canal. Distances are measured along this line. " + win,
                {"forks_vertex": k}),
        feature("south_branch_to_forks_water", "water", "Polygon", [ring],
                "The South Branch between the box floor and the forks",
                "The band between the two bank runs below. It stops at the forks: below them "
                "the channel splits, and a half-width means nothing there."),
        feature("south_branch_to_forks_nw_bank", "bank", "LineString",
                [list(p) for p in t["nw_bank"]],
                "North-west bank of the South Branch, box floor to the forks",
                "The centreline offset to its right, looking upstream, by half the measured width "
                "along its own normal, in metres. This is the bank Hubbard calls 'the north side' "
                "and Moses and Kirkland 'the northwestern side'. On the sheet it is acreage "
                "(W. Greene, J. O'Niel, T. O'Niel, E. McConnell) and not platted lots."),
        feature("south_branch_to_forks_se_bank", "bank", "LineString",
                [list(p) for p in t["se_bank"]],
                "South-east bank of the South Branch, box floor to the forks",
                "The centreline offset to its left, looking upstream. On the sheet it is the "
                "platted ground of section 29 along Water Street."),
    ]
    for key, pick in PICKS.items():
        e, n = above_to_utm(pick["px"])
        feats.append(feature(f"pick_{key}", "pick", "Point", [e, n],
                             {"bridgeport": "Bridgeport: where the canal opens into the river",
                              "forks": "The forks of the South Branch"}[key],
                             pick["what"] + f" Read by eye to +/-{pick['precision_px']} px "
                             f"(about {round(pick['precision_px'] * 2.05)} m), inside the fit's "
                             "25.0 m RMS.", {"px": pick["px"], "precision_px": pick["precision_px"]}))
    return {
        "type": "FeatureCollection",
        "name": "south_branch_to_bridgeport_1812",
        "crs": {"type": "name", "properties": {"name": "urn:ogc:def:crs:EPSG::26916"}},
        "_doc": "GENERATED by tools/trace_south_branch_bridgeport_rees_1849.py (T-2501) - do "
                "not hand-edit. The South Branch from the 1812/1834 box floor to the forks and "
                "the canal at Bridgeport, traced off REES & RUCKER 1849 through its committed "
                "georeference (data/traces/gcp/rees_rucker_1849_gcps.json, RMS 25.0 m). It is a "
                "MEASURING line for tools/derive_hardscrabble_1812.py and the input T-2502 will "
                "carry the 1812 ground down. No epoch reads it yet, and nothing in any scene "
                "moves when it changes. Everything here is inferred: the planform of a natural "
                "channel, drawn thirty-seven years after 1812, with no straightening of this reach "
                "before the sheet. See the tool's docstring.",
        "seed_px": t["seed_px"],
        "measured": measured,
        "features": feats,
    }


def above_to_utm(px_py):
    c = load(GCP)["fit"]["coefficients"]
    datum = load(ROOT / "data" / "datum.json")
    x, y = px_py
    return [round(c["a"] * x + c["b"] * y + c["c"] + datum["origin_utm_e"], 2),
            round(c["d"] * x + c["e"] * y + c["f"] + datum["origin_utm_n"], 2)]


def render(doc: dict) -> str:
    return json.dumps(doc, indent=1, ensure_ascii=False) + "\n"


def check_properties() -> int:
    if not OUT.exists():
        print(f"FAIL: {OUT.relative_to(ROOT)} is missing")
        return 1
    doc = load(OUT)
    m = doc.get("measured", {})
    bad = []
    for k, want in EXPECT.items():
        have = m.get(k)
        if want is None or have is None:
            bad.append(f"{k}: committed {have}, expected {want}")
            continue
        tol = TOL["length"] if k.endswith("along_m") or k == "length_m" else (
            TOL["width"] if k.startswith("width") else 0)
        if abs(have - want) > tol:
            bad.append(f"{k}: committed {have}, expected {want} (+/-{tol})")
    feats = {f["id"]: f for f in doc.get("features", [])}
    cen = feats.get("south_branch_to_bridgeport_centreline")
    if not cen or cen["geometry"]["coordinates"][-1] != above_to_utm(PICKS["bridgeport"]["px"]):
        bad.append("the centreline does not end on the Bridgeport pick")
    for f in doc.get("features", []):
        if f["properties"].get("confidence") != "inferred":
            bad.append(f"{f['id']}: confidence {f['properties'].get('confidence')}, not inferred")
        if f["properties"].get("sources") != ["rees_rucker_1849"]:
            bad.append(f"{f['id']}: sources are not exactly rees_rucker_1849")
    if bad:
        for b in bad:
            print(f"FAIL: {b}")
        return 1
    print(f"ok: {OUT.relative_to(ROOT)} holds its measured literals "
          f"({m['vertices']} vertices, {m['length_m']} m, forks at {m['forks_along_m']} m)")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--check-properties", action="store_true")
    args = ap.parse_args()
    if args.check_properties:
        return check_properties()
    text = render(build())
    if args.check:
        have = OUT.read_text(encoding="utf-8") if OUT.exists() else ""
        if have != text:
            print(f"DRIFT: {OUT.relative_to(ROOT)} is not what the sheet traces to")
            return 1
        print(f"ok: {OUT.relative_to(ROOT)} re-traces")
        return 0
    OUT.write_text(text, encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}: " + json.dumps(json.loads(text)["measured"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
