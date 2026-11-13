"""monument — a bronze group on a granite pedestal, in pure Python (T-3567).

See `monument_params` for the masses and the record for every reading. Like the K12, K16
and haystack archetypes this module writes its glTF itself with no Blender, and
`generators/monument_emit.py` calls `glb()` for each record; `generators/mesh_inputs.py`
hashes this file and that one into each asset's freshness record. It is not in
`generators/emit.py` for the reason `haystack.py` gives: registering an archetype there
re-stales every Blender mesh in the town.

## The pedestal

Granite masses, read off the Barnes-Crosby view (ICHi-19208, square-on from the 18th
Street walk) and J. W. Taylor's three-quarter view of 1893: the stage base, its top
washed in; the plinth with a projecting fillet; the die, carrying a bronze panel on each
face it is asked for; the cap, a cove out to a fillet and a wash in; then the cast bronze
rock. One granite material and one bronze one: two draw calls.

## The group (Rohl-Smith, 1893)

Five figures, built as the sculptor posed them and no more finely than a visitor on the
walk 5-15 m off can read them: each figure is joined from tapered limbs and balls, its
pose taken from the two photographs (`FIGURES` below, in metres off the rock's centre,
x along the front to the right as the street sees it, y back from the front, z up, at
the photographs' scale of about 2.2 m from the rock to the raised hands). The group is
scaled as a whole to the record's `group_h_m` less the rock. From the left: the warrior
with the tomahawk raised; Margaret Helm, staggering in her long skirt; Black Partridge
behind her, one hand raised against the blow, the musket in the other; the post surgeon
lying across the rock under them; the child at the right front reaching out. The faces,
the dress's folds, the feathers' number and the panels' reliefs are not modelled
(the record's liberty says so); the rear, which no photograph used here shows, is the
same masses seen from behind.
"""

from __future__ import annotations

import json
import math
import random
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from archetypes.monument_params import MonumentParams  # noqa: E402

GENERATOR = "chicago-4d generators/archetypes/monument.py (T-3567)"

M_GRANITE, M_BRONZE = 0, 1
# Name, linear base colour, roughness. The granite is the photographs' mid grey (the
# 1893 print shows it pale and fresh, the c. 1900 one a little darker); the bronze a dark
# brown patina, unpolished (no metal response: nothing in this renderer reflects).
MATERIALS = [
    ("monument_granite", (0.205, 0.200, 0.190, 1.0), 0.78),
    ("monument_bronze", (0.080, 0.066, 0.046, 1.0), 0.55),
]

LIMB_SIDES = 8
BALL_RINGS = 5

