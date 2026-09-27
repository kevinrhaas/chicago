#!/usr/bin/env python3
"""What the two 1834 surveys draw on the South Division bank between the bend and
the La Salle slough — the reading T-1630 asks for before anything is moved.

    tools/read_south_bank_swell_1834.py --build    re-read both sheets, write the record
    tools/read_south_bank_swell_1834.py --check    the gate: offline, re-derives every number
    tools/read_south_bank_swell_1834.py --report   print the reading
    tools/read_south_bank_swell_1834.py --self-test  the gate's assertions still fire when broken

THE QUESTION. The owner flew the 1835 scene along South Water Street and reported that
the south bank bulges some 20 m into the main stem between the bend at the forks and the
La Salle slough mouth, where Hathaway draws it even; he ruled that Wright's inked bank is
the target and that a correction going PAST that ink is as wrong as the swell. So the
ticket's first step is not a repair, it is a measurement: does the committed waterline
stand north of the ink Wright drew, or is the swell Wright's own?

WHY THIS CAN BE ASKED AT ALL, GIVEN THE MASTER SCAN IS UNREADABLE. `river.geojson` was
traced off the Boston Public Library master by `tools/trace_river.py`, and that region can
no longer be re-fetched: BPL re-encoded it, the pin in `data/traces/pinned_sources.json`
refuses the new bytes, and the tool declines to re-trace rather than read bytes it was not
made from (T-1397). This reading therefore goes to the OTHER sheet — the 600 dpi National
Archives / Historic Urban Plans facsimile (`wright_1834_nara_hup`), held in the working
copy, under its own eleven-point affine (RMS 16.02 m) — which is the stronger test anyway:
a committed line traced off one scan under one registration, checked against the same
draughtsman's ink on a different scan under a different registration, agrees for reasons
that have nothing to do with either fit.

AND WHY THE SECOND HALF IS MEASURED ON EACH SHEET SEPARATELY. The two 1834 sheets disagree
about the forks by 58 m, and the fits carry 16.0 m and 17.7 m of RMS, so "how far north is
the bank" cannot be compared BETWEEN sheets: the answer would be the registration's. What
can be compared is a distance measured inside one sheet — the width of ground the
draughtsman drew between his own bank and his own block tier, block by block. That number
is free of both fits and of the paper's stretch, and it is the one this file uses to say
whether Wright drew a swell and whether Hathaway did not.

Needs Pillow and numpy for `--build` only. `--check` opens no raster and touches no socket:
it re-derives every figure from the pixel stations this file commits and from the committed
waterline, which is what lets `tools/check.sh` ask it on every change.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data/traces/south_bank_swell_1834.json"
DATUM = ROOT / "data/datum.json"
WRIGHT_GCP = ROOT / "data/traces/gcp/wright_1834_nara_hup_gcps.json"
HATHAWAY_GCP = ROOT / "data/traces/gcp/hathaway_1834_gcps.json"
RIVER = ROOT / "data/terrain/epochs/e1834_harbor_cut/river.geojson"
SHORELINE = ROOT / "data/terrain/epochs/e1834_harbor_cut/shoreline.geojson"

WRIGHT_RASTER = ROOT.parent / "pre_fire_v1/maps/images/1834-wright-map.jpg"
HATHAWAY_RASTER = ROOT.parent / "pre_fire_v1/maps/images/1834_hathaway_map.jpg"

# --- the trace, stated so it can be re-run -------------------------------------------
# Seeds are hand-placed on each sheet, like every other seed in this project's tracers,
# and they are the only hand-placed numbers here. Wright's bank is followed in TWO runs
# because the La Salle re-entrant is a cusp: a follower that steps east cannot turn 90
# degrees into it, so the run stops on its west lip and is picked up on its east one.
WRIGHT_RUNS = [
    {"id": "west_of_slough", "seed_px": [1950.0, 2496.0], "to_px": 2438.0},
    {"id": "east_of_slough", "seed_px": [2460.0, 2455.0], "to_px": 2748.0},
]
HATHAWAY_RUNS = [
    {"id": "the_reach", "seed_px": [700.0, 831.7], "to_px": 1140.0},
]
STEP_PX = 2.0
HALF_PX = 7.0                 # search half-width about the predicted row
SMOOTH = 0.6                  # heading smoothing
DARK_BAND = 25                # a pixel within this of the window's darkest is "the stroke"
HATHAWAY_UPSCALE = 3          # the working copy is 1672 px wide; the fit's raster is 4000
HATHAWAY_HALF_PX = 12.0       # ...so the search half-width is in UPSCALED pixels
SAMPLE_EVERY_PX = 8           # the run is reported every 8 px of easting

# The platted tier fronting South Water Street, block by block, as a window of sheet
# columns on each sheet. Hand-placed on the drawing, read off the block numerals.
WRIGHT_BLOCKS = {"20": [2100, 2235], "19": [2280, 2400], "18": [2445, 2570], "17": [2610, 2740]}
HATHAWAY_BLOCKS = {"20": [742, 807], "19": [822, 883], "18": [900, 963], "17": [980, 1042]}
FRONT_SEARCH_PX = [20, 72]    # rows below the bank the block's north line is looked for in

# The committed waterline is two files: the forks trace to local E +314 and the harbour
# trace from there east. Both are Wright, both are the BPL master, and the join is the
# one `shoreline.geojson` states in its own note.
JOIN_E = 314.0

# --- T-1630's RECUT: the deliberate departure from Wright's ink -----------------------
# The owner answered this reading's question with option (b) on 2026-09-26: bring the bank
# in to HATHAWAY's taper on this reach, "at least 50% of what is north of south water
# street", and — on seeing the per-block table below — "i think it is closer to the
# hathaway map in that reading". So the bank no longer stands on Wright's ink between the
# bend near the forks and the La Salle mouth, ON PURPOSE, and this file's job changes from
# asserting that it does to RECORDING what was moved and re-deriving it.
#
# The amount is NOT a fraction of Wright and NOT the owner's drawn line. It is the two
# sheets' own disagreement, `wright_minus_hathaway_m` below, measured inside each sheet so
# no registration enters it: 5.6 m at block 20, 10.8 m at block 19. Halving Wright's 39.0 m
# at block 19 would have cut past Hathaway, which is the overcorrection his third message
# forbade. The shift is piecewise linear in local easting, zero at the bend and zero again
# at the La Salle mouth's east lip, so Wright's re-entrant stays the one break in the run
# and nothing outside the reach moves at all.
# The west end is the committed bend vertex at local E +228.91, not the turn's foot at
# E +167.59, and that is a measurement rather than a preference. West of E +222 the traced
# bank already stands SOUTH of South Water Street's own platted corridor edge — the river
# crosses the street at the forks, which is why the plat omits block 21 — so a shift that
# started at the foot of the turn put another 32 m of roadway under water for no reading.
# Clearance over the corridor edge is non-decreasing everywhere as a result.
RECUT_SHIFT_ANCHORS = [(228.91, 0.0), (268.00, 5.6), (390.00, 10.8),
                       (455.81, 10.8), (467.17, 0.0)]
# Block 18 is NOT shifted, and that is a measured refusal rather than an omission. The
# ruling's table asks 7.5 m of it, but east of the slough the committed bank stands only
# 5.4 m north of South Water Street's own platted corridor edge, so 7.5 m would put the
# river 2.1 m into the roadway. The owner's own words bound the reach — "from the bend in
# the west to the La Salle mouth", "east of the slough it already follows the bank" — and
# they are followed. The figure is kept here so the refusal has a number on it.
RECUT_BLOCK_18_REFUSED_M = 7.5
RECUT_VERTEX_TOL_M = 0.02      # the geojson keeps two decimals
REACH_E = [160.0, 690.0]
SAMPLE_ALONG_M = 5.0       # the committed line is measured every 5 m of its own run, not at vertices
# The re-entrant at the La Salle mouth is where the ink follower stops and restarts, so
# committed vertices inside it have no ink to be measured against on this reading and are
# reported as a count rather than silently matched to the nearest lip.
SLOUGH_MOUTH_E = [452.0, 484.0]


# --- committed geometry ---------------------------------------------------------------

def _datum():
    d = json.loads(DATUM.read_text())
    return d["origin_utm_e"], d["origin_utm_n"]


def committed_bank():
    """The committed south bank of the main stem, west to east, in local ENU metres."""
    oe, on = _datum()
    pts = []
    for f in json.loads(RIVER.read_text())["features"]:
        if str(f["properties"].get("name", "")).startswith("South Division"):
            pts += [(x - oe, y - on) for x, y in f["geometry"]["coordinates"] if (x - oe) <= JOIN_E]
    pts.sort(key=lambda p: p[0])
    east = []
    for f in json.loads(SHORELINE.read_text())["features"]:
        p = f["properties"]
        if p.get("kind") == "shore" and str(p["name"]).startswith("South shore"):
            east = [(x - oe, y - on) for x, y in f["geometry"]["coordinates"] if (x - oe) >= JOIN_E]
    east.sort(key=lambda p: p[0])
    return pts + east


def recut_shift(e):
    """Metres the bank was moved SOUTH at local easting `e`, piecewise linear."""
    a = RECUT_SHIFT_ANCHORS
    if e <= a[0][0] or e >= a[-1][0]:
        return 0.0
    for (e0, s0), (e1, s1) in zip(a, a[1:]):
        if e0 <= e <= e1:
            return s0 + (s1 - s0) * (e - e0) / (e1 - e0)
    return 0.0


def _recut_vertices(rec):
    """The reach's vertices as Wright's trace drew them, off the record's set-aside."""
    return [(float(e), float(n)) for e, n in rec["recut"]["wright_bank_as_traced"]]


