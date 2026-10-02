#!/usr/bin/env python3
"""Generate the town's woodpiles — one at every dwelling, by whose house it is.

WHAT THIS IS. T-1959, piece 2 of T-1212: *"woodpiles at every dwelling: the
yard-by-household rule in the placement policy (type x wealth) and a woodpile kind drawn
by yard.js, varying house to house."* The rule is `tools/yard_rule_1835.py`, printed in
the placement policy under `yard`; this tool spends it on every dwelling standing on the
scene date and writes `data/yard/town_woodpiles.json`, which `renderers/web/js/yard.js`
draws and `tools/check.sh` re-derives byte for byte.

WHICH ROOFS ARE DWELLINGS. Every placed roof whose function reads as a dwelling under
T-0052's clause (the same houses that get dooryard stems and gardens), every roof of a
dwelling family of the reconstruction spec (D1-D7, H1-H3), and the roofs that house a
household over a trade or a bar — a store-residence, a tavern, an inn, a hotel, a boarding
house. A building site (`*_under_construction`) houses nobody yet and is not one.

WHERE A PILE STANDS. Against its own house's BACK wall: the footprint edge whose outward
ground stands furthest from the nearest street on the house's own bank (the dooryard
tool's measure, `facing_street_segments`), which is where a household stacked the wood it
was burning — by the kitchen door, off the street. The pile is racked a hand's gap off the
wall, parallel to it, and slid along the wall from a corner chosen per house; when the back
wall is too short or the ground behind it is taken, the next wall round is tried, then the
pile is cut down (a second rick dropped, a stove rick shortened), and only then refused,
in writing. Every point of a pile must stand on dry ground inside the heightfield, inside
no footprint and clear of every other one, off every street's track and every plank walk,
clear of every committed fence line and outside every dooryard, clear of every committed
tree and bush, and clear of every other pile, of the trade goods and wagons already
standing, and of every privy and stable T-1960 dealt to the yards.

WHAT IS INVENTED is every pile's position, size and count — `reconstructed`, docs/
LIBERTIES.md L356. The FACT that a household kept firewood is `inferred`: the town priced
firewood by the cord every week of the summer, and the record's `existence` block says so.

    python3 tools/generate_woodpiles.py            write the record
    python3 tools/generate_woodpiles.py --check    re-derive and diff
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import generate_dooryard_plantings as dooryard  # noqa: E402
import yard_rule_1835 as rule  # noqa: E402
from generate_dooryard_plantings import (  # noqa: E402
    footprint_world, load, path_dist, poly_contains, poly_edge_dist, seg_dist)

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
STRUCTURES = DATA / "structures"
PLANTINGS = DATA / "flora" / "plantings"
YARD = DATA / "yard"
DOORYARDS = DATA / "enclosures" / "town_dooryard_pickets.json"
OUT = YARD / "town_woodpiles.json"

DWELLING_ARCHETYPES = {"frame_dwelling", "log_dwelling", "outbuilding", "frame_tavern",
                       "frame_storefront"}
HOUSEHOLD_FUNCTIONS = {"store_residence", "tavern_inn", "tavern", "hotel", "boarding_house",
                       "inn"}

# What a stick is. `stove` is a 2 ft length sawn for the stove; `cord` is the 4 ft
# cordwood the quartermaster's notice racks 8 ft long and 4 ft high.
STICK_M = {"stove": 0.61, "cord": 1.22}
WALL_GAP_M = 0.45          # racked a hand's gap off the wall, for the air
RICK_GAP_M = 0.35          # between two ricks along one wall
BLOCK_OUT_M = 1.1          # the chopping block stands this far out past the pile
CORNER_INSET_M = 0.35      # a pile starts this far in from the wall's corner
MIN_STOVE_RICK_M = 1.2     # a stove rick is cut down no shorter than this

# Clearances, each the smallest that keeps one object out of another.
OTHER_WALL_M = 0.6         # off any OTHER roof's wall
TRACK_SHOULDER_M = dooryard.TRACK_SHOULDER_M
TRACK_MARGIN_M = 0.6
WALK_MARGIN_M = 0.4
FENCE_MARGIN_M = 0.35
STEM_MARGIN_M = 1.0
GOODS_MARGIN_M = 1.2
WAGON_MARGIN_M = 3.6
PILE_MARGIN_M = 0.5
# A privy or a stable is walked round and into, so a pile keeps a full metre off it on
# every side rather than the 0.6 m it keeps off a house's wall: no rick across a door.
OUTBUILDING_M = 1.0
DRY_FLOOR_M = 0.6
NEAR_M = 45.0              # how far round a house anything is looked for


def dwelling(sid: str, sc: dict) -> tuple[bool, str]:
    """(is a dwelling, the function as read) — the module docstring's three clauses."""
    st_path = STRUCTURES / f"{sid}.json"
    st = load(st_path) if st_path.exists() else sc
    fn = (st.get("attributes") or {}).get("function") or \
        (sc.get("attributes") or {}).get("function")
    fn = fn.get("value") if isinstance(fn, dict) else fn
    fn = str(fn or "")
    if "under_construction" in fn:
        return False, fn
    family = (sc.get("reconstruction") or {}).get("family") or ""
    if sc.get("archetype") not in DWELLING_ARCHETYPES:
        return False, fn
    if family[:1] in ("D", "H") and family[1:].isdigit():
        return True, fn
    if fn in HOUSEHOLD_FUNCTIONS:
        return True, fn
    if sc.get("archetype") in ("frame_dwelling", "log_dwelling") and \
            dooryard.is_dwelling_function(fn):
        return True, fn
    if sc.get("archetype") == "outbuilding" and dooryard.is_dwelling_function(fn):
        return True, fn
    return False, fn


