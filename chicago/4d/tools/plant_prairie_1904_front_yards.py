#!/usr/bin/env python3
"""Plant the 1904 district's front yards: garden shrubs, young trees, a bed, ivy (T-3203, T-3223).

    python3 tools/plant_prairie_1904_front_yards.py              # write data/front_yards/1904.json
    python3 tools/plant_prairie_1904_front_yards.py --check      # the committed file is what this writes,
                                                                 # and nothing it plants blocks a door
    python3 tools/plant_prairie_1904_front_yards.py --self-test  # each fault the check refuses, planted

THE ASK. The owner, 2026-10-27, thread "Improve 1904 Prairie streetscape": *"plants in front of
the houses they seem to be missing flora on the property"*. T-3203 planted 1,354 shrubs, a
continuous foundation row on nearly every lot, drawn as lumps. The owner, 2026-10-28: *"I find
the bushes and plants and flowers added to be very low quality ... make sure they don't block
doorways, etc and are positioned correctly to not block the doors"* (T-3223).

WHAT THE PICTURES SHOW (docs/RESEARCH/prairie_1904_front_yards.md). Read again, lot by lot, the
district's photographs show MOWN LAWN behind the iron fence or the stone coping, the stoop, and
the parkway elms outside; most show no shrub at all: 1801, 1811, 1816, 1905, 2120 and the 1720
and 1736 houses. Those lots are drawn as the pictures show them, bare (`BARE`). The plantings a
picture does show are Pullman's: ivy over the west front and the porch, a few low shrubs at the
porch's foot, staked young trees in the lawn, and a border of shrubs inside the 18th Street
coping (both Detroit Publishing views); and 1912's ivy, in a print dated after 1904 (inferred).
Nothing records what grew on any other lot, so the rest is RECONSTRUCTED and kept to what the
pictures make likely (docs/LIBERTIES.md L-prairie-front-yards-3203): a third of the lots left as
open lawn, the others planted in one of the period's few ways, seeded by the parcel's id so a
re-run lays the same yard and no two neighbours match:

  * a matched pair of shrubs either side of the stoop's foot (a sheared arborvitae ball, a
    hydrangea, a spiraea or a rose);
  * a lilac or an arborvitae at a front corner of the house;
  * a short group of two or three shrubs against the front, between the stoop and a corner;
  * on a deep lot, now and then a young maple or linden in the lawn, and a round bed of
    geraniums or coleus cut in it.

WHAT IT KEEPS CLEAR, measured from each plant's EDGE (its crown's half-width), not its centre.
Every 1904 structure's baked model (data/sidecars/1904/*.json -> assets/gltf/*.glb, placed as
renderers/web/js/buildings.js places it) is laid on a 0.25 m plan raster: what stands tall is the
house, what stands low is a stoop, a step, a fence, a pier or a coping, what lies flat is a walk,
and a door's leaf, at any height a raised first floor sets it (DOOR_FOOT_M), is a door. A plant
keeps clear of the house's wall, a stoop and its steps, a fence or coping, a walk, a disk of
DOOR_RADIUS_M round every door of the lot's houses, and a way 2 x DOOR_WAY_M wide from every front
door straight to the lot line. The traced Sanborn footprints (data/traces/) are laid as houses
too, so a house whose model is not in the checkout (Glessner's) still is one. `--check` holds
the committed file to those rules against the models as they stand now (a rebake that moves a
stoop under a shrub fails and names it), and to being what this tool writes.

It writes data/front_yards/1904.json, which renderers/web/js/front-yards.js draws.
"""
from __future__ import annotations

import argparse
import glob
import hashlib
import json
import math
import random
import re
import struct
import sys
from pathlib import Path

import subprocess

import numpy as np
from scipy import ndimage

ROOT = Path(__file__).resolve().parent.parent
GRID = ROOT / "data" / "street_grid" / "1904.json"
SIDECARS = ROOT / "data" / "sidecars" / "1904"
ASSETS = ROOT / "assets"
TRACES = ROOT / "data" / "traces"
OUT = ROOT / "data" / "front_yards" / "1904.json"
LIBERTY = "L-prairie-front-yards-3203"

RES = 0.25                 # the plan raster, metres a cell
LOW_TOP_M = 1.8            # a triangle starting below this stands in the yard (a stoop, a fence, a wall)
TALL_M = 2.6               # ... and one reaching above this is the house itself
FLAT_M = 0.12              # a triangle wholly below this lies on the ground (a walk, a yard surface)
GROUND_MATS = ("turf", "earth", "lawn", "grass")   # a yard surface the lawn may lie beside, not a walk
DOOR_MATS = ("door_leaf", "draft_door", "k16_door", "k12_door")
DOOR_FOOT_M = 4.5          # a door leaf whose foot is below this is an entrance (a raised first floor's)
PORCH_HALF_MAX_M = 4.5     # a porch or stoop front kept clear runs at most this far either side of its door
DOOR_RADIUS_M = 2.0        # no plant's edge nearer a door (in plan) than this
DOOR_WAY_M = 2.6           # half the clear way kept from a front door straight to the lot line: the
                           # door seen from the street, its porch or stoop front included (T-3223,
                           # the owner on Pullman's porch: "plants in front of the pullman house doors")
STOOP_GAP_M = 0.45         # a plant's edge off a stoop, a step or a porch (low work by the house)
STOOP_REACH_M = 1.2        # low work this near the house is a stoop's, not a fence's
WALL_GAP_M = 0.12          # a plant's edge off the house's wall
LOW_GAP_M = 0.25           # ... off a fence, a coping or a pier
PAVED_GAP_M = 0.2          # ... off a walk
LOT_LINE_CLEAR_M = 0.85    # ... and off the street line (the boundary, its coping and gate)
SIDE_LINE_CLEAR_M = 0.40   # ... or the side lot lines
SIDE_REACH_M = 6.0         # a corner shrub stands no further back along a side wall than this
MIN_YARD_M = 1.6           # a house nearer its lot line than this has no front yard to plant
CHECK_SLACK_M = 0.12       # --check lets a rebake move a stoop or a wall this much under a plant
GATE_BAND_M = 1.0          # a lot line's fence or wall is read this deep into the lot (T-1934)
GATE_MIN_M = 0.45          # ... and a gap in it this long to GATE_MAX_M is a gateway (on the raster)
GATE_MAX_M = 6.0
GATE_WAY_M = 3.5           # a gateway's way is kept clear this far into the lot

