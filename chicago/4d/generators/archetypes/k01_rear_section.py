"""T-2820: a K01 house's REAR SECTION — 1625 Prairie's four-storey rear part, from the 1911 sheet and the McBirney photograph.

TICKET T-2820 (piece 1 of T-2754, of T-2731). The 1911 Sanborn sheet traces 1625's rear 7.6 m
stepping 1.3 m further south than its main body (s20-1625-a1, '4' storeys), and the Inland
Architect photograph of 1890 shows that part standing behind the main body's south wall: a
narrow brick face toward the street with a door at grade and a window a storey over it, a
cornice at the main eave's height, and over it a tall slated attic with a dormer on its street
face, its south end the brick wall carried up the attic's profile to a stack. K01's rear wing
(T-2343) stands behind the main body, inside its width, under a flat deck, so it cannot build
this; the record names it as `rear_section` (resolve() here bounds it) and this module builds it:

  walls()     the step-out's three outer walls — its street face, its outer side and its rear
              face — in the K03 brick to the main wall head, each opening the record reads cut
              through it (a K06 sash, or a plain boarded service door under a brick head); the
              main side wall is not drawn behind it, as a wing's host wall is not
  elements()  before the union: the ATTIC, a mansard section (steep lower faces front and rear
              to a curb, a low pitch over them to a ridge running across the house) extruded
              from the party wall to the step-out's outer face, and at each end the wall
              carried up the attic's profile as a coped parapet, the kit's parapet_element, so
              the attic dies into it as 1619's gable roof dies into its side walls; and each
              dormer on its lower faces, the main mansard's gabled dormer (T-2452)

Every number is the record's or K05's (k05_roofs.json parts.parapet, parts.coping), and
docs/LIBERTIES.md L-k01-1625-rear-section-2820 says which.
"""

from __future__ import annotations

import math

SIDES = ("north",)                      # the K01 wall it steps out from (1625's open south side)
FACES = ("street", "outer", "rear")     # the step-out's own walls
CORNER_M = 0.20                         # the least pier between an opening and a corner
DOOR_KIT = "k01.opening.service_door"   # a plain boarded door: no K07 stoop, no entrance kit
SASH = "k01.opening.sash_flat"
DOOR_REVEAL_M = 0.20


def _err(msg):
    from .k01_frontage_params import ParamError
    return ParamError(f"rear_section: {msg}")