def as_traced_bank(rec):
    """The committed bank with the recut reach put back the way the trace drew it, which
    is what the ink comparison below has to be measured against: the reading is about the
    TRACE, and the recut is a ruling laid over it, not a correction to it."""
    aside = {round(e, 2): n for e, n in _recut_vertices(rec)}
    out = []
    for e, n in committed_bank():
        k = round(e, 2)
        out.append((e, aside[k]) if k in aside else (e, n))
    return out


def recut_stations():
    """Every vertex of the recut reach as the two committed files hold it, by easting.

    Read off the GeoJSON rather than off `committed_bank()`: that function splices the two
    windows at JOIN_E and drops the forks run's easternmost vertex, which is one of the
    nine the rule moves. A vertex the gate cannot see is a vertex a hand edit can move.
    """
    oe, on = _datum()
    lo, hi = RECUT_SHIFT_ANCHORS[0][0], RECUT_SHIFT_ANCHORS[-1][0]
    out = {}
    for path in (RIVER, SHORELINE):
        for f in json.loads(path.read_text())["features"]:
            g = f["geometry"]
            rings = ([g["coordinates"]] if g["type"] == "LineString"
                     else g["coordinates"] if g["type"] == "Polygon" else [])
            for ring in rings:
                for c in ring:
                    e, n = round(c[0] - oe, 2), round(c[1] - on, 2)
                    if lo <= e <= hi and recut_shift(e) > 0.0 and 12.0 <= n <= 80.0:
                        out.setdefault(e, []).append(n)
    return out


