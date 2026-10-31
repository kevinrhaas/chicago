"""T-1881: a raised stone terrace against the main rear wall under a striped awning, as 1729
Prairie's stands at its south-east corner in J. W. Taylor's photographs nos. 16555 and 16554.

TICKET T-1881 (the owner, 2026-10-30, on Taylor's no. 16554: "the whole back of the pullman house
needs to be worked, stepped and there is a balcony"). Taylor's no. 16555, taken in summer from
across 18th Street, shows the house's rear wall at its 18th Street end with a terrace standing
out from it at the principal floor: a dressed-stone podium with an arched light in its south
face, a stone balustrade on pedestals round its open sides, and a striped awning pitched from
the wall over it on slender posts. The 1911 sheet draws the same place as a one-storey block
(the south-east 'B' block); no picture shows a storey there, and no. 16554, a winter view from
the south-east, shows the house's lower east windows standing clear over the balustrade. The
record names it `rear_terrace` and this module builds it on the K01 house:

  resolve()   the record checked against the house: on the main rear wall, inside its run and
              clear of every rear wing standing on it, its floor no higher than the principal
              floor, its awning pitched from under the eave down to over the balustrade
  dress()     the podium and its coping, the light in its south face, the balustrade's
              pedestals, rails and balusters round the open sides, the awning's posts, its
              striped canvas, and its valance along the eave and down both ends

The terrace's run, reach, floor and awning are read off no. 16555 through its solved camera
(data/reference_views/pullman_house_1729_prairie_conservatory/taylor_16555_west_front.json);
the sections of the coping, pedestals, rails and balusters, the awning's posts and the
stripes' colours (the photographs are monochrome) are this module's
(docs/LIBERTIES.md L-k01-1729-pullman-terrace-1881). Every other K01 house carries no
`rear_terrace`, so its bytes are unchanged.
"""

from __future__ import annotations

import math

KEYS = {"v_m", "out_m", "floor_m", "coping_m", "balustrade", "light", "awning"}
RAIL_KEYS = {"height_m", "pedestal_m", "rail_m", "baluster_m", "pitch_m"}
LIGHT_KEYS = {"width_m", "sill_m", "height_m"}
AWNING_KEYS = {"wall_m", "eave_m", "reach_m", "valance_m", "stripe_m", "posts", "post_m"}
WALL = "k01.wall.rear_service"
STONE, IRON = "bay_stone", "iron"
#: the canvas's two stripes: a light ground and a dark green stripe (reconstructed: the
#: photographs are monochrome; L-k01-1729-pullman-terrace-1881)
CANVAS = ("frieze_panel", "shutter")


class ParamError(ValueError):
    pass


