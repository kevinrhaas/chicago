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
                   names, centred between the basement light's lintel and the sill, or
                   (`apron_over_belt`, T-2526) between the storey's belt course and the sill
  lights           (T-1890) single lights by wall, place and storey: a side wall's wears its
                   storey's head as the front's do, and any may carry its own transom tiers
  shelf            (T-2531) over the apron, the light stood on a tablet proud of the wall over
                   a moulded shelf under its sill, the panel hung from the shelf's foot

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
DOOR_HOOD = "k09.trim.lintel_cornice_hood"   # T-2409: the kit's cornice hood over a flat-headed door
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
    if t.get("entrance") not in (None, ENTRANCE, DOOR_HOOD):
        raise ValueError(f"street_front_trim.entrance builds {ENTRANCE!r} or {DOOR_HOOD!r} alone")
    if t.get("apron") not in (None, APRON):
        raise ValueError(f"street_front_trim.apron builds {APRON!r} alone")
    if t.get("apron_over_belt") and not t.get("apron"):
        raise ValueError("street_front_trim.apron_over_belt places an apron, and names none")
    sh = t.get("shelf")
    if sh is not None and (not t.get("apron") or set(sh) != {"height_m", "proud_m", "tablet_m"}
                           or not 0.15 <= sh["height_m"] <= 0.5 or not 0.05 <= sh["proud_m"] <= 0.3
                           or not 0.0 < sh["tablet_m"] < sh["proud_m"]):
        raise ValueError("street_front_trim.shelf stands over an apron and takes height_m (0.15-0.5 m), "
                         "proud_m (0.05-0.3 m) and tablet_m (under the shelf's proud)")
    return t


def _storey(params, op) -> int:
    floors = params.floors_m
    return max(k for k, f in enumerate(floors) if op.sill_m >= f - 1e-6)


def light(params, op) -> dict | None:
    """T-1890: the `street_front_trim.lights` entry naming this light (its wall, place and
    storey), or None."""
    t = spec(params)
    if not t or op.component != "k01.opening.sash_flat":
        return None
    return next((e for e in t.get("lights", ()) if e["wall"] == op.wall and abs(e["s_m"] - op.s_m) < 1e-6
                 and e["storey"] == _storey(params, op)), None)


def head(params, op) -> str:
    """The head an opening takes: a kit trim id, or K01's flat lintel."""
    t = spec(params)
    # T-3186: a canted corner's face is the front's own, turned: its windows wear the front's heads
    # T-1890: and a side wall's light the record names in `lights` wears its storey's head
    if not t or (op.wall not in ("k01.wall.street_front", "k01.wall.cant") and light(params, op) is None):
        return FLAT
    if op.component == "k01.opening.door_leaf":
        return t.get("entrance") or FLAT
    if op.component == "k01.opening.sash_round_hooded":   # T-2960: the hood its round_heads name
        return ((getattr(params, "round_heads", None) or {}).get("hood") or {}).get("variant") or FLAT
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


def _lay(a, var, frame, s_c, y_off, conf, cid, d_off=0.0):
    """Move a kit variant's pieces (not its specimen board) onto the wall frame, `d_off`
    before it, and add them to the assembly's primitives. Returns the triangles laid."""
    from .k01_frontage import MATERIALS, Y, _add, _mul
    O, R, N = frame
    at = lambda q: _add(_add(_add(O, _mul(R, s_c + q[0])), _mul(Y, y_off + q[1])), _mul(N, q[2] + d_off))
    turn = lambda n: _add(_add(_mul(R, n[0]), _mul(Y, n[1])), _mul(N, n[2]))
    tris = 0
    for piece in var.pieces:
        if piece.role in BOARD_ROLES:
            continue
        mat = ROLE_MATERIAL[piece.role]
        tu, tv = a.tiles[a.fabric[mat]]   # the fabric the slot is bound to (K02's, T-2289)
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
    if hasattr(a, "seat"):   # T-2289: where the pieces stand, for a coursed front to dress
        a.seat(frame, [(s_c + q[0], y_off + q[1], q[2] + d_off) for piece in var.pieces
                       if piece.role not in BOARD_ROLES for q in piece.mesh.pos], cid)
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
    # T-2960: a round_heads hood's block stands its own distance past the jambs
    ov = ((getattr(p, "round_heads", None) or {}).get("hood") or {}).get("overhang_m") \
        if op.component == "k01.opening.sash_round_hooded" else None
    if ov is not None:
        v["overhang_m"] = ov
    seed = a.instance(kind, "trim", {"clear_width_m": op.width_m, "clear_height_m": op.height_m,
                                     "storey": _storey(p, op), **({"overhang_m": ov} if ov is not None else {})},
                      {"sill": sock(op.s_m, op.sill_m), "head": sock(op.s_m, op.head_m)})
    t = spec(p)
    aproned = bool(t.get("apron")) and _storey(p, op) in t.get("apron_storeys", [])
    sh = t.get("shelf") if aproned else None
    var = _seeded(kit, data, v, seed).build()
    _lay(a, var, frame, op.s_m, op.sill_m, conf, kind, sh["tablet_m"] if sh else 0.0)
    foot = _shelf(a, var, op, frame, conf, sh, seed) if sh else None
    if aproned:
        _apron(a, kit, data, op, frame, conf, foot)
    return True


