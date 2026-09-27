#!/usr/bin/env python3
"""THE KEEPER ON THE ROOF, NOT ONLY ON THE CARD.

T-1638, piece 1 of 4 of T-1200 — the South Water Street river front.

    tools/name_the_keepers_1835.py --build      write the keepers and the ledger
    tools/name_the_keepers_1835.py --check      re-derive both, refuse drift
    tools/name_the_keepers_1835.py --report     the keepers, the refusals, what is owed
    tools/name_the_keepers_1835.py --self-test  the guards, fired on the real data

## WHAT WAS MISSING

T-1613 dealt the committed plat to the town's banded households and T-1618 carried the
result onto the address book, so `data/reconstruction/1835_address_book.json` names, for
each of 108 households, the roof it was seated under. **The roof named nobody.** The link
existed in one direction only: open a South Water building in the walkthrough and its card
read `Anonymous count-unit toward the July 1835 665-roof programme`, while a file two
directories away said which household the placement policy had put in it. Twenty of those
seats are on the five South Water blocks, and this is the ticket that makes the card say so.

Nothing here is a reading and nothing here is new invention. The invention — WHICH
household takes WHICH lot — was made by the deal and is recorded as **L270**; what this
pass does is publish it where a visitor meets it, and **L276** carries that.

## THE RULING THAT REFUSES ELEVEN OF THE TWENTY

Eleven of the twenty South Water seats are households minted from the post office's letter
lists, and the owner's ruling of 2026-08-30 (T-0379) is explicit about that cohort: a
letter-list name is *a name the town knows, not a man with an address*. `tools/
mint_letter_list_residents.py --gate` holds it in two places — no `lives_at` on the card,
no structure record naming one of those people — for a stated reason: a later generator
that deals roofs by household could put seven hundred invented dwellings in the town off
the back of a post-office list, and nothing about the records would look wrong.

**So this pass refuses them, in writing, and does not route around the gate.** Writing the
household's NAME rather than its person id would slip past that gate's regular expression
and land exactly the claim the ruling forbids; the eleven are listed in the ledger with the
ruling that refuses them, and the deal's own seat for them is left standing untouched. That
disagreement between the deal and the ruling is not this pass's to settle — the deal seats
a letter-list household on a roof and the ruling says it may not have one — and it reaches
every district, not only this one. It is filed rather than papered over.

## WHAT A WRITTEN KEEPER SAYS, AND WHAT IT CAREFULLY DOES NOT

`occupants` is the prose a card shows, graded `reconstructed`, citing the sources that
carry the household's NAME and nothing further — no source places any of these households
anywhere, and each one's own address-book row says so. `resident_assignment` is the
machine-readable half: `status: assigned`, and `household_id`, which is the id
`data/residents/households/` holds.

**The id goes there and not into the prose, deliberately.**
`tools/generate_dooryard_pickets.py` admits a lot for a garden when a household id appears
in the `occupants` block, and a keeper a policy deal seats is not a measurement of anybody's
garden. Whether these lots should carry pickets is that generator's own question, on its own
evidence; this pass declines to answer it by side effect.

**And no mesh moves.** `generators/mesh_inputs.py` hashes the resolved archetype parameters
and the builder's bytes, not the record's prose, so a keeper costs no bake. The roof stays a
count-unit of the 665-roof programme, `inferred_anonymous`, with its existence, position and
footprint as conjectural as they were before anybody was named in it.

## WHICH WAY IT IS WRONG IF IT IS WRONG

Toward a town with too FEW keepers named. The scope is one district, the letter-list cohort
is refused rather than written, and a seat whose household carries no source even for its
name is refused too. Every one of those is counted and named, so the shortfall is readable
rather than implied.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
SEATS = DATA / "reconstruction" / "1835_platted_seats.json"
HOUSEHOLDS = DATA / "residents" / "households"
STRUCTURES = DATA / "structures"
LEDGER = DATA / "reconstruction" / "1835_roof_keepers.json"

TICKET = "T-1638"
PARENT = "T-1200"
TARGET_DATE = "1835-07-01"

# The districts this pass has been run for, as block-id prefixes. T-1200 builds the town
# one district at a time and hands the next on, so the scope is data and not a constant a
# reader has to trust: `--check` holds every seat OUTSIDE it as owed, by name.
DISTRICTS = {"south_water": "blk_south_water_"}

# The one generator this pass is wired through, by way of tools/inferred_occupancy.py. A
# seat on any other layer's roof is OWED rather than written, because a keeper the owning
# generator does not know about is drift on its next re-derivation and not a keeper at all.
BLOCK_INFILL_PREFIX = "recon_1835_blk_"

LETTER_LIST_REFUSAL = (
    "a household minted from the post office's letter lists, which the owner's ruling of "
    "2026-08-30 (T-0379) refuses a roof: a letter-list name is a name the town knows, not "
    "a man with an address. tools/mint_letter_list_residents.py --gate holds it. The "
    "placement policy's deal seated this household here anyway, and that disagreement is "
    "the deal's to answer, not this pass's to route around"
)

NO_SOURCE_REFUSAL = (
    "no source is carried for even this household's name, so there is nothing for the "
    "keeper attribute to cite and a card would state a name on this project's word alone"
)


class KeeperError(RuntimeError):
    """A keeper this pass cannot write honestly, or a tree that has stopped agreeing."""


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def dump(path: Path, doc: dict) -> None:
    path.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def occupants_note(seat: dict) -> str:
    return (
        "SEATED BY THE PLACEMENT POLICY'S PLATTED DEAL "
        "(data/reconstruction/1835_platted_seats.json, dealt by T-1613 and carried onto "
        f"this roof by {TICKET}; liberties L270 and L276). NO SOURCE PLACES THIS HOUSEHOLD "
        "HERE, OR ANYWHERE. Its own record gives a name and no address — no street, no lot "
        "and not even a division — so both halves of its band were dealt rather than read, "
        f"and the lot under this roof is the policy's {seat['policy_rule']} clause answered "
        f"on the committed plat: {seat['lot_id']}, fronting {seat['fronts']}, a standing "
        f"roof of family {seat['family']} the clause admits. THE SOURCES BELOW CARRY THE "
        "NAME AND NOTHING ELSE. The roof's own existence, position and footprint remain "
        "conjectural and are unchanged by the seating — it is still a count-unit of the "
        "665-roof programme, adopted rather than raised, so nothing was drawn off the "
        "reconstruction order book. The household's id is carried in resident_assignment "
        "rather than in this prose, because tools/generate_dooryard_pickets.py admits a lot "
        "for a garden on an id appearing HERE and a keeper a policy deal seats is not a "
        "measurement of anybody's garden."
    )


def assignment_note(seat: dict) -> str:
    return (
        f"{TICKET}: seated by the placement policy's platted deal under its "
        f"{seat['policy_rule']} clause, on {seat['lot_id']} fronting {seat['fronts']} — "
        f"a standing anonymous roof of family {seat['family']} "
        "this clause admits, adopted and not raised. WHICH household takes WHICH lot is "
        "this project's invention (L270); that the card now says so is L276. No source "
        "places this household on this lot, on this street, or in this division."
    )


def household_sources(doc: dict) -> list[str]:
    """Every source id the household's own people carry, for its NAME and nothing more."""
    out: set[str] = set()
    for person in doc.get("persons") or []:
        for sid in person.get("sources") or []:
            out.add(str(sid))
    return sorted(out)


