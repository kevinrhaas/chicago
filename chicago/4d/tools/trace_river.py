#!/usr/bin/env python3
"""Trace the 1834 Chicago River channel at the forks off the Wright 1834 survey.

The river geometry in `data/terrain/epochs/e1834_harbor_cut/` is not a shape
someone drew by eye — it is the output of this computation, whose inputs are the
committed ground control (`data/traces/gcp/wright_1834_gcps.json`), the committed
datum (`data/datum.json`), and one IIIF region of the BPL master scan whose
sha256 is recorded in the output. Re-running it reproduces the GeoJSON.

    python3 tools/trace_river.py            re-trace and write the GeoJSON
    python3 tools/trace_river.py --check    re-trace and diff against what is committed
    python3 tools/trace_river.py --debug    also write a PNG overlay of the trace
    python3 tools/trace_river.py --check-properties
                                            hold the committed files to the literals this
                                            file writes: no numpy, no network, milliseconds.
                                            This one IS in tools/check.sh; see the function.

How it works, and why it is a trace rather than an inference
------------------------------------------------------------
Wright draws the river the way period plats do: a **black bank line with a grey
wash band on the water side of it**, the middle of the channel left as bare
paper. So the water is not one colour to threshold — it is the region *between*
two shaded bands. The steps:

  1. local background: the paper's luminance varies with foxing, stain and the
     scan's vignette, so "darker than paper" is measured against a block
     percentile of the neighbourhood rather than a global level;
  2. the grey wash is separated from the pink/green/blue/yellow ward washes by
     its lack of hue departure from the local paper, not by luminance;
  3. a morphological CLOSING across the unshaded mid-channel joins the two bands
     into one solid channel, and an opening sheds the thin coloured street bands
     that touch it;
  4. seeds on each reach select the channel blob, holes are filled, the boundary
     is traced and simplified;
  5. pixels go to EPSG:26916 through the same least-squares affine that fixed the
     datum, then to local ENU metres.

Needs numpy, scipy, Pillow. The full re-trace is not part of tools/check.sh —
like the datum re-derivation it is a deliberate, occasional re-run, and it
degrades to a clear skip when the dependencies or the network are missing. That
left a "do not hand-edit" file with nothing gating it at all: `hydrology.geojson`
drifted from this generator on two provenance grades and no gate could see it
for a month (T-0687). `--check-properties` closes the half that costs nothing —
every literal these files carry, checked offline — and `tools/check.sh` runs it.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import math
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "data" / "terrain" / "epochs" / "e1834_harbor_cut"

IIIF = "https://iiif.digitalcommonwealth.org/iiif/2/commonwealth:js957744g"

# The region of the BPL master scan (resource space, 4204 x 5166) that this
# trace works in: the forks pixel from the datum derivation, +/- 560 px, which
# is +/- ~390 m on the ground — comfortably outside the 640 m terrain box.
FORKS_PX = (1428, 1812)
HALF_PX = 560
REGION = (FORKS_PX[0] - HALF_PX, FORKS_PX[1] - HALF_PX, 2 * HALF_PX, 2 * HALF_PX)

# Seeds, in resource pixels, one per reach. Read off the scan; each must land in
# open channel. They pick the channel blob out of everything else the wash
# threshold catches, and they are the only hand-placed numbers in the trace.
SEEDS = {
    "north_branch": (1308, 1472),
    "main_stem": (1928, 1712),
    "south_branch": (1438, 2112),
}
# The narrow watercourse Wright draws running north out of the main stem across
# Kinzie to Michigan Street. Traced separately and as a CENTRELINE, not as a
# polygon: it is an order of magnitude narrower than the river, its wash is
# broken by the pink Kinzie ward band and by the lot lines it crosses, and the
# closing radius the river needs would swallow it whole. The corridor below is
# hand-placed on the scan, like the river seeds, and is the only thing that says
# where to look.
SLOUGH_CORRIDOR = (1590, 1320, 1740, 1625)   # resource px: x0, y0, x1, y1

PARAMS = dict(
    bg_block=64, bg_pct=88,           # local paper luminance
    hue_block=280, hue_pct=40,        # local paper hue
    dark_lo=20, dark_hi=78,           # wash is darker than paper but lighter than ink
    hue_tol=11,                       # departure from local paper hue that means "coloured"
    speckle_px=500,
    ink_lum=110,                      # below this luminance a pixel is drawn line, not wash
    bank_frag_px=160,                 # a wash fragment this big is drafted, not paper grain
    bank_seam_px=3,                   # how wide a dry seam may be and still be one wash body
    bank_ink_px=1.5,                  # ...and the fragment must abut the bank Wright inked
    close_r=40, open_r=9, fill_r=15,  # channel morphology
    slough_open_r=3, slough_min_px=120,
    simplify_px=2.5,
)


# ---------------------------------------------------------------------------
# What this generator WRITES that it does not MEASURE
# ---------------------------------------------------------------------------
# Every literal the two GeoJSON files carry lives here rather than inline in
# main(), so that `--check-properties` can hold the committed files to them
# without numpy, without the network and without re-tracing a pixel. T-0687 is
# why: `hydrology.geojson` declares itself generated, stopped matching this file
# on two provenance grades, and nothing noticed for a month, because the only
# gate that could see it (`--check`) needs both the image and the scientific
# stack and is therefore not in `tools/check.sh`.

CRS = {"type": "name", "properties": {"name": "urn:ogc:def:crs:EPSG::26916"}}

RIVER_NAME = "e1834_harbor_cut river"
RIVER_DOC = ("Water polygon and bank lines for the Chicago River forks, terrain epoch "
             "e1834_harbor_cut. Coordinates are EPSG:26916 metres (UTM 16N, NAD83). Local "
             "ENU metres used by the scene are these minus data/datum.json origin_utm_e / "
             "origin_utm_n. Generated by tools/trace_river.py — do not hand-edit.")

HYDRO_NAME = "e1834_harbor_cut hydrology"
HYDRO_DOC = ("Secondary water at the forks. Generated by tools/trace_river.py — do not "
             "hand-edit. Marsh extents live in terrain_spec.json, which is authored.")

PROV_STATIC = {
    "traced_from": "wright_1834",
    "method": "grey bank-wash segmentation of the BPL master scan, closed across the "
              "unshaded mid-channel; boundary traced and simplified; pixels transformed "
              "to EPSG:26916 by the least-squares affine refit from "
              "data/traces/gcp/wright_1834_gcps.json",
    "tool": "tools/trace_river.py",
    "uncertainty_m": 20,
    "uncertainty_note": "Both 1834 sheets carry real anisotropic paper stretch, so a global "
                        "affine cannot do better than tens of metres locally; the two 1834 "
                        "sheets disagree about the forks by 58 m. Treat every vertex as "
                        "+/-20 m. See docs/RESEARCH/datum_derivation.md.",
}
# Read off the image or off the GCP refit, so `--check-properties` takes them as
# given and only `--check` can vouch for them.
PROV_MEASURED = ("affine_rms_m", "map_scale_m_per_px", "simplify_tolerance_m")

WATER_PROPS = {
    "kind": "water",
    "name": "Chicago River — the forks",
    "reaches": ["main_stem", "north_branch", "south_branch"],
    "water_surface_ft_above_datum": 0.0,
    "confidence": "inferred",
    "note": "Planform traced from the Wright 1834 survey; the water surface is flat at "
            "the datum because the pre-reversal river had a near-zero surface gradient "
            "and stood at lake level through the whole downtown reach. Planform is as "
            "drafted on a cadastral plat, not a hydrographic survey — see "
            "drafted_width_m below and docs/RESEARCH/terrain_forks.md.",
    "sources": ["wright_1834", "wikipedia_chicago_river"],
}

BANK_LABELS = {
    "north_division_shore": "North Division shore: east bank of the North Branch and north "
                            "bank of the main stem",
    "south_division_shore": "South Division shore: south bank of the main stem and east bank "
                            "of the South Branch",
    "west_division_shore": "West Division shore at Wolf Point: west bank of the North Branch "
                           "and west bank of the South Branch",
}
BANK_PROPS = {
    "kind": "bank",
    "crest_ft_above_datum": None,
    "confidence": "inferred",
    "note": "Bank line is the water polygon's boundary where it is not the edge of "
            "the traced window. Crest heights are carried in the heightfield spec, "
            "not here, because they come from narrative feet and not from the map.",
    "sources": ["wright_1834"],
}

# `{frags}` is the one measured number in this sentence; --check-properties
# matches the committed note as a template so the prose is gated and the count
# is not.
SLOUGH_NOTE = (
    "Wright 1834 draws a narrow winding watercourse running north out of "
    "the main stem, across Kinzie Street, ending at Michigan Street. Its "
    "existence and course are documented by the map; this is a CENTRELINE "
    "because the bank wash survives only in "
    "{frags} fragments — the pink Kinzie ward band and the lot "
    "lines it crosses erase the rest — so a traced boundary would be a "
    "fiction. The 1830 Thompson plat draws ONE watercourse, not three, "
    "and draws it across North Division block 6 — the same block this "
    "centreline crosses, so the plat corroborates it at block resolution "
    "and at no finer (T-0452, docs/RESEARCH/thompson_plat_sloughs.md). The "
    "\"three sloughs\" count is Conley/Stelzer 1933's, never Thompson's. "
    "THE TWO GRADES BELOW, RULED ON THE EVIDENCE BY T-0687. The width is "
    "MEASURED: it is twice the interior distance transform of the surviving "
    "wash fragments, read off this same scan at 0.7115 m per map pixel, so "
    "it is reasoned from evidence about this particular watercourse and is "
    "graded inferred — the same rung as the river polygon traced from the "
    "same wash, which it would be incoherent to sit below. What it measures "
    "is the width AS DRAFTED on a cadastral plat, not a sounded channel. "
    "The depth is INVENTED: no source gives a figure for this watercourse "
    "or any other on the town site, so a foot is assumed — the shallowest "
    "value that still reads as standing water for something Wright draws as "
    "a continuous channel rather than as marsh, and shallow enough not to "
    "assert a crossing problem nobody recorded. It is graded reconstructed, "
    "this project's bottom tier and its word for what the next sentence "
    "calls conjectural. Depth is conjectural: no source gives one."
)
SLOUGH_PROPS = {
    "kind": "watercourse_centreline",
    "name": "Unnamed slough, north side",
    "confidence": "attested",
    "width_confidence": "inferred",
    "assumed_depth_ft_below_datum": 1.0,
    "depth_confidence": "reconstructed",
    "sources": ["wright_1834", "thompson_plat_1830"],
}

def die(msg: str, code: int = 2):
    print(msg)
    raise SystemExit(code)


# ---------------------------------------------------------------------------
# raster
# ---------------------------------------------------------------------------

def fetch_region(cache: Path):
    x, y, w, h = REGION
    url = f"{IIIF}/{x},{y},{w},{h}/full/0/default.jpg"
    if cache.exists():
        raw = cache.read_bytes()
    else:
        print(f"fetching {url}")
        with urllib.request.urlopen(url, timeout=180) as r:  # noqa: S310
            raw = r.read()
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_bytes(raw)
    return raw, hashlib.sha256(raw).hexdigest()


# ---------------------------------------------------------------------------
# segmentation
# ---------------------------------------------------------------------------

def block_pct(arr, block, q, np):
    h, w = arr.shape
    bh, bw = (h + block - 1) // block, (w + block - 1) // block
    pad = np.full((bh * block, bw * block), np.nan, np.float32)
    pad[:h, :w] = arr
    t = pad.reshape(bh, block, bw, block).transpose(0, 2, 1, 3).reshape(bh, bw, -1)
    return np.nanpercentile(t, q, axis=2).astype(np.float32)


def upsample(small, shape, np):
    bh, bw = small.shape
    h, w = shape
    yi = np.clip(np.linspace(-0.5, bh - 0.5, h), 0, bh - 1)
    xi = np.clip(np.linspace(-0.5, bw - 0.5, w), 0, bw - 1)
    y0 = np.floor(yi).astype(int); y1 = np.minimum(y0 + 1, bh - 1); fy = (yi - y0)[:, None]
    x0 = np.floor(xi).astype(int); x1 = np.minimum(x0 + 1, bw - 1); fx = (xi - x0)[None, :]
    return ((small[y0][:, x0] * (1 - fx) + small[y0][:, x1] * fx) * (1 - fy)
            + (small[y1][:, x0] * (1 - fx) + small[y1][:, x1] * fx) * fy)


def disk(r, np):
    y, x = np.ogrid[-r:r + 1, -r:r + 1]
    return x * x + y * y <= r * r


def wash_terms(rgb, np):
    """The two fields every wash question on this sheet is asked of: how much
    DARKER than the local paper a pixel is, and how far its HUE departs from the
    local paper's. Extracted from `wash_mask` so that `seam_wash` can ask the
    complementary question — which pixels are a wash of ANOTHER colour — off the
    same two numbers, rather than re-deriving them and drifting."""
    a = rgb.astype(np.float32)
    R, G, B = a[..., 0], a[..., 1], a[..., 2]
    L = 0.299 * R + 0.587 * G + 0.114 * B
    shape = L.shape
    bg = upsample(block_pct(L, PARAMS["bg_block"], PARAMS["bg_pct"], np), shape, np)
    dark = bg - L
    rb, gb = R - B, G - B
    rb0 = upsample(block_pct(rb, PARAMS["hue_block"], PARAMS["hue_pct"], np), shape, np)
    gb0 = upsample(block_pct(gb, PARAMS["hue_block"], PARAMS["hue_pct"], np), shape, np)
    tint = np.abs(rb - rb0) + np.maximum(np.abs(gb - gb0) - 4, 0)
    return dark, tint


def wash_mask(rgb, np):
    """Pixels carrying the grey bank wash: darker than the local paper, and with
    no hue departure from it (which is what separates the bank shading from the
    pink/green/blue/yellow ward washes)."""
    dark, tint = wash_terms(rgb, np)
    return (dark > PARAMS["dark_lo"]) & (dark < PARAMS["dark_hi"]) & (tint < PARAMS["hue_tol"])


def coloured_mask(dark, tint, params):
    """A wash of ANOTHER colour: in the same darkness band `wash_mask` calls
    wash, and outside its hue tolerance. The exact complement of `wash_mask`
    inside that band — paper is lighter than `dark_lo`, ink is darker than
    `dark_hi`, and what is left is either the grey bank shading or one of
    Wright's ward and tract colours."""
    return (dark > params["dark_lo"]) & (dark < params["dark_hi"]) & (tint >= params["hue_tol"])


