#!/usr/bin/env python3
"""Fill the 1835 commercial core's street fronts to the density Gifford's drawing shows (T-3605).

The owner, 2026-11-15, after the first Tremont House was photo-matched to N. Roswell
Gifford's drawing: read the drawing "as a reasonable view of 1835", build its street to it,
then "reconsider the density of that and reapply that level of correct reasonable density
and alignment to the rest of the streets in 1835, like south water and all the other major
streets". Asked how far, he chose "Commercial core, about 60 stores": South Water and both
sides of Lake, Wells to State, each block front filled to about 70 % of its length (the
drawn block itself stands at about 89 %, and the drawing may show the street as late as
1839, so the core is not built to the drawing's full density).

WHAT THIS DOES. For every platted block face on those streets it measures how much of the
face's length committed buildings already hold within 3 m of the frontage line, and lays
ordinary anonymous stores (C1, C2, C3, an H3 boarding house on a long Lake front) into the
open stretches until the face reaches the target, largest stretch first so the new fronts
read as rows. Each store stands on the face's own line, 1.50 m back from the lot line (the
plat module's margin, as `tools/generate_block_infill.py` places its party-line runs), and
faces the street the face fronts. Sizes are sampled inside each family's authored band
(`tools/family_bands.py`), so nothing here needs a drawn-value exemption.

A reconstructed anonymous cottage set back a few metres behind an open front stands where a
store's body would go. It is moved straight back to 22 m from its street edge, the back of
its own lot, exactly as the drawn block's three cottages were; none is retired.

WHAT IS INVENTED. Everything about each store: that it stood, its family, its frontage and
depth, its station. The density is the owner's reading of a retrospective drawing, spread by
rule (docs/LIBERTIES.md L-core-row-fill-3605). These are NOT drawn buildings: no
`reconstruction.drawn` block. Like the drawn roofs, they are in the inventory's
`pictured_roofs` (its `by_prefix` entry for this prefix), so they re-weight no household:
they were raised for the street's look, not because the model's people needed more stores.

    python3 tools/generate_core_row_fill_1835.py            write the records (and the moves)
    python3 tools/generate_core_row_fill_1835.py --check    fail on drift
    python3 tools/generate_core_row_fill_1835.py --fronts   print the measured fronts
    python3 tools/generate_core_row_fill_1835.py --self-test
"""
from __future__ import annotations

import argparse
import copy
import json
import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
sys.path[:0] = [str(ROOT / "tools"), str(ROOT / "generators")]
from block_faces import face_frame, project  # noqa: E402
from family_bands import families, dimensions_m  # noqa: E402
from generate_block_infill import form_for, invented, no_build_rings, FUNCTIONS  # noqa: E402
import fabric_rule_1835  # noqa: E402
from generate_west_infill import footprint_origin  # noqa: E402
from plat_corridors import corridors, intrusion  # noqa: E402
from plat_occupancy import world_polygon, footprints, overlap_area  # noqa: E402
from inferred_occupancy import occupancy  # noqa: E402
from normalise_structure_function import canonical  # noqa: E402
from siding_stock import deal_records  # noqa: E402

LOTS = DATA / "traces" / "vectors" / "thompson_lots.json"
PREFIX = "recon_1835_core_"
SOURCE = "owner_chicago_1835_reconstruction_spec_2026"
LIBERTY = "L-core-row-fill-3605"
#: the blocks whose fronts are filled, by their west cross street (Wells to State)
CROSS = ("wells", "lasalle", "clark", "dearborn")
#: (block prefix, face, the street the face fronts, the side of that street)
FACES = (("south_water", "north", "south_water", "south side"),
         ("south_water", "south", "lake", "north side"),
         ("lake", "north", "lake", "south side"))
