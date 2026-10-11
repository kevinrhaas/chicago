"""The Prairie Avenue district draft: a serviceable house from a record, in pure Python (T-2329).

The owner's district pass (2026-10-08) asks for every frontage of Prairie Avenue to stand
as a believable draft — complete from the street, both walks, the alley and the air —
that the per-building tickets then REFINE in place. This module is that draft's builder.
It reads one `prairie_draft` record (written by `tools/draft_prairie_1904.py`, which
fits the record's rectangles inside the traced Sanborn parts and applies the draft rules
of `data/components/prairie_1904/draft_prairie_1904.json`) and writes one GLB.

  walls      every plan rectangle is a closed block from grade to its eave, in the
             fabric its construction names; a stone front is the street face only,
             over a stone basement course that runs round the whole building
  roofs      the main body takes its family's roof — hip, steep hip, mansard (a 72
             degree lower face to a curb, an 18 degree deck above it, dormers in the
             lower face), shaped gable (a stepped street gable above a ridge running
             back from the street) or flat behind a cornice; smaller pieces take a hip
             or a flat roof with a cornice
  openings   every storey of every exposed wall carries sash in a sill, a lintel and a
             meeting rail, at the family's bay count on the street front and a spacing
             on the others; a wall within 0.9 m of a lot line is a party wall and is
             left blind; the street front has its door, transom, stoop and area lights
  features   corner tower, front bay, porch, dormers, chimneys and string courses where
             the record names them

WHY NOT K01: `k01_frontage` builds one rectangle, one hip roof and one stone street
front, to the K01 metric contract, and refuses anything else (k01_frontage_params). A
district of mansards, shaped gables, turrets and L-shaped plans needs a coarser builder
that takes all of them; the per-building tickets replace this one house at a time.

Every solid is a closed box, prism or roof polyhedron; each face is wound counter-
clockwise seen from outside (checked against the solid's centre, so authoring order
cannot flip one). Coordinates are authored as (u, v, y) — u along the lot toward the
street, v along the street front, y up — and written to glTF as (u, y, -v), the
contract's footprint mapping (docs/GLB-CONTRACT.md).
"""

from __future__ import annotations

import hashlib
import json
import math
import struct

GENERATOR = "4d-chicago prairie_draft (T-2329)"

#: Flat colours, linear RGB, and roughness. A draft carries no texture: the per-building
#: tickets lay the K02-K04 libraries; this one only has to read as the right fabric.
MATERIALS = {
    "brick":  {"color": (0.30, 0.125, 0.085), "roughness": 0.9},
    "stone":  {"color": (0.40, 0.36, 0.29), "roughness": 0.85},
    "brownstone": {"color": (0.21, 0.13, 0.10), "roughness": 0.85},
    "frame":  {"color": (0.52, 0.48, 0.38), "roughness": 0.8},
    "trim":   {"color": (0.56, 0.53, 0.46), "roughness": 0.8},
    "cornice": {"color": (0.24, 0.22, 0.20), "roughness": 0.7},
    "roof":   {"color": (0.13, 0.14, 0.17), "roughness": 0.75},
    "glass":  {"color": (0.05, 0.06, 0.07), "roughness": 0.15, "metallic": 0.1},
    "door":   {"color": (0.18, 0.10, 0.06), "roughness": 0.6},
}
ORDER = tuple(MATERIALS)


def seed_rng(seed: int):
    """A small deterministic stream of floats in [0, 1) from the record's seed."""
    state = [seed & 0xFFFFFFFF or 1]

    def nxt() -> float:
        x = state[0]
        x ^= (x << 13) & 0xFFFFFFFF
        x ^= x >> 17
        x ^= (x << 5) & 0xFFFFFFFF
        state[0] = x & 0xFFFFFFFF
        return state[0] / 2 ** 32
    return nxt


# ---------------------------------------------------------------- mesh accumulation

def _sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def _dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _unit(a):
    n = math.sqrt(_dot(a, a))
    return (a[0] / n, a[1] / n, a[2] / n) if n > 1e-12 else (0.0, 0.0, 1.0)


