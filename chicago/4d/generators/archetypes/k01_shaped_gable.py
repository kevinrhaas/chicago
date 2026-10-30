"""T-2543: the K01 street front's SHAPED (Flemish) GABLE — 1812 Prairie's, from Albert Levy's photograph.

TICKET T-2543 (piece 1 of T-1884). The Wheeler house's front does not end at an eave: its wall
is carried up over the whole front as a tall gable whose outline swells from a kneeler at each
corner and draws in, in curves, to a pointed head under a finial, with a grid window lighting the
roof storey. K01's wall gable (k01_wall_gable, T-2428) is a straight-raked pediment on a dormer;
this is another thing, so it is its own element. The record names it as `shaped_gable`
(k01_frontage_params._shaped_gable resolves and bounds it), and this module builds it:

  element()  before the union: the gable as ONE closed slab, the record's outline extruded
             through its thickness on the street front, its face standing just proud of the
             hip's street eave so the eave dies into it. It is joined to the roof by the K05
             union like a stack, so where it passes through the slates the union cuts it
  cutters()  before the boolean: each light's recess, cut to K06's own hole
  dress()    after it: each light's K06 sash in its recess, the stone coping band laid on the
             face along the outline, the kneelers' pinnacles and the finial

The outline's own edges (the top of the slab) are stone coping; its faces are the side walls'
brick. Every number a piece is cut to is the record's or is named here, and docs/LIBERTIES.md
L-k01-1812-wheeler-front-2543 says which.

T-2730: 1625 Prairie's front is the same slab with a straight outline — a plain coped WALL
GABLE in the front's stone (`fabric: "front"`), its lights segment-headed and standing under
the eave, no kneeler pinnacles and no finial, and an oval `oculus` in a stone ring near the
apex, cut like a light and glazed here behind a cross of bars.
L-k01-1625-mcbirney-wall-gable-2730 says which numbers are read and which are not.

T-2889: 1812's front runs up into its gable with no gutter across it, so `takes_gutter`
stops the eave's gutter where the gable stands: its street run is not built, its two side
runs die into the slab's base at the base's back, and the base runs out past the side walls
far enough to take their lips (k01_frontage.rainwater; L-k01-1812-wheeler-third-storey-2889).

T-2951: 1812's gable to the Levy photograph's. Its grid window is `rows` of the K06 group
stacked over one another on stone transoms (`row_sills`), each light one pane (`panes`); its
outline steps over a square stone `shoulders` block each side, laid through the slab so it
stands over the outline as the print's do; and each kneeler's pinnacle stands over a carved
`scroll` console at the front's corner, under the slab's foot: a moulded roll at the console's
foot, a raised eye in it, and a cap under the slab. L-k01-1812-wheeler-gable-2951.

T-3090: the rest of 1812's gable as the Levy and c. 1955 photographs show it. The grid window's
`glazing: "dark"` reads its lights as the prints' dark openings (no K06 sash, a dark backing
behind glass), between `quoins` long and short up each side, under a `hood` whose upper edge
waves to a crown at its middle and a flick at each end, over a two-step `shelf`; each shoulder
block carries a sunk `panel`; each scroll a carved `rosette` in its eye; the `finial` is an
`urn` on a carved ball; and `base_ledge_half_m` draws the slab's base in from its foot to the
kneelers' ledge. L-k01-1812-wheeler-gable-3090.
"""

from __future__ import annotations

import math

LEDGE_OVER_FASCIA_M = 0.12  # the kneelers' ledge: this far over the street fascia's top
JOINT_M = 0.008             # half a coping joint
PIN_CAP_PROUD_M = 0.04      # a kneeler's cap before its shaft, all round
FINIAL_SINK_M = 0.06        # the finial's foot let into the apex


def _af():
    from . import k01_arched_front
    return k01_arched_front


def half_width(sg, y):
    """The outline's half-width at height y (over grade), on the record's profile."""
    pr = sg["profile_m"]
    if y <= pr[0][1]:
        return pr[0][0]
    for (w0, y0), (w1, y1) in zip(pr, pr[1:]):
        if y0 <= y <= y1:
            return w0 + (w1 - w0) * (y - y0) / (y1 - y0)
    return 0.0


