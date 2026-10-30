"""T-3242: a two-level timber veranda against the main rear wall, as 1701 Prairie's stands in its
rear photograph.

TICKET T-3242 (piece 3 of T-1875). Glessner House Museum's photograph of the rear of the Hibbard
house shows, against the main block's rear wall south of the 1874 range, an open veranda of two
decks: the lower at the principal floor over the garden, the upper an open balcony over it, each
railed with a turned balustrade along its front and its ends; slender posts standing in pairs
along the front carry the upper deck, a band of spindles under it; and a flight of steps comes
down off the lower deck's front at its north end to the lawn. The record names it
`rear_veranda` and this module builds it on the K01 house:

  resolve()   the record checked against the house: on the main rear wall, clear of every rear
              wing standing on it, its decks over grade and under the eave, its posts' pairs
              fitting their stations, its flight on the front inside the lower deck's balustrade
  dress()     the decks, the paired posts from grade to the upper deck, the spindle frieze
              under it, a balustrade round both decks (open at the flight's head) and the flight
              itself, a stone stair between painted cheeks with a sloped rail to a newel at its foot

The decks' heights, the veranda's run along the wall and its reach, the stations' count and
the flight's place are read off the photograph through its solved camera
(data/reference_views/hibbard_house_1701_prairie/ghm_rear.json); the sections of the posts,
rails, balusters and spindles are this module's (docs/LIBERTIES.md L-k01-hibbard-1701-3242).
Every other K01 house carries no `rear_veranda`, so its bytes are unchanged.
"""

from __future__ import annotations

import math

KEYS = {"v_m", "out_m", "decks_m", "deck_m", "post_m", "pair_gap_m", "stations", "frieze_m",
        "balustrade", "steps"}
RAIL_KEYS = {"height_m", "rail_m", "baluster_m", "pitch_m"}
STEP_KEYS = {"v_m", "width_m", "tread_m", "riser_m"}
WALL = "k01.wall.rear_service"


class ParamError(ValueError):
    pass