class Mesh:
    """One primitive per material; flat-shaded faces, each with its own vertices."""

    def __init__(self, conf: float):
        self.conf = conf
        self.prims = {m: {"pos": [], "nrm": [], "uv": [], "idx": []} for m in ORDER}

    def face(self, mat: str, pts, centre=None):
        """A planar convex polygon (u, v, y), wound outward from `centre` if given."""
        n = (0.0, 0.0, 0.0)
        for i in range(len(pts)):
            a, b = pts[i], pts[(i + 1) % len(pts)]
            n = (n[0] + (a[1] - b[1]) * (a[2] + b[2]), n[1] + (a[2] - b[2]) * (a[0] + b[0]),
                 n[2] + (a[0] - b[0]) * (a[1] + b[1]))
        if _dot(n, n) < 1e-14:
            return
        n = _unit(n)
        if centre is not None:
            c = tuple(sum(p[k] for p in pts) / len(pts) for k in range(3))
            if _dot(n, _sub(c, centre)) < 0:
                pts = list(reversed(pts))
                n = (-n[0], -n[1], -n[2])
        t1 = _unit(_sub(pts[1], pts[0]))
        t2 = _cross(n, t1)
        pr = self.prims[mat]
        base = len(pr["pos"])
        for p in pts:
            # glTF: x = u, y = y, z = -v
            pr["pos"].append((p[0], p[2], -p[1]))
            pr["nrm"].append((n[0], n[2], -n[1]))
            pr["uv"].append((_dot(p, t1) * 0.5, _dot(p, t2) * 0.5))
        for i in range(1, len(pts) - 1):
            pr["idx"] += [base, base + i, base + i + 1]

    def solid(self, faces, mat_of=None, mat="brick"):
        """A closed solid: every face wound away from the solid's vertex centre."""
        allp = [p for f in faces for p in f]
        c = tuple(sum(p[k] for p in allp) / len(allp) for k in range(3))
        for i, f in enumerate(faces):
            self.face(mat_of(i) if mat_of else mat, f, c)

    def box(self, mat, u0, u1, v0, v1, y0, y1, side_mats=None):
        """An axis-aligned block; `side_mats` maps 'u0','u1','v0','v1','top','bottom'."""
        if u1 - u0 < 1e-6 or v1 - v0 < 1e-6 or y1 - y0 < 1e-6:
            return
        P = lambda u, v, y: (u, v, y)  # noqa: E731
        faces = {
            "bottom": [P(u0, v0, y0), P(u1, v0, y0), P(u1, v1, y0), P(u0, v1, y0)],
            "top": [P(u0, v0, y1), P(u1, v0, y1), P(u1, v1, y1), P(u0, v1, y1)],
            "u0": [P(u0, v0, y0), P(u0, v1, y0), P(u0, v1, y1), P(u0, v0, y1)],
            "u1": [P(u1, v0, y0), P(u1, v1, y0), P(u1, v1, y1), P(u1, v0, y1)],
            "v0": [P(u0, v0, y0), P(u1, v0, y0), P(u1, v0, y1), P(u0, v0, y1)],
            "v1": [P(u0, v1, y0), P(u1, v1, y0), P(u1, v1, y1), P(u0, v1, y1)],
        }
        c = ((u0 + u1) / 2, (v0 + v1) / 2, (y0 + y1) / 2)
        for k, f in faces.items():
            self.face((side_mats or {}).get(k, mat), f, c)

    def triangles(self) -> int:
        return sum(len(p["idx"]) // 3 for p in self.prims.values())


# ---------------------------------------------------------------- roofs

def hip(m: Mesh, mat, u0, u1, v0, v1, y, pitch, o=0.35, soffit="cornice"):
    """A hipped roof over a rectangle, eaves `o` past the walls; ridge on the long axis."""
    u0, u1, v0, v1 = u0 - o, u1 + o, v0 - o, v1 + o
    du, dv = u1 - u0, v1 - v0
    t = math.tan(math.radians(pitch))
    if du >= dv:
        h = dv / 2 * t
        a, b = (u0 + dv / 2, (v0 + v1) / 2, y + h), (u1 - dv / 2, (v0 + v1) / 2, y + h)
    else:
        h = du / 2 * t
        a, b = ((u0 + u1) / 2, v0 + du / 2, y + h), ((u0 + u1) / 2, v1 - du / 2, y + h)
    c0, c1, c2, c3 = (u0, v0, y), (u1, v0, y), (u1, v1, y), (u0, v1, y)
    cen = ((u0 + u1) / 2, (v0 + v1) / 2, y + h / 3)
    if du >= dv:
        faces = [[c0, c1, b, a], [c2, c3, a, b], [c1, c2, b], [c3, c0, a]]
    else:
        faces = [[c1, c2, b, a], [c3, c0, a, b], [c0, c1, a], [c2, c3, b]]
    for f in faces:
        m.face(mat, f, cen)
    m.face(soffit, [c0, c1, c2, c3], cen)
    return y + h


def gable(m: Mesh, mat, u0, u1, v0, v1, y, pitch, along="u", o=0.3, end_mat="brick", verge=0.12):
    """A gabled roof with its ridge `along` u or v, and the two gable walls closed."""
    t = math.tan(math.radians(pitch))
    if along == "u":
        h = (v1 - v0) / 2 * t
        vm = (v0 + v1) / 2
        e0, e1 = v0 - o, v1 + o
        dy = o * t
        U0, U1 = u0 - verge, u1 + verge
        r0, r1 = (U0, vm, y + h), (U1, vm, y + h)
        cen = ((u0 + u1) / 2, vm, y + h / 3)
        m.face(mat, [(U0, e0, y - dy), (U1, e0, y - dy), r1, r0], cen)
        m.face(mat, [(U1, e1, y - dy), (U0, e1, y - dy), r0, r1], cen)
        m.face("cornice", [(U0, e0, y - dy), (U1, e0, y - dy), (U1, e1, y - dy), (U0, e1, y - dy)], cen)
        for U in (U0, U1):    # the gable ends, in the wall's fabric, a verge's width proud
            m.face(end_mat, [(U, e0, y - dy), (U, e1, y - dy), (U, vm, y + h)], cen)
    else:
        h = (u1 - u0) / 2 * t
        um = (u0 + u1) / 2
        e0, e1 = u0 - o, u1 + o
        dy = o * t
        V0, V1 = v0 - verge, v1 + verge
        r0, r1 = (um, V0, y + h), (um, V1, y + h)
        cen = (um, (v0 + v1) / 2, y + h / 3)
        m.face(mat, [(e0, V0, y - dy), (e0, V1, y - dy), r1, r0], cen)
        m.face(mat, [(e1, V1, y - dy), (e1, V0, y - dy), r0, r1], cen)
        m.face("cornice", [(e0, V0, y - dy), (e1, V0, y - dy), (e1, V1, y - dy), (e0, V1, y - dy)], cen)
        for V in (V0, V1):
            m.face(end_mat, [(e0, V, y - dy), (e1, V, y - dy), (um, V, y + h)], cen)
    return y + h


def mansard(m: Mesh, u0, u1, v0, v1, y, lower_h, lower_pitch=72.0, upper_pitch=18.0, o=0.3):
    """Mansard: a steep lower face from the eave to a curb, a low hip above it."""
    U0, U1, V0, V1 = u0 - o, u1 + o, v0 - o, v1 + o
    d = lower_h / math.tan(math.radians(lower_pitch))
    a0, a1, b0, b1 = U0 + d, U1 - d, V0 + d, V1 - d
    cen = ((u0 + u1) / 2, (v0 + v1) / 2, y + lower_h / 2)
    lo = [(U0, V0, y), (U1, V0, y), (U1, V1, y), (U0, V1, y)]
    hi = [(a0, b0, y + lower_h), (a1, b0, y + lower_h), (a1, b1, y + lower_h), (a0, b1, y + lower_h)]
    for i in range(4):
        m.face("roof", [lo[i], lo[(i + 1) % 4], hi[(i + 1) % 4], hi[i]], cen)
    m.face("cornice", lo, cen)
    # the curb: a thin moulded band round the break, then the deck
    m.box("cornice", a0 - 0.08, a1 + 0.08, b0 - 0.08, b1 + 0.08, y + lower_h - 0.05, y + lower_h + 0.12)
    top = hip(m, "roof", a0, a1, b0, b1, y + lower_h + 0.12, upper_pitch, o=0.0)
    return (a0, a1, b0, b1, d), top


def dormer_on_face(m: Mesh, side, s, y_sill, w, h, face_coord, slope_out, pitch_cap=45.0):
    """A dormer standing out of a roof face: a box, its sash and a small gabled cap.

    `side` is the wall it faces ('u1' street, 'u0' rear, 'v0', 'v1'); `s` its centre along
    that face; `face_coord` where its front stands; `slope_out` how far back it runs."""
    sign = 1 if side in ("u1", "v1") else -1
    f, b = face_coord, face_coord - sign * slope_out
    lo, hi = min(f, b), max(f, b)
    if side in ("u1", "u0"):
        m.box("cornice", lo, hi, s - w / 2, s + w / 2, y_sill - 0.2, y_sill + h + 0.25)
        gable(m, "roof", lo, hi, s - w / 2, s + w / 2, y_sill + h + 0.25, pitch_cap, along="u", o=0.12,
              end_mat="cornice", verge=0.0)
        g0 = f + sign * 0.02
        m.box("glass", min(f, g0), max(f, g0), s - w / 2 + 0.15, s + w / 2 - 0.15, y_sill, y_sill + h)
    else:
        m.box("cornice", s - w / 2, s + w / 2, lo, hi, y_sill - 0.2, y_sill + h + 0.25)
        gable(m, "roof", s - w / 2, s + w / 2, lo, hi, y_sill + h + 0.25, pitch_cap, along="v", o=0.12,
              end_mat="cornice", verge=0.0)
        g0 = f + sign * 0.02
        m.box("glass", s - w / 2 + 0.15, s + w / 2 - 0.15, min(f, g0), max(f, g0), y_sill, y_sill + h)


def prism(m: Mesh, mat, ring, y0, y1):
    cen = (sum(p[0] for p in ring) / len(ring), sum(p[1] for p in ring) / len(ring), (y0 + y1) / 2)
    n = len(ring)
    for i in range(n):
        a, b = ring[i], ring[(i + 1) % n]
        m.face(mat, [(a[0], a[1], y0), (b[0], b[1], y0), (b[0], b[1], y1), (a[0], a[1], y1)], cen)
    m.face(mat, [(p[0], p[1], y0) for p in ring], cen)
    m.face(mat, [(p[0], p[1], y1) for p in ring], cen)


def cone(m: Mesh, mat, ring, y0, apex_y):
    cu = sum(p[0] for p in ring) / len(ring)
    cv = sum(p[1] for p in ring) / len(ring)
    cen = (cu, cv, y0 + (apex_y - y0) / 4)
    n = len(ring)
    for i in range(n):
        a, b = ring[i], ring[(i + 1) % n]
        m.face(mat, [(a[0], a[1], y0), (b[0], b[1], y0), (cu, cv, apex_y)], cen)
    m.face("cornice", [(p[0], p[1], y0) for p in ring], cen)


# ---------------------------------------------------------------- walls and openings

def _wall_faces(r):
    u0, v0, u1, v1 = r
    return {"u1": (u1, v0, v1), "u0": (u0, v0, v1), "v1": (v1, u0, u1), "v0": (v0, u0, u1)}


def _covered(side, at, a, b, rects, me, pad=0.25):
    """Is the stretch of this wall at its middle inside another rectangle of the building?"""
    mid = (a + b) / 2
    for i, r in enumerate(rects):
        if i == me:
            continue
        u0, v0, u1, v1 = r
        if side in ("u0", "u1"):
            if u0 - pad <= at <= u1 + pad and v0 + pad < mid < v1 - pad:
                return True
        else:
            if v0 - pad <= at <= v1 + pad and u0 + pad < mid < u1 - pad:
                return True
    return False


def window(m: Mesh, side, at, s, sill, w, h, proud=0.03, trim="trim"):
    """A sash on a wall: glass, a meeting rail, a sill below and a lintel above."""
    sign = 1 if side in ("u1", "v1") else -1
    a, b = sorted((at, at + sign * proud))
    sa, sb = sorted((at, at + sign * 0.09))
    la, lb = sorted((at, at + sign * 0.06))
    if side in ("u0", "u1"):
        m.box("glass", a, b, s - w / 2, s + w / 2, sill, sill + h)
        m.box(trim, a, b + 0.005 if sign > 0 else b, s - w / 2, s + w / 2, sill + h * 0.52, sill + h * 0.52 + 0.05)
        m.box(trim, sa, sb, s - w / 2 - 0.08, s + w / 2 + 0.08, sill - 0.08, sill)
        m.box(trim, la, lb, s - w / 2 - 0.1, s + w / 2 + 0.1, sill + h, sill + h + 0.22)
    else:
        m.box("glass", s - w / 2, s + w / 2, a, b, sill, sill + h)
        m.box(trim, s - w / 2, s + w / 2, a, b + 0.005 if sign > 0 else b, sill + h * 0.52, sill + h * 0.52 + 0.05)
        m.box(trim, s - w / 2 - 0.08, s + w / 2 + 0.08, sa, sb, sill - 0.08, sill)
        m.box(trim, s - w / 2 - 0.1, s + w / 2 + 0.1, la, lb, sill + h, sill + h + 0.22)


def _spread(a, b, n, margin):
    """`n` centres evenly spread on [a, b] past `margin` at each end."""
    if n <= 0:
        return []
    a, b = a + margin, b - margin
    step = (b - a) / n
    return [a + step * (k + 0.5) for k in range(n)]


# ---------------------------------------------------------------- the building

def build(params, structure_id: str):
    """The draft's Mesh and its measured facts."""
    e, plan = params.elevation, params.plan
    conf = params.worst_conf("draft_plan", "draft_elevation", "stories", "construction")
    m = Mesh(conf)
    rnd = seed_rng(int(e["seed"]))
    stone = e.get("stone", "stone")
    con = params.construction
    wall_main = {"brick": "brick", "stone": stone, "frame": "frame",
                 "brick_with_stone_front": "brick", "stone_with_brick_rear": stone}[con]
    front_mat = stone if con in ("stone", "brick_with_stone_front", "stone_with_brick_rear") else wall_main
    wall_range = "brick" if con in ("brick_with_stone_front", "stone_with_brick_rear") else wall_main
    lot_v0, lot_v1 = plan["lot_v"]
    yard_u = plan["street_u"]
    parts = plan["parts"]
    rects = [tuple(p["rect"]) for p in parts]
    pf = float(e.get("principal_floor_m", 0.0))
    hs = [float(x) for x in e["storey_heights_m"]]
    party = float(e.get("party_wall_gap_m", 0.9))
    windows = doors = 0
    facts = {"parts": len(parts)}

    def eave_of(p):
        n = int(p.get("storeys", params.stories))
        return pf + sum(hs[:n]) if n <= len(hs) else pf + sum(hs) + (n - len(hs)) * hs[-1]

    main = parts[0]
    mu0, mv0, mu1, mv1 = main["rect"]
    main_eave = eave_of(main)
    is_house = params.kind == "house"

    for i, p in enumerate(parts):
        u0, v0, u1, v1 = p["rect"]
        role = p["role"]
        if role == "porch":
            deck = pf if is_house else 0.3
            m.box("trim", u0, u1, v0, v1, max(0.0, deck - 0.25), deck)
            top = deck + 3.0
            for (pu, pv) in ((u0 + 0.15, v0 + 0.15), (u1 - 0.15, v0 + 0.15), (u0 + 0.15, v1 - 0.15), (u1 - 0.15, v1 - 0.15)):
                m.box("trim", pu - 0.11, pu + 0.11, pv - 0.11, pv + 0.11, deck, top)
            m.box("cornice", u0 - 0.15, u1 + 0.15, v0 - 0.15, v1 + 0.15, top, top + 0.3)
            m.box("roof", u0 - 0.1, u1 + 0.1, v0 - 0.1, v1 + 0.1, top + 0.3, top + 0.38)
            continue
        eave = eave_of(p)
        mat = wall_range if role in ("range",) else wall_main
        sides = {}
        if role in ("main", "wing", "bay", "stone_front") and is_house:
            sides["u1"] = front_mat
        m.box(mat, u0, u1, v0, v1, 0.0, eave, side_mats=sides)
        if is_house:
            # the basement course: stone round the whole building to the principal floor
            m.box(stone, u0 - 0.04, u1 + 0.04, v0 - 0.04, v1 + 0.04,
                  0.0, max(0.3, pf - 0.15))
        n_st = int(p.get("storeys", params.stories))
        # string courses on the street faces of the body
        if is_house and role in ("main", "wing", "bay", "stone_front"):
            y = pf
            for k in range(1, n_st):
                y += hs[min(k - 1, len(hs) - 1)]
                m.box("trim", u1, u1 + 0.06, v0 - 0.02, v1 + 0.02, y - 0.06, y + 0.08)
        # roof
        roof = p.get("roof", "flat")
        pitch = float(p.get("pitch_deg", e.get("roof_pitch_deg", 40)))
        if roof == "flat":
            c = 0.35 if role in ("main", "wing", "bay", "stone_front") else 0.2
            m.box("cornice", u0 - c, u1 + c, v0 - c, v1 + c, eave - 0.4, eave)
            m.box("roof", u0, u1, v0, v1, eave, eave + 0.06)
            if role in ("main", "stone_front") and is_house:
                m.box(front_mat, u1 - 0.3, u1, v0, v1, eave, eave + 0.7)
                m.box("cornice", u1 - 0.35, u1 + 0.05, v0 - 0.05, v1 + 0.05, eave + 0.7, eave + 0.8)
            if e.get("brackets") and role in ("main", "stone_front"):
                for s in _spread(v0, v1, max(2, round((v1 - v0) / 1.1)), 0.2):
                    m.box("cornice", u1, u1 + 0.32, s - 0.07, s + 0.07, eave - 0.85, eave - 0.4)
            top = eave + 0.06
        elif roof in ("hip", "hip_steep"):
            m.box("cornice", u0 - 0.12, u1 + 0.12, v0 - 0.12, v1 + 0.12, eave - 0.35, eave)
            top = hip(m, "roof", u0, u1, v0, v1, eave, pitch)
        elif roof == "gable":
            along = "u" if (u1 - u0) >= (v1 - v0) else "v"
            top = gable(m, "roof", u0, u1, v0, v1, eave, pitch, along=along, end_mat=mat)
        elif roof == "mansard":
            m.box("cornice", u0 - 0.35, u1 + 0.35, v0 - 0.35, v1 + 0.35, eave - 0.45, eave)
            lower = float(e.get("mansard_lower_m", 3.0))
            (a0, a1, b0, b1, d), top = mansard(m, u0, u1, v0, v1, eave, lower, o=0.35)
            if role == "main":
                facts["mansard_curb_m"] = round(eave + lower, 3)
                sill = eave + 0.55
                # dormers stand on the lower face's mid-line; a 72 degree face rises
                # 3.08 m per metre in, so the dormer front stands about a third of the
                # way in from the eave line
                out = d * 0.35
                for side, a_, b_ in (("u1", v0, v1), ("u0", v0, v1)):
                    n = max(1, round((b_ - a_) / 3.2)) if side == "u0" else int(e.get("front_bays", 3))
                    at = (u1 + 0.35 - out) if side == "u1" else (u0 - 0.35 + out)
                    for s in _spread(a_, b_, n, 0.9):
                        dormer_on_face(m, side, s, sill, 1.0, 1.6, at, d * 0.65 + 0.6)
                        windows += 1
        elif roof == "shaped_gable":
            # the ridge runs back from the street; the street gable is a stepped wall above it
            top = gable(m, "roof", u0, u1, v0, v1, eave, pitch, along="u", o=0.25, end_mat=mat, verge=0.0)
            w = v1 - v0
            vm = (v0 + v1) / 2
            rise = top - eave
            steps = [(1.0, 0.0), (0.78, 0.30), (0.56, 0.58), (0.34, 0.86)]
            for k, (frac, yk) in enumerate(steps):
                ya = eave + rise * yk
                yb = eave + rise * (steps[k + 1][1] if k + 1 < len(steps) else 1.0) + 0.35
                m.box(front_mat, u1 - 0.4, u1, vm - w * frac / 2, vm + w * frac / 2, ya, yb)
                m.box("trim", u1 - 0.45, u1 + 0.05, vm - w * frac / 2 - 0.05, vm + w * frac / 2 + 0.05, yb, yb + 0.12)
            m.box("trim", u1 - 0.3, u1 + 0.02, vm - 0.2, vm + 0.2, top + 0.47, top + 1.3)
            window(m, "u1", u1, vm, eave + 0.6, 1.4, 1.5)
            windows += 1
        else:
            top = eave
        if role == "main":
            facts["eave_m"] = round(eave, 3)
            facts["top_m"] = round(top, 3)
        # attic dormers on a hipped main body with a half storey
        if role == "main" and roof in ("hip", "hip_steep") and e.get("attic_dormers"):
            out = 1.2
            for s in _spread(v0, v1, int(e.get("front_bays", 3)) if (v1 - v0) > 7 else 1, 1.2):
                dormer_on_face(m, "u1", s, eave + 0.35, 1.0, 1.4, u1 + 0.35 - out * 0.5, out + 0.8)
                windows += 1

        # ---- openings on every exposed wall of this piece
        if role == "stone_front":
            continue
        for side, (at, a, b) in _wall_faces(p["rect"]).items():
            length = b - a
            if length < 1.6:
                continue
            if side == "v0" and at - lot_v0 < party:
                continue
            if side == "v1" and lot_v1 - at < party:
                continue
            if _covered(side, at, a, b, rects, i):
                continue
            front = side == "u1" and role in ("main", "wing", "bay") and is_house
            if front and role == "main":
                n = int(e.get("front_bays", 3))
            else:
                n = int(max(0, (length - 0.8) // float(e.get("side_spacing_m", 3.0))))
                if role == "bay":
                    n = max(1, int(length // 1.6))
            if n <= 0:
                continue
            centres = _spread(a, b, n, 0.5 if role != "main" else 0.7)
            door_s = None
            if front and role == "main":
                door_s = centres[-1] if e.get("entrance", "north") == "north" else (
                    centres[0] if e.get("entrance") == "south" else centres[len(centres) // 2])
            if not is_house and side == "u0":
                # the alley face: a carriage door in the middle, a loft door above it
                cs = (a + b) / 2
                cw = min(3.0, length - 1.2)
                sign = -1
                m.box("door", at - 0.05, at, cs - cw / 2, cs + cw / 2, 0.0, 3.0)
                m.box("trim", at - 0.12, at, cs - cw / 2 - 0.15, cs + cw / 2 + 0.15, 3.0, 3.25)
                if n_st >= 2:
                    m.box("door", at - 0.05, at, cs - 0.6, cs + 0.6, hs[0] + 0.3, hs[0] + 2.1)
                doors += 1
                centres = [c for c in centres if abs(c - cs) > cw / 2 + 0.8]
            for k in range(n_st):
                base = (pf if is_house else 0.0) + sum(hs[:k])
                hk = hs[min(k, len(hs) - 1)]
                wh = min(2.2, hk - 1.3) if is_house else min(1.4, hk - 1.4)
                ww = float(e.get("sash_width_m", 1.0)) if is_house else 0.8
                sill = base + (0.75 if is_house else 1.1)
                for s in centres:
                    if k == 0 and door_s is not None and s == door_s:
                        continue
                    window(m, side, at, s, sill, ww, wh)
                    windows += 1
            if front and role == "main" and door_s is not None:
                # door, transom and stoop
                m.box("door", u1, u1 + 0.04, door_s - 0.6, door_s + 0.6, pf, pf + 2.7)
                m.box("glass", u1, u1 + 0.04, door_s - 0.6, door_s + 0.6, pf + 2.8, pf + 3.3)
                m.box("trim", u1, u1 + 0.12, door_s - 0.8, door_s + 0.8, pf + 3.3, pf + 3.55)
                doors += 1
                risers = max(1, round(pf / 0.17))
                rh = pf / risers
                tread = 0.3
                land = 1.2
                reach = land + (risers - 1) * tread
                room = yard_u - u1 - 0.3
                if reach > room:   # a stoop may not reach the walk: steepen the going
                    tread = max(0.22, (room - land) / max(1, risers - 1))
                sw = float(e.get("stoop_width_m", 1.8))
                m.box("stone", u1, u1 + land, door_s - sw / 2, door_s + sw / 2, 0.0, pf)
                for r in range(1, risers):
                    ua = u1 + land + (r - 1) * tread
                    m.box("stone", ua, ua + tread, door_s - sw / 2, door_s + sw / 2, 0.0, pf - r * rh)
                # area lights to the basement under the principal-floor windows
                if pf > 0.9:
                    for s in centres:
                        if s != door_s:
                            m.box("glass", u1, u1 + 0.03, s - 0.45, s + 0.45, max(0.15, pf - 0.85), pf - 0.3)
        # chimneys on the main body's side walls
        if role == "main" and int(e.get("chimneys", 0)):
            n = int(e["chimneys"])
            for k in range(n):
                uc = u0 + (u1 - u0) * (0.3 + 0.4 * k / max(1, n - 1)) if n > 1 else (u0 + u1) / 2
                vc = v0 + 0.55 if k % 2 == 0 else v1 - 0.55
                y1 = top + 1.0
                m.box("brick", uc - 0.45, uc + 0.45, vc - 0.3, vc + 0.3, eave - 1.0, y1)
                m.box("cornice", uc - 0.55, uc + 0.55, vc - 0.4, vc + 0.4, y1, y1 + 0.18)

    # ---- features
    for feat in e.get("features", []):
        kind = feat["kind"]
        if kind == "corner_tower":
            r = float(feat.get("radius_m", 1.9))
            cu, cv = feat["at"]
            ring = [(cu + r * math.cos(math.radians(22.5 + 45 * k)), cv + r * math.sin(math.radians(22.5 + 45 * k)))
                    for k in range(8)]
            y1 = main_eave + float(feat.get("above_eave_m", 2.8))
            prism(m, front_mat, ring, 0.0, y1)
            prism(m, "cornice", [(cu + (r + 0.25) * math.cos(math.radians(22.5 + 45 * k)),
                                  cv + (r + 0.25) * math.sin(math.radians(22.5 + 45 * k))) for k in range(8)],
                  y1 - 0.35, y1)
            cone(m, "roof", [(cu + (r + 0.3) * math.cos(math.radians(11.25 + 22.5 * k)),
                              cv + (r + 0.3) * math.sin(math.radians(11.25 + 22.5 * k))) for k in range(16)],
                 y1, y1 + float(feat.get("cap_m", 5.5)))
            m.box("cornice", cu - 0.06, cu + 0.06, cv - 0.06, cv + 0.06, y1 + float(feat.get("cap_m", 5.5)) - 0.2,
                  y1 + float(feat.get("cap_m", 5.5)) + 0.9)
            # sash on the three faces that look out over the street and the side
            for k in range(int(params.stories) + 1):
                base = pf + sum(hs[:k]) if k < len(hs) else main_eave + 0.4
                for j in (0, 1, 7):
                    ang = math.radians(45 * j)
                    nu, nv = math.cos(ang), math.sin(ang)
                    du_ = r * math.cos(math.radians(22.5))
                    gu, gv = cu + nu * (du_ + 0.02), cv + nv * (du_ + 0.02)
                    tu, tv = -nv, nu
                    w2 = 0.42
                    hgt = 1.7
                    pts = [(gu - tu * w2, gv - tv * w2, base + 0.75), (gu + tu * w2, gv + tv * w2, base + 0.75),
                           (gu + tu * w2, gv + tv * w2, base + 0.75 + hgt), (gu - tu * w2, gv - tv * w2, base + 0.75 + hgt)]
                    m.face("glass", pts, (cu, cv, base + 1.5))
                    windows += 1
            facts["tower_top_m"] = round(y1 + float(feat.get("cap_m", 5.5)), 3)
    facts["windows"] = windows
    facts["doors"] = doors
    facts["triangles"] = m.triangles()
    facts["roll"] = round(rnd(), 6)   # the stream's first draw, so a seed change is visible
    return m, facts


# ---------------------------------------------------------------- glTF

def _pad(b: bytes, fill: bytes = b"\x00") -> bytes:
    return b + fill * ((4 - len(b) % 4) % 4)


def palette(params) -> dict:
    """The flat colours, each nudged by the record's seed inside +-6 % so no two
    neighbouring houses share one brick (the draft's 'no identical repeated facades')."""
    rnd = seed_rng(int(params.elevation["seed"]) ^ 0x5EED)
    out = {}
    tint = params.elevation.get("tint", {})
    for name in ORDER:
        mm = dict(MATERIALS[name])
        base = tint.get(name, mm["color"])
        k = 1.0 + (rnd() - 0.5) * 0.12 if name in ("brick", "stone", "brownstone", "trim", "frame", "cornice") else 1.0
        mm["color"] = tuple(round(min(1.0, c * k), 4) for c in base)
        out[name] = mm
    return out


def to_glb(m: Mesh, params, structure_id: str, phase_id: str, scene_ids, facts: dict) -> bytes:
    mats = palette(params)
    used = [k for k in ORDER if m.prims[k]["idx"]]
    bin_ = bytearray()
    views, accessors = [], []

    def view(blob: bytes, target):
        nonlocal bin_
        off = len(bin_)
        bin_ += _pad(blob)
        views.append({"buffer": 0, "byteOffset": off, "byteLength": len(blob), "target": target})
        return len(views) - 1

    def accessor(values, ctype, typ, comps, target, minmax=False):
        flat = [x for v in values for x in (v if comps > 1 else (v,))]
        fmt = {5126: "f", 5125: "I", 5123: "H"}[ctype]
        acc = {"bufferView": view(struct.pack(f"<{len(flat)}{fmt}", *flat), target),
               "componentType": ctype, "count": len(values), "type": typ}
        if minmax:
            acc["min"] = [struct.unpack("<f", struct.pack("<f", min(v[k] for v in values)))[0] for k in range(comps)]
            acc["max"] = [struct.unpack("<f", struct.pack("<f", max(v[k] for v in values)))[0] for k in range(comps)]
        accessors.append(acc)
        return len(accessors) - 1

    materials_out, prims_out = [], []
    for name in used:
        mm = mats[name]
        materials_out.append({"name": f"draft_{name}", "pbrMetallicRoughness": {
            "baseColorFactor": [*mm["color"], 1.0],
            "metallicFactor": mm.get("metallic", 0.0), "roughnessFactor": mm["roughness"]}})
        pr = m.prims[name]
        pos = [tuple(round(c, 4) for c in p) for p in pr["pos"]]
        nrm = [tuple(round(c, 5) for c in p) for p in pr["nrm"]]
        uv = [tuple(round(c, 4) for c in p) for p in pr["uv"]]
        ctype = 5123 if len(pos) < 65536 else 5125
        prims_out.append({"attributes": {
            "POSITION": accessor(pos, 5126, "VEC3", 3, 34962, True),
            "NORMAL": accessor(nrm, 5126, "VEC3", 3, 34962),
            "TEXCOORD_0": accessor(uv, 5126, "VEC2", 2, 34962),
            "_CONFIDENCE": accessor([m.conf] * len(pos), 5126, "SCALAR", 1, 34962)},
            "indices": accessor(pr["idx"], ctype, "SCALAR", 1, 34963),
            "material": len(materials_out) - 1})
    name = f"{structure_id}__{phase_id}"
    draft = params.elevation.get("draft_label", {})
    gltf = {
        "asset": {"version": "2.0", "generator": GENERATOR,
                  "extras": {"ticket": "T-2329", "structure": f"data/structures/{structure_id}.json"}},
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": [{"name": name, "mesh": 0, "extras": {
            "structure_id": structure_id, "phase_id": phase_id, "scene_ids": list(scene_ids),
            "family": "prairie_draft", "kind": params.kind, "draft": draft, "measured": facts}}],
        "meshes": [{"name": name, "primitives": prims_out}],
        "materials": materials_out,
        "accessors": accessors,
        "bufferViews": views,
        "buffers": [{"byteLength": len(bin_)}],
    }
    js = _pad(json.dumps(gltf, separators=(",", ":"), sort_keys=True).encode(), b" ")
    out = struct.pack("<III", 0x46546C67, 2, 12 + 8 + len(js) + 8 + len(bin_))
    out += struct.pack("<II", len(js), 0x4E4F534A) + js
    out += struct.pack("<II", len(bin_), 0x004E4942) + bytes(bin_)
    return out


def structure_glb(params, structure_id: str, phase_id: str, scene_ids) -> bytes:
    m, facts = build(params, structure_id)
    return to_glb(m, params, structure_id, phase_id, scene_ids, facts)


def seed_of(structure_id: str) -> int:
    return int(hashlib.sha256(f"prairie_draft:{structure_id}".encode()).hexdigest()[:8], 16)
