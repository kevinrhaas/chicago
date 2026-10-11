"""K11 ironwork kit laid on a K01 frontage's front yard: fence, gates, piers, boundary wall (T-2319).

TICKET T-2319: piece 2 of T-1853 (package K11 of the T-1837 Prairie programme). Piece 1,
T-2318, built the ironwork kit (`k11_ironwork.py` from `data/components/prairie_1904/
k11_ironwork.json`) on specimen boards. This module puts the kit's own pieces on a house:
it calls the kit's builders (`fence_run`, `pier`, `hinges`, `leaf`, `wall_run`) and moves
what they build into the assembly's frame, so every picket, rail, pier and coping is the
geometry the kit's gate measures, not a copy of it.

What the record's `boundary` names, and what is built for it:

  fence     `k11.fence.spear_on_curb` along the street line, its curb's street face ON the
            line, from the south gate's pier to the north lot line, stopped at a pier on
            each side of every opening. No curb, rail or picket crosses an opening.
  entrance  `k11.gate.walk_gate_on_piers` on the walk to the door: two stone piers square
            to the stoop and a PAIR of leaves, one hung on each pier. A single leaf the
            kit's width would strike the stoop: the stoop's foot stands less than a metre
            behind the line, so each leaf is kept shorter than that gap, and the generator
            refuses a leaf whose swing (the whole disc it sweeps, at every angle) reaches
            the stoop's built mesh.
  side gate the kit's single walk gate across the mouth of the side passage, hung on the
            boundary wall's street pier and shutting on a stone pier in line with the
            house's south wall. The passage is the house's only way round to the rear
            (the coach house stands on the alley), so it is gated, never fenced.
  wall      `k11.wall.brick_with_piers` on the south lot line, its south face on the line,
            from the street pier back to the neighbour's front: 1812's draft stands on the
            line behind that, and the wall stops short of it.

A generic kit part is allowed here because 1808's own boundary is not read in any source
this project holds (k11_ironwork.json `restrictions`: a generic part never stands in place
of a documented one). The north side, against 1800 (Glessner), is left open: the yard
transition there is its own question (FRONTAGE-REGISTER: T-1944) and Glessner's boundary
is documented, so nothing generic is put on it.
"""

from __future__ import annotations

import math

FENCE = "k11.fence.spear_on_curb"
GATE = "k11.gate.walk_gate_on_piers"
WALL = "k11.wall.brick_with_piers"
STREET_FRONT = "k01.wall.street_front"
# the kit's roles, worn in the house's own slots; the wall's brick has its own slot,
# because "brick" is an envelope material and the contract reads grade off its lowest
# vertex (k01_contract.json measures): a wall sunk 0.10 m would move the house's origin
ROLE_MATERIAL = {"iron": "iron", "stone": "stoop_stone", "brick": "k11_wall_brick"}
CLEAR_M = 0.05          # a swinging leaf keeps this far from the stoop; nothing comes nearer the walk


def _kit():
    # imported late, as k10_frontage does: the kit imports k01_frontage's vector helpers
    from . import k11_ironwork
    return k11_ironwork


def spec(params) -> dict | None:
    """The record's `boundary`, checked against what this module can build."""
    t = getattr(params, "boundary", None)
    if not t:
        return None
    if t.get("fence") != FENCE:
        raise ValueError(f"boundary.fence builds {FENCE!r} alone")
    for g in ("entrance_gate", "side_gate"):
        if t[g].get("variant") != GATE:
            raise ValueError(f"boundary.{g} builds {GATE!r} alone")
    if t["wall"].get("variant") != WALL:
        raise ValueError(f"boundary.wall builds {WALL!r} alone")
    s0, s1 = t["lot_s_m"]
    if not s0 <= 0.0 < params.width_m <= s1 + 0.25:
        raise ValueError(f"boundary.lot_s_m {t['lot_s_m']} does not hold the street front 0..{params.width_m}")
    if t["entrance_gate"].get("leaves") != 2:
        raise ValueError("boundary.entrance_gate is built as a pair of leaves")
    return t


def _to_fence(mesh, line):
    """Kit frame (x along the line, z toward the street) -> the assembly's, for the street
    front: x is the street front's s (south to north, the assembly's -Z), z is out of the
    house (+X). A proper rotation, so windings and normals carry over."""
    mesh.pos = [(line + z, y, -x) for x, y, z in mesh.pos]
    mesh.nrm = [(z, y, -x) for x, y, z in mesh.nrm]


