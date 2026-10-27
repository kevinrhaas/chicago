"""T-3000: a mansard's deck dressed as 1801 Prairie's is in J. W. Taylor's photograph.

TICKET T-3000 (piece 3 of T-2540). Taylor's c. 1895 print of the Kimball house shows the
main mansard's steep faces stopping at a curb, and on the curb, all along the two faces the
camera sees, a rail of pierced iron cresting about 0.55 m high; a tall turned finial stands
at the front's north corner on a small slated pyramid the curb's corner rises into, and a
second, plainer one at the front's south end. The record names this as its mansard's
`deck` (k01_frontage_params resolves it through `resolve` here), and this module builds it
on the K05 mansard k01_frontage.roof already raises:

  dress()     after the K05 union: each corner hood, a slated pyramid in the lower faces'
              slate standing on the deck's corner, its outer faces on the curb's lines; the K10 kit's iron cresting (`k10.cresting.iron_ridge`, its posts,
              bars, scrolls and spears) along each side of the curb, `inset_m` onto the deck
              and its base bar let into it, stretched to the record's height and stopped short
              of every corner; and a turned finial at every corner, on a hood's apex where one
              stands and on the deck where none does

The cresting's pattern is the kit's, not the print's (whose panels read only as a dense
pierced band at this scale), and the finials' turnings are this module's: docs/LIBERTIES.md
L-kimball-1801-deck-cresting-3000 says which numbers are read and which are reconstructed.
"""

from __future__ import annotations

import math
import random

#: the curb's four corners, by the two K01 faces that meet at each
CORNERS = ("street_south", "street_north", "rear_south", "rear_north")
CRESTING = "k10.cresting.iron_ridge"
SIDES = ("south", "north", "street", "rear")
HOOD_INSET_M = 0.02        # a hood's base stands this far inside the curb's lines
HOOD_FOOT_M = 0.05         # a hood's foot stands this far under the curb, buried in the roof
CORNER_CLEAR_M = 0.05      # the cresting stops this far short of a hood's base
FINIAL_CLEAR_M = 0.12      # ... and this far short of a plain finial's turning
FINIAL_INSET_M = 0.15      # a plain finial stands this far inside both curb lines
LET_IN_M = 0.03            # a finial's foot let into what carries it
FINIAL_SEGS = 12
#: a finial's turning, (r, y) as fractions of its radius and height: a collar on the
#: foot, a vase, a ball between two rings, a waisted neck, a bulb, then the spike
FINIAL = ((0.0, 0.0), (0.9, 0.0), (0.9, 0.04), (0.55, 0.07), (0.5, 0.14), (1.0, 0.22), (1.0, 0.26),
          (0.45, 0.31), (0.4, 0.38), (0.8, 0.43), (0.8, 0.47), (0.4, 0.52), (0.3, 0.6), (0.65, 0.65),
          (0.3, 0.71), (0.12, 0.75), (0.06, 0.94), (0.0, 1.0))


class ParamError(ValueError):
    pass


