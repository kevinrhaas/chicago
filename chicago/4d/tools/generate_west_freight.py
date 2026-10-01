#!/usr/bin/env python3
"""Build T-1773's one reconstructed West Division freight roof at the forks.

The order book left the West's freight row one roof short (2 set, 1 standing), and this
writes that roof from `data/reconstruction/1835_west_freight_forks.json`: an F2 narrow
two-storey warehouse on plat lot 1 of `blk_west_lake_canal`, the Lake and West Water
corner, its front on the lot's West Water line and its rear toward the alley.

It authors NO coordinate of its own. The lot is read from the committed plat
(`data/traces/vectors/thompson_lots.json`), the footprint from the family band, the form
from the same helpers the block parcels use. Every value is an invention bounded by the
reconstruction specification and graded `reconstructed`; the lot number is the plat's,
the building on it is not anybody's reading.

    python3 tools/generate_west_freight.py            write the record
    python3 tools/generate_west_freight.py --check    it re-derives byte for byte
    python3 tools/generate_west_freight.py --self-test  the validator refuses bad ground
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
from generate_block_infill import form_for, finish_for, invented, no_build_rings, FUNCTIONS  # noqa: E402
from generate_west_infill import footprint_origin, omitted_street_corridors  # noqa: E402
from plat_corridors import corridors, intrusion  # noqa: E402
from plat_occupancy import world_polygon, footprints, overlap_area  # noqa: E402
from heightfield import Heightfield  # noqa: E402
from siding_stock import deal_records as deal_siding  # noqa: E402

CORRIDOR_LINE = "drawn"
CORRIDOR_LINE_WHY = ("A question about a roof on a lot: the warehouse stands on the plat's own "
                     "lot and is checked against the drawn street corridors it must stay out of.")
RECIPE = DATA / "reconstruction" / "1835_west_freight_forks.json"
LOTS = DATA / "traces" / "vectors" / "thompson_lots.json"
EPOCH = DATA / "terrain" / "epochs" / "e1834_harbor_cut"
SOURCE = "owner_chicago_1835_reconstruction_spec_2026"
BANK_SETBACK_M = 8.0      # the West memo's anonymous principal-roof setback from the traced bank
CLEARANCE_M = 3.0         # the three-metre separation every parcel generator holds


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def lot_polygon(block_id: str, column: str, row: int) -> list[tuple[float, float]]:
    def walk(node):
        if isinstance(node, dict):
            if node.get("id") == block_id and "lots" in node:
                return node
            for value in node.values():
                hit = walk(value)
                if hit:
                    return hit
        elif isinstance(node, list):
            for value in node:
                hit = walk(value)
                if hit:
                    return hit
        return None
    block = walk(load(LOTS))
    if block is None:
        raise ValueError(f"{block_id} is not in the committed plat")
    lots = [l for l in block["lots"] if l["column"] == column and l["row"] == row]
    if len(lots) != 1:
        raise ValueError(f"{block_id} has no single {column} lot in row {row}")
    return [tuple(p) for p in lots[0]["polygon"]]


def front_edge(lot: list[tuple[float, float]]) -> tuple[tuple[float, float], tuple[float, float]]:
    """The lot's street line: the edge whose midpoint lies farthest east (West Water side)."""
    edges = list(zip(lot, lot[1:] + lot[:1]))
    return max(edges, key=lambda e: (e[0][0] + e[1][0]) / 2)


def seat(lot, width: float, depth: float, setback: float) -> tuple[float, float, float]:
    """Centre the roof on the lot's frontage, `setback` metres inside its street line."""
    (ae, an), (be, bn) = front_edge(lot)
    de, dn = be - ae, bn - an
    length = math.hypot(de, dn)
    cx = sum(p[0] for p in lot) / len(lot)
    cy = sum(p[1] for p in lot) / len(lot)
    inward = (-dn / length, de / length)
    if inward[0] * (cx - ae) + inward[1] * (cy - an) < 0:
        inward = (-inward[0], -inward[1])
    mid = ((ae + be) / 2, (an + bn) / 2)
    offset = setback + depth / 2
    centre = (mid[0] + inward[0] * offset, mid[1] + inward[1] * offset)
    # The archetypes put the facade on max-v (+Y); point +Y back out at the street.
    bearing = (math.degrees(math.atan2(*inward)) + 180) % 360
    return (*footprint_origin(*centre, width, depth, bearing), bearing)


