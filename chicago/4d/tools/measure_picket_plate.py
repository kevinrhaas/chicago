#!/usr/bin/env python3
"""measure_picket_plate.py — what the fort's pickets are, and what the plate draws.

T-0094 was filed off row 3 of `docs/RESEARCH/fort_dearborn_image_accuracy.md`:
*"Pickets are flat-topped and dark; the plate's are pointed and pale."* Both
halves of that sentence are claims about pictures — one about a mesh this
repository ships, one about a lithograph it holds — and neither had ever been
measured. This file measures them. **It refutes the first half outright and finds
the second unsupported by the source it cites.**

## 1. The model's pickets are not flat-topped, and never have been

`generators/archetypes/palisade.py::_picket` builds every post as a rectangular
shaft plus a four-triangle sharpened head, and `PalisadeParams.picket_point_m`
sizes that head. It has done so since the archetype was written. Since T-0200 the
size is the record's own `form.picket_head_m` — 0.312 m on this stockade,
`reconstructed` — and `min(width x 1.3, height x 0.18)` is the fallback for a
palisade record that states no head; declaring it moved no vertex, because the
value written is the one that expression already produced. The committed master
says the same thing without being
asked to agree — `assets/gltf/fort_dearborn_palisade__picket_1816.glb` carries the
picket material's 21,504 positions at exactly three heights:

    0.000 m   6,144 verts   the feet
    3.388 m  12,288 verts   the shoulders, where the shaft ends
    3.700 m   3,072 verts   the apexes — 4 per post, 768 posts

**0.312 m of sharpened head on a 3.70 m picket, 8.4 % of its height.** A visitor
standing at the north wall sees the sawtooth plainly; `docs/evidence/t-0094-*`
are that view and the plate beside it.

So the gate below is not an improvement, it is a **ratchet on something that was
already true**: if the stockade ever loses its head — a flattened archetype, a
decimation pass that eats the apexes, a record that drives the point to nothing —
this fails and names it, instead of the claim being re-filed from a screenshot.

## 2. The plate does not draw them pointed

`data/sources/assets/prefire_views_kevin_2026_08/p4_0.png`, the coloured view of
the fort from across the river, draws the curtain under a **ruled cap line**. Read
off the east reach, over the 195 px between the gate work and the east corner:

- the cap resolves in 138 of 195 columns, 121 of them surviving a 3-sigma clip,
  and is straight to **0.45 px rms**, peak-to-peak 2.0 px — stable to a hundredth
  of a pixel across three independent detector thresholds;
- the plate nonetheless **resolves individual pickets**: the curtain's column
  profile autocorrelates at **+0.70 at a lag of 10 px**, and the west reach of the
  same wall gives +0.60 at the same lag, so the draughtsman was drawing posts and
  not a ribbon;
- the curtain stands about **43 px** tall in that reach, so a head of the model's
  own proportion would serrate the top by 0.084 x 43 = **3.6 px** — eight times the
  residual measured.

**The plate had the resolution to draw a point and drew none.** `p4_1`, the wider
view from the lake, rules the same flat cap — 49 columns at 0.33 px rms — but it
draws the fort a third the size, so it is reported as corroboration and no
proportion is taken off it.

This does not make the head wrong. A lithographer ruling the top of a distant
stockade is exactly what a lithographer does, and Kinzie's "high pickets" says
nothing about their heads. It makes the head **unattested and ours** — which is
what `docs/LIBERTIES.md` **L179** now records, claiming `form.picket_head_m` in
its `Covers:` field — and it makes "the plate draws them pointed" a reading the
plate does not carry. (This line said L192 until T-0200; there is no L192, and a
pointer to a liberty that does not exist is worse than none.)

## 3. "Pale" is a reading of half of one wall

The plate paints the fort's north curtain across a 1.9x range of tone in a single
view, medians in sRGB with Rec. 709 luminance beside them:

    east reach of the curtain      (200, 191, 158)   lum 191
    west reach of the SAME wall    (117, 102,  76)   lum 103
    the fort's own frame range     (193, 184, 148)   lum 183
    bare earth of the bank         (126, 114,  89)   lum 115
    the paper, above the fort      (221, 220, 190)   lum 218

The committed picket albedo — `hewn_log`, linear (0.340, 0.266, 0.188) — is sRGB
(158, 141, 120), **luminance 143, between the plate's two readings of the one
wall**. A source that paints half a stockade darker than the model paints it, and
half of it paler, cannot warrant moving the model in either direction, and the
directory's own README binds it further: these are **tier 5 pictorial** sources,
retrospective, admissible for materials only as `inferred`.

The trap the ticket names is real and separate: Fergus's whitewashed board fence
is the enclosure of **1850**, after the pickets came down, and no part of the tone
question may be answered out of it.

## Why the plate half does not gate

A tier-5 retrospective lithograph is not an instrument. It may inform a value and
it may refute a claim made about itself; it may not hold a build red. So section 1
gates — it reads the committed GLB and needs nothing but the standard library —
and sections 2 and 3 report. Without Pillow the plate sections skip and say so,
the same bargain `tools/measure_reference.py` makes.

    python3 tools/measure_picket_plate.py            the whole reading
    python3 tools/measure_picket_plate.py --gate     section 1, as check.sh runs it
    python3 tools/measure_picket_plate.py --self-test every assertion, broken
    python3 tools/measure_picket_plate.py --glb PATH  gate some other GLB
"""
from __future__ import annotations

