"""T-3255: a K01 wall's round-headed lights under eared and crested stone hoods, and the main
block's corners dressed as stone pilasters under carved capitals, as 1701 Prairie stands in
its photograph.

TICKET T-3255 (piece 2 of T-1876). Chicagology's photograph of the Hibbard house shows every
round-headed light of the front and the south flank under a light stone hood: a broad band
round the arch whose feet step out into ears at the springing and hang a short way down the
jambs, and a pointed crest standing up off the band's crown. The front's south-west corner
is a tall stone pilaster from the stone basement to a carved capital under the cornice. The
record names them `eared_round_heads` and `corner_pilasters`, and this module builds them:

  resolve_hoods()      the record checked: the walls it dresses, the band, ears and crest
                       inside their ranges, every dressed light round-headed, each hood under
                       the eave and clear of the light over it
  hood()               one light's hood in the wall's frame, in place of K06's arch band: the
                       band in twelve pieces, an ear each side (stopped half way to a
                       neighbour's, so a pair's ears meet and never overlap) and the crest
  resolve_pilasters()  the record checked: corners of the main block, a shaft between the
                       stone basement's top and the eave, a base and a capital in it
  corner_pilasters()   each named corner: a base, a shaft and a two-stage capital (its bell
                       and its abacus), each wrapped round the corner on both faces

The band, ear, crest and pilaster sizes are read off the photograph through its solved camera
at the scale of the lights the record already sizes; their sections, and the capital drawn as
two stepped blocks where the photograph shows carving, are this module's (docs/LIBERTIES.md
L-k01-hibbard-1701-3255). A record that names neither is the same bytes as before.
"""

from __future__ import annotations

import math

HOOD_WALLS = ("k01.wall.street_front", "k01.wall.side.north", "k01.wall.side.south")
HOOD_KEYS = {"walls", "band_m", "proud_m", "ear_m", "drop_m", "crest"}
CREST_KEYS = {"width_m", "height_m", "proud_m"}
ARC_PIECES = 12          # the band round a round head in this many straight pieces
CREST_BED_M = 0.06       # the crest's foot is let this far down into the band's crown

# a corner of the main block -> (the wall whose END it is, the wall whose START it is)
CORNERS = {
    "street_north": ("k01.wall.side.south", "k01.wall.street_front"),
    "street_south": ("k01.wall.street_front", "k01.wall.side.north"),
    "rear_south": ("k01.wall.side.north", "k01.wall.rear_service"),
    "rear_north": ("k01.wall.rear_service", "k01.wall.side.south"),
}
PILASTER_KEYS = {"corners", "width_m", "proud_m", "from_m", "to_m", "base_m", "capital_m"}
CAP_GROW_M = (0.03, 0.07)   # the capital's bell, then its abacus, this much wider and prouder
BASE_GROW_M = 0.03


class ParamError(ValueError):
    pass


def resolve_hoods(spec, *, openings, round_cut, eave) -> dict:
    """The record's `eared_round_heads`, checked against the lights it dresses (module doc)."""
    if not spec:
        return {}
    if not isinstance(spec, dict) or set(spec) != HOOD_KEYS or not isinstance(spec["crest"], dict) \
            or set(spec["crest"]) != CREST_KEYS:
        raise ParamError(f"eared_round_heads takes {sorted(HOOD_KEYS)}, its crest {sorted(CREST_KEYS)}")
    walls = tuple(spec["walls"]) if isinstance(spec["walls"], list) else ()
    if not walls or len(set(walls)) != len(walls) or not set(walls) <= set(HOOD_WALLS):
        raise ParamError(f"eared_round_heads.walls names one or more of {list(HOOD_WALLS)}, once each")
    b, pr, ear, dr = (float(spec[k]) for k in ("band_m", "proud_m", "ear_m", "drop_m"))
    cw, ch, cp = (float(spec["crest"][k]) for k in ("width_m", "height_m", "proud_m"))
    if not (0.1 <= b <= 0.3 and 0.03 <= pr <= 0.12 and 0.05 <= ear <= 0.25 and 0.1 <= dr <= 0.6):
        raise ParamError("eared_round_heads: a 0.1-0.3 m band 0.03-0.12 m proud, its ears 0.05-0.25 m out past "
                         "it and 0.1-0.6 m down the jambs")
    if not (0.1 <= cw <= 0.6 and 0.1 <= ch <= 0.5 and pr <= cp <= pr + 0.06):
        raise ParamError("eared_round_heads.crest: 0.1-0.6 m wide, rising 0.1-0.5 m over the band, as proud as the "
                         "band up to 0.06 m prouder")
    lit = [o for o in openings if o.wall in walls and o.component in round_cut]
    for w in walls:
        if not any(o.wall == w for o in lit):
            raise ParamError(f"eared_round_heads.walls: {w} has no round-headed light to dress")
    for o in lit:
        if o.rise_over_span:
            raise ParamError(f"eared_round_heads: the light at s {o.s_m} on {o.wall} is segmental; the hood "
                             f"follows a round head")
        if cw / 2 >= o.width_m / 2 + b:
            raise ParamError(f"eared_round_heads.crest.width_m {cw}: wider than the band's crown over the light at "
                             f"s {o.s_m} on {o.wall}")
        top = o.head_m + b + ch
        if top > eave - 0.3:
            raise ParamError(f"eared_round_heads: the crest over the light at s {o.s_m} on {o.wall} reaches "
                             f"{top:.2f} m, inside 0.3 m of the {eave:.2f} m eave")
        over = [q for q in lit if q.wall == o.wall and abs(q.s_m - o.s_m) < (q.width_m + o.width_m) / 2 + 2 * b
                and q.sill_m > o.head_m]
        if any(q.sill_m - 0.15 < top for q in over):
            raise ParamError(f"eared_round_heads: the crest over the light at s {o.s_m} on {o.wall} reaches "
                             f"{top:.2f} m, into the sill of the light over it")
    return {"walls": walls, "band_m": b, "proud_m": pr, "ear_m": ear, "drop_m": dr,
            "crest": {"width_m": cw, "height_m": ch, "proud_m": cp}}


