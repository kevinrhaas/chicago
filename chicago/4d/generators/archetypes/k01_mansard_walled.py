"""T-3384: a K01 mansard run straight into a side wall carried up through it — 1700-1706 Prairie.

TICKET T-3384 (the owner, 2026-11-05, with Chicagology's photograph and the Glessner House
Museum's Christmas print of the pair). K05's mansard (T-2370) rings all four walls, so the two
houses of the pair were each hipped at the party line: two hips crossing in a valley over the
party wall, a brick slab standing up out of the valley. The photographs show ONE mansard run
across the pair: its street face continuous from end to end, and the party wall carried up
through it, its coping a broad pale band following the roof's own section from the cornice up
the steep face to the deck and on over it, a stack standing on it just behind the deck's
railing; 1700's north end wall is carried up the same way past its end of the roof, its coping
falling down the steep face to the cornice at the corner, a stack on it behind the railing.

The record names each such wall as its mansard's `walled_ends`:

  resolve()       bounded: the wall (south or north, once each), `party` (the wall is shared:
                  each house of the pair carries the half on its own side of the line, so the
                  two halves meet on it and read as one wall centred on the party line), the
                  parapet's `upstand_m` over the roof, square to the slope, and its thickness
                  (the side wall's, or the record's half of a party wall). The mansard's deck
                  then runs on to the wall, so its ridge is the one a roof as long as the pair
                  rises to: a low ridge along the street, not a hip's apex
  extend()        the ring rectangle K05 builds the mansard on, carried on far past each walled
                  end, so the hips there stand outside the house and only the ridged section
                  reaches the wall
  elements()      before the union: on each walled end a brick slab on the wall head whose top
                  follows the roof's section `upstand_m` over it, from the rear fascia to the
                  front, and a coping band along that top (`drip_m` over the roof's side; on a
                  party wall none over the line, where the neighbour's half meets it); each
                  stack the record stands in the wall (`chimneys[].wall_end`), its box stopped on
                  the wall's plane. After it, two cutters outside the wall's plane take the rest
                  of the extended roof away, as k01_mansard_straight's do: over the wall from
                  under the soffit to the wall head SKIN_M proud of its face (`wall`, never
                  emitted), and from the wall head (the eaves' boxes from under the soffit) to
                  under the parapet's top on the plane itself (`parapet`: the wall's brick
                  closes the roof's section)
  cornice_cut()   the wall heads the walled ends take, in K10's perimeter s: no brackets and no
                  bed moulding run along them
  gutter_dead()   the gutter's runs they take; each live run stopped at the wall's outer plane

docs/LIBERTIES.md L-k01-1700-1706-roof-3384 says which numbers are read and which reconstructed.
"""

from __future__ import annotations

import math

WALLS = ("south", "north")
SKIN_M = 0.002          # as k01_mansard_straight.SKIN_M: the lower cut stands this far proud of the wall face
END_IN_M = 0.02         # the parapet's ends stand this far inside the fascia's line, front and rear
UPSTAND_M = (0.15, 0.6)  # the parapet's top over the roof, square to the slope
KNEELER_M = 0.25        # the parapet's top over the wall head at the fascia, front and rear
EXTEND_M = 4.0          # how far past the depth the rings run on beyond a walled end


def _err(msg):
    from .k01_frontage_params import ParamError
    return ParamError(f"mansard.walled_ends: {msg}")


