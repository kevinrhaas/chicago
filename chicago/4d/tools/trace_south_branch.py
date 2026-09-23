#!/usr/bin/env python3
"""Trace the South Branch south of the forks window, off Wright 1834.

The southern companion to `tools/trace_river.py` (the forks) and
`tools/trace_shoreline.py` (the harbour and the lake). Those two leave a gap
this one fills: Wright draws the South Branch on past the forks box, out of the
Original Town, across Madison Street and down through the School Section's
blocks 70, 71, 78 and 83-88 to the section's south line, and the project's
committed water stopped at the forks window's own edge.

    python3 tools/trace_south_branch.py            re-trace and write the GeoJSON
    python3 tools/trace_south_branch.py --check    re-trace and diff against committed
    python3 tools/trace_south_branch.py --debug    also write a PNG overlay
    python3 tools/trace_south_branch.py --check-properties
                                                   hold the committed file to this
                                                   file's literals: no numpy, no
                                                   network. This one IS in check.sh.

Why a third window rather than a bigger second one
--------------------------------------------------
`trace_river.py` says it in its own docstring and it is still true: the forks
work at a LOCAL block percentile, which is what lets a 70 m channel be found in
a town of coloured ward washes. Widening that window instead of adding one would
move every vertex the forks trace has already committed, because the morphology
that finds the channel is computed over the whole window — and the ground is
carved from those vertices. So this is a separate window whose NORTH edge is the
forks window's SOUTH edge (map row 2372), which makes the splice a declared line
rather than a tolerance: `river.geojson` is not touched by this tool at all, and
the two polygons abut on a row of the scan both of them name.

The one setting that had to change, and what it cost to find out
---------------------------------------------------------------
The hue reference. `wash_mask` separates Wright's grey bank wash from his
coloured ward washes by asking whether a pixel departs in hue from THE LOCAL
PAPER, and it estimates the local paper's hue as a percentile over a block of
`hue_block` pixels. At the forks, 280 px at the 40th percentile is paper. Here
it is not: from map row 3580 to row 3985 the channel runs right alongside the
yellow wash of the School Section's reserved blocks 87 and 88, a 280 px block
straddles the two, and the 40th percentile of it is the YELLOW. Measured over
that reach the grey bank wash then departs from its own reference by 27 units
against a tolerance of 11, so it was thrown away as a coloured wash: 400 px of
river — 285 m, the whole stretch between the two bridge symbols — simply did not
exist for the segmentation, and the channel came out as two disconnected pieces.
The fix is to read the paper off the LEAST tinted part of a SMALLER block
(`hue_block` 160, `hue_pct` 15) so the reference is paper even where paper is the
minority of the neighbourhood. The reach then comes out whole, from one seed,
with no hand-placed waypoints along it.

`open_r` also goes from 9 to 12, which is not a threshold so much as a knife: a
4,000 px patch of stained paper in the West Division, near block 51, hangs off
the channel by a neck the 9 px opening leaves standing. Widening the opening
severs it and changes the channel's own width at no station on the reach — that
is asserted below, not assumed.

The tear, and where it is not
-----------------------------
T-0794 asked this trace to say where the manuscript's missing portion falls,
because the Historic Urban Plans reproduction of the NARA original carries the
caption "Two portions are missing, the larger being near the lower center ...
the manuscript was mounted on cloth to repair this tear", and the lower centre
of the sheet is exactly blocks 87 and 88. It is not on THIS scan. The BPL master
this project traces carries the reach whole: both banks are drawn unbroken past
the reserved blocks, the two bridge symbols on it are intact, and the only thing
the region does carry is the yellow reservation wash described above — which is
what made the reach look absent to the machine and is a fact about the
reference, not about the paper. So nothing here is graded down for the tear and
no gap is boxed. See docs/RESEARCH/south_branch_school_section.md.

Needs numpy, scipy, Pillow and the network. Like the other two traces the full
re-run is a deliberate, occasional one and is not part of tools/check.sh; it
degrades to a clear skip when the dependencies are missing. `--check-properties`
is the half that costs nothing, and check.sh runs it.
"""

