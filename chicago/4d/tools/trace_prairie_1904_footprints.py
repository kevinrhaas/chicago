#!/usr/bin/env python3
"""Digitise the 1904 building footprints off a Prairie Avenue Sanborn sheet (T-2327, T-2328).

    python3 tools/trace_prairie_1904_footprints.py            # (re)write the footprint file(s)
    python3 tools/trace_prairie_1904_footprints.py --check    # re-derive, change nothing
    python3 tools/trace_prairie_1904_footprints.py --self-test
    python3 tools/trace_prairie_1904_footprints.py --sheet 20 --overlay DIR   # one sheet's study images

SHEETS. Sheet 28 (18th-20th, T-2327, for T-2159), sheet 20 (16th-18th, T-2328, for
T-2160) and sheet 35 (20th-22nd, T-2340, for T-2161). A sheet is added as one SHEETS entry
-- its fit, its census, its blocks -- and the reading below is the same for every sheet;
nothing in it is tuned per sheet. What does differ is the scan: sheet 35's copy is 3.7x
coarser, so the pixel rules are paper lengths scaled by each scan's resolution (see
set_px_rules), and on a scan that coarse a one-pixel wall is found by its darkness.

WHAT THIS IS. The outlines T-2159's draft builder stands each Prairie Avenue house on. The
sheet census (T-1841 for sheet 28, T-1840 for sheet 20) names every building on the sheet (`s28-1812-front`, `s28-1812-rear`, ...)
and rules on its 1904 state, but says of itself "Footprints are not digitized and no
dimension is claimed"; the only coordinates on these blocks were the parcel lines
(data/street_grid/1904.json, T-0474). This tool reads the buildings' outlines off the same
committed raster, carries them through the same fitted transform (T-1250,
data/traces/gcp/), and gives every census polygon its geometry.

HOW IT READS. Sanborn colours its fabric (pink brick, blue stone, yellow frame) and draws
every wall as a black line, so a building is the coloured ground inside its lines:

  1. every pixel is classed brick, stone, frame or not-fabric by fixed colour rules (CLASSES)
  2. a parcel's fabric is the classed pixels inside its lot lines (the T-0474 parcel polygon,
     taken back to pixels through the inverse of the sheet's fit)
  3. a BUILDING is a group of fabric joined across its own lines and lettering: the fabric
     closed by BRIDGE_PX and its holes filled
  4. a PART is fabric bounded by solid lines (a range, a porch, a stone front): the fabric
     NOT closed, so a drawn wall between two ranges separates them and a dashed one does not
  5. each outline is pushed out by LINE_HALF_PX to the centre of the drawn wall, traced along
     pixel edges, simplified (Douglas-Peucker, SIMPLIFY_PX) and carried to local metres

Census polygons are assigned by a declared rule (assign): the building nearest the street
takes the frontage's `front` and every `attached` id; buildings at the alley end take its
`detached_service` ids, nearest the alley first. A building the census has no id for is
kept and named `unassigned`, never dropped.

TIERS. The geometry is a 1911 survey carried to 1904, so every outline is INFERRED for 1904,
on the census's own ruling for each polygon (T-1841: present as mapped, 1911 garage labels
backcast as stables). The outline is good to the georeference (1.47 m RMS on standing
houses, data/traces/gcp/sanborn_1911_v3_sheet_28_gcps.json) plus the trace (about a pixel,
0.05 m). Part roles (main, range, porch, stone front) are INFERRED from colour, size and
position by the rule in `role`; storey counts are NOT read here -- the census's printed
notation is the only storey reading.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
REPO = ROOT.parents[1]
GCP_DIR = ROOT / "data" / "traces" / "gcp"
GRID = ROOT / "data" / "street_grid" / "1904.json"
CENSUS_DIR = REPO / "chicago" / "prairie_1904_v1" / "data" / "sheet_census"

SHEETS = {
    "28": {
        "gcp": "sanborn_1911_v3_sheet_28",
        "census": "sheet-28.json",
        "blocks": ("blk_indiana_prairie_18_20", "blk_prairie_calumet_18_20"),
        "out": ROOT / "data" / "traces" / "prairie_1904_footprints_s28.json",
        "ticket": "T-2327",
        "census_ticket": "T-1841",
    },
    "20": {
        "gcp": "sanborn_1911_v3_sheet_20",
        "census": "sheet-20.json",
        "blocks": ("blk_indiana_prairie_16_18", "blk_prairie_ic_16_18"),
        "out": ROOT / "data" / "traces" / "prairie_1904_footprints_s20.json",
        "ticket": "T-2328",
        "census_ticket": "T-1840",
    },
    "35": {
        "gcp": "sanborn_1911_v3_sheet_35",
        "census": "sheet-35.json",
        "blocks": ("blk_indiana_prairie_20_21", "blk_indiana_prairie_21_22",
                   "blk_prairie_calumet_20_21", "blk_prairie_calumet_21_22"),
        "out": ROOT / "data" / "traces" / "prairie_1904_footprints_s35.json",
        "ticket": "T-2340",
        "census_ticket": "T-1842",
    },
    # The district draft's named context buildings off Prairie Avenue (T-2982): the same
    # scan and fit as "35", read on five named lots of East Twentieth Street and Calumet
    # Avenue, against their own census beside the draft rules (the Prairie census counts
    # Prairie frontages only).
    "35x": {
        "gcp": "sanborn_1911_v3_sheet_35",
        "census_path": ROOT / "data" / "components" / "prairie_1904" / "edges_census_s35.json",
        "blocks": ("blk_indiana_prairie_20_21", "blk_prairie_calumet_20_21"),
        "parcels": ("e20th_213", "e20th_215", "e20th_217", "calumet_2008", "calumet_2018"),
        "out": ROOT / "data" / "traces" / "prairie_1904_footprints_s35x.json",
        "ticket": "T-2982",
        "census_ticket": "T-2982",
    },
    # The background behind Prairie Avenue (T-3008, piece 1 of T-2983): the same scan and
    # fit as "28", read on Calumet Avenue's west frontage from 18th to 20th Street (1800 is
    # Pullman's glasshouse ground, T-1934's, and is not traced here).
    "28x": {
        "gcp": "sanborn_1911_v3_sheet_28",
        "census_path": ROOT / "data" / "components" / "prairie_1904" / "edges_census_s28.json",
        "blocks": ("blk_prairie_calumet_18_20",),
        "parcels": ("calumet_1830", "calumet_1832", "calumet_1836", "calumet_1840", "calumet_1900",
                    "calumet_1910", "calumet_1922", "calumet_1928", "calumet_1932"),
        "out": ROOT / "data" / "traces" / "prairie_1904_footprints_s28x.json",
        "ticket": "T-3008",
        "census_ticket": "T-3008",
    },
    # The background behind Prairie Avenue (T-3019, piece 2 of T-3010): the same scan and fit
    # as "20", read on Indiana Avenue's east frontage from 16th to 18th Street and East
    # Sixteenth Street's row at 209-217; the unnumbered strips, open on the sheet and on
    # Robinson 1886, are not traced.
    "20w": {
        "gcp": "sanborn_1911_v3_sheet_20",
        "census_path": ROOT / "data" / "components" / "prairie_1904" / "edges_census_s20w.json",
        "blocks": ("blk_indiana_prairie_16_18",),
        "parcels": ("indiana_1601", "e16th_209", "indiana_1605", "indiana_1615", "indiana_1619",
                    "indiana_1623", "indiana_1623_1637_c", "indiana_1637", "indiana_1641",
                    "indiana_1703", "indiana_1713", "indiana_1727"),
        "out": ROOT / "data" / "traces" / "prairie_1904_footprints_s20w.json",
        "ticket": "T-3019",
        "census_ticket": "T-3019",
    },
    # The background behind Prairie Avenue (T-3018, piece 1 of T-3010): the same scan and fit
    # as "35", read on Calumet Avenue's west frontage from 20th to 22nd Street (2008 and 2018
    # are the named Hanford and Wheeler-Kohn houses, "35x"'s).
    "35e": {
        "gcp": "sanborn_1911_v3_sheet_35",
        "census_path": ROOT / "data" / "components" / "prairie_1904" / "edges_census_s35e.json",
        "blocks": ("blk_prairie_calumet_20_21", "blk_prairie_calumet_21_22"),
        "parcels": ("calumet_2000", "calumet_2004", "calumet_2016", "calumet_2032", "calumet_2100",
                    "calumet_2106", "calumet_2114", "calumet_2124", "calumet_2128", "calumet_2140"),
        "out": ROOT / "data" / "traces" / "prairie_1904_footprints_s35e.json",
        "ticket": "T-3018",
        "census_ticket": "T-3018",
    },
    # The background behind Prairie Avenue (T-3009, piece 2 of T-2983): the same scan and fit
    # as "35", read on Indiana Avenue's east frontage from 20th to 22nd Street and the two lots
    # of East Twenty-first Street behind its 2101-2105 corner (213-217 E. 20th are "35x"'s).
    "35w": {
        "gcp": "sanborn_1911_v3_sheet_35",
        "census_path": ROOT / "data" / "components" / "prairie_1904" / "edges_census_s35w.json",
        "blocks": ("blk_indiana_prairie_20_21", "blk_indiana_prairie_21_22"),
        "parcels": ("indiana_2001", "indiana_2007", "indiana_2009", "indiana_2011", "indiana_2013",
                    "indiana_2017", "indiana_2019", "indiana_2021", "indiana_2023", "indiana_2027",
                    "indiana_2029", "indiana_2101", "e21st_w_215", "e21st_215", "indiana_2107",
                    "indiana_2111", "indiana_2115", "indiana_2119", "indiana_2123", "indiana_2129"),
        "out": ROOT / "data" / "traces" / "prairie_1904_footprints_s35w.json",
        "ticket": "T-3009",
        "census_ticket": "T-3009",
    },
    # The background behind Prairie Avenue (T-3151, piece 2 of T-3145): sheet 27, which T-3150
    # ingested and fit, read on Indiana Avenue's east frontage from 18th to 20th Street and the
    # row at 213-217 East Eighteenth Street; the two unnumbered lots between 1839 and 1901 are
    # open on the sheet and not traced.
    "27w": {
        "gcp": "sanborn_1911_v3_sheet_27",
        "census_path": ROOT / "data" / "components" / "prairie_1904" / "edges_census_s27w.json",
        "blocks": ("blk_indiana_prairie_18_20",),
        "parcels": ("indiana_1801", "indiana_1803", "indiana_1805", "indiana_1807", "e18th_213",
                    "indiana_1809", "indiana_1813", "indiana_1815", "indiana_1819", "indiana_1821",
                    "indiana_1825", "indiana_1829", "indiana_1833", "indiana_1837", "indiana_1839",
                    "indiana_1901", "indiana_1909", "indiana_1913", "indiana_1915", "indiana_1917",
                    "indiana_1921", "indiana_1925", "indiana_1931", "indiana_1935"),
        "out": ROOT / "data" / "traces" / "prairie_1904_footprints_s27w.json",
        # This copy's frame wash is printed darker than sheets 20's and 28's: the alley sheds
        # read r 156-169, g 148-161, b 57-70 (10th-90th percentile over 1901's and 1913's), under
        # the frame rule's r > 170, so they fell out as paper. Their hue is the rule's own
        # (r-b and g-b far over it); only the floor on r is lowered, for this scan alone.
        "frame_r_min": 150,
        "ticket": "T-3151",
        "census_ticket": "T-3151",
    },
}

# Colour rules, on 8-bit sRGB. The paper is cream (r >= g >= b, r - g under 30); brick
# pink is r well over g; stone blue is the only ground with b over r; frame yellow is the
# only one with b far under both r and g. Measured on the sheet's 25 most common colours.
CLASSES = ("brick", "stone", "frame")
BRIDGE_PX = 7          # closes a drawn wall (3-5 px) and the lettering inside a building
LINE_HALF_PX = 2       # the fill stops at a wall's inner edge; its centre is ~2 px out
SIMPLIFY_PX = 2.5      # Douglas-Peucker tolerance, 0.13 m on sheet 28
MIN_PART_PX = 360      # 1 m2 at 0.0506 m/px: smaller fabric is lettering cut off by a line
MIN_BUILDING_PX = 720  # 2 m2
PARCEL_INSET_PX = 1    # stay off the neighbour's side of a shared lot line
PORCH_MAX_M2 = 15.0
STONE_FRONT_MAX_DEPTH_M = 1.6
ABUT_M = 1.5           # an outline the census has no id for, this near the house, is the house's
FRONT_SLIVER_GAP_M = 1.5  # a street-side sliver this near the building behind it is that building's front
PART_ERODE_PX = 1      # parts are labelled on fabric eroded this far, then grown back
TRIANGLE_FILL = 0.62   # under this share of its box a part is a triangle (a stable's cross)
LINE_MEAN = 140        # under this mean of r, g and b a pixel is a drawn line, not a wash
LINE_RULE_SCALE = 2.0  # ...on a scan this many times coarser than REF_M_PER_PX, or more
LINE_RULE = False      # set per sheet by set_px_rules
FRAME_R_MIN = 170      # the frame rule's floor on r; a scan with a darker yellow wash sets its own (SHEETS)
LINE_GAP_PX = 3        # ...and a straight wall broken for up to this many pixels is closed
REAR_SPLIT = 0.30      # the rear share of a lot a split-off service building begins in
REAR_SPLITS = (REAR_SPLIT, 0.45, 0.60)   # ...widened in these steps when a step finds nothing

# THE PIXEL RULES ARE PAPER RULES. A drawn wall, a letter and the gap a porch leaves are
# printed at a fixed size, so every *_PX above is a length on the sheet, stated here at the
# resolution it was set on: sheets 28 and 20, scanned at 0.0506 and 0.0508 m/px. A copy
# scanned coarser (sheet 35, 0.186 m/px) draws the same wall in fewer pixels, and is read
# with each rule divided by its resolution ratio, rounded to one decimal so that the two
# scans the rules were set on read at exactly 1.0 (their outlines are unchanged by it).
# Lengths are rounded to whole pixels and never below one; areas scale by the square.
REF_M_PER_PX = 0.0506
BASE_PX = {"BRIDGE_PX": 7, "LINE_HALF_PX": 2, "SIMPLIFY_PX": 2.5, "MIN_PART_PX": 360,
           "MIN_BUILDING_PX": 720, "PARCEL_INSET_PX": 1, "PART_ERODE_PX": 1}
PX_AREAS = ("MIN_PART_PX", "MIN_BUILDING_PX")
PX_FLOAT = ("SIMPLIFY_PX",)


def px_scale(m_per_px: float) -> float:
    return round(m_per_px / REF_M_PER_PX, 1)


def set_px_rules(m_per_px: float) -> dict:
    """Set the module's pixel rules for a scan at `m_per_px`, and return them."""
    k = px_scale(m_per_px)
    out = {}
    for name, v in BASE_PX.items():
        if name in PX_AREAS:
            out[name] = max(1, round(v / (k * k)))
        elif name in PX_FLOAT:
            out[name] = round(v / k, 2)
        else:
            out[name] = max(1, round(v / k))
    out["LINE_RULE"] = k >= LINE_RULE_SCALE
    # The line rule takes a wall's blurred edge pixels out of the fabric as well as its
    # core, so a wall reads about a pixel wider than the scaled bridge was set for.
    if out["LINE_RULE"]:
        out["BRIDGE_PX"] += 1
    globals().update(out)
    return out


