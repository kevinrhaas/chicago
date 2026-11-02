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
CROSS_CLEAR_M = 0.1        # ... and this far short of a pavilion's cross roof (T-1890)
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
            chimneys, bays=()) -> dict:
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
        # T-1881 (2026-11-02): or one rail round the deck and the decks of the K08 sections whose
        # mansards are joined to it (1729's: one curb and one rail over every section in the
        # Detroit print), a finial at each of the joined curb's corners (dress_joined)
        if cr.get("joined") is not None:
            if cr["joined"] is not True or sd is not None or cr.get("painted") is not None:
                raise ParamError("mansard.deck.cresting.joined: true, round the whole joined curb (no sides, iron)")
            out["cresting"]["joined"] = True
        # T-1871: or the kit's pattern in the eave's painted timber, not iron (1700-1706's
        # deck railing, a white fret in Chicagology's photograph)
        if cr.get("painted") is not None:
            if cr["painted"] is not True:
                raise ParamError("mansard.deck.cresting.painted: true, or leave it out for the iron")
            out["cresting"]["painted"] = True
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
    if (out.get("cresting") or {}).get("joined") and (deck.get("hoods") or deck.get("cross_roof") or not fn):
        raise ParamError("mansard.deck.cresting.joined: a finial at every corner (finials), no hoods or cross roof")
    if deck.get("cross_roof"):
        out["cross_roof"] = _cross_roof(deck["cross_roof"], out, bays, depth)
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


def _cross_roof(c: dict, dk: dict, bays, depth: float) -> dict:
    """T-1890: a street-front pavilion's cross roof run back through the deck's corner (1801's
    south pavilion: the Taylor photograph and HABS photograph 1 both show its slated roof
    running back from behind the coped gable over the curb, to a finial on its ridge's end
    about 4.5 m behind the front, where the cresting along the front stops and the corner
    has no finial of its own). `over_bay` names the K08 shallow projection whose gable carries
    the roof (`roof.gable.behind`, k08_bays.Bay._gable_behind); its plan is read off the bay,
    in the curb's (u, v): its cheeks' v, its ridge's v and height, and its end's u."""
    u0, u1, v0, v1 = dk["curb"]
    b = next((x for x in bays if x["id"] == c.get("over_bay")), None)
    bh = (((b or {}).get("variant") or {}).get("roof") or {}).get("gable", {}).get("behind")
    if b is None or b["wall"] != "k01.wall.street_front" or not b["variant"].get("shallow") or not bh:
        raise ParamError(f"mansard.deck.cross_roof.over_bay {c.get('over_bay')!r}: a shallow projection on the "
                         f"street front whose gable carries a roof behind it (roof.gable.behind)")
    g = b["variant"]["roof"]["gable"]
    pts = b["variant"]["plan"]["points"]
    xl, xr = float(pts[1][0]), float(pts[2][0])
    il, ir = (float(x) for x in g.get("inset_m", (0.0, 0.0)))
    s = float(b["s_m"])
    lo, hi, mid = s + xl, s + xr, s + (xl + il + xr - ir) / 2
    end, ridge = depth - float(bh["run_back_m"]), float(bh["ridge_m"])
    if hi >= v1 and v0 < lo:
        corner = "street_north"
    elif lo <= v0 and hi < v1:
        corner = "street_south"
    else:
        raise ParamError("mansard.deck.cross_roof: the pavilion's roof runs back through one of the street "
                         "front's curb corners, and only one")
    if not (u0 + 1.0 <= end < u1 - 0.5 and ridge > dk["curb_m"]):
        raise ParamError(f"mansard.deck.cross_roof: its ridge stands over the curb's {dk['curb_m']} m and its end "
                         f"on the deck, 0.5 m or more behind the street curb at u {u1:.2f} (not u {end:.2f})")
    out = {"over_bay": b["id"], "corner": corner, "v_m": [round(lo, 4), round(hi, 4)],
           "ridge_v_m": round(mid, 4), "ridge_m": ridge, "end_u_m": round(end, 4)}
    if c.get("hood") is not None:
        out["hood"] = _cross_hood(c["hood"], dk, end, mid, ridge)
    return out