# What the pictures show, lot by lot (see the module doc).
PICTURED = {
    "prairie_1729": {
        "sources": ["loc_det_4a08065_pullman_residence", "loc_det_4a08066_pullman_residence"],
        "pictures": ["a16-pullman-det-4a08065", "a16-pullman-det-4a08066"],
        "creeper": {"faces": ["street"], "cover": 0.7, "height_m": [3.5, 7.5], "grade": "attested",
                    "note": "Ivy over the west front and the porch, to about the second storey's sills and "
                            "past them on the porch's piers (both Detroit Publishing views)."},
        # T-1934 (the owner, 2026-10-30: the carriage ways with "no plants blocking it"): the border
        # starts at the house's east wall (d 45.5), where the print shows it, not along the house's
        # flank, where it stood across the porte-cochere's carriage way; and it stops short of the
        # stable court's way (the drives the house's K14 yard lays are paved to every plant here).
        "border": {"edge": "high_s", "d_m": [45.5, 60.5], "inset_m": 1.1, "grade": "attested",
                   "note": "A dense border of shrubs inside the coping along 18th Street, east of the house "
                           "(LC-D4-4a08066, right of the house), clear of the carriage ways."},
        "stoop": {"plant": "spiraea", "grade": "attested",
                  "note": "Low shrubs at the foot of the porch, either side of its steps (LC-D4-4a08065)."},
        "trees": {"plant": "linden", "count": 3, "grade": "attested",
                  "note": "Young trees, staked, in the lawn between the coping and the house front "
                          "(LC-D4-4a08065)."},
        # T-1934: the summer tub plants before the palm house and the stable, each where the 1894
        # Inland plate stands it, read through the plate's solved camera
        # (data/reference_views/pullman_house_1729_prairie_conservatory/inland_1894_plate.json) on
        # the plane named in `read`, and seen again or not contradicted in Taylor's 16555. `on`
        # "floor" stands the tub on the baked terrace under it, "grade" on the ground; `top_m` is
        # the plant's top over grade as the plate reads it. Inferred for 1904: the plate is ten
        # summers before the scene, and tubs are carried in for the winter and set out again.
        "tubs": {"grade": "inferred",
                 "note": "Clipped evergreens in tubs on and before the palm house's terrace and before the "
                         "stable's arcade, as the 1894 Inland Architect plate shows them in summer (a ball "
                         "on its tub, a ball on a clear stem, and a slim clipped column by the 18th Street wall's east pier, "
                         "which Taylor's photograph 16555 shows too). Inferred for 1 July 1904: tub plants "
                         "were wintered under glass and set out again each summer, and no picture nearer "
                         "1904 shows the terrace.",
                 "sources": ["inland_1894_pullman_palm_house_stable", "aic_taylor_16555_pullman_west_front"],
                 "plants": [
                     {"plant": "globe", "e": 1472.4, "n": -3173.0, "on": "floor", "top_m": 3.24, "w": 1.13,
                      "tub_m": 0.5, "read": "plate x 845-925 px, y 763-838 px, a ball as tall as it is wide "
                      "sitting on its tub east of the plate's flight, on the terrace behind its balustrade "
                      "(n -3173.0): its top 3.24 m"},
                     {"plant": "standard", "e": 1476.4, "n": -3181.2, "on": "grade", "top_m": 2.61, "w": 1.28,
                      "tub_m": 0.55, "read": "plate x 1290-1385 px, before the stable's west arcade "
                      "(read at e 1475.8, 1.6 m off its wall): its top 2.61 m, its stem seen to 0.72 m. "
                      "Stood 0.6 m nearer the wall (1.0 m off it, e 1476.4), so the carriage drive "
                      "into the court passes it clear (T-1934; a tub is moved each summer)"},
                     {"plant": "arborvitae", "e": 1473.1, "n": -3193.4, "on": "grade", "top_m": 1.9, "w": 0.55,
                      "tub_m": 0.0, "read": "plate x 1730-1780 px, its foot at y 1053 px on the ground, "
                      "inside the wall before its east pier; Taylor's 16555 shows it at x 650 px. Read at "
                      "e 1474.0, in the mouth of the court's carriage way that 16555 shows; stood 0.9 m "
                      "west, behind the pier, within the plate's and 16555's 1 m disagreement (T-1934)"},
                 ]},
    },
    "prairie_1912": {
        "sources": ["chicagology_1912_prairie_exterior_photo"],
        "pictures": ["a19-cgy-1912-exterior"],
        "creeper": {"faces": ["street"], "cover": 0.6, "height_m": [5.0, 10.5], "grade": "inferred",
                    "note": "Ivy over the north part of the front and the round bay to the third storey in "
                            "the photograph; the print shows an electric lamp, so it is after 1904, and ivy "
                            "of that reach was growing years before it."},
    },
}
# The lots a photograph shows with a bare lawn: drawn bare (the trees in those prints stand in
# the parkway, outside the fence, and are the parkway's own).
BARE = {
    "prairie_1801": ("taylor_c1895_kimball_residence_1801", "The photograph shows the lawn open to the house."),
    "prairie_1811": ("chicagology_1811_ames_photo", "The photograph shows the lawn open either side of the stoop."),
    "prairie_1816": ("chicagology_1816_henderson_photo", "The photograph shows bare ground behind the iron fence."),
    "prairie_1905": ("chicagology_1905_field_photo", "The photograph shows the yard bare behind the iron fence."),
    "prairie_2120": ("chicagology_2120_gorton_photo", "The photograph shows the yard bare behind the fence and posts."),
    "prairie_1720": ("glessner_blog_1720_tyrrell_photo", "The photograph shows the yard bare before the porch."),
    "prairie_1736": ("glessner_blog_1736_mcbirney_c1890_photo", "The photograph shows the lawn open before the porch."),
}

# The plants a yard is planted from, as front-yards.js grows them (YARD_PLANTS there): each
# plant's height band, and its crown's width band (the renderer grows its crown to it).
PLANTS = {
    "lilac": {"name": "common lilac", "h": [2.2, 3.2], "w": [1.8, 2.6]},
    "spiraea": {"name": "Van Houtte's spiraea", "h": [1.3, 1.8], "w": [1.7, 2.3]},
    "hydrangea": {"name": "smooth hydrangea, in flower", "h": [0.9, 1.25], "w": [1.1, 1.5]},
    "rose": {"name": "garden rose, in flower", "h": [0.9, 1.3], "w": [0.8, 1.2]},
    "arborvitae": {"name": "American arborvitae, sheared to a cone", "h": [2.0, 3.2], "w": [0.9, 1.3]},
    "globe": {"name": "arborvitae sheared to a ball", "h": [0.8, 1.15], "w": [0.9, 1.25]},
    "standard": {"name": "evergreen clipped to a ball on a clear stem, in a tub", "h": [1.4, 2.6], "w": [1.1, 1.6]},
    "maple": {"name": "young sugar maple", "h": [5.5, 8.5], "w": [2.6, 4.0]},
    "linden": {"name": "young linden", "h": [5.0, 8.0], "w": [2.6, 4.2]},
}
BEDS = {"round": "a round bed cut in the lawn, bedded out", "oval": "an oval bed, bedded out"}
# Each lot takes one way of planting (its share of the reconstructed lots).
SCHEMES = [("lawn", 0.26), ("stoop", 0.32), ("corners", 0.24), ("group", 0.18)]
# ... and a stoop pair or a group takes a shrub at a corner too on this share of its lots.
WITH_CORNER = 0.4
PAIRS = ["globe", "globe", "hydrangea", "spiraea", "rose"]
CORNER = ["lilac", "lilac", "arborvitae"]
GROUP = ["hydrangea", "spiraea", "rose", "globe"]


