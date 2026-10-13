#!/usr/bin/env python3
"""The 1904 context city (T-2477): faded stand-ins on every part of the map not yet built.

    python3 tools/build_context_1904.py            # (re)write data/context/1904.json
    python3 tools/build_context_1904.py --check    # re-derive, change nothing
    python3 tools/build_context_1904.py --self-test

THE ASK. The owner, 2026-10-13: "for all the areas we have not developed yet, but are on the
map, please include very simple buildings in varied appropriate colors based on Sanborn or
other projections, make them just gently faded ... I don't want to spend many triangles so
simple boxes are ok or very simple single color house structure shapes for the balance of
the city, and same with flora for it". Prairie Avenue is the built scene; this is the city
around it, drawn as what MIGHT be there and looking it (renderers/web/js/context.js fades it).

TWO KINDS OF STAND-IN, and the file says which every row is (`src`):

  sheet   READ off the committed Sanborn 1911 sheets 20, 28 and 35, through the same T-1250
          fit and the same colour classes as tools/trace_prairie_1904_footprints.py: every
          drawn building on the Indiana and Calumet faces, the cross-street lots and Calumet
          east at 20th (the sheets' own ground, Prairie Avenue's lots taken out). Each drawn
          part becomes one rectangle: the smallest that holds it. Its material is the sheet's
          colour (pink brick, blue stone, yellow frame). The outline is INFERRED for 1904 on
          Glessner House's reading that these sheets changed only at 1609-1611 and 1620
          Prairie between 1904 and 1911 (chicago/reference/prairie-avenue/.../README.md).
  project PROJECTED where no sheet is in hand: the rest of the e1871 box and a ring past it.
          Streets carried on the pitch the traced grid measures (Michigan, Indiana, Prairie,
          Calumet and 16th to 22nd as data/street_grid/1904.json and the terrain spec place
          them, repeated outward), lots on the frontages the traced grid's own non-Prairie
          lots measure, and the material mix the sheets above measure. RECONSTRUCTED.

Every height, roof, colour and tree is RECONSTRUCTED by the rules in RULES below: the sheets
print storey figures, and this tool does not read them (the census does that for Prairie
Avenue only). docs/LIBERTIES.md carries the one liberty that covers all of it (LIBERTY).

A stand-in never stands where a real building does: the renderer drops any rectangle a placed
structure's footprint touches, at load, so a draft that lands on Indiana or Calumet later
(T-2162 and its refiners) replaces its stand-in with no regeneration here.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import trace_prairie_1904_footprints as tf  # noqa: E402  (the fit, the colour classes, the parts)

ROOT = HERE.parent
REPO = ROOT.parents[1]
GRID = ROOT / "data" / "street_grid" / "1904.json"
HF = ROOT / "data" / "terrain" / "epochs" / "e1871_postfire"
SPEC = HF / "terrain_spec.json"
OUT = ROOT / "data" / "context" / "1904.json"
TICKET = "T-2477"
LIBERTY = "L-context-city-2477"
SEED = 19040701

SOURCES = {"20": "sanborn_1911_chicago_v3_sheet_20", "28": "sanborn_1911_chicago_v3_sheet_28",
           "35": "sanborn_1911_chicago_v3_sheet_35"}

# The sheets' own ground, as the grid's blocks (Prairie Avenue's lots are taken out of each)
# plus one piece the grid has no block for: Calumet's east face at 20th Street on sheet 28,
# its rectangle read at sheet pixels (4680, 4890)-(5420, 6080) through the sheet's fit.
SHEETS = {
    "20": {"blocks": ["blk_indiana_prairie_16_18"], "extra": []},
    "28": {"blocks": ["blk_prairie_calumet_18_20"],
           "extra": [[[1547.0, -3400.0], [1585.3, -3399.3], [1586.4, -3460.1], [1548.1, -3460.8]]]},
    "35": {"blocks": ["blk_indiana_prairie_20_21", "blk_indiana_prairie_21_22",
                      "blk_prairie_calumet_20_21", "blk_prairie_calumet_21_22"], "extra": []},
}
MATS = ("brick", "stone", "frame")

# ---------------------------------------------------------------------------------------------
# the rules (all RECONSTRUCTED; docs/LIBERTIES.md LIBERTY)

RULES = {
    "dwelling_masonry": {"eave_m": 10.5, "why": "a brick or stone house of 2-3 storeys on a raised "
                         "basement, the '3B' and '2B' the sheets print most often on these faces"},
    "wing": {"eave_m": 7.0, "why": "a drawn range behind or beside the main body: the sheets' rear '2B'"},
    "porch": {"eave_m": 3.2, "max_m2": 25.0, "why": "a part under 25 m2 and under a quarter of the main body"},
    "outbuilding": {"eave_m": 5.5, "max_m2": 110.0, "why": "a separate rear building under 110 m2: the "
                    "sheets' 2-storey stables, barns and sheds (a 1911 garage read as a stable)"},
    "frame_dwelling": {"eave_m": 6.5, "why": "a frame (yellow) house of 2 storeys"},
    "block": {"eave_m": 13.0, "min_m2": 450.0, "why": "a building over 450 m2: flats, an institution or a "
              "works, 3-4 storeys under a flat roof"},
    "big_block": {"eave_m": 16.0, "min_m2": 1200.0, "why": "over 1,200 m2: 4-5 storeys"},
    "roof": {"why": "a house is gabled along its long side or flat behind a cornice, about half each for "
             "masonry and always gabled for frame; a rise of 0.35-0.5 of the span"},
}
# Two buildings named on the sheets get their printed figures instead of the rule: the
# point is a sheet pixel inside the building, the figures are what the sheet prints there.
READINGS = [
    {"sheet": "35", "px": [280, 788], "what": "1st Presbyterian Church, Indiana Avenue at 21st Street",
     "printed": "'48' to eaves'; a hip roof drawn in dashes", "eave_m": 14.6, "roof": "gable"},
    {"sheet": "35", "px": [180, 866], "what": "1st Presbyterian Church tower",
     "printed": "'3' storeys; 'slated spire 90''", "eave_m": 18.0, "rise_m": 9.4, "roof": "pyramid"},
    {"sheet": "20", "px": [1500, 1700], "what": "Thompson-Reid & Collins Bros. Ice Cream Co., Indiana at 16th",
     "printed": "'4' at the corner, 'carpr. 4th', '1st, 3d & 4th floors'", "eave_m": 17.0, "roof": "flat"},
]

# The projection.
ROW_HALF_M = 33 * 0.3048          # a 66 ft street, the width every street on the sheets prints
ALLEY_M = 20 * 0.3048             # the sheets' 20 ft alleys
RING_M = 450.0                    # how far past the e1871 box the projection runs (W, N and S)
STREET_PITCH_M = 130.0            # projected cross streets past 16th and 22nd: the 20th-21st-22nd pitch
ROW_CLEAR_OF_WATER_M = 40.0       # the Illinois Central's tracks on the made ground by the lake
VACANT_MIN = 0.06

PALETTE = {
    "_why": ("Colour families, not colours: the sheets give the material, and each building takes "
             "one tone of its family by a seeded draw. Chicago's own brick ran red to the cream "
             "'Milwaukee' brick; its stone fronts were Joliet-Lemont limestone and brownstone."),
    "brick": ["#9c5b47", "#874c3c", "#a8674b", "#c4ad86", "#7d4436"],
    "stone": ["#b8ae95", "#8c7462", "#a09a8a"],
    "frame": ["#e3ddcc", "#d6caa5", "#a8a79a", "#8e8b68", "#c9c3b0"],
    "roof": ["#55595d", "#45484c", "#6b5a4a", "#5d4f45"],
    "tree": ["#5e7a45", "#6a8550", "#55703f", "#71874f"],
}


def r1(x: float) -> float:
    return round(float(x), 1)


def r2(x: float) -> float:
    return round(float(x), 2)


# ---------------------------------------------------------------------------------------------
# geometry


def min_rect(pts: np.ndarray) -> tuple:
    """The smallest rectangle holding a set of plan points: centre, width (across), depth
    (along the long side) and the long side's bearing in degrees, clockwise from north."""
    if len(pts) < 3:
        return None
    hull = _hull(pts)
    best = None
    for i in range(len(hull)):
        a, b = hull[i], hull[(i + 1) % len(hull)]
        d = b - a
        L = math.hypot(*d)
        if L < 1e-9:
            continue
        u = d / L
        v = np.array([-u[1], u[0]])
        pu, pv = hull @ u, hull @ v
        area = (pu.max() - pu.min()) * (pv.max() - pv.min())
        if best is None or area < best[0]:
            c = u * (pu.max() + pu.min()) / 2 + v * (pv.max() + pv.min()) / 2
            best = (area, c, pu.max() - pu.min(), pv.max() - pv.min(), u)
    _, c, lu, lv, u = best
    if lv > lu:                       # the long side carries the bearing
        u = np.array([-u[1], u[0]])
        lu, lv = lv, lu
    bearing = math.degrees(math.atan2(u[0], u[1])) % 180.0
    return float(c[0]), float(c[1]), float(lv), float(lu), bearing


