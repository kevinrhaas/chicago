"""palisade — a picket stockade or a worm rail fence standing on a footprint outline.

The first archetype in this project that builds a BOUNDARY rather than a building,
and the two things it makes are the enclosure of Fort Dearborn and the fence round
the garrison's garden.

**Orientation.** As everywhere else, the facade faces NORTH at rotation_deg 0, which
in Blender is the +y face (docs/GLB-CONTRACT.md; the exporter's export_yup=True maps
Blender +Y to glTF -Z, which the contract defines as north). For a stockade "facade"
means the wall the record calls the north wall, and the gate the record puts on `n`
is cut in that wall.

**A picket is a post, not a plank.** Every picket is an individual object with a
sharpened head, because a stockade read as a smooth extruded ribbon is the single
most recognisable way to get a frontier fort wrong, and because the confidence view
has to be able to dither the wall without dithering a texture. The cost is honest
and bounded: `PalisadeParams.picket_count` states it before the bake runs, and Fort
Dearborn's 212 m of curtain comes out near 700 posts at twelve triangles each.

**What is deliberately NOT built.** No ditch, no berm, no banquette, no walkway and
no loopholes in the curtain — none of the five is attested at this fort, and each
would be a claim about how it was defended rather than about what it looked like.
Wau-Bun's "small posterns here and there" are also absent: "here and there" is not a
position, and putting a postern somewhere would invent the one thing the sentence
declines to give. Both absences are recorded on the structure and admitted in
docs/LIBERTIES.md.

**Face winding.** Every quad is wound so its normal points out of the solid, per the
contract, even though Blender's default material exports doubleSided.
"""

from __future__ import annotations

import math
import sys
import zlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from common.logwork import HEWN_RGBA  # noqa: E402
from common import materials  # noqa: E402
from common.mesh import MeshBuilder, ROOF_RGBA, simple_material  # noqa: E402
from archetypes.palisade_params import PalisadeParams  # noqa: E402

M_PICKET, M_TIMBER, M_DARK = 0, 1, 2

# A gate leaf and its frame are sawn, heavier, and darker with weather than the
# split pickets beside them; the difference is what makes a gate read as a gate at
# fifty metres rather than as a hole.
GATE_RGBA = (0.38, 0.31, 0.24, 1.0)


class TonedBuilder(MeshBuilder):
    """MeshBuilder plus `_TONE`, a per-vertex multiplier on albedo (T-2123).

    A COPY of `fort_structure.TonedBuilder`, and the docstring there says why it
    is not shared from generators/common/ (every asset in the town would re-bake).
    Here it gives every picket its own weathering: a stockade of seven hundred
    posts cut from seven hundred trees, not one board painted seven hundred times.
    """

    def __init__(self, name: str):
        super().__init__(name)
        self.tone: list[float] = []
        self.tone_fn = None

    def add_poly(self, points, confidence: float, mat: int = 0) -> list[int]:
        idx = super().add_poly(points, confidence, mat)
        if self.tone_fn is None:
            self.tone.extend([1.0] * len(points))
        else:
            n = float(len(points))
            c = (sum(p[0] for p in points) / n, sum(p[1] for p in points) / n,
                 sum(p[2] for p in points) / n)
            self.tone.extend(float(self.tone_fn(p, c, mat)) for p in points)
        return idx

    def to_object(self, materials=None):
        ob = super().to_object(materials)
        if any(abs(t - 1.0) > 1e-6 for t in self.tone):
            attr = ob.data.attributes.new(name="_TONE", type="FLOAT", domain="POINT")
            for i, t in enumerate(self.tone):
                attr.data[i].value = t
        return ob


def _unit(name: str, *keys) -> float:
    """A stable number in [0, 1) from a name and some integers (crc32, so every
    bake deals the same picket the same irregularity)."""
    return (zlib.crc32(("|".join([name, *map(str, keys)])).encode()) & 0xFFFFFF) / float(0x1000000)


