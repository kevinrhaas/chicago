"""K14 condition kit laid on a K01 frontage's yard: lawn, front walk, side service walk (T-2360).

TICKET T-2360: piece 3 of T-2325 (package K14 of the T-1837 Prairie programme). T-2324 built
the condition kit (`k14_condition.py` from `data/components/prairie_1904/k14_condition.json`),
whose ground layers return WEIGHTS and leave how a yard shows them to the yard. This module
is that yard: it lays the ground inside the record's K11 boundary as surfaces of its own,
and reads both ground layers off the kit at the house's own age on the kit's target date.

What the record's `yard` names, and what is built for it:

  lawn          turf over the front yard, from the house's street front (and the foot of
                any bay standing on it) out to the fence curb's house face, between the
                house's south wall line and the north lot line. Piers, the curb, splash
                stones and the bay stand on it; nothing is cut round them.
  grass edge    the kit's `grass_edge`: a bare strip at the street front's wall foot, its
                width the kit's at this age and its line wobbling by the property's seed.
                Measured square to the wall, so it stays one width round a bay's curve.
  under stoop   the stoop is an open stair (only its foot touches grade), so the ground
                under it is shown, as bare earth: no lawn is kept in its shade.
  front walk    stone flags from the stoop's foot through the entrance gate to the public
                walk, in the stoop's own stone (one slot, no new draw), each flag a slab
                with its joints open, worn along the walk's centre (`path_wear`
                front_walk).
  service walk  cinder from the side gate back down the side passage, between the boundary
                wall and the house's south wall, to the record's `to_u_m`; worn in a
                beaten line along its centre (`path_wear` service_walk).

A layer's weight w becomes a `_TONE` on the walk's vertices, 1 - (1 - wear_tone) w, so a
worn line darkens the surface it is on and keeps its hue; the earth strip is a surface
because bare earth beside turf is a change of material, which a grey multiplier cannot
draw. Every surface is reconstructed: no source read here shows 1808's yard.

Behind a stone coping wall (T-3206: `layout: stone_coping_wall`, which has no gates) the yard is
laid by `dress_open`: the lawn across the whole front of the lot, and a front walk `width_m`
wide from the stoop's foot (a side stoop's: the end of its flight, where the foot opens) out
through the wall's opening to the public walk. Where no opening stands square to the stoop
(1834's, at the lot's north end in its photograph) the walk turns: out from the stoop, along
the wall's back clear of it, and out through the opening, each leg its own flags. A service walk
is optional there, and runs down the side passage the record names (`side`) through an opening
across its mouth. Every leg is written into the front walk's instance (`legs_m`), which
`tools/check_house_walks.py` reads off the GLB.

T-3215: `dress_open` also lays the yard of a front with no boundary (`layout: open`: 1621's and
1623's 1886 drawings, 1625's 1890 photograph), whose one opening is the lot's whole front and
whose lawn runs out to the public walk, and of a front garden (`layout: front_garden`, 1637's
engraving), whose walk comes out from the stoop's foot through the gap the stoop's flight leaves
between the garden's wall and its fence. And a boarded street line that closes its side yard's
mouth unbroken (1616's, `k11.fence.side_boards` with no side gate) lays no service walk: there is
no gate for one to come through.
"""

from __future__ import annotations

import math

from . import k11_frontage

# The ground surfaces stand this far over grade. Not Glessner's courtyard lift (0.015 m): the
# renderer beds a building on the LOWEST terrain under its bounds (buildings.js groundUnder),
# and across 1808's yard the drawn terrain rises up to 0.018 m above that bed (measured in
# the published /1904/ app, T-2360), so a 0.015 m lawn sank under it along the passage.
LAWN_Y = 0.035
STEP_S = 0.1        # lawn columns along the street front: the strip's 0.6 m wobble in six
ROW_U = 0.2         # walk rows along their length: path wear breaks up on a 0.8 m wavelength
FLAG_SINK = 0.05    # a flag's bed below grade, so its edge never shows a gap over the terrain
JOINT_M = 0.01      # a walk stands this far clear of the pier faces it passes between
MAX_SLOPE_GROW = 3.0  # a strip measured square to a steep curve is at most this many times wider in u
SURFACES = {"turf": "yard_turf", "earth": "yard_earth", "cinder": "yard_cinder",
            "stone_flags": "stoop_stone"}
UP = (0.0, 1.0, 0.0)
LAWN, FRONT_WALK, SERVICE_WALK = "k14.yard.lawn", "k14.yard.front_walk", "k14.yard.service_walk"
# the boundary layouts whose yard `dress_open` lays: a coping wall (T-3206), an open front and a
# front garden (T-3215), each handing K14 its back face (`inner_x_m`) and its openings
OPEN_LAYOUTS = (k11_frontage.COPING, k11_frontage.OPEN, k11_frontage.GARDEN)


