"""The K15 chimney kit: every stack a closed solid seated in its roof, written straight to glTF.

TICKET T-2312 (piece 1 of T-1857, K15). The kit's sizes are data in
`data/components/prairie_1904/k15_chimneys.json`; this module reads them and builds each
variant the way T-2313 will build a named house's chimneys:

  roof       each variant stands in one of K05's roofs, built by K05's own element code
             (generators/archetypes/k05_roofs.py), so a stack meets the same covering a
             house's roof will have.
  parts      the shaft, its corbel courses, string courses, corbel blocks and cap, each
             clay pot, the stepped side flashing, the apron, the back flashing and the
             cricket are CLOSED polyhedra built in the stack's own frame (a up the slope,
             b up, c across it).
  union      the roof and the parts are joined by K05's BSP boolean union, so the shaft is
             cut where it passes through the covering, the flashing where it lies on it,
             and the cricket's valleys where its slopes meet the roof plane.
  difference each flue (through its pot, if it has one) and each sunk panel is then cut
             out of the joined solid, so a flue is a dark recess with walls and a floor.
  closure    K05's closure welds, repairs T-junctions and triangulates; the result must
             be watertight and one shell with its roof (tools/check_chimney_kit.py).
  light      the reduced tier: each stack as one box on its shaft's plan, from inside the
             roof to the same top, joined to the same roof. It keeps location and height.

WHY PURE PYTHON, and why K05's machinery: the reasons k05_roofs.py gives. The gate measures
vertices and edges, and the union is the one K05's roofs are already proved closed by.

    python3 generators/archetypes/k15_chimneys.py           write the specimen GLB
    python3 generators/archetypes/k15_chimneys.py --check   refuse if it is stale
"""

from __future__ import annotations

import copy
import hashlib
import json
import math
import struct
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from archetypes import k05_roofs as K5  # noqa: E402
from archetypes.k01_frontage import Prim, _cross, _dot, _unit  # noqa: E402

ROOT = HERE.parents[1]
DATA = ROOT / "data" / "components" / "prairie_1904" / "k15_chimneys.json"
GENERATOR = "chicago-4d generators/archetypes/k15_chimneys.py (K15, T-2312)"
RECONSTRUCTED = 1.0  # k01_frontage_params.CONFIDENCE_VALUE["reconstructed"]
VARIANT_GAP = 4.0     # metres of ground between two variants on the specimen board

_fsum = K5._fsum

# Role -> material, the roof's own roles first. Fixed order: the file is the same bytes
# every run.
ROLE_MATERIAL = dict(K5.ROLE_MATERIAL)
ROLE_MATERIAL.update({
    "shaft_brick": "brick", "corbel_brick": "brick", "panel": "brick", "light_brick": "brick",
    "shaft_stone": "stone", "corbel_stone": "stone", "band": "stone", "dentil": "stone",
    "cap_stone": "stone", "light_stone": "stone",
    "soot": "soot", "cap_cement": "cement", "flue": "flue", "pot": "pot",
    "flashing": "flashing", "cricket": "flashing",
})
# The roof a stack stands in: the board, not the stack, and not costed as one.
ROOF_ROLES = tuple(K5.ROLE_MATERIAL)
# A shaft's own faces, which must never show below the covering.
SHAFT_ROLES = ("shaft_brick", "shaft_stone", "soot", "panel", "light_brick", "light_stone")
STACK_ROLES = tuple(r for r in ROLE_MATERIAL if r not in ROOF_ROLES)


def materials() -> dict:
    m = K5.materials()
    m.update({
        "brick": {"color": (0.50, 0.24, 0.18), "roughness": 0.92},
        "stone": {"color": (0.66, 0.55, 0.42), "roughness": 0.88},
        "soot": {"color": (0.24, 0.17, 0.15), "roughness": 0.95},
        "cement": {"color": (0.62, 0.61, 0.58), "roughness": 0.9},
        "flue": {"color": (0.03, 0.03, 0.03), "roughness": 1.0},
        "pot": {"color": (0.66, 0.36, 0.22), "roughness": 0.8},
        "flashing": {"color": (0.42, 0.44, 0.46), "roughness": 0.55},
    })
    return m