def ink_mask(rgb, np, lum_lo):
    """Wright's drawn line: darker than any wash he laid beside it. The same
    luminance threshold `tools/measure_water_outliers.py --vs-ink` measures
    against, so the trace and the measurement mean the same thing by "the ink"."""
    a = rgb.astype(np.float32)
    return (0.299 * a[..., 0] + 0.587 * a[..., 1] + 0.114 * a[..., 2]) < lum_lo


def bank_wash(wash, ink, seeds, close_r, open_r, fill_r, np, ndi, params):
    """Speckle-filter the wash, then put back the fragments a dry seam cut off
    the bank — the rule that keeps the boundary on the ink rather than the seam.

    The speckle floor exists so that stray tinted paper is not dragged into the
    channel by the 40 px close. On the South Branch's east bank it also throws
    away drafted bank wash. Rows 662-690 of the region carry a dry seam three to
    six pixels wide *inside* the wash, running parallel to the bank a little west
    of it; the strip of wash east of that seam is 205 px, well under the 500 px
    floor, and goes out with the specks. The closing is then left with nothing to
    bridge to, so the traced boundary walks the seam instead of the bank and
    stands 11.9, 12.4 and 14.7 m west of the ink where the other 66 bank vertices
    in the epoch sit a median 0.70 m from it
    (docs/RESEARCH/south_branch_spike_1834.md).

    A dropped fragment is drafted bank wash rather than a speck when all three
    hold, and the third is why this reads the ink as well as the wash:

      * it is at least `bank_frag_px` — big enough to have been laid with a brush
        rather than to be paper grain or a scan artefact;
      * it lies within `bank_seam_px` of the channel the surviving wash already
        gives, so it is across a seam from it and not somewhere else on the sheet;
      * it comes within `bank_ink_px` of the inked bank. Tint scatters along every
        traced edge; wash that abuts the line Wright drew is the bank's own.

    Returns the wash to trace from, and the fragments it put back.
    """
    lab, n = ndi.label(wash)
    sizes = ndi.sum_labels(np.ones_like(lab, np.float32), lab, np.arange(1, n + 1))
    kept = np.isin(lab, 1 + np.flatnonzero(sizes >= params["speckle_px"]))
    small = 1 + np.flatnonzero(sizes < params["speckle_px"])
    if not len(small):
        return kept, []
    # the channel the surviving wash gives on its own, which is what the
    # fragments are measured against
    provisional = channel_from(kept, seeds, close_r, open_r, fill_r, np, ndi)
    to_channel = ndi.minimum(ndi.distance_transform_edt(~provisional), lab, small)
    to_ink = ndi.minimum(ndi.distance_transform_edt(~ink), lab, small)
    sel = small[(sizes[small - 1] >= params["bank_frag_px"])
                & (np.asarray(to_channel) <= params["bank_seam_px"])
                & (np.asarray(to_ink) <= params["bank_ink_px"])]
    if not len(sel):
        return kept, []
    put_back = [(int(sizes[i - 1]), float(to_channel[list(small).index(i)])) for i in sel]
    return kept | np.isin(lab, sel), put_back