def resolve(spec, *, width, eave, wings, floor) -> dict:
    """The record's `rear_veranda`, checked against the house (module doc)."""
    if not spec:
        return {}
    if not isinstance(spec, dict) or set(spec) != KEYS or not isinstance(spec["balustrade"], dict) \
            or set(spec["balustrade"]) != RAIL_KEYS or not isinstance(spec["steps"], dict) \
            or set(spec["steps"]) != STEP_KEYS:
        raise ParamError(f"rear_veranda takes {sorted(KEYS)}, its balustrade {sorted(RAIL_KEYS)}, "
                         f"its steps {sorted(STEP_KEYS)}")
    v0, v1 = (float(x) for x in spec["v_m"])
    out, dm, pm, gap = (float(spec[k]) for k in ("out_m", "deck_m", "post_m", "pair_gap_m"))
    d0, d1 = (float(x) for x in spec["decks_m"])
    n, fz = int(spec["stations"]), float(spec["frieze_m"])
    if not (0.0 <= v0 < v1 <= width):
        raise ParamError(f"rear_veranda.v_m {spec['v_m']}: a run along the main rear wall, inside its 0..{width}")
    for w in wings:
        a, b = w["rect"][2], w["rect"][3]
        if abs(w["rect"][1]) < 1e-9 and a < v1 + 0.3 and v0 - 0.3 < b:
            raise ParamError(f"rear_veranda (v {v0}-{v1}) is within 0.3 m of the wing {w['id']} (v {a}-{b}) "
                             f"standing on the rear wall")
    if not (1.2 <= out <= 4.0 and 0.1 <= dm <= 0.4 and 0.08 <= pm <= 0.3 and 0.05 <= gap <= 0.5
            and 2 <= n <= 12 and 0.15 <= fz <= 0.8):
        raise ParamError("rear_veranda: 1.2-4 m out from the wall, its decks 0.1-0.4 m thick on 0.08-0.3 m "
                         "posts paired 0.05-0.5 m apart at 2-12 stations, a 0.15-0.8 m frieze")
    if not (0.6 <= d0 <= floor + 0.3 and d0 + 2.5 <= d1 - dm - fz and d1 + 1.0 <= eave):
        raise ParamError(f"rear_veranda.decks_m {spec['decks_m']}: the lower 0.6 m over grade and no higher than "
                         f"0.3 m over the principal floor ({floor} m), 2.5 m of clear storey under the upper "
                         f"deck's frieze, the upper a metre under the eave ({eave} m)")
    pair = 2 * pm + gap
    pitch = (v1 - v0 - pair) / (n - 1)
    if pitch < pair + 0.6:
        raise ParamError(f"rear_veranda: {n} stations of paired posts do not fit {v1 - v0:.2f} m with 0.6 m between")
    B = {k: float(x) for k, x in spec["balustrade"].items()}
    if not (0.6 <= B["height_m"] <= 1.1 and 0.05 <= B["rail_m"] <= 0.2 and 0.03 <= B["baluster_m"] <= 0.12
            and B["baluster_m"] + 0.04 <= B["pitch_m"] <= 0.3):
        raise ParamError("rear_veranda.balustrade: 0.6-1.1 m high, a 0.05-0.2 m rail, 0.03-0.12 m balusters "
                         "at least 0.04 m apart and no more than 0.3 m on centres")
    S = {k: float(x) for k, x in spec["steps"].items()}
    risers = round(d0 / S["riser_m"])
    if not (0.9 <= S["width_m"] <= 2.5 and 0.25 <= S["tread_m"] <= 0.4 and 0.14 <= S["riser_m"] <= 0.21
            and risers >= 2):
        raise ParamError("rear_veranda.steps: a flight 0.9-2.5 m wide, 0.25-0.4 m treads, 0.14-0.21 m risers")
    if not (v0 + pair + 0.1 <= S["v_m"] - S["width_m"] / 2 and S["v_m"] + S["width_m"] / 2 <= v1 - pair - 0.1):
        raise ParamError(f"rear_veranda.steps at v {S['v_m']}: the flight stands on the front between the "
                         f"corner stations' posts")
    stations = [round(v0 + pair / 2 + i * pitch, 4) for i in range(n)]
    lo, hi = S["v_m"] - S["width_m"] / 2, S["v_m"] + S["width_m"] / 2
    for c in stations:
        if c + pair / 2 > lo - 0.02 and c - pair / 2 < hi + 0.02:
            raise ParamError(f"rear_veranda.steps (v {lo:.2f}-{hi:.2f}) run into the posts at station v {c}")
    return {"wall": WALL, "v_m": [v0, v1], "out_m": out, "decks_m": [d0, d1], "deck_m": dm, "post_m": pm,
            "pair_gap_m": gap, "stations_v_m": stations, "frieze_m": fz, "balustrade": B,
            "steps": {**S, "risers": risers, "riser_m": round(d0 / risers, 4)}}


