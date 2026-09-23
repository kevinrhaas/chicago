#!/usr/bin/env python3
"""Say WHEN a trade is unrecorded, on the cards that hold one for a later year (T-0693).

    python3 tools/qualify_later_trades.py            write the pointer onto every card
    python3 tools/qualify_later_trades.py --check    everything re-derives; nothing drifted
    python3 tools/qualify_later_trades.py --report   the population this defect covers
    python3 tools/qualify_later_trades.py --self-test the rules below, held over the data

THE DEFECT, in the owner's words, 2026-09-04, with hh_allen_edward_richards.json open:
*"and there is evidence in there he is a druggist but that is not in his person record"*.
That file states the man's trade three times — in `book_evidence.as_read`, in the
`directories` block's `occupation_later`, and again in the person's prose note — and then
`persons[0].occupation.value` reads `none_recorded`, which is the one field a reader and
every downstream tool actually consults, and the only one of the four that is not true.

WHAT THIS IS NOT. It is NOT back-projection. A trade printed in 1839 or 1843 is evidence
about 1839 or 1843, and the ratified ladder that says so stays exactly as it is: no grade
moves, no 1835 claim is written, nobody gains a shop in the scene, and `occupation.value`
still reads `none_recorded` so that every consumer testing that string — the two directory
crosswalks, `back_project_addresses.py`, the mint tools — goes on behaving identically.
T-0633 is where a later address gets carried into a placement, and this pass does not
touch it.

WHAT IT IS. `none_recorded` is being made to carry two different states. "This project
holds no trade for this person anywhere" and "this project holds no trade for 1835 and a
dated one for 1839" are not the same fact, and until now they were the same record. This
pass gives the second one a `later_occupation` POINTER on the person's own occupation
block — the shape the ticket names — so the person stops asserting a bare absence its own
file contradicts on the next screen. The pointer is derived, wholly and only, from the
`directories` block already on the record: it invents nothing, reads no source, and can be
deleted without losing a byte.

THE FOUR RULES, which `--self-test` holds over the derivation.

  1. THE POINTER IS DERIVED FROM THE RECORD'S OWN `directories` BLOCK. Value, year,
     confidence and sources are copied from `occupation_later`, never re-parsed and never
     re-graded. If the block goes, the pointer goes with it.

  2. IT IS WRITTEN ONLY WHERE THE 1835 RECORD SAYS `none_recorded`. A person the project
     already holds an 1835 trade for has no absence to qualify, and this pass leaves that
     card alone rather than stacking a second answer on it.

  3. THE 1835 CLAIM DOES NOT MOVE. `value`, `confidence` and the note the mint tools own
     are passed through untouched; the pointer is a new key beside them. `--check`
     re-derives every file byte for byte, so a later pass that quietly promoted one would
     fail the gate rather than ship.

  4. THE DATE TRAVELS WITH THE TRADE. `describes_date` is carried onto the pointer, and
     the note names the volume's year in prose, because a trade without its year is the
     back-projection this pass exists to refuse.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOUSEHOLDS = ROOT / "data" / "residents" / "households"
GENERATOR = "tools/qualify_later_trades.py"
TICKET = "T-0693"
ABSENT = "none_recorded"
POINTER = "later_occupation"
FROM = "directories.people[].occupation_later"

NOTE = (
    "NONE RECORDED FOR 1835 — AND A TRADE IS RECORDED FOR {year}. This is a POINTER at "
    "`{origin}` on this same record, derived by `{generator}` and holding nothing that "
    "block does not already say. It is not a claim about the scene date: the 1835 "
    "occupation above still reads `none_recorded`, its grade has not moved, and no "
    "premises has been sought on the strength of it, because a directory of {year} is "
    "evidence about {year}. It is written because the field a reader consults was "
    "asserting an absence this file contradicts three lines further down, and \"no trade "
    "anywhere\" and \"no trade in the scene window, one printed {year}\" are not the same "
    "fact ({ticket})."
)


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def dumps(doc) -> str:
    return json.dumps(doc, indent=1, ensure_ascii=False) + "\n"


def later_trades(doc: dict) -> dict:
    """person_id -> the record's own `occupation_later`, for everyone that carries one."""
    people = ((doc.get("directories") or {}).get("people")) or []
    return {p["person_id"]: p["occupation_later"] for p in people
            if p.get("person_id") and (p.get("occupation_later") or {}).get("value")}


