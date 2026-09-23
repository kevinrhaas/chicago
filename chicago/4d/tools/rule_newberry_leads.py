#!/usr/bin/env python3
"""Rule on every lead the Newberry index offers, over every volume read — T-0590.

WHY THIS EXISTS. `tools/measure_research_spend.py` measured `newberry_index` on
2026-09-03 at 2,619 units read and 0 ruled on: the project's largest unspent
read. The owner's finding, in his words: "i see lots of research being done and
some apparent findings from parsing but there are not outputs or updates to the
household and resident data it seems, should i be concerned?" `leads.json` held
319 questions already framed against the residents, the civic lists, the 1840
heads and the structures, and nothing had answered one of them.

A ruling is the deliverable; a merge is not the quota. `census_1840/crosswalk.json`
states the standard: "A refusal is declared as explicitly as a merge - the absence
of one reads like a pair nobody has looked at yet." So every lead is ruled, and
every ruling is ANCHORED - to the card it stands on, and to the person in the town
it reaches where it reaches one.

WHAT A CARD CAN AND CANNOT DO. A Newberry card heads a family surname and names
the printed work that treats that family in a locality. It carries no forename,
no date about a person and no place beyond the locality of the book. So the
ladder below can never reach a merge on a card alone, and `read_newberry_index.py
--check` enforces exactly that on crosswalk.json. This file does not weaken it:
it says, one card at a time, WHY not - and separates the leads whose answer is
already on the shelf from the ones that need a book nobody here has.

THE LADDER, in order. The first test a lead fails decides it.

  1 ocr_variant_only      No candidate reached this heading by an exact surname
                          key - every one of them came through the OCR-similarity
                          window. The heading is not certainly that surname at
                          all, so the pair is refused twice over. This is the
                          `Beeubion` / `Jean Baptiste Beaubien` case already
                          written out by hand in crosswalk.json.
  2 locality_absent       Every card under this heading names Illinois only -
                          no Chicago, no Cook County. The lead stands on a
                          surname with the locality actively absent.
  3 discriminator_found   A card carries a token that is a candidate's FORENAME.
                          This would be the one thing that could lift a lead off
                          the surname, so it is tested rather than assumed. It is
                          never an automatic merge: it is raised for a hand
                          ruling. Volume 1 yields none, and the count is printed
                          so a later volume that does yield one cannot pass
                          quietly.
  4 testable_in_a_held_work
                          A Chicago or Cook County card, on an exact surname,
                          citing a work THIS PROJECT ALREADY HOLDS (Andreas, or
                          the 1839 directory). Outcome `candidate`: plausible,
                          insufficient, and answerable without acquiring
                          anything. This is the reading list.
  5 surname_only_chicago  A Chicago or Cook County card on an exact surname,
                          citing a work nobody here holds, or no work the
                          citation table could read. Refused, and the work it
                          waits on is named.

WHAT IS COUNTED. `measure_research_spend.py` dedupes a domain's rulings by their
anchor, so the spend of this file is the number of DISTINCT CARDS ruled on, not
the number of leads: 319 leads stand on 542 distinct cards, and each card gets
one ruling naming every lead it stands under. `lead_rulings` carries the per-lead
verdict the ticket asks for and is deliberately not an adjudication key, so the
same work is not counted twice.

    tools/rule_newberry_leads.py --write       write the rulings
    tools/rule_newberry_leads.py --check       re-derive and compare
    tools/rule_newberry_leads.py --self-test   prove the assertions fire
"""
from __future__ import annotations

import argparse
import difflib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOMAIN = ROOT / "data" / "research" / "newberry_index"
LEADS = DOMAIN / "leads.json"
# EVERY volume read so far. Was volume 1 alone when T-0590 wrote this; leads.json
# has covered every parsed volume since T-0578, and a lead the tool cannot see the
# cards of is a lead it cannot rule on.
RECORDS_GLOB = "entries_vol_*.json"
OUT = DOMAIN / "lead_crosswalk.json"