from __future__ import annotations

import argparse
import io
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import branches_file as bfile  # noqa: E402  — the shared owner of the output collection
import trace_river as tr  # noqa: E402  — the shared segmentation, deliberately not re-implemented

OUT = bfile.PATH

IIIF = tr.IIIF

# The region of the BPL master scan (resource space, 4204 x 5166) this trace
# works in. Its top edge is the forks window's bottom edge — trace_river's
# REGION is (868, 1252, 1120, 1120), so that row is 1252 + 1120 = 2372 — which is
# what makes the splice a line and not a tolerance. Its other three edges stand
# clear of the water: the traced channel's own extent is checked against them
# below, so a re-run that ever reached one would fail rather than publish a bank
# that is really a window.
SPLICE_ROW = 2372
REGION = (1150, SPLICE_ROW, 800, 2578)

# How near the reach's last drawn row a boundary vertex may come and still be
# published as a bank. Wright's wash runs straight into the School Section's
# south boundary line and stops on it: the survey ends there, the river does not.
# That terminal stretch is dropped for the same reason trace_shoreline.py drops
# the east edge of the lake wash — it is where the draughtsman lifted the brush,
# and publishing it would assert a river end this sheet never drew. It cannot be
# told by the ink, because at this terminus there IS a line: the section's own
# boundary, drawn across the channel.
LIMIT_MARGIN_PX = 6

# One seed, in resource pixels, in open channel two hundred rows below the
# splice. It is the only hand-placed number in this trace: the reach comes out of
# it in one connected piece, so there are no waypoints down the length.
SEEDS = {"south_branch": (1403, 2600)}

# The forks settings, with the two changes the docstring argues for.
PARAMS = dict(tr.PARAMS, hue_block=160, hue_pct=15, open_r=12)

# The collection's own fields describe every reach in it, so they are not this
# tool's to state: `branches.geojson` has had a second writer since T-1072 and
# tools/branches_file.py owns what the two of them agree on.
NAME = bfile.NAME
CRS = bfile.CRS
DOC = bfile.DOC

WATER_ID = "south_branch_school_section"
WATER_PROPS = {
    "kind": "water",
    "name": "Chicago River, South Branch — Original Town to the School Section's south line",
    "reaches": ["south_branch"],
    "water_surface_ft_above_datum": 0.0,
    "confidence": "inferred",
    "note": "Planform traced from the Wright 1834 survey, in a window whose north edge is "
            "the forks window's south edge, so this polygon abuts river.geojson on map row "
            "2372 of the BPL master and moves no vertex of it. The water surface is flat at "
            "the datum for the same reason the forks are: the pre-reversal river had a "
            "near-zero surface gradient and stood at lake level through this reach. NO BED "
            "DEPTH IS CLAIMED HERE AT ALL. A cadastral plat gives planform and not "
            "soundings, and a traced bank must not be allowed to promote a bed — see "
            "docs/RESEARCH/south_branch_school_section.md. The polygon's southern edge is "
            "the LIMIT OF THE SURVEY and not a river end: Wright's wash runs into the School "
            "Section's south boundary line and stops on it, and the two bank lines are cut "
            "short of that stretch rather than carried across it. The manuscript tear the NARA "
            "reproduction's caption reports near the sheet's lower centre is not present on "
            "this scan: the BPL master draws both banks unbroken past reserved blocks 87 and "
            "88, so no reach of this trace is graded down for it and no gap is boxed.",
    "sources": ["wright_1834"],
}

BANK_LABELS = {
    "south_branch_west_bank": "West bank of the South Branch: the Original Town west of "
                              "Market Street, and the School Section's blocks 69-71 and 78",
    "south_branch_east_bank": "East bank of the South Branch: the Original Town west of "
                              "Wells Street, and the School Section's blocks 83-88",
}
BANK_PROPS = {
    "kind": "bank",
    "crest_ft_above_datum": None,
    "confidence": "inferred",
    "note": "Bank line is the water polygon's boundary where it is neither the splice row "
            "this window's north edge stands on nor the survey limit its south end stops on. "
            "Crest heights are not carried here: south of the "
            "modelled terrain box there is no heightfield for them to belong to yet.",
    "sources": ["wright_1834"],
}

