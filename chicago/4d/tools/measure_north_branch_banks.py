#!/usr/bin/env python3
"""Both banks of the North Branch reach, per row, against the bank Wright inked.

T-1078. `tools/trace_north_branch.py` published a reach whose east boundary sat a
median 1.4 m inside Wright's inked east bank and was short of it by more than
10 m on 81 of the reach's 932 rows, in two stretches — and the fault was FILED
(docs/RESEARCH/north_branch_wabansia.md § 5) rather than measured once and
forgotten. This is the measurement, committed, so the repair could be argued
against a number and so the next change to the trace has to answer to one.

    python3 tools/measure_north_branch_banks.py           measure, print, and
                                                          compare the two masks
    python3 tools/measure_north_branch_banks.py --check    hold the committed
                                                          baseline to a re-run
    python3 tools/measure_north_branch_banks.py --write    rewrite the baseline

## What is measured, and why it is per row and not per vertex

`tools/measure_water_outliers.py --vs-ink` measures the committed geometry's
VERTICES against the ink, which is the right question for a spike. It is the
wrong question for a stretch: the boundary here is short over fifty-two
consecutive rows and the simplifier puts three vertices on them, so a vertex scan
reports three numbers where the fault has fifty-two. This reach runs north-south
across the sheet, so every row of it crosses the channel once and an east-west
ray per row is the natural traverse — which is how T-1072 measured it, and the
before column below reproduces its published numbers exactly.

For each row of the reach: the traced channel's outermost pixel on each side, and
the nearest INKED pixel outward from it (`trace_river.ink_mask`, the same
luminance threshold the trace reads the ink with). The signed distance is
POSITIVE when the boundary stands inside the ink — inside the water — which is
the direction this trace is deliberately wrong in, and NEGATIVE when it has
crossed Wright's line into the ground beyond, which is the direction it must
never be wrong in.

## The leak test, which is the one that could have gone badly

`hue_tol` 7 is not a tuning; it is the value at which the traced WEST bank stops
stepping 93 m into Wabansia's platted river-front lots (§ 3 of the research
note). Any repair to the east bank has to be shown not to have bought itself back
that error, and "the west median improved" does not show it. So the west bank is
measured against a fixed reference — the inked west bank as the PRE-repair trace
found it, row by row — and the test is that no row's boundary has crossed it.
Reported as `west_crossings` and `west_worst_crossing_m`, and both must be zero
for the repair to stand.

Needs numpy, scipy and Pillow and the Wright region raster, and degrades to a
clear skip without them — like the three traces, and for the same reason.
`tools/check.sh` holds the committed baseline's SHAPE (`--check-properties` on
the trace does the geometry); the numbers are re-derived by hand when the trace
changes, which is what `--check` is for.
"""

from __future__ import annotations

import argparse
import io
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import trace_north_branch as tnb  # noqa: E402
import trace_river as tr  # noqa: E402

BASELINE = ROOT / "tools" / "north_branch_bank_baseline.json"

# The rows the reach is measured over. Its south end is the splice row, the
# window's own south edge. Its north end is NOT the channel's first drawn row
# (309): the top eleven rows are the tip tapering into the line Wright ruled
# across his survey, where the nearest ink outward from the boundary IS that
# ruled line rather than a bank, and measuring the boundary against it would
# report the survey limit as a bank fault. 320 is where the two banks are both
# banks, and it is the span T-1072 measured, so the before column here is
# comparable to the number the ticket was opened on.
ROW_LO = 320
ROW_HI = tnb.SPLICE_ROW - 1

# How far OUTWARD a row's ray looks for the ink. Wider than any gap the reach
# carries (the worst is 46 px at the splice row) and narrower than the distance
# to the next drawn line beyond the bank, so a row whose bank ink is broken is
# dropped from the measurement rather than silently measured to a lot line.
INK_SEARCH_PX = 140