# The index itself, as tools/read_newberry_index.py names it. Stated on both
# generated docs so a ruling in either can be carried to a card (T-0598).
SOURCE_ID = "newberry_genealogical_index"
ACQUIRE = DOMAIN / "acquisition_list.json"
TICKET = "T-0590"

# The works `follow_up.json` reports as already on this project's shelf. Kept as a
# literal because it is a claim about THIS repo, not about the index: a work moves
# onto the list when a source record for it lands, and that is a decision somebody
# makes rather than a pattern match.
HELD_WORKS = ("andreas_history_of_chicago", "fergus_chicago_directory_1839")

# Tokens that look like a forename beside a surname and are not one. Every one of
# them was thrown up by running test 3 without the filter: 'Cook' is the county on
# the card's own locality line, 'Cary'/'Crosby' are the surname itself in another
# spelling, and 'and' is English. A discriminator has to come from outside the
# card's locality and outside the surname, or it discriminates nothing.
NOT_A_FORENAME = {
    "cook", "county", "chicago", "illinois", "ill", "iii", "lil", "and", "the",
    "for", "family", "index", "chi", "pub", "book", "second", "presb",
}
SURNAME_ECHO = 0.80  # a token this close to the surname key is the surname again


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def dump(path: Path, doc) -> None:
    path.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n",
                    encoding="utf-8")


def alpha(word: str) -> str:
    return re.sub(r"[^a-z]", "", word.lower())


def forename_tokens(name: str, surname_key: str) -> list:
    """The parts of a name this project holds that are not its surname.

    Initials are dropped: 'W. H. Adams' discriminates nothing a card could carry,
    because the cards have no initials either.
    """
    out = []
    for word in re.split(r"[\s.,']+", name or ""):
        token = alpha(word)
        if len(token) < 3 or token in NOT_A_FORENAME:
            continue
        if token == surname_key:
            continue
        if difflib.SequenceMatcher(None, token, surname_key).ratio() >= SURNAME_ECHO:
            continue
        out.append(token)
    return out


def card_words(as_read: str) -> set:
    return {alpha(w) for w in re.split(r"[^A-Za-z]+", as_read or "") if alpha(w)}