def resolve(spec, *, width, eave, wings, floor) -> dict:
    """The record's `rear_terrace`, checked against the house (module doc)."""
    if not spec:
        return {}
    if not isinstance(spec, dict) or set(spec) != KEYS or not isinstance(spec["balustrade"], dict) \
            or set(spec["balustrade"]) != RAIL_KEYS or not isinstance(spec["light"], dict) \
            or set(spec["light"]) != LIGHT_KEYS or not isinstance(spec["awning"], dict) \
            or set(spec["awning"]) != AWNING_KEYS:
        raise ParamError(f"rear_terrace takes {sorted(KEYS)}, its balustrade {sorted(RAIL_KEYS)}, its light "
                         f"{sorted(LIGHT_KEYS)}, its awning {sorted(AWNING_KEYS)}")
    v0, v1 = (float(x) for x in spec["v_m"])
    out, fl, cp = float(spec["out_m"]), float(spec["floor_m"]), float(spec["coping_m"])
    if not (0.0 <= v0 < v1 <= width) or v1 - v0 < 2.0:
        raise ParamError(f"rear_terrace.v_m {spec['v_m']}: a run of at least 2 m along the main rear wall, "
                         f"inside its 0..{width}")
    for w in wings:
        a, b = w["rect"][2], w["rect"][3]
        if abs(w["rect"][1]) < 1e-9 and a < v1 + 0.3 and v0 - 0.3 < b:
            raise ParamError(f"rear_terrace (v {v0}-{v1}) is within 0.3 m of the wing {w['id']} (v {a}-{b}) "
                             f"standing on the rear wall")
    if not (1.2 <= out <= 5.0 and 0.6 <= fl <= floor + 0.3 and 0.08 <= cp <= 0.3):
        raise ParamError(f"rear_terrace: 1.2-5 m out from the wall, its floor 0.6 m over grade and no higher "
                         f"than 0.3 m over the principal floor ({floor} m), a 0.08-0.3 m coping")
    B = {k: float(x) for k, x in spec["balustrade"].items()}
    if not (0.6 <= B["height_m"] <= 1.2 and 0.25 <= B["pedestal_m"] <= 0.6 and 0.06 <= B["rail_m"] <= 0.25
            and 0.04 <= B["baluster_m"] <= 0.16 and B["baluster_m"] + 0.04 <= B["pitch_m"] <= 0.35
            and B["rail_m"] <= B["pedestal_m"]):
        raise ParamError("rear_terrace.balustrade: 0.6-1.2 m high on 0.25-0.6 m pedestals, a 0.06-0.25 m rail no "
                         "wider than a pedestal, 0.04-0.16 m balusters at least 0.04 m apart and no more than "
                         "0.35 m on centres")
    L = {k: float(x) for k, x in spec["light"].items()}
    if not (0.4 <= L["width_m"] <= out - 2 * B["pedestal_m"] and 0.1 <= L["sill_m"]
            and L["sill_m"] + L["height_m"] <= fl - cp - 0.1 and L["height_m"] >= L["width_m"] / 2):
        raise ParamError(f"rear_terrace.light: 0.4 m across and inside the south face's pedestals, 0.1 m over "
                         f"grade and 0.1 m under the coping at {fl - cp:.2f} m, tall enough for its round head")
    A = {k: float(x) for k, x in spec["awning"].items()}
    posts = int(spec["awning"]["posts"])
    top = fl + B["height_m"]
    if not (top + 0.6 <= A["eave_m"] < A["wall_m"] <= eave - 0.3 and 0.0 <= A["reach_m"] <= 0.6
            and 0.1 <= A["valance_m"] <= 0.5 and 0.15 <= A["stripe_m"] <= 0.6
            and 2 <= posts <= 8 and 0.03 <= A["post_m"] <= 0.12):
        raise ParamError(f"rear_terrace.awning: its eave at least 0.6 m over the balustrade's top ({top:.2f} m) "
                         f"and under its foot on the wall, which stands at least 0.3 m under the eave ({eave} m); "
                         f"0-0.6 m past the terrace's front, a 0.1-0.5 m valance, 0.15-0.6 m stripes, 2-8 posts "
                         f"0.03-0.12 m square")
    A["posts"] = posts
    return {"wall": WALL, "v_m": [v0, v1], "out_m": out, "floor_m": fl, "coping_m": cp,
            "balustrade": B, "light": L, "awning": A}


