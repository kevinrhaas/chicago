#!/usr/bin/env python3
"""The 1904 context city (T-2477, T-2491): faded stand-ins and streets on the map not yet built.

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

T-2491 widened it. The owner, 2026-10-13: "we should have some streets where they should be
based on maps, you can continue it to the end of the visible map". The city now runs past the
box on every land side to the reach at which the 1904 haze is total (reach_m, from world.js),
on a street network laid between measured lines (network(): the school section's corners give
State, Halsted, Madison and Twelfth; the traced grid gives Michigan to Calumet and 16th to
22nd; the rest is filled at the section's own sixteenths and eighths). Robinson's 1886 plate 10
is a fourth sheet (r10), traced north of 16th Street. Land use past the sheets is by zone
(ZONES: shops on State and Wabash, lofts and offices toward the Loop, railway lands Clark to
Canal, cottages west of Canal). Past the near ring a run of lots is one box (lod 1) and a tree
is a bare crown. The streets themselves are faded ribbons (`streets`), kept off every traced
carriageway, alley, lot and the water. LIBERTY_STREETS in docs/LIBERTIES.md covers all of it.

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
EXTENDED_BY = "T-2491"
LIBERTY_STREETS = "L-context-streets-2491"
SEED = 19040701

SOURCES = {"20": "sanborn_1911_chicago_v3_sheet_20", "28": "sanborn_1911_chicago_v3_sheet_28",
           "35": "sanborn_1911_chicago_v3_sheet_35", "r10": "robinson_1886_chicago_plate_10"}
GCP_IDS = {"20": "sanborn_1911_v3_sheet_20", "28": "sanborn_1911_v3_sheet_28", "35": "sanborn_1911_v3_sheet_35",
           "r10": "robinson_1886_plate_10"}
SHEET_NAMES = {"20": "Sanborn 1911 vol. 3 sheet 20", "28": "Sanborn 1911 vol. 3 sheet 28",
               "35": "Sanborn 1911 vol. 3 sheet 35", "r10": "Robinson's 1886 atlas, plate 10"}
# The street network's anchors (T-2491): the school section's corners and G1, each a crossing
# read from OpenStreetMap; the 1904 grid's own streets come from data/street_grid/1904.json.
NETWORK_SOURCES = ["osm_streets_2026"]

# The sheets' own ground, as the grid's blocks (Prairie Avenue's lots are taken out of each)
# plus one piece the grid has no block for: Calumet's east face at 20th Street on sheet 28,
# its rectangle read at sheet pixels (4680, 4890)-(5420, 6080) through the sheet's fit.
SHEETS = {
    "20": {"blocks": ["blk_indiana_prairie_16_18"], "extra": []},
    "28": {"blocks": ["blk_prairie_calumet_18_20"],
           "extra": [[[1547.0, -3400.0], [1585.3, -3399.3], [1586.4, -3460.1], [1548.1, -3460.8]]]},
    "35": {"blocks": ["blk_indiana_prairie_20_21", "blk_indiana_prairie_21_22",
                      "blk_prairie_calumet_20_21", "blk_prairie_calumet_21_22"], "extra": []},
    # Robinson 1886, plate 10, north of 16th Street (T-2491): from the page's left edge (the
    # west lots of Indiana Avenue, curving into the binding) to the lake, and from the plate's
    # top rule down to 16th Street's north line. Read in pixels: 16th's centre is at y 973-983
    # and its 50 ft street half is 22 px, so the ground stops at y 950. The yards the plate
    # draws east of Indiana stay clear of projected houses because this ground is covered.
    # Its blue ruling lines read as stone wash; a part narrower than 2.5 m is one of them.
    "r10": {"blocks": [], "extra": [], "px_roi": [[8, 150], [1440, 150], [1440, 950], [8, 950]],
            "min_part_w_m": 2.5},
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
    # T-2491: past the near ring, and in the business zones, a run of three to six lots is one box.
    "house_row": {"eave_m": "10.5 masonry, 6.5 frame, x0.85-1.15", "why": "past the near ring a run of three to "
                  "six houses is drawn as one row, at the house rules' heights: at that distance the haze leaves a "
                  "third or less of its colour and a row reads as the houses would"},
    "shops_block": {"eave_m": "11-15", "why": "State Street and Wabash Avenue south of Twelfth: brick business "
                    "blocks of three and four storeys, shops under flats, to the lot line"},
    "business_block": {"eave_m": "17-24", "why": "Twelfth Street to Harrison: the wholesale and printing district's "
                       "lofts, five to seven storeys"},
    "loop_block": {"eave_m": "28-60", "why": "north of Harrison: the downtown's office and loft blocks, eight to "
                   "sixteen storeys"},
    "railway_shed": {"eave_m": "5.5-8", "why": "the railway lands: freight houses and engine sheds, long and low"},
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
RING_M = 450.0                    # past the e1871 box, houses stand one to a lot this far (W, N and S);
                                  # past it to the haze's reach (reach_m) they stand as rows of lots
ROW_CLEAR_OF_WATER_M = 40.0       # the Illinois Central's tracks on the made ground by the lake
CARRIAGEWAY_M = 38 * 0.3048       # a 66 ft street less two 14 ft sidewalk spaces (row_66 of the grid)
STREET_STEP_M = 2.0               # how finely a street line is tested for what it would cross
STREET_CLEAR_OF_WATER_M = 20.0
NEAR_BOX = (1100.0 - RING_M, 1800.0, -3800.0 - RING_M, -2900.0 + RING_M)
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
    gcp_id = GCP_IDS[sheet]
    gcp = json.loads((tf.GCP_DIR / f"{gcp_id}_gcps.json").read_text(encoding="utf-8"))
    raster = REPO / gcp["raster"]["path"]
    if tf.sha256(raster) != gcp["raster"]["sha256"]:
        raise SystemExit(f"{raster}: sha256 differs from {gcp_id}_gcps.json")
    fit = tf.Fit(gcp)
    tf.set_px_rules(fit.m_per_px)
    spec = SHEETS[sheet]
    blocks = {b["id"]: b for b in grid["blocks"]}
    rois = [blocks[b]["outline_local_m"] for b in spec["blocks"]] + spec["extra"]
    rois += [[list(fit.local(*q)) for q in spec["px_roi"]]] if spec.get("px_roi") else []
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
            # The hull of a part's pixel centres is the hull of its edge pixels' centres, and
            # there are far fewer of those to sort.
            ys, xs = np.nonzero(pm & ~ndimage.binary_erosion(pm))
            mats = np.bincount(cl[pm & fab], minlength=4)[1:]
            mat = MATS[int(np.argmax(mats))] if mats.sum() else "brick"
            pts = np.stack([xs + sx + x0 + 0.5, ys + sy + y0 + 0.5], 1) @ fit.A.T + fit.t
            rect = min_rect(pts)
            if rect is None or rect[2] < spec.get("min_part_w_m", 0.0):
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
                         "reading": reading["what"] if reading else None, "lod": 0})
    return rows, fit, rois


# ---------------------------------------------------------------------------------------------
# the projection: the street grid first, then the city on it


class Frame:
    """Plan axes on Prairie Avenue's own bearing (178.99, data/scenes/1904.json), from the
    sheet-28 control point at Prairie and 18th. u runs east across the avenues, v north up
    them. The section corners in hand (State and Halsted at Madison and at Roosevelt) stand
    within 0.4 degrees of these axes, so one frame carries the whole grid."""

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


def reach_m() -> float:
    """How far the 1904 air lets anything be seen: the distance at which renderers/web/js/
    world.js's FogExp2 leaves a surface less than one 8-bit step of its own colour,
    exp(-(d * density)^2) = 1/255. Read from the literal, so a change of air moves the city."""
    src = (ROOT / "renderers" / "web" / "js" / "world.js").read_text(encoding="utf-8")
    density = float(src.split("const HAZE_DENSITY = ")[1].split(";")[0])
    return math.sqrt(math.log(255.0)) / density


def network(grid: dict, fr: Frame, reach: float) -> dict:
    """The streets of the city the context draws, as lines of constant u (the avenues, which
    run north and south) and of constant v (the cross streets). Each line says what places it.

    MEASURED where the project holds a reading: Michigan, Indiana, Prairie and Calumet, and
    16th to 22nd, as data/street_grid/1904.json and the terrain spec place them; State and
    Halsted, Madison and Twelfth (Roosevelt) at the school section's corners, read from
    OpenStreetMap for T-0878 (data/traces/gcp/wright_1834_nara_hup_section_corners.json, and
    G1 of wright_1834_nara_hup_gcps.json for State and Madison). Chicago's section lines run
    down the middle of the streets laid on them.
    FILLED between and past those at the pitch they give (RECONSTRUCTED, LIBERTY_STREETS): the
    section's mile cut in sixteen across (the city's lots face the avenues, two 125 ft lots and
    an alley to a block) and in eight along (its cross streets an eighth of a mile apart); three
    numbered streets between Twelfth and 16th (the four intervals measure 203 m each); Twenty-
    second to Thirty-first a mile, as the section lines run, in nine; Wabash midway between
    State and Michigan; and Calumet's pitch repeated east until the water."""
    corners = json.loads((ROOT / "data/traces/gcp/wright_1834_nara_hup_section_corners.json").read_text(encoding="utf-8"))
    gcps = json.loads((ROOT / "data/traces/gcp/wright_1834_nara_hup_gcps.json").read_text(encoding="utf-8"))
    datum = json.loads((ROOT / "data/datum.json").read_text(encoding="utf-8"))

    def local(m):
        return m["utm_e"] - datum["origin_utm_e"], m["utm_n"] - datum["origin_utm_n"]
    at = {c["id"]: fr.uv(*local(c["modern"])) for c in corners["corners"]}
    g1 = next(g for g in gcps["gcps"] if g["id"] == "G1")
    at["G1"] = fr.uv(*local(g1["modern"]))
    u_state = (at["G1"][0] + at["S-SE"][0]) / 2
    u_halsted = (at["S-NW"][0] + at["S-SW"][0]) / 2
    v_madison = (at["G1"][1] + at["S-NW"][1]) / 2
    v_twelfth = (at["S-SE"][1] + at["S-SW"][1]) / 2
    mile = ((u_state - u_halsted) + (v_madison - v_twelfth)) / 2       # the section, as measured
    eighth = mile / 8

    def centre(cid, axis):
        p = next(c for c in grid["carriageways"] if c["id"] == cid)["polygon_local_m"]
        vals = [fr.uv(*q)[axis] for q in p]
        return (min(vals) + max(vals)) / 2
    spec = json.loads(SPEC.read_text(encoding="utf-8"))
    mich_e = float(spec["box_derivation"]["e_min"].split("(E +")[1].split(")")[0])
    v16 = centre("e16th_indiana_prairie", 1)
    m = {"michigan": fr.uv(mich_e, -2949.6)[0], "indiana": centre("indiana_16_18", 0),
         "prairie": centre("prairie_16_18", 0), "calumet": centre("calumet_20_22", 0)}
    pitch_east = m["calumet"] - m["prairie"]
    v = {"16th": v16, "18th": centre("e18th_indiana_prairie", 1), "20th": centre("e20th_indiana_calumet", 1),
         "21st": centre("e21st_indiana_calumet", 1), "22nd": centre("e22nd_indiana_calumet", 1)}
    box = (1100.0 - reach, 1800.0 + reach, -3800.0 - reach, -2900.0 + reach)
    cs = [fr.uv(e, n) for e in box[:2] for n in box[2:]]
    umin, umax = min(c[0] for c in cs), max(c[0] for c in cs)
    vmin, vmax = min(c[1] for c in cs), max(c[1] for c in cs)

    avenues = [(u_state, "State Street", "measured"), (u_halsted, "Halsted Street", "measured"),
               ((u_state + m["michigan"]) / 2, "Wabash Avenue", "filled")]
    avenues += [(m[k], f"{k.title()} Avenue", "measured") for k in ("michigan", "indiana", "prairie", "calumet")]
    for k in range(1, 16):
        avenues.append((u_state - k * eighth / 2, None, "filled"))
    u = u_halsted - eighth / 2
    while u > umin:
        avenues.append((u, None, "filled"))
        u -= eighth / 2
    u = m["calumet"] + pitch_east
    while u < umax:
        avenues.append((u, None, "filled"))
        u += pitch_east
    streets = [(v_madison, "Madison Street", "measured"), (v_twelfth, "Twelfth Street", "measured")]
    streets += [(v[k], f"{k} Street", "measured") for k in v]
    for k in range(1, 8):
        streets.append((v_madison - k * eighth, None, "filled"))
    for k, name in ((1, "13th"), (2, "14th"), (3, "15th")):
        streets.append((v_twelfth + (v16 - v_twelfth) * k / 4, f"{name} Street", "filled"))
    v31 = v["22nd"] - mile
    for k in range(1, 10):
        streets.append((v["22nd"] - mile * k / 9, f"{22 + k}{'rd' if 22 + k == 23 else 'th'} Street", "filled"))
    k, vv = 32, v31 - eighth
    while vv > vmin:
        streets.append((vv, f"{k}{'nd' if k == 32 else 'rd' if k == 33 else 'th'} Street", "filled"))
        k, vv = k + 1, vv - eighth
    vv = v_madison + eighth
    while vv < vmax:
        streets.append((vv, None, "filled"))
        vv += eighth
    return {"avenues": sorted(avenues), "streets": sorted(streets), "box_uv": (umin, umax, vmin, vmax),
            "u": {"state": u_state, "halsted": u_halsted, "clark": u_state - eighth, "wabash": (u_state + m["michigan"]) / 2,
                  "canal": u_state - 5 * eighth, **m},
            "v": {"madison": v_madison, "twelfth": v_twelfth, "harrison": v_twelfth + 0.375 * mile,
                  "31st": v31, **v},
            "mile_m": mile, "eighth_m": eighth, "pitch_east_m": pitch_east}


