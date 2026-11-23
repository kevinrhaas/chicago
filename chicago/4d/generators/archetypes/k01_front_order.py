"""A brick street front's order, laid on the K01 frontage (T-3722).

The record names it `front_order` and this module builds it on the street front, in that
wall's frame (s along the front from its low-s, south end; y over grade; d out of the wall):

  k01.front.pilaster        a brick pilaster strip between two bays, `proud_m` out of the
                            front, from `from_m` up to the capital, in the front's own brick
  k01.front.ionic_capital   its head under the entablature: a bell, a pair of volutes (each a
                            disc with its eye standing prouder), the channel between them and
                            a thin abacus over all, in the front's dressed stone
  k01.front.panel           a plain stone panel let into the brick between two storeys; or,
                            `carved`, a panel with a palmette and two rosettes in relief
  k01.front.keystone        a key block over a flat lintel, splayed wider at its head and
                            standing proud of the lintel it rises out of
  k01.front.scroll          a stone scroll stop at a corner of the front (or both): a console whose
                            back stands against the corner and whose top sweeps down and out
                            to a volute, on a brick pier of its own

2126 Prairie's, off its May 1905 Inland Architect plate (`inland_architect_1905_05_robbins_plate`):
four Ionic pilaster heads between the five bays under the entablature, the marble panels
between the principal and chamber storeys with the carved one over the door, the keyed
lintels and the scrolled marble stops at both corners. The carving and the volutes are
stated forms, not traced ones (docs/LIBERTIES.md L-k01-robbins-2126-3722). A record that does
not name `front_order` is the same bytes as before.
"""

from __future__ import annotations

import math

WALL = "k01.wall.street_front"
KEYS = {"pilasters", "panels", "keystones", "scroll"}
PILASTER_KEYS = {"at_m", "width_m", "proud_m", "from_m", "to_m", "capital"}
CAPITAL_KEYS = {"height_m", "width_m", "volute_m"}
PANEL_KEYS = {"at_m", "width_m", "y_m", "carved"}
KEY_KEYS = {"at_m", "y_m", "width_m", "proud_m"}
SCROLL_KEYS = {"side", "width_m", "pier_top_m", "top_m", "depth_m"}
DISC_SIDES = 16
PANEL_PROUD_M = 0.035
CARVING_PROUD_M = 0.03     # the carving stands this much proud of its panel
SCROLL_SLICES = 10


class ParamError(ValueError):
    pass


def _num(x, what):
    if isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x):
        raise ParamError(f"front_order: {what} must be a number, not {x!r}")
    return float(x)


