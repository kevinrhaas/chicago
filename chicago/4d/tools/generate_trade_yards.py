#!/usr/bin/env python3
"""Generate the goods each WORKING trade kept in its own yard — T-1961.

WHAT THIS IS, AND WHY IT IS A THIRD RECORD RATHER THAN A COLUMN ON THE FIRST.
`tools/generate_yard_goods.py` stands a merchant's stock on his own FRONTAGE, and its
evidence is Ordinance 9 of 7 November 1833 — boxes and barrels in the streets. It
refuses the working trades in writing: *"Several of them plainly kept stuff outside — a
cooperage most of all — but what they kept was tools and material rather than a
merchant's stock on a public frontage, and the rule would be guessing."* It also refuses
every reconstructed trade, because a cask on the footway of an invented shop is an
invention resting on an invention.

T-1212 is the owner's instruction that overrules both, for the yards: *"per business —
the trade goods and vehicles of T-0040 by trade (barrels at the coopers and packers,
wagons at the forwarders and the teamsters, lumber at the joiners, hides at the tannery,
hay at the stables within the hay limits)"*, every record `belongs_to` its business, and
the hay ordinance gate honoured. His standing ruling of 2026-08-18 covers the tier: *"you
are totally fine to be liberal with adding reconstructed items when i ask for things, you
can just label and mark them as such."* So every object here is `reconstructed`, carded
and claimed in `docs/LIBERTIES.md` L351, and WHERE each one stands is a rule.

This is a separate record because it is a separate claim about separate ground: the
frontage goods stand on a public footway in front of a shop; these stand BEHIND or BESIDE
a working building, on its own yard, and nothing here goes in a street.

THE RULE. A structure gets yard goods iff

  1. its `function` is one of the trades in `TRADES` below — the ticket's own list, read
     onto this dataset's vocabulary: casks at the cooperages and the packing and
     slaughter houses, a wagon at the forwarding houses and two at the teamster's yard,
     boards at the carpenters' and joiners' shops, hides at the tannery, a hay rick at the
     stables. NAMED OR RECONSTRUCTED ALIKE — that is the ticket;
  2. it is standing on the scene date (it is in `data/sidecars/1835/index.json`) and has
     a placed footprint;
  3. FOR HAY ONLY: the rick stands OUTSIDE the ring `data/reconstruction/
     1835_hay_limits.json` derives from Sec. 22 of the ordinance of 5 August 1835, which
     forbids stacking hay inside it. That ordinance is five weeks after the scene date and
     its own record says so; the owner asked that it be honoured anyway, and the reading
     taken is the conservative one — a stable inside the limits keeps its hay in the mow,
     and no rick is drawn there. Each one is refused in writing below;
  4. its yard has ground clear for the goods (see WHERE).

WHERE THE GOODS STAND is searched, not chosen, and the search is fixed. The faces are
tried REAR first, then the two SIDES — never the front, which is the street's and the
frontage layer's. On each face the goods stand square to the wall, their ground starting
`WALL_GAP_M` out from it, at the face's middle and then at fixed steps along it, at three
fixed depths out. The first stand whose ground passes every refusal is kept. A stand is
refused if its ground reaches within `WALL_CLEAR_M` of ANY committed footprint (its own
included), onto a plank walk, into a fenced garden or pen, into a street's travelled
track, onto a wharf deck or a beached hull, below the water surface or off the modelled
ground — the same world `generate_yard_goods.py` reads for its wagons, read once — or
within `KEEP_CLEAR_M` of any goods or wagon already standing, on either record. That last
margin is the smoke's own: `tools/smoke_renderer.mjs` claims every yard vertex within 2.6
m of a pile's anchor for that pile, so two things closer than that would be measured
against each other's anchors.

HOW MUCH is a fixed count per trade and not a lottery: a cooper's rank of six finished
casks; a packer's rank of eight pork barrels; one pile of boards at a joiner's; two
drying rails of hides at the tannery; one rick at a stable; one farm wagon at a
forwarding house; a farm wagon and a covered wagon at the teamster's yard.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "generators"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import generate_yard_goods as goods  # noqa: E402

ROOT = goods.ROOT
DATA = goods.DATA
OUT = DATA / "yard" / "town_trade_yards.json"
HAY_LIMITS = DATA / "reconstruction" / "1835_hay_limits.json"

# trade -> (what, why). `what` picks the deal below; `why` is printed on the record.
TRADES = {
    "cooperage": ("casks", "a cooper's finished casks stand in his yard until they are "
                  "carted to the packers and the wharves"),
    "packing_house": ("barrels", "a packer's barrels of pork and beef stand headed and "
                      "branded in the yard before they go to the wharf"),
    "slaughterhouse_packing": ("barrels", "a packer's barrels of pork and beef stand "
                               "headed and branded in the yard before they go to the "
                               "wharf"),
    "warehouse_and_slaughter_yard": ("barrels", "a packer's barrels of pork and beef "
                                     "stand headed in the yard before they go to the "
                                     "wharf"),
    "forwarding_and_commission_store": ("wagon", "a forwarder's goods came and went by "
                                        "wagon, and one stands in the yard"),
    "forwarding_commission_warehouse": ("wagon", "a forwarder's goods came and went by "
                                        "wagon, and one stands in the yard"),
    "stable_and_wagon_yard": ("teamster", "a teamster's yard is where his wagons stand "
                              "between hauls, and his stable keeps its hay"),
    "carpenter_or_joiner_shop": ("boards", "a joiner's boards are stacked and stickered "
                                 "in the yard to season"),
    "tannery": ("hides", "a tanner's hides hang over rails in the yard to dry"),
    "stable": ("hay", "a stable's hay stands in a rick outside it"),
    "hotel_stable": ("hay", "a stable's hay stands in a rick outside it"),
    "tavern_stable": ("hay", "a stable's hay stands in a rick outside it"),
}
WAGON_WORDS = {"farm_box": "farm wagon", "covered": "covered freight wagon"}

# Hay is the one deal a stand can also be refused for by the ordinance; a teamster's
# stable gets its rick on the same terms as any other.

# --- the goods' own forms (every one INVENTED; see `form` on the record) ---------- #
BARREL_PITCH_M = goods.BARREL_PITCH_M        # 0.62 m centre to centre, the frontage's
COOPER_RANK = (3, 2)                         # along x out
PACKER_RANK = (4, 2)
BOARD_M = (3.66, 0.30, 0.05)                 # 12 ft x 12 in x 2 in
BOARD_PILE = (3, 6, 0.05)                    # boards a course, courses, sticker depth
BOARD_GAP_M = 0.03
HIDE_RAIL_M = (2.4, 1.5, 0.08)               # length, height of the rail, rail square
HIDE_M = (0.55, 1.0, 0.012)                  # width along the rail, drop, thickness
HIDES_PER_RAIL = 3
HAY_RICK_M = (3.0, 2.0, 1.5, 2.4)            # length, width, eave, ridge

# --- the search ------------------------------------------------------------------ #
WALL_GAP_M = 1.2           # air between the wall and the goods' own ground
WALL_CLEAR_M = 1.0         # and between that ground and ANY committed footprint
KEEP_CLEAR_M = 2.6         # between this ground and any goods or wagon already standing
FENCE_CLEAR_M = 0.3        # and between it and any fence run
ALONG_STEPS_M = (0.0, -2.5, 2.5, -5.0, 5.0)
OUT_STEPS_M = (0.0, 1.5, 3.0)
FACES = ("rear", "left side", "right side")


def _round(x: float, places: int = 2) -> float:
    return goods._round(x, places)


def _hay_ring() -> list:
    return [tuple(p) for p in goods._load(HAY_LIMITS)["ring_local_enu_m"]]


def _faces(poly: list, place: dict):
    """(name, centre on the wall in ENU, outward bearing, wall length) for each face.

    Read in the footprint's own frame — `v` toward the street, `u` along it, the frame
    `docs/GLB-CONTRACT.md` fixes — and carried to ENU through `_to_enu`, so the outward
    bearing is MEASURED off two transformed points rather than reasoned from a sign.
    """
    u0 = min(p[0] for p in poly)
    u1 = max(p[0] for p in poly)
    v0 = min(p[1] for p in poly)
    v1 = max(p[1] for p in poly)
    um, vm = (u0 + u1) / 2, (v0 + v1) / 2
    out = []
    for name, (cu, cv), (du, dv), length in (
            ("rear", (um, v0), (0.0, -1.0), u1 - u0),
            ("left side", (u0, vm), (-1.0, 0.0), v1 - v0),
            ("right side", (u1, vm), (1.0, 0.0), v1 - v0)):
        a = goods._to_enu(cu, cv, place)
        b = goods._to_enu(cu + du, cv + dv, place)
        bearing = math.degrees(math.atan2(b[0] - a[0], b[1] - a[1])) % 360.0
        out.append((name, a, bearing, length))
    return out


def _frame(bearing: float):
    """Out of the wall (sin b, cos b) and along it (cos b, -sin b), in ENU — the frame
    `yard.js` draws every barrel, stack and pile in."""
    b = math.radians(bearing)
    return (math.sin(b), math.cos(b)), (math.cos(b), -math.sin(b))


def _grow(quad: list, by: float) -> list:
    """A convex quad grown outward by `by` metres along its own diagonals' directions."""
    ce = sum(p[0] for p in quad) / 4.0
    cn = sum(p[1] for p in quad) / 4.0
    out = []
    for e, n in quad:
        d = math.hypot(e - ce, n - cn) or 1.0
        out.append((e + (e - ce) / d * by * math.sqrt(2), n + (n - cn) / d * by * math.sqrt(2)))
    return out


