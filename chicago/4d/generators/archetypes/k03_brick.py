"""K03 brick on a K01 assembly: the service walls of 1808 Prairie (T-2291).

TICKET T-2291, piece 2 of T-1845 (package K03 of the T-1837 Prairie programme). Piece 1,
T-2290, built the brick library `assets/textures/prairie_1904_brick/` and wrote the bond,
joint and special rules as data in its `profiles.json`. This module reads that file and
lays it on the walls `k01_frontage.py` builds. Nothing here is a number of its own that
the profiles already state: the module, the joint, the rowlock, the soldier, the arch
ratios and the string-course projection all come out of `profiles.json`.

THE TARGET. 1808 Prairie (`pa-1808-6`) is the one house in the 1904 scene whose register
entry asks for common brick: "Common-brick side and rear ranges", against a rock-faced
stone street front. Until this ticket those three walls wore Glessner v4's courtyard
`brick_buff` — the one thing T-1845's acceptance names as wrong ("no Glessner courtyard
colour applied indiscriminately"). The comparison the ticket asks for is therefore the
house's own: its street front against its common-brick return and rear.

WHAT IS LAID, and why each is the form it is:

  walls     the `common_buff_common_6` panel — common buff brick in common bond, a header
            course every sixth, 9 mm weathered lime joints — with its OpenGL normal map.
            The panel is the library's balanced/light form; the full form (every brick a
            solid) was priced and refused here: the three walls hold about 52,000 bricks
            and the 1904 scene already spends 2.5 M of its 3.8 M triangles on Glessner.
  bond      courses registered at grade on every wall (v = 0 on a bed joint), and the
            perpends phased so the bond turns the two brick-to-brick quoins unbroken
            (`corner_return`): the north party wall ends its first course on a whole
            stretcher at the north-west quoin and the rear wall begins that course with a
            header-length return. The south-west quoin takes the cut the rear wall's
            length leaves, the way a mason's closer does.
  heads     two rowlock rings on a segmental arch over the principal- and second-floor
            windows (`segmental_arch`: rise 0.12 of the span, joints wedge, bricks stay
            rectangular). The third storey's heads sit 0.37 m under the soffit; two rings and
            their rise (0.34 m) would leave no course between arch and eave, so they take a
            soldier flat head instead.
  string    one projecting stretcher course at the second-floor line on the south wall and
            the rear, turning the south-west quoin. The north wall is a blank party wall
            against the Glessner court and carries none.
  condition the soot/damp mask the library leaves out of its maps on purpose
            (`profiles.json` `condition`): rising damp darkens the first 0.6 m above grade,
            and soot the sheltered band under the eave. It rides the vertex channel
            `_TONE`, which the renderer multiplies into colour (buildings.js
            applyPieceTone), so the clean 1904 body and the dirt stay separable.

Each unit (rowlock, soldier, string-course stretcher) draws ONE firing variant by weight
from a generator seeded by (component seed, course, unit) — the library's
`variation_rule` — and wears the joint-free `common_buff` fabric at its own offset.
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LIBRARY = ROOT / "assets" / "textures" / "prairie_1904_brick"
PROFILES = json.loads((LIBRARY / "profiles.json").read_text())

FABRIC = "common_buff"            # the register's "common brick"
PANEL = "common_buff_common_6"     # its common-bond panel
_fab = PROFILES["fabrics"][FABRIC]
_unit = _fab["unit"]
MODULE = _unit["module_m"]                       # 0.2159 along a course
COURSE = _unit["course_m"]                       # 0.066675 a course
JOINT = _fab["joint"]["width_m"]                 # 0.009
BRICK_H = _unit["stretcher_m"][1]                # 0.057675, a brick's face height
STRETCHER = _unit["stretcher_m"][0]              # 0.2069
BED = _unit["bed_depth_m"]                       # 0.1016, a rowlock's radial depth
_arch = PROFILES["specials"]["segmental_arch"]
RISE_TO_SPAN = 0.12                              # inside _arch["rise_to_span"]
RINGS = 2                                        # inside _arch["rings"]
SOLDIER_W = round(COURSE * 1.5 - JOINT, 4)       # specials.soldier.width_m
SOLDIER_H = round(MODULE - JOINT, 4)             # specials.soldier.height_m
STRING_PROUD = 0.018                             # inside string_course "0.012-0.025 m proud"
STRING_WEATHER = 0.006                           # the sloped top's fall, front to back
UNIT_PROUD = 0.012                               # an arch or soldier unit's face relief

assert _arch["rise_to_span"][0] <= RISE_TO_SPAN <= _arch["rise_to_span"][1]
assert _arch["rings"][0] <= RINGS <= _arch["rings"][1]

# The soot/damp mask, in metres above grade and below the soffit. Reconstructed, and
# recorded as L-k03-1808-service-brick-2291: a sheltered eave band and a splash zone,
# the two places a sooted city wall darkens first; neither is read off a photograph.
DAMP_TOP_M, DAMP_TONE = 0.60, 0.74
SOOT_DEPTH_M, SOOT_TONE = 1.60, 0.80


def _material(group: str, ident: str) -> dict:
    return json.loads((LIBRARY / group / ident / "material.json").read_text())


_panel = _material("panel", PANEL)
_body = _material("brick", FABRIC)
TILES = {f"k03:{PANEL}": tuple(_panel["tile_m"]), f"k03:{FABRIC}": tuple(_body["tile_m"])}
IMAGES = {
    f"k03:{PANEL}": {"basecolor": LIBRARY / "panel" / PANEL / _panel["web"]["basecolor"],
                     "normal": LIBRARY / "panel" / PANEL / _panel["web"]["normal_gl"]},
    f"k03:{FABRIC}": {"basecolor": LIBRARY / "brick" / FABRIC / _body["web"]["basecolor"]},
}
#: every map a K03 wall embeds: mesh_inputs hashes them, so a regenerated map stales the GLB
TEXTURE_FILES = sorted({p for v in IMAGES.values() for p in v.values()})

VARIANTS = _fab["variants"]

# The material slots k01_frontage adds. "brick" keeps its name: the K01 envelope measure
# reads walls by `^brick`. The units carry their variant's tint as the base colour, so
# the renderer batches all four with the wall's own fabric (one map, one key).
MATERIALS = {
    "brick": {"fabric": f"k03:{PANEL}", "color": (1.0, 1.0, 1.0),
              "roughness": round(_panel["mean_roughness"], 2), "normal": True,
              "courses": True, "condition": True},
}
for _v in VARIANTS:
    MATERIALS[f"brick_unit_{_v['id']}"] = {
        "fabric": f"k03:{FABRIC}", "color": tuple(_v["tint"]),
        "roughness": round(_body["mean_roughness"], 2), "condition": True}


def variant(seed: int, course: int, unit: int) -> str:
    """`variation_rule`: one variant by weight, seeded by (component seed, course, unit)."""
    h = hashlib.sha256(f"{seed}|{course}|{unit}".encode()).hexdigest()
    x = int(h[:8], 16) / 0x100000000
    acc = 0.0
    for v in VARIANTS:
        acc += v["weight"]
        if x < acc:
            return f"brick_unit_{v['id']}"
    return f"brick_unit_{VARIANTS[-1]['id']}"


def condition_breaks(soffit_m: float) -> tuple:
    """The wall heights the mask needs a vertex row at."""
    return (DAMP_TOP_M, round(soffit_m - SOOT_DEPTH_M, 4))


def tone(y: float, soffit_m: float) -> float:
    """The soot/damp multiplier at height y: piecewise linear, 1.0 on the clean body."""
    if y < DAMP_TOP_M:
        return round(DAMP_TONE + (1.0 - DAMP_TONE) * max(y, 0.0) / DAMP_TOP_M, 4)
    top = soffit_m - SOOT_DEPTH_M
    if y > top:
        return round(1.0 - (1.0 - SOOT_TONE) * min((y - top) / SOOT_DEPTH_M, 1.0), 4)
    return 1.0


# The perpend phase of each brick wall, as a fraction of the panel's width. The panel's
# u = 0 is a perpend of its first course (a stretcher course, offset 0) and a header course
# shares that phase, so a phase puts course 0's perpends where the corner rule wants them.
#   rear_service starts at the north-west quoin: course 0 begins with a header-length
#     (half-module) return, so its first perpend is half a module in;
#   side.north ENDS at that quoin: course 0 ends on a whole stretcher, a perpend at s = L;
#   side.south starts at the south-west quoin, where the rear wall's run ends: it turns the
#     corner the same way the rear wall does, and the rear wall's far end takes the closer.
def phase_u(wall_id: str, length_m: float, tile_u: float) -> float:
    if wall_id == "k01.wall.side.north":
        first = length_m % MODULE           # a perpend at s = L
    else:
        first = MODULE / 2                  # a header-length return at s = 0
    return round((-first / tile_u) % 1.0, 6)


def _rot(c, a):
    return (c[0] * math.cos(a) - c[1] * math.sin(a), c[0] * math.sin(a) + c[1] * math.cos(a))


def unit_box(asm, seed, course, idx, frame, quad, conf, proud=UNIT_PROUD, slope=0.0):
    """One brick, proud of the wall: its face, the four edges back to the wall, never the
    back. `quad` is four (s, y) corners counter-clockwise seen from outside. `slope`
    drops the face's top edge (a weathered string course sheds water)."""
    O, R, N = frame
    Y = (0.0, 1.0, 0.0)
    P = lambda s, y, d: tuple(O[i] + R[i] * s + Y[i] * y + N[i] * d for i in range(3))
    mat = variant(seed, course, idx)
    pr = asm.prim(mat)
    (s0, y0), (s1, y1), (s2, y2), (s3, y3) = quad
    # the face, slope applied to the two top corners (2 and 3)
    face = [P(s0, y0, proud), P(s1, y1, proud), P(s2, y2 - slope, proud), P(s3, y3 - slope, proud)]
    # a unit's fabric offset is its own: hash the unit into the fabric so no two match
    us = (seed ^ (course * 7919 + idx * 104729)) & 0xFFFFFFFF
    ax = (s1 - s0, y1 - y0)
    n = math.hypot(*ax)
    au = (ax[0] / n, ax[1] / n)
    U = tuple(R[i] * au[0] + Y[i] * au[1] for i in range(3))
    V = tuple(R[i] * -au[1] + Y[i] * au[0] for i in range(3))
    tu, tv = asm.tiles[MATERIALS[mat]["fabric"]]
    off = ((us & 0xFFFF) / 65536.0, (us >> 16) / 65536.0)
    pr.face(face, N, (P(s0, y0, proud), U, V, tu, tv, *off), conf)
    corners = [(s0, y0, 0.0), (s1, y1, 0.0), (s2, y2, slope), (s3, y3, slope)]
    for i in range(4):
        a, b = corners[i], corners[(i + 1) % 4]
        e = (b[0] - a[0], b[1] - a[1])
        el = math.hypot(*e)
        if el < 1e-6:
            continue
        out2 = (e[1] / el, -e[0] / el)          # outward in the wall plane (CCW polygon)
        out = tuple(R[k] * out2[0] + Y[k] * out2[1] for k in range(3))
        side = [P(a[0], a[1], 0.0), P(b[0], b[1], 0.0), P(b[0], b[1] - b[2], proud), P(a[0], a[1] - a[2], proud)]
        tang = tuple(R[k] * e[0] / el + Y[k] * e[1] / el for k in range(3))
        pr.face(side, out, (P(a[0], a[1], 0.0), tang, N, tu, tv, *off), conf)