def seed_of(component_id: str, index: int = 0, structure_id: str = "k15_chimney_kit") -> int:
    """K01's seed rule (k01_contract.json `seed`)."""
    return int(hashlib.sha256(f"{structure_id}|{component_id}|{index}".encode()).hexdigest()[:8], 16)


# -- the BSP difference (csg.js's subtract, beside K05's union) ----------------------------------

def subtract(a_polys, b_polys):
    a, b = K5.Node(a_polys), K5.Node(b_polys)
    a.invert()
    a.clip_to(b)
    b.clip_to(a)
    b.invert()
    b.clip_to(a)
    b.invert()
    a.build(b.all_polys())
    a.invert()
    return a.all_polys()


# -- the roof a variant stands in --------------------------------------------------------------

def roof_variant(v: dict, roofs: dict) -> dict:
    rv = copy.deepcopy([r for r in roofs["variants"] if r["id"] == v["roof"]][0])
    rv.update(v.get("roof_overrides", {}))
    return rv


def covering(rv: dict):
    """The covering's height over a plan point, for the two K05 roofs the kit stands in:
    a front gable (ridge along z) and a hip. eave_m is the covering's height at the wall
    line (K05), so the plane rises from there at the pitch."""
    W, D, E = rv["width_m"], rv["depth_m"], rv["eave_m"]
    t = math.tan(math.radians(rv["pitch_deg"]))
    if rv["kind"] == "gable":
        return lambda x, z: E + t * min(x, W - x), t
    if rv["kind"] == "hip":
        return lambda x, z: E + t * min(x, W - x, z, D - z), t
    raise ValueError(f"K15 stands only in a K05 gable or hip roof, not {rv['kind']}")


# -- a stack's own frame ------------------------------------------------------------------------

class Frame:
    """a up the slope (or across a ridge), b up, c across the slope; origin at the stack's
    plan centre. Axis permutations and signs only, so K05's hints map exactly."""

    def __init__(self, s: dict, cover):
        self.cx, self.cz = s["x"], s["z"]
        if s["across"] == "z":
            ua, uc = (1.0, 0.0), (0.0, 1.0)
        else:
            ua, uc = (0.0, 1.0), (1.0, 0.0)
        h = 0.01
        g = cover(self.cx + ua[0] * h, self.cz + ua[1] * h) - cover(self.cx - ua[0] * h, self.cz - ua[1] * h)
        sign = 1.0 if g >= 0 else -1.0
        self.ua = (ua[0] * sign, ua[1] * sign)
        self.uc = uc
        self.d, self.w = s["depth_m"], s["width_m"]
        self.cover = cover
        # astride a ridge if the covering falls on both sides of the plan centre
        lo = cover(*self.xz(-self.d / 2, 0.0))
        hi = cover(*self.xz(self.d / 2, 0.0))
        mid = cover(*self.xz(0.0, 0.0))
        self.ridge = mid > lo + 1e-9 and mid > hi + 1e-9

    def xz(self, a, c):
        return (self.cx + a * self.ua[0] + c * self.uc[0], self.cz + a * self.ua[1] + c * self.uc[1])

    def P(self, a, b, c):
        x, z = self.xz(a, c)
        return (x, b, z)

    def Q(self, a, b, c):
        """The same frame with a and c swapped: for a section in (c, b) extruded along a."""
        return self.P(c, b, a)

    def cov(self, a, c):
        return self.cover(*self.xz(a, c))

    def cov_line(self, a0, a1, c, extra=()):
        """Breakpoints of the covering along a line of constant c: its ends, a ridge
        between them, and any extra points asked for."""
        pts = {round(a0, 9), round(a1, 9)}
        if self.ridge and a0 < 0.0 < a1:
            pts.add(0.0)
        pts.update(round(x, 9) for x in extra if a0 <= x <= a1)
        return sorted(pts)