def _quad(e: float, n: float, bearing: float, length: float, depth: float,
          grow: float = 0.0) -> list:
    out, along = _frame(bearing)
    hl, hd = length / 2 + grow, depth / 2 + grow
    return [(e + along[0] * a + out[0] * d, n + along[1] * a + out[1] * d)
            for a, d in ((-hl, -hd), (hl, -hd), (hl, hd), (-hl, hd))]


def _fence_runs() -> list:
    """Every committed fence run, as (record id, polyline) — a pile does not stand
    astride a fence, whichever side of it the yard is on."""
    runs = []
    for path in sorted(goods.ENCLOSURES.glob("*.json")):
        if path.name == "index.json":
            continue
        rec = goods._load(path)
        for run in rec.get("runs", []):
            pts = [tuple(p) for p in (run.get("path_local_enu_m") or [])]
            if len(pts) >= 2:
                runs.append((rec.get("id") or path.stem, pts))
    return runs


def _crosses(quad: list, path: list) -> bool:
    """Does a polyline enter a convex quad — a vertex inside it, or an edge through it?"""
    if any(goods._poly_contains(p, quad) for p in path):
        return True

    def ccw(a, b, c):
        return (c[1] - a[1]) * (b[0] - a[0]) > (b[1] - a[1]) * (c[0] - a[0])

    for i in range(len(path) - 1):
        a, b = path[i], path[i + 1]
        for j in range(4):
            c, d = quad[j], quad[(j + 1) % 4]
            if ccw(a, c, d) != ccw(b, c, d) and ccw(a, b, c) != ccw(a, b, d):
                return True
    return False


