#!/usr/bin/env python3
"""THE EMPLOYMENT COVERAGE ANSWER: every person in the layer, at work or told why not.

T-1461, piece 1 of 2 of T-1449, of T-1434, of T-1189.

    tools/employment_coverage_1835.py --build       write the coverage join and its report
    tools/employment_coverage_1835.py --check       re-derive, refuse drift, assert the cover
    tools/employment_coverage_1835.py --self-test   the guards, fired on the real layer

THE GAP THIS CLOSES. Two passes have written where people worked and neither of them
covers the town. T-1432 carried across the 112 cards a SOURCE names in a house. T-1433
answered the 524 residents this project drew with a trade — seats for 124 of them and a
stated reason for the other 400. Between them that is 636 of the layer's 3,243 people,
and the other 2,607 stood in a silence no file admitted to: no workplace, no seat, no
reason, nothing. A card that says nothing about work reads exactly like a card that has
been ruled on and found to have no employer, and until this pass the two were the same
blank. This gives EVERY person one answer, from a closed set, in the words of the rule
that decided it — so a silence is now a statement and can be counted, gated and argued
with.

WHAT IT IS NOT, AND THE THREE THINGS IT REFUSES. It mints nobody, reads no page of any
source, raises no business and writes not one byte onto a person card. It is an
adjudication over committed files — the seven resident directories, the two joins above,
`premises_rulings.json` and the staffing model — and every answer it gives is already
implied by one of them. In particular:

  * IT SUPPLIES NO TRADE. 2,536 people carry `occupation: none_recorded`, which is the
    layer saying no source records their work. The temptation here is to read a trade in
    from the household — a wife keeps house, a son is at his father's bench — and it is
    refused. `no_trade_recorded` is the answer and it is a statement about the EVIDENCE.
  * IT SEATS NOBODY. Where T-1433 could not point at a house, this does not point at one
    either; it carries T-1433's own word for why.
  * IT DOES NOT CALL A WORKING PERSON UNEMPLOYED. The soldier at the post and the
    laundress over her own tub follow a trade and have no employer in the business layer.
    `at_a_trade_with_no_house_to_join` says that, because `not_employed` would be false.

THE FIVE ANSWERS. Every person gets exactly one, and the first three are the ticket's
"a workplace" while the last two are its "explicit not_employed reason":

  `at_a_named_house`                 a source names the house they worked in. The
                                     houses are on the card, written by T-1432.
  `at_a_seat_this_project_drew`      the staffing model names a class of house that
                                     employed their trade and the layer held one with
                                     room. T-1433 drew it and the card prints the draw.
  `on_their_own_account`             `premises_rulings.json` says this trade kept
                                     premises of its own. They are their own employer,
                                     and where the layer holds no such record the house
                                     is OWED rather than absent — unless it is a roof
                                     the programme has none left to owe, which is
                                     stated (T-1997).
  `at_a_trade_with_no_house_to_join` they carry a trade and the business layer holds no
                                     house this project may join them to. Five reasons:
                                     four are somebody else's ticket to close, and one
                                     (T-1993) says no house of trade is owed at all.
  `no_trade_recorded`                the layer records no trade for them and this pass
                                     does not supply one.

WORKING AGE IS THE STAFFING MODEL'S FLOOR AND THE CARD'S OWN BAND, KEPT APART. The model
names the youngest hand it staffs a house with — `youth_12_18`, "a boy or girl bound or
hired young" — and the floor is read OUT of that vocabulary rather than typed here, so
the day the model stops employing twelve-year-olds this moves with it. The card's
`age_band` is a different question: it says how the age was EVIDENCED, and the model says
so itself ("These say what age a kind of hand was ... They are different questions and
this file does not mix them"). So the two meet in one place only — does the card's band
lie above the floor, below it, or across it — and a band that lies ACROSS it is a third
answer and not a coin toss:

  `working_age`          the band lies wholly at or above the floor: 2,150 people.
  `below_working_age`    the band lies wholly below it: 483 people.
  `age_is_not_settled`   the band straddles the floor (10-14, 10-19) or the card carries
                         no band at all: 610 people. They are answered ANYWAY — an
                         employment question left open because an age is open is the
                         silence this pass exists to remove — and counted apart so a
                         reader can take them out again.

WHAT THE COVER IS WORTH, AND THE CAUTION THAT GOES WITH IT. 441 of the layer's people can
be placed at work: 112 at a named house, 124 at a drawn seat, 205 on their own account.
The town model's `employed_persons` figure is 424-588, from the 1840 schedule's 18% of
persons in its seven industry columns applied to the July population range. 441 is inside
that band, and the band is NOT thereby met: it is a size struck against a town of
2,353-3,265 people, the layer holds 3,243 cards, and the model's own open question says
the 1840 columns have no row for domestic service at all. A number inside a range is a
place to start arguing, not a job finished.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RESIDENTS = ROOT / "data" / "residents"
BUSINESSES = ROOT / "data" / "businesses"
PREMISES_RULINGS = BUSINESSES / "rulings" / "premises_rulings.json"
STAFFING_MODEL = ROOT / "data" / "reconstruction" / "1835_business_staffing_model.json"
TOWN_MODEL = ROOT / "data" / "reconstruction" / "1835_town_model.json"
SEATING = RESIDENTS / "reconstructed_seating.json"
ATTESTED_HOUSES = RESIDENTS / "attested_trade_houses.json"
ORDER_BOOK = ROOT / "data" / "reconstruction" / "1835_reconstruction_order_book.json"
COVERAGE_OUT = RESIDENTS / "employment_coverage.json"

SCENE_DATE = "1835-07-01"
TICKET = "T-1461"
PARENT_TICKET = "T-1449"

#: The directories of the resident layer that hold household-shaped records. The same
#: seven T-1433 reads, and for the same reason: three fifths of the people this answers
#: for do not stand in `households/`.
RESIDENT_DIRS = ("households", "reconstructed_trades", "lodgers", "underdocumented",
                 "transients", "readmitted", "merged")

#: A value the occupation field uses to say the sources record no trade. T-1433's list,
#: unchanged — the two passes must agree about what a trade is or their answers overlap.
NOT_A_TRADE = ("none_recorded", "not_recorded", "unknown", None, "")

#: T-1994's four answers for an attested trade whose premises ruling sends the person to an
#: establishment they do not keep, and no house in the register is owed for it. Each is a
#: STATED reason, never an owed one: the person works, and the town is short no house.
ATTESTED_NONE_OWED = ("serves_an_establishment_outside_the_register",
                      "not_held_by_the_establishment_on_the_scene_date",
                      "a_civic_seat_and_not_a_house",
                      "works_on_other_people_s_ground")
ATTESTED_ANSWERS = ("joined", "none_owed")

#: The five statuses, and for each the reasons it may carry. A status is never written
#: without a reason: "he is not at work" is not an answer, "the layer records no trade
#: for him" is. Closed here and asserted against in `verify`.
STATUSES = {
    "at_a_named_house": ("named_by_a_source", "on_the_staff_of_a_house",
                         "joined_by_the_attested_trade_ruling"),
    "at_a_seat_this_project_drew": ("seated_by_the_staffing_model",
                                    "drawn_onto_a_house_s_staff"),
    "on_their_own_account": ("keeps_their_own_house", "keeps_a_house_the_register_holds",
                             "roofs_kept_none_owed"),
    "at_a_trade_with_no_house_to_join": (
        "no_employer_named", "class_held_no_house", "class_full_none_owed",
        "trade_attested_no_house_named", "no_ruling_on_the_trade",
        "in_service_in_another_household", *ATTESTED_NONE_OWED,
        "the_printed_count_is_held",
        "the_mechanics_shops_are_over_their_count", "held_on_an_identity_question"),
    "no_trade_recorded": ("no_trade_recorded",),
}

#: The statuses that place a person at work. The other two are the ticket's "explicit
#: not_employed reason", and `at_a_trade_with_no_house_to_join` is in NEITHER set by
#: accident: those people work and this project cannot say where.
PLACED = ("at_a_named_house", "at_a_seat_this_project_drew", "on_their_own_account")

#: What each answer SAYS, in one sentence a card can print. Held here once rather than
#: on 3,243 rows, which is the difference between a 0.7 MB join and a 2 MB one.
WORDS = {
    "named_by_a_source":
        "A source names the house this person worked in, and the houses are listed "
        "above at the grade the business record gave each one.",
    "seated_by_the_staffing_model":
        "No source names a house for this person. The staffing model names a class of "
        "house that employed their trade, the layer held one with room in its band, and "
        "this project seated them there — a draw, shown above with the seed that redraws it.",
    "keeps_their_own_house":
        "The premises ruling for this trade says it kept a house of trade of its own, so "
        "this person is their own employer. Where the layer holds no such record the "
        "house is OWED — a gap in the business register, not a person out of work.",
    "no_employer_named":
        "The premises ruling says this trade kept no premises of its own, and the "
        "staffing model employs it in nobody else's: the soldier at the post, the "
        "laundress over her own tub, the farmer on his own ground. They are at work and "
        "the business layer has no house to join them to.",
    "class_held_no_house":
        "The staffing model names the class of house that employed this trade and the "
        "layer holds none of it trading on 1 July 1835, or every one is full to the "
        "band's high end. The town is owed more houses of the kind; the person is not "
        "put in one that is already full.",
    "class_full_none_owed":
        "The staffing model names the class of house that employed this trade, the layer "
        "holds every house of it the model counts on 1 July 1835, and each is full to the "
        "band's high end. The trade keeps no house of its own, so none is owed: the town "
        "is not short a house, and the person follows the trade with no room in it to "
        "join (T-1995).",
    "roofs_kept_none_owed":
        "The trade's house is a roof the programme schedules, a boarding house, and the "
        "order book cannot count one. Every standing boarding house is kept, and the "
        "roofs the programme still schedules are owed to the keepers ahead of this one in "
        "a seeded draw, so none is owed: the town is not short a boarding house this "
        "person would keep. They are still their own employer, and carry the trade on "
        "their own account with no house of their own (T-1997).",
    "trade_attested_no_house_named":
        "The sources name this person's trade and name no house for it. Drawing one "
        "would put a man the record knows into a shop nobody put him in, so no seat is "
        "drawn and the absence is carried instead.",
    "in_service_in_another_household":
        "The premises ruling for this trade says the work is given in another "
        "household's house: domestic service, done in a family's kitchen, washhouse and "
        "yard rather than in a house of trade. The staffing model employs the trade in "
        "the town's taverns and hotels only, and every one was full, but that does not "
        "make the town owed another tavern — no house of trade is owed for this person. "
        "Which household employed them no source says and this pass draws none.",
    "no_ruling_on_the_trade":
        "`premises_rulings.json` has never ruled on this trade, so whether it kept "
        "premises of its own is unanswered. T-1404 owns the ruling; until it is made "
        "this pass says so rather than guessing at it.",
    "keeps_a_house_the_register_holds":
        "A record in the business register names this person as the house's proprietor "
        "or partner, so they kept it and worked in it. The house is named here at the "
        "grade that record gives the proprietorship: attested where a source prints it, "
        "inferred where the trade's premises ruling raised it, reconstructed where this "
        "project drew the house and adopted them to keep it.",
    "on_the_staff_of_a_house":
        "A record in the business register names this person on its own staff: the "
        "office, church or agency they served, at a source the record cites. They did "
        "not keep the house; they worked in it.",
    "drawn_onto_a_house_s_staff":
        "A record in the business register carries this person on its staff at the "
        "reconstructed tier: this project drew them there, and the record says by what "
        "rule.",
    "joined_by_the_attested_trade_ruling":
        "A source attests this person's trade, and its premises ruling sends them to an "
        "establishment they did not keep. The business register holds that house and a "
        "source names them in it, or the card's own reasoning does; the ruling below "
        "says which, at the grade it allows (T-1994).",
    "serves_an_establishment_outside_the_register":
        "The establishment this trade served is held by a committed file that is not the "
        "business register — the garrison at the fort, an agency held for a company in "
        "another town — and that file places this person in it. They are at work, and no "
        "house of trade is owed (T-1994).",
    "not_held_by_the_establishment_on_the_scene_date":
        "The establishment this trade served does not hold this person on 1 July 1835: "
        "its own record names somebody else in the seat, the source dates the work out of "
        "the window, or a ruling already refused them. No house is owed; the ruling below "
        "says which (T-1994).",
    "a_civic_seat_and_not_a_house":
        "The premises ruling calls this trade a civic seat and not a house of trade. Where "
        "the seat sat is a place on the person (T-1405's associated_with), not a business, "
        "and the register's county offices are the clerk's room and do not hold it (T-1994).",
    "works_on_other_people_s_ground":
        "The premises ruling says this trade is done on somebody else's ground — inside the "
        "customer's building, in the field, in the vessel owner's yard — so it keeps no "
        "house of its own and is owed none (T-1994).",
    "the_mechanics_shops_are_over_their_count":
        "This trade kept a shop of its own, and the December 1835 State census has no line "
        "for it, so no count of its class was ever printed to be short of. What WAS printed "
        "is a count of shops: the Chicago American of 15 August 1835 numbers the town's "
        "\"twenty-five mechanics' shops of all kinds\", and the register's own printed "
        "houses of those trades trading on 1 July 1835 are more than that already (the "
        "figures are below). A shop raised for this person would push the town further "
        "past the one count there is. Most mechanics were hands in a master's shop, or "
        "carpenters and masons who worked where the wall was going up; which shop or "
        "which wall is not drawn, and no house is owed (T-2000).",
    "held_on_an_identity_question":
        "The premises ruling holds this person and trade on an open identity question: "
        "a man the register may already print under another reading of the name. Raising "
        "a shop of his own would split the two by arithmetic, and seating him in the "
        "printed man's shop would merge them the same way, so neither is done. The house "
        "waits on the question named below and is counted owed until it is answered "
        "(T-2000).",
    "the_printed_count_is_held":
        "This trade kept a house of its own, and the December 1835 State census counts "
        "the class of house it kept. The register and the houses this project drew "
        "already hold that count on 1 July 1835 (the figures are below), so a house "
        "raised for this person would be one more than the census printed. They follow "
        "the trade and no house is owed; which of the held houses they kept, clerked or "
        "partnered in is not drawn (T-1996).",
    "no_trade_recorded":
        "No source records a trade for this person and no reconstruction stage has given "
        "them one. This is a statement about the evidence and not about the person: a "
        "trade is not read in from the household, and none is supplied here.",
}

AGE_SCOPES = ("working_age", "below_working_age", "age_is_not_settled")

#: THE TRADES WHOSE WORK IS GIVEN IN SOMEBODY ELSE'S HOUSEHOLD (T-1993, piece 1 of 3 of
#: T-1991). T-1433 seats a reconstructed trade-holder in the class of house the staffing
#: model employs the trade in, and where every house of that class is full it answers
#: `class_held_no_house` — "the town is owed more houses of the kind". That is right for
#: a smith and wrong for a servant. The model staffs only HOUSES OF TRADE, so the one
#: class it employs `domestic` in is `tavern_or_hotel`, and 61 working-age domestics the
#: taverns had no room for read on 2 October 2026 as a town owed 61 hotel places. The
#: premises ruling already says where the rest of the trade worked — "Domestic service is
#: given in another household's house" — and a private household is not a house of trade
#: the register owes. So the overflow carries the ruling's answer instead of the model's.
#: The value is the ruling's own words, asserted against its `basis` in `verify` so the
#: day the ruling says otherwise this stops agreeing with it out loud. No household is
#: drawn for them: which family kept which servant is not in any file this reads.
IN_ANOTHER_HOUSEHOLD = {"domestic": "given in another household's house"}

#: THE REGISTER'S OWN PEOPLE ROWS (T-1990, piece 1 of 3 of T-1982). A business record
#: names the people it holds in three lists, and until this pass the join read none of
#: them: it read the CARD's `workplaces[]` (T-1432) and the SEATING (T-1433), so a man the
#: Indian Agency's own record names as its interpreter, or a milliner the business band
#: adopted to keep a reconstructed shop, still read "at a trade with no house" or "the
#: house is OWED" on their card — 78 of the 308 the completion audit counted owed a
#: workplace on 2026-10-02. The register already answered them; this reads its answer.
#: It writes nothing onto the record and decides no seat: the row is the business
#: record's, at the record's own tier, and `decided_by` says which record and which row.
REGISTER_KEEPS = ("proprietors", "partners")
REGISTER_STAFF = ("staff",)
REGISTER_REASONS = ("keeps_a_house_the_register_holds", "on_the_staff_of_a_house",
                    "drawn_onto_a_house_s_staff")

#: THE ATTESTED TRADES WITH NO HOUSE NAMED (T-1994, piece 2 of 3 of T-1991). After the
#: card, the seating and the register have answered, 25 people still read
#: `trade_attested_no_house_named`: a source gives their trade, its premises ruling sends
#: them to an establishment they did not keep, and nothing joined them to one. Drawing a
#: seat for a man the record knows is refused above, so each was ruled on BY NAME in
#: `attested_trade_houses.json` — joined to the house the register holds, at the grade the
#: source allows, or told in the ruling's own words why none is owed. This applies that
#: file and nothing else: a row whose person no longer reads that reason is stale and is
#: refused, because a ruling made against one answer is not a ruling on another.
ATTESTED_REASON = "trade_attested_no_house_named"
#: THE SECOND ANSWER A BY-NAME RULING MAY REPLACE (T-2001). A documented keeper whose card
#: reads `keeps_their_own_house` and whose house the register prints under a name no
#: person_id joins — John Bates Jr.'s auction store — is not owed a house; he is owed the
#: JOIN. The row says which answer it replaces (`replaces`, default the one above), the
#: guard still refuses a row whose person reads anything else, and a keeper's row may only
#: join: telling a documented keeper that none is owed is a different ruling (T-1996's
#: refusal) and is not made in this file.
ATTESTED_REPLACES = (ATTESTED_REASON, "keeps_their_own_house")
#: THE PRINTED COUNT ALREADY HELD (T-1996, piece 1 of 3 of T-1992). After the card, the
#: seating and the register have answered, a drawn head can still read
#: `keeps_their_own_house` with no house: the resident band drew heads at a trade by the
#: 1839 trade table's share of the PERSONS it was short, and the business band raises a
#: house only where the order book ORDERS one — against the December census's printed
#: count of the class. Where the census counts the class and the book's bucket is full
#: (`to_reconstruct - filled <= 0`: forty-four stores printed and sixty-five held, the
#: lawyers' scene-date bracket met), there is no house to owe. The answer reads the
#: book's own bucket and prints its figures.
#: ONLY ON A RECONSTRUCTED PERSON. A count a reconstructed house helps fill is exactly
#: the count a documented man's own house would retire it from (each such record's
#: `withdrawn_if` says so), so a person a source knows is never told the count is held;
#: they stay owed until somebody rules on them by name.
HELD_REASON = "the_printed_count_is_held"
HELD_FROM = "keeps_their_own_house"
HELD_GRADE = "reconstructed"

#: THE MECHANICS' SHOPS ALREADY PAST THEIR COUNT (T-2000, of T-1998). After every answer
#: above, a drawn head can still read `keeps_their_own_house` with no house at a trade
#: whose census class is `other`: the December census never counted it, the order book
#: orders only against printed counts, so no bucket will ever order the house and none
#: will ever say it is not owed. One count of these premises WAS printed — the Chicago
#: American, 15 August 1835, quoted by Andreas: "twenty-five mechanics' shops of all
#: kinds" — and docs/RESEARCH/business-layer.md (§ the mechanics' shops of 1835, T-1185)
#: already rules it the bound on the TOTAL of mechanics' shops, never on a row.
#: Which trades it counts is the premises ruling's own word: every ruling whose basis
#: says the trade is "one of the twenty-five mechanics' shops the Chicago American
#: counted", plus the works trades T-1185's own list of the mechanics' shops names
#: (smiths, butchers, tanners, saddlers) and whose ruling signs them as a works rather
#: than a shop front. The town is held to be at the count when the register's PRINTED
#: houses of those trades trading on 1 July 1835 meet it alone — no inferred or
#: reconstructed house is counted towards it, so nothing this project drew can be what
#: closes the count against a person it drew.
#: ONLY ON A RECONSTRUCTED PERSON, as T-1996 rules for the printed census counts: a man a
#: source knows is ruled on by name or left owed.
SHOPS_REASON = "the_mechanics_shops_are_over_their_count"
SHOPS_FROM = "keeps_their_own_house"
SHOPS_GRADE = "reconstructed"
SHOPS_CLASS = "other"
SHOPS_COUNT = 25
SHOPS_PRINTED = "twenty-five mechanics' shops of all kinds"
SHOPS_CITED = "one of the twenty-five mechanics' shops the Chicago American counted"
SHOPS_T1185_WORKS = ("blacksmith", "butcher", "tanner", "harness_maker", "saddler")
SHOPS_COUNTED_PROVENANCE = "compiled_from_register"

#: THE IDENTITY HOLD (T-2000). `premises_rulings.json#identity_holds` names a person and
#: a trade this project has an open identity question about, and refuses them a house of
#: their own. Without this the card read "the house is OWED" as though the register were
#: simply short; it is not short, it is waiting on a question, and the card says which.
HOLD_REASON = "held_on_an_identity_question"


class Fault(Exception):
    """A refusal, printed and exited on. Never a warning."""


# ------------------------------------------------------------------ reading --

def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load() -> dict:
    for path in (PREMISES_RULINGS, STAFFING_MODEL, TOWN_MODEL, SEATING):
        if not path.exists():
            raise Fault(f"{path.relative_to(ROOT)} is missing — this pass adjudicates "
                        "over committed files and cannot stand in for one")
    people = []
    for name in RESIDENT_DIRS:
        folder = RESIDENTS / name
        if not folder.is_dir():
            continue
        for path in sorted(folder.glob("*.json")):
            record = _load_json(path)
            households = (record.get("households") if isinstance(record, dict)
                          and "households" in record
                          else (record if isinstance(record, list) else [record]))
            for household in households:
                for person in household.get("persons") or []:
                    people.append((name, household, person))
    if not people:
        raise Fault("the residents layer holds no person")
    businesses = {}
    # The authored records are the register too (the civic establishments T-1188 raised,
    # the inferred houses of the trades, the reconstructed houses the business band
    # drew), and a join that read the top folder alone could not name one of them.
    for path in sorted(BUSINESSES.glob("*.json")) + sorted(
            (BUSINESSES / "authored").glob("*.json")):
        if path.name == "index.json":
            continue
        record = _load_json(path)
        for row in (record.get("businesses") if isinstance(record, dict)
                    and "businesses" in record
                    else (record if isinstance(record, list) else [record])):
            if isinstance(row, dict) and row.get("id"):
                businesses[row["id"]] = row
    seating = _load_json(SEATING)
    premises = _load_json(PREMISES_RULINGS)
    if not ORDER_BOOK.exists():
        raise Fault(f"{ORDER_BOOK.relative_to(ROOT)} is missing — the printed counts are "
                    "read from it and are not restated here")
    buckets = {}
    for family in _load_json(ORDER_BOOK).get("bucket_families") or []:
        if family.get("key") != "businesses":
            continue
        for bucket in family.get("buckets") or []:
            klass = (bucket.get("axes") or {}).get("class")
            if klass:
                buckets[klass] = bucket
    if not buckets:
        raise Fault("the order book holds no business bucket, so no printed count can be "
                    "read and none will be assumed")
    attested = (_load_json(ATTESTED_HOUSES).get("rows") or []
                if ATTESTED_HOUSES.exists() else [])
    return {
        "attested_houses": {row["person_id"]: row for row in attested},
        "buckets": buckets,
        "people": people,
        "businesses": businesses,
        "register": register_rows(businesses),
        "seating": {row["person_id"]: row for row in seating.get("rows") or []},
        "seating_ticket": seating.get("ticket"),
        "rulings": {r["occupation"]: r for r in premises["rulings"]},
        "identity_holds": {(h["person_id"], h["occupation"]): h
                           for h in premises.get("identity_holds") or []},
        "model": _load_json(STAFFING_MODEL),
        "town_model": _load_json(TOWN_MODEL),
    }


# ----------------------------------------------------------------- deriving --

def working_age_floor(model: dict) -> dict:
    """The youngest age the staffing model puts anybody to work at, read OUT of its own
    `age_bands` vocabulary rather than typed here. `youth_12_18` is the youngest term it
    holds and 12 is the number in it; the day the model stops staffing a house with a
    boy of twelve this floor moves with it and the report says it did."""
    bands = ((model.get("vocabularies") or {}).get("age_bands") or {})
    if not bands:
        raise Fault("the staffing model carries no age_band vocabulary, so this pass "
                    "has no floor to read and will not invent one")
    ages = [int(n) for term in bands for n in re.findall(r"\d+", term)]
    if not ages:
        raise Fault("the staffing model's age bands carry no ages")
    floor = min(ages)
    youngest = sorted(term for term in bands if str(floor) in re.findall(r"\d+", term))
    return {
        "floor": floor,
        "read_from": "data/reconstruction/1835_business_staffing_model.json"
                     "#vocabularies.age_bands",
        "the_term_it_came_from": youngest[0] if youngest else None,
        "in_the_model_s_words": bands.get(youngest[0]) if youngest else None,
        "why_it_is_read_and_not_typed":
            "The floor is the youngest age any role in the staffing model is staffed at. "
            "Reading it out of the model means a re-cut of the model moves it, and the "
            "counts below move with it, rather than this file going quietly stale.",
    }


def band_bounds(band):
    """The (low, high) years a resident card's age band covers, or None if it carries
    none. `50+` has no printed high end and is read as open above."""
    if not band:
        return None
    text = str(band).strip()
    pair = re.fullmatch(r"(\d+)\s*-\s*(\d+)", text)
    if pair:
        return int(pair.group(1)), int(pair.group(2))
    open_ended = re.fullmatch(r"(\d+)\s*\+", text)
    if open_ended:
        return int(open_ended.group(1)), None
    raise Fault(f"the age band {band!r} is in no form this pass reads. A band it cannot "
                "read is not quietly dropped: add the form here or fix the card.")


def age_scope(band, floor: int) -> str:
    bounds = band_bounds(band)
    if bounds is None:
        return "age_is_not_settled"
    low, high = bounds
    if high is not None and high < floor:
        return "below_working_age"
    if low >= floor:
        return "working_age"
    return "age_is_not_settled"


#: T-1433's seven kinds (T-1995 added `class_full_none_owed`, T-1997
#: `roofs_kept_none_owed`), mapped onto this pass's
#: answers. The mapping is the whole of what this pass says about those 524 people: it
#: re-words nothing and re-decides nothing.
FROM_SEATING = {
    "seated": ("at_a_seat_this_project_drew", "seated_by_the_staffing_model"),
    "keeps_their_own_house": ("on_their_own_account", "keeps_their_own_house"),
    "class_held_no_house": ("at_a_trade_with_no_house_to_join", "class_held_no_house"),
    "class_full_none_owed": ("at_a_trade_with_no_house_to_join", "class_full_none_owed"),
    "roofs_kept_none_owed": ("on_their_own_account", "roofs_kept_none_owed"),
    "no_employer_named": ("at_a_trade_with_no_house_to_join", "no_employer_named"),
    "no_ruling": ("at_a_trade_with_no_house_to_join", "no_ruling_on_the_trade"),
}


def answer(person: dict, context: dict) -> dict:
    """The one answer this person gets, and where it came from. Pure over the committed
    files: no counter, no draw, no order — which is why the same card answers the same
    way whatever order the layer is read in."""
    occupation = person.get("occupation") or {}
    trade = occupation.get("value")
    if trade in NOT_A_TRADE:
        trade = None

    workplaces = person.get("workplaces") or []
    if workplaces:
        return {
            "status": "at_a_named_house",
            "reason": "named_by_a_source",
            "decided_by": "the card's own workplaces[], written by T-1432",
            "houses": [w.get("business_id") for w in workplaces if w.get("business_id")],
        }

    seat = context["seating"].get(person["id"])
    if seat:
        kind = seat.get("kind")
        if kind not in FROM_SEATING:
            raise Fault(f"{person['id']} carries a seating kind {kind!r} this pass has "
                        "no answer for. A new kind is a new answer and must be ruled on "
                        "here, not folded into an old one.")
        status, reason = FROM_SEATING[kind]
        decided_by = (f"reconstructed_seating.json#{kind}, drawn by "
                      f"{context['seating_ticket']}")
        if kind == "class_held_no_house" and trade in IN_ANOTHER_HOUSEHOLD:
            reason = "in_service_in_another_household"
            decided_by += (f"; premises_rulings.json#{trade} = no_fixed_premises, "
                           f"{IN_ANOTHER_HOUSEHOLD[trade]!r}, read by T-1993")
        return {
            "status": status,
            "reason": reason,
            "decided_by": decided_by,
            "houses": [seat["business_id"]] if seat.get("business_id") else [],
        }

    if trade is None:
        return {
            "status": "no_trade_recorded",
            "reason": "no_trade_recorded",
            "decided_by": "the card's occupation, which records none",
            "houses": [],
        }

    ruling = context["rulings"].get(trade)
    if ruling is None:
        return {
            "status": "at_a_trade_with_no_house_to_join",
            "reason": "no_ruling_on_the_trade",
            "decided_by": f"premises_rulings.json has no ruling for {trade!r}",
            "houses": [],
        }
    if ruling.get("premises") == "own_premises":
        return {
            "status": "on_their_own_account",
            "reason": "keeps_their_own_house",
            "decided_by": f"premises_rulings.json#{trade} = own_premises",
            "houses": [],
        }
    return {
        "status": "at_a_trade_with_no_house_to_join",
        "reason": "trade_attested_no_house_named",
        "decided_by": f"premises_rulings.json#{trade} = {ruling.get('premises')}, and no "
                      "source names a house",
        "houses": [],
    }


def _covers_scene_date(row: dict) -> bool:
    """False only where the row's own dates put it wholly off 1 July 1835. A partial
    date ("1833-05") is compared at its own precision; a missing one bounds nothing."""
    start, end = row.get("from"), row.get("to")
    if start and str(start) > SCENE_DATE[:len(str(start))]:
        return False
    if end and str(end) < SCENE_DATE[:len(str(end))]:
        return False
    return True


def register_rows(businesses: dict) -> dict:
    """person_id -> the business register's rows naming them, on records present at the
    scene date and not excluded, in id order so the answer does not depend on the order
    the folder is read in."""
    out: dict = {}
    for bid, record in sorted(businesses.items()):
        if record.get("present_at_scene_date") is False or record.get("exclusion"):
            continue
        for side in REGISTER_KEEPS + REGISTER_STAFF:
            for row in record.get(side) or []:
                pid = row.get("person_id") if isinstance(row, dict) else None
                if not pid or not _covers_scene_date(row):
                    continue
                name = record.get("name")
                if isinstance(name, dict):
                    name = name.get("value")
                out.setdefault(pid, []).append({
                    "business_id": bid, "name": name or bid, "side": side,
                    "role": row.get("role"),
                    "tier": row.get("tier") or row.get("confidence")})
    return out


def register_answer(rows: list) -> dict:
    """The register's answer for one person. Keeping a house outranks serving on a staff
    roll, because the house a person keeps is where they are their own employer; the
    houses listed are every record of that rank, so two partnerships are both named."""
    keeps = [r for r in rows if r["side"] in REGISTER_KEEPS]
    chosen = keeps or rows
    if keeps:
        status, reason = "on_their_own_account", "keeps_a_house_the_register_holds"
    elif all(r["tier"] == "reconstructed" for r in chosen):
        status, reason = "at_a_seat_this_project_drew", "drawn_onto_a_house_s_staff"
    else:
        status, reason = "at_a_named_house", "on_the_staff_of_a_house"
    named = "; ".join(f"{r['business_id']}#{r['side']} ({r['role'] or 'unstated'}, "
                      f"{r['tier'] or 'ungraded'})" for r in chosen)
    houses = sorted({r["business_id"] for r in chosen})
    names = {r["business_id"]: r["name"] for r in chosen}
    return {
        "status": status,
        "reason": reason,
        "decided_by": f"the business register's own row: {named}, read by T-1990",
        "houses": houses,
        # The card has no business index to look a name up in, and the house is the
        # answer, so the name travels with it — on these rows only, which are the only
        # ones whose house the card does not already print from its own block.
        "house_names": [names[h] for h in houses],
    }


def attested_answer(ruling: dict, businesses: dict) -> dict:
    """The answer T-1994's ruling gives one person. A join names a house the register
    holds on the scene date and carries its grade and citation; a none-owed answer
    carries one of four stated reasons and the committed file that decides it."""
    pid, kind = ruling.get("person_id"), ruling.get("answer")
    where = f"{ATTESTED_HOUSES.name}#{pid}"
    if kind not in ATTESTED_ANSWERS:
        raise Fault(f"{where} answers {kind!r}, which is in no vocabulary here")
    if not ruling.get("basis"):
        raise Fault(f"{where} carries no basis. A ruling with no reasoning is a guess.")
    if kind == "joined":
        house = ruling.get("house")
        record = businesses.get(house)
        if record is None:
            raise Fault(f"{where} joins {house!r}, which the business register does not "
                        "hold")
        if record.get("present_at_scene_date") is False or record.get("exclusion"):
            raise Fault(f"{where} joins {house!r}, which is not trading on the scene date")
        if ruling.get("tier") not in ("attested", "inferred"):
            raise Fault(f"{where} joins at the tier {ruling.get('tier')!r}; a join of a "
                        "documented person is `attested` on a source or `inferred` on "
                        "stated reasoning, and nothing else")
        if not ruling.get("source_id"):
            raise Fault(f"{where} joins with no source_id to stand on")
        name = record.get("name")
        name = name.get("value") if isinstance(name, dict) else name
        return {
            "status": "at_a_named_house",
            "reason": "joined_by_the_attested_trade_ruling",
            "decided_by": f"attested_trade_houses.json#{pid}: {house} as "
                          f"{ruling.get('role') or 'unstated'}, {ruling['tier']} on "
                          f"{ruling['source_id']}, ruled by "
                          f"{ruling.get('ticket') or 'T-1994'}",
            "houses": [house],
            "house_names": [name or house],
            "ruling": ruling["basis"],
        }
    reason = ruling.get("reason")
    if reason not in ATTESTED_NONE_OWED:
        raise Fault(f"{where} says none is owed for the reason {reason!r}, which is not "
                    "one of the four this file may give")
    if not ruling.get("reads"):
        raise Fault(f"{where} says none is owed and names no committed file that says so")
    return {
        "status": "at_a_trade_with_no_house_to_join",
        "reason": reason,
        "decided_by": f"attested_trade_houses.json#{pid}, reading {ruling['reads']}, "
                      "ruled by T-1994",
        "houses": [],
        "ruling": ruling["basis"],
    }


def mechanic_trades(rulings: dict) -> list:
    """The trades the American's twenty-five counts, read off the premises rulings: those
    whose own basis names the count, and T-1185's works trades where they keep premises."""
    trades = {occ for occ, r in rulings.items()
              if r.get("premises") == "own_premises" and SHOPS_CITED in (r.get("basis") or "")}
    trades |= {occ for occ in SHOPS_T1185_WORKS
               if (rulings.get(occ) or {}).get("premises") == "own_premises"}
    if not trades:
        raise Fault("no premises ruling cites the Chicago American's twenty-five "
                    "mechanics' shops, so T-2000's count has nothing to count")
    return sorted(trades)