def r2(x: float) -> float:
    return round(float(x) + 0.0, 2)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# ---------------------------------------------------------------------------
# the transform


class Fit:
    def __init__(self, gcp: dict):
        c = gcp["fit"]["coefficients"]
        self.A = np.array([[c["a"], c["b"]], [c["d"], c["e"]]], dtype=np.float64)
        self.t = np.array([c["c"], c["f"]], dtype=np.float64)
        self.Ai = np.linalg.inv(self.A)
        self.m_per_px = gcp["fit"]["scale_m_per_px"]

    def local(self, px: float, py: float) -> tuple[float, float]:
        e, n = self.A @ np.array([px, py]) + self.t
        return float(e), float(n)

    def pixel(self, e: float, n: float) -> tuple[float, float]:
        px, py = self.Ai @ (np.array([e, n]) - self.t)
        return float(px), float(py)


# ---------------------------------------------------------------------------
# pixels


def classify(rgb: np.ndarray) -> np.ndarray:
    """0 not fabric, 1 brick, 2 stone, 3 frame."""
    r, g, b = (rgb[..., i].astype(np.int16) for i in range(3))
    out = np.zeros(r.shape, dtype=np.uint8)
    out[(r - g > 30) & (r - b > 25) & (r > 120)] = 1
    out[(b - r >= 10) & (g > 110)] = 2
    out[(r - b > 80) & (g - b > 60) & (r > FRAME_R_MIN)] = 3
    # A drawn line is darker than any wash. On a fine scan its core is near black and the
    # rules above already leave it out; on a coarse one (sheet 35) a one-pixel wall blurs
    # into the pink and reads as brick, which joins the parts it divides. So on a scan read
    # at LINE_RULE_SCALE or coarser, a pixel whose mean channel is under LINE_MEAN is line,
    # whatever its hue. (On the fine scans it would also eat the darker washes' edges, which
    # the fill already reads correctly, so it is not applied there.)
    # A one-pixel wall is broken by every letter and JPEG block it crosses, so the dark run
    # is closed along rows and along columns, bridging a gap of up to LINE_GAP_PX pixels in
    # a straight wall (the sheet's walls run with its lot lines, square to the raster).
    if LINE_RULE:
        dark = (r + g + b) < 3 * LINE_MEAN
        k = LINE_GAP_PX + 2
        dark = (dark | ndimage.binary_closing(dark, structure=np.ones((1, k), bool))
                | ndimage.binary_closing(dark, structure=np.ones((k, 1), bool)))
        out[dark] = 0
    return out


