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

The row turns the corner. The owner, offered 43 stores on South Water and Lake alone or more
on the cross streets (2026-11-16), chose "Add Clark, Dearborn, Wells, LaSalle": the cross
streets' fronts of the same blocks are filled the same way, after the main streets' rows are
laid and measured with them, but only within CROSS_REACH_M of South Water or Lake (a
Lake-Randolph block's south half fronts Randolph's end, not the core's) and never across an
alley's mouth. State's fronts are not among them.

No house is moved, and no store stands before one. Every building within DOORYARD_M of the
line keeps the frontage before it open: a store goes neither on it nor across the ground
between its door and the street it faces, so a house set back behind the row still has its own
dooryard out to the street, with LANE_M of open ground beside it. The owner, 2026-11-16, of
the first version, which had moved ten cottages straight back behind the new stores: "If
those 10 cottages in the business district were moved in and are sitting oddly in the
center of a property with no street facing etc please rework them unless that was a viable
site plan for the block". They were walled in behind a solid row, so they stand where they
stood, and the row leaves them their way to the street.

WHAT IS INVENTED. Everything about each store: that it stood, its family, its frontage and
depth, its station. The density is the owner's reading of a retrospective drawing, spread by
rule (docs/LIBERTIES.md L-core-row-fill-3605). These are NOT drawn buildings: no
`reconstruction.drawn` block. Like the drawn roofs, they are in the inventory's
`pictured_roofs` (its `by_prefix` entry for this prefix), so they re-weight no household:
they were raised for the street's look, not because the model's people needed more stores.

    python3 tools/generate_core_row_fill_1835.py            write the records
    python3 tools/generate_core_row_fill_1835.py --check    fail on drift
    python3 tools/generate_core_row_fill_1835.py --fronts   print the measured fronts
    python3 tools/generate_core_row_fill_1835.py --self-test
"""
from __future__ import annotations

import argparse
import copy
import functools
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

CORRIDOR_LINE = "drawn"
CORRIDOR_LINE_WHY = ("The row stands on platted block faces, so the block grid's own drawn "
                     "line is the street edge it is held clear of.")

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
#: the cross streets' fronts of the same blocks (the owner, 2026-11-16, offered 43 stores on
#: South Water and Lake or more on the cross streets: "Add Clark, Dearborn, Wells, LaSalle"):
#: a block's west face fronts its own cross street and its east face the next one east;
#: State's fronts are not among them. A Lake-Randolph block's cross fronts are filled only
#: between Lake and its alley, the half that belongs to Lake's core.
NEXT_EAST = {"wells": "lasalle", "lasalle": "clark", "clark": "dearborn"}
CROSS_FACES = tuple((prefix, face) for prefix in ("south_water", "lake") for face in ("west", "east"))
STREET_NAME = {"south_water": "South Water Street", "lake": "Lake Street",
               "wells": "Wells Street", "lasalle": "LaSalle Street", "clark": "Clark Street",
               "dearborn": "Dearborn Street"}
CROSS_NAME = {"wells": "Wells", "lasalle": "LaSalle", "clark": "Clark", "dearborn": "Dearborn"}
#: the block Gifford draws, built to the drawing; never filled again here
DRAWN_FACES = {("blk_south_water_clark", "south")}
TARGET_SHARE = 0.70
SETBACK_M = 1.50           # front wall behind the lot line: the plat module's margin
BUILT_BAND_M = 3.0         # a wall this close to the line holds the front
CORNER_M = 1.50            # clear of the cross street's corner
ROW_GAP_M = 0.10           # between two stores of one new row
OTHER_GAP_M = 0.50         # between a new store and anything else
#: the household layer's premises (tools/generate_inferred_households.py, the structures
#: its ownership file says it still writes) keep 3 m from every building that does not name
#: them as a party wall
INVENTED_GAP_M = 3.0
HOUSEHOLD_LAYER = DATA / "reconstruction" / "1835_inferred_household_pass_ownership.json"


@functools.lru_cache(maxsize=None)
def household_layer() -> frozenset[str]:
    owns = load(HOUSEHOLD_LAYER)["passes"]["tools/generate_inferred_households.py"]["still_owns"]
    return frozenset(owns["data/structures"]["ids"])
DOOR_GROUND_M = 3.0        # open ground a building's street door keeps before a store's back
BODY_BAND_M = SETBACK_M + 15.0 + DOOR_GROUND_M   # the deepest store body plus its clearance
#: a building whose front wall stands within this of the line keeps the frontage before it
#: open (its dooryard to the street); a store stands neither on it nor across its way out
DOORYARD_M = 30.0
LANE_M = 1.0               # open ground beside that dooryard, each side
MIN_DOORYARD_M2 = 12.0     # a privy or a woodshed keeps no dooryard of its own
#: the row's family rhythm; an H3 boarding house leads a long Lake Street stretch
RHYTHM = ("C2", "C3", "C1", "C2", "C3", "C2", "C1", "C3")
H3_MIN_STRETCH_M = 30.0


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _record(sid: str) -> dict:
    return load(DATA / "structures" / (sid + ".json"))


def rear_ell(record: dict, datum: dict) -> list:
    """The rear ell a frame tavern (an H3) builds outside its footprint polygon
    (generate_dooryard_plantings.rear_ell_world, which check_structure_clearance.py reads),
    in the scene's local frame, or []."""
    from generate_dooryard_plantings import rear_ell_world  # noqa: E402
    phase = next((ph for ph in record.get("phases") or []
                  if (ph.get("documented_range") or {}).get("from", "0000") <= "1835-07-01"
                  <= (ph.get("documented_range") or {}).get("to", "9999")), None)
    if phase is None or not (phase.get("position") or {}).get("utm_e"):
        return []
    pos = phase["position"]
    sidecar = {"id": record["id"], "archetype": record.get("archetype"), "phase": phase["id"],
               "footprint": phase.get("footprint") or {},
               "placement": {"local_e": float(pos["utm_e"]) - float(datum["origin_utm_e"]),
                             "local_n": float(pos["utm_n"]) - float(datum["origin_utm_n"]),
                             "rotation_deg": pos.get("rotation_deg") or 0.0}}
    return rear_ell_world(sidecar, record)


def standing_1835(datum: dict, exclude: set[str]) -> list[tuple[str, list]]:
    """Every footprint standing on the scene date, and every frame tavern's rear ell."""
    in_1835 = {s["id"] for s in load(DATA / "sidecars" / "1835" / "index.json")["structures"]}
    out = [(sid, poly) for sid, poly in footprints(datum, exclude) if sid in in_1835]
    for sid in {sid for sid, _ in out}:
        rec = _record(sid)
        if rec.get("archetype") == "frame_tavern":
            ell = rear_ell(rec, datum)
            if ell:
                out.append((sid, ell))
    return out


@functools.lru_cache(maxsize=None)
def bearings_1835() -> dict[str, float]:
    """Each standing building's facade bearing on the scene date, where its record has one."""
    out = {}
    for path in (DATA / "structures").glob("*.json"):
        for ph in load(path).get("phases") or []:
            rng, pos = ph.get("documented_range") or {}, ph.get("position") or {}
            if pos.get("rotation_deg") is None:
                continue
            if rng.get("from", "0000") <= "1835-07-01" <= rng.get("to", "9999"):
                out[path.stem] = float(pos["rotation_deg"]) % 360.0
                break
    return out


def faces_this_street(sid: str, frame: dict) -> bool:
    """A building whose front looks at this face's street (within 45 degrees), or one whose
    bearing is unknown, keeps its dooryard to it."""
    bearing = bearings_1835().get(sid)
    if bearing is None:
        return True
    return abs((bearing - frame["bearing"] + 180.0) % 360.0 - 180.0) <= 45.0


def door_apron(sid: str, poly) -> list | None:
    """The DOOR_GROUND_M of ground before a building's front wall, whichever street it faces:
    a store laid on any face keeps off it, so no door opens onto a store's side or back."""
    bearing = bearings_1835().get(sid)
    if bearing is None or _area(poly) < MIN_DOORYARD_M2:
        return None
    out = (math.sin(math.radians(bearing)), math.cos(math.radians(bearing)))
    reach = [p[0] * out[0] + p[1] * out[1] for p in poly]
    front = [p for p, r in zip(poly, reach) if r >= max(reach) - 0.5]
    side = (out[1], -out[0])
    a = min(front, key=lambda p: p[0] * side[0] + p[1] * side[1])
    b = max(front, key=lambda p: p[0] * side[0] + p[1] * side[1])
    return [a, b, (b[0] + out[0] * DOOR_GROUND_M, b[1] + out[1] * DOOR_GROUND_M),
            (a[0] + out[0] * DOOR_GROUND_M, a[1] + out[1] * DOOR_GROUND_M)]


def _area(poly) -> float:
    return abs(sum(p[0] * q[1] - q[0] * p[1] for p, q in zip(poly, poly[1:] + poly[:1]))) / 2.0


def measure_face(frame: dict, standing) -> dict:
    """Built length within BUILT_BAND_M of the line, and every footprint in the body band."""
    length = frame["length"]
    held, near, aprons = [], [], []
    for sid, poly in standing:
        apron = door_apron(sid, poly)
        if apron:
            ap = [project(frame, p) for p in apron]
            if max(q[1] for q in ap) >= -BODY_BAND_M and min(q[1] for q in ap) <= 0.5:
                aprons.append((min(q[0] for q in ap), max(q[0] for q in ap)))
        pr = [project(frame, p) for p in poly]
        lo, hi = min(q[0] for q in pr), max(q[0] for q in pr)
        front = max(q[1] for q in pr)          # the wall nearest the street (outward +)
        if hi < -2.0 or lo > length + 2.0 or front > 0.5:
            continue
        if front >= -BUILT_BAND_M:
            held.append((max(0.0, lo), min(length, hi)))
        if front >= -DOORYARD_M:
            near.append({"id": sid, "lo": lo, "hi": hi, "front": front, "area": _area(poly),
                         "faces": faces_this_street(sid, frame)})
    merged = []
    for a, b in sorted(held):
        if merged and a <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], b)
        else:
            merged.append([a, b])
    built = sum(b - a for a, b in merged)
    return {"length": length, "built": built, "held": merged, "aprons": aprons,
            "near": sorted(near, key=lambda o: o["lo"])}


