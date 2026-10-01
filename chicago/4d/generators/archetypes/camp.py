"""camp — the canvas, wagons and fires of the transient crowd of the summer of 1835.

See `camp_params` for the evidence, the forms and every dimension. This module only
builds: each pitched thing is made in its own frame (x across its front, y from its
front to its back, z up) and placed into the camp by a rotation about z and a
translation, so a ring can face its tents inwards with the same builders a row uses.

## No figure, no smoke

docs/LIBERTIES.md L1 binds every vertex here. A fire ring is stones, ash and a pot
crane, and the fire is out: a flame or a smoke column is the one thing a visitor
would read as a person at the fire, and the camp is drawn as the town drew it on a
morning when everybody had gone up the street to the land office.

## Deterministic, with no seed on the record

Two bakes of one record must make the same bytes (generators/mesh_inputs.py hashes
this file and the parameters, nothing else). The only variation — a tent pitched a
few degrees off square, a scatter's jitter — comes from `_jitter`, a pure function of
the pitch's index, so it varies along the camp and never between bakes.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from common import materials  # noqa: E402
from common.mesh import MeshBuilder, simple_material  # noqa: E402
from archetypes.camp_params import (  # noqa: E402
    BRUSH_SHELTER_D_M, BRUSH_SHELTER_W_M, FRONT_BAND_M, PITCH_GAP_M,
    WAGON_BED_L_M, WAGON_BED_W_M, WAGON_TONGUE_M, WAGON_TRACK_M, WALL_TENT_D_M,
    WALL_TENT_RIDGE_M, WALL_TENT_W_M, WALL_TENT_WALL_M, WEDGE_TENT_D_M,
    WEDGE_TENT_RIDGE_M, WEDGE_TENT_W_M, CampParams,
)

M_CANVAS, M_WOOD, M_DARK, M_STONE, M_BRUSH = 0, 1, 2, 3, 4

# Unbleached cotton duck. New canvas is the pale cream of the cloth; a season under
# a lake sun and a wood fire greys and browns it, and a patched cloth is the weathered
# one a shade darker. Chosen against the plank walks' weathered tones (L320) so the
# canvas reads as cloth beside timber and never as a white wall — and checked in the
# lit browser, where the first, paler values (0.65 for weathered) tone-mapped to white.
CANVAS_RGBA = {
    "new": (0.640, 0.610, 0.530, 1.0),
    "weathered": (0.480, 0.452, 0.390, 1.0),
    "patched": (0.430, 0.400, 0.340, 1.0),
}
# Wagon boxes, tent poles, chests and the woodpile: grey-brown weathered wood.
WOOD_RGBA = (0.330, 0.270, 0.200, 1.0)
# Cold ash, the iron of a tyre and the inside of a tent seen through the door.
DARK_RGBA = (0.090, 0.082, 0.072, 1.0)
# Field stone round a fire.
STONE_RGBA = (0.420, 0.400, 0.370, 1.0)
# Cut brush, a few days wilted.
BRUSH_RGBA = (0.300, 0.300, 0.170, 1.0)


def _jitter(i: int, k: int = 0) -> float:
    """A fixed value in [-1, 1] for pitch `i`, channel `k`. Deterministic."""
    x = math.sin((i + 1) * 12.9898 + (k + 1) * 78.233) * 43758.5453
    return 2.0 * (x - math.floor(x)) - 1.0


class _Placed:
    """Adds polygons to a MeshBuilder through a rotation about z and a translation."""

    def __init__(self, b: MeshBuilder, x: float, y: float, rot_deg: float, conf: float):
        self.b, self.x, self.y, self.conf = b, x, y, conf
        th = math.radians(rot_deg)
        self.c, self.s = math.cos(th), math.sin(th)

    def poly(self, pts, mat: int) -> None:
        self.b.add_poly([(self.x + p[0] * self.c - p[1] * self.s,
                          self.y + p[0] * self.s + p[1] * self.c, p[2]) for p in pts],
                        self.conf, mat)

    def box(self, x0, y0, z0, x1, y1, z1, mat: int, skip=()) -> None:
        f = {
            "bottom": [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0)],
            "top": [(x0, y0, z1), (x0, y1, z1), (x1, y1, z1), (x1, y0, z1)],
            "front": [(x0, y0, z0), (x0, y0, z1), (x1, y0, z1), (x1, y0, z0)],
            "back": [(x1, y1, z0), (x1, y1, z1), (x0, y1, z1), (x0, y1, z0)],
            "left": [(x0, y1, z0), (x0, y1, z1), (x0, y0, z1), (x0, y0, z0)],
            "right": [(x1, y0, z0), (x1, y0, z1), (x1, y1, z1), (x1, y1, z0)],
        }
        for k, pts in f.items():
            if k not in skip:
                self.poly(pts, mat)

    def disc_x(self, cx, cy, cz, r, half_t, mat: int, n: int = 10) -> None:
        """A wheel: an n-gon prism whose axis runs along y."""
        ring = [(cx + r * math.cos(2 * math.pi * i / n), cz + r * math.sin(2 * math.pi * i / n))
                for i in range(n)]
        self.poly([(x, cy - half_t, z) for x, z in ring], mat)
        self.poly([(x, cy + half_t, z) for x, z in reversed(ring)], mat)
        for i in range(n):
            (xa, za), (xb, zb) = ring[i], ring[(i + 1) % n]
            self.poly([(xa, cy - half_t, za), (xb, cy - half_t, zb),
                       (xb, cy + half_t, zb), (xa, cy + half_t, za)], mat)

    def log_x(self, x0, x1, cy, cz, r, mat: int, n: int = 6) -> None:
        """A log or a pole lying along x: an n-gon prism."""
        ring = [(cy + r * math.cos(2 * math.pi * i / n), cz + r * math.sin(2 * math.pi * i / n))
                for i in range(n)]
        for i in range(n):
            (ya, za), (yb, zb) = ring[i], ring[(i + 1) % n]
            self.poly([(x0, ya, za), (x0, yb, zb), (x1, yb, zb), (x1, ya, za)], mat)
        self.poly([(x0, y, z) for y, z in reversed(ring)], mat)
        self.poly([(x1, y, z) for y, z in ring], mat)

    def post(self, x, y, z0, z1, side, mat: int) -> None:
        h = side / 2.0
        self.box(x - h, y - h, z0, x + h, y + h, z1, mat, skip=("bottom",))


# ------------------------------------------------------------------ the pitches

def _wall_tent(p: _Placed) -> None:
    """A wall tent, door at y = 0, centred on x = 0."""
    hw, d = WALL_TENT_W_M / 2.0, WALL_TENT_D_M
    wz, rz = WALL_TENT_WALL_M, WALL_TENT_RIDGE_M
    fly = 0.12
    # the four walls; the front wall carries the door
    p.poly([(hw, d, 0), (hw, d, wz), (-hw, d, wz), (-hw, d, 0)], M_CANVAS)        # back
    p.poly([(-hw, 0, 0), (-hw, 0, wz), (-hw, d, wz), (-hw, d, 0)][::-1], M_CANVAS)  # left
    p.poly([(hw, 0, 0), (hw, d, 0), (hw, d, wz), (hw, 0, wz)][::-1], M_CANVAS)      # right
    door = 0.45
    p.poly([(-hw, 0, 0), (-door, 0, 0), (-door, 0, wz), (-hw, 0, wz)][::-1], M_CANVAS)
    p.poly([(door, 0, 0), (hw, 0, 0), (hw, 0, wz), (door, 0, wz)][::-1], M_CANVAS)
    # the gable ends, the front one with the door running up into it
    p.poly([(-hw, d, wz), (hw, d, wz), (0, d, rz)][::-1], M_CANVAS)
    p.poly([(-hw, 0, wz), (-door, 0, wz), (0, 0, rz - 0.35), (0, 0, rz)], M_CANVAS)
    p.poly([(door, 0, wz), (hw, 0, wz), (0, 0, rz), (0, 0, rz - 0.35)][::-1], M_CANVAS)
    # the door: the flaps tied back show the dark inside
    p.poly([(-door, 0.02, 0), (door, 0.02, 0), (door, 0.02, wz), (0, 0.02, rz - 0.35),
            (-door, 0.02, wz)][::-1], M_DARK)
    # the roof, with a little fly past the walls
    p.poly([(-hw - fly, -fly, wz - 0.06), (-hw - fly, d + fly, wz - 0.06),
            (0, d + fly, rz), (0, -fly, rz)][::-1], M_CANVAS)
    p.poly([(hw + fly, -fly, wz - 0.06), (0, -fly, rz), (0, d + fly, rz),
            (hw + fly, d + fly, wz - 0.06)][::-1], M_CANVAS)
    # the uprights and the ridge pole standing proud
    p.post(0, -0.05, 0, rz + 0.12, 0.06, M_WOOD)
    p.post(0, d + 0.05, 0, rz + 0.12, 0.06, M_WOOD)


def _wedge_tent(p: _Placed) -> None:
    """A wedge tent, door at y = 0, centred on x = 0."""
    hw, d, rz = WEDGE_TENT_W_M / 2.0, WEDGE_TENT_D_M, WEDGE_TENT_RIDGE_M
    p.poly([(-hw, 0, 0), (-hw, d, 0), (0, d, rz), (0, 0, rz)][::-1], M_CANVAS)
    p.poly([(hw, 0, 0), (0, 0, rz), (0, d, rz), (hw, d, 0)][::-1], M_CANVAS)
    p.poly([(hw, d, 0), (0, d, rz), (-hw, d, 0)][::-1], M_CANVAS)
    # the front: two flaps, one tied back, so half the triangle is the dark inside
    p.poly([(-hw, 0, 0), (0, 0, 0), (0, 0, rz)][::-1], M_CANVAS)
    p.poly([(0, 0.02, 0), (hw * 0.75, 0.02, 0), (0, 0.02, rz)][::-1], M_DARK)
    p.poly([(hw * 0.75, 0, 0), (hw, 0, 0), (0, 0, rz)][::-1], M_CANVAS)
    p.post(0, -0.05, 0, rz + 0.10, 0.05, M_WOOD)
    p.post(0, d + 0.05, 0, rz + 0.10, 0.05, M_WOOD)


def _wagon(p: _Placed) -> None:
    """A covered wagon along x, its tongue towards -x on the ground, centred on y = 0.

    The frame's x = 0 is the tongue's tip so the pitch starts where the wagon does.
    """
    t = WAGON_TONGUE_M
    x0, x1 = t, t + WAGON_BED_L_M
    hw = WAGON_BED_W_M / 2.0
    bz0, bz1 = 0.78, 1.30
    p.box(x0, -hw, bz0, x1, hw, bz1, M_WOOD)
    # the running gear: two axles and four wheels, iron-tyred, the hind pair taller
    gauge = WAGON_TRACK_M / 2.0 - 0.05
    for cx, r in ((x0 + 0.55, 0.50), (x1 - 0.55, 0.66)):
        p.box(cx - 0.06, -gauge, r - 0.06, cx + 0.06, gauge, r + 0.06, M_WOOD)
        for side in (-1, 1):
            p.disc_x(cx, side * gauge, r, r, 0.04, M_DARK)
    # the bonnet: canvas on hoop bows standing well above the box, drawn as a
    # half-ellipse tunnel — the bows rise higher than the box is wide, which is the
    # silhouette that reads as a covered wagon and not as a cart with a lid
    n, rb = 8, hw + 0.08
    arc = [(rb * math.cos(math.pi * i / n), bz1 + 0.05 + 1.15 * math.sin(math.pi * i / n))
           for i in range(n + 1)]
    xa, xb = x0 - 0.15, x1 + 0.15
    for i in range(n):
        (ya, za), (yb, zb) = arc[i], arc[i + 1]
        p.poly([(xa, ya, za), (xa, yb, zb), (xb, yb, zb), (xb, ya, za)][::-1], M_CANVAS)
    # the bonnet is closed at the back with its puckered end, open at the front
    p.poly([(xb, y, z) for y, z in arc] + [(xb, -rb, bz1), (xb, rb, bz1)][::-1], M_CANVAS)
    p.poly([(xa + 0.05, y * 0.92, z - 0.03) for y, z in arc][::-1], M_DARK)
    # the tongue, down on the ground at its tip
    p.poly([(0.0, -0.05, 0.05), (x0 + 0.4, -0.05, 0.62), (x0 + 0.4, 0.05, 0.62),
            (0.0, 0.05, 0.05)], M_WOOD)
    p.poly([(0.0, 0.05, 0.12), (x0 + 0.4, 0.05, 0.69), (x0 + 0.4, -0.05, 0.69),
            (0.0, -0.05, 0.12)], M_WOOD)


def _brush_shelter(p: _Placed) -> None:
    """A lean-to: two forked posts and a ridge pole at the front, brush sloping back
    to the ground. Open at the front, which faces y = 0."""
    hw, d = BRUSH_SHELTER_W_M / 2.0, BRUSH_SHELTER_D_M
    fz = 1.45
    p.post(-hw + 0.1, 0.1, 0, fz + 0.1, 0.08, M_WOOD)
    p.post(hw - 0.1, 0.1, 0, fz + 0.1, 0.08, M_WOOD)
    p.log_x(-hw - 0.15, hw + 0.15, 0.1, fz, 0.05, M_WOOD)
    p.poly([(-hw - 0.2, 0.0, fz + 0.05), (hw + 0.2, 0.0, fz + 0.05),
            (hw + 0.3, d, 0.0), (-hw - 0.3, d, 0.0)], M_BRUSH)
    p.poly([(-hw - 0.3, d, 0.0), (hw + 0.3, d, 0.0),
            (hw + 0.2, 0.0, fz + 0.05), (-hw - 0.2, 0.0, fz + 0.05)], M_BRUSH)
    p.poly([(-hw, 0.1, 0), (-hw, 0.1, fz), (-hw - 0.2, d, 0)], M_BRUSH)
    p.poly([(hw, 0.1, 0), (hw + 0.2, d, 0), (hw, 0.1, fz)], M_BRUSH)
    p.poly([(-hw + 0.1, 0.4, 0.02), (hw - 0.1, 0.4, 0.02), (hw - 0.1, d - 0.3, 0.02),
            (-hw + 0.1, d - 0.3, 0.02)], M_DARK)


def _fire_ring(p: _Placed) -> None:
    """Cold ash inside a ring of field stones, a pot crane over it. No flame."""
    n, r = 8, 0.48
    p.poly([(0.42 * math.cos(2 * math.pi * i / 10), 0.42 * math.sin(2 * math.pi * i / 10),
             0.025) for i in range(10)], M_DARK)
    for i in range(n):
        a = 2 * math.pi * (i + 0.5 * _jitter(i, 7)) / n
        cx, cy = r * math.cos(a), r * math.sin(a)
        s = 0.11 + 0.03 * _jitter(i, 8)
        p.box(cx - s, cy - s, 0.0, cx + s, cy + s, 0.13 + 0.04 * _jitter(i, 9), M_STONE,
              skip=("bottom",))
    for x in (-0.62, 0.62):
        p.post(x, 0.0, 0, 0.92, 0.05, M_WOOD)
    p.log_x(-0.70, 0.70, 0.0, 0.90, 0.025, M_WOOD)
    p.box(-0.13, -0.13, 0.42, 0.13, 0.13, 0.66, M_DARK)          # the kettle, hung


def _woodpile(p: _Placed) -> None:
    """Split cordwood, three courses, laid along x."""
    for k, (n, z) in enumerate(((4, 0.07), (3, 0.20), (2, 0.33))):
        for i in range(n):
            y = (i - (n - 1) / 2.0) * 0.15
            p.log_x(-0.6 + 0.04 * _jitter(i, k), 0.6, y, z, 0.07, M_WOOD)


def _baggage(p: _Placed) -> None:
    """What an open-sky sleeper had: two chests and a barrel, a blanket roll on top."""
    p.box(-0.55, -0.22, 0.0, 0.10, 0.22, 0.42, M_WOOD, skip=("bottom",))
    p.box(0.18, -0.20, 0.0, 0.70, 0.18, 0.34, M_WOOD, skip=("bottom",))
    p.log_x(-0.50, 0.05, 0.0, 0.52, 0.10, M_CANVAS)
    n, r = 8, 0.24
    ring = [(-0.95 + r * math.cos(2 * math.pi * i / n), 0.05 + r * math.sin(2 * math.pi * i / n))
            for i in range(n)]
    for i in range(n):
        (xa, ya), (xb, yb) = ring[i], ring[(i + 1) % n]
        p.poly([(xa, ya, 0.0), (xb, yb, 0.0), (xb, yb, 0.70), (xa, ya, 0.70)][::-1], M_WOOD)
    p.poly([(x, y, 0.70) for x, y in ring], M_WOOD)


_PITCH = {"wall_tent": _wall_tent, "wedge_tent": _wedge_tent,
          "wagon": _wagon, "brush_shelter": _brush_shelter}


# ------------------------------------------------------------------ the layouts

def _layout(params: CampParams) -> list:
    """Every item as `(kind, x, y, rot_deg)`: the pitches, then the front-band kit.

    A pitch's frame has its front at y = 0 facing -y; `rot_deg` turns it about z.
    Front-band items are dealt into the gaps between pitches, front to the camp's
    front, in the order fire, wood, baggage, round-robin until each count is spent.
    """
    pitches = params.pitches()
    items, gaps = [], []
    if params.arrangement == "row":
        x = PITCH_GAP_M
        y0 = FRONT_BAND_M
        for i, (kind, w, _d) in enumerate(pitches):
            cx = x + w / 2.0
            rot = 4.0 * _jitter(i, 1)
            if kind == "wagon":
                items.append((kind, x, y0 + WAGON_TRACK_M / 2.0, 0.0))
            else:
                items.append((kind, cx, y0 + 0.15 * _jitter(i, 2), rot))
            gaps.append(x - PITCH_GAP_M / 2.0)
            x += w + PITCH_GAP_M
        gaps.append(x - PITCH_GAP_M / 2.0)
        spots = [(gx + 0.6 * _jitter(i, 3), FRONT_BAND_M * 0.45 + 0.25 * _jitter(i, 4))
                 for i, gx in enumerate(gaps)]
        spots += [(cx, FRONT_BAND_M * 0.5) for _k, cx, _y, _r in items]
    elif params.arrangement == "ring":
        cu, cv = params.length_m / 2.0, params.depth_m / 2.0
        rr = params.ring_radius()
        n = max(1, len(pitches))
        for i, (kind, w, _d) in enumerate(pitches):
            a = 2 * math.pi * i / n - math.pi / 2.0
            ux, uy = math.cos(a), math.sin(a)
            # the frame's -y (its front) points at the centre
            rot = math.degrees(a) - 90.0
            if kind == "wagon":
                tx, ty = -uy, ux
                items.append((kind, cu + ux * rr - tx * w / 2.0, cv + uy * rr - ty * w / 2.0,
                              rot + 90.0))
            else:
                items.append((kind, cu + ux * rr, cv + uy * rr, rot))
        spots = [(cu, cv)] + [
            (cu + 0.55 * rr * math.cos(2 * math.pi * (i + 0.5) / n - math.pi / 2.0),
             cv + 0.55 * rr * math.sin(2 * math.pi * (i + 0.5) / n - math.pi / 2.0))
            for i in range(n)]
    else:
        cells = params.scatter_cells()
        for i, (kind, w, _d) in enumerate(pitches):
            cu, cv = cells[i]
            cv += FRONT_BAND_M
            cu += 0.35 * PITCH_GAP_M * _jitter(i, 5)
            rot = 14.0 * _jitter(i, 6)
            if kind == "wagon":
                items.append((kind, cu - w / 2.0, cv + WAGON_TRACK_M / 2.0, rot))
            else:
                items.append((kind, cu, cv, rot))
        spots = [(cells[i][0] + 0.8 * _jitter(i, 3), cells[i][1] + FRONT_BAND_M * 0.45)
                 for i in range(len(pitches))]
        spots += [(c[0] + 0.5 * _jitter(i, 4) + 1.4, c[1] + FRONT_BAND_M * 0.4)
                  for i, c in enumerate(cells)]

    kit = []
    counts = {"fire_ring": params.fire_rings, "woodpile": params.woodpiles,
              "baggage": params.baggage_heaps}
    while any(counts.values()):
        for kind in ("fire_ring", "woodpile", "baggage"):
            if counts[kind]:
                kit.append(kind)
                counts[kind] -= 1
    # spread the kit evenly over the spots rather than packing it at one end
    if kit and spots:
        step = len(spots) / len(kit)
        for i, kind in enumerate(kit):
            sx, sy = spots[int(i * step) % len(spots)]
            off = 0.0 if kind == "fire_ring" else (0.9 if kind == "woodpile" else -0.9)
            items.append((kind, sx + off * (1 if i % 2 else -1) * 0.5, sy,
                          20.0 * _jitter(i, 10)))
    return items


def build(params: CampParams, name: str):
    """Build the camp. Returns a Blender object at the local origin; z = 0 is the
    ground under the origin."""
    params.validate()
    b = MeshBuilder(name)
    # Least-confident wins over the attributes that say what the camp WAS.
    conf = params.worst_conf("tents", "tent_kind", "arrangement")
    kit_conf = params.worst_conf("wagons", "fire_rings", "baggage_heaps")
    builders = dict(_PITCH, fire_ring=_fire_ring, woodpile=_woodpile, baggage=_baggage)
    # `_layout` works with the camp's front at y = 0. docs/GLB-CONTRACT.md puts a
    # structure's front on its +y face (north at rotation_deg 0), so the whole layout
    # is turned 180 degrees about the footprint's centre — a rotation, not a mirror,
    # so no tent is built inside out.
    L, D = params.length_m, params.depth_m
    for kind, x, y, rot in _layout(params):
        c = conf if kind.endswith("_tent") else kit_conf
        builders[kind](_Placed(b, L - x, D - y, rot + 180.0, c))

    wood_r = materials.SUBSTRATES["hewn_log"].roughness
    mats = [
        simple_material("canvas", CANVAS_RGBA[params.canvas_condition], roughness=0.94),
        simple_material("wood", WOOD_RGBA, roughness=wood_r),
        simple_material("dark", DARK_RGBA, roughness=0.95),
        simple_material("stone", STONE_RGBA, roughness=0.97),
        simple_material("brush", BRUSH_RGBA, roughness=0.98),
    ]
    return b.to_object(mats)
