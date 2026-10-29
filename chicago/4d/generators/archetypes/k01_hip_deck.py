"""T-3241: a hip cut off level at a railed deck, as 1701 Prairie's roof stands in its photographs.

TICKET T-3241 (piece 2 of T-1875). Chicagology's photograph of the Hibbard house shows its
low hip rising from the bracketed cornice on the front and the south flank to a flat deck,
railed all round with a pale parapet pierced by a row of round holes between posts; Glessner
House Museum's rear photograph shows the same rail over the rear. The record names it
`hip_deck` and this module builds it on the K01 house:

  resolve()   the record checked against the roof: on a hip, the deck at least 0.5 m over the
              eave and at least 2 m across under the ridge it replaces, its rail a parapet the
              holes fit inside
  hip()       K05's hip ring stack (k05_roofs.hip_element) with its last ring at the deck's
              height instead of the ridge, so the stack closes itself with a level top
  dress()     the rail round the deck's edge: a plinth, a panel pierced with a roundel in every
              bay of it, a coping, and posts at the corners and along each side

The deck's height is read off the photograph through its solved camera; the rail's section,
its holes' size and pitch and the posts' spacing are this module's (docs/LIBERTIES.md
L-k01-hibbard-1701-3241). K05's own hip is untouched, so every other roof is the same bytes.
"""

from __future__ import annotations

import math

KEYS = {"deck_m", "rail"}
RAIL_KEYS = {"inset_m", "height_m", "post_m", "posts_every_m", "plinth_m", "coping_m", "thickness_m",
             "roundel_m", "pitch_m"}
SEGMENTS = 16           # a roundel's circle in this many straight pieces


class ParamError(ValueError):
    pass


def resolve(spec, *, depth, width, eave, pitch, overhang, roof_form) -> dict:
    """The record's `hip_deck`, checked against the house's hip (module doc)."""
    if not spec:
        return {}
    if not isinstance(spec, dict) or set(spec) != KEYS or not isinstance(spec["rail"], dict) \
            or set(spec["rail"]) != RAIL_KEYS:
        raise ParamError(f"hip_deck takes {sorted(KEYS)}, its rail {sorted(RAIL_KEYS)}")
    if roof_form != "hip":
        raise ParamError("hip_deck cuts a hip off level: roof_form hip")
    t = math.tan(math.radians(pitch))
    he = eave - overhang * t                     # the hip's eave line, the fascia's top
    half = (min(depth, width) + 2 * overhang) / 2
    deck = float(spec["deck_m"])
    rise = deck - he
    k = rise / t
    if rise < 0.5 or k > half - 1.0:
        raise ParamError(f"hip_deck.deck_m {deck}: at least 0.5 m over the hip's eave ({he:.2f} m) and leaving "
                         f"a deck at least 2 m across under the {he + half * t:.2f} m ridge")
    r = {n: float(v) for n, v in spec["rail"].items()}
    hole = r["height_m"] - r["plinth_m"] - r["coping_m"]
    if not (0.0 <= r["inset_m"] <= 0.5 and 0.4 <= r["height_m"] <= 1.2 and 0.1 <= r["post_m"] <= 0.5
            and 1.0 <= r["posts_every_m"] <= 4.0 and 0.04 <= r["plinth_m"] <= 0.3 and 0.04 <= r["coping_m"] <= 0.2
            and 0.05 <= r["thickness_m"] <= r["post_m"] and 0.1 <= r["roundel_m"] <= hole - 0.04
            and r["roundel_m"] + 0.04 <= r["pitch_m"] <= 1.0):
        raise ParamError("hip_deck.rail: 0-0.5 m in from the deck's edge, 0.4-1.2 m high on 0.1-0.5 m posts 1-4 m "
                         "apart, a 0.04-0.3 m plinth and 0.04-0.2 m coping, a panel no thicker than a post, "
                         "its roundels clear of plinth and coping and of each other")
    X0, X1, Z0, Z1 = -overhang + k, depth + overhang - k, -width - overhang + k, overhang - k
    return {"deck_m": round(deck, 4), "rise_m": round(rise, 4), "inset_m": round(k, 4),
            "rect": [round(X0, 4), round(X1, 4), round(Z0, 4), round(Z1, 4)], "rail": r}


def hip(k5, x0, x1, z0, z1, eave_y, t, o, f, deck):
    """K05's hip over the wall-line rectangle, cut off level at the deck (module doc)."""
    hs, he = eave_y - o * t - f, eave_y - o * t
    X0, X1, Z0, Z1 = x0 - o, x1 + o, z0 - o, z1 + o
    rise = deck["deck_m"] - he
    rings = [(hs, k5.inset_rect(X0, X1, Z0, Z1, 0.0)), (he, k5.inset_rect(X0, X1, Z0, Z1, 0.0)),
             (he + rise, k5.inset_rect(X0, X1, Z0, Z1, rise / t))]
    return k5.ring_stack(rings, ["fascia", "covering"], "soffit"), hs


