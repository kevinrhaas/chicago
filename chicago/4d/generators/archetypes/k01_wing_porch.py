"""T-3626: an open, roofed porch on a flat rear wing's deck, as 2013 Prairie's rear block carries
its top floor in the 2003 nomination photographs.

TICKET T-3626 (piece 2 of T-1916). The nomination says of the Reid house's rear section that
"the top floor of the rear section is open to provide a terrace", and two of its photographs show
it: the north side's (p. 36) the rear block's brick wall stopping at about 10.9 m with an open
storey over it under a flat roof to about 14 m, a post between its two openings; the rear's
(p. 38, from the south-east) the same storey from behind, slender dark posts at the corners and
between them, an iron railing along the rear on the wall's top, and the roof's fascia over all.
K01's wings stopped at their tin deck, so the record names it a flat wing's `roof_porch` and
this module builds it:

  resolve()   the record checked against the wing: a flat deck, the porch's posts inside the
              walls' runs, its roof clear over the railing and no higher than the deck of the
              wing (or main eave) it stands against, so the host wall stands behind its end
  dress()     a post at each of the deck's two outer (rear) corners and at the stations listed per
              side, from the deck to the roof; a railing (foot rail, top rail, balusters)
              between the posts along each railed side; and the roof, a slab on the posts run
              out by its overhang, painted tin on top, a painted soffit under and a fascia round
              its three open edges, its front end against the host wall

The porch's storey and its posts' places are read off the two photographs through the north
side's solved camera (data/reference_views/reid_house_2013_prairie/nrhp_2003_north_side.json);
the sections of the posts, rails and balusters and the roof's slab are this module's
(docs/LIBERTIES.md L-k01-2013-reid-porch-3626). Every other K01 wing carries no `roof_porch`,
so its bytes are unchanged.

K01's side names hold here: a wing's `south` wall is its v0 side, `north` its v1 side and
`rear` its u0 end; the assembly's frame is x = u, z = -v.
"""

from __future__ import annotations

import math

KEYS = {"storey_m", "post_m", "posts", "roof", "railing"}
ROOF_KEYS = {"slab_m", "overhang_m"}
RAIL_KEYS = {"sides", "height_m", "rail_m", "baluster_m", "pitch_m"}
SIDES = ("south", "north", "rear")
POST, RAIL = "iron", "iron"
TIN, FASCIA = "k04_painted_tin_sheet", "fascia"


class ParamError(ValueError):
    pass


def resolve(wid, spec, *, rect, deck, roof_kind, host_top) -> dict:
    """A wing's `roof_porch`, checked against the wing (module doc). `deck` is the wing's deck
    level, the porch's floor; `host_top` the top of whatever its front stands against (the
    host wing's deck, or the main eave)."""
    if spec is None:
        return {}
    if not isinstance(spec, dict) or set(spec) != KEYS or not isinstance(spec["roof"], dict) \
            or set(spec["roof"]) != ROOF_KEYS or not isinstance(spec["railing"], dict) \
            or set(spec["railing"]) != RAIL_KEYS or not isinstance(spec["posts"], dict) \
            or not set(spec["posts"]) <= set(SIDES):
        raise ParamError(f"rear_wings: {wid}'s roof_porch takes {sorted(KEYS)}, its roof {sorted(ROOF_KEYS)}, "
                         f"its railing {sorted(RAIL_KEYS)}, its posts by side ({', '.join(SIDES)})")
    if roof_kind != "flat":
        raise ParamError(f"rear_wings: {wid}'s roof_porch stands on a flat deck, not a {roof_kind} roof")
    u0, u1, v0, v1 = rect
    st, pm = float(spec["storey_m"]), float(spec["post_m"])
    slab, ov = float(spec["roof"]["slab_m"]), float(spec["roof"]["overhang_m"])
    R = {k: (list(x) if k == "sides" else float(x)) for k, x in spec["railing"].items()}
    if not (2.0 <= st <= 4.0 and 0.06 <= pm <= 0.3 and 0.1 <= slab <= 0.5 and 0.0 <= ov <= 0.6):
        raise ParamError(f"rear_wings: {wid}'s roof_porch: a 2-4 m storey on 0.06-0.3 m posts under a "
                         f"0.1-0.5 m roof overhanging 0-0.6 m")
    if not (set(R["sides"]) <= set(SIDES) and len(set(R["sides"])) == len(R["sides"])
            and 0.6 <= R["height_m"] <= 1.2 and 0.03 <= R["rail_m"] <= 0.15
            and 0.015 <= R["baluster_m"] <= 0.06 and R["baluster_m"] + 0.04 <= R["pitch_m"] <= 0.3):
        raise ParamError(f"rear_wings: {wid}'s roof_porch.railing: sides among {SIDES}, 0.6-1.2 m high, a "
                         f"0.03-0.15 m rail, 0.015-0.06 m balusters at least 0.04 m apart and no more than "
                         f"0.3 m on centres")
    if R["height_m"] + 0.6 > st:
        raise ParamError(f"rear_wings: {wid}'s roof_porch railing stands within 0.6 m of its roof")
    top = deck + st + slab
    if top > host_top + 1e-6:
        raise ParamError(f"rear_wings: {wid}'s roof_porch roof tops out at {top:.2f} m, over the "
                         f"{host_top:.2f} m of the wall it stands against")
    posts = {}
    for side in SIDES:
        a0, a1 = (u0, u1) if side != "rear" else (v0, v1)
        xs = sorted(float(x) for x in spec["posts"].get(side, ()))
        for x in xs:
            if not (a0 + pm + 0.6 <= x <= a1 - pm - 0.6):
                raise ParamError(f"rear_wings: {wid}'s roof_porch post at {x} on its {side} side stands "
                                 f"within 0.6 m of a corner post ({a0}..{a1})")
        for p_, q_ in zip(xs, xs[1:]):
            if q_ - p_ < pm + 0.6:
                raise ParamError(f"rear_wings: {wid}'s roof_porch posts at {p_} and {q_} stand under "
                                 f"0.6 m apart")
        posts[side] = tuple(round(x, 4) for x in xs)
    return {"storey_m": st, "post_m": pm, "posts": posts, "slab_m": slab, "overhang_m": ov,
            "railing": {**R, "sides": tuple(R["sides"])},
            "floor_m": round(deck, 4), "roof_m": round(deck + st, 4), "top_m": round(top, 4)}


