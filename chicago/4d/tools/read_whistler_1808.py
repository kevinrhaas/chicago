#!/usr/bin/env python3
"""read_whistler_1808.py — hold the reading of Whistler's 1808 draught of the FIRST fort.

T-2048 (piece 1 of 3 of T-0469). `data/traces/whistler_1808_fort_dearborn.json` reads
Captain John Whistler's draught of Fort Dearborn, dated in its parade 25 January 1808,
off the plate Quaife printed facing p. 164 (1913). It is the only plan of the fort
burned on 16 August 1812, and the only sheet in this dataset that states its own scale:
"The measurement of the Garrison including the Block Houses And Barrick are laid down
at twenty feet to the Inch". A reproduction does not keep the inch, so the scale is
MEASURED from the drafter's one dimension on the garrison: the flagstaff, lettered
"75 feete" along its length, drawn laid down from its foot at the centre of the parade.

    python3 tools/read_whistler_1808.py [--check]     # offline; run by check.sh
    python3 tools/read_whistler_1808.py --remeasure   # fetches the sheet (network)

`--check` holds what can be held without the raster, which the repository does not
commit (data/traces/README.md):
  * the scale is the staff's arithmetic (length / 75 ft), not a typed number;
  * every feet figure in the file is what its pixel box gives at that scale,
    so a hand-edited foot is refused;
  * the index is complete: all 34 numbers, each located, not located (with why),
    sheet-only (drawn, but where the sheet says it is not to scale), or omitted by
    the drafter. 33 and 34 MUST be the last, because the index says so;
  * the cross-checks the file says HOLD still hold on its own numbers;
  * (T-2049) the first fort's structure records are built FROM this reading: each
    `data/structures/first_fort_dearborn_*.json` names its register part, carries the
    part's measured plan dimensions (to 0.02 m) and its fort-frame box in its
    `symbolic_location`, and stands 1803-08-17 to 1812-08-16 — a range no committed
    scene date falls inside, so no scene draws the first fort beside the second one;
  * (T-2050) the fort is SEATED with one origin and one bearing: each record's utm point
    and rotation are what SEAT_LOCAL, SEAT_BEARING_DEG and its FACING give its box, and
    the two forts cannot resolve together — no second-fort phase opens inside the first
    fort's range, every scene resolves all fourteen first-fort records or none, and the
    1812 scene resolves all fourteen;
  * (T-2062) the factory, the agent's house, the stables and the two gardens OUTSIDE
    the stockade (`first_fort_outer_*`) stand where the register's `outside_the_stockade`
    rule puts them: the sheet's arrangement about the main gate, opened out by the
    drafter's own eighteen perches or the garden's lettered fifty feet to the inch;
  * (T-2507) the interpreter's house, armourer's shop, merchant's shop and bake house
    (nos. 19-22) stand by the same rule. A part drawn turned off the sheet's axes carries
    `turn_deg` (clockwise, about its box's centre) and is seated turned. A stated figure
    whose expansion does not govern (`governs: false`) is kept and computed, never used.
    And every outside record stands DRY: no footprint corner on the committed 1812 water.
  * (T-2513) Coursoll's worm-fenced field north of the river stands by the same rule. A
    field is GROUND, not a pictorial elevation, and carries no lettered scale, so its
    `scale_ft_per_in` is the word "expansion": its drawn outline is opened out by the
    same figure as its place, which is what the two gardens already get (their lettered
    fifty feet IS their expansion), and keeps the sheet's arrangement of fence and house.
  * (T-2508) the wharf (27) and the covered way (33) are seated on the committed 1812
    river by their index rows' `seat`, not by the outside rule: the wharf where the
    drafter's red '122 feet to River' about the outer row's north-west corner first meets
    the water west of the angle, laid along the bank with its deck at the ground of its
    heel; the covered way from the outer row's north-east corner along the frame's north
    to the water, in runs one joint apart, none on more than `max_fall_m` of fall, the
    last reaching the river.
  * (T-2504) the houses across the river WEST of Kinzie's (no. 31) stand where the
    register's `north_bank` rule puts them: the sheet's arrangement opened out about the
    Kinzie house AS BUILT (no. 30's drawn centre on kinzie_house_1812's footprint centre)
    by the drafter's '52 yards in length' on the picket between two of them. Each built
    one stands dry, covers both 1812 scene dates, closes before 1835-07-01, and overlaps
    neither its neighbours nor the Kinzie house.
  * (T-2513) Coursoll's worm-fenced field, west of them, stands by the same north-bank
    rule. A field is GROUND, not a pictorial building, and carries no lettered scale, so
    its `scale_ft_per_in` is the word "expansion": its drawn outline is opened out by the
    same figure as its place, which is what the two gardens outside the stockade already
    get (their lettered fifty feet IS their expansion). It is held to the same checks as
    the houses, so it may not stand on the house at its corner.

`--remeasure` fetches the working copy, refuses it if its sha256 has moved, and finds
the staff's two ends again: the longest near-continuous dark run in columns 994-1007,
bridging gaps of up to 12 px where the faint line crosses the north range's ink. It
must land on the file's own `staff_px`.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TRACE = ROOT / "data" / "traces" / "whistler_1808_fort_dearborn.json"
SOURCES = ROOT / "data" / "sources"
STATUSES = {"located", "not_located", "sheet_only", "omitted_by_drafter"}
TOL_FT = 0.05
STAFF_COLS = range(994, 1008)
DARK = 140
MAX_GAP = 12


def feet(box, s, ox, oy):
    x0, y0, x1, y1 = box
    r = lambda v: round(v, 1)
    return {"e_ft": [r((x0 - ox) / s), r((x1 - ox) / s)],
            "n_ft": [r((oy - y1) / s), r((oy - y0) / s)],
            "size_ft": [r((x1 - x0) / s), r((y1 - y0) / s)]}


def same(a, b):
    return all(abs(p - q) <= TOL_FT for k in ("e_ft", "n_ft", "size_ft")
               for p, q in zip(a[k], b[k]))


def check(doc: dict) -> list[str]:
    errs: list[str] = []
    src = SOURCES / f"{doc['source_id']}.json"
    if not src.exists():
        return [f"source {doc['source_id']} has no record in data/sources/"]
    if doc["sheet"]["sha256"] not in json.loads(src.read_text())["locator"]:
        errs.append("the sheet's sha256 is not the one its source record pins")

    sc = doc["scale"]
    top, foot = sc["staff_px"]["top"], sc["staff_px"]["foot"]
    length = foot[1] - top[1] + 1
    if sc["staff_px"]["length"] != length:
        errs.append(f"staff length {sc['staff_px']['length']} px is not foot-top+1 = {length}")
    s = round(length / sc["staff_ft"], 4)
    if sc["px_per_ft"] != s:
        errs.append(f"px_per_ft {sc['px_per_ft']} is not {length} px / {sc['staff_ft']} ft = {s}")
    ox, oy = foot
    w, h = doc["sheet"]["size_px"]

    boxes: dict[str, list[int]] = {}

    def hold(label, node):
        box = node["sheet_px"]
        if not (0 <= box[0] < box[2] <= w and 0 <= box[1] < box[3] <= h):
            errs.append(f"{label}: box {box} is not a box on a {w} x {h} sheet")
            return
        boxes[label] = box
        if "fort_ft" in node and not same(node["fort_ft"], feet(box, s, ox, oy)):
            errs.append(f"{label}: fort_ft {node['fort_ft']} is not what {box} gives "
                        f"({feet(box, s, ox, oy)})")

    hold("parade", doc["parade"])
    numbers = []
    for row in doc["index"]:
        n, st = row["no"], row["status"]
        numbers.append(n)
        if st not in STATUSES:
            errs.append(f"index {n}: status {st!r} is not one of {sorted(STATUSES)}")
        if st == "located":
            if not row.get("parts") and not row.get("lines"):
                errs.append(f"index {n}: located, but carries neither parts nor lines")
            for p in row.get("parts", []):
                if "fort_ft" not in p:
                    errs.append(f"index {n} {p['label']}: inside the garrison, so it must carry feet")
                hold(p["label"], p)
        elif not row.get("why"):
            errs.append(f"index {n}: {st} must say why")
    if numbers != list(range(1, 35)):
        errs.append(f"the index is not the drafter's 1-34 in order: {numbers}")
    for n in (33, 34):
        row = next((r for r in doc["index"] if r["no"] == n), None)
        if row and row["status"] != "omitted_by_drafter":
            errs.append(f"index {n}: the index says it is 'Omited in their places', "
                        f"so it cannot be {row['status']}")

    # The cross-checks the file says hold, re-taken on its own numbers.
    claims = {c["check"]: c["result"] for c in doc["cross_checks"]}
    px, py = doc["parade"]["sheet_px"][0::2], doc["parade"]["sheet_px"][1::2]
    off = max(abs(sum(px) / 2 - ox), abs(sum(py) / 2 - oy)) / s
    if claims.get("the staff's foot is the parade's centre") == "holds" and off >= 1.0:
        errs.append(f"the staff's foot is {off:.2f} ft off the parade's centre; the file says it holds")
    nw, se = boxes.get("north-west blockhouse"), boxes.get("south-east blockhouse")
    if nw and se and claims.get("the two blockhouses agree") == "holds":
        d = max(abs((nw[2] - nw[0]) - (se[2] - se[0])), abs((nw[3] - nw[1]) - (se[3] - se[1]))) / s
        if d > 2.0:
            errs.append(f"the blockhouses differ by {d:.1f} ft; the file says they agree within 2")
    inner = {r["no"]: r for r in doc["index"]}[5]["lines"]
    iw = (inner["east"]["x_px"] - inner["west"]["x_px"]) / s
    ih = (inner["south"]["y_px"] - inner["north"]["y_px"]) / s
    if claims.get("the inner row encloses a square") == "holds" and abs(iw - ih) / max(iw, ih) > 0.02:
        errs.append(f"the inner row is {iw:.1f} x {ih:.1f} ft, not square within 2 percent")
    return errs


#: T-2049. Each first-fort record, the register part it is built from, and how its plan
#: reads the part: "ew" — width east-west, depth north-south; "ns" — width along a range
#: that runs north-south; "front" — an ELEVATION, so only the width is measured.
RECORDS = {
    "first_fort_dearborn_blockhouse_nw": ("north-west blockhouse", "ew"),
    "first_fort_dearborn_blockhouse_se": ("south-east blockhouse", "ew"),
    "first_fort_dearborn_commanding_officers_barracks": ("east range", "ns"),
    "first_fort_dearborn_officers_barracks": ("west range", "ns"),
    "first_fort_dearborn_soldiers_barracks_sw": ("south range, west of the gate", "ew"),
    "first_fort_dearborn_soldiers_barracks_se": ("south range, east of the gate", "ew"),
    "first_fort_dearborn_north_range": ("north range", "ew"),
    "first_fort_dearborn_magazine": ("magazine", "front"),
    "first_fort_dearborn_small_house_ne": ("small house, north-east", "front"),
    "first_fort_dearborn_small_house_sw": ("small house, south-west", "ew"),
    "first_fort_dearborn_parade": ("parade", "ew"),
    "first_fort_dearborn_flagstaff": ("flagstaff", None),
    "first_fort_dearborn_pickets_inner": (5, "ew"),
    "first_fort_dearborn_pickets_outer": (6, "ew"),
}
FIRST_FORT = ("1803-08-17", "1812-08-16")
FT_M = 0.3048
TOL_M = 0.02

#: T-2050. The seat: ONE origin and ONE bearing for the whole frame, so no record can be
#: moved against another. The staff's foot stands on the fort site at local E +1152,
#: N +221 (the Wright 1834 reading the second fort also hangs on: both forts stood on
#: "the same ground"), and the frame's north is grid north (the register's own inference
#: that the sheet's right is east). Each record's origin is its box's corner after its
#: FACING — degrees clockwise from the frame's north that its front faces, from what the
#: record says it faces — so a footprint anchored at its own (0, 0) lands on its box.
SEAT_LOCAL = (1152.0, 221.0)
SEAT_BEARING_DEG = 0.0
FACING = {
    "first_fort_dearborn_commanding_officers_barracks": 270,   # west, onto the parade
    "first_fort_dearborn_officers_barracks": 90,               # east, onto the parade
    "first_fort_dearborn_north_range": 180,                    # south, onto the parade
    "first_fort_dearborn_magazine": 180,                       # its arched front, south
    "first_fort_dearborn_small_house_ne": 180,                 # its front, south
}
#: which box edges (e index, n index into [e0, e1, n0, n1]) a facing anchors at
CORNER = {0: (0, 2), 90: (0, 3), 180: (1, 3), 270: (1, 2)}
SEAT_TOL_M = 0.01
BOX = re.compile(r"E ([+-][\d.]+)\.\.([+-][\d.]+) ft, N ([+-][\d.]+)\.\.([+-][\d.]+) ft")


def seat(box: list[float], facing: int, datum: dict,
         turn: float = 0.0) -> tuple[float, float, float]:
    """The UTM point and facade bearing the seat gives a record with this frame box.

    `turn` (T-2507) is a drawing's own turn off the sheet's axes, degrees clockwise: the
    box is the plan in its own axes about its centre, and the corner is turned with it."""
    ce, cn = box[CORNER[facing][0]] * FT_M, box[CORNER[facing][1]] * FT_M
    if turn:
        mx, my = (box[0] + box[1]) / 2 * FT_M, (box[2] + box[3]) / 2 * FT_M
        de, dn, t = ce - mx, cn - my, math.radians(turn)
        ce = mx + de * math.cos(t) + dn * math.sin(t)
        cn = my - de * math.sin(t) + dn * math.cos(t)
    th = math.radians(SEAT_BEARING_DEG)
    e = SEAT_LOCAL[0] + ce * math.cos(th) + cn * math.sin(th)
    n = SEAT_LOCAL[1] - ce * math.sin(th) + cn * math.cos(th)
    return (datum["origin_utm_e"] + e, datum["origin_utm_n"] + n,
            (SEAT_BEARING_DEG + facing + turn) % 360)


def two_forts() -> list[str]:
    """T-2050: the first fort and the second can never resolve into one scene.

    Held twice. Over ALL dates: every phase of every second-fort record opens after the
    first fort's range closes, so no date a scene could take resolves both. And over the
    committed scenes: each resolves all fourteen first-fort records or none of them, and
    the 1812 scene resolves all fourteen and no second-fort record.
    """
    errs: list[str] = []
    sdir = ROOT / "data" / "structures"
    first = {p.stem: json.loads(p.read_text()) for p in sdir.glob("first_fort_dearborn_*.json")}
    second = {p.stem: json.loads(p.read_text()) for p in sdir.glob("fort_dearborn_*.json")}
    for sid, st in sorted(second.items()):
        for ph in st.get("phases", []):
            frm = ph.get("documented_range", {}).get("from", "")
            if frm <= FIRST_FORT[1]:
                errs.append(f"{sid}/{ph.get('id')}: opens {frm}, inside the first fort's range "
                            f"(to {FIRST_FORT[1]}) — a date could draw both forts")

    def resolves(st: dict, d: str) -> bool:
        return any(ph["documented_range"]["from"] <= d <= ph["documented_range"]["to"]
                   for ph in st.get("phases", []) if "documented_range" in ph)

    for p in sorted((ROOT / "data" / "scenes").glob("*.json")):
        d = json.loads(p.read_text())["target_date"]
        f = sorted(s for s, st in first.items() if resolves(st, d))
        s2 = sorted(s for s, st in second.items() if resolves(st, d))
        if f and s2:
            errs.append(f"scene {p.stem} ({d}) resolves both forts: {f[0]} and {s2[0]}")
        if f and len(f) != len(first):
            errs.append(f"scene {p.stem} ({d}) resolves {len(f)} of the first fort's {len(first)} records")
        if p.stem == "1812" and len(f) != len(first):
            errs.append(f"the 1812 scene ({d}) does not resolve the first fort")
    return errs


def records(doc: dict) -> list[str]:
    """The first fort's structure records against the reading they are built from."""
    errs: list[str] = []
    s = doc["scale"]["px_per_ft"]
    ox, oy = doc["scale"]["staff_px"]["foot"]
    parts = {p["label"]: p["fort_ft"] for r in doc["index"] for p in r.get("parts", [])}
    parts["parade"] = doc["parade"]["fort_ft"]
    north = (parts["north range, west room"], parts["north range, east room"])
    parts["north range"] = {
        "e_ft": [north[0]["e_ft"][0], north[1]["e_ft"][1]], "n_ft": north[1]["n_ft"],
        "size_ft": [round(north[1]["e_ft"][1] - north[0]["e_ft"][0], 1), north[1]["size_ft"][1]]}
    for r in doc["index"]:
        if "lines" in r:
            L = r["lines"]
            x0, x1, y0, y1 = L["west"]["x_px"], L["east"]["x_px"], L["north"]["y_px"], L["south"]["y_px"]
            parts[r["no"]] = feet([x0, y0, x1, y1], s, ox, oy)
    have = {p.stem for p in (ROOT / "data" / "structures").glob("first_fort_dearborn_*.json")}
    for sid in sorted(have ^ set(RECORDS)):
        errs.append(f"{sid}: {'a first-fort record this reading does not map' if sid in have else 'mapped here, but no record'}")
    scenes = [json.loads(p.read_text())["target_date"] for p in (ROOT / "data" / "scenes").glob("*.json")]
    datum = json.loads((ROOT / "data" / "datum.json").read_text())
    for sid, (label, axis) in RECORDS.items():
        f = ROOT / "data" / "structures" / f"{sid}.json"
        if not f.exists():
            continue
        st = json.loads(f.read_text())
        if len(st["phases"]) != 1:
            errs.append(f"{sid}: carries {len(st['phases'])} phases; the first fort has one")
            continue
        ph = st["phases"][0]
        rng = (ph["documented_range"]["from"], ph["documented_range"]["to"])
        if rng != FIRST_FORT:
            errs.append(f"{sid}: stands {rng[0]}..{rng[1]}, not the first fort's {FIRST_FORT[0]}..{FIRST_FORT[1]}")
        both = [d for d in scenes if rng[0] <= d <= rng[1]]
        if both and not (ROOT / "data" / "scenes" / "1812.json").exists():
            errs.append(f"{sid}: scene date {both[0]} resolves it, and no 1812 scene exists to own it")
        pos = ph["position"]
        m = BOX.search(pos.get("symbolic_location", ""))
        if not m:
            errs.append(f"{sid}: symbolic_location carries no fort-frame box to seat")
        elif pos.get("utm_e") is None or pos.get("utm_n") is None:
            errs.append(f"{sid}: not seated — the 1812 scene draws it, so it needs the seat's utm point")
        else:
            e, n, rot = seat([float(x) for x in m.groups()], FACING.get(sid, 0), datum)
            off = math.hypot(pos["utm_e"] - e, pos["utm_n"] - n)
            if off > SEAT_TOL_M or float(pos.get("rotation_deg") or 0.0) != rot:
                errs.append(f"{sid}: stands at {pos['utm_e']}, {pos['utm_n']} turned "
                            f"{pos.get('rotation_deg')}, not where the seat puts its box "
                            f"({e:.2f}, {n:.2f} turned {rot}): {off:.2f} m off")
        if axis is None:
            continue
        part = parts[label]
        e_ft, n_ft = part["e_ft"], part["n_ft"]
        loc = ph["position"].get("symbolic_location", "")
        want_e = f"E {e_ft[0]:+.1f}..{e_ft[1]:+.1f} ft"
        if want_e not in loc:
            errs.append(f"{sid}: symbolic_location does not carry the register's {want_e}")
        if axis != "front" and f"N {n_ft[0]:+.1f}..{n_ft[1]:+.1f} ft" not in loc:
            errs.append(f"{sid}: symbolic_location does not carry the register's N box")
        poly = ph["footprint"]["polygon"]
        w = max(p[0] for p in poly) - min(p[0] for p in poly)
        d = max(p[1] for p in poly) - min(p[1] for p in poly)
        ew, ns = (part["size_ft"][0] * FT_M, part["size_ft"][1] * FT_M)
        want = {"ew": (ew, ns), "ns": (ns, ew), "front": (ew, None)}[axis]
        if abs(w - want[0]) > TOL_M or (want[1] is not None and abs(d - want[1]) > TOL_M):
            errs.append(f"{sid}: footprint {w:.2f} x {d:.2f} m is not the register's "
                        f"{label!r} at {want[0]:.2f}" + (f" x {want[1]:.2f} m" if want[1] else " m wide"))
    return errs