def recut_check(rec):
    """Is the committed bank exactly the recut of the set-aside bank? Returns the worst
    vertex error in metres, and the count of stations the rule moved."""
    aside = {round(e, 2): n for e, n in _recut_vertices(rec)}
    got = recut_stations()
    worst, moved = 0.0, 0
    # A station the record sets aside but the files no longer carry, or the other way
    # round, is a full-scale error rather than a near miss: neither list may go quiet.
    for e in set(aside) | set(got):
        if e not in aside or e not in got:
            return 999.0, len(got)
        want = aside[e] - recut_shift(e)
        for n in got[e]:
            worst = max(worst, abs(want - n))
        moved += 1
    return round(worst, 3), moved


def resample(line, step):
    """Stations every `step` metres along a polyline, so the statistic below is a
    statistic of the LINE and not of wherever Douglas-Peucker happened to keep a vertex."""
    out = []
    carry = 0.0
    for a, b in zip(line, line[1:]):
        seg = math.hypot(b[0] - a[0], b[1] - a[1])
        t = carry
        while t < seg:
            out.append((a[0] + (b[0] - a[0]) * t / seg, a[1] + (b[1] - a[1]) * t / seg))
            t += step
        carry = t - seg
    out.append(line[-1])
    return out


def _seg_distance(p, a, b):
    ax, ay = a
    bx, by = b
    vx, vy = bx - ax, by - ay
    L2 = vx * vx + vy * vy
    if L2 <= 0:
        return math.hypot(p[0] - ax, p[1] - ay)
    t = max(0.0, min(1.0, ((p[0] - ax) * vx + (p[1] - ay) * vy) / L2))
    return math.hypot(p[0] - (ax + t * vx), p[1] - (ay + t * vy))


def ink_distance(point, runs):
    """Shortest distance from a point to any of the traced ink polylines."""
    best = None
    for run in runs:
        line = run["local_enu_m"]
        for a, b in zip(line, line[1:]):
            d = _seg_distance(point, a, b)
            if best is None or d < best:
                best = d
    return best


def _pct(values, q):
    if not values:
        return None
    s = sorted(values)
    i = (len(s) - 1) * q
    lo, hi = int(math.floor(i)), int(math.ceil(i))
    return s[lo] if lo == hi else s[lo] + (s[hi] - s[lo]) * (i - lo)


# --- what --check re-derives, offline ---------------------------------------------------