def _refusal(quad: list, world: dict, taken: list) -> str | None:
    """Why this ground may not hold goods, or None. The same world the wagons are
    refused against, worded for a pile rather than a vehicle."""
    pts = list(quad) + [(sum(p[0] for p in quad) / 4.0, sum(p[1] for p in quad) / 4.0)]
    hf = world["hf"]
    inset = goods.TOWN_EDGE_INSET_M
    for p in pts:
        if not (hf.origin_e + inset <= p[0] <= hf.origin_e + (hf.cols - 1) * hf.cell_m - inset
                and hf.origin_n + inset <= p[1]
                <= hf.origin_n + (hf.rows - 1) * hf.cell_m - inset):
            return "it reaches off the modelled ground."
        if hf.height(p[0], p[1]) < world["water_m"] + goods.TOWN_DRY_M:
            return "its ground is in the water or within 0.60 m of it."
    for sid, poly in world["walls"]:
        if any(goods._dist_to_polygon(p, poly) < WALL_CLEAR_M for p in pts):
            return f"it reaches within {WALL_CLEAR_M:.2f} m of {sid}'s committed footprint."
    for a, b, half, wid in world["walks"]:
        if any(goods._dist_to_path(p, [a, b]) < half + goods.TOWN_WALK_CLEAR_M
               for p in pts):
            return f"it stands on the plank walk {wid}."
    for interior in world["fenced"]:
        if interior["treatment"] == goods.WORKING_YARD_TREATMENT:
            continue
        if any(goods._poly_contains(p, interior["ring"]) for p in pts):
            return (f"it stands inside {interior['record']}, whose ground is "
                    f"{interior['treatment']} — a garden or a pen, not a working yard.")
    for rid, path in world["runs"]:
        if _crosses(_grow(quad, FENCE_CLEAR_M), path):
            return f"a fence run of {rid} passes through it."
    for st in world["streets"]:
        if any(goods._dist_to_path(p, st["path"])
               < st["track_w"] / 2 + goods.TOWN_TRACK_CLEAR_M - 1e-6 for p in pts):
            return f"it reaches into the {st['name']} travelled track."
    for deck in world["decks"]:
        if any(goods._dist_to_polygon(p, deck) < goods.TOWN_WHARF_CLEAR_M for p in pts):
            return "it stands on a committed wharf deck."
    for hull in world["hulls"]:
        if math.hypot(pts[-1][0] - hull[0], pts[-1][1] - hull[1]) < goods.TOWN_HULL_CLEAR_M:
            return "it stands on a hull drawn up on the bank."
    for what, other in taken:
        if goods._quads_overlap(quad, other):
            return (f"it stands within {KEEP_CLEAR_M:.2f} m of {what} already standing "
                    "there.")
    return None