def gutter_lip(p):
    """T-2889: how far the eave's gutter's outer lip stands off the wall (k01_frontage.rainwater:
    its axis a radius and 6 mm off the fascia, the fascia `eave_overhang_m` out)."""
    if not p.rainwater:
        return p.eave_overhang_m
    ro = p.rainwater["gutter_diameter_m"] / 2 + 0.004
    return p.eave_overhang_m + 2 * ro + 0.006


def geometry(p, ye):
    """The slab's numbers in the K01 frame (x = u toward the street, z = -v): its face and
    back, the ledge, the base's half-width and the outline as (z, y) points, counter-clockwise
    seen from the street."""
    sg = p.shaped_gable
    D, W, o = p.depth_m, p.width_m, p.eave_overhang_m
    xf = D + o + sg["proud_m"]
    xb = xf - sg["thickness_m"]
    zc = -W / 2
    ledge = sg.get("ledge_m") or ye + LEDGE_OVER_FASCIA_M   # T-2865: a ledge over the eave
    hb = W / 2 + o + 0.02             # the base covers the eave's corners
    if sg.get("takes_gutter"):        # T-2889: and the gutter's two side runs, which die into it
        hb = max(hb, W / 2 + gutter_lip(p) + 0.02)
    hl = half_width(sg, ledge)
    up = [(w, y) for w, y in sg["profile_m"] if y > ledge + 1e-6]
    right = [(hl, ledge)] + up        # foot to apex, the last on the centre line
    bl = sg.get("base_ledge_half_m") or hb   # T-3090: the base drawn in to the ledge
    side = [(zc - hb, sg["foot_m"]), (zc + hb, sg["foot_m"]), (zc + bl, ledge)]
    pts = side + [(zc + w, y) for w, y in right[:-1]] + [(zc, right[-1][1])]
    pts += [(zc - w, y) for w, y in reversed(right[:-1])] + [(zc - bl, ledge)]
    return {"xf": xf, "xb": xb, "zc": zc, "ledge": ledge, "hb": hb, "right": right,
            "apex": right[-1][1], "outline": pts}


def element(a, k5, ye):
    """The gable as one closed solid for the roof's union."""
    g = geometry(a.p, ye)
    a.shaped_gable_geom = g
    foot = a.p.shaped_gable["foot_m"]
    if a.p.shaped_gable.get("fabric") == "front":
        a.front_parapet_u = g["xb"] - 1e-6   # T-2730: _emit_shell dresses the slab in the front's stone
    a.front_gable_u = g["xb"] - 1e-6         # T-3093: and a toned front's brick, its brick

    def role(i, p_, q_):
        if abs(p_[1] - foot) < 1e-9 and abs(q_[1] - foot) < 1e-9:
            return "parapet"          # its soffit, over the wall's head
        if abs(p_[0] - q_[0]) < 1e-9:
            return "parapet"          # the base's two ends
        return "coping"               # the outline: the kneelers' ledges and the curves
    return k5.extrude(g["outline"], g["xb"], g["xf"], k5.frame("x"), role, "parapet", "parapet")


def _variant(sg, k6):
    li = sg["lights"]
    v = dict(next(x for x in k6.load()["variants"] if x["id"] == li["variant"]))
    v["clear_width_m"], v["clear_height_m"] = li["width_m"], li["height_m"]
    if li.get("panes"):   # T-2951: the grid's lights are one pane each
        v["panes"] = list(li["panes"])
    return v


def row_sills(li) -> list:
    """T-2951: each row's sill over grade, the lowest first — `rows` of the lights stacked on
    stone transoms `transom_m` deep (one row, the record's sill, when it names none)."""
    n, t = li.get("rows", 1), li.get("transom_m", 0.0)
    return [li["sill_m"] + r * (li["height_m"] + t) for r in range(n)]