STREET_NAME = {"south_water": "South Water Street", "lake": "Lake Street"}
CROSS_NAME = {"wells": "Wells", "lasalle": "LaSalle", "clark": "Clark", "dearborn": "Dearborn"}
#: the block Gifford draws, built to the drawing; never filled again here
DRAWN_FACES = {("blk_south_water_clark", "south")}
TARGET_SHARE = 0.70
SETBACK_M = 1.50           # front wall behind the lot line: the plat module's margin
BUILT_BAND_M = 3.0         # a wall this close to the line holds the front
CORNER_M = 1.50            # clear of the cross street's corner
ROW_GAP_M = 0.10           # between two stores of one new row
OTHER_GAP_M = 0.50         # between a new store and anything else
DOOR_GROUND_M = 3.0        # open ground a cottage's street door keeps before the store's back
BODY_BAND_M = SETBACK_M + 15.0 + DOOR_GROUND_M   # the deepest store body plus its clearance
MOVE_TO_SETBACK_M = 22.0   # a blocking cottage goes back to the rear of its lot
MOVABLE = re.compile(r"^recon_1835_.*_d[1-6]_\d+$")
#: the row's family rhythm; an H3 boarding house leads a long Lake Street stretch
RHYTHM = ("C2", "C3", "C1", "C2", "C3", "C2", "C1", "C3")
H3_MIN_STRETCH_M = 30.0


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _record(sid: str) -> dict:
    return load(DATA / "structures" / (sid + ".json"))


def standing_1835(datum: dict, exclude: set[str]) -> list[tuple[str, list]]:
    in_1835 = {s["id"] for s in load(DATA / "sidecars" / "1835" / "index.json")["structures"]}
    return [(sid, poly) for sid, poly in footprints(datum, exclude) if sid in in_1835]


def is_movable(sid: str) -> bool:
    """A reconstructed anonymous cottage is a count-unit, and may stand anywhere on its lot."""
    if not MOVABLE.match(sid):
        return False
    rec = _record(sid).get("reconstruction") or {}
    return rec.get("status") == "inferred_anonymous" and str(rec.get("family", "")).startswith("D")


def measure_face(frame: dict, standing) -> dict:
    """Built length within BUILT_BAND_M of the line, and every footprint in the body band."""
    length = frame["length"]
    held, near = [], []
    for sid, poly in standing:
        pr = [project(frame, p) for p in poly]
        lo, hi = min(q[0] for q in pr), max(q[0] for q in pr)
        front = max(q[1] for q in pr)          # the wall nearest the street (outward +)
        if hi < -2.0 or lo > length + 2.0 or front > 0.5:
            continue
        if front >= -BUILT_BAND_M:
            held.append((max(0.0, lo), min(length, hi)))
        if front >= -BODY_BAND_M:
            near.append({"id": sid, "lo": lo, "hi": hi, "front": front})
    built, cur = 0.0, None
    for a, b in sorted(held):
        if cur is None or a > cur[1]:
            built += (cur[1] - cur[0]) if cur else 0.0
            cur = [a, b]
        else:
            cur[1] = max(cur[1], b)
    built += (cur[1] - cur[0]) if cur else 0.0
    return {"length": length, "built": built, "near": sorted(near, key=lambda o: o["lo"])}


def fronts(datum: dict, standing) -> list[dict]:
    blocks = {b["id"]: b for b in load(LOTS)["blocks"]}
    out = []
    for cross in CROSS:
        for prefix, face, street, side in FACES:
            bid = f"blk_{prefix}_{cross}"
            frame = face_frame(blocks[bid], face)
            m = measure_face(frame, standing)
            out.append({"block": bid, "face": face, "street": street, "side": side,
                        "frame": frame, **m,
                        "drawn": (bid, face) in DRAWN_FACES})
    return out


