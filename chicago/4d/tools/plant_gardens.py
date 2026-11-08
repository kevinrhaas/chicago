#!/usr/bin/env python3
"""plant_gardens.py — lay out and plant the kitchen gardens a scene draws (T-3407).

THE GARDEN. The commanding officer's garden south of the first Fort Dearborn
(`first_fort_outer_officers_garden`), on 14 August 1812. The owner, 2026-11-06, at stop 9 of
the Fort Dearborn jaunt: "you describe this awesome garden for 1812 but nothing is in the
garden". Its paling was built (T-2062); this writes what is inside it.

THE BEDS are Whistler's 1808 draught's, read off the pinned sheet (data/traces/
whistler_1808_fort_dearborn.json, sha256 there) in its own pixels: the garden's four ruled
sides are px x 752..1166, y 1514..1722, and DRAUGHT_PX below is every other ruled line
inside them, measured by the dark-pixel profile across each band (T-3407). They are carried
into the record's box (its footprint, at the garden's lettered '5o feete to the Inch') by the
box's own two ratios, so the beds move if the box does. The draught's bed corners are clipped;
so are these, by CLIP_PX.

THE CROPS are reconstructed except where Quaife names them ("melons and other small fruit
and vegetables"), from M'Mahon's calendar for the August kitchen garden and its distances
(data/sources/mmahon_1857_american_gardeners_calendar.json): musk-melons in hills six feet
every way, water-melons nine or ten, pumpkins and squashes ten, running beans on poles in
drills four or five feet asunder, garden Indian corn in drills six feet apart with hills two
and a half feet asunder. docs/LIBERTIES.md L-t3407-officers-garden.

WRITES data/gardens/<scene>.json, drawn by renderers/web/js/gardens.js. Local ENU metres of
data/datum.json. A plant is [e, n, yaw_deg, scale, variant].

    python3 tools/plant_gardens.py            write it
    python3 tools/plant_gardens.py --check    re-derive and fail on drift; also refuse a
                                              plant outside its bed or a bed outside the
                                              paling, and a bed that is not the draught's
    python3 tools/plant_gardens.py --self-test  the check refuses what it should
"""
from __future__ import annotations

import argparse
import json
import math
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "gardens"
TICKET = "T-3407"
LIBERTY = "L-t3407-officers-garden"

# ---------------------------------------------------------------- the draught's lines
#: The garden's ruled box on the sheet (data/traces/whistler_1808_fort_dearborn.json
#: § outside_the_stockade, part officers_garden), and every ruled line inside it, in sheet
#: px: x grows east, y grows SOUTH. Read at T-3407 from the dark-pixel profile of each band.
BOX_PX = (752.0, 1514.0, 1166.0, 1722.0)
DRAUGHT_PX = {
    "border_inner_y": 1553.5,                      # the north border's south line
    "walk_x": (948.5, 969.5),                      # the walk in from the gate, and on south
    "row1_y": (1565.5, 1625.5),                    # the north row of four beds
    "row2_y": (1648.5, 1709.5),                    # the south row
    "cols_x": ((765.0, 851.0), (864.0, 949.5), (969.5, 1055.5), (1066.5, 1151.5)),
    "corner_r": 10.0,                              # the quarter-rounds in the two south corners
}
#: How far each drawn bed's corner is clipped, in sheet px.
CLIP_PX = 6.0