def cutters(a, k5) -> list:
    """Every light's recess, cut to K06's own hole through the slab's face."""
    from . import k06_windows as k6
    sg, g = a.p.shaped_gable, a.shaped_gable_geom
    li = sg["lights"]
    v = _variant(sg, k6)
    o = k6.Opening(v, k6.load())
    o.build()
    rev = v.get("overrides", {}).get("reveal_depth_m", k6.load()["parts"]["reveal_depth_m"]["value"])
    out = []
    for at in li["at_m"]:
        c = g["zc"] - at               # R runs -z along the street front
        for sill in row_sills(li):     # T-2951: a grid window cuts every row
            for hole in o.holes:       # a grouped variant cuts one hole a bay
                rec = [(c - q[0], sill + q[1]) for q in hole]
                out.append(k5.extrude(rec, g["xf"] - rev, g["xf"] + 0.05, k5.frame("x"), "reveal", "window", "reveal"))
    oc = sg.get("oculus")
    if oc:   # T-2730: the oval light's recess, to the lights' reveal depth
        ry = oc["centre_m"]
        rec = [(g["zc"] - p_ * oc["width_m"] / 2, ry + q_ * oc["height_m"] / 2) for p_, q_ in _oval()]
        out.append(k5.extrude(rec, g["xf"] - rev, g["xf"] + 0.05, k5.frame("x"), "reveal", "window", "reveal"))
    return out


OVAL_SIDES = 24             # the oculus's polygon
TRANSOM_PROUD_M = 0.02      # T-2951: a grid window's stone transoms, before the face
SHOULDER_BACK_M = 0.01      # a shoulder block's back, this far before the slab's back
SCROLL_SIDES = 20           # a scroll's roll
SCROLL_EYE = 0.55           # its eye's radius, of the roll's
SCROLL_EYE_PROUD_M = 0.03   # the eye standing before the roll
SCROLL_CAP_M = (0.08, 0.03)  # the console's cap: its height, and how far it overhangs all round


def _back(a, mat, frame, poly, d, seed, conf):
    """The face a block shows behind it, at depth d (poly counter-clockwise in (s, y))."""
    _af()._face(a, mat, frame, [(s, y, d) for s, y in reversed(poly)], (0, 0, -1), seed, conf)


def _shoulders(a, frame, sg, gseed, conf):
    """T-2951: the square stone block the outline steps over each side, at its shoulders —
    laid through the slab from just before its back to `proud_m` before its face, so it
    stands over the outline as the print's blocks do, and its back is drawn where it does."""
    sh = sg["shoulders"]
    W = a.p.width_m
    d0 = -(sg["thickness_m"] - SHOULDER_BACK_M)
    seed = a.instance("k01.roof.gable_shoulder", "roof",
                      {k_: sh[k_] for k_ in ("inner_m", "outer_m", "bed_m", "top_m", "proud_m")},
                      {"bed": (a.shaped_gable_geom["xf"], sh["bed_m"], a.shaped_gable_geom["zc"])})
    for sgn in (-1, 1):
        s0, s1 = sorted((W / 2 + sgn * sh["inner_m"], W / 2 + sgn * sh["outer_m"]))
        poly = [(s0, sh["bed_m"]), (s1, sh["bed_m"]), (s1, sh["top_m"]), (s0, sh["top_m"])]
        pn = sh.get("panel")
        if not pn:
            _prism(a, "limestone_trim", frame, poly, d0, sh["proud_m"], seed, conf)
        else:
            # T-3090: the block's face sunk in a panel — the block to the panel's floor, and
            # the face's four margins round it to the block's own face
            fl = sh["proud_m"] - pn["sunk_m"]
            _prism(a, "limestone_trim", frame, poly, d0, fl, seed, conf)
            sc_ = (s0 + s1) / 2
            p0, p1 = sc_ - pn["width_m"] / 2, sc_ + pn["width_m"] / 2
            q1 = sh["top_m"] - pn["drop_m"]
            q0 = q1 - pn["height_m"]
            for m_ in ([(s0, sh["bed_m"]), (s1, sh["bed_m"]), (s1, q0), (s0, q0)],
                       [(s0, q1), (s1, q1), (s1, sh["top_m"]), (s0, sh["top_m"])],
                       [(s0, q0), (p0, q0), (p0, q1), (s0, q1)],
                       [(p1, q0), (s1, q0), (s1, q1), (p1, q1)]):
                _prism(a, "limestone_trim", frame, m_, fl, sh["proud_m"], seed, conf)
        _back(a, "limestone_trim", frame, poly, d0, seed, conf)