def dress(a):
    """The veranda: decks, paired posts, frieze, balustrades and the garden flight."""
    from .k01_frontage import Y, _mul
    p, V = a.p, a.p.rear_veranda
    conf = p.worst_conf("footprint", "rear_veranda")
    mat, smat = "bay_strip_paint", "stoop_stone"
    pr, ps = a.prim(mat), a.prim(smat)
    (v0, v1), out = V["v_m"], V["out_m"]
    (d0, d1), dm, pm, gap = V["decks_m"], V["deck_m"], V["post_m"], V["pair_gap_m"]
    B, S, fz = V["balustrade"], V["steps"], V["frieze_m"]
    X0, X1 = -out, 0.0
    za, zb = -v1, -v0                                    # z = -v: the run's south and north ends
    seed = a.instance("k01.rear_veranda", "veranda",
                      {"v0_m": v0, "v1_m": v1, "out_m": out, "lower_deck_m": d0, "upper_deck_m": d1,
                       "stations": len(V["stations_v_m"])},
                      {"lower_deck": ((X0 + X1) / 2, d0, (za + zb) / 2), "upper_deck": ((X0 + X1) / 2, d1, (za + zb) / 2),
                       "steps_foot": (X0 - S["risers"] * S["tread_m"], 0.0, -S["v_m"])})
    X, Z = (1.0, 0.0, 0.0), (0.0, 0.0, 1.0)
    O = (0.0, 0.0, 0.0)
    bases = {m: (a.basis(m, O, X, Y, seed), a.basis(m, O, Z, Y, seed), a.basis(m, O, X, Z, seed))
             for m in (mat, smat)}
    up, down = Y, _mul(Y, -1)
    count = {"posts": 0, "balusters": 0, "spindles": 0}

    def box(x0, x1, y0, y1, z0, z1, skip=(), m=mat):
        if x1 - x0 < 1e-6 or y1 - y0 < 1e-6 or z1 - z0 < 1e-6:
            return
        bx, bz, bh = bases[m]
        prim = pr if m == mat else ps
        f = {"+x": ([(x1, y0, z0), (x1, y1, z0), (x1, y1, z1), (x1, y0, z1)], X, bz),
             "-x": ([(x0, y0, z0), (x0, y1, z0), (x0, y1, z1), (x0, y0, z1)], _mul(X, -1), bz),
             "+z": ([(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)], Z, bx),
             "-z": ([(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0)], _mul(Z, -1), bx),
             "top": ([(x0, y1, z0), (x1, y1, z0), (x1, y1, z1), (x0, y1, z1)], up, bh),
             "bottom": ([(x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1)], down, bh)}
        for k, (pts, nrm, b) in f.items():
            if k not in skip:
                prim.face(pts, nrm, b, conf)

    # the decks, each a slab from the wall out to the front, its back against the wall
    for d in (d0, d1):
        box(X0, X1, d - dm, d, za, zb, skip=("+x",))
    # the paired posts at every station, from grade to the upper deck's underside
    xp0, xp1 = X0 + 0.04, X0 + 0.04 + pm
    posts_z = []
    for c in V["stations_v_m"]:
        for zc in (-(c - gap / 2 - pm / 2), -(c + gap / 2 + pm / 2)):
            posts_z.append(zc)
            box(xp0, xp1, 0.0, d1 - dm, zc - pm / 2, zc + pm / 2, skip=("bottom", "top"))
            count["posts"] += 1

    def rail_run(axis, a0, a1, c, y0, h, rail, bal, pitch, kind):
        """A railed run between a0 and a1 along `axis` at cross position c: a foot rail, a top
        rail and balusters (or spindles) between, from y0 to y0 + h."""
        if a1 - a0 < 0.1:
            return
        W = (lambda s, y, w: (s, y, w)) if axis == "x" else (lambda s, y, w: (w, y, s))

        def b_(s0, s1, y_0, y_1, w0, w1, skip=()):
            (x0, _, z0), (x1, _, z1) = W(s0, 0.0, w0), W(s1, 0.0, w1)
            box(min(x0, x1), max(x0, x1), y_0, y_1, min(z0, z1), max(z0, z1), skip=skip)

        foot = min(0.08, rail)
        b_(a0, a1, y0 + 0.05, y0 + 0.05 + foot, c - rail / 2 + 0.01, c + rail / 2 - 0.01)
        b_(a0, a1, y0 + h - rail * 0.6, y0 + h, c - rail / 2, c + rail / 2)
        m = max(1, math.floor((a1 - a0) / pitch))
        step = (a1 - a0) / (m + 1)
        for i in range(1, m + 1):
            s = a0 + i * step
            b_(s - bal / 2, s + bal / 2, y0 + 0.05 + foot, y0 + h - rail * 0.6, c - bal / 2, c + bal / 2,
               skip=("top", "bottom"))
            count[kind] += 1

    xr = X0 + 0.04 + pm / 2                              # the front's rail line, on the posts
    zs = sorted(posts_z)                                 # most southerly (most negative z) first
    lo_z, hi_z = -(S["v_m"] + S["width_m"] / 2), -(S["v_m"] - S["width_m"] / 2)
    h, r, bal, pit = B["height_m"], B["rail_m"], B["baluster_m"], B["pitch_m"]
    # the front: between neighbouring posts (a pair's own gap is too narrow to rail), the lower
    # deck's opened at the flight's head
    for zl, zr in zip(zs, zs[1:]):
        g0, g1 = zl + pm / 2, zr - pm / 2
        if g1 - g0 <= gap + 1e-6:
            continue
        rail_run("z", g0, g1, xr, d1, h, r, bal, pit, "balusters")
        for q0, q1 in ((g0, min(g1, lo_z)), (max(g0, hi_z), g1)):
            rail_run("z", q0, q1, xr, d0, h, r, bal, pit, "balusters")
        # the frieze under the upper deck: a bottom rail and a row of spindles to the deck
        rail_run("z", g0, g1, xr, d1 - dm - fz - 0.05, fz, 0.07, 0.04, 0.11, "spindles")
    # the ends, wall to front post: balustrades on both decks, and the frieze under the upper
    for z_ in (za + pm / 2, zb - pm / 2):   # on the corner posts' centres
        for y0 in (d0, d1):
            rail_run("x", xp1, X1, z_, y0, h, r, bal, pit, "balusters")
        rail_run("x", xp1, X1, z_, d1 - dm - fz - 0.05, fz, 0.07, 0.04, 0.11, "spindles")
        box(X1 - 0.06, X1, d0, d1 + h, z_ - pm / 2, z_ + pm / 2, skip=("+x", "bottom"))   # the wall post
    # newels over the upper deck at the front posts' heads
    for zc in posts_z:
        box(xp0, xp1, d1, d1 + h + 0.06, zc - pm / 2, zc + pm / 2, skip=("bottom",))
    # the garden flight off the lower deck's front: a stone stair, each step a block down to
    # grade, between painted cheeks, a sloped rail on each to a newel at the foot
    nR, t, rr = S["risers"], S["tread_m"], S["riser_m"]
    for i in range(1, nR):
        box(X0 - i * t, X0 - (i - 1) * t, 0.0, d0 - i * rr, lo_z, hi_z,
            skip=("bottom",), m=smat)
    run = (nR - 1) * t
    ch = 0.07
    for zc in (lo_z - ch / 2, hi_z + ch / 2):
        z0, z1 = zc - ch / 2, zc + ch / 2
        # the cheek: a board from the deck's edge down the steps' nosings to grade
        prof = [(X0, d0 + 0.05), (X0 - run, rr + 0.05), (X0 - run - t, 0.0), (X0, 0.0)]
        for zz, nrm in ((z0, _mul(Z, -1)), (z1, Z)):
            q = [(x, y, zz) for x, y in prof]
            pr.face(q, nrm, bases[mat][0], conf)
        for (xa, ya), (xb, yb) in zip(prof, prof[1:] + prof[:1]):
            if ya < 1e-6 and yb < 1e-6:
                continue
            ex, ey = xb - xa, yb - ya
            ln = math.hypot(ex, ey)
            nrm = (ey / ln, -ex / ln, 0.0)
            if nrm[0] * ((xa + xb) / 2 - (X0 - run / 2)) + nrm[1] * ((ya + yb) / 2 - d0 / 3) < 0:
                nrm = (-nrm[0], -nrm[1], 0.0)
            pr.face([(xa, ya, z0), (xb, yb, z0), (xb, yb, z1), (xa, ya, z1)], nrm, bases[mat][0], conf)
        # the newel at the foot and the sloped rail from it up to the front post's head
        xn = X0 - run - t + 0.02
        box(xn, xn + pm, 0.0, h + 0.15, zc - pm / 2, zc + pm / 2, skip=("bottom",))
        ya, yb = d0 + h, h + 0.1
        xa, xb = X0, xn + pm
        sl = math.atan2(ya - yb, xa - xb)
        nu = (-math.sin(sl), math.cos(sl), 0.0)
        dr = r * 0.6
        pr.face([(xa, ya, z0), (xb, yb, z0), (xb, yb, z1), (xa, ya, z1)], nu, bases[mat][0], conf)
        pr.face([(xa, ya - dr, z0), (xb, yb - dr, z0), (xb, yb - dr, z1), (xa, ya - dr, z1)],
                _mul(nu, -1), bases[mat][0], conf)
        for zz, nrm in ((z0, _mul(Z, -1)), (z1, Z)):
            pr.face([(xa, ya - dr, zz), (xb, yb - dr, zz), (xb, yb, zz), (xa, ya, zz)], nrm, bases[mat][0], conf)
    a.rear_veranda_meta = {**count, "risers": nR, "top_m": round(d1 + h + 0.06, 4)}
