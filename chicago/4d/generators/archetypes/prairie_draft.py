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

def _seqsum(xs):
    """Add left to right, one term at a time — the same last bit on every CPython (T-2363).

    3.12 made the built-in `sum()` compensate floats (Neumaier) and 3.11 does not, so one
    record built different bytes on the steward runner's 3.12 than on the gate's pinned
    3.11 (house_2011_prairie's turret, #689). This is 3.11's `sum()` spelled out, so every
    committed draft keeps its bytes; `math.fsum` would have moved all of them. Never call
    the built-in `sum()` in this module: `tools/check_exact_sums.py` counts them.
    """
    total = 0
    for x in xs:
        total += x
    return total


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
            c = tuple(_seqsum(p[k] for p in pts) / len(pts) for k in range(3))
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
        c = tuple(_seqsum(p[k] for p in allp) / len(allp) for k in range(3))
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
        return _seqsum(len(p["idx"]) // 3 for p in self.prims.values())


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
    cen = (_seqsum(p[0] for p in ring) / len(ring), _seqsum(p[1] for p in ring) / len(ring), (y0 + y1) / 2)
    n = len(ring)
    for i in range(n):
        a, b = ring[i], ring[(i + 1) % n]
        m.face(mat, [(a[0], a[1], y0), (b[0], b[1], y0), (b[0], b[1], y1), (a[0], a[1], y1)], cen)
    m.face(mat, [(p[0], p[1], y0) for p in ring], cen)
    m.face(mat, [(p[0], p[1], y1) for p in ring], cen)


def cone(m: Mesh, mat, ring, y0, apex_y):
    cu = _seqsum(p[0] for p in ring) / len(ring)
    cv = _seqsum(p[1] for p in ring) / len(ring)
    cen = (cu, cv, y0 + (apex_y - y0) / 4)
    n = len(ring)
    for i in range(n):
        a, b = ring[i], ring[(i + 1) % n]
        m.face(mat, [(a[0], a[1], y0), (b[0], b[1], y0), (cu, cv, apex_y)], cen)
    m.face("cornice", [(p[0], p[1], y0) for p in ring], cen)


def hip_deck(m: Mesh, u0, u1, v0, v1, y, pitch, deck_h, o=0.35, insets=None):
    """A hipped roof cut off level `deck_h` over its eave: four sloped faces to a flat
    lead deck, and a ring of iron cresting round the deck. `insets` (u0, u1, v0, v1), the
    deck's edges in from the eave lines, gives each face its own pitch where a picture
    shows a steeper end. Returns the cresting's top."""
    u0, u1, v0, v1 = u0 - o, u1 + o, v0 - o, v1 + o
    inset = min(deck_h / math.tan(math.radians(pitch)), (u1 - u0) / 2 - 0.3, (v1 - v0) / 2 - 0.3)
    yd = y + inset * math.tan(math.radians(pitch))
    i_u0, i_u1, i_v0, i_v1 = insets if insets else (inset,) * 4
    a0, a1, b0, b1 = u0 + i_u0, u1 - i_u1, v0 + i_v0, v1 - i_v1
    lo = [(u0, v0, y), (u1, v0, y), (u1, v1, y), (u0, v1, y)]
    hi = [(a0, b0, yd), (a1, b0, yd), (a1, b1, yd), (a0, b1, yd)]
    cen = ((u0 + u1) / 2, (v0 + v1) / 2, y + (yd - y) / 3)
    for k in range(4):
        m.face("roof", [lo[k], lo[(k + 1) % 4], hi[(k + 1) % 4], hi[k]], cen)
    m.face("cornice", lo, cen)
    return crested_cap(m, [(a0, b0), (a1, b0), (a1, b1), (a0, b1)], (a0 + a1) / 2, (b0 + b1) / 2, yd)


def _on_face(side, at):
    """(s, n, y) on a wall -> (u, v, y): `s` runs along the wall, `n` out of it."""
    sign = 1 if side in ("u1", "v1") else -1
    if side in ("v0", "v1"):
        return lambda s, n, y: (s, at + sign * n, y)
    return lambda s, n, y: (at + sign * n, s, y)


def round_head(m: Mesh, mat, P, s, w, sill, spring, n, outward, seg=8):
    """A round-headed opening drawn flat on a wall: jambs from `sill` to `spring` and a
    half-circle over them, `n` out of the wall plane."""
    pts = [P(s - w / 2, n, sill), P(s + w / 2, n, sill)]
    for k in range(seg + 1):
        a = math.pi * k / seg
        pts.append(P(s + w / 2 * math.cos(a), n, spring + w / 2 * math.sin(a)))
    m.face(mat, pts, outward)


def stable_dress(m: Mesh, f: dict, rects: dict, wall: str, facts: dict) -> tuple[int, int]:
    """The Pullman stable's elevation from its pictures (T-3178), every number the record's:
    sash and round-headed lights on named faces, an arcade of round arches, a canted bay,
    a lantern on the roof deck, a square belvedere with a balustrade, and stacks."""
    windows = doors = 0

    def face_of(spec):
        u0, v0, u1, v1 = rects[spec["part"]]
        side = spec["side"]
        at = {"u0": u0, "u1": u1, "v0": v0, "v1": v1}[side]
        sign = 1 if side in ("u1", "v1") else -1
        P = _on_face(side, at)
        return P, (lambda s, y: P(s, -5.0, y)), sign

    for w in f.get("windows", []):
        P, inside, _ = face_of(w)
        s, sill, ww, hh = float(w["s"]), float(w["sill_m"]), float(w["w_m"]), float(w["h_m"])
        if w.get("head") == "round":
            spring = sill + hh - ww / 2
            round_head(m, "trim", P, s, ww + 0.3, sill - 0.1, spring, 0.03, inside(s, sill))
            round_head(m, "glass", P, s, ww, sill, spring, 0.06, inside(s, sill))
        else:
            m.face("trim", [P(s - ww / 2 - 0.12, 0.03, sill - 0.1), P(s + ww / 2 + 0.12, 0.03, sill - 0.1),
                            P(s + ww / 2 + 0.12, 0.03, sill + hh + 0.15), P(s - ww / 2 - 0.12, 0.03, sill + hh + 0.15)],
                   inside(s, sill))
            m.face("glass", [P(s - ww / 2, 0.06, sill), P(s + ww / 2, 0.06, sill),
                             P(s + ww / 2, 0.06, sill + hh), P(s - ww / 2, 0.06, sill + hh)], inside(s, sill))
        windows += 1
    for up in f.get("upper_walls", []):
        # an upper storey carried up through the roof's lower slope as one long wall
        # dormer with its own cornice, the stable's 18th Street front (T-3178)
        P, inside, _ = face_of(up)
        s0, s1 = float(up["s0"]), float(up["s1"])
        y0, y1, dp = float(up["from_m"]), float(up["top_m"]), float(up.get("depth_m", 1.2))
        a, b = P(s0, 0.0, y0), P(s1, -dp, y1)
        m.box(wall, min(a[0], b[0]), max(a[0], b[0]), min(a[1], b[1]), max(a[1], b[1]), y0, y1)
        a, b = P(s0 + (0.25 if s1 > s0 else -0.25) * -1, 0.3, y1 - 0.35), P(s1 + (0.25 if s1 > s0 else -0.25), -dp, y1)
        m.box("cornice", min(a[0], b[0]), max(a[0], b[0]), min(a[1], b[1]), max(a[1], b[1]), y1 - 0.35, y1)
        a, b = P(s0, 0.0, y1), P(s1, -dp, y1 + 0.06)
        m.box("roof", min(a[0], b[0]), max(a[0], b[0]), min(a[1], b[1]), max(a[1], b[1]), y1, y1 + 0.06)
    for band in f.get("courses", []):
        P, inside, _ = face_of(band)
        s0, s1, y = float(band["s0"]), float(band["s1"]), float(band["y_m"])
        q = [P(s0, 0.0, y), P(s1, 0.0, y), P(s1, 0.12, y), P(s0, 0.12, y)]
        m.solid([q, [P(s0, 0.0, y + 0.2), P(s1, 0.0, y + 0.2), P(s1, 0.12, y + 0.2), P(s0, 0.12, y + 0.2)],
                 [P(s0, 0.12, y), P(s1, 0.12, y), P(s1, 0.12, y + 0.2), P(s0, 0.12, y + 0.2)]], mat="trim")
    arc = f.get("arcade")
    if arc:
        P, inside, _ = face_of(arc)
        sill, spring = float(arc.get("sill_m", 0.0)), float(arc["spring_m"])
        pier = float(arc.get("pier_m", 0.45))
        for k, (s, w) in enumerate(zip(arc["centres"], arc["spans_m"])):
            s, w = float(s), float(w)
            round_head(m, "trim", P, s, w + 2 * 0.22, sill, spring, 0.04, inside(s, sill))
            round_head(m, "door" if k in arc.get("open", []) else "glass", P, s, w, sill, spring, 0.08,
                       inside(s, sill))
            # the piers' impost blocks at the springing
            for e_ in (s - w / 2 - pier / 2, s + w / 2 + pier / 2):
                m.solid([[P(e_ - pier / 2, 0.0, spring - 0.25), P(e_ + pier / 2, 0.0, spring - 0.25),
                          P(e_ + pier / 2, 0.0, spring), P(e_ - pier / 2, 0.0, spring)],
                         [P(e_ - pier / 2, 0.14, spring - 0.25), P(e_ + pier / 2, 0.14, spring - 0.25),
                          P(e_ + pier / 2, 0.14, spring), P(e_ - pier / 2, 0.14, spring)]], mat="trim")
            doors += 1
    bay = f.get("canted_bay")
    if bay:
        P, inside, _ = face_of(bay)
        s0, s1, d = float(bay["s0"]), float(bay["s1"]), float(bay["proj_m"])
        top, cap = float(bay["top_m"]), float(bay.get("cap_m", 0.8))
        g = 1.0 if s1 > s0 else -1.0     # the cheeks turn in toward each other along the face
        ring = [(s0, 0.0), (s0 + g * d, d), (s1 - g * d, d), (s1, 0.0)]
        ring3 = [P(a, b, 0.0) for a, b in ring]
        prism(m, wall, [(q[0], q[1]) for q in ring3], 0.0, top)
        o = 0.25
        ringo = [(s0 - g * o, -0.01), (s0 + g * (d - o * 0.41), d + o), (s1 - g * (d - o * 0.41), d + o),
                 (s1 + g * o, -0.01)]
        ro = [P(a, b, 0.0) for a, b in ringo]
        prism(m, "cornice", [(q[0], q[1]) for q in ro], top - 0.35, top)
        # a low hipped cap leaning back onto the wall
        rr = [(q[0], q[1]) for q in ro]
        apex = P((s0 + s1) / 2, 0.0, top + cap)
        cen = P((s0 + s1) / 2, -1.0, top)
        for k in range(3):
            a_, b_ = rr[k], rr[k + 1]
            m.face("roof", [(a_[0], a_[1], top), (b_[0], b_[1], top), apex], cen)
        # lights, one to each outer face, round-headed
        lt = bay["light"]
        for k in range(3):
            (a0, b0), (a1, b1) = ring[k], ring[k + 1]
            L = math.hypot(a1 - a0, b1 - b0)
            ta, tb = (a1 - a0) / L, (b1 - b0) / L
            ma, mb = (a0 + a1) / 2, (b0 + b1) / 2
            na, nb = tb, -ta          # outward: away from the bay's own middle
            if na * (ma - (s0 + s1) / 2) + nb * (mb - d / 2) < 0:
                na, nb = -na, -nb
            ww, sill, hh = float(lt["w_m"]), float(lt["sill_m"]), float(lt["h_m"])
            spring = sill + hh - ww / 2

            def Pf(t, off, y, ma=ma, mb=mb, ta=ta, tb=tb, na=na, nb=nb):
                return P(ma + ta * t + na * off, mb + tb * t + nb * off, y)
            for mat_, wd, off, y0 in (("trim", ww + 0.3, 0.03, sill - 0.1), ("glass", ww, 0.06, sill)):
                pts = [Pf(-wd / 2, off, y0), Pf(wd / 2, off, y0)]
                for j in range(9):
                    a = math.pi * j / 8
                    pts.append(Pf(wd / 2 * math.cos(a), off, spring + wd / 2 * math.sin(a)))
                m.face(mat_, pts, Pf(0.0, -3.0, sill))
            windows += 1
        facts["bay_top_m"] = round(top, 3)
    lan = f.get("lantern")
    if lan:
        cu, cv = lan["at"]
        r, y0 = float(lan["radius_m"]), float(lan["base_m"])
        dh, dome, fin = float(lan["drum_m"]), float(lan["dome_m"]), float(lan.get("finial_m", 0.9))
        ns = int(lan.get("sides", 8))
        ringf = lambda rad: [(cu + rad * math.cos(2 * math.pi * (k + 0.5) / ns),  # noqa: E731
                              cv + rad * math.sin(2 * math.pi * (k + 0.5) / ns)) for k in range(ns)]
        prism(m, "cornice", ringf(r + 0.15), y0 - 0.25, y0)
        prism(m, "trim", ringf(r), y0, y0 + dh)
        rg = ringf(r + 0.02)
        for k in range(ns):
            a_, b_ = rg[k], rg[(k + 1) % ns]
            ca, cb = a_[0] + (b_[0] - a_[0]) * 0.22, a_[1] + (b_[1] - a_[1]) * 0.22
            da, db = a_[0] + (b_[0] - a_[0]) * 0.78, a_[1] + (b_[1] - a_[1]) * 0.78
            m.face("glass", [(ca, cb, y0 + 0.25), (da, db, y0 + 0.25), (da, db, y0 + dh - 0.3),
                             (ca, cb, y0 + dh - 0.3)], (cu, cv, y0 + dh / 2))
            windows += 1
        prism(m, "cornice", ringf(r + 0.2), y0 + dh, y0 + dh + 0.22)
        # the dome in four rings to its crown
        yb = y0 + dh + 0.22
        prev = ringf(r + 0.1)
        for k in range(1, 5):
            t = k / 4
            rad = (r + 0.1) * math.cos(t * math.pi / 2) + 0.06
            yy = yb + dome * math.sin(t * math.pi / 2)
            nxt = ringf(rad)
            for j in range(ns):
                a_, b_, c_, d_ = prev[j], prev[(j + 1) % ns], nxt[(j + 1) % ns], nxt[j]
                m.face("roof", [(a_[0], a_[1], yb + dome * math.sin((k - 1) / 4 * math.pi / 2)),
                                (b_[0], b_[1], yb + dome * math.sin((k - 1) / 4 * math.pi / 2)),
                                (c_[0], c_[1], yy), (d_[0], d_[1], yy)], (cu, cv, yb))
            prev = nxt
        m.face("roof", [(p_[0], p_[1], yb + dome) for p_ in prev], (cu, cv, yb))
        m.box("cornice", cu - 0.05, cu + 0.05, cv - 0.05, cv + 0.05, yb + dome, yb + dome + fin)
        facts["lantern_top_m"] = round(yb + dome + fin, 3)
    bel = f.get("belvedere")
    if bel:
        u0, v0, u1, v1 = bel["rect"]
        top, bal = float(bel["top_m"]), float(bel.get("balustrade_m", 0.9))
        m.box(wall, u0, u1, v0, v1, 0.0, top - 0.45)
        m.box("cornice", u0 - 0.3, u1 + 0.3, v0 - 0.3, v1 + 0.3, top - 0.45, top)
        t = 0.22
        for b_ in ((u0 - 0.2, u1 + 0.2, v0 - 0.2, v0 - 0.2 + t), (u0 - 0.2, u1 + 0.2, v1 + 0.2 - t, v1 + 0.2),
                   (u0 - 0.2, u0 - 0.2 + t, v0 - 0.2, v1 + 0.2), (u1 + 0.2 - t, u1 + 0.2, v0 - 0.2, v1 + 0.2)):
            m.box("trim", b_[0], b_[1], b_[2], b_[3], top, top + bal - 0.12)
            m.box("cornice", b_[0] - 0.04, b_[1] + 0.04, b_[2] - 0.04, b_[3] + 0.04, top + bal - 0.12, top + bal)
        m.box("roof", u0, u1, v0, v1, top, top + 0.1)
        for side in bel.get("lights", []):
            at = {"u0": u0, "u1": u1, "v0": v0, "v1": v1}[side]
            mid = (v0 + v1) / 2 if side[0] == "u" else (u0 + u1) / 2
            window(m, side, at, mid, float(bel["light_sill_m"]), 0.9, float(bel.get("light_h_m", 1.5)))
            windows += 1
        facts["belvedere_top_m"] = round(top + bal, 3)
    for st in f.get("stacks", []):
        su, sv = st["at"]
        hw, hd = float(st["w_m"]) / 2, float(st["d_m"]) / 2
        m.box(wall, su - hw, su + hw, sv - hd, sv + hd, float(st.get("from_m", 4.0)), float(st["top_m"]))
        m.box("cornice", su - hw - 0.12, su + hw + 0.12, sv - hd - 0.12, sv + hd + 0.12,
              float(st["top_m"]) - 0.3, float(st["top_m"]))
    return windows, doors


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
        return pf + _seqsum(hs[:n]) if n <= len(hs) else pf + _seqsum(hs) + (n - len(hs)) * hs[-1]

    main = parts[0]
    mu0, mv0, mu1, mv1 = main["rect"]
    main_eave = eave_of(main)
    is_house = params.kind == "house"
    # a church's own dressing (T-3103) replaces the house front's sash, door and courses
    gothic = next((f for f in e.get("features", []) if f["kind"] == "gothic_church"), None)
    # faces a stable's dressing (T-3178) sets out from its pictures take no draft sash
    dressed = {d for f in e.get("features", []) if f["kind"] == "stable_dress" for d in f.get("dressed_faces", [])}
    if is_house and e.get("works"):
        return works_shell(m, e, parts, pf, hs, stone, lot_v0, lot_v1, party, facts, rnd)

    for i, p in enumerate(parts):
        u0, v0, u1, v1 = p["rect"]
        role = p["role"]
        if role == "porch":
            # a solid stone stoop up to the principal floor with its steps down on the face
            # away from the house: the draft's deck on four posts read as a slab hovering on
            # the lawn (T-2738); the refine pass builds the porch the photographs show
            deck = pf if is_house else 0.3
            m.box(stone if is_house else "trim", u0, u1, v0, v1, 0.0, deck)
            if deck >= 0.4:
                face = ("u1" if u0 >= mu1 - 0.1 else "v0" if v1 <= mv0 + 0.1 else "v1" if v0 >= mv1 - 0.1
                        else "u0" if u1 <= mu0 + 0.1 else "u1")
                n_st, tread = 4, 0.3
                rh = deck / (n_st + 1)
                mid = (v0 + v1) / 2 if face[0] == "u" else (u0 + u1) / 2
                half = min(0.9, ((v1 - v0) if face[0] == "u" else (u1 - u0)) / 2)
                for k in range(n_st):
                    a, b = k * tread, (k + 1) * tread
                    y = deck - (k + 1) * rh
                    if face == "u1":
                        m.box(stone, u1 + a, u1 + b, mid - half, mid + half, 0.0, y)
                    elif face == "u0":
                        m.box(stone, u0 - b, u0 - a, mid - half, mid + half, 0.0, y)
                    elif face == "v1":
                        m.box(stone, mid - half, mid + half, v1 + a, v1 + b, 0.0, y)
                    else:
                        m.box(stone, mid - half, mid + half, v0 - b, v0 - a, 0.0, y)
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
        if is_house and role in ("main", "wing", "bay", "stone_front") and not (gothic and role == "main"):
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
        elif roof == "hip_deck":
            # a hipped roof stopped at a flat deck inside an iron cresting, the stable roof of
            # the Pullman estate's 1894 plate (T-3178); `deck_m` is the deck over the eave
            m.box("cornice", u0 - 0.3, u1 + 0.3, v0 - 0.3, v1 + 0.3, eave - 0.4, eave)
            top = hip_deck(m, u0, u1, v0, v1, eave, pitch, float(p.get("deck_m", 3.0)),
                           insets=[float(x) for x in p["deck_insets_m"]] if p.get("deck_insets_m") else None)
        elif roof == "gable":
            along = "u" if (u1 - u0) >= (v1 - v0) else "v"
            inset = float(gothic.get("gable_inset_v0_m", 0.0)) if gothic and role == "main" else 0.0
            if inset:
                # the gable springs `inset` in from the north wall, over a narrow bay with its own
                # flat roof behind a cornice (the 1887 plate's north foot, T-3103)
                m.box("cornice", u0 - 0.2, u1 + 0.2, v0 - 0.2, v0 + inset, eave - 0.4, eave)
                m.box("roof", u0, u1, v0, v0 + inset, eave, eave + 0.06)
            top = gable(m, "roof", u0, u1, v0 + inset, v1, eave, pitch, along=along, end_mat=mat)
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
            if f"{p['id']}:{side}" in dressed:
                continue
            if gothic and role == "main" and side == "u1":
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
                # high v faces north unless the record says otherwise (the east side's lots)
                hi = e.get("v_toward", "north")
                lo = {"north": "south", "south": "north"}[hi]
                door_s = centres[-1] if e.get("entrance", "north") == hi else (
                    centres[0] if e.get("entrance") == lo else centres[len(centres) // 2])
            stn = e.get("station") if role == "main" else None
            if stn and side == "u1":
                # a station's street front: the passenger door at the end nearer the cross street
                # (high v faces `v_toward`, so a door at that end takes the last centre)
                door_s = centres[-1] if stn.get("door_end", "north") == e.get("v_toward", "north") else centres[0]
            if not is_house and side == "u0":
                # the alley face: a carriage door in the middle, a loft door above it
                cs = (a + b) / 2
                cw = min(3.0, length - 1.2) if not stn else float(stn.get("baggage_door_m", 2.4))
                sign = -1
                m.box("door", at - 0.05, at, cs - cw / 2, cs + cw / 2, 0.0, 3.0)
                m.box("trim", at - 0.12, at, cs - cw / 2 - 0.15, cs + cw / 2 + 0.15, 3.0, 3.25)
                if n_st >= 2 and not stn:   # a station's upper floor is no hay loft
                    m.box("door", at - 0.05, at, cs - 0.6, cs + 0.6, hs[0] + 0.3, hs[0] + 2.1)
                doors += 1
                centres = [c for c in centres if abs(c - cs) > cw / 2 + 0.8]
            for k in range(n_st):
                base = (pf if is_house else 0.0) + _seqsum(hs[:k])
                hk = hs[min(k, len(hs) - 1)]
                wh = min(2.2, hk - 1.3) if is_house else min(1.4, hk - 1.4)
                ww = float(e.get("sash_width_m", 1.0)) if is_house else 0.8
                sill = base + (0.75 if is_house else 1.1)
                for s in centres:
                    if k == 0 and door_s is not None and s == door_s:
                        continue
                    window(m, side, at, s, sill, ww, wh)
                    windows += 1
            if stn and side == "u1" and door_s is not None:
                doors += station_door(m, stn, u1, door_s)
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
            # 8 sides under a cone (the default), or 4 under a pyramid: a square tower (T-2330)
            ns = int(feat.get("sides", 8))
            half, step = 180 / ns, 360 / ns
            ring = [(cu + r * math.cos(math.radians(half + step * k)), cv + r * math.sin(math.radians(half + step * k)))
                    for k in range(ns)]
            y1 = main_eave + float(feat.get("above_eave_m", 2.8))
            prism(m, front_mat, ring, 0.0, y1)
            prism(m, "cornice", [(cu + (r + 0.25) * math.cos(math.radians(half + step * k)),
                                  cv + (r + 0.25) * math.sin(math.radians(half + step * k))) for k in range(ns)],
                  y1 - 0.35, y1)
            cap_ring = ([(cu + (r + 0.3) * math.cos(math.radians(11.25 + 22.5 * k)),
                          cv + (r + 0.3) * math.sin(math.radians(11.25 + 22.5 * k))) for k in range(16)] if ns == 8 else
                        [(cu + (r + 0.3) * math.cos(math.radians(half + step * k)),
                          cv + (r + 0.3) * math.sin(math.radians(half + step * k))) for k in range(ns)])
            if feat.get("cap", "cone") == "flat_crested":
                # a flat lead top inside a low iron cresting, the towers' other roof state (T-2351)
                tower_top = crested_cap(m, cap_ring, cu, cv, y1)
            elif feat.get("cap_top_r_m") is not None:
                # a spire that stops short of its point under a finial: a frustum to a small
                # flat top, the taper read off a photograph (T-3103)
                y2, rt = y1 + float(feat["cap_m"]), float(feat["cap_top_r_m"])
                k_ = rt / (r + 0.3)
                top_ring = [(cu + (p[0] - cu) * k_, cv + (p[1] - cv) * k_) for p in cap_ring]
                cen = (cu, cv, (y1 + y2) / 2)
                for i in range(len(cap_ring)):
                    a_, b_ = cap_ring[i], cap_ring[(i + 1) % len(cap_ring)]
                    c_, d_ = top_ring[(i + 1) % len(cap_ring)], top_ring[i]
                    m.face("roof", [(a_[0], a_[1], y1), (b_[0], b_[1], y1), (c_[0], c_[1], y2), (d_[0], d_[1], y2)], cen)
                m.face("cornice", [(p[0], p[1], y1) for p in cap_ring], cen)
                m.face("roof", [(p[0], p[1], y2) for p in top_ring], cen)
                tower_top = y2
            else:
                cone(m, "roof", cap_ring, y1, y1 + float(feat.get("cap_m", 5.5)))
                m.box("cornice", cu - 0.06, cu + 0.06, cv - 0.06, cv + 0.06, y1 + float(feat.get("cap_m", 5.5)) - 0.2,
                      y1 + float(feat.get("cap_m", 5.5)) + 0.9)
                tower_top = y1 + float(feat.get("cap_m", 5.5))
            # sash on the three faces that look out over the street and the side; a refined
            # record (T-2538) may name the floors its rows stand on and the faces they look
            # out of, as bearings in the plan (0 toward the street, 90 along +v)
            rows = ([float(b) for b in feat["window_rows_m"]] if "window_rows_m" in feat else
                    [pf + _seqsum(hs[:k]) if k < len(hs) else main_eave + 0.4
                     for k in range(int(params.stories) + 1)])
            faces = ([round(float(b) / step) % ns for b in feat["window_bearings_deg"]]
                     if "window_bearings_deg" in feat else [0, 1, ns - 1])
            for base in rows:
                for j in faces:
                    ang = math.radians(step * j)
                    nu, nv = math.cos(ang), math.sin(ang)
                    du_ = r * math.cos(math.radians(half))
                    gu, gv = cu + nu * (du_ + 0.02), cv + nv * (du_ + 0.02)
                    tu, tv = -nv, nu
                    w2 = 0.42
                    hgt = 1.7
                    pts = [(gu - tu * w2, gv - tv * w2, base + 0.75), (gu + tu * w2, gv + tv * w2, base + 0.75),
                           (gu + tu * w2, gv + tv * w2, base + 0.75 + hgt), (gu - tu * w2, gv - tv * w2, base + 0.75 + hgt)]
                    m.face("glass", pts, (cu, cv, base + 1.5))
                    windows += 1
            facts["tower_top_m"] = round(tower_top, 3)
        elif kind == "gothic_church":
            w_, d_ = gothic_church(m, feat, facts)
            windows += w_
            doors += d_
        elif kind == "stable_dress":
            w_, d_ = stable_dress(m, feat, {p["id"]: p["rect"] for p in parts}, front_mat, facts)
            windows += w_
            doors += d_
        elif kind == "party_wall":
            facts["party_wall_top_m"] = party_wall(m, parts, float(feat["v"]), eave_of, e)
    if e.get("station"):
        facts["station"] = station(m, e["station"], main["rect"], main_eave, hs)
    facts["windows"] = windows
    facts["doors"] = doors
    facts["triangles"] = m.triangles()
    facts["roll"] = round(rnd(), 6)   # the stream's first draw, so a seed change is visible
    return m, facts


# ---------------------------------------------------------------- a station's dressing (T-2399)

#: Block capitals on a 4 x 6 grid, each a list of strokes (x0, y0, x1, y1), and the
#: advance to the next letter in grid units. The letters the station's boards need and
#: the rest of the capitals and figures, so a board's wording is data, not code.
GLYPHS = {
    "A": ([(0, 0, 0, 6), (0, 6, 4, 6), (4, 6, 4, 0), (0, 3, 4, 3)], 5.6),
    "B": ([(0, 0, 0, 6), (0, 6, 3, 6), (3, 6, 3, 3), (0, 3, 4, 3), (4, 3, 4, 0), (4, 0, 0, 0)], 5.6),
    "C": ([(4, 6, 0, 6), (0, 6, 0, 0), (0, 0, 4, 0)], 5.6),
    "D": ([(0, 0, 0, 6), (0, 6, 3, 6), (3, 6, 4, 5), (4, 5, 4, 1), (4, 1, 3, 0), (3, 0, 0, 0)], 5.6),
    "E": ([(4, 6, 0, 6), (0, 6, 0, 0), (0, 0, 4, 0), (0, 3, 3, 3)], 5.6),
    "F": ([(4, 6, 0, 6), (0, 6, 0, 0), (0, 3, 3, 3)], 5.2),
    "G": ([(4, 6, 0, 6), (0, 6, 0, 0), (0, 0, 4, 0), (4, 0, 4, 3), (4, 3, 2, 3)], 5.6),
    "H": ([(0, 0, 0, 6), (4, 0, 4, 6), (0, 3, 4, 3)], 5.6),
    "I": ([(0, 0, 0, 6)], 1.6),
    "J": ([(4, 6, 4, 0), (4, 0, 0, 0), (0, 0, 0, 2)], 5.6),
    "K": ([(0, 0, 0, 6), (0, 3, 4, 6), (1, 3.75, 4, 0)], 5.6),
    "L": ([(0, 0, 0, 6), (0, 0, 4, 0)], 5.2),
    "M": ([(0, 0, 0, 6), (0, 6, 2.5, 3), (2.5, 3, 5, 6), (5, 6, 5, 0)], 6.6),
    "N": ([(0, 0, 0, 6), (0, 6, 4, 0), (4, 0, 4, 6)], 5.6),
    "O": ([(0, 0, 4, 0), (4, 0, 4, 6), (4, 6, 0, 6), (0, 6, 0, 0)], 5.6),
    "P": ([(0, 0, 0, 6), (0, 6, 4, 6), (4, 6, 4, 3), (4, 3, 0, 3)], 5.6),
    "Q": ([(0, 0, 4, 0), (4, 0, 4, 6), (4, 6, 0, 6), (0, 6, 0, 0), (2.5, 1.5, 4.5, -0.5)], 5.6),
    "R": ([(0, 0, 0, 6), (0, 6, 4, 6), (4, 6, 4, 3), (4, 3, 0, 3), (1.5, 3, 4, 0)], 5.6),
    "S": ([(4, 6, 0, 6), (0, 6, 0, 3), (0, 3, 4, 3), (4, 3, 4, 0), (4, 0, 0, 0)], 5.6),
    "T": ([(0, 6, 4, 6), (2, 6, 2, 0)], 5.6),
    "U": ([(0, 6, 0, 0), (0, 0, 4, 0), (4, 0, 4, 6)], 5.6),
    "V": ([(0, 6, 2, 0), (2, 0, 4, 6)], 5.6),
    "W": ([(0, 6, 1.25, 0), (1.25, 0, 2.5, 4), (2.5, 4, 3.75, 0), (3.75, 0, 5, 6)], 6.6),
    "X": ([(0, 0, 4, 6), (0, 6, 4, 0)], 5.6),
    "Y": ([(0, 6, 2, 3), (4, 6, 2, 3), (2, 3, 2, 0)], 5.6),
    "Z": ([(0, 6, 4, 6), (4, 6, 0, 0), (0, 0, 4, 0)], 5.6),
    "0": ([(0, 0, 4, 0), (4, 0, 4, 6), (4, 6, 0, 6), (0, 6, 0, 0)], 5.6),
    "1": ([(2, 0, 2, 6), (2, 6, 0.8, 4.8), (0.8, 0, 3.2, 0)], 5.2),
    "2": ([(0, 6, 4, 6), (4, 6, 4, 3), (4, 3, 0, 3), (0, 3, 0, 0), (0, 0, 4, 0)], 5.6),
    "3": ([(0, 6, 4, 6), (4, 6, 4, 0), (4, 0, 0, 0), (1, 3, 4, 3)], 5.6),
    "4": ([(0, 6, 0, 3), (0, 3, 4, 3), (3, 6, 3, 0)], 5.6),
    "5": ([(4, 6, 0, 6), (0, 6, 0, 3), (0, 3, 4, 3), (4, 3, 4, 0), (4, 0, 0, 0)], 5.6),
    "6": ([(4, 6, 0, 6), (0, 6, 0, 0), (0, 0, 4, 0), (4, 0, 4, 3), (4, 3, 0, 3)], 5.6),
    "7": ([(0, 6, 4, 6), (4, 6, 1.5, 0)], 5.6),
    "8": ([(0, 0, 4, 0), (4, 0, 4, 6), (4, 6, 0, 6), (0, 6, 0, 0), (0, 3, 4, 3)], 5.6),
    "9": ([(4, 3, 0, 3), (0, 3, 0, 6), (0, 6, 4, 6), (4, 6, 4, 0), (4, 0, 0, 0)], 5.6),
    ".": ([(0, 0, 0, 0.01)], 1.8),
    "&": ([(4, 0, 0, 6), (0, 6, 2.5, 6), (2.5, 6, 2.5, 4), (2.5, 4, 0, 2), (0, 2, 0, 0), (0, 0, 3, 0)], 5.6),
    " ": ([], 2.8),
}


def _onto(o, t, n):
    """Board coordinates (x along `t`, y up, z out along `n`) onto plan (u, v, y)."""
    return lambda x, y, z: (o[0] + t[0] * x + n[0] * z, o[1] + t[1] * x + n[1] * z, y)


def _quad_solid(m: Mesh, mat, P, corners, z0, z1):
    """A flat convex outline in board (x, y), extruded from z0 to z1 out of the board."""
    back = [P(x, y, z0) for x, y in corners]
    front = [P(x, y, z1) for x, y in corners]
    faces = [back, front] + [[back[i], back[(i + 1) % 4], front[(i + 1) % 4], front[i]] for i in range(4)]
    m.solid(faces, mat=mat)


def obox(m: Mesh, mat, P, x0, x1, y0, y1, z0, z1):
    """A box in a board's own frame (a board standing at any bearing)."""
    _quad_solid(m, mat, P, [(x0, y0), (x1, y0), (x1, y1), (x0, y1)], z0, z1)


# ---------------------------------------------------------------- a Gothic church's dressing (T-3103)

def slab(m: Mesh, mat, P, outline, z0, z1):
    """Any flat convex outline in board (x, y), extruded from z0 to z1 out of the board."""
    back = [P(x, y, z0) for x, y in outline]
    front = [P(x, y, z1) for x, y in outline]
    n = len(outline)
    m.solid([back, front] + [[back[i], back[(i + 1) % n], front[(i + 1) % n], front[i]] for i in range(n)], mat=mat)


def pointed(s, w, sill, head, seg=6):
    """A pointed opening's outline: jambs from `sill`, a two-centred arch to `head`.

    The arch rises 0.866 w (equilateral) when the opening is tall enough, else what it
    has, never less than half the span (a pointed, not a segmental, head)."""
    rise = max(w / 2, min(0.866 * w, (head - sill) * 0.5))
    ys = head - rise
    d = (rise * rise - w * w / 4) / w     # each arc's centre, inward of the far jamb
    r = w / 2 + d
    a_top = math.atan2(rise, d)
    right = [(s - d + r * math.cos(a_top * k / seg), ys + r * math.sin(a_top * k / seg)) for k in range(seg + 1)]
    left = [(s + d - r * math.cos(a_top * k / seg), ys + r * math.sin(a_top * k / seg)) for k in range(seg, -1, -1)]
    return [(s - w / 2, sill), (s + w / 2, sill)] + right + left[1:], ys


def disc(cx, cy, r, n=16):
    return [(cx + r * math.cos(2 * math.pi * k / n), cy + r * math.sin(2 * math.pi * k / n)) for k in range(n)]


def rose(m: Mesh, P, cx, cy, r, z, spokes=8):
    """A rose: a stone ring, glass inside it, a boss and spokes of tracery."""
    slab(m, "trim", P, disc(cx, cy, r), z, z + 0.04)
    slab(m, "glass", P, disc(cx, cy, r * 0.78), z + 0.04, z + 0.06)
    slab(m, "trim", P, disc(cx, cy, r * 0.22, 8), z + 0.06, z + 0.09)
    for k in range(spokes):
        a = 2 * math.pi * (k + 0.5) / spokes
        c, s_ = math.cos(a), math.sin(a)
        t = max(0.04, r * 0.06)
        p0, p1 = (cx + c * r * 0.2, cy + s_ * r * 0.2), (cx + c * r * 0.8, cy + s_ * r * 0.8)
        slab(m, "trim", P, [(p0[0] - s_ * t, p0[1] + c * t), (p0[0] + s_ * t, p0[1] - c * t),
                            (p1[0] + s_ * t, p1[1] - c * t), (p1[0] - s_ * t, p1[1] + c * t)], z + 0.06, z + 0.08)


def gothic_opening(m: Mesh, P, o):
    """One pointed opening on a board: a stone surround, its fill, mullions and a rose head.

    `o`: s (centre along the board), w, sill, head, lights, rose (bool), fill ('glass',
    'door' or 'louvre'), door_to (a door leaf to this height, glass above it)."""
    s, w, sill, head = float(o["s"]), float(o["w"]), float(o["sill"]), float(o["head"])
    fr = float(o.get("frame", 0.22))
    # the surround and fill reach `seat` back into the wall, so a board laid on a gable
    # end that stands a verge proud of the wall below it still meets the wall
    seat = -float(o.get("seat", 0.15))
    outer, _ = pointed(s, w + 2 * fr, sill - 0.12, head + fr)
    slab(m, "trim", P, outer, seat, 0.06)
    inner, ys = pointed(s, w, sill, head)
    fill = o.get("fill", "glass")
    slab(m, {"glass": "glass", "door": "door", "louvre": "cornice"}[fill], P, inner, seat, 0.08)
    if o.get("door_to") is not None:
        dt = float(o["door_to"])
        slab(m, "door", P, [(s - w / 2, sill), (s + w / 2, sill), (s + w / 2, dt), (s - w / 2, dt)], 0.0, 0.1)
        slab(m, "trim", P, [(s - w / 2, dt), (s + w / 2, dt), (s + w / 2, dt + 0.18), (s - w / 2, dt + 0.18)], 0.0, 0.12)
    n = int(o.get("lights", 1))
    low = float(o["door_to"]) + 0.18 if o.get("door_to") is not None else sill
    for k in range(1, n):
        x = s - w / 2 + w * k / n
        slab(m, "trim", P, [(x - 0.06, low), (x + 0.06, low), (x + 0.06, ys), (x - 0.06, ys)], 0.08, 0.12)
    if fill == "louvre":
        y = sill + 0.25
        while y < ys - 0.1:
            slab(m, "trim", P, [(s - w / 2, y), (s + w / 2, y), (s + w / 2, y + 0.07), (s - w / 2, y + 0.07)],
                 0.08, 0.13)
            y += 0.45
    if o.get("rose"):
        rise = head - ys
        r = min(w * 0.36, rise * 0.42)
        rose(m, P, s, ys + rise * 0.38, r, 0.08)
    return 1


def gothic_church(m: Mesh, feat: dict, facts: dict) -> tuple[int, int]:
    """The church's Gothic dressing, every place read off its photograph (T-3103).

    Board planes are named in the feature: `planes` maps a name to [axis, offset, out]
    with the offset from the feature's `at` (u from the front, v from the north face),
    `out` the side the face looks out of. Each item names its plane."""
    au, av = feat["at"]
    boards = {}
    for name, (axis, off, out) in feat["planes"].items():
        sgn = 1.0 if out > 0 else -1.0
        if axis == "u":
            boards[name] = _onto((au + off, av), (0.0, 1.0), (sgn, 0.0))
        else:
            boards[name] = _onto((au, av + off), (1.0, 0.0), (0.0, sgn))
    windows = doors = 0
    for o in feat.get("openings", []):
        gothic_opening(m, boards[o["plane"]], o)
        if o.get("fill") == "door" or o.get("door_to") is not None:
            doors += 1
        else:
            windows += 1
    for r_ in feat.get("roses", []):
        P = boards[r_["plane"]]
        cx, cy, r = (float(x) for x in r_["c_r"])
        slab(m, "trim", P, disc(cx, cy, r + 0.18), -0.15, 0.05)
        rose(m, P, cx, cy, r, 0.05)
        windows += 1
    for c in feat.get("courses", []):
        # a string course: [plane, s0, s1, y, depth]
        P = boards[c[0]]
        obox(m, "trim", P, float(c[1]), float(c[2]), float(c[3]) - 0.1, float(c[3]) + 0.1, 0.0, float(c[4]))
    for p in feat.get("panels", []):
        P = boards[p["plane"]]
        obox(m, "trim", P, p["s"][0], p["s"][1], p["h"][0], p["h"][1], 0.0, float(p.get("proud", 0.08)))
    # the gabled stone porch
    pc = feat.get("porch")
    if pc:
        u0, u1 = au + pc["u"][0], au + pc["u"][1]
        v0, v1 = av + pc["v"][0], av + pc["v"][1]
        sh, apex = float(pc["shoulder_m"]), float(pc["apex_m"])
        m.box("stone", u0, u1, v0, v1, 0.0, sh)
        pitch = math.degrees(math.atan2(apex - sh, (v1 - v0) / 2))
        gable(m, "roof", u0, u1, v0, v1, sh, pitch, along="u", o=0.15, end_mat="stone", verge=0.05)
        vm = (v0 + v1) / 2
        for sgn in (-1, 1):
            beam(m, "trim", (u1 + 0.12, vm + sgn * ((v1 - v0) / 2 + 0.2), sh - 0.1), (u1 + 0.12, vm, apex + 0.15), 0.32)
        m.box("trim", u1 - 0.1, u1 + 0.25, vm - 0.12, vm + 0.12, apex, apex + float(pc.get("finial_m", 0.8)))
    # the main gable's verge: coping on a corbel table, a kneeler at each foot, the cross
    vg = feat.get("verge")
    if vg:
        uf = au + float(vg["u"])
        va, vb, ve, ya = (av + float(vg["v"][0]), av + float(vg["v"][1]), float(vg["eave_m"]), float(vg["apex_m"]))
        vm = (va + vb) / 2
        for sgn in (-1, 1):
            foot = (uf + 0.2, vm + sgn * (vb - va) / 2, ve)
            top = (uf + 0.2, vm, ya)
            beam(m, "trim", foot, top, 0.45)
            # the corbel table: a block every `corbel_step_m` under the coping
            run = math.hypot((vb - va) / 2, ya - ve)
            n = int(run // float(vg.get("corbel_step_m", 0.7)))
            for k in range(1, n):
                t = k / n
                pv, py = foot[1] + (top[1] - foot[1]) * t, foot[2] + (top[2] - foot[2]) * t
                m.box("trim", uf, uf + 0.18, pv - 0.12, pv + 0.12, py - 0.62, py - 0.3)
            kv = foot[1]
            m.box("trim", uf - 0.05, uf + 0.45, kv - 0.65, kv + 0.65, ve - 1.1, ve + 0.6)
        cr = vg.get("cross_m")
        if cr:
            m.box("trim", uf + 0.05, uf + 0.35, vm - 0.14, vm + 0.14, ya, ya + float(cr))
            yc = ya + float(cr) * 0.62
            arm = float(vg.get("cross_span_m", 1.2)) / 2
            m.box("trim", uf + 0.05, uf + 0.35, vm - arm, vm + arm, yc - 0.13, yc + 0.13)
            P = _onto((uf + 0.15, vm), (0.0, 1.0), (1.0, 0.0))
            ring = vg.get("cross_ring_m")
            if ring is None:
                slab(m, "trim", P, disc(0.0, yc, 0.42, 12), 0.0, 0.12)
            else:
                # an open ring round the crossing, its outer radius read off a photograph
                # (T-3104), a band 0.14 m wide in sixteen pieces
                r1 = float(ring)
                r0 = r1 - 0.14
                for k in range(16):
                    a0, a1 = 2 * math.pi * k / 16, 2 * math.pi * (k + 1) / 16
                    slab(m, "trim", P, [(r0 * math.cos(a0), yc + r0 * math.sin(a0)),
                                        (r1 * math.cos(a0), yc + r1 * math.sin(a0)),
                                        (r1 * math.cos(a1), yc + r1 * math.sin(a1)),
                                        (r0 * math.cos(a1), yc + r0 * math.sin(a1))], 0.0, 0.12)
    # stepped buttresses, each a run of [u0, u1, v0, v1, y0, y1] stages under a sloped
    # offset, and an optional pinnacle: [u0, u1, v0, v1, y0, shaft_top, apex]
    for b in feat.get("buttresses", []):
        for st in b["stages"]:
            u0, u1, v0, v1, y0, y1 = st
            m.box("brick", au + u0, au + u1, av + v0, av + v1, y0, y1)
            along = "u" if (u1 - u0) < (v1 - v0) else "v"
            gable(m, "trim", au + u0, au + u1, av + v0, av + v1, y1, 50.0, along=along, o=0.05,
                  end_mat="trim", verge=0.02)
        pn = b.get("pinnacle")
        if pn:
            u0, u1, v0, v1, y0, y1, ap = pn
            m.box("trim", au + u0, au + u1, av + v0, av + v1, y0, y1)
            ring = [(au + u0 - 0.05, av + v0 - 0.05), (au + u1 + 0.05, av + v0 - 0.05),
                    (au + u1 + 0.05, av + v1 + 0.05), (au + u0 - 0.05, av + v1 + 0.05)]
            cone(m, "roof", ring, y1, ap)
    # gablets: a steep gable standing out of each face of the tower's head
    for g in feat.get("gablets", []):
        u0, u1, v0, v1 = au + g["rect"][0], au + g["rect"][1], av + g["rect"][2], av + g["rect"][3]
        y0, ap = float(g["spring_m"]), float(g["apex_m"])
        along = g["along"]
        half = ((v1 - v0) if along == "u" else (u1 - u0)) / 2
        gable(m, "roof", u0, u1, v0, v1, y0, math.degrees(math.atan2(ap - y0, half)), along=along, o=0.12,
              end_mat="brick", verge=0.1)
        if g.get("rose"):
            P = boards[g["rose"][0]]
            cx, cy, r = (float(x) for x in g["rose"][1:])
            rose(m, P, cx, cy, r, 0.0)
    # the north bay's stack
    for c in feat.get("stacks", []):
        u0, u1, v0, v1, y0, y1 = c
        m.box("brick", au + u0, au + u1, av + v0, av + v1, y0, y1)
        m.box("cornice", au + u0 - 0.1, au + u1 + 0.1, av + v0 - 0.1, av + v1 + 0.1, y1, y1 + 0.18)
    # the spire's band of lucarnes and its finial
    sp = feat.get("spire")
    if sp:
        cu, cv = au + sp["at"][0], av + sp["at"][1]
        y0, y1 = sp["band_m"]
        rb = float(sp["band_r_m"])
        prism(m, "cornice", [(cu + rb * math.cos(math.radians(22.5 + 45 * k)),
                              cv + rb * math.sin(math.radians(22.5 + 45 * k))) for k in range(8)], y0 - 0.3, y0)
        lw, lr, lh = float(sp["lucarne_w_m"]), float(sp["lucarne_out_m"]), float(sp["lucarne_h_m"])
        for k in range(4):
            if k % 2 == 0:
                sg = 1 if k == 0 else -1
                ua, ub = sorted((cu, cu + sg * lr))
                m.box("roof", ua, ub, cv - lw / 2, cv + lw / 2, y0, y0 + lh)
                gable(m, "roof", ua, ub, cv - lw / 2, cv + lw / 2, y0 + lh, 60.0, along="u", o=0.05,
                      end_mat="roof", verge=0.03)
                m.box("glass", ub if sg > 0 else ua - 0.02, (ub + 0.02) if sg > 0 else ua,
                      cv - lw * 0.3, cv + lw * 0.3, y0 + 0.2, y0 + lh - 0.1)
            else:
                sg = 1 if k == 1 else -1
                va_, vb_ = sorted((cv, cv + sg * lr))
                m.box("roof", cu - lw / 2, cu + lw / 2, va_, vb_, y0, y0 + lh)
                gable(m, "roof", cu - lw / 2, cu + lw / 2, va_, vb_, y0 + lh, 60.0, along="v", o=0.05,
                      end_mat="roof", verge=0.03)
                m.box("glass", cu - lw * 0.3, cu + lw * 0.3, vb_ if sg > 0 else va_ - 0.02,
                      (vb_ + 0.02) if sg > 0 else va_, y0 + 0.2, y0 + lh - 0.1)
        # the finial: a knob on the spire's flat top, a rod through a fleur's arms to the vane
        f0, f1 = sp["finial_m"]
        kw, kh = sp.get("knob_m", [0.36, 0.35])
        prism(m, "trim", [(cu + kw / 2 * math.cos(math.radians(22.5 + 45 * k)),
                           cv + kw / 2 * math.sin(math.radians(22.5 + 45 * k))) for k in range(8)], f0, f0 + kh)
        m.box("trim", cu - 0.05, cu + 0.05, cv - 0.05, cv + 0.05, f0 + kh, f1)
        yb = float(sp.get("fleur_m", f0 + (f1 - f0) * 0.6))
        fw = float(sp.get("fleur_w_m", 0.76)) / 2
        m.box("trim", cu - 0.06, cu + 0.06, cv - fw, cv + fw, yb - 0.08, yb + 0.08)
        m.box("trim", cu - fw, cu + fw, cv - 0.06, cv + 0.06, yb - 0.08, yb + 0.08)
        facts["finial_top_m"] = round(f1, 3)
    return windows, doors


def beam(m: Mesh, mat, p0, p1, w):
    """A square timber of side `w` from p0 to p1, (u, v, y) points at any slope."""
    ax = _sub(p1, p0)
    a = _cross(ax, (0.0, 0.0, 1.0))
    if _dot(a, a) < 1e-12:
        a = (1.0, 0.0, 0.0)
    a = _unit(a)
    b = _unit(_cross(ax, a))
    h = w / 2
    ring = [(-h, -h), (h, -h), (h, h), (-h, h)]
    lo = [(p0[0] + a[0] * x + b[0] * y, p0[1] + a[1] * x + b[1] * y, p0[2] + a[2] * x + b[2] * y) for x, y in ring]
    hi = [(p1[0] + a[0] * x + b[0] * y, p1[1] + a[1] * x + b[1] * y, p1[2] + a[2] * x + b[2] * y) for x, y in ring]
    m.solid([lo, hi] + [[lo[i], lo[(i + 1) % 4], hi[(i + 1) % 4], hi[i]] for i in range(4)], mat=mat)


def text_width(line: str, h: float) -> float:
    unit = h / 6.9
    return _seqsum(GLYPHS[c][1] for c in line) * unit - 1.6 * unit


def letter(m: Mesh, mat, P, line: str, x, y, h, z0, z1) -> int:
    """`line` in raised block capitals `h` tall, its baseline at y, starting at x. Returns
    the strokes cut."""
    unit = h / 6.9
    w = 0.9 * unit
    n = 0
    for c in line:
        strokes, adv = GLYPHS[c]
        for (a0, b0, a1, b1) in strokes:
            ax, ay = x + (a0 + 0.45) * unit, y + (b0 + 0.45) * unit
            bx, by = x + (a1 + 0.45) * unit, y + (b1 + 0.45) * unit
            dx, dy = bx - ax, by - ay
            ln = math.sqrt(dx * dx + dy * dy)
            dx, dy = dx / ln, dy / ln
            ax, ay, bx, by = ax - dx * w / 2, ay - dy * w / 2, bx + dx * w / 2, by + dy * w / 2
            px, py = -dy * w / 2, dx * w / 2
            _quad_solid(m, mat, P, [(ax - px, ay - py), (bx - px, by - py), (bx + px, by + py), (ax + px, ay + py)],
                        z0, z1)
            n += 1
        x += adv * unit
    return n


def nameboard(m: Mesh, P, length, y0, y1, lines, h, depth=0.05, two_faced=False, Pback=None) -> int:
    """A dark board with a light moulded edge and its wording raised on it, centred,
    lines stacked from the top. `P` is the board's frame, its face at z = 0 out to
    z = depth. A two-faced board (on posts) letters its back as well, through `Pback`."""
    obox(m, "cornice", P, 0.0, length, y0, y1, 0.0, depth)
    edge = 0.05
    strokes = 0
    gap = (y1 - y0 - len(lines) * h) / (len(lines) + 1)
    for Q in (P, Pback) if two_faced else (P,):
        for (xa, xb, ya, yb) in ((0, length, y1 - edge, y1), (0, length, y0, y0 + edge),
                                 (0, edge, y0, y1), (length - edge, length, y0, y1)):
            obox(m, "trim", Q, xa, xb, ya, yb, depth, depth + 0.02)
        base = y1 - gap - h
        for line in lines:
            strokes += letter(m, "trim", Q, line, (length - text_width(line, h)) / 2, base, h, depth, depth + 0.025)
            base -= gap + h
    return strokes


def station_door(m: Mesh, st: dict, u1: float, s: float) -> int:
    """The passenger door on a station's street front: a pair of leaves under a transom,
    and a bracketed hood over them."""
    w = float(st.get("door_width_m", 1.6))
    m.box("door", u1, u1 + 0.05, s - w / 2, s + w / 2, 0.0, 2.55)
    m.box("trim", u1, u1 + 0.07, s - 0.03, s + 0.03, 0.0, 2.55)          # the meeting stile
    m.box("glass", u1, u1 + 0.05, s - w / 2, s + w / 2, 2.65, 3.0)
    m.box("trim", u1, u1 + 0.1, s - w / 2 - 0.12, s - w / 2, 0.0, 3.1)
    m.box("trim", u1, u1 + 0.1, s + w / 2, s + w / 2 + 0.12, 0.0, 3.1)
    m.box("trim", u1, u1 + 0.12, s - w / 2 - 0.18, s + w / 2 + 0.18, 3.0, 3.12)
    hood = st.get("hood")
    if hood:
        y, d, hw = float(hood["y_m"]), float(hood["depth_m"]), float(hood["width_m"]) / 2
        # a lean-to hood falling 0.2 m to its fascia, on a bracket at each end
        top = [(u1, s - hw, y + 0.32), (u1 + d, s - hw, y + 0.12), (u1 + d, s + hw, y + 0.12), (u1, s + hw, y + 0.32)]
        bot = [(p[0], p[1], p[2] - 0.08) for p in top]
        m.solid([top, bot] + [[top[i], top[(i + 1) % 4], bot[(i + 1) % 4], bot[i]] for i in range(4)], mat="roof")
        m.box("cornice", u1 + d - 0.04, u1 + d + 0.02, s - hw, s + hw, y - 0.12, y + 0.14)
        for sv in (s - hw + 0.1, s + hw - 0.1):
            beam(m, "trim", (u1, sv, y - 0.75), (u1 + d * 0.8, sv, y + 0.02), 0.09)
            beam(m, "trim", (u1, sv, y + 0.02), (u1 + d - 0.05, sv, y + 0.02), 0.09)
    return 1


def station(m: Mesh, st: dict, rect, eave: float, hs) -> dict:
    """A railway station's platform, canopy and nameboards (T-2399).

    The platform lies against the track face (u0) out to an edge line the record gives
    as two (v, u) points; the canopy is a lean-to on brackets from that wall, over the
    stretch where the platform is deeper than it; boards on a face carry their wording in
    raised capitals, and a board `on_posts` stands on the platform, lettered both sides."""
    u0, v0, u1, v1 = rect
    facts = {}
    pf = st.get("platform")
    if pf:
        (va, ua), (vb, ub) = pf["edge_u"]
        edge = lambda v: ua + (ub - ua) * (v - va) / (vb - va)  # noqa: E731
        lo, hi = pf["v"]
        y = float(pf.get("deck_m", 0.3))
        ring = [(u0, lo), (edge(lo), lo), (edge(hi), hi), (u0, hi)]
        prism(m, "frame", ring, 0.0, y)
        # the planks' seams, running with the track, each from where the edge line crosses it
        k = 1
        while u0 - k * 0.16 > edge(hi) + 0.08:
            uu = u0 - k * 0.16
            vs = max(lo, va + (uu - ua) * (vb - va) / (ub - ua)) if uu < edge(lo) else lo
            m.face("roof", [(uu - 0.006, vs, y + 0.003), (uu + 0.006, vs, y + 0.003),
                            (uu + 0.006, hi, y + 0.003), (uu - 0.006, hi, y + 0.003)], (uu, (vs + hi) / 2, y - 1.0))
            k += 1
        # the edge timber the planks are spiked to, and a step at each end
        beam(m, "cornice", (edge(lo) + 0.08, lo, y - 0.12), (edge(hi) + 0.08, hi, y - 0.12), 0.2)
        for vv, dv in ((lo, -0.35), (hi, 0.35)):
            if u0 - 0.4 > edge(vv) + 0.4:
                m.box("frame", edge(vv) + 0.4, u0 - 0.4, min(vv, vv + dv), max(vv, vv + dv), 0.0, y / 2)
        facts["platform_m2"] = round(((u0 - edge(lo)) + (u0 - edge(hi))) / 2 * (hi - lo), 2)
        facts["platform_width_m"] = [round(u0 - edge(lo), 2), round(u0 - edge(hi), 2)]
    cn = st.get("canopy")
    if cn:
        ca, cb = cn["v"]
        d, yw, drop = float(cn["depth_m"]), float(cn["wall_y_m"]), float(cn["drop_m"])
        top = [(u0, ca, yw), (u0 - d, ca, yw - drop), (u0 - d, cb, yw - drop), (u0, cb, yw)]
        bot = [(p[0], p[1], p[2] - 0.08) for p in top]
        m.solid([top, bot] + [[top[i], top[(i + 1) % 4], bot[(i + 1) % 4], bot[i]] for i in range(4)], mat="roof")
        m.box("cornice", u0 - d - 0.05, u0 - d + 0.01, ca - 0.02, cb + 0.02, yw - drop - 0.3, yw - drop + 0.03)
        m.box("trim", u0 - 0.06, u0, ca, cb, yw - 0.18, yw - 0.02)                 # the wall plate
        n = max(2, round((cb - ca) / float(cn.get("bracket_every_m", 1.6))) + 1)
        for k in range(n):
            sv = ca + 0.1 + (cb - ca - 0.2) * k / (n - 1)
            under = yw - drop * 0.75 - 0.1
            beam(m, "trim", (u0, sv, yw - 1.15), (u0 - d * 0.72, sv, under), 0.1)       # the brace
            beam(m, "trim", (u0, sv, yw - 0.12), (u0 - d + 0.08, sv, yw - drop - 0.06), 0.1)  # the arm
        facts["canopy_m"] = [round(cb - ca, 2), round(d, 2)]
    strokes = boards = 0
    for bd in st.get("boards", []):
        h = float(bd["letter_m"])
        ya, yb = bd["y"]
        if bd.get("on_posts"):
            (va, ua), (vb, ub) = pf["edge_u"]
            t = _unit((ub - ua, vb - va, 0.0))
            n = (t[1], -t[0])           # the board faces the track, away from the wall
            if n[0] > 0:
                n = (-n[0], -n[1])
            t = (-n[1], n[0])           # the wording reads left to right from the track
            L = float(bd["length_m"])
            cv = float(bd["at_v"])
            cu = ua + (ub - ua) * (cv - va) / (vb - va) + float(bd.get("back_from_edge_m", 0.7))
            o = (cu - t[0] * L / 2, cv - t[1] * L / 2)
            P = _onto(o, t, n)
            # the back face's frame: from the board's far end, reading the other way, its
            # z = depth plane on the front frame's z = 0 (the board's back)
            ob = (o[0] + t[0] * L + n[0] * 0.03, o[1] + t[1] * L + n[1] * 0.03)
            Pb = _onto(ob, (-t[0], -t[1]), (-n[0], -n[1]))
            deck = float(pf.get("deck_m", 0.3))
            for x in (0.25, L - 0.25):
                q = P(x, 0, -0.06)
                m.box("trim", q[0] - 0.06, q[0] + 0.06, q[1] - 0.06, q[1] + 0.06, deck, yb + 0.12)
            strokes += nameboard(m, P, L, ya, yb, bd["lines"], h, depth=0.03, two_faced=True, Pback=Pb)
        else:
            face = bd["face"]
            n = {"u1": (1.0, 0.0), "u0": (-1.0, 0.0)}[face]
            t = (-n[1], n[0])
            at = u1 if face == "u1" else u0
            a, b = bd["v"]
            start = a if t[1] > 0 else b
            P = _onto((at, start), t, n)
            strokes += nameboard(m, P, b - a, ya, yb, bd["lines"], h)
        boards += 1
    facts["boards"] = boards
    facts["letter_strokes"] = strokes
    return facts


def crested_cap(m: Mesh, ring, cu, cv, y):
    """A tower's flat top: a lead deck on the cornice and a ring of iron cresting round its
    rim, posts and a top rail. Returns the cresting's top."""
    prism(m, "roof", ring, y, y + 0.12)
    crest = y + 0.12 + 0.75
    n = len(ring)
    for k in range(n):
        a, b = ring[k], ring[(k + 1) % n]
        pu, pv = a[0] + (cu - a[0]) * 0.06, a[1] + (cv - a[1]) * 0.06
        m.box("cornice", pu - 0.04, pu + 0.04, pv - 0.04, pv + 0.04, y + 0.12, crest)
        qu, qv = b[0] + (cu - b[0]) * 0.06, b[1] + (cv - b[1]) * 0.06
        rail = [(pu, pv, crest - 0.1), (qu, qv, crest - 0.1), (qu, qv, crest), (pu, pv, crest)]
        m.face("cornice", rail, (cu, cv, crest))                                   # outward
        m.face("cornice", rail, (2 * pu - cu, 2 * pv - cv, crest))                 # and inward
    return crest


def party_wall(m: Mesh, parts, v, eave_of, e, t=0.18, lift=0.45):
    """A party wall standing through one envelope at plan v (T-2351: the line Rees and
    Kimball divided their coach house on): brick, coped in stone, carried `lift` above the
    roof of every piece it crosses, gable-shaped where it crosses a ridge. Returns its top."""
    top = 0.0
    for p in parts:
        u0, v0, u1, v1 = p["rect"]
        if p.get("role") == "porch" or not (v0 < v < v1):
            continue
        eave = eave_of(p)
        roof = p.get("roof", "flat")
        tn = math.tan(math.radians(float(p.get("pitch_deg", e.get("roof_pitch_deg", 40)))))
        um = (u0 + u1) / 2
        if roof == "gable" and (u1 - u0) < (v1 - v0):      # the ridge runs along v: cross it
            ye, yp = eave + lift, eave + (u1 - u0) / 2 * tn + lift
        elif roof == "gable":                              # the ridge runs along u: cut the slope
            vm = (v0 + v1) / 2
            ye = yp = eave + ((v1 - v0) / 2 - abs(v - vm)) * tn + lift
        else:
            ye = yp = eave + lift
        a0, a1 = u0 - 0.05, u1 + 0.05
        faces = []
        for vs in (v - t, v + t):
            faces.append([(a0, vs, 0.0), (a1, vs, 0.0), (a1, vs, ye), (um, vs, yp), (a0, vs, ye)])
        faces.append([(a0, v - t, 0.0), (a0, v + t, 0.0), (a0, v + t, ye), (a0, v - t, ye)])
        faces.append([(a1, v - t, 0.0), (a1, v + t, 0.0), (a1, v + t, ye), (a1, v - t, ye)])
        faces.append([(a0, v - t, ye), (a0, v + t, ye), (um, v + t, yp), (um, v - t, yp)])
        faces.append([(um, v - t, yp), (um, v + t, yp), (a1, v + t, ye), (a1, v - t, ye)])
        m.solid(faces, mat_of=lambda i: "cornice" if i >= 4 else "brick")
        top = max(top, yp)
    return round(top, 3)


def works_shell(m: Mesh, e, parts, pf, hs, stone, lot_v0, lot_v1, party, facts, rnd):
    """A house still rising on the target date (T-2351: the Robbins house at 2126 on 1 July
    1904, the Hamill house razed and the new one building). Its walls stand as a hollow shell
    `raised_storeys` floors over the stone basement, the street wall and the front of its
    returns a part-storey (`course_m`) higher where the masons are; the openings are empty;
    there is no roof, sash, door or stoop; a deck is laid at the principal floor; and a pole
    scaffold with ledgers at every floor stands along the street and the open sides."""
    w = e["works"]
    n_up = int(w.get("raised_storeys", 1))
    course = float(w.get("course_m", 0.0))
    t = float(w.get("wall_m", 0.45))
    top = pf + _seqsum(hs[:n_up])
    rects = [tuple(p["rect"]) for p in parts]
    openings = 0
    for i, p in enumerate(parts):
        if p["role"] == "porch":
            continue                       # a porch is built after the walls
        u0, v0, u1, v1 = p["rect"]
        lead = course if p["role"] == "main" else 0.0
        um = (u0 + u1) / 2
        for (a0, a1, b0, b1, ytop) in ((u1 - t, u1, v0, v1, top + lead),        # street wall
                                       (um, u1 - t, v0, v0 + t, top + lead),     # returns, front half
                                       (um, u1 - t, v1 - t, v1, top + lead),
                                       (u0, um, v0, v0 + t, top),                # returns, rear half
                                       (u0, um, v1 - t, v1, top),
                                       (u0, u0 + t, v0 + t, v1 - t, top)):       # rear wall
            m.box(stone, a0, a1, b0, b1, 0.0, pf)
            m.box("brick", a0, a1, b0, b1, pf, ytop)
        m.box("trim", u0 + t, u1 - t, v0 + t, v1 - t, pf - 0.3, pf)
        for side, (at, a, b) in _wall_faces(p["rect"]).items():
            if b - a < 1.6 or _covered(side, at, a, b, rects, i):
                continue
            if (side == "v0" and at - lot_v0 < party) or (side == "v1" and lot_v1 - at < party):
                continue
            if side == "u1" and p["role"] == "main":
                n = int(e.get("front_bays", 3))
            else:
                n = int(max(0, (b - a - 0.8) // float(e.get("side_spacing_m", 3.0))))
            sign = 1 if side in ("u1", "v1") else -1
            x0, x1 = sorted((at, at + sign * 0.02))
            for k in range(n_up):
                sill = pf + _seqsum(hs[:k]) + 0.75
                hk = min(2.2, hs[min(k, len(hs) - 1)] - 1.3)
                for s in _spread(a, b, n, 0.7):
                    # an empty opening reads dark: the glass colour, with no sash, rail or sill
                    if side in ("u0", "u1"):
                        m.box("glass", x0, x1, s - 0.5, s + 0.5, sill, sill + hk)
                    else:
                        m.box("glass", s - 0.5, s + 0.5, x0, x1, sill, sill + hk)
                    m.box(stone, *((x0 - 0.06, x1 + 0.06, s - 0.6, s + 0.6) if side in ("u0", "u1") else
                                   (s - 0.6, s + 0.6, x0 - 0.06, x1 + 0.06)), sill + hk, sill + hk + 0.2)
                    openings += 1
    # the scaffold: poles 1.2 m off the main body's street wall and its open returns
    mu0, mv0, mu1, mv1 = parts[0]["rect"]
    pole_top = top + course + 1.8
    lines = [("u1", mu1 + 1.2, mv0 - 1.2, mv1 + 1.2)]
    if mv0 - lot_v0 >= party + 1.5:
        lines.append(("v0", mv0 - 1.2, mu0, mu1 + 1.2))
    if lot_v1 - mv1 >= party + 1.5:
        lines.append(("v1", mv1 + 1.2, mu0, mu1 + 1.2))
    levels = [pf + _seqsum(hs[:k]) for k in range(1, n_up + 1)] + [top + course]
    poles = 0
    for side, at, a, b in lines:
        for s in _spread(a, b, max(2, round((b - a) / 2.4) + 1), 0.0):
            uu, vv = (at, s) if side == "u1" else (s, at)
            m.box("trim", uu - 0.06, uu + 0.06, vv - 0.06, vv + 0.06, 0.0, pole_top)
            poles += 1
        for y in levels:
            if side == "u1":
                m.box("trim", at - 0.05, at + 0.05, a, b, y - 0.08, y)
                m.box("trim", at - 1.0, at + 0.1, a, b, y, y + 0.05)       # the planks
            else:
                m.box("trim", a, b, at - 0.05, at + 0.05, y - 0.08, y)
    facts["works"] = {"raised_storeys": n_up, "course_m": course, "poles": poles}
    facts["eave_m"] = round(top, 3)
    facts["top_m"] = round(top + course, 3)
    facts["windows"] = 0
    facts["openings"] = openings
    facts["doors"] = 0
    facts["triangles"] = m.triangles()
    facts["roll"] = round(rnd(), 6)
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