def pointer_for(later: dict) -> dict:
    """RULE 1 and RULE 4: copied from the block, carrying its year."""
    year = later.get("describes_date")
    return {
        "value": later["value"],
        "describes_date": year,
        "confidence": later.get("confidence"),
        "sources": list(later.get("sources") or []),
        "note": NOTE.format(year=year, ticket=TICKET, origin=FROM, generator=GENERATOR),
    }


def qualified(doc: dict) -> dict:
    """The record with the pointer on every person the block holds a trade for."""
    doc = json.loads(json.dumps(doc))
    later = later_trades(doc)
    for person in doc.get("persons") or []:
        occ = person.get("occupation")
        if not isinstance(occ, dict):
            continue
        want = later.get(person.get("id"))
        # RULE 2: only an absence gets qualified.  RULE 3: rebuilt in the record's own
        # key order, so the 1835 claim keeps its place as well as its value.
        rebuilt = {}
        for key, value in occ.items():
            if key == POINTER:
                continue
            rebuilt[key] = value
            if key == "confidence" and want and occ.get("value") == ABSENT:
                rebuilt[POINTER] = pointer_for(want)
        if want and occ.get("value") == ABSENT and POINTER not in rebuilt:
            rebuilt[POINTER] = pointer_for(want)
        person["occupation"] = rebuilt
    return doc


def written_files() -> dict[Path, str]:
    out: dict[Path, str] = {}
    for path in sorted(HOUSEHOLDS.glob("*.json")):
        doc = read_json(path)
        text = dumps(qualified(doc))
        if text != path.read_text(encoding="utf-8"):
            out[path] = text
    return out


def population() -> dict:
    """RULE 2's arithmetic: who the defect covers, and who it deliberately does not."""
    absent_with_later = []
    trade_with_later = []
    later_total = 0
    unmatched = []
    persons = 0
    absent_total = 0
    for path in sorted(HOUSEHOLDS.glob("*.json")):
        doc = read_json(path)
        later = later_trades(doc)
        later_total += len(later)
        ids = {p.get("id") for p in doc.get("persons") or []}
        unmatched += [f"{path.stem}/{pid}" for pid in later if pid not in ids]
        for person in doc.get("persons") or []:
            occ = person.get("occupation") or {}
            persons += 1
            if occ.get("value") == ABSENT:
                absent_total += 1
            want = later.get(person.get("id"))
            if not want:
                continue
            row = (path.stem, person.get("id"), want.get("value"), want.get("describes_date"))
            (absent_with_later if occ.get("value") == ABSENT else trade_with_later).append(row)
    return {
        "persons": persons,
        "occupation_none_recorded": absent_total,
        "occupation_later_on_a_record": later_total,
        "none_recorded_with_a_dated_later_trade": len(absent_with_later),
        "already_holds_an_1835_trade": len(trade_with_later),
        "occupation_later_naming_nobody_on_the_record": unmatched,
        "rows": absent_with_later,
    }


def report() -> int:
    pop = population()
    print("T-0693 — `none_recorded` while the same file holds a dated later trade\n")
    print("  person records                                     %5d" % pop["persons"])
    print("  occupation.value == none_recorded                  %5d" % pop["occupation_none_recorded"])
    print("  records carrying a directories occupation_later    %5d" % pop["occupation_later_on_a_record"])
    print("  ...of those, the person reads none_recorded        %5d  <- the defect"
          % pop["none_recorded_with_a_dated_later_trade"])
    print("  ...of those, the person already holds a trade      %5d  (left alone, rule 2)"
          % pop["already_holds_an_1835_trade"])
    print("  occupation_later naming nobody on its own record   %5d"
          % len(pop["occupation_later_naming_nobody_on_the_record"]))
    print()
    for hid, pid, value, year in pop["rows"]:
        print("  %-42s %-30s %s (%s)" % (hid, pid, value, year))
    return 0


