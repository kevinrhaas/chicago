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
  dormer    `k10.dormer.pedimented_on_bracketed_eave`'s face on the K05 street dormer
            (T-2326): the kit's dormer cornice swept across the face at the foot of the
            pediment and returned on both cheeks under their soffits, capped; and the
            kit's raking cornice, its two stepped bands, on the tympanum under K05's verge.
            The window takes no lintel: the cornice is its head, the kit's
            `window_top_gap_m` above it, as on the kit's own dormer.

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

from .k01_frontage_params import bracketed_section

CORNICE = "k10.cornice.bracketed_timber"
STONE = "k10.cornice.moulded_stone"      # T-2460: 1619's, from its drawing
CRESTING = "k10.cresting.iron_ridge"
DORMER = "k10.dormer.pedimented_on_bracketed_eave"
ROLE_MATERIAL = {"timber": "fascia", "iron": "iron",   # the eave's painted timber; the house's iron
                 "stone": "bay_stone"}                  # T-2460: a bay's stone, whose band the cornice continues
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
    if t.get("cornice") not in (None, CORNICE, STONE):
        raise ValueError(f"wall_head.cornice builds {CORNICE!r} or {STONE!r} alone")
    # T-3002: under a mansard the moulded stone cornice runs round the walls the record names
    # (1801's, under the Taylor photograph's slate faces), one run turned at every corner
    mw = t.get("walls")
    if t.get("cornice") == STONE and getattr(params, "roof_form", "hip") == "mansard":
        if t.get("pairs") or not mw or not _chain(mw):
            raise ValueError(f"{STONE} under a mansard names the walls it runs round (`walls`), each next to "
                             f"the last round the house, and has no brackets to pair")
    elif t.get("cornice") == STONE and (getattr(params, "roof_form", "hip") not in ("flat", "gable") or t.get("pairs")):
        raise ValueError(f"{STONE} runs along the street front between the side walls' parapets, under a "
                         f"flat or gable roof, and has no brackets to pair")
    elif mw is not None:
        raise ValueError(f"wall_head.walls names the walls {STONE!r} runs round under a mansard")
    if t.get("cresting") not in (None, CRESTING):
        raise ValueError(f"wall_head.cresting builds {CRESTING!r} alone")
    if t.get("dormer") not in (None, DORMER):
        raise ValueError(f"wall_head.dormer builds {DORMER!r} alone")
    if t.get("dormer") and not getattr(params, "dormer", None):
        raise ValueError("wall_head.dormer names a dormer face, and the record has no dormer")
    walls = {r.name: r.L for r in runs(params)}
    for c in t.get("clear_of", []):
        s0, s1 = c["s_m"]
        if c["wall"] not in walls or not 0.0 <= s0 < s1 <= walls[c["wall"]]:
            raise ValueError(f"wall_head.clear_of names {c['wall']} s {s0}..{s1}, not a stretch of a K01 wall")
    pr = t.get("pairs")
    if pr is not None and not (isinstance(pr, dict) and 0.6 <= float(pr.get("spacing_m", 0)) <= 2.4):
        raise ValueError("wall_head.pairs names the pairs' spacing_m, 0.6-2.4 m between stations")
    cw = t.get("crown")
    if cw is not None:
        cr = (getattr(params, "mansard", None) or {}).get("crown") or {}
        if cr.get("form") != "hip" or t.get("cornice") != CORNICE or pr is not None:
            raise ValueError(f"wall_head.crown carries {CORNICE!r}, unpaired, round a hipped crown "
                             f"(mansard.crown.form: hip)")
        blk = cw.get("block")
        if blk is not None and not (0.0 < float(blk["at"]) < 1.0 and 0.3 <= float(blk["width_m"]) <= 1.2
                                    and 0.0 <= float(blk["rise_m"]) <= 0.3 and 0.0 <= float(blk["proud_m"]) <= 0.1):
            raise ValueError("wall_head.crown.block: `at` 0-1 along the crown's face, width_m 0.3-1.2, "
                             "rise_m 0-0.3 over the fascia, proud_m 0-0.1 past it")
    st = t.get("stops_m")
    if st is not None and (t.get("cornice") != STONE or not st or set(st) - {"south", "north"}
                           or not all(0.0 < float(x) <= 1.5 for x in st.values())):
        raise ValueError(f"wall_head.stops_m stops {STONE!r} short of the south and/or north corner, "
                         f"0-1.5 m, capped there")
    # T-2680: a stone cornice may stand higher than the eave's soffit, its top lifted to the
    # foot of a stone finish's lattice (1808's crown, where the pictures seat the lattice on it)
    lf = t.get("lift_m")
    if lf is not None and (t.get("cornice") != STONE or not getattr(params, "stone_finish", None)
                           or not 0.0 < float(lf) <= 0.5):
        raise ValueError(f"wall_head.lift_m lifts {STONE!r} under a stone finish's lattice, 0-0.5 m")
    # T-2813: a stone cornice may stand shallower than the kit's section, every member's height
    # scaled to depth_m and its projection kept (1808's, where two photographs read its crown short)
    dp = t.get("depth_m")
    if dp is not None and (t.get("cornice") != STONE or not 0.15 <= float(dp) <= 0.36):
        raise ValueError(f"wall_head.depth_m scales {STONE!r}'s section to 0.15-0.36 m deep (the kit's is 0.36)")
    fz = t.get("frieze")
    # T-3186: and under the moulded stone cornice round a mansard (1901's two pictures), from
    # `height_m` under the cornice's foot up to it
    mansard_stone = t.get("cornice") == STONE and getattr(params, "roof_form", "hip") == "mansard"
    if fz is not None and (t.get("cornice") != CORNICE and not mansard_stone or set(fz) != {"height_m", "proud_m"}
                           or not 0.3 <= float(fz["height_m"]) <= 1.2 or not 0.01 <= float(fz["proud_m"]) <= 0.06):
        raise ValueError(f"wall_head.frieze runs under {CORNICE!r}, or under {STONE!r} round a mansard: "
                         f"height_m 0.3-1.2, proud_m 0.01-0.06")
    # T-3186: stone blocks under the moulded cornice's corona, K10's scrolled console in the
    # walls' stone, at an even spacing along every stretch of the course round a mansard
    bk = t.get("blocks")
    if bk is not None and (not mansard_stone or set(bk) != {"spacing_m", "height_m", "projection_m", "width_m"}
                           or not 0.4 <= float(bk["spacing_m"]) <= 1.6 or not 0.2 <= float(bk["height_m"]) <= 0.8
                           or not 0.08 <= float(bk["width_m"]) <= 0.3 or not 0.1 <= float(bk["projection_m"]) <= 0.4):
        raise ValueError(f"wall_head.blocks stand under {STONE!r} round a mansard: spacing_m 0.4-1.6, "
                         f"height_m 0.2-0.8, width_m 0.08-0.3, projection_m 0.1-0.4")
    # T-3184: the timber cornice's brackets sized off a picture (1834's photograph: deep carved
    # brackets, paired, under a cornice about 1.1 m deep), the kit's shape at the read size
    bm = t.get("bracket_m")
    if bm is not None and (t.get("cornice") != CORNICE or set(bm) != {"height_m", "projection_m", "width_m"}
                           or not 0.3 <= float(bm["height_m"]) <= 1.2 or not 0.08 <= float(bm["width_m"]) <= 0.3
                           or not 0.2 <= float(bm["projection_m"]) <= float(params.eave_overhang_m) - 0.02):
        raise ValueError(f"wall_head.bracket_m sizes {CORNICE!r}'s brackets: height_m 0.3-1.2, width_m 0.08-0.3, "
                         f"projection_m 0.2 m up to 0.02 m short of the eave's overhang")
    paint = t.get("paint")
    if paint is not None and not (len(paint.get("color", ())) == 3 and all(0.0 <= x <= 1.0 for x in paint["color"])):
        raise ValueError("wall_head.paint names the cornice timber's linear colour, three values 0-1")
    return t