# ...and how far INWARD, which is the half a one-sided ray gets wrong. Where the
# boundary has slipped PAST Wright's pen line the bank ink stands on the water
# side of it, an outward-only ray walks straight over it and reports the distance
# to the next drawn line beyond — at row 1251 the west boundary stands 2.8 m
# outside the inked west bank and an outward ray calls it 41.3 m INSIDE, because
# it found a lot line 58 px away (§ 2 of the research note has the true reading).
# 20 px is generous for a boundary that has overshot its own line and far too
# small to reach the opposite bank, which is never nearer than ~100 px here.
INK_INWARD_PX = 20

# The threshold the ticket and § 5 count rows at. Not a tolerance — the polygon
# declares uncertainty_m 20 — but the shape question: a boundary 10 m off its
# own source line over a run of rows is a stretch, not drafting scatter.
SHORT_M = 10.0

# Acceptance 2 of T-1078 asked for a number the ticket did not have: "no row's
# west boundary west of Wright's inked west bank by more than the p90 this ticket
# records", and that p90 — 8.54 m — is the EAST bank's. Measured, the west bank
# already stood 14.23 m outside its own inked line on 42 rows before any repair,
# in five stretches this note's § 5 names. So the ceiling here is that pre-repair
# reading rather than a figure borrowed from the other bank, and it is a RATCHET:
# it may come down, and `rows_worse_than_before` — which must be zero — is the
# test that actually carries the acceptance. The repair brings it to 9.96 m on 34
# rows, so the ratchet has already paid once.
LEAK_BUDGET_M = 14.23


def percentile(v, q):
    """The one statistic this needs, without dragging numpy into the print path."""
    s = sorted(v)
    if not s:
        return None
    k = (len(s) - 1) * q / 100.0
    lo, hi = int(k), min(int(k) + 1, len(s) - 1)
    return s[lo] + (s[hi] - s[lo]) * (k - lo)


def runs_of(rows, gap=3):
    """Consecutive stretches, so a run of short rows reads as one finding."""
    out = []
    for r in rows:
        if out and r <= out[-1][1] + gap:
            out[-1][1] = r
        else:
            out.append([r, r])
    return [[int(a), int(b)] for a, b in out]


def side_profile(water, ink, side, np, cell_m):
    """Per row: the boundary pixel, the inked bank, and the SIGNED gap.

    The inked bank is the nearest ink to the boundary — outward within
    `INK_SEARCH_PX`, inward within `INK_INWARD_PX` — and the sign says which side
    of Wright's line the boundary came down on. POSITIVE is inside the ink, in
    water that is really water, which is the direction this trace is deliberately
    wrong in. NEGATIVE is outside it, over the line into the ground beyond, which
    is the direction it must never be wrong in.
    """
    h, w = ink.shape
    prof = {}
    for y in range(ROW_LO, ROW_HI + 1):
        xs = np.nonzero(water[y])[0]
        if not len(xs):
            continue
        b = int(xs.max()) if side == "east" else int(xs.min())
        out_d = in_d = None
        if side == "east":
            k = np.nonzero(ink[y, b + 1:min(w, b + 1 + INK_SEARCH_PX)])[0]
            out_d = 1 + int(k[0]) if len(k) else None
            lo = max(0, b - INK_INWARD_PX)
            k = np.nonzero(ink[y, lo:b])[0]
            in_d = b - (lo + int(k[-1])) if len(k) else None
        else:
            lo = max(0, b - INK_SEARCH_PX)
            k = np.nonzero(ink[y, lo:b])[0]
            out_d = b - (lo + int(k[-1])) if len(k) else None
            k = np.nonzero(ink[y, b + 1:min(w, b + 1 + INK_INWARD_PX)])[0]
            in_d = 1 + int(k[0]) if len(k) else None
        if out_d is None and in_d is None:
            continue
        if in_d is not None and (out_d is None or in_d < out_d):
            d_px, ink_x = -in_d, (b - in_d if side == "east" else b + in_d)
        else:
            d_px, ink_x = out_d, (b + out_d if side == "east" else b - out_d)
        prof[y] = (b, int(ink_x), d_px * cell_m)
    return prof


