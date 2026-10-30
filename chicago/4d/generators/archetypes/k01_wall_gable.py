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
TYMPANUM_LIGHT_M = 0.08    # T-2917: a tympanum light's reveal, behind the tympanum's recess
COLONNETTE_BLOCK_M = 0.08  # T-2917: a colonnette's square base and capital, each this high
DOME_RINGS = 6             # T-3051: a pinnacle dome's rings, foot to knob
BLOCK_PLINTH_M = 0.12      # T-3051: a pinnacle block's plinth and cornice, each this high
BLOCK_CORNICE_M = 0.12
SCALE_COURSES = 5          # T-3064: a scaled pyramid's courses of scales, foot to tip
SCALE_LIP_M = 0.015        # T-3064: each course's foot standing proud of the one under it


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
    if "arch" in d["wall_gable"]:
        return out + arch_cutters(a, k5, P, xf, zc)
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


def arch(d, g) -> dict:
    """T-2917: the great arch's circle in the face's frame (x across it from its centre, y
    up from the face's foot), and the angles at which its intrados and extrados leave the
    pediment's foot, which is the cornice's top the ring stands on. T-2937: `Ro` is the
    archivolt's outermost edge, its hood's where it has one, and `to` that edge's angle."""
    ar = d["wall_gable"]["arch"]
    R, Re = ar["radius_m"], ar["radius_m"] + ar["ring_m"]
    Ro = Re + (ar["hood"]["ring_m"] if "hood" in ar else 0.0)
    cy = g["dhs"] - g["ys"] - ar["drop_m"]
    return {"R": R, "Re": Re, "Ro": Ro, "cy": cy, "ti": math.asin(ar["drop_m"] / R),
            "te": math.asin(ar["drop_m"] / Re), "to": math.asin(ar["drop_m"] / Ro)}


def _round_head(x, sill, w, h, n=8):
    """A round-headed light's outline (x across, y up), counter-clockwise from its sill."""
    r = w / 2
    spring = sill + h - r
    return [(x - r, sill), (x + r, sill)] + [(x + r * math.cos(math.pi * k / n), spring + r * math.sin(math.pi * k / n))
                                             for k in range(n + 1)]


def arch_cutters(a, k5, P, xf, zc) -> list:
    """The tympanum under the great arch, recessed `depth_m`, and its round-headed lights cut
    on through it to a dark back, and the crown light over the arch where the record has one.
    Refuses an arch whose ring, or a crown light, would run into the raking cornice."""
    d, g = a.p.dormer, a.dormer_geom
    ar, A = d["wall_gable"]["arch"], arch(d, g)
    pd = pediment(d, g)
    clear = (pd["inner"] - (g["ys"] + A["cy"])) / pd["cq"]    # the centre to the raking cornice's inner edge
    if A["Ro"] > clear - 0.03:
        raise ValueError("the wall gable's arch runs into its raking cornice")
    ys, n = g["ys"], 24
    curve = [A["ti"] + (math.pi - 2 * A["ti"]) * k / n for k in range(n + 1)]
    tym = [(zc - A["R"] * math.cos(t), ys + A["cy"] + A["R"] * math.sin(t)) for t in curve]
    out = [k5.extrude(tym, xf - ar["depth_m"], xf + 0.05, P, "dormer_face", "dormer_face", "hidden")]
    foot = g["dhs"] - ys
    for lt in ar["lights"]:
        pts = _round_head(lt["at_m"], foot + lt["sill_m"], lt["width_m"], lt["height_m"])
        out.append(k5.extrude([(zc - x, ys + y) for x, y in pts], xf - ar["depth_m"] - TYMPANUM_LIGHT_M,
                              xf + 0.05, P, "reveal", "backing", "reveal"))
    cl = ar.get("crown_light")
    if cl:   # the small light in the pediment over the arch's crown
        top = foot + cl["sill_m"] + cl["height_m"]
        if foot + cl["sill_m"] < A["cy"] + A["Ro"] + 0.05:
            raise ValueError("the wall gable's crown light stands on its arch's ring")
        if cl["width_m"] / 2 > (pd["inner"] - ys - top) / g["dt"] - 0.05:
            raise ValueError("the wall gable's crown light runs into its raking cornice")
        pts = _round_head(0.0, foot + cl["sill_m"], cl["width_m"], cl["height_m"])
        out.append(k5.extrude([(zc - x, ys + y) for x, y in pts], xf - TYMPANUM_LIGHT_M, xf + 0.05, P,
                              "reveal", "backing", "reveal"))
    a.wall_gable = {"arch_m": [round(A["R"], 4), round(A["Re"], 4), round(ys + A["cy"], 4)]}
    if "hood" in ar:
        a.wall_gable["hood_m"] = round(A["Ro"], 4)
    return out


