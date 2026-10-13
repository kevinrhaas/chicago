"""T-2428: the K01 street dormer built as a WALL GABLE — 1619 Prairie's roof storey.

TICKET T-2428 (piece 1 of T-2421, of T-2419). Treat & Foltz's drawing of John H. Hamline's
house (`building_budget_1886_06_hamline_farwell_houses`) lights its roof storey not with a
dormer on the hip but with a steep pedimented gable rising from the wall over the bow: three
short segment-headed lights, each under a block of radiating voussoirs, a horizontal cornice
and a raking cornice over them, a recessed panel in the pediment, a finial at the apex and a
pinnacle shaft either side at the gable's foot. The record names it as its dormer's
`wall_gable` (k01_frontage_params._wall_gable resolves and bounds it); this module builds it
on the K05 dormer that k01_frontage.roof already raises, so the face, cheeks and gabled roof
stay ONE closed solid with the hip and every cut is the union's:

  cutters()  before the boolean: each light's recess cut to K06's own hole (so its
             segmental head is the reveal's edge) and the pediment's recessed panel
  dress()    after it: each light's K06 sash in its recess, its voussoirs, the two
             pinnacles and the finial

The pediment's horizontal and raking cornices are K10's dormer face (k10_frontage._dormer),
laid as on any K10-dressed dormer. Every number a piece is cut to is the record's or is
named here, and docs/LIBERTIES.md L-k01-1619-hamline-wall-gable-2428 says which.
"""

from __future__ import annotations

import math

SEGMENTS = 7               # voussoirs a light: an odd number, so one stone is the crown's
JOINT_M = 0.008            # half a voussoir joint
PIN_CAP_PROUD_M = 0.04     # a pinnacle's cap before its shaft, all round
PIN_SIDES = 4              # a pinnacle's spire: a square pyramid
FINIAL_SINK_M = 0.06       # the finial's foot let into the ridge


def _k01():
    from . import k01_frontage
    return k01_frontage


def _af():
    from . import k01_arched_front
    return k01_arched_front


def lights(d) -> list:
    """Each light as (offset across the face from its centre, toward R), in order."""
    return list(d["sash"]["at_m"])


def _variant(d, k6):
    v = dict(next(x for x in k6.load()["variants"] if x["id"] == d["sash"]["variant"]))
    v["clear_width_m"], v["clear_height_m"] = d["sash"]["width_m"], d["sash"]["height_m"]
    return v


def head(d, k6):
    """The K06 head over a light, in the light's own frame (x across it, y above its sill)."""
    v = _variant(d, k6)
    sw, sh = d["sash"]["width_m"], d["sash"]["height_m"]
    ros = k6.load()["arch"]["segmental"]["working_rise_over_span"]
    rise = sw * ros if v["head"] == "segmental" else 0.0
    return k6.Head(v["head"], -sw / 2, sw / 2, sh - rise, ros)


def pediment(d, g) -> dict:
    """The tympanum K10 dresses: its foot (the cornice's top, the cheeks' soffit) and the
    inner edge of the raking cornice's bands at the face's centre line."""
    from . import k10_frontage
    data = k10_frontage._kit().load()
    dm = data["parts"]["dormer"]
    hs, dt, o, wd = g["dhs"], g["dt"], g["overhang"], d["width_m"]
    cq = math.sqrt(1 + dt * dt)
    apex = hs + (wd / 2 + o) * dt
    inner = apex - sum(b["width_m"] for b in dm["rake_bands"]) * cq
    return {"foot": hs, "apex": apex, "inner": inner, "cq": cq,
            "cornice_low": hs - max(u for _, u in data["parts"]["profiles"]["dormer_cornice"]["points"])}


def cutters(a, k5, P, xf, ys, zc) -> list:
    """The recesses the union cuts: every light's, to K06's hole, and the pediment panel."""
    from . import k06_windows as k6
    d = a.p.dormer
    v = _variant(d, k6)
    o = k6.Opening(v, k6.load())
    o.build()
    hole = o.holes[0]
    # K06's reveal depth, the variant's own where it overrides the kit's (as kit_reveal)
    rev = v.get("overrides", {}).get("reveal_depth_m", k6.load()["parts"]["reveal_depth_m"]["value"])
    sill = ys + d["sash"]["sill_m"]
    out = []
    for at in lights(d):
        c = zc - at                     # R runs -z along the street front
        rec = [(c - q[0], sill + q[1]) for q in hole]
        out.append(k5.extrude(rec, xf - rev, xf + 0.05, P, "reveal", "window", "reveal"))
    g = a.dormer_geom
    pd, pa = pediment(d, g), d["wall_gable"]["panel"]
    m = pa["inset_m"]
    y0, y1 = pd["foot"] + m, pd["inner"] - m * pd["cq"]
    hw = (y1 - y0) / g["dt"]
    if hw < 0.2:
        raise ValueError("the pediment's panel is narrower than its margins leave room for")
    tri = [(zc + hw, y0), (zc - hw, y0), (zc, y1)]
    out.append(k5.extrude(tri, xf - pa["depth_m"], xf + 0.05, P, "dormer_face", "dormer_face", "hidden"))
    a.wall_gable = {"panel_m": [round(y0, 4), round(y1, 4), round(2 * hw, 4)]}
    return out