def resolve(deck: dict, m: dict, depth: float, width: float, overhang: float, pitch: float,
            chimneys) -> dict:
    """The record's `mansard.deck`, bounded. `m` is the resolved mansard (its curb), `pitch`
    the deck's (roof_pitch_deg). Returns what dress() builds from."""
    if m.get("crown"):
        raise ParamError("mansard.deck dresses a mansard's own deck; a crown stands on it")
    run = m["lower_rise_m"] / math.tan(math.radians(m["lower_pitch_deg"]))
    u0, u1 = -overhang + run, depth + overhang - run
    v0, v1 = -overhang + run, width + overhang - run
    out = {"curb": [round(x, 4) for x in (u0, u1, v0, v1)], "curb_m": m["curb_m"],
           "deck_pitch_deg": pitch}
    cr = deck.get("cresting")
    if cr is not None:
        h, ins = float(cr["height_m"]), float(cr.get("inset_m", 0.08))
        if not 0.3 <= h <= 1.0 or not 0.03 <= ins <= 0.3:
            raise ParamError("mansard.deck.cresting: 0.3-1.0 m high, 0.03-0.3 m inside the curb")
        out["cresting"] = {"variant": CRESTING, "height_m": h, "inset_m": ins}
        # T-2964: on the curb's sides a picture shows it on (1816's street and north; its south
        # curb stands behind the flank bay's own crowned deck), all four by default
        sd = cr.get("sides")
        if sd is not None:
            if not sd or set(sd) - set(SIDES) or len(set(sd)) != len(sd):
                raise ParamError(f"mansard.deck.cresting.sides: some of {', '.join(SIDES)}, once each")
            out["cresting"]["sides"] = list(sd)
    fn = deck.get("finials")
    if fn is not None:
        fh, fr = float(fn["height_m"]), float(fn["radius_m"])
        if not 0.8 <= fh <= 3.0 or not 0.05 <= fr <= 0.2:
            raise ParamError("mansard.deck.finials: 0.8-3.0 m high, 0.05-0.2 m in radius")
        out["finials"] = {"height_m": fh, "radius_m": fr}
    hd = deck.get("hoods")
    if hd is not None:
        at = list(hd["corners"])
        b, r = float(hd["base_m"]), float(hd["rise_m"])
        if not at or set(at) - set(CORNERS) or len(set(at)) != len(at):
            raise ParamError(f"mansard.deck.hoods.corners: some of {', '.join(CORNERS)}, once each")
        if not 0.5 <= b <= 1.6 or not 0.5 <= r <= 2.5 or b > min(u1 - u0, v1 - v0) / 3:
            raise ParamError("mansard.deck.hoods: a 0.5-1.6 m base, no more than a third of the deck, "
                             "rising 0.5-2.5 m")
        if not fn:
            raise ParamError("mansard.deck.hoods carry a finial each: name mansard.deck.finials")
        out["hoods"] = {"corners": at, "base_m": b, "rise_m": r}
    if not out.keys() & {"cresting", "finials"}:
        raise ParamError("mansard.deck names its cresting, its finials or both")
    # a stack across the curb line would cut the rail: none may stand on it
    for c in chimneys:
        sx, sz = c["plan_m"]
        for along, lo, hi, cu, cv in (("v", u0, u1, None, v0), ("v", u0, u1, None, v1),
                                      ("u", v0, v1, u0, None), ("u", v0, v1, u1, None)):
            if cv is not None and abs(c["v_m"] - cv) < sz / 2 + 0.1 and lo < c["u_m"] < hi:
                raise ParamError(f"chimney at ({c['u_m']}, {c['v_m']}) stands on the curb at v {cv:.2f}")
            if cu is not None and abs(c["u_m"] - cu) < sx / 2 + 0.1 and lo < c["v_m"] < hi:
                raise ParamError(f"chimney at ({c['u_m']}, {c['v_m']}) stands on the curb at u {cu:.2f}")
    return out


def _corner(dk, name):
    """A corner's (u, v) on the curb and the inward signs (su, sv) along u and v."""
    u0, u1, v0, v1 = dk["curb"]
    face, side = name.split("_")
    u, su = (u1, -1.0) if face == "street" else (u0, 1.0)
    v, sv = (v0, 1.0) if side == "south" else (v1, -1.0)
    return u, v, su, sv


def deck_y(dk, inset):
    """The deck's surface `inset` inside the curb (both its slopes rise alike from the curb)."""
    return dk["curb_m"] + inset * math.tan(math.radians(dk["deck_pitch_deg"]))


def hoods(a, dk, conf):
    """Each corner hood: four slated faces rising from a square on the deck's corner, its outer
    edges HOOD_INSET_M inside the curb's lines, to the apex `rise_m` over the curb. Its foot
    is HOOD_FOOT_M under the curb, so the deck and the lower faces bury it all round. Laid as
    faces of their own rather than joined into the K05 union: the hood stands astride the
    deck's hip, and K05's roof graph would read the hood's inner hip and the deck's as one."""
    hd = dk.get("hoods")
    if not hd:
        return
    from .k01_frontage import _cross, _sub, _unit
    b, r = hd["base_m"], hd["rise_m"]
    mat = "mansard_slate" if a.fabric.get("mansard_slate") else "slate_covering"
    for name in hd["corners"]:
        u, v, su, sv = _corner(dk, name)
        ua, ub = sorted((u + su * HOOD_INSET_M, u + su * (HOOD_INSET_M + b)))
        va, vb = sorted((v + sv * HOOD_INSET_M, v + sv * (HOOD_INSET_M + b)))
        y0, apex = dk["curb_m"] - HOOD_FOOT_M, (( ua + ub) / 2, dk["curb_m"] + r, -(va + vb) / 2)
        seed = a.instance("k01.roof.deck_hood", "roof", {"base_m": b, "rise_m": r, "corner": name},
                          {"apex": apex})
        foot = [(ua, y0, -va), (ub, y0, -va), (ub, y0, -vb), (ua, y0, -vb)]
        for i in range(4):
            p, q = foot[i], foot[(i + 1) % 4]
            n = _unit(_cross(_sub(q, p), _sub(apex, p)))
            if n[1] < 0:
                p, q = q, p
                n = _unit(_cross(_sub(q, p), _sub(apex, p)))
            up = _unit(_sub(apex, ((p[0] + q[0]) / 2, y0, (p[2] + q[2]) / 2)))
            a.prim(mat).face([p, q, apex], n, a.basis(mat, p, _unit(_sub(q, p)), up, seed), conf)