def seed_of(key: str) -> int:
    return int(hashlib.sha256(key.encode()).hexdigest()[:8], 16)


def r2(x: float) -> float:
    return round(float(x), 2)


# ---------------------------------------------------------------- the GLBs, on the plan

def read_glb(path: Path):
    """Each primitive's material name, world-free positions (x, y, z) and triangles."""
    b = path.read_bytes()
    jlen = struct.unpack("<I", b[12:16])[0]
    j = json.loads(b[20:20 + jlen])
    off = 20 + jlen
    blen = struct.unpack("<I", b[off:off + 4])[0]
    binc = b[off + 8:off + 8 + blen]
    mats = [m.get("name", "") for m in j.get("materials", [])]

    def acc(i):
        a = j["accessors"][i]
        v = j["bufferViews"][a["bufferView"]]
        dt = {5126: np.float32, 5125: np.uint32, 5123: np.uint16, 5121: np.uint8}[a["componentType"]]
        n = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}[a["type"]]
        start = v.get("byteOffset", 0) + a.get("byteOffset", 0)
        stride = v.get("byteStride", 0)
        if stride and stride != n * np.dtype(dt).itemsize:
            raw = np.frombuffer(binc, np.uint8, count=stride * a["count"], offset=start).reshape(a["count"], stride)
            return raw[:, :n * np.dtype(dt).itemsize].copy().view(dt).reshape(a["count"], n)
        return np.frombuffer(binc, dt, count=a["count"] * n, offset=start).reshape(a["count"], n)

    out = []
    for node in j.get("nodes", []):
        if "mesh" not in node:
            continue
        for p in j["meshes"][node["mesh"]]["primitives"]:
            if p.get("mode", 4) != 4:
                continue
            pos = acc(p["attributes"]["POSITION"]).astype(np.float64)
            idx = acc(p["indices"]).reshape(-1, 3).astype(np.int64) if "indices" in p else \
                np.arange(len(pos)).reshape(-1, 3)
            out.append((mats[p["material"]] if "material" in p else "", pos, idx))
    return out


class Plan:
    """The district on a RES raster: house (tall), low (stoops, fences), paved (walks), doors."""

    def __init__(self, e0, n0, e1, n1):
        self.e0, self.n0 = e0, n0
        self.w = int(math.ceil((e1 - e0) / RES))
        self.h = int(math.ceil((n1 - n0) / RES))
        self.tall = np.zeros((self.h, self.w), bool)
        self.low = np.zeros((self.h, self.w), bool)
        self.paved = np.zeros((self.h, self.w), bool)
        self.floor = np.zeros((self.h, self.w))   # the highest level floor under LOW_TOP_M (a terrace's)
        self.doors = []   # (e, n, structure id)

    def cells(self, en):
        c = np.floor((en[:, 0] - self.e0) / RES).astype(np.int64)
        r = np.floor((en[:, 1] - self.n0) / RES).astype(np.int64)
        ok = (c >= 0) & (c < self.w) & (r >= 0) & (r < self.h)
        return r[ok], c[ok]

    def centre(self, r, c):
        return self.e0 + (c + 0.5) * RES, self.n0 + (r + 0.5) * RES

    def mark(self, mask, en):
        r, c = self.cells(en)
        mask[r, c] = True

    def lay_triangles(self, mask, tri_en, heights=None):
        """Every triangle's plan projection, sampled finer than a cell; with `heights`, each
        triangle's height is kept in the float raster `mask` where it is the highest."""
        if not len(tri_en):
            return
        a, b, c = tri_en[:, 0], tri_en[:, 1], tri_en[:, 2]
        edge = np.max(np.stack([np.hypot(*(b - a).T), np.hypot(*(c - b).T), np.hypot(*(a - c).T)]), axis=0)
        k = np.clip(np.ceil(edge / (RES * 0.7)).astype(int), 1, 400)
        for kk in np.unique(k):
            sel = k == kk
            uu, vv = np.meshgrid(np.arange(kk + 1), np.arange(kk + 1))
            keep = (uu + vv) <= kk
            u = uu[keep] / kk
            v = vv[keep] / kk
            w = 1 - u - v
            pts = (a[sel, None, :] * w[None, :, None] + b[sel, None, :] * u[None, :, None]
                   + c[sel, None, :] * v[None, :, None])
            if heights is None:
                self.mark(mask, pts.reshape(-1, 2))
                continue
            hh = np.repeat(heights[sel], pts.shape[1])
            r, c_ = np.floor((pts.reshape(-1, 2)[:, 1] - self.n0) / RES).astype(np.int64), \
                np.floor((pts.reshape(-1, 2)[:, 0] - self.e0) / RES).astype(np.int64)
            ok = (c_ >= 0) & (c_ < self.w) & (r >= 0) & (r < self.h)
            np.maximum.at(mask, (r[ok], c_[ok]), hh[ok])

    def lay_structure(self, sid, place, prims):
        d = math.radians(place.get("rotation_deg") or 0.0)
        cd, sd = math.cos(d), math.sin(d)
        e, n = place["local_e"], place["local_n"]
        for mat, pos, idx in prims:
            # three.js's yaw -rotation_deg about +Y, then (e, y, -n): buildings.js's placement
            we = e + pos[:, 0] * cd - pos[:, 2] * sd
            wn = n - pos[:, 0] * sd - pos[:, 2] * cd
            en = np.stack([we, wn], axis=1)
            y = pos[:, 1]
            tri = en[idx]
            ty = y[idx]
            lo, hi = ty.min(axis=1), ty.max(axis=1)
            name = mat.lower()
            if any(g in name for g in GROUND_MATS):
                continue
            flat = hi <= FLAT_M
            self.lay_triangles(self.paved, tri[flat])
            stand = (lo < LOW_TOP_M) & ~flat
            self.lay_triangles(self.tall, tri[stand & (hi >= TALL_M)])
            self.lay_triangles(self.low, tri[stand & (hi < TALL_M)])
            # a level floor raised off the ground (a terrace's), for a tub stood on it (T-1934)
            level = ~flat & (hi - lo <= 0.02) & (hi < LOW_TOP_M)
            self.lay_triangles(self.floor, tri[level], heights=hi[level])
            if any(name.startswith(m) for m in DOOR_MATS):
                # Every leaf whose foot stands below a raised first floor's: the front door at the
                # top of a high stoop is an entrance as much as a door at grade (T-3223: T-3203's
                # 2.5 m cut missed the raised doors of 39 lots, and planted across them).
                sel = lo < DOOR_FOOT_M
                if sel.any():
                    pts = tri[sel].reshape(-1, 2)
                    for cl in cluster(pts, 1.5):
                        self.doors.append((float(cl[0]), float(cl[1]), sid))

    def lay_polygon(self, mask, poly):
        poly = np.asarray(poly, float)
        e0, n0 = poly.min(axis=0)
        e1, n1 = poly.max(axis=0)
        c0, r0 = int((e0 - self.e0) / RES), int((n0 - self.n0) / RES)
        c1, r1 = int((e1 - self.e0) / RES) + 1, int((n1 - self.n0) / RES) + 1
        c0, r0, c1, r1 = max(c0, 0), max(r0, 0), min(c1, self.w), min(r1, self.h)
        if c1 <= c0 or r1 <= r0:
            return
        rr, cc = np.mgrid[r0:r1, c0:c1]
        pe, pn = self.centre(rr, cc)
        mask[r0:r1, c0:c1] |= inside(pe, pn, poly)