def shops_held(data: dict) -> dict:
    """The mechanics' shops trading on 1 July 1835, by the grade of the house. Only the
    register's printed houses are set against the American's count."""
    trades = set(mechanic_trades(data["rulings"]))
    by_provenance: dict = {}
    printed: dict = {}
    for record in data["businesses"].values():
        if not record.get("present_at_scene_date") or record.get("occupation") not in trades:
            continue
        grade = record.get("provenance") or "unstated"
        by_provenance[grade] = by_provenance.get(grade, 0) + 1
        if grade == SHOPS_COUNTED_PROVENANCE:
            printed[record["occupation"]] = printed.get(record["occupation"], 0) + 1
    return {
        "printed_count": SHOPS_COUNT,
        "printed_words": SHOPS_PRINTED,
        "printed_by": "the Chicago American, 15 August 1835, quoted by Andreas — six "
                      "weeks after the scene date (docs/RESEARCH/business-layer.md § the "
                      "mechanics' shops of 1835)",
        "trades_it_counts": sorted(trades),
        "register_printed_houses": sum(printed.values()),
        "register_printed_houses_by_trade": dict(sorted(printed.items())),
        "all_houses_by_provenance": dict(sorted(by_provenance.items())),
        "at_the_count": sum(printed.values()) >= SHOPS_COUNT,
    }