def polygon_mask(shape: tuple, poly_px: list, inset: int) -> np.ndarray:
    im = Image.new("1", (shape[1], shape[0]), 0)
    ImageDraw.Draw(im).polygon([tuple(p) for p in poly_px], fill=1)
    m = np.asarray(im, dtype=bool)
    return ndimage.binary_erosion(m, iterations=inset) if inset else m


def trace(mask: np.ndarray) -> list:
    """The outer boundary of a mask's one region, along pixel edges, as corner vertices
    (x, y) at each turn. Region kept on the right; diagonal neighbours count as joined."""
    ys, xs = np.nonzero(mask)
    i = np.lexsort((xs, ys))[0]
    y0, x0 = int(ys[i]), int(xs[i])
    h, w = mask.shape

    def inside(y, x):
        return 0 <= y < h and 0 <= x < w and bool(mask[y, x])

    step = {"E": (0, 1), "S": (1, 0), "W": (0, -1), "N": (-1, 0)}
    left = {"E": "N", "N": "W", "W": "S", "S": "E"}
    right = {v: k for k, v in left.items()}
    # the two pixels ahead of a corner vertex (y, x), as (ahead-left, ahead-right)
    ahead = {"E": ((-1, 0), (0, 0)), "S": ((0, 0), (0, -1)),
             "W": ((0, -1), (-1, -1)), "N": ((-1, -1), (-1, 0))}
    y, x, d = y0, x0, "E"
    verts = [(x0, y0)]
    for _ in range(4 * mask.size):
        dy, dx = step[d]
        y, x = y + dy, x + dx
        (ly, lx), (ry, rx) = ahead[d]
        if inside(y + ly, x + lx):
            nd = left[d]
        elif inside(y + ry, x + rx):
            nd = d
        else:
            nd = right[d]
        if (y, x) == (y0, x0) and nd == "E":
            break
        if nd != d:
            verts.append((x, y))
        d = nd
    return verts


def _dp(pts: list, tol: float) -> list:
    if len(pts) < 3:
        return pts
    a, b = np.array(pts[0], float), np.array(pts[-1], float)
    ab = b - a
    L = math.hypot(*ab)
    best, at = -1.0, 0
    for k in range(1, len(pts) - 1):
        p = np.array(pts[k], float) - a
        dist = abs(ab[0] * p[1] - ab[1] * p[0]) / L if L else math.hypot(*p)
        if dist > best:
            best, at = dist, k
    if best <= tol:
        return [pts[0], pts[-1]]
    return _dp(pts[:at + 1], tol)[:-1] + _dp(pts[at:], tol)


def simplify(ring: list, tol: float) -> list:
    """Douglas-Peucker on a closed ring, split at its first vertex and the one farthest away."""
    p0 = np.array(ring[0], float)
    far = max(range(len(ring)), key=lambda k: (math.hypot(*(np.array(ring[k], float) - p0)), -k))
    a = _dp(ring[:far + 1], tol)
    b = _dp(ring[far:] + [ring[0]], tol)
    out = a[:-1] + b[:-1]
    return out if len(out) >= 3 else ring


def area(poly: list) -> float:
    s = 0.0
    for (x1, y1), (x2, y2) in zip(poly, poly[1:] + poly[:1]):
        s += x1 * y2 - x2 * y1
    return s / 2.0


def outline(mask: np.ndarray, off: tuple, fit: Fit) -> dict:
    """A region's outline, pushed out to the wall's centre line, in pixels and local metres."""
    grown = ndimage.binary_dilation(mask, iterations=LINE_HALF_PX)
    ring = simplify(trace(grown), SIMPLIFY_PX)
    ring_px = [[round(x + off[0], 1), round(y + off[1], 1)] for x, y in ring]
    ring_m = [list(map(r2, fit.local(*p))) for p in ring_px]
    if area(ring_m) < 0:                       # counter-clockwise in local ENU
        ring_m, ring_px = ring_m[::-1], ring_px[::-1]
    return {"polygon_px": ring_px, "polygon_local_m": ring_m, "area_m2": r2(area(ring_m))}


# ---------------------------------------------------------------------------
# reading a parcel


def street_axis(lots: list) -> tuple:
    """Unit vector (local) from the rear lot line toward the street, the street line's
    midpoint, and the lot depth, from the parcels' named corners. Several lots read as one
    ground share a street line, so the axis is the first lot's and the depth the deepest."""
    u, front, depth = _street_axis(lots[0])
    return u, front, max([depth] + [_street_axis(q)[2] for q in lots[1:]])


def _street_axis(parcel: dict) -> tuple:
    # the lot's two street corners and two rear corners, whichever way it faces (a Prairie
    # lot faces east or west; a cross-street lot of sheet "35x" faces north)
    c = parcel["corners_local_m"]
    front = sum(np.array(v) for k, v in c.items() if k.endswith("_street")) / 2
    rear = sum(np.array(v) for k, v in c.items() if k.endswith("_rear")) / 2
    u = front - rear
    return u / np.linalg.norm(u), front, float(np.linalg.norm(front - rear))


def role(part: dict, main_id: str, depth_m: float) -> tuple[str, str]:
    if part["id"] == main_id:
        return "main", "the largest part of the building"
    if part["material"] == "frame" and part["area_m2"] <= PORCH_MAX_M2:
        return "porch", (f"frame (yellow) and at most {PORCH_MAX_M2:g} m2 on a masonry house: "
                         "a porch, stoop or lean-to")
    if part["material"] == "stone" and depth_m <= STONE_FRONT_MAX_DEPTH_M:
        return "stone_front", (f"stone (blue) and at most {STONE_FRONT_MAX_DEPTH_M:g} m deep: "
                               "a stone face or bay on a brick body")
    return "range", "a range bounded by drawn walls: a wing, a rear range or a bay"