def _wedges(cx, cy, r, a0, a1, L, R, top):
    """A segmental head's intrados from angle a0 to a1 about (cx, cy), radius r, cut into
    SEGMENTS stones radiating to the block L..R x ..top — k01_arched_front.wedges' cut for
    an arc that does not start on its centre's level."""
    hit = _af()._hit
    angs = [a0 + (a1 - a0) * i / SEGMENTS for i in range(SEGMENTS + 1)]
    corners = [(math.atan2(top - cy, R - cx), (R, top)), (math.atan2(top - cy, L - cx), (L, top))]
    out = []
    for b0, b1 in zip(angs, angs[1:]):
        A = (cx + r * math.cos(b0), cy + r * math.sin(b0))
        B = (cx + r * math.cos(b1), cy + r * math.sin(b1))
        pts = [A, hit(cx, cy, b0, L, R, top)]
        pts += [q for ang, q in corners if b0 + 1e-6 < ang < b1 - 1e-6]
        pts += [hit(cx, cy, b1, L, R, top), B]
        clean = []
        for q in pts:
            if not clean or math.dist(clean[-1], q) > 1e-6:
                clean.append(q)
        out.append(clean)
    return out


def _prism(a, mat, frame, poly, d0, d1, seed, conf):
    """A stone standing proud of the face: its front at d1 and every edge's side face;
    its back lies on the face, so it is not drawn."""
    af = _af()
    af._face(a, mat, frame, [(s, y, d1) for s, y in poly], (0, 0, 1), seed, conf)
    n = len(poly)
    for i in range(n):
        (s0, y0), (s1, y1) = poly[i], poly[(i + 1) % n]
        out = (y1 - y0, -(s1 - s0), 0.0)        # the edge's outward normal (counter-clockwise)
        af._face(a, mat, frame, [(s0, y0, d0), (s1, y1, d0), (s1, y1, d1), (s0, y0, d1)], out, seed, conf)


def _pyramid(a, mat, frame, s, d, y0, hw, y1, seed, conf):
    af = _af()
    base = [(s - hw, y0, d - hw), (s + hw, y0, d - hw), (s + hw, y0, d + hw), (s - hw, y0, d + hw)]
    for i in range(PIN_SIDES):
        p, q = base[i], base[(i + 1) % PIN_SIDES]
        mid = ((p[0] + q[0]) / 2 - s, 0.4, (p[2] + q[2]) / 2 - d)
        af._face(a, mat, frame, [p, q, (s, y1, d)], mid, seed, conf)