#: T-3002: the K01 walls in the order runs() goes round the house
LOOP = ("k01.wall.street_front", "k01.wall.side.north", "k01.wall.rear_service", "k01.wall.side.south")


def _chain(walls):
    """T-3002: `walls` in the order a run round the house meets them, starting where the
    wall before the first is not named; None unless each names a K01 wall once and they are
    one unbroken stretch round the house (all four are the whole ring, opened at the front)."""
    if not walls or len(set(walls)) != len(walls) or set(walls) - set(LOOP):
        return None
    if len(walls) == 4:
        return list(LOOP)
    first = next((w for w in LOOP if w in walls and LOOP[LOOP.index(w) - 1] not in walls), None)
    i = LOOP.index(first)
    out = [LOOP[(i + k) % 4] for k in range(len(walls))]
    return out if set(out) == set(walls) else None


def runs(params):
    """The wall head as four kit runs, one per K01 wall, in the walls' own frames: each
    starts at its wall's base socket and runs along its R, so s here is the wall's s."""
    K = _kit()
    D, W = params.depth_m, params.width_m
    return [K.Run("k01.wall.street_front", (D, 0.0), (D, -W), (True, True)),
            K.Run("k01.wall.side.north", (D, -W), (0.0, -W), (True, True)),
            K.Run("k01.wall.rear_service", (0.0, -W), (0.0, 0.0), (True, True)),
            K.Run("k01.wall.side.south", (0.0, 0.0), (D, 0.0), (True, True))]


def cornice_runs(params):
    """T-3261: runs(), with a canted corner's face (`cant_corner`, 1905's south-west corner
    under the 1893 plate's bracketed cornice) as a run of its own between the two walls it
    cuts, each cut wall's run starting or stopping at the cut. A run carries `s0`, the wall's
    own s at its start, so the wall's openings, pipes and bays still find it."""
    rr = runs(params)
    for r in rr:
        r.s0 = 0.0
    cc = getattr(params, "cant_corner", None) or {}
    if not cc:
        return rr
    from .k01_frontage_params import cant_corner_plan, CANT_WALL
    K = _kit()
    D, W = params.depth_m, params.width_m
    plan = cant_corner_plan(cc, D, W)
    (u0, v0), (u1, v1) = plan["ends"]
    by = {r.name: r for r in rr}
    cant = K.Run(CANT_WALL, (u0, -v0), (u1, -v1), (True, True))
    cant.s0 = 0.0
    if cc["corner"] == "north":   # the front stops at the cut; the north wall starts there
        front, north = by["k01.wall.street_front"], by["k01.wall.side.north"]
        front2 = K.Run(front.name, front.a, (u0, -v0), front.corners)
        north2 = K.Run(north.name, (u1, -v1), (0.0, -W), north.corners)
        front2.s0, north2.s0 = 0.0, plan["walls"][north.name][1]
        return [front2, cant, north2] + rr[2:]
    south, front = by["k01.wall.side.south"], by["k01.wall.street_front"]
    front2 = K.Run(front.name, (u1, -v1), (D, -W), front.corners)
    south2 = K.Run(south.name, south.a, (u0, -v0), south.corners)
    front2.s0, south2.s0 = plan["walls"][front.name][1], 0.0
    return [front2] + rr[1:3] + [south2, cant]


def _lay(a, pieces, conf, cid):
    """Add kit pieces (already in the assembly's frame) to the assembly's primitives."""
    from .k01_frontage import MATERIALS
    tris = 0
    for piece in pieces:
        mat = ROLE_MATERIAL[piece.role]
        fab = a.fabric[mat]          # the slot's fabric on this house (a bay's stone may be its front's)
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


def _blocked(params, run, y_low, bays, half, openings=None):
    """Where along a run no bracket centre may stand: over a head that reaches y_low, a
    downpipe, or a bay whose roof does; each widened by the bracket's half width. `bays` and
    every s here are the wall's own, moved onto the run by its `s0` (T-3261).
    T-3257: `openings` are a rear wing's own, for a run along one of its walls."""
    o0 = getattr(run, "s0", 0.0)
    out = []
    for o in (params.openings if openings is None else openings):
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
    # T-2366: a frieze's lights (k01_arched_front) on the street front, where they reach
    # the brackets' feet: the brackets stand on the piers between them, as in 1612's photograph
    fr = (getattr(params, "arched_front", None) or {}).get("frieze") or {}
    if fr and run.name == "k01.wall.street_front" and fr["sill_m"] + fr["height_m"] > y_low:
        out += [(s - fr["width_m"] / 2, s + fr["width_m"] / 2) for s in fr["s_m"]]
    # a neighbour's mass the record says stands within the brackets' reach (a party wall)
    out += [tuple(c["s_m"]) for c in spec(params).get("clear_of", []) if c["wall"] == run.name]
    return sorted((a - o0 - half - CLEAR_M, b - o0 + half + CLEAR_M) for a, b in out)


def pair_offsets(B) -> list:
    """T-2369: a pair's two brackets about its station, the kit's `pair_gap_m` apart."""
    d = B["pair_gap_m"] / 2 + B["width_m"] / 2
    return [-d, d]


def bracket_positions(params, run, B, y_low, bays, openings=None):
    """The kit's rule where the wall allows it: one bracket `corner_m` from every corner on
    both faces, then evenly at no more than `spacing_m` along every pier the heads, pipes
    and bays leave. A stretch too short for two takes one, at its corner end if it has
    one. Raises if a corner bracket has nowhere to stand.

    T-2369: a record whose `wall_head.pairs` names its brackets paired (1612's photograph)
    stands a pair, the kit's `pair_gap_m` apart, at each station, the stations evenly at no
    more than `pairs.spacing_m` along a stretch, and a stretch shorter than that takes one
    pair, at its corner end if it has one."""
    pairs = (spec(params) or {}).get("pairs")
    c = B["corner_m"]
    half = B["pair_gap_m"] / 2 + B["width_m"] if pairs else B["width_m"] / 2
    spacing, short = (pairs["spacing_m"], pairs["spacing_m"]) if pairs else (B["spacing_m"], B["range_spacing_m"][0])
    if pairs:
        c = max(c, half + 0.02)
    blocked = _blocked(params, run, y_low, bays, half, openings)
    # T-2404: a pavilion standing flush with the corner takes the corner itself, so that
    # corner has no bracket on this face (the pavilion's own eaves turn it)
    o0 = getattr(run, "s0", 0.0)   # T-3261: a run cut short by a canted corner
    held = [s for s in (c, run.L - c)
            if any(w == run.name and top > y_low and s0 - o0 < s < s1 - o0 and (s0 - o0 <= 1e-6 or s1 - o0 >= run.L - 1e-6)
                   for w, s0, s1, top in bays)]
    for s in (c, run.L - c):
        if s in held:
            continue
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
        if b - a < short:
            out.append(a if abs(a - c) < 1e-9 else (b if abs(b - (run.L - c)) < 1e-9 else (a + b) / 2))
            continue
        n = math.ceil((b - a) / spacing)
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
    if t.get("cornice") == STONE and p.roof_form == "mansard":
        _mansard_cornice(a, K, data, bays, conf)
    elif t.get("cornice") == STONE:
        _stone_cornice(a, K, data, bays, conf)
    elif t.get("cornice"):
        _cornice(a, K, data, bays, conf)
    if t.get("cresting"):
        _cresting(a, K, data, conf)
    if t.get("dormer"):
        _dormer(a, K, data, max(conf, p.conf("dormer")))