def _search(poly, place, length, depth, world, taken, skip_faces=()):
    """The first clear stand, searched in a fixed order, and every reason on the way."""
    last = None
    for name, (we, wn), bearing, wall in _faces(poly, place):
        if name in skip_faces:
            continue
        out, along = _frame(bearing)
        for d in OUT_STEPS_M:
            for s in ALONG_STEPS_M:
                if abs(s) + length / 2 > wall / 2 + 2.5:
                    continue
                off = WALL_GAP_M + d + depth / 2
                e = we + out[0] * off + along[0] * s
                n = wn + out[1] * off + along[1] * s
                why = _refusal(_quad(e, n, bearing, length, depth), world, taken)
                if why is None:
                    return {"face": name, "e": e, "n": n, "bearing": bearing,
                            "out_m": off, "along_m": s}, None
                last = f"{name}: {why}"
    return None, last


def _at(stand, along: float, out: float) -> list:
    o, a = _frame(stand["bearing"])
    return [_round(stand["e"] + a[0] * along + o[0] * out),
            _round(stand["n"] + a[1] * along + o[1] * out)]


def _rank(stand, cols: int, rows: int) -> list:
    items = []
    for r in range(rows):
        for c in range(cols):
            items.append({"kind": "barrel", "pose": "upright",
                          "at_local_enu_m": _at(stand, (c - (cols - 1) / 2) * BARREL_PITCH_M,
                                                (r - (rows - 1) / 2) * BARREL_PITCH_M),
                          "bearing_deg": _round(stand["bearing"], 1)})
    return items