def is_letter_list(doc: dict) -> bool:
    return any(person.get("letter_list_only") for person in doc.get("persons") or [])


def derive(scope: str) -> dict:
    """The ledger: every adopted seat written, refused or owed, and never dropped."""
    prefix = DISTRICTS[scope]
    seats = [s for s in load(SEATS)["seats"] if s.get("how") == "adopted"]
    written: list[dict] = []
    refused: list[dict] = []
    owed: list[dict] = []
    for seat in sorted(seats, key=lambda s: s["structure_id"]):
        row = {"household_id": seat["id"], "structure_id": seat["structure_id"],
               "block_id": seat["block_id"], "lot_id": seat["lot_id"],
               "clause": seat["policy_rule"], "family": seat["family"],
               "district": seat["district"]}
        card = HOUSEHOLDS / f"{seat['id']}.json"
        if not card.exists():
            raise KeeperError(f"{seat['id']} is seated on {seat['structure_id']} and "
                              f"data/residents/households/ does not hold it")
        doc = load(card)
        if is_letter_list(doc):
            refused.append({**row, "why": LETTER_LIST_REFUSAL})
            continue
        sources = household_sources(doc)
        if not sources:
            refused.append({**row, "why": NO_SOURCE_REFUSAL})
            continue
        if not (seat["block_id"] or "").startswith(prefix):
            owed.append({**row, "why": f"outside the district this pass has been run for "
                                       f"({scope}); T-1200's successors carry their own"})
            continue
        if not seat["structure_id"].startswith(BLOCK_INFILL_PREFIX):
            owed.append({**row, "why": "its roof is not one the platted block-infill "
                                       "generator owns, and this pass is only wired "
                                       "through that one"})
            continue
        written.append({
            **row, "name": doc["name"], "sources": sources,
            "occupants": {"value": doc["name"], "confidence": "reconstructed",
                          "sources": sources, "note": occupants_note(seat)},
            "resident_assignment": {"status": "assigned", "confidence": "reconstructed",
                                    "note": assignment_note(seat),
                                    "household_id": seat["id"]},
        })
    return {
        "$schema_note": "Derived. tools/name_the_keepers_1835.py --build writes it and "
                        "--check re-derives it; do not hand-edit.",
        "id": "1835_roof_keepers",
        "ticket": TICKET,
        "parent_ticket": PARENT,
        "target_date": TARGET_DATE,
        "generated_by": "tools/name_the_keepers_1835.py",
        "not_a_reading": "A publication of the platted deal (L270), not a reading of any "
                         "source. It seats nobody new, raises no roof and moves no mesh.",
        "raises_no_roof": "Every row here is an ADOPTION the deal already made. The "
                          "reconstruction order book is untouched and no GLB goes stale: "
                          "generators/mesh_inputs.py hashes archetype parameters, not prose.",
        "scope": {"district": scope, "block_prefix": prefix,
                  "districts_available": sorted(DISTRICTS)},
        "inputs": ["data/reconstruction/1835_platted_seats.json",
                   "data/residents/households/*.json"],
        "counts": {"adopted_seats": len(seats), "written": len(written),
                   "refused": len(refused), "owed": len(owed),
                   "refused_letter_list": sum(1 for r in refused
                                              if r["why"] == LETTER_LIST_REFUSAL),
                   "refused_no_source": sum(1 for r in refused
                                            if r["why"] == NO_SOURCE_REFUSAL)},
        "written": written,
        "refused": refused,
        "owed": owed,
    }