def resolve(spec, *, width, floor, eave) -> dict:
    """The record's `front_order`, checked against the main block (module doc)."""
    if not spec:
        return {}
    if not isinstance(spec, dict) or not set(spec) or set(spec) - KEYS:
        raise ParamError(f"front_order takes one or more of {sorted(KEYS)}")
    out = {}
    pl = spec.get("pilasters")
    if pl is not None:
        if not isinstance(pl, dict) or set(pl) != PILASTER_KEYS or not isinstance(pl["capital"], dict) \
                or set(pl["capital"]) != CAPITAL_KEYS or not isinstance(pl["at_m"], list) or not pl["at_m"]:
            raise ParamError(f"front_order.pilasters takes {sorted(PILASTER_KEYS)}, its capital "
                             f"{sorted(CAPITAL_KEYS)}")
        w, d, y0, y1 = (_num(pl[k], f"pilasters.{k}") for k in ("width_m", "proud_m", "from_m", "to_m"))
        ch, cw, vr = (_num(pl["capital"][k], f"pilasters.capital.{k}") for k in ("height_m", "width_m", "volute_m"))
        at = [_num(s, "pilasters.at_m") for s in pl["at_m"]]
        if not (0.2 <= w <= 0.8 and 0.02 <= d <= 0.15 and 0.15 <= ch <= 0.6 and w <= cw <= 1.4
                and 0.06 <= vr <= min(0.25, ch * 0.6)):
            raise ParamError("front_order.pilasters: a shaft 0.2-0.8 m broad and 0.02-0.15 m proud, a capital "
                             "0.15-0.6 m high and as broad as the shaft up to 1.4 m, volutes 0.06-0.25 m")
        if not (0.0 <= y0 <= floor + 1e-6 and y1 <= eave + 1e-6 and y1 - y0 >= ch + 2.0):
            raise ParamError(f"front_order.pilasters: from_m {y0} at or under the principal floor ({floor} m), "
                             f"to_m {y1} under the {eave:.2f} m eave, two metres of shaft under the capital")
        if any(not cw / 2 <= s <= width - cw / 2 for s in at) or sorted(at) != at \
                or any(b - a < cw for a, b in zip(at, at[1:])):
            raise ParamError(f"front_order.pilasters.at_m {at}: in order along the {width} m front, the capitals "
                             f"clear of its ends and of one another")
        out["pilasters"] = {"at_m": at, "width_m": w, "proud_m": d, "from_m": y0, "to_m": y1,
                            "capital": {"height_m": ch, "width_m": cw, "volute_m": vr}}
    pn = spec.get("panels")
    if pn is not None:
        if not isinstance(pn, list) or not pn:
            raise ParamError("front_order.panels is a list of panels")
        rows = []
        for i, q in enumerate(pn):
            if not isinstance(q, dict) or set(q) != PANEL_KEYS or not isinstance(q["carved"], bool) \
                    or not isinstance(q["y_m"], list) or len(q["y_m"]) != 2:
                raise ParamError(f"front_order.panels[{i}] takes {sorted(PANEL_KEYS)} (y_m [foot, head], carved "
                                 f"true or false)")
            s, w = _num(q["at_m"], "panels.at_m"), _num(q["width_m"], "panels.width_m")
            a, b = (_num(y, "panels.y_m") for y in q["y_m"])
            if not (0.3 <= w <= 2.5 and 0.1 <= b - a <= 1.2 and w / 2 <= s <= width - w / 2
                    and floor <= a and b <= eave):
                raise ParamError(f"front_order.panels[{i}]: 0.3-2.5 m across and 0.1-1.2 m high, on the front "
                                 f"between the principal floor and the eave")
            rows.append({"at_m": s, "width_m": w, "y_m": [a, b], "carved": q["carved"]})
        out["panels"] = rows
    ks = spec.get("keystones")
    if ks is not None:
        if not isinstance(ks, list) or not ks:
            raise ParamError("front_order.keystones is a list of rows")
        rows = []
        for i, q in enumerate(ks):
            if not isinstance(q, dict) or set(q) != KEY_KEYS or not isinstance(q["at_m"], list) or not q["at_m"] \
                    or not isinstance(q["y_m"], list) or len(q["y_m"]) != 2:
                raise ParamError(f"front_order.keystones[{i}] takes {sorted(KEY_KEYS)}")
            w, d = _num(q["width_m"], "keystones.width_m"), _num(q["proud_m"], "keystones.proud_m")
            a, b = (_num(y, "keystones.y_m") for y in q["y_m"])
            at = [_num(s, "keystones.at_m") for s in q["at_m"]]
            if not (0.1 <= w <= 0.5 and 0.02 <= d <= 0.2 and 0.15 <= b - a <= 0.8 and floor <= a and b <= eave) \
                    or any(not w <= s <= width - w for s in at):
                raise ParamError(f"front_order.keystones[{i}]: 0.1-0.5 m broad, 0.02-0.2 m proud, 0.15-0.8 m high, "
                                 f"on the front")
            rows.append({"at_m": at, "y_m": [a, b], "width_m": w, "proud_m": d})
        out["keystones"] = rows
    sc = spec.get("scroll")
    if sc is not None:
        if not isinstance(sc, dict) or set(sc) != SCROLL_KEYS or sc["side"] not in ("low", "high", "both"):
            raise ParamError(f"front_order.scroll takes {sorted(SCROLL_KEYS)}, its side low (s 0), high or both")
        w, y0, y1, dp = (_num(sc[k], f"scroll.{k}") for k in ("width_m", "pier_top_m", "top_m", "depth_m"))
        if not (0.4 <= w <= 1.6 and 0.5 <= y0 <= 3.5 and 0.6 <= y1 - y0 <= 2.0 and 0.2 <= dp <= 0.8):
            raise ParamError("front_order.scroll: 0.4-1.6 m across, its pier 0.5-3.5 m high, the scroll 0.6-2.0 m "
                             "over it and 0.2-0.8 m deep")
        out["scroll"] = {"side": sc["side"], "width_m": w, "pier_top_m": y0, "top_m": y1, "depth_m": dp}
    return out