#: T-2062. Outside the stockade the drafter's distances are "not laid down by a scale",
#: so these records are NOT built from the garrison frame's measured boxes. Each is the
#: sheet's arrangement opened out about the main gate by a figure he wrote himself —
#: `outside_the_stockade.the_rule` in the register — and stands for as long as the post.
OUTSIDE_PREFIX = "first_fort_outer_"
PERCH_FT = 16.5
WATER_1812 = ROOT / "data" / "terrain" / "epochs" / "e1830_natural" / "river.geojson"


def outside_boxes(doc: dict) -> dict[str, dict]:
    """Each outside record's fort-frame box (ft), footprint (m) and facing, from the register."""
    out = doc["outside_the_stockade"]
    s = doc["scale"]["px_per_ft"]
    ox, oy = doc["scale"]["staff_px"]["foot"]
    gx, gy = out["gate_px"]
    parts = {p["part"]: p for p in out["parts"]}

    def centre(box):
        return ((box[0] + box[2]) / 2, (box[1] + box[3]) / 2)

    exp = {}
    for key, e in out["expansions"].items():
        if "stated_ft" in e:
            cx, cy = centre(parts[e["measured_from_part"]]["sheet_px"])
            exp[key] = e["stated_ft"] / (math.hypot(cx - gx, cy - gy) / s)
        else:
            exp[key] = e["scale_ft_per_in"] / (out["inch_px"] / s)
    boxes = {}
    for p in out["parts"]:
        x0, y0, x1, y1 = p["sheet_px"]
        cx, cy = centre(p["sheet_px"])
        k = exp[p["expansion"]]
        ce = (gx - ox) / s + (cx - gx) / s * k
        cn = (oy - gy) / s - (cy - gy) / s * k
        # a ground part with no lettered scale is opened out with its place (T-2513)
        ft_per_px = (k / s if p["scale_ft_per_in"] == "expansion"
                     else p["scale_ft_per_in"] / out["inch_px"])
        w, h = (x1 - x0) * ft_per_px, (y1 - y0) * ft_per_px
        box = [round(ce - w / 2, 1), round(ce + w / 2, 1), round(cn - h / 2, 1), round(cn + h / 2, 1)]
        ew, ns = (box[1] - box[0]) * FT_M, (box[3] - box[2]) * FT_M
        boxes[p["record"]] = {"box": box, "facing": p["facing"], "expansion": round(k, 3),
                              "turn": float(p.get("turn_deg", 0.0)),
                              "size_m": (ns, ew) if p["facing"] in (90, 270) else (ew, ns)}
    return boxes