def box(F: Frame, a0, a1, b0, b1, c0, c1, role, top=None, bottom=None):
    """A closed box in a stack's frame. side roles may be a function of the face's outward
    direction in (a, c)."""
    def side(i, p, q):
        if abs(p[1] - q[1]) < 1e-12:
            return (top or role) if p[0] > q[0] else (bottom or role)
        return role(((-1.0 if i == 3 else 1.0), 0.0)) if callable(role) else role
    lo = role((0.0, -1.0)) if callable(role) else role
    hi = role((0.0, 1.0)) if callable(role) else role
    return K5.extrude([(a0, b0), (a1, b0), (a1, b1), (a0, b1)], c0, c1, F.P, side, lo, hi)


def split_box(F: Frame, a0, a1, c0, c1, levels, band_roles):
    """One closed box whose four sides are split at each inner level (no union between the
    bands, so no coplanar faces): band j's side facing (da, dc) takes band_roles[j](out)."""
    ring = [((a0, c0), (a1, c0), (0.0, -1.0)), ((a1, c0), (a1, c1), (1.0, 0.0)),
            ((a1, c1), (a0, c1), (0.0, 1.0)), ((a0, c1), (a0, c0), (-1.0, 0.0))]
    polys = []
    for j in range(len(levels) - 1):
        y0, y1 = levels[j], levels[j + 1]
        for (pa, pb, out) in ring:
            hx, hz = world_dir(F, *out)
            q = [F.P(pa[0], y0, pa[1]), F.P(pb[0], y0, pb[1]), F.P(pb[0], y1, pb[1]), F.P(pa[0], y1, pa[1])]
            polys.append(K5.oriented(q, band_roles[j](out), (hx, 0.0, hz)))
    corners = [r[0] for r in ring]
    polys.append(K5.oriented([F.P(a, levels[0], c) for a, c in corners], band_roles[0]((0.0, 0.0)),
                             (0.0, -1.0, 0.0)))
    polys.append(K5.oriented([F.P(a, levels[-1], c) for a, c in corners], band_roles[-1]((0.0, 0.0)),
                             (0.0, 1.0, 0.0)))
    return polys


def world_dir(F: Frame, da, dc):
    return (da * F.ua[0] + dc * F.uc[0], da * F.ua[1] + dc * F.uc[1])


def prism_xz(ring, y0, y1, role):
    """A vertical prism over a convex plan polygon (x, z), every face `role`."""
    pts = list(ring)
    if K5._area2d(pts) < 0:
        pts.reverse()
    cx = _fsum(p[0] for p in pts) / len(pts)
    cz = _fsum(p[1] for p in pts) / len(pts)
    polys = []
    for i in range(len(pts)):
        a, b = pts[i], pts[(i + 1) % len(pts)]
        pl = K5.oriented([(a[0], y0, a[1]), (b[0], y0, b[1]), (b[0], y1, b[1]), (a[0], y1, a[1])], role,
                         ((a[0] + b[0]) / 2 - cx, 0.0, (a[1] + b[1]) / 2 - cz))
        if pl:
            polys.append(pl)
    polys.append(K5.oriented([(x, y0, z) for x, z in pts], role, (0.0, -1.0, 0.0)))
    polys.append(K5.oriented([(x, y1, z) for x, z in pts], role, (0.0, 1.0, 0.0)))
    return polys


def circle(cx, cz, r, n):
    # rotated half a step, so a flat (not a vertex) faces each axis
    return [(cx + r * math.cos(2 * math.pi * (i + 0.5) / n), cz + r * math.sin(2 * math.pi * (i + 0.5) / n))
            for i in range(n)]


def pot_solid(x, z, y, profile, sides):
    rings = [(y + h, circle(x, z, r, sides)) for h, r in profile]
    return K5.ring_stack(rings, ["pot"] * (len(rings) - 1), "pot", "pot")


# -- one stack ------------------------------------------------------------------------------------

