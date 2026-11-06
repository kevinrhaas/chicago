"""haystack — one round stack of hay, pitched by hand round a stack pole.

See `haystack_params` for the evidence, the form and every dimension. This module builds
the stack and writes its glTF itself, in pure Python, with no Blender (the K12/K16 route,
T-2266): `generators/haystack_emit.py` calls `glb()` for each record and
`generators/mesh_inputs.py` hashes this file and that one, and nothing else, into the
asset's freshness record. That is why the archetype is not in `generators/emit.py`: every
Blender-built mesh hashes emit.py's bytes, so registering a new archetype there re-stales
the whole town (722 assets on 2026-10-15, `tools/measure_generator_half.py`).

## Hay, not a lathe (T-3401)

The first build (T-2510) was a surface of revolution of the params' half-section, 18
flat-shaded facets round, in one flat colour: the owner, 2026-11-06, saw "smooth pale
onion domes" and asked for stacks that "look photographic real and varied enough they
look real". So a stack is now built the way hay is:

- **the body** is a fine grid (48 round, 30 up the section), smooth-shaded, its girth
  lumped forkful by forkful and its peak a little off the axis, tipped by `lean_deg`,
  and cut back where `shape` says the stock or the farm took hay from it;
- **its hay** is the library sheet the material names (`stack_hay`, `stack_hay_weathered`,
  `stack_hay_cut` in `assets/textures/camp_1812_pbr/`, bound by
  renderers/web/js/camp-surfaces.js): combed stems, greyed thatch, the brighter heart.
  Each primitive carries the sheet's tile coordinates as `_UV` (docs/GLB-CONTRACT.md
  § Camp coverings) and a per-vertex `_TONE`: darker at the damp foot and under an
  overhang, a forkful paler or duller than the next;
- **tufts**: a thousand-odd wisps of hay stand out of the surface and hang from the eave
  and the overhang, so the stack's edge against the sky is ragged as hay is, never a
  curve;
- **the foot**: a skirt of trodden, fallen hay round the stack and, where hay was pulled,
  a heap or two of it on the ground.

Every one of those is the archetype's reconstruction (L-1812-lees-place-haystacks-2510),
fixed by the record's own seed so two builds make the same bytes.

## No figure, no animal

docs/LIBERTIES.md L1 binds every vertex here, and the cattle Wau-Bun puts among the
stacks are not drawn either: what stands at Lee's Place is the hay, and the marks the
cattle left in it.
"""

from __future__ import annotations

import json
import math
import random
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from common import materials  # noqa: E402
from archetypes.haystack_params import POLE_ABOVE_M, POLE_SIDE_M, HaystackParams  # noqa: E402

GENERATOR = "chicago-4d generators/archetypes/haystack.py (T-2510, T-3401)"

M_HAY, M_THATCH, M_HEART, M_POLE = 0, 1, 2, 3

# Material name, the linear mean of its sheet (what a renderer shows if the sheet fails
# to load: the stack degrades to the hay's own average colour, never to white), roughness,
# and the sheet's tile in metres (its material.json `span_m`), or None for an untextured one.
MATERIALS = [
    ("stack_hay", (0.212, 0.165, 0.087, 1.0), 0.95, 1.2),
    ("stack_hay_weathered", (0.145, 0.126, 0.094, 1.0), 0.97, 1.2),
    ("stack_hay_cut", (0.185, 0.144, 0.066, 1.0), 0.92, 0.9),
    # A peeled sapling gone grey-brown in the weather (linear; the first, 0.33, drew a
    # pale blue-grey stick against the evening sky).
    ("stack_pole", (0.110, 0.092, 0.070, 1.0), materials.SUBSTRATES["hewn_log"].roughness, None),
]

SEGMENTS = 48           # columns round the stack
RINGS = 30              # rings from the foot to the last below the peak
TUFTS = 760             # wisps over the body
EAVE_TUFTS = 300        # wisps hanging from the girth and any overhang
LITTER_TUFTS = 140      # wisps lying on the trodden skirt


def _smooth(t: float) -> float:
    t = min(1.0, max(0.0, t))
    return t * t * (3.0 - 2.0 * t)


def _wrap(a: float) -> float:
    """An angle difference folded into (-pi, pi]."""
    return (a + math.pi) % (2.0 * math.pi) - math.pi


def _norm(v):
    m = math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2]) or 1.0
    return (v[0] / m, v[1] / m, v[2] / m)


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def _add(a, b, k=1.0):
    return (a[0] + k * b[0], a[1] + k * b[1], a[2] + k * b[2])