def derive(rec):
    """Every measured figure in the record, recomputed from the record's own pixel
    stations and from the committed waterline. No raster, no network, no numpy."""
    out = {}
    runs = rec["wright_1834_nara_hup"]["runs"]
    # Measured against the bank as the TRACE drew it. Since T-1630's ruling the committed
    # bank is that line moved south on this reach, so measuring the committed geometry here
    # would report the ruling and lose the reading.
    dens = [p for p in resample(as_traced_bank(rec), SAMPLE_ALONG_M)
            if REACH_E[0] <= p[0] <= REACH_E[1]]
    inside = [p for p in dens if SLOUGH_MOUTH_E[0] <= p[0] <= SLOUGH_MOUTH_E[1]]
    measured = [p for p in dens if not (SLOUGH_MOUTH_E[0] <= p[0] <= SLOUGH_MOUTH_E[1])]
    ds = [ink_distance(p, runs) for p in measured]
    out["committed_against_wright_ink"] = {
        "stations": len(ds),
        "sampled_every_m": SAMPLE_ALONG_M,
        "in_the_slough_mouth_not_measured": len(inside),
        "median_m": round(_pct(ds, 0.5), 2),
        "p90_m": round(_pct(ds, 0.9), 2),
        "max_m": round(max(ds), 2),
    }
    widths = {}
    for sheet in ("wright_1834_nara_hup", "hathaway_1834"):
        widths[sheet] = {k: round(v["bank_local_n_m"] - v["front_local_n_m"], 1)
                         for k, v in rec[sheet]["south_water_ground"].items()}
    out["south_water_ground_m"] = widths
    w, h = widths["wright_1834_nara_hup"], widths["hathaway_1834"]
    diff = {k: round(w[k] - h[k], 1) for k in sorted(w) if k in h}
    out["wright_minus_hathaway_m"] = diff
    out["swell_amplitude_m"] = round(max(diff.values()) - min(diff.values()), 1)
    worst, moved = recut_check(rec)
    out["recut"] = {
        "vertices_moved": moved,
        "worst_vertex_error_m": worst,
        "shift_m_at_block_20": round(recut_shift(268.0), 1),
        "shift_m_at_block_19": round(recut_shift(390.0), 1),
        "shift_m_at_block_18": round(recut_shift(512.0), 1),
        "shift_m_at_block_17": round(recut_shift(636.0), 1),
        "step_across_the_la_salle_mouth_m": _mouth_step(),
        "straightness_p90_m": _straightness(),
    }
    return out


def _bank_at(line, e):
    for a, b in zip(line, line[1:]):
        if a[0] <= e <= b[0] and b[0] > a[0]:
            return a[1] + (b[1] - a[1]) * (e - a[0]) / (b[0] - a[0])
    return None


def _mouth_step():
    """How far the bank jumps across the La Salle re-entrant — the owner's own test that
    the reach west of the slough reads "even with the bank to the east"."""
    bank = committed_bank()
    return round(abs(_bank_at(bank, 455.0) - _bank_at(bank, 498.0)), 2)


def _straightness():
    """p90 departure, in metres, of the bank from a straight least-squares fit through the
    reach the ruling names — the acceptance clause's number, on the committed geometry."""
    pts = [p for p in resample(committed_bank(), SAMPLE_ALONG_M)
           if 220.0 <= p[0] <= 456.0]
    n = len(pts)
    mx = sum(p[0] for p in pts) / n
    my = sum(p[1] for p in pts) / n
    sxx = sum((p[0] - mx) ** 2 for p in pts)
    sxy = sum((p[0] - mx) * (p[1] - my) for p in pts)
    m = sxy / sxx
    res = sorted(abs(p[1] - (my + m * (p[0] - mx))) for p in pts)
    return round(_pct(res, 0.9), 2)


VERDICT_KEYS = ("committed_against_wright_ink", "south_water_ground_m",
                "wright_minus_hathaway_m", "swell_amplitude_m", "recut")


def check(rec=None, quiet=False, tag=""):
    rec = rec if rec is not None else json.loads(OUT.read_text())
    got = derive(rec)
    bad = []
    for k in VERDICT_KEYS:
        if rec["measured"][k] != got[k]:
            bad.append(f"  {k}\n    committed {rec['measured'][k]}\n    re-derived {got[k]}")
    # The reading's own verdict is gated too: if a later edit moved the committed bank,
    # the prose would still read correctly and only this would notice.
    stat = got["committed_against_wright_ink"]
    if stat["median_m"] > 5.0 or stat["p90_m"] > 12.0:
        bad.append("  the set-aside bank no longer stands on Wright's ink: "
                   f"median {stat['median_m']} m, p90 {stat['p90_m']} m "
                   "(this reading's verdict says it does)")
    # ...and the OTHER half of the verdict since T-1630's ruling: the committed bank is
    # that set-aside line moved south by the stated rule, and by nothing else. A hand edit
    # anywhere in the reach, or a shift that crept outside it, lands here.
    if got["recut"]["worst_vertex_error_m"] > RECUT_VERTEX_TOL_M:
        bad.append("  the committed bank is not the recut of the set-aside bank: worst "
                   f"vertex error {got['recut']['worst_vertex_error_m']} m > "
                   f"{RECUT_VERTEX_TOL_M} m")
    if got["recut"]["step_across_the_la_salle_mouth_m"] > 4.0:
        bad.append("  the bank still steps across the La Salle mouth by "
                   f"{got['recut']['step_across_the_la_salle_mouth_m']} m; the ruling's "
                   "acceptance is that the reach west of it reads level with the bank east")
    if bad:
        # Every line of a self-test's transcript is tagged, so a green run's deliberate
        # failures cannot be mistaken for the real thing (AGENTS.md rule 9).
        print(f"{tag}FAIL read_south_bank_swell_1834 --check")
        for line in "\n".join(bad).split("\n"):
            print(f"{tag}{line}")
        return 1
    if not quiet:
        print("south bank swell reading re-derives: "
              f"median {stat['median_m']} m / p90 {stat['p90_m']} m against Wright's ink, "
              f"swell {got['swell_amplitude_m']} m wider than Hathaway")
    return 0