def _minus(span: tuple[float, float], cuts) -> list[tuple[float, float]]:
    out = [span]
    for c0, c1 in cuts:
        out = [piece for a, b in out for piece in ((a, min(b, c0)), (max(a, c1), b)) if piece[1] > piece[0]]
    return out


def open_share(front: dict) -> tuple[float, float]:
    """(the face's length the row may stand on, how much of it is built): all of it, but on a
    cross street's face less the alley's mouth and the half of a block that fronts Randolph."""
    usable = _minus((0.0, front["length"]), front.get("closed", []))
    built = sum(max(0.0, min(b, d) - max(a, c)) for a, b in usable for c, d in front["held"])
    return sum(b - a for a, b in usable), built


def street_lines(exclude: str = PREFIX) -> dict[tuple[str, str], float]:
    """The setback every other generator's frontage row already stands at on a face: a
    block face carries one street line (tools/measure_street_line.py), so the row-fill
    stores stand on the line a face already has, and on SETBACK_M only where it has none."""
    lines: dict[tuple[str, str], set] = {}
    for path in (DATA / "structures").glob("*.json"):
        if path.stem.startswith(exclude):
            continue
        fr = ((load(path).get("reconstruction") or {}).get("frontage") or {})
        if fr.get("block") and fr.get("face") and fr.get("setback_m") is not None:
            lines.setdefault((fr["block"], fr["face"]), set()).add(round(float(fr["setback_m"]), 3))
    out = {}
    for key, found in lines.items():
        if len(found) != 1:
            raise ValueError(f"{key} already carries {len(found)} street lines {sorted(found)}")
        out[key] = found.pop()
    return out