# The poses, off the ICHi-19208 front (about 135 px a metre at the group) and checked on
# Taylor's 1893 three-quarter view. Each part: ("limb", a, b, ra, rb) a tapered round
# member; ("ball", c, r); ("ell", c, (rx, ry, rz)); ("cone", top, bottom, r_top, r_bottom).
FIGURES = {
    "warrior": [
        ("ball", (-0.40, 0.05, 1.70), 0.115),
        ("limb", (-0.45, 0.05, 1.52), (-0.41, 0.05, 1.63), 0.06, 0.055),
        ("limb", (-0.64, 0.05, 0.98), (-0.48, 0.05, 1.48), 0.13, 0.17),
        ("ball", (-0.62, 0.05, 0.97), 0.14),
        ("cone", (-0.62, 0.02, 1.02), (-0.62, -0.02, 0.76), 0.145, 0.17),
        # the right arm raised with the tomahawk
        ("ball", (-0.45, 0.05, 1.50), 0.075),
        ("limb", (-0.45, 0.05, 1.50), (-0.60, 0.00, 1.82), 0.065, 0.05),
        ("ball", (-0.60, 0.00, 1.82), 0.05),
        ("limb", (-0.60, 0.00, 1.82), (-0.56, 0.00, 2.04), 0.05, 0.04),
        ("ball", (-0.56, 0.00, 2.04), 0.05),
        ("limb", (-0.56, 0.00, 1.97), (-0.60, 0.00, 2.32), 0.018, 0.016),
        ("ell", (-0.53, 0.00, 2.27), (0.075, 0.015, 0.04)),
        # the left arm thrown back and out
        ("ball", (-0.68, 0.05, 1.47), 0.075),
        ("limb", (-0.68, 0.05, 1.47), (-0.86, 0.00, 1.22), 0.065, 0.05),
        ("ball", (-0.86, 0.00, 1.22), 0.05),
        ("limb", (-0.86, 0.00, 1.22), (-1.00, -0.05, 1.05), 0.05, 0.04),
        ("ball", (-1.00, -0.05, 1.05), 0.05),
        # the lunge: the left leg forward, the right braced back
        ("limb", (-0.68, 0.05, 0.92), (-0.82, -0.05, 0.50), 0.095, 0.065),
        ("ball", (-0.82, -0.05, 0.50), 0.065),
        ("limb", (-0.82, -0.05, 0.50), (-0.95, -0.10, 0.07), 0.065, 0.045),
        ("ell", (-0.97, -0.14, 0.04), (0.06, 0.11, 0.035)),
        ("limb", (-0.56, 0.08, 0.92), (-0.42, 0.15, 0.50), 0.095, 0.065),
        ("ball", (-0.42, 0.15, 0.50), 0.065),
        ("limb", (-0.42, 0.15, 0.50), (-0.32, 0.20, 0.07), 0.065, 0.045),
        ("ell", (-0.30, 0.16, 0.04), (0.06, 0.11, 0.035)),
    ],
    "helm": [
        ("ball", (0.12, -0.15, 1.58), 0.105),
        ("ball", (0.09, -0.08, 1.64), 0.07),
        ("limb", (0.08, -0.15, 1.42), (0.11, -0.15, 1.52), 0.05, 0.045),
        ("limb", (0.02, -0.12, 1.04), (0.08, -0.15, 1.41), 0.12, 0.14),
        ("cone", (0.02, -0.12, 1.06), (-0.04, -0.15, 0.03), 0.16, 0.40),
        # one arm out toward the warrior's, the other back to Black Partridge
        ("ball", (-0.08, -0.15, 1.41), 0.06),
        ("limb", (-0.08, -0.15, 1.41), (-0.25, -0.20, 1.27), 0.055, 0.045),
        ("ball", (-0.25, -0.20, 1.27), 0.045),
        ("limb", (-0.25, -0.20, 1.27), (-0.38, -0.15, 1.22), 0.045, 0.035),
        ("ball", (0.16, -0.12, 1.41), 0.06),
        ("limb", (0.16, -0.12, 1.41), (0.30, -0.05, 1.30), 0.055, 0.045),
        ("ball", (0.30, -0.05, 1.30), 0.045),
        ("limb", (0.30, -0.05, 1.30), (0.38, 0.05, 1.35), 0.045, 0.035),
    ],
    "black_partridge": [
        ("ball", (0.44, 0.35, 2.02), 0.12),
        ("limb", (0.46, 0.38, 2.10), (0.62, 0.40, 2.32), 0.03, 0.006),
        ("limb", (0.50, 0.40, 2.05), (0.75, 0.45, 1.85), 0.03, 0.006),
        ("limb", (0.47, 0.35, 1.84), (0.45, 0.35, 1.95), 0.065, 0.06),
        ("limb", (0.52, 0.35, 1.15), (0.48, 0.35, 1.80), 0.15, 0.19),
        ("ball", (0.53, 0.35, 1.12), 0.16),
        ("cone", (0.53, 0.33, 1.15), (0.53, 0.30, 0.82), 0.165, 0.20),
        # the right hand raised against the blow, over Mrs. Helm
        ("ball", (0.33, 0.33, 1.80), 0.085),
        ("limb", (0.33, 0.33, 1.80), (0.05, 0.25, 1.98), 0.07, 0.055),
        ("ball", (0.05, 0.25, 1.98), 0.055),
        ("limb", (0.05, 0.25, 1.98), (-0.33, 0.20, 2.13), 0.055, 0.045),
        ("ell", (-0.37, 0.19, 2.16), (0.05, 0.03, 0.08)),
        # the left arm round her, the musket slanting down to the right
        ("ball", (0.68, 0.35, 1.78), 0.085),
        ("limb", (0.68, 0.35, 1.78), (0.75, 0.25, 1.45), 0.07, 0.055),
        ("ball", (0.75, 0.25, 1.45), 0.055),
        ("limb", (0.75, 0.25, 1.45), (0.60, 0.10, 1.32), 0.055, 0.045),
        ("limb", (0.35, 0.25, 1.62), (0.98, 0.25, 0.95), 0.025, 0.025),
        ("ell", (0.93, 0.25, 1.00), (0.08, 0.035, 0.05)),
        # the stride
        ("limb", (0.45, 0.38, 1.08), (0.42, 0.40, 0.58), 0.10, 0.07),
        ("ball", (0.42, 0.40, 0.58), 0.07),
        ("limb", (0.42, 0.40, 0.58), (0.40, 0.42, 0.07), 0.07, 0.05),
        ("ell", (0.40, 0.37, 0.04), (0.065, 0.12, 0.035)),
        ("limb", (0.62, 0.36, 1.08), (0.82, 0.30, 0.60), 0.10, 0.07),
        ("ball", (0.82, 0.30, 0.60), 0.07),
        ("limb", (0.82, 0.30, 0.60), (1.00, 0.25, 0.07), 0.07, 0.05),
        ("ell", (1.03, 0.20, 0.04), (0.065, 0.12, 0.035)),
    ],
    "surgeon": [
        ("limb", (-0.30, 0.10, 0.18), (0.25, 0.15, 0.25), 0.13, 0.15),
        ("ball", (-0.45, 0.05, 0.22), 0.10),
        ("ball", (-0.20, 0.05, 0.30), 0.06),
        ("limb", (-0.20, 0.05, 0.30), (-0.15, -0.05, 0.55), 0.055, 0.045),
        ("ball", (-0.15, -0.05, 0.55), 0.045),
        ("limb", (-0.15, -0.05, 0.55), (-0.05, -0.10, 0.68), 0.045, 0.035),
        ("limb", (0.30, 0.18, 0.20), (0.65, 0.15, 0.14), 0.09, 0.065),
        ("limb", (0.65, 0.15, 0.14), (0.95, 0.05, 0.10), 0.065, 0.045),
        ("limb", (0.30, 0.12, 0.18), (0.60, 0.00, 0.30), 0.09, 0.065),
        ("ball", (0.60, 0.00, 0.30), 0.065),
        ("limb", (0.60, 0.00, 0.30), (0.85, -0.05, 0.08), 0.065, 0.045),
    ],
    "child": [
        ("ball", (0.97, -0.35, 0.62), 0.085),
        ("limb", (0.92, -0.33, 0.30), (0.95, -0.35, 0.53), 0.08, 0.09),
        ("cone", (0.92, -0.33, 0.38), (0.90, -0.33, 0.04), 0.09, 0.20),
        ("limb", (1.00, -0.35, 0.50), (1.12, -0.38, 0.58), 0.035, 0.03),
        ("limb", (1.12, -0.38, 0.58), (1.25, -0.40, 0.63), 0.03, 0.025),
        ("limb", (0.98, -0.30, 0.50), (1.10, -0.42, 0.52), 0.035, 0.03),
        ("limb", (1.10, -0.42, 0.52), (1.22, -0.45, 0.55), 0.03, 0.025),
    ],
}
#: Rock to the highest raised hand in the poses above, which `group_h_m` less the rock scales.
POSE_TOP_M = 2.20