def _cross_hood(h: dict, dk: dict, end: float, mid: float, ridge: float) -> dict:
    """T-1890: the slated hood over a cross roof's ridge end (HABS photograph 1 of 1801: a
    small slated pyramid, its hips white-flashed, capping the end where the cross roof's
    ridge meets the deck, the finial on its apex; on the Taylor print it stands behind the
    ridge and only lifts the finial). A square `base_m` across, centred on the ridge's end,
    rising to `rise_m` over the ridge; its foot HOOD_FOOT_M under the deck's lowest point
    under it, so the deck behind and the cross roof's slopes in front bury it all round."""
    if set(h) - {"base_m", "rise_m", "flashing_m"}:
        raise ParamError(f"mansard.deck.cross_roof.hood takes base_m, rise_m and flashing_m, not {sorted(h)}")
    b, r = float(h["base_m"]), float(h["rise_m"])
    fl = float(h.get("flashing_m", 0.0))
    u0, u1, v0, v1 = dk["curb"]
    ua, ub, va, vb = end - b / 2, end + b / 2, mid - b / 2, mid + b / 2
    if not 0.5 <= b <= 1.6 or not 0.3 <= r <= 2.0 or not (fl == 0.0 or 0.03 <= fl <= 0.12):
        raise ParamError("mansard.deck.cross_roof.hood: a 0.5-1.6 m base rising 0.3-2.0 m over the ridge, "
                         "its hips' flashing 0.03-0.12 m a side (or none)")
    if not (u0 + HOOD_INSET_M <= ua and ub <= u1 - HOOD_INSET_M and v0 + HOOD_INSET_M <= va
            and vb <= v1 - HOOD_INSET_M):
        raise ParamError(f"mansard.deck.cross_roof.hood: its {b} m base on the ridge's end stands inside the "
                         f"curb, {HOOD_INSET_M} m or more from each of its lines")
    low = min(ua - u0, u1 - ub, va - v0, v1 - vb)   # the base's corner nearest a curb line
    foot = dk["curb_m"] + low * math.tan(math.radians(dk["deck_pitch_deg"])) - HOOD_FOOT_M
    return {"base_m": b, "rise_m": r, "flashing_m": fl, "u_m": [round(ua, 4), round(ub, 4)],
            "v_m": [round(va, 4), round(vb, 4)], "foot_m": round(foot, 4), "apex_m": round(ridge + r, 4)}


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
    xh = (dk.get("cross_roof") or {}).get("hood")
    if xh:
        _cross_hood_faces(a, dk, xh, conf)
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


