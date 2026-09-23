#!/usr/bin/env python3
"""Carry the register's agency relation to the cards a visitor actually opens (T-1041).

T-0410 built the relation and stopped at the data. `identity.json`'s `agencies` records
that a house or a man HELD an agency for a named principal, `tools/compile_gazetteer.py`
writes `agencies_held` onto the holder's own record, and until this file existed nothing
read any of it. The walkthrough's card shows a trade, goods, proprietors, a street and a
placement, because those are the fields a business record had when the card was written.
A HOLDING IS NONE OF THOSE. It is a relation between two records, which is the whole
reason T-0410 exists — and so a reader of the town met Hubbard & Co. with no way to learn
that it insured property against loss by fire for the Howard of New-York for eleven
months, nor that the agency left it for one man three weeks before the scene date.

    python3 tools/compile_agencies.py             re-derive and write the file
    python3 tools/compile_agencies.py --check     re-derive and diff against committed
    python3 tools/compile_agencies.py --self-test prove the refusals fire when broken

WHAT IS DERIVED HERE AND WHAT IS ONLY CARRIED
---------------------------------------------
Nothing in this file is a judgement. Every principal, window, signature, witness and
note is the gazetteer's own text, copied unchanged: a relation re-argued in a second
file is a second relation, and the card must be able to say that it shows what the
register holds. Three things ARE derived, each from a committed file and each named:

  * `structure_id` — the roof a BUSINESS holder sits on, read off
    `street_face_adoptions.json`. That is how the card is found: the walkthrough opens a
    structure, and this is the only committed statement of which structure a business is
    seated on. A holder with no adoption carries `null` and is still written, because a
    holding that reaches no card is exactly the fault this ticket reports.
  * `household_id` — the card a PERSON holder's card is, read off the households' own
    `press_evidence[].record_id`, which is where `consolidate_resident_evidence.py`
    already records that a gazetteer person and a town card are the same reading. It is
    a lookup of an existing link, never a new identification: a person id that no
    household names carries `null`.
  * `printings_bracket_the_scene_date` — whether this holder's own first and last
    PRINTING fall either side of 1835-07-01. The name is deliberately awkward. A window
    of printings is not a window of holding: the register knows when the notice ran, and
    nothing in it says the appointment began with the first setting or ended with the
    last. The card says "printed" for the same reason.

WHAT THE CARD MAY NOT SAY, AND WHY IT IS ENFORCED HERE
------------------------------------------------------
T-1041's acceptance: "Nothing on the card implies the holder traded in the principal's
line, held a roof for it, or was a partner in any house he signed for." That is a claim
about rendered text, so the standing caveat the card prints is written HERE, beside the
relation it qualifies, rather than typed into a renderer where a later edit could drop
it. `--check` fails if it goes missing, and the smoke pins it on screen.

The refusal is carried for the same reason the holdings are. `business_jones_king_co`'s
`refused_holdings` entry is a judgement about that house — the segmenter put two
advertisements on one line and the fire-insurance notice is signed by the man, not by
the firm — and the card is where a reader would look for it. A refusal that only lives
in a research file reads, from the street, as a holding nobody has noticed.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
GAZETTEER = DATA / "research" / "newspapers" / "gazetteer.json"
ADOPTIONS = DATA / "research" / "newspapers" / "street_face_adoptions.json"
HOUSEHOLDS = DATA / "residents" / "households"
OUT = DATA / "reconstruction" / "1835_agencies.json"

SCENE_DATE = "1835-07-01"

#: The sentence the card prints under every holding. See the module docstring: it is
#: data because the acceptance clause it answers is about rendered text, and text that
#: lives in a renderer is text a later edit can drop without the gate noticing.
CAVEAT = ("A holding is a relation and nothing more. Nothing here says this holder "
          "dealt in the principal's line, kept a roof for it, or was a partner in any "
          "house that signed for it.")

#: What the window is a window of. Printed on the card beside the dates.
WINDOW_NOTE = ("The dates are the first and last PRINTING of this holder's notice in "
               "the corpus, not the term of the appointment: no printing says when the "
               "agency began or ended.")


def load(path: Path):
    return json.loads(path.read_text())


def business_seats() -> dict[str, str]:
    """business_id → structure_id, off the committed street-face adoptions."""
    doc = load(ADOPTIONS)
    return {row["business_id"]: row["structure_id"] for row in doc.get("adoptions", [])}


def person_cards() -> dict[str, str]:
    """gazetteer person id → household id, off the households' own press evidence.

    The link is `consolidate_resident_evidence.py`'s, not this tool's: a household's
    `press_evidence[].record_id` IS the gazetteer person the reading came from. Read
    rather than recomputed, so a card and a holding cannot come to disagree about who
    a man is.
    """
    found: dict[str, str] = {}
    for path in sorted(HOUSEHOLDS.glob("*.json")):
        doc = load(path)
        for person in doc.get("persons", []) or []:
            for row in person.get("press_evidence", []) or []:
                rid = row.get("record_id")
                if isinstance(rid, str) and rid.startswith("person_"):
                    found.setdefault(rid, doc["id"])
    return found


def brackets(first: str | None, last: str | None) -> bool:
    return bool(first and last and first <= SCENE_DATE <= last)


def holding_row(h: dict, seats: dict[str, str], cards: dict[str, str],
                refused: bool = False) -> dict:
    holder_id = h.get("holder_id") or ""
    row = {
        "holder": h.get("holder"),
        "holder_kind": h.get("holder_kind"),
        "holder_id": holder_id or None,
        "structure_id": seats.get(holder_id),
        "household_id": cards.get(holder_id),
        "first_issue": h.get("first_issue"),
        "last_issue": h.get("last_issue"),
        "printings_bracket_the_scene_date": brackets(h.get("first_issue"),
                                                     h.get("last_issue")),
        "signature": h.get("signature"),
        "number": h.get("number"),
        "witnesses": list(h.get("witnesses") or []),
        "note": h.get("note") or "",
    }
    if refused:
        row["refused_because"] = h.get("refused_because") or ""
    return row


def derive() -> dict:
    gaz = load(GAZETTEER)
    seats = business_seats()
    cards = person_cards()

    agencies = []
    for a in gaz.get("agencies", []):
        holdings = [holding_row(h, seats, cards) for h in a.get("holdings", [])]
        refusals = [holding_row(h, seats, cards, refused=True)
                    for h in a.get("refused_holdings", [])]
        agencies.append({
            "id": a["id"],
            "principal": a.get("principal"),
            "principal_seat": a.get("principal_seat"),
            "trade": a.get("trade"),
            "first_issue": a.get("first_issue"),
            "last_issue": a.get("last_issue"),
            "why": a.get("why") or "",
            "holdings": holdings,
            "refused_holdings": refusals,
        })
    agencies.sort(key=lambda a: a["id"])

    holdings_total = sum(len(a["holdings"]) for a in agencies)
    refused_total = sum(len(a["refused_holdings"]) for a in agencies)
    reachable = sum(1 for a in agencies for h in a["holdings"] + a["refused_holdings"]
                    if h["structure_id"] or h["household_id"])

    return {
        "$schema_note": "Derived. Not hand-editable — tools/compile_agencies.py --check "
                        "re-derives this file from the committed register on every commit.",
        "id": "1835_agencies",
        "target_date": SCENE_DATE,
        "ticket": "T-1041",
        "tool": "tools/compile_agencies.py",
        "reads": [
            "data/research/newspapers/gazetteer.json",
            "data/research/newspapers/street_face_adoptions.json",
            "data/residents/households/*.json",
        ],
        "why_this_file_exists":
            "AN AGENCY IS A RELATION, AND THE CARD HAD NO PLACE FOR ONE. T-0410 recorded "
            "that a house or a man held an agency for a named principal and nothing read "
            "it, so a visitor met Hubbard & Co. on La Salle Street with no way to learn "
            "that it insured property against loss by fire for the Howard of New-York, "
            "nor that the agency left it for one man three weeks before the scene date. "
            "This file carries the relation, unchanged, to the two cards it belongs on: "
            "the roof the holder is seated under and the town card of the man who signed.",
        "nothing_is_judged_here":
            "Every principal, window, signature, witness and note below is the "
            "gazetteer's own text, copied. The three derived fields are `structure_id`, "
            "`household_id` and `printings_bracket_the_scene_date`, each read off a "
            "committed file and each named in the tool's docstring. A relation re-argued "
            "in a second file would be a second relation.",
        "the_caveat_the_card_prints": CAVEAT,
        "the_window_is_printings": WINDOW_NOTE,
        "counts": {
            "agencies": len(agencies),
            "holdings": holdings_total,
            "refused_holdings": refused_total,
            "reaching_a_card": reachable,
        },
        "agencies": agencies,
    }


def write(doc: dict) -> None:
    OUT.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n")
    print(f"wrote {OUT.relative_to(ROOT)} — {doc['counts']['agencies']} agency(ies), "
          f"{doc['counts']['holdings']} holding(s), "
          f"{doc['counts']['refused_holdings']} refused, "
          f"{doc['counts']['reaching_a_card']} reaching a card")


def gate(doc: dict) -> list[str]:
    """The refusals. Each one is a way this file could go quietly wrong."""
    bad: list[str] = []
    if not doc["agencies"]:
        bad.append("the register holds no agency at all — the relation has gone missing")
    if doc["the_caveat_the_card_prints"] != CAVEAT:
        bad.append("the standing caveat the card prints is not the one this tool writes")
    for a in doc["agencies"]:
        rows = a["holdings"] + a["refused_holdings"]
        if not rows:
            bad.append(f"{a['id']} carries no holder at all")
        for h in rows:
            who = f"{a['id']}/{h.get('holder_id')}"
            if not h.get("witnesses"):
                bad.append(f"{who} rests on no printing — a holding with no witness is "
                           f"not a reading")
            if h.get("holder_kind") not in ("business", "person"):
                bad.append(f"{who} has holder_kind {h.get('holder_kind')!r}")
            if h.get("holder_kind") == "business" and h.get("household_id"):
                bad.append(f"{who} is a house and has been given a person's town card")
            if h.get("holder_kind") == "person" and h.get("structure_id"):
                bad.append(f"{who} is a man and has been seated on a roof — a man is not "
                           f"a building, and this file may not place one")
            if "refused_because" in h and not h["refused_because"]:
                bad.append(f"{who} is refused and does not say why")
    return bad


def check(doc: dict) -> int:
    bad = gate(doc)
    if bad:
        for line in bad:
            print(f"FAIL: {line}")
        return 1
    if not OUT.exists():
        print(f"FAIL: {OUT.relative_to(ROOT)} is missing — run the tool without --check")
        return 1
    committed = load(OUT)
    if committed != doc:
        print(f"FAIL: {OUT.relative_to(ROOT)} no longer matches what the register "
              f"re-derives to. Re-run tools/compile_agencies.py and commit the result.")
        return 1
    c = doc["counts"]
    print(f"OK   {OUT.relative_to(ROOT)} re-derives exactly "
          f"({c['agencies']} agency, {c['holdings']} holding(s), "
          f"{c['refused_holdings']} refused, {c['reaching_a_card']} reaching a card)")
    return 0


def self_test() -> int:
    failures: list[str] = []

    def fires(what: str, doc: dict, needle: str) -> None:
        bad = gate(doc)
        if any(needle in line for line in bad):
            print(f"   self-test | FAIL as designed: {what}")
        else:
            failures.append(what)
            print(f"   self-test | NOT CAUGHT: {what}")

    import copy
    good = derive()
    if gate(good):
        failures.append("the committed register does not pass its own gate")
        for line in gate(good):
            print(f"   self-test | unexpected: {line}")
    else:
        print("   self-test | ok: the register's own agencies pass the gate")

    d = copy.deepcopy(good)
    d["agencies"] = []
    fires("the relation goes missing entirely", d, "no agency at all")

    d = copy.deepcopy(good)
    d["the_caveat_the_card_prints"] = "Hubbard & Co. sold fire insurance."
    fires("the caveat is rewritten into a trade", d, "standing caveat")

    d = copy.deepcopy(good)
    d["agencies"][0]["holdings"][0]["witnesses"] = []
    fires("a holding is kept with no printing behind it", d, "no printing")

    d = copy.deepcopy(good)
    person = next((h for a in d["agencies"] for h in a["holdings"]
                   if h["holder_kind"] == "person"), None)
    if person is None:
        failures.append("the register holds no person holder to test the seating refusal")
    else:
        person["structure_id"] = "recon_1835_blk_randolph_wells_d2_07"
        fires("a man is seated on a roof", d, "a man is not")

    d = copy.deepcopy(good)
    ref = next((h for a in d["agencies"] for h in a["refused_holdings"]), None)
    if ref is None:
        failures.append("the register holds no refused holding to test")
    else:
        ref["refused_because"] = ""
        fires("a refusal stops saying why", d, "does not say why")

    if failures:
        print("SELF-TEST FAILED: " + "; ".join(failures))
        return 1
    print("self-test ok")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true",
                    help="re-derive and diff against the committed file")
    ap.add_argument("--self-test", action="store_true",
                    help="prove this tool's own refusals fire")
    args = ap.parse_args(argv)
    if args.self_test:
        return self_test()
    doc = derive()
    if args.check:
        return check(doc)
    write(doc)
    return 0


if __name__ == "__main__":
    sys.exit(main())