def spec(params) -> dict | None:
    """The record's `yard`, checked against what this module can build."""
    y = getattr(params, "yard", None)
    if not y:
        return None
    if not getattr(params, "boundary", None):
        raise ValueError("a yard is laid inside a K11 boundary, and this record names none")
    if params.boundary.get("layout") in OPEN_LAYOUTS:
        return open_spec(params, y)
    # T-3215: a boarded street line unbroken across the side yard's mouth (1616's) has no side
    # gate, and its yard no service walk. T-3216: nor has an iron front with no passage to gate
    unbroken = params.boundary.get("fence") == k11_frontage.BOARDS or (
        k11_frontage._side_passage_m(params.boundary) < k11_frontage._gate_clear_min())
    if not params.boundary.get("side_gate") and params.boundary.get("layout") != "stone_posts_rails" \
            and not (unbroken and "service_walk" not in y):
        raise ValueError("a yard's service walk runs through the K11 side gate, and this boundary names none")
    if y.get("lawn") != "turf":
        raise ValueError("yard.lawn builds 'turf' alone")
    if y.get("grass_edge") != "street_front":
        raise ValueError("yard.grass_edge runs along 'street_front' alone")
    fw, sw = y.get("front_walk") or {}, y.get("service_walk")
    if fw.get("surface") != "stone_flags" or (sw is not None and sw.get("surface") != "cinder"):
        raise ValueError("yard builds a stone_flags front walk and a cinder service walk")
    for name, w in (("front_walk", fw), ("service_walk", sw or {"wear_tone": 1.0})):
        if not 0.62 <= float(w["wear_tone"]) <= 1.0:
            raise ValueError(f"yard.{name}.wear_tone {w['wear_tone']} is under the kit's floor (0.62)")
    if not 0.3 <= float(fw["flag_m"]) <= 1.8:
        raise ValueError("yard.front_walk.flag_m is a flag's length, 0.3 to 1.8 m")
    if not LAWN_Y < float(fw["top_m"]) <= 0.1:
        raise ValueError("yard.front_walk.top_m stands a flag over the lawn, and no more than 0.1 m")
    return y


def _cond():
    # imported late: the kit reads numpy, and a record with no yard never needs it
    from . import k14_condition
    return k14_condition


def _up_grid(a, mat, rows, conf):
    """Lay a grid of (x, y, z, tone) points — rows along one axis, the same count of columns
    in every row — as up-facing quads; a zero-area quad is skipped."""
    pr = a.prim(mat)
    fab = a.fabric[mat]
    tu, tv = a.tiles[fab] if fab else (1.0, 1.0)
    tris = 0
    for r0, r1 in zip(rows, rows[1:]):
        for c in range(len(r0) - 1):
            quad = (r0[c], r0[c + 1], r1[c + 1], r1[c])
            for t in ((quad[0], quad[1], quad[2]), (quad[0], quad[2], quad[3])):
                (ax, _, az), (bx, _, bz), (cx, _, cz) = (q[:3] for q in t)
                ny = (bz - az) * (cx - ax) - (bx - ax) * (cz - az)
                if abs(ny) < 1e-9:
                    continue
                if ny < 0:
                    t = (t[0], t[2], t[1])
                base = len(pr.pos)
                for x, y, z, k in t:
                    pr.pos.append((x, y, z))
                    pr.nrm.append(UP)
                    pr.uv.append((x / tu, z / tv))
                    pr.conf.append(conf)
                    pr.tone.append(round(k, 5))
                pr.idx += [base, base + 1, base + 2]
                tris += 1
    return tris


def _bay_feet(a, D, s_lo, s_hi):
    """The outer foot of every bay standing on the street front, as [(s, u), ...] spans."""
    pts = {}
    for name, pr in a.prims.items():
        if not name.startswith("bay_"):
            continue
        for x, y, z in pr.pos:
            s = -z
            if y < 0.005 and x >= D - 1e-6 and s_lo < s < s_hi:
                k = round(s, 4)
                pts[k] = max(pts.get(k, D), x)
    spans, cur = [], []
    for s in sorted(pts):
        if cur and s - cur[-1][0] > 0.5:
            spans.append(cur)
            cur = []
        cur.append((s, pts[s]))
    if cur:
        spans.append(cur)
    return [sp for sp in spans if len(sp) > 1 and max(u for _, u in sp) > D + 0.05]


YARD_MATS = ("yard_turf", "yard_earth", "yard_cinder", "stoop_stone")


