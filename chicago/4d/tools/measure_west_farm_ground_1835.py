#!/usr/bin/env python3
"""Measure the ground the West Division's owed farm households could stand on. T-1793.

T-1784 asked for the owed West farm households to be "dealt as an off-plat D1 cabin and A2
barn recipe on the extended ground to E -700". Before a roof can be raised for them, four
things have to be known, and none of them was written down anywhere:

  1. WHO they are. `1835_off_plat_seats.json` owes 44 households to the band
     `west/farms_and_country_seats`. This reads each one's rung in the address book.
  2. WHERE a farm could stand. The modelled ground west of the branches is cut here, on a
     10 m lattice, by the Town of Chicago's own corporate boundary (1833, resolved by
     tools/measure_corporation_limits.py) and by the committed survey tracts — and each
     tract is classed as SUBDIVIDED (town ground, laid out in lots or blocks) or not.
  3. HOW BIG a farm is. One forty — 40 acres, the quarter-quarter section — is the unit
     the register and the newspaper both carry on this ground (see FORTY below).
  4. WHAT THE PROGRAMME CARRIES. A farmstead is two roofs, a D1 cabin and an A2 barn, and
     the West's remaining order is read out of the 668-roof programme and the order book.

It raises no roof, seats nobody and authors no coordinate. Every number is a join over
committed records; the only authored judgement is SUBDIVIDED, and each entry there says
which committed record it rests on.

    tools/measure_west_farm_ground_1835.py --build      write the record
    tools/measure_west_farm_ground_1835.py --check      the gate: re-derive and compare
    tools/measure_west_farm_ground_1835.py --self-test  its assertions still fire
"""
from __future__ import annotations

import argparse
import copy
import json
import math
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import measure_corporation_limits as corp  # noqa: E402  (the boundary, resolved, not stored)

RECORD = ROOT / "data/reconstruction/1835_west_farm_ground.json"
SEATS = ROOT / "data/reconstruction/1835_off_plat_seats.json"
ADDRESS_BOOK = ROOT / "data/reconstruction/1835_address_book.json"
PROGRAMME = ROOT / "data/reconstruction/1835_665_roof_programme.json"
ORDER_BOOK = ROOT / "data/reconstruction/1835_reconstruction_order_book.json"
INVENTORY = ROOT / "data/reconstruction/1835_building_inventory.json"
TRACTS = ROOT / "data/reconstruction/1835_survey_tracts.json"
LAND_SALES = ROOT / "data/reconstruction/1835_land_sales_by_tract.json"
GROUND = ROOT / "data/research/land_sales/ground.json"
BOX = ROOT / "data/terrain/west_of_box_reading.json"
EPOCH = ROOT / "data/terrain/epochs/e1834_harbor_cut"
# The river as the 1835 scene's terrain draws it, in three committed pieces that meet: the
# forks, the two branches up to the survey's lines, and the South Branch below Twelfth Street.
WATER_FILES = ("river.geojson", "branches.geojson", "south_branch_below_twelfth.geojson")
DATUM = ROOT / "data/datum.json"
STRUCTURES = ROOT / "data/structures"

BAND = "west/farms_and_country_seats"
CELL_M = 10.0

# 40 acres in square metres (1 acre = 4046.8564224 m², the international acre; the US survey
# acre differs in the sixth figure, which no count here can feel).
FORTY = {
    "acres": 40,
    "m2": round(40 * 4046.8564224, 1),
    "confidence": "inferred",
    "evidence": [
        "data/research/land_sales/ground.json#ls0054 — Edmond Roberts' W2NW of section 9, "
        "entered at the canal sale on 1830-10-05 and read at 40.00 acres: a forty on this very "
        "ground, the only register row under 80 acres that the project can place",
        "data/research/newspapers/extracted/chicago_american_1835_06_27.json#c003 — '40 acres "
        "of excellent land' offered for sale by legal description, in the week before the "
        "scene date",
    ],
    "note": "One forty per farmstead is the reading, not the record. A forty is the smallest "
            "aliquot part either source names on or near this ground, so it is the smallest "
            "holding this file will call a farm; a market garden on a town block is a "
            "household with a garden, which other clauses already deal. Every farm count "
            "below is therefore a CEILING — the most farmsteads the ground could hold if every "
            "farm were the smallest the evidence shows.",
}