def _circle(sc, yc, r):
    return [(sc + r * math.cos(2 * math.pi * i / SCROLL_SIDES), yc + r * math.sin(2 * math.pi * i / SCROLL_SIDES))
            for i in range(SCROLL_SIDES)]


def _scroll(a, frame, sg, W, sgn, conf):
    """T-2951: the carved scroll console under a kneeler, at the front's corner: a roll at its
    foot (`radius_m`, `proud_m` before the wall), a raised eye in it, the console's body over
    it up to a cap under the slab's foot, all inside the front's corner."""
    sc = sg["kneelers"]["scroll"]
    w, r, pr = sc["width_m"], sc["radius_m"], sc["proud_m"]
    s0 = 0.0 if sgn < 0 else W - w
    s1 = s0 + w
    yc = sc["bed_m"] + r
    ch, co = SCROLL_CAP_M
    top = sg["foot_m"]
    xs = s0 + w / 2
    seed = a.instance("k01.roof.gable_scroll", "roof", dict(sc),
                      {"foot": (a.shaped_gable_geom["xf"], round(sc["bed_m"], 4), round(-xs, 4))})
    d = -(a.p.eave_overhang_m + sg["proud_m"])   # the wall's face under the slab, behind its face
    _prism(a, "limestone_trim", frame, _circle(xs, yc, r), d, d + pr, seed, conf)
    if sc.get("rosette"):
        # T-3090: the print's eye is carved, a rosette: a boss at its middle and its petals
        # round it, each a pointed leaf standing out of the roll's face
        re_ = r * SCROLL_EYE
        _prism(a, "limestone_trim", frame, _circle(xs, yc, re_ * 0.32), d + pr, d + pr + SCROLL_EYE_PROUD_M * 1.4,
               seed, conf)
        n_ = sc["rosette"]
        for i in range(n_):
            t_ = 2 * math.pi * (i + 0.25) / n_
            ux, uy = math.cos(t_), math.sin(t_)
            vx, vy = -uy, ux
            hw_ = re_ * math.sin(math.pi / n_) * 0.8
            r0_, r1_, rm_ = re_ * 0.36, re_ * 1.02, re_ * 0.68
            _prism(a, "limestone_trim", frame, [(xs + ux * r0_, yc + uy * r0_),
                                                (xs + ux * rm_ + vx * hw_, yc + uy * rm_ + vy * hw_),
                                                (xs + ux * r1_, yc + uy * r1_),
                                                (xs + ux * rm_ - vx * hw_, yc + uy * rm_ - vy * hw_)],
                   d + pr, d + pr + SCROLL_EYE_PROUD_M, seed, conf)
    else:
        _prism(a, "limestone_trim", frame, _circle(xs, yc, r * SCROLL_EYE), d + pr, d + pr + SCROLL_EYE_PROUD_M,
               seed, conf)
    bw = r * 0.8                       # the body, narrower than the roll, from its axis up
    _prism(a, "limestone_trim", frame, [(xs - bw, yc), (xs + bw, yc), (xs + bw, top - ch), (xs - bw, top - ch)],
           d, d + pr * 0.8, seed, conf)
    _prism(a, "limestone_trim", frame, [(max(0.0, s0 - co) if sgn < 0 else s0 - co, top - ch),
                                        (s1 + co if sgn < 0 else min(W, s1 + co), top - ch),
                                        (s1 + co if sgn < 0 else min(W, s1 + co), top),
                                        (max(0.0, s0 - co) if sgn < 0 else s0 - co, top)],
           d, d + pr + co, seed, conf)


