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
            line behind that, and the wall stops short of it. A record that names no `wall`
            (T-2366: 1612's photograph shows none) builds none, and its side gate hangs on
            a pier of its own on the lot line.
  posts     (T-2366) where a record names `posts`, every gate hangs on a cast-iron post of
            that section and height, with no urn, instead of the kit's stone pier.
  boards    (T-2455) a record whose `fence` is `k11.fence.side_boards` closes its street
            line with timber boards `board_height_m` high instead of iron on a curb: the
            same close-boarded run 1620's north side is built of, from the south lot line
            (or the side gate's pier) to the entrance's pier and on to the north lot line.
            Such a front may name no `side_gate` where its picture draws the boards
            unbroken across the side yard's mouth (1616's, in the 1874 engraving of 1620).

A generic kit part is allowed here because 1808's own boundary is not read in any source
this project holds (k11_ironwork.json `restrictions`: a generic part never stands in place
of a documented one). The north side, against 1800 (Glessner), is left open: the yard
transition there is its own question (FRONTAGE-REGISTER: T-1944) and Glessner's boundary
is documented, so nothing generic is put on it.
"""

from __future__ import annotations

import math

FENCE = "k11.fence.spear_on_curb"
# T-2406: a timber board fence closing a side yard (1620's north side, its 1874 engraving)
BOARDS = "k11.fence.side_boards"
# T-1861: the fences a record may name, and the run style each is built in (k11_ironwork
# fence_run); the scroll band is the register's "lattice/iron boundary" at 1620. T-2455:
# the boards may close a street line too (1616's, drawn past 1620's corner in 1874)
FENCES = {FENCE: "spear", "k11.fence.scroll_band": "scroll", "k11.fence.lattice_arcade": "lattice",
          BOARDS: "boards"}
GATE = "k11.gate.walk_gate_on_piers"
WALL = "k11.wall.brick_with_piers"
STREET_FRONT = "k01.wall.street_front"
# the kit's roles, worn in the house's own slots; the wall's brick has its own slot,
# because "brick" is an envelope material and the contract reads grade off its lowest
# vertex (k01_contract.json measures): a wall sunk 0.10 m would move the house's origin
ROLE_MATERIAL = {"iron": "iron", "stone": "stoop_stone", "brick": "k11_wall_brick", "timber": "fence_boards"}
CLEAR_M = 0.05          # a swinging leaf keeps this far from the stoop; nothing comes nearer the walk
# T-2447: a front garden enclosed close before the house rather than on the street line
# (1637's engraving): a brick wall north of the stoop, an iron fence south of it, no gates
GARDEN = "front_garden"


def _kit():
    # imported late, as k10_frontage does: the kit imports k01_frontage's vector helpers
    from . import k11_ironwork
    return k11_ironwork


def spec(params) -> dict | None:
    """The record's `boundary`, checked against what this module can build."""
    t = getattr(params, "boundary", None)
    if not t:
        return None
    if t.get("layout") == "stone_posts_rails":
        if not (0.25 <= t.get("rail_height_m", 0) <= .65 and .35 <= t.get("post_height_m", 0) <= .9 and 1.5 <= t.get("entrance_clear_m", 0) <= 3):
            raise ValueError("stone_posts_rails: low rail, low posts, and a clear stair opening")
        return t
    if t.get("layout") == GARDEN:
        return garden_spec(params, t)
    if t.get("fence") not in FENCES:
        raise ValueError(f"boundary.fence builds one of {sorted(FENCES)}")
    for g in ("entrance_gate", "side_gate"):
        if g in t and t[g].get("variant") != GATE:
            raise ValueError(f"boundary.{g} builds {GATE!r} alone")
    if "entrance_gate" not in t:
        raise ValueError("boundary.entrance_gate: every front is gated on the walk to its door")
    # T-2455: only a boarded street line may close the side yard's mouth without a gate
    if "side_gate" not in t and FENCES[t["fence"]] != "boards":
        raise ValueError(f"boundary.side_gate: an iron front gates its side passage; only {BOARDS!r} may close it")
    if FENCES[t["fence"]] == "boards":
        if not 1.2 <= t.get("board_height_m", 0) <= 2.2:
            raise ValueError("a boarded street line names its height, boundary.board_height_m, 1.2-2.2 m")
        if t.get("side_fence"):
            raise ValueError("boundary.side_fence: a boarded street line has no iron for the boards to take over from")
    # T-2366: a lot whose side is not walled (1612's photograph shows its fence alone)
    # names no `wall`
    if t.get("wall") and t["wall"].get("variant") != WALL:
        raise ValueError(f"boundary.wall builds {WALL!r} alone")
    s0, s1 = t["lot_s_m"]
    if not s0 <= 0.0 < params.width_m <= s1 + 0.25:
        raise ValueError(f"boundary.lot_s_m {t['lot_s_m']} does not hold the street front 0..{params.width_m}")
    if t["entrance_gate"].get("leaves") != 2:
        raise ValueError("boundary.entrance_gate is built as a pair of leaves")
    if FENCES[t["fence"]] == "lattice" and not 0.2 <= t.get("lattice_pitch_m", 0) <= 0.6:
        raise ValueError("a lattice fence names its bay, boundary.lattice_pitch_m, 0.2-0.6 m")
    if t.get("lattice_span_bays", 2) not in (2, 3, 4):
        raise ValueError("boundary.lattice_span_bays: an arch spans 2, 3 or 4 bays")
    b = t.get("side_fence")
    if b:
        if b.get("variant") != BOARDS:
            raise ValueError(f"boundary.side_fence builds {BOARDS!r} alone")
        if not params.width_m + 0.5 <= b["from_s_m"] <= s1 - 1.0:
            raise ValueError(f"boundary.side_fence.from_s_m {b['from_s_m']}: north of the front, a metre short of the lot line")
        if not 1.2 <= b["height_m"] <= 2.2:
            raise ValueError(f"boundary.side_fence.height_m {b['height_m']}: a yard fence stands 1.2-2.2 m")
        if b["to_u_m"] >= 0.0:
            raise ValueError("boundary.side_fence.to_u_m: the boards run back past the house's rear wall")
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
    if t.get("layout") == "stone_posts_rails":
        return stone_boundary(a, t)
    if t.get("layout") == GARDEN:
        return garden(a, t)
    K = _kit()
    data = K.load()
    P = data["parts"]
    conf = p.conf("boundary")
    D = p.depth_m
    G, Pr, Wd = P["gate"], P["pier"], P["wall"]
    ps, wp = Pr["section_m"], Wd["pier_m"]
    # T-2366: a record whose gates hang on cast-iron posts, not stone piers (1612's
    # photograph): `posts` names their section and height, and they carry no urn
    po = t.get("posts")
    if po:
        ps = po["section_m"]

    def pier(x):
        if po:
            return var.pier(x, urn=False, half=ps / 2, h=po["height_m"], role="iron", cap_role="iron")
        return var.pier(x)
    s_south, s_north = t["lot_s_m"]
    street = D + t["street_line_m"]
    line = street - P["curb"]["width_m"] / 2           # the curb's street face on the street line
    walk = D + p.entrance_kit["front_yard_m"]           # the public walk's inner edge

    # the stoop, as built: how far its foot reaches, read off K07's mesh in front of the door
    door = next(o for o in p.openings if o.component == "k01.opening.door_leaf" and o.wall == STREET_FRONT)
    stoop = [q for q in a.prim("stoop_stone").pos if q[0] > D + 0.05 and abs(-q[2] - p.stoop_s_m(door.s_m)) < 2.0]
    foot = max(q[0] for q in stoop)

    fence, style = t["fence"], FENCES[t["fence"]]
    var = K.Variant({"id": fence, "kind": "fence", "pitch_m": t.get("lattice_pitch_m"),
                     "span_bays": t.get("lattice_span_bays", 2)}, data)
    B = t.get("side_fence")
    n_end = B["from_s_m"] - 0.06 if B else s_north - 0.12     # T-2406: the boards take the north end
    if style == "boards":
        n_end = s_north                                         # T-2455: boards run to the lot line, as 1620's do
    # the entrance: a pair of leaves square to the door, each hung on its own pier
    E = t["entrance_gate"]
    c = E["clear_m"]
    if c < G["clear_min_m"]:
        raise ValueError(f"the entrance gate's {c} m is under the kit's {G['clear_min_m']} m clear")
    ea, eb = p.stoop_s_m(door.s_m) - c / 2, p.stoop_s_m(door.s_m) + c / 2
    pe1, pe2 = pier(ea - ps / 2), pier(eb + ps / 2)
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
    S = t.get("side_gate")
    sa = sb = None
    if S:
        sa, sb = s_south + (wp if t.get("wall") else ps), S["pier_s_m"]
        if sb - sa < G["clear_min_m"]:
            raise ValueError(f"the side passage's gate has {sb - sa:.3f} m clear, under the kit's {G['clear_min_m']} m")
        ps1 = pier(sb + ps / 2)
        # hung on the wall's street pier, or with no wall on a stone pier on the lot line
        hxs, hs = var.hinges("wall pier" if t.get("wall") else pier(s_south + ps / 2).name, sa)
        k = G["keeper_proud_m"]
        var.member("latch keeper", "iron", ps1.name, sb - k, sb + 0.06, 0.88, 0.92, -0.015, 0.015, gate=True)
        leaf_s = var.leaf(hs, hxs, (sb - k - G["keeper_gap_m"]) - hxs, S["drawn_deg"], tag=" side")
        if line - _reach(leaf_s, hxs) < D + CLEAR_M:
            raise ValueError("the side gate's leaf would sweep into the house's front")
    # the fence: from the side gate's pier (T-2455: or a boarded front's south lot line) to
    # the entrance's, and from the entrance's to an end post whose curb stops on the north
    # lot line
    s0 = sb + ps if S else s_south
    if style == "boards":
        H = t["board_height_m"]
        south = _board_run(var, s0, ea - ps, H, "south run")
        north = _board_run(var, eb + ps, n_end, H, "north run")
    else:
        south = var.fence_run(s0, ea - ps, style, "south run", host_a=ps1.name, host_b=pe1.name)
        north = var.fence_run(eb + ps, n_end, style, "north run", host_a=pe2.name)
    # the rule the kit's restriction states, on the built geometry: no curb, rail or picket
    # of a run inside an opening (the pier caps' 50 mm overhang stands above the gate)
    for lo, hi, what in ((ea, eb, "entrance"),) + (((sa, sb, "side passage"),) if S else ()):
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
    W = t.get("wall")
    wv = K.Variant({"id": WALL, "kind": "wall"}, data)
    if W:
        x0 = W["from_u_m"]
        piers = wv.wall_run(x0, line, H=W["height_m"])
        for pc in wv.pieces:
            _to_wall(pc.mesh, -(s_south + wp / 2))

    posts = len(south) + len(north) - (0 if style == "boards" else 3)
    run = {"length_m": round((ea - ps) - s0 + n_end - (eb + ps), 4), "runs": 2, "posts": posts}
    if style == "boards":
        run["height_m"] = t["board_height_m"]
    a.instance(fence, "fence", run, {"line_south": (line, 0.0, -s0), "line_north": (line, 0.0, -n_end)})
    if B:
        boards(a, K, data, B, line, s_north, conf)
    a.instance(GATE, "gate", {"leaves": 2, "clear_m": c, "leaf_m": round(Lw, 4), "swing_reach_m": round(R, 4),
                              "stoop_foot_m": round(foot - D, 4)},
               {"opening": (line, 0.0, -p.stoop_s_m(door.s_m))})
    if S:
        a.instance(GATE, "gate", {"leaves": 1, "clear_m": round(sb - sa, 4)}, {"opening": (line, 0.0, -(sa + sb) / 2)})
    if W:
        a.instance(WALL, "wall", {"length_m": round(line - x0, 4), "height_m": W["height_m"], "piers": len(piers)},
                   {"street_end": (line, 0.0, -(s_south + wp / 2)), "rear_end": (x0, 0.0, -(s_south + wp / 2))})
    _lay(a, [pc for pc in var.pieces if not pc.meta.get("gate")], conf, fence)
    _lay(a, [pc for pc in var.pieces if pc.meta.get("gate")], conf, GATE)
    if W:
        _lay(a, wv.pieces, conf, WALL)
    a.boundary = {"line_x_m": round(line, 4), "stoop_foot_x_m": round(foot, 4), "leaf_reach_m": round(R, 4),
                  "entrance_s_m": [round(ea, 4), round(eb, 4)], "side_gate_s_m": [round(sa, 4), round(sb, 4)] if S else None,
                  "fence_posts_s_m": [round(x, 3) for x in south + north],
                  "wall_piers_x_m": [round(x, 3) for x in wv.meta["piers"]] if W else []}


def _board_run(var, x0, x1, H, tag):
    """A close-boarded run from x0 to x1 in the kit's frame (x along the run, z out of the
    yard): square posts let into the ground at no more than 2.4 m, two arris rails on the
    yard side let into them, and upright boards nailed to the rails' outer face from just
    over grade to the top. Returns the posts' centres along the run."""
    post, rail, bw, bt, gap = 0.1, (0.05, 0.1), 0.14, 0.022, 0.012
    n = max(1, math.ceil((x1 - x0 - post) / 2.4))
    xs = [x0 + post / 2 + (x1 - x0 - post) * i / n for i in range(n + 1)]
    names = [var.member(f"{tag} post {i + 1}", "timber", "ground", x - post / 2, x + post / 2, -0.15, H, -post / 2,
                        post / 2).name for i, x in enumerate(xs)]
    z_face = post / 2 - 0.02                       # the rails' outer face, just inside the posts'
    rails = [var.member(f"{tag} rail {k + 1}", "timber", names[0], x0, x1, y, y + rail[1], z_face - rail[0], z_face)
             for k, y in enumerate((0.3, H - 0.4))]
    m = max(1, round((x1 - x0) / (bw + gap)))
    w = (x1 - x0) / m
    for j in range(m):
        var.member(f"{tag} board {j + 1}", "timber", rails[0].name, x0 + j * w + gap / 2, x0 + (j + 1) * w - gap / 2,
                   0.03, H, z_face, z_face + bt)
    return xs


def boards(a, K, data, B, line, s_north, conf):
    """T-2406: the board fence on 1620's north side, as its 1874 engraving draws it: taking
    over from the lattice on the street line at `from_s_m`, turning at the north lot line and
    running back along it to `to_u_m`."""
    H = B["height_m"]
    front = K.Variant({"id": BOARDS, "kind": "fence"}, data)
    n1 = len(_board_run(front, B["from_s_m"], s_north, H, "street"))
    for pc in front.pieces:
        _to_fence(pc.mesh, line)
    side = K.Variant({"id": BOARDS, "kind": "fence"}, data)
    # the side run's posts stand inside the lot line, its boards on the line's yard side
    n2 = len(_board_run(side, B["to_u_m"], line - 0.06, H, "side"))
    for pc in side.pieces:
        pc.mesh.pos = [(x, y, -(s_north - 0.06) - z) for x, y, z in pc.mesh.pos]
        pc.mesh.nrm = [(x, y, -z) for x, y, z in pc.mesh.nrm]
        pc.mesh.idx = [i for t in zip(pc.mesh.idx[0::3], pc.mesh.idx[2::3], pc.mesh.idx[1::3]) for i in t]
    a.instance(BOARDS, "fence", {"length_m": round((s_north - B["from_s_m"]) + (line - B["to_u_m"]), 4),
                                 "height_m": H, "posts": n1 + n2},
               {"street_end": (line, 0.0, -B["from_s_m"]), "rear_end": (B["to_u_m"], 0.0, -(s_north - 0.06))})
    _lay(a, front.pieces + side.pieces, conf, BOARDS)


# -----------------------------------------------------------------------------------
# T-2447: the front garden — 1637 Prairie's engraving
# -----------------------------------------------------------------------------------

def garden_spec(params, t: dict) -> dict:
    """`layout: front_garden`: one line parallel to the street front, `line_m` before it,
    carrying a brick `wall` from `from_s_m` to `to_s_m` on one side of the stoop and an
    iron `fence` from the stoop's other cheek to `to_s_m`. No gate: the stoop's own flight
    crosses the line between them, and the walk comes up to its foot."""
    if t.get("fence") not in FENCES:
        raise ValueError(f"boundary.fence builds one of {sorted(FENCES)}")
    if FENCES[t["fence"]] == "boards":   # T-2455: boards close a street line, never a garden's
        raise ValueError(f"boundary.fence: a front garden's fence is iron, not {BOARDS!r}")
    if not 2.0 <= t.get("line_m", 0) <= 9.0:
        raise ValueError("boundary.line_m: a front garden's line stands 2-9 m before the street front, clear of its bays")
    s0, s1 = t["lot_s_m"]
    if not s0 <= 0.0 < params.width_m <= s1 + 0.25:
        raise ValueError(f"boundary.lot_s_m {t['lot_s_m']} does not hold the street front 0..{params.width_m}")
    W, F = t["wall"], t["fence_run"]
    if W.get("variant") != WALL:
        raise ValueError(f"boundary.wall builds {WALL!r} alone")
    if not 1.0 <= W["height_m"] <= 2.6:
        raise ValueError(f"boundary.wall.height_m {W['height_m']}: a garden wall stands 1.0-2.6 m")
    for what, run in (("wall", W), ("fence_run", F)):
        a, b = sorted((run["from_s_m"], run["to_s_m"]))
        if a < s0 - 1e-6 or b > s1 + 1e-6:
            raise ValueError(f"boundary.{what} s {a}..{b} leaves the lot {s0}..{s1}")
    top = t.get("fence_rail_top_m")
    if top is not None and not 0.8 <= top <= 2.2:
        raise ValueError(f"boundary.fence_rail_top_m {top}: a top rail stands 0.8-2.2 m over the curb")
    if params.entrance_kit.get("front_yard_m", 0) <= t["line_m"] + 0.5:
        raise ValueError("boundary.line_m: the garden's line stands inside the front yard, short of the walk")
    return t


def garden(a, t):
    """Lay a front garden's wall and fence on the line `line_m` before the street front.
    The wall runs between the kit's brick piers; the fence is the kit's run on its curb, its
    rails raised to `fence_rail_top_m` where the record reads a taller one. Each stops clear
    of the stoop's built cheeks, which the generator reads off K07's mesh."""
    import copy
    p = a.p
    K = _kit()
    data = copy.deepcopy(K.load())
    if t.get("fence_rail_top_m") is not None:
        data["parts"]["rail"]["top_m"] = t["fence_rail_top_m"]
    P = data["parts"]
    conf = p.conf("boundary")
    D = p.depth_m
    line = D + t["line_m"]
    door = next(o for o in p.openings if o.component == "k01.opening.door_leaf" and o.wall == STREET_FRONT)
    stoop = [q for q in a.prim("stoop_stone").pos if q[0] > D + 0.05 and abs(-q[2] - p.stoop_s_m(door.s_m)) < 2.0]
    foot = max(q[0] for q in stoop)
    cheeks = (min(-q[2] for q in stoop), max(-q[2] for q in stoop))
    W, F = t["wall"], t["fence_run"]
    wa, wb = sorted((W["from_s_m"], W["to_s_m"]))
    fa, fb = sorted((F["from_s_m"], F["to_s_m"]))
    for lo, hi, what in ((wa, wb, "wall"), (fa, fb, "fence")):
        if foot > line - 0.5 and lo < cheeks[1] + CLEAR_M and hi > cheeks[0] - CLEAR_M:
            raise ValueError(f"the garden's {what} s {lo:.3f}..{hi:.3f} runs into the stoop, whose cheeks stand at "
                             f"s {cheeks[0]:.3f}..{cheeks[1]:.3f} and whose foot reaches X {foot:.3f} over the line at {line:.3f}")
    wv = K.Variant({"id": WALL, "kind": "wall"}, data)
    piers = wv.wall_run(wa, wb, H=W["height_m"], urns=None if W.get("urns") else ())
    var = K.Variant({"id": t["fence"], "kind": "fence"}, data)
    posts = var.fence_run(fa, fb, FENCES[t["fence"]], "garden run")
    for pc in wv.pieces + var.pieces:
        _to_fence(pc.mesh, line)
    reach = max(q[0] for pc in wv.pieces + var.pieces for q in pc.mesh.pos)
    walk = D + p.entrance_kit["front_yard_m"]
    if reach > walk - CLEAR_M:
        raise ValueError(f"the garden reaches X {reach:.3f}, onto the walk at {walk:.3f}")
    a.instance(WALL, "wall", {"length_m": round(wb - wa, 4), "height_m": W["height_m"], "piers": len(piers)},
               {"end_a": (line, 0.0, -wa), "end_b": (line, 0.0, -wb)})
    a.instance(t["fence"], "fence", {"length_m": round(fb - fa, 4), "runs": 1, "posts": len(posts)},
               {"end_a": (line, 0.0, -fa), "end_b": (line, 0.0, -fb)})
    _lay(a, wv.pieces, conf, WALL)
    _lay(a, var.pieces, conf, t["fence"])
    a.boundary = {"line_x_m": round(line, 4), "stoop_foot_x_m": round(foot, 4),
                  "stoop_cheeks_s_m": [round(c, 4) for c in cheeks],
                  "wall_s_m": [round(wa, 4), round(wb, 4)], "wall_piers_s_m": [round(x, 3) for x in wv.meta["piers"]],
                  "fence_s_m": [round(fa, 4), round(fb, 4)], "fence_posts_s_m": [round(x, 3) for x in posts]}


def stone_boundary(a,t):
    """T-1883: low stone posts and solid rails read in the 1888 Keith plate.

    Both pedestrian passages stay open. No urn piers, iron infill or swinging gate
    is inferred from the later 1965 photograph.
    """
    from .k01_stone_finish import box_faces
    from .k01_frontage import Y
    p=a.p; D=p.depth_m; conf=p.conf("boundary")
    south,north=t["lot_s_m"]; line=D+t["street_line_m"]-.14
    door=next(o for o in p.openings if o.component=="k01.opening.door_leaf" and o.wall==STREET_FRONT)
    centre=p.stoop_s_m(door.s_m); half=t["entrance_clear_m"]/2
    ea,eb=centre-half,centre+half
    seed=a.instance("k11.fence.stone_posts_rails","fence",t,{"street":(line,0,0)})
    pr=a.prim("stoop_stone"); posts=[]
    def box(s0,s1,y0,y1,d0,d1):
        for pts,n in box_faces(s0,s1,y0,y1,d0,d1):
            world=[(line+z,y,-x) for x,y,z in pts]
            a._sface("stoop_stone",world,(n[2],n[1],-n[0]),world[0],(0,0,-1),seed,False,conf)
    for lo,hi in ((.0,ea),(eb,north)):
        n=max(1,round((hi-lo)/2.7)); xs=[lo+.16+(hi-lo-.32)*i/n for i in range(n+1)]
        for x in xs:
            box(x-.16,x+.16,0,t["post_height_m"],-.15,.14)
            box(x-.18,x+.18,t["post_height_m"],t["post_height_m"]+.06,-.17,.14)
        for x0,x1 in zip(xs,xs[1:]):
            box(x0+.16,x1-.16,.05,t["rail_height_m"],-.11,.11)
        posts+=xs
    # Read the stair alone, before the low boundary was laid.
    foot=max(q[0] for q in pr.pos if q[1]>.8 and q[0]>D+.05 and abs(-q[2]-centre)<1.3)
    # The bottom tread remains the flight's true foot even where the curved cheek is low.
    foot=max(foot,D+p.landing_depth_m+(p.risers-1)*p.tread_m)
    a.boundary={"line_x_m":line,"stoop_foot_x_m":round(foot,4),"leaf_reach_m":0,
                "entrance_s_m":[ea,eb],"side_gate_s_m":[south+.1,-.16],
                "fence_posts_s_m":posts,"wall_piers_x_m":[]}