def _depths(mask: np.ndarray, off: tuple, fit: Fit, u, front) -> tuple[float, float]:
    """Nearest and farthest metres in from the street line of a mask's pixels."""
    ys, xs = np.nonzero(mask)
    pts = np.stack([xs + off[0] + 0.5, ys + off[1] + 0.5], 1) @ fit.A.T + fit.t
    al = (pts - front) @ u
    return float(-al.max()), float(-al.min())


def _fill_ratio(mask: np.ndarray) -> float:
    """A region's share of its bounding box: a right triangle is 0.5, a rectangle 1."""
    ys, xs = np.nonzero(mask)
    return mask.sum() / float((ys.max() - ys.min() + 1) * (xs.max() - xs.min() + 1))


def part_masks(fabric: np.ndarray, gm: np.ndarray) -> list:
    """The parts of one building: its fabric split at drawn walls. The fabric is eroded a
    pixel first so a wall blurred by the JPEG still separates; each part is grown back."""
    plab, _ = ndimage.label(ndimage.binary_erosion(fabric & gm, iterations=PART_ERODE_PX))
    out = []
    for p in np.unique(plab[gm]):
        if p == 0:
            continue
        pm = plab == p
        if pm.sum() < MIN_PART_PX:
            continue
        grown = ndimage.binary_dilation(pm, iterations=PART_ERODE_PX) & gm
        out.append(ndimage.binary_fill_holes(ndimage.binary_closing(grown, iterations=3)) & gm)
    return out


def read_parcel(cls: np.ndarray, origin: tuple, lots: list, fit: Fit, n_rear: int,
                has_front: bool = True) -> tuple:
    """The buildings on one ground: a lot, or several lots one census frontage spans (read as
    their union, so a building standing across a strip line is one building, not pieces)."""
    ox, oy = origin
    polys = [[[fit.pixel(*p)[0] - ox, fit.pixel(*p)[1] - oy] for p in q["polygon_local_m"]] for q in lots]
    xs, ys = [p[0] for pp in polys for p in pp], [p[1] for pp in polys for p in pp]
    x0, y0 = max(int(min(xs)) - 2, 0), max(int(min(ys)) - 2, 0)
    x1, y1 = int(max(xs)) + 3, int(max(ys)) + 3
    sub = cls[y0:y1, x0:x1]
    if len(polys) == 1:
        lot = polygon_mask(sub.shape, [[p[0] - x0, p[1] - y0] for p in polys[0]], PARCEL_INSET_PX)
    else:
        lot = np.logical_or.reduce([polygon_mask(sub.shape, [[p[0] - x0, p[1] - y0] for p in pp], 0)
                                    for pp in polys])
        lot = ndimage.binary_erosion(lot, iterations=PARCEL_INSET_PX)
    fabric = (sub > 0) & lot
    fabric = ndimage.binary_opening(fabric, iterations=1)
    groups = ndimage.binary_fill_holes(ndimage.binary_closing(fabric, iterations=BRIDGE_PX)) & lot
    glab, gn = ndimage.label(groups, structure=np.ones((3, 3)))
    off = (x0 + ox, y0 + oy)
    u, front, depth = street_axis(lots)
    gms = [glab == g for g in range(1, gn + 1) if (glab == g).sum() >= MIN_BUILDING_PX]
    gms.sort(key=lambda m: _depths(m, off, fit, u, front)[0])
    # A sliver at the street is the front of the building behind it, cut off by a drawn line:
    # sheet 35w's 2007, the stone strip the sheet runs along the row's fronts, stands 0.7 m
    # before its house. Under PORCH_MAX_M2 and within FRONT_SLIVER_GAP_M of the next group,
    # it joins that group, so the census's front is the house and not the strip.
    if has_front and len(gms) > 1 and gms[0].sum() * fit.m_per_px ** 2 <= PORCH_MAX_M2 and \
            _depths(gms[1], off, fit, u, front)[0] - _depths(gms[0], off, fit, u, front)[1] <= FRONT_SLIVER_GAP_M:
        joined = ndimage.binary_closing(gms[0] | gms[1], iterations=BRIDGE_PX) & lot
        gms = [joined] + gms[2:]
    # More outlines than the census names, one of them against the house: the house cut in two
    # by a drawn wall the coarse scan's bridge does not close (sheet 35e's 2100, its frame
    # porch along the front, 1.3 m off it across the porch's dashed edge and the wall; 2140,
    # its 1B rear piece). The outline nearest the street group, within ABUT_M of it, joins it,
    # closed across the gap -- only while some outline would otherwise go unnamed, so a lot
    # the census names in full traces exactly as before. It runs after the sliver rule above: its
    # coarser closing and hole fill would take 2007's stone strip into the house's brick and lose
    # the strip's stone part (T-3018, landing after T-3009).
    abut_px = max(1, round(ABUT_M / fit.m_per_px))
    while has_front and len(gms) > 1 + n_rear:
        reach = ndimage.binary_dilation(gms[0], iterations=abut_px)
        near = [k for k in range(1, len(gms)) if (reach & gms[k]).any()]
        if not near:
            break
        k = max(near, key=lambda k: (reach & gms[k]).sum())
        gms[0] = ndimage.binary_fill_holes(ndimage.binary_closing(gms[0] | gms[k], iterations=abut_px)) & lot
        del gms[k]
    # A service building the sheet draws against the house's rear wall closes into the
    # house's group. When the census names more detached buildings than stand apart, the
    # street group's parts that begin in the rear REAR_SPLIT of the lot are split off as one.
    # Never where the census names no front building (there is no house to split it from),
    # and never so far that nothing is left at the street.
    # The rear share is widened a step at a time (REAR_SPLITS) only when the step before it
    # found no part to split, and only on a lot where NOTHING stands apart from the house: a
    # service building joined to it by a long rear range (sheet 35's 2035) begins further
    # forward than one drawn against the rear wall. Where some service building does stand
    # apart, ids left over are the joined-outline rule's (assign), as on sheet 20's 1720.
    split = None
    if gms and has_front and len(gms) - 1 < n_rear:
        pms0 = part_masks(fabric, gms[0])
        for share in (REAR_SPLITS if len(gms) == 1 else REAR_SPLITS[:1]):
            back = [pm for pm in pms0 if _depths(pm, off, fit, u, front)[0] >= (1 - share) * depth]
            if back and (gms[0] & ~ndimage.binary_dilation(np.logical_or.reduce(back), iterations=1)).sum() \
                    >= MIN_BUILDING_PX:
                U = np.logical_or.reduce(back)
                gms.insert(1, U)
                gms[0] = gms[0] & ~ndimage.binary_dilation(U, iterations=1)
                split = "drawn against the house's rear wall; split off as the census's detached building " \
                        f"(its parts begin in the rear {share:.0%} of the lot)"
                break
    out = []
    for k, gm in enumerate(gms):
        b = outline(gm, off, fit)
        pts = np.array(b["polygon_local_m"])
        along = (pts - front) @ u                       # <= 0: metres in from the street line
        b["from_street_m"] = [r2(-along.max()), r2(-along.min())]
        b["note"] = split if (split and k == 1) else None
        pms = part_masks(fabric, gm)
        # A crossed square marks a stable (T-1841's conventions): its diagonals cut the fill
        # into triangles, which are one range, not four.
        tri = [pm for pm in pms if _fill_ratio(pm) < TRIANGLE_FILL]
        crossed = bool(len(tri) >= 2 and _fill_ratio(np.logical_or.reduce(tri)) >= 0.85
                   and np.logical_or.reduce(tri).sum() >= 0.6 * gm.sum())
        if crossed:
            pms = [pm for pm in pms if not any(pm is t for t in tri)] + [np.logical_or.reduce(tri)]
        parts = []
        for pm in pms:
            cnt = np.bincount(sub[pm & fabric], minlength=4)[1:]
            o = outline(pm, off, fit)
            q = np.array(o["polygon_local_m"])
            al = (q - front) @ u
            parts.append({"material": CLASSES[int(np.argmax(cnt))], **o,
                          "from_street_m": [r2(-al.max()), r2(-al.min())],
                          "crossed": bool(crossed and pm is pms[-1])})
        parts.sort(key=lambda p: (p["from_street_m"][0], -p["area_m2"]))
        for k2, p in enumerate(parts):
            p["id"] = f"p{k2 + 1}"
        if parts:
            main = max(parts, key=lambda p: (p["area_m2"], -p["from_street_m"][0]))["id"]
            for p in parts:
                p["role"], p["role_rule"] = role(p, main, p["from_street_m"][1] - p["from_street_m"][0])
                if p["crossed"]:
                    p["role_rule"] += "; drawn as a crossed square, the sheet's mark for a stable"
        b["parts"] = [{k3: p[k3] for k3 in ("id", "role", "role_rule", "material", "crossed", "area_m2",
                                            "from_street_m", "polygon_local_m", "polygon_px")}
                      for p in parts]
        out.append(b)
    out.sort(key=lambda b: (b["from_street_m"][0], -b["area_m2"]))
    return out, depth


