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
    # T-1934: the wing's own dressed face (its rustication, pilasters and cornice) is the wall's
    # stone, which the record's `host_wall.color` sets; the drum's dress stays the kit's `stone`
    "host_stone": "house_wall",
    "stonework": "stone", "dome": "glass_substitute", "dome_rib": "frame", "opening": "dark",
    "sky_glass": "glass_sky", "sash": "sash", "interior": "interior_shade",
    "stone_field": "stone_rough",
    "gravel": "gravel",
    "plinth_stone": "stone",
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
        # T-3179: the opaque substitute toned as the 1894 plate and the c. 1897 photograph show
        # Beman's glass catching a pale sky, for the glazing that stands outside a house's one
        # transparent envelope where the pictures read it light, not dark
        "glass_sky": {"color": (0.60, 0.64, 0.66), "roughness": 0.2},
        # T-3164: the sash bars of the range's masonry windows, which the plate reads dark against
        # their pale panes; the paint's colour is reconstructed
        "sash": {"color": (0.20, 0.19, 0.16), "roughness": 0.7},
        # T-3164: a conservatory's planted depth seen through its glass, in shade but not a void
        "interior_shade": {"color": (0.10, 0.12, 0.09), "roughness": 1.0},
        # T-3164: the rusticated field of the Pullman conservatory's podium, which Lowe's print
        # reads a tone darker than the dressed piers and courses framing it; the tone is reconstructed
        "stone_rough": {"color": (0.56, 0.53, 0.46), "roughness": 0.95},
        # T-3164: the Pullman glasshouse ground's drive and walks, which both pictures read as pale
        # as the public walk against the lawn; a buff limestone gravel, its tone reconstructed
        "gravel": {"color": (0.66, 0.62, 0.54), "roughness": 0.95},
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
    n, he, hw = v["facets"], v["eave_m"], v["wall_top_m"]
    roof = v.get("roof", "cone")
    if n < 3:
        raise ValueError(f"{v['id']}: a segmental bay needs at least 3 facets, not {n}")
    if roof not in ("cone", "flat", "curved"):
        raise ValueError(f"{v['id']}: a segmental bay's roof is a cone, flat or curved, not {roof!r}")
    if hw <= he and roof != "flat":
        raise ValueError(f"{v['id']}: wall_top_m {hw} does not rise above eave_m {he}")
    if "rise_m" in v:
        # T-1905: a SEGMENT of a circle rather than its half: the bay meets the wall at
        # +-chord_m/2 and stands rise_m out at its middle, its facets inscribed in that arc
        # (1905 Prairie's conservatory, on the K08 bow its stone base is built on)
        if "radius_m" in v:
            raise ValueError(f"{v['id']}: a segmental bay is sized by radius_m (a half circle) or by "
                             f"chord_m and rise_m (a segment), not both")
        h, rise = v["chord_m"] / 2, v["rise_m"]
        if not 0.0 < rise <= h:
            raise ValueError(f"{v['id']}: a segment rises more than nothing and at most half its chord, not {rise}")
        Rc = (h * h + rise * rise) / (2 * rise)
        cz, half = rise - Rc, math.asin(h / Rc)
        ring = [(Rc * math.sin(half - 2 * half * k / n), cz + Rc * math.cos(half - 2 * half * k / n))
                for k in range(n + 1)]
        ring[0], ring[-1] = (h, 0.0), (-h, 0.0)   # exactly on the wall
        R = h
    else:
        R = v["radius_m"]
        ring = [(R * math.cos(math.pi * k / n), R * math.sin(math.pi * k / n)) for k in range(n + 1)]
        ring[0], ring[-1] = (R, 0.0), (-R, 0.0)       # exactly on the wall
    apex = (0.0, hw, 0.0)
    b = v["bays"]
    P = []
    # T-1905: a curved roof bows each hip of the half cone on the kit's quarter-ellipse (data
    # `curve`, the curvilinear lean-to's): it leaves the upright glass tangent to it and meets
    # the wall level at wall_top_m, every facet cut in horizontal strips that stay planar
    m = int(v.get("curve_facets", data["curve"]["facets"]))   # a variant may cut its curve coarser
    cv = ([(math.cos(math.pi / 2 * j / m), he + (hw - he) * math.sin(math.pi / 2 * j / m)) for j in range(m + 1)]
          if roof == "curved" else [])
    for k in range(n):
        (x0, z0), (x1, z1) = ring[k], ring[k + 1]
        hint = ((x0 + x1) / 2, 0.0, (z0 + z1) / 2)
        P.append(Panel(f"facet_{k}", [(x0, 0, z0), (x1, 0, z1), (x1, he, z1), (x0, he, z0)], hint,
                       plinth=True, bays=b))
        if roof == "cone":
            P.append(Panel(f"roof_{k}", [(x0, he, z0), (x1, he, z1), apex], (hint[0], 1.0, hint[2]), bays=b))
        for j in range(len(cv) - 1):
            (f0, y0), (f1, y1) = cv[j], cv[j + 1]
            lo = [(x0 * f0, y0, z0 * f0), (x1 * f0, y0, z1 * f0)]
            hi = [apex] if j == len(cv) - 2 else [(x1 * f1, y1, z1 * f1), (x0 * f1, y1, z0 * f1)]
            P.append(Panel(f"roof_{k}_{j}", lo + hi, (hint[0], 1.0, hint[2]), bays=b))
    plan_pts = list(reversed(ring))                # left to right along the wall, as the canted bay's
    # the staging runs on the chord of the first and last facets, stood out toward the glass
    if "rise_m" in v:
        # a segment is too shallow for a bench on its end facets' chord: it runs along the
        # house wall, bench_out_m off it, between the second facets' feet, facing the glass
        xb, zb = ring[2][0], v.get("bench_out_m", 0.0)
    else:
        xb, zb = R * math.cos(math.pi / n), R * math.sin(math.pi / n) + v.get("bench_out_m", 0.0)
    deep = v["rise_m"] if "rise_m" in v else R
    return {
        "panels": P, "host": True, "closed": False,
        "plan": plan_pts,
        "eaves": {"front": [(x, he, z) for x, z in plan_pts]},
        "ridges": [], "benches": [("front", (-xb, zb), (xb, zb))], "border": None,
        "eave_m": he, "top_m": hw, "centre": (0.0, hw / 2, deep / 2),
    }


def form_span_apse(v, data):
    """T-3164: a span house whose right end is rounded, as the 1911 sheet draws the east end of
    Pullman's glasshouse range across 18th Street: the end wall is a half-polygon of `facets`
    sides inscribed in a semicircle of half the span's width, under a half-cone of glass
    triangles whose hips all run to the ridge's end. The ridge runs `apex_out_m` past the
    springing, so the two hips off the side roofs do not lie in the springing's own upright
    plane, where they would share faces with the corner posts below them; the side roofs
    stay planar (their slope does not change along the ridge), and the cone's pitch is the
    roof's at the crown of the curve."""
    L, W, he, n = v["length_m"], v["width_m"], v["eave_m"], v["facets"]
    if n < 3:
        raise ValueError(f"{v['id']}: an apse needs at least 3 facets, not {n}")
    R = W / 2
    hr = he + R * math.tan(math.radians(v["pitch_deg"]))
    ring = [(L + R * math.sin(math.pi * k / n), R - R * math.cos(math.pi * k / n)) for k in range(n + 1)]
    ring[0], ring[-1] = (L, 0.0), (L, W)           # exactly on the span's eave lines
    apex = (L + v.get("apex_out_m", 0.25 * R), hr, R)
    door = v.get("door") or {}
    b = v["bays"]
    P = [
        Panel("front", [(0, 0, W), (L, 0, W), (L, he, W), (0, he, W)], (0, 0, 1), plinth=True, bays=b),
        Panel("back", [(L, 0, 0), (0, 0, 0), (0, he, 0), (L, he, 0)], (0, 0, -1), plinth=True, bays=b),
        Panel("roof_front", [(0, he, W), (L, he, W), apex, (0, hr, R)], (0, 1, 1), bays=b),
        Panel("roof_back", [(L, he, 0), (0, he, 0), (0, hr, R), apex], (0, 1, -1), bays=b),
        Panel("end_left", [(0, 0, 0), (0, 0, W), (0, he, W), (0, hr, R), (0, he, 0)], (-1, 0, 0), plinth=True,
              door=door if door.get("wall") == "end_left" else None),
    ]
    for k in range(n):
        (x0, z0), (x1, z1) = ring[k], ring[k + 1]
        hint = ((x0 + x1) / 2 - L, 0.0, (z0 + z1) / 2 - R)
        P.append(Panel(f"apse_{k}", [(x0, 0, z0), (x1, 0, z1), (x1, he, z1), (x0, he, z0)], hint, plinth=True,
                       bays=1))
        P.append(Panel(f"apse_roof_{k}", [(x0, he, z0), (x1, he, z1), apex], (hint[0], 1.0, hint[2]), bays=1))
    return {
        "panels": P, "host": False, "closed": True,
        "plan": [(0, 0)] + ring + [(0, W)],
        # one eave all the way round, back, curve and front, so the curve sheds too
        "eaves": {"round": [(0, he, 0)] + [(x, he, z) for x, z in ring] + [(0, he, W)]},
        "ridges": [((0, hr, R), apex, v["pitch_deg"])],
        "benches": [("front", (0, W), (L, W)), ("back", (L, 0), (0, 0))], "border": None,
        "eave_m": he, "top_m": hr, "centre": ((L + R) / 2, hr / 2, R),
    }


def vault_section(v, data):
    """T-3179: one half of a vault's section, [(z, y)] from the eave (z 0, the upright wall
    leaving it tangent) to the crown (z = width / 2). `pointed`: an arc whose centre stands on
    the springing line, so the two halves meet at a point, as Beman's conservatory over the
    Pullman glasshouses does in the 1894 Inland Architect plate (it must rise at least half its
    span); `elliptic`: a quarter-ellipse, so the halves meet level at the crown, as the low
    range behind it does."""
    W, he, rise = v["width_m"], v["eave_m"], v["rise_m"]
    n = v.get("facets") or data["curve"]["facets"]
    h = W / 2
    if v.get("section", "pointed") == "pointed":
        if rise < h:
            raise ValueError(f"{v['id']}: a pointed vault rises at least half its span ({h:.3f} m), not {rise}")
        c = (rise * rise - h * h) / (2 * h)      # the centre's offset past the crown: (h + c)^2 - c^2 = rise^2
        r, t1 = h + c, math.acos(c / (h + c))
        pts = [(r * (1 - math.cos(t1 * k / n)), he + r * math.sin(t1 * k / n)) for k in range(n + 1)]
    else:
        pts = [(h * (1 - math.cos(math.pi / 2 * k / n)), he + rise * math.sin(math.pi / 2 * k / n)) for k in range(n + 1)]
    pts[0], pts[-1] = (0.0, he), (h, he + rise)   # exactly on the eave and the crown
    return pts


