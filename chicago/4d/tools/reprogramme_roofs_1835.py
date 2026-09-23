#!/usr/bin/env python3
"""THE 668-ROOF PROGRAMME, RE-DERIVED AGAINST THE ORDER BOOK. T-1196.

    tools/reprogramme_roofs_1835.py --build       re-derive, write the record and the report
    tools/reprogramme_roofs_1835.py --check       re-derive and refuse drift
    tools/reprogramme_roofs_1835.py --self-test   the guards, fired on fixtures

WHAT THIS TOOL IS. An ADJUDICATION over committed derived files, exactly as the
order book and the lodging model are. It reads no page of any source, opens no
network, names nobody, ages nobody, and raises no roof. It asks one question of
each of the ten groups in the building inventory's district/group matrix -- does
the population, occupation and lodging model want a different number of roofs
here than the owner's 2026 specification scheduled? -- and records the answer
with the arithmetic that reached it.

WHY THE PROGRAMME NEEDED ASKING. The 668-roof schedule is a production decision
taken before the population layer existed. The order book (T-1166) now says what
the reconstructed town needs, and it carries five `programme_deltas` rows stamped
`owning_ticket: T-1196` precisely so this comparison would be made deliberately
rather than discovered halfway through a district.

WHAT A DELTA IS NOT. Three of those five rows are not disagreements about roofs
at all, and the largest of them is the most misleading:

  * `households_against_dwellings` (delta 308) compares HOUSEHOLDS against
    DWELLINGS. Satisfying it by adding 308 roofs would build a town of one family
    per roof -- which is the exact error the town model was written to refuse
    ("a roof programme that seats one family per roof undercounts the town"). The
    resolution is an OCCUPANCY RATE, and this tool states it: the programme's
    dwelling roofs hold the order book's households at a rate the November census
    itself brackets. Nothing is built.

  * `institutional_and_public` was a UNIT MISMATCH, corrected by T-1439. The town
    model's high end is 19 because it reads "9 institutional or public roofs
    outside the fort and 10 principal roofs inside it" -- and the programme
    schedules those ten under `fort_principal`, not under `institutional_public`.
    9 + 10 = 19. The programme and the model already agreed; only the comparison
    was wrong, and the order book now sums both groups on its programme side.

  * `boarding_houses` (delta 0) is CIRCULAR. `model_town_1835.build_lodging`
    takes the figure straight off `district_group_matrix`, so the model agreeing
    with the programme here is the programme agreeing with itself. A tautology is
    not corroboration and this record says so rather than banking it.

  * `inns_and_taverns` was a delta of 6 and is a delta of 2, BECAUSE THE FOLD RAN
    (T-1471, 2026-09-21). It compares a ROOF COUNT against a NOTICE COUNT, and
    the notice count was counting one house four times: five settings of E.
    Wentworth's standing Flag Creek advertisement had raised four businesses, and
    three settings of the Eagle Tavern's chair-and-harness notice had raised two.
    trade_class_rulings.json now folds them, so the register's 15 scene-date
    tavern records are 11 HOUSES. The identity ruling this tool refused to make
    has been made elsewhere, on the records, with its sources; what is left is
    still owed out and still not acted on -- see `deltas_owed_out`.

THE ONE THING THIS TOOL OWNS AND WRITES. The family-archetype crosswalk's COUNT
fields -- `target_roofs`, `remaining_roofs`, `priority_rank`, `priority_band` and
`roof_totals` -- are derived from the inventory's `family_targets` and the
crosswalk's own `priority_rule`, and its own `count_basis` note says as much. They
had drifted: four families (C2, W4, A2, A5) still carried the pre-T-0283/T-1036
targets, so the crosswalk summed to 662 against the inventory's 668, and nine
families carried a `priority_rank` one place out because T-0032 moved I3 from six
roofs to three without re-ranking. `--build` re-derives them. Everything else in
that file is authored -- archetypes, geometry bands, evidence and assumption notes
-- and is never touched here.

--check NEVER WRITES. A check that repairs the file it is checking (T-0856,
T-1341) reports a pass it manufactured; this one re-derives in memory and fails.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = DATA / "reconstruction" / "1835_roof_programme_rederivation.json"
REPORT = ROOT / "docs" / "RESEARCH" / "1835_roof_programme_rederivation.md"
CROSSWALK = DATA / "reconstruction" / "1835_family_archetype_crosswalk.json"

#: Every group in the inventory's matrix, and the families the crosswalk deals
#: it to. The two files must partition the same 668 roofs; `check_partition`
#: fires if they ever stop doing so.
GROUP_FAMILIES = {
    "ordinary_dwellings": ("D1", "D2", "D3", "D4", "D5", "D6", "D7"),
    "larger_boarding_houses": ("H1", "H2", "H3"),
    "stores_mixed_use": ("C1", "C2", "C3", "C4"),
    "inns_taverns": ("T1", "T2", "T3"),
    "workshops": ("W1", "W2", "W3", "W4", "W5"),
    "warehouses_freight": ("F1", "F2", "F3", "F4"),
    "institutional_public": ("I1", "I2", "I3"),
    "fort_principal": ("M1",),
    "barns_stables": (),
    "small_outbuildings": (),
}

#: The ancillary groups share the A families between them; the matrix splits
#: them by division and the crosswalk by form, so neither is a refinement of the
#: other and the partition is asserted over their SUM.
ANCILLARY_GROUPS = ("barns_stables", "small_outbuildings")
ANCILLARY_FAMILIES = ("A1", "A2", "A3", "A4", "A5")


class Fault(Exception):
    """A refusal. Never a warning: a roof target with a hole in it builds a town."""


# ------------------------------------------------------------------- inputs --

def load(root: Path = ROOT) -> dict:
    paths = {
        "inventory": root / "data" / "reconstruction" / "1835_building_inventory.json",
        "model": root / "data" / "reconstruction" / "1835_town_model.json",
        "book": root / "data" / "reconstruction" / "1835_reconstruction_order_book.json",
        "lodging": root / "data" / "reconstruction" / "1835_lodging_model.json",
        "crosswalk": root / "data" / "reconstruction" / "1835_family_archetype_crosswalk.json",
        "composition": root / "data" / "research" / "census_1840" / "composition_1840.json",
        # THE FOLD LIVES HERE, NOT IN THIS TOOL (T-1471). The identity ruling that
        # turns tavern NOTICES into tavern HOUSES is made in
        # trade_class_rulings.json and taken by tools/trade_census_1835.py; this
        # file reads the folded count so the inns_taverns row can say how much of
        # its old delta was one house advertising twice.
        "trade_census": root / "data" / "research" / "books" / "trade_census_1835_crosswalk.json",
    }
    out = {}
    for key, path in paths.items():
        if not path.exists():
            raise Fault(f"the re-derivation's input {path.name} is missing — "
                        "the programme cannot be re-cut without it")
        out[key] = json.loads(path.read_text(encoding="utf-8"))
    return out


def figure(model: dict, section_key: str, name: str) -> dict:
    for section in model["sections"]:
        if section["key"] != section_key:
            continue
        for fig in section["figures"]:
            if fig["figure"] == name:
                return fig
    raise Fault(f"the town model carries no figure {name!r} in section {section_key!r}")


# ------------------------------------------------------------- the crosswalk --

def band_for(remaining: int, bands: dict) -> str:
    """The crosswalk's own priority band for a remaining count.

    The bands are authored as prose ranges ("50 or more", "25-49"); they are read
    here rather than restated, so a band the owner re-cuts moves this tool with it.
    """
    order = ["P0", "P1", "P2", "P3", "P4"]
    edges = {}
    for key in order:
        text = str(bands.get(key, ""))
        digits = [int(tok) for tok in text.replace("-", " ").split() if tok.isdigit()]
        if not digits:
            raise Fault(f"the crosswalk's priority band {key} states no number: {text!r}")
        edges[key] = min(digits)
    for key in order:
        if remaining >= edges[key]:
            return key
    return order[-1]


def crosswalk_counts(inventory: dict, crosswalk: dict) -> dict:
    """The crosswalk's count fields, re-derived from the inventory.

    `target_roofs` is the inventory's live family target; `remaining_roofs` is
    that less the phase-1 roofs already instantiated (authored, and left alone);
    rank and band follow the file's own `priority_rule`.
    """
    targets = inventory["family_targets"]
    rule = crosswalk["priority_rule"]
    if rule.get("order") != "descending remaining_roofs, then family id":
        raise Fault("the crosswalk's priority_rule no longer orders by descending "
                    f"remaining_roofs then family id: {rule.get('order')!r} — "
                    "re-read it before this tool re-ranks anything")

    rows = {}
    for fam in crosswalk["families"]:
        fid = fam["id"]
        if fid not in targets:
            raise Fault(f"the crosswalk deals family {fid}, which the inventory's "
                        "family_targets does not schedule")
        phase1 = int(fam["phase1_instantiated"])
        target = int(targets[fid])
        if phase1 > target:
            raise Fault(f"{fid} has {phase1} phase-1 roofs standing against a target of "
                        f"{target} — the target cannot be met by unbuilding")
        rows[fid] = {"target_roofs": target, "phase1_instantiated": phase1,
                     "remaining_roofs": target - phase1}

    missing = sorted(set(targets) - set(rows))
    if missing:
        raise Fault(f"the inventory schedules {', '.join(missing)}, which the crosswalk "
                    "deals to no archetype")

    ordered = sorted(rows, key=lambda fid: (-rows[fid]["remaining_roofs"], fid))
    for rank, fid in enumerate(ordered, start=1):
        rows[fid]["priority_rank"] = rank
        rows[fid]["priority_band"] = band_for(rows[fid]["remaining_roofs"],
                                              rule.get("bands", {}))

    return {
        "families": rows,
        "roof_totals": {
            "target": sum(r["target_roofs"] for r in rows.values()),
            "phase1_instantiated": sum(r["phase1_instantiated"] for r in rows.values()),
            "remaining": sum(r["remaining_roofs"] for r in rows.values()),
        },
    }


def apply_counts(crosswalk: dict, counts: dict) -> dict:
    """A copy of the crosswalk with its count fields re-derived and nothing else moved."""
    out = json.loads(json.dumps(crosswalk))
    out["roof_totals"] = dict(counts["roof_totals"])
    for fam in out["families"]:
        for key, value in counts["families"][fam["id"]].items():
            fam[key] = value
    return out


def rewrite_counts_in_place(text: str, counts: dict) -> str:
    """The same re-derivation, written as a surgical edit of the file's own text.

    The crosswalk is hand-formatted — each family on one line, several keys to a
    line — and re-serialising it would churn 750 lines to move thirteen numbers,
    burying the change and colliding with every other branch that touches the
    file. So each count field is rewritten where it stands and the file's shape
    is left exactly as its author set it.
    """
    lines = text.split("\n")
    wanted = {f'"id": "{fid}"': (fid, row) for fid, row in counts["families"].items()}
    seen = set()
    for i, line in enumerate(lines):
        if line.lstrip().startswith('"roof_totals"'):
            indent = line[:len(line) - len(line.lstrip())]
            body = ", ".join(f'"{k}": {v}' for k, v in counts["roof_totals"].items())
            lines[i] = f"{indent}\"roof_totals\": {{{body}}},"
            seen.add("roof_totals")
            continue
        for needle, (fid, row) in wanted.items():
            if needle not in line:
                continue
            for key, value in row.items():
                rendered = json.dumps(value)
                before = line
                line = re.sub(rf'("{key}"\s*:\s*)(?:"[^"]*"|-?\d+)',
                              lambda m: m.group(1) + rendered, line, count=1)
                if line == before and f'"{key}"' not in before:
                    raise Fault(f"the crosswalk's {fid} row carries no {key} field to "
                                "re-derive — its shape has changed")
            lines[i] = line
            seen.add(fid)
            break
    missing = sorted((set(counts["families"]) | {"roof_totals"}) - seen)
    if missing:
        raise Fault(f"the crosswalk text holds no single-line row for {', '.join(missing)} — "
                    "re-derive it by hand or teach this tool the new layout")
    return "\n".join(lines)


def crosswalk_drift(crosswalk: dict, counts: dict) -> list[dict]:
    """Every count field on disk that the inventory no longer agrees with."""
    out = []
    for fam in crosswalk["families"]:
        want = counts["families"][fam["id"]]
        moved = {k: [fam.get(k), v] for k, v in want.items() if fam.get(k) != v}
        if moved:
            out.append({"family": fam["id"], "label": fam["label"], "fields": moved})
    totals = {k: [crosswalk["roof_totals"].get(k), v]
              for k, v in counts["roof_totals"].items()
              if crosswalk["roof_totals"].get(k) != v}
    if totals:
        out.append({"family": "roof_totals", "label": "the crosswalk's own totals",
                    "fields": totals})
    return out


# ----------------------------------------------------------------- the groups --

def group_rows(data: dict) -> list[dict]:
    """One row per matrix group: what the spec scheduled, what a model says, what stands."""
    inventory, model, book = data["inventory"], data["model"], data["book"]
    matrix = inventory["district_group_matrix"]
    spec = {g: int(matrix[g]["total"]) for g in GROUP_FAMILIES}

    dwellings = figure(model, "households_and_families", "dwellings_the_programme_schedules")
    boarding = figure(model, "lodging_and_institutions", "larger_boarding_houses")
    inns = figure(model, "lodging_and_institutions", "inns_and_taverns")
    institutional = figure(model, "lodging_and_institutions", "institutional_and_public_roofs")
    establishments = figure(model, "occupations", "establishments_in_the_compared_classes")

    households = int(book["totals"]["households_target"])
    standing_inns = sum(1 for p in data["lodging"]["places"] if p["class"] == "inn_tavern")
    tavern_row = next(c for c in data["trade_census"]["classes"] if c["class"] == "tavern")
    tavern_folded = len(tavern_row["folded_business_ids"])
    tavern_houses = int(tavern_row["town_records_at_scene_date"])
    tavern_notices = tavern_houses + tavern_folded
    trade_roofs = spec["stores_mixed_use"] + spec["workshops"] + spec["warehouses_freight"]

    def row(group, model_says, model_figure, unit, adopted, why):
        return {
            "group": group,
            "spec": spec[group],
            "model": model_says,
            "model_figure": model_figure,
            "compared_in": unit,
            "adopted": adopted,
            "delta": adopted - spec[group],
            "moved": adopted != spec[group],
            "why": why,
        }

    rows = [
        row("ordinary_dwellings", int(dwellings["low"]),
            "households_and_families.dwellings_the_programme_schedules",
            "roofs against roofs",
            spec["ordinary_dwellings"],
            f"The model's own low end IS this schedule. The order book's competing figure is "
            f"{households:,} HOUSEHOLDS, which is a different unit: satisfying it with roofs "
            f"would seat one family per roof, the error the town model exists to refuse. It is "
            "met by occupancy instead — see the dwellings reconciliation, where the rate the "
            "order book needs falls inside the band the November census brackets."),
        row("larger_boarding_houses", int(boarding["low"]),
            "lodging_and_institutions.larger_boarding_houses",
            "roofs against roofs",
            spec["larger_boarding_houses"],
            "The model reads this figure off district_group_matrix, so its agreement with the "
            "programme is the programme agreeing with itself. Recorded as circular rather than "
            "banked as corroboration; the group stands because nothing independent moves it."),
        row("inns_taverns", int(inns["high"]),
            "lodging_and_institutions.inns_and_taverns",
            "roofs against printed notices",
            spec["inns_taverns"],
            f"THE FOLD RAN AND THE GROUP MEETS THE TOWN EXACTLY (T-1471). The model's "
            f"{int(inns['high'])} is the business register's count of HOUSES at the scene "
            f"date: {tavern_notices} records folded to {tavern_houses} by {tavern_folded} "
            "one-house rulings in trade_class_rulings.json, which is where an identity ruling "
            "belongs and this tool still makes none of its own. One of those "
            f"{tavern_houses} is E. Wentworth's house on Flag Creek, eighteen miles south of "
            "Chicago on the Ottawa road — all five of its printings say so — and a house "
            f"outside the plat is no roof inside it. That leaves {tavern_houses - 1} public "
            f"houses in the town against the {spec['inns_taverns']} this programme schedules: "
            "the two figures MEET, and the group is left exactly as it is. The layer stands at "
            f"{standing_inns} of those {spec['inns_taverns']}, which is the schedule's own "
            "remaining build and not a disagreement about how many there should be."),
        row("institutional_public", int(institutional["low"]),
            "lodging_and_institutions.institutional_and_public_roofs",
            "roofs outside the fort against roofs outside the fort",
            spec["institutional_public"],
            f"The model's low end is the {int(institutional['low'])} roofs OUTSIDE the fort and "
            f"its high end adds the {spec['fort_principal']} principal roofs INSIDE it. The "
            f"programme schedules both — {spec['institutional_public']} institutional_public "
            f"plus {spec['fort_principal']} fort_principal — so the two agree at "
            f"{spec['institutional_public'] + spec['fort_principal']}. The order book's "
            "delta of ten is that high end read against one of the two groups."),
        row("fort_principal", int(institutional["high"]) - int(institutional["low"]),
            "lodging_and_institutions.institutional_and_public_roofs",
            "roofs against roofs",
            spec["fort_principal"],
            "The fort component of the model's institutional high end, and the same number. "
            "The compound is read from its dossiers, not apportioned."),
    ]

    for group in ("stores_mixed_use", "workshops", "warehouses_freight"):
        rows.append(row(
            group, None, "occupations.establishments_in_the_compared_classes",
            "roofs against establishments",
            spec[group],
            f"No model figure schedules this group on its own. The nearest comparandum is the "
            f"{int(establishments['low'])}–{int(establishments['high'])} establishments the "
            f"occupation model counts in the compared classes, against the {trade_roofs} "
            "commercial, workshop and freight roofs the programme schedules together — more "
            "trades than roofs, which is the store-over-office and shop-house town these "
            "families already build. Nothing moves a single group off that."))

    for group in ANCILLARY_GROUPS:
        rows.append(row(
            group, None, None, "not modelled",
            spec[group],
            "Ancillary. The town model carries no figure for yards and outbuildings and the "
            "order book orders none; the ratio to principal roofs is T-1212's to deal. The "
            "spec stands untouched."))

    rows.sort(key=lambda r: r["group"])
    return rows


def dwellings_reconciliation(data: dict) -> dict:
    """The 308-household delta, resolved as an occupancy rate rather than as roofs."""
    inventory, model, book = data["inventory"], data["model"], data["book"]
    matrix = inventory["district_group_matrix"]
    town = data["composition"]["beside_the_town"]["1835_town"]

    ordinary = int(matrix["ordinary_dwellings"]["total"])
    boarding = int(matrix["larger_boarding_houses"]["total"])
    dwelling_roofs = ordinary + boarding
    households = int(book["totals"]["households_target"])
    persons = int(book["totals"]["persons_target"])

    size = figure(model, "households_and_families", "household_size")
    low, high = float(size["low"]), float(size["high"])
    per_dwelling = float(town["people_per_dwelling"])
    # The census's people-per-dwelling divided by a household size is households
    # per dwelling; the LARGER household size gives the SMALLER rate.
    band = [round(per_dwelling / high, 3), round(per_dwelling / low, 3)]
    adopted = round(households / dwelling_roofs, 3)

    census_dwellings = int(town["dwellings"])
    return {
        "question": "The order book orders more households than the programme schedules "
                    "dwellings. How many households to a roof?",
        "ordinary_dwellings": ordinary,
        "larger_houses_and_boarding_houses": boarding,
        "dwelling_roofs_on_the_scene_date": dwelling_roofs,
        "households_the_order_book_orders": households,
        "households_per_dwelling_adopted": adopted,
        "households_per_dwelling_the_census_brackets": band,
        "inside_the_bracket": band[0] <= adopted <= band[1],
        "how_the_bracket_is_got": f"{per_dwelling} people per dwelling in the town census of "
                                  f"November 1835, over the 1840 city's household size of "
                                  f"{low}–{high} (median to mean).",
        "people_per_dwelling_adopted": round(persons / dwelling_roofs, 3),
        "census_dwellings_november_1835": census_dwellings,
        "roofs_short_of_the_census": census_dwellings - dwelling_roofs,
        "why_short_is_right": f"The census counted {census_dwellings} dwellings in November "
                              f"1835, four months after the scene, in the fastest-growing "
                              f"months the town had. A July programme of {dwelling_roofs} "
                              f"dwelling roofs stands "
                              f"{(census_dwellings - dwelling_roofs) / census_dwellings:.1%} "
                              "below it, which is growth across that gap and not a hole in the "
                              "schedule. The same date caution governs every class the "
                              "trade-census crosswalk compares.",
        "source": town["source"],
    }


def owed_out(rows: list[dict], data: dict) -> list[dict]:
    """Deltas this re-derivation does not act on, and who owns each."""
    inns = next(r for r in rows if r["group"] == "inns_taverns")
    tavern_row = next(c for c in data["trade_census"]["classes"] if c["class"] == "tavern")
    folded = len(tavern_row["folded_business_ids"])
    houses = int(tavern_row["town_records_at_scene_date"])
    return [
        {"id": "inns_and_taverns", "owed_to": None, "settled_by": "T-1471",
         "statement": "THE IDENTITY QUESTION IS ANSWERED AND THE GROUP IS LEFT ALONE. It was "
                      f"asked as: the register holds {houses + folded} tavern records at the "
                      "scene date and folds none of them — are they that many HOUSES? They are "
                      f"not. {folded} of them are re-settings of two standing advertisements, "
                      "ruled one house apiece in trade_class_rulings.json with the printed copy "
                      "beside each ruling. Five settings of E. Wentworth's Flag Creek notice — "
                      "the same four sentences every time, signing themselves 'Dec. 17, 1833' "
                      "a year after that date — had raised four businesses; three settings of "
                      "the Eagle Tavern's chair-and-harness notice — signing themselves 'June "
                      "11, 1834' and differing only in the keeper's middle initial — had raised "
                      f"two. So {houses + folded} records are {houses} houses, and the delta "
                      f"against {inns['spec']} scheduled roofs falls from "
                      f"{houses + folded - inns['spec']} to {houses - inns['spec']}. "
                      "AND THE LAST ONE IS NOT IN THE TOWN. E. Wentworth's house stood "
                      "eighteen miles south of Chicago on the Ottawa road, which all five of "
                      "its printings state and which no roof inside the plat can be. The "
                      f"town's own figure is therefore {houses - 1} public houses against the "
                      f"{inns['spec']} this programme schedules: they MEET, and there is "
                      "nothing left to re-cut. "
                      "THE REMAINDER RECONCILES TOO, which is the check on that. Six of the "
                      "town's ten records already sit on a standing public house (Couch on the "
                      "Tremont, Davis on the Steamboat, Murphy on the Exchange, Stow on the "
                      "Western, Walters on Wolf Point, Ingersoll on the Green Tree). Three "
                      "standing houses carry no register record at all — the Sauganash, the "
                      "Mansion House and the New York House — and the schedule has one roof "
                      f"still to raise ({inns['spec']} scheduled against the layer's nine "
                      "standing). Three unlinked houses plus one unbuilt roof is four, and "
                      "four is exactly the number of town records with no house yet: Beaubien, "
                      "Sweet, the Eagle Tavern and the Traveller's Home. Linking a keeper to "
                      "the house he kept is a person-to-house ruling and is not made here. "
                      "WHAT IS STILL OPEN, and named rather than ruled: the register's 'Eagle "
                      "Hotel' (Cable and Shrigley) and 'Eagle Tavern' (Carli) trade in the same "
                      "months under the same bird. That pair sits in trade_class_rulings.json's "
                      "`register_cautions` and cannot move this count either way — the Eagle "
                      "Hotel is already excluded from the scene date as contradicted before "
                      "it."},
        {"id": "institutional_and_public", "owed_to": "T-1196",
         "statement": "The false delta of ten is GONE (T-1439, 2026-09-21): "
                      "build_order_book_1835.programme_deltas now sums institutional_public "
                      "and fort_principal on its programme side, which is where the model's "
                      "high end already had them, and the two files read 19 against 19. What "
                      "is still owed is a COUNT: both ends of the model's figure are read off "
                      "district_group_matrix, so the corrected zero is a restatement and the "
                      "book prints it as one. Nothing outside the roof programme has said how "
                      "many institutional and public roofs the town had."},
        {"id": "boarding_houses", "owed_to": "T-1196",
         "statement": "model_town_1835.build_lodging takes larger_boarding_houses straight off "
                      "district_group_matrix, so that figure can never disagree with the "
                      "programme and the order book's delta of zero is a tautology. A figure "
                      "that cannot fail is not a check on 42 roofs. The book stopped printing "
                      "it as a pass with T-1439 and marks the row NOT A CHECK; an independent "
                      "count of the town's boarding houses is still owed to the re-cut."},
    ]


def build(data: dict) -> dict:
    inventory = data["inventory"]
    rows = group_rows(data)
    counts = crosswalk_counts(inventory, data["crosswalk"])
    spec_total = int(inventory["targets"]["roof_total"])
    adopted_total = sum(r["adopted"] for r in rows)
    lo, hi = [int(v) for v in inventory["targets"]["defensible_range"]]
    return {
        "$schema_note": "DERIVED — regenerate with tools/reprogramme_roofs_1835.py --build; "
                        "tools/check.sh re-derives it with --check. Do not hand-edit. The "
                        "crosswalk's count fields are re-derived by the same --build.",
        "id": "chicago_july_1835_roof_programme_rederivation",
        "ticket": "T-1196",
        "target_date": "1835-07-01",
        "generated_by": "tools/reprogramme_roofs_1835.py --build",
        "not_a_reading": "an adjudication over committed derived files — no page of any source "
                         "was opened, nobody is named, nothing is built, and no roof moves "
                         "ground",
        "inputs": [
            "data/reconstruction/1835_building_inventory.json",
            "data/reconstruction/1835_town_model.json",
            "data/reconstruction/1835_reconstruction_order_book.json",
            "data/reconstruction/1835_lodging_model.json",
            "data/reconstruction/1835_family_archetype_crosswalk.json",
            "data/research/census_1840/composition_1840.json",
        ],
        "method": {
            "one_row_per_group": "Every group in district_group_matrix is asked the question, "
                                 "including the ones no model figure reaches, so a group that "
                                 "stands says why it stands rather than going unmentioned.",
            "the_unit_is_the_test": "A delta between two different units is not a disagreement "
                                    "about roofs. Each row states what was compared with what.",
            "nothing_moves_on_a_tautology": "Where a model figure is read off the programme, "
                                            "the row records the circularity and the group "
                                            "stands on the spec.",
            "no_identity_rulings": "A register record is not folded into another here, and a "
                                   "confidence is never upgraded to close a delta.",
        },
        "groups": rows,
        "dwellings_reconciliation": dwellings_reconciliation(data),
        "crosswalk_counts": {
            "derived_from": "the inventory's family_targets and the crosswalk's own "
                            "priority_rule; every other field in that file is authored "
                            "and is not touched here",
            "roof_totals": counts["roof_totals"],
            "families": counts["families"],
        },
        "totals": {
            "spec_roof_total": spec_total,
            "adopted_roof_total": adopted_total,
            "moved": adopted_total - spec_total,
            "defensible_range": [lo, hi],
            "inside_the_range": lo <= adopted_total <= hi,
            "crosswalk_roof_total": counts["roof_totals"]["target"],
            "crosswalk_agrees_with_the_inventory": counts["roof_totals"]["target"] == spec_total,
        },
        "deltas_owed_out": owed_out(rows, data),
    }


# ------------------------------------------------------------------ the report --

def report_text(doc: dict) -> str:
    t = doc["totals"]
    rec = doc["dwellings_reconciliation"]
    out = [
        "# The 668-roof programme, re-derived against the order book",
        "",
        f"DERIVED. Written by `{doc['generated_by']}`; re-derived by `--check` in "
        "`tools/check.sh`. Do not hand-edit.",
        "",
        f"Ticket {doc['ticket']}. {doc['not_a_reading'].capitalize()}.",
        "",
        "## What moved",
        "",
        f"The specification schedules **{t['spec_roof_total']} roofs**; this re-derivation "
        f"adopts **{t['adopted_roof_total']}**"
        + (f", a move of {t['moved']:+d}." if t["moved"] else " — no group moves."),
        "",
        f"The inventory's own defensible range is {t['defensible_range'][0]}–"
        f"{t['defensible_range'][1]} roofs; the adopted total is "
        + ("inside it." if t["inside_the_range"] else "**outside it**."),
        "",
        "| Group | Spec | Model | Compared in | Adopted | Δ |",
        "|---|---:|---:|---|---:|---:|",
    ]
    for row in doc["groups"]:
        model = "—" if row["model"] is None else f"{row['model']}"
        out.append(f"| `{row['group']}` | {row['spec']} | {model} | {row['compared_in']} | "
                   f"{row['adopted']} | {row['delta']:+d} |")
    out += ["", "## Why each group stands where it does", ""]
    for row in doc["groups"]:
        out.append(f"**`{row['group']}`** — {row['why']}")
        out.append("")
    out += [
        "## The census's 398 dwellings, reconciled",
        "",
        rec["question"],
        "",
        f"- Dwelling roofs on the scene date: **{rec['dwelling_roofs_on_the_scene_date']}** "
        f"({rec['ordinary_dwellings']} ordinary dwellings, "
        f"{rec['larger_houses_and_boarding_houses']} larger houses and boarding houses).",
        f"- Households the order book orders: **{rec['households_the_order_book_orders']:,}**.",
        f"- Households to a dwelling, adopted: **{rec['households_per_dwelling_adopted']}**.",
        f"- The band the census brackets: "
        f"**{rec['households_per_dwelling_the_census_brackets'][0]}–"
        f"{rec['households_per_dwelling_the_census_brackets'][1]}** — "
        f"{rec['how_the_bracket_is_got']}",
        "- Inside the bracket: "
        + ("**yes**." if rec["inside_the_bracket"] else "**no**."),
        "",
        rec["why_short_is_right"],
        "",
        f"Source for the November figures: `{rec['source']}`.",
        "",
        "## The crosswalk's count fields",
        "",
    ]
    cw = doc["crosswalk_counts"]
    out.append("Re-derived from `1835_building_inventory.json`'s `family_targets` and the "
               "crosswalk's own `priority_rule`. Authored content — archetypes, geometry "
               "bands, evidence and assumption notes — is untouched.")
    out += ["", f"Target {cw['roof_totals']['target']} roofs · "
            f"{cw['roof_totals']['phase1_instantiated']} instantiated in phase 1 · "
            f"{cw['roof_totals']['remaining']} remaining.", "",
            "| Rank | Family | Target | Phase 1 | Remaining | Band |",
            "|---:|---|---:|---:|---:|---|"]
    for fid, row in sorted(cw["families"].items(), key=lambda kv: kv[1]["priority_rank"]):
        out.append(f"| {row['priority_rank']} | `{fid}` | {row['target_roofs']} | "
                   f"{row['phase1_instantiated']} | {row['remaining_roofs']} | "
                   f"{row['priority_band']} |")
    out += ["", "## Deltas this re-derivation does not act on", ""]
    for item in doc["deltas_owed_out"]:
        # A DELTA CAN BE SETTLED RATHER THAN OWED (T-1471). It stays in this section
        # because the section is "deltas this re-derivation does not act on", and a
        # settled delta it still does not act on is exactly that; what changes is that
        # nobody is carrying it any more, and the line has to say so or a reader will
        # go looking for an owner who has already finished.
        owner = (f"SETTLED by {item['settled_by']}" if item.get("settled_by")
                 else str(item["owed_to"]))
        out.append(f"**`{item['id']}`** → {owner}. {item['statement']}")
        out.append("")
    return "\n".join(out).rstrip() + "\n"


# ------------------------------------------------------------------ commands --

def cmd_build() -> int:
    data = load()
    doc = build(data)
    counts = crosswalk_counts(data["inventory"], data["crosswalk"])
    repaired = crosswalk_drift(data["crosswalk"], counts)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(report_text(doc), encoding="utf-8")
    rewritten = rewrite_counts_in_place(CROSSWALK.read_text(encoding="utf-8"), counts)
    if crosswalk_drift(json.loads(rewritten), counts):
        raise Fault("the in-place rewrite did not land the derived counts — refusing to "
                    "write a crosswalk that still disagrees with the inventory")
    CROSSWALK.write_text(rewritten, encoding="utf-8")
    t = doc["totals"]
    print(f"OK: the 1835 roof programme re-derives — {len(doc['groups'])} groups, "
          f"{t['spec_roof_total']} → {t['adopted_roof_total']} roofs, "
          f"{len(repaired)} crosswalk count row(s) brought back to the inventory, "
          f"{len(doc['deltas_owed_out'])} delta(s) owed out")
    return 0


def cmd_check() -> int:
    if not OUT.exists():
        raise Fault(f"{OUT.relative_to(ROOT)} has never been built")
    data = load()
    doc = build(data)
    on_disk = json.loads(OUT.read_text(encoding="utf-8"))
    if json.dumps(doc, sort_keys=True) != json.dumps(on_disk, sort_keys=True):
        raise Fault(f"{OUT.relative_to(ROOT)} no longer re-derives from its inputs — "
                    "run tools/reprogramme_roofs_1835.py --build")
    if REPORT.read_text(encoding="utf-8") != report_text(doc):
        raise Fault(f"{REPORT.relative_to(ROOT)} no longer re-derives from the record — "
                    "run tools/reprogramme_roofs_1835.py --build")

    # THE CROSSWALK AND THE INVENTORY DEAL THE SAME ROOFS. This is the drift the
    # ticket found: 662 against 668, and nine ranks one place out.
    counts = crosswalk_counts(data["inventory"], data["crosswalk"])
    drift = crosswalk_drift(data["crosswalk"], counts)
    if drift:
        named = ", ".join(f"{d['family']} ({', '.join(sorted(d['fields']))})" for d in drift[:6])
        raise Fault(f"{CROSSWALK.relative_to(ROOT)}'s count fields no longer re-derive from "
                    f"the inventory's family_targets: {named} — run "
                    "tools/reprogramme_roofs_1835.py --build")

    # THE TWO FILES PARTITION ONE PROGRAMME. A group whose families sum to a
    # different number is a roof scheduled twice or not at all.
    check_partition(data["inventory"])

    if not doc["totals"]["inside_the_range"]:
        raise Fault(f"the adopted total {doc['totals']['adopted_roof_total']} falls outside "
                    "the inventory's own defensible range, and the ticket says nothing about "
                    "why the range itself must move")
    if not doc["dwellings_reconciliation"]["inside_the_bracket"]:
        raise Fault("the households-per-dwelling rate the order book needs falls outside the "
                    "band the census brackets — the programme's dwelling half no longer holds "
                    "the town it is ordered for")
    t = doc["totals"]
    print(f"OK: the 1835 roof programme re-derivation holds — {t['adopted_roof_total']} roofs "
          f"inside {t['defensible_range'][0]}–{t['defensible_range'][1]}, "
          f"{doc['dwellings_reconciliation']['households_per_dwelling_adopted']} households to "
          f"a dwelling inside "
          f"{doc['dwellings_reconciliation']['households_per_dwelling_the_census_brackets']}, "
          f"crosswalk agrees at {t['crosswalk_roof_total']}")
    return 0


def check_partition(inventory: dict) -> None:
    targets = inventory["family_targets"]
    matrix = inventory["district_group_matrix"]
    for group, families in GROUP_FAMILIES.items():
        if not families:
            continue
        got = sum(int(targets[f]) for f in families)
        want = int(matrix[group]["total"])
        if got != want:
            raise Fault(f"the inventory's {group} matrix row totals {want} and its families "
                        f"{', '.join(families)} total {got}")
    got = sum(int(targets[f]) for f in ANCILLARY_FAMILIES)
    want = sum(int(matrix[g]["total"]) for g in ANCILLARY_GROUPS)
    if got != want:
        raise Fault(f"the inventory's ancillary matrix rows total {want} and families "
                    f"{', '.join(ANCILLARY_FAMILIES)} total {got}")
    if sum(int(v) for v in targets.values()) != int(inventory["targets"]["roof_total"]):
        raise Fault("the inventory's family_targets do not sum to its own roof_total")


def cmd_self_test() -> int:
    fired = 0

    def fires(what, fn):
        nonlocal fired
        try:
            fn()
        except Fault:
            fired += 1
            return
        raise AssertionError(f"no Fault raised: {what}")

    bands = {"P0": "50 or more", "P1": "25-49", "P2": "10-24", "P3": "5-9", "P4": "1-4"}
    assert band_for(50, bands) == "P0"
    assert band_for(49, bands) == "P1"
    assert band_for(10, bands) == "P2"
    assert band_for(9, bands) == "P3"
    assert band_for(1, bands) == "P4"

    # A RANK IS A POSITION IN THE FILE'S OWN ORDER, not a number left over from
    # the last time somebody moved a target. This is the I3 drift.
    inv = {"family_targets": {"A": 3, "B": 10, "C": 10},
           "district_group_matrix": {}, "targets": {"roof_total": 23}}
    cw = {"priority_rule": {"order": "descending remaining_roofs, then family id",
                            "bands": bands},
          "families": [{"id": "A", "label": "a", "phase1_instantiated": 0,
                        "priority_rank": 1, "priority_band": "P0"},
                       {"id": "B", "label": "b", "phase1_instantiated": 0},
                       {"id": "C", "label": "c", "phase1_instantiated": 0}],
          "roof_totals": {"target": 0, "phase1_instantiated": 0, "remaining": 0}}
    counts = crosswalk_counts(inv, cw)
    assert [counts["families"][f]["priority_rank"] for f in "ABC"] == [3, 1, 2], counts
    assert counts["roof_totals"]["target"] == 23

    # THE DRIFT IS REPORTED BEFORE IT IS REPAIRED, and `--check` only reports.
    drift = {d["family"] for d in crosswalk_drift(cw, counts)}
    assert drift == {"A", "B", "C", "roof_totals"}, drift
    assert not crosswalk_drift(apply_counts(cw, counts), counts)

    # APPLYING THE COUNTS MOVES NO AUTHORED FIELD.
    applied = apply_counts(cw, counts)
    assert [f["label"] for f in applied["families"]] == ["a", "b", "c"]

    # THE IN-PLACE REWRITE LANDS THE SAME VALUES AND MOVES NOTHING ELSE. The
    # fixture keeps the committed file's shape: one family to a line.
    text = ('{\n  "roof_totals": {"target": 0, "phase1_instantiated": 0, "remaining": 0},\n'
            '  "families": [\n'
            '    {"id": "A", "label": "a", "target_roofs": 9, "phase1_instantiated": 0, '
            '"remaining_roofs": 9, "priority_rank": 1, "priority_band": "P3", "note": "kept"},\n'
            '    {"id": "B", "label": "b", "target_roofs": 9, "phase1_instantiated": 0, '
            '"remaining_roofs": 9, "priority_rank": 2, "priority_band": "P3"},\n'
            '    {"id": "C", "label": "c", "target_roofs": 9, "phase1_instantiated": 0, '
            '"remaining_roofs": 9, "priority_rank": 3, "priority_band": "P3"}\n  ]\n}\n')
    out = rewrite_counts_in_place(text, counts)
    assert not crosswalk_drift(json.loads(out), counts), out
    assert '"note": "kept"' in out and out.count("\n") == text.count("\n"), out
    assert json.loads(out)["families"][0]["label"] == "a"

    # A LAYOUT THIS TOOL CANNOT EDIT IS A REFUSAL, never a silent skip.
    fires("a crosswalk row this tool cannot find",
          lambda: rewrite_counts_in_place(text.replace('"id": "C"', '"id":  "C"'), counts))

    # A CROSSWALK THAT DEALS A FAMILY THE INVENTORY DOES NOT SCHEDULE, and an
    # inventory that schedules one the crosswalk deals to nothing, are both holes.
    fires("a family the inventory does not schedule",
          lambda: crosswalk_counts({"family_targets": {"A": 3}},
                                   {"priority_rule": cw["priority_rule"],
                                    "families": [{"id": "Z", "label": "z",
                                                  "phase1_instantiated": 0}],
                                    "roof_totals": {}}))
    fires("a family the crosswalk deals to nothing",
          lambda: crosswalk_counts({"family_targets": {"A": 3, "B": 1}},
                                   {"priority_rule": cw["priority_rule"],
                                    "families": [{"id": "A", "label": "a",
                                                  "phase1_instantiated": 0}],
                                    "roof_totals": {}}))
    # A TARGET CANNOT BE MET BY UNBUILDING what already stands.
    fires("more phase-1 roofs than the target",
          lambda: crosswalk_counts({"family_targets": {"A": 1}},
                                   {"priority_rule": cw["priority_rule"],
                                    "families": [{"id": "A", "label": "a",
                                                  "phase1_instantiated": 4}],
                                    "roof_totals": {}}))
    # A RE-ORDERED priority_rule IS READ, NOT ASSUMED.
    fires("a priority_rule this tool no longer implements",
          lambda: crosswalk_counts(inv, dict(cw, priority_rule={"order": "by family id",
                                                                "bands": bands})))
    # THE TWO FILES MUST PARTITION ONE PROGRAMME. Fired on the committed
    # inventory with one matrix row moved, so the fixture cannot drift from the
    # shape the real check walks.
    real = load()["inventory"]
    check_partition(real)
    bent = json.loads(json.dumps(real))
    bent["district_group_matrix"]["inns_taverns"]["total"] += 6
    fires("families that do not sum to their matrix row",
          lambda: check_partition(bent))
    bent = json.loads(json.dumps(real))
    bent["family_targets"]["D1"] += 1
    fires("family targets that do not sum to the roof total",
          lambda: check_partition(bent))

    # THE REAL RE-DERIVATION CLOSES, AND IS BYTE-IDENTICAL TWICE OVER.
    data = load()
    doc = build(data)
    assert json.dumps(build(data), sort_keys=True) == json.dumps(doc, sort_keys=True)
    assert doc["totals"]["inside_the_range"], doc["totals"]
    assert doc["dwellings_reconciliation"]["inside_the_bracket"], doc["dwellings_reconciliation"]
    assert len(doc["groups"]) == len(GROUP_FAMILIES), doc["groups"]
    assert doc["totals"]["crosswalk_agrees_with_the_inventory"], doc["totals"]

    # EVERY GROUP IS ASKED, INCLUDING THE ONES NOTHING MOVES. A group that goes
    # unmentioned is a group nobody checked.
    assert {r["group"] for r in doc["groups"]} == set(GROUP_FAMILIES)
    for row in doc["groups"]:
        assert row["why"].strip(), row
        assert row["delta"] == row["adopted"] - row["spec"], row

    # NOTHING IS BUILT, SEATED OR NAMED HERE.
    text = json.dumps(doc)
    for forbidden in ("hh_", "rc_", "person_", "lives_at", "works_at", "structure_id"):
        assert forbidden not in text, f"the re-derivation carries a {forbidden}"

    t = doc["totals"]
    print(f"reprogramme_roofs_1835 self-tests pass ({fired} guards fired, "
          f"{len(doc['groups'])} groups, {t['spec_roof_total']} → "
          f"{t['adopted_roof_total']} roofs, nothing built)")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    try:
        if args.build:
            return cmd_build()
        if args.check:
            return cmd_check()
        if args.self_test:
            return cmd_self_test()
    except Fault as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
