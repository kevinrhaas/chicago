"""The K16 timber kit: frame cladding and exterior timber built board by board, written
straight to glTF.

TICKET T-2322 (piece 1 of T-1858, K16). The kit's sizes are data in
`data/components/prairie_1904/k16_timber.json`; this module reads them and builds four
samples, the parts T-2323 will put on 1638 Shortall-Gregory's Gothic front:

  clapboard_corner   clapboard over a water table, an outside corner with its pair of
                     corner boards and a short return, one cased window (the sash, glass,
                     blind and room are K06's), a frieze, a boxed eave and scroll brackets
  board_and_batten   vertical boards with a batten over every joint
  gothic_shingle     clapboard to a belt, square and fish-scale shingles inside rake
                     boards, pierced bargeboards on the verges meeting at a finial
  lattice_post       an oiled board floor nosing past its rim, a lattice skirt over a
                     dark crawl space, a chamfered post with brackets under the plate, a
                     varnished beaded ceiling

THE LAP RULE, which every lapped course (clapboard, shingle) is built by: a course's front
face falls from its butt, proud of the sheathing by support + butt, back by `butt` over one
exposure, so the next course's butt underside sits exactly on it — a shadow line `butt`
deep, never a gap and never a board through a board. `support` is how far the course
below holds a board off the sheathing, derived from tip, butt and lap (`support_of`).

WHY PURE PYTHON — the reasons k01_frontage.py gives: the gate measures vertices (laps,
staggers, battens over joints, piercings cut through), and they are easiest to hold when
this module writes them. `Prim` and the vector helpers are K01's own, the sash is K06's.

    python3 generators/archetypes/k16_timber.py           write the specimen GLB
    python3 generators/archetypes/k16_timber.py --check   refuse if it is stale
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

from archetypes.k01_frontage import Prim, _add, _cross, _dot, _mul, _sub, _unit  # noqa: E402
from archetypes import k06_windows as K06  # noqa: E402
from archetypes import k09_trim as K09  # noqa: E402
from archetypes import k14_yard as K14  # noqa: E402

ROOT = HERE.parents[1]
DATA = ROOT / "data" / "components" / "prairie_1904" / "k16_timber.json"
GENERATOR = "chicago-4d generators/archetypes/k16_timber.py (K16, T-2322)"
RECONSTRUCTED = 1.0  # k01_frontage_params.CONFIDENCE_VALUE["reconstructed"]

Y = (0.0, 1.0, 0.0)

# Role -> material. A role is what the gate measures; a material is what a renderer
# binds. Fixed order: the file is the same bytes every run.
ROLE_MATERIAL = {
    "sheathing": "sheathing",
    "clapboard": "body", "clapboard_butt": "body", "board": "body", "batten": "body",
    "shingle": "shingle", "shingle_butt": "shingle",
    "corner_board": "trim", "water_table": "trim", "drip_cap": "trim", "casing": "trim",
    "sill": "trim", "apron": "trim", "frieze": "trim", "fascia": "trim", "soffit": "trim",
    "bracket": "trim", "belt": "trim", "rake_board": "trim", "bargeboard": "trim",
    "finial": "trim", "lattice": "trim", "lattice_frame": "trim", "rim": "trim",
    "post": "trim", "plate": "trim",
    "porch_floor": "stained", "ceiling": "stained",
    "end_grain": "end_grain", "cutout": "end_grain",
    # K06's sash in a cased opening: the jamb lining is painted trim, the rest K06's
    "reveal": "trim", "frame": "sash", "sash_outer": "sash", "sash_inner": "sash",
    "glass_outer": "glass", "glass_inner": "glass", "came": "lead_came",
    "blind": "blind", "curtain": "curtain", "backing": "backing", "crawl": "backing",
    # the board: what a sample stands on or is cut from, excluded from its costs
    "foundation": "foundation", "roof": "roof", "backdrop": "backdrop",
    "interior": "plaster", "cut": "cut",
    # T-2323: a house in the scene — the plain body standing in for its envelope
    "stand_in": "stand_in", "stand_in_roof": "roof", "skirt": "trim",
    # T-2357: a whole frame house — its door, steps, roof covering and brick stack
    "door": "stained", "door_panel": "stained", "step_tread": "stained", "step_riser": "trim",
    # T-2425: 1638's arched entrance, its pierced spandrels painted with the porch's trim
    "spandrel": "trim",
    # T-2457: the small carved stops at the springs of 1638's bay lights, dark in the print
    "stop": "sash",
    "roof_covering": "roof", "chimney": "foundation",   # the stack is the foundation's brick
    # T-2456: 1638's street fence — iron bars on a stone base, painted timber gate piers on
    # stone plinths, each cap hollow behind its pierced faces, the finials iron
    "fence_bar": "fence_iron", "fence_rail": "fence_iron", "pier_finial": "fence_iron",
    "fence_base": "fence_stone", "pier_plinth": "fence_stone", "pier": "trim", "pier_cap": "trim",
    # T-3181: 1720's porch — its turned balustrades, the stair's cheeks and newels, and the iron
    # cresting round its deck, which takes the boundary's iron
    "rail": "trim", "baluster": "trim", "string": "trim", "newel": "trim", "cresting": "fence_iron",
    # T-3222: 1638's front walk, flags of the boundary's stone (its plinths'): one slot, no new draw
    "walk_flag": "fence_stone",
}
#: T-2425: how far behind a glazed door's glass the dark of the hall is laid
GLAZED_HALL_M = 0.15
BOARD_ROLES = ("foundation", "roof", "backdrop", "interior", "cut")
# Roles that are not timber: K06's glass and room, and the board.
NOT_TIMBER = ("glass_outer", "glass_inner", "came", "blind", "curtain", "backing", "crawl") + BOARD_ROLES
# T-2357: what a whole house adds that is not timber, its roof covering and its brick stack
NOT_TIMBER += ("roof_covering", "chimney")
NOT_TIMBER += ("fence_bar", "fence_rail", "pier_finial", "fence_base", "pier_plinth")
NOT_TIMBER += ("cresting",)
NOT_TIMBER += ("walk_flag",)
#: T-2456: the boundary's two materials, offered only to a house that builds one
BOUNDARY_MATERIALS = {
    "fence_iron": {"color": (0.12, 0.12, 0.12), "roughness": 0.6, "metallic": 0.4, "class": "metal"},
    "fence_stone": {"color": (0.70, 0.68, 0.62), "roughness": 0.92, "class": "masonry"},
}


def materials(data: dict) -> dict:
    p = data["paint"]
    k6 = K06.load()["parts"]
    g = k6["glass"]
    out = {name: {"color": tuple(p[name]["color"]), "roughness": p[name]["roughness"], "class": p[name]["class"]}
           for name in ("body", "trim", "shingle", "sash", "stained", "end_grain", "sheathing")}
    out.update({
        "glass": {"color": tuple(g["base_color"]), "roughness": g["roughness"], "metallic": g["metallic"],
                  "alpha": g["alpha"], "class": "glass"},
        "lead_came": {"color": (0.22, 0.23, 0.24), "roughness": 0.5, "metallic": 0.3, "class": "metal"},
        "blind": {"color": tuple(k6["blind"]["color"]), "roughness": 0.95, "class": "textile"},
        "curtain": {"color": tuple(k6["curtain"]["color"]), "roughness": 0.9, "class": "textile"},
        "backing": {"color": tuple(k6["backing"]["color"]), "roughness": 1.0, "class": "void"},
        "foundation": {"color": (0.55, 0.30, 0.22), "roughness": 0.92, "class": "masonry"},
        "roof": {"color": (0.24, 0.25, 0.27), "roughness": 0.8, "class": "roof"},
        "backdrop": {"color": (0.78, 0.76, 0.72), "roughness": 0.95, "class": "board"},
        "plaster": {"color": (0.86, 0.84, 0.79), "roughness": 0.95, "class": "board"},
        "cut": {"color": (0.62, 0.5, 0.36), "roughness": 0.95, "class": "unpainted"},
    })
    return out


def seed_of(component_id: str, index: int, structure_id: str = "k16_timber_kit") -> int:
    """K01's seed rule (k01_contract.json `seed`)."""
    return int(hashlib.sha256(f"{structure_id}|{component_id}|{index}".encode()).hexdigest()[:8], 16)


def unit01(seed: int, *salt) -> float:
    h = hashlib.sha256(f"{seed}|{'|'.join(str(s) for s in salt)}".encode()).hexdigest()[:8]
    return int(h, 16) / 0xFFFFFFFF


def support_of(fam: dict, length: float) -> float:
    """How far the course below holds a lapped board off the sheathing: the fixed point
    of the lap, where a board's front at one exposure above its butt is exactly the
    next board's support. `length` is the board's full width up the wall."""
    E, butt, tip = fam["exposure_m"], fam["butt_m"], fam["tip_m"]
    lap = length - E
    return (tip * length + (butt - tip) * lap) / E


def clapboard_support(cl: dict) -> float:
    return support_of(cl, cl["exposure_m"] + cl["lap_m"])


def shingle_support(sh: dict) -> float:
    return support_of(sh, sh["length_m"])


def absorb(dst: Prim, src: Prim, keep=None) -> None:
    """Append src's faces to dst (T-2323: a second opening on a wall, and the parts of a
    house merged into one mesh). `keep(tri_pts)` may refuse a triangle."""
    base = len(dst.pos)
    dst.pos += src.pos
    dst.nrm += src.nrm
    dst.uv += src.uv
    dst.conf += src.conf
    dst.tone += src.tone
    for t in range(0, len(src.idx), 3):
        tri = src.idx[t:t + 3]
        if keep is None or keep([src.pos[i] for i in tri]):
            dst.idx += [base + i for i in tri]


# -- 2D helpers ---------------------------------------------------------------------------

def area2(poly) -> float:
    return K06.area2(poly)


def ccw(poly):
    return poly if area2(poly) > 0 else poly[::-1]


def ray_hit(poly, c, d):
    """The nearest point where the ray c + l*d (l > 0) meets the closed polygon."""
    best = None
    for i, a in enumerate(poly):
        b = poly[(i + 1) % len(poly)]
        ex, ey = b[0] - a[0], b[1] - a[1]
        den = d[0] * ey - d[1] * ex
        if abs(den) < 1e-14:
            continue
        ax, ay = a[0] - c[0], a[1] - c[1]
        lam = (ax * ey - ay * ex) / den
        mu = (ax * d[1] - ay * d[0]) / den
        if lam > 1e-12 and -1e-9 <= mu <= 1 + 1e-9 and (best is None or lam < best[0]):
            best = (lam, (c[0] + lam * d[0], c[1] + lam * d[1]))
    return best[1]


def ring_quads(outer, hole):
    """Triangulable quads covering a convex `outer` minus a convex `hole` inside it:
    rays from the hole's centre through every vertex of both, so each quad has one
    edge on the outer boundary and one on the hole's."""
    # fsum, not sum: Python 3.12 made float sum() compensated, so 3.11 (CI's gate) and
    # 3.12 disagree in the last bit and the specimen's bytes with them
    c = (math.fsum(p[0] for p in hole) / len(hole), math.fsum(p[1] for p in hole) / len(hole))
    angs = sorted({round(math.atan2(p[1] - c[1], p[0] - c[0]), 12) for p in list(outer) + list(hole)})
    o_pts, h_pts = [], []
    for a in angs:
        d = (math.cos(a), math.sin(a))
        o_pts.append(ray_hit(outer, c, d))
        h_pts.append(ray_hit(hole, c, d))
    n = len(angs)
    return [(o_pts[i], o_pts[(i + 1) % n], h_pts[(i + 1) % n], h_pts[i]) for i in range(n)]


def inside(p, poly) -> bool:
    """Whether point p lies inside the closed polygon (even-odd)."""
    hit = False
    for i, a in enumerate(poly):
        b = poly[(i + 1) % len(poly)]
        if (a[1] > p[1]) != (b[1] > p[1]) and p[0] < a[0] + (p[1] - a[1]) * (b[0] - a[0]) / (b[1] - a[1]):
            hit = not hit
    return hit


def clip_segment(a, b, poly):
    """The part of segment a-b inside the convex CCW polygon, or None."""
    t0, t1 = 0.0, 1.0
    dx, dy = b[0] - a[0], b[1] - a[1]
    for i, p in enumerate(poly):
        q = poly[(i + 1) % len(poly)]
        nx, ny = -(q[1] - p[1]), q[0] - p[0]          # inward normal of a CCW edge
        num = nx * (a[0] - p[0]) + ny * (a[1] - p[1])
        den = nx * dx + ny * dy
        if abs(den) < 1e-14:
            if num < 0:
                return None
            continue
        t = -num / den
        if den > 0:
            t0 = max(t0, t)
        else:
            t1 = min(t1, t)
        if t0 > t1 - 1e-9:
            return None
    return ((a[0] + t0 * dx, a[1] + t0 * dy), (a[0] + t1 * dx, a[1] + t1 * dy))


def arc(cx, cy, rx, ry, a0, a1, n):
    return [(cx + rx * math.cos(a0 + (a1 - a0) * i / n), cy + ry * math.sin(a0 + (a1 - a0) * i / n))
            for i in range(n + 1)]


def octagon(a, c):
    """A square of half-side a with its corners chamfered by c, CCW, in (ds, dz)."""
    return [(a - c, -a), (a, -(a - c)), (a, a - c), (a - c, a), (-(a - c), a), (-a, a - c),
            (-a, -(a - c)), (-(a - c), -a)]


# -- frames: a wall face's own coordinates -----------------------------------------------------

class Frame:
    """s along the wall (to a viewer's right), y up, z out of the wall; origin on the
    sheathing at the left end, at grade."""

    def __init__(self, name, origin, u, n):
        self.name, self.O, self.u, self.n = name, origin, _unit(u), _unit(n)

    def P(self, s, y, z):
        return (self.O[0] + self.u[0] * s + self.n[0] * z, self.O[1] + y,
                self.O[2] + self.u[2] * s + self.n[2] * z)

    def V(self, ds, dy, dz):
        return (self.u[0] * ds + self.n[0] * dz, dy, self.u[2] * ds + self.n[2] * dz)

    def local(self, p):
        d = _sub(p, self.O)
        return (_dot(d, self.u), d[1], _dot(d, self.n))

    def record(self):
        return {"name": self.name, "origin": [round(c, 6) for c in self.O],
                "u": [round(c, 6) for c in self.u], "n": [round(c, 6) for c in self.n]}


# -- the builder ---------------------------------------------------------------------------------

