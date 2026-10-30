"""Glessner v4 street and stable sash (T-2211, audit GA-11A).

Every street-face window used to be one pane behind one flat frame with a bar
across its middle, so a whole front read as the same dark field. This module
draws what the HABS sheets and photographs show a window to be made of:

  double_hung   two sashes in two planes, the upper one outside the lower, each
                with its own stiles, top/meeting/bottom rails and its own glass;
                the frame's blind stop proud of both; a sloped oak sub-sill;
                the granite sill weathered toward the street with a drip nib.
                HABS sheet 5 (the Prairie main entrance's window) and photograph
                14 (the east wing's north pairs) show one-over-one sash.
  slit_sash     a narrow light with horizontal glazing bars, as HABS sheet 5
                draws the corridor slits beside the 18th Street entrance.
  gable_light   the 18th Street gable's round-headed light: a fixed arched sash,
                a stone transom, and a one-over-one sash below it (HABS
                photograph 14; the c. 1923 photograph 04 agrees).

T-2212 (audit GA-11B) carries the same sash into the courtyard, read off HABS
photograph 05 (c. 1923, the court; rights unknown, so read and never traced):

  courtyard     the same double-hung with a rock-faced limestone sill under a
                rough lintel; the east wing's four lights over the underpass are
                two-over-two (a vertical bar in each sash); the garden-level
                lights stand behind vertical iron bars.
  on_facet      the hall bow's and the dining bay's lights, which sit on curved
                or canted facets rather than an axis-aligned wall, are the same
                one-over-one double-hung, carried onto the facet by OnFacet.

The opening sizes stay the record's. The member sizes (stiles 48 mm, meeting
rails 38 mm, bottom rail 85 mm, the 45 mm sash planes) are a reconstruction at
ordinary 1880s joinery, recorded as L-glessner-sash-2211 in docs/LIBERTIES.md.
The reduced (light) tier keeps the earlier single pane for every window but the
gable light: it has under 3,000 triangles of its 200,000 left.
"""
from __future__ import annotations

import math

from archetypes import masonry_house as legacy

STILE = .048
TOP_RAIL = .052
MEET = .038
BOTTOM_RAIL = .085
UPPER = (-.245, -.205)   # outer sash, outside the parting bead
LOWER = (-.290, -.250)   # inner sash
FRAME = (-.290, -.170)   # blind stop and head, proud of both sashes


def sub3(p, q):
    return tuple(p[k] - q[k] for k in range(3))


def _d():
    from archetypes import masonry_house_v4_detail as d
    return d


def prism_u(b, pl, u0, u1, profile, conf, mat):
    """Extrude a convex (depth, z) profile along the wall from u0 to u1."""
    n = legacy._plane_dir(pl)
    left = [legacy._plane_point(pl, u0, z, off) for off, z in profile]
    right = [legacy._plane_point(pl, u1, z, off) for off, z in profile]
    along = tuple(right[0][k] - left[0][k] for k in range(3))
    b.raw(left, conf, mat, tuple(-v for v in along))
    b.raw(right, conf, mat, along)
    count = len(profile)
    cd = sum(p[0] for p in profile) / count
    cz = sum(p[1] for p in profile) / count
    for i in range(count):
        j = (i + 1) % count
        (da, za), (db, zb) = profile[i], profile[j]
        # Outward in the (depth, z) plane, then carried onto the wall's normal.
        md, mz = (da + db) / 2 - cd, (za + zb) / 2 - cz
        want = (n[0] * md, n[1] * md, mz)
        b.raw([left[i], left[j], right[j], right[i]], conf, mat, want)


def _sash(b, o, a, c, lo, hi, plane, rails, glass_off, conf, bars=0, stile=STILE, vbars=0):
    """One sash: stiles, rails (bottom, top) and its glass, with optional bars."""
    d = _d()
    d0, d1 = plane
    bottom, top = rails
    d.slab(b, o, a, a + stile, lo, hi, d0, d1, conf, d.PAINTED_WOOD)
    d.slab(b, o, c - stile, c, lo, hi, d0, d1, conf, d.PAINTED_WOOD)
    d.slab(b, o, a + stile, c - stile, lo, lo + bottom, d0, d1, conf, d.PAINTED_WOOD)
    d.slab(b, o, a + stile, c - stile, hi - top, hi, d0, d1, conf, d.PAINTED_WOOD)
    ga, gc, gz0, gz1 = a + stile, c - stile, lo + bottom, hi - top
    if gc - ga < .02 or gz1 - gz0 < .02:
        return
    d.glass_pane(b, [legacy._plane_point(o, u, z, glass_off) for u, z in
                     ((ga, gz0), (gc, gz0), (gc, gz1), (ga, gz1))], legacy._plane_dir(o), conf)
    for i in range(1, bars + 1):
        z = gz0 + (gz1 - gz0) * i / (bars + 1)
        d.slab(b, o, ga, gc, z - .011, z + .011, glass_off - .012, glass_off + .014, conf, d.PAINTED_WOOD)
    for i in range(1, vbars + 1):
        u = ga + (gc - ga) * i / (vbars + 1)
        d.slab(b, o, u - .011, u + .011, gz0, gz1, glass_off - .012, glass_off + .014, conf, d.PAINTED_WOOD)