def keeper_fields(ledger: dict) -> dict[str, dict]:
    """What each written roof's two attributes must say, keyed on structure id.

    Read off the ledger and never recomposed, because the ledger is what
    `tools/inferred_occupancy.py` hands the generator — so this check and the generator
    are reading one statement rather than agreeing by coincidence.
    """
    return {row["structure_id"]: {"occupants": row["occupants"],
                                  "resident_assignment": row["resident_assignment"]}
            for row in ledger["written"]}


def build(scope: str) -> int:
    """Write the LEDGER. The records are the generator's to write, and that is the point.

    `data/structures/recon_1835_blk_*` is re-derived byte-for-byte from its block recipe
    on every commit, which is what makes those parcels trustworthy — so a keeper written
    into one by hand is drift, and `generate_block_infill.py --check` says so. The link is
    data, the arrangement the household programme and the street-face adoptions already
    use: this writes the ledger, `tools/inferred_occupancy.py` hands the two blocks to
    whichever generator owns the roof, and the record stays re-derivable. So after this,
    run `python3 tools/generate_block_infill.py`.
    """
    ledger = derive(scope)
    dump(LEDGER, ledger)
    c = ledger["counts"]
    print(f"wrote {LEDGER.relative_to(ROOT)}: {c['written']} keeper(s) named, "
          f"{c['refused']} refused, {c['owed']} owed")
    print("   now re-derive the roofs that carry them: "
          "python3 tools/generate_block_infill.py")
    return 0


def problems(ledger_on_disk: dict, scope: str) -> list[str]:
    """Every way the tree can have stopped agreeing with the deal it publishes."""
    found: list[str] = []
    want_ledger = derive(scope)
    if ledger_on_disk != want_ledger:
        found.append(f"{LEDGER.name} does not re-derive from the platted deal and the "
                     f"household cards — run --build")
    fields = keeper_fields(want_ledger)
    for structure_id, want in sorted(fields.items()):
        path = STRUCTURES / f"{structure_id}.json"
        if not path.exists():
            found.append(f"{structure_id}: named as a keeper's roof and no record holds it")
            continue
        record = load(path)
        for key, value in want.items():
            if record.get(key) != value:
                found.append(f"{structure_id}: {key} is not what the deal says it is")
    # Nobody may be named a keeper this pass did not write — the refused eleven above all,
    # because slipping one of those in is the whole failure the 2026-08-30 ruling names.
    allowed = set(fields)
    refused_or_owed = {row["structure_id"]: row
                       for row in want_ledger["refused"] + want_ledger["owed"]}
    for path in sorted(STRUCTURES.glob("*.json")):
        record = load(path)
        assignment = record.get("resident_assignment") or {}
        held = assignment.get("household_id")
        if not held:
            continue
        if record["id"] not in allowed:
            why = (refused_or_owed.get(record["id"]) or {}).get("why", "no seat of the "
                                                                     "platted deal")
            found.append(f"{record['id']}: carries a keeper this pass did not write — {why}")
        elif held != fields[record["id"]]["resident_assignment"]["household_id"]:
            found.append(f"{record['id']}: carries a different household than the deal seats")
    return found


