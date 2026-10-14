#!/usr/bin/env python3
"""Trace the Illinois Central / Michigan Central tracks the 1904 lakefront stands on (T-2478).

    python3 tools/trace_ic_tracks_1904.py            re-trace and write data/railway/1904.json
    python3 tools/trace_ic_tracks_1904.py --check    re-trace and diff (needs Pillow + numpy)
    python3 tools/trace_ic_tracks_1904.py --check-properties
                                                     hold the committed file together, no raster

WHAT THE SHEETS DRAW. Sanborn's 1911 Chicago vol. 3 sheets 20 (16th to 18th Street) and 28
(18th to 20th) draw the railway east of Prairie Avenue and Calumet Avenue track by track, and
draw each track as TWO pen lines about 27 px (1.4 m) apart: its two rails. So a track is found
on a raster row as a pair of dark peaks 1.0-1.9 m apart in local metres, and its centreline is
the pair's midpoint. Single lines -- the right-of-way line, the lake edge, lettering, lot lines
-- do not pair and are dropped. Both sheets are georeferenced by tools/georef_prairie_1904.py
(data/traces/gcp/); this tool reads them through the same fits trace_ic_edge_1904.py does.

THE SHORE FRAME. Every centre is written as (s, d): s the distance along (a smoothed copy of) the
scene's own waterline `shore_1904_ic_edge` (data/terrain/epochs/e1871_postfire/shoreline.geojson, L287)
from its north end, and d the distance WEST of that line. Tracks run nearly parallel to the
shore, so a track is a slowly varying d(s), and linking a row's centres to the next row's is a
nearest-d match. The scene's waterline is the 1911 edge on these two reaches, so a track's d is
also its distance from the water the visitor sees.

LINKING. Rows are read every ROW_STEP px (about 2 m of s). A chain takes the nearest centre in
the next row within LINK_D_M of its own last d, missing at most GAP_ROWS rows (lettering such as
"ILLINOIS CENTRAL R.R." breaks a pair for a few rows). Chains shorter than MIN_POINTS are noise.

WHAT THE SHEETS DO NOT DRAW, AND WHAT STANDS IN. Neither sheet reaches the whole box:

  gap      sheet 20's paper stops at about E +1516, so east of that line from about N -3050
           to sheet 28's top edge (N -3165) no sheet draws a track. A chain that ends at the
           gap is joined to the chain starting beyond it whose d is nearest (within JOIN_D_M),
           straight across in (s, d). A chain with no partner ends where it was last drawn,
           closing on its nearest neighbour over MERGE_M as a turnout would: that is where
           the yard's ladder took it, and its shape is ours.
  ends     north of sheet 20's top (N -2897) and south of sheet 28's foot the chains are
           carried on at their last d to the box (N -2900 .. -3800): the shore runs on, the
           sheets do not, and nothing bounds it -- the same footing as the waterline's own
           segment F (L287).

Both stand-ins are RECONSTRUCTED and the file says which stretch of each track is which.

WHY THE 1911 LAYOUT FOR 1904. The 1891 Greeley-Carlson atlas (Prairie library
st-greeley-carlson-1891-prairie-environs) draws four or five tracks and the water just east of
them; 1911 draws eleven at 18th Street with 14-21 m of made ground beyond. The scene's
waterline already stands on the 1911 edge (L287, the nearer date), so the right-of-way it
bounds is the 1911 one, and the tracks on it are the 1911 tracks. George Glessner's photograph
looking north from 18th Street (st-ghm-george-glessner-ic-train-18th, c. 1887-1900) already
shows at least seven. How many were down on 1 July 1904 is not known; the liberty says so.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

try:
    import numpy as np
except ImportError:  # the gate's --check degrades to the committed file's properties
    np = None

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import trace_ic_edge_1904 as edge  # noqa: E402  (the same rasters, fits and datum)

OUT = ROOT / "data" / "railway" / "1904.json"
SHORE = ROOT / "data" / "terrain" / "epochs" / "e1871_postfire" / "shoreline.geojson"
SPEC = ROOT / "data" / "railway" / "1904_spec.json"

BOX_N = (-3800.0, -2900.0)
SHEETS = {
    # key in data/traces/gcp, raster, rows read, the column window searched
    "sanborn_1911_v3_sheet_20": {"raster": "sanborn_1911_vol3_sheet_20.jpg", "rows": (120, 7300),
                                 "cols": (3300, 5800), "source": "sanborn_1911_chicago_v3_sheet_20"},
    "sanborn_1911_v3_sheet_28": {"raster": "sanborn_1911_vol3_sheet_28.jpg", "rows": (120, 7300),
                                 "cols": (3600, 5800), "source": "sanborn_1911_chicago_v3_sheet_28"},
}
ROW_STEP = 40
PAIR_M = (1.0, 1.9)        # a track's two rails as drawn, metres apart along a raster row
EDGE_CLEAR_M = 2.0         # a centre this close to the water is the edge's own pen work
BIN_M = 10.0               # rows are voted on in bins of this much s
CLUSTER_GAP_M = 1.2        # two centres further apart than this in d are two tracks
SUPPORT = 0.4              # a track is kept in a bin when this share of its rows drew it
LINK_D_M = 1.6             # bin to bin, a chain's next d lies within this of its last
GAP_BINS = 2
SAME_TRACK_M = 1.5         # two chains this close in d are one track read twice
MIN_BINS = 3
JOIN_D_M = 3.5             # across the gap, a partner's d within this of the chain's
GAP_REACH_M = 140.0        # a sheet-20 chain ending further than this short of sheet 28 is not joined
MERGE_M = 30.0             # an end with no partner closes on its neighbour over this length
STEP_M = 5.0               # output vertex spacing along s


# ---------------------------------------------------------------------------
# the shore frame

def shore_line() -> list[tuple[float, float]]:
    doc = json.loads(SHORE.read_text(encoding="utf-8"))
    for f in doc["features"]:
        if f["properties"].get("role") == "scene_line" or f["properties"].get("name") == "shore_1904_ic_edge":
            return [(x - edge.OE, y - edge.ON) for x, y in f["geometry"]["coordinates"]]
    raise SystemExit("shore_1904_ic_edge not found in " + str(SHORE))


def smoothed(line, step=10.0, half=60.0):
    """The waterline resampled every `step` metres of N and averaged over +/- `half`: the
    traced pen line has kinks a metre or two across (sheet 28's run starts with one), and
    an offset curve taken from a kinked line fans out behind every kink."""
    line = sorted(line, key=lambda p: -p[1])
    ns = [line[0][1] - k * step for k in range(int((line[0][1] - line[-1][1]) // step) + 1)]

    def e_at(n):
        for a, b in zip(line, line[1:]):
            if b[1] <= n <= a[1]:
                f = (a[1] - n) / ((a[1] - b[1]) or 1e-9)
                return a[0] + f * (b[0] - a[0])
        return line[-1][0]
    es = [e_at(n) for n in ns]
    k = int(half // step)
    out = []
    for i, n in enumerate(ns):
        lo, hi = max(0, i - k), min(len(es), i + k + 1)
        # near an end the window is made symmetric so the line is not pulled sideways
        w = min(i - lo, hi - 1 - i)
        win = es[i - w:i + w + 1]
        out.append((sum(win) / len(win), n))
    return out


class Frame:
    """Arc length along the smoothed waterline, north to south, and distance west of it."""

    def __init__(self, line):
        line = smoothed(line)
        self.p = line
        self.s = [0.0]
        for a, b in zip(line, line[1:]):
            self.s.append(self.s[-1] + math.dist(a, b))

    def to_sd(self, e, n):
        best = None
        for i, (a, b) in enumerate(zip(self.p, self.p[1:])):
            ax, ay = a
            bx, by = b
            vx, vy = bx - ax, by - ay
            L2 = vx * vx + vy * vy or 1e-9
            t = max(0.0, min(1.0, ((e - ax) * vx + (n - ay) * vy) / L2))
            qx, qy = ax + t * vx, ay + t * vy
            dist = math.hypot(e - qx, n - qy)
            if best is None or dist < best[0]:
                L = math.sqrt(L2)
                # west of a southward-running line is to its right: cross product sign
                side = 1.0 if (vx * (n - ay) - vy * (e - ax)) < 0 else -1.0
                best = (dist, self.s[i] + t * L, side * dist)
        return best[1], best[2]

    def to_en(self, s, d):
        """Back from (s, d); past either end of the line it runs on along the end segment."""
        i = len(self.s) - 2
        for k in range(len(self.s) - 1):
            if self.s[k + 1] >= s:
                i = k
                break
        a, b = self.p[i], self.p[i + 1]
        L = (self.s[i + 1] - self.s[i]) or 1e-9
        t = (s - self.s[i]) / L
        ux, uy = (b[0] - a[0]) / L, (b[1] - a[1]) / L
        # west of a southward line: rotate the along-vector (ux, uy) by +90 deg -> (-uy, ux)
        wx, wy = -uy, ux
        if wx > 0:                                         # keep "west" pointing to -E
            wx, wy = -wx, -wy
        return (a[0] + t * (b[0] - a[0]) + d * wx, a[1] + t * (b[1] - a[1]) + d * wy)

    def s_at_n(self, n):
        for i, (a, b) in enumerate(zip(self.p, self.p[1:])):
            if b[1] <= n <= a[1]:
                t = (a[1] - n) / ((a[1] - b[1]) or 1e-9)
                return self.s[i] + t * (self.s[i + 1] - self.s[i])
        return self.s[0] if n > self.p[0][1] else self.s[-1]


# ---------------------------------------------------------------------------
# reading

def read_sheet(key, spec, frame):
    import numpy as np
    im = edge.load_rgb(spec["raster"])
    fit = edge.fit_of(key)
    rows = []
    for y in range(spec["rows"][0], min(spec["rows"][1], im.shape[0] - 3), ROW_STEP):
        xs = edge.track_lines(im, y, spec["cols"][0], spec["cols"][1])
        if len(xs) < 2:
            continue
        loc = [fit(x, y) for x in xs]
        # the water's edge at this row: the frame's d = 0 line
        centres = []
        i = 0
        while i < len(xs) - 1:
            gap = math.dist(loc[i], loc[i + 1])
            if PAIR_M[0] <= gap <= PAIR_M[1]:
                xm = (xs[i] + xs[i + 1]) / 2
                e, n = fit(xm, y)
                s, d = frame.to_sd(e, n)
                if d > EDGE_CLEAR_M:
                    centres.append((round(s, 2), round(d, 2)))
                i += 2
            else:
                i += 1
        if centres:
            rows.append({"row": y, "centres": sorted(centres, key=lambda c: c[1])})
    del np
    return rows


def stations(rows, s_from=None, s_to=None):
    """Per BIN_M of s, the tracks the bin's rows agree on: centres clustered by d (a new
    cluster past CLUSTER_GAP_M), kept where it is drawn at least SUPPORT as often as the bin's