def area(poly) -> float:
    return sum(poly[i][0] * poly[(i + 1) % len(poly)][1]
               - poly[(i + 1) % len(poly)][0] * poly[i][1]
               for i in range(len(poly))) / 2.0


def outbuilding_footprint(ob: dict) -> list[tuple[float, float]]:
    """A yard outbuilding's four corners in ENU, in the frame yard.js draws it in: along
    the face is (cos b, sin b) in world XZ and out of it (sin b, -cos b), world z being
    -north, so along is (cos b, -sin b) in ENU and out is (sin b, cos b)."""
    e, n = ob["at_local_enu_m"]
    b = math.radians(ob.get("bearing_deg") or 0.0)
    ha, ho = (ob.get("along_m") or 0.0) / 2, (ob.get("depth_m") or 0.0) / 2
    al, out = (math.cos(b), -math.sin(b)), (math.sin(b), math.cos(b))
    return [(e + al[0] * sa * ha + out[0] * so * ho, n + al[1] * sa * ha + out[1] * so * ho)
            for sa, so in ((-1, -1), (1, -1), (1, 1), (-1, 1))]


class Ground:
    """Everything a pile must stand clear of, read once and bucketed by house."""

    def __init__(self):
        self.w = dooryard.world()
        self.stems = []
        for path in sorted(PLANTINGS.glob("*.json")):
            if path.name == "index.json":
                continue
            for stem in load(path).get("stems") or []:
                at = stem.get("at_local_enu_m")
                if at:
                    self.stems.append(tuple(at))
        self.dooryards = []
        if DOORYARDS.exists():
            for run in load(DOORYARDS).get("runs") or []:
                pts = [tuple(p) for p in run.get("path_local_enu_m") or []]
                if len(pts) >= 3:
                    self.dooryards.append(pts)
        self.goods, self.wagons, self.outbuildings = [], [], []
        for path in sorted(YARD.glob("*.json")):
            if path.name in ("index.json", OUT.name):
                continue
            rec = load(path)
            for group in (rec.get("frontages") or []) + (rec.get("lots") or []):
                for item in group.get("items") or []:
                    if item.get("at_local_enu_m"):
                        self.goods.append(tuple(item["at_local_enu_m"]))
            for key in ("wagons", "benches", "sheds", "carts", "piles"):
                for thing in rec.get(key) or []:
                    if thing.get("at_local_enu_m"):
                        self.wagons.append(tuple(thing["at_local_enu_m"]))
            for ob in rec.get("outbuildings") or []:
                if ob.get("at_local_enu_m"):
                    self.outbuildings.append(outbuilding_footprint(ob))
        self.street_segs = []
        for pts, track_w, _banks in self.w.streets:
            clear = track_w / 2 + TRACK_SHOULDER_M + TRACK_MARGIN_M
            for i in range(len(pts) - 1):
                self.street_segs.append((tuple(pts[i]), tuple(pts[i + 1]), clear))
        self.fence_segs = []
        for pts in self.w.fences:
            for i in range(len(pts) - 1):
                self.fence_segs.append((tuple(pts[i]), tuple(pts[i + 1])))
        self.piles: list[list[tuple[float, float]]] = []

    def near(self, cx, cy):
        """The obstacles within NEAR_M of a house — the only ones a pile could touch."""
        def close(p):
            return abs(p[0] - cx) <= NEAR_M and abs(p[1] - cy) <= NEAR_M

        return {
            "footprints": [fp for fp in self.w.obstructions
                           if any(close(q) for q in fp)],
            "streets": [s for s in self.street_segs if close(s[0]) or close(s[1])],
            "walks": [s for s in self.w.walks if close(s[0]) or close(s[1])],
            "fences": [s for s in self.fence_segs if close(s[0]) or close(s[1])],
            "dooryards": [d for d in self.dooryards if any(close(q) for q in d)],
            "stems": [s for s in self.stems if close(s)],
            "goods": [g for g in self.goods if close(g)],
            "wagons": [g for g in self.wagons if close(g)],
            "outbuildings": [o for o in self.outbuildings if any(close(q) for q in o)],
        }

    def clear(self, p, own, near, wagon_ok=False) -> str | None:
        """None when `p` may carry wood, else the first reason it may not."""
        hf = self.w.hf
        e, n = p
        inset = dooryard.EDGE_INSET_M
        if not (hf.origin_e + inset <= e <= hf.origin_e + (hf.cols - 1) * hf.cell_m - inset
                and hf.origin_n + inset <= n
                <= hf.origin_n + (hf.rows - 1) * hf.cell_m - inset):
            return "off the heightfield"
        if hf.height(e, n) < float(hf.meta.get("water_surface_m", 0.0)) + DRY_FLOOR_M:
            return "wet ground"
        for fp in near["footprints"]:
            if poly_contains(p, fp):
                return "inside a roof"
            if fp is not own and poly_edge_dist(p, fp) < OTHER_WALL_M:
                return "against another roof"
        for a, b, clear in near["streets"]:
            if seg_dist(p, a, b) < clear:
                return "on a street"
        for a, b, half in near["walks"]:
            if seg_dist(p, a, b) < half + WALK_MARGIN_M:
                return "on a plank walk"
        for a, b in near["fences"]:
            if seg_dist(p, a, b) < FENCE_MARGIN_M:
                return "in a fence line"
        for d in near["dooryards"]:
            if poly_contains(p, d):
                return "in a dooryard"
        for s in near["stems"]:
            if math.hypot(e - s[0], n - s[1]) < STEM_MARGIN_M:
                return "at a tree or bush"
        for g in near["goods"]:
            if math.hypot(e - g[0], n - g[1]) < GOODS_MARGIN_M:
                return "among trade goods"
        for g in near["wagons"]:
            if math.hypot(e - g[0], n - g[1]) < WAGON_MARGIN_M:
                return "at a wagon"
        for o in near["outbuildings"]:
            if poly_contains(p, o) or poly_edge_dist(p, o) < OUTBUILDING_M:
                return "at a privy or stable"
        for pile in self.piles:
            if poly_contains(p, pile) or poly_edge_dist(p, pile) < PILE_MARGIN_M:
                return "on another woodpile"
        return None