PROV_STATIC = {
    "traced_from": "wright_1834",
    "method": "grey bank-wash segmentation of the BPL master scan, closed across the "
              "unshaded mid-channel; boundary traced and simplified; pixels transformed "
              "to EPSG:26916 by the least-squares affine refit from "
              "data/traces/gcp/wright_1834_gcps.json. The hue reference is read off a "
              "smaller block at a lower percentile than the forks trace uses, so that the "
              "School Section's yellow reservation wash cannot stand in for paper",
    "tool": "tools/trace_south_branch.py",
    "splices_onto": "data/terrain/epochs/e1834_harbor_cut/river.geojson at BPL master row 2372",
    "uncertainty_m": 20,
    "uncertainty_note": tr.PROV_STATIC["uncertainty_note"],
}
PROV_KEYS = ("traced_from", "method", "tool", "splices_onto", "iiif_region", "affine_rms_m",
             "map_scale_m_per_px", "simplify_tolerance_m", "uncertainty_m", "uncertainty_note")


def split_bank_runs(ring_px, limit_row):
    """Split the traced ring into the runs that are BANK and the runs that are not.

    `tools/trace_river.py`'s own `split_runs` drops the stretches that lie on the
    traced window's edge, and that is one of the two things to drop here: this
    window's north edge is the splice row, where the polygon meets the committed
    forks trace rather than a shore. The other is the reach's south end, which is
    not an edge of the window — the channel stops 161 px clear of it — but the
    edge of the SURVEY. Both are reported, in map pixels, on every run.
    """
    w, h = REGION[2], REGION[3]
    m = len(ring_px)
    reason = []
    for px, py in ring_px:
        if px <= 3 or py <= 3 or px >= w - 4 or py >= h - 4:
            reason.append("window")
        elif py >= limit_row - LIMIT_MARGIN_PX:
            reason.append("survey limit")
        else:
            reason.append(None)
    if not any(reason):
        return [list(range(m))]
    for kind in ("window", "survey limit"):
        n = sum(1 for r in reason if r == kind)
        print(f"   dropped {n} ring vertices on the {kind}")
    start = next(i for i in range(m) if reason[i])
    runs, cur = [], []
    for k in range(m + 1):
        i = (start + k) % m
        if reason[i]:
            if len(cur) > 2:
                runs.append([(cur[0] - 1) % m] + cur + [i])
            cur = []
        else:
            cur.append(i)
    return runs