class _Mesh:
    """Indexed vertices per material, in the archetype's frame (x east, y north, z up)."""

    def __init__(self):
        self.parts = [{"pos": [], "nrm": [], "uv": [], "tone": [], "conf": [], "idx": []}
                      for _ in MATERIALS]

    def vert(self, mat, p, n, uv, tone, conf) -> int:
        part = self.parts[mat]
        part["pos"].append(p)
        part["nrm"].append(n)
        part["uv"].append(uv)
        part["tone"].append(tone)
        part["conf"].append(conf)
        return len(part["pos"]) - 1

    def tri(self, mat, a, b, c) -> None:
        self.parts[mat]["idx"] += [a, b, c]

    def quad(self, mat, pts, nrm, uvs, tones, conf) -> None:
        # Wound so its front faces the way its normals do: a double-sided material lights
        # a back face with its normal turned over, so a wisp wound the wrong way would
        # draw dark against the stack it stands out of.
        g = _cross(_add(pts[1], pts[0], -1.0), _add(pts[2], pts[0], -1.0))
        n0 = nrm[0]
        if g[0] * n0[0] + g[1] * n0[1] + g[2] * n0[2] < 0:
            pts, nrm, uvs, tones = pts[::-1], nrm[::-1], uvs[::-1], tones[::-1]
        ix = [self.vert(mat, pts[k], nrm[k], uvs[k], tones[k], conf) for k in range(4)]
        self.tri(mat, ix[0], ix[1], ix[2])
        self.tri(mat, ix[0], ix[2], ix[3])

    @property
    def triangles(self) -> int:
        n = 0
        for part in self.parts:
            n += len(part["idx"]) // 3
        return n


