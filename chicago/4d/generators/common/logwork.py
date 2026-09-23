"""Hewn-log construction, shared by every archetype that has logs in it.

The forks in 1835 were a log town. Almost every archetype here will need the same
three things — a stack of log courses, chinking between them, and the notched ends
protruding at the corners — and if each archetype invents its own the buildings stop
looking like they belong to the same settlement. `frame_tavern._log_wing` established
the visual language on the Sauganash's 1829 cabin; this module is that language
factored out so `log_dwelling` and `bridge_timber` speak it too.

Two decisions worth stating, because they are visible in every render:

**Hewn and squared, not round.** Wau-Bun describes the Indian Agency House as "logs
hewed and squared", and hewing was the mark of a building meant to last rather than a
first-winter shelter. Squaring also lets a course be a box, which is what keeps the
triangle count of a whole town affordable. Round logs are modelled only where hewing
would be wrong: `log_prism` exists for that, and the bridge uses it for stringers, cap
logs and piles, none of which anybody squared. Bridge cribbing goes through
`hewn_log_wall` anyway — not because crib logs were hewn, but because the notched
corner is the same joint and it should read as the same joint.

**Chinking is a separate material, and it stands PROUD.** The gap between courses was
packed with clay, moss and lime, and it is pale where the logs are dark. Two things
follow, both learned from renders rather than from reasoning. The chink needs its own
material, because a dark crease between two identical bars is what a single material
already gives you for free and it reads as a stack of planks. And it has to sit in
front of the log face rather than behind it: a recessed strip lies in its own shadow at
every sun angle, so the pale material never catches light and the extra material buys
nothing. See hewn_log_wall.

No bpy import here beyond what MeshBuilder already pulls in — this is a geometry
module, not a scene module.
"""

from __future__ import annotations

import math

from common import materials
from common.mesh import MeshBuilder

# A hewn wall log at the forks: roughly 13 in on the face. Coarse enough that a
# 2.5 m wall is seven courses rather than seventeen, which is the difference
# between a few hundred triangles per building and a few thousand.
COURSE_M = 0.34
# How far the chinking stands proud of the log faces behind it. Small on purpose,
# and PROUD rather than recessed — the reasoning is in hewn_log_wall.
RELIEF_M = 0.022
# The squared section of a protruding notched end, and how far it overhangs.
NOTCH_D = 0.20
NOTCH_OUT = 0.24


def hewn_log_wall(b: MeshBuilder, x0: float, y0: float, x1: float, y1: float,
                  z0: float, z1: float, conf: float, m_log: int, m_chink: int,
                  skip: tuple[str, ...] = ("bottom",), course: float = COURSE_M,
                  notches: bool = True, relief: float = None) -> None:
    """A four-sided hewn-log wall between two corners, with chinking and notching.

    The core box is the LOG, and the chinking stands proud of it in a strip at every
    course line. This is the second arrangement tried and the first that worked. The
    first put the chinking behind and stood the log courses proud of it, which is
    truer to a section drawing — and rendered as a wall of pale bars separated by dark
    creases, because a recessed 5 cm strip sits in its own shadow at any sun angle. It
    made the chink material invisible and cost a whole extra material to achieve
    nothing. Proud chinking catches the light, so a log wall reads from across the
    river as dark timber striped with pale clay, which is what one looks like.
    """
    r = RELIEF_M if relief is None else relief
    b.add_box(x0, y0, z0, x1, y1, z1, conf, m_log, skip=skip)

    n = max(int((z1 - z0) / course), 1)
    # An absolute chink width, not a fraction of the course. Chinking between hewn
    # logs is a few centimetres of clay and lime and does not scale with the log; the
    # first pass made it 4.5% of the course, which came out at 15 mm and vanished at
    # any viewing distance.
    gap = min(0.055, course * 0.22)
    for i in range(n + 1):
        zc = z0 + i * course
        za, zb = zc - gap / 2, zc + gap / 2
        if za < z0 or zb > z1:
            continue
        _chink_line(b, x0, y0, x1, y1, za, zb, conf, m_chink, r)
    for i in range(n):
        za = z0 + i * course + gap / 2
        zb = min(z0 + (i + 1) * course - gap / 2, z1)
        if notches and zb > za:
            _corner_notches(b, x0, y0, x1, y1, za, zb, i, conf, m_log, r)


