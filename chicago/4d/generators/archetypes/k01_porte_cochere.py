"""T-3160: a one-storey arcaded porte-cochere on a side wall, as 1729 Prairie's stands on 18th Street.

TICKET T-3160 (piece 4 of T-1881). The Detroit Publishing photograph of the Pullman house
(LC-D4-12551) shows, on the 18th Street flank near the Prairie corner, a one-storey block of
rusticated stone piers carrying round arches: one in its west end, seen nearly square to the
camera, and one in its south front, seen edge-on past the corner pier, under an entablature
and a balustrade at the second floor. The record names it `porte_cochere` and this module lays
it on the K01 house k01_frontage.build has finished:

  resolve()   the record checked against the house: on a side wall, inside it and clear of
              every opening on that wall under its deck, each arch inside its face with a pier
              left either side, its crown under the entablature
  dress()     three walls standing out from the side wall (the two ends and the front), each
              a pier-and-spandrel wall round its arch with the arch's soffit turned through
              it, an entablature over the whole plan (its soffit the passage's ceiling, its
              top the balcony's deck) and a balustrade round the deck's three open sides

The block's plan, the arches' places, spans and crowns, and the entablature's and the
balustrade's heights are read off the print through its solved camera; the walls' thickness,
the entablature's projection and the balustrade's section are this module's (docs/LIBERTIES.md
L-pullman-1729-porte-cochere-3160).

T-1881 (the owner, 2026-10-30: "this part of the pullman house would have been balanced not off
centered lop sided like that, and there is more detail you need on it on the corners and arches"),
two optional keys:

  back_m      the plane the block stands from, metres out from the side wall: a pavilion's
              face it stands before. Its ends begin there, so an end's arch is judged and
              centred on the face a visitor sees, not on a face running back into the pavilion.
              An end's outer pier is measured to the block's corner, the front wall's turned
              end included, keeping 0.1 m of end wall between the arch and the front wall.
  dressing    the stone dressing Taylor's photograph no. 1445 shows round the arches:
              rustication (banded courses on every pier from grade to the entablature, broken
              by the impost and stopped clear of the arch's ring, the corner piers' bands
              turned round the corner), impost (a moulded band across each pier
              at the springing) and archivolt (a ring of voussoirs proud of the face round each
              arch's head, its keystone standing higher and prouder) (docs/LIBERTIES.md
              L-pullman-1729-porte-dressing-1881).
"""

from __future__ import annotations

import math

KEYS = {"wall", "s_m", "out_m", "thickness_m", "spring_m", "head_m", "arches", "entablature", "balustrade"}
FACES = ("low_end", "front", "high_end")
ENT_KEYS = {"height_m", "proud_m"}
BAL_KEYS = {"height_m", "post_m", "baluster_m", "pitch_m", "rail_m"}
SEGMENTS = 12           # an arch's half-circle in this many straight pieces
PIER_MIN_M = 0.4        # the least pier an arch leaves at either side of its face
END_STUB_M = 0.1        # the least end wall an end's arch leaves before the front wall's inner face
DRESS_KEYS = {"rustication", "impost", "archivolt"}


class ParamError(ValueError):
    pass


def resolve(spec, *, depth, width, stone, openings) -> dict:
    """The record's `porte_cochere`, checked against the house (module doc)."""
    if not spec:
        return {}
    if not isinstance(spec, dict) or not KEYS <= set(spec) <= KEYS | {"back_m", "dressing"}:
        raise ParamError(f"porte_cochere takes {sorted(KEYS)} (and back_m, dressing)")
    if not stone:
        raise ParamError("porte_cochere is laid in the front's stone: it needs a stone_front")
    wall = spec["wall"]
    if wall not in ("k01.wall.side.north", "k01.wall.side.south"):
        raise ParamError("porte_cochere.wall: k01.wall.side.north or k01.wall.side.south")
    s0, s1 = sorted(float(x) for x in spec["s_m"])
    out, t = float(spec["out_m"]), float(spec["thickness_m"])
    ys, H = float(spec["spring_m"]), float(spec["head_m"])
    if not 0.0 <= s0 < s1 <= depth or s1 - s0 < 3.0:
        raise ParamError(f"porte_cochere.s_m [{s0}, {s1}]: at least 3 m along the side wall, inside its {depth} m")
    if not 2.0 <= out <= 8.0 or not 0.3 <= t <= 1.2 or 2 * t > s1 - s0 - 1.0 or t > out - 1.0:
        raise ParamError("porte_cochere: 2-8 m out, its walls 0.3-1.2 m thick with a passage at least 1 m inside them")
    back = float(spec.get("back_m", 0.0))
    if not 0.0 <= back <= out - t - 1.5:
        raise ParamError(f"porte_cochere.back_m {back}: 0 to {out - t - 1.5:.2f} m, leaving its ends at least "
                         f"1.5 m of face")
    dressing = _resolve_dressing(spec.get("dressing"))
    E, B = spec["entablature"], spec["balustrade"]
    if set(E) != ENT_KEYS or set(B) != BAL_KEYS or len(B["rail_m"]) != 2:
        raise ParamError("porte_cochere.entablature takes height_m and proud_m; its balustrade height_m, post_m, "
                         "baluster_m, pitch_m and rail_m [width, depth]")
    eh, ep = float(E["height_m"]), float(E["proud_m"])
    bh, bp, bb, bpi = (float(B[k]) for k in ("height_m", "post_m", "baluster_m", "pitch_m"))
    rw, rd = (float(x) for x in B["rail_m"])
    if not (0.15 <= eh <= 0.8 and 0.0 <= ep <= 0.4 and 0.4 <= bh <= 1.2 and 0.1 <= bp <= 0.5
            and 0.03 <= bb <= 0.2 and bb + 0.05 <= bpi <= 0.5 and 0.05 <= rw <= bp and 0.05 <= rd <= bh / 3):
        raise ParamError("porte_cochere: a 0.15-0.8 m entablature up to 0.4 m proud; a 0.4-1.2 m balustrade on "
                         "0.1-0.5 m posts, 0.03-0.2 m balusters at a wider pitch, its rail no wider than a post")
    lengths = {"low_end": out, "front": s1 - s0, "high_end": out}
    arches = []
    for j, ar in enumerate(spec["arches"]):
        if set(ar) != {"face", "centre_m", "span_m"} or ar["face"] not in FACES:
            raise ParamError(f"porte_cochere.arches[{j}] takes face ({', '.join(FACES)}), centre_m and span_m")
        # the front's centre is the side wall's own s; an end's is metres out from the wall
        c, w = float(ar["centre_m"]) - (s0 if ar["face"] == "front" else 0.0), float(ar["span_m"])
        L = lengths[ar["face"]]
        if ar["face"] == "front":
            ok = c - w / 2 >= t + PIER_MIN_M - 1e-6 and c + w / 2 <= L - t - PIER_MIN_M + 1e-6
        elif back > 0.0:
            # T-1881: an end standing before a pavilion is judged on the face it shows, from
            # back_m to the block's corner (the front wall's turned end is the corner pier's)
            ok = c - w / 2 >= back + PIER_MIN_M - 1e-6 and c + w / 2 <= L - PIER_MIN_M + 1e-6 \
                and c + w / 2 <= L - t - END_STUB_M + 1e-6
        else:
            ok = c - w / 2 >= PIER_MIN_M - 1e-6 and c + w / 2 <= L - t - PIER_MIN_M + 1e-6
        if not 1.0 <= w <= 5.0 or not ok:
            raise ParamError(f"porte_cochere.arches[{j}]: a 1-5 m arch on its {L:.2f} m face leaving a "
                             f"{PIER_MIN_M} m pier each side")
        if any(a["face"] == ar["face"] for a in arches):
            raise ParamError(f"porte_cochere.arches[{j}]: one arch a face")
        if ys + w / 2 > H - 0.2:
            raise ParamError(f"porte_cochere.arches[{j}]: its crown ({ys + w / 2:.2f} m) stands within 0.2 m "
                             f"of the entablature at {H} m")
        arches.append({"face": ar["face"], "centre_m": c, "span_m": w})
    if not 2.5 <= ys < H <= 9.0:
        raise ParamError("porte_cochere: the arches spring at least 2.5 m up, under the entablature (at most 9 m)")
    top = H + eh + bh
    for o in openings:   # nothing on the side wall it stands against, under its deck's rail
        if o.wall == wall and o.s_m + o.width_m / 2 > s0 - 0.1 and o.s_m - o.width_m / 2 < s1 + 0.1 \
                and o.sill_m < top + 0.1:
            raise ParamError(f"porte_cochere (s {s0}-{s1}, to {top:.2f} m) stands over the opening at s {o.s_m} "
                             f"on {wall}")
    if dressing:
        for ar in arches:
            if dressing.get("archivolt"):
                A = dressing["archivolt"]
                if ys + ar["span_m"] / 2 + A["band_m"] + A["keystone_m"] > H - 0.02:
                    raise ParamError(f"porte_cochere.dressing.archivolt: the {ar['face']} arch's keystone "
                                     f"stands into the entablature at {H} m")
            if dressing.get("impost") and dressing["impost"]["height_m"] > ys - 1.0:
                raise ParamError("porte_cochere.dressing.impost: at least 1 m of pier under it")
    return {"wall": wall, "s_m": [s0, s1], "out_m": out, "thickness_m": t, "spring_m": ys, "head_m": H,
            **({"back_m": back} if back else {}), **({"dressing": dressing} if dressing else {}),
            "arches": arches, "entablature": {"height_m": eh, "proud_m": ep},
            "balustrade": {"height_m": bh, "post_m": bp, "baluster_m": bb, "pitch_m": bpi, "rail_m": [rw, rd]}}