def _hull(pts: np.ndarray) -> np.ndarray:
    p = sorted(map(tuple, np.unique(pts, axis=0)))
    if len(p) < 3:
        return np.array(p)

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo, hi = [], []
    for q in p:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], q) <= 0:
            lo.pop()
        lo.append(q)
    for q in reversed(p):
        while len(hi) >= 2 and cross(hi[-2], hi[-1], q) <= 0:
            hi.pop()
        hi.append(q)
    return np.array(lo[:-1] + hi[:-1], dtype=np.float64)


def inside(e: float, n: float, poly: list) -> bool:
    ok = False
    for (x1, y1), (x2, y2) in zip(poly, poly[1:] + poly[:1]):
        if (y1 > n) != (y2 > n) and e < x1 + (n - y1) * (x2 - x1) / (y2 - y1):
            ok = not ok
    return ok


def rect_corners(e, n, w, d, bearing):
    t = math.radians(bearing)
    u = (math.sin(t), math.cos(t))
    v = (u[1], -u[0])
    return [(e + su * u[0] * d / 2 + sv * v[0] * w / 2, n + su * u[1] * d / 2 + sv * v[1] * w / 2)
            for su, sv in ((1, 1), (1, -1), (-1, -1), (-1, 1))]


# ---------------------------------------------------------------------------------------------
# the heightfield: land, water, and how far from the water


