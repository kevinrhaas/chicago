"""T-3158: a stone street front divided into pavilions, as 1729 Prairie's is in the Detroit print.

TICKET T-3158 (piece 2 of T-1881). The Detroit Publishing photograph of the Pullman house
(LC-D4-12551) shows its Prairie front cut into bays by rusticated piers: banded stone strips,
the courses long and short in turn, that rise from the base to the cornice and break the deep
frieze under it, the south-west corner turned by the same quoined pier; a row of modillions
under the cornice's corona all round; panels sunk in the frieze between the piers; and on the
mansard over two of the piers a raised rib, so the roof reads in sections over the bays. The
record names all of it as `street_front_pavilions` and this module lays it on the K01 house
k01_frontage.build has finished:

  resolve()   the record checked against the house: each pier inside the front and clear of
              every street opening (and the voussoirs round it), the corner pier at the high-s
              end, the frieze between the window heads and the modillions, the ribs on the
              street face of a mansard and clear of its dormers
  dress()     after K10's cornice: the piers (a recessed core, then the rusticated courses
              proud of it, each channel-jointed, the courses stepping in and out by the quoin
              step, and a plain block through the frieze to the cornice's bed), the frieze's
              bed course and its framed panels between the piers, the modillions along every
              stretch of the stone cornice, and the ribs up the mansard's street face

The piers' places and the frieze's and cornice's heights are read off the print through its
solved camera; the courses' rhythm, the panels' framing, the modillions' size and pitch and
the ribs' section are this module's, bounded by the print's scale (about 16 px a metre at the
front): docs/LIBERTIES.md L-pullman-1729-pavilions-3158 says which numbers are read and which
are reconstructed.
"""

from __future__ import annotations

import math

KEYS = {"piers", "proud_m", "from_m", "course_m", "channel_m", "quoin_step_m", "frieze", "modillions",
        "mansard_ribs", "belt"}
FRIEZE_KEYS = {"from_s_m", "bed_m", "bed_proud_m", "panel_m", "panel_max_m", "panel_inset_m", "frame_m",
               "frame_proud_m"}
MODILLION_KEYS = {"pitch_m", "width_m", "out_m", "drop_m", "end_clear_m"}
RIB_KEYS = {"s_m", "width_m", "proud_m"}
BELT_KEYS = {"bed_m", "profile", "runs"}
BELT_WALLS = ("k01.wall.street_front", "k01.wall.side.north", "k01.wall.rear_service", "k01.wall.side.south")
# T-1881: a pier stands on the street front (the default) or on the side.north flank, whose
# high-s corner turns onto the rear wall (1729's 18th Street flank, Taylor's photograph no. 1445)
PIER_WALLS = ("k01.wall.street_front", "k01.wall.side.north")
CORE_BACK_M = 0.08      # the pier's core stands this far behind its courses' faces: the channels' floor
RING_M = 0.25           # a pier stands this far clear of a street opening's jamb (its voussoir ring)
RIB_BURY_M = 0.02       # a rib's back is let this far into the slate it stands on
RIB_CURB_CLEAR_M = 0.05  # a rib stops this far under the curb, below the cresting's base bar


class ParamError(ValueError):
    pass


