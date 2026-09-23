#!/usr/bin/env python3
"""Read the nine coloured swatches in J. S. Wright's 1834 legend, and say what
each colour can and cannot decide about the ground (T-0792, piece 1).

    tools/read_wright_legend_swatches.py --build             re-read the raster, rewrite the record
    tools/read_wright_legend_swatches.py --check-properties  the gate: offline, re-derives every number
    tools/read_wright_legend_swatches.py --report            print the reading
    tools/read_wright_legend_swatches.py --self-test         the gate's assertions still fire when broken

THE HOLE THIS CLOSES. Wright's legend is nine coloured chips, each naming a survey
tract and most of them a date, and it is the only place on any sheet in this project
that says WHO SURVEYED WHAT GROUND AND WHEN. T-0792 asks for nine tract polygons off
those colours. Nothing had ever measured the chips. Three open tickets — T-0792 itself,
T-0796 on the Michigan St tract, T-1082 on the wash between Wright's bank shading and
his inked bank line — all say some form of "read it against the legend's swatches", and
none of them could, because the swatches had no committed colour, no pixel box and no
statement of how far apart they are.

WHAT THIS READS, AND IN WHAT ORDER OF CONFIDENCE.

  the chips        Nine boxes located on the NA/HUP raster by their own darkness against
                   the paper, each chip's interior sampled with its inked border eroded
                   away: median, mean and per-channel standard deviation, and the count.
                   This is a measurement of the raster and nothing else, and it is the
                   only `documented` claim here.
  the separation   The distance between every pair of chip medians, against the spread
                   INSIDE a chip. This is arithmetic on the measurement.
  the bands        Where each separable colour appears on the sheet: pixels near a class
                   colour, thinned to the broad boundary bands by requiring a cell of
                   8x8 px to be at least 45 % covered, then joined into components. A
                   band is evidence about the raster; naming the ground under it is not,
                   and the naming lives in docs/RESEARCH/wright_1834_legend_swatches.md
                   where it can be argued with.

THE RESULT THAT MATTERS, and it is a refusal. The nine chips do not carry nine
separable colours. Chips 3 (Wabansia) and 7 (Fractional Section 15) differ by 10 RGB
units; chips 4, 6 and 9 (Kinzie's Addition, the unnamed 1833 survey, Part of Canal
Section 9) lie within 30 of each other; and the per-pixel spread inside a single chip is
30 to 60 units per channel. So a pixel of wash on the sheet cannot be assigned to a chip
— only to a CLASS of chips. T-0792 asks for the two ambiguous swatches to be read "by
matching swatch to ground on the sheet"; measured, that method cannot do it, and saying
so is worth more than a confident wrong answer. What is left is position: inside a class
whose other members are named ground, the band that is not on named ground is the
unnamed chip's. That argument is piece 2's to make with polygons.

WHY THE NA/HUP SHEET AND NOT THE BPL ONE. The chips are a centimetre of paper; at 600
dpi they are 54 px wide and at the BPL scan's resolution they would be half that. The
local metres printed beside every band come from the committed NA/HUP affine
(`data/traces/gcp/wright_1834_nara_hup_gcps.json`), whose own y scale is under challenge
in T-0878 — so they are stated as INDICATIVE, to say which part of town a band is in,
and nothing in this file is geometry anything else may stand on.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import deque
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RECORD = ROOT / "data" / "traces" / "wright_1834_legend_swatches.json"
GCPS = ROOT / "data" / "traces" / "gcp" / "wright_1834_nara_hup_gcps.json"
DATUM = ROOT / "data" / "datum.json"

# The chip column, read off the raster and then frozen: the nine boxes are stable
# features of one scan and re-finding them on every run would make the record depend on
# a threshold rather than on the paper.
CHIP_X0, CHIP_X1 = 2996, 3050          # interior, the inked border already eroded away
CHIP_ROWS = [(3768, 3805), (3819, 3850), (3863, 3899), (3913, 3949), (3959, 4001),
             (4005, 4034), (4045, 4075), (4093, 4119), (4129, 4168)]
CHIP_EROSION_TOP, CHIP_EROSION_BOTTOM = 6, 5

# The legend's wording, read at 2x off the 600 dpi scan. `text` is what the hand writes;
# `reading` is what it is taken to say where the hand is ambiguous, and the difference is
# never silent.
LEGEND = [
    {"text": "U. S. Military Reservation", "reading": "U.S. Military Reservation", "date": None},
    {"text": "Surveyed by Canal Com. in 1830", "reading": "Surveyed by Canal Com. in 1830", "date": 1830},
    {"text": "Wonbonsia Surveyed in 1831", "reading": "Wabansia, surveyed in 1831", "date": 1831},
    {"text": "Kinzies Addⁿ. Surveyed „ 1833", "reading": "Kinzie's Addition, surveyed 1833", "date": 1833},
    {"text": "School Section „ 1833", "reading": "School Section, surveyed 1833", "date": 1833},
    {"text": "Surveyed. ——— 1833", "reading": "Surveyed 1833 — no tract named", "date": 1833},
    {"text": "Fractional Section 15", "reading": "Fractional Section 15", "date": None},
    {"text": "Surveyed in 1833", "reading": "Surveyed in 1833 — no tract named", "date": 1833},
    {"text": "Part of Canal Sec. No 9", "reading": "Part of Canal Section No. 9", "date": None},
]

# A chip pair closer than this is not separable by eye or by arithmetic on this paper:
# it is under a fifth of the per-channel spread inside a single chip, which the record
# measures rather than assumes.
CLASS_THRESHOLD = 35.0

# The band extraction. A pixel joins a class when it is within MATCH of the class colour,
# clear of the paper, and carries some chroma; a cell of KxK px is a band cell when it is
# at least COVER covered; a component is kept at MIN_CELLS.
BAND_MATCH = 45.0
BAND_PAPER_MIN = 55.0
BAND_SAT_MIN = 0.30
BAND_K = 8
BAND_COVER = 0.45
BAND_MIN_CELLS = 40

# The sheet's inner neat line, read off the same raster by projecting its dark ink: the
# double rule stands at x 681/700 and x 4337/4390, y 986 and y 5701. A band whose centroid
# falls outside it is paper — margin, foxing, the tear's repair — and is marked, not dropped.
NEAT_LINE = {"x0": 620, "y0": 960, "x1": 4400, "y1": 5720}
LEGEND_BOX = {"x0": 2960, "y0": 3740, "x1": 3120, "y1": 4185}


def load(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))


def affine():
    return load(GCPS)["fit"]["coefficients"], load(DATUM)


def to_local(px: float, py: float) -> tuple[float, float]:
    c, d = affine()
    E = c["a"] * px + c["b"] * py + c["c"]
    N = c["d"] * px + c["e"] * py + c["f"]
    return E - d["origin_utm_e"], N - d["origin_utm_n"]


def dist(u, v) -> float:
    return sum((a - b) ** 2 for a, b in zip(u, v)) ** 0.5


def classes_from(medians, threshold=CLASS_THRESHOLD):
    """Single-link grouping of the chips at `threshold`, 1-based chip numbers."""
    parent = list(range(len(medians)))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for i in range(len(medians)):
        for j in range(i + 1, len(medians)):
            if dist(medians[i], medians[j]) < threshold:
                parent[find(i)] = find(j)
    groups: dict[int, list[int]] = {}
    for i in range(len(medians)):
        groups.setdefault(find(i), []).append(i + 1)
    return [g for _, g in sorted(groups.items(), key=lambda kv: kv[1][0])]


# ---------------------------------------------------------------- the build side

def build() -> int:
    try:
        import numpy as np
        from PIL import Image
    except ImportError as exc:            # a narrow, loud skip — never a silent pass
        print(f"SKIP --build: needs numpy and Pillow ({exc})", file=sys.stderr)
        return 3
    Image.MAX_IMAGE_PIXELS = None
    src = load(GCPS)["raster"]
    working = ROOT.parent.parent / src["working_copy"]
    if not working.exists():
        print(f"SKIP --build: the working copy is not in this checkout ({working})", file=sys.stderr)
        return 3
    arr = np.asarray(Image.open(working).convert("RGB"), dtype=np.float32)

    chips = []
    for i, (y0, y1) in enumerate(CHIP_ROWS, start=1):
        box = arr[y0 + CHIP_EROSION_TOP:y1 - CHIP_EROSION_BOTTOM, CHIP_X0:CHIP_X1].reshape(-1, 3)
        chips.append({
            "chip": i,
            "legend": LEGEND[i - 1],
            "box_px": {"x0": CHIP_X0, "y0": y0, "x1": CHIP_X1, "y1": y1},
            "sampled_px": int(box.shape[0]),
            "median_rgb": [int(round(v)) for v in np.median(box, axis=0)],
            "mean_rgb": [round(float(v), 1) for v in box.mean(axis=0)],
            "sd_rgb": [round(float(v), 1) for v in box.std(axis=0)],
        })

    medians = [c["median_rgb"] for c in chips]
    groups = classes_from(medians)
    paper = [int(round(v)) for v in np.median(arr.reshape(-1, 3)[::997], axis=0)]

    reps = [[sum(medians[i - 1][k] for i in g) / len(g) for k in range(3)] for g in groups]
    mx, mn = arr.max(2), arr.min(2)
    sat = (mx - mn) / np.maximum(mx, 1.0)
    from_paper = np.linalg.norm(arr - np.array(paper, dtype=np.float32), axis=2)
    stack = np.stack([np.linalg.norm(arr - np.array(r, dtype=np.float32), axis=2) for r in reps])
    label, best = stack.argmin(0), stack.min(0)
    keep = (best < BAND_MATCH) & (from_paper > BAND_PAPER_MIN) & (sat > BAND_SAT_MIN)

    K = BAND_K
    H, W = arr.shape[0] // K, arr.shape[1] // K
    bands = []
    for gi, group in enumerate(groups):
        cover = ((label == gi) & keep)[:H * K, :W * K].reshape(H, K, W, K).mean(axis=(1, 3))
        mask = cover > BAND_COVER
        bridged = mask.copy()
        for axis in (0, 1):
            for shift in (1, -1):
                bridged |= np.roll(mask, shift, axis=axis)
        found = []
        for comp in _components(bridged, BAND_MIN_CELLS):
            ys = [p[0] * K for p in comp]
            xs = [p[1] * K for p in comp]
            cx, cy = sum(xs) / len(xs), sum(ys) / len(ys)
            e0, n0 = to_local(min(xs), max(ys))
            e1, n1 = to_local(max(xs), min(ys))
            found.append({
                "cells": len(comp),
                "box_px": {"x0": min(xs), "y0": min(ys), "x1": max(xs), "y1": max(ys)},
                "centroid_px": [round(cx, 1), round(cy, 1)],
                "box_local_m": {"e0": round(e0, 1), "n0": round(n0, 1),
                                "e1": round(e1, 1), "n1": round(n1, 1)},
                "off_map": not (NEAT_LINE["x0"] <= cx <= NEAT_LINE["x1"]
                                and NEAT_LINE["y0"] <= cy <= NEAT_LINE["y1"]),
                "in_legend": (LEGEND_BOX["x0"] <= cx <= LEGEND_BOX["x1"]
                              and LEGEND_BOX["y0"] <= cy <= LEGEND_BOX["y1"]),
            })
        found.sort(key=lambda b: -b["cells"])
        bands.append({
            "class": group,
            "class_colour_rgb": [round(v, 1) for v in reps[gi]],
            "band_count": len(found),
            "bands": found[:8],
        })

    doc = _record(chips, groups, paper, bands, cross_check(groups, bands))
    RECORD.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {RECORD.relative_to(ROOT)}: 9 chips, {len(groups)} separable colours, "
          f"{sum(b['band_count'] for b in bands)} bands")
    return 0


def _components(mask, min_cells):
    H, W = mask.shape
    seen = [[False] * W for _ in range(H)]
    out = []
    for y in range(H):
        row = mask[y]
        for x in range(W):
            if not row[x] or seen[y][x]:
                continue
            seen[y][x] = True
            queue, cells = deque([(y, x)]), []
            while queue:
                cy, cx = queue.popleft()
                cells.append((cy, cx))
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        ny, nx = cy + dy, cx + dx
                        if 0 <= ny < H and 0 <= nx < W and mask[ny][nx] and not seen[ny][nx]:
                            seen[ny][nx] = True
                            queue.append((ny, nx))
            if len(cells) >= min_cells:
                out.append(cells)
    return out


SCHOOL_BLOCKS = ROOT / "data" / "traces" / "vectors" / "school_section_blocks_1834.json"


def cross_check(groups, bands) -> dict:
    """The one test this reading can be put to, and it is not a self-assessment.

    Chip 5 says `School Section`, and section 16's four sides are already committed —
    seated on GCP G1 and a nominal mile, by work that never looked at a colour. So the
    yellow class's bands can be held against them. Nothing here CHOOSES the section for
    the chip; it asks whether each committed side falls INSIDE the band of that chip's
    colour, which is the claim a painted boundary wash actually makes. A band is 40 to
    120 m thick — brush, bleed and the cell grid — so its outer edge is not an estimate
    of a line and is not treated as one.
    """
    anchor = load(SCHOOL_BLOCKS)["anchor"]
    entry = next(e for e in bands if 5 in e["class"])
    # The grace is the registration's OWN RMS, read from it rather than typed here: the
    # fit in force changed under T-1091 and a figure written into a tool does not follow
    # (T-1092 found this one still quoting the superseded eight-point fit's 16.19 m).
    out = {"confidence": "inferred", "rms_grace_m": load(GCPS)["fit"]["rms_m"]}
    for side, axis in (("north", "n"), ("south", "n"), ("east", "e"), ("west", "e")):
        want = anchor[side]
        out[side] = _side_check(entry["bands"], axis, want)
        out[side]["committed_m"] = round(want, 2)
    out["note"] = (
        "Every committed side of section 16 falls inside the band of chip 5's own colour. "
        "The section's geometry comes from the PLSS corner at State and Madison and a "
        "nominal mile; the band comes from a colour chip 3,000 px away on the same paper. "
        "They were derived without reference to each other, so the agreement is evidence "
        "that reading ground off these chips is worth doing — and it is the ONLY "
        "chip-to-ground reading this file makes. The other eight are piece 2's."
    )
    return out


def _side_check(bands, axis, want) -> dict:
    """Find the band of the right orientation whose span holds `want`, and describe it."""
    best = None
    for band in bands:
        box = band["box_local_m"]
        e_span = abs(box["e1"] - box["e0"])
        n_span = abs(box["n1"] - box["n0"])
        if axis == "n" and not e_span > 2 * n_span:
            continue
        if axis == "e" and not n_span > 2 * e_span:
            continue
        lo, hi = sorted((box[axis + "0"], box[axis + "1"]))
        gap = 0.0 if lo <= want <= hi else min(abs(want - lo), abs(want - hi))
        cand = {"band_span_m": [round(lo, 1), round(hi, 1)],
                "band_mid_m": round((lo + hi) / 2, 1),
                "outside_band_by_m": round(gap, 1),
                "cells": band["cells"]}
        if best is None or (cand["outside_band_by_m"], -cand["cells"]) < \
                (best["outside_band_by_m"], -best["cells"]):
            best = cand
    return best or {"band_span_m": None, "band_mid_m": None,
                    "outside_band_by_m": None, "cells": 0}


def _record(chips, groups, paper, bands, checks) -> dict:
    medians = [c["median_rgb"] for c in chips]
    separation = [[round(dist(medians[i], medians[j]), 1) for j in range(9)] for i in range(9)]
    worst_sd = max(max(c["sd_rgb"]) for c in chips)
    return {
        "_doc": (
            "The nine coloured chips of J. S. Wright's 1834 legend, measured off the NA/HUP "
            "600 dpi scan, and the bands of each separable colour on the sheet. Built by "
            "tools/read_wright_legend_swatches.py --build; gated offline by --check-properties. "
            "The chip colours are documented measurements of the raster. The BANDS are "
            "measurements too, but the GROUND under a band is an argument and is made in "
            "docs/RESEARCH/wright_1834_legend_swatches.md, not here."
        ),
        "source_id": "wright_1834_nara_hup",
        "raster": load(GCPS)["raster"],
        "affine": {
            "from": "data/traces/gcp/wright_1834_nara_hup_gcps.json",
            "confidence": "inferred",
            "note": (
                "Local metres are INDICATIVE — they say which part of town a band is in. "
                "The NA/HUP fit's y scale is under challenge in T-0878 (the School Section's "
                "mile measures 1658.65 m north-south against 1603.04 m east-west on the same "
                "fit), so no geometry in this project may stand on a number printed here."
            ),
        },
        "method": {
            "chip_column_px": {"x0": CHIP_X0, "x1": CHIP_X1},
            "chip_erosion_px": {"top": CHIP_EROSION_TOP, "bottom": CHIP_EROSION_BOTTOM},
            "paper_rgb": paper,
            "class_threshold_rgb": CLASS_THRESHOLD,
            "band": {"match_rgb": BAND_MATCH, "paper_min_rgb": BAND_PAPER_MIN,
                     "saturation_min": BAND_SAT_MIN, "cell_px": BAND_K,
                     "cell_coverage_min": BAND_COVER, "min_cells": BAND_MIN_CELLS},
            "neat_line_px": NEAT_LINE,
            "legend_box_px": LEGEND_BOX,
        },
        "chips": chips,
        "separation_rgb": separation,
        "separability": {
            "confidence": "documented",
            "classes": groups,
            "worst_within_chip_sd_rgb": worst_sd,
            "finding": (
                f"Nine chips, {len(groups)} separable colours. The closest pair is "
                f"{_closest(separation)}. The widest per-channel spread INSIDE a single chip is "
                f"{worst_sd} RGB units, so a pixel of wash cannot be assigned to a chip — only "
                "to a class. Matching swatch to ground by colour alone therefore cannot resolve "
                "the two swatches T-0792 calls ambiguous, and this file records that as a "
                "refusal rather than guessing from the legend's order."
            ),
        },
        "bands_by_class": bands,
        "cross_check_school_section": checks,
    }


def _closest(separation) -> str:
    best, pair = None, None
    for i in range(9):
        for j in range(i + 1, 9):
            if best is None or separation[i][j] < best:
                best, pair = separation[i][j], (i + 1, j + 1)
    return f"chips {pair[0]} and {pair[1]} at {best} RGB units"


# ---------------------------------------------------------------- the gate

def check_properties(doc: dict | None = None) -> int:
    """Offline: no numpy, no Pillow, no raster read except the file's own header."""
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from check_wright_nara_registration import jpeg_properties, sha256

    doc = doc if doc is not None else load(RECORD)
    bad: list[str] = []

    chips = doc.get("chips", [])
    if len(chips) != 9:
        bad.append(f"chips: {len(chips)} committed, the legend has 9")
    for i, chip in enumerate(chips, start=1):
        if chip.get("chip") != i:
            bad.append(f"chips[{i}].chip: committed {chip.get('chip')}, expected {i}")
        want = LEGEND[i - 1] if i <= len(LEGEND) else None
        if want is not None and chip.get("legend") != want:
            bad.append(f"chips[{i}].legend: committed {chip.get('legend')} != {want}")
        box = chip.get("box_px", {})
        rows = CHIP_ROWS[i - 1] if i <= len(CHIP_ROWS) else (None, None)
        if (box.get("x0"), box.get("x1"), box.get("y0"), box.get("y1")) != \
           (CHIP_X0, CHIP_X1, rows[0], rows[1]):
            bad.append(f"chips[{i}].box_px: committed {box} is not the frozen chip box")
        height = (rows[1] - CHIP_EROSION_BOTTOM) - (rows[0] + CHIP_EROSION_TOP)
        want_n = height * (CHIP_X1 - CHIP_X0)
        if chip.get("sampled_px") != want_n:
            bad.append(f"chips[{i}].sampled_px: committed {chip.get('sampled_px')} != "
                       f"{want_n} for its own eroded box")
        for key in ("median_rgb", "mean_rgb", "sd_rgb"):
            v = chip.get(key)
            if not (isinstance(v, list) and len(v) == 3 and all(0 <= float(x) <= 255 for x in v)):
                bad.append(f"chips[{i}].{key}: {v} is not three channel values")

    medians = [c.get("median_rgb") for c in chips]
    if all(isinstance(m, list) and len(m) == 3 for m in medians) and len(medians) == 9:
        for i in range(9):
            for j in range(9):
                want = round(dist(medians[i], medians[j]), 1)
                got = doc.get("separation_rgb", [[None] * 9] * 9)[i][j]
                if abs(float(got) - want) > 0.05:
                    bad.append(f"separation_rgb[{i}][{j}]: committed {got} != {want} "
                               "re-derived from the committed medians")
        want_classes = classes_from(medians, doc["method"]["class_threshold_rgb"])
        if doc["separability"]["classes"] != want_classes:
            bad.append(f"separability.classes: committed {doc['separability']['classes']} != "
                       f"{want_classes} re-derived at the committed threshold")
        worst = max(max(c["sd_rgb"]) for c in chips)
        if abs(doc["separability"]["worst_within_chip_sd_rgb"] - worst) > 0.05:
            bad.append("separability.worst_within_chip_sd_rgb does not match the chips")
        closest = min(doc["separation_rgb"][i][j] for i in range(9) for j in range(i + 1, 9))
        if closest >= worst / 5:
            bad.append(f"the refusal no longer follows: closest pair {closest} is not under "
                       f"a fifth of the worst within-chip spread {worst}")

    coeffs, datum = affine()
    for entry in doc.get("bands_by_class", []):
        group = entry.get("class")
        if not group or any(g not in range(1, 10) for g in group):
            bad.append(f"bands_by_class: {group} is not a group of chip numbers")
        for k, band in enumerate(entry.get("bands", [])):
            box = band["box_px"]
            for corner, px, py in (("0", box["x0"], box["y1"]), ("1", box["x1"], box["y0"])):
                E = coeffs["a"] * px + coeffs["b"] * py + coeffs["c"] - datum["origin_utm_e"]
                N = coeffs["d"] * px + coeffs["e"] * py + coeffs["f"] - datum["origin_utm_n"]
                for axis, want, got in (("e", E, band["box_local_m"]["e" + corner]),
                                        ("n", N, band["box_local_m"]["n" + corner])):
                    if abs(want - got) > 0.05:
                        bad.append(f"bands_by_class[{group}].bands[{k}].box_local_m.{axis}{corner}:"
                                   f" committed {got} != {round(want, 1)} through the committed affine")
            cx, cy = band["centroid_px"]
            if not (box["x0"] <= cx <= box["x1"] and box["y0"] <= cy <= box["y1"]):
                bad.append(f"bands_by_class[{group}].bands[{k}]: centroid outside its own box")
            want_off = not (NEAT_LINE["x0"] <= cx <= NEAT_LINE["x1"]
                            and NEAT_LINE["y0"] <= cy <= NEAT_LINE["y1"])
            if band["off_map"] != want_off:
                bad.append(f"bands_by_class[{group}].bands[{k}].off_map: committed "
                           f"{band['off_map']} != {want_off} for its own centroid")
            if band["cells"] < BAND_MIN_CELLS:
                bad.append(f"bands_by_class[{group}].bands[{k}]: {band['cells']} cells is under "
                           f"the committed floor {BAND_MIN_CELLS}")

    checks = doc.get("cross_check_school_section")
    if not checks:
        bad.append("cross_check_school_section: missing")
    else:
        anchor = load(SCHOOL_BLOCKS)["anchor"]
        entry = next((e for e in doc.get("bands_by_class", []) if 5 in e.get("class", [])), None)
        for side, axis in (("north", "n"), ("south", "n"), ("east", "e"), ("west", "e")):
            got = checks.get(side, {})
            if abs(got.get("committed_m", 0) - round(anchor[side], 2)) > 0.005:
                bad.append(f"cross_check_school_section.{side}.committed_m: committed "
                           f"{got.get('committed_m')} != {round(anchor[side], 2)} in the "
                           "blocks file's own anchor")
            want = _side_check((entry or {}).get("bands", []), axis, anchor[side])
            for key in ("band_span_m", "band_mid_m", "outside_band_by_m", "cells"):
                if got.get(key) != want[key]:
                    bad.append(f"cross_check_school_section.{side}.{key}: committed "
                               f"{got.get(key)} != {want[key]} re-derived from the bands")
            gap = want["outside_band_by_m"]
            grace = checks.get("rms_grace_m", load(GCPS)["fit"]["rms_m"])
            if gap is None or gap > grace:
                bad.append(f"cross_check_school_section.{side}: section 16's committed side "
                           f"stands {gap} m outside chip 5's band, past the sheet's own "
                           f"{grace} m RMS — the one chip-to-ground reading this file makes "
                           "no longer holds")

    raster = doc.get("raster", {})
    if raster != load(GCPS)["raster"]:
        bad.append("raster: this record's raster block has drifted from the registration's")
    working = ROOT.parent.parent / raster.get("working_copy", "")
    if not working.exists():
        print(f"  SKIP raster identity: {raster.get('working_copy')} is not in this checkout")
    else:
        if sha256(working) != raster.get("sha256"):
            bad.append("raster.sha256: the working copy is not the sheet this was read off")
        props = jpeg_properties(working)
        if (props.get("width"), props.get("height")) != (raster.get("width"), raster.get("height")):
            bad.append(f"raster size: committed {raster.get('width')}x{raster.get('height')} != "
                       f"{props.get('width')}x{props.get('height')} in the JPEG header")
        for y0, y1 in CHIP_ROWS:
            if not (0 <= y0 < y1 <= props.get("height", 0)):
                bad.append(f"chip row {y0}-{y1} falls outside the raster")
        if not (0 <= CHIP_X0 < CHIP_X1 <= props.get("width", 0)):
            bad.append("the chip column falls outside the raster")

    for line in bad:
        print("  " + line)
    print(f"{'FAIL' if bad else 'ok'}: wright 1834 legend swatches — {len(chips)} chips, "
          f"{len(doc.get('separability', {}).get('classes', []))} separable colours, "
          f"{sum(e.get('band_count', 0) for e in doc.get('bands_by_class', []))} bands"
          + (f", {len(bad)} problem(s)" if bad else ""))
    return 1 if bad else 0