def seam_wash(wash, ink, coloured, seeds, close_r, open_r, fill_r, np, ndi, params):
    """`bank_wash` for a seam WIDER than a brush stroke: put back the wash a dry
    band cut off the bank, when nothing Wright drew stands between the two.

    T-1078. `bank_wash` decides a dropped fragment on three numbers, and two of
    them are the width of the South Branch's seam: the fragment must lie within
    `bank_seam_px` (3) of the surviving channel and come within `bank_ink_px`
    (1.5) of the inked bank. On the North Branch north of the Addition the same
    fault appears with a seam ten to fifteen pixels wide, and Wright's wash there
    stops a few pixels short of his own pen line, so BOTH of those terms refuse a
    402-px strip of unmistakable bank wash (tint 0-6 against a tolerance of 7)
    standing between the channel and the ink over the reach's last thirty rows —
    and the traced boundary falls 32.7 m inside the ink at the splice row.

    Widening the two tolerances would be a knob. This asks the question they were
    standing in for, and asks it of the scan:

      **is there a path from the fragment to the channel that crosses nothing
      Wright drew?**

    A path may run over bare paper and over grey bank wash. It may NOT cross ink,
    and it may NOT cross a wash of another colour — which is what makes the rule
    safe in the one direction this reach cannot afford to be wrong in. Wabansia's
    river-front lots are washed green; a fragment out in the lots is unreachable
    because the green stands between it and the water, so this rule cannot do
    what `hue_tol` 11 did and read platted ground as river. It is also why the
    reach's OTHER short stretch (rows 728-779) is left alone rather than closed:
    a coloured wash stands between the bank wash and the ink there, so no path
    exists, and what that colour is belongs to the tract layer (T-0792).

    The reach is bounded by `close_r` — the radius the channel morphology already
    bridges across unwashed mid-channel — so the rule introduces no tolerance of
    its own. It is not a load-bearing bound: the same three fragments are put
    back, and the same 1,155 px of wash, at every radius from 10 to 40 px.

    Returns the wash to trace from, and the fragments it put back.
    """
    lab, n = ndi.label(wash)
    sizes = ndi.sum_labels(np.ones_like(lab, np.float32), lab, np.arange(1, n + 1))
    kept = np.isin(lab, 1 + np.flatnonzero(sizes >= params["speckle_px"]))
    small = 1 + np.flatnonzero(sizes < params["speckle_px"])
    if not len(small):
        return kept, []
    # the channel the surviving wash gives on its own, which is what the
    # fragments are measured against — the same provisional mask `bank_wash` uses
    provisional = channel_from(kept, seeds, close_r, open_r, fill_r, np, ndi)
    undrawn = ~ink & ~coloured
    near = ndi.binary_dilation(provisional, disk(close_r, np))
    reach = ndi.binary_propagation(provisional, mask=(provisional | undrawn) & near)
    to_reach = np.asarray(ndi.minimum(ndi.distance_transform_edt(~reach), lab, small))
    sel = small[(sizes[small - 1] >= params["bank_frag_px"]) & (to_reach <= 1)]
    if not len(sel):
        return kept, []
    put_back = sorted((int(sizes[i - 1]) for i in sel), reverse=True)
    return kept | np.isin(lab, sel), put_back