# THE PICKETS ARE SPLIT TIMBER, AND NO TWO ARE ALIKE (T-2123). Every number below
# is RECONSTRUCTED and L384 owns them. What bounds them: the record's own reading
# of "pickets" — "split or roughly squared timber posts set upright" (construction,
# on fort_dearborn_palisade) — and the owner's report that the wall read as plain.
# A split post has a flat face where the log was riven and a rounded back where
# the bark was; set by hand, it stands a little turned. Its HEIGHT stays the
# record's: tools/measure_picket_plate.py gates the point as cut from a picket of
# exactly that height, and a line sawn level is what a stockade's top was. Until this ticket all seven hundred were the
# same squared post to the millimetre, which is what made the curtain read as a
# manufactured fence.
#: How much narrower than the record's face a picket may be (never wider, so no
#: post can overlap its neighbour).
PICKET_NARROW = 0.14
#: How far one picket is turned about its own axis, at most, either way.
PICKET_TURN_DEG = 5.0
#: How far one picket's weathering differs from the next. The plank walk's board
#: span is 0.14 (frontage.js); a post from another tree, set another year, more.
PICKET_SPAN = 0.18
#: Foot and head of every post: the foot stands in splash and damp and is
#: darker; the head is bleached. Interpolated up the post.
PICKET_FOOT_K = 0.78
PICKET_HEAD_K = 1.06
#: The ribbands: two horizontal timbers spiked across the INSIDE of the curtain,
#: which is what holds a picket line straight once the posts start to work in the
#: ground. Standard frontier stockade practice; not attested at this fort.
RIBBAND_HALF_T = 0.05
RIBBAND_H = 0.16
RIBBAND_AT = (0.85, 0.80)   # metres above the ground, and below the head


def build(params: PalisadeParams, name: str):
    """Build the enclosure. Returns a Blender object at the local origin."""
    params.validate()
    b = TonedBuilder(name)

    if params.wall_kind == "worm_fence":
        _worm_fence(b, params)
    else:
        _stockade(b, params)

    mats = [
        # 0.93 was this module's own number; the sheet gives hewn log 0.92, and
        # T-0007 converges the three stray log surfaces onto it so that every log
        # in the town traces to one row of docs/RESEARCH/materials.md.
        simple_material("log", HEWN_RGBA,
                        roughness=materials.SUBSTRATES["hewn_log"].roughness),
        # NOT A ROOF, and it never was: this slot draws the two gate leaves. It was
        # called `roof` because `M_ROOF` is the index the shared mesh helpers use for
        # a second material, and the name came along for the ride. Renamed at T-1487,
        # when every other `roof` material in the town started stating its covering —
        # a gate that claims to be a roof would be the one exception to that sentence.
        simple_material("gate", GATE_RGBA, roughness=0.88),
        # ONE DARK (T-0126) — the sheet's `DARK` row. Here it is the two shut gate
        # leaves, drawn dark so the gate reads as closed rather than as a gap; the
        # row's note records that use alongside the openings it is named for.
        simple_material("dark", materials.DARK.rgba,
                        roughness=materials.DARK.roughness),
    ]
    return b.to_object(mats)


# ------------------------------------------------------------------- stockade

def _stockade(b: MeshBuilder, p: PalisadeParams) -> None:
    """The picket curtain, its gates and its corner works.

    The curtain of each side is built as a list of intervals along that side with
    the gate opening and the two corner returns removed, so a bastion and a gate
    can never leave a picket standing inside either of them.
    """
    c_wall = p.worst_conf("wall_kind", "picket_height_m", "construction")
    c_gate = p.conf("gate_sides", "reconstructed")
    c_bast = p.conf("bastion_corners", "reconstructed")
    w, d = p.width_m, p.depth_m

    # (side, along-axis run length, the two endpoints in plan)
    sides = {
        "s": ((0.0, 0.0), (w, 0.0)),
        "e": ((w, 0.0), (w, d)),
        "n": ((w, d), (0.0, d)),
        "w": ((0.0, d), (0.0, 0.0)),
    }
    # which corner sits at which end of each side, in the order the side is walked
    corner_at = {
        "s": ("sw", "se"), "e": ("se", "ne"), "n": ("ne", "nw"), "w": ("nw", "sw"),
    }

    for side, (a, z) in sides.items():
        run = math.dist(a, z)
        cuts = []
        if side in p.gate_sides:
            half = p.gate_width_m / 2.0
            cuts.append((run / 2.0 - half, run / 2.0 + half))
        for end, corner in zip((0.0, run), corner_at[side]):
            if corner in p.bastion_corners:
                lo, hi = (0.0, p.bastion_length_m) if end == 0.0 else \
                         (run - p.bastion_length_m, run)
                cuts.append((lo, hi))
        for t0, t1 in _intervals(run, cuts):
            _picket_run(b, p, _lerp(a, z, t0 / run), _lerp(a, z, t1 / run), c_wall)

    for corner in p.bastion_corners:
        _bastion(b, p, corner, c_bast)
    for side in p.gate_sides:
        _gate(b, p, side, c_gate)


