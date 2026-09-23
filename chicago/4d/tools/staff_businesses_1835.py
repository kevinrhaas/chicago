#!/usr/bin/env python3
"""THE STAFFING JOIN, ATTESTED AND INFERRED HALF: where the named people worked.

T-1432, piece 1 of 3 of T-1189.

    tools/staff_businesses_1835.py --build       write persons[].workplaces and the report
    tools/staff_businesses_1835.py --check       re-derive, refuse drift, assert the join
    tools/staff_businesses_1835.py --self-test   the guards, fired on the real join

THE GAP THIS CLOSES. The business layer names 196 people across its records —
proprietors, partners and, so far, one apprentice — and 144 of those rows carry a
`person_id`, 110 distinct town cards between them. So the register knows where
those people worked. **Their own cards did not.** `persons[]` has never held a
workplace at all; `works_at` existed only on the HOUSEHOLD, where it is a singular,
undated structure id — a PLACE. A man who kept a store and a card that said nothing
about a store were the same person read from two ends, with nothing holding the two
ends together. This tool writes the join down on the person's side and puts a gate
on it, so the two ends can no longer drift apart in silence.

WHAT IT IS NOT. It mints nobody, reads no page of any source, and invents no
employment. Every row it writes is a row the business layer already carries,
carried across at ITS OWN tier with ITS OWN basis, source and claim ids. An
`inferred` hand joins as `inferred`; nothing is upgraded by being copied. The
reconstructed residents who have a trade and no workplace are T-1433's, and the
shortfall against the staffing model — the clerks and journeymen the model says the
town's houses employed and no source names — is T-1434's. Both are named in the
report so the gap stays visible rather than reading as a finished job.

A PRINTED NAME WITH NO CARD IS A STATEMENT ABOUT THE EVIDENCE. 53 of the layer's
person rows carry `person_id: null` — a name the register could not match to a town
card. They are counted in the report and they are never invented into one. Writing a
card for "Brewster" because a notice printed "Brewster, Hogan & Co." is exactly the
move this project refuses.

WHY THE FIELD IS `workplaces` AND NOT `works_at`, WHICH IS WHAT T-1189 ASKED FOR.
`works_at` is already taken, and it means something else: on a household it is a
SINGULAR, UNDATED structure id — the building — and `tools/validate.py` and
`tools/associations.py` both police it as one, on persons as well as on households.
A list of dated employments under that name would have read as a second opinion about
the same field, and the gate would have refused it as a malformed link. So the place a
person WORKED keeps its word, and the firms they worked FOR get their own: one entry a
(house, role), dated, graded and cited. The two answer different questions and now say
so.

THE JOIN IS BIDIRECTIONAL AND THE GATE ASSERTS IT BOTH WAYS. A `workplaces` entry with
no business record naming that person back in that role is a fossil, and a named row
with no entry is a person whose card has quietly lost their trade. Either one is a
failure here; neither is a warning.

AND SINCE T-1462, `workplaces` IS THE ATTESTED AND INFERRED HALF AND SAYS SO. That
ticket wrote the 124 reconstructed seats T-1433 drew onto the business records, which
is where the houses needed them; this tool does not carry them back onto the cards. A
`workplaces` row means a source puts this person in this house, and a drawn seat is not
that — its person-side record is data/residents/reconstructed_seating.json, under its
own gate. The practical half of the reason is the write set: three fifths of the seated
people stand in `reconstructed_trades/`, `lodgers/` and the other mint-owned
directories, each re-derived whole by its own mint and refusing a differing byte, so a
foreign key there needs the carry tools/resident_mint_carry.py does for `households/`.
Writing it for the 33 inside `households/` alone would make one seat read as a
workplace and the identical seat next door read as nothing.

WHAT IT RESOLVES AGAINST IS THE WHOLE LAYER, THOUGH. A business row may name a person
in any of the seven card directories, and `person_cards` reads all seven — the write
set is one directory and the resolve set is the town.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BUSINESSES = ROOT / "data" / "businesses"
HOUSEHOLDS = ROOT / "data" / "residents" / "households"
RESIDENTS_ROOT = ROOT / "data" / "residents"

#: Every directory of the resident layer that holds cards, in the reading
#: compile_businesses.py and employment_coverage_1835.py both already take. A
#: business row may name a person in any of them — the reconstruction programme
#: writes its people BESIDE `households/` because the research mints re-derive it —
#: and a join that could only RESOLVE a name in `households/` refused the town's own
#: cards as danglers the moment T-1462 put a reconstructed hand on a record.
RESIDENT_CARD_DIRS = ("households", "merged", "readmitted", "reconstructed_trades",
                      "lodgers", "transients", "underdocumented")
BUSINESS_SCHEMA = ROOT / "data" / "businesses.schema.json"
RESIDENT_INDEX = ROOT / "data" / "residents" / "index.json"
STAFFING_MODEL = ROOT / "data" / "reconstruction" / "1835_business_staffing_model.json"
REPORT_OUT = ROOT / "data" / "reconstruction" / "1835_staffing_join.json"

SCENE_DATE = "1835-07-01"
TICKET = "T-1432"
PARENT_TICKET = "T-1189"

#: The three lists on a business record that name people, in the order the schema
#: carries them. `staff` is the one T-1189 fills; the other two the register wrote.
PEOPLE_KEYS = ("proprietors", "partners", "staff")

#: Every key a `workplaces` entry carries, in the order it is written. The shape is
#: fixed here rather than in the renderer so a card and a gate read the same row.
ENTRY_KEYS = ("business_id", "business_name", "role", "printed_as", "from", "to",
              "tier", "basis", "source_id", "claim_ids",
              "business_present_at_scene_date")

#: WHERE THE LIST SITS ON THE PERSON, AND WHY IT IS A FIXED SLOT. Immediately after
#: `occupation`, so a reader meets the trade and the place together — and, more to the
#: point, so the four mints can put it back in the same place. A mint rebuilds its card
#: whole and `tools/resident_mint_carry.py` carries the foreign keys back; anything it
#: appends at the TAIL lands after the keys that other passes pop and re-append, and
#: reads as drift on every card by turns. `dated_bounds` and `appearance_bounds` were
#: each given a fixed slot for exactly this, at T-1326 and T-1337. This is the third.
AFTER_KEYS = ("occupation", "roles")


class Fault(Exception):
    """A refusal, printed and exited on. Never a warning."""


# ------------------------------------------------------------------ reading --

def load() -> dict:
    if not BUSINESSES.is_dir():
        raise Fault("the business layer is missing")
    if not HOUSEHOLDS.is_dir():
        raise Fault("the residents layer is missing")
    # `index.json` is the compiled manifest compile_businesses.py writes over the
    # records; it is not one of them, and reading it as one is how a join gains a
    # 198th house with no id.
    businesses = [json.loads(p.read_text(encoding="utf-8"))
                  for p in sorted(BUSINESSES.glob("*.json")) if p.name != "index.json"]
    if not businesses:
        raise Fault("the business layer holds no records")
    households = []
    for path in sorted(HOUSEHOLDS.glob("*.json")):
        households.append((path, json.loads(path.read_text(encoding="utf-8"))))
    if not households:
        raise Fault("the residents layer holds no household records")
    # THE CARDS A NAME MAY RESOLVE TO AND THE CARDS THIS TOOL WRITES ARE TWO SETS,
    # and they became two sets at T-1462. `households` is what gets `workplaces`
    # written onto it; `all_cards` is every id the resident layer holds anywhere, and
    # it exists so that a business row naming a reconstructed trade-holder resolves
    # instead of reading as a dangling link. The write set is deliberately unchanged:
    # the other six directories are re-derived whole by their own mints, and a foreign
    # key on one of those cards needs that mint to carry it back.
    all_cards = []
    for folder in RESIDENT_CARD_DIRS:
        folder_path = RESIDENTS_ROOT / folder
        if not folder_path.is_dir():
            continue
        for path in sorted(folder_path.glob("*.json")):
            all_cards.append((path, json.loads(path.read_text(encoding="utf-8"))))
    schema = json.loads(BUSINESS_SCHEMA.read_text(encoding="utf-8"))
    index = json.loads(RESIDENT_INDEX.read_text(encoding="utf-8"))
    return {
        "businesses": businesses,
        "households": households,
        "all_cards": all_cards,
        "roles": list(schema["$defs"]["role"]["enum"]),
        "tiers": list(schema["$defs"]["tier"]["enum"]),
        "vocabulary": index["vocabulary"],
    }


def person_cards(households) -> dict:
    """Every person id the residents layer holds, to the household that holds it."""
    cards = {}
    for path, hh in households:
        for person in hh.get("persons") or []:
            pid = person.get("id")
            if pid:
                cards[pid] = (path.name, hh.get("id"), person.get("name"))
    return cards


# ----------------------------------------------------------------- deriving --

def entry(business: dict, row: dict) -> dict:
    """One workplace, as the business record already states it. Nothing is added."""
    return {
        "business_id": business["id"],
        "business_name": business.get("name"),
        "role": row.get("role"),
        # THE PRINTED NAME IS EVIDENCE and it is not always the card's name: the
        # register matched "Wm. Brewster" to brewster_william and the setting is
        # what a reader can check the match against.
        "printed_as": row.get("name"),
        "from": row.get("from"),
        "to": row.get("to"),
        # NOT UPGRADED BY BEING COPIED. The row's own tier travels with it.
        "tier": row.get("tier"),
        "basis": row.get("basis"),
        "source_id": row.get("source_id"),
        "claim_ids": list(row.get("claim_ids") or []),
        # The record's own field, carried so a card can say "not trading on
        # 1 July" without a second fetch. It is about the HOUSE, not the person.
        "business_present_at_scene_date": bool(business.get("present_at_scene_date")),
    }


def fold(entries: list) -> list:
    """One entry per (business, role). A person named twice in one role at one
    house is one employment, and the widest bracket and every claim id are kept —
    the register printed some partners under two styles and T-1401 folded those in
    the data, but a fold that only works because the data was already folded is a
    fold that fails the day it is needed."""
    by_key: dict = {}
    for row in entries:
        key = (row["business_id"], row["role"])
        had = by_key.get(key)
        if not had:
            by_key[key] = row
            continue
        if row["from"] and (not had["from"] or row["from"] < had["from"]):
            had["from"] = row["from"]
        if row["to"] and (not had["to"] or row["to"] > had["to"]):
            had["to"] = row["to"]
        for claim in row["claim_ids"]:
            if claim not in had["claim_ids"]:
                had["claim_ids"].append(claim)
        had["claim_ids"].sort()
    return [by_key[k] for k in sorted(by_key)]


def derive(data: dict) -> dict:
    """The join, from the business layer alone. Deterministic and order-free."""
    cards = person_cards(data["all_cards"])
    roles = set(data["roles"])
    tiers = set(data["tiers"])
    by_person: dict = {}
    named_rows = 0
    seats_not_carried = 0
    unresolved: dict = {}
    staffed_ids = []
    for business in data["businesses"]:
        has_person = False
        for key in PEOPLE_KEYS:
            for row in business.get(key) or []:
                named_rows += 1
                if row.get("role") not in roles:
                    raise Fault(f"{business['id']}/{key}: role '{row.get('role')}' is not one "
                                f"the businesses schema holds")
                if row.get("tier") not in tiers:
                    raise Fault(f"{business['id']}/{key}: tier '{row.get('tier')}' is not one "
                                f"the grade ladder holds")
                pid = row.get("person_id")
                if not pid:
                    # A NAME THE REGISTER COULD NOT MATCH. Counted, never invented.
                    unresolved.setdefault(business["id"], []).append(row.get("name"))
                    continue
                if pid not in cards:
                    raise Fault(f"{business['id']}/{key}: person_id '{pid}' names no town "
                                f"card — the business layer and the residents layer disagree")
                has_person = True
                if row.get("tier") == "reconstructed":
                    # A RECONSTRUCTED SEAT IS RECORDED ON THE PERSON'S SIDE ALREADY, AND
                    # NOT HERE (T-1462). `workplaces` is the list of houses a SOURCE puts
                    # a person in, and the 124 seats T-1433 drew are not that: their
                    # person-side record is data/residents/reconstructed_seating.json,
                    # which re-derives under its own gate and says, for every one of
                    # them, which term of the order rule seated them where.
                    #
                    # THE REASON IT IS NOT SIMPLY BOTH. Three fifths of the seated people
                    # stand in `reconstructed_trades/`, `lodgers/` and the other mint-owned
                    # directories, each of which its own mint re-derives WHOLE and refuses
                    # a differing byte of. Writing a foreign key onto one of those cards
                    # needs that mint to carry it back the way tools/resident_mint_carry.py
                    # carries it for `households/`, and that is a piece of work with its
                    # own acceptance. Writing it onto the 33 in `households/` and not the
                    # 91 outside it would be worse than not writing it: the same seat
                    # would read as a workplace or as nothing at all depending on which
                    # directory the mint happened to put the person in.
                    seats_not_carried += 1
                    continue
                by_person.setdefault(pid, []).append(entry(business, row))
        if has_person:
            staffed_ids.append(business["id"])
    return {
        "by_person": {pid: fold(rows) for pid, rows in sorted(by_person.items())},
        "named_rows": named_rows,
        "reconstructed_seats_not_carried": seats_not_carried,
        "unresolved": {k: sorted(v) for k, v in sorted(unresolved.items())},
        "businesses_with_people": sorted(staffed_ids),
        "businesses": [b["id"] for b in data["businesses"]],
        "cards": cards,
    }



# --------------------------------------------------- what the join asks back --

def name_parts(name: str) -> tuple:
    """(forename-ish tokens, surname) off a printed or card name, punctuation and
    the project's bracketed editorial marks removed. Deliberately crude: it is used
    only to RAISE A QUESTION, never to settle one."""
    text = str(name or "")
    while "[" in text and "]" in text:
        text = text[:text.index("[")] + text[text.index("]") + 1:]
    # THE REGISTER PRINTS BOTH WAYS ROUND. "Curtiss, L. G." is a directory setting of
    # the same name as "L. G. Curtiss", and reading the comma as a space turns a
    # surname into a forename and invents a disagreement that is not there.
    inverted = "," in text
    words_ = [t.strip(".,;:()'\u2019") for t in text.replace(",", " ").split()]
    words_ = [t for t in words_ if t and t[0].isalpha()]
    if len(words_) < 2:
        return ((), words_[0].lower() if words_ else "")
    if inverted:
        return (tuple(t.lower() for t in words_[1:]), words_[0].lower())
    return (tuple(t.lower() for t in words_[:-1]), words_[-1].lower())


def middle_initials(printed: str) -> tuple:
    """The middle tokens of a printed name, as initials. 'Wm. H. Taylor' -> ('h',)."""
    fore, _ = name_parts(printed)
    return tuple(t[0] for t in fore[1:])


def questions(join: dict) -> list:
    """WHAT THE JOIN ASKS BACK, and it asks rather than answers.

    Putting a card's own name beside every name the register printed for it is the
    first time the two have stood in one place, and two mechanical disagreements fall
    out at once: a card that carries no middle initial where every printing of it
    carries one, and printings that disagree with each OTHER about the initial. Both
    are questions about identity, which is not this tool's licence — it carries rows
    across, it does not re-match anybody. They are counted here, named, and handed to
    T-1190, which is the ticket that converges the layer by id.
    """
    out = []
    for pid, rows in join["by_person"].items():
        card = join["cards"].get(pid)
        if not card:
            continue
        card_fore, card_sur = name_parts(card[2] or "")
        printings = sorted({r["printed_as"] for r in rows if r.get("printed_as")})
        if not printings or not card_sur:
            continue
        mids = [middle_initials(x) for x in printings]
        every_printing_has_a_middle = all(m for m in mids)
        card_has_a_middle = bool(card_fore[1:])
        disagree = sorted({m[0] for m in mids if m})
        flags = []
        if every_printing_has_a_middle and not card_has_a_middle:
            flags.append("every printing of this name carries a middle initial and the card "
                         "carries none")
        if len(disagree) > 1:
            flags.append("the printings disagree about the middle initial: "
                         + ", ".join(sorted(x.upper() + "." for x in disagree)))
        # A FORENAME IS NOT COMPARED AT ALL, and that is deliberate. The period spells
        # one man Wm., William and Will. in three notices, and a rule that read those
        # as three men would bury the two real questions above in fifty false ones.
        # Initials are mechanical; spelling is a reading, and readings are T-1190's.
        if flags:
            out.append({
                "person_id": pid,
                "the_card_reads": card[2],
                "the_register_printed": printings,
                "houses": sorted({r["business_id"] for r in rows}),
                "what_disagrees": flags,
            })
    return sorted(out, key=lambda r: r["person_id"])


# ------------------------------------------------------------------ writing --

def place(person: dict, entries: list) -> dict:
    """Return the person with `workplaces` set — beside the roles, not tacked on the
    end — or with it removed where this join gives them none."""
    out: dict = {}
    placed = False
    after = next((k for k in AFTER_KEYS if k in person), None)
    for key, value in person.items():
        if key == "workplaces":
            continue
        out[key] = value
        if entries and not placed and key == after:
            out["workplaces"] = entries
            placed = True
    if entries and not placed:
        out["workplaces"] = entries
    return out


def apply_to_households(data: dict, join: dict) -> list:
    """The households as they should stand, as (path, text) pairs."""
    out = []
    for path, hh in data["households"]:
        rebuilt = dict(hh)
        rebuilt["persons"] = [place(p, join["by_person"].get(p.get("id")) or [])
                              for p in (hh.get("persons") or [])]
        out.append((path, json.dumps(rebuilt, indent=1, ensure_ascii=False) + "\n"))
    return out


# ------------------------------------------------------------------- report --

def report(data: dict, join: dict) -> dict:
    by_role: dict = {}
    by_tier: dict = {}
    for rows in join["by_person"].values():
        for row in rows:
            by_role[row["role"]] = by_role.get(row["role"], 0) + 1
            by_tier[row["tier"]] = by_tier.get(row["tier"], 0) + 1
    asked = questions(join)
    model = json.loads(STAFFING_MODEL.read_text(encoding="utf-8"))
    dry = model["dry_run"]
    written = sum(len(v) for v in join["by_person"].values())
    without = [b for b in join["businesses"] if b not in set(join["businesses_with_people"])]
    return {
        "$schema_note": "DERIVED — regenerate with tools/staff_businesses_1835.py --build; "
                        "tools/check.sh re-derives it. Do not hand-edit.",
        "id": "1835_staffing_join",
        "ticket": TICKET,
        "parent_ticket": PARENT_TICKET,
        "target_date": SCENE_DATE,
        "generated_by": "tools/staff_businesses_1835.py --build",
        "not_a_reading": "an adjudication over committed files — no page of any source is "
                         "read here, and no person is written",
        "writes_no_person": True,
        "mints_nobody": True,
        "what_it_writes": "persons[].workplaces in data/residents/households/*.json — one entry "
                          "per (business, role) the business layer already names that person "
                          "in, carried at the business row's own tier, basis, source and claim "
                          "ids. Nothing is upgraded by being copied across.",
        "inputs": [
            "data/businesses/*.json",
            "data/residents/households/*.json",
            "data/reconstruction/1835_business_staffing_model.json",
        ],
        "counts": {
            "business_records": len(join["businesses"]),
            "person_rows_in_the_business_layer": join["named_rows"],
            "rows_carrying_a_person_id": written,
            "distinct_persons_tied_to_a_workplace": len(join["by_person"]),
            "businesses_with_at_least_one_named_person": len(join["businesses_with_people"]),
            "businesses_with_none": len(without),
            "town_cards": len(join["cards"]),
        },
        "by_role": [{"role": r, "entries": by_role[r]} for r in sorted(by_role)],
        "by_tier": {t: by_tier[t] for t in sorted(by_tier)},
        "unresolved_printed_names": {
            "what_this_is": "A person row the register could not match to a town card. The "
                            "printed name is the evidence and no card is invented for it; the "
                            "row keeps its place in the business record and joins nobody.",
            "rows": sum(len(v) for v in join["unresolved"].values()),
            "businesses": len(join["unresolved"]),
            "by_business": join["unresolved"],
        },
        "businesses_with_no_named_person": without,
        "questions_for_the_convergence": {
            "what_this_is": "The first time a card's own name has stood beside every name the "
                            "register printed for it. These are mechanical disagreements, not "
                            "refutations: this tool carries rows across at the identity the "
                            "business layer already asserted and re-matches nobody. T-1190 is "
                            "the ticket that converges the layer by id and they are its.",
            "cards": len(asked),
            "rows": asked,
        },
        "what_this_does_not_do": {
            "it_does_not_carry_the_reconstructed_seats_onto_the_cards": (
                f"T-1462 put {join['reconstructed_seats_not_carried']} reconstructed hands "
                "on the business records — the seats T-1433 drew — and this join leaves "
                "every one of them off `workplaces`. `workplaces` is the list of houses a "
                "SOURCE puts a person in; the seats' person-side record is "
                "data/residents/reconstructed_seating.json, which re-derives under its own "
                "gate and states, for each one, which term of the order rule seated them "
                "where. Three fifths of those people stand outside `households/` in "
                "directories their own mints re-derive whole, so carrying the key back "
                "needs those mints to carry it, and writing it for the minority that do "
                "stand in `households/` would make one seat read as a workplace and the "
                "next as nothing at all."),
            "the_shortfall_is_left_standing": (
                f"The staffing model implies {dry['staff_total']['low']}–"
                f"{dry['staff_total']['typical']}–{dry['staff_total']['high']} hands over "
                f"{dry['businesses_staffed']} houses. This join writes none of them: it "
                "carries across only what a source already names."),
            "T-1433": "Seats the reconstructed residents who have a trade and no workplace, "
                      "and gives the no-fixed-premises trades their employer or a casual "
                      "entry with its reason.",
            "T-1434": "Mints the shortfall to the model's typical band, gives every "
                      "working-age person a workplace or an explicit reason, and prints the "
                      "filled count on the business card and in the order book.",
        },
    }


# --------------------------------------------------------------- the refusals --

def verify(data: dict, join: dict, households) -> dict:
    """The join as it stands on disk, asserted BOTH ways. `households` is the
    (path, record) list to check — the real one, or a mutated copy in the
    self-test."""
    want = join["by_person"]
    seen: dict = {}
    for path, hh in households:
        for person in hh.get("persons") or []:
            rows = person.get("workplaces")
            if rows is None:
                continue
            if not isinstance(rows, list) or not rows:
                raise Fault(f"{path.name}/{person.get('id')}: workplaces is present and empty — "
                            "a person with no workplace carries no key at all")
            seen[person.get("id")] = rows
    # ONE: nothing on a card the register does not name back.
    for pid, rows in sorted(seen.items()):
        if pid not in want:
            raise Fault(f"{pid} carries workplaces and no business record names them — "
                        "the join has a fossil on it")
        if json.dumps(rows, sort_keys=True) != json.dumps(want[pid], sort_keys=True):
            raise Fault(f"{pid}'s workplaces no longer re-derive from the business layer — "
                        "run tools/staff_businesses_1835.py --build")
    # TWO: nothing named that the card has lost.
    for pid in sorted(want):
        if pid not in seen:
            raise Fault(f"{pid} is named in the business layer and their card carries no "
                        "workplaces — run tools/staff_businesses_1835.py --build")
    return seen


# ------------------------------------------------------------------ commands --

def cmd_build() -> int:
    data = load()
    join = derive(data)
    for path, text in apply_to_households(data, join):
        if path.read_text(encoding="utf-8") != text:
            path.write_text(text, encoding="utf-8")
    doc = report(data, join)
    REPORT_OUT.parent.mkdir(parents=True, exist_ok=True)
    REPORT_OUT.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n",
                          encoding="utf-8")
    c = doc["counts"]
    print(f"OK: the 1835 staffing join — {c['rows_carrying_a_person_id']} workplaces written "
          f"onto {c['distinct_persons_tied_to_a_workplace']} cards, over "
          f"{c['businesses_with_at_least_one_named_person']} of {c['business_records']} houses; "
          f"{doc['unresolved_printed_names']['rows']} printed names matched no card and "
          "stay unmatched, nobody minted")
    return 0


def cmd_check() -> int:
    if not REPORT_OUT.exists():
        raise Fault(f"{REPORT_OUT.relative_to(ROOT)} has never been built")
    data = load()
    join = derive(data)
    for path, text in apply_to_households(data, join):
        if path.read_text(encoding="utf-8") != text:
            raise Fault(f"data/residents/households/{path.name} no longer re-derives its "
                        "workplaces from the business layer — run "
                        "tools/staff_businesses_1835.py --build")
    verify(data, join, data["households"])
    doc = report(data, join)
    on_disk = json.loads(REPORT_OUT.read_text(encoding="utf-8"))
    if json.dumps(doc, sort_keys=True) != json.dumps(on_disk, sort_keys=True):
        raise Fault(f"{REPORT_OUT.relative_to(ROOT)} no longer re-derives from its inputs — "
                    "run tools/staff_businesses_1835.py --build")
    # THE ACCEPTANCE'S OWN LINE: this piece carries across, it does not mint. A
    # workplace on a card no business row names is the failure that would mean it
    # had started doing T-1434's job without T-1434's acceptance.
    c = doc["counts"]
    print(f"OK: the 1835 staffing join re-derives — {c['rows_carrying_a_person_id']} "
          f"workplaces on {c['distinct_persons_tied_to_a_workplace']} cards, joined both "
          f"ways, {doc['unresolved_printed_names']['rows']} printed names left unmatched")
    return 0


def cmd_self_test() -> int:
    fired = 0

    def fires(what, fn):
        nonlocal fired
        try:
            fn()
        except Fault:
            fired += 1
            return
        raise AssertionError(f"guard did not fire: {what}")

    data = load()
    join = derive(data)

    # THE DERIVATION IS ORDER-FREE AND BYTE-IDENTICAL TWICE OVER.
    assert json.dumps(derive(data)["by_person"], sort_keys=True) == json.dumps(
        join["by_person"], sort_keys=True)

    # NOTHING IS UPGRADED BY BEING COPIED. Every entry's tier is a tier some row of
    # the business layer carries for that person at that house.
    tiers_by_pair = {}
    for business in data["businesses"]:
        for key in PEOPLE_KEYS:
            for row in business.get(key) or []:
                if row.get("person_id"):
                    tiers_by_pair.setdefault(
                        (row["person_id"], business["id"], row["role"]), set()).add(row["tier"])
    for pid, rows in join["by_person"].items():
        for row in rows:
            assert row["tier"] in tiers_by_pair[(pid, row["business_id"], row["role"])], row

    # A PRINTED NAME WITH NO CARD JOINS NOBODY.
    assert join["unresolved"], "the layer holds unmatched printed names and this says so"
    for names in join["unresolved"].values():
        for name in names:
            assert name not in join["by_person"], name

    # THE FOLD KEEPS THE WIDEST BRACKET AND EVERY CLAIM ID.
    folded = fold([
        {"business_id": "biz_x", "role": "partner", "from": "1834-01-01", "to": "1834-06-01",
         "claim_ids": ["a"]},
        {"business_id": "biz_x", "role": "partner", "from": "1833-01-01", "to": "1835-06-01",
         "claim_ids": ["b", "a"]},
    ])
    assert len(folded) == 1 and folded[0]["from"] == "1833-01-01", folded
    assert folded[0]["to"] == "1835-06-01" and folded[0]["claim_ids"] == ["a", "b"], folded

    # THE FOUR MUTATIONS. Each is a way the join could rot in silence, and each
    # must stop the gate. They are applied to a COPY of the real records, so the
    # guards are fired against the town as it actually stands.
    def mutated(fn):
        copy = [(path, json.loads(json.dumps(hh))) for path, hh in data["households"]]
        fn(copy)
        return lambda: verify(data, join, copy)

    def first_with_work(copy):
        for _, hh in copy:
            for person in hh.get("persons") or []:
                if person.get("workplaces"):
                    return person
        raise AssertionError("no card carries workplaces — build it first")

    fires("a dropped entry", mutated(lambda c: first_with_work(c).pop("workplaces")))
    fires("an entry naming a house that does not name it back",
          mutated(lambda c: first_with_work(c)["workplaces"][0].__setitem__(
              "business_id", "biz_not_a_house")))
    fires("a flipped role", mutated(lambda c: first_with_work(c)["workplaces"][0].__setitem__(
        "role", "porter")))
    fires("a tier upgraded on the card alone",
          mutated(lambda c: first_with_work(c)["workplaces"][0].__setitem__(
              "tier", "attested" if first_with_work(c)["workplaces"][0]["tier"] != "attested"
              else "reconstructed")))
    fires("an empty workplaces list",
          mutated(lambda c: first_with_work(c).__setitem__("workplaces", [])))

    # AND A ROW THE RESIDENTS LAYER HOLDS NO CARD FOR STOPS THE DERIVATION.
    broken = dict(data)
    broken["businesses"] = [dict(data["businesses"][0],
                                 proprietors=[{"name": "X", "person_id": "not_a_card",
                                               "role": "proprietor", "tier": "attested"}],
                                 partners=[], staff=[])]
    fires("a person_id naming no town card", lambda: derive(broken))

    doc = report(data, join)
    assert doc["writes_no_person"] is True and doc["mints_nobody"] is True
    c = doc["counts"]
    print(f"staff_businesses_1835 self-tests pass ({fired} guards fired, "
          f"{c['rows_carrying_a_person_id']} workplaces over "
          f"{c['distinct_persons_tied_to_a_workplace']} cards, "
          f"{doc['unresolved_printed_names']['rows']} printed names unmatched, nobody minted)")
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