def _resolve_dressing(d) -> dict:
    """porte_cochere.dressing (module doc): each of its three parts optional."""
    if d is None:
        return {}
    if not isinstance(d, dict) or not d or not set(d) <= DRESS_KEYS:
        raise ParamError(f"porte_cochere.dressing takes any of {sorted(DRESS_KEYS)}")
    out = {}
    if "rustication" in d:
        r = d["rustication"]
        if set(r) != {"course_m", "channel_m", "proud_m"}:
            raise ParamError("porte_cochere.dressing.rustication takes course_m, channel_m and proud_m")
        c, ch, pr = (float(r[k]) for k in ("course_m", "channel_m", "proud_m"))
        if not (0.2 <= c <= 0.8 and 0.02 <= ch <= 0.15 and 0.02 <= pr <= 0.12):
            raise ParamError("porte_cochere.dressing.rustication: 0.2-0.8 m courses, 0.02-0.15 m channels, "
                             "0.02-0.12 m proud")
        out["rustication"] = {"course_m": c, "channel_m": ch, "proud_m": pr}
    if "impost" in d:
        r = d["impost"]
        if set(r) != {"height_m", "proud_m"}:
            raise ParamError("porte_cochere.dressing.impost takes height_m and proud_m")
        h, pr = float(r["height_m"]), float(r["proud_m"])
        if not (0.1 <= h <= 0.5 and 0.04 <= pr <= 0.2):
            raise ParamError("porte_cochere.dressing.impost: 0.1-0.5 m high, 0.04-0.2 m proud")
        out["impost"] = {"height_m": h, "proud_m": pr}
    if "archivolt" in d:
        r = d["archivolt"]
        if set(r) != {"band_m", "proud_m", "voussoirs", "keystone_m"}:
            raise ParamError("porte_cochere.dressing.archivolt takes band_m, proud_m, voussoirs and keystone_m")
        b, pr, n, k = float(r["band_m"]), float(r["proud_m"]), r["voussoirs"], float(r["keystone_m"])
        if not (0.15 <= b <= 0.6 and 0.03 <= pr <= 0.15 and isinstance(n, int) and 5 <= n <= 25 and n % 2 == 1
                and 0.0 <= k <= 0.4):
            raise ParamError("porte_cochere.dressing.archivolt: a 0.15-0.6 m ring 0.03-0.15 m proud, an odd "
                             "5-25 voussoirs (one the keystone, at the crown), the keystone 0-0.4 m higher")
        out["archivolt"] = {"band_m": b, "proud_m": pr, "voussoirs": n, "keystone_m": k}
    return out


