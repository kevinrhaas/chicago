"""T-2366: a K02 stone street front read off a photograph — round arches, keystones, a frieze,
a pilastered frontispiece, an arched portico and the iron at its windows.

TICKET T-2366. 1612 Prairie's own photograph (data/sources/assets/goodman_1612_photo_owner_
2026_10) shows what its record's paraphrase did not: every window round-headed, each group
under a block of voussoirs whose joints radiate into the banded stone and a long tapered
keystone; a dark frieze with small lights between the stone and the bracketed cornice; the
door behind an arched portico on four columns, framed by two pilasters under a hood; iron
guards at the principal windows and grilles in the basement lights. The record names all of
it (`street_front_openings`, `street_front_dress`); k01_frontage_params resolves it into
`params.arched_front`, and this module lays it, called by k01_frontage.stone_front:

  plan()  before the coursing: the obstacles the courses go round (each group's clear hole to
          its spring and its voussoir block above), and the seats of what stands proud of the
          face (keystones, pilasters, hood), so the stones under them are laid flush
  lay()   after it: the voussoirs, the piers between paired lights, the keystones, the
          frieze, the frontispiece, the portico and the iron

A voussoir block is cut into wedges from each light's centre along K06's own head vertices
(k06_windows.Head.curve: 12 segments over the half circle), so every intrados edge is the
reveal's edge and no sliver of wall is left open; the two segments at the crown are one
stone, which the keystone covers. Each wedge runs out to the block's rectangle, so the arch's
joints radiate into the coursing as the photograph shows. Every number a piece is cut to is
the record's or is named here, and docs/LIBERTIES.md L-k01-1612-goodman-2366 says which.
"""

from __future__ import annotations

import math

ROUND_SEGMENTS = 12          # k06_windows.Head.curve's segments over a round head
KEYSTONE_PROUD_M = 0.06      # the keystone's face before the wall's
FRIEZE_RECESS_M = 0.12       # a frieze light's glass behind the frieze's face
FILLET = (0.08, 0.04)        # the frieze's foot: a fillet this high, this proud
IRON_BAR_M = 0.018           # a guard's or grille's square bar
SHAFT_SIDES = 16
SCROLL_SEGMENTS = 18         # T-2818: one grille scroll's volute, in straight runs of bar
BELT_PROUD_M = 0.05          # T-2819: a belt course's face before the wall (k01_frontage.stone_front's F)


def _k01():
    from . import k01_frontage
    return k01_frontage


def groups_of(params):
    return (params.arched_front or {}).get("groups", ())


def grouped_ops(params) -> set:
    return {i for g in groups_of(params) for i in g["ops"]}


def plan(a, frame):
    """The rectangles the coursing goes round, and the seats of what stands proud."""
    p, af = a.p, a.p.arched_front
    rects = []
    for g in af["groups"]:
        L, R = g["cuts"][0], g["cuts"][-1]
        rects.append((g["lights"][0][0], g["lights"][-1][1], g["sill_m"], g["spring_m"]))   # the clear hole
        rects.append((L, R, g["spring_m"], g["top_m"]))                                      # the voussoir block
        k = g["keystone"]
        w = max(k["width_m"]) / 2
        a.seat(frame, [(k["s_m"] - w, k["bed_m"], 0.0), (k["s_m"] + w, k["top_m"], 0.0)], "K01.keystone")
    fp = af["frontispiece"]
    if fp:
        for s0, s1 in fp["pilaster_s_m"]:
            a.seat(frame, [(s0, p.principal_floor_m, 0.0), (s1, fp["hood"]["bed_m"], 0.0)], "K01.pilaster")
        h = fp["hood"]
        a.seat(frame, [(h["s_m"][0], h["bed_m"], 0.0), (h["s_m"][1], h["top_m"], 0.0)], "K01.hood")
    po = af["portico"]
    if po and po.get("archivolt_m"):
        # T-2369: the imposts and the ring are all that meet the wall
        c, (i0, i1) = po["centre_s_m"], po["impost_m"]
        hw, ro = po["half_width_m"], po["arch_radius_m"] + po["archivolt_m"]
        if po.get("impost_from_m", 0.0) < 1e-6:
            a.seat(frame, [(c - hw, i0, 0.0), (c + hw, i1, 0.0)], "K01.portico")
        if "archivolt_depth_m" not in po:
            sp = po.get("spring_m", i1)
            a.seat(frame, [(c - ro, sp, 0.0), (c + ro, sp + po.get("arch_rise_m", po["arch_radius_m"]) + po["archivolt_m"], 0.0)],
                   "K01.portico")
    elif po:
        c, hw = po["centre_s_m"], po["half_width_m"] + po["cornice_overhang_m"]
        a.seat(frame, [(c - hw, po["impost_m"][0], 0.0), (c + hw, po["cornice_m"][1], 0.0)], "K01.portico")
    return rects


# -- small solids ----------------------------------------------------------------------

def _P(frame, s, y, d):
    k = _k01()
    O, R, N = frame
    return k._add(k._add(k._add(O, k._mul(R, s)), k._mul(k.Y, y)), k._mul(N, d))


def _face(a, mat, frame, pts, hint, seed, conf, au=None, av=None):
    """A planar convex face given in (s, y, d); its UVs metres along `au`/`av` (default the
    wall's R and Y, or N where the face is level)."""
    k = _k01()
    O, R, N = frame
    W = [_P(frame, *q) for q in pts]
    h = k._add(k._add(k._mul(R, hint[0]), k._mul(k.Y, hint[1])), k._mul(N, hint[2]))
    n = (0.0, 0.0, 0.0)
    for i, q in enumerate(W):
        r = W[(i + 1) % len(W)]
        n = k._add(n, ((q[1] - r[1]) * (q[2] + r[2]), (q[2] - r[2]) * (q[0] + r[0]), (q[0] - r[0]) * (q[1] + r[1])))
    if k._dot(n, n) < 1e-16:
        return
    n = k._unit(n)
    if k._dot(n, h) < 0:
        n = k._mul(n, -1)
    if au is None:
        au = R if abs(k._dot(n, R)) < 0.9 else N
    if av is None:
        av = k.Y if abs(k._dot(n, k.Y)) < 0.9 else N
    a.prim(mat).face(W, n, a.basis(mat, O, au, av, seed), conf)


def _box(a, mat, frame, s0, s1, y0, y1, d0, d1, seed, conf, skip=()):
    """A box in the wall's frame; `skip` names faces not drawn: 'back' (d0), 'front' (d1),
    'bottom', 'top', 'left' (s0), 'right' (s1)."""
    faces = {
        "front": ([(s0, y0, d1), (s1, y0, d1), (s1, y1, d1), (s0, y1, d1)], (0, 0, 1)),
        "back": ([(s0, y0, d0), (s1, y0, d0), (s1, y1, d0), (s0, y1, d0)], (0, 0, -1)),
        "bottom": ([(s0, y0, d0), (s1, y0, d0), (s1, y0, d1), (s0, y0, d1)], (0, -1, 0)),
        "top": ([(s0, y1, d0), (s1, y1, d0), (s1, y1, d1), (s0, y1, d1)], (0, 1, 0)),
        "left": ([(s0, y0, d0), (s0, y1, d0), (s0, y1, d1), (s0, y0, d1)], (-1, 0, 0)),
        "right": ([(s1, y0, d0), (s1, y1, d0), (s1, y1, d1), (s1, y0, d1)], (1, 0, 0)),
    }
    for name, (pts, hint) in faces.items():
        if name not in skip:
            _face(a, mat, frame, pts, hint, seed, conf)


def _frustum(a, mat, frame, s, d, y0, y1, r0, r1, seed, conf):
    """A column shaft: a frustum of SHAFT_SIDES faces, no ends (a base and a capital close it)."""
    ring = lambda y, r: [(s + r * math.cos(2 * math.pi * i / SHAFT_SIDES), y, d + r * math.sin(2 * math.pi * i / SHAFT_SIDES))
                         for i in range(SHAFT_SIDES)]
    lo, hi = ring(y0, r0), ring(y1, r1)
    for i in range(SHAFT_SIDES):
        j = (i + 1) % SHAFT_SIDES
        mid = 2 * math.pi * (i + 0.5) / SHAFT_SIDES
        _face(a, mat, frame, [lo[i], lo[j], hi[j], hi[i]], (math.cos(mid), 0.0, math.sin(mid)), seed, conf)


# -- the voussoir block ----------------------------------------------------------------

def _hit(cx, cy, ang, L, R, top):
    c, s = math.cos(ang), math.sin(ang)
    t = []
    if c > 1e-9:
        t.append((R - cx) / c)
    if c < -1e-9:
        t.append((L - cx) / c)
    if s > 1e-9:
        t.append((top - cy) / s)
    k = min(t)
    return (cx + k * c, cy + k * s)


def wedges(cx, cy, r, L, R, top, merge_crown=True):
    """The block L..R x cy..top cut into stones radiating from (cx, cy) along a round head's
    vertices at radius r: each a convex polygon, counter-clockwise, as
    (points, edge kinds) — 'intrados', 'radial', or 'side'/'top'/'spring' on the block."""
    angs = [math.pi * i / ROUND_SEGMENTS for i in range(ROUND_SEGMENTS + 1)]
    if merge_crown:
        h = ROUND_SEGMENTS // 2
        angs = angs[:h] + angs[h + 1:]
    corners = [(math.atan2(top - cy, R - cx), (R, top)), (math.atan2(top - cy, L - cx), (L, top))]
    out = []
    for a0, a1 in zip(angs, angs[1:]):
        A = (cx + r * math.cos(a0), cy + r * math.sin(a0))
        B = (cx + r * math.cos(a1), cy + r * math.sin(a1))
        pts = [A, _hit(cx, cy, a0, L, R, top)]
        pts += [q for ang, q in corners if a0 + 1e-6 < ang < a1 - 1e-6]
        pts += [_hit(cx, cy, a1, L, R, top), B]
        clean = []
        for q in pts:
            if not clean or math.dist(clean[-1], q) > 1e-6:
                clean.append(q)
        if math.dist(clean[0], clean[-1]) < 1e-6:
            clean.pop()
        kinds = []
        for i, q in enumerate(clean):
            n = clean[(i + 1) % len(clean)]
            if i == len(clean) - 1:
                kinds.append("intrados")
            elif abs(q[0] - n[0]) < 1e-6 and (abs(q[0] - L) < 1e-6 or abs(q[0] - R) < 1e-6):
                kinds.append("side")
            elif abs(q[1] - n[1]) < 1e-6 and abs(q[1] - top) < 1e-6:
                kinds.append("top")
            elif abs(q[1] - n[1]) < 1e-6 and abs(q[1] - cy) < 1e-6:
                kinds.append("spring")
            else:
                kinds.append("radial")
        out.append((clean, kinds, (a0 + a1) / 2))
    return out


