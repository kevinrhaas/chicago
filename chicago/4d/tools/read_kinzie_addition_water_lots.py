#!/usr/bin/env python3
"""Read the river-front water lots of Kinzie's Addition off Wright's 1834 survey.

    tools/read_kinzie_addition_water_lots.py               print the reading
    tools/read_kinzie_addition_water_lots.py --write       write the trace
    tools/read_kinzie_addition_water_lots.py --check       cheap: re-derive every metre
                                                           from the pixels committed beside it
    tools/read_kinzie_addition_water_lots.py --check-sheet  re-open the raster and re-read it

A LOT STRIP IS NOT A BLOCK GRID, and that is the whole point of reading it
separately. Everything else Wright plats north of the river is a module — a tier
pitch and a column pitch, two families of parallel rules, blocks between them.
The ground between the Addition's south tier and the water is not that: it is one
run of narrow parcels laid side by side against a curving bank, each as wide as
the draughtsman needed and as deep as the bank left room for, numbered straight
through from the Original Town's line to the lake. Fitting a grid to it would
invent regularity the sheet does not draw. So this reading carries the run's own
geometry — a front line, a back line, the division strokes between the parcels —
and reports what a lot strip has instead of a module: a frontage per lot, and the
spread of those frontages.

THE SHEET is the National Archives / Historic Urban Plans facsimile registered as
`wright_1834_nara_hup` (5050 x 6628 px at 600 dpi), the same raster and the same
affine `tools/read_kinzie_addition_streets.py` reads the Addition's streets on, so
the two readings can be subtracted from each other without a scan-to-scan hop.

HOW THE RUN IS FOUND. Nothing here is picked off a crop by eye except one seed
point and one bearing. From that seed a tangential follower walks the strip's
FRONT line — the drawn river bank, which is the strongest continuous stroke in
this corner of the sheet — one pixel at a time, re-centring on the darkest line
within two pixels of its projected step and turning by a damped fraction of the
correction. That walk defines an arc-length coordinate `s` along the run and a
perpendicular coordinate `t` northward from the front line, and everything below
is measured in that frame.

HOW A DIVISION STROKE IS TOLD FROM A NUMERAL. Both are ink inside the strip, and
a profile that sums darkness cannot tell them apart — Wright's figures are as
black as his rules. What separates them is that a division stroke crosses the
WHOLE depth of the parcel and a figure does not. So the observable here is the
MINIMUM darkness over the depth band rather than the sum: a stroke scores high
because it is dark at every t, a figure scores near zero because it is blank
above or below itself. The strokes also lean — hard, in the wedge east of the
bend, where they stand square to the back line rather than to the bank — so the
minimum is taken over a small fan of shears and the best-scoring shear is kept
and reported with each division.

WHAT THIS READING SETTLES AND WHAT IT REFUSES. It settles the run's shape, its
length, where each division stands, and therefore how many parcels the sheet
draws and how wide each is relative to its neighbours. It does NOT settle the
absolute width of a lot in feet on the ground: the NA fit carries 16.19 m RMS and
its two axis scales differ by 5.2 per cent, so a frontage is reported both raw and
scaled by the factor the committed street reading measured for this method against
the Original Town's platted 80 ft corridors on this same sheet. And it refuses the
figures: at this scan's resolution the terminal run and the three parcels east of
the break are legible and the rest are not. What the reading does instead is
COUNT, and the count closes — see `numbering` below.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPO = ROOT.parent.parent
GCP = ROOT / "data/traces/gcp/wright_1834_nara_hup_gcps.json"
STREETS = ROOT / "data/traces/kinzie_addition_street_grid.json"
OUT = ROOT / "data/traces/kinzie_addition_water_lots.json"
FT = 0.3048

# ------------------------------------------------------------- the walk
#
# The one thing read by eye. The seed sits on the drawn bank at the run's west
# terminus, where the Original Town's east line meets the water; the bearing is
# the slope the bank leaves it on. Crop to check it: (2890, 2330)-(3000, 2400).
SEED_PX = (2932.0, 2371.0)
SEED_SLOPE = -0.70          # raster dy/dx at the seed
STEPS = 930                 # one pixel each; the run ends on the harbour line
FOLLOW_HALF_PX = 2.0        # how far off its projected step the walk may re-centre
FOLLOW_GRAIN_PX = 0.25
FOLLOW_SMOOTH = 0.12        # damping on the turn, so a numeral cannot steer the walk
FOLLOW_TANGENT = (-4.0, -2.0, 0.0, 2.0, 4.0)

# ------------------------------------------------------- the division strokes
DEPTH_BAND_PX = (4, 20)     # inside the front line, clear of both drawn edges
SHEARS = tuple(round(i * 0.15, 2) for i in range(-9, 10))
DIVISION_MIN = 25.0         # darkness units (150 - grey), on the minimum over depth
DIVISION_WINDOW = 8         # a division must be the strongest within +-8 px of arc
DIVISION_MERGE = 15         # two peaks closer than this are one stroke

# ------------------------------------------------------------- the back line
BACK_SEARCH_PX = (10, 54)
BACK_MIN = 30.0
BACK_STATION_PX = 10        # report a depth every this many pixels of arc
STATION_PX = BACK_STATION_PX

# The detector is re-run at each of these to MEASURE its own instability rather than
# to claim a number: the spread it returns is written into the file beside the strokes.
SETTINGS = ((DIVISION_MIN, DIVISION_WINDOW, DIVISION_MERGE),
            (25.0, 6, 12), (25.0, 7, 14), (20.0, 6, 12), (30.0, 8, 15))

# ---------------------------------------------------------------- what was read
#
# PARCELS is not the detector's count. It is the count the sheet's own terminal
# figures force: the westernmost cell is lettered 1 and the easternmost 35, the run
# is continuous between them, and the figures 15, 16 and 17 land where a continuous
# count from the west puts them.
PARCELS = 35
BREAK_LOT = 14

# The figures legible at 8x to 14x on the facsimile, with the crop each was read on.
DOCUMENTED = [1, 15, 16, 17, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35]
CROPS = {
    "1": [2925, 2280, 3070, 2385],
    "15-17": [3160, 2090, 3290, 2185],
    "26-35": [3500, 1950, 3900, 2220],
}

BREAK_NOTE = (
    "Between the thirteenth cell of the run and the cell the sheet letters 15, the "
    "strip's back line falls to meet its front line and rises again about forty pixels "
    "further east: a reach of bank with no back line over it, found here by the back-line "
    "search returning nothing at three consecutive stations. The reach is not a tear — the "
    "paper is whole, the bank stroke is unbroken and the wash carries across it — and this "
    "reading does not say what it is. What it does say is that the run's own figures need "
    "that reach to carry lot 14: the cell east of it is lettered 15, the cell at the far "
    "end is lettered 35, and a continuous count west to east reaches both only with the "
    "break counted in. Lot 14 is therefore INFERRED, and is the only number in this file "
    "that is inferred from a count rather than refused outright."
)


def _sheet():
    g = json.loads(GCP.read_text())
    img = REPO / g["raster"]["working_copy"]
    if not img.exists():
        raise SystemExit(f"the registered raster is not in this checkout: {img}")
    return g, img


class Raster:
    def __init__(self, path):
        from PIL import Image
        self.px = Image.open(path).convert("L").load()

    def grey(self, x, y):
        xi, yi = int(x), int(y)
        fx, fy = x - xi, y - yi
        p = self.px
        return (p[xi, yi] * (1 - fx) * (1 - fy) + p[xi + 1, yi] * fx * (1 - fy)
                + p[xi, yi + 1] * (1 - fx) * fy + p[xi + 1, yi + 1] * fx * fy)

    def ink(self, x, y):
        return max(0.0, 150.0 - self.grey(x, y))


def walk(r):
    """The front line: arc-length stations along the drawn bank, and its bearing there."""
    p = SEED_PX
    th = math.atan2(SEED_SLOPE, 1.0)
    pts, ths = [p], [th]
    n = int(FOLLOW_HALF_PX / FOLLOW_GRAIN_PX)
    for _ in range(STEPS):
        d = (math.cos(th), math.sin(th))
        nx, ny = -d[1], d[0]
        q = (p[0] + d[0], p[1] + d[1])
        best = None
        for i in range(-n, n + 1):
            t = i * FOLLOW_GRAIN_PX
            c = (q[0] + nx * t, q[1] + ny * t)
            v = sum(150.0 - r.grey(c[0] + d[0] * s, c[1] + d[1] * s) for s in FOLLOW_TANGENT)
            if best is None or v > best[0]:
                best = (v, c, t)
        _, c, t = best
        th += FOLLOW_SMOOTH * math.atan2(t, 1.0)
        p = c
        pts.append(p)
        ths.append(th)
    return pts, ths


def _at(pts, ths, s, t):
    """The raster point t pixels north of arc station s."""
    if s < 0:
        s = 0.0
    if s > len(pts) - 1.001:
        s = len(pts) - 1.001
    j = int(s)
    f = s - j
    x = pts[j][0] * (1 - f) + pts[j + 1][0] * f
    y = pts[j][1] * (1 - f) + pts[j + 1][1] * f
    th = ths[j] * (1 - f) + ths[j + 1] * f
    nx, ny = -math.sin(th), math.cos(th)
    return x - nx * t, y - ny * t




def _obs(r, pts, ths):
    """For every arc station: the minimum darkness over the parcel's depth, taken at the
    best of a fan of shears, and that shear. A division stroke crosses the whole depth
    and so scores high; a figure is blank above or below itself and scores near zero."""
    lo, hi = DEPTH_BAND_PX
    mid = (lo + hi) // 2
    obs, shear = [], []
    for i in range(len(pts)):
        bv, bk = -1.0, 0.0
        for k in SHEARS:
            v = min(max(r.ink(*_at(pts, ths, i + d + k * (t - mid), t)) for d in (-1, 0, 1))
                    for t in range(lo, hi + 1))
            if v > bv:
                bv, bk = v, k
        obs.append(bv)
        shear.append(bk)
    return obs, shear


def _pick(obs, shear, minimum, window, merge):
    found = []
    for i in range(2, len(obs) - 2):
        if obs[i] >= minimum and obs[i] == max(obs[max(0, i - window):i + window + 1]):
            if found and i - found[-1][0] < merge:
                if obs[i] > found[-1][1]:
                    found[-1] = (i, obs[i], shear[i])
            else:
                found.append((i, obs[i], shear[i]))
    return found


def back_line(r, pts, ths):
    """The strip's back line, per station: the first stroke north of the front."""
    lo, hi = BACK_SEARCH_PX
    out = []
    for i in range(0, len(pts), BACK_STATION_PX):
        prof = [r.ink(*_at(pts, ths, i, t)) for t in range(lo, hi + 1)]
        d = None
        for j in range(1, len(prof) - 1):
            if prof[j] >= BACK_MIN and prof[j] >= prof[j - 1] and prof[j] >= prof[j + 1]:
                d = lo + j
                break
        out.append((i, d))
    return out


