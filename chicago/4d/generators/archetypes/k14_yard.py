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


def spec(params) -> dict | None:
    """The record's `yard`, checked against what this module can build."""
    y = getattr(params, "yard", None)
    if not y:
        return None
    if not getattr(params, "boundary", None):
        raise ValueError("a yard is laid inside a K11 boundary, and this record names none")
    if not params.boundary.get("side_gate"):
        raise ValueError("a yard's service walk runs through the K11 side gate, and this boundary names none")
    if y.get("lawn") != "turf":
        raise ValueError("yard.lawn builds 'turf' alone")
    if y.get("grass_edge") != "street_front":
        raise ValueError("yard.grass_edge runs along 'street_front' alone")
    fw, sw = y.get("front_walk") or {}, y.get("service_walk") or {}
    if fw.get("surface") != "stone_flags" or sw.get("surface") != "cinder":
        raise ValueError("yard builds a stone_flags front walk and a cinder service walk")
    for name, w in (("front_walk", fw), ("service_walk", sw)):
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


def dress(a):
    """Lay the record's yard on the assembly: the lawn and its bare strip, the earth under
    the stoop, the front walk's flags and the service walk's cinder."""
    p = a.p
    y = spec(p)
    if not y:
        return
    if not getattr(a, "boundary", None):
        raise ValueError("the yard is laid after the K11 boundary, and none was built")
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
    stoop = [-q[2] for q in a.prim("stoop_stone").pos
             if D + 0.05 < q[0] <= foot + 1e-6 and q[1] > 0.1 and abs(-q[2] - door.s_m) < 2.0]
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
    S = y["service_walk"]
    sk = 1.0 - float(S["wear_tone"])
    c = (wall_face + 0.0) / 2
    half = (0.0 - wall_face) / 2
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

    to_u = float(S["to_u_m"])
    service_tris = _up_grid(a, SURFACES["cinder"], walk_rows(to_u, pier_in, wall_face, 0.0, "service_walk", c, sk, offs, LAWN_Y), conf)
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
        flag_tris += _up_grid(a, mat, walk_rows(u0, u1, w0, w1, "front_walk", door.s_m, fk, foffs, top), conf)
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
               {"stoop_foot": (foot, top, -door.s_m), "public_walk": (public, top, -door.s_m)})
    a.instance(SERVICE_WALK, "yard", {"length_m": round(public - to_u, 4), "width_m": round(-wall_face, 4),
                                      "triangles": service_tris},
               {"rear_end": (to_u, LAWN_Y, -c), "gate": (pier_in, LAWN_Y, -(sa + sb) / 2)})
    a.yard = {"lawn_triangles": lawn_tris, "earth_triangles": earth_tris, "flag_triangles": flag_tris,
              "service_triangles": service_tris, "strip_m": [round(min(widths), 4), round(max(widths), 4)],
              "stoop_s_m": [round(st0, 4), round(st1, 4)], "bays": len(bays)}