def _grade_spec(y: dict) -> dict | None:
    """`yard.grade_m` (T-3206): how far the ground the app lays rises over the house's own
    base under its front yard, measured in the published app (tools/qa_house_walks_t3206.mjs).
    The app stands a house on the LOWEST ground under its walls (building-feet.js), so where
    the lot rises toward the street a yard laid at the base's grade is under the ground: at
    1834 Prairie the ground is 67-88 mm over the base and the 60 mm flags never showed.
    `front` is the rise at the street front on the stoop's axis, `street` at the public
    walk's inner edge, `per_m_s` how it changes per metre along s; between the front and
    the rear (u 0) it falls linearly to nothing, where the walls' feet are."""
    g = y.get("grade_m")
    if g is None:
        return None
    if set(g) - {"front", "street", "per_m_s", "note"}:
        raise ValueError(f"yard.grade_m takes front, street, per_m_s and a note; {sorted(g)}")
    for k in ("front", "street"):
        if not 0.0 <= float(g[k]) <= 0.3:
            raise ValueError(f"yard.grade_m.{k} {g[k]} is a rise over the house's base, 0-0.3 m")
    if not abs(float(g.get("per_m_s", 0.0))) <= 0.02:
        raise ValueError("yard.grade_m.per_m_s is a cross-fall, no more than 0.02 m a metre")
    return g


def _lift(a, g, marks, axis, public):
    """Raise every vertex the yard laid by the ground's rise under it (`_grade_spec`)."""
    D = a.p.depth_m
    f, s_, k = float(g["front"]), float(g["street"]), float(g.get("per_m_s", 0.0))
    for m, n0 in marks.items():
        pr = a.prims.get(m)
        if pr is None:
            continue
        for i in range(n0, len(pr.pos)):
            x, yy, z = pr.pos[i]
            s = -z
            if x <= D:
                w = max(0.0, x / D)
                rise = w * (f + k * (s - axis))
            else:
                t = min(1.0, (x - D) / max(1e-6, public - D))
                rise = f + (s_ - f) * t + k * (s - axis)
            pr.pos[i] = (x, round(yy + max(0.0, rise), 5), z)


def dress(a):
    """Lay the record's yard on the assembly: the lawn and its bare strip, the earth under
    the stoop, the front walk's flags and the service walk's cinder; then lift it onto the
    ground the app lays, where the record measures that (`yard.grade_m`)."""
    p = a.p
    y = spec(p)
    if not y:
        return
    g = _grade_spec(y)
    if g is None:
        return _dress(a, y)
    marks = {m: len(a.prims[m].pos) if m in a.prims else 0 for m in YARD_MATS}
    out = _dress(a, y)
    door = next(o for o in p.openings if o.component == "k01.opening.door_leaf" and o.wall == k11_frontage.STREET_FRONT)
    _lift(a, g, marks, p.stoop_s_m(door.s_m), p.depth_m + p.entrance_kit["front_yard_m"])
    return out


