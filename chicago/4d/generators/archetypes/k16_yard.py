"""A whole frame house's front yard: its street-line kerb, posts and railing, and the walks
through it (T-3205).

The owner, 2026-10-27, of the worked Prairie houses: "make sure that you have their walkways to
their house correct and the front gate/fence/borders and side fence/borders etc are correct
photographic match ... others are missing, cant enter". A K01 house lays these with K11
(`k11_frontage.py`) and K14 (`k14_yard.py`), which are written against K01's assembly; a K16
frame house (`k16_timber.frame_house`, 1720's) had none, so a visitor met a lawn and no way in.
This lays the same things on a frame house, in the plan frame `frame_house` builds in (x = u
toward the street, z = -v), and writes the same component instances K11 and K14 write, so
`tools/check_house_walks.py` reads a frame house's walk and kerb as it reads a brick one's.

What the record's `boundary` (`layout: stone_coping_wall`) names, and what is built:

  kerb     squared stone on the street line, its street face on `street_u_m`, from the south
           lot line to the north in `runs` (south to north, each `{to_s_m, height_m}`), each
           `thickness_m` through, its top rounded across (`round_top`, the 2015 survivor of
           1720's: a limestone kerb with a half-round top) or flat.
  posts    a run that names `post: true` is a stone post `thickness_m` square, its top
           rounded across the street front (the photograph's round-topped posts).
  railing  a run that names `rail_m` carries an iron railing on the kerb's top to that height
           over grade: square bars at the kit's pitch between a bottom and a top rail.
  opening  a run `{to_s_m, opening: true}` lays nothing: the walk passes there.

What its `yard` names:

  front walk  stone flags from the stair's foot (read off the built steps) out through the
              kerb's opening to the street line, `width_m` wide, straight where the opening
              holds it and turned behind the kerb otherwise (k14_yard._route).
  service walk  optional: cinder (or flags) in through another opening, `turn_u_m` along the
              front and back down the side passage `passage_s_m` to `to_u_m`.
  grade_m     as K14's (k14_yard._grade_spec): the app's ground over the house's lowest foot,
              measured in the published app, lifts every vertex the yard lays.

No lawn is laid: the frame house's ground is the app's own (K16's flat paint has no turf to
draw it in), so the walks lie on it and the kerb stands on it.
"""

from __future__ import annotations

import math

from . import k14_yard

COPING = "stone_coping_wall"
FLAG_SINK = 0.05
JOINT_M = 0.01
ARC = 6                 # segments in a half-round top
BAR_M, BAR_PITCH_M = 0.018, 0.12
RAIL_M = (0.03, 0.04)   # the top rail's height and breadth
UP = (0.0, 1.0, 0.0)


def spec(form: dict) -> tuple[dict | None, dict | None]:
    b = (form.get("boundary") or {}).get("value")
    y = (form.get("yard") or {}).get("value")
    if b is None and y is None:
        return None, None
    if b is None or b.get("layout") != COPING:
        raise ValueError("a frame house's yard is laid inside a `stone_coping_wall` boundary")
    s0, s1 = b["lot_s_m"]
    if not 0.2 <= b.get("thickness_m", 0) <= 0.6:
        raise ValueError("stone_coping_wall: thickness_m 0.2-0.6 m")
    last = s0
    for r in b["runs"]:
        if r.get("opening"):
            if not last + 0.9 <= r["to_s_m"]:
                raise ValueError(f"stone_coping_wall run {r}: an opening is at least 0.9 m wide")
        elif r.get("post"):
            if not 0.2 <= r["to_s_m"] - last <= 0.6 or not 0.5 <= r["height_m"] <= 2.0:
                raise ValueError(f"stone_coping_wall post {r}: 0.2-0.6 m square, 0.5-2.0 m high")
        else:
            if not last + 0.3 <= r["to_s_m"] or not 0.15 <= r["height_m"] <= 1.2:
                raise ValueError(f"stone_coping_wall run {r}: at least 0.3 m long, 0.15-1.2 m high")
            if "rail_m" in r and not r["height_m"] + 0.3 <= r["rail_m"] <= 1.5:
                raise ValueError(f"stone_coping_wall run {r}: a railing 0.3 m or more over its kerb, to 1.5 m")
        last = r["to_s_m"]
    if abs(last - s1) > 1e-6:
        raise ValueError(f"stone_coping_wall: the runs end at s {last}, not on the north lot line {s1}")
    if y is not None:
        fw = y.get("front_walk") or {}
        if fw.get("surface") != "stone_flags" or not 0.9 <= float(fw.get("width_m", 0)) <= 3.0:
            raise ValueError("yard.front_walk: stone_flags, width_m 0.9-3.0")
        if not 0.3 <= float(fw["flag_m"]) <= 1.8 or not 0.03 < float(fw["top_m"]) <= 0.1:
            raise ValueError("yard.front_walk: flag_m 0.3-1.8, top_m 0.03-0.1")
        k14_yard._grade_spec(y)
    return b, y


