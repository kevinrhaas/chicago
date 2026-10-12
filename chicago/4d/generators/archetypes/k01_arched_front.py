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
    for i, (s0, s1, spring, r, sill) in enumerate(g["lights"]):
        cx = (s0 + s1) / 2
        L, Rr = g["cuts"][i], g["cuts"][i + 1]
        for pts, kinds, mid in wedges(cx, spring, r, L, Rr, g["top_m"]):
            bed = k._unit(k._add(k._mul(R, math.cos(mid)), k._mul(k.Y, math.sin(mid))))
            a.stone(frame, pts, [hj] * len(pts), "rough_stone_trim", a._stone_seed(cid, inst, j), conf,
                    recess=recess, bevel=wk["bevel_m"], F=0.0, bed=bed)
            j += 1
    # the piers between paired lights, from the sill to the spring: one stone each
    for (p0, p1) in g["piers"]:
        a.stone(frame, [(p0, g["sill_m"]), (p1, g["sill_m"]), (p1, g["spring_m"]), (p0, g["spring_m"])], [hj] * 4,
                "rough_stone_trim", a._stone_seed(cid, inst, j), conf, recess=recess, bevel=wk["bevel_m"], F=0.0)
        j += 1
    _keystone(a, frame, g["keystone"], a._stone_seed(cid, inst, j), conf)


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
            for (s0, s1, spring, r, sill) in g["lights"]:
                cx, d = (s0 + s1) / 2, -gr["set_back_m"]
                for i in range(1, gr["bars"] + 1):
                    x = s0 + (s1 - s0) * i / (gr["bars"] + 1)
                    yt = spring + math.sqrt(max(r * r - (x - cx) ** 2, 0.0)) - 0.03
                    _bar(a, frame, x - b / 2, x + b / 2, sill + 0.02, yt, d - b, d, seed, conf)
                for yy in (sill + 0.25, spring - 0.15):
                    _bar(a, frame, s0 + 0.02, s1 - 0.02, yy, yy + b, d - 2 * b, d - b, seed, conf)


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
    seed = a.instance("k11.rail.stoop_rail", "stair", {"risers": n, "rail_height_m": H, "sides": 2,
                                                       "balusters_per_tread": R["per_tread"],
                                                       "scroll_m": sr["scroll_m"]},
                      {"top": _P(frame, door.s_m, y0 + H, L), "foot": _P(frame, door.s_m, r + H, F)})
    d_top, d_foot = L - 0.12, F - g / 2
    sc = sr["scroll_m"]
    for sg in (-1, 1):
        x = door.s_m + sg * (p.stoop_width_m / 2 - R["inset_m"])
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
        # the scroll: the handrail carried past the foot newel and turned down in a half turn
        cy, cd = rail_top(d_foot) - sc / 2, d_foot
        pts = [(cy + sc / 2 * math.cos(t), cd + sc / 2 * math.sin(t))
               for t in (math.pi * j / 6 for j in range(7))]
        for p0, p1 in zip(pts, pts[1:]):
            _beam(a, "iron", frame, x, rw, p0, p1, rm * 0.8, seed, conf)


def lay(a, frame, yf, length, conf, recess):
    af = a.p.arched_front
    for g in af["groups"]:
        _voussoirs(a, frame, g, conf, recess)
    if af["frieze"]:
        _frieze(a, frame, af, yf, length, conf)
    if af["frontispiece"]:
        _frontispiece(a, frame, af["frontispiece"], conf)
    if af["portico"]:
        _portico(a, frame, af["portico"], conf)
    if af.get("stoop_rails"):
        _rails(a, frame, af["stoop_rails"], conf)
    _guards(a, frame, af, conf)