def _stretch(pieces, y0, s):
    """Stretch pieces upward from y0 by s, their normals turned to match (inverse transpose)."""
    for pc in pieces:
        m = pc.mesh
        m.pos = [(q[0], y0 + (q[1] - y0) * s, q[2]) for q in m.pos]
        nn = []
        for n in m.nrm:
            x, y, z = n[0], n[1] / s, n[2]
            ln = math.sqrt(x * x + y * y + z * z) or 1.0
            nn.append((x / ln, y / ln, z / ln))
        m.nrm = nn


def _turn(pieces, uc, zc):
    """Turn pieces built along X about the origin onto a run along Z: (x, y, z) -> (uc - z, y,
    zc + x), a rotation about the vertical, so winding and normals stay true."""
    for pc in pieces:
        m = pc.mesh
        m.pos = [(uc - q[2], q[1], zc + q[0]) for q in m.pos]
        m.nrm = [(-n[2], n[1], n[0]) for n in m.nrm]


def _cant_cut(p, dk, ins):
    """T-3186: where a canted corner's face crosses the cresting's lines, `ins` inside the curb:
    the side runs it stops ({side: (end, where)}), and the face's own run from the street
    side's line to the side wall's, as (u, v) points."""
    from .k01_frontage_params import cant_corner_plan
    plan = cant_corner_plan(p.cant_corner, p.depth_m, p.width_m)
    (fu, fv), _ = plan["ends"]
    nu, nv = plan["normal"]
    u0, u1, v0, v1 = dk["curb"]
    k = nu * fu + nv * fv + (u1 - p.depth_m) - ins     # the face's line, moved out to the curb, in
    north = p.cant_corner["corner"] == "north"
    us, vside = u1 - ins, (v1 - ins if north else v0 + ins)
    vs, uside = (k - nu * us) / nv, (k - nv * vside) / nu
    return {"stops": {"street": ("hi" if north else "lo", vs), ("north" if north else "south"): ("hi", uside)},
            "ends": ((us, vs), (uside, vside)) if north else ((uside, vside), (us, vs))}


def _aim(pieces, x, z, d):
    """T-3186: pieces built along X about the origin turned onto the plan direction d = (dx, dz)
    and moved to (x, z): a rotation about the vertical, as _turn's, so winding stays true."""
    for pc in pieces:
        m = pc.mesh
        m.pos = [(x + q[0] * d[0] - q[2] * d[1], q[1], z + q[0] * d[1] + q[2] * d[0]) for q in m.pos]
        m.nrm = [(n[0] * d[0] - n[2] * d[1], n[1], n[0] * d[1] + n[2] * d[0]) for n in m.nrm]