def dress(a):
    """The arcade's walls, its entablature and its balustrade (module doc)."""
    from .k01_frontage import Y, _add, _mul
    p, pc = a.p, a.p.porte_cochere
    D, W = p.depth_m, p.width_m
    conf = p.worst_conf("footprint", "stone_front", "porte_cochere")
    if pc["wall"] == "k01.wall.side.north":
        O, R, N = (D, 0.0, -W), (-1.0, 0.0, 0.0), (0.0, 0.0, -1.0)
    else:
        O, R, N = (D, 0.0, 0.0), (-1.0, 0.0, 0.0), (0.0, 0.0, 1.0)
    P = lambda s, y, d: _add(_add(_add(O, _mul(R, s)), _mul(Y, y)), _mul(N, d))
    mat = "bay_stone"
    pr = a.prim(mat)
    (s0, s1), out, t = pc["s_m"], pc["out_m"], pc["thickness_m"]
    ys, H = pc["spring_m"], pc["head_m"]
    bk = pc.get("back_m", 0.0)   # T-1881: the plane its ends stand from (a pavilion's face)
    seed = a.instance("k01.porte_cochere", "porte_cochere",
                      {"s0_m": s0, "s1_m": s1, "out_m": out, "spring_m": ys, "head_m": H,
                       "arches": len(pc["arches"])},
                      {"deck": P((s0 + s1) / 2, H + pc["entablature"]["height_m"], out / 2)})
    bf, bh, be = a.basis(mat, O, R, Y, seed), a.basis(mat, O, R, N, seed), a.basis(mat, O, N, Y, seed)
    quad = lambda pts, n, b: pr.face(pts, n, b, conf)
    up, down = Y, _mul(Y, -1)

    # each wall in its own (a, y, w) coordinates: `a` along its face, `w` through it from the
    # outer face inwards; `at(a, y, w)` puts a point in the house, `nf` is its outer normal
    walls = {
        "front": (lambda a_, y, w: P(s0 + a_, y, out - w), N, s1 - s0, bf, be, 0.0),
        "low_end": (lambda a_, y, w: P(s0 + w, y, a_), _mul(R, -1), out - t, be, bf, bk),
        "high_end": (lambda a_, y, w: P(s1 - w, y, a_), R, out - t, be, bf, bk),
    }
    arch_of = {ar["face"]: ar for ar in pc["arches"]}
    for face, (at, nf, L, b_face, b_end, a0) in walls.items():
        ni = _mul(nf, -1)
        ar = arch_of.get(face)
        # the faces, outer then inner: piers and (over an arch) spandrel strips from its curve up
        for w, n in ((0.0, nf), (t, ni)):
            if ar:
                c, r = ar["centre_m"], ar["span_m"] / 2
                quad([at(a0, 0.0, w), at(c - r, 0.0, w), at(c - r, H, w), at(a0, H, w)], n, b_face)
                quad([at(c + r, 0.0, w), at(L, 0.0, w), at(L, H, w), at(c + r, H, w)], n, b_face)
                for k in range(SEGMENTS):
                    t0, t1 = math.pi * k / SEGMENTS, math.pi * (k + 1) / SEGMENTS
                    x0, y0 = c + r * math.cos(t0), ys + r * math.sin(t0)
                    x1, y1 = c + r * math.cos(t1), ys + r * math.sin(t1)
                    quad([at(x0, y0, w), at(x0, H, w), at(x1, H, w), at(x1, y1, w)], n, b_face)
            else:
                quad([at(a0, 0.0, w), at(L, 0.0, w), at(L, H, w), at(a0, H, w)], n, b_face)
        if ar:
            c, r = ar["centre_m"], ar["span_m"] / 2
            # the jambs, grade to springing, facing into the opening
            for x, k in ((c - r, 1.0), (c + r, -1.0)):
                dirn = _mul(_sub_(at(1.0, 0.0, 0.0), at(0.0, 0.0, 0.0)), k)
                quad([at(x, 0.0, 0.0), at(x, ys, 0.0), at(x, ys, t), at(x, 0.0, t)], dirn, b_end)
            # the arch's soffit, turned through the wall
            for k in range(SEGMENTS):
                t0, t1 = math.pi * k / SEGMENTS, math.pi * (k + 1) / SEGMENTS
                tm = (t0 + t1) / 2
                x0, y0 = c + r * math.cos(t0), ys + r * math.sin(t0)
                x1, y1 = c + r * math.cos(t1), ys + r * math.sin(t1)
                along = _sub_(at(1.0, 0.0, 0.0), at(0.0, 0.0, 0.0))
                n = _add(_mul(along, -math.cos(tm)), _mul(Y, -math.sin(tm)))
                quad([at(x0, y0, 0.0), at(x1, y1, 0.0), at(x1, y1, t), at(x0, y0, t)], n, bh)
    # the front wall's ends, past the end walls' outer faces (its corners turned)
    for s_, n in ((s0, _mul(R, -1)), (s1, R)):
        quad([P(s_, 0.0, out - t), P(s_, 0.0, out), P(s_, H, out), P(s_, H, out - t)], n, be)

    # the entablature: one slab over the whole plan, standing `proud` past the walls; its
    # underside the passage's ceiling inside the walls and the overhang's soffit outside them
    eh, ep = pc["entablature"]["height_m"], pc["entablature"]["proud_m"]
    S0, S1, Dd, y1 = s0 - ep, s1 + ep, out + ep, H + eh
    quad([P(S0, y1, bk), P(S1, y1, bk), P(S1, y1, Dd), P(S0, y1, Dd)], up, bh)
    quad([P(S0, H, Dd), P(S1, H, Dd), P(S1, y1, Dd), P(S0, y1, Dd)], N, bf)
    for s_, n in ((S0, _mul(R, -1)), (S1, R)):
        quad([P(s_, H, bk), P(s_, H, Dd), P(s_, y1, Dd), P(s_, y1, bk)], n, be)
    quad([P(s0 + t, H, bk), P(s1 - t, H, bk), P(s1 - t, H, out - t), P(s0 + t, H, out - t)], down, bh)
    if ep > 0:
        quad([P(S0, H, out), P(S1, H, out), P(S1, H, Dd), P(S0, H, Dd)], down, bh)
        quad([P(S0, H, bk), P(s0, H, bk), P(s0, H, out), P(S0, H, out)], down, bh)
        quad([P(s1, H, bk), P(S1, H, bk), P(S1, H, out), P(s1, H, out)], down, bh)

    # the balustrade round the deck's three open sides: posts at its corners and against the
    # wall, a rail over square balusters along the front and both ends
    B = pc["balustrade"]
    pm, bm, (rw, rd) = B["post_m"], B["baluster_m"], B["rail_m"]
    y2, y3 = y1, y1 + B["height_m"]
    yr = y3 - rd
    e = 0.04
    Ls, Rs, F = S0 + e, S1 - e, Dd - e

    def box(a0, a1, b0, b1, d0, d1, skip=()):
        f = {"front": ([P(a0, b0, d1), P(a1, b0, d1), P(a1, b1, d1), P(a0, b1, d1)], N, bf),
             "back": ([P(a0, b0, d0), P(a1, b0, d0), P(a1, b1, d0), P(a0, b1, d0)], _mul(N, -1), bf),
             "top": ([P(a0, b1, d0), P(a1, b1, d0), P(a1, b1, d1), P(a0, b1, d1)], up, bh),
             "bottom": ([P(a0, b0, d0), P(a1, b0, d0), P(a1, b0, d1), P(a0, b0, d1)], down, bh),
             "left": ([P(a0, b0, d0), P(a0, b0, d1), P(a0, b1, d1), P(a0, b1, d0)], _mul(R, -1), be),
             "right": ([P(a1, b0, d0), P(a1, b0, d1), P(a1, b1, d1), P(a1, b1, d0)], R, be)}
        for k, (pts, n, b) in f.items():
            if k not in skip:
                quad(pts, n, b)

    for a0, d0 in ((Ls, F - pm), (Rs - pm, F - pm), (Ls, bk), (Rs - pm, bk)):
        box(a0, a0 + pm, y2, y3, d0, d0 + pm, skip=("bottom",) + (("back",) if d0 == bk else ()))
    fr = (F - pm / 2 - rw / 2, F - pm / 2 + rw / 2)
    box(Ls + pm, Rs - pm, yr, y3 - 0.02, *fr, skip=("left", "right"))
    mid = lambda x, y_: (x + y_) / 2
    for a0 in (Ls, Rs - pm):
        ac = (mid(a0, a0 + pm) - rw / 2, mid(a0, a0 + pm) + rw / 2)
        box(*ac, yr, y3 - 0.02, bk + pm, F - pm, skip=("back", "front"))

    def balusters(lo, hi, along_s, fixed):
        n = max(1, math.floor((hi - lo) / B["pitch_m"]))
        step = (hi - lo) / (n + 1)
        for i in range(1, n + 1):
            m = lo + i * step
            if along_s:
                box(m - bm / 2, m + bm / 2, y2, yr, fixed - bm / 2, fixed + bm / 2, skip=("bottom", "top"))
            else:
                box(fixed - bm / 2, fixed + bm / 2, y2, yr, m - bm / 2, m + bm / 2, skip=("bottom", "top"))
        return n
    nb = balusters(Ls + pm, Rs - pm, True, mid(*fr))
    for a0 in (Ls, Rs - pm):
        nb += balusters(bk + pm, F - pm, False, mid(a0, a0 + pm))
    dressed = _dress_stone(pc, walls, arch_of, quad, bh) if pc.get("dressing") else {}
    a.seat((O, R, N), [(s, y, 0.0) for s in (S0, S1) for y in (0.0, y3)], "k01.porte_cochere")
    a.porte_cochere_meta = {"arches": len(pc["arches"]), "balusters": nb, "top_m": round(y3, 4), **dressed}