def stack_solids(s: dict, F: Frame, data: dict, t: float):
    """The closed parts of one stack (joined by union) and its cutters (taken away after),
    with the numbers they were built to. The stack comes in two: its BODY (shaft, courses,
    bands, blocks, flashing, cricket) below the cap's bed and its HEAD (the cap and its
    pots) on it. See join_stack for why."""
    p = data["parts"]
    fl, ck, ov = p["flashing"], p["cricket"], p["overlap_m"]
    d, w = F.d, F.w
    a0, a1, c0, c1 = -d / 2, d / 2, -w / 2, w / 2
    mat = s["material"]
    corners = [(a, c) for a in (a0, a1) for c in (c0, c1)]
    cov_lo = min(F.cov(a, c) for a, c in corners)
    cov_hi = max(F.cov(0.0, 0.0), *(F.cov(a, c) for a, c in corners))
    top = s["top_m"]
    cap = s["cap"]
    y_cap = top - cap["thickness_m"]
    y_head = y_cap - _fsum(h for h, _ in s["corbels"])
    solids, cutters = [], []

    # the shaft, with the leeward faces of its top band sooted
    so = data["soot"]
    th = math.radians(so["from_deg"] + 180.0)
    lee = (math.sin(th), -math.cos(th))   # local east +X, local north -Z (K01 frame)
    y_soot = max(y_head - so["band_m"], cov_hi + fl["upstand_m"] + 0.2)
    shaft_role = f"shaft_{mat}"

    def soot_role(out):
        x, z = world_dir(F, *out)
        return "soot" if x * lee[0] + z * lee[1] > 1e-9 else shaft_role
    b0 = cov_lo - p["shaft"]["below_covering_m"]
    solids.append(split_box(F, a0, a1, c0, c1, (b0, y_soot, y_head + ov), (lambda out: shaft_role, soot_role)))

    # corbel courses, then the cap, each a little down into the one below
    y = y_head
    for h, proj in s["corbels"]:
        solids.append(box(F, a0 - proj, a1 + proj, y - ov, y + h, c0 - proj, c1 + proj, f"corbel_{mat}"))
        y += h
    cp = cap["projection_m"]
    head = [box(F, a0 - cp, a1 + cp, y_cap, top, c0 - cp, c1 + cp, cap["role"])]

    # sandstone string courses
    for hb, tb, pb in s.get("bands", []):
        yb = cov_hi + hb
        solids.append(box(F, a0 - pb, a1 + pb, yb, yb + tb, c0 - pb, c1 + pb, "band"))

    # a row of stone corbel blocks under the head, on both broad faces
    if s.get("dentils"):
        n, bw, bh, bp = s["dentils"]
        for k in range(n):
            cc = c0 + (k + 0.5) * w / n
            for af, sg in ((a0, -1.0), (a1, 1.0)):
                ea, eb = af - sg * ov, af + sg * bp
                solids.append(box(F, min(ea, eb), max(ea, eb), y_head - bh, y_head + ov, cc - bw / 2, cc + bw / 2,
                                  "dentil"))

    # sunk panels on both broad faces: cutters
    if s.get("panels"):
        n, pw, ph, pd, pbot = s["panels"]
        for k in range(n):
            cc = c0 + (k + 0.5) * w / n
            for af, sg in ((a0, -1.0), (a1, 1.0)):
                ea, eb = af - sg * pd, af + sg * 0.05
                cutters.append(box(F, min(ea, eb), max(ea, eb), cov_hi + pbot, cov_hi + pbot + ph,
                                   cc - pw / 2, cc + pw / 2, "panel"))

    # flues: through a pot if the flue has one, else square in the cap
    pf = data["pot"]
    fo = p["flue"]["opening_m"]
    head_cutters = []
    yb = top - p["flue"]["depth_m"]
    for off, pot in flues(s):
        x, z = F.xz(0.0, off)
        # each cutter in two, at the cap's bed: the lower half cuts the body, the upper
        # the head, and their rings meet vertex for vertex at the bed
        if pot:
            prof = pf["profiles"][pot]
            head.append(pot_solid(x, z, top, prof, pf["sides"]))
            ytop = top + max(h for h, _ in prof)
            # a square bore: its faces lie on the stack's own axes, so cutting it makes no
            # new plane through a neighbouring pot (a round bore's twelve did, and left
            # slivers no 1 mm weld closes)
            bo = pf["bore_m"]
            cutters.append(box(F, -bo, bo, yb, y_cap, off - bo, off + bo, "flue"))
            head_cutters.append(box(F, -bo, bo, y_cap, ytop + 0.05, off - bo, off + bo, "flue"))
        else:
            cutters.append(box(F, -fo / 2, fo / 2, yb, y_cap, off - fo / 2, off + fo / 2, "flue"))
            head_cutters.append(box(F, -fo / 2, fo / 2, y_cap, top + 0.05, off - fo / 2, off + fo / 2, "flue"))

    # flashing: an apron below (on both slopes astride a ridge), stepped side flashing,
    # and behind a slope stack a cricket if it is wide, else back flashing
    thk, up, lap, emb, below = fl["thickness_m"], fl["upstand_m"], fl["lap_m"], fl["embed_m"], fl["below_covering_m"]
    wrap = thk + 0.04

    def apron(af, sg, role="flashing"):
        # its upstand half a course above the side flashing's, so their tops never share
        # a plane at the corner they overlap in
        yf = F.cov(af, 0.0) + p["course_m"] / 2
        yc = yf - p["course_m"] / 2
        out = [(af - sg * emb, yc - below),
               (af + sg * lap, F.cov(af + sg * lap, 0.0) - below),
               (af + sg * lap, F.cov(af + sg * lap, 0.0) + thk),
               (af + sg * thk, F.cov(af + sg * thk, 0.0) + thk),
               (af + sg * thk, yf + up),
               (af - sg * emb, yf + up)]
        return K5.extrude(out, c0 - wrap, c1 + wrap, F.P, role, role, role)

    solids.append(apron(a0, -1.0))
    behind = "apron" if F.ridge else ("cricket" if w > ck["min_width_m"] else "back")
    if F.ridge or behind == "back":
        solids.append(apron(a1, 1.0))
    step_run = p["course_m"] / t
    for cf, sg in ((c0, -1.0), (c1, 1.0)):
        n = max(1, math.ceil((a1 - a0) / step_run - 1e-9))
        edges = [a0 + (a1 - a0) * k / n for k in range(n + 1)]
        tops = []
        for k in range(n):
            xs = F.cov_line(edges[k], edges[k + 1], cf)
            tops.append(max(F.cov(x, cf) for x in xs) + up)
        bottom = [(x, F.cov(x, cf) - below - 0.01) for x in F.cov_line(a0, a1, cf)]
        stairs = []
        for k in range(n - 1, -1, -1):
            stairs.append((edges[k + 1], tops[k]))
            stairs.append((edges[k], tops[k]))
        out = K5._clean2(bottom + stairs)
        e0, e1 = cf - sg * emb, cf + sg * thk
        solids.append(K5.extrude(out, min(e0, e1), max(e0, e1), F.P, "flashing", "flashing", "flashing"))
    meta = {"behind": behind}
    if behind == "cricket":
        yf = F.cov(a1, 0.0)
        h = (w / 2) * math.tan(math.radians(ck["pitch_deg"]))
        half = (w / 2) * (h + below) / h
        run = h / t
        sec = [(-half, yf - below), (half, yf - below), (0.0, yf + h)]
        solids.append(K5.extrude(sec, a1 - emb, a1 + run + 0.05, F.Q, "cricket", "cricket", "cricket"))
        meta["cricket_rise_m"] = round(h, 4)
        meta["cricket_run_m"] = round(run, 4)
    meta.update({"cover_low_m": round(cov_lo, 4), "cover_high_m": round(cov_hi, 4), "top_m": top,
                 "head_m": round(y_head, 4), "astride_ridge": F.ridge, "flues": len(s["flues"]),
                 "pots": sum(1 for _, x in flues(s) if x), "material": mat, "bed_m": round(y_cap, 4)})
    return {"body": solids, "cut_body": cutters, "head": head, "cut_head": head_cutters, "bed": y_cap}, meta


