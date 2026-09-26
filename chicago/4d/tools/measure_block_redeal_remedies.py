#!/usr/bin/env python3
"""THE PLATTED BLOCKS' SIX REFAMILY VERDICTS, AND THE CLAUSE THAT FREES THEM. T-1482.

    tools/measure_block_redeal_remedies.py --build      write the report
    tools/measure_block_redeal_remedies.py --check      re-derive and refuse drift
    tools/measure_block_redeal_remedies.py --self-test  the assertions, on fixtures

T-1445 adjudicated the town's 285 anonymous roofs and returned 32 refamily verdicts.
T-1451 carried out the six whose ids do not move; T-1480 and T-1494 migrated the North
Division's nine and the phase-one South parcel's eleven. THESE SIX ARE THE REMAINDER,
and the rename was never what stopped them.

Every one of the six is an A-family yard building standing at a `yard` setback off its
block alley, behind the principal roof on its own lot. The adjudication moves each one
into an `ordinary_dwellings` family. The inventory class was read off the GROUP ALONE, so
a dwelling family came out `principal_functional` wherever it stood --- and the parcel
gate refuses a second principal roof on a lot that already carries one. All six were
refused, all 36 families the adjudication offers across them are ordinary dwellings so no
re-deal inside the verdict avoided it, and the three blocks hold two open lots between
them against six roofs needing ground. That was this tool's finding, it was costed as
three remedies, and it was put to the owner because all three change what the town IS.

HE RULED ON 2026-09-23: option (a), *"treat a rear cottage as ancillary, so a lot may
carry a main house plus a rear dwelling"*. T-1610 carries that ruling into the two places
it has to live --- `rear_dwelling_behind_its_own_roof` in the placement policy, and
`reconcile_665.inventory_class`, which now reads the POSITION as well as the group: off
the alley, on a lot whose principal roof is already dealt, a dwelling is ancillary. So
this tool's own measurement is what shows the ruling landed. It re-derives the same six
verdicts against the same committed files and finds NONE of them refused, and the class
no longer moves for any of them, which is why the block schedule's principal-roof counts
do not move either.

AND T-1611 HAS NOW RUN. `tools/execute_roof_redeal.py --redeal-blocks` carried all six out
--- the slot family moved, the class was ASKED of the derivation rather than typed, the
record ids moved with the family and every committed file that named one was carried across,
and the meshes were rebaked. So the ordinary reading of this tool is now ZERO outstanding
verdicts, and that is what a carried-out adjudication looks like from here: the ledger is
re-derived over the town as it stands, the six conform where they stand, and the
re-derivation returns `keep` for each. The permanent record of the move is the block
recipe's own `redealt` block, which `execute_roof_redeal.py --check-blocks` holds to the
slots and to the live adjudication. NOTHING IS ADJUDICATED HERE AND NOTHING IS MOVED: no
verdict is rewritten, no family is chosen, no recipe slot moves, no confidence changes and
no record is written to. The three remedies stay in the report as what was asked and what
each would have cost, with the one the owner took marked as taken --- and the clause
witness stays too, because the argument that won the ruling does not stop being the reason
for it once it has been acted on.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
RECON = DATA / "reconstruction"
LEDGER = RECON / "1835_roof_redeal.json"
BLOCK_RECIPE = RECON / "1835_platted_block_parcels.json"
POLICY = RECON / "1835_placement_policy.json"
REPORT = RECON / "1835_block_redeal_remedies.json"
DOC = ROOT / "docs" / "RESEARCH" / "1835_block_redeal_remedies.md"

TICKET = "T-1482"
PREFIX = "recon_1835_blk_"
CLAUSE_ID = "ancillary_behind_its_own_roof"

sys.path.insert(0, str(ROOT / "tools"))

# The same letter-to-group mapping the adjudication and the 665 ledger use, and the same
# class derivation the generators deal by. Imported rather than retyped: a class computed
# under a second opinion about which letter is a stable, or about what standing in a yard
# means, would not be the one the generator enforces. Since T-1610 `inventory_class` takes
# the POSITION as well as the family, which is the owner's rear-cottage ruling written as
# code; called with no position it gives the group-only answer it always gave.
from reconcile_665 import group_of, houses_a_household  # noqa: E402
from reconcile_665 import inventory_class  # noqa: E402


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def outstanding(ledger: dict) -> list[dict]:
    """The block verdicts T-1451 recorded rather than executed, in id order."""
    return sorted((v for v in ledger["verdicts"]
                   if v["id"].startswith(PREFIX) and v["verdict"] == "refamily"),
                  key=lambda v: v["id"])


def slot_index(recipe: dict) -> dict[str, tuple[dict, dict, int]]:
    """Every id this recipe builds, against the block and slot that build it.

    The id is the generator's own: block, family and the sequence number the slot's
    POSITION in the deal gives it. Refamilying keeps the position, so the sequence
    survives the rename and only the family letter in the middle moves.
    """
    out = {}
    for block in recipe["blocks"]:
        start = int(block.get("seq_start", 1))
        for seq, slot in enumerate(block["slots"], start=start):
            sid = (f"{PREFIX}{block['block_id'].removeprefix('blk_')}"
                   f"_{slot['family'].lower()}_{seq:02d}")
            out[sid] = (block, slot, seq)
    return out


def principal_lots(block: dict) -> dict[int, str]:
    """Which lot each of this deal's principal roofs stands on, by roof id.

    `generate_block_infill` builds this same set as `used` and refuses it holding a
    lot twice. A frontage run holds no lot per unit — it counts against the lots the
    recipe named for it — so those lots are in the set once, under the run's name.
    """
    start = int(block.get("seq_start", 1))
    held: dict[int, str] = {}
    for seq, slot in enumerate(block["slots"], start=start):
        if slot["inventory_class"] != "principal_functional" or "lot" not in slot:
            continue
        held[int(slot["lot"])] = (f"{PREFIX}{block['block_id'].removeprefix('blk_')}"
                                  f"_{slot['family'].lower()}_{seq:02d}")
    for index in (block.get("frontage") or {}).get("lots", ()):
        held.setdefault(int(index), f"the frontage run "
                                    f"{block['programme_phase']} was dealt")
    return held


def open_lots(block: dict) -> list[dict]:
    entries = block.get("open_lots")
    if entries is None:
        single = block.get("open_lot")
        entries = [single] if single else []
    return list(entries)


def witness_rows() -> list[dict]:
    """The clause's own evidence, re-read against the same scored term.

    `_breaches` scores `class:<the traffic class of the street the record FRONTS>`
    against the clause's `avoids`. The clause avoids `class:principal`, so this asks the
    documented stables and barns it cites the question it asked the six roofs.

    T-1511: a record beyond the census's frontage reach fronts no street and therefore
    has no class, so the scored term cannot speak for it either way — `no` would read as
    "and the clause is content with it", which is not what the policy says. Such a row is
    reported as `fronts_no_street` and counted separately from the breaching ones. Two of
    this clause's four evidence records are in that position: `fort_dearborn_big_barn`
    and `fort_dearborn_wash_house`, on the reservation, 270.75 m and 420.22 m from the
    nearest platted corridor. The policy still refuses the wash house — the clause seats
    a roof by a `yard` setback off a block alley and there is no platted lot under it —
    and accepts the barn under `farms_and_country_seats`, which is the `unplatted`
    clause written for that ground.
    """
    import placement_policy_1835 as policy  # noqa: PLC0415
    clause = policy.clause(CLAUSE_ID)
    by_id = {row["id"]: row for row in policy.reading()["rows"]}
    rows = []
    for rid in clause["evidence"]:
        row = by_id.get(rid)
        if row is None:
            rows.append({"id": rid, "standing_with_a_street": False})
            continue
        rows.append({
            "id": rid, "standing_with_a_street": True,
            "family": row["family"], "street": row.get("street"),
            "street_class": row["class"],
            "setback_m": (None if row["setback_m"] is None
                          else round(float(row["setback_m"]), 2)),
            "fronts_no_street": row.get("street") is None,
            "breaches_its_own_clause": f"class:{row['class']}" in clause["avoids"],
            "the_policy_refuses_it": CLAUSE_ID in {
                cid for cid, breaches in row["breaches"].items() if breaches},
        })
    return rows


METHOD = {
    "the_class_is_read_off_the_group_and_the_position": (
        "`generate_block_infill` writes a roof's `inventory_class` from its slot, and "
        "`reconcile_665.inventory_class` is the one derivation behind every slot: the "
        "two ancillary groups are barns_stables and small_outbuildings and those are "
        "ancillary wherever they stand, and since T-1610 anything else is ancillary too "
        "when it stands in the YARD — off the alley, on a lot whose principal roof is "
        "already dealt. That is the owner's ruling of 2026-09-23 and the placement "
        "policy's `rear_dwelling_behind_its_own_roof`. Imported here rather than "
        "retyped, because a class computed under a second opinion would not be the one "
        "the generator enforces."),
    "the_refusal_is_the_generator_s_own": (
        "The parcel gate collects the lots its principal roofs stand on — the frontage "
        "run counting against the lots it was dealt — and refuses the set holding a lot "
        "twice: `two principal roofs on one lot`. This tool asks that same question of "
        "each roof at its standing position, and names the roof already there. It is "
        "still asked of all six: the gate has not been loosened and the lots are still "
        "held. What changed is the class each roof lands in, so the question now has a "
        "different answer."),
    "every_offered_family_is_asked": (
        "The adjudication ranks the families each roof could become. A remedy inside "
        "the verdict would have been an offered family whose group is ancillary, so the "
        "class did not move by the family alone; every one of them is asked and the "
        "count of ancillary offers is the answer. It is still nought, and it is still "
        "worth printing: it is the measurement that showed no re-deal inside the verdict "
        "could have avoided the refusal, which is why the question went to the owner."),
    "the_ground_is_counted_not_estimated": (
        "The `move them instead` remedy is priced against the lots the recipe itself "
        "calls open, with the recipe's own stated reason for each one carried into the "
        "report — a lot declared open on the programme's alternating-vacancy assumption "
        "is not free ground, it is a statement about the town."),
    "the_clause_is_asked_its_own_question": (
        "The six were refused for standing nearest a principal street, which is the one "
        "term the clause scores. The same term is put to the four documented buildings "
        "the clause cites as its evidence. This adjudicates nothing: it is the "
        "measurement that decides whether the third remedy is even available."),
    "nothing_is_written_to": (
        "No verdict is rewritten, no recipe slot moves, no record or asset is touched "
        "and no confidence changes. These roofs are inferred_anonymous before and after. "
        "The six are NOT yet carried out — the recipe still stands them as A-family slots "
        "and nothing has been rebaked. That is T-1611."),
}


def build() -> dict:
    ledger = load(LEDGER)
    recipe = load(BLOCK_RECIPE)
    index = slot_index(recipe)

    roofs = []
    for verdict in outstanding(ledger):
        found = index.get(verdict["id"])
        if found is None:
            raise SystemExit(f"{verdict['id']}: the adjudication refamilies it and no "
                             f"slot in {BLOCK_RECIPE.name} builds it")
        block, slot, seq = found
        if slot["family"] != verdict["family"]:
            raise SystemExit(f"{verdict['id']}: the slot stands as {slot['family']}, "
                             f"not the {verdict['family']} the adjudication describes")
        held = principal_lots(block)
        lot = int(slot["lot"]) if "lot" in slot else None
        # T-1610. The position is the recipe's own: `stands_on` and the lot, against the
        # lots this same deal already stood a principal roof on. A caller passing no
        # position gets the group-only answer, which is what `families_offered` below asks
        # for — it is a question about the FAMILY, not about where this roof stands.
        to_class = inventory_class(
            verdict["to_family"], stands_on=slot.get("stands_on"),
            lot_carries_a_principal_roof=lot is not None and lot in held)
        offered = [{"family": f, "group": group_of(f),
                    "inventory_class": inventory_class(f)}
                   for f in verdict["families_offered"]]
        new_id = (f"{PREFIX}{block['block_id'].removeprefix('blk_')}"
                  f"_{verdict['to_family'].lower()}_{seq:02d}")
        refusal = None
        if to_class == "principal_functional" and lot is not None and lot in held:
            refusal = (f"{block['block_id']}: two principal roofs on one lot — lot "
                       f"{lot} already carries {held[lot]}")
        roofs.append({
            "id": verdict["id"], "would_become": new_id, "sequence": seq,
            "block_id": block["block_id"],
            "programme_phase": block["programme_phase"],
            "stands_on": slot["stands_on"], "lot": lot,
            "fronts": slot["fronts"], "setback_m": slot.get("setback_m"),
            "setback_class": "yard",
            "was_family": verdict["family"], "was_group": verdict["group"],
            "was_inventory_class": slot["inventory_class"],
            "to_family": verdict["to_family"], "to_group": verdict["to_group"],
            "implied_inventory_class": to_class,
            "class_moves": to_class != slot["inventory_class"],
            "lot_already_carries": held.get(lot),
            "refused_by_the_parcel_gate": refusal,
            "families_offered": offered,
            "ancillary_families_offered": sum(
                1 for row in offered if row["inventory_class"] == "ancillary"),
            "why_the_adjudication_refamilied_it": verdict["reason"],
        })

    blocks = {}
    for roof in roofs:
        entry = blocks.setdefault(roof["block_id"], {"roofs_needing_ground": 0,
                                                     "open_lots": []})
        entry["roofs_needing_ground"] += 1
    for block in recipe["blocks"]:
        if block["block_id"] not in blocks:
            continue
        for row in open_lots(block):
            entry = blocks[block["block_id"]]["open_lots"]
            if any(existing["lot"] == int(row["lot"]) for existing in entry):
                continue
            entry.append({"lot": int(row["lot"]), "declared_open_because": row["why"]})

    witness = witness_rows()
    breaching = [row for row in witness if row.get("breaches_its_own_clause")]
    streetless = [row for row in witness if row.get("fronts_no_street")]
    ground = sum(len(entry["open_lots"]) for entry in blocks.values())

    return {
        "$schema_note": "Derived. Re-derive with tools/measure_block_redeal_remedies.py "
                        "--build; tools/check.sh runs --check.",
        "id": "1835_block_redeal_remedies",
        "ticket": TICKET,
        "target_date": "1835",
        "generated_by": "tools/measure_block_redeal_remedies.py --build",
        "not_a_reading": "No page of any source is read here. This measures committed "
                         "files against each other and adjudicates nothing.",
        "inputs": [
            "data/reconstruction/1835_roof_redeal.json",
            "data/reconstruction/1835_platted_block_parcels.json",
            "data/reconstruction/1835_placement_policy.json",
        ],
        "method": METHOD,
        "counts": {
            "outstanding_verdicts": len(roofs),
            "refused_by_the_parcel_gate": sum(
                1 for r in roofs if r["refused_by_the_parcel_gate"]),
            "inventory_class_moves": sum(1 for r in roofs if r["class_moves"]),
            "families_offered": sum(len(r["families_offered"]) for r in roofs),
            "ancillary_families_offered": sum(
                r["ancillary_families_offered"] for r in roofs),
            "open_lots_across_the_three_blocks": ground,
            "clause_evidence_records": len(witness),
            "clause_evidence_breaching_their_own_clause": len(breaching),
            "clause_evidence_fronting_no_street": len(streetless),
        },
        "roofs": roofs,
        "ground": blocks,
        "clause_witness": {
            "clause": CLAUSE_ID,
            "scored_term": "class:principal in `avoids`, against the traffic class of "
                           "the street each record FRONTS — a record that fronts none "
                           "has no class and the term cannot speak for it (T-1511); "
                           "`the_policy_refuses_it` is the clause's whole answer, both "
                           "terms",
            "rows": witness,
            "clause_evidence_fronting_no_street": len(streetless),
            "reading": (
                f"{len(breaching)} of the {len(witness)} documented buildings this "
                f"clause cites as its evidence FRONTS a principal street, which "
                f"is the position the clause says it avoids and the one term the policy "
                f"scores. `wolf_point_tavern_stable` is an A1 standing 36.70 m from a "
                f"principal street; the roof now standing as "
                f"`recon_1835_blk_randolph_market_d4_07` WAS an A1 standing 29.28 m "
                f"from one, until T-1611 re-dealt it. The test that refamilies the second "
                f"refamilies the first. That is a question about the clause, and this "
                f"tool does not answer it."
                + (f" {len(streetless)} more front no street at all, out on the "
                   f"reservation beyond the census's frontage reach (T-1511): the "
                   f"scored term has no class to read for them, and the clause's own "
                   f"answer is printed beside it — it refuses "
                   f"{sum(1 for r in streetless if r['the_policy_refuses_it'])} of them "
                   f"on the `yard` setback it seats by, which is measured off a block "
                   f"alley this ground does not have." if streetless else "")),
        },
        "ruling": {
            "asked": "2026-09-23",
            "answered": "2026-09-23",
            "by": "the owner, on T-1482's question, via Manager's 4D board",
            "question": "Six roofs re-classed from yard building to dwelling would each "
                        "become a second main house on a lot that already has one. "
                        "Which way?",
            "answer": "(a) Treat a rear cottage as ancillary, so a lot may carry a main "
                      "house plus a rear dwelling",
            "carried_into": [
                "data/reconstruction/1835_placement_policy.json — the clause "
                "`rear_dwelling_behind_its_own_roof`, tier `inferred`, citing no record "
                "because the town holds none",
                "tools/reconcile_665.py — `inventory_class` reads the position as well "
                "as the group, and is the one derivation the generators deal by",
                "tools/generate_block_infill.py — the adoption gate asks the GROUP, so a "
                "rear cottage may house a household and a privy still may not",
            ],
            "what_it_does_not_do": "The six are not re-dealt. The recipe stands them as "
                                   "A-family slots, no id has moved and no mesh has been "
                                   "rebaked — T-1611 does that, and this report is what "
                                   "says it now can be.",
            "why_the_schedule_does_not_move": "Because the six stay ancillary, the "
                                              "blocks' principal-roof counts are "
                                              "unchanged, so `lot_ceiling_principal` and "
                                              "`block_rooms` are untouched. A promotion "
                                              "to principal would have breached both.",
        },
        "remedies": [
            {
                "id": "clause_a_dwelling_in_the_yard",
                "taken": True,
                "what": "Admit a dwelling-family roof at a yard setback behind its "
                        "lot's principal roof — a rear cottage — as ANCILLARY, and "
                        "write the clause that covers it.",
                "what_it_changes": "The town gains a building class it had never "
                                   "stated. `ancillary_behind_its_own_roof` applies to "
                                   "A1–A5 only, so a D-family roof in the yard was "
                                   "covered by no clause at all. The adoption gate had "
                                   "to be ruled on too: it refused an ancillary roof an "
                                   "occupant on the reasoning that a yard building is a "
                                   "shed, and a rear cottage is not one.",
                "costs": f"{len(roofs)} roofs keep their position; one new policy "
                         f"clause, tier `inferred` and citing no record; one ruling on "
                         f"adoption. TAKEN by the owner on 2026-09-23.",
            },
            {
                "id": "move_them_onto_open_ground",
                "taken": False,
                "what": "Deal the six onto free lots as principal roofs.",
                "what_it_changes": "The verdict's own sentence — `the slot is wanted "
                                   "and the position stands` — no longer holds, and the "
                                   "ground is not there: the three blocks hold "
                                   f"{ground} open lot(s) against {len(roofs)} roofs, "
                                   "and each of those lots is declared open in the "
                                   "recipe with a stated reason, carried into `ground` "
                                   "below. Taking one is overruling the programme's "
                                   "alternating-vacancy assumption, not finding space.",
                "costs": f"{len(roofs) - ground} roof(s) with nowhere to stand even "
                         f"after both open lots are spent.",
            },
            {
                "id": "leave_them_where_they_are",
                "taken": False,
                "what": "Let the six stand as the A-family yard buildings they are and "
                        "record the refusal against the adjudication.",
                "what_it_changes": "It re-opens T-1445's scoring for this clause, "
                                   "because the reason these six were refused refuses "
                                   f"{len(breaching)} of the clause's own "
                                   f"{len(witness)} evidence records too. That is the "
                                   "owner's call and not this tool's: a scored term "
                                   "that its own evidence breaches is either the wrong "
                                   "term or the wrong evidence.",
                "costs": "0 roofs move; the adjudication's block verdicts are withdrawn "
                         "and the clause is re-read.",
            },
        ],
    }


def render(doc: dict) -> str:
    return json.dumps(doc, indent=2, ensure_ascii=False) + "\n"


def render_markdown(doc: dict) -> str:
    """The same measurement, for a reader. Derived from the report, never beside it."""
    counts = doc["counts"]
    out = [
        "# The platted blocks' six refamily verdicts, and the clause that frees them "
        "— July 1835",
        "",
        f"DERIVED — regenerate with `tools/{Path(__file__).name} --build`. {TICKET}.",
        "",
        "T-1445 adjudicated 285 anonymous roofs and returned 32 refamily verdicts. "
        "T-1451 carried out the six whose ids do not move; T-1480 migrated the North "
        "Division's nine and T-1494 the phase-one South parcel's eleven. These six are "
        "the remainder, and the rename was never what stopped them.",
        "",
        "Each is an A-family yard building standing at a yard setback off its block "
        "alley, behind the principal roof on its own lot, and the adjudication moves "
        "every one into an `ordinary_dwellings` family. The inventory class was read off "
        "the GROUP alone, so a dwelling family came out `principal_functional` wherever "
        "it stood — and the parcel gate refuses a second principal roof on a lot that "
        "already carries one. All six were refused, and the committed "
        "`multi_building_lot` rule admits a second principal roof only on a "
        "principal-street lot in a party-line run of shared side walls; these six stand "
        "off the alley at the back.",
        "",
        f"**The owner ruled on {doc['ruling']['answered']}:** "
        f"{doc['ruling']['answer']}. That ruling is now "
        "`rear_dwelling_behind_its_own_roof` in the placement policy and a position in "
        "`reconcile_665.inventory_class`: off the alley, on a lot whose principal roof "
        "is already dealt, a dwelling is ANCILLARY. The same six verdicts re-derived "
        "against the same committed files are no longer refused, and because they stay "
        "ancillary the blocks' principal-roof counts do not move either.",
        "",
        f"**What is still not done:** {doc['ruling']['what_it_does_not_do']}",
        "",
        f"- outstanding verdicts: **{counts['outstanding_verdicts']}**",
        f"- refused by the parcel gate: **{counts['refused_by_the_parcel_gate']}**",
        f"- offered families that would leave the inventory class alone: "
        f"**{counts['ancillary_families_offered']}** of "
        f"{counts['families_offered']}",
        f"- open lots across the three blocks: "
        f"**{counts['open_lots_across_the_three_blocks']}**, against "
        f"{counts['outstanding_verdicts']} roofs",
        "",
        "## The six, and what refuses each one",
        "",
        "| roof | becomes | stands | was | now | the refusal |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for roof in doc["roofs"]:
        stands = (f"lot {roof['lot']}, off the {roof['stands_on']}, "
                  f"{roof['setback_m']} m")
        out.append(
            f"| `{roof['id']}` | `{roof['would_become']}` | {stands} | "
            f"{roof['was_family']} ({roof['was_inventory_class']}) | "
            f"{roof['to_family']} ({roof['implied_inventory_class']}) | "
            f"{roof['refused_by_the_parcel_gate']} |")
    out += [
        "",
        "Every one of the "
        f"{counts['families_offered']} families the adjudication offers across the six "
        "is an ordinary dwelling, so no offered family avoided the promotion by its "
        "letter alone. There was no re-deal inside the verdict, which is why the "
        "question had to go to the owner rather than being solved here.",
        "",
        "## The ground the other remedy would need",
        "",
        "| block | roofs needing a lot | open lots |",
        "| --- | ---: | ---: |",
    ]
    for block_id in sorted(doc["ground"]):
        entry = doc["ground"][block_id]
        out.append(f"| `{block_id}` | {entry['roofs_needing_ground']} | "
                   f"{len(entry['open_lots'])} |")
    out += [
        "",
        "And each of those open lots is declared open in the recipe with a stated "
        "reason — the programme's own alternating-vacancy assumption. Taking one is "
        "overruling that assumption, not finding space.",
        "",
        "## The clause, asked its own question",
        "",
        doc["clause_witness"]["reading"],
        "",
        "| evidence record | family | street it fronts | class | setback m | "
        "scored term | the clause refuses it |",
        "| --- | --- | --- | --- | ---: | --- | --- |",
    ]
    for row in doc["clause_witness"]["rows"]:
        if not row.get("standing_with_a_street"):
            out.append(f"| `{row['id']}` | — | — | — | — | — | "
                       f"not standing with a street |")
            continue
        term = ("cannot speak — it fronts none" if row["fronts_no_street"]
                else "yes" if row["breaches_its_own_clause"] else "no")
        setback = "—" if row["setback_m"] is None else f"{row['setback_m']:.2f}"
        out.append(f"| `{row['id']}` | {row['family']} | "
                   f"{row['street'] or '(none)'} | {row['street_class'] or '—'} | "
                   f"{setback} | {term} | "
                   f"{'yes' if row['the_policy_refuses_it'] else 'no'} |")
    out += ["", "## The three remedies, and what each one changes", "",
            "All three change what the town IS, so this tool costed them and asked "
            "rather than choosing. The owner answered on "
            f"{doc['ruling']['answered']}; the one he took is marked.", ""]
    for remedy in doc["remedies"]:
        taken = " — **TAKEN**" if remedy["taken"] else ""
        out += [f"### {remedy['what']}{taken}", "",
                remedy["what_it_changes"], "",
                f"**Costs:** {remedy['costs']}", ""]
    out += ["## Where the ruling lives", ""]
    out += [f"- {line}" for line in doc["ruling"]["carried_into"]]
    out += ["", doc["ruling"]["why_the_schedule_does_not_move"], ""]
    return "\n".join(out)


def check() -> int:
    if not REPORT.exists():
        print(f"DRIFT: {REPORT.relative_to(ROOT)} is missing — run --build")
        return 1
    doc = build()
    if REPORT.read_text(encoding="utf-8") != render(doc):
        print(f"DRIFT: {REPORT.relative_to(ROOT)} no longer re-derives from the "
              f"ledger, the block recipe and the placement policy")
        return 1
    if not DOC.exists() or DOC.read_text(encoding="utf-8") != render_markdown(doc):
        print(f"DRIFT: {DOC.relative_to(ROOT)} no longer re-derives from the report")
        return 1
    print(f"{doc['counts']['outstanding_verdicts']} outstanding platted-block verdict(s), "
          f"{doc['counts']['refused_by_the_parcel_gate']} refused by the parcel gate "
          f"(the rear-cottage clause freed them and T-1611 carried them out), "
          f"{doc['counts']['ancillary_families_offered']} of "
          f"{doc['counts']['families_offered']} offered families would have left the "
          f"class alone by their letter, "
          f"{doc['counts']['open_lots_across_the_three_blocks']} open lot(s) "
          f"against them")
    return 0


def self_test() -> int:
    failures = []

    def want(cond, msg):
        if not cond:
            failures.append(msg)

    want(inventory_class("A1") == "ancillary",
         "a stable is a yard building wherever it stands")
    want(inventory_class("A1", stands_on="street",
                        lot_carries_a_principal_roof=False) == "ancillary",
         "and a stable on the street line is still a stable — the group half of the "
         "derivation is not weakened by the position half")
    want(inventory_class("D4") == "principal_functional",
         "a dwelling family asked with no position is a principal roof, which is the "
         "answer the North Division's placement rows still get")

    # T-1610, the owner's ruling of 2026-09-23, put to the derivation in all four corners.
    # This is what the six verdicts turn on, so it is asserted here and not only measured.
    want(inventory_class("D4", stands_on="alley",
                        lot_carries_a_principal_roof=True) == "ancillary",
         "a dwelling off the alley behind its own lot's principal roof is a REAR COTTAGE "
         "and ancillary — the ruling itself")
    want(inventory_class("D4", stands_on="street",
                        lot_carries_a_principal_roof=True) == "principal_functional",
         "a house on the street line is not made ancillary by its lot being occupied; "
         "that case is the party-line run's, and it is the gate's business")
    want(inventory_class("D4", stands_on="alley",
                        lot_carries_a_principal_roof=False) == "principal_functional",
         "a dwelling off an alley with no principal roof in front of it is nobody's rear "
         "cottage — an ancillary roof serves the lot it is in the yard of")

    # A slot whose lot is free takes a principal roof without argument; the gate is a
    # statement about the LOT, not about refamilying.
    block = {"block_id": "blk_fixture", "programme_phase": "fixture",
             "slots": [{"family": "D5", "inventory_class": "principal_functional",
                        "lot": 0, "stands_on": "street", "fronts": "randolph"},
                       {"family": "A1", "inventory_class": "ancillary", "lot": 0,
                        "stands_on": "alley", "fronts": "randolph"},
                       {"family": "A3", "inventory_class": "ancillary", "lot": 4,
                        "stands_on": "alley", "fronts": "randolph"}]}
    held = principal_lots(block)
    want(held == {0: "recon_1835_blk_fixture_d5_01"},
         "the held lots are the principal roofs', and a yard building holds none")
    want(4 not in held, "a free lot is free")

    # A frontage run counts against every lot it was dealt, which is what makes the
    # second deal on blk_randolph_market a refusal as well.
    run = {"block_id": "blk_fixture", "programme_phase": "fixture", "slots": [],
           "frontage": {"lots": [1]}}
    want(1 in principal_lots(run),
         "a frontage run holds the lots it was dealt, so a yard building on one of "
         "them cannot be promoted either")

    # The id survives the refamily at its own sequence — the rename is the easy half.
    idx = slot_index({"blocks": [dict(block, slots=block["slots"])]})
    want("recon_1835_blk_fixture_a1_02" in idx,
         "a slot's sequence is its position in the deal")
    want(idx["recon_1835_blk_fixture_a1_02"][2] == 2,
         "and the sequence is what the refamilied id keeps")

    seq_started = slot_index({"blocks": [{"block_id": "blk_fixture", "seq_start": 9,
                                          "programme_phase": "fixture",
                                          "slots": [{"family": "A1", "lot": 1,
                                                     "inventory_class": "ancillary",
                                                     "stands_on": "alley",
                                                     "fronts": "washington"}]}]})
    want("recon_1835_blk_fixture_a1_09" in seq_started,
         "a second deal's sequence starts where the recipe says it does")

    # T-1610's two gates, proven by breaking them. The derivation above is only a rule
    # until something refuses a recipe that disagrees with it, and the whole worth of the
    # ruling to T-1611 is that the six can be re-dealt and CANNOT be field-edited.
    import generate_block_infill as gbi  # noqa: PLC0415

    cottage = {"block_id": "blk_fixture", "programme_phase": "fixture",
               "slots": [{"family": "D5", "inventory_class": "principal_functional",
                          "lot": 0, "stands_on": "street", "fronts": "randolph"},
                         {"family": "D2", "inventory_class": "ancillary", "lot": 0,
                          "stands_on": "alley", "fronts": "randolph"}]}
    try:
        gbi.check_slot_inventory_classes(cottage)
        want(True, "")
    except SystemExit as exc:
        want(False, f"a rear cottage dealt as ancillary is what T-1611 writes and the "
                    f"generator refused it: {exc}")

    field_edit = {"block_id": "blk_fixture", "programme_phase": "fixture",
                  "slots": [{"family": "D5", "inventory_class": "ancillary", "lot": 0,
                             "stands_on": "street", "fronts": "randolph"}]}
    try:
        gbi.check_slot_inventory_classes(field_edit)
        want(False, "a street-standing dwelling typed `ancillary` is a field edit and the "
                    "generator took it")
    except SystemExit:
        want(True, "")

    orphan = {"block_id": "blk_fixture", "programme_phase": "fixture",
              "slots": [{"family": "D2", "inventory_class": "ancillary", "lot": 4,
                         "stands_on": "alley", "fronts": "randolph"}]}
    try:
        gbi.check_slot_inventory_classes(orphan)
        want(False, "a dwelling off an alley with no principal roof in front of it is "
                    "nobody's rear cottage and cannot be called ancillary")
    except SystemExit:
        want(True, "")

    want(houses_a_household("D2") and houses_a_household("D5"),
         "a rear cottage may house a household — the ruling's point")
    want(not houses_a_household("A1") and not houses_a_household("A3"),
         "and a stable and a privy still may not, which is the reason the adoption gate "
         "was ever written")

    doc = load(REPORT) if REPORT.exists() else build()
    want(doc["counts"]["ancillary_families_offered"] == 0,
         "no offered family leaves the inventory class alone by its letter — that is "
         "what showed the re-deal had nowhere to go inside the verdict, and it is why "
         "the question went to the owner")
    want(doc["counts"]["refused_by_the_parcel_gate"] == 0,
         "not one outstanding verdict is refused any more: the rear-cottage clause is "
         "in force. If this comes back non-zero the ruling has been lost out of the "
         "policy or out of the derivation, and T-1611 cannot run")
    want(doc["counts"]["inventory_class_moves"] == 0,
         "and no class moves, which is why the blocks' principal-roof counts and "
         "`lot_ceiling_principal` are untouched by carrying the six out")
    want(doc["ruling"]["answer"].startswith("(a)"),
         "the report carries the owner's answer, not a summary of it")
    want(any(r["taken"] for r in doc["remedies"])
         and sum(1 for r in doc["remedies"] if r["taken"]) == 1,
         "exactly one remedy is marked taken — three costed options with none or two "
         "chosen is a report nobody can act on")

    for message in failures:
        print(f"  FAIL {message}")
    print(f"{20 - len(failures)} of 20 assertion(s) pass")
    return 1 if failures else 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    if args.check:
        return check()
    if args.build:
        doc = build()
        REPORT.write_text(render(doc), encoding="utf-8")
        DOC.write_text(render_markdown(doc), encoding="utf-8")
        print(f"wrote {REPORT.relative_to(ROOT)} and {DOC.relative_to(ROOT)}")
        return 0
    ap.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