def _dress_stone(pc, walls, arch_of, quad, bh) -> dict:
    """T-1881: porte_cochere.dressing (module doc) on the three walls' outer faces: banded
    courses on every pier from grade to the entablature, an impost band at the springing, and a
    ring of voussoirs round each arch's head with its keystone standing higher and prouder."""
    from .k01_frontage import Y, _add, _mul
    dz = pc["dressing"]
    ys, out, t = pc["spring_m"], pc["out_m"], pc["thickness_m"]
    Ru, Im, Av = dz.get("rustication"), dz.get("impost"), dz.get("archivolt")
    counts = {"courses": 0, "voussoirs": 0}
    # the corner piers' bands turn the corner: the front's run past its ends by their
    # projection and close the corner square the ends' stop short of
    turn = max(Ru["proud_m"] if Ru else 0.0, Im["proud_m"] if Im else 0.0)
    for face, (at, nf, L, b_face, b_end, a0) in walls.items():
        along = _sub_(at(1.0, 0.0, 0.0), at(0.0, 0.0, 0.0))
        vec = lambda da, dy: _add(_mul(along, da), _mul(Y, dy))
        if face == "front":
            lo, hi, ext = 0.0, L, turn
        else:
            lo, hi, ext = a0, out, 0.0          # to the corner, the front wall's turned end included
        ar = arch_of.get(face)
        piers = [(lo - ext, ar["centre_m"] - ar["span_m"] / 2), (ar["centre_m"] + ar["span_m"] / 2, hi + ext)] \
            if ar else [(lo - ext, hi + ext)]

        def block(p0, p1, y0, y1, pr):
            o, i_ = -pr, 0.0                      # w: proud of the face (negative is outwards)
            quad([at(p0, y0, o), at(p1, y0, o), at(p1, y1, o), at(p0, y1, o)], nf, b_face)
            quad([at(p0, y1, o), at(p1, y1, o), at(p1, y1, i_), at(p0, y1, i_)], Y, bh)
            quad([at(p0, y0, o), at(p1, y0, o), at(p1, y0, i_), at(p0, y0, i_)], _mul(Y, -1), bh)
            quad([at(p0, y0, o), at(p0, y1, o), at(p0, y1, i_), at(p0, y0, i_)], _mul(along, -1), b_end)
            quad([at(p1, y0, o), at(p1, y1, o), at(p1, y1, i_), at(p1, y0, i_)], along, b_end)

        y_top = ys - (Im["height_m"] if Im else 0.0)
        H = pc["head_m"]
        # over the impost the piers' bands run on to the entablature, each course stopped
        # clear of the arch's ring at its foot (Taylor's no. 1445: the corner pier banded to
        # the entablature, the spandrel over the arch plain)
        ring = (ar["span_m"] / 2 + (Av["band_m"] + 0.02 if Av else 0.0)) if ar else 0.0
        for side, (p0, p1) in enumerate(piers):
            if p1 - p0 < 0.05:
                continue
            if Ru:
                c, ch = Ru["course_m"], Ru["channel_m"]
                for ya, yb in ((0.0, y_top), (ys, H)):
                    y0 = ya
                    while y0 < yb - 0.1:
                        q0, q1 = p0, p1
                        if ar and ya == ys:
                            dy = y0 - ys
                            reach = math.sqrt(max(ring * ring - dy * dy, 0.0))
                            if side == 0:
                                q1 = min(p1, ar["centre_m"] - reach)
                            else:
                                q0 = max(p0, ar["centre_m"] + reach)
                        if q1 - q0 >= 0.1:
                            block(q0, q1, y0, min(y0 + c, yb), Ru["proud_m"])
                            counts["courses"] += 1
                        y0 += c + ch
            if Im:
                block(p0, p1, y_top, ys, Im["proud_m"])
        if ar and Av:
            c, r, b, n = ar["centre_m"], ar["span_m"] / 2, Av["band_m"], Av["voussoirs"]
            gap = 0.012 / r                       # a mortar joint between voussoirs, in radians
            for k in range(n):
                t0, t1 = math.pi * k / n + gap, math.pi * (k + 1) / n - gap
                key = k == n // 2
                ro, pr = r + b + (Av["keystone_m"] if key else 0.0), Av["proud_m"] + (0.03 if key else 0.0)
                o = -pr
                pt = lambda rad, th, w: at(c + rad * math.cos(th), ys + rad * math.sin(th), w)
                quad([pt(r, t0, o), pt(r, t1, o), pt(ro, t1, o), pt(ro, t0, o)], nf, b_face)
                tm = (t0 + t1) / 2
                radial = vec(math.cos(tm), math.sin(tm))
                quad([pt(ro, t0, o), pt(ro, t1, o), pt(ro, t1, 0.0), pt(ro, t0, 0.0)], radial, bh)
                quad([pt(r, t0, o), pt(r, t1, o), pt(r, t1, 0.0), pt(r, t0, 0.0)], _mul(radial, -1), bh)
                quad([pt(r, t0, o), pt(ro, t0, o), pt(ro, t0, 0.0), pt(r, t0, 0.0)],
                     vec(math.sin(t0), -math.cos(t0)), b_end)
                quad([pt(r, t1, o), pt(ro, t1, o), pt(ro, t1, 0.0), pt(r, t1, 0.0)],
                     vec(-math.sin(t1), math.cos(t1)), b_end)
                counts["voussoirs"] += 1
    return counts


def _sub_(u, v):
    return (u[0] - v[0], u[1] - v[1], u[2] - v[2])


# -- T-3241: a corner porch on the street front ---------------------------------------
# 1701 Prairie's, in Chicagology's photograph and on the 1911 sheet (the stone '1' piece on
# the front's north end): a one-storey stone arcade standing out from the front at its
# corner, on the principal floor's stone podium, its openings arched, under an entablature
# and a balustrade at the second floor. The porte-cochere's walls, entablature and
# balustrade, laid on the street front, with a podium under the openings and more than one
# arch a face (`corner_porch`; docs/LIBERTIES.md L-k01-hibbard-1701-3241).

PORCH_KEYS = {"s_m", "out_m", "thickness_m", "floor_m", "spring_m", "head_m", "arches", "entablature", "balustrade"}
PORCH_PIER_M = 0.2      # the least pier a porch arch leaves at either side, a column's