# The one authored judgement here. A tract is SUBDIVIDED when a committed record says it was
# laid out in town lots or blocks before the scene date; a farm on it would be a farm on town
# property, which the farms clause's own `ground:outside_plat` preference does not mean.
SUBDIVIDED = {
    "canal_commissioners_1830": "the Original Town itself — the Canal Commissioners' plat of "
                                "1830, whose lots the committed lot ledger draws",
    "wabansia": "surveyed into a subdivision in 1831 (the tract's own legend); its blocks are "
                "T-1785's ground and its one evidenced household is that ticket's",
    "school_section": "sold in 1833 by the block — the register carries {school_blocks} "
                      "school-section block rows on this tract in 1835_land_sales_by_tract.json, "
                      "each block {block_min}–{block_max} acres",
    "kinzies_addition": "Kinzie's Addition, surveyed into lots in 1833 (the tract's own legend)",
    "us_military_reservation": "the reservation — not a farm ground, and not in the West",
    "fractional_section_15": "east of the South Branch — not in the West",
}
RESIDUAL = "canal_section_9_remainder"
# Not a tract: the West ground below the School Section's south line (Twelfth Street), which
# no committed survey tract covers and the box carries south to its floor.
SOUTH_OF_TWELFTH = "below_the_school_section"


# --------------------------------------------------------------------------- geometry

def load(path: Path):
    return json.loads(path.read_text())


def inside(pt, ring) -> bool:
    x, y = pt
    hit = False
    n = len(ring)
    for i in range(n):
        x1, y1 = ring[i]
        x2, y2 = ring[(i + 1) % n]
        if (y1 > y) != (y2 > y):
            if x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
                hit = not hit
    return hit


def crossings(ring, y) -> list[float]:
    out = []
    n = len(ring)
    for i in range(n):
        x1, y1 = ring[i]
        x2, y2 = ring[(i + 1) % n]
        if (y1 > y) != (y2 > y):
            out.append(x1 + (y - y1) * (x2 - x1) / (y2 - y1))
    return out


def branch_rings() -> list[tuple[str, list]]:
    datum = load(DATUM)
    e0, n0 = datum["origin_utm_e"], datum["origin_utm_n"]
    out = []
    for name in WATER_FILES:
        for ft in load(EPOCH / name)["features"]:
            g = ft["geometry"]
            if g["type"] != "Polygon":
                continue
            ring = [(e - e0, n - n0) for e, n in g["coordinates"][0]]
            out.append((ft["properties"].get("name") or name, ring))
    return out


# --------------------------------------------------------------------------- the reading