def self_test() -> int:
    """The four rules, held over a record built to trip each one."""
    failures = []

    def want(label, got, expected):
        if got != expected:
            failures.append(f"{label}: expected {expected!r}, got {got!r}")

    later = {"value": "druggist, Leroy M. Boyce", "describes_date": 1839,
             "confidence": "attested", "sources": ["fergus_chicago_directory_1839"],
             "note": "the block's own note, which is not copied"}
    block = {"people": [{"person_id": "a", "occupation_later": later},
                        {"person_id": "b", "occupation_later": later},
                        {"person_id": "c", "occupation_later": {"value": None}}]}
    doc = {
        "persons": [
            {"id": "a", "occupation": {"value": ABSENT, "confidence": "reconstructed",
                                       "note": "the mint tool's own note"}},
            {"id": "b", "occupation": {"value": "druggist", "confidence": "attested",
                                       "note": "an 1835 trade is recorded"}},
            {"id": "c", "occupation": {"value": ABSENT, "confidence": "reconstructed"}},
            {"id": "d", "occupation": {"value": ABSENT, "confidence": "reconstructed"}},
        ],
        "directories": block,
    }
    out = qualified(doc)
    a, b, c, d = out["persons"]

    # RULE 1 — derived from the block, and nothing else is copied off it.
    want("rule 1 value", a["occupation"][POINTER]["value"], later["value"])
    want("rule 1 sources", a["occupation"][POINTER]["sources"], later["sources"])
    want("rule 1 does not copy the block's note",
         later["note"] in a["occupation"][POINTER]["note"], False)
    want("rule 1 names where it came from",
         FROM in a["occupation"][POINTER]["note"], True)
    want("rule 1 carries no figure the renderer does not read",
         list(a["occupation"][POINTER]),
         ["value", "describes_date", "confidence", "sources", "note"])

    # RULE 2 — only an absence is qualified; a recorded trade and a person the block
    # does not name are both left exactly as they were.
    want("rule 2 leaves a recorded trade alone", POINTER in b["occupation"], False)
    want("rule 2 ignores an empty occupation_later", POINTER in c["occupation"], False)
    want("rule 2 ignores a person the block does not name", POINTER in d["occupation"], False)

    # RULE 3 — the 1835 claim does not move, and the pointer sits after `confidence`
    # rather than displacing anything.
    want("rule 3 value", a["occupation"]["value"], ABSENT)
    want("rule 3 confidence", a["occupation"]["confidence"], "reconstructed")
    want("rule 3 note", a["occupation"]["note"], "the mint tool's own note")
    want("rule 3 key order", list(a["occupation"]), ["value", "confidence", POINTER, "note"])

    # RULE 4 — the year travels with the trade, in the data and in the prose.
    want("rule 4 describes_date", a["occupation"][POINTER]["describes_date"], 1839)
    want("rule 4 names the year in prose", "1839" in a["occupation"][POINTER]["note"], True)

    # IDEMPOTENT — a second pass over its own output changes nothing, which is what
    # `--check` rests on.
    want("idempotent", qualified(out), out)

    # AND THE GATE IS REAL: a promoted value would be caught rather than shipped.
    promoted = json.loads(json.dumps(doc))
    promoted["persons"][0]["occupation"]["value"] = "druggist"
    want("a promoted 1835 value is not written back",
         POINTER in qualified(promoted)["persons"][0]["occupation"], False)

    for line in failures:
        print("FAIL " + line)
    print("%s: %d rule check(s), %d failure(s)" % (GENERATOR, 14, len(failures)))
    return 1 if failures else 0


def main() -> int:
    if "--self-test" in sys.argv:
        return self_test()
    if "--report" in sys.argv:
        return report()
    pending = written_files()
    if "--check" in sys.argv:
        if pending:
            print("qualify_later_trades: %d record(s) do not match the derivation:"
                  % len(pending))
            for path in sorted(pending)[:20]:
                print("  " + str(path.relative_to(ROOT)))
            print("Run `python3 %s` and commit the result (%s)." % (GENERATOR, TICKET))
            return 1
        print("qualify_later_trades: every record re-derives (%s)" % TICKET)
        return 0
    for path, text in sorted(pending.items()):
        path.write_text(text, encoding="utf-8")
    print("qualify_later_trades: wrote %d record(s)" % len(pending))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