# ---------------------------------------------------------------- the crops
CROPS = {
    "muskmelon": ("musk-melons", "attested",
                  "Quaife: in the commanding officer's gardens 'melons and other small fruit and vegetables were raised'. "
                  "Hills six feet every way (M'Mahon), the fruit ripening on the vine in mid-August."),
    "watermelon": ("water-melons", "attested",
                   "Melons are Quaife's. Water-melons in hills nine or ten feet apart (M'Mahon)."),
    "currant": ("red currant bushes", "attested",
                "Small fruit is Quaife's; which small fruit is ours. Currants were picked in July, so a few strings are left."),
    "gooseberry": ("gooseberry bushes", "attested", "Small fruit is Quaife's; which small fruit is ours."),
    "raspberry": ("raspberry canes", "attested", "Small fruit is Quaife's; which small fruit is ours. Last year's canes stand spent among this year's."),
    "strawberry": ("strawberries", "attested", "Small fruit is Quaife's; which small fruit is ours. In August only leaves and runners."),
    "cabbage": ("cabbages and savoys", "reconstructed", "M'Mahon's August work: plant the last savoys two feet every way; earth up the cabbages."),
    "corn": ("Indian corn", "reconstructed", "Garden Indian corn in drills six feet apart, two stalks to a hill every two and a half feet (M'Mahon), tasselled and silking in August."),
    "pole_bean": ("running beans on poles", "reconstructed", "Running kidney-beans in drills four or five feet asunder, on poles (M'Mahon), in leaf and pod."),
    "potato": ("potatoes", "reconstructed", "Earthed up in hills, the tops beginning to yellow."),
    "squash": ("squashes and pumpkins", "reconstructed", "Hills ten feet apart (M'Mahon), the fruit turning."),
    "cucumber": ("cucumbers", "reconstructed", "M'Mahon's August: melons and cucumbers 'in an advancing or fruiting state'."),
    "onion": ("onions", "reconstructed", "In drills; in August half their tops have fallen over, the sign they are ripe."),
    "beet": ("beets", "reconstructed", "In drills a foot apart."),
    "carrot": ("carrots", "reconstructed", "In drills a foot apart."),
    "parsnip": ("parsnips", "reconstructed", "In drills a foot apart."),
    "lettuce": ("lettuce and endive", "reconstructed", "M'Mahon's August: transplant the advancing lettuces; tie up the full-grown endive."),
    "asparagus": ("asparagus", "reconstructed", "In its summer fern, the cutting long over."),
    "herb": ("sage and thyme", "reconstructed", "M'Mahon's August: cut the herbs in flower to dry for winter."),
}
CROP_SOURCES = {"attested": ["quaife_1913", "mmahon_1857_american_gardeners_calendar"],
                "reconstructed": ["mmahon_1857_american_gardeners_calendar"]}

FT = 0.3048


def _read(p: Path) -> dict:
    return json.loads(p.read_text())


def garden_frame(record: dict) -> dict:
    """The garden's plan frame: origin (the footprint's (0, 0)) in local ENU, and its +u, +v
    axes. Rotation is clockwise (the structures' convention), 0 here."""
    datum = _read(ROOT / "data" / "datum.json")
    phase = record["phases"][0]
    pos = phase["position"]
    e = pos["utm_e"] - datum["origin_utm_e"]
    n = pos["utm_n"] - datum["origin_utm_n"]
    r = math.radians(pos.get("rotation_deg", 0.0))
    poly = phase["footprint"]["polygon"]
    w = max(p[0] for p in poly) - min(p[0] for p in poly)
    d = max(p[1] for p in poly) - min(p[1] for p in poly)
    return {"origin": [round(e, 3), round(n, 3)],
            "u": [round(math.cos(r), 6), round(-math.sin(r), 6)],
            "v": [round(math.sin(r), 6), round(math.cos(r), 6)],
            "size": [round(w, 3), round(d, 3)]}


def px_to_plan(size, x, y):
    """Sheet px to the garden's plan metres (u east from the west paling, v north from the south)."""
    x0, y0, x1, y1 = BOX_PX
    w, d = size
    return ((x - x0) / (x1 - x0) * w, (y1 - y) / (y1 - y0) * d)


def clipped_rect(size, x0, y0, x1, y1, clip=CLIP_PX, which=("nw", "ne", "se", "sw")):
    """A drawn bed (sheet px box) as a plan polygon, its named corners clipped."""
    pts = []
    for corner, (cx, cy), (ax, ay), (bx, by) in (
        ("nw", (x0, y0), (0, clip), (clip, 0)),
        ("ne", (x1, y0), (-clip, 0), (0, clip)),
        ("se", (x1, y1), (0, -clip), (-clip, 0)),
        ("sw", (x0, y1), (clip, 0), (0, -clip)),
    ):
        if corner in which:
            pts.append((cx + ax, cy + ay))
            pts.append((cx + bx, cy + by))
        else:
            pts.append((cx, cy))
    # px is y-down; walked nw->ne->se->sw that is clockwise on the sheet, so counter-
    # clockwise in plan (v up). Round to the centimetre.
    return [[round(u, 2), round(v, 2)] for u, v in (px_to_plan(size, x, y) for x, y in pts)]