def cluster(pts, gap):
    """Points into groups no further than `gap` apart; each group's middle."""
    out = []
    for p in pts:
        for g in out:
            if math.hypot(p[0] - g[0] / g[2], p[1] - g[1] / g[2]) < gap:
                g[0] += p[0]; g[1] += p[1]; g[2] += 1
                break
        else:
            out.append([p[0], p[1], 1])
    return [(g[0] / g[2], g[1] / g[2]) for g in out]


def inside(pe, pn, poly):
    """Vectorised even-odd point-in-polygon."""
    res = np.zeros(pe.shape, bool)
    m = len(poly)
    for i in range(m):
        (xa, ya), (xb, yb) = poly[i], poly[(i + 1) % m]
        cond = (ya > pn) != (yb > pn)
        with np.errstate(divide="ignore", invalid="ignore"):
            xi = xa + (pn - ya) * (xb - xa) / (yb - ya)
        res ^= cond & (pe < xi)
    return res


# ---------------------------------------------------------------- one lot

def gate_ways(s, d, width, fence, inlot):
    """T-1934 (the owner, 2026-10-30, on Pullman's carriage ways: "no plants blocking it"): every
    gateway in a lot's fence or wall is kept clear. Along each of the lot's three street-side
    lines (the street line, d 0, and the side lines, s 0 and s = width) the fence, coping or pier
    raster is read in a band GATE_BAND_M deep; a run along the line with none of it, closed by
    fence at both ends and GATE_MIN_M to GATE_MAX_M long, is an opening, and a way as wide as it
    is kept clear GATE_WAY_M into the lot. Returns the mask of those ways."""
    out = np.zeros(s.shape, bool)
    for along, depth, lo in ((s, d, 0.0), (d, s, 0.0), (d, width - s, 0.0)):
        band = inlot & (depth >= lo) & (depth <= GATE_BAND_M)
        if not band.any():
            continue
        a = np.round(along[band] / RES).astype(int)
        f = fence[band]
        if not f.any():
            continue
        a0, a1 = a.min(), a.max()
        has = np.zeros(a1 - a0 + 1, bool)
        np.logical_or.at(has, a[f] - a0, True)
        seen = np.zeros(a1 - a0 + 1, bool)
        seen[a - a0] = True
        k = 0
        while k < len(has):
            if has[k] or not seen[k]:
                k += 1
                continue
            j = k
            while j < len(has) and not has[j] and seen[j]:
                j += 1
            closed = k > 0 and has[k - 1] and j < len(has) and has[j]
            L = (j - k) * RES
            if closed and GATE_MIN_M <= L <= GATE_MAX_M:
                t0, t1 = (a0 + k) * RES - RES / 2, (a0 + j) * RES - RES / 2
                out |= inlot & (along >= t0) & (along <= t1) & (depth >= lo) & (depth <= GATE_WAY_M)
            k = j
    return out


def lot_frame(p):
    cs = p["corners_local_m"]
    street = [np.array(v, float) for k, v in cs.items() if k.endswith("_street")]
    rear = [np.array(v, float) for k, v in cs.items() if k.endswith("_rear")]
    if len(street) != 2 or len(rear) != 2:
        return None
    a, b = street
    su = (b - a) / np.linalg.norm(b - a)
    mid_rear = (rear[0] + rear[1]) / 2
    nu = np.array([-su[1], su[0]])
    if np.dot(mid_rear - (a + b) / 2, nu) < 0:
        nu = -nu
    return a, su, nu, float(np.linalg.norm(b - a))