def _to_wall(mesh, zc):
    """Kit frame -> the assembly's, for a wall run along +X (u) centred on Z = zc."""
    mesh.pos = [(x, y, zc + z) for x, y, z in mesh.pos]


def _lay(a, pieces, conf, cid):
    """Add kit pieces (already in the assembly's frame) to the assembly's primitives."""
    from .k01_frontage import MATERIALS
    tris = 0
    for piece in pieces:
        mat = ROLE_MATERIAL[piece.role]
        fab = MATERIALS[mat].get("fabric")
        tu, tv = a.tiles[fab] if fab else (1.0, 1.0)
        pr = a.prim(mat)
        base = len(pr.pos)
        m = piece.mesh
        for q, n, uv in zip(m.pos, m.nrm, m.uv):
            pr.pos.append(q)
            pr.nrm.append(n)
            pr.uv.append((uv[0] / tu, uv[1] / tv))   # the kit's UVs are surface metres
            pr.conf.append(conf)
            pr.tone.append(pr.tone_of(q[1]) if pr.tone_of else 1.0)
        pr.idx += [base + i for i in m.idx]
        tris += m.triangles()
    a.trim_triangles[cid] = a.trim_triangles.get(cid, 0) + tris
    return tris


def _reach(pieces, hx):
    """The radius of the disc a leaf sweeps about its hinge axis (x = hx, z = 0, kit frame)."""
    return max(math.hypot(x - hx, z) for pc in pieces for x, _, z in pc.mesh.pos)