import argparse
import json
import math
import pathlib
import statistics
import struct
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
GLB = ROOT / "assets/gltf/fort_dearborn_palisade__picket_1816.glb"
RECORD = ROOT / "data/structures/fort_dearborn_palisade.json"
PLATE = ROOT / "data/sources/assets/prefire_views_kevin_2026_08/p4_0.png"
PLATE_WIDE = ROOT / "data/sources/assets/prefire_views_kevin_2026_08/p4_1.png"

#: The picket material's index in the palisade build — `palisade.M_PICKET`. The
#: gate resolves it by name rather than by number so a re-ordered material list
#: fails loudly instead of measuring the gate leaves.
PICKET_MATERIAL = "log"

#: How short a head may get before this is a flat-topped stockade. Not a tuning
#: knob: the archetype's own rule yields 8.4 % on this record, and 4 % is half of
#: that, which is the point at which the sawtooth stops reading at the wall.
MIN_POINT_FRACTION = 0.04

# ---------------------------------------------------------------- the plate
#
# Rectangles read off `p4_0.png` by eye, in its own pixels, and stated here rather
# than buried: this file cannot pretend they were surveyed. `p4_0` is 1538 x 859.
# EAST_CURTAIN is the reach of the north curtain between the log gate work and the
# east corner; WEST_CURTAIN is the reach on the other side of the same gate. The
# five tone anchors are all inside the same plate so the reading survives the
# paper's age-tint, which no absolute number would.
EAST_CURTAIN = (965, 1160)          # x span, both sections use it
EAST_CAP_ROWS = (364, 384)          # where the cap line is looked for
EAST_BODY_ROWS = (380, 410)         # the picket body, for rhythm and tone
WEST_CURTAIN = (340, 630)
WEST_BODY_ROWS = (384, 410)
TONE_BOXES = [
    ("east reach of the curtain", (965, 380, 1160, 412)),
    ("west reach of the same wall", (330, 382, 640, 412)),
    ("the fort's own frame range", (915, 345, 1140, 362)),
    ("bare earth of the bank", (200, 440, 700, 480)),
    ("the paper, above the fort", (600, 60, 760, 110)),
]
WIDE_CAP = (505, 640, 255, 272)     # p4_1's pale reach, corroboration only


class Fault(ValueError):
    """The measurement cannot be taken at all."""


# --------------------------------------------------------------- section 1