# What each zone of the projection draws. RECONSTRUCTED (LIBERTY_STREETS): the 1904 city's
# uses, from what the city is known to have been and not from a map of each block; the one map
# in hand that reaches past the sheets (Robinson 1886, plate 10) is traced, not zoned.
ZONES = {
    "residential": "houses on lots, as the traced sheets' own faces: the default",
    "workers": "west of Canal Street: the frame cottages and flats of the Near West Side and Bridgeport, seven in ten frame",
    "shops": "State Street and Wabash Avenue from Twelfth to 22nd: three- and four-storey brick business blocks",
    "business": "Twelfth Street to Harrison, east of Canal Street: the near-south wholesale and printing district, five to seven storeys",
    "loop": "north of Harrison, east of Canal Street: the downtown's office and loft blocks, eight to sixteen storeys",
    "railway": "Clark Street to Canal Street from Twelfth to 22nd: the railway lands and the river (the terminal "
               "yards of the stations at Polk Street and Twelfth, and the South Branch through them): long sheds, no houses",
}
ZONE_MIX = {"workers": {"brick": 0.3, "stone": 0.0, "frame": 0.7},
            "shops": {"brick": 0.8, "stone": 0.2, "frame": 0.0},
            "business": {"brick": 0.8, "stone": 0.2, "frame": 0.0},
            "loop": {"brick": 0.6, "stone": 0.4, "frame": 0.0}}
