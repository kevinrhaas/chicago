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
  apron        (T-2883) or an oriel's apron in their place: its plan carried straight down
               as a flat face to a moulded foot proud of it, closed under the foot back
               to the wall (1625's oriel, from its print), in its own `apron` role (T-2904)
  floor bands  a string course at every floor line between storeys
  eaves        a soffit out to a fascia, or (T-2460) a moulded section the variant's
               eaves name as a `profile` (in the role they name, T-2472; a band's stone
               by default), swept and mitred as the soffit is; on a variant naming `brackets` (T-2408), a
               console under the soffit at every corner of the plan and a row of
               modillions along each run
  roof         the plan's own lines offset to the eaves and lifted at one pitch: a
               hipped roof over a polygon (trimmed at its hips), a cone over a curve;
               a tower's cap is the whole ring's, closed at the back where the wall
               plane cuts it, with a finial at the apex; a bay's hip may FLARE (T-2408):
               flat at the eaves and steepening inward, cut into bands at one
               distance in from the eaves on every plane, so the hips stay shared
  balcony      (T-2525) a bow's iron balcony rail on its eaves, round the plan from wall to
               wall: a post at each end against the wall, square bars between a foot rail
               and a top rail (T-2780: or a stone balustrade round a canted bay's flat top; T-2888: or
               an iron rail round a projection's flat top); and a window entry's `grille`, iron bars in its reveal
               clipped to its head, with an arch ring over them as 1621's drawing draws
  heads        (T-2531) a window entry's `voussoirs`: a block of splayed stones over the
               light from its head to the string course, their joints fanned, as 1621's
               drawing draws over its basement lights
  floor balcony (T-2534) a projection's balcony on one of its floors, bowed out from its
               front under the window it serves: a stone slab and a stone balustrade on it
  frieze       (T-2778) a windowless storey's carved frieze: on every run a dressed panel
               proud of the face between plain stiles, and on it a guilloche, a chain of
               interlaced rings standing proud in turn (the light tier keeps the panel)
  spire        (T-2778) a roof whose every plane runs from its eaves line up to one apex on
               the wall plane over the plan's middle, a polygonal cone; and an oriel carried
               up through its house's eave (`back_from_m`) closes its back on the wall plane
               from that height to the apex, since no wall stands behind it there
  gable        (T-2998) a projection's coped stone gable: its front carried up between two
               kneelers over its corners, a slope from each to a ridge on its middle run back
               to the wall, a stone coping along each rake, and a pinnacle on each kneeler
               and a finial on the apex when the roof names them
  gable panel  (T-3002) a carved panel filling a gable's tympanum (1801's south pavilion): a
               dressed panel `proud_m` out, `border_m` in from the copings' beds and stood
               `base_m` over the wall top, and on it a tall leafy relief, a stem up its middle
               with pairs of leaves leaning out from it, each as long as the panel allows, under
               a fleuron near the apex and over a boss at the foot (the light tier keeps the panel)
  head frieze  (T-3002) a dressed band across one run over a storey's windows, under the wall
               top, with a roundel on it (1801's south pavilion under its gable's shelf)
  stage        (T-1890) a tower's corbelled upper stage (1801's, in the Taylor print and HABS
               photograph 2): from one of its storey lines up, its ring is `radius_m` across
               where the shaft's below is the plan's, carried out over the shaft on `corbel_courses`
               stepped stone courses, and its eaves and cone are the stage's; the shaft is
               capped under it, with no eaves or roof of its own
  shallow      (T-3047) a full-height projection too thin for its windows' recesses or its
               gable's copings (1801's south pavilion, 0.1 m proud on its 1911 sheet): the
               recesses run back through the wall plane (`host_holes`, which its host opens
               its face round), and the gable is a solid parapet carried back past the plane
  chamfer      (T-3048) a shallow projection flush with its wall's corner may cut that corner:
               its last run cants from the front's corner back to the SIDE wall's plane behind
               the wall's face (a `side` junction, mitred and trimmed on that plane, not the
               face's), the gable on the shortened front and its kneeler over the chamfer's
               head; its host cuts its own corner under it (k01_frontage_params.chamfer_spans)

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

import bisect
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
ROUND_APRON_STEPS = 8   # T-3007: a round apron's quarter round, in facets of 11.25 degrees
Y = (0.0, 1.0, 0.0)

# Role -> material. Fixed order: the file is the same bytes every run. `roof` and
# `finial` take the variant's covering (see material_of).
ROLE_MATERIAL = {
    "wall": "masonry", "masonry_relief": "masonry", "reveal": "masonry", "mullion": "masonry", "roof_back": "masonry",
    "plinth": "dressed_stone", "band": "dressed_stone", "corbel": "dressed_stone",
    "carving": "dressed_stone",   # T-2931: the carved relief on a pilaster's shaft
    "apron": "dressed_stone",   # T-2904: its own role, so a host may lay it in a stone of its own
    "sill": "sill_stone", "head": "head_stone",
    "soffit": "trim", "fascia": "trim", "bracket": "trim",
    "frame": "joinery", "sash_outer": "joinery", "sash_inner": "joinery",
    "glass_outer": "glass", "glass_inner": "glass", "came": "lead_came",
    "blind": "blind", "curtain": "curtain", "backing": "backing",
    "roof": "covering", "finial": "covering", "iron": "iron",
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
        "iron": {"color": (0.055, 0.055, 0.06), "roughness": 0.55},   # T-2525: K01's iron
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
        """Where a surface z out of the face begins: on the wall plane, or mitred (T-3048: or,
        a chamfer's, on its side wall's plane, square to the wall's)."""
        if self.start == "side":
            return -z * self.n[0] / self.e[0]
        if self.start == "wall":
            if self.kind == "line":
                return -z * self.n[1] / self.e[1]
            return (self.phi0 - self.phi_wall(z, left=True)) * self.R
        return -z * math.tan(self.start[1] / 2)

    def s_end(self, z):
        if self.end == "side":
            return self.L - z * self.n[0] / self.e[0]
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


def line_runs(points, side=None):
    """T-3048: `side` ("left" or "right") ends that run on its side wall's plane, behind the
    wall's face (a chamfered corner's), in place of the wall's face."""
    runs = []
    n = len(points) - 1
    dirs = []
    for i in range(n):
        a, b = points[i], points[i + 1]
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        dirs.append(((b[0] - a[0]) / L, (b[1] - a[1]) / L))
    for i in range(n):
        st = ("side" if side == "left" else "wall") if i == 0 else ("corner", turn(dirs[i - 1], dirs[i]))
        en = ("side" if side == "right" else "wall") if i == n - 1 else ("corner", turn(dirs[i], dirs[i + 1]))
        runs.append(Run("line", st, en, A=tuple(points[i]), B=tuple(points[i + 1])))
    return runs


def polygon_vertices(sides, R, cz, turned_deg=0.0):
    """A regular polygon, a face square to the front; vertices by bearing, -180..180.
    T-3176: `turned_deg` turns it about its centre, so a square turned 45 degrees stands
    with an angle to the front (1827's tower, set diagonally across its corner)."""
    out = []
    for k in range(sides):
        b = math.radians(-180 + 180 / sides + turned_deg + k * 360 / sides)
        out.append((R * math.sin(b), cz + R * math.cos(b)))
    return out


def across_corner_chain(ring, corner):
    """T-3176: the part of a ring standing outside its house when it is set across the house's
    corner at x = 0: everything but the quadrant behind the wall's face (z < 0) and inside its
    end (x < 0 for the right corner, x > 0 for the left), walked left to right from where the
    ring crosses one plane to where it crosses the other."""
    k = 1.0 if corner == "right" else -1.0
    inside = lambda q: q[1] < -1e-9 and k * q[0] < -1e-9
    n = len(ring)
    start = next(i for i in range(n) if inside(ring[i]) and not inside(ring[(i + 1) % n]))
    chain = []
    for j in range(n + 1):
        a, b = ring[(start + j) % n], ring[(start + j + 1) % n]
        if inside(a) and not inside(b):
            # entering the outside: across the wall's face (right) or the side's plane (left)
            if corner == "right":
                t = a[1] / (a[1] - b[1])
            else:
                t = a[0] / (a[0] - b[0])
            chain.append((a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1])))
        if not inside(b):
            chain.append(b)
        elif not inside(a):
            if corner == "right":
                t = a[0] / (a[0] - b[0])
            else:
                t = a[1] / (a[1] - b[1])
            q = (a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1]))
            if math.dist(q, chain[-1]) > 1e-3:
                chain.append(q)
            break
    tidy = []
    for q in chain:
        if not tidy or math.dist(q, tidy[-1]) > 1e-3:
            tidy.append(q)
    return tidy


def plan_of(v: dict):
    """The variant's runs, and what its roof and its bearings are measured from."""
    p = v["plan"]
    if p["kind"] == "polyline":
        pts = [tuple(q) for q in p["points"]]
        runs = line_runs(pts, p.get("side_end"))
        return runs, {"centre": None, "kind": "polyline", "lines": [(r.A, r.e, r.n) for r in runs]}
    if p["kind"] == "bow":
        h, rise = p["chord_m"] / 2, p["rise_m"]
        R = (h * h + rise * rise) / (2 * rise)
        c = (0.0, rise - R)
        return [Run("arc", "wall", "wall", c=c, R=R)], {"centre": c, "kind": "arc", "R": R}
    if p["kind"] == "circle":
        R, c = p["radius_m"], (0.0, p["centre_proud_m"])
        return [Run("arc", "wall", "wall", c=c, R=R)], {"centre": c, "kind": "arc", "R": R}
    if p["kind"] == "polygon" and p.get("across_corner"):
        # T-3176: a ring set across its house's corner (1827's turned square): its runs are the
        # ring outside the house, from the wall's face round to the side wall's plane, the last
        # (or first) run ending on that plane as a chamfer's does (T-3048)
        n, R, cz = p["sides"], p["radius_m"], p["centre_proud_m"]
        ring = polygon_vertices(n, R, cz, float(p.get("turned_deg", 0.0)))
        chain = across_corner_chain(ring, p["across_corner"])
        runs = line_runs(chain, p["across_corner"])
        for r in runs:
            r.across = p["across_corner"]
        lines = []
        for k in range(n):
            a, b = ring[k], ring[(k + 1) % n]
            L = math.hypot(b[0] - a[0], b[1] - a[1])
            e = ((b[0] - a[0]) / L, (b[1] - a[1]) / L)
            lines.append((a, e, (-e[1], e[0])))
        return runs, {"centre": (0.0, cz), "kind": "polygon", "lines": lines,
                                                      "ring": ring, "across_corner": p["across_corner"]}
    if p["kind"] == "polygon":
        n, R, cz = p["sides"], p["radius_m"], p["centre_proud_m"]
        ring = polygon_vertices(n, R, cz, float(p.get("turned_deg", 0.0)))
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


def bend(run: Run, flat: dict, out: dict, step, join_quads=False, keep_behind=()):
    """Map a strip's faces onto the run. On an arc, each face is cut into slabs of s first,
    and every vertex takes the curve's own frame, so its normal is the true one."""
    # where the outer face has an edge (a jamb, a band's end): a face meeting the outer face
    # is cut there too, so two faces that share the face's curve share its chords exactly
    edges = sorted({round(p[0], 9) for role, pr in flat.items() if role != "masonry_relief" for p in pr.pos if abs(p[2]) < 1e-9}) if step else []
    for role, pr in flat.items():
        dst = out.setdefault(role, Prim(role))
        t = 0
        while t < len(pr.idx):
            ids = pr.idx[t:t + 3]
            t += 3
            # Clip a convex planar quad once, rather than subdividing its hidden
            # diagonal. Opted in by coursed bays; existing kit bytes stay stable.
            if join_quads and t + 3 <= len(pr.idx):
                nxt = pr.idx[t:t + 3]
                if nxt[:2] == [ids[0], ids[2]]:
                    q = ids + [nxt[2]]
                    normal = pr.nrm[q[0]]
                    points = [pr.pos[i] for i in q]
                    turns = [_dot(_cross(_sub(points[(i+1)%4], points[i]),
                                         _sub(points[(i+2)%4], points[(i+1)%4])), normal) for i in range(4)]
                    if all(abs(_dot(_sub(p, points[0]), normal)) < 1e-9 for p in points) and \
                            (all(v > 1e-12 for v in turns) or all(v < -1e-12 for v in turns)) and \
                            all(pr.nrm[i] == normal for i in q):
                        ids = q
                        t += 3
            poly = [(*pr.pos[i], *pr.nrm[i], *pr.uv[i]) for i in ids]
            pieces = [poly]
            if step:
                s_lo = min(q[0] for q in poly)
                s_hi = max(q[0] for q in poly)
                k0, k1 = math.floor(s_lo / step + 1e-9), math.ceil(s_hi / step - 1e-9)
                cuts = [k * step for k in range(k0 + 1, k1)]
                if role != "masonry_relief" and any(abs(q[2]) < 1e-9 for q in poly):
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
                # (T-3047: but a shallow bay's window recesses, which run back through it).
                # T-3048: a chamfer's run stands behind it to the side wall, whose plane trims it
                across = getattr(run, "across", None)
                if across is not None:
                    # T-3176: a ring across its house's corner stands outside the house on the
                    # wall's side of the corner (trimmed by the wall's plane) or past the end wall
                    # (trimmed by the end wall's plane), whichever side this run stands on
                    k = 1.0 if across == "right" else -1.0
                    if min(k * run.A[0], k * run.world(run.L, 0.0, 0.0)[0]) >= -1e-9:
                        piece = clip_half(piece, lambda q: k * run.world(q[0], q[1], q[2])[0] + 1e-9)
                    else:
                        piece = clip_half(piece, lambda q: run.world(q[0], q[1], q[2])[2] + 1e-9)
                elif run.end == "side":
                    xs = run.world(run.L, 0.0, 0.0)[0]
                    piece = clip_half(piece, lambda q: xs - run.world(q[0], q[1], q[2])[0] + 1e-9)
                elif run.start == "side":
                    xs = run.world(0.0, 0.0, 0.0)[0]
                    piece = clip_half(piece, lambda q: run.world(q[0], q[1], q[2])[0] - xs + 1e-9)
                elif role not in keep_behind:
                    piece = clip_half(piece, lambda q: run.world(q[0], q[1], q[2])[2] + 1e-9)
                if len(piece) < 3:
                    continue
                pts, nrms, uvs = [], [], []
                for q in piece:
                    s, y, z = q[0], q[1], q[2]
                    al, ou = run.frame(s)
                    p = run.world(s, y, z)
                    if -0.01 < p[2] < 0.0 and "side" not in (run.start, run.end) and across is None:     # a mitre's end bent onto the curve: onto the wall plane
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


BED_CLEAR_M = 0.2   # T-2773: the least a host front's bed is carried clear of a bay's band line