def dresses_dormer(params) -> bool:
    """Whether the record dresses its dormer's face from the kit (K01 then draws no
    lintel over the dormer's sash: the kit's cornice is its head)."""
    return bool((getattr(params, "wall_head", None) or {}).get("dormer"))


def dormer_fit(params, data) -> dict:
    """The K05 dormer's face heights against the kit's pediment cornice. The cornice's
    top is the cheeks' soffit (where it is returned), so the sash's head has to stand
    the cornice's depth and the kit's window gap under that soffit. Raises if not."""
    from . import k05_roofs as k5
    d, Dm = params.dormer, data["parts"]["dormer"]
    dp = k5.load()["parts"]["dormer"]
    dt = math.tan(math.radians(d["pitch_deg"]))
    hc = max(u for _, u in data["parts"]["profiles"]["dormer_cornice"]["points"])
    soffit = d["face_height_m"] - dp["overhang_m"] * dt - dp["fascia_depth_m"]   # above the face's foot
    head = d["sash"]["sill_m"] + d["sash"]["height_m"]
    room = soffit - hc - head
    if room < Dm["window_top_gap_m"] - 1e-9:
        raise ValueError(f"the dormer's sash head stands {soffit - head:.3f} m under its cheek soffit; the kit's "
                         f"pediment cornice ({hc} m) and window gap ({Dm['window_top_gap_m']} m) need "
                         f"{hc + Dm['window_top_gap_m']:.3f} m")
    return {"soffit_m": soffit, "cornice_m": hc, "head_gap_m": room}


def _dormer(a, K, data, conf):
    """The kit's pedimented dormer face on the K05 dormer, built as the kit builds its
    specimen's (`Variant._dormer`) in the face's own frame — x across the face, y up, z
    out of it, the face at z = 0 — and turned onto the house: z is the assembly's +x."""
    p, g = a.p, a.dormer_geom
    d, Dm = p.dormer, data["parts"]["dormer"]
    fit = dormer_fit(p, data)
    corn = [tuple(q) for q in data["parts"]["profiles"]["dormer_cornice"]["points"]]
    hc, pj = fit["cornice_m"], max(n for n, _ in corn)
    wd, dt, o, v = d["width_m"], g["dt"], g["overhang"], d["verge_m"]
    hs, rt = g["dhs"], Dm["return_m"]
    if pj > o - 0.01:
        raise ValueError("the dormer cornice's return would reach past its cheek's soffit")
    if rt > g["xf"] - g["back"]:
        raise ValueError("the dormer cornice's return is longer than its cheek")
    if Dm["rake_bands"][0]["proud_m"] > v - 0.01:
        raise ValueError("the raking cornice would stand proud of K05's verge")
    seed = a.instance(DORMER, "cornice", {"face_width_m": wd, "cornice_m": hc, "projection_m": pj,
                                          "return_m": rt, "pitch_deg": d["pitch_deg"],
                                          "rake_bands": len(Dm["rake_bands"]),
                                          "head_gap_m": fit["head_gap_m"]},
                      {"eave": (g["xf"], hs, (g["zs"] + g["zn"]) / 2)})
    var = K.Variant({"id": DORMER, "kind": "dormer", "material": "timber"}, data)
    var.seed, var.rng = seed, random.Random(seed)
    # the horizontal cornice: across the face at the pediment's foot, returned along both
    # cheeks and capped. Under the cheeks' soffit its top is open (it lies on the soffit);
    # in front of the face, where only the verge's raking soffit is above it, it is closed
    druns = [K.Run("dormer left", (-wd / 2, -rt), (-wd / 2, 0.0), (False, True)),
             K.Run("dormer front", (-wd / 2, 0.0), (wd / 2, 0.0), (True, True)),
             K.Run("dormer right", (wd / 2, 0.0), (wd / 2, -rt), (True, False))]
    path = [druns[0].at(0.0, hs - hc)] + [r.at(r.L, hs - hc) for r in druns]
    c = var.piece("dormer cornice", "timber", "open", run_names=[r.name for r in druns])
    K.sweep(c.mesh, path, K.Y, corn[:-1], side=1.0, caps=(True, True), cap_close=[corn[-1]])
    top = var.piece("dormer cornice top", "timber", "open")
    top.mesh.poly([(-wd / 2 - pj, hs, 0.0), (-wd / 2 - pj, hs, pj), (wd / 2 + pj, hs, pj), (wd / 2 + pj, hs, 0.0)], K.Y)
    # the raking cornice: the kit's stepped bands on the tympanum, the first under K05's
    # raking soffit (whose line runs from the cheeks' soffit at the overhang to the apex),
    # each standing on the cornice's top and stopped square where that top ends
    cq = math.sqrt(1 + dt * dt)
    apex = hs + (wd / 2 + o) * dt
    xe = wd / 2 + pj
    off = 0.0
    for i, band in enumerate(Dm["rake_bands"]):
        yo, yi = apex - off * cq, apex - (off + band["width_m"]) * cq
        xo, xi = (yo - hs) / dt, (yi - hs) / dt
        if xi <= 0.0:
            raise ValueError("the raking cornice's bands meet below the pediment's apex")
        if xo > xe:      # stopped square over the cornice's end, its end face closed
            ye = hs + (xo - xe) * dt
            poly = [(-xe, hs), (-xe, ye), (0.0, yo), (xe, ye), (xe, hs), (xi, hs), (0.0, yi), (-xi, hs)]
            opened = {1, 2, 4, 7}
        else:
            poly = [(-xo, hs), (0.0, yo), (xo, hs), (xi, hs), (0.0, yi), (-xi, hs)]
            opened = {0, 1, 2, 5}
        pc = var.piece(f"rake {'crown' if i == 0 else 'fascia'}", "timber", "open")
        K.prism(pc.mesh, poly, 0.0, band["proud_m"], open_edges=opened)
        off += band["width_m"]
    # onto the house: the face's x runs north (-z), its z out along the assembly's +x
    xf, zc = g["xf"], (g["zs"] + g["zn"]) / 2
    for pc in var.pieces:
        m = pc.mesh
        m.pos = [(xf + q[2], q[1], zc - q[0]) for q in m.pos]
        m.nrm = [(n[2], n[1], -n[0]) for n in m.nrm]
    a.dormer_face = {"cornice_m": [round(hs - hc, 4), round(hs, 4)], "projection_m": pj, "return_m": rt,
                     "head_gap_m": round(fit["head_gap_m"], 4),
                     "rake_bands": [b["width_m"] for b in Dm["rake_bands"]]}
    _lay(a, var.pieces, conf, DORMER)