def quarter_round(size, corner, r_px, steps=6):
    x0, y0, x1, y1 = BOX_PX
    cx, cy = (x0, y1) if corner == "sw" else (x1, y1)
    sx = 1 if corner == "sw" else -1
    pts = [(cx, cy)]
    for i in range(steps + 1):
        a = (math.pi / 2) * i / steps
        pts.append((cx + sx * r_px * math.cos(a), cy - r_px * math.sin(a)))
    if sx < 0:
        pts = [pts[0]] + pts[1:][::-1]
    plan = [px_to_plan(size, x, y) for x, y in pts]
    # keep it counter-clockwise in plan
    area = sum(plan[i][0] * plan[(i + 1) % len(plan)][1] - plan[(i + 1) % len(plan)][0] * plan[i][1] for i in range(len(plan)))
    if area < 0:
        plan = plan[::-1]
    return [[round(u, 2), round(v, 2)] for u, v in plan]


def beds(size) -> list[dict]:
    D = DRAUGHT_PX
    x0, y0, x1, y1 = BOX_PX
    out = []
    note = ("A bed Whistler's 1808 draught rules inside the garden, read off the sheet in its own pixels "
            "and carried into the record's box at the garden's lettered scale (tools/plant_gardens.py DRAUGHT_PX).")
    src = ["whistler_1808_fort_dearborn_draught"]

    def bed(id_, name, poly, crop, plan):
        out.append({"id": id_, "name": name, "crop": crop, "plan": plan, "grade": "inferred",
                    "sources": src, "note": note, "poly": poly})

    bed("border_w", "the north border, west of the walk",
        clipped_rect(size, x0, y0, D["walk_x"][0], D["border_inner_y"], which=("se", "sw")),
        "currant", "small_fruit_w")
    bed("border_e", "the north border, east of the walk",
        clipped_rect(size, D["walk_x"][1], y0, x1, D["border_inner_y"], which=("se", "sw")),
        "raspberry", "small_fruit_e")
    plans = [["cabbage", "corn", "pole_bean", "potato"], ["muskmelon", "watermelon", "squash", "roots"]]
    names = [["cabbages and savoys", "Indian corn", "running beans", "potatoes"],
             ["musk-melons", "water-melons", "squashes and cucumbers", "onions, beets, carrots, parsnips, lettuce"]]
    for r, ys in enumerate((D["row1_y"], D["row2_y"])):
        for c, xs in enumerate(D["cols_x"]):
            plan = plans[r][c]
            bed(f"bed_{'n' if r == 0 else 's'}{c + 1}",
                f"the {'north' if r == 0 else 'south'} row, bed {c + 1} from the west: {names[r][c]}",
                clipped_rect(size, xs[0], ys[0], xs[1], ys[1]),
                {"roots": "onion"}.get(plan, plan), plan)
    for corner in ("sw", "se"):
        bed(f"corner_{corner}", f"the quarter-round bed in the {corner.upper()} corner",
            quarter_round(size, corner, D["corner_r"]), "herb", "herb")
    return out


# ---------------------------------------------------------------- planting
def _bbox(poly):
    us = [p[0] for p in poly]
    vs = [p[1] for p in poly]
    return min(us), min(vs), max(us), max(vs)


def inside(poly, u, v) -> bool:
    hit = False
    j = len(poly) - 1
    for i in range(len(poly)):
        (xi, yi), (xj, yj) = poly[i], poly[j]
        if (yi > v) != (yj > v) and u < (xj - xi) * (v - yi) / (yj - yi) + xi:
            hit = not hit
        j = i
    return hit


def edge_dist(poly, u, v) -> float:
    best = 1e9
    j = len(poly) - 1
    for i in range(len(poly)):
        (ax, ay), (bx, by) = poly[j], poly[i]
        dx, dy = bx - ax, by - ay
        t = max(0.0, min(1.0, ((u - ax) * dx + (v - ay) * dy) / (dx * dx + dy * dy or 1)))
        best = min(best, math.hypot(u - ax - dx * t, v - ay - dy * t))
        j = i
    return best