def light_solid(s: dict, F: Frame, data: dict):
    """The reduced tier: one box on the shaft's plan from inside the roof to the full top
    (the cap's top, or a pot's lip if it carries pots), so it keeps location and height."""
    d, w = F.d, F.w
    corners = [(a, c) for a in (-d / 2, d / 2) for c in (-w / 2, w / 2)]
    cov_lo = min(F.cov(a, c) for a, c in corners)
    top = full_top(s, data)
    return box(F, -d / 2, d / 2, cov_lo - data["parts"]["shaft"]["below_covering_m"], top, -w / 2, w / 2,
               f"light_{s['material']}")


def flues(s: dict):
    """A stack's flues as (offset across the stack, pot profile or None)."""
    return [(f["at"], f.get("pot")) for f in s["flues"]]


def full_top(s: dict, data: dict) -> float:
    pots = [x for _, x in flues(s) if x]
    if not pots:
        return s["top_m"]
    return s["top_m"] + max(max(h for h, _ in data["pot"]["profiles"][p]) for p in pots)


# -- a variant ------------------------------------------------------------------------------------

class Stack:
    def __init__(self, v, rv, pts, tris, meta, origin, light=False):
        self.v, self.rv, self.pts, self.tris, self.meta, self.O = v, rv, pts, tris, meta, origin
        self.light = light
        self.seed = seed_of(v["id"] + (".light" if light else ""))