def _erode(m, r, np, ndi):
    """Erosion that treats everything outside the window as solid. scipy's
    default (`border_value=0`) eats a band of radius r off every edge, which
    would have pulled the traced channel 40 px clear of the window and made the
    river look as though it ended in mid-air."""
    return ndi.binary_erosion(m, disk(r, np), border_value=1)


def channel_from(wash, seeds, close_r, open_r, fill_r, np, ndi, speckle=None):
    lab, n = ndi.label(wash)
    if speckle:
        sizes = ndi.sum_labels(np.ones_like(lab, np.float32), lab, np.arange(1, n + 1))
        wash = np.isin(lab, 1 + np.flatnonzero(sizes >= speckle))
    m = _erode(ndi.binary_dilation(wash, disk(close_r, np)), close_r, np, ndi)
    if open_r:
        m = ndi.binary_dilation(_erode(m, open_r, np, ndi), disk(open_r, np))
    lab2, _ = ndi.label(m)
    keep = set()
    for name, (sx, sy) in seeds.items():
        x, y = sx - REGION[0], sy - REGION[1]
        v = int(lab2[y, x])
        if v == 0:                                  # seed fell on a bank line
            ys, xs = np.nonzero(m)
            i = int(((xs - x) ** 2 + (ys - y) ** 2).argmin())
            v = int(lab2[ys[i], xs[i]])
            print(f"   seed {name} landed off-channel; snapped {math.hypot(xs[i]-x, ys[i]-y):.0f} px")
        keep.add(v)
    out = np.isin(lab2, sorted(keep))
    if fill_r:                                      # close the fork's open middle
        out = _erode(ndi.binary_fill_holes(ndi.binary_dilation(out, disk(fill_r, np))),
                     fill_r, np, ndi)
    return ndi.binary_fill_holes(out)