def _sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def _norm(v):
    m = math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2]) or 1.0
    return (v[0] / m, v[1] / m, v[2] / m)


class _Mesh:
    """Indexed vertices per material, in the archetype's frame (x east, y north, z up)."""

    def __init__(self):
        self.parts = [{"pos": [], "nrm": [], "conf": [], "idx": []} for _ in MATERIALS]

    def vert(self, mat, p, n, conf) -> int:
        part = self.parts[mat]
        part["pos"].append(p)
        part["nrm"].append(n)
        part["conf"].append(conf)
        return len(part["pos"]) - 1

    def tri(self, mat, a, b, c) -> None:
        self.parts[mat]["idx"] += [a, b, c]

    def face(self, mat, pts, conf) -> None:
        """A flat convex polygon, wound counter-clockwise seen from outside."""
        n = _norm(_cross(_sub(pts[1], pts[0]), _sub(pts[2], pts[0])))
        ix = [self.vert(mat, p, n, conf) for p in pts]
        for k in range(1, len(ix) - 1):
            self.tri(mat, ix[0], ix[k], ix[k + 1])

    @property
    def triangles(self) -> int:
        n = 0
        for p in self.parts:
            n += len(p["idx"]) // 3
        return n


def _ring(cx, cy, w, d):
    """A rectangle's corners anticlockwise from the south-west, round (cx, cy)."""
    return [(cx - w / 2, cy - d / 2), (cx + w / 2, cy - d / 2),
            (cx + w / 2, cy + d / 2), (cx - w / 2, cy + d / 2)]