def resolve(spec, *, width, stone, openings, mansard, eave, wall_head, depth=None, bays=()) -> dict:
    """The record's `street_front_pavilions`, checked against the house (module doc)."""
    if not spec:
        return {}
    if not isinstance(spec, dict) or not {"piers", "proud_m", "from_m", "course_m", "channel_m"} <= set(spec) <= KEYS:
        raise ParamError(f"street_front_pavilions takes {sorted(KEYS)}")
    if not stone:
        raise ParamError("street_front_pavilions are laid in the front's stone: they need a stone_front")
    d, y0, ch, gap = (float(spec[k]) for k in ("proud_m", "from_m", "course_m", "channel_m"))
    step = float(spec.get("quoin_step_m", 0.0))
    if not (0.05 <= d <= 0.25 and 0.3 <= ch <= 0.8 and 0.02 <= gap <= 0.12 and 0.0 <= step <= 0.2):
        raise ParamError("street_front_pavilions: piers 0.05-0.25 m proud, in courses of 0.3-0.8 m with 0.02-0.12 m "
                         "channels, stepping 0-0.2 m in and out")
    if y0 < float(stone.get("coping_top_m", 0.0)) - 1e-6:
        raise ParamError("street_front_pavilions.from_m: the piers stand on the base's coping, not below it")
    piers, last = [], {w: -1.0 for w in PIER_WALLS}
    for j, pr in enumerate(spec["piers"]):
        if not set(pr) <= {"s_m", "corner", "return_m", "wall"}:
            raise ParamError(f"street_front_pavilions.piers[{j}] takes s_m, corner, return_m and wall")
        wall = pr.get("wall", PIER_WALLS[0])
        if wall not in PIER_WALLS or (wall != PIER_WALLS[0] and depth is None):
            raise ParamError(f"street_front_pavilions.piers[{j}].wall is one of {PIER_WALLS}")
        L = width if wall == PIER_WALLS[0] else float(depth)
        s0, s1 = (float(x) for x in pr["s_m"])
        corner = bool(pr.get("corner"))
        if not (s0 > last[wall] and 0.6 <= s1 - s0 <= 1.6 and s1 <= L + 1e-6):
            raise ParamError(f"street_front_pavilions.piers[{j}]: 0.6-1.6 m wide, in order along its wall, "
                             f"inside it (0-{L} m)")
        if corner != (abs(s1 - L) < 1e-6):
            raise ParamError(f"street_front_pavilions.piers[{j}]: the corner pier, and only it, ends at its "
                             f"wall's high-s corner ({L} m)")
        ret = float(pr.get("return_m", 0.0))
        # the front's corner pier returns onto the flank; a flank's may stop at its corner (return_m
        # 0), where the rear is built against
        if corner and not (0.5 <= ret <= 1.6 or (wall != PIER_WALLS[0] and ret == 0.0)):
            raise ParamError(f"street_front_pavilions.piers[{j}]: the corner pier returns 0.5-1.6 m round its "
                             f"corner (a flank's may return 0)")
        for o in openings:
            if o.wall == wall and o.s_m + o.width_m / 2 + RING_M > s0 and o.s_m - o.width_m / 2 - RING_M < s1:
                raise ParamError(f"street_front_pavilions.piers[{j}] at s {s0}-{s1} meets the opening at s {o.s_m}")
        for bay in bays:
            if wall != PIER_WALLS[0] and bay["wall"] == wall and bay["span_m"][0] < s1 and bay["span_m"][1] > s0:
                raise ParamError(f"street_front_pavilions.piers[{j}] at s {s0}-{s1} on {wall} meets {bay['id']}")
        piers.append({"s_m": (s0, s1), "corner": corner, "return_m": ret,
                      **({"wall": wall} if wall != PIER_WALLS[0] else {})})
        last[wall] = s1
    street = [o for o in openings if o.wall == "k01.wall.street_front"]
    out = {"piers": tuple(piers), "proud_m": d, "from_m": y0, "course_m": ch, "channel_m": gap, "quoin_step_m": step}
    fz = spec.get("frieze")
    if fz:
        if set(fz) != FRIEZE_KEYS:
            raise ParamError(f"street_front_pavilions.frieze takes {sorted(FRIEZE_KEYS)}")
        b0, b1 = (float(x) for x in fz["bed_m"])
        p0, p1 = (float(x) for x in fz["panel_m"])
        heads = max((o.head_m for o in street), default=0.0)
        if not (heads + RING_M <= b0 < b1 <= p0 < p1 <= eave):
            raise ParamError("street_front_pavilions.frieze: its bed over every street head and its voussoirs, "
                             "the panels over the bed, all under the wall head")
        out["frieze"] = {"from_s_m": float(fz["from_s_m"]), "bed_m": (b0, b1), "bed_proud_m": float(fz["bed_proud_m"]),
                         "panel_m": (p0, p1), "panel_max_m": float(fz["panel_max_m"]),
                         "panel_inset_m": float(fz["panel_inset_m"]), "frame_m": float(fz["frame_m"]),
                         "frame_proud_m": float(fz["frame_proud_m"])}
        if not (-2.0 <= out["frieze"]["from_s_m"] <= 0.0 and 1.0 <= out["frieze"]["panel_max_m"] <= 4.0
                and 0.02 <= out["frieze"]["bed_proud_m"] <= d and 0.02 <= out["frieze"]["frame_proud_m"] <= d):
            raise ParamError("street_front_pavilions.frieze: from 0-2 m before the front's low-s end, panels "
                             "1-4 m long, bed and frames proud no further than the piers")
    md = spec.get("modillions")
    if md:
        if set(md) != MODILLION_KEYS:
            raise ParamError(f"street_front_pavilions.modillions takes {sorted(MODILLION_KEYS)}")
        if (wall_head or {}).get("cornice") != "k10.cornice.moulded_stone":
            raise ParamError("street_front_pavilions.modillions hang under the K10 moulded stone cornice")
        m = {k: float(v) for k, v in md.items()}
        if not (0.3 <= m["pitch_m"] <= 1.0 and 0.06 <= m["width_m"] <= m["pitch_m"] / 2
                and 0.1 <= m["out_m"] <= 0.3 and 0.1 <= m["drop_m"] <= 0.4 and m["end_clear_m"] >= m["width_m"]):
            raise ParamError("street_front_pavilions.modillions: 0.3-1 m apart, at most half that wide, reaching "
                             "0.1-0.3 m out and 0.1-0.4 m under the cornice's bed, clear of each end")
        out["modillions"] = m
    rb = spec.get("mansard_ribs")
    if rb:
        if set(rb) != RIB_KEYS:
            raise ParamError(f"street_front_pavilions.mansard_ribs takes {sorted(RIB_KEYS)}")
        if not mansard:
            raise ParamError("street_front_pavilions.mansard_ribs stand on a mansard's street face")
        w, rp = float(rb["width_m"]), float(rb["proud_m"])
        if not (0.2 <= w <= 0.8 and 0.04 <= rp <= 0.2):
            raise ParamError("street_front_pavilions.mansard_ribs: 0.2-0.8 m wide, 0.04-0.2 m proud")
        inset = mansard["lower_rise_m"] / math.tan(math.radians(mansard["lower_pitch_deg"]))
        ss = tuple(float(x) for x in rb["s_m"])
        for c in ss:
            if not inset + w < c < width - inset - w:
                raise ParamError(f"street_front_pavilions.mansard_ribs: the rib at s {c} meets a hip")
            for dm in mansard.get("dormers", ()):
                if dm["face"] != "street":
                    continue
                half = dm["width_m"] / 2 + 0.1
                if abs(dm["along_m"] - c) < half + w / 2:
                    raise ParamError(f"street_front_pavilions.mansard_ribs: the rib at s {c} meets the dormer at "
                                     f"{dm['along_m']}")
        out["mansard_ribs"] = {"s_m": ss, "width_m": w, "proud_m": rp}
    bt = spec.get("belt")
    if bt:
        out["belt"] = _resolve_belt(bt, width=width, depth=depth, openings=openings, eave=eave, bays=bays)
    return out


