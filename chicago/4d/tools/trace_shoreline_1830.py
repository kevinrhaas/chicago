#!/usr/bin/env python3
"""Trace the PRE-CUT mouth of the Chicago River off the Harrison 1830 harbour plan.

WHAT THIS FILE IS FOR, SINCE T-1286. It is a SECOND, INDEPENDENT reading of the
landform the shoreline state `shore_1812_pre_cut` carries, and it does not carry that
state. The owner ruled on 2026-09-17 that Wright 1834 is accurate enough to carry the
pre-cut shore, so the state is DERIVED by `tools/derive_shore_1812.py` and this trace
was never adopted (the PR that wrote it, custom#1398, was closed). The reason it could
not carry the line is in `data/sources/harrison_1830_river_mouth.json`: tier 2 (what
is readable is Andreas's 1884 re-engraving), memory additions admitted on its face, no
scale bar, and the shoreline is not among what it supplies. What it IS, is the only
pre-cut sheet held, read by a different method — so `tools/measure_shore_1812_harrison.py`
measures how far it sits from the derived line, and that measurement is its use. It
writes `data/terrain/harrison_1830_pre_cut_reading.geojson`, deliberately OUTSIDE
`data/terrain/epochs/`, so no scene can find it by looking for a shoreline.

It needs the network (the plate is fetched from the Internet Archive and its sha256
recorded) and numpy, scipy and Pillow, so it is NOT a check.sh step; the committed
reading is what the measurement reads.

The western companion to `tools/trace_shoreline.py` in subject and its opposite in
date. That tool traces the harbour AFTER the 1833-34 cut, off Wright 1834. This one
traces the same ground BEFORE it: the main stem running east past Fort Dearborn, the
bend south at the reservation, and the old southward channel behind the sand bar —
the water the cut destroyed.

    python3 tools/trace_shoreline_1830.py            re-trace and write the GeoJSON
    python3 tools/trace_shoreline_1830.py --check    re-trace and diff against committed
    python3 tools/trace_shoreline_1830.py --debug    also write a PNG of the segmentation

THE SHEET, AND WHY IT IS THIS ONE. `harrison_1830_river_mouth` is a U.S. civil
engineer's survey of the mouth, drawn February 1830 to show the proposed harbour
improvements — that is, drawn to record the mouth as it stood before anyone improved
it. It is the only pre-cut plan this project holds that draws the outlet. It letters
the features this trace needs in the draughtsman's own hand: "Old Mouth of River very
shallow", "Sand" and "Gravel" over the bar, "Beach", and — the one thing that must NOT
come forward to 1812 — "Channel cut by the Soldiers in 1828".

THE TRANSFORM IS NOT RE-DERIVED HERE. It is the one T-0883 stated and T-0882 checked
against the same raster: the plate rotated 90 degrees anticlockwise so its own north
arrow stands vertical, the stockade's ink centre at pixel (1445, 644) hung on the
committed palisade's local E +1152, N +221, and 0.33528 m per pixel — the 1.10 ft/px
scale docs/RESEARCH/fort_dearborn.md section 3 derives from the commandant's quarters.
This tool asserts the stockade ink still falls in its stated window before it uses it,
so a different scan or a different rotation stops the trace rather than moving a shore.

WHAT COMES OUT, AND WHAT DELIBERATELY DOES NOT. The hachure field is the water: this
engraving shades the water side of every shore and leaves the land white, so the water
body is the dense-ink region and the shore is its boundary. What that boundary is NOT,
everywhere, is a shore — east of the bar the lake's hachures simply thin out and stop,
and that edge is where the engraver's ruling pen stopped, not where Lake Michigan
began. `tools/trace_shoreline.py` separates the two by asking whether Wright INKED a
line under a vertex, and that test is run here too — but it does not discriminate on
this sheet and the run says so out loud: Harrison's plate is line art end to end, so
every boundary vertex is near ink and the test drops nothing. What keeps the lake out
of the published lines here is therefore not that test but two things that are declared
rather than inferred: the CUTS below, which sever the lake from the river at the foot
of the bar, and the ANCHORS, which publish only the two runs a hand-placed anchor
claims. Nothing here publishes a lake edge, a water polygon or a sand bar, and nothing
here publishes the 1828 soldiers' channel — see CUTS and `known_defects`.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "data" / "terrain"
OUT = OUT_DIR / "harrison_1830_pre_cut_reading.geojson"

# Internet Archive leaf n242 of historyofchicago01andr = Andreas vol. 1 p. 113.
IMAGE_URL = "https://archive.org/download/historyofchicago01andr/page/n242_w1600.jpg"
RAW_SIZE = (2003, 2715)          # as delivered; (2715, 2003) after the rotation
ROT_SIZE = (2715, 2003)

# The committed Harrison transform (T-0883, checked by T-0882). Pixels are in the
# ROTATED frame: +x east, +y south.
ANCHOR_PX = (1445, 644)
ANCHOR_LOCAL = (1152.0, 221.0)
SCALE_M_PER_PX = 0.33528
# The stockade's own ink window in that frame. This is the assertion that the raster
# in hand is the raster the transform was stated against.
STOCKADE_PX = (1356, 553, 1535, 730)
STOCKADE_TOL_PX = 12

# The sheet's neat lines, measured off the raster as the only columns and rows
# carrying frame-length ink. The trace works strictly inside them.
FRAME = (399, 249, 2337, 1832)   # x0, y0, x1, y1, half-open

# Hand-placed, and the only numbers here read off the scan by eye, exactly as
# tools/trace_shoreline.py places its own. Seeds select the water; anchors claim a
# boundary run for a name. Rotated-frame pixels.
SEEDS = {
    "main_stem": (1000, 700),           # open channel west of the fort
    "old_south_channel": (1580, 1300),  # behind the bar, below the reservation
}
ANCHORS = {
    # inside the reservation, against its lake shore and the old channel's west bank
    "south_shore_pre_cut": (1590, 1180),
    # the north bank of the main stem, opposite the fort
    "north_shore_pre_cut": (1380, 480),
}
ANCHOR_MAX_PX = 90

# The fort's stockade is solid ink at a hachure field's density and stands on dry
# ground. It is blanked by its own committed window rather than by a threshold,
# because a threshold that removed it would remove drawn shore as well.
# Declared cuts, each one a decision and not a threshold. A cut severs the water
# body; the boundary it leaves behind is a window edge and is dropped with the neat
# lines, exactly as `split_at_frame` drops them.
CUTS = {
    "stockade": (STOCKADE_PX, "The fort's stockade is solid ink at a hachure field's "
                 "density and stands on dry ground. It is cut by its own committed "
                 "window rather than by a threshold, because a threshold that removed "
                 "it would remove drawn shore with it."),
    "soldiers_channel_1828": ((1870, 690, 2115, 860),
                 "The arm Harrison letters 'Channel cut by the Soldiers in 1828'. It "
                 "is dated on the sheet's own face to sixteen years AFTER the state "
                 "this trace serves, so the trace is cut across it and neither its "
                 "banks nor the lake beyond it are published."),
    "old_mouth": ((1560, 1490, 1790, 1530),
                 "The foot of the bar, beside the mouth Harrison letters 'very "
                 "shallow'. The cut is what makes the lake a SEPARATE body from the "
                 "old channel, so no lake edge can reach a named run: east of the bar "
                 "the hachures thin and stop where the engraver's ruling pen stopped, "
                 "not where Lake Michigan began, and this trace publishes none of it. "
                 "The old channel's own west bank continues south of the cut to the "
                 "foot of the sheet, and is published."),
}
BLANK = [box for box, _ in CUTS.values()]
# A solid building glyph is denser than any hachure field and much smaller. Both
# tests have to bite: the fort's ranges are solid too, and they are big.
GLYPH_DENS = 0.82
GLYPH_MAX_PX = 3000

PARAMS = dict(
    bg_pct=75, ink_below=40,   # "darker than paper", as the Thompson forks trace reads ink
    dens_r=25, dens=0.30,      # a hachure FIELD, not a hachure line
    close_r=9, spur_r=31,
    speckle_px=4000,
    simplify_px=2.5,
    ink_ridge_r=7, ink_ridge=45,  # a drawn line is a ridge; a hachure field is a step
    ink_near_px=14,
    run_min_m=40.0,
)

# What this sheet draws that 1812 may not have. Recorded here and in the output so a
# reader can see the omission was a decision.
EXCLUDED = {
    "soldiers_channel_1828": {
        "lettered": "Channel cut by the Soldiers in 1828",
        "why": "It is dated on the sheet's own face to sixteen years AFTER the state "
               "this trace serves. A shoreline state addressed to 15 August 1812 may "
               "not carry a channel the garrison dug in 1828.",
    },
}


def die(msg: str, code: int = 2):
    print(msg)
    raise SystemExit(code)


def fetch(cache: Path):
    if not cache.exists():
        cache.parent.mkdir(parents=True, exist_ok=True)
        with urllib.request.urlopen(IMAGE_URL, timeout=180) as r:
            cache.write_bytes(r.read())
    return hashlib.sha256(cache.read_bytes()).hexdigest()


def to_local(px, py):
    return (round(ANCHOR_LOCAL[0] + (px - ANCHOR_PX[0]) * SCALE_M_PER_PX, 2),
            round(ANCHOR_LOCAL[1] - (py - ANCHOR_PX[1]) * SCALE_M_PER_PX, 2))


def length_m(line):
    return sum(math.dist(line[i], line[i + 1]) for i in range(len(line) - 1))


def split_at_frame(ring_px, margin=4):
    """Split the ring into runs, dropping the stretches that only follow the neat
    line or the edge of a declared cut. Pixel space, where both are axis-aligned."""
    x0, y0, x1, y1 = FRAME

    def on_cut(px, py):
        for bx0, by0, bx1, by1 in BLANK:
            if (bx0 - 12 <= px <= bx1 + 12) and (by0 - 12 <= py <= by1 + 12):
                return True
        return False

    on = [px <= x0 + margin or py <= y0 + margin or px >= x1 - 1 - margin
          or py >= y1 - 1 - margin or on_cut(px, py) for px, py in ring_px]
    m = len(ring_px)
    if not any(on):
        return [list(range(m))]
    start = next(i for i in range(m) if on[i])
    runs, cur = [], []
    for k in range(m + 1):
        i = (start + k) % m
        if on[i]:
            if len(cur) > 2:
                runs.append(cur)
            cur = []
        else:
            cur.append(i)
    return runs


def split_on_ink(idx, ring_px, d_ink, near):
    """Divide one boundary run into the stretches the engraver INKED a shore under
    and the stretches where only the hachure field ended. Yields (is_shore, idx)."""
    out, cur, flag = [], [], None
    for i in idx:
        px, py = ring_px[i]
        f = bool(d_ink[py - FRAME[1], px - FRAME[0]] <= near)
        if f != flag and cur:
            out.append((flag, cur))
            cur = []
        flag = f
        cur.append(i)
    if cur:
        out.append((flag, cur))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--debug", action="store_true")
    ap.add_argument("--cache", default=str(Path("/tmp") / "harrison_1830_n242.jpg"))
    args = ap.parse_args()

    try:
        import numpy as np
        from PIL import Image
        from scipy import ndimage as ndi
    except ImportError as e:
        die(f"SKIP: {e.name} not installed (pip install numpy scipy pillow); "
            f"1830 shoreline trace not run", 0)

    sys.path.insert(0, str(ROOT / "tools"))
    import trace_river as tr                                    # noqa: PLC0415

    datum = json.loads((ROOT / "data" / "datum.json").read_text())
    if not datum.get("verified"):
        die("REFUSING: data/datum.json is not verified.")
    o_e, o_n = datum["origin_utm_e"], datum["origin_utm_n"]

    cache = Path(args.cache)
    sha = fetch(cache)
    im = Image.open(cache)
    if im.size != RAW_SIZE:
        die(f"REFUSING: the plate is {im.size}, not {RAW_SIZE}; the committed "
            f"Harrison transform was stated against that raster")
    rot = im.transpose(Image.ROTATE_90).convert("L")
    if rot.size != ROT_SIZE:
        die(f"REFUSING: rotated plate is {rot.size}, not {ROT_SIZE}")
    a = np.asarray(rot).astype(np.float32)

    x0, y0, x1, y1 = FRAME
    sub = a[y0:y1, x0:x1]
    ink = sub < (np.percentile(sub, PARAMS["bg_pct"]) - PARAMS["ink_below"])

    # --- the transform's own assertion, before anything is measured from it -----
    sx0, sy0, sx1, sy1 = STOCKADE_PX
    pad = 40
    win = ink[sy0 - pad - y0:sy1 + pad - y0, sx0 - pad - x0:sx1 + pad - x0]
    lab, n = ndi.label(win)
    if n == 0:
        die("REFUSING: no ink at the stockade window")
    sizes = ndi.sum_labels(np.ones_like(lab, np.float32), lab, np.arange(1, n + 1))
    big = 1 + int(np.argmax(sizes))
    ys, xs = np.nonzero(lab == big)
    got = (int(xs.min()) + sx0 - pad, int(ys.min()) + sy0 - pad,
           int(xs.max()) + sx0 - pad, int(ys.max()) + sy0 - pad)
    # The committed window is the STOCKADE. At this trace's ink threshold the
    # largest component also carries the block Harrison draws projecting outside
    # the south-west angle, so the reading runs past the window's south edge and a
    # box-for-box test would fail on a raster that is in fact the right one. What
    # is tested instead is what the transform actually uses: where the stockade's
    # ink is CENTRED, and how wide it is.
    cx, cy = (got[0] + got[2]) / 2, (got[1] + got[3]) / 2
    ex, ey = (sx0 + sx1) / 2, (sy0 + sy1) / 2
    off = max(abs(cx - ex), abs(cy - ey), abs((got[2] - got[0]) - (sx1 - sx0)))
    if off > STOCKADE_TOL_PX:
        die(f"REFUSING: the stockade ink centres on {(round(cx,1), round(cy,1))} at "
            f"{got[2]-got[0]} px wide, {off:.1f} px off the committed centre "
            f"{(ex, ey)} at {sx1-sx0} px. The transform in this file was stated "
            f"against a raster this is not; re-derive it rather than moving a shore "
            f"under it.")
    print(f"transform: stockade ink centres on {(round(cx,1), round(cy,1))} "
          f"against {(ex, ey)}, {got[2]-got[0]} px wide against {sx1-sx0}; "
          f"worst of the three is {off:.1f} px; {SCALE_M_PER_PX} m/px")

    # --- the water body --------------------------------------------------------
    D = ndi.uniform_filter(ink.astype(np.float32), size=PARAMS["dens_r"])
    water = D > PARAMS["dens"]
    # building glyphs: solid, small, and standing on land
    solid = D > GLYPH_DENS
    gl, gn = ndi.label(solid)
    gs = ndi.sum_labels(np.ones_like(gl, np.float32), gl, np.arange(1, gn + 1))
    glyphs = np.isin(gl, 1 + np.flatnonzero(gs < GLYPH_MAX_PX))
    glyphs = ndi.binary_dilation(glyphs, np.ones((9, 9)))
    water &= ~glyphs
    print(f"glyphs: {int(np.count_nonzero(gs < GLYPH_MAX_PX))} solid blob(s) under "
          f"{GLYPH_MAX_PX} px read as building ink rather than as water")
    for bx0, by0, bx1, by1 in BLANK:
        water[by0 - 6 - y0:by1 + 6 - y0, bx0 - 6 - x0:bx1 + 6 - x0] = False
    water = ndi.binary_closing(water, np.ones((PARAMS["close_r"],) * 2))
    # Harrison draws the shop, the out-buildings, Craft's warehouse and his house as
    # small hatched blocks standing ON the bank. Hatched, they are as dense as a
    # hachure field and they touch it, so no threshold and no size rule separates
    # them — but each is a SPUR narrower than the water it hangs off. An opening at
    # `spur_r` takes a protrusion narrower than that and leaves the channel, which
    # is 150 px wide here, exactly where it was.
    r = PARAMS["spur_r"] // 2
    yy, xx = np.ogrid[-r:r + 1, -r:r + 1]
    disk = (xx * xx + yy * yy) <= r * r      # a DISK: a square one leaves the bank
    water = ndi.binary_opening(water, disk)  # stepped on the axes, which a bank is not
    lab, n = ndi.label(water)
    seed_labels = {k: int(lab[sy - y0, sx - x0]) for k, (sx, sy) in SEEDS.items()}
    if 0 in seed_labels.values() or len(set(seed_labels.values())) != 1:
        die(f"REFUSING: the seeds do not land in one water body: {seed_labels}")
    water = lab == next(iter(seed_labels.values()))
    filled = ndi.binary_fill_holes(water)
    holes = filled & ~water
    hl, hn = ndi.label(holes)
    hs = ndi.sum_labels(np.ones_like(hl, np.float32), hl, np.arange(1, hn + 1))
    keep = 1 + np.flatnonzero(hs >= PARAMS["speckle_px"])
    water = filled & ~np.isin(hl, keep)
    print(f"water {int(water.sum()):,} px; {hn} hole(s), {len(keep)} kept as island(s)")

    # --- a drawn line, as against a field that merely stops ---------------------
    lo = ndi.minimum_filter(sub, size=PARAMS["ink_ridge_r"])
    hi = ndi.maximum_filter(sub, size=PARAMS["ink_ridge_r"])
    drawn = ink & ((hi - lo) > PARAMS["ink_ridge"])
    d_ink = ndi.distance_transform_edt(~drawn)

    ring = tr.simplify_ring(tr.trace_outer(water, np), PARAMS["simplify_px"])
    ring_px = [(px + x0, py + y0) for px, py in ring]
    runs, kept, dropped_px = [], [], 0
    for idx in split_at_frame(ring_px):
        for is_shore, part in split_on_ink(idx, ring_px,
                                           d_ink, PARAMS["ink_near_px"]):
            pts = [ring_px[i] for i in part]
            if is_shore:
                runs.append(pts)
            else:
                dropped_px += len(pts)
    print(f"boundary: {len(runs)} inked run(s); {dropped_px} vertices where the "
          f"hachure field stopped and nothing was drawn under it")

    named, unclaimed = {}, 0
    for pts in runs:
        line = [to_local(px, py) for px, py in pts]
        if length_m(line) < PARAMS["run_min_m"]:
            continue
        best, bestd = None, 1e18
        for key, (ax, ay) in ANCHORS.items():
            d = min(math.hypot(px - ax, py - ay) for px, py in pts)
            if d < bestd:
                best, bestd = key, d
        if bestd > ANCHOR_MAX_PX:
            unclaimed += 1
            continue
        if best not in named or length_m(line) > length_m(named[best]["line"]):
            named[best] = {"line": line, "px": pts, "anchor_px": round(bestd, 1)}
    for key in ANCHORS:
        if key not in named:
            die(f"REFUSING: no inked boundary run came within {ANCHOR_MAX_PX} px "
                f"of the {key} anchor")
    print(f"named {len(named)} run(s); {unclaimed} inked run(s) no anchor claimed")

    if args.debug:
        Image.fromarray((water * 255).astype(np.uint8)).save("/tmp/harrison_water.png")

    feats = []
    for key, rec in named.items():
        line = rec["line"]
        feats.append({
            "type": "Feature",
            "id": key,
            "properties": {
                "kind": "shore",
                "name": NAMES[key],
                "confidence": "inferred",
                "observed_date": "1830-02-24",
                "source_id": "harrison_1830_river_mouth",
                "anchor_px_distance": rec["anchor_px"],
                "vertices": len(line),
                "length_m": round(length_m(line), 1),
                "note": NOTES[key],
            },
            "geometry": {
                "type": "LineString",
                "coordinates": [[round(o_e + e, 2), round(o_n + nn, 2)]
                                for e, nn in line],
            },
        })
    doc = {
        "type": "FeatureCollection",
        "_doc": DOC,
        "source": "harrison_1830_river_mouth",
        "image_sha256": sha,
        "transform": {
            "image": "Internet Archive leaf n242 of historyofchicago01andr "
                     "(Andreas, History of Chicago, vol. 1, p. 113)",
            "orientation": "rotated 90 degrees anticlockwise so the sheet's own "
                           "true-north arrow stands vertical; 2715 x 2003 px in that "
                           "orientation, +x east and +y south",
            "anchor_px": list(ANCHOR_PX),
            "anchor_local_enu_m": list(ANCHOR_LOCAL),
            "scale_m_per_px": SCALE_M_PER_PX,
            "stated_by": "T-0883, checked against this raster by T-0882 and again here",
        },
        "generated_by": "tools/trace_shoreline_1830.py",
        "excluded": EXCLUDED,
        "known_defects": KNOWN_DEFECTS,
        "cuts": {k: {"box_px": list(b), "why": w} for k, (b, w) in CUTS.items()},
        "crs_note": "Coordinates are EPSG:26916 metres (UTM 16N, NAD83); local ENU "
                    "metres are these minus data/datum.json origin_utm_e/origin_utm_n.",
        "features": feats,
    }
    text = json.dumps(doc, indent=1, ensure_ascii=False) + "\n"
    if args.check:
        if not OUT.exists():
            die(f"FAIL {OUT.relative_to(ROOT)} is missing")
        if OUT.read_text(encoding="utf-8") != text:
            die(f"FAIL {OUT.relative_to(ROOT)} is not what this tool traces today")
        print(f"OK {OUT.relative_to(ROOT)} is a fixed point of its own tracer")
        return 0
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text, encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}")
    return 0


NAMES = {
    "south_shore_pre_cut":
        "South and east shore before the cut: the south bank of the main stem past "
        "Fort Dearborn, the reservation's lake shore, and the west bank of the old "
        "southward channel",
    "north_shore_pre_cut":
        "North shore before the cut: the north bank of the main stem opposite the "
        "fort, and the lake shore north of the old mouth",
}
NOTES = {
    "south_shore_pre_cut":
        "This is the shore the 1833-34 harbour cut destroyed. It runs east along the "
        "main stem, turns south at the reservation where the bar deflected the river, "
        "and follows the old channel toward the mouth Harrison letters 'very shallow'. "
        "Graded inferred, not documented: the POSITION of each vertex is a measurement "
        "off a federal harbour survey, but the sheet readable here is Andreas's 1884 "
        "re-engraving of it, which says on its own face that it carries 'additions and "
        "changes suggested by the Memory of Early Settlers'.",
    "north_shore_pre_cut":
        "The north bank of the main stem, the Kinzie side. Same grade and the same "
        "reason as the south shore; the reach east of the old mouth is where this "
        "sheet's hachure field thins, and no vertex is published past the last one "
        "the engraver drew a line under.",
}
KNOWN_DEFECTS = [
    "south_shore_pre_cut carries about 60 m of the 1828 soldiers' channel's WESTERN "
    "ENTRANCE, between the old channel and the cut box at x 1870. The box cannot be "
    "carried further west without severing the old channel from the main stem, which "
    "the seed test refuses; the arm itself, its east bank and the lake beyond it are "
    "all outside. Read the entrance as 1828 work, not as 1812 shore.",
    "Two short spurs remain where Harrison draws a hatched block ON the bank — the "
    "shop, and Craft's house and warehouse. They are as dense as a hachure field and "
    "they touch it, and the opening at `spur_r` takes the narrower ones only.",
    "The opening that removes those spurs also stands the line up to half its radius "
    "(5.2 m) off the bank on a tight convex bend. That is inside this trace's stated "
    "uncertainty and is not corrected by hand.",
]
DOC = (
    "The shore of the Chicago River's mouth BEFORE the harbour cut, traced off the "
    "Harrison 1830 survey by tools/trace_shoreline_1830.py. A CROSS-CHECK READING, NOT A "
    "SHORELINE STATE: `shore_1812_pre_cut` is derived from Wright 1834 by "
    "tools/derive_shore_1812.py (owner ruling, 2026-09-17), and this file is what "
    "tools/measure_shore_1812_harrison.py measures that line against (T-1286). No scene "
    "reads it. It is NOT the 1835 shore either and may not be substituted for it: "
    "the 1833-34 cut, the piers and the harbour reach are all absent here because none "
    "of them existed when this sheet was drawn. Equally, the 1828 soldiers' channel the "
    "sheet letters is NOT published — see `excluded`. Do not hand-edit: "
    "`--check` asserts this file is a fixed point of its tracer."
)


if __name__ == "__main__":
    raise SystemExit(main())