def _band(m, mat, lo, z0, hi, z1, conf, top=False):
    """The four sides between rectangle `lo` at z0 and rectangle `hi` at z1 (a box when
    they are the same, a wash or a cove when not), and its top when asked."""
    for k in range(4):
        a, b = lo[k], lo[(k + 1) % 4]
        c, d = hi[(k + 1) % 4], hi[k]
        m.face(mat, [(a[0], a[1], z0), (b[0], b[1], z0), (c[0], c[1], z1), (d[0], d[1], z1)], conf)
    if top:
        m.face(mat, [(p[0], p[1], z1) for p in hi], conf)


def _pedestal(m: _Mesh, p: MonumentParams, cx: float, cy: float) -> float:
    conf = p.worst_conf("base_w_m", "base_d_m", "base_h_m", "plinth_w_m", "die_w_m", "die_h_m")
    z = 0.0
    # the stage base, its top washed in to a ledge round the plinth
    base = _ring(cx, cy, p.base_w_m, p.base_d_m)
    ledge = _ring(cx, cy, min(p.base_w_m, p.plinth_w_m + 0.24), min(p.base_d_m, p.plinth_d_m + 0.24))
    _band(m, M_GRANITE, base, z - 0.15, base, p.base_h_m - p.base_wash_m, conf)
    _band(m, M_GRANITE, base, p.base_h_m - p.base_wash_m, ledge, p.base_h_m, conf, top=True)
    z = p.base_h_m
    # the plinth, and the fillet projecting at its top
    plinth = _ring(cx, cy, p.plinth_w_m, p.plinth_d_m)
    fil = 0.10
    _band(m, M_GRANITE, plinth, z, plinth, z + p.plinth_h_m - fil, conf)
    fillet = _ring(cx, cy, p.plinth_w_m + 0.06, p.plinth_d_m + 0.06)
    _band(m, M_GRANITE, fillet, z + p.plinth_h_m - fil, fillet, z + p.plinth_h_m - 0.04, conf)
    die = _ring(cx, cy, p.die_w_m, p.die_d_m)
    _band(m, M_GRANITE, fillet, z + p.plinth_h_m - 0.04, die, z + p.plinth_h_m, conf, top=True)
    z += p.plinth_h_m
    # the die
    _band(m, M_GRANITE, die, z, die, z + p.die_h_m, conf)
    die_z = z
    z += p.die_h_m
    # the cap: a cove out, a fillet, a wash in
    o = p.cap_overhang_m
    cove = _ring(cx, cy, p.die_w_m + 2 * o, p.die_d_m + 2 * o)
    wash = _ring(cx, cy, p.die_w_m + o * 0.6, p.die_d_m + o * 0.6)
    h = p.cap_h_m
    _band(m, M_GRANITE, die, z, cove, z + h * 0.40, conf)
    _band(m, M_GRANITE, cove, z + h * 0.40, cove, z + h * 0.75, conf)
    _band(m, M_GRANITE, cove, z + h * 0.75, wash, z + h, conf, top=True)
    z += h
    _panels(m, p, cx, cy, die_z)
    return z


