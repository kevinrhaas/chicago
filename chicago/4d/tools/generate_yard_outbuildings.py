#!/usr/bin/env python3
"""Generate the yard outbuildings — a privy at every dwelling lot and a stable for the
horse-keeping households (T-1960, piece 3 of T-1212).

WHAT THIS IS. T-1212's rule, verbatim: *"privy placement off the alley, stable/barn for the
households that kept a horse (merchants, forwarders, physicians, teamsters, the taverns)"*,
and its stop condition: *"no lot in the town is bare ground by default."* Before this record
the town stood 38 baked privies and 31 baked stables, dealt as count-units of the roof
programme to the blocks that programme reached. 124 improved platted lots with a dwelling on
them had a yard behind the house and nothing standing in it. A town of 3,265 people with no
privy behind most of its houses is not a cleaner town; it is a wrong one.

WHAT IT BUILDS. For every improved platted lot (the same survey the lot-line fences read —
`generate_lot_line_fences.survey`, one committed building centre or more inside a lot of
`data/traces/vectors/thompson_lots.json`) that carries a DWELLING:

  1. a **privy** in a rear corner of the yard, its back 0.75 m inside the rear lot line —
     off the alley, where a night-soil man reached it and where the house's own back door
     was furthest from it — unless a committed privy already stands on the lot;
  2. a **stable** in the other rear corner when the household kept a horse, unless a
     committed stable, barn or carriage shed already stands on the lot. A household kept a
     horse when the house's own class (the fabric rule's `fabric_basis.class`, L330) is
     `merchant`, `keeper` or `freight`, when the house is a tavern, inn, hotel or boarding
     house, or when its reconstructed occupation is a teamster's. That is T-1212's list —
     merchants, forwarders, the taverns, teamsters — read off fields the town already
     carries. Physicians are on the list and on no committed field, so none is reached.

THE HOUSE DECIDES THE SIZE AND THE FINISH, which is what "by household" means here: a
labourer's privy is a 3½-foot box of sawmill slabs; a tradesman's a 4-foot board privy; a
keeper's and a merchant's a 5-foot two-seat, the merchant's whitewashed. The boards weather
by the house's own `age_state` (L348's FIN-W years). Every dimension is invented and
bounded in docs/LIBERTIES.md L353; nothing is a reading of any particular yard.

WHAT IT REFUSES, and says so on the record:
  * a lot whose buildings leave no yard behind them (`yard_for`'s own reason);
  * a corner where the outbuilding would come within `CLEAR_M` of a committed footprint or
    a wagon already standing in the yard — the other corner is tried first;
  * a corner where the outbuilding would stand in a doorway (T-1691): the door's clear
    zone is `generate_entrances.doorway_zones()`, the same rectangle
    `tools/measure_doorways.py --gate` holds every placed object out of. A rear corner can
    face a NEIGHBOUR's front door where a lot runs behind a cross-street roof, and that
    door moves when the house's own fabric does — so the dealer asks, rather than the
    gate finding a privy on somebody's step after the fact. The other corner is tried first;
  * the dwellings standing off the platted lots. They have no lot line to put an alley
    behind, and inventing one is a different claim; they are counted, not drawn.

AND THE BACK OF EVERY CORE STORE'S LOT (T-3605, the owner 2026-11-16: *"places in back
of the stores and buildings for horses and wagons and loading and maybe there are workshops
based on what kind of business it is"*). The commercial core's reconstructed row stores
(`recon_1835_core_*`) name no firm and no household, so the two rules above never reached
them. Each now gets ONE outbuilding in the ground behind it, dealt by the store's own
family (`BACK_LOT`): a stable for the two-storey store and the boarding house, a workshop
for the store-residence, a storehouse for the small shop. The stable stands at the back of
the lot and the others a few steps behind the back door; `LOADING_M` of ground is always
kept clear at the back wall, where the goods came in. The search is fixed — stations along
the back lot from the far end or the near end, square behind the store first and then slid
along its back — and refuses the same things the corners refuse, plus another lot's line.

AND WELLS. T-1212 asks for *"a well where the lot's household class and the wells research
allow"*. `docs/RESEARCH/wells.md` § 4 refuses a well CLASS for the town — July 1835 drank
from the lake by cart — and that ruling stands; the layer it drove (`data/wells/`) draws
places, not a distribution. So this record deals no well and says so in `wells`.

Run with no arguments to write `data/yard/town_yard_outbuildings.json`; `--check`
re-derives it and diffs, writing nothing (tools/check.sh runs that).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import generate_lot_line_fences as fences  # noqa: E402
from generate_dooryard_pickets import convex_overlap, footprint_world, poly_contains  # noqa: E402
import generate_entrances  # noqa: E402  (T-1691: no outbuilding in a doorway)
import enclosure_owners  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUT = DATA / "yard" / "town_yard_outbuildings.json"
TRADE_GOODS = DATA / "yard" / "town_trade_goods.json"

REAR_INSET_M = 0.75   # an outbuilding's back stands this far inside the rear lot line
SIDE_INSET_M = 0.75   # and its side this far inside the side lot line
CLEAR_M = 0.60        # how close it may come to a committed wall
WAGON_CLEAR_M = 2.5   # and to a wagon already standing in the yard

DWELLING_ARCHETYPES = ("frame_dwelling", "log_dwelling", "frame_tavern", "masonry_house")
KEEPER_WORDS = ("tavern", "inn", "hotel", "boarding")
HORSE_CLASSES = ("merchant", "keeper", "freight")
HORSE_OCCUPATIONS = ("teamster", "carter", "drayman")
PRIVY_WORDS = ("privy",)
STABLE_WORDS = ("stable", "barn", "carriage")

# THE PRIVY BY CLASS: [along, depth, low eave, high eave] in metres, and its finish. Sizes
# are the common one- and two-seat boxes of the period's builders' guides, in round feet:
# 3½ ft, 4 ft, 5 × 4 ft. INVENTED, bounded in L353.
PRIVY = {
    "labourer":  {"size": [1.07, 1.07, 1.85, 2.05], "finish": "slab"},
    "tradesman": {"size": [1.22, 1.22, 1.95, 2.20], "finish": "board"},
    "freight":   {"size": [1.22, 1.22, 1.95, 2.20], "finish": "board"},
    "yard":      {"size": [1.22, 1.22, 1.95, 2.20], "finish": "board"},
    "works":     {"size": [1.22, 1.22, 1.95, 2.20], "finish": "board"},
    "keeper":    {"size": [1.52, 1.22, 2.00, 2.30], "finish": "board"},
    "merchant":  {"size": [1.52, 1.22, 2.00, 2.30], "finish": "whitewash"},
}
# THE STABLE: [along, depth, eave, ridge] — a gabled board-and-batten stable, ridge running
# along. A keeper's holds a traveller's horses as well as his own, so it is the bigger.
STABLE = {
    "keeper":   {"size": [6.10, 4.27, 2.60, 4.10], "stalls": 4},
    "merchant": {"size": [4.88, 3.66, 2.45, 3.75], "stalls": 2},
    "freight":  {"size": [4.88, 3.66, 2.45, 3.75], "stalls": 2},
    "teamster": {"size": [4.88, 3.66, 2.45, 3.75], "stalls": 2},
}
WEATHER = {"new": "fresh", "recent": "seasoned", "established": "weathered",
           "older_frontier": "grey"}

# THE BACK OF EVERY CORE STORE'S LOT (T-3605). The owner, 2026-11-16, of the commercial
# core's row of reconstructed stores: *"I could see places in back of the stores and
# buildings for horses and wagons and loading and maybe there are workshops based on what
# kind of business it is but those areas behind the stores I imagine some would be divided
# into work areas and others might be horse and wagons storage but check my history on
# this so it is all accurate"*. His history is T-1212 (a stable for the households that
# kept a horse, goods by trade) and the 2026-08-27 business-front clause (a store at the
# street with its own ground behind it). The core stores (`recon_1835_core_*`) name no
# firm and no household, so neither rule reached them and the ground behind them stood
# bare. No source names what stood behind any of them; the store's own FAMILY is the only
# thing the town knows about the business, so the family's crosswalk entry decides:
#   * C3, the narrow two-storey store, carries the freight-opening vocabulary — the
#     wholesale and forwarding trade that kept a horse and a wagon: a stable at the back of
#     the lot, the ground between it and the back door left open as the wagon and loading
#     yard;
#   * H3, the boarding house, a keeper's stable (T-1212 lists the boarding houses);
#   * C2, the store-residence ("shop below; attic rooms; rear lean-to"), the
#     tradesman-shopkeeper's work room: a workshop a few steps behind the back door;
#   * C1, the small shop, grocery or land office: a storehouse for its stock, where goods
#     came off a cart at the back door.
# Every one is reconstructed and claimed in docs/LIBERTIES.md L-store-back-lots-3605.
STORE_PREFIX = "recon_1835_core_"
BACK_LOT = {
    "C3": {"kind": "stable", "end": "far", "size": STABLE["merchant"]["size"],
           "stalls": STABLE["merchant"]["stalls"], "roof": "gable",
           "finish": "board_and_batten",
           # a row store's back lot can be narrower than a two-stall stable; one stall
           # (12 ft square) is the stable a narrow lot was given instead
           "narrow": {"size": [3.66, 3.66, 2.45, 3.60], "stalls": 1},
           "use": ("horse and wagon: a stable at the back of the lot; the ground between "
                   "it and the store's back door is the wagon and loading yard")},
    "H3": {"kind": "stable", "end": "far", "size": STABLE["keeper"]["size"],
           "stalls": STABLE["keeper"]["stalls"], "roof": "gable",
           "finish": "board_and_batten",
           "use": "the boarding house's stable at the back of the lot, for its boarders' horses"},
    "C2": {"kind": "workshop", "end": "near", "size": [3.66, 3.05, 2.30, 2.90],
           "roof": "shed", "finish": "board",
           "use": "a work room: the tradesman-shopkeeper's workshop behind the back door"},
    "C1": {"kind": "storehouse", "end": "near", "size": [3.05, 2.44, 2.15, 2.60],
           "roof": "shed", "finish": "board",
           "use": "a storehouse for the shop's stock, unloaded at the back door"},
}
LOADING_M = 4.0       # clear ground kept at a store's back wall, where goods came in
BACK_REACH_M = 40.0   # how far behind the store its back lot is searched
BACK_STEP_M = 0.5     # the search step along the back lot
LOT_INSET_M = 0.75    # an outbuilding stands this far inside every line of its lot
WALL_ROOM_M = 2.0     # and this far off any other building's wall, which keeps its
                      # woodpile's room (tools/generate_woodpiles.py stacks against walls)


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def text_of(v) -> str:
    v = v.get("value") if isinstance(v, dict) else v
    return (v or "").strip().lower() if isinstance(v, str) else ""


def function_of(sc) -> str:
    return text_of((sc.get("attributes") or {}).get("function"))


NOT_A_HOME = ("meeting", "church", "school", "council", "office", "agency", "store_only")


def is_dwelling(sc) -> bool:
    if sc.get("archetype") in DWELLING_ARCHETYPES:
        # The archetype is a building's FORM; a frame meeting house is built like a house
        # and nobody lives in it.
        return not any(w in function_of(sc) for w in NOT_A_HOME)
    if sc.get("archetype") == "frame_storefront":
        fn = function_of(sc)
        return "residence" in fn or "dwelling" in fn
    if sc.get("archetype") == "outbuilding":
        fn = function_of(sc)
        return fn == "dwelling" or "dwelling_or_shanty" in fn
    return False


def class_of(sc) -> tuple[str, str]:
    """The household class a house's yard is dealt by, and where it was read."""
    rec = sc.get("reconstruction") or {}
    k = (rec.get("fabric_basis") or {}).get("class")
    if k:
        return k, "fabric_basis.class (L330)"
    fn = function_of(sc)
    if any(w in fn for w in KEEPER_WORDS):
        return "keeper", f"its function, {fn}"
    if "store" in fn or "merchant" in fn or "trading" in fn:
        return "merchant", f"its function, {fn}"
    if sc.get("archetype") == "log_dwelling":
        return "labourer", "its archetype, log_dwelling"
    return "tradesman", "no class on the record; the town's commonest house"


