"""The K13 conservatory kit: glasshouses whose frame reads, written straight to glTF.

TICKET T-2305 (piece 1 of T-1855, K13). The kit's sizes are data in
`data/components/prairie_1904/k13_conservatories.json`; this module reads them and
builds each variant as the houses T-2306 will put in the Pullman service garden:

  panels        every glazed face of the house, a convex polygon with an outward
                normal: the upright walls, the roof slopes, a curvilinear roof's
                facets, a lantern's sides and roof
  members       three tiers. PRIMARY posts, rafters, ribs, corner posts, hips and
                jambs; SECONDARY plates (sill, eave, ridge, verge, wall plate,
                transom, door head, lock rail); TERTIARY glazing bars, running one
                way only. A member between two panels is built once on their edge
                with faces parallel to both; a member inside a panel is a strip
                standing proud of the glass and running in behind it
  glass         one pane per cell between bars, in the panel's plane, single-sided
                and facing out. The panels of one house make ONE convex envelope,
                so a line of sight enters by one pane and leaves by panes that face
                away from it and are not drawn. A lantern standing up off the roof
                would break the envelope, so it takes the opaque glass substitute
  plinth        a brick dwarf wall under a stone coping, swept along the walls'
                feet; the glass stands on its sill plate on the coping
  door          a half-glazed door between primary jambs, the plinth stopped for it
  rainwater     K04's half-round gutter on every eave, falling to its outlet, a
                round pipe with a swan neck past the coping and a shoe over a splash
                stone at grade; K04's bracket spacing
  ridge vent    a louvred ventilator along a span roof's ridge
  planting      a staging bench with low pot-plant masses, and a border against a
                lean-to's wall: opaque, restrained, clear of the glass

WHY PURE PYTHON: the reasons k01_frontage.py and k06_windows.py give. The gate
measures vertices (tier against tier, the envelope's convexity, panes against bars,
pipe against grade), and they are easiest to hold when this module writes them.
`Prim` and the vector helpers are K01's; `clip` and `area2` are K06's.

    python3 generators/archetypes/k13_conservatories.py           write the specimen GLB
    python3 generators/archetypes/k13_conservatories.py --check   refuse if it is stale
"""

from __future__ import annotations

import hashlib
import json
import math
import struct
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from archetypes.k01_frontage import Prim, _add, _cross, _dot, _mul, _sub, _unit  # noqa: E402
from archetypes.k06_windows import area2  # noqa: E402

ROOT = HERE.parents[1]
DATA = ROOT / "data" / "components" / "prairie_1904" / "k13_conservatories.json"
GENERATOR = "chicago-4d generators/archetypes/k13_conservatories.py (K13, T-2305)"
RECONSTRUCTED = 1.0  # k01_frontage_params.CONFIDENCE_VALUE["reconstructed"]

Y = (0.0, 1.0, 0.0)
NEAR_COPLANAR_DEG = 25.0   # below this two panels' edge takes strips, not one edge member

# Role -> material. A role is what the gate measures; a material is what a renderer
# binds. Fixed order: the file is the same bytes every run.
ROLE_MATERIAL = {
    "glass": "glass", "substitute": "glass_substitute",
    "primary": "frame", "secondary": "frame", "tertiary": "frame", "door_panel": "frame",
    "vent": "frame", "vent_dark": "dark",
    "plinth": "brick", "coping": "stone",
    "gutter": "rainwater", "bracket": "rainwater", "pipe": "rainwater",
    "bench": "staging", "plant": "foliage", "floor": "floor",
    "wall": "house_wall", "ground": "ground",
    "host_band": "house_wall",
}
BOARD_ROLES = ("wall", "ground", "host_band")
TIERS = ("primary", "secondary", "tertiary")
TIER_OF = {"corner": "primary", "hip": "primary", "eave": "secondary", "ridge": "secondary",
           "verge": "secondary", "transom": "secondary", "free": "secondary"}


def materials(data: dict) -> dict:
    g, s = data["glass"], data["substitute"]
    return {
        "glass": {"color": tuple(g["base_color"]), "roughness": g["roughness"], "metallic": g["metallic"],
                  "alpha": g["alpha"]},
        "glass_substitute": {"color": tuple(s["base_color"]), "roughness": s["roughness"],
                             "metallic": s["metallic"]},
        "frame": {"color": (0.86, 0.85, 0.80), "roughness": 0.75},
        "dark": {"color": (0.035, 0.035, 0.03), "roughness": 1.0},
        "brick": {"color": (0.55, 0.30, 0.22), "roughness": 0.92},
        "stone": {"color": (0.74, 0.70, 0.62), "roughness": 0.85},
        "rainwater": {"color": (0.17, 0.20, 0.18), "roughness": 0.45, "metallic": 0.2},
        "staging": {"color": (0.36, 0.27, 0.18), "roughness": 0.85},
        "foliage": {"color": (0.13, 0.24, 0.10), "roughness": 0.95},
        "floor": {"color": (0.50, 0.27, 0.20), "roughness": 0.8},
        "house_wall": {"color": (0.62, 0.40, 0.31), "roughness": 0.92},
        "ground": {"color": (0.36, 0.34, 0.30), "roughness": 1.0},
    }


def seed_of(component_id: str, index: int, structure_id: str = "k13_conservatory_kit") -> int:
    """K01's seed rule (k01_contract.json `seed`)."""
    return int(hashlib.sha256(f"{structure_id}|{component_id}|{index}".encode()).hexdigest()[:8], 16)


def unit01(seed: int, salt: int) -> float:
    return ((seed >> (salt % 16)) & 0xFFFF) / 65535.0


# -- small geometry ------------------------------------------------------------------------

def newell(pts):
    n = (0.0, 0.0, 0.0)
    for i, a in enumerate(pts):
        b = pts[(i + 1) % len(pts)]
        n = _add(n, ((a[1] - b[1]) * (a[2] + b[2]), (a[2] - b[2]) * (a[0] + b[0]), (a[0] - b[0]) * (a[1] + b[1])))
    return n


def hclip(poly, a, b, c):
    """`poly` clipped to the half-plane a*u + b*v <= c."""
    out = []
    for i, p in enumerate(poly):
        q = poly[(i + 1) % len(poly)]
        fp, fq = a * p[0] + b * p[1] - c, a * q[0] + b * q[1] - c
        if fp <= 1e-12:
            out.append(p)
        if (fp <= 1e-12) != (fq <= 1e-12):
            t = fp / (fp - fq)
            out.append((p[0] + t * (q[0] - p[0]), p[1] + t * (q[1] - p[1])))
    # drop repeated points the clip can leave at a vertex on the line
    clean = []
    for p in out:
        if not clean or abs(p[0] - clean[-1][0]) > 1e-10 or abs(p[1] - clean[-1][1]) > 1e-10:
            clean.append(p)
    if len(clean) > 1 and abs(clean[0][0] - clean[-1][0]) < 1e-10 and abs(clean[0][1] - clean[-1][1]) < 1e-10:
        clean.pop()
    return clean


def key3(p):
    return tuple(round(c, 6) for c in p)


def plan(p):
    return (p[0], p[2])


def hnorm(dx, dz):
    n = math.hypot(dx, dz)
    return (dx / n, 0.0, dz / n)


def mitre(o1, o2):
    k = 1.0 + _dot(o1, o2)
    return _mul(_add(o1, o2), 1.0 / k)