class _Stack:
    """The stack's surface as a function: radius and centre at each (angle, height)."""

    def __init__(self, params: HaystackParams):
        self.p = params
        rng = random.Random(params.seed)
        self.rng = rng
        self.cx = self.cy = params.side_m / 2.0
        h = params.height_m
        prof = list(params.profile())
        if params.shape == "settled":
            # dried down: the belly pushed out, the shoulder sunk and the top gone round
            # and full rather than drawn to a point
            sh = params.shoulder_z_m
            prof = [(r * (1.0 + 0.10 * math.sin(math.pi * min(z / (0.75 * h), 1.0))
                          + (0.16 * (z - sh) / (h - sh) if z > sh else 0.0)),
                     z if z <= 0.4 * h else 0.4 * h + (z - 0.4 * h) * 0.93)
                    for r, z in prof[:-1]] + [(0.0, 0.4 * h + 0.6 * h * 0.93)]
        elif params.shape == "pitched":
            # fresh: the top drawn in straighter to a sharper peak
            sh = params.shoulder_z_m
            prof = [(r * (1.0 - (0.10 * math.sin(math.pi * (z - sh) / (h - sh)) if z > sh else 0.0)), z)
                    for r, z in prof[:-1]] + [prof[-1]]
        self.prof = prof
        # The half-section densified: RINGS points by arc length, foot to just below the peak.
        seg = []
        for k in range(len(prof) - 1):
            (r0, z0), (r1, z1) = prof[k], prof[k + 1]
            seg.append(math.hypot(r1 - r0, z1 - z0))
        total = 0.0
        for d in seg:
            total += d
        self.arc_total = total
        stop = total - 0.10 * h * 0.35      # leave the cap's last few centimetres to the fan
        self.ring_s = [stop * j / (RINGS - 1) for j in range(RINGS)]
        self.seg = seg
        # Forkfuls: lumps on the girth, each its own size, fixed by the seed.
        self.waves = [(rng.randint(2, 7), rng.uniform(0, 2 * math.pi), rng.uniform(-1.2, 1.2),
                       rng.uniform(0.012, 0.030)) for _ in range(5)]
        self.blobs = [(rng.uniform(-math.pi, math.pi), rng.uniform(0.05, 0.95) * h,
                       rng.uniform(0.25, 0.55), rng.uniform(0.25, 0.6), rng.uniform(-0.05, 0.06))
                      for _ in range(16)]
        lean = math.radians(params.lean_deg)
        self.lean_dir = rng.uniform(0, 2 * math.pi)
        self.lean = math.tan(lean)
        # A settled stack's top slumps toward its lean; any stack's peak is a little off.
        self.slump = (0.22 if params.shape == "settled" else 0.07) * params.radius_m
        # Fed: the stock have eaten in all round, deeper in some bays than others.
        self.fed = [(rng.randint(1, 4), rng.uniform(0, 2 * math.pi), rng.uniform(0.3, 1.0))
                    for _ in range(3)]
        self.fed_depth = rng.uniform(0.24, 0.34)
        self.fed_top = rng.uniform(1.15, 1.35)
        # Cut: hay pulled out of one side, down to the ground.
        self.cut_dir = rng.uniform(0, 2 * math.pi)
        self.cut_half = rng.uniform(0.42, 0.55)
        self.cut_in = rng.uniform(0.42, 0.55)      # the face, as a fraction of the radius
        self.cut_top = rng.uniform(0.50, 0.62) * h
        self.offsets = {m: (rng.uniform(0, 7), rng.uniform(0, 7)) for m in range(3)}

    def section(self, s: float):
        """(r, z) on the profile at arc length s."""
        prof = self.prof
        acc = 0.0
        for k, d in enumerate(self.seg):
            if s <= acc + d or k == len(self.seg) - 1:
                t = 0.0 if d <= 0 else min(1.0, max(0.0, (s - acc) / d))
                (r0, z0), (r1, z1) = prof[k], prof[k + 1]
                return r0 + (r1 - r0) * t, z0 + (z1 - z0) * t
            acc += d
        return prof[-1]

    def centre(self, z: float):
        """The stack's axis at height z: tipped by the lean, the top slumped."""
        h = self.p.height_m
        f = z / h
        off = self.lean * z + self.slump * f * f
        return (self.cx + off * math.cos(self.lean_dir), self.cy + off * math.sin(self.lean_dir))

    def lump(self, a: float, z: float) -> float:
        h = self.p.height_m
        v = 0.0
        for m, ph, tilt, amp in self.waves:
            v += amp * math.sin(m * a + ph + tilt * z / h * math.pi)
        for ba, bz, bw, bh, amp in self.blobs:
            da = _wrap(a - ba)
            v += amp * math.exp(-(da / bw) ** 2 - ((z - bz) / bh) ** 2)
        return v

    def eaten(self, a: float, z: float) -> float:
        """How far in (metres) the stack is cut or eaten at angle a, height z."""
        p = self.p
        if p.shape == "fed":
            bay = 0.0
            for m, ph, w in self.fed:
                bay += w * (0.5 + 0.5 * math.sin(m * a + ph))
            bay = 0.55 + 0.45 * bay / 2.3
            up = _smooth(z / 0.22) * 0.55 + 0.45
            down = 1.0 - _smooth((z - (self.fed_top - 0.35)) / 0.35)
            return self.fed_depth * bay * up * down
        if p.shape == "cut":
            da = abs(_wrap(a - self.cut_dir))
            if da >= self.cut_half + 0.25:
                return 0.0
            r_here, _ = self.section(self._s_at(z))
            # pulled from below, so the face leans back toward its top, and torn, not sawn
            rise = min(1.0, z / max(self.cut_top, 0.1))
            face = self.cut_in * p.radius_m * (1.0 + 0.45 * rise) / max(math.cos(min(da, 1.35)), 0.2)
            depth = max(0.0, r_here - face)
            ragged = (1.0 + 0.16 * math.sin(7.0 * a + 4.0 * z + 1.3) + 0.10 * math.sin(19.0 * a - 6.0 * z)
                      + 0.07 * math.sin(41.0 * a + 13.0 * z))
            side = 1.0 - _smooth((da - self.cut_half) / 0.25)
            # a hollow pulled out by hand and fork, highest in its middle and falling away
            # to its sides, never a doorway's square head
            head = self.cut_top * (1.0 - 0.55 * (min(da, self.cut_half) / self.cut_half) ** 2)
            top = 1.0 - _smooth((z - head) / 0.45)
            return depth * side * top * ragged
        return 0.0

    def _s_at(self, z: float) -> float:
        lo, hi = 0.0, self.arc_total
        for _ in range(30):
            mid = (lo + hi) / 2.0
            if self.section(mid)[1] < z:
                lo = mid
            else:
                hi = mid
        return lo

    def point(self, a: float, s: float):
        """The surface at angle a, arc length s: (x, y, z), how far eaten, the plain radius."""
        r, z = self.section(s)
        r_lumped = r * (1.0 + self.lump(a, z))
        e = min(self.eaten(a, z), 0.85 * r_lumped)
        rr = max(0.05, r_lumped - e)
        cx, cy = self.centre(z)
        return (cx + rr * math.cos(a), cy + rr * math.sin(a), z), e, r