FRONT_KINDS = ("front", "attached", "non_building_use")   # what stands at the street


def for_1904(b: dict, crow: list) -> str:
    """Whether this outline IS the 1904 building, on the census's own ruling for its frontage.
    `as_mapped`: the census rules the polygon present in 1904 as the 1911 sheet draws it.
    `not_1904`: the census backcasts the frontage from the 1886 plate (`backcast_1886`), so a
    front outline here is the 1911 replacement -- or, with no front drawn, the 1904 house is
    simply not on this sheet -- and a draft must not stand on it.
    `phase_unresolved`: the census leaves the frontage's 1904 phase open (sheet 35's 2126,
    Robbins, building or rebuilding about then), so the draft declares one.
    `replaced_after_1904` reads as `not_1904` too: a directory or a dated advertisement puts
    another use on the lot in 1904 (sheet 35w's 2001-2003, 2101-2105 and 215-217, T-3013), so
    the 1911 front outline is the later building, and the 1904 one is unread, not drawn."""
    rows = [f for f in crow if set(b.get("census_ids", [])) & {p["id"] for p in f["polygons"]}]
    if any(f["decision_1904"] in ("backcast_1886", "replaced_after_1904") for f in rows) \
            and b.get("kind") in ("front", "non_building_use"):
        return "not_1904"
    if any(f["decision_1904"] == "phase_unresolved" for f in rows):
        return "phase_unresolved"
    return "as_mapped" if rows and all(f["decision_1904"] == "present_as_mapped" for f in rows) else \
        ("as_mapped_rear_of_backcast" if rows else "no_census_ruling")


def grounds(parcels: list, census: dict) -> list:
    """The parcels in sheet order, as grounds: a lot on its own, or -- where one census
    frontage with polygons spans several lots -- those lots together, in sheet order."""
    out, taken = [], set()
    for parcel in parcels:
        if parcel["id"] in taken:
            continue
        span = {parcel["id"]}
        for f in census["frontages"]:
            if parcel["id"] in f["parcel_ids"] and f["polygons"] and len(f["parcel_ids"]) > 1:
                span |= set(f["parcel_ids"])
        lots = [q for q in parcels if q["id"] in span and q["id"] not in taken]
        taken |= {q["id"] for q in lots}
        out.append(lots)
    return out


SHARE_NOTE = ("several census frontages stand on this one traced lot, so its buildings are divided "
              "among them: the buildings nearest the street, one per frontage, are its fronts, taken "
              "in address order (numbers rise southward on these blocks, so north first), and every "
              "other building goes to the front whose strip along the street holds its centre, the "
              "strips meeting midway between neighbouring fronts")


def frontage_shares(buildings: list, crow: list, lots: list, depth: float) -> list:
    """[(census rows, buildings)] for one ground. One share holding everything, unless the
    ground carries several census frontages with a front each (sheet 35's prairie_2000:
    2000, 2010 and 2018 on one T-0474 strip), when the rule in SHARE_NOTE divides it."""
    fronted = [f for f in crow if any(p["kind"] in FRONT_KINDS for p in f["polygons"])]
    if len(fronted) < 2 or len(buildings) < len(fronted) or len(fronted) != len(crow):
        return [(crow, buildings)]
    u, _, _ = _street_axis(lots[0])
    along = np.array([-u[1], u[0]])             # along the street line

    def pos(b):
        pts = np.array(b["polygon_local_m"])
        return float(pts.mean(axis=0) @ along)

    # Each front must be a building of its own that begins in the street half of the lot;
    # where fewer do, the frontages share one drawn building (sheet 20's 1700/1706, a pair
    # of townhouses traced as one) and the ground stays one share.
    fronts = sorted(buildings, key=lambda b: b["from_street_m"][0])[:len(fronted)]
    if any(b["from_street_m"][0] >= depth / 2 for b in fronts):
        return [(crow, buildings)]
    order = sorted(fronted, key=lambda f: int(re.match(r"\d+", f["printed_number_1911"]).group()))
    north = 1.0 if along[1] > 0 else -1.0        # the street axis, pointed north
    fronts.sort(key=lambda b: -north * pos(b))   # north first: lowest number first
    cuts = [(pos(a) + pos(b)) / 2 for a, b in zip(fronts, fronts[1:])]
    shares = [(f_, [b]) for f_, b in zip(order, fronts)]
    for b in buildings:
        if any(b is f for f in fronts):
            continue
        k = sum(1 for c in cuts if north * pos(b) < north * c)
        shares[k][1].append(b)
    return [([f_], bs) for f_, bs in shares]


def assign(buildings: list, census_rows: list, vacant: list, depth: float) -> list:
    """Census polygon ids onto traced buildings (rule in the module doc)."""
    polys = [p for row in census_rows for p in row["polygons"]]
    front = [p["id"] for p in polys if p["kind"] in FRONT_KINDS]
    rear = [p["id"] for p in polys if p["kind"] == "detached_service"]
    vac = [v["id"] for v in vacant]
    left = list(buildings)
    if front and left:
        b = min(left, key=lambda b: b["from_street_m"][0])
        dwelling = any(p["kind"] in ("front", "attached") for p in polys)
        b["census_ids"], b["kind"] = front, "front" if dwelling else "non_building_use"
        left.remove(b)
    left.sort(key=lambda b: -b["from_street_m"][1])          # nearest the alley first
    placed = []
    for pid in list(rear):
        if not left:
            break
        b = left.pop(0)
        b["census_ids"], b["kind"] = [pid], "detached_service"
        placed.append(b)
    # More detached ids than detached outlines: the sheet draws two service buildings joined
    # (a stable against a range), so they trace as one outline of several parts. The ids left
    # over go onto the joined outline nearest the alley that has more than one part.
    over = [i for i in rear if not any(i in b["census_ids"] for b in placed)]
    joined = [b for b in placed if len(b.get("parts", [])) > 1]
    if over and joined:
        joined[0]["census_ids"] = joined[0]["census_ids"] + over
        joined[0]["note"] = ((joined[0].get("note") + "; ") if joined[0].get("note") else "") + (
            f"the census names {len(joined[0]['census_ids'])} detached buildings here and the sheet draws "
            "them joined: one outline carries every id, and its parts are where they divide")
    for b in left:
        if vac:
            b["census_ids"], b["kind"] = vac, "vacant_ground_structure"
        else:
            b["census_ids"], b["kind"] = [], "unassigned"
    want = front + rear
    got = {i for b in buildings for i in b.get("census_ids", [])}
    return [i for i in want if i not in got]


# ---------------------------------------------------------------------------
# the document