def segmental_head(asm, seed, frame, s0, s1, y_head, conf):
    """Two rowlock rings on a segmental arch springing from the head's corners."""
    span = s1 - s0
    rise = RISE_TO_SPAN * span
    radius = (span * span / 4 + rise * rise) / (2 * rise)
    cs, cy = (s0 + s1) / 2, y_head + rise - radius
    half = math.asin((span / 2) / radius)
    pitch = BRICK_H + JOINT                       # a unit and its joint at the intrados
    r_in = radius
    for ring in range(RINGS):
        r_out = r_in + BED
        n = max(3, round(2 * half * r_in / pitch))
        step = 2 * half / n
        # the joint wedges; the brick stays rectangular — refuse a ring whose extrados
        # joint would pass the profile's cap (2.5 x the joint width); add a ring instead
        assert r_out * step - BRICK_H <= 2.5 * JOINT + 1e-9, "extrados joint past its cap"
        for k in range(n):
            phi = -half + (k + 0.5) * step          # from the left springing, clockwise
            # radial direction in (s, y): straight up at phi = 0
            er = (math.sin(phi), math.cos(phi))
            et = (math.cos(phi), -math.sin(phi))
            h = BRICK_H / 2
            c_in = (cs + er[0] * r_in, cy + er[1] * r_in)
            c_out = (cs + er[0] * r_out, cy + er[1] * r_out)
            quad = [(c_in[0] - et[0] * h, c_in[1] - et[1] * h), (c_in[0] + et[0] * h, c_in[1] + et[1] * h),
                    (c_out[0] + et[0] * h, c_out[1] + et[1] * h), (c_out[0] - et[0] * h, c_out[1] - et[1] * h)]
            # intrados left, intrados right, extrados right, extrados left: counter-clockwise
            # seen from outside, the intrados edge first (the unit's U axis)
            unit_box(asm, seed, 1000 + ring, k, frame, quad, conf)
        r_in = r_out + JOINT
    return r_in - JOINT - radius + rise           # the head's height above y_head at the crown


def soldier_head(asm, seed, frame, s0, s1, y_head, conf):
    """A soldier flat head: units on end, one past each jamb, on the bond's own width."""
    pitch = SOLDIER_W + JOINT
    n = math.ceil((s1 - s0) / pitch) + 2
    start = (s0 + s1) / 2 - (n * pitch - JOINT) / 2
    for k in range(n):
        a = start + k * pitch
        unit_box(asm, seed, 2000, k, frame,
                 [(a, y_head), (a + SOLDIER_W, y_head), (a + SOLDIER_W, y_head + SOLDIER_H),
                  (a, y_head + SOLDIER_H)], conf)


def string_course(asm, seed, frame, s_from, s_to, y_top, conf):
    """A projecting stretcher course whose top falls toward its face (weathered)."""
    pitch = MODULE
    y0 = y_top - BRICK_H
    k, a = 0, s_from
    while a < s_to - 1e-6:
        b = min(a + STRETCHER, s_to)
        unit_box(asm, seed, 3000, k, frame, [(a, y0), (b, y0), (b, y_top), (a, y_top)], conf,
                 proud=STRING_PROUD, slope=STRING_WEATHER)
        a += pitch
        k += 1
