#!/usr/bin/env python3
"""Nothing stands inside a building: no other building, no fence, no yard prop (T-3078).

    python3 tools/check_structure_clearance.py               the gate, every scene
    python3 tools/check_structure_clearance.py --report      every finding, ruled ones too
    python3 tools/check_structure_clearance.py --self-test   break it six ways; each must fire

WHY THIS EXISTS. The owner, 2026-10-23, with a screenshot from 35 ft over Lake and Canal
in 1835: *"Not right make sure this does not happen again."* Two shops stood inside each
other there — Goss & Cobb's saddlery and Pierce's blacksmith shop, each placed on the
south-east corner by its own record a fortnight apart, 2.7 m deep into one another — with
the Lake Street rail fence running into them. Sweeping the three scenes for the same fault
found two more pairs of buildings grown together in 1835 (the Exchange Coffee House and the
New York House, 6.5 m deep; a riverbank shed built through the agency striker's cabin) and
fences through four rotated houses. Every one of those passed every gate this project ran,
because each tool that placed a thing tested it only against what that tool knew about, and
the tools that dodged houses read a footprint the renderer does not draw: the shared
`footprint_world` in tools/generate_dooryard_pickets.py turned a footprint COUNTER-clockwise
by its bearing, so at 90 or 270 degrees the fence cut itself clear of the house's mirror image
and ran through the house. This asks the question once, of the placed shapes, across layers.

WHAT IS A BUILDING'S SHAPE. Its sidecar footprint polygon placed the way the renderer seats
the mesh (renderers/web/js/angles.js bearingToYaw: the bearing turns it CLOCKWISE), plus the
rear ell a frame tavern record builds outside that polygon, because a fence through an
ell is a fence through the house (generate_dooryard_plantings.rear_ell_world, which the
yard tools now stand clear of too). Other wings that sit outside their polygon are not seen
here; that is a limit, not a ruling.

THE THREE QUESTIONS, per scene (1812, 1835, 1904):

  A. BUILDING INTO BUILDING. Two walled footprints may share a party wall — the infill rows
     stand wall to wall and seat 0.0 to 0.35 m into each other — but not stand inside one
     another: a pair whose overlap is deeper than PARTY_WALL_M is a fault. (Convex pairs are
     measured by the separating-axis depth; a non-convex footprint by sampled area over
     NONCONVEX_AREA_M2.) A `palisade` record is a fence, not a room: it is asked question B
     along its perimeter instead, so a garden fence round a house is fine and one through
     it is not. A footprint that is open ground (a parade) is ruled below.
  B. FENCE THROUGH BUILDING. Every fence run on the enclosure layer, every street-edge fence
     and plank walk, and every palisade's perimeter, sampled every SAMPLE_M: no sample may
     stand more than FENCE_TOL_M inside a building. A fence that ENDS AT a wall is a fence
     meeting a house, which is what yard fences do; one that goes on inside it is the bug.
  C. PROP INSIDE BUILDING. Every placed item on the yard layers (woodpiles, trade goods,
     wagons, sheds, outbuildings, building material, the water cart) and the street edge's
     posts and fittings: its centre may not stand more than PROP_TOL_M inside a building. A
     woodpile against a wall stands outside it; one whose middle is in the parlour does not.

  D. BUILDING ACROSS A WALK OR AN ALLEY (1835, T-3360). The owner, 2026-11-03, over State
     and Lake: buildings "placed in the middle of the walkways or alleys" — St. Mary's church
     stood 3.97 m out past its State Street lot line and the plank walk stopped dead at its
     wall; Chappel's school did the same north of Lake and sat in its block's alley mouth.
     The street-edge generator had been doing exactly what it says (a march step a footprint
     stands on carries no boards) and the alley generator cut its lane short and printed the
     cut, so nothing went red: a refused step is the generator's answer, not a fault. This
     asks the TOWN the question instead. Every street-edge face the walk rule marches
     (tools/generate_frontage_works.py, the same faces and the same three probes across the
     deck its march uses) may carry no building on its walk line, and no building may stand
     more than ALLEY_TOL_M inside a platted alley strip (thompson_lots.json
     `alley_local_enu_m`). Where a source fixes a building so exactly that the walk must have
     gone round it, that is a ruling in RULED_ON_WAY, with the reason.

RULINGS are the pairs that overlap on purpose, each with the reason; a ruling that no longer
matches anything fails, so the list cannot outlive what it excuses.
"""
from __future__ import annotations