def check_properties() -> int:
    """Hold the committed file to the literals above — offline, in milliseconds."""
    if not OUT.exists():
        print(f"FAIL {OUT.relative_to(ROOT)} is not committed")
        return 1
    doc = json.loads(OUT.read_text())
    bad = []

    def eq(label, got, want):
        if got != want:
            bad.append(f"{label}: committed {got!r} != {want!r}")

    own = (WATER_ID, *BANK_LABELS)
    bfile.check_collection(doc, own, eq, bad)
    feats = {f.get("id"): f for f in doc.get("features", [])}

    w = feats.get(WATER_ID, {}).get("properties", {})
    for k in ("kind", "name", "reaches", "water_surface_ft_above_datum", "confidence",
              "note", "sources"):
        eq(f"{WATER_ID}.{k}", w.get(k), WATER_PROPS[k])
    if "bed_depth_ft_below_datum" in w or "assumed_depth_ft_below_datum" in w:
        bad.append(f"{WATER_ID}: carries a bed depth, which this trace refuses to claim")
    prov = w.get("provenance") or {}
    eq("provenance key order", list(prov), list(PROV_KEYS))
    for k, v in PROV_STATIC.items():
        eq(f"provenance.{k}", prov.get(k), v)
    reg = prov.get("iiif_region") or {}
    eq("iiif_region", [reg.get("image"), reg.get("x"), reg.get("y"), reg.get("w"), reg.get("h")],
       [IIIF, REGION[0], REGION[1], REGION[2], REGION[3]])
    if reg.get("y") != SPLICE_ROW:
        bad.append(f"iiif_region.y {reg.get('y')} is not the splice row {SPLICE_ROW}")

    for bid, label in BANK_LABELS.items():
        b = feats.get(bid, {}).get("properties", {})
        eq(f"{bid}.name", b.get("name"), label)
        for k in ("kind", "crest_ft_above_datum", "confidence", "note", "sources"):
            eq(f"{bid}.{k}", b.get(k), BANK_PROPS[k])

    for line in bad:
        print("FAIL", line)
    if not bad:
        print(f"OK   {OUT.relative_to(ROOT)} matches tools/trace_south_branch.py literals "
              f"({len(feats)} features, splice row {SPLICE_ROW})")
    return 1 if bad else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="diff against the committed GeoJSON")
    ap.add_argument("--check-properties", action="store_true",
                    help="hold the committed GeoJSON to this file's literals — no numpy, "
                         "no network; this is the half tools/check.sh runs")
    ap.add_argument("--debug", action="store_true", help="write a PNG overlay of the trace")
    ap.add_argument("--cache", default=str(Path("/tmp") / "wright_1834_south_branch_region.jpg"))
    args = ap.parse_args()

    if args.check_properties:
        return check_properties()

    try:
        import numpy as np
        from PIL import Image
        from scipy import ndimage as ndi
    except ImportError as e:
        tr.die(f"SKIP: {e.name} not installed (pip install numpy scipy pillow); "
               "south branch trace not run", 0)

    # The shared segmentation reads its window and its settings off trace_river's
    # module globals. Point them at this window for the life of this process — it
    # is one process per trace, and the alternative is a second copy of 300 lines
    # of morphology that would then drift from the one this project has argued
    # about. The forks window is asserted first, so a change there is caught here.
    if (tr.REGION[1] + tr.REGION[3]) != SPLICE_ROW:
        tr.die(f"the forks window's south edge is row {tr.REGION[1] + tr.REGION[3]}, not "
               f"{SPLICE_ROW}: this trace's splice line moved with it and must be re-argued")
    tr.REGION = REGION
    tr.SEEDS = SEEDS
    tr.PARAMS.clear()
    tr.PARAMS.update(PARAMS)

    datum = json.loads((ROOT / "data" / "datum.json").read_text())
    if not datum.get("verified"):
        tr.die("REFUSING: data/datum.json is not verified.")
    o_e, o_n = datum["origin_utm_e"], datum["origin_utm_n"]

    coef, rms, n_gcp = tr.affine_from_gcps()
    to_utm = tr.make_to_utm(coef)
    cell_m = 0.5 * (math.hypot(coef[0], coef[3]) + math.hypot(coef[1], coef[4]))
    print(f"affine refit from {n_gcp} GCPs, RMS {rms:.1f} m; {cell_m:.4f} m per map pixel")

    raw, sha = tr.fetch_region(Path(args.cache))
    rgb = np.asarray(Image.open(io.BytesIO(raw)).convert("RGB"))
    print(f"region {REGION} sha256 {sha[:16]}...  {rgb.shape[1]}x{rgb.shape[0]} px")

    wash = tr.wash_mask(rgb, np)
    water = tr.channel_from(wash, SEEDS, PARAMS["close_r"], PARAMS["open_r"], 0,
                            np, ndi, speckle=PARAMS["speckle_px"])
    print(f"channel {int(water.sum())} px")

    ys, xs = np.nonzero(water)
    y0, y1, x0, x1 = int(ys.min()), int(ys.max()), int(xs.min()), int(xs.max())
    print(f"channel extent in resource px: y {y0 + REGION[1]}..{y1 + REGION[1]}, "
          f"x {x0 + REGION[0]}..{x1 + REGION[0]}")
    if y0 > 2:
        tr.die(f"the channel starts {y0} px below the splice row — it must reach the window's "
               "north edge or it does not join river.geojson")
    for label, clear_px in (("south", REGION[3] - 1 - y1), ("west", x0),
                            ("east", REGION[2] - 1 - x1)):
        if clear_px <= 2:
            tr.die(f"the channel stands {clear_px} px off the window's {label} edge: that edge "
                   "would be published as a bank, and it is not one. Widen REGION and "
                   "re-argue it.")
        print(f"   clear of the {label} edge by {clear_px} px")

    widths = tr.width_stations(water, None, np, ndi, cell_m)
    print("drafted channel width (m / ft):",
          {k: f"{v} / {v / 0.3048:.0f}" for k, v in widths.items()})

    def px_to_local(pts):
        out = []
        for px, py in pts:
            E, N = to_utm(px + REGION[0], py + REGION[1])
            out.append((round(E - o_e, 2), round(N - o_n, 2)))
        return out

    ring_px = tr.simplify_ring(tr.trace_outer(water, np), PARAMS["simplify_px"])
    ring_local = px_to_local(ring_px)
    runs = [[ring_local[i] for i in idx] for idx in split_bank_runs(ring_px, y1)]
    runs.sort(key=lambda r: -sum(math.dist(r[i], r[i + 1]) for i in range(len(r) - 1)))
    print(f"water ring {len(ring_local)} vertices; bank runs {[len(r) for r in runs]}")
    if len(runs) != 2:
        tr.die(f"expected exactly two bank runs (one per side of one reach), got {len(runs)}")
    runs.sort(key=lambda r: sum(p[0] for p in r) / len(r))
    named = list(zip(("south_branch_west_bank", "south_branch_east_bank"), runs))

    prov = {
        **PROV_STATIC,
        "iiif_region": {"image": IIIF, "x": REGION[0], "y": REGION[1],
                        "w": REGION[2], "h": REGION[3], "sha256": sha},
        "affine_rms_m": round(rms, 1),
        "map_scale_m_per_px": round(cell_m, 4),
        "simplify_tolerance_m": round(PARAMS["simplify_px"] * cell_m, 2),
    }
    prov = {k: prov[k] for k in PROV_KEYS}

    features = [{
        "type": "Feature",
        "id": WATER_ID,
        "geometry": {"type": "Polygon", "coordinates": [
            [[e + o_e, n + o_n] for e, n in ring_local]
            + [[ring_local[0][0] + o_e, ring_local[0][1] + o_n]]]},
        "properties": {
            **{k: WATER_PROPS[k] for k in ("kind", "name", "reaches",
                                           "water_surface_ft_above_datum", "confidence",
                                           "note")},
            "drafted_width_m": widths,
            "sources": WATER_PROPS["sources"],
            "provenance": prov,
        },
    }]
    for key, run in named:
        features.append({
            "type": "Feature",
            "id": key,
            "geometry": {"type": "LineString",
                         "coordinates": [[e + o_e, n + o_n] for e, n in run]},
            "properties": {
                "kind": BANK_PROPS["kind"],
                "name": BANK_LABELS[key],
                "crest_ft_above_datum": BANK_PROPS["crest_ft_above_datum"],
                "confidence": BANK_PROPS["confidence"],
                "note": BANK_PROPS["note"],
                "sources": BANK_PROPS["sources"],
            },
        })

    text = bfile.render((WATER_ID, *BANK_LABELS), features)
    if args.check:
        old = OUT.read_text() if OUT.exists() else ""
        same = old == text
        print(f"{'OK  ' if same else 'DIFF'} {OUT.relative_to(ROOT)}")
        return 0 if same else 1
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text)
    print(f"wrote {OUT.relative_to(ROOT)} ({len(text):,} bytes)")

    if args.debug:
        over = rgb.copy()
        edge = water ^ ndi.binary_erosion(water, tr.disk(2, np))
        over[water] = (0.6 * over[water] + np.array([0, 90, 240]) * 0.4).astype(np.uint8)
        over[edge] = (255, 0, 0)
        p = Path("/tmp") / "south_branch_trace_debug.png"
        Image.fromarray(over).save(p)
        print("debug overlay", p)
    return 0


if __name__ == "__main__":
    sys.exit(main())
