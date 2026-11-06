"""T-1881: a hanging lantern on a wrought-iron bracket fixed to a K01 house's street front, as
1729 Prairie's hangs beside its portico in the 1890 Albertype plate.

TICKET T-1881 (the image gate on pullman_house_1729_prairie). The plate (Prairie library
a16-albertype-1890-pullman-residence; data/reference_views/pullman_house_1729_prairie/
albertype_1890.json) draws, just south of the portico and under the belt course, a dark
bell-shaped fitting between two banded piers: a cap widening downward over a glazed body and a
small drop, about 0.7 m across and 0.9 m tall at the plate's 22 px a metre. Through the plate's
solved camera the two piers and the gap between them are the entrance part's south corner
pilaster, its 1.6 m south return, and a pilaster at the inner angle on the main wall (widths
17, 15 and 15 px against the build's 16, 17 and 16), so the lantern hangs off the return, which
faces 18th Street. No K01, K07 or K08 kit drew a lantern on a wall; the record names this one
`wall_lanterns` and this module builds it:

  resolve()   the record checked against the house: on the street front, inside its run, its
              face one of the wall's own (`out`) or a return looking along it (`+s`/`-s`),
              its arm and lantern of a hanging lantern's size, hung under the eave
  dress()     each lantern's back plate and arm with its brace, the drop rod, the bell cap and
              its brim, the glazed body on iron corner bars, the base and the drop finial

The lantern's place and size are read off the plate; its profile (how the bell curves, the
glazing's taper, the finial) and the bracket's section are this module's, below what the
plate resolves at 22 px a metre (docs/LIBERTIES.md L-k01-1729-pullman-lantern-1881). Every other
K01 house carries no `wall_lanterns`, so its bytes are unchanged.
"""

from __future__ import annotations

import math

KEYS = {"wall", "at_m", "faces", "hang_m", "arm_m", "lantern"}
LANTERN_KEYS = {"width_m", "height_m"}
WALLS = ("k01.wall.street_front",)
FACES = ("out", "+s", "-s")
IRON, GLASS = "iron", "glass"
SIDES = 8


class ParamError(ValueError):
    pass


def resolve(spec, *, width, eave) -> list:
    """The record's `wall_lanterns`, checked against the house (module doc)."""
    if not spec:
        return []
    if not isinstance(spec, list):
        raise ParamError("wall_lanterns is a list of lanterns")
    out = []
    for j, L in enumerate(spec):
        if not isinstance(L, dict) or set(L) != KEYS or not isinstance(L["lantern"], dict) \
                or set(L["lantern"]) != LANTERN_KEYS:
            raise ParamError(f"wall_lanterns[{j}] takes {sorted(KEYS)}, its lantern {sorted(LANTERN_KEYS)}")
        if L["wall"] not in WALLS or L["faces"] not in FACES:
            raise ParamError(f"wall_lanterns[{j}]: on {WALLS}, its face looking one of {FACES}")
        s, o = (float(x) for x in L["at_m"])
        hang, arm = float(L["hang_m"]), float(L["arm_m"])
        w, h = float(L["lantern"]["width_m"]), float(L["lantern"]["height_m"])
        if not (0.0 <= s <= width and 0.0 <= o <= 4.0) or (L["faces"] == "out" and o > 0.5):
            raise ParamError(f"wall_lanterns[{j}].at_m {L['at_m']}: along the wall inside 0..{width} m, at most "
                             f"4 m out on a return, 0.5 m on the wall's own face")
        if not (0.3 <= w <= 1.0 and 0.4 <= h <= 1.5 and w / 2 + 0.05 <= arm <= 1.2):
            raise ParamError(f"wall_lanterns[{j}]: a lantern 0.3-1 m across and 0.4-1.5 m tall, its axis "
                             f"0.05 m clear of the face past its half-width and at most 1.2 m out")
        if not (2.2 + h <= hang <= eave - 0.3):
            raise ParamError(f"wall_lanterns[{j}].hang_m {hang}: its foot at least 2.2 m over grade, its arm "
                             f"at least 0.3 m under the eave ({eave} m)")
        out.append({"wall": L["wall"], "at_m": (s, o), "faces": L["faces"], "hang_m": hang, "arm_m": arm,
                    "width_m": w, "height_m": h})
    return out


def profile(w, h):
    """The lantern's half-section, top to bottom: (radius, depth under the arm, material).
    A ring and a short drop rod, the bell cap curving out to its brim, the glazed body tapering
    in, the base and the drop finial."""
    R = w / 2
    pts = [(0.0, 0.0, IRON), (0.035, 0.0, IRON), (0.035, 0.06, IRON), (0.05, 0.06, IRON)]
    cap = 0.3 * h
    for i in range(1, 5):
        t = i / 4
        pts.append((0.05 + (R - 0.05) * t ** 1.7, 0.06 + cap * t, IRON))
    brim = 0.06 + cap
    pts += [(R, brim + 0.035, IRON), (0.84 * R, brim + 0.035, IRON)]
    g0, g1 = brim + 0.035, 0.82 * h
    pts += [(0.64 * R, g1, GLASS), (0.68 * R, g1, IRON), (0.68 * R, g1 + 0.03, IRON),
            (0.16 * R, 0.93 * h, IRON), (0.0, h, IRON)]
    return pts, (g0, g1)