def _tone(stack: _Stack, a: float, z: float, e: float, top_frac: float) -> float:
    """The vertex's brightness: damp and dark at the foot, shadowed under an overhang,
    each forkful its own, a new stack's crown a little greyed."""
    h = stack.p.height_m
    t = 0.72 + 0.28 * _smooth(z / 0.7)
    t *= 1.0 + 1.4 * stack.lump(a + 0.9, z * 1.3)
    if e > 0.03:
        # the pulled face is fresh hay, brighter than the weathered outside; the waist the
        # stock have eaten stands in the overhang's shadow
        t *= 1.12 if stack.p.shape == "cut" else 0.86 + 0.10 * _smooth(z / 0.6)
    if stack.p.condition == "new" and z > top_frac * h:
        t *= 0.90
    return round(max(0.45, min(1.25, t)), 3)


def _material(stack: _Stack, z: float, e: float) -> int:
    p = stack.p
    if e > 0.08:
        return M_HEART
    if p.condition == "weathered":
        return M_THATCH
    # A new stack's crown takes the weather first: the top fifth of it is greyed.
    return M_THATCH if z > 0.80 * p.height_m else M_HAY


def _uv(stack: _Stack, mat: int, a: float, s: float):
    span = MATERIALS[mat][3] or 1.0
    ou, ov = stack.offsets.get(mat, (0.0, 0.0))
    u = a * stack.p.radius_m / span + ou
    v = (stack.arc_total - s) / span + ov   # the sheet's stems run down it: v falls down the stack
    return (u, v)


def _body(m: _Mesh, stack: _Stack, conf: float) -> None:
    n = SEGMENTS
    angs = [2.0 * math.pi * i / n for i in range(n)]
    grid, eat = [], []
    for s in stack.ring_s:
        row, erow = [], []
        for a in angs:
            pt, e, _ = stack.point(a, s)
            row.append(pt)
            erow.append(e)
        grid.append(row)
        eat.append(erow)
    peak_z = stack.prof[-1][1]
    pcx, pcy = stack.centre(peak_z)
    peak = (pcx, pcy, peak_z)
    nr = len(grid)

    def normal(j, i):
        up = grid[min(j + 1, nr - 1)][i] if j + 1 < nr else peak
        dn = grid[max(j - 1, 0)][i]
        ar = _add(grid[j][(i + 1) % n], grid[j][(i - 1) % n], -1.0)
        mer = _add(up, dn, -1.0)
        nv = _norm(_cross(ar, mer))
        # outward: away from the axis at this height (or up, at the cap)
        cx, cy = stack.centre(grid[j][i][2])
        out = (grid[j][i][0] - cx, grid[j][i][1] - cy, 0.15)
        if nv[0] * out[0] + nv[1] * out[1] + nv[2] * out[2] < 0:
            nv = (-nv[0], -nv[1], -nv[2])
        return nv

    nrm = [[normal(j, i) for i in range(n)] for j in range(nr)]
    # A quad's material is decided by its own middle, so a cut face is one material.
    # Corners are shared within a material; the seam column (i = n) is its own vertex,
    # because the sheet's u runs on round it rather than back to 0.
    shared = {}

    def corner(mat, jj, ii):
        key = (mat, jj, ii)
        if key not in shared:
            a = 2.0 * math.pi * ii / n
            i0 = ii % n
            shared[key] = m.vert(mat, grid[jj][i0], nrm[jj][i0], _uv(stack, mat, a, stack.ring_s[jj]),
                                 _tone(stack, a, grid[jj][i0][2], eat[jj][i0], 0.8), conf)
        return shared[key]

    for j in range(nr - 1):
        for i in range(n):
            k = (i + 1) % n
            zc = (grid[j][i][2] + grid[j + 1][i][2]) / 2.0
            ec = (eat[j][i] + eat[j][k] + eat[j + 1][i] + eat[j + 1][k]) / 4.0
            mat = _material(stack, zc, ec)
            # (lo i, lo i+1, hi i+1, hi i) runs counter-clockwise seen from outside
            q = [corner(mat, j, i), corner(mat, j, i + 1), corner(mat, j + 1, i + 1), corner(mat, j + 1, i)]
            m.tri(mat, q[0], q[1], q[2])
            m.tri(mat, q[0], q[2], q[3])
    # The cap: a fan from the last ring to the peak.
    top = nr - 1
    mat = M_THATCH
    pk = m.vert(mat, peak, (0.0, 0.0, 1.0), _uv(stack, mat, 0.0, stack.arc_total), 0.85, conf)
    for i in range(n):
        k = (i + 1) % n
        a0, a1 = angs[i], angs[i] + 2 * math.pi / n
        v0 = m.vert(mat, grid[top][i], nrm[top][i], _uv(stack, mat, a0, stack.ring_s[top]),
                    _tone(stack, a0, grid[top][i][2], 0.0, 0.8), conf)
        v1 = m.vert(mat, grid[top][k], nrm[top][k], _uv(stack, mat, a1, stack.ring_s[top]),
                    _tone(stack, a1, grid[top][k][2], 0.0, 0.8), conf)
        m.tri(mat, v0, v1, pk)
    # The foot is closed so the stack is a solid from below.
    mat = M_THATCH
    fc = m.vert(mat, (stack.cx, stack.cy, 0.02), (0.0, 0.0, -1.0), (0.0, 0.0), 0.6, conf)
    ring = [m.vert(mat, grid[0][i], (0.0, 0.0, -1.0), (0.0, 0.0), 0.6, conf) for i in range(n)]
    for i in range(n):
        m.tri(mat, ring[(i + 1) % n], ring[i], fc)