def check(scope: str) -> int:
    if not LEDGER.exists():
        print(f"FAIL: {LEDGER.relative_to(ROOT)} is missing — run --build")
        return 1
    found = problems(load(LEDGER), scope)
    if found:
        print(f"FAIL: {len(found)} problem(s)")
        for line in found:
            print(f"   {line}")
        return 1
    ledger = load(LEDGER)
    c = ledger["counts"]
    print(f"OK: {c['written']} South Water roof(s) name the keeper the platted deal seated "
          f"there, {c['refused']} refused in writing and {c['owed']} owed to T-1200's "
          f"successors")
    return 0


def report(scope: str) -> int:
    ledger = derive(scope)
    print(f"THE KEEPERS ON THE ROOFS — {scope}, {ledger['counts']['adopted_seats']} "
          f"adopted seat(s) in the platted deal\n")
    print(f"WRITTEN ({len(ledger['written'])}):")
    for row in ledger["written"]:
        print(f"   {row['structure_id']:<48} {row['family']:<3} {row['name'][:52]}")
    print(f"\nREFUSED ({len(ledger['refused'])}) — counted by reason:")
    for why, label in ((LETTER_LIST_REFUSAL, "the letter-list ruling of 2026-08-30"),
                       (NO_SOURCE_REFUSAL, "no source for the name")):
        rows = [r for r in ledger["refused"] if r["why"] == why]
        print(f"   {len(rows):>4}  {label}")
        for row in rows[:6]:
            print(f"         {row['household_id']:<26} {row['structure_id']}")
        if len(rows) > 6:
            print(f"         … and {len(rows) - 6} more")
    print(f"\nOWED ({len(ledger['owed'])}): seats outside {scope}, carried by T-1200's "
          f"successors T-1201 … T-1208")
    return 0


def self_test(scope: str) -> int:
    """Break each assertion on a copy of the ledger and require --check to name it."""
    ledger = load(LEDGER)
    if problems(ledger, scope):
        print("   the committed tree does not pass its own check; fix that first")
        return 1
    cases = []

    def drop_a_keeper(doc: dict) -> dict:
        doc["written"] = doc["written"][1:]
        return doc

    def rename_a_keeper(doc: dict) -> dict:
        doc["written"][0]["occupants"]["value"] = "The Somebody household"
        return doc

    def move_a_keeper(doc: dict) -> dict:
        doc["written"][0]["resident_assignment"]["household_id"] = "hh_not_a_household"
        return doc

    def miscount(doc: dict) -> dict:
        doc["counts"]["refused"] = 0
        return doc

    def unrefuse_the_letter_lists(doc: dict) -> dict:
        doc["refused"] = [r for r in doc["refused"] if r["why"] != LETTER_LIST_REFUSAL]
        return doc

    cases = [("a named keeper goes missing", drop_a_keeper),
             ("a keeper's name is changed", rename_a_keeper),
             ("a keeper's household is changed", move_a_keeper),
             ("the counts stop counting", miscount),
             ("the letter-list refusals are quietly dropped", unrefuse_the_letter_lists)]
    failures = 0
    for label, break_it in cases:
        broken = break_it(json.loads(json.dumps(ledger)))
        if not problems(broken, scope):
            print(f"   NOT CAUGHT: {label}")
            failures += 1
    if failures:
        return 1
    print(f"   OK: all {len(cases)} of the check's assertions fire when broken")
    return 0


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--district", default="south_water", choices=sorted(DISTRICTS))
    args = ap.parse_args(argv)
    try:
        if args.build:
            return build(args.district)
        if args.check:
            return check(args.district)
        if args.report:
            return report(args.district)
        if args.self_test:
            return self_test(args.district)
    except KeeperError as exc:
        print(f"FAIL: {exc}")
        return 1
    ap.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