def _frame():
    g = json.loads(GCP.read_text())
    d = json.loads((ROOT / "data/datum.json").read_text())
    c = g["fit"]["coefficients"]

    def to_local(px, py):
        return (round(c["a"] * px + c["b"] * py + c["c"] - d["origin_utm_e"], 2),
                round(c["d"] * px + c["e"] * py + c["f"] - d["origin_utm_n"], 2))

    return to_local


def _mean(xs):
    return sum(xs) / len(xs)


def _sd(xs):
    if len(xs) < 2:
        return 0.0
    m = _mean(xs)
    return math.sqrt(sum((x - m) ** 2 for x in xs) / (len(xs) - 1))


def read():
    g, img = _sheet()
    r = Raster(img)
    pts, ths = walk(r)
    obs, shear = _obs(r, pts, ths)
    back = back_line(r, pts, ths)
    to_local = _frame()

    def point(i, p):
        # the committed pixel is rounded FIRST and the metres derived from it, so the
        # file's own numbers re-derive from each other and the gate can say so.
        q = [round(p[0], 1), round(p[1], 1)]
        return {"s_px": i, "px": q, "local_enu_m": list(to_local(*q))}

    stations = list(range(0, len(pts), STATION_PX))
    if stations[-1] != len(pts) - 1:
        stations.append(len(pts) - 1)
    front = [point(i, pts[i]) for i in stations]

    depths = []
    for i, d in back:
        e = {"s_px": i, "depth_px": d}
        if d is not None:
            e.update(point(i, _at(pts, ths, i, d)))
        depths.append(e)

    strokes = []
    for i, v, k in _pick(obs, shear, DIVISION_MIN, DIVISION_WINDOW, DIVISION_MERGE):
        e = point(i, pts[i])
        e["min_ink_over_depth"] = round(v, 1)
        e["shear_dsdt"] = k
        strokes.append(e)

    stability = []
    for minimum, window, merge in SETTINGS:
        stability.append({"minimum_ink": minimum, "window_px": window, "merge_px": merge,
                          "strokes": len(_pick(obs, shear, minimum, window, merge))})

    return {"front_line": front, "back_line": depths, "strokes": strokes,
            "stability": stability, "steps": len(pts) - 1, "raster": g["raster"]}