def shops_answer(person: dict, trade: str, data: dict, held: dict) -> dict | None:
    """T-2000's answer for a drawn head at a mechanic trade the census never counted,
    where the register's printed shops already meet the American's count; else None."""
    ruling = data["rulings"].get(trade) or {}
    if (person.get("grade") != SHOPS_GRADE or ruling.get("census_class") != SHOPS_CLASS
            or trade not in held["trades_it_counts"] or not held["at_the_count"]):
        return None
    return {
        "status": "at_a_trade_with_no_house_to_join",
        "reason": SHOPS_REASON,
        "decided_by": f"premises_rulings.json#{trade} = own_premises, census_class "
                      f"{SHOPS_CLASS} (no printed count); the Chicago American, 15 August "
                      f"1835: \"{SHOPS_PRINTED}\"; the register prints "
                      f"{held['register_printed_houses']} of them trading on 1 July 1835, "
                      "so none is owed — ruled by T-2000",
        "houses": [],
    }


def hold_answer(hold: dict) -> dict:
    return {
        "status": "at_a_trade_with_no_house_to_join",
        "reason": HOLD_REASON,
        "decided_by": f"premises_rulings.json#identity_holds — {hold['question']} "
                      f"({hold['where']}): no house is raised while it is open — named "
                      "by T-2000",
        "houses": [],
    }


