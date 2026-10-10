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
}
BOARD_ROLES = ("foundation", "roof", "backdrop", "interior", "cut")
# Roles that are not timber: K06's glass and room, and the board.
NOT_TIMBER = ("glass_outer", "glass_inner", "came", "blind", "curtain", "backing", "crawl") + BOARD_ROLES


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
    def clapboards(self, F, s0, s1, y_start, y_end, ends=("trim", "trim"), cuts=(), course0=0):
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
        R = Frame("return", F.P(W, 0, 0), (0.0, 0.0, -1.0), (1.0, 0.0, 0.0))
        y_start = self._base(F, 0.0, W, y_fd, T, ("cut", "cut"), R, W, D)
        fr = tr["frieze"]
        y_fr0 = y_s - fr["height_m"]
        cb, ct = tr["corner_board"]["width_m"], tr["corner_board"]["thickness_m"]

        # the cased windows: K06's sash in a K16 casing (one on the specimen; T-2323 a list)
        holes, cuts = [], []
        for win in v.get("windows") or [v["window"]]:
            hole, cut = self._cased_window(F, win, y_start)
            holes.append(hole)
            cuts.append(cut)

        # walls: sheathing, interior, the specimen's two cuts
        self.sheathing(F, (0.0, W, y_fd, y_s), holes)
        self.sheathing(R, (0.0, D, y_fd, y_s))
        self.sheathing(F, (0.0, W - T, y_fd, y_s), holes, role="interior", z=-T, hint_z=-1)
        self.sheathing(R, (T, D, y_fd, y_s), role="interior", z=-T, hint_z=-1)
        self.poly(F, "cut", [(0, y_fd, -T), (0, y_fd, 0), (0, y_s, 0), (0, y_s, -T)], (-1, 0, 0))
        self.poly(R, "cut", [(D, y_fd, -T), (D, y_s, -T), (D, y_s, 0), (D, y_fd, 0)], (1, 0, 0))

        # clapboard, front and return, and the corner boards between them
        self.clapboards(F, 0.0, W - cb + ct, y_start, y_fr0, ("cut", "trim"), cuts)
        self.clapboards(R, cb - ct, D, y_start, y_fr0, ("trim", "cut"))
        tc = self.tone("corner")
        self.box(F, "corner_board", W - cb + ct, W + ct, y_start, y_fr0, 0, ct, skip=("back", "top"), tone=tc)
        self.box(R, "corner_board", 0.0, cb - ct, y_start, y_fr0, 0, ct, skip=("back", "top", "s0"), tone=tc)

        # frieze, boxed eave, brackets
        ft = fr["thickness_m"]
        ev = tr["eave"]
        P_, fh = ev["projection_m"], ev["fascia_m"]
        self.mitred_run(F, R, [(0.0, y_fr0), (ft, y_fr0), (ft, y_s), (0.0, y_s)], ["frieze", "frieze", None, None],
                        0.0, W, D, ("end_grain", "end_grain"), self.tone("frieze"))
        self.mitred_run(F, R, [(0.0, y_s), (P_, y_s), (P_, y_s + fh), (0.0, y_s + fh)], ["soffit", "fascia", "roof", None],
                        0.0, W, D, ("cut", "cut"), self.tone("eave"))
        br = dict(tr["bracket"])
        sp = br["spacing_m"]
        nb = int((W - 0.8) / sp) + 1
        first = (W - (nb - 1) * sp) / 2
        for kb in range(nb):
            self.bracket(F, first + kb * sp, ft, y_s, br, br["thickness_m"], tone=self.tone("bracket", kb))
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
            cuts.append(cut)
        cb, ct = tr["corner_board"]["width_m"], tr["corner_board"]["thickness_m"]
        self.clapboards(F, cb, W - cb, y_start, y_belt, ("trim", "trim"), cuts)
        tc = self.tone("corner")
        self.box(F, "corner_board", 0.0, cb, y_start, y_belt, 0, ct, skip=("back", "top"), tone=tc)
        self.box(F, "corner_board", W - cb, W, y_start, y_belt, 0, ct, skip=("back", "top"), tone=tc)
        be = tr["belt"]
        cap = tr["water_table"]["cap"]
        y_b1 = y_belt + be["height_m"]
        y_g = y_b1 + cap["height_m"]
        zc = be["thickness_m"] + cap["projection_m"]
        self.profile_run(F, [(0.0, y_belt), (be["thickness_m"], y_belt), (be["thickness_m"], y_b1), (0.0, y_b1)],
                         ["belt", "belt", None, None], 0.0, W, ("end_grain", "end_grain"), self.tone("belt"))
        self.profile_run(F, [(0.0, y_b1), (zc, y_b1), (zc, y_g - cap["fall_m"]), (0.0, y_g)],
                         ["drip_cap", "drip_cap", "drip_cap", None], 0.0, W, ("end_grain", "end_grain"), self.tone("belt"))
        p = math.radians(go["pitch_deg"])
        tp, cp_, sp_ = math.tan(p), math.cos(p), math.sin(p)
        y_ap = y_g + (W / 2) * tp
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
        add("soffit", [(0, y_g, 0), (W / 2, y_ap, 0), (W / 2, y_ap, ov - bbt), (0, y_g, ov - bbt)], (sp_, -cp_, 0),
            self.tone("verge"))
        add("roof", [(0, y_g, back), (W / 2, y_ap, back), (W / 2, y_ap, 0), (0, y_g, 0)], (sp_, -cp_, 0))
        add("roof", [(0, y_g, back), (0, y_g, ov), (0, y_g + h_roof, ov), (0, y_g + h_roof, back)], (-1, 0, 0))
        add("roof", [(0, y_g, back), (0, y_g + h_roof, back), (W / 2, y_ap + h_roof, back), (W / 2, y_ap, back)], (0, 0, -1))

        # the pierced bargeboard, in its own (t along the rake, v down from it)
        Lr = (W / 2) / cp_

        def tv(t, vv):
            return (t * cp_ + vv * sp_, y_g + t * sp_ - vv * cp_)

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
        self.shingles(F, inner, y_g, v["bands"], W / 2)

        # the finial through the apex
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
        self.meta["gable"] = {"y_g": y_g, "y_ap": y_ap, "h_roof": h_roof, "back_m": back}   # T-2323
        self.meta.update({"wall_thickness_m": T, "pitch_deg": go["pitch_deg"],
                          "focus": [W * 0.3, y_ap - 0.9, 0.15], "span_m": 3.4})

    def _porch(self):
        v, d = self.v, self.data
        po, tr = d["porch"], d["trim"]
        F = self.F
        fl, la, pt, pl, ce = po["floor"], po["lattice"], po["post"], po["plate"], po["ceiling"]
        yf, Dp = fl["height_m"], v.get("depth_m", fl["depth_m"])   # T-2323: a house's own depth
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
        for layer, sign, zfront in ((0, 1, z0f), (1, -1, z0f - lt)):
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
        sp = Wf - a - 0.05
        tp_ = self.tone("post")
        y_b, y_h = yf + pt["base_m"], yp - pt["head_m"]
        for (y0, y1, skip) in ((yf, y_b, ("bottom", "top")), (y_h, yp, ("bottom", "top"))):
            self.box(F, "post", sp - a, sp + a, y0, y1, zp - a, zp + a, skip=skip, tone=tp_)
        octo = octagon(a, chm)
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
        # the plate, the brackets under it, the beaded ceiling, the roof over all
        self.box(F, "plate", 0.0, Wf + 0.05, yp, yc, zp - pd / 2, zp + pd / 2, skip=("top",), tone=self.tone("plate"),
                 roles={"s0": "cut", "s1": "end_grain"})
        br = dict(tr["bracket"], drop_m=pt["head_m"], reach_m=0.28)
        self.bracket(F, sp - a, zp, yp, br, br["thickness_m"], along_s=True, outward=-1.0, tone=tp_)
        self.bracket(F, sp + a, zp, yp, br, br["thickness_m"], along_s=True, outward=1.0, tone=tp_)
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
    probe = Sample(half, data).build()
    reach = max(p[0] for pr in probe.prims.values() for p in pr.pos)    # the half's roof edge
    c = Wg + join + reach
    out["porch_right"] = Sample(half, data, (c, 0.0, 0.0)).build()
    out["porch_left"] = Sample(half, data, (c, 0.0, 0.0)).build()      # mirrored when merged
    out["_porch_mirror_s"] = c
    for k in ("gable", "wing_wall", "porch_right", "porch_left"):
        out[k].seed = seed_of(out[k].v["id"], 0, sid)
    return out


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
    if bay:
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
        house.box(house.F, "skirt", a, b, 0.0, y_rim0, 0.0, zl, skip=("back", "bottom"), tone=house.tone("skirt", a))
    # merge: the porch's left half mirrored, the board roles dropped
    mirror_s(parts["porch_left"], c)
    for k in ("gable", "wing_wall", "porch_right", "porch_left"):
        sm = parts[k]
        porch = k.startswith("porch")
        for role, pr in sm.prims.items():
            if role in ("backdrop", "interior") or (porch and role == "cut"):
                continue
            dst = "stand_in" if role == "cut" else role
            absorb(house.prims.setdefault(dst, Prim(dst)), pr)
    # turn it to face its street; the origin (the front's left end, at grade) stays put
    k = {"east": 1, "south": 0}[form["layout"]["value"]["faces"]]
    for pr in house.prims.values():
        pr.pos = [_rot_y(q, k) for q in pr.pos]
        pr.nrm = [_rot_y(q, k) for q in pr.nrm]
    house.meta.update({"parts": {kk: triangles(parts[kk]) for kk in ("gable", "wing_wall", "porch_right", "porch_left")},
                       "focus": [0.0, 3.0, 0.0], "span_m": 9.0})
    return house


def structure_materials(house: Sample, data: dict, form: dict) -> dict:
    """The materials a house draws, and only those; its roof takes the record's covering."""
    mats = materials(data)
    mats["stand_in"] = dict(STAND_IN, color=tuple(form["body"]["value"].get("color", STAND_IN["color"])))
    cov = form.get("roof_covering")
    if cov and cov["value"].get("color"):
        mats["roof"] = dict(mats["roof"], color=tuple(cov["value"]["color"]), roughness=0.9)
    used = {ROLE_MATERIAL[r] for r, pr in house.prims.items() if pr.idx}
    return {k: m for k, m in mats.items() if k in used}


def structure_glb(house: Sample, data: dict, form: dict, structure_id: str, phase_id: str, scene_ids) -> bytes:
    name = f"{structure_id}__{phase_id}"
    return to_glb([house], data, node_name=name, mats=structure_materials(house, data, form), node_extras={
        "structure_id": structure_id, "phase_id": phase_id, "scene_ids": list(scene_ids),
        "parts_triangles": house.meta["parts"]},
        extras={"ticket": "T-2323", "structure": f"data/structures/{structure_id}.json"})


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