def _cross_hood_faces(a, dk, xh, conf):
    """T-1890: the cross roof's hood (_cross_hood): four slated faces from its square foot to
    the apex over the ridge's end, laid as a corner hood's are, and along each hip a roll of
    pale zinc `flashing_m` down each face either side, a centimetre proud of the slate."""
    from .k01_frontage import _cross, _sub, _unit
    xr = dk["cross_roof"]
    (ua, ub), (va, vb), y0 = xh["u_m"], xh["v_m"], xh["foot_m"]
    apex = (xr["end_u_m"], xh["apex_m"], -xr["ridge_v_m"])
    mat = "mansard_slate" if a.fabric.get("mansard_slate") else "slate_covering"
    seed = a.instance("k01.roof.deck_hood", "roof", {"base_m": xh["base_m"], "rise_m": xh["rise_m"],
                                                      "corner": "cross_roof"}, {"apex": apex})
    foot = [(ua, y0, -va), (ub, y0, -va), (ub, y0, -vb), (ua, y0, -vb)]
    normals = []
    for i in range(4):
        p, q = foot[i], foot[(i + 1) % 4]
        n = _unit(_cross(_sub(q, p), _sub(apex, p)))
        if n[1] < 0:
            p, q = q, p
            n = _unit(_cross(_sub(q, p), _sub(apex, p)))
        normals.append(n)
        up = _unit(_sub(apex, ((p[0] + q[0]) / 2, y0, (p[2] + q[2]) / 2)))
        a.prim(mat).face([p, q, apex], n, a.basis(mat, p, _unit(_sub(q, p)), up, seed), conf)
    w = xh.get("flashing_m", 0.0)
    if not w:
        return
    zinc = "k04_zinc_sheet"
    for i in range(4):   # hip i runs from foot[i] up to the apex, between faces i-1 and i
        c = foot[i]
        along = _unit(_sub(apex, c))
        for n, far in ((normals[i - 1], foot[i - 1]), (normals[i], foot[(i + 1) % 4])):
            off = tuple(0.012 * x for x in n)
            side = _unit(_cross(n, along))
            if side[0] * (far[0] - c[0]) + side[1] * (far[1] - c[1]) + side[2] * (far[2] - c[2]) < 0:   # into the face, not off it
                side = tuple(-x for x in side)
            p0 = tuple(c[k] + off[k] for k in range(3))
            p1 = tuple(apex[k] + off[k] for k in range(3))
            q0 = tuple(p0[k] + w * side[k] for k in range(3))
            q1 = tuple(p1[k] + w * 0.3 * side[k] for k in range(3))   # narrowing up to the apex
            a.prim(zinc).face([p0, q0, q1, p1], n, a.basis(zinc, p0, along, side, seed), conf)


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


#: T-1881: on a joined curb, a jog shorter than this (a section's face set a little in from the
#: house's at a flush corner) carries no rail and one finial at its middle, not one at each end
JOG_M = 0.6
#: ... and a run of the joined rail as short as this is laid (a section's return between its
#: finials, 0.3-1 m on 1729's), where K10's own minimum would leave a gap in the one rail
JOINED_MIN_M = 0.25


def joined_outline(dk, decks):
    """T-1881: the joined curb: the union of the house's curb rectangle and each joined section's
    curb (each square to the plan) as one loop of (u, v) corners, walked with the decks on its
    left, collinear corners dropped. A section clear of the house's curb is refused."""
    u0, u1, v0, v1 = dk["curb"]
    rects = [(u0, v0, u1, v1)]
    for d in decks:
        us, vs = [q[0] for q in d["curb"]], [q[1] for q in d["curb"]]
        for q in d["curb"]:   # a section's curb is square to the plan: its corners on two u's and two v's
            if min(abs(q[0] - x) for x in (min(us), max(us))) > 1e-3 or min(abs(q[1] - y) for y in (min(vs), max(vs))) > 1e-3:
                raise ValueError(f"{d['bay']}: a joined section's curb stands square to the house's")
        rects.append((min(us), min(vs), max(us), max(vs)))
    xs = sorted({round(c, 4) for r in rects for c in (r[0], r[2])})
    ys = sorted({round(c, 4) for r in rects for c in (r[1], r[3])})
    inside = lambda x, y: any(r[0] < x < r[2] and r[1] < y < r[3] for r in rects)
    cov = {(i, j): inside((xs[i] + xs[i + 1]) / 2, (ys[j] + ys[j + 1]) / 2)
           for i in range(len(xs) - 1) for j in range(len(ys) - 1)}
    c = lambda i, j: cov.get((i, j), False)
    nxt = {}   # directed boundary edges, the covered cell on the left in (u, v)
    for (i, j), on in cov.items():
        if not on:
            continue
        if not c(i, j - 1):
            nxt[(i, j)] = (i + 1, j)
        if not c(i + 1, j):
            nxt[(i + 1, j)] = (i + 1, j + 1)
        if not c(i, j + 1):
            nxt[(i + 1, j + 1)] = (i, j + 1)
        if not c(i - 1, j):
            nxt[(i, j + 1)] = (i, j)
    start = min(nxt)
    loop, k = [start], nxt[start]
    while k != start:
        if len(loop) > len(nxt):
            raise ValueError("the joined curb is not one loop")
        loop.append(k)
        k = nxt[k]
    if len(loop) != len(nxt):
        raise ValueError("the joined curb is not one loop (a section stands clear of the house's curb)")
    pts = [(xs[i], ys[j]) for i, j in loop]
    keep = []
    for n, p in enumerate(pts):
        a, b = pts[n - 1], pts[(n + 1) % len(pts)]
        if abs((p[0] - a[0]) * (b[1] - p[1]) - (p[1] - a[1]) * (b[0] - p[0])) > 1e-9:
            keep.append(p)
    return keep