def bucket_full(bucket: dict) -> bool:
    """True where the order book orders no further house of the class: what it left to
    reconstruct, the business band has filled (or there was nothing left to fill)."""
    return (bucket.get("to_reconstruct") or 0) - (bucket.get("filled") or 0) <= 0


def held_answer(person: dict, trade: str, data: dict) -> dict | None:
    """T-1996's answer for a drawn head whose own house the printed count already holds,
    or None where it does not apply: a documented person, a trade whose class the census
    never counted, or a bucket still short of its count."""
    if person.get("grade") != HELD_GRADE:
        return None
    klass = (data["rulings"].get(trade) or {}).get("census_class")
    bucket = data.get("buckets", {}).get(klass)
    if bucket is None or not bucket_full(bucket):
        return None
    held = f"{bucket.get('known')} known + {bucket.get('filled') or 0} filled"
    return {
        "status": "at_a_trade_with_no_house_to_join",
        "reason": HELD_REASON,
        "decided_by": f"premises_rulings.json#{trade} = own_premises, census_class "
                      f"{klass}; 1835_reconstruction_order_book.json#{bucket['key']}: "
                      f"printed {bucket.get('census_count')} {bucket.get('unit') or ''}"
                      f"{'s' if bucket.get('unit') else ''}, target "
                      f"{bucket.get('target')}, held {held}, so none is ordered — "
                      "ruled by T-1996",
        "houses": [],
    }