def resolve(ends, m: dict, *, depth: float, width: float, eave: float, pitch: float, overhang: float,
            side_wall: float, dormers: list, k5: dict) -> list:
    """The record's `mansard.walled_ends`, bounded, and the mansard's ridge moved to the one the
    run-on roof rises to (`m` is the resolved mansard, changed in place)."""
    if not isinstance(ends, list) or not ends:
        raise _err("a list of the side walls carried up through the roof")
    if m.get("side_parapet") or m.get("crown") or m.get("straight"):
        raise _err("a walled end is a side wall carried through a plain mansard: no side parapet, crown "
                   "or straight wall beside it")
    out, seen = [], set()
    cp = k5["parts"]["coping"]
    for e in ends:
        if set(e) - {"wall", "party", "upstand_m", "thickness_m", "coping_m"} or "wall" not in e:
            raise _err(f"each names its wall, and optionally party, upstand_m, thickness_m, coping_m (not {sorted(e)})")
        w = e["wall"]
        if w not in WALLS or w in seen:
            raise _err(f"wall {w!r}: south or north, once each")
        seen.add(w)
        party = e.get("party", False)
        if party not in (True, False):
            raise _err("party: true for a wall shared with the house beyond it")
        up = float(e.get("upstand_m", 0.3))
        if not UPSTAND_M[0] <= up <= UPSTAND_M[1]:
            raise _err(f"upstand_m {up}: {UPSTAND_M[0]}-{UPSTAND_M[1]} m over the roof")
        tw = float(e.get("thickness_m", side_wall))
        if not 0.15 <= tw <= side_wall + 1e-9:
            raise _err(f"thickness_m {tw}: 0.15 m up to the side wall's {side_wall} m (a party wall's half)")
        cop = float(e.get("coping_m", cp["thickness_m"]))
        if not cp["thickness_m"] <= cop <= 0.3:
            raise _err(f"coping_m {cop}: {cp['thickness_m']}-0.3 m")
        if any(d.get("face") == w for d in dormers):
            raise _err(f"a dormer on the {w} face: that face is the wall's, carried up")
        out.append({"wall": w, "party": party, "upstand_m": up, "thickness_m": tw, "coping_m": cop,
                    "drip_m": float(cp["drip_m"])})
    # the deck runs on to the walls, so its low hip is a ridge along the street over the depth's middle
    run = m["lower_rise_m"] / math.tan(math.radians(m["lower_pitch_deg"]))
    half = depth / 2 + overhang
    if width + overhang * 2 + EXTEND_M < depth + overhang * 2:
        raise _err("the run-on roof is shorter than the house is deep")
    m["ridge_m"] = round(eave + m["lower_rise_m"] + (half - run) * math.tan(math.radians(pitch)), 4)
    return out


def extend(p, z0: float, z1: float) -> tuple[float, float]:
    """The ring rectangle's z0..z1 (z = -v) carried on past each walled end."""
    for e in p.mansard["walled_ends"]:
        if e["wall"] == "south":
            z1 += p.depth_m + EXTEND_M
        else:
            z0 -= p.depth_m + EXTEND_M
    return z0, z1


def section(p) -> list:
    """The roof's top on a walled end's plane, from the rear fascia to the front, as (u, y): the
    lower faces (their curve, where the variant bows them), the curbs and the deck's ridge."""
    m, D, o, E = p.mansard, p.depth_m, p.eave_overhang_m, p.eave_m
    rise = m["lower_rise_m"]
    run = rise / math.tan(math.radians(m["lower_pitch_deg"]))
    L = math.hypot(run, rise)
    P0, P2 = (0.0, E), (run, E + rise)
    nrm = (-(P2[1] - P0[1]) / L, (P2[0] - P0[0]) / L)
    sgn = 1.0 if m["profile"] == "convex" else -1.0
    mid = ((P0[0] + P2[0]) / 2, (P0[1] + P2[1]) / 2)
    P1 = (mid[0] + sgn * m["bulge"] * L * nrm[0], mid[1] + sgn * m["bulge"] * L * nrm[1])
    n = m["segments"]
    face = []
    for k in range(n + 1):
        t = k / n
        face.append(((1 - t) ** 2 * P0[0] + 2 * (1 - t) * t * P1[0] + t * t * P2[0],
                     (1 - t) ** 2 * P0[1] + 2 * (1 - t) * t * P1[1] + t * t * P2[1]))
    X0, X1 = -o, D + o
    rear = [(X0 + i, y) for i, y in face]
    front = [(X1 - i, y) for i, y in reversed(face)]
    return rear + [((X0 + X1) / 2, m["ridge_m"])] + front