class Sample:
    def __init__(self, variant: dict, data: dict, origin=(0.0, 0.0, 0.0), index: int = 0):
        self.v, self.data, self.O = variant, data, origin
        self.prims: dict[str, Prim] = {}
        self.seed = seed_of(variant["id"], index)
        self.F = Frame("front", origin, (1.0, 0.0, 0.0), (0.0, 0.0, 1.0))
        self.meta: dict = {"frames": [], "courses": [], "boards": [], "battens": [], "piercings": [],
                           "lattice": [], "focus": [0.0, 1.5, 0.0], "span_m": 2.0}

    # faces ------------------------------------------------------------------------
    def face(self, role, pts, hint, tone=1.0):
        n = (0.0, 0.0, 0.0)
        for i, a in enumerate(pts):
            b = pts[(i + 1) % len(pts)]
            n = _add(n, ((a[1] - b[1]) * (a[2] + b[2]), (a[2] - b[2]) * (a[0] + b[0]),
                         (a[0] - b[0]) * (a[1] + b[1])))
        if math.sqrt(_dot(n, n)) < 1e-12:
            return
        n = _unit(n)
        if _dot(n, hint) < 0:   # turn it round, keeping the first vertex: a fan stays a fan
            n = _mul(n, -1)
            pts = [pts[0]] + list(reversed(pts[1:]))
        au = _cross(Y, n)
        au = _unit(au) if _dot(au, au) > 1e-9 else (1.0, 0.0, 0.0)
        av = _cross(n, au)
        pr = self.prims.setdefault(role, Prim(role))
        pr.face(list(pts), n, (pts[0], au, av, 1.0, 1.0, 0.0, 0.0), RECONSTRUCTED)
        for k in range(len(pts)):
            pr.tone[-1 - k] = tone

    def poly(self, F, role, pts, hint, tone=1.0):
        self.face(role, [F.P(*p) for p in pts], F.V(*hint), tone)

    def box(self, F, role, s0, s1, y0, y1, z0, z1, skip=(), tone=1.0, roles=None):
        """An axis box in frame F; `roles` may name another role per face."""
        roles = roles or {}
        faces = {
            "front": ([(s0, y0, z1), (s1, y0, z1), (s1, y1, z1), (s0, y1, z1)], (0, 0, 1)),
            "back": ([(s0, y0, z0), (s0, y1, z0), (s1, y1, z0), (s1, y0, z0)], (0, 0, -1)),
            "s0": ([(s0, y0, z0), (s0, y0, z1), (s0, y1, z1), (s0, y1, z0)], (-1, 0, 0)),
            "s1": ([(s1, y0, z0), (s1, y1, z0), (s1, y1, z1), (s1, y0, z1)], (1, 0, 0)),
            "bottom": ([(s0, y0, z0), (s1, y0, z0), (s1, y0, z1), (s0, y0, z1)], (0, -1, 0)),
            "top": ([(s0, y1, z0), (s0, y1, z1), (s1, y1, z1), (s1, y1, z0)], (0, 1, 0)),
        }
        for k, (pts, h) in faces.items():
            if k not in skip:
                self.poly(F, roles.get(k, role), pts, h, tone)

    def profile_run(self, F, profile, edge_roles, s0, s1, cap_roles=(None, None), tone=1.0):
        """A CCW profile in (z, y) extruded along s from s0 to s1. edge_roles[i] names
        the role of the face on profile edge i (None: hidden, not built)."""
        n = len(profile)
        for i in range(n):
            r = edge_roles[i]
            if not r:
                continue
            (za, ya), (zb, yb) = profile[i], profile[(i + 1) % n]
            hint = (0.0, -(zb - za), (yb - ya))   # outward normal of a CCW edge, as (s, y, z)
            self.poly(F, r, [(s0, ya, za), (s1, ya, za), (s1, yb, zb), (s0, yb, zb)], hint, tone)
        if cap_roles[0]:
            self.poly(F, cap_roles[0], [(s0, y, z) for z, y in profile], (-1, 0, 0), tone)
        if cap_roles[1]:
            self.poly(F, cap_roles[1], [(s1, y, z) for z, y in profile], (1, 0, 0), tone)

    def mitred_run(self, Ff, Fr, profile, edge_roles, s0, corner, depth, cap_roles=(None, None), tone=1.0):
        """A profile run along the front frame from s0 to an outside corner at `corner`,
        mitred there, and back along the return frame to `depth`. The two pieces meet on
        the mitre plane; their mitre faces are hidden against each other and not built."""
        n = len(profile)
        for i in range(n):
            r = edge_roles[i]
            if not r:
                continue
            (za, ya), (zb, yb) = profile[i], profile[(i + 1) % n]
            hint = (0.0, -(zb - za), (yb - ya))
            self.poly(Ff, r, [(s0, ya, za), (corner + za, ya, za), (corner + zb, yb, zb), (s0, yb, zb)], hint, tone)
            self.poly(Fr, r, [(-za, ya, za), (depth, ya, za), (depth, yb, zb), (-zb, yb, zb)], hint, tone)
        if cap_roles[0]:
            self.poly(Ff, cap_roles[0], [(s0, y, z) for z, y in profile], (-1, 0, 0), tone)
        if cap_roles[1]:
            self.poly(Fr, cap_roles[1], [(depth, y, z) for z, y in profile], (1, 0, 0), tone)

    def bracket(self, F, s_c, z_face, y_top, br, thick, along_s=False, outward=1.0, tone=1.0):
        """A scroll bracket. Its profile is star-shaped from the corner where it meets
        its carrier and the member over it, so one fan covers each side face. Normally
        the profile stands in (z, y) at s = s_c (an eave bracket off a wall); with
        `along_s` it stands in (s, y) at z = z_face (a porch bracket off a post face at
        s_c, reaching `outward`)."""
        R, D, w, nseg = br["reach_m"], br["drop_m"], br["web_m"], br["curve_segments"]
        prof = [(0.0, 0.0), (R, 0.0), (R, -w)]
        prof += arc(R, -D, R - w, D - w, math.pi / 2, math.pi, nseg)[1:]
        prof += [(0.0, -D)]
        hidden = {0, len(prof) - 1}            # the edge under the member, the edge on the carrier
        if not along_s:
            def P(o, dy, side):
                return (s_c + side * thick / 2, y_top + dy, z_face + o)
            sides = ((-1, (-1, 0, 0)), (1, (1, 0, 0)))
        else:
            def P(o, dy, side):
                return (s_c + outward * o, y_top + dy, z_face + side * thick / 2)
            sides = ((-1, (0, 0, -1)), (1, (0, 0, 1)))
        for side, h in sides:
            self.poly(F, "bracket", [P(o, dy, side) for o, dy in prof], h, tone)
        n = len(prof)
        orient = 1.0 if area2(prof) > 0 else -1.0   # the profile runs clockwise
        for i in range(n):
            if i in hidden:
                continue
            a, b = prof[i], prof[(i + 1) % n]
            ex, ey = b[0] - a[0], b[1] - a[1]
            nx, ny = orient * ey, -orient * ex       # the edge's outward normal
            hint = (outward * nx, ny, 0.0) if along_s else (0.0, ny, nx)
            self.poly(F, "bracket", [P(a[0], a[1], -1), P(b[0], b[1], -1), P(b[0], b[1], 1), P(a[0], a[1], 1)],
                      hint, tone)

    def tone(self, *salt):
        lo, hi = self.data["paint"]["wear"]["tone_range"]
        return round(hi - (hi - lo) * unit01(self.seed, *salt), 4)

    # cladding -----------------------------------------------------------------------
    def clapboards(self, F, s0, s1, y_start, y_end, ends=("trim", "trim"), cuts=(), course0=0, span=None):
        """Courses from y_start to y_end across s0-s1. T-2398: `span(y0)` may narrow a course
        to (a, b), both ends cut, or drop it (None): a gable's courses shortening to its rake."""
        cl = self.data["cladding"]["clapboard"]
        E, butt, L = cl["exposure_m"], cl["butt_m"], cl["board_length_m"]
        step, minp, gap = cl["stagger_step_m"], cl["min_piece_m"], cl["joint_gap_m"]
        sup = clapboard_support(cl)
        Z0, k = sup + butt, butt / E
        n = int(math.ceil((y_end - y_start) / E - 1e-9))
        self.meta["frames"].append(dict(F.record(), family="clapboard", s=[s0, s1], y=[y_start, y_end]))
        for i in range(n):
            ci = course0 + i
            y0 = y_start + i * E
            y1 = min(y0 + E, y_end)
            ivs = [(s0, s1, ends[0], ends[1])]
            if span is not None:
                ab = span(y0)
                if ab is None:
                    continue
                ivs = [(ab[0], ab[1], "cut", "cut")]
            for (sa, sb, ya, yb) in cuts:
                if y0 >= ya - 1e-6 and y0 + E <= yb + 1e-6:
                    nxt = []
                    for (a, b, ka, kb) in ivs:
                        if sb <= a or sa >= b:
                            nxt.append((a, b, ka, kb))
                            continue
                        if sa > a:
                            nxt.append((a, sa, ka, "trim"))
                        if sb < b:
                            nxt.append((sb, b, "trim", kb))
                    ivs = nxt
            off = (ci * step) % L
            series = [off + m * L for m in range(-2, int((s1 - s0) / L) + 3)]
            joints = []
            pieces = []
            for (a, b, ka, kb) in ivs:
                js = [s0 + j for j in series if a + minp < s0 + j < b - minp]
                # T-2323: a joint dropped for falling within min_piece of an end can leave a
                # board longer than it comes; put one back where both pieces stay whole
                at = [a] + js + [b]
                for m in range(len(at) - 1, 0, -1):
                    if at[m] - at[m - 1] > L + 1e-9:
                        at.insert(m, max(at[m - 1] + minp, min(at[m - 1] + L, at[m] - minp)))
                js = at[1:-1]
                cutsat = [a] + js + [b]
                kinds = [ka] + ["joint"] * len(js) + [kb]
                for j in range(len(cutsat) - 1):
                    p = cutsat[j] + (gap / 2 if kinds[j] == "joint" else 0.0)
                    q = cutsat[j + 1] - (gap / 2 if kinds[j + 1] == "joint" else 0.0)
                    pieces.append((p, q, kinds[j], kinds[j + 1]))
                joints += js
            zt = Z0 - k * (y1 - y0)
            for pi, (p, q, kp, kq) in enumerate(pieces):
                t = self.tone("clap", F.name, ci, pi)
                self.poly(F, "clapboard", [(p, y0, Z0), (q, y0, Z0), (q, y1, zt), (p, y1, zt)], (0, k, 1), t)
                self.poly(F, "clapboard_butt", [(p, y0, sup), (q, y0, sup), (q, y0, Z0), (p, y0, Z0)], (0, -1, 0), t)
                # the end of a board at a joint or a cut is end grain; at trim it is hidden
                back_top = sup * (1 - (y1 - y0) / (E + cl["lap_m"]))
                sec = [(y0, sup), (y0, Z0), (y1, zt), (y1, back_top)]
                for s_end, kind, hs in ((p, kp, -1), (q, kq, 1)):
                    if kind in ("joint", "cut"):
                        self.poly(F, "end_grain", [(s_end, yy, zz) for yy, zz in sec], (hs, 0, 0), t)
            self.meta["courses"].append({"family": "clapboard", "frame": F.name, "course": ci,
                                         "y0": round(y0, 6), "y1": round(y1, 6), "front_butt": round(Z0, 6),
                                         "support": round(sup, 6), "joints": [round(j, 6) for j in joints],
                                         "pieces": [[round(p, 6), round(q, 6)] for p, q, _, _ in pieces]})
        return sup, Z0

    def smooth_board(self, F, s0, s1, y_start, y_end, cuts=(), incised=()):
        """T-2521: a smooth painted face from y_start to y_end across s0-s1, flush boards laid on
        the clapboard's course lines (each its own paint tone), standing where the clapboard's butts would so the casing and the corner boards keep their reveal over it,
        and cut by the strips a pointed head cuts its courses by, so its edges stand under the
        band. Each `incised` ornament is a trefoil cut into it, one lobe up: a groove `groove_m`
        wide and `depth_m` deep round three lobes `lobe_r_m` in radius whose middles stand
        `lobe_off_m` from its centre (`centre_m`, `centre_y_m`)."""
        cl = self.data["cladding"]["clapboard"]
        zf = clapboard_support(cl) + cl["butt_m"]
        boxes, cut_in = [], []
        for o in incised:
            lobes = [(o["lobe_off_m"] * math.cos(math.radians(a)), o["lobe_off_m"] * math.sin(math.radians(a)))
                     for a in (90, 210, 330)]

            def radius(a, d, lobes=lobes, rl=o["lobe_r_m"]):     # out to the lobes' outline, inset by d
                u = (math.cos(a), math.sin(a))
                best = 0.0
                for lx, ly in lobes:
                    b = u[0] * lx + u[1] * ly
                    disc = (rl - d) ** 2 - (lx * lx + ly * ly - b * b)
                    if disc >= 0:
                        best = max(best, b + math.sqrt(disc))
                return best
            c, n = (o["centre_m"], o["centre_y_m"]), 60
            angs = [2 * math.pi * k / n for k in range(n)]
            outer = [(c[0] + radius(a, 0.0) * math.cos(a), c[1] + radius(a, 0.0) * math.sin(a)) for a in angs]
            inner = [(c[0] + radius(a, o["groove_m"]) * math.cos(a), c[1] + radius(a, o["groove_m"]) * math.sin(a))
                     for a in angs]
            m = 0.01
            box = (min(x for x, _ in outer) - m, max(x for x, _ in outer) + m,
                   min(y for _, y in outer) - m, max(y for _, y in outer) + m)
            if box[0] < s0 or box[1] > s1 or box[2] < y_start or box[3] > y_end or any(
                    not (box[1] <= ha or box[0] >= hb or box[3] <= hy0 or box[2] >= hy1) for ha, hb, hy0, hy1 in cuts) \
                    or any(box[2] < cs["y"][1] and not (box[1] <= cs["s"][0] or box[0] >= cs["s"][1])
                           for cs in self.meta.get("casings", [])):     # clear of each casing's band
                raise ValueError(f"{self.v['id']}: the incised trefoil at {c} does not stand clear on the board")
            boxes.append(box)
            cut_in.append((c, outer, inner, o["depth_m"]))
        # flush boards on the clapboard's course lines, each its own paint tone, the openings and
        # each ornament's field cut from them as the courses are cut
        E = cl["exposure_m"]
        rects = [(s0, s1, y_start, y_end)]
        for (ha, hb, hy0, hy1) in list(cuts) + boxes:
            nxt = []
            for (a, b, c0, d0) in rects:
                if hb <= a or ha >= b or hy1 <= c0 or hy0 >= d0:
                    nxt.append((a, b, c0, d0))
                    continue
                nxt += [r for r in ((a, b, c0, hy0), (a, b, hy1, d0), (a, ha, max(c0, hy0), min(d0, hy1)),
                                    (hb, b, max(c0, hy0), min(d0, hy1))) if r[1] - r[0] > 1e-9 and r[3] - r[2] > 1e-9]
            rects = nxt
        for (a, b, c0, d0) in rects:
            k0, k1 = int(math.floor((c0 - y_start) / E + 1e-9)), int(math.ceil((d0 - y_start) / E - 1e-9))
            for k in range(k0, k1):
                ya, yb = max(c0, y_start + k * E), min(d0, y_start + (k + 1) * E)
                if yb - ya > 1e-9:
                    self.poly(F, "board", [(a, ya, zf), (b, ya, zf), (b, yb, zf), (a, yb, zf)], (0, 0, 1),
                              self.tone("smooth", F.name, k))
        for (c, outer, inner, dp), (a0, a1, b0, b1) in zip(cut_in, boxes):
            tone = self.tone("smooth", F.name, int(math.floor((c[1] - y_start) / E)))
            rect = [(a0, b0), (a1, b0), (a1, b1), (a0, b1)]
            pts = rect + outer
            for tri in K09.triangulate(rect, [outer]):
                self.poly(F, "board", [(*pts[i], zf) for i in tri], (0, 0, 1), tone)
            n, zb = len(outer), zf - dp
            for k in range(n):
                o0, o1, i0, i1 = outer[k], outer[(k + 1) % n], inner[k], inner[(k + 1) % n]
                mx, my = (o0[0] + o1[0]) / 2 - c[0], (o0[1] + o1[1]) / 2 - c[1]
                self.poly(F, "board", [(c[0], c[1], zf), (i0[0], i0[1], zf), (i1[0], i1[1], zf)], (0, 0, 1), tone)
                # the groove: its floor and its two walls, in the board's paint (the bake's occlusion
                # is what shades a cut, as it shades every other recess in the house)
                self.poly(F, "board", [(i0[0], i0[1], zb), (o0[0], o0[1], zb), (o1[0], o1[1], zb), (i1[0], i1[1], zb)],
                          (0, 0, 1), tone)
                self.poly(F, "board", [(o0[0], o0[1], zb), (o1[0], o1[1], zb), (o1[0], o1[1], zf), (o0[0], o0[1], zf)],
                          (-mx, -my, 0), tone)
                self.poly(F, "board", [(i0[0], i0[1], zb), (i1[0], i1[1], zb), (i1[0], i1[1], zf), (i0[0], i0[1], zf)],
                          (mx, my, 0), tone)
        self.meta.setdefault("smooth", []).append({"frame": F.name, "s": [s0, s1], "y": [y_start, y_end],
                                                    "face_z": round(zf, 6), "incised": len(cut_in)})

    def shingles(self, F, clip_poly, y_start, bands, s_mid):
        sh = self.data["cladding"]["shingle"]
        E, w, butt, nseg = sh["exposure_m"], sh["width_m"], sh["butt_m"], sh["arc_segments"]
        sup = shingle_support(sh)
        Z0, k = sup + butt, butt / E
        clip_poly = ccw(clip_poly)
        top = max(p[1] for p in clip_poly)
        lo_s, hi_s = min(p[0] for p in clip_poly), max(p[0] for p in clip_poly)
        self.meta["frames"].append(dict(F.record(), family="shingle", s=[lo_s, hi_s], y=[y_start, top]))
        seq = []
        for b in bands:
            seq += [b["pattern"]] * b["courses"]
        i = 0
        while y_start + i * E < top - 1e-6 and i < len(seq):
            y0 = y_start + i * E
            pat = seq[i]
            half = 0.5 * w if i % 2 else 0.0
            j0 = int(math.floor((lo_s - s_mid - half) / w)) - 1
            j1 = int(math.ceil((hi_s - s_mid - half) / w)) + 1
            y_top = y0 + E + w / 2 + 0.01
            joints = []
            for j in range(j0, j1 + 1):
                c = s_mid + half + j * w
                if pat == "fishscale":
                    r = w / 2
                    butt_line = arc(c, y0 + r, r, r, math.pi, 2 * math.pi, nseg)
                else:
                    butt_line = [(c - w / 2, y0), (c + w / 2, y0)]
                shape = butt_line + [(c + w / 2, y_top), (c - w / 2, y_top)]
                cl = K06.clip(ccw(shape), clip_poly)
                if len(cl) < 3 or abs(area2(cl)) < 1e-7:
                    continue
                t = self.tone("shingle", i, j)
                self.poly(F, "shingle", [(s, y, Z0 - k * (y - y0)) for s, y in cl], (0, k, 1), t)
                for a, b in zip(butt_line, butt_line[1:]):
                    seg = clip_segment(a, b, clip_poly)
                    if not seg:
                        continue
                    (sa, ya), (sb, yb) = seg
                    if math.dist(seg[0], seg[1]) < 1e-6:
                        continue
                    nx, ny = (yb - ya), -(sb - sa)        # outward (below) for a left-to-right butt
                    za, zb = Z0 - k * (ya - y0), Z0 - k * (yb - y0)
                    self.poly(F, "shingle_butt", [(sa, ya, za - butt), (sb, yb, zb - butt), (sb, yb, zb), (sa, ya, za)],
                              (nx, ny, 0), t)
                if lo_s < c - w / 2 < hi_s:
                    joints.append(c - w / 2)
            self.meta["courses"].append({"family": "shingle", "frame": F.name, "course": i, "pattern": pat,
                                         "y0": round(y0, 6), "y1": round(y0 + E, 6), "front_butt": round(Z0, 6),
                                         "support": round(sup, 6), "joints": [round(j, 6) for j in joints]})
            i += 1
        return sup, Z0

    def sheathing(self, F, outline, holes=(), role="sheathing", z=0.0, hint_z=1):
        """A wall plane: a rectangle (s0, s1, y0, y1) with rectangular holes cut from it
        by strips, or a convex polygon with none."""
        if isinstance(outline, tuple):
            s0, s1, y0, y1 = outline
            rects = [(s0, s1, y0, y1)]
            for (ha, hb, hy0, hy1) in holes:
                nxt = []
                for (a, b, c, d) in rects:
                    if hb <= a or ha >= b or hy1 <= c or hy0 >= d:
                        nxt.append((a, b, c, d))
                        continue
                    if c < hy0:
                        nxt.append((a, b, c, hy0))
                    if d > hy1:
                        nxt.append((a, b, hy1, d))
                    if a < ha:
                        nxt.append((a, ha, max(c, hy0), min(d, hy1)))
                    if b > hb:
                        nxt.append((hb, b, max(c, hy0), min(d, hy1)))
                rects = nxt
            for (a, b, c, d) in rects:
                self.poly(F, role, [(a, c, z), (b, c, z), (b, d, z), (a, d, z)], (0, 0, hint_z))
        else:
            self.poly(F, role, [(s, y, z) for s, y in outline], (0, 0, hint_z))

    # samples ----------------------------------------------------------------------
    def build(self):
        getattr(self, "_" + self.v["kind"])()
        return self

    def _base(self, F, s0, s1, y_fd, T, caps=("cut", "cut"), Fr=None, corner=None, depth=None):
        """Foundation, water table and its drip cap; returns where cladding starts."""
        wt = self.data["trim"]["water_table"]
        t, h = wt["thickness_m"], wt["height_m"]
        cap = wt["cap"]
        y1 = y_fd + h
        zc = t + cap["projection_m"]
        y_start = y1 + cap["height_m"]
        found = [(-T, 0.0), (t, 0.0), (t, y_fd), (-T, y_fd)]
        board = [(0.0, y_fd), (t, y_fd), (t, y1), (0.0, y1)]
        drip = [(0.0, y1), (zc, y1), (zc, y_start - cap["fall_m"]), (0.0, y_start)]
        runs = ((found, [None, "foundation", None, None], ("foundation", "foundation")),
                (board, [None, "water_table", None, None], caps),
                (drip, ["drip_cap", "drip_cap", "drip_cap", None], caps))
        for ri, (prof, roles, cp) in enumerate(runs):
            cp = tuple("end_grain" if c == "cut" and ri else c for c in cp)
            if Fr is None:
                self.profile_run(F, prof, roles, s0, s1, cp, self.tone("base", ri))
            else:
                self.mitred_run(F, Fr, prof, roles, s0, corner, depth, cp, self.tone("base", ri))
        return y_start

    def _clapboard_wall(self):
        v, d = self.v, self.data
        tr, T = d["trim"], d["wall"]["thickness_m"]
        cl = d["cladding"]["clapboard"]
        E = cl["exposure_m"]
        W, D, y_fd, y_s = v["width_m"], v["return_m"], v["foundation_m"], v["wall_top_m"]
        F = self.F
        # T-2357: a wall with no return (`return_m` 0) runs straight and ends cut, where a
        # house's wall dies into another wall instead of turning an outside corner
        corner = D > 0
        R = Frame("return", F.P(W, 0, 0), (0.0, 0.0, -1.0), (1.0, 0.0, 0.0)) if corner else None
        if corner:
            y_start = self._base(F, 0.0, W, y_fd, T, ("cut", "cut"), R, W, D)
        else:
            y_start = self._base(F, 0.0, W, y_fd, T)
        fr = dict(tr["frieze"], **({"height_m": v["frieze_m"]} if "frieze_m" in v else {}))   # T-2521
        y_fr0 = y_s - fr["height_m"]
        cb, ct = tr["corner_board"]["width_m"], tr["corner_board"]["thickness_m"]

        # the cased windows: K06's sash in a K16 casing (one on the specimen; T-2323 a list)
        holes, cuts = [], []
        for win in (v["windows"] if "windows" in v else [v["window"]]):
            hole, cut = self._cased_window(F, win, y_start)
            holes.append(hole)
            cuts.extend(cut if isinstance(cut, list) else [cut])    # T-2424: a pointed head's courses
        for door in v.get("doors") or []:   # T-2357: a panelled door in a K16 casing
            hole, cut = self._cased_door(F, door, y_start)
            holes.append(hole)
            cuts.append(cut)

        # walls: sheathing, interior, the specimen's two cuts
        self.sheathing(F, (0.0, W, y_fd, y_s), holes)
        if corner:
            self.sheathing(R, (0.0, D, y_fd, y_s))
        self.sheathing(F, (0.0, W - T if corner else W, y_fd, y_s), holes, role="interior", z=-T, hint_z=-1)
        if corner:
            self.sheathing(R, (T, D, y_fd, y_s), role="interior", z=-T, hint_z=-1)
        self.poly(F, "cut", [(0, y_fd, -T), (0, y_fd, 0), (0, y_s, 0), (0, y_s, -T)], (-1, 0, 0))
        if corner:
            self.poly(R, "cut", [(D, y_fd, -T), (D, y_s, -T), (D, y_s, 0), (D, y_fd, 0)], (1, 0, 0))
        else:
            self.poly(F, "cut", [(W, y_fd, -T), (W, y_s, -T), (W, y_s, 0), (W, y_fd, 0)], (1, 0, 0))

        # clapboard, front and return, and the corner boards between them
        if corner:
            self.clapboards(F, 0.0, W - cb + ct, y_start, y_fr0, ("cut", "trim"), cuts)
            self.clapboards(R, cb - ct, D, y_start, y_fr0, ("trim", "cut"))
            tc = self.tone("corner")
            self.box(F, "corner_board", W - cb + ct, W + ct, y_start, y_fr0, 0, ct, skip=("back", "top"), tone=tc)
            self.box(R, "corner_board", 0.0, cb - ct, y_start, y_fr0, 0, ct, skip=("back", "top", "s0"), tone=tc)
        else:
            # T-2395: a wall with no return may still end on an outside corner, where its own
            # corner board stands (`boards`: [at its start, at its end]) and the neighbouring
            # face's cladding or board dies against it
            b0, b1 = (v.get("boards") or (False, False))
            a, b = (cb - ct if b0 else 0.0), (W - cb + ct if b1 else W)
            if v.get("cladding") == "smooth":     # T-2521: a smooth board, its ornament incised
                self.smooth_board(F, a, b, y_start, y_fr0, cuts, v.get("incised") or [])
            else:
                self.clapboards(F, a, b, y_start, y_fr0, ("trim" if b0 else "cut", "trim" if b1 else "cut"), cuts)
            tc = self.tone("corner")
            if b0:
                self.box(F, "corner_board", -ct, cb - ct, y_start, y_fr0, 0, ct, skip=("back", "top"), tone=tc)
            if b1:
                self.box(F, "corner_board", W - cb + ct, W + ct, y_start, y_fr0, 0, ct, skip=("back", "top"), tone=tc)

        # frieze, boxed eave, brackets
        ft = fr["thickness_m"]
        ev = dict(tr["eave"], **(v.get("eave") or {}))     # T-3182: a house's own deeper eave
        P_, fh = ev["projection_m"], ev["fascia_m"]
        frieze = ([(0.0, y_fr0), (ft, y_fr0), (ft, y_s), (0.0, y_s)], ["frieze", "frieze", None, None])
        eave = ([(0.0, y_s), (P_, y_s), (P_, y_s + fh), (0.0, y_s + fh)], ["soffit", "fascia", "roof", None])
        for (prof, roles), caps, key in ((frieze, ("end_grain", "end_grain"), "frieze"), (eave, ("cut", "cut"), "eave")):
            if corner:
                self.mitred_run(F, R, prof, roles, 0.0, W, D, caps, self.tone(key))
            else:
                self.profile_run(F, prof, roles, 0.0, W, caps, self.tone(key))
        br = dict(tr["bracket"], **(v.get("bracket") or {}))
        sp = br["spacing_m"]
        nb = int((W - 0.8) / sp) + 1
        first = (W - (nb - 1) * sp) / 2
        at = [first + kb * sp for kb in range(nb)]
        if v.get("bracket_pairs_m") is not None:     # T-3182: brackets in pairs where the photograph has them
            at = [p + e * br["pair_m"] / 2 for p in v["bracket_pairs_m"] for e in (-1, 1)]
        for kb, s_b in enumerate(at):
            self.bracket(F, s_b, ft, y_s, br, br["thickness_m"], tone=self.tone("bracket", kb))
        for fl in v.get("frieze_lights") or []:
            self._frieze_light(F, fl, ft)
        if corner:
            self.bracket(R, (cb - ct + D) / 2, ft, y_s, br, br["thickness_m"], tone=self.tone("bracket", "r"))
        self.meta["eave"] = {"y_top": y_s + fh, "projection_m": P_}   # T-2323
        self.meta.update({"wall_thickness_m": T, "focus": [W * 0.62, 2.1, 0.0], "span_m": 3.2})

    def _cased_window(self, F, win, y_start):
        """K06's sash in a K16 casing on frame F at win's centre_m and sill_m: sill, apron,
        casing and drip cap, the apron and cap ended on clapboard butt lines. Returns the
        hole it leaves in the sheathing and the rectangle it cuts from the clapboard."""
        tr = self.data["trim"]
        E = self.data["cladding"]["clapboard"]["exposure_m"]
        cs = tr["casing"]
        k6 = K06.load()
        kv = copy.deepcopy(next(x for x in k6["variants"] if x["id"] == win["k06_variant"]))
        kv["clear_height_m"] = win["clear_height_m"]
        if "clear_width_m" in win:     # T-2396: a narrow face's sash
            kv["clear_width_m"] = win["clear_width_m"]
        if "panes" in win:     # T-2424: a sash glazed otherwise than its K06 variant
            kv["panes"] = list(win["panes"])
        if "head_radius_ratio" in win:     # T-2457: a blunter (drop) pointed head
            kv["head_radius_ratio"] = win["head_radius_ratio"]
        kv.setdefault("overrides", {})["reveal_depth_m"] = cs["reveal_depth_m"]
        c, ys = win["centre_m"], win["sill_m"]
        op = CasedOpening(kv, k6, origin=F.P(c, ys, 0.0)).build()
        for role, pr in op.prims.items():
            if self.meta.get("casings") and role in self.prims:   # a second opening (T-2323)
                absorb(self.prims[role], pr)
            else:
                self.prims[role] = pr
        hw, H = kv["clear_width_m"] / 2, kv["clear_height_m"]
        rev = op.meta["reveal_depth_m"]
        sl = op.meta["sill_top_at_frame_m"] / rev
        cw, cth = cs["width_m"], cs["thickness_m"]
        sa, sb = c - hw - cw, c + hw + cw
        zf = cth + cs["sill"]["projection_m"]
        yf_top = ys - zf * sl
        ysb = yf_top - cs["sill"]["thickness_m"]
        line = lambda yy, up: y_start + E * (math.ceil((yy - y_start) / E - 1e-6) if up
                                             else math.floor((yy - y_start) / E + 1e-6))
        y_ap = line(ysb - cs["apron_m"], False)
        dc = cs["drip_cap"]
        y_top = line(ys + H + cs["head_m"] + dc["height_m"], True)
        yHc = y_top - dc["height_m"]
        yH = ys + H
        tw = self.tone("casing")
        # sill: its top falls outward along the line the K06 jambs stand on
        self.poly(F, "sill", [(c - hw, ys + rev * sl, -rev), (c + hw, ys + rev * sl, -rev), (c + hw, ys, 0), (c - hw, ys, 0)],
                  (0, 1, 0.1), tw)
        self.poly(F, "sill", [(sa, ys, 0), (sb, ys, 0), (sb, yf_top, zf), (sa, yf_top, zf)], (0, 1, 0.1), tw)
        self.poly(F, "sill", [(sa, ysb, zf), (sb, ysb, zf), (sb, yf_top, zf), (sa, yf_top, zf)], (0, 0, 1), tw)
        self.poly(F, "sill", [(sa, ysb, cth), (sb, ysb, cth), (sb, ysb, zf), (sa, ysb, zf)], (0, -1, 0), tw)
        for s_e, hs in ((sa, -1), (sb, 1)):
            self.poly(F, "end_grain", [(s_e, ysb, 0), (s_e, ysb, zf), (s_e, yf_top, zf), (s_e, ys, 0)], (hs, 0, 0), tw)
        self.box(F, "apron", sa, sb, y_ap, ysb, 0, cth, skip=("back", "top"), tone=tw,
                 roles={"s0": "end_grain", "s1": "end_grain"})
        if win.get("surround") == "pointed":     # T-2423: the casing carried round the head
            return self._pointed_surround(F, c, hw, H, ys, sl, sa, sb, y_ap, y_start, tw,
                                          win.get("head_radius_ratio", 1.0), win.get("stops"))
        if win.get("surround") == "round":       # T-3182: the casing carried round a round head
            return self._round_surround(F, win, kv, c, hw, H, ys, sl, sa, sb, y_ap, y_start, tw)
        for (a, b) in ((sa, c - hw), (c + hw, sb)):
            yb = ys - cth * sl
            self.poly(F, "casing", [(a, yb, cth), (b, yb, cth), (b, yH, cth), (a, yH, cth)], (0, 0, 1), tw)
            self.poly(F, "casing", [(a, ys, 0), (a, yb, cth), (a, yH, cth), (a, yH, 0)], (-1, 0, 0), tw)
            self.poly(F, "casing", [(b, ys, 0), (b, yb, cth), (b, yH, cth), (b, yH, 0)], (1, 0, 0), tw)
        self.box(F, "casing", sa, sb, yH, yHc, 0, cth, skip=("back", "top", "bottom"), tone=tw,
                 roles={"s0": "end_grain", "s1": "end_grain"})
        self.poly(F, "casing", [(c - hw, yH, 0), (c + hw, yH, 0), (c + hw, yH, cth), (c - hw, yH, cth)], (0, -1, 0), tw)
        zc = cth + dc["projection_m"]
        cap = [(0.0, yHc), (zc, yHc), (zc, yHc + dc["front_m"]), (0.0, y_top)]
        self.poly(F, "drip_cap", [(sa, yHc, cth), (sb, yHc, cth), (sb, yHc, zc), (sa, yHc, zc)], (0, -1, 0), tw)
        self.profile_run(F, cap, [None, "drip_cap", "drip_cap", None], sa, sb, ("end_grain", "end_grain"), tw)
        hole = (c - hw, c + hw, ys, ys + H)
        cut = (sa, sb, y_ap, y_top)
        self.meta["casing"] = {"s": [sa, sb], "y": [y_ap, y_top], "apron_m": round(ysb - y_ap, 6),
                               "head_m": round(yHc - yH, 6), "on_course_lines": True}
        self.meta.setdefault("casings", []).append(self.meta["casing"])
        return hole, cut

    def _pointed_surround(self, F, c, hw, H, ys, sl, sa, sb, y_ap, y_start, tw, ratio=1.0, stops=None):
        """T-2423: a pointed sash's casing carried round its head instead of squared off: the
        two jamb casings rise to the spring and an arched band of the casing's width follows
        the K06 equilateral head to its point, with no head board or drip cap (a hood mould
        over the opening sheds its water). The clapboard is cut course by course: the whole
        casing's width up to the spring, then each course to the clear arch at its foot, so
        every board end stands under the band. Returns the sheathing hole and the cuts.
        T-2457: `ratio` under 1 is a drop head (its arcs' radius that share of the span, as K06
        builds the sash), and `stops` a small block at each spring on the band's outer edge."""
        cs = self.data["trim"]["casing"]
        cw, cth = cs["width_m"], cs["thickness_m"]
        E = self.data["cladding"]["clapboard"]["exposure_m"]
        span = 2 * hw
        rise = K06.Head("pointed", -hw, hw, 0.0, radius_ratio=ratio).rise if ratio != 1.0 \
            else math.sqrt(span * span - hw * hw)
        R = span * ratio
        spring, top = ys + H - rise, ys + H
        yb = ys - cth * sl
        for (a, b) in ((sa, c - hw), (c + hw, sb)):
            self.poly(F, "casing", [(a, yb, cth), (b, yb, cth), (b, spring, cth), (a, spring, cth)], (0, 0, 1), tw)
            self.poly(F, "casing", [(a, ys, 0), (a, yb, cth), (a, spring, cth), (a, spring, 0)], (-1, 0, 0), tw)
            self.poly(F, "casing", [(b, ys, 0), (b, yb, cth), (b, spring, cth), (b, spring, 0)], (1, 0, 0), tw)
        hd = K06.Head("pointed", c - hw, c + hw, spring, radius_ratio=ratio)
        inner = hd.curve(0.0, c + hw, c - hw)
        outer = hd.curve(-cw, c + hw + cw, c - hw - cw)
        for (p0, p1), (q0, q1) in zip(zip(inner, inner[1:]), zip(outer, outer[1:])):
            mx, my = (p0[0] + p1[0]) / 2 - c, (p0[1] + p1[1]) / 2 - spring
            self.poly(F, "casing", [(p0[0], p0[1], cth), (q0[0], q0[1], cth), (q1[0], q1[1], cth), (p1[0], p1[1], cth)],
                      (0, 0, 1), tw)
            self.poly(F, "casing", [(q0[0], q0[1], 0), (q1[0], q1[1], 0), (q1[0], q1[1], cth), (q0[0], q0[1], cth)],
                      (mx, my, 0), tw)
            self.poly(F, "casing", [(p0[0], p0[1], 0), (p1[0], p1[1], 0), (p1[0], p1[1], cth), (p0[0], p0[1], cth)],
                      (-mx, -my, 0), tw)
        cuts, k = [], round((y_ap - y_start) / E)
        while y_start + k * E < top - 1e-6:
            y0 = y_start + k * E
            if y0 < spring - 1e-9:
                off = hw + cw
            elif ratio == 1.0:
                off = math.sqrt(max(0.0, span * span - (y0 - spring) ** 2)) - hw
            else:
                off = math.sqrt(max(0.0, R * R - (y0 - spring) ** 2)) - (R - hw)
            cuts.append((c - off, c + off, y0, y0 + E))
            k += 1
        apex_out = max(q[1] for q in outer)
        if stops:     # T-2457: a dark stop at each spring of the band, on its outer edge
            sw, sh, sp = stops["width_m"], stops["height_m"], stops["projection_m"]

            def clear(y):     # a level face never lies on a clapboard course's butt
                q = (y - y_start) / E
                return y + 0.006 if abs(q - round(q)) * E < 0.003 else y
            for e in (sa, sb):
                self.box(F, "stop", e - sw / 2, e + sw / 2, clear(spring - sh / 2), clear(spring + sh / 2), 0.0, cth + sp,
                         skip=("back",), tone=self.tone("stop", e))
        self.meta["casing"] = {"s": [sa, sb], "y": [y_ap, round(apex_out, 6)], "head": "pointed",
                               "spring_m": round(spring, 6), "on_course_lines": False}
        self.meta.setdefault("casings", []).append(self.meta["casing"])
        return (c - hw, c + hw, ys, top), cuts

    def _arch_band(self, F, cx, spring, r0, r1, z1, tone, legs=(0.0, 0.0), n=6, outer=True, z_in=0.0):
        """T-3182: a flat band applied to the cladding round a round head, from radius r0 to r1
        about (cx, spring) and standing z1 proud, over the half circle; `legs` carries its right
        and left ends straight down that far under the spring, each ended square. A band with
        another band round it builds no `outer` edge, and the one round it starts its inner
        edge at `z_in`, the inner band's face, so the two never share a face."""
        angs = [math.pi * k / n for k in range(n + 1)]
        inner = [(cx + r0 * math.cos(a), spring + r0 * math.sin(a)) for a in angs]
        outer = [(cx + r1 * math.cos(a), spring + r1 * math.sin(a)) for a in angs]
        if legs[0] > 0:
            inner, outer = [(cx + r0, spring - legs[0])] + inner, [(cx + r1, spring - legs[0])] + outer
        if legs[1] > 0:
            inner, outer = inner + [(cx - r0, spring - legs[1])], outer + [(cx - r1, spring - legs[1])]
        for k in range(len(inner) - 1):
            p0, p1, q0, q1 = inner[k], inner[k + 1], outer[k], outer[k + 1]
            mx, my = (q0[0] + q1[0]) / 2 - cx, (q0[1] + q1[1]) / 2 - spring
            self.poly(F, "casing", [(p0[0], p0[1], z1), (q0[0], q0[1], z1), (q1[0], q1[1], z1), (p1[0], p1[1], z1)],
                      (0, 0, 1), tone)
            if outer:
                self.poly(F, "casing", [(q0[0], q0[1], 0), (q1[0], q1[1], 0), (q1[0], q1[1], z1), (q0[0], q0[1], z1)],
                          (mx, my, 0), tone)
            zi = z_in
            self.poly(F, "casing", [(p0[0], p0[1], zi), (p1[0], p1[1], zi), (p1[0], p1[1], z1), (p0[0], p0[1], z1)],
                      (-mx, -my, 0), tone)
        for end, on in ((0, legs[0] > 0), (-1, legs[1] > 0)):     # a leg's foot, ended square
            if on:
                p, q = inner[end], outer[end]
                self.poly(F, "casing", [(p[0], p[1], 0), (q[0], q[1], 0), (q[0], q[1], z1), (p[0], p[1], z1)],
                          (0, -1, 0), tone)

    def _round_surround(self, F, win, kv, c, hw, H, ys, sl, sa, sb, y_ap, y_start, tw):
        """T-3182: a round-headed sash's casing carried round its head, as 1720 Prairie's
        photograph shows every front window: the jamb casings (and, between a pair's lights,
        the mullion's) rise to the spring and a band of the casing's width follows each light's
        half circle, with no head board or drip cap. `hood_mould` sets a moulded band round
        the casing's (width_m, projection_m), its outer ends carried `legs_m` down the jambs.
        The clapboard is cut course by course to the clear head at each course's foot, as the
        pointed surround's is, so every board end stands under the band."""
        cs = self.data["trim"]["casing"]
        cw, cth = cs["width_m"], cs["thickness_m"]
        E = self.data["cladding"]["clapboard"]["exposure_m"]
        bays, mull = kv.get("bays", 1), kv.get("mullion_m", 0.0)
        bw = (2 * hw - mull * (bays - 1)) / bays
        r = bw / 2
        top = ys + H
        spring = top - r
        heads = [c - hw + r + k * (bw + mull) for k in range(bays)]
        yb = ys - cth * sl
        jambs = [(sa, c - hw), (c + hw, sb)] + [(x + r, x + r + mull) for x in heads[:-1]]
        for (a, b) in jambs:
            self.poly(F, "casing", [(a, yb, cth), (b, yb, cth), (b, spring, cth), (a, spring, cth)], (0, 0, 1), tw)
            self.poly(F, "casing", [(a, ys, 0), (a, yb, cth), (a, spring, cth), (a, spring, 0)], (-1, 0, 0), tw)
            self.poly(F, "casing", [(b, ys, 0), (b, yb, cth), (b, spring, cth), (b, spring, 0)], (1, 0, 0), tw)
        hm = win.get("hood_mould")
        for k, x in enumerate(heads):     # a pair's bands meet over the mullion: the second stands a hair proud
            self._arch_band(F, x, spring, r, r + cw, cth + 0.003 * k, tw, outer=not hm)
        y_out = spring + r + cw
        if hm:
            th = self.tone("hood_mould")
            for k, x in enumerate(heads):
                legs = (hm["legs_m"] if k == bays - 1 else 0.0, hm["legs_m"] if k == 0 else 0.0)
                self._arch_band(F, x, spring, r + cw, r + cw + hm["width_m"], cth + hm["projection_m"] + 0.003 * k,
                                th, legs, z_in=cth + 0.003 * k)
            y_out += hm["width_m"]
        cuts, k = [], round((y_ap - y_start) / E)
        while y_start + k * E < top - 1e-6:
            y0 = y_start + k * E
            if y0 < spring - 1e-9:
                cuts.append((sa, sb, y0, y0 + E))
            else:
                for x in heads:
                    off = math.sqrt(max(0.0, r * r - (y0 - spring) ** 2))
                    if off > 1e-6:
                        cuts.append((x - off, x + off, y0, y0 + E))
            k += 1
        if win.get("hood"):
            self._bracketed_hood(F, win["hood"], c, y_out, y_start)
        self.meta["casing"] = {"s": [sa, sb], "y": [y_ap, round(y_out, 6)], "head": "round",
                               "spring_m": round(spring, 6), "on_course_lines": False}
        self.meta.setdefault("casings", []).append(self.meta["casing"])
        return (c - hw, c + hw, ys, top), cuts

    def _bracketed_hood(self, F, hv, c, y_under, y_start):
        """T-3182: a flat hood on two scroll brackets over a window, 1720 Prairie's middle upper
        window: a moulded slab `width_m` across, `height_m` deep and `projection_m` out, its
        underside `above_m` over the casing's head, a bracket under each end."""
        w, h, pz = hv["width_m"], hv["height_m"], hv["projection_m"]
        E = self.data["cladding"]["clapboard"]["exposure_m"]

        def clear(y):     # a level face applied to the cladding never lies on a course's butt
            q = (y - y_start) / E
            return y + 0.006 if abs(q - round(q)) * E < 0.003 else y
        y0 = clear(y_under + hv["above_m"])
        c += hv.get("offset_m", 0.0)     # the hood's middle off the window's, where the picture puts it
        th = self.tone("hood")
        yc = clear(y0 + h)
        self.box(F, "frieze", c - w / 2, c + w / 2, y0, yc, 0.0, pz, skip=("back", "top"), tone=th,
                 roles={"front": "fascia", "bottom": "soffit"})
        self.box(F, "drip_cap", c - w / 2 - 0.04, c + w / 2 + 0.04, yc, clear(yc + 0.06), 0.0, pz + 0.04,
                 skip=("back",), tone=th)
        if hv.get("panel"):     # a plain raised panel standing on the hood, under the eave
            pw, ph_, pp = hv["panel"]["width_m"], hv["panel"]["height_m"], hv["panel"]["projection_m"]
            self.box(F, "casing", c - pw / 2, c + pw / 2, clear(yc + 0.06), clear(yc + 0.06 + ph_), 0.0, pp,
                     skip=("back", "bottom"), tone=th)
        br = dict(self.data["trim"]["bracket"], **hv["bracket"])
        for e in (-1, 1):
            self.bracket(F, c + e * (w / 2 - br["thickness_m"]), 0.0, y0, br, br["thickness_m"], tone=th)
        self.meta.setdefault("hoods", []).append({"centre_m": c, "underside_m": round(y0, 6), "width_m": w})

    def _frieze_light(self, F, fl, zf):
        """T-3182: a small light let into the frieze between the eave's brackets, 1720 Prairie's
        photograph: an `oval` (a stadium, lying along the frieze) or `round`-headed lights,
        `bays` of them either side of a `mullion_m`, glazed and framed by a moulding `frame_m`
        wide standing 0.03 m proud of the frieze board (its front alone: an edge that shallow ten
        metres up is not seen, and the wall's triangle budget is better spent on the windows)."""
        c, yc, w, h, bw = fl["centre_m"], fl["centre_y_m"], fl["width_m"], fl["height_m"], fl["frame_m"]
        bays, mull = fl.get("bays", 1), fl.get("mullion_m", 0.0)
        lw = (w - mull * (bays - 1)) / bays
        n = 6
        tf = self.tone("frieze_light")
        for k in range(bays):
            x = c - w / 2 + lw / 2 + k * (lw + mull)

            def outline(g, x=x):
                if fl["kind"] == "oval":
                    rr, hs = h / 2 + g, max(0.0, (lw - h) / 2)
                    right = [(x + hs + rr * math.cos(a), yc + rr * math.sin(a))
                             for a in (-math.pi / 2 + math.pi * j / n for j in range(n + 1))]
                    left = [(x - hs + rr * math.cos(a), yc + rr * math.sin(a))
                            for a in (math.pi / 2 + math.pi * j / n for j in range(n + 1))]
                    return right + left
                rr, spring = lw / 2 + g, yc + h / 2 - lw / 2
                return [(x + rr, yc - h / 2 - g)] + [(x + rr * math.cos(a), spring + rr * math.sin(a))
                                                     for a in (math.pi * j / n for j in range(n + 1))] \
                    + [(x - rr, yc - h / 2 - g)]
            i_, o = outline(0.0), outline(bw)
            self.poly(F, "glass_outer", [(p[0], p[1], zf + 0.004) for p in i_], (0, 0, 1), tf)
            z1 = zf + 0.03
            m = len(i_)
            for j in range(m):
                p0, p1, q0, q1 = i_[j], i_[(j + 1) % m], o[j], o[(j + 1) % m]
                self.poly(F, "casing", [(p0[0], p0[1], z1), (q0[0], q0[1], z1), (q1[0], q1[1], z1), (p1[0], p1[1], z1)],
                          (0, 0, 1), tf)
        self.meta.setdefault("frieze_lights", []).append({"centre_m": c, "kind": fl["kind"], "bays": bays})

    def _hood(self, F, hv):
        """T-2423: a moulded hood over a gable's windows, read off 1638's photograph: a band
        rising from a label stop at each end along a cubic ogee to a point under a finial,
        mirrored about its centre. `curve` is the left half's four control points, s from the
        centre and y over grade; the band is `width_m` across and stands `projection_m` out."""
        hc, w, zp = hv["centre_m"], hv["width_m"], hv["projection_m"]
        P = hv["curve"]
        butts = [c["y0"] for c in self.meta["courses"] if c["family"] == "clapboard"]

        def clear(y):     # a level face applied to the cladding never lies on a course's butt
            return y + 0.006 if any(abs(y - b) < 0.003 for b in butts) else y
        n = 16
        pts, tans = [], []
        for i in range(n + 1):
            t = i / n
            b = ((1 - t) ** 3, 3 * (1 - t) ** 2 * t, 3 * (1 - t) * t * t, t ** 3)
            d = (-3 * (1 - t) ** 2, 3 * (1 - t) ** 2 - 6 * (1 - t) * t, 6 * (1 - t) * t - 3 * t * t, 3 * t * t)
            pts.append((math.fsum(b[j] * P[j][0] for j in range(4)), math.fsum(b[j] * P[j][1] for j in range(4))))
            tx, ty = math.fsum(d[j] * P[j][0] for j in range(4)), math.fsum(d[j] * P[j][1] for j in range(4))
            L = math.hypot(tx, ty) or 1.0
            tans.append((tx / L, ty / L))
        up = [(x - ty * w / 2, y + tx * w / 2) for (x, y), (tx, ty) in zip(pts, tans)]   # outer (upper) edge
        lo = [(x + ty * w / 2, y - tx * w / 2) for (x, y), (tx, ty) in zip(pts, tans)]
        th = self.tone("hood")
        for side in (-1, 1):       # the left half (control points as given), then mirrored
            def m(q):
                return (hc + (q[0] if side == -1 else -q[0]), q[1])
            half = [(hc, -1.0), (hc, 99.0), (hc + side * 9.0, 99.0), (hc + side * 9.0, -1.0)]
            for i in range(n):
                a0, a1, b0, b1 = m(up[i]), m(up[i + 1]), m(lo[i]), m(lo[i + 1])
                # each half's face stops at the centre line, so the two never overlap at the point
                fr = K06.clip(ccw([b0, b1, a1, a0]), ccw(half))
                if len(fr) >= 3 and abs(area2(fr)) > 1e-9:
                    self.poly(F, "casing", [(q[0], q[1], zp) for q in fr], (0, 0, 1), th)
                tx, ty = tans[i]
                nx = -ty if side == -1 else ty
                self.poly(F, "casing", [(a0[0], a0[1], 0), (a1[0], a1[1], 0), (a1[0], a1[1], zp), (a0[0], a0[1], zp)],
                          (nx, tx, 0), th)
                self.poly(F, "casing", [(b0[0], b0[1], 0), (b1[0], b1[1], 0), (b1[0], b1[1], zp), (b0[0], b0[1], zp)],
                          (-nx, -tx, 0), th)
            st = hv["stop"]
            s0 = m(pts[0])[0]
            y0 = P[0][1]
            if st.get("kind") == "volute":    # T-2457: the band's end curled outward and down
                r = st["radius_m"]
                self._applied_ring(F, (s0 + side * 0.6 * r, y0 - 0.4 * r), lambda a, d: r - d, st["eye_m"],
                                   r - st["eye_m"], zp + 0.01, th)
            else:
                self.box(F, "casing", s0 - st["width_m"] / 2, s0 + st["width_m"] / 2, clear(y0 - st["height_m"]),
                         clear(y0 + w / 2), 0.0, zp + 0.01, skip=("back",), tone=th)
        if hv.get("tracery"):     # T-2457: a cusped trefoil between the lights' heads, under the point
            tv = hv["tracery"]
            rl, dl = tv["lobe_r_m"], tv["lobe_off_m"]
            lobes = [(dl * math.cos(math.radians(a)), dl * math.sin(math.radians(a))) for a in (90, 210, 330)]

            def trefoil(a, d):     # the distance out to the three lobes' outline, inset by d
                u = (math.cos(a), math.sin(a))
                best = 0.0
                for cx, cy in lobes:
                    b = u[0] * cx + u[1] * cy
                    disc = (rl - d) ** 2 - (cx * cx + cy * cy - b * b)
                    if disc >= 0:
                        best = max(best, b + math.sqrt(disc))
                return best
            self._applied_ring(F, (hc, tv["centre_y_m"]), trefoil, 0.0, tv["ring_m"], tv["projection_m"], th, n=60)
        # the finial on the point: a square post, a cross-piece and a pyramid cap
        fh, a = hv["finial_m"], 0.035
        ya = P[3][1]
        tf = self.tone("hood_finial")
        self.box(F, "finial", hc - a, hc + a, clear(ya - w), ya + fh - 0.14, 0.0, zp + 0.01, skip=("back", "top"), tone=tf)
        yx = ya + 0.55 * fh
        self.box(F, "finial", hc - 0.1, hc + 0.1, clear(yx - 0.025), clear(yx + 0.025), 0.0, zp + 0.005, skip=("back",),
                 tone=tf)
        yt, zc = ya + fh - 0.14, (zp + 0.01) / 2
        apex = (hc, ya + fh, zc)
        for (p, q, hint) in (((hc - a, 0.0), (hc + a, 0.0), (0, 0.4, -1)), ((hc + a, zp + 0.01), (hc - a, zp + 0.01), (0, 0.4, 1)),
                             ((hc - a, zp + 0.01), (hc - a, 0.0), (-1, 0.4, 0)), ((hc + a, 0.0), (hc + a, zp + 0.01), (1, 0.4, 0))):
            self.poly(F, "finial", [(p[0], yt, p[1]), (q[0], yt, q[1]), apex], hint, tf)
        self.meta["hood"] = {"centre_m": hc, "apex_m": ya, "finial_top_m": round(ya + fh, 6),
                             "stops_m": [round(hc + P[0][0], 6), round(hc - P[0][0], 6)]}

    def _applied_ring(self, F, c, radius, d_in, ring, zf, tone, n=24):
        """T-2457: a flat moulded ring applied to the cladding, standing `zf` proud, round a
        centre c (s, y): its outline at angle a is `radius(a, 0)` out, its inner edge
        `radius(a, ring)`; `d_in` > 0 leaves an eye of that radius instead (a volute's)."""
        angs = [2 * math.pi * k / n for k in range(n)]
        o = [(c[0] + radius(a, 0.0) * math.cos(a), c[1] + radius(a, 0.0) * math.sin(a)) for a in angs]
        if d_in > 0:
            i_ = [(c[0] + d_in * math.cos(a), c[1] + d_in * math.sin(a)) for a in angs]
        else:
            i_ = [(c[0] + radius(a, ring) * math.cos(a), c[1] + radius(a, ring) * math.sin(a)) for a in angs]
        for k in range(n):
            o0, o1, i0, i1 = o[k], o[(k + 1) % n], i_[k], i_[(k + 1) % n]
            mx, my = (o0[0] + o1[0]) / 2 - c[0], (o0[1] + o1[1]) / 2 - c[1]
            self.poly(F, "casing", [(i0[0], i0[1], zf), (o0[0], o0[1], zf), (o1[0], o1[1], zf), (i1[0], i1[1], zf)],
                      (0, 0, 1), tone)
            self.poly(F, "casing", [(o0[0], o0[1], 0), (o1[0], o1[1], 0), (o1[0], o1[1], zf), (o0[0], o0[1], zf)],
                      (mx, my, 0), tone)
            self.poly(F, "casing", [(i0[0], i0[1], 0), (i1[0], i1[1], 0), (i1[0], i1[1], zf), (i0[0], i0[1], zf)],
                      (-mx, -my, 0), tone)

    def _oculus(self, F, ov):
        """T-2423: the oval in 1638's gable: a moulded ring round a sunk field, applied to the
        cladding. The photograph shows its field as pale as the wall, with no glass or bar in
        it, so it is built blind; `field_m` and `ring_m` are its two faces' stand-off."""
        sc, yc, ax, ay, rw = ov["centre_m"], ov["centre_y_m"], ov["width_m"] / 2, ov["height_m"] / 2, ov["ring_m"]
        zf, zr, n = ov["field_z_m"], ov["ring_z_m"], 32
        el = lambda k, d: (sc + (ax - d) * math.cos(2 * math.pi * k / n), yc + (ay - d) * math.sin(2 * math.pi * k / n))
        to = self.tone("oculus")
        self.poly(F, "casing", [(*el(k, rw), zf) for k in range(n)], (0, 0, 1), to)
        for k in range(n):
            o0, o1, i0, i1 = el(k, 0.0), el(k + 1, 0.0), el(k, rw), el(k + 1, rw)
            mx, my = (o0[0] + o1[0]) / 2 - sc, (o0[1] + o1[1]) / 2 - yc
            self.poly(F, "casing", [(i0[0], i0[1], zr), (o0[0], o0[1], zr), (o1[0], o1[1], zr), (i1[0], i1[1], zr)], (0, 0, 1), to)
            self.poly(F, "casing", [(o0[0], o0[1], 0), (o1[0], o1[1], 0), (o1[0], o1[1], zr), (o0[0], o0[1], zr)], (mx, my, 0), to)
            self.poly(F, "casing", [(i0[0], i0[1], zf), (i1[0], i1[1], zf), (i1[0], i1[1], zr), (i0[0], i0[1], zr)], (-mx, -my, 0), to)
        self.meta["oculus"] = {"centre": [sc, yc], "size_m": [ov["width_m"], ov["height_m"]]}

    def _cased_door(self, F, door, y_start):
        """T-2357: a panelled door in a K16 casing on frame F, centred at door's centre_m,
        its threshold on the water table's drip cap (where the cladding starts). The leaf
        stands at the casing's reveal, stiles and rails flush and the panels sunk behind
        them; the jambs and head are lined in painted trim; the side casings stand on the
        drip cap's slope and the head carries a drip cap ended on a clapboard butt line.
        Returns the hole it leaves in the sheathing and the rectangle it cuts from the
        clapboard."""
        tr = self.data["trim"]
        E = self.data["cladding"]["clapboard"]["exposure_m"]
        cs, wt = tr["casing"], tr["water_table"]
        c, w, H = door["centre_m"], door["clear_width_m"], door["clear_height_m"]
        hw = w / 2
        rev = cs["reveal_depth_m"]
        cw, cth = cs["width_m"], cs["thickness_m"]
        sa, sb = c - hw - cw, c + hw + cw
        # T-2520: a transom light over the leaves raises the opening (yH) above the leaves' head (yL)
        tm = door.get("transom")
        y0, yL = y_start, y_start + H
        yH = yL + (tm["bar_m"] + tm["apex_m"] if tm else 0.0)
        tw = self.tone("door_casing", c)
        # the jamb lining, the head soffit and the threshold, the wall's depth to the leaf
        for s_e, hs in ((c - hw, 1), (c + hw, -1)):
            self.poly(F, "reveal", [(s_e, y0, 0), (s_e, y0, -rev), (s_e, yH, -rev), (s_e, yH, 0)], (hs, 0, 0), tw)
        self.poly(F, "reveal", [(c - hw, yH, 0), (c - hw, yH, -rev), (c + hw, yH, -rev), (c + hw, yH, 0)], (0, -1, 0), tw)
        self.poly(F, "sill", [(c - hw, y0, -rev), (c + hw, y0, -rev), (c + hw, y0, 0), (c - hw, y0, 0)], (0, 1, 0), tw)
        # the leaf: stiles and rails a frame round sunk panels, `panels` [columns, rows]
        st, rt, rb, rl = door["stile_m"], door["top_rail_m"], door["bottom_rail_m"], door["lock_rail_m"]
        ncol, nrow = door["panels"]
        sink = door["panel_sink_m"]
        x0, x1 = c - hw + st, c + hw - st
        pw = (x1 - x0 - (ncol - 1) * st) / ncol
        rows = []
        y_lo = y0 + rb
        y_hi = yL - rt
        ph = (y_hi - y_lo - (nrow - 1) * rl) / nrow
        for j in range(nrow):
            rows.append((y_lo + j * (ph + rl), y_lo + j * (ph + rl) + ph))
        panels = [(x0 + i * (pw + st), x0 + i * (pw + st) + pw, ya, yb) for i in range(ncol) for (ya, yb) in rows]
        td = self.tone("door", c)
        self.sheathing(F, (c - hw, c + hw, y0, yL), panels, role="door", z=-rev)
        if tm:
            self._door_transom(F, tm, c, hw, yL, rev, door["panel_sink_m"], tw)
        glazed = bool(door.get("glazed"))     # T-2425: each panel a light of glass, the hall dark behind
        for (pa, pb, ya, yb) in panels:
            zb = -rev - sink
            if glazed:
                self.poly(F, "glass_outer", [(pa, ya, zb), (pb, ya, zb), (pb, yb, zb), (pa, yb, zb)], (0, 0, 1))
                zh = zb - GLAZED_HALL_M
                self.poly(F, "backing", [(pa, ya, zh), (pb, ya, zh), (pb, yb, zh), (pa, yb, zh)], (0, 0, 1))
            else:
                self.poly(F, "door_panel", [(pa, ya, zb), (pb, ya, zb), (pb, yb, zb), (pa, yb, zb)], (0, 0, 1), td)
            for q in ([(pa, ya, zb), (pa, ya, -rev), (pa, yb, -rev), (pa, yb, zb)],
                      [(pb, ya, zb), (pb, yb, zb), (pb, yb, -rev), (pb, ya, -rev)],
                      [(pa, ya, zb), (pb, ya, zb), (pb, ya, -rev), (pa, ya, -rev)],
                      [(pa, yb, zb), (pa, yb, -rev), (pb, yb, -rev), (pb, yb, zb)]):
                cx, cy = (pa + pb) / 2, (ya + yb) / 2
                mx, my = math.fsum(p[0] for p in q) / 4, math.fsum(p[1] for p in q) / 4
                self.poly(F, "door", q, (cx - mx, cy - my, 0), td)
        # the casing: its feet on the drip cap's slope, the head, the head's drip cap
        sl = wt["cap"]["fall_m"] / (wt["thickness_m"] + wt["cap"]["projection_m"])
        dc = cs["drip_cap"]
        y_top = y_start + E * math.ceil((yH + cs["head_m"] + dc["height_m"] - y_start) / E - 1e-6)
        yHc = y_top - dc["height_m"]
        yb_ = y0 - cth * sl
        for (a, b) in ((sa, c - hw), (c + hw, sb)):
            self.poly(F, "casing", [(a, yb_, cth), (b, yb_, cth), (b, yH, cth), (a, yH, cth)], (0, 0, 1), tw)
            self.poly(F, "casing", [(a, y0, 0), (a, yb_, cth), (a, yH, cth), (a, yH, 0)], (-1, 0, 0), tw)
            self.poly(F, "casing", [(b, y0, 0), (b, yb_, cth), (b, yH, cth), (b, yH, 0)], (1, 0, 0), tw)
        self.box(F, "casing", sa, sb, yH, yHc, 0, cth, skip=("back", "top", "bottom"), tone=tw,
                 roles={"s0": "end_grain", "s1": "end_grain"})
        self.poly(F, "casing", [(c - hw, yH, 0), (c + hw, yH, 0), (c + hw, yH, cth), (c - hw, yH, cth)], (0, -1, 0), tw)
        zc = cth + dc["projection_m"]
        cap = [(0.0, yHc), (zc, yHc), (zc, yHc + dc["front_m"]), (0.0, y_top)]
        self.poly(F, "drip_cap", [(sa, yHc, cth), (sb, yHc, cth), (sb, yHc, zc), (sa, yHc, zc)], (0, -1, 0), tw)
        self.profile_run(F, cap, [None, "drip_cap", "drip_cap", None], sa, sb, ("end_grain", "end_grain"), tw)
        dm = {"s": [round(sa, 6), round(sb, 6)], "y": [round(y0, 6), round(y_top, 6)],
              "panels": len(panels), "glazed": glazed, "on_course_lines": True}
        if tm:
            dm["transom"] = {"glass_y": [round(yL + tm["bar_m"], 6), round(yH, 6)], "side_m": tm["side_m"]}
        self.meta.setdefault("doors", []).append(dm)
        return (c - hw, c + hw, y0, yH), (sa, sb, y0, y_top)

    def _door_transom(self, F, tm, c, hw, yL, rev, sink, tw):
        """T-2520: a glazed transom over a door's leaves, the opening's full width: a bar on
        the leaves' head, then one light under a low gable, `side_m` high at the jambs and
        `apex_m` at the middle, the two corners over its slopes filled with painted board to
        the opening's square head. The glass is sunk as the leaves' lights are, the hall dark
        behind it."""
        yg, ys, ya = yL + tm["bar_m"], yL + tm["bar_m"] + tm["side_m"], yL + tm["bar_m"] + tm["apex_m"]
        zb = -rev - sink
        zh = zb - GLAZED_HALL_M
        light = [(c - hw, yg), (c + hw, yg), (c + hw, ys), (c, ya), (c - hw, ys)]
        self.poly(F, "glass_outer", [(s, y, zb) for s, y in light], (0, 0, 1))
        self.poly(F, "backing", [(s, y, zh) for s, y in light], (0, 0, 1))
        self.poly(F, "door", [(c - hw, yL, -rev), (c + hw, yL, -rev), (c + hw, yg, -rev), (c - hw, yg, -rev)], (0, 0, 1), tw)
        self.poly(F, "door", [(c - hw, ys, -rev), (c, ya, -rev), (c - hw, ya, -rev)], (0, 0, 1), tw)
        self.poly(F, "door", [(c + hw, ys, -rev), (c + hw, ya, -rev), (c, ya, -rev)], (0, 0, 1), tw)
        rise = ya - ys
        for (p, q), hint in ((((c - hw, yg), (c + hw, yg)), (0, 1, 0)),
                             (((c - hw, yg), (c - hw, ys)), (1, 0, 0)),
                             (((c + hw, yg), (c + hw, ys)), (-1, 0, 0)),
                             (((c - hw, ys), (c, ya)), (rise, -hw, 0)),
                             (((c, ya), (c + hw, ys)), (-rise, -hw, 0))):
            self.poly(F, "door", [(*p, zb), (*q, zb), (*q, -rev), (*p, -rev)], hint, tw)

    def _batten_wall(self):
        v, d = self.v, self.data
        T = d["wall"]["thickness_m"]
        bb = d["cladding"]["board_and_batten"]
        W, y_fd, y_s = v["width_m"], v["foundation_m"], v["wall_top_m"]
        F = self.F
        y_start = self._base(F, 0.0, W, y_fd, T)
        fr = d["trim"]["frieze"]
        bw, bt, g = bb["board_width_m"], bb["board_m"], bb["gap_m"]
        btw, btt = bb["batten_width_m"], bb["batten_m"]
        ft = bt + btt + 0.008
        y_fr0 = y_s - fr["height_m"]
        s = 0.0
        boards = []
        while s < W - 1e-6:
            boards.append((s, min(s + bw, W)))
            s += bw + g
        for i, (a, b) in enumerate(boards):
            t = self.tone("board", i)
            self.poly(F, "board", [(a, y_start, bt), (b, y_start, bt), (b, y_fr0, bt), (a, y_fr0, bt)], (0, 0, 1), t)
            self.poly(F, "end_grain", [(a, y_start, 0), (b, y_start, 0), (b, y_start, bt), (a, y_start, bt)], (0, -1, 0), t)
            if a < 1e-9:
                self.poly(F, "cut", [(a, y_start, 0), (a, y_start, bt), (a, y_fr0, bt), (a, y_fr0, 0)], (-1, 0, 0))
            if b > W - 1e-9:
                self.poly(F, "cut", [(b, y_start, 0), (b, y_fr0, 0), (b, y_fr0, bt), (b, y_start, bt)], (1, 0, 0))
        self.meta["boards"] = [[round(a, 6), round(b, 6)] for a, b in boards]
        for i in range(len(boards) - 1):
            gc = (boards[i][1] + boards[i + 1][0]) / 2
            a, b = gc - btw / 2, gc + btw / 2
            t = self.tone("batten", i)
            self.box(F, "batten", a, b, y_start, y_fr0, bt, bt + btt, skip=("back", "top"), tone=t,
                     roles={"bottom": "end_grain"})
            self.meta["battens"].append([round(a, 6), round(b, 6)])
        self.profile_run(F, [(0.0, y_fr0), (ft, y_fr0), (ft, y_s), (0.0, y_s)], ["frieze", "frieze", "frieze", None],
                         0.0, W, ("end_grain", "end_grain"), self.tone("frieze"))
        self.poly(F, "interior", [(0, y_fd, -T), (0, y_s, -T), (W, y_s, -T), (W, y_fd, -T)], (0, 0, -1))
        self.poly(F, "cut", [(0, y_fd, -T), (0, y_fd, 0), (0, y_s, 0), (0, y_s, -T)], (-1, 0, 0))
        self.poly(F, "cut", [(W, y_fd, -T), (W, y_s, -T), (W, y_s, 0), (W, y_fd, 0)], (1, 0, 0))
        self.poly(F, "cut", [(0, y_s, -T), (0, y_s, 0), (W, y_s, 0), (W, y_s, -T)], (0, 1, 0))
        self.meta.update({"wall_thickness_m": T, "frieze_thickness_m": ft, "focus": [W / 2, 1.6, 0.0], "span_m": 2.2})

    def _gable(self):
        v, d = self.v, self.data
        tr, T, go = d["trim"], d["wall"]["thickness_m"], d["gothic"]
        W, y_fd, y_belt = v["width_m"], v["foundation_m"], v["belt_m"]
        F = self.F
        y_start = self._base(F, 0.0, W, y_fd, T)
        holes, cuts = [], []
        for win in v.get("windows", []):    # T-2323: a house's gable front has its sash
            hole, cut = self._cased_window(F, win, y_start)
            holes.append(hole)
            cuts.extend(cut if isinstance(cut, list) else [cut])    # T-2423: a pointed head's courses
        cb, ct = tr["corner_board"]["width_m"], tr["corner_board"]["thickness_m"]
        be = tr["belt"]
        cap = tr["water_table"]["cap"]
        y_b1 = y_belt + be["height_m"]
        y_g = y_b1 + cap["height_m"]
        zc = be["thickness_m"] + cap["projection_m"]
        p = math.radians(go["pitch_deg"])
        tp, cp_, sp_ = math.tan(p), math.cos(p), math.sin(p)
        y_ap = y_g + (W / 2) * tp
        rw = tr["rake_board"]["width_m"]
        # T-2423: `field: clapboard` carries the wall's clapboard up into the gable to the rake
        # board, with no belt and no shingle, as 1638's photograph shows; the rake still springs
        # at the belt's height, so the roof and the body behind it do not move
        clap_field = v.get("field") == "clapboard"
        tc = self.tone("corner")
        if clap_field:
            E = d["cladding"]["clapboard"]["exposure_m"]
            # the first course whose foot the rake board's lower edge cuts inside the corner
            # boards; every course below it runs from corner board to corner board
            y_lo = y_start + E * (math.floor((y_g - rw / cp_ + cb * tp - y_start) / E + 1e-9) + 1)
            self.clapboards(F, cb, W - cb, y_start, y_lo, ("trim", "trim"), cuts)

            def span(y0):
                a = max(cb, (y0 - y_g + rw / cp_) / tp)
                return (a, W - a) if W - 2 * a > 1e-6 else None

            n_lo = round((y_lo - y_start) / E)
            n_hi = int(math.ceil((y_ap - rw / cp_ - y_lo) / E - 1e-9))
            self.clapboards(F, cb, W - cb, y_lo, y_lo + n_hi * E, cuts=cuts, course0=n_lo, span=span)
            for s0_, s1_ in ((0.0, cb), (W - cb, W)):
                self.box(F, "corner_board", s0_, s1_, y_start, y_g, 0, ct, skip=("back", "top"), tone=tc)
        else:
            self.clapboards(F, cb, W - cb, y_start, y_belt, ("trim", "trim"), cuts)
            self.box(F, "corner_board", 0.0, cb, y_start, y_belt, 0, ct, skip=("back", "top"), tone=tc)
            self.box(F, "corner_board", W - cb, W, y_start, y_belt, 0, ct, skip=("back", "top"), tone=tc)
            self.profile_run(F, [(0.0, y_belt), (be["thickness_m"], y_belt), (be["thickness_m"], y_b1), (0.0, y_b1)],
                             ["belt", "belt", None, None], 0.0, W, ("end_grain", "end_grain"), self.tone("belt"))
            self.profile_run(F, [(0.0, y_b1), (zc, y_b1), (zc, y_g - cap["fall_m"]), (0.0, y_g)],
                             ["drip_cap", "drip_cap", "drip_cap", None], 0.0, W, ("end_grain", "end_grain"),
                             self.tone("belt"))
        if v.get("hood"):
            self._hood(F, v["hood"])
        if v.get("oculus"):
            self._oculus(F, v["oculus"])
        # the wall: sheathing and interior up to the rake, its two lower cuts
        tri = [(0.0, y_g), (W, y_g), (W / 2, y_ap)]
        self.sheathing(F, (0.0, W, y_fd, y_g), holes)
        self.sheathing(F, tri)
        self.sheathing(F, (0.0, W, y_fd, y_g), holes, role="interior", z=-T, hint_z=-1)
        self.sheathing(F, tri, role="interior", z=-T, hint_z=-1)
        self.poly(F, "cut", [(0, y_fd, -T), (0, y_fd, 0), (0, y_g, 0), (0, y_g, -T)], (-1, 0, 0))
        self.poly(F, "cut", [(W, y_fd, -T), (W, y_g, -T), (W, y_g, 0), (W, y_fd, 0)], (1, 0, 0))
        rk = tr["rake_board"]
        rw, rkt = rk["width_m"], rk["thickness_m"]
        bg = go["bargeboard"]
        bd, bbt, ov = bg["depth_m"], bg["thickness_m"], go["verge_overhang_m"]
        h_roof = go["roof_m"] / cp_
        back = -0.6
        half = []   # (role, pts (s, y, z), hint) for the left half, mirrored for the right

        def add(role, pts, hint, tone=1.0):
            half.append((role, pts, hint, tone))

        # rake board on the wall, under the verge
        tr_ = self.tone("rake")
        rb = [(0.0, y_g), (W / 2, y_ap), (W / 2, y_ap - rw / cp_), (rw / sp_, y_g)]
        add("rake_board", [(s, y, rkt) for s, y in rb], (0, 0, 1), tr_)
        add("rake_board", [(rb[3][0], y_g, 0), (rb[2][0], rb[2][1], 0), (rb[2][0], rb[2][1], rkt), (rb[3][0], y_g, rkt)],
            (sp_, -cp_, 0), tr_)
        add("rake_board", [(0.0, y_g, 0), (rb[3][0], y_g, 0), (rb[3][0], y_g, rkt), (0.0, y_g, rkt)], (0, -1, 0), tr_)
        # the roof over the verge (board), its soffit (trim)
        add("roof", [(0, y_g + h_roof, ov), (W / 2, y_ap + h_roof, ov), (W / 2, y_ap + h_roof, back), (0, y_g + h_roof, back)],
            (-sp_, cp_, 0))
        add("roof", [(0, y_g, ov), (W / 2, y_ap, ov), (W / 2, y_ap + h_roof, ov), (0, y_g + h_roof, ov)], (0, 0, 1))
        # T-2457: a plain verge board stands in front of the roof's edge, so the soffit runs to it
        vg = v.get("verge")
        z_sf = ov if vg else ov - bbt
        add("soffit", [(0, y_g, 0), (W / 2, y_ap, 0), (W / 2, y_ap, z_sf), (0, y_g, z_sf)], (sp_, -cp_, 0),
            self.tone("verge"))
        add("roof", [(0, y_g, back), (W / 2, y_ap, back), (W / 2, y_ap, 0), (0, y_g, 0)], (sp_, -cp_, 0))
        add("roof", [(0, y_g, back), (0, y_g, ov), (0, y_g + h_roof, ov), (0, y_g + h_roof, back)], (-1, 0, 0))
        add("roof", [(0, y_g, back), (0, y_g + h_roof, back), (W / 2, y_ap + h_roof, back), (W / 2, y_ap, back)], (0, 0, -1))

        # the pierced bargeboard, in its own (t along the rake, v down from it)
        Lr = (W / 2) / cp_

        def tv(t, vv):
            return (t * cp_ + vv * sp_, y_g + t * sp_ - vv * cp_)

        holes = []
        if vg:
            self._plain_verge(vg, add, tv, Lr, tp, cp_, h_roof, ov)
        else:
            lo_t, hi_t = bg["end_m"], Lr - bd * tp - bg["end_m"]
            cell = bg["cell_m"]
            ncell = max(0, int((hi_t - lo_t) / cell))
            t0 = lo_t + ((hi_t - lo_t) - ncell * cell) / 2
            tb = self.tone("barge")
            zF, zB = ov, ov - bbt
            pieces = [[(0.0, 0.0), (t0, 0.0), (t0, bd), (-bd * tp, bd)],
                      [(t0 + ncell * cell, 0.0), (Lr, 0.0), (Lr - bd * tp, bd), (t0 + ncell * cell, bd)]]
            for pc in pieces:
                xy = [tv(*q) for q in pc]
                add("bargeboard", [(s, y, zF) for s, y in xy], (0, 0, 1), tb)
                add("bargeboard", [(s, y, zB) for s, y in xy], (0, 0, -1), tb)
            holes = []
            for kc in range(ncell):
                ta, tb_ = t0 + kc * cell, t0 + (kc + 1) * cell
                cc = ((ta + tb_) / 2, bd / 2)
                if kc % 2 == 0:
                    r = bg["circle_r_m"]
                    ns = bg["circle_segments"]
                    hole = [(cc[0] + r * math.cos(2 * math.pi * i / ns), cc[1] + r * math.sin(2 * math.pi * i / ns))
                            for i in range(ns)]
                else:
                    vs = bg["vesica"]
                    L2, w2, ns = vs["length_m"] / 2, vs["width_m"] / 2, vs["segments"]
                    Rv = (L2 * L2 + w2 * w2) / (2 * w2)
                    f0 = math.atan2(Rv - w2, L2)
                    upper = [(cc[0] + Rv * math.cos(f0 + (math.pi - 2 * f0) * i / ns),
                              cc[1] - (Rv - w2) + Rv * math.sin(f0 + (math.pi - 2 * f0) * i / ns)) for i in range(ns)]
                    lower = [(cc[0] - Rv * math.cos(f0 + (math.pi - 2 * f0) * i / ns),
                              cc[1] + (Rv - w2) - Rv * math.sin(f0 + (math.pi - 2 * f0) * i / ns)) for i in range(ns)]
                    hole = upper + lower
                rect = [(ta, 0.0), (tb_, 0.0), (tb_, bd), (ta, bd)]
                for q in ring_quads(ccw(rect), ccw(hole)):
                    xy = [tv(*pp) for pp in q]
                    add("bargeboard", [(s, y, zF) for s, y in xy], (0, 0, 1), tb)
                    add("bargeboard", [(s, y, zB) for s, y in xy], (0, 0, -1), tb)
                hxy = [tv(*pp) for pp in ccw(hole)]
                cxy = (math.fsum(pp[0] for pp in hxy) / len(hxy), math.fsum(pp[1] for pp in hxy) / len(hxy))
                for i in range(len(hxy)):
                    a, b = hxy[i], hxy[(i + 1) % len(hxy)]
                    m = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
                    add("cutout", [(a[0], a[1], zB), (b[0], b[1], zB), (b[0], b[1], zF), (a[0], a[1], zF)],
                        (cxy[0] - m[0], cxy[1] - m[1], 0), tb)
                holes.append(hxy)
            bl0, bl1 = tv(-bd * tp, bd), tv(Lr - bd * tp, bd)
            add("bargeboard", [(bl0[0], bl0[1], zB), (bl1[0], bl1[1], zB), (bl1[0], bl1[1], zF), (bl0[0], bl0[1], zF)],
                (sp_, -cp_, 0), tb)
            e0, e1 = tv(0.0, 0.0), tv(-bd * tp, bd)
            add("end_grain", [(e0[0], e0[1], zB), (e1[0], e1[1], zB), (e1[0], e1[1], zF), (e0[0], e0[1], zF)], (-1, 0, 0), tb)
        for role, pts, hint, tone in half:
            self.poly(F, role, pts, hint, tone)
            self.poly(F, role, [(W - s, y, z) for s, y, z in pts], (-hint[0], hint[1], hint[2]), tone)
        for hxy in holes:
            for mirror in (False, True):
                pts = [((W - s) if mirror else s, y) for s, y in hxy]
                self.meta["piercings"].append({"frame": "front", "front_z": zF, "back_z": zB,
                                               "hole": [[round(s, 6), round(y, 6)] for s, y in pts]})

        # shingles inside the rake boards
        inner = [(rw / sp_, y_g), (W - rw / sp_, y_g), (W / 2, y_ap - rw / cp_)]
        if not clap_field:
            self.shingles(F, inner, y_g, v["bands"], W / 2)

        # the finial through the apex; T-2457: or the record's cluster of pinnacles
        if v.get("pinnacles"):
            self._pinnacles(F, v["pinnacles"], W / 2, y_ap + h_roof, tp, ov + vg["thickness_m"] / 2 if vg else ov - bbt / 2)
        else:
            self._kit_finial(F, W, y_ap, h_roof, bd, cp_, ov, bbt, go)
        self._gable_meta(W, y_g, y_ap, h_roof, back, go)

    def _gable_meta(self, W, y_g, y_ap, h_roof, back, go):
        self.meta["gable"] = {"y_g": y_g, "y_ap": y_ap, "h_roof": h_roof, "back_m": back}   # T-2323
        self.meta.update({"wall_thickness_m": self.data["wall"]["thickness_m"], "pitch_deg": go["pitch_deg"],
                          "focus": [W * 0.3, y_ap - 0.9, 0.15], "span_m": 3.4})

    def _plain_verge(self, vg, add, tv, Lr, tp, cp_, h_roof, ov):
        """T-2457: 1638's verge, read off its photograph: a broad plain board with no piercing,
        standing just in front of the roof's edge and covering it, its depth `depth_m` measured
        down from the roof's top, and a bead `bead_m` deep standing `bead_proud_m` proud along
        its lower edge. Built in the bargeboard's own (t along the rake, v down from the roof's
        underside), the left half only; the caller mirrors it."""
        vt = -h_roof * cp_
        vb = vt + vg["depth_m"]
        vm = vb - vg["bead_m"]
        z0 = ov + 0.002
        z1 = z0 + vg["thickness_m"]
        z2 = z1 + vg["bead_proud_m"]
        tb = self.tone("barge")
        sp_ = math.sqrt(1.0 - cp_ * cp_)

        def at(v, z, apex=False):
            s, y = tv((Lr if apex else 0.0) - v * tp, v)
            return (s, y, z)
        add("bargeboard", [at(vt, z1), at(vt, z1, True), at(vm, z1, True), at(vm, z1)], (0, 0, 1), tb)
        add("bargeboard", [at(vt, z0), at(vt, z0, True), at(vt, z1, True), at(vt, z1)], (-sp_, cp_, 0), tb)
        add("bargeboard", [at(vm, z1), at(vm, z1, True), at(vm, z2, True), at(vm, z2)], (-sp_, cp_, 0), tb)
        add("bargeboard", [at(vm, z2), at(vm, z2, True), at(vb, z2, True), at(vb, z2)], (0, 0, 1), tb)
        add("bargeboard", [at(vb, z2), at(vb, z2, True), at(vb, z0, True), at(vb, z0)], (sp_, -cp_, 0), tb)
        add("end_grain", [at(vt, z0), at(vt, z1), at(vb, z1), at(vb, z0)], (-1, 0, 0), tb)
        add("end_grain", [at(vm, z1), at(vm, z2), at(vb, z2), at(vb, z1)], (-1, 0, 0), tb)

    def _pinnacles(self, F, pv, sc, y_top, tp, zc):
        """T-2457: 1638's apex, read off its photograph: a cluster of pointed pinnacles in place of
        the kit's chamfered finial and drop. Each is a square shaft `section_m` across, standing
        on the verge `offset_m` from the apex (mirrored either side; 0 is the apex itself) to
        `shaft_top_m` over the apex's roof line, under a pyramid to its point at `top_m`."""
        tf = self.tone("finial")
        for p in pv:
            a = p["section_m"] / 2
            for off in ((0.0,) if p["offset_m"] == 0 else (-p["offset_m"], p["offset_m"])):
                c = sc + off
                y0 = y_top - (abs(off) + a) * tp - 0.05
                y1, y2 = y_top + p["shaft_top_m"], y_top + p["top_m"]
                self.box(F, "finial", c - a, c + a, y0, y1, zc - a, zc + a, skip=("bottom", "top"), tone=tf)
                corners = [(c - a, zc + a), (c + a, zc + a), (c + a, zc - a), (c - a, zc - a)]
                for (s0, z0), (s1, z1) in zip(corners, corners[1:] + corners[:1]):
                    m = ((s0 + s1) / 2 - c, (z0 + z1) / 2 - zc)
                    self.poly(F, "finial", [(s0, y1, z0), (s1, y1, z1), (c, y2, zc)], (m[0], 0.5 * a, m[1]), tf)
        self.meta["pinnacles"] = [{"offset_m": p["offset_m"], "top_m": round(y_top + p["top_m"], 6)} for p in pv]

    def _kit_finial(self, F, W, y_ap, h_roof, bd, cp_, ov, bbt, go):
        fi = go["finial"]
        a, chm = fi["section_m"] / 2, fi["chamfer_m"]
        zc_ = ov - bbt / 2
        yb0 = y_ap - bd / cp_ - fi["drop_m"] + 0.2
        yb1 = y_ap + h_roof + fi["above_m"]
        octo = octagon(a, chm)
        tf = self.tone("finial")
        for i in range(8):
            (ds0, dz0), (ds1, dz1) = octo[i], octo[(i + 1) % 8]
            mid = ((ds0 + ds1) / 2, (dz0 + dz1) / 2)
            self.poly(F, "finial", [(W / 2 + ds0, yb0, zc_ + dz0), (W / 2 + ds1, yb0, zc_ + dz1),
                                    (W / 2 + ds1, yb1, zc_ + dz1), (W / 2 + ds0, yb1, zc_ + dz0)], (mid[0], 0, mid[1]), tf)
            self.poly(F, "finial", [(W / 2 + ds0, yb1, zc_ + dz0), (W / 2 + ds1, yb1, zc_ + dz1),
                                    (W / 2, yb1 + fi["point_m"], zc_)], (mid[0], 0.5, mid[1]), tf)
            self.poly(F, "finial", [(W / 2 + ds0, yb0, zc_ + dz0), (W / 2, yb0 - fi["point_m"], zc_),
                                    (W / 2 + ds1, yb0, zc_ + dz1)], (mid[0], -0.5, mid[1]), tf)

    def _gable_end(self):
        """T-2398: the gable over a frame house's end wall, standing on the boxed eave that runs
        across the wall below it (a closed, pedimented gable). Clapboard is laid up from the
        eave in courses each cut short where it meets the rake board's lower edge, round any
        attic sash the record names; a rake board runs under each verge to the apex. The verge
        box over it (soffit and fascia) is the roof's, built with it in `frame_house`."""
        v, d = self.v, self.data
        rk = d["trim"]["rake_board"]
        rw, rkt = rk["width_m"], rk["thickness_m"]
        W, y_b = v["width_m"], v["base_m"]
        p = math.radians(v["pitch_deg"])
        t, cp_, sp_ = math.tan(p), math.cos(p), math.sin(p)
        F = self.F
        # the verge box's underside where it meets the wall, at the wall's two ends and apex
        y_e = y_b + v["projection_m"] * t - v["fascia_m"]
        y_ap = y_e + (W / 2) * t
        drop = rw / cp_                  # the rake board's depth, measured plumb
        holes, cuts = [], []
        for win in v.get("windows") or []:
            hole, cut = self._cased_window(F, win, y_b)
            holes.append(hole)
            cuts.append(cut)

        def span(y0):
            # a course reaches as far as the rake board's lower edge stands above its foot
            a = max(0.0, (y0 - y_e + drop) / t)
            return (a, W - a) if W - 2 * a > 1e-6 else None

        cl = d["cladding"]["clapboard"]
        n = int(math.ceil((y_ap - y_b) / cl["exposure_m"]))
        self.clapboards(F, 0.0, W, y_b, y_b + n * cl["exposure_m"], cuts=cuts, span=span)
        tr_ = self.tone("rake")
        for side in (1, -1):             # the left rake, then the right mirrored
            def m(s):
                return s if side == 1 else W - s
            lo = [(m(0.0), y_e - drop), (m(W / 2), y_ap - drop)]
            hi = [(m(0.0), y_e), (m(W / 2), y_ap)]
            # its foot is under the verge box at the wall's corner, so it has no end face
            self.poly(F, "rake_board", [(s, y, rkt) for s, y in (lo[0], lo[1], hi[1], hi[0])], (0, 0, 1), tr_)
            self.poly(F, "rake_board", [(lo[0][0], lo[0][1], 0), (lo[1][0], lo[1][1], 0), (lo[1][0], lo[1][1], rkt),
                                        (lo[0][0], lo[0][1], rkt)], (side * sp_, -cp_, 0), tr_)
        self.meta["gable"] = {"y_e": y_e, "y_ap": y_ap}
        self.meta.update({"focus": [W / 2, y_ap - 1.0, 0.0], "span_m": W})

    def _porch(self):
        v, d = self.v, self.data
        po, tr = d["porch"], d["trim"]
        F = self.F
        fl, la, pt, pl, ce = po["floor"], po["lattice"], po["post"], po["plate"], po["ceiling"]
        if "post_m" in v:      # T-2425: a house's own post, broader than the kit's
            pt = dict(pt, section_m=v["post_m"])
        if "plate" in v:       # T-2519: a house's own plate (its clear height, its depth)
            pl = dict(pl, **v["plate"])
        if "roof_m" in v:      # T-2533: a house's own fascia, as deep as its photograph draws it
            po = dict(po, roof_m=v["roof_m"])
        yf, Dp = fl["height_m"], v.get("depth_m", fl["depth_m"])   # T-2323: a house's own depth
        yf += v.get("basement_m", 0.0)     # T-2523: the floor raised by the basement under it
        pitch = fl["board_width_m"] + fl["gap_m"]
        nb = int(round(v["width_m"] / pitch))
        Wf = nb * pitch - fl["gap_m"]
        bt = fl["board_m"]
        z_end = Dp + fl["nosing_m"]
        y_rim1 = yf - bt
        y_rim0 = y_rim1 - fl["rim_m"]
        rim_t = 0.04
        yp = yf + pl["clear_m"]
        yc = yp + pl["height_m"]
        ov_r = po["roof_overhang_m"]
        zp = Dp - pt["setback_m"]
        pd = pl["depth_m"]
        # backdrop
        self.poly(F, "backdrop", [(0, 0, 0), (Wf + ov_r + 0.2, 0, 0), (Wf + ov_r + 0.2, yc + po["roof_m"], 0),
                                  (0, yc + po["roof_m"], 0)], (0, 0, 1))
        # floor boards, oiled, running out from the wall
        for i in range(nb):
            a = i * pitch
            b = a + fl["board_width_m"]
            t = self.tone("floor", i)
            self.poly(F, "porch_floor", [(a, yf, 0), (a, yf, z_end), (b, yf, z_end), (b, yf, 0)], (0, 1, 0), t)
            self.poly(F, "end_grain", [(a, y_rim1, z_end), (b, y_rim1, z_end), (b, yf, z_end), (a, yf, z_end)], (0, 0, 1), t)
            self.poly(F, "porch_floor", [(a, y_rim1, Dp), (b, y_rim1, Dp), (b, y_rim1, z_end), (a, y_rim1, z_end)],
                      (0, -1, 0), t)
            self.poly(F, "cut" if i == 0 else "porch_floor", [(a, y_rim1, 0), (a, y_rim1, z_end), (a, yf, z_end), (a, yf, 0)],
                      (-1, 0, 0), t)
            self.poly(F, "porch_floor", [(b, y_rim1, 0), (b, yf, 0), (b, yf, z_end), (b, y_rim1, z_end)], (1, 0, 0), t)
        tr_ = self.tone("rim")
        self.box(F, "rim", 0.0, Wf, y_rim0, y_rim1, Dp - rim_t, Dp, skip=("back", "top"), tone=tr_,
                 roles={"s0": "cut", "s1": "end_grain"})
        # lattice skirt, framed, over the dark crawl space
        fw, fth, lw, lt = la["frame_m"], la["frame_thickness_m"], la["lath_width_m"], la["lath_m"]
        zl = Dp - la["setback_m"]
        tl = self.tone("lattice")
        z0f = zl - fth
        self.box(F, "lattice_frame", 0.0, Wf, 0.0, fw, z0f, zl, skip=("back", "bottom"), tone=tl,
                 roles={"s0": "cut", "s1": "end_grain"})
        self.box(F, "lattice_frame", 0.0, Wf, y_rim0 - fw, y_rim0, z0f, zl, skip=("back", "top"), tone=tl,
                 roles={"s0": "cut", "s1": "end_grain"})
        self.box(F, "lattice_frame", 0.0, fw, fw, y_rim0 - fw, z0f, zl, skip=("back", "top", "bottom"), tone=tl,
                 roles={"s0": "cut"})
        self.box(F, "lattice_frame", Wf - fw, Wf, fw, y_rim0 - fw, z0f, zl, skip=("back", "top", "bottom"), tone=tl,
                 roles={"s1": "end_grain"})
        o0, o1, q0, q1 = fw, Wf - fw, fw, y_rim0 - fw          # the opening
        m = fw / 2
        clipr = [(o0 - m, q0 - m), (o1 + m, q0 - m), (o1 + m, q1 + m), (o0 - m, q1 + m)]
        hw_ = lw * math.sqrt(2) / 2
        step = la["pitch_m"] * math.sqrt(2)
        ylo, yhi = q0 - m - 1.0, q1 + m + 1.0
        n_layer = [0, 0]
        # T-3182: an `open` skirt (1720 Prairie's photograph: the floor's rim over a dark void)
        # keeps the frame and the dark crawl space and lays no laths
        for layer, sign, zfront in ((0, 1, z0f), (1, -1, z0f - lt)) if v.get("skirt") != "open" else ():
            cmin = (o0 - m) - sign * yhi - 2 if sign > 0 else (o0 - m) + ylo - 2
            cmax = (o1 + m) - sign * ylo + 2 if sign > 0 else (o1 + m) + yhi + 2
            cc = cmin
            while cc <= cmax:
                quad = [(cc - hw_ + sign * ylo, ylo), (cc + hw_ + sign * ylo, ylo),
                        (cc + hw_ + sign * yhi, yhi), (cc - hw_ + sign * yhi, yhi)]
                poly = K06.clip(ccw(quad), clipr)
                cc += step
                if len(poly) < 3 or abs(area2(poly)) < 1e-6:
                    continue
                n_layer[layer] += 1
                self.poly(F, "lattice", [(s, y, zfront) for s, y in poly], (0, 0, 1), tl)
                cx = math.fsum(p_[0] for p_ in poly) / len(poly)
                cy = math.fsum(p_[1] for p_ in poly) / len(poly)
                for i in range(len(poly)):
                    a, b = poly[i], poly[(i + 1) % len(poly)]
                    on_clip = any(abs(a[0] - e) < 1e-9 and abs(b[0] - e) < 1e-9 for e in (o0 - m, o1 + m)) or \
                        any(abs(a[1] - e) < 1e-9 and abs(b[1] - e) < 1e-9 for e in (q0 - m, q1 + m))
                    if on_clip:
                        continue
                    mm = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
                    self.poly(F, "lattice", [(a[0], a[1], zfront - lt), (b[0], b[1], zfront - lt), (b[0], b[1], zfront),
                                             (a[0], a[1], zfront)], (mm[0] - cx, mm[1] - cy, 0), tl)
        zcr = z0f - 2 * lt - la["crawl_m"]
        self.poly(F, "crawl", [(o0, q0, zcr), (o1, q0, zcr), (o1, q1, zcr), (o0, q1, zcr)], (0, 0, 1))
        rect = [(o0, q0), (o1, q0), (o1, q1), (o0, q1)]
        for i in range(4):
            a, b = rect[i], rect[(i + 1) % 4]
            mm = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
            cx, cy = (o0 + o1) / 2, (q0 + q1) / 2
            self.poly(F, "crawl", [(a[0], a[1], zcr), (b[0], b[1], zcr), (b[0], b[1], z0f - 2 * lt), (a[0], a[1], z0f - 2 * lt)],
                      (cx - mm[0], cy - mm[1], 0))
        self.meta["lattice"] = {"laths": n_layer, "pitch_m": la["pitch_m"], "layers_z": [round(z0f, 6), round(z0f - lt, 6)]}
        # the post: square blocks, a chamfered shaft, flat chamfer stops
        a, chm = pt["section_m"] / 2, pt["chamfer_m"]
        sp = Wf - a - v.get("post_inset_m", 0.05)     # T-2519: the post's outer face in from the floor's end
        tp_ = self.tone("post")
        y_b, y_h = yf + pt["base_m"], yp - pt["head_m"]
        octo = octagon(a, chm)

        def post_at(sp):
            for (y0, y1, skip) in ((yf, y_b, ("bottom", "top")), (y_h, yp, ("bottom", "top"))):
                self.box(F, "post", sp - a, sp + a, y0, y1, zp - a, zp + a, skip=skip, tone=tp_)
            for i in range(8):
                (ds0, dz0), (ds1, dz1) = octo[i], octo[(i + 1) % 8]
                self.poly(F, "post", [(sp + ds0, y_b, zp + dz0), (sp + ds1, y_b, zp + dz1), (sp + ds1, y_h, zp + dz1),
                                      (sp + ds0, y_h, zp + dz0)], ((ds0 + ds1) / 2, 0, (dz0 + dz1) / 2), tp_)
            for i in range(1, 8, 2):    # the four chamfer stops on each block, the corner triangles
                (ds0, dz0), (ds1, dz1) = octo[i - 1], octo[i]
                corner = (math.copysign(a, ds0 + ds1), math.copysign(a, dz0 + dz1))
                for yy, hy in ((y_b, 1), (y_h, -1)):
                    self.poly(F, "post", [(sp + ds0, yy, zp + dz0), (sp + corner[0], yy, zp + corner[1]), (sp + ds1, yy, zp + dz1)],
                              (0, hy, 0), tp_)

        inner = v.get("inner_posts_m", [])     # T-3180: a long porch's posts between its ends
        pair = v.get("pair_m")     # T-3181: every post doubled, the pair's centres this far apart
        if pair:     # the end pair keeps its outer post at the floor's end; an inner pair straddles its place
            groups = [(s_in - pair / 2, s_in + pair / 2) for s_in in sorted(inner)] + [(sp - pair, sp)]
        else:
            groups = [(s_in, s_in) for s_in in sorted(inner)] + [(sp, sp)]
        for g0, g1 in groups:
            for s_p in sorted({g0, g1}):
                post_at(s_p)
        if pair:
            self.meta["posts_s_m"] = [round(s_p, 6) for g in groups for s_p in g]
        # the plate, the brackets under it, the beaded ceiling, the roof over all
        self.box(F, "plate", 0.0, Wf + 0.05, yp, yc, zp - pd / 2, zp + pd / 2, skip=("top",), tone=self.tone("plate"),
                 roles={"s0": "cut", "s1": "end_grain"})
        # T-3181: the openings between the post groups, the middle one spanning the mirror line
        openings = [(-(groups[0][0] - a), groups[0][0] - a)]
        openings += [(g[1] + a, h[0] - a) for g, h in zip(groups, groups[1:])]
        if v.get("arcade"):     # T-3181: a segmental arch over every opening, no brackets
            self._porch_arcade(F, v["arcade"], openings, zp - pd / 2, zp + pd / 2, yp)
        if v.get("balustrade"):     # T-3181: a turned balustrade in every opening but the stair's
            self._porch_balustrade(F, v["balustrade"], openings[1:], zp, yf)
        if v.get("cresting"):       # T-3181: iron cresting round the roof's deck
            self._porch_cresting(F, v["cresting"], Wf + 0.05 + ov_r, zp + pd / 2 + ov_r, yc + po["roof_m"])
        if v.get("arch"):     # T-2425: an arched head between the posts takes the brackets' place
            self._porch_arch(F, v["arch"], sp - a, zp - pd / 2, zp + pd / 2, yp)
        elif v.get("arcade"):
            pass
        else:
            br = dict(tr["bracket"], drop_m=pt["head_m"], reach_m=0.28)
            for s_p in [s_p for g in groups for s_p in sorted({g[0], g[1]})]:
                self.bracket(F, s_p - a, zp, yp, br, br["thickness_m"], along_s=True, outward=-1.0, tone=tp_)
                self.bracket(F, s_p + a, zp, yp, br, br["thickness_m"], along_s=True, outward=1.0, tone=tp_)
        if v.get("stoop"):    # T-2425: steps up between cheek walls in the posts' line
            self._porch_stoop(F, v["stoop"], sp, a, zp + a, Dp + fl["nosing_m"], yf)
        z_in = zp - pd / 2
        bw_, bead, bdp = ce["board_width_m"], ce["bead_m"], ce["bead_depth_m"]
        nbc = int(z_in / bw_)
        edges = [i * (z_in / nbc) for i in range(nbc + 1)]
        tcl = self.tone("ceiling")
        for i in range(nbc):
            za = edges[i] + (bead / 2 if i > 0 else 0.0)
            zb = edges[i + 1] - (bead / 2 if i < nbc - 1 else 0.0)
            self.poly(F, "ceiling", [(0, yc, za), (Wf + 0.05, yc, za), (Wf + 0.05, yc, zb), (0, yc, zb)], (0, -1, 0), tcl)
        for i in range(1, nbc):
            zm = edges[i]
            self.poly(F, "ceiling", [(0, yc, zm - bead / 2), (0, yc + bdp, zm), (Wf + 0.05, yc + bdp, zm),
                                     (Wf + 0.05, yc, zm - bead / 2)], (0, -1, 1), tcl)
            self.poly(F, "ceiling", [(0, yc + bdp, zm), (0, yc, zm + bead / 2), (Wf + 0.05, yc, zm + bead / 2),
                                     (Wf + 0.05, yc + bdp, zm)], (0, -1, -1), tcl)
        zr = zp + pd / 2 + ov_r
        sr = Wf + 0.05 + ov_r
        yr = yc + po["roof_m"]
        self.poly(F, "roof", [(0, yr, 0), (0, yr, zr), (sr, yr, zr), (sr, yr, 0)], (0, 1, 0))
        self.poly(F, "fascia", [(0, yc, zr), (sr, yc, zr), (sr, yr, zr), (0, yr, zr)], (0, 0, 1), self.tone("fascia"))
        self.poly(F, "fascia", [(sr, yc, 0), (sr, yr, 0), (sr, yr, zr), (sr, yc, zr)], (1, 0, 0), self.tone("fascia"))
        self.poly(F, "cut", [(0, yc, 0), (0, yc, zr), (0, yr, zr), (0, yr, 0)], (-1, 0, 0))
        self.poly(F, "soffit", [(0, yc, zp + pd / 2), (sr, yc, zp + pd / 2), (sr, yc, zr), (0, yc, zr)], (0, -1, 0))
        self.poly(F, "soffit", [(Wf + 0.05, yc, 0), (sr, yc, 0), (sr, yc, zp + pd / 2), (Wf + 0.05, yc, zp + pd / 2)],
                  (0, -1, 0))
        self.meta.update({"floor_width_m": round(Wf, 6), "focus": [Wf * 0.62, 1.3, Dp * 0.8], "span_m": 3.0})

    def _porch_arcade(self, F, ar, openings, z0, z1, yp):
        """T-3181: 1720's arcade, a segmental arch over every opening between the post groups,
        springing `spring_below_plate_m` under the plate and rising `rise_m` to its crown (the
        middle opening, across the mirror line, `middle_rise_m`), its spandrel a solid board
        as deep as the plate. An opening is (s_a, s_b) between post faces; the middle one's
        s_a is its mirror image, and only its half from s 0 is built."""
        y_sp = yp - ar["spring_below_plate_m"]
        tsp = self.tone("spandrel")
        built = []
        for i, (s_a, s_b) in enumerate(openings):
            h = ar["middle_rise_m"] if i == 0 else ar["rise_m"]
            c = (s_b - s_a) / 2
            if not (0.0 < h <= c and y_sp + h < yp - 0.02):
                raise ValueError(f"{self.v['id']}: an arch rising {h} m over {2 * c:.3f} m does not stand under its plate")
            R = (c * c + h * h) / (2 * h)
            cs, cy = (s_a + s_b) / 2, y_sp + h - R
            s_lo = max(s_a, 0.0)
            n = max(3, math.ceil((s_b - s_lo) / 0.25))
            arc_ = [(s_lo + (s_b - s_lo) * k / n, 0.0) for k in range(n + 1)]
            arc_ = [(s, cy + math.sqrt(max(0.0, R * R - (s - cs) ** 2))) for s, _ in arc_]
            for (sa, ya), (sb, yb) in zip(arc_, arc_[1:]):
                self.poly(F, "spandrel", [(sa, ya, z1), (sb, yb, z1), (sb, yp, z1), (sa, yp, z1)], (0, 0, 1), tsp)
                self.poly(F, "spandrel", [(sa, ya, z0), (sa, yp, z0), (sb, yp, z0), (sb, yb, z0)], (0, 0, -1), tsp)
                m = ((sa + sb) / 2, (ya + yb) / 2)
                self.poly(F, "spandrel", [(sa, ya, z0), (sb, yb, z0), (sb, yb, z1), (sa, ya, z1)],
                          (cs - m[0], cy - m[1], 0), tsp)
            built.append({"span_m": round(2 * c, 6), "rise_m": h, "radius_m": round(R, 6)})
        self.meta["arcade"] = {"spring_m": round(y_sp, 6), "arches": built}

    def _turned(self, F, role, s_c, z_c, y0, y1, w, prof, tone=1.0):
        """T-3181: a turned baluster or newel's shaft, square-turned: four faces whose edge runs
        the profile [(half-width as a share of w / 2, share of the height)] from y0 up to y1,
        its ends hidden in the rails it stands between."""
        rings = [(f * w / 2, y0 + t * (y1 - y0)) for f, t in prof]
        sides = (((1, 0), (1, 1), (1, -1)), ((0, 1), (-1, 1), (1, 1)),
                 ((-1, 0), (-1, -1), (-1, 1)), ((0, -1), (1, -1), (-1, -1)))
        for (r0, ya), (r1, yb) in zip(rings, rings[1:]):
            for (ns, nz), (pa_s, pa_z), (pb_s, pb_z) in sides:
                self.poly(F, role, [(s_c + pa_s * r0, ya, z_c + pa_z * r0), (s_c + pb_s * r0, ya, z_c + pb_z * r0),
                                    (s_c + pb_s * r1, yb, z_c + pb_z * r1), (s_c + pa_s * r1, yb, z_c + pa_z * r1)],
                          (ns, 0, nz), tone)

    def _porch_balustrade(self, F, bl, openings, zp, yf):
        """T-3181: a turned balustrade in the posts' line across each opening: a bottom rail on
        the floor, balusters at `pitch_m` (each opening divided evenly), and a moulded top rail
        `height_m` over the floor, its ends dying into the posts."""
        H, p = bl["height_m"], bl["pitch_m"]
        bh, bw = bl["bottom_rail_m"]
        th, tw = bl["top_rail_m"]
        tr = self.tone("rail")
        count = 0
        for s_a, s_b in openings:
            self.box(F, "rail", s_a, s_b, yf, yf + bh, zp - bw / 2, zp + bw / 2, skip=("bottom", "s0", "s1"), tone=tr)
            self.box(F, "rail", s_a, s_b, yf + H - th, yf + H, zp - tw / 2, zp + tw / 2, skip=("s0", "s1"), tone=tr)
            n = max(1, round((s_b - s_a) / p))
            for j in range(n):
                s_c = s_a + (s_b - s_a) * (j + 0.5) / n
                self._turned(F, "baluster", s_c, zp, yf + bh, yf + H - th, bl["baluster_m"], BALUSTER, self.tone("baluster", j))
            count += n
        self.meta["balustrade"] = {"height_m": H, "balusters": count}

    def _porch_cresting(self, F, cr, sr, zr, yr):
        """T-3181: iron cresting on the porch roof's deck, `inset_m` in from its edge along the
        front and back along its open end to `return_to_m` from the wall: a base bar and a top
        bar `height_m` over the deck, square bars between them at `bar_pitch_m`, and posts at
        no more than `post_pitch_m` standing `post_above_m` over the top bar, each under a
        pointed knob. Iron, so bound to the boundary's iron and outside the timber rules."""
        H, ci = cr["height_m"], cr["inset_m"]
        bb, tb, bar, pm = cr["base_bar_m"], cr["top_bar_m"], cr["bar_m"], cr["post_m"]
        S, Z, Z0 = sr - ci, zr - ci, cr["return_to_m"]
        nbar = npost = 0
        y_top = yr + H + cr["post_above_m"]

        def post(s_c, z_c):
            self.box(F, "cresting", s_c - pm / 2, s_c + pm / 2, yr + bb, y_top, z_c - pm / 2, z_c + pm / 2,
                     skip=("bottom", "top"))
            tip = (s_c, y_top + cr["knob_m"], z_c)
            q = [(s_c - pm / 2, y_top, z_c + pm / 2), (s_c + pm / 2, y_top, z_c + pm / 2),
                 (s_c + pm / 2, y_top, z_c - pm / 2), (s_c - pm / 2, y_top, z_c - pm / 2)]
            for i in range(4):
                a_, b_ = q[i], q[(i + 1) % 4]
                self.poly(F, "cresting", [a_, b_, tip], ((a_[0] + b_[0]) / 2 - s_c, 0.3, (a_[2] + b_[2]) / 2 - z_c))

        # the front run: its bars wrap the corner, and it meets its mirror at s 0 with no post there
        for y0, y1, h, sk in ((yr, yr + bb, bb / 2, ("bottom", "s0")), (yr + H - tb, yr + H, tb / 2, ("s0",))):
            self.box(F, "cresting", 0.0, S + h, y0, y1, Z - h, Z + h, skip=sk)
        k = max(1, round(S / cr["bar_pitch_m"]))
        for j in range(k):
            u = S * (j + 0.5) / k
            self.box(F, "cresting", u - bar / 2, u + bar / 2, yr + bb, yr + H - tb, Z - bar / 2, Z + bar / 2,
                     skip=("bottom", "top"))
        nbar += k
        m = max(1, math.ceil(S / cr["post_pitch_m"]))
        for j in range(1, m + 1):
            post(S * j / m, Z)
        npost += m
        # the return along the open end, from the front run's back face to `return_to_m`
        for y0, y1, h, sk in ((yr, yr + bb, bb / 2, ("bottom", "front")), (yr + H - tb, yr + H, tb / 2, ("front",))):
            self.box(F, "cresting", S - h, S + h, y0, y1, Z0, Z - h, skip=sk)
        L = Z - Z0
        k = max(1, round(L / cr["bar_pitch_m"]))
        for j in range(k):
            u = Z0 + L * (j + 0.5) / k
            self.box(F, "cresting", S - bar / 2, S + bar / 2, yr + bb, yr + H - tb, u - bar / 2, u + bar / 2,
                     skip=("bottom", "top"))
        nbar += k
        m = max(1, math.ceil(L / cr["post_pitch_m"]))
        for j in range(m):
            post(S, Z0 + L * j / m)
        npost += m
        self.meta["cresting"] = {"height_m": H, "bars": nbar, "posts": npost}

    def _porch_arch(self, F, ar, w, z0, z1, yp):
        """T-2425: the half of a four-centred pointed arch between the porch's middle (s 0) and
        its post's inner face (s w), springing `spring_below_plate_m` under the plate and rising
        `rise_m` to a point: a lower arc of `lower_radius_ratio` x w swept `lower_sweep_deg` from
        the spring, then a flatter arc tangent to it whose centre lies past the middle, so the
        two halves meet in a point; or, `kind: trefoil` (T-2519), a cusped trefoil arch
        (`_trefoil_curve`). The spandrel over it is a solid board as deep as the plate,
        pierced by a quatrefoil of four lobes `lobe_m` in radius, `quatrefoil_inset_m` [in from
        the post, down from the plate] to its middle."""
        y_sp = yp - ar["spring_below_plate_m"]
        if ar.get("kind") == "trefoil":     # T-2519
            curve, h, radii = self._trefoil_curve(ar, w, y_sp)
        else:
            h = ar["rise_m"]
            r1 = ar["lower_radius_ratio"] * w
            al = math.radians(ar["lower_sweep_deg"])
            k = (r1 * r1 - (w - r1) ** 2 - h * h) / (2 * ((w - r1) * math.cos(al) - h * math.sin(al) + r1))
            r2 = r1 - k
            c1 = (w - r1, y_sp)
            c2 = (w - r1 + k * math.cos(al), y_sp + k * math.sin(al))
            if not (r2 > r1 and c2[0] < 0):
                raise ValueError(f"{self.v['id']}: the arch does not close in a point (r2 {r2:.3f}, centre {c2[0]:.3f})")
            a_cr = math.atan2(y_sp + h - c2[1], -c2[0])
            n1, n2 = 8, 10
            curve = [((c1[0] + r1 * math.cos(al * i / n1), c1[1] + r1 * math.sin(al * i / n1)), c1) for i in range(n1)]
            curve += [((c2[0] + r2 * math.cos(al + (a_cr - al) * i / n2), c2[1] + r2 * math.sin(al + (a_cr - al) * i / n2)), c2)
                      for i in range(n2)]
            curve.append(((0.0, y_sp + h), c2))
            radii = [r1, r2]
        if y_sp + h > yp - 0.005:
            raise ValueError(f"{self.v['id']}: the arch's crown ({y_sp + h:.3f}) stands in the plate ({yp:.3f})")
        # the quatrefoil: the far side of four circles through its middle, on the axes
        lr = ar["lobe_m"]
        qc = (w - ar["quatrefoil_inset_m"][0], yp - ar["quatrefoil_inset_m"][1])
        hole = []
        for i in range(48):
            t = 2 * math.pi * i / 48
            r = max(lr * math.cos(t - f) + math.sqrt(max(0.0, lr * lr - (lr * math.sin(t - f)) ** 2))
                    for f in (0.0, math.pi / 2, math.pi, 1.5 * math.pi))
            hole.append((qc[0] + r * math.cos(t), qc[1] + r * math.sin(t)))
        outer = [p for p, _ in reversed(curve)] + [(w, yp), (0.0, yp)]
        for q in hole:     # the piercing stands clear of the arch and the board's edges
            if not (q[0] < w - 0.02 and q[1] < yp - 0.02 and inside(q, outer)):
                raise ValueError(f"{self.v['id']}: the quatrefoil breaks out of its spandrel")
        holes = [hole]
        if ar.get("fret"):     # T-2533: the board's field cut away round the quatrefoil's ring
            holes += self._fret_openings(ar["fret"], curve, outer, w, yp, qc,
                                         max(math.hypot(q[0] - qc[0], q[1] - qc[1]) for q in hole))
        pts = outer + [q for h in holes for q in h]
        tsp = self.tone("spandrel")
        for tri in K09.triangulate(outer, holes):
            tq = [pts[i] for i in tri]
            self.poly(F, "spandrel", [(x, y, z1) for x, y in tq], (0, 0, 1), tsp)
            self.poly(F, "spandrel", [(x, y, z0) for x, y in tq], (0, 0, -1), tsp)
        for i in range(len(curve) - 1):     # the arch's soffit, crown to spring
            (p, c), (q, _) = curve[i + 1], curve[i]
            m = ((p[0] + q[0]) / 2, (p[1] + q[1]) / 2)
            self.poly(F, "spandrel", [(p[0], p[1], z0), (q[0], q[1], z0), (q[0], q[1], z1), (p[0], p[1], z1)],
                      (c[0] - m[0], c[1] - m[1], 0), tsp)
        for hl in holes:                    # the piercings' cut edges, facing into each one
            hc = qc if hl is hole else (math.fsum(q[0] for q in hl) / len(hl), math.fsum(q[1] for q in hl) / len(hl))
            for i in range(len(hl)):
                p, q = hl[i], hl[(i + 1) % len(hl)]
                m = ((p[0] + q[0]) / 2, (p[1] + q[1]) / 2)
                self.poly(F, "spandrel", [(p[0], p[1], z0), (q[0], q[1], z0), (q[0], q[1], z1), (p[0], p[1], z1)],
                          (hc[0] - m[0], hc[1] - m[1], 0), tsp)
        self.meta["arch"] = {"spring_m": round(y_sp, 6), "crown_m": round(y_sp + h, 6), "half_span_m": round(w, 6),
                             "radii_m": [round(r, 6) for r in radii], "quatrefoil_m": [round(qc[0], 6), round(qc[1], 6)]}
        if len(holes) > 1:
            self.meta["arch"]["fret_openings_m2"] = [round(abs(area2(hl)) / 2, 6) for hl in holes[1:]]

    def _fret_openings(self, fr, curve, outer, w, yp, qc, r_q):
        """T-2533: the trefoil's spandrel as open fretwork. What stands of the board is a band
        round the head foil `head_band_m` broad and round each side foil `side_band_m` broad, a
        ring round the quatrefoil out to `ring_m` from its middle, a tie `tie_m` broad from the
        ring down to the cusp, pierced by a round eye `eye_m` across standing `eye_at_m` from the
        quatrefoil's middle (`r_q` is the quatrefoil's own reach), and a frame `rim_m` broad along the post, under the plate and at the
        middle where the two halves meet; every other part of the field is cut away. Each opening
        is found on a 5 mm grid, kept if a circle `min_opening_m` across fits in it, and traced
        from its widest point by marching rays out to the solid (the clearance is an exact
        distance, so each step may go as far as it reads). Returns the openings and the eye as
        polygons, wound either way."""
        R, e, tie = fr["ring_m"], fr["rim_m"], fr["tie_m"]
        cs, ch = curve[0][1], curve[-1][1]
        rs = math.hypot(curve[0][0][0] - cs[0], curve[0][0][1] - cs[1]) + fr["side_band_m"]
        rh = math.hypot(curve[-1][0][0] - ch[0], curve[-1][0][1] - ch[1]) + fr["head_band_m"]
        cusp = next(p for p, c in curve if c != cs)
        L = math.hypot(cusp[0] - qc[0], cusp[1] - qc[1])
        if not r_q + 0.01 + fr["eye_m"] / 2 < fr["eye_at_m"] < L - fr["eye_m"] / 2 or fr["eye_m"] >= tie - 0.02:
            raise ValueError(f"{self.v['id']}: the fretwork's eye does not stand within its tie, clear of the quatrefoil and cusp")

        def seg_d(p, a, b):
            ab = (b[0] - a[0], b[1] - a[1])
            t = max(0.0, min(1.0, ((p[0] - a[0]) * ab[0] + (p[1] - a[1]) * ab[1]) / (ab[0] ** 2 + ab[1] ** 2)))
            return math.hypot(p[0] - a[0] - t * ab[0], p[1] - a[1] - t * ab[1])

        def clear(p):
            return min(math.hypot(p[0] - ch[0], p[1] - ch[1]) - rh, math.hypot(p[0] - cs[0], p[1] - cs[1]) - rs,
                       math.hypot(p[0] - qc[0], p[1] - qc[1]) - R, seg_d(p, qc, cusp) - tie / 2,
                       w - e - p[0], yp - e - p[1], p[0] - e / 2)
        g = 0.005
        y_lo = min(q[1] for q in outer)
        nx, ny = int(w / g) + 1, int((yp - y_lo) / g) + 1
        val = {}
        for i in range(nx):
            for j in range(ny):
                p = (i * g, y_lo + j * g)
                if inside(p, outer):
                    c = clear(p)
                    if c > 0:
                        val[(i, j)] = c
        out, seen = [], set()
        for start in sorted(val):
            if start in seen:
                continue
            comp, stack = [], [start]
            seen.add(start)
            while stack:
                c = stack.pop()
                comp.append(c)
                for d in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    n = (c[0] + d[0], c[1] + d[1])
                    if n in val and n not in seen:
                        seen.add(n)
                        stack.append(n)
            top = max(comp, key=lambda c: (val[c], c))
            if 2 * val[top] < fr["min_opening_m"]:
                continue
            s0 = (top[0] * g, y_lo + top[1] * g)
            poly = []
            for k in range(96):
                t, dr = 0.0, (math.cos(2 * math.pi * k / 96), math.sin(2 * math.pi * k / 96))
                for _ in range(200):
                    d = clear((s0[0] + t * dr[0], s0[1] + t * dr[1]))
                    if d < 1e-5:
                        break
                    t += d
                poly.append((s0[0] + t * dr[0], s0[1] + t * dr[1]))
            for c in comp:     # traced from its widest point, the opening must hold all of itself
                if val[c] > 2 * g and not inside((c[0] * g, y_lo + c[1] * g), poly):
                    raise ValueError(f"{self.v['id']}: a fretwork opening cannot be traced from its middle")
            out.append(poly)
        t = fr["eye_at_m"] / L
        ec = (qc[0] + t * (cusp[0] - qc[0]), qc[1] + t * (cusp[1] - qc[1]))
        out.append([(ec[0] + fr["eye_m"] / 2 * math.cos(math.pi * k / 12), ec[1] + fr["eye_m"] / 2 * math.sin(math.pi * k / 12))
                    for k in range(24)])
        return out

    def _trefoil_curve(self, ar, w, y_sp):
        """T-2519: the half of a cusped trefoil arch, from its spring at the post's inner face
        (s w) to its crown at the middle (s 0): a side foil of radius `foil_radius_m` tangent to
        the post at the spring, its centre level with it, swept up over its top until it meets
        the head, a round foil of radius `head_radius_m` centred on the middle `head_over_spring_m`
        over the spring, in a cusp; then the head on to its crown. Returns the curve as (point,
        centre) pairs, the crown's height over the spring and the two radii."""
        rs, rh = ar["foil_radius_m"], ar["head_radius_m"]
        cs, ch = (w - rs, y_sp), (0.0, y_sp + ar["head_over_spring_m"])
        dx, dy = ch[0] - cs[0], ch[1] - cs[1]
        d = math.hypot(dx, dy)
        if not (abs(rh - rs) < d < rh + rs) or cs[0] <= 0:
            raise ValueError(f"{self.v['id']}: the trefoil's head and side foils do not meet in a cusp")
        a_ = (rs * rs - rh * rh + d * d) / (2 * d)
        hh = math.sqrt(max(0.0, rs * rs - a_ * a_))
        mx, my = cs[0] + a_ * dx / d, cs[1] + a_ * dy / d
        cusp = max(((mx - hh * dy / d, my + hh * dx / d), (mx + hh * dy / d, my - hh * dx / d)), key=lambda q: q[1])
        if not 0.0 < cusp[0] < w:
            raise ValueError(f"{self.v['id']}: the trefoil's cusp falls outside its half-span")
        t1 = math.atan2(cusp[1] - cs[1], cusp[0] - cs[0])
        t2 = math.atan2(cusp[1] - ch[1], cusp[0] - ch[0])
        n1, n2 = 10, 10
        curve = [((cs[0] + rs * math.cos(t1 * i / n1), cs[1] + rs * math.sin(t1 * i / n1)), cs) for i in range(n1)]
        curve += [((ch[0] + rh * math.cos(t2 + (math.pi / 2 - t2) * i / n2),
                    ch[1] + rh * math.sin(t2 + (math.pi / 2 - t2) * i / n2)), ch) for i in range(n2)]
        curve.append(((0.0, ch[1] + rh), ch))
        return curve, ch[1] + rh - y_sp, [rs, rh]

    def _porch_stoop(self, F, so, sp, a, z_back, z_edge, yf):
        """T-2425: the half of a stoop from grade to the porch floor (the floor is its top tread),
        every riser equal and solved from the floor height under `max_riser_m`, between the
        middle and a cheek wall standing in the post's line, as broad as the post: the cheek
        runs out from the post's face over the steps, its top `cheek_above_m` over the nosings'
        line, and ends square at the foot."""
        n = max(2, math.ceil(yf / so["max_riser_m"] - 1e-9))
        r, g = yf / n, so["going_m"]
        s_in = sp - a
        ts = self.tone("stoop")
        for k in range(1, n):
            z0 = z_edge + (n - 1 - k) * g
            self.box(F, "step_riser", 0.0, s_in, 0.0, k * r, z0, z0 + g, skip=("back", "bottom", "s0", "s1"),
                     tone=self.tone("step", k), roles={"top": "step_tread"})
        z_foot = z_edge + (n - 1) * g
        ca = so["cheek_above_m"]
        top = lambda z: ca + yf - (yf - r) * (z - z_edge) / (z_foot - z_edge)
        side = [(z_back, 0.0), (z_foot, 0.0), (z_foot, top(z_foot)), (z_edge, top(z_edge)), (z_back, top(z_edge))]
        for s_, hs in ((sp - a, -1), (sp + a, 1)):
            self.poly(F, "skirt", [(s_, y, z) for z, y in side], (hs, 0, 0), ts)
        self.poly(F, "skirt", [(sp - a, 0.0, z_foot), (sp + a, 0.0, z_foot), (sp + a, top(z_foot), z_foot),
                               (sp - a, top(z_foot), z_foot)], (0, 0, 1), ts)
        for (za, zb) in ((z_back, z_edge), (z_edge, z_foot)):
            self.poly(F, "skirt", [(sp - a, top(max(za, z_edge)), za), (sp - a, top(zb), zb), (sp + a, top(zb), zb),
                                   (sp + a, top(max(za, z_edge)), za)], (0, 1, 0), ts)
        self.meta["stoop"] = {"risers": n, "riser_m": round(r, 6), "going_m": g, "foot_z_m": round(z_foot, 6),
                              "width_m": round(2 * s_in, 6)}