def _arch_dress(a, frame, O, conf):
    """The great arch's ring of voussoirs standing on the cornice, and the colonnettes
    between and beside the flat-headed lights under it, in the face's own stone."""
    k, af = _k01(), _af()
    d, g = a.p.dormer, a.dormer_geom
    ar, A = d["wall_gable"]["arch"], arch(d, g)
    wd, sc, cy, n = d["width_m"], d["width_m"] / 2, A["cy"], ar["stones"]
    ang = [A["ti"] + (math.pi - 2 * A["ti"]) * i / n for i in range(n + 1)]
    out = list(ang)
    out[0], out[-1] = A["te"], math.pi - A["te"]      # the springers' beds lie on the cornice
    aseed = a.instance("k01.opening.gable_arch", "opening",
                       {"radius_m": ar["radius_m"], "ring_m": ar["ring_m"], "proud_m": ar["proud_m"],
                        "stones": n, "lights": len(ar["lights"])},
                       {"crown": k._add(O, k._add(k._mul(frame[1], sc), k._mul(k.Y, cy + A["Re"])))})
    for i in range(n):
        poly = [(sc + A["R"] * math.cos(ang[i]), cy + A["R"] * math.sin(ang[i])),
                (sc + A["Re"] * math.cos(out[i]), cy + A["Re"] * math.sin(out[i])),
                (sc + A["Re"] * math.cos(out[i + 1]), cy + A["Re"] * math.sin(out[i + 1])),
                (sc + A["R"] * math.cos(ang[i + 1]), cy + A["R"] * math.sin(ang[i + 1]))]
        _prism(a, "dormer_stone", frame, k._inset(poly, [JOINT_M] * 4), 0.0, ar["proud_m"], aseed, conf)
    hd = ar.get("hood")
    if hd:
        # T-2937: the archivolt's outer order, the plate's moulded hood round the ring: cut on
        # the voussoirs' own joints, standing prouder than they do, its ends on the cornice
        hang = list(ang)
        hang[0], hang[-1] = A["to"], math.pi - A["to"]
        for i in range(n):
            poly = [(sc + A["Re"] * math.cos(out[i]), cy + A["Re"] * math.sin(out[i])),
                    (sc + A["Ro"] * math.cos(hang[i]), cy + A["Ro"] * math.sin(hang[i])),
                    (sc + A["Ro"] * math.cos(hang[i + 1]), cy + A["Ro"] * math.sin(hang[i + 1])),
                    (sc + A["Re"] * math.cos(out[i + 1]), cy + A["Re"] * math.sin(out[i + 1]))]
            _prism(a, "dormer_stone", frame, k._inset(poly, [JOINT_M] * 4), 0.0, hd["proud_m"], aseed, conf)
    # the colonnettes: a square base on the lights' sill line, a round shaft and a square
    # capital under the cornice, each standing out of the face by its own radius
    co = ar["colonnettes"]
    r, b = co["radius_m"], co["block_m"]
    y0 = g["ys"] + d["sash"]["sill_m"]
    y1 = pediment(d, g)["cornice_low"]
    Fr = ((O[0], 0.0, O[2]), frame[1], frame[2])
    for c in co["at_m"]:
        s = sc + c
        cseed = a.instance("k01.wall.gable_colonnette", "wall", {"radius_m": r, "height_m": round(y1 - y0, 4)},
                           {"foot": k._add(O, k._add(k._mul(frame[1], s), k._mul(k.Y, y0 - g["ys"])))})
        af._box(a, "dormer_stone", Fr, s - b, s + b, y0, y0 + COLONNETTE_BLOCK_M, r - b, r + b, cseed, conf,
                skip=("back", "bottom"))
        af._frustum(a, "dormer_stone", Fr, s, r, y0 + COLONNETTE_BLOCK_M, y1 - COLONNETTE_BLOCK_M, r, r * 0.9,
                    cseed, conf)
        af._box(a, "dormer_stone", Fr, s - b, s + b, y1 - COLONNETTE_BLOCK_M, y1, r - b, r + b, cseed, conf,
                skip=("back", "top"))


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