def dress(a):
    """The lanterns, each on its bracket (module doc)."""
    from .k01_frontage import Y, _add, _mul
    p = a.p
    conf = p.worst_conf("footprint", "wall_lanterns")
    D = p.depth_m
    # the street front's frame: origin, along it, out of it (k01_pavilions' `front`)
    O, R_, N = (D, 0.0, 0.0), (0.0, 0.0, -1.0), (1.0, 0.0, 0.0)
    at = lambda s, y, o: _add(_add(_add(O, _mul(R_, s)), _mul(Y, y)), _mul(N, o))
    prims = {m: a.prim(m) for m in (IRON, GLASS)}
    meta = []
    for L in p.wall_lanterns:
        s, o = L["at_m"]
        f = {"out": N, "+s": R_, "-s": _mul(R_, -1)}[L["faces"]]
        side = {"out": R_, "+s": N, "-s": N}[L["faces"]]          # across the arm, level
        root = at(s, L["hang_m"], o)
        axis = _add(root, _mul(f, L["arm_m"]))
        top = L["hang_m"]
        seed = a.instance("k01.wall_lantern", "lantern",
                          {"s_m": s, "out_m": o, "faces": L["faces"], "hang_m": top, "arm_m": L["arm_m"],
                           "width_m": L["width_m"], "height_m": L["height_m"]},
                          {"bracket": root, "lantern": (axis[0], top - L["height_m"] / 2, axis[2])})
        bases = {m: a.basis(m, root, side, Y, seed) for m in (IRON, GLASS)}

        def bar(p0, p1, t, m=IRON):
            """A square iron bar t across from p0 to p1, its sides level and plumb-ish."""
            d = tuple(q - r for q, r in zip(p1, p0))
            ln = math.sqrt(math.fsum(x * x for x in d))
            u = tuple(x / ln for x in d)
            v = side
            wv = (u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0])
            c = [(-1, -1), (1, -1), (1, 1), (-1, 1)]
            ring = lambda P: [_add(_add(P, _mul(v, t / 2 * x)), _mul(wv, t / 2 * y)) for x, y in c]
            r0, r1 = ring(p0), ring(p1)
            for k in range(4):
                n_ = _add(_mul(v, c[k][0] + c[(k + 1) % 4][0]), _mul(wv, c[k][1] + c[(k + 1) % 4][1]))
                prims[m].face([r0[k], r0[(k + 1) % 4], r1[(k + 1) % 4], r1[k]], n_, bases[m], conf)
            prims[m].face(r1, u, bases[m], conf)
            prims[m].face(r0, _mul(u, -1), bases[m], conf)

        # the back plate on the face, the arm out to the axis, its brace from under the plate,
        # and a scroll's worth of upturn at the arm's end
        plate = at(s, top - 0.12, o)
        a.proud_box(IRON, (_add(root, _mul(Y, -0.27)), side, f), -0.07, 0.07, 0.0, 0.34, 0.025, seed, conf)
        bar(root, _add(axis, _mul(f, 0.06)), 0.04)
        bar(_add(plate, _mul(Y, -0.2)), _add(root, _mul(f, 0.6 * L["arm_m"])), 0.03)
        bar(_add(axis, _mul(f, 0.06)), _add(_add(axis, _mul(f, 0.06)), _mul(Y, 0.08)), 0.04)
        # the lantern: a surface of revolution, eight-sided, hung from the arm on its axis
        pts, (g0, g1) = profile(L["width_m"], L["height_m"])
        P = lambda r, dy, k: _add(_add(axis, _mul(Y, -dy)),
                                  _add(_mul(f, r * math.cos(2 * math.pi * (k + 0.5) / SIDES)),
                                       _mul(side, r * math.sin(2 * math.pi * (k + 0.5) / SIDES))))
        for (r0, y0, _), (r1, y1, m) in zip(pts, pts[1:]):
            dr, dy = r1 - r0, -(y1 - y0)                 # down the profile, y up
            for k in range(SIDES):
                am = 2 * math.pi * (k + 1) / SIDES
                rad = _add(_mul(f, math.cos(am)), _mul(side, math.sin(am)))
                n_ = _add(_mul(rad, -dy), _mul(Y, dr))
                quad = [P(r0, y0, k), P(r0, y0, k + 1), P(r1, y1, k + 1), P(r1, y1, k)]
                quad = [q for i, q in enumerate(quad) if all(
                    math.fsum((x - z) ** 2 for x, z in zip(q, quad[j])) > 1e-12 for j in range(i))]
                if len(quad) >= 3:
                    prims[m].face(quad, n_, bases[m], conf)
        # the glazing's iron corner bars, brim to base
        rg0, rg1 = 0.84 * L["width_m"] / 2, 0.64 * L["width_m"] / 2
        for k in range(SIDES):
            bar(P(rg0, g0, k), P(rg1, g1, k), 0.02)
        meta.append({"s_m": s, "foot_m": round(top - L["height_m"], 4), "axis": [round(x, 4) for x in axis]})
    a.wall_lanterns_meta = meta