def _meet(a, d, b, e):
    """Where the line a + t d meets b + s e."""
    den = d[0] * e[1] - d[1] * e[0]
    t = ((b[0] - a[0]) * e[1] - (b[1] - a[1]) * e[0]) / den
    return (a[0] + t * d[0], a[1] + t * d[1])


def offset(line, h: float, ua: float, ub: float, foot: float | None = None) -> list:
    """`line` (u increasing) moved `h` square to each of its runs, upward, its ends cut at u = ua, ub;
    or, with `foot`, each end's steep run brought down from the curb to `foot` at ua or ub, so the
    upstand tapers down the steep face and the coping lands on the cornice's top."""
    segs = []
    for (x0, y0), (x1, y1) in zip(line, line[1:]):
        L = math.hypot(x1 - x0, y1 - y0)
        d = ((x1 - x0) / L, (y1 - y0) / L)
        segs.append(((x0 - d[1] * h, y0 + d[0] * h), d))
    mid = [_meet(a, d, b, e) for (a, d), (b, e) in zip(segs, segs[1:])]
    if foot is None:
        return ([_meet(segs[0][0], segs[0][1], (ua, 0.0), (0.0, 1.0))] + mid
                + [_meet(segs[-1][0], segs[-1][1], (ub, 0.0), (0.0, 1.0))])
    return [(ua, foot)] + mid + [(ub, foot)]


def _plane(p, e):
    """The wall's outer plane (z) and the sign out of the house."""
    return (0.0, 1.0) if e["wall"] == "south" else (-p.width_m, -1.0)


def stack_solids(p, k5, c, hs):
    """A stack standing in a walled end (`wall_end`): its shaft and cap, each stopped on the
    wall's plane (a party wall's stack is centred on the line: this house builds its half)."""
    e = next(x for x in p.mansard["walled_ends"] if x["wall"] == c["wall_end"])
    plane, sg = _plane(p, e)
    sx, sz = c["plan_m"]
    u, z = c["u_m"], -c["v_m"]
    cp, cd, top = c["cap_proud_m"], c["cap_depth_m"], c["top_m"]
    lo_z, hi_z = z - sz / 2, z + sz / 2
    clo, chi = lo_z - cp, hi_z + cp
    if sg > 0:
        hi_z, chi = min(hi_z, plane), min(chi, plane)
    else:
        lo_z, clo = max(lo_z, plane), max(clo, plane)
    P = k5.frame("z")
    y0 = hs - 0.5
    return [k5.extrude([(u - sx / 2, y0), (u + sx / 2, y0), (u + sx / 2, top - cd / 2), (u - sx / 2, top - cd / 2)],
                       lo_z, hi_z, P, lambda i, p_, q_: "chimney" if i != 2 else "hidden", "chimney", "chimney"),
            k5.extrude([(u - sx / 2 - cp, top - cd), (u + sx / 2 + cp, top - cd), (u + sx / 2 + cp, top),
                        (u - sx / 2 - cp, top)], clo, chi, P, "coping", "coping", "coping")]