def summarise(prof):
    d = [v[2] for v in prof.values()]
    short = [y for y, v in prof.items() if v[2] > SHORT_M]
    outside = {y: round(-v[2], 2) for y, v in prof.items() if v[2] < 0}
    return {
        "rows": len(d),
        "median_m": round(percentile(d, 50), 2),
        "p90_m": round(percentile(d, 90), 2),
        "max_m": round(max(d), 2),
        "rows_over_10m": len(short),
        "stretches": runs_of(sorted(short)),
        "rows_outside_the_ink": len(outside),
        "worst_outside_the_ink_m": round(max(outside.values(), default=0.0), 2),
        "outside_stretches": runs_of(sorted(outside)),
    }


def measure(np, ndi):
    from PIL import Image

    tnb.configure()
    coef, rms, n_gcp = tr.affine_from_gcps()
    cell_m = 0.5 * (abs(coef[0] ** 2 + coef[3] ** 2) ** 0.5
                    + abs(coef[1] ** 2 + coef[4] ** 2) ** 0.5)
    raw, sha = tr.fetch_region(Path("/tmp") / "wright_1834_north_branch_region.jpg")
    rgb = np.asarray(Image.open(io.BytesIO(raw)).convert("RGB"))
    print(f"region {tnb.REGION} sha256 {sha[:16]}...  {cell_m:.4f} m per map pixel, "
          f"affine RMS {rms:.1f} m from {n_gcp} GCPs")

    P = tnb.PARAMS
    wash = tr.wash_mask(rgb, np)
    ink = tr.ink_mask(rgb, np, P["ink_lum"])

    # BEFORE: the mask the trace published until T-1078 — the speckle floor and
    # nothing else, which is what dropped the cut-off bank wash.
    before = tr.channel_from(wash, tnb.SEEDS, P["close_r"], P["open_r"], 0, np, ndi,
                             speckle=P["speckle_px"])
    # AFTER: the mask the trace publishes now, taken from the trace itself.
    after, _ = tnb.channel(rgb, np, ndi, quiet=True)
    # What `bank_wash`'s three-pixel seam does on this reach, for the record.
    bw, bw_put = tr.bank_wash(wash, ink, tnb.SEEDS, P["close_r"], P["open_r"], 0, np, ndi, P)
    bank_wash_mask = tr.channel_from(bw, tnb.SEEDS, P["close_r"], P["open_r"], 0, np, ndi)

    out = {
        "ticket": "T-1078",
        "reach_rows": [ROW_LO, ROW_HI],
        "iiif_region_sha256": sha,
        "map_scale_m_per_px": round(cell_m, 4),
        "channel_px": {"before": int(before.sum()),
                       "bank_wash_only": int(bank_wash_mask.sum()),
                       "after": int(after.sum())},
        "bank_wash_puts_back_on_the_east_bank": False,
    }

    profiles = {}
    for name, mask in (("before", before), ("after", after)):
        for side in ("east", "west"):
            prof = side_profile(mask, ink, side, np, cell_m)
            profiles[(name, side)] = prof
            out.setdefault(name, {})[side] = summarise(prof)
            s = out[name][side]
            print(f"{name:7s} {side:5s} n={s['rows']} median={s['median_m']:5.2f} "
                  f"p90={s['p90_m']:5.2f} max={s['max_m']:6.2f} "
                  f">10m={s['rows_over_10m']:3d} stretches={s['stretches']}")

    # bank_wash on the east bank, measured rather than asserted
    bw_east = side_profile(bank_wash_mask, ink, "east", np, cell_m)
    same = all(bw_east.get(y, (None,))[0] == profiles[("before", "east")][y][0]
               for y in profiles[("before", "east")])
    out["bank_wash_puts_back_on_the_east_bank"] = not same
    out["bank_wash_fragments_put_back"] = sorted(int(px) for px, _d in bw_put)
    print(f"bank_wash: {len(bw_put)} fragment(s) put back anywhere on the reach "
          f"{sorted(int(px) for px, _d in bw_put)}; east boundary moved: {not same}")

    # THE LEAK TEST, in acceptance 2's own words: no row's west boundary west of
    # Wright's inked west bank by more than the p90 this ticket records (8.54 m),
    # and no row worse than it already was.
    bw, aw = profiles[("before", "west")], profiles[("after", "west")]
    deeper = [(y, round(bw[y][2] - aw[y][2], 2)) for y in aw
              if y in bw and aw[y][2] < min(0.0, bw[y][2]) - 1e-9]
    out["west_leak_test"] = {
        "budget_m": LEAK_BUDGET_M,
        "rows_outside_the_ink": out["after"]["west"]["rows_outside_the_ink"],
        "worst_outside_the_ink_m": out["after"]["west"]["worst_outside_the_ink_m"],
        "rows_worse_than_before": len(deeper),
        "worst_deepening_m": round(max((m for _y, m in deeper), default=0.0), 2),
        "rows": runs_of(sorted(y for y, _m in deeper)),
    }
    lt = out["west_leak_test"]
    print(f"leak test: {lt['rows_outside_the_ink']} row(s) outside the inked west bank, "
          f"worst {lt['worst_outside_the_ink_m']} m of a {LEAK_BUDGET_M} m budget; "
          f"{lt['rows_worse_than_before']} row(s) worse than before")

    # THE SPLICE ROW, both sides
    sp = {}
    for name in ("before", "after"):
        for side in ("east", "west"):
            p = profiles[(name, side)].get(ROW_HI)
            if p:
                sp[f"{name}_{side}"] = {
                    "boundary_resource_x": p[0] + tnb.REGION[0],
                    "ink_resource_x": p[1] + tnb.REGION[0],
                    "inside_the_ink_m": round(p[2], 2),
                }
    out["splice_row"] = {"row": ROW_HI, **sp}
    for k, v in sp.items():
        print(f"splice row {ROW_HI} {k:12s} boundary x={v['boundary_resource_x']} "
              f"ink x={v['ink_resource_x']}  {v['inside_the_ink_m']} m inside the ink")
    return out