def form_vault(v, data):
    """T-3179: a free-standing span whose roof is a vault of planar glass facets on
    `vault_section`, both halves alike, the end walls closing the section. The section is
    convex, so the glass stays one envelope."""
    L, W, he, rise = v["length_m"], v["width_m"], v["eave_m"], v["rise_m"]
    cp = vault_section(v, data)
    door = v.get("door") or {}
    b = v["bays"]
    P = [
        Panel("front", [(0, 0, W), (L, 0, W), (L, he, W), (0, he, W)], (0, 0, 1), plinth=True, bays=b),
        Panel("back", [(L, 0, 0), (0, 0, 0), (0, he, 0), (L, he, 0)], (0, 0, -1), plinth=True, bays=b),
    ]
    for k in range(len(cp) - 1):
        (z0, y0), (z1, y1) = cp[k], cp[k + 1]
        P.append(Panel(f"facet_back_{k}", [(L, y0, z0), (0, y0, z0), (0, y1, z1), (L, y1, z1)],
                       (0, z1 - z0, -(y1 - y0)), bays=b))
        P.append(Panel(f"facet_front_{k}", [(0, y0, W - z0), (L, y0, W - z0), (L, y1, W - z1), (0, y1, W - z1)],
                       (0, z1 - z0, y1 - y0), bays=b))
    for x, nx, name in ((0.0, -1.0, "end_left"), (L, 1.0, "end_right")):
        pts = [(x, 0, 0), (x, 0, W)] + [(x, y, W - z) for z, y in cp] + [(x, y, z) for z, y in reversed(cp[:-1])]
        P.append(Panel(name, pts, (nx, 0, 0), plinth=True, door=door if door.get("wall") == name else None))
    return {
        "panels": P, "host": False, "closed": True,
        "plan": [(0, 0), (L, 0), (L, W), (0, W)],
        "eaves": {"front": [(0, he, W), (L, he, W)], "back": [(0, he, 0), (L, he, 0)]},
        # staging only along the walls `planting` names
        "ridges": [], "benches": [b for b in (("front", (0, W), (L, W)), ("back", (L, 0), (0, 0)))
                                  if "bench_" + b[0] in v.get("planting", ("bench_front", "bench_back"))],
        "border": None, "eave_m": he, "top_m": he + rise, "centre": (L / 2, (he + rise) / 2, W / 2), "section": cp,
    }


FORMS = {"lean_to": form_lean_to, "span": form_span, "span_lantern": form_span_lantern,
         "curvilinear_lean_to": form_curvilinear_lean_to, "canted_bay": form_canted_bay,
         "segmental_bay": form_segmental_bay, "span_apse": form_span_apse, "vault": form_vault}

#: The forms that stand against a house wall and need a `host_wall` on their record. A
#: free-standing house (a span, with or without its lantern or apse, or a vault) needs none (T-3164).
HOST_FORMS = frozenset({"lean_to", "curvilinear_lean_to", "canted_bay", "segmental_bay"})


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
        # T-3164: an end wall another glasshouse closes (`abuts`, the free-standing forms' end
        # walls by name) is left out, so a line of sight never meets a second glass envelope
        # inside the first; the plinth still runs under it, as the two houses' shared footing
        abuts = set(v.get("abuts") or ())
        if abuts:
            f["panels"] = [p for p in f["panels"] if p.name not in abuts and p.name.removesuffix("_lantern") not in abuts]
        # T-3179: walls of masonry (`masonry` names them) carry the glass; their glass is not built
        masonry = set((v.get("masonry") or {}).get("sides") or ())
        if masonry:
            f["panels"] = [p for p in f["panels"] if p.name not in masonry]
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
            # T-1905: a plinth of the house's stone, where the glass stands on a stone base
            pr = "plinth_stone" if self.v.get("plinth_fabric") == "stone" else "plinth"
            self._sweep([pr, "coping", "coping", "coping", "coping", "coping", pr], pts,
                        [(f, Y) for f in frames], seg_o, prof, edges)
            for end, sgn in ((0, -1.0), (len(pts) - 1, 1.0)):
                if closed_loop:
                    break
                if self.form["host"] and abs(pts[end][2]) < 1e-9:
                    continue
                t = _unit(_sub(pts[1], pts[0])) if end == 0 else _unit(_sub(pts[-1], pts[-2]))
                fr = frames[end]
                for poly, role in zip(caps, (pr, "coping")):
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


def _prism(h: House, role, plan, y0, y1, top=True, bottom=False):
    """An upright prism on the convex plan polygon `plan` [(x, z)], from y0 to y1."""
    cx = cz = 0.0
    for x, z in plan:                      # left to right, so the bytes do not hang on the Python version
        cx, cz = cx + x, cz + z
    c = (cx / len(plan), cz / len(plan))
    for i, a in enumerate(plan):
        b = plan[(i + 1) % len(plan)]
        out = ((a[0] + b[0]) / 2 - c[0], 0.0, (a[1] + b[1]) / 2 - c[1])
        h.face(role, [(a[0], y0, a[1]), (b[0], y0, b[1]), (b[0], y1, b[1]), (a[0], y1, a[1])], out)
    if top:
        h.face(role, [(x, y1, z) for x, z in plan], Y)
    if bottom:
        h.face(role, [(x, y0, z) for x, z in plan], (0, -1, 0))


def _arc(r, n, a0=0.0, a1=math.pi):
    return [(r * math.cos(a0 + (a1 - a0) * k / n), r * math.sin(a0 + (a1 - a0) * k / n)) for k in range(n + 1)]


def _ring(h: House, role, r_out, r_in, n, y0, y1, a0=0.0, a1=math.pi, bottom=False):
    """A band between two arcs (a balustrade, an entablature's face): one quad prism a segment,
    its underside drawn when `bottom` (a rail seen from below, T-1934)."""
    o, i_ = _arc(r_out, n, a0, a1), _arc(r_in, n, a0, a1)
    for k in range(n):
        (ax, az), (bx, bz), (cx, cz), (dx, dz) = o[k], o[k + 1], i_[k + 1], i_[k]
        mx, mz = (ax + bx) / 2, (az + bz) / 2
        h.face(role, [(ax, y0, az), (bx, y0, bz), (bx, y1, bz), (ax, y1, az)], (mx, 0.0, mz))
        h.face(role, [(dx, y0, dz), (cx, y0, cz), (cx, y1, cz), (dx, y1, dz)], (-mx, 0.0, -mz))
        h.face(role, [(ax, y1, az), (bx, y1, bz), (cx, y1, cz), (dx, y1, dz)], Y)
        if bottom:
            h.face(role, [(ax, y0, az), (bx, y0, bz), (cx, y0, cz), (dx, y0, dz)], (0, -1, 0))
    for (ax, az), (dx, dz) in ((o[0], i_[0]), (o[-1], i_[-1])):   # the two ends only
        t = (-az, 0.0, ax) if (ax, az) == o[0] else (az, 0.0, -ax)
        h.face(role, [(ax, y0, az), (dx, y0, dz), (dx, y1, dz), (ax, y1, az)], (-t[0], 0.0, -t[2]))


def _lathe(h: House, role, cx, cz, prof, sides=8, cap=True):
    """T-1934: a turned piece (an urn, a column's base or capital ring) of `sides` facets on the
    profile `prof` [(radius, y)] read bottom to top, about the upright through (cx, cz); a
    zero radius closes it to a point, and its last ring is capped when `cap`."""
    ring = [(math.cos(math.tau * (k + 0.5) / sides), math.sin(math.tau * (k + 0.5) / sides)) for k in range(sides)]
    for (r0, y0), (r1, y1) in zip(prof, prof[1:]):
        for k in range(sides):
            (c0, s0), (c1, s1) = ring[k], ring[(k + 1) % sides]
            q = [(cx + r0 * c0, y0, cz + r0 * s0), (cx + r0 * c1, y0, cz + r0 * s1)]
            q += [(cx + r1 * c1, y1, cz + r1 * s1)] + ([] if r1 < 1e-9 else [(cx + r1 * c0, y1, cz + r1 * s0)])
            if r0 < 1e-9:
                q = q[1:]
            cm, sm = (c0 + c1) / 2, (s0 + s1) / 2
            h.face(role, q, (cm, (r0 - r1) / max(1e-9, abs(y1 - y0) + abs(r0 - r1)), sm))
    r, y = prof[-1]
    if cap and r > 1e-9:
        h.face(role, [(cx + r * c, y, cz + r * s_) for c, s_ in ring], Y)


def _urn(h: House, cx, cz, y0, u: dict):
    """T-1934: a garden urn on a pier, as the Inland plate and Taylor's view show them on the
    Pullman terrace: a foot, a bowl swelling to `radius_m` and a lid, `height_m` tall."""
    r, ht = u["radius_m"], u["height_m"]
    prof = [(0.45 * r, 0.0), (0.45 * r, 0.12), (0.3 * r, 0.2), (0.85 * r, 0.32), (r, 0.5), (0.9 * r, 0.68),
            (0.6 * r, 0.76), (0.7 * r, 0.82), (0.35 * r, 0.92), (0.0, 1.0)]
    _lathe(h, "stonework", cx, cz, [(a, y0 + b * ht) for a, b in prof], u.get("sides", 8))


def _balustrade(h: House, a, b, y0, height, spec: dict, dies=()):
    """T-1934: an open balustrade on the straight run a -> b (plan points (x, z)): a plinth and a
    rail `thickness_m` thick, and between them balusters at `pitch_m`, each a swelling belly
    under a neck, square in plan; a solid die `die_m` wide at each fraction along the run named
    in `dies` (0 and 1 are its ends), where no baluster stands."""
    (ax, az), (bx, bz) = a, b
    L = math.hypot(bx - ax, bz - az)
    if L < 0.05:
        return
    tx, tz = (bx - ax) / L, (bz - az) / L
    nx, nz = -tz, tx
    th = spec["thickness_m"]

    def quad(s0, s1, half):
        return [(ax + tx * s + nx * w, az + tz * s + nz * w) for s, w in ((s0, -half), (s1, -half), (s1, half), (s0, half))]

    pl, rl = spec["plinth_m"], spec["rail_m"]
    _prism(h, "stonework", quad(0.0, L, th / 2), y0, y0 + pl)
    _prism(h, "stonework", quad(0.0, L, th / 2 + 0.03), y0 + height - rl, y0 + height, bottom=True)
    dw = spec.get("die_m", 0.0)
    spans, cur = [], 0.0
    for f in sorted(dies):
        c = min(max(f * L, dw / 2), L - dw / 2)
        if c - dw / 2 < cur - 1e-6:       # one die where two would overlap
            continue
        _prism(h, "stonework", quad(c - dw / 2, c + dw / 2, th / 2 + 0.02), y0 + pl, y0 + height - rl, top=False)
        spans.append((cur, c - dw / 2))
        cur = c + dw / 2
    spans.append((cur, L))
    pitch, rb = spec["pitch_m"], spec["radius_m"]
    yb, yn, yt = y0 + pl, y0 + pl + 0.45 * (height - pl - rl), y0 + height - rl
    for s0, s1 in spans:
        n = int((s1 - s0) / pitch)
        if n < 1:
            continue
        gap = (s1 - s0 - n * pitch) / 2
        for i in range(n):
            s = s0 + gap + pitch * (i + 0.5)
            cx, cz = ax + tx * s, az + tz * s
            for r, y_a, y_b in ((rb, yb, yn), (0.6 * rb, yn, yt)):
                _prism(h, "stonework", [(cx + tx * r * p + nx * r * q, cz + tz * r * p + nz * r * q)
                                        for p, q in ((-1, -1), (1, -1), (1, 1), (-1, 1))], y_a, y_b, top=False)


def _balustrade_ring(h: House, rc, n, y0, height, spec: dict):
    """T-1934: the open balustrade round the palm house's drum: a plinth and a rail on the half
    ring of radius `rc` in `n` segments, and balusters at `pitch_m` round it."""
    th, pl, rl = spec["thickness_m"], spec["plinth_m"], spec["rail_m"]
    _ring(h, "stonework", rc + th / 2, rc - th / 2, n, y0, y0 + pl)
    _ring(h, "stonework", rc + th / 2 + 0.03, rc - th / 2 - 0.03, n, y0 + height - rl, y0 + height, bottom=True)
    L = math.pi * rc
    k = int(L / spec["pitch_m"])
    rb = spec["radius_m"]
    yb, yn, yt = y0 + pl, y0 + pl + 0.45 * (height - pl - rl), y0 + height - rl
    for i in range(k):
        t = math.pi * (i + 0.5) / k
        cx, cz, ux, uz = rc * math.cos(t), rc * math.sin(t), -math.sin(t), math.cos(t)
        for r, y_a, y_b in ((rb, yb, yn), (0.6 * rb, yn, yt)):
            _prism(h, "stonework", [(cx + ux * r * p + math.cos(t) * r * q, cz + uz * r * p + math.sin(t) * r * q)
                                    for p, q in ((-1, -1), (1, -1), (1, 1), (-1, 1))], y_a, y_b, top=False)


