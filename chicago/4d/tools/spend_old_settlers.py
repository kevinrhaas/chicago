#!/usr/bin/env python3
"""Fergus's old-settler death notices, spent on the people they name (T-0678, pass 4).

    python3 tools/spend_old_settlers.py             write the ledger and the cards
    python3 tools/spend_old_settlers.py --check     everything re-derives; nothing drifted
    python3 tools/spend_old_settlers.py --report    person by person, what the list says
    python3 tools/spend_old_settlers.py --self-test the rules below, held over what it derives

WHY THIS EXISTS. T-0634 spent the town's own rolls, T-0635 Fergus 1839's later lists and
T-0636 the federal land tract sales. This is pass 4, and it takes the last block the
`old_settlers` domain had left standing. Two adjudications live in that domain and name
people this town holds cards for:

    data/research/old_settlers/crosswalk.json                     45 roster merges, OS1/OS2A
    data/research/old_settlers/death_notices_crosswalk_1835.json  64 death-notice matches

THE FIRST BLOCK IS ALREADY SPENT and this pass does not touch it: `tools/old_settlers.py`
writes the roster's source id onto a resident record for an OS1 or OS2A merge as it
builds, so all 45 are on their cards already. `--check` holds that rather than assuming
it — a group declared spent by somebody else is exactly the kind of claim that rots — and
the ledger states it per source. The second block is the unwritten one: 40 of the 64
matched people had nothing on their card from this list, and the domain's own second-hop
measurement reported 38 rulings that reached a person and never reached that person's
card.

WHAT THIS SOURCE IS, AND THE LIMIT THAT TRAVELS WITH IT. The list is the OBITUARY printed
in Robert Fergus's Directory of the City of Chicago for 1843 (1896) — "Names, places,
dates, and ages at death of some of Chicago's Old Settlers, prior to 1843, and other
well-known citizens who arrived after 1843". THE HEADER ADMITS THE SECOND HALF, so
presence in the list is not evidence of arrival before 1843 and never evidence of
residence on 1 July 1835. That admission is quoted onto every card this pass writes,
because a card that carried the match without the admission would read as a finding about
1835, which it is not.

WHAT IS AND IS NOT WRITTEN, in five rules — passes 1-3's four, and one this source needs.

  1. ONLY WHAT THE CROSSWALK ALREADY DECLARED. This pass re-adjudicates nothing. It reads
     `matches[]` and writes those. The 21 `contested`, the 19 `ambiguous` and the 259
     `refusals` are rivals still standing and write nothing.

  2. ONE BLOCK AND NO OTHER KEY. A household gains `old_settler_deaths` and nothing else is
     touched — not a grade, not an arrival, not a claim block, not a placement, not
     `persons[]`, and above all not `present_on_scene_date`. `--self-test` holds it by
     diffing a record through the applier and asserting the changed key set.

  3. NO GRADE MOVES, and the crosswalk itself forbids it: every match carries `carry_rule`
     — "Whatever is carried is carried as evidence of a DEATH and of an interval the birth
     falls in, never as an 1835 fact and never as a grade." That sentence is quoted onto
     every card. T-0515 applies the ladder against every source at once.

  4. ONE ENTRY PER PERSON, NOT PER MATCH. The crosswalk matches one entry to one person by
     construction — where one person met two entries it filed the pair as `ambiguous` — so
     a person is told once, naming the record id behind it.

  5. THE DISCRIMINATOR IS WRITTEN DOWN, because on 10 of these 64 people it is one letter.
     The rule is a folded surname plus an agreeing first initial, and EITHER SIDE may be
     the one printing an initial: the crosswalk flags the 9 whose 1835 card gives no
     forename, and the list prints an initial for 2 more — "Adams, E. F." meets Elizabeth
     Adams on the letter E and on nothing else. So each side is stated separately, and
     `the_agreement` says in words which case a reader is looking at.
     Hiding a thin match inside a well-formed block is how a card comes to look better
     than its evidence.

WHY THE BLOCK IS ON THE HOUSEHOLD AND NOT IN THE PERSON'S NOTE. `tools/old_settlers.py`
rule OS2A reads a resident record as TEXT, looking for the roster's forename spelled out
somewhere in it. A paragraph naming "Flint, Dr. Austin" on the card of "A. W. Flint" would
hand that rule the spelling it is meant to find independently, and the roster merge would
follow from this pass's own write. That is the circularity the `directories` block was
excluded for, and this block is excluded beside it, in the same list, for the same reason.

THE LEDGER IS NOT A CROSSWALK, deliberately, and for the reason passes 1-3 gave:
`data/research/old_settlers/resident_spend_1835.json` carries no "crosswalk" in its name so
that `measure_research_spend.py` does not read a record of WRITES as a second adjudication
and report the pass grading its own homework.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOMAIN = ROOT / "data" / "research" / "old_settlers"
DEATHS = DOMAIN / "death_notices_crosswalk_1835.json"
ROSTER = DOMAIN / "crosswalk.json"
LEDGER = DOMAIN / "resident_spend_1835.json"
HOUSEHOLDS = ROOT / "data" / "residents" / "households"

SCHEMA = 1
BLOCK = "old_settler_deaths"

# The list, and the only source id this pass writes. The crosswalk states it at the top of
# the file and the records file states the same one.
SOURCE_ID = "fergus_1843_old_settler_death_notices"

LADDER_LIMIT = (
    "This pass WRITES THE EVIDENCE AND MOVES NO GRADE. A death notice printed in 1896 says "
    "a person of this name died on a day; under the ratified ladder (T-0513) that is later "
    "evidence about a DEATH, and it is never an 1835 residence. T-0515 applies the ladder "
    "against every source at once; this pass hands it the evidence and not the verdict."
)


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def dumps(doc) -> str:
    return json.dumps(doc, indent=1, ensure_ascii=False) + "\n"


def dump(path: Path, doc) -> None:
    path.write_text(dumps(doc), encoding="utf-8")


# --- what the list says ----------------------------------------------------------------

# What a card is told about one entry. The crosswalk's own field names, unrenamed: a
# reader who opens the research file after the card should meet the same words.
ENTRY_KEYS = ("as_read", "trade_or_office", "manner_of_death", "place_of_death",
              "death_date", "age_as_printed", "birth_year_earliest", "birth_year_latest",
              "birth_year_arithmetic")


def spells_a_forename(given_as_read) -> bool:
    """True when a printed given name spells a forename out rather than initialling it.

    A token is a forename when it carries no stop and runs to three letters or more:
    "Joseph" and "Austin" do, "E." and "F." do not, and neither does the honorific in
    "Sergt. Joseph" or "Dr. Austin" — which is why the test is any-token and not
    first-token. It is a reading of the domain's own `given_as_read` field and it
    adjudicates nothing: it says what the page printed, not who the person was."""
    for token in str(given_as_read or "").split():
        if "." not in token and len(token) >= 3 and token.replace("-", "").isalpha():
            return True
    return False


def entry_given_as_read() -> dict:
    """record id -> the given name the list prints, out of the domain's own reading."""
    return {r["id"]: (r.get("normalized") or {}).get("given_as_read")
            for r in load(DOMAIN / "death_notices.json").get("records") or []}