def derive(data: dict) -> dict:
    floor = working_age_floor(data["model"])["floor"]
    context = {"seating": data["seating"], "rulings": data["rulings"],
               "seating_ticket": data["seating_ticket"]}
    register = data.get("register") or {}
    held = shops_held(data)
    rows = []
    for folder, household, person in data["people"]:
        occupation = person.get("occupation") or {}
        band = person.get("age_band")
        band = band.get("value") if isinstance(band, dict) else band
        block = answer(person, context)
        scope = age_scope(band, floor)
        # The card and the seating answer first and keep their answer where it names a
        # house. Where it names none, a register row naming the person is the house —
        # except below the working-age floor, where a child on a staff roll is a fault
        # in one of the two files and is left for `verify`'s guard to say so, not placed.
        if (not block["houses"] and person["id"] in register
                and scope != "below_working_age"):
            block = register_answer(register[person["id"]])
        ruling = (data.get("attested_houses") or {}).get(person["id"])
        if ruling is not None:
            replaces = ruling.get("replaces") or ATTESTED_REASON
            if replaces not in ATTESTED_REPLACES:
                raise Fault(f"{person['id']} is ruled on in "
                            f"{ATTESTED_HOUSES.relative_to(ROOT)} against {replaces!r}, "
                            f"which is not one of {list(ATTESTED_REPLACES)}")
            if replaces != ATTESTED_REASON and ruling.get("answer") != "joined":
                raise Fault(f"{person['id']} keeps their own house and the ruling tells "
                            "them none is owed. A keeper's row in this file joins the "
                            "house the register prints or it is not made here.")
            if block["reason"] != replaces:
                raise Fault(f"{person['id']} is ruled on in "
                            f"{ATTESTED_HOUSES.relative_to(ROOT)} and reads "
                            f"{block['reason']!r}, not {replaces!r}. The ruling was "
                            "made against the answer it replaces; retire the row.")
            block = attested_answer(ruling, data["businesses"])
        trade = occupation.get("value") or ""
        if block["reason"] == HELD_FROM and not block["houses"]:
            # T-1996 answers a class the census counts, T-2000 one it never did (and
            # names an identity hold first): the three never apply to the same person.
            hold = (data.get("identity_holds") or {}).get((person["id"], trade))
            block = (hold_answer(hold) if hold is not None
                     else held_answer(person, trade, data)
                     or shops_answer(person, trade, data, held) or block)
        rows.append({
            "person_id": person["id"],
            "household_id": household.get("id"),
            "record_folder": folder,
            "age_band": band,
            "age_scope": scope,
            "trade": (occupation.get("value")
                      if occupation.get("value") not in NOT_A_TRADE else None),
            "trade_confidence": occupation.get("confidence"),
            **block,
        })
    rows.sort(key=lambda r: r["person_id"])
    return {"rows": rows, "floor": floor, "mechanics_shops": held}


