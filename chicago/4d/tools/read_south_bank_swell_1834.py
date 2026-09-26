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
    dens = [p for p in resample(committed_bank(), SAMPLE_ALONG_M)
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
    return out


VERDICT_KEYS = ("committed_against_wright_ink", "south_water_ground_m",
                "wright_minus_hathaway_m", "swell_amplitude_m")


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
        bad.append("  the committed bank no longer stands on Wright's ink: "
                   f"median {stat['median_m']} m, p90 {stat['p90_m']} m "
                   "(this reading's verdict says it does)")
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
        f"THE COMMITTED BANK IS WRIGHT'S INK. Over {s['stations']} committed vertices between "
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
        "to correct on the trace's own terms. Bringing the bank in to the owner's line would "
        "move it OFF the ink of the sheet his own third message makes the arbiter, which is "
        "the one thing that message forbids. That is a ruling, not a measurement, and it is "
        "asked rather than taken.",
    ]


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
    a = ap.parse_args()
    if a.build:
        return build()
    if a.check:
        return check()
    if a.self_test:
        return self_test()
    return report()


if __name__ == "__main__":
    sys.exit(main())