def dress_joined(a, dk, conf):
    """T-1881 (2026-11-02): one rail of the K10 kit's iron cresting round the house's deck and
    the decks of the sections joined to it (1729's, one curb and one rail over every section in
    the Detroit print), `inset_m` in from the joined curb, with a turned finial at each of its
    corners where the two runs' rail lines cross; the rail stops short of each finial. A short
    jog (JOG_M) carries one finial at its middle instead of two and no rail."""
    from . import k10_frontage
    from .k09_trim import lathe, Piece
    K = k10_frontage._kit()
    data = K.load()
    decks = getattr(a, "joined_decks", [])
    for d in decks:
        if abs(d["curb_m"] - dk["curb_m"]) > 1e-3:
            raise ValueError(f"{d['bay']}: a joined section's curb ({d['curb_m']} m) stands at the house's "
                             f"({dk['curb_m']} m)")
    cr, fn = dk["cresting"], dk["finials"]
    ins = cr["inset_m"]
    pitch = min([math.tan(math.radians(dk["deck_pitch_deg"]))] + [d["pitch"] for d in decks])
    y_cap = dk["curb_m"] + pitch * ins
    pts = joined_outline(dk, decks)
    n = len(pts)
    # the rail's loop: each corner moved `ins` in along both its runs' inward normals
    tan = [((pts[(k + 1) % n][0] - pts[k][0]), (pts[(k + 1) % n][1] - pts[k][1])) for k in range(n)]
    tan = [(t[0] / math.hypot(*t), t[1] / math.hypot(*t)) for t in tan]
    nin = [(-t[1], t[0]) for t in tan]          # the inside is on the left of each run
    rail = [(pts[k][0] + ins * (nin[k - 1][0] + nin[k][0]), pts[k][1] + ins * (nin[k - 1][1] + nin[k][1]))
            for k in range(n)]
    seg = [math.dist(rail[k], rail[(k + 1) % n]) for k in range(n)]
    jog = [s < JOG_M for s in seg]
    posts = {}   # where finials stand, keyed by corner (or by a jog's run, at its middle)
    for k in range(n):
        if jog[k] and jog[k - 1]:
            raise ValueError("the joined curb turns twice in a jog's length")
        if jog[k]:
            q0, q1 = rail[k], rail[(k + 1) % n]
            posts[("jog", k)] = ((q0[0] + q1[0]) / 2, (q0[1] + q1[1]) / 2)
        elif not jog[k - 1]:
            posts[("corner", k)] = rail[k]
    clear = fn["radius_m"] + FINIAL_CLEAR_M
    laid = {"cresting": [], "finials": [], "joined": [d["bay"] for d in decks]}
    for k in range(n):
        if jog[k]:
            continue
        q0, q1 = rail[k], rail[(k + 1) % n]
        s0 = clear + (seg[k - 1] / 2 if jog[k - 1] else 0.0)
        s1 = clear + (seg[(k + 1) % n] / 2 if jog[(k + 1) % n] else 0.0)
        L = seg[k] - s0 - s1
        if L < JOINED_MIN_M:   # a short return still carries its rail between its two finials
            continue
        t = tan[k]
        mu, mv = q0[0] + t[0] * (s0 + L / 2), q0[1] + t[1] * (s0 + L / 2)
        seed = a.instance(CRESTING, "cresting", {"length_m": round(L, 4), "ridge_cap_top_m": round(y_cap, 4),
                                                 "height_m": cr["height_m"], "host": "joined mansard deck",
                                                 "run": k}, {"ridge": (mu, y_cap, -mv)})
        var = K.Variant(dict(next(v for v in data["variants"] if v["id"] == CRESTING)), data)
        var.seed, var.rng = seed, random.Random(seed)
        got = var.cresting(0.0, L, y_cap, 0.0, host="joined mansard deck")
        _aim(var.pieces, mu, -mv, (t[0], -t[1]))     # the plan's (x, z) = (u, -v)
        top = max(q[1] for pc in var.pieces for q in pc.mesh.pos)
        _stretch(var.pieces, y_cap - 0.007, cr["height_m"] / (top - (y_cap - 0.007)))
        laid["cresting"].append({"run": k, "from": [round(c, 3) for c in q0], "to": [round(c, 3) for c in q1],
                                 "length_m": round(L, 3), "posts": len(got)})
        k10_frontage._lay(a, var.pieces, conf, CRESTING)
    foot = y_cap - LET_IN_M
    for key in sorted(posts):
        u, v = posts[key]
        name = f"{key[0]} {key[1]}"
        a.instance("k01.roof.deck_finial", "finial", {"height_m": fn["height_m"], "corner": name,
                                                       "host": "joined mansard deck"}, {"foot": (u, foot, -v)})
        pc = Piece(f"finial {name}", "iron", "rooted", host="joined mansard deck")
        lathe(pc.mesh, (u, -v), [(fn["radius_m"] * r, foot + fn["height_m"] * y) for r, y in FINIAL], FINIAL_SEGS)
        k10_frontage._lay(a, [pc], conf, "k01.roof.deck_finial")
        laid["finials"].append({"corner": name, "at": [round(u, 3), round(v, 3)], "foot_m": round(foot, 3)})
    a.deck = laid