def _lerp(a, z, t):
    return (a[0] + (z[0] - a[0]) * t, a[1] + (z[1] - a[1]) * t)


def _intervals(run: float, cuts: list) -> list:
    """`[0, run]` with every cut interval removed, merged and sorted."""
    keep = [(0.0, run)]
    for c0, c1 in sorted(cuts):
        out = []
        for k0, k1 in keep:
            if c1 <= k0 or c0 >= k1:
                out.append((k0, k1))
                continue
            if c0 > k0:
                out.append((k0, min(c0, k1)))
            if c1 < k1:
                out.append((max(c1, k0), k1))
        keep = out
    return [(a, z) for a, z in keep if z - a > 1e-6]


def _picket_run(b: MeshBuilder, p: PalisadeParams, a, z, conf: float) -> None:
    """Pickets standing shoulder to shoulder from `a` to `z` in plan.

    Spacing is honoured as a target and then divided evenly into the run, so a
    wall does not end with a half-gap and two runs either side of a gate stay in
    step with each other.
    """
    run = math.dist(a, z)
    n = max(1, int(round(run / p.picket_spacing_m)))
    step = run / n
    ux, uy = (z[0] - a[0]) / run, (z[1] - a[1]) / run
    nx, ny = -uy, ux                                    # unit normal, in plan
    hw = min(p.picket_width_m, step) / 2.0
    ht = p.picket_width_m / 2.0
    for i in range(n):
        t = (i + 0.5) * step
        cx, cy = a[0] + ux * t, a[1] + uy * t
        _picket(b, p, cx, cy, ux, uy, nx, ny, hw, ht, conf)
    # The ribbands, on the side the run's normal points to — inside the curtain
    # (each side and each bastion return is walked so that +n is inward).
    if p.wall_kind == "picket_stockade" and run > 0.6:
        inner = ht + RIBBAND_HALF_T
        lo_z = RIBBAND_AT[0]
        hi_z = p.picket_height_m - p.picket_point_m - RIBBAND_AT[1]
        for z0 in (lo_z, hi_z):
            _beam(b, (a[0] + nx * inner, a[1] + ny * inner),
                  (z[0] + nx * inner, z[1] + ny * inner), nx, ny, RIBBAND_HALF_T,
                  z0, z0 + RIBBAND_H, conf, M_TIMBER)


def _picket(b: MeshBuilder, p: PalisadeParams, cx, cy, ux, uy, nx, ny,
            hw, ht, conf: float) -> None:
    """One split post with a sharpened head, in the run's own axes.

    Built from its own axes rather than as an axis-aligned box, so the same
    function serves the curtain, the returns of a bastion and the flanks of a
    gate without any of them having to be parallel to x or y.

    A six-sided section since T-2123: the riven face flat on the inside of the
    curtain, the back chamfered where the round of the log was, so from outside
    the wall reads as a row of timbers rather than of boards. Height, width, turn,
    the lean of the point and the weathering are each the post's own, from a hash
    of where it stands (the constants above; L384). Eighteen triangles, up from
    twelve: six-sided shaft, six-triangle head.
    """
    def r(k):
        return 2.0 * _unit(b.name, "picket", round(cx * 100), round(cy * 100), k) - 1.0

    # Height and head stay the record's to the millimetre: the stockade was cut
    # to a line, and tools/measure_picket_plate.py gates the point as CUT FROM a
    # picket of the record's height. The variety is in the section and the wood.
    height = p.picket_height_m
    head = p.picket_point_m
    shaft = height - head
    hw = hw * (1.0 - PICKET_NARROW * 0.5 * (r(2) + 1.0))
    turn = math.radians(PICKET_TURN_DEG * r(3))
    cs, sn = math.cos(turn), math.sin(turn)
    au, av = ux * cs - nx * sn, uy * cs - ny * sn       # the turned run axis
    an, bn = -av, au                                    # and its normal

    def at(u, v):
        return (cx + au * u + an * v, cy + av * u + bn * v)

    # counter-clockwise from above in (along, normal): inner face at +ht
    section = [at(-hw, -0.25 * ht), at(-0.55 * hw, -ht), at(0.55 * hw, -ht),
               at(hw, -0.25 * ht), at(hw, ht), at(-hw, ht)]
    lean = hw * 0.35 * r(4)
    apex = (*at(lean, 0.0), height)
    k = 1.0 + PICKET_SPAN * r(5)

    def tone(pt, _c, mat):
        if mat != M_PICKET:
            return 1.0
        f = max(0.0, min(1.0, pt[2] / height))
        return k * (PICKET_FOOT_K + (PICKET_HEAD_K - PICKET_FOOT_K) * f)

    prev = b.tone_fn
    b.tone_fn = tone
    n = len(section)
    for i in range(n):
        (x0, y0), (x1, y1) = section[i], section[(i + 1) % n]
        b.add_poly([(x0, y0, 0.0), (x1, y1, 0.0),
                    (x1, y1, shaft), (x0, y0, shaft)], conf, M_PICKET)
    for i in range(n):
        (x0, y0), (x1, y1) = section[i], section[(i + 1) % n]
        b.add_poly([(x0, y0, shaft), (x1, y1, shaft), apex], conf, M_PICKET)
    b.tone_fn = prev


