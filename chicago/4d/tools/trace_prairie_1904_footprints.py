#!/usr/bin/env python3
"""Digitise the 1904 building footprints off a Prairie Avenue Sanborn sheet (T-2327, T-2328).

    python3 tools/trace_prairie_1904_footprints.py            # (re)write the footprint file(s)
    python3 tools/trace_prairie_1904_footprints.py --check    # re-derive, change nothing
    python3 tools/trace_prairie_1904_footprints.py --self-test
    python3 tools/trace_prairie_1904_footprints.py --sheet 20 --overlay DIR   # one sheet's study images

SHEETS. Sheet 28 (18th-20th, T-2327, for T-2159) and sheet 20 (16th-18th, T-2328, for
T-2160). A sheet is added as one SHEETS entry -- its fit, its census, its blocks -- and the
reading below is the same for every sheet; nothing in it is tuned per sheet.

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
PART_ERODE_PX = 1      # parts are labelled on fabric eroded this far, then grown back
TRIANGLE_FILL = 0.62   # under this share of its box a part is a triangle (a stable's cross)
REAR_SPLIT = 0.30      # the rear share of a lot a split-off service building begins in


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
    out[(r - b > 80) & (g - b > 60) & (r > 170)] = 3
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
    c = parcel["corners_local_m"]
    if parcel["side"] == "west":
        front = (np.array(c["NE_street"]) + np.array(c["SE_street"])) / 2
        rear = (np.array(c["NW_rear"]) + np.array(c["SW_rear"])) / 2
    else:
        front = (np.array(c["NW_street"]) + np.array(c["SW_street"])) / 2
        rear = (np.array(c["NE_rear"]) + np.array(c["SE_rear"])) / 2
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
    # A service building the sheet draws against the house's rear wall closes into the
    # house's group. When the census names more detached buildings than stand apart, the
    # street group's parts that begin in the rear REAR_SPLIT of the lot are split off as one.
    # Never where the census names no front building (there is no house to split it from),
    # and never so far that nothing is left at the street.
    split = None
    if gms and has_front and len(gms) - 1 < n_rear:
        back = [pm for pm in part_masks(fabric, gms[0])
                if _depths(pm, off, fit, u, front)[0] >= (1 - REAR_SPLIT) * depth]
        if back and (gms[0] & ~ndimage.binary_dilation(np.logical_or.reduce(back), iterations=1)).sum() \
                >= MIN_BUILDING_PX:
            U = np.logical_or.reduce(back)
            gms.insert(1, U)
            gms[0] = gms[0] & ~ndimage.binary_dilation(U, iterations=1)
            split = "drawn against the house's rear wall; split off as the census's detached building " \
                    f"(its parts begin in the rear {REAR_SPLIT:.0%} of the lot)"
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
    simply not on this sheet -- and a draft must not stand on it."""
    rows = [f for f in crow if set(b.get("census_ids", [])) & {p["id"] for p in f["polygons"]}]
    if any(f["decision_1904"] == "backcast_1886" for f in rows) and b.get("kind") in ("front", "non_building_use"):
        return "not_1904"
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
    grid = json.loads(GRID.read_text(encoding="utf-8"))
    census = json.loads((CENSUS_DIR / spec["census"]).read_text(encoding="utf-8"))
    parcels = [p for p in grid["parcels"] if p["block"] in spec["blocks"] and p["street"] == "prairie"]
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
        missing = assign(buildings, crow, vac, depth)
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
        "census": f"chicago/prairie_1904_v1/data/sheet_census/{spec['census']}",
        "parcels_from": "data/street_grid/1904.json",
        "method": {
            "classes": "brick r-g>30 & r-b>25 & r>120; stone b-r>=10 & g>110; frame r-b>80 & g-b>60 & r>170 (8-bit sRGB)",
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
                         "on a backcast frontage, drawn in 1911 and not ruled out); no_census_ruling"),
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
    print(f"self-test: {'PASS' if not fails else f'{fails} FAILED'}")
    return 1 if fails else 0


def overlay(sheet: str, doc: dict, out_dir: Path) -> None:
    gcp = json.loads((GCP_DIR / f"{SHEETS[sheet]['gcp']}_gcps.json").read_text(encoding="utf-8"))
    with Image.open(REPO / gcp["raster"]["path"]) as im:
        base = im.convert("RGB")
    draw = ImageDraw.Draw(base)
    colour = {"main": (0, 90, 200), "range": (0, 160, 60), "porch": (230, 120, 0), "stone_front": (150, 0, 180)}
    for row in doc["parcels"]:
        for b in row["buildings"]:
            for p in b["parts"]:
                draw.line([tuple(q) for q in p["polygon_px"] + p["polygon_px"][:1]], fill=colour[p["role"]], width=3)
            ring = b["polygon_px"] + b["polygon_px"][:1]
            draw.line([tuple(q) for q in ring], fill=(220, 0, 0) if b["kind"] != "unassigned" else (0, 0, 0), width=5)
            x = min(q[0] for q in b["polygon_px"]); y = min(q[1] for q in b["polygon_px"])
            draw.text((x + 8, y + 8), b["id"].split("-", 1)[1], fill=(200, 0, 0))
    out_dir.mkdir(parents=True, exist_ok=True)
    xs = [q[0] for r in doc["parcels"] for b in r["buildings"] for q in b["polygon_px"]]
    ys = [q[1] for r in doc["parcels"] for b in r["buildings"] for q in b["polygon_px"]]
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
