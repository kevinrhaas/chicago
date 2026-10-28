#!/usr/bin/env python3
"""Plant the 1904 district's front yards: foundation shrubs, low beds, creeper (T-3203).

    python3 tools/plant_prairie_1904_front_yards.py           # write data/front_yards/1904.json
    python3 tools/plant_prairie_1904_front_yards.py --check   # the committed file is what this writes

THE ASK (the owner, 2026-10-27, thread "Improve 1904 Prairie streetscape"): *"plants in front
of the houses they seem to be missing flora on the property"*. Every house lot of the drawn
district was the field's bare sward from its lot line to its front wall, with nothing planted.

WHAT THE PICTURES SHOW, and what is therefore graded as what (the brief's section 7,
tickets/evidence/streetscape-1904-2026-10-27/BRIEF.md):

  * the Detroit Publishing views of the Pullman house (LC-D4-4a08065, -4a08066, 1890s) show
    ivy over the west front and the porch, and a dense border of shrubs inside the coping
    along 18th Street east of the house: ATTESTED, at Pullman's;
  * the photograph of 1912 Prairie (the Moulton-Lowden house; an electric street lamp dates
    the print after 1904) shows ivy over the north part of the front and the round bay up to
    the third storey: INFERRED for 1904 (ivy of that reach is years old when photographed);
  * no picture read here shows an urn on a stoop clearly enough to place one, so none is placed;
  * nothing records species, beds or shrubs lot by lot. Every other lot gets the district's
    common treatment, RECONSTRUCTED (docs/LIBERTIES.md L-prairie-front-yards-3203): foundation
    shrubs along the front and the first metres of the sides, and one to three low beds cut in
    the lawn before the house, all varied per lot by a seed taken from the parcel's id, so a re-run lays the same yard and no two neighbours match.

WHAT IT READS, so the planting keeps clear of what is built. Every 1904 structure's baked
model (data/sidecars/1904/*.json -> assets/gltf/*.glb, placed by the sidecar's local_e,
local_n and rotation_deg exactly as renderers/web/js/buildings.js places it) is laid on a
0.25 m plan raster of the district: what stands tall is the house, what stands low is a stoop,
a fence, a pier or a coping, what lies flat is a paved walk, and a door's leaf names the line
of the walk to it, kept clear from the door to the lot line. The traced Sanborn footprints
(data/traces/prairie_1904_footprints_s*.json) are laid as well, so a house whose model is
not in the checkout (Glessner's) is still a house. The lots, their street lines and the
frame each yard is measured in are the T-0474 grid's (data/street_grid/1904.json).

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
DOOR_CLEAR_M = 1.35        # half the clear way kept from a door to the lot line
SHRUB_WALL_M = (0.45, 0.95)   # a foundation shrub's centre, off the house's wall
SIDE_REACH_M = 7.0         # foundation planting runs this far back along a side wall
LOT_LINE_CLEAR_M = 0.85    # nothing nearer the street line (the boundary, its coping and gate)
SIDE_LINE_CLEAR_M = 0.40   # ... or the side lot lines
LOW_CLEAR_M = 0.45         # from a stoop, fence, pier or coping
PAVED_CLEAR_M = 0.35       # from a walk
MIN_YARD_M = 1.6           # a house nearer its lot line than this has no front yard to plant

# What the pictures show, lot by lot (see the module doc).
PICTURED = {
    "prairie_1729": {
        "sources": ["loc_det_4a08065_pullman_residence", "loc_det_4a08066_pullman_residence"],
        "pictures": ["a16-pullman-det-4a08065", "a16-pullman-det-4a08066"],
        "creeper": {"faces": ["street"], "cover": 0.7, "height_m": [3.5, 7.5], "grade": "attested",
                    "note": "Ivy over the west front and the porch, to about the second storey's sills and "
                            "past them on the porch's piers (both Detroit Publishing views)."},
        "border": {"edge": "high_s", "d_m": [18.0, 62.0], "inset_m": 1.1, "grade": "attested",
                   "note": "A dense border of shrubs inside the coping along 18th Street, east of the house "
                           "(LC-D4-4a08066, right of the house)."},
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

# The shrubs a lot is planted from. A form is a shape and a habit, not a species claim.
FORMS = {
    "clipped": {"name": "clipped evergreen", "r": [0.35, 0.55], "h": [0.6, 1.0],
                "note": "a sheared, rounded foundation shrub (box, yew or arborvitae kept low)"},
    "mound": {"name": "flowering shrub", "r": [0.5, 0.8], "h": [0.8, 1.5],
              "note": "a loose deciduous mound (spiraea, hydrangea, snowball, barberry)"},
    "tall": {"name": "tall shrub", "r": [0.7, 1.0], "h": [1.7, 2.5],
             "note": "a lilac or syringa grown up at a corner of the house"},
}
BEDS = {"round": "a round bed cut in the lawn", "oval": "an oval bed", "border": "a narrow strip bed"}
SCHEMES = [   # each lot takes one: which forms it is planted from, and their shares
    {"clipped": 0.75, "mound": 0.2, "tall": 0.05},
    {"clipped": 0.35, "mound": 0.55, "tall": 0.1},
    {"clipped": 0.1, "mound": 0.75, "tall": 0.15},
    {"clipped": 1.0},
    {"mound": 0.85, "tall": 0.15},
]


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

    def lay_triangles(self, mask, tri_en):
        """Every triangle's plan projection, sampled finer than a cell."""
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
            self.mark(mask, pts.reshape(-1, 2))

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
            if any(name.startswith(m) for m in DOOR_MATS):
                low_door = lo < 1.0 + float(np.median(lo)) if len(lo) else False
                sel = (lo < 2.5) & low_door
                if sel.any():
                    pts = tri[sel].reshape(-1, 2)
                    # one door per structure at its lowest leaves' middle; a draft has one front door
                    for cl in cluster(pts, 2.0):
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