class Yard:
    """One lot's window of the plan in the lot's own frame (s along the street line, d into the
    lot), with how much room a plant has at every cell: the half-width a crown may have there
    and keep its edge off the house, a stoop, a fence, a walk, a door and the lot's lines."""

    def __init__(self, p, plan: Plan, house, sids):
        self.ok = False
        fr = lot_frame(p)
        if fr is None:
            return
        A, su, nu, width = fr
        self.A, self.su, self.nu, self.width = A, su, nu, width
        poly = np.asarray(p["polygon_local_m"], float)
        e0, n0 = poly.min(axis=0) - 3.0
        e1, n1 = poly.max(axis=0) + 3.0
        c0, r0 = max(int((e0 - plan.e0) / RES), 0), max(int((n0 - plan.n0) / RES), 0)
        c1, r1 = min(int((e1 - plan.e0) / RES) + 1, plan.w), min(int((n1 - plan.n0) / RES) + 1, plan.h)
        self.r0, self.c0 = r0, c0
        rr, cc = np.mgrid[r0:r1, c0:c1]
        pe, pn = plan.centre(rr, cc)
        self.pe, self.pn = pe, pn
        s = (pe - A[0]) * su[0] + (pn - A[1]) * su[1]
        d = (pe - A[0]) * nu[0] + (pn - A[1]) * nu[1]
        self.s, self.d = s, d
        inlot = inside(pe, pn, poly)
        self.inlot = inlot
        Hw = house[r0:r1, c0:c1]
        H = Hw & inlot
        if not H.any():
            return
        front = float(np.where(H, d, np.inf).min())
        self.front = front
        self.H = H
        low = plan.low[r0:r1, c0:c1]
        paved = plan.paved[r0:r1, c0:c1]
        dh = ndimage.distance_transform_edt(~Hw) * RES
        stoop = low & (dh <= STOOP_REACH_M)
        fence = low & ~stoop
        # The lot's doors: every door of a structure on it, in the window.
        self.doors = []
        keep = np.zeros(H.shape, bool)
        stoops, _ = ndimage.label(stoop)
        for de, dn, sid in plan.doors:
            if sid not in sids:
                continue
            ds = (de - A[0]) * su[0] + (dn - A[1]) * su[1]
            dd = (de - A[0]) * nu[0] + (dn - A[1]) * nu[1]
            if not (-3 <= ds <= width + 3) or dd > front + 30:
                continue
            keep |= (pe - de) ** 2 + (pn - dn) ** 2 <= DOOR_RADIUS_M ** 2
            front_door = -0.5 <= ds <= width + 0.5 and dd <= front + 8.0
            if front_door:
                keep |= (np.abs(s - ds) <= DOOR_WAY_M) & (d <= dd + 0.5) & (d >= -1)
                # ...and the whole front of the stoop or porch the door opens onto, whatever its
                # width (T-3227: Pullman's porch is wider than the door's way)
                near = stoops * (((pe - de) ** 2 + (pn - dn) ** 2) <= DOOR_RADIUS_M ** 2 + 1.0)
                for k in np.unique(near[near > 0]):
                    ss = s[stoops == k]
                    lo_, hi_ = max(ss.min(), ds - PORCH_HALF_MAX_M), min(ss.max(), ds + PORCH_HALF_MAX_M)
                    keep |= (s >= lo_ - 0.3) & (s <= hi_ + 0.3) & (d <= dd + 0.5) & (d >= -1)
            self.doors.append((r2(ds), r2(dd), front_door))
        self.keep = keep
        edt = lambda m: ndimage.distance_transform_edt(~m) * RES if m.any() else np.full(m.shape, 99.0)
        self.gate_way = gate_ways(s, d, width, fence, inlot)
        self.terms = {
            "the house's wall": dh - WALL_GAP_M,
            "a stoop or its steps": edt(stoop) - STOOP_GAP_M,
            "a fence, coping or pier": edt(fence) - LOW_GAP_M,
            "a walk": edt(paved) - PAVED_GAP_M,
            "a door or the way to it": edt(keep),
            "a gateway in the lot's fence or wall": edt(self.gate_way),
            "the lot's lines": np.minimum(np.minimum(d - LOT_LINE_CLEAR_M, s - SIDE_LINE_CLEAR_M),
                                          width - SIDE_LINE_CLEAR_M - s),
        }
        room = np.minimum.reduce(list(self.terms.values()))
        room[~inlot | Hw] = -1
        self.room = room
        self.dh = dh
        self.dstoop = self.terms["a stoop or its steps"] + STOOP_GAP_M
        self.ok = True

    def world(self, i):
        return r2(self.pe.flat[i]), r2(self.pn.flat[i])

    def floor_at(self, e, n, plan):
        """The level floor's height under a point, metres over grade (0 on the ground)."""
        r, c = int((n - plan.n0) / RES), int((e - plan.e0) / RES)
        return float(plan.floor[r, c]) if 0 <= r < plan.h and 0 <= c < plan.w else 0.0

    def at(self, e, n):
        r = int((n - (self.pn[0, 0] - RES / 2)) / RES)
        c = int((e - (self.pe[0, 0] - RES / 2)) / RES)
        return (r, c) if 0 <= r < self.room.shape[0] and 0 <= c < self.room.shape[1] else None

    def why(self, rc, r):
        """The rule a plant of half-width r at cell rc breaks, or None."""
        if not self.inlot[rc]:
            return "outside its lot"
        if self.H[rc]:
            return "inside the house"
        near = [f"{name} ({max(0.0, t[rc]):.2f} m of room for {r:.2f})" for name, t in self.terms.items()
                if t[rc] < r - CHECK_SLACK_M]
        return f"too near {', '.join(near)}" if near else None


