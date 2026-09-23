#!/usr/bin/env python3
"""The candidate-fact table, and the spend of the facts it asserts — T-1232.

WHAT WAS WRONG. The resident layer had spent years of reading into `resident_research`
blocks and then left the findings there, in prose. 94 of those blocks carry an ASSERTED
IDENTITY — the project's own verdict that the person behind the research is the person on
the card — and inside their summaries sat dated arrivals, origins, marriages, deaths,
expansions of initials and departures that the structured fields beside them still read as
null. `hh_andrus_thomas` is the whole defect in one record: the DuPage history gives
"arrival in Chicago Dec. 1, 1833", and the card's `origin` says "Not attested."

A fact that exists only in a paragraph is a fact no query can reach, no gate can hold and no
later ticket can fill a family from. This tool turns each of them into a ROW.

THE TABLE IS THE PRODUCT, NOT THE SPEND. Most rows are withheld, and that is the point.
Three standing rulings do the withholding and none of them is this tool's to overturn:

  later_only          T-0513's ladder, applied by T-0514/T-0515: a volume printed after
                      1 July 1835 may date and corroborate and may NEVER promote. A birth
                      year arithmetic'd out of an 1871 death notice is a real reading and
                      is not an 1835 fact.
  outside_chicago     A source that puts the person somewhere else. Paul Kingston left for
                      Racine on 2 January 1835; that is why his presence cannot be lifted,
                      and writing it down is what makes the grade legible.
  contradicted        Two readings that disagree — including a volume that disagrees with
                      itself, which Fergus 26-29 does about where John S. C. Hogan died.
  insufficient_identity   A surname-only agreement, or a name too common to tie.
  unresolved:T-NNNN   The fact belongs to a field another ticket is building. A trade is
                      T-1145's plural roles; a premises is T-1147's location spend.
  duplicate           The record already holds the value; the row records which source it
                      rests on, which is often more than the record could say before.
  no_candidate        The block proposes nothing to adjudicate — either the consolidation's
                      "confirmed, not moved" verdict on an identity, or a documented no-find.
                      It is NOT a finding that the person did not exist, and it is listed
                      rather than skipped so the table can prove every block was read.
  asserted            Written onto the record, with its source, its date and its reason.

NOTHING HERE MINTS A PERSON. A marriage names a spouse and a chronology names a travelling
companion; neither becomes a household member. T-1170 fills families, from exactly these
rows, under the household model. T-1146 acceptance 4 is the rule and this tool obeys it by
having no code that can create one.

  python3 tools/spend_person_facts.py            # derive the table, write the spend
  python3 tools/spend_person_facts.py --check    # re-derive and fail on any drift
  python3 tools/spend_person_facts.py --self-test  # the adjudication rules, mutated
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RESIDENTS = ROOT / "data" / "residents"
READINGS = ROOT / "data" / "research" / "residents" / "person_fact_readings.json"
TABLE = RESIDENTS / "person_facts.json"
# T-1233. The withheld half of the table, projected for the card. The full table is
# 800 kB and most of it is `no_candidate` rows, which say "read, nothing proposed";
# what a visitor needs is the 204 rows where something WAS proposed and this project
# refused it, with the reason. A projection rather than a second reading: it is
# derived from the same rows in the same run and held by --check in both directions.
WITHHELD = RESIDENTS / "person_facts_withheld.json"
SOURCES = ROOT / "data" / "sources"
TICKET = "T-1232"
SCENE_DATE = "1835-07-01"

VERDICTS = ("asserted", "duplicate", "contradicted", "insufficient_identity",
            "later_only", "outside_chicago", "no_candidate")
FIELDS = ("arrival_at_chicago", "origin", "reason_for_coming", "sex", "name_as_printed",
          "birth_year_bound", "death", "marriage", "life_event", "departure_from_chicago",
          "workplace", "role", "none")
PLACE_CLASSES = ("chicago", "outside_chicago", "not_a_place")

# The only fields a row is allowed to write onto a household's own claim blocks, and only
# where that block is null and the household holds one person. A household field is a claim
# about everybody under the roof; one person's origin may not be dealt to a second person.
HOUSEHOLD_FIELDS = {"origin": "origin", "reason_for_coming": "reason_for_coming"}


def load(path: Path):
    return json.loads(path.read_text())


def verdict_ok(v: str) -> bool:
    return v in VERDICTS or (v.startswith("unresolved:T-") and len(v) == len("unresolved:T-0000"))


def check_row(row: dict, where: str, source_ids: set, on_record: dict) -> list[str]:
    """The rules a candidate row is held to. Returned as errors, never raised.

    These are the rules the mutation tests bite on: each one turns a specific wrong
    verdict into a specific red line, so a future edit that quietly promotes a later
    volume or an out-of-town fact cannot pass by being plausible.
    """
    bad: list[str] = []
    for key in ("field", "value", "confidence", "source", "describes_date",
                "place_class", "quote", "adjudication", "reason"):
        if not str(row.get(key) or "").strip():
            bad.append(f"{where}: '{key}' is empty — a row that cannot say this is not a candidate")
    if row.get("field") not in FIELDS:
        bad.append(f"{where}: fact class {row.get('field')!r} is not one of {FIELDS}")
    if row.get("place_class") not in PLACE_CLASSES:
        bad.append(f"{where}: place_class {row.get('place_class')!r} is not one of {PLACE_CLASSES}")
    if not verdict_ok(str(row.get("adjudication"))):
        bad.append(f"{where}: adjudication {row.get('adjudication')!r} is not a verdict; "
                   f"use one of {VERDICTS} or unresolved:T-NNNN")
    if row.get("source") and row.get("source") not in source_ids:
        bad.append(f"{where}: source {row.get('source')!r} does not resolve in data/sources/")
    if len(str(row.get("reason") or "")) < 40:
        bad.append(f"{where}: the reason is shorter than a sentence. A verdict without its "
                   f"reasoning is the prose this table exists to replace")

    verdict = str(row.get("adjudication"))
    dd = str(row.get("describes_date") or "")

    # R1 — a reading of a date after the scene may never be asserted. T-0513's ladder.
    if verdict == "asserted" and dd > SCENE_DATE:
        bad.append(f"{where}: describes {dd}, after the scene date {SCENE_DATE}, and is "
                   f"asserted. A later volume may date and corroborate and may never "
                   f"promote (T-0513/T-0514/T-0515)")
    # R2 — a fact that places the person outside the town may not be asserted as an
    # arrival at Chicago or a workplace in it.
    if (verdict == "asserted" and row.get("place_class") == "outside_chicago"
            and row.get("field") in ("arrival_at_chicago", "workplace")):
        bad.append(f"{where}: a {row.get('field')} asserted on a fact the source places "
                   f"outside Chicago")
    # R3 — an asserted row must be graded, and `reconstructed` is not a grade a READING
    # can carry: this tool reads sources, it does not model.
    if verdict == "asserted" and row.get("confidence") not in ("attested", "inferred"):
        bad.append(f"{where}: an asserted row is graded {row.get('confidence')!r}; a reading "
                   f"is attested or inferred, never reconstructed")
    # R4 — a row that repeats a value the record already carries is a duplicate and may
    # not be asserted a second time.
    if verdict == "asserted":
        existing = on_record.get(row.get("field"))
        if existing is not None and str(existing).strip() == str(row.get("value")).strip():
            bad.append(f"{where}: asserted, and the record already carries this exact value "
                       f"for {row.get('field')} — that is a duplicate")
    return bad


def record_values(person: dict, household: dict) -> dict:
    """What the record already said BEFORE this tool wrote anything.

    A value this tool spent is not evidence that the record already held it — reading it
    back as one would make the second run of the tool contradict the first, and the R4
    duplicate rule would fire on the tool's own output. A claim block carrying this
    ticket's stamp is therefore read as the null it was filled from.
    """
    def val(block):
        if not isinstance(block, dict):
            return block
        if TICKET in str(block.get("note") or ""):
            return None
        return block.get("value")
    return {
        "arrival_at_chicago": val(household.get("arrival")),
        "origin": val(household.get("origin")),
        "reason_for_coming": val(household.get("reason_for_coming")),
        "sex": person.get("sex"),
        "name_as_printed": person.get("name"),
        "birth_year_bound": val(person.get("birth_year")),
        "role": val(person.get("occupation")),
    }


def build(readings: dict, households: list[tuple[Path, dict]], source_ids: set):
    """Every research block the layer holds, as adjudicated rows."""
    rows: list[dict] = []
    errors: list[str] = []
    authored = readings.get("readings") or {}
    no_candidate = set((readings.get("no_candidate") or {}).get("person_ids") or [])
    seen_matched: set[str] = set()

    for path, h in households:
        for person in h.get("persons") or []:
            rr = person.get("resident_research")
            if not isinstance(rr, dict):
                continue
            pid = person.get("id")
            base = {
                "person_id": pid,
                "household_id": h.get("id"),
                "name_as_read": person.get("name"),
                "source_id": None,
                "claim_or_record_id": f"resident_research:{rr.get('ticket') or 'unticketed'}",
                "describes_date": rr.get("reviewed_on") or "",
            }
            if rr.get("asserted_identity"):
                seen_matched.add(pid)
                authored_rows = authored.get(pid)
                if authored_rows:
                    on_record = record_values(person, h)
                    for i, row in enumerate(authored_rows):
                        where = f"{pid}[{i}]"
                        errors += check_row(row, where, source_ids, on_record)
                        rows.append({
                            **base,
                            "source_id": row.get("source"),
                            "claim_or_record_id": f"{base['claim_or_record_id']}#{i + 1:02d}",
                            "describes_date": row.get("describes_date"),
                            "field": row.get("field"),
                            "proposed_value": row.get("value"),
                            "precision": row.get("precision"),
                            "confidence": row.get("confidence"),
                            "place_class": row.get("place_class"),
                            "quote": row.get("quote"),
                            "adjudication": row.get("adjudication"),
                            "reason": row.get("reason"),
                        })
                elif pid in no_candidate:
                    rows.append({
                        **base, "source_id": (rr.get("source_ids") or [None])[0],
                        "field": "none", "proposed_value": None, "precision": None,
                        "confidence": None, "place_class": "not_a_place",
                        "quote": rr.get("summary") or "",
                        "adjudication": "no_candidate",
                        "reason": "The block is a verdict on the IDENTITY and proposes no fact "
                                  "about the person that the record does not already hold. "
                                  "Listed rather than skipped, so the table can prove every "
                                  "matched block was read.",
                    })
                else:
                    errors.append(f"{pid}: a matched research block with no reading and no "
                                  f"place in no_candidate — every matched block is read or "
                                  f"is declared to have nothing in it")
            else:
                # The unmatched blocks: one disposition row each, in the fields T-1159's
                # borderline roster reads, so the roster is a filter over this table rather
                # than a second reading of the same corpus.
                outcome = rr.get("outcome") or "unstated"
                cand = rr.get("candidate_ids") or [c.get("id") for c in (rr.get("candidates") or [])]
                if outcome in ("candidate_identity", "candidate") or cand:
                    verdict, reason = "insufficient_identity", (
                        "The research found a candidate and could not bridge it to this person "
                        "by more than name similarity. The name stays on the borderline roster "
                        "(T-1159) and the candidate is not spent.")
                else:
                    verdict, reason = "no_candidate", (
                        "The research reviewed this person and found nothing outside the record "
                        "already held. A documented no-find, not evidence that the person did "
                        "not exist, and nothing to spend.")
                rows.append({
                    **base, "source_id": (rr.get("source_ids") or [None])[0],
                    "field": "none", "proposed_value": None, "precision": None,
                    "confidence": None, "place_class": "not_a_place",
                    "quote": (rr.get("summary") or "")[:400],
                    "adjudication": verdict, "reason": reason,
                    "research_outcome": outcome,
                    "candidate_ids": cand or None,
                })

    for pid in sorted(set(authored) | no_candidate):
        if pid not in seen_matched:
            errors.append(f"{pid}: read in person_fact_readings.json and the layer holds no "
                          f"matched research block for that person id")
    return rows, errors


def tally(rows: list[dict]) -> dict:
    out: dict = {}
    for row in rows:
        v = str(row["adjudication"])
        key = "unresolved" if v.startswith("unresolved:") else v
        out[key] = out.get(key, 0) + 1
    return dict(sorted(out.items()))


def table_document(rows: list[dict]) -> dict:
    asserted = [r for r in rows if r["adjudication"] == "asserted"]
    by_field: dict = {}
    for r in asserted:
        by_field[r["field"]] = by_field.get(r["field"], 0) + 1
    return {
        "_doc": "T-1232. Every resident-research block the layer holds, as adjudicated "
                "candidate-fact rows. Generated by tools/spend_person_facts.py from "
                "data/research/residents/person_fact_readings.json and the household records; "
                "never hand-edited, and held by that tool's --check. A row names the person, "
                "the household, the name as it was read, the source, the claim or record it "
                "came from, the date it SPEAKS ABOUT (which is not the date it was printed), "
                "the proposed value and the verdict with its reason. The withheld rows are "
                "the majority and are the reason the file exists: T-1159's borderline roster "
                "is a filter over this table, not a second reading.",
        "ticket": TICKET,
        "generated_by": "tools/spend_person_facts.py",
        "scene_date": SCENE_DATE,
        "counts": {
            "rows": len(rows),
            "by_adjudication": tally(rows),
            "asserted_by_field": dict(sorted(by_field.items())),
            "people_with_an_asserted_fact": len(sorted({r["person_id"] for r in asserted})),
        },
        "rows": sorted(rows, key=lambda r: (r["person_id"], r["claim_or_record_id"], r["field"])),
    }


WITHHELD_CARD_KEYS = ("person_id", "field", "proposed_value", "describes_date",
                      "source_id", "claim_or_record_id", "quote", "place_class",
                      "adjudication", "reason")


def withheld_document(rows: list[dict]) -> dict:
    """The rows where a fact was proposed and this project would not assert it.

    `no_candidate` is excluded and `asserted` is excluded, for opposite reasons: the
    first proposed nothing to withhold and the second is already on the card as a
    `profile_facts` row. What is left is the judgement — 204 rows over 172 people —
    and until T-1233 it reached a visitor nowhere at all.
    """
    withheld = [r for r in rows
                if r["adjudication"] not in ("asserted", "no_candidate")]
    return {
        "_doc": "T-1233. Every candidate fact the research proposed and this project "
                "REFUSED, with the reason, projected out of data/residents/person_facts.json "
                "for renderers/web/js/residents.js. Generated by tools/spend_person_facts.py "
                "and never hand-edited; that tool's --check holds it against the full table. "
                "A withheld row is not a fact about the town and must never be read as one: "
                "it is this project's reasoning about a reading, published so a visitor can "
                "disagree with the refusal instead of never learning it was made.",
        "ticket": "T-1233",
        "generated_by": "tools/spend_person_facts.py",
        "scene_date": SCENE_DATE,
        "counts": {
            "rows": len(withheld),
            "people": len({r["person_id"] for r in withheld}),
            "by_adjudication": tally(withheld),
        },
        "rows": [{k: r[k] for k in WITHHELD_CARD_KEYS}
                 for r in sorted(withheld, key=lambda r: (r["person_id"],
                                                          r["claim_or_record_id"],
                                                          r["field"]))],
    }


def spend(rows: list[dict], households: list[tuple[Path, dict]]) -> tuple[dict, int]:
    """Write the asserted rows onto the records, and count what moved.

    Two places, and no third: a person's own `profile_facts` list, which is additive and
    cannot displace anything; and a household's null `origin`/`reason_for_coming`, only
    where the household holds ONE person, because a household field speaks for everybody
    under the roof.
    """
    by_person: dict = {}
    for r in rows:
        if r["adjudication"] == "asserted":
            by_person.setdefault(r["person_id"], []).append(r)

    moved = {"profile_facts": 0, "household_fields": 0, "people": 0}
    for path, h in households:
        persons = h.get("persons") or []
        touched = False
        for person in persons:
            facts = by_person.get(person.get("id"))
            if not facts:
                if "profile_facts" in person:
                    del person["profile_facts"]
                    touched = True
                continue
            block = []
            for r in facts:
                row = {
                    "field": r["field"],
                    "value": r["proposed_value"],
                    "confidence": r["confidence"],
                    "sources": [r["source_id"]],
                    "describes_date": r["describes_date"],
                    "place_class": r["place_class"],
                    "record_id": r["claim_or_record_id"],
                    "as_read": r["quote"],
                    "note": r["reason"],
                }
                if r.get("precision"):
                    row["precision"] = r["precision"]
                block.append(row)
            if person.get("profile_facts") != block:
                person["profile_facts"] = block
                touched = True
            moved["profile_facts"] += len(block)
            moved["people"] += 1

            if len(persons) == 1:
                for r in facts:
                    key = HOUSEHOLD_FIELDS.get(r["field"])
                    if not key:
                        continue
                    cur = h.get(key)
                    if isinstance(cur, dict) and cur.get("value") is None:
                        h[key] = {
                            "value": r["proposed_value"],
                            "confidence": r["confidence"],
                            "sources": [r["source_id"]],
                            "note": f"{r['reason']} Read from {r['source_id']}: "
                                    f"“{r['as_read'] if 'as_read' in r else r['quote']}”. "
                                    f"Spent by {TICKET} out of the matched resident research, "
                                    f"which held it in prose; the household's other claims are "
                                    f"untouched.",
                        }
                        moved["household_fields"] += 1
                        touched = True
        if touched:
            path.write_text(json.dumps(h, indent=1, ensure_ascii=False) + "\n")
    return moved, len(by_person)


def households_on_disk() -> list[tuple[Path, dict]]:
    return [(p, load(p)) for p in sorted((RESIDENTS / "households").glob("*.json"))]


def self_test() -> int:
    """The adjudication rules, each mutated into the failure it exists to catch."""
    ok = True
    src = {"a_source"}
    good = {"field": "arrival_at_chicago", "value": "1833-12-01", "confidence": "inferred",
            "source": "a_source", "describes_date": "1833-12-01", "place_class": "chicago",
            "quote": "arrival in Chicago Dec. 1, 1833", "adjudication": "asserted",
            "reason": "The source gives the day and the record holds only a postal bound."}
    cases = [
        ("a clean asserted row", good, {}, 0),
        ("a later-volume reading, asserted",
         {**good, "describes_date": "1871-10-23"}, {}, 1),
        ("an out-of-town arrival, asserted",
         {**good, "place_class": "outside_chicago"}, {}, 1),
        ("a reconstructed grade on a reading",
         {**good, "confidence": "reconstructed"}, {}, 1),
        ("a value the record already carries",
         good, {"arrival_at_chicago": "1833-12-01"}, 1),
        ("a verdict that is not a verdict",
         {**good, "adjudication": "probably"}, {}, 1),
        ("an unresolved pointer at another ticket",
         {**good, "adjudication": "unresolved:T-1145"}, {}, 0),
        ("a source that does not resolve",
         {**good, "source": "no_such_source"}, {}, 1),
        ("a reason too short to be one",
         {**good, "reason": "because"}, {}, 1),
        ("a fact class off the vocabulary",
         {**good, "field": "favourite_colour"}, {}, 1),
    ]
    for name, row, on_record, want in cases:
        got = len(check_row(row, "t", src, on_record))
        if got != want:
            ok = False
            print(f"  FAIL {name}: expected {want} error(s), got {got}")
        else:
            print(f"  ok   {name}")
    print("self-test: " + ("all rules bite" if ok else "SOME RULES DID NOT BITE"))
    return 0 if ok else 1


def main(argv: list[str]) -> int:
    if "--self-test" in argv:
        return self_test()
    check = "--check" in argv
    readings = load(READINGS)
    source_ids = {p.stem for p in SOURCES.glob("*.json")}
    households = households_on_disk()

    rows, errors = build(readings, households, source_ids)
    if errors:
        for e in errors[:40]:
            print(f"  {e}")
        print(f"person facts: {len(errors)} reading error(s)")
        return 1

    doc = table_document(rows)
    withheld_doc = withheld_document(rows)
    if check:
        red = 0
        if not TABLE.exists():
            print(f"  {TABLE.relative_to(ROOT)} is missing — run tools/spend_person_facts.py")
            return 1
        on_disk = load(TABLE)
        if on_disk != doc:
            print(f"  {TABLE.relative_to(ROOT)} does not match the readings it is derived "
                  f"from. Re-run tools/spend_person_facts.py in the commit that changed them")
            red += 1
        # T-1233's projection, held exactly. A card that shows a refusal the table no
        # longer makes is worse than a card that shows none.
        if not WITHHELD.exists():
            print(f"  {WITHHELD.relative_to(ROOT)} is missing — run tools/spend_person_facts.py")
            return 1
        if load(WITHHELD) != withheld_doc:
            print(f"  {WITHHELD.relative_to(ROOT)} does not match the table it is projected "
                  f"from. Re-run tools/spend_person_facts.py")
            red += 1
        # The spend itself, held in both directions: every asserted row is on its record
        # with the same value, and no record carries a profile fact the table does not.
        want: dict = {}
        for r in rows:
            if r["adjudication"] == "asserted":
                want.setdefault(r["person_id"], []).append((r["field"], r["proposed_value"]))
        have: dict = {}
        for _, h in households:
            for person in h.get("persons") or []:
                pf = person.get("profile_facts")
                if pf:
                    have[person["id"]] = [(f.get("field"), f.get("value")) for f in pf]
        for pid in sorted(set(want) | set(have)):
            if sorted(want.get(pid, [])) != sorted(have.get(pid, [])):
                print(f"  {pid}: the record's profile_facts and the table disagree — "
                      f"{len(have.get(pid, []))} on the record, {len(want.get(pid, []))} asserted")
                red += 1
        if red:
            print(f"person facts: {red} drift(s)")
            return 1
        print(f"person facts: {len(rows)} row(s) across {len(households)} household(s); "
              f"{doc['counts']['by_adjudication'].get('asserted', 0)} asserted and on the "
              f"records; table and readings agree")
        return 0

    moved, people = spend(rows, households)
    TABLE.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n")
    WITHHELD.write_text(json.dumps(withheld_doc, indent=1, ensure_ascii=False) + "\n")
    print(f"person facts: {len(rows)} row(s) — {doc['counts']['by_adjudication']}")
    print(f"  withheld projection: {withheld_doc['counts']['rows']} refusal(s) over "
          f"{withheld_doc['counts']['people']} person(s)")
    print(f"  spent onto {people} person(s): {moved['profile_facts']} profile fact(s), "
          f"{moved['household_fields']} household field(s) filled")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
