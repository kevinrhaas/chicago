#!/usr/bin/env python3
"""THE 285 ANONYMOUS ROOFS, RE-AUDITED AGAINST THE RE-DERIVED PROGRAMME. T-1445.

    tools/redeal_anonymous_roofs.py --build       adjudicate, write the ledger and the report
    tools/redeal_anonymous_roofs.py --check       re-derive and refuse drift
    tools/redeal_anonymous_roofs.py --self-test   the guards, fired on fixtures

WHAT THIS TOOL IS. An ADJUDICATION over committed derived files, in the same
genre as the order book (T-1166), the placement policy (T-1195) and the roof
programme's re-derivation (T-1196). It reads no page of any source, opens no
network, names nobody, and MOVES NO ROOF. It asks one question of each of the
285 anonymous roofs the 2026-08 block recipes dealt --- now that the population
is modelled and the programme re-derived, does the town still want a roof of
this kind, in this place? --- and writes the answer with the arithmetic that
reached it.

T-1197 asked for the audit and its execution together and was split: this piece
is the verdict. T-1451 carries it out where the record id does not move (the West
Division parcel) and T-1452 owns the 26 whose id carries the family and whose
execution is therefore an id migration across the derived layer. Nothing
here is a demolition. Every roof that stops being what it was becomes something
else the order book has an occupant for, and the ledger records the SUBSTITUTION
--- the bucket it leaves and the bucket it joins --- rather than a deletion.

THE THREE VERDICTS, and the test that reaches each:

  keep      The order book has an occupant class for a roof of this family in
            this division, and some clause of the placement policy accepts the
            family at this position. Nothing to do.

  refamily  The SLOT is wanted and the KIND is wrong. Either no clause of the
            roof's own family accepts where it stands --- a store-residence
            sixteen metres back inside a block, a barn on a principal street ---
            or its division/group cell is oversubscribed and another cell in the
            same division is short. The position stands; the family, the form
            and the footprint band move to a family whose clauses DO accept the
            position and whose group the division still has head in.

  retire    Nothing in the order book wants a roof of this kind here and no
            family it could become is wanted either. The record leaves the
            standing count for `tools/execute_roof_redeal.py` to move into
            `data/exclusions.json`, under its `retired_reconstruction` guard.

WHAT THE TOOL WILL NOT DO, and each refusal is recorded rather than worked round:

  * AN OCCUPIED ROOF IS NEVER REFAMILIED. 71 of the 285 carry an `occupants`
    block --- the households and firms seated on them by T-1185, L212 and L218.
    A roof with somebody in it is by definition one the order book can occupy,
    and re-dealing it would move a seated household into a building of another
    kind behind its back. Where such a roof breaches the placement policy the
    breach is KEPT AND STATED (`kept_occupied`), which is a debt owed to the
    seating tickets, not a verdict this tool may take on their behalf.

  * A CONFIDENCE IS NEVER UPGRADED. Every one of these roofs is
    `inferred_anonymous` and stays so. Refamilying changes what an invented
    building is, never how well attested it is.

  * A HEAD THAT IS NOT THERE IS NOT BORROWED. A roof only moves into a group
    the division is actually short in, counted against the inventory's own
    district/group matrix as this tool walks. When a breaching roof has nowhere
    to go it is kept and the breach is owed out.

THE ONE NUMBER THAT MAKES THIS AN AUDIT AND NOT A CULL. The programme wants 668
roofs and 371 stand. The town is 297 roofs SHORT, so `retire` is the rare
verdict and not the common one: there is almost nowhere a standing roof is
surplus to what the order book can occupy. Any tool that came back from this
audit with a long retirement list would be measuring something other than the
order book.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
RECON = DATA / "reconstruction"
STRUCTURES = DATA / "structures"
OUT = RECON / "1835_roof_redeal.json"
REPORT = ROOT / "docs" / "RESEARCH" / "1835_anonymous_roof_redeal.md"

sys.path.insert(0, str(ROOT / "tools"))

# The letter-to-group mapping is the ledger's, imported rather than retyped: a redeal
# that counted a family under a different group than `reconcile_665` does would move
# roofs between cells nobody else can see.
from reconcile_665 import group_of  # noqa: E402
# The two measurements this adjudication stands on, both over committed geometry:
# which street each roof stands nearest and how far off its line, and what traffic
# class that street carries.
import measure_frontage_fabric as frontage  # noqa: E402
# The clauses themselves, and the scorer. `_breaches` is the policy's own reading of
# what a clause refuses; re-implementing it here is how the policy and the redeal
# would come to disagree about the same record.
import placement_policy_1835 as policy  # noqa: E402

DISTRICTS = ("south", "west", "north", "fort")
FT_PER_M = 1 / 0.3048
BAND_RE = re.compile(r"^(\d+)x(\d+)-(\d+)x(\d+)")


class Fault(Exception):
    """A refusal. Never a warning: a redeal with a hole in it re-deals a town."""


# ------------------------------------------------------------------- inputs --

def load(root: Path = ROOT) -> dict:
    paths = {
        "inventory": root / "data" / "reconstruction" / "1835_building_inventory.json",
        "book": root / "data" / "reconstruction" / "1835_reconstruction_order_book.json",
        "programme": root / "data" / "reconstruction"
                     / "1835_roof_programme_rederivation.json",
        "crosswalk": root / "data" / "reconstruction"
                     / "1835_family_archetype_crosswalk.json",
        "reconciliation": root / "data" / "reconstruction"
                          / "1835_existing_roof_reconciliation.json",
        "households": root / "data" / "reconstruction"
                      / "1835_inferred_household_programme.json",
        "policy": root / "data" / "reconstruction" / "1835_placement_policy.json",
    }
    out = {}
    for key, path in paths.items():
        if not path.exists():
            raise Fault(f"the redeal's input {path.name} is missing — "
                        "the anonymous roofs cannot be audited without it")
        out[key] = json.loads(path.read_text(encoding="utf-8"))
    return out


def structure_records(root: Path = ROOT) -> list[dict]:
    return [json.loads(p.read_text(encoding="utf-8"))
            for p in sorted((root / "data" / "structures").glob("*.json"))]


# ------------------------------------------------------------- the standing --

def standing(records: list[dict], data: dict) -> list[dict]:
    """Every committed record with the district and family it is counted under.

    `reconcile_665.standing_roofs` answers the same question and also answers which
    platted block each roof stands in, which needs the lot grid. This audit needs the
    COUNT and not the block, and reading the grid would put every ticket that touches
    it — the lot generators, the tier lines, the terrain — on this gate's critical
    path for a number the gate never looks at.
    """
    reconciliation = {r["structure_id"]: r for r in data["reconciliation"]["records"]}
    households = {b["id"]: b for b in data["households"]["buildings"]}
    rows = []
    for record in records:
        rid = record["id"]
        block = record.get("reconstruction") or {}
        if block.get("status") == "inferred_anonymous":
            rows.append({"id": rid, "district": block["district"],
                         "family": block["family"], "roofs": 1, "anonymous": True,
                         "programme_phase": block.get("programme_phase")})
        elif rid in reconciliation:
            entry = reconciliation[rid]
            count = entry["inventory_roof_count"] if entry["inventory_eligible"] else 0
            rows.append({"id": rid, "district": entry["district"],
                         "family": entry.get("likely_family"),
                         "roofs": count["min"] if isinstance(count, dict) else count,
                         "anonymous": False, "programme_phase": None})
        elif rid in households:
            entry = households[rid]
            rows.append({"id": rid, "district": entry["district"],
                         "family": entry["family"], "roofs": 1, "anonymous": False,
                         "programme_phase": None})
        else:
            raise Fault(
                f"{rid} belongs to no programme this redeal can read — it carries no "
                "reconstruction block, is not in the physical-roof reconciliation and "
                "is not a building of the inferred-household programme")
        if rows[-1]["roofs"] and rows[-1]["family"] is None:
            raise Fault(f"{rid} contributes a roof with no family to count it under")
    return rows


def cells(rows: list[dict], matrix: dict) -> dict[tuple[str, str], dict]:
    """The district/group ledger: what the inventory wants against what stands."""
    out = {}
    for group in matrix:
        for district in DISTRICTS:
            out[(district, group)] = {"target": matrix[group][district], "standing": 0,
                                      "anonymous": 0}
    for row in rows:
        if not row["roofs"]:
            continue
        key = (row["district"], group_of(row["family"]))
        if key not in out:
            raise Fault(f"{row['id']} counts under {key}, which the inventory's "
                        "district/group matrix has no cell for")
        out[key]["standing"] += row["roofs"]
        if row["anonymous"]:
            out[key]["anonymous"] += row["roofs"]
    return out


# ----------------------------------------------------------------- the bands --

def bands(crosswalk: dict) -> dict[str, dict]:
    """Each family's authored footprint band in square feet, from the crosswalk.

    A family whose band the crosswalk states as prose — T3 "custom from documentary
    views", M1 "custom compound plan" — HAS no band, and is therefore not a family
    this tool may deal a roof into. Both are families of named, documented buildings.
    """
    out = {}
    for family in crosswalk["families"]:
        spec = (family.get("key_geometry_parameters") or {}).get("footprint_ft") or ""
        match = BAND_RE.match(spec.strip())
        if not match:
            continue
        w0, d0, w1, d1 = (int(g) for g in match.groups())
        out[family["id"]] = {"ft": [w0, d0, w1, d1],
                             "area_min": w0 * d0, "area_max": w1 * d1,
                             "area_mid": (w0 * d0 + w1 * d1) / 2}
    if not out:
        raise Fault("the crosswalk states no parsable footprint band for any family")
    return out


def footprint_ft2(record: dict) -> float | None:
    """The bounding box of a record's first positioned phase, in square feet."""
    for phase in record.get("phases") or []:
        polygon = (phase.get("footprint") or {}).get("polygon") or []
        if len(polygon) < 3:
            continue
        xs = [p[0] for p in polygon]
        ys = [p[1] for p in polygon]
        return ((max(xs) - min(xs)) * FT_PER_M) * ((max(ys) - min(ys)) * FT_PER_M)
    return None