def plant_lot(p, plan: Plan, house, low, paved, sids):
    fr = lot_frame(p)
    if fr is None:
        return None
    A, su, nu, width = fr
    poly = np.asarray(p["polygon_local_m"], float)
    e0, n0 = poly.min(axis=0) - 1.0
    e1, n1 = poly.max(axis=0) + 1.0
    c0, r0 = max(int((e0 - plan.e0) / RES), 0), max(int((n0 - plan.n0) / RES), 0)
    c1, r1 = min(int((e1 - plan.e0) / RES) + 1, plan.w), min(int((n1 - plan.n0) / RES) + 1, plan.h)
    rr, cc = np.mgrid[r0:r1, c0:c1]
    pe, pn = plan.centre(rr, cc)
    s = (pe - A[0]) * su[0] + (pn - A[1]) * su[1]
    d = (pe - A[0]) * nu[0] + (pn - A[1]) * nu[1]
    inlot = inside(pe, pn, poly)
    H = house[r0:r1, c0:c1] & inlot
    if not H.any():
        return None
    # the house front: the nearest house cell to the street line, column by column
    d_house = np.where(H, d, np.inf)
    front = float(d_house.min())
    if front < MIN_YARD_M or front > 30:
        return None
    rng = random.Random(seed_of(p["id"]))

    # the door line(s): every door of a structure on this lot within the front's reach
    corridor = np.zeros(H.shape, bool)
    doors = []
    for de, dn, sid in plan.doors:
        if sid not in sids:
            continue
        ds = (de - A[0]) * su[0] + (dn - A[1]) * su[1]
        dd = (de - A[0]) * nu[0] + (dn - A[1]) * nu[1]
        if not (-0.5 <= ds <= width + 0.5) or dd > front + 8.0:
            continue
        doors.append((r2(ds), r2(dd)))
        corridor |= (np.abs(s - ds) <= DOOR_CLEAR_M) & (d <= dd + 0.5) & (d >= -1)

    dist_house = ndimage.distance_transform_edt(~H) * RES
    dist_low = ndimage.distance_transform_edt(~(low[r0:r1, c0:c1])) * RES
    dist_paved = ndimage.distance_transform_edt(~(paved[r0:r1, c0:c1] | corridor)) * RES
    reach = front + SIDE_REACH_M
    usable = (inlot & ~H & (d >= LOT_LINE_CLEAR_M) & (s >= SIDE_LINE_CLEAR_M) & (s <= width - SIDE_LINE_CLEAR_M)
              & (dist_low >= LOW_CLEAR_M) & (dist_paved >= PAVED_CLEAR_M) & (d <= reach))

    def world(i):
        return r2(pe.flat[i]), r2(pn.flat[i])

    scheme = rng.choice(SCHEMES)
    forms = list(scheme)
    weights = [scheme[f] for f in forms]
    spacing = rng.uniform(1.0, 1.55)
    shrubs = []
    taken = []

    def free_of(e, n, gap):
        return all(math.hypot(e - x, n - y) >= gap for x, y in taken)

    # foundation shrubs: cells hugging the house, front first, then the sides' first metres
    band = usable & (dist_house >= SHRUB_WALL_M[0]) & (dist_house <= SHRUB_WALL_M[1])
    idx = np.flatnonzero(band)
    order = sorted(idx, key=lambda i: (d.flat[i] > front + 0.9, rng.random()))
    gaps = rng.random() < 0.35   # some lots plant in clumps with lawn between them
    for i in order:
        e, n = world(i)
        if not free_of(e, n, spacing):
            continue
        if gaps and rng.random() < 0.3:
            taken.append((e, n))
            continue
        f = rng.choices(forms, weights)[0]
        if f == "tall" and d.flat[i] < front - 0.2:
            f = "mound"   # a lilac at a corner or a side, not across a front's windows
        spec = FORMS[f]
        shrubs.append([e, n, r2(rng.uniform(*spec["r"])), r2(rng.uniform(*spec["h"])), f,
                       r2(rng.uniform(0, 1))])
        taken.append((e, n))

    # a pictured border (Pullman's along 18th Street)
    pic = PICTURED.get(p["id"], {})
    if "border" in pic:
        bd = pic["border"]
        edge_s = bd["inset_m"] if bd["edge"] == "low_s" else width - bd["inset_m"]
        dd = bd["d_m"][0]
        while dd <= bd["d_m"][1]:
            e = A[0] + su[0] * edge_s + nu[0] * dd
            n = A[1] + su[1] * edge_s + nu[1] * dd
            r, c = int((n - plan.n0) / RES) - r0, int((e - plan.e0) / RES) - c0
            if 0 <= r < H.shape[0] and 0 <= c < H.shape[1] and not H[r, c] and dist_low[r, c] >= 0.3 \
                    and dist_paved[r, c] >= PAVED_CLEAR_M:
                f = "mound" if rng.random() < 0.7 else "tall"
                shrubs.append([r2(e), r2(n), r2(rng.uniform(0.6, 0.85)), r2(rng.uniform(1.3, 2.1)), f,
                               r2(rng.uniform(0, 1)), "attested"])
                taken.append((r2(e), r2(n)))
            dd += rng.uniform(1.0, 1.3)

    # low beds in the lawn before the house
    beds = []
    area = float((usable & (d < front)).sum()) * RES * RES
    want = 0 if area < 14 else min(3, 1 + int(area // 45))
    if want and rng.random() < 0.15:
        want -= 1
    open_lawn = usable & (d < front - 1.0) & (d >= 1.4)
    clear = ndimage.distance_transform_edt(open_lawn) * RES
    for _ in range(want):
        kind = rng.choice(["round", "round", "oval", "border"])
        a_ = rng.uniform(0.7, 1.15) if kind != "border" else rng.uniform(1.6, 2.6)
        b_ = a_ if kind == "round" else (a_ * rng.uniform(0.55, 0.75) if kind == "oval" else rng.uniform(0.35, 0.5))
        need = (a_ if kind == "round" else max(a_, b_)) + 0.35
        cand = np.flatnonzero(clear >= need)
        cand = [i for i in cand if free_of(*world(i), need + 0.5)]
        if not cand:
            break
        i = rng.choice(cand)
        e, n = world(i)
        # a strip bed lies along the front; the others square to the lot
        heading = math.degrees(math.atan2(su[0], su[1]))
        beds.append([e, n, r2(a_), r2(b_), r2(heading % 360), kind, rng.randrange(4)])
        taken.append((e, n))
        yy, xx = np.ogrid[:clear.shape[0], :clear.shape[1]]
        rr_, cc_ = np.unravel_index(i, clear.shape)
        clear[(yy - rr_) ** 2 + (xx - cc_) ** 2 <= ((need + 0.6) / RES) ** 2] = 0

    # creeper on the walls a picture shows it on
    creeper = []
    if "creeper" in pic:
        cr = pic["creeper"]
        # a wall that faces the street: the house stands just behind the cell, into the lot
        sh = int(round(0.5 / RES))
        behind = ndimage.shift(H.astype(np.uint8), (-nu[1] * sh, -nu[0] * sh), order=0, cval=0) > 0
        hug = (inlot & ~H & (dist_house <= 0.3) & behind & (d < front + 6.0) & (dist_paved >= 0.2)
               & (dist_low >= 0.15))
        cand = list(np.flatnonzero(hug))
        rng.shuffle(cand)
        cand.sort(key=lambda i: s.flat[i])
        last = -9.0
        for i in cand:
            if s.flat[i] - last < 0.9:
                continue
            last = s.flat[i]
            if rng.random() > cr["cover"]:
                continue
            e, n = world(i)
            creeper.append([e, n, r2(math.degrees(math.atan2(-nu[0], -nu[1])) % 360),
                            r2(rng.uniform(1.2, 1.9)), r2(rng.uniform(*cr["height_m"]))])

    grade = "reconstructed"
    return {
        "parcel": p["id"], "street": p["street"], "side": p.get("side"),
        "addresses": p.get("addresses_1911", []),
        "frame": {"origin": [r2(A[0]), r2(A[1])], "along": [round(float(su[0]), 5), round(float(su[1]), 5)],
                  "into": [round(float(nu[0]), 5), round(float(nu[1]), 5)], "width_m": r2(width)},
        "front_m": r2(front), "doors": doors, "scheme": SCHEMES.index(scheme),
        "grade": grade, "shrubs": shrubs, "beds": beds, "creeper": creeper,
        **({"pictured": {k: v for k, v in pic.items() if k in ("sources", "pictures")},
            "pictured_notes": {k: {"grade": v["grade"], "note": v["note"]} for k, v in pic.items()
                               if isinstance(v, dict) and "grade" in v}} if pic else {}),
    }


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
        lot = plant_lot(p, plan, house, plan.low, plan.paved, by_parcel.get(p["id"], set()))
        if lot:
            lots.append(lot)
    lots.sort(key=lambda l: l["parcel"])
    summary = {
        "lots": len(lots),
        "shrubs": sum(len(l["shrubs"]) for l in lots),
        "beds": sum(len(l["beds"]) for l in lots),
        "creeper_patches": sum(len(l["creeper"]) for l in lots),
        "attested_shrubs": sum(1 for l in lots for s in l["shrubs"] if len(s) > 6),
        "lots_with_a_door_line": sum(1 for l in lots if l["doors"]),
    }
    return {
        "_doc": "The 1904 district's front yards (T-3203): foundation shrubs along each house lot's front "
                "and the first metres of its sides, low beds in the lawn before the house, and creeper where a "
                "picture shows it. GENERATED by "
                "tools/plant_prairie_1904_front_yards.py from data/street_grid/1904.json, the 1904 "
                "sidecars' baked models and the traced Sanborn footprints -- do not hand-edit; re-run the "
                "tool. Local ENU metres of data/datum.json. shrubs: [e, n, radius_m, height_m, form, tone, "
                "(grade if not the lot's)]; beds: [e, n, half_length_m, half_width_m, heading_deg, kind, "
                "palette]; creeper: [e, n, facing_deg, width_m, height_m]. The lawn is the ground's own sward.",
        "scene": "1904", "target_date": "1904-07-01", "ticket": "T-3203",
        "generated_by": "tools/plant_prairie_1904_front_yards.py",
        "liberty": LIBERTY,
        "forms": FORMS, "beds": BEDS,
        "placement": {
            "raster_m": RES, "shrub_wall_m": list(SHRUB_WALL_M), "side_reach_m": SIDE_REACH_M,
            "lot_line_clear_m": LOT_LINE_CLEAR_M, "door_clear_m": DOOR_CLEAR_M, "low_clear_m": LOW_CLEAR_M,
            "paved_clear_m": PAVED_CLEAR_M, "min_yard_m": MIN_YARD_M,
            "note": "Shrubs stand 0.45-0.95 m off the house's walls, clear of the lot line, its boundary, every "
                    "stoop, pier and paved walk, and of a 2.7 m way from each front door straight to the lot "
                    "line; beds stand in the open lawn before the house. Seeded by the parcel's id.",
        },
        "summary": summary,
        "lots": lots,
    }


def collisions(data, laid) -> list[str]:
    """Every planting the committed file lays that now stands on something built: in a house,
    on a stoop, fence, pier or walk, or across a door's way. A rebake that moves a stoop or a
    walk under a shrub is what this catches; one that moves nothing a yard touches is not."""
    grid, parcels, plan, house, by_parcel = laid
    near_low = ndimage.distance_transform_edt(~plan.low) * RES
    near_paved = ndimage.distance_transform_edt(~plan.paved) * RES
    out = []

    def cell(e, n):
        r, c = int((n - plan.n0) / RES), int((e - plan.e0) / RES)
        return (r, c) if 0 <= r < plan.h and 0 <= c < plan.w else None

    for lot in data["lots"]:
        A = np.array(lot["frame"]["origin"]); su = np.array(lot["frame"]["along"]); nu = np.array(lot["frame"]["into"])
        doors = []
        for de, dn, sid in plan.doors:
            if sid in by_parcel.get(lot["parcel"], set()):
                ds = (de - A[0]) * su[0] + (dn - A[1]) * su[1]
                dd = (de - A[0]) * nu[0] + (dn - A[1]) * nu[1]
                if -0.5 <= ds <= lot["frame"]["width_m"] + 0.5 and dd <= lot["front_m"] + 8.0:
                    doors.append((ds, dd))
        things = [("shrub", s[0], s[1], 0.0) for s in lot["shrubs"]] + \
                 [("bed", b[0], b[1], min(b[2], b[3]) * 0.5) for b in lot["beds"]]
        for kind, e, n, pad in things:
            rc = cell(e, n)
            if rc is None:
                continue
            ds = (e - A[0]) * su[0] + (n - A[1]) * su[1]
            dd = (e - A[0]) * nu[0] + (n - A[1]) * nu[1]
            why = None
            if house[rc]:
                why = "inside a house"
            elif near_low[rc] < 0.25 + pad:
                why = "on a stoop, fence, pier or coping"
            elif near_paved[rc] < 0.15 + pad:
                why = "on a paved walk"
            elif any(abs(ds - x) < DOOR_CLEAR_M - 0.3 and dd <= y for x, y in doors):
                why = "across the way to a front door"
            if why:
                out.append(f"{lot['parcel']}: a {kind} at {e:.2f} E, {n:.2f} N stands {why}")
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    laid = lay_district()
    data = build(laid)
    text = json.dumps(data, indent=1, ensure_ascii=False) + "\n"
    if args.check:
        # THE CHECK ASKS TWO QUESTIONS, because the yards stand on the baked houses, and every
        # house ticket rebakes one. Byte for byte is the first: the committed file is what the
        # tool writes. When it is not, the file is held to what matters instead, that no
        # planting it lays stands in a house, on a stoop, fence or walk, or across a door's
        # way, against the models as they stand now; so a rebake that moves nothing a yard
        # touches does not turn the gate red, and one that does says what moved.
        if not OUT.exists():
            print(f"{OUT.relative_to(ROOT)} is missing: run tools/plant_prairie_1904_front_yards.py", file=sys.stderr)
            return 1
        if OUT.read_text() == text:
            print(f"front yards: {OUT.relative_to(ROOT)} is what the tool writes ({data['summary']})")
            return 0
        bad = collisions(json.loads(OUT.read_text()), laid)
        if bad:
            for line in bad[:20]:
                print(f"  {line}", file=sys.stderr)
            print(f"{OUT.relative_to(ROOT)}: {len(bad)} planting(s) now stand on something built: "
                  "re-run tools/plant_prairie_1904_front_yards.py", file=sys.stderr)
            return 1
        print(f"front yards: {OUT.relative_to(ROOT)} is behind the models (a house was rebaked since), "
              "and every planting still clears what is built; re-run the tool to refresh it")
        return 0
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text)
    print(f"wrote {OUT.relative_to(ROOT)}: {data['summary']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