def resolve(e: dict, *, depth: float, width: float, eave: float, side_wall: float, overhang: float,
            cw, openings) -> dict:
    """The record's `rear_section` resolved and bounded, or {} when it names none."""
    if not e:
        return {}
    import json
    from .k01_frontage_params import (MANSARD_ROOFS, ROOT, Opening, _round_dormer, _within,
                                      mansard_face_height)
    side = e.get("side")
    if side not in SIDES:
        raise _err(f"side {side!r}: a section steps out from {', '.join(SIDES)} (the one built)")
    u0, u1 = (float(x) for x in e["u_m"])
    step = float(e["step_m"])
    if not (abs(u0) < 1e-9 and 2.0 <= u1 <= depth - 2.0):
        raise _err(f"u_m {e['u_m']}: from the rear wall (0) to at least 2 m short of the front")
    if not 0.6 <= step <= 4.0:
        raise _err(f"step_m {step}: a section steps 0.6-4.0 m past the side wall")
    k5 = json.loads((ROOT / "data" / "components" / "prairie_1904" / "k05_roofs.json").read_text())
    m = e["attic"]
    vid = m.get("variant")
    if vid not in MANSARD_ROOFS:
        raise _err(f"attic.variant {vid!r}: one of {', '.join(MANSARD_ROOFS)}")
    v = next(x for x in k5["variants"] if x["id"] == vid)
    lower, upper = float(m["lower_pitch_deg"]), float(m["pitch_deg"])
    _within(lower, k5["ranges"]["mansard_lower_deg"], "rear_section.attic.lower_pitch_deg")
    _within(upper, k5["ranges"]["mansard_upper_deg"], "rear_section.attic.pitch_deg")
    rise, o = float(m["lower_rise_m"]), float(m["overhang_m"])
    if not 2.0 <= rise <= 4.5:
        raise _err(f"attic.lower_rise_m {rise}: an attic storey's face rises 2.0-4.5 m")
    if not 0.1 <= o <= 1.0:
        raise _err(f"attic.overhang_m {o}: its cornice projects 0.1-1.0 m")
    if o < overhang:
        raise _err(f"attic.overhang_m {o}: under the main eave's {overhang} m, whose eave would stand out of it")
    run = rise / math.tan(math.radians(lower))
    half = (u1 - u0) / 2 + o
    if run >= half - 0.5:
        raise _err(f"attic.lower_rise_m {rise}: the curb leaves no upper roof")
    curb = round(eave + rise, 4)
    ridge = round(curb + (half - run) * math.tan(math.radians(upper)), 4)
    pp, cp = k5["parts"]["parapet"], k5["parts"]["coping"]
    attic = {"variant": vid, "profile": v["profile"], "bulge": 0.0, "lower_pitch_deg": lower,
             "pitch_deg": upper, "lower_rise_m": rise, "overhang_m": o, "run_m": round(run, 4),
             "curb_m": curb, "ridge_m": ridge, "parapet_m": side_wall,
             "upstand_m": float(pp["upstand_min_m"]), "coping_m": float(cp["thickness_m"]),
             "drip_m": float(cp["drip_m"])}
    # the walls: each face's length, and the host wall's span the section covers (s from the
    # front on K01's north wall, which runs front to rear)
    lengths = {"street": step, "outer": u1 - u0, "rear": step}
    host = "k01.wall.side.north"
    span = (round(depth - u1, 4), round(depth - u0, 4))
    for op in openings:
        if op.wall == host and op.s_m + op.width_m / 2 > span[0] - 0.12 and op.s_m - op.width_m / 2 < span[1]:
            raise _err(f"the side wall's opening at s {op.s_m} stands behind the section ({span[0]}-{span[1]})")
    ops, laid = [], {f: [] for f in FACES}
    for i, w in enumerate(e.get("openings") or ()):
        what = f"openings[{i}]"
        face, kind = w.get("face"), w.get("kind")
        if face not in FACES:
            raise _err(f"{what}.face {face!r}: one of {', '.join(FACES)}")
        s, wd, sill, h = (float(w[x]) for x in ("s_m", "width_m", "sill_m", "height_m"))
        if kind == "sash":
            # the picture's own sizes: the contract's single sash width, its height read (the
            # starting range yields to the picture, as street_front_windows' do)
            _within(wd, cw, f"rear_section.{what}.width_m")
            if not 1.0 <= h <= 3.2:
                raise _err(f"{what}.height_m {h}: a sash read off a picture stands 1.0-3.2 m")
            comp = SASH
        elif kind == "door":
            if not (0.75 <= wd <= 1.2 and 1.9 <= h <= 2.7 and 0.0 <= sill <= 0.6):
                raise _err(f"{what}: a service door 0.75-1.2 m wide, 1.9-2.7 m high, its sill 0-0.6 m over grade")
            comp = DOOR_KIT
        else:
            raise _err(f"{what}.kind {kind!r}: sash or door")
        if s - wd / 2 < CORNER_M - 1e-9 or s + wd / 2 > lengths[face] - CORNER_M + 1e-9:
            raise _err(f"{what} stands closer than {CORNER_M} m to a corner of its {lengths[face]:.3f} m wall")
        if sill + h + 0.30 > eave - 0.20:
            raise _err(f"{what}'s head runs into the cornice")
        for j, (a0, a1, b0, b1) in enumerate(laid[face]):
            if s - wd / 2 < a1 and s + wd / 2 > a0 and sill < b1 + 0.45 and sill + h > b0 - 0.45:
                raise _err(f"{what} meets an opening under or over it, or its head")
        laid[face].append((s - wd / 2, s + wd / 2, sill, sill + h))
        ops.append(Opening(comp, f"k01.wall.rear_section.{face}", round(s, 4), round(sill, 4), wd, h, kind == "sash"))
    # the dormers, on the attic's street or rear lower face: each the main mansard's gabled
    # dormer, standing on what the main roof leaves of that face and clear of the end parapet
    dormers = []
    for i, d in enumerate(m.get("dormers") or ()):
        what = f"rear_section.attic.dormers[{i}]"
        face = d.get("face")
        if face not in ("street", "rear"):
            raise _err(f"attic.dormers[{i}].face {face!r}: street or rear")
        r_ = _round_dormer(d, what, run)
        c, r = float(d["along_m"]), r_["width_m"] / 2
        lo, hi = width + overhang, width + step - side_wall - 0.05
        if not lo + r - 1e-9 <= c <= hi - r + 1e-9:
            raise _err(f"attic.dormers[{i}].along_m {c}: its face stands past the main eave and clear of the "
                       f"parapet only for {lo + r:.2f}-{hi - r:.2f} m")
        foot = mansard_face_height(r_["face_setback_m"], rise, lower, 0.0, v["profile"])
        if foot + r_["sill_m"] + r_["head_m"] > rise - 0.1:
            raise _err(f"attic.dormers[{i}]: its head meets the curb at {rise} m over the cornice")
        dormers.append(dict(r_, face=face, along_m=c, foot_m=round(eave + foot, 4)))
    attic["dormers"] = dormers
    return {"side": side, "u_m": (u0, u1), "step_m": step, "eave_m": eave, "host_wall": host,
            "host_span_m": span, "attic": attic, "openings": tuple(ops),
            "rect": (u0, u1, width, round(width + step, 4))}