def _wall_dress(h: House, host: dict, x0: float, x1: float):
    """T-1934: the wing's south face as the Inland plate and Taylor's 16555 show it: banded
    rustication (courses standing a few centimetres proud of the wall, so each joint reads as a
    line of the wall's own darker tone), broad pilasters with caps, and a moulded cornice under
    the parapet. Courses stop at the palm house, at each opening and behind each pilaster. All of it
    is the wall's own stone (`host_stone`): in the winter print the face prints as dark as the
    wall, and only the drum's columns print lighter."""
    H = host["height_m"]
    ru, pi_, co = host.get("rustication"), host.get("pilasters"), host.get("cornice")
    if ru:
        R = h.v["radius_m"] + ru["clear_of_drum_m"]
        cut = [(-R, R, 0.0, H)]
        for o in host.get("openings", []):
            cut.append((o["centre_m"] - o["width_m"] / 2 - 0.15, o["centre_m"] + o["width_m"] / 2 + 0.15,
                        o["sill_m"] - 0.1, o["sill_m"] + o["height_m"] + 0.25))
        for c in (pi_ or {}).get("at_m", []):
            cut.append((c - pi_["width_m"] / 2 + 0.02, c + pi_["width_m"] / 2 - 0.02, 0.0, H))
        y, top, d = ru["from_m"], H - (co["height_m"] if co else 0.0), ru["out_m"]
        while y + ru["course_m"] <= top + 1e-6:
            ya, yb = y + ru["joint_m"] / 2, y + ru["course_m"] - ru["joint_m"] / 2
            runs, cur = [], x0
            for a, b, c0, c1 in sorted(cut):
                if c1 > ya and c0 < yb and b > cur:
                    if a > cur:
                        runs.append((cur, a))
                    cur = max(cur, b)
            if cur < x1:
                runs.append((cur, x1))
            for a, b in runs:
                if b - a > 0.1:
                    h.face("host_stone", [(a, ya, d), (b, ya, d), (b, yb, d), (a, yb, d)], (0, 0, 1))
                    h.face("host_stone", [(a, yb, 0.0), (b, yb, 0.0), (b, yb, d), (a, yb, d)], Y)
                    h.face("host_stone", [(a, ya, d), (b, ya, d), (b, ya, 0.0), (a, ya, 0.0)], (0, -1, 0))
            y += ru["course_m"]
    if pi_:
        w, out, y0 = pi_["width_m"], pi_["out_m"], pi_.get("from_m", 0.0)
        y1 = H - (co["height_m"] if co else 0.0)
        for c in pi_["at_m"]:
            _prism(h, "host_stone", [(c - w / 2, -0.02), (c + w / 2, -0.02), (c + w / 2, out), (c - w / 2, out)],
                   y0, y1 - pi_["cap_m"], top=False)
            _prism(h, "host_stone", [(c - w / 2 - 0.06, -0.02), (c + w / 2 + 0.06, -0.02), (c + w / 2 + 0.06, out + 0.06),
                                    (c - w / 2 - 0.06, out + 0.06)], y1 - pi_["cap_m"], y1, top=False, bottom=True)
    if co:    # stopped either side of the drum, whose own cornice carries it round
        g = co["clear_of_drum_m"]
        for a, b in ((x0, -g), (g, x1)):
            _prism(h, "host_stone", [(a, -0.025), (b, -0.025), (b, co["out_m"]), (a, co["out_m"])],
                   H - co["height_m"], H + 0.02, bottom=True)


def palm_house(h: House, sw: dict):
    """T-3165: the dress Beman gave the Pullman palm house (1892), as the 1894 Inland Architect
    plate and J. W. Taylor's photographs show it, round the K13 bay's glass drum: a stone
    podium, a column at every facet joint, an entablature and a balustrade round the drum's
    flat top, and a ribbed dome on a short collar over the drum's centre. The glass stays the
    kit's (one convex single-sided envelope); the dome, which stands up off the drum, takes the
    opaque glass substitute, as the kit's lantern does, so no line of sight crosses two glass
    envelopes."""
    v = h.v
    R, n, he = v["radius_m"], v["facets"], v["eave_m"]
    base, col, ent = sw["podium_m"], sw["column_radius_m"], sw["entablature"]
    ro = R + sw["podium_out_m"]
    into = [(ro, -0.02), (-ro, -0.02)]    # every piece runs 2 cm into the wing, never face to face with it
    _prism(h, "stonework", [(x, z) for x, z in reversed(_arc(ro, n))] + into, 0.0, base)
    # a column at every facet joint, the two at the wall standing half in it
    rc = R + col
    e0, e1, eo = he - 0.15, he + ent["height_m"], R + ent["out_m"]   # its soffit hides the eave plate
    cs = sw.get("column")
    for x, z in _arc(rc, n):
        if cs:    # T-1934: a round shaft on a square plinth and a torus, under a capital and an abacus
            pb, tb, cp, ab = cs["plinth_m"], cs["torus_m"], cs["capital_m"], cs["abacus_m"]
            sq = [(x - 1.25 * col, z - 1.25 * col), (x + 1.25 * col, z - 1.25 * col),
                  (x + 1.25 * col, z + 1.25 * col), (x - 1.25 * col, z + 1.25 * col)]
            _prism(h, "stonework", sq, base, base + pb)
            _lathe(h, "stonework", x, z, [(1.15 * col, base + pb), (1.15 * col, base + pb + tb),
                                          (col, base + pb + tb), (0.88 * col, e0 - cp - ab),
                                          (1.1 * col, e0 - ab)], cs["sides"], cap=False)
            _prism(h, "stonework", [(a + (a - x) * 0.08, c + (c - z) * 0.08) for a, c in sq], e0 - ab, e0, top=False,
                   bottom=True)
        else:
            _prism(h, "stonework", [(x + col * math.cos(math.tau * k / 8), z + col * math.sin(math.tau * k / 8))
                                    for k in range(8)], base, he - 0.15, top=False)
    m_arc = n * sw.get("arc_per_facet", 1)
    if ent.get("cornice_m"):    # T-1934: architrave and frieze under a cornice standing further out
        eb = e1 - ent["cornice_m"]
        _prism(h, "stonework", [(x, z) for x, z in reversed(_arc(eo, m_arc))] + [(eo, -0.02), (-eo, -0.02)], e0, eb,
               top=False, bottom=True)
        ec = R + ent["cornice_out_m"]
        _prism(h, "stonework", [(x, z) for x, z in reversed(_arc(ec, m_arc))] + [(ec, -0.02), (-ec, -0.02)], eb, e1,
               bottom=True)
    else:
        _prism(h, "stonework", [(x, z) for x, z in reversed(_arc(eo, n))] + [(eo, -0.02), (-eo, -0.02)], e0, e1,
               bottom=True)
    b = sw["balustrade"]
    if b.get("pitch_m"):
        _balustrade_ring(h, eo - 0.05 - b["thickness_m"] / 2, m_arc, e1, b["height_m"], b)
    else:
        _ring(h, "stonework", eo - 0.05, eo - 0.05 - b["thickness_m"], n, e1, e1 + b["height_m"])
    gb = sw.get("glazing_bars")
    if gb:
        # T-1934 (the owner, 2026-10-30: "a fair amount of detail work to do on the glass atrium"):
        # the drum's lights crossed by horizontal bars, a transom among them, as 16554 and the 1894
        # plate show each bay between the columns divided into a grid of panes; a strip a little
        # proud of each facet's glass, stopped short of the columns
        bw, out, step = gb["bar_m"], gb.get("out_m", 0.03), gb["every_m"]
        ys, y = [], base + step
        while y < he - 0.25:
            ys.append(y)
            y += step
        tr = gb.get("transom_m")
        pts = _arc(R, n)
        for k in range(n):
            (ax, az), (bx, bz) = pts[k], pts[k + 1]
            mx, mz = (ax + bx) / 2, (az + bz) / 2
            L = math.hypot(mx, mz) or 1.0
            nx, nz = mx / L * out, mz / L * out
            cut = col * 1.1 / (math.hypot(bx - ax, bz - az) or 1.0)
            a0 = (ax + (bx - ax) * cut + nx, az + (bz - az) * cut + nz)
            b0 = (bx - (bx - ax) * cut + nx, bz - (bz - az) * cut + nz)
            for yy in ys + ([tr] if tr else []):
                hw = (gb.get("transom_bar_m", bw * 2) if yy == tr else bw) / 2
                h.face(gb.get("role", "dome_rib"), [(a0[0], yy - hw, a0[1]), (b0[0], yy - hw, b0[1]),
                                                   (b0[0], yy + hw, b0[1]), (a0[0], yy + hw, a0[1])], (mx, 0.0, mz))
    if sw.get("color"):
        # T-1934: the palm house's stone is the house's own (every picture prints its columns,
        # entablature, balustrade and terrace in the walls' tone; the kit's pale stone read white)
        h.meta["stone_color"] = list(sw["color"])
    if sw.get("interior_dark"):
        # T-1934: the palm house's depth behind its glass, drawn dark a centimetre off the wing's
        # face, so the drum reads as the pictures show it (glazing in shadow, palms against it)
        # and not as the wing's pale stone seen through the panes
        h.face("opening", [(-R + 0.01, base, 0.01), (R - 0.01, base, 0.01), (R - 0.01, he, 0.01),
                           (-R + 0.01, he, 0.01)], (0, 0, 1))
    d = sw["dome"]
    rd, m = d["radius_m"], d["segments"]
    dome_role, rib_every = d.get("role", "dome"), d.get("rib_every", 2)
    collar = [(rd * math.cos(math.tau * k / m), rd * math.sin(math.tau * k / m)) for k in range(m)]
    _prism(h, "stonework", collar, e1, d["spring_m"], top=False)
    rings = d["rings"]
    prof = [(rd * math.cos(math.pi / 2 * j / rings), d["spring_m"] + d["rise_m"] * math.sin(math.pi / 2 * j / rings))
            for j in range(rings + 1)]
    for j in range(rings):
        (r0, y0), (r1, y1) = prof[j], prof[j + 1]
        for k in range(m):
            t0, t1 = math.tau * k / m, math.tau * (k + 1) / m
            q = [(r0 * math.cos(t0), y0, r0 * math.sin(t0)), (r0 * math.cos(t1), y0, r0 * math.sin(t1))]
            q += [(r1 * math.cos(t1), y1, r1 * math.sin(t1))] + ([] if r1 < 1e-9 else [(r1 * math.cos(t0), y1, r1 * math.sin(t0))])
            tm = (t0 + t1) / 2
            h.face(dome_role, q, (math.cos(tm), 0.4 + j / rings, math.sin(tm)))
    # a rib on every other meridian (every `rib_every`-th): a strip standing 4 cm proud of the dome
    w = d.get("rib_m", 0.1)
    for k in range(0, m, rib_every):
        t = math.tau * k / m
        c, s_, ux, uz = math.cos(t), math.sin(t), -math.sin(t), math.cos(t)
        for j in range(rings):
            (r0, y0), (r1, y1) = prof[j], prof[j + 1]
            o0, o1 = r0 + 0.04, r1 + 0.04
            h.face("dome_rib", [(o0 * c - ux * w / 2, y0, o0 * s_ - uz * w / 2), (o0 * c + ux * w / 2, y0, o0 * s_ + uz * w / 2),
                                (o1 * c + ux * w / 2, y1, o1 * s_ + uz * w / 2), (o1 * c - ux * w / 2, y1, o1 * s_ - uz * w / 2)],
                   (c, 0.5, s_))
    if d.get("finial_m"):
        _prism(h, "dome_rib", [(0.08 * math.cos(math.tau * k / 6), 0.08 * math.sin(math.tau * k / 6)) for k in range(6)],
               d["spring_m"] + d["rise_m"] - 0.05, d["spring_m"] + d["rise_m"] + d["finial_m"])
    h.meta["palm_house"] = {"top_m": round(d["spring_m"] + d["rise_m"] + d.get("finial_m", 0.0), 3)}