def plant_lot(p, plan: Plan, house, sids):
    y = Yard(p, plan, house, sids)
    if not y.ok:
        return None
    front = y.front
    if front < MIN_YARD_M or front > 30:
        return None
    rng = random.Random(seed_of(p["id"]))
    s, d, room = y.s, y.d, y.room
    pic = PICTURED.get(p["id"], {})
    shrubs, trees, beds, taken = [], [], [], []

    def clear_of_others(e, n, r, k=1.0):
        return all(math.hypot(e - x, n - yy) >= (r + rr) * k for x, yy, rr in taken)

    def size(key):
        pl = PLANTS[key]
        t = rng.random()
        h = pl["h"][0] + (pl["h"][1] - pl["h"][0]) * t
        w = (pl["w"][0] + pl["w"][1]) / 2 * h / ((pl["h"][0] + pl["h"][1]) / 2)
        return r2(h), r2(w)

    def best(mask, score, r, k=1.0):
        """The best-scoring cell of `mask` with room for half-width r, clear of what is planted."""
        idx = np.flatnonzero(mask & (room >= r))
        if not len(idx):
            return None
        for i in idx[np.argsort(score.flat[idx], kind="stable")][:400]:
            e, n = y.world(i)
            if clear_of_others(e, n, r, k):
                return i
        return None

    def put(key, i, grade=None, h=None, w=None):
        if h is None:
            h, w = size(key)
        e, n = y.world(i)
        row = [e, n, key, h, w] + ([grade] if grade else [])
        (trees if key in ("maple", "linden") else shrubs).append(row)
        taken.append((e, n, 0.4 if key in ("maple", "linden") else w / 2))
        return h, w

    # the house's front, its first metres along the sides, and its corners
    Hf = y.H & (d <= front + 1.0)
    s_lo, s_hi = float(s[Hf].min()), float(s[Hf].max())
    hug = lambda r, reach=0.55: (y.dh <= r + WALL_GAP_M + reach) | (y.dstoop <= r + STOOP_GAP_M + reach)
    front_doors = sorted([dd for dd in y.doors if dd[2]], key=lambda dd: dd[1])
    bare = BARE.get(p["id"])
    if bare:
        scheme = "pictured bare"
    elif pic:
        scheme = "pictured"
    else:
        roll = rng.random()
        acc = 0.0
        scheme = SCHEMES[-1][0]
        for name, share in SCHEMES:
            acc += share
            if roll < acc:
                scheme = name
                break

    # A house drawn with no front door (an unworked draft) has no stoop to flank and no known
    # way in, so its planting keeps off the front altogether: only beside its corners.
    if not front_doors and scheme in ("stoop", "group"):
        scheme = "corners"

    if scheme == "stoop" or "stoop" in pic:
        if front_doors:
            ds0 = front_doors[0][0]
            key = pic["stoop"]["plant"] if "stoop" in pic else rng.choice(PAIRS)
            h, w = size(key)
            r = w / 2
            zone = hug(r) & (d <= front + 1.5)
            left = best(zone & (s < ds0), np.abs(s - ds0) + 0.4 * np.abs(d - front), r)
            right = best(zone & (s > ds0), np.abs(s - ds0) + 0.4 * np.abs(d - front), r)
            if left is not None and right is not None:
                g = pic.get("stoop", {}).get("grade")
                put(key, left, g, h, w)
                put(key, right, g, h, w)
            elif scheme == "stoop":
                # no room for a matched pair at this stoop: a pair or nothing, never one
                scheme = "corners"
        elif scheme == "stoop":
            scheme = "corners"

    extra_corner = scheme in ("stoop", "group") and rng.random() < WITH_CORNER
    if scheme == "corners" or extra_corner:
        both = scheme == "corners" and rng.random() < 0.5
        corners = [(s_lo, -1), (s_hi, 1)]
        rng.shuffle(corners)
        for cs, side in corners[: 2 if both else 1]:
            key = rng.choice(CORNER)
            h, w = size(key)
            r = w / 2
            zone = hug(r, 0.7) & (d <= front + SIDE_REACH_M) & (d >= front - r - 1.0)
            if not front_doors:
                zone &= (s < s_lo) | (s > s_hi)
            target_s = cs + side * (r + 0.2)
            i = best(zone, np.hypot(s - target_s, d - (front + 0.6)), r)
            if i is not None:
                put(key, i, None, h, w)

    if scheme == "group":
        key = rng.choice(GROUP)
        h, w = size(key)
        r = w / 2
        zone = hug(r, 0.45) & (d <= front + 0.8)
        cand = np.flatnonzero(zone & (room >= r))
        if len(cand):
            i0 = int(cand[rng.randrange(len(cand))])
            e0, n0 = y.world(i0)
            n_ = rng.choice([2, 3, 3])
            step = w * 0.92
            sgn = rng.choice([-1, 1])
            for k in range(n_):
                ts = s.flat[i0] + sgn * k * step
                i = best(zone, np.hypot(s - ts, d - d.flat[i0]), r, 0.85)
                if i is None:
                    break
                if k and math.hypot(s.flat[i] - ts, d.flat[i] - d.flat[i0]) > 0.6:
                    break
                put(key, i, None, h, w)

    # pictured tub plants (Pullman's, T-1934): each where its picture stands it, not searched for;
    # the border and the lawn's trees then keep off them as off any planting
    if "tubs" in pic:
        for t in pic["tubs"]["plants"]:
            stand = r2(y.floor_at(t["e"], t["n"], plan)) if t["on"] == "floor" else 0.0
            h = r2(t["top_m"] - stand - t["tub_m"])
            shrubs.append([t["e"], t["n"], t["plant"], h, t["w"], pic["tubs"]["grade"], stand, t["tub_m"]])
            taken.append((t["e"], t["n"], t["w"] / 2))

    # a pictured border (Pullman's along 18th Street), kept off the coping as every plant is
    if "border" in pic:
        bd = pic["border"]
        edge_s = bd["inset_m"] if bd["edge"] == "low_s" else y.width - bd["inset_m"]
        dd = bd["d_m"][0]
        while dd <= bd["d_m"][1]:
            key = "spiraea" if rng.random() < 0.7 else "lilac"
            h, w = size(key)
            i = best((np.abs(d - dd) <= 0.6) & (np.abs(s - edge_s) <= 1.2), np.abs(s - edge_s) + np.abs(d - dd), w / 2, 0.8)
            if i is not None:
                put(key, i, bd["grade"], h, w)
            dd += rng.uniform(1.4, 1.9)

    # young trees: Pullman's, pictured; elsewhere, now and then on a deep lot
    want_trees = 0
    tree_key = None
    if "trees" in pic:
        want_trees, tree_key = pic["trees"]["count"], pic["trees"]["plant"]
    elif not bare and front >= 7.0 and rng.random() < 0.25:
        want_trees, tree_key = 1, rng.choice(["maple", "linden"])
    if want_trees:
        lawn = (y.dh >= 3.5) & (d >= 2.0) & (d <= front - 2.0) & (y.terms["a walk"] >= 0.9) \
            & (y.terms["a door or the way to it"] >= 1.2)
        for k in range(want_trees):
            if "trees" in pic:
                # spread through the lawn as the views show them: each as far from every
                # other planting as the lawn allows
                near = np.full(room.shape, 30.0)
                for x, yy, _ in taken:
                    near = np.minimum(near, np.hypot(y.pe - x, y.pn - yy))
                score = -near + rng.random() * 0.01
            else:
                frac = s / max(1.0, y.width)
                score = np.minimum(np.abs(frac - 0.18), np.abs(frac - 0.82)) + 0.02 * np.abs(d - front * 0.45)
            i = best(lawn, score, 0.4, 1.0)
            if i is None:
                break
            put(tree_key, i, pic.get("trees", {}).get("grade"))

    # a bed in the lawn: on a quarter of the planted lots deep enough to hold one
    if not bare and scheme != "lawn" and front >= 6.5 and rng.random() < 0.25:
        kind = rng.choice(["round", "round", "oval"])
        a_ = rng.uniform(0.85, 1.15) if kind == "round" else rng.uniform(1.2, 1.5)
        b_ = a_ if kind == "round" else a_ * rng.uniform(0.55, 0.7)
        R = max(a_, b_)
        lawn = (d <= front - R - 1.2) & (y.terms["a walk"] >= R + 0.5) & (y.terms["a door or the way to it"] >= R + 0.6)
        i = best(lawn, -room + 0.3 * np.abs(d - front * 0.5), R + 0.3, 1.0)
        if i is not None:
            e, n = y.world(i)
            heading = math.degrees(math.atan2(y.su[0], y.su[1]))
            beds.append([e, n, r2(a_), r2(b_), r2(heading % 360), kind, rng.randrange(4)])
            taken.append((e, n, R))

    # creeper on the walls a picture shows it on
    creeper = []
    if "creeper" in pic:
        cr = pic["creeper"]
        H = y.H
        sh = int(round(0.5 / RES))
        behind = ndimage.shift(H.astype(np.uint8), (-y.nu[1] * sh, -y.nu[0] * sh), order=0, cval=0) > 0
        hugc = (y.inlot & ~H & (y.dh <= 0.3) & behind & (d < front + 6.0) & (y.terms["a walk"] >= 0.0)
                & (y.terms["a door or the way to it"] >= 0.0))
        cand = list(np.flatnonzero(hugc))
        rng.shuffle(cand)
        cand.sort(key=lambda i: s.flat[i])
        last = -9.0
        for i in cand:
            if s.flat[i] - last < 0.9:
                continue
            last = s.flat[i]
            if rng.random() > cr["cover"]:
                continue
            w = r2(rng.uniform(1.2, 1.9))
            # the patch's whole width off a door and its way, not just its middle
            if y.terms["a door or the way to it"].flat[i] < w / 2:
                continue
            e, n = y.world(i)
            creeper.append([e, n, r2(math.degrees(math.atan2(-y.nu[0], -y.nu[1])) % 360),
                            w, r2(rng.uniform(*cr["height_m"]))])

    out = {
        "parcel": p["id"], "street": p["street"], "side": p.get("side"),
        "addresses": p.get("addresses_1911", []),
        "frame": {"origin": [r2(y.A[0]), r2(y.A[1])], "along": [round(float(y.su[0]), 5), round(float(y.su[1]), 5)],
                  "into": [round(float(y.nu[0]), 5), round(float(y.nu[1]), 5)], "width_m": r2(y.width)},
        "front_m": r2(front), "doors": [[a, b] for a, b, f in y.doors if f], "scheme": scheme,
        "grade": "attested" if bare else "reconstructed",
        "shrubs": shrubs, "trees": trees, "beds": beds, "creeper": creeper,
    }
    if bare:
        out["pictured"] = {"sources": [bare[0]]}
        out["pictured_notes"] = {"bare": {"grade": "attested", "note": bare[1]}}
    elif pic:
        out["pictured"] = {k: v for k, v in pic.items() if k in ("sources", "pictures")}
        if "tubs" in pic:
            out["pictured"]["sources"] = out["pictured"]["sources"] + pic["tubs"]["sources"]
        out["pictured_notes"] = {k: {"grade": v["grade"], "note": v["note"]} for k, v in pic.items()
                                 if isinstance(v, dict) and "grade" in v}
    return out