def _oval():
    """The unit oval as (cos, sin) pairs, counter-clockwise."""
    return [(math.cos(2 * math.pi * i / OVAL_SIDES), math.sin(2 * math.pi * i / OVAL_SIDES))
            for i in range(OVAL_SIDES)]


def _oculus(a, frame, sg, g, gseed, conf):
    """T-2730: the oval light — its dark backing and glass at the recess's back, a cross of
    glazing bars, and the stone ring proud of the face round it, laid as voussoirs."""
    from . import k06_windows as k6
    oc = sg["oculus"]
    W = a.p.width_m
    rev = k6.load()["parts"]["reveal_depth_m"]["value"]
    s0, y0 = W / 2, oc["centre_m"]
    rw, rh, ring = oc["width_m"] / 2, oc["height_m"] / 2, oc["ring_m"]
    seed = a.instance("k01.opening.gable_oculus", "opening",
                      {"width_m": oc["width_m"], "height_m": oc["height_m"], "ring_m": ring},
                      {"centre": (g["xf"], y0, g["zc"])})
    af = _af()
    pane = [(s0 + c * rw, y0 + q * rh) for c, q in _oval()]
    af._face(a, "backing", frame, [(s, y, -rev) for s, y in pane], (0, 0, 1), seed, conf)
    af._face(a, "glass", frame, [(s, y, -rev + 0.03) for s, y in pane], (0, 0, 1), seed, conf)
    b = oc["bars_m"] / 2
    if b:
        _prism(a, "sash", frame, [(s0 - rw, y0 - b), (s0 + rw, y0 - b), (s0 + rw, y0 + b), (s0 - rw, y0 + b)],
               -rev, -rev + 0.06, seed, conf)
        _prism(a, "sash", frame, [(s0 - b, y0 - rh), (s0 + b, y0 - rh), (s0 + b, y0 + rh), (s0 - b, y0 + rh)],
               -rev, -rev + 0.06, seed, conf)
    ov = _oval()
    for (c0, q0), (c1, q1) in zip(ov, ov[1:] + ov[:1]):
        poly = [(s0 + c0 * rw, y0 + q0 * rh), (s0 + c1 * rw, y0 + q1 * rh),
                (s0 + c1 * (rw + ring), y0 + q1 * (rh + ring)), (s0 + c0 * (rw + ring), y0 + q0 * (rh + ring))]
        _prism(a, "limestone_trim", frame, poly, 0.0, oc["proud_m"], gseed, conf)


def _prism(a, mat, frame, poly, d0, d1, seed, conf):
    """A stone standing proud of the face, counter-clockwise in (s, y)."""
    area = math.fsum(p[0] * q[1] - q[0] * p[1] for p, q in zip(poly, poly[1:] + poly[:1]))
    if area < 0:
        poly = list(reversed(poly))
    from . import k01_wall_gable
    k01_wall_gable._prism(a, mat, frame, poly, d0, d1, seed, conf)


# T-3090: the urn finial's turned outline, bottom to top, as (fraction of its height,
# fraction of the ball's radius): the carved ball, the neck and its ring, the urn's moulded
# foot, its body swelling to its shoulder, the lid and the knob
URN_PROFILE = [(0.0, 0.62), (0.02, 0.85), (0.08, 0.96), (0.18, 1.0), (0.28, 0.88), (0.35, 0.58),
               (0.37, 0.4), (0.41, 0.4), (0.41, 0.54), (0.46, 0.54), (0.46, 0.36), (0.52, 0.46),
               (0.6, 0.62), (0.68, 0.58), (0.74, 0.42), (0.74, 0.5), (0.8, 0.46), (0.82, 0.23),
               (0.86, 0.19), (0.9, 0.23), (0.95, 0.12), (1.0, 0.015)]
HOOD_STRIPS = 24            # the hood's waved top, in this many upright strips
DARK_FRAME_M = 0.03         # a dark light's frame, round its glass


