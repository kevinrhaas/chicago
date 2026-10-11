"""K10 cornice kit laid on a K01 frontage's wall head and ridge (T-2317).

TICKET T-2317: piece 2 of T-1852 (package K10 of the T-1837 Prairie programme). Piece 1,
T-2316, built the cornice kit (`k10_cornices.py` from `data/components/prairie_1904/
k10_cornices.json`) on specimen boards. This module puts the kit's own pieces on a house:
it calls the kit's builders (`console`, `sweep`, `Variant.cresting`) in the assembly's own
frame, so every bracket, moulding and iron bar is the geometry the kit's gate measures,
not a copy of it.

What the record's `wall_head` names, and what is built for it:

  cornice   `k10.cornice.bracketed_timber` under the K05 eave: the kit's scrolled brackets
            at full size, their backs on the wall and their tops under the soffit, and
            between them the kit's bed moulding swept along the wall head. The roof is
            K05's, so its soffit and fascia are the cornice's soffit and crown; K10 adds
            what stands under them. The bed moulding is one section per stretch between
            two brackets, mitred round every corner it crosses and dying into a bracket's
            side at both ends, so all four corners turn and nothing stops in the air.
  cresting  `k10.cresting.iron_ridge` on the main ridge: the kit's posts, bars, scrolls
            and spears, the base bar let into K04's copper ridge roll, on every stretch of
            ridge between the hips' ends and the chimney stacks long enough to carry it.

A WALL HEAD WITH NO ROOM FOR A FRIEZE. The kit's frieze is 0.55 m deep; under 1808's
soffit the third storey's heads stop 0.07 m short of it, so a frieze could only run by
cutting the heads. Brackets therefore stand on the piers between the heads, and the
continuous line is the bed moulding, which clears every head (the generator refuses a
head that would reach it). Where a head, a downpipe or a bay stands, no bracket does, nor
along a stretch the record's `clear_of` names: on 1808 that is the north party wall where
Glessner's south gable leans against it, higher than the brackets' feet.

A generic kit section is allowed here because 1808's own wall head is not read in any
source this project holds (k10_cornices.json `restrictions`: a generic section never
stands in place of a documented one). Glessner's is its own and this module never touches
it.
"""

from __future__ import annotations

import math
import random

CORNICE = "k10.cornice.bracketed_timber"
CRESTING = "k10.cresting.iron_ridge"
ROLE_MATERIAL = {"timber": "fascia", "iron": "iron"}   # the eave's painted timber; the house's iron
HEAD_HORN_M = 0.12      # K01's flat lintel runs this far past each jamb; K03's soldier head less
HEAD_RISE_M = 0.30      # K01's lintel, the deepest head a K01 opening takes
CLEAR_M = 0.03          # a bracket stands this far (along the wall) from a head, a pipe or a bay
STACK_CLEAR_M = 0.25    # the cresting stops this far from a chimney's cap or a hip's end
MIN_CRESTING_M = 1.0    # a stretch of ridge shorter than this carries none


def _kit():
    # imported late: k10_cornices imports k01_frontage's vector helpers, and k01_frontage
    # imports this module, so a top-level import here would be circular
    from . import k10_cornices
    return k10_cornices


def spec(params) -> dict | None:
    """The record's `wall_head`, checked against what this module can build."""
    t = getattr(params, "wall_head", None)
    if not t:
        return None
    if t.get("cornice") not in (None, CORNICE):
        raise ValueError(f"wall_head.cornice builds {CORNICE!r} alone")
    if t.get("cresting") not in (None, CRESTING):
        raise ValueError(f"wall_head.cresting builds {CRESTING!r} alone")
    walls = {r.name: r.L for r in runs(params)}
    for c in t.get("clear_of", []):
        s0, s1 = c["s_m"]
        if c["wall"] not in walls or not 0.0 <= s0 < s1 <= walls[c["wall"]]:
            raise ValueError(f"wall_head.clear_of names {c['wall']} s {s0}..{s1}, not a stretch of a K01 wall")
    return t


def runs(params):
    """The wall head as four kit runs, one per K01 wall, in the walls' own frames: each
    starts at its wall's base socket and runs along its R, so s here is the wall's s."""
    K = _kit()
    D, W = params.depth_m, params.width_m
    return [K.Run("k01.wall.street_front", (D, 0.0), (D, -W), (True, True)),
            K.Run("k01.wall.side.north", (D, -W), (0.0, -W), (True, True)),
            K.Run("k01.wall.rear_service", (0.0, -W), (0.0, 0.0), (True, True)),
            K.Run("k01.wall.side.south", (0.0, 0.0), (D, 0.0), (True, True))]


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