def _inside(pt, ring) -> bool:
    x, y = pt
    hit = False
    for (x1, y1), (x2, y2) in zip(ring, ring[1:] + ring[:1]):
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            hit = not hit
    return hit


def wet_corners(pos: dict, poly: list) -> list[tuple[float, float]]:
    """T-2507: the footprint corners that stand on the committed 1812 water (river.geojson)."""
    g = json.loads(WATER_1812.read_text())
    rings = [f["geometry"]["coordinates"] for f in g["features"]
             if f["properties"].get("kind") == "water" and f["geometry"]["type"] == "Polygon"]
    t = math.radians(float(pos.get("rotation_deg") or 0.0))
    ux, uy = (math.cos(t), -math.sin(t)), (math.sin(t), math.cos(t))
    wet = []
    for x, y in poly:
        c = (pos["utm_e"] + x * ux[0] + y * uy[0], pos["utm_n"] + x * ux[1] + y * uy[1])
        if any(_inside(c, r[0]) and not any(_inside(c, h) for h in r[1:]) for r in rings):
            wet.append(c)
    return wet


def outside_records(doc: dict) -> list[str]:
    """The records built outside the stockade against the rule they are built to."""
    errs: list[str] = []
    if "outside_the_stockade" not in doc:
        return errs
    out = doc["outside_the_stockade"]
    e17 = out["expansions"]["agent_17"]
    if abs(e17["stated_ft"] - 18 * PERCH_FT) > 0.01:
        errs.append(f"no. 17's stated distance is {e17['stated_ft']} ft, not eighteen perches")
    boxes = outside_boxes(doc)
    have = {p.stem for p in (ROOT / "data" / "structures").glob(f"{OUTSIDE_PREFIX}*.json")}
    for sid in sorted(have ^ set(boxes)):
        errs.append(f"{sid}: {'an outside record the register does not read' if sid in have else 'read in the register, but no record'}")
    datum = json.loads((ROOT / "data" / "datum.json").read_text())
    for sid, b in sorted(boxes.items()):
        f = ROOT / "data" / "structures" / f"{sid}.json"
        if not f.exists():
            continue
        st = json.loads(f.read_text())
        ph = st["phases"][0]
        if len(st["phases"]) != 1 or ph["documented_range"]["to"] != FIRST_FORT[1]:
            errs.append(f"{sid}: must carry one phase closing with the first fort on {FIRST_FORT[1]}")
        pos = ph["position"]
        want = "E {:+.1f}..{:+.1f} ft, N {:+.1f}..{:+.1f} ft".format(*b["box"])
        if want not in pos.get("symbolic_location", ""):
            errs.append(f"{sid}: symbolic_location does not carry the rule's box {want}")
        e, n, rot = seat(b["box"], b["facing"], datum, b["turn"])
        off = math.hypot(pos["utm_e"] - e, pos["utm_n"] - n)
        if off > SEAT_TOL_M or float(pos.get("rotation_deg") or 0.0) != rot:
            errs.append(f"{sid}: stands {off:.2f} m / {pos.get('rotation_deg')} deg off where the "
                        f"rule seats its box ({e:.2f}, {n:.2f} turned {rot})")
        poly = ph["footprint"]["polygon"]
        w = max(p[0] for p in poly) - min(p[0] for p in poly)
        d = max(p[1] for p in poly) - min(p[1] for p in poly)
        if abs(w - b["size_m"][0]) > TOL_M or abs(d - b["size_m"][1]) > TOL_M:
            errs.append(f"{sid}: footprint {w:.2f} x {d:.2f} m is not the rule's "
                        f"{b['size_m'][0]:.2f} x {b['size_m'][1]:.2f} m")
        for c in wet_corners(pos, poly):
            errs.append(f"{sid}: a footprint corner ({c[0]:.2f}, {c[1]:.2f}) stands on the "
                        f"committed 1812 water — the river governs a figure that puts a house in it")
    for key, e in out["expansions"].items():
        users = [p["part"] for p in out["parts"] if p["expansion"] == key]
        if e.get("governs") is False and users:
            errs.append(f"expansion {key} is kept but does not govern, and {users} use it")
    return errs