def _shift(polys, dx):
    return [K5.Poly([(p[0] + dx, p[1], p[2]) for p in pl.v], pl.role) for pl in polys]


def variant_parts(v: dict, data: dict, roofs: dict, light: bool = False):
    rv = roof_variant(v, roofs)
    roof, rmeta = K5.variant_solids(rv, roofs)
    cover, t = covering(rv)
    stacks, metas = [], []
    for s in v["stacks"]:
        F = Frame(s, cover)
        if light:
            stacks.append({"body": [light_solid(s, F, data)], "cut_body": [], "head": [], "cut_head": [],
                           "bed": None})
            metas.append({"top_m": round(full_top(s, data), 4), "centre": [s["x"], s["z"]]})
        else:
            parts, m = stack_solids(s, F, data, t)
            stacks.append(parts)
            m["centre"] = [s["x"], s["z"]]
            m["full_top_m"] = round(full_top(s, data), 4)
            metas.append(m)
    return rv, list(roof), stacks, {"ridge_m": rmeta.get("ridge_m"), "stacks": metas}


def _cut(polys, cutters):
    for c in cutters:
        polys = subtract(polys, c)
    return polys


def union_on(a_polys, b_polys, y):
    """K05's union with both trees rooted on the level plane y, which separates a (below)
    from b (above). A BSP plane is infinite: a pot's twelve faces would otherwise split
    every shaft, corbel and flashing polygon they happen to span, and the slivers they
    leave are what a 1 mm weld cannot close. Rooted on y, a polygon on one side never
    meets the other side's planes."""
    def node(polys):
        n = K5.Node()
        n.plane = K5.Plane((0.0, 1.0, 0.0), y)
        n.build(polys)
        return n
    a, b = node(a_polys), node(b_polys)
    # csg.js reads a missing back child as SOLID. That is right for a's root (everything
    # of a is behind it, nothing in front), wrong for b's: below y is outside b. So b's
    # root gets a back child whose plane faces down, with nothing behind it: all of the
    # space below y lies in its front, which (childless) reads as outside.
    b.back = K5.Node()
    b.back.plane = K5.Plane((0.0, -1.0, 0.0), -y)
    a.clip_to(b)
    b.clip_to(a)
    b.invert()
    b.clip_to(a)
    b.invert()
    a.build(b.all_polys())
    return a.all_polys()