def _dress(a, y):
    p = a.p
    if not getattr(a, "boundary", None):
        raise ValueError("the yard is laid after the K11 boundary, and none was built")
    if p.boundary.get("layout") in OPEN_LAYOUTS:
        return dress_open(a, y)
    K = _cond()
    cond = K.Condition()
    seed = K.property_seed(a.sid)
    built = float(y["built"])
    conf = p.conf("yard")
    kit = k11_frontage._kit().load()["parts"]
    D = p.depth_m
    b = a.boundary
    s_south, s_north = p.boundary["lot_s_m"]
    curb_in = b["line_x_m"] - kit["curb"]["width_m"] / 2          # the curb's house face
    pier_in = b["line_x_m"] - kit["pier"]["section_m"] / 2        # the gate piers' house face
    public = D + p.entrance_kit["front_yard_m"]                    # the public walk's inner edge
    wall_face = s_south + kit["wall"]["thickness_m"]               # the boundary wall's north face
    foot = b["stoop_foot_x_m"]
    door = next(o for o in p.openings if o.component == "k01.opening.door_leaf" and o.wall == k11_frontage.STREET_FRONT)
    # the stoop as built: its steps and cheeks (a splash stone is 0.04 m high, a step is not)
    # T-3206: within the stoop's own half-width, as K11 reads its foot (T-3171): a porch's
    # flight as wide as its hood (1827's, 5 m) has every tread's ends past 2 m
    reach = max(2.0, p.stoop_width_m / 2 + 0.1)
    stoop = [-q[2] for q in a.prim("stoop_stone").pos
             if D + 0.05 < q[0] <= foot + 1e-6 and q[1] > 0.1 and abs(-q[2] - p.stoop_s_m(door.s_m)) < reach]
    st0, st1 = min(stoop), max(stoop)
    ea, eb = b["entrance_s_m"]
    w0, w1 = ea + JOINT_M, eb - JOINT_M
    bays = _bay_feet(a, D, 0.0, s_north)

    def wall_u(s):
        for sp in bays:
            if sp[0][0] <= s <= sp[-1][0]:
                for (sa, ua), (sb, ub) in zip(sp, sp[1:]):
                    if sa <= s <= sb:
                        return ua + (ub - ua) * ((s - sa) / (sb - sa) if sb > sa else 0.0)
        return D

    def strip(s):
        """The bare strip's reach in u at s: the kit's width, square to the wall foot."""
        h = 1e-3
        slope = (wall_u(s + h) - wall_u(s - h)) / (2 * h)
        grow = min(math.sqrt(1.0 + slope * slope), MAX_SLOPE_GROW)
        return float(cond.bare_width(s, built=built, seed=seed)) * grow

    # -- the lawn, its bare strip and the earth under the stoop, column by column ---------
    cuts = {0.0, s_north, st0, st1, w0, w1}
    for sp in bays:
        cuts |= {sp[0][0], sp[-1][0]}
    cuts = sorted(c for c in cuts if 0.0 <= c <= s_north)
    edges = []
    for lo, hi in zip(cuts, cuts[1:]):
        n = max(1, math.ceil((hi - lo) / STEP_S - 1e-9))
        edges += [lo + (hi - lo) * i / n for i in range(n)]
    edges.append(cuts[-1])
    lawn_rows, earth_rows, under_rows = [], [], []
    for s0, s1 in zip(edges, edges[1:]):
        mid = (s0 + s1) / 2
        if st0 <= mid <= st1:
            under_rows.append([[(x, LAWN_Y, -s, 1.0) for x in (D, foot)] for s in (s0, s1)])
            if not w0 <= mid <= w1:
                lawn_rows.append([[(x, LAWN_Y, -s, 1.0) for x in (foot, curb_in)] for s in (s0, s1)])
            continue
        e = [(wall_u(s), wall_u(s) + strip(s)) for s in (s0, s1)]
        earth_rows.append([[(u, LAWN_Y, -s, 1.0) for u in pair] for s, pair in zip((s0, s1), e)])
        lawn_rows.append([[(pair[1], LAWN_Y, -s, 1.0), (curb_in, LAWN_Y, -s, 1.0)] for s, pair in zip((s0, s1), e)])
    lawn_tris = sum(_up_grid(a, SURFACES["turf"], r, conf) for r in lawn_rows)
    earth_tris = sum(_up_grid(a, SURFACES["earth"], r, conf) for r in earth_rows + under_rows)
    widths = [strip(s) for s in edges if not st0 <= s <= st1]

    # -- the service walk: cinder down the side passage, worn along its centre ------------
    S = y.get("service_walk") or {"wear_tone": 1.0}     # T-3215: none behind unbroken boards
    sk = 1.0 - float(S["wear_tone"])
    c = (wall_face + 0.0) / 2
    half = (0.0 - wall_face) / 2
    if S.get("band") == "gate":
        # T-3206: a wide side yard (1816's, 1824's) keeps its walk to the side gate's own width
        # all the way back, along the lot line, and leaves the rest of the passage to the ground
        wall_face, c0 = b["side_gate_s_m"][0] + JOINT_M, b["side_gate_s_m"][1]
        c, half = (wall_face + c0) / 2, (c0 - wall_face) / 2
    offs = sorted({max(-half, min(half, o)) for o in (-half, -0.5, -0.35, -0.2, 0.0, 0.2, 0.35, 0.5, half)})

    def walk_rows(u0, u1, s_lo, s_hi, use, centre, k, offsets, y_top):
        n = max(1, math.ceil((u1 - u0) / ROW_U - 1e-9))
        cols = sorted({min(s_hi, max(s_lo, centre + o)) for o in offsets})
        rows = []
        for i in range(n + 1):
            u = u0 + (u1 - u0) * i / n
            rows.append([(u, y_top, -s, 1.0 - k * float(cond.path_wear(s - centre, u, use=use, built=built, seed=seed)))
                         for s in cols])
        return rows

    service_tris = 0
    if "service_walk" in y:
        to_u = float(S["to_u_m"])
        service_tris = _up_grid(a, SURFACES["cinder"], walk_rows(to_u, pier_in, wall_face, c + half, "service_walk", c, sk, offs, LAWN_Y), conf)
        sa, sb = b["side_gate_s_m"]
        service_tris += _up_grid(a, SURFACES["cinder"], walk_rows(pier_in, public, sa + JOINT_M, sb, "service_walk", c, sk, offs, LAWN_Y), conf)

    # -- the front walk: stone flags from the stoop's foot to the public walk -------------
    F = y["front_walk"]
    fk = 1.0 - float(F["wear_tone"])
    top = float(F["top_m"])
    L = public - foot
    nf = max(1, round(L / float(F["flag_m"])))
    fl = (L - (nf - 1) * JOINT_M) / nf
    fhalf = (w1 - w0) / 2
    foffs = (-fhalf, -0.5, -0.25, 0.0, 0.25, 0.5, fhalf)
    mat = SURFACES["stone_flags"]
    pr = a.prim(mat)
    flag_tris = 0
    for j in range(nf):
        u0 = foot + j * (fl + JOINT_M)
        u1 = u0 + fl
        flag_tris += _up_grid(a, mat, walk_rows(u0, u1, w0, w1, "front_walk", p.stoop_s_m(door.s_m), fk, foffs, top), conf)
        # the flag's edges, down to its bed: its long sides, its joints and its street end
        bs = a.basis(mat, (0.0, 0.0, 0.0), (1.0, 0.0, 0.0), UP, seed)
        be = a.basis(mat, (0.0, 0.0, 0.0), (0.0, 0.0, -1.0), UP, seed)
        P = lambda u, yy, s: (u, yy, -s)
        sides = [([P(u0, -FLAG_SINK, w0), P(u1, -FLAG_SINK, w0), P(u1, top, w0), P(u0, top, w0)], (0.0, 0.0, 1.0), bs),
                 ([P(u0, -FLAG_SINK, w1), P(u1, -FLAG_SINK, w1), P(u1, top, w1), P(u0, top, w1)], (0.0, 0.0, -1.0), bs),
                 ([P(u1, -FLAG_SINK, w0), P(u1, -FLAG_SINK, w1), P(u1, top, w1), P(u1, top, w0)], (1.0, 0.0, 0.0), be)]
        if j:   # the first flag abuts the stoop's bottom riser, and its face there is never seen
            sides.append(([P(u0, -FLAG_SINK, w0), P(u0, -FLAG_SINK, w1), P(u0, top, w1), P(u0, top, w0)], (-1.0, 0.0, 0.0), be))
        for pts, n, basis in sides:
            pr.face(pts, n, basis, conf)
            flag_tris += 2

    a.instance(LAWN, "yard", {"built": built, "age_factor": round(cond.factor(built), 4),
                              "strip_m": [round(min(widths), 4), round(max(widths), 4)],
                              "triangles": lawn_tris, "earth_triangles": earth_tris},
               {"street_front_south": (D, LAWN_Y, 0.0), "street_front_north": (D, LAWN_Y, -s_north)})
    a.instance(FRONT_WALK, "yard", {"flags": nf, "flag_m": round(fl, 4), "width_m": round(w1 - w0, 4),
                                    "wear_tone_min": round(1.0 - fk * float(cond.path_wear(0.0, foot, use="front_walk", built=built, seed=seed)), 4),
                                    "triangles": flag_tris},
               {"stoop_foot": (foot, top, -p.stoop_s_m(door.s_m)), "public_walk": (public, top, -p.stoop_s_m(door.s_m))})
    if "service_walk" in y:
        a.instance(SERVICE_WALK, "yard", {"length_m": round(public - to_u, 4), "width_m": round(2 * half, 4),
                                          "triangles": service_tris},
                   {"rear_end": (to_u, LAWN_Y, -c), "gate": (pier_in, LAWN_Y, -(sa + sb) / 2)})
    a.yard = {"lawn_triangles": lawn_tris, "earth_triangles": earth_tris, "flag_triangles": flag_tris,
              "service_triangles": service_tris, "strip_m": [round(min(widths), 4), round(max(widths), 4)],
              "stoop_s_m": [round(st0, 4), round(st1, 4)], "bays": len(bays)}