def deal_range(sid, what, lo_hi, step=0.01):
    lo, hi = lo_hi
    v = lo + (hi - lo) * rule.fraction(sid, what)
    return round(round(v / step) * step, 2)


def deal_int(sid, what, lo_hi):
    lo, hi = lo_hi
    return lo + int(rule.fraction(sid, what) * (hi - lo + 1))


def plan(sid: str, row: dict, ricks: int, length: float | None):
    """The pile in the wall's own frame: (along, out) rectangles and the items drawn.

    `along` runs from the start of the pile; `out` away from the wall. Returns
    (row_length, depth, parts), each part (kind, along_centre, out_centre, half_along,
    half_out, extras).
    """
    kind = row["kind"]
    parts = []
    if kind == "cordwood":
        depth = STICK_M[row["stick"]]
        L = length if length is not None else deal_range(sid, "length", row["length_m"])
        along = 0.0
        for i in range(ricks):
            h = deal_range(sid, f"height{i}", row["height_m"])
            parts.append(("cordwood", along + L / 2, WALL_GAP_M + depth / 2, L / 2,
                          depth / 2, {"length_m": L, "depth_m": depth, "height_m": h,
                                      "stick": row["stick"]}))
            along += L + RICK_GAP_M
        total = along - RICK_GAP_M
        out_back = WALL_GAP_M + depth
    elif kind == "log_heap":
        n = deal_int(sid, "logs", row["logs"])
        L = length if length is not None else deal_range(sid, "loglen", row["log_length_m"])
        depth = 0.36 * n + 0.3
        parts.append(("log_heap", L / 2, WALL_GAP_M + depth / 2, L / 2, depth / 2,
                      {"logs": n, "log_length_m": L, "depth_m": round(depth, 2)}))
        total, out_back = L, WALL_GAP_M + depth
    else:
        n = deal_int(sid, "pieces", row["pieces"])
        L = 1.7
        depth = 1.3
        parts.append(("slab_heap", L / 2, WALL_GAP_M + depth / 2, L / 2, depth / 2,
                      {"pieces": n}))
        total, out_back = L, WALL_GAP_M + depth
    if row.get("block"):
        # The block stands out past the pile, toward the end the barrow comes from.
        at_end = rule.fraction(sid, "blockend") < 0.5
        a = 0.45 if at_end else max(total - 0.45, 0.45)
        parts.append(("chopping_block", a, out_back + BLOCK_OUT_M, 0.3, 0.3,
                      {"billets": deal_int(sid, "billets", (1, 3))}))
    return total, parts