def self_test():
    """Break each gated figure and prove the check fails on it."""
    base = json.loads(OUT.read_text())
    fails = 0
    for mutate, what in (
        (lambda r: r["measured"].__setitem__("swell_amplitude_m", 0.0), "the swell amplitude"),
        (lambda r: r["measured"]["committed_against_wright_ink"].__setitem__("median_m", 0.0),
         "the median ink distance"),
        (lambda r: r["wright_1834_nara_hup"]["south_water_ground"]["19"]
         .__setitem__("bank_local_n_m", 0.0), "a block's bank northing"),
        (lambda r: r["recut"]["wright_bank_as_traced"][0].__setitem__(1, 0.0),
         "a set-aside vertex, so the recut no longer re-derives"),
        (lambda r: r["recut"]["wright_bank_as_traced"].pop(0),
         "a set-aside station, so one the files carry is unaccounted for"),
        (lambda r: r["measured"]["recut"].__setitem__("vertices_moved", 0),
         "the count of vertices the recut moved"),
    ):
        r = json.loads(json.dumps(base))
        mutate(r)
        print(f"   self-test | breaking {what} must fail the check")
        if check(r, quiet=True, tag="   self-test | ") == 0:
            print(f"   self-test | FAIL: breaking {what} did not fail the check")
            fails += 1
        else:
            print(f"   self-test | ...it failed, as it must")
    print("read_south_bank_swell_1834 self-test: "
          + ("ok" if fails == 0 else f"{fails} assertion(s) did not fire"))
    return 1 if fails else 0


# --- the build half: the two rasters ------------------------------------------------------

def _fit(path):
    c = json.loads(Path(path).read_text())["fit"]["coefficients"]
    oe, on = _datum()
    return lambda px, py: (c["a"] * px + c["b"] * py + c["c"] - oe,
                           c["d"] * px + c["e"] * py + c["f"] - on)


def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _follow(A, seed, to_px, half):
    """Walk east along a drawn stroke, taking the darkness-weighted centroid of the
    darkest band in a window about the predicted row. Returns {column: row}."""
    import numpy as np
    x, y = float(seed[0]), float(seed[1])
    dy = 0.0
    out = {int(round(x)): y}
    while x < to_px:
        x += STEP_PX
        yp = y + dy * STEP_PX
        lo, hi = int(yp - half), int(yp + half)
        ys = np.arange(lo, hi + 1)
        vals = A[lo:hi + 1, int(round(x))]
        m = vals < vals.min() + DARK_BAND
        w = 255.0 - vals[m]
        if w.sum() <= 0:
            raise SystemExit(f"the stroke is lost at column {x:.0f}: no ink in the window")
        yn = float((ys[m] * w).sum() / w.sum())
        dy = SMOOTH * dy + (1 - SMOOTH) * ((yn - y) / STEP_PX)
        y = yn
        out[int(round(x))] = y
    return out


def _front_row(A, x0, x1, bank_y):
    """The platted tier's north line inside one block: the darkest ROW of the block's
    own columns, which a letter cannot win because a letter is local in x."""
    import numpy as np
    lo, hi = int(bank_y + FRONT_SEARCH_PX[0]), int(bank_y + FRONT_SEARCH_PX[1])
    rows = (255.0 - A[lo:hi, x0:x1]).mean(axis=1)
    return lo + int(np.argmax(rows))


def _read_sheet(raster, gcp, runs_spec, blocks, upscale, half):
    from PIL import Image
    import numpy as np
    Image.MAX_IMAGE_PIXELS = None
    im = Image.open(raster).convert("L")
    native = list(im.size)
    if upscale != 1:
        im = im.resize((im.width * upscale, im.height * upscale), Image.LANCZOS)
    A = np.asarray(im, dtype=float)
    loc = _fit(gcp)
    S = upscale
    rows = {}
    runs = []
    for spec in runs_spec:
        seed = [spec["seed_px"][0] * S, spec["seed_px"][1] * S]
        d = _follow(A, seed, spec["to_px"] * S, half)
        rows.update(d)
        px = [[round(x / S, 1), round(y / S, 1)] for x, y in sorted(d.items())
              if int(x) % (SAMPLE_EVERY_PX * S) == 0]
        runs.append({"id": spec["id"], "px": px,
                     "local_enu_m": [[round(v, 2) for v in loc(p[0] * S / S, p[1] * S / S)]
                                     if S == 1 else
                                     [round(v, 2) for v in loc(p[0] * (4000 / native[0]),
                                                               p[1] * (4000 / native[0]))]
                                     for p in px]})

    def bank_at(x):
        for o in range(0, 4):
            for s in (o, -o):
                if int(x * S) + s in rows:
                    return rows[int(x * S) + s]
        raise SystemExit(f"no bank station near column {x}")

    ground = {}
    for k, (x0, x1) in blocks.items():
        xc = (x0 + x1) // 2
        by = bank_at(xc)
        fy = _front_row(A, int(x0 * S), int(x1 * S), by)
        if S == 1:
            bn = loc(xc, by / S)[1]
            fn = loc(xc, fy / S)[1]
        else:
            k2 = 4000 / native[0]
            bn = loc(xc * k2, by / S * k2)[1]
            fn = loc(xc * k2, fy / S * k2)[1]
        ground[k] = {"columns_px": [x0, x1], "bank_px_y": round(by / S, 1),
                     "front_px_y": round(fy / S, 1),
                     "bank_local_n_m": round(bn, 1), "front_local_n_m": round(fn, 1)}
    return {"raster": {"working_copy": str(raster.relative_to(ROOT.parent.parent)),
                       "width": native[0], "height": native[1], "sha256": _sha256(raster)},
            "runs": runs, "south_water_ground": ground}