def _resolve_belt(bt, *, width, depth, openings, eave, bays) -> dict:
    """T-1881: the moulded belt course between the principal and second storeys (Taylor's
    photograph no. 1445 and the 1890 Albertype: a deep, shadowed band under the second
    storey's sills, round the Prairie front, its pavilions and the 18th Street flank). One
    moulded section `profile` ([out, up] pairs from the wall's face at its bed, back to the
    wall at its top), its bed at `bed_m`, swept along `runs` (each a wall and the stretch of
    it, s_m [from, to], in the wall's own s) and round every K08 projection standing on them."""
    if set(bt) != BELT_KEYS:
        raise ParamError(f"street_front_pavilions.belt takes {sorted(BELT_KEYS)}")
    y0 = float(bt["bed_m"])
    prof = [(float(n), float(u)) for n, u in bt["profile"]]
    if len(prof) < 4 or prof[0] != (0.0, 0.0) or prof[-1][0] != 0.0:
        raise ParamError("street_front_pavilions.belt.profile runs from the wall's face at the bed [0, 0] out "
                         "and back to the wall at its top [0, height]")
    h = prof[-1][1]
    if not (0.1 <= h <= 1.2 and all(0.0 <= n <= 0.3 for n, _ in prof)
            and all(b[1] >= a[1] - 1e-9 for a, b in zip(prof, prof[1:]))):
        raise ParamError("street_front_pavilions.belt.profile: 0.1-1.2 m high, at most 0.3 m out, never "
                         "turning back down")
    if not 1.0 <= y0 <= eave - h - 1.0:
        raise ParamError(f"street_front_pavilions.belt.bed_m {y0}: over the ground and a metre under the wall head")
    lengths = {"k01.wall.street_front": width, "k01.wall.side.north": depth, "k01.wall.rear_service": width,
               "k01.wall.side.south": depth}
    runs = []
    for j, r in enumerate(bt["runs"]):
        if set(r) != {"wall", "s_m"} or r["wall"] not in BELT_WALLS:
            raise ParamError(f"street_front_pavilions.belt.runs[{j}] takes wall (a K01 wall) and s_m [from, to]")
        a, b = (float(x) for x in r["s_m"])
        if not 0.0 <= a < b - 0.5 or b > lengths[r["wall"]] + 1e-6:
            raise ParamError(f"street_front_pavilions.belt.runs[{j}].s_m [{a}, {b}] is not a stretch of "
                             f"{r['wall']} (0-{lengths[r['wall']]} m)")
        for o in openings:
            if o.wall == r["wall"] and a < o.s_m < b and o.sill_m < y0 + h and o.head_m > y0:
                raise ParamError(f"street_front_pavilions.belt runs through {o.component} at s {o.s_m} on {o.wall}")
        on = []
        for bay in bays:
            if bay["wall"] != r["wall"]:
                continue
            s0, s1 = bay["span_m"]
            if s1 <= a or s0 >= b:
                continue
            pts = bay["variant"].get("plan", {}).get("points")
            if bay["variant"].get("kind") != "projection" or not pts or len(pts) != 4 \
                    or abs(pts[0][1]) > 1e-9 or abs(pts[3][1]) > 1e-9 or abs(pts[0][0] - pts[1][0]) > 1e-9 \
                    or abs(pts[2][0] - pts[3][0]) > 1e-9:
                raise ParamError(f"street_front_pavilions.belt: {bay['id']} is not a square projection to run round")
            on.append((float(s0), float(s1), float(pts[1][1]), bay["id"]))
        runs.append({"wall": r["wall"], "s_m": (a, b), "bays": tuple(sorted(on))})
    if not runs:
        raise ParamError("street_front_pavilions.belt names at least one run")
    return {"bed_m": y0, "profile": tuple(prof), "height_m": h, "runs": tuple(runs)}


