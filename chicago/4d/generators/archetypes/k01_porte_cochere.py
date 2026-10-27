"""T-3160: a one-storey arcaded porte-cochere on a side wall, as 1729 Prairie's stands on 18th Street.

TICKET T-3160 (piece 4 of T-1881). The Detroit Publishing photograph of the Pullman house
(LC-D4-12551) shows, on the 18th Street flank near the Prairie corner, a one-storey block of
rusticated stone piers carrying round arches: one in its west end, seen nearly square to the
camera, and one in its south front, seen edge-on past the corner pier, under an entablature
and a balustrade at the second floor. The record names it `porte_cochere` and this module lays
it on the K01 house k01_frontage.build has finished:

  resolve()   the record checked against the house: on a side wall, inside it and clear of
              every opening on that wall under its deck, each arch inside its face with a pier
              left either side, its crown under the entablature
  dress()     three walls standing out from the side wall (the two ends and the front), each
              a pier-and-spandrel wall round its arch with the arch's soffit turned through
              it, an entablature over the whole plan (its soffit the passage's ceiling, its
              top the balcony's deck) and a balustrade round the deck's three open sides

The block's plan, the arches' places, spans and crowns, and the entablature's and the
balustrade's heights are read off the print through its solved camera; the walls' thickness,
the entablature's projection and the balustrade's section are this module's (docs/LIBERTIES.md
L-pullman-1729-porte-cochere-3160).
"""

from __future__ import annotations

import math

KEYS = {"wall", "s_m", "out_m", "thickness_m", "spring_m", "head_m", "arches", "entablature", "balustrade"}
FACES = ("low_end", "front", "high_end")
ENT_KEYS = {"height_m", "proud_m"}
BAL_KEYS = {"height_m", "post_m", "baluster_m", "pitch_m", "rail_m"}
SEGMENTS = 12           # an arch's half-circle in this many straight pieces
PIER_MIN_M = 0.4        # the least pier an arch leaves at either side of its face


class ParamError(ValueError):
    pass