def _taken_from(record: dict) -> list:
    """Everything already standing on the goods record, grown by the keep-clear."""
    taken = []
    for f in record.get("frontages", []):
        for it in f.get("items", []):
            e, n = it["at_local_enu_m"]
            taken.append((f"{f['structure_id']}'s frontage goods",
                          _quad(e, n, 0.0, 1.0, 1.0, KEEP_CLEAR_M)))
    for w in record.get("wagons", []):
        taken.append((f"the wagon {w['id']}", goods._wagon_ground(w, KEEP_CLEAR_M)))
    for lot in record.get("lots", []):
        for it in lot.get("items", []):
            e, n = it["at_local_enu_m"]
            taken.append((f"{lot['structure_id']}'s stack",
                          _quad(e, n, 0.0, 4.0, 4.0, KEEP_CLEAR_M)))
    return taken


def build(ids: list, cars: dict):
    world = goods._town_world(cars)
    world["runs"] = _fence_runs()
    ring = _hay_ring()
    taken = []
    for name in ("town_trade_goods.json", "lot_building_material.json",
                 "bridge_head_timber.json", "town_water_cart.json"):
        path = DATA / "yard" / name
        if path.exists():
            taken += _taken_from(goods._load(path))

    lots, wagons, refused = [], [], []
    for sid in ids:
        sc = cars.get(sid)
        if sc is None:
            continue
        fn = (sc.get("attributes") or {}).get("function") or {}
        trade = fn.get("value")
        if trade not in TRADES:
            continue                                            # clause 1
        what, why = TRADES[trade]
        place = sc.get("placement") or {}
        poly = (sc.get("footprint") or {}).get("polygon") or []
        if len(poly) < 3 or place.get("local_e") is None:
            refused.append({"structure_id": sid, "trade": trade,
                            "why": "no placed footprint — no yard to stand goods in."})
            continue                                            # clause 2

        items, own_wagons, faces = [], [], []
        hay = what in ("hay", "teamster")
        if hay and goods._poly_contains((place["local_e"], place["local_n"]), ring):
            refused.append({"structure_id": sid, "trade": trade, "goods": "hay", "why": (
                "it stands INSIDE the hay limits — the ring Sec. 22 of the ordinance of "
                "5 August 1835 walks, inside which stacking hay is forbidden "
                "(data/reconstruction/1835_hay_limits.json). The ordinance is five weeks "
                "after the scene date; the owner asked that it be honoured, so this "
                "stable keeps its hay in the mow and no rick is drawn.")})
            if what == "hay":
                continue                                        # clause 3

        def place_pile(kind_word, length, depth, deal):
            stand, last = _search(poly, place, length, depth, world, taken)
            if stand is None:
                refused.append({"structure_id": sid, "trade": trade, "goods": kind_word,
                                "why": f"no clear ground on any face; the last stand "
                                       f"tried was refused because {last}"})
                return False
            got = deal(stand)
            items.extend(got)
            faces.append(stand["face"])
            taken.append((f"{sid}'s {kind_word}",
                          _quad(stand["e"], stand["n"], stand["bearing"], length, depth,
                                KEEP_CLEAR_M)))
            return True

        if what == "casks":
            place_pile("casks", COOPER_RANK[0] * BARREL_PITCH_M,
                       COOPER_RANK[1] * BARREL_PITCH_M,
                       lambda st: _rank(st, *COOPER_RANK))
        elif what == "barrels":
            place_pile("barrels", PACKER_RANK[0] * BARREL_PITCH_M,
                       PACKER_RANK[1] * BARREL_PITCH_M,
                       lambda st: _rank(st, *PACKER_RANK))
        elif what == "boards":
            depth = BOARD_PILE[0] * (BOARD_M[1] + BOARD_GAP_M)
            place_pile("boards", BOARD_M[0], depth, lambda st: [{
                "kind": "boards", "at_local_enu_m": _at(st, 0.0, 0.0),
                "bearing_deg": _round(st["bearing"], 1), "courses": BOARD_PILE[1]}])
        elif what == "hides":
            for _ in range(2):
                place_pile("hides", HIDE_RAIL_M[0], 0.6, lambda st: [{
                    "kind": "hides", "at_local_enu_m": _at(st, 0.0, 0.0),
                    "bearing_deg": _round(st["bearing"], 1), "hides": HIDES_PER_RAIL}])
        if what in ("hay", "teamster") and \
                not goods._poly_contains((place["local_e"], place["local_n"]), ring):
            L, W = HAY_RICK_M[0], HAY_RICK_M[1]

            def rick(st):
                if goods._poly_contains((st["e"], st["n"]), ring):
                    return []
                return [{"kind": "hay", "at_local_enu_m": _at(st, 0.0, 0.0),
                         "bearing_deg": _round(st["bearing"], 1)}]
            place_pile("hay", L, W, rick)

        if what in ("wagon", "teamster"):
            kinds = ("farm_box",) if what == "wagon" else ("farm_box", "covered")
            for i, kind in enumerate(kinds):
                back, fore = goods._kind_reach(kind)
                length = back + fore
                stand, last = _search(poly, place, length, 2 * goods.WAGON_HALF_W_M,
                                      world, taken)
                if stand is None:
                    refused.append({"structure_id": sid, "trade": trade, "goods": kind,
                                    "why": f"no clear ground for a wagon on any face; the "
                                           f"last stand tried was refused because {last}"})
                    continue
                # The wagon's nose points along the wall; its stand is its body's middle,
                # so the searched rectangle's centre is shifted back by half the pole.
                nose = (stand["bearing"] + 90.0) % 360.0
                shift = (fore - back) / 2
                ne, nn = math.sin(math.radians(nose)), math.cos(math.radians(nose))
                at = [_round(stand["e"] - ne * shift), _round(stand["n"] - nn * shift)]
                wagon = {
                    "id": f"{sid}_yard_wagon_{i + 1}",
                    "kind": kind,
                    "belongs_to": sid,
                    "in_yard_of": sid,
                    "tilt": kind == "covered",
                    "yoke": kind == "covered",
                    "confidence": "reconstructed",
                    "at_local_enu_m": at,
                    "bearing_deg": _round(nose, 1),
                    "face": stand["face"],
                    "note": (f"A {WAGON_WORDS[kind]} standing unhitched in "
                             f"the yard of {sc.get('name') or sid}, off its "
                             f"{stand['face']}, nose along the wall: {why}. The owner's "
                             "T-1212 asks for wagons at the forwarders and the teamsters; "
                             "the stand is the first clear one a fixed search of the "
                             "building's rear and side yards finds. Reconstructed: "
                             "docs/LIBERTIES.md L351."),
                }
                own_wagons.append(wagon)
                faces.append(stand["face"])
                taken.append((f"the wagon {wagon['id']}",
                              goods._wagon_ground(wagon, KEEP_CLEAR_M)))

        wagons.extend(own_wagons)
        if not items:
            continue
        quad = [goods._to_enu(uu, vv, place) for uu, vv in (
            (min(p[0] for p in poly), min(p[1] for p in poly)),
            (max(p[0] for p in poly), min(p[1] for p in poly)),
            (max(p[0] for p in poly), max(p[1] for p in poly)),
            (min(p[0] for p in poly), max(p[1] for p in poly)))]
        lots.append({
            "structure_id": sid,
            "name": sc.get("name"),
            "belongs_to": sid,
            "trade": trade,
            "trade_confidence": fn.get("confidence"),
            "why_goods": why,
            "confidence": "reconstructed",
            "faces": sorted(set(faces)),
            "ground_quad_local_enu_m": [[_round(p[0]), _round(p[1])] for p in quad],
            "items": items,
        })

    lots.sort(key=lambda r: r["structure_id"])
    wagons.sort(key=lambda w: w["id"])
    refused.sort(key=lambda r: (r["structure_id"], r.get("goods") or ""))
    return lots, wagons, refused