def _tuft(m: _Mesh, mat: int, base, direction, side, length, width, droop, nrm, uv0, span, tone, conf):
    """One wisp of hay: a tapering strip from `base` along `direction`, bending down; six
    vertices, four triangles, lit with the surface's normal so it reads as the stack's."""
    tip = _add(_add(base, direction, length), (0.0, 0.0, -droop))
    mid = _add(_add(base, direction, 0.55 * length), (0.0, 0.0, -0.3 * droop))
    w0, w1, w2 = width / 2.0, width * 0.32, width * 0.08
    pts = [_add(base, side, -w0), _add(base, side, w0), _add(mid, side, -w1), _add(mid, side, w1),
           _add(tip, side, -w2), _add(tip, side, w2)]
    u0, v0 = uv0
    du = width / span
    uvs = [(u0, v0), (u0 + du, v0), (u0 + 0.33 * du, v0 - 0.55 * length / span),
           (u0 + 0.66 * du, v0 - 0.55 * length / span), (u0 + 0.45 * du, v0 - length / span),
           (u0 + 0.55 * du, v0 - length / span)]
    tones = [tone, tone, tone, tone, round(tone * 0.92, 3), round(tone * 0.92, 3)]
    ix = [m.vert(mat, pts[k], nrm, uvs[k], tones[k], conf) for k in range(6)]
    g = _cross(_add(pts[1], pts[0], -1.0), _add(pts[2], pts[0], -1.0))
    flip = g[0] * nrm[0] + g[1] * nrm[1] + g[2] * nrm[2] < 0
    for a, b, c in ((0, 1, 3), (0, 3, 2), (2, 3, 5), (2, 5, 4)):
        if flip:
            b, c = c, b
        m.tri(mat, ix[a], ix[b], ix[c])


def _surface_frame(stack: _Stack, a: float, s: float):
    """Point, outward normal, down-the-section tangent and round-the-stack tangent at (a, s)."""
    d = 0.02
    p, e, _ = stack.point(a, s)
    pu, _, _ = stack.point(a, min(s + d, stack.arc_total))
    pd, _, _ = stack.point(a, max(s - d, 0.0))
    pa, _, _ = stack.point(a + d, s)
    pb, _, _ = stack.point(a - d, s)
    down = _norm(_add(pd, pu, -1.0))
    around = _norm(_add(pa, pb, -1.0))
    n = _norm(_cross(around, _add(pu, pd, -1.0)))
    cx, cy = stack.centre(p[2])
    if n[0] * (p[0] - cx) + n[1] * (p[1] - cy) < 0:
        n = (-n[0], -n[1], -n[2])
    return p, e, n, down, around