def elements(p, k5, hs: float):
    """The parapets and stacks (joined before the union) and the cutters (taken away after it),
    in the K01 frame (x = u, z = -v)."""
    D, o, E = p.depth_m, p.eave_overhang_m, p.eave_m
    sec = section(p)
    ua, ub = -o + END_IN_M, D + o - END_IN_M
    far, lo = o + 2.0, hs - 0.5
    Pz, Px = k5.frame("z"), k5.frame("x")
    solids, cutters = [], []
    for e in p.mansard["walled_ends"]:
        plane, sg = _plane(p, e)
        tw, up, cop, dr = e["thickness_m"], e["upstand_m"], e["coping_m"], e["drip_m"]
        inner = plane - sg * tw
        top = offset(sec, up, ua, ub, E + KNEELER_M)
        cap = offset(sec, up + cop, ua, ub, E + KNEELER_M + cop)
        zi, zo = sorted((inner, plane))
        solids.append(k5.extrude([(ua, E), (ub, E)] + list(reversed(top)), zi, zo, Pz,
                                 lambda i, p_, q_: "base" if i == 0 else "parapet", "parapet", "parapet"))
        # the coping: over the roof's side by the drip; over the line none on a party wall, where
        # the neighbour's half meets this one, else the drip there too
        ci, co = inner - sg * dr, plane + (0.0 if e["party"] else sg * dr)
        solids.append(k5.extrude(list(top) + list(reversed(cap)), min(ci, co), max(ci, co), Pz,
                                 "coping", "coping", "coping"))
        # the cutters, outside the plane: over the wall to the wall head SKIN_M proud of its face
        out, sk = sg * (D + EXTEND_M + far), sg * SKIN_M   # out past the far end of the run-on roof
        cutters.append(k5.extrude([(plane + out, lo), (plane + sk, lo), (plane + sk, E), (plane + out, E)],
                                  0.0, D, Px, "wall", "parapet", "parapet"))
        # ... and on the plane, from the wall head (the eaves' boxes from under the soffit) to half
        # the upstand over the roof: under the coping's drip, over everything the roof has
        lid = [(u, y + up / 2) for u, y in sec]
        outline = [(-far, lo), (0.0, lo), (0.0, E), (D, E), (D, lo), (D + far, lo),
                   (D + far, lid[-1][1])] + list(reversed(lid)) + [(-far, lid[0][1])]
        zc = sorted((plane, plane + out))
        cutters.append(k5.extrude(outline, zc[0], zc[1], Pz, "wall",
                                  "parapet" if sg > 0 else "hidden", "parapet" if sg < 0 else "hidden"))
    for c in p.chimneys:
        if c.get("wall_end"):
            solids += stack_solids(p, k5, c, hs)
    return solids, cutters


def wall_ends(p) -> list:
    return list(((getattr(p, "mansard", None) or {}).get("walled_ends")) or [])


def cornice_cut(p) -> list:
    """The walled ends' runs of the wall head, in K10's perimeter s (the street front from
    south to north, then north from the front, the rear from north to south, the south from
    the rear): no eave box stands on them, so no bracket and no bed moulding."""
    D, W = p.depth_m, p.width_m
    return [(W, W + D) if e["wall"] == "north" else (2 * W + D, 2 * W + 2 * D) for e in wall_ends(p)]


# -- the deck's fret railing ------------------------------------------------------------------

#: T-3384: the white fret along 1700-1706's deck, as Chicagology's photograph shows it close: square
#: posts about a metre apart under a moulded rail on a bottom rail, and in each panel one bar
#: corner to corner, from the top at one post down to the foot of the next, with a rectilinear
#: key in each triangle it leaves, the upper one the lower turned half round. In the panel's
#: unit square (0, 0) is the foot of the panel's first post and (1, 1) the head of the next.
FRET_KEYS = (((0.0, 0.55), (0.3, 0.55), (0.3, 0.18), (0.12, 0.18), (0.12, 0.38)),
             ((0.56, 0.0), (0.56, 0.3), (0.44, 0.3)))
FRET = {"post_m": 0.09, "rail_m": 0.07, "cap_depth_m": 0.1, "bar_m": 0.035,
        "post_d": 0.09, "rail_d": 0.07, "bar_d": 0.04, "key_d": 0.032, "let_in_m": 0.03}