def join_stack(st: dict, cut: bool = True):
    """One stack as one solid: body and head each joined and cut on their own, then joined
    on the cap's bed. The result's first polygon lies in the bed's plane, so when it is
    joined to the roof (whose covering lies wholly below every bed) the roof's polygons
    stay on the body's side of the tree and never meet a pot's planes."""
    body = K5.union_all(st["body"])
    if cut:
        body = _cut(body, st["cut_body"])
    if not st["head"]:
        return body
    head = K5.union_all(st["head"])
    if cut:
        head = _cut(head, st["cut_head"])
    return union_on(body, head, st["bed"])


def build_variant(v: dict, data: dict, roofs: dict, origin=(0.0, 0.0, 0.0), joined: bool = True,
                  light: bool = False, cut: bool = True) -> Stack:
    rv, roof, stacks, meta = variant_parts(v, data, roofs, light)

    def place(solids):
        return K5._snap([_shift(s, origin[0]) for s in solids] if origin[0] else solids)
    roof = place(roof)
    stacks = [{k: (place(x) if isinstance(x, list) else x) for k, x in st.items()} for st in stacks]
    if joined:
        polys = K5.union_all(roof)
        for st in stacks:
            polys = K5.union(polys, join_stack(st, cut))
    else:
        polys = [p for s in roof for p in s] + [p for st in stacks for s in st["body"] + st["head"] for p in s]
    pts, tris = K5.close(polys)
    return Stack(v, rv, pts, tris, meta, origin, light)


def footprint_span(v: dict, data: dict, roofs: dict):
    _, roof, stacks, _ = variant_parts(v, data, roofs)
    xs = [p[0] for s in roof + [s for st in stacks for s in st["body"] + st["head"]] for pl in s for p in pl.v]
    return min(xs), max(xs)


def build_kit(data: dict | None = None, roofs: dict | None = None) -> list[tuple[Stack, Stack]]:
    data = data or load()
    roofs = roofs or K5.load()
    out, x = [], 0.0
    for v in data["variants"]:
        lo, hi = footprint_span(v, data, roofs)
        O = (x - lo, 0.0, 0.0)
        out.append((build_variant(v, data, roofs, origin=O), build_variant(v, data, roofs, origin=O, light=True)))
        x += (hi - lo) + VARIANT_GAP
    return out


def load() -> dict:
    return json.loads(DATA.read_text())


def triangles(r: Stack, roles=STACK_ROLES) -> int:
    return _fsum(1 for t in r.tris if t[3] in roles)


# -- glTF ---------------------------------------------------------------------------------------------

def _prims(r: Stack) -> dict[str, Prim]:
    """Flat-shaded per triangle, metric UVs on each face's own contour (K05's rule)."""
    prims: dict[str, Prim] = {}
    Y = (0.0, 1.0, 0.0)
    for a, b, c, role, n in r.tris:
        tn = K5._tri_normal(r.pts, (a, b, c))
        au = _cross(Y, tn)
        au = _unit(au) if _dot(au, au) > 1e-9 else (1.0, 0.0, 0.0)
        av = _cross(tn, au)
        pr = prims.setdefault(role, Prim(role))
        pr.face([r.pts[a], r.pts[b], r.pts[c]], tn, ((0.0, 0.0, 0.0), au, av, 1.0, 1.0, 0.0, 0.0), RECONSTRUCTED)
    return prims