def dress(a, dk, conf):
    """The cresting along each side of the curb and a finial at every corner (module doc)."""
    from . import k10_frontage
    K = k10_frontage._kit()
    data = K.load()
    hoods(a, dk, conf)
    hd = dk.get("hoods") or {"corners": [], "base_m": 0.0, "rise_m": 0.0}
    fn = dk.get("finials")
    u0, u1, v0, v1 = dk["curb"]
    laid = {"cresting": [], "finials": []}

    def stop(name):   # how far along each side from this corner the cresting stops
        if name in hd["corners"]:
            return HOOD_INSET_M + hd["base_m"] + CORNER_CLEAR_M
        if fn:
            return FINIAL_INSET_M + fn["radius_m"] + FINIAL_CLEAR_M
        return 0.25

    cr = dk.get("cresting")
    if cr:
        ins = cr["inset_m"]
        y_cap = deck_y(dk, ins)
        sides = (("south", "u", v0 + ins, u0, u1, "rear_south", "street_south"),
                 ("north", "u", v1 - ins, u0, u1, "rear_north", "street_north"),
                 ("street", "v", u1 - ins, v0, v1, "street_south", "street_north"),
                 ("rear", "v", u0 + ins, v0, v1, "rear_south", "rear_north"))
        cant = _cant_cut(a.p, dk, ins) if getattr(a.p, "cant_corner", None) else None
        for side, along, at, lo, hi, c_lo, c_hi in sides:
            if side not in cr.get("sides", SIDES):
                continue
            end, where = (cant or {"stops": {}})["stops"].get(side, (None, None))
            lo, hi = (where, hi) if end == "lo" else (lo, where) if end == "hi" else (lo, hi)
            s0, s1 = lo + stop(c_lo), hi - stop(c_hi)
            L = s1 - s0
            if L < k10_frontage.MIN_CRESTING_M:
                continue
            mid = (s0 + s1) / 2
            ridge = (mid, y_cap, -at) if along == "u" else (at, y_cap, -mid)
            seed = a.instance(CRESTING, "cresting", {"length_m": round(L, 4), "ridge_cap_top_m": round(y_cap, 4),
                                                     "height_m": cr["height_m"], "host": "mansard deck",
                                                     "side": side}, {"ridge": ridge})
            var = K.Variant(dict(next(v for v in data["variants"] if v["id"] == CRESTING)), data)
            var.seed, var.rng = seed, random.Random(seed)
            if along == "u":   # a run along X, at z = -v
                posts = var.cresting(mid, L, y_cap, -at, host="mansard deck")
            else:              # built along X about the origin, then turned onto Z at x = u
                posts = var.cresting(0.0, L, y_cap, 0.0, host="mansard deck")
                _turn(var.pieces, at, -mid)
            top = max(q[1] for pc in var.pieces for q in pc.mesh.pos)
            _stretch(var.pieces, y_cap - 0.007, cr["height_m"] / (top - (y_cap - 0.007)))
            laid["cresting"].append({"side": side, "from_m": round(s0, 3), "to_m": round(s1, 3),
                                     "posts": len(posts)})
            k10_frontage._lay(a, var.pieces, conf, CRESTING)
        if cant:   # T-3186: and along the canted corner's curb, between the two runs it stopped
            (ua, va), (ub, vb) = cant["ends"]
            span = math.hypot(ub - ua, vb - va)
            L = span - 2 * stop(None)
            d = ((ub - ua) / span, -(vb - va) / span)        # in the plan's (x, z) = (u, -v)
            mid = ((ua + ub) / 2, -(va + vb) / 2)
            seed = a.instance(CRESTING, "cresting", {"length_m": round(L, 4), "ridge_cap_top_m": round(y_cap, 4),
                                                     "height_m": cr["height_m"], "host": "mansard deck",
                                                     "side": "cant"}, {"ridge": (mid[0], y_cap, mid[1])})
            var = K.Variant(dict(next(v for v in data["variants"] if v["id"] == CRESTING)), data)
            var.seed, var.rng = seed, random.Random(seed)
            posts = var.cresting(0.0, L, y_cap, 0.0, host="mansard deck")
            _aim(var.pieces, mid[0], mid[1], d)
            top = max(q[1] for pc in var.pieces for q in pc.mesh.pos)
            _stretch(var.pieces, y_cap - 0.007, cr["height_m"] / (top - (y_cap - 0.007)))
            laid["cresting"].append({"side": "cant", "from_m": 0.0, "to_m": round(L, 3), "posts": len(posts)})
            k10_frontage._lay(a, var.pieces, conf, CRESTING)
    if fn:
        from .k09_trim import lathe, Piece
        for name in CORNERS:
            u, v, su, sv = _corner(dk, name)
            if name in hd["corners"]:
                c = HOOD_INSET_M + hd["base_m"] / 2
                foot = dk["curb_m"] + hd["rise_m"] - LET_IN_M
                host = "corner hood"
            else:
                c = FINIAL_INSET_M
                foot = deck_y(dk, c) - LET_IN_M
                host = "mansard deck"
            x, z = u + su * c, -(v + sv * c)
            a.instance("k01.roof.deck_finial", "finial", {"height_m": fn["height_m"], "corner": name,
                                                           "host": host}, {"foot": (x, foot, z)})
            pc = Piece(f"finial {name}", "iron", "rooted", host=host)
            lathe(pc.mesh, (x, z), [(fn["radius_m"] * r, foot + fn["height_m"] * y) for r, y in FINIAL],
                  FINIAL_SEGS)
            k10_frontage._lay(a, [pc], conf, "k01.roof.deck_finial")
            laid["finials"].append({"corner": name, "foot_m": round(foot, 3), "on": host})
    a.deck = laid


def crown_finial(a, cr, conf):
    """T-3175: a hipped crown's turned finial (k01_frontage_params._hip_crown), standing on
    its ridge's street end, the apex the end's hip and the two side hips meet at, its foot
    let into the ridge; the deck's turning, laid as a deck finial on the crown."""
    from . import k10_frontage
    from .k09_trim import lathe, Piece
    fn = cr["finial"]
    x, z = cr["ridge_x_m"][1], (cr["z0"] + cr["z1"]) / 2
    foot = cr["ridge_m"] - LET_IN_M
    a.instance("k01.roof.deck_finial", "finial", {"height_m": fn["height_m"], "corner": "crown",
                                                   "host": "mansard crown"}, {"foot": (x, foot, z)})
    pc = Piece("finial crown", "iron", "rooted", host="mansard crown")
    lathe(pc.mesh, (x, z), [(fn["radius_m"] * r, foot + fn["height_m"] * y) for r, y in FINIAL], FINIAL_SEGS)
    k10_frontage._lay(a, [pc], conf, "k01.roof.deck_finial")