import argparse
import copy
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
sys.path.insert(0, str(ROOT / "tools"))

from generate_dooryard_plantings import rear_ell_world  # noqa: E402
from occupied_footprints import additional_world_polygons  # noqa: E402

SCENES = ("1812", "1835", "1904")
PARTY_WALL_M = 0.40       # deeper than a wall's thickness is one building inside another
NONCONVEX_AREA_M2 = 0.50  # the same question for an L-shaped footprint, asked by area
FENCE_TOL_M = 0.05        # a fence end may touch a wall line; it may not go on inside
PROP_TOL_M = 0.15         # a prop's centre may sit on a wall line, not inside the room
SAMPLE_M = 0.10

FIRST_FORT = ("Whistler's 1808 draught of the first fort sets each blockhouse straddling the angle "
              "of both picket rows, and the record seats the draught's box as drawn")

# Pairs that overlap ON PURPOSE. (scene, a, b) with a < b, and why. A pair listed here that no
# longer overlaps fails the gate: a ruling is a statement about the town, kept only while true.
RULED = {
    ("1812", "first_fort_dearborn_blockhouse_nw", "first_fort_dearborn_pickets_inner"):
        FIRST_FORT,
    ("1812", "first_fort_dearborn_blockhouse_nw", "first_fort_dearborn_pickets_outer"):
        FIRST_FORT,
    ("1812", "first_fort_dearborn_blockhouse_se", "first_fort_dearborn_pickets_inner"):
        FIRST_FORT,
    ("1812", "first_fort_dearborn_blockhouse_se", "first_fort_dearborn_pickets_outer"):
        FIRST_FORT,
    ("1835", "fort_dearborn_blockhouse", "fort_dearborn_palisade"):
        ("the second fort's blockhouse stands at the south-west angle astride the corner of "
         "the stockade and projecting outside it, as its own record places it"),
}

# Footprints that are ground, not walls: a fence or a building may stand on them. Kept short
# and by id, so nothing becomes open ground by being renamed.
OPEN_GROUND = {
    "first_fort_dearborn_parade": "the parade is the fort's open square; its buildings stand round and on it",
    "first_fort_dearborn_flagstaff": "a pole, not a room",
    "fort_dearborn_parade": "the parade is the fort's open square; its buildings stand round and on it",
    "fort_dearborn_flagstaff": "a pole, not a room",
}

FENCE_ARCHETYPES = {"palisade"}

ALLEY_TOL_M = 0.05        # a wall may stand on the alley line, not inside the strip

# Buildings a source places so exactly that the walk or the alley went round them (question D):
# (scene, structure id, "walk" | "alley") and why. Empty: every building that stood on a walk or
# in an alley on 2026-11-03 was placed by a corner, a block face or a recipe, never by a
# coordinate, and was moved back onto its lot instead (T-3360). A ruling here that no longer
# matches anything fails, like RULED.
RULED_ON_WAY: dict = {}


# --------------------------------------------------------------------------- geometry
def placed(sidecar: dict) -> list[tuple[float, float]]:
    """The sidecar footprint where the renderer stands it: bearing turns it clockwise."""
    fp = (sidecar.get("footprint") or {}).get("polygon") or []
    pl = sidecar.get("placement") or {}
    e0, n0 = pl.get("local_e"), pl.get("local_n")
    if e0 is None or n0 is None or len(fp) < 3:
        return []
    return [to_world(u, v, pl) for u, v in fp]


def to_world(u: float, v: float, pl: dict) -> tuple[float, float]:
    th = math.radians(float(pl.get("rotation_deg") or 0.0))
    c, s = math.cos(th), math.sin(th)
    return (float(pl["local_e"]) + u * c + v * s, float(pl["local_n"]) - u * s + v * c)


def convex(poly) -> bool:
    signs = set()
    n = len(poly)
    for i in range(n):
        a, b, c = poly[i], poly[(i + 1) % n], poly[(i + 2) % n]
        cr = (b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0])
        if abs(cr) > 1e-9:
            signs.add(cr > 0)
    return len(signs) <= 1