def wall_frames(p) -> dict:
    """Each step-out wall as (origin, along, length) in the assembly's frame (+X is u, -Z is v),
    read left to right from outside as the main walls are."""
    rs = p.rear_section
    u0, u1, v0, v1 = rs["rect"]
    return {"street": ((u1, 0.0, -v0), (0.0, 0.0, -1.0), v1 - v0),
            "outer": ((u1, 0.0, -v1), (-1.0, 0.0, 0.0), u1 - u0),
            "rear": ((u0, 0.0, -v1), (0.0, 0.0, 1.0), v1 - v0)}


def walls(a) -> None:
    """The step-out's three walls in the K03 brick to the main wall head, their openings cut."""
    from . import k03_brick
    p, rs = a.p, a.p.rear_section
    E = rs["eave_m"]
    for face, (O, R, length) in wall_frames(p).items():
        cid = f"k01.wall.rear_section.{face}"
        ops = [o for o in rs["openings"] if o.wall == cid]
        hs = [(o.s_m - o.width_m / 2, o.s_m + o.width_m / 2, o.sill_m, o.head_m) for o in ops]
        breaks = (a.soffit_m, *k03_brick.condition_breaks(a.soffit_m))
        frame, t = a.wall(cid, "brick", O, R, length, E, p.side_thickness_m, hs, breaks)
        for o in ops:
            if o.component == DOOR_KIT:
                service_door(a, o, frame, t)
            else:
                a.opening(o, frame, t, "brick", "limestone_trim")