def free_stretches(front: dict) -> tuple[list[tuple[float, float]], list[str]]:
    """Open stations along the face once the movable cottages are set aside."""
    hard, moves = [], []
    for o in front["near"]:
        if o["front"] < -BUILT_BAND_M and is_movable(o["id"]):
            moves.append(o["id"])
            continue
        hard.append((o["lo"] - OTHER_GAP_M - 0.05, o["hi"] + OTHER_GAP_M + 0.05))
    lo, hi = CORNER_M, front["length"] - CORNER_M
    stretches, s = [], lo
    for a, b in sorted(hard):
        if a > s:
            stretches.append((s, min(a, hi)))
        s = max(s, b)
    if s < hi:
        stretches.append((s, hi))
    return [(a, b) for a, b in stretches if b - a > 5.0], moves


def lay_front(front: dict, table: dict, seq0: int) -> tuple[list[dict], list[str]]:
    """The stores this face takes, largest open stretch first, until it reaches the target."""
    if front["drawn"]:
        return [], []
    want = TARGET_SHARE * front["length"] - front["built"]
    if want <= 3.0:
        return [], []
    stretches, movable = free_stretches(front)
    laid, used_moves, seq, added, beat = [], set(), seq0, 0.0, seq0  # each face enters the rhythm where the last left it
    for a, b in sorted(stretches, key=lambda st: st[1] - st[0], reverse=True):
        s = a
        while added < want:
            fam = RHYTHM[beat % len(RHYTHM)]
            if (front["street"] == "lake" and b - a >= H3_MIN_STRETCH_M and s == a
                    and not any(x["family"] == "H3" for x in laid)):
                fam = "H3"
            sid = f"{PREFIX}{fam.lower()}_{seq + 1:03d}"
            width, depth = dimensions_m(fam, table[fam]["band_ft"], sid)
            if s + width > b + 1e-9:
                break
            seq += 1
            beat += fam != "H3"
            laid.append({"id": sid, "family": fam, "width": width, "depth": depth,
                         "station": (round(s, 3), round(s + width, 3))})
            s += width + ROW_GAP_M
            added += width
        if added >= want:
            break
    # only the cottages that stand behind a laid store's body move
    for x in laid:
        for o in front["near"]:
            if o["id"] in movable and o["hi"] > x["station"][0] - OTHER_GAP_M \
                    and o["lo"] < x["station"][1] + OTHER_GAP_M \
                    and o["front"] > -(SETBACK_M + x["depth"] + DOOR_GROUND_M):
                used_moves.add(o["id"])
    return laid, sorted(used_moves)


def centre_of(front: dict, x: dict) -> tuple[float, float]:
    fr = front["frame"]
    mid = (x["station"][0] + x["station"][1]) / 2.0
    off = SETBACK_M + x["depth"] / 2.0
    return (fr["origin"][0] + fr["along"][0] * mid - fr["outward"][0] * off,
            fr["origin"][1] + fr["along"][1] * mid - fr["outward"][1] * off)