def grid(poly, du, dv, inset, rng, jitter=0.06, stagger=False):
    u0, v0, u1, v1 = _bbox(poly)
    nu = max(1, int((u1 - u0 - 2 * inset) / du) + 1)
    nv = max(1, int((v1 - v0 - 2 * inset) / dv) + 1)
    su = (u1 - u0 - (nu - 1) * du) / 2
    sv = (v1 - v0 - (nv - 1) * dv) / 2
    for j in range(nv):
        for i in range(nu):
            u = u0 + su + i * du + (du / 2 if stagger and j % 2 else 0)
            v = v0 + sv + j * dv
            u += (rng.random() - 0.5) * 2 * jitter
            v += (rng.random() - 0.5) * 2 * jitter
            if inside(poly, u, v) and edge_dist(poly, u, v) >= inset * 0.8:
                yield u, v, j


def plant_bed(bed, rng):
    """[(kind, u, v, yaw, scale)] for one bed, by its plan."""
    poly, plan = bed["poly"], bed["plan"]
    out = []

    def put(kind, u, v, scale=(0.88, 1.12), yaw=None, skip=0.0):
        if rng.random() < skip:
            return
        out.append((kind, u, v, rng.uniform(0, 360) if yaw is None else yaw, rng.uniform(*scale)))

    u0, v0, u1, v1 = _bbox(poly)
    if plan == "small_fruit_w":
        # back row against the paling: currants and gooseberries alternate; then two
        # rows of strawberries along the walk side.
        for u, v, _ in grid([[u0, v1 - 1.6], [u1, v1 - 1.6], [u1, v1 - 0.2], [u0, v1 - 0.2]], 1.7, 1.0, 0.7, rng):
            put("currant" if int(u / 1.7) % 2 == 0 else "gooseberry", u, v1 - 0.95, (0.85, 1.1))
        for u, v, _ in grid([[u0, v1 - 3.6], [u1, v1 - 3.6], [u1, v1 - 2.2], [u0, v1 - 2.2]], 1.9, 1.0, 0.8, rng, stagger=True):
            put("gooseberry" if int(u / 1.9) % 3 else "currant", u, v1 - 2.9, (0.8, 1.05))
        for vv in (v0 + 0.9, v0 + 1.6, v0 + 2.3):
            u = u0 + 1.0
            while u < u1 - 1.0:
                if inside(poly, u, vv):
                    put("strawberry", u, vv, (0.9, 1.1), yaw=rng.uniform(-8, 8))
                u += 1.0
    elif plan == "small_fruit_e":
        for u, v, _ in grid([[u0, v1 - 2.6], [u1, v1 - 2.6], [u1, v1 - 0.3], [u0, v1 - 0.3]], 0.95, 0.9, 0.6, rng, jitter=0.12):
            put("raspberry", u, v)
        for u, v, _ in grid([[u0, v0 + 0.4], [u1, v0 + 0.4], [u1, v0 + 3.4], [u0, v0 + 3.4]], 0.85, 0.85, 0.7, rng, jitter=0.1):
            put("asparagus", u, v)
    elif plan == "cabbage":
        for u, v, _ in grid(poly, 0.7, 0.65, 0.45, rng, stagger=True):
            put("cabbage", u, v, (0.85, 1.15), skip=0.07)             # a few cut for the table
    elif plan == "corn":
        # drills six feet apart, hills two and a half feet asunder (M'Mahon)
        for u, v, _ in grid(poly, 2.5 * FT, 6 * FT, 0.6, rng, jitter=0.05):
            put("corn", u, v, (0.9, 1.08))
    elif plan == "pole_bean":
        # drills four or five feet asunder, a pole to each hill
        for u, v, _ in grid(poly, 3 * FT, 4.5 * FT, 0.6, rng, jitter=0.05):
            put("pole_bean", u, v, (0.9, 1.08))
    elif plan == "potato":
        for u, v, _ in grid(poly, 0.75, 0.9, 0.5, rng, jitter=0.07):
            put("potato", u, v, (0.85, 1.12))
    elif plan == "muskmelon":
        for u, v, _ in grid(poly, 6 * FT, 6 * FT, 0.9, rng, jitter=0.1):
            put("muskmelon", u, v, (0.9, 1.1))
    elif plan == "watermelon":
        for u, v, _ in grid(poly, 9.5 * FT, 9.5 * FT, 1.3, rng, jitter=0.1, stagger=True):
            put("watermelon", u, v, (1.15, 1.35))
    elif plan == "squash":
        mid = (u0 + u1) / 2
        west = [[u0, v0], [mid - 0.4, v0], [mid - 0.4, v1], [u0, v1]]
        east = [[mid + 0.4, v0], [u1, v0], [u1, v1], [mid + 0.4, v1]]
        for u, v, _ in grid(west, 10 * FT * 0.8, 10 * FT * 0.8, 1.4, rng, jitter=0.15, stagger=True):
            if inside(poly, u, v):
                put("squash", u, v, (0.95, 1.15))
        for u, v, _ in grid(east, 4 * FT, 4 * FT, 0.8, rng, jitter=0.1):
            if inside(poly, u, v):
                put("cucumber", u, v, (0.9, 1.1))
    elif plan == "roots":
        # drills a foot and a half apart, running east-west, in blocks by crop; a
        # drill is laid as one-metre lengths.
        order = ["onion"] * 5 + ["beet"] * 5 + ["carrot"] * 5 + ["parsnip"] * 4 + ["lettuce"] * 3
        v = v1 - 0.55
        k = 0
        while v > v0 + 0.45 and k < len(order):
            u = u0 + 1.0
            while u < u1 - 0.9:
                if inside(poly, u, v) and edge_dist(poly, u, v) > 0.45:
                    put(order[k], u, v, (0.92, 1.08), yaw=180.0 * rng.randrange(2) + rng.uniform(-3, 3))
                u += 1.0
            v -= 0.45
            k += 1
    elif plan == "herb":
        for u, v, _ in grid(poly, 0.7, 0.7, 0.3, rng, jitter=0.08):
            put("herb", u, v, (0.9, 1.2))
    return out