def _w(u, y, v):
    return (u, y, -v)


def _box(house, role, u0, u1, y0, y1, v0, v1, tone=1.0, skip=("bottom",)):
    house.box(house.F, role, u0, u1, y0, y1, -v1, -v0, skip=skip, tone=tone)


def _kerb(house, b, v0, v1, h):
    """A run of kerb from v0 to v1, `h` high, its street face on the line."""
    uo = b["street_u_m"]
    T = b["thickness_m"]
    ui = uo - T
    if b.get("round_top"):
        r = T / 2
        uc = (ui + uo) / 2
        prof = [(uo, 0.0), (uo, h - r)] + [(uc + r * math.cos(math.pi * i / ARC), h - r + r * math.sin(math.pi * i / ARC))
                                          for i in range(1, ARC)] + [(ui, h - r), (ui, 0.0)]
    else:
        prof = [(uo, 0.0), (uo, h), (ui, h), (ui, 0.0)]
    for (ua, ya), (ub, yb) in zip(prof, prof[1:]):
        hint = (yb - ya, -(ub - ua), 0.0)          # outward from the kerb's middle, in (u, y)
        mu, my = (ua + ub) / 2 - (ui + uo) / 2, (ya + yb) / 2 - h / 2
        if hint[0] * mu + hint[1] * my < 0:
            hint = (-hint[0], -hint[1], 0.0)
        house.face("coping", [_w(ua, ya, v0), _w(ub, yb, v0), _w(ub, yb, v1), _w(ua, ya, v1)], hint)
    for v, k in ((v0, 1.0), (v1, -1.0)):
        house.face("coping", [_w(u, y, v) for u, y in prof], (0.0, 0.0, k))


def _post(house, b, v0, v1, h):
    """A square stone post, its top rounded across the street front (a half-round in v)."""
    uo = b["street_u_m"]
    ui = uo - b["thickness_m"]
    r = (v1 - v0) / 2
    vc = (v0 + v1) / 2
    _box(house, "kerb_post", ui, uo, 0.0, h - r, v0, v1, skip=("bottom", "top"))
    arc = [(vc + r * math.cos(math.pi * i / ARC), h - r + r * math.sin(math.pi * i / ARC)) for i in range(ARC + 1)]
    for (va, ya), (vb, yb) in zip(arc, arc[1:]):
        nv, ny = (va + vb) / 2 - vc, (ya + yb) / 2 - (h - r)
        house.face("kerb_post", [_w(ui, ya, va), _w(uo, ya, va), _w(uo, yb, vb), _w(ui, yb, vb)], (0.0, ny, -nv))
    for u, k in ((uo, 1.0), (ui, -1.0)):
        house.face("kerb_post", [_w(u, y, v) for v, y in arc], (k, 0.0, 0.0))