# ---------------------------------------------------------------- the district

def tracked_models() -> set[str]:
    """The baked models git carries. Glessner's is built elsewhere and ignored here, so the
    tool reads the same models on every checkout and lays that house from its trace."""
    out = subprocess.run(["git", "ls-files", "-z", "assets/gltf"], cwd=ROOT, capture_output=True, check=True)
    return {s for s in out.stdout.decode().split("\0") if s}


def lay_district():
    """The district's plan raster, with every 1904 model and trace laid on it."""
    grid = json.loads(GRID.read_text())
    parcels = grid["parcels"]
    allp = np.concatenate([np.asarray(p["polygon_local_m"], float) for p in parcels])
    e0, n0 = allp.min(axis=0) - 20
    e1, n1 = allp.max(axis=0) + 20
    plan = Plan(float(e0), float(n0), float(e1), float(n1))
    by_parcel: dict[str, set] = {}
    tracked = tracked_models()
    for f in sorted(SIDECARS.glob("*.json")):
        sc = json.loads(f.read_text())
        if "placement" not in sc or "asset" not in sc:
            continue
        pl = sc["placement"]
        if pl.get("local_e") is None:
            continue
        m = re.findall(r"parcel (\w+)", pl.get("symbolic_location") or "")
        if m:
            by_parcel.setdefault(m[0], set()).add(sc["id"])
        glb = ASSETS / sc["asset"]
        if f"assets/{sc['asset']}" not in tracked or not glb.exists():
            continue   # traced below
        plan.lay_structure(sc["id"], pl, read_glb(glb))
    traced = np.zeros_like(plan.tall)
    for f in sorted(glob.glob(str(TRACES / "prairie_1904_footprints_s*.json"))):
        for tp in json.loads(Path(f).read_text())["parcels"]:
            for b in tp["buildings"]:
                if b.get("for_1904") in ("not_1904",) or not b.get("polygon_local_m"):
                    continue
                plan.lay_polygon(traced, b["polygon_local_m"])
    # a house is its walls closed and filled, and the trace where no model stands
    house = ndimage.binary_fill_holes(ndimage.binary_closing(plan.tall, iterations=3)) | traced
    house = ndimage.binary_opening(house, iterations=1) | plan.tall
    return grid, parcels, plan, house, by_parcel


def build(laid=None):
    grid, parcels, plan, house, by_parcel = laid or lay_district()
    lots = []
    for p in parcels:
        lot = plant_lot(p, plan, house, by_parcel.get(p["id"], set()))
        if lot:
            lots.append(lot)
    lots.sort(key=lambda l: l["parcel"])
    schemes = {}
    for l in lots:
        schemes[l["scheme"]] = schemes.get(l["scheme"], 0) + 1
    summary = {
        "lots": len(lots),
        "shrubs": sum(len(l["shrubs"]) for l in lots),
        "trees": sum(len(l["trees"]) for l in lots),
        "beds": sum(len(l["beds"]) for l in lots),
        "creeper_patches": sum(len(l["creeper"]) for l in lots),
        "attested_plants": sum(1 for l in lots for s in l["shrubs"] + l["trees"] if len(s) > 5),
        "lots_with_a_door": sum(1 for l in lots if l["doors"]),
        "schemes": dict(sorted(schemes.items())),
    }
    return {
        "_doc": "The 1904 district's front yards (T-3203, T-3223): garden shrubs, young trees, a bed and ivy, "
                "each lot planted as its photograph shows it or, unpictured, in one of the period's few ways, "
                "and kept clear of every door, stoop, walk and fence. GENERATED by "
                "tools/plant_prairie_1904_front_yards.py from data/street_grid/1904.json, the 1904 "
                "sidecars' baked models and the traced Sanborn footprints -- do not hand-edit; re-run the "
                "tool. Local ENU metres of data/datum.json. shrubs and trees: [e, n, plant, height_m, "
                "crown_width_m, (grade if not the lot's), (stand_m, tub_m: a tub plant's, what its tub stands on "
                "over the ground and the tub's height)]; beds: [e, n, half_length_m, half_width_m, "
                "heading_deg, kind, scheme]; creeper: [e, n, facing_deg, width_m, height_m]. The lawn is "
                "the ground's own sward.",
        "scene": "1904", "target_date": "1904-07-01", "ticket": "T-3223",
        "generated_by": "tools/plant_prairie_1904_front_yards.py",
        "liberty": LIBERTY,
        "plants": PLANTS, "beds": BEDS,
        "placement": {
            "raster_m": RES, "door_radius_m": DOOR_RADIUS_M, "door_way_half_m": DOOR_WAY_M,
            "stoop_gap_m": STOOP_GAP_M, "wall_gap_m": WALL_GAP_M, "low_gap_m": LOW_GAP_M,
            "paved_gap_m": PAVED_GAP_M, "lot_line_clear_m": LOT_LINE_CLEAR_M, "min_yard_m": MIN_YARD_M,
            "schemes": dict(SCHEMES),
            "note": "Each plant's crown edge stands clear of the house's wall, every stoop and step, fence, "
                    "coping and walk, a 2 m disk round every door, and a 5.2 m way from each front door to "
                    "the lot line. Lots a photograph shows bare are bare. Seeded by the parcel's id.",
        },
        "summary": summary,
        "lots": lots,
    }