def dress(a, roof_seed):
    """The lights' sashes, their voussoirs, the pinnacles and the finial."""
    from . import k06_windows as k6
    from archetypes.k01_frontage_params import Opening
    k = _k01()
    af = _af()
    p, d, g = a.p, a.p.dormer, a.dormer_geom
    wg = d["wall_gable"]
    conf = p.worst_conf("dormer")
    wd, hf = d["width_m"], d["face_height_m"]
    zc = (g["zs"] + g["zn"]) / 2
    O = (g["xf"], g["ys"], g["zs"])
    R = (0.0, 0.0, -1.0)
    N = k._cross(R, k.Y)
    frame = (O, R, N)
    ats = lights(d)
    hd = head(d, k6)
    a.instance("k01.wall.dormer_face", "wall", {"length_m": wd, "height_m": hf, "thickness_m": d["face_thickness_m"],
                                                "construction": "masonry", "openings": len(ats), "head": hd.kind,
                                                "wall_gable": True, "panel_m": a.wall_gable["panel_m"]},
               {"base": O, "top": k._add(O, k._mul(k.Y, hf))})
    if not hasattr(a, "_kit"):
        a._kit = k6.load()
    v = _variant(d, k6)
    sw, sh, sill = d["sash"]["width_m"], d["sash"]["height_m"], d["sash"]["sill_m"]
    vs = wg["voussoirs"]
    top = sill + hd.apex() + vs["ring_m"]
    if g["ys"] + top > pediment(d, g)["cornice_low"] - 0.02:
        raise ValueError("the wall gable's voussoirs run into its cornice")
    roles = {r: ("limestone_trim" if m == "stone" else (m or "dormer_stone")) for r, m in a.K06_ROLES.items()}
    for at in ats:
        s = wd / 2 + at
        op = Opening("k01.opening.gable_light", "k01.wall.dormer_face", s, sill, sw, sh)
        seed = a.instance(op.component, "opening", {"clear_width_m": sw, "clear_height_m": sh,
                                                    "k06_variant": v["id"], "wall": op.wall},
                          {"sill": k._add(O, k._add(k._mul(R, s), k._mul(k.Y, sill)))})
        o = k6.Opening(v, a._kit)
        o.seed = seed
        o.build()
        a.graft(o, "K06", roles, frame, op, lambda role, sd=seed: (sd, conf), ("reveal",))
        # the voussoirs: the head's block, the light's width and `side_m` either side of it
        # up to `ring_m` over the crown, cut radially from the head's own centre
        vseed = a.instance("k01.opening.segmental_arch", "opening",
                           {"of": op.component, "segments": SEGMENTS, "ring_m": vs["ring_m"],
                            "proud_m": vs["proud_m"], "rise_m": round(hd.rise, 4)},
                           {"crown": k._add(O, k._add(k._mul(R, s), k._mul(k.Y, sill + hd.apex())))})
        L, Rr = s - sw / 2 - vs["side_m"], s + sw / 2 + vs["side_m"]
        if hd.kind == "segmental":
            cx, cy, r = s, sill + hd.cy, hd.R
            a0 = math.atan2(sill + hd.spring - cy, sw / 2)
            stones = _wedges(cx, cy, r, a0, math.pi - a0, L, Rr, top)
        else:
            stones = [[(L, sill + hd.spring), (Rr, sill + hd.spring), (Rr, top), (L, top)]]
        for poly in stones:
            _prism(a, "limestone_trim", frame, k._inset(poly, [JOINT_M] * len(poly)), 0.0, vs["proud_m"], vseed, conf)
    # the pinnacles: square shafts either side of the face's foot, from under the wall
    # head (through the eave) past the face's eave, a cap and a pyramid over each
    pn = wg["pinnacles"]
    hw = pn["shaft_m"] / 2
    for i, sg in enumerate((-1, 1)):
        s = wd / 2 + sg * pn["at_m"]
        y0, y1 = g["ys"] + pn["foot_m"], g["ys"] + pn["top_m"]
        pseed = a.instance("k01.roof.gable_pinnacle", "roof",
                           {"shaft_m": pn["shaft_m"], "top_m": round(y1, 4), "cap_m": pn["cap_m"],
                            "spire_m": pn["spire_m"]},
                           {"foot": k._add(O, k._add(k._mul(R, s), k._mul(k.Y, pn["foot_m"])))})
        Fr = ((O[0], 0.0, O[2]), R, N)
        af._box(a, "limestone_trim", Fr, s - hw, s + hw, y0, y1, -hw, hw, pseed, conf, skip=("bottom", "top"))
        c = hw + PIN_CAP_PROUD_M
        af._box(a, "limestone_trim", Fr, s - c, s + c, y1, y1 + pn["cap_m"], -c, c, pseed, conf)
        _pyramid(a, "limestone_trim", Fr, s, 0.0, y1 + pn["cap_m"], hw, y1 + pn["cap_m"] + pn["spire_m"], pseed, conf)
    # the finial: a turned stone on the ridge over the pediment's apex, let into it
    fn = wg["finial"]
    ya = g["ridge"] - FINIAL_SINK_M
    fseed = a.instance("k01.roof.gable_finial", "roof", {"height_m": fn["height_m"], "radius_m": fn["radius_m"]},
                       {"foot": (O[0], round(ya, 4), zc)})
    Fr = ((O[0], 0.0, zc), R, N)
    rr, hgt = fn["radius_m"], fn["height_m"]
    af._frustum(a, "limestone_trim", Fr, 0.0, 0.0, ya, ya + 0.35 * hgt, rr * 0.7, rr, fseed, conf)
    af._frustum(a, "limestone_trim", Fr, 0.0, 0.0, ya + 0.35 * hgt, ya + 0.55 * hgt, rr, rr * 0.45, fseed, conf)
    af._frustum(a, "limestone_trim", Fr, 0.0, 0.0, ya + 0.55 * hgt, ya + hgt, rr * 0.45, 0.004, fseed, conf)