def host_dress(h: House, host: dict):
    """T-3165: what the Inland plate and Taylor's view show of the wing round the palm house:
    a balustraded parapet over its south face, the raised terrace before it with a flight of
    steps to the drum, the terrace's own balustrade, and its arched openings (drawn dark,
    a reveal's depth proud of the wall)."""
    # the dress stops 2 cm inside the block's ends, so no face of it lies on an end wall
    x0, x1, H = -host["west_m"] + 0.02, host["east_m"] - 0.02, host["height_m"]
    p = host.get("parapet")
    if p and p.get("pitch_m"):
        # T-1934: an open balustrade either side of the drum's own, a die over each pilaster
        t, gap = p["thickness_m"], p["clear_of_drum_m"]
        pil = [c for c in (host.get("pilasters") or {}).get("at_m", [])]
        for a, b in ((x0, -gap), (gap, x1)):
            dies = [0.0, 1.0] + [(c - a) / (b - a) for c in pil if a < c < b]
            _balustrade(h, (a, -0.06 - t / 2), (b, -0.06 - t / 2), H, p["height_m"], p, dies)
        h.meta["plan_extra_m2"] = h.meta.get("plan_extra_m2", 0.0) + (x1 - x0) * host["depth_m"]
    elif p:
        t = p["thickness_m"]
        # 3 cm back from the wall's face, so the drum's balustrade can run into it
        _prism(h, "stonework", [(x0, -0.03), (x1, -0.03), (x1, -t), (x0, -t)], H, H + p["height_m"])
    _wall_dress(h, host, x0, x1)
    tr = host.get("terrace")
    if tr:
        D, T, sw = tr["depth_m"], tr["height_m"], tr["steps"]
        x0 = -tr["west_m"] + 0.02 if tr.get("west_m") else x0   # it stops at the house's own wall
        sx0, sx1 = sw["centre_m"] - sw["width_m"] / 2, sw["centre_m"] + sw["width_m"] / 2
        _prism(h, "stonework", [(x0, D), (x1, D), (x1, -0.04), (x0, -0.04)], 0.0, T)
        k = max(1, round(T / sw["riser_m"]))
        for i in range(1, k):             # the terrace itself is the top tread
            y1 = T * (k - i) / k
            z0 = D + sw["tread_m"] * i
            _prism(h, "stonework", [(sx0, z0), (sx1, z0), (sx1, D - 0.02), (sx0, D - 0.02)], y1 - T / k, y1)
        b = tr["balustrade"]
        for a, c in ((x0, sx0), (sx1, x1)):
            if c - a > 0.1 and b.get("pitch_m"):
                # T-1934: an open balustrade between square piers, an urn on each pier
                pw, t = b["pier_m"], b["thickness_m"]
                # its ends run 2 cm into the piers, so no end face lies on a pier's
                _balustrade(h, (a + pw - 0.02, D - pw / 2), (c - pw + 0.02, D - pw / 2), T, b["height_m"], b)
                for px in (a + pw / 2, c - pw / 2):
                    _prism(h, "stonework", [(px - pw / 2, D - pw), (px + pw / 2, D - pw), (px + pw / 2, D),
                                            (px - pw / 2, D)], T, T + b["height_m"] + b["pier_over_m"])
                    if b.get("urn"):
                        _urn(h, px, D - pw / 2, T + b["height_m"] + b["pier_over_m"], b["urn"])
            elif c - a > 0.1:
                _prism(h, "stonework", [(a, D), (c, D), (c, D - b["thickness_m"]), (a, D - b["thickness_m"])],
                       T, T + b["height_m"])
        if b.get("pitch_m"):
            h.meta["plan_extra_m2"] = h.meta.get("plan_extra_m2", 0.0) + (x1 - x0) * D
    for o in host.get("openings", []):
        cx, w, y0, hh = o["centre_m"], o["width_m"], o["sill_m"], o["height_m"]
        r = w / 2
        pts = [(cx - r, y0, 0.03), (cx + r, y0, 0.03)]
        pts += [(cx + r * math.cos(math.pi * k / 8), y0 + hh - r + r * math.sin(math.pi * k / 8), 0.03) for k in range(9)]
        h.face("opening", pts, (0, 0, 1))


def _dome(h: House, d: dict, cx: float, cz: float, y0: float, role: str = "dome"):
    """T-3179: a ribbed dome of `rings` x `segments` facets in the opaque glass substitute on a
    circle of `radius_m` centred at (cx, cz), springing at y0 and rising `rise_m`, a rib on every
    other meridian and an optional finial: the palm house's dome, stood anywhere."""
    rd, m, rings = d["radius_m"], d["segments"], d["rings"]
    prof = [(rd * math.cos(math.pi / 2 * j / rings), y0 + d["rise_m"] * math.sin(math.pi / 2 * j / rings))
            for j in range(rings + 1)]
    for j in range(rings):
        (r0, ya), (r1, yb) = prof[j], prof[j + 1]
        for k in range(m):
            t0, t1 = math.tau * k / m, math.tau * (k + 1) / m
            q = [(cx + r0 * math.cos(t0), ya, cz + r0 * math.sin(t0)), (cx + r0 * math.cos(t1), ya, cz + r0 * math.sin(t1))]
            q += [(cx + r1 * math.cos(t1), yb, cz + r1 * math.sin(t1))]
            q += [] if j == rings - 1 else [(cx + r1 * math.cos(t0), yb, cz + r1 * math.sin(t0))]
            tm = (t0 + t1) / 2
            h.face(role, q, (math.cos(tm), 0.4 + j / rings, math.sin(tm)))
    w = d.get("rib_m", 0.1)
    for k in range(0, m, 2):
        t = math.tau * k / m
        c, s_, ux, uz = math.cos(t), math.sin(t), -math.sin(t), math.cos(t)
        for j in range(rings):
            (r0, ya), (r1, yb) = prof[j], prof[j + 1]
            o0, o1 = r0 + 0.04, r1 + 0.04
            h.face("dome_rib", [(cx + o0 * c - ux * w / 2, ya, cz + o0 * s_ - uz * w / 2),
                                (cx + o0 * c + ux * w / 2, ya, cz + o0 * s_ + uz * w / 2),
                                (cx + o1 * c + ux * w / 2, yb, cz + o1 * s_ + uz * w / 2),
                                (cx + o1 * c - ux * w / 2, yb, cz + o1 * s_ - uz * w / 2)], (c, 0.5, s_))
    top = y0 + d["rise_m"]
    if d.get("finial_profile"):
        _turned(h, "dome_rib", cx, cz, top, d["finial_profile"])
        return top + d["finial_profile"][-1][1]
    if d.get("finial_m"):
        _prism(h, "dome_rib", [(cx + 0.08 * math.cos(math.tau * k / 6), cz + 0.08 * math.sin(math.tau * k / 6))
                               for k in range(6)], top - 0.05, top + d["finial_m"])
    return top + d.get("finial_m", 0.0)


def _turned(h: House, role, cx: float, cz: float, y0: float, profile, sides: int = 8):
    """T-3164: a turned ornament on (cx, y0, cz): the profile's [radius, height over y0] pairs,
    foot to tip, lathed in `sides` flat faces and capped at the tip, as the Pullman dome's
    finial stands in its pictures (a flared foot, a bulb, a neck, a knob and a spike)."""
    ring = lambda r, y: [(cx + r * math.cos(math.tau * (k + 0.5) / sides), y, cz + r * math.sin(math.tau * (k + 0.5) / sides))
                         for k in range(sides)]
    rings = [ring(r, y0 + dy) for r, dy in profile]
    for (ra, dya), (rb, dyb), a, b in zip(profile, profile[1:], rings, rings[1:]):
        for k in range(sides):
            t = math.tau * (k + 1) / sides
            q = [a[k], a[(k + 1) % sides], b[(k + 1) % sides], b[k]]
            h.face(role, q, (math.cos(t) * (dyb - dya), ra - rb, math.sin(t) * (dyb - dya)))
    h.face(role, rings[-1], Y)


def masonry_walls(h: House, ms: dict):
    """T-3179: the masonry the Inland plate shows round the Pullman glasshouse range across 18th
    Street, where the 1911 sheet letters only a glass roof: a wall `thickness_m` thick outside
    each side `masonry` names (front or back, the span's long walls), from grade to `height_m`
    (the eave and a parapet over it), under a coping; pilasters between a row of windows, drawn
    dark a centimetre proud; and an optional open porch of columns under a flat entablature."""
    v = h.v
    L, W, t = v["length_m"], v["width_m"], ms.get("thickness_m", 0.0)
    for side in ms["sides"]:
        H, cp, wn, pil = ms["height_m"], ms["coping"], ms.get("windows"), ms["pilaster"]
        z0, z1, sz = (W, W + t, 1.0) if side == "front" else (-t, 0.0, -1.0)
        zf = z1 if sz > 0 else z0                       # the wall's outer face
        _prism(h, "stonework", [(0.0, z0), (L, z0), (L, z1), (0.0, z1)], 0.0, H, top=False)
        zo = zf + sz * cp["out_m"]
        _prism(h, "stonework", [(0.0, min(zf - sz * t, zo)), (L, min(zf - sz * t, zo)),
                                (L, max(zf - sz * t, zo)), (0.0, max(zf - sz * t, zo))], H, H + cp["thickness_m"],
               bottom=True)
        if not wn:                                      # a plain wall, its coping only
            continue
        m0 = wn["margin_m"]                             # T-3164: the far end's margin may differ
        m1 = wn.get("margin_end_m", m0)
        n = max(1, int((L - m0 - m1) / wn["spacing_m"] + 1e-9))
        step = (L - m0 - m1) / n
        for i in range(n + 1):                          # a pilaster at each bay line
            x = m0 + step * i
            za, zb = sorted((zf - sz * 0.02, zf + sz * pil["out_m"]))
            _prism(h, "stonework", [(x - pil["width_m"] / 2, za), (x + pil["width_m"] / 2, za),
                                    (x + pil["width_m"] / 2, zb), (x - pil["width_m"] / 2, zb)], 0.0, H - 0.02)
        for c in ms.get("courses", ()):                 # T-3164: string courses the length of the wall
            za, zb = sorted((zf - sz * 0.03, zf + sz * c["out_m"]))     # its back clear of the pilasters'
            _prism(h, "stonework", [(-c["out_m"], za), (L + c["out_m"], za), (L + c["out_m"], zb),
                                    (-c["out_m"], zb)], c["from_m"], c["to_m"])
        lt, pn = wn.get("lights"), wn.get("panel")
        for i in range(n):                              # a window in each bay
            x = m0 + step * (i + 0.5)
            a, b = x - wn["width_m"] / 2, x + wn["width_m"] / 2
            y0, y1 = wn["sill_m"], wn["head_m"]
            zw = zf + sz * 0.01
            if not lt:
                h.face("opening", [(a, y0, zw), (b, y0, zw), (b, y1, zw), (a, y1, zw)], (0.0, 0.0, sz))
            else:
                # T-3164: the Inland plate reads these panes pale against dark sash bars, so the
                # window is the pale substitute glass under its frame and muntins
                h.face("sky_glass", [(a, y0, zw), (b, y0, zw), (b, y1, zw), (a, y1, zw)], (0.0, 0.0, sz))
                bw, zb_ = lt["bar_m"], zw + sz * 0.01
                bars = [(a + (b - a) * k / lt["across"], None) for k in range(lt["across"] + 1)]
                bars += [(None, y0 + (y1 - y0) * k / lt["up"]) for k in range(lt["up"] + 1)]
                for bx, by in bars:
                    if by is None:                      # the uprights a few mm prouder than the rails
                        u0, u1, zu = max(a, bx - bw / 2), min(b, bx + bw / 2), zb_ + sz * 0.005
                        q = [(u0, y0, zu), (u1, y0, zu), (u1, y1, zu), (u0, y1, zu)]
                    else:
                        v0, v1 = max(y0, by - bw / 2), min(y1, by + bw / 2)
                        q = [(a, v0, zb_), (b, v0, zb_), (b, v1, zb_), (a, v1, zb_)]
                    h.face("sash", q, (0.0, 0.0, sz))
            if pn:                                      # T-3164: the sunk panel under the sill
                pa, pb = x - pn["width_m"] / 2, x + pn["width_m"] / 2
                p0, p1, m = pn["from_m"], pn["to_m"], pn["moulding_m"]
                za, zb = sorted((zf - sz * 0.025, zf + sz * pn["out_m"]))
                for r in ((pa, pb, p0, p0 + m), (pa, pb, p1 - m, p1), (pa, pa + m, p0 + m, p1 - m),
                          (pb - m, pb, p0 + m, p1 - m)):
                    _prism(h, "stonework", [(r[0], za), (r[1], za), (r[1], zb), (r[0], zb)], r[2], r[3])
    po = ms.get("porch")
    if po:
        x0, x1, D, ph = po["from_m"], po["to_m"], po["depth_m"], po["height_m"]
        zf, sz = (W + t, 1.0) if po["side"] == "front" else (-t, -1.0)
        zd = zf + sz * D
        rc = po["column_radius_m"]
        for i in range(po["columns"]):
            x = x0 + rc + (x1 - x0 - 2 * rc) * i / max(1, po["columns"] - 1)
            zc = zd - sz * rc
            _prism(h, "stonework", [(x + rc * math.cos(math.tau * k / 8), zc + rc * math.sin(math.tau * k / 8))
                                    for k in range(8)], 0.0, ph, top=False)
        za, zb = sorted((zf - sz * 0.02, zd + sz * 0.1))
        _prism(h, "stonework", [(x0 - 0.1, za), (x1 + 0.1, za), (x1 + 0.1, zb), (x0 - 0.1, zb)], ph,
               ph + po["entablature_m"], bottom=True)
        # the door it shelters, dark on the wall
        xm, dw = (x0 + x1) / 2, po["door_width_m"]
        zw = zf + sz * 0.015                            # clear of the windows' plane
        h.face("opening", [(xm - dw / 2, 0.0, zw), (xm + dw / 2, 0.0, zw), (xm + dw / 2, ph - 0.3, zw),
                           (xm - dw / 2, ph - 0.3, zw)], (0.0, 0.0, sz))