def _railing(house, b, v0, v1, h, top):
    """Iron bars on the kerb's top, between a bottom rail on the kerb and a top rail."""
    uc = b["street_u_m"] - b["thickness_m"] / 2
    hb = BAR_M / 2
    rh, rw = RAIL_M
    y0 = h - (b["thickness_m"] / 2 if b.get("round_top") else 0.0) + 0.02
    _box(house, "kerb_rail", uc - rw / 2, uc + rw / 2, h, h + rh, v0, v1)
    _box(house, "kerb_rail", uc - rw / 2, uc + rw / 2, top - rh, top, v0, v1)
    n = max(1, round((v1 - v0) / BAR_PITCH_M))
    bars = 0
    for i in range(n):
        v = v0 + (v1 - v0) * (i + 0.5) / n
        _box(house, "kerb_bar", uc - hb, uc + hb, max(y0, h + rh), top - rh, v - hb, v + hb, skip=("bottom", "top"))
        bars += 1
    return bars


def _flags(house, role, legs, flag_m, top, along_key, seed_tone):
    """Each leg (u0, u1, s0, s1, along) laid in flags `flag_m` long along its length."""
    tris = n = 0
    for li, (u0, u1, s0, s1, along) in enumerate(legs):
        L = (u1 - u0) if along == "u" else (s1 - s0)
        nf = max(1, round(L / flag_m))
        fl = (L - (nf - 1) * JOINT_M) / nf
        for j in range(nf):
            a0 = (u0 if along == "u" else s0) + j * (fl + JOINT_M)
            a1 = a0 + fl
            tone = 0.9 + 0.1 * ((j * 37 + li * 11 + seed_tone) % 7) / 6
            if along == "u":
                _box(house, role, a0, a1, -FLAG_SINK, top, s0, s1, tone=tone)
            else:
                _box(house, role, u0, u1, -FLAG_SINK, top, a0, a1, tone=tone)
            n += 1
            tris += 10
    return n, tris


def _lift(house, roles, marks, g, D, public, axis):
    f, s_, k = float(g["front"]), float(g["street"]), float(g.get("per_m_s", 0.0))
    for role, n0 in marks.items():
        pr = house.prims.get(role)
        if pr is None:
            continue
        for i in range(n0, len(pr.pos)):
            x, yy, z = pr.pos[i]
            s = -z
            if x <= D:
                rise = max(0.0, x / D) * (f + k * (s - axis))
            else:
                t = min(1.0, (x - D) / max(1e-6, public - D))
                rise = f + (s_ - f) * t + k * (s - axis)
            pr.pos[i] = (x, round(yy + max(0.0, rise), 5), z)