class Panel:
    """A glazed face: a convex polygon, its outward normal N, and a frame (U along,
    V up the face) whose 2D coordinates every member and pane is cut in."""

    def __init__(self, name, pts, hint, kind="glass", plinth=False, bays=0, door=None, lantern=False):
        pts = [tuple(float(c) for c in p) for p in pts]
        n = newell(pts)
        if _dot(n, hint) < 0:
            pts, n = pts[::-1], _mul(n, -1)
        self.N = _unit(n)
        up = _sub(Y, _mul(self.N, _dot(Y, self.N)))
        self.V = _unit(up)
        self.U = _cross(self.V, self.N)
        self.name, self.pts, self.kind = name, pts, kind
        self.plinth, self.bays, self.door, self.lantern = plinth, bays, door, lantern
        self.vertical = abs(self.N[1]) < 1e-6
        self.O = min(pts, key=lambda p: (round(_dot(p, self.V), 9), _dot(p, self.U)))
        self.poly = [self.uv(p) for p in pts]
        if area2(self.poly) <= 0:
            raise ValueError(f"panel {name} is not counter-clockwise about its normal")

    def uv(self, p):
        d = _sub(p, self.O)
        return (_dot(d, self.U), _dot(d, self.V))

    def P(self, u, v, off=0.0):
        return _add(self.O, _add(_mul(self.U, u), _add(_mul(self.V, v), _mul(self.N, off))))

    def edges(self):
        n = len(self.pts)
        return [(i, self.pts[i], self.pts[(i + 1) % n], self.poly[i], self.poly[(i + 1) % n]) for i in range(n)]

    def inward(self, i):
        """The inward unit normal of edge i in 2D, and the edge's start."""
        a, b = self.poly[i], self.poly[(i + 1) % len(self.poly)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        ln = math.hypot(dx, dy)
        return (-dy / ln, dx / ln), a

    def v_of_y(self, y):
        """For an upright panel: the v of a world height."""
        return y - self.O[1]


# -- the forms -----------------------------------------------------------------------------
# Each returns panels, the plinth plan (segments along the walls' feet), the eave runs
# that shed, the ridges that carry a vent, the staging lines and the house's facts.

def form_lean_to(v, data):
    L, D, he = v["length_m"], v["depth_m"], v["eave_m"]
    hw = he + D * math.tan(math.radians(v["pitch_deg"]))
    door = v.get("door") or {}
    P = [
        Panel("front", [(0, 0, D), (L, 0, D), (L, he, D), (0, he, D)], (0, 0, 1), plinth=True, bays=v["bays"]),
        Panel("roof", [(0, he, D), (L, he, D), (L, hw, 0), (0, hw, 0)], (0, 1, 1), bays=v["bays"]),
        Panel("end_left", [(0, 0, 0), (0, 0, D), (0, he, D), (0, hw, 0)], (-1, 0, 0), plinth=True,
              door=door if door.get("wall") == "end_left" else None),
        Panel("end_right", [(L, 0, D), (L, 0, 0), (L, hw, 0), (L, he, D)], (1, 0, 0), plinth=True,
              door=door if door.get("wall") == "end_right" else None),
    ]
    return {
        "panels": P, "host": True, "closed": False,
        "plan": [(0, 0), (0, D), (L, D), (L, 0)],
        "eaves": {"front": [(0, he, D), (L, he, D)]},
        "ridges": [], "benches": [("front", (0, D), (L, D))], "border": ((0, 0), (L, 0)),
        "eave_m": he, "top_m": hw, "centre": (L / 2, hw / 2, D / 2),
    }


def form_span(v, data):
    L, W, he = v["length_m"], v["width_m"], v["eave_m"]
    hr = he + W / 2 * math.tan(math.radians(v["pitch_deg"]))
    door = v.get("door") or {}
    b = v["bays"]
    P = [
        Panel("front", [(0, 0, W), (L, 0, W), (L, he, W), (0, he, W)], (0, 0, 1), plinth=True, bays=b),
        Panel("back", [(L, 0, 0), (0, 0, 0), (0, he, 0), (L, he, 0)], (0, 0, -1), plinth=True, bays=b),
        Panel("roof_front", [(0, he, W), (L, he, W), (L, hr, W / 2), (0, hr, W / 2)], (0, 1, 1), bays=b),
        Panel("roof_back", [(L, he, 0), (0, he, 0), (0, hr, W / 2), (L, hr, W / 2)], (0, 1, -1), bays=b),
        Panel("end_left", [(0, 0, 0), (0, 0, W), (0, he, W), (0, hr, W / 2), (0, he, 0)], (-1, 0, 0), plinth=True,
              door=door if door.get("wall") == "end_left" else None),
        Panel("end_right", [(L, 0, W), (L, 0, 0), (L, he, 0), (L, hr, W / 2), (L, he, W)], (1, 0, 0), plinth=True,
              door=door if door.get("wall") == "end_right" else None),
    ]
    return {
        "panels": P, "host": False, "closed": True,
        "plan": [(0, 0), (L, 0), (L, W), (0, W)],
        "eaves": {"front": [(0, he, W), (L, he, W)], "back": [(0, he, 0), (L, he, 0)]},
        "ridges": [((0, hr, W / 2), (L, hr, W / 2), v["pitch_deg"])],
        "benches": [("front", (0, W), (L, W)), ("back", (L, 0), (0, 0))], "border": None,
        "eave_m": he, "top_m": hr, "centre": (L / 2, hr / 2, W / 2),
    }


def form_span_lantern(v, data):
    L, W, he = v["length_m"], v["width_m"], v["eave_m"]
    ln = data["lantern"]
    lw, lh = ln["width_m"], ln["height_m"]
    tp, tl = math.tan(math.radians(v["pitch_deg"])), math.tan(math.radians(ln["pitch_deg"]))
    zf, zb = W / 2 + lw / 2, W / 2 - lw / 2
    yc = he + (W / 2 - lw / 2) * tp
    yt = yc + lh
    yr = yt + lw / 2 * tl
    door = v.get("door") or {}
    b = v["bays"]
    S = ln["glazing"]
    P = [
        Panel("front", [(0, 0, W), (L, 0, W), (L, he, W), (0, he, W)], (0, 0, 1), plinth=True, bays=b),
        Panel("back", [(L, 0, 0), (0, 0, 0), (0, he, 0), (L, he, 0)], (0, 0, -1), plinth=True, bays=b),
        Panel("roof_front", [(0, he, W), (L, he, W), (L, yc, zf), (0, yc, zf)], (0, 1, 1), bays=b),
        Panel("roof_back", [(L, he, 0), (0, he, 0), (0, yc, zb), (L, yc, zb)], (0, 1, -1), bays=b),
        Panel("lantern_front", [(0, yc, zf), (L, yc, zf), (L, yt, zf), (0, yt, zf)], (0, 0, 1), kind=S, bays=b,
              lantern=True),
        Panel("lantern_back", [(L, yc, zb), (0, yc, zb), (0, yt, zb), (L, yt, zb)], (0, 0, -1), kind=S, bays=b,
              lantern=True),
        Panel("lantern_roof_front", [(0, yt, zf), (L, yt, zf), (L, yr, W / 2), (0, yr, W / 2)], (0, 1, 1), kind=S,
              bays=b, lantern=True),
        Panel("lantern_roof_back", [(L, yt, zb), (0, yt, zb), (0, yr, W / 2), (L, yr, W / 2)], (0, 1, -1), kind=S,
              bays=b, lantern=True),
    ]
    for x, nx, name in ((0.0, -1.0, "end_left"), (L, 1.0, "end_right")):
        P.append(Panel(name, [(x, 0, 0), (x, 0, W), (x, he, W), (x, yc, zf), (x, yc, zb), (x, he, 0)], (nx, 0, 0),
                       plinth=True, door=door if door.get("wall") == name else None))
        P.append(Panel(name + "_lantern", [(x, yc, zb), (x, yc, zf), (x, yt, zf), (x, yr, W / 2), (x, yt, zb)],
                       (nx, 0, 0), kind=S, lantern=True))
    return {
        "panels": P, "host": False, "closed": True,
        "plan": [(0, 0), (L, 0), (L, W), (0, W)],
        "eaves": {"front": [(0, he, W), (L, he, W)], "back": [(0, he, 0), (L, he, 0)]},
        "ridges": [((0, yr, W / 2), (L, yr, W / 2), ln["pitch_deg"])],
        "benches": [("front", (0, W), (L, W)), ("back", (L, 0), (0, 0))], "border": None,
        "eave_m": he, "top_m": yr, "centre": (L / 2, yr / 2, W / 2),
    }


def curve_points(v, data):
    D, he, rise = v["depth_m"], v["eave_m"], v["rise_m"]
    n = data["curve"]["facets"]
    return [(D * math.cos(math.pi / 2 * k / n), he + rise * math.sin(math.pi / 2 * k / n)) for k in range(n + 1)]


def form_curvilinear_lean_to(v, data):
    L, D, he, rise = v["length_m"], v["depth_m"], v["eave_m"], v["rise_m"]
    door = v.get("door") or {}
    cp = curve_points(v, data)          # (z, y) from the eave to the wall plate
    P = [Panel("front", [(0, 0, D), (L, 0, D), (L, he, D), (0, he, D)], (0, 0, 1), plinth=True, bays=v["bays"])]
    for k in range(len(cp) - 1):
        (z0, y0), (z1, y1) = cp[k], cp[k + 1]
        nz, ny = (y1 - y0), (z0 - z1)   # the chord's outward normal in (z, y)
        P.append(Panel(f"facet_{k}", [(0, y0, z0), (L, y0, z0), (L, y1, z1), (0, y1, z1)], (0, ny, nz),
                       bays=v["bays"]))
    for x, nx, name in ((0.0, -1.0, "end_left"), (L, 1.0, "end_right")):
        pts = [(x, 0, 0), (x, 0, D)] + [(x, y, z) for z, y in cp]
        P.append(Panel(name, pts, (nx, 0, 0), plinth=True, door=door if door.get("wall") == name else None))
    return {
        "panels": P, "host": True, "closed": False,
        "plan": [(0, 0), (0, D), (L, D), (L, 0)],
        "eaves": {"front": [(0, he, D), (L, he, D)]},
        "ridges": [], "benches": [("front", (0, D), (L, D))], "border": ((0, 0), (L, 0)),
        "eave_m": he, "top_m": he + rise, "centre": (L / 2, (he + rise) / 2, D / 2), "curve": cp,
    }


def form_canted_bay(v, data):
    Wc, D, he, hw = v["face_m"], v["depth_m"], v["eave_m"], v["wall_top_m"]
    h = Wc / 2
    xh = h + D * (1 - math.sqrt(2))     # where each hip meets the house wall
    if xh <= 0:
        raise ValueError(f"{v['id']}: face_m {Wc} is too narrow for depth_m {D}; the hips cross")
    b = v["bays"]
    P = [
        Panel("front", [(-h, 0, D), (h, 0, D), (h, he, D), (-h, he, D)], (0, 0, 1), plinth=True, bays=b),
        Panel("cant_right", [(h, 0, D), (h + D, 0, 0), (h + D, he, 0), (h, he, D)], (1, 0, 1), plinth=True, bays=b),
        Panel("cant_left", [(-h - D, 0, 0), (-h, 0, D), (-h, he, D), (-h - D, he, 0)], (-1, 0, 1), plinth=True, bays=b),
        Panel("roof_front", [(-h, he, D), (h, he, D), (xh, hw, 0), (-xh, hw, 0)], (0, 1, 1), bays=b),
        Panel("roof_right", [(h, he, D), (h + D, he, 0), (xh, hw, 0)], (1, 1, 1), bays=b),
        Panel("roof_left", [(-h - D, he, 0), (-h, he, D), (-xh, hw, 0)], (-1, 1, 1), bays=b),
    ]
    return {
        "panels": P, "host": True, "closed": False,
        "plan": [(-h - D, 0), (-h, D), (h, D), (h + D, 0)],
        "eaves": {"front": [(-h - D, he, 0), (-h, he, D), (h, he, D), (h + D, he, 0)]},
        "ridges": [], "benches": [("front", (-h, D), (h, D))], "border": None,
        "eave_m": he, "top_m": hw, "centre": (0.0, hw / 2, D / 2),
    }


def form_segmental_bay(v, data):
    """T-2306: a bay on a half-polygon of `facets` sides inscribed in a semicircle of
    `radius_m` against the house wall, under a half-cone of glass triangles whose hips
    all run to one apex on the wall at `wall_top_m`. The Pullman wing's bay is drawn as
    a semicircle on the 1911 sheet; this is the kit's way of building one in planar glass."""
    R, n, he, hw = v["radius_m"], v["facets"], v["eave_m"], v["wall_top_m"]
    if n < 3:
        raise ValueError(f"{v['id']}: a segmental bay needs at least 3 facets, not {n}")
    if hw <= he:
        raise ValueError(f"{v['id']}: wall_top_m {hw} does not rise above eave_m {he}")
    ring = [(R * math.cos(math.pi * k / n), R * math.sin(math.pi * k / n)) for k in range(n + 1)]
    ring[0], ring[-1] = (R, 0.0), (-R, 0.0)       # exactly on the wall
    apex = (0.0, hw, 0.0)
    b = v["bays"]
    P = []
    for k in range(n):
        (x0, z0), (x1, z1) = ring[k], ring[k + 1]
        hint = ((x0 + x1) / 2, 0.0, (z0 + z1) / 2)
        P.append(Panel(f"facet_{k}", [(x0, 0, z0), (x1, 0, z1), (x1, he, z1), (x0, he, z0)], hint,
                       plinth=True, bays=b))
        P.append(Panel(f"roof_{k}", [(x0, he, z0), (x1, he, z1), apex], (hint[0], 1.0, hint[2]), bays=b))
    plan_pts = list(reversed(ring))                # left to right along the wall, as the canted bay's
    # the staging runs on the chord of the first and last facets, stood out toward the glass
    xb, zb = R * math.cos(math.pi / n), R * math.sin(math.pi / n) + v.get("bench_out_m", 0.0)
    return {
        "panels": P, "host": True, "closed": False,
        "plan": plan_pts,
        "eaves": {"front": [(x, he, z) for x, z in plan_pts]},
        "ridges": [], "benches": [("front", (-xb, zb), (xb, zb))], "border": None,
        "eave_m": he, "top_m": hw, "centre": (0.0, hw / 2, R / 2),
    }


FORMS = {"lean_to": form_lean_to, "span": form_span, "span_lantern": form_span_lantern,
         "curvilinear_lean_to": form_curvilinear_lean_to, "canted_bay": form_canted_bay,
         "segmental_bay": form_segmental_bay}


# -- the builder ----------------------------------------------------------------------------

class House:
    """One variant, built in its own frame (x along the front, y up, z out of the house
    wall or across the house) and placed at `origin` on the board."""

    def __init__(self, variant: dict, data: dict, origin=(0.0, 0.0, 0.0), index: int = 0):
        self.v, self.data, self.O = variant, data, origin
        self.k04 = json.loads((ROOT / data["k04"]).read_text())["profiles"]
        self.prims: dict[str, Prim] = {}
        self.members: list[dict] = []
        self.panes: list[dict] = []
        self.edges: list[dict] = []
        self.gutters: list[dict] = []
        self.pipes: list[dict] = []
        self.coping_lines: list[tuple] = []
        self.ribs: list[list] = []
        self.seed = seed_of(variant["id"], index)
        self.meta: dict = {}

    # faces -------------------------------------------------------------------------
    def face(self, role, pts, hint):
        n = newell(pts)
        if math.sqrt(_dot(n, n)) < 1e-12:
            return
        n = _unit(n)
        if _dot(n, hint) < 0:
            n = _mul(n, -1)
        au = _cross(Y, n)
        au = _unit(au) if _dot(au, au) > 1e-9 else (1.0, 0.0, 0.0)
        av = _cross(n, au)
        w = [_add(p, self.O) for p in pts]
        self.prims.setdefault(role, Prim(role)).face(w, n, (w[0], au, av, 1.0, 1.0, 0.0, 0.0), RECONSTRUCTED)

    def slab(self, panel, region, out, inn, lines, tier, kind, width):
        """A member cut as `region` (2D, in the panel), standing `out` proud of the glass
        and running `inn` behind it, with side faces along each of `lines`."""
        if len(region) < 3 or abs(area2(region)) < 1e-10:
            return
        self.face(tier, [panel.P(u, v, out) for u, v in region], panel.N)
        self.face(tier, [panel.P(u, v, -inn) for u, v in region], _mul(panel.N, -1))
        for i, p in enumerate(region):
            q = region[(i + 1) % len(region)]
            for a, b, c in lines:
                if abs(a * p[0] + b * p[1] - c) < 1e-7 and abs(a * q[0] + b * q[1] - c) < 1e-7:
                    hint = _add(_mul(panel.U, a), _mul(panel.V, b))
                    self.face(tier, [panel.P(p[0], p[1], out), panel.P(q[0], q[1], out),
                                     panel.P(q[0], q[1], -inn), panel.P(p[0], p[1], -inn)], hint)
        verts = [panel.P(u, v, o) for u, v in region for o in (out, -inn)]
        self.members.append({"tier": tier, "kind": kind, "panel": panel.name, "width": width,
                             "standing": max(_dot(_sub(p, panel.O), panel.N) for p in verts),
                             "behind": -min(_dot(_sub(p, panel.O), panel.N) for p in verts)})

    def emit(self, role, poly3, hint, cuts):
        """A face clipped by each half-space (x - E).m >= 0 in `cuts`."""
        for E, m in cuts:
            out = []
            for i, a in enumerate(poly3):
                b = poly3[(i + 1) % len(poly3)]
                fa, fb = _dot(_sub(a, E), m), _dot(_sub(b, E), m)
                if fa >= -1e-12:
                    out.append(a)
                if (fa >= -1e-12) != (fb >= -1e-12):
                    out.append(_add(a, _mul(_sub(b, a), fa / (fa - fb))))
            poly3 = out
            if len(poly3) < 3:
                return []
        self.face(role, poly3, hint)
        return poly3

    def mitred(self, panel, region, out, inn, lines, tier, kind, width, cuts):
        """A member whose end(s) are cut on the mitre planes `cuts`, open there: its
        partner across the edge closes it."""
        if len(region) < 3 or abs(area2(region)) < 1e-10:
            return
        verts = []
        verts += self.emit(tier, [panel.P(u, v, out) for u, v in region], panel.N, cuts)
        verts += self.emit(tier, [panel.P(u, v, -inn) for u, v in region], _mul(panel.N, -1), cuts)
        for i, p in enumerate(region):
            q = region[(i + 1) % len(region)]
            for a, b, c in lines:
                if abs(a * p[0] + b * p[1] - c) < 1e-7 and abs(a * q[0] + b * q[1] - c) < 1e-7:
                    hint = _add(_mul(panel.U, a), _mul(panel.V, b))
                    verts += self.emit(tier, [panel.P(p[0], p[1], out), panel.P(q[0], q[1], out),
                                              panel.P(q[0], q[1], -inn), panel.P(p[0], p[1], -inn)], hint, cuts)
        self.members.append({"tier": tier, "kind": kind, "panel": panel.name, "width": width,
                             "standing": max(_dot(_sub(p, panel.O), panel.N) for p in verts),
                             "behind": -min(_dot(_sub(p, panel.O), panel.N) for p in verts), "mitred": len(cuts)})

    def mitre_edges(self, p):
        """The edges of `p` across which its primaries meet a partner: a shared horizontal
        edge whose other panel has the same bays."""
        out = []
        for i, a, b, _, _ in p.edges():
            e, _ = self.edge_of[(p.name, i)]
            if len(e["owners"]) != 2 or abs(a[1] - b[1]) > 1e-9:
                continue
            q = next(o for o, _ in e["owners"] if o is not p)
            if q.bays != p.bays or p.bays < 2:
                continue
            n2, _ = p.inward(i)
            tA = _add(_mul(p.U, n2[0]), _mul(p.V, n2[1]))
            j = next(j for o, j in e["owners"] if o is q)
            m2, _ = q.inward(j)
            tB = _add(_mul(q.U, m2[0]), _mul(q.V, m2[1]))
            out.append((i, a, _sub(tA, tB), e["kind"]))
        return out

    # the build ---------------------------------------------------------------------
    def build(self):
        v, d = self.v, self.data
        f = FORMS[v["form"]](v, d)
        self.form = f
        self.panels = f["panels"]
        self.meta.update({"eave_m": f["eave_m"], "top_m": f["top_m"], "centre": list(f["centre"])})
        self._edges()
        for p in self.panels:
            self._panel(p)
        self._plinth()
        self._floor()
        for name, pts in f["eaves"].items():
            g = next((g for g in v["gutters"] if g["eave"] == name), None)
            if g is None:
                continue
            self._gutter(name, pts, {"left": "start", "right": "end", "both": "both"}[g["outlet"]])
        if v.get("ridge_vent"):
            for r0, r1, pitch in f["ridges"]:
                self._vent(r0, r1, pitch)
        self._planting()
        return self

    def _edges(self):
        by = {}
        for p in self.panels:
            for i, a, b, _, _ in p.edges():
                by.setdefault(frozenset((key3(a), key3(b))), []).append((p, i))
        self.edge_of = {}
        tiers = self.data["tiers"]
        for k, owners in by.items():
            if len(owners) > 2:
                raise ValueError(f"{self.v['id']}: an edge is shared by {len(owners)} panels")
            pa, ia = owners[0]
            pb, ib = owners[1] if len(owners) == 2 else (None, None)
            a, b = pa.pts[ia], pa.pts[(ia + 1) % len(pa.pts)]
            dvec = _unit(_sub(b, a))
            ang = math.degrees(math.acos(max(-1.0, min(1.0, _dot(pa.N, pb.N))))) if pb else None
            if pb is None:
                kind = "base" if abs(a[1]) < 1e-9 and abs(b[1]) < 1e-9 else "free"
            elif abs(dvec[1]) > 0.999:
                kind = "corner"
            elif abs(dvec[1]) < 1e-6:
                if pa.vertical and pb.vertical:
                    kind = "transom"
                elif pa.vertical != pb.vertical:
                    kind = "eave"
                else:
                    kind = "ridge" if ang >= NEAR_COPLANAR_DEG else "joint"
            else:
                kind = "verge" if pa.vertical != pb.vertical else "hip"
            tier = TIER_OF.get(kind)
            style = "none" if tier is None else (
                "edge" if pb is not None and ang >= NEAR_COPLANAR_DEG else ("half" if pb is not None else "strip"))
            e = {"key": k, "kind": kind, "tier": tier, "style": style, "a": a, "b": b, "angle_deg": ang,
                 "owners": [(pa, ia)] + ([(pb, ib)] if pb else [])}
            for p, i in e["owners"]:
                other = next((q for q, _ in e["owners"] if q is not p), None)
                inset = 0.0
                if style == "edge":
                    h = self.edge_half(kind)
                    n2, _ = p.inward(i)
                    t3 = _add(_mul(p.U, n2[0]), _mul(p.V, n2[1]))
                    inset = h / abs(_dot(t3, other.N))
                elif style == "half":
                    inset = tiers[tier]["width_m"] / 2
                elif style == "strip":
                    inset = tiers[tier]["width_m"]
                self.edge_of[(p.name, i)] = (e, inset)
            self.edges.append(e)
        for e in self.edges:
            if e["style"] == "edge":
                self._edge_member(e)

    def edge_half(self, kind):
        t = self.data["tiers"][TIER_OF[kind]]
        return t["verge_half_m"] if kind == "verge" else t["edge_half_m"]

    def _edge_member(self, e):
        """A member on the edge between two panels: a parallelogram section with two faces
        parallel to each panel at the tier's half width, run the edge's length."""
        (pa, _), (pb, _) = e["owners"]
        h = self.edge_half(e["kind"])
        nA, nB = pa.N, pb.N
        c = _dot(nA, nB)
        xs = []
        for sA, sB in ((1, 1), (1, -1), (-1, -1), (-1, 1)):
            al = h * (sA - c * sB) / (1 - c * c)
            be = h * (sB - c * sA) / (1 - c * c)
            xs.append(_add(_mul(nA, al), _mul(nB, be)))
        a, b = e["a"], e["b"]
        dvec = _unit(_sub(b, a))
        ends, cuts = [], []
        for end, sgn in ((a, -1.0), (b, 1.0)):
            meets = [o for o in self.edges if o is not e and key3(end) in o["key"]]
            twins = [o for o in meets if o["kind"] == e["kind"] and o["style"] == "edge"]
            for o in twins:     # mitre on the plane bisecting the two members' directions
                d_o = _unit(_sub(o["b"], o["a"]) if key3(o["a"]) == key3(end) else _sub(o["a"], o["b"]))
                cuts.append((end, _sub(_mul(dvec, -sgn), d_o)))
            ext = 0.0
            if e["kind"] in ("eave", "ridge") and any(o["kind"] == "verge" for o in meets) and not twins:
                ext = h + 0.007
            on_ground = abs(end[1]) < 1e-9
            on_host = self.form["host"] and abs(end[2]) < 1e-9
            ends.append((_add(end, _mul(dvec, sgn * (ext if not twins else 0.3))), sgn,
                         not (on_ground or on_host or twins)))
        (A, _, capA), (B, _, capB) = ends
        for k in range(4):
            x0, x1 = xs[k], xs[(k + 1) % 4]
            self.emit(e["tier"], [_add(A, x0), _add(B, x0), _add(B, x1), _add(A, x1)], _add(x0, x1), cuts)
        for (E, sgn, cap) in ends:
            if cap:
                self.face(e["tier"], [_add(E, x) for x in xs], _mul(dvec, sgn))
        self.members.append({"tier": e["tier"], "kind": e["kind"], "panel": pa.name, "width": 2 * h,
                             "standing": max(_dot(x, nA) for x in xs), "behind": -min(_dot(x, nA) for x in xs),
                             "edge": True})

    def _inner(self, p):
        poly = list(p.poly)
        for i, *_ in p.edges():
            e, inset = self.edge_of[(p.name, i)]
            n2, a = p.inward(i)
            poly = hclip(poly, -n2[0], -n2[1], -(inset + n2[0] * a[0] + n2[1] * a[1]))
        return poly

    def _panel(self, p):
        tiers = self.data["tiers"]
        T1, T2, T3 = tiers["primary"], tiers["secondary"], tiers["tertiary"]
        inner = self._inner(p)
        # strips on free and near-coplanar edges, fitted between the other edges' insets
        for i, *_ in p.edges():
            e, inset = self.edge_of[(p.name, i)]
            if e["style"] not in ("half", "strip"):
                continue
            n2, a = p.inward(i)
            reg = list(p.poly)
            for j, *_ in p.edges():
                if j == i:
                    continue
                _, ins_j = self.edge_of[(p.name, j)]
                m2, b0 = p.inward(j)
                reg = hclip(reg, -m2[0], -m2[1], -(ins_j + m2[0] * b0[0] + m2[1] * b0[1]))
            line = (n2[0], n2[1], inset + n2[0] * a[0] + n2[1] * a[1])
            reg = hclip(reg, *line)
            t = tiers[e["tier"]]
            self.slab(p, reg, t["proud_m"], t["inner_m"], [line], e["tier"], e["kind"], t["width_m"])
        if len(inner) < 3:
            return
        us = [q[0] for q in inner]
        u_lo, u_hi = min(us), max(us)
        role = "glass" if p.kind == "glass" else "substitute"
        pt = self.data["plinth"]["height_m"]
        v_sill = p.v_of_y(pt) if p.plinth else None
        v_glass = v_sill + T2["width_m"] if p.plinth else -1e9
        # the vertical members: primaries at the bays, the door's jambs, bars between
        verticals = []          # (u0, u1, tier, kind, v_from)
        base = min(p.edges(), key=lambda e: (e[3][1] + e[4][1]))
        b_lo, b_hi = sorted((base[3][0], base[4][0]))
        w1 = T1["width_m"]
        for k in range(1, p.bays):
            c = b_lo + (b_hi - b_lo) * k / p.bays
            verticals.append((c - w1 / 2, c + w1 / 2, "primary",
                              "rib" if p.name.startswith("facet") else ("post" if p.vertical else "rafter"),
                              v_sill if p.plinth else -1e9))
        door = None
        if p.door:
            dd = self.data["door"]
            c = b_lo + (b_hi - b_lo) * p.door["at"]
            hw_ = dd["width_m"] / 2
            door = {"c": c, "l": c - hw_, "r": c + hw_, "head": p.v_of_y(dd["height_m"]),
                    "lock": p.v_of_y(dd["lock_rail_m"]), "floor": p.v_of_y(dd["floor_m"])}
            for s in (-1, 1):
                j0 = c + s * hw_
                j1 = j0 + s * T1["width_m"]
                verticals.append((min(j0, j1), max(j0, j1), "primary", "jamb", p.v_of_y(0.0)))
        verticals.sort()
        # bars, evenly dividing each run between primaries (the door's own column apart)
        stops = [(u_lo, u_lo)] + [(a, b) for a, b, *_ in verticals] + [(u_hi, u_hi)]
        bars, segments = [], []
        pmax = self.data["glass"]["pane_width_m"]["max"]
        for (_, a), (b, _) in zip(stops, stops[1:]):
            if door and a >= door["l"] - 1e-9 and b <= door["r"] + 1e-9:
                continue
            gap = b - a
            if gap <= 1e-6:
                continue
            n = max(1, math.ceil((gap + 1e-9) / (pmax + T3["width_m"])))
            while (gap - (n - 1) * T3["width_m"]) / n > pmax + 1e-9:
                n += 1
            cw = (gap - (n - 1) * T3["width_m"]) / n
            seg = len(segments)
            segments.append({"a": a, "b": b, "cells": n, "cell_m": cw})
            for k in range(1, n):
                u0 = a + k * cw + (k - 1) * T3["width_m"]
                bars.append((u0, u0 + T3["width_m"], seg))
        # build them
        mitres = self.mitre_edges(p)
        for u0, u1, tier, kind, vfrom in verticals:
            t = tiers[tier]
            lines = [(-1, 0, -u0), (1, 0, u1)]
            if kind in ("post", "rafter", "rib") and mitres:
                reg = list(p.poly)
                cut_ids = {i for i, *_ in mitres}
                for j, *_ in p.edges():
                    _, ins_j = self.edge_of[(p.name, j)]
                    m2, b0 = p.inward(j)
                    d = -0.3 if j in cut_ids else ins_j
                    reg = hclip(reg, -m2[0], -m2[1], -(d + m2[0] * b0[0] + m2[1] * b0[1]))
                reg = hclip(hclip(hclip(reg, -1, 0, -u0), 1, 0, u1), 0, -1, -vfrom)
                self.mitred(p, reg, t["proud_m"], t["inner_m"], lines, tier, kind, u1 - u0,
                            [(a, m) for _, a, m, _ in mitres])
            else:
                reg = hclip(hclip(hclip(inner, -1, 0, -u0), 1, 0, u1), 0, -1, -vfrom)
                self.slab(p, reg, t["proud_m"], t["inner_m"], lines, tier, kind, u1 - u0)
            if kind == "rib":
                self.ribs.append((p.name, (u0 + u1) / 2))
        joints = [m for m in mitres if m[3] == "joint"]   # a curvilinear roof's bars run on across
        for u0, u1, _ in bars:
            lines = [(-1, 0, -u0), (1, 0, u1)]
            if joints:
                reg = list(p.poly)
                cut_ids = {i for i, *_ in joints}
                for j, *_ in p.edges():
                    _, ins_j = self.edge_of[(p.name, j)]
                    m2, b0 = p.inward(j)
                    d = -0.3 if j in cut_ids else ins_j
                    reg = hclip(reg, -m2[0], -m2[1], -(d + m2[0] * b0[0] + m2[1] * b0[1]))
                reg = hclip(hclip(hclip(reg, -1, 0, -u0), 1, 0, u1), 0, -1, -v_glass)
                self.mitred(p, reg, T3["proud_m"], T3["inner_m"], lines, "tertiary", "bar", u1 - u0,
                            [(a, m) for _, a, m, _ in joints])
            else:
                reg = hclip(hclip(hclip(inner, -1, 0, -u0), 1, 0, u1), 0, -1, -v_glass)
                self.slab(p, reg, T3["proud_m"], T3["inner_m"], lines, "tertiary", "bar", u1 - u0)
        if p.plinth:     # the sill plate on the coping, stopped at the door's jambs
            spans = [(u_lo, u_hi)]
            if door:
                jl = min(a for a, b, t_, k_, _ in verticals if k_ == "jamb")
                jr = max(b for a, b, t_, k_, _ in verticals if k_ == "jamb")
                spans = [(u_lo, jl), (jr, u_hi)]
            for ua, ub in spans:
                reg = hclip(hclip(hclip(hclip(inner, 0, -1, -v_sill), 0, 1, v_sill + T2["width_m"]),
                                  -1, 0, -ua), 1, 0, ub)
                self.slab(p, reg, T2["proud_m"], T2["inner_m"], [(0, 1, v_sill + T2["width_m"])],
                          "secondary", "sill_plate", T2["width_m"])
        # panes: every cell between verticals, above the sill plate
        cuts = sorted([(a, b) for a, b, *_ in verticals] + [(a, b) for a, b, _ in bars])
        edges_u = [u_lo] + [x for ab in cuts for x in ab] + [u_hi]
        for k in range(0, len(edges_u), 2):
            a, b = edges_u[k], edges_u[k + 1]
            if b - a <= 1e-6:
                continue
            if door and a >= door["l"] - 1e-9 and b <= door["r"] + 1e-9:
                continue
            cell = hclip(hclip(hclip(inner, -1, 0, -a), 1, 0, b), 0, -1, -v_glass)
            self._pane(p, cell, role, self._segment_of(segments, a, b))
        if door:
            self._door(p, inner, door, role)

    @staticmethod
    def _segment_of(segments, a, b):
        for i, s in enumerate(segments):
            if a >= s["a"] - 1e-9 and b <= s["b"] + 1e-9:
                return i
        return None

    def _pane(self, p, cell, role, segment):
        if len(cell) < 3 or abs(area2(cell)) < 1e-9:
            return
        self.face(role, [p.P(u, v) for u, v in cell], p.N)
        us = [q[0] for q in cell]
        self.panes.append({"panel": p.name, "poly": cell, "role": role, "segment": segment,
                           "u_width": max(us) - min(us), "verts": [p.P(u, v) for u, v in cell]})

    def _door(self, p, inner, door, role):
        T2, T3 = self.data["tiers"]["secondary"], self.data["tiers"]["tertiary"]
        l, r, c = door["l"], door["r"], door["c"]
        hd, lk, fl = door["head"], door["lock"], door["floor"]
        col = hclip(hclip(inner, -1, 0, -l), 1, 0, r)
        for v0, kind in ((hd, "door_head"), (lk, "lock_rail")):
            reg = hclip(hclip(col, 0, -1, -v0), 0, 1, v0 + T2["width_m"])
            self.slab(p, reg, T2["proud_m"], T2["inner_m"], [(0, -1, -v0), (0, 1, v0 + T2["width_m"])],
                      "secondary", kind, T2["width_m"])
        panel = hclip(hclip(col, 0, -1, -fl), 0, 1, lk)
        self.face("door_panel", [p.P(u, v) for u, v in panel], p.N)
        b0, b1 = c - T3["width_m"] / 2, c + T3["width_m"] / 2
        reg = hclip(hclip(hclip(col, -1, 0, -b0), 1, 0, b1), 0, -1, -(lk + T2["width_m"]))
        self.slab(p, reg, T3["proud_m"], T3["inner_m"], [(-1, 0, -b0), (1, 0, b1)], "tertiary", "bar",
                  T3["width_m"])
        seg = f"door:{p.name}"
        for a, b in ((l, b0), (b1, r)):
            for v0, v1 in ((lk + T2["width_m"], hd), (hd + T2["width_m"], 1e9)):
                cell = hclip(hclip(hclip(hclip(col, -1, 0, -a), 1, 0, b), 0, -1, -v0), 0, 1, v1)
                self._pane(p, cell, role, seg)
        self.meta["door"] = {"panel": p.name, "width_m": r - l, "head_m": hd, "lock_m": lk}

    # the plinth --------------------------------------------------------------------
    def _plan_segments(self):
        pts = self.form["plan"]
        n = len(pts)
        cx = sum(q[0] for q in pts) / n
        cz = sum(q[1] for q in pts) / n
        segs = []
        m = n if self.form["closed"] else n - 1
        for i in range(m):
            a, b = pts[i], pts[(i + 1) % n]
            o = hnorm(b[1] - a[1], -(b[0] - a[0]))
            mid = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
            if o[0] * (mid[0] - cx) + o[2] * (mid[1] - cz) < 0:
                o = _mul(o, -1)
            segs.append((a, b, o))
        return segs

    def _door_gap(self, a, b):
        """The plinth's gap on the plan segment a-b, if a door stands in it: from jamb
        centre to jamb centre, so no plinth end lies in a jamb's face."""
        T1 = self.data["tiers"]["primary"]
        for p in self.panels:
            if not p.door:
                continue
            base = [q for q in p.pts if abs(q[1]) < 1e-9]
            if {key3((a[0], 0.0, a[1])), key3((b[0], 0.0, b[1]))} != {key3(q) for q in base}:
                continue
            half = self.data["door"]["width_m"] / 2 + T1["width_m"] / 2
            # the door's fraction is along the panel's base edge in u; map it to this segment
            ua, ub = p.uv((a[0], 0.0, a[1]))[0], p.uv((b[0], 0.0, b[1]))[0]
            uc = min(ua, ub) + abs(ub - ua) * p.door["at"]
            c = abs(uc - ua)
            return (c - half, c + half)
        return None

    def _plinth(self):
        pl = self.data["plinth"]
        pt, ct = pl["height_m"], pl["coping"]["thickness_m"]
        po, pi, co, ci = pl["out_m"], pl["in_m"], pl["coping"]["out_m"], pl["coping"]["in_m"]
        prof = [(po, 0), (po, pt - ct), (co, pt - ct), (co, pt), (-ci, pt), (-ci, pt - ct), (-pi, pt - ct), (-pi, 0)]
        edges = [(i, i + 1) for i in range(7)]
        caps = [[(-pi, 0), (po, 0), (po, pt - ct), (-pi, pt - ct)], [(-ci, pt - ct), (co, pt - ct), (co, pt), (-ci, pt)]]
        segs = self._plan_segments()
        runs = []      # each: list of (point, o_segment)
        cur = []
        order = list(range(len(segs)))
        gaps = {i: self._door_gap(a, b) for i, (a, b, o) in enumerate(segs)}
        if self.form["closed"] and any(gaps.values()):
            k = next(i for i in order if gaps[i])
            order = order[k:] + order[:k + 1]
        for idx, i in enumerate(order):
            a, b, o = segs[i]
            L = math.dist(a, b)
            t = ((b[0] - a[0]) / L, (b[1] - a[1]) / L)
            at = lambda s: (a[0] + t[0] * s, a[1] + t[1] * s)
            g = gaps[i]
            first, last = idx == 0, idx == len(order) - 1
            if g and self.form["closed"] and first:
                cur = [(at(g[1]), o)]
                continue
            if g and self.form["closed"] and last:
                cur.append((a, o))
                cur.append((at(g[0]), o))
                runs.append(cur)
                cur = []
                continue
            cur.append((a, o))
            if g:
                cur.append((at(g[0]), o))
                runs.append(cur)
                cur = [(at(g[1]), o)]
        if cur:
            if self.form["closed"]:
                cur.append(cur[0])
                runs.append(cur)
            else:
                a, b, o = segs[order[-1]]
                cur.append((b, o))
                runs.append(cur)
        for run in runs:
            if len(run) < 2:
                continue
            pts = [(q[0], 0.0, q[1]) for q, _ in run]
            seg_o = [run[i][1] for i in range(len(run) - 1)]
            frames = ([seg_o[0]] + [mitre(seg_o[i - 1], seg_o[i]) for i in range(1, len(run) - 1)]
                      + [seg_o[-1]])
            closed_loop = key3(pts[0]) == key3(pts[-1])
            if closed_loop:
                m = mitre(seg_o[-1], seg_o[0])
                frames[0] = frames[-1] = m
            self._sweep(["plinth", "coping", "coping", "coping", "coping", "coping", "plinth"], pts,
                        [(f, Y) for f in frames], seg_o, prof, edges)
            for end, sgn in ((0, -1.0), (len(pts) - 1, 1.0)):
                if closed_loop:
                    break
                if self.form["host"] and abs(pts[end][2]) < 1e-9:
                    continue
                t = _unit(_sub(pts[1], pts[0])) if end == 0 else _unit(_sub(pts[-1], pts[-2]))
                fr = frames[end]
                for poly, role in zip(caps, ("plinth", "coping")):
                    self.face(role, [_add(pts[end], _add(_mul(fr, a_), _mul(Y, b_))) for a_, b_ in poly],
                              _mul(t, sgn))
            for i in range(len(pts) - 1):
                A = _add(pts[i], _mul(frames[i], co))
                B = _add(pts[i + 1], _mul(frames[i + 1], co))
                self.coping_lines.append((plan(A), plan(B)))

    def _sweep(self, roles, pts, frames, seg_frames, prof, edges, cap_start=None, cap_end=None):
        """Skin `prof` along the stations `pts`. frames[i] = (a axis, b axis) at station i,
        already mitred; seg_frames[s] = the segment's own unit `a` axis, for the hints."""
        for s in range(len(pts) - 1):
            sa = seg_frames[s]
            sb = frames[s][1]
            for k, (i, j) in enumerate(edges):
                pa, pb = prof[i], prof[j]
                q = [_add(pts[s], _add(_mul(frames[s][0], pa[0]), _mul(frames[s][1], pa[1]))),
                     _add(pts[s + 1], _add(_mul(frames[s + 1][0], pa[0]), _mul(frames[s + 1][1], pa[1]))),
                     _add(pts[s + 1], _add(_mul(frames[s + 1][0], pb[0]), _mul(frames[s + 1][1], pb[1]))),
                     _add(pts[s], _add(_mul(frames[s][0], pb[0]), _mul(frames[s][1], pb[1])))]
                n2 = (pb[1] - pa[1], -(pb[0] - pa[0]))
                hint = _add(_mul(sa, n2[0]), _mul(sb, n2[1]))
                self.face(roles[k] if isinstance(roles, list) else roles, q, hint)

    def _floor(self):
        pl = self.data["plinth"]
        segs = self._plan_segments()
        xs = [q[0] for q in self.form["plan"]]
        zs = [q[1] for q in self.form["plan"]]
        poly = [(min(xs) - 1, min(zs) - 1), (max(xs) + 1, min(zs) - 1), (max(xs) + 1, max(zs) + 1),
                (min(xs) - 1, max(zs) + 1)]
        if self.form["host"]:
            poly = hclip(poly, 0, -1, 0.0)            # z >= 0: the house wall closes the back
        for a, b, o in segs:                            # inside every plinth's inner face
            poly = hclip(poly, o[0], o[2], o[0] * a[0] + o[2] * a[1] - pl["in_m"])
        y = self.data["door"]["floor_m"]
        self.face("floor", [(x, y, z) for x, z in poly], Y)
        self.meta["floor"] = poly

    # rainwater ---------------------------------------------------------------------
    def _gutter(self, name, eave, outlet):
        rw = self.data["rainwater"]
        gk = self.k04["gutter"]
        r = gk["kinds"][rw["gutter_kind"]]["diameter_m"] / 2
        fall = gk["fall"]
        dk = self.k04["downpipe"]
        rp = dk["kinds"][rw["pipe_kind"]]["diameter_m"] / 2
        # outward plan normals per eave segment
        cx, cz = self.form["centre"][0], self.form["centre"][2]
        so = []
        for a, b in zip(eave, eave[1:]):
            o = hnorm(b[2] - a[2], -(b[0] - a[0]))
            mid = ((a[0] + b[0]) / 2, (a[2] + b[2]) / 2)
            if o[0] * (mid[0] - cx) + o[2] * (mid[1] - cz) < 0:
                o = _mul(o, -1)
            so.append(o)
        # how far the eave's members stand out of the wall plane: the gutter hangs clear
        reach = 0.0
        for p in self.prims.get("secondary", Prim("x")).pos + self.prims.get("primary", Prim("x")).pos:
            q = _sub(p, self.O)
            for (a, b), o in zip(zip(eave, eave[1:]), so):
                ab = (b[0] - a[0], 0.0, b[2] - a[2])
                t = _dot(_sub(q, a), ab) / _dot(ab, ab)
                off = _dot(_sub(q, a), o)
                if -0.02 <= t <= 1.02 and abs(q[1] - a[1]) < 0.12 and off < 0.15:
                    reach = max(reach, off)
        dg = reach + r + 0.005
        y_hi = eave[0][1] - 0.02
        pts = []
        for i, e in enumerate(eave):
            if i == 0:
                m = so[0]
            elif i == len(eave) - 1:
                m = so[-1]
            else:
                m = mitre(so[i - 1], so[i])
            pts.append(_add((e[0], y_hi, e[2]), _mul(m, dg)))
        trim = rw["end_trim_m"]
        pts[0] = _add(pts[0], _mul(_unit(_sub(pts[1], pts[0])), trim))
        pts[-1] = _add(pts[-1], _mul(_unit(_sub(pts[-2], pts[-1])), trim))
        frames_o = [so[0]] + [mitre(so[i - 1], so[i]) for i in range(1, len(pts) - 1)] + [so[-1]]
        seg_o = list(so)
        # the fall: to one end, or from the middle to both
        if outlet == "both":
            S = sum(math.dist(plan(a), plan(b)) for a, b in zip(pts, pts[1:]))
            acc = 0.0
            for i in range(len(pts) - 1):
                l = math.dist(plan(pts[i]), plan(pts[i + 1]))
                if acc <= S / 2 < acc + l - 1e-9 and S / 2 - acc > 1e-9:
                    t = (S / 2 - acc) / l
                    mid = _add(pts[i], _mul(_sub(pts[i + 1], pts[i]), t))
                    pts.insert(i + 1, mid)
                    frames_o.insert(i + 1, seg_o[i])
                    seg_o.insert(i + 1, seg_o[i])
                    break
                acc += l
        S = sum(math.dist(plan(a), plan(b)) for a, b in zip(pts, pts[1:]))
        acc, ys = 0.0, []
        for i, q in enumerate(pts):
            if i:
                acc += math.dist(plan(pts[i - 1]), plan(q))
            drop = {"end": acc, "start": S - acc, "both": abs(acc - S / 2)}[outlet]
            ys.append(y_hi - fall * drop)
        pts = [(q[0], y, q[2]) for q, y in zip(pts, ys)]
        th = 0.003
        n = 6
        outer = [(r * math.cos(math.pi + math.pi * k / n), r * math.sin(math.pi + math.pi * k / n)) for k in range(n + 1)]
        inner = [((r - th) * math.cos(math.pi + math.pi * k / n), (r - th) * math.sin(math.pi + math.pi * k / n))
                 for k in range(n, -1, -1)]
        prof = outer + inner
        edges = [(i, (i + 1) % len(prof)) for i in range(len(prof))]
        self._sweep("gutter", pts, [(f, Y) for f in frames_o], seg_o, prof, edges)
        for end, sgn in ((0, -1.0), (len(pts) - 1, 1.0)):
            t = _unit(_sub(pts[1], pts[0])) if end == 0 else _unit(_sub(pts[-1], pts[-2]))
            self.face("gutter", [_add(pts[end], _add(_mul(frames_o[end], a), _mul(Y, b))) for a, b in outer],
                      _mul(t, sgn))
        # brackets at K04's spacing, straps across the gutter's mouth
        sp = gk["bracket"]["spacing_m"]
        bw = gk["bracket"]["section_m"][0] / 2
        s_at = sp / 2
        acc = 0.0
        for i in range(len(pts) - 1):
            A, B = pts[i], pts[i + 1]
            l = math.dist(plan(A), plan(B))
            t = _unit(_sub(B, A))
            o = seg_o[i]
            while s_at <= acc + l:
                C = _add(A, _mul(_sub(B, A), (s_at - acc) / l))
                C = _add(C, (0.0, 0.004, 0.0))
                self.face("bracket", [_add(C, _add(_mul(o, -r - 0.006), _mul(t, -bw))),
                                      _add(C, _add(_mul(o, r + 0.006), _mul(t, -bw))),
                                      _add(C, _add(_mul(o, r + 0.006), _mul(t, bw))),
                                      _add(C, _add(_mul(o, -r - 0.006), _mul(t, bw)))], Y)
                s_at += sp
            acc += l
        g = {"eave": name, "path": pts, "radius_m": r, "offset_m": dg, "outlet": outlet, "length_m": S,
             "rim_m": [q[1] for q in pts], "eave_line": eave}
        self.gutters.append(g)
        ends = {"end": [len(pts) - 1], "start": [0], "both": [0, len(pts) - 1]}[outlet]
        for end in ends:
            nb = end - 1 if end else 1
            t = _unit(_sub(pts[nb], pts[end]))
            out = _add(pts[end], _mul(t, rw["outlet_inset_m"]))
            o = seg_o[end - 1] if end else seg_o[0]
            self._pipe(out, o, r, rp, dg, g)

    def _pipe(self, out, o, r, rp, dg, g):
        dk = self.k04["downpipe"]
        pl = self.data["plinth"]
        shoe = dk["shoe"]
        kick = math.radians(shoe["kick_deg"])
        o_need = pl["coping"]["out_m"] + dk["offset_from_wall_m"] + rp
        o_p = max(dg, o_need)
        top = (out[0], out[1] - r + 0.002, out[2])
        st = [top, _add(top, (0.0, -0.08, 0.0))]
        if o_p > dg + 1e-6:
            dd = o_p - dg
            st.append(_add(st[-1], _add(_mul(o, dd), (0.0, -dd / math.tan(kick), 0.0))))
        y_shoe = shoe["end_above_grade_m"] + shoe["length_m"] * math.cos(kick)
        st.append((st[-1][0], y_shoe, st[-1][2]))
        st.append(_add(st[-1], _add(_mul(o, shoe["length_m"] * math.sin(kick)),
                                    (0.0, -shoe["length_m"] * math.cos(kick), 0.0))))
        s = _unit(_cross(o, Y))
        ms = []
        for a, b in zip(st, st[1:]):
            t = _unit(_sub(b, a))
            ms.append(_unit(_cross(t, s)))
        frames = [(s, ms[0])] + [(s, mitre(ms[i - 1], ms[i])) for i in range(1, len(st) - 1)] + [(s, ms[-1])]
        k = 8
        prof = [(rp * math.cos(2 * math.pi * i / k + math.pi / k), rp * math.sin(2 * math.pi * i / k + math.pi / k))
                for i in range(k)]
        edges = [(i, (i + 1) % k) for i in range(k)]
        # hints: the segment's own frame
        for si in range(len(st) - 1):
            self._sweep("pipe", st[si:si + 2], frames[si:si + 2], [s], prof, edges)
        t_end = _unit(_sub(st[-1], st[-2]))
        self.face("pipe", [_add(st[-1], _add(_mul(s, a), _mul(frames[-1][1], b))) for a, b in prof], t_end)
        # the splash stone under the shoe
        e = st[-1]
        hs, th = 0.15, 0.04
        c0 = (e[0], 0.0, e[2])
        u, w = s, o
        corners = [_add(c0, _add(_mul(u, su * hs), _mul(w, sw * hs))) for su, sw in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
        topc = [_add(q, (0.0, th, 0.0)) for q in corners]
        self.face("coping", topc, Y)
        for i in range(4):
            a, b = corners[i], corners[(i + 1) % 4]
            mid = _sub(_mul(_add(a, b), 0.5), c0)
            self.face("coping", [a, b, _add(b, (0.0, th, 0.0)), _add(a, (0.0, th, 0.0))], mid)
        self.pipes.append({"stations": st, "radius_m": rp, "gutter": g["eave"], "outlet": out,
                           "end_above_grade_m": st[-1][1], "o_m": o_p})

    # the ridge ventilator ----------------------------------------------------------
    def _vent(self, r0, r1, pitch):
        rv = self.data["ridge_vent"]
        tp = math.tan(math.radians(pitch))
        e = _unit(_sub(r1, r0))
        s = _unit(_cross(Y, e))
        a = rv["width_m"] / 2
        A = _add(r0, _mul(e, rv["end_inset_m"]))
        B = _sub(r1, _mul(e, rv["end_inset_m"]))
        yR = r0[1]
        y_base = yR - a * tp
        y_top = yR + rv["height_m"]
        oh, cr = rv["cap_overhang_m"], rv["cap_rise_m"]
        at = lambda P, ss, y: (P[0] + s[0] * ss, y, P[2] + s[2] * ss)
        n = rv["louvres"]
        bh = (y_top - y_base) / n
        for sg in (-1.0, 1.0):
            for k in range(n):
                y0 = y_base + k * bh
                q = [at(A, sg * (a + 0.03), y0), at(B, sg * (a + 0.03), y0), at(B, sg * a, y0 + bh),
                     at(A, sg * a, y0 + bh)]
                self.face("vent", q, _add(_mul(s, sg), (0.0, -1.0, 0.0)))
            ab = a - 0.02
            yb = yR - ab * tp - 0.005
            self.face("vent_dark", [at(A, sg * ab, yb), at(B, sg * ab, yb), at(B, sg * ab, y_top),
                                    at(A, sg * ab, y_top)], _mul(s, sg))
            self.face("vent", [at(A, sg * (a + oh), y_top), at(B, sg * (a + oh), y_top), at(B, 0.0, y_top + cr),
                               at(A, 0.0, y_top + cr)], _add(_mul(s, sg), (0.0, 2.0, 0.0)))
        for P, sg in ((A, -1.0), (B, 1.0)):
            self.face("vent", [at(P, -a, y_base), at(P, a, y_base), at(P, a, y_top), at(P, 0.0, y_top + cr),
                               at(P, -a, y_top)], _mul(e, sg))
        self.meta.setdefault("vents", []).append({"from": list(A), "to": list(B), "top_m": y_top + cr})

    # planting ----------------------------------------------------------------------
    def _frustum(self, c, y0, r, h, rot):
        ring0 = [(c[0] + r * math.cos(rot + math.pi * k / 3), y0, c[1] + r * math.sin(rot + math.pi * k / 3))
                 for k in range(6)]
        ring1 = [(c[0] + 0.62 * r * math.cos(rot + math.pi * k / 3), y0 + h, c[1] + 0.62 * r * math.sin(rot + math.pi * k / 3))
                 for k in range(6)]
        for k in range(6):
            a0, b0, a1, b1 = ring0[k], ring0[(k + 1) % 6], ring1[k], ring1[(k + 1) % 6]
            mid = (((a0[0] + b0[0]) / 2) - c[0], 0.0, ((a0[2] + b0[2]) / 2) - c[1])
            self.face("plant", [a0, b0, b1, a1], mid)
        self.face("plant", ring1, Y)

    def _planting(self):
        st = self.data["staging"]
        pl = self.data["plinth"]
        fl = self.data["door"]["floor_m"]
        bn = st["bench"]
        cx, cz = self.form["centre"][0], self.form["centre"][2]
        k_plant = 0
        for _name, a, b in self.form["benches"]:
            L = math.dist(a, b)
            t = ((b[0] - a[0]) / L, (b[1] - a[1]) / L)
            n_in = (-t[1], t[0])
            if n_in[0] * (cx - a[0]) + n_in[1] * (cz - a[1]) < 0:
                n_in = (t[1], -t[0])
            s0, s1 = pl["in_m"] + bn["end_inset_m"], L - pl["in_m"] - bn["end_inset_m"]
            f0, f1 = pl["in_m"] + bn["clear_m"], pl["in_m"] + bn["clear_m"] + bn["depth_m"]
            at = lambda s, f, y: (a[0] + t[0] * s + n_in[0] * f, y, a[1] + t[1] * s + n_in[1] * f)
            h = bn["height_m"]
            tt, nn = (t[0], 0.0, t[1]), (n_in[0], 0.0, n_in[1])
            self.face("bench", [at(s0, f0, h), at(s1, f0, h), at(s1, f1, h), at(s0, f1, h)], Y)
            self.face("bench", [at(s0, f0, fl), at(s1, f0, fl), at(s1, f0, h), at(s0, f0, h)], _mul(nn, -1))
            self.face("bench", [at(s0, f1, fl), at(s1, f1, fl), at(s1, f1, h), at(s0, f1, h)], nn)
            self.face("bench", [at(s0, f0, fl), at(s0, f1, fl), at(s0, f1, h), at(s0, f0, h)], _mul(tt, -1))
            self.face("bench", [at(s1, f0, fl), at(s1, f1, fl), at(s1, f1, h), at(s1, f0, h)], tt)
            pp = st["pot_plants"]
            s = s0 + 0.25
            fm = (f0 + f1) / 2
            while s <= s1 - 0.2:
                sd = seed_of(self.v["id"], 1000 + k_plant)
                hh = pp["height_m"][0] + (pp["height_m"][1] - pp["height_m"][0]) * unit01(sd, 0)
                rr = pp["radius_m"][0] + (pp["radius_m"][1] - pp["radius_m"][0]) * unit01(sd, 8)
                c = at(s, fm, 0.0)
                self._frustum((c[0], c[2]), h, rr, hh, unit01(sd, 4) * math.pi)
                k_plant += 1
                s += pp["spacing_m"]
        if self.form["border"]:
            bd = st["border"]
            (x0, _), (x1, _) = self.form["border"]
            x = x0 + pl["in_m"] + 0.45
            while x <= x1 - pl["in_m"] - 0.45 + 1e-9:
                sd = seed_of(self.v["id"], 2000 + k_plant)
                hh = bd["height_m"][0] + (bd["height_m"][1] - bd["height_m"][0]) * unit01(sd, 0)
                rr = bd["radius_m"][0] + (bd["radius_m"][1] - bd["radius_m"][0]) * unit01(sd, 8)
                self._frustum((x, bd["from_wall_m"]), fl, rr, hh, unit01(sd, 4) * math.pi)
                k_plant += 1
                x += bd["spacing_m"]


# -- the specimen board ----------------------------------------------------------------------

BOARD_PAD = 0.6
BOARD_GAP = 1.6


def extents(h: House):
    xs = [p[0] - h.O[0] for r, pr in h.prims.items() if r not in BOARD_ROLES for p in pr.pos]
    zs = [p[2] - h.O[2] for r, pr in h.prims.items() if r not in BOARD_ROLES for p in pr.pos]
    return min(xs), max(xs), min(zs), max(zs)


def board(h: House):
    x0, x1, z0, z1 = extents(h)
    x0, x1 = x0 - BOARD_PAD, x1 + BOARD_PAD
    if h.form["host"]:
        top = h.meta["top_m"] + 0.6
        dz = 0.45
        h.face("wall", [(x0, 0, 0), (x1, 0, 0), (x1, top, 0), (x0, top, 0)], (0, 0, 1))
        h.face("wall", [(x0, top, 0), (x1, top, 0), (x1, top, -dz), (x0, top, -dz)], Y)
        for x, sx in ((x0, -1.0), (x1, 1.0)):
            h.face("wall", [(x, 0, 0), (x, top, 0), (x, top, -dz), (x, 0, -dz)], (sx, 0, 0))
        zg0 = 0.0
    else:
        zg0 = z0 - 1.0
    zg1 = z1 + 1.4
    h.face("ground", [(x0, 0, zg0), (x1, 0, zg0), (x1, 0, zg1), (x0, 0, zg1)], Y)
    h.meta["board"] = {"x": [x0, x1], "z": [zg0, zg1]}
    return x1 - x0


def load() -> dict:
    return json.loads(DATA.read_text())


def build_variant(v: dict, data: dict, origin=(0.0, 0.0, 0.0), with_board: bool = True, index: int = 0) -> House:
    h = House(v, data, origin, index).build()
    if with_board:
        board(h)
    return h


def build_kit(data: dict | None = None) -> list[House]:
    data = data or load()
    out, x = [], 0.0
    for i, v in enumerate(data["variants"]):
        probe = build_variant(v, data, index=i)
        bx0, bx1 = probe.meta["board"]["x"]
        h = build_variant(v, data, origin=(x - bx0, 0.0, 0.0), index=i)
        out.append(h)
        x += (bx1 - bx0) + BOARD_GAP
    return out


def triangles(h: House, include_board: bool = False) -> int:
    return sum(len(p.idx) // 3 for r, p in h.prims.items() if include_board or r not in BOARD_ROLES)


# -- glTF -------------------------------------------------------------------------------------

def _pad(b: bytes, fill: bytes = b"\x00") -> bytes:
    return b + fill * ((4 - len(b) % 4) % 4)


# -- a house in the scene (T-2306) --------------------------------------------------------------

def host_wing(h: House, host: dict):
    """The wall a host form stands against, closed as a plain block: the bay's own wall
    runs west_m and east_m either side of the bay's centre, and the block goes depth_m
    back (north, -z) and height_m up. Role `wall`, so it is costed apart from the house."""
    x0, x1, D, H = -host["west_m"], host["east_m"], host["depth_m"], host["height_m"]
    h.face("wall", [(x0, 0, 0), (x1, 0, 0), (x1, H, 0), (x0, H, 0)], (0, 0, 1))
    h.face("wall", [(x1, 0, -D), (x0, 0, -D), (x0, H, -D), (x1, H, -D)], (0, 0, -1))
    h.face("wall", [(x0, 0, -D), (x0, 0, 0), (x0, H, 0), (x0, H, -D)], (-1, 0, 0))
    h.face("wall", [(x1, 0, 0), (x1, 0, -D), (x1, H, -D), (x1, H, 0)], (1, 0, 0))
    h.face("wall", [(x0, H, 0), (x1, H, 0), (x1, H, -D), (x0, H, -D)], Y)
    # a base course and a coping band so the block reads as masonry; the base course stops
    # short of the bay, whose plinth and frame end on the wall face
    gap = max(abs(q[0]) for q in h.form["plan"]) + 0.15
    bc, cp = host.get("base_course_m", 0.0), host.get("coping_m", 0.0)
    if bc:
        _band(h, x0, x1, -D, 0.0, 0.0, bc, 0.05, gaps=((-gap, gap),))
    if cp:
        _band(h, x0, x1, -D, 0.0, H - cp, H, 0.05)
    h.meta["host"] = {"x": [x0, x1], "z": [-D, 0.0], "height_m": H}
    if host.get("color"):
        h.meta["host"]["color"] = list(host["color"])


def _band(h: House, x0, x1, zn, zs, y0, y1, out, gaps=()):
    """A course standing `out` proud all round the block between heights y0 and y1, role
    `host_band`, its south face stopped at each (a, b) in `gaps`. The top (and, off the
    ground, the bottom) is tiled in strips that meet and never overlap."""
    xa, xb, zso, zno = x0 - out, x1 + out, zs + out, zn - out
    ys = [(y1, Y)] + ([(y0, (0, -1, 0))] if y0 > 0 else [])

    def strip(u0, u1, w0, w1):
        for y, n in ys:
            h.face("host_band", [(u0, y, w0), (u1, y, w0), (u1, y, w1), (u0, y, w1)], n)

    pieces, cur = [], xa
    for ga, gb in sorted(gaps):
        pieces.append((cur, ga))
        cur = gb
    pieces.append((cur, xb))
    for u0, u1 in pieces:
        h.face("host_band", [(u0, y0, zso), (u1, y0, zso), (u1, y1, zso), (u0, y1, zso)], (0, 0, 1))
        strip(u0, u1, zs, zso)
        for x, sx, cut in ((u0, -1.0, u0 != xa), (u1, 1.0, u1 != xb)):
            if cut:    # an end at a gap: close it back to the wall
                h.face("host_band", [(x, y0, zs), (x, y0, zso), (x, y1, zso), (x, y1, zs)], (sx, 0, 0))
    h.face("host_band", [(xb, y0, zno), (xa, y0, zno), (xa, y1, zno), (xb, y1, zno)], (0, 0, -1))
    strip(xa, xb, zno, zn)
    for x, xo, sx in ((x0, xa, -1.0), (x1, xb, 1.0)):
        h.face("host_band", [(xo, y0, zso), (xo, y0, zno), (xo, y1, zno), (xo, y1, zso)], (sx, 0, 0))
        strip(min(x, xo), max(x, xo), zn, zs)


def structure_house(st: dict, phase: dict, data: dict | None = None) -> House:
    """The conservatory a k13_conservatories record names, built against its host wall."""
    data = data or load()
    form = phase["form"]
    h = House(form["conservatory"]["value"], data).build()
    if h.form["host"]:
        host_wing(h, form["host_wall"]["value"])
    return h


def structure_glb(h: House, data: dict, structure_id: str, phase_id: str, scene_ids) -> bytes:
    name = f"{structure_id}__{phase_id}"
    return to_glb([h], data, host_color=(h.meta.get("host") or {}).get("color"), node_name=name, node_extras={
        "structure_id": structure_id, "phase_id": phase_id, "scene_ids": list(scene_ids)},
        extras={"ticket": "T-2306", "structure": f"data/structures/{structure_id}.json"})


def to_glb(kit: list[House], data: dict, node_name: str | None = None, node_extras: dict | None = None,
           extras: dict | None = None, host_color=None) -> bytes:
    mats = materials(data)
    if node_extras:     # a structure in the scene carries only the materials it draws (T-2306)
        used = {ROLE_MATERIAL[r] for h in kit for r, pr in h.prims.items() if pr.idx}
        mats = {k: m for k, m in mats.items() if k in used}
        if "house_wall" in mats and host_color:
            mats["house_wall"] = {**mats["house_wall"], "color": tuple(host_color)}
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
        entry = {"name": f"k13_{name}", "pbrMetallicRoughness": {
            "baseColorFactor": [*[round(c, 4) for c in m["color"]], alpha],
            "metallicFactor": m.get("metallic", 0.0), "roughnessFactor": m["roughness"]}}
        if alpha < 1.0:
            entry["alphaMode"] = "BLEND"
        materials_out.append(entry)
    for h in kit:
        by_mat: dict[str, list[Prim]] = {}
        for role in ROLE_MATERIAL:   # fixed order
            if role in h.prims and h.prims[role].idx:
                by_mat.setdefault(ROLE_MATERIAL[role], []).append(h.prims[role])
        prims_out = []
        for name in mat_names:
            if name not in by_mat:
                continue
            pos, nrm, uv, conf, idx = [], [], [], [], []
            for pr in by_mat[name]:
                base = len(pos)
                pos += [tuple(round(c, 5) for c in q) for q in pr.pos]
                nrm += pr.nrm
                uv += pr.uv
                conf += pr.conf
                idx += [base + i for i in pr.idx]
            ctype = 5123 if len(pos) < 65536 else 5125
            prims_out.append({"attributes": {
                "POSITION": accessor(pos, 5126, "VEC3", 3, 34962, True),
                "NORMAL": accessor(nrm, 5126, "VEC3", 3, 34962),
                "TEXCOORD_0": accessor(uv, 5126, "VEC2", 2, 34962),
                "_CONFIDENCE": accessor(conf, 5126, "SCALAR", 1, 34962)},
                "indices": accessor(idx, ctype, "SCALAR", 1, 34963),
                "material": mat_names.index(name)})
        meshes.append({"name": node_name or h.v["id"], "primitives": prims_out})
        widths = [p["u_width"] for p in h.panes]
        nodes.append({"name": node_name or h.v["id"], "mesh": len(meshes) - 1, "extras": {**(node_extras or {}),
            "component_id": h.v["id"], "family": "conservatory", "form": h.v["form"], "seed": h.seed,
            "origin": [round(c, 4) for c in h.O],
            "triangles_house": triangles(h), "triangles_with_board": triangles(h, True),
            "sockets": {"base": [0.0, 0.0, 0.0], "eave": [0.0, round(h.meta["eave_m"], 4), 0.0],
                        "top": [0.0, round(h.meta["top_m"], 4), 0.0]},
            "centre": [round(c, 4) for c in h.meta["centre"]],
            "measured": {"panes": len(h.panes),
                         "pane_width_m": [round(min(widths), 4), round(max(widths), 4)],
                         "members": {t: sum(1 for m in h.members if m["tier"] == t) for t in TIERS},
                         "gutters": len(h.gutters), "pipes": len(h.pipes)}}})
        if h.meta.get("host"):
            nodes[-1]["extras"]["host"] = {k: ([round(c, 4) for c in x] if isinstance(x, list) else round(x, 4))
                                           for k, x in h.meta["host"].items()}
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
        "extras": {"k13": {"data": "data/components/prairie_1904/k13_conservatories.json", "ticket": "T-2305",
                           "contract": "data/components/prairie_1904/k01_contract.json",
                           "rainwater": "data/components/prairie_1904/k04_roofs.json", **(extras or {})}},
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
                  f"{DATA.relative_to(ROOT)}: run python3 generators/archetypes/k13_conservatories.py")
            return 1
        print(f"ok   {out.relative_to(ROOT)} is the generator's bytes ({len(blob)} B)")
        return 0
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(blob)
    print(f"wrote {out.relative_to(ROOT)} ({len(blob)} B)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