def make_record(front: dict, x: dict, table: dict, datum: dict, people: dict, n: int) -> dict:
    fam, sid = x["family"], x["id"]
    spec = table[fam]
    width, depth = x["width"], x["depth"]
    bearing = front["frame"]["bearing"]
    ce, cn = centre_of(front, x)
    east, north = footprint_origin(ce, cn, width, depth, bearing)
    fabric = fabric_rule_1835.deal(sid, fam, spec["archetype"])
    form = fabric_rule_1835.apply_form(form_for(fam, spec, sid, width, depth, fabric["paint"]),
                                       fabric)
    street = STREET_NAME[front["street"]]
    cross = front["block"].rsplit("_", 1)[-1]
    function_term = FUNCTIONS.get(fam) or canonical(spec["label"])
    return {
        "id": sid,
        "name": f"Reconstructed {fam} {spec['label'].lower()} #{n:03d}",
        "archetype": spec["archetype"],
        "phases": [{
            "id": "inferred_1835",
            "documented_range": {
                "from": "1835-01-01", "to": "1835-12-31", "confidence": "reconstructed",
                "note": ("Anonymous count-unit of the commercial core's row fill (T-3605): the "
                         "owner's reading of Gifford's drawing of the first Tremont House's "
                         "street, spread over South Water and Lake from Wells to State at "
                         "about 70 % of each block front. No evidence establishes that this "
                         "particular building existed, and no source names an occupant.")},
            "position": {
                "utm_e": round(datum["origin_utm_e"] + east, 3),
                "utm_n": round(datum["origin_utm_n"] + north, 3),
                "rotation_deg": bearing,
                "symbolic_location": (f"Anonymous reconstructed store on the {front['side']} "
                                      f"of {street}, in the block west-bounded by "
                                      f"{CROSS_NAME[cross]} Street; one unit of the street's row"),
                "confidence": "reconstructed",
                "note": (f"PARTY-LINE FRONTAGE, DERIVED FROM THE COMMITTED PLAT (T-3605). It "
                         f"stands on the {front['face']} face of {front['block']}, whose line "
                         f"and bearing are read from the block boundary in "
                         f"data/traces/vectors/thompson_lots.json, at stations "
                         f"{x['station'][0]:.2f}-{x['station'][1]:.2f} m from the face's west "
                         f"end, its front wall {SETBACK_M:.2f} m behind the lot line (the plat "
                         f"module's margin, as the block programme's own party-line runs "
                         f"stand). The bearing is the face's, so the front looks square at "
                         f"{street}. The station is the row-fill rule's (largest open stretch "
                         f"first, until the face is about 70 % built), not a measurement."),
                "derivation": {"method": "not_derivable",
                               "reason": "No parcel-by-parcel July 1835 roof register survives "
                                         "in the supplied evidence, and no lot on this face is "
                                         "numbered."}},
            "footprint": {
                "polygon": [[0, 0], [width, 0], [width, depth], [0, depth]],
                "confidence": "reconstructed",
                "note": (f"A {width:.2f} × {depth:.2f} m rectangle sampled deterministically "
                         f"inside the {fam} family's authored footprint band; no individual "
                         f"dimensions are documented.")},
            "form": form,
            "change_note": ("T-3605 raises this store in the commercial core's row fill; a "
                            "better-evidenced named roof substitutes for it rather than "
                            "adding to the town.")}],
        "function": invented(function_term,
                             f"The {fam} type, as a store on a commercial street front; no "
                             f"proprietor is recovered for it."),
        "reconstruction": {
            "status": "inferred_anonymous", "family": fam, "district": "south",
            "inventory_class": "principal_functional",
            "programme_phase": "core_row_fill_1835", "source_id": SOURCE,
            "block_id": front["block"], "stands_on": "frontage", "fronts": front["street"],
            "sequence": n, "finish_key": fabric["finish_key"],
            "roof_condition": fabric["roof_condition"], "age_state": fabric["age_state"],
            "fabric_basis": fabric["fabric_basis"],
            "frontage": {"block": front["block"], "face": front["face"],
                         "setback_m": SETBACK_M, "abuts": None,
                         "why": (f"T-3605: the owner's 'Commercial core, about 60 stores' "
                                 f"(2026-11-15) fills this face toward {int(TARGET_SHARE * 100)} "
                                 f"% of its length, from {front['built'] / front['length']:.0%} "
                                 f"built ({LIBERTY}).")}},
        **({"occupants": people[sid]} if sid in people else {}),
        "research_note": ("RECONSTRUCTED / GENERATED, NOT AN ATTESTED NAMED BUILDING. The "
                          "density of this street front is the owner's reading of Gifford's "
                          "retrospective drawing of the first Tremont House's street (T-3605); "
                          "the store's presence, family, frontage, depth and station are "
                          "interpretive. Its occupants, if any, are dealt by the town's "
                          "housing tools and graded by their own records."),
        "review_required": False,
    }


SETBACK_NOTE = re.compile(r"stands (\d+(?:\.\d+)?) m back from its street edge")