def addressed_lots() -> list[list[tuple[float, float]]]:
    """The lots a printed lot address names (data/research/newspapers/lot_addresses.json).
    An address places the one building that stands on its lot (tools/lot_addresses.py), so
    the row fill raises nothing on one: a second roof would unplace the first."""
    import lot_addresses  # noqa: E402
    if not lot_addresses.LEDGER.exists():
        return []
    return [lot_addresses.lot_polygon(a) for a in load(lot_addresses.LEDGER).get("addresses", [])]


def street_faces() -> list[tuple[str, str, str, str]]:
    """(block, face, street, side) for every front the row fills, South Water's and Lake's first."""
    out = [(f"blk_{prefix}_{cross}", face, street, side)
           for cross in CROSS for prefix, face, street, side in FACES]
    for cross in CROSS:
        for prefix, face in CROSS_FACES:
            street = cross if face == "west" else NEXT_EAST.get(cross)
            if street:
                out.append((f"blk_{prefix}_{cross}", face, street,
                            "east side" if face == "west" else "west side"))
    return out


ALLEY_MOUTH_M = 1.0   # a cross-street row keeps the alley's mouth open, and this beside it
CROSS_REACH_M = 25.0  # how far a main street's row turns the corner up a cross street


def closed_stations(block: dict, frame: dict) -> list[tuple[float, float]]:
    """On a cross street's face, the alley's mouth; and on a Lake-Randolph block, everything
    south of the alley, which fronts Randolph's half of the block, not Lake's."""
    if frame["bearing"] % 180.0 < 45.0 or frame["bearing"] % 180.0 > 135.0:
        return []                                   # a north or south face: no alley mouth
    alley = block.get("alley_local_enu_m") or []
    if not alley:
        return []
    st = [project(frame, p)[0] for p in alley]
    lo, hi = min(st) - ALLEY_MOUTH_M, max(st) + ALLEY_MOUTH_M
    closed = [(lo, hi)]
    if block["bounded_by"].get("north") == "lake":
        north = max(block["boundary_local_enu_m"], key=lambda p: p[1])
        if project(frame, north)[0] > hi:
            closed.append((-1e9, hi))
        else:
            closed.append((lo, 1e9))
    # the row turns the corner: only the stretch within CROSS_REACH_M of a main street
    ends = [0.0, frame["length"]]
    if block["bounded_by"].get("north") == "lake":
        north = max(block["boundary_local_enu_m"], key=lambda p: p[1])
        ends = [min(ends, key=lambda e: abs(e - project(frame, north)[0]))]
    reach = sorted((max(0.0, e - CROSS_REACH_M), min(frame["length"], e + CROSS_REACH_M)) for e in ends)
    gaps, s = [], -1e9
    for a, b in reach:
        if a > s:
            gaps.append((s, a))
        s = max(s, b)
    gaps.append((s, 1e9))
    return closed + gaps