def _P(frame, s, y, d):
    from .k01_frontage import Y, _add, _mul
    O, R, N = frame
    return _add(_add(_add(O, _mul(R, s)), _mul(Y, y)), _mul(N, d))


def _box(a, mat, frame, s0, s1, y0, y1, d0, d1, seed, conf, skip=()):
    """A closed box in the wall's frame; `skip` names the faces it leaves off
    ("s0", "s1", "y0", "y1", "d0") where something else stands against them."""
    from .k01_frontage import Y, _mul
    O, R, N = frame
    pr = a.prim(mat)
    P = lambda s, y, d: _P(frame, s, y, d)
    faces = {
        "d1": ([P(s0, y0, d1), P(s1, y0, d1), P(s1, y1, d1), P(s0, y1, d1)], N, (O, R, Y)),
        "d0": ([P(s0, y0, d0), P(s1, y0, d0), P(s1, y1, d0), P(s0, y1, d0)], _mul(N, -1.0), (O, _mul(R, -1.0), Y)),
        "s0": ([P(s0, y0, d0), P(s0, y0, d1), P(s0, y1, d1), P(s0, y1, d0)], _mul(R, -1.0), (P(s0, 0, 0), N, Y)),
        "s1": ([P(s1, y0, d0), P(s1, y0, d1), P(s1, y1, d1), P(s1, y1, d0)], R, (P(s1, 0, 0), _mul(N, -1.0), Y)),
        "y1": ([P(s0, y1, d0), P(s1, y1, d0), P(s1, y1, d1), P(s0, y1, d1)], Y, (O, R, _mul(N, -1.0))),
        "y0": ([P(s0, y0, d0), P(s1, y0, d0), P(s1, y0, d1), P(s0, y0, d1)], _mul(Y, -1.0), (O, R, N)),
    }
    for k, (pts, n, (o, r, u)) in faces.items():
        if k not in skip:
            _face(a, pr, mat, pts, n, o, r, u, seed, conf)


def _disc(s, y, r, n=DISC_SIDES):
    return [(s + r * math.cos(2 * math.pi * k / n), y + r * math.sin(2 * math.pi * k / n)) for k in range(n)]