def _cornice(a, K, data, bays, conf):
    p = a.p
    B = dict(data["parts"]["bracket"], **{k: float(x) for k, x in (p.wall_head.get("bracket_m") or {}).items()})   # T-3184
    bed = [tuple(q) for q in data["parts"]["profiles"]["bed_mould"]["points"]]
    y_s = a.soffit_m                                  # K05's soffit, flat all round
    hb = max(u for _, u in bed)
    y_bed = y_s - hb
    if B["projection_m"] > p.eave_overhang_m - 0.02:
        raise ValueError("the brackets would reach the fascia")
    for o in p.openings:
        if o.head_m + HEAD_RISE_M > y_bed - 0.005:
            raise ValueError(f"the head over {o.wall} s {o.s_m} reaches the bed moulding at {y_bed:.3f} m")
    # T-2465: a pavilion under a crown is carried up to the crown's own cornice, through
    # the line of the bed moulding, which runs into its cheeks; its brackets stand clear
    cr = (getattr(p, "mansard", None) or {}).get("crown") or {}
    # T-2472: a bay carrying the cornice's own section as its eaves (k01_frontage_params'
    # `eaves.cornice`) rises to the bed moulding's foot and carries it round its plan, under
    # the house's soffit and fascia; the wall's bed moulding stops at its junctions
    sec = [tuple(q) for q in bracketed_section(data, p.eave_overhang_m)]
    cut = []
    # T-2787: a tower rises past the eave, so the bed moulding stops at its junctions and
    # dies into its ring, on whichever wall it stands (a cut is perimeter s: the street
    # front's run starts the perimeter, then north, rear and south, as `runs` lays them)
    at_run, acc = {}, 0.0
    for r in cornice_runs(p):   # T-3261: a wall's own s at a run's start is its s0
        at_run[r.name], acc = acc - r.s0, acc + r.L
    for b, (wall, s0, s1, top) in zip(p.bays, bays):
        if b.get("wing"):   # T-2842: a tower on a rear wing's wall is clear of the main wall head
            continue
        if b["variant"]["kind"] == "tower":
            cut.append(tuple(at_run[wall] + s for s in b["span_m"]))
            continue
        if cr.get("form") == "hip" and wall == "k01.wall.street_front" \
                and -cr["z1"] - cr["overhang_m"] <= s0 and s1 <= -cr["z0"] + cr["overhang_m"]:
            continue
        ev = b["variant"].get("overrides", {}).get("eaves", {})
        if [tuple(q) for q in ev.get("profile", ())] == sec:
            wall_top = math.fsum(st["height_m"] for st in b["variant"]["storeys"])
            # T-2964: on any wall (1816's south flank bay, carried up into its own mansard), its
            # cut at that wall's perimeter s, as a tower's is
            if b["variant"].get("base") != "grade" or abs(wall_top - y_bed) > 0.001:
                raise ValueError(f"the bay {b['id']} carries the cornice's section; it rises from grade "
                                 f"to the bed moulding's foot at {y_bed:.3f} m (has {wall_top:.3f})")
            cut.append(tuple(at_run[wall] + s for s in b["span_m"]))
            continue
        if b.get("through_eave"):
            # T-2778: an oriel carried up through the eave; the bed moulding dies into its
            # cants at its junctions, and its brackets stand clear of it (_blocked)
            cut.append(tuple(b["span_m"]))
            continue
        if top > y_bed - 0.005:
            raise ValueError(f"the bay on {wall} reaches the bed moulding at {y_bed:.3f} m")
    # T-2995: a mansard on some walls only: the straight walls' head carries no eave box, so no
    # bracket and no bed moulding (k01_mansard_straight.perimeter_span)
    straight = (getattr(p, "mansard", None) or {}).get("straight")
    if straight:
        from .k01_mansard_straight import perimeter_span
        cut.append(perimeter_span(p))
    w, h = B["width_m"], B["height_m"]
    y_low = y_s - h
    # T-2350: under a flat roof the cornice is the street front's alone — its box ends flush
    # with the side walls, which rise into coped parapets (party walls, in a row) — so the
    # brackets and the bed moulding run along that one wall, corner to corner, and stop
    # T-2459: and so under a gable whose side walls are carried up as parapets (1619's)
    flat = getattr(p, "roof_form", "hip") in ("flat", "gable")
    rr = runs(p)[:1] if flat else cornice_runs(p)
    stations = []                                     # (perimeter s, run index, s)
    start = 0.0
    for i, r in enumerate(rr):
        for s in bracket_positions(p, r, B, y_low, bays):
            stations.append((start + s, i, s))
        start += r.L
    perim = start
    if straight:
        c0, c1 = perimeter_span(p)
        stations = [st for st in stations if not c0 - w / 2 - 0.05 <= st[0] <= c1 + w / 2 + 0.05]
    crown = _crown_stations(p, B, cr, spec(p).get("crown"))
    seed = a.instance(CORNICE, "cornice",
                      {"brackets": len(stations) * (2 if spec(p).get("pairs") else 1),
                       **({"crown_brackets": len(crown["stations"])} if crown else {}),
                       **({"paired": True} if spec(p).get("pairs") else {}),
                       "bracket_height_m": h, "bracket_projection_m": B["projection_m"],
                       "bed_mould": "bed_mould", "soffit_m": y_s},
                      {"soffit": (p.depth_m, y_s, 0.0)})
    var = K.Variant({"id": CORNICE, "kind": "bracketed", "material": "timber"}, data)
    var.seed, var.rng = seed, random.Random(seed)
    paired = bool(spec(p).get("pairs"))
    offs = pair_offsets(B) if paired else [0.0]
    k = 0
    for _, i, s in stations:
        for d in offs:
            k += 1
            pc = var.piece(f"bracket {k}", "timber", "open", bracket={"run": rr[i].name, "s": s + d})
            K.console(pc.mesh, rr[i], s + d, y_s, 0.0, w, h, B["projection_m"], B["curl"])
    # the bed moulding runs between the stations' outer brackets
    w = 2 * (offs[-1] + w / 2)
    # the bed moulding: from each bracket's side to the next one's, round every corner
    # between them; open on the wall, on the soffit and at both ends (on the brackets)
    cum = [0.0]
    for r in rr:
        cum.append(cum[-1] + r.L)

    def point(ps):
        ps = min(ps, perim) if flat else ps % perim
        i = max(j for j in range(len(rr)) if cum[j] <= ps + 1e-9)
        return rr[i].at(ps - cum[i], y_bed)

    spans = []
    for k, (ps, _, _) in enumerate(stations):
        if flat and k + 1 == len(stations):
            break
        nxt = stations[(k + 1) % len(stations)][0] + (perim if k + 1 == len(stations) else 0.0)
        spans.append((ps + w / 2, nxt - w / 2))
    if flat:
        spans = [(0.0, stations[0][0] - w / 2)] + spans + [(stations[-1][0] + w / 2, perim)]
    # the street front starts the perimeter; the span that closes it runs on past `perim`
    for c0, c1 in [(c0 + m, c1 + m) for c0, c1 in cut for m in (0.0, perim)]:
        spans = [q for s0, s1 in spans for q in ((s0, min(s1, c0)), (max(s0, c1), s1)) if q[1] - q[0] > 1e-6]
    for k, (s0, s1) in enumerate(spans):
        corners = [c + m * perim for m in (0, 1) for c in cum[:len(rr)] if s0 + 1e-6 < c + m * perim < s1 - 1e-6]
        path = [point(s0)] + [point(c) for c in sorted(corners)] + [point(s1)]
        pc = var.piece(f"bed moulding {k + 1}", "timber", "open")
        K.sweep(pc.mesh, path, K.Y, bed, side=1.0, sgn=1.0)
    # T-3184: a plain frieze read off a picture (1834's photograph), from `height_m` under the
    # soffit up to the bed moulding, `proud_m` before the wall and swept round every corner
    # behind the brackets, in the cornice's painted timber; the heads stand clear under it
    fz = spec(p).get("frieze")
    if fz:
        y_f = y_s - float(fz["height_m"])
        for o in p.openings:
            if o.head_m + HEAD_RISE_M > y_f - 0.005 and o.wall in {r.name for r in rr}:
                raise ValueError(f"wall_head.frieze: the head over {o.wall} s {o.s_m} reaches the frieze at {y_f:.3f} m")
        fp = float(fz["proud_m"])
        prof = [(0.0, 0.0), (fp, 0.0), (fp, y_bed - y_f)]
        fspans = [(0.0, perim)]
        for c0, c1 in [(c0 + m, c1 + m) for c0, c1 in cut for m in (0.0, perim)]:
            fspans = [q for s0, s1 in fspans for q in ((s0, min(s1, c0)), (max(s0, c1), s1)) if q[1] - q[0] > 1e-6]

        def fpoint(ps):
            ps = min(ps, perim) if flat else (ps if abs(ps - perim) < 1e-9 else ps % perim)
            i = max(j for j in range(len(rr)) if cum[j] <= ps + 1e-9 and j < len(rr))
            return rr[i].at(ps - cum[i], y_f)
        for k, (s0, s1) in enumerate(fspans):
            corners = [c + m * perim for m in (0, 1) for c in cum[:len(rr)] if s0 + 1e-6 < c + m * perim < s1 - 1e-6]
            path = [fpoint(s0)] + [fpoint(c) for c in sorted(corners)] + [fpoint(s1)]
            pc = var.piece(f"frieze {k + 1}", "timber", "open")
            K.sweep(pc.mesh, path, K.Y, prof, side=1.0, sgn=1.0)
    if crown:
        _crown_cornice(a, K, var, B, bed, y_s, y_bed, crown)
    a.wall_head = {"brackets": [round(s, 3) for s in (st[2] for st in stations)], "paired": paired,
                   **({"crown": {"brackets": {r.name: [round(s, 3) for i, s in crown["stations"] if crown["runs"][i] is r]
                                              for r in crown["runs"]},
                                 **({"block": crown["block_box"]} if crown.get("block_box") else {})}} if crown else {}),
                   "bracket_runs": {r.name: [round(st[2] + getattr(r, "s0", 0.0), 3) for st in stations if st[1] == i]
                                    for i, r in enumerate(rr)},
                   "bed_mould_m": [round(y_bed, 4), round(y_s, 4)]}
    _lay(a, var.pieces, conf, CORNICE)