best-drawn track, and
    written at the cluster's median (the vote is against the best-drawn track in the bin). One row's stray pair -- a letter, a hatch, a lot line
    meeting a track -- does not survive the vote."""
    import statistics
    bins = {}
    for r in rows:
        for s, d in r["centres"]:
            if (s_from is not None and s < s_from) or (s_to is not None and s > s_to):
                continue
            bins.setdefault(int(s // BIN_M), {}).setdefault(r["row"], []).append(d)
    out = []
    for b in sorted(bins):
        rowsd = bins[b]
        ds = sorted(d for v in rowsd.values() for d in v)
        clusters, cur = [], [ds[0]]
        for d in ds[1:]:
            if d - cur[-1] > CLUSTER_GAP_M:
                clusters.append(cur)
                cur = [d]
            else:
                cur.append(d)
        clusters.append(cur)
        # a row crosses the yard on a slant, so each track is drawn by only some of a bin's
        # rows: the vote is against the best-drawn track in the bin, not the row count
        best = max(len(c) for c in clusters)
        keep = [round(statistics.median(c), 2) for c in clusters if len(c) >= max(2, SUPPORT * best)]
        if keep:
            out.append({"s": round((b + 0.5) * BIN_M, 1), "d": keep})
    return out


def chains_of(st):
    """Bin to bin, each chain takes the nearest kept d within LINK_D_M, skipping at most
    GAP_BINS bins; chains shorter than MIN_BINS are dropped."""
    done, live = [], []
    for b in st:
        used = set()
        for ch in sorted(live, key=lambda c: c["pts"][-1][1]):
            last = ch["pts"][-1][1]
            cand = [(abs(d - last), j) for j, d in enumerate(b["d"]) if j not in used and abs(d - last) <= LINK_D_M]
            if cand:
                _, j = min(cand)
                used.add(j)
                ch["pts"].append((b["s"], b["d"][j]))
                ch["miss"] = 0
            else:
                ch["miss"] += 1
        for j, d in enumerate(b["d"]):
            if j not in used:
                live.append({"pts": [(b["s"], d)], "miss": 0})
        keep = []
        for ch in live:
            (done if ch["miss"] > GAP_BINS else keep).append(ch)
        live = keep
    return dedupe([c["pts"] for c in done + live if len(c["pts"]) >= MIN_BINS])


def dedupe(chains):
    """One track read as two chains -- a break in the vote, then a fresh start beside the
    old one -- is one track: two chains whose d agree within SAME_TRACK_M wherever both are
    drawn (and that overlap or nearly meet in s) are merged, their shared bins averaged."""
    def d_on(c):
        return {s: d for s, d in c}

    changed = True
    while changed:
        changed = False
        for i in range(len(chains)):
            for j in range(i + 1, len(chains)):
                a, b = d_on(chains[i]), d_on(chains[j])
                common = set(a) & set(b)
                if common:
                    near = sum(abs(a[s] - b[s]) for s in common) / len(common) < SAME_TRACK_M
                else:
                    (ea, eb) = (chains[i][-1], chains[j][0]) if chains[i][-1][0] < chains[j][0][0] else (chains[j][-1], chains[i][0])
                    near = 0 < eb[0] - ea[0] <= (GAP_BINS + 2) * BIN_M and abs(eb[1] - ea[1]) < SAME_TRACK_M
                if near:
                    merged = {**a, **b}
                    for s in common:
                        merged[s] = round((a[s] + b[s]) / 2, 2)
                    chains[i] = sorted(merged.items())
                    del chains[j]
                    changed = True
                    break
            if changed:
                break
    return chains


def assemble(frame, st20, st28):
    """Sheet 20's chains and sheet 28's, joined across the gap between the papers; heads and
    tails the paper cut carried to the box; any other end closed on its neighbour."""
    s_lo, s_hi = frame.s_at_n(BOX_N[1]), frame.s_at_n(BOX_N[0])
    north = [{"pts": c, "src": "sanborn_1911_chicago_v3_sheet_20"} for c in chains_of(st20)]
    south = [{"pts": c, "src": "sanborn_1911_chicago_v3_sheet_28"} for c in chains_of(st28)]
    s28_top = min(c["pts"][0][0] for c in south)
    s20_top = min(c["pts"][0][0] for c in north)

    def seg(a, b, how, src=None):
        out = {"from_s": round(a, 1), "to_s": round(b, 1), "how": how}
        if src:
            out["source"] = src
        return out

    tracks, taken = [], set()
    for a in sorted(north, key=lambda c: c["pts"][-1][1]):
        end_s, end_d = a["pts"][-1]
        cand = [(abs(b["pts"][0][1] - end_d), k) for k, b in enumerate(south) if k not in taken
                and b["pts"][0][0] <= s28_top + 2 * BIN_M and abs(b["pts"][0][1] - end_d) <= JOIN_D_M]
        if cand and end_s >= s28_top - GAP_REACH_M:
            _, k = min(cand)
            taken.add(k)
            b = south[k]
            tracks.append({"pts": a["pts"] + b["pts"], "segments": [
                seg(a["pts"][0][0], end_s, "traced", a["src"]),
                seg(end_s, b["pts"][0][0], "joined_across_gap"),
                seg(b["pts"][0][0], b["pts"][-1][0], "traced", b["src"])], "tail_src": b["src"]})
        else:
            tracks.append({"pts": list(a["pts"]), "segments": [seg(a["pts"][0][0], end_s, "traced", a["src"])],
                           "tail_src": a["src"]})
    for k, b in enumerate(south):
        if k not in taken:
            tracks.append({"pts": list(b["pts"]), "segments": [seg(b["pts"][0][0], b["pts"][-1][0], "traced", b["src"])],
                           "tail_src": b["src"]})

    def d_at(t, s):
        p = t["pts"]
        if s < p[0][0] or s > p[-1][0]:
            return None
        for i in range(len(p) - 1):
            if p[i + 1][0] >= s:
                f = 0 if p[i + 1][0] == p[i][0] else (s - p[i][0]) / (p[i + 1][0] - p[i][0])
                return p[i][1] + f * (p[i + 1][1] - p[i][1])
        return p[-1][1]

    def neighbour(t, s, d0):
        best = None
        for u in tracks:
            if u is t:
                continue
            dn = d_at(u, s)
            if dn is not None and abs(dn - d0) < 9 and (best is None or abs(dn - d0) < abs(best - d0)):
                best = dn
        return best

    for t in tracks:
        # head: a track that starts at sheet 20's top edge runs on north to the box
        s0, d0 = t["pts"][0]
        if s0 - s20_top <= BIN_M:
            t["pts"].insert(0, (round(s_lo - 25, 1), d0))
            t["segments"].insert(0, seg(s_lo, s0, "carried_past_sheet"))
        else:
            nb = neighbour(t, s0 - MERGE_M, d0)
            if nb is not None:
                ins = [(round(s0 - MERGE_M * k / 6, 1), round(d0 + (nb - d0) * smoothstep(k / 6), 3)) for k in range(6, 0, -1)]
                t["pts"][:0] = ins
                t["segments"].insert(0, seg(s0 - MERGE_M, s0, "closes_on_neighbour"))
        # tail: sheet 28's paper edge cuts the yard on a slant, east tracks first, and every
        # tail it cuts runs on south to the box; a tail inside sheet 20 closes on a neighbour
        s1, d1 = t["pts"][-1]
        if t["tail_src"] == "sanborn_1911_chicago_v3_sheet_28":
            t["pts"].append((round(s_hi + 25, 1), d1))
            t["segments"].append(seg(s1, s_hi, "carried_past_sheet"))
        else:
            nb = neighbour(t, s1 + MERGE_M, d1)
            if nb is not None:
                t["pts"] += [(round(s1 + MERGE_M * k / 6, 1), round(d1 + (nb - d1) * smoothstep(k / 6), 3)) for k in range(1, 7)]
                t["segments"].append(seg(s1, s1 + MERGE_M, "closes_on_neighbour"))
    return tracks, {"sheet20_from_s": s20_top, "sheet28_from_s": s28_top, "box_s": [round(s_lo, 1), round(s_hi, 1)]}


def smoothstep(f):
    return f * f * (3 - 2 * f)


def densify(pts):
    """d(s) resampled every STEP_M so a straight run between two bins is a straight line on the ground."""
    out = [pts[0]]
    for a, b in zip(pts, pts[1:]):
        n = max(1, int((b[0] - a[0]) // STEP_M))
        for k in range(1, n + 1):
            f = k / n
            out.append((round(a[0] + (b[0] - a[0]) * f, 2), round(a[1] + (b[1] - a[1]) * f, 3)))
    return out


HF_DIR = ROOT / "data" / "terrain" / "epochs" / "e1871_postfire"
MIN_RUN_M = 20.0           # a run shorter than this between face cuts is not laid
GRID = ROOT / "data" / "street_grid" / "1904.json"
ROW_REACH_M = 15.0         # the cinder edge follows the outermost track this far either way
FACE_DROP_M = 0.25         # ground this far below the crest 8 m inland is the embankment face


def heightfield():
    import numpy as np
    h = json.loads((HF_DIR / "heightfield.json").read_text(encoding="utf-8"))
    a = np.fromfile(HF_DIR / "heightfield.bin", dtype="<i2").reshape(h["rows"], h["cols"]) * h["scale"]

    def z(e, n):
        c = (e - h["origin_e"]) / h["cell_m"]
        r = (n - h["origin_n"]) / h["cell_m"]
        c0, r0 = int(max(0, min(h["cols"] - 2, math.floor(c)))), int(max(0, min(h["rows"] - 2, math.floor(r))))
        fc, fr = min(1.0, max(0.0, c - c0)), min(1.0, max(0.0, r - r0))
        return float((a[r0, c0] * (1 - fc) + a[r0, c0 + 1] * fc) * (1 - fr) + (a[r0 + 1, c0] * (1 - fc) + a[r0 + 1, c0 + 1] * fc) * fr)
    return z


def off_the_face(frame, z, pts):
    """The runs of a track whose bed stands on the graded crest. North of 16th Street the
    scene's waterline is the 1886 planform moved east (L287 segment A), not the 1911 edge the
    sheet's tracks stood beside, and there the committed ground has begun to fall to the lake
    within a few metres of the easternmost tracks. A bed is never hung on the embankment's
    face: where the ground under a centreline stands FACE_DROP_M below the ground 8 m inland
    of it, that stretch is left out, and the file says so."""
    runs, cur = [], []
    for s, d in pts:
        e, n = frame.to_en(s, d)
        e2, n2 = frame.to_en(s, d + 8.0)
        if z(e, n) < z(e2, n2) - FACE_DROP_M:
            if cur:
                runs.append(cur)
            cur = []
        else:
            cur.append((s, d))
    if cur:
        runs.append(cur)
    return [r for r in runs if len(r) >= 2 and r[-1][0] - r[0][0] >= MIN_RUN_M]


def clip_to_box(pts):
    """The polyline cut at the box's north and south edges, by interpolation."""
    out = []
    inside = lambda p: BOX_N[0] <= p[1] <= BOX_N[1]
    for a, b in zip(pts, pts[1:] + [None]):
        if inside(a):
            out.append([round(a[0], 2), round(a[1], 2)])
        if b is None:
            break
        if inside(a) != inside(b):
            edge_n = BOX_N[1] if max(a[1], b[1]) > BOX_N[1] else BOX_N[0]
            f = (edge_n - a[1]) / ((b[1] - a[1]) or 1e-9)
            out.append([round(a[0] + f * (b[0] - a[0]), 2), round(edge_n, 2)])
    return out