def moved_record(sid: str, front: dict, datum: dict, obstacles: list) -> dict:
    """The cottage moved straight back toward the rear of its lot: MOVE_TO_SETBACK_M from
    its street edge, or the nearest setback behind the row that clears every other roof
    by OTHER_GAP_M and stays on the lot's own side of the alley."""
    record = copy.deepcopy(_record(sid))
    phase = record["phases"][0]
    poly = world_polygon(phase, datum)
    fr = front["frame"]
    now = -max(project(fr, p)[1] for p in poly)        # current setback of its front wall
    deep = -min(project(fr, p)[1] for p in poly) - now  # its own depth across the face
    if now >= MOVE_TO_SETBACK_M - 1e-3:
        return record
    lot_depth = float(next(b for b in load(LOTS)["blocks"]
                           if b["id"] == front["block"])["depth_m"]) / 2.0
    tried = sorted({round(MOVE_TO_SETBACK_M + d, 1) for d in
                    [0, -2, 2, -4, 4, -6, 6, 8, 10, 12, 14]},
                   key=lambda v: abs(v - MOVE_TO_SETBACK_M))
    pos = phase["position"]
    for target in tried:
        if target + deep > lot_depth - 2.0 or target < SETBACK_M + 15.0:
            continue
        shift = target - now
        cand = [(p[0] - fr["outward"][0] * shift, p[1] - fr["outward"][1] * shift) for p in poly]
        if all(_gap(cand, q) >= (DOOR_GROUND_M if o.startswith(PREFIX) else OTHER_GAP_M + 0.05)
               for o, q in obstacles if o != sid):
            pos["utm_e"] = round(pos["utm_e"] - fr["outward"][0] * shift, 3)
            pos["utm_n"] = round(pos["utm_n"] - fr["outward"][1] * shift, 3)
            note = SETBACK_NOTE.sub(f"stands {target:.1f} m back from its street edge",
                                    pos["note"], count=1)
            if note == pos["note"]:
                note += f" It stands {target:.1f} m back from its street edge."
            pos["note"] = note + (f" T-3605: moved {shift:.1f} m straight back, toward the "
                                  f"rear of its lot, so the commercial core's row stands at the "
                                  f"street ({LIBERTY}).")
            return record
    raise ValueError(f"{sid}: no setback behind the row clears its lot's other roofs")


def build(datum: dict | None = None):
    datum = datum or load(DATA / "datum.json")
    table, people = families(), occupancy()
    mine = {p.stem for p in (DATA / "structures").glob(PREFIX + "*.json")}
    standing = standing_1835(datum, mine)
    fs = fronts(datum, standing)
    records, moves, seq, summary = [], {}, 0, []
    for front in fs:
        laid, mv = lay_front(front, table, seq)
        seq += len(laid)
        for x in laid:
            records.append(make_record(front, x, table, datum, people,
                                       int(x["id"].rsplit("_", 1)[1])))
        laid_polys = [(r["id"], world_polygon(r["phases"][0], datum)) for r in records]
        for sid in mv:
            moved_polys = [(m, world_polygon(r["phases"][0], datum)) for m, r in moves.items()]
            obstacles = [(o, q) for o, q in standing if o not in moves] + laid_polys + moved_polys
            moves[sid] = moved_record(sid, front, datum, obstacles)
        added = sum(x["width"] for x in laid)
        summary.append({"block": front["block"], "face": front["face"],
                        "street": f"{STREET_NAME[front['street']]} ({front['side']})",
                        "length_m": round(front["length"], 1),
                        "built_m": round(front["built"], 1),
                        "built_pct": round(100 * front["built"] / front["length"], 1),
                        "stores": len(laid),
                        "families": [x["family"] for x in laid],
                        "after_pct": round(100 * (front["built"] + added) / front["length"], 1),
                        "moves": mv, "drawn": front["drawn"]})
    deal_records(records)
    declare_ground(records, datum)
    report = validate(records, moves, datum)
    return records, moves, summary, report