def wing_runs(w):
    """T-3257: a flat rear wing's wall head as three kit runs — its north, rear and south
    walls, in that order round it, each from its wall's own origin (`wing_walls`), so s here
    is the wall's s. The chain is open at the host wall at both ends."""
    K = _kit()
    u0, u1, v0, v1 = w["rect"]
    wid = w["id"]
    return [K.Run(f"k01.wall.wing.{wid}.north", (u1, -v1), (u0, -v1), (False, True)),
            K.Run(f"k01.wall.wing.{wid}.rear", (u0, -v1), (u0, -v0), (True, True)),
            K.Run(f"k01.wall.wing.{wid}.south", (u0, -v0), (u1, -v0), (True, False))]


def dress_wings(a, bays):
    """T-3257: the house's bracketed timber cornice carried round a flat rear wing that names
    it (rear_wings[].roof.cornice; 1701's 1874 range, its rear photograph): the kit's brackets,
    paired as the house's are, under the wing deck's soffit on its three walls, and the bed
    moulding swept between them round both corners and dying into the host wall at each end.
    A bay on a wing wall that reaches the bed moulding (1701's oriel, its crest under the
    cornice) stops the moulding at its sides, and no bracket stands over it."""
    p = a.p
    wings = [w for w in p.rear_wings if w["roof"]["kind"] == "flat" and w.get("cornice")]
    if not wings:
        return
    if (spec(p) or {}).get("cornice") != CORNICE:
        raise ValueError(f"{wings[0]['id']} carries {CORNICE!r} round its deck, and the house's wall head does not")
    K = _kit()
    data = K.load()
    B = dict(data["parts"]["bracket"], **{k: float(x) for k, x in ((p.wall_head or {}).get("bracket_m") or {}).items()})
    bed = [tuple(q) for q in data["parts"]["profiles"]["bed_mould"]["points"]]
    hb = max(u for _, u in bed)
    paired = bool((spec(p) or {}).get("pairs"))
    offs = pair_offsets(B) if paired else [0.0]
    conf = max(p.conf("rear_wings"), p.conf("wall_head"))
    for w in wings:
        y_s = w["top_m"]
        y_bed, y_low = y_s - hb, y_s - B["height_m"]
        if B["projection_m"] > w["overhang_m"] - 0.02:
            raise ValueError(f"{w['id']}: the cornice's brackets would reach its deck's fascia")
        for o in w["openings"]:
            if o.head_m + HEAD_RISE_M > y_bed - 0.005:
                raise ValueError(f"{w['id']}: the head over {o.wall} s {o.s_m} reaches the bed moulding at {y_bed:.3f} m")
        rr = wing_runs(w)
        stations, cuts, start = [], [], 0.0
        for i, r in enumerate(rr):
            for s in bracket_positions(p, r, B, y_low, bays, w["openings"]):
                stations.append((start + s, i, s))
            cuts += [(start + s0, start + s1) for wall, s0, s1, top in bays if wall == r.name and top > y_bed - 0.005]
            start += r.L
        perim = start
        seed = a.instance(CORNICE, "cornice",
                          {"wing": w["id"], "brackets": len(stations) * len(offs), **({"paired": True} if paired else {}),
                           "bracket_height_m": B["height_m"], "bracket_projection_m": B["projection_m"],
                           "bed_mould": "bed_mould", "soffit_m": y_s},
                          {"soffit": (w["rect"][0], y_s, -w["rect"][2])})
        var = K.Variant({"id": CORNICE, "kind": "bracketed", "material": "timber"}, data)
        var.seed, var.rng = seed, random.Random(seed)
        k = 0
        for _, i, s in stations:
            for d in offs:
                k += 1
                pc = var.piece(f"wing bracket {k}", "timber", "open", bracket={"run": rr[i].name, "s": s + d})
                K.console(pc.mesh, rr[i], s + d, y_s, 0.0, B["width_m"], B["height_m"], B["projection_m"], B["curl"])
        bw = 2 * (offs[-1] + B["width_m"] / 2)
        cum = [0.0]
        for r in rr:
            cum.append(cum[-1] + r.L)

        def point(ps):
            ps = min(max(ps, 0.0), perim)
            i = max(j for j in range(len(rr)) if cum[j] <= ps + 1e-9)
            i = min(i, len(rr) - 1)
            return rr[i].at(ps - cum[i], y_bed)

        edges = [0.0] + [x for st in stations for x in (st[0] - bw / 2, st[0] + bw / 2)] + [perim]
        spans = [(edges[j], edges[j + 1]) for j in range(0, len(edges), 2)]
        for c0, c1 in cuts:
            spans = [q for s0, s1 in spans for q in ((s0, min(s1, c0)), (max(s0, c1), s1)) if q[1] - q[0] > 1e-6]
        for j, (s0, s1) in enumerate(spans):
            corners = [c for c in cum[1:len(rr)] if s0 + 1e-6 < c < s1 - 1e-6]
            path = [point(s0)] + [point(c) for c in corners] + [point(s1)]
            pc = var.piece(f"wing bed moulding {j + 1}", "timber", "open")
            K.sweep(pc.mesh, path, K.Y, bed, side=1.0, sgn=1.0)
        _lay(a, var.pieces, conf, CORNICE)


