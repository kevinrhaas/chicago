#!/usr/bin/env python3
"""THE KEEPER ON THE ROOF, NOT ONLY ON THE CARD.

T-1638, piece 1 of 4 of T-1200 — the South Water Street river front.
T-1685, piece 1 of 4 of T-1202 — the Randolph–Washington tier. One pass, one ledger, a
district added to `DISTRICTS` and `RUN_FOR` each time a build ticket reaches one.

    tools/name_the_keepers_1835.py --build      write the keepers and the ledger
    tools/name_the_keepers_1835.py --report --districts randolph    one district's rows
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

### AND SINCE T-1675 THE ROOF SAYS SO TOO

The refusal was filed in the ledger and nowhere on the roof, so eleven South Water records
stood with no `resident_assignment` at all — which is exactly what an unseated count-unit
looks like. A reader of the tree could not tell *the deal reached this roof and a ruling
stopped it* from *the deal never reached this roof*, and T-1641 counted them as eleven
dwellings standing with no household, which is true and is not the whole truth. Each of
those roofs now carries `resident_assignment` with `status: unassigned` and a note that
says which of the two it is — **naming no household**, for the reason below.

It also carries the number that decides whether the refusal is a shortage. `households_left`
counts, per clause and division, the deal's own OWED households that neither refusal here
rejects: 14 for `labourer_dwellings`, 143 for `tradesman_dwellings` and 105 for
`merchant_and_professional_dwellings` in the south division when it was first measured. So
none of the eleven is an empty cottage for want of people — every one is a roof the deal
could seat if it consulted this ruling before dealing, and that it does not is the finding.
It is filed as its own ticket rather than fixed here, because the deal reaches every
district and a re-deal is not one district's pass to make.

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

Toward a town with too FEW keepers named. The scope is the districts the build tickets have
actually reached, the letter-list cohort is refused rather than written, and a seat whose
household carries no source even for its name is refused too. Every one of those is counted
and named, so the shortfall is readable rather than implied.
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

TARGET_DATE = "1835-07-01"

# The districts this pass has been run for, as block-id prefixes, each with the ticket
# that ran it. T-1200 and its successors build the town one district at a time and hand
# the next on, so the scope is data and not a constant a reader has to trust: `--check`
# holds every seat OUTSIDE it as owed, by name.
#
# **The ticket rides on the district and not on the module** (T-1685). Every note this
# pass writes names the ticket that carried the keeper onto the roof, and a second
# district running through the same code does not make T-1638 the author of its prose.
# `says_why` is the ticket that made a REFUSED roof say so on the record: for South Water
# that was the follow-up T-1675, months after T-1638 wrote the keepers; for every district
# since, the refusals are said on the roof from the first pass, so it is the pass's own.
DISTRICTS = {
    "south_water": {"prefix": "blk_south_water_", "ticket": "T-1638",
                    "parent": "T-1200", "says_why": "T-1675"},
    "randolph": {"prefix": "blk_randolph_", "ticket": "T-1685",
                 "parent": "T-1202", "says_why": "T-1685"},
}

# The order the passes have been run in, which is the order the ledger states them in.
RUN_FOR = ("south_water", "randolph")

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

# T-1685, and it is A DISAGREEMENT THIS PASS FILES RATHER THAN A RULING IT APPLIES.
# `is_letter_list` reads the PERSON's flag, and `tools/mint_letter_list_residents.py`
# clears that flag — correctly, and with a gate of its own behind it — the moment a
# person carrying it turns up in a press reading that is not a letter list: "a person
# carrying BOTH may not carry the flag". What it does not do is revise the HOUSEHOLD's
# name, which was minted when the letter list was all there was. Seven cards stand with
# the two halves disagreeing, and one of them, hh_bradford_harriet, is seated by the
# platted deal on a Randolph roof. Writing it would put the sentence "The Bradford
# household — a name from the post office's letter lists" on a building card in a town
# whose ruling of 2026-08-30 says a letter-list name is not a man with an address; NOT
# writing it costs one keeper of sixteen. So the roof is refused, the disagreement is
# named on it, and the stale naming is filed as its own ticket rather than fixed in
# passing — it reaches 7 cards town-wide and every reader of their names, which is not
# one district's pass to make.
#
# T-1689 made that revision at its source: the mint now renames a card in the same step
# that refuses its flag, and its `--gate` holds the name and the flag together on every
# card it minted. So this refusal class is EMPTY by construction, and the two roofs it
# held are written like any other keeper. The test stays as a defence in case the gate
# is ever bypassed; its self-test case went with the last row it could exercise.
LETTER_LIST_NAME = "a name from the post office's letter lists"

NAME_DISAGREES_REFUSAL = (
    "this household's own name still says it is “a name from the post office's letter "
    "lists” while no person on its card carries letter_list_only — the flag having been "
    "cleared, correctly, because a press reading that is not a letter list stands beside "
    "it. So one record makes two statements about which evidence its name rests on, and "
    "the owner's ruling of 2026-08-30 (T-0379) turns on exactly that question. This pass "
    "publishes neither statement onto a roof until one of them is withdrawn; the stale "
    "naming is tools/mint_letter_list_residents.py's to revise and is filed as T-1689"
)


class KeeperError(RuntimeError):
    """A keeper this pass cannot write honestly, or a tree that has stopped agreeing."""


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def dump(path: Path, doc: dict) -> None:
    path.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def occupants_note(seat: dict, ticket: str) -> str:
    return (
        "SEATED BY THE PLACEMENT POLICY'S PLATTED DEAL "
        "(data/reconstruction/1835_platted_seats.json, dealt by T-1613 and carried onto "
        f"this roof by {ticket}; liberties L270 and L276). NO SOURCE PLACES THIS HOUSEHOLD "
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


def assignment_note(seat: dict, ticket: str) -> str:
    return (
        f"{ticket}: seated by the placement policy's platted deal under its "
        f"{seat['policy_rule']} clause, on {seat['lot_id']} fronting {seat['fronts']} — "
        f"a standing anonymous roof of family {seat['family']} "
        "this clause admits, adopted and not raised. WHICH household takes WHICH lot is "
        "this project's invention (L270); that the card now says so is L276. No source "
        "places this household on this lot, on this street, or in this division."
    )


def refusal_note(seat: dict, why: str, left: int, ticket: str, says_why: str) -> str:
    """What a roof says when the deal seated somebody on it and a ruling refuses them.

    T-1675. The eleven South Water roofs this pass refused stood with `resident_assignment`
    ABSENT, which reads as a roof nobody was ever dealt — the same silence an unseated
    count-unit keeps. The refusal was in the ledger and nowhere on the roof, so a reader of
    the record could not tell "the deal reached this roof and a ruling stopped it" from
    "the deal never reached this roof". It now says which.

    **It names no household.** The refusal is the letter-list ruling's, and writing the
    household's id or name onto a structure record is the one thing that ruling forbids —
    `tools/mint_letter_list_residents.py --gate` matches a letter-list person id in any
    structure record, and a name would slip the same claim past the regular expression. The
    seat the refusal answers is named in the ledger, which is not a structure record and
    already holds it. So this note points there rather than restating it.
    """
    return (
        f"NO KEEPER, AND NOT FOR WANT OF ONE ({says_why}). The placement policy's "
        f"platted deal seated a household on this roof under its {seat['policy_rule']} "
        f"clause, on {seat['lot_id']} — a standing anonymous roof of family "
        f"{seat['family']} that clause admits — and {ticket} refused to carry it onto "
        f"the record: {why}. "
        "The seat still stands in data/reconstruction/1835_platted_seats.json and the "
        "refusal in data/reconstruction/1835_roof_keepers.json § refused, which names the "
        "household; this note deliberately does not, because naming it here is the claim "
        "the ruling forbids. WHETHER THAT IS A SHORTAGE, MEASURED: "
        f"{left} unseated household(s) of this same clause and division carry a source for "
        "their name and are refused a roof by no ruling "
        "(1835_roof_keepers.json § households_left, re-derived from the deal's own owed "
        "rows on every commit). "
        + ("So the roof stands empty because the deal does not consult the ruling before "
           "it deals, not because the town ran out of people. " if left else
           "So the town really has run out of people this clause may seat here, and an "
           "empty cottage on this lot is the honest answer rather than a gap. ") +
        "The roof itself is unchanged: a conjectural count-unit of the 665-roof programme, "
        "adopted by nobody, its existence, position and footprint as invented as before."
    )


def households_left(seats_doc: dict, refused: list[dict]) -> list[dict]:
    """Per clause and division, the households a refusal did NOT exhaust.

    THIS IS THE NUMBER T-1675 ASKS FOR, and it is measured rather than asserted: for each
    (clause, division) a refused seat stands in, how many of the deal's OWED rows that same
    clause admits are households neither refusal above would reject — not minted from the
    letter lists, and carrying a source for their name. A zero here would mean the honest
    answer really is an empty cottage; anything else means the roof is seatable and the
    deal's order is what put a refused household on it.
    """
    wanted = sorted({(row["clause"], row["district"]) for row in refused})
    out: list[dict] = []
    for clause, district in wanted:
        eligible = 0
        for owed in seats_doc.get("owed") or []:
            if owed.get("clause") != clause or owed.get("district") != district:
                continue
            card = HOUSEHOLDS / f"{owed['id']}.json"
            if not card.exists():
                continue
            doc = load(card)
            if (is_letter_list(doc) or name_disagrees(doc)
                    or not household_sources(doc)):
                continue
            eligible += 1
        out.append({
            "clause": clause, "district": district, "households_left": eligible,
            "means": ("the deal's own owed rows of this clause and division whose "
                      "households neither the letter-list ruling nor the no-source "
                      "refusal rejects — so a roof refused here could be seated by one of "
                      "them if the deal consulted the ruling before it dealt")
            if eligible else
                     ("no unseated household of this clause and division survives both "
                      "refusals, so an empty roof here is the honest answer"),
        })
    return out


def household_sources(doc: dict) -> list[str]:
    """Every source id the household's own people carry, for its NAME and nothing more."""
    out: set[str] = set()
    for person in doc.get("persons") or []:
        for sid in person.get("sources") or []:
            out.add(str(sid))
    return sorted(out)