class Ground:
    def __init__(self):
        meta = json.loads((HF / "heightfield.json").read_text(encoding="utf-8"))
        raw = np.fromfile(HF / "heightfield.bin", dtype="<i2").astype(np.float64)
        self.h = raw.reshape(meta["rows"], meta["cols"]) * meta["scale"] + meta["offset"]
        self.cell, self.e0, self.n0 = meta["cell_m"], meta["origin_e"], meta["origin_n"]
        self.rows, self.cols = self.h.shape
        water = self.h < 0.0
        self.to_water = ndimage.distance_transform_edt(~water) * self.cell

    def _rc(self, e, n):
        """Row and column, clamped to the box: past it the skirt carries the edge outward
        (data/terrain/epochs/e1871_postfire/heightfield.json § skirt), so the edge answers."""
        c = min(max(int(round((e - self.e0) / self.cell)), 0), self.cols - 1)
        r = min(max(int(round((n - self.n0) / self.cell)), 0), self.rows - 1)
        return r, c

    def water_m(self, e, n):
        r, c = self._rc(e, n)
        return float(self.to_water[r, c])


# ---------------------------------------------------------------------------------------------
# reading the sheets


def heights(mat: str, part_m2: float, main_m2: float, building_m2: float, is_main: bool,
            detached_rear: bool, rnd) -> tuple:
    """(rule, eave, roof, rise) for one drawn part, by RULES."""
    if building_m2 >= RULES["big_block"]["min_m2"]:
        return "big_block", RULES["big_block"]["eave_m"], "flat", 0.0
    if building_m2 >= RULES["block"]["min_m2"]:
        return "block", RULES["block"]["eave_m"], "flat", 0.0
    if not is_main and part_m2 <= RULES["porch"]["max_m2"] and part_m2 <= 0.25 * main_m2:
        return "porch", RULES["porch"]["eave_m"], "flat", 0.0
    if detached_rear and building_m2 <= RULES["outbuilding"]["max_m2"]:
        small = building_m2 < 30.0
        return "outbuilding", (3.4 if small else RULES["outbuilding"]["eave_m"]), "gable", (1.6 if small else 2.6)
    if mat == "frame":
        return "frame_dwelling", RULES["frame_dwelling"]["eave_m"], "gable", rnd.uniform(2.6, 3.6)
    if not is_main:
        return "wing", RULES["wing"]["eave_m"], ("gable" if rnd.random() < 0.4 else "flat"), 2.4
    roof = "gable" if rnd.random() < 0.5 else "flat"
    return "dwelling_masonry", RULES["dwelling_masonry"]["eave_m"], roof, (rnd.uniform(3.2, 4.4) if roof == "gable" else 0.0)