def _bastion(b: MeshBuilder, p: PalisadeParams, corner: str, conf: float) -> None:
    """One corner work: the picket line leaving the wall, projecting, and returning.

    A bastion of this class is a re-entrant of the curtain and nothing else — no
    floor, no roof, nothing inside it. That is what distinguishes it from the
    blockhouse at the south-west angle, which is a building and has its own record.
    """
    w, d = p.width_m, p.depth_m
    L, P = p.bastion_length_m, p.bastion_projection_m
    sx, sy = (1.0 if corner in ("ne", "se") else -1.0,
              1.0 if corner in ("ne", "nw") else -1.0)
    ox, oy = (w if sx > 0 else 0.0), (d if sy > 0 else 0.0)
    path = [
        (ox - sx * L, oy),
        (ox - sx * L, oy + sy * P),
        (ox + sx * P, oy + sy * P),
        (ox + sx * P, oy - sy * L),
        (ox, oy - sy * L),
    ]
    for a, z in zip(path, path[1:]):
        _picket_run(b, p, a, z, conf)


def _gate(b: MeshBuilder, p: PalisadeParams, side: str, conf: float) -> None:
    """A gateway in one wall: two heavy jamb posts, a lintel, and two leaves.

    The leaves are hung shut. A fort with its gates standing open makes a claim
    about the hour of the day; a fort with them shut makes a claim about a
    garrison that is there, and the garrison IS attested for 1835-07-01 while
    nothing describes the gates being worked. See docs/RESEARCH/fort_dearborn.md.
    """
    w, d = p.width_m, p.depth_m
    if side in ("n", "s"):
        cx, cy = w / 2.0, (d if side == "n" else 0.0)
        ux, uy = 1.0, 0.0
    else:
        cx, cy = (w if side == "e" else 0.0), d / 2.0
        ux, uy = 0.0, 1.0
    nx, ny = -uy, ux
    half = p.gate_width_m / 2.0
    jamb = 0.20
    head = p.picket_height_m * 0.86

    for s in (-1.0, 1.0):
        jx, jy = cx + ux * (half + jamb) * s, cy + uy * (half + jamb) * s
        _post(b, jx, jy, ux, uy, nx, ny, jamb, 0.17, p.picket_height_m + 0.10,
              conf, M_TIMBER)
    # lintel across the head
    _beam(b, (cx - ux * (half + jamb * 2), cy - uy * (half + jamb * 2)),
          (cx + ux * (half + jamb * 2), cy + uy * (half + jamb * 2)),
          nx, ny, 0.14, head, head + 0.26, conf, M_TIMBER)
    # Two leaves, shut: each one runs from the meeting stile at the centre of the
    # gateway out to its own jamb, so the pair covers the opening exactly and
    # neither reaches past the frame.
    #
    # This used to derive each leaf from a midpoint — `a` an end, `z` the other
    # end, then half a gate width either side of `(a + z) / 2`. For the left leaf
    # `a` was the centre and it came out right; for the right leaf the selector
    # made `a` the jamb as well, so `a` and `z` were the same point, the midpoint
    # landed ON the jamb, and the leaf was built centred there. On Fort Dearborn's
    # 3.6 m gateway that left 0.90 m of it standing open with daylight through the
    # wall, and put 0.90 m of leaf out past the opening across the pickets — in
    # both documented gates, in the committed GLB. Held now by
    # tools/measure_fort_gates.py, which reads the shipped mesh rather than
    # re-deriving these two lines, because the derivation was the fault.
    for s in (-1.0, 1.0):
        _beam(b, (cx, cy), (cx + ux * half * s, cy + uy * half * s),
              nx, ny, 0.055, 0.02, head - 0.05, conf, M_DARK)