def build(scene: str = "1812") -> dict:
    record = _read(ROOT / "data" / "structures" / "first_fort_outer_officers_garden.json")
    fr = garden_frame(record)
    size = fr["size"]
    bl = beds(size)
    (oe, on), (ue, un), (ve, vn) = fr["origin"], fr["u"], fr["v"]
    plants: dict[str, list] = {}
    for b in bl:
        rng = random.Random(f"{TICKET}:{b['id']}")
        for kind, u, v, yaw, scale in plant_bed(b, rng):
            e = oe + ue * u + ve * v
            n = on + un * u + vn * v
            plants.setdefault(kind, []).append([round(e, 2), round(n, 2), round(yaw, 1), round(scale, 3),
                                                rng.randrange(3)])
    garden = {
        "id": "first_fort_outer_officers_garden",
        "structure_id": "first_fort_outer_officers_garden",
        "name": "The commanding officer's garden",
        "where": "South of the first Fort Dearborn, inside its paling",
        "frame": {"origin": fr["origin"], "u": fr["u"], "v": fr["v"]},
        "size_m": size,
        "walk_grade": "inferred",
        "paling_inset_m": 0.15,
        "beds": [{k: b[k] for k in ("id", "name", "crop", "grade", "sources", "note", "poly")} for b in bl],
        "plants": {k: plants[k] for k in sorted(plants)},
    }
    return {
        "_doc": ("The kitchen gardens this scene draws (T-3407): each garden's beds and walks, in its own plan "
                 "frame (u east from the west paling, v north from the south, metres; frame.origin is plan (0, 0) "
                 "in local ENU metres of data/datum.json), and what grows in them. GENERATED by "
                 "tools/plant_gardens.py from the garden's structure record and Whistler's 1808 draught -- do not "
                 "hand-edit; re-run the tool. plants: {kind: [[e, n, yaw_deg, scale, variant], ...]} in local ENU. "
                 "Drawn by renderers/web/js/gardens.js."),
        "scene": scene,
        "target_date": "1812-08-14",
        "ticket": TICKET,
        "generated_by": "tools/plant_gardens.py",
        "liberty": LIBERTY,
        "layout_note": ("The beds and walks are Whistler's 1808 draught's, measured off the pinned sheet and carried "
                        "into the garden's box at its lettered scale: inferred, since that scale is read and the "
                        "box itself is placed by rule."),
        "crops": {k: {"name": v[0], "grade": v[1], "sources": CROP_SOURCES[v[1]], "note": v[2]}
                  for k, v in CROPS.items()},
        "gardens": [garden],
    }


def dump(doc: dict) -> str:
    """Compact enough to ship: one plant per line, the rest indented."""
    text = json.dumps(doc, indent=1, ensure_ascii=False)
    # fold every plant's five numbers onto one line
    import re
    text = re.sub(r"\[\n\s+(-?[\d.]+),\n\s+(-?[\d.]+),\n\s+(-?[\d.]+),\n\s+(-?[\d.]+),\n\s+(\d+)\n\s+\]",
                  r"[\1, \2, \3, \4, \5]", text)
    text = re.sub(r"\[\n\s+(-?[\d.]+),\n\s+(-?[\d.]+)\n\s+\]", r"[\1, \2]", text)
    return text + "\n"