def _band(pts, hw, start_in=0.0):
    """An orthogonal or straight polyline thickened `hw` each side into one simple polygon, its
    first end carried `start_in` on past its first point (into what it springs from)."""
    if start_in:
        (x0, y0), (x1, y1) = pts[0], pts[1]
        L = math.hypot(x1 - x0, y1 - y0)
        pts = [(x0 - (x1 - x0) / L * start_in, y0 - (y1 - y0) / L * start_in)] + list(pts[1:])
    segs = []
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        L = math.hypot(x1 - x0, y1 - y0)
        segs.append(((x1 - x0) / L, (y1 - y0) / L))
    left, right = [], []
    for k, q in enumerate(pts):
        ds = [segs[j] for j in (k - 1, k) if 0 <= j < len(segs)]
        if len(ds) == 1:
            d = ds[0]
            left.append((q[0] - d[1] * hw, q[1] + d[0] * hw))
            right.append((q[0] + d[1] * hw, q[1] - d[0] * hw))
        else:
            for out, sg in ((left, 1.0), (right, -1.0)):
                a = (pts[k - 1][0] - sg * ds[0][1] * hw, pts[k - 1][1] + sg * ds[0][0] * hw)
                b = (q[0] - sg * ds[1][1] * hw, q[1] + sg * ds[1][0] * hw)
                out.append(_meet(a, ds[0], b, ds[1]))
    return left + list(reversed(right))


def fret_pieces(L: float, y0: float, height: float, panel: float, host: str):
    """The fret railing `L` long along X about the origin, its foot at y0, `height` high, in panels
    of about `panel` between posts; one piece per part, in the eave's painted timber."""
    from .k09_trim import Piece, box, prism
    F = FRET
    n = max(1, round((L - F["post_m"]) / panel))
    pw, rh, H = F["post_m"], F["rail_m"], height
    step = (L - pw) / n
    xs = [-L / 2 + pw / 2 + k * step for k in range(n + 1)]
    out = []
    pc = Piece("fret posts", "timber", "rooted", host=host)
    for x in xs:
        box(pc.mesh, x - pw / 2, x + pw / 2, y0 - F["let_in_m"], y0 + H - 0.03, -F["post_d"] / 2, F["post_d"] / 2)
    out.append(pc)
    pc = Piece("fret rails", "timber", "open", host=host)
    box(pc.mesh, -L / 2 + 0.01, L / 2 - 0.01, y0, y0 + rh, -F["rail_d"] / 2, F["rail_d"] / 2)
    box(pc.mesh, -L / 2 + 0.005, L / 2 - 0.005, y0 + H - rh, y0 + H, -F["cap_depth_m"] / 2, F["cap_depth_m"] / 2)
    out.append(pc)
    bars = Piece("fret bars", "timber", "open", host=host)
    keys = Piece("fret keys", "timber", "open", host=host)
    hw, e = F["bar_m"] / 2, 0.01
    for x_l, x_r in zip(xs, xs[1:]):
        xa, xb, ya, yb = x_l + pw / 2, x_r - pw / 2, y0 + rh, y0 + H - rh
        w, h = xb - xa, yb - ya
        # the bar corner to corner, its ends let into the post and the rails
        xa_, xb_, ya_, yb_ = xa - e, xb + e, ya - e, yb + e
        al = math.atan2(yb_ - ya_, xb_ - xa_)
        sx, sy = hw / math.sin(al), hw / math.cos(al)
        prism(bars.mesh, [(xa_, yb_), (xa_ + sx, yb_), (xb_, ya_ + sy), (xb_, ya_), (xb_ - sx, ya_), (xa_, yb_ - sy)],
              -F["bar_d"] / 2, F["bar_d"] / 2, back=True)
        for key in FRET_KEYS:
            for turn in (False, True):
                q = [((1 - fx) if turn else fx, (1 - fy) if turn else fy) for fx, fy in key]
                poly = _band([(xa + fx * w, ya + fy * h) for fx, fy in q], hw, start_in=e)
                prism(keys.mesh, poly, -F["key_d"] / 2, F["key_d"] / 2, back=True)
    out += [bars, keys]
    return out