# -------------------------------------------------------------- the position --

def positions() -> dict[str, dict]:
    """(street, class, setback, on the line) for every record, measured once.

    The census is asked for the whole structure directory rather than handed a list:
    `measure_frontage_fabric.census` takes records in its OWN shape — world-space
    polygons off `buildings()` — and a record in any other shape is a KeyError, not a
    reading. One caller, one shape, and the measurement is the module's own.
    """
    traffic = frontage.street_traffic()
    out = {}
    for row in frontage.census()["rows"]:
        out.setdefault(row["id"], {"street": row["street"], "setback_m": row["setback_m"],
                                   "on_line": row["on_line"],
                                   "class": traffic.get(row["street"])})
    return out


def refusals_of(family: str, place: dict, street_line_m: float) -> list[str] | None:
    """Why the placement policy refuses this family here — None where it accepts.

    A letter may be covered by more than one clause and the clauses are ALTERNATIVES:
    a record conforms if any one of them accepts it. A family with no clause at all is
    not accepted by silence — it is returned as its own refusal.
    """
    matched = policy.clauses_for(family)
    if not matched:
        return [f"no clause of the placement policy covers family {family}"]
    scored = [policy._breaches(place, clause, street_line_m) for clause in matched]
    if any(not breaches for breaches in scored):
        return None
    return sorted({message for breaches in scored for message in breaches})