#: T-2504. The no. 31 houses are settlers', not the fort's: each closes on its own date,
#: which must fall after both 1812 scene dates and before the 1835 scene.
NORTH_BANK_OPEN_BY = ("1812-08-01", "1812-08-14")
NORTH_BANK_CLOSE_BEFORE = "1835-07-01"


def _corners(pos: dict, poly: list) -> list[tuple[float, float]]:
    """A footprint's corners in UTM, turned the way wet_corners turns them."""
    t = math.radians(float(pos.get("rotation_deg") or 0.0))
    ux, uy = (math.cos(t), -math.sin(t)), (math.sin(t), math.cos(t))
    return [(pos["utm_e"] + x * ux[0] + y * uy[0], pos["utm_n"] + x * ux[1] + y * uy[1])
            for x, y in poly]


def _overlap(a: list, b: list) -> bool:
    """Two convex footprints overlap: no separating axis among their edges' normals."""
    for poly in (a, b):
        for (x1, y1), (x2, y2) in zip(poly, poly[1:] + poly[:1]):
            nx, ny = y1 - y2, x2 - x1
            pa = [nx * x + ny * y for x, y in a]
            pb = [nx * x + ny * y for x, y in b]
            if max(pa) <= min(pb) or max(pb) <= min(pa):
                return False
    return True