class CasedOpening(K06.Opening):
    """K06's sash, glass, blind, curtain and room in a timber wall: K16 lays the sill,
    the casing and the drip cap, so K06's stone sill and head band are not built."""

    def _sill(self, holes, rev, run, sill):
        return None

    def _head_band(self, holes, hb):
        return None

    def _well(self, holes, wl):
        return None


# -- a house in the scene (T-2323) ---------------------------------------------------------------
#
# A k16_timber record names the timber parts of ONE house's street front — a Gothic gable, a
# clapboard wall with its corner, a porch — as kit variants in full, and the plain body they
# stand against. The parts are built in the kit's own frame (front facing +z, s to a viewer's
# right) at their places along the front, merged into one mesh, and turned so the front faces
# the record's `faces` bearing. The specimen's board roles go: the backdrop and the plaster
# face are the body's, and the wall ends ("cut") are painted as the body they run into.

STAND_IN = {"color": (0.8, 0.75, 0.62), "roughness": 0.85, "class": "stand_in"}
#: a front's own outward normal, in the scene's frame (x east, -z north), by the street it faces
FACES = {"east": ((0.0, 0.0, 1.0), (1.0, 0.0, 0.0)), "south": ((0.0, 0.0, 1.0), (0.0, 0.0, 1.0))}