def read_glb(path: pathlib.Path):
    """The glTF JSON chunk and its binary buffer. No decoder, no dependencies."""
    data = path.read_bytes()
    magic, _version, length = struct.unpack_from("<III", data, 0)
    if magic != 0x46546C67:
        raise Fault(f"{path.name} is not a GLB")
    off, js, bin_ = 12, None, b""
    while off < length:
        clen, ctype = struct.unpack_from("<II", data, off)
        chunk = data[off + 8: off + 8 + clen]
        if ctype == 0x4E4F534A:
            js = json.loads(chunk.decode("utf-8"))
        elif ctype == 0x004E4942:
            bin_ = chunk
        off += 8 + clen
    if js is None:
        raise Fault(f"{path.name} carries no JSON chunk")
    return js, bin_


_COMPONENT = {5126: ("f", 4), 5125: ("I", 4), 5123: ("H", 2), 5121: ("B", 1)}
_COUNT = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}


def read_accessor(js, bin_, index):
    """One accessor as a list of tuples. Uncompressed masters only — the web
    derivatives are meshopt-packed, and this gate reads the master on purpose."""
    acc = js["accessors"][index]
    if "bufferView" not in acc:
        raise Fault("accessor has no bufferView — is this a compressed derivative?")
    bv = js["bufferViews"][acc["bufferView"]]
    fmt, size = _COMPONENT[acc["componentType"]]
    ncomp = _COUNT[acc["type"]]
    start = bv.get("byteOffset", 0) + acc.get("byteOffset", 0)
    stride = bv.get("byteStride") or ncomp * size
    return [struct.unpack_from("<" + fmt * ncomp, bin_, start + i * stride)
            for i in range(acc["count"])]


def model_head(glb: pathlib.Path = GLB) -> dict:
    """What the committed mesh actually builds on top of a picket.

    Blender exports Y-up, so a picket's height is the mesh's +Y. Every post is a
    shaft with a four-triangle head, so the picket primitive's vertices land on
    exactly three heights and the top one is the apexes.
    """
    js, bin_ = read_glb(glb)
    names = [m.get("name") for m in js.get("materials", [])]
    if PICKET_MATERIAL not in names:
        raise Fault(f"{glb.name} has no '{PICKET_MATERIAL}' material — it carries "
                    f"{names}; the picket surface cannot be identified")
    want = names.index(PICKET_MATERIAL)
    prim = next((p for m in js["meshes"] for p in m["primitives"]
                 if p.get("material") == want), None)
    if prim is None:
        raise Fault(f"{glb.name} draws nothing with the '{PICKET_MATERIAL}' material")
    ys = [round(v[1], 4) for v in read_accessor(js, bin_, prim["attributes"]["POSITION"])]
    levels = sorted({y: ys.count(y) for y in set(ys)}.items())
    if len(levels) < 3:
        raise Fault(f"the picket surface stands on {len(levels)} height(s) "
                    f"{[lv[0] for lv in levels]} — a shaft and a head make three")
    (_foot, n_foot), (shoulder, n_shoulder), (apex, n_apex) = levels[0], levels[-2], levels[-1]
    record = json.loads(RECORD.read_text())
    form = record["phases"][0]["form"]
    return {
        "glb": glb.name,
        "verts": len(ys),
        "levels": [{"y_m": y, "verts": n} for y, n in levels],
        "foot_verts": n_foot,
        "shoulder_m": shoulder,
        "shoulder_verts": n_shoulder,
        "apex_m": apex,
        "apex_verts": n_apex,
        "point_m": round(apex - shoulder, 4),
        "point_fraction": round((apex - shoulder) / apex, 4) if apex else 0.0,
        "posts": n_apex // 4,
        "record_picket_height_m": form["picket_height_m"]["value"],
        "record_picket_height_confidence": form["picket_height_m"]["confidence"],
    }