def read_sheet(sheet: str, grid: dict, rnd) -> tuple:
    gcp_id = SOURCES[sheet].replace("chicago_v3", "v3")
    gcp = json.loads((tf.GCP_DIR / f"{gcp_id}_gcps.json").read_text(encoding="utf-8"))
    raster = REPO / gcp["raster"]["path"]
    if tf.sha256(raster) != gcp["raster"]["sha256"]:
        raise SystemExit(f"{raster}: sha256 differs from {gcp_id}_gcps.json")
    fit = tf.Fit(gcp)
    tf.set_px_rules(fit.m_per_px)
    spec = SHEETS[sheet]
    blocks = {b["id"]: b for b in grid["blocks"]}
    rois = [blocks[b]["outline_local_m"] for b in spec["blocks"]] + spec["extra"]
    prairie = [p["polygon_local_m"] for p in grid["parcels"]
               if p["street"] == "prairie" and p["block"] in spec["blocks"]]
    px = lambda poly: [list(fit.pixel(*q)) for q in poly]  # noqa: E731
    allpx = [q for poly in rois for q in px(poly)]
    x0, y0 = int(min(q[0] for q in allpx)) - 10, int(min(q[1] for q in allpx)) - 10
    x1, y1 = int(max(q[0] for q in allpx)) + 10, int(max(q[1] for q in allpx)) + 10
    with Image.open(raster) as im:
        rgb = np.asarray(im.convert("RGB").crop((x0, y0, x1, y1)))
    cls = tf.classify(rgb)
    shape = cls.shape
    roi = np.zeros(shape, bool)
    for poly in rois:
        roi |= tf.polygon_mask(shape, [[x - x0, y - y0] for x, y in px(poly)], 0)
    keep_out = np.zeros(shape, bool)
    for poly in prairie:
        keep_out |= tf.polygon_mask(shape, [[x - x0, y - y0] for x, y in px(poly)], 0)
    keep_out = ndimage.binary_dilation(keep_out, iterations=max(2, tf.LINE_HALF_PX + 1))
    roi &= ~keep_out
    fabric = (cls > 0) & roi
    joined = ndimage.binary_fill_holes(ndimage.binary_closing(fabric, iterations=tf.BRIDGE_PX)) & roi
    lab, nlab = ndimage.label(joined)
    sizes = ndimage.sum(joined, lab, range(1, nlab + 1))
    overrides = {}
    for i, rd in enumerate(READINGS):
        if rd["sheet"] == sheet:
            x, y = rd["px"][0] - x0, rd["px"][1] - y0
            if 0 <= y < shape[0] and 0 <= x < shape[1]:
                overrides[i] = (y, x)
    m2 = fit.m_per_px ** 2
    rows = []
    objects = ndimage.find_objects(lab)
    for k in range(1, nlab + 1):
        if sizes[k - 1] < tf.MIN_BUILDING_PX:
            continue
        ys_, xs_ = objects[k - 1]
        sy, sx = max(ys_.start - 4, 0), max(xs_.start - 4, 0)
        sl = (slice(sy, ys_.stop + 4), slice(sx, xs_.stop + 4))
        gm = lab[sl] == k
        fab, cl = fabric[sl], cls[sl]
        parts = tf.part_masks(fab, gm) or [gm]
        building_m2 = float(gm.sum()) * m2
        recs = []
        for pm in parts:
            ys, xs = np.nonzero(pm)
            mats = np.bincount(cl[pm & fab], minlength=4)[1:]
            mat = MATS[int(np.argmax(mats))] if mats.sum() else "brick"
            pts = np.stack([xs + sx + x0 + 0.5, ys + sy + y0 + 0.5], 1) @ fit.A.T + fit.t
            rect = min_rect(pts)
            if rect is None:
                continue
            recs.append({"mask": pm, "mat": mat, "m2": float(pm.sum()) * m2, "rect": rect})
        if not recs:
            continue
        recs.sort(key=lambda r: -r["m2"])
        main = recs[0]
        # A separate small building toward the alley: the stable or shed behind a house. The
        # sheets put the alley at the back of every face, so "toward the alley" is "away from
        # its own avenue": nearer the block's middle line than the block's edge.
        detached_rear = building_m2 <= RULES["outbuilding"]["max_m2"]
        for j, r in enumerate(recs):
            rule, eave, roof, rise = heights(r["mat"], r["m2"], main["m2"], building_m2, j == 0, detached_rear, rnd)
            reading = None
            for i, (yy, xx) in overrides.items():
                yy, xx = yy - sy, xx - sx
                if 0 <= yy < r["mask"].shape[0] and 0 <= xx < r["mask"].shape[1] and r["mask"][yy, xx]:
                    reading = READINGS[i]
            if reading:
                rule, eave, roof = "printed", reading["eave_m"], reading["roof"]
                rise = reading.get("rise_m", 0.45 * r["rect"][2] if roof == "gable" else 0.0)
            e, n, w, d, bearing = r["rect"]
            if roof == "gable" and rule != "printed":
                rise = min(rise, 0.5 * w + 0.5)
            rows.append({"e": e, "n": n, "w": w, "d": d, "bearing": bearing, "eave": eave, "rise": rise,
                         "roof": roof, "mat": r["mat"], "rule": rule, "src": sheet,
                         "reading": reading["what"] if reading else None})
    return rows, fit


# ---------------------------------------------------------------------------------------------
# the projection


class Frame:
    """Plan axes on Prairie Avenue's own bearing (178.99, data/scenes/1904.json), from the
    sheet-28 control point at Prairie and 18th."""

    def __init__(self, grid: dict):
        self.o = np.array([1401.86, -3206.60])
        t = math.radians(178.99 + 180.0)
        self.v = np.array([math.sin(t), math.cos(t)])        # up the avenue, northward
        self.u = np.array([self.v[1], -self.v[0]])            # across it, eastward

    def uv(self, e, n):
        p = np.array([e, n]) - self.o
        return float(p @ self.u), float(p @ self.v)

    def en(self, u, v):
        p = self.o + self.u * u + self.v * v
        return float(p[0]), float(p[1])