# ---------------------------------------------------------------------------
# vectorising
# ---------------------------------------------------------------------------

MOORE = [(1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1)]


def slough_centreline(wash, river, np, ndi, cell_m):
    """The north-side slough, as a centreline plus a measured width.

    Its wash survives only in five fragments — the pink Kinzie ward band and the
    lot lines it crosses erase the rest — so a polygon trace would be a fiction
    dressed up as a boundary. What the map does support is where the watercourse
    ran and how wide it was drawn, so that is what comes out: a per-row centre of
    the surviving wash inside a hand-placed corridor, gaps filled by linear
    interpolation between the fragments, and the drafted width read off the
    interior distance transform of the fragments themselves.
    """
    x0, y0, x1, y1 = SLOUGH_CORRIDOR
    free = wash & ~ndi.binary_dilation(river, disk(2, np))
    corr = np.zeros_like(free)
    corr[y0 - REGION[1]:y1 - REGION[1], x0 - REGION[0]:x1 - REGION[0]] = True
    base = ndi.binary_opening(free & corr, disk(PARAMS["slough_open_r"], np))
    lab, n = ndi.label(base)
    if not n:
        return [], 0.0, 0
    sizes = ndi.sum_labels(np.ones_like(lab, np.float32), lab, np.arange(1, n + 1))
    base = np.isin(lab, 1 + np.flatnonzero(sizes >= PARAMS["slough_min_px"]))
    frags = int(np.count_nonzero(sizes >= PARAMS["slough_min_px"]))

    din = ndi.distance_transform_edt(base)
    rows, centres = [], []
    for r in range(base.shape[0]):
        xs = np.flatnonzero(base[r])
        if xs.size:
            rows.append(r)
            centres.append(0.5 * (xs.min() + xs.max()))
    if len(rows) < 4:
        return [], 0.0, frags
    lo, hi = rows[0], rows[-1]
    grid = np.arange(lo, hi + 1)
    cx = np.interp(grid, rows, centres)
    k = 15                                          # smooth the interpolated joins
    pad = np.pad(cx, k, mode="edge")
    cx = np.convolve(pad, np.ones(2 * k + 1) / (2 * k + 1), mode="valid")

    step = max(1, len(grid) // 40)
    line = [(float(cx[i]), float(grid[i])) for i in range(0, len(grid), step)]
    line.append((float(cx[-1]), float(grid[-1])))
    width = float(np.percentile(din[base], 88)) * 2 * cell_m
    return line, round(width, 1), frags


def trace_outer(mask, np):
    """Moore-neighbour boundary trace of the largest component's outer ring.
    Returns pixel coordinates (x, y) in mask space, closed, counter-clockwise in
    image coordinates."""
    ys, xs = np.nonzero(mask)
    if not len(ys):
        return []
    i = int(np.lexsort((xs, ys))[0])
    start = (int(xs[i]), int(ys[i]))
    h, w = mask.shape

    def solid(p):
        x, y = p
        return 0 <= x < w and 0 <= y < h and mask[y, x]

    out = [start]
    b = 7                                   # came from the west
    cur = start
    for _ in range(8 * int(mask.sum()) + 16):
        found = False
        for k in range(1, 9):
            d = (b + k) % 8
            nb = (cur[0] + MOORE[d][0], cur[1] + MOORE[d][1])
            if solid(nb):
                b = (d + 5) % 8             # backtrack points at where we came from
                cur = nb
                found = True
                break
        if not found:
            break
        if cur == start and len(out) > 2:
            break
        out.append(cur)
    return out


def rdp(pts, eps):
    """Ramer-Douglas-Peucker on an open polyline."""
    if len(pts) < 3:
        return list(pts)
    a, b = pts[0], pts[-1]
    ax, ay = a; bx, by = b
    dx, dy = bx - ax, by - ay
    n = math.hypot(dx, dy)
    worst, wi = -1.0, 0
    for i in range(1, len(pts) - 1):
        px, py = pts[i]
        if n < 1e-9:
            dist = math.hypot(px - ax, py - ay)
        else:
            dist = abs(dy * px - dx * py + bx * ay - by * ax) / n
        if dist > worst:
            worst, wi = dist, i
    if worst <= eps:
        return [a, b]
    return rdp(pts[:wi + 1], eps)[:-1] + rdp(pts[wi:], eps)


def simplify_ring(ring, eps):
    if len(ring) < 4:
        return ring
    half = len(ring) // 2
    a = rdp(ring[:half + 1], eps)
    b = rdp(ring[half:] + [ring[0]], eps)
    return a[:-1] + b[:-1]


# ---------------------------------------------------------------------------
# georeferencing
# ---------------------------------------------------------------------------

def affine_from_gcps():
    """Refit the pixel -> EPSG:26916 affine from the committed ground control,
    exactly as tools/rederive_datum.py does, so the river and the datum origin
    can never come from different transforms."""
    sys.path.insert(0, str(ROOT / "tools"))
    from rederive_datum import fit_from_traces  # noqa: PLC0415
    try:
        from pyproj import Transformer  # noqa: PLC0415
    except ImportError:
        die("SKIP: pyproj not installed (pip install pyproj); river trace not run", 0)
    t = Transformer.from_crs(4326, 26916, always_xy=True)
    coef, rms, rows = fit_from_traces("data/traces/gcp/wright_1834_gcps.json", t)
    return coef, rms, len(rows)


def make_to_utm(coef):
    a, b, c, d, e, f = coef

    def to_utm(px, py):
        return (a * px + b * py + c, d * px + e * py + f)
    return to_utm


# ---------------------------------------------------------------------------
# reach labelling and measurement
# ---------------------------------------------------------------------------

def split_runs(ring_px, margin=3):
    """Split the traced ring into the runs that are real bank and the runs that
    are only the edge of the traced window. Done in PIXEL space, where the window
    is exactly axis-aligned; the local ENU frame is rotated ~1.2 deg off it, so
    the same test there would miss.

    Returns index runs into `ring_px`.
    """
    w, h = REGION[2], REGION[3]
    on_edge = [px <= margin or py <= margin or px >= w - 1 - margin or py >= h - 1 - margin
               for px, py in ring_px]
    m = len(ring_px)
    if not any(on_edge):
        return [list(range(m))]
    start = next(i for i in range(m) if on_edge[i])
    runs, cur = [], []
    for k in range(m + 1):
        i = (start + k) % m
        if on_edge[i]:
            if len(cur) > 2:
                # carry the flanking window-edge vertices into the run, so a bank
                # line reaches the edge of the trace instead of stopping at the
                # last vertex RDP happened to keep
                runs.append([(cur[0] - 1) % m] + cur + [i])
            cur = []
        else:
            cur.append(i)
    return runs


def width_stations(mask, to_local, np, ndi, cell_m):
    """Channel width along each reach: 2 x the interior distance transform read
    at its local ridge, sampled at a few points per reach."""
    din = ndi.distance_transform_edt(mask)
    out = {}
    for name, (sx, sy) in SEEDS.items():
        x, y = sx - REGION[0], sy - REGION[1]
        # walk a small window and take the largest interior distance near the seed
        win = din[max(0, y - 40):y + 41, max(0, x - 40):x + 41]
        out[name] = round(float(win.max()) * 2 * cell_m, 1)
    return out


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def check_properties() -> int:
    """Hold the committed GeoJSON to the literals above — offline, in milliseconds.

    `--check` is the real gate: it re-traces the scan and reproduces both files
    byte for byte. It cannot live in `tools/check.sh`, and the cost of putting it
    there is the reason, not an oversight — it needs numpy, scipy and Pillow,
    which the agent sandbox does not carry, and it fetches a 1,120 px IIIF region
    from Boston Public Library over the network. A per-commit gate that installs
    a scientific stack and reaches the internet is a gate that gets skipped, and
    a skipped gate is what let T-0687 happen.

    So the half that needs neither is gated instead. Everything this file writes
    divides cleanly in two: MEASURED values, which come out of the image or the
    GCP refit, and LITERALS, which are typed here. The drift T-0687 found was
    entirely in the literals — two provenance grades — and so is every drift a
    hand-edit of a "do not hand-edit" file can plausibly introduce, because
    hand-editing coordinates is not a thing anybody does by accident. This
    compares every literal and takes the measured numbers as given.

    What it therefore does NOT catch, said plainly so nobody trusts it too far:
    a coordinate, a `drafted_width_m`, an affine RMS or the region sha256 that
    stops matching the scan. Only `--check` can see those, and it stays a
    deliberate, occasional re-run.
    """
    problems: list[str] = []

    def load(name: str):
        path = OUT_DIR / name
        if not path.exists():
            problems.append(f"{path.relative_to(ROOT)} is missing")
            return None
        try:
            return json.loads(path.read_text())
        except json.JSONDecodeError as e:
            problems.append(f"{path.relative_to(ROOT)} is not loadable: {e}")
            return None

    def same(where: str, key: str, got, want):
        if got != want:
            problems.append(f"{where}: {key} is {got!r}, the generator writes {want!r}")

    def envelope(doc, name: str, want_name: str, want_doc: str):
        same(name, "name", doc.get("name"), want_name)
        same(name, "crs", doc.get("crs"), CRS)
        same(name, "_doc", doc.get("_doc"), want_doc)

    def provenance(where: str, prov):
        if not isinstance(prov, dict):
            problems.append(f"{where}: provenance is not an object")
            return
        for key, want in PROV_STATIC.items():
            same(where, f"provenance.{key}", prov.get(key), want)
        region = prov.get("iiif_region") or {}
        for key, want in (("image", IIIF), ("x", REGION[0]), ("y", REGION[1]),
                          ("w", REGION[2]), ("h", REGION[3])):
            same(where, f"provenance.iiif_region.{key}", region.get(key), want)
        for key in PROV_MEASURED:
            if key not in prov:
                problems.append(f"{where}: provenance.{key} is missing")

    river = load("river.geojson")
    if river is not None:
        envelope(river, "river.geojson", RIVER_NAME, RIVER_DOC)
        feats = {f.get("id"): f for f in river.get("features", [])}
        want_ids = {"chicago_river_forks", *BANK_LABELS}
        if set(feats) != want_ids:
            problems.append(f"river.geojson: features are {sorted(feats)}, "
                            f"the generator writes {sorted(want_ids)}")
        water = feats.get("chicago_river_forks")
        if water:
            props = water.get("properties") or {}
            for key, want in WATER_PROPS.items():
                same("river.geojson/chicago_river_forks", key, props.get(key), want)
            if "drafted_width_m" not in props:
                problems.append("river.geojson/chicago_river_forks: drafted_width_m is missing")
            provenance("river.geojson/chicago_river_forks", props.get("provenance"))
        for fid, label in BANK_LABELS.items():
            bank = feats.get(fid)
            if not bank:
                continue
            props = bank.get("properties") or {}
            where = f"river.geojson/{fid}"
            same(where, "name", props.get("name"), label)
            for key, want in BANK_PROPS.items():
                same(where, key, props.get(key), want)

    hydro = load("hydrology.geojson")
    if hydro is not None:
        envelope(hydro, "hydrology.geojson", HYDRO_NAME, HYDRO_DOC)
        feats = {f.get("id"): f for f in hydro.get("features", [])}
        if set(feats) != {"north_side_slough"}:
            problems.append(f"hydrology.geojson: features are {sorted(feats)}, "
                            f"the generator writes ['north_side_slough']")
        slough = feats.get("north_side_slough")
        if slough:
            props = slough.get("properties") or {}
            where = "hydrology.geojson/north_side_slough"
            for key, want in SLOUGH_PROPS.items():
                same(where, key, props.get(key), want)
            # The note carries one measured number; gate the prose around it.
            pattern = re.escape(SLOUGH_NOTE).replace(re.escape("{frags}"), r"\d+")
            if not re.fullmatch(pattern, props.get("note") or ""):
                problems.append(f"{where}: note is not the sentence the generator writes "
                                f"(only the wash-fragment count may differ)")
            if "drafted_width_m" not in props:
                problems.append(f"{where}: drafted_width_m is missing")
            provenance(where, props.get("provenance"))

    for msg in problems:
        print(f"DRIFT {msg}")
    if problems:
        print(f"\n{len(problems)} drift(s). These files say 'Generated by tools/trace_river.py "
              f"— do not hand-edit'. Change the generator and re-run it, do not edit the JSON:")
        print("  python3 tools/trace_river.py          # needs numpy scipy pillow + network")
        return 1
    print("OK   both files carry the literals tools/trace_river.py writes "
          "(measured values need --check)")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="diff against the committed GeoJSON")
    ap.add_argument("--check-properties", action="store_true",
                    help="hold the committed GeoJSON to this file's literals — no numpy, "
                         "no network; this is the half tools/check.sh runs")
    ap.add_argument("--debug", action="store_true", help="write a PNG overlay of the trace")
    ap.add_argument("--cache", default=str(Path("/tmp") / "wright_1834_forks_region.jpg"))
    args = ap.parse_args()

    if args.check_properties:
        return check_properties()

    try:
        import numpy as np
        from PIL import Image
        from scipy import ndimage as ndi
    except ImportError as e:
        die(f"SKIP: {e.name} not installed (pip install numpy scipy pillow); river trace not run", 0)

    datum = json.loads((ROOT / "data" / "datum.json").read_text())
    if not datum.get("verified"):
        die("REFUSING: data/datum.json is not verified.")
    o_e, o_n = datum["origin_utm_e"], datum["origin_utm_n"]

    coef, rms, n_gcp = affine_from_gcps()
    to_utm = make_to_utm(coef)
    scale_x = math.hypot(coef[0], coef[3])
    scale_y = math.hypot(coef[1], coef[4])
    cell_m = 0.5 * (scale_x + scale_y)
    print(f"affine refit from {n_gcp} GCPs, RMS {rms:.1f} m; {cell_m:.4f} m per map pixel")

    raw, sha = fetch_region(Path(args.cache))
    rgb = np.asarray(Image.open(io.BytesIO(raw)).convert("RGB"))
    print(f"region {REGION} sha256 {sha[:16]}...  {rgb.shape[1]}x{rgb.shape[0]} px")

    wash = wash_mask(rgb, np)
    ink = ink_mask(rgb, np, PARAMS["ink_lum"])
    traced_wash, put_back = bank_wash(wash, ink, SEEDS, PARAMS["close_r"], PARAMS["open_r"],
                                      PARAMS["fill_r"], np, ndi, PARAMS)
    if put_back:
        print(f"   bank wash across a seam: {len(put_back)} fragment(s) put back, "
              + ", ".join(f"{px} px at {d:.0f} px" for px, d in sorted(put_back, reverse=True)))
    river = channel_from(traced_wash, SEEDS, PARAMS["close_r"], PARAMS["open_r"],
                         PARAMS["fill_r"], np, ndi)
    slough_px, slough_w, slough_frags = slough_centreline(wash, river, np, ndi, cell_m)
    print(f"channel {int(river.sum())} px; slough centreline {len(slough_px)} pts from "
          f"{slough_frags} wash fragments, drafted width {slough_w} m")

    widths = width_stations(river, None, np, ndi, cell_m)
    print("drafted channel width (m / ft):",
          {k: f"{v} / {v/0.3048:.0f}" for k, v in widths.items()})

    def px_to_local(pts):
        out = []
        for px, py in pts:
            E, N = to_utm(px + REGION[0], py + REGION[1])
            out.append((round(E - o_e, 2), round(N - o_n, 2)))
        return out

    water_px = simplify_ring(trace_outer(river, np), PARAMS["simplify_px"])
    water_local = px_to_local(water_px)
    slough_local = px_to_local(slough_px)
    print(f"water ring {len(water_local)} vertices, slough line {len(slough_local)}")

    # Bank runs: split the ring where it leaves the traced window, and name each
    # run by the division whose shore it is. Ordering is stable because the ring
    # is traced from a fixed start and the window is fixed.
    runs = [[water_local[i] for i in idx] for idx in split_runs(water_px)]
    runs.sort(key=lambda r: -sum(math.dist(r[i], r[i + 1]) for i in range(len(r) - 1)))
    print(f"bank runs: {[len(r) for r in runs]}")
    named = []
    for r in runs:
        cen_e = sum(p[0] for p in r) / len(r)
        cen_n = sum(p[1] for p in r) / len(r)
        if cen_n > 0 and cen_e > -40:
            key = "north_division_shore"
        elif cen_e > 0:
            key = "south_division_shore"
        else:
            key = "west_division_shore"
        named.append((key, BANK_LABELS[key], r))

    prov = {
        **PROV_STATIC,
        "iiif_region": {"image": IIIF, "x": REGION[0], "y": REGION[1],
                        "w": REGION[2], "h": REGION[3], "sha256": sha},
        "affine_rms_m": round(rms, 1),
        "map_scale_m_per_px": round(cell_m, 4),
        "simplify_tolerance_m": round(PARAMS["simplify_px"] * cell_m, 2),
    }
    # PROV_STATIC's prose sits after the measured numbers in the committed file;
    # keep the emitted key order fixed so a re-run is byte-identical.
    prov = {k: prov[k] for k in ("traced_from", "method", "tool", "iiif_region",
                                 "affine_rms_m", "map_scale_m_per_px",
                                 "simplify_tolerance_m", "uncertainty_m",
                                 "uncertainty_note")}

    features = [{
        "type": "Feature",
        "id": "chicago_river_forks",
        "geometry": {"type": "Polygon", "coordinates": [
            [[e + o_e, n + o_n] for e, n in water_local]
            + [[water_local[0][0] + o_e, water_local[0][1] + o_n]]]},
        "properties": {
            **{k: WATER_PROPS[k] for k in ("kind", "name", "reaches",
                                           "water_surface_ft_above_datum", "confidence",
                                           "note")},
            "drafted_width_m": widths,
            "sources": WATER_PROPS["sources"],
            "provenance": prov,
        },
    }]
    for key, label, run in named:
        features.append({
            "type": "Feature",
            "id": key,
            "geometry": {"type": "LineString",
                         "coordinates": [[e + o_e, n + o_n] for e, n in run]},
            "properties": {
                "kind": BANK_PROPS["kind"],
                "name": label,
                "crest_ft_above_datum": BANK_PROPS["crest_ft_above_datum"],
                "confidence": BANK_PROPS["confidence"],
                "note": BANK_PROPS["note"],
                "sources": BANK_PROPS["sources"],
            },
        })

    river_fc = {
        "type": "FeatureCollection",
        "name": RIVER_NAME,
        "crs": CRS,
        "_doc": RIVER_DOC,
        "features": features,
    }

    hydro_fc = {
        "type": "FeatureCollection",
        "name": HYDRO_NAME,
        "crs": CRS,
        "_doc": HYDRO_DOC,
        "features": [{
            "type": "Feature",
            "id": "north_side_slough",
            "geometry": {"type": "LineString",
                         "coordinates": [[e + o_e, n + o_n] for e, n in slough_local]},
            "properties": {
                "kind": SLOUGH_PROPS["kind"],
                "name": SLOUGH_PROPS["name"],
                "confidence": SLOUGH_PROPS["confidence"],
                "note": SLOUGH_NOTE.format(frags=slough_frags),
                "drafted_width_m": slough_w,
                "width_confidence": SLOUGH_PROPS["width_confidence"],
                "assumed_depth_ft_below_datum": SLOUGH_PROPS["assumed_depth_ft_below_datum"],
                "depth_confidence": SLOUGH_PROPS["depth_confidence"],
                "sources": SLOUGH_PROPS["sources"],
                "provenance": prov,
            },
        }],
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    wrote = []
    for path, doc in ((OUT_DIR / "river.geojson", river_fc),
                      (OUT_DIR / "hydrology.geojson", hydro_fc)):
        text = json.dumps(doc, indent=1) + "\n"
        if args.check:
            old = path.read_text() if path.exists() else ""
            same = old == text
            print(f"{'OK  ' if same else 'DIFF'} {path.relative_to(ROOT)}")
            if not same:
                return 1
        else:
            path.write_text(text)
            wrote.append(f"{path.relative_to(ROOT)} ({len(text):,} bytes)")
    for w in wrote:
        print("wrote", w)

    if args.debug:
        over = rgb.copy()
        edge = river ^ ndi.binary_erosion(river, disk(2, np))
        over[river] = (0.6 * over[river] + np.array([0, 90, 240]) * 0.4).astype(np.uint8)
        for px, py in slough_px:
            over[int(py) - 3:int(py) + 4, int(px) - 3:int(px) + 4] = (255, 200, 0)
        over[edge] = (255, 0, 0)
        p = Path("/tmp") / "river_trace_debug.png"
        Image.fromarray(over).save(p)
        print("debug overlay", p)
    return 0


if __name__ == "__main__":
    sys.exit(main())