def dress(a):
    """The terrace: podium, coping, light, balustrade, awning posts, canvas and valance."""
    from .k01_frontage import Y, _mul
    p, T = a.p, a.p.rear_terrace
    conf = p.worst_conf("footprint", "rear_terrace")
    (v0, v1), out, fl, cp = T["v_m"], T["out_m"], T["floor_m"], T["coping_m"]
    B, L, A = T["balustrade"], T["light"], T["awning"]
    X0, X1 = -out, 0.0
    za, zb = -v1, -v0                                    # z = -v: the run's south and north ends
    top = fl + B["height_m"]
    seed = a.instance("k01.rear_terrace", "terrace",
                      {"v0_m": v0, "v1_m": v1, "out_m": out, "floor_m": fl, "awning_eave_m": A["eave_m"],
                       "awning_wall_m": A["wall_m"]},
                      {"floor": ((X0 + X1) / 2, fl, (za + zb) / 2),
                       "awning": ((X0 + X1) / 2, (A["eave_m"] + A["wall_m"]) / 2, (za + zb) / 2)})
    X, Z = (1.0, 0.0, 0.0), (0.0, 0.0, 1.0)
    O = (0.0, 0.0, 0.0)
    mats = (STONE, IRON) + CANVAS
    bases = {m: (a.basis(m, O, X, Y, seed), a.basis(m, O, Z, Y, seed), a.basis(m, O, X, Z, seed)) for m in mats}
    prims = {m: a.prim(m) for m in mats}
    up, down = Y, _mul(Y, -1)
    count = {"balusters": 0, "pedestals": 0, "posts": 0, "stripes": 0}

    def box(x0, x1, y0, y1, z0, z1, skip=(), m=STONE):
        if x1 - x0 < 1e-6 or y1 - y0 < 1e-6 or z1 - z0 < 1e-6:
            return
        bx, bz, bh = bases[m]
        f = {"+x": ([(x1, y0, z0), (x1, y1, z0), (x1, y1, z1), (x1, y0, z1)], X, bz),
             "-x": ([(x0, y0, z0), (x0, y1, z0), (x0, y1, z1), (x0, y0, z1)], _mul(X, -1), bz),
             "+z": ([(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)], Z, bx),
             "-z": ([(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0)], _mul(Z, -1), bx),
             "top": ([(x0, y1, z0), (x1, y1, z0), (x1, y1, z1), (x0, y1, z1)], up, bh),
             "bottom": ([(x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1)], down, bh)}
        for k, (pts, nrm, b) in f.items():
            if k not in skip:
                prims[m].face(pts, nrm, b, conf)

    # the podium: the south face carries its arched light, the east front and north end are
    # whole; its back stands against the wall
    ys = fl - cp
    box(X0, X1, 0.0, ys, za, zb, skip=("+x", "-z", "bottom"))
    xc, r = (X0 + X1) / 2, L["width_m"] / 2
    yl0, ysp = L["sill_m"], L["sill_m"] + L["height_m"] - r
    seg = 12
    bx = bases[STONE][0]
    S = lambda x, y: (x, y, za)
    south = prims[STONE]
    n_s = _mul(Z, -1)
    # the south face round the light: the piers either side, the apron under it and the
    # spandrel over its round head, in strips so the face stays one plane with a hole
    south.face([S(X0, 0.0), S(xc - r, 0.0), S(xc - r, ys), S(X0, ys)], n_s, bx, conf)
    south.face([S(xc + r, 0.0), S(X1, 0.0), S(X1, ys), S(xc + r, ys)], n_s, bx, conf)
    south.face([S(xc - r, 0.0), S(xc + r, 0.0), S(xc + r, yl0), S(xc - r, yl0)], n_s, bx, conf)
    for k in range(seg):
        t0, t1 = math.pi * k / seg, math.pi * (k + 1) / seg
        xa, ya = xc + r * math.cos(t0), ysp + r * math.sin(t0)
        xb, yb = xc + r * math.cos(t1), ysp + r * math.sin(t1)
        south.face([S(xa, ya), S(xa, ys), S(xb, ys), S(xb, yb)], n_s, bx, conf)
    # the light itself: dark glass sunk 0.12 m in the opening, its jambs and soffit turned
    sunk = 0.12
    dark = prims[IRON]
    G = lambda x, y: (x, y, za + sunk)
    pane = [G(xc - r, yl0), G(xc + r, yl0), G(xc + r, ysp)]
    pane += [G(xc + r * math.cos(math.pi * k / seg), ysp + r * math.sin(math.pi * k / seg)) for k in range(1, seg)]
    pane += [G(xc - r, ysp)]
    dark.face(pane, n_s, bases[IRON][0], conf)
    for x_, nx in ((xc - r, 1.0), (xc + r, -1.0)):
        south.face([(x_, yl0, za), (x_, ysp, za), (x_, ysp, za + sunk), (x_, yl0, za + sunk)],
                   (nx, 0.0, 0.0), bases[STONE][1], conf)
    south.face([(xc - r, yl0, za), (xc + r, yl0, za), (xc + r, yl0, za + sunk), (xc - r, yl0, za + sunk)],
               up, bases[STONE][2], conf)
    for k in range(seg):
        t0, t1 = math.pi * k / seg, math.pi * (k + 1) / seg
        tm = (t0 + t1) / 2
        xa, ya = xc + r * math.cos(t0), ysp + r * math.sin(t0)
        xb, yb = xc + r * math.cos(t1), ysp + r * math.sin(t1)
        south.face([(xa, ya, za), (xb, yb, za), (xb, yb, za + sunk), (xa, ya, za + sunk)],
                   (-math.cos(tm), -math.sin(tm), 0.0), bases[STONE][2], conf)
    # the coping, 0.05 m proud on the open sides, its top the terrace's floor
    e = 0.05
    box(X0 - e, X1, ys, fl, za - e, zb + e, skip=("+x",))

    # the balustrade: pedestals at the corners and along the front, between them a plinth,
    # square balusters and a top rail, on the coping's centreline inset by half a pedestal
    pm, rm, bm, pit = B["pedestal_m"], B["rail_m"], B["baluster_m"], B["pitch_m"]
    h = B["height_m"]
    xf = X0 + pm / 2                                     # the front's line
    zs, zn = za + pm / 2, zb - pm / 2                    # the ends' lines
    run = zn - zs
    n_mid = max(0, math.ceil(run / 3.0) - 1)             # pedestals no more than 3 m apart
    front_ped = [zs + run * i / (n_mid + 1) for i in range(n_mid + 2)]
    peds = [(xf, z_) for z_ in front_ped] + [(X1 - pm / 2, zs), (X1 - pm / 2, zn)]
    for x_, z_ in peds:
        box(x_ - pm / 2, x_ + pm / 2, fl, top + 0.06, z_ - pm / 2, z_ + pm / 2, skip=("bottom",))
        box(x_ - pm / 2 - 0.03, x_ + pm / 2 + 0.03, top + 0.06, top + 0.12, z_ - pm / 2 - 0.03, z_ + pm / 2 + 0.03)
        count["pedestals"] += 1

    def rail_run(along_x, a0, a1, c):
        if a1 - a0 < 0.2:
            return
        def b_(s0, s1, y0, y1, w, skip=()):
            if along_x:
                box(s0, s1, y0, y1, c - w / 2, c + w / 2, skip=skip)
            else:
                box(c - w / 2, c + w / 2, y0, y1, s0, s1, skip=skip)
        plinth, rail = 0.12, 0.1
        b_(a0, a1, fl, fl + plinth, rm, skip=("bottom",))
        b_(a0, a1, top - rail, top, rm)
        m = max(1, math.floor((a1 - a0) / pit))
        step = (a1 - a0) / (m + 1)
        for i in range(1, m + 1):
            s = a0 + i * step
            b_(s - bm / 2, s + bm / 2, fl + plinth, top - rail, bm, skip=("top", "bottom"))
            count["balusters"] += 1

    for za_, zb_ in zip(front_ped, front_ped[1:]):        # the front, pedestal to pedestal
        rail_run(False, za_ + pm / 2, zb_ - pm / 2, xf)
    for z_ in (zs, zn):                                   # the ends, front pedestal to the wall's
        rail_run(True, xf + pm / 2, X1 - pm, z_)

    # the awning: iron posts on the front's pedestals up to its eave, the canvas pitched from
    # the wall to the eave in stripes running down the pitch, and its valance hung along the
    # eave and down both ends
    ye, yw, rc = A["eave_m"], A["wall_m"], A["reach_m"]
    pq = A["post_m"]
    xe = X0 - rc
    za_a, zb_a = za - rc, zb
    nP = A["posts"]
    for i in range(nP):
        z_ = zs + run * i / (nP - 1)
        box(xf - pq / 2, xf + pq / 2, top + 0.12, ye, z_ - pq / 2, z_ + pq / 2, skip=("bottom",), m=IRON)
        count["posts"] += 1
    box(xe, xe + 0.05, ye - 0.05, ye, za_a, zb_a, m=IRON)  # the eave's rail on the posts' heads
    slope = (yw - ye) / (X1 - xe)
    ln = math.hypot(X1 - xe, yw - ye)
    nu = (-(yw - ye) / ln, (X1 - xe) / ln, 0.0)            # the canvas's upper normal
    nd = _mul(nu, -1)
    width_z = zb_a - za_a
    ns = max(1, round(width_z / A["stripe_m"]))
    for k in range(ns):
        z0, z1 = za_a + width_z * k / ns, za_a + width_z * (k + 1) / ns
        m = CANVAS[k % 2]
        pts = [(xe, ye, z0), (X1, yw, z0), (X1, yw, z1), (xe, ye, z1)]
        prims[m].face(pts, nu, bases[m][2], conf)
        prims[m].face(list(reversed(pts)), nd, bases[m][2], conf)
        # the valance along the eave, in the same stripe
        vq = [(xe, ye - A["valance_m"], z0), (xe, ye - A["valance_m"], z1), (xe, ye, z1), (xe, ye, z0)]
        prims[m].face(vq, _mul(X, -1), bases[m][1], conf)
        prims[m].face(list(reversed(vq)), X, bases[m][1], conf)
        count["stripes"] += 1
    # the ends' valances, hung under the pitch from the eave to the wall, striped across
    nv = max(1, round((X1 - xe) / A["stripe_m"]))
    for z_, nz in ((za_a, _mul(Z, -1)), (zb_a, Z)):
        for k in range(nv):
            x0, x1 = xe + (X1 - xe) * k / nv, xe + (X1 - xe) * (k + 1) / nv
            y0, y1 = ye + slope * (x0 - xe), ye + slope * (x1 - xe)
            m = CANVAS[k % 2]
            q = [(x0, y0 - A["valance_m"], z_), (x1, y1 - A["valance_m"], z_), (x1, y1, z_), (x0, y0, z_)]
            prims[m].face(q, nz, bases[m][0], conf)
            prims[m].face(list(reversed(q)), _mul(nz, -1), bases[m][0], conf)
    a.rear_terrace_meta = {**count, "top_m": round(top, 4), "awning_m": [round(ye, 4), round(yw, 4)]}
