"""The rungs the ladder has already ruled, written onto the cards no mint owns (T-0720).

    python3 tools/spend_ladder_rungs.py --build      write
    python3 tools/spend_ladder_rungs.py --check      re-derive and diff
    python3 tools/spend_ladder_rungs.py --report     every rung spent and every refusal
    python3 tools/spend_ladder_rungs.py --coverage   the ladder's reach, before and after
    python3 tools/spend_ladder_rungs.py --gate       the invariants this pass owes
    python3 tools/spend_ladder_rungs.py --self-test  those assertions, broken on purpose

WHAT THIS PASS IS, AND WHY IT IS A SPEND RATHER THAN A READING.

`tools/consolidate_resident_evidence.py --build` fires the owner's ratified ladder of
2026-09-03 against every identity it can build and writes the result to
`data/research/residents/grading_proposal.json`. That file is a PROPOSAL by design:
keeping it one is what lets the owner read a diff of every grade before any of them
moves. Two passes have spent parts of it — `mint_civic_residents.py --build` mints the
identities the town did not hold, `--regrade` rules on the ones it did — and between
them they own the 531 cards that carry a `ladder_rule`.

Nothing owned the other 873. T-0692's `--coverage` measured it on dev on 2026-09-04:
864 of those people carry a rung the ladder HAS ruled, sitting in the proposal, with no
pass that ever carried it onto the card. 106 of them are `attested`. A grade a reader
cannot argue with is the defect that ticket exists to name, and this pass closes it.

WHAT IT WRITES, AND THE ONE THING IT WILL NOT DO.

One scalar: `ladder_rule`, on the person, immediately after `grade`. Nothing else on the
card moves — not the grade, not the subtype, not a source, not a note. That is the whole
discipline of this pass, and the reason it is safe to run across cards four other passes
wrote: it adds the REASON for a grade that is already there and touches nothing that any
of those passes derives.

It follows that the pass may only write where the ladder AGREES with the card. Where the
rung proposes a grade or a subtype the card does not carry, the rung is not written: the
row goes to the owner's conflict list in `data/research/residents/ladder_spend.json`
with the reason, and the card is left exactly as its own pass wrote it. NO GRADE IS EVER
DOWNGRADED HERE to close the coverage gap. The 45 downgrades in that list were already
ruled on and declined by T-0515, which wrote the refusal onto each card; the other 37
are the ladder's own G5 abstentions and the one row that would take a
`projected_resident` caveat off a card on evidence this pass has not read.

WHERE THE OWNERSHIP LINE FALLS, so `--check` can tell a hand-edit from a derivation.
`ladder_rule` on a card is `civic_mint` or it is this pass — measured on dev before this
pass ran, those two sets were `(rule, civic_mint)` = 531 and `(no rule, no civic_mint)`
= 873, with no card on either diagonal. So: the civic mint owns every person carrying
`civic_mint: true` and this pass never looks at one; every other person's rung is
derived here, and `--check` fails if a card carries one this derivation does not reach.

NO COUNT IS WRITTEN INTO PROSE, for the reason the mints beside this one give: the
corpus grows most weeks the loop runs, and a figure copied into a docstring is wrong by
the next transcription. `--report` prints what was spent; `--coverage` prints the reach.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
HOUSEHOLDS = DATA / "residents" / "households"
PROPOSAL = DATA / "research" / "residents" / "grading_proposal.json"
MASTER = DATA / "research" / "residents" / "identity_master.json"
SPEND = DATA / "research" / "residents" / "ladder_spend.json"

sys.path.insert(0, str(ROOT / "tools"))
from consolidate_resident_evidence import GRADE_RULES  # noqa: E402  (one ladder, not two)

GENERATED_BY = "tools/spend_ladder_rungs.py --build"
TICKET = "T-0720"

# The reach of the ladder as T-0692's `--coverage` measured it on dev on 2026-09-04, the
# morning this pass was written. It is a historical reading and cannot be re-derived
# once the spend has landed, so it is a constant here rather than a field in a generated
# file that would quietly restate today's answer as the day's before-picture (T-0764 is
# the same defect in a cohort manifest).
COVERAGE_BEFORE = {
    "measured_on": "2026-09-04",
    "person_records": 1404,
    "carry_a_rule": 531,
    "carry_no_rule": 873,
    "proposed_not_written": 864,
}

# Why a rung was refused rather than written. Each is a disagreement between the ladder
# and the card, and every one of them is the owner's to rule on.
REFUSAL_KINDS = {
    "downgrade": "the rung proposes a LOWER grade than the card carries. T-0515 ruled on "
                 "this row and declined it, because the card rests on evidence the "
                 "consolidation never read; the refusal is on the card. Writing the rung "
                 "here would say the card carries a grade it does not.",
    "abstention": "the ladder abstains (G5): every appearance it can see describes a date "
                  "after the scene year, and it declines to demote a resident on evidence "
                  "it has not read. An abstention is not a rung, so there is none to write.",
    "subtype": "the rung proposes the same grade with a DIFFERENT resident_subtype. "
               "Taking a `projected_resident` caveat off a card, or putting one on, is a "
               "change to what the card claims and not a reason for what it already says.",
    "grade_disagrees": "the rung proposes a grade the card does not carry and no row in "
                       "`changes_to_existing_people` accounts for the difference.",
}


def load(path: pathlib.Path):
    return json.loads(path.read_text(encoding="utf-8"))


def dumps(doc, indent=1) -> str:
    return json.dumps(doc, indent=indent, ensure_ascii=False) + "\n"


def with_rung(person: dict, rule: str) -> dict:
    """The person, carrying `ladder_rule` immediately after `grade`.

    The position is fixed rather than appended so that two passes writing the same
    field — this one and `mint_placed_residents.carry_forward` — produce the same bytes.
    """
    out: dict = {}
    for key, value in person.items():
        if key == "ladder_rule":
            continue
        out[key] = value
        if key == "grade":
            out["ladder_rule"] = rule
    if "ladder_rule" not in out:
        out["ladder_rule"] = rule
    return out


def rulings(proposal: dict, master: dict):
    """(the rung ruled for each town person, the rows the proposal already disputes)."""
    ruling = {entry["identity"]: entry for entry in proposal["proposals"]}
    by_person = {}
    for row in master["identities"]:
        entry = ruling.get(row["id"])
        if entry is None:
            continue
        canonical = row.get("canonical_person_id")
        for person_id in row.get("town_person_ids") or []:
            # An identity that names a different card as its canonical person ruled for
            # THAT card. The rung was never offered to this one and this pass does not
            # offer it either — `absorbed_by_another_card` in T-0692's coverage.
            if person_id == canonical:
                by_person[person_id] = (row["id"], entry)
    disputed = {change["person_id"]: change
                for change in proposal.get("changes_to_existing_people", [])}
    return by_person, disputed


def decide(docs: dict, proposal: dict, master: dict):
    """Every card with no rung, ruled on. Pure — a function of the two research files
    and the committed tree. Returns (spent, conflicts, foreign)."""
    by_person, disputed = rulings(proposal, master)
    spent, conflicts, foreign = [], [], []
    for path in sorted(docs):
        doc = docs[path]
        for person in doc.get("persons") or []:
            person_id = person.get("id")
            if not person_id:
                continue
            if person.get("civic_mint"):
                continue                      # the civic mint's own, and gated there
            found = by_person.get(person_id)
            if found is None:
                # No identity, or an identity that ruled for another card. T-0692's
                # coverage names both with their reason; there is no rung to spend.
                if person.get("ladder_rule"):
                    foreign.append((path, person_id, person["ladder_rule"]))
                continue
            identity, entry = found
            row = {
                "person_id": person_id,
                "household_id": doc.get("id"),
                "name": person.get("name"),
                "identity": identity,
                "rule": entry["rule"],
                "grade": person.get("grade"),
                "resident_subtype": person.get("resident_subtype"),
            }
            change = disputed.get(person_id)
            agrees = (entry.get("grade") == person.get("grade")
                      and (entry.get("resident_subtype") or None)
                      == (person.get("resident_subtype") or None))
            if agrees and change is None:
                spent.append((path, row))
                continue
            # The abstention is read FIRST. G5's rows are recorded with a downward
            # direction because the card's grade is higher than the nothing the ladder
            # proposes — but a rung that proposes no grade at all is an abstention, and
            # calling it a downgrade would say the ladder asked for something.
            if entry.get("grade") is None:
                kind = "abstention"
            elif change is not None and change.get("direction") == "down":
                kind = "downgrade"
            elif entry.get("grade") == person.get("grade"):
                kind = "subtype"
            else:
                kind = "grade_disagrees"
            row["kind"] = kind
            row["proposed"] = {"grade": entry.get("grade"),
                               "resident_subtype": entry.get("resident_subtype")}
            row["why"] = REFUSAL_KINDS[kind]
            conflicts.append(row)
    return spent, conflicts, foreign


def spend_record(spent, conflicts, docs) -> dict:
    by_rule, by_kind = {}, {}
    for _path, row in spent:
        by_rule[row["rule"]] = by_rule.get(row["rule"], 0) + 1
    for row in conflicts:
        by_kind[row["kind"]] = by_kind.get(row["kind"], 0) + 1
    people = sum(len(doc.get("persons") or []) for doc in docs.values())
    carried = sum(1 for doc in docs.values() for p in doc.get("persons") or []
                  if p.get("civic_mint"))
    return {
        "schema": 1,
        "_doc": "GENERATED by tools/spend_ladder_rungs.py --build (T-0720). The rungs "
                "the ratified ladder had already ruled in grading_proposal.json and no "
                "pass had written onto a card, spent onto the cards the civic mint does "
                "not own. NO GRADE MOVES HERE: a rung is written only where the ladder "
                "AGREES with the grade and subtype the card already carries, and every "
                "disagreement is on the conflict list below for the owner to rule on.",
        "generated_by": GENERATED_BY,
        "ticket": TICKET,
        "coverage_before": COVERAGE_BEFORE,
        "counts": {
            "person_records": people,
            "carried_by_the_civic_mint": carried,
            "rungs_spent": len(spent),
            "conflicts_for_the_owner": len(conflicts),
            "spent_by_rule": dict(sorted(by_rule.items())),
            "conflicts_by_kind": dict(sorted(by_kind.items())),
        },
        "refusal_kinds": REFUSAL_KINDS,
        "spent": [row for _path, row in sorted(spent, key=lambda s: s[1]["person_id"])],
        "conflicts": sorted(conflicts, key=lambda r: r["person_id"]),
    }


def build(preload: dict | None = None):
    docs = ({pathlib.Path(p): json.loads(t) for p, t in preload.items()}
            if preload is not None
            else {p: load(p) for p in sorted(HOUSEHOLDS.glob("*.json"))})
    proposal, master = load(PROPOSAL), load(MASTER)
    spent, conflicts, foreign = decide(docs, proposal, master)

    wanted: dict = {}
    for path, row in spent:
        wanted.setdefault(path, {})[row["person_id"]] = row["rule"]
    files = {}
    for path, doc in docs.items():
        rungs = wanted.get(path, {})
        persons = doc.get("persons") or []
        rebuilt, touched = [], False
        for person in persons:
            rule = rungs.get(person.get("id"))
            if rule is None:
                if person.get("ladder_rule") and not person.get("civic_mint"):
                    touched = True            # a rung this derivation does not reach
                    person = {k: v for k, v in person.items() if k != "ladder_rule"}
                rebuilt.append(person)
                continue
            if person.get("ladder_rule") != rule:
                touched = True
            rebuilt.append(with_rung(person, rule))
        if not touched:
            continue
        out = dict(doc)
        out["persons"] = rebuilt
        files[path] = dumps(out, 1)
    record = spend_record(spent, conflicts, docs)
    files[SPEND] = dumps(record, 1)
    return files, spent, conflicts, foreign, record


def invariants(spent, conflicts, foreign, docs, proposal, master) -> list:
    """The assertions the acceptance names. Each returns a sentence, or nothing."""
    problems = []
    for path, person_id, rule in foreign:
        problems.append(f"{person_id} carries ladder_rule {rule} and neither the civic "
                        f"mint nor this pass derives it ({pathlib.Path(path).name})")
    for _path, row in spent:
        rule = row["rule"]
        if rule not in GRADE_RULES:
            problems.append(f"{row['person_id']} is spent an unknown rung {rule}")
            continue
        if GRADE_RULES[rule][0] != row["grade"]:
            problems.append(f"{row['person_id']} is spent {rule}, which proposes "
                            f"{GRADE_RULES[rule][0]}, onto a card graded {row['grade']}")
    for row in conflicts:
        if row["kind"] not in REFUSAL_KINDS:
            problems.append(f"{row['person_id']} is refused for an unknown reason "
                            f"{row['kind']}")
        if not row.get("why"):
            problems.append(f"{row['person_id']} is refused and the list states no reason")
    # THE SPEND IS TOTAL OR IT IS NOTHING (the acceptance's own words). Every person the
    # ladder ruled on and no mint owns is either carrying the rung or on the conflict
    # list. A person in neither is one this pass met and has no account of.
    by_person, _disputed = rulings(proposal, master)
    accounted = {row["person_id"] for _p, row in spent} | {r["person_id"] for r in conflicts}
    stranded = []
    for doc in docs.values():
        for person in doc.get("persons") or []:
            pid = person.get("id")
            if not pid or person.get("civic_mint"):
                continue
            if pid in by_person and pid not in accounted:
                stranded.append(pid)
    if stranded:
        problems.append(f"{len(stranded)} person record(s) the ladder ruled on are "
                        f"neither spent nor on the conflict list "
                        f"(first: {', '.join(sorted(stranded)[:5])})")
    # NOTHING IS GRADED DOWN TO CLOSE THE GAP. Every conflict leaves the card alone.
    for row in conflicts:
        if row["kind"] == "downgrade" and row["proposed"]["grade"] == row["grade"]:
            problems.append(f"{row['person_id']} is listed as a downgrade and the card "
                            f"already carries the lower grade")
    return problems


def report(spent, conflicts, record) -> None:
    counts = record["counts"]
    print("\nTHE RUNGS SPENT")
    for rule, n in counts["spent_by_rule"].items():
        print(f"  {rule:<5} {GRADE_RULES[rule][0] or 'no proposal':<18} {n:>5}   "
              f"{GRADE_RULES[rule][1][:56]}")
    print(f"  {'':<5} {'':<18} {counts['rungs_spent']:>5}   total")
    print("\nTHE CONFLICT LIST — the owner's, one row per disagreement")
    for kind, n in counts["conflicts_by_kind"].items():
        print(f"  {kind:<16} {n:>5}   {REFUSAL_KINDS[kind][:60]}")
    for row in conflicts:
        print(f"    {row['person_id']:<28} {str(row['name'])[:30]:<32} "
              f"{row['rule']:<5} {row['grade']} -> {row['proposed']['grade']}")
    print(f"\n  the full list, one person per line: {SPEND.relative_to(ROOT)}")


def coverage(record) -> None:
    before, counts = record["coverage_before"], record["counts"]
    after_rule = counts["carried_by_the_civic_mint"] + counts["rungs_spent"]
    print("\nTHE LADDER'S REACH, BEFORE AND AFTER THE SPEND")
    print(f"  {'':<44} {'before':>8} {'after':>8}")
    print(f"  {'person records in data/residents/':<44} "
          f"{before['person_records']:>8} {counts['person_records']:>8}")
    print(f"  {'carrying a ladder_rule on the card':<44} "
          f"{before['carry_a_rule']:>8} {after_rule:>8}")
    print(f"  {'carrying none':<44} {before['carry_no_rule']:>8} "
          f"{counts['person_records'] - after_rule:>8}")
    print(f"  {'a rung ruled and never written':<44} "
          f"{before['proposed_not_written']:>8} {len(record['conflicts']):>8}")
    print(f"\n  before: T-0692's --coverage on dev, {before['measured_on']}. "
          f"after: this pass, re-derived now.")
    print("  the rows still without a rung are the conflict list — the ladder disagrees "
          "with the\n  card and the owner rules, which is not a coverage gap but a "
          "question waiting on him.")


def self_test() -> int:
    """Break each assertion on purpose and require the gate to fire."""
    docs = {p: load(p) for p in sorted(HOUSEHOLDS.glob("*.json"))}
    proposal, master = load(PROPOSAL), load(MASTER)
    spent, conflicts, foreign = decide(docs, proposal, master)
    ok = True

    if invariants(spent, conflicts, foreign, docs, proposal, master):
        print("  FAIL the committed tree does not pass its own gate")
        ok = False
    else:
        print("  ok    the committed tree passes its own gate")

    broken = [(pathlib.Path("hh_x.json"), "someone", "G1a")]
    if any("neither the civic mint nor this pass" in p
           for p in invariants(spent, conflicts, broken, docs, proposal, master)):
        print("  ok    a rung no derivation reaches is caught")
    else:
        print("  FAIL a hand-written rung was allowed through")
        ok = False

    bad = [(p, dict(row, grade="attested")) for p, row in spent if row["rule"] == "G3"][:1]
    if bad and any("onto a card graded" in p
                   for p in invariants(bad, conflicts, [], docs, proposal, master)):
        print("  ok    a rung spent onto a grade it does not propose is caught")
    else:
        print("  FAIL a rung above its card's grade was allowed through")
        ok = False

    if any("neither spent nor on the conflict list" in p
           for p in invariants(spent[:-1], conflicts, [], docs, proposal, master)):
        print("  ok    a ruled person accounted for nowhere is caught")
    else:
        print("  FAIL an unaccounted person was allowed through")
        ok = False

    nokind = [dict(conflicts[0], kind="invented")] if conflicts else []
    if nokind and any("refused for an unknown reason" in p
                      for p in invariants(spent, nokind, [], docs, proposal, master)):
        print("  ok    a refusal citing no known reason is caught")
    else:
        print("  FAIL an unexplained refusal was allowed through")
        ok = False

    # The one this pass exists to make impossible: writing a rung would move a grade.
    moved = decide({pathlib.Path("hh_probe.json"): {
        "id": "hh_probe",
        "persons": [{"id": "probe", "grade": "attested"}]}}, proposal, master)
    if not moved[0]:
        print("  ok    a card the ladder never ruled on is never spent a rung")
    else:
        print("  FAIL a rung was spent onto a person with no ruling")
        ok = False

    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", action="store_true", help="write the rungs and the record")
    ap.add_argument("--check", action="store_true", help="re-derive and report any drift")
    ap.add_argument("--report", action="store_true", help="every rung spent, every refusal")
    ap.add_argument("--coverage", action="store_true", help="the ladder's reach, before/after")
    ap.add_argument("--gate", action="store_true", help="the invariants this pass owes")
    ap.add_argument("--self-test", action="store_true", help="break them on purpose")
    args = ap.parse_args()

    if args.self_test:
        return self_test()

    files, spent, conflicts, foreign, record = build()
    docs = {p: load(p) for p in sorted(HOUSEHOLDS.glob("*.json"))}
    proposal, master = load(PROPOSAL), load(MASTER)

    if args.gate:
        problems = invariants(spent, conflicts, foreign, docs, proposal, master)
        for problem in problems:
            print(f"   {problem}")
        if problems:
            print(f"   {len(problems)} problem(s)")
            return 1
        print(f"   OK: {len(spent)} rung(s) spent onto cards the ladder agrees with, "
              f"{len(conflicts)} conflict(s) left for the owner")
        return 0
    if args.report:
        report(spent, conflicts, record)
        return 0
    if args.coverage:
        coverage(record)
        return 0
    if args.check:
        drift = [p for p, text in files.items()
                 if not p.exists() or p.read_text(encoding="utf-8") != text]
        for p in drift:
            print(f"   DRIFT: {p.relative_to(ROOT)}")
        problems = invariants(spent, conflicts, foreign, docs, proposal, master)
        for problem in problems:
            print(f"   {problem}")
        if drift or problems:
            print(f"   {len(drift)} file(s) differ from what this pass derives; "
                  f"{len(problems)} invariant(s) broken")
            return 1
        print(f"   OK: {len(spent)} spent rung(s) re-derive from the ladder, "
              f"{len(conflicts)} conflict(s) still the owner's")
        return 0

    for path, text in files.items():
        path.write_text(text, encoding="utf-8")
    print(f"spent {len(spent)} rung(s) onto {len(files) - 1} household file(s); "
          f"{len(conflicts)} conflict(s) listed for the owner")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