def north_bank_boxes(doc: dict) -> tuple[dict[str, dict], dict[str, float]]:
    """Each north-bank part's fort-frame box (ft), and the expansions computed."""
    nb = doc["north_bank"]
    s = doc["scale"]["px_per_ft"]
    datum = json.loads((ROOT / "data" / "datum.json").read_text())
    an = json.loads((ROOT / "data" / "structures" / f"{nb['anchor']['record']}.json").read_text())
    ph = an["phases"][0]
    cs = _corners(ph["position"], ph["footprint"]["polygon"])
    ae = (sum(c[0] for c in cs) / len(cs) - datum["origin_utm_e"] - SEAT_LOCAL[0]) / FT_M
    an_ = (sum(c[1] for c in cs) / len(cs) - datum["origin_utm_n"] - SEAT_LOCAL[1]) / FT_M
    x0, y0, x1, y1 = nb["anchor"]["sheet_px"]
    ax, ay = (x0 + x1) / 2, (y0 + y1) / 2
    (lx0, ly0), (lx1, ly1) = nb["expansion"]["line_px"]
    exp = {"north_bank": nb["expansion"]["stated_ft"] / (math.hypot(lx1 - lx0, ly1 - ly0) / s),
           "agent_17": outside_boxes(doc)["first_fort_outer_agents_house"]["expansion"]}
    k = exp["north_bank"]
    out = doc["outside_the_stockade"]
    boxes = {}
    for p in nb["parts"]:
        x0, y0, x1, y1 = p["sheet_px"]
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        ce = ae + (cx - ax) / s * k
        cn = an_ - (cy - ay) / s * k
        # a ground part with no lettered scale is opened out with its place (T-2513)
        ft_per_px = (k / s if p["scale_ft_per_in"] == "expansion"
                     else p["scale_ft_per_in"] / out["inch_px"])
        w, h = (x1 - x0) * ft_per_px, (y1 - y0) * ft_per_px
        box = [round(ce - w / 2, 1), round(ce + w / 2, 1), round(cn - h / 2, 1), round(cn + h / 2, 1)]
        ew, ns = (box[1] - box[0]) * FT_M, (box[3] - box[2]) * FT_M
        boxes[p["part"]] = {"box": box, "facing": p["facing"], "record": p.get("record"),
                            "turn": float(p.get("turn_deg", 0.0)),
                            "size_m": (ns, ew) if p["facing"] in (90, 270) else (ew, ns)}
    return boxes, exp