# ------------------------------------------------------------------ report --

def _tally(rows, key):
    out: dict = {}
    for row in rows:
        out[row[key]] = out.get(row[key], 0) + 1
    return dict(sorted(out.items()))


def _figure(town_model: dict, section: str, figure: str):
    for block in town_model.get("sections") or []:
        if block.get("key") != section:
            continue
        for row in block.get("figures") or []:
            if row.get("figure") == figure:
                return row
    return None


def report(data: dict, coverage: dict) -> dict:
    rows = coverage["rows"]
    floor = working_age_floor(data["model"])
    placed = [r for r in rows if r["status"] in PLACED]
    with_trade = [r for r in rows if r["trade"]]
    working = [r for r in rows if r["age_scope"] == "working_age"]
    employed = _figure(data["town_model"], "occupations", "employed_persons") or {}
    given_trade = _figure(data["town_model"], "occupations",
                          "people_the_layer_gives_a_trade") or {}
    cross: dict = {}
    for row in rows:
        cross.setdefault(row["age_scope"], {})
        cross[row["age_scope"]][row["status"]] = \
            cross[row["age_scope"]].get(row["status"], 0) + 1
    return {
        "$schema_note": "DERIVED — regenerate with tools/employment_coverage_1835.py "
                        "--build; tools/check.sh re-derives it. Do not hand-edit.",
        "not_a_card": "A JOIN BESIDE THE RESIDENT LAYER, NOT A FIELD ON IT. Keyed on "
                      "person_id, in the same idiom as reconstructed_seating.json and "
                      "directories.json — two thirds of these cards are the byte-compared "
                      "output of a reconstruction stage and a key appended to one breaks "
                      "that stage's gate rather than adding a field.",
        "id": "1835_employment_coverage",
        "ticket": TICKET,
        "parent_ticket": PARENT_TICKET,
        "target_date": SCENE_DATE,
        "generated_by": "tools/employment_coverage_1835.py --build",
        "not_a_reading": "an adjudication over committed files — no page of any source is "
                         "read here, no person is written, no trade is supplied and no "
                         "seat is drawn",
        "writes_no_person": True,
        "mints_nobody": True,
        "supplies_no_trade": True,
        "what_it_writes": "one row per person in the resident layer: the one employment "
                          "answer they carry, the rule that decided it, and whether their "
                          "age band puts them above the staffing model's working-age floor",
        "inputs": [
            "data/residents/{households,reconstructed_trades,lodgers,underdocumented,"
            "transients,readmitted,merged}/*.json",
            "data/residents/reconstructed_seating.json (T-1433)",
            "data/residents/attested_trade_houses.json (T-1994)",
            "data/reconstruction/1835_reconstruction_order_book.json (the printed counts, "
            "T-1996)",
            "data/businesses/*.json",
            "data/businesses/authored/*.json (the register's own people rows, T-1990)",
            "data/businesses/rulings/premises_rulings.json (and its identity_holds, "
            "T-2000)",
            "data/reconstruction/1835_business_staffing_model.json",
            "data/reconstruction/1835_town_model.json",
        ],
        "working_age_rule": {
            **floor,
            "scopes": {
                "working_age": "the card's age band lies wholly at or above the floor",
                "below_working_age": "the band lies wholly below it",
                "age_is_not_settled": "the band straddles the floor, or the card carries "
                                      "none. These people are answered anyway and counted "
                                      "apart, so a reader can take them out again.",
            },
        },
        "vocabulary": {
            "statuses": {status: {"reasons": list(reasons),
                                  "places_them_at_work": status in PLACED}
                         for status, reasons in sorted(STATUSES.items())},
            "reasons": dict(sorted(WORDS.items())),
            "at_work_is_not_placed":
                "`at_a_trade_with_no_house_to_join` is in neither set and that is the "
                "point of it. Those people follow a trade; what is missing is a house in "
                "the business layer to join them to. Counting them as unemployed would be "
                "false and counting them as placed would be an invention.",
        },
        "counts": {
            "people": len(rows),
            "by_status": _tally(rows, "status"),
            "by_reason": _tally(rows, "reason"),
            "by_age_scope": _tally(rows, "age_scope"),
            "by_age_scope_and_status": {k: dict(sorted(v.items()))
                                        for k, v in sorted(cross.items())},
            "placed_at_work": len(placed),
            "carry_a_trade": len(with_trade),
            "working_age": len(working),
            "working_age_placed_at_work": len([r for r in working
                                               if r["status"] in PLACED]),
            "working_age_with_no_trade_recorded":
                len([r for r in working if r["status"] == "no_trade_recorded"]),
        },
        "mechanics_shops": coverage["mechanics_shops"],
        "against_the_town_model": {
            "employed_persons": {
                "model_low": employed.get("low"),
                "model_high": employed.get("high"),
                "the_layer_places": len(placed),
                "inside_the_band": bool(employed) and
                                   employed.get("low", 0) <= len(placed) <= employed.get("high", 0),
                "method_the_model_used": employed.get("method"),
                "why_this_is_not_a_job_finished":
                    "The model's band is a SIZE struck against a town of 2,353-3,265 "
                    "people; the layer holds a different number of cards and the model's "
                    "own open question says the 1840 industry columns have no row for "
                    "domestic service at all. A figure inside a range is where the "
                    "argument starts.",
            },
            "people_the_layer_gives_a_trade": {
                "model_low": given_trade.get("low"),
                "model_high": given_trade.get("high"),
                "the_layer_gives_today": len(with_trade),
                "note": "The model's figure was struck before the reconstruction bands "
                        "ran. The layer gives more people a trade than it did; the model "
                        "re-cuts from the layer and will carry it when it next does.",
            },
        },
        "what_this_does_not_do": {
            "the_business_side_is_T-1462s":
                "Nothing is written onto a business record here. `staff[]` stays as the "
                "register left it, and the order book's employment buckets stay unfilled "
                "until T-1459's re-cut lets the mint run.",
            "it_supplies_no_trade":
                f"{_tally(rows, 'status').get('no_trade_recorded', 0)} people carry no "
                "trade and leave here carrying none. Reading one in from the household "
                "would be the reconstruction doing by inference what its own stages do "
                "under a quota.",
            "it_re_decides_nothing":
                "Every answer is already implied by a committed file. T-1432's join, "
                "T-1433's seating, the business register's own proprietors, partners "
                "and staff (T-1990), the by-name rulings on the attested trades (T-1994), "
                "the order book's printed counts (T-1996) and "
                "premises_rulings.json each keep their own words; "
                "this pass only guarantees that one of them reaches every card.",
        },
        "rows": rows,
    }


