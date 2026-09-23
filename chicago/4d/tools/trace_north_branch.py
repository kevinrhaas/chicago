#!/usr/bin/env python3
"""Trace the North Branch north of the forks window, off Wright 1834.

The northern companion to `tools/trace_south_branch.py`, and the last of the
three windows the river needs on this sheet. `tools/trace_river.py` stops at the
forks box; Wright draws the North Branch on past it, out of the Original Town,
across Kinzie Street and up the length of Wabansia — past the water lots of
Kain's and Hight's subdivision and the blocks lettered Right and Owen — to the
line he ruled across the top of his survey.

    python3 tools/trace_north_branch.py            re-trace and write the GeoJSON
    python3 tools/trace_north_branch.py --check    re-trace and diff against committed
    python3 tools/trace_north_branch.py --debug    also write a PNG overlay
    python3 tools/trace_north_branch.py --check-properties
                                                   hold the committed file to this
                                                   file's literals: no numpy, no
                                                   network. This one IS in check.sh.

A fourth window, spliced on a declared row
------------------------------------------
Same reasoning as the South Branch, mirrored: the forks work at a LOCAL block
percentile, so widening that window would move every vertex the forks trace has
already committed and the ground is carved from those vertices. This is a
separate window whose SOUTH edge is the forks window's NORTH edge (map row
1252 — `trace_river`'s REGION starts there), which makes the splice a declared
line rather than a tolerance. `river.geojson` is not read and not rewritten.

The hue tolerance, and the wash that made it move
-------------------------------------------------
The forks settings carry north unchanged except for one: `hue_tol`, 11 -> 7.

`wash_mask` separates Wright's grey bank wash from his coloured ward washes by
how far a pixel's hue departs from the local paper's. On Wabansia's river front
that separation is the narrowest it is anywhere on the sheet. Medians over a
13-row band at map row 745, across the west bank: the green wash on the
river-front lots reads R-B 27, G-B 31; the grey bank wash beside it reads R-B 32,
G-B 19; the paper of the channel between the banks reads R-B 40, G-B 26. Green
and grey differ by one channel and by thirteen units of it, and at a tolerance of
11 the green passes as bank. It is not a small error: at `hue_tol` 8 the traced west
bank steps 131 px — 93 m — into the lots at row 800, and the polygon published
as river would have covered ground Wright drew as platted lots with lot lines
across it.

7 is the value the argument lands on and 6 is the other one that works; at 5 the
upper reach's own bank wash starts going out with the colours and the trace
breaks at row 764. The whole usable band is two wide, which is why this is
argued from the pixels above rather than tuned.

The price on the east bank, and the half of it the sheet will pay back
------------------------------------------------------------------------
The tight tolerance was paid for on the east bank, which sat a median 1.4 m
inside Wright's ink and short of it by more than 10 m on 81 of the reach's 932
rows — rows 728-779, and the last 30 rows at the splice. T-1078 read both
stretches off the scan and they are not one fault:

  * **rows 1222-1251, the splice** — a dry band ten to fifteen pixels wide cuts
    402 px of plain bank wash (tint 0-6, against a tolerance of 7) off the
    channel, and it goes out with the specks. This is T-0834's South Branch
    fault with a wider seam, and `tr.seam_wash` now puts it back: the fragment is
    reachable from the channel across bare paper and grey wash without crossing
    ink or a wash of another colour. The boundary at the splice row goes from
    32.7 m inside the ink to 6.4 m, and the stretch leaves the >10 m list.
  * **rows 728-779** — a COLOURED wash stands between the bank wash and the ink,
    17 to 19 px of it, `dark` 26-67 and `tint` 12-61. There is no path to carry
    the water across and no fragment to put back: reading it as bank would be
    exactly the error `hue_tol` 7 exists to prevent. It is left short, and what
    that colour is belongs to the tract layer (T-0792).

Measured with `tools/measure_north_branch_banks.py`, whose baseline carries the
before and after; docs/RESEARCH/north_branch_wabansia.md § 5 states the trade.

North of the survey there is no river
-------------------------------------
Wright ruled a line across the top of the sheet and washed the river up to it,
so the channel's north end is where he stopped drawing, not where the river
stopped running: the North Branch ran on to the Skokie marshes for miles past
anything on this plat. The terminal stretch is dropped for exactly the reason
`trace_south_branch.py` drops its southern one — publishing it would assert a
river end this sheet never drew — and it cannot be told by the ink, because at
this terminus there IS a line: the survey's own north boundary, drawn across the
channel.

Needs numpy, scipy, Pillow and the network. Like the other three traces the full
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
# works in. Its bottom edge is the forks window's top edge — trace_river's
# REGION starts at row 1252 — which is what makes the splice a line and not a
# tolerance. Its other three edges stand clear of the water: the traced channel's
# own extent is checked against them below, so a re-run that ever reached one
# would fail rather than publish a bank that is really a window.
SPLICE_ROW = 1252
REGION = (640, 0, 780, SPLICE_ROW)

# How near the reach's first drawn row a boundary vertex may come and still be
# published as a bank. See "North of the survey there is no river" above.
LIMIT_MARGIN_PX = 6

# One seed, in resource pixels, in open channel seven rows above the splice, so
# that the piece the seed selects is by construction the piece that joins the
# committed forks trace. It is the only hand-placed number in this trace: the
# reach comes out of it in one connected piece, so there are no waypoints up the
# length.
SEEDS = {"north_branch": (1185, 1245)}

# The forks settings, with the one change the docstring argues for.
PARAMS = dict(tr.PARAMS, hue_tol=7)

NAME = bfile.NAME
CRS = bfile.CRS
DOC = bfile.DOC

WATER_ID = "north_branch_wabansia"
WATER_PROPS = {
    "kind": "water",
    "name": "Chicago River, North Branch — the forks to the north line of Wright's survey",
    "reaches": ["north_branch"],
    "water_surface_ft_above_datum": 0.0,
    "confidence": "inferred",
    "note": "Planform traced from the Wright 1834 survey, in a window whose south edge is "
            "the forks window's north edge, so this polygon abuts river.geojson on map row "
            "1252 of the BPL master and moves no vertex of it. The water surface is flat at "
            "the datum for the same reason the forks are: the pre-reversal river had a "
            "near-zero surface gradient and stood at lake level through this reach. NO BED "
            "DEPTH IS CLAIMED HERE AT ALL. A cadastral plat gives planform and not "
            "soundings, and a traced bank must not be allowed to promote a bed — see "
            "docs/RESEARCH/north_branch_wabansia.md. The polygon's northern edge is the "
            "NORTH LINE OF THE SURVEY and not a river end: Wright washed the channel up to "
            "the line he ruled across the top of the sheet and stopped, while the North "
            "Branch itself ran on north for miles, and the two bank lines are cut short of "
            "that stretch rather than carried across it. The hue tolerance is tighter here "
            "than at the forks because the green wash on Wabansia's river-front lots would "
            "otherwise be read as bank wash; the reading is in the tool's docstring.",
    "sources": ["wright_1834"],
}

BANK_LABELS = {
    "north_branch_west_bank": "West bank of the North Branch: Wabansia's river front — the "
                              "water lots of Kain's and Hight's subdivision and the blocks "
                              "west of them",
    "north_branch_east_bank": "East bank of the North Branch: the unplatted ground east of "
                              "the river, between Kinzie's Addition and the north line of "
                              "the survey",
}
BANK_PROPS = {
    "kind": "bank",
    "crest_ft_above_datum": None,
    "confidence": "inferred",
    "note": "Bank line is the water polygon's boundary where it is neither the splice row "
            "this window's south edge stands on nor the survey's north line its other end "
            "stops on. Crest heights are not carried here: north of the modelled terrain "
            "box there is no heightfield for them to belong to yet.",
    "sources": ["wright_1834"],
}

PROV_STATIC = {
    "traced_from": "wright_1834",
    "method": "grey bank-wash segmentation of the BPL master scan, closed across the "
              "unshaded mid-channel; boundary traced and simplified; pixels transformed "
              "to EPSG:26916 by the least-squares affine refit from "
              "data/traces/gcp/wright_1834_gcps.json. The hue tolerance is tighter than the "
              "forks trace's, so that the green wash on Wabansia's river-front lots cannot "
              "be read as the grey wash of the bank beside it. Bank wash that a dry seam "
              "cut off the channel is put back where bare paper or grey wash reaches it "
              "from the channel without crossing ink or a wash of another colour "
              "(tools/trace_river.py seam_wash, T-1078)",
    "tool": "tools/trace_north_branch.py",
    "splices_onto": "data/terrain/epochs/e1834_harbor_cut/river.geojson at BPL master row 1252",
    "uncertainty_m": 20,
    "uncertainty_note": tr.PROV_STATIC["uncertainty_note"],
}
PROV_KEYS = ("traced_from", "method", "tool", "splices_onto", "iiif_region", "affine_rms_m",
             "map_scale_m_per_px", "simplify_tolerance_m", "uncertainty_m", "uncertainty_note")


def configure():
    """Point `trace_river`'s module globals at THIS window and these settings.

    The shared segmentation reads its window and its settings off `trace_river`'s
    module globals. Both this trace and `tools/measure_north_branch_banks.py`
    call this, so the measurement measures the mask the trace publishes rather
    than a second copy of it. The forks window is asserted first, so a change
    there is caught here.
    """
    if tr.REGION[1] != SPLICE_ROW:
        tr.die(f"the forks window's north edge is row {tr.REGION[1]}, not {SPLICE_ROW}: this "
               "trace's splice line moved with it and must be re-argued")
    tr.REGION = REGION
    tr.SEEDS = SEEDS
    tr.PARAMS.clear()
    tr.PARAMS.update(PARAMS)


def channel(rgb, np, ndi, quiet=False):
    """The reach's channel mask, and the ink it was read against.

    `tr.seam_wash` (T-1078) stands where `trace_river`'s own main() puts
    `bank_wash`: between the wash threshold and the channel morphology. It is the
    wider-seam reading of the same fault, and it is what carries the last thirty
    rows of this reach out to Wright's pen line instead of leaving the boundary
    32.7 m inside it at the splice. `bank_wash` itself is not used here — its
    three-pixel seam and 1.5-pixel ink terms put nothing back on this reach at
    all, which is measured in docs/RESEARCH/north_branch_wabansia.md § 5.
    """
    wash = tr.wash_mask(rgb, np)
    ink = tr.ink_mask(rgb, np, PARAMS["ink_lum"])
    dark, tint = tr.wash_terms(rgb, np)
    coloured = tr.coloured_mask(dark, tint, PARAMS)
    traced_wash, put_back = tr.seam_wash(wash, ink, coloured, SEEDS, PARAMS["close_r"],
                                         PARAMS["open_r"], 0, np, ndi, PARAMS)
    if put_back and not quiet:
        print(f"   bank wash across a dry seam: {len(put_back)} fragment(s) put back, "
              + ", ".join(f"{px} px" for px in put_back))
    water = tr.channel_from(traced_wash, SEEDS, PARAMS["close_r"], PARAMS["open_r"], 0,
                            np, ndi)
    return water, ink


def split_bank_runs(ring_px, limit_row):
    """Split the traced ring into the runs that are BANK and the runs that are not.

    `tools/trace_river.py`'s own `split_runs` drops the stretches that lie on the
    traced window's edge, and that is one of the two things to drop here: this
    window's south edge is the splice row, where the polygon meets the committed
    forks trace rather than a shore. The other is the reach's north end, which is
    not an edge of the window — the channel stops well clear of it — but the edge
    of the SURVEY. Both are reported, in map pixels, on every run.
    """
    w, h = REGION[2], REGION[3]
    m = len(ring_px)
    reason = []
    for px, py in ring_px:
        if px <= 3 or py <= 3 or px >= w - 4 or py >= h - 4:
            reason.append("window")
        elif py <= limit_row + LIMIT_MARGIN_PX:
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
    if reg.get("y", -1) + reg.get("h", -1) != SPLICE_ROW:
        bad.append(f"iiif_region bottom row {reg.get('y')} + {reg.get('h')} is not the splice "
                   f"row {SPLICE_ROW}")

    for bid, label in BANK_LABELS.items():
        b = feats.get(bid, {}).get("properties", {})
        eq(f"{bid}.name", b.get("name"), label)
        for k in ("kind", "crest_ft_above_datum", "confidence", "note", "sources"):
            eq(f"{bid}.{k}", b.get(k), BANK_PROPS[k])

    for line in bad:
        print("FAIL", line)
    if not bad:
        print(f"OK   {OUT.relative_to(ROOT)} matches tools/trace_north_branch.py literals "
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
    ap.add_argument("--cache", default=str(Path("/tmp") / "wright_1834_north_branch_region.jpg"))
    args = ap.parse_args()

    if args.check_properties:
        return check_properties()

    try:
        import numpy as np
        from PIL import Image
        from scipy import ndimage as ndi
    except ImportError as e:
        tr.die(f"SKIP: {e.name} not installed (pip install numpy scipy pillow); "
               "north branch trace not run", 0)

    configure()

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

    water, _ink = channel(rgb, np, ndi)
    print(f"channel {int(water.sum())} px")

    ys, xs = np.nonzero(water)
    y0, y1, x0, x1 = int(ys.min()), int(ys.max()), int(xs.min()), int(xs.max())
    print(f"channel extent in resource px: y {y0 + REGION[1]}..{y1 + REGION[1]}, "
          f"x {x0 + REGION[0]}..{x1 + REGION[0]}")
    if REGION[3] - 1 - y1 > 2:
        tr.die(f"the channel stops {REGION[3] - 1 - y1} px above the splice row — it must "
               "reach the window's south edge or it does not join river.geojson")
    for label, clear_px in (("north", y0), ("west", x0), ("east", REGION[2] - 1 - x1)):
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
    runs = [[ring_local[i] for i in idx] for idx in split_bank_runs(ring_px, y0)]
    runs.sort(key=lambda r: -sum(math.dist(r[i], r[i + 1]) for i in range(len(r) - 1)))
    print(f"water ring {len(ring_local)} vertices; bank runs {[len(r) for r in runs]}")
    if len(runs) != 2:
        tr.die(f"expected exactly two bank runs (one per side of one reach), got {len(runs)}")
    runs.sort(key=lambda r: sum(p[0] for p in r) / len(r))
    named = list(zip(("north_branch_west_bank", "north_branch_east_bank"), runs))

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
        p = Path("/tmp") / "north_branch_trace_debug.png"
        Image.fromarray(over).save(p)
        print("debug overlay", p)
    return 0


if __name__ == "__main__":
    sys.exit(main())