def make_record(recipe: dict, datum: dict) -> dict:
    row = recipe["placement"]
    family, seed = row["family"], row["geometry_seed"]
    spec = families()[family]
    width, depth = dimensions_m(family, spec["band_ft"], seed)
    lot = lot_polygon(row["block_id"], row["lot_column"], row["lot_row"])
    east, north, bearing = seat(lot, width, depth, float(row["front_setback_m"]))
    finish, paint = finish_for(seed)
    return {
        "id": row["structure_id"],
        "name": f"Reconstructed West Water Street {spec['label'].lower()}",
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
                "symbolic_location": "Reconstructed warehouse at Lake and West Water Streets, facing the forks of the river",
                "confidence": "reconstructed",
                "note": (f"The lot is the plat's (Thompson 1830, {row['block_id']} lot "
                         f"{row['plat_lot_number']}); this roof on it is not. Centred on the "
                         f"lot's West Water line and set {row['front_setback_m']} m inside it, "
                         "the rear toward the block's alley. Chosen as the one platted West "
                         "Division lot facing the South Branch at the forks; no source seats "
                         "a building here."),
                "derivation": {"method": "not_derivable",
                               "reason": "No parcel-by-parcel July 1835 West Division roof register survives in the supplied evidence."}},
            "footprint": {
                "polygon": [[0, 0], [width, 0], [width, depth], [0, depth]],
                "confidence": "reconstructed",
                "note": f"Deterministically sampled {width:.3f} by {depth:.3f} metre rectangle inside the {family} typology band; neither dimension is attested for this invented roof."},
            "form": form_for(family, spec, seed, width, depth, paint),
            "change_note": "T-1773 adds the West Division's second freight roof without moving an existing building."}],
        "function": invented(FUNCTIONS[family],
                             f"The {family} type fills the West Division's freight row in the order book. No forwarder, owner or cargo is recovered for it."),
        "reconstruction": {
            "status": "inferred_anonymous", "family": family, "district": "west",
            "inventory_class": "principal_functional",
            "programme_phase": "west_freight_forks_1835", "source_id": SOURCE,
            "sequence": 1, "finish_key": finish,
            "roof_condition": "weathered", "age_state": "recent"},
        "research_note": ("RECONSTRUCTED, NOT A RECOVERED ADDRESS. The order book's West freight "
                          "row sets two roofs and one stood; this is the second. The family, the "
                          "lot, the dimensions, the finish and every form value are inventions "
                          "bounded by the reconstruction specification and recorded in "
                          "docs/LIBERTIES.md. A named West Division warehouse, if one is ever "
                          "read, replaces it."),
        "review_required": False,
    }


def point_segment_distance(e, n, a, b):
    de, dn = b[0] - a[0], b[1] - a[1]
    span = de * de + dn * dn
    t = 0.0 if span == 0 else max(0.0, min(1.0, ((e - a[0]) * de + (n - a[1]) * dn) / span))
    return math.hypot(e - (a[0] + t * de), n - (a[1] + t * dn))


def separation(a, b) -> float:
    if overlap_area(b, a) > .001:
        return 0.0
    return min(point_segment_distance(*p, q, r)
               for x, y in ((a, b), (b, a)) for p in x
               for q, r in zip(y, y[1:] + y[:1]))