def rule_lead(lead: dict, cards: dict) -> dict:
    """One lead, ruled. Returns the verdict and the reason, in prose."""
    surname = lead["surname_key"]
    entries = [cards[e] for e in lead["entries"] if e in cards]
    printed = "/".join(lead.get("spellings_as_printed") or [surname]) or surname
    names = [c.get("name") for c in lead.get("candidates") or []]
    against = "; ".join(n for n in names if n)

    exact = [c for c in lead.get("candidates") or []
             if (c.get("rule") or "").strip() == "exact surname"]
    exact_names = "; ".join(c.get("name") for c in exact if c.get("name"))
    chicago = [c for c in entries if (c.get("normalized") or {}).get("chicago_or_cook")]
    works = sorted({w for c in entries
                    for w in ((c.get("normalized") or {}).get("works_cited") or [])})
    held = [w for w in works if w in HELD_WORKS]

    found = []
    for cand in lead.get("candidates") or []:
        tokens = forename_tokens(cand.get("name"), surname)
        for card in entries:
            hit = sorted(set(tokens) & card_words(card.get("as_read")))
            if hit:
                found.append({"card": card["id"], "candidate": cand.get("id"),
                              "tokens": hit})

    if not exact:
        return {
            "outcome": "refused", "class": "ocr_variant_only",
            "reason": "Refused twice over. No candidate reaches %r by an exact "
                      "surname key - every one of them came through the OCR "
                      "similarity window, so the heading is not certainly %r at "
                      "all. And if it were, a heading against %s would still be a "
                      "surname against a person, which is always a refusal here."
                      % (printed, printed, against or "a person in this project"),
            "discriminators": found, "works": works, "held_works": held,
        }
    if not chicago:
        return {
            "outcome": "refused", "class": "locality_absent",
            "reason": "Refused. All %d card(s) heading %r name Illinois and neither "
                      "Chicago nor Cook County, so the lead against %s stands on a "
                      "surname with the locality actively absent - the one thing "
                      "beyond the name that a card could have contributed."
                      % (len(entries), printed, against or "this project's person"),
            "discriminators": found, "works": works, "held_works": held,
        }
    if found:
        return {
            "outcome": "candidate", "class": "discriminator_found",
            "reason": "Raised for a hand ruling, not merged. A card heading %r "
                      "carries a token that is a forename of %s rather than the "
                      "surname or the locality. That is the only thing an index "
                      "card could offer beyond a name, so it is never spent "
                      "automatically." % (printed, against),
            "discriminators": found, "works": works, "held_works": held,
        }
    if held:
        return {
            "outcome": "candidate", "class": "testable_in_a_held_work",
            "reason": "Plausible, insufficient - and answerable without acquiring "
                      "anything. %d of the %d card(s) heading %r name Chicago or "
                      "Cook County, the heading is the surname of %s exactly, and "
                      "the cards under it cite %s, which this project already "
                      "holds. Read it there. No card here gives a forename, so "
                      "this mints nobody."
                      % (len(chicago), len(entries), printed,
                         exact_names or "a person here", ", ".join(held)),
            "discriminators": found, "works": works, "held_works": held,
        }
    return {
        "outcome": "refused", "class": "surname_only_chicago",
        "reason": "Refused. %d of the %d card(s) heading %r do name Chicago or Cook "
                  "County and the heading is the surname of %s exactly, but the "
                  "index files every family of a surname under one heading and "
                  "gives no forename, so %r against %s is a surname against a "
                  "person. It waits on %s, which this project does not hold."
                  % (len(chicago), len(entries), printed,
                     exact_names or "a person here", printed,
                     against or "a person here",
                     ", ".join(works) if works else
                     "a work the citation table could not read off the card"),
        "discriminators": found, "works": works, "held_works": held,
    }


def person_anchor(lead: dict) -> list:
    """The town-side ids a lead reaches, and which of them are people.

    Only the residents layer carries person ids: its candidates are `persons[].id`
    inside the 825 household records. A voter id names a line on a poll list, an
    1840 id names a line on a census sheet and a structure id names a building -
    all three are names the project holds, none of them is a person record.
    """
    ids = [c.get("id") for c in lead.get("candidates") or [] if c.get("id")]
    return ids if lead.get("layer") == "residents" else []