# ------------------------------------------------------------------- gates --

def verify(data: dict, coverage: dict, committed: dict) -> None:
    """The cover, asserted. Four ways it can be wrong and each is a failure, never a
    warning: a person with no answer, a person with two, an answer in a word the
    vocabulary does not hold, and a child at work. T-1990 added the register's word
    for a house whose record does not name the person; T-1993 adds another household's
    service claimed for a trade, or under a ruling, that does not give it."""
    rows = committed.get("rows") or []
    for trade, words in sorted(IN_ANOTHER_HOUSEHOLD.items()):
        ruling = data["rulings"].get(trade) or {}
        if ruling.get("premises") != "no_fixed_premises" or \
                words not in (ruling.get("basis") or ""):
            raise Fault(f"premises_rulings.json#{trade} no longer says the work is "
                        f"{words!r} at no fixed premises of its own, and T-1993 answers "
                        "that trade's overflow in those words. Re-rule here with it.")
    seen: dict = {}
    for row in rows:
        pid = row.get("person_id")
        if pid in seen:
            raise Fault(f"{pid} carries two employment answers. Every person gets one, "
                        "and a second is two files disagreeing about the same card.")
        seen[pid] = row
    layer = {person["id"] for _, _, person in data["people"]}
    missing = sorted(layer - set(seen))
    if missing:
        raise Fault(f"{len(missing)} people in the resident layer carry no employment "
                    f"answer — the first is {missing[0]}. A card with no answer is the "
                    "silence this pass exists to remove.")
    person_of = {person["id"]: person for _, _, person in data["people"]}
    held = shops_held(data)
    fossils = sorted(set(seen) - layer)
    if fossils:
        raise Fault(f"{len(fossils)} answers are carried for people the layer does not "
                    f"hold — the first is {fossils[0]}. A card that has been merged away "
                    "takes its answer with it.")
    for row in rows:
        status, reason = row.get("status"), row.get("reason")
        if status not in STATUSES:
            raise Fault(f"{row['person_id']} carries the status {status!r}, which is in "
                        "no vocabulary this gate holds")
        if reason not in STATUSES[status]:
            raise Fault(f"{row['person_id']} carries {status!r} with the reason "
                        f"{reason!r}, which that status does not admit")
        if reason == "in_service_in_another_household" and (
                row.get("trade") not in IN_ANOTHER_HOUSEHOLD or row.get("houses")):
            raise Fault(f"{row['person_id']} carries {reason!r} at the trade "
                        f"{row.get('trade')!r}{' and a house' if row.get('houses') else ''}"
                        ". Only a trade the premises ruling gives in another household's "
                        "house may say so, and saying so names no house of trade.")
        if row.get("age_scope") not in AGE_SCOPES:
            raise Fault(f"{row['person_id']} carries the age scope "
                        f"{row.get('age_scope')!r}, which is in no vocabulary here")
        if row["age_scope"] == "below_working_age" and status in PLACED:
            raise Fault(f"{row['person_id']} is below the staffing model's working-age "
                        f"floor and is placed at work as {status!r}. A child in a shop is "
                        "either a wrong age band or a wrong seat, and both are faults.")
        for house in row.get("houses") or []:
            if house not in data["businesses"]:
                raise Fault(f"{row['person_id']} is placed at {house!r}, which the "
                            "business layer does not hold")
            if reason in REGISTER_REASONS:
                record = data["businesses"][house]
                named = {r.get("person_id") for side in REGISTER_KEEPS + REGISTER_STAFF
                         for r in record.get(side) or [] if isinstance(r, dict)}
                if row["person_id"] not in named:
                    raise Fault(f"{row['person_id']} is placed at {house!r} on the "
                                f"register's word ({reason}), and that record names "
                                "nobody of the id. The register answer is the record's "
                                "own row or it is nothing.")
        if reason == SHOPS_REASON:
            person = person_of.get(row["person_id"]) or {}
            klass = (data["rulings"].get(row.get("trade")) or {}).get("census_class")
            if person.get("grade") != SHOPS_GRADE:
                raise Fault(f"{row['person_id']} is graded {person.get('grade')!r} and is "
                            "told the mechanics' shops are past their count. A person a "
                            "source knows is ruled on by name or left owed.")
            if klass != SHOPS_CLASS or row.get("trade") not in held["trades_it_counts"]:
                raise Fault(f"{row['person_id']} at {row.get('trade')!r} (census class "
                            f"{klass!r}) is set against the American's twenty-five, which "
                            "counts only the mechanic trades the census never counted.")
            if not held["at_the_count"]:
                raise Fault(f"{row['person_id']} is told the mechanics' shops are past "
                            f"their count, and the register prints only "
                            f"{held['register_printed_houses']} of the {SHOPS_COUNT}. A "
                            "count still short owes the house.")
        if reason == HOLD_REASON and (
                (row["person_id"], row.get("trade")) not in (data.get("identity_holds") or {})
                or row.get("houses")):
            raise Fault(f"{row['person_id']} is said to be held on an identity question at "
                        f"{row.get('trade')!r}, and premises_rulings.json#identity_holds "
                        "holds no such person and trade. A hold is the ruling's or nothing.")
        if reason == HELD_REASON:
            person = person_of.get(row["person_id"]) or {}
            if person.get("grade") != HELD_GRADE:
                raise Fault(f"{row['person_id']} is graded {person.get('grade')!r} and is "
                            "told the printed count is held. A documented person's own "
                            "house is what would retire a reconstructed one from that "
                            "count; they are ruled on by name or left owed.")
            klass = (data["rulings"].get(row.get("trade")) or {}).get("census_class")
            bucket = (data.get("buckets") or {}).get(klass)
            if bucket is None or not bucket_full(bucket):
                raise Fault(f"{row['person_id']} is told the printed count of "
                            f"{klass!r} is held, and the order book "
                            + ("has no bucket for it" if bucket is None else
                               f"still orders {bucket.get('to_reconstruct')} with "
                               f"{bucket.get('filled') or 0} filled")
                            + ". A count still short owes the house.")


# ---------------------------------------------------------------- commands --

def cmd_build() -> int:
    data = load()
    coverage = derive(data)
    doc = report(data, coverage)
    verify(data, coverage, doc)
    COVERAGE_OUT.parent.mkdir(parents=True, exist_ok=True)
    COVERAGE_OUT.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n",
                            encoding="utf-8")
    counts = doc["counts"]
    print(f"OK: the 1835 employment coverage — {counts['people']} people answered, "
          f"{counts['placed_at_work']} placed at work, "
          f"{counts['people'] - counts['placed_at_work']} carrying a stated reason "
          f"they are not; {counts['working_age']} of working age and none of them "
          "left silent; nobody minted, no trade supplied")
    return 0


def cmd_check() -> int:
    if not COVERAGE_OUT.exists():
        raise Fault(f"{COVERAGE_OUT.relative_to(ROOT)} has never been built")
    data = load()
    coverage = derive(data)
    was = json.loads(COVERAGE_OUT.read_text(encoding="utf-8"))
    now = report(data, coverage)
    verify(data, coverage, was)
    if json.dumps(was, sort_keys=True) != json.dumps(now, sort_keys=True):
        raise Fault(f"{COVERAGE_OUT.relative_to(ROOT)} no longer re-derives — run "
                    "tools/employment_coverage_1835.py --build")
    print(f"OK: all {now['counts']['people']} people in the resident layer re-derive to "
          "the one employment answer the join carries, and none of them to none")
    return 0


