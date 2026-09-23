#!/usr/bin/env python3
"""Peter Pruyne against Peter Pryne: the exhaustion over the 1833 tax roll.

T-1135. T-1132 ruled the Pruyne/Pryne pair UNDECIDED under U1 and wrote down what
would settle it: "Not a page but a COUNT, in C12's shape moved from the forename to
the surname." This tool is that count. It is the arithmetic and not the ruling — the
ruling is hand-authored at data/residents/card_merge_rulings.json, cluster
`pruyne-pryne`, and reasoned out at docs/RESEARCH/pruyne_pryne_exhaustion.md.

THE THREE GATES, in the order a reader should refuse them.

  A — DOES THE ROLL HAVE TO CARRY HIM? C12's second condition asks for an INDEPENDENT
      NON-NAME FACT putting the survivor on the closed roll. The fact offered is
      ground: the 1833 tax list is a roll of the owners and estates of ground inside
      the town (T-1117, town_findings_voter_lists v005), and the Illinois State
      Archives tract register has Peter Pruyne buying at the school-section auction of
      22-25 October 1833. THAT IS NOT ENOUGH ON ITS OWN AND T-1017 SAYS SO: buying at
      that sale was measured and REFUSED as a check on a town-side name. So the gate
      does not ask whether he bought there. It asks WHERE THE GROUND IS, against the
      ring the Trustees walked on 7 November 1833, and it prints both answers — the
      two rows that fall inside the corporate line and the two that fall outside it.

  B — IS ANY OTHER ENTRY LEFT FOR HIM? The exhaustion, run over the WHOLE roll and
      printed. Every one of the 115 entries is scored by the letters between its
      surname and `pruyne`, because the varying half here is the surname and a count
      over the handful of entries that share the forename would not close: thirteen
      entries on this roll print no forename at all. THE RULE NEVER FOLDS ON A
      RESEMBLANCE. It EXCLUDES on a difference, which is the safe direction: saying
      that `beaubien` is not a printing of `pruyne` asks nothing of a reader's
      willingness to believe, where saying that `pryne` is would ask everything.

  C — IS A CLERK CAUGHT DISTINGUISHING THEM? D5's discriminator, and the thing that
      would refuse the merge outright: a closed roll that enters BOTH spellings as
      separate entries. Scored over every committed source text in the corpus.

    tools/exhaust_tax_1833.py --report      the roll and the three gates
    tools/exhaust_tax_1833.py --build       re-measure and write
    tools/exhaust_tax_1833.py --check       re-measure, diff, assert the invariants
    tools/exhaust_tax_1833.py --self-test   the assertions, broken on purpose
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CIVIC = ROOT / "data" / "research" / "civic"
RECORDS = CIVIC / "records" / "voter_lists_1833_1835.json"
GROUND = ROOT / "data" / "research" / "land_sales" / "ground.json"
RULINGS = ROOT / "data" / "research" / "land_sales" / "resident_rulings.json"
OUT = CIVIC / "tax_1833_exhaustion.json"
RESEARCH = ROOT / "data" / "research"

TICKET = "T-1135"
GENERATED_BY = "tools/exhaust_tax_1833.py --build"

SURVIVOR = "pruyne_peter"
FOLDED = "pryne_peter"
SURNAME = "pruyne"
FORENAME = "peter"
ROLL = "tax_1833"

sys.path.insert(0, str(ROOT / "tools"))
from consolidate_town_cards import (  # noqa: E402
    MERGED, compatible, forename_tokens, read_town,
)
from measure_corporation_limits import inside, limits_ring  # noqa: E402

# The stem, as any source in this corpus could print it. Deliberately wider than the
# two spellings in dispute: gate C is a search for a clerk who distinguished them, and
# a search that only looks for what it expects to find has not searched.
STEM = re.compile(r"\bPr[uy]?[uy]?ne?s?\b", re.IGNORECASE)


def town_cards() -> list:
    """Every person on a card, INCLUDING the cards this project has already folded.

    Read from `data/residents/merged/` as well as the index, because the count this
    tool prints must mean the same thing on both sides of its own ruling. A card that
    has been folded onto another still ACCOUNTS FOR the roll entry it was minted from —
    nothing about that entry became unexplained when the fold landed — and a measurement
    that quietly lost a bearer of the stem the moment the merge it argues for went in
    would be a gate that cannot be run twice.
    """
    rows = list(read_town())
    for path in sorted(MERGED.glob("*.json")):
        doc = json.loads(path.read_text(encoding="utf-8"))
        # A folded card is kept as `superseded_record` under a `merged_into` header,
        # so the persons are one level in. A card folded by an older pass that wrote
        # the record at the top level is read the same way by the fallback.
        card = doc.get("superseded_record") or doc
        for person in card.get("persons") or []:
            rows.append({"household": doc["id"], "person": person["id"],
                         "name": person.get("name") or "", "folded": True})
    for row in rows:
        row.setdefault("folded", False)
        row["parsed"] = forename_tokens(row["name"])
    return rows


def levenshtein(a: str, b: str) -> int:
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


# ---------------------------------------------------------------------------
# gate A — the ground, against the line the Trustees walked

def gate_a() -> dict:
    """Peter Pruyne's 1833 ground, each parcel tested against the corporate ring.

    A parcel counts as inside only when ALL FOUR corners of its block polygon fall
    inside the ring. The block is what this project put on the ground and the lot
    within it was not placed (T-0797), so a centroid test would be claiming to know
    where in the block the lot sat, which the sheet does not say.
    """
    ring, _ = limits_ring()
    tracts = json.loads(GROUND.read_text(encoding="utf-8"))["tracts"]
    ruled = {r["purchaser_as_read"]: r
             for r in json.loads(RULINGS.read_text(encoding="utf-8"))["ruled"]}
    rows = []
    for tract in tracts:
        if SURNAME.upper() not in tract["purchaser_as_read"].upper():
            continue
        if not tract["date_purchased"].startswith("1833"):
            continue
        ground = tract.get("ground") or {}
        corners = [tuple(p) for p in (ground.get("ring_local_enu") or [])]
        adjudication = ruled.get(tract["purchaser_as_read"])
        rows.append({
            "record_id": tract["record_id"],
            "purchaser_as_read": tract["purchaser_as_read"],
            "part": tract["part"],
            "date_purchased": tract["date_purchased"],
            "block": ground.get("block_number"),
            "corners_tested": len(corners),
            "corners_inside_the_limits": sum(inside(p, ring) for p in corners),
            "inside_the_limits": bool(corners) and all(inside(p, ring) for p in corners),
            "adjudicated_to": (adjudication or {}).get("resident_id"),
            "adjudication": (adjudication or {}).get("ruling", "not_ruled"),
        })
    rows.sort(key=lambda r: (r["date_purchased"], r["record_id"]))
    carrying = [r for r in rows
                if r["inside_the_limits"] and r["adjudicated_to"] == SURVIVOR
                and r["adjudication"] == "upheld"]
    return {
        "the_question": "Does an independent non-name fact put Peter Pruyne on a roll "
                        "of the owners of ground inside the Town of Chicago in 1833?",
        "the_line": {
            "ordinance": "chicago_democrat_1833_11_26#c024, the Trustees' first village "
                         "ordinance, passed 7 November 1833 and printed nineteen days later",
            "resolved_by": "tools/measure_corporation_limits.py",
            "vertices": len(ring),
        },
        "rows": rows,
        "rows_1833": len(rows),
        "rows_inside_the_limits": sum(r["inside_the_limits"] for r in rows),
        "rows_outside_the_limits": sum(not r["inside_the_limits"] for r in rows),
        "rows_inside_and_adjudicated_to_the_survivor": len(carrying),
        "earliest_row_inside_the_limits": min(
            (r["date_purchased"] for r in rows if r["inside_the_limits"]), default=None),
        "holds": bool(carrying),
        "what_it_does_not_say": "The roll prints no day within 1833, so nothing here "
                                "dates the assessment. What it bounds is the other end: "
                                "the Town of Chicago did not exist before 10 August 1833, "
                                "and this corpus holds no statement of its bounds earlier "
                                "than the ordinance of 7 November 1833 — after every row "
                                "above. That bound is an inference and is graded as one.",
    }


# ---------------------------------------------------------------------------
# gate B — the exhaustion, over the whole roll

def gate_b() -> dict:
    records = json.loads(RECORDS.read_text(encoding="utf-8"))["records"]
    roll = [r for r in records if r["locator"]["list"] == ROLL]
    town = town_cards()

    scored = []
    for entry in roll:
        parsed = forename_tokens(entry["normalized"])
        surname = parsed[0] if parsed else ""
        given = parsed[1] if parsed else []
        cards = [r["person"] for r in town
                 if r["parsed"] and r["parsed"][0] == surname
                 and compatible(parsed, r["parsed"])] if parsed else []
        scored.append({
            "record_id": entry["id"],
            "entry": entry["locator"]["entry"],
            "as_read": entry["as_read"],
            "surname": surname,
            "prints_a_forename": bool(given),
            "forename_could_be_peter": bool(given) and compatible(("x", given),
                                                                  ("x", [FORENAME])),
            "letters_from_pruyne": levenshtein(surname, SURNAME),
            "accounted_for_by": [c for c in cards if c != SURVIVOR],
        })
    scored.sort(key=lambda r: r["entry"])
    at_one = [r for r in scored if r["letters_from_pruyne"] <= 1]
    nearest_other = min((r["letters_from_pruyne"] for r in scored
                         if r["record_id"] != "tax_1833_086"), default=None)
    return {
        "the_question": "Is any entry on this roll other than number 86 one that "
                        "'Peter Pruyne' could be a printing of?",
        "roll_entries": len(roll),
        "entries_printing_no_forename_at_all": sum(not r["prints_a_forename"]
                                                   for r in scored),
        "why_the_count_is_over_the_surname": "Thirteen entries print no forename, so a "
                                             "count over the bearers of 'Peter' cannot "
                                             "close. The varying half is the surname and "
                                             "the count is run over it.",
        "distance_histogram": dict(sorted(Counter(
            r["letters_from_pruyne"] for r in scored).items())),
        "entries_within_one_letter_of_pruyne": [r["record_id"] for r in at_one],
        "nearest_other_entry_in_letters": nearest_other,
        "entries_whose_forename_could_be_peter": [
            r["record_id"] for r in scored if r["forename_could_be_peter"]],
        "entries_accounted_for_by_a_card_that_is_not_the_survivor":
            sum(bool(r["accounted_for_by"]) for r in scored),
        "entries_the_layer_holds_no_card_for": [
            {"record_id": r["record_id"], "as_read": r["as_read"],
             "letters_from_pruyne": r["letters_from_pruyne"]}
            for r in scored if not r["accounted_for_by"]],
        "holds": len(at_one) == 1 and at_one[0]["record_id"] == "tax_1833_086",
        "roll": scored,
    }


# ---------------------------------------------------------------------------
# gate C — is a clerk caught distinguishing them?

def gate_c() -> dict:
    """Every committed source TEXT, scored for the stem's spellings.

    Only `data/research/**/text/` is read. The derived files of this project carry
    both spellings by construction — the crosswalks, the identity master, this file —
    and counting them would be catching ourselves rather than a clerk.
    """
    texts = []
    for path in sorted(RESEARCH.glob("*/text/*")):
        if path.suffix not in (".txt", ".md"):
            continue
        found = Counter(m.lower() for m in
                        STEM.findall(path.read_text(encoding="utf-8", errors="replace")))
        # `prune`/`prunes` is the fruit, and the Democrat advertised it. It is kept in
        # the count and named here rather than filtered away silently.
        spellings = {k: v for k, v in found.items() if k not in ("prune", "prunes")}
        if spellings:
            texts.append({"text": str(path.relative_to(ROOT)),
                          "spellings": dict(sorted(spellings.items()))})
    both = [t for t in texts if "pruyne" in t["spellings"] and "pryne" in t["spellings"]]
    return {
        "the_question": "Does any one source print both spellings as separate entries? "
                        "That is D5's discriminator and it would refuse the merge.",
        "texts_carrying_the_stem": len(texts),
        "texts_carrying_both_spellings": [t["text"] for t in both],
        "holds": not both,
        "texts": texts,
    }


# ---------------------------------------------------------------------------

def bearers_of_the_stem() -> list:
    out = []
    for row in town_cards():
        if row["parsed"] and STEM.fullmatch(row["parsed"][0]):
            out.append({"person": row["person"], "name": row["name"],
                        "household": row["household"], "folded": row["folded"]})
    return sorted(out, key=lambda r: r["person"])


def measure() -> dict:
    a, b, c = gate_a(), gate_b(), gate_c()
    return {
        "schema": 1,
        "domain": "civic",
        "ticket": TICKET,
        "generated_by": GENERATED_BY,
        "the_ruling_is_not_here": "This file is the arithmetic. The ruling is hand-authored "
                                  "at data/residents/card_merge_rulings.json -> clusters -> "
                                  "pruyne-pryne, and reasoned out at "
                                  "docs/RESEARCH/pruyne_pryne_exhaustion.md.",
        "the_pair": {"survivor": SURVIVOR, "folded": FOLDED,
                     "bearers_of_the_stem_in_the_layer": bearers_of_the_stem()},
        "gate_a_the_ground": a,
        "gate_b_the_exhaustion": b,
        "gate_c_no_clerk_distinguishes_them": c,
        "all_three_hold": bool(a["holds"] and b["holds"] and c["holds"]),
    }


def invariants(doc: dict) -> list:
    """(label, ok) for each figure the ruling turns on. Every one of these can move."""
    a = doc["gate_a_the_ground"]
    b = doc["gate_b_the_exhaustion"]
    c = doc["gate_c_no_clerk_distinguishes_them"]
    return [
        ("the roll is still the 115 entries the source enumerates",
         b["roll_entries"] == 115),
        ("exactly one entry stands within one letter of 'pruyne', and it is number 86",
         b["entries_within_one_letter_of_pruyne"] == ["tax_1833_086"]),
        ("the next-nearest entry is three or more letters away, so nothing sits between",
         (b["nearest_other_entry_in_letters"] or 0) >= 3),
        ("some row of the register puts the survivor's own upheld ground inside the "
         "corporate limits in 1833", a["rows_inside_and_adjudicated_to_the_survivor"] >= 1),
        ("some 1833 row of his falls OUTSIDE the limits, so the test discriminates",
         a["rows_outside_the_limits"] >= 1),
        ("no committed source text prints both spellings", c["holds"]),
        ("the corpus holds exactly two bearers of the stem, folded cards included — a "
         "third would reopen the ruling at its one-bearer clause",
         len(doc["the_pair"]["bearers_of_the_stem_in_the_layer"]) == 2),
    ]


def dump(doc: dict) -> str:
    return json.dumps(doc, indent=1, ensure_ascii=False) + "\n"


def report(doc: dict) -> None:
    a, b, c = (doc["gate_a_the_ground"], doc["gate_b_the_exhaustion"],
               doc["gate_c_no_clerk_distinguishes_them"])
    print(f"T-1135 — {SURVIVOR} against {FOLDED}, over the 1833 tax roll\n")
    print("GATE A — the ground, against the line of 7 November 1833")
    for row in a["rows"]:
        where = "INSIDE " if row["inside_the_limits"] else "outside"
        print(f"  {row['record_id']}  {row['date_purchased']}  {row['purchaser_as_read']:18s}"
              f"  {row['part']:12s} block {str(row['block']):>4s}  {where} the limits"
              f"  ({row['corners_inside_the_limits']}/{row['corners_tested']} corners)"
              f"  -> {row['adjudicated_to'] or '—'} ({row['adjudication']})")
    print(f"  holds: {a['holds']}\n")
    print("GATE B — the exhaustion over all "
          f"{b['roll_entries']} entries of the roll")
    print(f"  letters from 'pruyne': {b['distance_histogram']}")
    print(f"  within one letter: {b['entries_within_one_letter_of_pruyne']}")
    print(f"  next nearest entry: {b['nearest_other_entry_in_letters']} letters")
    print(f"  entries printing no forename at all: "
          f"{b['entries_printing_no_forename_at_all']}")
    print(f"  holds: {b['holds']}\n")
    print("GATE C — no clerk caught distinguishing them")
    print(f"  source texts carrying the stem: {c['texts_carrying_the_stem']}")
    print(f"  texts carrying BOTH spellings: {c['texts_carrying_both_spellings']}")
    print(f"  holds: {c['holds']}\n")
    for label, ok in invariants(doc):
        print(f"  [{'ok' if ok else 'RED'}] {label}")


def check(quiet: bool = False) -> int:
    fresh = measure()
    if not OUT.exists():
        print(f"exhaust_tax_1833: {OUT.relative_to(ROOT)} is not committed — run --build")
        return 1
    stored = json.loads(OUT.read_text(encoding="utf-8"))
    bad = 0
    if dump(stored) != dump(fresh):
        print("exhaust_tax_1833: the committed measurement no longer re-derives — "
              "run --build and read the diff before committing it")
        bad = 1
    for label, ok in invariants(fresh):
        if not ok:
            print(f"exhaust_tax_1833: RED — {label}")
            bad = 1
    if bad:
        print("exhaust_tax_1833: T-1135's ruling stands on the figures above; if one has "
              "moved the ruling reopens rather than quietly standing on a measurement "
              "that moved underneath it.")
        return 1
    if not quiet:
        print(f"exhaust_tax_1833: ok — {len(invariants(fresh))} invariants, "
              f"{fresh['gate_b_the_exhaustion']['roll_entries']} entries on the roll")
    return 0


def self_test() -> int:
    """Break each invariant on purpose and require the failure."""
    doc = measure()
    failures = 0

    def must_fire(label, mutate):
        nonlocal failures
        broken = json.loads(dump(doc))
        mutate(broken)
        if all(ok for _, ok in invariants(broken)):
            print(f"self-test: NOT CAUGHT — {label}")
            failures += 1
        else:
            print(f"self-test: caught — {label}")

    must_fire("the roll losing an entry",
              lambda d: d["gate_b_the_exhaustion"].__setitem__("roll_entries", 114))
    must_fire("a second entry arriving within one letter",
              lambda d: d["gate_b_the_exhaustion"].__setitem__(
                  "entries_within_one_letter_of_pruyne",
                  ["tax_1833_086", "tax_1833_085"]))
    must_fire("an entry appearing two letters away",
              lambda d: d["gate_b_the_exhaustion"].__setitem__(
                  "nearest_other_entry_in_letters", 2))
    must_fire("the survivor's ground falling out of the limits",
              lambda d: d["gate_a_the_ground"].__setitem__(
                  "rows_inside_and_adjudicated_to_the_survivor", 0))
    must_fire("every 1833 row falling inside, so the test stops discriminating",
              lambda d: d["gate_a_the_ground"].__setitem__("rows_outside_the_limits", 0))
    must_fire("a source turning up that prints both spellings",
              lambda d: d["gate_c_no_clerk_distinguishes_them"].__setitem__("holds", False))
    must_fire("a third bearer of the stem arriving in the layer",
              lambda d: d["the_pair"]["bearers_of_the_stem_in_the_layer"].append(
                  {"person": "pruin_peter"}))
    if failures:
        print(f"self-test: {failures} assertion(s) did not fire")
        return 1
    print("self-test: every assertion fires when broken")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--build", action="store_true", help="re-measure and write")
    ap.add_argument("--check", action="store_true", help="re-measure, diff, assert")
    ap.add_argument("--report", action="store_true", help="print the three gates")
    ap.add_argument("--self-test", action="store_true", help="break each assertion")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    if args.check:
        return check(args.quiet)
    doc = measure()
    if args.build:
        OUT.write_text(dump(doc), encoding="utf-8")
        print(f"exhaust_tax_1833: wrote {OUT.relative_to(ROOT)}")
    if args.report or not args.build:
        report(doc)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
