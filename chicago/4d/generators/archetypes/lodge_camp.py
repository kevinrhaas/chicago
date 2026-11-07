"""lodge_camp — one group of the Potawatomi camp of August 1812 (T-3342).

See `lodge_camp_params` for the evidence, the forms and every dimension. This module lays
the group out and builds it, and writes its glTF itself in pure Python with no Blender
(the K12/K16/haystack route, T-2266): `generators/lodge_camp_emit.py` calls `glb()` for
each record, and `generators/mesh_inputs.py` hashes this file and that one into the
asset's freshness record, so registering it costs no other mesh a rebake.

## How a group is laid out

A group is a cluster of families round a shared work yard, which is how the narrators
the params cite put a camp together: lodges round the place the cooking is done, the
drying racks and the mortar by it, the stores on scaffolds behind the lodges, the canoes
drawn up at the water's edge and the horses picketed apart. The layout is this project's
(L-1812-potawatomi-camp-2515):

1. one yard to each arbor, strung along the group's long axis, each with its hearth just
   outside the arbor's open side;
2. the dwellings, largest first, each the best of many seeded tries at a spot 4-11 m
   from a yard, with its door turned to that yard (a door on the yard is a door on the
   fire and the work) and a gap a walker can pass through kept round it;
3. racks, the mortar and the woodpile by the yards; scaffolds and hide frames behind
   and between the lodges; extra hearths by the lodges; canoes along the named edge;
   tether stakes and pack saddles in the open.

Every choice comes off one seeded `random.Random` taken from the record's id, so two
bakes of a record make the same bytes and no two groups are laid out alike.

## Surfaces

The mats, the bark and the arbor's boughs are three textured materials,
`camp_cattail_mat`, `camp_elm_bark` and `camp_boughs`, whose maps are T-3342's library
(assets/textures/camp_1812_pbr/), bound by name in the renderer (camp-surfaces.js,
docs/GLB-CONTRACT.md § Camp coverings). Their UVs are written here in tiles of each
map's span (the `_UV` channel, docs/GLB-CONTRACT.md § Camp coverings), every mat and
sheet with its own offset into the tile so no two repeat in step, and each piece carries its own `_TONE` so a lodge reads as mats of different
seasons and not as one printed cloth. Poles, hides, ash and the rest are plain colours.
"""

from __future__ import annotations

import json
import math
import random
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from archetypes.lodge_camp_params import (  # noqa: E402
    ARBOR, BARK_HOUSE, BARK_SPAN_M, BOUGH_SPAN_M, CANOE_L_M, COURSE_M, GAP_M, LODGE_SIZES,
    LONG_LODGE, MARGIN_M, MAT_LEN_M, MAT_SPAN_M, RACK_L_M, SCAFFOLD, LodgeCampParams,
    ParamError,
)

GENERATOR = "chicago-4d generators/archetypes/lodge_camp.py (T-3342)"


def _seqsum(xs):
    """Add left to right, one term at a time: the same last bit on every CPython (T-2363).

    3.12 made the built-in `sum()` compensate floats and 3.11 does not, so a pure-Python
    emitter that called it built different bytes on the two (prairie_draft's _seqsum).
    """
    total = 0.0
    for x in xs:
        total += x
    return total

(M_MAT, M_BARK, M_BOUGH, M_POLE, M_DARK, M_ASH, M_CHAR, M_HIDE, M_KETTLE, M_MEAT,
 M_FISH, M_BIRCH, M_WOOD, M_EMBER, M_CORD) = range(15)

# name, base colour (linear), roughness, metallic, emissive. The three coverings carry
# the mean of their map as the colour a page without the map falls back to; the binder
# turns it white when the map arrives (camp-surfaces.js).
MATERIALS = [
    ("camp_cattail_mat", (0.300, 0.255, 0.165, 1.0), 0.88, 0.0, None),
    ("camp_elm_bark", (0.205, 0.175, 0.140, 1.0), 0.93, 0.0, None),
    ("camp_boughs", (0.075, 0.085, 0.035, 1.0), 0.90, 0.0, None),
    # Peeled and barked saplings, greyed: the frames, racks and stakes.
    ("camp_pole", (0.150, 0.125, 0.095, 1.0), 0.92, 0.0, None),
    # The inside of a lodge seen through its door.
    ("camp_dark", (0.040, 0.034, 0.028, 1.0), 0.98, 0.0, None),
    ("camp_ash", (0.330, 0.320, 0.300, 1.0), 0.98, 0.0, None),
    ("camp_char", (0.050, 0.042, 0.036, 1.0), 0.97, 0.0, None),
    # Rawhide and smoked skin: doors, bundles, the hide on its frame.
    ("camp_hide", (0.300, 0.215, 0.140, 1.0), 0.82, 0.0, None),
    # A trade kettle of brass, dulled by the fire.
    ("camp_kettle", (0.380, 0.270, 0.120, 1.0), 0.55, 0.65, None),
    ("camp_meat", (0.105, 0.042, 0.028, 1.0), 0.72, 0.0, None),
    ("camp_fish", (0.420, 0.360, 0.270, 1.0), 0.70, 0.0, None),
    # A bark canoe's skin, the brown inner face of the bark turned out as these canoes
    # were usually built, the seams pitched dark.
    ("camp_birch", (0.330, 0.240, 0.150, 1.0), 0.80, 0.0, None),
    # Heavier wood: a dugout, a mortar, firewood.
    ("camp_wood", (0.220, 0.170, 0.120, 1.0), 0.90, 0.0, None),
    # The coals at the heart of a hearth.
    ("camp_ember", (0.250, 0.060, 0.020, 1.0), 0.90, 0.0, (0.55, 0.16, 0.03)),
    ("camp_cord", (0.180, 0.140, 0.095, 1.0), 0.95, 0.0, None),
]

TAU = 2.0 * math.pi

# The materials the renderer binds a library sheet to by name (camp-surfaces.js).
TEXTURED = (M_MAT, M_BARK, M_BOUGH)


# ------------------------------------------------------------------ the mesh

class _Mesh:
    """Polygons in the group's frame (x along the ground, y across it, z up), each with
    its material, confidence, piece tone and UVs. Fanned into triangles when written."""

    def __init__(self):
        self.polys: list = []

    def add(self, pts, mat, conf, tone=1.0, uvs=None):
        self.polys.append(([tuple(float(c) for c in p) for p in pts], mat, float(conf),
                           float(tone), uvs))


class _Frame:
    """Adds an item's local polygons through a rotation about z and a translation."""

    def __init__(self, m: _Mesh, x: float, y: float, rot_deg: float, conf: float):
        self.m, self.x, self.y, self.conf = m, x, y, conf
        th = math.radians(rot_deg)
        self.c, self.s = math.cos(th), math.sin(th)

    def w(self, p):
        return (self.x + p[0] * self.c - p[1] * self.s, self.y + p[0] * self.s + p[1] * self.c, p[2])

    def poly(self, pts, mat, tone=1.0, uvs=None):
        self.m.add([self.w(p) for p in pts], mat, self.conf, tone, uvs)

    def grid(self, rows, mat, tone=1.0, uvrows=None):
        """A patch from a 2-D list of points (rows of columns), as quads."""
        for i in range(len(rows) - 1):
            for j in range(len(rows[i]) - 1):
                pts = [rows[i][j], rows[i][j + 1], rows[i + 1][j + 1], rows[i + 1][j]]
                uv = None if uvrows is None else [uvrows[i][j], uvrows[i][j + 1],
                                                  uvrows[i + 1][j + 1], uvrows[i + 1][j]]
                self.poly(pts, mat, tone, uv)

    def rod(self, a, b, r, mat, sides=4, tone=1.0):
        """A pole between two points: a prism of `sides` faces, open-ended."""
        d = [b[i] - a[i] for i in range(3)]
        ln = math.sqrt(_seqsum(c * c for c in d)) or 1.0
        d = [c / ln for c in d]
        up = (0.0, 0.0, 1.0) if abs(d[2]) < 0.9 else (1.0, 0.0, 0.0)
        u = (d[1] * up[2] - d[2] * up[1], d[2] * up[0] - d[0] * up[2], d[0] * up[1] - d[1] * up[0])
        un = math.sqrt(_seqsum(c * c for c in u)) or 1.0
        u = [c / un for c in u]
        v = (d[1] * u[2] - d[2] * u[1], d[2] * u[0] - d[0] * u[2], d[0] * u[1] - d[1] * u[0])
        ring = [(math.cos(TAU * k / sides), math.sin(TAU * k / sides)) for k in range(sides)]
        ends = [[tuple(o[i] + r * (cu * u[i] + cv * v[i]) for i in range(3)) for cu, cv in ring]
                for o in (a, b)]
        for k in range(sides):
            j = (k + 1) % sides
            uv = [(k / sides, 0.0), (j / sides, 0.0), (j / sides, ln), (k / sides, ln)]
            self.poly([ends[0][k], ends[0][j], ends[1][j], ends[1][k]], mat, tone, uv)

    def cylinder(self, cx, cy, z0, z1, r, mat, n=8, tone=1.0, top=True, top_mat=None):
        ring = [(cx + r * math.cos(TAU * k / n), cy + r * math.sin(TAU * k / n)) for k in range(n)]
        for k in range(n):
            (xa, ya), (xb, yb) = ring[k], ring[(k + 1) % n]
            self.poly([(xa, ya, z0), (xb, yb, z0), (xb, yb, z1), (xa, ya, z1)], mat, tone,
                      [(k * r, z0), ((k + 1) * r, z0), ((k + 1) * r, z1), (k * r, z1)])
        if top:
            self.poly([(x, y, z1) for x, y in ring], top_mat if top_mat is not None else mat, tone)

    def log(self, a, b, r, mat, sides=6, tone=1.0, caps=True):
        """A log lying between two points, capped."""
        self.rod(a, b, r, mat, sides, tone)
        if caps:
            for o, sgn in ((a, -1), (b, 1)):
                d = [b[i] - a[i] for i in range(3)]
                ln = math.sqrt(_seqsum(c * c for c in d)) or 1.0
                d = [c / ln for c in d]
                up = (0.0, 0.0, 1.0) if abs(d[2]) < 0.9 else (1.0, 0.0, 0.0)
                u = (d[1] * up[2] - d[2] * up[1], d[2] * up[0] - d[0] * up[2], d[0] * up[1] - d[1] * up[0])
                un = math.sqrt(_seqsum(c * c for c in u)) or 1.0
                u = [c / un for c in u]
                v = (d[1] * u[2] - d[2] * u[1], d[2] * u[0] - d[0] * u[2], d[0] * u[1] - d[1] * u[0])
                pts = [tuple(o[i] + r * (math.cos(TAU * k / sides) * u[i] + math.sin(TAU * k / sides) * v[i])
                             for i in range(3)) for k in range(sides)]
                self.poly(pts if sgn > 0 else pts[::-1], mat, tone * 0.8)

    def box(self, x0, y0, z0, x1, y1, z1, mat, tone=1.0):
        f = [[(x0, y0, z1), (x0, y1, z1), (x1, y1, z1), (x1, y0, z1)],
             [(x0, y0, z0), (x0, y0, z1), (x1, y0, z1), (x1, y0, z0)],
             [(x1, y1, z0), (x1, y1, z1), (x0, y1, z1), (x0, y1, z0)],
             [(x0, y1, z0), (x0, y1, z1), (x0, y0, z1), (x0, y0, z0)],
             [(x1, y0, z0), (x1, y0, z1), (x1, y1, z1), (x1, y1, z0)]]
        for pts in f:
            self.poly(pts, mat, tone)


