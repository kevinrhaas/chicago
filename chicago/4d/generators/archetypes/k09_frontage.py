"""K09 carved trim laid on a K01 frontage's street front (T-2310).

TICKET T-2310: piece 2 of T-1851 (package K09 of the T-1837 Prairie programme). Piece 1,
T-2309, built the carved-trim kit (`k09_trim.py` from `data/components/prairie_1904/
k09_trim.json`) on specimen boards. This module puts the kit's own pieces on a house: it
builds them with the kit's builders in the kit's frame (x along the wall, y up, z out of
the face) and moves them onto one of `k01_frontage`'s walls, so every ring, moulding,
console, capital and leaf is the geometry `tools/check_trim_kit.py` measures, not a copy.

What the record's `street_front_trim` names, and what is built for it:

  entrance         engaged foliate colonnettes on the stoop's landing carrying a round
                   voussoir ring over the door, a label returned level at its springs;
                   the half-round over the flat door head is the wall's own face (a plain
                   tympanum, so the ring rests on stone, never on the door's void)
  by_storey        per storey, the street windows' head: the kit's restrained rowhouse
                   surround (architrave and a cornice hood on consoles), its cornice hood
                   alone, or `k01.flat_lintel` (K01's own stone lintel, kept)
  apron            the kit's bounded foliate panel under each window of the storeys it
                   names, centred between the basement light's lintel and the sill

A generic kit motif is allowed here because 1808's own carving is not read in any source
this project holds (k09_trim.json `restrictions`: a generic motif never replaces a
landmark's documented carving). Glessner's carving is its own and this module never
touches it.

Pieces keep the kit's roles: `trim` is the house's smooth limestone trim, `carving` its
own slot so the carved stone can be costed and coloured apart.
"""

from __future__ import annotations

import random

ROLE_MATERIAL = {"trim": "limestone_trim", "carving": "carved_trim"}
BOARD_ROLES = ("wall", "backing", "ground")
FLAT = "k01.flat_lintel"
HEADS = ("k09.surround.rowhouse_restrained", "k09.trim.lintel_cornice_hood", FLAT)
ENTRANCE = "k09.entrance.ring_on_colonnettes"
APRON = "k09.trim.foliate_panel"
SILL_REACH_M = 0.08          # K01's sill runs this far past each jamb
SEAT_GAP_M = 0.004           # a capital stops this short of what it carries (no face on a face)


def _kit():
    # imported late: k09_trim imports k01_frontage's vector helpers, and k01_frontage
    # imports this module, so a top-level import here would be circular
    from . import k09_trim
    return k09_trim


def _variant(kit, data, vid):
    return next(v for v in data["variants"] if v["id"] == vid)


def spec(params) -> dict | None:
    """The record's `street_front_trim`, checked against what this module can build."""
    t = getattr(params, "street_front_trim", None)
    if not t:
        return None
    by = t.get("by_storey", [])
    if len(by) != params.stories or any(h not in HEADS for h in by):
        raise ValueError(f"street_front_trim.by_storey needs one of {HEADS} per storey")
    if t.get("entrance") not in (None, ENTRANCE):
        raise ValueError(f"street_front_trim.entrance builds {ENTRANCE!r} alone")
    if t.get("apron") not in (None, APRON):
        raise ValueError(f"street_front_trim.apron builds {APRON!r} alone")
    return t


def _storey(params, op) -> int:
    floors = params.floors_m
    return max(k for k, f in enumerate(floors) if op.sill_m >= f - 1e-6)


def head(params, op) -> str:
    """The head an opening takes: a kit trim id, or K01's flat lintel."""
    t = spec(params)
    if not t or op.wall != "k01.wall.street_front":
        return FLAT
    if op.component == "k01.opening.door_leaf":
        return ENTRANCE if t.get("entrance") else FLAT
    if op.component != "k01.opening.sash_flat":
        return FLAT
    return t["by_storey"][_storey(params, op)]


def sill_reach(params, op) -> float:
    """How far a sill runs past each jamb: under an architrave, past its outer edge, so
    the architrave's open feet stand on the sill and never hang over the wall."""
    if head(params, op) != "k09.surround.rowhouse_restrained":
        return SILL_REACH_M
    kit = _kit()
    ar = kit.load()["parts"]["profiles"]["architrave"]["points"]
    return max(n for n, _ in ar) + 0.03


def _lay(a, var, frame, s_c, y_off, conf, cid):
    """Move a kit variant's pieces (not its specimen board) onto the wall frame and add
    them to the assembly's primitives. Returns the triangles laid."""
    from .k01_frontage import MATERIALS, Y, _add, _mul
    O, R, N = frame
    at = lambda q: _add(_add(_add(O, _mul(R, s_c + q[0])), _mul(Y, y_off + q[1])), _mul(N, q[2]))
    turn = lambda n: _add(_add(_mul(R, n[0]), _mul(Y, n[1])), _mul(N, n[2]))
    tris = 0
    for piece in var.pieces:
        if piece.role in BOARD_ROLES:
            continue
        mat = ROLE_MATERIAL[piece.role]
        tu, tv = a.tiles[MATERIALS[mat]["fabric"]]
        pr = a.prim(mat)
        base = len(pr.pos)
        m = piece.mesh
        for q, n, uv in zip(m.pos, m.nrm, m.uv):
            p = at(q)
            pr.pos.append(p)
            pr.nrm.append(turn(n))
            pr.uv.append((uv[0] / tu, uv[1] / tv))   # the kit's UVs are surface metres
            pr.conf.append(conf)
            pr.tone.append(pr.tone_of(p[1]) if pr.tone_of else 1.0)
        pr.idx += [base + i for i in m.idx]
        tris += m.triangles()
    a.trim_triangles[cid] = a.trim_triangles.get(cid, 0) + tris   # costed per kit id
    return tris