def keeps_horse(sc, klass: str) -> str | None:
    """Why this household kept a horse, or None."""
    occ = text_of((sc.get("reconstruction") or {}).get("occupation"))
    if any(w in occ for w in HORSE_OCCUPATIONS):
        return "teamster"
    if any(w in function_of(sc) for w in KEEPER_WORDS):
        return "keeper"
    if klass in HORSE_CLASSES:
        return klass
    return None


def rect(cu, cv, half_u, half_v, ud, vd):
    """A rectangle in ENU from its centre and half-extents in the lot's own (u, v) frame."""
    out = []
    for a, b in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
        out.append((cu[0] + ud[0] * a * half_u + vd[0] * b * half_v,
                    cu[1] + ud[1] * a * half_u + vd[1] * b * half_v))
    return out


def yard_wagons() -> list[tuple[float, float]]:
    if not TRADE_GOODS.exists():
        return []
    return [tuple(w["at_local_enu_m"]) for w in load(TRADE_GOODS).get("wagons", [])
            if isinstance(w.get("at_local_enu_m"), list)]


def bearing_deg(out_enu) -> float:
    """The layer's own frame (yard.js): along the face is (cos b, sin b) in world XZ and
    out of it is (sin b, -cos b), world z being -north. So for an ENU outward unit vector
    (ox, oy), along is (oy, -ox) in ENU, i.e. (oy, ox) in world XZ."""
    ox, oy = out_enu
    return round(math.degrees(math.atan2(ox, oy)), 2)