def _break(doc):
    """The one cell of the run the sheet leaves open: where the back line is not there
    to be found. Derived from the ink, not counted off by index."""
    blank = [b["s_px"] for b in doc["back_line"] if b["depth_px"] is None]
    if len(blank) < 2:
        return None
    runs, cur = [], [blank[0]]
    for s in blank[1:]:
        if s - cur[-1] <= 2 * BACK_STATION_PX:
            cur.append(s)
        else:
            runs.append(cur)
            cur = [s]
    runs.append(cur)
    runs = [r for r in runs if len(r) >= 2]
    if not runs:
        return None
    longest = max(runs, key=len)
    return {"from_s_px": longest[0] - BACK_STATION_PX, "to_s_px": longest[-1] + BACK_STATION_PX,
            "stations_without_a_back_line": len(longest)}


def document(doc):
    g = json.loads(GCP.read_text())
    grid = json.loads(STREETS.read_text())
    ratio = grid["control_summary"]["method_over_read"]
    to_local = _frame()

    fl = doc["front_line"]
    arc_m = 0.0
    for a, b in zip(fl, fl[1:]):
        arc_m += math.hypot(b["local_enu_m"][0] - a["local_enu_m"][0],
                            b["local_enu_m"][1] - a["local_enu_m"][1])
    m_per_px = arc_m / (fl[-1]["s_px"] - fl[0]["s_px"])

    brk = _break(doc)
    deep = [b["depth_px"] for b in doc["back_line"] if b["depth_px"] is not None]
    pitch = [b["s_px"] - a["s_px"] for a, b in zip(doc["strokes"], doc["strokes"][1:])]
    counts = sorted(s["strokes"] for s in doc["stability"])

    def ft(px):
        return round(px * m_per_px / ratio / FT, 1)

    return {
        "_doc": __doc__.strip(),
        "ticket": "T-1063 (piece 4 of T-0789)",
        "id": "kinzie_addition_water_lots_1834",
        "plat": "kinzie_addition",
        "generated_by": "tools/read_kinzie_addition_water_lots.py",
        "raster": {k: g["raster"][k] for k in
                   ("working_copy", "width", "height", "dpi", "sha256", "source_id")},
        "registration": {
            # Read off the GCP file rather than restated here: T-1091 replaced the
            # eight-point fit with an eleven-point one AFTER this reading was first
            # written, and the sentence that named the old RMS went stale in place.
            # `--check` re-derives every metre through whichever fit is in force, so the
            # provenance line has to move with it.
            "gcp_file": "data/traces/gcp/wright_1834_nara_hup_gcps.json",
            "fit": g["fit"]["type"],
            "rms_m": g["fit"]["rms_m"],
            "adopted": g["fit"]["adopted"].split(".")[0],
        },
        "read_on": "2026-09-12",
        "method": "tools/read_kinzie_addition_water_lots.py — a tangential follower walks "
                  "the drawn bank from one seed point, which gives the run an arc "
                  "coordinate; the back line is the first stroke north of the front at "
                  "each station; the division strokes are the arc positions where the "
                  "MINIMUM darkness over the parcel's depth peaks, over a fan of shears. "
                  "`--check` re-derives every metre here from the pixels committed beside "
                  "it; `--check-sheet` re-opens the raster and re-reads all of it.",
        "frame": {
            "seed_px": list(SEED_PX),
            "seed_slope_dy_dx": SEED_SLOPE,
            "steps_px": doc["steps"],
            "station_px": STATION_PX,
            "arc_length_m": round(arc_m, 1),
            "m_per_arc_px": round(m_per_px, 4),
            "note": "s is arc length in raster pixels from the seed along the drawn bank; "
                    "t is pixels north of it, square to the walk's bearing there.",
        },
        "run": {
            "west_terminus_px": fl[0]["px"],
            "east_terminus_px": fl[-1]["px"],
            "west_terminus_local_enu_m": fl[0]["local_enu_m"],
            "east_terminus_local_enu_m": fl[-1]["local_enu_m"],
            "parcels": PARCELS,
            "break": brk,
            "break_at_lot": BREAK_LOT,
            "what_it_is": "One run of narrow parcels laid side by side against the north "
                          "bank of the Main Branch, from the Original Town's east line to "
                          "the harbour, numbered straight through. It is not a block and "
                          "it is not subdivided into lots inside a block: on this sheet it "
                          "is the tract's wharfage, and the only ground in the Addition "
                          "Wright draws without a tier and a column.",
        },
        "front_line": doc["front_line"],
        "back_line": doc["back_line"],
        "division_strokes": {
            "found": doc["strokes"],
            "settings": {"minimum_ink": DIVISION_MIN, "window_px": DIVISION_WINDOW,
                         "merge_px": DIVISION_MERGE, "shear_fan": list(SHEARS),
                         "depth_band_px": list(DEPTH_BAND_PX)},
            "pitch_px": {"mean": round(_mean(pitch), 1), "sd": round(_sd(pitch), 1),
                         "min": min(pitch), "max": max(pitch), "n": len(pitch)},
            "stability": doc["stability"],
            "grade": "inferred, every one of them. The strokes are real ink and the "
                     "detector is finding ink, but it does not find the SAME ink under "
                     "every reasonable setting: the fan below returns between "
                     f"{counts[0]} and {counts[-1]} strokes where the run's own figures "
                     f"require {PARCELS - 1}. In the wedge east of the break the strokes "
                     "stand square to the back line rather than to the bank and lean by "
                     "most of a parcel's width across the depth, which is where the "
                     "disagreement is. So this list says WHERE the sheet rules its "
                     "parcels off, to about a stroke's width, and it does NOT say which "
                     "stroke bounds which numbered lot.",
        },
        "module": {
            "mean_frontage_ft": ft(doc["steps"] / PARCELS),
            "mean_frontage_m": round(doc["steps"] / PARCELS * m_per_px, 2),
            "depth_px": {"mean": round(_mean(deep), 1), "sd": round(_sd(deep), 1),
                         "n": len(deep)},
            "depth_ft": ft(_mean(deep)),
            "method_over_read": ratio,
            "reading": "The mean frontage does not come from the strokes — it comes from "
                       "the two things the sheet does settle: the run's arc length, and "
                       "that the run is " + str(PARCELS) + " parcels because its first "
                       "figure is 1 and its last is 35. A width in feet is that arc "
                       "carried to metres through the committed NA affine and then divided "
                       "by the factor data/traces/kinzie_addition_street_grid.json measured "
                       "for this sheet and this class of method against the Original Town's "
                       "platted 80 ft corridors — a width RELATIVE to a known width on the "
                       "same paper, which is the only width this sheet can settle.",
            "against_the_original_town": "Thompson's lots front 80 ft on the street. These "
                                         "front about " + str(ft(doc["steps"] / PARCELS)) +
                                         " ft on the water and run about " + str(ft(_mean(deep))) +
                                         " ft back, which is the shape of wharfage rather "
                                         "than of a town lot.",
        },
        "numbering": {
            "rule": "One run, west to east: 1 at the Original Town's east line, 35 at the "
                    "harbour. No tier, no column, no boustrophedon — a lot strip has one "
                    "axis and the figures follow it.",
            "documented": DOCUMENTED,
            "refused": [n for n in range(1, PARCELS + 1) if n not in DOCUMENTED],
            "crops": CROPS,
            "why_refused": "Wright's figures in the western half of the run are about two "
                           "millimetres of pen on a manuscript that was mounted on cloth to "
                           "repair a tear, and the 600-dpi facsimile does not carry them: at "
                           "8x to 14x the cells hold a shape and not a number. "
                           f"{PARCELS - len(DOCUMENTED)} of the {PARCELS} are refused on "
                           "that ground, lot 14 among them. Nothing is upgraded to make the "
                           "run look complete.",
            "break": BREAK_NOTE,
        },
        "refusals": [
            "Which stroke bounds which numbered lot is NOT settled — see "
            "`division_strokes.grade`. A per-lot frontage table would be an invention.",
            "No lot line is drawn inside a parcel on this sheet and none is derived here.",
            "This file authors no fabric: no wharf, no frontage run, no roof. It is a "
            "reading of a sheet, and the ground anything is spent onto is the committed "
            "bank's, not this file's.",
            "The seating is the sheet's own affine, whose RMS is 16.19 m and whose two axis "
            "scales differ by 5.2 per cent. Where this run sits against the committed 1834 "
            "bank trace is not settled here.",
        ],
    }