def declare_ground(records: list[dict], datum: dict) -> None:
    """Declare ground contact on every store the validator measures off the 1835 ground.

    Measured with the validator's own `unlanded_values` on the 1835 scene's committed
    heightfield, so the declaration and the check cannot disagree. A store laid at its
    street line on ground that rises or falls across its walls by more than the walker's
    step stands as built; nothing records a sill, a cut or a graded front for it, and
    inventing one would claim more than the row fill does.
    """
    import validate as V  # noqa: E402 — heavy; only build() needs it
    from heightfield import Heightfield  # noqa: E402
    scene = load(DATA / "scenes" / "1835.json")
    field = Heightfield.load(DATA / "terrain" / "epochs" / scene["terrain_epoch"])
    if field is None or datum.get("origin_utm_e") is None:
        return
    origin = (float(datum["origin_utm_e"]), float(datum["origin_utm_n"]))
    found = V.unlanded_values({r["id"]: r for r in records}, {"1835": scene}, V.Report(),
                              field, origin, V.archetype_ground_contact(),
                              fields={scene["terrain_epoch"]: field})
    gaps = {(sid, pid): gap for sid, pid, _, _, gap in found if gap is not None}
    for r in records:
        for ph in r["phases"]:
            gap = gaps.get((r["id"], ph["id"]))
            if gap is None:
                continue
            ph["ground_contact"] = {
                "state": "approach_not_modelled",
                "note": (f"T-3605. Laid at its street line by the core row fill, this store "
                         f"stands on {scene['terrain_epoch']} ground that its walls meet "
                         f"{gap:+.2f} m off the ground at its placement origin, more than the walker's "
                         f"0.35 m step. Nothing in the record is wrong: the position is the "
                         f"block face and the footprint is the family band. What is missing "
                         f"is what reconciled a store front with uneven ground in 1835, a "
                         f"sill on blocks, a cut, or a graded walk, and nothing says which, so "
                         f"none is drawn (docs/LIBERTIES.md {LIBERTY}). WHAT WOULD SETTLE "
                         f"IT: an underpinning for 1835 (tools/check_sunken_sills.py SCENES), "
                         f"or a finer terrain epoch under this block.")}


def _gap(a, b) -> float:
    if overlap_area(b, a) > 1e-4:
        return 0.0
    def seg(p, q, r):
        de, dn = r[0] - q[0], r[1] - q[1]
        span = de * de + dn * dn
        u = 0.0 if span == 0 else max(0.0, min(1.0, ((p[0]-q[0])*de + (p[1]-q[1])*dn) / span))
        return math.hypot(p[0] - (q[0] + u * de), p[1] - (q[1] + u * dn))
    return min(seg(p, q, r) for x, y in ((a, b), (b, a)) for p in x
               for q, r in zip(y, y[1:] + y[:1]))