# ------------------------------------------------------------------ the lodges

def _superellipse(theta, p):
    c, s = math.cos(theta), math.sin(theta)
    return (math.copysign(abs(c) ** (2.0 / p), c), math.copysign(abs(s) ** (2.0 / p), s))


class _Dome:
    """The surface of a bent-pole lodge: plan a superellipse of half-axes (a, b) and
    exponent `p`, the wall standing near-upright and rounding over into the crown."""

    def __init__(self, a, b, h, p=2.0, q=2.4, rng=None, ribs=0):
        self.a, self.b, self.h, self.p, self.q = a, b, h, p, q
        # a lodge raised by hand on bent saplings is never true: a few slow swells round
        # it, the crown off-centre, and the covering sagging between the arched poles
        self.wob = [] if rng is None else [(k, rng.uniform(0.015, 0.035) / k ** 0.5, rng.uniform(0, TAU))
                                           for k in (2, 3, 5)]
        self.ribs, self.sag = ribs, (0.035 if ribs else 0.0)
        self.lean = (0.0, 0.0) if rng is None else (rng.uniform(-0.12, 0.12), rng.uniform(-0.12, 0.12))
        # arc length up the profile, on the mean radius, sampled in f = z / h
        n = 80
        self.fs = [i / n for i in range(n + 1)]
        r = (a + b) / 2.0
        self.ss = [0.0]
        for i in range(1, n + 1):
            f0, f1 = self.fs[i - 1], self.fs[i]
            dr = r * (self.scale(f1) - self.scale(f0))
            dz = h * (f1 - f0)
            self.ss.append(self.ss[-1] + math.hypot(dr, dz))

    def scale(self, f):
        return max(0.0, 1.0 - min(f, 1.0) ** self.q) ** (1.0 / self.q)

    def f_at(self, s):
        """The height fraction at arc length s up the profile."""
        ss, fs = self.ss, self.fs
        if s <= 0:
            return 0.0
        for i in range(1, len(ss)):
            if ss[i] >= s:
                t = (s - ss[i - 1]) / max(ss[i] - ss[i - 1], 1e-9)
                return fs[i - 1] + t * (fs[i] - fs[i - 1])
        return 1.0

    def pt(self, theta, f, out=0.0):
        cx, cy = _superellipse(theta, self.p)
        sc = self.scale(f)
        # outward: the plan normal tilted by the profile's slope
        nx, ny = cx / max(self.a, 1e-6), cy / max(self.b, 1e-6)
        nl = math.hypot(nx, ny) or 1.0
        df = 0.01
        dr = (self.scale(min(f + df, 1.0)) - self.scale(max(f - df, 0.0))) * (self.a + self.b) / 2.0
        dz = self.h * (min(f + df, 1.0) - max(f - df, 0.0))
        tl = math.hypot(dr, dz) or 1.0
        horiz, vert = dz / tl, -dr / tl
        wob = 1.0 + _seqsum(a * math.cos(k * theta + ph) for k, a, ph in self.wob)
        if self.ribs:
            # sag midway between ribs, most on the wall's shoulder, none at the foot
            rib = abs(math.sin(self.ribs * theta / 2.0))
            wob -= self.sag * rib ** 2 * math.sin(math.pi * min(f / 0.85, 1.0))
        lx, ly = self.lean[0] * f * f, self.lean[1] * f * f
        return (self.a * sc * cx * wob + lx + out * horiz * nx / nl,
                self.b * sc * cy * wob + ly + out * horiz * ny / nl,
                self.h * f * (1.0 + 0.5 * (wob - 1.0)) + out * vert)

    def perimeter_angles(self, f, n=96):
        """Cumulative perimeter (m) round the ring at height fraction f, by angle."""
        th = [TAU * k / n - math.pi / 2.0 for k in range(n + 1)]
        cum = [0.0]
        for k in range(1, n + 1):
            a, b = self.pt(th[k - 1], f), self.pt(th[k], f)
            cum.append(cum[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
        return th, cum


def _angle_at(th, cum, d):
    """The angle at perimeter distance d round the ring (d may run past one lap)."""
    total = cum[-1]
    lap = math.floor(d / total) if total else 0
    d -= lap * total
    for i in range(1, len(cum)):
        if cum[i] >= d:
            t = (d - cum[i - 1]) / max(cum[i] - cum[i - 1], 1e-9)
            return th[i - 1] + t * (th[i] - th[i - 1]) + lap * TAU
    return th[-1] + lap * TAU


def _covering_course(fr: _Frame, dome: _Dome, rng, s0, s1, out0, mat, span, piece_len,
                     tone_rng, gaps=(), rows=2, bulge=0.035, curl=0.0):
    """One course of the covering between arc lengths s0 and s1 up the profile: pieces
    (mats or bark sheets) of random length round the ring, each its own patch, lapping
    its neighbour, with its own tile offset and tone. `gaps` are perimeter ranges
    (d0, d1) at the course's foot left open (a door)."""
    f0, f1 = dome.f_at(s0), dome.f_at(s1)
    fm = (f0 + f1) / 2.0
    th, cum = dome.perimeter_angles(fm)
    total = cum[-1]
    if total < 0.3:
        return
    start = rng.uniform(0, total)
    # lay pieces until the ring is closed, skipping the gaps (measured from angle -90)
    d = 0.0
    k = 0
    while d < total - 0.05:
        ln = rng.uniform(*piece_len)
        if total - d - ln < piece_len[0] * 0.5:
            ln = total - d
        a, b = d, min(d + ln, total)
        d = b
        k += 1
        segs = [(a, b)]
        for g0, g1 in gaps:
            nxt = []
            for x0, x1 in segs:
                if x1 <= g0 or x0 >= g1:
                    nxt.append((x0, x1))
                else:
                    if x0 < g0:
                        nxt.append((x0, g0))
                    if x1 > g1:
                        nxt.append((g1, x1))
            segs = nxt
        for x0, x1 in segs:
            if x1 - x0 < 0.12:
                continue
            lap = 0.07
            e0, e1 = x0 - lap, x1 + lap
            if gaps:
                for g0, g1 in gaps:
                    if abs(x0 - g1) < 1e-6:
                        e0 = x0
                    if abs(x1 - g0) < 1e-6:
                        e1 = x1
            cols = max(2, int(round((e1 - e0) / 0.42)))
            out = out0 + (0.012 if k % 2 else 0.0) + rng.uniform(0, 0.006)
            tone = tone_rng()
            ou, ov = rng.random(), rng.random()
            prow, uvrow = [], []
            for r_ in range(rows + 1):
                t = r_ / rows
                s = s0 + (s1 - s0) * t
                f = dome.f_at(s)
                line, uvl = [], []
                for c_ in range(cols + 1):
                    u = c_ / cols
                    dd = e0 + (e1 - e0) * u
                    ang = _angle_at(th, cum, (dd + 0.0) % total if True else dd)
                    bl = bulge * math.sin(math.pi * u) * math.sin(math.pi * t)
                    cl = 0.0
                    if curl:
                        edge = max(abs(u - 0.5) * 2, abs(t - 0.5) * 2)
                        cl = curl * max(0.0, edge - 0.6) / 0.4 * (0.6 + 0.4 * rng.random())
                    line.append(dome.pt(ang, f, out + bl + cl))
                    uvl.append((ou + (dd - e0) / span, ov + (s - s0) / span))
                prow.append(line)
                uvrow.append(uvl)
            fr.grid(prow, mat, tone, uvrow)
    del start


def _ring_pole(fr: _Frame, dome: _Dome, f, out, r=0.022, n=14, skip=None):
    """A binding pole laid round the lodge at height fraction f."""
    pts = [dome.pt(TAU * k / n - math.pi / 2.0, f, out) for k in range(n + 1)]
    for k in range(n):
        if skip and skip(TAU * k / n - math.pi / 2.0, TAU * (k + 1) / n - math.pi / 2.0):
            continue
        fr.rod(pts[k], pts[k + 1], r, M_POLE, sides=3)


def _door(fr: _Frame, dome: _Dome, rng, theta, half_w, door_h, style):
    """The doorway on the ring at angle `theta`: the dark inside, the frame's two poles,
    and the door covering — a hide or mat let down, half rolled, or put aside."""
    f_top = door_h / dome.h
    ths = [theta - half_w, theta + half_w]
    pa0, pa1 = dome.pt(ths[0], 0.0, 0.0), dome.pt(ths[1], 0.0, 0.0)
    pb0, pb1 = dome.pt(ths[0], f_top, 0.0), dome.pt(ths[1], f_top, 0.0)
    # the dark inside, set a little in
    inset = 0.25
    cx, cy = (pa0[0] + pa1[0]) / 2.0, (pa0[1] + pa1[1]) / 2.0
    ln = math.hypot(cx, cy) or 1.0
    ix, iy = -cx / ln * inset, -cy / ln * inset
    fr.poly([(pa0[0] + ix, pa0[1] + iy, 0.0), (pa1[0] + ix, pa1[1] + iy, 0.0),
             (pb1[0] + ix, pb1[1] + iy, door_h + 0.1), (pb0[0] + ix, pb0[1] + iy, door_h + 0.1)], M_DARK)
    # the floor just inside
    fr.poly([(pa0[0], pa0[1], 0.01), (pa1[0], pa1[1], 0.01),
             (pa1[0] + 3 * ix, pa1[1] + 3 * iy, 0.01), (pa0[0] + 3 * ix, pa0[1] + 3 * iy, 0.01)], M_DARK)
    # the jamb poles and the lintel
    for t in ths:
        fr.rod(dome.pt(t, 0.0, 0.03), dome.pt(t, f_top + 0.06, 0.03), 0.03, M_POLE, sides=4)
    fr.rod(dome.pt(ths[0], f_top + 0.05, 0.05), dome.pt(ths[1], f_top + 0.05, 0.05), 0.03, M_POLE, sides=4)
    mat = M_HIDE if style in ("hide_down", "hide_aside") else M_MAT
    tone = 0.55 if mat == M_HIDE and rng.random() < 0.5 else 0.95
    out = 0.07
    if style in ("hide_down", "mat_down"):
        lo = 0.05
        rows = [[dome.pt(ths[0], f_top + 0.04, out), dome.pt(ths[1], f_top + 0.04, out)],
                [dome.pt(ths[0], lo / dome.h, out + 0.06), dome.pt(ths[1], lo / dome.h, out + 0.06)]]
        fr.grid(rows, mat, tone, [[(0, 1), (0.9, 1)], [(0, 0), (0.9, 0)]] if mat == M_MAT else None)
    elif style == "rolled":
        z = door_h - 0.05
        a, b = dome.pt(ths[0] - 0.05, z / dome.h, out + 0.08), dome.pt(ths[1] + 0.05, z / dome.h, out + 0.08)
        fr.log(a, b, 0.09, M_MAT, sides=6)
    else:  # hide_aside: let down at one side of the opening
        side = ths[0] if rng.random() < 0.5 else ths[1]
        w = half_w * 0.9
        t0, t1 = (side, side + w) if side == ths[0] else (side - w, side)
        rows = [[dome.pt(t0, f_top + 0.04, out), dome.pt(t1, f_top + 0.04, out)],
                [dome.pt(t0, 0.02, out + 0.05), dome.pt(t1, 0.02, out + 0.05)]]
        fr.grid(rows, mat, tone)


def mat_lodge(fr: _Frame, rng, size, mats_tone, bark_roof=False, long=False):
    """A bent-pole lodge, its door at -y (two doors, at -y and +y, on a long lodge),
    covered in courses of mats; `bark_roof` lays elm-bark sheets above the second
    course, held by more binding poles."""
    W, D, H = size
    a, b = W / 2.0, D / 2.0
    dome = _Dome(a, b, H, p=2.8 if long else 2.0, q=2.4 if not long else 2.0, rng=rng,
                 ribs=2 * rng.randint(4, 6))
    s_top = dome.ss[-1]
    # the smoke opening: stop the covering where the ring is 16 % of the plan
    f_hole = (1.0 - 0.12 ** dome.q) ** (1.0 / dome.q)
    s_hole = s_top * 0.0
    for i, f in enumerate(dome.fs):
        if f >= f_hole:
            s_hole = dome.ss[i]
            break
    door_h = 1.35 if not long else 1.5
    half_w = 0.42 / max((a + b) / 2.0, 0.5)   # radians either side of the door's centre
    doors = [-math.pi / 2.0] + ([math.pi / 2.0] if long else [])
    # perimeter ranges of the doors at the foot, for the courses that cross them
    th, cum = dome.perimeter_angles(0.15)
    total = cum[-1]

    def dist_of(theta):
        # perimeter distance of angle theta measured from -90 deg
        t = (theta + math.pi / 2.0) % TAU
        k = t / TAU * (len(cum) - 1)
        i = int(k)
        return cum[i] + (k - i) * (cum[min(i + 1, len(cum) - 1)] - cum[i])

    def gaps_for(fm):
        thm, cumm = dome.perimeter_angles(fm)
        tot = cumm[-1]
        out = []
        for d in doors:
            hw = 0.45
            c = (d + math.pi / 2.0) % TAU / TAU * tot
            g0, g1 = c - hw, c + hw
            if g0 < 0:
                out += [(0.0, g1), (tot + g0, tot)]
            else:
                out.append((g0, min(g1, tot)))
        return out
    del th, total, dist_of

    courses = []
    s = 0.0
    while s < s_hole - 0.12:
        s1 = min(s + COURSE_M, s_hole)
        if s_hole - s1 < 0.35:
            s1 = s_hole
        courses.append((s, s1))
        s = s1 - 0.10   # the next course laps over this one's top
    out0 = 0.0
    for k, (s0, s1) in enumerate(courses):
        z_foot = dome.h * dome.f_at(s0)
        crosses_door = z_foot < door_h - 0.15
        gaps = gaps_for((dome.f_at(s0) + dome.f_at(s1)) / 2.0) if crosses_door else ()
        is_bark = bark_roof and k >= 2
        if is_bark:
            _covering_course(fr, dome, rng, s0, s1, out0 + 0.01 * k, M_BARK, BARK_SPAN_M,
                             (0.75, 1.15), lambda: rng.uniform(0.78, 1.15), gaps, rows=2,
                             bulge=0.015, curl=0.05)
        else:
            _covering_course(fr, dome, rng, s0, s1, out0 + 0.012 * k, M_MAT, MAT_SPAN_M,
                             MAT_LEN_M, mats_tone, gaps, rows=2, bulge=0.035)
        # door lintel mats above the opening are part of the next course; a course
        # whose foot is below the door top and whose head is above it leaves the
        # opening's upper part to the lintel piece here:
        if crosses_door and dome.h * dome.f_at(s1) > door_h + 0.05:
            for d in doors:
                hw = 0.42 / max((dome.a + dome.b) / 2.0 * dome.scale(door_h / dome.h), 0.4)
                rows_, uvr = [], []
                ou, ov = rng.random(), rng.random()
                for r_ in range(2):
                    zz = door_h if r_ == 0 else dome.h * dome.f_at(s1)
                    f = zz / dome.h
                    line, uvl = [], []
                    for c_ in range(3):
                        t = d - hw * 1.15 + 2.3 * hw * c_ / 2
                        line.append(dome.pt(t, f, out0 + 0.012 * k + 0.004))
                        uvl.append((ou + c_ * 0.45, ov + r_ * 0.5))
                    rows_.append(line)
                    uvr.append(uvl)
                fr.grid(rows_, M_BARK if is_bark else M_MAT, mats_tone(), uvr)
    # the smoke opening at the crown: dark, the frame's pole ends standing through it
    f_cap = dome.f_at(s_hole)
    n = 12
    fr.poly([dome.pt(TAU * k / n - math.pi / 2.0, f_cap, -0.03) for k in range(n)], M_DARK)
    for k in range(4):
        t = TAU * (k + 0.5) / 4 + rng.uniform(-0.2, 0.2)
        p0 = dome.pt(t, f_cap - 0.03, 0.02)
        fr.rod(p0, (p0[0] * 0.8, p0[1] * 0.8, p0[2] + rng.uniform(0.18, 0.35)), 0.025, M_POLE, sides=3)
    # a mat laid half over the opening against the rain, on most lodges
    if rng.random() < 0.6:
        t = rng.uniform(0, TAU)
        c0, c1 = dome.pt(t - 0.5, f_cap - 0.06, 0.05), dome.pt(t + 0.5, f_cap - 0.06, 0.05)
        far = dome.pt(t + math.pi, f_cap, 0.0)
        mid = ((c0[0] + far[0]) / 2.0 * 0.55 + c0[0] * 0.0, (c0[1] + far[1]) / 2.0 * 0.55, f_cap * dome.h + 0.12)
        mid2 = ((c1[0] + far[0]) / 2.0 * 0.55, (c1[1] + far[1]) / 2.0 * 0.55, f_cap * dome.h + 0.12)
        fr.poly([c0, c1, mid2, mid], M_MAT if not bark_roof else M_BARK, mats_tone(),
                [(0, 0), (0.9, 0), (0.9, 0.5), (0, 0.5)])
    # binding poles round the lodge at the course seams, broken over the doors
    door_skip = lambda t0, t1: any(  # noqa: E731
        min(abs(((t0 + t1) / 2 - d + math.pi) % TAU - math.pi), TAU) < 0.32 for d in doors)
    for k, (s0, s1) in enumerate(courses[1:], start=1):
        f = dome.f_at(s0 + 0.12)
        z = dome.h * f
        _ring_pole(fr, dome, f, 0.05 + 0.012 * k, skip=door_skip if z < door_h + 0.1 else None)
    if bark_roof and len(courses) > 2:
        f = dome.f_at((courses[2][0] + courses[2][1]) / 2.0)
        _ring_pole(fr, dome, f, 0.09, n=12)
    # two arched poles over the crown hold the covering down
    for base in (rng.uniform(0, math.pi),):
        for t in (base, base + math.pi / 2.0):
            prev = None
            for i in range(7):
                ang = t if i < 4 else t + math.pi
                f = (i / 3.0) * f_cap if i < 4 else (6 - i) / 3.0 * f_cap
                q = dome.pt(ang, min(f, f_cap), 0.07 + 0.012 * len(courses))
                if prev is not None:
                    fr.rod(prev, q, 0.024, M_POLE, sides=3)
                prev = q
    styles = ("hide_down", "mat_down", "rolled", "hide_aside")
    for d in doors:
        _door(fr, dome, rng, d, half_w, door_h, rng.choice(styles))
    return dome


def bark_house(fr: _Frame, rng, size, mats_tone):
    """Forsyth's summer house: an oblong of elm-bark sheets on a pole frame, a gabled bark
    roof on a ridge pole, a door at each end (at -y and +y), binding poles outside."""
    W, L, Hw, Hr = size
    x0, x1, y0, y1 = -W / 2.0, W / 2.0, 0.0, L
    bark = lambda: rng.uniform(0.80, 1.15)  # noqa: E731

    def sheet(p00, p10, p01, p11, cols=2, rows=2, curl=0.05, bow=0.02, nrm=(0, 0, 0), u_len=1.0, v_len=1.0):
        ou, ov = rng.random(), rng.random()
        grid, uvg = [], []
        for r_ in range(rows + 1):
            t = r_ / rows
            line, uvl = [], []
            for c_ in range(cols + 1):
                u = c_ / cols
                p = [p00[i] * (1 - u) * (1 - t) + p10[i] * u * (1 - t) + p01[i] * (1 - u) * t + p11[i] * u * t
                     for i in range(3)]
                edge = max(abs(u - 0.5) * 2, abs(t - 0.5) * 2)
                o = bow * math.sin(math.pi * u) * math.sin(math.pi * t) \
                    + curl * max(0.0, edge - 0.55) / 0.45 * (0.5 + 0.5 * rng.random())
                line.append(tuple(p[i] + nrm[i] * o for i in range(3)))
                uvl.append((ou + u * u_len / BARK_SPAN_M, ov + t * v_len / BARK_SPAN_M))
            grid.append(line)
            uvg.append(uvl)
        fr.grid(grid, M_BARK, bark(), uvg)

    # posts at the corners and along the sides, standing a little proud of the walls
    for y in [y0 + i * L / 4.0 for i in range(5)]:
        for x in (x0, x1):
            fr.rod((x, y, 0.0), (x, y, Hw + 0.15), 0.05, M_POLE, sides=4)
    for y in (y0, y1):
        fr.rod((0.0, y, 0.0), (0.0, y, Hr + 0.1), 0.055, M_POLE, sides=4)
    fr.rod((0.0, y0 - 0.35, Hr + 0.05), (0.0, y1 + 0.35, Hr + 0.05), 0.05, M_POLE, sides=5)
    # long walls: sheets up the wall, lapping
    for x, nx in ((x0, -1.0), (x1, 1.0)):
        yy = y0
        k = 0
        while yy < y1 - 0.05:
            w = rng.uniform(0.85, 1.2)
            ya, yb = yy - 0.06, min(yy + w, y1) + 0.06
            off = nx * (0.03 + (0.012 if k % 2 else 0.0))
            sheet((x + off, ya, -0.02), (x + off, yb, -0.02), (x + off, ya, Hw + 0.08), (x + off, yb, Hw + 0.08),
                  nrm=(nx, 0, 0), u_len=yb - ya, v_len=Hw + 0.1)
            yy += w
            k += 1
    # gable ends with their doors
    door_w, door_h = 0.95, 1.55
    for y, ny in ((y0, -1.0), (y1, 1.0)):
        off = ny * 0.03
        xx = x0
        k = 0
        while xx < x1 - 0.05:
            w = rng.uniform(0.8, 1.1)
            xa, xb = xx - 0.05, min(xx + w, x1) + 0.05
            segs = [(xa, xb)]
            if xb > -door_w / 2 and xa < door_w / 2:
                segs = [s for s in ((xa, -door_w / 2), (door_w / 2, xb)) if s[1] - s[0] > 0.1]
            for sa, sb in segs:
                o = off + ny * (0.012 if k % 2 else 0.0)
                # up to the roof line: the gable's height at each edge
                ha = Hw + (Hr - Hw) * (1 - abs(sa) / (W / 2.0))
                hb = Hw + (Hr - Hw) * (1 - abs(sb) / (W / 2.0))
                sheet((sa, y + o, -0.02), (sb, y + o, -0.02), (sa, y + o, ha), (sb, y + o, hb),
                      nrm=(0, ny, 0), u_len=sb - sa, v_len=max(ha, hb))
            xx += w
            k += 1
        # above the door
        sheet((-door_w / 2 - 0.05, y + off, door_h), (door_w / 2 + 0.05, y + off, door_h),
              (-door_w / 2 - 0.05, y + off, Hw + (Hr - Hw) * (1 - (door_w / 2 + 0.05) / (W / 2))),
              (door_w / 2 + 0.05, y + off, Hw + (Hr - Hw) * (1 - (door_w / 2 + 0.05) / (W / 2))),
              nrm=(0, ny, 0), u_len=door_w, v_len=1.0)
        # the dark inside and the door hide
        yi = y - ny * 0.3
        fr.poly([(-door_w / 2, yi, 0.0), (door_w / 2, yi, 0.0), (door_w / 2, yi, door_h), (-door_w / 2, yi, door_h)], M_DARK)
        fr.poly([(-door_w / 2, y, 0.01), (door_w / 2, y, 0.01), (door_w / 2, yi, 0.01), (-door_w / 2, yi, 0.01)], M_DARK)
        if rng.random() < 0.5:
            yo = y + ny * 0.08
            fr.poly([(-door_w / 2 - 0.05, yo, door_h + 0.05), (door_w / 2 + 0.05, yo, door_h + 0.05),
                     (door_w / 2 + 0.05, yo, 0.05), (-door_w / 2 - 0.05, yo, 0.05)][::int(ny)], M_HIDE,
                    rng.choice((0.55, 0.9)))
        else:
            fr.log((-door_w / 2 - 0.1, y + ny * 0.1, door_h), (door_w / 2 + 0.1, y + ny * 0.1, door_h), 0.08, M_HIDE, 6, 0.8)
    # the roof: sheets laid up each slope in two courses, lapping, the ridge capped
    ov = 0.3
    for sx in (-1.0, 1.0):
        ex, ez = sx * (W / 2.0 + ov), Hw - ov * (Hr - Hw) / (W / 2.0)
        rx, rz = 0.0, Hr
        sl = math.hypot(ex - rx, ez - rz)
        nrm = (sx * (Hr - Hw) / (W / 2.0), 0.0, 1.0)
        nl = math.hypot(nrm[0], nrm[2])
        nrm = (nrm[0] / nl, 0.0, nrm[2] / nl)
        for c_, (t0, t1) in enumerate(((0.0, 0.58), (0.48, 1.04))):
            yy = y0 - 0.25 + rng.uniform(-0.2, 0.0)
            k = 0
            while yy < y1 + 0.25:
                w = rng.uniform(0.85, 1.2)
                ya, yb = yy - 0.05, min(yy + w, y1 + 0.3) + 0.05
                o = 0.03 + 0.03 * c_ + (0.012 if k % 2 else 0.0)
                pa = (ex + (rx - ex) * t0 + nrm[0] * o, 0, ez + (rz - ez) * t0 + nrm[2] * o)
                pb = (ex + (rx - ex) * t1 + nrm[0] * o, 0, ez + (rz - ez) * t1 + nrm[2] * o)
                sheet((pa[0], ya, pa[2]), (pa[0], yb, pa[2]), (pb[0], ya, pb[2]), (pb[0], yb, pb[2]),
                      nrm=nrm, u_len=yb - ya, v_len=sl * (t1 - t0))
                yy += w
                k += 1
        # binding poles along the slope
        for t in (0.25, 0.7):
            px, pz = ex + (rx - ex) * t + nrm[0] * 0.12, ez + (rz - ez) * t + nrm[2] * 0.12
            fr.rod((px, y0 - 0.3, pz), (px, y1 + 0.3, pz), 0.03, M_POLE, sides=3)
        # and along the wall
        for z in (0.55, 1.3):
            fr.rod((sx * (W / 2.0 + 0.07), y0 - 0.1, z), (sx * (W / 2.0 + 0.07), y1 + 0.1, z), 0.028, M_POLE, sides=3)
    # the ridge left open for the smoke over the middle third, a dark slit
    fr.poly([(-0.18, L * 0.35, Hr + 0.02), (0.18, L * 0.35, Hr + 0.02), (0.18, L * 0.65, Hr + 0.02),
             (-0.18, L * 0.65, Hr + 0.02)], M_DARK)


# ------------------------------------------------------------------ the yard

def arbor(fr: _Frame, rng):
    """Forked posts, two beams and cross poles, roofed over with cut leafy boughs.
    Its open front is -y. Two floor mats laid under it."""
    L, Dp, Ha = ARBOR
    xs = (-L / 2.0, 0.0, L / 2.0)
    for x in xs:
        for y in (0.0, Dp):
            h = Ha + rng.uniform(-0.05, 0.05)
            fr.rod((x + rng.uniform(-0.05, 0.05), y, 0.0), (x, y, h), 0.055, M_POLE, sides=5)
            fr.rod((x, y, h - 0.15), (x - 0.12, y, h + 0.12), 0.03, M_POLE, sides=3)
            fr.rod((x, y, h - 0.15), (x + 0.12, y, h + 0.12), 0.03, M_POLE, sides=3)
    for y in (0.0, Dp):
        fr.rod((-L / 2.0 - 0.3, y, Ha + 0.03), (L / 2.0 + 0.3, y, Ha + 0.03), 0.05, M_POLE, sides=5)
    for i in range(8):
        x = -L / 2.0 - 0.1 + (L + 0.2) * i / 7 + rng.uniform(-0.06, 0.06)
        fr.rod((x, -0.3, Ha + 0.10), (x + rng.uniform(-0.1, 0.1), Dp + 0.3, Ha + 0.10), 0.03, M_POLE, sides=3)
    # the boughs: one lumpy mass of cut leafy branches thrown over the poles, thick in
    # the middle, ragged at the edges where the branch ends hang over and droop
    nx_, ny_ = 9, 7
    ex, ey = L / 2.0 + 0.55, Dp / 2.0 + 0.5
    cy0 = Dp / 2.0
    top, bot, uvs = [], [], []
    ou, ov = rng.random(), rng.random()
    for j in range(ny_ + 1):
        lt, lb, lu = [], [], []
        for i in range(nx_ + 1):
            u, v = -1.0 + 2.0 * i / nx_, -1.0 + 2.0 * j / ny_
            edge = max(abs(u), abs(v))
            rag = rng.uniform(-0.28, 0.22) if edge > 0.99 else rng.uniform(-0.06, 0.06)
            x = u * (ex + rag)
            y = cy0 + v * (ey + rag)
            hump = (1.0 - edge ** 2) * rng.uniform(0.18, 0.36)
            droop = (rng.uniform(0.25, 0.75) if edge > 0.99 else 0.0)
            z = Ha + 0.14 + hump - droop
            lt.append((x, y, z))
            lb.append((x * 0.97, y if edge > 0.99 else y, (z - 0.10) if edge > 0.99 else Ha + 0.11))
            lu.append((ou + x / BOUGH_SPAN_M, ov + y / BOUGH_SPAN_M))
        top.append(lt)
        bot.append(lb)
        uvs.append(lu)
    fr.grid(top, M_BOUGH, rng.uniform(0.9, 1.1), uvs)
    fr.grid([row[::-1] for row in bot], M_BOUGH, 0.55, [row[::-1] for row in uvs])
    # loose branch ends hanging over the edges
    for i in range(14):
        side = i % 4
        t = rng.uniform(-0.95, 0.95)
        if side < 2:
            sy = -1.0 if side == 0 else 1.0
            base = (t * ex, cy0 + sy * (ey - 0.15), Ha + 0.12)
            out_ = (0.0, sy)
        else:
            sx = -1.0 if side == 2 else 1.0
            base = (sx * (ex - 0.15), cy0 + t * ey, Ha + 0.12)
            out_ = (sx, 0.0)
        drop = rng.uniform(0.5, 1.1)
        w = rng.uniform(0.25, 0.45)
        tip = (base[0] + out_[0] * drop * 0.5 + rng.uniform(-0.15, 0.15),
               base[1] + out_[1] * drop * 0.5 + rng.uniform(-0.15, 0.15), base[2] - drop)
        px, py = -out_[1], out_[0]
        a0 = (base[0] - px * w, base[1] - py * w, base[2])
        a1 = (base[0] + px * w, base[1] + py * w, base[2])
        mid = tuple((base[k] + tip[k]) / 2.0 for k in range(3))
        m0 = (mid[0] - px * w * 1.2, mid[1] - py * w * 1.2, mid[2])
        m1 = (mid[0] + px * w * 1.2, mid[1] + py * w * 1.2, mid[2])
        ou, ov = rng.random(), rng.random()
        k = 1.0 / BOUGH_SPAN_M
        fr.poly([a0, a1, m1, tip, m0], M_BOUGH, rng.uniform(0.75, 1.05),
                [(ou, ov), (ou + 2 * w * k, ov), (ou + 2.2 * w * k, ov + drop * 0.5 * k),
                 (ou + w * k, ov + drop * k), (ou - 0.2 * w * k, ov + drop * 0.5 * k)])
    # floor mats of rushes, laid flat
    for i in range(2):
        cx, cy = rng.uniform(-0.8, 0.8), rng.uniform(0.9, 1.6)
        a = rng.uniform(-0.25, 0.25)
        hw, hd = 0.85, 0.5
        ca, sa = math.cos(a), math.sin(a)
        pts = [(cx + u * ca - v * sa, cy + u * sa + v * ca, 0.012 + 0.004 * i)
               for u, v in ((-hw, -hd), (hw, -hd), (hw, hd), (-hw, hd))]
        ou, ov = rng.random(), rng.random()
        fr.poly(pts, M_MAT, rng.uniform(0.95, 1.15),
                [(ou, ov), (ou + 2 * hw, ov), (ou + 2 * hw, ov + 2 * hd), (ou, ov + 2 * hd)])
    _kettle(fr, rng.uniform(-1.2, 1.2), rng.uniform(0.4, 2.2), 0.0, 0.17, upright=rng.random() < 0.6)


def _kettle(fr: _Frame, x, y, z, r, upright=True):
    n = 8
    h = r * 1.05
    if upright:
        fr.cylinder(x, y, z, z + h, r, M_KETTLE, n=n, top=False)
        fr.poly([(x + r * 0.92 * math.cos(TAU * k / n), y + r * 0.92 * math.sin(TAU * k / n), z + h * 0.85)
                 for k in range(n)], M_DARK)
        # the bail
        fr.rod((x - r, y, z + h), (x, y, z + h + r * 0.9), 0.008, M_CORD, sides=3)
        fr.rod((x, y, z + h + r * 0.9), (x + r, y, z + h), 0.008, M_CORD, sides=3)
    else:
        fr.cylinder(x, y, z, z + h, r, M_KETTLE, n=n, top=True)


def hearth(fr: _Frame, rng, with_tripod=None):
    """An open fire: an ash bed and a scorched ring, logs pushed in from round it, the
    coals, a kettle on a tripod or a crane, and often a roasting spit."""
    n = 11
    ring = [(math.cos(TAU * k / n), math.sin(TAU * k / n)) for k in range(n)]
    rs = [rng.uniform(0.75, 1.0) for _ in range(n)]
    fr.poly([(1.05 * r * c, 1.05 * r * s, 0.008) for (c, s), r in zip(ring, rs)], M_CHAR, 1.0)
    fr.poly([(0.55 * r * c, 0.55 * r * s, 0.018) for (c, s), r in zip(ring, rs)], M_ASH, rng.uniform(0.8, 1.1))
    for k in range(3):
        a = rng.uniform(0, TAU)
        rr = rng.uniform(0.0, 0.15)
        x, y = rr * math.cos(a), rr * math.sin(a)
        fr.poly([(x - 0.07, y - 0.05, 0.03), (x + 0.08, y - 0.04, 0.03), (x + 0.05, y + 0.07, 0.03),
                 (x - 0.06, y + 0.06, 0.03)], M_EMBER)
    nl = rng.randint(4, 6)
    a0 = rng.uniform(0, TAU)
    for k in range(nl):
        a = a0 + TAU * k / nl + rng.uniform(-0.25, 0.25)
        ln = rng.uniform(0.75, 1.15)
        r = rng.uniform(0.04, 0.065)
        p_in = (0.12 * math.cos(a), 0.12 * math.sin(a), 0.05)
        p_mid = (0.38 * math.cos(a), 0.38 * math.sin(a), 0.045)
        p_out = ((0.12 + ln) * math.cos(a), (0.12 + ln) * math.sin(a), r)
        fr.log(p_in, p_mid, r, M_CHAR, 5, caps=False)
        fr.log(p_mid, p_out, r, M_WOOD, 5, tone=rng.uniform(0.8, 1.1))
    tripod = rng.random() < 0.65 if with_tripod is None else with_tripod
    if tripod:
        apex = (rng.uniform(-0.05, 0.05), rng.uniform(-0.05, 0.05), rng.uniform(1.45, 1.65))
        b0 = rng.uniform(0, TAU)
        for k in range(3):
            a = b0 + TAU * k / 3
            foot = (1.0 * math.cos(a), 1.0 * math.sin(a), 0.0)
            over = tuple(apex[i] + (apex[i] - foot[i]) * 0.12 for i in range(3))
            fr.rod(foot, over, 0.028, M_POLE, sides=4)
        kz = rng.uniform(0.35, 0.5)
        fr.rod(apex, (apex[0], apex[1], kz + 0.37), 0.008, M_CORD, sides=3)
        _kettle(fr, apex[0], apex[1], kz, 0.19)
    else:
        a = rng.uniform(0, TAU)
        ca, sa = math.cos(a), math.sin(a)
        fx, fy = 0.95 * ca, 0.95 * sa
        fr.rod((fx, fy, 0.0), (fx, fy, 0.75), 0.035, M_POLE, sides=4)
        fr.rod((fx, fy, 0.68), (fx - 0.1 * sa, fy + 0.1 * ca, 0.85), 0.02, M_POLE, sides=3)
        tail = (1.9 * ca, 1.9 * sa, 0.0)
        tip = (-0.05 * ca, -0.05 * sa, 1.05)
        fr.rod(tail, tip, 0.03, M_POLE, sides=4)
        fr.rod(tip, (tip[0], tip[1], 0.72), 0.008, M_CORD, sides=3)
        _kettle(fr, tip[0], tip[1], 0.38, 0.17)
    if rng.random() < 0.6:
        a = rng.uniform(0, TAU)
        foot = (0.85 * math.cos(a), 0.85 * math.sin(a), 0.0)
        tip = (0.1 * math.cos(a), 0.1 * math.sin(a), 0.62)
        fr.rod(foot, tip, 0.015, M_POLE, sides=3)
        mx = [foot[i] + (tip[i] - foot[i]) * 0.82 for i in range(3)]
        fr.box(mx[0] - 0.07, mx[1] - 0.06, mx[2] - 0.08, mx[0] + 0.07, mx[1] + 0.06, mx[2] + 0.06, M_MEAT)
    for k in range(rng.randint(0, 3)):
        a = rng.uniform(0, TAU)
        r = rng.uniform(0.62, 0.8)
        x, y = r * math.cos(a), r * math.sin(a)
        s = rng.uniform(0.07, 0.12)
        _sack(fr, rng, x, y, -0.03, 2 * s, 1.6 * s, s * 0.9, M_ASH, rng.uniform(0.9, 1.3))


def drying_rack(fr: _Frame, rng):
    """Forked posts at each end carrying three poles, strips of meat or split fish
    hanging over them. Along x, centred."""
    L = RACK_L_M
    for x in (-L / 2.0, L / 2.0):
        for y in (-0.25, 0.25):
            fr.rod((x, y, 0.0), (x, y * 0.3, 1.75), 0.04, M_POLE, sides=4)
    hs = (1.05, 1.32, 1.6)
    fish = rng.random() < 0.4
    for h in hs:
        fr.rod((-L / 2.0 - 0.2, 0.0, h), (L / 2.0 + 0.2, 0.0, h), 0.022, M_POLE, sides=3)
        x = -L / 2.0 + 0.2
        while x < L / 2.0 - 0.15:
            if rng.random() < 0.8:
                w = rng.uniform(0.05, 0.09)
                if fish:
                    d = rng.uniform(0.32, 0.45)
                    fr.poly([(x - w, 0.015, h), (x + w, 0.015, h), (x + w * 1.6, 0.02, h - d * 0.55),
                             (x, 0.02, h - d), (x - w * 1.6, 0.02, h - d * 0.55)], M_FISH, rng.uniform(0.75, 1.15))
                else:
                    d1, d2 = rng.uniform(0.18, 0.4), rng.uniform(0.18, 0.4)
                    t = rng.uniform(0.8, 1.2)
                    fr.poly([(x - w, 0.0, h + 0.02), (x + w, 0.0, h + 0.02), (x + w, -0.03, h - d1), (x - w, -0.03, h - d1)], M_MEAT, t)
                    fr.poly([(x - w, 0.0, h + 0.02), (x - w, 0.03, h - d2), (x + w, 0.03, h - d2), (x + w, 0.0, h + 0.02)], M_MEAT, t)
            x += rng.uniform(0.17, 0.26)


def scaffold(fr: _Frame, rng, mats_tone):
    """Hubbard's scaffold: four forked posts and a platform of poles, rolled mats,
    bundles and a bark box stored on it, a notched log for a ladder. Along x."""
    L, Dd, Hp = SCAFFOLD
    for x in (-L / 2.0, L / 2.0):
        for y in (-Dd / 2.0, Dd / 2.0):
            fr.rod((x, y, 0.0), (x, y, Hp + 0.12), 0.05, M_POLE, sides=4)
    for y in (-Dd / 2.0, Dd / 2.0):
        fr.rod((-L / 2.0 - 0.2, y, Hp), (L / 2.0 + 0.2, y, Hp), 0.045, M_POLE, sides=4)
    for i in range(9):
        x = -L / 2.0 + L * i / 8
        fr.rod((x, -Dd / 2.0 - 0.15, Hp + 0.07), (x, Dd / 2.0 + 0.15, Hp + 0.07), 0.035, M_POLE, sides=3)
    z = Hp + 0.1
    y = -Dd / 2.0 + 0.25
    for i in range(rng.randint(2, 4)):
        r = rng.uniform(0.12, 0.18)
        ln = rng.uniform(1.3, 1.75)
        x0 = rng.uniform(-L / 2.0 + 0.05, L / 2.0 - ln - 0.05) if ln < L - 0.1 else -L / 2.0
        if y + r > Dd / 2.0:
            break
        fr.log((x0, y + r, z + r), (x0 + ln, y + r, z + r), r, M_MAT, 6, mats_tone())
        y += 2 * r + 0.03
    for i in range(rng.randint(1, 3)):
        x = rng.uniform(-L / 2.0 + 0.3, L / 2.0 - 0.3)
        w, d, h = rng.uniform(0.35, 0.55), rng.uniform(0.3, 0.4), rng.uniform(0.22, 0.35)
        _sack(fr, rng, x, Dd / 2.0 - d / 2 - 0.05, z, w, d, h, M_HIDE, rng.uniform(0.7, 1.1))
    fr.rod((L / 2.0 + 0.9, 0.1, 0.0), (L / 2.0 - 0.05, 0.0, Hp + 0.1), 0.07, M_WOOD, sides=5)


def hide_frame(fr: _Frame, rng):
    """A hide laced into a frame of four poles, leaning back on a prop."""
    W, H = 1.8, 2.0
    lean = 0.35
    p = lambda u, v: (u, lean * v / H, v)  # noqa: E731
    fr.rod(p(-W / 2, 0), p(-W / 2, H + 0.1), 0.035, M_POLE, sides=4)
    fr.rod(p(W / 2, 0), p(W / 2, H + 0.1), 0.035, M_POLE, sides=4)
    fr.rod(p(-W / 2 - 0.15, 0.25), p(W / 2 + 0.15, 0.25), 0.03, M_POLE, sides=3)
    fr.rod(p(-W / 2 - 0.15, H - 0.05), p(W / 2 + 0.15, H - 0.05), 0.03, M_POLE, sides=3)
    fr.rod((0.0, lean + 0.9, 0.0), p(0.0, H - 0.1), 0.03, M_POLE, sides=3)
    n = 12
    pts = []
    for k in range(n):
        a = TAU * k / n
        r = rng.uniform(0.82, 1.0)
        u, v = 0.68 * W / 2 * r * math.cos(a), H / 2 + 0.36 * H * r * math.sin(a)
        pts.append(p(u, v))
    fr.poly(pts, M_HIDE, rng.uniform(1.15, 1.4))
    for k in range(0, n, 2):
        a = TAU * k / n
        u = W / 2 * (1 if math.cos(a) > 0 else -1)
        fr.rod(pts[k], p(u if abs(math.cos(a)) > 0.5 else pts[k][0], 0.25 if math.sin(a) < -0.5 else
                         (H - 0.05 if math.sin(a) > 0.5 else pts[k][2])), 0.006, M_CORD, sides=3)


def woodpile(fr: _Frame, rng):
    """Gathered deadwood: limbs and sticks of every length heaped roughly one way."""
    a0 = rng.uniform(-0.3, 0.3)
    for i in range(rng.randint(12, 18)):
        a = a0 + rng.uniform(-0.35, 0.35)
        ln = rng.uniform(0.9, 2.2)
        r = rng.uniform(0.025, 0.07)
        cx, cy = rng.uniform(-0.25, 0.25), rng.uniform(-0.35, 0.35)
        z = r + min(i, 10) * 0.025 + rng.uniform(0, 0.05)
        ca, sa = math.cos(a), math.sin(a)
        fr.log((cx - ca * ln / 2, cy - sa * ln / 2, z * rng.uniform(0.6, 1.0)),
               (cx + ca * ln / 2, cy + sa * ln / 2, z), r, M_WOOD, 5, rng.uniform(0.75, 1.25))


def mortar(fr: _Frame, rng):
    """A wooden mortar, a hollowed log stood on end, its pestle stood in it."""
    r = rng.uniform(0.19, 0.24)
    h = rng.uniform(0.55, 0.7)
    fr.cylinder(0.0, 0.0, 0.0, h, r, M_WOOD, n=8, top=True, top_mat=M_WOOD)
    fr.poly([(0.6 * r * math.cos(TAU * k / 8), 0.6 * r * math.sin(TAU * k / 8), h + 0.004) for k in range(8)], M_DARK)
    a = rng.uniform(0, TAU)
    top = (0.28 * math.cos(a), 0.28 * math.sin(a), h + 1.05)
    fr.rod((0.0, 0.0, h - 0.15), top, 0.035, M_WOOD, sides=5)
    fr.log((top[0] * 0.9, top[1] * 0.9, top[2] - 0.25), top, 0.06, M_WOOD, 6)


def canoe(fr: _Frame, rng, dugout=False, overturned=False):
    """A bark canoe, sewn panels with upturned ends, or a dugout; along x, centred.
    Laid on the ground right way up or turned over."""
    L = CANOE_L_M if not dugout else 4.6
    beam = 0.86 if not dugout else 0.68
    depth = 0.36 if not dugout else 0.42
    st = 9
    secs = []
    for i in range(st):
        t = -1.0 + 2.0 * i / (st - 1)
        w = beam / 2.0 * max(0.04, 1.0 - abs(t) ** (2.4 if not dugout else 3.5))
        top = depth + (0.28 * abs(t) ** 5 if not dugout else 0.04 * abs(t) ** 2)
        bot = 0.03 + (0.10 * abs(t) ** 3 if not dugout else 0.05 * abs(t) ** 3)
        x = t * L / 2.0
        prof = [(-w, top), (-w * 0.92, bot + (top - bot) * 0.35), (-w * 0.45, bot), (0.0, bot - 0.01),
                (w * 0.45, bot), (w * 0.92, bot + (top - bot) * 0.35), (w, top)]
        secs.append([(x, y, z) for y, z in prof])
    if overturned:
        H = max(p[2] for s in secs for p in s)
        secs = [[(x, -y, H - z + 0.02) for x, y, z in s] for s in secs]
    mat = M_WOOD if dugout else M_BIRCH
    for i in range(st - 1):
        tone = rng.uniform(0.85, 1.12) if not dugout else rng.uniform(0.9, 1.05)
        for j in range(len(secs[i]) - 1):
            fr.poly([secs[i][j], secs[i + 1][j], secs[i + 1][j + 1], secs[i][j + 1]], mat,
                    tone * (0.92 if j in (2, 3) else 1.0))
    # gunwales and thwarts
    for side in (0, -1):
        for i in range(st - 1):
            fr.rod(secs[i][side], secs[i + 1][side], 0.022 if not dugout else 0.035, M_POLE if not dugout else M_WOOD, sides=3)
    if not dugout:
        for i in (2, 4, 6):
            fr.rod(secs[i][0], secs[i][-1], 0.018, M_POLE, sides=3)
        # the pitched seams, dark lines across the hull
        for i in (2, 6):
            for j in range(len(secs[i]) - 1):
                a, b = secs[i][j], secs[i][j + 1]
                fr.rod(a, b, 0.012, M_CHAR, sides=3)
    elif not overturned:
        # the hollow
        inner = [(p[0], p[1] * 0.75, p[2] - 0.04) for p in [secs[k][0] for k in range(1, st - 1)]]
        inner2 = [(p[0], p[1] * 0.75, p[2] - 0.04) for p in [secs[k][-1] for k in range(1, st - 1)]]
        for k in range(len(inner) - 1):
            fr.poly([inner[k], inner[k + 1], inner2[k + 1], inner2[k]], M_DARK)
    # paddles laid by it
    if rng.random() < 0.7:
        y0 = -beam / 2.0 - 0.35
        x0 = rng.uniform(-1.0, 0.0)
        fr.rod((x0, y0, 0.03), (x0 + 1.15, y0 + 0.05, 0.03), 0.018, M_POLE, sides=3)
        fr.poly([(x0 + 1.15, y0 - 0.06, 0.035), (x0 + 1.75, y0 - 0.06, 0.035), (x0 + 1.75, y0 + 0.16, 0.035),
                 (x0 + 1.15, y0 + 0.16, 0.035)][::-1], M_POLE, 1.1)


def picket(fr: _Frame, rng):
    """A tether stake and its line paid out across the grazing, coiled at the end."""
    fr.rod((0.0, 0.0, 0.0), (0.0, 0.0, 0.65), 0.04, M_POLE, sides=4)
    a = rng.uniform(0, TAU)
    ln = rng.uniform(3.0, 5.5)
    ex, ey = ln * math.cos(a), ln * math.sin(a)
    mid = (ex * 0.5, ey * 0.5, 0.08)
    fr.rod((0.0, 0.0, 0.55), mid, 0.009, M_CORD, sides=3)
    fr.rod(mid, (ex, ey, 0.02), 0.009, M_CORD, sides=3)
    n = 7
    for k in range(n):
        a0, a1 = TAU * k / n, TAU * (k + 1) / n
        fr.rod((ex + 0.18 * math.cos(a0), ey + 0.18 * math.sin(a0), 0.02),
               (ex + 0.18 * math.cos(a1), ey + 0.18 * math.sin(a1), 0.02), 0.009, M_CORD, sides=3)


def pack_saddle(fr: _Frame, rng, mats_tone):
    """A pack saddle laid by: crossed bucks at each end on two side bars, over a pad of
    hide, with a load of rolled mats and a bundle beside it."""
    for x in (-0.3, 0.3):
        fr.rod((x, -0.28, 0.08), (x, 0.12, 0.55), 0.025, M_WOOD, sides=4)
        fr.rod((x, 0.28, 0.08), (x, -0.12, 0.55), 0.025, M_WOOD, sides=4)
    for y in (-0.22, 0.22):
        fr.rod((-0.45, y, 0.14), (0.45, y, 0.14), 0.03, M_WOOD, sides=4)
    fr.box(-0.5, -0.4, 0.0, 0.5, 0.4, 0.08, M_HIDE, rng.uniform(0.5, 0.8))
    for k in range(rng.randint(1, 2)):
        r = rng.uniform(0.13, 0.17)
        y = 0.75 + k * (2 * r + 0.04)
        fr.log((-0.75, y, r), (0.75, y, r), r, M_MAT, 6, mats_tone())
    w = rng.uniform(0.45, 0.6)
    _sack(fr, rng, 0.0, -0.85, 0.0, w, 0.5, rng.uniform(0.3, 0.45), M_HIDE, rng.uniform(0.75, 1.1))


def _sack(fr: _Frame, rng, x, y, z, w, d, h, mat, tone=1.0):
    """A soft bundle wrapped in hide or a mat and tied: a lumpy, flat-bottomed ovoid."""
    nu, nv = 7, 4
    bumps = [rng.uniform(0.88, 1.1) for _ in range(nu)]
    rows = []
    for j in range(nv + 1):
        el = -0.15 + (math.pi / 2.0 + 0.15) * j / nv
        line = []
        for i in range(nu + 1):
            az = TAU * i / nu
            bm = bumps[i % nu] if 0 < j < nv else 1.0
            cr = math.cos(el) * bm
            line.append((x + w / 2.0 * cr * math.cos(az), y + d / 2.0 * cr * math.sin(az),
                         z + max(0.0, h * (0.12 + 0.88 * math.sin(el)))))
        rows.append(line)
    fr.grid(rows, mat, tone)
    # the tie round its middle
    for i in range(nu):
        a0, a1 = TAU * i / nu, TAU * (i + 1) / nu
        fr.rod((x + w * 0.51 * math.cos(a0), y + d * 0.51 * math.sin(a0), z + h * 0.55),
               (x + w * 0.51 * math.cos(a1), y + d * 0.51 * math.sin(a1), z + h * 0.55), 0.008, M_CORD, sides=3)


def bundle(fr: _Frame, rng, mats_tone):
    """By a lodge door: a bundle, a rolled mat or a bark box."""
    k = rng.random()
    if k < 0.4:
        _sack(fr, rng, 0.0, 0.0, 0.0, rng.uniform(0.45, 0.7), rng.uniform(0.35, 0.5),
              rng.uniform(0.25, 0.4), M_HIDE, rng.uniform(0.7, 1.15))
    elif k < 0.75:
        r = rng.uniform(0.12, 0.16)
        fr.log((-0.75, 0.0, r), (0.75, 0.0, r), r, M_MAT, 6, mats_tone())
    else:
        fr.cylinder(0.0, 0.0, 0.0, rng.uniform(0.3, 0.45), rng.uniform(0.14, 0.2), M_BARK, n=7)


# ------------------------------------------------------------------ the layout

def _obb(x, y, rot, hw, hd):
    """The corners of a rectangle centred at (x, y), turned rot degrees."""
    th = math.radians(rot)
    c, s = math.cos(th), math.sin(th)
    return [(x + u * c - v * s, y + u * s + v * c) for u, v in ((-hw, -hd), (hw, -hd), (hw, hd), (-hw, hd))]


def _overlap(p, q):
    """Separating-axis test for two convex polygons."""
    for poly in (p, q):
        for i in range(len(poly)):
            a, b = poly[i], poly[(i + 1) % len(poly)]
            ax, ay = b[1] - a[1], a[0] - b[0]
            pa = [ax * x + ay * y for x, y in p]
            qa = [ax * x + ay * y for x, y in q]
            if max(pa) < min(qa) or max(qa) < min(pa):
                return False
    return True


class _Layout:
    def __init__(self, params: LodgeCampParams, rng):
        self.p, self.rng = params, rng
        self.taken: list = []

    def inside(self, poly):
        L, D = self.p.length_m, self.p.depth_m
        return all(MARGIN_M <= x <= L - MARGIN_M and MARGIN_M <= y <= D - MARGIN_M for x, y in poly)

    def free(self, poly):
        return self.inside(poly) and not any(_overlap(poly, t) for t in self.taken)

    def place(self, hw, hd, cost, tries=160, rot_fn=None, gap=GAP_M / 2.0, take_gap=None):
        """The cheapest free spot of `tries` seeded tries; None when nothing fits."""
        L, D = self.p.length_m, self.p.depth_m
        best = None
        for _ in range(tries):
            x, y = self.rng.uniform(0, L), self.rng.uniform(0, D)
            rot = rot_fn(x, y) if rot_fn else self.rng.uniform(0, 360)
            poly = _obb(x, y, rot, hw + gap, hd + gap)
            if not self.free(poly):
                continue
            c = cost(x, y) + self.rng.uniform(0, 0.8)
            if best is None or c < best[0]:
                best = (c, x, y, rot)
        if best is None:
            return None
        _, x, y, rot = best
        g = gap if take_gap is None else take_gap
        self.taken.append(_obb(x, y, rot, hw + g, hd + g))
        return x, y, rot


def _facing(px, py, tx, ty):
    """The rotation that turns an item's -y (its door) towards (tx, ty)."""
    return math.degrees(math.atan2(ty - py, tx - px)) + 90.0


def layout(params: LodgeCampParams):
    """Every item as (kind, x, y, rot_deg, extra) in the group's frame. A layout that
    cannot seat every dwelling is dealt again from the next seed, a fixed number of
    times, so the result stays a pure function of the record."""
    last = None
    for attempt in range(24):
        try:
            return _layout_once(params, random.Random(params.seed + 7919 * attempt))
        except ParamError as e:
            last = e
    raise last


def _layout_once(params: LodgeCampParams, rng):
    lay = _Layout(params, rng)
    L, D = params.length_m, params.depth_m
    items = []
    long_axis_x = L >= D
    ny = max(1, params.arbors) if (params.dwellings or params.arbors) else 0
    yards = []
    for i in range(ny):
        t = (i + 0.5) / ny
        x = L * t if long_axis_x else L * 0.5 + rng.uniform(-1.5, 1.5)
        y = D * 0.5 + rng.uniform(-1.5, 1.5) if long_axis_x else D * t
        yards.append((x + rng.uniform(-1.0, 1.0), y))
    # the arbors and their hearths, which make the yards
    for i, (x, y) in enumerate(yards):
        if i < params.arbors:
            rot = rng.uniform(-20, 20) + (0 if long_axis_x else 90)
            th = math.radians(rot)
            poly = _obb(x - math.sin(th) * ARBOR[1] / 2.0, y + math.cos(th) * ARBOR[1] / 2.0, rot,
                        ARBOR[0] / 2.0 + 0.4, ARBOR[1] / 2.0 + 0.4)
            if lay.free(poly):
                lay.taken.append(poly)
                items.append(("arbor", x, y, rot, None))
                th = math.radians(rot)
                hx, hy = x + 1.6 * math.sin(th), y - 1.6 * math.cos(th)
                lay.taken.append(_obb(hx, hy, 0, 1.15, 1.15))
                items.append(("hearth", hx, hy, rng.uniform(0, 360), True))

    # canoes, drawn up along the named edge, end to end
    if params.canoes:
        edge = params.canoe_edge
        along = L if edge in ("north", "south") else D
        n = params.canoes
        for i in range(n):
            t = (i + 0.5) / n
            a = along * (0.15 + 0.7 * t) + rng.uniform(-0.6, 0.6)
            inset = MARGIN_M + 1.0 + rng.uniform(0.0, 0.8)
            if edge == "north":
                x, y, rot = a, D - inset, 0.0
            elif edge == "south":
                x, y, rot = a, inset, 0.0
            elif edge == "east":
                x, y, rot = L - inset, a, 90.0
            else:
                x, y, rot = inset, a, 90.0
            rot += rng.uniform(-8, 8)
            poly = _obb(x, y, rot, CANOE_L_M / 2.0 + 0.2, 0.75)
            if lay.free(poly):
                lay.taken.append(poly)
                items.append(("canoe", x, y, rot, (i % 3 == 2, rng.random() < 0.35)))

    def near_yard(lo, hi):
        def cost(x, y):
            d = min(math.hypot(x - a, y - b) for a, b in yards) if yards else 6.0
            return (lo - d) * 3 if d < lo else ((d - hi) * 2 if d > hi else 0.0)
        return cost

    def to_yard(x, y):
        if not yards:
            return rng.uniform(0, 360)
        a, b = min(yards, key=lambda q: math.hypot(x - q[0], y - q[1]))
        return _facing(x, y, a, b) + rng.uniform(-22, 22)

    dw = (["bark_house"] * params.bark_houses + ["long_lodge"] * params.long_lodges)
    domes = (["mat_lodge"] * params.mat_lodges + ["bark_roofed"] * params.bark_roofed_lodges)
    rng.shuffle(domes)
    sizes = []
    for k, kind in enumerate(domes):
        sizes.append(LODGE_SIZES[2] if k % 4 == 0 else (LODGE_SIZES[0] if k % 4 == 3 else LODGE_SIZES[1]))
    order = [(k, None) for k in dw] + list(zip(domes, sizes))
    lodges = []
    for kind, size in order:
        if kind == "bark_house":
            hw, hd = BARK_HOUSE[0] / 2.0 + 0.4, BARK_HOUSE[1] / 2.0 + 0.4
        elif kind == "long_lodge":
            hw, hd = LONG_LODGE[0] / 2.0 + 0.1, LONG_LODGE[1] / 2.0 + 0.1
        else:
            hw, hd = size[0] / 2.0 + 0.1, size[1] / 2.0 + 0.1
        got = lay.place(hw, hd, near_yard(4.5, 10.5), tries=1200, rot_fn=to_yard)
        if got is None:
            raise ParamError(f"{params.seed_name}: no room left for a {kind} — fewer lodges or "
                             f"more ground")
        x, y, rot = got
        items.append((kind, x, y, rot, size))
        lodges.append((x, y, rot, hd))
    # by each door, sometimes, a bundle or a rolled mat
    for x, y, rot, hd in lodges:
        for _ in range(rng.randint(0, 2)):
            th = math.radians(rot)
            off = rng.uniform(-1.0, 1.0)
            bx = x + (hd + 1.0) * math.sin(th) + off * math.cos(th)
            by = y - (hd + 1.0) * math.cos(th) + off * math.sin(th)
            poly = _obb(bx, by, rot, 0.8, 0.25)
            if lay.free(poly):
                lay.taken.append(poly)
                items.append(("bundle", bx, by, rot + rng.uniform(-30, 30), None))

    def by_lodge(lo, hi):
        def cost(x, y):
            if not lodges:
                return 0.0
            d = min(math.hypot(x - a, y - b) - h for a, b, _, h in lodges)
            return (lo - d) * 3 if d < lo else ((d - hi) * 2 if d > hi else 0.0)
        return cost

    def put(kind, hw, hd, cost, n, extra=None):
        for _ in range(n):
            got = lay.place(hw, hd, cost, gap=0.45)
            if got:
                items.append((kind, *got, extra))

    put("hearth", 1.05, 1.05, by_lodge(1.0, 3.5), params.hearths, None)
    put("drying_rack", RACK_L_M / 2.0 + 0.3, 0.5, near_yard(2.5, 7.0), params.drying_racks)
    put("mortar", 0.5, 0.5, near_yard(1.5, 4.0), params.mortars)
    put("woodpile", 1.15, 0.65, near_yard(2.0, 5.5), params.woodpiles)
    put("scaffold", SCAFFOLD[0] / 2.0 + 0.4, SCAFFOLD[1] / 2.0 + 0.6, by_lodge(0.8, 3.0), params.scaffolds)
    put("hide_frame", 1.05, 0.9, by_lodge(1.0, 4.0), params.hide_frames)
    # the horse ground: stakes across the open, pack saddles laid by
    put("picket", 0.6, 0.6, lambda x, y: 0.0, params.horse_pickets)
    put("pack_saddle", 0.85, 1.2, lambda x, y: 0.0, params.pack_saddles)
    return items


# ------------------------------------------------------------------ the build

def mesh(params: LodgeCampParams) -> _Mesh:
    params.validate()
    m = _Mesh()
    rng = random.Random(params.seed ^ 0x5EED)
    conf_lodge = params.worst_conf("mat_lodges", "long_lodges", "bark_roofed_lodges", "bark_houses")
    conf_yard = params.worst_conf("arbors", "hearths", "drying_racks", "scaffolds", "hide_frames",
                                  "woodpiles", "mortars")
    conf_canoe = params.worst_conf("canoes")
    conf_horse = params.worst_conf("horse_pickets", "pack_saddles")
    cond = params.mat_condition

    def mats_tone():
        if cond == "new":
            return rng.uniform(1.0, 1.2)
        if cond == "weathered":
            return rng.uniform(0.78, 0.98)
        return rng.uniform(0.8, 1.18)

    for kind, x, y, rot, extra in layout(params):
        if kind in ("mat_lodge", "bark_roofed", "long_lodge", "bark_house"):
            if kind == "bark_house":
                # the house's own frame runs y from its door at 0 to L: centre it
                fr = _Frame(m, x, y, rot, conf_lodge)
                shift = BARK_HOUSE[1] / 2.0
                fr2 = _Frame(m, x - shift * -math.sin(math.radians(rot)), y - shift * math.cos(math.radians(rot)),
                             rot, conf_lodge)
                del fr
                bark_house(fr2, rng, BARK_HOUSE, mats_tone)
            else:
                size = LONG_LODGE if kind == "long_lodge" else extra
                fr = _Frame(m, x, y, rot, conf_lodge)
                mat_lodge(fr, rng, size, mats_tone, bark_roof=(kind == "bark_roofed"), long=(kind == "long_lodge"))
            continue
        c = conf_canoe if kind == "canoe" else (conf_horse if kind in ("picket", "pack_saddle") else conf_yard)
        fr = _Frame(m, x, y, rot, c)
        if kind == "arbor":
            arbor(fr, rng)
        elif kind == "hearth":
            hearth(fr, rng, with_tripod=None if not extra else True)
        elif kind == "drying_rack":
            drying_rack(fr, rng)
        elif kind == "scaffold":
            scaffold(fr, rng, mats_tone)
        elif kind == "hide_frame":
            hide_frame(fr, rng)
        elif kind == "woodpile":
            woodpile(fr, rng)
        elif kind == "mortar":
            mortar(fr, rng)
        elif kind == "canoe":
            canoe(fr, rng, dugout=extra[0], overturned=extra[1])
        elif kind == "picket":
            picket(fr, rng)
        elif kind == "pack_saddle":
            pack_saddle(fr, rng, mats_tone)
        elif kind == "bundle":
            bundle(fr, rng, mats_tone)
    return m


def _pad(blob: bytes, fill: bytes = b"\x00") -> bytes:
    return blob + fill * ((4 - len(blob) % 4) % 4)


def _unit_normal(pts) -> tuple:
    nx = ny = nz = 0.0
    for i, p in enumerate(pts):
        q = pts[(i + 1) % len(pts)]
        nx += (p[1] - q[1]) * (p[2] + q[2])
        ny += (p[2] - q[2]) * (p[0] + q[0])
        nz += (p[0] - q[0]) * (p[1] + q[1])
    m = math.sqrt(nx * nx + ny * ny + nz * nz) or 1.0
    return (nx / m, ny / m, nz / m)


def glb(params: LodgeCampParams, structure_id: str, phase_id: str) -> bytes:
    """The group's GLB. glTF is y-up: the archetype's (x, y, z) is written as (x, z, -y),
    a rotation, so no face turns inside out (docs/GLB-CONTRACT.md)."""
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
    for mi in range(len(MATERIALS)):
        pos, nrm, uv, conf, tone, idx = [], [], [], [], [], []
        for pts, mat, c, t, uvs in m.polys:
            if mat != mi:
                continue
            nz = _unit_normal(pts)
            ngl = (round(nz[0], 4), round(nz[2], 4), round(-nz[1], 4))
            base = len(pos)
            for k, p in enumerate(pts):
                pos.append(to_gl(p))
                nrm.append(ngl)
                uv.append((round(uvs[k][0], 4), round(1.0 - uvs[k][1], 4)) if uvs else (0.0, 0.0))
                conf.append(c)
                tone.append(round(t, 3))
            for k in range(1, len(pts) - 1):
                idx += [base, base + k, base + k + 1]
        if not idx:
            continue
        attrs = {"POSITION": accessor(pos, 5126, "VEC3", 3, 34962, True),
                 "NORMAL": accessor(nrm, 5126, "VEC3", 3, 34962),
                 "_CONFIDENCE": accessor(conf, 5126, "SCALAR", 1, 34962)}
        if mi in TEXTURED:
            # The coverings' tile coordinates, as `_UV` and not TEXCOORD_0: no texture
            # rides in the GLB (the renderer binds the library's sheets by name), so
            # the web derivative's prune would drop a TEXCOORD_0 nothing samples.
            attrs["_UV"] = accessor(uv, 5126, "VEC2", 2, 34962)
        if any(abs(t - 1.0) > 1e-6 for t in tone):
            attrs["_TONE"] = accessor(tone, 5126, "SCALAR", 1, 34962)
        used.append(mi)
        prims.append({"attributes": attrs,
                      "indices": accessor(idx, 5123 if len(pos) < 65536 else 5125, "SCALAR", 1, 34963),
                      "material": len(used) - 1})
    mats = []
    for mi in used:
        name, rgba, r, metal, emis = MATERIALS[mi]
        spec = {"name": name, "doubleSided": True, "pbrMetallicRoughness": {
            "baseColorFactor": [round(x, 4) for x in rgba], "metallicFactor": metal,
            "roughnessFactor": round(r, 4)}}
        if emis:
            spec["emissiveFactor"] = [round(x, 4) for x in emis]
        mats.append(spec)
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