def dresses(p, op) -> bool:
    """Does the record's eared hood dress this light (a round one on a wall it names)?"""
    h = p.eared_hoods
    return bool(h) and op.wall in h["walls"]


def prism(a, mat, frame, pts, d0, d1, seed, conf):
    """A convex outline `pts` ((s, y) in the wall's frame, either winding) stood out of the wall
    from `d0` to `d1`: its face and its sides; its back stays in the wall."""
    from .k01_frontage import Y, _add, _mul, _sub
    O, R, N = frame
    P = lambda s, y, d: _add(_add(_add(O, _mul(R, s)), _mul(Y, y)), _mul(N, d))
    area = 0.0                               # twice the signed area, added left to right (T-2363)
    for i in range(len(pts)):
        area += pts[i][0] * pts[(i + 1) % len(pts)][1] - pts[(i + 1) % len(pts)][0] * pts[i][1]
    if area < 0:
        pts = list(reversed(pts))
    pr = a.prim(mat)
    pr.face([P(s, y, d1) for s, y in pts], N, a.basis(mat, O, R, Y, seed), conf)
    for i, (s0, y0) in enumerate(pts):
        s1, y1 = pts[(i + 1) % len(pts)]
        ln = math.hypot(s1 - s0, y1 - y0)
        if ln < 1e-6:
            continue
        ns, ny = (y1 - y0) / ln, -(s1 - s0) / ln          # outward, the outline counter-clockwise
        n = _add(_mul(R, ns), _mul(Y, ny))
        along = _sub(P(s1, y1, 0.0), P(s0, y0, 0.0))
        pr.face([P(s0, y0, d0), P(s1, y1, d0), P(s1, y1, d1), P(s0, y0, d1)], n,
                a.basis(mat, P(s0, y0, 0.0), _mul(along, 1.0 / ln), N, seed), conf)


def hood(a, op, frame, mat, seed, conf):
    """One light's eared and crested hood (module doc), in the wall's frame."""
    h = a.p.eared_hoods
    b, pr, ear, dr = h["band_m"], h["proud_m"], h["ear_m"], h["drop_m"]
    c, r = op.s_m, op.width_m / 2
    ri, ro = r, r + b
    ys = op.head_m - r                       # the springing
    # a neighbour on the same wall whose hood stands level with this one stops the ear half way
    lo, hi = c - ro - ear, c + ro + ear
    for q in a.p.openings:
        if q is op or q.wall != op.wall or not dresses(a.p, q) or abs(q.head_m - op.head_m) > dr:
            continue
        mid = (q.s_m + c) / 2
        if q.s_m < c:
            lo = max(lo, mid)
        elif q.s_m > c:
            hi = min(hi, mid)
    if lo > c - ro or hi < c + ro:
        raise ValueError(f"{op.wall} s {op.s_m}: the hood's band runs into its neighbour's")
    for i in range(ARC_PIECES):
        t0, t1 = math.pi * i / ARC_PIECES, math.pi * (i + 1) / ARC_PIECES
        prism(a, mat, frame, [(c + ri * math.cos(t0), ys + ri * math.sin(t0)),
                              (c + ro * math.cos(t0), ys + ro * math.sin(t0)),
                              (c + ro * math.cos(t1), ys + ro * math.sin(t1)),
                              (c + ri * math.cos(t1), ys + ri * math.sin(t1))], 0.0, pr, seed, conf)
    for s0, s1 in ((lo, c - ri), (c + ri, hi)):    # the ears, the band's feet stepped out
        prism(a, mat, frame, [(s0, ys - dr), (s1, ys - dr), (s1, ys), (s0, ys)], 0.0, pr, seed, conf)
    cw, ch, cp = h["crest"]["width_m"], h["crest"]["height_m"], h["crest"]["proud_m"]
    y0 = ys + ro - CREST_BED_M
    prism(a, mat, frame, [(c - cw / 2, y0), (c + cw / 2, y0), (c + cw / 2, ys + ro + ch * 0.35),
                          (c, ys + ro + ch), (c - cw / 2, ys + ro + ch * 0.35)], 0.0, cp, seed, conf)
    a.eared_hood_meta = getattr(a, "eared_hood_meta", []) + [
        {"wall": op.wall, "s_m": op.s_m, "ears_m": [round(lo, 4), round(hi, 4)],
         "crest_top_m": round(ys + ro + ch, 4)}]