def street_lines(grid: dict, fr: Frame) -> tuple:
    """The avenues (u) and cross streets (v) the projection is laid on: the grid's own
    carriageway centres where the grid draws them, Michigan Avenue from the terrain spec,
    and past them the measured pitch repeated."""
    def centre(cid, axis):
        p = next(c for c in grid["carriageways"] if c["id"] == cid)["polygon_local_m"]
        vals = [fr.uv(*q)[axis] for q in p]
        return (min(vals) + max(vals)) / 2
    spec = json.loads(SPEC.read_text(encoding="utf-8"))
    mich = spec["box_derivation"]["e_min"]          # "...Michigan Avenue's crossing of 16th Street (E +1136.7)..."
    mich_e = float(mich.split("(E +")[1].split(")")[0])
    v16 = centre("e16th_indiana_prairie", 1)
    av = {"michigan": fr.uv(mich_e, -2949.6)[0], "indiana": centre("indiana_16_18", 0),
          "prairie": centre("prairie_16_18", 0), "calumet": centre("calumet_20_22", 0)}
    pitch_w = av["indiana"] - av["michigan"]
    xs = {"16th": v16, "18th": centre("e18th_indiana_prairie", 1), "20th": centre("e20th_indiana_calumet", 1),
          "21st": centre("e21st_indiana_calumet", 1), "22nd": centre("e22nd_indiana_calumet", 1)}
    return av, pitch_w, xs