def build(sheet: str) -> dict:
    spec = SHEETS[sheet]
    gcp = json.loads((GCP_DIR / f"{spec['gcp']}_gcps.json").read_text(encoding="utf-8"))
    raster = REPO / gcp["raster"]["path"]
    if sha256(raster) != gcp["raster"]["sha256"]:
        raise SystemExit(f"{raster}: sha256 differs from {spec['gcp']}_gcps.json; re-read before tracing")
    fit = Fit(gcp)
    px_rules = set_px_rules(fit.m_per_px)
    globals()["FRAME_R_MIN"] = spec.get("frame_r_min", 170)
    grid = json.loads(GRID.read_text(encoding="utf-8"))
    census = json.loads((spec.get("census_path") or CENSUS_DIR / spec["census"]).read_text(encoding="utf-8"))
    parcels = [p for p in grid["parcels"] if p["block"] in spec["blocks"] and (
        p["id"] in spec["parcels"] if spec.get("parcels") else p["street"] == "prairie")]
    bx = [fit.pixel(*q) for p in parcels for q in p["polygon_local_m"]]
    x0, y0 = int(min(p[0] for p in bx)) - 8, int(min(p[1] for p in bx)) - 8
    x1, y1 = int(max(p[0] for p in bx)) + 8, int(max(p[1] for p in bx)) + 8
    with Image.open(raster) as im:
        rgb = np.asarray(im.convert("RGB").crop((x0, y0, x1, y1)))
    cls = classify(rgb)
    rows, problems = [], []
    for lots in grounds(parcels, census):
        parcel, ids = lots[0], {q["id"] for q in lots}
        crow = [f for f in census["frontages"] if ids & set(f["parcel_ids"]) and f["polygons"]]
        alias = [f["frontage_id"] for f in census["frontages"]
                 if ids & set(f["parcel_ids"]) and not f["polygons"]]
        vac = [v for v in census["vacant_ground"] if ids & set(v["parcel_ids"])]
        n_rear = sum(1 for f in crow for p in f["polygons"] if p["kind"] == "detached_service")
        has_front = any(p["kind"] in FRONT_KINDS for f in crow for p in f["polygons"])
        buildings, depth = read_parcel(cls, (x0, y0), lots, fit, n_rear, has_front)
        shares = frontage_shares(buildings, crow, lots, depth)
        missing = [i for rows_, bs in shares for i in assign(bs, rows_, vac, depth)]
        # A frontage the census rules a non-building use with nothing drawn on it (sheet
        # 35's 2141, "no building, street to alley") is the ground itself: its id is carried
        # on the row, not reported as untraced.
        on_ground = [i for i in missing if not buildings and i in
                     {p["id"] for f in crow for p in f["polygons"] if p["kind"] == "non_building_use"}]
        missing = [i for i in missing if i not in on_ground]
        decision = sorted({f["decision_1904"] for f in crow}) or (["vacant"] if vac else [])
        for k, b in enumerate(buildings):
            b["id"] = f"s{sheet}fp-{parcel['id'].removeprefix('prairie_')}-b{k + 1}"
            b["for_1904"] = for_1904(b, crow)
        rows.append({
            "parcel_id": parcel["id"],
            **({"ground_parcel_ids": [q["id"] for q in lots],
                "ground_note": "one census frontage spans these lots, so they are read as one ground"}
               if len(lots) > 1 else {}),
            "side": parcel["side"],
            "addresses_1911": parcel.get("addresses_1911", []),
            "census_frontages": [f["frontage_id"] for f in crow],
            "census_aliases": alias,
            "census_decision_1904": decision,
            "lot_depth_m": r2(depth),
            "census_ids_not_traced": missing,
            **({"census_ids_on_ground": on_ground,
                "on_ground_note": "the census rules this frontage a non-building use and the sheet draws "
                                  "nothing on it: the lot itself is its outline"} if on_ground else {}),
            **({"frontage_shares": [{"frontage_id": r_[0]["frontage_id"] if r_ else None,
                                      "buildings": [b["id"] for b in bs]} for r_, bs in shares],
                "frontage_shares_note": SHARE_NOTE} if len(shares) > 1 else {}),
            "buildings": [{k: b[k] for k in ("id", "kind", "census_ids", "for_1904", "note", "area_m2", "from_street_m",
                                             "polygon_local_m", "polygon_px", "parts")}
                          for b in buildings],
        })
        if missing:
            problems.append(f"{parcel['id']}: census polygon(s) with no traced outline: {', '.join(missing)}")
    n_b = sum(len(r["buildings"]) for r in rows)
    return {
        "_doc": ("Building footprints on Sanborn 1911 vol. 3 sheet " + sheet + " for the 1904 target, one "
                 "outline per building and per drawn part, keyed to the " + spec["census_ticket"] + " sheet census. "
                 "GENERATED by tools/trace_prairie_1904_footprints.py from the committed raster through the "
                 "T-1250 fit -- do not hand-edit; re-run the tool. " + spec["ticket"] + "."),
        "ticket": spec["ticket"],
        "sheet": sheet,
        "target_date": census["target_date"],
        "source": gcp["source"],
        "raster": gcp["raster"],
        "frame": "local ENU metres of data/datum.json (x east, y north); polygon_px on the raster named above",
        "fit": {"gcp_file": f"data/traces/gcp/{spec['gcp']}_gcps.json", **gcp["fit"]["coefficients"],
                "m_per_px": fit.m_per_px,
                "fit_rms_m": gcp["fit"]["rms_m"],
                "independent_rms_m": gcp.get("independent_checks", {}).get("rms_component_m")},
        "census": (str(spec["census_path"].relative_to(REPO)) if spec.get("census_path")
                   else f"chicago/prairie_1904_v1/data/sheet_census/{spec['census']}"),
        "parcels_from": "data/street_grid/1904.json",
        "method": {
            "classes": f"brick r-g>30 & r-b>25 & r>120; stone b-r>=10 & g>110; frame r-b>80 & g-b>60 & r>{FRAME_R_MIN} (8-bit sRGB)"
                       + (f"; none where (r+g+b)/3<{LINE_MEAN}, a drawn line on this coarse scan, its "
                          f"breaks of up to {LINE_GAP_PX} px closed along rows and columns" if LINE_RULE else ""),
            **({"px_scale": px_scale(fit.m_per_px)} if px_scale(fit.m_per_px) != 1.0 else {}),
            "bridge_px": BRIDGE_PX, "line_half_px": LINE_HALF_PX, "simplify_px": SIMPLIFY_PX,
            "min_part_m2": r2(MIN_PART_PX * fit.m_per_px ** 2),
            "min_building_m2": r2(MIN_BUILDING_PX * fit.m_per_px ** 2),
            "assignment": ("the building nearest the street takes the frontage's front, attached and "
                           "non_building_use census ids; the others take its detached_service ids nearest the alley "
                           "first, and detached ids left over go onto the joined (several-part) outline nearest the "
                           "alley; one left over on vacant ground takes that ground's id, any other is kept as "
                           "unassigned. A frontage spanning several lots is read on their union"),
        },
        "tiers": {
            "outline": f"inferred -- a 1911 survey carried to 1904 on {spec['census_ticket']}'s per-polygon ruling",
            "part_role": "inferred -- colour, size and position by the rule in each part's role_rule",
            "storeys": "not read here: the census's printed notation is the storey reading",
            "for_1904": ("per building: as_mapped (the census rules it present in 1904 as drawn); not_1904 (a "
                         "front the census backcasts from the 1886 plate -- the 1911 outline is a later "
                         "replacement and no draft stands on it); as_mapped_rear_of_backcast (a rear building "
                         "on a backcast frontage, drawn in 1911 and not ruled out); no_census_ruling"
                         + ("; phase_unresolved (the census leaves its 1904 phase open and the draft declares one)"
                            if any(f["decision_1904"] == "phase_unresolved" for f in census["frontages"]
                                   if f["polygons"]) else "")
                         + ("; a front on a frontage ruled replaced_after_1904 is not_1904 as well (a dated "
                            "record puts another use on the lot in 1904, so the 1911 outline is the later "
                            "building and the 1904 one is unread)"
                            if any(f["decision_1904"] == "replaced_after_1904" for f in census["frontages"]) else "")),
        },
        "accuracy": accuracy(gcp),
        "counts": {"parcels": len(rows), "buildings": n_b,
                   "parts": sum(len(b["parts"]) for r in rows for b in r["buildings"])},
        "problems": problems,
        "parcels": rows,
    }