def place(entry, yard, which: int, along: float, depth: float, blockers, wagons,
          doors=()):
    """Centre of an outbuilding in rear corner `which` (0 or 1), or None and why."""
    poly = yard["poly"]
    ra, rb = yard["rear"]
    corner = poly[ra] if which == 0 else poly[rb]
    other = poly[rb] if which == 0 else poly[ra]
    width = yard["width"]
    ud = ((other[0] - corner[0]) / width, (other[1] - corner[1]) / width)
    # Inward, toward the street: the lot's own front-to-rear axis, reversed.
    fa, fb = fences.lot_edges(entry["block"], entry["lot"])[0]
    fm = ((poly[fa][0] + poly[fb][0]) / 2, (poly[fa][1] + poly[fb][1]) / 2)
    rm = ((poly[ra][0] + poly[rb][0]) / 2, (poly[ra][1] + poly[rb][1]) / 2)
    dl = math.hypot(fm[0] - rm[0], fm[1] - rm[1])
    vd = ((fm[0] - rm[0]) / dl, (fm[1] - rm[1]) / dl)
    u = SIDE_INSET_M + along / 2
    v = REAR_INSET_M + depth / 2
    c = (corner[0] + ud[0] * u + vd[0] * v, corner[1] + ud[1] * u + vd[1] * v)
    if yard["v_of"](c) - depth / 2 < yard["v_start"] - 1e-6 - fences.REAR_CLEAR_M + CLEAR_M:
        return None, f"{depth:.2f} m deep will not stand behind the house"
    shape = rect(c, ud, along / 2, depth / 2, ud, vd)
    if not all(poly_contains(p, poly) for p in shape):
        return None, "it would cross the lot's own line"
    grown = rect(c, ud, along / 2 + CLEAR_M, depth / 2 + CLEAR_M, ud, vd)
    for fp, bb in blockers:
        if fences.bbox_apart(fences.bbox(grown), bb, 0.0):
            continue
        if convex_overlap(grown, fp):
            return None, "a committed building stands in that corner"
    for w in wagons:
        if math.hypot(w[0] - c[0], w[1] - c[1]) < WAGON_CLEAR_M + max(along, depth) / 2:
            return None, "a wagon already stands in that corner"
    for ring, bb in doors:
        if fences.bbox_apart(fences.bbox(shape), bb, 0.0):
            continue
        if convex_overlap(shape, ring):
            return None, "a door opens onto that corner"
    return {"at": c, "out": vd, "shape": shape}, None