def _post(b: MeshBuilder, cx, cy, ux, uy, nx, ny, hw, ht, height,
          conf: float, mat: int) -> None:
    """A squared post standing on the ground, in the run's own axes."""
    corners = [
        (cx - ux * hw - nx * ht, cy - uy * hw - ny * ht),
        (cx + ux * hw - nx * ht, cy + uy * hw - ny * ht),
        (cx + ux * hw + nx * ht, cy + uy * hw + ny * ht),
        (cx - ux * hw + nx * ht, cy - uy * hw + ny * ht),
    ]
    for i in range(4):
        (x0, y0), (x1, y1) = corners[i], corners[(i + 1) % 4]
        b.add_poly([(x0, y0, 0.0), (x1, y1, 0.0),
                    (x1, y1, height), (x0, y0, height)], conf, mat)
    b.add_poly([(x, y, height) for x, y in corners], conf, mat)


def _beam(b: MeshBuilder, a, z, nx, ny, ht, z0, z1, conf: float, mat: int) -> None:
    """A horizontal member from `a` to `z` in plan, `ht` half-thick across the run,
    running from z0 to z1 in height. All six faces, outward."""
    lo = [(a[0] - nx * ht, a[1] - ny * ht), (z[0] - nx * ht, z[1] - ny * ht),
          (z[0] + nx * ht, z[1] + ny * ht), (a[0] + nx * ht, a[1] + ny * ht)]
    for i in range(4):
        (x0, y0), (x1, y1) = lo[i], lo[(i + 1) % 4]
        b.add_poly([(x0, y0, z0), (x1, y1, z0), (x1, y1, z1), (x0, y0, z1)], conf, mat)
    b.add_poly([(x, y, z1) for x, y in lo], conf, mat)
    b.add_poly([(x, y, z0) for x, y in reversed(lo)], conf, mat)


# ----------------------------------------------------------------- worm fence

def _worm_fence(b: MeshBuilder, p: PalisadeParams) -> None:
    """A zigzag rail fence round the enclosure.

    A worm fence has no posts: split rails are stacked in alternating panels that
    lean on each other at the angles, which is why it is drawn as a zigzag on a
    period survey and why it needs no hole dug anywhere. The zigzag is the whole
    identity of the thing, so it is built rather than approximated by a straight
    run of rails.
    """
    conf = p.worst_conf("wall_kind", "fence_height_m")
    w, d = p.width_m, p.depth_m
    loop = [(0.0, 0.0), (w, 0.0), (w, d), (0.0, d), (0.0, 0.0)]
    for a, z in zip(loop, loop[1:]):
        _worm_run(b, p, a, z, conf)


def _worm_run(b: MeshBuilder, p: PalisadeParams, a, z, conf: float) -> None:
    run = math.dist(a, z)
    n = max(1, int(round(run / p.panel_length_m)))
    step = run / n
    ux, uy = (z[0] - a[0]) / run, (z[1] - a[1]) / run
    nx, ny = -uy, ux
    rail_h = p.fence_height_m / p.rail_courses
    for i in range(n):
        s = 1.0 if i % 2 == 0 else -1.0
        t0, t1 = i * step, (i + 1) * step
        p0 = (a[0] + ux * t0 + nx * p.panel_offset_m * -s,
              a[1] + uy * t0 + ny * p.panel_offset_m * -s)
        p1 = (a[0] + ux * t1 + nx * p.panel_offset_m * s,
              a[1] + uy * t1 + ny * p.panel_offset_m * s)
        for k in range(p.rail_courses):
            z0 = k * rail_h + rail_h * 0.18
            _beam(b, p0, p1, nx, ny, 0.055, z0, z0 + rail_h * 0.62,
                  conf, M_PICKET if k % 2 == 0 else M_TIMBER)