def _shelf(a, var, op, frame, conf, sh, seed):
    """T-2531: the light stood `tablet_m` proud of the wall on a stone tablet as wide as
    its trim's seat, whose sides are its returns and whose inner faces carry the reveal
    out to the trim, over a moulded shelf under its sill (two stepped courses, the upper
    `proud_m` before the wall), as 1621's drawing draws the light over its door. Returns
    the shelf's foot."""
    mat = ROLE_MATERIAL["trim"]
    tab, hgt, out = sh["tablet_m"], sh["height_m"], sh["proud_m"]
    back = [q for piece in var.pieces if piece.role not in BOARD_ROLES for q in piece.mesh.pos if q[2] < 0.005]
    s0, s1 = op.s_m + min(q[0] for q in back), op.s_m + max(q[0] for q in back)
    top = op.sill_m + max(q[1] for q in back)
    h0, h1 = op.s_m - op.width_m / 2, op.s_m + op.width_m / 2
    for b in ((s0, h0, op.sill_m, top), (h1, s1, op.sill_m, top), (h0, h1, op.head_m, top)):
        a.proud_box(mat, frame, b[0], b[1], b[2], b[3], tab, seed, conf)
    y1 = op.sill_m - 0.10                      # K01's sill stands on the shelf
    y0, ym = y1 - hgt, y1 - hgt * 0.6
    w = (s1 - s0) / 2 + 0.05
    a.proud_box(mat, frame, op.s_m - w, op.s_m + w, ym, y1, out, seed, conf)
    a.proud_box(mat, frame, op.s_m - w + 0.06, op.s_m + w - 0.06, y0, ym, out * 0.55, seed, conf)
    if hasattr(a, "seat"):
        a.seat(frame, [(s0, op.sill_m, tab), (s1, top, tab)], "K09.shelf")
        a.seat(frame, [(op.s_m - w, y0, out), (op.s_m + w, y1, out)], "K09.shelf")
    return y0


def _socket(frame, s, y):
    from .k01_frontage import Y, _add, _mul
    O, R, N = frame
    return _add(_add(O, _mul(R, s)), _mul(Y, y))


def _apron(a, kit, data, op, frame, conf, shelf_foot=None):
    """The kit's foliate panel, centred between the basement light's lintel and the sill,
    or (T-2531) hung from the foot of the shelf the light stands on."""
    p = a.p
    v = _variant(kit, data, APRON)
    below = [o for o in p.openings if o.wall == op.wall and abs(o.s_m - op.s_m) < 1e-6
             and o.head_m <= op.sill_m and o is not op]
    floor_y = max((o.head_m + 0.30 for o in below), default=p.principal_floor_m)   # K01's lintel
    if spec(p).get("apron_over_belt"):
        # T-2526: the panel stands on its storey's belt course, under the sill it carries
        floor_y = max(floor_y, p.floors_m[_storey(p, op)])
    top_y = op.sill_m - 0.10                                                      # K01's sill
    if top_y - floor_y < v["height_m"] + 0.2:
        raise ValueError(f"no room for an apron under the window at s = {op.s_m}")
    base = round((floor_y + top_y - v["height_m"]) / 2, 4)
    if shelf_foot is not None:
        if shelf_foot - v["height_m"] < floor_y:
            raise ValueError(f"no room for an apron under the shelf at s = {op.s_m}")
        base = round(shelf_foot - v["height_m"], 4)
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