def wedges_segmental(cx, spring, rise, radius, L, R, top):
    """T-2818: the block L..R x spring..top over a segmental head cut into stones radiating
    from the arc's centre (`radius` under the crown, below the spring) along K06's own head
    vertices (k06_windows.Head.curve: 8 segments over the arc), the two at the crown one
    stone, and at each end a skewback: the stone between the springing line, the block's
    side and the first joint, which a round head has no need of. Each as wedges() gives it."""
    cy = spring + rise - radius
    t0 = math.acos(max(-1.0, min(1.0, math.sqrt(max(radius * radius - (rise - radius) ** 2, 0.0)) / radius)))
    n = 8
    angs = [t0 + (math.pi - 2 * t0) * i / n for i in range(n + 1)]
    angs = angs[:n // 2] + angs[n // 2 + 1:]
    corners = [(math.atan2(top - cy, R - cx), (R, top)), (math.atan2(top - cy, L - cx), (L, top))]
    P = lambda t: (cx + radius * math.cos(t), cy + radius * math.sin(t))
    out = []
    # the skewbacks, right then left: spring line, side, (the block's top corner), the joint
    hr, hl = _hit(cx, cy, angs[0], L, R, top), _hit(cx, cy, angs[-1], L, R, top)
    right = [P(angs[0]), (R, spring)] + ([(R, top)] if hr[1] > top - 1e-6 and hr[0] < R - 1e-6 else []) + [hr]
    left = [(L, spring), P(angs[-1]), hl] + ([(L, top)] if hl[1] > top - 1e-6 and hl[0] > L + 1e-6 else [])
    for pts in (right, left):
        clean = []
        for q in pts:
            if not clean or math.dist(clean[-1], q) > 1e-6:
                clean.append(q)
        out.append((clean, ["spring"] + ["side"] * (len(clean) - 2) + ["radial"], math.pi / 2))
    for a0, a1 in zip(angs, angs[1:]):
        A, B = P(a0), P(a1)
        pts = [A, _hit(cx, cy, a0, L, R, top)]
        pts += [q for ang, q in corners if a0 + 1e-6 < ang < a1 - 1e-6]
        pts += [_hit(cx, cy, a1, L, R, top), B]
        clean = []
        for q in pts:
            if not clean or math.dist(clean[-1], q) > 1e-6:
                clean.append(q)
        out.append((clean, ["radial"] * (len(clean) - 1) + ["intrados"], (a0 + a1) / 2))
    return out


def wedges_elliptical(cx, spring, half, rise, L, R, top):
    """T-3134: the block L..R x spring..top over a half-elliptical head (semi-axes `half` and
    `rise`, centred on the springing line) cut into stones along K06's own head vertices
    (k06_windows.Head.curve: 12 equal steps of the parametric angle over the half), the two
    at the crown one stone, each joint run from the ellipse's centre through its vertex out
    to the block's edge. Each as wedges() gives it."""
    ts = [math.pi * i / ROUND_SEGMENTS for i in range(ROUND_SEGMENTS + 1)]
    h = ROUND_SEGMENTS // 2
    ts = ts[:h] + ts[h + 1:]
    P = lambda t: (cx + half * math.cos(t), spring + rise * math.sin(t))
    ang = lambda t: math.atan2(rise * math.sin(t), half * math.cos(t))
    corners = [(math.atan2(top - spring, R - cx), (R, top)), (math.atan2(top - spring, L - cx), (L, top))]
    out = []
    for t0, t1 in zip(ts, ts[1:]):
        a0, a1 = ang(t0), ang(t1)
        pts = [P(t0), _hit(cx, spring, a0, L, R, top)]
        pts += [q for an, q in corners if a0 + 1e-6 < an < a1 - 1e-6]
        pts += [_hit(cx, spring, a1, L, R, top), P(t1)]
        clean = []
        for q in pts:
            if not clean or math.dist(clean[-1], q) > 1e-6:
                clean.append(q)
        if math.dist(clean[0], clean[-1]) < 1e-6:
            clean.pop()
        out.append((clean, ["radial"] * (len(clean) - 1) + ["intrados"], (a0 + a1) / 2))
    return out


def _moulding(a, frame, g, mo, conf):
    """T-3134: a narrow moulded ring of light stone round an arch's intrados and down both
    jambs to the floor, as the Levy print shows 1812's porch arch: two faces stepped out from
    the opening's edge (`steps_m` broad, `proud_m` before the wall), on the head's own curve
    (k06_windows.Head, the hole K07 cuts) so its inner edge is the reveal's."""
    from . import k06_windows
    (s0, s1, spring, rise, floor), = g["lights"]
    el = g.get("elliptical")
    kind = "elliptical" if el else "segmental" if g.get("segmental") else "round"
    ros = rise / (s1 - s0)
    (w1, w2), (p1, p2) = mo["steps_m"], mo["proud_m"]
    seed = a.instance("k01.opening.arch_moulding", "opening",
                      {"of": g["component"], "head": kind, "width_m": round(w1 + w2, 4), "proud_m": p1},
                      {"springing": _P(frame, s0 - w1 - w2, spring, p1)})

    def path(off):
        hd = k06_windows.Head(kind, s0, s1, spring, ros)
        return [(s0 - off, floor)] + hd.curve(-off, s1 + off, s0 - off)[::-1] + [(s1 + off, floor)]
    sec = [(0.0, 0.0), (0.0, p1), (w1, p1), (w1, p2), (w1 + w2, p2), (w1 + w2, 0.0)]
    rings = {off: path(off) for off in (0.0, w1, w1 + w2)}
    cx = (s0 + s1) / 2
    # T-3135: an arch cut into a projection's corner: its moulding past the corner stands on
    # the projection's own face, as both 1812 photographs draw it, each face split at the corner
    cut = _k01().entrance_cut(a.p) if g["component"] == "k01.opening.door_leaf" else None

    def face(a, mat, frame, pts, hint, seed, conf, _put=_face):
        if cut is None:
            return _put(a, mat, frame, pts, hint, seed, conf)
        k, xc, fwd = (1.0 if cut["side"] == "left" else -1.0), cut["corner_s_m"], cut["proud_m"]
        for keep_in, dd in ((True, fwd), (False, 0.0)):   # the side within the bay goes forward
            res = []
            for i, q in enumerate(pts):
                r = pts[(i + 1) % len(pts)]
                dq, dr = k * (q[0] - xc), k * (r[0] - xc)
                if (dq <= 1e-9) == keep_in:
                    res.append(q)
                if (dq <= 1e-9) != (dr <= 1e-9):
                    t = dq / (dq - dr)
                    res.append(tuple(q[j] + (r[j] - q[j]) * t for j in range(3)))
            if len(res) >= 3 and max(abs(k * (x[0] - xc)) for x in res) > 1e-6:
                _put(a, mat, frame, [(x, y, d + dd) for x, y, d in res], hint, seed, conf)
    for (oa, da), (ob, db) in zip(sec, sec[1:]):
        A, B = rings[oa], rings[ob]
        for i in range(len(A) - 1):
            pts = [(*A[i], da), (*A[i + 1], da), (*B[i + 1], db), (*B[i], db)]
            if oa == ob:   # a riser: the innermost faces the opening, the outermost the wall
                m = ((A[i][0] + A[i + 1][0]) / 2, (A[i][1] + A[i + 1][1]) / 2)
                k = 1.0 if oa > 0 else -1.0
                o = (m[0] - cx, m[1] - spring) if m[1] > spring + 1e-9 else (m[0] - cx, 0.0)
                hint = (k * o[0], k * o[1], 0.0)
            else:
                hint = (0, 0, 1)
            face(a, "dress_stone", frame, pts, hint, seed, conf)
    for sg in (-1, 1):   # the feet, on the floor
        for (ra, rb, d) in ((0.0, w1, p1), (w1, w1 + w2, p2)):
            x0, x1 = sorted((cx + sg * ((s1 - s0) / 2 + ra), cx + sg * ((s1 - s0) / 2 + rb)))
            face(a, "dress_stone", frame, [(x0, floor, 0.0), (x1, floor, 0.0), (x1, floor, d), (x0, floor, d)],
                  (0, -1, 0), seed, conf)


def _keystone(a, frame, k, seed, conf):
    s, y0, y1 = k["s_m"], k["bed_m"], k["top_m"]
    w0, w1 = (x / 2 for x in k["width_m"])
    F = KEYSTONE_PROUD_M
    mat = "dress_stone"
    _face(a, mat, frame, [(s - w0, y0, F), (s + w0, y0, F), (s + w1, y1, F), (s - w1, y1, F)], (0, 0, 1), seed, conf)
    _face(a, mat, frame, [(s - w0, y0, 0.0), (s + w0, y0, 0.0), (s + w0, y0, F), (s - w0, y0, F)], (0, -1, 0), seed, conf)
    _face(a, mat, frame, [(s - w1, y1, 0.0), (s + w1, y1, 0.0), (s + w1, y1, F), (s - w1, y1, F)], (0, 1, 0), seed, conf)
    for sg in (-1, 1):
        _face(a, mat, frame, [(s + sg * w0, y0, 0.0), (s + sg * w1, y1, 0.0), (s + sg * w1, y1, F), (s + sg * w0, y0, F)],
              (sg, -0.2, 0), seed, conf)


def _curved(a, frame, g, conf, recess, cid, inst):
    """T-2531: one light's ring turned to a curved extrados, as 1621's drawing draws its door's:
    each voussoir cut between the head's radius and the ring's, standing `ring_proud_m`
    before the wall, and the block's spandrels round it laid as the wall's own stone, flush,
    with no joint between their pieces but the ring's. Returns the next stone's index."""
    k = _k01()
    O, R, N = frame
    wk = a.p.stone["wall"]
    hj = wk["joint_m"] / 2
    (s0, s1, spring, r, _sill), = g["lights"]
    cx, ro = (s0 + s1) / 2, r + g["lights"][0][0] - g["cuts"][0]
    angs = [math.pi * i / ROUND_SEGMENTS for i in range(ROUND_SEGMENTS + 1)]
    h = ROUND_SEGMENTS // 2
    angs = angs[:h] + angs[h + 1:]
    P = lambda rr, t: (cx + rr * math.cos(t), spring + rr * math.sin(t))
    j = 0
    for a0, a1 in zip(angs, angs[1:]):
        mid = (a0 + a1) / 2
        bed = k._unit(k._add(k._mul(R, math.cos(mid)), k._mul(k.Y, math.sin(mid))))
        a.stone(frame, [P(r, a0), P(ro, a0), P(ro, a1), P(r, a1)], [hj] * 4, "rough_stone_trim",
                a._stone_seed(cid, inst, j), conf, recess=recess, bevel=wk["bevel_m"], F=g["ring_proud_m"], bed=bed)
        j += 1
    for pts, kinds, mid in wedges(cx, spring, ro, g["cuts"][0], g["cuts"][-1], g["top_m"]):
        joints = [0.0 if kd == "radial" else hj for kd in kinds]
        a.stone(frame, pts, joints, "rough_stone_trim", a._stone_seed(cid, inst, j), conf,
                recess=recess, bevel=0.0, F=0.0)
        j += 1
    return j


def _voussoirs(a, frame, g, conf, recess):
    k = _k01()
    O, R, N = frame
    st = a.p.stone
    wk = st["wall"]
    cid = "k01.opening.round_arch"
    a.instance(cid, "opening", {"lights": len(g["lights"]), "spring_m": g["spring_m"], "top_m": g["top_m"],
                                "ring_m": round(g["lights"][0][0] - g["cuts"][0], 4),
                                "segments": ROUND_SEGMENTS, "of": g["component"]},
               {"springing": _P(frame, g["cuts"][0], g["spring_m"], 0.0),
                "crown": _P(frame, g["keystone"]["s_m"], g["keystone"]["bed_m"], 0.0)})
    inst = len(a.components[cid]["instances"]) - 1
    hj = wk["joint_m"] / 2
    j = 0
    if g.get("extrados") == "curved":
        j = _curved(a, frame, g, conf, recess, cid, inst)
    for i, (s0, s1, spring, r, sill) in enumerate(g["lights"] if g.get("extrados") != "curved" else ()):
        cx = (s0 + s1) / 2
        L, Rr = g["cuts"][i], g["cuts"][i + 1]
        sg = g.get("segmental")
        ws = (wedges_elliptical(cx, spring, (s1 - s0) / 2, r, L, Rr, g["top_m"]) if g.get("elliptical")
              else wedges_segmental(cx, spring, r, sg["radius_m"], L, Rr, g["top_m"]) if sg
              else wedges(cx, spring, r, L, Rr, g["top_m"]))
        for pts, kinds, mid in ws:
            bed = k._unit(k._add(k._mul(R, math.cos(mid)), k._mul(k.Y, math.sin(mid))))
            a.stone(frame, pts, [hj] * len(pts), "rough_stone_trim", a._stone_seed(cid, inst, j), conf,
                    recess=recess, bevel=wk["bevel_m"], F=0.0, bed=bed)
            j += 1
    # the piers between paired lights, from the sill to the spring: one stone each
    for (p0, p1) in g["piers"]:
        a.stone(frame, [(p0, g["sill_m"]), (p1, g["sill_m"]), (p1, g["spring_m"]), (p0, g["spring_m"])], [hj] * 4,
                "rough_stone_trim", a._stone_seed(cid, inst, j), conf, recess=recess, bevel=wk["bevel_m"], F=0.0)
        j += 1
    cl = loggia_columns(a.p, g)
    if cl:   # T-2918: the arch springs from clustered shafts in its jambs
        _jamb_columns(a, frame, g, cl, conf)
    cv = loggia_carving(a.p, g)
    if cv:   # T-2923: the loggia's carving stands where the keystone would (the print has none)
        _loggia_carving(a, frame, g, cv, conf)
        return
    if g.get("moulding"):   # T-3134: the moulded ring runs unbroken over the crown (the print has no keystone)
        _moulding(a, frame, g, g["moulding"], conf)
        return
    _keystone(a, frame, g["keystone"], a._stone_seed(cid, inst, j), conf)


# -- T-2923: 1801's loggia carving ----------------------------------------------------------

LOGGIA_ARCHES = ("k01.opening.door_leaf", "k01.opening.loggia_side_arch")


def loggia_carving(p, g) -> dict:
    """The loggia's carving (`entrance_kit.loggia.carving`) where `g` is one of its two arches,
    else an empty dict."""
    if g["component"] not in LOGGIA_ARCHES:
        return {}
    return (((p.entrance_kit or {}).get("loggia") or {}).get("carving")) or {}


def loggia_columns(p, g) -> dict:
    """T-2918: the loggia's jamb columns (`entrance_kit.loggia.columns`) where `g` is its
    mouth, else an empty dict."""
    if g["component"] != "k01.opening.door_leaf":
        return {}
    return (((p.entrance_kit or {}).get("loggia") or {}).get("columns")) or {}


def _jamb_columns(a, frame, g, cl, conf):
    """T-2918: 1811's porch mouth (the Inland Architect plate of October 1888): each side of
    the arch a cluster of round shafts standing before the jamb's face, `shafts_m` off the
    intrados outward, on one plinth a side, each shaft on a square base under a carved
    capital, a necking ring and a bell flaring to a square abacus whose top is the arch's
    springing. The plate's capitals are carved leafage finer than its 2.3 cm a pixel; the
    bell and abacus stand for it (docs/LIBERTIES.md L-k01-1811-ames-front-2541)."""
    (s0, s1, spring, r, floor), = g["lights"]
    c = (s0 + s1) / 2
    rs, pr = cl["radius_m"], cl["proud_m"]
    ph, bh, ch = cl["plinth_m"], cl["base_m"], cl["capital_m"]
    left, right = cl["shafts_m"]
    axes = [c - r - x for x in left] + [c + r + x for x in right]
    seed = a.instance("k01.wall.jamb_columns", "wall",
                      {"of": g["component"], "shafts": len(axes), "radius_m": rs,
                       "shafts_s_m": [round(x, 4) for x in axes], "plinth_top_m": round(floor + ph, 4),
                       "spring_m": round(spring, 4),
                       "carving": "a necking ring, a flared bell and an abacus standing for the plate's leafage"},
                      {"springing": _P(frame, c - r, spring, pr)})
    mat = "dress_stone"
    yp, yb, yc = floor + ph, floor + ph + bh, spring - ch
    bw, aw = rs + 0.03, rs * 1.55
    for sg, side in ((-1, left), (1, right)):
        ss = [c + sg * (r + x) for x in side]
        pa, pb = min(ss) - bw - 0.04, max(ss) + bw + 0.04
        # the plinth runs back into the jamb's face; its inner end stands on the intrados' line
        if sg < 0:
            pb = min(pb, c - r + rs)
        else:
            pa = max(pa, c + r - rs)
        _box(a, mat, frame, pa, pb, floor, yp, 0.0, pr + bw + 0.04, seed, conf, skip=("back", "bottom"))
        for sc in ss:
            _box(a, mat, frame, sc - bw, sc + bw, yp, yb, pr - bw, pr + bw, seed, conf, skip=("bottom",))
            _frustum(a, mat, frame, sc, pr, yb, yc, rs, rs * 0.92, seed, conf)
            # the necking ring, then the bell from the shaft out to the abacus' corners
            _frustum(a, mat, frame, sc, pr, yc, yc + 0.04, rs * 1.08, rs * 1.08, seed, conf)
            _frustum(a, mat, frame, sc, pr, yc + 0.04, spring - 0.06, rs * 0.92, aw, seed, conf)
            _box(a, mat, frame, sc - aw, sc + aw, spring - 0.06, spring, pr - aw, pr + aw, seed, conf)


def _raised(a, frame, poly, d0, d1, seed, conf, mat="dress_stone"):
    """A raised piece on a wall's face: the convex outline `poly` ((s, y), counter-clockwise),
    its face `d1` before the wall, its sides down to `d0` (at or under the face it stands on,
    so no side ends in the air); no back."""
    _face(a, mat, frame, [(s, y, d1) for s, y in poly], (0, 0, 1), seed, conf)
    for i in range(len(poly)):
        (s0, y0), (s1, y1) = poly[i], poly[(i + 1) % len(poly)]
        _face(a, mat, frame, [(s0, y0, d0), (s1, y1, d0), (s1, y1, d1), (s0, y0, d1)], (y1 - y0, s0 - s1, 0.0),
              seed, conf)


def _disc(cx, cy, rx, ry, n=12):
    return [(cx + rx * math.cos(2 * math.pi * i / n), cy + ry * math.sin(2 * math.pi * i / n)) for i in range(n)]


def _archivolt(a, frame, c, spring, r, floor, av, seed, conf):
    """The arch's moulded archivolt: two faces stepped out from the intrados (`steps_m` broad,
    `proud_m` before the wall), turned round the head and run down both jambs to the floor."""
    (w1, w2), (p1, p2) = av["steps_m"], av["proud_m"]
    n = ROUND_SEGMENTS

    def path(rho):
        return ([(c - rho, floor)] + [(c + rho * math.cos(math.pi * (n - i) / n), spring + rho * math.sin(math.pi * (n - i) / n))
                                      for i in range(n + 1)] + [(c + rho, floor)])
    r1, r2 = r + w1, r + w1 + w2
    # the section from the intrados out, (radius, proud); each step's riser faces the arch
    sec = [(r, 0.0), (r, p1), (r1, p1), (r1, p2), (r2, p2), (r2, 0.0)]
    rings = {rho: path(rho) for rho in (r, r1, r2)}
    for (ra, da), (rb, db) in zip(sec, sec[1:]):
        A, B = rings[ra], rings[rb]
        for i in range(len(A) - 1):
            pts = [(*A[i], da), (*A[i + 1], da), (*B[i + 1], db), (*B[i], db)]
            if ra == rb:   # a riser: it faces in (toward the arch) or, the outermost, out
                m = ((A[i][0] + A[i + 1][0]) / 2, (A[i][1] + A[i + 1][1]) / 2)
                k = 1.0 if ra == r2 else -1.0
                o = (m[0] - c, m[1] - spring) if m[1] > spring + 1e-9 else (m[0] - c, 0.0)
                hint = (k * o[0], k * o[1], 0.0)
            else:
                hint = (0, 0, 1)
            _face(a, "dress_stone", frame, pts, hint, seed, conf)
    for sg in (-1, 1):   # the feet, on the floor
        for (ra, rb, d) in ((r, r1, p1), (r1, r2, p2)):
            sa, sb = sorted((c + sg * ra, c + sg * rb))
            _face(a, "dress_stone", frame, [(sa, floor, 0.0), (sb, floor, 0.0), (sb, floor, d), (sa, floor, d)],
                  (0, -1, 0), seed, conf)


def _loggia_carving(a, frame, g, cv, conf):
    """T-2923: 1801's loggia carving (J. W. Taylor's c. 1895 photograph), on each of its two
    arches' faces: the archivolt (`_archivolt`); a carved pier each side, `off_m` outside the
    intrados and `width_m` broad, from the floor on a base to a capital under `top_m`, a
    chain of raised lozenges down its shaft; and a rosette in each spandrel, where the print
    shows carved leafage. The print's carving is finer than its 2.7 cm a pixel; what stands
    for it is reconstructed (docs/LIBERTIES.md L-kimball-1801-loggia-carving-2923)."""
    (s0, s1, spring, r, floor), = g["lights"]
    c = (s0 + s1) / 2
    av, pi = cv["archivolt"], cv["piers"]
    e1 = r + pi["off_m"] + pi["width_m"]
    seed = a.instance("k01.wall.loggia_carving", "wall",
                      {"of": g["component"], "archivolt_m": sum(av["steps_m"]), "piers_s_m": [c - e1, c + e1],
                       "piers_top_m": pi["top_m"],
                       "carving": "lozenge chains, spandrel rosettes and an archivolt standing for the print's"},
                      {"crown": _P(frame, c, spring + r, 0.0)})
    _archivolt(a, frame, c, spring, r, floor, av, seed, conf)
    e0 = r + pi["off_m"]
    e1 = e0 + pi["width_m"]
    pr, bh, ch, top = pi["proud_m"], pi["base_m"], pi["capital_m"], pi["top_m"]
    wl, hl = pi["lozenge_m"]
    ya, yb = floor + bh, top - ch
    n = max(1, math.floor((yb - ya - 0.08) / hl))
    y0 = (ya + yb) / 2 - n * hl / 2
    for sg in (-1, 1):
        pa, pb = sorted((c + sg * e0, c + sg * e1))
        _box(a, "dress_stone", frame, pa - 0.03, pb + 0.03, floor, ya, 0.0, pr + 0.03, seed, conf, skip=("back",))
        _box(a, "dress_stone", frame, pa, pb, ya, yb, 0.0, pr, seed, conf, skip=("back", "top", "bottom"))
        _box(a, "dress_stone", frame, pa - 0.04, pb + 0.04, yb, top, 0.0, pr + 0.04, seed, conf, skip=("back",))
        m = (pa + pb) / 2
        for k in range(n):
            yc = y0 + (k + 0.5) * hl
            _raised(a, frame, [(m, yc - hl / 2), (m + wl / 2, yc), (m, yc + hl / 2), (m - wl / 2, yc)],
                    pr - 0.005, pr + 0.02, seed, conf)
        # the spandrel's rosette, on the 45-degree line outside the archivolt
        rr = cv["rosette_m"]
        rho = r + sum(av["steps_m"]) + rr + 0.05
        sx, sy = c + sg * rho * math.sqrt(0.5), spring + rho * math.sqrt(0.5)
        _raised(a, frame, _disc(sx, sy, rr, rr), -0.005, 0.03, seed, conf)
        _raised(a, frame, _disc(sx, sy, rr * 0.45, rr * 0.45), 0.025, 0.05, seed, conf)
    if cv.get("frieze"):
        _loggia_frieze(a, frame, c, e1 + 0.04, top, cv["frieze"], cv["cartouche_band"], seed, conf)


def _loggia_frieze(a, frame, c, half, bed, fr, cb, seed, conf):
    """T-2932: over each of the loggia's arches, from capital to capital (`half` each side of the
    arch's axis), the Taylor print's two carved bands: the relief frieze on the capitals'
    line, its carving T-2819's guilloche standing for the print's leafage and figures, under a
    moulded course; and over that the cartouche band under the second storey's sill, an oval
    cartouche on the axis of the window over the arch and a roundel each side of it, where
    the print's scrolled frames stand. The print's carving is finer than its 2.7 cm a pixel;
    what stands for it is reconstructed (docs/LIBERTIES.md L-kimball-1801-loggia-frieze-2932)."""
    O, R, N = frame
    s0, s1 = c - half, c + half
    top, pf = fr["top_m"], fr["proud_m"]
    _box(a, "dress_stone", frame, s0, s1, bed, top, 0.0, pf, seed, conf, skip=("back",))
    # the guilloche on the frieze's face: _guilloche_run lays it on a belt BELT_PROUD_M out
    lift = _k01()._mul(N, pf - BELT_PROUD_M)
    gframe = (_k01()._add(O, lift), R, N)
    rings = _guilloche_run(a, gframe, s0, s1, bed, top, fr["guilloche"], seed, conf)
    # the moulded course over it: a fillet, then its face stepped out
    c0, c1 = top + fr["course_m"] * 0.35, top + fr["course_m"]
    _box(a, "dress_stone", frame, s0, s1, top, c0, 0.0, pf + 0.02, seed, conf, skip=("back", "bottom"))
    _box(a, "dress_stone", frame, s0, s1, c0, c1, 0.0, fr["course_proud_m"], seed, conf, skip=("back",))
    # the cartouche band, from the course to under the sill
    ct, pk = cb["top_m"], cb["proud_m"]
    _box(a, "dress_stone", frame, s0, s1, c1, ct, 0.0, pk, seed, conf, skip=("back", "bottom"))
    cw, chh = cb["cartouche_m"]
    yc = (c1 + ct) / 2
    _raised(a, frame, _disc(c, yc, cw / 2, chh / 2, 20), pk - 0.005, pk + 0.03, seed, conf)
    _raised(a, frame, _disc(c, yc, cw / 2 - 0.07, chh / 2 - 0.07, 20), pk + 0.025, pk + 0.05, seed, conf)
    rr = cb["roundel_m"]
    for sg in (-1, 1):
        sx = c + sg * (cw / 2 + (half - cw / 2) / 2)
        _raised(a, frame, _disc(sx, yc, rr, rr, 16), pk - 0.005, pk + 0.025, seed, conf)
        _raised(a, frame, _disc(sx, yc, rr * 0.5, rr * 0.5, 12), pk + 0.02, pk + 0.045, seed, conf)
    comp = a.components["k01.wall.loggia_carving"]["instances"][-1]["params"]
    comp.update({"frieze_m": [bed, top], "cartouche_band_m": [c1, ct], "frieze_rings": rings})


# -- the frieze ------------------------------------------------------------------------

def _frieze(a, frame, af, yf, length, conf):
    fr = af["frieze"]
    y0 = af["stone_top_m"]
    cid = "k01.wall.frieze"
    seed = a.instance(cid, "wall", {"bed_m": y0, "top_m": yf, "lights": len(fr["s_m"]),
                                    "light_m": [fr["width_m"], fr["height_m"]]},
                      {"bed": _P(frame, 0.0, y0, 0.0), "top": _P(frame, 0.0, yf, 0.0)})
    hw = fr["width_m"] / 2
    ly0, ly1 = fr["sill_m"], fr["sill_m"] + fr["height_m"]
    xs = sorted({0.0, length, *[x + d for x in fr["s_m"] for d in (-hw, hw)]})
    ys = [y0 + FILLET[0], ly0, ly1, yf]
    holes = [(x - hw, x + hw) for x in fr["s_m"]]
    for s0, s1 in zip(xs, xs[1:]):
        for b0, b1 in zip(ys, ys[1:]):
            if b0 == ly0 and any(abs(s0 - h0) < 1e-9 for h0, _ in holes):
                continue
            _face(a, "fascia", frame, [(s0, b0, 0.0), (s1, b0, 0.0), (s1, b1, 0.0), (s0, b1, 0.0)], (0, 0, 1), seed, conf)
    _box(a, "fascia", frame, 0.0, length, y0, y0 + FILLET[0], 0.0, FILLET[1], seed, conf, skip=("back",))
    D = FRIEZE_RECESS_M
    for h0, h1 in holes:
        for pts, hint in (([(h0, ly0, 0.0), (h1, ly0, 0.0), (h1, ly0, -D), (h0, ly0, -D)], (0, 1, 0)),
                          ([(h0, ly1, 0.0), (h1, ly1, 0.0), (h1, ly1, -D), (h0, ly1, -D)], (0, -1, 0)),
                          ([(h0, ly0, 0.0), (h0, ly1, 0.0), (h0, ly1, -D), (h0, ly0, -D)], (1, 0, 0)),
                          ([(h1, ly0, 0.0), (h1, ly1, 0.0), (h1, ly1, -D), (h1, ly0, -D)], (-1, 0, 0))):
            _face(a, "fascia", frame, pts, hint, seed, conf)
        # T-2369: 1612's frieze lights read white in its photograph, so a white-painted
        # panel stands behind each light's glass where another front shows the dark room
        _face(a, "frieze_panel" if fr.get("panel") else "backing", frame,
              [(h0, ly0, -D), (h1, ly0, -D), (h1, ly1, -D), (h0, ly1, -D)], (0, 0, 1), seed, conf)
        _face(a, "glass", frame, [(h0, ly0, -D + 0.03), (h1, ly0, -D + 0.03), (h1, ly1, -D + 0.03), (h0, ly1, -D + 0.03)],
              (0, 0, 1), seed, conf)


# -- the entrance: frontispiece and portico ----------------------------------------------

def _frontispiece(a, frame, fp, conf):
    p = a.p
    h = fp["hood"]
    cid = "k01.wall.frontispiece"
    seed = a.instance(cid, "wall", {"pilasters": len(fp["pilaster_s_m"]), "pilaster_proud_m": fp["pilaster_proud_m"],
                                    "hood_m": [h["bed_m"], h["top_m"]], "hood_proud_m": h["proud_m"]},
                      {"hood": _P(frame, sum(h["s_m"]) / 2, h["bed_m"], 0.0)})
    for s0, s1 in fp["pilaster_s_m"]:
        _box(a, "dress_stone", frame, s0, s1, p.principal_floor_m, h["bed_m"], 0.0, fp["pilaster_proud_m"], seed, conf,
             skip=("back", "top"))
    hs0, hs1 = h["s_m"]
    pr, mid = h["proud_m"], h["bed_m"] + h["fascia_m"]
    _box(a, "dress_stone", frame, hs0 + pr * 0.4, hs1 - pr * 0.4, h["bed_m"], mid, 0.0, pr * 0.6, seed, conf,
         skip=("back", "top"))
    _box(a, "dress_stone", frame, hs0, hs1, mid, h["top_m"], 0.0, pr, seed, conf, skip=("back", "bottom"))
    _face(a, "dress_stone", frame, [(hs0, mid, pr * 0.6), (hs1, mid, pr * 0.6), (hs1, mid, pr), (hs0, mid, pr)],
          (0, -1, 0), seed, conf)
    for e0, e1 in ((hs0, hs0 + pr * 0.4), (hs1 - pr * 0.4, hs1)):
        _face(a, "dress_stone", frame, [(e0, mid, 0.0), (e1, mid, 0.0), (e1, mid, pr * 0.6), (e0, mid, pr * 0.6)],
              (0, -1, 0), seed, conf)


def _portico(a, frame, po, conf):
    """Columns on pedestals, an impost block over each side's columns, and over the door
    either an arch block turned as a barrel from the wall to the front under a cornice slab
    or (T-2369, `archivolt_m`) a round archivolt alone on the imposts, as 1612's photograph
    shows its shallow portico: a curved ring with the wall seen over it."""
    c, hw, r = po["centre_s_m"], po["half_width_m"], po["arch_radius_m"]
    F = po["front_m"]
    i0, i1 = po["impost_m"]
    ring = po.get("archivolt_m")
    rise = po.get("arch_rise_m", r)      # T-2369: a rise under the radius turns an elliptical arch
    sp = po.get("spring_m", i1)          # T-2369: an archivolt may spring below its imposts' top
    top = sp + rise + ring if ring else po["cornice_m"][1]
    cid = "k01.wall.portico"
    seed = a.instance(cid, "wall", {"columns": len(po["columns_s_m"]) * len(po["columns_d_m"]), "front_m": F,
                                    "arch_radius_m": r, "impost_m": [i0, i1], "top_m": top,
                                    **({"archivolt_m": ring} if ring else {})},
                      {"crown": _P(frame, c, i1 + r, F)})
    mat = "dress_stone"
    ped, base_h = po["pedestal_m"], 0.08
    for sc in po["columns_s_m"]:
        for d in po["columns_d_m"]:
            _box(a, mat, frame, sc - ped / 2, sc + ped / 2, 0.0, po["pedestal_top_m"], d - ped / 2, d + ped / 2,
                 seed, conf, skip=("bottom",))
            b = ped * 0.8
            _box(a, mat, frame, sc - b / 2, sc + b / 2, po["pedestal_top_m"], po["pedestal_top_m"] + base_h,
                 d - b / 2, d + b / 2, seed, conf, skip=("bottom",))
            r0, r1 = po["shaft_radius_m"]
            _frustum(a, mat, frame, sc, d, po["pedestal_top_m"] + base_h, po["capital_bed_m"], r0, r1, seed, conf)
            cap = ped * 0.85
            _box(a, mat, frame, sc - cap / 2, sc + cap / 2, po["capital_bed_m"], i0, d - cap / 2, d + cap / 2,
                 seed, conf, skip=("top",))
    if ring:
        # the imposts: a block over each side's columns from the frontispiece's face
        # (`impost_from_m`) to the front and a little over it, and the archivolt springing
        # from their inner ends, its intrados `arch_radius_m` across and `arch_rise_m` high
        o, d0 = po.get("impost_overhang_m", 0.0), po.get("impost_from_m", 0.0)
        cap = po.get("impost_cap_m", 0.0)   # a cap this deep over the block, `o` over it all round
        back = ("back",) if d0 < 1e-6 else ()
        for s0, s1, out in ((c - hw, c - r - ring, -1), (c + r + ring, c + hw, 1)):
            if cap:
                _box(a, mat, frame, s0, s1, i0, i1 - cap, d0, F, seed, conf, skip=back + ("top",))
                e0, e1 = (s0 - o, s1) if out < 0 else (s0, s1 + o)
                _box(a, mat, frame, e0, e1, i1 - cap, i1, d0, F + o, seed, conf, skip=back)
            else:
                _box(a, mat, frame, s0, s1, i0, i1, d0, F + o, seed, conf, skip=back)
        # the ring: `archivolt_depth_m` deep at the front, or turned back to the wall
        b0 = F - po["archivolt_depth_m"] if "archivolt_depth_m" in po else 0.0
        n = ROUND_SEGMENTS
        E = lambda t, k: (c + (r + k) * math.cos(t), sp + (rise + k) * math.sin(t))
        for k in range(n):
            t0, t1 = math.pi * k / n, math.pi * (k + 1) / n
            p0, q0 = [E(t0, 0.0), E(t1, 0.0)], [E(t1, ring), E(t0, ring)]
            for dd, hz in ((F, 1), (b0, -1)) if b0 > 1e-6 else ((F, 1),):
                _face(a, mat, frame, [(x, y, dd) for x, y in p0 + q0], (0, 0, hz), seed, conf)
            tm = (t0 + t1) / 2
            for (x0, y0), (x1, y1), h in ((p0[0], p0[1], (-math.cos(tm), -math.sin(tm), 0)),
                                          (q0[1], q0[0], (math.cos(tm), math.sin(tm), 0))):
                _face(a, mat, frame, [(x0, y0, b0), (x1, y1, b0), (x1, y1, F), (x0, y0, F)], h, seed, conf)
        return
    # the side beams: the impost, wall to front
    for s0, s1, inner in ((c - hw, c - r, "right"), (c + r, c + hw, "left")):
        _box(a, mat, frame, s0, s1, i0, i1, 0.0, F, seed, conf, skip=("back", "top"))
    # the arch block: wedges about the springing centre, extruded wall to front
    for pts, kinds, mid in wedges(c, i1, r, c - hw, c + hw, po["top_m"], merge_crown=True):
        _face(a, mat, frame, [(q[0], q[1], F) for q in pts], (0, 0, 1), seed, conf)
        for i, kind in enumerate(kinds):
            q, n = pts[i], pts[(i + 1) % len(pts)]
            if kind == "intrados":
                h = (c - (q[0] + n[0]) / 2, i1 - (q[1] + n[1]) / 2, 0)
            elif kind == "side":
                h = (q[0] - c, 0, 0)
            else:
                continue
            _face(a, mat, frame, [(q[0], q[1], 0.0), (n[0], n[1], 0.0), (n[0], n[1], F), (q[0], q[1], F)], h, seed, conf)
    o = po["cornice_overhang_m"]
    c0, c1 = po["cornice_m"]
    _box(a, mat, frame, c - hw - o, c + hw + o, c0, c1, 0.0, F + o, seed, conf, skip=("back",))


# -- the iron ----------------------------------------------------------------------------

def _bar(a, frame, s0, s1, y0, y1, d0, d1, seed, conf):
    _box(a, "iron", frame, s0, s1, y0, y1, d0, d1, seed, conf)


def _guards(a, frame, af, conf):
    p = a.p
    bc, gr = af["balconettes"], af["grilles"]
    b = IRON_BAR_M
    for g in af["groups"]:
        if bc and g["component"] == bc["component"]:
            seed = a.instance("k01.opening.balconette", "opening", {"height_m": bc["height_m"], "proud_m": bc["proud_m"]},
                              {"sill": _P(frame, g["keystone"]["s_m"], g["sill_m"], 0.0)})
            s0, s1 = g["lights"][0][0] - 0.06, g["lights"][-1][1] + 0.06
            y0, y1, d = g["sill_m"] + bc["foot_m"], g["sill_m"] + bc["height_m"], bc["proud_m"]
            for yy in (y0, y1 - 0.03, (y0 + y1) / 2):
                _bar(a, frame, s0, s1, yy, yy + 0.03, d, d + 0.03, seed, conf)
            n = max(2, round((s1 - s0) / bc["pitch_m"]))
            for i in range(n + 1):
                x = s0 + (s1 - s0) * i / n
                x = min(max(x, s0 + b / 2), s1 - b / 2)
                _bar(a, frame, x - b / 2, x + b / 2, y0, y1, d + 0.006, d + 0.006 + b, seed, conf)
            for x in (s0, s1 - b):    # the guard's returns to the wall
                _bar(a, frame, x, x + b, y1 - 0.03, y1, 0.0, d, seed, conf)
        if gr and g["component"] == gr["component"]:
            seed = a.instance("k01.opening.grille", "opening", {"bars": gr["bars"]},
                              {"sill": _P(frame, g["keystone"]["s_m"], g["sill_m"], 0.0)})
            sc = gr.get("scrolls")
            for (s0, s1, spring, r, sill) in g["lights"]:
                cx, d = (s0 + s1) / 2, -gr["set_back_m"]
                # T-2818: under a segmental head the bars stop on its arc, centred below the spring
                sg = g.get("segmental")
                rad, cy = (sg["radius_m"], spring + r - sg["radius_m"]) if sg else (r, spring)
                foot = sc["foot_m"] if sc else None
                for i in range(1, gr["bars"] + 1):
                    x = s0 + (s1 - s0) * i / (gr["bars"] + 1)
                    yt = foot if sc else cy + math.sqrt(max(rad * rad - (x - cx) ** 2, 0.0)) - 0.03
                    _bar(a, frame, x - b / 2, x + b / 2, sill + 0.02, yt, d - b, d, seed, conf)
                for yy in ((sill + 0.25, foot - b) if sc else (sill + 0.25, spring - 0.15)):
                    _bar(a, frame, s0 + 0.02, s1 - 0.02, yy, yy + b, d - 2 * b, d - b, seed, conf)
                if sc:
                    _scrolls(a, frame, sc, s0 + 0.02, s1 - 0.02, foot, spring, d - b, d, seed, conf)


def _rod(a, frame, p0, p1, w, d0, d1, seed, conf):
    """An iron bar `w` wide in the wall's plane from (s, y) p0 to p1, d0..d1 deep: its face,
    its back and its two edges (its ends meet the next rod's)."""
    ds, dy = p1[0] - p0[0], p1[1] - p0[1]
    L = math.hypot(ds, dy)
    if L < 1e-6:
        return
    ns, ny = -dy / L * w / 2, ds / L * w / 2
    lo = [(p0[0] - ns, p0[1] - ny), (p1[0] - ns, p1[1] - ny)]
    hi = [(p0[0] + ns, p0[1] + ny), (p1[0] + ns, p1[1] + ny)]
    quad = [lo[0], lo[1], hi[1], hi[0]]
    _face(a, "iron", frame, [(x, y, d1) for x, y in quad], (0, 0, 1), seed, conf)
    _face(a, "iron", frame, [(x, y, d0) for x, y in quad], (0, 0, -1), seed, conf)
    for (e, f), hint in (((lo[0], lo[1]), (-ns, -ny, 0)), ((hi[0], hi[1]), (ns, ny, 0))):
        _face(a, "iron", frame, [(e[0], e[1], d0), (f[0], f[1], d0), (f[0], f[1], d1), (e[0], e[1], d1)], hint, seed, conf)


def _scrolls(a, frame, sc, s0, s1, foot, spring, d0, d1, seed, conf):
    """T-2818: a grille's band of scrolls, as 1623's drawing draws over its uprights: `count`
    volutes side by side between the band's foot bar and the springing, each a flat iron bar
    curled from the cell's edge into its centre, turned alternately, so the band reads as
    the drawing's row of C-scrolls."""
    n = int(sc["count"])
    w = (s1 - s0) / n
    hb = spring - foot
    rc = min(w, hb) / 2 - 0.012
    turns, seg = 1.5, SCROLL_SEGMENTS
    for i in range(n):
        cx, cy = s0 + w * (i + 0.5), foot + hb / 2
        hand = 1 if i % 2 == 0 else -1
        pts = []
        for j in range(seg + 1):
            t = j / seg
            ang = math.pi / 2 * (1 - hand) + hand * (math.pi * 0.25 + 2 * math.pi * turns * t)
            rr = rc * (1 - 0.65 * t)
            pts.append((cx + rr * math.cos(ang), cy + rr * math.sin(ang)))
        for p0, p1 in zip(pts, pts[1:]):
            _rod(a, frame, p0, p1, IRON_BAR_M, d0, d1, seed, conf)


def _beam(a, mat, frame, s, w, p0, p1, h, seed, conf):
    """A bar of section w (along the wall) by h, from (y, d) p0 to p1 in the plane at s."""
    dy, dd = p1[0] - p0[0], p1[1] - p0[1]
    L = math.hypot(dy, dd)
    ny, nd = -dd / L * h / 2, dy / L * h / 2           # half the section, square to the bar
    if ny < 0:
        ny, nd = -ny, -nd
    lo = [(p0[0] - ny, p0[1] - nd), (p1[0] - ny, p1[1] - nd)]
    hi = [(p0[0] + ny, p0[1] + nd), (p1[0] + ny, p1[1] + nd)]
    s0, s1 = s - w / 2, s + w / 2
    up = (0, ny, nd)
    for (a0, a1), hint in ((hi, up), (lo, (0, -ny, -nd))):
        _face(a, mat, frame, [(s0, a0[0], a0[1]), (s1, a0[0], a0[1]), (s1, a1[0], a1[1]), (s0, a1[0], a1[1])], hint, seed, conf)
    for x, hx in ((s0, -1), (s1, 1)):
        _face(a, mat, frame, [(x, lo[0][0], lo[0][1]), (x, lo[1][0], lo[1][1]), (x, hi[1][0], hi[1][1]),
                              (x, hi[0][0], hi[0][1])], (hx, 0, 0), seed, conf)
    for (e, f), hint in (((lo[0], hi[0]), (0, -dy, -dd)), ((lo[1], hi[1]), (0, dy, dd))):
        _face(a, mat, frame, [(s0, e[0], e[1]), (s1, e[0], e[1]), (s1, f[0], f[1]), (s0, f[0], f[1])], hint, seed, conf)


def _rails(a, frame, sr, conf):
    """T-2369: the stoop's iron rails, as 1612's photograph shows them on its cheekless
    stoop: on each side the K11 kit's stoop rail (k11_ironwork.json `stair_rail`) — a newel
    on the landing and one on the bottom tread, a handrail raked between them its height
    over the nosing line, two balusters on every tread at its quarter points — and at the
    foot the handrail turned down over the newel in a scroll `scroll_m` across."""
    import json
    from . import k01_frontage as K
    p = a.p
    R = json.loads((K.ROOT / "data" / "components" / "prairie_1904" / "k11_ironwork.json").read_text())["parts"]["stair_rail"]
    door = next(o for o in p.openings if o.component == "k01.opening.door_leaf")
    st = a.door_variant()["stair"]
    if st.get("cheeks"):
        raise ValueError("stoop_rails stand on a stoop's open ends; this stoop has stone cheeks")
    y0, n, r, g, L = p.door_floor_m, p.risers, p.riser_m, p.tread_m, p.landing_depth_m
    F = L + (n - 1) * g                                  # the last riser, at the foot
    nose = lambda d: y0 - (d - L) * r / g                # the nosing line
    tread = lambda d: y0 - min(n, max(0, math.floor((d - L) / g) + 1)) * r if d > L else y0
    H, nm, bm, rm, rw = R["height_m"], R["newel_m"], R["baluster_m"], R["rail_m"], R["rail_width_m"]
    # T-2817: on the stoop's own axis, which 1623's stands north of its door's
    cs = p.stoop_s_m(door.s_m)
    seed = a.instance("k11.rail.stoop_rail", "stair", {"risers": n, "rail_height_m": H, "sides": 2,
                                                       "balusters_per_tread": R["per_tread"],
                                                       "scroll_m": sr["scroll_m"]},
                      {"top": _P(frame, cs, y0 + H, L), "foot": _P(frame, cs, r + H, F)})
    d_top, d_foot = L - 0.12, F - g / 2
    sc = sr["scroll_m"]
    if sr.get("guard"):
        _landing_guard(a, frame, sr["guard"], cs, R, y0, d_top, g, seed, conf)
    for sg in (-1, 1):
        x = cs + sg * (p.stoop_width_m / 2 - R["inset_m"])
        rail_top = lambda d: nose(min(max(d, L), F)) + H
        for d in (d_top, d_foot):
            yt = rail_top(d) + 0.1
            _box(a, "iron", frame, x - nm / 2, x + nm / 2, tread(d), yt, d - nm / 2, d + nm / 2, seed, conf,
                 skip=("bottom",))
        _beam(a, "iron", frame, x, rw, (rail_top(d_top), d_top), (rail_top(d_foot), d_foot), rm, seed, conf)
        for k in range(1, n):
            for q in [(j + 0.5) / R["per_tread"] for j in range(R["per_tread"])]:
                d = L + (k - 1) * g + q * g
                if d >= d_foot - nm:
                    continue
                _box(a, "iron", frame, x - bm / 2, x + bm / 2, tread(d), rail_top(d), d - bm / 2, d + bm / 2,
                     seed, conf, skip=("bottom",))
        # T-3184: a panel of scrolls along the rake under the handrail (1834's photograph: the
        # rails are scrolled cast-iron panels on newels), between it and a bar `panel_m` below
        pm = sr.get("panel_m")
        if pm:
            lo = lambda d: rail_top(d) - pm
            _beam(a, "iron", frame, x, rw, (lo(d_top), d_top), (lo(d_foot), d_foot), rm * 0.6, seed, conf)
            n_c = max(2, round((d_foot - d_top) / 0.24))
            cell = (d_foot - d_top) / n_c
            rc = min(cell, pm) / 2 - 0.015
            for c in range(n_c):
                dc = d_top + cell * (c + 0.5)
                yc = rail_top(dc) - pm / 2
                hand = 1 if c % 2 == 0 else -1
                pts = []
                for j in range(SCROLL_SEGMENTS + 1):
                    t = j / SCROLL_SEGMENTS
                    ang = math.pi / 2 * (1 - hand) + hand * (math.pi * 0.25 + 2 * math.pi * 1.5 * t)
                    rr_ = rc * (1 - 0.65 * t)
                    pts.append((yc + rr_ * math.sin(ang), dc + rr_ * math.cos(ang)))
                for p0, p1 in zip(pts, pts[1:]):
                    _beam(a, "iron", frame, x, rw * 0.6, p0, p1, IRON_BAR_M, seed, conf)
        # the scroll: the handrail carried past the foot newel and turned down in a half turn
        cy, cd = rail_top(d_foot) - sc / 2, d_foot
        pts = [(cy + sc / 2 * math.cos(t), cd + sc / 2 * math.sin(t))
               for t in (math.pi * j / 6 for j in range(7))]
        for p0, p1 in zip(pts, pts[1:]):
            _beam(a, "iron", frame, x, rw, p0, p1, rm * 0.8, seed, conf)


def _landing_guard(a, frame, gd, cs, R, y0, d, g, seed, conf):
    """T-2817: the landing's guard, as 1623's drawing draws it at the stoop's head: from the
    stoop rail's head newel along the landing's street edge to `to_v_m`, where a newel ends
    it — the stoop rail's height, newel, handrail and baluster pitch, a foot bar, and between
    `panel_v_m` an ornamental panel in place of the balusters: a lozenge of flat bar on a
    ring, framed by two posts (the drawing's panel of iron ornament, there too small to read)."""
    p = a.p
    H, nm, bm, rm, rw = R["height_m"], R["newel_m"], R["baluster_m"], R["rail_m"], R["rail_width_m"]
    b = IRON_BAR_M
    side = 1.0 if gd["to_v_m"] > cs else -1.0
    xa = cs + side * (p.stoop_width_m / 2 - R["inset_m"])        # the stoop rail's head newel
    xb = gd["to_v_m"] - side * nm / 2                             # the guard's own end newel
    lo, hi = sorted((xa + side * nm / 2, xb - side * nm / 2))
    top, foot = y0 + H, y0 + 0.06
    _box(a, "iron", frame, xb - nm / 2, xb + nm / 2, y0, top + 0.1, d - nm / 2, d + nm / 2, seed, conf, skip=("bottom",))
    _box(a, "iron", frame, lo, hi, top - rm, top, d - rw / 2, d + rw / 2, seed, conf)
    _box(a, "iron", frame, lo, hi, foot, foot + b, d - b / 2, d + b / 2, seed, conf)
    if gd.get("scrolled"):
        # T-3184: a guard pierced along its whole length (1834's photograph), the stoop's own
        # scrolled panel laid flat: two rows of scrolls on a middle bar, no balusters
        ym = (foot + b + top - rm) / 2
        _box(a, "iron", frame, lo, hi, ym - b / 2, ym + b / 2, d - b / 2, d + b / 2, seed, conf)
        count = max(2, round((hi - lo) / max(0.12, ym - foot - b)))
        for y_a, y_b in ((foot + b, ym - b / 2), (ym + b / 2, top - rm)):
            _scrolls(a, frame, {"count": count}, lo, hi, y_a, y_b, d - b / 2, d + b / 2, seed, conf)
        return
    pa, pb = sorted(gd["panel_v_m"])
    pitch = g / R["per_tread"]
    n = max(1, round((hi - lo) / pitch))
    for i in range(1, n):
        x = lo + (hi - lo) * i / n
        if pa - pitch / 2 < x < pb + pitch / 2:
            continue
        _box(a, "iron", frame, x - bm / 2, x + bm / 2, foot + b, top - rm, d - bm / 2, d + bm / 2, seed, conf)
    for x in (pa, pb):      # the panel's posts
        _box(a, "iron", frame, x - b, x + b, foot + b, top - rm, d - b, d + b, seed, conf)
    y_lo, y_hi = foot + b, top - rm
    cx, cy = (pa + pb) / 2, (y_lo + y_hi) / 2
    hx, hy = (pb - pa) / 2 - b, (y_hi - y_lo) / 2
    lz = [(cx, y_lo), (cx + hx, cy), (cx, y_hi), (cx - hx, cy)]
    for p0, p1 in zip(lz, lz[1:] + lz[:1]):
        _rod(a, frame, p0, p1, b, d - b / 2, d + b / 2, seed, conf)
    rr = min(hx, hy) * 0.45
    ring = [(cx + rr * math.cos(2 * math.pi * j / 16), cy + rr * math.sin(2 * math.pi * j / 16)) for j in range(17)]
    for p0, p1 in zip(ring, ring[1:]):
        _rod(a, frame, p0, p1, b, d - b / 2, d + b / 2, seed, conf)


def _carved_band(a, frame, af, length, conf):
    """T-2819: the carving on a carved band (1623's drawing: a band of carving across the front
    at the arches' springing, on the piers between and beside them). The band is a belt course
    `k01_frontage.stone_front` lays, its face BELT_PROUD_M before the wall; on every run of it
    between the lights it crosses, the oriel's guilloche (k08_bays._guilloche): rings of
    `ring_width_m` along the run's middle at `pitch` of their radius, every other one standing
    `ring_proud_m` and the rest half that, so where two cross one passes over the other; each
    ring is sunk 0.01 m into the band's face, so none stands off it."""
    cb = af["carved_band"]
    b0, b1, g = cb["bed_m"], cb["top_m"], cb["guilloche"]
    seed = a.instance("k01.wall.carved_band", "wall", {"bed_m": b0, "top_m": b1},
                      {"bed": _P(frame, 0.0, b0, 0.0), "top": _P(frame, 0.0, b1, 0.0)})
    cuts = sorted((q[0], q[1]) for gr in af["groups"] for q in gr["lights"] if q[4] < b1 and q[2] > b0)
    runs, x = [], 0.0
    for c0, c1 in cuts:
        if c0 > x:
            runs.append((x, c0))
        x = max(x, c1)
    if x < length:
        runs.append((x, length))
    for s0, s1 in runs:
        n = _guilloche_run(a, frame, s0, s1, b0, b1, g, seed, conf)
        if n:
            a.components["k01.wall.carved_band"]["instances"][-1]["params"].setdefault("rings", 0)
            a.components["k01.wall.carved_band"]["instances"][-1]["params"]["rings"] += n


def _guilloche_run(a, frame, s0, s1, b0, b1, g, seed, conf):
    """T-2819's guilloche on one run [s0, s1] of a belt [b0, b1]; returns its rings (0 where
    a sliver of pier holds none)."""
    w, rp, k, mg = g["ring_width_m"], g["ring_proud_m"], int(g["segments"]), g["margin_m"]
    d0 = BELT_PROUD_M - 0.01
    yc = (b0 + b1) / 2
    R = min(g["radius_m"], (b1 - b0) / 2 - mg, (s1 - s0) / 2 - mg)
    if R < 2 * w:
        return 0
    pitch = g["pitch"] * R
    n = max(1, math.floor((s1 - s0 - 2 * R - 2 * mg) / pitch + 1e-9) + 1)
    sc = (s0 + s1) / 2 - (n - 1) * pitch / 2
    for j in range(n):
        d1 = BELT_PROUD_M + (rp if j % 2 == 0 else rp / 2)
        cs = sc + j * pitch
        ring = lambda r, t: (cs + r * math.cos(2 * math.pi * t / k), yc + r * math.sin(2 * math.pi * t / k))
        for t in range(k):
            o0, o1, i0, i1 = ring(R, t), ring(R, t + 1), ring(R - w, t), ring(R - w, t + 1)
            mo = ((o0[0] + o1[0]) / 2 - cs, (o0[1] + o1[1]) / 2 - yc, 0.0)
            _face(a, "limestone_trim", frame, [(*o0, d1), (*o1, d1), (*i1, d1), (*i0, d1)], (0, 0, 1), seed, conf)
            _face(a, "limestone_trim", frame, [(*o0, d0), (*o1, d0), (*o1, d1), (*o0, d1)], mo, seed, conf)
            _face(a, "limestone_trim", frame, [(*i1, d0), (*i0, d0), (*i0, d1), (*i1, d1)],
                  (-mo[0], -mo[1], 0.0), seed, conf)
    return n


def _interlace_run(a, frame, s0, s1, b0, b1, il, seed, conf):
    """T-3093: an interlace on one run [s0, s1] of a belt [b0, b1], two straps crossing as a
    plait (1812's frieze, read at 3x on Levy's print: crossing straps where T-2819's rings had
    stood for them). Each strap's centre line is a sine about the belt's middle, the second
    the first's mirror, so they cross every half `wavelength_m`; each stands up to `proud_m`
    before the belt and dips to a fifth of that at alternate crossings, the other strap over
    it there, as a plait's straps pass over and under. The print's leaves between the straps
    are not modelled. Returns the crossings."""
    st, rp, mg = il["strap_m"], il["proud_m"], il["margin_m"]
    wl, k = il["wavelength_m"], int(il["segments"])
    d0 = BELT_PROUD_M - 0.005
    yc = (b0 + b1) / 2
    amp = (b1 - b0) / 2 - mg - st / 2
    halves = max(1, round((s1 - s0) / (wl / 2)))
    lam = 2 * (s1 - s0) / halves              # whole half waves on the run, so both ends cross
    n = halves * k
    for i in (0, 1):
        sign = 1.0 if i == 0 else -1.0
        ph = lambda s: 2 * math.pi * (s - s0) / lam
        c = [(s0 + (s1 - s0) * j / n) for j in range(n + 1)]
        mid = [(s, yc + sign * amp * math.sin(ph(s))) for s in c]
        dep = [BELT_PROUD_M + rp * (0.6 + 0.4 * sign * math.cos(ph(s))) for s in c]
        edges = []
        for j, (s, y) in enumerate(mid):
            sa, ya = mid[max(j - 1, 0)]
            sb, yb = mid[min(j + 1, n)]
            ts, ty = sb - sa, yb - ya
            ln = math.hypot(ts, ty)
            ns, ny = -ty / ln * st / 2, ts / ln * st / 2
            edges.append(((s + ns, y + ny), (s - ns, y - ny)))
        for j in range(n):
            (u0, l0), (u1, l1) = edges[j], edges[j + 1]
            e0, e1 = dep[j], dep[j + 1]
            _face(a, "limestone_trim", frame, [(*l0, e0), (*l1, e1), (*u1, e1)], (0, 0, 1), seed, conf)
            _face(a, "limestone_trim", frame, [(*l0, e0), (*u1, e1), (*u0, e0)], (0, 0, 1), seed, conf)
            for (p0, p1), hint in (((u0, u1), (u0[0] - mid[j][0], u0[1] - mid[j][1], 0.0)),
                                   ((l0, l1), (l0[0] - mid[j][0], l0[1] - mid[j][1], 0.0))):
                _face(a, "limestone_trim", frame, [(*p0, d0), (*p1, d0), (*p1, e1)], hint, seed, conf)
                _face(a, "limestone_trim", frame, [(*p0, d0), (*p1, e1), (*p0, e0)], hint, seed, conf)
    return halves + 1


def _panel_run(a, frame, s0, s1, b0, b1, pa, seed, conf):
    """T-2915: a band of sunk panels on one run of a belt: raised ribs on the belt's face, one
    along its bed, one along its top and one between each two rows, and in each row upright
    ribs `length_m` apart, every other row's set off half a panel so the joints break as a
    bond's. Each rib stands `proud_m` before the belt and is sunk 0.005 m into it. Returns
    the panels."""
    rows, ln, rib, pr = pa["rows"], pa["length_m"], pa["rib_m"], pa["proud_m"]
    d0, d1 = BELT_PROUD_M - 0.005, BELT_PROUD_M + pr
    h = (b1 - b0 - rib) / rows

    def box(x0, x1, y0, y1):
        for (p0, p1, p2, p3), nrm in (
                (((x0, y0, d1), (x1, y0, d1), (x1, y1, d1), (x0, y1, d1)), (0, 0, 1)),
                (((x0, y1, d0), (x1, y1, d0), (x1, y1, d1), (x0, y1, d1)), (0, 1, 0)),
                (((x0, y0, d0), (x0, y0, d1), (x1, y0, d1), (x1, y0, d0)), (0, -1, 0)),
                (((x0, y0, d0), (x0, y1, d0), (x0, y1, d1), (x0, y0, d1)), (-1, 0, 0)),
                (((x1, y0, d0), (x1, y0, d1), (x1, y1, d1), (x1, y1, d0)), (1, 0, 0))):
            _face(a, "limestone_trim", frame, [p0, p1, p2, p3], nrm, seed, conf)

    count = 0
    for r in range(rows + 1):          # the long ribs
        y = b0 + r * h
        box(s0, s1, y, y + rib)
    for r in range(rows):              # the upright ribs, each row's set off half a panel
        ya, yb = b0 + r * h + rib, b0 + (r + 1) * h
        n = max(1, round((s1 - s0 - rib) / ln))
        step = (s1 - s0 - rib) / n
        xs = [s0 + step * (i + (0.5 if r % 2 else 0.0)) for i in range(n + 1)]
        xs = ([s0] if r % 2 else []) + [x for x in xs if x <= s1 - rib + 1e-9] + ([s1 - rib] if r % 2 else [])
        for x in xs:
            box(x, x + rib, ya, yb)
        count += len(xs) - 1
    return count


def street_carved_bands(a, frame, bands, conf):
    """T-2915: the carved belts of a named-window front (1812's photograph: the carved
    interlace over the second storey's north window, the band of sunk panels over it), each a
    belt course `k01_frontage.stone_front` lays, its face BELT_PROUD_M before the wall, carved
    from `s_m` [from, to] along the front with T-2819's guilloche or with sunk panels."""
    for cb in bands:
        b0, b1 = cb["bed_m"], cb["top_m"]
        s0, s1 = cb["s_m"]
        kind = next(k for k in ("guilloche", "interlace", "panels") if k in cb)
        seed = a.instance("k01.wall.carved_band", "wall",
                          {"bed_m": b0, "top_m": b1, "from_s_m": s0, "to_s_m": s1, "carving": kind},
                          {"bed": _P(frame, s0, b0, 0.0), "top": _P(frame, s1, b1, 0.0)})
        if kind == "guilloche":
            n = _guilloche_run(a, frame, s0, s1, b0, b1, cb["guilloche"], seed, conf)
            a.components["k01.wall.carved_band"]["instances"][-1]["params"]["rings"] = n
        elif kind == "interlace":
            n = _interlace_run(a, frame, s0, s1, b0, b1, cb["interlace"], seed, conf)
            a.components["k01.wall.carved_band"]["instances"][-1]["params"]["crossings"] = n
        else:
            n = _panel_run(a, frame, s0, s1, b0, b1, cb["panels"], seed, conf)
            a.components["k01.wall.carved_band"]["instances"][-1]["params"]["panels"] = n


def side_arch(a, frame, g):
    """T-2910: the loggia's side arch on its end wall, laid as a door's arched group is: the
    voussoir block's stones radiating from the arch's centre, and its keystone."""
    k = a.p.stone
    conf = a.p.worst_conf("footprint", "stories", "storey_heights_m", "construction", "stone_front",
                          "entrance_kit")
    _voussoirs(a, frame, g, conf, k["wall"]["recess_m"])


def street_iron(a, frame, si, conf):
    """T-3184: a brick front's iron (k01_frontage_params._street_iron), read off 1834's
    photograph: the stoop's rails as `_rails` lays them on an arched front, and each
    balconette."""
    if si.get("stoop_rails"):
        _rails(a, frame, si["stoop_rails"], conf)
    for b in si.get("balconettes", ()):
        _balconette(a, frame, b, conf)


def _balconette(a, frame, bc, conf):
    """T-3184: a balconette before a street window, as 1834's photograph shows two: a dressed
    stone slab out from the front at the floor, on scrolled consoles where it stands clear of
    the basement's top, and on it a pierced iron guard — a top rail and a foot bar, a newel at
    each front corner, returns to the wall, and between them the band of C-scrolls a grille
    is filled with (`_scrolls`), standing for the print's pierced panels."""
    s0, s1, fl, d, h, sl, n = (bc[k] for k in ("from_s_m", "to_s_m", "floor_m", "proud_m", "height_m",
                                              "slab_m", "consoles"))
    seed = a.instance("k01.opening.balconette", "opening",
                      {"length_m": s1 - s0, "height_m": h, "proud_m": d, "slab_m": sl, "consoles": n},
                      {"floor": _P(frame, (s0 + s1) / 2, fl, 0.0)})
    _box(a, "limestone_trim", frame, s0, s1, fl - sl, fl, 0.0, d, seed, conf, skip=("back",))
    # the consoles: a scrolled block under the slab, deep at its head and dying into the wall
    cw, drop = 0.16, min(0.55, 2.4 * d)
    for i in range(n):
        x = s0 + 0.12 + (s1 - s0 - 0.24) * i / max(1, n - 1)
        steps = 5
        for k in range(steps):
            t0, t1 = k / steps, (k + 1) / steps
            reach = (d - 0.04) * (1.0 - t0) ** 1.6
            _box(a, "limestone_trim", frame, x - cw / 2, x + cw / 2, fl - sl - drop * t1, fl - sl - drop * t0,
                 0.0, max(0.05, reach), seed, conf, skip=("back",))
    b = IRON_BAR_M
    g0, g1 = s0 + 0.04, s1 - 0.04
    f0 = d - 0.06                                   # the guard's face, in from the slab's edge
    y0, y1 = fl, fl + h
    _bar(a, frame, g0, g1, y1 - 0.035, y1, f0 - 0.03, f0 + 0.01, seed, conf)       # the top rail
    _bar(a, frame, g0, g1, y0 + 0.02, y0 + 0.05, f0 - b, f0, seed, conf)            # the foot bar
    _bar(a, frame, g0, g1, y0 + 0.14, y0 + 0.14 + b, f0 - b, f0, seed, conf)        # the scroll band's foot
    for x in (g0, g1 - 0.04):                                                       # the corner newels
        _bar(a, frame, x, x + 0.04, y0, y1, f0 - 0.04, f0, seed, conf)
    for x in (g0, g1 - b):                                                          # the returns
        for yy in (y1 - 0.035, y0 + 0.02):
            _bar(a, frame, x, x + b, yy, yy + 0.03, 0.0, f0 - 0.04, seed, conf)
    # the pierced panel: two rows of scrolls between the scroll band's foot and the top rail
    ym = (y0 + 0.14 + b + y1 - 0.035) / 2
    _bar(a, frame, g0, g1, ym - b / 2, ym + b / 2, f0 - b, f0, seed, conf)
    count = max(2, round((g1 - g0) / max(0.12, ym - y0 - 0.14)))
    for lo_, hi_ in ((y0 + 0.14 + b, ym - b / 2), (ym + b / 2, y1 - 0.035)):
        _scrolls(a, frame, {"count": count}, g0 + 0.04, g1 - 0.04, lo_, hi_, f0 - b, f0, seed, conf)


def lay(a, frame, yf, length, conf, recess):
    af = a.p.arched_front
    for g in af["groups"]:
        _voussoirs(a, frame, g, conf, recess)
    if af.get("carved_band"):
        _carved_band(a, frame, af, length, conf)
    if af["frieze"]:
        _frieze(a, frame, af, yf, length, conf)
    if af["frontispiece"]:
        _frontispiece(a, frame, af["frontispiece"], conf)
    if af["portico"]:
        _portico(a, frame, af["portico"], conf)
    if af.get("stoop_rails"):
        _rails(a, frame, af["stoop_rails"], conf)
    _guards(a, frame, af, conf)