def gate(head: dict, echo=print) -> int:
    """The stockade is pointed. Three ways it could stop being, all refused."""
    bad = 0
    point, frac = head["point_m"], head["point_fraction"]
    if point <= 0:
        echo(f"  FAIL  {head['glb']}: the pickets are FLAT-TOPPED — the highest "
             f"vertices sit at the shaft top, {head['apex_m']} m")
        bad += 1
    elif frac < MIN_POINT_FRACTION:
        echo(f"  FAIL  {head['glb']}: the head is {point} m, {frac * 100:.1f} % of "
             f"the picket — under the {MIN_POINT_FRACTION * 100:.0f} % at which the "
             f"sawtooth stops reading at the wall")
        bad += 1
    else:
        echo(f"  ok    the pickets are pointed — {point} m of head, "
             f"{frac * 100:.1f} % of a {head['apex_m']} m picket")
    if head["apex_verts"] % 4:
        echo(f"  FAIL  {head['glb']}: {head['apex_verts']} apex vertices is not a "
             f"whole number of four-triangle heads")
        bad += 1
    elif head["apex_verts"] >= head["shoulder_verts"]:
        echo(f"  FAIL  {head['glb']}: {head['apex_verts']} apex vertices against "
             f"{head['shoulder_verts']} at the shoulder — a head is one vertex per "
             f"post against four, so these are caps and not points")
        bad += 1
    else:
        echo(f"  ok    {head['posts']} posts carry one apex each "
             f"({head['apex_verts']} verts, 4 per post)")
    if abs(head["apex_m"] - head["record_picket_height_m"]) > 0.02:
        echo(f"  FAIL  {head['glb']}: the mesh tops out at {head['apex_m']} m and the "
             f"record states {head['record_picket_height_m']} m — the point was added "
             f"to the picket instead of cut out of it")
        bad += 1
    else:
        echo(f"  ok    the point is CUT FROM the picket, not stacked on it — mesh "
             f"{head['apex_m']} m against the record's "
             f"{head['record_picket_height_m']} m "
             f"({head['record_picket_height_confidence']})")
    return 1 if bad else 0


# ------------------------------------------------------- sections 2 and 3

def _pillow():
    try:
        from PIL import Image  # noqa: PLC0415
        return Image
    except ImportError:
        return None


def _lum(c):
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def cap_line(px, x0, x1, ylo, yhi, dark=130, pale=155, run=3):
    """The curtain's top edge, per column, and how straight it is.

    A column resolves when a dark row is followed by `run` pale ones — the ruled
    cap over the lit wall. The fit is re-run three times against a 3-sigma MAD
    clip so a chimney or a figure crossing the line cannot bend it.
    """
    pts = []
    for x in range(x0, x1):
        hit = None
        for y in range(ylo, yhi):
            if _lum(px[x, y]) < dark and all(_lum(px[x, y + k]) > pale
                                             for k in range(1, run + 1)):
                hit = y
        if hit is not None:
            pts.append((x, hit))
    raw = len(pts)
    if raw < 20:
        return {"columns_offered": x1 - x0, "columns_resolved": raw, "rms_px": None}
    for _ in range(3):
        n = len(pts)
        mx = sum(p[0] for p in pts) / n
        my = sum(p[1] for p in pts) / n
        slope = (sum((p[0] - mx) * (p[1] - my) for p in pts)
                 / sum((p[0] - mx) ** 2 for p in pts))
        icpt = my - slope * mx
        res = [p[1] - (slope * p[0] + icpt) for p in pts]
        mad = statistics.median([abs(r) for r in res]) * 1.4826 or 1.0
        keep = [p for p, r in zip(pts, res) if abs(r) <= 3 * mad]
        if len(keep) < 20:
            break
        pts = keep
    n = len(pts)
    res = [p[1] - (slope * p[0] + icpt) for p in pts]
    return {
        "columns_offered": x1 - x0, "columns_resolved": raw, "columns_kept": n,
        "slope": round(slope, 4), "intercept": round(icpt, 2),
        "rms_px": round(math.sqrt(sum(r * r for r in res) / n), 2),
        "peak_to_peak_px": round(max(res) - min(res), 1),
    }