# -----------------------------------------------------------------------------------
# T-3206: a yard behind a stone coping wall — the walk through its opening
# -----------------------------------------------------------------------------------

PASSAGE_CLEAR_M = 0.45   # a turned walk's cross leg stands this far off the wall's back face


def open_spec(params, y: dict) -> dict:
    """`yard` inside a `stone_coping_wall`: as `spec`, but the walk names its width (no gate
    sizes it), and the service walk is optional and names the passage it runs down."""
    if y.get("lawn") != "turf":
        raise ValueError("yard.lawn builds 'turf' alone")
    if y.get("grass_edge") != "street_front":
        raise ValueError("yard.grass_edge runs along 'street_front' alone")
    fw = y.get("front_walk") or {}
    if fw.get("surface") != "stone_flags":
        raise ValueError("yard builds a stone_flags front walk")
    if not 0.9 <= float(fw.get("width_m", 0)) <= 3.0:
        raise ValueError("yard.front_walk.width_m: behind a coping wall the walk names its width, 0.9-3.0 m")
    if not 0.62 <= float(fw["wear_tone"]) <= 1.0:
        raise ValueError(f"yard.front_walk.wear_tone {fw['wear_tone']} is under the kit's floor (0.62)")
    if not 0.3 <= float(fw["flag_m"]) <= 1.8:
        raise ValueError("yard.front_walk.flag_m is a flag's length, 0.3 to 1.8 m")
    if not LAWN_Y < float(fw["top_m"]) <= 0.1:
        raise ValueError("yard.front_walk.top_m stands a flag over the lawn, and no more than 0.1 m")
    sw = y.get("service_walk")
    if sw is not None:
        if sw.get("surface") not in ("cinder", "stone_flags") or sw.get("side") not in ("south", "north"):
            raise ValueError("yard.service_walk: a cinder or stone_flags walk down the 'south' or 'north' passage")
        if not 0.62 <= float(sw["wear_tone"]) <= 1.0:
            raise ValueError(f"yard.service_walk.wear_tone {sw['wear_tone']} is under the kit's floor (0.62)")
    return y