def sat_depth(a, b) -> float:
    """How far the two convex polygons would have to move apart; <= 0 if they do not touch."""
    best = math.inf
    for poly in (a, b):
        n = len(poly)
        for i in range(n):
            x1, y1 = poly[i]
            x2, y2 = poly[(i + 1) % n]
            ax, ay = -(y2 - y1), x2 - x1
            ln = math.hypot(ax, ay)
            if ln < 1e-12:
                continue
            ax, ay = ax / ln, ay / ln
            pa = [ax * x + ay * y for x, y in a]
            pb = [ax * x + ay * y for x, y in b]
            best = min(best, min(max(pa), max(pb)) - max(min(pa), min(pb)))
    return best


def inside(p, poly) -> bool:
    x, y = p
    hit = False
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
            hit = not hit
    return hit


def edge_distance(p, poly) -> float:
    best = math.inf
    n = len(poly)
    for i in range(n):
        a, b = poly[i], poly[(i + 1) % n]
        vx, vy = b[0] - a[0], b[1] - a[1]
        span = vx * vx + vy * vy
        t = 0.0 if span == 0 else max(0.0, min(1.0, ((p[0] - a[0]) * vx + (p[1] - a[1]) * vy) / span))
        best = min(best, math.dist(p, (a[0] + t * vx, a[1] + t * vy)))
    return best


def depth_inside(p, poly) -> float:
    """How far inside the polygon the point stands; 0 outside."""
    return edge_distance(p, poly) if inside(p, poly) else 0.0


def bbox(poly):
    xs = [p[0] for p in poly]
    ys = [p[1] for p in poly]
    return min(xs), min(ys), max(xs), max(ys)


def boxes_apart(a, b, pad=0.0) -> bool:
    return a[2] + pad < b[0] or b[2] + pad < a[0] or a[3] + pad < b[1] or b[3] + pad < a[1]


def sampled_area(a, b) -> float:
    ba, bb = bbox(a), bbox(b)
    x0, y0 = max(ba[0], bb[0]), max(ba[1], bb[1])
    x1, y1 = min(ba[2], bb[2]), min(ba[3], bb[3])
    if x1 <= x0 or y1 <= y0:
        return 0.0
    st, n = SAMPLE_M, 0
    x = x0 + st / 2
    while x < x1:
        y = y0 + st / 2
        while y < y1:
            if inside((x, y), a) and inside((x, y), b):
                n += 1
            y += st
        x += st
    return n * st * st


def run_inside(path, poly) -> tuple[float, float]:
    """(metres of the run more than FENCE_TOL_M inside, deepest point) along a polyline."""
    length, deepest = 0.0, 0.0
    for a, b in zip(path, path[1:]):
        seg = math.dist(a, b)
        steps = max(1, int(seg / SAMPLE_M))
        for k in range(steps + 1):
            t = k / steps
            d = depth_inside((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t), poly)
            if d > FENCE_TOL_M:
                length += seg / steps
                deepest = max(deepest, d)
    return length, deepest


# --------------------------------------------------------------------------- reading
def load(path: Path):
    with open(path) as fh:
        return json.load(fh)


def buildings(scene: str, overrides: dict | None = None) -> list[dict]:
    out = []
    for f in sorted((DATA / "sidecars" / scene).glob("*.json")):
        try:
            sc = load(f)
        except (OSError, ValueError):
            continue
        if not isinstance(sc, dict) or "placement" not in sc or "footprint" not in sc:
            continue
        if overrides and sc.get("id") in overrides:
            sc = overrides[sc["id"]]
        # The walker's own exclusions (walker.js footprintsFrom): a water-anchored footprint
        # is a deck you walk on, and a record another layer draws is that layer's line.
        if (sc.get("placement") or {}).get("vertical_anchor") == "water" or sc.get("drawn_by"):
            continue
        poly = placed(sc)
        if len(poly) < 3:
            continue
        sid = sc.get("id") or f.stem
        rec_path = DATA / "structures" / f"{sid}.json"
        rec = load(rec_path) if rec_path.exists() else None
        shapes = [poly, *additional_world_polygons(sc)]
        ell = rear_ell_world(sc, rec) if rec else []
        if ell:
            shapes.append(ell)
        out.append({"id": sid, "archetype": sc.get("archetype"), "shapes": shapes,
                    "box": bbox([p for s in shapes for p in s])})
    return out