def is_letter_list(doc: dict) -> bool:
    return any(person.get("letter_list_only") for person in doc.get("persons") or [])


def name_disagrees(doc: dict) -> bool:
    """The card's NAME says letter list and its person's flag does not (T-1685)."""
    return LETTER_LIST_NAME in (doc.get("name") or "") and not is_letter_list(doc)


def district_of(seat: dict, scopes: tuple[str, ...]) -> str | None:
    """Which run-for district's pass owns this seat's block, or None if none does.

    T-1685. The scope became plural the moment a second district ran, and the district
    is what decides whose ticket the roof's prose names — so the lookup is one function
    both the writing and the refusing side ask, rather than a prefix test repeated.
    """
    block = seat["block_id"] or ""
    for scope in scopes:
        if block.startswith(DISTRICTS[scope]["prefix"]):
            return scope
    return None


def derive(scopes: tuple[str, ...]) -> dict:
    """The ledger: every adopted seat written, refused or owed, and never dropped."""
    seats_doc = load(SEATS)
    seats = [s for s in seats_doc["seats"] if s.get("how") == "adopted"]
    written: list[dict] = []
    refused: list[dict] = []
    owed: list[dict] = []
    # T-1675. A refusal is written onto the roof only where this pass OWNS the roof — the
    # same two tests a written keeper passes, because the record is re-derived by the
    # block-infill generator and a note on a roof that generator does not own is drift.
    # A refusal outside them is still filed here, and still says nothing on a card.
    def ours(seat: dict) -> bool:
        return (district_of(seat, scopes) is not None
                and seat["structure_id"].startswith(BLOCK_INFILL_PREFIX))

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
            refused.append({**row, "why": LETTER_LIST_REFUSAL, "on_the_card": ours(seat)})
            continue
        if name_disagrees(doc):
            refused.append({**row, "why": NAME_DISAGREES_REFUSAL,
                            "on_the_card": ours(seat)})
            continue
        sources = household_sources(doc)
        if not sources:
            refused.append({**row, "why": NO_SOURCE_REFUSAL, "on_the_card": ours(seat)})
            continue
        scope = district_of(seat, scopes)
        if scope is None:
            owed.append({**row, "why": f"outside the districts this pass has been run for "
                                       f"({', '.join(scopes)}); T-1200's successors carry "
                                       f"their own"})
            continue
        if not seat["structure_id"].startswith(BLOCK_INFILL_PREFIX):
            owed.append({**row, "why": "its roof is not one the platted block-infill "
                                       "generator owns, and this pass is only wired "
                                       "through that one"})
            continue
        ticket = DISTRICTS[scope]["ticket"]
        written.append({
            **row, "name": doc["name"], "sources": sources,
            "occupants": {"value": doc["name"], "confidence": "reconstructed",
                          "sources": sources, "note": occupants_note(seat, ticket)},
            "resident_assignment": {"status": "assigned", "confidence": "reconstructed",
                                    "note": assignment_note(seat, ticket),
                                    "household_id": seat["id"]},
        })

    # T-1675, and the order matters: the count is measured first, then spent in the notes,
    # so the number a roof states and the number the ledger publishes are one reading.
    on_the_card = [row for row in refused if row["on_the_card"]]
    left = households_left(seats_doc, on_the_card)
    left_by_band = {(row["clause"], row["district"]): row["households_left"]
                    for row in left}
    seat_by_roof = {seat["structure_id"]: seat for seat in seats}
    for row in on_the_card:
        seat = seat_by_roof[row["structure_id"]]
        scope = district_of(seat, scopes)
        row["resident_assignment"] = {
            "status": "unassigned", "confidence": "reconstructed",
            "note": refusal_note(seat, row["why"],
                                 left_by_band[(row["clause"], row["district"])],
                                 DISTRICTS[scope]["ticket"],
                                 DISTRICTS[scope]["says_why"]),
        }
    return {
        "$schema_note": "Derived. tools/name_the_keepers_1835.py --build writes it and "
                        "--check re-derives it; do not hand-edit.",
        "id": "1835_roof_keepers",
        "passes": [{"district": scope, "block_prefix": DISTRICTS[scope]["prefix"],
                    "ticket": DISTRICTS[scope]["ticket"],
                    "parent_ticket": DISTRICTS[scope]["parent"],
                    "refusals_said_on_the_roof_by": DISTRICTS[scope]["says_why"]}
                   for scope in scopes],
        "target_date": TARGET_DATE,
        "generated_by": "tools/name_the_keepers_1835.py",
        "not_a_reading": "A publication of the platted deal (L270), not a reading of any "
                         "source. It seats nobody new, raises no roof and moves no mesh.",
        "raises_no_roof": "Every row here is an ADOPTION the deal already made. The "
                          "reconstruction order book is untouched and no GLB goes stale: "
                          "generators/mesh_inputs.py hashes archetype parameters, not prose.",
        "scope": {"districts": list(scopes),
                  "block_prefixes": [DISTRICTS[scope]["prefix"] for scope in scopes],
                  "districts_available": sorted(DISTRICTS)},
        "inputs": ["data/reconstruction/1835_platted_seats.json",
                   "data/residents/households/*.json"],
        "counts": {"adopted_seats": len(seats), "written": len(written),
                   "refused": len(refused), "owed": len(owed),
                   "refused_letter_list": sum(1 for r in refused
                                              if r["why"] == LETTER_LIST_REFUSAL),
                   "refused_no_source": sum(1 for r in refused
                                            if r["why"] == NO_SOURCE_REFUSAL),
                   "refused_name_disagrees": sum(1 for r in refused
                                                 if r["why"] == NAME_DISAGREES_REFUSAL),
                   "refused_on_the_card": len(on_the_card),
                   "refused_with_a_household_left": sum(
                       1 for r in on_the_card
                       if left_by_band[(r["clause"], r["district"])])},
        "written": written,
        "refused": refused,
        "households_left": left,
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


def refusal_fields(ledger: dict) -> dict[str, dict]:
    """What each REFUSED roof this pass owns must say, keyed on structure id (T-1675).

    The same shape and the same source of truth as `keeper_fields`: read off the ledger,
    never recomposed, so the check and the generator read one statement. A refused roof
    carries `resident_assignment` and nothing else — no `occupants`, because there is no
    keeper to write prose about, and no `household_id`, because that is the claim the
    letter-list ruling forbids and the deal's own `adoptable()` reads it to reserve a roof.
    """
    return {row["structure_id"]: {"resident_assignment": row["resident_assignment"]}
            for row in ledger["refused"] if row.get("on_the_card")}


def build(scopes: tuple[str, ...]) -> int:
    """Write the LEDGER. The records are the generator's to write, and that is the point.

    `data/structures/recon_1835_blk_*` is re-derived byte-for-byte from its block recipe
    on every commit, which is what makes those parcels trustworthy — so a keeper written
    into one by hand is drift, and `generate_block_infill.py --check` says so. The link is
    data, the arrangement the household programme and the street-face adoptions already
    use: this writes the ledger, `tools/inferred_occupancy.py` hands the two blocks to
    whichever generator owns the roof, and the record stays re-derivable. So after this,
    run `python3 tools/generate_block_infill.py`.
    """
    ledger = derive(scopes)
    dump(LEDGER, ledger)
    c = ledger["counts"]
    print(f"wrote {LEDGER.relative_to(ROOT)}: {c['written']} keeper(s) named, "
          f"{c['refused']} refused ({c['refused_on_the_card']} of them said on the roof, "
          f"{c['refused_with_a_household_left']} with a household still left for it), "
          f"{c['owed']} owed")
    print("   now re-derive the roofs that carry them: "
          "python3 tools/generate_block_infill.py")
    return 0


def problems(ledger_on_disk: dict, scopes: tuple[str, ...]) -> list[str]:
    """Every way the tree can have stopped agreeing with the deal it publishes."""
    found: list[str] = []
    want_ledger = derive(scopes)
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
    # T-1675. A REFUSED roof this pass owns says so on the record, or it reads like a roof
    # the deal never reached. Both halves are faults: a missing block and a block that has
    # stopped saying what the ledger says.
    for structure_id, want in sorted(refusal_fields(want_ledger).items()):
        path = STRUCTURES / f"{structure_id}.json"
        if not path.exists():
            found.append(f"{structure_id}: named as a refused seat's roof and no record "
                         f"holds it")
            continue
        record = load(path)
        block = record.get("resident_assignment")
        if not block:
            found.append(f"{structure_id}: the deal seated a household here and this pass "
                         f"refused it, and the record says nothing — run --build, then "
                         f"python3 tools/generate_block_infill.py")
        elif block != want["resident_assignment"]:
            found.append(f"{structure_id}: resident_assignment is not the refusal the "
                         f"ledger states")
        elif record.get("occupants"):
            found.append(f"{structure_id}: a refused seat's roof carries occupants prose, "
                         f"which is a keeper the ruling refuses and which the deal reads "
                         f"as a rival claim and holds the roof back for")
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


def check(scopes: tuple[str, ...]) -> int:
    if not LEDGER.exists():
        print(f"FAIL: {LEDGER.relative_to(ROOT)} is missing — run --build")
        return 1
    found = problems(load(LEDGER), scopes)
    if found:
        print(f"FAIL: {len(found)} problem(s)")
        for line in found:
            print(f"   {line}")
        return 1
    ledger = load(LEDGER)
    c = ledger["counts"]
    print(f"OK: {c['written']} roof(s) across {', '.join(ledger['scope']['districts'])} "
          f"name the keeper the platted deal seated there, {c['refused']} refused in "
          f"writing and {c['owed']} owed to T-1200's successors")
    return 0


def report(scopes: tuple[str, ...]) -> int:
    ledger = derive(scopes)
    print(f"THE KEEPERS ON THE ROOFS — {', '.join(scopes)}, "
          f"{ledger['counts']['adopted_seats']} adopted seat(s) in the platted deal\n")
    print(f"WRITTEN ({len(ledger['written'])}):")
    for row in ledger["written"]:
        print(f"   {row['structure_id']:<48} {row['family']:<3} {row['name'][:52]}")
    print(f"\nREFUSED ({len(ledger['refused'])}) — counted by reason:")
    for why, label in ((LETTER_LIST_REFUSAL, "the letter-list ruling of 2026-08-30"),
                       (NO_SOURCE_REFUSAL, "no source for the name"),
                       (NAME_DISAGREES_REFUSAL,
                        "the card's name and its flag disagree (T-1689)")):
        rows = [r for r in ledger["refused"] if r["why"] == why]
        print(f"   {len(rows):>4}  {label}")
        for row in rows[:6]:
            print(f"         {row['household_id']:<26} {row['structure_id']}")
        if len(rows) > 6:
            print(f"         … and {len(rows) - 6} more")
    print(f"\nHOUSEHOLDS LEFT for the {ledger['counts']['refused_on_the_card']} refusal(s) "
          f"this pass wrote onto a roof — is the refusal a shortage?")
    for row in ledger["households_left"]:
        verdict = "NOT a shortage" if row["households_left"] else "genuinely exhausted"
        print(f"   {row['clause']:<38} {row['district']:<6} "
              f"{row['households_left']:>5} left   {verdict}")
    print(f"\nOWED ({len(ledger['owed'])}): seats outside {', '.join(scopes)}, carried by "
          f"T-1200's successors T-1201 … T-1208")
    return 0


def self_test(scopes: tuple[str, ...]) -> int:
    """Break each assertion on a copy of the ledger and require --check to name it."""
    ledger = load(LEDGER)
    if problems(ledger, scopes):
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

    def silence_a_refusal(doc: dict) -> dict:
        for row in doc["refused"]:
            if row.get("on_the_card"):
                row.pop("resident_assignment", None)
                row["on_the_card"] = False
                break
        return doc

    def restate_a_refusal(doc: dict) -> dict:
        for row in doc["refused"]:
            if row.get("on_the_card"):
                row["resident_assignment"]["note"] = "No keeper."
                break
        return doc

    def name_the_refused_household(doc: dict) -> dict:
        for row in doc["refused"]:
            if row.get("on_the_card"):
                row["resident_assignment"]["household_id"] = row["household_id"]
                break
        return doc

    def fake_the_headroom(doc: dict) -> dict:
        for row in doc["households_left"]:
            row["households_left"] = 0
        return doc

    cases = [("a refusal stops saying so on the roof", silence_a_refusal),
             ("a refusal's reason is rewritten", restate_a_refusal),
             ("a refused roof is made to name its household", name_the_refused_household),
             ("the households left are typed rather than counted", fake_the_headroom),
             ("a named keeper goes missing", drop_a_keeper),
             ("a keeper's name is changed", rename_a_keeper),
             ("a keeper's household is changed", move_a_keeper),
             ("the counts stop counting", miscount),
             ("the letter-list refusals are quietly dropped", unrefuse_the_letter_lists)]
    failures = 0
    for label, break_it in cases:
        broken = break_it(json.loads(json.dumps(ledger)))
        # T-1685. A CASE THAT CHANGES NOTHING PROVES NOTHING. Every one of these breaks
        # a row of a particular kind, and a ledger that happens to hold none of that kind
        # would let the case pass by mutating nothing at all — which reads as a green
        # assertion and is the absence of one. So a no-op mutation is a failure in its own
        # right, and it says so rather than being counted as caught.
        if broken == ledger:
            print(f"   NOT EXERCISED: {label} — the committed ledger holds no row of "
                  f"that kind, so this case asserts nothing")
            failures += 1
            continue
        if not problems(broken, scopes):
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
    # T-1685. Plural, and defaulting to every district the pass HAS been run for, so
    # `--check` in check.sh holds the whole published ledger rather than one district of
    # it. Naming a subset is for reading a single district's report, never for building.
    ap.add_argument("--districts", nargs="+", default=list(RUN_FOR),
                    choices=sorted(DISTRICTS))
    args = ap.parse_args(argv)
    scopes = tuple(d for d in RUN_FOR if d in set(args.districts))
    try:
        if args.build:
            return build(scopes)
        if args.check:
            return check(scopes)
        if args.report:
            return report(scopes)
        if args.self_test:
            return self_test(scopes)
    except KeeperError as exc:
        print(f"FAIL: {exc}")
        return 1
    ap.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