def resolve_porch(spec, *, width, openings, bays) -> dict:
    """The record's `corner_porch`, checked against the house: on the street front, from
    one corner, clear of the door and of every bay, each arch inside its face with a pier
    left either side, its crown under the entablature."""
    if not spec:
        return {}
    if not isinstance(spec, dict) or not PORCH_KEYS <= set(spec) <= PORCH_KEYS | {"roundels"}:
        raise ParamError(f"corner_porch takes {sorted(PORCH_KEYS)} (and roundels)")
    s0, s1 = sorted(float(x) for x in spec["s_m"])
    out, t, fl = float(spec["out_m"]), float(spec["thickness_m"]), float(spec["floor_m"])
    ys, H = float(spec["spring_m"]), float(spec["head_m"])
    if not (s0 == 0.0 or s1 == width) or not 2.5 <= s1 - s0 <= 8.0 or s1 > width:
        raise ParamError(f"corner_porch.s_m [{s0}, {s1}]: 2.5-8 m along the front from one of its corners (0 or {width})")
    if not 0.8 <= out <= 4.0 or not 0.2 <= t <= 0.8 or t > out - 0.4:
        raise ParamError("corner_porch: 0.8-4 m out, its walls 0.2-0.8 m thick with at least 0.4 m inside them")
    if not 0.0 <= fl <= 3.0 or not fl + 1.5 <= ys < H <= 9.0:
        raise ParamError("corner_porch: a 0-3 m podium, the arches springing at least 1.5 m over it, under the entablature")
    E, B = spec["entablature"], spec["balustrade"]
    if set(E) != ENT_KEYS or set(B) != BAL_KEYS or len(B["rail_m"]) != 2:
        raise ParamError("corner_porch.entablature takes height_m and proud_m; its balustrade height_m, post_m, "
                         "baluster_m, pitch_m and rail_m [width, depth]")
    eh, ep = float(E["height_m"]), float(E["proud_m"])
    bh, bp, bb, bpi = (float(B[k]) for k in ("height_m", "post_m", "baluster_m", "pitch_m"))
    rw, rd = (float(x) for x in B["rail_m"])
    if not (0.15 <= eh <= 0.8 and 0.0 <= ep <= 0.4 and 0.4 <= bh <= 1.2 and 0.1 <= bp <= 0.5
            and 0.03 <= bb <= 0.2 and bb + 0.05 <= bpi <= 0.5 and 0.05 <= rw <= bp and 0.05 <= rd <= bh / 3):
        raise ParamError("corner_porch: a 0.15-0.8 m entablature up to 0.4 m proud; a 0.4-1.2 m balustrade on "
                         "0.1-0.5 m posts, 0.03-0.2 m balusters at a wider pitch, its rail no wider than a post")
    lengths = {"low_end": out, "front": s1 - s0, "high_end": out}
    arches = []
    for j, ar in enumerate(spec["arches"]):
        if set(ar) != {"face", "centre_m", "span_m"} or ar["face"] not in FACES:
            raise ParamError(f"corner_porch.arches[{j}] takes face ({', '.join(FACES)}), centre_m and span_m")
        c, w = float(ar["centre_m"]) - (s0 if ar["face"] == "front" else 0.0), float(ar["span_m"])
        L = lengths[ar["face"]]
        lo = t if ar["face"] == "front" else 0.0
        hi = L - t
        if not 0.4 <= w <= 4.0 or c - w / 2 < lo + PORCH_PIER_M - 1e-6 or c + w / 2 > hi - PORCH_PIER_M + 1e-6:
            raise ParamError(f"corner_porch.arches[{j}]: a 0.4-4 m arch on its {L:.2f} m face leaving a "
                             f"{PORCH_PIER_M} m pier each side")
        if ys + w / 2 > H - 0.15:
            raise ParamError(f"corner_porch.arches[{j}]: its crown ({ys + w / 2:.2f} m) stands within 0.15 m "
                             f"of the entablature at {H} m")
        for a in arches:
            if a["face"] == ar["face"] and abs(a["centre_m"] - c) < (a["span_m"] + w) / 2 + PORCH_PIER_M - 1e-6:
                raise ParamError(f"corner_porch.arches[{j}]: it leaves no {PORCH_PIER_M} m pier beside the arch at "
                                 f"{a['centre_m']:.2f} m on its face")
        arches.append({"face": ar["face"], "centre_m": c, "span_m": w})
    arches.sort(key=lambda a: (FACES.index(a["face"]), a["centre_m"]))
    for o in openings:   # the door is never behind it; the lights it stands before show through its arches
        if o.wall == "k01.wall.street_front" and o.component == "k01.opening.door_leaf" \
                and o.s_m + o.width_m / 2 > s0 - ep - 0.1 and o.s_m - o.width_m / 2 < s1 + ep + 0.1:
            raise ParamError(f"corner_porch (s {s0}-{s1}) stands before the door at s {o.s_m}")
    for b in bays:
        if b["wall"] == "k01.wall.street_front":
            b0, b1 = b["span_m"]
            if b1 > s0 - ep - 0.05 and b0 < s1 + ep + 0.05:
                raise ParamError(f"corner_porch (s {s0}-{s1}) runs into the bay {b['id']} (s {b0:.2f}-{b1:.2f})")
    # T-3257: carved roundels on the podium's front face (1701's, the photograph's dark
    # discs in stone rings under the arcade, over the fence), each a ring proud of the face
    # round a dark sunk disc, under the floor and clear of the face's ends
    rs = spec.get("roundels")
    roundels = None
    if rs is not None:
        if set(rs) != {"y_m", "d_m", "centre_m"} or not rs["centre_m"]:
            raise ParamError("corner_porch.roundels takes y_m, d_m and centre_m (along the front)")
        ry, rdm = float(rs["y_m"]), float(rs["d_m"])
        if not 0.2 <= rdm <= 0.9 or ry - rdm / 2 < 0.15 or ry + rdm / 2 > fl - 0.1:
            raise ParamError(f"corner_porch.roundels: 0.2-0.9 m across, at least 0.15 m off the ground and "
                             f"0.1 m under the porch's floor at {fl} m")
        cs = [float(c) - s0 for c in rs["centre_m"]]
        if any(c - rdm / 2 < 0.1 or c + rdm / 2 > s1 - s0 - 0.1 for c in cs):
            raise ParamError("corner_porch.roundels stand inside the porch's front face, 0.1 m clear of its ends")
        roundels = {"y_m": ry, "d_m": rdm, "centre_m": cs}
    return {"wall": "k01.wall.street_front", "s_m": [s0, s1], "out_m": out, "thickness_m": t, "floor_m": fl,
            **({"roundels": roundels} if roundels else {}),
            "spring_m": ys, "head_m": H, "arches": arches, "entablature": {"height_m": eh, "proud_m": ep},
            "balustrade": {"height_m": bh, "post_m": bp, "baluster_m": bb, "pitch_m": bpi, "rail_m": [rw, rd]}}