def _tufts(m: _Mesh, stack: _Stack, conf: float) -> None:
    rng = random.Random(stack.p.seed ^ 0x5EED)
    h = stack.p.height_m
    s_max = stack.ring_s[-1]
    # Over the body: wisps lying down the slope, lifted a little off it.
    for _ in range(TUFTS):
        a = rng.uniform(0, 2 * math.pi)
        s = rng.uniform(0.04, 0.97) * s_max
        p, e, n, down, around = _surface_frame(stack, a, s)
        mat = _material(stack, p[2], e)
        lift = rng.uniform(0.15, 0.6)
        dirv = _norm(_add(down, n, lift))
        twist = rng.uniform(-0.45, 0.45)
        dirv = _norm(_add(dirv, around, twist))
        length = rng.uniform(0.14, 0.42)
        width = rng.uniform(0.035, 0.08)
        base = _add(p, n, -0.02)
        span = MATERIALS[mat][3]
        _tuft(m, mat, base, dirv, around, length, width, rng.uniform(0.0, 0.08) * length, n,
              _uv(stack, mat, a, s), span, round(rng.uniform(0.82, 1.18) * _tone(stack, a, p[2], e, 0.8), 3), conf)
    # Hanging from the girth, and from the lip of any overhang the stock have eaten under.
    for _ in range(EAVE_TUFTS):
        a = rng.uniform(0, 2 * math.pi)
        if stack.p.shape == "fed" and rng.random() < 0.6:
            z = stack.fed_top - rng.uniform(0.25, 0.45)
        elif stack.p.shape == "cut" and rng.random() < 0.35:
            a = stack.cut_dir + rng.uniform(-1, 1) * stack.cut_half
            z = rng.uniform(0.2, 1.0) * stack.cut_top
        else:
            z = rng.uniform(0.45, 0.75) * stack.p.shoulder_z_m
        s = stack._s_at(min(z, 0.9 * h))
        p, e, n, down, around = _surface_frame(stack, a, s)
        mat = _material(stack, p[2], e)
        dirv = _norm(_add((0.0, 0.0, -1.0), n, rng.uniform(0.2, 0.7)))
        dirv = _norm(_add(dirv, around, rng.uniform(-0.3, 0.3)))
        length = rng.uniform(0.18, 0.5)
        width = rng.uniform(0.04, 0.09)
        span = MATERIALS[mat][3]
        _tuft(m, mat, _add(p, n, -0.025), dirv, around, length, width, 0.05 * length, n,
              _uv(stack, mat, a, s), span, round(rng.uniform(0.8, 1.1) * _tone(stack, a, p[2], e, 0.8), 3), conf)


def _litter(m: _Mesh, stack: _Stack, conf: float) -> None:
    """Fallen and trodden hay round the foot, and the heaps of pulled hay."""
    rng = random.Random(stack.p.seed ^ 0x11773)
    p = stack.p
    n = SEGMENTS
    mat = M_THATCH if p.condition == "weathered" else M_HAY
    span = MATERIALS[mat][3]
    foot = p.profile()[0][0]
    waves = [(rng.randint(2, 6), rng.uniform(0, 2 * math.pi), rng.uniform(0.1, 0.3)) for _ in range(3)]
    reach = 0.65 if p.shape in ("fed", "cut") else 0.35
    rows = []
    for i in range(n + 1):
        a = 2.0 * math.pi * i / n
        w = 0.0
        for k, ph, amp in waves:
            w += amp * math.sin(k * a + ph)
        out = foot + reach * (1.0 + w)
        if p.shape == "cut":
            out += 0.5 * max(0.0, math.cos(_wrap(a - stack.cut_dir)))
        cx, cy = stack.centre(0.0)
        rin = 0.80 * foot
        rmid = (rin + out) / 2.0
        rows.append([(cx + r * math.cos(a), cy + r * math.sin(a), z)
                     for r, z in ((rin, 0.16), (rmid, 0.07), (out, -0.05))])
    for i in range(n):
        for j in range(2):
            pts = [rows[i][j], rows[i][j + 1], rows[i + 1][j + 1], rows[i + 1][j]]
            uvs = [(pt[0] / span, pt[1] / span) for pt in pts]
            tones = [0.78 if jj == 0 else 0.86 for jj in (j, j + 1, j + 1, j)]
            m.quad(mat, pts, [(0.0, 0.0, 1.0)] * 4, uvs, tones, conf)
    for _ in range(LITTER_TUFTS):
        a = rng.uniform(0, 2 * math.pi)
        r = foot * rng.uniform(0.95, 1.0) + rng.uniform(0.0, reach + 0.2)
        cx, cy = stack.centre(0.0)
        base = (cx + r * math.cos(a), cy + r * math.sin(a), 0.04)
        b = a + rng.uniform(-1.2, 1.2)
        dirv = _norm((math.cos(b), math.sin(b), rng.uniform(-0.05, 0.12)))
        side = _norm(_cross((0.0, 0.0, 1.0), dirv))
        _tuft(m, mat, base, dirv, side, rng.uniform(0.15, 0.35), rng.uniform(0.04, 0.08), 0.02,
              (0.0, 0.0, 1.0), (base[0] / span, base[1] / span), span,
              round(rng.uniform(0.75, 1.05), 3), conf)
    # Heaps of pulled hay: where hay was cut from the side, and where the stock were fed.
    heaps = []
    if p.shape == "cut":
        heaps.append((stack.cut_dir + rng.uniform(-0.3, 0.3), foot + 0.55, rng.uniform(0.55, 0.8)))
        heaps.append((stack.cut_dir + rng.uniform(0.5, 0.9), foot + 0.85, rng.uniform(0.35, 0.5)))
    elif p.shape == "fed":
        heaps.append((rng.uniform(0, 2 * math.pi), foot + 0.55, rng.uniform(0.45, 0.65)))
    for ha, hr, rad in heaps:
        cx, cy = stack.centre(0.0)
        hx, hy = cx + hr * math.cos(ha), cy + hr * math.sin(ha)
        _heap(m, rng, (hx, hy), rad, rad * rng.uniform(0.45, 0.6), conf)