def _lit_band(h: House, bd: dict, o, t, n, s0, s1, y0, y1):
    """T-3164: the band of upright glazing between the conservatory's podium and its eave, as
    the Lowe photograph and the Inland plate show it: white framing over the run from `s0` to
    `s1` (along `t` from `o`, `out_m` off the glass on the outward normal `n`), and in it lights
    about `light_m` wide between bars `bar_m` wide under rails `rail_m` deep, each light a
    round-headed pane in the planted shade behind the glass, drawn 5 mm proud of the framing.
    With `transom_below_m`, a transom bar stands that far under the head and the light is two
    panes, a tall one under the bar and a short round-headed one over it (the transept's).
    One face a pane and one the framing, so a band costs a few triangles a light."""
    if s1 - s0 < 0.3:
        return
    k = max(1, round((s1 - s0) / bd["light_m"]))
    w, out, rail = bd["bar_m"], bd["out_m"], bd["rail_m"]
    P = lambda s, y, d=0.0: (o[0] + t[0] * s + n[0] * (out + d), y, o[1] + t[1] * s + n[1] * (out + d))
    nn = (n[0], 0.0, n[1])
    h.face("dome_rib", [P(s0, y0), P(s1, y0), P(s1, y1), P(s0, y1)], nn)
    step = (s1 - s0 - w) / k
    r = (step - w) / 2
    lo, spring = y0 + rail, y1 - rail - r
    m = bd.get("head_segments", 4)
    tb = bd.get("transom_below_m")
    yt = y1 - tb if tb else None                    # T-3164: a transom bar's centre, under the heads
    for j in range(k):
        c = s0 + w / 2 + step * (j + 0.5)
        ya = lo if yt is None else yt + w / 2
        sp = max(spring, ya)
        arc = [P(c + r * math.cos(math.pi * q / m), sp + r * math.sin(math.pi * q / m), 0.005) for q in range(m + 1)]
        h.face("interior", [P(c - r, ya, 0.005), P(c + r, ya, 0.005)] + arc, nn)
        if yt is not None:                          # the tall light under the transom
            h.face("interior", [P(c - r, lo, 0.005), P(c + r, lo, 0.005), P(c + r, yt - w / 2, 0.005),
                                P(c - r, yt - w / 2, 0.005)], nn)


def rotunda(h: House, rs: dict):
    """T-3179: the round east end of the Pullman range as the Inland plate shows it: a column at
    every joint of the span_apse's half-ring and `straight_columns` more along each side of its
    straight part, on a stone podium, the glass between them, an entablature round the whole at
    the range's coping, and a low ribbed dome over the curve's centre. With the entablature's
    `from_m`, its underside (and so the columns' heads) stands there rather than just under the
    eave (T-3164: both pictures put it level with the range's course over the window heads)."""
    v = h.v
    L, W, n, he = v["length_m"], v["width_m"], v["facets"], v["eave_m"]
    R = W / 2
    ring = lambda r: [(L + r * math.sin(math.pi * k / n), R - r * math.cos(math.pi * k / n)) for k in range(n + 1)]
    ro = R + rs["podium_out_m"]
    _prism(h, "stonework", ring(ro) + [(0.02, R + ro), (0.02, R - ro)], 0.0, rs["podium_m"])
    col = rs["column_radius_m"]
    k_s = rs.get("straight_columns", 0)
    e = rs["entablature"]
    e0 = e.get("from_m", he - 0.15)
    feet = ring(R + col) + [(L * i / (k_s + 1), z) for i in range(1, k_s + 1) for z in (-col, W + col)]
    for x, z in feet:
        _prism(h, "stonework", [(x + col * math.cos(math.tau * k / 8), z + col * math.sin(math.tau * k / 8))
                                for k in range(8)], rs["podium_m"], e0, top=False)
    eo = R + e["out_m"]
    _prism(h, "stonework", ring(eo) + [(0.02, R + eo), (0.02, R - eo)], e0, he + e["height_m"], bottom=True)
    return _dome(h, rs["dome"], L, R, he + e["height_m"], "sky_glass")


def ribs(h: House, prof, xa, xb, ze, sgn, zin, hip, spacing):
    """T-3179: the transept's glazing bars, as the plate draws them: a rib following the section
    up each long slope at every `spacing` along the arm, from the hip to where the slope meets the
    nave, each a strip 6 cm wide standing 3 cm proud of the substitute glazing."""
    w, out = 0.06, 0.03
    z_lo, z_hi = sorted((hip(0.0), zin(prof[-1][1])))
    n = max(1, int(abs(z_hi - z_lo) / spacing))
    for i in range(1, n):
        z = z_lo + (z_hi - z_lo) * i / n
        for xs, sx in ((xa, 1.0), (xb, -1.0)):
            for (q0, y0), (q1, y1) in zip(prof, prof[1:]):
                # only where this station lies on the slope (between its hip and the nave)
                if not all(min(hip(q), zin(y)) - 1e-6 <= z <= max(hip(q), zin(y)) + 1e-6 for q, y in ((q0, y0), (q1, y1))):
                    continue
                dx, dy = q1 - q0, y1 - y0
                ln = math.hypot(dx, dy)
                nx, ny = -sx * dy / ln, dx / ln          # the slope's outward normal in (x, y)
                a = (xs + sx * q0 + nx * out, y0 + ny * out)
                b = (xs + sx * q1 + nx * out, y1 + ny * out)
                h.face("dome_rib", [(a[0], a[1], z - w / 2), (b[0], b[1], z - w / 2), (b[0], b[1], z + w / 2),
                                    (a[0], a[1], z + w / 2)], (nx, ny, 0.0))


def _finial(h: House, cx: float, cz: float, y0: float, height: float):
    """T-3164: an iron finial, a slim hexagonal shaft standing `height` over (cx, y0, cz) with a
    collar a third of the way up, as the dome's own finial is drawn."""
    hexa = lambda r: [(cx + r * math.cos(math.tau * k / 6), cz + r * math.sin(math.tau * k / 6)) for k in range(6)]
    _prism(h, "dome_rib", hexa(0.04), y0 - 0.03, y0 + height)
    _prism(h, "dome_rib", hexa(0.08), y0 + height * 0.3, y0 + height * 0.3 + 0.06)


def _cresting(h: House, x: float, z0: float, z1: float, y0: float, cr: dict):
    """T-3164: a run of iron cresting along a level crest at x from z0 to z1: a foot rail and a
    top rail `height_m` over the crest, and square pickets between them every `picket_m`, each
    standing `spike_m` past the top rail."""
    ht, sp, w = cr["height_m"], cr["picket_m"], cr.get("rail_m", 0.04)
    sk, pw = cr.get("spike_m", 0.08), cr.get("bar_m", 0.025)
    for ya in (y0, y0 + ht - w):
        _prism(h, "dome_rib", [(x - w / 2, z0), (x + w / 2, z0), (x + w / 2, z1), (x - w / 2, z1)], ya, ya + w)
    # the end pickets stand a bar's width inside the rails' ends, so no face is drawn twice
    a, b = z0 + pw, z1 - pw
    n = max(1, round((b - a) / sp))
    for k in range(n + 1):
        z = a + (b - a) * k / n
        _prism(h, "dome_rib", [(x - pw / 2, z - pw / 2), (x + pw / 2, z - pw / 2), (x + pw / 2, z + pw / 2),
                               (x - pw / 2, z + pw / 2)], y0 + w, y0 + ht + sk)