# The forks trace measures the North Branch's drafted width just SOUTH of the
# splice row and this trace measures it just NORTH of it, from two windows that
# share nothing but that line. They should agree, and before T-1078 they did not:
# 62.6 m against 72.9 m, a 10.3 m step at the seam, because the east bank was
# short exactly there. The tolerance below is the step the two windows are allowed
# to keep — a drafted width read through a distance transform at two stations one
# row apart, not a survey.
SPLICE_WIDTH_TOLERANCE_M = 1.0


def check_properties() -> int:
    """Hold the committed baseline to this file's literals and to the two things
    the repair must not stop being true — offline, in milliseconds, and therefore
    runnable by `tools/check.sh`.

    `--check` is the real gate and cannot live there: it needs numpy, scipy and
    Pillow and fetches the IIIF region over the network, the same reason the three
    traces' own `--check` modes are not gated either. What IS gated is the pair of
    claims a future change to the trace could quietly break without any file
    looking wrong — that the east bank's repair did not buy back the west bank's
    93 m leak, and that the two windows still agree on the channel's width across
    the line they are spliced on.
    """
    bad = []
    if not BASELINE.exists():
        print(f"FAIL {BASELINE.relative_to(ROOT)} is not committed")
        return 1
    b = json.loads(BASELINE.read_text())

    def eq(label, got, want):
        if got != want:
            bad.append(f"{label}: baseline {got!r} != {want!r}")

    eq("ticket", b.get("ticket"), "T-1078")
    eq("reach_rows", b.get("reach_rows"), [ROW_LO, ROW_HI])
    for k in ("map_scale_m_per_px", "iiif_region_sha256", "channel_px", "splice_row"):
        if k not in b:
            bad.append(f"baseline has no {k}")

    # THE LEAK TEST, as a per-commit invariant
    lt = b.get("west_leak_test") or {}
    eq("west_leak_test.budget_m", lt.get("budget_m"), LEAK_BUDGET_M)
    if lt.get("worst_outside_the_ink_m", 1e9) > LEAK_BUDGET_M:
        bad.append(f"the west boundary stands {lt.get('worst_outside_the_ink_m')} m west of "
                   f"Wright's inked west bank on {lt.get('rows_outside_the_ink')} row(s), "
                   f"past the {LEAK_BUDGET_M} m acceptance 2 allows — the repair has bought "
                   "back the leak hue_tol 7 exists to prevent")
    for side in ("east", "west"):
        a = (b.get("after") or {}).get(side) or {}
        be2 = (b.get("before") or {}).get(side) or {}
        if a.get("rows_outside_the_ink", 1e9) > be2.get("rows_outside_the_ink", -1):
            bad.append(f"the {side} boundary stands outside Wright's ink on "
                       f"{a.get('rows_outside_the_ink')} rows after the repair and on "
                       f"{be2.get('rows_outside_the_ink')} before it")
    if lt.get("rows_worse_than_before", 1) != 0:
        bad.append(f"the west boundary is further outside the ink than before the repair on "
                   f"{lt.get('rows_worse_than_before')} row(s), worst "
                   f"{lt.get('worst_deepening_m')} m")

    # the east bank must not have got worse, and the splice must have got better
    be, ae = (b.get("before") or {}).get("east") or {}, (b.get("after") or {}).get("east") or {}
    if ae.get("rows_over_10m", 1e9) > be.get("rows_over_10m", -1):
        bad.append(f"the east bank is short on {ae.get('rows_over_10m')} rows after the "
                   f"repair and was short on {be.get('rows_over_10m')} before it")
    sp = b.get("splice_row") or {}
    a_sp = (sp.get("after_east") or {}).get("inside_the_ink_m")
    b_sp = (sp.get("before_east") or {}).get("inside_the_ink_m")
    if a_sp is None or b_sp is None or a_sp >= b_sp:
        bad.append(f"the splice row's east boundary stands {a_sp} m inside the ink and "
                   f"stood {b_sp} m — the stretch this ticket was opened on")

    # the two windows agree on the channel's width across the line they splice on
    def width(path, fid):
        doc = json.loads((ROOT / path).read_text())
        for f in doc.get("features", []):
            if f.get("id") == fid:
                return (f["properties"].get("drafted_width_m") or {}).get("north_branch")
        return None

    epoch = "data/terrain/epochs/e1834_harbor_cut"
    north = width(f"{epoch}/branches.geojson", "north_branch_wabansia")
    forks = width(f"{epoch}/river.geojson", "chicago_river_forks")
    if north is None or forks is None:
        bad.append(f"no drafted north_branch width to compare: {north!r} / {forks!r}")
    elif abs(north - forks) > SPLICE_WIDTH_TOLERANCE_M:
        bad.append(f"the two windows disagree on the North Branch's drafted width across "
                   f"the splice row: {north} m north of it, {forks} m south of it")

    for line in bad:
        print("FAIL", line)
    if not bad:
        print(f"OK   {BASELINE.relative_to(ROOT)} — the west boundary is at worst "
              f"{lt.get('worst_outside_the_ink_m')} m outside the ink of a "
              f"{LEAK_BUDGET_M} m budget and no row worse than before; the splice row's "
              f"east boundary stands {a_sp} m inside the ink, was {b_sp} m; the two "
              f"windows agree on {north} m of drafted width across the splice")
    return 1 if bad else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="diff against the committed baseline")
    ap.add_argument("--check-properties", action="store_true",
                    help="hold the committed baseline to this file's literals and to the "
                         "leak test — no numpy, no network; this is the half check.sh runs")
    ap.add_argument("--write", action="store_true", help="rewrite the committed baseline")
    args = ap.parse_args()

    if args.check_properties:
        return check_properties()

    try:
        import numpy as np
        from scipy import ndimage as ndi
        import PIL  # noqa: F401
    except ImportError as e:
        print(f"SKIP: {e.name} not installed (pip install numpy scipy pillow); "
              "north branch bank measurement not run")
        return 0

    got = measure(np, ndi)
    text = json.dumps(got, indent=2) + "\n"
    if args.write:
        BASELINE.write_text(text)
        print(f"wrote {BASELINE.relative_to(ROOT)}")
        return 0
    if args.check:
        if not BASELINE.exists():
            print(f"FAIL {BASELINE.relative_to(ROOT)} is not committed")
            return 1
        same = BASELINE.read_text() == text
        print(f"{'OK  ' if same else 'DIFF'} {BASELINE.relative_to(ROOT)}")
        return 0 if same else 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
