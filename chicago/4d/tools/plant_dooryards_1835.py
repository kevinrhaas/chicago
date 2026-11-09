"""The 1835 town's dooryard gardens, planted (T-3476) — data/gardens/1835.json.

The owner, 2026-11-07: *"now that you have a knowledge of how to plant gardens, can you do a
sweep of 1812 and 1835 and improve all of the gardens? ... all of the gardens should be
unique, not necessarily wildly different crops but different sizes and layouts that are
sensible for the design of the property and the family"*.

Every garden is a run of `data/enclosures/town_dooryard_pickets.json`: its fence, size,
place, layout and beds are that record's (tools/generate_dooryard_pickets.py, laid out by
tools/dooryard_layouts.py), and renderers/web/js/yards.js lays its beds and walks on the
ground. This writes only what grows in the beds, planted the way tools/plant_gardens.py
plants the officer's garden of 1812, and at the scene's own date: 1 July, so the file says
`summer_stage: july` and renderers/web/js/gardens.js draws M'Mahon's early July
(SEASON_CROPS.july) — corn in blade, beans partway up their poles, vines running, the small
fruit ripe. Every crop here is reconstructed: no source names what any household in the
town grew. docs/LIBERTIES.md L-t3476-dooryard-gardens.

Called by tools/plant_gardens.py (which writes and checks both scenes).
"""
from __future__ import annotations

import json
import math
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RECORD = ROOT / "data" / "enclosures" / "town_dooryard_pickets.json"
TICKET = "T-3476"
LIBERTY = "L-t3476-dooryard-gardens"
FT = 0.3048
SOURCES = ["mmahon_1857_american_gardeners_calendar"]

# The kinds the town's beds grow, and the plans (bed kinds) the layouts name.
CROPS = {
    "potato": ("potatoes", "In hills two feet and a half apart, in flower at midsummer."),
    "cabbage": ("cabbages", "Set out in spring two feet apart, heading by July."),
    "corn": ("Indian corn", "In hills three feet each way, in blade at the beginning of July, not yet tasselled."),
    "pole_bean": ("running beans on poles", "A pole to each hill, the vines partway up them and in flower in July."),
    "squash": ("squashes and pumpkins", "In hills among the corn or by themselves, the runners going out in July."),
    "cucumber": ("cucumbers", "In hills four feet apart; M'Mahon's July has the first fit to pick."),
    "onion": ("onions", "In drills, in full top."),
    "beet": ("beets", "In drills a foot apart."),
    "carrot": ("carrots", "In drills a foot apart."),
    "parsnip": ("parsnips", "In drills a foot apart."),
    "lettuce": ("lettuce", "Sown in succession in drills."),
    "herb": ("pot herbs: sage, thyme, parsley", "A bed of pot herbs by the gate."),
    "currant": ("currant bushes", "Ripe in early July."),
    "gooseberry": ("gooseberry bushes", "Ripening in early July."),
    "raspberry": ("raspberry canes", "In fruit at the beginning of July."),
    "strawberry": ("strawberries", "The fruit done by July; in leaf and runner."),
}
PLANS = {
    "potato": ("potatoes", "potato"),
    "cabbage": ("cabbages", "cabbage"),
    "corn": ("Indian corn", "corn"),
    "field_corn": ("corn in hills, with squash among it", "corn"),
    "pole_bean": ("beans on poles", "pole_bean"),
    "vines": ("cucumbers and squashes", "cucumber"),
    "roots": ("onions, beets, carrots and parsnips in drills", "onion"),
    "onion_salad": ("onions and lettuce", "onion"),
    "herb": ("pot herbs", "herb"),
    "bushes": ("currants and gooseberries under the fence", "currant"),
    "raspberry": ("raspberries under the fence", "raspberry"),
    "strawberry": ("strawberries", "strawberry"),
}


def _bbox(poly):
    us = [p[0] for p in poly]
    vs = [p[1] for p in poly]
    return min(us), min(vs), max(us), max(vs)