def build():
    wright = _read_sheet(WRIGHT_RASTER, WRIGHT_GCP, WRIGHT_RUNS, WRIGHT_BLOCKS, 1, HALF_PX)
    hath = _read_sheet(HATHAWAY_RASTER, HATHAWAY_GCP, HATHAWAY_RUNS, HATHAWAY_BLOCKS,
                       HATHAWAY_UPSCALE, HATHAWAY_HALF_PX)
    rec = {
        "_doc": __doc__.split("\n\n")[0].strip(),
        "ticket": "T-1630 step 1 (the owner's report of 2026-09-26)",
        "not_a_reading": "This re-reads ground the project has already read. `river.geojson` "
                         "and `shoreline.geojson` are Wright's bank traced off the BPL master; "
                         "this file traces the same ink on the NA/HUP facsimile and on Hathaway "
                         "to say whether the committed line stands on it. It asserts no new "
                         "feature, moves nothing and adjudicates no source unit.",
        "read_on": "2026-09-26",
        "registrations": {
            "wright_1834_nara_hup": "data/traces/gcp/wright_1834_nara_hup_gcps.json, `fit` "
                                    "(NA pixel -> EPSG:26916, eleven points, RMS 16.02 m)",
            "hathaway_1834": "data/traces/gcp/hathaway_1834_gcps.json, `fit` "
                             "(working-raster pixel -> EPSG:26916, RMS 17.7 m)",
        },
        "method": {
            "tracer": "darkness-weighted centroid of the darkest band in a window about the "
                      "predicted row, stepping east, heading smoothed",
            "step_px": STEP_PX, "search_half_width_px": HALF_PX,
            "heading_smoothing": SMOOTH, "dark_band": DARK_BAND,
            "sample_every_px": SAMPLE_EVERY_PX,
            "hathaway_upscale": HATHAWAY_UPSCALE,
            "block_front": "the darkest ROW of a block's own columns between 20 and 72 px "
                           "below the bank — a letter is local in x and cannot win a row mean",
            "why_two_runs_on_wright": "the La Salle re-entrant is a cusp; a follower stepping "
                                      "east cannot turn into it, so the run stops on its west "
                                      "lip and restarts on its east one",
        },
        "wright_1834_nara_hup": wright,
        "hathaway_1834": hath,
        "confidence": "attested",
        "confidence_note": "Every number is a measurement of a stated raster by a stated tracer "
                           "with committed parameters, re-derivable offline from the stations "
                           "below. What it is documented ABOUT is the sheets: where these two "
                           "draughtsmen put their ink. Which of them is right about the 1835 "
                           "river is not asserted here and is not this reading's to assert.",
    }
    rec["measured"] = derive(rec)
    rec["findings"] = findings(rec)
    OUT.write_text(json.dumps(rec, indent=1) + "\n")
    print(f"wrote {OUT.relative_to(ROOT)}")
    return 0