def projected(grid: dict, ground: Ground, fr: Frame, sheet_rows: list, rnd) -> tuple:
    av, pitch_w, xs = street_lines(grid, fr)
    box = (1100.0 - RING_M, 1800.0, -3800.0 - RING_M, -2900.0 + RING_M)
    corners = [fr.uv(e, n) for e in box[:2] for n in box[2:]]
    umin, umax = min(c[0] for c in corners), max(c[0] for c in corners)
    vmin, vmax = min(c[1] for c in corners), max(c[1] for c in corners)
    avenues = sorted(av.values())
    while avenues[0] - pitch_w > umin - pitch_w:
        avenues.insert(0, avenues[0] - pitch_w)
    streets = sorted(xs.values())
    while streets[0] - STREET_PITCH_M > vmin - STREET_PITCH_M:
        streets.insert(0, streets[0] - STREET_PITCH_M)
    while streets[-1] + STREET_PITCH_M < vmax + STREET_PITCH_M:
        streets.append(streets[-1] + STREET_PITCH_M)
    # What the sheets and the grid already answer for: no projection there.
    covered = [p["polygon_local_m"] for p in grid["parcels"]]
    covered += [b["outline_local_m"] for b in grid["blocks"] if b["id"] != "blk_indiana_prairie_18_20"]
    covered += [a["polygon_local_m"] for a in grid["alleys"]]
    covered += [ex for s in SHEETS.values() for ex in s["extra"]]
    # East of Prairie's east lots north of 18th, and of Calumet's east lots south of it, the
    # sheets draw the Illinois Central's tracks: no lots.
    # The line is the grid's own: blk_prairie_ic_16_18's rail-side edge, which is the right-of-way's
    # west line on sheets 20 and 28, held where the box stops it in the north and run to its end at
    # Calumet's curve in the south; south of that, the depth of Calumet's east lots on sheet 28.
    rail = next(b for b in grid["blocks"] if b["id"] == "blk_prairie_ic_16_18")["outline_local_m"]
    (ua_, va_), (ub_, vb_) = fr.uv(*rail[-1]), fr.uv(*rail[-3])

    def east_limit(v):
        if v < vb_:
            return av["calumet"] + ROW_HALF_M + 46.0
        t = (min(v, va_) - va_) / (vb_ - va_)
        return ua_ + (ub_ - ua_) * t
    frontages = [p["frontage_ft"] * 0.3048 for p in grid["parcels"]
                 if p["street"] in ("indiana", "calumet") and p.get("frontage_ft")]
    vacant = VACANT_MIN
    mats = [r["mat"] for r in sheet_rows if r["rule"] in ("dwelling_masonry", "frame_dwelling", "block", "big_block")]
    mix = {m: mats.count(m) / len(mats) for m in MATS}
    buildings, trees = [], []

    def place_ok(e, n, margin=0.0):
        if any(inside(e, n, poly) for poly in covered):
            return False
        return ground.water_m(e, n) > ROW_CLEAR_OF_WATER_M + margin

    def rect_ok(e, n, w, d, bearing):
        return place_ok(e, n) and all(place_ok(ce, cn) for ce, cn in rect_corners(e, n, w, d, bearing))

    avenue_pairs = list(zip(avenues, avenues[1:] + [avenues[-1] + pitch_w]))
    for ua, ub in avenue_pairs:
        mid = (ua + ub) / 2
        for va, vb in zip(streets, streets[1:]):            # va south, vb north
            lo, hi = va + ROW_HALF_M, vb - ROW_HALF_M
            if hi - lo < 15:
                continue
            for side, u_front, u_back, sgn in (("w", ua + ROW_HALF_M, mid - ALLEY_M / 2, 1),
                                               ("e", ub - ROW_HALF_M, mid + ALLEY_M / 2, -1)):
                depth = abs(u_back - u_front)
                v = hi
                corner = True
                while v - lo > 6.0:
                    f = frontages[rnd.randrange(len(frontages))]
                    f = min(f, v - lo)
                    vc = v - f / 2
                    uf = u_front
                    v -= f
                    lot_ok = max(u_front, u_back) <= east_limit(vc) and umin <= u_front <= umax and vmin <= vc <= vmax
                    e0, n0 = fr.en(uf + sgn * depth / 2, vc)
                    if not lot_ok or not place_ok(e0, n0):
                        corner = False
                        continue
                    # the parkway tree in front of the lot
                    if rnd.random() < 0.65:
                        te, tn = fr.en(uf - sgn * 2.6, vc + rnd.uniform(-f / 3, f / 3))
                        if place_ok(te, tn, -15.0):
                            trees.append(tree(te, tn, rnd, "project"))
                    if rnd.random() < vacant:
                        corner = False
                        continue
                    big = corner and rnd.random() < 0.18 and f < 25
                    mat = pick(mix, rnd)
                    if big:
                        w, d = min(f * 1.6, 30.0) - 1.0, min(depth - 10, 26.0)
                        rule, eave, roof, rise = "block", RULES["block"]["eave_m"], "flat", 0.0
                        vc2 = vc - f * 0.3
                    else:
                        w = max(5.2, f - rnd.uniform(1.5, 3.5))
                        d = min(rnd.uniform(12.0, 20.0), depth - 14.0)
                        rule, eave, roof, rise = heights(mat, w * d, w * d, w * d, True, False, rnd)
                        eave *= rnd.uniform(0.85, 1.15)       # one house is not its neighbour's height
                        vc2 = vc
                    setback = rnd.uniform(4.5, 7.5)
                    be, bn = fr.en(uf + sgn * (setback + d / 2), vc2)
                    bearing = math.degrees(math.atan2(fr.u[0], fr.u[1])) % 180.0   # the lot's depth, across the avenue
                    if not rect_ok(be, bn, w, d, bearing):
                        corner = False
                        continue
                    buildings.append({"e": be, "n": bn, "w": w, "d": d, "bearing": bearing,
                                      "eave": eave, "rise": min(rise, 0.5 * d + 0.5) if roof == "gable" else 0.0,
                                      "roof": roof, "mat": mat, "rule": rule, "src": "project", "reading": None})
                    corner = False
                    # back yard: a stable at the alley on a wide lot, and a tree or two
                    if f >= 11.0 and rnd.random() < 0.45:
                        sw, sd = rnd.uniform(6.0, 8.0), rnd.uniform(7.0, 9.5)
                        se, sn = fr.en(u_back - sgn * (sd / 2 + 0.6), vc + rnd.uniform(-1.5, 1.5))
                        smat = "frame" if rnd.random() < 0.45 else "brick"
                        if rect_ok(se, sn, sw, sd, bearing):
                            buildings.append({"e": se, "n": sn, "w": sw, "d": sd, "bearing": bearing,
                                              "eave": RULES["outbuilding"]["eave_m"], "rise": 2.4, "roof": "gable",
                                              "mat": smat, "rule": "outbuilding", "src": "project", "reading": None})
                    for _ in range(2):
                        if rnd.random() < 0.5:
                            yu = uf + sgn * rnd.uniform(setback + d + 3.0, depth - 10.0)
                            if (yu - uf) * sgn > setback + d + 2.0:
                                te, tn = fr.en(yu, vc + rnd.uniform(-f / 3, f / 3))
                                if place_ok(te, tn, -15.0):
                                    trees.append(tree(te, tn, rnd, "project"))
    return buildings, trees, {"avenues_u_m": [r1(a) for a in avenues], "streets_v_m": [r1(s) for s in streets],
                              "avenue_pitch_m": r1(pitch_w), "measured": {k: r1(x) for k, x in {**av, **xs}.items()},
                              "material_mix": {k: r2(v) for k, v in mix.items()},
                              "frontages_from": f"{len(frontages)} Indiana and Calumet lots of data/street_grid/1904.json"}