def _crown_stations(p, B, cr, c):
    """T-2467: the bracketed cornice carried round a hipped crown's pavilion — 1637's wing,
    whose engraving draws its cornice as a band as deep as the main one's with a block in it
    over the window, where T-2465's crown carried K05's fascia alone. The pavilion's walls
    rise into the crown's soffit, so the house's own brackets and bed moulding run round its
    three faces on the main wall head's line: its cheek off the street front, its face and
    its far cheek. A cheek that leaves the street front starts at an inside corner, so its
    brackets stand clear of the front's (by the brackets' projection); a cheek flush with a
    side wall runs on into that wall's run, whose corner bracket closes its spacing. The
    record's `block` stands over the window, `at` along the face, its back on the wall, from
    the brackets' feet through the crown's fascia to `rise_m` over it, `proud_m` past it.
    Returns None where the record asks for none of this."""
    if not c or cr.get("form") != "hip":
        return None
    K = _kit()
    D, W = p.depth_m, p.width_m
    x1, za, zb = cr["x1"], cr["z1"], cr["z0"]
    rr = [K.Run("k10.crown.cheek_a", (D, za), (x1, za), (False, True)),
          K.Run("k10.crown.face", (x1, za), (x1, zb), (True, True)),
          K.Run("k10.crown.cheek_b", (x1, zb), (D, zb), (True, False))]
    flush = (abs(za) < 1e-6, abs(zb + W) < 1e-6)      # a cheek on a side wall's plane
    w, cc, sp = B["width_m"], B["corner_m"], B["spacing_m"]
    inside = B["projection_m"] + w / 2 + CLEAR_M      # clear of the street front's brackets

    def even(a_, b_, drop_last=False):
        n = max(1, math.ceil((b_ - a_) / sp - 1e-9))
        out = [a_ + (b_ - a_) * i / n for i in range(n + 1)]
        return out[:-1] if drop_last else out

    out = []
    # the cheeks: from the outside corner to the street front, or on into the side wall's run
    for i, f, corner_first in ((0, flush[0], False), (2, flush[1], True)):
        L = rr[i].L
        if f:   # the side run's corner bracket stands `cc` past this cheek's street end
            ss = even(cc, L + cc, drop_last=True) if corner_first else [L - s for s in even(cc, L + cc, True)]
        else:
            lo, hi = (cc, L - inside) if corner_first else (inside, L - cc)
            if hi - lo < 0:
                raise ValueError(f"{rr[i].name}: {L:.2f} m leaves no room for a bracket clear of the front's")
            # a stretch too short for two takes one, at its outside corner
            ss = even(lo, hi) if hi - lo >= B["range_spacing_m"][0] else [lo if corner_first else hi]
        out += [(i, s) for s in ss]
    # the face: a bracket `cc` from each corner, evenly between, and none where the block stands
    L = rr[1].L
    blk = c.get("block")
    free = [(cc, L - cc)]
    box = None
    if blk:
        bw = float(blk["width_m"])
        s0 = float(blk["at"]) * L - bw / 2
        box = (s0, s0 + bw)
        free = [(cc, s0 - w / 2 - CLEAR_M), (s0 + bw + w / 2 + CLEAR_M, L - cc)]
        if free[0][1] < cc or free[1][0] > L - cc:
            raise ValueError(f"wall_head.crown.block: {bw} m at {blk['at']} leaves no corner bracket room")
    for a_, b_ in free:
        out += [(1, s) for s in even(a_, b_)]
    return {"runs": rr, "stations": [(i, s) for i, s in out], "block": blk, "box": box,
            "overhang_m": cr["overhang_m"]}


def _crown_cornice(a, K, var, B, bed, y_s, y_bed, crown):
    """T-2467: lay `_crown_stations`' brackets, the bed moulding between them round the
    crown's three faces (mitred at its two outside corners, dying into each bracket's side
    and the block's), and the block."""
    p = a.p
    rr, w, h = crown["runs"], B["width_m"], B["height_m"]
    for k, (i, s) in enumerate(crown["stations"]):
        pc = var.piece(f"crown bracket {k + 1}", "timber", "open", bracket={"run": rr[i].name, "s": s})
        K.console(pc.mesh, rr[i], s, y_s, 0.0, w, h, B["projection_m"], B["curl"])
    cum = [0.0]
    for r in rr:
        cum.append(cum[-1] + r.L)
    stops = sorted((cum[i] + s - w / 2, cum[i] + s + w / 2) for i, s in crown["stations"])
    if crown["box"]:
        stops = sorted(stops + [(cum[1] + crown["box"][0], cum[1] + crown["box"][1])])

    def point(ps):
        i = max(j for j in range(len(rr)) if cum[j] <= ps + 1e-9)
        return rr[i].at(ps - cum[i], y_bed)

    edges = [0.0] + [q for st in stops for q in st] + [cum[-1]]
    for k in range(0, len(edges), 2):
        s0, s1 = edges[k], edges[k + 1]
        if s1 - s0 < 1e-6:
            continue
        path = [point(s0)] + [point(c) for c in cum[1:-1] if s0 + 1e-6 < c < s1 - 1e-6] + [point(s1)]
        pc = var.piece(f"crown bed moulding {k // 2 + 1}", "timber", "open")
        K.sweep(pc.mesh, path, K.Y, bed, side=1.0, sgn=1.0)
    if crown["box"]:
        blk = crown["block"]
        s0, s1 = crown["box"]
        y0, y1 = y_s - h, p.eave_m + float(blk["rise_m"])
        n1 = crown["overhang_m"] + float(blk["proud_m"])
        pc = var.piece("crown block", "timber", "open")
        K.face_box(pc.mesh, rr[1], s0, s1, y0, y1, 0.0, n1, skip=("back",))
        crown["block_box"] = {"s_m": [round(s0, 3), round(s1, 3)], "y_m": [round(y0, 4), round(y1, 4)],
                              "proud_m": round(n1, 3)}