def service_door(a, op, frame, thickness) -> None:
    """A plain boarded door in its brick reveal under a soldier head: the photograph's door
    at the section's foot, a service door, so no K07 entrance and no stoop."""
    from . import k03_brick
    from .k01_frontage import Y, _add, _mul
    p = a.p
    O, R, N = frame
    conf = p.worst_conf("footprint", "rear_section")
    seed = a.instance(op.component, "opening", {"clear_width_m": op.width_m, "clear_height_m": op.height_m,
                                                "reveal_m": DOOR_REVEAL_M, "wall": op.wall},
                      {"sill": _add(O, _add(_mul(R, op.s_m), _mul(Y, op.sill_m))),
                       "head": _add(O, _add(_mul(R, op.s_m), _mul(Y, op.head_m)))})
    P = lambda s, y, d: _add(_add(_add(O, _mul(R, s)), _mul(Y, y)), _mul(N, d))
    s0, s1, y0, y1, d = op.s_m - op.width_m / 2, op.s_m + op.width_m / 2, op.sill_m, op.head_m, -DOOR_REVEAL_M
    rev = a.prim("brick")
    b = a.basis("brick", O, R, Y, seed)
    neg = lambda v: tuple(-x for x in v)
    rev.face([P(s0, y0, 0), P(s0, y0, d), P(s0, y1, d), P(s0, y1, 0)], R, b, conf)
    rev.face([P(s1, y0, d), P(s1, y0, 0), P(s1, y1, 0), P(s1, y1, d)], neg(R), b, conf)
    rev.face([P(s0, y1, 0), P(s0, y1, d), P(s1, y1, d), P(s1, y1, 0)], neg(Y), b, conf)
    leaf = a.prim("door_leaf")
    leaf.face([P(s0, y0, d), P(s1, y0, d), P(s1, y1, d), P(s0, y1, d)], N, a.basis("door_leaf", O, R, Y, seed), conf)
    k03_brick.soldier_head(a, seed, frame, s0, s1, y1, conf)


def elements(a, k5, f: float):
    """The attic and its two end parapets as closed K05 elements in the K01 frame (x is u, z is
    -v), the parapets first so the union keeps their faces on the walls' planes; the body
    under the attic; and the dormers' bodies and their sash recesses."""
    from .k01_gable_roof import FRONT_SET_M
    p, rs = a.p, a.p.rear_section
    m, E = rs["attic"], rs["eave_m"]
    u0, u1, v0, v1 = rs["rect"]
    o, run, rise = m["overhang_m"], m["run_m"], m["lower_rise_m"]
    tl = math.tan(math.radians(m["lower_pitch_deg"]))
    xm, yr, yc = (u0 + u1) / 2, m["ridge_m"], m["curb_m"]
    hs = E - f
    P = k5.frame("z")
    attic = k5.extrude([(u0 - o, hs), (u1 + o, hs), (u1 + o, E), (u1 + o - run, yc), (xm, yr),
                        (u0 - o + run, yc), (u0 - o, E)], -v1, 0.0, P,
                       k5.by_edge("covering", "soffit", "fascia"), "fascia", "fascia")
    tw, up = m["parapet_m"], m["upstand_m"]
    # the parapet's head: the attic's outline over the walls' planes, `up` clear of it
    ln = [(u0 + FRONT_SET_M, E + o * tl + up), (u0 - o + run, yc + up), (xm, yr + up),
          (u1 + o - run, yc + up), (u1 - FRONT_SET_M, E + o * tl + up)]
    solids = []
    for c0, c1 in ((-v1, -v1 + tw), (-tw, 0.0)):
        solids += k5.parapet_element({}, ln, (c0, c1), "z", tw, hs, m["coping_m"], m["drip_m"], 0.0, 0.0)
    solids += [attic, k5.body_box(u0, u1, -v1, 0.0, hs - 1.0, hs)]
    a.rear_section_line = [[round(x, 4), round(y, 4)] for x, y in ln]
    bodies, recesses = [], []
    fascia = {"street": u1 + o, "rear": u0 - o}
    for d in m["dormers"]:
        g = a.round_dormer_body(d, d["face"], fascia[d["face"]], -d["along_m"], rise, m["lower_pitch_deg"],
                                0.0, E, profile=m["profile"])
        a.round_dormers.append(g["geom"])
        bodies.append(g["body"])
        recesses.append(g["recess"])
    return solids + bodies, recesses