def corner_order(lot_id: str) -> list[int]:
    h = int(hashlib.sha256(lot_id.encode()).hexdigest()[:8], 16)
    return [h % 2, 1 - h % 2]


def build():
    entries, sidecars = fences.survey()
    homes, works = enclosure_owners.household_links()
    footprints = []
    for sid, sc in sidecars.items():
        fp = footprint_world(sc)
        if len(fp) >= 3:
            footprints.append((fp, fences.bbox(fp)))
    wagons = yard_wagons()
    doors = [(ring, fences.bbox(ring)) for _, ring in generate_entrances.doorway_zones()]

    out, refused, stats = [], [], {"dwelling_lots": 0, "privies": 0, "stables": 0,
                                   "privy_standing": 0, "stable_standing": 0,
                                   "horse_households": 0}
    on_plat = set()
    for e in entries:
        lot_id = f"{e['block']['id']}_lot{e['index']}"
        on_plat.update(e["buildings"])
        here = [(s, sidecars[s]) for s in e["buildings"]]
        houses = [(s, sc) for s, sc in here if is_dwelling(sc)]
        if not houses:
            continue
        stats["dwelling_lots"] += 1
        yard, why = fences.yard_for(e)
        # The house the yard belongs to: the one nearest the street, which is the one the
        # yard stands behind (yard_for measures from the same building).
        if yard:
            houses.sort(key=lambda h: min(yard["v_of"](p) for p in footprint_world(h[1])))
        house_id, house = houses[0]
        klass, read_from = class_of(house)
        households = []
        for s, _ in houses:
            households += [{"id": hh, "held_as": "home", "at": s} for hh in homes.get(s, [])]
        has_privy = any(any(w in function_of(sc) for w in PRIVY_WORDS) for _, sc in here)
        has_stable = any(any(w in function_of(sc) for w in STABLE_WORDS) for _, sc in here)
        horse = keeps_horse(house, klass)
        stats["horse_households"] += 1 if horse else 0
        stats["privy_standing"] += 1 if has_privy else 0
        stats["stable_standing"] += 1 if (horse and has_stable) else 0
        wants = [] if has_privy else ["privy"]
        if horse and not has_stable:
            wants.append("stable")
        if not wants:
            continue
        if not yard:
            for kind in wants:
                refused.append({"lot": lot_id, "kind": kind, "belongs_to": house_id,
                                "why": f"no yard: {why}"})
            continue
        age = (house.get("reconstruction") or {}).get("age_state") or "established"
        taken = []
        for kind in wants:
            if kind == "privy":
                p = PRIVY.get(klass, PRIVY["tradesman"])
                size, extra = p["size"], {"finish": p["finish"]}
            else:
                s = STABLE[horse if horse in STABLE else "merchant"]
                size, extra = s["size"], {"finish": "board_and_batten", "stalls": s["stalls"]}
            spot, whys = None, []
            for which in corner_order(lot_id):
                if which in taken:
                    continue
                spot, w = place(e, yard, which, size[0], size[1], footprints, wagons,
                                doors)
                if spot:
                    taken.append(which)
                    break
                whys.append(w)
            if not spot:
                refused.append({"lot": lot_id, "kind": kind, "belongs_to": house_id,
                                "why": "; ".join(dict.fromkeys(whys))})
                continue
            stats["privies" if kind == "privy" else "stables"] += 1
            item = {
                "id": f"{kind}_{lot_id}",
                "kind": kind,
                "lot": lot_id,
                "belongs_to": house_id,
                "households": households,
                "household_class": klass,
                "class_read_from": read_from,
                "at_local_enu_m": [round(spot["at"][0], 2), round(spot["at"][1], 2)],
                "bearing_deg": bearing_deg(spot["out"]),
                "along_m": size[0],
                "depth_m": size[1],
                "eave_m": size[2],
                "head_m": size[3],
                "roof": "shed" if kind == "privy" else "gable",
                "weather": WEATHER.get(age, "weathered"),
                "confidence": "reconstructed",
            }
            item.update(extra)
            if kind == "stable":
                item["kept_a_horse_because"] = horse
            out.append(item)

    store_items, store_refused = store_back_lots(entries, sidecars, footprints, wagons,
                                                 doors, out)
    for it in store_items:
        stats["store_" + it["kind"] + "s"] = stats.get("store_" + it["kind"] + "s", 0) + 1
    stats["store_back_lots"] = len(store_items)
    out += store_items
    refused += store_refused
    off_plat = sorted(s for s, sc in sidecars.items()
                      if s not in on_plat and is_dwelling(sc))
    return out, refused, stats, off_plat