def plant_bed(plan, poly, rng, grid, inside, edge_dist):
    """[(kind, u, v, yaw_local_deg, scale)] for one bed of the town, by its plan."""
    out = []
    u0, v0, u1, v1 = _bbox(poly)
    along_u = (u1 - u0) >= (v1 - v0)

    def put(kind, u, v, scale=(0.88, 1.12), yaw=None, skip=0.0):
        if rng.random() < skip:
            return
        out.append((kind, u, v, rng.uniform(0, 360) if yaw is None else yaw, rng.uniform(*scale)))

    def drills(order, pitch=0.45, step=1.0, margin=0.35):
        """Drills down the bed's long side, one metre of row to an instance, by crop."""
        k = 0
        if along_u:
            v = v1 - margin
            while v > v0 + margin * 0.9 and order:
                u = u0 + 0.6
                while u < u1 - 0.5:
                    if inside(poly, u, v) and edge_dist(poly, u, v) > 0.3:
                        put(order[k % len(order)], u, v, (0.92, 1.08), yaw=180.0 * rng.randrange(2) + rng.uniform(-3, 3))
                    u += step
                v -= pitch
                k += 1
        else:
            u = u0 + margin
            while u < u1 - margin * 0.9 and order:
                v = v0 + 0.6
                while v < v1 - 0.5:
                    if inside(poly, u, v) and edge_dist(poly, u, v) > 0.3:
                        put(order[k % len(order)], u, v, (0.92, 1.08), yaw=90.0 + 180.0 * rng.randrange(2) + rng.uniform(-3, 3))
                    v += step
                u += pitch
                k += 1

    def row_of(kinds, spacing):
        """One row of bushes down the middle of a border bed."""
        if along_u:
            v = (v0 + v1) / 2
            u = u0 + spacing / 2
            i = 0
            while u < u1 - spacing / 3:
                put(kinds[i % len(kinds)], u + rng.uniform(-0.1, 0.1), v + rng.uniform(-0.1, 0.1), (0.8, 1.1))
                u += spacing
                i += 1
        else:
            u = (u0 + u1) / 2
            v = v0 + spacing / 2
            i = 0
            while v < v1 - spacing / 3:
                put(kinds[i % len(kinds)], u + rng.uniform(-0.1, 0.1), v + rng.uniform(-0.1, 0.1), (0.8, 1.1))
                v += spacing
                i += 1

    if plan == "potato":
        for u, v, _ in grid(poly, 0.76, 0.9, 0.35, rng, jitter=0.07):
            put("potato", u, v, (0.85, 1.12))
    elif plan == "cabbage":
        for u, v, _ in grid(poly, 0.65, 0.62, 0.32, rng, stagger=True):
            put("cabbage", u, v, (0.85, 1.15), skip=0.05)
    elif plan == "corn":
        for u, v, _ in grid(poly, 3 * FT, 3 * FT, 0.4, rng, jitter=0.06):
            put("corn", u, v, (0.9, 1.08))
    elif plan == "field_corn":
        # hills three and a half feet each way, and a squash hill in about one in nine
        for u, v, _ in grid(poly, 3.5 * FT, 3.5 * FT, 0.45, rng, jitter=0.1):
            if rng.random() < 0.11:
                put("squash", u, v, (0.9, 1.1))
            else:
                put("corn", u, v, (0.88, 1.08))
    elif plan == "pole_bean":
        for u, v, _ in grid(poly, 3 * FT, 4 * FT, 0.4, rng, jitter=0.05):
            put("pole_bean", u, v, (0.9, 1.08))
    elif plan == "vines":
        for u, v, _ in grid(poly, 4 * FT, 4 * FT, 0.5, rng, jitter=0.1, stagger=True):
            put("cucumber" if rng.random() < 0.6 else "squash", u, v, (0.9, 1.1))
    elif plan == "roots":
        order = ["onion", "onion", "beet", "beet", "carrot", "carrot", "parsnip"]
        rng.shuffle(order)
        drills(order)
    elif plan == "onion_salad":
        drills(["onion", "lettuce", "onion", "lettuce", "lettuce"])
    elif plan == "herb":
        for u, v, _ in grid(poly, 0.6, 0.6, 0.28, rng, jitter=0.08):
            put("herb", u, v, (0.9, 1.2))
    elif plan == "bushes":
        row_of(["currant", "gooseberry"] if rng.random() < 0.5 else ["currant", "currant", "gooseberry"], 1.5)
    elif plan == "raspberry":
        for u, v, _ in grid(poly, 0.8, 0.8, 0.35, rng, jitter=0.12):
            put("raspberry", u, v)
    elif plan == "strawberry":
        for u, v, _ in grid(poly, 0.5, 0.6, 0.28, rng, jitter=0.05):
            put("strawberry", u, v, (0.9, 1.1))
    else:
        raise ValueError(f"no plan {plan!r}")
    return out


