#!/usr/bin/env python3
"""Build T-2268's two reconstructed South Division river warehouses on the South Branch bank.

The order book's South `warehouses_freight/street_line` band sets ten roofs and finds seven
standing, and the 668-roof schedule has nowhere left to put the three it owes: every South
Water lot is held, no free South lot stands within the bank-landing reach of the water, and
the Dearborn reach's bank takes no more sheds. So all three sat on the gated balance south
of Madison, which is ground with no river. This writes the two F3s of the three from
`data/reconstruction/1835_south_freight_bank.json` instead: large river warehouses on the
dry, unplatted strip between Market Street and the South Branch, between Madison and
Washington, the ground Newberry & Dole's works already use a block further north.

THE CLAUSE IS THE BANK LANDING (`bank_landing` in tools/placement_policy_1835.py, T-2022),
and the recipe's `basis` argues it. The validator holds each roof inside the clause's reach
of the traced water and at least the bank setback off it, so the anonymous-roof audit reads
them as conforming. The F4 lumber shed the band also owes is NOT built here: the clause
admits F1-F3 only (T-2269).

It authors NO coordinate of its own. Each roof is measured off two committed street lines —
Market Street's west corridor edge and Madison Street's north one, both from
`plat_corridors` — with the footprint from the family band and the form from the same
helpers the block parcels use. Every value is an invention bounded by the reconstruction
specification and graded `reconstructed`; this is not a lot, and nobody's reading puts a
building here.

    python3 tools/generate_south_freight.py            write the records
    python3 tools/generate_south_freight.py --check    they re-derive byte for byte
    python3 tools/generate_south_freight.py --self-test  the validator refuses bad ground
"""

from __future__ import annotations

import argparse
import copy
import importlib
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
sys.path[:0] = [str(ROOT / "tools"), str(ROOT / "generators")]

from family_bands import families, dimensions_m  # noqa: E402
from generate_block_infill import form_for, invented, no_build_rings, FUNCTIONS  # noqa: E402
from generate_block_infill import point_in_polygon  # noqa: E402
from generate_west_infill import footprint_origin, omitted_street_corridors  # noqa: E402
from plat_corridors import corridors, intrusion  # noqa: E402
from plat_occupancy import world_polygon, footprints, overlap_area  # noqa: E402
from heightfield import Heightfield  # noqa: E402
from siding_stock import deal_records as deal_siding  # noqa: E402
import fabric_rule_1835  # noqa: E402  (T-1816: the finish says whose house it is)
from check_structure_corridors import laps as street_laps  # noqa: E402  (T-1743)
from placement_policy_1835 import bank_landing_reach_m  # noqa: E402  (the clause it stands on)
from generate_north_freight import point_segment_distance, separation  # noqa: E402

CORRIDOR_LINE = "drawn"
CORRIDOR_LINE_WHY = ("A question about a roof beside a street: each warehouse is measured off "
                     "Market's and Madison's drawn corridors and checked against the drawn "
                     "corridors it must stay out of.")

RECIPE = DATA / "reconstruction" / "1835_south_freight_bank.json"
LOTS = DATA / "traces" / "vectors" / "thompson_lots.json"
EPOCH = DATA / "terrain" / "epochs" / "e1834_harbor_cut"
SOURCE = "owner_chicago_1835_reconstruction_spec_2026"