def mirror_s(sm: Sample, c: float) -> Sample:
    """Reflect a built sample across the plane s = c: positions and normals reflected, each
    triangle's winding turned so it still faces out."""
    for pr in sm.prims.values():
        pr.pos = [(2 * c - x, y, z) for x, y, z in pr.pos]
        pr.nrm = [(-x, y, z) for x, y, z in pr.nrm]
        pr.idx = [i for t in range(0, len(pr.idx), 3) for i in (pr.idx[t], pr.idx[t + 2], pr.idx[t + 1])]
    return sm


def _rot_y(p, k):
    """Turn a point a quarter-turn k times about y: +z to +x for k = 1."""
    x, y, z = p
    for _ in range(k % 4):
        x, z = z, -x
    return (x, y, z)


def gabled_body(sm: Sample, s0, s1, z0, z1, y_eave, y_ridge, ridge_along: str, lift=0.0, skip=(), s1_wall_to=None):
    """A closed plain block under a two-slope roof, role stand_in / stand_in_roof. The ridge
    runs along s (`ridge_along="s"`, slopes to front and back) or along z (gable ends front and
    back). The walls stop at y_eave; `lift` raises the roof's eave line above it (a roof's own
    thickness at a verge, a boxed eave's depth) and the strip between is closed. `skip` names
    faces not built; `s1_wall_to` stops the s1 wall short of z1 (where a timber return is)."""
    F = sm.F
    ye, yr = y_eave + lift, y_ridge + lift
    walls = {"s0": ([(s0, 0, z0), (s0, 0, z1), (s0, y_eave, z1), (s0, y_eave, z0)], (-1, 0, 0)),
             "s1": ([(s1, 0, z0), (s1, y_eave, z0), (s1, y_eave, s1_wall_to if s1_wall_to is not None else z1),
                     (s1, 0, s1_wall_to if s1_wall_to is not None else z1)], (1, 0, 0)),
             "back": ([(s0, 0, z0), (s0, y_eave, z0), (s1, y_eave, z0), (s1, 0, z0)], (0, 0, -1))}
    for k, (pts, h) in walls.items():
        if k not in skip:
            sm.poly(F, "stand_in", pts, h)
    if ridge_along == "z":
        sm_ = (s0 + s1) / 2
        for a, b, h in ((s0, sm_, (-1, 1, 0)), (sm_, s1, (1, 1, 0))):
            ya, yb = (ye, yr) if a == s0 else (yr, ye)
            sm.poly(F, "stand_in_roof", [(a, ya, z0), (b, yb, z0), (b, yb, z1), (a, ya, z1)], h)
        if "back" not in skip:
            sm.poly(F, "stand_in", [(s0, y_eave, z0), (s0, ye, z0), (sm_, yr, z0), (s1, ye, z0), (s1, y_eave, z0)],
                    (0, 0, -1))
        for x, k, hs in ((s0, "s0", -1), (s1, "s1", 1)):
            if lift and k not in skip:
                sm.poly(F, "stand_in_roof", [(x, y_eave, z0), (x, y_eave, z1), (x, ye, z1), (x, ye, z0)], (hs, 0, 0))
    else:
        zm = (z0 + z1) / 2
        if lift and "back" not in skip:      # the back wall up to the roof's eave line
            sm.poly(F, "stand_in", [(s0, y_eave, z0), (s0, ye, z0), (s1, ye, z0), (s1, y_eave, z0)], (0, 0, -1))
        for a, b, h in ((z1, zm, (0, 1, 1)), (zm, z0, (0, 1, -1))):
            ya, yb = (ye, yr) if a == z1 else (yr, ye)
            sm.poly(F, "stand_in_roof", [(s0, ya, a), (s1, ya, a), (s1, yb, b), (s0, yb, b)], h)
        for x, k, hs in ((s0, "s0", -1), (s1, "s1", 1)):
            if k not in skip:
                sm.poly(F, "stand_in", [(x, y_eave, z1), (x, ye, z1), (x, yr, zm), (x, ye, z0), (x, y_eave, z0)],
                        (hs, 0, 0))