def accuracy(gcp: dict) -> str:
    """The sheet's absolute accuracy, as its own GCP file states it -- never borrowed from another sheet."""
    ind = gcp.get("independent_checks")
    if ind:
        head = (f"the georeference's independent check ({ind['rms_component_m']} m RMS per component, worst "
                f"{ind['max_component_m']} m)")
    else:
        head = (f"the georeference's own fit residual ({gcp['fit']['rms_m']} m RMS on its control crossings; "
                "the sheet's GCP file carries no independent check, so nothing better is claimed)")
    m = gcp["fit"].get("scale_m_per_px") or abs(gcp["fit"]["coefficients"]["a"])
    if px_scale(m) > 1.0:
        head += (f"; the fit is a similarity at the printed scale on {gcp['fit'].get('degrees_of_freedom')} "
                 "degrees of freedom, so its residual says little about the sheet away from its crossings")
        return head + (f", plus about a pixel of trace ({m:.2f} m on this coarser copy); relative accuracy "
                       f"inside one lot is the trace's, about {2 * m:.1f} m")
    return head + " plus about a pixel of trace; relative accuracy inside one lot is the trace's, about 0.1 m"


_PAIR = re.compile(r"\[\s*(-?[\d.]+),\s*(-?[\d.]+)\s*\]")


def dumps(doc: dict) -> str:
    """Indented, with every coordinate pair on one line."""
    return _PAIR.sub(r"[\1, \2]", json.dumps(doc, indent=1, ensure_ascii=False)) + "\n"


# ---------------------------------------------------------------------------
# checks


def contract(doc: dict, grid: dict) -> list:
    bad = []
    parcels = {p["id"]: p for p in grid["parcels"]}
    seen = {}
    for row in doc["parcels"]:
        lots = [parcels[i]["polygon_local_m"] for i in row.get("ground_parcel_ids", [row["parcel_id"]])]
        if row["census_ids_not_traced"]:
            bad.append(f"{row['parcel_id']}: census ids with no outline {row['census_ids_not_traced']}")
        for b in row["buildings"]:
            poly = b["polygon_local_m"]
            if area(poly) <= 0:
                bad.append(f"{b['id']}: outline not counter-clockwise or empty")
            if b["kind"] == "unassigned":
                bad.append(f"{b['id']}: a building the census does not name")
            for p in poly:
                if not any(inside_tol(p, lot, 0.35) for lot in lots):
                    bad.append(f"{b['id']}: vertex {p} outside its lot {row['parcel_id']}")
                    break
            for i in b["census_ids"]:
                if i in seen:
                    bad.append(f"{i}: assigned twice ({seen[i]}, {b['id']})")
                seen[i] = b["id"]
            if not b["parts"]:
                bad.append(f"{b['id']}: no parts")
    return bad


def inside_tol(p, poly, tol) -> bool:
    x, y = p
    n, inside = len(poly), False
    for k in range(n):
        (x1, y1), (x2, y2) = poly[k], poly[(k + 1) % n]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            inside = not inside
    if inside:
        return True
    for k in range(n):
        (x1, y1), (x2, y2) = poly[k], poly[(k + 1) % n]
        dx, dy = x2 - x1, y2 - y1
        t = max(0.0, min(1.0, ((x - x1) * dx + (y - y1) * dy) / (dx * dx + dy * dy)))
        if math.hypot(x - (x1 + t * dx), y - (y1 + t * dy)) <= tol:
            return True
    return False


def self_test() -> int:
    fails = 0

    def ok(name, cond):
        nonlocal fails
        print(f"  {'ok  ' if cond else 'FAIL'} {name}")
        fails += 0 if cond else 1

    sq = np.zeros((20, 20), bool); sq[5:15, 4:12] = True
    ring = trace(sq)
    ok("trace: a rectangle is four corners", sorted(ring) == sorted([(4, 5), (12, 5), (12, 15), (4, 15)]))
    ok("trace: its area is the pixel count", abs(abs(area(ring)) - sq.sum()) < 1e-9)
    ell = sq.copy(); ell[10:15, 8:12] = False
    ok("trace: an L is six corners", len(trace(ell)) == 6 and abs(abs(area(trace(ell))) - ell.sum()) < 1e-9)
    diag = np.zeros((30, 30), bool)
    for k in range(20):
        diag[5 + k, 5:6 + k] = True
    ok("simplify: a staircase hypotenuse becomes a line", len(simplify(trace(diag), SIMPLIFY_PX)) == 3)
    px = np.array([[[220, 160, 165], [160, 180, 195], [235, 215, 90], [232, 222, 200], [10, 10, 10]]], np.uint8)
    ok("classify: brick, stone, frame, paper, ink", classify(px).tolist() == [[1, 2, 3, 0, 0]])
    lot = [[0, 0], [10, 0], [10, 10], [0, 10]]
    ok("inside_tol: inside", inside_tol([5, 5], lot, 0.35))
    ok("inside_tol: within tolerance", inside_tol([10.3, 5], lot, 0.35))
    ok("inside_tol: refuses outside", not inside_tol([10.5, 5], lot, 0.35))
    b1 = {"from_street_m": [2.0, 20.0]}; b2 = {"from_street_m": [45.0, 53.0]}
    rows = [{"polygons": [{"id": "f", "kind": "front"}, {"id": "w", "kind": "attached"},
                          {"id": "r", "kind": "detached_service"}]}]
    missing = assign([b2, b1], rows, [], 54.0)
    ok("assign: street building takes front and attached", b1["census_ids"] == ["f", "w"])
    ok("assign: alley building takes the rear", b2["census_ids"] == ["r"] and not missing)
    b3 = {"from_street_m": [2.0, 20.0]}
    ok("assign: an untraced census id is reported", assign([b3], rows, [], 54.0) == ["r"])
    st = {"from_street_m": [1.0, 20.0]}
    ok("assign: a non-building use at the street takes its id",
       assign([st], [{"polygons": [{"id": "n", "kind": "non_building_use"}]}], [], 30.0) == []
       and st["kind"] == "non_building_use" and st["census_ids"] == ["n"])
    h = {"from_street_m": [2.0, 20.0]}; j = {"from_street_m": [40.0, 55.0], "parts": [{}, {}]}
    two = [{"polygons": [{"id": "f", "kind": "front"}, {"id": "r1", "kind": "detached_service"},
                         {"id": "r2", "kind": "detached_service"}]}]
    ok("assign: two detached ids on one joined outline", assign([h, j], two, [], 56.0) == []
       and j["census_ids"] == ["r1", "r2"] and "joined" in j["note"])
    j1 = {"from_street_m": [40.0, 55.0], "parts": [{}]}
    ok("assign: a one-part outline does not absorb a second id",
       assign([dict(h), j1], two, [], 56.0) == ["r2"])
    cen = {"frontages": [{"parcel_ids": ["a", "b"], "polygons": [{"id": "r", "kind": "detached_service"}]},
                         {"parcel_ids": ["c"], "polygons": [{"id": "f", "kind": "front"}]}]}
    ok("grounds: a frontage over two lots reads them as one ground",
       [[q["id"] for q in g] for g in grounds([{"id": "a"}, {"id": "b"}, {"id": "c"}], cen)] == [["a", "b"], ["c"]])
    grid = {"parcels": [{"id": "x", "polygon_local_m": lot}]}
    good = {"parcels": [{"parcel_id": "x", "census_ids_not_traced": [], "buildings": [
        {"id": "b", "kind": "front", "census_ids": ["f"], "polygon_local_m": [[1, 1], [4, 1], [4, 4]],
         "parts": [{}]}]}]}
    ok("contract: a good document passes", contract(good, grid) == [])
    import copy
    out = copy.deepcopy(good); out["parcels"][0]["buildings"][0]["polygon_local_m"][1] = [12, 1]
    ok("contract: refuses an outline outside its lot", any("outside" in m for m in contract(out, grid)))
    cw = copy.deepcopy(good); cw["parcels"][0]["buildings"][0]["polygon_local_m"].reverse()
    ok("contract: refuses a clockwise outline", any("counter-clockwise" in m for m in contract(cw, grid)))
    un = copy.deepcopy(good); un["parcels"][0]["buildings"][0]["kind"] = "unassigned"
    ok("contract: refuses an unnamed building", any("does not name" in m for m in contract(un, grid)))
    tw = copy.deepcopy(good); tw["parcels"][0]["buildings"].append(copy.deepcopy(tw["parcels"][0]["buildings"][0]))
    ok("contract: refuses a census id assigned twice", any("twice" in m for m in contract(tw, grid)))
    fine = set_px_rules(0.0508)
    ok("px rules: the scans they were set on read at scale 1.0, unchanged",
       {k: fine[k] for k in BASE_PX} == BASE_PX and not fine["LINE_RULE"]
       and set_px_rules(REF_M_PER_PX)["BRIDGE_PX"] == BASE_PX["BRIDGE_PX"])
    coarse = set_px_rules(0.185854)
    ok("px rules: a scan 3.7x coarser scales lengths, areas by the square, and takes the line rule",
       coarse["LINE_RULE"] and coarse["LINE_HALF_PX"] == 1 and coarse["MIN_PART_PX"] == round(360 / 3.7 ** 2)
       and coarse["BRIDGE_PX"] == round(7 / 3.7) + 1)
    wall = np.full((9, 9, 3), (218, 168, 172), np.uint8); wall[:, 4] = (134, 96, 95); wall[3:5, 4] = (218, 168, 172)
    ok("classify: on a coarse scan a blurred one-pixel wall is line, its 2 px break closed",
       (classify(wall)[:, 4] == 0).all() and (classify(wall)[:, 3] == 1).all())
    set_px_rules(REF_M_PER_PX)
    ok("classify: on a fine scan the same wall reads as the brick it is drawn on",
       (classify(wall)[:, 4] == 1).all())
    lot_w = {"side": "west", "corners_local_m": {"NE_street": [50, 90], "SE_street": [50, 0],
                                                 "NW_rear": [0, 90], "SW_rear": [0, 0]}}

    def box(x0, y0, x1, y1, d):
        return {"polygon_local_m": [[x0, y0], [x1, y0], [x1, y1], [x0, y1]], "from_street_m": [d, d + 10]}
    hs = [box(30, 70, 47, 85, 3.0), box(30, 40, 47, 52, 3.0), box(30, 5, 47, 20, 3.0)]
    ss = [box(0, 72, 8, 84, 42.0), box(0, 38, 8, 50, 42.0), box(0, 6, 8, 18, 42.0)]
    fr = [{"frontage_id": n, "printed_number_1911": n,
           "polygons": [{"id": f"{n}-f", "kind": "front"}, {"id": f"{n}-r", "kind": "detached_service"}]}
          for n in ("2018", "2000", "2010")]
    sh = frontage_shares(hs + ss, fr, [lot_w], 50.0)
    ok("frontage shares: three frontages on one lot, north first in address order, each with its stable",
       [(r_[0]["frontage_id"], [hs.index(b) if b in hs else 10 + ss.index(b) for b in bs]) for r_, bs in sh]
       == [("2000", [0, 10]), ("2010", [1, 11]), ("2018", [2, 12])])
    one = frontage_shares([hs[0], ss[0]], fr[:2], [lot_w], 50.0)
    ok("frontage shares: two frontages on one drawn building stay one share", len(one) == 1)
    print(f"self-test: {'PASS' if not fails else f'{fails} FAILED'}")
    return 1 if fails else 0