def problems(doc: dict) -> list[str]:
    out = []
    for g in doc["gardens"]:
        W, D = g["size_m"]
        (oe, on), (ue, un), (ve, vn) = g["frame"]["origin"], g["frame"]["u"], g["frame"]["v"]
        for b in g["beds"]:
            for u, v in b["poly"]:
                if not (-0.01 <= u <= W + 0.01 and -0.01 <= v <= D + 0.01):
                    out.append(f"{g['id']}: bed {b['id']} reaches outside the paling at ({u}, {v})")
        polys = [b["poly"] for b in g["beds"]]
        for kind, rows in g["plants"].items():
            if kind not in doc["crops"]:
                out.append(f"{g['id']}: plants an unknown crop {kind}")
            for e, n, *_ in rows:
                de, dn = e - oe, n - on
                u, v = de * ue + dn * un, de * ve + dn * vn
                if not any(inside(p, u, v) for p in polys):
                    out.append(f"{g['id']}: a {kind} at ({e}, {n}) stands outside every bed")
        # the walk in from the gate stays clear: nothing between the border beds
        if g["id"] != "first_fort_outer_officers_garden":
            continue
        x0, _, x1, _ = BOX_PX
        wu0, _ = px_to_plan(g["size_m"], DRAUGHT_PX["walk_x"][0], 0)
        wu1, _ = px_to_plan(g["size_m"], DRAUGHT_PX["walk_x"][1], 0)
        for kind, rows in g["plants"].items():
            for e, n, *_ in rows:
                de, dn = e - oe, n - on
                u = de * ue + dn * un
                if wu0 + 0.2 < u < wu1 - 0.2:
                    out.append(f"{g['id']}: a {kind} at ({e}, {n}) stands in the walk in from the gate")
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if not a.self_test:
        # T-3476: the 1835 town's dooryard gardens, written and checked beside 1812's
        import plant_dooryards_1835
        town = plant_dooryards_1835.build(grid, inside, edge_dist)
        rc = finish(town, OUT / "1835.json", a.check)
        if rc:
            return rc
    doc = build()
    return finish(doc, OUT / "1812.json", a.check, a.self_test)


def finish(doc: dict, path: Path, check: bool, self_test: bool = False) -> int:
    text = dump(doc)
    if self_test:
        bad = json.loads(text)
        g = bad["gardens"][0]
        g["plants"]["cabbage"][0][0] -= 40.0
        g["beds"][0]["poly"][0][1] += 50.0
        g["plants"].setdefault("tomato", []).append(g["plants"]["corn"][0])
        found = problems(bad)
        want = ["stands outside every bed", "reaches outside the paling", "unknown crop"]
        missing = [w for w in want if not any(w in f for f in found)]
        for f in found[:6]:
            print(f"   self-test | refused: {f}")
        if missing:
            print(f"plant_gardens self-test: FAIL — not refused: {missing}")
            return 1
        print("plant_gardens self-test: PASS (a plant off its bed, a bed past the paling and an unknown crop are refused)")
        return 0
    errs = problems(doc)
    if check:
        if not path.exists() or path.read_text() != text:
            errs.append(f"{path.relative_to(ROOT)} is not what tools/plant_gardens.py writes — re-run it")
        for e in errs:
            print(f"FAIL {e}")
        if errs:
            return 1
        n = sum(len(v) for g in doc["gardens"] for v in g["plants"].values())
        print(f"plant_gardens: OK — {doc['scene']}: {len(doc['gardens'])} garden(s), "
              f"{sum(len(g['beds']) for g in doc['gardens'])} beds, {n} plants, re-derived byte for byte")
        return 0
    if errs:
        for e in errs:
            print(f"FAIL {e}")
        return 1
    OUT.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    counts: dict[str, int] = {}
    for g in doc["gardens"]:
        for k, v in g["plants"].items():
            counts[k] = counts.get(k, 0) + len(v)
    print(f"wrote {path.relative_to(ROOT)} — {sum(counts.values())} plants: {counts}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