def matches() -> list:
    """The crosswalk's matches, in card order, with what each one may carry."""
    doc = load(DEATHS)
    given = entry_given_as_read()
    rows = []
    for match in doc.get("matches") or []:
        entry = (match.get("entries") or [None])[0]
        if entry is None:
            continue
        resident_initial_only = bool(match.get("resident_given_is_initial_only"))
        entry_initial_only = not spells_a_forename(given.get(entry.get("record")))
        rows.append({
            "household_id": match["household_id"],
            "person_id": match["person_id"],
            "resident": match.get("resident"),
            "rule": match.get("rule"),
            "resident_given_is_initial_only": resident_initial_only,
            "entry_given_as_read": given.get(entry.get("record")),
            "entry_given_is_initial_only": entry_initial_only,
            "matched_on_initial_only": resident_initial_only or entry_initial_only,
            "could_carry": list(match.get("could_carry") or []),
            "record_id": entry.get("record"),
            "entry": {k: entry.get(k) for k in ENTRY_KEYS},
        })
    rows.sort(key=lambda r: (r["household_id"], r["person_id"]))
    return rows


def roster_merges() -> list:
    """The 45 OS1/OS2A merges — read to be CHECKED, never to be written (rule 1)."""
    return list(load(ROSTER).get("merges") or [])