def resolve(spec, *, depth, width, stone, openings) -> dict:
    """The record's `porte_cochere`, checked against the house (module doc)."""
    if not spec:
        return {}
    if not isinstance(spec, dict) or set(spec) != KEYS:
        raise ParamError(f"porte_cochere takes {sorted(KEYS)}")
    if not stone:
        raise ParamError("porte_cochere is laid in the front's stone: it needs a stone_front")
    wall = spec["wall"]
    if wall not in ("k01.wall.side.north", "k01.wall.side.south"):
        raise ParamError("porte_cochere.wall: k01.wall.side.north or k01.wall.side.south")
    s0, s1 = sorted(float(x) for x in spec["s_m"])
    out, t = float(spec["out_m"]), float(spec["thickness_m"])
    ys, H = float(spec["spring_m"]), float(spec["head_m"])
    if not 0.0 <= s0 < s1 <= depth or s1 - s0 < 3.0:
        raise ParamError(f"porte_cochere.s_m [{s0}, {s1}]: at least 3 m along the side wall, inside its {depth} m")
    if not 2.0 <= out <= 8.0 or not 0.3 <= t <= 1.2 or 2 * t > s1 - s0 - 1.0 or t > out - 1.0:
        raise ParamError("porte_cochere: 2-8 m out, its walls 0.3-1.2 m thick with a passage at least 1 m inside them")
    E, B = spec["entablature"], spec["balustrade"]
    if set(E) != ENT_KEYS or set(B) != BAL_KEYS or len(B["rail_m"]) != 2:
        raise ParamError("porte_cochere.entablature takes height_m and proud_m; its balustrade height_m, post_m, "
                         "baluster_m, pitch_m and rail_m [width, depth]")
    eh, ep = float(E["height_m"]), float(E["proud_m"])
    bh, bp, bb, bpi = (float(B[k]) for k in ("height_m", "post_m", "baluster_m", "pitch_m"))
    rw, rd = (float(x) for x in B["rail_m"])
    if not (0.15 <= eh <= 0.8 and 0.0 <= ep <= 0.4 and 0.4 <= bh <= 1.2 and 0.1 <= bp <= 0.5
            and 0.03 <= bb <= 0.2 and bb + 0.05 <= bpi <= 0.5 and 0.05 <= rw <= bp and 0.05 <= rd <= bh / 3):
        raise ParamError("porte_cochere: a 0.15-0.8 m entablature up to 0.4 m proud; a 0.4-1.2 m balustrade on "
                         "0.1-0.5 m posts, 0.03-0.2 m balusters at a wider pitch, its rail no wider than a post")
    lengths = {"low_end": out, "front": s1 - s0, "high_end": out}
    arches = []
    for j, ar in enumerate(spec["arches"]):
        if set(ar) != {"face", "centre_m", "span_m"} or ar["face"] not in FACES:
            raise ParamError(f"porte_cochere.arches[{j}] takes face ({', '.join(FACES)}), centre_m and span_m")
        # the front's centre is the side wall's own s; an end's is metres out from the wall
        c, w = float(ar["centre_m"]) - (s0 if ar["face"] == "front" else 0.0), float(ar["span_m"])
        L = lengths[ar["face"]]
        lo = t if ar["face"] == "front" else 0.0          # the front's corners are the end walls' piers
        hi = L - t                                        # an end's outer corner is the front wall's
        if not 1.0 <= w <= 5.0 or c - w / 2 < lo + PIER_MIN_M - 1e-6 or c + w / 2 > hi - PIER_MIN_M + 1e-6:
            raise ParamError(f"porte_cochere.arches[{j}]: a 1-5 m arch on its {L:.2f} m face leaving a "
                             f"{PIER_MIN_M} m pier each side")
        if any(a["face"] == ar["face"] for a in arches):
            raise ParamError(f"porte_cochere.arches[{j}]: one arch a face")
        if ys + w / 2 > H - 0.2:
            raise ParamError(f"porte_cochere.arches[{j}]: its crown ({ys + w / 2:.2f} m) stands within 0.2 m "
                             f"of the entablature at {H} m")
        arches.append({"face": ar["face"], "centre_m": c, "span_m": w})
    if not 2.5 <= ys < H <= 9.0:
        raise ParamError("porte_cochere: the arches spring at least 2.5 m up, under the entablature (at most 9 m)")
    top = H + eh + bh
    for o in openings:   # nothing on the side wall it stands against, under its deck's rail
        if o.wall == wall and o.s_m + o.width_m / 2 > s0 - 0.1 and o.s_m - o.width_m / 2 < s1 + 0.1 \
                and o.sill_m < top + 0.1:
            raise ParamError(f"porte_cochere (s {s0}-{s1}, to {top:.2f} m) stands over the opening at s {o.s_m} "
                             f"on {wall}")
    return {"wall": wall, "s_m": [s0, s1], "out_m": out, "thickness_m": t, "spring_m": ys, "head_m": H,
            "arches": arches, "entablature": {"height_m": eh, "proud_m": ep},
            "balustrade": {"height_m": bh, "post_m": bp, "baluster_m": bb, "pitch_m": bpi, "rail_m": [rw, rd]}}