def runs_1835(layers: dict | None = None) -> list[tuple[str, str, list]]:
    """(layer, id, path) for every fence and walk the 1835 layers draw."""
    layers = layers if layers is not None else layer_files()
    out = []
    for name, doc in layers.items():
        if name.startswith("enclosures/"):
            for run in doc.get("runs") or []:
                if run.get("path_local_enu_m"):
                    out.append((name, run.get("id") or "?", run["path_local_enu_m"]))
        elif name == "frontage/town_street_edge.json":
            for fence in doc.get("fences") or []:
                out.append((name, fence.get("id") or "?", fence["path_local_enu_m"]))
            for walk in doc.get("walks") or []:
                out.append((name, walk.get("id") or "?", walk["centreline_local_enu_m"]))
    return out


def props_1835(layers: dict | None = None) -> list[tuple[str, str, list]]:
    """(layer, id, point) for every placed prop on the yard layers and the street edge."""
    layers = layers if layers is not None else layer_files()
    out = []

    def walk(o, layer, label):
        if isinstance(o, dict):
            at = o.get("at_local_enu_m")
            if isinstance(at, list) and len(at) == 2 and all(isinstance(v, (int, float)) for v in at):
                out.append((layer, o.get("id") or o.get("kind") or label, at))
            for k, v in o.items():
                if k == "refused":
                    continue
                walk(v, layer, o.get("id") or o.get("structure_id") or label)
        elif isinstance(o, list):
            for v in o:
                walk(v, layer, label)

    for name, doc in layers.items():
        if name.startswith("yard/"):
            walk(doc, name, name)
        elif name == "frontage/town_street_edge.json":
            for key in ("posts", "fittings"):
                for item in doc.get(key) or []:
                    walk(item, name, key)
    return out


def layer_files() -> dict:
    out = {}
    for sub in ("enclosures", "yard"):
        for f in sorted((DATA / sub).glob("*.json")):
            if f.name == "index.json":
                continue
            out[f"{sub}/{f.name}"] = load(f)
    out["frontage/town_street_edge.json"] = load(DATA / "frontage" / "town_street_edge.json")
    return out


# --------------------------------------------------------------------------- the questions
def findings(scene: str, blds: list[dict], runs=(), props=()) -> list[dict]:
    out = []
    walls = [b for b in blds if b["archetype"] not in FENCE_ARCHETYPES and b["id"] not in OPEN_GROUND]
    fences = [b for b in blds if b["archetype"] in FENCE_ARCHETYPES]

    # A. building into building
    for i in range(len(walls)):
        for j in range(i + 1, len(walls)):
            a, b = walls[i], walls[j]
            if boxes_apart(a["box"], b["box"]):
                continue
            worst = None
            for sa in a["shapes"]:
                for sb in b["shapes"]:
                    if boxes_apart(bbox(sa), bbox(sb)):
                        continue
                    if convex(sa) and convex(sb):
                        d = sat_depth(sa, sb)
                        if d > PARTY_WALL_M:
                            worst = max(worst or 0.0, d)
                    else:
                        area = sampled_area(sa, sb)
                        if area > NONCONVEX_AREA_M2:
                            worst = max(worst or 0.0, area)
            if worst is not None:
                x, y = sorted((a["id"], b["id"]))
                out.append({"scene": scene, "kind": "building_in_building", "a": x, "b": y,
                            "text": f"{x} and {y} stand inside each other "
                                    f"({worst:.2f} {'m deep' if worst <= 50 else 'm2'})"})

    # B. fences (palisade perimeters here; layer runs below) through walls
    def fence_hits(layer, rid, path):
        box = bbox(path)
        for w in walls:
            if boxes_apart(box, w["box"]):
                continue
            for shape in w["shapes"]:
                length, deepest = run_inside(path, shape)
                if length > 0:
                    x, y = sorted((rid, w["id"]))
                    out.append({"scene": scene, "kind": "fence_through_building", "a": x, "b": y,
                                "text": f"{layer} {rid} runs {length:.2f} m inside {w['id']}, "
                                        f"{deepest:.2f} m deep"})
                    break

    for f in fences:
        ring = f["shapes"][0]
        fence_hits("palisade", f["id"], ring + [ring[0]])
    for layer, rid, path in runs:
        fence_hits(layer, rid, path)

    # C. props inside walls
    for layer, pid, at in props:
        for w in walls:
            b = w["box"]
            if not (b[0] - 1 <= at[0] <= b[2] + 1 and b[1] - 1 <= at[1] <= b[3] + 1):
                continue
            d = max(depth_inside(at, s) for s in w["shapes"])
            if d > PROP_TOL_M:
                out.append({"scene": scene, "kind": "prop_in_building", "a": pid, "b": w["id"],
                            "text": f"{layer} {pid} stands {d:.2f} m inside {w['id']}"})
                break
    return out