def edges_by_backness(fp, near, w, cx, cy):
    """The house's walls, back wall first: the outward ground furthest from its street."""
    ring = max(math.hypot(q[0] - cx, q[1] - cy) for q in fp)
    facing = dooryard.facing_street_segments(cx, cy, ring + 6.0, w)
    ccw = area(fp) > 0
    out = []
    for i in range(len(fp)):
        a, b = fp[i], fp[(i + 1) % len(fp)]
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dy)
        if L < 1.0:
            continue
        ux, uy = dx / L, dy / L
        nx, ny = (uy, -ux) if ccw else (-uy, ux)
        probe = ((a[0] + b[0]) / 2 + nx * 3.0, (a[1] + b[1]) / 2 + ny * 3.0)
        street = dooryard.YARD_STREET_REACH_M
        for s, t in facing:
            street = min(street, seg_dist(probe, s, t))
        out.append({"i": i, "a": a, "u": (ux, uy), "n": (nx, ny), "len": L,
                    "street": round(street, 3)})
    out.sort(key=lambda e: (-e["street"], -e["len"], e["i"]))
    return out


def rect(edge, along0, ac, oc, ha, ho):
    """A part's four corners in ENU, given its centre in the wall's frame."""
    (ax, ay), (ux, uy), (nx, ny) = edge["a"], edge["u"], edge["n"]
    out = []
    for sa, so in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
        al = along0 + ac + sa * ha
        o = oc + so * ho
        out.append((ax + ux * al + nx * o, ay + uy * al + ny * o))
    return out