def build() -> tuple:
    leads_doc = load(LEADS)
    leads = leads_doc.get("leads") or []
    cards = {}
    volumes = []
    for path in sorted((DOMAIN / "records").glob(RECORDS_GLOB)):
        doc = load(path)
        volumes.append(doc.get("volume"))
        for rec in doc.get("records") or []:
            cards[rec["id"]] = rec
    volumes = sorted(v for v in volumes if v)

    lead_rulings = []
    per_card = {}
    for lead in leads:
        verdict = rule_lead(lead, cards)
        people = person_anchor(lead)
        row = {
            "lead_id": lead["id"],
            "surname_key": lead["surname_key"],
            "spellings_as_printed": lead.get("spellings_as_printed") or [],
            "layer": lead["layer"],
            "outcome": verdict["outcome"],
            "class": verdict["class"],
            "reason": verdict["reason"],
            "record_ids": list(lead.get("entries") or []),
            "candidates": [{"id": c.get("id"), "name": c.get("name"),
                            "rule": c.get("rule")}
                           for c in lead.get("candidates") or []],
            "person_ids": people,
            "works_cited": verdict["works"],
            "held_works": verdict["held_works"],
            "discriminators": verdict["discriminators"],
        }
        lead_rulings.append(row)
        for rid in lead.get("entries") or []:
            slot = per_card.setdefault(rid, {"leads": [], "outcome": "refused"})
            slot["leads"].append(row)
            if row["outcome"] == "candidate":
                slot["outcome"] = "candidate"

    refusals, ambiguous = [], []
    for rid in sorted(per_card):
        slot = per_card[rid]
        card = cards.get(rid) or {}
        rows = slot["leads"]
        # The card's own ruling takes the strongest verdict any lead on it reached:
        # a card that is refused against the voters and a candidate against the
        # residents has been looked at, and it is the LOOKING that is the spend.
        lead_row = next((r for r in rows if r["outcome"] == slot["outcome"]), rows[0])
        # A card reaches a person only where the town side IS a person record and
        # the heading picks out exactly one of them; two Abbotts under one heading
        # is the index doing what an index does, and it resolves to neither.
        people = sorted({p for r in rows for p in r["person_ids"]})
        against = "; ".join(n for r in rows for n in
                            [c["name"] for c in r["candidates"] if c.get("name")])
        entry = {
            "record_id": rid,
            "a": card.get("as_read", ""),
            "b": against,
            "outcome": slot["outcome"],
            "class": lead_row["class"],
            "rule": "%s Ruled on the card %r against %s."
                    % (lead_row["reason"], card.get("as_read", ""), against or "-"),
            "layers": sorted({r["layer"] for r in rows}),
            "leads": [r["lead_id"] for r in rows],
            "person_ids": people,
            "person_id": people[0] if len(people) == 1 else None,
            "evidence": [rid, "data/research/newberry_index/leads.json"],
            "locator": card.get("locator"),
            "ticket": TICKET,
        }
        (ambiguous if slot["outcome"] == "candidate" else refusals).append(entry)

    counts = {
        "leads_ruled": len(lead_rulings),
        "cards_ruled": len(per_card),
        "by_outcome": {},
        "by_class": {},
        "matched": 0,
        "discriminators_found": sum(len(r["discriminators"]) for r in lead_rulings),
    }
    for row in lead_rulings:
        counts["by_outcome"][row["outcome"]] = counts["by_outcome"].get(row["outcome"], 0) + 1
        counts["by_class"][row["class"]] = counts["by_class"].get(row["class"], 0) + 1

    doc = {
        "schema": 1,
        "domain": "newberry_index",
        "volumes": volumes,
        "ticket": TICKET,
        "generated_by": "tools/rule_newberry_leads.py --write",
        # T-0598: the index every lead and every card here was ruled out of.
        "source_id": SOURCE_ID,
        "_doc": "GENERATED. Every lead the volumes read so far offer, ruled and ANCHORED - to the "
                "card it stands on and, where the town side is a person record, to "
                "the person it reaches. NO MERGES, and there never will be: a card "
                "heads a family surname over a citation and names no forename, so "
                "every identification it seems to offer is refused. The refusals "
                "are the output. `matched` is a reachable outcome that no volume read "
                "so far reaches, and the test for it is run rather than assumed - "
                "see `counts.discriminators_found`.",
        "ladder": [
            {"step": 1, "class": "ocr_variant_only", "outcome": "refused",
             "test": "no candidate reached the heading by an exact surname key"},
            {"step": 2, "class": "locality_absent", "outcome": "refused",
             "test": "no card under the heading names Chicago or Cook County"},
            {"step": 3, "class": "discriminator_found", "outcome": "candidate",
             "test": "a card carries a candidate's forename - raised for a hand "
                     "ruling, never merged automatically"},
            {"step": 4, "class": "testable_in_a_held_work", "outcome": "candidate",
             "test": "a Chicago or Cook card on an exact surname citing a work this "
                     "project already holds"},
            {"step": 5, "class": "surname_only_chicago", "outcome": "refused",
             "test": "a Chicago or Cook card on an exact surname, citing a work "
                     "nobody here holds or none the table could read"},
        ],
        "counts": counts,
        "lead_rulings": lead_rulings,
        "ambiguous": ambiguous,
        "refusals": refusals,
    }
    return doc, cards, volumes