def _panels(m: _Mesh, p: MonumentParams, cx: float, cy: float, die_z: float) -> None:
    """The bronze panels, 2 cm proud of the die: 0.30-0.85 of its height, as ICHi-19208
    shows the front one (y 548-650 px on a die of 520-705), 0.82 of the face's width."""
    if not p.panels:
        return
    conf = p.worst_conf("panels")
    z0, z1 = die_z + p.die_h_m * 0.30, die_z + p.die_h_m * 0.85
    t = 0.02
    faces = ["s", "n", "e", "w"][: {1: 1, 2: 2, 4: 4}[p.panels]]
    for f in faces:
        if f in ("s", "n"):
            w = p.die_w_m * 0.82
            y = cy - p.die_d_m / 2 if f == "s" else cy + p.die_d_m / 2
            lo = _ring(cx, y + (-t / 2 if f == "s" else t / 2), w, t)
        else:
            w = p.die_d_m * 0.75
            x = cx + p.die_w_m / 2 if f == "e" else cx - p.die_w_m / 2
            lo = _ring(x + (t / 2 if f == "e" else -t / 2), cy, t, w)
        _band(m, M_BRONZE, lo, z0, lo, z1, conf)


def _rock(m: _Mesh, p: MonumentParams, cx: float, cy: float, z0: float) -> None:
    """The cast ground the group stands on: a lumpy field over the cap's top, highest
    under the figures, skirted down to the granite at its edge."""
    conf = p.worst_conf("rock_h_m")
    rng = random.Random(p.seed)
    nx, ny = 16, 12
    w, d = p.die_w_m + p.cap_overhang_m * 0.4, p.die_d_m + p.cap_overhang_m * 0.4
    lumps = [(rng.uniform(-0.45, 0.45) * w, rng.uniform(-0.4, 0.4) * d, rng.uniform(0.15, 0.35),
              rng.uniform(0.25, 1.0)) for _ in range(9)]

    def height(fx, fy):
        ex = 1.0 - (2 * abs(fx) / w) ** 4
        ey = 1.0 - (2 * abs(fy) / d) ** 4
        edge = max(0.0, min(ex, ey))
        bump = math.fsum(a * math.exp(-((fx - lx) ** 2 + (fy - ly) ** 2) / (2 * r * r)) for lx, ly, r, a in lumps)
        return p.rock_h_m * (0.25 + 0.75 * edge * (0.55 + 0.45 * min(1.0, bump)))

    grid = {}
    for j in range(ny + 1):
        for i in range(nx + 1):
            fx, fy = (i / nx - 0.5) * w, (j / ny - 0.5) * d
            grid[i, j] = (cx + fx, cy + fy, z0 + height(fx, fy))
    for j in range(ny):
        for i in range(nx):
            a, b, c, e = grid[i, j], grid[i + 1, j], grid[i + 1, j + 1], grid[i, j + 1]
            m.face(M_BRONZE, [a, b, c], conf)
            m.face(M_BRONZE, [a, c, e], conf)
    # the skirt: the field's edge straight down to the cap
    edge = ([grid[i, 0] for i in range(nx + 1)] + [grid[nx, j] for j in range(1, ny + 1)]
            + [grid[i, ny] for i in range(nx - 1, -1, -1)] + [grid[0, j] for j in range(ny - 1, 0, -1)])
    for k in range(len(edge)):
        a, b = edge[k], edge[(k + 1) % len(edge)]
        m.face(M_BRONZE, [(a[0], a[1], z0), (b[0], b[1], z0), b, a], conf)