def double_hung(b, o, a, c, z0, z1, conf, frame=.062, meet_from_top=.5, sill=True,
                divided=False, sill_mat=None):
    """A one-over-one double-hung window filling the opening a..c, z0..z1.

    `divided` makes it two-over-two: one vertical bar in each sash (T-2212).
    `sill_mat` replaces the street's granite sill (the courtyard's is rock-faced
    limestone)."""
    d = _d()
    P = lambda u, z, off: legacy._plane_point(o, u, z, off)
    n = legacy._plane_dir(o)
    width = c - a
    units = 2 if width > 1.7 else 1
    mull = .05
    # The interior stays the bounded shadow volume behind the glass.
    d.interior_recess(b, [(a + frame, z0 + frame), (c - frame, z0 + frame),
                          (c - frame, z1 - frame), (a + frame, z1 - frame)], P, n)
    # Frame: jambs and head proud of the sashes, a mullion between paired units.
    for x0, x1, y0, y1 in ((a, a + frame, z0, z1), (c - frame, c, z0, z1), (a, c, z1 - frame, z1)):
        d.slab(b, o, x0, x1, y0, y1, FRAME[0], FRAME[1], conf, d.PAINTED_WOOD)
    # Oak sub-sill, weathered outward, under the lower sash.
    sub = z0 + frame
    prism_u(b, o, a, c, [(-.300, z0), (-.150, z0), (-.150, z0 + .028), (-.300, sub)], conf, d.PAINTED_WOOD)
    inner_a, inner_c = a + frame, c - frame
    span = (inner_c - inner_a - mull * (units - 1)) / units
    for k in range(units):
        ua = inner_a + k * (span + mull)
        uc = ua + span
        if k:
            d.slab(b, o, ua - mull, ua, z0, z1, FRAME[0], FRAME[1], conf, d.PAINTED_WOOD)
        top = z1 - frame
        meet = top - (top - sub) * meet_from_top
        vb = 1 if divided else 0
        _sash(b, o, ua, uc, meet - MEET / 2, top, UPPER, (MEET, TOP_RAIL), -.226, conf, vbars=vb)
        _sash(b, o, ua, uc, sub, meet + MEET / 2, LOWER, (BOTTOM_RAIL, MEET), -.271, conf, vbars=vb)
    if sill:
        granite_sill(b, o, a, c, z0, conf, sill_mat)


def granite_sill(b, o, a, c, z0, conf, mat=None):
    """The street sill: weathered toward the street, with a drip nib under its nose."""
    d = _d()
    mat = mat if mat is not None else d.GRANITE
    prism_u(b, o, a - .09, c + .09, [(-.055, z0 - .085), (.110, z0 - .085), (.110, z0 + .004), (-.055, z0 + .028)],
            conf, mat)
    prism_u(b, o, a - .09, c + .09, [(.086, z0 - .104), (.110, z0 - .104), (.110, z0 - .085), (.086, z0 - .085)],
            conf, mat)


def slit_sash(b, o, a, c, z0, z1, conf, sill_mat=None, sill=True, panes=None):
    """A narrow light: one sash in a light frame, divided by horizontal bars.

    T-2928: `panes` fixes the count a drawing gives (1: no bars), and `sill=False`
    leaves the stone to the light's own drawn sill `band`."""
    d = _d()
    P = lambda u, z, off: legacy._plane_point(o, u, z, off)
    n = legacy._plane_dir(o)
    frame = .035
    d.interior_recess(b, [(a + frame, z0 + frame), (c - frame, z0 + frame),
                          (c - frame, z1 - frame), (a + frame, z1 - frame)], P, n)
    for x0, x1, y0, y1 in ((a, a + frame, z0, z1), (c - frame, c, z0, z1), (a, c, z1 - frame, z1)):
        d.slab(b, o, x0, x1, y0, y1, FRAME[0], FRAME[1], conf, d.PAINTED_WOOD)
    prism_u(b, o, a, c, [(-.300, z0), (-.170, z0), (-.170, z0 + .022), (-.300, z0 + frame)], conf, d.PAINTED_WOOD)
    lights = panes or max(2, round((z1 - z0) / .55))
    _sash(b, o, a + frame, c - frame, z0 + frame, z1 - frame, LOWER, (.06, .045), -.271, conf,
          bars=lights - 1, stile=.036)
    if sill:
        granite_sill(b, o, a, c, z0, conf, sill_mat)