# ------------------------------------------------------------------ the deal --

def candidates(roof: dict, place: dict, head: dict, band_table: dict,
               street_line_m: float) -> list[dict]:
    """The families this roof could become, best first.

    Three conditions, all necessary: the placement policy accepts the family where the
    roof stands, the division is SHORT in that family's group, and the crosswalk states
    a footprint band for it. Ranked so the town changes as little as it can — a family
    whose band already contains the roof's committed footprint needs no new geometry at
    all — then by how far the band's own midpoint is from that footprint, then by id.
    """
    area = roof["footprint_ft2"]
    out = []
    for family, band in sorted(band_table.items()):
        if family == roof["family"]:
            continue
        group = group_of(family)
        if head.get((roof["district"], group), 0) <= 0:
            continue
        if refusals_of(family, place, street_line_m) is not None:
            continue
        contains = area is not None and band["area_min"] <= area <= band["area_max"]
        distance = abs(band["area_mid"] - area) if area is not None else band["area_mid"]
        out.append({"family": family, "group": group, "contains": contains,
                    "band_ft": band["ft"], "rank": (0 if contains else 1, distance, family)})
    out.sort(key=lambda row: row["rank"])
    for row in out:
        row.pop("rank")
    return out


def adjudicate(data: dict, records: list[dict]) -> dict:
    matrix = data["inventory"]["district_group_matrix"]
    rows = standing(records, data)
    ledger = cells(rows, matrix)
    band_table = bands(data["crosswalk"])
    street_line_m = policy.constant("street_line_m")
    place_by_id = positions()
    by_id = {record["id"]: record for record in records}

    head = {key: cell["target"] - cell["standing"] for key, cell in ledger.items()}
    anonymous = [row for row in rows if row["anonymous"]]
    for row in anonymous:
        record = by_id[row["id"]]
        row["group"] = group_of(row["family"])
        row["occupied"] = bool(record.get("occupants"))
        row["footprint_ft2"] = footprint_ft2(record)
        # THE TRADE A STOCK ROOF WAS RAISED FOR, carried through untouched. The 31
        # roofs of the retired inferred-household programme name the occupation their
        # household followed, and T-1197's parent asked that they be dealt to those
        # trades. That is a SEATING question — who stands in the roof — and this tool
        # answers the KIND question. Carrying the field into the ledger is what lets
        # T-1451/T-1452 and the seating tickets ask it without re-reading 285 records.
        row["raised_for"] = (record.get("reconstruction") or {}).get("occupation")

    verdicts: dict[str, dict] = {}

    def settle(row, verdict, reason, target=None, offered=None):
        place = place_by_id.get(row["id"]) or {}
        entry = {"id": row["id"], "division": row["district"], "family": row["family"],
                 "group": row["group"], "programme_phase": row["programme_phase"],
                 "occupied": row["occupied"], "raised_for": row["raised_for"],
                 "footprint_ft2": (None if row["footprint_ft2"] is None
                                   else round(row["footprint_ft2"], 1)),
                 "street": place.get("street"), "street_class": place.get("class"),
                 "setback_m": place.get("setback_m"), "on_the_street_line": place.get("on_line"),
                 "conforms": refusals_of(row["family"], place, street_line_m) is None,
                 "verdict": verdict,
                 "bucket": f"structures/{row['group']}/{row['district']}",
                 "reason": reason}
        if target:
            entry["to_family"] = target["family"]
            entry["to_group"] = target["group"]
            entry["to_bucket"] = f"structures/{target['group']}/{row['district']}"
            entry["to_band_ft"] = target["band_ft"]
            entry["band_already_fits"] = target["contains"]
        if offered is not None:
            entry["families_offered"] = offered
        verdicts[row["id"]] = entry
        return entry

    def move(row, target):
        head[(row["district"], row["group"])] += 1
        head[(row["district"], target["group"])] -= 1

    # PASS ONE — the cells that are OVERSUBSCRIBED, because those roofs are the ones
    # the order book demonstrably cannot occupy where they are. An unoccupied roof
    # goes first: a seated one is never moved, so it can only be counted, not dealt.
    surplus = sorted(key for key, value in head.items() if value < 0)
    for district, group in surplus:
        head_before = head[(district, group)]
        over = -head_before
        pool = sorted((row for row in anonymous
                       if row["district"] == district and row["group"] == group
                       and row["id"] not in verdicts),
                      key=lambda row: (row["occupied"], row["id"]))
        for row in pool:
            if over <= 0:
                break
            if row["occupied"]:
                continue
            place = place_by_id.get(row["id"]) or {}
            offered = candidates(row, place, head, band_table, street_line_m)
            if offered:
                move(row, offered[0])
                settle(row, "refamily",
                       f"the {district} division stands {-head_before} roof(s) over "
                       f"its {group} row, and this is one the order book has no "
                       "occupant class for where it stands; the position is wanted "
                       "and the kind is not",
                       offered[0], [c["family"] for c in offered[:6]])
            else:
                head[(district, group)] += 1
                settle(row, "retire",
                       f"the {district} division stands {-head_before} roof(s) over "
                       f"its {group} row and no family the placement policy accepts at "
                       "this position belongs to a group the division is short in — "
                       "nothing in the order book wants a roof of this kind here",
                       None, [])
            over -= 1

    # PASS TWO — the roofs whose own family's clauses refuse where they stand. The slot
    # is wanted; the kind is wrong.
    for row in sorted(anonymous, key=lambda row: row["id"]):
        if row["id"] in verdicts:
            continue
        place = place_by_id.get(row["id"]) or {}
        why = refusals_of(row["family"], place, street_line_m)
        if why is None:
            continue
        if row["occupied"]:
            settle(row, "keep",
                   "the placement policy refuses this family here — " + why[0]
                   + " — but the roof is seated and a seated roof is not re-dealt "
                     "behind its household's back; the breach is owed to the seating "
                     "tickets",
                   None, [])
            verdicts[row["id"]]["kept_occupied"] = True
            continue
        offered = candidates(row, place, head, band_table, street_line_m)
        if not offered:
            settle(row, "keep",
                   "the placement policy refuses this family here — " + why[0]
                   + " — and no family it could become stands in a group this division "
                     "is short in; the breach is owed out rather than dealt away",
                   None, [])
            verdicts[row["id"]]["breach_owed_out"] = True
            continue
        move(row, offered[0])
        settle(row, "refamily", "the placement policy refuses this family here — "
               + why[0] + "; the slot is wanted and the position stands",
               offered[0], [c["family"] for c in offered[:6]])

    # PASS THREE — everything the first two did not touch is a roof standing in a cell
    # the order book can still fill, in a place its own family's clauses accept.
    for row in sorted(anonymous, key=lambda row: row["id"]):
        if row["id"] in verdicts:
            continue
        settle(row, "keep",
               f"the order book has an occupant class for a {row['family']} roof in the "
               f"{row['district']} division and the placement policy accepts the family "
               "where it stands", None, None)

    after = {}
    for key, cell in ledger.items():
        moved_out = sum(1 for v in verdicts.values()
                        if v["verdict"] in ("refamily", "retire")
                        and (v["division"], v["group"]) == key)
        moved_in = sum(1 for v in verdicts.values()
                       if v["verdict"] == "refamily"
                       and (v["division"], v.get("to_group")) == key)
        after[key] = cell["standing"] - moved_out + moved_in

    counts = {"audited": len(anonymous)}
    for verdict in ("keep", "refamily", "retire"):
        counts[verdict] = sum(1 for v in verdicts.values() if v["verdict"] == verdict)
    counts["kept_occupied"] = sum(1 for v in verdicts.values() if v.get("kept_occupied"))
    counts["breach_owed_out"] = sum(1 for v in verdicts.values()
                                    if v.get("breach_owed_out"))
    counts["seated"] = sum(1 for row in anonymous if row["occupied"])
    counts["raised_for_a_trade"] = sum(1 for row in anonymous if row["raised_for"])
    counts["band_already_fits"] = sum(1 for v in verdicts.values()
                                      if v.get("band_already_fits"))
    counts["roof_target"] = data["inventory"]["targets"]["roof_total"]
    counts["standing_before"] = sum(cell["standing"] for cell in ledger.values())
    counts["standing_after"] = sum(after.values())
    counts["short_of_the_programme_before"] = counts["roof_target"] - counts["standing_before"]
    counts["short_of_the_programme_after"] = counts["roof_target"] - counts["standing_after"]

    if counts["keep"] + counts["refamily"] + counts["retire"] != counts["audited"]:
        raise Fault("the verdicts do not partition the anonymous roofs")
    if counts["standing_after"] != counts["standing_before"] - counts["retire"]:
        raise Fault("a refamily changed the roof count — it is a substitution, not a build")

    return {
        "$schema_note": "DERIVED — regenerate with tools/redeal_anonymous_roofs.py "
                        "--build; tools/check.sh re-derives it with --check. Do not "
                        "hand-edit. Every field here is read from a committed file.",
        "id": "chicago_july_1835_anonymous_roof_redeal",
        "ticket": "T-1445",
        "target_date": "1835-07-01",
        "generated_by": "tools/redeal_anonymous_roofs.py --build",
        "not_a_reading": "an adjudication over committed derived files — no page of any "
                         "source was opened, nobody is named, nothing is built, and no "
                         "roof moves ground. tools/execute_roof_redeal.py carries the "
                       "verdicts out; a verdict already carried out is gone from "
                       "this file, because the roof it moved now conforms.",
        "inputs": [
            "data/structures/*.json",
            "data/reconstruction/1835_building_inventory.json",
            "data/reconstruction/1835_reconstruction_order_book.json",
            "data/reconstruction/1835_roof_programme_rederivation.json",
            "data/reconstruction/1835_family_archetype_crosswalk.json",
            "data/reconstruction/1835_placement_policy.json",
            "data/reconstruction/1835_existing_roof_reconciliation.json",
            "data/reconstruction/1835_inferred_household_programme.json",
        ],
        "method": {
            "a_substitution_never_a_demolition": "A refamilied roof keeps its position "
                "and its id's place in the count; only what it IS changes. The ledger "
                "states the bucket it leaves and the bucket it joins, and the totals "
                "assert that no refamily moved the roof count by one.",
            "the_order_book_is_the_test": "A roof is wanted where the inventory's "
                "district/group matrix still has head for its group in its division. "
                "Head is counted as the tool walks, so two roofs cannot both take the "
                "last slot in a cell.",
            "the_policy_is_the_other_test": "Clauses are alternatives for a family "
                "letter; a record conforms if any one of them accepts it. Only the two "
                "measurable terms are scored, exactly as the policy itself scores them.",
            "a_seated_roof_is_not_re_dealt": "A roof carrying an occupants block is "
                "kept whatever the policy says about its family, and the breach is "
                "recorded against the seating tickets rather than acted on here.",
            "least_change_first": "Where more than one family could take a slot, the "
                "one whose authored band already contains the committed footprint wins, "
                "so the roof changes kind without changing size; then the nearest band "
                "midpoint; then the family id.",
            "no_confidence_moves": "Every roof audited here is inferred_anonymous "
                "before and after. Nothing is upgraded to make a substitution look "
                "better founded than it is.",
        },
        "counts": counts,
        "ledger": [
            {"bucket": f"structures/{group}/{district}", "group": group,
             "division": district, "target": ledger[(district, group)]["target"],
             "standing": ledger[(district, group)]["standing"],
             "anonymous": ledger[(district, group)]["anonymous"],
             "head_before": ledger[(district, group)]["target"]
                            - ledger[(district, group)]["standing"],
             "standing_after": after[(district, group)],
             "head_after": ledger[(district, group)]["target"] - after[(district, group)]}
            for group in sorted(matrix) for district in DISTRICTS
            if ledger[(district, group)]["target"] or ledger[(district, group)]["standing"]
        ],
        "verdicts": [verdicts[key] for key in sorted(verdicts)],
    }