def _fires(what: str, thunk) -> None:
    try:
        thunk()
    except Fault:
        return
    raise Fault(f"the guard against {what} did not fire")


def cmd_self_test() -> int:
    data = load()
    coverage = derive(data)
    committed = report(data, coverage)

    def silent():
        bent = json.loads(json.dumps(committed))
        bent["rows"].pop()
        verify(data, coverage, bent)
    _fires("a person left with no employment answer", silent)

    def doubled():
        bent = json.loads(json.dumps(committed))
        bent["rows"].append(json.loads(json.dumps(bent["rows"][0])))
        verify(data, coverage, bent)
    _fires("a person carrying two answers", doubled)

    def fossil():
        bent = json.loads(json.dumps(committed))
        row = json.loads(json.dumps(bent["rows"][0]))
        row["person_id"] = "nobody_this_town_holds"
        bent["rows"].append(row)
        verify(data, coverage, bent)
    _fires("an answer carried for a card the layer does not hold", fossil)

    def bad_word():
        bent = json.loads(json.dumps(committed))
        bent["rows"][0]["status"] = "gainfully_occupied"
        verify(data, coverage, bent)
    _fires("a status in a word the vocabulary does not hold", bad_word)

    def mismatched():
        bent = json.loads(json.dumps(committed))
        bent["rows"][0]["status"] = "no_trade_recorded"
        bent["rows"][0]["reason"] = "named_by_a_source"
        verify(data, coverage, bent)
    _fires("a status carrying a reason it does not admit", mismatched)

    def child_at_work():
        bent = json.loads(json.dumps(committed))
        row = next((r for r in bent["rows"] if r["age_scope"] == "below_working_age"), None)
        if row is None:
            raise Fault("the self-test found nobody below the working-age floor")
        row["status"] = "at_a_named_house"
        row["reason"] = "named_by_a_source"
        verify(data, coverage, bent)
    _fires("a child below the model's floor placed in a shop", child_at_work)

    def register_house_not_named():
        bent = json.loads(json.dumps(committed))
        row = next((r for r in bent["rows"] if r["reason"] in REGISTER_REASONS), None)
        if row is None:
            raise Fault("the self-test found nobody the business register places")
        other = next(b for b in sorted(data["businesses"]) if b not in row["houses"]
                     and row["person_id"] not in json.dumps(data["businesses"][b]))
        row["houses"] = [other]
        verify(data, coverage, bent)
    _fires("a register answer naming a house whose record does not name the person",
           register_house_not_named)

    def servant_at_a_forge():
        bent = json.loads(json.dumps(committed))
        # Any row at a trade with no house that is not already in service: since T-1995
        # emptied `class_held_no_house` of its tradesmen, the domestics were all it held.
        row = next(r for r in bent["rows"]
                   if r["status"] == "at_a_trade_with_no_house_to_join"
                   and r["reason"] != "in_service_in_another_household")
        row["reason"] = "in_service_in_another_household"
        row["trade"] = "blacksmith"
        verify(data, coverage, bent)
    _fires("another household's service claimed for a trade the ruling keeps in a shop",
           servant_at_a_forge)

    def ruling_moved():
        bent = dict(data)
        bent["rulings"] = {**data["rulings"], "domestic": {
            **data["rulings"]["domestic"], "premises": "own_premises"}}
        verify(bent, coverage, committed)
    _fires("the domestic ruling changing under T-1993's answer", ruling_moved)

    def unreadable_band():
        band_bounds("middle-aged")
    _fires("an age band in a form this pass cannot read", unreadable_band)

    def stale_ruling():
        bent = dict(data)
        other = next(r["person_id"] for r in coverage["rows"]
                     if r["reason"] == "no_trade_recorded")
        ruling = next(iter(data["attested_houses"].values()), None)
        if ruling is None:
            raise Fault("the self-test found no T-1994 ruling to bend")
        bent["attested_houses"] = {other: {**ruling, "person_id": other}}
        derive(bent)
    _fires("a T-1994 ruling applied to a person it was not made against", stale_ruling)

    def join_to_nothing():
        ruling = next((r for r in data["attested_houses"].values()
                       if r.get("answer") == "joined"), None)
        if ruling is None:
            raise Fault("the self-test found no T-1994 join to bend")
        attested_answer({**ruling, "house": "biz_no_such_house"}, data["businesses"])
    _fires("a T-1994 join naming a house the register does not hold", join_to_nothing)

    def owed_by_fiat():
        ruling = next(r for r in data["attested_houses"].values()
                      if r.get("answer") == "none_owed")
        attested_answer({**ruling, "reason": "because_we_said_so"}, data["businesses"])
    _fires("a T-1994 none-owed answer in a reason outside its four", owed_by_fiat)

    def keeper_told_none_owed():
        keeper = next((r for r in data["attested_houses"].values()
                       if r.get("replaces") == "keeps_their_own_house"), None)
        if keeper is None:
            raise Fault("the self-test found no T-2001 keeper's join to bend")
        none_owed = next(r for r in data["attested_houses"].values()
                         if r.get("answer") == "none_owed")
        bent = dict(data)
        bent["attested_houses"] = {**data["attested_houses"], keeper["person_id"]: {
            **none_owed, "person_id": keeper["person_id"],
            "replaces": "keeps_their_own_house"}}
        derive(bent)
    _fires("a documented keeper told by a by-name ruling that none is owed",
           keeper_told_none_owed)

    def shops_on_a_documented_person():
        bent = json.loads(json.dumps(committed))
        row = next(r for r in bent["rows"] if r["reason"] == SHOPS_REASON)
        documented = next(p for _, _, p in data["people"]
                          if p.get("grade") not in (SHOPS_GRADE, None))
        bent["rows"] = [r for r in bent["rows"] if r["person_id"] != documented["id"]]
        row["person_id"] = documented["id"]
        verify(data, coverage, bent)
    _fires("a documented person told the mechanics' shops are past their count",
           shops_on_a_documented_person)

    def shops_short_of_the_count():
        bent = dict(data)
        bent["businesses"] = {k: v for k, v in data["businesses"].items()
                              if v.get("provenance") != SHOPS_COUNTED_PROVENANCE}
        verify(bent, coverage, committed)
    _fires("the shop answer against a register short of the twenty-five",
           shops_short_of_the_count)

    def shops_at_a_counted_class():
        bent = json.loads(json.dumps(committed))
        row = next(r for r in bent["rows"] if r["reason"] == SHOPS_REASON)
        row["trade"] = "grocer"
        verify(data, coverage, bent)
    _fires("the American's count spent on a class the census counts",
           shops_at_a_counted_class)

    def hold_by_fiat():
        bent = dict(data)
        bent["identity_holds"] = {}
        verify(bent, coverage, committed)
    _fires("an identity hold the premises ruling does not carry", hold_by_fiat)

    def held_on_a_documented_person():
        bent = json.loads(json.dumps(committed))
        row = next((r for r in bent["rows"] if r["reason"] == HELD_REASON), None)
        if row is None:
            raise Fault("the self-test found nobody the printed count holds")
        documented = next(p for _, _, p in data["people"]
                          if p.get("grade") not in (HELD_GRADE, None))
        bent["rows"] = [r for r in bent["rows"] if r["person_id"] != documented["id"]]
        row["person_id"] = documented["id"]
        verify(data, coverage, bent)
    _fires("a documented person told the printed count is held", held_on_a_documented_person)

    def held_against_a_short_count():
        row = next(r for r in committed["rows"] if r["reason"] == HELD_REASON)
        klass = data["rulings"][row["trade"]]["census_class"]
        short = {**data["buckets"][klass], "to_reconstruct": 99, "filled": 0}
        bent_data = {**data, "buckets": {**data["buckets"], klass: short}}
        verify(bent_data, coverage, committed)
    _fires("a held-count answer against a bucket still short", held_against_a_short_count)

    print("OK: all twenty assertions of the employment coverage fire when broken")
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
    except Fault as err:
        print(f"FAIL: {err}", file=sys.stderr)
        return 1
    ap.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