def build_acquisitions(cards: dict, volumes: list) -> dict:
    """The 166 Chicago/Cook cards whose citation matched no work in the table.

    The ticket is explicit that these are a SEPARATE finding and must not be forced
    into a lead: they point at works this project does not hold, or at citations
    the works table could not read. Both are true, and which is which matters, so
    the residue is split on whether the card's own line still carries a publication
    year - the only thing on an unreadable citation that survives the photostat
    intact. A card is listed, never graded: nothing here says what work it names.
    """
    rows = []
    for rid in sorted(cards):
        card = cards[rid]
        norm = card.get("normalized") or {}
        if not norm.get("chicago_or_cook") or norm.get("works_cited"):
            continue
        body = (card.get("as_read") or "").split(" | ", 1)[-1]
        years = sorted(set(re.findall(r"\b1[678]\d\d\b", body)))
        rows.append({
            "record_id": rid,
            "as_read": card.get("as_read"),
            "surname_key": norm.get("surname_as_printed"),
            "localities": norm.get("localities"),
            "years_on_the_card": years,
            "locator": card.get("locator"),
        })
    return {
        "schema": 1,
        "domain": "newberry_index",
        "volumes": volumes,
        "ticket": TICKET,
        "generated_by": "tools/rule_newberry_leads.py --write",
        # T-0598: the index every lead and every card here was ruled out of.
        "source_id": SOURCE_ID,
        "_doc": "GENERATED. The Chicago and Cook County cards, over every volume read, whose "
                "citation the works table did not reach. An ACQUISITION LIST, not "
                "leads: each names a printed work that this project cannot open, "
                "and nothing here says which work. Deliberately keyed `cards` and "
                "not `records`, because these are already counted as read under "
                "records/entries_vol_NN.json and a second copy would read as a "
                "second reading in tools/measure_research_spend.py.",
        "note": "T-0581, T-0582 and T-0583 already exist for three of the works the "
                "Chicago cards name. This residue is the rest, and it is the "
                "weakest part of the volume-1 reading: the photostat's text layer "
                "mangles author names so badly that a citation reading '(Ayidrciu, "
                "K T.) 1884' cannot be assigned to a work without opening the "
                "index page again. The publication year is what survives, so it is "
                "carried and nothing is inferred from it.",
        "counts": {
            "cards": len(rows),
            "with_a_year_on_the_card": sum(1 for r in rows if r["years_on_the_card"]),
        },
        "cards": rows,
    }


def check() -> list:
    """The file on disk must be what the ladder produces from the committed cards."""
    bad = []
    if not OUT.exists():
        return ["lead_crosswalk.json is missing - run --write"]
    doc, cards, volumes = build()
    on_disk = load(OUT)
    if on_disk != doc:
        bad.append("lead_crosswalk.json does not re-derive from leads.json and the "
                   "committed cards - it has been edited by hand, or the leads moved "
                   "under it")
    if on_disk.get("merges"):
        bad.append("lead_crosswalk.json carries a merge - an index card is a surname "
                   "over a citation, and a surname-only merge is always a refusal")
    ruled = {r["lead_id"] for r in on_disk.get("lead_rulings") or []}
    offered = {l["id"] for l in load(LEADS).get("leads") or []}
    missing = sorted(offered - ruled)
    if missing:
        bad.append("%d lead(s) offered and not ruled on: %s"
                   % (len(missing), ", ".join(missing[:5])))
    for row in on_disk.get("lead_rulings") or []:
        where = "lead_crosswalk.json %s" % row.get("lead_id")
        if row.get("outcome") not in ("matched", "candidate", "refused"):
            bad.append("%s: outcome %r is outside the three this file may reach"
                       % (where, row.get("outcome")))
        if not str(row.get("reason") or "").strip():
            bad.append("%s: a ruling with no reason written out" % where)
        if not (row.get("record_ids") or []):
            bad.append("%s: a ruling anchored to no card" % where)
    for key in ("refusals", "ambiguous"):
        for entry in on_disk.get(key) or []:
            where = "lead_crosswalk.json %s %s" % (key, entry.get("record_id"))
            if not entry.get("record_id"):
                bad.append("%s: a ruling with no record_id - an unanchored ruling "
                           "is not a spend" % where)
            if entry.get("record_id") not in cards:
                bad.append("%s: anchored to a card that is not in the records" % where)
            if not str(entry.get("rule") or "").strip():
                bad.append("%s: a ruling with no rule" % where)
            if not (entry.get("evidence") or []):
                bad.append("%s: a ruling with no evidence[]" % where)
    if not ACQUIRE.exists():
        bad.append("acquisition_list.json is missing - run --write")
    else:
        want = build_acquisitions(cards, volumes)
        if load(ACQUIRE) != want:
            bad.append("acquisition_list.json does not re-derive from the committed "
                       "cards")
    return bad