def findings(rec):
    m = rec["measured"]
    s = m["committed_against_wright_ink"]
    w = m["south_water_ground_m"]["wright_1834_nara_hup"]
    h = m["south_water_ground_m"]["hathaway_1834"]
    d = m["wright_minus_hathaway_m"]
    hot = max(d, key=lambda k: d[k])
    return [
        f"THE TRACED BANK IS WRIGHT'S INK. Over {s['stations']} traced stations between "
        f"local E +{REACH_E[0]:.0f} and E +{REACH_E[1]:.0f}, the waterline stands a median "
        f"{s['median_m']} m from the bank Wright inked, p90 {s['p90_m']} m, worst "
        f"{s['max_m']} m — against a trace whose own stated vertex uncertainty is +/-20 m and "
        "two registrations carrying 17.5 m and 16.0 m of RMS. The swell is not a tracing "
        "artefact, and it is not lettering read as ground: it is what Wright drew.",
        "WRIGHT DRAWS THE SWELL. Measured inside his own sheet, so no registration enters it, "
        "the ground he draws between his bank and his block tier's north line runs "
        + ", ".join(f"{v} m at block {k}" for k, v in sorted(w.items(), reverse=True)) + ".",
        "HATHAWAY DOES NOT. The same measurement on his sheet runs "
        + ", ".join(f"{v} m at block {k}" for k, v in sorted(h.items(), reverse=True))
        + " — a monotone narrowing eastward with no local maximum in it. The owner is right "
          "that Hathaway draws this reach even.",
        f"THE TWO SHEETS DISAGREE BY {m['swell_amplitude_m']} m ACROSS THE REACH. Wright is "
        + ", ".join(f"{v} m wider at block {k}" for k, v in sorted(d.items(), reverse=True))
        + f", so the departure peaks at block {hot} and has died out by the east end. The "
          "reported bulge is that disagreement, and it is about half the 20 m read off the "
          "scene, where the eye is also carrying the block grid's own 8.58 m corridor-line "
          "offset (docs/CORRIDOR-LINES.md).",
        "SO THE TICKET'S FIRST HYPOTHESIS IS REFUTED. There is nothing to re-trace and nothing "
        "to correct on the trace's own terms: bringing the bank in moves it OFF the ink of "
        "the sheet the datum, the plat and the block grid are all fitted to. That is a "
        "ruling, not a measurement, and it was asked rather than taken.",
    ] + ([] if "recut" not in rec else [
        "AND THE OWNER RULED FOR HATHAWAY ON THIS REACH (option b). The committed bank is now "
        f"Wright's traced line moved SOUTH by {m['recut']['shift_m_at_block_20']} m at block "
        f"20 and {m['recut']['shift_m_at_block_19']} m at block 19 — the two sheets' own "
        "disagreement, measured inside each sheet, not a fraction of Wright and not a drawn "
        f"line — over {m['recut']['vertices_moved']} bank stations between the bend near the "
        "forks and the La Salle mouth. Zero at both ends, so Wright's re-entrant stays the "
        "one break in the run and nothing outside the reach moves.",
        "THE SWELL IS GONE, AND THESE ARE THE NUMBERS. The bank's step across the La Salle "
        f"mouth falls to {m['recut']['step_across_the_la_salle_mouth_m']} m, which is the "
        "owner's own test that the reach west of the slough reads level with the bank east of "
        f"it; its p90 departure from a straight fit over local E +220..+456 is "
        f"{m['recut']['straightness_p90_m']} m, so the outer plank walk that follows it runs "
        "roughly straight. Block 18 is NOT moved and that is a refusal with a number on it: "
        f"the ruling asks {rec['recut']['block_18_refused_m']} m of it and the committed bank "
        "there stands only 5.4 m north of South Water Street's own platted corridor edge.",
        "THE BANK ON THIS REACH IS RECONSTRUCTED, NOT DOCUMENTED. Wright's ink is kept above, "
        "vertex for vertex, as the set-aside reading, and every figure in this record is still "
        "measured against it — the reading is about the trace, and the ruling is laid over it.",
    ])


# --- the recut half: move the committed bank, once, and record what was moved ---------

RECUT_RULING = (
    "Owner answer of 2026-09-26, option (b) of this reading's own question: \"ok yes st "
    "till want to bring that bulge in some, so the sidewalk is fairly straight and "
    "following, at least 50% of what is north of south water street i think\", and on "
    "seeing the per-block table, \"i think it is closer to the hathaway map in that "
    "reading\". The bank on this reach follows HATHAWAY 1834; Wright's ink is the "
    "set-aside reading and is kept below, vertex for vertex."
)