def _start(a, axis, w):
    """Where the walk leaves the stoop: (u, s0, s1) — the stoop's foot square to its axis, or a
    side stoop's flight end (k07_entrances.Entrance._side_stoop: the foot opens toward `run`, its
    flight `out_m` off the front), the band beyond it."""
    p, b, D = a.p, a.boundary, a.p.depth_m
    ss = p.entrance_kit.get("side_stoop")
    if not ss:
        if b.get("stoop_foot_x_m") is None:
            raise ValueError("the coping wall read no stoop foot to start the walk at")
        return b["stoop_foot_x_m"], axis - w / 2, axis + w / 2
    k = 1.0 if ss["run"] == "right" else -1.0
    lo, hi = sorted(float(x) for x in ss["landing_v_m"])
    foot = (hi if k > 0 else lo) + k * (p.risers - 1) * p.tread_m
    return D + float(ss["out_m"]), *sorted((foot, foot + k * w))


def _route(start, openings, inner, public, w):
    """The walk's legs, each (u0, u1, s0, s1, along): straight out through an opening that holds
    the band with 0.05 m to spare, or turned along the wall's back to the nearest opening."""
    u0, b0, b1 = start
    fits = [o for o in openings if o[0] + 0.05 <= b0 and b1 <= o[1] - 0.05]
    if fits:
        return [(u0, public, b0, b1, "u")]
    if not openings:
        raise ValueError("the coping wall leaves no opening for the walk to pass")
    c = (b0 + b1) / 2
    o = min(openings, key=lambda o: abs((o[0] + o[1]) / 2 - c))
    wo = min(w, o[1] - o[0] - 0.1)
    if wo < 0.8:
        raise ValueError(f"the coping wall's opening s {o[0]:.3f}..{o[1]:.3f} is too narrow for a walk")
    oc = (o[0] + o[1]) / 2
    o0, o1 = oc - wo / 2, oc + wo / 2
    ut = inner - PASSAGE_CLEAR_M - w
    if ut < u0 + 0.3:
        raise ValueError(f"no room to turn the walk between the stoop's foot ({u0:.3f}) and the wall ({inner:.3f})")
    return [(u0, ut, b0, b1, "u"), (ut, ut + w, min(b0, o0), max(b1, o1), "s"), (ut + w, public, o0, o1, "u")]


