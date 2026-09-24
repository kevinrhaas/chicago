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
                                     is OWED rather than absent.
  `at_a_trade_with_no_house_to_join` they carry a trade and the business layer holds no
                                     house this project may join them to. Four reasons,
                                     each somebody else's ticket to close.
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

#: The five statuses, and for each the reasons it may carry. A status is never written
#: without a reason: "he is not at work" is not an answer, "the layer records no trade
#: for him" is. Closed here and asserted against in `verify`.
STATUSES = {
    "at_a_named_house": ("named_by_a_source",),
    "at_a_seat_this_project_drew": ("seated_by_the_staffing_model",),
    "on_their_own_account": ("keeps_their_own_house",),
    "at_a_trade_with_no_house_to_join": (
        "no_employer_named", "class_held_no_house",
        "trade_attested_no_house_named", "no_ruling_on_the_trade"),
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
    "trade_attested_no_house_named":
        "The sources name this person's trade and name no house for it. Drawing one "
        "would put a man the record knows into a shop nobody put him in, so no seat is "
        "drawn and the absence is carried instead.",
    "no_ruling_on_the_trade":
        "`premises_rulings.json` has never ruled on this trade, so whether it kept "
        "premises of its own is unanswered. T-1404 owns the ruling; until it is made "
        "this pass says so rather than guessing at it.",
    "no_trade_recorded":
        "No source records a trade for this person and no reconstruction stage has given "
        "them one. This is a statement about the evidence and not about the person: a "
        "trade is not read in from the household, and none is supplied here.",
}

AGE_SCOPES = ("working_age", "below_working_age", "age_is_not_settled")


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
    for path in sorted(BUSINESSES.glob("*.json")):
        if path.name == "index.json":
            continue
        record = _load_json(path)
        for row in (record.get("businesses") if isinstance(record, dict)
                    and "businesses" in record
                    else (record if isinstance(record, list) else [record])):
            if isinstance(row, dict) and row.get("id"):
                businesses[row["id"]] = row
    seating = _load_json(SEATING)
    return {
        "people": people,
        "businesses": businesses,
        "seating": {row["person_id"]: row for row in seating.get("rows") or []},
        "seating_ticket": seating.get("ticket"),
        "rulings": {r["occupation"]: r for r in _load_json(PREMISES_RULINGS)["rulings"]},
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


#: T-1433's five kinds, mapped onto this pass's answers. The mapping is the whole of what
#: this pass says about those 524 people: it re-words nothing and re-decides nothing.
FROM_SEATING = {
    "seated": ("at_a_seat_this_project_drew", "seated_by_the_staffing_model"),
    "keeps_their_own_house": ("on_their_own_account", "keeps_their_own_house"),
    "class_held_no_house": ("at_a_trade_with_no_house_to_join", "class_held_no_house"),
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
        return {
            "status": status,
            "reason": reason,
            "decided_by": f"reconstructed_seating.json#{kind}, drawn by "
                          f"{context['seating_ticket']}",
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


def derive(data: dict) -> dict:
    floor = working_age_floor(data["model"])["floor"]
    context = {"seating": data["seating"], "rulings": data["rulings"],
               "seating_ticket": data["seating_ticket"]}
    rows = []
    for folder, household, person in data["people"]:
        occupation = person.get("occupation") or {}
        band = person.get("age_band")
        band = band.get("value") if isinstance(band, dict) else band
        block = answer(person, context)
        rows.append({
            "person_id": person["id"],
            "household_id": household.get("id"),
            "record_folder": folder,
            "age_band": band,
            "age_scope": age_scope(band, floor),
            "trade": (occupation.get("value")
                      if occupation.get("value") not in NOT_A_TRADE else None),
            "trade_confidence": occupation.get("confidence"),
            **block,
        })
    rows.sort(key=lambda r: r["person_id"])
    return {"rows": rows, "floor": floor}


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
            "data/businesses/*.json",
            "data/businesses/rulings/premises_rulings.json",
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
                "T-1433's seating and premises_rulings.json each keep their own words; "
                "this pass only guarantees that one of them reaches every card.",
        },
        "rows": rows,
    }


# ------------------------------------------------------------------- gates --

def verify(data: dict, coverage: dict, committed: dict) -> None:
    """The cover, asserted. Four ways it can be wrong and each is a failure, never a
    warning: a person with no answer, a person with two, an answer in a word the
    vocabulary does not hold, and a child at work."""
    rows = committed.get("rows") or []
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

    def unreadable_band():
        band_bounds("middle-aged")
    _fires("an age band in a form this pass cannot read", unreadable_band)

    print("OK: all seven assertions of the employment coverage fire when broken")
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