def report() -> int:
    doc = load(RECORD)
    print("Wright 1834 legend — nine chips\n")
    for chip in doc["chips"]:
        print(f"  {chip['chip']}  rgb {tuple(chip['median_rgb'])!s:18s} "
              f"sd {tuple(chip['sd_rgb'])!s:22s} {chip['legend']['reading']}")
    print("\n  separable colours:", doc["separability"]["classes"])
    print("  ", doc["separability"]["finding"])
    c = doc["cross_check_school_section"]
    print("\n  chip 5 against the committed section 16 — each side inside its band:")
    for k in ("north", "south", "east", "west"):
        print(f"     {k:6s} committed {c[k]['committed_m']:9.1f}  band {c[k]['band_span_m']}"
              f"  outside by {c[k]['outside_band_by_m']} m")
    print("\nbands on the sheet\n")
    for entry in doc["bands_by_class"]:
        print(f"  class {entry['class']} rgb {tuple(entry['class_colour_rgb'])} — "
              f"{entry['band_count']} band(s)")
        for band in entry["bands"]:
            flag = "  off-map" if band["off_map"] else ("  legend key" if band["in_legend"] else "")
            b, m = band["box_px"], band["box_local_m"]
            print(f"     {band['cells']:5d} cells  px [{b['x0']},{b['y0']}]-[{b['x1']},{b['y1']}]"
                  f"  E {m['e0']:.0f}..{m['e1']:.0f}  N {m['n0']:.0f}..{m['n1']:.0f}{flag}")
    return 0