# --- what a card is told ---------------------------------------------------------------

def card_person(row: dict) -> dict:
    out = {
        "person_id": row["person_id"],
        "matched_as": row["resident"],
        "matched_by": row["rule"],
        "matched_on_initial_only": row["matched_on_initial_only"],
        "resident_given_is_initial_only": row["resident_given_is_initial_only"],
        "entry_given_as_read": row["entry_given_as_read"],
        "entry_given_is_initial_only": row["entry_given_is_initial_only"],
        "the_agreement": ("a surname and one initial"
                          if row["matched_on_initial_only"]
                          else "a surname and a forename spelled out on both sides"),
        "record_id": row["record_id"],
    }
    out.update({k: v for k, v in row["entry"].items() if k != "as_read"})
    out["as_read"] = row["entry"]["as_read"]
    return out


def card_note(rows: list) -> str:
    doc = load(DEATHS)
    thin = any(r["matched_on_initial_only"] for r in rows)
    return (
        "LATER EVIDENCE OF A DEATH, BESIDE THE 1835 CLAIMS AND NOT INSIDE THEM. Fergus's "
        "1843 directory (1896) prints an obituary list of old settlers, and one of its "
        "entries meets somebody of this name. THE HEADER OF THE LIST IS QUOTED ABOVE, and it "
        "is the limit the whole reading turns on. %s %s %s%s"
        % (doc["what_a_match_here_does_not_mean"],
           doc["matches"][0]["carry_rule"],
           ("THE AGREEMENT HERE IS A SURNAME AND ONE INITIAL: one of the two sides prints "
            "an initial where the forename would be, so a single letter is the whole of the "
            "discriminator and the match is as thin as the rule allows. " if thin else ""),
           LADDER_LIMIT))


def cards() -> dict:
    out = {}
    for row in matches():
        block = out.setdefault(row["household_id"], {
            "the_header_admission": load(DEATHS)["the_header_admission"],
            "note": None,
            "sources": [SOURCE_ID],
            "people": [],
        })
        block["people"].append(card_person(row))
    for hid, block in out.items():
        block["people"].sort(key=lambda p: p["person_id"])
        block["note"] = card_note([{"matched_on_initial_only": p["matched_on_initial_only"]}
                                   for p in block["people"]])
    return out


# --- the ledger ------------------------------------------------------------------------

