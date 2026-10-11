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
    if po:
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
        _face(a, "backing", frame, [(h0, ly0, -D), (h1, ly0, -D), (h1, ly1, -D), (h0, ly1, -D)], (0, 0, 1), seed, conf)
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
    """Four columns on pedestals, a beam over each side pair, an arch block over the door
    turned as a barrel from the wall to the front, and a cornice slab over all."""
    c, hw, r = po["centre_s_m"], po["half_width_m"], po["arch_radius_m"]
    F = po["front_m"]
    i0, i1 = po["impost_m"]
    top, (c0, c1) = po["top_m"], po["cornice_m"]
    cid = "k01.wall.portico"
    seed = a.instance(cid, "wall", {"columns": 2 * len(po["columns_d_m"]), "front_m": F, "arch_radius_m": r,
                                    "impost_m": [i0, i1], "top_m": c1},
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
    # the side beams: the impost, wall to front
    for s0, s1, inner in ((c - hw, c - r, "right"), (c + r, c + hw, "left")):
        _box(a, mat, frame, s0, s1, i0, i1, 0.0, F, seed, conf, skip=("back", "top"))
    # the arch block: wedges about the springing centre, extruded wall to front
    for pts, kinds, mid in wedges(c, i1, r, c - hw, c + hw, top, merge_crown=True):
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
    _guards(a, frame, af, conf)