def canted_bay_body(sm: Sample, plan, height, roof_m=0.12):
    """A plain canted bay standing on the front: `plan` is (s, z) from the wall out and back
    to it, built as a prism to `height` under a flat roof slab."""
    F = sm.F
    for (sa, za), (sb, zb) in zip(plan, plan[1:]):
        n = (-(zb - za), 0, (sb - sa))        # outward for a plan running left to right
        sm.poly(F, "stand_in", [(sa, 0, za), (sb, 0, zb), (sb, height, zb), (sa, height, za)], n)
        sm.poly(F, "stand_in_roof", [(sa, height, za), (sb, height, zb), (sb, height + roof_m, zb),
                                     (sa, height + roof_m, za)], n)
    sm.poly(F, "stand_in_roof", [(s, height + roof_m, z) for s, z in plan], (0, 1, 0))


# -- T-2424: a canted bay built from its photograph --------------------------------------------
#
# A bay whose record names its `lights` is built like the tower: each of its faces a kit
# `clapboard_wall` with no return, a post (the kit's corner board, widened to the record's
# `post_m`) at each angle and a pointed light in a pointed casing between them. What runs round
# the angles is built round the plan instead, so every angle mitres: a panelled base under a
# weathered sill course, and a moulded cornice under a flat deck that falls from the wall.

#: the bay's faces, from the wall on the front's left round to the wall on its right
BAY_KEYS = tuple(f"bay.{i}" for i in range(3))
#: what a bay face does not keep of its kit wall: the base and the straight eave, which the
#: bay's own base and cornice replace round its angles
BAY_DROP = ("foundation", "water_table", "drip_cap", "soffit", "fascia", "roof", "bracket")
#: the least run of siding a face keeps between a post and its light's casing
BAY_MIN_SIDING = 0.05
#: the base, in (out from the face, up): plinth, chamfer, panelled field, sill course, its top
BAY_BASE = ((0.0, 0.0), (0.05, 0.0), (0.05, 0.12), (0.035, 0.14), (0.035, None), (0.075, None),
            (0.075, None), (0.03, None))
#: the cornice over the wall top: soffit, fascia, bed and crown mouldings, the top fillet
BAY_CORNICE = ((0.032, 0.0), (0.2, 0.0), (0.2, 0.2), (0.26, 0.27), (0.26, 0.32), (0.3, 0.36), (0.3, 0.42))


def bay_offset(plan, d):
    """The bay's plan (s, z) moved out by d, its angles mitred and its two ends kept on the wall."""
    seg = [(_unit((b[0] - a[0], 0.0, b[1] - a[1])), a, b) for a, b in zip(plan, plan[1:])]
    nrm = [(-u[2], u[0]) for u, _, _ in seg]
    out = []
    for j, p in enumerate(plan):
        if j in (0, len(plan) - 1):
            i = 0 if j == 0 else len(seg) - 1
            u, n = seg[i][0], nrm[i]
            t = -(p[1] + d * n[1]) / u[2]
            out.append((p[0] + d * n[0] + t * u[0], 0.0))
        else:
            a, b = nrm[j - 1], nrm[j]
            k = d / (1.0 + a[0] * b[0] + a[1] * b[1])
            out.append((p[0] + k * (a[0] + b[0]), p[1] + k * (a[1] + b[1])))
    return out, nrm


def bay_ring(sm: Sample, plan, profile, roles, y0=0.0):
    """A profile in (out, up) carried round the bay's plan from the wall to the wall, mitred
    at every angle; roles[i] names the face on profile edge i (None: hidden, not built)."""
    rings = [bay_offset(plan, o) for o, _ in profile]
    for i, r in enumerate(roles):
        if not r:
            continue
        (oa, ya), (ob, yb) = profile[i], profile[i + 1]
        (pa, nrm), (pb, _) = rings[i], rings[i + 1]
        for j, n in enumerate(nrm):
            hint = (n[0] * (yb - ya), oa - ob, n[1] * (yb - ya))
            sm.face(r, [(pa[j][0], y0 + ya, pa[j][1]), (pa[j + 1][0], y0 + ya, pa[j + 1][1]),
                        (pb[j + 1][0], y0 + yb, pb[j + 1][1]), (pb[j][0], y0 + yb, pb[j][1])], hint)


def bay_parts(st: dict, form: dict, data: dict) -> dict:
    """The bay's faces, each a kit wall set down on its side of the plan."""
    sid = st["id"]
    bv = form["canted_bay"]["value"]
    lt = bv["lights"]
    plan = [tuple(q) for q in bv["plan"]]
    ct = data["trim"]["corner_board"]["thickness_m"]
    cw = data["trim"]["casing"]["width_m"]
    out = {}
    for i, (a, b) in enumerate(zip(plan, plan[1:])):
        W = math.hypot(b[0] - a[0], b[1] - a[1])
        # a post at each angle, and a run of siding between it and the light's casing
        if W / 2 - lt["clear_width_m"] / 2 - cw - (bv["post_m"] - ct) < BAY_MIN_SIDING:
            raise ValueError(f"{sid}: canted bay face {i} is {W:.3f} m, too narrow for its light and posts")
        fd = copy.deepcopy(data)
        fd["trim"]["corner_board"]["width_m"] = bv["post_m"]
        fd["trim"]["frieze"]["height_m"] = bv["frieze_m"]
        wt = fd["trim"]["water_table"]
        v = {"id": f"k16.wall.{sid}.bay_{i}", "kind": "clapboard_wall", "use": "wall", "width_m": round(W, 6),
             "return_m": 0.0, "boards": [True, True],
             "foundation_m": round(bv["base_m"] - wt["height_m"] - wt["cap"]["height_m"], 6),
             "wall_top_m": bv["wall_top_m"],
             "windows": [dict(lt, centre_m=round(W / 2, 6))]}
        sm = Sample(v, fd).build()
        for role in BAY_DROP:
            sm.prims.pop(role, None)
        U = _unit((b[0] - a[0], 0.0, b[1] - a[1]))
        place(sm, (a[0], 0.0, a[1]), U)
        sm.seed = seed_of(v["id"], 0, sid)
        out[f"bay.{i}"] = sm
    return out


