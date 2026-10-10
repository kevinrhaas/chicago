"""The K08 bay kit: bays, oriels and towers as closed projections, written straight to glTF.

TICKET T-2307 (piece 1 of T-1850, K08). The kit's sizes are data in
`data/components/prairie_1904/k08_bays.json`; this module reads them and builds each
variant as T-2308 will put one on a Prairie Avenue 1904 house:

  plan         a polyline, a segmental bow, a circle or a regular polygon, cut by the
               host wall's outer face (z = 0) into RUNS from one junction to the other
  walls        each run's outer face, its windows' holes cut through it in a
               T-junction-free cell grid, one storey band at a time
  windows      K06 openings (generators/archetypes/k06_windows.py), each a closed
               recess; on a curved run the whole opening is bent to the curve
  plinth       on grade: a stone plinth, proud, mitred round every corner
  corbel       an oriel: stone courses each stepped out over the one below
  floor bands  a string course at every floor line between storeys
  eaves        a soffit out to a fascia
  roof         the plan's own lines offset to the eaves and lifted at one pitch: a
               hipped roof over a polygon (trimmed at its hips), a cone over a curve;
               a tower's cap is the whole ring's, closed at the back where the wall
               plane cuts it, with a finial at the apex

Everything a run carries is built FLAT, in the run's own (s, y, z) frame (s along the
run's outer face, y up, z out of it: K06's frame), then mapped onto the run: rigidly
for a straight run, bent round its centre for an arc. A bent face is first cut into
slabs no wider than the data's `max_seg_deg`, and every vertex takes the true curve's
normal, so a near view sees neither a facet nor a shading crease.

WHY PURE PYTHON: the reasons k01_frontage.py and k06_windows.py give. The gate
(tools/check_bay_kit.py) measures vertices, and they are easiest to hold when this
module writes them.

    python3 generators/archetypes/k08_bays.py           write the specimen GLB
    python3 generators/archetypes/k08_bays.py --check   refuse if it is stale
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

from archetypes import k06_windows as K6  # noqa: E402
from archetypes.k01_frontage import Prim, _add, _cross, _dot, _mul, _sub, _unit  # noqa: E402,F401

ROOT = HERE.parents[1]
DATA = ROOT / "data" / "components" / "prairie_1904" / "k08_bays.json"
GENERATOR = "chicago-4d generators/archetypes/k08_bays.py (K08, T-2307)"
RECONSTRUCTED = 1.0  # k01_frontage_params.CONFIDENCE_VALUE["reconstructed"]
Y = (0.0, 1.0, 0.0)

# Role -> material. Fixed order: the file is the same bytes every run. `roof` and
# `finial` take the variant's covering (see material_of).
ROLE_MATERIAL = {
    "wall": "masonry", "reveal": "masonry", "mullion": "masonry", "roof_back": "masonry",
    "plinth": "dressed_stone", "band": "dressed_stone", "corbel": "dressed_stone",
    "sill": "sill_stone", "head": "head_stone",
    "soffit": "trim", "fascia": "trim",
    "frame": "joinery", "sash_outer": "joinery", "sash_inner": "joinery",
    "glass_outer": "glass", "glass_inner": "glass", "came": "lead_came",
    "blind": "blind", "curtain": "curtain", "backing": "backing",
    "roof": "covering", "finial": "covering",
    "board_wall": "board", "ground": "ground",
}
# The specimen's board, not the bay: excluded from a variant's costs and its checks.
BOARD_ROLES = ("board_wall", "ground")
# A window's own parts, as K06 names them.
WINDOW_ROLES = ("reveal", "mullion", "sill", "head", "frame", "sash_outer", "sash_inner",
                "glass_outer", "glass_inner", "came", "blind", "curtain", "backing")


def load() -> dict:
    return json.loads(DATA.read_text())


def materials(data: dict) -> dict:
    """Every material the kit can bind; coverings by their K04 fabric id."""
    m6 = K6.materials(K6.load())
    out = {
        "masonry": m6["masonry"], "dressed_stone": {"color": (0.74, 0.70, 0.62), "roughness": 0.85},
        "sill_stone": m6["sill_stone"], "head_stone": m6["head_stone"],
        "trim": {"color": (0.30, 0.24, 0.19), "roughness": 0.6},
        "joinery": m6["joinery"], "glass": m6["glass"], "lead_came": m6["lead_came"],
        "blind": m6["blind"], "curtain": m6["curtain"], "backing": m6["backing"],
        "board": {"color": (0.58, 0.52, 0.44), "roughness": 0.95}, "ground": m6["ground"],
    }
    for fab, col in data["roofs"]["covering_colors"].items():
        metal = fab.startswith("copper") or fab.startswith("tin")
        out[f"covering_{fab}"] = {"color": tuple(col), "roughness": 0.45 if metal else 0.7,
                                  "metallic": 0.35 if fab.startswith("copper") else 0.0}
    return out


def material_of(role: str, v: dict) -> str:
    m = ROLE_MATERIAL[role]
    return f"covering_{v['roof']['covering']}" if m == "covering" else m


def seed_of(component_id: str, index: int = 0, structure_id: str = "k08_bay_kit") -> int:
    """K01's seed rule (k01_contract.json `seed`)."""
    return int(hashlib.sha256(f"{structure_id}|{component_id}|{index}".encode()).hexdigest()[:8], 16)


def part(v: dict, data: dict, name: str) -> dict:
    """A part's sizes, with the variant's overrides laid over the kit's."""
    out = dict(data["parts"][name])
    out.update(v.get("overrides", {}).get(name, {}))
    return out