def belt_path(run, r, y):
    """One belt run's path in plan: along the wall at its face, stepping out round each
    projection's cheeks and across its front; a projection flush with the run's end (a
    corner pavilion) carries the path to the corner on its own face."""
    a, b = r["s_m"]
    eps = 1e-6
    pts = []
    first = next((x for x in r["bays"] if x[0] <= a + eps < x[1]), None)
    pts.append((a, first[2] if first and first[0] < a - eps else 0.0))
    for s0, s1, d, _ in r["bays"]:
        if s0 > a + eps:
            pts += [(s0, 0.0), (s0, d)]
        elif s0 >= a - eps:
            pts += [(a, d)]
        if s1 < b - eps:
            pts += [(s1, d), (s1, 0.0)]
        else:
            pts += [(b, d)]
    if pts[-1][0] < b - eps:
        pts.append((b, 0.0))
    out = []
    for s, n in pts:
        q = run.at(s, y, n)
        if not out or max(abs(q[i] - out[-1][i]) for i in range(3)) > 1e-6:
            out.append(q)
    return out


def _join(runs, paths, lengths):
    """The runs' paths joined where one wall's run ends at its corner and the next wall's
    (round the house in K01's order) starts there, so the belt turns the corner mitred."""
    out, prev = [], None
    for r, p in zip(runs, paths):
        i = BELT_WALLS.index(r["wall"])
        if prev and BELT_WALLS.index(prev["wall"]) == (i - 1) % 4 \
                and abs(prev["s_m"][1] - lengths[prev["wall"]]) < 1e-6 and abs(r["s_m"][0]) < 1e-6:
            same = max(abs(p[0][k] - out[-1][-1][k]) for k in range(3)) < 1e-6
            out[-1] = out[-1] + (p[1:] if same else p)
        else:
            out.append(list(p))
        prev = r
    clean = []
    for p in out:
        q = [p[0]]
        for i in range(1, len(p) - 1):
            u = tuple(p[i][k] - q[-1][k] for k in range(3))
            v = tuple(p[i + 1][k] - p[i][k] for k in range(3))
            cr = (u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0])
            if max(abs(c) for c in cr) > 1e-9 or (u[0] * v[0] + u[1] * v[1] + u[2] * v[2]) < 0:
                q.append(p[i])
        q.append(p[-1])
        clean.append(q)
    return clean