def validate(record: dict, recipe: dict, datum: dict) -> str:
    row = recipe["placement"]
    if record["id"] != row["structure_id"] or record["reconstruction"]["family"] != row["family"]:
        raise ValueError("the record's identity or family is not the recipe's")
    phase = record["phases"][0]
    importlib.import_module("archetypes." + record["archetype"] + "_params").from_phase(phase)
    poly = world_polygon(phase, datum)
    lanes = {**corridors(), **omitted_street_corridors()}
    street, depth = intrusion(poly, lanes)
    if street:
        raise ValueError(f"{record['id']} intrudes into {street}: {depth:.3f} m")
    for name, ring in no_build_rings().items():
        if overlap_area(ring, poly) > .001:
            raise ValueError(f"{record['id']} intersects refused ground {name}")
    lot = lot_polygon(row["block_id"], row["lot_column"], row["lot_row"])
    if overlap_area(lot, poly) < .999 * abs(sum(
            a[0] * b[1] - b[0] * a[1] for a, b in zip(poly, poly[1:] + poly[:1]))) / 2:
        raise ValueError(f"{record['id']} does not stand wholly on its lot")
    water = []
    for filename in ("river.geojson", "branches.geojson", "shoreline.geojson"):
        path = EPOCH / filename
        if not path.exists():
            continue
        for feature in load(path)["features"]:
            if feature["properties"].get("kind") == "water" and feature["geometry"]["type"] == "Polygon":
                water.append([(e - datum["origin_utm_e"], n - datum["origin_utm_n"])
                              for e, n in feature["geometry"]["coordinates"][0]])
    if not water:
        raise ValueError("no traced water was read, so the bank setback cannot be held")
    bank = min(separation(poly, ring) for ring in water)
    if bank < BANK_SETBACK_M:
        raise ValueError(f"{record['id']} is only {bank:.2f} m from traced water")
    field = Heightfield.load(EPOCH)
    if field is None:
        raise ValueError("committed terrain is required")
    heights = [field.height(*p) for p in poly]
    if not all(field.covers(*p) for p in poly) or min(heights) < 0:
        raise ValueError(f"{record['id']} lacks dry modelled ground at every corner")
    others = footprints(datum, {record["id"]})
    nearest = min((separation(poly, other), name) for name, other in others)
    if nearest[0] < CLEARANCE_M:
        raise ValueError(f"{record['id']} has only {nearest[0]:.3f} m clearance from {nearest[1]}")
    # GLB contract: the facade is max-v, polygon vertices 2 and 3. It must face the street.
    a, b = front_edge(lot)
    front = min(point_segment_distance(*p, a, b) for p in poly[2:4])
    back = min(point_segment_distance(*p, a, b) for p in poly[:2])
    if not abs(front - float(row["front_setback_m"])) < .01 or back <= front + 3:
        raise ValueError(f"{record['id']} does not face West Water: front {front:.3f}, back {back:.3f} m")
    return (f"{record['id']}: front {front:.2f} m inside the lot line, traced bank {bank:.2f} m, "
            f"nearest {nearest[0]:.2f} m ({nearest[1]}), ground {min(heights):.2f} m, "
            f"relief {max(heights) - min(heights):.2f} m")


def record_from_inputs() -> tuple[dict, str]:
    recipe, datum = load(RECIPE), load(DATA / "datum.json")
    record = make_record(recipe, datum)
    deal_siding([record])
    return record, validate(record, recipe, datum)


def self_test() -> int:
    record, _ = record_from_inputs()
    recipe, datum = load(RECIPE), load(DATA / "datum.json")
    cases = []
    roadway = copy.deepcopy(record)
    roadway["phases"][0]["position"]["utm_e"] += 30
    cases.append(("a roof moved into West Water Street", roadway))
    off = copy.deepcopy(record)
    off["phases"][0]["position"]["utm_n"] -= 12
    cases.append(("a roof straddling the next lot", off))
    backwards = copy.deepcopy(record)
    phase = backwards["phases"][0]
    poly = world_polygon(phase, datum)
    centre = [sum(p[i] for p in poly) / 4 for i in (0, 1)]
    width, depth = phase["footprint"]["polygon"][2]
    bearing = (phase["position"]["rotation_deg"] + 180) % 360
    east, north = footprint_origin(*centre, width, depth, bearing)
    phase["position"].update(utm_e=datum["origin_utm_e"] + east,
                             utm_n=datum["origin_utm_n"] + north, rotation_deg=bearing)
    cases.append(("a warehouse turned to face the alley", backwards))
    wrong = copy.deepcopy(record)
    wrong["reconstruction"]["family"] = "F1"
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
    record, report = record_from_inputs()
    path = DATA / "structures" / (record["id"] + ".json")
    content = json.dumps(record, indent=2, ensure_ascii=False) + "\n"
    print(report)
    if args.check:
        if not path.exists() or path.read_text(encoding="utf-8") != content:
            print(f"FAIL: {path.relative_to(ROOT)} does not re-derive")
            return 1
        print("PASS: the West freight roof re-derives exactly")
        return 0
    path.write_text(content, encoding="utf-8")
    print(f"PASS: wrote {path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