def recut(dry=False):
    """Move the committed bank south by the ruling's amount and record the set-aside.

    Runs ONCE. The record's `recut.wright_bank_as_traced` is the trace's own line, so a
    second run would shift an already-shifted bank; the tool refuses rather than letting
    that happen, and `--check` re-derives the whole thing from the set-aside afterwards.
    """
    rec = json.loads(OUT.read_text())
    if "recut" in rec:
        print("the recut is already recorded; --check re-derives it. Nothing to do.")
        return 0
    oe, on = _datum()
    lo, hi = RECUT_SHIFT_ANCHORS[0][0], RECUT_SHIFT_ANCHORS[-1][0]
    aside, moved = {}, 0
    for path in (RIVER, SHORELINE):
        doc = json.loads(path.read_text())
        for f in doc["features"]:
            g = f["geometry"]
            rings = ([g["coordinates"]] if g["type"] == "LineString"
                     else g["coordinates"] if g["type"] == "Polygon" else [])
            for ring in rings:
                for c in ring:
                    e, n = round(c[0] - oe, 2), round(c[1] - on, 2)
                    if not (lo <= e <= hi):
                        continue
                    sh = recut_shift(e)
                    if sh <= 0.0:
                        continue
                    # The SOUTH BANK OF THE MAIN STEM only. The north bank stands 100 m
                    # north of it on this reach and does not move; the two vertices inside
                    # the La Salle channel below the mouth (N +9.6 and N +5.3) are the
                    # slough T-1628 cut back a fortnight ago, whose mouth at (466, +10) is
                    # settled and stays where it is. What moves is the bank and the outer
                    # lip of Wright's re-entrant that the bank arrives at.
                    if n > 80.0 or n < 12.0:
                        continue
                    aside.setdefault(e, n)
                    c[1] = round(on + n - sh, 2)
                    moved += 1
        if not dry:
            path.write_text(json.dumps(doc, indent=1) + "\n")
    rec["recut"] = {
        "ticket": "T-1630",
        "ruling": RECUT_RULING,
        "grade": "reconstructed",
        "grade_note": (
            "The waterline on this reach is no longer a trace of the sheet the datum, the "
            "plat and the block grid are fitted to. It is Wright's traced line displaced "
            "by the two sheets' own measured disagreement, on the owner's ruling, which is "
            "an invention within stated bounds. docs/LIBERTIES.md carries it."),
        "sources": ["hathaway_1834", "wright_1834_nara_hup"],
        "shift_anchors_local_e_m": [[e, sh] for e, sh in RECUT_SHIFT_ANCHORS],
        "block_18_refused_m": RECUT_BLOCK_18_REFUSED_M,
        "block_18_refusal": (
            "East of the slough the committed bank stands 5.4 m north of South Water "
            "Street's own platted corridor edge, so the ruling's 7.5 m would put the river "
            "2.1 m into the roadway. The reach is bounded by the owner's own words, \"from "
            "the bend in the west to the La Salle mouth\"."),
        "wright_bank_as_traced": [[e, aside[e]] for e in sorted(aside)],
    }
    rec["measured"].update(derive(rec))
    rec["findings"] = findings(rec)
    if not dry:
        OUT.write_text(json.dumps(rec, indent=1) + "\n")
    m = rec["measured"]["recut"]
    print(f"recut: {moved} vertex writes over {len(aside)} distinct bank stations; "
          f"worst re-derivation error {m['worst_vertex_error_m']} m; "
          f"step across the La Salle mouth {m['step_across_the_la_salle_mouth_m']} m; "
          f"straightness p90 {m['straightness_p90_m']} m")
    return 0


def report():
    rec = json.loads(OUT.read_text())
    m = rec["measured"]
    print(f"South Division bank, the bend to the La Salle mouth — read {rec['read_on']}")
    print(f"  {rec['ticket']}")
    s = m["committed_against_wright_ink"]
    print(f"\n  committed waterline against Wright's inked bank (NA/HUP sheet), "
          f"{s['stations']} stations at {s['sampled_every_m']:.0f} m:")
    print(f"    median {s['median_m']} m   p90 {s['p90_m']} m   worst {s['max_m']} m   "
          f"({s['in_the_slough_mouth_not_measured']} in the slough mouth, not measured)")
    print("\n  the ground each sheet draws between its own bank and its own block tier:")
    print("    block   Wright   Hathaway   Wright wider by")
    for k in sorted(m["wright_minus_hathaway_m"], reverse=True):
        print(f"      {k:>2}    {m['south_water_ground_m']['wright_1834_nara_hup'][k]:6.1f} m "
              f"{m['south_water_ground_m']['hathaway_1834'][k]:8.1f} m "
              f"{m['wright_minus_hathaway_m'][k]:12.1f} m")
    print(f"\n  swell, as the two sheets' disagreement across the reach: "
          f"{m['swell_amplitude_m']} m")
    if "recut" in m:
        r = m["recut"]
        print(f"\n  the recut, on the owner's ruling of 2026-09-26 (option b):")
        print(f"    bank moved south {r['shift_m_at_block_20']} m at block 20, "
              f"{r['shift_m_at_block_19']} m at block 19, "
              f"{r['shift_m_at_block_18']} m at block 18, "
              f"{r['shift_m_at_block_17']} m at block 17")
        print(f"    {r['vertices_moved']} bank stations moved; "
              f"re-derives to {r['worst_vertex_error_m']} m")
        print(f"    step across the La Salle mouth {r['step_across_the_la_salle_mouth_m']} m; "
              f"straightness p90 {r['straightness_p90_m']} m")
    print("")
    for f in rec["findings"]:
        print(f"  * {f}\n")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--recut", action="store_true",
                    help="apply T-1630's ruling to the committed bank (once)")
    a = ap.parse_args()
    if a.build:
        return build()
    if a.check:
        return check()
    if a.self_test:
        return self_test()
    if a.recut:
        return recut()
    return report()


if __name__ == "__main__":
    sys.exit(main())