def item_shape(ob) -> list[tuple[float, float]]:
    """An outbuilding's ground rectangle from its own record (the yard.js frame)."""
    b = math.radians(ob["bearing_deg"])
    # bearing_deg's inverse: out (ENU) is (sin b, cos b) and along is (cos b, -sin b).
    out = (math.sin(b), math.cos(b))
    al = (math.cos(b), -math.sin(b))
    return rect(tuple(ob["at_local_enu_m"]), al, ob["along_m"] / 2, ob["depth_m"] / 2,
                al, out)


def store_back_lots(entries, sidecars, footprints, wagons, doors, placed):
    """T-3605: the back of each core store's lot, dealt by the store's own family."""
    items, refused = [], []
    taken = [(item_shape(ob), fences.bbox(item_shape(ob))) for ob in placed]

    def hits(shape, against) -> bool:
        bb = fences.bbox(shape)
        return any(not fences.bbox_apart(bb, b, 0.0) and convex_overlap(shape, f)
                   for f, b in against)

    def search(frame, size, end, lots, whys):
        """The first clear stand for an outbuilding of `size` in the store's back lot."""
        c0, back, front, ud, v_rear, u_lo, u_hi = frame
        along, depth = size[0], size[1]
        first = v_rear + LOADING_M + depth / 2
        last = v_rear + BACK_REACH_M - depth / 2
        stations = [first + i * BACK_STEP_M for i in range(int((last - first) / BACK_STEP_M) + 1)]
        if end == "far":
            stations.reverse()
        # Square behind the store first, then slid along its back, never so far that its
        # middle leaves the store's own width: a row store's back lot can straddle a
        # platted lot line, and an outbuilding does not.
        u_mid = (u_lo + u_hi) / 2
        slides = [0.0] + [d * k * BACK_STEP_M for k in range(1, 40) for d in (1, -1)]
        slides = [d for d in slides if u_lo <= u_mid + d <= u_hi]
        for v in stations:
            for du in slides:
                u = u_mid + du
                c = (c0[0] + back[0] * v + ud[0] * u, c0[1] + back[1] * v + ud[1] * u)
                shape = rect(c, ud, along / 2, depth / 2, ud, front)
                inset = rect(c, ud, along / 2 + LOT_INSET_M, depth / 2 + LOT_INSET_M,
                             ud, front)
                home = next((i for i, lot in enumerate(lots)
                             if all(poly_contains(p, lot) for p in inset)), None)
                if home is None:
                    whys.append("off its lot")
                    continue
                grown = rect(c, ud, along / 2 + WALL_ROOM_M, depth / 2 + WALL_ROOM_M,
                             ud, front)
                if hits(grown, footprints):
                    whys.append("a committed building stands there")
                    continue
                if hits(rect(c, ud, along / 2 + CLEAR_M, depth / 2 + CLEAR_M, ud, front),
                        taken):
                    whys.append("another outbuilding stands there")
                    continue
                if any(math.hypot(w[0] - c[0], w[1] - c[1]) < WAGON_CLEAR_M
                       + max(along, depth) / 2 for w in wagons):
                    whys.append("a wagon stands there")
                    continue
                if hits(shape, doors):
                    whys.append("a door opens onto it")
                    continue
                return c, home, shape
        return None

    for e in entries:
        lots = [lot["polygon"] for lot in e["block"]["lots"]]
        lot_id = f"{e['block']['id']}_lot{e['index']}"
        for sid in e["buildings"]:
            if not sid.startswith(STORE_PREFIX):
                continue
            sc = sidecars[sid]
            rec = sc.get("reconstruction") or {}
            fam = rec.get("family")
            spec = BACK_LOT.get(fam)
            if not spec:
                continue
            fp = footprint_world(sc)
            r = math.radians((sc.get("placement") or {}).get("rotation_deg") or 0.0)
            # The store faces its street along (sin r, cos r), a compass bearing; its back
            # lot runs the other way, and `along` is square to that.
            front = (math.sin(r), math.cos(r))
            back = (-front[0], -front[1])
            ud = (math.cos(r), -math.sin(r))
            c0 = (sum(p[0] for p in fp) / len(fp), sum(p[1] for p in fp) / len(fp))
            vs = [(p[0] - c0[0]) * back[0] + (p[1] - c0[1]) * back[1] for p in fp]
            us = [(p[0] - c0[0]) * ud[0] + (p[1] - c0[1]) * ud[1] for p in fp]
            frame = (c0, back, front, ud, max(vs), min(us), max(us))
            tries = [(spec["size"], spec.get("stalls"))]
            if "narrow" in spec:
                tries.append((spec["narrow"]["size"], spec["narrow"]["stalls"]))
            spot, whys = None, []
            for size, stalls in tries:
                spot = search(frame, size, spec["end"], lots, whys)
                if spot:
                    break
            if not spot:
                refused.append({"lot": lot_id, "kind": spec["kind"], "belongs_to": sid,
                                "why": "; ".join(dict.fromkeys(whys)) or "no ground"})
                continue
            c, home, shape = spot
            taken.append((shape, fences.bbox(shape)))
            along, depth, eave, head = size
            age = rec.get("age_state") or "established"
            item = {
                "id": f"{spec['kind']}_{sid}",
                "kind": spec["kind"],
                "lot": f"{e['block']['id']}_lot{home}",
                "belongs_to": sid,
                "households": [],
                "household_class": (rec.get("fabric_basis") or {}).get("class") or "merchant",
                "class_read_from": "fabric_basis.class (L330)",
                "store_family": fam,
                "back_lot_use": spec["use"],
                "at_local_enu_m": [round(c[0], 2), round(c[1], 2)],
                "bearing_deg": bearing_deg(front),
                "along_m": along,
                "depth_m": depth,
                "eave_m": eave,
                "head_m": head,
                "roof": spec["roof"],
                "weather": WEATHER.get(age, "weathered"),
                "confidence": "reconstructed",
                "finish": spec["finish"],
            }
            if stalls:
                item["stalls"] = stalls
            items.append(item)
    return items, refused