def _form() -> dict:
    inv = "reconstructed"
    return {
        "barrel_height_m": {"value": goods.BARREL_H_M, "confidence": inv,
                            "note": "The frontage layer's own cask (town_trade_goods.json), "
                                    "unchanged: a provision barrel on its head."},
        "barrel_belly_diameter_m": {"value": goods.BARREL_BELLY_D_M, "confidence": inv,
                                    "note": "As the frontage layer's."},
        "barrel_head_diameter_m": {"value": goods.BARREL_HEAD_D_M, "confidence": inv,
                                   "note": "As the frontage layer's."},
        "board_m": {"value": list(BOARD_M), "confidence": inv, "note": (
            "INVENTED. A sawn board 12 ft by 12 in by 2 in, recorded converted — the "
            "commonest length the building-material pile already uses for a stick "
            "(lot_building_material.json's 3.66 m), sawn flat for a joiner's bench "
            "rather than squared for a frame. No Chicago board of 1835 is measured.")},
        "board_pile": {"value": list(BOARD_PILE), "confidence": inv, "note": (
            "INVENTED. Three boards a course, six courses, each course laid on three "
            "cross-sticks 0.05 m deep so the air goes through — stickered, the way "
            "green lumber is stacked to season. A pile about 0.6 m high.")},
        "hide_rail_m": {"value": list(HIDE_RAIL_M), "confidence": inv, "note": (
            "INVENTED. A drying rail 2.4 m long on two posts, its rail 1.5 m up and "
            "0.08 m square: high enough that a hide folded over it clears the ground.")},
        "hide_m": {"value": list(HIDE_M), "confidence": inv, "note": (
            "INVENTED. Each hide hangs 1.0 m down either side of the rail and is drawn "
            "0.55 m wide — a side, not a whole hide spread. Three to a rail.")},
        "hay_rick_m": {"value": list(HAY_RICK_M), "confidence": inv, "note": (
            "INVENTED. A rectangular rick 3.0 m by 2.0 m, 1.5 m to the eave and 2.4 m "
            "to the ridge, its top raked to a ridge so the rain runs off — a stable's "
            "stack of a few loads, not a farmer's. Nothing states the shape or the size "
            "of any rick in Chicago in 1835.")},
    }