def check_offline(path=OUT):
    """Every metre in the committed file re-derives from the pixels committed beside it."""
    doc = json.loads(path.read_text())
    to_local = _frame()
    bad = []
    pts = (doc["front_line"] + [b for b in doc["back_line"] if "px" in b]
           + doc["division_strokes"]["found"])
    for e in pts:
        want = [round(v, 2) for v in to_local(*e["px"])]
        if want != [round(v, 2) for v in e["local_enu_m"]]:
            bad.append((e["px"], e["local_enu_m"], want))
    fl = doc["front_line"]
    arc = sum(math.hypot(b["local_enu_m"][0] - a["local_enu_m"][0],
                         b["local_enu_m"][1] - a["local_enu_m"][1])
              for a, b in zip(fl, fl[1:]))
    if round(arc, 1) != doc["frame"]["arc_length_m"]:
        bad.append(("arc_length_m", doc["frame"]["arc_length_m"], round(arc, 1)))
    if round(arc / (fl[-1]["s_px"] - fl[0]["s_px"]), 4) != doc["frame"]["m_per_arc_px"]:
        bad.append(("m_per_arc_px", doc["frame"]["m_per_arc_px"], None))
    if doc["run"]["parcels"] != PARCELS or doc["run"]["break_at_lot"] != BREAK_LOT:
        bad.append(("run", doc["run"]["parcels"], PARCELS))
    if doc["numbering"]["documented"] != DOCUMENTED:
        bad.append(("documented figures", doc["numbering"]["documented"], DOCUMENTED))
    if sorted(doc["numbering"]["documented"] + doc["numbering"]["refused"]) != list(range(1, PARCELS + 1)):
        bad.append(("numbering", "documented + refused is not the whole run", None))
    br = doc["run"]["break"]
    blank = [b["s_px"] for b in doc["back_line"] if b["depth_px"] is None]
    if br and not all(br["from_s_px"] < s < br["to_s_px"] for s in blank[:br["stations_without_a_back_line"]]):
        bad.append(("break", "does not cover the stations with no back line", None))
    if bad:
        for b in bad:
            print("  drift:", b, file=sys.stderr)
        raise SystemExit(f"{len(bad)} statement(s) in {path.name} no longer re-derive")
    print(f"{path.name}: {len(fl)} front-line stations, {len(doc['back_line'])} depths and "
          f"{len(doc['division_strokes']['found'])} strokes re-derive; run of {PARCELS}")