def alternating_courses(low, high, deep_max, low_ratio):
    """T-2584: the course lines from `low` to `high` laid deep and thin in turn from the bed
    up, as the street front's T-2566 rhythm lays them: the fewest courses whose deep one is
    no taller than `deep_max`, each thin one `low_ratio` of the deep, the span ending on a
    deep course whenever the count is odd."""
    h = high - low
    for n in range(1, 64):
        deep = h / ((n + 1) // 2 + low_ratio * (n // 2))
        if deep <= deep_max + 1e-9:
            ys, y = [low], low
            for i in range(n - 1):
                y += deep if i % 2 == 0 else low_ratio * deep
                ys.append(y)
            return [*ys, high]
    raise ValueError(f"no alternating coursing fits {h:.3f} m under {deep_max} m courses")


def masonry_cells(o, holes, length, low, high, spec, trim_holes=()):
    """Rock-faced courses over the true curved wall; shallow relief is a separate role.

    The light tier retains the wall and its metric stone texture. Full detail adds
    bevelled faces per unit, with deterministic relief and open mortar joints.
    Only holes crossing a course split that course's units.
    """
    import random
    rng = random.Random(1883)
    ch, bw, joint, relief = (spec[k] for k in ("course_m", "block_m", "joint_m", "relief_m"))
    if any(not h[-1] for h in holes):
        raise ValueError("masonry_cells currently supports flat-headed bay openings")
    wall_cells(o, "wall", holes, 0., length, low, high)
    holes = [*holes, *trim_holes]  # raised dressings own their sockets, not overlapping stone
    c = spec.get("coursing")
    if c and c["rhythm"] == "street_front" and "beds_m" not in c:
        c = None   # T-2773: a bay laid on its host front's beds, built away from the front: even courses
    if c and "beds_m" in c:
        # T-2773: laid on the host front's beds; one closer than BED_CLEAR_M to this storey's
        # band line is not carried, so no course too thin to lay is left under the band
        lines = [low, *[y for y in c["beds_m"] if low + BED_CLEAR_M < y < high - BED_CLEAR_M], high]
    elif c:
        lines = alternating_courses(low, high, ch, c["low_ratio"])
    else:
        lines = [low, *[low+i*ch for i in range(1, math.ceil((high-low)/ch))], high]
    rows = sorted({*lines, *[y for h in holes for y in (h[2], h[3]) if low < y < high]})
    for row, (ya, yb) in enumerate(zip(rows, rows[1:])):
        cy = (ya+yb)/2
        active = [h for h in holes if h[2] < cy < h[3]]
        cuts = sorted({0., length,
                       *[x for i in range(math.ceil(length/bw)+1)
                         if 0 < (x := i*bw+(bw/2 if row % 2 else 0)) < length],
                       *[x for h in active for x in h[:2] if 0 < x < length]})
        for xa, xb in zip(cuts, cuts[1:]):
            cx = (xa+xb)/2
            if any(h[0] < cx < h[1] for h in active) or min(xb-xa, yb-ya) < joint*3:
                continue
            outer = K6.box(xa+joint/2, xb-joint/2, ya+joint/2, yb-joint/2)
            inset = min(.018, (xb-xa)/8, (yb-ya)/8)
            inner = K6.box(xa+joint/2+inset, xb-joint/2-inset,
                           ya+joint/2+inset, yb-joint/2-inset)
            if c:   # T-2584: a deep course on the upper half of the rock face, a thin one on the lower
                if "beds_m" in c:   # T-2773: by its height, as the front's own are
                    i = bisect.bisect_right(lines, cy)
                    thin = lines[i] - lines[i - 1] < c["thin_below_m"]
                else:
                    thin = bisect.bisect_right(lines, cy) % 2 == 0
                depth = -relief*((.6 if thin else .8)+.2*rng.random())
            else:
                depth = -relief*(.6+.4*rng.random())
            for i in range(4):
                j = (i+1) % 4
                o.face("masonry_relief", [o.P(*outer[i], 0), o.P(*outer[j], 0),
                                          o.P(*inner[j], depth), o.P(*inner[i], depth)], (0, 0, 1))
            o.plane("masonry_relief", inner, depth)



def ledge(o, role, run, y, z0, z1, hint):
    """A horizontal face between two offsets of the run, mitred at its ends."""
    o.face(role, [o.P(run.s_start(z0), y, -z0), o.P(run.s_end(z0), y, -z0),
                  o.P(run.s_end(z1), y, -z1), o.P(run.s_start(z1), y, -z1)], hint)


def moulding(o, role, run, y0, profile):
    """T-2460: a moulded section, [n out, u up] from its seat on the face at y0 to its top
    back on the face, swept along the run and mitred at its ends as a ledge is. Its flat
    top is left to the roof that starts on it, as the plain eaves' top is."""
    top = max(u for _, u in profile)
    for (n0, u0), (n1, u1) in zip(profile, profile[1:]):
        if abs(u0 - top) < 1e-9 and abs(u1 - top) < 1e-9:
            continue
        o.face(role, [o.P(run.s_start(n0), y0 + u0, -n0), o.P(run.s_end(n0), y0 + u0, -n0),
                      o.P(run.s_end(n1), y0 + u1, -n1), o.P(run.s_start(n1), y0 + u1, -n1)],
               (0.0, n0 - n1, u1 - u0))


def proud(o, role, run, y0, y1, out, top=True, bottom=True):
    """A slab standing `out` proud of the run's face from y0 to y1: front and ledges."""
    o.plane(role, K6.box(run.s_start(out), run.s_end(out), y0, y1), -out)
    if top:
        ledge(o, role, run, y1, 0.0, out, Y)
    if bottom:
        ledge(o, role, run, y0, 0.0, out, (0.0, -1.0, 0.0))


def prism(o, role, poly2, d0, d1):
    """T-2525: a closed bar: the (s, y) polygon `poly2` carried from depth d0 to d1 behind
    the face (d1 > d0), its front, its back and its sides."""
    o.plane(role, poly2, d0)
    o.plane(role, poly2[::-1], d1, (0.0, 0.0, -1.0))
    o.tube(role, poly2, d0, d1, inward=False)


def rect(s0, s1, y0, y1):
    return [(s0, y0), (s1, y0), (s1, y1), (s0, y1)]


def head_y(outline, x) -> float:
    """The top of a clear hole's outline (K06's, at the face) over x."""
    best = None
    for (a, b) in zip(outline, outline[1:] + outline[:1]):
        if min(a[0], b[0]) - 1e-9 <= x <= max(a[0], b[0]) + 1e-9 and abs(b[0] - a[0]) > 1e-9:
            y = a[1] + (b[1] - a[1]) * (x - a[0]) / (b[0] - a[0])
            best = y if best is None else max(best, y)
    return best


def grille(o, g: dict):
    """T-2525: iron in a window's reveal, `set_back_m` behind the face and in front of its
    frame: `bars` square uprights clipped to the head, a foot bar and a bar at the head's
    spring, and an arch ring of `ring_radius_m` whose crown stands just under that bar (the
    scroll 1621's drawing draws over its basement bars, as a plain ring). In the opening's
    own frame, so the bay bends it with the opening."""
    out = o.holes[0]
    s0, s1 = min(q[0] for q in out), max(q[0] for q in out)
    hd = o.meta["heads"][0]
    spring = hd.get("spring_m", hd.get("top_m", max(q[1] for q in out)))
    b, d = IRON_BAR_M, g["set_back_m"]
    if not (0.0 < d and d + 2 * b + 0.002 <= o.meta["reveal_depth_m"]):
        raise ValueError(f"a grille {d} m back does not stand in a {o.meta['reveal_depth_m']} m reveal")
    if "panel" in g:
        return grille_panel(o, g, s0, s1, spring)
    n = g["bars"]
    for i in range(1, n + 1):
        x = s0 + (s1 - s0) * i / (n + 1)
        prism(o, "iron", rect(x - b / 2, x + b / 2, 0.003, head_y(out, x) - 0.003), d + b + 0.002, d + 2 * b + 0.002)
    for y in (0.06, spring - 0.03):    # 3 mm off the jambs: never in the reveal's planes
        prism(o, "iron", rect(s0 + 0.003, s1 - 0.003, y, y + b), d, d + b)
    r = g["ring_radius_m"]
    if not 0.05 < r < (s1 - s0) / 2:
        raise ValueError(f"a grille's ring of {r} m does not stand in a {s1 - s0:.3f} m light")
    cy, segs = spring - 0.03 - b / 2 - r, 12
    ro, ri = r + b / 2, r - b / 2
    arc = [(math.cos(math.pi * j / segs), math.sin(math.pi * j / segs)) for j in range(segs + 1)]
    q = lambda c, rr: (rr * c[0], cy + rr * c[1])
    for c0, c1 in zip(arc, arc[1:]):          # one band, so no two segments meet face to face
        band = [q(c0, ri), q(c0, ro), q(c1, ro), q(c1, ri)]
        o.plane("iron", band[::-1], d)
        o.plane("iron", band, d + b, (0.0, 0.0, -1.0))
        for rr, sg in ((ro, 1.0), (ri, -1.0)):
            m = ((c0[0] + c1[0]) * sg, (c0[1] + c1[1]) * sg, 0.0)
            o.face("iron", [o.P(*q(c0, rr), d), o.P(*q(c1, rr), d), o.P(*q(c1, rr), d + b), o.P(*q(c0, rr), d + b)], m)
    for c in (arc[0], arc[-1]):               # its two feet
        o.face("iron", [o.P(*q(c, ri), d), o.P(*q(c, ro), d), o.P(*q(c, ro), d + b), o.P(*q(c, ri), d + b)],
               (0.0, -1.0, 0.0))
    for x in (-r, r):     # the ring's legs down to the foot bar
        prism(o, "iron", rect(x - b / 2, x + b / 2, 0.06 + b, cy), d + b + 0.002, d + 2 * b + 0.002)


IRON_BAR_M = 0.018        # T-2525: K01's guard and grille bar (k01_arched_front.IRON_BAR_M)
VOLUTE_SEGMENTS = 14      # T-3129: one panel volute, in straight runs of bar


def _rod(o, p0, p1, d, b):
    """T-3129: a flat bar `b` square from (s, y) p0 to p1, its face `d` behind the wall's:
    the front and the two long sides."""
    _run(o, [p0, p1], d, b)


def _run(o, pts, d, b, closed=False):
    """T-3129: a bar `b` square along the (s, y) polyline `pts` (`closed`: round to its
    first point), its face `d` behind the wall's. Mitred at every bend, so its runs share
    their edges and no two faces of one bar lie over each other."""
    if closed and math.dist(pts[0], pts[-1]) < 1e-9:
        pts = pts[:-1]
    n = len(pts)
    segs = [(pts[i], pts[(i + 1) % n]) for i in range(n if closed else n - 1)]
    nrm = []
    for a, c in segs:
        L = math.dist(a, c)
        nrm.append((-(c[1] - a[1]) / L, (c[0] - a[0]) / L))
    off = []
    for i in range(n):
        ks = ((i - 1) % n, i) if closed else [k for k in (i - 1, i) if 0 <= k < len(segs)]
        ins = [nrm[k] for k in ks]
        mx, my = sum(q[0] for q in ins), sum(q[1] for q in ins)
        m = math.hypot(mx, my)
        mx, my = mx / m, my / m
        k = b / 2 / max(0.3, mx * ins[0][0] + my * ins[0][1])
        off.append((mx * k, my * k))
    L_ = [(pts[i][0] + off[i][0], pts[i][1] + off[i][1]) for i in range(n)]
    R_ = [(pts[i][0] - off[i][0], pts[i][1] - off[i][1]) for i in range(n)]
    for i in range(len(segs)):
        j = (i + 1) % n
        nx, ny = nrm[i]
        o.plane("iron", [R_[i], R_[j], L_[j], L_[i]], d)
        o.face("iron", [o.P(*L_[i], d), o.P(*L_[j], d), o.P(*L_[j], d + b), o.P(*L_[i], d + b)], (nx, ny, 0.0))
        o.face("iron", [o.P(*R_[i], d), o.P(*R_[j], d), o.P(*R_[j], d + b), o.P(*R_[i], d + b)], (-nx, -ny, 0.0))


def _circle(c, r, segs):
    return [(c[0] + r * math.cos(2 * math.pi * j / segs), c[1] + r * math.sin(2 * math.pi * j / segs))
            for j in range(segs + 1)]


def _volute(c, r, start, hand, turns=1.25):
    """A bar curled `turns` times from radius r at angle `start` into a third of it at c."""
    return [(c[0] + r * (1 - 0.68 * t) * math.cos(start + hand * 2 * math.pi * turns * t),
             c[1] + r * (1 - 0.68 * t) * math.sin(start + hand * 2 * math.pi * turns * t))
            for t in (j / VOLUTE_SEGMENTS for j in range(VOLUTE_SEGMENTS + 1))]


def grille_panel(o, g, s0, s1, top):
    """T-3129: a basement light's grille as 1811 Prairie's c. 1888 photograph shows it
    (chicagology_photo): a flat-bar frame round the light, a border `border_m` wide of short
    bars at `pitch_m` (uprights across the head and foot, rungs up the sides), and inside it a
    square panel: a rosette `rosette_m` across at the centre with eight spokes out to a ring
    of `ring_radius_m`, a volute in each corner curling toward the ring, and a smaller one on
    the middle of each side. The frames, the ring and the rosette stand at the set-back; the
    spokes, the volutes and the border's bars just behind them, as the bar grille's uprights
    do, so no two bars in one plane lie over each other."""
    b, d, P = IRON_BAR_M, g["set_back_m"], g["panel"]
    back = d + b + 0.002
    bd, pitch, r0, R = P["border_m"], P["pitch_m"], P["rosette_m"] / 2, g["ring_radius_m"]
    x0, x1, y0, y1 = s0 + 0.012, s1 - 0.012, 0.012, top - 0.012
    xi0, xi1, yi0, yi1 = x0 + bd, x1 - bd, y0 + bd, y1 - bd
    cx, cy = (xi0 + xi1) / 2, (yi0 + yi1) / 2
    hx, hy = (xi1 - xi0) / 2, (yi1 - yi0) / 2
    h = min(hx, hy)
    if not (0.04 <= bd and xi1 - xi0 > 0.3 and yi1 - yi0 > 0.3 and 0.02 <= r0 < R <= 0.7 * h):
        raise ValueError(f"a grille panel with a {bd} m border and a {R} m ring does not stand in a "
                         f"{s1 - s0:.3f} x {top:.3f} m light")
    for (u0, u1, v0, v1) in ((x0, x1, y0, y1), (xi0, xi1, yi0, yi1)):   # the frame and the panel's
        _run(o, [(u0, v0), (u1, v0), (u1, v1), (u0, v1)], d, b, closed=True)
    n = max(2, round((x1 - x0) / pitch))
    for i in range(1, n):                   # the head's and foot's uprights
        x = x0 + (x1 - x0) * i / n
        for (ya, yb) in ((y0, yi0), (yi1, y1)):
            _rod(o, (x, ya), (x, yb), back, b)
    m = max(2, round((yi1 - yi0) / pitch))
    for i in range(1, m):                   # the sides' rungs
        y = yi0 + (yi1 - yi0) * i / m
        for (xa, xb) in ((x0, xi0), (xi1, x1)):
            _rod(o, (xa, y), (xb, y), back, b)
    _run(o, _circle((cx, cy), r0, 10), d, b, closed=True)
    _run(o, _circle((cx, cy), R, 24), d, b, closed=True)
    re = R - 0.012                          # the spokes stop behind the ring
    for k in range(8):                      # the rosette's spokes
        a = math.pi * k / 4
        _rod(o, (cx + r0 * math.cos(a), cy + r0 * math.sin(a)), (cx + re * math.cos(a), cy + re * math.sin(a)), back, b)
    # the volutes stand behind the frames with the spokes, clear of the spokes' ends: in the
    # corners, and smaller on the middle of each side
    rc = 0.3 * h
    for sx, sy in ((1, 1), (-1, 1), (-1, -1), (1, -1)):
        c = (cx + sx * (hx - rc - 0.012), cy + sy * (hy - rc - 0.012))
        _run(o, _volute(c, rc, math.atan2(-sy, -sx), sx * sy), back, b)
    rm = 0.15 * h
    for k, (ux, uy) in enumerate(((1, 0), (0, 1), (-1, 0), (0, -1))):
        c = (cx + ux * (hx - rm - 0.012), cy + uy * (hy - rm - 0.012))
        _run(o, _volute(c, rm, math.atan2(-uy, -ux), 1 if k % 2 == 0 else -1), back, b)


def _check_balcony_scroll_geometry(iron, panel, top_rails, clearance=0.01):
    """Check emitted flat-frame vertices, independently of the scroll's placement formula.

    The panel body's bounding box conservatively encloses its slopes. Below its
    shoulders, iron must clear its actual front. The tail's highest vertices must
    enter one emitted rectangular top-rail prism, rather than float in front of it.
    This is a local construction check, not a rendered or photographic verdict.
    """
    if not iron or not panel or not top_rails or any(not rail for rail in top_rails):
        raise ValueError("a balcony scroll needs emitted iron, panel and top-rail geometry")

    def bounds(points):
        return tuple(min(p[i] for p in points) for i in range(3)), \
               tuple(max(p[i] for p in points) for i in range(3))

    lo, hi = bounds(panel)
    eps = 1e-9
    for x, y, z in iron:
        if y < lo[1] - eps:
            raise ValueError("a balcony scroll falls below its panel's floor")
        if lo[0] - eps <= x <= hi[0] + eps and lo[1] - eps <= y <= hi[1] + clearance \
                and z < hi[2] + clearance - eps:
            raise ValueError("a balcony scroll intersects or fails to clear its emitted stone panel")
    rail_bounds = [bounds(rail) for rail in top_rails]
    top = max(p[1] for p in iron)
    tail = [p for p in iron if abs(p[1] - top) <= eps]
    if any(not any(all(a[i] - eps <= p[i] <= b[i] + eps for i in range(3))
                   for a, b in rail_bounds) for p in tail):
        raise ValueError("a balcony scroll's emitted tail is unsupported by its top rail")


def _inset(poly, b):
    """A convex counter-clockwise (s, y) polygon with every edge moved `b` inward."""
    lines = []
    for i, a in enumerate(poly):
        c = poly[(i + 1) % len(poly)]
        dx, dy = c[0] - a[0], c[1] - a[1]
        L = math.hypot(dx, dy)
        nx, ny = -dy / L, dx / L
        lines.append(((a[0] + nx * b, a[1] + ny * b), (dx, dy)))
    out = []
    for i in range(len(lines)):
        (p0, d0), (p1, d1) = lines[i - 1], lines[i]
        den = d0[0] * d1[1] - d0[1] * d1[0]
        t = ((p1[0] - p0[0]) * d1[1] - (p1[1] - p0[1]) * d1[0]) / den
        out.append((p0[0] + d0[0] * t, p0[1] + d0[1] * t))
    return out


def voussoir_head(o, vs: dict, s0: float, s1: float, y0: float, y1: float):
    """T-2531: a block of splayed voussoirs over a light, from its head (y0) to the course
    above it (y1): `stones` dressed stones, the block `splay_m` wider each side at its top
    than at the light's jambs, their joints fanned so each runs from its point on the head
    to its point on the top. Each stone stands `proud_m` before the face, `joint_m` from
    the next, its arris chamfered `bevel_m` so the joints read as the drawing's lines. In
    the strip's own frame, so the bay bends it."""
    n, sp, pr, j, bv = vs["stones"], vs["splay_m"], vs["proud_m"], vs["joint_m"] / 2, vs["bevel_m"]
    y0 += 0.001     # off the reveal's soffit, whose plane the stones' beds would otherwise share
    bot = [s0 + (s1 - s0) * i / n for i in range(n + 1)]
    top = [s0 - sp + (s1 - s0 + 2 * sp) * i / n for i in range(n + 1)]
    for i in range(n):
        ja = j if i else 0.0
        jb = j if i < n - 1 else 0.0
        poly = [(bot[i] + ja, y0), (bot[i + 1] - jb, y0), (top[i + 1] - jb, y1 - j), (top[i] + ja, y1 - j)]
        face = _inset(poly, bv)
        o.plane("head", face, -pr)
        for k in range(4):     # the chamfer, from the arris back to the face
            a, b, fa, fb = poly[k], poly[(k + 1) % 4], face[k], face[(k + 1) % 4]
            mx, my = (a[0] + b[0]) / 2 - (fa[0] + fb[0]) / 2, (a[1] + b[1]) / 2 - (fa[1] + fb[1]) / 2
            o.face("head", [o.P(*a, -(pr - bv)), o.P(*b, -(pr - bv)), o.P(*fb, -pr), o.P(*fa, -pr)],
                   (mx, my, bv))
        # its sides start a millimetre into the wall: on the face they would be edges
        # `bend` cuts every wall cell at
        o.tube("head", poly, 0.001, -(pr - bv), inward=False)


def surround(o, su: dict, op, s: float, tier: str) -> list:
    """T-2931: a window's moulded surround (1801's lights, from the Taylor photograph): a jamb
    `band_m` broad each side of the light (of a grouped window, of the whole group), from the
    sill's top up into the lintel, which K06 has widened over it and stood proud of it as the
    hood (see `window`). Each jamb is moulded in two faces: its outer two thirds `proud_m` out,
    the third beside the reveal half that, so the light reads set back in a stepped frame.
    A jamb has no back (it stands on the wall's face) and buries its foot in the sill and its
    head in the lintel, so no end of it lies on another face. Returns the jambs' (s0, s1, y0,
    y1) for a coursed wall's cells; the light tier keeps one plain face per jamb."""
    pts = [(q[0] + s, q[1] + op.O[1]) for h in op.holes for q in h]
    x0, x1 = min(q[0] for q in pts), max(q[0] for q in pts)
    y_head = max(q[1] for q in pts)
    b, d = su["band_m"], su["proud_m"]
    # the sill's top falls outward; under the jamb's front it is at most `fall_m` down
    y0, y1 = op.O[1] - 0.016, y_head + 0.004
    out = []
    for a0, a1, inner in ((x0 - b, x0, 1), (x1, x1 + b, 0)):
        out.append((a0, a1, y0, y1))
        if tier != "full":
            o.proud("band", rect(a0, a1, y0, y1), d)
            continue
        # the section, (s, out) from the wall at the jamb's outer edge round to the reveal's
        cut = a0 + b * 2 / 3 if inner else a1 - b * 2 / 3
        sec = [(a0, 0.0), (a0, d), (cut, d), (cut, d / 2), (a1, d / 2), (a1, 0.0)] if inner else \
              [(a0, 0.0), (a0, d / 2), (cut, d / 2), (cut, d), (a1, d), (a1, 0.0)]
        for (s0_, n0), (s1_, n1) in zip(sec, sec[1:]):
            # the section runs up, over and down, so its outside is to the left of each step
            o.face("band", [o.P(s0_, y0, -n0), o.P(s1_, y0, -n1), o.P(s1_, y1, -n1), o.P(s0_, y1, -n0)],
                   (n0 - n1, 0.0, s1_ - s0_))
        # its ends, buried in the sill and the lintel: each a convex piece of the section
        for y, hy in ((y0, -1.0), (y1, 1.0)):
            for p0, p1, dd in ((a0, cut, d if inner else d / 2), (cut, a1, d / 2 if inner else d)):
                o.face("band", [o.P(p0, y, 0.0), o.P(p1, y, 0.0), o.P(p1, y, -dd), o.P(p0, y, -dd)], (0.0, hy, 0.0))
    return out


# -- a window: a K06 opening, its recess cut to the bay ------------------------------------------

class _Cut:
    """T-2998: a run whose eaves end square on the plane where it meets its neighbour, not
    mitred round the corner: a return's under a gable, stopped on the face's plane inside
    the kneeler that covers it. Uncut, it is the run itself."""

    def __init__(self, run, start=False, end=False):
        self.run, self.start_cut, self.end_cut = run, start, end

    def __getattr__(self, k):
        return getattr(self.run, k)

    def s_start(self, z):
        return 0.0 if self.start_cut else self.run.s_start(z)

    def s_end(self, z):
        return self.run.L if self.end_cut else self.run.s_end(z)


def gable_face(v: dict):
    """T-2998: the run a gable roof is carried up from, or None under any other roof. A gable
    stands on a projection's square plan (a return, the front, a return), the front square
    to the wall: the front is the gable, its ridge runs back to the wall on the plan's
    middle, and its slopes fall to the returns."""
    rf = v.get("roof") or {}
    if rf.get("kind") != "gable":
        return None
    pts = [tuple(map(float, q)) for q in v["plan"]["points"]] if v["plan"]["kind"] == "polyline" else []
    eq = lambda a, b: abs(a - b) < 1e-9
    # T-3048: or one return a chamfer, from the front's corner back to its side wall's plane
    # behind the wall's face (1801's south pavilion on its 1911 sheet), the gable on the front
    side = v["plan"].get("side_end")
    if side and len(pts) == 4:
        k = 0 if side == "left" else 3
        if pts[k][1] < 0.0 and (pts[k][0] < pts[1][0] if side == "left" else pts[2][0] < pts[k][0]):
            pts[k] = (pts[1 if side == "left" else 2][0], 0.0)
    if v["kind"] != "projection" or len(pts) != 4 or not (eq(pts[0][1], 0.0) and eq(pts[3][1], 0.0)
                                                        and eq(pts[0][0], pts[1][0]) and eq(pts[2][0], pts[3][0])
                                                        and eq(pts[1][1], pts[2][1]) and pts[1][1] > 0
                                                        and pts[1][0] < pts[2][0]):
        raise ValueError(f"{v['id']}: a gable stands on a projection's square plan, two returns and a front")
    if rf.get("flare") or rf.get("finial"):
        raise ValueError(f"{v['id']}: a gable does not flare, and its finial is its own stone one (gable.finial)")
    if not 1.0 <= float(rf["pitch"]) <= 3.0:
        raise ValueError(f"{v['id']}: a coped gable rises 1.0-3.0 m a metre in, not {rf['pitch']}")
    return 1


def k06_variant(w: dict) -> dict:
    data6 = K6.load()
    v6 = copy.deepcopy(next(x for x in data6["variants"] if x["id"] == w["opening"]))
    # T-2537: a grouped window read off a picture names its own mullion (k01_frontage_params bounds it)
    for k in ("clear_width_m", "clear_height_m", "mullion_m"):
        if k in w:
            v6[k] = w[k]
    # T-2815: a transom window's lights in tiers on stone bars, read off a picture (Keith's bow)
    if "tiers" in w:
        v6["tiers"] = w["tiers"]
    # T-2886: a light between a bay's columns names its own narrower head band
    if "head_band_m" in w:
        v6["overrides"] = {**v6.get("overrides", {}), "head_band_m": w["head_band_m"]}
    # T-2883: a narrow light (an oriel's cheek) is one light a sash: no bar splits its glass
    if w.get("narrow"):
        v6["panes"] = [1, 1]
        if "transom_m" in v6:   # T-3007: and its transom one light (1811's oriel's return)
            v6["transom_lights"] = 1
    return v6


def window(w: dict, s: float, y_sill: float, recess: float):
    """The K06 opening for one window entry, its sill socket at (s, y_sill) on the face, its
    room cut so the recess runs `recess` behind the face: (opening, daylight hole)."""
    data6 = copy.deepcopy(K6.load())
    v6 = k06_variant(w)
    if w.get("narrow"):
        # T-2883: its sill and lintel stop at its jambs, so a light 0.3 m across stands in a
        # cheek under half a metre deep, the cheek's own stone its surround
        data6["parts"]["sill"]["horn_m"] = 0.0
        data6["parts"]["head_band"]["ear_m"] = 0.0
        # and its sashes take K06's least stile, so the glass is most of a light so narrow
        data6["parts"]["sash"]["stile_m"] = data6["parts"]["sash"]["range_stile_m"][0]
    if w.get("surround"):
        # T-2931: a moulded surround's jambs stand on the sill's horns and run up into the
        # lintel's ears, so the sill and the lintel reach as far out as the surround does and
        # the lintel stands proud of it as its hood (1801's lights, from the Taylor photograph)
        su = w["surround"]
        # (a centimetre past the jambs, so a jamb's side never lies on the sill's end)
        data6["parts"]["sill"]["horn_m"] = su["band_m"] + 0.01
        data6["parts"]["head_band"].update({"ear_m": su["band_m"] + 0.01, "width_m": su["head_m"],
                                             "proud_m": su["head_proud_m"]})
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
        # T-3047: on a shallow projection, each window's hole as (x0, x1, y0, y1) in the bay's
        # frame: its recess runs back through the wall plane, where the host opens its face
        self.host_holes: list[tuple] = []
        self.seed = seed_of(v["id"], 0 if tier == "full" else 1)
        self.runs, self.plan = plan_of(v)
        self.stage_runs: list = []   # T-1890: a staged tower's upper ring, numbered on from `runs`

    def build(self, board: bool = True):
        if self.v.get("stage"):
            return self._build_staged(board)
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
        # T-2460: eaves that name a moulded section are that section, in the bay's stone:
        # it reaches out as far as the section does and its top is the roof's eaves line
        prof = [tuple(q) for q in eaves.get("profile", ())]
        if prof:
            ov, fh = max(n for n, _ in prof), max(u for _, u in prof)
        y_e = y_top + fh
        gi = gable_face(v)   # T-2998: the run a gable is carried up from, or None
        self._y_top = y_top
        self.meta.update({"base_m": y0, "levels_m": [round(y, 4) for y in levels], "wall_top_m": round(y_top, 4),
                          "eave_m": round(y_e, 4), "wall_thickness_m": wall_t, "recess_m": recess,
                          "overhang_m": ov, "max_seg_deg": cv["max_seg_deg"]})
        # windows, by run and storey
        per_run = {i: {k: [] for k in range(len(v["storeys"]))} for i in range(len(self.runs))}
        for k, st in enumerate(v["storeys"]):
            for w in st["windows"]:
                for i, s in locate(self.runs, self.plan, w):
                    per_run[i][k].append((w, s))
        y_wall0 = plinth["height_m"] if grade else self._wall_foot(y0)
        if not y_wall0 < levels[1] - 1e-9:
            raise ValueError(f"{v['id']}: its walls start at {y_wall0:.3f} m, over its lowest storey")
        for i, run in enumerate(self.runs):
            flat = strip(f"{v['id']}|run{i}")
            for k in range(len(v["storeys"])):
                holes = []
                trim_holes = []
                lo = y_wall0 if k == 0 else levels[k]
                hi = levels[k + 1]
                for w, s in per_run[i][k]:
                    o = window(w, s, levels[k] + w["sill_m"], w.get("recess_m", recess))
                    if w.get("grille") and self.tier == "full":   # the light tier keeps the hole
                        grille(o, w["grille"])
                    for h in o.holes:
                        sh = [(q[0] + s, q[1] + o.O[1]) for q in h]
                        holes.append((sh[0][0], sh[1][0], sh[0][1], sh[2][1], sh[2:], len(sh) == 4))
                        if v.get("shallow"):
                            xs = sorted(run.world(q[0], 0.0, 0.0)[0] for q in sh)
                            ys = [q[1] for q in sh]
                            self.host_holes.append((xs[0], xs[-1], min(ys), max(ys)))
                    if w.get("voussoirs"):
                        # T-2531: a dressed head over the light, up to the string course
                        sh = [(q[0] + s, q[1] + o.O[1]) for q in o.holes[0]]
                        y_hi = hi - band["height_m"] / 2 if k + 1 < len(v["storeys"]) else hi
                        if y_hi - max(q[1] for q in sh) < 0.1:
                            raise ValueError(f"no room for a voussoir head over the light at s = {s:.3f}")
                        voussoir_head(flat, w["voussoirs"], min(q[0] for q in sh), max(q[0] for q in sh),
                                      max(q[1] for q in sh), y_hi)
                    if w.get("surround"):
                        jambs = surround(flat, w["surround"], o, s, self.tier)
                        if v.get("masonry"):
                            trim_holes += [(a - .002, b + .002, c - .002, d + .002, (), True) for a, b, c, d in jambs]
                    if v.get("masonry"):
                        for role in ("sill", "head"):
                            pts = o.prims[role].pos
                            x0, x1 = min(p[0] for p in pts)-.002, max(p[0] for p in pts)+.002
                            y0_, y1 = min(p[1] for p in pts)-.002, max(p[1] for p in pts)+.002
                            trim_holes.append((x0, x1, y0_, y1, (), True))
                        if w.get("voussoirs"):   # T-2531: the dressed head stands where the cells would
                            sp = w["voussoirs"]["splay_m"] + .002
                            trim_holes.append((min(q[0] for q in sh) - sp, max(q[0] for q in sh) + sp,
                                               max(q[1] for q in sh) - .002, y_hi + .002, (), True))
                    drop = cv.get("drop_roles", ()) if self.tier == "light" else ()
                    if w.get("voussoirs"):     # T-2531: they are its head, in place of K06's lintel
                        drop = (*drop, "head")
                    merge(flat.prims, o.prims, drop)
                    self.windows.append(self._window_record(run, i, k, w, s, o, wall_t))
                # T-2919: a bay rock-faced to a storey line (`to_m`) is smooth ashlar over it
                if v.get("masonry") and self.tier == "full" and hi <= v["masonry"].get("to_m", math.inf) + 1e-6:
                    masonry_cells(flat, holes, run.L, lo, hi, v["masonry"], trim_holes)
                else:
                    wall_cells(flat, "wall", holes, 0.0, run.L, lo, hi)
                if v["storeys"][k].get("frieze"):
                    if per_run[i][k] or k == 0:
                        raise ValueError(f"{v['id']}: a frieze is a windowless storey over another")
                    self._frieze(flat, run, levels[k], hi, v["storeys"][k]["frieze"], band["height_m"],
                                 k + 1 < len(v["storeys"]))
                hf = v["storeys"][k].get("head_frieze")
                if hf and i == hf["run"]:
                    self._head_frieze(flat, run, levels[k], hf)
                if 0 < k and v["storeys"][k].get("corbel_table"):
                    self._corbel_table(flat, run, levels[k], v["storeys"][k]["corbel_table"])
                elif 0 < k:
                    yb = levels[k]
                    proud(flat, "band", run, yb - band["height_m"] / 2, yb + band["height_m"] / 2, band["proud_m"])
            if v.get("pilasters"):
                self._pilasters(flat, run, i, levels, y_wall0, band["height_m"])
            if grade:
                proud(flat, "plinth", run, 0.0, plinth["height_m"], plinth["proud_m"], bottom=False)
            # the eaves: a soffit out to the fascia, the fascia's top the roof's eaves line
            if v.get("cap_band"):
                self._cap_band(flat, run, y_top, v["cap_band"])
            # T-2998: under a gable the face has no eaves (it is carried up as the gable), and
            # the returns' eaves stop square on the face's plane, inside the kneelers
            er = _Cut(run, start=gi is not None and i == gi + 1, end=gi is not None and i == gi - 1)
            if v.get("capped"):
                pass   # T-1890: a staged tower's shaft, its top inside the stage's corbel courses
            elif gi is not None and i == gi:
                pass
            elif gi is not None and "side" in (run.start, run.end):
                pass   # T-3048: a chamfer's head is under its kneeler, which closes over it
            elif prof:
                # T-2472: in the stone of the bay's bands, or the role its eaves name (the
                # bracketed cornice's section is the eave's painted timber)
                moulding(flat, eaves.get("role", "band"), er, y_top, prof)
            else:
                ledge(flat, "soffit", er, y_top, 0.0, ov, (0.0, -1.0, 0.0))
                flat.plane("fascia", K6.box(er.s_start(ov), er.s_end(ov), y_top, y_e), -ov)
            if v.get("brackets"):
                self._modillions(flat, run, y_top, ov)
            if v.get("corbel_table"):
                self._eave_corbel_table(flat, run, y_top, ov)
            if v.get("balcony"):
                self._balcony(flat, run, y_e, ov, first=i == 0, idx=i)
            if v.get("floor_balcony"):
                ((fi, fs),) = locate(self.runs, self.plan, {"at": [v["floor_balcony"]["at"]]})
                if fi == i:
                    self._floor_balcony(flat, fs, cv)
            if not grade and v.get("apron"):
                self._apron_face(flat, run, y0)
            elif not grade:
                self._corbel_courses(flat, run, y0)
            bend(run, flat.prims, self.prims, run.seg_step(cv["max_seg_deg"]), join_quads=bool(v.get("masonry")),
                 keep_behind=WINDOW_ROLES if v.get("shallow") else ())
        world = strip(f"{v['id']}|world")
        if not grade and v.get("apron"):
            self._apron_bottom(world, y0, cv)
        elif not grade:
            self._corbel_bottom(world, y0, cv)
        if not v.get("capped"):
            self._roof(world, y_e, ov, cv)
        if v.get("back_from_m") is not None:
            self._back(world, float(v["back_from_m"]), y_top, y_e)
        if v.get("corner_back_m") is not None:
            self._corner_back(world, float(v["corner_back_m"]), y_top, y_e, ov)
        if v.get("back_over") is not None:
            self._back_over(world, v["back_over"])
        if v.get("brackets"):
            self._consoles(world, y_top, ov)
        merge(self.prims, world.prims)
        self._sockets(y0, y_e)
        if board:
            self._board(y_e)
        return self

    def _build_staged(self, board):
        """T-1890: a tower with a corbelled upper stage, as two of the kit's own builds in one
        frame. The shaft is the plan's ring, its storeys under `from_storey`, capped (no eaves,
        no roof): its top stands inside the stage's corbel courses. The stage is the same
        tower on a ring `radius_m` about the same centre, standing on that storey line as an
        oriel stands on its floor, its corbel courses stepped from its face back to the shaft's
        (their reach the two radii's difference, so the lowest course bears on the shaft), and
        its eaves, cone and finial are the tower's."""
        import copy
        v, st = self.v, self.v["stage"]
        k, R2, K = int(st["from_storey"]), float(st["radius_m"]), int(st["corbel_courses"])
        R1 = float(v["plan"]["radius_m"])
        if v["kind"] != "tower" or v["plan"]["kind"] != "circle" or v["base"] != "grade":
            raise ValueError(f"{v['id']}: only a round tower on grade takes a corbelled stage")
        if not 0 < k < len(v["storeys"]) or not R1 < R2 or K < 1:
            raise ValueError(f"{v['id']}: its stage stands on one of its storey lines, wider than its shaft, "
                             f"on at least one corbel course")
        cb = part(v, self.data, "corbel")
        if (R2 - R1) / (K + 1) > cb["max_oversail_ratio"] * cb["course_height_m"] + 1e-9:
            raise ValueError(f"{v['id']}: {K} corbel courses cannot carry its stage {R2 - R1:.3f} m out "
                             f"(each oversails at most {cb['max_oversail_ratio']} of its height)")
        lo = copy.deepcopy(v)
        lo.pop("stage")
        lo["storeys"], lo["capped"] = lo["storeys"][:k], True
        lower = Bay(lo, self.data, self.tier).build(board=False)
        y_s = lower.meta["wall_top_m"]
        hi = copy.deepcopy(v)
        hi.pop("stage")
        hi["storeys"], hi["base"] = hi["storeys"][k:], y_s
        hi["plan"] = {**v["plan"], "radius_m": R2}
        hi["corbel"] = {"courses": K, "reach_m": R2 - R1}
        upper = Bay(hi, self.data, self.tier).build(board=False)
        merge(self.prims, lower.prims)
        merge(self.prims, upper.prims)
        # the stage's windows on the stage's ring, numbered on from the shaft's runs and storeys
        n = len(lower.runs)
        for w in upper.windows:
            w["run"], w["storey"] = w["run"] + n, w["storey"] + k
        self.stage_runs = upper.runs
        self.windows = lower.windows + upper.windows
        self.meta = dict(upper.meta)
        self.meta.update({"base_m": 0.0, "levels_m": lower.meta["levels_m"] + upper.meta["levels_m"][1:],
                          "stage": {"base_m": round(y_s, 4), "radius_m": R2, "shaft_radius_m": R1,
                                    "junctions_x": [round(upper.runs[0].world(0.0, 0, 0)[0], 4),
                                                    round(upper.runs[-1].world(upper.runs[-1].L, 0, 0)[0], 4)],
                                    **upper.meta["corbel"]}})
        self._sockets(0.0, upper.meta["eave_m"])
        if board:
            self._board(upper.meta["eave_m"])
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
        # T-1890: a staged tower's corbel steps back to its shaft, not to the wall
        reach = v["corbel"].get("reach_m") or max(r.world(s, 0, 0)[2] for r in self.runs for s in (0.0, r.L))
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

    def _apron_layout(self, y0):
        """T-2883: (foot, the foot's profile [n out, u up] from its underside to the face).
        T-3007: a ROUND apron (`form` "round", 1811's oriel's rock-faced base on its 1888
        plate) is a quarter round of `radius_m` from the face turned under to its foot, so its
        profile runs from the underside, that far behind the face, up round to the face, and
        the walls stand from the round's top (`_wall_foot`): its foot may be the floor itself,
        the round then taken out of the lowest storey's wall."""
        foot = float(self.v["apron"]["foot_m"])
        if self.v["apron"].get("form") == "round":
            R = float(self.v["apron"]["radius_m"])
            if not 0.1 <= R <= 0.5 or not y0 - 0.5 <= foot <= y0 <= foot + R:
                raise ValueError(f"{self.v['id']}: a round apron turns under on 0.1-0.5 m (not {R}) from a foot "
                                 f"at most 0.5 m under its floor at {y0} m, its top on or over the floor")
            k = ROUND_APRON_STEPS
            return foot, [(-R + R * math.cos(math.pi / 2 * (k - j) / k), R - R * math.sin(math.pi / 2 * (k - j) / k))
                          for j in range(k + 1)]
        prof = [tuple(q) for q in part(self.v, self.data, "apron")["foot_profile"]]
        if not foot + max(u for _, u in prof) < y0:
            raise ValueError(f"{self.v['id']}: the apron's foot at {foot} m leaves no face under the floor at {y0} m")
        return foot, prof

    def _wall_foot(self, y0):
        """Where an oriel's walls start: its floor, or the top of its round apron (T-3007)."""
        ap = self.v.get("apron") or {}
        return max(y0, float(ap["foot_m"]) + float(ap["radius_m"])) if ap.get("form") == "round" else y0

    def _apron_face(self, flat, run, y0):
        """The run's face carried straight down from the floor to the foot, and the foot's
        moulding swept along it, in the apron's own role (T-2904: the kit lays it in the
        support's stone; a host may give it a stone of its own, as 1625's print reads it)."""
        foot, prof = self._apron_layout(y0)
        if self.v["apron"].get("form") != "round":   # T-3007: a round apron is its moulding alone
            wall_cells(flat, "apron", [], 0.0, run.L, foot + max(u for _, u in prof), y0)
        moulding(flat, "apron", run, foot, prof)

    def _apron_bottom(self, world, y0, cv):
        """The foot's underside: the plan offset out to the foot's nose, closed back to the wall."""
        foot, prof = self._apron_layout(y0)
        rnd = self.v["apron"].get("form") == "round"
        # T-3007: a round apron's underside is its plan offset IN by its radius, back to the wall
        z = min(n for n, _ in prof) if rnd else max(n for n, _ in prof)
        pts = []
        for r in self.runs:
            a, b = r.s_start(z), r.s_end(z)
            st = r.seg_step(cv["max_seg_deg"])
            n = max(1, math.ceil((b - a) / st)) if st else 1
            for j in range(n + (1 if r is self.runs[-1] else 0)):
                pts.append(r.world(a + (b - a) * j / n, foot, z))
        world.face("apron", pts, (0.0, -1.0, 0.0))
        self.meta["apron"] = {"top_m": round(y0, 4), "foot_m": round(foot, 4),
                              "foot_height_m": round(max(u for _, u in prof), 4), "foot_proud_m": round(z, 4),
                              **({"form": "round"} if rnd else {})}

    # brackets (T-2408) -----------------------------------------------------------------------
    def _modillions(self, flat, run, y_top, ov):
        """A row of plain blocks under the soffit along one run, each standing out from the
        run's face toward the fascia, kept `margin_m` clear of the run's ends where the
        corner consoles stand."""
        if self.tier == "light":
            return    # a far view's copy: the consoles carry the eaves' outline, the row is detail
        m = self.v["brackets"]["modillions"]
        w, drop, out = m["width_m"], m["drop_m"], m["out_m"]
        if out > ov:
            raise ValueError(f"{self.v['id']}: a modillion {out} m out reaches past the fascia at {ov} m")
        a, b = run.s_start(0.0) + m["margin_m"], run.s_end(0.0) - m["margin_m"]
        n = math.floor((b - a - w) / m["spacing_m"] + 1e-9) + 1 if b - a >= w else 0
        if n <= 0:
            return
        gap = (b - a - n * w) / max(n - 1, 1) if n > 1 else 0.0
        x0 = a if n > 1 else (a + b - w) / 2
        y0 = y_top - drop
        for k in range(n):
            s0 = x0 + k * (w + gap)
            s1 = s0 + w
            flat.plane("bracket", K6.box(s0, s1, y0, y_top), -out)
            for s_, hx in ((s0, -1.0), (s1, 1.0)):
                flat.face("bracket", [flat.P(s_, y0, 0.0), flat.P(s_, y_top, 0.0), flat.P(s_, y_top, -out),
                                      flat.P(s_, y0, -out)], (hx, 0.0, 0.0))
            flat.face("bracket", [flat.P(s0, y0, 0.0), flat.P(s1, y0, 0.0), flat.P(s1, y0, -out),
                                  flat.P(s0, y0, -out)], (0.0, -1.0, 0.0))
        self.meta.setdefault("brackets", {})["modillions"] = self.meta.get("brackets", {}).get("modillions", 0) + n

    def _corbel_table(self, flat, run, y_floor, ct):
        """T-1890: a corbel table carrying a storey (1801's 18th Street section, the Taylor
        print and HABS photograph 2): in place of the floor band, a stone course `course_m`
        deep and `proud_m` out under the storey's floor line, and under it a row of corbels
        `block_m` wide at `pitch_m`, each two steps down to `height_m` under the line, the
        upper as proud as the course less a tenth, the lower half as proud, kept `margin_m`
        clear of the run's ends. The light tier keeps the course."""
        h, cm, out, w, pm, mg = (float(ct[k]) for k in ("height_m", "course_m", "proud_m", "block_m",
                                                         "pitch_m", "margin_m"))
        proud(flat, "band", run, y_floor - cm, y_floor, out)
        if self.tier == "light":
            return
        a, b = run.s_start(0.0) + mg, run.s_end(0.0) - mg
        n = math.floor((b - a - w) / pm + 1e-9) + 1 if b - a >= w else 0
        if n <= 0:
            return
        gap = (b - a - n * w) / max(n - 1, 1) if n > 1 else 0.0
        x0 = a if n > 1 else (a + b - w) / 2
        y_c, y_m, y_f = y_floor - cm, y_floor - cm - (h - cm) / 2, y_floor - h
        for k in range(n):
            s0 = x0 + k * (w + gap)
            s1 = s0 + w
            for ya, yb, o in ((y_m, y_c, out * 0.9), (y_f, y_m, out * 0.45)):
                flat.plane("corbel", K6.box(s0, s1, ya, yb), -o)
                for s_, hx in ((s0, -1.0), (s1, 1.0)):
                    flat.face("corbel", [flat.P(s_, ya, 0.0), flat.P(s_, yb, 0.0), flat.P(s_, yb, -o),
                                         flat.P(s_, ya, -o)], (hx, 0.0, 0.0))
                flat.face("corbel", [flat.P(s0, ya, 0.0), flat.P(s1, ya, 0.0), flat.P(s1, ya, -o),
                                     flat.P(s0, ya, -o)], (0.0, -1.0, 0.0))
        self.meta["corbel_table"] = self.meta.get("corbel_table", 0) + n

    def _eave_corbel_table(self, flat, run, y_top, ov):
        """T-3195: a row of plain stone blocks under a moulded eave along every run (1827's
        tower, from the Doane photograph): blocks `width_m` across, `drop_m` deep under the
        wall top and `out_m` before the face, as many as fit at `spacing_m` between `margin_m`
        from each of the run's ends (so a polygon's corners stand clear), spread evenly there. Each block's back and top stand
        against the face and the moulding's bed and are not drawn."""
        if self.tier == "light":
            return    # a far view's copy: the moulding carries the eave's outline, the row is detail
        m = self.v["corbel_table"]
        w, drop, out = m["width_m"], m["drop_m"], m["out_m"]
        if out > ov:
            raise ValueError(f"{self.v['id']}: a corbel {out} m out reaches past its eave at {ov} m")
        a, b = run.s_start(0.0) + m["margin_m"], run.s_end(0.0) - m["margin_m"]
        n = math.floor((b - a - w) / m["spacing_m"] + 1e-9) + 1 if b - a >= w else 0
        if n <= 0:
            return    # a run too short for one block (a return the host wall all but closes)
        gap = (b - a - n * w) / max(n - 1, 1) if n > 1 else 0.0
        x0 = a if n > 1 else (a + b - w) / 2
        y0 = y_top - drop
        for k in range(n):
            s0 = x0 + k * (w + gap)
            s1 = s0 + w
            flat.plane("corbel", K6.box(s0, s1, y0, y_top), -out)
            for s_, hx in ((s0, -1.0), (s1, 1.0)):
                flat.face("corbel", [flat.P(s_, y0, 0.0), flat.P(s_, y_top, 0.0), flat.P(s_, y_top, -out),
                                     flat.P(s_, y0, -out)], (hx, 0.0, 0.0))
            flat.face("corbel", [flat.P(s0, y0, 0.0), flat.P(s1, y0, 0.0), flat.P(s1, y0, -out),
                                 flat.P(s0, y0, -out)], (0.0, -1.0, 0.0))
        self.meta["corbel_table"] = self.meta.get("corbel_table", 0) + n

    def _consoles(self, world, y_top, ov):
        """A console under the soffit at every corner of the plan, on the corner's bisector:
        its top on the soffit from the corner out `reach_m`, its underside a quarter ellipse
        sweeping in and down to the corner `drop_m` under the soffit, `thickness_m` across.
        Its top and its back stand against the soffit and the corner and are not drawn."""
        c = self.v["brackets"]["consoles"]
        R, D, t = c["reach_m"], c["drop_m"], c["thickness_m"] / 2
        if self.plan["kind"] != "polyline":
            raise ValueError(f"{self.v['id']}: consoles stand at a polyline's corners")
        lines = self.plan["lines"]
        k = c["segments"] if self.tier == "full" else max(2, c["segments"] // 2)
        arc = [(R - R * math.sin(math.pi / 2 * j / k), -D + D * math.cos(math.pi / 2 * j / k)) for j in range(k + 1)]
        n_c = 0
        for (a1, e1, n1), (a2, e2, n2) in zip(lines, lines[1:]):
            bx, bz = n1[0] + n2[0], n1[1] + n2[1]
            L = math.hypot(bx, bz)
            bx, bz = bx / L, bz / L
            if R > ov / max(n1[0] * bx + n1[1] * bz, 1e-9) + 1e-9:
                raise ValueError(f"{self.v['id']}: a console {R} m out reaches past the eaves' corner")
            C = self._offset_corner((a1, n1), (a2, n2), 0.0)
            tx, tz = -bz, bx
            P = lambda r, y, side: (C[0] + r * bx + side * t * tx, y_top + y, C[1] + r * bz + side * t * tz)
            for side in (-1.0, 1.0):
                for j in range(k):
                    world.face("bracket", [P(0.0, 0.0, side), P(*arc[j], side), P(*arc[j + 1], side)],
                               (side * tx, 0.0, side * tz))
            for j in range(k):
                (r0, y0), (r1, y1) = arc[j], arc[j + 1]
                hr, hy = R - (r0 + r1) / 2, -D - (y0 + y1) / 2   # the underside faces the ellipse's centre
                world.face("bracket", [P(r0, y0, -1.0), P(r1, y1, -1.0), P(r1, y1, 1.0), P(r0, y0, 1.0)],
                           (hr * bx, hy, hr * bz))
            n_c += 1
        self.meta.setdefault("brackets", {})["consoles"] = n_c

    # roof -----------------------------------------------------------------------------------
    def _roof(self, world, y_e, ov, cv):
        rf = self.v["roof"]
        tower = self.v["kind"] == "tower"
        if rf["kind"] == "gable":
            return self._gable(world, self._y_top, y_e, ov)
        if rf["kind"] == "spire":
            self._spire(world, y_e, ov, float(rf["rise_m"]))
        elif self.plan["kind"] == "arc":
            self._cone(world, y_e, ov, rf["pitch"], cv, tower)
        else:
            self._hip(world, y_e, ov, rf["pitch"], tower)
        if rf.get("finial"):
            self._finial(world)

    def _hip(self, world, y_e, ov, pitch, tower):
        """The plan's lines offset to the eaves and lifted at one pitch; each plane keeps the
        part of the plan where it is the lowest, so the planes meet on their hips."""
        lines = [((a[0] + ov * n[0], a[1] + ov * n[1]), (-n[0], -n[1])) for a, e, n in self.plan["lines"]]
        flare = self.v["roof"].get("flare")
        if flare and (tower or pitch == 0):
            raise ValueError(f"{self.v['id']}: only a bay's pitched hip flares")
        mn = self.v["roof"].get("mansard")
        if mn and (tower or flare or pitch == 0 or self.plan["kind"] != "polyline"):
            raise ValueError(f"{self.v['id']}: a mansard is a polyline bay's pitched hip, unflared")
        if tower:
            ring = self.plan["ring"]
            k = len(ring)
            R = math.hypot(ring[0][0] - self.plan["centre"][0], ring[0][1] - self.plan["centre"][1])
            Re = R + ov / math.cos(math.pi / k)
            c = self.plan["centre"]
            dom = [(c[0] + (q[0] - c[0]) * Re / R, c[1] + (q[1] - c[1]) * Re / R) for q in ring]
            if not self.plan.get("across_corner"):
                dom = clip_half(dom, lambda p: p[1])
            # T-3176: a tower set across its corner stands past the main eave on both its walls,
            # so its cap is the whole ring's (as a corner turret's cone is, T-2900)
        else:
            dom = [self._offset_corner(None, lines[0], ov)]
            for i in range(len(lines) - 1):
                dom.append(self._offset_corner(lines[i], lines[i + 1], ov))
            dom.append(self._offset_corner(lines[-1], None, ov))
        if area(dom) < 0:
            dom.reverse()
        d = lambda L, p: L[1][0] * (p[0] - L[0][0]) + L[1][1] * (p[1] - L[0][1])
        faces = []
        # T-3176: a hip cut flat at `deck_rise_m` over its eaves (1827's tower, its slated hip
        # stopped under a crested deck in the Doane photograph): every plane is kept under it,
        # and the deck is the plan's eaves outline drawn in by the planes' common run to it
        deck = self.v["roof"].get("deck_rise_m")
        if deck is not None and (not tower or pitch <= 0 or flare or mn):
            raise ValueError(f"{self.v['id']}: only a tower's pitched, unflared hip is cut flat to a deck")
        if pitch == 0:
            faces.append((dom, lambda p: y_e))
        else:
            for i, Li in enumerate(lines):
                reg = dom
                for j, Lj in enumerate(lines):
                    if j != i and reg:
                        reg = clip_half(reg, lambda p, Lj=Lj: d(Lj, p) - d(Li, p))
                if reg and deck is not None:
                    reg = clip_half(reg, lambda p, Li=Li: float(deck) / pitch - d(Li, p))
                if len(reg) >= 3 and abs(area(reg)) > 1e-8:
                    if flare:
                        faces += self._flare_bands(reg, Li, d, y_e, pitch, flare)
                    elif mn:
                        faces += self._mansard_bands(reg, Li, d, y_e, pitch, mn)
                    else:
                        faces.append((reg, lambda p, Li=Li: y_e + pitch * d(Li, p)))
        apex = (0.0, y_e, 0.0)
        for reg, hgt in faces:
            pts = [(p[0], hgt(p), p[1]) for p in reg]
            world.face("roof", pts, Y)
            for q in pts:
                if q[1] > apex[1]:
                    apex = q
            if tower or mn:
                for a, b in zip(reg, reg[1:] + reg[:1]):
                    if abs(a[1]) < 1e-9 and abs(b[1]) < 1e-9:
                        world.face("roof_back", [(a[0], y_e, 0.0), (b[0], y_e, 0.0), (b[0], hgt(b), 0.0),
                                                 (a[0], hgt(a), 0.0)], (0.0, 0.0, -1.0))
        self.meta["roof"] = {"kind": "flat" if pitch == 0 else "hip", "pitch": pitch, "planes": len(faces),
                             "apex": [round(c, 4) for c in apex]}
        if deck is not None:
            top = dom
            for Li in lines:
                top = clip_half(top, lambda p, Li=Li: d(Li, p) - float(deck) / pitch)
            if len(top) < 3:
                raise ValueError(f"{self.v['id']}: its deck {deck} m over the eaves stands over the hip's apex")
            y_d = y_e + float(deck)
            world.face("roof", [(p[0], y_d, p[1]) for p in top], Y)
            self.meta["roof"]["deck"] = {"y_m": round(y_d, 4), "corners": [[round(p[0], 4), round(p[1], 4)] for p in top]}
            if self.v["roof"].get("cresting"):
                self._deck_cresting(world, top, y_d, self.v["roof"]["cresting"])
        if flare:
            self.meta["roof"]["flare"] = dict(flare)
        if mn:
            # the curb: the eaves lines offset in by the lower faces' run, met pairwise and at
            # the wall plane, so a host can stand cresting on it (k01_frontage.bay)
            run = float(mn["rise_m"]) / math.tan(math.radians(float(mn["lower_pitch_deg"])))
            inner = [((a[0] + run * n[0], a[1] + run * n[1]), n) for a, n in lines]   # n points inward
            curb = [self._offset_corner(None, inner[0], 0.0)]
            for i in range(len(inner) - 1):
                curb.append(self._offset_corner(inner[i], inner[i + 1], 0.0))
            curb.append(self._offset_corner(inner[-1], None, 0.0))
            self.meta["roof"]["mansard"] = {"rise_m": float(mn["rise_m"]), "lower_pitch_deg": float(mn["lower_pitch_deg"]),
                                            "curb_m": round(y_e + float(mn["rise_m"]), 4),
                                            "curb": [[round(c, 4) for c in q] for q in curb]}

    def _gable(self, world, y_top, y_e, ov):
        """T-2998: a coped stone gable (1801 Prairie's south pavilion, the Taylor photograph).
        The front is carried up past the wall top as a gable between two KNEELERS, square
        blocks over the plan's front corners that stand from the wall top to the copings'
        foot, run back to the wall plane and cover the returns' eaves (stopped on the
        front's plane, `_Cut`). From each kneeler's inner face a slope of the roof rises at
        `pitch` to a ridge on the plan's middle, eaves line high at the kneeler, and runs
        back from the gable to the wall plane. The gable's face stands `upstand_m` over the
        roof's plane under a stone COPING along each rake, proud of the face, its back the
        parapet's over the roof. A PINNACLE (a square shaft under a pyramid) may stand on
        each kneeler and a stone FINIAL (a block under a pyramid) on the apex.
        T-3073: `inset_m` [left, right] stands the gable's own corners that far in from the
        front's (1801's, on the Taylor photograph, stops short of the chamfer): its middle,
        rakes and pinnacles move with them, and each kneeler runs on out from the gable's
        corner over the front's, so the wall top beside a narrower gable is still covered."""
        rf, g = self.v["roof"], self.v["roof"]["gable"]
        pitch = float(rf["pitch"])
        pts = self.v["plan"]["points"]
        xl, p, xr = float(pts[1][0]), float(pts[1][1]), float(pts[2][0])
        il, ir = (float(a) for a in g.get("inset_m", (0.0, 0.0)))
        # T-1890: up to 1.5 m (1801's 18th Street section, its wall dormer about 3.2 m across a 6 m front)
        if not (0.0 <= il <= 1.5 and 0.0 <= ir <= 1.5):
            raise ValueError(f"{self.v['id']}: a gable's inset_m stands its corners 0-1.5 m in from the front's")
        gl, gr = xl + il, xr - ir             # the gable's own corners (the front's unless inset)
        xc = (gl + gr) / 2
        up = float(g["upstand_m"])
        cw, ch, cp = (float(g["coping"][k]) for k in ("width_m", "height_m", "proud_m"))
        kw, ko = float(g["kneeler"]["width_m"]), float(g["kneeler"]["out_m"])
        zf, zb = p + cp, p + cp - cw          # the copings' front and back (the parapet's back)
        xa, xb = gl + kw, gr - kw             # the kneelers' inner faces
        if not (0.1 <= up <= 0.6 and 0.1 <= ch <= 0.4 and 0.0 <= cp <= 0.15 and 0.01 <= ko <= 0.15):
            raise ValueError(f"{self.v['id']}: gable upstand 0.1-0.6 m, coping 0.1-0.4 m high and 0-0.15 m "
                             f"proud, kneeler 0.01-0.15 m out past the eaves (so its side is not the fascia's)")
        # T-3047: on a shallow projection the copings are wider than it is deep, so the gable is
        # a solid parapet carried back through the wall plane to the copings' back, with no roof
        # in front of the plane; its host closes nothing over the wall top
        shallow = bool(self.v.get("shallow"))
        chamfer = self.v["plan"].get("side_end")   # T-3048: a chamfered return, on a shallow one
        if not ((zb <= -0.05 if shallow else 0.05 <= zb) and zb <= p - 0.1 and 0.1 <= kw and xa <= xc - 0.5):
            raise ValueError(f"{self.v['id']}: the coping's back {zb:.3f} m out stands 0.05 m out of the wall "
                             f"(on a shallow projection 0.05 m behind it) and 0.1 m behind the front, and the "
                             f"kneelers leave the gable a metre across")
        roof = lambda x: y_e + pitch * (xc - xa - abs(x - xc))
        under = lambda x: roof(x) + up
        top = lambda x: under(x) + ch
        y_r, y_k = roof(xc), top(xa)
        F, B, D = (0.0, 0.0, 1.0), (0.0, 0.0, -1.0), (0.0, -1.0, 0.0)
        # the roof's two slopes, kneeler to ridge, from the parapet's back to the wall plane
        for xs in (xa, xb) if not shallow else ():
            world.face("roof", [(xs, y_e, 0.0), (xc, y_r, 0.0), (xc, y_r, zb), (xs, y_e, zb)], Y)
        if shallow:
            # the parapet's underside over the wall top, from its back to the front, corner to
            # corner (past them the kneelers' own)
            world.face("band", [(xl, y_top, zb), (xr, y_top, zb), (xr, y_top, p), (xl, y_top, p)], D)
        # the gable: the front carried up from the wall top to the copings' beds
        world.face("wall", [(xa, y_top, p), (xb, y_top, p), (xb, under(xb), p), (xc, under(xc), p),
                            (xa, under(xa), p)], F)
        for xs in (xa, xb):
            n = (-1.0 if xs < xc else 1.0, 0.0, 0.0)
            # the parapet's back over the roof (a shallow one's from the wall top)
            y_b = (lambda x: y_top) if shallow else roof
            world.face("band", [(xs, y_b(xs), zb), (xc, y_b(xc), zb), (xc, under(xc), zb), (xs, under(xs), zb)], B)
            # the coping, kneeler to apex: its top, its bed's overhang, its front and its back
            world.face("band", [(xs, top(xs), zb), (xc, top(xc), zb), (xc, top(xc), zf), (xs, top(xs), zf)],
                       _add(Y, _mul(n, pitch)))
            world.face("band", [(xs, under(xs), p), (xc, under(xc), p), (xc, under(xc), zf), (xs, under(xs), zf)], D)
            world.face("band", [(xs, under(xs), zf), (xc, under(xc), zf), (xc, top(xc), zf), (xs, top(xs), zf)], F)
            world.face("band", [(xs, under(xs), zb), (xc, under(xc), zb), (xc, top(xc), zb), (xs, top(xs), zb)], B)
        # the kneelers, over the plan's front corners; their backs over the eaves line only,
        # where a host closes a projection's back from its wall top to its eaves
        knees = ((xl - ov - ko, xa), (xb, xr + ov + ko))
        for (a, b), (e0, e1) in zip(knees, ((xl - ov, xl), (xr, xr + ov))):
            if shallow:   # T-3047: carried back with the parapet, its back and underside its own
                self._block(world, "band", a, b, y_top, y_k, zb, zf, under=False)
                k0, k1 = (a, xl) if a < xl else (xr, b)
                # T-3048: over a chamfer it oversails the canted face, so its underside runs
                # out to the front's plane (the chamfer has no eaves of its own)
                zc = p if (a < xl and chamfer == "left") or (a >= xl and chamfer == "right") else 0.0
                world.face("band", [(k0, y_top, zb), (k1, y_top, zb), (k1, y_top, zc), (k0, y_top, zc)], D)
            else:
                self._block(world, "band", a, b, y_top, y_k, 0.0, zf, back_from=y_e, under=False)
            # its underside where the return's soffit is not: out past the fascia, and proud
            # of the front
            world.face("band", [(a, y_top, p), (b, y_top, p), (b, y_top, zf), (a, y_top, zf)], D)
            o0, o1 = (a, e0) if a < e0 else (e1, b)
            if shallow:   # T-3047: past the return's fascia on either side (its parapet's is the rest)
                o0, o1 = (a, e0) if a < xl else (e1, b)
            if not ((a < xl and chamfer == "left") or (a >= xl and chamfer == "right")):
                world.face("band", [(o0, y_top, 0.0), (o1, y_top, 0.0), (o1, y_top, p), (o0, y_top, p)], D)
        meta = {"kind": "gable", "pitch": pitch, "planes": 0 if shallow else 2, "apex": [round(xc, 4), round(y_r, 4), 0.0],
                "ridge_m": round(y_r, 4), "kneeler_m": round(y_k, 4), "gable_top_m": round(top(xc), 4)}
        if g.get("panel"):
            meta["panel"] = self._gable_panel(world, g["panel"], xa, xb, xc, y_top, under, p, pitch)
        zm = (zb + zf) / 2
        pn = g.get("pinnacle")
        if pn:
            w, sh, cap = (float(pn[k]) for k in ("width_m", "shaft_m", "cap_m"))
            if not (w <= min(cw, xa - xl + ov + ko) - 0.04 and 0.1 <= sh <= 2.0 and 0.1 <= cap <= 1.5):
                raise ValueError(f"{self.v['id']}: a pinnacle stands inside its kneeler, its shaft 0.1-2 m "
                                 f"and its cap 0.1-1.5 m")
            # over the kneelers' middles, or on an inset gable over its own corners' kneelers
            spots = [(a + b) / 2 for a, b in knees] if not (il or ir) else [gl + kw / 2, gr - kw / 2]
            for x in spots:
                self._spike(world, x, zm, w, y_k, sh, cap)
            meta["pinnacle_top_m"] = round(y_k + sh + cap, 4)
        fn = g.get("finial")
        if fn:
            w, sh, cap = (float(fn[k]) for k in ("width_m", "shaft_m", "cap_m"))
            if not (w <= cw - 0.04 and 0.05 <= sh <= 1.0 and 0.1 <= cap <= 1.5):
                raise ValueError(f"{self.v['id']}: a gable's finial stands on its copings, its block 0.05-1 m "
                                 f"and its cap 0.1-1.5 m")
            # its block seated down the copings' slope to where both rakes are under it
            self._spike(world, xc, zm, w, top(xc) - pitch * w / 2, sh + pitch * w / 2, cap)
            meta["finial_top_m"] = round(top(xc) + sh + cap, 4)
        self.meta["roof"] = meta

    def _gable_panel(self, world, pn, xa, xb, xc, y_top, under, p, pitch):
        """T-3002: the carved panel filling a gable's tympanum (1801's south pavilion: a tall
        leafy relief up the gable to its apex, the Taylor photograph). A dressed panel
        `proud_m` out of the gable's face, `border_m` in from the copings' beds and between
        the kneelers, from `base_m` over the wall top; on it a STEM `stem_m` wide up its
        middle, a pair of LEAVES at every `pitch_m` up it, each a lozenge leaning out and up
        from the stem and as long as the panel lets it be (`leaf_m` at most, `margin_m` clear
        of the panel's edge), a lozenge BOSS at its foot and a FLEURON at its head, all
        standing the relief's `proud_m` past the panel. The light tier keeps the panel."""
        keys = {"border_m", "base_m", "proud_m", "relief"}
        rk = {"proud_m", "stem_m", "leaf_m", "pitch_m", "margin_m"}
        fk = {"kind", "proud_m", "rays", "ring_m", "hub_m", "margin_m"}   # T-1890: a fan
        rl = pn.get("relief") if isinstance(pn, dict) else None
        fan = isinstance(rl, dict) and rl.get("kind") == "fan"
        if not isinstance(rl, dict) or set(pn) != keys or set(rl) != (fk if fan else rk):
            raise ValueError(f"{self.v['id']}: a gable panel takes {sorted(keys)}, its relief {sorted(rk)}")
        b, base, pr = float(pn["border_m"]), float(pn["base_m"]), float(pn["proud_m"])
        if fan:
            return self._fan_panel(world, b, base, pr, rl, xa, xb, xc, y_top, under, p, pitch)
        rp, sw, lm, pm, mg = (float(rl[k]) for k in ("proud_m", "stem_m", "leaf_m", "pitch_m", "margin_m"))
        if not (0.05 <= b <= 0.3 and 0.0 <= base <= 0.5 and 0.01 <= pr <= 0.06 and 0.01 <= rp <= 0.06
                and 0.04 <= sw <= 0.2 and 0.15 <= lm <= 0.8 and 0.15 <= pm <= 0.8 and 0.02 <= mg <= 0.15):
            raise ValueError(f"{self.v['id']}: a gable panel's border 0.05-0.3 m, base 0-0.5 m, proud 0.01-0.06 m; "
                             f"its relief 0.01-0.06 m proud, stem 0.04-0.2 m, leaves and pitch 0.15-0.8 m, "
                             f"margin 0.02-0.15 m")
        dn = b * math.sqrt(1.0 + pitch * pitch)          # the border, measured down a rake
        left = lambda x: under(xa) - dn + pitch * (x - xa)   # each rake's bed, `border_m` in
        right = lambda x: under(xb) - dn + pitch * (xb - x)
        y_b, apex = y_top + base, left(xc)
        poly = [(xa + b, y_b), (xb - b, y_b), (xb - b, apex + 1.0), (xa + b, apex + 1.0)]
        poly = clip_half(clip_half(poly, lambda q: left(q[0]) - q[1]), lambda q: right(q[0]) - q[1])
        if apex - y_b < 1.0:
            raise ValueError(f"{self.v['id']}: a gable panel needs a metre over its base")
        world.plane("band", poly, -(p + pr))
        world.tube("band", poly, -p, -(p + pr), inward=False)
        meta = {"y_m": [round(y_b, 4), round(apex, 4)], "leaves": 0}
        if self.tier == "light":
            return meta
        z0 = -(p + pr)

        def lay(q, k=1.0):   # stood `k` of the relief's proud past the panel
            world.plane("band", q, z0 - k * rp)
            world.tube("band", q, z0, z0 - k * rp, inward=False)

        def half(y):   # the panel's half-width at height y, short of its margin
            return xc - max(xa + b, xa + (y - left(xa)) / pitch) - mg

        y0, top = y_b + mg, apex - mg
        lay([(xc, y0), (xc + 2 * sw, y0 + 2 * sw), (xc, y0 + 4 * sw), (xc - 2 * sw, y0 + 4 * sw - 2 * sw)])
        hf = (top - y0) * 0.12                               # the fleuron's height, under the apex
        stem = [(xc - sw / 2, y0 + 4 * sw), (xc + sw / 2, y0 + 4 * sw), (xc + sw / 2, top - hf), (xc - sw / 2, top - hf)]
        lay(stem)
        fw = min(3 * sw, 2 * max(half(top - hf / 2), sw / 2))
        lay([(xc, top - hf), (xc + fw / 2, top - hf / 2), (xc, top), (xc - fw / 2, top - hf / 2)])
        n, y = 0, y0 + 4 * sw + pm / 2
        while y < top - hf - 0.05:
            rise, wl = 0.5, 0.9                               # a leaf climbs half its length; its width
            L = min(lm, half(y + rise * lm) - sw / 2)
            if L < 0.12:
                break
            for sg in (-1.0, 1.0):
                x0 = xc + sg * sw / 2
                tip = (x0 + sg * L, y + rise * L)
                mid = lambda t, o: (x0 + sg * L * t - sg * o * rise, y + rise * L * t + o)
                # leaves overlap the next two up their side, so each of three stands its own depth
                lay(sorted([(x0, y), mid(0.45, wl * L / 2), tip, mid(0.55, -wl * L / 2)],
                           key=lambda q: math.atan2(q[1] - (y + rise * L / 2), q[0] - (x0 + sg * L / 2))),
                    (0.8, 0.65, 0.5)[n % 3])
            n += 1
            y += pm
        meta["leaves"] = 2 * n
        return meta

    def _fan_panel(self, world, b, base, pr, rl, xa, xb, xc, y_top, under, p, pitch):
        """T-1890: a gable panel carved as a FAN (1801's 18th Street wall dormer, a sunburst in
        both the Taylor print and HABS photograph 2): the dressed panel as `_gable_panel` lays
        it, and on it a half wheel standing on the panel's foot on its axis, as large as the
        panel holds `margin_m` clear of its sides and rakes: a RING `ring_m` deep round its
        arc, `rays` RAYS between it and a half-disc HUB `hub_m` across, each narrowing to the
        hub, all standing the relief's `proud_m` past the panel. The light tier keeps the panel."""
        rp, n, rm, hm, mg = (float(rl["proud_m"]), int(rl["rays"]), float(rl["ring_m"]), float(rl["hub_m"]),
                             float(rl["margin_m"]))
        if not (0.05 <= b <= 0.3 and 0.0 <= base <= 0.5 and 0.01 <= pr <= 0.06 and 0.01 <= rp <= 0.06
                and 5 <= n <= 31 and 0.03 <= rm <= 0.2 and 0.05 <= hm <= 0.4 and 0.0 <= mg <= 0.15):
            raise ValueError(f"{self.v['id']}: a fan panel's border 0.05-0.3 m, base 0-0.5 m, proud 0.01-0.06 m; "
                             f"its relief 0.01-0.06 m proud, 5-31 rays, ring 0.03-0.2 m, hub 0.05-0.4 m, "
                             f"margin 0-0.15 m")
        dn = b * math.sqrt(1.0 + pitch * pitch)
        left = lambda x: under(xa) - dn + pitch * (x - xa)
        right = lambda x: under(xb) - dn + pitch * (xb - x)
        y_b, apex = y_top + base, left(xc)
        poly = [(xa + b, y_b), (xb - b, y_b), (xb - b, apex + 1.0), (xa + b, apex + 1.0)]
        poly = clip_half(clip_half(poly, lambda q: left(q[0]) - q[1]), lambda q: right(q[0]) - q[1])
        if apex - y_b < 1.0:
            raise ValueError(f"{self.v['id']}: a gable panel needs a metre over its base")
        world.plane("band", poly, -(p + pr))
        world.tube("band", poly, -p, -(p + pr), inward=False)
        R = min(xc - (xa + b), (apex - y_b) / math.sqrt(1.0 + pitch * pitch)) - mg
        if R < hm + rm + 0.1:
            raise ValueError(f"{self.v['id']}: a fan panel's wheel ({R:.3f} m) does not clear its hub and ring")
        meta = {"y_m": [round(y_b, 4), round(apex, 4)], "fan": {"radius_m": round(R, 4), "rays": n}}
        if self.tier == "light":
            return meta
        z0 = -(p + pr)

        def lay(q, k=1.0):
            world.plane("band", q, z0 - k * rp)
            world.tube("band", q, z0, z0 - k * rp, inward=False)

        at = lambda r, t: (xc + r * math.cos(t), y_b + r * math.sin(t))
        seg = 2 * n
        z1 = z0 - rp
        for j in range(seg):   # the ring: its face a quad a step round the arc, its sides once round
            t0, t1 = math.pi * j / seg, math.pi * (j + 1) / seg
            world.plane("band", [at(R - rm, t0), at(R, t0), at(R, t1), at(R - rm, t1)], z1)
        world.tube("band", [at(R, math.pi * j / seg) for j in range(seg + 1)]
                   + [at(R - rm, math.pi * j / seg) for j in range(seg, -1, -1)], z0, z1, inward=False)
        lay([at(hm, math.pi * j / seg) for j in range(seg + 1)])   # the hub
        half = math.pi / n * 0.3                       # a ray's half-width at the ring, in angle
        for i in range(n):   # each ray clear of the hub and the ring by 5 mm, so no side is shared
            t = math.pi * (i + 0.5) / n
            r0, r1 = hm + 0.005, R - rm - 0.005
            lay([at(r0, t - half * 0.25), at(r1, t - half), at(r1, t + half), at(r0, t + half * 0.25)], 0.7)
        return meta

    def _block(self, world, role, x0, x1, y0, y1, z0, z1, back_from=None, under=True):
        """T-2998: a closed stone block, square to the bay's frame; its back on z0 from
        `back_from` up when a host closes the rest, and no underside where the caller lays
        its own."""
        Lx, Rx = (-1.0, 0.0, 0.0), (1.0, 0.0, 0.0)
        world.face(role, [(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)], (0.0, 0.0, 1.0))
        world.face(role, [(x0, y1, z0), (x1, y1, z0), (x1, y1, z1), (x0, y1, z1)], Y)
        if under:
            world.face(role, [(x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1)], (0.0, -1.0, 0.0))
        world.face(role, [(x0, y0, z0), (x0, y0, z1), (x0, y1, z1), (x0, y1, z0)], Lx)
        world.face(role, [(x1, y0, z0), (x1, y0, z1), (x1, y1, z1), (x1, y1, z0)], Rx)
        yb = y0 if back_from is None else back_from
        world.face(role, [(x0, yb, z0), (x1, yb, z0), (x1, y1, z0), (x0, y1, z0)], (0.0, 0.0, -1.0))

    def _spike(self, world, x, z, w, y0, sh, cap):
        """T-2998: a pinnacle or a gable's finial: a square shaft `w` across from y0 up `sh`,
        under a square pyramid `cap` high; its foot sits on the stone it stands on."""
        h = w / 2
        ring = [(x - h, z - h), (x + h, z - h), (x + h, z + h), (x - h, z + h)]
        y1, tip = y0 + sh, (x, y0 + sh + cap, z)
        for (ax, az), (bx, bz) in zip(ring, ring[1:] + ring[:1]):
            n = ((ax + bx) / 2 - x, 0.0, (az + bz) / 2 - z)    # out of the shaft's middle
            world.face("band", [(ax, y0, az), (bx, y0, bz), (bx, y1, bz), (ax, y1, az)], n)
            world.face("band", [(ax, y1, az), (bx, y1, bz), tip], _add(n, Y))

    def _eaves_outline(self, ov):
        """The plan's eaves line: each run's line offset `ov` out, from where the first meets
        the wall plane to where the last does, through the corners between them."""
        lines = [((a[0] + ov * n[0], a[1] + ov * n[1]), (-n[0], -n[1])) for a, e, n in self.plan["lines"]]
        return [self._offset_corner(None, lines[0], ov)] + \
            [self._offset_corner(lines[i], lines[i + 1], ov) for i in range(len(lines) - 1)] + \
            [self._offset_corner(lines[-1], None, ov)]

    def _spire(self, world, y_e, ov, rise):
        """T-2778: a polygonal cone. Every plane runs from one run's eaves line up to a single
        apex `rise` over the eaves, on the wall plane over the middle of the plan, so the
        planes meet on hips that all run to it (a hip at one pitch would end in a ridge
        along the wall instead). Its back, the triangle on the wall plane under the apex,
        is closed: against a wall it is the wall's own face, and over a house's eave
        (`_back`) nothing else stands there."""
        if self.plan["kind"] != "polyline" or self.v["kind"] != "oriel":
            raise ValueError(f"{self.v['id']}: a spire stands on an oriel's straight runs")
        if not 0.5 <= rise <= 6.0:
            raise ValueError(f"{self.v['id']}: a spire rises 0.5-6 m over its eaves, not {rise}")
        dom = self._eaves_outline(ov)
        # the apex stands the finial's radius off the wall plane, so the finial's shaft does too
        # T-3007: or over the point the roof names (`apex_m` along the wall), where a plan is
        # not symmetric (1811's oriel, its apex over its front's middle on the 1888 plate)
        ax = self.v["roof"].get("apex_m")
        if ax is not None and not dom[0][0] + 0.3 <= float(ax) <= dom[-1][0] - 0.3:
            raise ValueError(f"{self.v['id']}: a spire's apex_m {ax} stands 0.3 m inside its eaves' ends")
        apex = ((dom[0][0] + dom[-1][0]) / 2 if ax is None else float(ax), y_e + rise,
                part(self.v, self.data, "finial")["radius_m"] if self.v["roof"].get("finial") else 0.0)
        for a, b in zip(dom, dom[1:]):
            world.face("roof", [(a[0], y_e, a[1]), (b[0], y_e, b[1]), apex], Y)
        self._spire_back = (dom[0][0], dom[-1][0], apex)
        if self.v.get("back_from_m") is None:
            world.face("roof_back", [(dom[-1][0], y_e, 0.0), (dom[0][0], y_e, 0.0), apex], (0.0, 0.0, -1.0))
        self.meta["roof"] = {"kind": "spire", "rise_m": rise, "planes": len(dom) - 1,
                             "apex": [round(c, 4) for c in apex]}

    def _back(self, world, y_b, y_top, y_e):
        """T-2778: an oriel carried up through its house's eave has no wall behind it over that
        eave, so its back is closed on the wall plane, in its own walling, from `y_b` (the
        house's wall head, where the house's roof leaves the wall) up: behind its walls to
        their top, behind its eaves to their line, and under its spire to the apex. Cut at
        the junctions and at the eaves' ends, so no edge of it ends on another's middle.

        T-2989: a wall top UNDER `y_b` (1811's oriel, its cornice under its house's eave
        datum) has no back to its walls to close, since the house's own wall stands behind
        them to `y_b`: the back is closed behind its eaves from `y_b` (if they rise past
        it) and under its spire from its eaves line."""
        if not hasattr(self, "_spire_back"):
            raise ValueError(f"{self.v['id']}: only an oriel under a spire is carried through an eave")
        jl, jr = self.runs[0].world(0.0, 0.0, 0.0)[0], self.runs[-1].world(self.runs[-1].L, 0.0, 0.0)[0]
        el, er, apex = self._spire_back
        under = y_top <= y_b
        if not el < jl < jr < er or not (y_b < y_top - 0.3 or under):
            raise ValueError(f"{self.v['id']}: its back from {y_b} m needs the wall top at least 0.3 m over it, "
                             f"or under it")
        B = (0.0, 0.0, -1.0)
        q = lambda x0, x1, y0, y1: [(x1, y0, 0.0), (x0, y0, 0.0), (x0, y1, 0.0), (x1, y1, 0.0)]
        if not under:
            world.face("roof_back", q(jl, jr, y_b, y_top), B)
        for x0, x1 in ((el, jl), (jl, jr), (jr, er)):
            if not under or y_b < y_e:
                world.face("roof_back", q(x0, x1, y_b if under else y_top, y_e), B)
            world.face("roof_back", [(x1, y_e, 0.0), (x0, y_e, 0.0), apex], B)
        self.meta["back"] = {"from_m": round(y_b, 4), "to_m": round(apex[1], 4)}

    def _corner_back(self, world, y_b, y_top, y_e, ov):
        """T-3176: a tower set across its house's corner has no wall behind it over the house's
        wall head (`y_b`), on either of the two planes that cut its ring: there it is closed in
        its own walling, on the wall's plane (z = 0) from its first junction to the corner and on
        the side wall's plane (x = 0) from the corner to its last, up to its wall top; then out
        to its eaves' ends under its soffit, to the eaves line; and its whole cap, which stands
        over the house's roof behind those planes, is closed under the part of it there."""
        if not self.plan.get("across_corner") or not y_b < y_top - 0.3:
            raise ValueError(f"{self.v['id']}: only a tower across its corner is closed on its corner, "
                             f"its wall top at least 0.3 m over {y_b} m")
        right = self.plan["across_corner"] == "right"
        first, last = self.runs[0], self.runs[-1]
        # where its walls and its eaves meet each plane
        wall_x = (first.world(0.0, 0.0, 0.0) if right else last.world(last.L, 0.0, 0.0))[0]
        side_z = (last.world(last.L, 0.0, 0.0) if right else first.world(0.0, 0.0, 0.0))[2]
        ew = first.world(first.s_start(ov), 0.0, ov) if right else last.world(last.s_end(ov), 0.0, ov)
        es = last.world(last.s_end(ov), 0.0, ov) if right else first.world(first.s_start(ov), 0.0, ov)
        eave_x, eave_z = ew[0], es[2]
        F, S = (0.0, 0.0, -1.0), ((-1.0 if right else 1.0), 0.0, 0.0)
        for x0, y0, y1 in ((wall_x, y_b, y_top), (eave_x, y_top, y_e)):
            world.face("roof_back", [(x0, y0, 0.0), (0.0, y0, 0.0), (0.0, y1, 0.0), (x0, y1, 0.0)], F)
        for z0, y0, y1 in ((side_z, y_b, y_top), (eave_z, y_top, y_e)):
            world.face("roof_back", [(0.0, y0, z0), (0.0, y0, 0.0), (0.0, y1, 0.0), (0.0, y1, z0)], S)
        ring = self.plan["ring"]
        c = self.plan["centre"]
        k = len(ring)
        R = math.hypot(ring[0][0] - c[0], ring[0][1] - c[1])
        Re = R + ov / math.cos(math.pi / k)
        dom = [(c[0] + (q[0] - c[0]) * Re / R, c[1] + (q[1] - c[1]) * Re / R) for q in ring]
        under = clip_half(clip_half(dom, lambda p: -p[1]), (lambda p: -p[0]) if right else (lambda p: p[0]))
        if len(under) >= 3:
            world.face("soffit", [(p[0], y_e, p[1]) for p in under], (0.0, -1.0, 0.0))
        self.meta["back"] = {"from_m": round(y_b, 4), "to_m": round(y_e, 4), "corner": self.plan["across_corner"]}

    def _back_over(self, world, bo):
        """T-3007: where the host's wall is not on the wall plane behind the bay (1811's oriel,
        its south return carried out over the entrance block's rounded corner on the 1888
        plate), its back is closed on that plane, in its own walling, over `x` along the wall
        and from `y` to `y`: so no one looking up the gap between it and the round sees into
        it. The host says where (k01_frontage.bay); the face stands inside the bay's plan."""
        (x0, x1), (y0, y1) = (tuple(map(float, bo["x"])), tuple(map(float, bo["y"])))
        jl, jr = self.runs[0].world(0.0, 0.0, 0.0)[0], self.runs[-1].world(self.runs[-1].L, 0.0, 0.0)[0]
        if not jl - 1e-9 <= x0 < x1 <= jr + 1e-9 or not y0 < y1:
            raise ValueError(f"{self.v['id']}: its back over x {x0}..{x1} from {y0} to {y1} m stands "
                             f"outside its junctions ({jl:.3f}..{jr:.3f})")
        world.face("roof_back", [(x1, y0, 0.0), (x0, y0, 0.0), (x0, y1, 0.0), (x1, y1, 0.0)], (0.0, 0.0, -1.0))
        self.meta["back_over"] = {"x": [round(x0, 4), round(x1, 4)], "y": [round(y0, 4), round(y1, 4)]}

    def _frieze(self, flat, run, y0, y1, fr, band_h, framed_above):
        """T-2778: a windowless storey's carved frieze on one run, between the floor bands
        that bound it: a dressed panel `proud_m` out, `border_m` in from the run's ends
        (the stiles) and from the bands, and on it a guilloche, rings of `ring_width_m` laid
        along the panel's middle at `pitch` of their radius, every other one standing
        `ring_proud_m` and the rest half that, so where two cross one passes over the
        other. The light tier keeps the panel and drops the rings."""
        b, pr = float(fr["border_m"]), float(fr["proud_m"])
        lo = y0 + band_h / 2 + b / 2
        hi = y1 - (band_h / 2 if framed_above else 0.0) - b / 2
        s0, s1 = b, run.L - b
        if s1 - s0 < 0.2 or hi - lo < 0.2:
            raise ValueError(f"{self.v['id']}: a {run.L:.2f} by {y1 - y0:.2f} m frieze leaves no panel")
        rect_ = rect(s0, s1, lo, hi)
        flat.plane("band", rect_, -pr)
        flat.tube("band", rect_, 0.0, -pr, inward=False)
        self.meta.setdefault("frieze", {"panels": 0, "rings": 0})["panels"] += 1
        if self.tier == "light":
            return
        self.meta["frieze"]["rings"] += self._guilloche(flat, s0, s1, lo, hi, fr["guilloche"], pr)

    def _cap_band(self, flat, run, y_top, cb):
        """T-2815: a carved band round the bay under its cap (Keith's bow on the 1888 plate:
        a dark carved band under the cap's light top): a dressed strip `height_m` deep
        under the eaves moulding's seat, `proud_m` out along the whole run, carrying the
        frieze's guilloche. Its top stands 2 mm under the seat, whose own underside the
        moulding draws (mitred at the run's ends, so the two would overlap on one plane).
        The light tier keeps the strip and drops the rings."""
        h, pr = float(cb["height_m"]), float(cb["proud_m"])
        lo, hi = y_top - h, y_top - 0.002
        rect_ = rect(0.0, run.L, lo, hi)
        flat.plane("band", rect_, -pr)
        flat.tube("band", rect_, 0.0, -pr, inward=False)
        m = self.meta.setdefault("cap_band", {"y_m": [round(lo, 4), round(hi, 4)], "rings": 0})
        if self.tier == "light":
            return
        m["rings"] += self._guilloche(flat, 0.0, run.L, lo, hi, cb["guilloche"], pr)

    def _guilloche(self, flat, s0, s1, lo, hi, g, pr):
        """Rings of `ring_width_m` laid along a panel's middle at `pitch` of their radius,
        every other one standing `ring_proud_m` and the rest half that, so where two cross
        one passes over the other; returns how many."""
        w, rp, k = float(g["ring_width_m"]), float(g["ring_proud_m"]), int(g["segments"])
        R = min(float(g["radius_m"]), (hi - lo) / 2 - float(g["margin_m"]), (s1 - s0) / 2 - float(g["margin_m"]))
        if R < 2 * w:
            raise ValueError(f"{self.v['id']}: a frieze panel {hi - lo:.2f} m high holds no ring")
        pitch = float(g["pitch"]) * R
        n = max(1, math.floor((s1 - s0 - 2 * R - 2 * g["margin_m"]) / pitch + 1e-9) + 1)
        sc = (s0 + s1) / 2 - (n - 1) * pitch / 2
        yc = (lo + hi) / 2
        for j in range(n):
            self._ring(flat, sc + j * pitch, yc, R, w, k, -pr, -pr - (rp if j % 2 == 0 else rp / 2))
        return n

    @staticmethod
    def _ring(flat, cs, yc, R, w, k, d0, d1):
        """One ring of `k` segments, `w` wide inside radius R, standing from depth d0 out to d1."""
        ring_ = lambda r, t: (cs + r * math.cos(2 * math.pi * t / k), yc + r * math.sin(2 * math.pi * t / k))
        for t in range(k):
            o0, o1, i0, i1 = ring_(R, t), ring_(R, t + 1), ring_(R - w, t), ring_(R - w, t + 1)
            flat.plane("band", [o0, o1, i1, i0], d1)
            mo = ((o0[0] + o1[0]) / 2 - cs, (o0[1] + o1[1]) / 2 - yc, 0.0)
            flat.face("band", [flat.P(*o0, d0), flat.P(*o1, d0), flat.P(*o1, d1), flat.P(*o0, d1)], mo)
            flat.face("band", [flat.P(*i1, d0), flat.P(*i0, d0), flat.P(*i0, d1), flat.P(*i1, d1)],
                      (-mo[0], -mo[1], 0.0))

    @staticmethod
    def _loop(flat, role, cs, yc, R, w, k, d0, d1, back=True):
        """T-3092: a ring of `k` segments, `w` wide inside radius R, its front at depth d0 and
        its back at d1 (a free ring, a roundel on a bar), or with no back (`back` False) standing
        from the face it is set on, d1 4 mm into it, as a carved boss does."""
        ring_ = lambda r, t: (cs + r * math.cos(2 * math.pi * t / k), yc + r * math.sin(2 * math.pi * t / k))
        for t in range(k):
            o0, o1, i0, i1 = ring_(R, t), ring_(R, t + 1), ring_(R - w, t), ring_(R - w, t + 1)
            flat.plane(role, [o0, o1, i1, i0], d0)
            if back:
                flat.plane(role, [i0, i1, o1, o0], d1, (0.0, 0.0, -1.0))
            mo = ((o0[0] + o1[0]) / 2 - cs, (o0[1] + o1[1]) / 2 - yc, 0.0)
            flat.face(role, [flat.P(*o0, d0), flat.P(*o1, d0), flat.P(*o1, d1), flat.P(*o0, d1)], mo)
            flat.face(role, [flat.P(*i1, d0), flat.P(*i0, d0), flat.P(*i0, d1), flat.P(*i1, d1)],
                      (-mo[0], -mo[1], 0.0))

    def _head_frieze(self, flat, run, y_floor, hf):
        """T-3002: a dressed band across the run over a storey's windows (1801's south pavilion,
        the Taylor photograph: under the gable's shelf, over the third storey's pair): `proud_m`
        out from `from_m` to `to_m` over the storey's floor, `border_m` in from the run's ends
        (clear of the pilasters there), and on it a ROUNDEL at `at` along the run, a ring
        `ring_m` wide round a boss, both standing `proud_m` past the band. The light tier
        keeps the band and drops the roundel."""
        b, pr = float(hf["border_m"]), float(hf["proud_m"])
        lo, hi = y_floor + float(hf["from_m"]), y_floor + float(hf["to_m"])
        s0, s1 = b, run.L - b
        if s1 - s0 < 0.5:
            raise ValueError(f"{self.v['id']}: a {run.L:.2f} m run leaves its head frieze no band")
        band_ = rect(s0, s1, lo, hi)
        flat.plane("band", band_, -pr)
        flat.tube("band", band_, 0.0, -pr, inward=False)
        m = {"run": hf["run"], "y_m": [round(lo, 4), round(hi, 4)], "s_m": [round(s0, 4), round(s1, 4)]}
        self.meta["head_frieze"] = m
        if self.tier == "light":
            return
        rd = hf["roundel"]
        R, w, rp, k = float(rd["radius_m"]), float(rd["ring_m"]), float(rd["proud_m"]), int(rd["segments"])
        cs, yc = run.L * float(hf["at"]), (lo + hi) / 2
        if not (R <= (hi - lo) / 2 - 0.02 and s0 + 0.02 <= cs - R and cs + R <= s1 - 0.02 and w < R - 0.02):
            raise ValueError(f"{self.v['id']}: the head frieze's roundel ({R} m) does not stand inside its band")
        self._ring(flat, cs, yc, R, w, k, -pr, -pr - rp)
        boss = [(cs + (R - w - 0.01) * math.cos(2 * math.pi * t / k), yc + (R - w - 0.01) * math.sin(2 * math.pi * t / k))
                for t in range(k)]
        flat.plane("band", boss, -pr - rp * 0.6)
        flat.tube("band", boss, -pr, -pr - rp * 0.6, inward=False)
        m["roundel"] = {"s_m": round(cs, 4), "y_m": round(yc, 4), "radius_m": R}

    def _flare_bands(self, reg, Li, d, y_e, pitch, flare):
        """T-2408: one plane of a flared hip. Its slope runs from `eave_pitch` at the eaves up
        to the roof's `pitch` at `over_m` in from them, and on at that pitch beyond, so the
        profile is a parabola then a line; the plane is cut into `bands` strips at fixed
        distances in from the eaves, each strip flat between the profile's heights at its
        edges. Every plane is cut at the same distances, so each cut meets its neighbour's on
        the hip between them and the planes still share their hips vertex for vertex."""
        a, b, L = flare["eave_pitch"], pitch, flare["over_m"]
        n = flare["bands"] if self.tier == "full" else max(2, flare["bands"] // 2)
        g = lambda t: (a * t + (b - a) * t * t / (2 * L)) if t <= L else (a * L + (b - a) * L / 2 + b * (t - L))
        top = max(d(Li, p) for p in reg)
        cuts = [L * k / n for k in range(n + 1)]
        cuts = [c for c in cuts if c < top - 1e-6] + [max(top, L)]
        out = []
        for lo, hi in zip(cuts, cuts[1:]):
            piece = clip_half(clip_half(reg, lambda p: d(Li, p) - lo), lambda p: hi - d(Li, p))
            if len(piece) < 3 or abs(area(piece)) < 1e-8:
                continue
            g0, g1 = g(lo), g(hi)
            out.append((piece, lambda p, lo=lo, hi=hi, g0=g0, g1=g1: y_e + g0 + (g1 - g0) * (d(Li, p) - lo) / (hi - lo)))
        return out

    def _mansard_bands(self, reg, Li, d, y_e, pitch, mn):
        """T-2964: one plane of a bay's mansard (1816 Prairie's two canted bays carried up through
        the cornice under their own crowns, the Chicagology photograph). From the eaves the
        lower face rises `rise_m` at `lower_pitch_deg` to the curb, and over the curb the deck
        runs on at the roof's `pitch`. Every plane is cut at the same distance in from the
        eaves, so the cuts meet on the hips and the planes share them vertex for vertex; the
        back is closed on the wall plane (`_hip`), where the house's own roof stands behind."""
        r, deg = float(mn["rise_m"]), float(mn["lower_pitch_deg"])
        if not 1.0 <= r <= 6.0 or not 60.0 <= deg <= 85.0 or not 0.0 <= pitch <= 0.4:
            raise ValueError(f"{self.v['id']}: a mansard rises 1.0-6.0 m at 60-85 deg to a deck pitched 0-0.4")
        run = r / math.tan(math.radians(deg))
        out = []
        for lo, hi, g0, k in ((0.0, run, 0.0, r / run), (run, 1e6, r, pitch)):
            piece = clip_half(clip_half(reg, lambda p: d(Li, p) - lo), lambda p: hi - d(Li, p))
            if len(piece) < 3 or abs(area(piece)) < 1e-8:
                continue
            out.append((piece, lambda p, lo=lo, g0=g0, k=k: y_e + g0 + k * (d(Li, p) - lo)))
        return out

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
        leans on the wall, a tower's is whole and closed at the back where the wall cuts it.
        T-2900: a corner turret's (`cap_whole`, its eaves at its wing's and its centre maybe
        behind the wall's face) is not cut at all: it stands whole over the wing's roof."""
        c, R = self.plan["centre"], self.plan["R"]
        whole = bool(self.v.get("cap_whole"))
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
            if whole:
                return 0.0, Re
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

    def _deck_cresting(self, world, top, y_d, cr):
        """T-3176: the deck's cresting, an iron band `height_m` tall and `thickness_m` thick
        standing on the deck's edge all round (1827's tower, the Doane photograph), and a post
        at each of its corners carrying a finial (`_finial`)."""
        h, t = float(cr["height_m"]), float(cr["thickness_m"])
        if not (0.2 <= h <= 1.2 and 0.02 <= t <= 0.2):
            raise ValueError(f"{self.v['id']}: a deck's cresting is 0.2-1.2 m tall and 0.02-0.2 m thick")
        cx = sum(p[0] for p in top) / len(top)
        cz = sum(p[1] for p in top) / len(top)
        inner = []
        for p in top:
            r = math.hypot(p[0] - cx, p[1] - cz)
            inner.append((cx + (p[0] - cx) * (r - t) / r, cz + (p[1] - cz) * (r - t) / r))
        n = len(top)
        for i in range(n):
            a, b, ai, bi = top[i], top[(i + 1) % n], inner[i], inner[(i + 1) % n]
            m = ((a[0] + b[0]) / 2 - cx, 0.0, (a[1] + b[1]) / 2 - cz)
            world.face("iron", [(a[0], y_d, a[1]), (b[0], y_d, b[1]), (b[0], y_d + h, b[1]), (a[0], y_d + h, a[1])], m)
            world.face("iron", [(ai[0], y_d, ai[1]), (bi[0], y_d, bi[1]), (bi[0], y_d + h, bi[1]),
                                (ai[0], y_d + h, ai[1])], (-m[0], 0.0, -m[2]))
            world.face("iron", [(a[0], y_d + h, a[1]), (b[0], y_d + h, b[1]), (bi[0], y_d + h, bi[1]),
                                (ai[0], y_d + h, ai[1])], Y)
        self.meta["roof"]["cresting"] = {"height_m": h, "thickness_m": t}
        self._finial_at = [(p[0], y_d + h, p[1]) for p in top]

    def _finial(self, world):
        f = part(self.v, self.data, "finial")
        if getattr(self, "_finial_at", None):
            # T-3176: a finial over each corner of a crested deck
            tops = []
            for at in self._finial_at:
                tops.append(self._finial_one(world, at, f))
            self.meta["finial"] = {"top_m": round(max(tops), 4), "count": len(tops)}
            return
        ax, ay, az = self.meta["roof"]["apex"]
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

    def _finial_one(self, world, at, f):
        """T-3176: a finial standing on a point (a crested deck's corner): the turned shaft
        `_finial` lays on an apex, from the point up."""
        ax, ay, az = at
        r0, H = f["radius_m"], f["height_m"]
        k = 8
        ring = lambda r, y: [(ax + r * math.cos(2 * math.pi * j / k), y, az + r * math.sin(2 * math.pi * j / k))
                             for j in range(k)]
        lo, hi = ring(r0, ay - 0.02), ring(r0 * 0.35, ay + H)
        for j in range(k):
            jj = (j + 1) % k
            m = (math.cos(2 * math.pi * (j + 0.5) / k), 0.0, math.sin(2 * math.pi * (j + 0.5) / k))
            world.face("finial", [lo[j], lo[jj], hi[jj], hi[j]], m)
        world.face("finial", hi, Y)
        return ay + H

    # sockets and the specimen's board --------------------------------------------------------
    def _balcony(self, flat, run, y_e, ov, first=True, idx=0):
        """T-2525: an iron rail on the eaves, `inset_m` in from their edge and round the run
        from the wall to the wall: a square post against the wall at each end, a foot rail
        and a top rail between them, and square bars at `pitch_m` under the top rail. Only a
        bow, one arc from the wall to the wall, takes it (k01_frontage_params refuses others);
        T-2780: or a canted bay's flat top, a post at each end of each run, in the bay's dressed
        stone where the balcony names `fabric: stone` (1637's south bay, its balustrade);
        T-2888: or a projection's flat top the same way, round its cheeks and front (1812's).
        T-3092: a rail may carry a stone `panel` in the middle of one run, rising to a pedestal,
        with iron scrolls over its sweeps, and its bars may each carry a `roundel` (1812's)."""
        bl = self.v["balcony"]
        role = "band" if bl.get("fabric") == "stone" else "iron"
        z = ov - bl["inset_m"]
        pm, bm, (rw, rd) = bl["post_m"], bl["bar_m"], bl["rail_m"]
        # T-2888: a projection's runs meet square, where a post ending at the corner would
        # stand its face in the next run's rail end; there the corner post stands centred on
        # the corner and the rails run into it, stopping short of the corner by half their
        # width and half the post's together, halved, so the two runs' rails never meet
        square = self.v["kind"] == "projection"
        tuck = (rw + pm) / 4
        # a stone balustrade's feet stand on a 2 mm bed over the flat roof, not in its plane,
        # and so does an iron rail on a projection's flat top (T-2888)
        y0, y3 = y_e + (0.002 if role == "band" or square else 0.0), y_e + bl["height_m"]
        d0, d1 = -z - pm / 2, -z + pm / 2
        sa, sb = run.s_start(z), run.s_end(z)
        last = run is self.runs[-1]
        p0 = sa if first else None
        p1 = sb - pm if not square or last else sb - pm / 2
        # a canted top's runs meet at its corners, where the run before stood its end post
        for a in (a for a in (p0, p1) if a is not None):
            prism(flat, role, rect(a, a + pm, y0, y3), d0, d1)
        e0 = sa + pm if first or not square else sa + pm / 2
        e1 = sb - pm if not square or last else sb - pm / 2
        r0 = sa + pm / 2 if first or not square else sa + tuck
        r1 = sb - pm / 2 if not square or last else sb - tuck
        # the rails run into the posts' middles, so no end of theirs lies in a post's face
        pn = bl.get("panels")
        # T-2930: a stone balustrade of pierced panels lays its foot rail on the roof as a
        # base course to `foot_rail_m`, where an open balustrade lifts it clear; its bed 3 mm
        # over the posts' own, so the posts it runs into do not share its underside
        foot = (y0 + 0.003, y0 + bl["foot_rail_m"]) if pn else (y0 + bl["foot_rail_m"], y0 + bl["foot_rail_m"] + rd / 2)
        pnl = bl.get("panel") if bl.get("panel", {}).get("run") == idx else None
        if pnl:
            # T-3092: the rails run into the pedestal's middle over the panel, and the foot
            # rail stops 4 mm inside the panel's ends; no bar stands where the panel does
            c, hw, pw = (sa + sb) / 2, pnl["width_m"] / 2, pnl["pedestal_m"][0]
            spans = {"top": ((r0, c - pw / 4), (c + pw / 4, r1)), "foot": ((r0, c - hw + 0.004), (c + hw - 0.004, r1))}
        top_rails = []
        for key, (ya, yb) in (("top", (y3 - rd, y3 - 0.004)), ("foot", foot)):
            for a, b in (spans[key] if pnl else ((r0, r1),)):
                start = len(flat.prims[role].pos) if role in flat.prims else 0
                prism(flat, role, rect(a, b, ya, yb), -z - rw / 2, -z + rw / 2)
                if pnl and key == "top":
                    top_rails.append(flat.prims[role].pos[start:])
        if pnl:
            self._balcony_panel(flat, pnl, c, y0, y3 - rd, z, bm, top_rails)
        if pn:
            self._pierced_panels(flat, role, pn, e0, e1, foot[1], y3 - rd, z, y0, y3)
            return
        n = max(1, math.floor((e1 - e0) / bl["pitch_m"]))
        step = (e1 - e0) / (n + 1)
        # the light tier keeps the posts and rails, the rail's outline, and drops the bars
        rn = bl.get("roundel")
        bars = 0
        for i in (range(1, n + 1) if self.tier == "full" else ()):
            m = e0 + i * step
            if pnl and abs(m - c) < pnl["width_m"] / 2 + bm:
                continue
            prism(flat, role, rect(m - bm / 2, m + bm / 2, y0, y3 - rd / 2), -z - bm / 2, -z + bm / 2)   # into the rail
            bars += 1
            if rn:
                # T-3092: a ring round the bar under the top rail, thinner than the bar is deep
                # so its faces stand inside the bar's where the bar runs through it
                self._loop(flat, role, m, y3 - rd - rn["radius_m"] - rn["drop_m"], rn["radius_m"], rn["width_m"],
                           12, -z - bm / 3, -z + bm / 3)
        self.meta["balcony"] = {"bars": bars if pnl else n, "top_m": round(y3, 4), "line_out_m": round(z, 4)}
        if pnl:
            self.meta["balcony"]["panel"] = {"run": idx, "s_m": [round(c - pnl["width_m"] / 2, 4),
                                                                 round(c + pnl["width_m"] / 2, 4)]}
        if rn:
            self.meta["balcony"]["roundels"] = bars

    def _balcony_panel(self, flat, pnl, c, y0, y_rail, z, bm, top_rails):
        """T-3092: a balcony's stone panel in the middle of its front run (1812's, the Levy
        print): `width_m` across, centred on the run, its top low at its ends (`end_m` over the
        floor) and swept up in a straight slope over `sweep_m` to its shoulders
        (`shoulder_m`), level from there to a pedestal `pedestal_m` [across, high] on its middle
        under a cap; `thickness_m` deep on the rail's line. Over each sweep, between the panel and
        the top rail, an iron scroll (`scroll_m` its radius) whose tail rises into the rail, and
        on the panel beside the pedestal a small carved scroll each side (`boss_m`). The light
        tier keeps the panel and the pedestal and drops the scrolls."""
        hw, t = pnl["width_m"] / 2, pnl["thickness_m"] / 2
        (pw, ph), sw = pnl["pedestal_m"], pnl["sweep_m"]
        e, sh = y0 + pnl["end_m"], y0 + pnl["shoulder_m"]
        d0, d1 = -z - t, -z + t
        panel_start = len(flat.prims["band"].pos) if "band" in flat.prims else 0
        for sg in (-1, 1):
            # the outline from the panel's end in to the pedestal, 4 mm into it
            xs = [c + sg * hw, c + sg * (hw - sw), c + sg * (pw / 2 - 0.004)]
            ys = [e, sh, sh]
            for j in range(len(xs) - 1):
                a, b = (xs[j], xs[j + 1]) if sg < 0 else (xs[j + 1], xs[j])
                ya, yb = (ys[j], ys[j + 1]) if sg < 0 else (ys[j + 1], ys[j])
                quad = [(a, y0), (b, y0), (b, yb), (a, ya)]
                flat.plane("band", quad, d0)
                flat.plane("band", quad[::-1], d1, (0.0, 0.0, -1.0))
                # its top, and its underside on the floor's 2 mm bed
                flat.face("band", [flat.P(b, yb, d0), flat.P(a, ya, d0), flat.P(a, ya, d1), flat.P(b, yb, d1)],
                          (-(yb - ya), b - a, 0.0))
                flat.face("band", [flat.P(a, y0, d0), flat.P(b, y0, d0), flat.P(b, y0, d1), flat.P(a, y0, d1)],
                          (0.0, -1.0, 0.0))
            xe = c + sg * hw
            flat.face("band", [flat.P(xe, y0, d0), flat.P(xe, y0, d1), flat.P(xe, e, d1), flat.P(xe, e, d0)][::-sg],
                      (float(sg), 0.0, 0.0))
        panel_vertices = flat.prims["band"].pos[panel_start:]
        # the pedestal, deeper than the panel, and its cap over it, broader and deeper again;
        # its foot 3 mm over the panel's, whose ends run 4 mm into it, so no two beds coincide
        pt = t + 0.03
        prism(flat, "band", rect(c - pw / 2, c + pw / 2, y0 + 0.003, y0 + ph), -z - pt, -z + pt)
        prism(flat, "band", rect(c - pw / 2 - 0.03, c + pw / 2 + 0.03, y0 + ph - 0.004, y0 + ph + 0.05),
              -z - pt - 0.025, -z + pt + 0.025)
        if self.tier != "full":
            return
        r, rb = pnl["scroll_m"], pnl["boss_m"]
        for sg in (-1, 1):
            # The Levy scroll stands before the sloping panel, not wholly above it.
            # Its exact stand-off is reconstructed: keep the iron's back 10 mm clear
            # of the stone, and return its tail to the rail above the panel's shoulder.
            sx = c + sg * (hw - 0.45 * sw)
            cy = y_rail - r - bm
            w, gap = bm / 2, 0.01
            scroll_z = z + t + w / 2 + gap
            iron_start = len(flat.prims["iron"].pos) if "iron" in flat.prims else 0
            self._scroll(flat, sx, cy, r, -sg, y_rail + 0.004, w, scroll_z, tail_z=z)
            _check_balcony_scroll_geometry(flat.prims["iron"].pos[iron_start:], panel_vertices, top_rails, gap)
            # the carved scroll on the panel's face beside the pedestal
            self._loop(flat, "carving", c + sg * (pw / 2 + rb + 0.03), (y0 + sh) / 2 + 0.03, rb, rb * 0.45, 12,
                       -z - t - 0.025, -z - t + 0.004, back=False)

    def _scroll(self, flat, cs, cy, r, hand, y_top, w, z, tail_z=None):
        """T-3092: an iron C-scroll: a square bar `w` wound inward from the
        top of a circle of radius `r` about (cs, cy) through a turn and a quarter to 0.45 of it,
        `hand` the way it winds, and a tail from its start up into the rail. `tail_z` can
        return the tail from the scroll's proud plane to the rail without a floating gap.
        Its turns stand further apart than the bar is wide, so the strip never folds over itself."""
        n = 30
        pts = []
        for j in range(n + 1):
            f = j / n
            a = math.pi / 2 + hand * 2.5 * math.pi * f
            rr = r * (1 - 0.55 * f)
            pts.append((cs + rr * math.cos(a), cy + rr * math.sin(a)))
        pts.insert(0, (cs, y_top))
        depths = [z if tail_z is None else tail_z, *([z] * (len(pts) - 1))]
        def at(p, i, side):
            return flat.P(p[0], p[1], -depths[i] + side * w / 2)
        nrm = []
        for j, p in enumerate(pts):
            q0, q1 = pts[max(0, j - 1)], pts[min(len(pts) - 1, j + 1)]
            tx, ty = q1[0] - q0[0], q1[1] - q0[1]
            L = math.hypot(tx, ty)
            nrm.append((-ty / L, tx / L))
        L_ = [(p[0] + n_[0] * w / 2, p[1] + n_[1] * w / 2) for p, n_ in zip(pts, nrm)]
        R_ = [(p[0] - n_[0] * w / 2, p[1] - n_[1] * w / 2) for p, n_ in zip(pts, nrm)]
        for j in range(len(pts) - 1):
            quad = [R_[j], R_[j + 1], L_[j + 1], L_[j]]
            area = sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(quad, quad[1:] + quad[:1]))
            if area < 0:
                quad = quad[::-1]
            inds = [j, j + 1, j + 1, j]
            for poly, ix, side, hint in ((quad, inds, -1, (0.0, 0.0, 1.0)),
                                         (quad[::-1], inds[::-1], 1, (0.0, 0.0, -1.0))):
                verts = [at(p, i, side) for p, i in zip(poly, ix)]
                if depths[j] != depths[j + 1]:
                    # The returning tail's strip edges can twist in depth. Each
                    # triangle needs its own actual normal, not one quad average.
                    for tri in ((verts[0], verts[1], verts[2]), (verts[0], verts[2], verts[3])):
                        flat.face("iron", tri, hint)
                else:
                    flat.face("iron", verts, hint)
            for side, sgn in ((L_, 1.0), (R_, -1.0)):
                a, b = side[j], side[j + 1]
                h = (nrm[j][0] * sgn, nrm[j][1] * sgn, 0.0)
                flat.face("iron", [at(a, j, -1), at(b, j + 1, -1),
                                   at(b, j + 1, 1), at(a, j, 1)], h)
        a, b = L_[-1], R_[-1]
        tx, ty = pts[-1][0] - pts[-2][0], pts[-1][1] - pts[-2][1]
        flat.face("iron", [at(a, -1, -1), at(b, -1, -1),
                           at(b, -1, 1), at(a, -1, 1)], (tx, ty, 0.0))

    def _pilasters(self, flat, run, i, levels, y_wall0, band_h):
        """T-2931: carved pilasters at a run's ends (1801's bow and its south pavilion, from the
        Taylor photograph): in every storey a shaft `width_m` broad and `proud_m` out, from the
        plinth or the floor band under it to the band or the eaves over it, on a base and under a
        capital that each stand wider and prouder than the shaft (the capital the more) (the lowest from `foot_m`, on a
        stepped corbel `corbel_m` tall where the record gives one); on the shaft's face a chain of
        carved lozenges `relief_m` proud between them. At a corner of the plan the shaft wraps
        it (its side stands `proud_m` off the next run's face, as a mitred band does); at a
        junction with the wall it starts where its face meets the wall's plane. The base and
        the capital bury their backs in the wall; the lozenges bury theirs 4 mm in the shaft,
        so no face lies on another. The light tier keeps the shafts, bases and capitals."""
        pl = self.v["pilasters"]
        ends = [q["at"] for q in pl["at"] if q["run"] == i]
        if not ends:
            return
        w, d, hc, hb = pl["width_m"], pl["proud_m"], pl["capital_m"], pl["base_m"]
        lz = pl.get("lozenges")
        n = len(levels) - 1
        count = 0
        for at in ends:
            for side in (("start", "end") if at == "both" else (at,)):
                for k in range(n):
                    lo = pl.get("foot_m", y_wall0) if k == 0 else levels[k] + band_h / 2
                    hi = levels[k + 1] - band_h / 2 if k + 1 < n else levels[k + 1]
                    # each piece runs 4 mm into what it stands on and what stands on it (the
                    # band, the plinth, the soffit, the base and the capital)
                    for ya, yb, grow in ((lo - 0.004, lo + hb, 0.02), (hi - hc, hi + 0.004, 0.045),
                                         (lo + hb - 0.004, hi - hc + 0.004, 0.0)):
                        dz = d + grow
                        if side == "start":
                            a0, a1, c0, c1 = run.s_start(dz), run.s_start(0.0) + w + grow, run.s_start(dz), run.s_start(0.0)
                        else:
                            a0, a1, c0, c1 = run.s_end(0.0) - w - grow, run.s_end(dz), run.s_end(0.0), run.s_end(dz)
                        flat.proud("band", rect(a0, a1, ya, yb), dz)
                        if c1 - c0 > 1e-6:
                            # round a corner: its back where it oversails the next run, over its
                            # own height alone, so the pieces' backs do not overlap where they meet
                            yc0, yc1 = {0.02: (ya, lo + hb), 0.0: (lo + hb, hi - hc)}.get(grow, (hi - hc, yb))
                            flat.plane("band", rect(c0, c1, yc0, yc1)[::-1], 0.0, (0.0, 0.0, -1.0))
                    if k == 0 and pl.get("corbel_m"):
                        # under the lowest base, a corbel of two stepped courses, the upper as
                        # broad and proud as the shaft, the lower narrower and half as proud
                        cm, mid_ = pl["corbel_m"], (run.s_start(0.0) + w / 2 if side == "start" else run.s_end(0.0) - w / 2)
                        for ya, yb, hw, dz in ((lo - cm / 2, lo + 0.004, w / 2, d), (lo - cm, lo - cm / 2 + 0.004, w / 3, d / 2)):
                            a0, a1 = max(mid_ - hw, run.s_start(dz)), min(mid_ + hw, run.s_end(dz))
                            flat.proud("band", rect(a0, a1, ya, yb), dz)
                    if lz and self.tier == "full":
                        mid = run.s_start(0.0) + w / 2 if side == "start" else run.s_end(0.0) - w / 2
                        lw = w - 2 * lz["margin_m"]
                        span = hi - hc - lo - hb - 2 * lz["margin_m"]
                        m = max(1, int(span // lz["pitch_m"]))
                        step = span / m
                        for j in range(m):
                            cy = lo + hb + lz["margin_m"] + step * (j + 0.5)
                            hh = (step - lz["gap_m"]) / 2
                            prism(flat, "carving", [(mid, cy - hh), (mid + lw / 2, cy), (mid, cy + hh), (mid - lw / 2, cy)],
                                  -d - lz["relief_m"], -d + 0.004)
                            count += 1
        self.meta.setdefault("pilasters", {"shafts": 0, "lozenges": 0})
        self.meta["pilasters"]["shafts"] += n * sum(2 if a == "both" else 1 for a in ends)
        self.meta["pilasters"]["lozenges"] += count

    def _pierced_panels(self, flat, role, pn, e0, e1, lo, hi, z, y0, y3):
        """T-2930: a stone balustrade's pierced panels (1801's bow, from the Taylor print), in
        place of its bars: the run between its end posts cut into `count` panels by posts of
        the same stone, and in each panel a diagonal lattice of square-cut straps `bar_m`
        thick, two families of them crossing at `pitch_m` along the run, so the stone between
        them is pierced through in diamonds `rows` to the panel's height (and halves of them
        against the rails). Every strap is clipped to its panel and carried 4 mm into the
        rails and posts round it (the second family 6 mm), so no end of one lies in another's face;
        the second family stands 4 mm inside the first's faces where they cross, so no two faces coincide.
        The light tier keeps the posts and rails and drops the straps, as it drops bars."""
        bl = self.v["balcony"]
        pm, bm, p = bl["post_m"], bl["bar_m"], bl["pitch_m"]
        cnt, rows = int(pn["count"]), int(pn["rows"])
        d0, d1 = -z - pm / 2, -z + pm / 2
        w = (e1 - e0 - (cnt - 1) * pm) / cnt
        h = hi - lo
        m = h / (rows * p)                         # the straps' rise along the run
        wh = bm * math.sqrt(1 + m * m) / m         # a strap's width measured along the run
        straps = 0
        for i in range(cnt):
            s0 = e0 + i * (w + pm)
            s1 = s0 + w
            if i:
                prism(flat, role, rect(s0 - pm, s0, y0, y3), d0, d1)
            if self.tier != "full":
                continue
            mid = (s0 + s1) / 2               # the lattice centred on its panel, a crossing on its axis
            reach = math.ceil((w / 2 + rows * p + wh) / p) + 1
            # the second family runs 6 mm into the rails and posts, the first 4 mm, so where
            # two straps cross on a rail their buried ends never share a plane
            for sg, (t0, t1), e in ((1, (-z - bm / 2, -z + bm / 2), 0.004),
                                    (-1, (-z - bm / 2 + 0.004, -z + bm / 2 - 0.004), 0.006)):
                c0, c1, b0, b1 = s0 - e, s1 + e, lo - e, hi + e
                for k in range(-reach, reach + 1):
                    a = mid + k * p           # where the strap's axis meets the foot rail
                    at = lambda y, o: a + o + sg * (y - lo) / m
                    poly = [(at(b0, -wh / 2), b0), (at(b0, wh / 2), b0), (at(b1, wh / 2), b1), (at(b1, -wh / 2), b1)]
                    for f in (lambda q: q[0] - c0, lambda q: c1 - q[0], lambda q: q[1] - b0, lambda q: b1 - q[1]):
                        poly = clip_half(poly, f) if poly else poly
                    poly = [q for n_, q in enumerate(poly) if math.dist(q, poly[n_ - 1]) > 1e-6]
                    if len(poly) < 3:
                        continue
                    area = sum(q[0] * r[1] - r[0] * q[1] for q, r in zip(poly, poly[1:] + poly[:1])) / 2
                    if abs(area) > 2e-5:
                        prism(flat, role, poly if area > 0 else poly[::-1], t0, t1)
                        straps += 1
        self.meta["balcony"] = {"panels": cnt, "straps": straps, "top_m": round(y3, 4), "line_out_m": round(z, 4)}

    def _floor_balcony(self, flat, s_c, cv):
        """T-2534: a balcony on a projection's floor, out from its front run under the window it
        serves, all in the bay's dressed stone: a slab on a segmental bow from the wall to the
        wall, `chord_m` along the face and `rise_m` out, its top the floor; on it a balustrade
        `inset_m` in from the slab's edge — a square post against the wall at each end, a
        coping rail swept round the bow between them and square balusters at `pitch_m` under it
        (the light tier keeps the slab, the posts and the rail, and drops the balusters). Built
        in the run's flat frame (z out of the face), so a straight run carries it rigidly."""
        fb = self.v["floor_balcony"]
        h, rise, inset = fb["chord_m"] / 2, fb["rise_m"], fb["inset_m"]
        pm, bm, (rw, rd) = fb["post_m"], fb["bar_m"], fb["rail_m"]
        y1 = fb["floor_m"]
        y0, y3 = y1 - fb["slab_m"], y1 + fb["height_m"]
        R = (h * h + rise * rise) / (2 * rise)
        zc = rise - R
        f0 = math.asin(h / R)
        n = max(2, math.ceil(math.degrees(2 * f0) / cv["max_seg_deg"]))

        def at(r, f):
            return (s_c + r * math.sin(f), zc + r * math.cos(f))

        def arc(r, fa, fb_, k):
            return [at(r, fa + (fb_ - fa) * j / k) for j in range(k + 1)]

        def P(q, y):
            return flat.P(q[0], y, -q[1])

        def band(inner, outer, ya, yb, top=True, bottom=True):
            """A swept block between two arcs of points, from ya to yb: its faces out and in."""
            for a, sgn in ((outer, 1.0), (inner, -1.0)):
                if a is None:
                    continue
                for j in range(len(a) - 1):
                    m = ((a[j][0] + a[j + 1][0]) / 2 - s_c, (a[j][1] + a[j + 1][1]) / 2 - zc)
                    flat.face(role, [P(a[j], ya), P(a[j + 1], ya), P(a[j + 1], yb), P(a[j], yb)],
                              (sgn * m[0], 0.0, sgn * m[1]))
            for y, hint, on in ((yb, Y, top), (ya, (0.0, -1.0, 0.0), bottom)):
                if not on:
                    continue
                if inner is None:
                    flat.face(role, [P(q, y) for q in outer], hint)
                    continue
                for j in range(len(outer) - 1):
                    flat.face(role, [P(inner[j], y), P(outer[j], y), P(outer[j + 1], y), P(inner[j + 1], y)], hint)

        def role_box(s0, s1, z0, z1, ya, yb):
            q = [(s0, z0), (s1, z0), (s1, z1), (s0, z1)]
            for k in range(4):
                a, b = q[k], q[(k + 1) % 4]
                m = ((a[0] + b[0]) / 2 - (s0 + s1) / 2, (a[1] + b[1]) / 2 - (z0 + z1) / 2)
                flat.face(role, [P(a, ya), P(b, ya), P(b, yb), P(a, yb)], (m[0], 0.0, m[1]))
            flat.face(role, [P(p, yb) for p in q], Y)

        # the slab: the bow's segment, its top the floor, its edge the arc; its back is the wall
        role = "band"     # the bay's dressed stone, slab and balustrade alike
        band(None, arc(R, -f0, f0, n), y0, y1)
        # the rail's line, `inset_m` in from the slab's edge, ends at a post against the wall
        r = R - inset
        f1 = math.acos(max(-1.0, min(1.0, (pm / 2 - zc) / r)))
        ends = [at(r, -f1), at(r, f1)]
        for q in ends:
            role_box(q[0] - pm / 2, q[0] + pm / 2, 0.003, pm + 0.003, y1, y3)   # off the wall face
        k = max(2, math.ceil(n * f1 / f0))
        band(arc(r - rw / 2, -f1, f1, k), arc(r + rw / 2, -f1, f1, k), y3 - rd, y3 - 0.004)
        length = 2 * f1 * r
        bars = max(1, math.floor((length - pm) / fb["pitch_m"]))
        for j in (range(1, bars + 1) if self.tier == "full" else ()):
            q = at(r, -f1 + 2 * f1 * j / (bars + 1))
            role_box(q[0] - bm / 2, q[0] + bm / 2, q[1] - bm / 2, q[1] + bm / 2, y1, y3 - rd / 2)
        self.meta["floor_balcony"] = {"floor_m": round(y1, 4), "top_m": round(y3, 4), "bars": bars,
                                      "chord_m": round(2 * h, 4), "rise_m": round(rise, 4)}

    def _sockets(self, y0, y_e):
        first, last = self.runs[0], self.runs[-1]
        jl, jr = first.world(0.0, y0, 0.0), last.world(last.L, y0, 0.0)
        reach = max(r.world(s, 0, 0)[2] for r in self.runs for s in [r.L * j / 16 for j in range(17)])
        self.meta["sockets"] = {"junction_left": [round(c, 4) for c in jl], "junction_right": [round(c, 4) for c in jr],
                                "base": [0.0, round(y0, 4), 0.0], "eave": [0.0, round(y_e, 4), 0.0]}
        self.meta["plan"] = {"runs": [{"kind": r.kind, "length_m": round(r.L, 4),
                                       "start": r.start if r.start in ("wall", "side") else ["corner", round(math.degrees(r.start[1]), 3)],
                                       "end": r.end if r.end in ("wall", "side") else ["corner", round(math.degrees(r.end[1]), 3)]}
                                      for r in self.runs],
                             "width_at_wall_m": round(jr[0] - jl[0], 4), "projection_m": round(reach, 4)}

    def _board(self, y_e):
        """The host wall the bay is keyed to, its top and returns, and grade in front."""
        xs = [p[0] for pr in self.prims.values() for p in pr.pos]
        x0, x1 = min(xs) - 1.0, max(xs) + 1.0
        roof_y = max((p[1] for p in self.prims["roof"].pos if abs(p[2]) < 1e-6), default=y_e) \
            if self.prims.get("roof") else y_e   # T-3176: a whole cap may touch no wall plane
        top = y_e if self.v["kind"] == "tower" else roof_y + 0.6
        D = 0.45
        if self.v.get("shallow"):
            # T-3047: a shallow bay's host is opened round its recesses, deeper than they reach,
            # and stops under its parapet, which closes its own top
            top = self.meta["wall_top_m"]
            D = max(D, -min(p[2] for p in self.prims["backing"].pos) + 0.1)
        b = strip(f"{self.v['id']}|board")
        for (a0, a1), (b0, b1) in host_cells((x0, x1), (0.0, top), self.host_holes):
            b.face("board_wall", [(a0, b0, 0.0), (a1, b0, 0.0), (a1, b1, 0.0), (a0, b1, 0.0)], (0.0, 0.0, 1.0))
        b.face("board_wall", [(x0, top, 0.0), (x1, top, 0.0), (x1, top, -D), (x0, top, -D)], Y)
        for x, hx in ((x0, -1.0), (x1, 1.0)):
            b.face("board_wall", [(x, 0.0, 0.0), (x, top, 0.0), (x, top, -D), (x, 0.0, -D)], (hx, 0.0, 0.0))
        b.face("board_wall", [(x0, 0.0, -D), (x1, 0.0, -D), (x1, top, -D), (x0, top, -D)], (0.0, 0.0, -1.0))
        G = max(p[2] for pr in self.prims.values() for p in pr.pos) + 1.5
        b.face("ground", [(x0, 0.0, 0.0), (x1, 0.0, 0.0), (x1, 0.0, G), (x0, 0.0, G)], Y)
        merge(self.prims, b.prims)
        self.meta["board"] = {"x": [round(x0, 4), round(x1, 4)], "top_m": round(top, 4), "ground_to_m": round(G, 4)}


def host_cells(xr, yr, holes):
    """T-3047: the rectangle xr x yr less the rectangular holes (x0, x1, y0, y1) in it, as
    ((x0, x1), (y0, y1)) cells on the holes' own lines, each row's free cells merged: a host
    face opened round a shallow bay's recesses. With no hole in it, the rectangle itself."""
    hs = [h for h in holes if h[0] < xr[1] - 1e-9 and h[1] > xr[0] + 1e-9 and h[2] < yr[1] - 1e-9 and h[3] > yr[0] + 1e-9]
    if not hs:
        return [(xr, yr)]
    xs = sorted({xr[0], xr[1], *(min(max(c, xr[0]), xr[1]) for h in hs for c in h[:2])})
    ys = sorted({yr[0], yr[1], *(min(max(c, yr[0]), yr[1]) for h in hs for c in h[2:4])})
    out = []
    for ya, yb in zip(ys, ys[1:]):
        run = None
        for xa, xb in zip(xs, xs[1:]):
            cx, cy = (xa + xb) / 2, (ya + yb) / 2
            if any(h[0] < cx < h[1] and h[2] < cy < h[3] for h in hs):
                run = None
            elif run is not None and abs(run[1] - xa) < 1e-12:
                run[1] = xb
            else:
                run = [xa, xb]
                out.append((run, (ya, yb)))
    return [((r[0], r[1]), y) for r, y in out]


def support_bottom(v: dict, data: dict | None = None) -> float:
    """T-2883: how low an oriel's support reaches: its apron's foot, or its lowest corbel course."""
    if v.get("apron"):
        return float(v["apron"]["foot_m"])
    data = data or load()
    return float(v["base"]) - v["corbel"]["courses"] * float(data["parts"]["corbel"]["course_height_m"])


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