def ledger_doc() -> dict:
    rows = matches()
    deaths, roster = load(DEATHS), load(ROSTER)
    merges = roster_merges()
    by_source = {}
    for merge in merges:
        by_source[merge["source_id"]] = by_source.get(merge["source_id"], 0) + 1
    return {
        "schema": SCHEMA,
        "_doc": (
            "GENERATED by tools/spend_old_settlers.py. The ledger of T-0678's consolidation "
            "pass 4: which of the old_settlers domain's rulings were written onto the card "
            "they name, and what each card was told. It is a record of WRITES, not of "
            "adjudications — the adjudications are crosswalk.json and "
            "death_notices_crosswalk_1835.json — and it deliberately carries no 'crosswalk' "
            "in its name so that measure_research_spend.py does not count a write as a "
            "second ruling."),
        "generated_by": "tools/spend_old_settlers.py",
        "ticket": "T-0678",
        "pass": "consolidation pass 4",
        "source_id": SOURCE_ID,
        "reads": [
            "data/research/old_settlers/death_notices_crosswalk_1835.json",
            "data/research/old_settlers/crosswalk.json",
        ],
        "writes": "data/residents/households/*.json — the household's old_settler_deaths block",
        "the_header_admission": deaths["the_header_admission"],
        "carry_rule": deaths["matches"][0]["carry_rule"],
        "counts": {
            "matched_rulings": len(deaths["matches"]),
            "people_written": len(rows),
            "households_touched": len({r["household_id"] for r in rows}),
            "grades_changed": 0,
            "carrying_a_date_of_death": sum(1 for r in rows if r["entry"]["death_date"]),
            "carrying_a_birth_interval": sum(1 for r in rows
                                             if r["entry"]["birth_year_earliest"]),
            "matched_on_initial_only": sum(1 for r in rows if r["matched_on_initial_only"]),
            "the_1835_card_gives_no_forename": sum(1 for r in rows
                                                   if r["resident_given_is_initial_only"]),
            "the_list_prints_no_forename": sum(1 for r in rows
                                               if r["entry_given_is_initial_only"]),
            "died_outside_chicago": sum(1 for r in rows if r["entry"]["place_of_death"]),
        },
        "already_written_by_another_pass": {
            "what": ("The 45 roster merges of crosswalk.json are written onto their cards by "
                     "tools/old_settlers.py as it builds — rule OS1/OS2A, 'only merges are "
                     "written' — so this pass would only duplicate them. It writes none of "
                     "them and CHECKS all of them instead: --check fails if a merged person "
                     "stops citing the roll they were merged from."),
            "merges": len(merges),
            "by_source": dict(sorted(by_source.items())),
        },
        "not_written": [
            {
                "group": "contested",
                "rulings": len(deaths.get("contested") or []),
                "why": ("two 1835 people meet one entry and the crosswalk chose neither; a "
                        "card citing the entry anyway would print an undecided identity as a "
                        "decided one"),
            },
            {
                "group": "ambiguous",
                "rulings": len(deaths.get("ambiguous") or []),
                "why": ("one 1835 person meets more than one entry, so the list names a "
                        "death and cannot say which one is this person's"),
            },
            {
                "group": "refusals",
                "rulings": len(deaths.get("refusals") or []),
                "why": ("the surname agrees and the given initial does not, or is absent — a "
                        "surname-only agreement is a refusal however good it looks"),
            },
            {
                "group": "probable (roster)",
                "rulings": len(roster.get("probable") or []),
                "why": ("rule OS2: one bearer of the surname and an initial that agrees, with "
                        "nothing spelling the forename out. Probable is not merged and goes "
                        "to the identity master as a proposal"),
            },
            {
                "group": "refusals (roster)",
                "rulings": len(roster.get("refusals") or []),
                "why": "no bearer of the surname, or the forename initials differ (OS3/OS4/OS5)",
            },
        ],
        "people": [
            {
                "household_id": r["household_id"],
                "person_id": r["person_id"],
                "record_id": r["record_id"],
                "death_date": r["entry"]["death_date"],
                "birth_year_earliest": r["entry"]["birth_year_earliest"],
                "birth_year_latest": r["entry"]["birth_year_latest"],
                "matched_on_initial_only": r["matched_on_initial_only"],
            }
            for r in rows
        ],
    }


# --- the write -------------------------------------------------------------------------

# The block this pass's own block sits IN FRONT OF. `tools/spend_directories.py` derives a
# household by popping its `directories` block and putting it back, which lands it last;
# this pass does the same with its own. Two passes that both append cannot both be right
# about the order, and the loser reports the winner's output as drift — which is how a
# green gate turns red on a file neither pass disagrees about. So this one goes BEFORE
# `directories` wherever both are present, and the order is stable whichever runs last.
AFTER_THIS_PASS = "directories"


def household_text(hid: str, block: dict | None) -> str:
    """The record with this pass's block on it, and nothing else of this pass's."""
    doc = load(HOUSEHOLDS / ("%s.json" % hid))
    doc.pop(BLOCK, None)
    if block:
        tail = {}
        if AFTER_THIS_PASS in doc:
            tail[AFTER_THIS_PASS] = doc.pop(AFTER_THIS_PASS)
        doc[BLOCK] = json.loads(json.dumps(block))
        doc.update(tail)
    return dumps(doc)


def written_files() -> dict:
    block = cards()
    out = {LEDGER: dumps(ledger_doc())}
    for path in sorted(HOUSEHOLDS.glob("*.json")):
        hid = path.stem
        if hid in block:
            out[path] = household_text(hid, block[hid])
        elif BLOCK in load(path):
            out[path] = household_text(hid, None)
    return out


def build(quiet: bool = False) -> int:
    touched = 0
    for path, text in written_files().items():
        if not path.exists() or path.read_text(encoding="utf-8") != text:
            path.write_text(text, encoding="utf-8")
            touched += 1
    if not quiet:
        print("old-settler deaths: %d file(s) written" % touched)
    return 0


# --- the gate --------------------------------------------------------------------------