def _stone_cornice(a, K, data, bays, conf):
    """T-2460: the kit's moulded stone cornice along the street front, its top the K05
    soffit, in place of brackets and a bed moulding: corner to corner, as the bracketed one
    runs under a flat or gable roof whose side walls rise into parapets, and capped at both
    corners. A K08 bay that rises to it carries the same section as its own eaves (its wall
    top at the cornice's foot, k01_frontage_params' `eaves.cornice`), so the bay's cornice
    continues the wall's: the wall's stops at the bay's junctions and dies into it there.
    `bays` is (wall, s0, s1, top) for every K08 bay, in the record's order."""
    p = a.p
    v = next(x for x in data["variants"] if x["id"] == STONE)
    prof = [tuple(q) for q in data["parts"]["profiles"][v["profile"]]["points"]]
    pj, ch = max(n for n, _ in prof), max(u for _, u in prof)
    if p.wall_head.get("depth_m"):                  # T-2813: the section scaled in height alone
        k = float(p.wall_head["depth_m"]) / ch
        prof, ch = [(n, u * k) for n, u in prof], ch * k
    y_s = a.soffit_m + float(p.wall_head.get("lift_m", 0.0))
    y_c = y_s - ch
    front = runs(p)[0]
    if pj > p.eave_overhang_m - 0.02:
        raise ValueError("the stone cornice would reach the eave's fascia")
    for o in p.openings:
        if o.wall == front.name and o.head_m + HEAD_RISE_M > y_c - 0.005:
            raise ValueError(f"the head over {o.wall} s {o.s_m} reaches the stone cornice at {y_c:.3f} m")
    cut = []
    for b, (wall, s0, s1, top) in zip(p.bays, bays):
        if wall != front.name or top <= y_c - 0.005:
            continue
        if b["variant"]["kind"] == "tower":   # T-2787: the course dies into a tower's ring
            cut.append(tuple(b["span_m"]))
            continue
        if b.get("through_eave"):   # T-2542: and into the cants of an oriel carried through the eave
            cut.append(tuple(b["span_m"]))
            continue
        ev = b["variant"].get("overrides", {}).get("eaves", {})
        wall_top = b["variant"].get("base", 0.0) if b["variant"].get("base") != "grade" else 0.0
        wall_top += math.fsum(st["height_m"] for st in b["variant"]["storeys"])
        if [tuple(q) for q in ev.get("profile", ())] != prof or abs(wall_top - y_c) > 0.001:
            raise ValueError(f"the bay {b['id']} reaches the stone cornice at {y_c:.3f} m; it rises to it only "
                             f"carrying its section (eaves.cornice), its wall top at {y_c:.3f} m (has {wall_top:.3f})")
        cut.append(tuple(b["span_m"]))
    spans, at = [], 0.0
    for c0, c1 in sorted(cut):
        spans.append((at, c0))
        at = c1
    spans.append((at, front.L))
    # T-2679: a corner the course stops short of (1808's north-east, where it dies against
    # the corner pier's carved boss); capped there as at a corner
    stops = p.wall_head.get("stops_m") or {}
    lo, hi = float(stops.get("south", 0.0)), front.L - float(stops.get("north", 0.0))
    # T-3112: and the pier at the low-s end, capped under it (`front_pier`), takes none
    if getattr(p, "front_pier", None):
        lo = max(lo, p.front_pier["to_m"])
    spans = [(max(s0, lo), min(s1, hi)) for s0, s1 in spans if min(s1, hi) > max(s0, lo)]
    info = {"projection_m": pj, "height_m": ch, "profile": v["profile"], "soffit_m": y_s,
            "bays_carrying_it": len(cut)}
    if stops:
        info["stops_m"] = {k: float(x) for k, x in sorted(stops.items())}
    if p.wall_head.get("lift_m"):
        info["lift_m"] = float(p.wall_head["lift_m"])
    if p.wall_head.get("depth_m"):
        info["depth_m"] = float(p.wall_head["depth_m"])
    seed = a.instance(STONE, "cornice", info, {"soffit": (p.depth_m, y_s, 0.0)})
    var = K.Variant({"id": STONE, "kind": "moulded", "material": "stone"}, data)
    var.seed, var.rng = seed, random.Random(seed)
    for k, (s0, s1) in enumerate(spans):
        pc = var.piece(f"stone cornice {k + 1}", "stone", "open", run_names=[front.name])
        ends = (s0 < lo + 1e-9, s1 > hi - 1e-9)       # capped at a corner or a stop; dying into a bay
        K.sweep(pc.mesh, [front.at(s0, y_c), front.at(s1, y_c)], K.Y, prof, side=1.0, sgn=1.0, caps=ends)
    a.wall_head = {"cornice": STONE, "cornice_m": [round(y_c, 4), round(y_s, 4)], "projection_m": pj,
                   "stretches": [[round(s0, 3), round(s1, 3)] for s0, s1 in spans]}
    _lay(a, var.pieces, conf, STONE)


def _mansard_cornice(a, K, data, bays, conf):
    """T-3002: the kit's moulded stone cornice under a mansard's eave (1801 Prairie's heavy
    cornice under the slate faces, the Taylor photograph): its top the K05 soffit, as under a
    flat roof, but run round the walls the record names in one section, mitred at every
    corner it turns and capped where the named walls end. A K08 bay on those walls that
    stands up to it — a pavilion, a tower, a bow under its own cornice — takes it into its
    side, so the course stops on the bay's junctions; nothing else interrupts it, and a head
    that would reach it is refused, as on the street front."""
    p = a.p
    v = next(x for x in data["variants"] if x["id"] == STONE)
    prof = [tuple(q) for q in data["parts"]["profiles"][v["profile"]]["points"]]
    pj, ch = max(n for n, _ in prof), max(u for _, u in prof)
    if p.wall_head.get("depth_m"):
        k = float(p.wall_head["depth_m"]) / ch
        prof, ch = [(n, u * k) for n, u in prof], ch * k
    y_s = a.soffit_m
    y_c = y_s - ch
    if pj > p.eave_overhang_m - 0.02:
        raise ValueError("the stone cornice would reach the eave's fascia")
    by = {r.name: r for r in runs(p)}
    chain = [by[w] for w in _chain(p.wall_head["walls"])]
    cum = [0.0]
    for r in chain:
        cum.append(cum[-1] + r.L)
    names = [r.name for r in chain]
    for o in p.openings:
        if o.wall in names and o.head_m + HEAD_RISE_M > y_c - 0.005:
            raise ValueError(f"the head over {o.wall} s {o.s_m} reaches the stone cornice at {y_c:.3f} m")
    cut, into = [], []
    for b, (wall, s0, s1, top) in zip(p.bays, bays):
        # T-1890: but a shallow pavilion the cornice is carried across stands behind it (1801's
        # wall gable, HABS photograph 1: the course runs on under its lights to the corner)
        if wall in names and top > y_c - 0.005 and not b.get("cornice_across"):
            i = names.index(wall)
            cut.append((cum[i] + s0, cum[i] + s1))
            into.append(b["id"])
    # T-1890: a chamfered pavilion's corner cut (k01_frontage_params.chamfer_spans) takes the
    # course off the side wall too, from the lost corner back to where the canted face meets
    # it (1801's south wall, carried by the course since its south bay took the cornice round
    # it); the course is capped there, against the face, as at a corner
    from .k01_frontage_params import chamfer_spans
    capped = set()
    for wall, (s0, s1) in chamfer_spans(p.bays, p.depth_m, p.width_m).items():
        if wall in names and wall != "k01.wall.street_front":
            i = names.index(wall)
            cut.append((cum[i] + s0, cum[i] + s1))
            capped.add(round(cum[i] + (s1 if s0 < 1e-9 else s0), 6))
    spans, at = [], 0.0
    for c0, c1 in sorted(cut):
        if c0 > at:
            spans.append((at, c0))
        at = max(at, c1)
    if cum[-1] > at:
        spans.append((at, cum[-1]))

    def point(ps):
        i = max(j for j in range(len(chain)) if cum[j] <= ps + 1e-9)
        return chain[i].at(ps - cum[i], y_c)

    info = {"projection_m": pj, "height_m": ch, "profile": v["profile"], "soffit_m": y_s,
            "walls": names, "bays_carrying_it": len(cut)}
    if p.wall_head.get("depth_m"):
        info["depth_m"] = float(p.wall_head["depth_m"])
    seed = a.instance(STONE, "cornice", info, {"soffit": (p.depth_m, y_s, 0.0)})
    var = K.Variant({"id": STONE, "kind": "moulded", "material": "stone"}, data)
    var.seed, var.rng = seed, random.Random(seed)
    # T-3186: a canted corner's face stands in place of the corner its two walls met at, so the
    # course turns it on two mitres; it is never cut there (k01_frontage_params._cant_corner)
    cc = getattr(p, "cant_corner", None) or {}
    cant = {}
    if cc:
        from .k01_frontage_params import cant_corner_plan
        plan = cant_corner_plan(cc, p.depth_m, p.width_m)
        pair = list(plan["walls"])
        j = next((i for i in range(1, len(names)) if {names[i - 1], names[i]} == set(pair)), None)
        if j is None:
            raise ValueError("a canted corner's cornice turns it inside one run of the named walls")
        cant[j] = [(u, y_c, -v) for u, v in plan["ends"]]
        lo_, hi_ = cum[j] - plan["walls"][names[j - 1]][1] + plan["walls"][names[j - 1]][0], cum[j] + \
            plan["walls"][names[j]][1] - plan["walls"][names[j]][0]
        if any(lo_ - 1e-6 < x < hi_ + 1e-6 for sp in spans for x in sp):
            raise ValueError("the stone cornice stops on a canted corner's cut")
    paths = []
    for k, (s0, s1) in enumerate(spans):
        path = [point(s0)] + [q for j, c in enumerate(cum[1:-1], 1) if s0 + 1e-6 < c < s1 - 1e-6
                              for q in cant.get(j, [point(c)])] + [point(s1)]
        pc = var.piece(f"stone cornice {k + 1}", "stone", "open", run_names=names)
        ends = (s0 < 1e-9 or round(s0, 6) in capped,   # capped where the named walls end or a
                s1 > cum[-1] - 1e-9 or round(s1, 6) in capped)   # chamfer cuts them; dying into a bay
        K.sweep(pc.mesh, path, K.Y, prof, side=1.0, sgn=1.0, caps=ends)
        paths.append((path, ends))
    a.wall_head = {"cornice": STONE, "cornice_m": [round(y_c, 4), round(y_s, 4)], "projection_m": pj,
                   "walls": names, "dies_into": into,
                   "stretches": [[round(s0, 3), round(s1, 3)] for s0, s1 in spans]}
    _stone_frieze_blocks(a, K, var, prof, y_c, paths, names + ["k01.wall.cant"] * bool(cc))
    _lay(a, var.pieces, conf, STONE)