def pick(mix: dict, rnd) -> str:
    x = rnd.random()
    for m in MATS:
        x -= mix[m]
        if x <= 0:
            return m
    return MATS[0]


def tree(e, n, rnd, src) -> dict:
    h = rnd.uniform(10.0, 17.0)
    return {"e": e, "n": n, "h": h, "r": rnd.uniform(0.24, 0.32) * h, "src": src}


def sheet_trees(grid: dict, rows: list, rnd) -> list:
    """Trees on the sheets' own ground: along the Indiana and Calumet parkways (never Prairie
    Avenue's, which T-2473 plants), and one or two in each of their lots' back yards."""
    out = []
    for f in grid["faces"]:
        if f["street"] not in ("indiana", "calumet"):
            continue
        for a, b, c, d in f["bands"].get("parkway", []):
            p0 = (np.array(a) + np.array(d)) / 2
            p1 = (np.array(b) + np.array(c)) / 2
            L = float(np.linalg.norm(p1 - p0))
            s = rnd.uniform(3.0, 8.0)
            while s < L - 3.0:
                if rnd.random() < 0.7:
                    q = p0 + (p1 - p0) * (s / L)
                    out.append(tree(float(q[0]), float(q[1]), rnd, "sheet"))
                s += rnd.uniform(9.0, 13.0)
    rects = [rect_corners(r["e"], r["n"], r["w"] + 3, r["d"] + 3, r["bearing"]) for r in rows]
    for p in grid["parcels"]:
        if p["street"] == "prairie":
            continue
        poly = p["polygon_local_m"]
        xs = [q[0] for q in poly]
        ys = [q[1] for q in poly]
        for _ in range(3):
            if rnd.random() < 0.5:
                e, n = rnd.uniform(min(xs), max(xs)), rnd.uniform(min(ys), max(ys))
                if inside(e, n, poly) and not any(inside(e, n, rc) for rc in rects):
                    out.append(tree(e, n, rnd, "sheet"))
    return out


# ---------------------------------------------------------------------------------------------
# the document


def build() -> dict:
    import random
    rnd = random.Random(SEED)
    grid = json.loads(GRID.read_text(encoding="utf-8"))
    ground = Ground()
    sheet_rows = []
    for s in SHEETS:
        rows, _ = read_sheet(s, grid, rnd)
        sheet_rows += rows
    fr = Frame(grid)
    proj_rows, proj_trees, projection = projected(grid, ground, fr, sheet_rows, rnd)
    trees = sheet_trees(grid, sheet_rows, rnd) + proj_trees
    srcs = ["20", "28", "35", "project"]
    roofs = ["flat", "gable", "pyramid"]
    rules = sorted({r["rule"] for r in sheet_rows + proj_rows})
    brows = []
    for r in sheet_rows + proj_rows:
        tones = len(PALETTE[r["mat"]])
        brows.append([r1(r["e"]), r1(r["n"]), r1(r["bearing"]), r1(r["w"]), r1(r["d"]), r1(r["eave"]),
                      r1(r["rise"]), roofs.index(r["roof"]), MATS.index(r["mat"]), rnd.randrange(tones),
                      rnd.randrange(len(PALETTE["roof"])), srcs.index(r["src"]), rules.index(r["rule"])])
    trows = [[r1(t["e"]), r1(t["n"]), r1(t["h"]), r1(t["r"]), rnd.randrange(len(PALETTE["tree"])),
              0 if t["src"] == "sheet" else 1] for t in trees]
    readings = [{k: v for k, v in rd.items()} for rd in READINGS]
    by_src = {s: sum(1 for b in brows if srcs[b[11]] == s) for s in srcs}
    return {
        "_doc": ("The 1904 context city: faded stand-ins for every part of the map not yet built (T-2477). "
                 "GENERATED by tools/build_context_1904.py -- do not hand-edit; re-run the tool. Local ENU "
                 "metres of data/datum.json. Drawn by renderers/web/js/context.js, which fades them and drops any "
                 "a placed structure touches."),
        "ticket": TICKET,
        "scene": "1904",
        "target_date": "1904-07-01",
        "liberty": LIBERTY,
        "generated_by": "tools/build_context_1904.py",
        "seed": SEED,
        "sources": list(SOURCES.values()),
        "tiers": {
            "sheet_outline": ("inferred -- the smallest rectangle holding each part a Sanborn 1911 sheet draws, "
                              "carried to 1904 on Glessner House's reading that these sheets changed only at "
                              "1609-1611 and 1620 Prairie (Prairie lots are not read here)"),
            "sheet_material": "inferred -- the sheet's own colour: pink brick, blue stone, yellow frame",
            "projection": ("reconstructed -- no sheet in hand: streets on the measured pitch, lots on the measured "
                           "frontages, materials in the measured mix"),
            "height_roof_colour_trees": "reconstructed -- by `rules`; the sheets' storey figures are not read",
        },
        "rules": RULES,
        "readings": readings,
        "palette": PALETTE,
        "projection": projection,
        "fields": {
            "buildings": ["e", "n", "bearing_deg", "width_m", "depth_m", "eave_m", "rise_m", "roof", "material",
                          "tone", "roof_tone", "src", "rule"],
            "trees": ["e", "n", "height_m", "crown_r_m", "tone", "src"],
        },
        "enums": {"roof": roofs, "material": list(MATS), "src": srcs, "rule": rules,
                  "tree_src": ["sheet", "project"]},
        "counts": {"buildings": len(brows), "by_src": by_src, "trees": len(trows)},
        "buildings": brows,
        "trees": trows,
    }