def dress(a, frames):
    """Lay the record's `front_order` on the street front (module doc)."""
    from .k01_dressings import prism
    p, fo = a.p, a.p.front_order
    conf = max(p.conf("front_order"), p.conf("footprint"))
    frame = frames[WALL][0][0]
    brick, trim, carved = a.front_brick, "limestone_trim", "carved_trim"
    meta = {}
    pl = fo.get("pilasters")
    if pl:
        w, d, y0, y1 = pl["width_m"], pl["proud_m"], pl["from_m"], pl["to_m"]
        ch, cw, vr = pl["capital"]["height_m"], pl["capital"]["width_m"], pl["capital"]["volute_m"]
        yc = y1 - ch                                   # the shaft's top, the capital's bed
        yv = y1 - ch * 0.45                            # the volutes' eyes
        for s in pl["at_m"]:
            seed = a.instance("k01.front.pilaster", "masonry", {"width_m": w, "proud_m": d},
                              {"foot": _P(frame, s, y0, 0.0), "head": _P(frame, s, yc, 0.0)})
            prism(a, brick, frame, [(s - w / 2, y0), (s + w / 2, y0), (s + w / 2, yc), (s - w / 2, yc)],
                  0.0, d, seed, conf)
            seed = a.instance("k01.front.ionic_capital", "trim", {"height_m": ch, "width_m": cw, "volute_m": vr},
                              {"bed": _P(frame, s, yc, 0.0)})
            bw = w / 2 + 0.03                          # the bell, a little broader than the shaft
            prism(a, trim, frame, [(s - bw, yc), (s + bw, yc), (s + bw, yv), (s - bw, yv)], 0.0, d + 0.04, seed, conf)
            ve = cw / 2 - vr                           # each volute's eye, off the axis
            prism(a, trim, frame, [(s - ve, yv), (s + ve, yv), (s + ve, yv + vr), (s - ve, yv + vr)],
                  0.0, d + 0.055, seed, conf)          # the channel between them
            for sv in (s - ve, s + ve):
                prism(a, trim, frame, _disc(sv, yv, vr), 0.0, d + 0.075, seed, conf)
                prism(a, trim, frame, _disc(sv, yv, vr * 0.38, 10), 0.0, d + 0.105, seed, conf)
            aw = cw / 2 - vr * 0.4                     # the abacus over the channel, under the entablature
            prism(a, trim, frame, [(s - aw, y1 - 0.06), (s + aw, y1 - 0.06), (s + aw, y1), (s - aw, y1)],
                  0.0, d + 0.085, seed, conf)
        meta["pilasters"] = {"at_m": pl["at_m"], "capital_top_m": y1}
    for q in fo.get("panels", ()):
        s, w, (ya, yb) = q["at_m"], q["width_m"], q["y_m"]
        seed = a.instance("k01.front.panel", "trim", {"width_m": w, "height_m": round(yb - ya, 4),
                                                       "carved": q["carved"]}, {"centre": _P(frame, s, ya, 0.0)})
        prism(a, trim, frame, [(s - w / 2, ya), (s + w / 2, ya), (s + w / 2, yb), (s - w / 2, yb)],
              0.0, PANEL_PROUD_M, seed, conf)
        if q["carved"]:
            h, ym, top = yb - ya, (ya + yb) / 2, PANEL_PROUD_M + CARVING_PROUD_M
            # a palmette on the axis: a fan of five leaves off a small base
            for k in range(5):
                t = math.radians(-50 + 25 * k)
                ln = h * (0.36 if k in (0, 4) else 0.42)
                bx, by = s, ya + h * 0.18
                tx, ty = bx + ln * math.sin(t), by + ln * math.cos(t)
                nx, ny = math.cos(t) * h * 0.05, -math.sin(t) * h * 0.05
                prism(a, carved, frame, [(bx - nx * 0.4, by - ny * 0.4), (bx + nx * 0.4, by + ny * 0.4),
                                         (tx + nx, ty + ny), (tx - nx, ty - ny)], PANEL_PROUD_M, top, seed, conf)
            # and a rosette and a running leaf either side of it
            for sgn in (-1, 1):
                prism(a, carved, frame, _disc(s + sgn * w * 0.3, ym, h * 0.24, 12), PANEL_PROUD_M, top, seed, conf)
                x0, x1 = s + sgn * w * 0.12, s + sgn * w * 0.44
                lo, hi = (x0, x1) if sgn > 0 else (x1, x0)
                prism(a, carved, frame, [(lo, ya + h * 0.12), (hi, ya + h * 0.12), (hi, ya + h * 0.22), (lo, ya + h * 0.22)],
                      PANEL_PROUD_M, top - 0.012, seed, conf)
    if fo.get("panels"):
        meta["panels"] = len(fo["panels"])
    for q in fo.get("keystones", ()):
        w, d, (ya, yb) = q["width_m"], q["proud_m"], q["y_m"]
        for s in q["at_m"]:
            seed = a.instance("k01.front.keystone", "trim", {"width_m": w, "proud_m": d},
                              {"foot": _P(frame, s, ya, 0.0)})
            prism(a, trim, frame, [(s - w / 2, ya), (s + w / 2, ya), (s + w * 0.62, yb), (s - w * 0.62, yb)],
                  0.0, d, seed, conf)
    if fo.get("keystones"):
        meta["keystones"] = sum(len(q["at_m"]) for q in fo["keystones"])
    sc = fo.get("scroll")
    if sc:
        for side in (("low", "high") if sc["side"] == "both" else (sc["side"],)):
            _scroll(a, frame, dict(sc, side=side), p.width_m, brick, trim, conf)
        meta["scroll"] = sc["side"]
    a.front_order_meta = meta