def fronts(datum: dict, standing, faces=None) -> list[dict]:
    blocks = {b["id"]: b for b in load(LOTS)["blocks"]}
    lines = street_lines()
    rings = addressed_lots()
    out = []
    for bid, face, street, side in (faces or street_faces()):
        frame = face_frame(blocks[bid], face)
        m = measure_face(frame, standing)
        m["addressed"] = []
        for ring in rings:
            pr = [project(frame, p) for p in ring]
            if max(q[1] for q in pr) > -BODY_BAND_M and min(q[1] for q in pr) < 0.5:
                m["addressed"].append((min(q[0] for q in pr), max(q[0] for q in pr)))
        m["closed"] = closed_stations(blocks[bid], frame)
        out.append({"block": bid, "face": face, "street": street, "side": side,
                    "frame": frame, "setback": lines.get((bid, face), SETBACK_M), **m,
                    "drawn": (bid, face) in DRAWN_FACES})
    return out


def free_stretches(front: dict) -> tuple[list[tuple[float, float]], list[str]]:
    """Open stations along the face: clear of every building a store's body would reach, and
    of the dooryard before every building set back within DOORYARD_M of the line."""
    hard = []
    for o in front["near"]:
        if o["front"] >= -BODY_BAND_M:
            gap = (INVENTED_GAP_M if o["id"] in household_layer() else OTHER_GAP_M) + 0.05
            hard.append((o["lo"] - gap, o["hi"] + gap))
        if o["area"] >= MIN_DOORYARD_M2 and o["faces"]:
            hard.append((o["lo"] - LANE_M, o["hi"] + LANE_M))
    hard += front.get("addressed", []) + front.get("closed", [])
    hard += [(a - OTHER_GAP_M, b + OTHER_GAP_M) for a, b in front.get("aprons", [])]
    lo, hi = CORNER_M, front["length"] - CORNER_M
    stretches, s = [], lo
    for a, b in sorted(hard):
        if a > s:
            stretches.append((s, min(a, hi)))
        s = max(s, b)
    if s < hi:
        stretches.append((s, hi))
    return [(a, b) for a, b in stretches if b - a > 5.0], []


#: how far inside its family's ridge band a store's modelled ridge (eave + run x tan
#: pitch, tools/ridge_model.py, which the baked ridge meets to the millimetre) must stand
RIDGE_CLEAR_M = 0.005