def _chink_line(b: MeshBuilder, x0, y0, x1, y1, za, zb, conf, mat, r) -> None:
    """One course line of proud chinking, on all four elevations.

    Face plus a bottom return per elevation. The return is what casts the thin shadow
    that separates one course from the next; a face on its own reads as a painted
    stripe rather than as packed clay.
    """
    # -y elevation
    b.add_poly([(x0, y0 - r, za), (x1, y0 - r, za), (x1, y0 - r, zb), (x0, y0 - r, zb)],
               conf, mat)
    b.add_poly([(x0, y0, za), (x1, y0, za), (x1, y0 - r, za), (x0, y0 - r, za)],
               conf, mat)
    # +y elevation
    b.add_poly([(x1, y1 + r, za), (x0, y1 + r, za), (x0, y1 + r, zb), (x1, y1 + r, zb)],
               conf, mat)
    b.add_poly([(x1, y1, za), (x0, y1, za), (x0, y1 + r, za), (x1, y1 + r, za)],
               conf, mat)
    # -x elevation
    b.add_poly([(x0 - r, y1, za), (x0 - r, y0, za), (x0 - r, y0, zb), (x0 - r, y1, zb)],
               conf, mat)
    b.add_poly([(x0, y1, za), (x0, y0, za), (x0 - r, y0, za), (x0 - r, y1, za)],
               conf, mat)
    # +x elevation
    b.add_poly([(x1 + r, y0, za), (x1 + r, y1, za), (x1 + r, y1, zb), (x1 + r, y0, zb)],
               conf, mat)
    b.add_poly([(x1, y0, za), (x1, y1, za), (x1 + r, y1, za), (x1 + r, y0, za)],
               conf, mat)


def _corner_notches(b: MeshBuilder, x0, y0, x1, y1, za, zc, i: int, conf, mat,
                    relief: float = RELIEF_M) -> None:
    """Protruding notched ends at the four corners, alternating axis by course.

    Real corner notching alternates: one course runs east-west and its ends show on
    the gable walls, the next runs north-south and shows on the eave walls. Alternating
    here is what stops the corners reading as four vertical strips.
    """
    o, d = NOTCH_OUT, NOTCH_D
    r = relief * 1.7             # clear of the chink lines so nothing is coplanar
    along_x = (i % 2 == 0)
    for cx, sx in ((x0, -1), (x1, 1)):
        for cy, sy in ((y0, -1), (y1, 1)):
            if along_x:
                ax0, ax1 = sorted((cx + sx * o, cx - sx * d))
                ay0, ay1 = sorted((cy + sy * r, cy - sy * d))
            else:
                ax0, ax1 = sorted((cx + sx * r, cx - sx * d))
                ay0, ay1 = sorted((cy + sy * o, cy - sy * d))
            # Whichever way the log runs, the two faces that point back into the
            # building are the same pair, and drawing them costs four triangles a
            # corner a course for surfaces nobody can see.
            hidden_x = "right" if sx < 0 else "left"
            hidden_y = "back" if sy < 0 else "front"
            b.add_box(ax0, ay0, za, ax1, ay1, zc, conf, mat,
                      skip=(hidden_x, hidden_y, "bottom"))


def log_prism(b: MeshBuilder, p0, p1, radius: float, conf: float, mat: int,
              sides: int = 6) -> None:
    """A round (unhewn) log between two points, as a low-sided prism.

    Only axis-aligned runs are supported, which is all the project needs: bridge
    stringers, cap logs and piles are all square to the deck. Six sides is the
    cheapest section that still catches a highlight down its length; four reads as
    a squared timber, which would contradict the source that says these were logs.
    """
    ax = max(range(3), key=lambda i: abs(p1[i] - p0[i]))
    if p1[ax] < p0[ax]:                       # normalise direction; see below
        p0, p1 = p1, p0
    u, v = [i for i in range(3) if i != ax]

    # Winding, and why this is not decoration: glTF meshes are single-sided by
    # default, so a cap wound the wrong way is an invisible hole in the render and
    # the mistake is easy to miss on a dark log. A ring built counter-clockwise in
    # the (u, v) plane yields an outward normal only when (u, v, ax) is a
    # right-handed cycle of (x, y, z) — true for ax = x and ax = z, false for
    # ax = y. Reversing the ring in that case makes one traversal order correct for
    # every axis, so the side quads and the caps below need no per-axis special case.
    handed = -1 if ax == 1 else 1
    ring = []
    for k in range(sides):
        a = 2 * math.pi * (k + 0.5) / sides
        ring.append((radius * math.cos(a), radius * math.sin(a)))
    if handed < 0:
        ring.reverse()

    def pt(end, k):
        c = list(end)
        c[u] += ring[k][0]
        c[v] += ring[k][1]
        return tuple(c)

    for k in range(sides):
        k2 = (k + 1) % sides
        b.add_poly([pt(p0, k), pt(p0, k2), pt(p1, k2), pt(p1, k)], conf, mat)
    b.add_poly([pt(p0, k) for k in range(sides - 1, -1, -1)], conf, mat)
    b.add_poly([pt(p1, k) for k in range(sides)], conf, mat)


# Weathered hewn oak, and clay-and-lime chinking. Both are LINEAR values, and both
# now come OFF THE SHEET (`common/materials.py`, T-0007) rather than being declared
# here. The argument behind the log's value is unchanged and belongs in front of a
# reader of this module: it is deliberately about a fifth darker than the paler
# hewn-log value this project also carried, because the chink stripe needs something
# to contrast against or the material split is wasted — and rendered side by side
# under the same light (generators/preview.py --archetype frame_tavern) a first pass
# at 0.295 put the log dwellings visibly in a different town from the Sauganash's
# wing. What T-0007 changes is that the Sauganash's wing finally uses it too
# (materials.md finding 2).
HEWN_RGBA = materials.HEWN_LOG.rgba
CHINK_RGBA = materials.CHINKING.rgba