def bay_trim(house: Sample, form: dict, data: dict) -> dict:
    """The bay's base, sill course and cornice round its plan, the raised panel under each
    light, and the deck over the cornice falling from the wall to the crown."""
    bv = form["canted_bay"]["value"]
    plan = [tuple(q) for q in bv["plan"]]
    yb, ys = bv["base_m"], bv["wall_top_m"]
    base = tuple((o, y if y is not None else yb - (0.09, 0.09, 0.04, 0.0)[k - 4])
                 for k, (o, y) in enumerate(BAY_BASE))
    bay_ring(house, plan, base, (None, "water_table", "water_table", "apron", "sill", "sill", "sill"))
    bay_ring(house, plan, BAY_CORNICE, ("soffit", "fascia", "drip_cap", "drip_cap", "drip_cap", "drip_cap"), ys)
    ct = data["trim"]["corner_board"]["thickness_m"]
    for i, (a, b) in enumerate(zip(plan, plan[1:])):
        F = Frame(f"bay_{i}", (a[0], 0.0, a[1]), (b[0] - a[0], 0.0, b[1] - a[1]), (-(b[1] - a[1]), 0.0, b[0] - a[0]))
        W = math.hypot(b[0] - a[0], b[1] - a[1])
        inset = bv["post_m"] - ct + 0.05
        house.box(F, "casing", inset, W - inset, 0.17, yb - 0.12, 0.035, 0.035 + ct * 0.6, skip=("back",),
                  tone=house.tone("bay_panel", i))
    top = ys + BAY_CORNICE[-1][1]
    edge, _ = bay_offset(plan, BAY_CORNICE[-1][0])
    deck = [(s, top + bv["roof_m"] * (1.0 - z / max(q[1] for q in edge)), z) for s, z in edge]
    house.face("roof_covering", deck, (0.0, 1.0, 0.0))
    return {"plan": [list(q) for q in plan], "base_m": yb, "wall_top_m": ys, "cornice_top_m": round(top, 4),
            "deck_at_wall_m": round(top + bv["roof_m"], 4)}


#: T-2395: a timber body's parts, in the order they are merged and measured
BODY_KEYS = tuple(f"body.{k}{n}" for k in ("south", "north", "wing_north", "wing_rear") for n in ("", ".2")) \
    + ("body.rear", "body.rear_north")


def body_part_keys(parts: dict) -> tuple:
    """A front record's body parts in merge order: the timber body's faces, then any annex's
    walls (T-2397), the corner tower's faces (T-2396) and the canted bay's (T-2424), each held
    to the kit's rules by the gate."""
    return tuple(k for k in BODY_KEYS + TOWER_KEYS + BAY_KEYS if k in parts) \
        + tuple(k for k in parts if k.startswith("annex."))


def structure_parts(st: dict, phase: dict, data: dict | None = None) -> dict:
    """The front's parts as built samples, each in place along the front, before merging:
    what the gate measures (tools/check_timber_kit.py holds each to the kit's rules)."""
    data = data or load()
    form = phase["form"]
    sid = st["id"]
    gv = form["gable"]["value"]
    wv = form["wing_wall"]["value"]
    pv = form["porch"]["value"]
    Wg = gv["width_m"]
    join = form["layout"]["value"]["join_gap_m"]
    out = {"gable": Sample(gv, data, (0.0, 0.0, 0.0)).build(),
           "wing_wall": Sample(wv, data, (Wg + join, 0.0, 0.0)).build()}
    half = dict(pv, width_m=pv["half_width_m"])
    lift = basement_of(form)
    if lift:     # T-2523: the floor stands the basement higher; the half is set down by it, to
        half["basement_m"] = lift      # come back up with the house (its lattice and stoop to grade)
    probe = Sample(half, data).build()
    reach = max(p[0] for pr in probe.prims.values() for p in pr.pos)    # the half's roof edge
    # the porch stands with its roof's south edge at the gable's, unless the record places its
    # middle (T-2396: 1638's photograph puts its porch, and the tower on it, there)
    c = pv["centre_m"] if "centre_m" in pv else Wg + join + reach
    out["porch_right"] = Sample(half, data, (c, -lift, 0.0)).build()
    out["porch_left"] = Sample(half, data, (c, -lift, 0.0)).build()      # mirrored when merged
    out["_porch_mirror_s"] = c
    for k in ("gable", "wing_wall", "porch_right", "porch_left"):
        out[k].seed = seed_of(out[k].v["id"], 0, sid)
    if form["body"]["value"].get("timber_walls"):
        out.update(timber_body_parts(st, form, data, out))
    if form.get("tower"):
        out.update(tower_parts(st, form, data, out))
    if form.get("canted_bay") and "lights" in form["canted_bay"]["value"]:     # T-2424
        out.update(bay_parts(st, form, data))
    return out


# -- T-2395: the body behind a front closed in K16 timber ----------------------------------------
#
# The front's frame: s along the front from its left (south) end, z out toward the street, y up.
# The gable's range runs back `gable_depth_m` behind the gable; the wing's range `wing_depth_m`
# behind the wing wall. Each flank is a kit `clapboard_wall` set down on its side; the gable's
# range ends at the back in a second kit gable, the front's own pitch, belt and foundation. The
# flanks' eave is set where the main roof, carried back on the front gable's own rake, comes
# down to their fascia, so the roof meets the gable's verge with no step.

def body_flank_top(gable: Sample, data: dict, under: float) -> float:
    """The wall top of a flank under a roof that runs back on the front gable's rake line."""
    g = gable.meta["gable"]
    ev = data["trim"]["eave"]
    t = math.tan(math.radians(data["gothic"]["pitch_deg"]))
    return g["y_g"] + g["h_roof"] - under - ev["projection_m"] * t - ev["fascia_m"]


def timber_body_parts(st: dict, form: dict, data: dict, front: dict) -> dict:
    sid = st["id"]
    body = form["body"]["value"]
    tw = body["timber_walls"]
    gv, wv = form["gable"]["value"], form["wing_wall"]["value"]
    Wg, Ww, join = gv["width_m"], wv["width_m"], form["layout"]["value"]["join_gap_m"]
    Lg, Dw = body["gable_depth_m"], body["wing_depth_m"]
    Wr = body.get("rear_width_m", Wg)      # T-2397: the range behind the wing, widened past the gable's
    s1 = Wg + join + Ww
    y_flank = round(body_flank_top(front["gable"], data, body["roof_under_m"]), 6)

    out = {}

    def wall(key, O, U, L, top, boards):
        """One face, as one kit wall or, past `split_m`, two meeting end to end (a long flank
        would outrun one wall's triangle budget): `body.<key>` and `body.<key>.2`."""
        w = tw.get(key, {})       # T-2397: the widened range's short back wall may name nothing
        cut = w.get("split_m")
        runs = [(0.0, cut, (boards[0], False)), (cut, L, (False, boards[1]))] if cut else [(0.0, L, boards)]
        for i, (a, b, bd) in enumerate(runs):
            v = {"id": f"k16.wall.{sid}.body_{key}" + (f"_{i + 1}" if i else ""), "kind": "clapboard_wall",
                 "use": "wall", "width_m": round(b - a, 6), "return_m": 0.0, "boards": list(bd),
                 "foundation_m": gv["foundation_m"], "wall_top_m": top,
                 "windows": [dict(x, centre_m=round(x["centre_m"] - a, 6)) for x in w.get("windows", [])
                             if a <= x["centre_m"] < b],
                 "doors": [dict(x, centre_m=round(x["centre_m"] - a, 6)) for x in w.get("doors", [])
                           if a <= x["centre_m"] < b]}
            sm = Sample(v, data).build()
            place(sm, _add(O, _mul(U, a)), U)
            sm.seed = seed_of(v["id"], 0, sid)
            out[f"body.{key}" + (f".{i + 1}" if i else "")] = sm

    D = wv["return_m"]
    # the gable range's south flank, from the back corner to the front's
    wall("south", (0.0, 0.0, -Lg), (0.0, 0.0, 1.0), Lg, y_flank, (True, True))
    # its north flank behind the wing, from the wing's back wall to the back corner
    wall("north", (Wr, 0.0, -Dw), (0.0, 0.0, -1.0), Lg - Dw, y_flank, (False, True))
    # the wing's north side, on from the wing wall's return, and its back wall
    wall("wing_north", (s1, 0.0, -D), (0.0, 0.0, -1.0), Dw - D, wv["wall_top_m"], (False, True))
    wall("wing_rear", (s1, 0.0, -Dw), (-1.0, 0.0, 0.0), s1 - Wr, wv["wall_top_m"], (True, False))
    if Wr > Wg:     # T-2397: the widened range's back, from its north corner to the rear gable
        wall("rear_north", (Wr, 0.0, -Lg), (-1.0, 0.0, 0.0), Wr - Wg, y_flank, (False, False))
    # the rear gable, measured in its own frame as the front's is and turned into place when
    # the house is merged (`_rear_at`)
    # T-2423: the front's own hood, oval and clapboard field are the street front's, not the back's
    rv = dict({k: x for k, x in gv.items() if k not in ("field", "hood", "oculus")}, id=f"k16.gable.{sid}.body_rear", windows=list(tw["rear"].get("windows", [])),
              bands=tw["rear"].get("bands", gv["bands"]))
    out["body.rear"] = Sample(rv, data).build()
    out["body.rear"].seed = seed_of(rv["id"], 0, sid)
    out["_rear_at"] = ((Wg, 0.0, -Lg), (-1.0, 0.0, 0.0))
    out["_flank_top_m"] = y_flank
    if body.get("annexes"):
        out.update(annex_parts(st, body, gv["foundation_m"], y_flank, data))
    return out


# -- T-2397: the pieces the plan draws against the body ------------------------------------------
#
# Each annex is a block in the lot plan's frame (u east, v north, about the front's south end,
# as the record's footprint is), standing `against` one side of the body, walled by the kit as a
# whole frame house's later block is (`frame_house_parts`), and turned with nothing: the house
# is merged in the front's frame and turned to its street, then the annexes are merged into it
# where they already stand. `open` names a side that joins another annex: no wall, no eave.

def _annex_blocks(body: dict, y_flank: float) -> list[dict]:
    return [dict(b, wall_top_m=y_flank if b["wall_top_m"] == "flank" else b["wall_top_m"])
            for b in body["annexes"]]


def annex_parts(st: dict, body: dict, foundation_m: float, y_flank: float, data: dict) -> dict:
    fh = {"foundation_m": foundation_m, "return_m": body["annex_return_m"],
          "blocks": _annex_blocks(body, y_flank)}
    parts = frame_house_parts(st, {"form": {"frame_house": {"value": fh}}}, data)
    out = {}
    for k, sm in parts.items():
        sm.seed = seed_of(sm.v["id"], 0, st["id"])
        out[f"annex.{k}"] = sm
    return out


def annex_roofs(house: Sample, parts: dict, form: dict, data: dict) -> dict:
    """Each annex's roof, in the plan frame: a flat deck just over its eave, overhanging only
    where it has a wall, a lean-to from its outer eave up into the main roof at the wing's
    pitch, its two ends closed in painted board as the wing's are, or (T-2522) a gable whose
    ridge runs north into the main roof (`_annex_gable`)."""
    body = form["body"]["value"]
    ev = data["trim"]["eave"]
    P_, fh = ev["projection_m"], ev["fascia_m"]
    t = math.tan(math.radians(data["gothic"]["pitch_deg"]))
    tl = math.tan(math.radians(body["wing_roof_pitch_deg"]))
    ye = parts["_flank_top_m"] + fh                 # the main roof's eave line, P_ out of a flank
    F = house.F
    out = {}
    for b in _annex_blocks(body, parts["_flank_top_m"]):
        u0, v0, u1, v1 = b["rect_uv"]
        walled = {w["side"] for w in b["walls"]}
        x0 = u0 - P_ if "west" in walled else u0
        x1 = u1 + P_ if "east" in walled else u1
        z0 = -v1 - P_ if "north" in walled else -v1
        z1 = -v0 + P_ if "south" in walled else -v0
        yb = b["wall_top_m"] + fh
        if b["roof"]["kind"] == "lean_to":
            if b["against"] != "north":
                raise ValueError(f"{b['id']}: a lean-to rises against the body's south flank only")
            # the main roof's south slope: y = ye + (v + P_) t; the lean-to's: yb + (v - v0 + P_) tl
            vi = (yb - ye + (P_ - v0) * tl - P_ * t) / (t - tl)
            yi = yb + (vi - v0 + P_) * tl
            y0 = ye + P_ * t                            # the main roof over the flank's face
            house.poly(F, "roof_covering", [(u0, yb, z1), (u1, yb, z1), (u1, yi, -vi), (u0, yi, -vi)], (0, 1, 1))
            for u, hu in ((u0, -1), (u1, 1)):
                house.poly(F, "fascia", [(u, yi, -vi), (u, y0, 0.0), (u, yb, z1)], (hu, 0, 0))
                house.poly(F, "fascia", [(u, y0, 0.0), (u, yb, 0.0), (u, yb, z1)], (hu, 0, 0))
            out[b["id"]] = {"eave_m": round(yb, 4), "meets_main_m": round(yi, 4), "meets_v_m": round(vi, 4)}
        elif b["roof"]["kind"] == "gable":
            out[b["id"]] = _annex_gable(house, b, x0, x1, z1, yb, ye, t, P_, fh)
        else:
            yd = yb + b["roof"].get("deck_m", 0.03)
            house.poly(F, "roof_covering", [(x0, yd, z1), (x1, yd, z1), (x1, yd, z0), (x0, yd, z0)], (0, 1, 0))
            for side, q, hnt in (("south", [(x0, yb, z1), (x1, yb, z1), (x1, yd, z1), (x0, yd, z1)], (0, 0, 1)),
                                 ("north", [(x1, yb, z0), (x0, yb, z0), (x0, yd, z0), (x1, yd, z0)], (0, 0, -1)),
                                 ("west", [(x0, yb, z0), (x0, yb, z1), (x0, yd, z1), (x0, yd, z0)], (-1, 0, 0)),
                                 ("east", [(x1, yb, z1), (x1, yb, z0), (x1, yd, z0), (x1, yd, z1)], (1, 0, 0))):
                if side in walled:
                    house.poly(F, "roof_covering", q, hnt)
            out[b["id"]] = {"deck_m": round(yd, 4)}
    return out


def _annex_gable(house: Sample, b: dict, x0, x1, z1, yb, ye, t, P_, fh) -> dict:
    """T-2522: a gable over an annex on the south flank, its ridge running north (along v) from
    a gable over its south wall into the main roof's south slope. Each slope runs under the main
    eave to the flank and, above that eave, stops on its valley with the main roof
    (y = ye + (v + P_) t); the south end is closed under its verge as `_gable` closes one."""
    if b["against"] != "north" or b["roof"].get("ridge") != "v":
        raise ValueError(f"{b['id']}: a gabled annex stands against the south flank with its ridge along v")
    tw = math.tan(math.radians(b["roof"]["pitch_deg"]))
    F = house.F
    xm, yr = (x0 + x1) / 2, yb + (x1 - x0) / 2 * tw
    if not yb < ye < yr:
        raise ValueError(f"{b['id']}: a gabled annex's eave stands under the main eave and its ridge over it")
    vi = (yr - ye) / t - P_                     # where the ridge runs into the main roof
    zs, zw, ze, zf = z1, -b["rect_uv"][1], P_, 0.0     # verge, south wall, main eave's edge, flank
    run = (ye - yb) / tw                        # from each eave in to where the slope reaches the main eave
    for xe, sx in ((x1, 1), (x0, -1)):
        xv = xe - sx * run
        n = (sx * tw, 1, 0)
        house.poly(F, "roof_covering", [(xe, yb, zs), (xe, yb, ze), (xm, yr, ze), (xm, yr, zs)], n)
        house.poly(F, "roof_covering", [(xv, ye, ze), (xm, yr, -vi), (xm, yr, ze)], n)
        house.poly(F, "roof_covering", [(xe, yb, ze), (xe, yb, zf), (xv, ye, zf), (xv, ye, ze)], n)
        house.poly(F, "fascia", [(xe, yb - fh, zs), (xm, yr - fh, zs), (xm, yr, zs), (xe, yb, zs)], (0, 0, 1))
        house.poly(F, "soffit", [(xe, yb - fh, zw), (xe, yb - fh, zs), (xm, yr - fh, zs), (xm, yr - fh, zw)],
                   (-sx * tw, -1, 0))
    return {"eave_m": round(yb, 4), "ridge_m": round(yr, 4), "ridge_meets_main_v_m": round(vi, 4),
            "verge_v_m": round(-zs, 4)}


def timber_body_roofs(house: Sample, parts: dict, form: dict, data: dict) -> dict:
    """The main roof carried back on the front gable's rake to the rear gable, over both
    flanks' eaves, and a lean-to over the wing from its north eave up to the main roof."""
    body = form["body"]["value"]
    gv, wv = form["gable"]["value"], form["wing_wall"]["value"]
    Wg, Ww, join = gv["width_m"], wv["width_m"], form["layout"]["value"]["join_gap_m"]
    Lg, Dw = body["gable_depth_m"], body["wing_depth_m"]
    s1 = Wg + join + Ww
    ev = data["trim"]["eave"]
    P_, fh = ev["projection_m"], ev["fascia_m"]
    g = parts["gable"].meta["gable"]
    t = math.tan(math.radians(data["gothic"]["pitch_deg"]))
    y0 = g["y_g"] + g["h_roof"] - body["roof_under_m"]       # the roof at the range's two walls
    ye = parts["_flank_top_m"] + fh                           # ... and at the flanks' fascia
    yr = y0 + (Wg / 2) * t
    xm = Wg / 2
    F = house.F
    house.poly(F, "roof_covering", [(-P_, ye, 0.0), (xm, yr, 0.0), (xm, yr, -Lg), (-P_, ye, -Lg)], (-1, 1, 0))
    house.poly(F, "roof_covering", [(Wg + P_, ye, -Lg), (xm, yr, -Lg), (xm, yr, 0.0), (Wg + P_, ye, 0.0)], (1, 1, 0))
    Wr = body.get("rear_width_m", Wg)
    for z, hz in ((0.0, 1), (-Lg, -1)):        # the eave's ends: the wedge under the roof's overhang
        for x0, x1 in ((-P_, 0.0), (Wg + P_, Wg)):
            if z == -Lg and x1 == Wg and Wr > Wg:   # T-2397: under the widened range's lean-to
                continue
            house.poly(F, "fascia", [(x0, ye, z), (x1, ye, z), (x1, y0, z)], (0, 0, hz))
    # the wing's lean-to, from its eave (the wing wall's) to where it meets the main roof
    tl = math.tan(math.radians(body["wing_roof_pitch_deg"]))
    ywe = wv["wall_top_m"] + fh
    xo = s1 + P_
    xi = (y0 + Wg * t - ywe - xo * tl) / (t - tl)
    yi = ywe + (xo - xi) * tl
    house.poly(F, "roof_covering", [(xo, ywe, 0.0), (xi, yi, 0.0), (xi, yi, -Dw), (xo, ywe, -Dw)], (1, 1, 0))
    for z, hz in ((0.0, 1), (-Dw, -1)):
        house.poly(F, "fascia", [(xi, yi, z), (Wg, y0, z), (xo, ywe, z)], (0, 0, hz))
        house.poly(F, "fascia", [(Wg, y0, z), (Wg, ywe, z), (xo, ywe, z)], (0, 0, hz))
    out = {"flank_top_m": round(parts["_flank_top_m"], 4), "eave_m": round(ye, 4), "ridge_m": round(yr, 4),
           "lean_to_top_m": round(yi, 4), "lean_to_meets_x_m": round(xi, 4)}
    if Wr > Wg:
        # T-2397: the range behind the wing widened to Wr, under its own lean-to at the wing's
        # pitch from its north eave (the flanks', so the eave line runs on) up into the main
        # roof; its back end closed in board as the wing's are, its front end inside the wing
        xo = Wr + P_
        xr = (y0 + Wg * t - ye - xo * tl) / (t - tl)
        yri = ye + (xo - xr) * tl
        house.poly(F, "roof_covering", [(xo, ye, -Dw), (xr, yri, -Dw), (xr, yri, -Lg), (xo, ye, -Lg)], (1, 1, 0))
        house.poly(F, "fascia", [(xr, yri, -Lg), (Wg, y0, -Lg), (xo, ye, -Lg)], (0, 0, -1))
        house.poly(F, "fascia", [(Wg, y0, -Lg), (Wg, ye, -Lg), (xo, ye, -Lg)], (0, 0, -1))
        out.update({"rear_lean_to_top_m": round(yri, 4), "rear_lean_to_meets_x_m": round(xr, 4)})
    return out


# -- T-2396: a corner tower standing on the porch -------------------------------------------------
#
# 1638's photograph shows, at the north end of the front, a regular octagon standing on the porch's
# roof: an upper stage lit by a pointed sash in each street face, a cornice, and an octagonal spire
# to a finial. Each of the eight faces is a kit `clapboard_wall` with no return and a corner board
# at each angle, its water table the band the stage stands on; the wall's own straight eave and
# brackets are left off, because eight straight eaves cannot meet at an octagon's angles, and the
# cornice and the spire are built round the octagon instead so every angle mitres. The tower is
# centred on the porch and its front face stands on the porch plate's front, so it is the porch's
# second storey and not a separate thing beside it; its back faces run into the house and show only
# where they rise above the north range's roof.

#: the faces, by their outward normal turning from the street front (+z) toward the north (+s)
TOWER_FACES = ("e", "ne", "n", "nw", "w", "sw", "s", "se")
TOWER_KEYS = tuple(f"tower.{f}" for f in TOWER_FACES)
#: what a tower face does not keep of its kit wall: the straight eave and its brackets (the
#: octagon's own cornice replaces them), and the foundation a stage on a porch roof has none of
TOWER_DROP = ("foundation", "soffit", "fascia", "roof", "bracket")


def tower_ring(c, zc, r, y):
    """The octagon of apothem r about (c, zc) at height y, its vertices between the faces in
    TOWER_FACES order (the first between the front and the north-east face)."""
    rho = r / math.cos(math.pi / 8)
    return [(c + rho * math.sin(math.pi / 8 + j * math.pi / 4), y, zc + rho * math.cos(math.pi / 8 + j * math.pi / 4))
            for j in range(8)]


def tower_parts(st: dict, form: dict, data: dict, front: dict) -> dict:
    sid = st["id"]
    tv = form["tower"]["value"]
    porch = front["porch_right"]
    c = front["_porch_mirror_s"]
    z_front = max(p[2] for p in porch.prims["plate"].pos)     # the porch plate's front
    y0 = max(p[1] for p in porch.prims["roof"].pos)            # the porch roof the stage stands on
    A = tv["across_flats_m"]
    R, w = A / 2, A * math.tan(math.pi / 8)
    zc = z_front - R
    lit = {f: wv for wv in tv.get("windows", []) for f in wv["faces"]}
    out = {}
    for i, f in enumerate(TOWER_FACES):
        th = i * math.pi / 4
        n, U = (math.sin(th), 0.0, math.cos(th)), (math.cos(th), 0.0, -math.sin(th))
        O = _add((c + R * n[0], y0, zc + R * n[2]), _mul(U, -w / 2))
        win = lit.get(f)
        v = {"id": f"k16.wall.{sid}.tower_{f}", "kind": "clapboard_wall", "use": "wall", "width_m": round(w, 6),
             "return_m": 0.0, "boards": [True, True], "foundation_m": 0.0,
             "wall_top_m": round(tv["wall_top_m"] - y0, 6),
             "windows": [{"k06_variant": win["k06_variant"], "clear_width_m": win["clear_width_m"],
                          "clear_height_m": win["clear_height_m"], "sill_m": round(win["sill_m"] - y0, 6),
                          "centre_m": round(w / 2, 6),
                          **({"surround": win["surround"]} if win and win.get("surround") else {})}] if win else []}
        sg = tv.get("stage")
        if sg:     # T-2521: the stage smooth under a shallower frieze, a trefoil incised over each light
            v.update(cladding="smooth", frieze_m=sg["frieze_m"])
            if win and sg.get("incised"):
                o = sg["incised"]
                v["incised"] = [{"centre_m": round(w / 2, 6), "centre_y_m": round(o["centre_y_m"] - y0, 6),
                                 **{k: o[k] for k in ("lobe_r_m", "lobe_off_m", "groove_m", "depth_m")}}]
        sm = Sample(v, data).build()
        for role in TOWER_DROP:
            sm.prims.pop(role, None)
        place(sm, O, U)
        sm.seed = seed_of(v["id"], 0, sid)
        out[f"tower.{f}"] = sm
    out["_tower"] = {"c": c, "zc": zc, "R": R, "y0": y0}
    return out


def tower_roof(house: Sample, parts: dict, form: dict, data: dict) -> dict:
    """The tower's cornice and spire round its octagon: a soffit and fascia out at the eave's
    projection, the spire's covering kicked out over them and then up at its own pitch to the
    apex, and a chamfered finial through the apex."""
    tv = form["tower"]["value"]
    t = parts["_tower"]
    c, zc, R = t["c"], t["zc"], t["R"]
    ev = data["trim"]["eave"]
    fr = data["trim"]["frieze"]
    P_, fh = tv["eave_projection_m"], ev["fascia_m"]
    y_s, y_ap = tv["wall_top_m"], tv["spire_apex_m"]
    F = house.F
    face = R + fr["thickness_m"]
    inner, outer = tower_ring(c, zc, face, y_s), tower_ring(c, zc, R + P_, y_s)
    top = tower_ring(c, zc, R + P_, y_s + fh)
    kick = tower_ring(c, zc, face, y_s + fh + tv["kick_m"])
    apex = (c, y_ap, zc)
    for j in range(8):
        k = (j + 1) % 8
        mid = ((outer[j][0] + outer[k][0]) / 2 - c, 0.0, (outer[j][2] + outer[k][2]) / 2 - zc)
        house.poly(F, "soffit", [inner[j], outer[j], outer[k], inner[k]], (0, -1, 0))
        house.poly(F, "fascia", [outer[j], top[j], top[k], outer[k]], mid)
        house.poly(F, "roof_covering", [top[j], kick[j], kick[k], top[k]], _add(mid, (0.0, 1.0, 0.0)))
        house.poly(F, "roof_covering", [kick[j], apex, kick[k]], _add(mid, (0.0, 0.6, 0.0)))
    # the finial: a chamfered octagonal post from inside the spire to above its apex, to a point
    fi = data["gothic"]["finial"]
    a = fi["section_m"] / 2
    ring = [(c + ds, 0.0, zc + dz) for ds, dz in octagon(a, fi["chamfer_m"])]
    y_lo = y_ap - fi["drop_m"]
    y_hi = y_ap + tv["finial_m"]
    for j in range(8):
        p, q = ring[j], ring[(j + 1) % 8]
        mid = ((p[0] + q[0]) / 2 - c, 0.0, (p[2] + q[2]) / 2 - zc)
        house.poly(F, "finial", [(p[0], y_lo, p[2]), (q[0], y_lo, q[2]), (q[0], y_hi, q[2]), (p[0], y_hi, p[2])], mid)
        house.poly(F, "finial", [(p[0], y_hi, p[2]), (q[0], y_hi, q[2]), (c, y_hi + fi["point_m"], zc)],
                   _add(mid, (0.0, 0.5, 0.0)))
    return {"stage_base_m": round(t["y0"], 4), "wall_top_m": y_s, "eave_m": round(y_s + fh, 4),
            "spire_apex_m": y_ap, "finial_top_m": round(y_hi + fi["point_m"], 4),
            "across_flats_m": tv["across_flats_m"], "front_z_m": round(zc + R, 4)}


# -- T-2523: a house raised on its basement ------------------------------------------------------
#
# Every height a record gives is over the basement's top: the parts are built as before, the
# porch's floor the basement higher and its half set down by it, and then the whole house is
# raised. A foundation's foot stays on grade, so each foundation runs on down as the basement's
# wall, its brick coursed on (its texture's v carried down with it).

#: the roles whose foot is on grade before the lift and stays there
BASEMENT_STRETCH = ("foundation",)
#: a basement wall built below the old grade (under a part with no foundation of its own),
#: raised with the house and then laid in with the foundations
BASEMENT_WALL = "basement_wall"


def basement_of(form: dict) -> float:
    return form["basement"]["value"]["height_m"] if form.get("basement") else 0.0


def raise_on_basement(house: Sample, lift: float) -> dict:
    """Raise the merged house `lift` metres, keeping each foundation's foot on grade."""
    kept = 0
    for role, pr in house.prims.items():
        stretch = role in BASEMENT_STRETCH
        for i, p in enumerate(pr.pos):
            if stretch and abs(p[1]) < 1e-9:
                n = pr.nrm[i]
                au = _cross(Y, n)
                au = _unit(au) if _dot(au, au) > 1e-9 else (1.0, 0.0, 0.0)
                u, w = pr.uv[i]
                pr.uv[i] = (u, w + lift * _cross(n, au)[1])
                kept += 1
            else:
                pr.pos[i] = (p[0], p[1] + lift, p[2])
    if BASEMENT_WALL in house.prims:
        absorb(house.prims.setdefault("foundation", Prim("foundation")), house.prims.pop(BASEMENT_WALL))
    return {"height_m": lift, "kept_on_grade": kept}