BANK_SETBACK_M = 8.0      # the anonymous principal-roof setback from the traced bank, as at the forks
CLEARANCE_M = 3.0         # the three-metre separation every parcel generator holds
RELIEF_M = 0.30           # the generators' own relief bound, the one measure_south_bank_ground reads


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def street_edge(street: str, west: bool) -> tuple[tuple[float, float], tuple[float, float]]:
    """The southmost segment of Market Street's west corridor edge, south end first: the
    side of the street the bank is on, over the stretch from Madison to Washington. Read
    from the corridor ring by the x of its vertices, so nothing is typed in."""
    ring = corridors()[street]["ring"]
    half = sorted(ring, key=lambda p: p[0])[:len(ring) // 2] if west else ring
    a, b = sorted(half, key=lambda p: p[1])[:2]
    return a, b


def corner_station(edge, corner: str) -> float:
    """Metres along the edge from its south end to where it leaves `corner`'s corridor:
    Madison Street's north line, read on the drawn corridor at a centimetre step."""
    (ae, an), (be, bn) = edge
    length = math.hypot(be - ae, bn - an)
    ring = [tuple(p) for p in corridors()[corner]["ring"]]
    step = 0.01
    s = 0.0
    while s < length:
        t = s / length
        if not point_in_polygon((ae + t * (be - ae), an + t * (bn - an)), ring):
            return s
        s += step
    raise ValueError(f"the edge never leaves {corner}'s corridor")


def seats(recipe: dict) -> list[tuple[dict, float, float, float, float, float]]:
    """Every placement's origin and bearing, walked north from Madison's corner in order:
    (row, width, depth, east, north, bearing). Each roof's back wall stands
    `rear_setback_m` inside Market's west line and its front faces the branch."""
    edge = street_edge(recipe["street"], west=True)
    (ae, an), (be, bn) = edge
    length = math.hypot(be - ae, bn - an)
    along = ((be - ae) / length, (bn - an) / length)
    west = (-along[1], along[0])                     # left of a northward walk is west
    if west[0] > 0:
        west = (-west[0], -west[1])
    station = corner_station(edge, recipe["corner_street"])
    out = []
    table = families()
    for row in recipe["placements"]:
        spec = table[row["family"]]
        width, depth = dimensions_m(row["family"], spec["band_ft"], row["geometry_seed"])
        station += float(row.get("station_m", row.get("gap_m", 0.0)))
        mid = station + width / 2
        offset = float(row["rear_setback_m"]) + depth / 2
        centre = (ae + along[0] * mid + west[0] * offset,
                  an + along[1] * mid + west[1] * offset)
        # The archetypes put the facade on max-v (+Y); point +Y west, at the branch.
        bearing = math.degrees(math.atan2(*west)) % 360
        east, north = footprint_origin(*centre, width, depth, bearing)
        out.append((row, width, depth, east, north, bearing))
        station += width
    return out


def make_record(recipe: dict, datum: dict, seat: tuple) -> dict:
    row, width, depth, east, north, bearing = seat
    family, seed = row["family"], row["geometry_seed"]
    sequence = int(row["sequence"])
    spec = families()[family]
    fabric = fabric_rule_1835.deal(row["structure_id"], family, spec["archetype"])
    finish, paint = fabric["finish_key"], fabric["paint"]
    where = ("at the Madison Street corner" if sequence == 1
             else "north of the first across a cart way")
    return {
        "id": row["structure_id"],
        # The anonymous programme's production name, which display-name.js reads into the
        # title a visitor sees ("A vacant large river warehouse"); any other shape is
        # shown verbatim and the smoke refuses it.
        "name": f"Reconstructed {family} {spec['label'].lower()} #{sequence:03d}",
        "archetype": spec["archetype"],
        "phases": [{
            "id": "inferred_1835",
            "documented_range": {
                "from": "1835-01-01", "to": "1835-12-31", "confidence": "reconstructed",
                "note": "An invented count-unit for July 1835, not evidence that this particular building existed."},
            "position": {
                "utm_e": round(datum["origin_utm_e"] + east, 3),
                "utm_n": round(datum["origin_utm_n"] + north, 3),
                "rotation_deg": round(bearing, 6),
                "symbolic_location": f"Reconstructed river warehouse on the South Branch's east bank below Market Street, {where}, facing the branch",
                "confidence": "reconstructed",
                "note": (f"Off the plat: the strip between Market Street's corridor and the "
                         f"traced water carries no lot line. The roof's back wall stands "
                         f"{row['rear_setback_m']} m inside Market's west line and its front "
                         "faces the branch it would load from, as Newberry & Dole's packing "
                         "house does on the same bank. Chosen under the bank-landing clause "
                         "(T-2268): no South Water lot is free and the Dearborn reach takes no "
                         "more, and this is the empty stretch of the one bank left, between "
                         "Madison and Washington; no source seats a building here."),
                "derivation": {"method": "not_derivable",
                               "reason": "No parcel-by-parcel July 1835 South Division roof register survives in the supplied evidence."}},
            "footprint": {
                "polygon": [[0, 0], [width, 0], [width, depth], [0, depth]],
                "confidence": "reconstructed",
                "note": f"Deterministically sampled {width:.3f} by {depth:.3f} metre rectangle inside the {family} typology band; neither dimension is attested for this invented roof."},
            "form": fabric_rule_1835.apply_form(
                form_for(family, spec, seed, width, depth, paint), fabric),
            "change_note": "T-2268 adds one of the South street line's owed freight roofs without moving an existing building."}],
        "function": invented(FUNCTIONS[family],
                             f"The {family} type fills the South Division's street-line freight band in the order book. No forwarder, owner or cargo is recovered for it."),
        "reconstruction": {
            "status": "inferred_anonymous", "family": family, "district": "south",
            "inventory_class": "principal_functional",
            "programme_phase": recipe["id"], "source_id": SOURCE,
            "sequence": sequence, "finish_key": finish,
            "roof_condition": fabric["roof_condition"], "age_state": fabric["age_state"],
            "fabric_basis": fabric["fabric_basis"]},
        "research_note": ("RECONSTRUCTED, NOT A RECOVERED ADDRESS. The order book's South "
                          "street-line freight band sets ten roofs and seven stood; this is "
                          f"the {'eighth' if sequence == 1 else 'ninth'}. The family, the place "
                          "on the bank, the dimensions, the finish and every form value are "
                          "inventions bounded by the reconstruction specification and recorded "
                          "in docs/LIBERTIES.md. A named South Branch warehouse, if one is ever "
                          "read, replaces it."),
        "review_required": False,
    }


def water_rings(datum: dict) -> list[list[tuple[float, float]]]:
    water = []
    for filename in ("river.geojson", "branches.geojson", "shoreline.geojson"):
        path = EPOCH / filename
        if not path.exists():
            continue
        for feature in load(path)["features"]:
            if feature["properties"].get("kind") == "water" and feature["geometry"]["type"] == "Polygon":
                water.append([(e - datum["origin_utm_e"], n - datum["origin_utm_n"])
                              for e, n in feature["geometry"]["coordinates"][0]])
    return water


def validate(records: list[dict], recipe: dict, datum: dict) -> str:
    rows = recipe["placements"]
    if [r["id"] for r in records] != [p["structure_id"] for p in rows] or \
            [r["reconstruction"]["family"] for r in records] != [p["family"] for p in rows]:
        raise ValueError("the records' identities or families are not the recipe's")
    lanes = {**corridors(), **omitted_street_corridors()}
    water = water_rings(datum)
    if not water:
        raise ValueError("no traced water was read, so the bank setback cannot be held")
    field = Heightfield.load(EPOCH)
    if field is None:
        raise ValueError("committed terrain is required")
    lots = [[tuple(p) for p in lot["polygon"]]
            for block in load(LOTS)["blocks"] for lot in block["lots"]]
    mine = {r["id"] for r in records}
    others = footprints(datum, mine)
    market = street_edge(recipe["street"], west=True)
    polys = {}
    report = []
    for record, row in zip(records, rows):
        phase = record["phases"][0]
        importlib.import_module("archetypes." + record["archetype"] + "_params").from_phase(phase)
        poly = world_polygon(phase, datum)
        polys[record["id"]] = poly
        street, depth = intrusion(poly, lanes)
        if street:
            raise ValueError(f"{record['id']} intrudes into {street}: {depth:.3f} m")
        for lap in street_laps({record["id"]: record}, datum=datum):
            raise ValueError(f"{record['id']} stands {lap['depth_m']} m inside "
                             f"{lap['street']}'s drawn corridor")
        for name, ring in no_build_rings().items():
            if overlap_area(ring, poly) > .001:
                raise ValueError(f"{record['id']} intersects refused ground {name}")
        # Off the plat, and it says so: a roof that reached onto a platted lot would be the
        # block generator's to deal, and this recipe would be a way around its refusals.
        for lot in lots:
            if overlap_area(lot, poly) > .01:
                raise ValueError(f"{record['id']} stands on a platted lot")
        bank = min(separation(poly, ring) for ring in water)
        if bank < BANK_SETBACK_M:
            raise ValueError(f"{record['id']} is only {bank:.2f} m from traced water")
        # The clause that admits it: nothing between this roof and the river at all.
        if bank > bank_landing_reach_m():
            raise ValueError(f"{record['id']} stands {bank:.2f} m from traced water, beyond "
                             f"bank_landing's {bank_landing_reach_m():.2f} m")
        heights = [field.height(*p) for p in poly]
        if not all(field.covers(*p) for p in poly) or min(heights) < 0:
            raise ValueError(f"{record['id']} lacks dry modelled ground at every corner")
        if max(heights) - min(heights) > RELIEF_M:
            raise ValueError(f"{record['id']} stands on {max(heights) - min(heights):.2f} m "
                             f"of relief, beyond the generators' {RELIEF_M} m")
        nearest = min((separation(poly, other), name) for name, other in others)
        if nearest[0] < CLEARANCE_M:
            raise ValueError(f"{record['id']} has only {nearest[0]:.3f} m clearance from {nearest[1]}")
        # GLB contract: the facade is max-v, polygon vertices 2 and 3. It must face the
        # branch, so its back (vertices 0 and 1) is the side nearest Market Street.
        front = min(point_segment_distance(*p, *market) for p in poly[2:4])
        back = min(point_segment_distance(*p, *market) for p in poly[:2])
        if not abs(back - float(row["rear_setback_m"])) < .01 or front <= back + 3:
            raise ValueError(f"{record['id']} does not face the branch: back {back:.3f}, front {front:.3f} m")
        report.append(f"{record['id']}: back {back:.2f} m inside Market's line, traced bank "
                      f"{bank:.2f} m, nearest {nearest[0]:.2f} m ({nearest[1]}), ground "
                      f"{min(heights):.2f} m, relief {max(heights) - min(heights):.2f} m")
    ids = list(polys)
    for i, a in enumerate(ids):
        for b in ids[i + 1:]:
            gap = separation(polys[a], polys[b])
            if gap < CLEARANCE_M:
                raise ValueError(f"{a} has only {gap:.3f} m clearance from {b}")
    return "\n".join(report)


def records_from_inputs() -> tuple[list[dict], str]:
    recipe, datum = load(RECIPE), load(DATA / "datum.json")
    records = [make_record(recipe, datum, seat) for seat in seats(recipe)]
    deal_siding(records)
    return records, validate(records, recipe, datum)


def self_test() -> int:
    records, _ = records_from_inputs()
    recipe, datum = load(RECIPE), load(DATA / "datum.json")
    cases = []
    roadway = copy.deepcopy(records)
    roadway[0]["phases"][0]["position"]["utm_e"] += 10
    cases.append(("a roof moved into Market Street", roadway))
    corner = copy.deepcopy(records)
    corner[0]["phases"][0]["position"]["utm_n"] -= 8
    cases.append(("a roof moved into Madison Street", corner))
    wet = copy.deepcopy(records)
    wet[1]["phases"][0]["position"]["utm_e"] -= 30
    cases.append(("a roof moved down the bank into the branch", wet))
    crowded = copy.deepcopy(records)
    crowded[1]["phases"][0]["position"]["utm_n"] = crowded[0]["phases"][0]["position"]["utm_n"] + 12
    cases.append(("two roofs closer than the parcel clearance", crowded))
    backwards = copy.deepcopy(records)
    phase = backwards[0]["phases"][0]
    poly = world_polygon(phase, datum)
    centre = [sum(p[i] for p in poly) / 4 for i in (0, 1)]
    width, depth = phase["footprint"]["polygon"][2]
    bearing = (phase["position"]["rotation_deg"] + 180) % 360
    east, north = footprint_origin(*centre, width, depth, bearing)
    phase["position"].update(utm_e=datum["origin_utm_e"] + east,
                             utm_n=datum["origin_utm_n"] + north, rotation_deg=bearing)
    cases.append(("a warehouse turned to face Market Street", backwards))
    wrong = copy.deepcopy(records)
    wrong[0]["reconstruction"]["family"] = "F4"
    cases.append(("a family the recipe did not order", wrong))
    for label, mutated in cases:
        try:
            validate(mutated, recipe, datum)
        except (ValueError, SystemExit):
            print("PASS self-test: refuses " + label)
        else:
            print("FAIL self-test: did not refuse " + label)
            return 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        return self_test()
    records, report = records_from_inputs()
    print(report)
    stale = []
    for record in records:
        path = DATA / "structures" / (record["id"] + ".json")
        content = json.dumps(record, indent=2, ensure_ascii=False) + "\n"
        if args.check:
            if not path.exists() or path.read_text(encoding="utf-8") != content:
                stale.append(str(path.relative_to(ROOT)))
            continue
        path.write_text(content, encoding="utf-8")
        print(f"PASS: wrote {path.relative_to(ROOT)}")
    if args.check:
        if stale:
            print("FAIL: does not re-derive: " + ", ".join(stale))
            return 1
        print("PASS: the South Branch freight roofs re-derive exactly")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