def try_place(ground, sid, fp, near, edge, total, parts):
    """The first slide along `edge` where every part is clear, or (None, reason)."""
    if total + 2 * CORNER_INSET_M > edge["len"]:
        return None, "the wall is shorter than the pile"
    first = "start" if rule.fraction(sid, "corner") < 0.5 else "end"
    starts = {"start": CORNER_INSET_M, "end": edge["len"] - CORNER_INSET_M - total,
              "middle": (edge["len"] - total) / 2}
    order = [first, "end" if first == "start" else "start", "middle"]
    why = None
    for which in order:
        along0 = starts[which]
        polys, reason = [], None
        for kind, ac, oc, ha, ho, _x in parts:
            poly = rect(edge, along0, ac, oc, ha, ho)
            cen = (sum(q[0] for q in poly) / 4, sum(q[1] for q in poly) / 4)
            mids = [((poly[k][0] + poly[(k + 1) % 4][0]) / 2,
                     (poly[k][1] + poly[(k + 1) % 4][1]) / 2) for k in range(4)]
            for p in poly + mids + [cen]:
                reason = ground.clear(p, fp, near)
                if reason:
                    break
            if reason:
                break
            polys.append(poly)
        if not reason:
            return (along0, polys), None
        why = why or reason
    return None, why


def bearing_of(edge) -> float:
    """yard.js's frame: along = (cos b, -sin b) in ENU, so b = atan2(-u_n, u_e)."""
    ux, uy = edge["u"]
    return round(math.degrees(math.atan2(-uy, ux)) % 360.0, 2)


def place(ground, sid, sc, fp, row_name, row):
    cx = sum(q[0] for q in fp) / len(fp)
    cy = sum(q[1] for q in fp) / len(fp)
    near = ground.near(cx, cy)
    edges = edges_by_backness(fp, near, ground.w, cx, cy)
    ricks_hi = deal_int(sid, "ricks", row["ricks"]) if row["kind"] == "cordwood" else 1
    attempts = []
    for ricks in range(ricks_hi, 0, -1):
        lengths = [None]
        if row["kind"] == "cordwood" and row["stick"] == "stove":
            base = deal_range(sid, "length", row["length_m"])
            lengths = [None] + [round(L, 2) for L in (base * 0.75, MIN_STOVE_RICK_M)
                                if L >= MIN_STOVE_RICK_M and L < base]
        for length in lengths:
            total, parts = plan(sid, row, ricks, length)
            for edge in edges:
                spot, why = try_place(ground, sid, fp, near, edge, total, parts)
                if spot:
                    along0, polys = spot
                    edge["rank"] = edges.index(edge)
                    return edge, along0, parts, polys, ricks, length, None
                attempts.append(why)
    reasons = sorted({a for a in attempts if a})
    return None, None, None, None, None, None, ", ".join(reasons) or "no wall to stack on"


def build():
    ground = Ground()
    lots, refused = [], []
    counts = {"dwellings": 0, "by_row": {}, "by_class": {}, "by_basis": {}, "items": {}}
    for sid in sorted(ground.w.sidecars):
        sc = ground.w.sidecars[sid]
        pl = sc.get("placement") or {}
        if pl.get("vertical_anchor") == "water" or sc.get("drawn_by"):
            continue
        is_home, fn = dwelling(sid, sc)
        if not is_home:
            continue
        fp = footprint_world(sc)
        if len(fp) < 3:
            continue
        counts["dwellings"] += 1
        st_path = STRUCTURES / f"{sid}.json"
        text = st_path.read_text(encoding="utf-8") if st_path.exists() else ""
        who = rule.household(sid, sc, text)
        house_kind = rule.house(sc, abs(area(fp)))
        row_name, row = rule.row_for(who["class"], house_kind)
        # The footprint as the obstruction list holds it, so `own` is matched by identity.
        own = next((o for o in ground.w.obstructions if o == fp), fp)
        edge, along0, parts, polys, ricks, length, why = place(
            ground, sid, sc, own, row_name, row)
        if edge is None:
            refused.append({"structure_id": sid, "row": row_name,
                            "why": f"no wall with clear ground behind it: {why}"})
            continue
        ground.piles.extend(polys)
        items = []
        for k, (kind, ac, oc, ha, ho, extra) in enumerate(parts):
            poly = polys[k]
            cen = (round(math.fsum(q[0] for q in poly) / 4, 2), round(math.fsum(q[1] for q in poly) / 4, 2))
            item = {"kind": kind, "at_local_enu_m": list(cen), "bearing_deg": bearing_of(edge)}
            item.update(extra)
            item["seed"] = int(rule.fraction(sid, f"seed{k}") * 2 ** 31)
            items.append(item)
            counts["items"][kind] = counts["items"].get(kind, 0) + 1
        lot = {
            "structure_id": sid,
            "name": sc.get("name"),
            "function": fn or None,
            "household_class": who["class"],
            "household_by": who["by"],
            "house": house_kind,
            "row": row_name,
            "rule": row["rule"],
            "confidence": "reconstructed",
            "wall": "back" if edge["rank"] == 0 else "side",
            "items": items,
        }
        if who["household"]:
            lot["household"] = who["household"]
        if who["trade"]:
            lot["trade"] = who["trade"]
        if ricks is not None and row["kind"] == "cordwood" and \
                ricks < deal_int(sid, "ricks", row["ricks"]):
            lot["cut_down"] = f"dealt {deal_int(sid, 'ricks', row['ricks'])} ricks; " \
                              f"{ricks} fit the wall"
        elif length is not None:
            lot["cut_down"] = f"the rick shortened to {length} m to fit the wall"
        lots.append(lot)
        counts["by_row"][row_name] = counts["by_row"].get(row_name, 0) + 1
        counts["by_class"][who["class"]] = counts["by_class"].get(who["class"], 0) + 1
        counts["by_basis"][who["by"]] = counts["by_basis"].get(who["by"], 0) + 1
    counts["piled"] = len(lots)
    counts["refused"] = len(refused)
    for k in ("by_row", "by_class", "by_basis", "items"):
        counts[k] = dict(sorted(counts[k].items()))
    return lots, refused, counts