def _heap(m: _Mesh, rng, centre, rad, height, conf) -> None:
    """A loose heap of pulled hay: a low lumpy dome, wisps over it."""
    mat = M_HEART
    span = MATERIALS[mat][3]
    n, rings = 20, 6
    phs = [(rng.randint(2, 5), rng.uniform(0, 2 * math.pi), rng.uniform(0.05, 0.14)) for _ in range(3)]
    grid = []
    for j in range(rings + 1):
        t = j / rings
        row = []
        for i in range(n):
            a = 2 * math.pi * i / n
            w = 1.0
            for k, ph, amp in phs:
                w += amp * math.sin(k * a + ph + 2.0 * t)
            r = rad * w * math.cos(t * math.pi / 2.0)
            z = height * math.sin(t * math.pi / 2.0) ** 0.8 - 0.04
            row.append((centre[0] + r * math.cos(a), centre[1] + r * math.sin(a), z))
        grid.append(row)
    for j in range(rings):
        for i in range(n):
            k = (i + 1) % n
            pts = [grid[j][i], grid[j][k], grid[j + 1][k], grid[j + 1][i]]
            ns = []
            for pt in pts:
                ns.append(_norm((pt[0] - centre[0], pt[1] - centre[1], 0.6 * rad + pt[2])))
            uvs = [(pt[0] / span, (pt[1] + pt[2]) / span) for pt in pts]
            tones = [round(0.8 + 0.25 * (pt[2] / height), 3) for pt in pts]
            m.quad(mat, pts, ns, uvs, tones, conf)
    for _ in range(30):
        a = rng.uniform(0, 2 * math.pi)
        r = rad * rng.uniform(0.1, 0.9)
        z = height * math.cos(r / rad * math.pi / 2.0) - 0.03
        base = (centre[0] + r * math.cos(a), centre[1] + r * math.sin(a), max(z, 0.0))
        b = a + rng.uniform(-1.5, 1.5)
        dirv = _norm((math.cos(b), math.sin(b), rng.uniform(-0.2, 0.5)))
        side = _norm(_cross((0.0, 0.0, 1.0), dirv))
        _tuft(m, mat, base, dirv, side, rng.uniform(0.15, 0.3), rng.uniform(0.04, 0.07), 0.05,
              _norm((math.cos(a), math.sin(a), 1.0)), (base[0] / span, base[1] / span), span,
              round(rng.uniform(0.85, 1.15), 3), conf)


def _beam(m: _Mesh, path, side_m: float, conf: float) -> None:
    """A square timber along a polyline: four faces, flat-shaded, capped at its ends."""
    h = side_m / 2.0
    frames = []
    for k, p in enumerate(path):
        q0 = path[max(k - 1, 0)]
        q1 = path[min(k + 1, len(path) - 1)]
        t = _norm(_add(q1, q0, -1.0))
        ref = (0.0, 0.0, 1.0) if abs(t[2]) < 0.9 else (1.0, 0.0, 0.0)
        u = _norm(_cross(t, ref))
        v = _norm(_cross(t, u))
        frames.append([_add(_add(p, u, sx * h), v, sy * h)
                       for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))])
    for k in range(len(path) - 1):
        a, b = frames[k], frames[k + 1]
        for f in range(4):
            g = (f + 1) % 4
            pts = [a[f], a[g], b[g], b[f]]
            nv = _norm(_cross(_add(pts[1], pts[0], -1.0), _add(pts[3], pts[0], -1.0)))
            m.quad(M_POLE, pts, [nv] * 4, [(0.0, 0.0)] * 4, [1.0] * 4, conf)
    for fr, sgn in ((frames[0], -1.0), (frames[-1], 1.0)):
        nv = _norm(_cross(_add(fr[1], fr[0], -1.0), _add(fr[3], fr[0], -1.0)))
        nv = (sgn * nv[0], sgn * nv[1], sgn * nv[2])
        m.quad(M_POLE, fr, [nv] * 4, [(0.0, 0.0)] * 4, [1.0] * 4, conf)