def _stone_frieze_blocks(a, K, var, prof, y_c, paths, walls):
    """T-3186: 1901 Prairie's two pictures put a frieze under the moulded stone cornice and,
    standing on it, a course of carved stone blocks — scrolled consoles — at an even
    spacing under the corona. The frieze (`wall_head.frieze`) is a plain band `height_m`
    under the cornice's foot, `proud_m` before the wall, swept along the course's own
    paths (round the canted corner's mitres, dying into a bay where the course does),
    open on the wall and lying under the cornice's bed. The blocks (`wall_head.blocks`)
    are K10's console, its back on the frieze's face and its top under the corona's
    soffit, one `corner_m` (at least clear of its own width) from each end of every
    straight stretch of the paths, evenly between at no more than `spacing_m`; one that
    would stand in a chimney stack or on a downpipe is left out. A head that reaches the
    frieze's or the blocks' foot is refused, as at the cornice."""
    p = a.p
    fz, bk = p.wall_head.get("frieze"), p.wall_head.get("blocks")
    if not fz and not bk:
        return
    fp = float(fz["proud_m"]) if fz else 0.0
    foot = y_c - float(fz["height_m"]) if fz else y_c
    # the corona's soffit: the section's widest level step outward, as a height and its reach
    steps = [(q1[0] - q0[0], q0[1], q1[0]) for q0, q1 in zip(prof, prof[1:]) if abs(q1[1] - q0[1]) < 1e-9 and q1[0] > q0[0]]
    _, u_s, n_s = max(steps)
    y_top = y_c + u_s
    if bk:
        h, w, bp = float(bk["height_m"]), float(bk["width_m"]), float(bk["projection_m"])
        if fp + bp > n_s - 0.02:
            raise ValueError(f"wall_head.blocks: {bp} m before the frieze reaches past the corona's soffit "
                             f"({n_s} m out, less 20 mm)")
        if fz and y_top - h < foot:
            raise ValueError(f"wall_head.blocks: {h} m under the corona's soffit stands below the frieze's foot")
        foot = min(foot, y_top - h)
    for o in p.openings:
        if o.wall in walls and o.head_m + HEAD_RISE_M > foot - 0.005:
            raise ValueError(f"the head over {o.wall} s {o.s_m} reaches the stone cornice's frieze or blocks at {foot:.3f} m")
    out = {}
    if fz:
        fh = float(fz["height_m"])
        fsec = [(0.0, 0.0), (fp, 0.0), (fp, fh)]
        for k, (path, ends) in enumerate(paths):
            pc = var.piece(f"stone frieze {k + 1}", "stone", "open", run_names=walls)
            K.sweep(pc.mesh, [(x, y_c - fh, z) for x, _, z in path], K.Y, fsec, side=1.0, sgn=1.0,
                    caps=ends, cap_close=[(0.0, fh)])
        out["frieze_m"] = [round(y_c - fh, 4), round(y_c, 4)]
    if bk:
        B = _kit().load()["parts"]["bracket"]
        c = max(B["corner_m"], w / 2 + CLEAR_M)
        sp = float(bk["spacing_m"])
        r = p.rainwater or {}
        pipes = [(x["wall"], x["s_m"], r.get("pipe_diameter_m", 0.0) / 2 + r.get("pipe_offset_from_wall_m", 0.0))
                 for x in r.get("downpipes", [])]
        by = {q.name: q for q in runs(p)}
        pipe_xz = [by[wl].at(s, 0.0) for wl, s, _ in pipes if wl in by]
        stacks = [(ch["u_m"] - ch["plan_m"][0] / 2 - ch["cap_proud_m"] - CLEAR_M,
                   ch["u_m"] + ch["plan_m"][0] / 2 + ch["cap_proud_m"] + CLEAR_M,
                   -ch["v_m"] - ch["plan_m"][1] / 2 - ch["cap_proud_m"] - CLEAR_M,
                   -ch["v_m"] + ch["plan_m"][1] / 2 + ch["cap_proud_m"] + CLEAR_M) for ch in p.chimneys]
        k, skipped, count = 0, 0, 0
        for path, _ in paths:
            for q0, q1 in zip(path, path[1:]):
                run = K.Run("stone blocks", (q0[0], q0[2]), (q1[0], q1[2]), (True, True))
                if run.L < w + 2 * CLEAR_M:
                    continue
                lo, hi = (c, run.L - c) if run.L - 2 * c >= 0 else (run.L / 2, run.L / 2)
                n = max(1, math.ceil((hi - lo) / sp - 1e-9))
                for i in range(n + 1 if hi > lo else 1):
                    s = lo + (hi - lo) * i / n
                    foot_xz = [run.at(s + d, 0.0, fp + e) for d in (-w / 2, w / 2) for e in (0.0, bp)]
                    xs, zs = [q[0] for q in foot_xz], [q[2] for q in foot_xz]
                    if any(min(xs) < x1 and max(xs) > x0 and min(zs) < z1 and max(zs) > z0 for x0, x1, z0, z1 in stacks) \
                            or any(min(xs) - rad - w / 2 < q[0] < max(xs) + rad + w / 2
                                   and min(zs) - rad - w / 2 < q[2] < max(zs) + rad + w / 2
                                   for q, (_, _, rad) in zip(pipe_xz, pipes)):
                        skipped += 1
                        continue
                    k += 1
                    pc = var.piece(f"stone block {k}", "stone", "open", bracket={"run": run.name, "s": s})
                    K.console(pc.mesh, run, s, y_top, fp, w, h, bp, B["curl"])
                    count += 1
        out["blocks"] = {"count": count, "left_out": skipped, "y_m": [round(y_top - h, 4), round(y_top, 4)]}
    a.wall_head.update(out)


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