def missing_cards(rows: list) -> list:
    """Every ruling has to be ON the record it names, or the ruling is only a file."""
    bad = []
    for row in rows:
        path = HOUSEHOLDS / ("%s.json" % row["household_id"])
        if not path.exists():
            bad.append("%s — the household the ruling names does not exist" % row["household_id"])
            continue
        doc = load(path)
        if not any(p.get("id") == row["person_id"] for p in doc.get("persons") or []):
            bad.append("%s/%s — the person the ruling names is not on the card"
                       % (row["household_id"], row["person_id"]))
            continue
        block = doc.get(BLOCK) or {}
        written = {p.get("person_id"): p for p in block.get("people") or []}
        if row["person_id"] not in written:
            bad.append("%s/%s — matched by the crosswalk and the card carries no entry"
                       % (row["household_id"], row["person_id"]))
        elif written[row["person_id"]].get("record_id") != row["record_id"]:
            bad.append("%s/%s — the card names record %s and the crosswalk names %s"
                       % (row["household_id"], row["person_id"],
                          written[row["person_id"]].get("record_id"), row["record_id"]))
        if SOURCE_ID not in (block.get("sources") or []):
            bad.append("%s — carries this pass's block and does not cite %s"
                       % (row["household_id"], SOURCE_ID))
    return bad


def strays(rows: list) -> list:
    """…and a card may not carry this pass's block without a ruling behind it."""
    ruled = {(r["household_id"], r["person_id"]) for r in rows}
    bad = []
    for path in sorted(HOUSEHOLDS.glob("*.json")):
        doc = load(path)
        for person in (doc.get(BLOCK) or {}).get("people") or []:
            if (doc.get("id"), person.get("person_id")) not in ruled:
                bad.append("%s/%s — carries this pass's entry and no match names them"
                           % (doc.get("id"), person.get("person_id")))
    return bad


def roster_gaps() -> list:
    """The group this pass declares ALREADY SPENT, held rather than assumed.

    `tools/old_settlers.py` writes the roll's source id onto a merged person as it builds.
    The ledger says so out loud, and a sentence in a ledger that nothing checks is how a
    group comes to be reported as spent years after it stopped being."""
    bad = []
    for merge in roster_merges():
        path = HOUSEHOLDS / ("%s.json" % merge["household_id"])
        if not path.exists():
            bad.append("%s — the roster merge names a household that does not exist"
                       % merge["household_id"])
            continue
        person = next((p for p in load(path).get("persons") or []
                       if p.get("id") == merge["person_id"]), None)
        if person is None:
            bad.append("%s/%s — the roster merge names a person who is not on the card"
                       % (merge["household_id"], merge["person_id"]))
        elif merge["source_id"] not in (person.get("sources") or []):
            bad.append("%s/%s — merged under %s and the card does not cite %s"
                       % (merge["household_id"], merge["person_id"], merge["rule"],
                          merge["source_id"]))
    return bad


def check(quiet: bool = False) -> int:
    rows = matches()
    if not LEDGER.exists():
        print("   the ledger is missing: %s" % LEDGER.relative_to(ROOT))
        return 1
    drift = [path for path, text in written_files().items()
             if not path.exists() or path.read_text(encoding="utf-8") != text]
    if drift:
        for path in drift[:20]:
            print("   %s no longer re-derives from the crosswalk — re-run the tool"
                  % path.relative_to(ROOT))
        return 1
    bad = missing_cards(rows) + strays(rows) + roster_gaps()
    if bad:
        for line in bad[:20]:
            print("   %s" % line)
        if len(bad) > 20:
            print("   …and %d more" % (len(bad) - 20))
        return 1
    if not quiet:
        print("old-settler deaths: %d death notice(s) on %d card(s), %d roster merge(s) "
              "still cited, no strays"
              % (len(rows), len({r["household_id"] for r in rows}), len(roster_merges())))
    return 0