def dress(a):
    """The arcade's walls, its entablature and its balustrade (module doc)."""
    from .k01_frontage import Y, _add, _mul
    p, pc = a.p, a.p.porte_cochere
    D, W = p.depth_m, p.width_m
    conf = p.worst_conf("footprint", "stone_front", "porte_cochere")
    if pc["wall"] == "k01.wall.side.north":
        O, R, N = (D, 0.0, -W), (-1.0, 0.0, 0.0), (0.0, 0.0, -1.0)
    else:
        O, R, N = (D, 0.0, 0.0), (-1.0, 0.0, 0.0), (0.0, 0.0, 1.0)
    P = lambda s, y, d: _add(_add(_add(O, _mul(R, s)), _mul(Y, y)), _mul(N, d))
    mat = "bay_stone"
    pr = a.prim(mat)
    (s0, s1), out, t = pc["s_m"], pc["out_m"], pc["thickness_m"]
    ys, H = pc["spring_m"], pc["head_m"]
    seed = a.instance("k01.porte_cochere", "porte_cochere",
                      {"s0_m": s0, "s1_m": s1, "out_m": out, "spring_m": ys, "head_m": H,
                       "arches": len(pc["arches"])},
                      {"deck": P((s0 + s1) / 2, H + pc["entablature"]["height_m"], out / 2)})
    bf, bh, be = a.basis(mat, O, R, Y, seed), a.basis(mat, O, R, N, seed), a.basis(mat, O, N, Y, seed)
    quad = lambda pts, n, b: pr.face(pts, n, b, conf)
    up, down = Y, _mul(Y, -1)

    # each wall in its own (a, y, w) coordinates: `a` along its face, `w` through it from the
    # outer face inwards; `at(a, y, w)` puts a point in the house, `nf` is its outer normal
    walls = {
        "front": (lambda a_, y, w: P(s0 + a_, y, out - w), N, s1 - s0, bf, be),
        "low_end": (lambda a_, y, w: P(s0 + w, y, a_), _mul(R, -1), out - t, be, bf),
        "high_end": (lambda a_, y, w: P(s1 - w, y, a_), R, out - t, be, bf),
    }
    arch_of = {ar["face"]: ar for ar in pc["arches"]}
    for face, (at, nf, L, b_face, b_end) in walls.items():
        ni = _mul(nf, -1)
        ar = arch_of.get(face)
        # the faces, outer then inner: piers and (over an arch) spandrel strips from its curve up
        for w, n in ((0.0, nf), (t, ni)):
            if ar:
                c, r = ar["centre_m"], ar["span_m"] / 2
                quad([at(0.0, 0.0, w), at(c - r, 0.0, w), at(c - r, H, w), at(0.0, H, w)], n, b_face)
                quad([at(c + r, 0.0, w), at(L, 0.0, w), at(L, H, w), at(c + r, H, w)], n, b_face)
                for k in range(SEGMENTS):
                    t0, t1 = math.pi * k / SEGMENTS, math.pi * (k + 1) / SEGMENTS
                    x0, y0 = c + r * math.cos(t0), ys + r * math.sin(t0)
                    x1, y1 = c + r * math.cos(t1), ys + r * math.sin(t1)
                    quad([at(x0, y0, w), at(x0, H, w), at(x1, H, w), at(x1, y1, w)], n, b_face)
            else:
                quad([at(0.0, 0.0, w), at(L, 0.0, w), at(L, H, w), at(0.0, H, w)], n, b_face)
        if ar:
            c, r = ar["centre_m"], ar["span_m"] / 2
            # the jambs, grade to springing, facing into the opening
            for x, k in ((c - r, 1.0), (c + r, -1.0)):
                dirn = _mul(_sub_(at(1.0, 0.0, 0.0), at(0.0, 0.0, 0.0)), k)
                quad([at(x, 0.0, 0.0), at(x, ys, 0.0), at(x, ys, t), at(x, 0.0, t)], dirn, b_end)
            # the arch's soffit, turned through the wall
            for k in range(SEGMENTS):
                t0, t1 = math.pi * k / SEGMENTS, math.pi * (k + 1) / SEGMENTS
                tm = (t0 + t1) / 2
                x0, y0 = c + r * math.cos(t0), ys + r * math.sin(t0)
                x1, y1 = c + r * math.cos(t1), ys + r * math.sin(t1)
                along = _sub_(at(1.0, 0.0, 0.0), at(0.0, 0.0, 0.0))
                n = _add(_mul(along, -math.cos(tm)), _mul(Y, -math.sin(tm)))
                quad([at(x0, y0, 0.0), at(x1, y1, 0.0), at(x1, y1, t), at(x0, y0, t)], n, bh)
    # the front wall's ends, past the end walls' outer faces (its corners turned)
    for s_, n in ((s0, _mul(R, -1)), (s1, R)):
        quad([P(s_, 0.0, out - t), P(s_, 0.0, out), P(s_, H, out), P(s_, H, out - t)], n, be)

    # the entablature: one slab over the whole plan, standing `proud` past the walls; its
    # underside the passage's ceiling inside the walls and the overhang's soffit outside them
    eh, ep = pc["entablature"]["height_m"], pc["entablature"]["proud_m"]
    S0, S1, Dd, y1 = s0 - ep, s1 + ep, out + ep, H + eh
    quad([P(S0, y1, 0.0), P(S1, y1, 0.0), P(S1, y1, Dd), P(S0, y1, Dd)], up, bh)
    quad([P(S0, H, Dd), P(S1, H, Dd), P(S1, y1, Dd), P(S0, y1, Dd)], N, bf)
    for s_, n in ((S0, _mul(R, -1)), (S1, R)):
        quad([P(s_, H, 0.0), P(s_, H, Dd), P(s_, y1, Dd), P(s_, y1, 0.0)], n, be)
    quad([P(s0 + t, H, 0.0), P(s1 - t, H, 0.0), P(s1 - t, H, out - t), P(s0 + t, H, out - t)], down, bh)
    if ep > 0:
        quad([P(S0, H, out), P(S1, H, out), P(S1, H, Dd), P(S0, H, Dd)], down, bh)
        quad([P(S0, H, 0.0), P(s0, H, 0.0), P(s0, H, out), P(S0, H, out)], down, bh)
        quad([P(s1, H, 0.0), P(S1, H, 0.0), P(S1, H, out), P(s1, H, out)], down, bh)

    # the balustrade round the deck's three open sides: posts at its corners and against the
    # wall, a rail over square balusters along the front and both ends
    B = pc["balustrade"]
    pm, bm, (rw, rd) = B["post_m"], B["baluster_m"], B["rail_m"]
    y2, y3 = y1, y1 + B["height_m"]
    yr = y3 - rd
    e = 0.04
    Ls, Rs, F = S0 + e, S1 - e, Dd - e

    def box(a0, a1, b0, b1, d0, d1, skip=()):
        f = {"front": ([P(a0, b0, d1), P(a1, b0, d1), P(a1, b1, d1), P(a0, b1, d1)], N, bf),
             "back": ([P(a0, b0, d0), P(a1, b0, d0), P(a1, b1, d0), P(a0, b1, d0)], _mul(N, -1), bf),
             "top": ([P(a0, b1, d0), P(a1, b1, d0), P(a1, b1, d1), P(a0, b1, d1)], up, bh),
             "bottom": ([P(a0, b0, d0), P(a1, b0, d0), P(a1, b0, d1), P(a0, b0, d1)], down, bh),
             "left": ([P(a0, b0, d0), P(a0, b0, d1), P(a0, b1, d1), P(a0, b1, d0)], _mul(R, -1), be),
             "right": ([P(a1, b0, d0), P(a1, b0, d1), P(a1, b1, d1), P(a1, b1, d0)], R, be)}
        for k, (pts, n, b) in f.items():
            if k not in skip:
                quad(pts, n, b)

    for a0, d0 in ((Ls, F - pm), (Rs - pm, F - pm), (Ls, 0.0), (Rs - pm, 0.0)):
        box(a0, a0 + pm, y2, y3, d0, d0 + pm, skip=("bottom",) + (("back",) if d0 == 0.0 else ()))
    fr = (F - pm / 2 - rw / 2, F - pm / 2 + rw / 2)
    box(Ls + pm, Rs - pm, yr, y3 - 0.02, *fr, skip=("left", "right"))
    mid = lambda x, y_: (x + y_) / 2
    for a0 in (Ls, Rs - pm):
        ac = (mid(a0, a0 + pm) - rw / 2, mid(a0, a0 + pm) + rw / 2)
        box(*ac, yr, y3 - 0.02, pm, F - pm, skip=("back", "front"))

    def balusters(lo, hi, along_s, fixed):
        n = max(1, math.floor((hi - lo) / B["pitch_m"]))
        step = (hi - lo) / (n + 1)
        for i in range(1, n + 1):
            m = lo + i * step
            if along_s:
                box(m - bm / 2, m + bm / 2, y2, yr, fixed - bm / 2, fixed + bm / 2, skip=("bottom", "top"))
            else:
                box(fixed - bm / 2, fixed + bm / 2, y2, yr, m - bm / 2, m + bm / 2, skip=("bottom", "top"))
        return n
    nb = balusters(Ls + pm, Rs - pm, True, mid(*fr))
    for a0 in (Ls, Rs - pm):
        nb += balusters(pm, F - pm, False, mid(a0, a0 + pm))
    a.seat((O, R, N), [(s, y, 0.0) for s in (S0, S1) for y in (0.0, y3)], "k01.porte_cochere")
    a.porte_cochere_meta = {"arches": len(pc["arches"]), "balusters": nb, "top_m": round(y3, 4)}


def _sub_(u, v):
    return (u[0] - v[0], u[1] - v[1], u[2] - v[2])