def dress_porch(a):
    """The corner porch's walls on their podium, its floor, entablature and balustrade."""
    from .k01_frontage import Y, _add, _mul
    p, pc = a.p, a.p.corner_porch
    D = p.depth_m
    conf = p.worst_conf("footprint", "corner_porch")
    O, R, N = (D, 0.0, 0.0), (0.0, 0.0, -1.0), (1.0, 0.0, 0.0)
    P = lambda s, y, d: _add(_add(_add(O, _mul(R, s)), _mul(Y, y)), _mul(N, d))
    mat = "bay_stone"
    pr = a.prim(mat)
    (s0, s1), out, t = pc["s_m"], pc["out_m"], pc["thickness_m"]
    fl, ys, H = pc["floor_m"], pc["spring_m"], pc["head_m"]
    seed = a.instance("k01.corner_porch", "corner_porch",
                      {"s0_m": s0, "s1_m": s1, "out_m": out, "floor_m": fl, "spring_m": ys, "head_m": H,
                       "arches": len(pc["arches"])},
                      {"deck": P((s0 + s1) / 2, H + pc["entablature"]["height_m"], out / 2)})
    bf, bh, be = a.basis(mat, O, R, Y, seed), a.basis(mat, O, R, N, seed), a.basis(mat, O, N, Y, seed)
    quad = lambda pts, n, b: pr.face(pts, n, b, conf)
    up, down = Y, _mul(Y, -1)
    walls = {
        "front": (lambda a_, y, w: P(s0 + a_, y, out - w), N, s1 - s0, bf, be),
        "low_end": (lambda a_, y, w: P(s0 + w, y, a_), _mul(R, -1), out - t, be, bf),
        "high_end": (lambda a_, y, w: P(s1 - w, y, a_), R, out - t, be, bf),
    }
    for face, (at, nf, L, b_face, b_end) in walls.items():
        ni = _mul(nf, -1)
        along = _sub_(at(1.0, 0.0, 0.0), at(0.0, 0.0, 0.0))
        ars = [ar for ar in pc["arches"] if ar["face"] == face]
        for w, n in ((0.0, nf), (t, ni)):
            x = 0.0
            for ar in ars:
                c, r = ar["centre_m"], ar["span_m"] / 2
                quad([at(x, 0.0, w), at(c - r, 0.0, w), at(c - r, H, w), at(x, H, w)], n, b_face)
                if fl > 0.0:   # the podium under the opening
                    quad([at(c - r, 0.0, w), at(c + r, 0.0, w), at(c + r, fl, w), at(c - r, fl, w)], n, b_face)
                for k in range(SEGMENTS):
                    t0, t1 = math.pi * k / SEGMENTS, math.pi * (k + 1) / SEGMENTS
                    x0, y0 = c + r * math.cos(t0), ys + r * math.sin(t0)
                    x1, y1 = c + r * math.cos(t1), ys + r * math.sin(t1)
                    quad([at(x0, y0, w), at(x0, H, w), at(x1, H, w), at(x1, y1, w)], n, b_face)
                x = c + r
            quad([at(x, 0.0, w), at(L, 0.0, w), at(L, H, w), at(x, H, w)], n, b_face)
        for ar in ars:
            c, r = ar["centre_m"], ar["span_m"] / 2
            for x, k in ((c - r, 1.0), (c + r, -1.0)):   # the jambs, podium to springing
                quad([at(x, fl, 0.0), at(x, ys, 0.0), at(x, ys, t), at(x, fl, t)], _mul(along, k), b_end)
            if fl > 0.0:   # the opening's sill on the podium
                quad([at(c - r, fl, 0.0), at(c + r, fl, 0.0), at(c + r, fl, t), at(c - r, fl, t)], up, bh)
            for k in range(SEGMENTS):   # the arch's soffit, turned through the wall
                t0, t1 = math.pi * k / SEGMENTS, math.pi * (k + 1) / SEGMENTS
                tm = (t0 + t1) / 2
                x0, y0 = c + r * math.cos(t0), ys + r * math.sin(t0)
                x1, y1 = c + r * math.cos(t1), ys + r * math.sin(t1)
                n = _add(_mul(along, -math.cos(tm)), _mul(Y, -math.sin(tm)))
                quad([at(x0, y0, 0.0), at(x1, y1, 0.0), at(x1, y1, t), at(x0, y0, t)], n, bh)
    rnd = pc.get("roundels")
    if rnd:   # T-3257: the podium's roundels (resolve_porch)
        ring_out, sunk, k_n = 0.05, 0.02, 24
        ro, ri = rnd["d_m"] / 2, rnd["d_m"] / 2 * 0.72
        dark = a.prim("iron")
        bi = a.basis("iron", O, R, Y, seed)
        for c in rnd["centre_m"]:
            cc = s0 + c
            ang = [2 * math.pi * k / k_n for k in range(k_n + 1)]
            for k in range(k_n):
                a0, a1 = ang[k], ang[k + 1]
                q = lambda rr, an, d: P(cc + rr * math.cos(an), rnd["y_m"] + rr * math.sin(an), out + d)
                quad([q(ri, a0, ring_out), q(ri, a1, ring_out), q(ro, a1, ring_out), q(ro, a0, ring_out)], N, bf)
                am = (a0 + a1) / 2
                no = _add(_mul(R, math.cos(am)), _mul(Y, math.sin(am)))
                quad([q(ro, a0, 0.0), q(ro, a0, ring_out), q(ro, a1, ring_out), q(ro, a1, 0.0)], no, bf)
                quad([q(ri, a1, sunk), q(ri, a1, ring_out), q(ri, a0, ring_out), q(ri, a0, sunk)], _mul(no, -1), bf)
                dark.face([q(0.0, a0, sunk), q(ri, a0, sunk), q(ri, a1, sunk)], N, bi, conf)
    for s_, n in ((s0, _mul(R, -1)), (s1, R)):   # the front wall's ends, its corners turned
        quad([P(s_, 0.0, out - t), P(s_, 0.0, out), P(s_, H, out), P(s_, H, out - t)], n, be)
    # the porch's floor on the podium, inside its walls
    quad([P(s0 + t, fl, 0.0), P(s1 - t, fl, 0.0), P(s1 - t, fl, out - t), P(s0 + t, fl, out - t)], up, bh)

    eh, ep = pc["entablature"]["height_m"], pc["entablature"]["proud_m"]
    S0, S1, Dd, y1 = s0 - ep, s1 + ep, out + ep, H + eh
    if s0 == 0.0:   # flush with the side wall at the corner, as the sheet draws it
        S0 = s0
    if s1 == p.width_m:
        S1 = s1
    quad([P(S0, y1, 0.0), P(S1, y1, 0.0), P(S1, y1, Dd), P(S0, y1, Dd)], up, bh)
    quad([P(S0, H, Dd), P(S1, H, Dd), P(S1, y1, Dd), P(S0, y1, Dd)], N, bf)
    for s_, n in ((S0, _mul(R, -1)), (S1, R)):
        quad([P(s_, H, 0.0), P(s_, H, Dd), P(s_, y1, Dd), P(s_, y1, 0.0)], n, be)
    quad([P(s0 + t, H, 0.0), P(s1 - t, H, 0.0), P(s1 - t, H, out - t), P(s0 + t, H, out - t)], down, bh)
    if ep > 0:
        quad([P(S0, H, out), P(S1, H, out), P(S1, H, Dd), P(S0, H, Dd)], down, bh)
        if S0 < s0:
            quad([P(S0, H, 0.0), P(s0, H, 0.0), P(s0, H, out), P(S0, H, out)], down, bh)
        if S1 > s1:
            quad([P(s1, H, 0.0), P(S1, H, 0.0), P(S1, H, out), P(s1, H, out)], down, bh)

    B = pc["balustrade"]
    pm, bm, (rw, rd) = B["post_m"], B["baluster_m"], B["rail_m"]
    y2, y3 = y1, y1 + B["height_m"]
    yr = y3 - rd
    e = 0.04
    Ls, Rs, F = S0 + e, S1 - e, Dd - e

    def box(a0, a1, b0, b1, d0, d1, skip=()):
        f = {"front": ([P(a0, b0, d1), P(a1, b0, d1), P(a1, b1, d1), P(a0, b1, d1)], N, bf),
             "back": ([P(a0, b0, d0), P(a1, b0, d0), P(a1, b1, d0), P(a0, b1, d0)], _mul(N, -1), bf),
             "top": ([P(a0, b1, d0), P(a1, b1, d0), P(a1, b1, d1), P(a0, b1, d1)], up, bh),
             "bottom": ([P(a0, b0, d0), P(a1, b0, d0), P(a1, b0, d1), P(a0, b0, d1)], down, bh),
             "left": ([P(a0, b0, d0), P(a0, b0, d1), P(a0, b1, d1), P(a0, b1, d0)], _mul(R, -1), be),
             "right": ([P(a1, b0, d0), P(a1, b0, d1), P(a1, b1, d1), P(a1, b1, d0)], R, be)}
        for k, (pts, n, b) in f.items():
            if k not in skip:
                quad(pts, n, b)

    for a0, d0 in ((Ls, F - pm), (Rs - pm, F - pm), (Ls, 0.0), (Rs - pm, 0.0)):
        box(a0, a0 + pm, y2, y3, d0, d0 + pm, skip=("bottom",) + (("back",) if d0 == 0.0 else ()))
    fr = (F - pm / 2 - rw / 2, F - pm / 2 + rw / 2)
    box(Ls + pm, Rs - pm, yr, y3 - 0.02, *fr, skip=("left", "right"))
    mid = lambda x, y_: (x + y_) / 2
    for a0 in (Ls, Rs - pm):
        ac = (mid(a0, a0 + pm) - rw / 2, mid(a0, a0 + pm) + rw / 2)
        box(*ac, yr, y3 - 0.02, pm, F - pm, skip=("back", "front"))

    def balusters(lo, hi, along_s, fixed):
        n = max(1, math.floor((hi - lo) / B["pitch_m"]))
        step = (hi - lo) / (n + 1)
        for i in range(1, n + 1):
            m = lo + i * step
            if along_s:
                box(m - bm / 2, m + bm / 2, y2, yr, fixed - bm / 2, fixed + bm / 2, skip=("bottom", "top"))
            else:
                box(fixed - bm / 2, fixed + bm / 2, y2, yr, m - bm / 2, m + bm / 2, skip=("bottom", "top"))
        return n
    nb = balusters(Ls + pm, Rs - pm, True, mid(*fr))
    for a0 in (Ls, Rs - pm):
        nb += balusters(pm, F - pm, False, mid(a0, a0 + pm))
    a.seat((O, R, N), [(s, y, 0.0) for s in (S0, S1) for y in (0.0, y3)], "k01.corner_porch")
    a.corner_porch_meta = {"arches": len(pc["arches"]), "balusters": nb, "top_m": round(y3, 4)}