def _blocked(params, run, y_low, bays, half):
    """Where along a run no bracket centre may stand: over a head that reaches y_low, a
    downpipe, or a bay whose roof does; each widened by the bracket's half width."""
    out = []
    for o in params.openings:
        if o.wall == run.name and o.head_m + HEAD_RISE_M > y_low:
            out.append((o.s_m - o.width_m / 2 - HEAD_HORN_M, o.s_m + o.width_m / 2 + HEAD_HORN_M))
    r = params.rainwater or {}
    rp = r.get("pipe_diameter_m", 0.0) / 2
    for x in r.get("downpipes", []):
        if x["wall"] == run.name:
            out.append((x["s_m"] - rp, x["s_m"] + rp))
    for wall, s0, s1, top in bays:
        if wall == run.name and top > y_low:
            out.append((s0, s1))
    # a neighbour's mass the record says stands within the brackets' reach (a party wall)
    out += [tuple(c["s_m"]) for c in spec(params).get("clear_of", []) if c["wall"] == run.name]
    return sorted((a - half - CLEAR_M, b + half + CLEAR_M) for a, b in out)


def bracket_positions(params, run, B, y_low, bays):
    """The kit's rule where the wall allows it: one bracket `corner_m` from every corner on
    both faces, then evenly at no more than `spacing_m` along every pier the heads, pipes
    and bays leave. A stretch too short for two takes one, at its corner end if it has
    one. Raises if a corner bracket has nowhere to stand."""
    c, half = B["corner_m"], B["width_m"] / 2
    blocked = _blocked(params, run, y_low, bays, half)
    for s in (c, run.L - c):
        if any(a < s < b for a, b in blocked):
            raise ValueError(f"{run.name}: no room for the corner bracket at s {s:.3f}")
    free, at = [], c
    for a, b in blocked:
        if b <= at or a >= run.L - c:
            at = max(at, b)
            continue
        if a > at:
            free.append((at, a))
        at = max(at, b)
    if at < run.L - c:
        free.append((at, run.L - c))
    out = []
    for a, b in free:
        if b - a < B["range_spacing_m"][0]:
            out.append(a if abs(a - c) < 1e-9 else (b if abs(b - (run.L - c)) < 1e-9 else (a + b) / 2))
            continue
        n = math.ceil((b - a) / B["spacing_m"])
        out += [a + (b - a) * i / n for i in range(n + 1)]
    return out


def dress(a, bays):
    """Lay the record's wall head on the assembly: brackets and bed moulding under the
    K05 soffit, cresting on the ridge. `bays` is (wall, s0, s1, top) for every K08 bay."""
    p = a.p
    t = spec(p)
    if not t:
        return
    K = _kit()
    data = K.load()
    conf = max(p.conf("wall_head"), p.conf("roof_form"), p.conf("eave_overhang_m"))
    if t.get("cornice"):
        _cornice(a, K, data, bays, conf)
    if t.get("cresting"):
        _cresting(a, K, data, conf)