def validate(records: list[dict], moves: dict, datum: dict) -> list[str]:
    import importlib
    if len({r["id"] for r in records}) != len(records):
        raise ValueError("two row-fill stores share an id")
    lanes, refused = corridors(), no_build_rings()
    ids = {r["id"] for r in records} | set(moves)
    others = standing_1835(datum, ids)
    own = [(r["id"], world_polygon(r["phases"][0], datum)) for r in records]
    moved = [(sid, world_polygon(r["phases"][0], datum)) for sid, r in moves.items()]
    # The inventory's `pictured_roofs` keeps these roofs off the household model's weights
    # (tools/model_town_1835.py household_matrix), as it keeps Gifford's; its entry for this
    # prefix must say what is written here.
    group = {"C": "stores_mixed_use", "H": "larger_boarding_houses"}
    held: dict = {}
    for r in records:
        rec = r["reconstruction"]
        cell = held.setdefault(group[rec["family"][0]], {})
        cell[rec["district"]] = cell.get(rec["district"], 0) + 1
    pictured = load(DATA / "reconstruction" / "1835_building_inventory.json").get(
        "pictured_roofs") or {}
    said = (pictured.get("by_prefix") or {}).get(PREFIX)
    if said != held or PREFIX not in (pictured.get("structure_prefixes") or []):
        raise ValueError(f"the inventory's pictured_roofs entry for {PREFIX} says {said} "
                         f"and the records hold {held}")
    report = []
    for record, (sid, poly) in zip(records, own):
        importlib.import_module("archetypes." + record["archetype"] + "_params").from_phase(
            record["phases"][0], record)
        street, depth = intrusion(poly, lanes)
        if street:
            raise ValueError(f"{sid} intrudes {depth:.2f} m into {street}")
        for name, ring in refused.items():
            if overlap_area(ring, poly) > 1e-3:
                raise ValueError(f"{sid} stands on refused ground {name}")
        near_row = min((_gap(poly, q) for o, q in own if o != sid), default=99.0)
        if near_row < ROW_GAP_M - 2e-3:  # positions round to the millimetre
            raise ValueError(f"{sid} stands {near_row:.2f} m from a neighbour in its own row")
        near = min(((_gap(poly, q), o) for o, q in others + moved), default=(99.0, None))
        if near[0] < OTHER_GAP_M - 2e-3:
            raise ValueError(f"{sid} stands {near[0]:.2f} m from {near[1]}")
        report.append(f"{sid}: nearest other {near[0]:.2f} m ({near[1]})")
    for sid, poly in moved:
        street, depth = intrusion(poly, lanes)
        if street:
            raise ValueError(f"moved {sid} intrudes {depth:.2f} m into {street}")
        near = min(((_gap(poly, q), o) for o, q in others + own + [m for m in moved if m[0] != sid]),
                   default=(99.0, None))
        if near[0] < OTHER_GAP_M - 1e-6:
            raise ValueError(f"moved {sid} stands {near[0]:.2f} m from {near[1]}")
        report.append(f"{sid}: moved back, nearest other {near[0]:.2f} m ({near[1]})")
    return report


def self_test() -> int:
    datum = load(DATA / "datum.json")
    records, moves, _, _ = build(datum)
    cases = []
    dup = copy.deepcopy(records)
    dup[1]["id"] = dup[0]["id"]
    cases.append(("two stores under one id", dup))
    road = copy.deepcopy(records)
    road[0]["phases"][0]["position"]["utm_n"] += 14.0 if records[0]["phases"][0]["position"]["rotation_deg"] < 90 or records[0]["phases"][0]["position"]["rotation_deg"] > 270 else -14.0
    cases.append(("a store moved into its street", road))
    onto = copy.deepcopy(records)
    onto[0]["phases"][0]["position"] = copy.deepcopy(onto[1]["phases"][0]["position"])
    cases.append(("two stores on one spot", onto))
    for label, mutated in cases:
        try:
            validate(mutated, moves, datum)
        except (ValueError, SystemExit):
            print("   self-test | PASS: refuses " + label)
        else:
            print("   self-test | FAIL: did not refuse " + label)
            return 1
    print("PASS: generate_core_row_fill_1835 self-test")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--fronts", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    records, moves, summary, report = build()
    if args.fronts:
        print(json.dumps(summary, indent=1))
        return 0
    drift, expected = [], set()
    out = [(r["id"], r) for r in records] + list(moves.items())
    for sid, record in out:
        path = DATA / "structures" / (sid + ".json")
        expected.add(path)
        content = json.dumps(record, indent=2, ensure_ascii=False) + "\n"
        if args.check:
            if not path.exists() or path.read_text(encoding="utf-8") != content:
                drift.append(str(path.relative_to(ROOT)))
        else:
            path.write_text(content, encoding="utf-8")
    stale = [p for p in (DATA / "structures").glob(PREFIX + "*.json") if p not in expected]
    if args.check:
        drift += [str(p.relative_to(ROOT)) for p in stale]
    else:
        for p in stale:
            p.unlink()
    print("\n".join(report))
    if drift:
        print("FAIL: core row-fill records drift: " + ", ".join(drift))
        return 1
    print(f"PASS: {len(records)} core row-fill stores, {len(moves)} cottages moved back"
          + (" rederive exactly" if args.check else " written"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