def dumps(doc: dict) -> str:
    head = {k: v for k, v in doc.items() if k not in ("buildings", "trees")}
    s = json.dumps(head, indent=1, ensure_ascii=False)[:-2]
    rows = lambda key: ",\n".join(json.dumps(r, separators=(",", ":")) for r in doc[key])  # noqa: E731
    return s + f',\n "buildings": [\n{rows("buildings")}\n ],\n "trees": [\n{rows("trees")}\n ]\n}}\n'


def contract(doc: dict) -> list:
    """What must hold of any build: rows well formed, nothing on Prairie Avenue's lots or
    streets, nothing in the water, every sheet named a source."""
    bad = []
    grid = json.loads(GRID.read_text(encoding="utf-8"))
    prairie = [p["polygon_local_m"] for p in grid["parcels"] if p["street"] == "prairie"]
    prairie += [c["polygon_local_m"] for c in grid["carriageways"] if c["id"].startswith("prairie_")]
    ground = Ground()
    for i, b in enumerate(doc["buildings"]):
        e, n, _, w, d, eave, rise = b[:7]
        if not (w > 0 and d > 0 and eave > 0 and rise >= 0):
            bad.append(f"building {i}: non-positive size {b}")
        if any(inside(e, n, p) for p in prairie):
            bad.append(f"building {i} at ({e}, {n}) stands on a Prairie Avenue lot or roadway")
        if ground.water_m(e, n) <= 0:
            bad.append(f"building {i} at ({e}, {n}) stands in the water")
    for i, t in enumerate(doc["trees"]):
        if any(inside(t[0], t[1], p) for p in prairie):
            bad.append(f"tree {i} at ({t[0]}, {t[1]}) stands on Prairie Avenue")
    src_dir = ROOT / "data" / "sources"
    for s in doc["sources"]:
        if not (src_dir / f"{s}.json").exists():
            bad.append(f"source {s} does not resolve in data/sources")
    if not doc["counts"]["by_src"].get("project") or not sum(v for k, v in doc["counts"]["by_src"].items() if k != "project"):
        bad.append("one kind of stand-in is missing entirely")
    return bad


def self_test() -> int:
    doc = json.loads(OUT.read_text(encoding="utf-8"))
    grid = json.loads(GRID.read_text(encoding="utf-8"))
    p = next(q for q in grid["parcels"] if q["street"] == "prairie")["polygon_local_m"]
    e = sum(q[0] for q in p) / len(p)
    n = sum(q[1] for q in p) / len(p)
    broken = dict(doc, buildings=doc["buildings"] + [[e, n, 0, 8, 12, 10, 3, 1, 0, 0, 0, 3, 0]])
    fails = contract(broken)
    ok = any("Prairie Avenue lot" in f for f in fails)
    wet = dict(doc, buildings=doc["buildings"] + [[1790.0, -3700.0, 0, 8, 12, 10, 3, 1, 0, 0, 0, 3, 0]])
    ok2 = any("water" in f for f in contract(wet))
    print(f"a stand-in on a Prairie Avenue lot: {'FAIL (caught)' if ok else 'NOT CAUGHT'}")
    print(f"a stand-in in the lake: {'FAIL (caught)' if ok2 else 'NOT CAUGHT'}")
    return 0 if ok and ok2 else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    doc = build()
    bad = contract(doc)
    for b in bad[:20]:
        print("FAIL", b)
    text = dumps(doc)
    if a.check:
        cur = OUT.read_text(encoding="utf-8") if OUT.exists() else ""
        if cur != text:
            print(f"FAIL {OUT.relative_to(ROOT)} does not re-derive; run tools/build_context_1904.py")
            return 1
        print(f"ok   {OUT.relative_to(ROOT)} re-derives: {doc['counts']}")
        return 1 if bad else 0
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text, encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}: {doc['counts']} ({len(text) // 1024} KiB)")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