def _seeded(kit, data, v, seed):
    var = kit.Variant(v, data)
    var.seed, var.rng = seed, random.Random(seed)
    return var


def dress(a, op, frame, conf):
    """Build an opening's K09 head (and apron) on its wall. False if it takes K01's
    flat lintel instead."""
    p = a.p
    kind = head(p, op)
    if kind == FLAT:
        return False
    kit = _kit()
    data = kit.load()
    sock = lambda s, y: _socket(frame, s, y)
    if kind == ENTRANCE:
        _entrance(a, kit, data, op, frame, conf)
        return True
    v = dict(_variant(kit, data, kind), clear_width_m=op.width_m, clear_height_m=op.height_m)
    seed = a.instance(kind, "trim", {"clear_width_m": op.width_m, "clear_height_m": op.height_m,
                                     "storey": _storey(p, op)},
                      {"sill": sock(op.s_m, op.sill_m), "head": sock(op.s_m, op.head_m)})
    _lay(a, _seeded(kit, data, v, seed).build(), frame, op.s_m, op.sill_m, conf, kind)
    t = spec(p)
    if t.get("apron") and _storey(p, op) in t.get("apron_storeys", []):
        _apron(a, kit, data, op, frame, conf)
    return True


def _socket(frame, s, y):
    from .k01_frontage import Y, _add, _mul
    O, R, N = frame
    return _add(_add(O, _mul(R, s)), _mul(Y, y))


def _apron(a, kit, data, op, frame, conf):
    """The kit's foliate panel, centred between the basement light's lintel and the sill."""
    p = a.p
    v = _variant(kit, data, APRON)
    below = [o for o in p.openings if o.wall == op.wall and abs(o.s_m - op.s_m) < 1e-6
             and o.head_m <= op.sill_m and o is not op]
    floor_y = max((o.head_m + 0.30 for o in below), default=p.principal_floor_m)   # K01's lintel
    top_y = op.sill_m - 0.10                                                      # K01's sill
    if top_y - floor_y < v["height_m"] + 0.2:
        raise ValueError(f"no room for an apron under the window at s = {op.s_m}")
    base = round((floor_y + top_y - v["height_m"]) / 2, 4)
    v = dict(v, base_m=0.0)
    seed = a.instance(APRON, "panel", {"width_m": v["width_m"], "height_m": v["height_m"]},
                      {"base": _socket(frame, op.s_m, base)})
    _lay(a, _seeded(kit, data, v, seed).build(), frame, op.s_m, base, conf, APRON)


def _entrance(a, kit, data, op, frame, conf):
    """A round ring on two engaged foliate colonnettes, a label over all."""
    p = a.p
    P = data["parts"]
    co, vs = P["colonnette"], P["voussoir"]
    ring_v = _variant(kit, data, "k09.trim.arch_ring_round")
    col_v = _variant(kit, data, "k09.trim.colonnette_foliate")
    # the abacus is cut to the plinth's width so the column stands clear of the jamb; the
    # ring's intrados springs from the abacus' inner edge, just outside the door's jamb
    a2 = co["plinth_m"] / 2
    half = op.width_m / 2 + 0.01
    cx = half + a2
    cz = co["shaft_diameter_m"] * 0.375             # engaged: the shaft's back is in the wall
    spring = op.head_m
    stop = 0.14
    seed = a.instance(ENTRANCE, "surround",
                      {"clear_width_m": op.width_m, "spring_m": spring, "ring_span_m": 2 * half,
                       "voussoirs": ring_v["voussoirs"], "order": col_v["order"]},
                      {"threshold": _socket(frame, op.s_m, op.sill_m), "spring": _socket(frame, op.s_m, spring)})
    var = _seeded(kit, data, {"id": ENTRANCE, "kind": "entrance"}, seed)
    arch = kit.Arch("round", 0.0, 2 * half, spring)
    R = vs["ring_depth_m"]
    var.ring(arch, 0.0, R, ring_v["voussoirs"], vs["proud_m"], name="entrance ring")
    var.label(arch, R + 0.01, stop)
    top = arch.apex() + R + 0.01 + max(n for n, _ in P["profiles"]["label"]["points"])
    belt = p.floors_m[1] - 0.20 if len(p.floors_m) > 1 else None   # k01_frontage's belt course
    if belt is not None and top >= belt:
        raise ValueError(f"the entrance label's crown ({top:.3f} m) runs into the belt course ({belt:.3f} m)")
    _lay(a, var, frame, op.s_m, 0.0, conf, ENTRANCE)
    cols = _seeded(kit, data, col_v, seed ^ 0x5A5A5A5A)
    for sgn, side in ((-1, "l"), (1, "r")):
        cols.colonnette(sgn * cx, cz, spring - op.sill_m - SEAT_GAP_M, col_v["order"],
                        name=f"entrance {side} colonnette", abacus_m=2 * a2)
    _lay(a, cols, frame, op.s_m, op.sill_m, conf, ENTRANCE)