def pavilion(h: House, ps: dict):
    """T-3179: Beman's conservatory at the head of the Pullman range, as the 1894 Inland plate and
    the Lowe photograph show it, round the K13 vault's pointed nave: a stone podium under the glass
    band, the arched stone entrance in its north end, a pointed transept crossing the nave (its
    glass the opaque substitute, which the kit gives what stands outside the one transparent
    envelope), and a ribbed dome on a glazed drum over the crossing."""
    v = h.v
    L, W, he = v["length_m"], v["width_m"], v["eave_m"]
    nave = h.form["section"]
    pod, po = ps["podium_m"], ps["podium_out_m"]
    _prism(h, "stonework", [(-po, -po), (L + po, -po), (L + po, W + po), (-po, W + po)], 0.0, pod)
    tr = ps["transept"]
    xc, tw, reach = tr["centre_m"], tr["width_m"], tr["reach_m"]
    xa, xb = xc - tw / 2, xc + tw / 2
    # its section rises upright off the eave and turns level at the crest (the plate's ribs), and
    # its end is hipped on the same curve, so the end reads as a curved hip and not a gable
    arm = vault_section({"id": v["id"] + ".transept", "width_m": tw, "eave_m": he, "rise_m": tr["rise_m"],
                         "section": tr.get("section", "elliptic"), "facets": v.get("facets")}, h.data)

    def into(y):
        """How far in from the nave's wall its roof stands at height y (0 at the eave)."""
        for (z0, y0), (z1, y1) in zip(nave, nave[1:]):
            if y0 <= y <= y1 + 1e-9:
                return z0 + (z1 - z0) * (y - y0) / (y1 - y0) if y1 > y0 else z1
        return nave[-1][0]

    for sgn, zw in ((-1.0, 0.0), (1.0, W)):           # the east arm (z < 0) and the west
        ze = zw + sgn * reach
        zin = lambda y: zw - sgn * into(y)
        kf = tr.get("hip_m", tw / 2) / (tw / 2)        # the end's run, as a share of the sides'
        hip = lambda q: ze - sgn * q * kf              # the hip line's z at a run q in from the eave
        for x in (xa, xb):
            h.face("sky_glass", [(x, 0.0, ze), (x, 0.0, zw), (x, he, zw), (x, he, ze)], (x - xc, 0.0, 0.0))
        h.face("sky_glass", [(xa, 0.0, ze), (xb, 0.0, ze), (xb, he, ze), (xa, he, ze)], (0.0, 0.0, sgn))
        for (q0, y0), (q1, y1) in zip(arm, arm[1:]):
            for xs, sx in ((xa, 1.0), (xb, -1.0)):     # the two long slopes, from the hip to the nave
                h.face("sky_glass", [(xs + sx * q0, y0, hip(q0)), (xs + sx * q1, y1, hip(q1)),
                                (xs + sx * q1, y1, zin(y1)), (xs + sx * q0, y0, zin(y0))], (-sx * (y1 - y0), q1 - q0, 0.0))
            end = [(xa + q0, y0, hip(q0)), (xb - q0, y0, hip(q0)), (xb - q1, y1, hip(q1))]
            end += [] if xb - q1 - (xa + q1) < 1e-6 else [(xa + q1, y1, hip(q1))]
            h.face("sky_glass", end, (0.0, q1 - q0, sgn * (y1 - y0)))
        za, zb = sorted((zw - sgn * 0.05, ze + sgn * po))
        _prism(h, "stonework", [(xa - po, za), (xb + po, za), (xb + po, zb), (xa - po, zb)], 0.0, pod + 0.01)
        bd = tr.get("band")
        if bd and bd.get("light_m"):
            # T-3164: the arms' band as both pictures show it on the east arm's north side and
            # its end: white framing, and in it tall lights under a transom, each with a short
            # round-headed light over it, in the planted shade (the north front's band, drawn
            # with its transom): the end from corner to corner of the podium, each side from
            # the nave's wall to the end's corner
            y0 = pod + 0.01
            _lit_band(h, bd, (xa, ze + sgn * po), (1.0, 0.0), (0.0, sgn), -po, tw + po, y0, he)
            for x, sx in ((xa, -1.0), (xb, 1.0)):
                _lit_band(h, bd, (x + sx * po, zw), (0.0, sgn), (sx, 0.0), 0.0, reach + po, y0, he)
        elif bd:
            # T-3164: the upright glass between the podium and the springing, which the Inland
            # plate reads as dark lights in pale frames at eye level, not the roof's sky-lit glass:
            # a dark pane a few cm proud of the substitute glass on the end and both sides, and
            # its frames over it at an even spacing
            y0, y1, bw, sp = pod + 0.01, he, bd["bar_m"], bd["lights_m"]
            o1, o2 = 0.02 + po, 0.03 + po
            walls = [((xa, ze + sgn * o1), (xb, ze + sgn * o1), (0.0, 0.0, sgn), ze + sgn * o2)]
            for x, sx in ((xa, -1.0), (xb, 1.0)):
                walls.append(((x + sx * o1, zw), (x + sx * o1, ze), (sx, 0.0, 0.0), x + sx * o2))
            for (pa, pb, nrm, far) in walls:
                along_x = nrm[2] != 0.0
                h.face("opening", [(pa[0], y0, pa[1]), (pb[0], y0, pb[1]), (pb[0], y1, pb[1]), (pa[0], y1, pa[1])], nrm)
                a0, a1 = (pa[0], pb[0]) if along_x else (pa[1], pb[1])
                n = max(1, round(abs(a1 - a0) / sp))
                pts = [a0 + (a1 - a0) * k / n for k in range(n + 1)]
                for k, t in enumerate(pts):          # the uprights, the end ones inside the run
                    c = min(max(t, min(a0, a1) + bw / 2), max(a0, a1) - bw / 2)
                    q0, q1 = c - bw / 2, c + bw / 2
                    if along_x:
                        h.face("dome_rib", [(q0, y0, far), (q1, y0, far), (q1, y1, far), (q0, y1, far)], nrm)
                    else:
                        h.face("dome_rib", [(far, y0, q0), (far, y0, q1), (far, y1, q1), (far, y1, q0)], nrm)
                f2 = far + (nrm[2] if along_x else nrm[0]) * 0.005
                for yy in (y0 + bw / 2, (y0 + y1) / 2 + bd.get("transom_m", 0.0), y1 - bw / 2):   # sill, transom, head
                    v0, v1 = yy - bw / 2, yy + bw / 2
                    if along_x:
                        h.face("dome_rib", [(a0, v0, f2), (a1, v0, f2), (a1, v1, f2), (a0, v1, f2)], nrm)
                    else:
                        h.face("dome_rib", [(f2, v0, a0), (f2, v0, a1), (f2, v1, a1), (f2, v1, a0)], nrm)
        h.meta["plan_extra_m2"] = h.meta.get("plan_extra_m2", 0.0) + tw * reach
        # glazing bars: a rib up each long slope, standing 3 cm proud
        ribs(h, arm, xa, xb, ze, sgn, zin, hip, tr.get("rib_spacing_m", 0.6))
        cr = ps.get("cresting")
        if cr:
            # T-3164: the iron cresting the plate draws along the arm's level crest, from its hipped
            # end to the nave's glass, and the finial over the end, both in the frame's paint
            q, yt = arm[-1]
            z0, z1 = sorted((hip(q), zin(yt)))
            _cresting(h, xc, z0, z1, yt, cr)
            fh = cr.get("end_finial_m")
            if fh:
                _finial(h, xc, hip(q), yt, fh)
    # the entrance in the north end: an arched opening drawn dark and its stone surround
    en = ps["entrance"]
    zc, r, ht = W / 2, en["width_m"] / 2, en["height_m"]
    arc = [(zc + r * math.cos(math.pi * k / 12), ht - r + r * math.sin(math.pi * k / 12)) for k in range(13)]
    h.face("opening", [(-po - 0.01, 0.0, zc - r), (-po - 0.01, 0.0, zc + r)] + [(-po - 0.01, y, z) for z, y in arc],
           (-1.0, 0.0, 0.0))
    sw, so = en["surround_m"], -po - 0.03
    outer = [(zc + (r + sw) * math.cos(math.pi * k / 12), ht - r + (r + sw) * math.sin(math.pi * k / 12)) for k in range(13)]
    for (za, ya), (zb, yb), (zc_, yc), (zd, yd) in zip(arc, arc[1:], outer[1:], outer):
        h.face("stonework", [(so, ya, za), (so, yb, zb), (so, yc, zc_), (so, yd, zd)], (-1.0, 0.0, 0.0))
    for z0, z1 in ((zc - r - sw, zc - r), (zc + r, zc + r + sw)):
        h.face("stonework", [(so, 0.0, z0), (so, 0.0, z1), (so, ht - r, z1), (so, ht - r, z0)], (-1.0, 0.0, 0.0))
    if ps.get("podium_dress"):
        _podium_dress(h, ps["podium_dress"], L, W, xa, xb, reach, po, pod,
                      {"north": [(zc - r - sw + po, zc + r + sw + po)]})
    # the north end's broad arched frame round the glass, and the bar up its middle (the plate's)
    fw, fo = ps.get("arch_frame_m", 0.0), -0.05
    if fw:
        out = [(W - z, y) for z, y in nave] + [(z, y) for z, y in reversed(nave[:-1])]   # (z, y), eave to eave
        inner = []
        for i, (z, y) in enumerate(out):
            a, b = out[max(i - 1, 0)], out[min(i + 1, len(out) - 1)]
            dz, dy = b[0] - a[0], b[1] - a[1]
            ln = math.hypot(dz, dy)
            nz, ny = dy / ln, -dz / ln                 # inward: the outline runs west to east over the top
            inner.append((z + nz * fw, y + ny * fw))
        for (za, ya), (zb, yb), (zc_, yc), (zd, yd) in zip(out, out[1:], inner[1:], inner):
            h.face("dome_rib", [(fo, ya, za), (fo, yb, zb), (fo, yc, zc_), (fo, yd, zd)], (-1.0, 0.0, 0.0))
        m = ps.get("mullion_m", 0.15)
        h.face("dome_rib", [(fo, he, W / 2 - m / 2), (fo, he, W / 2 + m / 2), (fo, nave[-1][1] - fw, W / 2 + m / 2),
                            (fo, nave[-1][1] - fw, W / 2 - m / 2)], (-1.0, 0.0, 0.0))
    if ps.get("apex_finial_m"):
        # T-3164: the small ornament the plate draws over the north arch's point
        _finial(h, 0.0, W / 2, nave[-1][1], ps["apex_finial_m"])
    # T-3164: the north front's lower storey as the pictures show it (owner, 2026-10-28: "the
    # pavilion's great arched glass front as an opaque gable over a black opening")
    bd = ps.get("band")
    if bd:
        sw_ = en["surround_m"]
        runs = {"north": ((0.0, 0.0), (0.0, 1.0), (-1.0, 0.0), [(0.0, zc - r - sw_), (zc + r + sw_, W)]),
                "west_north": ((0.0, W), (1.0, 0.0), (0.0, 1.0), [(0.0, xa - po)]),
                "east_north": ((L, 0.0), (-1.0, 0.0), (0.0, -1.0), [(L - xa + po, L)])}
        for name in bd["walls"]:                   # only the runs the record names
            o_, t_, n_, spans = runs[name]
            for s0, s1 in spans:
                _lit_band(h, bd, o_, t_, n_, s0, s1, pod, he)
    if ps.get("interior_dark_m"):
        # the conservatory's planted depth behind its glass, drawn in shade inside the nave as
        # palm_house draws the palm house's: the pictures read the glass dark over the lower half
        # of the arch, with the roof's light over it
        i = ps.get("interior_inset_m", 0.3)
        _prism(h, "interior", [(i, i), (L - i, i), (L - i, W - i), (i, W - i)], pod, ps["interior_dark_m"])
    # the drum and dome over the crossing, or (T-3164) where the record's `centre_m` stands them
    # along the nave: both pictures put the Pullman dome north of the transept's middle
    dr = ps["drum"]
    xd = dr.get("centre_m", xc)
    _prism(h, "sky_glass", [(xd + dr["radius_m"] * math.cos(math.tau * (k + 0.5) / dr["sides"]),
                        W / 2 + dr["radius_m"] * math.sin(math.tau * (k + 0.5) / dr["sides"])) for k in range(dr["sides"])],
           dr["base_m"], dr["top_m"])
    h.meta["pavilion"] = {"top_m": round(_dome(h, ps["dome"], xd, W / 2, dr["top_m"], "sky_glass"), 3)}
    if ps.get("gate"):
        gate(h, ps["gate"])
    if ps.get("grounds"):
        grounds(h, ps["grounds"])