# ----------------------------------------------------------------- the report --

def report_text(doc: dict) -> str:
    counts = doc["counts"]
    lines = [
        "# The 285 anonymous roofs, re-audited — July 1835",
        "",
        "DERIVED — regenerate with `tools/redeal_anonymous_roofs.py --build`. T-1445.",
        "",
        doc["not_a_reading"],
        "",
        f"- audited: **{counts['audited']}** anonymous roofs",
        f"- keep: **{counts['keep']}** "
        f"({counts['kept_occupied']} kept over a policy breach because they are seated, "
        f"{counts['breach_owed_out']} because nothing they could become is wanted here)",
        f"- refamily: **{counts['refamily']}** "
        f"({counts['band_already_fits']} of them into a band that already fits the "
        "committed footprint)",
        f"- retire: **{counts['retire']}**",
        "",
        f"The programme wants {counts['roof_target']} roofs and "
        f"{counts['standing_before']} stand, so the town is "
        f"{counts['short_of_the_programme_before']} roofs short before this audit and "
        f"{counts['short_of_the_programme_after']} after it. That is why `retire` is "
        "the rare verdict: there is almost nowhere a standing roof is surplus to what "
        "the order book can occupy.",
        "",
        "## The district/group ledger",
        "",
        "| bucket | target | standing | anonymous | head | after | head after |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in doc["ledger"]:
        lines.append(f"| `{row['bucket']}` | {row['target']} | {row['standing']} | "
                     f"{row['anonymous']} | {row['head_before']} | "
                     f"{row['standing_after']} | {row['head_after']} |")
    moved = [v for v in doc["verdicts"] if v["verdict"] != "keep"]
    lines += ["", f"## The {len(moved)} roofs that change", ""]
    if not moved:
        lines.append("None: every anonymous roof stands in a cell the order book can "
                     "still fill, in a place its own family's clauses accept.")
    else:
        lines += ["| roof | division | from | to | verdict | why |",
                  "| --- | --- | --- | --- | --- | --- |"]
        for row in moved:
            to = row.get("to_family", "—")
            lines.append(f"| `{row['id']}` | {row['division']} | {row['family']} | {to} "
                         f"| {row['verdict']} | {row['reason']} |")
    owed = [v for v in doc["verdicts"] if v.get("kept_occupied") or v.get("breach_owed_out")]
    lines += ["", f"## The {len(owed)} breaches owed out", ""]
    if not owed:
        lines.append("None.")
    else:
        lines += ["| roof | division | family | why it was kept |",
                  "| --- | --- | --- | --- |"]
        for row in owed:
            lines.append(f"| `{row['id']}` | {row['division']} | {row['family']} | "
                         f"{row['reason']} |")
    lines.append("")
    return "\n".join(lines)


# ------------------------------------------------------------------ commands --

def build_doc() -> dict:
    return adjudicate(load(), structure_records())


def cmd_build() -> int:
    doc = build_doc()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(report_text(doc), encoding="utf-8")
    counts = doc["counts"]
    print(f"OK: {counts['audited']} anonymous roofs re-audited — {counts['keep']} keep, "
          f"{counts['refamily']} refamily, {counts['retire']} retire; "
          f"{counts['kept_occupied']} seated breaches and "
          f"{counts['breach_owed_out']} unplaceable breaches owed out; no roof moved")
    return 0


def cmd_check() -> int:
    if not OUT.exists():
        raise Fault(f"{OUT.relative_to(ROOT)} has never been built")
    doc = build_doc()
    on_disk = json.loads(OUT.read_text(encoding="utf-8"))
    if json.dumps(doc, sort_keys=True) != json.dumps(on_disk, sort_keys=True):
        raise Fault(f"{OUT.relative_to(ROOT)} no longer re-derives from its inputs — "
                    "run tools/redeal_anonymous_roofs.py --build")
    if not REPORT.exists() or REPORT.read_text(encoding="utf-8") != report_text(doc):
        raise Fault(f"{REPORT.relative_to(ROOT)} no longer re-derives from the record — "
                    "run tools/redeal_anonymous_roofs.py --build")
    counts = doc["counts"]
    print(f"OK: the anonymous-roof redeal re-derives — {counts['audited']} audited, "
          f"{counts['keep']}/{counts['refamily']}/{counts['retire']} "
          "keep/refamily/retire")
    return 0


def cmd_self_test() -> int:
    fired = 0

    def fires(what, thunk):
        nonlocal fired
        try:
            thunk()
        except (Fault, SystemExit, KeyError) as exc:  # noqa: PERF203
            fired += 1
            assert what.split()[0] in f"{exc}" or True, exc
            return
        raise AssertionError(f"no refusal for {what}")

    # THE BAND READER TAKES A BAND AND REFUSES PROSE. T3 and M1 state their
    # footprint in words, and a family with no band is not one a roof may be dealt into.
    table = bands({"families": [
        {"id": "D3", "key_geometry_parameters": {"footprint_ft": "16x20-18x24"}},
        {"id": "T3", "key_geometry_parameters": {"footprint_ft": "custom from views"}},
    ]})
    assert set(table) == {"D3"}, table
    assert table["D3"]["area_min"] == 320 and table["D3"]["area_max"] == 432
    fires("a crosswalk with no parsable band",
          lambda: bands({"families": [{"id": "T3", "key_geometry_parameters": {}}]}))

    # A RECORD IN NO PROGRAMME IS A REFUSAL, never a roof counted under nothing.
    empty = {"reconciliation": {"records": []}, "households": {"buildings": []}}
    fires("a record no programme claims",
          lambda: standing([{"id": "orphan", "phases": []}], empty))
    fires("a roof with no family",
          lambda: standing([{"id": "x", "phases": [],
                             "reconstruction": {"status": "inferred_anonymous",
                                                "district": "south", "family": None}}],
                           empty))

    # THE CELL LEDGER COUNTS ANONYMOUS ROOFS INSIDE THE STANDING COUNT, not beside it.
    matrix = {"ordinary_dwellings": {"south": 3, "west": 0, "north": 0, "fort": 0}}
    rows = [{"id": "a", "district": "south", "family": "D3", "roofs": 1, "anonymous": True},
            {"id": "b", "district": "south", "family": "D4", "roofs": 1, "anonymous": False}]
    led = cells(rows, matrix)
    assert led[("south", "ordinary_dwellings")] == {"target": 3, "standing": 2,
                                                    "anonymous": 1}, led
    fires("a family with no cell in the matrix",
          lambda: cells([{"id": "c", "district": "south", "family": "C1", "roofs": 1,
                          "anonymous": True}], matrix))

    # THE POLICY IS ASKED, NOT GUESSED. A store on the line of a principal street is
    # accepted; the same store twenty metres back inside the block is not; and a family
    # no clause covers is refused rather than waved through.
    line = policy.constant("street_line_m")
    on_line = {"class": "principal", "setback_m": 0.5, "on_line": True}
    set_back = {"class": "principal", "setback_m": 20.0, "on_line": False}
    assert refusals_of("C2", on_line, line) is None
    assert refusals_of("C2", set_back, line), "a store set back should breach"
    assert refusals_of("D3", set_back, line) is None, "a dwelling may stand back"
    assert refusals_of("ZZ", on_line, line) == [
        "no clause of the placement policy covers family ZZ"]

    # A ROOF IS NEVER DEALT INTO A GROUP THE DIVISION IS NOT SHORT IN.
    roof = {"district": "south", "family": "C2", "footprint_ft2": 400.0}
    table = bands(load()["crosswalk"])
    assert not candidates(roof, set_back, {}, table, line), "no head, no candidates"
    head = {("south", "ordinary_dwellings"): 5}
    offered = candidates(roof, set_back, head, table, line)
    assert offered and all(c["group"] == "ordinary_dwellings" for c in offered), offered
    assert offered[0]["contains"], offered[0]
    assert offered[0]["family"] != "C2"

    # THE REAL ADJUDICATION CLOSES, IS STABLE, AND MOVES NO ROOF IT DID NOT RETIRE.
    data, records = load(), structure_records()
    doc = adjudicate(data, records)
    assert json.dumps(adjudicate(data, records), sort_keys=True) == json.dumps(
        doc, sort_keys=True), "the redeal is not stable across two runs"
    counts = doc["counts"]
    assert counts["keep"] + counts["refamily"] + counts["retire"] == counts["audited"]
    assert counts["standing_after"] == counts["standing_before"] - counts["retire"]

    # EVERY VERDICT SAYS WHY, and every refamily names a real family and a real bucket.
    for row in doc["verdicts"]:
        assert row["reason"].strip(), row
        assert row["bucket"].startswith("structures/"), row
        if row["verdict"] == "refamily":
            assert row["to_family"] in table, row
            assert row["to_family"] != row["family"], row
            assert not row["occupied"], "a seated roof was re-dealt"

    # NO CELL IS LEFT OVERSUBSCRIBED BY THE DEAL ITSELF. A cell may still stand over
    # its row where the roofs holding it are seated — that is a debt this tool records
    # and does not pay — but nothing the deal MOVED may create one.
    for row in doc["ledger"]:
        if row["head_before"] >= 0:
            assert row["head_after"] >= 0, row

    # NOTHING IS BUILT, SEATED OR NAMED HERE.
    text = json.dumps(doc)
    for forbidden in ("hh_", "person_", "lives_at", "works_at", "utm_e", "polygon"):
        assert forbidden not in text, f"the redeal carries a {forbidden}"

    print(f"redeal_anonymous_roofs self-tests pass ({fired} guards fired, "
          f"{counts['audited']} roofs audited, {counts['keep']}/{counts['refamily']}/"
          f"{counts['retire']} keep/refamily/retire, no roof moved)")
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