def _poles(m: _Mesh, stack: _Stack, conf: float) -> None:
    p = stack.p
    h = p.height_m
    if p.stack_pole:
        # The pole the stack was built round, standing clear of the peak, following the
        # stack's lean; it starts inside the top so no gap shows where it leaves the hay.
        z0, z1 = h - 0.6, h + POLE_ABOVE_M
        c0, c1 = stack.centre(z0), stack.centre(h)
        k = POLE_ABOVE_M / 0.6
        top = (c1[0] + (c1[0] - c0[0]) * k + 0.05, c1[1] + (c1[1] - c0[1]) * k + 0.03, z1)
        _beam(m, [(c0[0], c0[1], z0), (c1[0], c1[1], h), top], POLE_SIDE_M * 1.15, conf)
    if p.rider_poles:
        # Two pairs of poles tied over the peak, each pair straddling it and lying down
        # its sides, to hold the top against the wind.
        rng = random.Random(p.seed ^ 0x9013)
        a0 = rng.uniform(0, math.pi)
        s_lo = stack._s_at(0.55 * h)
        for pair in range(2):
            a = a0 + pair * math.pi / 2.0 + rng.uniform(-0.12, 0.12)
            path = []
            steps = 7
            for k in range(steps, -1, -1):
                s = s_lo + (stack.ring_s[-1] - s_lo) * k / steps
                pt, _, _ = stack.point(a, s)
                _, _, nv, _, _ = _surface_frame(stack, a, s)
                path.append(_add(pt, nv, 0.05))
            pk = stack.centre(h)
            path.append((pk[0], pk[1], h + 0.04))
            for k in range(steps + 1):
                s = s_lo + (stack.ring_s[-1] - s_lo) * (steps - k) / steps
                pt, _, _ = stack.point(a + math.pi, s)
                _, _, nv, _, _ = _surface_frame(stack, a + math.pi, s)
                path.append(_add(pt, nv, 0.05))
            _beam(m, path, 0.065, conf)


def mesh(params: HaystackParams) -> _Mesh:
    """The stack's vertices, its foot's centre at the middle of the footprint square."""
    params.validate()
    m = _Mesh()
    conf = params.worst_conf("diameter_m", "height_m", "condition", "shape")
    pole_conf = params.worst_conf("stack_pole")
    stack = _Stack(params)
    _body(m, stack, conf)
    _tufts(m, stack, conf)
    _litter(m, stack, conf)
    _poles(m, stack, pole_conf)
    return m


def material_specs(params: HaystackParams) -> list[tuple[str, tuple, float]]:
    return [(name, rgba, rough) for name, rgba, rough, _ in MATERIALS]


def _pad(blob: bytes, fill: bytes = b"\x00") -> bytes:
    return blob + fill * ((4 - len(blob) % 4) % 4)


def glb(params: HaystackParams, structure_id: str, phase_id: str) -> bytes:
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
        if MATERIALS[mi][3] is not None:
            # The sheet's tile coordinates, as `_UV` and not TEXCOORD_0: no texture rides
            # in the GLB (camp-surfaces.js binds the library's sheet by the material's
            # name), so the web derivative's prune would drop a TEXCOORD_0 nothing samples.
            uv = [(round(u, 4), round(1.0 - v, 4)) for u, v in part["uv"]]
            attrs["_UV"] = accessor(uv, 5126, "VEC2", 2, 34962)
        if any(abs(t - 1.0) > 1e-6 for t in part["tone"]):
            attrs["_TONE"] = accessor(part["tone"], 5126, "SCALAR", 1, 34962)
        used.append(mi)
        idx = part["idx"]
        prims.append({"attributes": attrs,
                      "indices": accessor(idx, 5123 if len(pos) < 65536 else 5125, "SCALAR", 1, 34963),
                      "material": len(used) - 1})
    mats = []
    for mi in used:
        name, rgba, r, _span = MATERIALS[mi]
        mats.append({"name": name, "doubleSided": True, "pbrMetallicRoughness": {
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