def check_sheet():
    # DEGRADE POLITELY, LIKE THE OTHER THIRTEEN RASTER STEPS (T-1083) — this one
    # did not, and the cost was measured on 2026-09-13: it raised a bare
    # ModuleNotFoundError for PIL, `tools/check.sh` counted that as a failed step,
    # and `.github/steward/pr-lap.sh` reads a red gate as "do not push". The lap
    # therefore refused EVERY open PR — `pushed=0 … red=11` on run 272 — so no
    # branch could be brought current and nothing could merge. The owner saw it as
    # "getting some red PR's".
    #
    # The lap and the bake install the readers now, so this path should not be
    # reached in CI. It is here because a gate step that CRASHES when a library is
    # absent takes the whole gate with it, wherever it runs: the next workflow, or
    # any agent sandbox. `--check` (check_offline) stands on the committed pixels
    # and needs nothing, which is why that half was green throughout.
    #
    # C4D_GATE_REQUIRE_READERS=1 keeps T-1083's rule intact: a GATE may not count a
    # skip as a pass, so where the readers are required this is still RED.
    try:
        from PIL import Image  # noqa: F401
    except ImportError:
        if os.environ.get("C4D_GATE_REQUIRE_READERS") == "1":
            raise SystemExit(
                "Pillow is not installed and C4D_GATE_REQUIRE_READERS=1: a gate may "
                "not count a skip as a pass (T-1083). pip install Pillow")
        print(f"   Pillow is absent, so THE SHEET WAS NOT RE-READ. {OUT.name} stands on "
              "its committed reading; `--check` re-derives it from the committed pixels "
              "and is unaffected.")
        return
    built = document(read())
    have = json.loads(OUT.read_text())
    if json.dumps(built, sort_keys=True) != json.dumps(have, sort_keys=True):
        raise SystemExit(f"{OUT.name} no longer matches a fresh read of the sheet")
    print(f"{OUT.name}: re-read from the raster, byte for byte the same")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--check-sheet", action="store_true")
    a = ap.parse_args()
    if a.check:
        return check_offline()
    if a.check_sheet:
        return check_sheet()
    doc = document(read())
    if a.write:
        OUT.write_text(json.dumps(doc, indent=1) + "\n")
        print(f"wrote {OUT.relative_to(ROOT)}")
    else:
        m = doc["module"]
        d = doc["division_strokes"]
        print(f"{PARCELS} parcels over {doc['frame']['arc_length_m']} m; break at lot "
              f"{BREAK_LOT}; mean frontage {m['mean_frontage_ft']} ft, depth "
              f"{m['depth_ft']} ft; {len(d['found'])} strokes, pitch "
              f"{d['pitch_px']['mean']} +/- {d['pitch_px']['sd']} px; stability "
              f"{[s['strokes'] for s in d['stability']]}")


if __name__ == "__main__":
    main()