# -- T-3239: a columned porch on a side wall ------------------------------------------
# 1906 Prairie's, in Chicagology's wood engraving of the Edson Keith house: on the south flank,
# in the angle the south wing makes with the main wall, a porch on round columns over the
# terrace's podium, under an entablature whose top is a balcony railed by a balustrade before
# the wing's arched light. The porte-cochere's entablature and balustrade, stood on columns
# instead of arcaded walls and on a podium, with the end that meets the wing left closed
# (`side_porch`; docs/LIBERTIES.md L-k01-1906-keith-3238).

SIDE_KEYS = {"wall", "s_m", "out_m", "floor_m", "head_m", "closed_end", "columns", "entablature", "balustrade"}
COLUMN_KEYS = {"diameter_m", "front", "end", "plinth_m", "capital_m"}
SHAFT_SIDES = 12        # a column's round shaft in this many flat faces


def resolve_side_porch(spec, *, depth, openings) -> dict:
    """The record's `side_porch`, checked against the house: on a side wall, inside it, every
    column inside the porch's plan, its podium under its head, and no light on that wall cut
    through its entablature."""
    if not spec:
        return {}
    if not isinstance(spec, dict) or set(spec) != SIDE_KEYS:
        raise ParamError(f"side_porch takes {sorted(SIDE_KEYS)}")
    wall = spec["wall"]
    if wall not in ("k01.wall.side.north", "k01.wall.side.south"):
        raise ParamError("side_porch.wall: k01.wall.side.north or k01.wall.side.south")
    s0, s1 = sorted(float(x) for x in spec["s_m"])
    out, fl, H = float(spec["out_m"]), float(spec["floor_m"]), float(spec["head_m"])
    if not 0.0 <= s0 < s1 <= depth or not 2.5 <= s1 - s0 <= 10.0:
        raise ParamError(f"side_porch.s_m [{s0}, {s1}]: 2.5-10 m along the side wall, inside its {depth} m")
    if not 1.0 <= out <= 4.0 or not 0.0 <= fl <= 3.0 or not fl + 2.2 <= H <= 9.0:
        raise ParamError("side_porch: 1-4 m out, on a 0-3 m podium, its head at least 2.2 m over the floor (at most 9 m)")
    if spec["closed_end"] not in ("low", "high", None):
        raise ParamError("side_porch.closed_end: low, high or null (the end that meets another wall)")
    C = spec["columns"]
    if not isinstance(C, dict) or set(C) != COLUMN_KEYS or len(C["plinth_m"]) != 2 or len(C["capital_m"]) != 2:
        raise ParamError(f"side_porch.columns takes {sorted(COLUMN_KEYS)}, plinth_m and capital_m [width, height]")
    dia = float(C["diameter_m"])
    (pw, ph), (cw, chh) = (tuple(float(x) for x in C[k]) for k in ("plinth_m", "capital_m"))
    if not (0.15 <= dia <= 0.6 and dia <= pw <= 1.0 and 0.05 <= ph <= 0.6 and dia <= cw <= 1.0
            and 0.05 <= chh <= 0.6 and ph + chh + 1.5 <= H - fl):
        raise ParamError("side_porch.columns: 0.15-0.6 m shafts on plinths and under capitals at least as wide, "
                         "with at least 1.5 m of shaft between them")
    front = sorted(float(x) for x in C["front"])
    end = sorted(float(x) for x in C["end"])
    if len(front) < 2 or any(not s0 + pw / 2 - 1e-6 <= x <= s1 - pw / 2 + 1e-6 for x in front):
        raise ParamError(f"side_porch.columns.front: at least two columns, each inside s {s0}-{s1}")
    if any(not pw / 2 <= x <= out - pw / 2 + 1e-6 for x in end) or (end and spec["closed_end"] is None):
        raise ParamError("side_porch.columns.end: columns along the open end, inside the porch's depth")
    E, B = spec["entablature"], spec["balustrade"]
    if set(E) != ENT_KEYS or set(B) != BAL_KEYS or len(B["rail_m"]) != 2:
        raise ParamError("side_porch.entablature takes height_m and proud_m; its balustrade height_m, post_m, "
                         "baluster_m, pitch_m and rail_m [width, depth]")
    eh, ep = float(E["height_m"]), float(E["proud_m"])
    bh, bp, bb, bpi = (float(B[k]) for k in ("height_m", "post_m", "baluster_m", "pitch_m"))
    rw, rd = (float(x) for x in B["rail_m"])
    if not (0.15 <= eh <= 0.8 and 0.0 <= ep <= 0.4 and 0.4 <= bh <= 1.2 and 0.1 <= bp <= 0.5
            and 0.03 <= bb <= 0.2 and bb + 0.05 <= bpi <= 0.5 and 0.05 <= rw <= bp and 0.05 <= rd <= bh / 3):
        raise ParamError("side_porch: a 0.15-0.8 m entablature up to 0.4 m proud; a 0.4-1.2 m balustrade on "
                         "0.1-0.5 m posts, 0.03-0.2 m balusters at a wider pitch, its rail no wider than a post")
    for o in openings:   # a light stands under its ceiling or over its deck (behind the open balustrade,
        # as a balcony's lights do), never through the entablature
        if o.wall == wall and o.s_m + o.width_m / 2 > s0 - ep - 0.1 and o.s_m - o.width_m / 2 < s1 + ep + 0.1 \
                and o.sill_m < H + eh + 0.05 and o.head_m > H - 0.05:
            raise ParamError(f"side_porch (s {s0}-{s1}, its entablature {H}-{H + eh:.2f} m) stands across the "
                             f"opening at s {o.s_m} on {wall}")
    return {"wall": wall, "s_m": [s0, s1], "out_m": out, "floor_m": fl, "head_m": H,
            "closed_end": spec["closed_end"],
            "columns": {"diameter_m": dia, "front": front, "end": end, "plinth_m": [pw, ph], "capital_m": [cw, chh]},
            "entablature": {"height_m": eh, "proud_m": ep},
            "balustrade": {"height_m": bh, "post_m": bp, "baluster_m": bb, "pitch_m": bpi, "rail_m": [rw, rd]}}