def self_test() -> int:
    base = load(RECORD)
    failures = 0

    def fires(label, mutate):
        nonlocal failures
        doc = json.loads(json.dumps(base))
        mutate(doc)
        import io, contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = check_properties(doc)
        if rc == 0:
            print(f"  DID NOT FIRE: {label}")
            failures += 1
        else:
            print(f"  ok: {label}")

    def bump_median(doc):
        doc["chips"][2]["median_rgb"] = [int(v) + 40 for v in doc["chips"][2]["median_rgb"]]

    fires("a chip median moved without its separation matrix", bump_median)
    fires("a separation entry edited by hand",
          lambda d: d["separation_rgb"][0].__setitem__(1, 999.9))
    fires("the class grouping edited to make nine colours look separable",
          lambda d: d["separability"].__setitem__("classes", [[i] for i in range(1, 10)]))
    fires("a legend line reworded in the record",
          lambda d: d["chips"][4]["legend"].__setitem__("reading", "Wolcott's Addition"))
    fires("a chip box moved off its frozen row",
          lambda d: d["chips"][0]["box_px"].__setitem__("y0", 3700))
    fires("a band's local metres edited away from its own pixels",
          lambda d: d["bands_by_class"][0]["bands"][0]["box_local_m"].__setitem__("e0", -1.0))
    fires("a band marked on-map whose centroid is off it",
          lambda d: d["bands_by_class"][0]["bands"][0].__setitem__("off_map",
                     not d["bands_by_class"][0]["bands"][0]["off_map"]))
    fires("the school-section cross-check edited away from the bands",
          lambda d: d["cross_check_school_section"]["east"].__setitem__(
              "band_mid_m", 0.0))
    fires("the raster block drifting from the registration's",
          lambda d: d["raster"].update(sha256="0" * 64))
    print(f"{'FAIL' if failures else 'ok'}: self-test, {failures} assertion(s) did not fire")
    return 1 if failures else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--check-properties", action="store_true")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.build:
        return build()
    if args.check_properties:
        return check_properties()
    if args.report:
        return report()
    if args.self_test:
        return self_test()
    ap.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