def rhythm(px, x0, x1, y0, y1):
    """The pitch at which the plate draws separate pickets, by autocorrelation of
    the curtain's column-mean darkness."""
    prof = [sum(_lum(px[x, y]) for y in range(y0, y1)) / (y1 - y0)
            for x in range(x0, x1)]
    mean = sum(prof) / len(prof)
    dev = [v - mean for v in prof]
    den = sum(v * v for v in dev) or 1.0
    lags = [(lag, sum(dev[i] * dev[i + lag] for i in range(len(dev) - lag)) / den)
            for lag in range(3, 20)]
    lag, corr = max(lags, key=lambda t: t[1])
    return {"pitch_px": lag, "autocorr": round(corr, 3),
            "profile_sd": round(statistics.pstdev(prof), 1)}


def curtain_height_px(px, x0, x1, cap):
    """How tall the curtain stands where the cap was fitted, so the serration a
    pointed head would draw can be stated in the plate's own pixels.

    The foot is where the pale wall gives out into the darker bank; the top is the
    fitted cap at the same column, so the wall's own lean cancels. Median, because
    the bank is scumbled and a handful of columns find the wrong edge.
    """
    if cap.get("rms_px") is None:
        return None
    heights = []
    for x in range(x0, x1):
        for y in range(405, 432):
            if all(_lum(px[x, y + k]) < 150 for k in range(4)) and _lum(px[x, y - 3]) > 160:
                heights.append(y - (cap["slope"] * x + cap["intercept"]))
                break
    if len(heights) < 20:
        return None
    return round(statistics.median(heights), 1)


def strokes(px, x0, x1, y0, y1):
    """The narrowest thing the plate ACTUALLY DRAWS on this curtain, in its own px.

    T-0185's question is not "does the plate disagree" — it plainly does, at a
    10 px pitch on a 43 px wall, which is 0.23 of the wall's height per post and
    therefore an 0.85 m picket nobody split. The question is whether that pitch
    is a reading of the fort or the floor of the medium. So: take the same column
    profile `rhythm` autocorrelates, split it about its own mean, and measure the
    run lengths. The dark runs are the drawn posts and the pale runs are the gaps
    between them, and the NARROWEST of each is what this plate could hold.

    The first and last run are dropped — both are cut by the crop rather than by
    the draughtsman, so their length is the rectangle's and not the plate's.
    """
    prof = [sum(_lum(px[x, y]) for y in range(y0, y1)) / (y1 - y0)
            for x in range(x0, x1)]
    mean = sum(prof) / len(prof)
    runs, state, n = [], None, 0
    for v in prof:
        pale = v > mean
        if pale == state:
            n += 1
        else:
            if state is not None:
                runs.append((state, n))
            state, n = pale, 1
    runs.append((state, n))
    runs = runs[1:-1]
    pale = [n for s, n in runs if s]
    dark = [n for s, n in runs if not s]
    if not pale or not dark:
        return None
    return {
        "posts_drawn": len(dark),
        "min_stroke_px": min(dark), "median_stroke_px": statistics.median(dark),
        "min_gap_px": min(pale), "median_gap_px": statistics.median(pale),
    }


def record_pickets() -> dict:
    """The three figures this ticket is about, off the record rather than the mesh.

    The GLB carries the height and the post count; it cannot carry the WIDTH and
    the SPACING separately, because a shaft of one width set at another pitch and
    a wider shaft at a wider pitch build the same silhouette from the front. Both
    are `reconstructed` on the record and both are what T-0185 asks about, so
    they are read where they are stated.
    """
    phase = json.loads(RECORD.read_text())["phases"][0]["form"]
    out = {}
    for key in ("picket_height_m", "picket_width_m", "picket_spacing_m"):
        out[key] = float(phase[key]["value"])
        out[key + "_confidence"] = phase[key]["confidence"]
    out["gap_m"] = round(out["picket_spacing_m"] - out["picket_width_m"], 4)
    return out