def record(lots: list, wagons: list, refused: list) -> dict:
    by_trade: dict = {}
    by_kind: dict = {}
    for lot in lots:
        by_trade[lot["trade"]] = by_trade.get(lot["trade"], 0) + 1
        for it in lot["items"]:
            by_kind[it["kind"]] = by_kind.get(it["kind"], 0) + 1
    hay_refused = sum(1 for r in refused if r.get("goods") == "hay"
                      and "INSIDE the hay limits" in r["why"])
    return {
        "_doc": (
            "Goods each WORKING trade kept in its own yard — casks at the cooperages, "
            "barrels at the packing and slaughter houses, boards at the joiners', hides "
            "at the tannery, a hay rick at the stables outside the hay limits, and "
            "wagons at the forwarding houses and the teamster's yard. GENERATED by "
            "tools/generate_trade_yards.py from the sidecars, the committed streets, "
            "walks, fences and wharves, the other yard records and "
            "data/reconstruction/1835_hay_limits.json; tools/check.sh re-derives it byte "
            "for byte. Drawn by renderers/web/js/yard.js through the same `lots` and "
            "`wagons` contract as the building material and the town's wagons. Every "
            "object is reconstructed and belongs_to the structure whose yard it stands "
            "in: docs/LIBERTIES.md L351. T-1961 (piece 4 of T-1212)."),
        "id": "town_trade_yards",
        "name": "Goods in the working trades' yards",
        "kind": "yard_goods",
        "scene": "1835",
        "target_date": "1835-07-01",
        "coordinates": ("Local East-North-Up metres from data/datum.json's origin, the "
                        "same frame data/enclosures/, data/signage/ and the sidecars' "
                        "placement.local_e / local_n use."),
        "counts": {
            "yards": len(lots),
            "objects": sum(len(lot["items"]) for lot in lots),
            "by_trade": dict(sorted(by_trade.items())),
            "by_kind": dict(sorted(by_kind.items())),
            "wagons": len(wagons),
            "refused": len(refused),
            "hay_refused_inside_the_limits": hay_refused,
        },
        "existence": {
            "value": "goods standing in the yards of the town's working trades",
            "confidence": "reconstructed",
            "sources": [],
            "note": (
                "THE OWNER'S INSTRUCTION, NOT A SOURCE. T-1212 (owner, 2026-10-01) asks "
                "for the trade goods and vehicles of T-0040 by trade: barrels at the "
                "coopers and packers, wagons at the forwarders and the teamsters, lumber "
                "at the joiners, hides at the tannery, hay at the stables within the hay "
                "limits. No source this project holds puts any of these objects at any "
                "of these yards on 1 July 1835. What the rule rests on is what each trade "
                "is: a cooper makes casks, a packer fills them, a joiner seasons boards, "
                "a tanner dries hides, a stable keeps hay. Every object is graded "
                "reconstructed and claimed in docs/LIBERTIES.md L351."),
        },
        "hay_limit": {
            "source_id": "chicago_democrat_1833_1835",
            "record": "data/reconstruction/1835_hay_limits.json",
            "confidence": "documented",
            "note": (
                "Sec. 22 of the ordinance of 5 August 1835 forbids stacking hay inside the "
                "limits it walks. It postdates the scene by five weeks, and the hay-limits "
                "record says it places nothing; this record is the first to READ it, at "
                "the owner's instruction, and reads it conservatively: no rick stands "
                "inside the ring, and a stable inside it keeps its hay in the mow. Both "
                "the stable's own point and the rick's must lie outside. The opposite "
                "reading — a corporation legislates against what people do, so ricks "
                "stood inside the line in July — is the same argument the frontage goods "
                "rest on, and is the one this record declines."),
        },
        "form": _form(),
        "rule": {
            "note": (
                "A structure whose function is one of the trades below, standing on the "
                "scene date with a placed footprint, gets its trade's goods on the first "
                "clear stand a fixed search of its rear and side yards finds — never its "
                "front, which is the street's. A stand is refused within "
                f"{WALL_CLEAR_M:.2f} m of any committed footprint, on a walk, in a garden "
                "or pen, in a travelled track, on a wharf or a hull, in or near the "
                f"water, or within {KEEP_CLEAR_M:.2f} m of anything already standing. Hay "
                "is also refused inside the hay limits. Read the clauses in "
                "tools/generate_trade_yards.py."),
            "trades": {k: {"goods": v[0], "why": v[1]} for k, v in sorted(TRADES.items())},
            "search": {"faces": list(FACES), "wall_gap_m": WALL_GAP_M,
                       "along_steps_m": list(ALONG_STEPS_M),
                       "out_steps_m": list(OUT_STEPS_M),
                       "wall_clear_m": WALL_CLEAR_M, "keep_clear_m": KEEP_CLEAR_M},
        },
        "lots": lots,
        "wagons": wagons,
        "refused": refused,
        "research_note": (
            "WHAT WOULD MOVE ANY OF THIS. A lot description, an insurance survey, a "
            "sale notice or a view naming what stood in any one of these yards; a "
            "cooper's or packer's advertisement giving a stock; the tannery's own "
            "description; any 1835 complaint about a rick inside the line, which would "
            "argue for the reading this record declines."),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="re-derive and diff, write nothing")
    args = ap.parse_args()
    ids, cars = goods._standing()
    lots, wagons, refused = build(ids, cars)
    text = json.dumps(record(lots, wagons, refused), indent=2, ensure_ascii=False) + "\n"
    objects = sum(len(lot["items"]) for lot in lots)
    if args.check:
        if not OUT.exists():
            print(f"TRADE YARDS DRIFT\n  - {OUT.relative_to(ROOT)} is missing")
            return 1
        if OUT.read_text(encoding="utf-8") != text:
            print(f"TRADE YARDS DRIFT\n  - {OUT.relative_to(ROOT)} has drifted from the "
                  "rule in tools/generate_trade_yards.py")
            return 1
        print(f"verified {objects} object(s) in {len(lots)} trade yard(s) and "
              f"{len(wagons)} yard wagon(s) ({len(refused)} refused with a reason)")
        return 0
    OUT.write_text(text, encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)} — {objects} object(s) in {len(lots)} trade "
          f"yard(s), {len(wagons)} yard wagon(s) ({len(refused)} refused)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