def _podium_dress(h: House, pd: dict, L, W, xa, xb, reach, po, pod, cuts: dict):
    """T-3164: the pavilion's stone podium as Lowe's print and the 1894 Inland plate show it:
    a projecting base course and a moulded cap course under the glass band, a broad pier at each
    outer corner standing proud of the wall, and between the piers a field of banded rustication
    (courses standing a few centimetres proud, so each joint reads as a line), the field sunk
    behind the piers' faces, so each run reads as a panel. Only the runs the record names are
    dressed; `cuts` are spans along a run (from its start) where an opening breaks it."""
    ze, zw = -reach - po, W + reach + po
    runs = {  # start (x, z), direction along, outward normal, length, piers at (start, end)
        "north": ((-po, -po), (0.0, 1.0), (-1.0, 0.0), W + 2 * po, (True, True)),
        "east_north": ((-po, -po), (1.0, 0.0), (0.0, -1.0), xa, (True, False)),
        "east_arm_north": ((xa - po, -po), (0.0, -1.0), (-1.0, 0.0), reach, (False, True)),
        "east_arm_end": ((xa - po, ze), (1.0, 0.0), (0.0, -1.0), xb - xa + 2 * po, (True, True)),
        "east_arm_south": ((xb + po, ze), (0.0, 1.0), (1.0, 0.0), reach, (True, False)),
        "east_south": ((xb + po, -po), (1.0, 0.0), (0.0, -1.0), L - xb, (False, True)),
        "west_north": ((-po, W + po), (1.0, 0.0), (0.0, 1.0), xa, (True, False)),
        "west_arm_north": ((xa - po, W + po), (0.0, 1.0), (-1.0, 0.0), reach, (False, True)),
        "west_arm_end": ((xa - po, zw), (1.0, 0.0), (0.0, 1.0), xb - xa + 2 * po, (True, True)),
        "west_arm_south": ((xb + po, zw), (0.0, -1.0), (1.0, 0.0), reach, (True, False)),
        "west_south": ((xb + po, W + po), (1.0, 0.0), (0.0, 1.0), L - xb, (False, True)),
    }
    # each convex corner is one run's: it carries its slabs round the corner, and the run it
    # meets (when that run is dressed too) stops them flush at the corner, so no two faces share
    # a plane there; `yields` names the ends that stop, and the run each one meets
    yields = {"east_north": ("north", None), "west_north": ("north", None),
              "east_arm_north": (None, "east_arm_end"), "east_arm_south": ("east_arm_end", None),
              "west_arm_north": (None, "west_arm_end"), "west_arm_south": ("west_arm_end", None)}
    bc, cc, pi_, ru = pd["base"], pd["cap"], pd["piers"], pd.get("rustication")
    y_b, y_c = bc["height_m"], pod - cc["height_m"]

    def spans(a, b, cut):
        """[a, b] less every cut span."""
        out, cur = [], a
        for c0, c1 in sorted(cut):
            if c1 > cur and c0 < b:
                if c0 > cur:
                    out.append((cur, c0))
                cur = max(cur, c1)
        if cur < b:
            out.append((cur, b))
        return [(p, q) for p, q in out if q - p > 0.05]

    n_piers = n_courses = 0
    for name in pd["runs"]:
        (ox, oz), (tx, tz), (nx, nz), S, (p0, p1) = runs[name]
        P = lambda s, y, off: (ox + tx * s + nx * off, y, oz + tz * s + nz * off)
        n = (nx, 0.0, nz)
        cut = cuts.get(name, [])

        def block(s0, s1, y0, y1, out, top=True, bottom=True, ends=(True, True), role="stonework"):
            """A slab on the run from s0 to s1, y0 to y1, standing `out` proud of the wall; a face
            nobody can see (on the ground, under a cap, against a wall) is left out."""
            h.face(role, [P(s0, y0, out), P(s1, y0, out), P(s1, y1, out), P(s0, y1, out)], n)
            for s_, sg, e in ((s0, -1.0, ends[0]), (s1, 1.0, ends[1])):
                if e:
                    h.face(role, [P(s_, y0, 0.0), P(s_, y0, out), P(s_, y1, out), P(s_, y1, 0.0)],
                           (tx * sg, 0.0, tz * sg))
            if top:
                h.face(role, [P(s0, y1, 0.0), P(s1, y1, 0.0), P(s1, y1, out), P(s0, y1, out)], Y)
            if bottom:
                h.face(role, [P(s0, y0, out), P(s1, y0, out), P(s1, y0, 0.0), P(s0, y0, 0.0)], (0.0, -1.0, 0.0))

        y0_, y1_ = yields.get(name, (None, None))
        stop = (y0_ in pd["runs"], y1_ in pd["runs"])
        convex = (p0, p1)

        def reach_of(out):
            """The span a slab standing `out` proud runs: round a corner it owns, flush at one it
            yields; at an inside corner the run starting there begins flush and the run ending
            there stops `out` short, against the other's front."""
            lo = -out if convex[0] and not stop[0] else 0.0
            hi = S if stop[1] else (S + out if convex[1] else S - out)
            return lo, hi

        def ends_of(a, b, lo, hi):
            """End faces for a slab from a to b: none where it stops at a corner or runs into a wall."""
            return (a > lo + 1e-6 or (convex[0] and not stop[0]), b < hi - 1e-6 or (convex[1] and not stop[1]))
        lo, hi = reach_of(bc["out_m"])
        for a, b in spans(lo, hi, cut):
            block(a, b, 0.0, y_b, bc["out_m"], bottom=False, ends=ends_of(a, b, lo, hi))
        lo, hi = reach_of(cc["out_m"])
        for a, b in spans(lo, hi, cut):
            block(a, b, y_c, pod + 0.02, cc["out_m"], ends=ends_of(a, b, lo, hi))
        w, pout = pi_["width_m"], pi_["out_m"]
        lo, hi = reach_of(pout)
        pier = []
        if p0:
            pier.append((lo, w))
        if p1:
            pier.append((S - w, hi))
        for a, b in pier:
            block(a, b, y_b, y_c, pout, top=False, bottom=False, ends=ends_of(a, b, lo, hi))
            n_piers += 1
        if ru:
            k = max(1, round((y_c - y_b) / ru["course_m"]))
            ch, j = (y_c - y_b) / k, ru["joint_m"]
            for i in range(k):
                ya, yb = y_b + i * ch + (j / 2 if i else 0.0), y_b + (i + 1) * ch - (j / 2 if i < k - 1 else 0.0)
                for a, b in spans(0.0, S, cut + [(a_ - 0.01, b_ + 0.01) for a_, b_ in pier]):
                    # a course's 2 cm ledges are left out, and so is an end against the nave's wall
                    block(a, b, ya, yb, ru["out_m"], top=False, bottom=False,
                          ends=(a > 1e-6 or p0, b < S - 1e-6 or p1), role="stone_field")
                    n_courses += 1
    h.meta["podium_dress"] = {"piers": n_piers, "course_runs": n_courses}


def _roll(h: House, role, x0, x1, y, z, r, sides=12):
    """T-3164: a scroll's roll, a cylinder lying across x from x0 to x1 about (y, z), capped."""
    ring = [(y + r * math.sin(math.tau * k / sides), z + r * math.cos(math.tau * k / sides)) for k in range(sides)]
    for k in range(sides):
        (ya, za), (yb, zb) = ring[k], ring[(k + 1) % sides]
        h.face(role, [(x0, ya, za), (x1, ya, za), (x1, yb, zb), (x0, yb, zb)], (0.0, (ya + yb) / 2 - y, (za + zb) / 2 - z))
    for x, sx in ((x0, -1.0), (x1, 1.0)):
        h.face(role, [(x, yy, zz) for yy, zz in ring], (sx, 0.0, 0.0))


def _sunk_face(h: House, role, P, n, width, y0, y1, pn: dict):
    """T-3164: one upright face of a shaft with a sunk panel in it. `P(s, y, off)` is the point
    `s` along the face, at height `y`, `off` out along its normal `n`; the panel stands
    `margin_m` in from each edge over `y_m`, sunk `depth_m`, its four reveals drawn."""
    m, (p0, p1), d = pn["margin_m"], pn["y_m"], pn["depth_m"]
    s0, s1 = m, width - m
    quad = lambda a0, a1, b0, b1, off=0.0: [P(a0, b0, off), P(a1, b0, off), P(a1, b1, off), P(a0, b1, off)]
    for a0, a1, b0, b1 in ((0.0, s0, y0, y1), (s1, width, y0, y1), (s0, s1, y0, p0), (s0, s1, p1, y1)):
        h.face(role, quad(a0, a1, b0, b1), n)
    h.face(role, quad(s0, s1, p0, p1, -d), n)
    e = _unit(_sub(P(1.0, 0.0, 0.0), P(0.0, 0.0, 0.0)))
    h.face(role, [P(s0, p0, 0.0), P(s0, p1, 0.0), P(s0, p1, -d), P(s0, p0, -d)], e)
    h.face(role, [P(s1, p0, 0.0), P(s1, p1, 0.0), P(s1, p1, -d), P(s1, p0, -d)], _mul(e, -1.0))
    h.face(role, [P(s0, p0, 0.0), P(s1, p0, 0.0), P(s1, p0, -d), P(s0, p0, -d)], Y)
    h.face(role, [P(s0, p1, 0.0), P(s1, p1, 0.0), P(s1, p1, -d), P(s0, p1, -d)], (0.0, -1.0, 0.0))


def _panelled_shaft(h: House, role, x0, x1, za, zb, y0, y1, pn: dict):
    """T-3164: a gate pier's square shaft from y0 to y1 with a sunk panel in each of its four
    faces, as both pictures show it on the faces they see (the street face and the drive's)."""
    faces = (  # (start corner, direction along the face, outward normal, width)
        ((x0, za), (1.0, 0.0), (0.0, 0.0, -1.0), x1 - x0),
        ((x1, za), (0.0, 1.0), (1.0, 0.0, 0.0), zb - za),
        ((x1, zb), (-1.0, 0.0), (0.0, 0.0, 1.0), x1 - x0),
        ((x0, zb), (0.0, -1.0), (-1.0, 0.0, 0.0), zb - za),
    )
    for (cx, cz), (ex, ez), n, width in faces:
        P = lambda s, y, off, cx=cx, cz=cz, ex=ex, ez=ez, n=n: (cx + ex * s + n[0] * off, y, cz + ez * s + n[2] * off)
        _sunk_face(h, role, P, n, width, y0, y1, pn)


def _relief(h: House, role, P, n, top, bottom, buried_start=False):
    """T-3164: a strip standing proud of a face: `top` and `bottom` its edges as [(s, y)] in
    the face's frame, as many points each, drawn as front quads with their reveals and ends
    (the first end left out when `buried_start`: it lies in the face the strip runs out of)."""
    for (a, b), (c, d) in zip(zip(top, bottom), zip(top[1:], bottom[1:])):
        h.face(role, [P(*b, 1.0), P(*d, 1.0), P(*c, 1.0), P(*a, 1.0)], n)
        h.face(role, [P(*a, 0.0), P(*c, 0.0), P(*c, 1.0), P(*a, 1.0)], Y)
        h.face(role, [P(*b, 0.0), P(*d, 0.0), P(*d, 1.0), P(*b, 1.0)], (0.0, -1.0, 0.0))
    _ends(h, role, P, top, bottom, ((-1, -2),) if buried_start else ((0, 1), (-1, -2)))


def _ends(h: House, role, P, one, other, which=((0, 1), (-1, -2))):
    """The end faces of a relief strip between the edges `one` and `other`, each facing off
    the strip along its own run."""
    for i, j in which:
        a, b = one[i], other[i]
        h.face(role, [P(*a, 0.0), P(*b, 0.0), P(*b, 1.0), P(*a, 1.0)], _sub(P(*a, 0.0), P(*one[j], 0.0)))