def drawn_scale(plate: dict, pickets: dict) -> dict | None:
    """The plate's own scale, and the model's rhythm expressed in the plate's px.

    ONE assumption, and it is the plate's own: that the curtain it draws is the
    wall this record builds, so the 42.9 px it stands is the record's 3.7 m. That
    is not a claim about 1816 — it is the only way to put two pictures of the same
    wall into one unit, and it is exactly the assumption the ticket's own "0.23 of
    the wall's height per post" already makes.
    """
    if not plate.get("curtain_px"):
        return None
    px_per_m = plate["curtain_px"] / pickets["picket_height_m"]
    east, west = plate.get("east_strokes"), plate.get("west_strokes")
    finest_gap = min(s["min_gap_px"] for s in (east, west) if s) if (east or west) else None
    finest_stroke = min(s["min_stroke_px"] for s in (east, west) if s) if (east or west) else None
    return {
        "px_per_m": round(px_per_m, 2),
        "model_pitch_px": round(pickets["picket_spacing_m"] * px_per_m, 2),
        "model_post_px": round(pickets["picket_width_m"] * px_per_m, 2),
        "model_gap_px": round(pickets["gap_m"] * px_per_m, 2),
        "plate_pitch_m": round(plate["east_rhythm"]["pitch_px"] / px_per_m, 3),
        "finest_gap_px": finest_gap,
        "finest_stroke_px": finest_stroke,
        "undrawable": finest_gap is not None
        and pickets["gap_m"] * px_per_m < finest_gap,
    }


def tone(px, boxes):
    out = []
    for label, (x0, y0, x1, y1) in boxes:
        vals = [px[x, y] for x in range(x0, x1) for y in range(y0, y1)]
        med = tuple(int(statistics.median(c[i] for c in vals)) for i in range(3))
        out.append({"what": label, "rgb": med, "lum": round(_lum(med))})
    return out


def srgb(x: float) -> int:
    """Linear to 8-bit sRGB, so the baked albedo can be read beside the plate."""
    v = 12.92 * x if x <= 0.0031308 else 1.055 * (x ** (1 / 2.4)) - 0.055
    return int(round(max(0.0, min(1.0, v)) * 255))


def model_albedo() -> dict:
    """What `hewn_log` is, read out of the material sheet rather than quoted."""
    sys.path.insert(0, str(ROOT / "generators"))
    from common import materials  # noqa: PLC0415
    lin = materials.HEWN_LOG.rgba[:3]
    rgb = tuple(srgb(c) for c in lin)
    return {"finish": materials.HEWN_LOG.key, "linear": lin, "rgb": rgb,
            "lum": round(_lum(rgb)), "tier": materials.HEWN_LOG.tier}


def plate_reading() -> dict | None:
    Image = _pillow()
    if Image is None:
        return None
    if not PLATE.exists():
        raise Fault(f"{PLATE} is missing — the plate this ticket cites is not here")
    px = Image.open(PLATE).convert("RGB").load()
    east_cap = cap_line(px, EAST_CURTAIN[0], EAST_CURTAIN[1], *EAST_CAP_ROWS)
    out = {
        "plate": PLATE.name,
        "east_cap": east_cap,
        "east_rhythm": rhythm(px, EAST_CURTAIN[0], EAST_CURTAIN[1], *EAST_BODY_ROWS),
        "west_rhythm": rhythm(px, WEST_CURTAIN[0], WEST_CURTAIN[1], *WEST_BODY_ROWS),
        "east_strokes": strokes(px, EAST_CURTAIN[0], EAST_CURTAIN[1], *EAST_BODY_ROWS),
        "west_strokes": strokes(px, WEST_CURTAIN[0], WEST_CURTAIN[1], *WEST_BODY_ROWS),
        "curtain_px": curtain_height_px(px, EAST_CURTAIN[0], EAST_CURTAIN[1], east_cap),
        "tone": tone(px, TONE_BOXES),
        "albedo": model_albedo(),
        "pickets": record_pickets(),
    }
    out["scale"] = drawn_scale(out, out["pickets"])
    if PLATE_WIDE.exists():
        wpx = Image.open(PLATE_WIDE).convert("RGB").load()
        out["wide_cap"] = cap_line(wpx, *WIDE_CAP)
    return out