def _courses(y0, y1, ch):
    n = max(1, round((y1 - y0) / ch))
    h = (y1 - y0) / n
    return [(y0 + i * h, y0 + (i + 1) * h) for i in range(n)]


def dress(a):
    """The piers, the frieze, the modillions and the ribs (module doc)."""
    from .k01_frontage import Y, _cross
    p, pv = a.p, a.p.pavilions
    D, W = p.depth_m, p.width_m
    conf = p.worst_conf("footprint", "storey_heights_m", "stone_front", "street_front_pavilions")
    front = ((D, 0.0, 0.0), (0.0, 0.0, -1.0), (1.0, 0.0, 0.0))
    side = ((D, 0.0, -W), (-1.0, 0.0, 0.0), (0.0, 0.0, -1.0))
    rear = ((0.0, 0.0, -W), (0.0, 0.0, 1.0), (-1.0, 0.0, 0.0))
    # each wall a pier stands on: its frame, its length and the frame its corner returns onto
    on = {PIER_WALLS[0]: (front, W, side), PIER_WALLS[1]: (side, D, rear)}
    d, gap, step = pv["proud_m"], pv["channel_m"], pv["quoin_step_m"]
    fz = pv.get("frieze") or {}
    top = a.wall_head["cornice_m"][0] if a.wall_head.get("cornice_m") else a.soffit_m
    band = fz["bed_m"][0] if fz else top
    md = pv.get("modillions")
    if fz and md and fz["panel_m"][1] > top - md["drop_m"] - 0.02:
        raise ValueError(f"street_front_pavilions: the frieze's panels reach the modillions under the cornice at {top:.3f} m")
    cid = "k01.pavilion.pier"
    for j, pr in enumerate(pv["piers"]):
        s0, s1 = pr["s_m"]
        front_, Lw, side_ = on[pr.get("wall", PIER_WALLS[0])]
        ret = pr["corner"] and pr["return_m"] > 0.0
        if pr["corner"]:
            s1 = Lw + d     # the corner pier's front runs past the next wall's face by its own proud
        mid = tuple(front_[0][i] + front_[1][i] * (s0 + s1) / 2 for i in range(3))
        seed = a.instance(cid, "pavilion", {"s0_m": s0, "s1_m": pr["s_m"][1], "proud_m": d, "from_m": pv["from_m"],
                                             "to_m": top, "corner": pr["corner"], "return_m": pr["return_m"],
                                             **({"wall": pr["wall"]} if "wall" in pr else {})},
                          {"base": (mid[0], pv["from_m"], mid[2]), "top": (mid[0], top, mid[2])})
        # the core: the channels' floor, from the coping to the cornice's bed
        a.proud_box("bay_stone", front_, s0 + step, s1 - (0.0 if pr["corner"] else step), pv["from_m"], top,
                    d - CORE_BACK_M, seed, conf)
        if ret:
            a.proud_box("bay_stone", side_, 0.0, pr["return_m"] - step, pv["from_m"], top, d - CORE_BACK_M, seed + 1, conf)
        for i, (y0, y1) in enumerate(_courses(pv["from_m"], band, pv["course_m"])):
            long_ = i % 2 == 0
            g0, g1 = y0 + gap / 2, y1 - gap / 2
            if pr["corner"]:
                # long on the front and short on the return in one course, the other way in the next
                a.proud_box("bay_stone", front_, s0 + (0.0 if long_ else step), s1, g0, g1, d, seed + 2 + i, conf)
                if ret:
                    a.proud_box("bay_stone", side_, 0.0, pr["return_m"] - (step if long_ else 0.0), g0, g1, d,
                                seed + 2 + i, conf)
            else:
                e = 0.0 if long_ else step
                a.proud_box("bay_stone", front_, s0 + e, s1 - e, g0, g1, d, seed + 2 + i, conf)
        if band < top:   # the plain head through the frieze, the cornice's bed on it
            a.proud_box("bay_stone", front_, s0, s1, band, top, d, seed + 999, conf)
            if ret:
                a.proud_box("bay_stone", side_, 0.0, pr["return_m"], band, top, d, seed + 998, conf)
    if a.wall_head.get("cornice") == "k10.cornice.moulded_stone" and band < top:
        _cornice_breaks(a, pv, top, conf)
    if pv.get("belt"):
        _belt(a, pv, conf)
    if fz:
        cid = "k01.pavilion.frieze_panel"
        spans, at = [], fz["from_s_m"]
        for pr in pv["piers"]:
            if "wall" in pr:
                continue    # the frieze's panels are the street front's
            spans.append((at, pr["s_m"][0]))
            at = pr["s_m"][1]
        if at < W - 0.5:
            spans.append((at, W))
        (b0, b1), (q0, q1) = fz["bed_m"], fz["panel_m"]
        ins, fm, fp = fz["panel_inset_m"], fz["frame_m"], fz["frame_proud_m"]
        for k, (s0, s1) in enumerate(spans):
            seed = a.instance(cid, "pavilion", {"s0_m": s0, "s1_m": s1, "bed_m": [b0, b1], "panel_m": [q0, q1]},
                              {"centre": (D, (q0 + q1) / 2, -(s0 + s1) / 2)})
            a.proud_box("bay_stone", front, s0, s1, b0, b1, fz["bed_proud_m"], seed, conf)
            n = max(1, math.ceil((s1 - s0 - 2 * ins) / fz["panel_max_m"]))
            L = (s1 - s0 - ins * (n + 1)) / n
            for i in range(n):
                c0 = s0 + ins + i * (L + ins)
                c1 = c0 + L
                # the panel's moulded frame: four strips standing proud round a sunk field
                a.proud_box("bay_stone", front, c0, c1, q1 - fm, q1, fp, seed + 10 * i + 1, conf)
                a.proud_box("bay_stone", front, c0, c1, q0, q0 + fm, fp, seed + 10 * i + 2, conf)
                a.proud_box("bay_stone", front, c0, c0 + fm, q0 + fm, q1 - fm, fp, seed + 10 * i + 3, conf)
                a.proud_box("bay_stone", front, c1 - fm, c1, q0 + fm, q1 - fm, fp, seed + 10 * i + 4, conf)
    if md and a.wall_head.get("stretches"):
        from . import k10_frontage
        cid = "k01.pavilion.modillion"
        y_c = a.wall_head["cornice_m"][0]
        frames = {"k01.wall.street_front": front, "k01.wall.side.north": side,
                  "k01.wall.rear_service": ((0.0, 0.0, -W), (0.0, 0.0, 1.0), _cross((0.0, 0.0, 1.0), Y)),
                  "k01.wall.side.south": ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), _cross((1.0, 0.0, 0.0), Y))}
        runs, start, laid = k10_frontage.runs(p), 0.0, 0
        hw, clear, pitch = md["width_m"] / 2, md["end_clear_m"], md["pitch_m"]
        nxt = {PIER_WALLS[0]: "k01.wall.side.north", PIER_WALLS[1]: "k01.wall.rear_service"}
        broken = [w for pr in pv["piers"] for wl in [pr.get("wall", PIER_WALLS[0])] for w in (
            [(wl, pr["s_m"][0] - 0.02, pr["s_m"][1] + 1.0), (nxt[wl], -1.0, pr["return_m"] + 0.02)]
            if pr["corner"] else [(wl, pr["s_m"][0] - 0.02, pr["s_m"][1] + 0.02)])]
        for run in runs:
            L = run.L
            for t0, t1 in a.wall_head["stretches"]:
                s0, s1 = max(t0 - start, 0.0) + clear, min(t1 - start, L) - clear
                if s1 - s0 < pitch:
                    continue
                n = int((s1 - s0) // pitch)
                off = s0 + ((s1 - s0) - n * pitch) / 2
                fr = frames[run.name]
                for i in range(n + 1):
                    c = off + i * pitch
                    if any(lo - hw < c < hi + hw for wall, lo, hi in broken if wall == run.name):
                        continue   # under a break the pier's head stands where the console would
                    seed = a.instance(cid, "pavilion", {"wall": run.name, "s_m": round(c, 4)},
                                      {"bed": (0.0, y_c, 0.0)})
                    # a block under the corona and the console's foot under it, half as far out
                    a.proud_box("bay_stone", fr, c - hw, c + hw, y_c, y_c + 0.15, md["out_m"], seed, conf)
                    a.proud_box("bay_stone", fr, c - hw, c + hw, y_c - md["drop_m"], y_c, md["out_m"] / 2, seed + 1, conf)
                    laid += 1
            start += L
        a.pavilion_modillions = laid
    rb = pv.get("mansard_ribs")
    if rb:
        m = p.mansard
        E, o = p.eave_m, p.eave_overhang_m
        pitch = math.radians(m["lower_pitch_deg"])
        t = (-math.cos(pitch), math.sin(pitch), 0.0)       # up the street face
        nrm = (math.sin(pitch), math.cos(pitch), 0.0)      # out of it
        L = m["lower_rise_m"] / math.sin(pitch) - RIB_CURB_CLEAR_M / math.sin(pitch)
        base = (D + o, E, 0.0)
        cid = "k01.roof.mansard_rib"
        pr_ = a.prim("bay_stone")
        for c in rb["s_m"]:
            seed = a.instance(cid, "pavilion", {"s_m": c, "width_m": rb["width_m"], "proud_m": rb["proud_m"]},
                              {"foot": (D + o, E, -c)})
            z0, z1 = -c + rb["width_m"] / 2, -c - rb["width_m"] / 2

            def P(along, z, out):
                return (base[0] + t[0] * along + nrm[0] * out, base[1] + t[1] * along + nrm[1] * out, z)
            bf = a.basis("bay_stone", P(0, z0, rb["proud_m"]), (0.0, 0.0, -1.0), t, seed)
            bs = a.basis("bay_stone", P(0, z0, 0), t, nrm, seed)
            be = a.basis("bay_stone", P(0, z0, 0), (0.0, 0.0, -1.0), nrm, seed)
            q, b = rb["proud_m"], -RIB_BURY_M
            pr_.face([P(0, z0, q), P(L, z0, q), P(L, z1, q), P(0, z1, q)], nrm, bf, conf)
            pr_.face([P(0, z0, b), P(L, z0, b), P(L, z0, q), P(0, z0, q)], (0.0, 0.0, 1.0), bs, conf)
            pr_.face([P(0, z1, b), P(L, z1, b), P(L, z1, q), P(0, z1, q)], (0.0, 0.0, -1.0), bs, conf)
            pr_.face([P(L, z0, b), P(L, z1, b), P(L, z1, q), P(L, z0, q)], t, be, conf)
            pr_.face([P(0, z0, b), P(0, z1, b), P(0, z1, q), P(0, z0, q)], (-t[0], -t[1], 0.0), be, conf)


def _cornice_breaks(a, pv, y_c, conf):
    """The K10 moulded stone cornice broken forward over each pier by the pier's own proud:
    the kit's section swept along the pier's face from end to end and capped at both, its seat
    on the pier's head; round the corner pier's two faces in one mitred run."""
    from . import k10_frontage
    K = k10_frontage._kit()
    data = K.load()
    p = a.p
    v = next(x for x in data["variants"] if x["id"] == k10_frontage.STONE)
    prof = [tuple(q) for q in data["parts"]["profiles"][v["profile"]]["points"]]
    if p.wall_head.get("depth_m"):
        ch = max(u for _, u in prof)
        prof = [(n, u * float(p.wall_head["depth_m"]) / ch) for n, u in prof]
    rn = k10_frontage.runs(p)
    d = pv["proud_m"]
    cid = "k01.pavilion.cornice_break"
    var = K.Variant({"id": cid, "kind": "moulded", "material": "stone"}, data)
    for j, pr in enumerate(pv["piers"]):
        s0, s1 = pr["s_m"]
        i = PIER_WALLS.index(pr.get("wall", PIER_WALLS[0]))
        front, side = rn[i], rn[i + 1]
        ret = pr["corner"] and pr["return_m"] > 0.0
        seed = a.instance(cid, "pavilion", {"s0_m": s0, "s1_m": s1, "proud_m": d, "corner": pr["corner"],
                                            **({"wall": pr["wall"]} if "wall" in pr else {})},
                          {"bed": front.at((s0 + s1) / 2, y_c, d)})
        var.seed, var.rng = seed, __import__("random").Random(seed)
        pc = var.piece(f"cornice break {j + 1}", "stone", "open",
                       run_names=[front.name] + ([side.name] if ret else []))
        path = [front.at(s0, y_c, d), front.at(front.L + d, y_c, d)] + ([side.at(pr["return_m"], y_c, d)] if ret else []) \
            if pr["corner"] else [front.at(s0, y_c, d), front.at(s1, y_c, d)]
        K.sweep(pc.mesh, path, K.Y, prof, side=1.0, sgn=1.0, caps=(True, True))
    k10_frontage._lay(a, var.pieces, conf, cid)


def _belt(a, pv, conf):
    """T-1881: the belt course (`_resolve_belt`) swept along its runs and round their
    projections, mitred at every turn and capped where a run stops; over each pier broken
    forward by the pier's proud, as the cornice is (`_cornice_breaks`)."""
    import random
    from . import k10_frontage
    K = k10_frontage._kit()
    data = K.load()
    p, bt = a.p, pv["belt"]
    y, prof = bt["bed_m"], list(bt["profile"])
    runs = {r.name: r for r in k10_frontage.runs(p)}
    lengths = {n: r.L for n, r in runs.items()}
    paths = [belt_path(runs[r["wall"]], r, y) for r in bt["runs"]]
    cid = "k01.pavilion.belt"
    var = K.Variant({"id": cid, "kind": "moulded", "material": "stone"}, data)
    names = [r["wall"] for r in bt["runs"]]
    seed = a.instance(cid, "pavilion", {"bed_m": y, "height_m": bt["height_m"], "walls": names,
                                        "projections": [x[3] for r in bt["runs"] for x in r["bays"]]},
                      {"bed": paths[0][0]})
    var.seed, var.rng = seed, random.Random(seed)
    for j, path in enumerate(_join(bt["runs"], paths, lengths)):
        pc = var.piece(f"belt {j + 1}", "stone", "open", run_names=names)
        K.sweep(pc.mesh, path, K.Y, prof, side=1.0, sgn=1.0, caps=(True, True))
    d = pv["proud_m"]
    order = ("k01.wall.street_front", "k01.wall.side.north", "k01.wall.rear_service")
    for j, pr in enumerate(pv["piers"]):
        s0, s1 = pr["s_m"]
        i = PIER_WALLS.index(pr.get("wall", PIER_WALLS[0]))
        front, side = runs[order[i]], runs[order[i + 1]]
        on_front = [r["s_m"] for r in bt["runs"] if r["wall"] == front.name]
        on_side = pr["return_m"] > 0.0 and any(r["wall"] == side.name for r in bt["runs"])
        if not any(a0 <= s0 and s1 <= b0 + 1e-6 for a0, b0 in on_front):
            continue
        pc = var.piece(f"belt break {j + 1}", "stone", "open",
                       run_names=[front.name] + ([side.name] if pr["corner"] and on_side else []))
        if pr["corner"] and on_side:
            path = [front.at(s0, y, d), front.at(front.L + d, y, d), side.at(pr["return_m"], y, d)]
        elif pr["corner"] and pr["return_m"] == 0.0:    # a flank's corner pier: to its own end
            path = [front.at(s0, y, d), front.at(front.L + d, y, d)]
        else:
            path = [front.at(s0, y, d), front.at(s1, y, d)]
        K.sweep(pc.mesh, path, K.Y, prof, side=1.0, sgn=1.0, caps=(True, True))
    k10_frontage._lay(a, var.pieces, conf, cid)