def _dark_lights(a, frame, v, s, sill, rev, gseed, conf):
    """T-3090: a light the print reads as a dark opening — no sash in it, the dark backing at
    the recess's back and the glass just before it, a thin frame round it."""
    from . import k06_windows as k6
    o = k6.Opening(v, a._kit)
    o.build()
    af = _af()
    for hole in o.holes:
        pane = [(s + q[0], sill + q[1]) for q in hole]
        af._face(a, "backing", frame, [(x, y, -rev + 0.004) for x, y in pane], (0, 0, 1), gseed, conf)
        af._face(a, "glass", frame, [(x, y, -rev + 0.03) for x, y in pane], (0, 0, 1), gseed, conf)
        xs_, ys_ = [x for x, _ in pane], [y for _, y in pane]
        x0, x1, y0, y1 = min(xs_), max(xs_), min(ys_), max(ys_)
        f = DARK_FRAME_M
        for poly in ([(x0, y0), (x1, y0), (x1, y0 + f), (x0, y0 + f)], [(x0, y1 - f), (x1, y1 - f), (x1, y1), (x0, y1)],
                     [(x0, y0 + f), (x0 + f, y0 + f), (x0 + f, y1 - f), (x0, y1 - f)],
                     [(x1 - f, y0 + f), (x1, y0 + f), (x1, y1 - f), (x1 - f, y1 - f)]):
            _prism(a, "sash", frame, poly, -rev + 0.004, -rev + 0.05, gseed, conf)


def _window_dress(a, frame, li, s, gseed, conf):
    """T-3090: the grid window's quoins up each side, its waved hood and its moulded shelf."""
    hw = li["width_m"] / 2
    rs = row_sills(li)
    yb, yt = rs[0], rs[-1] + li["height_m"]
    qn = li.get("quoins")
    if qn:
        n = len(rs)
        h = (yt - yb) / n
        for i in range(n):
            w_ = qn["long_m"] if i % 2 == 0 else qn["short_m"]
            y0, y1 = yb + i * h + JOINT_M, yb + (i + 1) * h - JOINT_M
            for sgn in (-1, 1):
                e0, e1 = sorted((s + sgn * hw, s + sgn * (hw + w_)))
                _prism(a, "limestone_trim", frame, [(e0, y0), (e1, y0), (e1, y1), (e0, y1)],
                       0.0, qn["proud_m"], gseed, conf)
    hd = li.get("hood")
    if hd:
        half = hw + hd["over_m"]
        def top(t):   # t from -1 to 1 across the hood
            y = yt + hd["height_m"]
            if abs(t) < 0.35:
                y += hd["crown_m"] * (1 + math.cos(math.pi * t / 0.35)) / 2
            if abs(t) > 0.8:
                y += hd["flick_m"] * ((abs(t) - 0.8) / 0.2) ** 2
            return y
        for i in range(HOOD_STRIPS):
            t0, t1 = -1 + 2 * i / HOOD_STRIPS, -1 + 2 * (i + 1) / HOOD_STRIPS
            x0, x1 = s + t0 * half, s + t1 * half
            _prism(a, "limestone_trim", frame, [(x0, yt), (x1, yt), (x1, top(t1)), (x0, top(t0))],
                   0.0, hd["proud_m"], gseed, conf)
    sf = li.get("shelf")
    if sf:
        half = hw + sf["over_m"]
        _prism(a, "limestone_trim", frame, [(s - half, yb - sf["height_m"]), (s + half, yb - sf["height_m"]),
                                            (s + half, yb), (s - half, yb)], 0.0, sf["proud_m"], gseed, conf)
        if sf["band_m"]:
            y1 = yb - sf["height_m"]
            _prism(a, "limestone_trim", frame, [(s - hw, y1 - sf["band_m"]), (s + hw, y1 - sf["band_m"]),
                                                (s + hw, y1), (s - hw, y1)], 0.0, sf["band_proud_m"], gseed, conf)