# ------------------------------------------------------------------ report

def report(head: dict, plate: dict | None) -> None:
    print("\n  THE MODEL — what the committed master builds on top of a picket")
    print(f"    {head['glb']}: {head['verts']} positions on the "
          f"'{PICKET_MATERIAL}' surface, at {len(head['levels'])} heights")
    for lv in head["levels"]:
        print(f"      {lv['y_m']:>7.3f} m   {lv['verts']:>6d} verts")
    print(f"    {head['posts']} posts, each a shaft to {head['shoulder_m']} m and a "
          f"{head['point_m']} m head — {head['point_fraction'] * 100:.1f} % of its height")

    if plate is None:
        print("\n  THE PLATE — skipped: Pillow is not installed here.")
        print("    pip install Pillow, or read the numbers in this file's docstring.")
        return

    cap = plate["east_cap"]
    print(f"\n  THE PLATE — {plate['plate']}, tier 5 pictorial, reported and not gated")
    print(f"    cap line, east reach: resolved in {cap['columns_resolved']} of "
          f"{cap['columns_offered']} columns, kept {cap.get('columns_kept')}, "
          f"straight to {cap['rms_px']} px rms "
          f"(peak-to-peak {cap['peak_to_peak_px']} px)")
    print(f"    drawn picket pitch:   east {plate['east_rhythm']['pitch_px']} px "
          f"(autocorr {plate['east_rhythm']['autocorr']:+.2f}), "
          f"west {plate['west_rhythm']['pitch_px']} px "
          f"(autocorr {plate['west_rhythm']['autocorr']:+.2f})")
    if plate["curtain_px"]:
        serration = head["point_fraction"] * plate["curtain_px"]
        print(f"    the curtain stands {plate['curtain_px']} px tall there, so a head "
              f"of the model's proportion would serrate it by {serration:.1f} px — "
              f"{serration / cap['rms_px']:.0f}x the residual measured")
    if plate.get("wide_cap"):
        w = plate["wide_cap"]
        print(f"    p4_1 rules the same flat cap, {w['columns_resolved']} columns at "
              f"{w['rms_px']} px rms — corroboration, too coarse to quantify")
    sc = plate.get("scale")
    pk = plate["pickets"]
    if sc:
        print("\n  THE SCALE — what the plate COULD have drawn, in its own pixels (T-0185)")
        print(f"    the curtain is {plate['curtain_px']} px for the record's "
              f"{pk['picket_height_m']} m wall, so the plate draws at {sc['px_per_m']} px/m")
        print(f"    the model's rhythm at that scale: {sc['model_pitch_px']} px pitch = "
              f"{sc['model_post_px']} px of post and {sc['model_gap_px']} px of gap")
        east, west = plate["east_strokes"], plate["west_strokes"]
        for label, st in (("east", east), ("west", west)):
            if st:
                print(f"    {label} reach draws {st['posts_drawn']} posts: strokes "
                      f"{st['min_stroke_px']}-{st['median_stroke_px']:.0f} px, gaps "
                      f"{st['min_gap_px']}-{st['median_gap_px']:.0f} px")
        if sc["undrawable"]:
            print(f"    THE PLATE COULD NOT DRAW THIS WALL: the model's gap is "
                  f"{sc['model_gap_px']} px and the narrowest gap the plate holds "
                  f"anywhere on this curtain is {sc['finest_gap_px']} px — "
                  f"{sc['finest_gap_px'] / max(sc['model_gap_px'], 1e-9):.1f}x wider")
            print(f"    so its {plate['east_rhythm']['pitch_px']} px pitch "
                  f"({sc['plate_pitch_m']} m per post, on a "
                  f"{pk['picket_height_m']} m wall) is the FLOOR OF THE MEDIUM, not a "
                  f"reading of the fort: an {sc['plate_pitch_m']} m post is not a picket")
        else:
            print(f"    the plate had the resolution for the model's own rhythm "
                  f"({sc['model_gap_px']} px gap against a {sc['finest_gap_px']} px "
                  f"floor) and drew a coarser one — the disagreement is REAL")

    print("\n  THE TONE — medians in sRGB, all five anchors inside the one plate")
    for row in plate["tone"]:
        print(f"      {row['what']:<30s} {str(row['rgb']):<18s} lum {row['lum']:>3d}")
    alb = plate["albedo"]
    print(f"      {'the model, ' + alb['finish'] + ' albedo':<30s} "
          f"{str(alb['rgb']):<18s} lum {alb['lum']:>3d}   ({alb['tier']})")
    east = next(r for r in plate["tone"] if r["what"].startswith("east"))
    west = next(r for r in plate["tone"] if r["what"].startswith("west"))
    lo, hi = sorted((east["lum"], west["lum"]))
    inside = lo <= alb["lum"] <= hi
    print(f"    the plate paints one wall across {hi / max(lo, 1):.2f}x of tone; the "
          f"model's albedo falls {'INSIDE' if inside else 'OUTSIDE'} that range")