def north_bank_records(doc: dict) -> list[str]:
    """T-2504: the no. 31 houses against the north-bank rule they are built to."""
    errs: list[str] = []
    if "north_bank" not in doc:
        return errs
    nb = doc["north_bank"]
    if nb["expansion"].get("governs") is not True:
        errs.append("north_bank: its expansion must govern, or the bank has no rule")
    boxes, _ = north_bank_boxes(doc)
    datum = json.loads((ROOT / "data" / "datum.json").read_text())
    an = json.loads((ROOT / "data" / "structures" / f"{nb['anchor']['record']}.json").read_text())
    feet = {nb["anchor"]["record"]: _corners(an["phases"][0]["position"],
                                             an["phases"][0]["footprint"]["polygon"])}
    for part, b in sorted(boxes.items()):
        sid = b["record"]
        row = next(p for p in nb["parts"] if p["part"] == part)
        if sid is None:
            if not row.get("builds"):
                errs.append(f"north_bank {part}: read and not built, so it must name the ticket that builds it")
            continue
        f = ROOT / "data" / "structures" / f"{sid}.json"
        if not f.exists():
            errs.append(f"north_bank {part}: names {sid}, which has no record")
            continue
        st = json.loads(f.read_text())
        if len(st["phases"]) != 1:
            errs.append(f"{sid}: a north-bank house carries one phase")
        ph = st["phases"][0]
        rng = ph["documented_range"]
        if not (rng["from"] <= NORTH_BANK_OPEN_BY[0] and rng["to"] >= NORTH_BANK_OPEN_BY[1]
                and rng["to"] < NORTH_BANK_CLOSE_BEFORE):
            errs.append(f"{sid}: stands {rng['from']}..{rng['to']}, which must cover "
                        f"{' and '.join(NORTH_BANK_OPEN_BY)} and close before {NORTH_BANK_CLOSE_BEFORE}")
        pos = ph["position"]
        want = "E {:+.1f}..{:+.1f} ft, N {:+.1f}..{:+.1f} ft".format(*b["box"])
        if want not in pos.get("symbolic_location", ""):
            errs.append(f"{sid}: symbolic_location does not carry the rule's box {want}")
        e, n, rot = seat(b["box"], b["facing"], datum, b["turn"])
        off = math.hypot(pos["utm_e"] - e, pos["utm_n"] - n)
        if off > SEAT_TOL_M or float(pos.get("rotation_deg") or 0.0) != rot:
            errs.append(f"{sid}: stands {off:.2f} m / {pos.get('rotation_deg')} deg off where the "
                        f"north-bank rule seats its box ({e:.2f}, {n:.2f} turned {rot})")
        poly = ph["footprint"]["polygon"]
        w = max(p[0] for p in poly) - min(p[0] for p in poly)
        d = max(p[1] for p in poly) - min(p[1] for p in poly)
        if abs(w - b["size_m"][0]) > TOL_M or abs(d - b["size_m"][1]) > TOL_M:
            errs.append(f"{sid}: footprint {w:.2f} x {d:.2f} m is not the rule's "
                        f"{b['size_m'][0]:.2f} x {b['size_m'][1]:.2f} m")
        for c in wet_corners(pos, poly):
            errs.append(f"{sid}: a footprint corner ({c[0]:.2f}, {c[1]:.2f}) stands on the "
                        f"committed 1812 water")
        feet[sid] = _corners(pos, poly)
    ids = sorted(feet)
    for i, a in enumerate(ids):
        for b_ in ids[i + 1:]:
            if _overlap(feet[a], feet[b_]):
                errs.append(f"north_bank: {a} and {b_} stand on one another")
    return errs


#: T-2508. The wharf (27) and the covered way (33) are NOT placed by the outside rule:
#: the draught says its river "is not regularly surveyed", so each is seated on the
#: committed 1812 river instead, by the figures in its index row's `seat`, measured from
#: the outer picket row's own record. Neither id takes a prefix the checks above glob.
OUTER_ROW = "first_fort_dearborn_pickets_outer"
HEIGHTFIELD_1812 = WATER_1812.parent / "heightfield.json"
#: how far south of the bank the wharf's two tangent casts start, and how far apart they are
BANK_CAST_M, BANK_SPAN_M = 15.0, 8.0
ROT_TOL_DEG = 0.05


def _wet(pt: tuple[float, float]) -> bool:
    """Whether a UTM point stands on the committed 1812 water."""
    return bool(wet_corners({"utm_e": pt[0], "utm_n": pt[1]}, [(0.0, 0.0)]))