def ridge_width(fam: str, spec: dict, sid: str, width: float, depth: float
                ) -> tuple[float, float]:
    """The sampled store, widened inside its family's width band where the sampled
    frontage is too narrow for any pitch the family allows to carry its ridge into the
    family's ridge band (tools/measure_ridge_band.py measures the baked one). The pitch
    band and the ridge band are both the family's; the width is what gives way, and
    never past the family's own widest."""
    from family_bands import ridge_band_m
    from ridge_model import ridge_run_m
    band = ridge_band_m(spec.get("ridge_ft"))
    if band is None:
        return width, depth
    hi_w = spec["band_ft"][2] * .3048
    w = width
    while True:
        form = form_for(fam, spec, sid, w, depth, "unpainted")
        val = lambda k: (form[k]["value"] if isinstance(form.get(k), dict) else form.get(k))
        run = ridge_run_m(spec["archetype"], val("roof_type") or "gable", w, depth,
                          val("gable_front"))
        if run is None:
            return width, depth
        ridge = val("wall_height_m") + run * math.tan(math.radians(val("roof_pitch_deg")))
        if ridge >= band[0] + RIDGE_CLEAR_M or w >= hi_w - 1e-6:
            return round(w, 3), depth
        w = min(hi_w, w + 0.05)


def lay_front(front: dict, table: dict, seq0: int) -> tuple[list[dict], list[str]]:
    """The stores this face takes, largest open stretch first, until it reaches the target."""
    if front["drawn"]:
        return [], []
    usable, built = open_share(front)
    want = TARGET_SHARE * usable - built
    if want <= 3.0:
        return [], []
    stretches, _ = free_stretches(front)
    laid, seq, added, beat = [], seq0, 0.0, seq0  # each face enters the rhythm where the last left it
    for a, b in sorted(stretches, key=lambda st: st[1] - st[0], reverse=True):
        s = a
        while added < want:
            fam = RHYTHM[beat % len(RHYTHM)]
            if (front["street"] == "lake" and b - a >= H3_MIN_STRETCH_M and s == a
                    and not any(x["family"] == "H3" for x in laid)):
                fam = "H3"
            sid = f"{PREFIX}{fam.lower()}_{seq + 1:03d}"
            width, depth = ridge_width(fam, table[fam], sid,
                                       *dimensions_m(fam, table[fam]["band_ft"], sid))
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
    return laid, []


def centre_of(front: dict, x: dict) -> tuple[float, float]:
    fr = front["frame"]
    mid = (x["station"][0] + x["station"][1]) / 2.0
    off = front["setback"] + x["depth"] / 2.0
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
                         "about 70 % of each block front, and turning the corner up the "
                         "cross streets' fronts for 25 m. No evidence establishes that this "
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
                         f"end, its front wall {front['setback']:.2f} m behind the lot line ("
                         + ("the plat module's margin, as the block programme's own party-line "
                            "runs stand" if front["setback"] == SETBACK_M else
                            "the street line this face's earlier row already stands on; a "
                            "block face carries one") +
                         f"). The bearing is the face's, so the front looks square at "
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
                         "setback_m": front["setback"], "abuts": None,
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


