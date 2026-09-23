#!/usr/bin/env python3
"""WHY THE PLATTED BLOCKS' SIX REFAMILY VERDICTS CANNOT BE CARRIED OUT. T-1482.

    tools/measure_block_redeal_remedies.py --build      write the report
    tools/measure_block_redeal_remedies.py --check      re-derive and refuse drift
    tools/measure_block_redeal_remedies.py --self-test  the assertions, on fixtures

T-1445 adjudicated the town's 285 anonymous roofs and returned 32 refamily verdicts.
T-1451 carried out the six whose ids do not move; T-1480 and T-1494 migrated the North
Division's nine and the phase-one South parcel's eleven. THESE SIX ARE THE REMAINDER,
and this tool is the demonstration that they are not a migration at all --- the rename
is the easy half and it is not what stops them.

Every one of the six is an A-family yard building standing at a `yard` setback off its
block alley, behind the principal roof on its own lot. The adjudication moves each one
into an `ordinary_dwellings` family. `generate_block_infill` reads a roof's inventory
class from its group, so a dwelling family is `principal_functional` --- and the parcel
gate refuses a second principal roof on a lot that already carries one. The committed
`multi_building_lot` rule admits a second principal roof ONLY on a principal-street lot
in a party-line run of shared side walls; these six stand off the alley at the back.

So the ticket's own sentence is the finding: this is a re-deal of the block's mix and
not a field edit. What this tool adds is that THE RE-DEAL HAS NOWHERE TO GO. Every one
of the 36 families the adjudication offers across the six roofs is an ordinary dwelling,
so no offered family avoids the refusal; the three blocks hold two open lots between
them against six roofs needing ground, and both of those lots are declared open in the
recipe with a stated reason.

NOTHING IS ADJUDICATED HERE AND NOTHING IS MOVED. No verdict is rewritten, no family is
chosen, no confidence moves and no record is written to. The report states the three
remedies and what each one costs, measured off committed files, and the ticket is
blocked on the owner because all three change what the town IS.
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

# The same letter-to-group mapping the adjudication and the 665 ledger use, and the
# same ancillary groups the North Division's executor read a class out of. Imported
# rather than retyped: a class computed under a second opinion about which letter is
# a stable would not be the one the generator enforces.
from execute_roof_redeal import ANCILLARY_GROUPS  # noqa: E402
from reconcile_665 import group_of  # noqa: E402


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def inventory_class(family: str) -> str:
    return "ancillary" if group_of(family) in ANCILLARY_GROUPS else "principal_functional"


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

    `_breaches` scores `class:<the nearest street's traffic class>` against the
    clause's `avoids`. The clause avoids `class:principal`, so this asks the
    documented stables and barns it cites the question it asked the six roofs.
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
            "setback_m": round(float(row["setback_m"]), 2),
            "breaches_its_own_clause": f"class:{row['class']}" in clause["avoids"],
        })
    return rows


METHOD = {
    "the_class_is_read_off_the_group": (
        "`generate_block_infill` writes a roof's `inventory_class` from its slot, and "
        "the North Division's executor derives the class a refamily lands in from the "
        "group it joins: the two ancillary groups are barns_stables and "
        "small_outbuildings, everything else is principal_functional. Both are "
        "imported here rather than retyped."),
    "the_refusal_is_the_generator_s_own": (
        "The parcel gate collects the lots its principal roofs stand on — the frontage "
        "run counting against the lots it was dealt — and refuses the set holding a lot "
        "twice: `two principal roofs on one lot`. This tool asks that same question of "
        "each roof at its standing position, and names the roof already there."),
    "every_offered_family_is_asked": (
        "The adjudication ranks the families each roof could become. A remedy inside "
        "the verdict would be an offered family whose group is ancillary, so the class "
        "does not move; every one of them is asked and the count of ancillary offers "
        "is the answer."),
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
        "and no confidence changes. These roofs are inferred_anonymous before and after."),
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
        to_class = inventory_class(verdict["to_family"])
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
        },
        "roofs": roofs,
        "ground": blocks,
        "clause_witness": {
            "clause": CLAUSE_ID,
            "scored_term": "class:principal in `avoids`, against the traffic class of "
                           "the street each record stands nearest",
            "rows": witness,
            "reading": (
                f"{len(breaching)} of the {len(witness)} documented buildings this "
                f"clause cites as its evidence stand nearest a principal street, which "
                f"is the position the clause says it avoids and the one term the policy "
                f"scores. `wolf_point_tavern_stable` is an A1 standing 36.70 m from a "
                f"principal street; `recon_1835_blk_randolph_market_a1_07` is an A1 "
                f"standing 29.28 m from one. The test that refamilies the second "
                f"refamilies the first. That is a question about the clause, and this "
                f"tool does not answer it."),
        },
        "remedies": [
            {
                "id": "clause_a_dwelling_in_the_yard",
                "what": "Admit a dwelling-family roof at a yard setback behind its "
                        "lot's principal roof — a rear cottage — as ANCILLARY, and "
                        "write the clause that covers it.",
                "what_it_changes": "The town gains a building class it has never "
                                   "stated. `ancillary_behind_its_own_roof` applies to "
                                   "A1–A5 only, so a D-family roof in the yard is "
                                   "covered by no clause, and `refusals_of` returns a "
                                   "family with no clause as its own refusal. The "
                                   "adoption gate would also have to rule on whether "
                                   "such a roof may house anybody: it refuses an "
                                   "ancillary roof today on the reasoning that a yard "
                                   "building is a shed.",
                "costs": f"{len(roofs)} roofs keep their position; one new policy "
                         f"clause; one ruling on adoption.",
            },
            {
                "id": "move_them_onto_open_ground",
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
        "# The platted blocks' six refamily verdicts, and why none of them can be "
        "carried out — July 1835",
        "",
        f"DERIVED — regenerate with `tools/{Path(__file__).name} --build`. {TICKET}.",
        "",
        "T-1445 adjudicated 285 anonymous roofs and returned 32 refamily verdicts. "
        "T-1451 carried out the six whose ids do not move; T-1480 migrated the North "
        "Division's nine and T-1494 the phase-one South parcel's eleven. These six are "
        "the remainder, and the rename is the easy half of them — it is not what stops "
        "them.",
        "",
        "Each is an A-family yard building standing at a yard setback off its block "
        "alley, behind the principal roof on its own lot, and the adjudication moves "
        "every one into an `ordinary_dwellings` family. `generate_block_infill` reads a "
        "roof's inventory class from its group, so a dwelling family is "
        "`principal_functional` — and the parcel gate refuses a second principal roof "
        "on a lot that already carries one. The committed `multi_building_lot` rule "
        "admits a second principal roof only on a principal-street lot in a party-line "
        "run of shared side walls; these six stand off the alley at the back.",
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
        "is an ordinary dwelling, so no offered family avoids the promotion. There is "
        "no re-deal inside the verdict.",
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
        "| evidence record | family | nearest street | class | setback m | breaches "
        "its own clause |",
        "| --- | --- | --- | --- | ---: | --- |",
    ]
    for row in doc["clause_witness"]["rows"]:
        if not row.get("standing_with_a_street"):
            out.append(f"| `{row['id']}` | — | — | — | — | not standing with a street |")
            continue
        out.append(f"| `{row['id']}` | {row['family']} | {row['street']} | "
                   f"{row['street_class']} | {row['setback_m']:.2f} | "
                   f"{'yes' if row['breaches_its_own_clause'] else 'no'} |")
    out += ["", "## The three remedies, and what each one changes", ""]
    for remedy in doc["remedies"]:
        out += [f"### {remedy['what']}", "",
                remedy["what_it_changes"], "",
                f"**Costs:** {remedy['costs']}", ""]
    out += ["Blocked on the owner. All three change what the town IS, and this tool "
            "adjudicates nothing.", ""]
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
          f"{doc['counts']['refused_by_the_parcel_gate']} refused by the parcel gate, "
          f"{doc['counts']['ancillary_families_offered']} of "
          f"{doc['counts']['families_offered']} offered families would leave the class "
          f"alone, {doc['counts']['open_lots_across_the_three_blocks']} open lot(s) "
          f"against them")
    return 0


def self_test() -> int:
    failures = []

    def want(cond, msg):
        if not cond:
            failures.append(msg)

    want(inventory_class("A1") == "ancillary",
         "a stable is a yard building")
    want(inventory_class("D4") == "principal_functional",
         "a dwelling family is not a yard building, which is the whole difficulty")

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

    doc = load(REPORT) if REPORT.exists() else build()
    want(doc["counts"]["ancillary_families_offered"] == 0,
         "no offered family leaves the inventory class alone — if one ever does, the "
         "re-deal has somewhere to go and this report is out of date")
    want(doc["counts"]["refused_by_the_parcel_gate"]
         == doc["counts"]["outstanding_verdicts"],
         "every outstanding verdict is refused; a report that held a runnable one "
         "would be a ticket to run, not a question to ask")

    for message in failures:
        print(f"  FAIL {message}")
    print(f"{9 - len(failures)} of 9 assertion(s) pass")
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