def resolve_pilasters(spec, *, floor, eave) -> dict:
    """The record's `corner_pilasters`, checked against the main block (module doc)."""
    if not spec:
        return {}
    if not isinstance(spec, dict) or set(spec) != PILASTER_KEYS:
        raise ParamError(f"corner_pilasters takes {sorted(PILASTER_KEYS)}")
    cs = tuple(spec["corners"]) if isinstance(spec["corners"], list) else ()
    if not cs or len(set(cs)) != len(cs) or not set(cs) <= set(CORNERS):
        raise ParamError(f"corner_pilasters.corners names one or more of {sorted(CORNERS)}, once each")
    w, d, y0, y1, hb, hc = (float(spec[k]) for k in ("width_m", "proud_m", "from_m", "to_m", "base_m",
                                                      "capital_m"))
    if not (0.2 <= w <= 0.8 and 0.04 <= d <= 0.2 and 0.1 <= hb <= 0.5 and 0.2 <= hc <= 0.8):
        raise ParamError("corner_pilasters: a shaft 0.2-0.8 m broad on each face, 0.04-0.2 m proud, a 0.1-0.5 m "
                         "base and a 0.2-0.8 m capital")
    if not 0.0 <= y0 <= floor + 1e-6 or not y1 <= eave + 1e-6 \
            or y1 - y0 < hb + hc + 2.0:
        raise ParamError(f"corner_pilasters: from_m {y0} at or under the principal floor ({floor} m), to_m {y1} "
                         f"under the {eave:.2f} m eave, two metres of shaft between base and capital")
    return {"corners": cs, "width_m": w, "proud_m": d, "from_m": y0, "to_m": y1, "base_m": hb,
            "capital_m": hc}


def corner_pilasters(a, frames):
    """Each named corner's pilaster (module doc): base, shaft, bell and abacus, each a block on
    the wall the corner ends and a block on the wall it starts, the second carried round the
    corner by the first's projection, so the two faces meet at a clean arris."""
    p, cp = a.p, a.p.corner_pilasters
    conf = max(p.conf("corner_pilasters"), p.conf("footprint"))
    mat = "limestone_trim"
    w, d, y0, y1, hb, hc = (cp[k] for k in ("width_m", "proud_m", "from_m", "to_m", "base_m", "capital_m"))
    lengths = {"k01.wall.street_front": p.width_m, "k01.wall.side.north": p.depth_m,
               "k01.wall.side.south": p.depth_m, "k01.wall.rear_service": p.width_m}
    ym = y1 - hc * 0.45                      # the bell's top, the abacus's bed
    stages = ((y0, y0 + hb, BASE_GROW_M), (y0 + hb, ym - hc * 0.55, 0.0), (ym - hc * 0.55, ym, CAP_GROW_M[0]),
              (ym, y1, CAP_GROW_M[1]))
    for corner in cp["corners"]:
        end_wall, start_wall = CORNERS[corner]
        (fe, _), (fs, _) = frames[end_wall], frames[start_wall]
        L = lengths[end_wall]
        seed = a.instance("k01.corner_pilaster", "trim",
                          {"corner": corner, "width_m": w, "proud_m": d, "base_m": hb, "capital_m": hc},
                          {"foot": _at(fe[0], L, y0), "head": _at(fe[0], L, y1)})
        for ya, yb, g in stages:
            dd = d + g
            # on the wall the corner ends: up to the corner; on the one it starts: round it
            prism(a, mat, fe[0], [(L - w - g, ya), (L, ya), (L, yb), (L - w - g, yb)], 0.0, dd, seed, conf)
            prism(a, mat, fs[0], [(-dd, ya), (w + g, ya), (w + g, yb), (-dd, yb)], 0.0, dd, seed, conf)
        a.corner_pilaster_meta = getattr(a, "corner_pilaster_meta", []) + [
            {"corner": corner, "from_m": y0, "to_m": y1}]


def _at(frame, s, y):
    from .k01_frontage import Y, _add, _mul
    O, R, _N = frame
    return _add(_add(O, _mul(R, s)), _mul(Y, y))