def _frame(axis):
    axis = _norm(axis)
    helper = (0.0, 0.0, 1.0) if abs(axis[2]) < 0.9 else (1.0, 0.0, 0.0)
    u = _norm(_cross(axis, helper))
    v = _cross(axis, u)
    return u, v


def _limb(m, a, b, ra, rb, conf, sides=LIMB_SIDES):
    axis = _sub(b, a)
    u, v = _frame(axis)
    ring_a, ring_b = [], []
    for k in range(sides):
        t = 2 * math.pi * k / sides
        n = tuple(math.cos(t) * u[i] + math.sin(t) * v[i] for i in range(3))
        ring_a.append(m.vert(M_BRONZE, tuple(a[i] + ra * n[i] for i in range(3)), n, conf))
        ring_b.append(m.vert(M_BRONZE, tuple(b[i] + rb * n[i] for i in range(3)), n, conf))
    for k in range(sides):
        k2 = (k + 1) % sides
        m.tri(M_BRONZE, ring_a[k], ring_a[k2], ring_b[k2])
        m.tri(M_BRONZE, ring_a[k], ring_b[k2], ring_b[k])
    # close the ends, so a thin member seen end-on is not hollow
    ca = m.vert(M_BRONZE, a, _norm(tuple(-x for x in axis)), conf)
    cb = m.vert(M_BRONZE, b, _norm(axis), conf)
    for k in range(sides):
        k2 = (k + 1) % sides
        m.tri(M_BRONZE, ca, ring_a[k2], ring_a[k])
        m.tri(M_BRONZE, cb, ring_b[k], ring_b[k2])


def _ell(m, c, radii, conf, sides=LIMB_SIDES, rings=BALL_RINGS):
    rx, ry, rz = radii
    rows = []
    for j in range(rings + 1):
        ph = math.pi * j / rings - math.pi / 2
        row = []
        for k in range(sides):
            t = 2 * math.pi * k / sides
            d = (math.cos(ph) * math.cos(t), math.cos(ph) * math.sin(t), math.sin(ph))
            n = _norm((d[0] / rx, d[1] / ry, d[2] / rz))
            row.append(m.vert(M_BRONZE, (c[0] + rx * d[0], c[1] + ry * d[1], c[2] + rz * d[2]), n, conf))
        rows.append(row)
    for j in range(rings):
        for k in range(sides):
            k2 = (k + 1) % sides
            a, b, cc, d = rows[j][k], rows[j][k2], rows[j + 1][k2], rows[j + 1][k]
            m.tri(M_BRONZE, a, b, cc)
            m.tri(M_BRONZE, a, cc, d)


def _cone(m, top, bottom, rt, rb, conf, sides=12):
    """A skirt: open at the top, closed at the hem."""
    _limb(m, bottom, top, rb, rt, conf, sides)


def _group(m: _Mesh, p: MonumentParams, cx: float, cy: float, z0: float) -> None:
    conf = p.worst_conf("group_h_m")
    k = (p.group_h_m - p.rock_h_m) / POSE_TOP_M
    # the poses' y runs back from the front, which is the archetype's +y (north)
    place = lambda q: (cx + k * q[0], cy + k * q[1], z0 + k * q[2])  # noqa: E731
    for name in ("warrior", "helm", "black_partridge", "surgeon", "child"):
        for part in FIGURES[name]:
            kind = part[0]
            if kind == "limb":
                _limb(m, place(part[1]), place(part[2]), k * part[3], k * part[4], conf)
            elif kind == "ball":
                r = k * part[2]
                _ell(m, place(part[1]), (r, r, r), conf)
            elif kind == "ell":
                _ell(m, place(part[1]), tuple(k * r for r in part[2]), conf)
            elif kind == "cone":
                _cone(m, place(part[1]), place(part[2]), k * part[3], k * part[4], conf)