def ways_1835(blds: list[dict]) -> list[dict]:
    """Question D: buildings standing on a street-edge walk line or inside a platted alley."""
    import generate_frontage_works as gfw   # noqa: E402 — heavy, and only 1835 needs it
    out = []
    walls = [b for b in blds if b["archetype"] not in FENCE_ARCHETYPES and b["id"] not in OPEN_GROUND]
    # The march's own building shape: centre, radius and ring, one entry per shape so a rear
    # ell blocks the walk the way its house does.
    feet = []
    for w in walls:
        for shape in w["shapes"]:
            ce = sum(p[0] for p in shape) / len(shape)
            cn = sum(p[1] for p in shape) / len(shape)
            feet.append({"id": w["id"], "pts": shape, "e": ce, "n": cn,
                         "r": max(math.hypot(p[0] - ce, p[1] - cn) for p in shape)})
    lots = gfw._lots()
    faces = gfw._edge_faces(lots)
    covered = {(f["block"]["id"], f["face"]) for f in faces}
    faces += gfw._front_faces(lots, gfw._placed_footprints(), gfw._streets(), covered)
    half = gfw.WALK_W_M / 2.0
    seen = set()
    for entry in faces:
        frame = entry["frame"]
        steps = max(1, int(frame["length"] / 0.5))
        for k in range(steps + 1):
            t = frame["length"] * k / steps
            pt = (frame["origin"][0] + frame["along"][0] * t + frame["outward"][0] * gfw.EDGE_OFFSET_M,
                  frame["origin"][1] + frame["along"][1] * t + frame["outward"][1] * gfw.EDGE_OFFSET_M)
            sid = gfw._wall_on(pt, half, frame["outward"], feet)
            key = (sid, entry["block"]["id"], entry["face"])
            if sid and key not in seen:
                seen.add(key)
                out.append({"scene": "1835", "kind": "building_on_walk", "a": sid, "b": "walk",
                            "text": f"{sid} stands on the plank walk line of {entry['block']['id']}'s "
                                    f"{entry['face']} face ({entry['street']}), {t:.1f} m along it"})
    for blk in lots.get("blocks", []):
        strip = blk.get("alley_local_enu_m")
        if not strip or len(strip) < 4:
            continue
        q = [tuple(p) for p in strip[:4]]
        sides = [(q[i], q[(i + 1) % 4]) for i in range(4)]
        lens = [math.dist(a, b) for a, b in sides]
        k = 0 if lens[0] + lens[2] < lens[1] + lens[3] else 1
        mid = lambda s: ((s[0][0] + s[1][0]) / 2.0, (s[0][1] + s[1][1]) / 2.0)  # noqa: E731
        a, b = mid(sides[k]), mid(sides[k + 2])
        length, hw = math.dist(a, b), (lens[k] + lens[k + 2]) / 4.0 - ALLEY_TOL_M
        if length < 1e-6 or hw <= 0:
            continue
        u = ((b[0] - a[0]) / length, (b[1] - a[1]) / length)
        nrm = (-u[1], u[0])
        box = bbox(q)
        for w in walls:
            if boxes_apart(box, w["box"]):
                continue
            hit = None
            for shape in w["shapes"]:
                sb = bbox(shape)
                s = 0.0
                while s <= length and hit is None:
                    for f in (-1.0, -0.5, 0.0, 0.5, 1.0):
                        p = (a[0] + u[0] * s + nrm[0] * hw * f, a[1] + u[1] * s + nrm[1] * hw * f)
                        if sb[0] <= p[0] <= sb[2] and sb[1] <= p[1] <= sb[3] and inside(p, shape):
                            hit = s
                            break
                    s += 0.25
            if hit is not None:
                out.append({"scene": "1835", "kind": "building_in_alley", "a": w["id"], "b": "alley",
                            "text": f"{w['id']} stands inside {blk['id']}'s platted alley, "
                                    f"{hit:.1f} m along it"})
    return out