def _ground(datum: dict):
    """The 1812 heightfield as a function of a UTM point (bilinear, metres over the water)."""
    import struct
    meta = json.loads(HEIGHTFIELD_1812.read_text())
    raw = (HEIGHTFIELD_1812.parent / meta["bin"]).read_bytes()
    cols = meta["cols"]

    def at(c, r):
        return struct.unpack_from("<h", raw, 2 * (r * cols + c))[0] * meta["scale"] + meta["offset"]

    def h(pt):
        x = (pt[0] - datum["origin_utm_e"] - meta["origin_e"]) / meta["cell_m"]
        y = (pt[1] - datum["origin_utm_n"] - meta["origin_n"]) / meta["cell_m"]
        i, j = int(x), int(y)
        fx, fy = x - i, y - j
        return (at(i, j) * (1 - fx) * (1 - fy) + at(i + 1, j) * fx * (1 - fy)
                + at(i, j + 1) * (1 - fx) * fy + at(i + 1, j + 1) * fx * fy)
    return h


def _edge(a: tuple[float, float], b: tuple[float, float]) -> tuple[float, float]:
    """The water's edge between a dry point `a` and a wet point `b`, to a millimetre."""
    for _ in range(40):
        m = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
        a, b = (a, m) if _wet(m) else (m, b)
    return b


def outer_row_corners() -> dict[str, tuple[float, float]]:
    """The outer picket row's north-west and north-east corners, from its own record."""
    ph = json.loads((ROOT / "data" / "structures" / f"{OUTER_ROW}.json").read_text())["phases"][0]
    e, n = ph["position"]["utm_e"], ph["position"]["utm_n"]
    xs = [p[0] for p in ph["footprint"]["polygon"]]
    ys = [p[1] for p in ph["footprint"]["polygon"]]
    return {"nw": (e + min(xs), n + max(ys)), "ne": (e + max(xs), n + max(ys))}


def wharf_seat(seat: dict, ground, inch_px: float) -> dict:
    """Where index no. 27's `seat` puts the wharf: the bank point the drafter's own
    distance reaches from the outer row's north-west corner, on the sheet's side of it,
    with the deck laid along the committed bank there."""
    cx, cy = outer_row_corners()["nw"]
    r = seat["radius_ft"] * FT_M

    def on(b):
        t = math.radians(b)
        return (cx + r * math.sin(t), cy + r * math.cos(t))
    b = seat["from_bearing_deg"]
    if _wet(on(b)):
        raise ValueError(f"the {seat['radius_ft']} ft circle is already wet at bearing {b}")
    while not _wet(on(b + 1.0)):
        b += 1.0
        if b > seat["from_bearing_deg"] + 180:
            raise ValueError("the circle never meets the committed 1812 water")
    lo, hi = b, b + 1.0
    for _ in range(40):
        mid = (lo + hi) / 2
        lo, hi = (lo, mid) if _wet(on(mid)) else (mid, hi)
    foot = on(hi)
    ends = [_edge((foot[0] + k, foot[1] - BANK_CAST_M), (foot[0] + k, foot[1] + BANK_CAST_M))
            for k in (-BANK_SPAN_M / 2, BANK_SPAN_M / 2)]
    du, dv = ends[1][0] - ends[0][0], ends[1][1] - ends[0][1]
    ln = math.hypot(du, dv)
    tu = (du / ln, dv / ln)
    nv = (-tu[1], tu[0])                       # waterward: the bank runs with the water on its left
    if not _wet((foot[0] + nv[0], foot[1] + nv[1])):
        raise ValueError("the bank's normal at the wharf does not point into the water")
    half = seat["along_bank_m"] / 2
    origin = (foot[0] - half * tu[0], foot[1] - half * tu[1])
    heel = (foot[0] - seat["heel_m"] * nv[0], foot[1] - seat["heel_m"] * nv[1])
    return {"foot": foot, "bearing": hi, "origin": origin,
            "rotation": round((math.degrees(math.atan2(tu[0], tu[1])) - 90.0) % 360, 2),
            "deck": round(ground(heel), 2),
            "reach_m": round(seat["reach_px"] * seat["scale_ft_per_in"] / inch_px * FT_M, 3)}


def covered_way_runs(seat: dict, ground) -> list[dict]:
    """Index no. 33's runs: from the outer row's north-east corner along the frame's
    north, each its own enclosure, one joint apart, the last ending on the water."""
    ex, ny = outer_row_corners()["ne"]
    w = seat["width_m"]
    out = []
    for sid, (y0, y1) in zip(seat["records"], seat["runs_m"]):
        line = [(ex - w / 2, ny + y0 + (y1 - y0) * k / 20) for k in range(21)]
        across = [(ex - w * k / 4, ny + y) for k in range(5) for y in (y0, y1)]
        hs = [ground(p) for p in line + across]
        out.append({"record": sid, "origin": (ex - w, ny + y0), "length_m": round(y1 - y0, 3),
                    "fall_m": round(max(hs) - min(hs), 2), "y0": y0, "y1": y1})
    return out