def overlay(sheet: str, doc: dict, out_dir: Path) -> None:
    gcp = json.loads((GCP_DIR / f"{SHEETS[sheet]['gcp']}_gcps.json").read_text(encoding="utf-8"))
    with Image.open(REPO / gcp["raster"]["path"]) as im:
        base = im.convert("RGB")
    # A coarse scan is drawn on at the fine scans' paper scale, so its images read alike.
    sc = max(1, round(px_scale(doc["fit"]["m_per_px"])))
    if sc > 1:
        base = base.resize((base.width * sc, base.height * sc), Image.NEAREST)

    def P(q):
        return (q[0] * sc, q[1] * sc)
    draw = ImageDraw.Draw(base)
    colour = {"main": (0, 90, 200), "range": (0, 160, 60), "porch": (230, 120, 0), "stone_front": (150, 0, 180)}
    for row in doc["parcels"]:
        for b in row["buildings"]:
            for p in b["parts"]:
                draw.line([P(q) for q in p["polygon_px"] + p["polygon_px"][:1]], fill=colour[p["role"]], width=3)
            ring = b["polygon_px"] + b["polygon_px"][:1]
            draw.line([P(q) for q in ring], fill=(220, 0, 0) if b["kind"] != "unassigned" else (0, 0, 0), width=5)
            x = min(P(q)[0] for q in b["polygon_px"]); y = min(P(q)[1] for q in b["polygon_px"])
            draw.text((x + 8, y + 8), b["id"].split("-", 1)[1], fill=(200, 0, 0))
    out_dir.mkdir(parents=True, exist_ok=True)
    xs = [P(q)[0] for r in doc["parcels"] for b in r["buildings"] for q in b["polygon_px"]]
    ys = [P(q)[1] for r in doc["parcels"] for b in r["buildings"] for q in b["polygon_px"]]
    box = (int(min(xs)) - 60, int(min(ys)) - 60, int(max(xs)) + 60, int(max(ys)) + 60)
    crop = base.crop(box)
    crop.resize((crop.width // 3, crop.height // 3), Image.LANCZOS).save(out_dir / "overlay.jpg", quality=82)
    mid = (box[0] + box[2]) // 2
    for name, b in (("overlay-west.jpg", (box[0], box[1], mid - 150, box[3])),
                    ("overlay-east.jpg", (mid - 150, box[1], box[2], box[3]))):
        c = base.crop(b)
        c.resize((c.width * 2 // 5, c.height * 2 // 5), Image.LANCZOS).save(out_dir / name, quality=82)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--overlay", metavar="DIR")
    ap.add_argument("--sheet", choices=sorted(SHEETS), help="only this sheet (required with --overlay)")
    a = ap.parse_args()
    if a.overlay and not a.sheet:
        ap.error("--overlay writes one sheet's images; name it with --sheet")
    if a.self_test:
        return self_test()
    grid = json.loads(GRID.read_text(encoding="utf-8"))
    rc = 0
    for sheet, spec in SHEETS.items():
        if a.sheet and sheet != a.sheet:
            continue
        doc = build(sheet)
        text = dumps(doc)
        bad = contract(doc, grid)
        rel = spec["out"].relative_to(ROOT)
        if a.check:
            have = spec["out"].read_text(encoding="utf-8") if spec["out"].exists() else ""
            if have != text:
                print(f"FAIL {rel}: stale -- re-run tools/trace_prairie_1904_footprints.py")
                rc = 1
        else:
            spec["out"].write_text(text, encoding="utf-8")
        if a.overlay:
            overlay(sheet, doc, Path(a.overlay))
        for m in bad:
            print(f"FAIL sheet {sheet}: {m}")
        rc = rc or (1 if bad else 0)
        c = doc["counts"]
        print(f"{'ok  ' if not bad else 'FAIL'} sheet {sheet}: {c['parcels']} parcels, {c['buildings']} buildings, "
              f"{c['parts']} parts -> {rel}")
    return rc


if __name__ == "__main__":
    sys.exit(main())