def to_glb(kit: list[tuple[Stack, Stack]], data: dict) -> bytes:
    mats = materials()
    bin_ = bytearray()
    views, accessors, meshes, nodes = [], [], [], []

    def view(blob: bytes, target):
        nonlocal bin_
        off = len(bin_)
        bin_ += K5._pad(blob)
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

    mat_names = list(mats)
    materials_out = [{"name": f"k15_{name}", "pbrMetallicRoughness": {
        "baseColorFactor": [*[round(c, 4) for c in mats[name]["color"]], 1.0],
        "metallicFactor": 0.0, "roughnessFactor": mats[name]["roughness"]}} for name in mat_names]

    def mesh_of(r: Stack, name: str):
        prims = _prims(r)
        by_mat: dict[str, list[Prim]] = {}
        for role in ROLE_MATERIAL:   # fixed order
            if role in prims and prims[role].idx:
                by_mat.setdefault(ROLE_MATERIAL[role], []).append(prims[role])
        prims_out = []
        for mname in mat_names:
            if mname not in by_mat:
                continue
            pos, nrm, uv, conf, idx = [], [], [], [], []
            for pr in by_mat[mname]:
                base = len(pos)
                pos += [tuple(round(c, 5) for c in q) for q in pr.pos]
                nrm += [tuple(round(c, 6) for c in q) for q in pr.nrm]
                uv += [tuple(round(c, 5) for c in q) for q in pr.uv]
                conf += pr.conf
                idx += [base + i for i in pr.idx]
            ctype = 5123 if len(pos) < 65536 else 5125
            prims_out.append({"attributes": {
                "POSITION": accessor(pos, 5126, "VEC3", 3, 34962, True),
                "NORMAL": accessor(nrm, 5126, "VEC3", 3, 34962),
                "TEXCOORD_0": accessor(uv, 5126, "VEC2", 2, 34962),
                "_CONFIDENCE": accessor(conf, 5126, "SCALAR", 1, 34962)},
                "indices": accessor(idx, ctype, "SCALAR", 1, 34963),
                "material": mat_names.index(mname)})
        meshes.append({"name": name, "primitives": prims_out})
        return len(meshes) - 1

    for full, light in kit:
        vid = full.v["id"]
        for r, name, tier in ((full, vid, "full"), (light, vid + ".light", "light")):
            stacks = []
            for s, m in zip(r.v["stacks"], r.meta["stacks"]):
                x, z = s["x"] + r.O[0], s["z"]
                stacks.append({"centre": [round(x, 4), round(z, 4)], "top_m": m.get("full_top_m", m["top_m"]),
                               **({k: m[k] for k in ("cover_low_m", "cover_high_m", "head_m", "behind",
                                                     "astride_ridge", "flues", "pots", "material")}
                                  if tier == "full" else {})})
            nodes.append({"name": name, "mesh": mesh_of(r, name), "extras": {
                "component_id": vid, "family": "chimney", "tier": tier, "roof": r.v["roof"], "seed": r.seed,
                "origin": [round(c, 4) for c in r.O],
                "triangles_stack": triangles(r), "triangles_with_board": len(r.tris),
                "ridge_m": r.meta["ridge_m"], "stacks": stacks}})
    gltf = {
        "asset": {"version": "2.0", "generator": GENERATOR},
        "scene": 0,
        "scenes": [{"nodes": list(range(len(nodes)))}],
        "nodes": nodes,
        "meshes": meshes,
        "materials": materials_out,
        "accessors": accessors,
        "bufferViews": views,
        "buffers": [{"byteLength": len(bin_)}],
        "extras": {"k15": {"data": "data/components/prairie_1904/k15_chimneys.json", "ticket": "T-2312",
                           "roofs": "data/components/prairie_1904/k05_roofs.json",
                           "contract": "data/components/prairie_1904/k01_contract.json"}},
    }
    js = K5._pad(json.dumps(gltf, separators=(",", ":"), sort_keys=True).encode(), b" ")
    body = bytes(bin_)
    total = 12 + 8 + len(js) + 8 + len(body)
    return (struct.pack("<III", 0x46546C67, 2, total) + struct.pack("<I4s", len(js), b"JSON") + js
            + struct.pack("<I4s", len(body), b"BIN\x00") + body)


def main(argv) -> int:
    data = load()
    blob = to_glb(build_kit(data), data)
    out = ROOT / data["specimen"]
    if "--check" in argv:
        if not out.exists() or out.read_bytes() != blob:
            print(f"FAIL {out.relative_to(ROOT)} is not what the generator builds from "
                  f"{DATA.relative_to(ROOT)}: run python3 generators/archetypes/k15_chimneys.py")
            return 1
        print(f"ok   {out.relative_to(ROOT)} is the generator's bytes ({len(blob)} B)")
        return 0
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(blob)
    print(f"wrote {out.relative_to(ROOT)} ({len(blob)} B)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