def dress_side_porch(a):
    """The side porch's podium, its columns, entablature and balustrade (module doc above)."""
    from .k01_frontage import Y, _add, _mul
    p, pc = a.p, a.p.side_porch
    D, W = p.depth_m, p.width_m
    conf = p.worst_conf("footprint", "side_porch")
    # in the wall's own frame (k01_frontage's walls), so `s_m` is the openings' s: the north
    # wall's runs from the front, the south wall's from the rear
    if pc["wall"] == "k01.wall.side.north":
        O, R, N = (D, 0.0, -W), (-1.0, 0.0, 0.0), (0.0, 0.0, -1.0)
    else:
        O, R, N = (0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 0.0, 1.0)
    P = lambda s, y, d: _add(_add(_add(O, _mul(R, s)), _mul(Y, y)), _mul(N, d))
    mat = "bay_stone"
    pr = a.prim(mat)
    (s0, s1), out, fl, H = pc["s_m"], pc["out_m"], pc["floor_m"], pc["head_m"]
    C, closed = pc["columns"], pc["closed_end"]
    seed = a.instance("k01.side_porch", "side_porch",
                      {"s0_m": s0, "s1_m": s1, "out_m": out, "floor_m": fl, "head_m": H,
                       "columns": len(C["front"]) + len(C["end"])},
                      {"deck": P((s0 + s1) / 2, H + pc["entablature"]["height_m"], out / 2)})
    bf, bh, be = a.basis(mat, O, R, Y, seed), a.basis(mat, O, R, N, seed), a.basis(mat, O, N, Y, seed)
    quad = lambda pts, n, b: pr.face(pts, n, b, conf)
    up, down = Y, _mul(Y, -1)

    def box(a0, a1, b0, b1, d0, d1, skip=()):
        f = {"front": ([P(a0, b0, d1), P(a1, b0, d1), P(a1, b1, d1), P(a0, b1, d1)], N, bf),
             "back": ([P(a0, b0, d0), P(a1, b0, d0), P(a1, b1, d0), P(a0, b1, d0)], _mul(N, -1), bf),
             "top": ([P(a0, b1, d0), P(a1, b1, d0), P(a1, b1, d1), P(a0, b1, d1)], up, bh),
             "bottom": ([P(a0, b0, d0), P(a1, b0, d0), P(a1, b0, d1), P(a0, b0, d1)], down, bh),
             "left": ([P(a0, b0, d0), P(a0, b0, d1), P(a0, b1, d1), P(a0, b1, d0)], _mul(R, -1), be),
             "right": ([P(a1, b0, d0), P(a1, b0, d1), P(a1, b1, d1), P(a1, b1, d0)], R, be)}
        for k, (pts, n, b) in f.items():
            if k not in skip:
                quad(pts, n, b)

    # the podium: the porch's floor over a stone block from grade, its back the wall
    if fl > 0.0:
        box(s0, s1, 0.0, fl, 0.0, out, skip=("back", "bottom"))

    # the columns: a square plinth, a round shaft and a square capital under the entablature
    dia, (pw, ph), (cw, chh) = C["diameter_m"], C["plinth_m"], C["capital_m"]
    end_s = s1 - pw / 2 if closed == "low" else s0 + pw / 2
    spots = [(x, out - pw / 2) for x in C["front"]] + [(end_s, d) for d in C["end"]]
    r = dia / 2
    for (sc, dc) in spots:
        box(sc - pw / 2, sc + pw / 2, fl, fl + ph, dc - pw / 2, dc + pw / 2, skip=("bottom",))
        box(sc - cw / 2, sc + cw / 2, H - chh, H, dc - cw / 2, dc + cw / 2, skip=("top",))
        y0, y1_ = fl + ph, H - chh
        for k in range(SHAFT_SIDES):
            t0, t1 = 2 * math.pi * k / SHAFT_SIDES, 2 * math.pi * (k + 1) / SHAFT_SIDES
            tm = (t0 + t1) / 2
            q0 = (sc + r * math.cos(t0), dc + r * math.sin(t0))
            q1 = (sc + r * math.cos(t1), dc + r * math.sin(t1))
            n = _add(_mul(R, math.cos(tm)), _mul(N, math.sin(tm)))
            quad([P(q0[0], y0, q0[1]), P(q1[0], y0, q1[1]), P(q1[0], y1_, q1[1]), P(q0[0], y1_, q0[1])], n, be)

    # the entablature: one slab over the plan, `proud` past its open sides; its top the balcony
    eh, ep = pc["entablature"]["height_m"], pc["entablature"]["proud_m"]
    S0 = s0 if closed == "low" else s0 - ep
    S1 = s1 if closed == "high" else s1 + ep
    Dd, y1 = out + ep, H + eh
    box(S0, S1, H, y1, 0.0, Dd, skip=("back",))

    # the balustrade round the balcony's open sides: posts at its corners and against the wall
    B = pc["balustrade"]
    pm, bm, (rw, rd) = B["post_m"], B["baluster_m"], B["rail_m"]
    y2, y3 = y1, y1 + B["height_m"]
    yr = y3 - rd
    e = 0.04
    Ls, Rs, F = S0 + e, S1 - e, Dd - e
    mid = lambda x, y_: (x + y_) / 2
    for a0, d0 in ((Ls, F - pm), (Rs - pm, F - pm), (Ls, 0.0), (Rs - pm, 0.0)):
        if d0 == 0.0 and ((closed == "low" and a0 == Ls) or (closed == "high" and a0 != Ls)):
            continue          # the closed end meets a wall: no post against the house there
        box(a0, a0 + pm, y2, y3, d0, d0 + pm, skip=("bottom",) + (("back",) if d0 == 0.0 else ()))
    fr = (F - pm / 2 - rw / 2, F - pm / 2 + rw / 2)
    box(Ls + pm, Rs - pm, yr, y3 - 0.02, *fr, skip=("left", "right"))

    def balusters(lo, hi, along_s, fixed):
        n = max(1, math.floor((hi - lo) / B["pitch_m"]))
        step = (hi - lo) / (n + 1)
        for i in range(1, n + 1):
            m = lo + i * step
            if along_s:
                box(m - bm / 2, m + bm / 2, y2, yr, fixed - bm / 2, fixed + bm / 2, skip=("bottom", "top"))
            else:
                box(fixed - bm / 2, fixed + bm / 2, y2, yr, m - bm / 2, m + bm / 2, skip=("bottom", "top"))
        return n
    nb = balusters(Ls + pm, Rs - pm, True, mid(*fr))
    for a0, which in ((Ls, "low"), (Rs - pm, "high")):
        if which == closed:
            continue
        ac = (mid(a0, a0 + pm) - rw / 2, mid(a0, a0 + pm) + rw / 2)
        box(*ac, yr, y3 - 0.02, pm, F - pm, skip=("back", "front"))
        nb += balusters(pm, F - pm, False, mid(a0, a0 + pm))
    a.seat((O, R, N), [(s, y, 0.0) for s in (S0, S1) for y in (0.0, y3)], "k01.side_porch")
    a.side_porch_meta = {"columns": len(spots), "balusters": nb, "top_m": round(y3, 4)}