def dress(a, w):
    """The porch on wing `w`'s deck: posts, railings and its roof (module doc)."""
    from .k01_frontage import Y, _mul
    P = w["roof_porch"]
    conf = a.p.worst_conf("rear_wings", "footprint")
    u0, u1, v0, v1 = w["rect"]
    hv0, hv1 = w["host_v_m"]
    pm, yd, yr, yt = P["post_m"], P["floor_m"], P["roof_m"], P["top_m"]
    ov, Rl = P["overhang_m"], P["railing"]
    seed = a.instance(f"k01.roof_porch.wing.{w['id']}", "porch",
                      {"storey_m": P["storey_m"], "post_m": pm, "roof_m": yr, "top_m": yt,
                       "posts": len(P["posts"]["south"]) + len(P["posts"]["north"]) + len(P["posts"]["rear"]) + 2,
                       "railed": ",".join(Rl["sides"])},
                      {"floor": ((u0 + u1) / 2, yd, -(v0 + v1) / 2), "roof": ((u0 + u1) / 2, yt, -(v0 + v1) / 2)})
    X, Z, O = (1.0, 0.0, 0.0), (0.0, 0.0, 1.0), (0.0, 0.0, 0.0)
    count = {"posts": 0, "balusters": 0}

    def box(m, x0, x1, y0, y1, z0, z1, skip=()):
        if x1 - x0 < 1e-6 or y1 - y0 < 1e-6 or z1 - z0 < 1e-6:
            return
        bx, bz, bh = (a.basis(m, O, X, Y, seed), a.basis(m, O, Z, Y, seed), a.basis(m, O, X, Z, seed))
        f = {"+x": ([(x1, y0, z0), (x1, y1, z0), (x1, y1, z1), (x1, y0, z1)], X, bz),
             "-x": ([(x0, y0, z0), (x0, y1, z0), (x0, y1, z1), (x0, y0, z1)], _mul(X, -1), bz),
             "+z": ([(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)], Z, bx),
             "-z": ([(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0)], _mul(Z, -1), bx),
             "top": ([(x0, y1, z0), (x1, y1, z0), (x1, y1, z1), (x0, y1, z1)], Y, bh),
             "bottom": ([(x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1)], _mul(Y, -1), bh)}
        for k, (pts, nrm, b) in f.items():
            if k not in skip:
                a.prim(m).face(pts, nrm, b, conf)

    # the posts, their outer faces on the walls' faces: the two rear corners, and the
    # stations each side lists (u along south and north, v along the rear); at the host wall
    # the railing dies into the wall, so no post stands there
    za, zb = -v1, -v0                     # z of the north (v1) and south (v0) walls
    stations = {"south": [(u0, zb)] + [(x, zb) for x in P["posts"]["south"]],
                "north": [(u0, za)] + [(x, za) for x in P["posts"]["north"]],
                "rear": [(u0, za), (u0, zb)] + [(u0, -x) for x in P["posts"]["rear"]]}
    placed = set()
    for side, pts in stations.items():
        for x, z in pts:
            cx = min(max(x, u0 + pm / 2), u1 - pm / 2)
            cz = min(max(z, za + pm / 2), zb - pm / 2)
            key = (round(cx, 4), round(cz, 4))
            if key in placed:
                continue
            placed.add(key)
            box(POST, cx - pm / 2, cx + pm / 2, yd, yr, cz - pm / 2, cz + pm / 2, skip=("bottom", "top"))
            count["posts"] += 1

    def rail_run(axis, a0, a1, c):
        """A railing between a0 and a1 along `axis` (x or z) on the line c: a foot rail, a top
        rail and balusters between them, from the deck up its height."""
        if a1 - a0 < 0.1:
            return
        h, r, bal, pitch = Rl["height_m"], Rl["rail_m"], Rl["baluster_m"], Rl["pitch_m"]

        def b_(s0, s1, y0, y1, w0, w1, skip=()):
            if axis == "x":
                box(RAIL, s0, s1, y0, y1, w0, w1, skip=skip)
            else:
                box(RAIL, w0, w1, y0, y1, s0, s1, skip=skip)

        foot = 0.06
        b_(a0, a1, yd + 0.05, yd + 0.05 + foot, c - r / 2 + 0.005, c + r / 2 - 0.005)
        b_(a0, a1, yd + h - r * 0.6, yd + h, c - r / 2, c + r / 2)
        m = max(1, math.floor((a1 - a0) / pitch))
        step = (a1 - a0) / (m + 1)
        for i in range(1, m + 1):
            s = a0 + i * step
            b_(s - bal / 2, s + bal / 2, yd + 0.05 + foot, yd + h - r * 0.6, c - bal / 2, c + bal / 2,
               skip=("top", "bottom"))
            count["balusters"] += 1

    for side in Rl["sides"]:
        if side == "rear":
            zs = sorted({cz for (cx, cz) in placed if abs(cx - (u0 + pm / 2)) < 1e-6})
            for zl, zr in zip(zs, zs[1:]):
                rail_run("z", zl + pm / 2, zr - pm / 2, u0 + pm / 2)
        else:
            cz = (zb - pm / 2) if side == "south" else (za + pm / 2)
            xs = sorted({cx for (cx, z_) in placed if abs(z_ - cz) < 1e-6}) + [u1]
            for xl, xr in zip(xs, xs[1:]):
                rail_run("x", xl + pm / 2, xr - (pm / 2 if xr < u1 else 0.0), cz)

    # the roof: a slab on the posts, run out by its overhang over the three open sides, tin on
    # top, a painted soffit under and a fascia round the open edges; at the front it dies into
    # the host wall, closed only where it runs past that wall's ends
    a0_, a1_, b0, b1 = u0 - ov, u1, v0 - ov, v1 + ov
    Xp = lambda u, y, v: (u, y, -v)
    E, NZ = X, (0.0, 0.0, -1.0)
    a.prim(TIN).face([Xp(a0_, yt, b0), Xp(a1_, yt, b0), Xp(a1_, yt, b1), Xp(a0_, yt, b1)], Y,
                     a.basis(TIN, Xp(a0_, yt, b0), E, NZ, seed), conf)
    a.prim(FASCIA).face([Xp(a0_, yr, b0), Xp(a1_, yr, b0), Xp(a1_, yr, b1), Xp(a0_, yr, b1)], (0.0, -1.0, 0.0),
                        a.basis(FASCIA, Xp(a0_, yr, b0), E, NZ, seed), conf)
    edge = lambda O_, R_: a.basis(FASCIA, O_, R_, Y, seed)
    a.prim(FASCIA).face([Xp(a0_, yr, b0), Xp(a1_, yr, b0), Xp(a1_, yt, b0), Xp(a0_, yt, b0)], (0.0, 0.0, 1.0),
                        edge(Xp(a0_, yr, b0), E), conf)
    a.prim(FASCIA).face([Xp(a0_, yr, b1), Xp(a1_, yr, b1), Xp(a1_, yt, b1), Xp(a0_, yt, b1)], NZ,
                        edge(Xp(a1_, yr, b1), (-1.0, 0.0, 0.0)), conf)
    a.prim(FASCIA).face([Xp(a0_, yr, b0), Xp(a0_, yr, b1), Xp(a0_, yt, b1), Xp(a0_, yt, b0)], (-1.0, 0.0, 0.0),
                        edge(Xp(a0_, yr, b1), (0.0, 0.0, 1.0)), conf)
    for c0, c1 in ((b0, min(hv0, b1)), (max(hv1, b0), b1)):
        if c1 - c0 > 1e-6:
            a.prim(FASCIA).face([Xp(a1_, yr, c0), Xp(a1_, yr, c1), Xp(a1_, yt, c1), Xp(a1_, yt, c0)], E,
                                edge(Xp(a1_, yr, c1), (0.0, 0.0, 1.0)), conf)
    a.wing_porch_meta = {**getattr(a, "wing_porch_meta", {}),
                         w["id"]: {**count, "floor_m": yd, "roof_m": yr, "top_m": yt}}