def collisions(data, laid) -> list[str]:
    """Every planting the file lays that now breaks a clearance against the models as they stand:
    in a house, on or against a stoop, a step, a fence or a walk, or across a door or its way. A
    rebake that moves a stoop under a shrub is what this catches; one that moves nothing a yard
    touches is not (CHECK_SLACK_M of drift is allowed)."""
    grid, parcels, plan, house, by_parcel = laid
    by_id = {p["id"]: p for p in parcels}
    out = []
    for lot in data["lots"]:
        p = by_id.get(lot["parcel"])
        if p is None:
            out.append(f"{lot['parcel']}: no such lot in the street grid")
            continue
        y = Yard(p, plan, house, by_parcel.get(lot["parcel"], set()))
        if not y.ok:
            if lot["shrubs"] or lot["trees"] or lot["beds"]:
                out.append(f"{lot['parcel']}: planted, but no house stands on it now")
            continue
        an = lambda w: ("an " if w[0] in "aeiou" else "a ") + w
        # a tub stood up on a floor (Pullman's terrace) stands on what is built, so only the floor
        # under it is asked: that it is still there, at the height the row says
        for s in lot["shrubs"]:
            if len(s) > 6 and s[6] > 0:
                f = y.floor_at(s[0], s[1], plan)
                if abs(f - s[6]) > CHECK_SLACK_M:
                    out.append(f"{lot['parcel']}: {an(PLANTS[s[2]]['name'])} at {s[0]:.2f} E, {s[1]:.2f} N "
                               f"stands on a floor {s[6]:.2f} m up, and the models put one {f:.2f} m up there")
        things = [(an(PLANTS[s[2]]["name"]), s[0], s[1], s[4] / 2) for s in lot["shrubs"]
                  if not (len(s) > 6 and s[6] > 0)] + \
                 [(an(PLANTS[t[2]]["name"]), t[0], t[1], 0.4) for t in lot["trees"]] + \
                 [("a bed", b[0], b[1], max(b[2], b[3])) for b in lot["beds"]]
        # ivy hugs the wall, so only a door and its way bound it: its whole width clear of them
        for c in lot["creeper"]:
            rc = y.at(c[0], c[1])
            if rc is not None and y.terms["a door or the way to it"][rc] < c[3] / 2 - CHECK_SLACK_M:
                out.append(f"{lot['parcel']}: ivy at {c[0]:.2f} E, {c[1]:.2f} N stands too near a door or "
                           f"the way to it ({max(0.0, y.terms['a door or the way to it'][rc]):.2f} m of room "
                           f"for {c[3] / 2:.2f})")
        for name, e, n, r in things:
            rc = y.at(e, n)
            if rc is None:
                out.append(f"{lot['parcel']}: {name} at {e:.2f} E, {n:.2f} N is outside the lot's window")
                continue
            why = y.why(rc, r)
            if why:
                out.append(f"{lot['parcel']}: {name} at {e:.2f} E, {n:.2f} N stands {why}")
    return out


def self_test() -> int:
    """Plant each fault the check refuses on a real lot, and prove it is refused."""
    laid = lay_district()
    data = build(laid)
    ok = True

    def case(label, mutate, want):
        nonlocal ok
        d = json.loads(json.dumps(data))
        mutate(d)
        bad = collisions(d, laid)
        hit = any(want in b for b in bad)
        ok &= hit
        print(f"   self-test | {'ok  ' if hit else 'FAIL'} the check refuses {label}"
              + (f": {bad[0]}" if bad else ""))

    clean = collisions(data, laid)
    print(f"   self-test | {'ok  ' if not clean else 'FAIL'} the planted file passes its own check"
          + (f": {clean[0]}" if clean else ""))
    ok &= not clean
    lot = next(l for l in data["lots"] if l["doors"] and l["shrubs"] and l["front_m"] >= 4)
    A = np.array(lot["frame"]["origin"]); su = np.array(lot["frame"]["along"]); nu = np.array(lot["frame"]["into"])
    ds, dd = lot["doors"][0]
    at = lambda s_, d_: [r2(A[0] + su[0] * s_ + nu[0] * d_), r2(A[1] + su[1] * s_ + nu[1] * d_)]

    def shrub_at(s_, d_):
        def m(d):
            l = next(x for x in d["lots"] if x["parcel"] == lot["parcel"])
            l["shrubs"].append([*at(s_, d_), "globe", 1.0, 1.0])
        return m
    case("a shrub on the way to a front door", shrub_at(ds, max(1.5, lot["front_m"] - 2.5)), "a door")
    case("a shrub beside a front door", shrub_at(ds + 1.2, min(dd, lot["front_m"]) - 0.7), "door")
    case("a shrub in the house", shrub_at(ds, dd + 3.0), "inside the house")

    def ivy_at(s_, d_):
        def m(d):
            l = next(x for x in d["lots"] if x["parcel"] == lot["parcel"])
            l["creeper"].append([*at(s_, d_), 270.0, 1.5, 5.0])
        return m
    case("ivy on the wall beside a front door", ivy_at(ds + 1.0, dd - 0.3), "ivy at")

    def tub_afloat(d):
        l = next(x for x in d["lots"] if x["parcel"] == "prairie_1729")
        s_ = next(s for s in l["shrubs"] if len(s) > 6 and s[6] > 0)
        s_[6] = r2(s_[6] + 0.6)
    case("a tub stood on a floor the models do not have", tub_afloat, "stands on a floor")

    def in_gateway(d):
        # T-1934: inside the wall's gateway on 18th Street that Pullman's carriages came through
        l = next(x for x in d["lots"] if x["parcel"] == "prairie_1729")
        l["shrubs"].append([1475.3, -3194.2, "globe", 1.0, 1.0])
    case("a shrub in a gateway", in_gateway, "a gateway")
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    laid = lay_district()
    data = build(laid)
    text = json.dumps(data, indent=1, ensure_ascii=False) + "\n"
    if args.check:
        # THE CHECK ASKS TWO QUESTIONS, because the yards stand on the baked houses and every
        # house ticket rebakes one. Whatever the file, no planting in it may stand in a house,
        # against a stoop, a step, a fence or a walk, or across a door or its way, against the
        # models as they stand now (T-3223). Then: it is what the tool writes; a file merely
        # behind a rebake that moved nothing a yard touches passes, and says to refresh it.
        if not OUT.exists():
            print(f"{OUT.relative_to(ROOT)} is missing: run tools/plant_prairie_1904_front_yards.py", file=sys.stderr)
            return 1
        bad = collisions(json.loads(OUT.read_text()), laid)
        if bad:
            for line in bad[:20]:
                print(f"  {line}", file=sys.stderr)
            print(f"{OUT.relative_to(ROOT)}: {len(bad)} planting(s) stand on something built or across a "
                  "door's way: re-run tools/plant_prairie_1904_front_yards.py", file=sys.stderr)
            return 1
        if OUT.read_text() == text:
            print(f"front yards: {OUT.relative_to(ROOT)} is what the tool writes, and every planting clears "
                  f"every door, stoop, walk and fence ({data['summary']})")
            return 0
        print(f"front yards: {OUT.relative_to(ROOT)} is behind the models (a house was rebaked since), "
              "and every planting still clears what is built; re-run the tool to refresh it")
        return 0
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text)
    print(f"wrote {OUT.relative_to(ROOT)}: {data['summary']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