def water_works(doc: dict) -> list[str]:
    """T-2508: the wharf and the covered way against the seats their index rows state."""
    errs: list[str] = []
    rows = {r["no"]: r for r in doc["index"]}
    if "seat" not in rows[27] or "seat" not in rows[33]:
        return errs
    datum = json.loads((ROOT / "data" / "datum.json").read_text())
    ground = _ground(datum)
    sdir = ROOT / "data" / "structures"

    def phase(sid):
        f = sdir / f"{sid}.json"
        if not f.exists():
            errs.append(f"{sid}: named by the register's seat, but no record")
            return None
        st = json.loads(f.read_text())
        ph = st["phases"][0]
        if len(st["phases"]) != 1 or (ph["documented_range"]["from"], ph["documented_range"]["to"]) \
                != ("1808-01-25", FIRST_FORT[1]):
            errs.append(f"{sid}: must carry one phase, 1808-01-25 (the draught) to {FIRST_FORT[1]}")
        return ph

    s27 = rows[27]["seat"]
    try:
        w = wharf_seat(s27, ground, doc["outside_the_stockade"]["inch_px"])
    except ValueError as e:
        return errs + [f"no. 27: {e}"]
    ph = phase(s27["record"])
    if ph:
        pos, poly = ph["position"], ph["footprint"]["polygon"]
        off = math.hypot(pos["utm_e"] - w["origin"][0], pos["utm_n"] - w["origin"][1])
        if off > SEAT_TOL_M or abs(float(pos["rotation_deg"]) - w["rotation"]) > ROT_TOL_DEG:
            errs.append(f"{s27['record']}: stands {off:.2f} m / {pos['rotation_deg']} deg off where "
                        f"the seat puts it ({w['origin'][0]:.2f}, {w['origin'][1]:.2f} turned {w['rotation']})")
        us, vs = [p[0] for p in poly], [p[1] for p in poly]
        want = (0.0, s27["along_bank_m"], -s27["heel_m"], w["reach_m"])
        if max(abs(a - b) for a, b in zip((min(us), max(us), min(vs), max(vs)), want)) > TOL_M:
            errs.append(f"{s27['record']}: footprint u {min(us)}..{max(us)}, v {min(vs)}..{max(vs)} "
                        f"is not the seat's u 0..{want[1]}, v {want[2]}..{want[3]}")
        deck = ph["form"]["deck_height_m"]["value"]
        if abs(deck - w["deck"]) > 0.01:
            errs.append(f"{s27['record']}: deck {deck} m is not the ground at its heel, {w['deck']} m")
    s33 = rows[33]["seat"]
    runs = covered_way_runs(s33, ground)
    prev = 0.0
    for i, r in enumerate(runs):
        if abs(r["y0"] - prev - s33["joint_m"]) > 1e-6:
            errs.append(f"{r['record']}: starts {r['y0'] - prev:.2f} m after the run before it, "
                        f"not one joint ({s33['joint_m']} m)")
        prev = r["y1"]
        if r["fall_m"] > s33["max_fall_m"]:
            errs.append(f"{r['record']}: the ground falls {r['fall_m']} m under it, more than "
                        f"{s33['max_fall_m']} m — its uphill pickets would be buried past a man's height")
        ph = phase(r["record"])
        if not ph:
            continue
        pos, poly = ph["position"], ph["footprint"]["polygon"]
        off = math.hypot(pos["utm_e"] - r["origin"][0], pos["utm_n"] - r["origin"][1])
        if off > SEAT_TOL_M or float(pos.get("rotation_deg") or 0.0) != SEAT_BEARING_DEG:
            errs.append(f"{r['record']}: stands {off:.2f} m off where the seat puts it")
        us, vs = [p[0] for p in poly], [p[1] for p in poly]
        if abs(max(us) - s33["width_m"]) > TOL_M or abs(max(vs) - r["length_m"]) > TOL_M:
            errs.append(f"{r['record']}: footprint {max(us)} x {max(vs)} m is not the seat's "
                        f"{s33['width_m']} x {r['length_m']} m")
    if runs:
        ex, ny = outer_row_corners()["ne"]
        mid = (ex - s33["width_m"] / 2, ny + runs[-1]["y1"])
        if not _wet((mid[0], mid[1] + s33["joint_m"])) or _wet((mid[0], mid[1] - s33["joint_m"])):
            errs.append(f"{runs[-1]['record']}: its north end is not within {s33['joint_m']} m of "
                        f"the committed 1812 water — the covered way must reach the river")
    return errs


def fetch(doc: dict) -> bytes:
    cache = Path("/tmp") / "chicago4d-whistler-1808.png"
    if not cache.exists():
        with urllib.request.urlopen(doc["sheet"]["url"], timeout=60) as r:
            cache.write_bytes(r.read())
    data = cache.read_bytes()
    got = hashlib.sha256(data).hexdigest()
    if got != doc["sheet"]["sha256"]:
        raise SystemExit(f"the working copy's sha256 is {got}, not the pinned "
                         f"{doc['sheet']['sha256']} — the sheet has moved; re-read it")
    return data


def remeasure(doc: dict) -> list[str]:
    import io
    from PIL import Image
    im = Image.open(io.BytesIO(fetch(doc))).convert("L")
    w, h = im.size
    px = im.load()
    dark_rows = [y for y in range(h) if min(px[x, y] for x in STAFF_COLS) < DARK]
    runs, start, prev = [], None, None
    for y in dark_rows:
        if start is None or y - prev > MAX_GAP:
            if start is not None:
                runs.append((start, prev))
            start = y
        prev = y
    if start is not None:
        runs.append((start, prev))
    top, foot = max(runs, key=lambda r: r[1] - r[0])
    want = doc["scale"]["staff_px"]
    print(f"   staff: top y {top}, foot y {foot}, {foot - top + 1} px "
          f"= {(foot - top + 1) / doc['scale']['staff_ft']:.4f} px/ft")
    errs = []
    if [top, foot] != [want["top"][1], want["foot"][1]]:
        errs.append(f"the staff measures y {top}-{foot}; the file says "
                    f"{want['top'][1]}-{want['foot'][1]}")
    return errs


def main() -> int:
    doc = json.loads(TRACE.read_text())
    errs = (check(doc) + records(doc) + two_forts() + outside_records(doc) + water_works(doc)
            + north_bank_records(doc))
    if "--remeasure" in sys.argv:
        errs += remeasure(doc)
    if errs:
        for e in errs:
            print(f"FAIL: {e}")
        return 1
    rows = doc["index"]
    count = {st: sum(1 for r in rows if r["status"] == st) for st in sorted(STATUSES)}
    print(f"OK: Whistler 1808 at {doc['scale']['px_per_ft']} px/ft off the 75 ft staff; "
          f"34 index numbers — " + ", ".join(f"{v} {k}" for k, v in count.items())
          + f"; {len(RECORDS)} first-fort records built from it"
          + (f", {len(outside_boxes(doc))} outside the stockade (T-2062)"
             if "outside_the_stockade" in doc else "")
          + (f"; the wharf and the covered way's {len(doc['index'][32]['seat']['records'])} runs "
             f"on the 1812 river (T-2508)" if "seat" in doc["index"][32] else "")
          + (f"; {sum(1 for p in doc['north_bank']['parts'] if p.get('record'))} records across "
             f"the river by the north-bank rule (T-2504, T-2513, T-2485)" if "north_bank" in doc else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