ZONE_EAVE = {"shops": (11.0, 15.0), "business": (17.0, 24.0), "loop": (28.0, 60.0)}


def projected(grid: dict, ground: Ground, fr: Frame, net: dict, sheet_rows: list, covered_extra: list,
              plate_top_v: float, rnd) -> tuple:
    U, V = net["u"], net["v"]
    umin, umax, vmin, vmax = net["box_uv"]
    near_box = NEAR_BOX
    avenues = [a[0] for a in net["avenues"]]
    streets = [s[0] for s in net["streets"]]
    # What the sheets and the grid already answer for: no projection there.
    covered = [p["polygon_local_m"] for p in grid["parcels"]]
    covered += [b["outline_local_m"] for b in grid["blocks"] if b["id"] != "blk_indiana_prairie_18_20"]
    covered += [a["polygon_local_m"] for a in grid["alleys"]]
    covered += [ex for s in SHEETS.values() for ex in s["extra"]] + covered_extra
    cov_bb = [(min(q[0] for q in p), max(q[0] for q in p), min(q[1] for q in p), max(q[1] for q in p)) for p in covered]
    # East of Prairie's east lots north of 18th, and of Calumet's east lots south of it, the
    # sheets draw the Illinois Central's tracks: no lots. The line is the grid's own:
    # blk_prairie_ic_16_18's rail-side edge, held where the box stops it in the north and run to
    # its end at Calumet's curve in the south; south of that, the depth of Calumet's east lots on
    # sheet 28. North of 16th Street, Robinson's plate draws the Illinois Central's yards east of
    # Indiana Avenue's lots and no Prairie Avenue: what it draws there is traced, and past its top
    # only Indiana's west face stands; north of Twelfth, only Michigan's (the lake front and its
    # park lie east).
    rail = next(b for b in grid["blocks"] if b["id"] == "blk_prairie_ic_16_18")["outline_local_m"]
    (ua_, va_), (ub_, vb_) = fr.uv(*rail[-1]), fr.uv(*rail[-3])

    def east_limit(v):
        if v > V["twelfth"] + ROW_HALF_M:
            return U["michigan"]
        if v > V["16th"] + ROW_HALF_M:
            return U["indiana"]
        if v < vb_:
            return U["calumet"] + ROW_HALF_M + 46.0
        t = (min(v, va_) - va_) / (vb_ - va_)
        return ua_ + (ub_ - ua_) * t

    def zone(u_face, u, v):
        if v > V["twelfth"] + ROW_HALF_M and u > U["canal"]:
            return "loop" if v > V["harrison"] else "business"
        if u_face is not None and V["22nd"] < v < V["twelfth"] and min(abs(u_face - U["state"]), abs(u_face - U["wabash"])) < 1.0:
            return "shops"
        if V["22nd"] - ROW_HALF_M < v < V["twelfth"] + ROW_HALF_M and U["canal"] - ROW_HALF_M <= u <= U["clark"] + ROW_HALF_M:
            return "railway"
        if u < U["canal"]:
            return "workers"
        return "residential"

    frontages = [p["frontage_ft"] * 0.3048 for p in grid["parcels"]
                 if p["street"] in ("indiana", "calumet") and p.get("frontage_ft")]
    mats = [r["mat"] for r in sheet_rows if r["src"] in ("20", "28", "35")
            and r["rule"] in ("dwelling_masonry", "frame_dwelling", "block", "big_block")]
    mix = {m: mats.count(m) / len(mats) for m in MATS}
    buildings, trees = [], []

    def is_covered(e, n):
        return any(x0 <= e <= x1 and y0 <= n <= y1 and inside(e, n, p)
                   for (x0, x1, y0, y1), p in zip(cov_bb, covered))

    def place_ok(e, n, margin=0.0):
        return ground.water_m(e, n) > ROW_CLEAR_OF_WATER_M + margin and not is_covered(e, n)

    def rect_ok(e, n, w, d, bearing):
        return place_ok(e, n) and all(place_ok(ce, cn) for ce, cn in rect_corners(e, n, w, d, bearing))

    across = math.degrees(math.atan2(fr.u[0], fr.u[1])) % 180.0      # a lot's depth, across the avenue
    along = math.degrees(math.atan2(fr.v[0], fr.v[1])) % 180.0       # a row's length, up the avenue

    def near(e, n):
        return near_box[0] <= e <= near_box[1] and near_box[2] <= n <= near_box[3]

    def add(e, n, w, d, bearing, eave, rise, roof, mat, rule, lod):
        buildings.append({"e": e, "n": n, "w": w, "d": d, "bearing": bearing, "eave": eave,
                          "rise": min(rise, 0.5 * w + 0.5) if roof == "gable" else 0.0, "roof": roof,
                          "mat": mat, "rule": rule, "src": "project", "reading": None, "lod": lod})

    for ua, ub in zip(avenues, avenues[1:]):
        if ub - ua < 40:
            continue
        mid = (ua + ub) / 2
        for va, vb in zip(streets, streets[1:]):            # va south, vb north
            lo, hi = va + ROW_HALF_M, vb - ROW_HALF_M
            if hi - lo < 15:
                continue
            bz = zone(None, mid, (va + vb) / 2)
            if bz == "railway":
                # One to three long sheds in a block of the railway lands, on its long axis.
                for _ in range(rnd.choice((0, 1, 1, 2, 3))):
                    L = min(rnd.uniform(60.0, 160.0), hi - lo - 10)
                    W = rnd.uniform(12.0, 24.0)
                    if L < 30:
                        continue
                    uc = rnd.uniform(ua + ROW_HALF_M + W / 2 + 4, ub - ROW_HALF_M - W / 2 - 4)
                    vc = rnd.uniform(lo + L / 2 + 4, hi - L / 2 - 4)
                    e, n = fr.en(uc, vc)
                    if uc <= east_limit(vc) and rect_ok(e, n, W, L, along):
                        add(e, n, W, L, along, rnd.uniform(5.5, 8.0), W * 0.18, rnd.choice(("gable", "flat")),
                            "brick" if rnd.random() < 0.6 else "frame", "railway_shed", 1)
                continue
            for side, u_front, u_back, sgn, u_face in (("w", ua + ROW_HALF_M, mid - ALLEY_M / 2, 1, ua),
                                                       ("e", ub - ROW_HALF_M, mid + ALLEY_M / 2, -1, ub)):
                depth = abs(u_back - u_front)
                if depth < 14:
                    continue
                v = hi
                corner = True
                while v - lo > 6.0:
                    z = zone(u_face, u_front + sgn * depth / 2, v)
                    e0, n0 = fr.en(u_front + sgn * depth / 2, v - 5)
                    lod = 0 if near(e0, n0) else 1
                    if z in ("shops", "business", "loop") or lod == 1:
                        # A run of lots as one building: a business block, or past the near ring
                        # a row of houses read at the distance the haze lets it be seen.
                        run = min(sum(frontages[rnd.randrange(len(frontages))] for _ in range(rnd.randint(3, 6))),
                                  v - lo)
                        vc = v - run / 2
                        v -= run
                        uc = u_front + sgn * depth / 2
                        if not (max(u_front, u_back) <= east_limit(vc) and umin <= uc <= umax and vmin <= vc <= vmax):
                            continue
                        if rnd.random() < VACANT_MIN:
                            continue
                        zmix = ZONE_MIX.get(z, mix)
                        mat = pick(zmix, rnd)
                        if z in ZONE_EAVE:
                            lo_e, hi_e = ZONE_EAVE[z]
                            # a shop block is a shop under flats, 18-28 m deep; a loft fills its lot
                            dd = min(depth - 4.0, rnd.uniform(18.0, 28.0) if z == "shops" else rnd.uniform(0.7, 0.95) * depth)
                            eave, roof, rise, rule = rnd.uniform(lo_e, hi_e), "flat", 0.0, f"{z}_block"
                            setback = 1.0
                        else:
                            dd = min(rnd.uniform(12.0, 18.0), depth - 14.0)
                            frame = mat == "frame"
                            eave = (RULES["frame_dwelling"]["eave_m"] if frame else RULES["dwelling_masonry"]["eave_m"]) \
                                * rnd.uniform(0.85, 1.15)
                            roof = "gable" if frame or rnd.random() < 0.5 else "flat"
                            rise, rule = (dd * rnd.uniform(0.35, 0.45) if roof == "gable" else 0.0), "house_row"
                            setback = rnd.uniform(4.5, 7.5)
                        ln = run - rnd.uniform(2.0, 4.0)
                        be, bn = fr.en(u_front + sgn * (setback + dd / 2), vc)
                        if ln > 5 and rect_ok(be, bn, dd, ln, along):
                            add(be, bn, dd, ln, along, eave, rise, roof, mat, rule, lod)
                        if z in ("residential", "workers"):
                            for k in range(int(run // 14)):
                                if rnd.random() < 0.5:
                                    te, tn = fr.en(u_front - sgn * 2.6, v + run * (k + 0.5) / max(1, int(run // 14)))
                                    if place_ok(te, tn, -15.0):
                                        trees.append(tree(te, tn, rnd, "project"))
                        continue
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
                    if rnd.random() < VACANT_MIN:
                        corner = False
                        continue
                    big = corner and rnd.random() < 0.18 and f < 25
                    mat = pick(ZONE_MIX.get(z, mix), rnd)
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
                    if not rect_ok(be, bn, w, d, across):
                        corner = False
                        continue
                    buildings.append({"e": be, "n": bn, "w": w, "d": d, "bearing": across,
                                      "eave": eave, "rise": min(rise, 0.5 * d + 0.5) if roof == "gable" else 0.0,
                                      "roof": roof, "mat": mat, "rule": rule, "src": "project", "reading": None, "lod": 0})
                    corner = False
                    # back yard: a stable at the alley on a wide lot, and a tree or two
                    if f >= 11.0 and rnd.random() < 0.45:
                        sw, sd = rnd.uniform(6.0, 8.0), rnd.uniform(7.0, 9.5)
                        se, sn = fr.en(u_back - sgn * (sd / 2 + 0.6), vc + rnd.uniform(-1.5, 1.5))
                        smat = "frame" if rnd.random() < 0.45 else "brick"
                        if rect_ok(se, sn, sw, sd, across):
                            buildings.append({"e": se, "n": sn, "w": sw, "d": sd, "bearing": across,
                                              "eave": RULES["outbuilding"]["eave_m"], "rise": 2.4, "roof": "gable",
                                              "mat": smat, "rule": "outbuilding", "src": "project", "reading": None,
                                              "lod": 0})
                    for _ in range(2):
                        if rnd.random() < 0.5:
                            yu = uf + sgn * rnd.uniform(setback + d + 3.0, depth - 10.0)
                            if (yu - uf) * sgn > setback + d + 2.0:
                                te, tn = fr.en(yu, vc + rnd.uniform(-f / 3, f / 3))
                                if place_ok(te, tn, -15.0):
                                    trees.append(tree(te, tn, rnd, "project"))
    return buildings, trees, {"material_mix": {k: r2(x) for k, x in mix.items()},
                              "frontages_from": f"{len(frontages)} Indiana and Calumet lots of data/street_grid/1904.json",
                              "near_ring_m": RING_M, "zones": ZONES}, east_limit, zone


def street_segments(grid: dict, ground: Ground, fr: Frame, net: dict, east_limit, zone) -> list:
    """The faded streets: each line of the network, cut where it would cross the street grid's
    own drawing (its carriageways, walks, lots and alleys stay the street grid's, and T-2475
    blends that edge), the water, the railway lands (a cross street runs through them, an
    avenue does not) and the ground east of the lot line."""
    halfw = CARRIAGEWAY_M / 2
    polys = [c["polygon_local_m"] for c in grid["carriageways"]] + [a["polygon_local_m"] for a in grid["alleys"]]
    polys += [p["polygon_local_m"] for p in grid["parcels"]] + [b["outline_local_m"] for b in grid["blocks"]]
    for f in grid["faces"]:
        for band in f["bands"].values():
            polys += [list(q) for q in band]
    bbs = [(min(q[0] for q in p) - halfw - 2, max(q[0] for q in p) + halfw + 2,
            min(q[1] for q in p) - halfw - 2, max(q[1] for q in p) + halfw + 2) for p in polys]
    umin, umax, vmin, vmax = net["box_uv"]
    out = []
    ux0, ux1 = min(b[0] for b in bbs), max(b[1] for b in bbs)
    uy0, uy1 = min(b[2] for b in bbs), max(b[3] for b in bbs)

    def blocked(e, n):
        if not (ux0 <= e <= ux1 and uy0 <= n <= uy1):
            return False
        for (x0, x1, y0, y1), p in zip(bbs, polys):
            if x0 <= e <= x1 and y0 <= n <= y1 and inside(e, n, p):
                return True
        return False

    def run(line, axis, idx, tier):
        segs, cur = [], None
        lo, hi = (vmin, vmax) if axis == "u" else (umin, umax)
        t = lo
        while t <= hi:
            u, v = (line, t) if axis == "u" else (t, line)
            e, n = fr.en(u, v)
            side = [fr.en(u + halfw + 1, v), fr.en(u - halfw - 1, v)] if axis == "u" else \
                [fr.en(u, v + halfw + 1), fr.en(u, v - halfw - 1)]
            ok = (ground.water_m(e, n) > STREET_CLEAR_OF_WATER_M
                  and u <= east_limit(v) + ROW_HALF_M
                  and not (axis == "u" and zone(None, u, v) == "railway")
                  and not blocked(e, n) and not any(blocked(*q) for q in side))
            if ok and cur is None:
                cur = [t, t]
            elif ok:
                cur[1] = t
            elif cur is not None:
                segs.append(cur)
                cur = None
            t += STREET_STEP_M
        if cur is not None:
            segs.append(cur)
        for a, b in segs:
            if b - a < 12.0:
                continue
            (e0, n0), (e1, n1) = (fr.en(line, a), fr.en(line, b)) if axis == "u" else (fr.en(a, line), fr.en(b, line))
            out.append([r1(e0), r1(n0), r1(e1), r1(n1), idx, tier])
    names = []
    for kind, lines in (("u", net["avenues"]), ("v", net["streets"])):
        for line, name, tier in lines:
            names.append(name)
            run(line, kind, len(names) - 1, 0 if tier == "measured" else 1)
    return out, names


def pick(mix: dict, rnd) -> str:
    x = rnd.random()
    for m in MATS:
        x -= mix[m]
        if x <= 0:
            return m
    return MATS[0]


def tree(e, n, rnd, src) -> dict:
    h = rnd.uniform(10.0, 17.0)
    lod = 0 if NEAR_BOX[0] <= e <= NEAR_BOX[1] and NEAR_BOX[2] <= n <= NEAR_BOX[3] else 1
    return {"e": e, "n": n, "h": h, "r": rnd.uniform(0.24, 0.32) * h, "src": src, "lod": lod}


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
    fr = Frame(grid)
    sheet_rows, plate_roi = [], []
    for s in SHEETS:
        rows, fit, rois = read_sheet(s, grid, rnd)
        sheet_rows += rows
        if SHEETS[s].get("px_roi"):
            plate_roi = rois[-1]
    plate_top_v = max(fr.uv(*q)[1] for q in plate_roi)
    reach = reach_m()
    net = network(grid, fr, reach)
    proj_rows, proj_trees, projection, east_limit, zone = projected(
        grid, ground, fr, net, sheet_rows, [plate_roi], plate_top_v, rnd)
    streets, street_names = street_segments(grid, ground, fr, net, east_limit, zone)
    trees = sheet_trees(grid, sheet_rows, rnd) + proj_trees
    srcs = ["20", "28", "35", "r10", "project"]
    roofs = ["flat", "gable", "pyramid"]
    rules = sorted({r["rule"] for r in sheet_rows + proj_rows})
    brows = []
    for r in sheet_rows + proj_rows:
        tones = len(PALETTE[r["mat"]])
        brows.append([r1(r["e"]), r1(r["n"]), r1(r["bearing"]), r1(r["w"]), r1(r["d"]), r1(r["eave"]),
                      r1(r["rise"]), roofs.index(r["roof"]), MATS.index(r["mat"]), rnd.randrange(tones),
                      rnd.randrange(len(PALETTE["roof"])), srcs.index(r["src"]), rules.index(r["rule"]), r["lod"]])
    trows = [[r1(t["e"]), r1(t["n"]), r1(t["h"]), r1(t["r"]), rnd.randrange(len(PALETTE["tree"])),
              0 if t["src"] == "sheet" else 1, t["lod"]] for t in trees]
    readings = [{k: v for k, v in rd.items()} for rd in READINGS]
    by_src = {s: sum(1 for b in brows if srcs[b[11]] == s) for s in srcs}
    projection["network"] = {
        "_doc": network.__doc__.strip(),
        "reach_m": r1(reach), "mile_m": r1(net["mile_m"]), "eighth_m": r1(net["eighth_m"]),
        "pitch_east_m": r1(net["pitch_east_m"]),
        "anchors_u_m": {k: r1(x) for k, x in net["u"].items()}, "anchors_v_m": {k: r1(x) for k, x in net["v"].items()},
        "carriageway_m": r2(CARRIAGEWAY_M),
    }
    return {
        "_doc": ("The 1904 context city: faded stand-ins for every part of the map not yet built (T-2477), its "
                 "streets and its reach to the haze (T-2491). GENERATED by tools/build_context_1904.py -- do not "
                 "hand-edit; re-run the tool. Local ENU metres of data/datum.json. Drawn by "
                 "renderers/web/js/context.js, which fades them and drops any a placed structure touches."),
        "ticket": TICKET,
        "extended_by": EXTENDED_BY,
        "scene": "1904",
        "target_date": "1904-07-01",
        "liberty": LIBERTY,
        "liberty_streets": LIBERTY_STREETS,
        "generated_by": "tools/build_context_1904.py",
        "seed": SEED,
        "sources": list(SOURCES.values()) + NETWORK_SOURCES,
        "sheet_names": SHEET_NAMES,
        "sheet_sources": SOURCES,
        "tiers": {
            "sheet_outline": ("inferred -- the smallest rectangle holding each part a Sanborn 1911 sheet draws, "
                              "carried to 1904 on Glessner House's reading that these sheets changed only at "
                              "1609-1611 and 1620 Prairie (Prairie lots are not read here); north of 16th Street, "
                              "what Robinson's 1886 plate 10 draws, carried eighteen years forward"),
            "sheet_material": "inferred -- the map's own colour: pink brick, blue stone, yellow frame",
            "projection": ("reconstructed -- no map of this ground is in hand: streets on the grid the section "
                           "corners and the street grid measure, lots on the measured frontages, buildings by the "
                           "zone the 1904 city's known uses give the block"),
            "streets": ("measured where a crossing is read (the street grid's own, the section corners), filled at "
                        "the pitch those readings give elsewhere; the carriageway's 38 ft is the grid's row_66"),
            "height_roof_colour_trees": "reconstructed -- by `rules`; the maps' storey figures are not read",
        },
        "rules": RULES,
        "readings": readings,
        "palette": PALETTE,
        "projection": projection,
        "fields": {
            "buildings": ["e", "n", "bearing_deg", "width_m", "depth_m", "eave_m", "rise_m", "roof", "material",
                          "tone", "roof_tone", "src", "rule", "lod"],
            "trees": ["e", "n", "height_m", "crown_r_m", "tone", "src", "lod"],
            "streets": ["e0", "n0", "e1", "n1", "name", "tier"],
        },
        "enums": {"roof": roofs, "material": list(MATS), "src": srcs, "rule": rules,
                  "tree_src": ["sheet", "project"], "lod": ["one to a lot", "a row of lots"],
                  "street_name": street_names, "street_tier": ["measured", "filled"]},
        "counts": {"buildings": len(brows), "by_src": by_src, "by_lod": [sum(1 for b in brows if b[13] == k) for k in (0, 1)],
                   "trees": len(trows), "streets": len(streets),
                   "street_km": r1(sum(math.hypot(s[2] - s[0], s[3] - s[1]) for s in streets) / 1000)},
        "buildings": brows,
        "trees": trows,
        "streets": streets,
    }


def dumps(doc: dict) -> str:
    head = {k: v for k, v in doc.items() if k not in ("buildings", "trees", "streets")}
    s = json.dumps(head, indent=1, ensure_ascii=False)[:-2]
    rows = lambda key: ",\n".join(json.dumps(r, separators=(",", ":")) for r in doc[key])  # noqa: E731
    return (s + f',\n "buildings": [\n{rows("buildings")}\n ],\n "trees": [\n{rows("trees")}\n ],'
            f'\n "streets": [\n{rows("streets")}\n ]\n}}\n')


def contract(doc: dict) -> list:
    """What must hold of any build: rows well formed, nothing on Prairie Avenue's lots or
    streets, nothing in the water, every sheet named a source."""
    bad = []
    grid = json.loads(GRID.read_text(encoding="utf-8"))
    prairie = [p["polygon_local_m"] for p in grid["parcels"] if p["street"] == "prairie"]
    prairie += [c["polygon_local_m"] for c in grid["carriageways"] if c["id"].startswith("prairie_")]
    ground = Ground()

    def boxed(polys):
        bb = [(min(q[0] for q in p), max(q[0] for q in p), min(q[1] for q in p), max(q[1] for q in p)) for p in polys]
        lo = (min(b[0] for b in bb), max(b[1] for b in bb), min(b[2] for b in bb), max(b[3] for b in bb))

        def hit(e, n):
            if not (lo[0] <= e <= lo[1] and lo[2] <= n <= lo[3]):
                return False
            return any(x0 <= e <= x1 and y0 <= n <= y1 and inside(e, n, p) for (x0, x1, y0, y1), p in zip(bb, polys))
        return hit
    on_prairie = boxed(prairie)
    for i, b in enumerate(doc["buildings"]):
        e, n, _, w, d, eave, rise = b[:7]
        if not (w > 0 and d > 0 and eave > 0 and rise >= 0):
            bad.append(f"building {i}: non-positive size {b}")
        if on_prairie(e, n):
            bad.append(f"building {i} at ({e}, {n}) stands on a Prairie Avenue lot or roadway")
        if ground.water_m(e, n) <= 0:
            bad.append(f"building {i} at ({e}, {n}) stands in the water")
    for i, t in enumerate(doc["trees"]):
        if on_prairie(t[0], t[1]):
            bad.append(f"tree {i} at ({t[0]}, {t[1]}) stands on Prairie Avenue")
    # A faded street never lies on the street grid's own drawing (T-2491): its carriageways,
    # alleys, lots and blocks are the grid's, and T-2475 blends where the two meet.
    gridp = [c["polygon_local_m"] for c in grid["carriageways"]] + [a["polygon_local_m"] for a in grid["alleys"]]
    gridp += [p["polygon_local_m"] for p in grid["parcels"]] + [b["outline_local_m"] for b in grid["blocks"]]
    on_grid = boxed(gridp)
    half = CARRIAGEWAY_M / 2
    for i, st in enumerate(doc.get("streets", [])):
        e0, n0, e1, n1 = st[:4]
        L = math.hypot(e1 - e0, n1 - n0)
        if L <= 0:
            bad.append(f"street {i}: zero length")
            continue
        ue, un = (e1 - e0) / L, (n1 - n0) / L
        k = 0.0
        while k <= L:
            for off in (-half, 0.0, half):
                e, n = e0 + ue * k - un * off, n0 + un * k + ue * off
                if on_grid(e, n):
                    bad.append(f"street {i} ({doc['enums']['street_name'][st[4]]}) crosses the street grid at ({r1(e)}, {r1(n)})")
                    break
            else:
                k += 5.0
                continue
            break
    src_dir = ROOT / "data" / "sources"
    for s in doc["sources"]:
        if not (src_dir / f"{s}.json").exists():
            bad.append(f"source {s} does not resolve in data/sources")
    if not doc["counts"]["by_src"].get("project") or not sum(v for k, v in doc["counts"]["by_src"].items() if k != "project"):
        bad.append("one kind of stand-in is missing entirely")
    return bad


def self_test() -> int:
    # The contract is asked of the committed document's head with its rows emptied: what is
    # tested is that each refusal fires, and --check has already asked it of every row.
    doc = dict(json.loads(OUT.read_text(encoding="utf-8")), buildings=[], trees=[], streets=[])
    grid = json.loads(GRID.read_text(encoding="utf-8"))
    p = next(q for q in grid["parcels"] if q["street"] == "prairie")["polygon_local_m"]
    e = sum(q[0] for q in p) / len(p)
    n = sum(q[1] for q in p) / len(p)
    broken = dict(doc, buildings=doc["buildings"] + [[e, n, 0, 8, 12, 10, 3, 1, 0, 0, 0, 4, 0, 0]])
    fails = contract(broken)
    ok = any("Prairie Avenue lot" in f for f in fails)
    wet = dict(doc, buildings=doc["buildings"] + [[1790.0, -3700.0, 0, 8, 12, 10, 3, 1, 0, 0, 0, 4, 0, 0]])
    ok2 = any("water" in f for f in contract(wet))
    across = dict(doc, streets=doc["streets"] + [[1300.0, -3100.0, 1500.0, -3100.0, 0, 1]])
    ok3 = any("crosses the street grid" in f for f in contract(across))
    print(f"a stand-in on a Prairie Avenue lot: {'FAIL (caught)' if ok else 'NOT CAUGHT'}")
    print(f"a stand-in in the lake: {'FAIL (caught)' if ok2 else 'NOT CAUGHT'}")
    print(f"a faded street across Prairie Avenue's blocks: {'FAIL (caught)' if ok3 else 'NOT CAUGHT'}")
    return 0 if ok and ok2 and ok3 else 1


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