def record(items, refused, stats, off_plat) -> dict:
    return {
        "id": "town_yard_outbuildings",
        "name": "The yard outbuildings — a privy behind every house, a stable for the horse-keepers",
        "kind": "yard_outbuildings",
        "scene": "1835",
        "target_date": "1835-07-01",
        "generated_by": "tools/generate_yard_outbuildings.py",
        "generated_from": ["data/traces/vectors/thompson_lots.json",
                           "data/sidecars/1835/*.json", "data/residents/index.json",
                           "data/yard/town_trade_goods.json"],
        "existence": {
            "confidence": "reconstructed",
            "note": ("A privy stood behind every town house of 1835 — there was no other "
                     "arrangement to be had before sewers — and a household that kept a "
                     "horse stabled it on its own lot. That much is the norm of the period, "
                     "not a reading of any yard here; WHICH corner, what size and what "
                     "finish are dealt by rule from the house's own class and age. "
                     "docs/LIBERTIES.md L353. Behind each of the commercial core's "
                     "reconstructed row stores stands one more outbuilding, dealt by the "
                     "store's own family — a stable, a workshop or a storehouse — with the "
                     "ground at its back door left open for loading; no source names what "
                     "stood behind any of them. docs/LIBERTIES.md L-store-back-lots-3605."),
        },
        "rule": {
            "privy": "every dwelling lot with a yard behind the house and no committed privy",
            "stable": ("a dwelling lot whose house's class is merchant, keeper or freight, "
                       "whose house is a tavern, inn, hotel or boarding house, or whose "
                       "occupation is a teamster's — and that has no committed stable, barn "
                       "or carriage shed"),
            "where": (f"a rear corner, its back {REAR_INSET_M} m inside the rear lot line "
                      f"(off the alley) and {SIDE_INSET_M} m in from the side line, at least "
                      f"{CLEAR_M} m clear of every committed wall; the corner is chosen by a "
                      "hash of the lot id and the other is tried when it is taken"),
            "size_by_class": {k: v for k, v in PRIVY.items()},
            "stable_by_reason": {k: v for k, v in STABLE.items()},
            "weather_by_age_state": WEATHER,
            "store_back_lot": {
                "applies_to": f"the commercial core's row stores ({STORE_PREFIX}*), T-3605",
                "by_family": {k: {kk: vv for kk, vv in v.items()} for k, v in BACK_LOT.items()},
                "where": (f"behind the store, its door side toward the store's back wall, "
                          f"{LOADING_M} m of loading ground kept clear at that wall; a stable "
                          f"at the back of the lot, the rest as near the store as is clear; "
                          f"at least {LOT_INSET_M} m inside every lot line and {WALL_ROOM_M} m "
                          "clear of every committed wall (a woodpile's room); searched within "
                          f"{BACK_REACH_M} m of the store in {BACK_STEP_M} m steps"),
                "liberty": "docs/LIBERTIES.md L-store-back-lots-3605",
            },
        },
        "wells": ("None dealt. docs/RESEARCH/wells.md § 4 refuses a well class for the town "
                  "— July 1835 Chicago drank from the lake by cart — and that ruling stands; "
                  "data/wells/ draws only the wells a source places."),
        "counts": {**stats, "refused": len(refused), "dwellings_off_plat": len(off_plat)},
        "dwellings_off_plat_note": ("Dwellings standing on no platted lot have no lot line "
                                    "to put an alley behind; they are counted, not drawn."),
        "outbuildings": items,
        "refused": refused,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true", help="re-derive and diff, write nothing")
    args = ap.parse_args()
    items, refused, stats, off_plat = build()
    text = json.dumps(record(items, refused, stats, off_plat), indent=2,
                      ensure_ascii=False) + "\n"
    if args.check:
        have = OUT.read_text(encoding="utf-8") if OUT.exists() else ""
        if have != text:
            print(f"FAIL {OUT.relative_to(ROOT)} does not re-derive — run "
                  "python3 tools/generate_yard_outbuildings.py")
            return 1
        print(f"ok   {OUT.relative_to(ROOT)} re-derives: {stats['privies']} privies, "
              f"{stats['stables']} stables, {stats['store_back_lots']} store back lots, "
              f"{len(refused)} refused")
        return 0
    OUT.write_text(text, encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}: {stats['privies']} privies, "
          f"{stats['stables']} stables, {len(refused)} refused; {stats}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