# -- 2D helpers in plan (x, z) ----------------------------------------------------------------

def clip_half(poly, f):
    """Sutherland-Hodgman against one half-plane: keep the part where f(p) >= 0."""
    out = []
    for j, p in enumerate(poly):
        q = poly[(j + 1) % len(poly)]
        fp, fq = f(p), f(q)
        if fp >= 0:
            out.append(p)
        if (fp >= 0) != (fq >= 0):
            t = fp / (fp - fq)
            out.append(tuple(p[k] + t * (q[k] - p[k]) for k in range(len(p))))
    return out


def area(poly) -> float:
    return math.fsum(p[0] * q[1] - q[0] * p[1] for p, q in zip(poly, poly[1:] + poly[:1])) / 2


def hull(points):
    """Monotone-chain convex hull, counter-clockwise."""
    pts = sorted(set((round(p[0], 9), round(p[1], 9)) for p in points))
    if len(pts) < 3:
        return pts
    cr = lambda o, a, b: (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo, hi = [], []
    for p in pts:
        while len(lo) >= 2 and cr(lo[-2], lo[-1], p) <= 0:
            lo.pop()
        lo.append(p)
    for p in reversed(pts):
        while len(hi) >= 2 and cr(hi[-2], hi[-1], p) <= 0:
            hi.pop()
        hi.append(p)
    return lo[:-1] + hi[:-1]


# -- runs: the plan cut into pieces a strip can be built on -----------------------------------

class Run:
    """One piece of the plan. Its frame: s along the outer face from its start, y up, z out
    of the face. A line run maps rigidly; an arc run bends round its centre, clockwise seen
    from above (left junction -> front -> right junction), so phi falls as s grows."""

    def __init__(self, kind, start, end, **kw):
        self.kind, self.start, self.end = kind, start, end   # start/end: "wall" or ("corner", tau)
        if kind == "line":
            self.A, B = kw["A"], kw["B"]
            dx, dz = B[0] - self.A[0], B[1] - self.A[1]
            self.L = math.hypot(dx, dz)
            self.e = (dx / self.L, dz / self.L)
            self.n = (-self.e[1], self.e[0])          # outward
        else:
            self.c, self.R = kw["c"], kw["R"]
            self.phi0 = self.phi_wall(0.0, left=True)
            self.L = (self.phi0 - self.phi_wall(0.0, left=False)) * self.R

    # the arc's junctions: where the circle of radius R + z meets z = 0
    def phi_wall(self, z, left):
        a = math.asin(max(-1.0, min(1.0, -self.c[1] / (self.R + z))))
        return math.pi - a if left else a

    def phi(self, s):
        return self.phi0 - s / self.R

    def world(self, s, y, z):
        if self.kind == "line":
            return (self.A[0] + s * self.e[0] + z * self.n[0], y, self.A[1] + s * self.e[1] + z * self.n[1])
        f = self.phi(s)
        r = self.R + z
        return (self.c[0] + r * math.cos(f), y, self.c[1] + r * math.sin(f))

    def frame(self, s):
        """(along, out) at s, as 3D vectors."""
        if self.kind == "line":
            return (self.e[0], 0.0, self.e[1]), (self.n[0], 0.0, self.n[1])
        f = self.phi(s)
        return (math.sin(f), 0.0, -math.cos(f)), (math.cos(f), 0.0, math.sin(f))

    def s_start(self, z):
        """Where a surface z out of the face begins: on the wall plane, or mitred."""
        if self.start == "wall":
            if self.kind == "line":
                return -z * self.n[1] / self.e[1]
            return (self.phi0 - self.phi_wall(z, left=True)) * self.R
        return -z * math.tan(self.start[1] / 2)

    def s_end(self, z):
        if self.end == "wall":
            if self.kind == "line":
                return self.L - z * self.n[1] / self.e[1]
            return (self.phi0 - self.phi_wall(z, left=False)) * self.R
        return self.L + z * math.tan(self.end[1] / 2)

    def seg_step(self, max_deg):
        """The widest slab of s a bent face may span."""
        return self.R * math.radians(max_deg) if self.kind == "arc" else None


def turn(e1, e2) -> float:
    """The turning angle from direction e1 to e2, positive at a convex corner of the plan."""
    return -math.atan2(e1[0] * e2[1] - e1[1] * e2[0], e1[0] * e2[0] + e1[1] * e2[1])


def line_runs(points):
    runs = []
    n = len(points) - 1
    dirs = []
    for i in range(n):
        a, b = points[i], points[i + 1]
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        dirs.append(((b[0] - a[0]) / L, (b[1] - a[1]) / L))
    for i in range(n):
        st = "wall" if i == 0 else ("corner", turn(dirs[i - 1], dirs[i]))
        en = "wall" if i == n - 1 else ("corner", turn(dirs[i], dirs[i + 1]))
        runs.append(Run("line", st, en, A=tuple(points[i]), B=tuple(points[i + 1])))
    return runs


def polygon_vertices(sides, R, cz):
    """A regular polygon, a face square to the front; vertices by bearing, -180..180."""
    out = []
    for k in range(sides):
        b = math.radians(-180 + 180 / sides + k * 360 / sides)
        out.append((R * math.sin(b), cz + R * math.cos(b)))
    return out


def plan_of(v: dict):
    """The variant's runs, and what its roof and its bearings are measured from."""
    p = v["plan"]
    if p["kind"] == "polyline":
        pts = [tuple(q) for q in p["points"]]
        runs = line_runs(pts)
        return runs, {"centre": None, "kind": "polyline", "lines": [(r.A, r.e, r.n) for r in runs]}
    if p["kind"] == "bow":
        h, rise = p["chord_m"] / 2, p["rise_m"]
        R = (h * h + rise * rise) / (2 * rise)
        c = (0.0, rise - R)
        return [Run("arc", "wall", "wall", c=c, R=R)], {"centre": c, "kind": "arc", "R": R}
    if p["kind"] == "circle":
        R, c = p["radius_m"], (0.0, p["centre_proud_m"])
        return [Run("arc", "wall", "wall", c=c, R=R)], {"centre": c, "kind": "arc", "R": R}
    if p["kind"] == "polygon":
        n, R, cz = p["sides"], p["radius_m"], p["centre_proud_m"]
        ring = polygon_vertices(n, R, cz)
        chain = []
        # walk the ring by bearing from the left junction to the right, keeping z >= 0
        for k in range(n):
            a, b = ring[k], ring[(k + 1) % n]
            if a[1] >= 0 and (not chain or chain[-1] != a):
                chain.append(a)
            if (a[1] < 0) != (b[1] < 0):
                t = a[1] / (a[1] - b[1])
                chain.append((a[0] + t * (b[0] - a[0]), 0.0))
        # rotate so the chain starts at the left junction (the crossing with the least x)
        k0 = min((i for i, q in enumerate(chain) if abs(q[1]) < 1e-12), key=lambda i: chain[i][0])
        chain = chain[k0:] + chain[:k0]
        # a junction within a millimetre of a vertex IS that vertex: no sliver of a run
        tidy = []
        for q in chain:
            if tidy and math.dist(q, tidy[-1]) < 1e-3:
                if abs(q[1]) < 1e-12:
                    tidy[-1] = q
                continue
            tidy.append(q)
        chain = tidy
        lines = []
        for k in range(n):
            a, b = ring[k], ring[(k + 1) % n]
            L = math.hypot(b[0] - a[0], b[1] - a[1])
            e = ((b[0] - a[0]) / L, (b[1] - a[1]) / L)
            lines.append((a, e, (-e[1], e[0])))
        return line_runs(chain), {"centre": (0.0, cz), "kind": "polygon", "lines": lines, "ring": ring}
    raise ValueError(f"unknown plan kind {p['kind']}")


def locate(runs, plan, w: dict):
    """Where each of a window entry's positions falls: (run index, s of its centre)."""
    total = math.fsum(r.L for r in runs)
    out = []
    if "at" in w:
        for f in w["at"]:
            s = f * total
            for i, r in enumerate(runs):
                if s <= r.L + 1e-9 or i == len(runs) - 1:
                    out.append((i, s))
                    break
                s -= r.L
        return out
    c = plan["centre"]
    for b in w["at_deg"]:
        d = (math.sin(math.radians(b)), math.cos(math.radians(b)))
        for i, r in enumerate(runs):
            if r.kind == "arc":
                out.append((i, (r.phi0 - math.atan2(d[1], d[0])) * r.R))
                break
            # the ray from the centre: c + t d meets A + s e
            den = d[0] * r.e[1] - d[1] * r.e[0]
            if abs(den) < 1e-12:
                continue
            ax, az = r.A[0] - c[0], r.A[1] - c[1]
            s = (ax * d[1] - az * d[0]) / den
            t = (ax * r.e[1] - az * r.e[0]) / den
            if t > 0 and -1e-9 <= s <= r.L + 1e-9:
                out.append((i, s))
                break
        else:
            raise ValueError(f"{w['opening']}: bearing {b} meets no run")
    return out


# -- the strip: a run's faces, built flat --------------------------------------------------------

def strip(name: str) -> K6.Opening:
    """A face container in a run's flat frame: K06's own, so its faces are built as K06's are."""
    return K6.Opening({"id": name}, K6.load())


def merge(dst: dict, src: dict, drop=()):
    for role, pr in src.items():
        if role in drop or not pr.idx:
            continue
        d = dst.setdefault(role, Prim(role))
        base = len(d.pos)
        d.pos += pr.pos
        d.nrm += pr.nrm
        d.uv += pr.uv
        d.conf += pr.conf
        d.tone += pr.tone
        d.idx += [base + i for i in pr.idx]


def add_poly(pr: Prim, pts, nrms, uvs):
    base = len(pr.pos)
    for p, n, uv in zip(pts, nrms, uvs):
        pr.pos.append(p)
        pr.nrm.append(n)
        pr.uv.append(uv)
        pr.conf.append(RECONSTRUCTED)
        pr.tone.append(1.0)
    for i in range(1, len(pts) - 1):
        pr.idx += [base, base + i, base + i + 1]


def bend(run: Run, flat: dict, out: dict, step):
    """Map a strip's faces onto the run. On an arc, each face is cut into slabs of s first,
    and every vertex takes the curve's own frame, so its normal is the true one."""
    # where the outer face has an edge (a jamb, a band's end): a face meeting the outer face
    # is cut there too, so two faces that share the face's curve share its chords exactly
    edges = sorted({round(p[0], 9) for pr in flat.values() for p in pr.pos if abs(p[2]) < 1e-9}) if step else []
    for role, pr in flat.items():
        dst = out.setdefault(role, Prim(role))
        for t in range(0, len(pr.idx), 3):
            ids = pr.idx[t:t + 3]
            poly = [(*pr.pos[i], *pr.nrm[i], *pr.uv[i]) for i in ids]
            pieces = [poly]
            if step:
                s_lo = min(q[0] for q in poly)
                s_hi = max(q[0] for q in poly)
                k0, k1 = math.floor(s_lo / step + 1e-9), math.ceil(s_hi / step - 1e-9)
                cuts = [k * step for k in range(k0 + 1, k1)]
                if any(abs(q[2]) < 1e-9 for q in poly):
                    cuts += [e for e in edges if s_lo + 1e-7 < e < s_hi - 1e-7]
                cuts = sorted(c for c in cuts if s_lo + 1e-7 < c < s_hi - 1e-7)
                if cuts:
                    pieces = []
                    for a, b in zip([s_lo] + cuts, cuts + [s_hi]):
                        piece = clip_half(clip_half(poly, lambda q: q[0] - a), lambda q: b - q[0])
                        if len(piece) >= 3:
                            pieces.append(piece)
            for piece in pieces:
                # the wall plane trims the bay: nothing of it stands behind the host wall's face
                piece = clip_half(piece, lambda q: run.world(q[0], q[1], q[2])[2] + 1e-9)
                if len(piece) < 3:
                    continue
                pts, nrms, uvs = [], [], []
                for q in piece:
                    s, y, z = q[0], q[1], q[2]
                    al, ou = run.frame(s)
                    p = run.world(s, y, z)
                    if -0.01 < p[2] < 0.0:     # a mitre's end bent onto the curve: onto the wall plane
                        p = (p[0], p[1], 0.0)
                    pts.append(p)
                    nrms.append(_unit((q[3] * al[0] + q[5] * ou[0], q[4], q[3] * al[2] + q[5] * ou[2])))
                    uvs.append((q[6], q[7]))
                n = (0.0, 0.0, 0.0)
                for j in range(1, len(pts) - 1):
                    n = _add(n, _cross(_sub(pts[j], pts[0]), _sub(pts[j + 1], pts[0])))
                if _dot(n, n) > 4e-14:      # a sliver the wall plane left: nothing to draw
                    add_poly(dst, pts, nrms, uvs)


def wall_cells(o: K6.Opening, role, holes, s_lo, s_hi, y_lo, y_hi, d=0.0, hint=(0.0, 0.0, 1.0)):
    """A wall band around its holes, a T-junction-free cell grid (K06's wall_panel, cut to
    a band). A hole: (s0, s1, bottom, spring, top chain right -> left, flat?)."""
    xb, yb = {s_lo, s_hi}, {y_lo, y_hi}
    for s0, s1, yb0, sp, _top, _flat in holes:
        xb |= {s0, s1}
        yb |= {yb0, sp}
    xb, yb = sorted(xb), sorted(yb)
    for i in range(len(xb) - 1):
        for j in range(len(yb) - 1):
            sc, yc = (xb[i] + xb[i + 1]) / 2, (yb[j] + yb[j + 1]) / 2
            if any(s0 < sc < s1 and yb0 < yc < sp for s0, s1, yb0, sp, _t, _f in holes):
                continue
            if any(s0 < sc < s1 and yc > sp and not fl for s0, s1, _y, sp, _t, fl in holes):
                continue      # over an arch: the curve strips below fill it
            o.plane(role, K6.box(xb[i], xb[i + 1], yb[j], yb[j + 1]), d, hint)
    for s0, s1, _y, sp, top, fl in holes:
        if fl:
            continue
        for k in range(len(top) - 1):
            p, q = top[k], top[k + 1]
            o.plane(role, [(q[0], q[1]), (p[0], p[1]), (p[0], y_hi), (q[0], y_hi)], d, hint)


def ledge(o, role, run, y, z0, z1, hint):
    """A horizontal face between two offsets of the run, mitred at its ends."""
    o.face(role, [o.P(run.s_start(z0), y, -z0), o.P(run.s_end(z0), y, -z0),
                  o.P(run.s_end(z1), y, -z1), o.P(run.s_start(z1), y, -z1)], hint)


def proud(o, role, run, y0, y1, out, top=True, bottom=True):
    """A slab standing `out` proud of the run's face from y0 to y1: front and ledges."""
    o.plane(role, K6.box(run.s_start(out), run.s_end(out), y0, y1), -out)
    if top:
        ledge(o, role, run, y1, 0.0, out, Y)
    if bottom:
        ledge(o, role, run, y0, 0.0, out, (0.0, -1.0, 0.0))


# -- a window: a K06 opening, its recess cut to the bay ------------------------------------------

def k06_variant(w: dict) -> dict:
    data6 = K6.load()
    v6 = copy.deepcopy(next(x for x in data6["variants"] if x["id"] == w["opening"]))
    for k in ("clear_width_m", "clear_height_m"):
        if k in w:
            v6[k] = w[k]
    return v6


def window(w: dict, s: float, y_sill: float, recess: float):
    """The K06 opening for one window entry, its sill socket at (s, y_sill) on the face, its
    room cut so the recess runs `recess` behind the face: (opening, daylight hole)."""
    data6 = copy.deepcopy(K6.load())
    v6 = k06_variant(w)
    probe = K6.Opening(v6, data6).build()
    inner_glass = probe.meta["depth_backing_m"] - data6["parts"]["backing"]["depth_m"]
    data6["parts"]["backing"]["depth_m"] = recess - inner_glass
    o = K6.Opening(v6, data6, origin=(s, y_sill, 0.0)).build()
    return o


# -- the bay ----------------------------------------------------------------------------------------

class Bay:
    def __init__(self, v: dict, data: dict, tier: str = "full"):
        self.v, self.data, self.tier = v, data, tier
        self.prims: dict[str, Prim] = {}
        self.meta: dict = {}
        self.windows: list[dict] = []
        self.seed = seed_of(v["id"], 0 if tier == "full" else 1)
        self.runs, self.plan = plan_of(v)

    def build(self, board: bool = True):
        v, data = self.v, self.data
        cv = data["curves"][self.tier]
        wall_t = part(v, data, "wall")["thickness_m"]
        recess = part(v, data, "recess")["depth_m"]
        plinth, band, eaves = part(v, data, "plinth"), part(v, data, "floor_band"), part(v, data, "eaves")
        grade = v["base"] == "grade"
        y0 = 0.0 if grade else float(v["base"])
        levels = [y0]
        for st in v["storeys"]:
            levels.append(levels[-1] + st["height_m"])
        y_top = levels[-1]
        ov, fh = eaves["overhang_m"], eaves["fascia_m"]
        y_e = y_top + fh
        self.meta.update({"base_m": y0, "levels_m": [round(y, 4) for y in levels], "wall_top_m": round(y_top, 4),
                          "eave_m": round(y_e, 4), "wall_thickness_m": wall_t, "recess_m": recess,
                          "overhang_m": ov, "max_seg_deg": cv["max_seg_deg"]})
        # windows, by run and storey
        per_run = {i: {k: [] for k in range(len(v["storeys"]))} for i in range(len(self.runs))}
        for k, st in enumerate(v["storeys"]):
            for w in st["windows"]:
                for i, s in locate(self.runs, self.plan, w):
                    per_run[i][k].append((w, s))
        y_wall0 = plinth["height_m"] if grade else y0
        for i, run in enumerate(self.runs):
            flat = strip(f"{v['id']}|run{i}")
            for k in range(len(v["storeys"])):
                holes = []
                lo = y_wall0 if k == 0 else levels[k]
                hi = levels[k + 1]
                for w, s in per_run[i][k]:
                    o = window(w, s, levels[k] + w["sill_m"], w.get("recess_m", recess))
                    for h in o.holes:
                        sh = [(q[0] + s, q[1] + o.O[1]) for q in h]
                        holes.append((sh[0][0], sh[1][0], sh[0][1], sh[2][1], sh[2:], len(sh) == 4))
                    drop = cv.get("drop_roles", ()) if self.tier == "light" else ()
                    merge(flat.prims, o.prims, drop)
                    self.windows.append(self._window_record(run, i, k, w, s, o, wall_t))
                wall_cells(flat, "wall", holes, 0.0, run.L, lo, hi)
                if 0 < k:
                    yb = levels[k]
                    proud(flat, "band", run, yb - band["height_m"] / 2, yb + band["height_m"] / 2, band["proud_m"])
            if grade:
                proud(flat, "plinth", run, 0.0, plinth["height_m"], plinth["proud_m"], bottom=False)
            # the eaves: a soffit out to the fascia, the fascia's top the roof's eaves line
            ledge(flat, "soffit", run, y_top, 0.0, ov, (0.0, -1.0, 0.0))
            flat.plane("fascia", K6.box(run.s_start(ov), run.s_end(ov), y_top, y_e), -ov)
            if not grade:
                self._corbel_courses(flat, run, y0)
            bend(run, flat.prims, self.prims, run.seg_step(cv["max_seg_deg"]))
        world = strip(f"{v['id']}|world")
        if not grade:
            self._corbel_bottom(world, y0, cv)
        self._roof(world, y_e, ov, cv)
        merge(self.prims, world.prims)
        self._sockets(y0, y_e)
        if board:
            self._board(y_e)
        return self

    # windows ---------------------------------------------------------------------------
    def _window_record(self, run, i, k, w, s, o, wall_t):
        """What the gate needs of a window once it is bent: where its panes are and which
        way they face, and the plan its recess occupies."""
        y_sill = o.O[1]
        panes = []
        for p in o.panes:
            cs = math.fsum(q[0] for q in p["poly"]) / len(p["poly"]) + s
            cy = math.fsum(q[1] for q in p["poly"]) / len(p["poly"]) + y_sill
            al, ou = run.frame(cs)
            panes.append({"at": run.world(cs, cy, -p["depth_m"]), "out": ou, "along": al})
        bk = o.prims["backing"].pos
        s_lo, s_hi = min(q[0] for q in bk), max(q[0] for q in bk)
        z_lo = min(q[2] for q in bk)
        step = run.seg_step(3.75) or (s_hi - s_lo)
        n = max(1, math.ceil((s_hi - s_lo) / step))
        foot = [run.world(s_lo + (s_hi - s_lo) * j / n, 0.0, z)[0::2] for j in range(n + 1) for z in (0.0, z_lo)]
        allp = [q for pr in o.prims.values() for q in pr.pos]
        return {"opening": w["opening"], "run": i, "storey": k, "s": round(s, 4),
                "s_extent": [round(min(q[0] for q in allp), 4), round(max(q[0] for q in allp), 4)],
                "y_all": [round(min(q[1] for q in allp), 4), round(max(q[1] for q in allp), 4)],
                "y": [round(min(q[1] for q in bk), 4), round(max(q[1] for q in bk), 4)],
                "recess_m": round(-z_lo, 4), "footprint": hull(foot), "panes": panes,
                "why_not_ordinary": w.get("why_not_ordinary")}

    # supports ----------------------------------------------------------------------------
    def _corbel_layout(self, y0):
        v, data = self.v, self.data
        cb = part(v, data, "corbel")
        K = v["corbel"]["courses"]
        reach = max(r.world(s, 0, 0)[2] for r in self.runs for s in (0.0, r.L))
        step = reach / (K + 1)
        h = cb["course_height_m"]
        return K, step, h, reach

    def _corbel_courses(self, flat, run, y0):
        K, step, h, _reach = self._corbel_layout(y0)
        for k in range(K):
            zk, zp = -(k + 1) * step, -k * step
            ytop, ybot = y0 - k * h, y0 - (k + 1) * h
            flat.plane("corbel", K6.box(run.s_start(zk), run.s_end(zk), ybot, ytop), -zk)
            ledge(flat, "corbel", run, ytop, zp, zk, (0.0, -1.0, 0.0))

    def _corbel_bottom(self, world, y0, cv):
        K, step, h, reach = self._corbel_layout(y0)
        z = -K * step
        y = y0 - K * h
        pts = []
        for r in self.runs:
            a, b = r.s_start(z), r.s_end(z)
            st = r.seg_step(cv["max_seg_deg"])
            n = max(1, math.ceil((b - a) / st)) if st else 1
            for j in range(n + (1 if r is self.runs[-1] else 0)):
                pts.append(r.world(a + (b - a) * j / n, y, z))
        world.face("corbel", pts, (0.0, -1.0, 0.0))
        self.meta["corbel"] = {"courses": K, "course_height_m": h, "step_m": round(step, 4),
                               "reach_m": round(reach, 4), "bearing_m": round(reach - K * step, 4),
                               "bottom_m": round(y, 4)}

    # roof -----------------------------------------------------------------------------------
    def _roof(self, world, y_e, ov, cv):
        rf = self.v["roof"]
        tower = self.v["kind"] == "tower"
        if self.plan["kind"] == "arc":
            self._cone(world, y_e, ov, rf["pitch"], cv, tower)
        else:
            self._hip(world, y_e, ov, rf["pitch"], tower)
        if rf.get("finial"):
            self._finial(world)

    def _hip(self, world, y_e, ov, pitch, tower):
        """The plan's lines offset to the eaves and lifted at one pitch; each plane keeps the
        part of the plan where it is the lowest, so the planes meet on their hips."""
        lines = [((a[0] + ov * n[0], a[1] + ov * n[1]), (-n[0], -n[1])) for a, e, n in self.plan["lines"]]
        if tower:
            ring = self.plan["ring"]
            k = len(ring)
            R = math.hypot(ring[0][0] - self.plan["centre"][0], ring[0][1] - self.plan["centre"][1])
            Re = R + ov / math.cos(math.pi / k)
            c = self.plan["centre"]
            dom = [(c[0] + (q[0] - c[0]) * Re / R, c[1] + (q[1] - c[1]) * Re / R) for q in ring]
            dom = clip_half(dom, lambda p: p[1])
        else:
            dom = [self._offset_corner(None, lines[0], ov)]
            for i in range(len(lines) - 1):
                dom.append(self._offset_corner(lines[i], lines[i + 1], ov))
            dom.append(self._offset_corner(lines[-1], None, ov))
        if area(dom) < 0:
            dom.reverse()
        d = lambda L, p: L[1][0] * (p[0] - L[0][0]) + L[1][1] * (p[1] - L[0][1])
        faces = []
        if pitch == 0:
            faces.append((dom, lambda p: y_e))
        else:
            for i, Li in enumerate(lines):
                reg = dom
                for j, Lj in enumerate(lines):
                    if j != i and reg:
                        reg = clip_half(reg, lambda p, Lj=Lj: d(Lj, p) - d(Li, p))
                if len(reg) >= 3 and abs(area(reg)) > 1e-8:
                    faces.append((reg, lambda p, Li=Li: y_e + pitch * d(Li, p)))
        apex = (0.0, y_e, 0.0)
        for reg, hgt in faces:
            pts = [(p[0], hgt(p), p[1]) for p in reg]
            world.face("roof", pts, Y)
            for q in pts:
                if q[1] > apex[1]:
                    apex = q
            if tower:
                for a, b in zip(reg, reg[1:] + reg[:1]):
                    if abs(a[1]) < 1e-9 and abs(b[1]) < 1e-9:
                        world.face("roof_back", [(a[0], y_e, 0.0), (b[0], y_e, 0.0), (b[0], hgt(b), 0.0),
                                                 (a[0], hgt(a), 0.0)], (0.0, 0.0, -1.0))
        self.meta["roof"] = {"kind": "flat" if pitch == 0 else "hip", "pitch": pitch, "planes": len(faces),
                             "apex": [round(c, 4) for c in apex]}

    @staticmethod
    def _offset_corner(L1, L2, ov):
        """Where two eaves lines meet; a line with no neighbour meets the wall plane z = 0."""
        if L1 is None or L2 is None:
            (a, n) = L2 if L1 is None else L1
            e = (n[1], -n[0])
            t = -a[1] / e[1]
            return (a[0] + t * e[0], 0.0)
        (a1, n1), (a2, n2) = L1, L2
        e1, e2 = (n1[1], -n1[0]), (n2[1], -n2[0])
        den = e1[0] * e2[1] - e1[1] * e2[0]
        t = ((a2[0] - a1[0]) * e2[1] - (a2[1] - a1[1]) * e2[0]) / den
        return (a1[0] + t * e1[0], a1[1] + t * e1[1])

    def _cone(self, world, y_e, ov, pitch, cv, tower):
        """A cone on the plan's circle offset to the eaves, cut by the wall plane: a bow's
        leans on the wall, a tower's is whole and closed at the back where the wall cuts it."""
        c, R = self.plan["centre"], self.plan["R"]
        Re = R + ov
        step = math.radians(cv["max_seg_deg"])
        cz = c[1]
        cross = []
        if abs(cz) < Re:
            a = math.asin(-cz / Re)
            cross = [a, math.pi - a]
        if tower:
            phis = sorted(set([2 * math.pi * j / math.ceil(2 * math.pi / step) for j in range(math.ceil(2 * math.pi / step))]
                              + [(q + 2 * math.pi) % (2 * math.pi) for q in cross]))
            phis.append(phis[0] + 2 * math.pi)
        else:
            lo, hi = cross[0], cross[1]
            n = math.ceil((hi - lo) / step)
            phis = [lo + (hi - lo) * j / n for j in range(n + 1)]

        def span(f):
            s = math.sin(f)
            if cz >= 0:
                r_hi = Re if s >= 0 else min(Re, cz / -s)
                return 0.0, r_hi
            r_lo = -cz / s if s > 1e-12 else Re
            return min(r_lo, Re), Re

        def P(f, r):
            return (c[0] + r * math.cos(f), y_e + pitch * (Re - r), cz + r * math.sin(f))

        def N(f):
            return _unit((pitch * math.cos(f), 1.0, pitch * math.sin(f)))

        pr = world.prims.setdefault("roof", Prim("roof"))
        apex_y = y_e + pitch * Re if tower else max(P(f, span(f)[0])[1] for f in phis)
        for f0, f1 in zip(phis, phis[1:]):
            (l0, h0), (l1, h1) = span(f0), span(f1)
            if h0 - l0 < 1e-9 and h1 - l1 < 1e-9:
                continue
            fm = (f0 + f1) / 2
            q = [P(f0, l0), P(f1, l1), P(f1, h1), P(f0, h0)]
            n = [N(f0) if l0 > 0 else N(fm), N(f1) if l1 > 0 else N(fm), N(f1), N(f0)]
            uv = [(p[0], p[2]) for p in q]
            if l0 == 0 and l1 == 0:
                add_poly(pr, [q[0], q[3], q[2]][::-1], [n[0], n[3], n[2]][::-1], [uv[0], uv[3], uv[2]][::-1])
            else:
                add_poly(pr, q[::-1], n[::-1], uv[::-1])
            if tower and h0 < Re - 1e-9 and h1 < Re - 1e-9:
                a, b = P(f0, h0), P(f1, h1)
                world.face("roof_back", [(a[0], y_e, 0.0), (b[0], y_e, 0.0), (b[0], b[1], 0.0), (a[0], a[1], 0.0)],
                           (0.0, 0.0, -1.0))
        self.meta["roof"] = {"kind": "cone", "pitch": pitch, "eave_radius_m": round(Re, 4), "segments": len(phis) - 1,
                             "apex": [round(c[0], 4), round(apex_y, 4), round(cz, 4)] if tower else None}

    def _finial(self, world):
        ax, ay, az = self.meta["roof"]["apex"]
        f = part(self.v, self.data, "finial")
        r0, H = f["radius_m"], f["height_m"]
        k = 8
        ring = lambda r, y: [(ax + r * math.cos(2 * math.pi * j / k), y, az + r * math.sin(2 * math.pi * j / k))
                             for j in range(k)]
        lo, hi = ring(r0, ay - 0.15), ring(r0 * 0.35, ay + H)
        for j in range(k):
            jj = (j + 1) % k
            m = (math.cos(2 * math.pi * (j + 0.5) / k), 0.0, math.sin(2 * math.pi * (j + 0.5) / k))
            world.face("finial", [lo[j], lo[jj], hi[jj], hi[j]], m)
        world.face("finial", hi, Y)
        self.meta["finial"] = {"top_m": round(ay + H, 4)}

    # sockets and the specimen's board --------------------------------------------------------
    def _sockets(self, y0, y_e):
        first, last = self.runs[0], self.runs[-1]
        jl, jr = first.world(0.0, y0, 0.0), last.world(last.L, y0, 0.0)
        reach = max(r.world(s, 0, 0)[2] for r in self.runs for s in [r.L * j / 16 for j in range(17)])
        self.meta["sockets"] = {"junction_left": [round(c, 4) for c in jl], "junction_right": [round(c, 4) for c in jr],
                                "base": [0.0, round(y0, 4), 0.0], "eave": [0.0, round(y_e, 4), 0.0]}
        self.meta["plan"] = {"runs": [{"kind": r.kind, "length_m": round(r.L, 4),
                                       "start": r.start if r.start == "wall" else ["corner", round(math.degrees(r.start[1]), 3)],
                                       "end": r.end if r.end == "wall" else ["corner", round(math.degrees(r.end[1]), 3)]}
                                      for r in self.runs],
                             "width_at_wall_m": round(jr[0] - jl[0], 4), "projection_m": round(reach, 4)}

    def _board(self, y_e):
        """The host wall the bay is keyed to, its top and returns, and grade in front."""
        xs = [p[0] for pr in self.prims.values() for p in pr.pos]
        x0, x1 = min(xs) - 1.0, max(xs) + 1.0
        roof_y = max(p[1] for p in self.prims["roof"].pos if abs(p[2]) < 1e-6) if self.prims.get("roof") else y_e
        top = y_e if self.v["kind"] == "tower" else roof_y + 0.6
        D = 0.45
        b = strip(f"{self.v['id']}|board")
        b.face("board_wall", [(x0, 0.0, 0.0), (x1, 0.0, 0.0), (x1, top, 0.0), (x0, top, 0.0)], (0.0, 0.0, 1.0))
        b.face("board_wall", [(x0, top, 0.0), (x1, top, 0.0), (x1, top, -D), (x0, top, -D)], Y)
        for x, hx in ((x0, -1.0), (x1, 1.0)):
            b.face("board_wall", [(x, 0.0, 0.0), (x, top, 0.0), (x, top, -D), (x, 0.0, -D)], (hx, 0.0, 0.0))
        b.face("board_wall", [(x0, 0.0, -D), (x1, 0.0, -D), (x1, top, -D), (x0, top, -D)], (0.0, 0.0, -1.0))
        G = max(p[2] for pr in self.prims.values() for p in pr.pos) + 1.5
        b.face("ground", [(x0, 0.0, 0.0), (x1, 0.0, 0.0), (x1, 0.0, G), (x0, 0.0, G)], Y)
        merge(self.prims, b.prims)
        self.meta["board"] = {"x": [round(x0, 4), round(x1, 4)], "top_m": round(top, 4), "ground_to_m": round(G, 4)}


def build_variant(v: dict, data: dict | None = None, tier: str = "full", board: bool = True) -> Bay:
    return Bay(v, data or load(), tier).build(board)


def triangles(b: Bay, include_board: bool = False) -> int:
    return sum(len(p.idx) // 3 for r, p in b.prims.items() if include_board or r not in BOARD_ROLES)


PANEL_GAP = 1.2


def build_kit(data: dict | None = None):
    """Every variant at both tiers, laid out along +X: the full tier, then the light."""
    data = data or load()
    out, x = [], 0.0
    for tier in ("full", "light"):
        for v in data["variants"]:
            b = build_variant(v, data, tier)
            x0, x1 = b.meta["board"]["x"]
            b.offset = (round(x - x0, 4), 0.0, 0.0)
            out.append(b)
            x += (x1 - x0) + PANEL_GAP
    return out


# -- glTF ---------------------------------------------------------------------------------------------

def _pad(b: bytes, fill: bytes = b"\x00") -> bytes:
    return b + fill * ((4 - len(b) % 4) % 4)


def to_glb(kit, data: dict) -> bytes:
    mats = materials(data)
    mat_names = list(mats)
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

    materials_out = []
    for name in mat_names:
        m = mats[name]
        alpha = m.get("alpha", 1.0)
        entry = {"name": f"k08_{name}", "pbrMetallicRoughness": {
            "baseColorFactor": [*[round(c, 4) for c in m["color"]], alpha],
            "metallicFactor": m.get("metallic", 0.0), "roughnessFactor": m["roughness"]}}
        if alpha < 1.0:
            entry["alphaMode"] = "BLEND"
        materials_out.append(entry)
    for b in kit:
        by_mat: dict[str, list[Prim]] = {}
        for role in ROLE_MATERIAL:   # fixed order
            if role in b.prims and b.prims[role].idx:
                by_mat.setdefault(material_of(role, b.v), []).append(b.prims[role])
        prims_out = []
        for name in mat_names:
            if name not in by_mat:
                continue
            # welded: a vertex two faces share (same place, normal, UV) is written once
            pos, nrm, uv, conf, idx, seen = [], [], [], [], [], {}
            for pr in by_mat[name]:
                for i in pr.idx:
                    key = (tuple(round(c, 5) for c in pr.pos[i]), tuple(round(c, 5) for c in pr.nrm[i]),
                           tuple(round(c, 5) for c in pr.uv[i]), pr.conf[i])
                    if key not in seen:
                        seen[key] = len(pos)
                        pos.append(key[0])
                        nrm.append(key[1])
                        uv.append(key[2])
                        conf.append(key[3])
                    idx.append(seen[key])
            ctype = 5123 if len(pos) < 65536 else 5125
            prims_out.append({"attributes": {
                "POSITION": accessor(pos, 5126, "VEC3", 3, 34962, True),
                "NORMAL": accessor(nrm, 5126, "VEC3", 3, 34962),
                "TEXCOORD_0": accessor(uv, 5126, "VEC2", 2, 34962),
                "_CONFIDENCE": accessor(conf, 5126, "SCALAR", 1, 34962)},
                "indices": accessor(idx, ctype, "SCALAR", 1, 34963),
                "material": mat_names.index(name)})
        name = f"{b.v['id']}.{b.tier}"
        meshes.append({"name": name, "primitives": prims_out})
        nodes.append({"name": name, "mesh": len(meshes) - 1, "translation": list(b.offset), "extras": {
            "component_id": b.v["id"], "family": b.v["kind"], "tier": b.tier, "seed": b.seed,
            "triangles": triangles(b), "triangles_with_board": triangles(b, True),
            "windows": len(b.windows),
            "sockets": b.meta["sockets"], "plan": b.meta["plan"],
            "measured": {k: b.meta[k] for k in ("levels_m", "eave_m", "wall_thickness_m", "recess_m", "roof",
                                                "max_seg_deg") if k in b.meta}}})
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
        "extras": {"k08": {"data": "data/components/prairie_1904/k08_bays.json", "ticket": "T-2307",
                           "windows": "data/components/prairie_1904/k06_windows.json",
                           "contract": "data/components/prairie_1904/k01_contract.json"}},
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
                  f"{DATA.relative_to(ROOT)}: run python3 generators/archetypes/k08_bays.py")
            return 1
        print(f"ok   {out.relative_to(ROOT)} is the generator's bytes ({len(blob)} B)")
        return 0
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(blob)
    print(f"wrote {out.relative_to(ROOT)} ({len(blob)} B)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
