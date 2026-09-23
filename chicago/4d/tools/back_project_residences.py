#!/usr/bin/env python3
"""Position an 1835 HOME from an address printed after 1835 — T-0669.

THE FOURTH GRAMMAR, AIMED AT THE OTHER QUESTION. `tools/back_project_addresses.py`
(T-0633, policy `docs/ADDRESS-BACK-PROJECTION.md`, liberty L218) reads a street printed
four to nine years after the scene backwards and carries it as a BUSINESS's street face.
Its clause 2 refuses, by name, an address the volume itself prints as a RESIDENCE — its
own `res` or `bds` — because positioning a home is "the same mechanism aimed at a
different question", and it named this ticket as the place that question gets answered.

This file answers it. The policy is `docs/RESIDENCE-BACK-PROJECTION.md` and the liberty
is **L223**. The mechanism is deliberately the business pass's, imported rather than
copied — the same street tables, the same folding, the same 1835 street layer — because
two passes reading `Michigan ave` differently would be a worse fault than either reading.
What differs is the argument, and it differs in two places that are stated as clauses
rather than left in the code:

  R2  A HOME NEEDS NO ATTESTED TRADE, where a business does. The business pass's clause 1
      refuses a person the 1835 corpus gives no trade, and it is right to: there is no
      business for a later door to place, and minting one out of an 1844 directory is the
      thing that pass may never do. A residence is not that claim. Everybody the town
      holds lived somewhere in it, so an absent occupation removes nothing, and this pass
      therefore adjudicates every residence-printed address rather than the handful whose
      person also happens to carry a trade.

  R5  A FACE, AND NEVER A POINT, where a business may reach a crossing. The business pass
      resolves `cor.` and `near` onto the point where two committed centrelines meet. A
      home does not get one here, for two reasons written out in the policy: the corner
      words in these entries hang off street NUMBERS from a grid 1835 did not have, and a
      dwelling moves more than a shopfront does. The extra precision would be this pass
      claiming most exactly where its evidence is thinnest.

WHAT IT DOES NOT DO. It writes no `lives_at`. `docs/STREET-FACE-ADOPTION.md` limit 3 says
dealing a household to one roof on a face is an allocation and not a reading; stacking
that on an address already carried back eight years would be two inventions under one
chip. `--self-test` asserts it rather than the prose promising it.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from back_project_addresses import (  # noqa: E402
    NOT_1835,
    RESIDENCE_PREFIX,
    SCENE_YEAR,
    split_home,
    STREET_1835,
    VOLUME_TITLE,
    households,
    load_streets,
    street_words,
)

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "data" / "research" / "directories" / "residence_back_projection.json"

# `res` is where the directory says a man lived; `bds` is where it says he boarded.
# They are not one claim — a lodging is a month's rent and a residence is a household
# — so the record carries which word was printed and the policy reasons about both.
BOARDS = re.compile(r"^\s*(bds\.?|boards)\b", re.I)

# A directory's back-reference to the line above it. Fergus prints `res same` where the
# previous entry's address stands, and the crosswalk that fed this layer carried the two
# words without the antecedent — so there is no address here at all to read backwards.
SAME_AS_ABOVE = re.compile(r"^\s*(res\.?|bds\.?|boards)\s+same\b", re.I)

# A NAMED PLACE, tested BEFORE any street name is looked for, and that ordering is the
# whole point of the table. `bds Lake House` contains the word `Lake` and the Lake House
# is a hotel on the north side, nowhere near Lake Street; `res Fort Dearborn` contains
# `Dearborn` and the fort stands at the river mouth, not on Dearborn Street. Resolving
# either as a street face would be the pass inventing a placement out of a collision
# between a building's name and a street's.
NAMED_PLACE = (
    (re.compile(r"\bfort\s+dearborn\b", re.I),
     "The entry names Fort Dearborn — the fort at the river mouth — and not Dearborn "
     "Street, which runs south from the river three blocks west of it. The fort IS 1835 "
     "ground and the town holds it, but this policy's unit is a street face and a "
     "reservation is not one, so the address is refused here rather than resolved onto "
     "the wrong grammar."),
    (re.compile(r"\bgovern(?:ment|m'?t)\s+reservation\b", re.I),
     "The entry names the government reservation — the military ground round the fort — "
     "which is a place the town holds and is not a street. This policy positions a home "
     "on a street face and has no grammar for a reservation, so it refuses rather than "
     "reaching for the nearest street name."),
    (re.compile(r"\b(house|hotel|refectory|tavern|saloon|exchange)\b", re.I),
     "The entry names a public house by its sign — where this person boarded, not a "
     "street they lived on. A house of 1843 is a building, and resolving a building "
     "printed eight years after the scene onto 1835 ground is a second reading this pass "
     "does not make: it would have to identify the house, date it to 1835 and place it, "
     "and each of those is its own source question."),
    (re.compile(r"\b(mrs|mr|miss|dr|capt|col|maj|rev)\b\.?\s+[A-Z]", re.I),
     "The entry names the household this person boarded with, by its head, and not a "
     "street. Where that household is itself in this town the two records could be "
     "joined, but that is a crosswalk between two people and not an address read "
     "backwards."),
    (re.compile(r"\b\d(?:st|d|nd|rd|th)\s+ward\b", re.I),
     "The entry gives a WARD, which is a division of the Chicago of 1843 and not a "
     "street. The town's 1835 wards are not these wards — the city was not incorporated "
     "until 1837 — so the figure does not carry back at all."),
)

# `bds John Gray`, `bds Erastus Bowen`: a bare personal name, no title to key on. Two
# capitalised words and no street word anywhere is a person, and the row above catches
# only the titled ones. The surname takes an internal capital because `bds Michael
# McDonald` is a person by any reading and `McDonald` is not `[A-Z][a-z]+`.
BARE_PERSON = re.compile(r"^[A-Z][a-z]+\.?\s+([A-Z]\.?\s+)?[A-Z][a-zA-Z']+\b")

# `bds H. Wolcott`: the same person, set with an INITIAL instead of a forename — and
# unlike `bds John Gray` it has to be tested BEFORE the street table rather than after
# it, because the surname a man boards with can also be a street this town has. Alexander
# Wolcott boarded with H. Wolcott in 1843; `street_words` read `Wolcott` as Wolcott
# Street, the bare-personal-name row is only reached when NO street name is found, and
# the pass placed a man on a street because his host shared a name with it. The compass
# initials are excluded, or `res N. Water` reads as a man called Water; and a street word
# anywhere in the body means the volume is naming a street, not a host.
INITIALLED_PERSON = re.compile(
    r"^(?!(?:N|S|E|W|No|So)\b)[A-Z]\.\s*(?:[A-Z]\.\s*)?[A-Z][a-zA-Z']+\.?$")

# `residence Hum phrey Clark's`: THE POSSESSIVE, which is the surest of the three and
# the only one that survives the archive.org reading. The two tests above key on the
# SHAPE of a name — an initial and a period, or two capitalised words — and a mis-set
# space inside a forename defeats both: `Hum phrey` is neither `H.` nor `[A-Z][a-z]+`
# followed by a capital. What it cannot defeat is the apostrophe the compositor set to
# say whose house this is. None of these four volumes ever prints a STREET
# possessively, so a body ending `'s` names a householder, and it is tested in front of
# the street table for exactly the reason `INITIALLED_PERSON` is: Erastus Clark boarded
# at Humphrey Clark's, and `street_words` reads `Clark` as Clark Street. T-0987 stretch
# 6 found this by placing him there.
POSSESSIVE_HOST = re.compile(r"['\u2019]s\.?$")


def kind_of(printed: str) -> str:
    return "boards" if BOARDS.match(printed) else "resides"


def adjudicate_one(streets, hh, persons, person, claim) -> dict:
    """One residence-printed address, through the five clauses, in order."""
    # The home HALF of the field, and the whole field stays the quote (T-0987
    # stretch 7). Where the crosswalk's split left the trade's trailing corner in
    # front of the residence word, reading the whole field would send the five
    # clauses at the shop's street instead of the house's.
    field = str(claim["value"])
    printed = split_home(field)[1] or field
    year = int(claim.get("describes_date") or 0)
    pid = person["person_id"]
    trade = ((persons.get(pid) or {}).get("occupation") or {}).get("value")
    lives_at = (hh.get("lives_at") or {}).get("value")
    row = {
        "household_id": hh["id"],
        "person_id": pid,
        "person": (persons.get(pid) or {}).get("name") or pid,
        "address_as_printed": field,
        "address_read_as_the_home": printed if printed != field else None,
        "kind": kind_of(printed),
        "describes_date": year,
        "read_back_years": year - SCENE_YEAR if year else None,
        "sources": list(claim.get("sources") or []),
        "occupation_1835": trade if trade and trade != "none_recorded" else None,
        "trade_not_required": True,
        "lives_at_1835": lives_at,
        "outcome": None,
        "clause": None,
        "reason": None,
        "street_id": None,
        "face": None,
        "placement": None,
    }

    # R3 — an 1835 placement always wins, exactly as the business pass's clause 2 says.
    if lives_at:
        row.update(outcome="already_better_placed", clause="R3",
                   reason=f"An 1835 placement already stands: this household lives at "
                          f"`{lives_at}`, and clause R3 says an attested 1835 placement "
                          f"beats a door printed {row['read_back_years']} years later.")
        return row

    # R4 — the address has to be a street, on the 1835 grid, under that name.
    if SAME_AS_ABOVE.match(printed):
        row.update(outcome="refused", clause="R4",
                   reason="The directory prints `same` — a back-reference to the address "
                          "on the line above it — and the crosswalk that fed this layer "
                          "carried the two words without their antecedent. There is no "
                          "address here to read backwards, and inventing the neighbouring "
                          "entry's street would be reading the volume's typography as "
                          "evidence about the ground.")
        return row

    body = RESIDENCE_PREFIX.sub("", printed).strip(" .,")
    # The volume's own typesetting loses a space: `bds American TemperanceHouse` is
    # printed exactly so, and `\bhouse\b` cannot see a word that has no boundary in
    # front of it — which sent a public house down the bare-personal-name row below
    # and refused it for the wrong reason. A lower-to-upper transition is re-spaced
    # for THIS scan only: the sign table keys on common nouns, so splitting a name
    # like `McDonald` costs it nothing, while `street_words` and `BARE_PERSON` below
    # keep the printed body untouched because both of them do key on names.
    sign_body = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", body)
    for pattern, why in NAMED_PLACE:
        if pattern.search(sign_body):
            row.update(outcome="refused", clause="R4", reason=why)
            return row

    if POSSESSIVE_HOST.search(body):
        row.update(outcome="refused", clause="R4",
                   reason="The entry names the person the householder boarded with in "
                          "the possessive — whose house it is — and not a street; these "
                          "volumes never print a street that way. It is tested before "
                          "the street table because the householder's surname can be a "
                          "street this town carries. Where that person is also in "
                          "this town the two records could be joined, but that is a "
                          "crosswalk between two people and not an address read "
                          "backwards.")
        return row

    if INITIALLED_PERSON.match(body):
        row.update(outcome="refused", clause="R4",
                   reason="The entry names the person the householder boarded with, set "
                          "with an initial, and not a street — and the surname is also a "
                          "street this town carries, which is the collision this test is "
                          "ordered in front of the street table to catch. Where that "
                          "person is also in this town the two records could be joined, "
                          "but that is a crosswalk between two people and not an address "
                          "read backwards.")
        return row

    names = street_words(printed)
    if not names:
        if BARE_PERSON.match(body):
            row.update(outcome="refused", clause="R4",
                       reason="The entry names the person the householder boarded with "
                              "and not a street. Where that person is also in this town "
                              "the two records could be joined, but that is a crosswalk "
                              "between two people and not an address read backwards.")
        else:
            row.update(outcome="refused", clause="R4",
                       reason="The address names no street at all, so there is nothing to "
                              "resolve onto the 1835 grid.")
        return row

    head, rest = names[0], names[1:]
    if head in NOT_1835:
        row.update(outcome="refused", clause="R4", reason=NOT_1835[head])
        return row
    if head not in STREET_1835:
        row.update(outcome="refused", clause="R4",
                   reason=f"'{head}' is not a street this pass's 1835 table knows, and a "
                          f"name it cannot rule on is refused rather than guessed.")
        return row

    sid = STREET_1835[head]
    street = streets[sid]
    row.update(street_id=sid, face=street["name_1835"])

    # R4's second half — a qualifier naming a street the town does not have is fatal to
    # the whole address, not just to the qualifier. Giles Spring's `res 62 Adams near
    # State` is the case the ticket expected to survive on State: it does not, because
    # the directory says his house was on Adams, and moving him to State would be this
    # pass placing him where the volume does not say he was.
    for other in rest:
        if other in NOT_1835:
            row.update(outcome="refused", clause="R4",
                       reason=f"The face resolves — {street['name_1835']} is 1835's — but "
                              f"the entry sets the house against a second street the town "
                              f"does not have: {NOT_1835[other]} Taking the face and "
                              f"dropping the qualifier would put the home somewhere the "
                              f"address does not say it was.")
            return row

    # R5 — a face, and never a point. The business pass would resolve a `cor.` or a
    # `near` onto a crossing here; a home does not get one.
    narrower = [streets[STREET_1835[o]]["name_1835"] for o in rest
                if o in STREET_1835 and STREET_1835[o] != sid]
    row.update(
        outcome="placed", clause="R4 and R5", placement="face",
        reason=(f"{street['name_1835']} stands in 1835 under that name and in that place, "
                f"and the entry prints it as this person's "
                f"{'lodging' if row['kind'] == 'boards' else 'home'}. "
                + (f"The volume narrows it further — it names "
                   f"{' and '.join(narrower)} — and clause R5 declines to take the point: "
                   f"a corner or a run between two crossings is a fact about the numbered "
                   f"grid of the 1840s, and a house moves more than a shopfront does. "
                   if narrower else "")
                + f"So the placement is the FACE and nothing narrower, and no roof is "
                  f"dealt."))
    return row


def adjudicate(streets, records) -> list[dict]:
    """Every residence-printed `address_later` in the layer. R1 is this selection.

    R1 — THE POPULATION. This pass reads an address the volume itself prints as a
    residence and no other. The business pass reads the rest and refuses these at its
    own clause 2, so between them every one of the layer's later addresses is
    adjudicated exactly once and by the rule written for its question.
    """
    rows = []
    for _, hh in records:
        block = hh.get("directories")
        if not block:
            continue
        persons = {p["id"]: p for p in hh.get("persons", [])}
        for person in block.get("people", []):
            claim = person.get("address_later")
            if not (claim and claim.get("value")):
                continue
            if not split_home(claim["value"])[1]:
                continue
            rows.append(adjudicate_one(streets, hh, persons, person, claim))
    rows.sort(key=lambda r: (r["household_id"], r["person_id"]))
    return rows


def note_for(row: dict) -> str:
    """The plain words clause R5 requires, on the record itself."""
    back = row["read_back_years"]
    volume = ", ".join(VOLUME_TITLE.get(s, s) for s in row["sources"])
    word = "boarded" if row["kind"] == "boards" else "lived"
    if row["outcome"] == "placed":
        return (
            f"A LATER HOME ADDRESS, READ BACKWARDS {back} YEARS. The street is not an "
            f"1835 reading: {volume} printed where this person {word} in "
            f"{row['describes_date']}, and this pass carries it back to the scene date "
            f"because nothing in the 1835 corpus says where the house stood. What is "
            f"claimed is the street FACE and nothing narrower — no lot, no roof, no door "
            f"count, and no corner even where the volume prints one — and the grade is "
            f"`reconstructed`, this dataset's word for a figure the reconstruction "
            f"supplies rather than a source. {row['reason']} A home is carried back on a "
            f"weaker argument than a shop is: a shopfront is capital sunk into one "
            f"street's trade and a lodging is a month's rent, which is why this policy "
            f"claims less than docs/ADDRESS-BACK-PROJECTION.md does from the same volume. "
            f"The rule is docs/RESIDENCE-BACK-PROJECTION.md and the liberty is L223; a "
            f"reader who thinks {back} years is too far to carry a house should read the "
            f"grade as the disagreement being invited.")
    if row["outcome"] == "already_better_placed":
        return (
            f"NOT READ BACK, BECAUSE SOMETHING BETTER ALREADY STANDS. {volume} prints an "
            f"address against this name in {row['describes_date']}, and it is left where "
            f"it is. {row['reason']} The later address stays on the record as "
            f"{row['describes_date']}'s evidence and moves nothing.")
    return (
        f"REFUSED, AND THE REFUSAL IS THE RECORD. {volume} prints where this person "
        f"{word} in {row['describes_date']} and this pass will not carry it back to "
        f"1835. "
        f"{row['reason']} A refusal is written here rather than dropped so that a later "
        f"run can see the address was read and ruled on, not missed "
        f"(docs/RESIDENCE-BACK-PROJECTION.md, clause {row['clause']}).")


def block_for(row: dict) -> dict:
    """The `residence_back_projection` block as the household record carries it.

    Shaped exactly like T-0633's `back_projection` block, and for the reason that pass
    gives: `street_id` stays in the ledger because the record already carries the same
    fact in the words the volume used, and a `confidence` is written only where there is
    a placement to grade — a refusal is not a figure held at low confidence, it is the
    absence of a figure.
    """
    return {
        "outcome": row["outcome"],
        "clause": row["clause"],
        "kind": row["kind"],
        "value": row["face"] if row["outcome"] == "placed" else None,
        **({"confidence": "reconstructed"} if row["outcome"] == "placed" else {}),
        "describes_date": row["describes_date"],
        "read_back_years": row["read_back_years"],
        "placement": row["placement"],
        "sources": list(row["sources"]),
        "note": note_for(row),
    }


def counts(rows, records) -> dict:
    placed = [r for r in rows if r["outcome"] == "placed"]
    lives = sum(1 for _, h in records if (h.get("lives_at") or {}).get("value"))
    works = sum(1 for _, h in records if (h.get("works_at") or {}).get("value"))
    return {
        "addresses_adjudicated": len(rows),
        "printed_as_a_residence": len([r for r in rows if r["kind"] == "resides"]),
        "printed_as_a_lodging": len([r for r in rows if r["kind"] == "boards"]),
        "placed": len(placed),
        "placed_as_a_face": len([r for r in placed if r["placement"] == "face"]),
        "placed_with_no_1835_trade": len([r for r in placed
                                          if not r["occupation_1835"]]),
        "already_better_placed": len([r for r in rows
                                      if r["outcome"] == "already_better_placed"]),
        "refused": len([r for r in rows if r["outcome"] == "refused"]),
        "faces_reached": sorted({r["face"] for r in placed}),
        "lives_at_real_values": lives,
        "works_at_real_values": works,
    }


def build(records=None):
    streets = load_streets()
    records = records if records is not None else households()
    rows = adjudicate(streets, records)
    ledger = {
        "schema": 1,
        "_doc": "GENERATED by tools/back_project_residences.py (T-0669). Every address a "
                "Chicago directory of 1839, 1843 or 1844 prints as a RESIDENCE — its own "
                "`res` or `bds` — against a person of 1835, put through the five clauses "
                "of docs/RESIDENCE-BACK-PROJECTION.md. The policy is L223 and the unit of "
                "a placement is a STREET FACE, never a corner, never a lot and never a "
                "roof. Refusals are here in full: an address this pass declines is a "
                "reading it made, not one it missed.",
        "generated_by": "tools/back_project_residences.py",
        "policy": "docs/RESIDENCE-BACK-PROJECTION.md",
        "liberty": "L223",
        "scene_year": SCENE_YEAR,
        "street_layer": "data/streets/1835.json",
        "business_pass": "tools/back_project_addresses.py",
        "counts": counts(rows, records),
        "rows": rows,
    }
    blocks = {f"{r['household_id']}::{r['person_id']}": block_for(r) for r in rows}
    return ledger, blocks


def write() -> dict:
    records = households()
    ledger, blocks = build(records)
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    # `indent=1, ensure_ascii=False` and a trailing newline, because every other writer
    # over this layer uses exactly that shape and compares its files byte for byte.
    LEDGER.write_text(json.dumps(ledger, indent=1, ensure_ascii=False) + "\n")
    for path, hh in records:
        block = hh.get("directories")
        if not block:
            continue
        touched = False
        for person in block.get("people", []):
            key = f"{hh['id']}::{person['person_id']}"
            if key in blocks:
                if person.get("residence_back_projection") != blocks[key]:
                    person["residence_back_projection"] = blocks[key]
                    touched = True
            elif "residence_back_projection" in person:
                del person["residence_back_projection"]
                touched = True
        if touched:
            path.write_text(json.dumps(hh, indent=1, ensure_ascii=False) + "\n")
    return ledger["counts"]


def check() -> int:
    records = households()
    ledger, blocks = build(records)
    problems = []
    if not LEDGER.exists():
        problems.append(f"{LEDGER.relative_to(ROOT)} is missing")
    elif json.loads(LEDGER.read_text()) != ledger:
        problems.append(f"{LEDGER.relative_to(ROOT)} disagrees with a re-derivation — "
                        f"run tools/back_project_residences.py --write")
    for path, hh in records:
        for person in (hh.get("directories") or {}).get("people", []):
            key = f"{hh['id']}::{person['person_id']}"
            if person.get("residence_back_projection") != blocks.get(key):
                problems.append(f"{path.name}: {person['person_id']} carries a "
                                f"residence_back_projection block that is not the one "
                                f"this pass derives")
    for p in problems[:20]:
        print(f"   {p}")
    if problems:
        print(f"back_project_residences: {len(problems)} problem(s)")
        return 1
    c = ledger["counts"]
    print(f"back_project_residences: ok — {c['addresses_adjudicated']} residence "
          f"addresses adjudicated, {c['placed']} placed, {c['refused']} refused")
    return 0


def self_test() -> int:
    """The clauses, on cases the corpus actually contains."""
    streets = load_streets()
    fails = []

    def one(printed, trade=None, lives=None, year=1843):
        hh = {"id": "hh_t", "lives_at": {"value": lives},
              "persons": [{"id": "p", "name": "T", "occupation": {"value": trade}}]}
        person = {"person_id": "p"}
        claim = {"value": printed, "describes_date": year,
                 "sources": ["fergus_chicago_directory_1843"]}
        return adjudicate_one(streets, hh, {"p": hh["persons"][0]}, person, claim)

    def want(label, row, outcome, clause, placement=None):
        if row["outcome"] != outcome or row["clause"] != clause or (
                placement is not None and row["placement"] != placement):
            fails.append(f"{label}: got {row['outcome']}/{row['clause']}/"
                         f"{row['placement']}, wanted {outcome}/{clause}/{placement}")

    # R2, the departure this policy is FOR: no trade in 1835 refuses nothing here,
    # where the business pass's clause 1 would have refused it outright.
    want("a home needs no trade", one("res Clark", trade="none_recorded"),
         "placed", "R4 and R5", "face")
    want("nor an occupation block at all", one("res Clark", trade=None),
         "placed", "R4 and R5", "face")
    # R3 — an 1835 placement wins.
    want("an 1835 lives_at wins", one("res Clark", lives="some_roof"),
         "already_better_placed", "R3")
    # Norris's own shorthand for the same word, from his preface, and the population
    # this pass gained when T-0987 stretch 6 let that volume's parse cross: `h` is
    # house, `r` is residence, and the mis-set `hou.«e` is in the corpus as printed.
    want("Norris's h is a home", one("h Clark st", year=1844),
         "placed", "R4 and R5", "face")
    want("Norris's r is a home", one("r Clark", year=1844),
         "placed", "R4 and R5", "face")
    want("house spelled out is a home", one("house Clark st", year=1844),
         "placed", "R4 and R5", "face")
    want("a mis-set house is still a house", one("hou.\u00abe Clark st", year=1844),
         "placed", "R4 and R5", "face")
    # R4 — `same` is a back-reference and not an address, in every volume's word for it.
    want("res same", one("res same"), "refused", "R4")
    want("bds same", one("bds same"), "refused", "R4")
    want("house same", one("house same", year=1844), "refused", "R4")
    want("h same", one("h same", year=1844), "refused", "R4")
    # R4 — a named place is tested BEFORE any street name, which is what keeps the
    # Lake House off Lake Street and Fort Dearborn off Dearborn Street.
    want("bds Lake House", one("bds Lake House"), "refused", "R4")
    # The 1843 volume prints this with the space dropped, and a sign is still a sign.
    r_sign = one("bds American TemperanceHouse")
    if "public house by its sign" not in (r_sign["reason"] or ""):
        fails.append("bds American TemperanceHouse: refused, but not as a named house")
    want("res Fort Dearborn", one("res Fort Dearborn"), "refused", "R4")
    want("res Government Reservation", one("res Government Reservation"),
         "refused", "R4")
    want("bds Mrs. Post", one("bds Mrs. Post"), "refused", "R4")
    want("bds John Gray", one("bds John Gray"), "refused", "R4")
    want("bds Michael McDonald", one("bds Michael McDonald"), "refused", "R4")
    # The host whose surname is also a street: refused as a person, and the compass
    # initial that must NOT read as one.
    want("bds H. Wolcott is a host, not Wolcott Street",
         one("bds H. Wolcott"), "refused", "R4")
    # The possessive, and the mis-set forename that defeats both shape tests above.
    want("residence Humphrey Clark's is a host, not Clark Street",
         one("residence Humphrey Clark's", year=1844), "refused", "R4")
    want("a mis-set forename does not save the host",
         one("residence Hum phrey Clark's", year=1844), "refused", "R4")
    want("res J. Gray's", one("res J. Gray's", year=1844), "refused", "R4")
    # ...and a street is still a street: no volume prints one possessively.
    want("res Clark st is not a host", one("res Clark st", year=1844),
         "placed", "R4 and R5", "face")
    want("res N. Water is a street and not a man called Water",
         one("res N. Water"), "placed", "R4 and R5", "face")
    want("a ward is not a street", one("res 3d Ward, south of Jackson"), "refused", "R4")
    # R4 — the 1835 grid, head and qualifier both.
    want("Michigan ave is not Michigan Street", one("res 96 Michigan ave"),
         "refused", "R4")
    want("Dearborn pl is a later platting", one("res 5 Dearborn pl"), "refused", "R4")
    want("West Water is not in the layer", one("res West Water near Lake"),
         "refused", "R4")
    want("a qualifier off the grid refuses the whole address",
         one("res LaSalle, bet Washington and Madison"), "refused", "R4")
    want("and so does Adams, which the ticket expected State to rescue",
         one("res 62 Adams near State"), "refused", "R4")
    # ...AND SO DOES A QUALIFIER THE VOLUME CONTRACTED — T-1050. This is the case that
    # found the hole: `h Clark st. b Mad. & Mon` is Rebecca Sherman's entry and it had
    # been PLACED on Clark Street, because the street table knew `Madison` and not
    # Norris's `Mad.`, so R4's second half never saw the qualifier. Two lines down the
    # same column he sets John Rue's house the same place spelled out, and that one was
    # refused. The assertion is therefore not just the outcome but that the two
    # spellings of one address get one verdict, for one reason, word for word.
    want("a contracted qualifier refuses the address too",
         one("h Clark st. b Mad. & Mon", year=1844), "refused", "R4")
    abbreviated = one("h Clark st. b Mad. & Mon", year=1844)
    spelled_out = one("h Clark, b Madison and Monroe", year=1844)
    if abbreviated["reason"] != spelled_out["reason"]:
        fails.append("one address, two spellings, two reasons:\n"
                     f"      abbreviated: {abbreviated['reason']}\n"
                     f"      spelled out: {spelled_out['reason']}")
    # The other entry the contractions reach, and the reason a refusal is not enough on
    # its own: John Kinzie's `h c Mich dc Cass` was refused before this too, but for the
    # wrong street — the table could not see `Mich`, so CASS became the head and the
    # north-side Michigan Street his house actually stood on was never resolved.
    r_kinzie = one("h c Mich dc Cass", year=1844)
    if r_kinzie["face"] != "Michigan Street" or r_kinzie["outcome"] != "refused":
        fails.append(f"h c Mich dc Cass: got {r_kinzie['outcome']} on "
                     f"{r_kinzie['face']}, wanted refused on Michigan Street")
    # And a contraction cannot turn an 1835 street off the grid: the head still places.
    want("a contracted head street on the grid still places",
         one("h Rand st. b Dear and Lake sts", year=1844),
         "placed", "R4 and R5", "face")
    # R5 — a face, and never a point, even where the volume prints a corner.
    want("a bare street is a face", one("res Market"), "placed", "R4 and R5", "face")
    want("three 1835 streets are still one face",
         one("res Washington, bet Franklin and Market"), "placed", "R4 and R5", "face")
    r = one("bds. Randolph street cor. Dearborn", year=1839)
    want("a printed corner is still only a face", r, "placed", "R4 and R5", "face")
    if r.get("position_local_enu_m") is not None or "position_local_enu_m" in block_for(r):
        fails.append("R5: a residence reached a point, which this policy never claims")
    if r["kind"] != "boards":
        fails.append("`bds.` should read as a lodging, not a residence")
    if one("res Market")["kind"] != "resides":
        fails.append("`res` should read as a residence")

    # R5 is not optional: every placement is graded, says it was read back, and is a
    # face. And nothing this pass writes touches an 1835 link.
    ledger, _ = build()
    for row in ledger["rows"]:
        b = block_for(row)
        if row["outcome"] == "placed":
            if b["confidence"] != "reconstructed":
                fails.append(f"{row['person_id']}: a placement graded {b['confidence']}")
            if b["placement"] != "face":
                fails.append(f"{row['person_id']}: a placement narrower than a face")
            if "read backwards" not in b["note"].lower():
                fails.append(f"{row['person_id']}: the note does not say it is read back")
        if not (b["note"] or "").strip():
            fails.append(f"{row['person_id']}: no note")
    for _, hh in households():
        for person in (hh.get("directories") or {}).get("people", []):
            bp = person.get("residence_back_projection")
            if bp and set(bp) & {"lives_at", "works_at", "position_local_enu_m"}:
                fails.append(f"{hh['id']}: a residence block writing a link or a point")

    # THE TWO PASSES MAY BOTH RULE, AND MAY NEVER BOTH PLACE. A residence-printed
    # address against a person the 1835 papers give no trade is refused by the business
    # pass at ITS clause 1 — there is no business to position — and adjudicated here on
    # its own merits, which is two rulings on two questions and not a contradiction. 44
    # of these 48 are in that position today. What would be a contradiction is the same
    # printed address earning a placement under both policies, so that is what is
    # asserted: the business pass places none of this population. Three of the 48 stand
    # OFF there instead of refusing — Elston, Kercheval and Miller carry a real
    # `works_at` — and a stand-off is not a placement, so it is not a collision either.
    import back_project_addresses as business
    biz, _ = business.build()
    mine = {(r["household_id"], r["person_id"]) for r in ledger["rows"]}
    for r in biz["rows"]:
        if (r["household_id"], r["person_id"]) not in mine:
            continue
        if r["outcome"] == "placed":
            fails.append(f"{r['person_id']}: the business pass PLACED an address "
                         f"printed as a residence, which only this pass may do")

    # T-1122: NEITHER PASS'S GENERATED PROSE ASSUMES THE HOUSEHOLDER'S SEX. Both are
    # asserted from here as well as from the business pass's own self-test, because the
    # two share their tables and are held word-for-word to each other — a phrase can be
    # introduced on either side of that import and must fail on both.
    fails.extend(business.sexed_prose("back_project_residences",
        business.generated_prose(ledger["rows"], note_for,
            [(f"NAMED_PLACE[{i}]", why) for i, (_, why) in enumerate(NAMED_PLACE)]
            + [(f"NOT_1835[{k}]", v) for k, v in NOT_1835.items()])))
    fails.extend(business.sexed_prose("back_project_addresses",
        business.generated_prose(biz["rows"], business.note_for)))

    for f in fails:
        print(f"   {f}")
    print(f"back_project_residences --self-test: "
          f"{'FAIL' if fails else 'ok'} ({len(fails)} problem(s))")
    return 1 if fails else 0


def report() -> int:
    ledger, _ = build()
    for k, v in ledger["counts"].items():
        print(f"  {k}: {v}")
    print()
    for row in ledger["rows"]:
        mark = {"placed": "PLACED  ", "already_better_placed": "STOOD-OFF",
                "refused": "refused "}[row["outcome"]]
        print(f"  {mark} {row['person']:28s} {row['kind']:8s} "
              f"{row['face'] or '-':22s} <- {row['address_as_printed']}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--report", action="store_true")
    args = ap.parse_args()
    if args.write:
        c = write()
        print(f"back_project_residences: {c['addresses_adjudicated']} adjudicated, "
              f"{c['placed']} placed on a face, {c['already_better_placed']} already "
              f"better placed, {c['refused']} refused")
        return 0
    if args.self_test:
        return self_test()
    if args.report:
        return report()
    return check()


if __name__ == "__main__":
    sys.exit(main())