def report() -> int:
    rows = matches()
    print("%-30s %-26s %-9s %-12s %-11s %s"
          % ("household", "person", "record", "died", "born", "matched on"))
    print("-" * 104)
    for r in rows:
        born = ("%s-%s" % (r["entry"]["birth_year_earliest"], r["entry"]["birth_year_latest"])
                if r["entry"]["birth_year_earliest"] else "—")
        print("%-30s %-26s %-9s %-12s %-11s %s"
              % (r["household_id"], r["person_id"], r["record_id"],
                 r["entry"]["death_date"] or "—", born,
                 "an initial" if r["matched_on_initial_only"] else "a forename"))
    print("-" * 104)
    print("%d people, %d with a date of death, %d with a birth interval, %d on an initial"
          % (len(rows), sum(1 for r in rows if r["entry"]["death_date"]),
             sum(1 for r in rows if r["entry"]["birth_year_earliest"]),
             sum(1 for r in rows if r["matched_on_initial_only"])))
    return 0


def self_test() -> int:
    failures = []

    def want(label, cond):
        if not cond:
            failures.append(label)

    rows = matches()
    want("the crosswalk's matches all reach a row", len(rows) == len(load(DEATHS)["matches"]))
    want("every row names a record", all(r["record_id"] for r in rows))
    want("no row carries a second entry — the crosswalk files those as ambiguous",
         all(len(m.get("entries") or []) == 1 for m in load(DEATHS)["matches"]))

    # Rule 2, held by diffing a record through the applier.
    hid = rows[0]["household_id"]
    before = load(HOUSEHOLDS / ("%s.json" % hid))
    after = json.loads(household_text(hid, cards()[hid]))
    with_both = next((r["household_id"] for r in rows
                      if AFTER_THIS_PASS in load(HOUSEHOLDS / ("%s.json" % r["household_id"]))), None)
    if with_both:
        keys = list(json.loads(household_text(with_both, cards()[with_both])))
        want("this pass's block sits in front of the directories block",
             keys.index(BLOCK) < keys.index(AFTER_THIS_PASS))
    want("the applier adds exactly one key",
         set(after) - set(before) <= {BLOCK} and not set(before) - set(after))
    want("the applier changes nothing else",
         all(after[k] == before[k] for k in before if k != BLOCK))
    want("the applier moves no grade",
         [p.get("grade") for p in after["persons"]] == [p.get("grade") for p in before["persons"]])

    # Rule 1: nothing outside `matches` is ever written.
    doc = load(DEATHS)
    ruled = {(r["household_id"], r["person_id"]) for r in rows}
    for group in ("contested", "ambiguous"):
        for entry in doc.get(group) or []:
            for pid in ([entry.get("person_id")] if entry.get("person_id")
                        else [c.get("person_id") for c in entry.get("residents") or []]):
                want("a %s ruling is never written (%s)" % (group, pid),
                     not any(p == pid for _, p in ruled) or entry.get("person_id") is None)

    # Rule 5: the thin matches are declared, not hidden.
    thin = [r for r in rows if r["matched_on_initial_only"]]
    block = cards()
    want("every thin match says so on its card",
         all(any(p["person_id"] == r["person_id"] and p["matched_on_initial_only"]
                 for p in block[r["household_id"]]["people"]) for r in thin))
    want("a card holding a thin match says so in prose",
         all("SURNAME AND ONE INITIAL" in block[r["household_id"]]["note"] for r in thin))
    want("a forename spelled on both sides is not called thin",
         all(not r["matched_on_initial_only"] for r in rows
             if not r["resident_given_is_initial_only"]
             and spells_a_forename(r["entry_given_as_read"])))
    want("an initialled given name is read as initials",
         spells_a_forename("Dr. Austin") and spells_a_forename("Sergt. Joseph")
         and not spells_a_forename("E. F.") and not spells_a_forename("W. B."))

    # The header admission travels with the evidence, on every card.
    want("every card quotes the list's admission",
         all("does not mean the person was in Chicago in 1835" in b["note"]
             for b in block.values()))

    # The gate can fail: a card that loses its entry is caught.
    broken = [dict(r) for r in rows]
    broken[0] = dict(broken[0], record_id="fdn9999")
    want("a card naming the wrong record is caught", missing_cards(broken))

    for line in failures:
        print("   FAIL %s" % line)
    print("spend_old_settlers self-test: %d assertion(s) failed" % len(failures))
    return 1 if failures else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--report", action="store_true")
    parser.add_argument("--self-test", action="store_true", dest="self_test")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        return self_test()
    if args.report:
        return report()
    if args.check:
        return check(quiet=args.quiet)
    return build(quiet=args.quiet)


if __name__ == "__main__":
    raise SystemExit(main())