def mesh(params: MonumentParams) -> _Mesh:
    """The monument, its base centred in the footprint rectangle, grade at z 0."""
    params.validate()
    m = _Mesh()
    cx, cy = params.base_w_m / 2, params.base_d_m / 2
    top = _pedestal(m, params, cx, cy)
    _rock(m, params, cx, cy, top)
    _group(m, params, cx, cy, top + params.rock_h_m * 0.55)
    return m


def _pad(blob: bytes, fill: bytes = b"\x00") -> bytes:
    return blob + fill * ((4 - len(blob) % 4) % 4)


def glb(params: MonumentParams, structure_id: str, phase_id: str) -> bytes:
    """The structure's GLB. glTF is y-up: the archetype's (x, y, z) is written as
    (x, z, -y), a rotation, so no face turns inside out (docs/GLB-CONTRACT.md)."""
    m = mesh(params)
    to_gl = lambda p: (round(p[0], 4), round(p[2], 4), round(-p[1], 4))  # noqa: E731
    bin_ = bytearray()
    views, accessors, prims = [], [], []

    def view(blob: bytes, target: int) -> int:
        nonlocal bin_
        off = len(bin_)
        bin_ += _pad(blob)
        views.append({"buffer": 0, "byteOffset": off, "byteLength": len(blob), "target": target})
        return len(views) - 1

    def accessor(values, ctype, typ, comps, target, minmax=False) -> int:
        flat = [x for v in values for x in (v if comps > 1 else (v,))]
        fmt = {5126: "f", 5123: "H", 5125: "I"}[ctype]
        acc = {"bufferView": view(struct.pack(f"<{len(flat)}{fmt}", *flat), target),
               "componentType": ctype, "count": len(values), "type": typ}
        if minmax:
            acc["min"] = [struct.unpack("<f", struct.pack("<f", min(v[k] for v in values)))[0]
                          for k in range(comps)]
            acc["max"] = [struct.unpack("<f", struct.pack("<f", max(v[k] for v in values)))[0]
                          for k in range(comps)]
        accessors.append(acc)
        return len(accessors) - 1

    used = []
    for mi, part in enumerate(m.parts):
        if not part["idx"]:
            continue
        pos = [to_gl(p) for p in part["pos"]]
        nrm = [(round(n[0], 4), round(n[2], 4), round(-n[1], 4)) for n in part["nrm"]]
        attrs = {"POSITION": accessor(pos, 5126, "VEC3", 3, 34962, True),
                 "NORMAL": accessor(nrm, 5126, "VEC3", 3, 34962),
                 "_CONFIDENCE": accessor(part["conf"], 5126, "SCALAR", 1, 34962)}
        used.append(mi)
        idx = part["idx"]
        prims.append({"attributes": attrs,
                      "indices": accessor(idx, 5123 if len(pos) < 65536 else 5125, "SCALAR", 1, 34963),
                      "material": len(used) - 1})
    mats = []
    for mi in used:
        name, rgba, r = MATERIALS[mi]
        mats.append({"name": name, "pbrMetallicRoughness": {
            "baseColorFactor": [round(x, 4) for x in rgba], "metallicFactor": 0.0,
            "roughnessFactor": round(r, 4)}})
    name = f"{structure_id}__{phase_id}"
    gltf = {
        "asset": {"version": "2.0", "generator": GENERATOR},
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": [{"name": name, "mesh": 0,
                   "extras": {"structure_id": structure_id, "phase_id": phase_id}}],
        "meshes": [{"name": name, "primitives": prims}],
        "materials": mats,
        "accessors": accessors,
        "bufferViews": views,
        "buffers": [{"byteLength": len(bin_)}],
    }
    js = _pad(json.dumps(gltf, separators=(",", ":"), sort_keys=True).encode(), b" ")
    body = bytes(bin_)
    total = 12 + 8 + len(js) + 8 + len(body)
    return (struct.pack("<III", 0x46546C67, 2, total) + struct.pack("<I4s", len(js), b"JSON") + js
            + struct.pack("<I4s", len(body), b"BIN\x00") + body)