def write() -> int:
    doc, cards, volumes = build()
    dump(OUT, doc)
    dump(ACQUIRE, build_acquisitions(cards, volumes))
    print("%d leads ruled on %d cards - %s"
          % (doc["counts"]["leads_ruled"], doc["counts"]["cards_ruled"],
             ", ".join("%s %d" % (k, v)
                       for k, v in sorted(doc["counts"]["by_outcome"].items()))))
    for cls, n in sorted(doc["counts"]["by_class"].items()):
        print("   %-26s %d" % (cls, n))
    print("acquisition list: %d cards" % load(ACQUIRE)["counts"]["cards"])
    return 0


def self_test() -> int:
    """Break each assertion and prove the gate says so."""
    fired = []

    def run(label, mutate, expect):
        doc, cards, volumes = build()
        broken = mutate(json.loads(json.dumps(doc)))
        saved = OUT.read_text(encoding="utf-8") if OUT.exists() else None
        try:
            dump(OUT, broken)
            bad = check()
        finally:
            if saved is not None:
                OUT.write_text(saved, encoding="utf-8")
        hit = any(expect in b for b in bad)
        fired.append((label, hit))
        print("   %-46s %s" % (label, "fires" if hit else "SILENT"))

    def drop_reason(doc):
        doc["lead_rulings"][0]["reason"] = ""
        return doc

    def drop_anchor(doc):
        doc["refusals"][0].pop("record_id", None)
        return doc

    def drop_lead(doc):
        doc["lead_rulings"] = doc["lead_rulings"][1:]
        return doc

    def add_merge(doc):
        doc["merges"] = [{"into": "x", "from": "y"}]
        return doc

    def bad_outcome(doc):
        doc["lead_rulings"][0]["outcome"] = "probably"
        return doc

    run("a ruling with no reason", drop_reason, "no reason written out")
    run("a ruling with no anchor", drop_anchor, "not a spend")
    run("a lead offered and not ruled", drop_lead, "not ruled on")
    run("a merge in a finding aid's crosswalk", add_merge, "carries a merge")
    run("an outcome outside the three", bad_outcome, "outside the three")

    silent = [l for l, ok in fired if not ok]
    if silent:
        print("SILENT assertions: %s" % ", ".join(silent))
        return 1
    print("all %d assertions fire" % len(fired))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.write:
        return write()
    if args.self_test:
        return self_test()
    if args.check:
        bad = check()
        if bad:
            for b in bad:
                print("   %s" % b)
            print("%d problem(s)" % len(bad))
            return 1
        doc = load(OUT)
        print("newberry lead rulings: %d leads on %d cards, %d merges"
              % (doc["counts"]["leads_ruled"], doc["counts"]["cards_ruled"], 0))
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