def dress(house, form: dict) -> dict | None:
    """Lay the record's kerb, posts, railing and walks on a frame house; return what was built
    and the component instances (for the GLB's extras), or None when it names neither."""
    b, y = spec(form)
    if b is None:
        return None
    fh = form["frame_house"]["value"]
    D = fh["blocks"][0]["rect_uv"][2]
    uo, T = b["street_u_m"], b["thickness_m"]
    inner = uo - T
    s_lo, s_hi = b["lot_s_m"]
    roles = ("coping", "kerb_post", "kerb_rail", "kerb_bar", "yard_flag", "yard_cinder")
    # the stair's foot, read off the built steps before anything else shares their roles
    steps = [q for r in ("step_riser", "step_tread") for q in house.prims[r].pos] if "step_riser" in house.prims else []
    marks = {r: len(house.prims[r].pos) if r in house.prims else 0 for r in roles}
    runs, last, bars = [], s_lo, 0
    for r in b["runs"]:
        a, c = last, r["to_s_m"]
        if r.get("opening"):
            runs.append((a, c, None))
        elif r.get("post"):
            _post(house, b, a, c, r["height_m"])
            runs.append((a, c, r["height_m"]))
        else:
            _kerb(house, b, a, c, r["height_m"])
            if "rail_m" in r:
                bars += _railing(house, b, a, c, r["height_m"], r["rail_m"])
            runs.append((a, c, r["height_m"]))
        last = c
    openings = [[round(a, 4), round(c, 4)] for a, c, h in runs if h is None]
    comps = [{"id": "k11.wall." + COPING, "family": "wall", "instances": [{
        "params": {"thickness_m": T, "lot_s_m": [s_lo, s_hi], "runs": b["runs"], "round_top": bool(b.get("round_top"))},
        "sockets": {"street": [uo, 0.0, 0.0]}}]}]
    out = {"kerb_runs": [[round(a, 4), round(c, 4), h] for a, c, h in runs if h is not None],
           "openings_s_m": openings, "railing_bars": bars, "inner_u_m": round(inner, 4)}
    if y is None:
        return {"built": out, "components": comps}
    F = y["front_walk"]
    w = float(F["width_m"])
    st = fh.get("porch", {}).get("steps") or {}
    axis = float(st.get("centre_m", 0.0))
    near = [q for q in steps if abs(-q[2] - axis) < float(st.get("width_m", 2.0)) / 2 + 0.05]
    if not near:
        raise ValueError("yard.front_walk: no built steps to start the walk at")
    foot = max(q[0] for q in near)
    legs = k14_yard._route((foot, axis - w / 2, axis + w / 2), [tuple(o) for o in openings], inner, uo, w)
    top = float(F["top_m"])
    nflags, ftris = _flags(house, "yard_flag", legs, float(F["flag_m"]), top, "u", 3)
    comps.append({"id": k14_yard.FRONT_WALK, "family": "yard", "instances": [{
        "params": {"flags": nflags, "width_m": w, "triangles": ftris,
                   "legs_m": [[round(l[0], 4), round(l[1], 4), round(l[2], 4), round(l[3], 4), l[4]] for l in legs]},
        "sockets": {"stoop_foot": [round(legs[0][0], 4), top, round(-(legs[0][2] + legs[0][3]) / 2, 4)],
                    "public_walk": [round(uo, 4), top, round(-(legs[-1][2] + legs[-1][3]) / 2, 4)]}}]})
    out["front_walk_legs_m"] = [[round(x, 4) if isinstance(x, float) else x for x in l] for l in legs]
    S = y.get("service_walk")
    if S:
        o0, o1 = S["opening_s_m"]
        if not any(o[0] - 1e-6 <= o0 and o1 <= o[1] + 1e-6 for o in openings):
            raise ValueError(f"yard.service_walk: s {o0}..{o1} is not an opening of the kerb {openings}")
        tu, (p0, p1), to_u = float(S["turn_u_m"]), S["passage_s_m"], float(S["to_u_m"])
        ww = float(S["width_m"])
        slegs = [(tu + ww, uo, o0, o1, "u"), (tu, tu + ww, min(o0, p0), max(o1, p1), "s"), (to_u, tu, p0, p1, "u")]
        role = "yard_cinder" if S["surface"] == "cinder" else "yard_flag"
        sn, stris = _flags(house, role, slegs, 100.0 if S["surface"] == "cinder" else float(F["flag_m"]),
                           LAWN_TOP if S["surface"] == "cinder" else top, "u", 5)
        comps.append({"id": k14_yard.SERVICE_WALK, "family": "yard", "instances": [{
            "params": {"width_m": ww, "triangles": stris,
                       "legs_m": [[round(l[0], 4), round(l[1], 4), round(l[2], 4), round(l[3], 4), l[4]] for l in slegs]},
            "sockets": {"rear_end": [to_u, LAWN_TOP, round(-(p0 + p1) / 2, 4)],
                        "gate": [uo, LAWN_TOP, round(-(o0 + o1) / 2, 4)]}}]})
        out["service_walk_legs_m"] = [[round(x, 4) if isinstance(x, float) else x for x in l] for l in slegs]
    g = k14_yard._grade_spec(y)
    if g is not None:
        _lift(house, ("yard_flag", "yard_cinder"), marks, g, D, uo, axis)
    return {"built": out, "components": comps}


LAWN_TOP = 0.03         # a cinder walk's top: just over the ground, as K14's (k14_yard.LAWN_Y)