def garden_bars(b, o, a, c, z0, z1, conf):
    """Vertical iron bars across a garden-level courtyard light (HABS photograph 05)."""
    d = _d()
    count = max(3, round((c - a) / .115))
    for i in range(1, count):
        x, y, _ = legacy._plane_point(o, a + (c - a) * i / count, 0, -.10)
        d.cylinder(b, x, y, z0 + .02, z1 - .02, .011, conf, d.IRON, 6)


class OnFacet:
    """A builder that carries sash drawn on the plane y = 0 (u along +x, outward
    along PLANE's outward side) onto a bay or bow facet: u runs from p along
    `tangent`, outward is `normal`. The canonical plane's sign is chosen so the
    map keeps handedness, so faces drawn without a wanted normal keep their winding."""

    def __init__(self, b, p, tangent, normal):
        self.b, self.p, self.t, self.n = b, p, tangent, normal
        self.params = b.params
        self.s = 1 if tangent[0] * normal[1] - tangent[1] * normal[0] > 0 else -1
        self.plane = {'axis': 'y', 'sign': self.s, 'at': 0.0}

    def _map(self, v, base):
        x, y, z = v
        y *= self.s
        return (base[0] + self.t[0] * x + self.n[0] * y, base[1] + self.t[1] * x + self.n[1] * y, z)

    def raw(self, pts, confidence, mat, want=None):
        return self.b.raw([self._map(q, self.p) for q in pts], confidence, mat,
                          None if want is None else self._map(want, (0.0, 0.0)))


def on_facet(b, p, tangent, normal, width, z0, z1, conf):
    """A one-over-one double-hung on a facet of the hall bow or the dining bay.
    The facet's own stone sill and lintel stay; this is the frame, sash and glass."""
    f = OnFacet(b, p, tangent, normal)
    double_hung(f, f.plane, 0.0, width, z0, z1, conf, sill=False)


def gable_light(b, o, conf):
    """The 18th Street gable's light: arched fixed sash, stone transom, sash below."""
    d = _d()
    a, c, z0 = o['u0'], o['u1'], o['z0']
    t0, t1 = o['transom_z']
    spring = o['spring_z']
    r = (c - a) / 2
    cx = (a + c) / 2
    P = lambda u, z, off: legacy._plane_point(o, u, z, off)
    n = legacy._plane_dir(o)
    # The transom is one stone through the reveal, its face set just inside the wall's.
    d.solid_polygon(b, o, [(a, t0), (c, t0), (c, t1), (a, t1)], -.29, -.02, conf, d.GRANITE)
    # Head: a fixed arched sash whose frame follows the opening.
    steps = 10
    def outline(inset):
        rr = r - inset
        pts = [(a + inset, t1 + (inset if inset else 0)), (c - inset, t1 + (inset if inset else 0))]
        pts += [(cx + rr * math.cos(math.pi * i / steps), spring + rr * math.sin(math.pi * i / steps))
                for i in range(steps + 1)]
        return pts
    outer, inner = outline(0.0), outline(.045)
    d.interior_recess(b, outer, P, n)
    d.glass_pane(b, [P(u, z, -.235) for u, z in inner], n, conf)
    for i in range(len(outer)):
        j = (i + 1) % len(outer)
        face = [P(*outer[i], -.205), P(*outer[j], -.205), P(*inner[j], -.205), P(*inner[i], -.205)]
        b.raw(face, conf, d.PAINTED_WOOD, n)
        mid = ((inner[i][0] + inner[j][0]) / 2, (inner[i][1] + inner[j][1]) / 2)
        toward = sub3(P(cx, (t1 + spring) / 2, -.23), P(mid[0], mid[1], -.23))
        b.raw([P(*inner[i], -.205), P(*inner[j], -.205), P(*inner[j], -.25), P(*inner[i], -.25)],
              conf, d.PAINTED_WOOD, toward)
    # Below the transom: a one-over-one sash, its meeting rail a little below the middle.
    double_hung(b, o, a, c, z0, t0, conf, frame=.045, meet_from_top=.55, sill=False)