def dress(a):
    """The deck's rail: plinth, pierced panel, coping and posts round its four sides."""
    from .k01_frontage import Y, _mul
    p, dk = a.p, a.p.hip_deck
    conf = max(p.conf("hip_deck"), p.conf("roof_form"))
    mat = "bay_stone"
    pr = a.prim(mat)
    r = dk["rail"]
    X0, X1, Z0, Z1 = dk["rect"]
    yd = dk["deck_m"]
    i, th, pm = r["inset_m"], r["thickness_m"], r["post_m"]
    XA, XB, ZA, ZB = X0 + i, X1 - i, Z0 + i, Z1 - i          # the rail's outer line
    seed = a.instance("k01.hip_deck", "roof_deck",
                      {"deck_m": yd, "inset_m": dk["inset_m"], "rail_height_m": r["height_m"]},
                      {"deck": ((X0 + X1) / 2, yd, (Z0 + Z1) / 2)})
    O, X, Z = (0.0, yd, 0.0), (1.0, 0.0, 0.0), (0.0, 0.0, 1.0)
    bx, bz, bh = a.basis(mat, O, X, Y, seed), a.basis(mat, O, Z, Y, seed), a.basis(mat, O, X, Z, seed)
    quad = lambda pts, n, b: pr.face(pts, n, b, conf)
    up, down = Y, _mul(Y, -1)

    def box(x0, x1, y0, y1, z0, z1, skip=()):
        f = {"+x": ([(x1, y0, z0), (x1, y1, z0), (x1, y1, z1), (x1, y0, z1)], X, bz),
             "-x": ([(x0, y0, z0), (x0, y1, z0), (x0, y1, z1), (x0, y0, z1)], _mul(X, -1), bz),
             "+z": ([(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)], Z, bx),
             "-z": ([(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0)], _mul(Z, -1), bx),
             "top": ([(x0, y1, z0), (x1, y1, z0), (x1, y1, z1), (x0, y1, z1)], up, bh),
             "bottom": ([(x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1)], down, bh)}
        for k, (pts, n, b) in f.items():
            if k not in skip:
                quad(pts, n, b)

    yp, yc, yt = yd + r["plinth_m"], yd + r["height_m"] - r["coping_m"], yd + r["height_m"]
    rad = r["roundel_m"] / 2
    holes = 0
    # each side: its run's ends (the corner posts' inner faces) and where its panel's middle stands
    runs = [("x", XA + pm, XB - pm, ZA + pm / 2), ("x", XA + pm, XB - pm, ZB - pm / 2),
            ("z", ZA + pm, ZB - pm, XA + pm / 2), ("z", ZA + pm, ZB - pm, XB - pm / 2)]
    for x_, z_ in ((XA, ZA), (XB - pm, ZA), (XA, ZB - pm), (XB - pm, ZB - pm)):   # the corner posts
        box(x_, x_ + pm, yd, yt + 0.05, z_, z_ + pm, skip=("bottom",))
    for axis, a0, a1, c in runs:
        n = max(1, math.ceil((a1 - a0) / (r["posts_every_m"] - pm)))
        step = (a1 - a0 + pm) / n                           # a bay of the side, post to post
        W = (lambda a_, y, w: (a_, y, w)) if axis == "x" else (lambda a_, y, w: (w, y, a_))
        A, Nw = (X, Z) if axis == "x" else (Z, X)
        b_face = bx if axis == "x" else bz

        def bx_(a_0, a_1, y0, y1, w0, w1, skip=()):
            (x0, _, z0), (x1, _, z1) = W(a_0, 0.0, w0), W(a_1, 0.0, w1)
            box(min(x0, x1), max(x0, x1), y0, y1, min(z0, z1), max(z0, z1), skip=skip)

        for j in range(n):
            b0 = a0 + j * step
            b1 = b0 + step - pm
            if j > 0:   # the post at the bay's start
                bx_(b0 - pm, b0, yd, yt + 0.05, c - pm / 2, c + pm / 2, skip=("bottom",))
            bx_(b0, b1, yd, yp, c - th / 2 - 0.02, c + th / 2 + 0.02, skip=("bottom",))
            bx_(b0, b1, yc, yt, c - th / 2 - 0.03, c + th / 2 + 0.03)
            # the panel between them, a roundel in each of its cells
            cells = max(1, round((b1 - b0) / r["pitch_m"]))
            cw = (b1 - b0) / cells
            ym, hh = (yp + yc) / 2, (yc - yp) / 2
            for q in range(cells):
                ac, hw = b0 + (q + 0.5) * cw, cw / 2
                rr = min(rad, hw - 0.02, hh - 0.02)
                corner = math.atan2(hh, hw)
                angs = sorted({2 * math.pi * s / SEGMENTS for s in range(SEGMENTS)}
                              | {corner, math.pi - corner, math.pi + corner, 2 * math.pi - corner})
                rect = lambda g: min(hw / abs(math.cos(g)) if abs(math.cos(g)) > 1e-9 else 1e9,
                                     hh / abs(math.sin(g)) if abs(math.sin(g)) > 1e-9 else 1e9)
                for g0, g1 in zip(angs, angs[1:] + [angs[0] + 2 * math.pi]):
                    for w, nn in ((c - th / 2, _mul(Nw, -1)), (c + th / 2, Nw)):
                        pts = [W(ac + rr * math.cos(g0), ym + rr * math.sin(g0), w),
                               W(ac + rr * math.cos(g1), ym + rr * math.sin(g1), w),
                               W(ac + rect(g1) * math.cos(g1), ym + rect(g1) * math.sin(g1), w),
                               W(ac + rect(g0) * math.cos(g0), ym + rect(g0) * math.sin(g0), w)]
                        quad(pts, nn, b_face)
                    gm = (g0 + g1) / 2   # the hole's own reveal, facing its middle
                    nrm = tuple(-math.cos(gm) * A[k] - math.sin(gm) * Y[k] for k in range(3))
                    quad([W(ac + rr * math.cos(g0), ym + rr * math.sin(g0), c - th / 2),
                          W(ac + rr * math.cos(g1), ym + rr * math.sin(g1), c - th / 2),
                          W(ac + rr * math.cos(g1), ym + rr * math.sin(g1), c + th / 2),
                          W(ac + rr * math.cos(g0), ym + rr * math.sin(g0), c + th / 2)], nrm, b_face)
                holes += 1
    a.hip_deck_meta = {"roundels": holes, "top_m": round(yt, 4)}