def build(grid, inside, edge_dist) -> dict:
    rec = json.loads(RECORD.read_text())
    gardens = []
    for run in rec["runs"]:
        gd = run.get("garden")
        if not gd:
            continue
        (oe, on), (ue, un), (ve, vn) = gd["frame"]["origin"], gd["frame"]["u"], gd["frame"]["v"]
        theta = math.degrees(math.atan2(un, ue))

        house = run["belongs_to"][0]["structures"][0] if run.get("belongs_to") else None
        beds, plants = [], {}
        for i, b in enumerate(gd["beds"]):
            plan, poly = b["plan"], b["poly"]
            name, crop = PLANS[plan]
            bid = f"bed{i + 1}"
            beds.append({"id": bid, "name": name, "crop": crop, "grade": "reconstructed", "sources": [],
                         "note": (f"Laid out '{gd['style']}' by tools/dooryard_layouts.py for this house "
                                  f"(T-3476); the bed and what grows in it are invented."),
                         "poly": poly})
            rng = random.Random(f"{TICKET}:{run['id']}:{bid}")
            for kind, u, v, yaw, scale in plant_bed(plan, poly, rng, grid, inside, edge_dist):
                e = oe + ue * u + ve * v
                n = on + un * u + vn * v
                plants.setdefault(kind, []).append([round(e, 2), round(n, 2), round((yaw + theta) % 360, 1),
                                                    round(scale, 3), rng.randrange(3)])
        gardens.append({
            "id": run["id"],
            "structure_id": house,
            "name": "A dooryard garden",
            "where": f"Behind the house on {run['id'].replace('blk_', '').replace('_lot', ', lot ').replace('_', ' and ', 1)}",
            "frame": gd["frame"],
            "size_m": gd["size_m"],
            "ground": "beds",
            "walk_grade": "reconstructed",
            "paling_inset_m": 0.3,
            "beds": beds,
            "plants": {k: plants[k] for k in sorted(plants)},
        })
    return {
        "_doc": ("The 1835 town's dooryard gardens (T-3476): what grows in the beds of each run of "
                 "data/enclosures/town_dooryard_pickets.json, whose fence, size, layout and beds are that "
                 "record's; yards.js lays the beds and walks, this file only plants them. GENERATED by "
                 "tools/plant_gardens.py (tools/plant_dooryards_1835.py) -- do not hand-edit; re-run the tool. "
                 "Beds are in each garden's frame (u across, v back from the house, metres); plants are "
                 "[e, n, yaw_deg, scale, variant] in local ENU. Drawn by renderers/web/js/gardens.js."),
        "scene": "1835",
        "target_date": "1835-07-01",
        "summer_stage": "july",
        # the plants are drawn out to this distance and no farther (gardens.js deal): a town
        # garden is behind its fence and among houses, and ninety of them reach a kilometre
        "reach_m": 160,
        "ticket": TICKET,
        "generated_by": "tools/plant_gardens.py",
        "liberty": LIBERTY,
        "layout_note": ("Each garden's size, place, layout and fence follow its house's class, read off a hash "
                        "of its lot (tools/generate_dooryard_pickets.py); none is attested."),
        "crops": {**{k: {"name": v[0], "grade": "reconstructed", "sources": SOURCES, "note": v[1]}
                     for k, v in CROPS.items()}},
        "gardens": gardens,
    }