def _scaled(a, mat, frame, lo, hi, y0, y1, seed, conf, scaled=True):
    """T-3064: a cap's stone from the rectangle `lo` (s0, s1, d0, d1) at `y0` to `hi` at `y1`
    (a point for a pyramid), laid in courses of scales, each course's foot standing
    `SCALE_LIP_M` proud of the one under it (1811's north pinnacle, the plate's scaled
    stone), or plain, in one course."""
    af = _af()
    n = SCALE_COURSES if scaled else 1
    at = lambda f, e: tuple(p + (q - p) * f + e * sg for p, q, sg in zip(lo, hi, (-1, 1, -1, 1)))
    for i in range(n):
        ya, yb = y0 + (y1 - y0) * i / n, y0 + (y1 - y0) * (i + 1) / n
        ra, rb = at(i / n, SCALE_LIP_M if i else 0.0), at((i + 1) / n, 0.0)
        A = [(ra[0], ya, ra[2]), (ra[1], ya, ra[2]), (ra[1], ya, ra[3]), (ra[0], ya, ra[3])]
        B = [(rb[0], yb, rb[2]), (rb[1], yb, rb[2]), (rb[1], yb, rb[3]), (rb[0], yb, rb[3])]
        for j in range(PIN_SIDES):
            k_ = (j + 1) % PIN_SIDES
            out = ((A[j][0] + A[k_][0]) / 2 - (ra[0] + ra[1]) / 2, 0.4, (A[j][2] + A[k_][2]) / 2 - (ra[2] + ra[3]) / 2)
            pts = [A[j], A[k_], B[k_]] if B[j] == B[k_] else [A[j], A[k_], B[k_], B[j]]
            af._face(a, mat, frame, pts, out, seed, conf)
        if i:
            af._face(a, mat, frame, A, (0.0, -1.0, 0.0), seed, conf)


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
                                                "wall_gable": True, **a.wall_gable},
               {"base": O, "top": k._add(O, k._mul(k.Y, hf))})
    if not hasattr(a, "_kit"):
        a._kit = k6.load()
    v = _variant(d, k6)
    sw, sh, sill = d["sash"]["width_m"], d["sash"]["height_m"], d["sash"]["sill_m"]
    vs = wg.get("voussoirs")     # T-2917: under a great arch the lights stand between colonnettes
    top = sill + hd.apex() + (vs["ring_m"] if vs else 0.0)
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
        if not vs:
            continue
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
    if "arch" in wg:
        _arch_dress(a, frame, O, conf)
    # the pinnacles: square shafts either side of the face's foot, from under the wall
    # head (through the eave) past the face's eave, a cap and a pyramid over each (T-3064:
    # or, under a block, only to a band below the eave, the block taking the eave's end)
    pn = wg["pinnacles"]
    hw = pn["shaft_m"] / 2
    heads = pn.get("heads")
    pd = pediment(d, g) if pn.get("engage") or heads else None
    rake = lambda s_: pd["apex"] - abs(s_ - wd / 2) * g["dt"]
    if pn.get("engage"):
        # T-2937: a shaft that takes the rake's end must stand clear over the rake where the
        # rake enters it, at its inner face, or the raking cornice would run over its cap
        # (T-3051: unless a block over the shaft takes the rake's foot instead)
        for i, h in enumerate(heads or [None, None]):
            top = h["top_m"] if h else pn["top_m"]
            if h and "block" in h:
                continue
            if g["ys"] + top < pd["apex"] - (pn["at_m"] - hw) * g["dt"] + 0.25:
                raise ValueError("the wall gable's rake runs over its pinnacles' caps")
    for i, sg in enumerate((-1, 1)):
        s = wd / 2 + sg * pn["at_m"]
        h = heads[i] if heads else None
        top_m, spire_m = (h["top_m"], h["spire_m"]) if h else (pn["top_m"], pn["spire_m"])
        y0, y1 = g["ys"] + pn["foot_m"], g["ys"] + top_m
        pseed = a.instance("k01.roof.gable_pinnacle", "roof",
                           {"shaft_m": pn["shaft_m"], "top_m": round(y1, 4), "cap_m": pn["cap_m"],
                            "spire_m": spire_m, **({"spire": h["spire"]} if h else {})},
                           {"foot": k._add(O, k._add(k._mul(R, s), k._mul(k.Y, pn["foot_m"])))})
        Fr = ((O[0], 0.0, O[2]), R, N)
        af._box(a, "limestone_trim", Fr, s - hw, s + hw, y0, y1, -hw, hw, pseed, conf, skip=("bottom", "top"))
        c = hw + PIN_CAP_PROUD_M
        af._box(a, "limestone_trim", Fr, s - c, s + c, y1, y1 + pn["cap_m"], -c, c, pseed, conf)
        if h and h["spire"] == "dome":
            # T-3051: a dome on the cap (1811's south pinnacle: the plate's scaled dome),
            # its profile a quarter ellipse from the cap's half-width, closed by a knob
            yb, rr = y1 + pn["cap_m"], c - 0.01
            n = DOME_RINGS
            ring = [(yb + spire_m * 0.85 * math.sin(math.pi / 2 * j / n), rr * math.cos(math.pi / 2 * j / n))
                    for j in range(n + 1)]
            ring[-1] = (ring[-1][0], 0.03)
            for (ya, ra), (yb_, rb) in zip(ring, ring[1:]):
                af._frustum(a, "limestone_trim", Fr, s, 0.0, ya, yb_, ra, rb, pseed, conf)
            yk = ring[-1][0]
            af._frustum(a, "limestone_trim", Fr, s, 0.0, yk, yb + spire_m, 0.03, 0.004, pseed, conf)
        elif h and "block" in h and top_m <= d["face_height_m"]:
            # T-3064: a shaft stopped under its block (the plate's north pinnacle, its band level
            # with the horizontal cornice): the cap's stone rises from the band, leaning in, to
            # the block's plinth, so the eave's end dies into it under the block
            b, c = h["block"], hw + PIN_CAP_PROUD_M
            sc, bw = s - sg * b["in_m"], b["width_m"] / 2
            yt = g["ys"] + b["foot_m"]
            _scaled(a, "limestone_trim", Fr, (s - c, s + c, -c, c), (sc - bw, sc + bw, -bw, bw),
                    y1 + pn["cap_m"], yt, pseed, conf, h["spire"] == "scaled_pyramid")
            # the eave's end, where it leaves the face's edge, must die into that stone
            o, t = (d["width_m"] / 2 + g["overhang"]) - pn["at_m"], (g["dhe"] - y1 - pn["cap_m"]) / (yt - y1 - pn["cap_m"])
            if not 0.0 < t < 1.0 or (1 - t) * c + t * (b["in_m"] - bw) * -1 < o - 1e-6:
                raise ValueError(f"the wall gable's eave leaves its pinnacle's stone under the block: its end "
                                 f"{o:.3f} m past the shaft's centre at {g['dhe']:.3f} m")
        elif h and h["spire"] == "scaled_pyramid":
            _scaled(a, "limestone_trim", Fr, (s - hw, s + hw, -hw, hw), (s, s, 0.0, 0.0),
                    y1 + pn["cap_m"], y1 + pn["cap_m"] + spire_m, pseed, conf)
        else:
            _pyramid(a, "limestone_trim", Fr, s, 0.0, y1 + pn["cap_m"], hw, y1 + pn["cap_m"] + spire_m, pseed, conf)
        if h and "block" in h:
            # T-3051: the moulded block over the low shaft's inner side, taking the rake's foot
            # (the plate's north pinnacle): a plinth, a die and a cornice, square on plan
            b = h["block"]
            sc = s - sg * b["in_m"]
            yf, yt = g["ys"] + b["foot_m"], g["ys"] + b["foot_m"] + b["height_m"]
            inner = sc - sg * b["width_m"] / 2
            if not yf < rake(inner) < yt - 0.25 or not yf <= rake(s - sg * hw) + 0.1:
                raise ValueError(f"the wall gable's rake does not die into its pinnacle's block: the rake at "
                                 f"{rake(inner):.3f} m by its inner face and {rake(s - sg * hw):.3f} m by the "
                                 f"shaft's, the block {yf:.3f}-{yt:.3f} m (wall head {g['ys']:.3f} m)")
            bw = b["width_m"] / 2
            for (ya, yb_, hb) in ((yf, yf + BLOCK_PLINTH_M, bw), (yf + BLOCK_PLINTH_M, yt - BLOCK_CORNICE_M, bw - 0.04),
                                  (yt - BLOCK_CORNICE_M, yt, bw + 0.03)):
                af._box(a, "limestone_trim", Fr, sc - hb, sc + hb, ya, yb_, -hb, hb, pseed, conf)
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
