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
                   storey's head as the front's do, and any may carry its own transom tiers,
                   and a surrounded one its `pilasters`: a carved pilaster each side whose
                   capital carries the hood's end in place of its console
  shelf            (T-2531) over the apron, the light stood on a tablet proud of the wall over
                   a moulded shelf under its sill, the panel hung from the shelf's foot
  crest            (T-3270) on the storeys it names, a carved crest standing on each street
                   window's cornice hood: a palmette at its middle between two scroll volutes
                   on low sweeps, `width_m` across (never wider than the hood), `height_m` high
                   and `proud_m` out of the wall (1905 Prairie's chamber windows, the 1893 plate)
  frieze_roundels  (T-3270) at each `s_m` along the front, a pair of carved rings `gap_m` apart
                   centred at `y_m` in the wall head's frieze, between two upright blocks
                   `block_m` wide (the plate's frieze over each pier, read "1 O O 1")

A generic kit motif is allowed here because 1808's own carving is not read in any source
this project holds (k09_trim.json `restrictions`: a generic motif never replaces a
landmark's documented carving). Glessner's carving is its own and this module never
touches it.

Pieces keep the kit's roles: `trim` is the house's smooth limestone trim, `carving` its
own slot so the carved stone can be costed and coloured apart.
"""

from __future__ import annotations

import math
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
PILASTER = "k09.trim.light_pilaster"   # T-1890: a surrounded light's pilasters (`lights[].pilasters`)
PILASTER_BURY_M = 0.004      # each pilaster piece runs this far into what it stands on and carries
PILASTER_BASE_GROW_M = 0.02  # a base stands this much wider (each side) and prouder than its shaft
PILASTER_CAP_GROW_M = 0.045  # and a capital this much (K08's pilasters, T-2931)


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
    cr = t.get("crest")
    if cr is not None and (set(cr) != {"storeys", "width_m", "height_m", "proud_m"}
                           or not all(isinstance(k, int) and 0 <= k < params.stories for k in cr["storeys"])
                           or not 0.4 <= cr["width_m"] <= 2.0 or not 0.15 <= cr["height_m"] <= 0.6
                           or not 0.04 <= cr["proud_m"] <= 0.2):
        raise ValueError("street_front_trim.crest takes storeys (by index), width_m (0.4-2.0 m), height_m "
                         "(0.15-0.6 m) and proud_m (0.04-0.2 m)")
    fr = t.get("frieze_roundels")
    if fr is not None and (set(fr) != {"s_m", "y_m", "radius_m", "ring_m", "proud_m", "gap_m", "block_m"}
                           or not fr["s_m"] or not 0.08 <= fr["radius_m"] <= 0.3
                           or not 0.02 <= fr["ring_m"] < fr["radius_m"] or not 0.01 <= fr["proud_m"] <= 0.08
                           or not 2 * fr["radius_m"] < fr["gap_m"] <= 1.5 or not 0.0 <= fr["block_m"] <= 0.2):
        raise ValueError("street_front_trim.frieze_roundels takes s_m (a list), y_m, radius_m (0.08-0.3 m), "
                         "ring_m (under the radius), proud_m (0.01-0.08 m), gap_m (the pair's centres, clear "
                         "of each other, up to 1.5 m) and block_m (0-0.2 m)")
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
    pil = (light(p, op) or {}).get("pilasters") if kind == "k09.surround.rowhouse_restrained" else None
    if pil:
        # T-1890: the hood runs out over each pilaster's capital, which carries it in place of a console
        v.update(overhang_m=pilaster_overhang(pil), consoles=False)
    # T-2960: a round_heads hood's block stands its own distance past the jambs
    ov = ((getattr(p, "round_heads", None) or {}).get("hood") or {}).get("overhang_m") \
        if op.component == "k01.opening.sash_round_hooded" else None
    if ov is not None:
        v["overhang_m"] = ov
    seed = a.instance(kind, "trim", {"clear_width_m": op.width_m, "clear_height_m": op.height_m,
                                     "storey": _storey(p, op), **({"overhang_m": ov} if ov is not None else {}),
                                     **({"overhang_m": v["overhang_m"], "consoles": False} if pil else {})},
                      {"sill": sock(op.s_m, op.sill_m), "head": sock(op.s_m, op.head_m)})
    t = spec(p)
    aproned = bool(t.get("apron")) and _storey(p, op) in t.get("apron_storeys", [])
    sh = t.get("shelf") if aproned else None
    var = _seeded(kit, data, v, seed).build()
    _lay(a, var, frame, op.s_m, op.sill_m, conf, kind, sh["tablet_m"] if sh else 0.0)
    foot = _shelf(a, var, op, frame, conf, sh, seed) if sh else None
    if aproned:
        _apron(a, kit, data, op, frame, conf, foot)
    if pil:
        _pilasters(a, kit, data, op, frame, conf, pil)
    cr = t.get("crest")
    if cr and _storey(p, op) in cr["storeys"] and op.component == "k01.opening.sash_flat":
        _crest(a, var, op, frame, conf, cr, seed)
    return True


ARC_PIECES = 16      # a carved ring's pieces round its circle


def _crest(a, var, op, frame, conf, cr, seed):
    """T-3270: a carved crest on a window's cornice hood (module doc): it stands on the hood's
    top, as wide as the spec or the hood's top (the narrower), its back in the wall."""
    from .k01_dressings import prism
    mat = ROLE_MATERIAL["carving"]
    pts = [q for piece in var.pieces if piece.role not in BOARD_ROLES for q in piece.mesh.pos]
    top = max(q[1] for q in pts)
    at_top = [q[0] for q in pts if q[1] > top - 1e-6]
    W = min(cr["width_m"], max(at_top) - min(at_top))
    h, d = cr["height_m"], cr["proud_m"]
    c, y0 = op.s_m, op.sill_m + top
    pw = W / 6                                   # the palmette's half width
    r = min(h * 0.4, W / 8)                      # each volute's radius
    prism(a, mat, frame, [(c - pw, y0), (c + pw, y0), (c + pw, y0 + 0.6 * h), (c, y0 + h),
                          (c - pw, y0 + 0.6 * h)], 0.0, d, seed, conf)
    for sg in (-1, 1):
        vc = c + sg * (W / 2 - r)
        prism(a, mat, frame, [(c + sg * pw, y0), (vc, y0), (vc, y0 + 1.2 * r), (c + sg * pw, y0 + 0.45 * h)],
              0.0, d * 0.7, seed, conf)
        ring = [(vc + r * math.cos(2 * math.pi * k / 8), y0 + r + r * math.sin(2 * math.pi * k / 8))
                for k in range(8)]
        prism(a, mat, frame, ring, 0.0, d * 0.85, seed, conf)
        eye = [(vc + r * 0.45 * math.cos(2 * math.pi * k / 8), y0 + r + r * 0.45 * math.sin(2 * math.pi * k / 8))
               for k in range(8)]
        prism(a, mat, frame, eye, d * 0.85, d, seed, conf)
    a.crest_meta = getattr(a, "crest_meta", []) + [
        {"s_m": round(c, 4), "foot_m": round(y0, 4), "top_m": round(y0 + h, 4), "width_m": round(W, 4)}]


def frieze(a, frame, conf):
    """T-3270: the frieze's carved roundels (module doc), each pair between its two blocks."""
    t = spec(a.p)
    fr = (t or {}).get("frieze_roundels")
    if not fr:
        return
    from .k01_dressings import prism
    mat = ROLE_MATERIAL["carving"]
    R, ri, d, g, bw, y = fr["radius_m"], fr["radius_m"] - fr["ring_m"], fr["proud_m"], fr["gap_m"], \
        fr["block_m"], fr["y_m"]
    for s in fr["s_m"]:
        seed = a.instance("k09.frieze.roundels", "trim", {"radius_m": R, "gap_m": g},
                          {"centre": _socket(frame, s, y)})
        for c in (s - g / 2, s + g / 2):
            for i in range(ARC_PIECES):
                t0, t1 = 2 * math.pi * i / ARC_PIECES, 2 * math.pi * (i + 1) / ARC_PIECES
                prism(a, mat, frame, [(c + ri * math.cos(t0), y + ri * math.sin(t0)),
                                      (c + R * math.cos(t0), y + R * math.sin(t0)),
                                      (c + R * math.cos(t1), y + R * math.sin(t1)),
                                      (c + ri * math.cos(t1), y + ri * math.sin(t1))], 0.0, d, seed, conf)
        if bw:
            for sg in (-1, 1):
                x0 = s + sg * (g / 2 + R + 0.06)
                x1 = x0 + sg * bw
                prism(a, mat, frame, [(min(x0, x1), y - R), (max(x0, x1), y - R), (max(x0, x1), y + R),
                                      (min(x0, x1), y + R)], 0.0, d, seed, conf)


def pilaster_overhang(pil) -> float:
    """T-1890: how far a pilastered light's hood runs past its architrave: over the gap, the
    shaft and its capital's spread, and a centimetre on, so the block covers the capital."""
    return round(pil["gap_m"] + pil["width_m"] + PILASTER_CAP_GROW_M + 0.01, 4)


def _pilasters(a, kit, data, op, frame, conf, pil):
    """T-1890: a carved pilaster each side of a surrounded light (1801's two lights over the
    loggia, the Taylor print: each light between two pilasters rising from the belt under its
    sill to carved capitals beside its head, a carved lozenge on each shaft; HABS 1965's
    photograph 2 shows one to a shaft, centred). Each stands
    `gap_m` clear of the architrave: a base on `foot_m` (over grade), a shaft `width_m` broad
    and `proud_m` out, and a capital under the hood's frieze block where the console would
    hang, the base and the capital each wider and prouder than the shaft (the capital the
    more), as K08's pilasters on 1801's bow are (T-2931); on the shaft `count` lozenges
    `height_m` tall, spaced evenly up it. Every piece runs 4 mm into what it
    stands on and what it carries, the lozenges 4 mm into the shaft, so no face lies on another."""
    P = data["parts"]
    aw = max(n for n, _ in P["profiles"]["architrave"]["points"])
    w, d, hb, hc = pil["width_m"], pil["proud_m"], pil["base_m"], pil["capital_m"]
    lo = pil["foot_m"] - op.sill_m              # in the light's frame: y up from its sill
    hi = op.height_m + aw                       # the frieze block's bed
    x0 = op.width_m / 2 + aw + pil["gap_m"]
    lz = pil.get("lozenges")
    seed = a.instance(PILASTER, "trim", {"width_m": w, "proud_m": d, "base_m": hb, "capital_m": hc,
                                         "gap_m": pil["gap_m"], "storey": _storey(a.p, op)},
                      {"foot": _socket(frame, op.s_m, pil["foot_m"]), "head": _socket(frame, op.s_m, op.sill_m + hi)})
    var = _seeded(kit, data, {"id": PILASTER, "kind": "pilaster"}, seed)
    B = PILASTER_BURY_M
    for sgn, side in ((-1, "l"), (1, "r")):
        xa, xb = sorted((sgn * x0, sgn * (x0 + w)))
        for name, ya, yb, grow in (("base", lo - B, lo + hb, PILASTER_BASE_GROW_M),
                                   ("capital", hi - hc, hi + B, PILASTER_CAP_GROW_M),
                                   ("shaft", lo + hb - B, hi - hc + B, 0.0)):
            pc = var.piece(f"{side} pilaster {name}", "trim", "open", relief={"plane_z": 0.0, "proud_m": d + grow})
            kit.box(pc.mesh, xa - grow, xb + grow, ya, yb, 0.0, d + grow, skip=("back",))
        if not lz:
            continue
        lw, hh, m = w - 2 * lz["margin_m"], lz["height_m"] / 2, lz["count"]
        step = (hi - hc - lo - hb) / m
        cx = (xa + xb) / 2
        for j in range(m):
            cy = lo + hb + step * (j + 0.5)
            pc = var.piece(f"{side} pilaster lozenge {j + 1}", "carving", "rooted", host=f"{side} pilaster shaft",
                           relief={"plane_z": d, "proud_m": lz["relief_m"]})
            kit.prism(pc.mesh, [(cx, cy - hh), (cx + lw / 2, cy), (cx, cy + hh), (cx - lw / 2, cy)],
                      d - B, d + lz["relief_m"])
    _lay(a, var, frame, op.s_m, op.sill_m, conf, PILASTER)


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
