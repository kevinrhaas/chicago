#!/usr/bin/env python3
"""measure_fort_works_plate.py — where does `p4_0` actually put the fort's raised works?

T-0095, and the second time in two days that a Fort Dearborn parcel has been seeded
by a plate read with the eye. T-0094 was told "the plate draws the pickets pointed"
and measurement gave a flat cap at 0.45 px rms. T-0095 was told this:

    `p4_0` draws the corner works RISING ABOVE the curtain with their own pyramidal
    roofs and small lanterns, and a log-faced work over the gate in the middle of
    the wall.

Half of that sentence is right. There is one plate, and it draws **two** log-faced
works with pyramidal roofs and lanterns, and **both of them stand over the middle of
the wall**. Neither is at an angle. The reading that produced the ticket saw two
roofed lanterned works, knew the record puts works at two angles, and joined them.

**What the plate actually draws, measured below.** The stockade's east angle is at
column 319 and the picket crest — 42.4 px high — is the skyline from there, rising
0.04 curtain heights over its first twenty columns: the corner is drawn PLAIN, which
is what the record says of that angle (`bastion_corners` is `nw` and `se`; the 1830
plan leaves the north-east plain). Over 862 px of drawn wall the two raised works
stand at **0.435 and 0.521 of the run**, 2.25 and 2.96 curtain heights up — the two
tallest things on the sheet by two thirds of a curtain height. **A corner work stands
at 0.000 or 1.000.** The nearer of the two is a quarter of the wall — some 23 m, three
bastion lengths — from the nearest angle.

**And the west angle is not evidence, because the plate does not show it.** The crest
is last legible at column 1181; past it the silhouette stands 25 px higher again and
that material is green by 12.1 against 8.0 over the fort itself. It is the tree
outside the walls. The north-west bastion — the one angle on this face the record
actually puts a work at — is behind it. The plate has nothing to say about its
height, and this file says so rather than reading a number out of leaves.

WHY THE PLATE COULD NOT HAVE SETTLED IT ANYWAY
----------------------------------------------
`data/exclusions.json` already pins one feature of this plate to the FIRST fort: the
flagstaff, which the T-0044 pass refused for exactly this reason — the passage it
comes from ends *"Such was the old Fort previous to 1812"*. The same entry lists that
fort's own most distinctive feature as **two blockhouses**, and two roofed lanterned
log towers is what this plate raises. They are in the wrong place for the first fort
too (it had them at the south-east and north-west angles, not amidships), so the sheet
matches neither fort's documented arrangement. It is a retrospective artist's
impression that has taken features from both. **Nothing new is massed at this fort on
its authority** — not at the angles and not over the gate.

WHAT IS MEASURED, AND HOW THE FLAG IS KEPT OUT OF IT
-----------------------------------------------------
The plate is a coloured lithograph on grained paper, so everything is done on a
Gaussian-blurred luminance and against each column's OWN sky, sampled from a band
well above the fort — a single global threshold reads the left half of the sheet
darker than the right and walks the skyline down a slope that is in the paper.

A pixel is `structure` where it is `SKY_DROP` below its column's sky. That mask is
then **eroded by a horizontal window `MIN_MASS_PX` wide**: anything narrower than
that is a LINE rather than a mass, which deletes the flagstaff, the finials and the
engraver's hatching, and leaves every roof, wall and tower. What survives is then
reduced to the single connected component that touches the picket crest — which drops
the flag, now that the mast holding it up has been eroded away, and the ink blemish
floating in the sky at (970, 250). The silhouette of the fort is the top of what is
left.

The curtain crest is read where it IS the skyline. There are exactly two such runs —
the wall inboard of the east angle, before the first range begins, and the wall past
the last range at the west end — and they are picked out by the one property that
separates them from the bank horizons either side of the fort, which are flat runs at
a similar level: **the fort stands between them.** The pair is required to be at least
300 px apart, level to within 3 px of each other, and to have 95 % of the silhouette
between them ABOVE them. A first version of this took the lowest flat run on the sheet
and measured the bank.

Note that erosion trims `MIN_MASS_PX // 2` from each end of every mass, so the angle
comes out six columns inboard of the ink. That is a constant bias on both ends of the
wall and it cancels in every ratio below; it is stated rather than corrected, because
correcting it would mean claiming a sub-pixel edge on a lithograph.

THE THREE ASSERTIONS
--------------------
 1. **The highest point of the fort's silhouette stands in the middle third of the
    drawn wall.** It is the right-hand work's lantern. A corner work would put it at
    an end.
 2. **The angle the plate draws unoccluded is drawn plain** — over `ANGLE_PROBE_PX`
    of wall inboard of the east angle the silhouette stays within `RISE_TOL` of the
    curtain crest. And the west angle is reported as OCCLUDED, never as measured.
 3. **The record has not been built to the misreading.** `ne` — the angle this plate
    draws plain — stays out of `bastion_corners`, and no form attribute raises a
    corner work above `picket_height_m`. This is the assertion that will fire if a
    future run acts on the sentence at the top of this file.

**The reading is BANKED** in `fort_works_plate_baseline.json`, for two reasons. CI
installs `jsonschema` and `pyproj` and no image library, and a gate that skipped
the plate in silence there would be worth nothing; and a detector edit that
quietly moves the reading is a thing this project has been bitten by. So with
Pillow the sheet is re-read and checked against the bank, and without it the third
assertion — the one about the RECORD, which needs no image — runs on the banked
reading and says out loud that it did.

    tools/measure_fort_works_plate.py                  the reading
    tools/measure_fort_works_plate.py --gate           exit 1 on any of the three
    tools/measure_fort_works_plate.py --self-test      break each assertion, in memory
    tools/measure_fort_works_plate.py --write-baseline re-derive the banked reading
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLATE = (ROOT / "data" / "sources" / "assets" / "prefire_views_kevin_2026_08" / "p4_0.png")
RECORD = ROOT / "data" / "structures" / "fort_dearborn_palisade.json"
BASELINE = Path(__file__).resolve().parent / "fort_works_plate_baseline.json"

# The window the fort occupies on the sheet. Generous on every side: it is a search
# box, not a measurement, and every number below is found inside it rather than
# assumed. The sheet is 1538 x 859.
FORT_X0, FORT_X1 = 285, 1235
SKY_Y0, SKY_Y1 = 40, 120          # clear sky in every column of the window
SEARCH_Y0, SEARCH_Y1 = 130, 470   # above the tallest finial, below the bank

BLUR_SIGMA = 1.6                  # kills the paper grain, keeps every drawn edge
SKY_DROP = 32.0                   # luminance below a column's own sky to read as ink

# One millimetre of drawn wall is about 0.06 px here. Twelve pixels is three drawn
# pickets: below that a mark is a line — a mast, a finial, a hatching stroke — and
# this file is measuring MASSES. Erosion at this width is what keeps the flagstaff
# out of the silhouette without anyone having to name its columns.
MIN_MASS_PX = 12

RISE_TOL = 0.25          # curtain heights: within this of the crest is "plain wall"
ANGLE_PROBE_PX = 20      # how far inboard of an angle assertion 2 looks
MIDDLE_LO, MIDDLE_HI = 1.0 / 3.0, 2.0 / 3.0

# Reading the picket foot: how far the sheet has to move away from the drawn face
# of the wall before the ground under it has begun. The two exposed runs differ by
# about ninety luminance levels, so this is a CHANGE and not a level.
FOOT_DELTA = 35

# Peak reporting only — nothing is asserted on these. A peak is the lowest y in a
# window this wide, and two peaks nearer than the separation are one peak.
PEAK_WINDOW = 12
PEAK_SEPARATION_PX = 40


class PlateError(RuntimeError):
    """The plate cannot be read into a measurement."""


class NoReader(PlateError):
    """Pillow is not installed, so the SHEET cannot be re-read here.

    Not the same thing as a failure, and it must not be reported as one. CI
    installs `jsonschema` and `pyproj` and no image library, and the workflow
    files are out of scope for an overnight run — so the reading is BANKED in
    `fort_works_plate_baseline.json` and the gate stands on that when it cannot
    open the sheet. What survives without Pillow is the assertion that matters
    most anyway: the third one, which is about the RECORD and not about the
    lithograph. A committed plate does not change; a record does.
    """


# ------------------------------------------------------------------ the plate

def _luminance():
    try:
        from PIL import Image, ImageFilter  # noqa: PLC0415
    except ImportError as e:  # pragma: no cover
        raise NoReader(f"Pillow is not installed: {e}") from e
    if not PLATE.exists():
        raise PlateError(f"{PLATE.relative_to(ROOT)} is missing")
    img = Image.open(PLATE).convert("L").filter(ImageFilter.GaussianBlur(BLUR_SIGMA))
    w, h = img.size
    # `tobytes()` rather than `getdata()`: mode "L" is one byte per pixel in
    # row-major order, so this is the same numbers without the deprecation
    # warning Pillow prints into the middle of the gate's output.
    px = img.tobytes()
    return [list(px[y * w:(y + 1) * w]) for y in range(h)], w, h


def _erode_rows(mask: list, width: int) -> list:
    """Erode each row by a horizontal window `width` wide.

    A pixel survives only if the whole window centred on it is ink, so a mark
    narrower than the window disappears and a broad one keeps all but `width // 2`
    of each edge. Done with a running sum rather than a convolution because this
    has to work in a bare Python 3.11 with no numpy in the commit gate.
    """
    half = width // 2
    out = []
    for row in mask:
        n = len(row)
        run, acc = [0] * (n + 1), 0
        for i, v in enumerate(row):
            acc += 1 if v else 0
            run[i + 1] = acc
        keep = [False] * n
        for i in range(n):
            a, z = max(0, i - half), min(n, i + half + 1)
            keep[i] = (run[z] - run[a]) == (z - a)
        out.append(keep)
    return out


def _largest_component(mask: list, seeds: list) -> list:
    """The connected component of `mask` reachable from `seeds` (4-connected)."""
    h, w = len(mask), len(mask[0])
    seen = [[False] * w for _ in range(h)]
    stack = [(y, x) for y, x in seeds if 0 <= y < h and 0 <= x < w and mask[y][x]]
    for y, x in stack:
        seen[y][x] = True
    while stack:
        y, x = stack.pop()
        for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            ny, nx = y + dy, x + dx
            if 0 <= ny < h and 0 <= nx < w and mask[ny][nx] and not seen[ny][nx]:
                seen[ny][nx] = True
                stack.append((ny, nx))
    return seen


def read_plate() -> dict:
    """Everything this file measures off `p4_0`, in sheet pixels."""
    lum, w, h = _luminance()
    xs = range(FORT_X0, min(FORT_X1, w))

    sky = {x: sum(lum[y][x] for y in range(SKY_Y0, SKY_Y1)) / (SKY_Y1 - SKY_Y0)
           for x in xs}

    # ink mask over the search window, per column against its own sky
    ys = list(range(SEARCH_Y0, min(SEARCH_Y1, h)))
    raw = [[lum[y][x] < sky[x] - SKY_DROP for x in xs] for y in ys]
    eroded = _erode_rows(raw, MIN_MASS_PX)

    # The picket crest is the lowest thing in the window that runs the whole width
    # of the fort, so seed the component from the BOTTOM row of the search band and
    # keep what is connected to it. The flag, its mast eroded away, is not.
    seeds = [(len(ys) - 1, i) for i in range(len(list(xs)))]
    solid = _largest_component(eroded, seeds)

    cols = list(xs)
    top = {}
    for i, x in enumerate(cols):
        for j in range(len(ys)):
            if solid[j][i]:
                top[x] = ys[j]
                break

    # THE CREST, and it is found rather than assumed. The picket top is the skyline
    # in exactly two places — the wall inboard of the east angle, before the first
    # range begins, and the wall beyond the last range at the west end. Both are
    # flat runs at the same level, they are most of the fort apart, and EVERYTHING
    # BETWEEN THEM STANDS ABOVE THEM: that last property is the fort, and it is what
    # separates the crest from the bank horizons either side of it, which are also
    # flat runs and were what a first version of this picked.
    flat = []
    run = []
    for x in cols:
        y = top.get(x)
        if y is None:
            if len(run) >= 10:
                flat.append(run)
            run = []
            continue
        if run and abs(y - top[run[-1]]) <= 2:
            run.append(x)
        else:
            if len(run) >= 10:
                flat.append(run)
            run = [x]
    if len(run) >= 10:
        flat.append(run)

    def level(r):
        return sum(top[x] for x in r) / len(r)

    best = None
    for i, left in enumerate(flat):
        for right in flat[i + 1:]:
            if right[0] - left[-1] < 300:
                continue
            if abs(level(left) - level(right)) > 3:
                continue
            c = (level(left) + level(right)) / 2.0
            between = [top[x] for x in range(left[-1] + 1, right[0]) if x in top]
            if not between:
                continue
            above = sum(1 for y in between if y <= c - 4)
            if above < 0.95 * len(between):
                continue
            span = right[-1] - left[0]
            if best is None or span > best[0]:
                best = (span, left, right, c)
    if best is None:
        raise PlateError("no pair of crest runs with the fort standing between them — "
                         "the picket crest cannot be read")
    _, crest_left, crest_right, crest_y = best
    crest_run = crest_left
    east = crest_left[0]
    west_last = crest_right[-1]

    # THE CURTAIN'S OWN HEIGHT: crest down to the dark line the pickets stand on.
    # Read as a CHANGE against the picket band's own tone rather than against the
    # sky, because the two exposed runs are drawn at opposite ends of the sheet's
    # range — the east run is in shadow and darker than the ground under it, the
    # west run is the whitewashed face and lighter. A rule that only looked for a
    # darkening would read one of them and silently miss the other.
    heights = []
    for x in list(crest_left) + list(crest_right):
        band = sorted(lum[y][x] for y in range(int(crest_y) + 3, int(crest_y) + 13))
        face = band[len(band) // 2]
        for y in range(int(crest_y) + 15, min(int(crest_y) + 75, h - 1)):
            if abs(lum[y][x] - face) >= FOOT_DELTA:
                heights.append(y - crest_y)
                break
    if not heights:
        raise PlateError("the picket foot is not readable on either exposed run, so the "
                         "curtain height — the unit everything below is in — has no value")
    heights.sort()
    curtain_px = heights[len(heights) // 2]

    # Where foliage closes over the wall: a column is occluded where the sheet is
    # green-dominant anywhere between the crest and the bank.
    from PIL import Image  # noqa: PLC0415
    rgb = Image.open(PLATE).convert("RGB")
    px = rgb.load()
    # Only the band the WALL occupies counts: the prairie below the bank is green
    # everywhere and says nothing about whether the stockade is visible.
    # WHAT STANDS WHERE THE CREST STOPS. The west angle is the one the record
    # actually puts a work at, and the reason this file will not read a height there
    # is that the crest is last legible at `west_last` and the silhouette rises again
    # immediately afterwards. Asked what that material IS: its green excess against
    # the sheet's own sky, over the same band of wall. A tree is green; a log tower
    # in shadow is not, and a first version of this that tested hue alone called the
    # middle of the fort foliage — the sky on this sheet is itself green-dominant by
    # about fourteen levels.
    def _green(x0, x1):
        vals = []
        for x in range(x0, x1):
            if x not in top:
                continue
            for y in range(int(crest_y) - 60, int(crest_y) + 6):
                r, g, bl = px[x, y]
                if lum[y][x] < sky[x] - 40:
                    vals.append(g - (r + bl) / 2.0)
        return round(sum(vals) / len(vals), 2) if vals else None

    beyond = (west_last + 1, min(west_last + 61, FORT_X1))
    beyond_rise = [round((crest_y - top[x]) / 1.0, 1)
                   for x in range(*beyond) if x in top]

    run_px = (west_last - east) if west_last else float("nan")
    return {
        "sheet": [w, h],
        "crest_y": round(crest_y, 2),
        "curtain_px": round(curtain_px, 2),
        "east_angle_x": east,
        "last_crest_x": west_last,
        "wall_run_px": run_px,
        "west_crest_run": [crest_right[0], crest_right[-1]],
        "beyond_crest_x": list(beyond),
        "beyond_crest_rise_px": round(sum(beyond_rise) / len(beyond_rise), 1)
                                if beyond_rise else None,
        "beyond_crest_green": _green(*beyond),
        "fort_green": _green(east, west_last),
        "silhouette": top,
        "crest_run": [crest_run[0], crest_run[-1]],
    }


def peaks(plate: dict, limit: int = 6) -> list:
    """The tallest separated peaks of the fort's silhouette, where each one stands.

    Deliberately does NOT try to say which peaks are works and which are ranges.
    A first version did, on a rise threshold, and the left-hand work clears the
    right-hand range's ridge by seven per cent of a curtain height — a number no
    threshold should be asked to sit inside. Nothing here is asserted on; the
    assertions use the single HIGHEST point, which beats everything else on the
    sheet by two thirds of a curtain height. This is the reading the memo cites.
    """
    crest, ch = plate["crest_y"], plate["curtain_px"]
    top, east, run = plate["silhouette"], plate["east_angle_x"], plate["wall_run_px"]
    cols = sorted(top)
    local = [x for x in cols
             if top[x] == min(top[u] for u in range(x - PEAK_WINDOW, x + PEAK_WINDOW + 1)
                              if u in top)]
    out = []
    for x in sorted(local, key=lambda u: top[u]):
        if any(abs(x - p["apex_x"]) < PEAK_SEPARATION_PX for p in out):
            continue
        y = top[x]
        wide = [u for u in cols if abs(u - x) < 200 and top[u] <= y + 2]
        out.append({
            "apex_x": x, "apex_y": y,
            "rise_curtains": round((crest - y) / ch, 2),
            "width_px": (max(wide) - min(wide) + 1) if wide else 1,
            "along_wall": round((x - east) / run, 3),
        })
        if len(out) >= limit:
            break
    return out


# ----------------------------------------------------------------- assertions

def assess(plate: dict, found: list, record: dict) -> dict:
    crest, ch = plate["crest_y"], plate["curtain_px"]
    top, east, run = plate["silhouette"], plate["east_angle_x"], plate["wall_run_px"]

    highest_x = min((x for x in top if top[x] is not None), key=lambda x: top[x])
    highest = {"x": highest_x, "y": top[highest_x],
               "along_wall": round((highest_x - east) / run, 3)}

    probe = [x for x in range(east, east + ANGLE_PROBE_PX) if x in top]
    angle_rise = max(((crest - top[x]) / ch for x in probe), default=0.0)

    form = record["phases"][0]["form"]
    corners = list(form.get("bastion_corners", {}).get("value", []))
    picket_h = float(form["picket_height_m"]["value"])
    # The signature of the misreading: a corner work given a height, a roof, a
    # lantern or a storey. `bastion_length_m` and `bastion_projection_m` are the
    # work's PLAN and are not that — the 1830 plan draws both and this file has no
    # quarrel with either.
    raised = {k: v.get("value") for k, v in form.items()
              if k.startswith("bastion_")
              and any(w in k for w in ("height", "roof", "lantern", "stor", "cap"))}
    return {
        "highest_point": highest,
        "east_angle_rise_curtains": round(angle_rise, 3),
        "east_angle_probe_px": ANGLE_PROBE_PX,
        "bastion_corners": corners,
        "picket_height_m": picket_h,
        "corner_attrs_above_curtain": raised,
        "works": found,
    }


def assess_from(base: dict, record: dict) -> dict:
    """The same assessment, from a BANKED plate reading and the live record."""
    form = record["phases"][0]["form"]
    return {
        "highest_point": {"along_wall": base["highest_along_wall"]},
        "east_angle_rise_curtains": base["east_angle_rise_curtains"],
        "east_angle_probe_px": ANGLE_PROBE_PX,
        "bastion_corners": list(form.get("bastion_corners", {}).get("value", [])),
        "picket_height_m": float(form["picket_height_m"]["value"]),
        "corner_attrs_above_curtain": {
            k: v.get("value") for k, v in form.items()
            if k.startswith("bastion_")
            and any(w in k for w in ("height", "roof", "lantern", "stor", "cap"))},
        "works": [],
    }


def findings(a: dict) -> list:
    bad = []
    f = a["highest_point"]["along_wall"]
    if not MIDDLE_LO <= f <= MIDDLE_HI:
        bad.append(f"the highest point of the fort's silhouette stands at {f:.3f} of the "
                   f"drawn wall, outside the middle third — p4_0 would then be putting a "
                   f"raised work at an angle after all, and this file's reading is wrong")
    if a["east_angle_rise_curtains"] > RISE_TOL:
        bad.append(f"the east angle is no longer drawn plain: the silhouette stands "
                   f"{a['east_angle_rise_curtains']:.2f} curtain heights above the crest "
                   f"within {a['east_angle_probe_px']} px of the corner")
    if "ne" in a["bastion_corners"]:
        bad.append("the record now puts a corner work at the NORTH-EAST angle — the one "
                   "angle p4_0 draws unoccluded, and draws plain. Andreas and Hubbard both "
                   "give nw and se; the 1830 plan leaves the north-east plain")
    if a["corner_attrs_above_curtain"]:
        bad.append(f"the record now gives a corner work a height, roof or lantern of its "
                   f"own: {sorted(a['corner_attrs_above_curtain'])}, over a "
                   f"{a['picket_height_m']} m curtain. p4_0 raises nothing at either angle "
                   f"it draws, and it is not evidence that could — see this file's head")
    return bad


# ------------------------------------------------------------------ self-test

def self_test(base: dict, re_read: bool) -> int:
    """Break each assertion in memory and confirm it is noticed.

    Runs on the banked reading when there is no image library, because the three
    assertions are about the ASSESSMENT and none of them needs the sheet open —
    a self-test that quietly did nothing in CI would be worse than none.
    """
    ok = True

    def case(label, mutate, expect):
        nonlocal ok
        a = json.loads(json.dumps(base))
        mutate(a)
        got = findings(a)
        hit = any(expect in g for g in got)
        print(f"   {'ok  ' if hit else 'FAIL'}  {label}")
        if not hit:
            print(f"          expected {expect!r}, got {got}")
            ok = False

    if findings(base):
        print("   FAIL  the plate and the record do not agree today, so the self-test "
              "has no clean starting point")
        for g in findings(base):
            print(f"          {g}")
        return 1
    print("   ok    the plate and the record agree today"
          + ("" if re_read else " (on the BANKED reading — no image library here)"))

    case("a highest point at the east angle is caught",
         lambda a: a["highest_point"].update(along_wall=0.02), "outside the middle third")
    case("a highest point at the west angle is caught",
         lambda a: a["highest_point"].update(along_wall=0.98), "outside the middle third")
    case("a work rising at the drawn angle is caught",
         lambda a: a.update(east_angle_rise_curtains=1.6), "no longer drawn plain")
    case("a corner work added at the north-east angle is caught",
         lambda a: a["bastion_corners"].append("ne"), "NORTH-EAST angle")
    case("a corner work raised above the curtain is caught",
         lambda a: a.update(corner_attrs_above_curtain={"bastion_height_m": 7.4}),
         "a height, roof or lantern of its own")

    edge = json.loads(json.dumps(base))
    edge["highest_point"]["along_wall"] = MIDDLE_HI - 0.001
    inside = not findings(edge)
    print(f"   {'ok  ' if inside else 'FAIL'}  the edge of the middle third is not a fault")
    ok = ok and inside

    print("\nSELF-TEST " + ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


# ----------------------------------------------------------------- baseline

# What may move between two readings of the SAME committed lithograph before it
# means the detector changed rather than the noise did. Everything here is in
# sheet pixels except the last, which is a fraction of the wall run.
DRIFT = {"crest_y": 1.0, "curtain_px": 1.5, "east_angle_x": 2.0,
         "last_crest_x": 2.0, "wall_run_px": 3.0, "highest_along_wall": 0.010}


def banked() -> dict:
    if not BASELINE.exists():
        raise PlateError(f"{BASELINE.name} is missing, so there is no banked reading of the "
                         f"plate to stand on")
    return json.loads(BASELINE.read_text(encoding="utf-8"))["reading"]


def reading_of(plate: dict, a: dict) -> dict:
    return {"crest_y": plate["crest_y"], "curtain_px": plate["curtain_px"],
            "east_angle_x": plate["east_angle_x"], "last_crest_x": plate["last_crest_x"],
            "wall_run_px": plate["wall_run_px"],
            "east_angle_rise_curtains": a["east_angle_rise_curtains"],
            "highest_along_wall": a["highest_point"]["along_wall"],
            "beyond_crest_rise_px": plate["beyond_crest_rise_px"],
            "beyond_crest_green": plate["beyond_crest_green"],
            "fort_green": plate["fort_green"]}


def drift(fresh: dict, base: dict) -> list:
    out = []
    for k, tol in DRIFT.items():
        if k not in fresh or k not in base:
            continue
        if abs(float(fresh[k]) - float(base[k])) > tol:
            out.append(f"the plate now reads {k} = {fresh[k]} where the banked reading is "
                       f"{base[k]} (tolerance {tol}). The lithograph is committed and cannot "
                       f"have changed, so the detector has — re-derive with "
                       f"--write-baseline and say in the commit what moved")
    return out


def show(plate: dict, found: list, a: dict) -> None:
    print(f"   p4_0: the stockade's east angle at x={plate['east_angle_x']}, the last "
          f"unoccluded crest at x={plate['last_crest_x']}, "
          f"{plate['wall_run_px']} px of drawn wall")
    print(f"   the picket crest sits at y={plate['crest_y']:.1f} and stands "
          f"{plate['curtain_px']:.1f} px high")
    if plate.get("beyond_crest_rise_px") is not None:
        print(f"   past the last crest the silhouette stands "
              f"{plate['beyond_crest_rise_px']:.0f} px higher again and that material is "
              f"green by {plate['beyond_crest_green']:.1f} against {plate['fort_green']:.1f} "
              f"over the fort itself — it is the tree outside the walls, and the "
              f"NORTH-WEST angle is behind it. The plate cannot speak to that angle.")
    print("   the tallest peaks of the silhouette, tallest first "
          "(0.000 = the east angle, 1.000 = the west):")
    for pk in found:
        print(f"     {pk['rise_curtains']:5.2f} curtain heights up, "
              f"{pk['width_px']:4d} px wide, at {pk['along_wall']:.3f} of the wall")
    print(f"   the highest point of the silhouette is at "
          f"{a['highest_point']['along_wall']:.3f} of the wall — an angle would be "
          f"0.000 or 1.000")
    print(f"   the east angle rises {a['east_angle_rise_curtains']:.3f} curtain heights "
          f"over its first {ANGLE_PROBE_PX} px: the corner is drawn plain")


# ---------------------------------------------------------------------- main

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--gate", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--write-baseline", action="store_true",
                    help="re-derive the banked plate reading (needs Pillow)")
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    record = json.loads(RECORD.read_text(encoding="utf-8"))

    plate = found = None
    try:
        plate = read_plate()
        found = peaks(plate)
    except NoReader as e:
        if args.write_baseline:
            print(f"   FAIL cannot write the baseline: {e}")
            return 1
    except PlateError as e:
        print(f"   FAIL {e}")
        return 1

    if plate is None:
        # No image library. Assertion 3 still runs, against the banked reading of
        # assertions 1 and 2. Said out loud, every time, so that a green line here
        # is never mistaken for the sheet having been re-read.
        base = banked()
        a = assess_from(base, record)
        if args.self_test:
            return self_test(a, re_read=False)
        bad = findings(a)
        if not args.quiet or bad:
            print("   Pillow is not installed, so the LITHOGRAPH WAS NOT RE-READ. Standing "
                  f"on the banked reading in {BASELINE.name}: the highest point of the "
                  f"silhouette at {base['highest_along_wall']:.3f} of the wall, the east "
                  f"angle rising {base['east_angle_rise_curtains']:.3f} curtain heights. "
                  "Only the assertion about the RECORD is live here.")
        for g in bad:
            print(f"   FAIL {g}")
        return 1 if (bad and args.gate) else 0

    a = assess(plate, found, record)
    fresh = reading_of(plate, a)

    if args.write_baseline:
        BASELINE.write_text(json.dumps({
            "$note": "T-0095. The banked reading of data/sources/assets/"
                     "prefire_views_kevin_2026_08/p4_0.png by "
                     "tools/measure_fort_works_plate.py. The plate is committed and cannot "
                     "change, so this exists for two reasons: CI installs no image library "
                     "and would otherwise skip the plate half in silence, and a detector "
                     "edit that quietly moves the reading is a thing this project has been "
                     "bitten by. Regenerate with --write-baseline, and only ever with the "
                     "reason in the commit.",
            "reading": fresh,
            "peaks": found,
        }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        show(plate, found, a)
        print(f"\n   wrote {BASELINE.name}")
        return 0

    if args.self_test:
        return self_test(a, re_read=True)

    if args.json:
        out = dict(a)
        out["plate"] = {k: v for k, v in plate.items() if k != "silhouette"}
        print(json.dumps(out, indent=2, sort_keys=True))
        return 0

    bad = findings(a) + drift(fresh, banked())
    if not args.quiet or bad:
        show(plate, found, a)
    for g in bad:
        print(f"   FAIL {g}")
    if not bad and not args.quiet:
        print("   p4_0 raises no work at either angle it draws, and the record has not "
              "been built as though it did")
    return 1 if (bad and args.gate) else 0


if __name__ == "__main__":
    sys.exit(main())
