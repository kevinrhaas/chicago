#!/usr/bin/env python3
"""T-0638 fault C: the register of names the letter lists print that look misread.

    python3 tools/register_letter_list_suspicions.py --build
    python3 tools/register_letter_list_suspicions.py --check
    python3 tools/register_letter_list_suspicions.py --self-test

WHAT THIS IS, AND WHAT IT DELIBERATELY IS NOT. T-0638 fixed two READING RULES —
which token of a printed name is the family name, and whether an apostrophe splits a
word — and both are mechanical, provable and reversible. It found a third thing that
is none of those: about a dozen names whose LETTERS look wrong. `Hhelps` where the
town has a Phelps, `Bobinson` where it has a Robinson, `Conkiin` for Conklin. Each of
those is a reading judgement over a scanned column of small type, and this project
does not invent readings — several of these lists were printed nine times over
(T-0318, T-0424, T-0428) and the right repair is a cleaner impression, not a guess.

So this file is a WORKLIST, not a correction. Every row carries the name as the town
holds it, the string the paper actually printed, the claim id of the column it was
printed in, and a SUSPICION — explicitly labelled, graded nothing, acted on nowhere.
Nothing downstream may read `suspected_reading` as a name. A later pass working the
page images gets a list of thirteen columns to look at instead of a hunt through 727
households; if the impression settles the letters, that pass changes the reading at
the source (the extracted column, then the register, then the mint) and deletes the
row from here.

REPRODUCIBLE. The printings and the claim ids are read out of the gazetteer, so this
file cannot drift from the corpus. The suspicions themselves are AUTHORED — they are
the ticket's own list, quoted, and they are the one thing here a machine did not
derive; SUSPICIONS below is where they live and the only place they may be edited.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
HOUSEHOLDS = DATA / "residents" / "households"
GAZETTEER = DATA / "research" / "newspapers" / "gazetteer.json"
OUT = DATA / "research" / "residents" / "letter_list_reading_suspicions.json"

# household id -> (what looks misread, what it might be). The right-hand side is a
# SUSPICION and nothing else: no source states it, no record carries it, and no tool
# may promote it. `null` means "these letters cannot be read with confidence and the
# project declines to guess at all" — which is a finding too.
SUSPICIONS: tuple[tuple[str, str, str | None], ...] = (
    ("hh_hhelps_theodore_e", "Hhelps", "Phelps"),
    ("hh_bobinson_george_is", "Bobinson", "Robinson"),
    ("hh_bobinson_george_is", "IS.", None),
    ("hh_willinm_g", "Willinm", None),
    ("hh_orinsbey_martin_t", "Orinsbey", "Ormsby"),
    ("hh_merrich_j_b", "merrich", "Merrick"),
    ("hh_regera_john_v", "Regera", "Rogers"),
    ("hh_ranwin_o", "Ranwin", "Rankin"),
    ("hh_mdolold_james", "M'Dolold", "M'Donald"),
    ("hh_nelts_wm", "Nelts", "Welts"),
    ("hh_conkiin_robert_i", "Conkiin", "Conklin"),
    ("hh_jones_es_high", "Es,Jones, High", None),
    ("hh_perry_a_8", "8.", None),
    ("hh_gabbs_james_i1", "I1.", None),
    ("hh_abbot_8_g", "8.", None),
    ("hh_preston_stephen_ii", "II.", None),
)

WHY_NULL = ("the letters cannot be read with confidence from the impressions this "
            "project holds, and it declines to guess")

NOTES = {
    ("hh_willinm_g", "Willinm"):
        "A FORENAME IN THE SURNAME SLOT, not a misspelling of one: the printing gives "
        "'Willinm G.' and no other token, so the family name may never have been set.",
    ("hh_jones_es_high", "Es,Jones, High"):
        "READS AS A RUN-ON OF TWO ENTRIES — the tail of one name and the head of the "
        "next, set without the break between them. The household is held under the one "
        "surname the string does contain.",
    ("hh_bobinson_george_is", "IS."):
        "A two-character cluster standing where a middle initial goes.",
    ("hh_perry_a_8", "8."):
        "A DIGIT standing where an initial goes — the type or the scan, not a name.",
    ("hh_abbot_8_g", "8."):
        "A DIGIT standing where an initial goes — the type or the scan, not a name.",
    ("hh_gabbs_james_i1", "I1."):
        "A letter and a digit standing where a single initial goes.",
    ("hh_preston_stephen_ii", "II."):
        "A two-character cluster standing where a middle initial goes.",
}


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def dumps(doc):
    return json.dumps(doc, indent=1, ensure_ascii=False) + "\n"


def head_person(doc: dict) -> dict | None:
    return next((p for p in doc.get("persons") or [] if p.get("id") == doc.get("head")),
                None)


def build() -> dict:
    # Keyed on the DISPLAY name, because that is what a household stores and the
    # gazetteer stores the string the paper set — which for a fault-A name is the
    # same tokens in the other order (T-0638). display() is imported from the pass
    # that minted these people so the two can never fall out of step.
    sys.path.insert(0, str(ROOT / "tools"))
    from mint_letter_list_residents import display  # noqa: PLC0415

    gazetteer = {}
    for person in load(GAZETTEER)["persons"]:
        gazetteer.setdefault(display(person["name"]), person)
        gazetteer.setdefault(person["name"], person)
    rows = []
    problems = []
    for household_id, printed, suspected in SUSPICIONS:
        path = HOUSEHOLDS / f"{household_id}.json"
        if not path.exists():
            problems.append(f"{household_id}: no such household — the register names a "
                            f"record the town does not hold")
            continue
        doc = load(path)
        head = head_person(doc)
        gaz = gazetteer.get(head["name"]) if head else None
        variants = sorted({v["as_printed"] for v in (gaz or {}).get("variants") or []})
        claims = sorted((gaz or {}).get("mentions") or [])
        if gaz is None:
            problems.append(f"{household_id}: {head and head['name']!r} is in no "
                            f"gazetteer entry, so its printing cannot be cited")
        row = {
            "household": household_id,
            "person": doc["head"],
            "held_as": head["name"] if head else None,
            "printed": printed,
            "printings": variants,
            "claims": claims,
            "status": "suspicion",
            "grade": None,
            "acted_on": False,
            "suspected_reading": suspected,
        }
        note = NOTES.get((household_id, printed))
        if suspected is None and note is None:
            note = WHY_NULL
        if note:
            row["note"] = note
        rows.append(row)
    if problems:
        for p in problems:
            print(f"   REFUSED: {p}")
        raise SystemExit(2)
    rows.sort(key=lambda r: (r["household"], r["printed"]))
    return {
        "schema": "letter-list-reading-suspicions-v1",
        "_doc": (
            "T-0638 FAULT C. Names the post office's letter lists print that look "
            "MISREAD rather than mis-ordered. This is a worklist for a pass working "
            "the page images, and it is not evidence of anything: `suspected_reading` "
            "is a SUSPICION, it is graded nothing, no source states it, no record "
            "carries it, and nothing downstream may read it as a name. `null` there "
            "means the project declines to guess at all. Rebuild with "
            "tools/register_letter_list_suspicions.py --build."
        ),
        "generated_by": "tools/register_letter_list_suspicions.py",
        "ticket": "T-0638",
        "counts": {
            "rows": len(rows),
            "households": len({r["household"] for r in rows}),
            "with_a_suspected_reading": sum(1 for r in rows if r["suspected_reading"]),
            "declining_to_guess": sum(1 for r in rows if not r["suspected_reading"]),
        },
        "rows": rows,
    }


def self_test() -> int:
    """The one invariant that matters here: nothing in this file is evidence."""
    doc = build()
    failed = 0
    for row in doc["rows"]:
        if row["grade"] is not None or row["status"] != "suspicion" or row["acted_on"]:
            failed += 1
            print(f"   FAIL {row['household']}: a row claims more than a suspicion")
        if not row["claims"]:
            failed += 1
            print(f"   FAIL {row['household']}: cites no printed column")
        if not row["printings"]:
            failed += 1
            print(f"   FAIL {row['household']}: records no printing")
    if failed:
        print(f"   {failed} assertion(s) failed")
        return 1
    print(f"   OK: {len(doc['rows'])} suspicion(s) over "
          f"{doc['counts']['households']} household(s), every one cited, "
          f"graded nothing and acted on nowhere")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    doc = build()
    if args.check:
        if not OUT.exists() or OUT.read_text(encoding="utf-8") != dumps(doc):
            print(f"   FAIL {OUT.relative_to(ROOT)} is stale or hand-edited; rebuild it "
                  f"with tools/register_letter_list_suspicions.py --build")
            return 1
        print(f"   ok    {OUT.relative_to(ROOT)} re-derives — {doc['counts']['rows']} "
              f"suspicion(s), none of them evidence")
        return 0
    OUT.write_text(dumps(doc), encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)} — {doc['counts']['rows']} row(s), "
          f"{doc['counts']['with_a_suspected_reading']} with a suspected reading, "
          f"{doc['counts']['declining_to_guess']} declining to guess")
    return 0


if __name__ == "__main__":
    sys.exit(main())