def judge(all_findings: list[dict]) -> tuple[list[dict], list[dict], list[tuple]]:
    """(faults, ruled, stale rulings)."""
    faults, ruled, used = [], [], set()
    for f in all_findings:
        key = (f["scene"], f["a"], f["b"])
        if key in RULED or key in RULED_ON_WAY:
            ruled.append(f)
            used.add(key)
        else:
            faults.append(f)
    stale = [k for k in (*RULED, *RULED_ON_WAY) if k not in used]
    return faults, ruled, stale


def survey(overrides: dict | None = None, layers: dict | None = None) -> list[dict]:
    out = []
    for scene in SCENES:
        blds = buildings(scene, (overrides or {}).get(scene))
        if scene == "1835":
            out += findings(scene, blds, runs_1835(layers), props_1835(layers))
            out += ways_1835(blds)
        else:
            out += findings(scene, blds)
    return out


def describe(f: dict) -> str:
    return f"{f['scene']}: {f['text']}"


# --------------------------------------------------------------------------- self-test
def self_test() -> int:
    problems = []

    def expect(label, ok):
        print(f"   self-test | {'ok  ' if ok else 'FAIL'} {label}")
        if not ok:
            problems.append(label)

    # 0. the convention: a 90-degree building turns clockwise, the way the renderer draws it.
    sc = {"placement": {"local_e": 0.0, "local_n": 0.0, "rotation_deg": 90.0},
          "footprint": {"polygon": [[0, 0], [10, 0], [10, 4], [0, 4]]}}
    poly = placed(sc)
    expect("a bearing of 90 turns the footprint's +u axis to the SOUTH (clockwise), as angles.js does",
           abs(poly[1][0]) < 1e-9 and abs(poly[1][1] + 10) < 1e-9)

    base = survey()
    faults, _, stale = judge(base)
    expect("the committed town is clean", not faults and not stale)

    def sidecar(scene, sid):
        return load(DATA / "sidecars" / scene / f"{sid}.json")

    # 1. two buildings put on one corner: the saddlery moved onto the blacksmith shop.
    a = copy.deepcopy(sidecar("1835", "goss_cobb_saddlery"))
    b = sidecar("1835", "pierce_blacksmith_shop")
    a["placement"]["local_e"] = b["placement"]["local_e"] + 3.0
    a["placement"]["local_n"] = b["placement"]["local_n"] + 3.0
    a["placement"]["rotation_deg"] = 0.0
    hit = [f for f in survey({"1835": {a["id"]: a}}) if f["kind"] == "building_in_building"
           and {f["a"], f["b"]} == {"goss_cobb_saddlery", "pierce_blacksmith_shop"}]
    expect("…two shops placed on one corner are refused", bool(hit))

    # 2. a fence through a rotated house: a run laid across the middle of a 90-degree building.
    house = sidecar("1835", "bates_auction_room")
    poly = placed(house)
    cx = sum(p[0] for p in poly) / len(poly)
    cy = sum(p[1] for p in poly) / len(poly)
    layers = layer_files()
    rails = copy.deepcopy(layers["enclosures/town_lot_line_rails.json"])
    rails["runs"].append({"id": "self_test_run", "path_local_enu_m": [[cx - 20, cy], [cx + 20, cy]]})
    layers["enclosures/town_lot_line_rails.json"] = rails
    hit = [f for f in survey(layers=layers) if f["kind"] == "fence_through_building" and "self_test_run" in (f["a"], f["b"])]
    expect("…a fence laid through a house turned to 90 degrees is refused", bool(hit))

    # 3. the same fence read through the counter-clockwise footprint misses the house — which is
    #    the fault this gate was written for, proved by reproducing it.
    th = math.radians(90.0)
    pl = house["placement"]
    wrong = [(pl["local_e"] + u * math.cos(th) - v * math.sin(th), pl["local_n"] + u * math.sin(th) + v * math.cos(th))
             for u, v in house["footprint"]["polygon"]]
    expect("…and the counter-clockwise footprint the fence tools read before does NOT contain the house's middle",
           not inside((cx, cy), wrong))

    # 4. a prop inside a house: a woodpile dropped in the auction room.
    layers = layer_files()
    piles = copy.deepcopy(layers["yard/town_woodpiles.json"])
    piles["lots"].append({"structure_id": "self_test", "items": [{"id": "self_test_pile", "kind": "cordwood", "at_local_enu_m": [cx, cy]}]})
    layers["yard/town_woodpiles.json"] = piles
    hit = [f for f in survey(layers=layers) if f["kind"] == "prop_in_building" and f["a"] == "self_test_pile"]
    expect("…a woodpile standing in a room is refused", bool(hit))

    # 5. question D (T-3360): a house set down on a plank walk line and another in an alley.
    walked = next(w for w in json.loads((DATA / "frontage" / "town_street_edge.json").read_text())["walks"]
                  if w["id"].endswith("_walk_1") and "_crossing_" not in w["id"])
    (e0, n0), (e1, n1) = walked["centreline_local_enu_m"]
    on_walk = copy.deepcopy(sidecar("1835", "goss_cobb_saddlery"))
    on_walk["placement"].update({"local_e": (e0 + e1) / 2.0 - 3.0, "local_n": (n0 + n1) / 2.0 - 3.0,
                                 "rotation_deg": 0.0})
    hit = [f for f in survey({"1835": {on_walk["id"]: on_walk}})
           if f["kind"] == "building_on_walk" and f["a"] == on_walk["id"]]
    expect("…a shop set down on a plank walk line is refused", bool(hit))
    lots_doc = load(DATA / "traces" / "vectors" / "thompson_lots.json")
    strip = next(b["alley_local_enu_m"] for b in lots_doc["blocks"] if b.get("alley_local_enu_m"))
    ae = sum(p[0] for p in strip[:4]) / 4.0
    an = sum(p[1] for p in strip[:4]) / 4.0
    in_alley = copy.deepcopy(sidecar("1835", "goss_cobb_saddlery"))
    in_alley["placement"].update({"local_e": ae - 2.0, "local_n": an - 2.0, "rotation_deg": 0.0})
    hit = [f for f in survey({"1835": {in_alley["id"]: in_alley}})
           if f["kind"] == "building_in_alley" and f["a"] == in_alley["id"]]
    expect("…a shop set down in the middle of a platted alley is refused", bool(hit))

    # 6. a ruling that excuses nothing is itself refused.
    RULED[("1835", "a_house_that_is_not", "another_that_is_not")] = "self-test"
    try:
        _, _, stale = judge(base)
        expect("…a ruling that no longer matches anything is refused", bool(stale))
    finally:
        del RULED[("1835", "a_house_that_is_not", "another_that_is_not")]

    if problems:
        print(f"SELF-TEST FAIL: {len(problems)} case(s) did not fire")
        return 1
    print("self-test: every case fired")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    faults, ruled, stale = judge(survey())
    if args.report:
        for f in ruled:
            key = (f["scene"], f["a"], f["b"])
            print("ruled  " + describe(f) + " — " + (RULED.get(key) or RULED_ON_WAY[key]))
    for f in faults:
        print("FAIL   " + describe(f))
    for k in stale:
        print(f"FAIL   ruling {k} matches nothing any more — delete it")
    if faults or stale:
        print(f"STRUCTURE CLEARANCE FAIL: {len(faults)} thing(s) stand inside a building, "
              f"{len(stale)} stale ruling(s)")
        return 1
    print(f"structure clearance: no building, fence or yard prop stands inside a building in "
          f"{', '.join(SCENES)}, and no 1835 building stands on a plank walk line or in an alley "
          f"({len(ruled)} ruled overlap(s))")
    return 0


if __name__ == "__main__":
    sys.exit(main())