def dress(a, roof_seed):
    """The lights' sashes, the coping band on the face, the kneelers and the finial."""
    from . import k06_windows as k6
    from archetypes.k01_frontage_params import Opening
    from . import k01_frontage as k
    af = _af()
    p, sg, g = a.p, a.p.shaped_gable, a.shaped_gable_geom
    conf = p.worst_conf("shaped_gable")
    W = p.width_m
    R = (0.0, 0.0, -1.0)
    N = k._cross(R, k.Y)
    O = (g["xf"], 0.0, 0.0)            # s along the front from its south end, y over grade
    frame = (O, R, N)
    gseed = a.instance("k01.roof.shaped_gable", "roof",
                       {"foot_m": sg["foot_m"], "ledge_m": round(g["ledge"], 4), "apex_m": g["apex"],
                        "thickness_m": sg["thickness_m"], "proud_m": sg["proud_m"],
                        "lights": len(sg["lights"]["at_m"]), "profile_points": len(sg["profile_m"])},
                       {"foot": (g["xf"], sg["foot_m"], g["zc"]), "apex": (g["xf"], g["apex"], g["zc"])})
    # the lights: K06's sash in each recess
    li = sg["lights"]
    if not hasattr(a, "_kit"):
        a._kit = k6.load()
    v = _variant(sg, k6)
    roles = {r: ("limestone_trim" if m == "stone" else (m or "dormer_stone")) for r, m in a.K06_ROLES.items()}
    rev = k6.load()["parts"]["reveal_depth_m"]["value"]
    for at in li["at_m"]:
        s = W / 2 + at
        for sill in row_sills(li):
            if li.get("glazing") == "dark":
                _dark_lights(a, frame, v, s, sill, rev, gseed, conf)
                continue
            op = Opening("k01.opening.gable_light", "k01.wall.shaped_gable", s, sill, li["width_m"], li["height_m"])
            seed = a.instance(op.component, "opening", {"clear_width_m": li["width_m"], "clear_height_m": li["height_m"],
                                                        "k06_variant": v["id"], "wall": op.wall},
                              {"sill": k._add(O, k._add(k._mul(R, s), k._mul(k.Y, sill)))})
            o = k6.Opening(v, a._kit)
            o.seed = seed
            o.build()
            a.graft(o, "K06", roles, frame, op, lambda role, sd=seed: (sd, conf), ("reveal",))
        _window_dress(a, frame, li, s, gseed, conf)
        if li.get("rows", 1) < 2:
            continue
        # T-2951: a grid window's stone — the transom between each row and the one over it,
        # across the window, and the group's mullions up its whole height
        hw = li["width_m"] / 2
        rs = row_sills(li)
        for y0 in rs[1:]:
            y1 = y0 - li["transom_m"]
            _prism(a, "limestone_trim", frame, [(s - hw, y1), (s + hw, y1), (s + hw, y0), (s - hw, y0)],
                   0.0, TRANSOM_PROUD_M, gseed, conf)
        n, m = v.get("bays", 1), v.get("mullion_m", 0.0)
        bw = (li["width_m"] - (n - 1) * m) / n
        yb, yt = rs[0], rs[-1] + li["height_m"]
        for i in range(n - 1):
            m0 = s - hw + (i + 1) * bw + i * m
            _prism(a, "limestone_trim", frame, [(m0, yb), (m0 + m, yb), (m0 + m, yt), (m0, yt)],
                   0.0, TRANSOM_PROUD_M, gseed, conf)
    # the coping band: a dressed stone strip on the face along the outline, both sides
    cw, cp = sg["coping"]["width_m"], sg["coping"]["proud_m"]
    right = g["right"]
    for sgn in (1, -1):
        for (w0, y0), (w1, y1) in zip(right, right[1:]):
            dx, dy = (w1 - w0) * sgn, y1 - y0
            L = math.hypot(dx, dy)
            nx, ny = -dy / L * sgn, dx / L * sgn          # toward the gable's inside
            if ny > 0:
                nx, ny = -nx, -ny
            A_, B_ = (W / 2 + sgn * w0, y0), (W / 2 + sgn * w1, y1)
            poly = [A_, B_, (B_[0] + nx * cw, B_[1] + ny * cw), (A_[0] + nx * cw, A_[1] + ny * cw)]
            if w1 == 0.0 and not sg["finial"]:
                # T-2730: with no finial over it the two rakes' coping meets mitred on the
                # centre line, its inner edge cut where it crosses the apex's plumb line
                t_ = (W / 2 - poly[3][0]) / dx
                poly[2] = (W / 2, poly[3][1] + t_ * dy)
            _prism(a, "limestone_trim", frame, poly, 0.0, cp, gseed, conf)
    if sg.get("oculus"):
        _oculus(a, frame, sg, g, gseed, conf)
    if sg.get("shoulders"):
        _shoulders(a, frame, sg, gseed, conf)
    # the kneelers: a square pinnacle on each ledge, a cap and a pyramid over it
    kn = sg["kneelers"]
    xm = g["xf"] - sg["thickness_m"] / 2
    Fr = ((xm, 0.0, 0.0), R, N)
    hw = kn["shaft_m"] / 2 if kn else 0.0
    for sgn in ((-1, 1) if kn else ()):  # T-2730: a plain coped gable's ledge is its kneeler
        s = W / 2 + sgn * kn["at_m"]
        y0, y1 = g["ledge"], kn["top_m"]
        pseed = a.instance("k01.roof.gable_pinnacle", "roof",
                           {"shaft_m": kn["shaft_m"], "top_m": y1, "cap_m": kn["cap_m"], "spire_m": kn["spire_m"]},
                           {"foot": (xm, round(y0, 4), round(-s, 4))})
        af._box(a, "limestone_trim", Fr, s - hw, s + hw, y0, y1, -hw, hw, pseed, conf, skip=("bottom", "top"))
        c = hw + PIN_CAP_PROUD_M
        af._box(a, "limestone_trim", Fr, s - c, s + c, y1, y1 + kn["cap_m"], -c, c, pseed, conf)
        from . import k01_wall_gable
        k01_wall_gable._pyramid(a, "limestone_trim", Fr, s, 0.0, y1 + kn["cap_m"], hw,
                                y1 + kn["cap_m"] + kn["spire_m"], pseed, conf)
        if kn.get("scroll"):
            _scroll(a, frame, sg, W, sgn, conf)
    # the finial: a turned stone on the apex, let into it
    fn = sg["finial"]
    if not fn:
        return
    ya = g["apex"] - FINIAL_SINK_M
    fseed = a.instance("k01.roof.gable_finial", "roof", {"height_m": fn["height_m"], "radius_m": fn["radius_m"]},
                       {"foot": (xm, round(ya, 4), g["zc"])})
    Ff = ((xm, 0.0, g["zc"]), R, N)
    rr, hgt = fn["radius_m"], fn["height_m"]
    if fn.get("form") == "urn":
        # T-3090: a carved ball on the apex's plinth and an urn over it on a moulded foot,
        # under a lid and a knob — the c. 1955 photograph's, which Levy's print cuts at the
        # urn's foot. Turned on URN_PROFILE, (height, radius) of the whole and of the ball.
        pts = [(ya + hgt * f, rr * q) for f, q in URN_PROFILE]
        for (y0, r0), (y1, r1) in zip(pts, pts[1:]):
            if y1 - y0 > 1e-6 or abs(r1 - r0) > 1e-6:
                af._frustum(a, "limestone_trim", Ff, 0.0, 0.0, y0, y1, r0, r1, fseed, conf)
        return
    af._frustum(a, "limestone_trim", Ff, 0.0, 0.0, ya, ya + 0.3 * hgt, rr, rr * 1.1, fseed, conf)
    af._frustum(a, "limestone_trim", Ff, 0.0, 0.0, ya + 0.3 * hgt, ya + 0.55 * hgt, rr * 1.1, rr * 0.5, fseed, conf)
    af._frustum(a, "limestone_trim", Ff, 0.0, 0.0, ya + 0.55 * hgt, ya + hgt, rr * 0.5, 0.004, fseed, conf)