def record(lots, refused, counts):
    stove, cord = STICK_M["stove"], STICK_M["cord"]
    return {
        "_doc": (
            "A woodpile at every dwelling, by whose house it is (T-1959, piece 2 of "
            "T-1212). GENERATED by tools/generate_woodpiles.py from the yard-by-household "
            "rule in tools/yard_rule_1835.py — printed in data/reconstruction/"
            "1835_placement_policy.json under `yard` — and re-derived byte for byte by "
            "tools/check.sh. NOT structure records and NOT baked: a woodpile is a small "
            "thing standing on ground this project has already drawn, so it is derived "
            "from the committed footprints and drawn at load by renderers/web/js/yard.js, "
            "and a pick on it opens the card of the house it stands behind. docs/"
            "LIBERTIES.md L356 claims what is invented."),
        "id": "town_woodpiles",
        "name": "Woodpiles at the town's dwellings",
        "kind": "yard_goods",
        "scene": "1835",
        "target_date": "1835-07-01",
        "coordinates": ("Local East-North-Up metres from data/datum.json's origin, the "
                        "same frame data/enclosures/ and data/signage/ and the sidecars' "
                        "placement.local_e / placement.local_n use."),
        "counts": counts,
        "existence": {
            "value": "every household in the town kept firewood at its house",
            "confidence": "inferred",
            "sources": ["chicago_democrat_1833_1835"],
            "note": (
                "REASONED FROM THE TOWN'S OWN PRICE CURRENT, NOT READ OFF ANY HOUSE. The "
                "Chicago Democrat's weekly 'Chicago Prices Current' quotes firewood by the "
                "cord through the summer of 1835 — $2.50 the cord on 27 May "
                "(chicago_democrat_1835_05_27#c001) and $2.00 on 12 August "
                "(chicago_democrat_1835_08_12#c002) — and a paper prices weekly what its "
                "readers buy weekly. The same paper carries the quartermaster's call for "
                "five hundred cords for the troops at Fort Dearborn (4 June 1835 #c008, "
                "again 1 July #c018). Wood was what the town cooked and heated with, so a "
                "dwelling kept some. WHERE each pile stood, how big it was and how it was "
                "stacked is stated by nothing, and every pile here is graded "
                "`reconstructed` for that reason: the vertex carries the weaker grade, so "
                "a visitor who hides `reconstructed` hides the layer."),
        },
        "form": {
            "cord_m": {
                "value": [2 * cord, cord, cord],
                "confidence": "inferred",
                "sources": ["chicago_democrat_1833_1835"],
                "note": ("8 ft long, 4 ft high and 4 ft wide, 'measuring from half the "
                         "slope of each end of the sticks' — the quartermaster's own "
                         "specification of a cord (chicago_democrat_1835_06_04#c008). It "
                         "is the army's contract and not a household's, so the grade is "
                         "inferred: a cord in this town was the measure firewood was "
                         "priced in, and the merchant's and keeper's rows rack it at its "
                         "own length and depth."),
            },
            "stove_stick_m": {
                "value": stove, "confidence": "reconstructed",
                "note": ("INVENTED. A 4 ft stick sawn in two for a cookstove or a small "
                         "box stove; no source states the length a Chicago household cut "
                         "its wood to."),
            },
            "billet_m": {
                "value": 0.13, "confidence": "reconstructed",
                "note": ("INVENTED. A split quarter of a 6-8 in round, the size a stick "
                         "is split to for a fire; how many courses a rick is drawn in is "
                         "its height over this."),
            },
            "log_m": {
                "value": [0.32, 0.22], "confidence": "reconstructed",
                "note": ("INVENTED. The two diameters an unsplit length is drawn between, "
                         "a pole a man and a horse could drag in, not a saw log."),
            },
            "block_m": {
                "value": [0.5, 0.46], "confidence": "reconstructed",
                "note": ("INVENTED. A chopping block's height and diameter: a round sawn "
                         "off a butt log, knee high."),
            },
            "slab_m": {
                "value": [1.4, 0.26, 0.06], "confidence": "reconstructed",
                "note": ("INVENTED. A sawmill slab — the bark-side offcut of a log sawn "
                         "to boards — 1.4 m by 0.26 m by 0.06 m."),
            },
        },
        "rule": {
            "policy": ("data/reconstruction/1835_placement_policy.json#yard — authored in "
                       "tools/yard_rule_1835.py"),
            "rows": {k: {"rule": v["rule"], "who": v["who"], "why": v["why"]}
                     for k, v in rule.WOODPILE.items()},
            "placement": (
                "against the house's back wall — the edge whose outward ground is "
                "furthest from the nearest street on the house's own bank — racked "
                f"{WALL_GAP_M} m off it and parallel, slid from a corner chosen per house; "
                "then the next wall round; then the pile cut down (a rick dropped, a stove "
                f"rick shortened to no less than {MIN_STOVE_RICK_M} m); then refused in "
                "writing. Every point clear of every roof, street, walk, fence, dooryard, "
                "tree, trade good, wagon, privy, stable and other pile."),
            "july": ("every rick is dealt at or below a full cord's 4 ft: a winter's wood "
                     "was laid in from the autumn, and July is the year's low."),
        },
        "lots": lots,
        "refused": refused,
        "research_note": (
            "WHAT WOULD MOVE ANY OF THIS. A probate inventory, an insurance survey or a "
            "lot sale notice of 1834-36 that names a woodshed or a quantity of wood at a "
            "particular Chicago house would put that house's pile on its evidence. A "
            "dated view of a back lot — none of the committed plates shows one — would "
            "say how town wood was stacked. A household account would say how much a "
            "family burned in a summer month. WHAT THIS DOES NOT DRAW: a woodshed (an A4 "
            "family roof, built by the build tickets), a sawbuck, an axe, or anyone "
            "working the pile — L1, no human figure."),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="re-derive and diff, write nothing")
    args = ap.parse_args()
    lots, refused, counts = build()
    text = json.dumps(record(lots, refused, counts), indent=1, ensure_ascii=False) + "\n"
    summary = (f"{counts['piled']} woodpiles at {counts['dwellings']} dwellings "
               f"({counts['refused']} refused for want of room) — {counts['by_row']}")
    if args.check:
        if not OUT.exists() or OUT.read_text(encoding="utf-8") != text:
            print(f"WOODPILE DRIFT\n  - {OUT.relative_to(ROOT)} has drifted from the rule "
                  f"in tools/generate_woodpiles.py — run it and read the diff")
            return 1
        print(f"verified {summary}")
        return 0
    OUT.write_text(text, encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)} — {summary}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