def derive() -> dict:
    seats = load(SEATS)
    book = {r["id"]: r for r in load(ADDRESS_BOOK)["rows"]}
    owed = [o for o in seats["owed"] if o.get("band") == BAND]
    # T-1794: the farmstead rule seats farm households under a standing cabin-and-barn pair
    # ahead of the labourers, so the band is now the seated AND the owed.
    farmed = [x for x in seats["seats"] if x.get("band") == BAND]
    band_size = len(owed) + len(farmed)
    rungs = Counter(book[o["id"]].get("rung", "absent") for o in owed if o["id"] in book)
    missing = [o["id"] for o in owed if o["id"] not in book]
    handed = Counter(o.get("handed_to") for o in owed)
    why = Counter(o.get("why", "") for o in owed)

    box = load(BOX)["box_local_enu_m"]
    e_min, e_max = float(box["e"][0]), float(box["e"][1])
    n_min, n_max = float(box["n"][0]), float(box["n"][1])
    limits, _reach = corp.limits_ring()
    water = branch_rings()

    tracts = [t for t in load(TRACTS)["tracts"] if t.get("placed") and t.get("polygon_local_enu_m")]
    ordered = [t for t in tracts if t["id"] != RESIDUAL] + [t for t in tracts if t["id"] == RESIDUAL]
    legends = {t["id"]: t.get("legend_text") for t in tracts}

    cell_m2 = CELL_M * CELL_M
    area = Counter()          # (tract, inside_limits) -> cells
    west_cells = 0
    beyond_trace_cells = 0
    eastmost_west_e = -math.inf
    farm_cells = set()
    rows = int((n_max - n_min) // CELL_M)
    cols = int((e_max - e_min) // CELL_M)
    school = next(t for t in tracts if t["id"] == "school_section")
    school_south_n = min(p[1] for p in school["polygon_local_enu_m"])
    for j in range(rows):
        y = n_min + (j + 0.5) * CELL_M
        xs = [x for _, ring in water for x in crossings(ring, y)]
        if not xs:
            beyond_trace_cells += cols
            continue
        west_of = min(xs)
        for i in range(cols):
            x = e_min + (i + 0.5) * CELL_M
            if x >= west_of:
                break
            west_cells += 1
            eastmost_west_e = max(eastmost_west_e, x)
            tract = next((t["id"] for t in ordered if inside((x, y), t["polygon_local_enu_m"])), None)
            if tract is None and y < school_south_n:
                tract = SOUTH_OF_TWELFTH
            within = inside((x, y), limits)
            area[(tract, within)] += 1
            if not within and tract not in SUBDIVIDED:
                farm_cells.add((i, j))

    land = load(LAND_SALES)
    blocks = [r["parcel_acres"] for r in land["sorted"]
              if r.get("ground_kind") == "school_section_block" and r.get("tract") == "school_section"]
    subdivided_why = {
        k: v.format(school_blocks=len(blocks), block_min=min(blocks) if blocks else None,
                    block_max=max(blocks) if blocks else None)
        for k, v in SUBDIVIDED.items()
    }

    by_tract = {}
    for tid in sorted({k[0] or "on_no_tract" for k in area}):
        key = None if tid == "on_no_tract" else tid
        inside_m2 = area[(key, True)] * cell_m2
        outside_m2 = area[(key, False)] * cell_m2
        by_tract[tid] = {
            "legend": legends.get(key) if key else None,
            "inside_the_limits_m2": inside_m2,
            "outside_the_limits_m2": outside_m2,
            "outside_the_limits_forties": round(outside_m2 / FORTY["m2"], 2),
            "subdivided": key in SUBDIVIDED,
            "why": subdivided_why.get(key) if key in SUBDIVIDED else (
                "the residual of section 9 — what the other tracts leave over; no committed "
                "record lays it out in lots" if key == RESIDUAL else
                "west of the South Branch and south of the School Section's south line — no "
                "committed survey tract covers it and no lot is drawn on it" if key == SOUTH_OF_TWELFTH else
                "no committed survey tract covers this ground"),
        }

    farm_m2 = len(farm_cells) * cell_m2
    farm_forties = farm_m2 / FORTY["m2"]

    def cell_of(e, n):
        return (int((e - e_min) // CELL_M), int((n - n_min) // CELL_M))

    datum = load(DATUM)
    standing = []
    for path in sorted(STRUCTURES.glob("*.json")):
        rec = load(path)
        for ph in rec.get("phases", []):
            pos = ph.get("position") or {}
            if pos.get("utm_e") is None or pos.get("utm_n") is None:
                continue
            e = pos["utm_e"] - datum["origin_utm_e"]
            n = pos["utm_n"] - datum["origin_utm_n"]
            if cell_of(e, n) in farm_cells:
                fam = (rec.get("reconstruction") or {}).get("family")
                standing.append({"id": rec["id"], "family": fam})
            break
    standing_fams = Counter(s["family"] or "named" for s in standing)

    entries = []
    for t in load(GROUND)["tracts"]:
        g = t.get("ground") or {}
        ring = g.get("corners_local_enu") or g.get("ring_local_enu")
        acres = float(t.get("acres_as_read") or 0)
        if not ring or acres < FORTY["acres"] or t.get("void"):
            continue
        cells = [c for c in farm_cells
                 if inside((e_min + (c[0] + 0.5) * CELL_M, n_min + (c[1] + 0.5) * CELL_M), ring)]
        west_outside = 0
        for j in range(rows):
            y = n_min + (j + 0.5) * CELL_M
            xs = [x for _, r in water for x in crossings(r, y)]
            if not xs:
                continue
            for i in range(cols):
                x = e_min + (i + 0.5) * CELL_M
                if x >= min(xs):
                    break
                if inside((x, y), ring) and not inside((x, y), limits) \
                        and not any(inside((x, y), r) for _, r in water):
                    west_outside += 1
        if not west_outside:
            continue
        entries.append({
            "record_id": t["record_id"], "purchaser": t["purchaser_normalized"],
            "part": f'{t["part"]} of section {t["section"]}', "acres_as_read": acres,
            "date_purchased": t["date_purchased"], "type_of_sale": t["type_of_sale"],
            "west_ground_outside_the_limits_m2": west_outside * cell_m2,
            "of_it_on_unsubdivided_ground_m2": len(cells) * cell_m2,
        })

    prog = load(PROGRAMME)["remaining"]
    west_family = prog["by_district_family"]["west"]
    west_group = prog["by_district_group"]["west"]
    buckets = {b["key"]: b for bf in load(ORDER_BOOK)["bucket_families"] for b in bf.get("buckets", [])}
    od = buckets["structures/ordinary_dwellings/west"]
    bs = buckets["structures/barns_stables/west"]
    target = load(INVENTORY)["districts"]["west"]["target"]

    ground_ceiling = math.floor(farm_forties)
    pairs = min(standing_fams.get("D1", 0), standing_fams.get("A2", 0))
    programme_ceiling = min(west_family.get("D1", 0), west_family.get("A2", 0))

    doc = {
        "$schema_note": "DERIVED — regenerate with tools/measure_west_farm_ground_1835.py --build; "
                        "tools/check.sh re-derives it (--check). Do not hand-edit.",
        "id": "chicago_july_1835_west_farm_ground",
        "ticket": "T-1793",
        "parent_ticket": "T-1784",
        "successor": "T-1794",
        "target_date": "1835-07-01",
        "generated_by": "tools/measure_west_farm_ground_1835.py --build",
        "not_a_reading": "no page of any source is read here. Every figure is a join over committed "
                         "records: the seats owe the households, the address book grades them, the "
                         "corporation ordinance (resolved) and the survey tracts cut the ground, the "
                         "register places the forties, the programme and the order book hold the roofs.",
        "raises_no_roof": "nothing here builds, seats or moves anything. It is the measurement T-1794 "
                          "deals on.",
        "inputs": [str(p.relative_to(ROOT)) for p in
                   (SEATS, ADDRESS_BOOK, TRACTS, LAND_SALES, GROUND, BOX, DATUM,
                    PROGRAMME, ORDER_BOOK, INVENTORY)] +
                  [str((EPOCH / f).relative_to(ROOT)) for f in WATER_FILES] +
                  ["data/reconstruction/1835_corporation_limits.json (via tools/measure_corporation_limits.py)",
                   "data/structures/*.json (positions)"],
        "the_households": {
            "band": BAND,
            "owed": len(owed),
            "seated_in_farmsteads": [
                {"id": x["id"], "cabin": x["structure_id"], "barn": x.get("farmstead_barn")}
                for x in farmed],
            "by_rung": dict(sorted(rungs.items())),
            "missing_from_the_address_book": missing,
            "placed_by_a_source": sum(n for r, n in rungs.items() if r != "policy_only"),
            "handed_to": dict(handed),
            "why_owed": dict(why),
            "statement": "every one of them is `policy_only`: a name from the post office's letter "
                         "lists with no address, its division dealt from the order book's household "
                         "target and its class from the town model's employment distribution, whose "
                         "`Agriculture` column is the farms clause. No source puts any of them on any "
                         "ground — the post office served the whole country round, and a farmer who "
                         "collected mail at Chicago need not have farmed inside the modelled box."
                         if rungs and set(rungs) == {"policy_only"} else
                         "not every owed household is `policy_only`; see by_rung",
        },
        "the_grid": {
            "cell_m": CELL_M,
            "box_local_enu_m": {"e": [e_min, e_max], "n": [n_min, n_max]},
            "west_of_the_branches": "a cell is West when it lies west of the westmost crossing of "
                                    "the committed river water polygons on its own row (" +
                                    ", ".join(WATER_FILES) + ")",
            "west_cells": west_cells,
            "west_m2": west_cells * cell_m2,
            "rows_beyond_the_traced_branches_m2": beyond_trace_cells * cell_m2,
            "rows_beyond_the_traced_branches": "north of the North Branch's trace no water is "
                                               "committed to divide the ground by, so those rows "
                                               "are not read as West at all",
            "eastmost_west_cell_e_m": eastmost_west_e,
        },
        "the_ground": {
            "corporation_limits": "the Trustees' bounds of 7 November 1833 "
                                  "(chicago_democrat_1833_11_26#c024), resolved by "
                                  "tools/measure_corporation_limits.py. On the West the line is "
                                  "Jefferson Street, so the ground outside it is a strip between "
                                  "Jefferson and the box's west wall.",
            "by_tract": by_tract,
            "subdivided_tracts": sorted(SUBDIVIDED),
        },
        "the_forty": FORTY,
        "the_farm_ground": {
            "what_it_is": "West, outside the corporation limits, and on no subdivided tract",
            "m2": farm_m2,
            "forties": round(farm_forties, 2),
            "standing_on_it": len(standing),
            "standing_by_family": dict(sorted(standing_fams.items())),
            "standing_ids": sorted(s["id"] for s in standing),
        },
        "documented_farm_size_entries": {
            "rule": "register rows of 40 acres or more whose placed ground reaches West ground "
                    "outside the corporation limits",
            "rows": entries,
            "count": len(entries),
        },
        "the_programme": {
            "west_target": target,
            "west_remaining": load(PROGRAMME)["remaining"]["by_district"]["west"],
            "remaining_by_family": {"D1": west_family.get("D1", 0), "A2": west_family.get("A2", 0)},
            "ordinary_dwellings": {"to_build": od["to_build"], "owning_ticket": od["owning_ticket"]},
            "barns_stables": {"to_build": bs["to_build"], "owning_ticket": bs["owning_ticket"]},
            "roofs_a_farmstead_per_owed_household_needs": 2 * len(owed),
            "farmsteads_the_ground_admits_beyond_those_standing": max(0, ground_ceiling - pairs),
            "remaining_by_group": west_group,
        },
        "the_ceiling": {
            "farmsteads_the_ground_holds_at_one_per_forty": ground_ceiling,
            "farmsteads_the_programme_carries_as_it_stands": programme_ceiling,
            "owed_households_left_beyond_the_ground_at_best": max(0, band_size - ground_ceiling),
            "cabin_and_barn_pairs_already_standing_on_it": pairs,
            "farm_households_seated_in_them": len(farmed),
            "pairs_note": "a D1 cabin and an A2 barn that already stand on the farm ground ARE a "
                          "farmstead's two roofs, and seating a farm household under one draws on "
                          "no programme headroom at all. Since T-1794 the off-plat deal's "
                          "farmstead rule (tools/seat_off_plat_ground_1835.py) gives them to farm "
                          "households ahead of the labourers, who ranked above the farms clause "
                          "and had taken every one.",
        },
    }
    doc["verdict"] = (
        f"{band_size} West farm households are dealt and no source places one of them: "
        f"{len(farmed)} are seated in a standing farmstead and {len(owed)} are owed. The West "
        f"ground outside the 1833 corporation limits and off every subdivided tract is "
        f"{farm_m2 / 10000:.1f} ha — {farm_forties:.2f} forties — so at one farm to the smallest "
        f"holding either source names, the modelled ground holds at most {ground_ceiling} "
        f"farmstead(s), and {max(0, band_size - ground_ceiling)} of the {band_size} must be stated "
        f"as farming beyond it. {len(standing)} roof(s) already stand on that ground, "
        f"{standing_fams.get('D1', 0)} of them D1 cabins and {standing_fams.get('A2', 0)} A2 barns — "
        f"{pairs} cabin-and-barn pair(s), {len(farmed)} of them seated by a farm household under "
        f"the farmstead rule. The programme "
        f"carries {programme_ceiling} D1+A2 farmstead(s) as it stands: the West has "
        f"{west_family.get('D1', 0)} D1 and {west_family.get('A2', 0)} A2 left to build, its "
        f"{od['to_build']} remaining dwellings are {od['owning_ticket']}'s and its "
        f"{bs['to_build']} barns {bs['owning_ticket']}'s. {len(entries)} register row(s) of farm "
        f"size reach the West ground outside the limits."
    )
    return doc


# --------------------------------------------------------------------------- gate

def problems(doc: dict) -> list[str]:
    out = []
    h = doc["the_households"]
    if h["owed"] != sum(h["by_rung"].values()) + len(h["missing_from_the_address_book"]):
        out.append("the owed households do not add up to their rungs")
    if h["missing_from_the_address_book"]:
        out.append(f"owed households absent from the address book: {h['missing_from_the_address_book'][:5]}")
    g = doc["the_grid"]
    if g["west_cells"] <= 0:
        out.append("no West ground was read — the branches or the box moved")
    if g["eastmost_west_cell_e_m"] >= g["box_local_enu_m"]["e"][1] - g["cell_m"]:
        out.append("West ground reaches the box's east wall — the water no longer divides it")
    total = sum(t["inside_the_limits_m2"] + t["outside_the_limits_m2"]
                for t in doc["the_ground"]["by_tract"].values())
    if abs(total - g["west_m2"]) > 1e-6:
        out.append(f"the tracts carry {total} m² of West ground but the grid read {g['west_m2']}")
    f = doc["the_farm_ground"]
    admitted = sum(t["outside_the_limits_m2"] for k, t in doc["the_ground"]["by_tract"].items()
                   if not t["subdivided"])
    if abs(admitted - f["m2"]) > 1e-6:
        out.append("the farm ground is not the unsubdivided ground outside the limits")
    c = doc["the_ceiling"]
    if c["farm_households_seated_in_them"] > c["cabin_and_barn_pairs_already_standing_on_it"]:
        out.append("more farm households are seated in farmsteads than cabin-and-barn pairs stand")
    if any(not x["barn"] for x in h["seated_in_farmsteads"]):
        out.append("a farm household is seated in a cabin with no barn named beside it")
    if c["farmsteads_the_ground_holds_at_one_per_forty"] != math.floor(f["forties"] + 1e-9):
        out.append("the ground ceiling is not the whole forties of the farm ground")
    if c["farmsteads_the_programme_carries_as_it_stands"] > min(doc["the_programme"]["remaining_by_family"].values()):
        out.append("the programme ceiling exceeds the West's remaining D1 or A2")
    return out


def check() -> int:
    if not RECORD.exists():
        print(f"FAIL {RECORD.relative_to(ROOT)} is missing — run --build")
        return 1
    committed = load(RECORD)
    derived = derive()
    bad = problems(derived)
    if committed != derived:
        diff = [k for k in derived if committed.get(k) != derived.get(k)]
        bad.append(f"{RECORD.relative_to(ROOT)} is stale in {diff} — run --build")
    for b in bad:
        print(f"FAIL {b}")
    if not bad:
        print("ok   " + derived["verdict"])
    return 1 if bad else 0


def self_test() -> int:
    doc = derive()
    if problems(doc):
        print("FAIL the derived record already fails its own assertions")
        return 1
    breaks = []

    def broken(label, mutate):
        d = copy.deepcopy(doc)
        mutate(d)
        breaks.append((label, problems(d)))

    broken("an owed household dropped from the rungs",
           lambda d: d["the_households"]["by_rung"].update(policy_only=d["the_households"]["by_rung"].get("policy_only", 0) - 1))
    broken("a tract's area inflated",
           lambda d: next(iter(d["the_ground"]["by_tract"].values())).update(inside_the_limits_m2=1e9))
    broken("the farm ground inflated", lambda d: d["the_farm_ground"].update(m2=d["the_farm_ground"]["m2"] + 1e6))
    broken("the ground ceiling raised",
           lambda d: d["the_ceiling"].update(farmsteads_the_ground_holds_at_one_per_forty=99))
    broken("the programme ceiling raised",
           lambda d: d["the_ceiling"].update(farmsteads_the_programme_carries_as_it_stands=99))
    broken("no West ground", lambda d: d["the_grid"].update(west_cells=0))
    silent = [label for label, p in breaks if not p]
    for label, p in breaks:
        print(f"{'ok  ' if p else 'FAIL'} {label}: {p[0] if p else 'NOT CAUGHT'}")
    return 1 if silent else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if a.check:
        return check()
    doc = derive()
    bad = problems(doc)
    for b in bad:
        print(f"FAIL {b}")
    if a.build and not bad:
        RECORD.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n")
        print(f"wrote {RECORD.relative_to(ROOT)}")
    print(json.dumps({k: doc[k] for k in ("the_farm_ground", "the_ceiling")}, indent=1))
    print(doc["verdict"])
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