def _face(a, pr, mat, pts, n, origin, right, up, seed, conf):
    """One planar face, its corners turned so their winding agrees with its normal `n`."""
    from .k01_frontage import _cross, _dot, _sub
    if _dot(_cross(_sub(pts[1], pts[0]), _sub(pts[2], pts[0])), n) < 0:
        pts = list(reversed(pts))
    pr.face(pts, n, a.basis(mat, origin, right, up, seed), conf)


def _scroll(a, frame, sc, width, brick, trim, conf):
    """The corner's scroll stop on its pier, both beyond the front's end and against it."""
    from .k01_dressings import prism
    from .k01_frontage import Y, _add, _mul, _sub
    O, R, N = frame
    w, y0, y1, dp = sc["width_m"], sc["pier_top_m"], sc["top_m"], sc["depth_m"]
    sign = -1.0 if sc["side"] == "low" else 1.0       # out from the corner, past the front's end
    end = 0.0 if sc["side"] == "low" else width
    S = lambda x: end + sign * x                      # x: out from the corner, 0 to w
    seed = a.instance("k01.front.scroll", "trim", {"width_m": w, "pier_top_m": y0, "top_m": y1, "depth_m": dp},
                      {"corner": _P(frame, end, y0, 0.0)})
    lo, hi = sorted((S(0.0), S(w)))
    # the pier: its face against the corner's side wall left off, and its foot in the ground
    _box(a, brick, frame, lo, hi, 0.0, y0, -dp, 0.0, seed, conf, skip=("y0", "s1" if sign < 0 else "s0"))
    # the console: slices from the corner out, each a trapezoid under the sweep
    top = lambda x: y0 + 0.22 + (y1 - y0 - 0.22) * (1.0 - x / w) ** 2.2
    d0, d1 = -dp + 0.04, -0.04
    pr = a.prim(trim)
    P = lambda s, y, d: _P(frame, s, y, d)
    out = _mul(R, sign)
    xs = [w * k / SCROLL_SLICES for k in range(SCROLL_SLICES + 1)]
    for xa, xb in zip(xs, xs[1:]):
        sa_, sb_, ya, yb = S(xa), S(xb), top(xa), top(xb)
        quad = [(sa_, y0), (sb_, y0), (sb_, yb), (sa_, ya)]
        _face(a, pr, trim, [P(s, y, d1) for s, y in quad], N, O, R, Y, seed, conf)
        _face(a, pr, trim, [P(s, y, d0) for s, y in quad], _mul(N, -1.0), O, _mul(R, -1.0), Y, seed, conf)
        # the sweep's top between the two slices' heads, its normal up and out
        ln = math.hypot(xb - xa, yb - ya)
        nrm = _add(_mul(out, (ya - yb) / ln), _mul(Y, (xb - xa) / ln))
        along = _mul(_sub(P(sb_, yb, 0.0), P(sa_, ya, 0.0)), 1.0 / ln)
        _face(a, pr, trim, [P(sa_, ya, d0), P(sb_, yb, d0), P(sb_, yb, d1), P(sa_, ya, d1)], nrm,
              P(sa_, ya, 0.0), along, N, seed, conf)
    # the outer end's face, from the pier's top to the sweep's foot
    so, ho = S(w), top(w)
    _face(a, pr, trim, [P(so, y0, d0), P(so, y0, d1), P(so, ho, d1), P(so, ho, d0)], out,
          P(so, 0.0, 0.0), N, Y, seed, conf)
    # the volute at the sweep's foot, a drum proud of the console's face, its eye prouder still
    r = min(0.22, (y1 - y0) * 0.2, w * 0.24)
    sv = S(w - r)
    prism(a, trim, frame, _disc(sv, y0 + r, r), d1, d1 + 0.03, seed, conf)
    prism(a, trim, frame, _disc(sv, y0 + r, r * 0.4, 10), d1 + 0.03, d1 + 0.06, seed, conf)