def build(datum: dict | None = None):
    datum = datum or load(DATA / "datum.json")
    table, people = families(), occupancy()
    mine = {p.stem for p in (DATA / "structures").glob(PREFIX + "*.json")}
    standing = standing_1835(datum, mine)
    records, moves, seq, summary = [], {}, 0, []
    faces = street_faces()
    main = [f for f in faces if f[1] in ("north", "south")]
    cross = [f for f in faces if f[1] in ("east", "west")]

    def lay(fs):
        nonlocal seq
        for front in fs:
            laid, mv = lay_front(front, table, seq)
            seq += len(laid)
            for x in laid:
                records.append(make_record(front, x, table, datum, people,
                                           int(x["id"].rsplit("_", 1)[1])))
            usable, built = open_share(front)
            added = sum(x["width"] for x in laid)
            summary.append({"block": front["block"], "face": front["face"],
                            "street": f"{STREET_NAME[front['street']]} ({front['side']})",
                            "length_m": round(usable, 1),
                            "built_m": round(built, 1),
                            "built_pct": round(100 * built / usable, 1),
                            "stores": len(laid),
                            "families": [x["family"] for x in laid],
                            "after_pct": round(100 * (built + added) / usable, 1),
                            "moves": mv, "drawn": front["drawn"]})

    lay(fronts(datum, standing, main))
    # the cross streets' fronts are measured with the main streets' new rows standing, so a
    # Lake or South Water corner store holds its corner on the cross street too
    laid = [(r["id"], world_polygon(r["phases"][0], datum)) for r in records]
    laid += [(r["id"], e) for r in records for e in [rear_ell(r, datum)] if e]
    lay(fronts(datum, standing + laid, cross))
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
    # a committed row-fill store this run no longer writes is not another building
    others = [(o, q) for o, q in standing_1835(datum, ids) if not o.startswith(PREFIX)]
    own = [(r["id"], world_polygon(r["phases"][0], datum)) for r in records]
    ells = [(r["id"], e) for r in records for e in [rear_ell(r, datum)] if e]
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
    blocks, frames = {b["id"]: b for b in load(LOTS)["blocks"]}, {}
    for record, (sid, poly) in zip(records, own):
        importlib.import_module("archetypes." + record["archetype"] + "_params").from_phase(
            record["phases"][0], record)
        street, depth = intrusion(poly, lanes)
        if street:
            raise ValueError(f"{sid} intrudes {depth:.2f} m into {street}")
        for name, ring in refused.items():
            if overlap_area(ring, poly) > 1e-3:
                raise ValueError(f"{sid} stands on refused ground {name}")
        near_row = min((_gap(poly, q) for o, q in own + ells if o != sid), default=99.0)
        if near_row < ROW_GAP_M - 2e-3:  # positions round to the millimetre
            raise ValueError(f"{sid} stands {near_row:.2f} m from a neighbour in its own row")
        near = min(((_gap(poly, q), o) for o, q in others + moved), default=(99.0, None))
        if near[0] < OTHER_GAP_M - 2e-3:
            raise ValueError(f"{sid} stands {near[0]:.2f} m from {near[1]}")
        invented = min(((_gap(poly, q), o) for o, q in others if o in household_layer()),
                       default=(99.0, None))
        if invented[0] < INVENTED_GAP_M - 2e-3:
            raise ValueError(f"{sid} stands {invented[0]:.2f} m from {invented[1]}, the household "
                             f"layer's premises, which keep {INVENTED_GAP_M} m")
        rec = record["reconstruction"]["frontage"]
        frame = frames.setdefault((rec["block"], rec["face"]),
                                  face_frame(blocks[rec["block"]], rec["face"]))
        mine = [project(frame, p) for p in poly]
        lo, hi = min(q[0] for q in mine), max(q[0] for q in mine)
        for o, q in others + [x for x in own if x[0] != sid]:
            apron = door_apron(o, q)
            if apron and overlap_area(apron, poly) > 1e-3:
                raise ValueError(f"{sid} stands on the ground before {o}'s front door")
            if o.startswith(PREFIX) or _area(q) < MIN_DOORYARD_M2 or not faces_this_street(o, frame):
                continue
            pr = [project(frame, p) for p in q]
            behind = max(t[1] for t in pr)
            if -DOORYARD_M <= behind <= 0.5 and min(t[0] for t in pr) - LANE_M < hi - 2e-3 \
                    and max(t[0] for t in pr) + LANE_M > lo + 2e-3:
                raise ValueError(f"{sid} stands across the dooryard of {o}, whose front stands "
                                 f"{-behind:.1f} m behind the line: its way to the street is shut")
        report.append(f"{sid}: nearest other {near[0]:.2f} m ({near[1]})")
    for sid, ell in ells:
        near = min(((_gap(ell, q), o) for o, q in others + [x for x in own if x[0] != sid]),
                   default=(99.0, None))
        if near[0] < ROW_GAP_M - 2e-3:
            raise ValueError(f"{sid}'s rear ell stands {near[0]:.2f} m from {near[1]}")
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
    # a store slid along its face to stand before a set-back house's door
    blocks = {b["id"]: b for b in load(LOTS)["blocks"]}
    others = [(o, q) for o, q in standing_1835(datum, {r["id"] for r in records})
              if not o.startswith(PREFIX) and _area(q) >= MIN_DOORYARD_M2]
    for k, r in enumerate(records):
        fr = r["reconstruction"]["frontage"]
        frame = face_frame(blocks[fr["block"]], fr["face"])
        mine = [project(frame, p) for p in world_polygon(r["phases"][0], datum)]
        mid = (min(q[0] for q in mine) + max(q[0] for q in mine)) / 2
        house = next(([project(frame, p) for p in q] for o, q in others
                      if -DOORYARD_M <= max(project(frame, p)[1] for p in q) <= -BODY_BAND_M
                      and 0 <= project(frame, q[0])[0] <= frame["length"]), None)
        if house:
            shift = (min(t[0] for t in house) + max(t[0] for t in house)) / 2 - mid
            slid = copy.deepcopy(records)
            pos = slid[k]["phases"][0]["position"]
            pos["utm_e"] += frame["along"][0] * shift
            pos["utm_n"] += frame["along"][1] * shift
            cases.append(("a store across a house's dooryard", slid))
            break
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
    print(f"PASS: {len(records)} core row-fill stores, no house moved"
          + (" rederive exactly" if args.check else " written"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