# --------------------------------------------------------------- self-test

def self_test() -> int:
    """Break each of the gate's four assertions and watch it fire."""
    failures = []
    real = model_head()
    quiet = lambda *a, **k: None  # noqa: E731 — the self-test reads return codes

    if gate(real, echo=quiet) != 0:
        failures.append("clean read")
        print("  SELF-TEST FAIL: the committed master does not pass its own gate")
    else:
        print("  passes: the committed master, unmodified")

    flat = dict(real, apex_m=real["shoulder_m"], point_m=0.0, point_fraction=0.0)
    if gate(flat, echo=quiet) == 0:
        failures.append("flat top")
        print("  SELF-TEST FAIL: a flat-topped stockade passed")
    else:
        print("  fires: a stockade whose apexes sit at the shaft top")

    stub = dict(real, point_m=0.05, point_fraction=0.013)
    if gate(stub, echo=quiet) == 0:
        failures.append("stub head")
        print("  SELF-TEST FAIL: a head too short to read passed")
    else:
        print("  fires: a head worn down under the fraction that reads at the wall")

    capped = dict(real, apex_verts=real["shoulder_verts"])
    if gate(capped, echo=quiet) == 0:
        failures.append("capped")
        print("  SELF-TEST FAIL: four apex vertices per post — a flat cap — passed")
    else:
        print("  fires: as many apex vertices as shoulders, which is a cap")

    stacked = dict(real, apex_m=round(real["apex_m"] + 0.312, 4))
    if gate(stacked, echo=quiet) == 0:
        failures.append("stacked")
        print("  SELF-TEST FAIL: a point stacked on top of a full-height picket passed")
    else:
        print("  fires: a picket that grew by its own point")

    if failures:
        print(f"  SELF-TEST FAILED: {len(failures)} assertion(s) did not fire")
        return 1
    print("  self-test: every assertion fires when broken")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="what the fort's pickets are, and "
                                             "what the plate draws")
    ap.add_argument("--gate", action="store_true",
                    help="section 1 only: fail if the stockade is not pointed")
    ap.add_argument("--self-test", action="store_true",
                    help="break each of the gate's assertions and watch it fire")
    ap.add_argument("--json", action="store_true", help="machine-readable reading")
    ap.add_argument("--quiet", action="store_true", help="gate output only")
    ap.add_argument("--glb", help="measure some other GLB (proving the gate fires)")
    args = ap.parse_args()

    if args.self_test:
        return self_test()

    head = model_head(pathlib.Path(args.glb) if args.glb else GLB)
    if args.gate:
        rc = gate(head)
        if not args.quiet and rc == 0:
            print("  (the plate half is reported by the same file without --gate; "
                  "a tier-5 lithograph does not hold a build red)")
        return rc
    plate = plate_reading()
    if args.json:
        print(json.dumps({"model": head, "plate": plate}, indent=1))
        return 0
    report(head, plate)
    return gate(head)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Fault as exc:
        print(f"  FAIL — {exc}")
        sys.exit(1)