def dress(a):
    """Lay the record's boundary on the assembly: the front fence and its piers, the
    entrance's pair of gates, the side passage's gate and the south boundary wall."""
    p = a.p
    t = spec(p)
    if not t:
        return
    K = _kit()
    data = K.load()
    P = data["parts"]
    conf = p.conf("boundary")
    D = p.depth_m
    G, Pr, Wd = P["gate"], P["pier"], P["wall"]
    ps, wp = Pr["section_m"], Wd["pier_m"]
    s_south, s_north = t["lot_s_m"]
    street = D + t["street_line_m"]
    line = street - P["curb"]["width_m"] / 2           # the curb's street face on the street line
    walk = D + p.entrance_kit["front_yard_m"]           # the public walk's inner edge

    # the stoop, as built: its foot and its sides, read off K07's mesh in front of the door
    door = next(o for o in p.openings if o.component == "k01.opening.door_leaf" and o.wall == STREET_FRONT)
    stoop = [q for q in a.prim("stoop_stone").pos if q[0] > D + 0.05 and abs(-q[2] - door.s_m) < 2.0]
    foot = max(q[0] for q in stoop)

    var = K.Variant({"id": FENCE, "kind": "fence"}, data)
    # the entrance: a pair of leaves square to the door, each hung on its own pier
    E = t["entrance_gate"]
    c = E["clear_m"]
    if c < G["clear_min_m"]:
        raise ValueError(f"the entrance gate's {c} m is under the kit's {G['clear_min_m']} m clear")
    ea, eb = door.s_m - c / 2, door.s_m + c / 2
    pe1, pe2 = var.pier(ea - ps / 2), var.pier(eb + ps / 2)
    Lw = (c - 2 * G["hinge_offset_m"] - G["keeper_gap_m"]) / 2
    hxa, ha = var.hinges(pe1.name, ea)
    leaf_a = var.leaf(ha, hxa, Lw, E["drawn_deg"], tag=" south")
    hxb, hb = var.hinges(pe2.name, eb, side=-1)
    leaf_b = var.leaf(hb, hxb, Lw, E["drawn_deg"], side=-1, tag=" north")
    R = max(_reach(leaf_a, hxa), _reach(leaf_b, hxb))
    if line - R < foot + CLEAR_M:
        raise ValueError(f"an entrance leaf sweeps {R:.3f} m from the line at X {line:.3f}, into the stoop's "
                         f"foot at {foot:.3f}: keep each leaf under {line - foot - CLEAR_M:.3f} m")
    # the side passage: the wall's street pier (its south face on the lot line) to a stone
    # pier in line with the house's south wall; hung on the wall pier, shut on the stone one
    S = t["side_gate"]
    sa, sb = s_south + wp, S["pier_s_m"]
    if sb - sa < G["clear_min_m"]:
        raise ValueError(f"the side passage's gate has {sb - sa:.3f} m clear, under the kit's {G['clear_min_m']} m")
    ps1 = var.pier(sb + ps / 2)
    hxs, hs = var.hinges("wall pier", sa)
    k = G["keeper_proud_m"]
    var.member("latch keeper", "iron", ps1.name, sb - k, sb + 0.06, 0.88, 0.92, -0.015, 0.015, gate=True)
    leaf_s = var.leaf(hs, hxs, (sb - k - G["keeper_gap_m"]) - hxs, S["drawn_deg"], tag=" side")
    if line - _reach(leaf_s, hxs) < D + CLEAR_M:
        raise ValueError("the side gate's leaf would sweep into the house's front")
    # the fence: from the side gate's pier to the entrance's, and from the entrance's to an
    # end post whose curb stops on the north lot line
    south = var.fence_run(sb + ps, ea - ps, "spear", "south run", host_a=ps1.name, host_b=pe1.name)
    north = var.fence_run(eb + ps, s_north - 0.12, "spear", "north run", host_a=pe2.name)
    # the rule the kit's restriction states, on the built geometry: no curb, rail or picket
    # of a run inside an opening (the pier caps' 50 mm overhang stands above the gate)
    for lo, hi, what in ((ea, eb, "entrance"), (sa, sb, "side passage")):
        for pc in var.pieces:
            if pc.meta.get("gate") or "cap" in pc.name:
                continue
            xs = [x for x, _, _ in pc.mesh.pos]
            if min(xs) < hi - 1e-6 and max(xs) > lo + 1e-6:
                raise ValueError(f"{pc.name} crosses the {what} opening s {lo:.3f}..{hi:.3f}")
    for pc in var.pieces:
        _to_fence(pc.mesh, line)
    reach = max(q[0] for pc in var.pieces for q in pc.mesh.pos)
    if reach > walk - CLEAR_M:
        raise ValueError(f"the boundary reaches X {reach:.3f}, onto the walk at {walk:.3f}")

    # the wall, on the south lot line from the street pier back toward 1812's front
    W = t["wall"]
    wv = K.Variant({"id": WALL, "kind": "wall"}, data)
    x0 = W["from_u_m"]
    piers = wv.wall_run(x0, line, H=W["height_m"])
    for pc in wv.pieces:
        _to_wall(pc.mesh, -(s_south + wp / 2))

    seed = a.instance(FENCE, "fence", {"length_m": round((ea - ps) - (sb + ps) + (s_north - 0.12) - (eb + ps), 4),
                                        "runs": 2, "posts": len(south) + len(north) - 2},
                      {"line_south": (line, 0.0, -(sb + ps)), "line_north": (line, 0.0, -(s_north - 0.12))})
    var.seed = wv.seed = seed
    a.instance(GATE, "gate", {"leaves": 2, "clear_m": c, "leaf_m": round(Lw, 4), "swing_reach_m": round(R, 4),
                              "stoop_foot_m": round(foot - D, 4)},
               {"opening": (line, 0.0, -door.s_m)})
    a.instance(GATE, "gate", {"leaves": 1, "clear_m": round(sb - sa, 4)}, {"opening": (line, 0.0, -(sa + sb) / 2)})
    a.instance(WALL, "wall", {"length_m": round(line - x0, 4), "height_m": W["height_m"], "piers": len(piers)},
               {"street_end": (line, 0.0, -(s_south + wp / 2)), "rear_end": (x0, 0.0, -(s_south + wp / 2))})
    _lay(a, [pc for pc in var.pieces if not pc.meta.get("gate")], conf, FENCE)
    _lay(a, [pc for pc in var.pieces if pc.meta.get("gate")], conf, GATE)
    _lay(a, wv.pieces, conf, WALL)
    a.boundary = {"line_x_m": round(line, 4), "stoop_foot_x_m": round(foot, 4), "leaf_reach_m": round(R, 4),
                  "entrance_s_m": [round(ea, 4), round(eb, 4)], "side_gate_s_m": [round(sa, 4), round(sb, 4)],
                  "fence_posts_s_m": [round(x, 3) for x in south + north], "wall_piers_x_m": [round(x, 3) for x in wv.meta["piers"]]}
