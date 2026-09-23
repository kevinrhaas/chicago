#!/usr/bin/env python3
"""Chicago's public buildings are few enough to be listed, so nothing anonymous
may be one — and the target may not count more of them than the list holds.

ROADMAP T-I3 / ticket T-0032. A dwelling nobody named is the ordinary case in this
project: the town held some three thousand people whose houses were never
enumerated roof by roof, so an invented dwelling is a count-unit toward a
documented aggregate. A public building nobody named is a different claim — that
an institution stood on this ground and left no record at all — and the
enumeration behind `docs/RESEARCH/civic_public_buildings_1835.md` is what makes
that claim refusable rather than merely discouraged: on 1 July 1835 the town's
public buildings with a roof are THREE, all three are committed named records, and
every remaining public FUNCTION in the town was carried on inside a private
building.

So the three institutional families are enumerable, and this holds them to it.

## What is asserted

**I1 (worship or meeting) and I3 (civic or public-service) are absolute.** Not a
ratchet: an anonymous roof of either family is a regression, and zero is the
enforceable number. `tools/generate_block_infill.py` has refused all three
families by name since L93, but that refusal only ever covered the block
generator — the North, West and phase-one parcels ran before it existed and
nothing has ever asked the committed records the question.

**I2 (school or community-use) is a ratchet at one.** `recon_1835_north_i2_015`
stands in the North Division from a parcel written before any of this, massed as
a generic frame block. L93 records it rather than quietly removing it, because a
liberty this project took is not deleted to make a gate pass. It may shrink — a
named school record substituting for it is exactly the move T-I3 licenses — and
it may not grow.

**The I3 target equals the civic ledger.** This is the half T-I3 left open and
T-0032 closes. The target was SIX and the town's civic roofs are three, so three
of its six slots counted nothing; the schedule went on dealing those slots to
blocks, and every generator went on refusing them. The ledger below names every
civic or public-service building this project has researched and settles each one
against the committed dataset rather than against a memory of the dossier — a
roof that stood is a reconciliation entry crediting a roof, a building that came
later is either an exclusion dated past the scene or a committed record the
reconciliation credits none, and a function without a building of its own is an
exclusion with no date at all, because what refuses it is its kind.

**And the institutional district row equals the same enumeration.** The inventory
apportioned twelve institutional roofs as south 10 / west 1 / north 1 while the
named records stand south 5 / west 1 / north 3, so the schedule kept finding
institutional headroom in the South Division that no evidence supports and none
in the North where three of these buildings actually are. The row is now the
census, which is what drives every district head to zero: the block schedule can
no longer deal an institutional slot at all, in any division.

## What is only reported

The census: which committed records the physical-roof reconciliation types into
each institutional family.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
STRUCTURES = DATA / "structures"
RECON = DATA / "reconstruction"

INSTITUTIONAL = ("I1", "I2", "I3")
DISTRICTS = ("south", "west", "north", "fort")
SCENE_YEAR = 1835

# The families an anonymous roof may never carry, and the reason, stated where a
# failure will print it. Absolute rather than ratcheted: see the module docstring.
ABSOLUTE = {
    "I1": "worship or meeting buildings. Every congregation in the town in July "
          "1835 is a named record with its own dossier, so an anonymous one is "
          "not a count-unit toward the four — it is a fifth congregation.",
    "I3": "civic or public-service buildings. The town's are enumerable and all "
          "of them are committed named records: the log jail, the council house "
          "and the lighthouse. Every other public function in Chicago on the "
          "scene date — the post office, the United States Land Office, the "
          "county offices — was carried on inside a private building, and the "
          "court-house and the engine house were both built after it.",
}

# The one liberty already taken, named rather than pattern-matched. A ratchet
# that counted by family alone would let a SECOND anonymous school in as long as
# the first went out.
LEGACY_I2 = "recon_1835_north_i2_015"

# THE CIVIC LEDGER — every civic or public-service building this project has
# researched, and what it was on 1835-07-01. The verdict is a claim and NOT the
# evidence: each one is settled below against the committed dataset, so a record
# that quietly changes state breaks this rather than sliding past it. That is the
# fault this ledger exists for — the court-house stood in the scene for four days
# while the reconciliation already credited it no roof, because the two documents
# disagreed and nothing read them together.
#
#   stood            a roof stood on the scene date; verified in the physical-roof
#                    reconciliation as an I3 record crediting at least one roof
#   later            built after 1835-07-01; verified as an exclusion dated past
#                    the scene, or as a committed record the reconciliation
#                    credits no roof for reasons of chronology
#   function_only    the public function existed and had no building of its own;
#                    verified as an exclusion with NO date, because a kind guard
#                    is what refuses it
#   roofless         it stood and it had no roof; verified as a committed record
#                    the reconciliation credits none
#
# Only `stood` counts toward the I3 target. Sources for every line are in
# docs/RESEARCH/civic_public_buildings_1835.md and in each entry's own record.
CIVIC_LEDGER = (
    ("log_jail", "stood",
     "the first Cook County jail, north-west corner of the public square"),
    ("council_house", "stood",
     "the Indian agency council house on the north side of the river"),
    ("chicago_lighthouse_1832", "stood",
     "the second lighthouse tower at the river mouth"),
    ("cook_county_courthouse_1835", "later",
     "erected in the fall of 1835 — the chronology puts it at November and the "
     "Recorder moved into it toward the end of October"),
    ("first_fire_engine_house", "later",
     "contracted 30 December 1835 and still unfinished in February 1836"),
    ("market_house_lake_state", "later", "1837"),
    ("custom_house_chicago", "later",
     "Chicago was not a port of entry until the act of 16 July 1846"),
    ("chicago_town_hall", "function_only",
     "never built — the town was a tenant on the county's square and polled its "
     "own elections in taverns"),
    ("us_land_office_1835", "function_only",
     "open, staffed and transacting business four weeks before the scene date, "
     "in a room on the east side of Lake Street"),
    ("estray_pen", "roofless",
     "the town's first public building, and a small wooden enclosure quite roofless"),
)


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def anonymous_institutional() -> list[dict]:
    """Every generated roof whose programme typed it into an institutional family.

    Both invented layers are asked, because they are two generators and only one
    of them has ever carried the refusal: the anonymous parcels write a
    `reconstruction` block on the record, and the inferred-household layer keeps
    its family in the household programme.
    """
    households = {
        b["id"]: b
        for b in load(RECON / "1835_inferred_household_programme.json")["buildings"]
    }
    found = []
    for path in sorted(STRUCTURES.glob("*.json")):
        record = load(path)
        rid = record["id"]
        block = record.get("reconstruction") or {}
        family, layer = None, None
        if block.get("status") == "inferred_anonymous":
            family, layer = block.get("family"), "anonymous parcel"
        elif rid in households:
            family, layer = households[rid].get("family"), "inferred household"
        if family in INSTITUTIONAL:
            found.append({"id": rid, "family": family, "layer": layer,
                          "district": block.get("district")
                          or households.get(rid, {}).get("district")})
    return found


def named_institutional(reconciliation: dict) -> dict[str, list[str]]:
    """The committed records the roof reconciliation types into each family."""
    census: dict[str, list[str]] = {f: [] for f in INSTITUTIONAL}
    for entry in reconciliation["records"]:
        family = entry.get("likely_family")
        if family in INSTITUTIONAL:
            census[family].append(entry["structure_id"])
    return {f: sorted(ids) for f, ids in census.items()}


def named_by_district(reconciliation: dict) -> dict[str, int]:
    """The same census counted by division, which is what the matrix row must be."""
    counts = {d: 0 for d in DISTRICTS}
    for entry in reconciliation["records"]:
        if entry.get("likely_family") in INSTITUTIONAL and entry.get("roof_count", 0):
            counts[entry["district"]] = counts.get(entry["district"], 0) + 1
    return counts


def _excluded_index(exclusions: dict) -> dict[str, dict]:
    return {row["id"]: row for row in exclusions.get("excluded", [])}


def _recon_index(reconciliation: dict) -> dict[str, dict]:
    return {row["structure_id"]: row for row in reconciliation["records"]}


def civic_ledger(reconciliation: dict, exclusions: dict) -> list[dict]:
    """Settle every line of CIVIC_LEDGER against the committed dataset.

    Returns one row per candidate carrying its claimed verdict, the state the data
    actually supports and, where the two disagree, why.
    """
    recon = _recon_index(reconciliation)
    excluded = _excluded_index(exclusions)
    rows: list[dict] = []
    for rid, verdict, gloss in CIVIC_LEDGER:
        entry, drop = recon.get(rid), excluded.get(rid)
        fault = None
        if verdict == "stood":
            if entry is None:
                fault = "claims to have stood and is not in the roof reconciliation"
            elif entry.get("likely_family") != "I3":
                fault = (f"claims to have stood as a civic roof and the reconciliation "
                         f"types it {entry.get('likely_family')!r}")
            elif not entry.get("roof_count"):
                fault = "claims to have stood and the reconciliation credits it no roof"
        elif verdict == "later":
            year = None
            if drop is not None and drop.get("earliest_scene"):
                year = int(str(drop["earliest_scene"])[:4])
            if year is not None:
                if year <= SCENE_YEAR:
                    fault = (f"is dated out of the scene and its exclusion opens at "
                             f"{drop['earliest_scene']}, which is not later than "
                             f"{SCENE_YEAR}")
            elif entry is None:
                fault = ("is dated out of the scene and is neither an exclusion with a "
                         "date nor a record the reconciliation has ruled on")
            elif entry.get("roof_count") or entry.get("inventory_eligible"):
                fault = ("is dated out of the scene and the reconciliation still "
                         "credits it a roof")
        elif verdict == "function_only":
            if drop is None:
                fault = ("is a public function with no building of its own and is not "
                         "guarded in data/exclusions.json")
            elif drop.get("earliest_scene"):
                fault = (f"is refused for its KIND and its exclusion carries the date "
                         f"{drop['earliest_scene']}, which is a different refusal")
        elif verdict == "roofless":
            if entry is None:
                fault = "is roofless and is not in the roof reconciliation"
            elif entry.get("roof_count"):
                fault = "is roofless and the reconciliation credits it a roof"
        rows.append({"id": rid, "verdict": verdict, "gloss": gloss, "fault": fault})
    return rows


def ledger_findings(rows: list[dict], targets: dict, matrix: dict) -> list[str]:
    """Every way the ledger, the family target and the matrix row can disagree."""
    findings = [f"{r['id']} {r['fault']}" for r in rows if r["fault"]]
    stood = [r["id"] for r in rows if r["verdict"] == "stood"]
    target = targets.get("I3")
    if target != len(stood):
        findings.append(
            f"the I3 target is {target} and the civic ledger settles {len(stood)} "
            f"roof(s) standing on the scene date ({', '.join(stood) or 'none'}). A "
            f"target above the ledger is a slot that counts nothing, and the block "
            f"schedule deals it to a block where every generator then refuses it; a "
            f"target below it is a documented roof with nothing to count against.")
    families = sum(t for f, t in targets.items() if f in INSTITUTIONAL)
    row = matrix.get("institutional_public", {})
    if row.get("total") != families:
        findings.append(
            f"the institutional_public row totals {row.get('total')} and I1+I2+I3 "
            f"sum to {families}")
    return findings


def district_findings(counts: dict[str, int], matrix: dict) -> list[str]:
    """The matrix row must be the census, division by division.

    Not a nicety. A row that promises more institutional roofs in a division than
    the enumeration holds is headroom `tools/reconcile_665.py` will apportion to an
    institutional family, and every generator refuses those — so the slot is dealt,
    refused and lost, and the block is short a roof for arithmetic reasons.
    """
    row = matrix.get("institutional_public", {})
    findings = []
    for district in DISTRICTS:
        want, have = counts.get(district, 0), row.get(district)
        if want != have:
            findings.append(
                f"the institutional_public target for the {district} division is "
                f"{have} and {want} named institutional record(s) stand there. The "
                f"row is the enumeration: a new public building moves it, and moves "
                f"the district and roof totals with it, consciously.")
    return findings


def self_test() -> int:
    """Break each assertion in memory and confirm it is noticed."""
    reconciliation = load(RECON / "1835_existing_roof_reconciliation.json")
    exclusions = load(DATA / "exclusions.json")
    inventory = load(RECON / "1835_building_inventory.json")
    targets = inventory["family_targets"]
    matrix = inventory["district_group_matrix"]

    good = ledger_findings(civic_ledger(reconciliation, exclusions), targets, matrix)
    good += district_findings(named_by_district(reconciliation), matrix)
    if good:
        print("   FAIL  the committed dataset does not pass, so the self-test has no "
              "clean starting point")
        for line in good:
            print(f"          {line}")
        return 1
    print("   ok    the committed dataset passes, so a break below is this test's "
          "own doing")

    ok = True

    def case(label: str, findings: list[str], expect: str) -> None:
        nonlocal ok
        hit = any(expect in f for f in findings)
        print(f"   {'ok  ' if hit else 'FAIL'}  {label}")
        if not hit:
            print(f"          expected a finding containing {expect!r}, got {findings}")
            ok = False

    def copy(doc):
        return json.loads(json.dumps(doc))

    six = copy(targets)
    six["I3"] = 6
    case("the six-roof target this ticket corrected is caught",
         ledger_findings(civic_ledger(reconciliation, exclusions), six, matrix),
         "the I3 target is 6 and the civic ledger settles 3")

    two = copy(targets)
    two["I3"] = 2
    case("a target BELOW the ledger is caught too — it is not a ceiling",
         ledger_findings(civic_ledger(reconciliation, exclusions), two, matrix),
         "the I3 target is 2 and the civic ledger settles 3")

    standing = copy(reconciliation)
    for row in standing["records"]:
        if row["structure_id"] == "cook_county_courthouse_1835":
            row.update(roof_count=1, inventory_eligible=True, likely_family="I3")
    case("the court-house standing again on 1 July is caught",
         ledger_findings(civic_ledger(standing, exclusions), targets, matrix),
         "cook_county_courthouse_1835 is dated out of the scene and the "
         "reconciliation still credits it a roof")

    gone = copy(reconciliation)
    for row in gone["records"]:
        if row["structure_id"] == "log_jail":
            row["roof_count"] = 0
    case("a civic roof quietly losing its roof is caught",
         ledger_findings(civic_ledger(gone, exclusions), targets, matrix),
         "log_jail claims to have stood and the reconciliation credits it no roof")

    roofed = copy(reconciliation)
    for row in roofed["records"]:
        if row["structure_id"] == "estray_pen":
            row["roof_count"] = 1
    case("a roof on the roofless estray pen is caught",
         ledger_findings(civic_ledger(roofed, exclusions), targets, matrix),
         "estray_pen is roofless and the reconciliation credits it a roof")

    ungated = copy(exclusions)
    ungated["excluded"] = [r for r in ungated["excluded"]
                           if r["id"] != "us_land_office_1835"]
    case("dropping the land-office kind guard is caught",
         ledger_findings(civic_ledger(reconciliation, ungated), targets, matrix),
         "us_land_office_1835 is a public function with no building of its own")

    early = copy(exclusions)
    for row in early["excluded"]:
        if row["id"] == "market_house_lake_state":
            row["earliest_scene"] = "1834"
    case("an exclusion re-dated back into the scene is caught",
         ledger_findings(civic_ledger(reconciliation, early), targets, matrix),
         "market_house_lake_state is dated out of the scene and its exclusion opens")

    south_heavy = copy(matrix)
    south_heavy["institutional_public"].update(south=10, north=1, total=12)
    case("the old south 10 / north 1 apportionment is caught",
         district_findings(named_by_district(reconciliation), south_heavy),
         "the institutional_public target for the south division is 10 and 5 named")

    unbalanced = copy(matrix)
    unbalanced["institutional_public"]["total"] = 12
    case("a row total that no longer equals I1+I2+I3 is caught",
         ledger_findings(civic_ledger(reconciliation, exclusions), targets, unbalanced),
         "the institutional_public row totals 12 and I1+I2+I3 sum to 9")

    print("SELF-TEST PASS" if ok else "SELF-TEST FAIL")
    return 0 if ok else 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gate", action="store_true",
                        help="exit 1 when an anonymous roof carries an institutional "
                             "family, or the target does not match the civic ledger")
    parser.add_argument("--quiet", action="store_true",
                        help="print the assertion and the failures, not the census")
    parser.add_argument("--self-test", action="store_true",
                        help="break each assertion in memory and confirm it fires")
    args = parser.parse_args()

    if args.self_test:
        return self_test()

    inventory = load(RECON / "1835_building_inventory.json")
    targets = inventory["family_targets"]
    matrix = inventory["district_group_matrix"]
    reconciliation = load(RECON / "1835_existing_roof_reconciliation.json")
    exclusions = load(DATA / "exclusions.json")

    census = named_institutional(reconciliation)
    found = anonymous_institutional()
    ledger = civic_ledger(reconciliation, exclusions)

    failures: list[str] = []
    for row in sorted(found, key=lambda r: (r["family"], r["id"])):
        family = row["family"]
        if family in ABSOLUTE:
            failures.append(
                f"{row['id']} is an anonymous roof of family {family} in the "
                f"{row['layer']} layer — {ABSOLUTE[family]}")
        elif row["id"] != LEGACY_I2:
            failures.append(
                f"{row['id']} is a SECOND anonymous roof of family I2. The one this "
                f"project carries, {LEGACY_I2}, is a liberty recorded in "
                f"docs/LIBERTIES.md (L93) and not a precedent. A school nobody named "
                f"is a claim that a school stood here and left no record.")
    failures += ledger_findings(ledger, targets, matrix)
    failures += district_findings(named_by_district(reconciliation), matrix)

    stood = [r for r in ledger if r["verdict"] == "stood"]
    if not args.quiet:
        for family in INSTITUTIONAL:
            named = census[family]
            print(f"   {family}  target {targets.get(family, '?'):>2}  "
                  f"{len(named)} named record(s) standing: {', '.join(named) or '—'}")
        print("\n   THE CIVIC LEDGER on 1835-07-01")
        for row in ledger:
            print(f"     {row['verdict']:<13} {row['id']:<28} {row['gloss']}")
        counts = named_by_district(reconciliation)
        print("\n   institutional roofs by division: "
              + ", ".join(f"{d} {counts.get(d, 0)}" for d in DISTRICTS)
              + f" — the matrix row reads "
              + ", ".join(f"{d} {matrix['institutional_public'].get(d)}"
                          for d in DISTRICTS))

    anon_i2 = [r["id"] for r in found if r["family"] == "I2"]
    if failures:
        print("\n   INSTITUTIONAL CLAIM FAILURES")
        for line in failures:
            print(f"     - {line}")
        return 1 if args.gate else 0

    print(f"   no anonymous roof carries I1 or I3, and I2 holds at "
          f"{len(anon_i2)} ({', '.join(anon_i2) or 'none'}). The town's public "
          f"buildings are named records, and the I3 target is the "
          f"{len(stood)} of them that had a roof on the scene date.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