def structure_house(st: dict, phase: dict, data: dict | None = None) -> Sample:
    """The whole front, merged into one sample and turned to face its street."""
    data = data or load()
    form = phase["form"]
    parts = structure_parts(st, phase, data)
    T = data["wall"]["thickness_m"]
    body = form["body"]["value"]
    gv, wv = form["gable"]["value"], form["wing_wall"]["value"]
    Wg, Ww, join = gv["width_m"], wv["width_m"], form["layout"]["value"]["join_gap_m"]
    house = Sample({"id": st["id"], "kind": "structure", "use": "structure"}, data)
    lift = basement_of(form)
    timber = bool(body.get("timber_walls"))
    if timber:     # T-2395: the body closed in kit timber under its own roofs
        house.meta["body"] = timber_body_roofs(house, parts, form, data)
    if form.get("tower"):     # T-2396: the corner tower's cornice, spire and finial
        house.meta["tower"] = tower_roof(house, parts, form, data)
    else:
        # the stand-in body: the gable's range behind its front, the wing's behind its wall
        g = parts["gable"].meta["gable"]
        lift = g["h_roof"] - body["roof_under_m"]
        gabled_body(house, 0.0, Wg, -body["gable_depth_m"], -T, g["y_g"], g["y_ap"], "z", lift=lift)
        e = parts["wing_wall"].meta["eave"]
        s1 = Wg + join + Ww
        zm = body["wing_depth_m"] / 2
        yr = e["y_top"] + zm * math.tan(math.radians(body["wing_roof_pitch_deg"]))
        eave_lift = e["y_top"] - wv["wall_top_m"]
        # its roof runs out to the wall's face (z = 0), where the boxed eave's top takes over
        gabled_body(house, Wg + join, s1, -body["wing_depth_m"], 0.0, wv["wall_top_m"], yr - eave_lift, "s",
                    lift=eave_lift, skip=("s0",), s1_wall_to=-wv["return_m"])
    bay = form.get("canted_bay")
    if bay and "lights" in bay["value"]:     # T-2424: its faces are parts, merged below
        house.meta["bay"] = bay_trim(house, form, data)
        if lift:     # T-2523: the basement's wall carried round under the bay's plinth
            plan = [tuple(q) for q in bay["value"]["plan"]]
            bay_ring(house, plan, ((BAY_BASE[1][0], -lift), BAY_BASE[1]), (BASEMENT_WALL,))
    elif bay:
        b = bay["value"]
        canted_bay_body(house, [tuple(q) for q in b["plan"]], b["height_m"], b.get("roof_m", 0.12))
    # the porch's two open ends: a painted skirt board under the floor from the wall to the
    # lattice, so the crawl space is closed at the sides as it is behind the lattice
    po = data["porch"]
    c = parts["_porch_mirror_s"]
    Wf = parts["porch_right"].meta["floor_width_m"]
    Dp = form["porch"]["value"].get("depth_m", po["floor"]["depth_m"])
    y_rim0 = po["floor"]["height_m"] - po["floor"]["board_m"] - po["floor"]["rim_m"]
    zl = Dp - po["lattice"]["setback_m"]
    sk = po["lattice"]["frame_thickness_m"]
    for a, b in ((c + Wf - sk, c + Wf), (c - Wf, c - Wf + sk)):
        house.box(house.F, "skirt", a, b, -lift, y_rim0, 0.0, zl, skip=("back", "bottom"), tone=house.tone("skirt", a))
    # merge: the porch's left half mirrored, the board roles dropped
    mirror_s(parts["porch_left"], c)
    keys = ("gable", "wing_wall", "porch_right", "porch_left") + body_part_keys(parts)
    annex = tuple(k for k in keys if k.startswith("annex."))
    if timber:
        place(parts["body.rear"], *parts["_rear_at"])
    for k in keys:
        if k in annex:
            continue
        sm = parts[k]
        porch = k.startswith("porch")
        for role, pr in sm.prims.items():
            if role in ("backdrop", "interior") or (porch and role == "cut"):
                continue
            # a timber body's cut ends are painted board ends; the front's die into the stand-in
            dst = ("fascia" if timber else "stand_in") if role == "cut" else role
            absorb(house.prims.setdefault(dst, Prim(dst)), pr)
    # turn it to face its street; the origin (the front's left end, at grade) stays put
    k = {"east": 1, "south": 0}[form["layout"]["value"]["faces"]]
    for pr in house.prims.values():
        pr.pos = [_rot_y(q, k) for q in pr.pos]
        pr.nrm = [_rot_y(q, k) for q in pr.nrm]
    if annex:   # T-2397: built where they stand in the plan, merged after the turn
        if k != 1:
            raise ValueError(f"{st['id']}: annexes are planned about a front facing east")
        house.meta["annexes"] = annex_roofs(house, parts, form, data)
        for kk in annex:
            for role, pr in parts[kk].prims.items():
                if role not in ("backdrop", "interior", "cut"):
                    absorb(house.prims.setdefault(role, Prim(role)), pr)
    house.meta.update({"parts": {kk: triangles(parts[kk]) for kk in keys},
                       "focus": [0.0, 3.0, 0.0], "span_m": 9.0})
    if lift:     # T-2523: the house up on its basement, the fence left on the walk
        house.meta["basement"] = raise_on_basement(house, lift)
    if form.get("boundary"):     # T-2456: the street fence, built facing east and turned with the rest
        bd = Sample({"id": f"{st['id']}.boundary", "kind": "boundary", "use": "boundary"}, data)
        house.meta["boundary"] = boundary(bd, form["boundary"]["value"])
        for role, pr in bd.prims.items():
            pr.pos = [_rot_y(q, k) for q in pr.pos]
            pr.nrm = [_rot_y(q, k) for q in pr.nrm]
            absorb(house.prims.setdefault(role, Prim(role)), pr)
        house.meta["parts"]["boundary"] = triangles(bd)
    if form.get("yard"):     # T-3222: a K14 front walk from the stair's foot out through the gateway
        yd = Sample({"id": f"{st['id']}.yard", "kind": "yard", "use": "yard"}, data)
        house.meta["yard"] = yard_walk(yd, form["yard"]["value"], parts, form, st["id"])
        for role, pr in yd.prims.items():
            absorb(house.prims.setdefault(role, Prim(role)), pr)
        house.meta["parts"]["yard"] = triangles(yd)
    return house


# -- T-2456: the street fence and its gate piers ------------------------------------------------
#
# Built in the front's own frame (s along the front from its south end, z out toward the street,
# y up from grade), so the record's numbers are the ones read off the print through the camera.
# The base and its bars run from a lot line to the first pier and on from the second to the other
# lot line; the gateway between the piers is open, its walk at grade.

def heart(c, y_lobe, lobe_r, lobe_off, y_apex, n=10):
    """An inverted heart in (a, y), anticlockwise: two lobes of radius `lobe_r` whose middles
    stand `lobe_off` either side of the axis at `y_lobe`, meeting in a notch on the axis, and
    their outer sides drawn up as tangents to a point on the axis at `y_apex`."""
    cx, cy = c + lobe_off, y_lobe
    dx, dy = c - cx, y_apex - cy
    d = math.hypot(dx, dy)
    if d <= lobe_r:
        raise ValueError("the heart's point stands inside its lobe")
    t_from = math.atan2(dy, dx) - math.acos(lobe_r / d)          # the right side's tangent point
    y_notch = cy - math.sqrt(max(0.0, lobe_r * lobe_r - lobe_off * lobe_off))
    t_to = math.atan2(y_notch - cy, c - cx)         # clockwise round the lobe's foot to the notch
    if t_to > t_from:
        t_to -= 2 * math.pi
    right = [(cx + lobe_r * math.cos(t_from + (t_to - t_from) * i / n),
              cy + lobe_r * math.sin(t_from + (t_to - t_from) * i / n)) for i in range(n + 1)]
    left = [(2 * c - x, y) for x, y in reversed(right[:-1])]
    return list(reversed([(c, y_apex)] + right + left))


def pierced_board(sm: Sample, Fr: Frame, role, outer, d0, d1, hole, tone):
    """A board whose outline is the anticlockwise polygon `outer` in frame Fr's (a, y), its
    faces at d0 (in) and d1 (out), pierced through by the polygon `hole`; the piercing's cut
    edges are `cutout`. T-2521: an outline, not a rectangle, so a cap board's corners can flare."""
    pts = list(outer) + hole
    for tri in K09.triangulate(outer, [hole]):
        tq = [pts[i] for i in tri]
        sm.poly(Fr, role, [(x, y, d1) for x, y in tq], (0, 0, 1), tone)
        sm.poly(Fr, role, [(x, y, d0) for x, y in tq], (0, 0, -1), tone)
    for i in range(len(outer)):
        p, q = outer[i], outer[(i + 1) % len(outer)]
        h = (q[1] - p[1], p[0] - q[0])     # the edge's outward normal on an anticlockwise outline
        sm.poly(Fr, role, [(p[0], p[1], d0), (q[0], q[1], d0), (q[0], q[1], d1), (p[0], p[1], d1)], (h[0], h[1], 0),
                tone)
    mx = math.fsum(x for x, _ in hole) / len(hole)
    my = math.fsum(y for _, y in hole) / len(hole)
    for i in range(len(hole)):
        p, q = hole[i], hole[(i + 1) % len(hole)]
        m = ((p[0] + q[0]) / 2, (p[1] + q[1]) / 2)
        sm.poly(Fr, "cutout", [(p[0], p[1], d0), (q[0], q[1], d0), (q[0], q[1], d1), (p[0], p[1], d1)],
                (mx - m[0], my - m[1], 0), tone)


def cap_outline(cp: dict, y0: float, inner: float | None = None, n: int = 8) -> list:
    """T-2521: a gate cap board's outline, anticlockwise in (a, y), from y0 to the cap's top: as
    broad as the cap's `top_half_m` (or `half_m` with no flare), and where the cap's `flare`
    is given each lower corner swept out to `half_m` at `widest_m` along a quarter-sine from
    `from_m`, then turned back in a quarter-round to its foot at `foot_m`, a hood over the
    heart. `inner` keeps the board's straight edges in to that half-breadth (a side board,
    which stands between the street and yard boards) while its corners flare as theirs do."""
    fl, y1 = cp.get("flare"), cp["top_m"]
    if not fl:
        h = cp["half_m"] if inner is None else inner
        return [(-h, y0), (h, y0), (h, y1), (-h, y1)]
    h0, h1 = cp["top_half_m"], cp["half_m"]
    hs = h0 if inner is None else inner
    yf, yw, yt = fl["foot_m"], fl["widest_m"], fl["from_m"]
    ear = [(h0 + (h1 - h0) * math.sin(math.pi / 2 * k / n), yf + (yw - yf) * (1 - math.cos(math.pi / 2 * k / n)))
           for k in range(n + 1)]                                        # the foot rounded out to the widest
    ear += [(h0 + (h1 - h0) * math.cos(math.pi / 2 * k / n), yw + (yt - yw) * k / n) for k in range(1, n + 1)]
    side = [(hs, y0), (hs, yf)] + ([] if hs == h0 else [(h0, yf)]) + ear[1:-1] + \
        ([] if hs == h0 else [(h0, yt)]) + [(hs, yt), (hs, y1)]
    side = [q for m, q in enumerate(side) if m == 0 or q != side[m - 1]]
    return side + [(-a, y) for a, y in reversed(side)]


def _gate_pier(sm: Sample, pv: dict, pr: dict, zc: float) -> dict:
    """One gate pier centred at s `centre_m` on the base's line: a stone plinth, a painted
    square shaft, a hollow cap of four boards each pierced with a heart, dark inside, under a
    low pyramid, and an iron finial — a spike, or a spike through a ring in the street's plane."""
    c, ts = pr["centre_m"], sm.tone("pier", pr["centre_m"])
    hp, hs = pv["plinth_m"] / 2, pv["section_m"] / 2
    sm.box(sm.F, "pier_plinth", c - hp, c + hp, 0.0, pv["plinth_top_m"], zc - hp, zc + hp, skip=("bottom",),
           tone=sm.tone("plinth", c))
    y_cap = pv["shaft_top_m"]
    sm.box(sm.F, "pier", c - hs, c + hs, pv["plinth_top_m"], y_cap, zc - hs, zc + hs, skip=("bottom", "top"), tone=ts)
    cp = pv["cap"]
    ho, t, y_top = cp.get("top_half_m", cp["half_m"]), cp["board_m"], cp["top_m"]     # T-2521: flared under
    hi = ho - t
    hk = hi - 0.005      # the dark behind the hearts, clear of the boards' inner faces
    sm.box(sm.F, "backing", c - hk, c + hk, y_cap, y_top, zc - hk, zc + hk, skip=("bottom",))
    hv = cp["heart"]
    for n in ((0.0, 0.0, 1.0), (1.0, 0.0, 0.0), (0.0, 0.0, -1.0), (-1.0, 0.0, 0.0)):
        Fr = Frame("pier cap", (c, 0.0, zc), (n[2], 0.0, -n[0]), n)
        # the street and yard boards run past the side boards' ends
        outline = cap_outline(cp, y_cap, None if n[0] == 0.0 else hi)
        hole = heart(0.0, hv["lobe_y_m"], hv["lobe_r_m"], hv["lobe_off_m"], hv["apex_y_m"])
        pierced_board(sm, Fr, "pier_cap", outline, hi, ho, hole, ts)
    e = ho + cp["eave_m"]
    y_ap = y_top + cp["rise_m"]
    sq = [(c - e, zc - e), (c + e, zc - e), (c + e, zc + e), (c - e, zc + e)]
    sm.poly(sm.F, "pier_cap", [(x, y_top, z) for x, z in sq], (0, -1, 0), ts)
    for i in range(4):
        (x0, z0), (x1, z1) = sq[i], sq[(i + 1) % 4]
        out = ((x0 + x1) / 2 - c, 0.0, (z0 + z1) / 2 - zc)
        sm.face("pier_cap", [sm.F.P(x0, y_top, z0), sm.F.P(x1, y_top, z1), sm.F.P(c, y_ap, zc)],
                sm.F.V(out[0], 0.5, out[2]), ts)
    f = pv["finial"]
    r = f["rod_m"] / 2
    y_tip = f["top_m"]
    y_shank = y_tip - f["point_m"]
    sm.box(sm.F, "pier_finial", c - r, c + r, y_ap - 0.01, y_shank, zc - r, zc + r, skip=("bottom", "top"))
    for i in range(4):
        q = [(c - r, zc - r), (c + r, zc - r), (c + r, zc + r), (c - r, zc + r)]
        (x0, z0), (x1, z1) = q[i], q[(i + 1) % 4]
        sm.face("pier_finial", [sm.F.P(x0, y_shank, z0), sm.F.P(x1, y_shank, z1), sm.F.P(c, y_tip, zc)],
                sm.F.V((x0 + x1) / 2 - c, 0.3, (z0 + z1) / 2 - zc), 1.0)
    out = {"centre_m": c, "cap_top_m": round(y_ap, 6), "finial_top_m": y_tip}
    if pr.get("ring"):
        R, w = f["ring_r_m"], f["ring_bar_m"]
        yc = f["ring_y_m"]
        if yc - R - w / 2 < y_ap:
            raise ValueError(f"the ring at {yc} m sits into its cap, whose point is {y_ap:.3f} m")
        m = 16
        for i in range(m):
            t0, t1 = 2 * math.pi * i / m, 2 * math.pi * (i + 1) / m
            ring = [(c + (R + sg * w / 2) * math.cos(t), yc + (R + sg * w / 2) * math.sin(t))
                    for t, sg in ((t0, 1), (t1, 1), (t1, -1), (t0, -1))]
            for z, h in ((zc + w / 2, 1), (zc - w / 2, -1)):
                sm.poly(sm.F, "pier_finial", [(x, y, z) for x, y in ring], (0, 0, h))
            for (x0, y0), (x1, y1) in ((ring[0], ring[1]), (ring[2], ring[3])):
                mx, my = (x0 + x1) / 2 - c, (y0 + y1) / 2 - yc
                sg = 1 if math.hypot(mx, my) > R else -1
                sm.poly(sm.F, "pier_finial", [(x0, y0, zc - w / 2), (x1, y1, zc - w / 2), (x1, y1, zc + w / 2),
                                              (x0, y0, zc + w / 2)], (sg * mx, sg * my, 0))
        out["ring_y_m"] = yc
    return out


def boundary(sm: Sample, bv: dict) -> dict:
    """T-2456: the street fence on the lot's front line — a stone base with iron bars on a top
    rail, from each lot line to a gate pier, and the two piers either side of an open gateway."""
    zl = bv["street_line_m"]
    pv = bv["pier"]
    zc = zl - pv["plinth_m"] / 2                 # the plinths' street faces on the line
    s_lo, s_hi = bv["lot_s_m"]
    end = bv["end_clear_m"]
    piers = sorted(bv["piers"], key=lambda q: q["centre_m"])
    hp = pv["plinth_m"] / 2
    runs = [(s_lo + end, piers[0]["centre_m"] - hp), (piers[-1]["centre_m"] + hp, s_hi - end)]
    b, f = bv["base"], bv["bars"]
    hb, hr, w = b["width_m"] / 2, f["bar_m"] / 2, f["bar_m"]
    yb, yt = b["height_m"], f["height_m"]
    ry0 = yt - f["rail_m"]
    bars = []
    for i, (s0, s1) in enumerate(runs):
        if s1 - s0 < f["pitch_m"]:
            raise ValueError(f"the fence's run s {s0:.3f}..{s1:.3f} is shorter than a bar's pitch")
        sm.box(sm.F, "fence_base", s0, s1, 0.0, yb, zc - hb, zc + hb, skip=("bottom",), tone=sm.tone("base", i))
        sm.box(sm.F, "fence_rail", s0, s1, ry0, yt, zc - hr, zc + hr)
        if "first_m" in f:      # T-2524: from the gate pier at the print's own pitch, its first bar on the plinth
            p, n = f["pitch_m"], int((s1 - s0 - f["first_m"] - hr) / f["pitch_m"] + 1e-9) + 1
            at = [s0 + f["first_m"] + p * j for j in range(n)] if i else [s1 - f["first_m"] - p * j for j in range(n)]
        else:
            k = round((s1 - s0) / f["pitch_m"])
            p = (s1 - s0) / k
            at = [s0 + p * (j + 0.5) for j in range(k)]
        for s in at:
            sm.box(sm.F, "fence_bar", s - hr, s + hr, yb, ry0, zc - hr, zc + hr, skip=("bottom", "top"))
            bars.append(round(s, 4))
    built = [_gate_pier(sm, pv, pr, zc) for pr in piers]
    gate = piers[-1]["centre_m"] - piers[0]["centre_m"] - 2 * hp
    return {"line_z_m": zl, "runs_s_m": [[round(a, 4), round(c, 4)] for a, c in runs], "bars": len(bars),
            "bar_pitch_m": f["pitch_m"] if "first_m" in f else
            round((runs[1][1] - runs[1][0]) / round((runs[1][1] - runs[1][0]) / f["pitch_m"]), 4),
            "gateway_clear_m": round(gate, 4), "piers": built}


# -- T-3222: the front walk, a K14 walk laid by the K16 front ---------------------------------
#
# A K16 front had no walk: 1638's stair came down onto bare ground and its fence's gateway
# opened on nothing, so the house could not be walked into from the street. K14 routes it
# (`k14_yard._route`: straight out from the stair's foot when the opening is square to it,
# otherwise out, turned along the boundary's back clear of it, and out through the opening to
# the public walk), the condition kit wears it (`path_wear`, front_walk), and it is laid here
# in flags, each leg its own, as `k14_yard.dress_open` lays them. Built in the house's frame
# after its turn (u out of the front toward the street, s north along it, glTF (u, y, -s)), the
# frame `tools/check_house_walks.py` reads, so only a front facing east takes one.

WALK_ROLE = "walk_flag"