def dress(a, dk, conf):
    """The cresting along each side of the curb and a finial at every corner (module doc)."""
    if (dk.get("cresting") or {}).get("joined"):
        return dress_joined(a, dk, conf)
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

    xr = dk.get("cross_roof")
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
            if xr:   # T-1890: the run stops short of a pavilion's cross roof through its corner
                if side == "street":
                    s0, s1 = ((xr["v_m"][1] + CROSS_CLEAR_M, s1) if xr["corner"] == "street_south"
                              else (s0, xr["v_m"][0] - CROSS_CLEAR_M))
                elif xr["corner"] in (c_lo, c_hi):
                    s1 = xr["end_u_m"] - CROSS_CLEAR_M
                    if xr.get("hood"):   # ... and short of the hood on its end
                        s1 = min(s1, xr["hood"]["u_m"][0] - CORNER_CLEAR_M)
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
            if cr.get("painted"):
                for pc in var.pieces:
                    pc.role = "timber"
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
        for name in CORNERS + (("cross_roof",) if xr else ()):
            if xr and name == xr["corner"]:
                continue   # T-1890: under the pavilion's cross roof, whose ridge's end carries it
            if name == "cross_roof" and xr.get("hood"):   # on its hood's apex, over the end
                x, z = xr["end_u_m"], -xr["ridge_v_m"]
                foot, host = xr["hood"]["apex_m"] - LET_IN_M, "cross roof hood"
            elif name == "cross_roof":
                x, z = xr["end_u_m"] + fn["radius_m"], -xr["ridge_v_m"]
                foot, host = xr["ridge_m"] - LET_IN_M, "cross roof"
            else:
                u, v, su, sv = _corner(dk, name)
            if name == "cross_roof":
                pass
            elif name in hd["corners"]:
                c = HOOD_INSET_M + hd["base_m"] / 2
                foot = dk["curb_m"] + hd["rise_m"] - LET_IN_M
                host = "corner hood"
            else:
                c = FINIAL_INSET_M
                foot = deck_y(dk, c) - LET_IN_M
                host = "mansard deck"
            if name != "cross_roof":
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