def _cornice(a, K, data, bays, conf):
    p = a.p
    B = data["parts"]["bracket"]
    bed = [tuple(q) for q in data["parts"]["profiles"]["bed_mould"]["points"]]
    y_s = a.soffit_m                                  # K05's soffit, flat all round
    hb = max(u for _, u in bed)
    y_bed = y_s - hb
    if B["projection_m"] > p.eave_overhang_m - 0.02:
        raise ValueError("the brackets would reach the fascia")
    for o in p.openings:
        if o.head_m + HEAD_RISE_M > y_bed - 0.005:
            raise ValueError(f"the head over {o.wall} s {o.s_m} reaches the bed moulding at {y_bed:.3f} m")
    for wall, s0, s1, top in bays:
        if top > y_bed - 0.005:
            raise ValueError(f"the bay on {wall} reaches the bed moulding at {y_bed:.3f} m")
    w, h = B["width_m"], B["height_m"]
    y_low = y_s - h
    rr = runs(p)
    stations = []                                     # (perimeter s, run index, s)
    start = 0.0
    for i, r in enumerate(rr):
        for s in bracket_positions(p, r, B, y_low, bays):
            stations.append((start + s, i, s))
        start += r.L
    perim = start
    seed = a.instance(CORNICE, "cornice",
                      {"brackets": len(stations), "bracket_height_m": h, "bracket_projection_m": B["projection_m"],
                       "bed_mould": "bed_mould", "soffit_m": y_s},
                      {"soffit": (p.depth_m, y_s, 0.0)})
    var = K.Variant({"id": CORNICE, "kind": "bracketed", "material": "timber"}, data)
    var.seed, var.rng = seed, random.Random(seed)
    for k, (_, i, s) in enumerate(stations):
        pc = var.piece(f"bracket {k + 1}", "timber", "open", bracket={"run": rr[i].name, "s": s})
        K.console(pc.mesh, rr[i], s, y_s, 0.0, w, h, B["projection_m"], B["curl"])
    # the bed moulding: from each bracket's side to the next one's, round every corner
    # between them; open on the wall, on the soffit and at both ends (on the brackets)
    cum = [0.0]
    for r in rr:
        cum.append(cum[-1] + r.L)

    def point(ps):
        ps %= perim
        i = max(j for j in range(4) if cum[j] <= ps + 1e-9)
        return rr[i].at(ps - cum[i], y_bed)

    for k, (ps, _, _) in enumerate(stations):
        nxt = stations[(k + 1) % len(stations)][0] + (perim if k + 1 == len(stations) else 0.0)
        s0, s1 = ps + w / 2, nxt - w / 2
        corners = [c + m * perim for m in (0, 1) for c in cum[:4] if s0 + 1e-6 < c + m * perim < s1 - 1e-6]
        path = [point(s0)] + [point(c) for c in sorted(corners)] + [point(s1)]
        pc = var.piece(f"bed moulding {k + 1}", "timber", "open")
        K.sweep(pc.mesh, path, K.Y, bed, side=1.0, sgn=1.0)
    a.wall_head = {"brackets": [round(s, 3) for s in (st[2] for st in stations)],
                   "bracket_runs": {r.name: [round(st[2], 3) for st in stations if st[1] == i] for i, r in enumerate(rr)},
                   "bed_mould_m": [round(y_bed, 4), round(y_s, 4)]}
    _lay(a, var.pieces, conf, CORNICE)


def _cresting(a, K, data, conf):
    """The kit's cresting on every stretch of the main ridge clear of the stacks."""
    p = a.p
    D, W = p.depth_m, p.width_m
    zr, x0, x1 = -W / 2, W / 2, D - W / 2              # a 45-degree hip's ridge
    stacks = sorted((c["u_m"] - c["plan_m"][0] / 2 - c["cap_proud_m"], c["u_m"] + c["plan_m"][0] / 2 + c["cap_proud_m"])
                    for c in p.chimneys if abs(c["v_m"] - W / 2) < c["plan_m"][1] / 2)
    stretches, at = [], x0
    for s0, s1 in stacks:
        stretches.append((at, s0))
        at = s1
    stretches.append((at, x1))
    # K04's ridge roll, as built: its crown is what the base bar is let into
    roll = [q for q in a.prim("k04_copper_sheet").pos if abs(q[2] - zr) < 0.1 and x0 < q[0] < x1
            and q[1] > p.ridge_m - 0.2 and not any(s0 - 0.1 < q[0] < s1 + 0.1 for s0, s1 in stacks)]
    if not roll:
        raise ValueError("no K04 ridge roll to set the cresting in")
    y_cap = max(q[1] for q in roll)
    laid = []
    for s0, s1 in stretches:
        L = s1 - s0 - 2 * STACK_CLEAR_M
        if L < MIN_CRESTING_M:
            continue
        xc = (s0 + s1) / 2
        seed = a.instance(CRESTING, "cresting", {"length_m": L, "ridge_cap_top_m": y_cap},
                          {"ridge": (xc, y_cap, zr)})
        var = K.Variant(dict(next(v for v in data["variants"] if v["id"] == CRESTING)), data)
        var.seed, var.rng = seed, random.Random(seed)
        posts = var.cresting(xc, L, y_cap, zr, host="k04 ridge roll")
        laid.append({"from_m": round(xc - L / 2, 3), "to_m": round(xc + L / 2, 3), "posts": len(posts)})
        _lay(a, var.pieces, conf, CRESTING)
    if not laid:
        raise ValueError("no stretch of ridge is long enough for the cresting")
    a.cresting = laid