def yard_walk(sm: Sample, yv: dict, parts: dict, form: dict, sid: str) -> dict:
    """Lay the record's `yard.front_walk` and return what was built: the legs, the flags and the
    GLB node's K14/K16 component instances (the walk, and the boundary's runs either side of
    its gateway), which the walk gate reads."""
    from archetypes import k14_condition as KC      # numpy, read only by a house with a yard
    if form["layout"]["value"]["faces"] != "east":
        raise ValueError(f"{sid}: a K16 yard is laid about a front facing east")
    if not form.get("boundary"):
        raise ValueError(f"{sid}: a K16 yard's walk comes in through its boundary's gateway, and none is named")
    stoop = parts["porch_right"].meta.get("stoop")
    if not stoop:
        raise ValueError(f"{sid}: a K16 yard's walk starts at the porch stair's foot, and the porch has no stair")
    bv = form["boundary"]["value"]
    pv = bv["pier"]
    hp = pv["plinth_m"] / 2
    p0, p1 = sorted(q["centre_m"] for q in bv["piers"])
    gate = (p0 + hp, p1 - hp)                        # between the plinths' faces
    line = bv["street_line_m"]
    inner = line - pv["plinth_m"]                    # the plinths' back faces, the boundary's back
    axis = parts["porch_right"].O[0]                 # the porch's middle, the stair's axis
    foot = stoop["foot_z_m"]
    F = yv["front_walk"]
    w, top, fk = float(F["width_m"]), float(F["top_m"]), 1.0 - float(F["wear_tone"])
    legs = K14._route((foot, axis - w / 2, axis + w / 2), [gate], inner, line, w)
    g = K14._grade_spec(yv)
    cond, seed, built = KC.Condition(), KC.property_seed(sid), float(yv["built"])

    def rise(u, s):        # the app's ground over the house's base (yard.grade_m): `front` at the front, `street` at the line
        if g is None:
            return 0.0
        f, st_, k = float(g["front"]), float(g["street"]), float(g.get("per_m_s", 0.0))
        t = min(1.0, max(0.0, u / line))
        return max(0.0, f + (st_ - f) * t + k * (s - axis))

    pr = sm.prims.setdefault(WALK_ROLE, Prim(WALK_ROLE))
    nflags = 0
    for li, (u0, u1, s0, s1, along) in enumerate(legs):
        L = (u1 - u0) if along == "u" else (s1 - s0)
        nf = max(1, round(L / float(F["flag_m"])))
        fl = (L - (nf - 1) * K14.JOINT_M) / nf
        cu, cs = (u0 + u1) / 2, (s0 + s1) / 2
        half = ((s1 - s0) if along == "u" else (u1 - u0)) / 2
        offs = (-half, -0.5, -0.25, 0.0, 0.25, 0.5, half)
        for j in range(nf):
            a0 = (u0 if along == "u" else s0) + j * (fl + K14.JOINT_M)
            a1 = a0 + fl
            q0, q1, r0, r1 = (a0, a1, s0, s1) if along == "u" else (u0, u1, a0, a1)
            # the flag's top, a grid of rows along the leg and columns across it, each vertex
            # toned by the wear across the walk's centre line at that point
            if along == "u":
                cols = sorted({min(s1, max(s0, cs + o)) for o in offs})
                n = max(1, math.ceil((q1 - q0) / K14.ROW_U - 1e-9))
                grid = [[(q0 + (q1 - q0) * i / n, s) for s in cols] for i in range(n + 1)]
                wear = lambda u, s: cond.path_wear(s - cs, u, use="front_walk", built=built, seed=seed)
            else:
                cols = sorted({min(u1, max(u0, cu + o)) for o in offs})
                n = max(1, math.ceil((r1 - r0) / K14.ROW_U - 1e-9))
                grid = [[(u, r0 + (r1 - r0) * i / n) for u in cols] for i in range(n + 1)]
                wear = lambda u, s: cond.path_wear(u - cu, s, use="front_walk", built=built, seed=seed)
            for ra, rb in zip(grid, grid[1:]):
                for c in range(len(ra) - 1):
                    cell = [ra[c], ra[c + 1], rb[c + 1], rb[c]]
                    if abs((cell[2][0] - cell[0][0]) * (cell[2][1] - cell[0][1])) < 1e-9:
                        continue
                    sm.face(WALK_ROLE, [(u, top + rise(u, s), -s) for u, s in cell], (0.0, 1.0, 0.0))
                    for i in range(1, 5):
                        x, _y, z = pr.pos[-i]
                        pr.tone[-i] = round(1.0 - fk * float(wear(x, -z)), 5)
            # its four edges down to its bed; the first abuts the stair's bottom riser
            sides = [((q0, r0), (q1, r0), (0.0, 0.0, 1.0)), ((q0, r1), (q1, r1), (0.0, 0.0, -1.0)),
                     ((q1, r0), (q1, r1), (1.0, 0.0, 0.0)), ((q0, r0), (q0, r1), (-1.0, 0.0, 0.0))]
            if li == 0 and j == 0:
                sides.pop()
            for (ua, sa), (ub, sb), hint in sides:
                sm.face(WALK_ROLE, [(ua, -K14.FLAG_SINK + rise(ua, sa), -sa), (ub, -K14.FLAG_SINK + rise(ub, sb), -sb),
                                    (ub, top + rise(ub, sb), -sb), (ua, top + rise(ua, sa), -sa)], hint)
            nflags += 1
    rl = [[round(u0, 4), round(u1, 4), round(s0, 4), round(s1, 4), al] for u0, u1, s0, s1, al in legs]
    s_lo, s_hi = bv["lot_s_m"]
    x = line - hp                                    # the boundary's line, through the plinths' middles
    runs = [(s_lo + bv["end_clear_m"], gate[0]), (gate[1], s_hi - bv["end_clear_m"])]
    walk = {"id": K14.FRONT_WALK, "family": "yard", "instances": [{
        "params": {"flags": nflags, "width_m": round(w, 4), "triangles": len(pr.idx) // 3, "legs_m": rl},
        "sockets": {"stoop_foot": [round(legs[0][0], 4), top, round(-(legs[0][2] + legs[0][3]) / 2, 4)],
                    "public_walk": [round(line, 4), top, round(-(legs[-1][2] + legs[-1][3]) / 2, 4)]}}]}
    fence = {"id": "k16.boundary.street_fence", "family": "fence", "instances": [
        {"params": {"run": i, "s_m": [round(a, 4), round(b, 4)]},
         "sockets": {"end_a": [round(x, 4), 0.0, round(-a, 4)], "end_b": [round(x, 4), 0.0, round(-b, 4)]}}
        for i, (a, b) in enumerate(runs)]}
    return {"legs_m": rl, "flags": nflags, "gateway_s_m": [round(gate[0], 4), round(gate[1], 4)],
            "components": [walk, fence]}


def structure_materials(house: Sample, data: dict, form: dict) -> dict:
    """The materials a house draws, and only those; its roof takes the record's covering."""
    mats = materials(data)
    mats["stand_in"] = dict(STAND_IN, color=tuple(form["body"]["value"].get("color", STAND_IN["color"])))
    mats.update(BOUNDARY_MATERIALS)     # T-2456: kept below only where a boundary uses them
    cov = form.get("roof_covering")
    if cov and cov["value"].get("color"):
        mats["roof"] = dict(mats["roof"], color=tuple(cov["value"]["color"]), roughness=0.9)
    used = {ROLE_MATERIAL[r] for r, pr in house.prims.items() if pr.idx}
    return {k: m for k, m in mats.items() if k in used}


def structure_glb(house: Sample, data: dict, form: dict, structure_id: str, phase_id: str, scene_ids) -> bytes:
    name = f"{structure_id}__{phase_id}"
    return to_glb([house], data, node_name=name, mats=structure_materials(house, data, form), node_extras={
        "structure_id": structure_id, "phase_id": phase_id, "scene_ids": list(scene_ids),
        "parts_triangles": house.meta["parts"],
        # T-3222: a house with a yard names its walk and its boundary's runs, as a K01 front does
        **({"k16": {"components": house.meta["yard"]["components"]}} if house.meta.get("yard") else {})},
        extras={"ticket": "T-2323", "structure": f"data/structures/{structure_id}.json"})


# -- T-2357: a whole small frame house, closed on every face from the kit ------------------------
#
# The record's `frame_house` names blocks in the LOT PLAN frame the district draft used — u
# from the rear toward the street, v along the street front, glTF (u, y, -v) — so the record
# keeps the draft's position and rotation. Every wall is a kit `clapboard_wall` built in its
# own frame and set down on its side of its block; the walls run counter-clockwise from above
# (east, north, west, south), each turning its outside corner with a short return that the
# next wall's cladding takes up from, so the block closes with every corner a K16 corner.

SIDE_RUN = {   # side -> (start corner of rect_uv as (u index, v index), direction in glTF)
    "east": ((2, 1), (0.0, 0.0, -1.0)), "north": ((2, 3), (-1.0, 0.0, 0.0)),
    "west": ((0, 3), (0.0, 0.0, 1.0)), "south": ((0, 1), (1.0, 0.0, 0.0)),
}


def side_frame(rect, side):
    """The start corner (glTF), the run direction and the length of one side of a block."""
    (iu, iv), U = SIDE_RUN[side]
    O = (rect[iu], 0.0, -rect[iv])
    L = rect[3] - rect[1] if side in ("east", "west") else rect[2] - rect[0]
    return O, U, L


def place(sm: Sample, O, U) -> None:
    """Set a sample built in the default frame (s along x, z out) down at O with its s along
    U: a turn about y and a move, so its UVs (surface metres) are untouched."""
    N = _cross(U, Y)
    for pr in sm.prims.values():
        pr.pos = [_add(O, _add(_add(_mul(U, p[0]), _mul(Y, p[1])), _mul(N, p[2]))) for p in pr.pos]
        pr.nrm = [_add(_add(_mul(U, n[0]), _mul(Y, n[1])), _mul(N, n[2])) for n in pr.nrm]
    at = lambda p: _add(O, _add(_add(_mul(U, p[0]), _mul(Y, p[1])), _mul(N, p[2])))
    turn = lambda d: _add(_add(_mul(U, d[0]), _mul(Y, d[1])), _mul(N, d[2]))
    for fr in sm.meta["frames"]:     # the gate reads each run in its own frame: move those too
        fr["origin"] = [round(c, 6) for c in at(fr["origin"])]
        fr["u"], fr["n"] = [round(c, 6) for c in turn(fr["u"])], [round(c, 6) for c in turn(fr["n"])]
    sm.O = at(sm.O)


def frame_house_parts(st: dict, phase: dict, data: dict | None = None) -> dict:
    """Every wall and porch half of a whole frame house, built and set in place, keyed
    `<block>.<side>` and `porch_right` / `porch_left`: what the gate measures, each held to
    the kit's rules the way its specimen sample is."""
    data = data or load()
    fh = phase["form"]["frame_house"]["value"]
    sid = st["id"]
    D = fh["return_m"]
    out = {}
    for b in fh["blocks"]:
        walls = b["walls"]
        free = not b.get("against")
        for i, w in enumerate(walls):
            O, U, L = side_frame(b["rect_uv"], w["side"])
            last = i == len(walls) - 1
            start = D if (free or i > 0) else 0.0     # the previous wall's return covers this much
            ret = 0.0 if (last and not free) else D
            v = {"id": f"k16.wall.{sid}.{b['id']}_{w['side']}", "kind": "clapboard_wall", "use": "wall",
                 "width_m": round(L - start, 6), "return_m": ret, "foundation_m": fh["foundation_m"],
                 "wall_top_m": b["wall_top_m"],
                 **({"frieze_m": b["frieze_m"]} if "frieze_m" in b else {}),     # T-3180: a block's own frieze
                 **{k: b[k] for k in ("eave", "bracket") if k in b},              # T-3182: its own eave
                 **({"bracket_pairs_m": [round(x - start, 6) for x in w["bracket_pairs_m"]]}
                    if "bracket_pairs_m" in w else {}),
                 **({"frieze_lights": [dict(x, centre_m=round(x["centre_m"] - start, 6)) for x in w["frieze_lights"]]}
                    if "frieze_lights" in w else {}),
                 "windows": [dict(x, centre_m=round(x["centre_m"] - start, 6)) for x in w.get("windows", [])],
                 "doors": [dict(x, centre_m=round(x["centre_m"] - start, 6)) for x in w.get("doors", [])]}
            sm = Sample(v, data, index=0).build()
            place(sm, _add(O, _mul(U, start)), U)
            out[f"{b['id']}.{w['side']}"] = sm
            if b["roof"]["kind"] == "gable" and w["side"] in GABLE_SIDES[b["roof"].get("ridge", "u")]:
                ev = data["trim"]["eave"]       # T-2398: the gable over this end wall
                g = {"id": f"k16.gable.{sid}.{b['id']}_{w['side']}", "kind": "gable_end", "use": "wall",
                     "width_m": L, "base_m": b["wall_top_m"] + ev["fascia_m"], "pitch_deg": b["roof"]["pitch_deg"],
                     "projection_m": ev["projection_m"], "fascia_m": ev["fascia_m"],
                     "windows": w.get("gable_windows", [])}
                sm = Sample(g, data, index=0).build()
                place(sm, O, U)
                out[f"{b['id']}.{w['side']}_gable"] = sm
    po = fh.get("porch")
    if po:
        main = fh["blocks"][0]
        O, U, _ = side_frame(main["rect_uv"], po.get("side", "east"))
        half = dict(po, width_m=po["half_width_m"])
        probe = Sample(half, data).build()
        reach = max(p[0] for pr in probe.prims.values() for p in pr.pos)
        c = po["centre_m"]
        right = Sample(half, data, (c, 0.0, 0.0)).build()
        left = Sample(half, data, (c, 0.0, 0.0)).build()
        mirror_s(left, c)
        steps = po.get("steps")
        if steps:
            _porch_steps(right, data, po, steps)
        for k, sm in (("porch_right", right), ("porch_left", left)):
            place(sm, O, U)
            out[k] = sm
        out["_porch_reach_m"] = reach
    for j, bay in enumerate(fh.get("bays") or []):
        out.update(_frame_bay_faces(sid, fh, bay, data, j))
    return out


def _bay_frame(fh: dict, bay: dict):
    """T-3182: where a frame house's bay plan stands: its (s, z) run along the named side of the
    first block from that side's start corner, z out from the wall."""
    O, U, _ = side_frame(fh["blocks"][0]["rect_uv"], bay["side"])
    return O, U, _cross(U, Y)


def _frame_bay_faces(sid: str, fh: dict, bay: dict, data: dict, j: int) -> dict:
    """T-3182: an upper-storey canted bay standing on a frame house's porch deck, 1720 Prairie's
    photograph: each face of its plan a kit `clapboard_wall` with no return, a post at each
    angle (the corner board widened to `post_m`) and that face's own `windows`; and, where the
    plan's first point stands past the wall's start corner (`back`), a plain face closing the
    bay's back from that point to the corner. Each face is keyed `bay<j>.<i>`."""
    plan = [tuple(q) for q in bay["plan"]]
    Ow, Uw, Nw = _bay_frame(fh, bay)
    at = lambda q: _add(Ow, _add(_mul(Uw, q[0]), _mul(Nw, q[1])))
    fd = copy.deepcopy(data)
    fd["trim"]["corner_board"]["width_m"] = bay["post_m"]
    fd["trim"]["frieze"]["height_m"] = bay["frieze_m"]
    wt = fd["trim"]["water_table"]
    y_fd = round(bay["base_m"] - wt["height_m"] - wt["cap"]["height_m"], 6)
    runs = [(a, b, f.get("windows", [])) for (a, b), f in zip(zip(plan, plan[1:]), bay["faces"])]
    if plan[0][0] < 0:
        runs.append(((0.0, 0.0), plan[0], []))
    out = {}
    for i, (a, b, wins) in enumerate(runs):
        W = math.hypot(b[0] - a[0], b[1] - a[1])
        v = {"id": f"k16.wall.{sid}.bay{j}_{i}", "kind": "clapboard_wall", "use": "wall", "width_m": round(W, 6),
             "return_m": 0.0, "boards": [True, True], "foundation_m": y_fd, "wall_top_m": bay["wall_top_m"],
             "windows": wins}
        sm = Sample(v, fd).build()
        for role in BAY_DROP:
            sm.prims.pop(role, None)
        A, B = at(a), at(b)
        place(sm, A, _unit(_sub(B, A)))
        sm.seed = seed_of(v["id"], 0, sid)
        out[f"bay{j}.{i}"] = sm
    return out


def _frame_bay_trim(house: Sample, fh: dict, bay: dict, data: dict) -> dict:
    """T-3182: the bay's base on the deck, its cornice round the plan, a raised panel under each
    face's lights, and its hipped cap: each slope rising from the cornice's edge to the wall,
    the front's to a level line `cap_rise_m` over the cornice, the cants' to that line's ends.
    Where the plan stands past the wall's corner, the cap's back is closed down to the cornice."""
    plan = [tuple(q) for q in bay["plan"]]
    sm = Sample({"id": f"{house.v['id']}.bay", "kind": "structure", "use": "structure"}, data)
    yf, yb, ys = bay["floor_m"], bay["base_m"] - bay["floor_m"], bay["wall_top_m"]
    base = tuple((o, y if y is not None else yb - (0.09, 0.09, 0.04, 0.0)[k - 4])
                 for k, (o, y) in enumerate(BAY_BASE))
    bay_ring(sm, plan, base, (None, "water_table", "water_table", "apron", "sill", "sill", "sill"), yf)
    bay_ring(sm, plan, BAY_CORNICE, ("soffit", "fascia", "drip_cap", "drip_cap", "drip_cap", "drip_cap"), ys)
    ct = data["trim"]["corner_board"]["thickness_m"]
    for i, (a, b) in enumerate(zip(plan, plan[1:])):
        F = Frame(f"bay_{i}", (a[0], 0.0, a[1]), (b[0] - a[0], 0.0, b[1] - a[1]), (-(b[1] - a[1]), 0.0, b[0] - a[0]))
        W = math.hypot(b[0] - a[0], b[1] - a[1])
        inset = bay["post_m"] - ct + 0.05
        sm.box(F, "casing", inset, W - inset, yf + 0.17, yf + yb - 0.12, 0.035, 0.035 + ct * 0.6, skip=("back",),
               tone=sm.tone("bay_panel", i))
    top = ys + BAY_CORNICE[-1][1]
    edge, _ = bay_offset(plan, BAY_CORNICE[-1][0])
    yr = top + bay["cap_rise_m"]
    e = [(q[0], top, q[1]) for q in edge]
    w1, w2 = (edge[1][0], yr, 0.0), (edge[2][0], yr, 0.0)
    sm.face("roof_covering", [e[0], e[1], w1], (0.0, 1.0, 0.0))
    sm.face("roof_covering", [e[1], e[2], w2, w1], (0.0, 1.0, 0.0))
    sm.face("roof_covering", [e[2], e[3], w2], (0.0, 1.0, 0.0))
    if edge[0][0] < 0:     # the cap's back, past the corner: a board down to the cornice
        y0 = yr if w1[0] <= 0 else top + (yr - top) * (0.0 - edge[0][0]) / (w1[0] - edge[0][0])
        back = [(edge[0][0], top, 0.0)] + ([w1] if w1[0] < 0 else []) + [(0.0, y0, 0.0), (0.0, top, 0.0)]
        sm.face("frieze", back, (0.0, 0.0, -1.0))
        sm.face("frieze", [(edge[0][0], ys, 0.0), (0.0, ys, 0.0), (0.0, top, 0.0), (edge[0][0], top, 0.0)],
                (0.0, 0.0, -1.0))
    Ow, Uw, _ = _bay_frame(fh, bay)
    place(sm, Ow, Uw)
    for role, pr in sm.prims.items():
        absorb(house.prims.setdefault(role, Prim(role)), pr)
    return {"plan": [list(q) for q in plan], "floor_m": yf, "wall_top_m": ys, "cap_top_m": round(yr, 4)}


def _front_gable(house: Sample, b: dict, fg: dict, P_: float, fh_m: float) -> dict:
    """T-3182: a low gable over the middle of a block's east front, standing on its eave, 1720
    Prairie's photograph: a boarded tympanum flush with the eave's fascia, a rake board
    `rake_m` deep `overhang_m` out from it, a soffit under the rake back to the tympanum, and
    two roof slopes run back from the rake to where the ridge meets the hip's front slope."""
    u0, v0, u1, v1 = b["rect_uv"]
    t = math.tan(math.radians(fg["pitch_deg"]))
    th = math.tan(math.radians(b["roof"]["pitch_deg"]))
    hw, vc = fg["width_m"] / 2, fg["centre_m"]
    ye = b["wall_top_m"] + fh_m
    ya = ye + hw * t
    xt = u1 + P_
    xf, rk = xt + fg["overhang_m"], fg["rake_m"]
    xr = xt - (ya - ye) / th                 # where the ridge runs into the hip's front slope
    zc = -vc
    F = house.F
    house.poly(F, "board", [(xt, ye, zc + hw), (xt, ye, zc - hw), (xt, ya, zc)], (1, 0, 0))
    for side in (1, -1):
        ze = zc + side * hw
        house.poly(F, "roof_covering", [(xf, ye, ze), (xf, ya, zc), (xr, ya, zc), (xt, ye, ze)], (0, 1, side))
        house.poly(F, "fascia", [(xf, ye - rk, ze), (xf, ye, ze), (xf, ya, zc), (xf, ya - rk, zc)], (1, 0, 0))
        house.poly(F, "soffit", [(xt, ye - rk, ze), (xf, ye - rk, ze), (xf, ya - rk, zc), (xt, ya - rk, zc)],
                   (0, -1, -side * t))
        house.poly(F, "fascia", [(xt, ye - rk, ze), (xf, ye - rk, ze), (xf, ye, ze), (xt, ye, ze)], (0, 0, side))
    return {"centre_m": vc, "width_m": fg["width_m"], "apex_m": round(ya, 4)}


def _porch_steps(sm: Sample, data: dict, po: dict, steps: dict) -> None:
    """Timber steps from grade to the porch floor in front of `steps.centre_m` (in the
    porch's own frame, before it is set down): risers equal and solved from the floor
    height, each step a block with an oiled tread and painted riser and strings."""
    fl = data["porch"]["floor"]
    yf, Dp = fl["height_m"] + po.get("basement_m", 0.0), po.get("depth_m", fl["depth_m"])   # T-3180: a raised floor
    n = max(2, math.ceil(yf / steps["max_riser_m"] - 1e-9))
    r, g = yf / n, steps["going_m"]
    c, hw = steps["centre_m"] - po["centre_m"], steps["width_m"] / 2   # in the half's own frame
    z_edge = Dp + fl["nosing_m"]
    for k in range(1, n):             # the floor is the top tread
        z0 = z_edge + (n - 1 - k) * g
        sm.box(sm.F, "step_riser", c - hw, c + hw, 0.0, k * r, z0, z0 + g, skip=("back", "bottom"),
               tone=sm.tone("step", k), roles={"top": "step_tread"})
    sm.meta["steps"] = {"risers": n, "riser_m": round(r, 6), "going_m": g, "width_m": steps["width_m"]}
    if steps.get("cheek"):
        _stair_cheeks(sm, steps["cheek"], c, hw, n, r, g, z_edge, yf)


#: T-3181: a turned baluster's profile, [half-width as a share of its greatest, share of its height]:
#: a square foot, a neck, the vase's belly, a second neck and a square head
BALUSTER = [(0.75, 0.0), (0.5, 0.12), (1.0, 0.38), (0.42, 0.72), (0.7, 0.86), (0.75, 1.0)]


def _stair_cheeks(sm: Sample, ch: dict, c: float, hw: float, n: int, r: float, g: float, z_edge: float,
                  yf: float) -> None:
    """T-3181: a raking balustrade either side of the stair: a closed string `width_m` thick let
    0.02 m into the steps' ends, its top `string_above_m` over the nosings' line, turned
    balusters on it at `pitch_m`, a raking rail `height_m` over the nosings, and a newel at the
    foot `newel_above_m` over the rail. The steps are built whole in the right half, so both
    cheeks are too."""
    F = sm.F
    z_foot = z_edge + (n - 1) * g                      # the bottom step's nosing
    nose = lambda z: (n - (z - z_edge) / g) * r        # the nosings' line
    cw, sa, H = ch["width_m"], ch["string_above_m"], ch["height_m"]
    rh, rw, nw = ch["rail_m"], ch["rail_width_m"], ch["newel_m"]
    z_n0 = z_foot - nw / 2                             # the newel's back face
    t = sm.tone("string")
    k = max(1, round((z_n0 - z_edge) / ch["pitch_m"]))
    for side in (-1, 1):
        s0 = c + side * (hw - 0.02)
        s1 = s0 + side * cw
        sc = (s0 + s1) / 2
        lo, hi = min(s0, s1), max(s0, s1)
        z_b = z_edge - 0.01        # its back end under the floor's nosing, clear of the boards' end grain
        string = [(z_b, 0.0), (z_n0, 0.0), (z_n0, nose(z_n0) + sa), (z_b, nose(z_b) + sa)]
        rail = [(z_b, nose(z_b) + H - rh), (z_n0, nose(z_n0) + H - rh), (z_n0, nose(z_n0) + H), (z_b, nose(z_b) + H)]
        for role, prof in (("string", string), ("rail", rail)):
            if role == "rail":     # the rail as broad as its own section, centred over the string
                lo, hi = sc - rw / 2, sc + rw / 2
            for s_, hs in ((lo, -1), (hi, 1)):
                sm.poly(F, role, [(s_, y, z) for z, y in prof], (hs, 0, 0), t)
            (z0, y0), (z1, y1), (z2, y2), (z3, y3) = prof
            # the top, the back end, and (the rail's) underside; the foot dies into the newel
            sm.poly(F, role, [(lo, y2, z2), (hi, y2, z2), (hi, y3, z3), (lo, y3, z3)], (0, 1, 0), t)
            sm.poly(F, role, [(lo, y3, z3), (hi, y3, z3), (hi, y0, z0), (lo, y0, z0)], (0, 0, -1), t)
            if role == "rail":
                sm.poly(F, role, [(lo, y0, z0), (hi, y0, z0), (hi, y1, z1), (lo, y1, z1)], (0, -1, 0), t)
        for j in range(k):
            z = z_edge + (z_n0 - z_edge) * (j + 0.5) / k
            sm._turned(F, "baluster", sc, z, nose(z) + sa, nose(z) + H - rh, ch["baluster_m"], BALUSTER,
                       sm.tone("baluster", j))
        y_n = nose(z_foot) + H + ch["newel_above_m"]
        sm.box(F, "newel", sc - nw / 2, sc + nw / 2, 0.0, y_n, z_n0, z_n0 + nw, skip=("bottom",), tone=sm.tone("newel", side))
    sm.meta["cheeks"] = {"balusters": 2 * k, "foot_z_m": round(z_foot, 6), "height_m": H}


#: T-2398: the end walls a gable roof stands its gables on, by the plan axis its ridge runs along
GABLE_SIDES = {"u": ("east", "west"), "v": ("north", "south")}


def _gable(house: Sample, x0, x1, z0, z1, ye, pitch_deg, ridge, walls, fh):
    """T-2398: a gable over the eave rectangle, its ridge along the plan's u (x) or v (z). Each
    gable end is closed under its verge by a box the eave's depth: a soffit under the slope from
    the wall out, and a fascia at its outer edge. `walls` gives each end's wall plane."""
    t = math.tan(math.radians(pitch_deg))
    F = house.F
    if ridge == "u":
        zm, yr = (z0 + z1) / 2, ye + (z1 - z0) / 2 * t
        house.poly(F, "roof_covering", [(x0, ye, z1), (x1, ye, z1), (x1, yr, zm), (x0, yr, zm)], (0, 1, 1))
        house.poly(F, "roof_covering", [(x1, ye, z0), (x0, ye, z0), (x0, yr, zm), (x1, yr, zm)], (0, 1, -1))
        for xo, xw, hs in ((x1, walls[0], 1), (x0, walls[1], -1)):
            for ze in (z0, z1):
                hz = 1 if ze > zm else -1
                house.poly(F, "fascia", [(xo, ye - fh, ze), (xo, yr - fh, zm), (xo, yr, zm), (xo, ye, ze)], (hs, 0, 0))
                house.poly(F, "soffit", [(xw, ye - fh, ze), (xo, ye - fh, ze), (xo, yr - fh, zm), (xw, yr - fh, zm)],
                           (0, -1, -hz * t))
        return yr, ("x", x0, x1, zm)
    xm, yr = (x0 + x1) / 2, ye + (x1 - x0) / 2 * t
    house.poly(F, "roof_covering", [(x1, ye, z0), (x1, ye, z1), (xm, yr, z1), (xm, yr, z0)], (1, 1, 0))
    house.poly(F, "roof_covering", [(x0, ye, z1), (x0, ye, z0), (xm, yr, z0), (xm, yr, z1)], (-1, 1, 0))
    for zo, zw, hs in ((z0, walls[0], -1), (z1, walls[1], 1)):
        for xe in (x0, x1):
            hx = 1 if xe > xm else -1
            house.poly(F, "fascia", [(xe, ye - fh, zo), (xm, yr - fh, zo), (xm, yr, zo), (xe, ye, zo)], (0, 0, hs))
            house.poly(F, "soffit", [(xe, ye - fh, zw), (xe, ye - fh, zo), (xm, yr - fh, zo), (xm, yr - fh, zw)],
                       (-hx * t, -1, 0))
    return yr, ("z", z0, z1, xm)


def _hip(house: Sample, x0, x1, z0, z1, ye, pitch_deg):
    """A hip over the eave rectangle: the ridge along the longer side, four planes."""
    t = math.tan(math.radians(pitch_deg))
    F = house.F
    if (x1 - x0) >= (z1 - z0):
        h = (z1 - z0) / 2
        zm, xa, xb, yr = (z0 + z1) / 2, x0 + h, x1 - h, ye + h * t
        house.poly(F, "roof_covering", [(x0, ye, z1), (x1, ye, z1), (xb, yr, zm), (xa, yr, zm)], (0, 1, 1))
        house.poly(F, "roof_covering", [(x1, ye, z0), (x0, ye, z0), (xa, yr, zm), (xb, yr, zm)], (0, 1, -1))
        house.poly(F, "roof_covering", [(x0, ye, z0), (x0, ye, z1), (xa, yr, zm)], (-1, 1, 0))
        house.poly(F, "roof_covering", [(x1, ye, z1), (x1, ye, z0), (xb, yr, zm)], (1, 1, 0))
        return yr, ("x", xa, xb, zm)
    h = (x1 - x0) / 2
    xm, za, zb, yr = (x0 + x1) / 2, z0 + h, z1 - h, ye + h * t
    house.poly(F, "roof_covering", [(x1, ye, z0), (x1, ye, z1), (xm, yr, zb), (xm, yr, za)], (1, 1, 0))
    house.poly(F, "roof_covering", [(x0, ye, z1), (x0, ye, z0), (xm, yr, za), (xm, yr, zb)], (-1, 1, 0))
    house.poly(F, "roof_covering", [(x0, ye, z0), (x1, ye, z0), (xm, yr, za)], (0, 1, -1))
    house.poly(F, "roof_covering", [(x1, ye, z1), (x0, ye, z1), (xm, yr, zb)], (0, 1, 1))
    return yr, ("z", za, zb, xm)


def frame_house(st: dict, phase: dict, data: dict | None = None) -> Sample:
    """The whole house merged into one sample in the lot plan frame (T-2357)."""
    data = data or load()
    fh = phase["form"]["frame_house"]["value"]
    parts = frame_house_parts(st, phase, data)
    ev = data["trim"]["eave"]
    P_, fh_m = ev["projection_m"], ev["fascia_m"]
    house = Sample({"id": st["id"], "kind": "structure", "use": "structure"}, data)
    ridge = {}
    for i, b in enumerate(fh["blocks"]):
        u0, v0, u1, v1 = b["rect_uv"]
        P_ = (b.get("eave") or {}).get("projection_m", ev["projection_m"])     # T-3182: a block's own eave
        x0, x1, z0, z1 = u0 - P_, u1 + P_, -v1 - P_, -v0 + P_
        if b.get("against"):     # the eave stops on the wall the block stands against
            a = b["against"]
            x0, x1, z0, z1 = (u0 if a == "west" else x0, u1 if a == "east" else x1,
                              -v1 if a == "north" else z0, -v0 if a == "south" else z1)
        ye = b["wall_top_m"] + fh_m
        roof = b["roof"]
        if roof["kind"] == "hip":
            ridge[b["id"]] = _hip(house, x0, x1, z0, z1, ye, roof["pitch_deg"])
        elif roof["kind"] == "gable":
            along = roof.get("ridge", "u")
            walls = (u1, u0) if along == "u" else (-v1, -v0)
            ridge[b["id"]] = _gable(house, x0, x1, z0, z1, ye, roof["pitch_deg"], along, walls, fh_m)
        else:                   # a flat deck just over the eave's top, its edges closed
            yd = ye + roof.get("deck_m", 0.03)
            house.poly(house.F, "roof_covering", [(x0, yd, z1), (x1, yd, z1), (x1, yd, z0), (x0, yd, z0)], (0, 1, 0))
            for q, hnt in (([(x0, ye, z1), (x1, ye, z1), (x1, yd, z1), (x0, yd, z1)], (0, 0, 1)),
                           ([(x1, ye, z0), (x0, ye, z0), (x0, yd, z0), (x1, yd, z0)], (0, 0, -1)),
                           ([(x0, ye, z0), (x0, ye, z1), (x0, yd, z1), (x0, yd, z0)], (-1, 0, 0)),
                           ([(x1, ye, z1), (x1, ye, z0), (x1, yd, z0), (x1, yd, z1)], (1, 0, 0))):
                house.poly(house.F, "roof_covering", q, hnt)
            ridge[b["id"]] = (yd, None)
        if b.get("front_gable"):
            house.meta["front_gable"] = _front_gable(house, b, b["front_gable"], P_, fh_m)
    for bay in fh.get("bays") or []:
        house.meta.setdefault("bays", []).append(_frame_bay_trim(house, fh, bay, data))
    ch = fh.get("chimney")
    if ch:
        yr = ridge[fh["blocks"][0]["id"]][0]
        xc, zc = ch["u_m"], -ch["v_m"]
        hx, hz = ch["width_m"] / 2, ch["depth_m"] / 2
        y_top = yr + ch["above_ridge_m"]
        y_foot = fh["blocks"][0]["wall_top_m"]
        cap, ch_h = ch.get("cap_m", 0.05), ch.get("cap_height_m", 0.15)
        house.box(house.F, "chimney", xc - hx, xc + hx, y_foot, y_top - ch_h, zc - hz, zc + hz, skip=("bottom",),
                  roles={"top": "chimney"})
        house.box(house.F, "chimney", xc - hx - cap, xc + hx + cap, y_top - ch_h, y_top, zc - hz - cap, zc + hz + cap)
    for k, sm in parts.items():
        if k.startswith("_"):
            continue
        for role, pr in sm.prims.items():
            if role in ("backdrop", "interior", "cut"):
                continue
            absorb(house.prims.setdefault(role, Prim(role)), pr)
    main = fh["blocks"][0]["rect_uv"]
    house.meta.update({"parts": {k: triangles(sm) for k, sm in parts.items() if not k.startswith("_")},
                       "focus": [main[2], 3.0, -(main[1] + main[3]) / 2], "span_m": 12.0})
    return house


def frame_house_materials(house: Sample, data: dict, form: dict) -> dict:
    """The materials a whole frame house draws: the kit's, its own body paint where the
    record names one, its roof's covering and its stack's brick."""
    mats = materials(data)
    mats.update(BOUNDARY_MATERIALS)     # T-3181: a porch's iron cresting; kept below only where used
    paint = form["frame_house"]["value"].get("paint") or {}
    for k, col in paint.items():
        mats[k] = dict(mats[k], color=tuple(col))
    cov = form.get("roof_covering")
    if cov and cov["value"].get("color"):
        mats["roof"] = dict(mats["roof"], color=tuple(cov["value"]["color"]), roughness=0.9)
    used = {ROLE_MATERIAL[r] for r, pr in house.prims.items() if pr.idx}
    return {k: m for k, m in mats.items() if k in used}


def frame_house_glb(house: Sample, data: dict, form: dict, structure_id: str, phase_id: str, scene_ids) -> bytes:
    name = f"{structure_id}__{phase_id}"
    return to_glb([house], data, node_name=name, mats=frame_house_materials(house, data, form), node_extras={
        "structure_id": structure_id, "phase_id": phase_id, "scene_ids": list(scene_ids),
        "parts_triangles": house.meta["parts"]},
        extras={"ticket": "T-2357", "structure": f"data/structures/{structure_id}.json"})


# -- the kit -------------------------------------------------------------------------------------

PANEL_GAP = 1.2


def load() -> dict:
    return json.loads(DATA.read_text())


def extents(sm: Sample):
    xs = [p[0] for pr in sm.prims.values() for p in pr.pos]
    return min(xs), max(xs)


def build_variant(v: dict, data: dict, origin=(0.0, 0.0, 0.0), index: int = 0) -> Sample:
    return Sample(v, data, origin, index).build()


def build_kit(data: dict | None = None) -> list[Sample]:
    data = data or load()
    out, x = [], 0.0
    for i, v in enumerate(data["samples"]):
        lo, hi = extents(build_variant(v, data, index=i))
        sm = build_variant(v, data, origin=(x - lo, 0.0, 0.0), index=i)
        out.append(sm)
        x += (hi - lo) + PANEL_GAP
    return out


def triangles(sm: Sample, include_board: bool = False) -> int:
    return sum(len(p.idx) // 3 for r, p in sm.prims.items() if include_board or r not in BOARD_ROLES)


# -- glTF ----------------------------------------------------------------------------------------

def _pad(b: bytes, fill: bytes = b"\x00") -> bytes:
    return b + fill * ((4 - len(b) % 4) % 4)


def to_glb(kit: list[Sample], data: dict, node_name: str | None = None, node_extras: dict | None = None,
           extras: dict | None = None, mats: dict | None = None) -> bytes:
    mats = mats or materials(data)
    bin_ = bytearray()
    views, accessors, meshes, nodes = [], [], [], []

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

    mat_names = list(mats)
    materials_out = []
    for name in mat_names:
        m = mats[name]
        alpha = m.get("alpha", 1.0)
        entry = {"name": f"k16_{name}", "pbrMetallicRoughness": {
            "baseColorFactor": [*[round(c, 4) for c in m["color"]], alpha],
            "metallicFactor": m.get("metallic", 0.0), "roughnessFactor": m["roughness"]},
            "extras": {"class": m["class"]}}
        if alpha < 1.0:
            entry["alphaMode"] = "BLEND"
        materials_out.append(entry)
    for sm in kit:
        by_mat: dict[str, list[Prim]] = {}
        for role in ROLE_MATERIAL:   # fixed order
            if role in sm.prims and sm.prims[role].idx:
                by_mat.setdefault(ROLE_MATERIAL[role], []).append(sm.prims[role])
        prims_out = []
        for name in mat_names:
            if name not in by_mat:
                continue
            pos, nrm, uv, conf, col, idx = [], [], [], [], [], []
            for pr in by_mat[name]:
                base = len(pos)
                pos += [tuple(round(c, 5) for c in q) for q in pr.pos]
                nrm += pr.nrm
                uv += pr.uv
                conf += pr.conf
                col += [(t, t, t) for t in pr.tone]
                idx += [base + i for i in pr.idx]
            ctype = 5123 if len(pos) < 65536 else 5125
            prims_out.append({"attributes": {
                "POSITION": accessor(pos, 5126, "VEC3", 3, 34962, True),
                "NORMAL": accessor(nrm, 5126, "VEC3", 3, 34962),
                "TEXCOORD_0": accessor(uv, 5126, "VEC2", 2, 34962),
                "COLOR_0": accessor(col, 5126, "VEC3", 3, 34962),
                "_CONFIDENCE": accessor(conf, 5126, "SCALAR", 1, 34962)},
                "indices": accessor(idx, ctype, "SCALAR", 1, 34963),
                "material": mat_names.index(name)})
        meshes.append({"name": node_name or sm.v["id"], "primitives": prims_out})
        nodes.append({"name": node_name or sm.v["id"], "mesh": len(meshes) - 1, "extras": {**(node_extras or {}),
            "component_id": sm.v["id"], "family": sm.v["kind"], "seed": sm.seed,
            "origin": [round(c, 4) for c in sm.O],
            "triangles_sample": triangles(sm), "triangles_with_board": triangles(sm, True),
            "sockets": {"base": [0.0, 0.0, 0.0]},
            "focus": [round(c, 4) for c in sm.meta["focus"]], "span_m": sm.meta["span_m"],
            "params": {k: sm.v[k] for k in sm.v if k not in ("note", "confidence")}}})
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
        "extras": {"k16": {"data": "data/components/prairie_1904/k16_timber.json", "ticket": "T-2322",
                           "contract": "data/components/prairie_1904/k01_contract.json",
                           "windows": "data/components/prairie_1904/k06_windows.json", **(extras or {})}},
    }
    js = _pad(json.dumps(gltf, separators=(",", ":"), sort_keys=True).encode(), b" ")
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
                  f"{DATA.relative_to(ROOT)}: run python3 generators/archetypes/k16_timber.py")
            return 1
        print(f"ok   {out.relative_to(ROOT)} is the generator's bytes ({len(blob)} B)")
        return 0
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(blob)
    print(f"wrote {out.relative_to(ROOT)} ({len(blob)} B)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