def build():
    spec = json.loads(SPEC.read_text(encoding="utf-8"))
    frame = Frame(shore_line())
    rows, readings = {}, {}
    for key, sp in SHEETS.items():
        rows[key] = read_sheet(key, sp, frame)
        readings[key] = {"rows_read": len(rows[key]), "centres": sum(len(r["centres"]) for r in rows[key])}
    st28 = stations(rows["sanborn_1911_v3_sheet_28"])
    # where both papers draw the yard, sheet 28 draws all of it and sheet 20 only what its
    # paper's east edge leaves, so sheet 20 is read only north of sheet 28's first bin
    st20 = stations(rows["sanborn_1911_v3_sheet_20"], s_to=st28[0]["s"] - BIN_M)
    readings["sanborn_1911_v3_sheet_20"]["bins"] = len(st20)
    readings["sanborn_1911_v3_sheet_28"]["bins"] = len(st28)
    tracks, cover = assemble(frame, st20, st28)
    for t in tracks:
        t["pts"] = densify(t["pts"])
    z = heightfield()
    crest = crest_line(frame, z)
    split = []
    for t in tracks:
        runs = off_the_face(frame, z, t["pts"])
        s_from, s_to = t["pts"][0][0], t["pts"][-1][0]
        for r in runs:
            segs = [dict(sg) for sg in t["segments"] if sg["to_s"] > r[0][0] and sg["from_s"] < r[-1][0]]
            if segs:
                segs[0]["from_s"] = max(segs[0]["from_s"], round(r[0][0], 1))
                segs[-1]["to_s"] = min(segs[-1]["to_s"], round(r[-1][0], 1))
            left = [[round(a, 1), round(b, 1)] for a, b in ((s_from, r[0][0]), (r[-1][0], s_to)) if b - a > 1]
            split.append({"pts": r, "segments": segs, "left_off_face_s": left})
    tracks = split
    tracks.sort(key=lambda t: (round(t["pts"][len(t["pts"]) // 2][1], 1)))
    out_tracks = []
    for i, t in enumerate(tracks):
        line = clip_to_box([frame.to_en(s, d) for s, d in t["pts"]])
        if len(line) < 2:
            continue
        i = len(out_tracks)
        drawn = t["segments"]
        traced = math.fsum(sg["to_s"] - sg["from_s"] for sg in drawn if sg["how"] == "traced")
        total = math.fsum(sg["to_s"] - sg["from_s"] for sg in drawn)
        out_tracks.append({
            "id": f"ic_track_{i + 1:02d}",
            "centreline_local_m": line,
            "length_m": round(math.fsum(math.dist(a, b) for a, b in zip(line, line[1:])), 1),
            "traced_fraction": round(traced / total, 3) if total else 0.0,
            "segments": [{k: (round(v, 2) if isinstance(v, float) else v) for k, v in sg.items()} for sg in t["segments"]],
            "left_off_embankment_face_s": t["left_off_face_s"],
            "geometry_tier": "inferred" if traced / max(total, 1e-9) > 0.5 else "reconstructed",
        })
    doc = {
        "_doc": ("GENERATED by tools/trace_ic_tracks_1904.py from Sanborn 1911 sheets 20 and 28 and the authored "
                 "spec data/railway/1904_spec.json; do not edit by hand. The Illinois Central / Michigan Central "
                 "tracks east of Prairie and Calumet Avenues for the 1904 scene (T-2478): every track's centreline "
                 "in local ENU metres, and which stretch of it a sheet draws (traced), which is joined across the "
                 "gap between the sheets, carried past a sheet's end, or closed on a neighbour as a ladder would. "
                 "Drawn by renderers/web/js/railway.js with the sections, ties, ballast and verges the spec states."),
        "scene": "1904",
        "target_date": "1904-07-01",
        "ticket": "T-2478",
        "generated_by": "tools/trace_ic_tracks_1904.py",
        "frame": "local ENU metres, data/datum.json",
        "shore_frame": "s along shore_1904_ic_edge from its north end, d west of it (L287)",
        "sources": ["sanborn_1911_chicago_v3_sheet_20", "sanborn_1911_chicago_v3_sheet_28"],
        "readings": readings,
        "coverage_s_m": {k: round(v, 2) if isinstance(v, float) else v for k, v in cover.items()},
        "tracks": out_tracks,
        "right_of_way": right_of_way(frame, tracks, spec, crest),
        "lake_edge": lake_edge(frame, z, crest, spec),
        **{k: v for k, v in spec.items() if not k.startswith("_")},
        "spec_from": "data/railway/1904_spec.json",
    }
    return doc


def in_poly(e, n, poly):
    hit = False
    for (xi, yi), (xj, yj) in zip(poly, poly[-1:] + poly[:-1]):
        if (yi > n) != (yj > n) and e < (xj - xi) * (n - yi) / (yj - yi) + xi:
            hit = not hit
    return hit


CREST_DROP_M = 0.12        # ground this far under the grade behind it is still the face
TOE_LAKEWARD_M = 1.5       # the stone runs on under the water this far past the waterline
EDGE_SMOOTH_M = 15.0       # crest and toe are averaged along the shore over this either way


def crest_line(frame, z):
    """Where the embankment's lakeward face meets the graded crest, and where it meets
    the water, as d at every STEP_M of s. The face is the heightfield's own (terrain_spec
    `ic_row_embankment`, 1 in 1.5 from the water to the grade): the crest is the first d,
    walking inland, at which the ground stands within CREST_DROP_M of the grade 12 m
    behind it; the waterline is the last d before that at which it is under the water.
    Both are smoothed along the shore so a 2.5 m heightfield cell does not jag them."""
    ss = np.arange(0.0, frame.s[-1] + STEP_M, STEP_M)
    crest, water = [], []
    ds = np.arange(-6.0, 30.0, 0.25)
    for s_ in ss:
        h = np.array([z(*frame.to_en(s_, d)) for d in ds])
        grade = float(np.median(h[(ds >= 12.0) & (ds <= 16.0)]))
        up = np.nonzero(h >= grade - CREST_DROP_M)[0]
        ic = int(up[0]) if len(up) else len(ds) - 1
        wet = np.nonzero(h[:ic] <= 0.0)[0]
        crest.append(float(ds[ic]))
        water.append(float(ds[wet[-1]]) if len(wet) else float(ds[0]))
    k = int(EDGE_SMOOTH_M / STEP_M)
    kern = np.ones(2 * k + 1) / (2 * k + 1)
    sm = lambda a: np.convolve(np.pad(np.array(a), k, mode="edge"), kern, mode="valid")
    return {"s": ss, "crest": sm(crest), "water": sm(water)}


def right_of_way(frame, tracks, spec, crest):
    """The cinder ground and the verges either side of it, as plan polygons.

    At every STEP_M along the shore frame the ground runs from the westernmost track
    present plus the spec's west margin to the easternmost less its east margin; the
    edge is the running extreme over ROW_REACH_M either way, then smoothed, so a short
    siding does not bite a notch in it. The west verge lies inland of the cinders; the
    east verge between them and the lake, never on the embankment's face: its outer edge
    keeps the made ground's least width inland of the crest, and where the tracks crowd
    the edge the verge narrows to make room (T-2479)."""
    b, v = spec["ballast"], spec["verges"]
    lo = min(t["pts"][0][0] for t in tracks)
    hi = max(t["pts"][-1][0] for t in tracks)
    ss = np.arange(math.floor(lo / STEP_M) * STEP_M, hi + STEP_M, STEP_M)
    west = np.full(len(ss), np.nan)
    east = np.full(len(ss), np.nan)
    for t in tracks:
        ts = np.array([p[0] for p in t["pts"]])
        td = np.array([p[1] for p in t["pts"]])
        inside = (ss >= ts[0]) & (ss <= ts[-1])
        d = np.interp(ss[inside], ts, td)
        west[inside] = np.fmax(west[inside], d)
        east[inside] = np.fmin(east[inside], d)
    have = ~np.isnan(west)
    ss, west, east = ss[have], west[have], east[have]
    k = int(ROW_REACH_M / STEP_M)
    w2 = np.array([west[max(0, i - k):i + k + 1].max() for i in range(len(ss))])
    e2 = np.array([east[max(0, i - k):i + k + 1].min() for i in range(len(ss))])
    kern = np.ones(2 * k + 1) / (2 * k + 1)
    sm = lambda a: np.convolve(np.pad(a, k, mode="edge"), kern, mode="valid")
    dw = sm(w2) + b["west_margin_m"]
    de = np.maximum(sm(e2) - b["east_margin_m"], EDGE_CLEAR_M + v["width_m"])
    # off the face: the verge's outer edge stays the made ground's width inland of the
    # crest, and the verge keeps at least a metre, giving the rest up where it must
    me = spec["edge"]["made_ground"]
    cr = np.interp(ss, crest["s"], crest["crest"])
    keep = cr + me["min_width_m"]
    de = np.maximum(de, np.minimum(keep + v["width_m"], e2 - b["bed_half_width_m"] - 0.25))
    de = np.maximum(de, keep + me["min_verge_m"])
    de_out = np.maximum(de - v["width_m"], keep)
    # the right-of-way's west line is the lots' rear line where the grid draws one
    # (sheet 20's ic_row): neither the cinders nor the verge cross into a block
    blocks = [b_["outline_local_m"] for b_ in json.loads(GRID.read_text(encoding="utf-8"))["blocks"]]
    outer = dw + v["width_m"]
    for i, s_ in enumerate(ss):
        while outer[i] > w2[i] + b["bed_half_width_m"] + 1.0 and any(
                in_poly(*frame.to_en(s_, outer[i]), poly) for poly in blocks):
            outer[i] -= 0.25
    outer = np.minimum(outer, sm(outer))  # no single-sample notch
    dw = np.minimum(dw, np.maximum(outer - 1.0, w2 + b["bed_half_width_m"]))

    def band(d_a, d_b):
        """A ribbon as stations across it, [e_a, n_a, e_b, n_b] every STEP_M, kept inside the box."""
        out = []
        for s_, da, db in zip(ss, d_a, d_b):
            (ea, na), (eb, nb) = frame.to_en(s_, da), frame.to_en(s_, db)
            if BOX_N[0] <= (na + nb) / 2 <= BOX_N[1]:
                out.append([round(ea, 2), round(na, 2), round(eb, 2), round(nb, 2)])
        return out

    return {
        "stations_doc": ("Each ribbon is a run of stations [e_west, n_west, e_east, n_east] across it, every 5 m "
                         "along it; `made_ground` is T-2479's strip between the east verge and the lake edge's crest."),
        "cinders": band(dw, de),
        "verges": [
            {"side": "west", "stations": band(outer, dw)},
            {"side": "east", "stations": band(de, de_out)},
        ],
        # the made ground (T-2479): from the cap at the crest to the verge, run on under
        # the verge's faded edge so no seam of the heightfield's grass shows between them
        "made_ground": band(de_out + me["under_verge_m"], cr),
        "tier": "reconstructed",
        "note": ("Where the cinders stop and the weeds begin is not drawn on either sheet: the "
                 "edges are the outermost tracks plus the spec's margins, smoothed. RECONSTRUCTED "
                 "(L-ic-tracks-2478)."),
    }


def lake_edge(frame, z, crest, spec):
    """The railway's edge against the lake (T-2479): the stone face from TOE_LAKEWARD_M
    under the water up to the crest, the cap timber along the crest, and the made ground
    from the crest inland to the east verge's outer edge, all as stations along the shore
    over the s the tracks' cinders cover. Heights are the heightfield's, read by the
    renderer; this file says where."""
    lo, hi = crest["s"][0], crest["s"][-1]
    ss = crest["s"]
    face, cap = [], []
    for s_, dc, dwt in zip(ss, crest["crest"], crest["water"]):
        (ea, na), (eb, nb) = frame.to_en(s_, dwt - TOE_LAKEWARD_M), frame.to_en(s_, dc + 0.15)
        (ec, nc) = frame.to_en(s_, dc)
        if BOX_N[0] <= nc <= BOX_N[1]:
            face.append([round(ea, 2), round(na, 2), round(eb, 2), round(nb, 2)])
            cap.append([round(ec, 2), round(nc, 2)])
    return {
        "stations_doc": ("`face` runs from the toe under the water to the crest, as stations [e_lake, n_lake, "
                         "e_land, n_land] every 5 m along the shore; `crest` is the cap timber's line. The made "
                         "ground between the crest and the east verge is right_of_way.made_ground."),
        "face": face,
        "crest": cap,
        "s_range_m": [round(float(lo), 1), round(float(hi), 1)],
        "crest_d_m": [round(float(crest["crest"].min()), 2), round(float(crest["crest"].max()), 2)],
        "waterline_d_m": [round(float(crest["water"].min()), 2), round(float(crest["water"].max()), 2)],
        "tier": "reconstructed",
        "note": ("The face, its crest and the waterline are the committed heightfield's (terrain_spec "
                 "ic_row_embankment); what the face is made of, the cap and the piles are not read off "
                 "any source. RECONSTRUCTED (L-ic-lake-edge-2479)."),
    }


def check_properties(doc) -> list[str]:
    bad = []
    if not doc.get("tracks"):
        bad.append("no tracks")
    for t in doc.get("tracks", []):
        line = t["centreline_local_m"]
        if len(line) < 2:
            bad.append(f"{t['id']}: fewer than two vertices")
        for e, n in line:
            if not (1100 <= e <= 1800 and BOX_N[0] - 1 <= n <= BOX_N[1] + 1):
                bad.append(f"{t['id']}: vertex {e},{n} outside the e1871 box")
                break
        hows = {s["how"] for s in t["segments"]}
        if not hows <= {"traced", "joined_across_gap", "carried_past_sheet", "closes_on_neighbour"}:
            bad.append(f"{t['id']}: unknown segment kind {hows}")
        if t["geometry_tier"] not in ("inferred", "reconstructed"):
            bad.append(f"{t['id']}: tier {t['geometry_tier']}")
    row = doc.get("right_of_way") or {}
    if len(row.get("cinders") or []) < 2:
        bad.append("right_of_way: no cinder ground")
    if len(row.get("verges") or []) != 2 or any(len(v.get("stations") or []) < 2 for v in row.get("verges") or []):
        bad.append("right_of_way: expected a west and an east verge")
    if len(row.get("made_ground") or []) < 2:
        bad.append("right_of_way: no made ground")
    edge = doc.get("lake_edge") or {}
    if len(edge.get("face") or []) < 2 or len(edge.get("crest") or []) < 2:
        bad.append("lake_edge: no face or no crest")
    for k in ("gauge_m", "rail", "ties", "ballast", "verges", "edge", "liberty"):
        if k not in doc:
            bad.append(f"spec block `{k}` missing")
    return bad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--check-properties", action="store_true")
    a = ap.parse_args()
    if a.check_properties:
        doc = json.loads(OUT.read_text(encoding="utf-8"))
        bad = check_properties(doc)
        for b in bad:
            print("FAIL railway 1904:", b)
        print(f"railway 1904: {len(doc['tracks'])} tracks, {'OK' if not bad else 'FAIL'}")
        sys.exit(1 if bad else 0)
    if a.check:
        try:
            import numpy  # noqa: F401
            from PIL import Image  # noqa: F401
        except ImportError:
            print("WARN Pillow/numpy absent: the sheets were not re-read; holding the committed file together only")
            doc = json.loads(OUT.read_text(encoding="utf-8"))
            bad = check_properties(doc)
            for b in bad:
                print("FAIL railway 1904:", b)
            sys.exit(1 if bad else 0)
    doc = build()
    text = json.dumps(doc, indent=1, ensure_ascii=False) + "\n"
    if a.check:
        old = OUT.read_text(encoding="utf-8") if OUT.exists() else ""
        if old != text:
            print("FAIL: data/railway/1904.json is stale -- run tools/trace_ic_tracks_1904.py")
            sys.exit(1)
        bad = check_properties(doc)
        for b in bad:
            print("FAIL railway 1904:", b)
        if bad:
            sys.exit(1)
        print(f"railway 1904: re-traced, {len(doc['tracks'])} tracks, matches the committed file")
        return
    bad = check_properties(doc)
    if bad:
        for b in bad:
            print("FAIL:", b)
        sys.exit(1)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text, encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}: {len(doc['tracks'])} tracks; readings {doc['readings']}")


if __name__ == "__main__":
    main()