def dress_open(a, y):
    """Lay a yard behind a stone coping wall: the lawn across the lot's front between the house
    (and its bays) and the wall's back, earth under the stoop, the front walk's legs of flags and
    the optional service walk."""
    p = a.p
    K = _cond()
    cond = K.Condition()
    seed = K.property_seed(a.sid)
    built = float(y["built"])
    conf = p.conf("yard")
    D = p.depth_m
    b = a.boundary
    s_south, s_north = p.boundary["lot_s_m"]
    inner = b["inner_x_m"]
    public = D + p.entrance_kit["front_yard_m"]
    openings = b["openings_s_m"]
    door = next(o for o in p.openings if o.component == "k01.opening.door_leaf" and o.wall == k11_frontage.STREET_FRONT)
    axis = p.stoop_s_m(door.s_m)
    F = y["front_walk"]
    w = float(F["width_m"])
    start = _start(a, axis, w)
    legs = _route(start, openings, inner, public, w)
    for u0, u1, s0, s1, along in legs:
        if u1 <= u0 + 1e-6 or s1 <= s0 + 1e-6:
            raise ValueError(f"a walk leg u {u0:.3f}..{u1:.3f} s {s0:.3f}..{s1:.3f} has no length")
    # the stoop as built (its steps and cheeks), for the earth under it
    foot = b.get("stoop_foot_x_m") or start[0]
    stoop = [-q[2] for q in a.prim("stoop_stone").pos
             if D + 0.05 < q[0] <= foot + 1e-6 and q[1] > 0.1 and abs(-q[2] - axis) < max(2.0, p.stoop_width_m / 2 + 0.1)]
    st0, st1 = (min(stoop), max(stoop)) if stoop else (axis, axis)
    S = y.get("service_walk")
    lo, hi = s_south, s_north
    if S and S["side"] == "south":
        lo = 0.0
    if S and S["side"] == "north":
        hi = p.width_m
    w0, w1 = legs[0][2], legs[0][3]
    bays = _bay_feet(a, D, 0.0, s_north)

    def wall_u(s):
        for sp in bays:
            if sp[0][0] <= s <= sp[-1][0]:
                for (sa, ua), (sb, ub) in zip(sp, sp[1:]):
                    if sa <= s <= sb:
                        return ua + (ub - ua) * ((s - sa) / (sb - sa) if sb > sa else 0.0)
        return D

    def strip(s):
        if not 0.0 <= s <= p.width_m:
            return 0.0                    # beside the house there is no wall foot to bare
        h = 1e-3
        slope = (wall_u(s + h) - wall_u(s - h)) / (2 * h)
        grow = min(math.sqrt(1.0 + slope * slope), MAX_SLOPE_GROW)
        return float(cond.bare_width(s, built=built, seed=seed)) * grow

    # -- the lawn, its bare strip and the earth under the stoop, column by column ---------
    cuts = {lo, hi, 0.0, p.width_m, st0, st1, w0, w1}
    for sp in bays:
        cuts |= {sp[0][0], sp[-1][0]}
    cuts = sorted(c for c in cuts if lo <= c <= hi)
    edges = []
    for c0, c1 in zip(cuts, cuts[1:]):
        n = max(1, math.ceil((c1 - c0) / STEP_S - 1e-9))
        edges += [c0 + (c1 - c0) * i / n for i in range(n)]
    edges.append(cuts[-1])
    lawn_rows, earth_rows, under_rows = [], [], []
    straight_from_foot = legs[0][0] <= foot + 1e-6
    for s0, s1 in zip(edges, edges[1:]):
        mid = (s0 + s1) / 2
        if stoop and st0 <= mid <= st1:
            under_rows.append([[(x, LAWN_Y, -s, 1.0) for x in (D, foot)] for s in (s0, s1)])
            if not (straight_from_foot and w0 <= mid <= w1) and inner > foot + 0.05:
                lawn_rows.append([[(x, LAWN_Y, -s, 1.0) for x in (foot, inner)] for s in (s0, s1)])
            continue
        e = [(wall_u(s), wall_u(s) + strip(s)) for s in (s0, s1)]
        if strip(mid) > 0:
            earth_rows.append([[(u, LAWN_Y, -s, 1.0) for u in pair] for s, pair in zip((s0, s1), e)])
        lawn_rows.append([[(pair[1], LAWN_Y, -s, 1.0), (inner, LAWN_Y, -s, 1.0)] for s, pair in zip((s0, s1), e)])
    lawn_tris = earth_tris = 0          # integer counts, added left to right (T-2363)
    for r in lawn_rows:
        lawn_tris += _up_grid(a, SURFACES["turf"], r, conf)
    for r in earth_rows + under_rows:
        earth_tris += _up_grid(a, SURFACES["earth"], r, conf)
    widths = [strip(s) for s in edges if 0.0 <= s <= p.width_m and not st0 <= s <= st1] or [0.0]

    # -- the front walk: each leg its flags, worn along its centre -------------------------
    fk = 1.0 - float(F["wear_tone"])
    top = float(F["top_m"])
    mat = SURFACES["stone_flags"]
    pr = a.prim(mat)
    flag_tris, nflags = 0, 0
    for li, (u0, u1, s0, s1, along) in enumerate(legs):
        L = (u1 - u0) if along == "u" else (s1 - s0)
        nf = max(1, round(L / float(F["flag_m"])))
        fl = (L - (nf - 1) * JOINT_M) / nf
        half = ((s1 - s0) if along == "u" else (u1 - u0)) / 2
        offs = (-half, -0.5, -0.25, 0.0, 0.25, 0.5, half)
        for j in range(nf):
            a0 = (u0 if along == "u" else s0) + j * (fl + JOINT_M)
            a1 = a0 + fl
            if along == "u":
                q0, q1, r0, r1 = a0, a1, s0, s1
                cs = (s0 + s1) / 2
                cols = sorted({min(s1, max(s0, cs + o)) for o in offs})
                n = max(1, math.ceil((q1 - q0) / ROW_U - 1e-9))
                rows = [[(q0 + (q1 - q0) * i / n, top, -s,
                          1.0 - fk * float(cond.path_wear(s - cs, q0 + (q1 - q0) * i / n, use="front_walk", built=built, seed=seed)))
                         for s in cols] for i in range(n + 1)]
            else:
                q0, q1, r0, r1 = u0, u1, a0, a1
                cu = (u0 + u1) / 2
                cols = sorted({min(u1, max(u0, cu + o)) for o in offs})
                n = max(1, math.ceil((r1 - r0) / ROW_U - 1e-9))
                rows = [[(u, top, -(r0 + (r1 - r0) * i / n),
                          1.0 - fk * float(cond.path_wear(u - cu, r0 + (r1 - r0) * i / n, use="front_walk", built=built, seed=seed)))
                         for u in cols] for i in range(n + 1)]
            flag_tris += _up_grid(a, mat, rows, conf)
            nflags += 1
            # the flag's four edges, down to its bed (the first abuts the stoop's riser)
            bs = a.basis(mat, (0.0, 0.0, 0.0), (1.0, 0.0, 0.0), UP, seed)
            be = a.basis(mat, (0.0, 0.0, 0.0), (0.0, 0.0, -1.0), UP, seed)
            P = lambda u, yy, s: (u, yy, -s)
            sides = [([P(q0, -FLAG_SINK, r0), P(q1, -FLAG_SINK, r0), P(q1, top, r0), P(q0, top, r0)], (0.0, 0.0, 1.0), bs),
                     ([P(q0, -FLAG_SINK, r1), P(q1, -FLAG_SINK, r1), P(q1, top, r1), P(q0, top, r1)], (0.0, 0.0, -1.0), bs),
                     ([P(q1, -FLAG_SINK, r0), P(q1, -FLAG_SINK, r1), P(q1, top, r1), P(q1, top, r0)], (1.0, 0.0, 0.0), be),
                     ([P(q0, -FLAG_SINK, r0), P(q0, -FLAG_SINK, r1), P(q0, top, r1), P(q0, top, r0)], (-1.0, 0.0, 0.0), be)]
            if li == 0 and j == 0 and not p.entrance_kit.get("side_stoop"):
                sides.pop()       # the first flag abuts the stoop's bottom riser
            for pts, nrm, basis in sides:
                pr.face(pts, nrm, basis, conf)
                flag_tris += 2

    # -- the service walk, down the passage the record names, through the wall's opening ----
    service_tris = 0
    if S:
        if S["side"] == "south":
            pa, pb = s_south + JOINT_M, 0.0
        else:
            pa, pb = p.width_m, s_north - JOINT_M
        if not any(o[0] - 1e-6 <= pa and pb <= o[1] + 1e-6 for o in openings):
            raise ValueError(f"yard.service_walk: no opening in the coping wall across the {S['side']} passage "
                             f"(s {pa:.3f}..{pb:.3f}); the wall's openings are {openings}")
        sk = 1.0 - float(S["wear_tone"])
        c = (pa + pb) / 2
        half = (pb - pa) / 2
        cols = sorted({max(pa, min(pb, c + o)) for o in (-half, -0.5, -0.35, -0.2, 0.0, 0.2, 0.35, 0.5, half)})
        to_u = float(S["to_u_m"])
        n = max(1, math.ceil((public - to_u) / ROW_U - 1e-9))
        y_s = LAWN_Y + (0.004 if S["surface"] == "stone_flags" else 0.0)
        rows = [[(to_u + (public - to_u) * i / n, y_s, -s,
                  1.0 - sk * float(cond.path_wear(s - c, to_u + (public - to_u) * i / n, use="service_walk", built=built, seed=seed)))
                 for s in cols] for i in range(n + 1)]
        service_tris = _up_grid(a, SURFACES[S["surface"]], rows, conf)

    a.instance(LAWN, "yard", {"built": built, "age_factor": round(cond.factor(built), 4),
                              "strip_m": [round(min(widths), 4), round(max(widths), 4)],
                              "triangles": lawn_tris, "earth_triangles": earth_tris},
               {"street_front_south": (D, LAWN_Y, 0.0), "street_front_north": (D, LAWN_Y, -s_north)})
    a.instance(FRONT_WALK, "yard", {"flags": nflags, "width_m": round(w, 4), "triangles": flag_tris,
                                    "legs_m": [[round(u0, 4), round(u1, 4), round(s0, 4), round(s1, 4), al]
                                               for u0, u1, s0, s1, al in legs]},
               {"stoop_foot": (legs[0][0], top, -(legs[0][2] + legs[0][3]) / 2),
                "public_walk": (public, top, -(legs[-1][2] + legs[-1][3]) / 2)})
    if S:
        a.instance(SERVICE_WALK, "yard", {"length_m": round(public - float(S["to_u_m"]), 4), "width_m": round(pb - pa, 4),
                                          "triangles": service_tris},
                   {"rear_end": (float(S["to_u_m"]), LAWN_Y, -(pa + pb) / 2), "gate": (inner, LAWN_Y, -(pa + pb) / 2)})
    a.yard = {"lawn_triangles": lawn_tris, "earth_triangles": earth_tris, "flag_triangles": flag_tris,
              "service_triangles": service_tris, "strip_m": [round(min(widths), 4), round(max(widths), 4)],
              "stoop_s_m": [round(st0, 4), round(st1, 4)], "bays": len(bays), "legs_m": legs}