def _wing_carving(h: House, role, xa, zp, sg, run, r, hi, lo, cv: dict):
    """T-3164: the carving on a gate wing's street face (x = xa, facing 18th Street), as Lowe's
    photograph and the 1894 plate show it: a spiral C-scroll by the pier, leafage trailing from
    it under the sweep toward the roll, and a fillet over the plain base below them. Everything
    stands `proud_m` off the face; `d` runs along the wing from the pier, `y` up."""
    t = cv["proud_m"]
    n = (-1.0, 0.0, 0.0)
    P = lambda d, y, k: (xa - t * k, y, zp + sg * d)
    top_y = lambda d: lo + (hi - lo) * (1.0 - min(d, run) / run) ** 2
    f0, f1 = cv["fillet_m"]
    end = run - r                               # where the block under the roll begins
    stop = end - 0.01                           # the fillet stops short of the block's face
    _relief(h, role, P, n, [(0.0, f1), (stop, f1)], [(0.0, f0), (stop, f0)], buried_start=True)
    sc = cv["scroll"]
    dc, yc, (r0, r1), turns, wd, ns = sc["d_m"], sc["y_m"], sc["r_m"], sc["turns"], sc["width_m"], sc["segments"]
    outer, inner = [], []
    for k in range(ns + 1):
        f = k / ns
        a, rr = math.tau * turns * f, r0 + (r1 - r0) * f
        c, s_ = math.cos(a), math.sin(a)
        outer.append((dc + rr * s_, yc + rr * c))
        inner.append((dc + (rr - wd) * s_, yc + (rr - wd) * c))
    for (a, b), (c, d) in zip(zip(outer, inner), zip(outer[1:], inner[1:])):
        h.face(role, [P(*a, 1.0), P(*c, 1.0), P(*d, 1.0), P(*b, 1.0)], n)
        for e0, e1, inward in ((a, c, False), (b, d, True)):
            mx, my = (e0[0] + e1[0]) / 2 - dc, (e0[1] + e1[1]) / 2 - yc
            hint = (0.0, -my if inward else my, sg * (-mx if inward else mx))
            h.face(role, [P(*e0, 0.0), P(*e1, 0.0), P(*e1, 1.0), P(*e0, 1.0)], hint)
    _ends(h, role, P, outer, inner)
    lf = cv["leaf"]
    d0, d1, nl = dc + r0, end - lf["clear_m"], lf["lobes"]
    xs = [d0 + (d1 - d0) * k / (2 * nl) for k in range(2 * nl + 1)]
    top = [(d, top_y(d) - lf["below_top_m"] - (lf["dip_m"] if k % 2 else 0.0)) for k, d in enumerate(xs)]
    _relief(h, role, P, n, top, [(d, lf["y_m"]) for d in xs])


def gate(h: House, gs: dict):
    """T-3164: the estate's gate on 18th Street, as the 1894 Inland plate draws it in its
    foreground: two square stone piers on a plinth under a stepped cap, each with a low wing
    returning toward the drive along the street line, its top sweeping down from the pier to a
    scroll's roll over a block at the drive's edge. Placed in this record's frame (x = u south
    from the north-east corner, z = -v) where the plate's camera puts their bases."""
    xn, s = gs["north_u_m"], gs["pier_m"]
    x0, x1 = xn, xn + s
    rect = lambda a, b, c, d: [(a, c), (b, c), (b, d), (a, d)]
    w = gs["wing"]
    for p in gs["piers"]:
        za, zb = sorted((-p["v_m"][0], -p["v_m"][1]))
        po, pl = gs["plinth_out_m"], gs["plinth_m"]
        _prism(h, "stonework", rect(x0 - po, x1 + po, za - po, zb + po), 0.0, pl)
        if gs.get("panel"):
            _panelled_shaft(h, "stonework", x0, x1, za, zb, pl, gs["shaft_m"], gs["panel"])
        else:
            _prism(h, "stonework", rect(x0, x1, za, zb), pl, gs["shaft_m"], top=False)
        cap = gs["cap"]                         # the cap's courses, bottom up, each `out` past the shaft
        for i, (out, y0, y1) in enumerate(cap):
            below, above = cap[i - 1][0] if i else 0.0, cap[i + 1][0] if i + 1 < len(cap) else -1.0
            # a course's top or underside is drawn only where it shows past its neighbour
            _prism(h, "stonework", rect(x0 - out, x1 + out, za - out, zb + out), y0, y1,
                   top=above < out, bottom=out > below)
        # the wing: from the pier's face toward the drive (z grows with `sg`), centred on the pier
        zp, zw = -p["wing_v_m"][0], -p["wing_v_m"][1]
        sg = 1.0 if zw > zp else -1.0
        L, t, r = abs(zw - zp), w["thickness_m"], w["scroll_r_m"]
        xa, xb = x0 + (s - t) / 2, x0 + (s + t) / 2
        hi, lo, n = w["high_m"], w["low_m"], w.get("segments", 8)
        run = L - w["end_m"]                      # the sweep's run, from the pier to the roll's crown
        top = [(run * k / n, lo + (hi - lo) * (1.0 - k / n) ** 2) for k in range(n + 1)]
        for (d0, y0), (d1, y1) in zip(top, top[1:]):
            z0_, z1_ = zp + sg * d0, zp + sg * d1
            for x, sx in ((xa, -1.0), (xb, 1.0)):
                h.face("stonework", [(x, 0.0, z0_), (x, 0.0, z1_), (x, y1, z1_), (x, y0, z0_)], (sx, 0.0, 0.0))
            h.face("stonework", [(xa, y0, z0_), (xb, y0, z0_), (xb, y1, z1_), (xa, y1, z1_)], (0.0, d1 - d0, sg * (y0 - y1)))
        # the roll at the sweep's foot, and the block under it out to the drive's edge
        zr = zp + sg * run
        _roll(h, "stonework", xa - 0.02, xb + 0.02, lo - r, zr, r)
        eb = w["block_m"]
        zc, zd = sorted((zr - sg * r, zw))
        _prism(h, "stonework", rect(xa - 0.04, xb + 0.04, zc, zd), 0.0, eb)
        if gs.get("carving"):
            _wing_carving(h, "stonework", xa, zp, sg, run, r, hi, lo, gs["carving"])


GRAVEL_PROUD_M = 0.02   # a drive's gravel over the ground its row measures, as K14's drives stand


def grounds(h: House, gr: dict):
    """T-3164: the ground the gate opens onto, as the 1894 Inland plate and Lowe's print show it
    from 18th Street: the gravel drive between the gate's wings, the walk that enters east of the
    east pier and runs to the conservatory's door, the forecourt along the conservatory's north
    front, and the low stone coping that closes the lawn on the lot line west of the gate.

    Each gravel surface is a run of `rows_m` [u, v_a, v_b, lift] across it, laid as quads from row
    to row GRAVEL_PROUD_M over its `lift` (the app's ground over the house's bed, measured where
    the row runs, since the app beds the house on the lowest ground under its feet and the drive
    runs uphill of it). The coping follows `line_m` [[u, v], ...], its street face on the line
    and `thick_m` into the lot (the side the line has on its right as it runs), a body to `body_m`
    under a cap course to `top_m` standing `cap_out_m` past both faces; its first end abuts the
    west pier and is not drawn. Placed in this record's frame (x = u, z = -v), as the gate is."""
    for srf in gr["gravel"]:
        rows = srf["rows_m"]
        for (u0, a0, b0, l0), (u1, a1, b1, l1) in zip(rows, rows[1:]):
            y0, y1 = l0 + GRAVEL_PROUD_M, l1 + GRAVEL_PROUD_M
            h.face("gravel", [(u0, y0, -a0), (u0, y0, -b0), (u1, y1, -b1), (u1, y1, -a1)], Y)
    cp = gr.get("coping")
    if not cp:
        return
    line = [tuple(map(float, q)) for q in cp["line_m"]]
    t, hb, ht, co = cp["thick_m"], cp["body_m"], cp["top_m"], cp["cap_out_m"]
    norms = []
    for (ua, va), (ub, vb) in zip(line, line[1:]):
        L = math.hypot(ub - ua, vb - va)
        norms.append(((vb - va) / L, -(ub - ua) / L))      # into the lot, in (u, v)
    def offset(k):
        """The unit-into-the-lot offset at vertex k, mitred where two runs meet."""
        if k == 0:
            return norms[0]
        if k == len(line) - 1:
            return norms[-1]
        (a, b), (c, d) = norms[k - 1], norms[k]
        m = 1.0 + a * c + b * d
        return ((a + c) / m, (b + d) / m)
    offs = [offset(k) for k in range(len(line))]
    at = lambda k, d, y: (line[k][0] + offs[k][0] * d, y, -(line[k][1] + offs[k][1] * d))
    for k in range(len(line) - 1):
        nu, nv = norms[k]
        out, inw = (-nu, 0.0, nv), (nu, 0.0, -nv)
        for d, y0, y1, hint in ((0.0, 0.0, hb, out), (t, 0.0, hb, inw),
                                (-co, hb, ht, out), (t + co, hb, ht, inw)):
            h.face("stonework", [at(k, d, y0), at(k + 1, d, y0), at(k + 1, d, y1), at(k, d, y1)], hint)
        h.face("stonework", [at(k, -co, ht), at(k + 1, -co, ht), at(k + 1, t + co, ht), at(k, t + co, ht)], Y)
    # the far end, where the coping stops at the Calumet Avenue line
    k = len(line) - 1
    eu, ev = line[k][0] - line[k - 1][0], line[k][1] - line[k - 1][1]
    end = (eu, 0.0, -ev)
    h.face("stonework", [at(k, 0.0, 0.0), at(k, t, 0.0), at(k, t, hb), at(k, 0.0, hb)], end)
    h.face("stonework", [at(k, -co, hb), at(k, t + co, hb), at(k, t + co, ht), at(k, -co, ht)], end)


def structure_house(st: dict, phase: dict, data: dict | None = None) -> House:
    """The conservatory a k13_conservatories record names, built against its host wall."""
    data = data or load()
    form = phase["form"]
    h = House(form["conservatory"]["value"], data).build()
    # T-1905: a host wall that is another record's own (`structure`) is that building's, so
    # nothing is built for it: 1905 Prairie's conservatory stands against the house's south wall
    if h.form["host"] and "structure" not in form["host_wall"]["value"]:
        host_wing(h, form["host_wall"]["value"])
        host_dress(h, form["host_wall"]["value"])
    if form["conservatory"]["value"].get("stonework"):
        palm_house(h, form["conservatory"]["value"]["stonework"])
    v = form["conservatory"]["value"]
    if v.get("masonry"):
        masonry_walls(h, v["masonry"])
    if v.get("rotunda"):
        rotunda(h, v["rotunda"])
    if v.get("pavilion"):
        pavilion(h, v["pavilion"])
    return h


def structure_glb(h: House, data: dict, structure_id: str, phase_id: str, scene_ids) -> bytes:
    name = f"{structure_id}__{phase_id}"
    # T-1905: a house standing on a base (`base_m`, 1905 Prairie's on its stone bow) is built
    # and gated in its own frame and lifted only as it is written, so its plinth, glass and
    # pipes are measured from the ground they stand on, the base's top
    lift = float(h.v.get("base_m", 0.0))
    return to_glb([h], data, host_color=(h.meta.get("host") or {}).get("color"), stone_color=h.meta.get("stone_color"),
                  node_name=name, node_extras={
        "structure_id": structure_id, "phase_id": phase_id, "scene_ids": list(scene_ids),
        **({"base_m": lift} if lift else {})},
        extras={"ticket": "T-2306", "structure": f"data/structures/{structure_id}.json"}, lift=lift)


def to_glb(kit: list[House], data: dict, node_name: str | None = None, node_extras: dict | None = None,
           extras: dict | None = None, host_color=None, stone_color=None, lift: float = 0.0) -> bytes:
    mats = materials(data)
    if node_extras:     # a structure in the scene carries only the materials it draws (T-2306)
        used = {ROLE_MATERIAL[r] for h in kit for r, pr in h.prims.items() if pr.idx}
        mats = {k: m for k, m in mats.items() if k in used}
        if "house_wall" in mats and host_color:
            mats["house_wall"] = {**mats["house_wall"], "color": tuple(host_color)}
        if "stone" in mats and stone_color:
            mats["stone"] = {**mats["stone"], "color": tuple(stone_color)}
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
                pos += ([tuple(round(c, 5) for c in q) for q in pr.pos] if not lift
                        else [(round(q[0], 5), round(q[1] + lift, 5), round(q[2], 5)) for q in pr.pos])
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
