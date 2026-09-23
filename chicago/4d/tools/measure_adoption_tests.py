#!/usr/bin/env python3
"""Evaluate method rule 6's three adoption tests for a roof, as a command.

ROADMAP T-A15, and the same move T-A14 made for the face rule. Rule 6 of
`data/reconstruction/1835_inferred_household_programme.json` says an anonymous block
roof may be adopted by an inferred household only where ALL THREE of these pass:

  1. the trade's own argument states IN ITS COMMITTED TEXT that its count is a floor
     rather than a bound;
  2. the roof's FAMILY is one this layer already houses that trade in;
  3. the roof's DIVISION is one this layer already houses that trade in.

Tests 2 and 3 are table lookups and have been reproducible since K21 put a `family` on
every roof this layer raises. **Test 1 is a statement about a paragraph of prose, and
until this tool nothing read it.** Every parcel that has cited it has cited it from
memory, and on 2026-08-15 that produced a claim which does not reproduce: T-A14 recorded
that the D4 it was dealt "passes all three tests" for the TEAMSTERS and the D2 for the
LAUNDRESSES. Measured here, neither trade's argument contains any statement about a floor
at all — the only occurrence of the word in the laundress argument is Andreas's "with the
floor covered besides", which is a plank floor in a boarding house. Only the CARPENTERS
and the LABOURERS state it. That is the difference between a rule and a habit, and it is
why this file exists rather than another remembered number.

**What test 1 is not.** It is not "method rule 3 lists this trade as unbounded". Rule 3
names four trades whose count is argued from the town's building rate rather than from a
roof cap — carpenters, labourers, laundresses, teamsters — and rule 6 could have been
written to point at that list. It was not: it was written to point at the trade's own
argument, which is a stronger requirement, because an argument that has never claimed to
be a floor has never invited anybody to raise it. The two readings disagree for exactly
two trades. **K28 settled it on 2026-08-16 in favour of the literal reading this tool
already implements** (rule 6 clause iii), so the `*` below marks a refusal with a named
remedy rather than an open question: if the laundresses' or the teamsters' count really
is a floor, the place to say so is that trade's own argument. This still prints BOTH
readings, because the reader is owed the disagreement the decision was made about.

Detection is deliberately conservative and always shows its working: a match is a
sentence in which "floor" is used as a predicate of the count, and every matched sentence
is printed so a reader can refuse it. A trade whose argument says nothing is reported as
NOT STATED, which is a failure — silence is not a pass, exactly as T-A5 held for test 2.

**TESTS 2 AND 3 READ TWO PROJECTIONS OF ONE TABLE, AND T-A3H MEASURED WHAT THAT ADMITS.**
The layer houses a trade in (family, division) PAIRS. Rule 6 says in its own text that
its three tests are independent, so test 2 asks the set of families and test 3 the set of
divisions, and a roof can pass on a family taken from one division and a division taken
from another family — a pairing this layer has never housed the trade in. That is not a
corner case: it is every "second roof" any block parcel has ever recorded. The carpenters'
D4 candidacy rests on one household in the NORTH Division and the labourers' D2 on four in
the NORTH and WEST, while every carpenter and labourer this layer houses in the SOUTH
Division is in a D3 or a D1. So the `pair housed` column, and `--pairs`.

**K28 REFUSED THE PAIR READING ON 2026-08-16 (rule 6 clause i), and the reason is the one
this tool had already put in front of it.** Requiring the pair refuses the fourteenth
labouring household — T-A4's D1 adopted in the West Division, argued in exactly the
projected form — and rule 6 names that adoption as one of the four decisions its third
test recovers. Rule 6 says in the same breath that a test which has to be told the answers
is a preference and one that recovers them is a rule; the pair reading has to be told one
of the four. So the projections stand, and what bounds them is the CAP K28 added in the
same clause list: **one adoption per trade per block parcel** (clause ii). The projections
widen which roofs are eligible; the cap bounds how fast any of them may move a count.

Standalone, and still not wired into tools/check.sh. What IS gated now lives in
`tools/generate_inferred_households.py`, which refuses an adoption by a trade whose own
argument states no floor (clause iii) and a block that adopts one trade twice (clause ii).
This tool reports the table those gates are decided against; a second copy of the rule in
the gate path is how the two would drift, which is why the gate imports `floor_evidence`
from here instead of restating the predicate.

Usage:
    tools/measure_adoption_tests.py D1 south          # one roof family in one division
    tools/measure_adoption_tests.py --roof recon_1835_blk_randolph_clark_d1_06
    tools/measure_adoption_tests.py --floors          # which trades state a floor, and why
    tools/measure_adoption_tests.py --pairs           # housed pairs vs the projections
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
STRUCTURES = DATA / "structures"
PROGRAMME = DATA / "reconstruction" / "1835_inferred_household_programme.json"

# Rule 3's four trades, quoted from the committed method list rather than retyped as a
# judgement. Used only to REPORT the disagreement described in the module docstring.
RULE_3_UNBOUNDED = ("carpenter", "labourer", "laundress", "teamster")

# "floor" used as a predicate of the count. The negative case this must not match is
# Andreas's "with the floor covered besides" in the laundress argument, where the floor
# is made of planks.
FLOOR_PREDICATE = re.compile(
    r"\b(?:is|as|still|remains|calls\s+itself|stated\s+as|state[sd]?)\s+"
    r"(?:a|its\s+own)?\s*\bfloor\b"
    r"|\ba\s+floor\s+(?:by|under|beneath)\b",
    re.IGNORECASE,
)


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def family_of(structure_id: str) -> str | None:
    """The programme family a committed roof carries, or None.

    K21 put `reconstruction.family` on every roof this layer raises; the block parcels'
    roofs have carried it from the start. A roof with no family answers no test.
    """
    path = STRUCTURES / f"{structure_id}.json"
    if not path.exists():
        return None
    record = load(path)

    def find(node):
        if isinstance(node, dict):
            if isinstance(node.get("family"), str):
                return node["family"]
            for value in node.values():
                found = find(value)
                if found:
                    return found
        elif isinstance(node, list):
            for value in node:
                found = find(value)
                if found:
                    return found
        return None

    return find(record)


def sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"(?<=[.])\s+", text) if s.strip()]


def floor_evidence(argument: str) -> list[str]:
    """Sentences in which the trade's own argument calls its count a floor."""
    return [s for s in sentences(argument) if FLOOR_PREDICATE.search(s)]


def table(programme: dict) -> dict[str, set[tuple[str, str]]]:
    """trade -> {(family, division)} this layer already houses it in."""
    housed: dict[str, set[tuple[str, str]]] = {}
    for household in programme["households"]:
        family = family_of(household["lives_at"]) if household.get("lives_at") else None
        if not family:
            continue
        housed.setdefault(household["occupation"], set()).add(
            (family, household["division"]))
    return housed


def report(programme: dict, family: str, division: str, verbose: bool) -> int:
    housed = table(programme)
    census = {e["occupation"]: e for e in programme["occupation_census"]}
    print(f"method rule 6, evaluated for a {family} roof in the "
          f"{division} division\n")
    print(f"  {'trade':<22}{'1 floor stated':<16}{'2 family':<11}"
          f"{'3 division':<12}{'verdict':<12}pair housed")
    passing = []
    projected = []
    for trade in sorted(census):
        pairs = housed.get(trade, set())
        families = {f for f, _ in pairs}
        divisions = {d for _, d in pairs}
        if family not in families and division not in divisions:
            continue
        evidence = floor_evidence(census[trade]["argument"])
        t1, t2, t3 = bool(evidence), family in families, division in divisions
        verdict = "ADOPTABLE" if (t1 and t2 and t3) else "refused"
        if t1 and t2 and t3:
            passing.append(trade)
            if (family, division) not in pairs:
                projected.append(trade)
        rule3 = " *" if (not t1 and trade in RULE_3_UNBOUNDED) else ""
        pair = "yes" if (family, division) in pairs else "NO"
        print(f"  {trade:<22}{('yes' if t1 else 'NOT STATED') + rule3:<16}"
              f"{('yes' if t2 else 'no'):<11}{('yes' if t3 else 'no'):<12}"
              f"{verdict:<12}{pair}")
        if verbose and evidence:
            for line in evidence:
                print(f"      floor: {line}")
    print()
    if passing:
        print(f"  {len(passing)} trade(s) pass all three tests: {', '.join(passing)}")
    else:
        print("  no trade passes all three tests — this roof stays an anonymous "
              "count-unit")
    print("\n  * method rule 3 names this trade unbounded, but its own argument never "
          "claims a\n    floor, so it fails test 1 as rule 6 is written. K28 settled "
          "that reading on\n    2026-08-16 (rule 6 clause iii): the remedy is to argue "
          "the floor in the trade's\n    own argument, not to widen the test.")
    for trade in projected:
        pairs = housed.get(trade, set())
        fam_where = sorted({d for f, d in pairs if f == family})
        div_what = sorted({f for f, d in pairs if d == division})
        print(f"\n  {trade}: PASSES ON A PAIR THIS LAYER HAS NEVER HOUSED. It houses no "
              f"{trade}\n  in a {family} in the {division} division. Test 2 passes on the "
              f"{family}s it houses\n  this trade in — {', '.join(fam_where)} — and test 3 "
              f"on the {division} division, where it\n  houses the trade in "
              f"{', '.join(div_what)}. The verdict is the product of two projections\n"
              f"  of one table, which is what rule 6 means by "
              f"\"the three tests are independent\".")
    print("\n  Passing all three is permission, not an instruction — and since K28 "
          "(2026-08-16)\n  that sentence is a clause rather than a manner of speaking: "
          "rule 6 caps a block\n  parcel at ONE adoption per trade, so a block dealt two "
          "of a trade's families may\n  hand it one roof. The table is read as two "
          "PROJECTIONS and not as pairs; the\n  `pair housed` column above is therefore "
          "reporting, not a fourth test.")
    return 0


def pairs_report(programme: dict) -> int:
    """Every (family, division) pair this layer houses each trade in.

    Tests 2 and 3 are evaluated against the two PROJECTIONS of this table, so a roof
    passes on a family taken from one row and a division taken from another. T-A3h
    measured what that costs: every "second roof" any block parcel has recorded — the
    carpenters' D4 and the labourers' D2, in the South Division, at nine blocks — is a
    pair that appears nowhere below. The stricter reading is NOT obviously right and
    this tool does not take it: requiring the pair would refuse the fourteenth
    labouring household, a D1 adopted in the West Division when this layer housed
    labourers west of the river only in D2s, and rule 6 names that adoption as one of
    the four its third test recovers.
    """
    housed = table(programme)
    print("the (family, division) pairs this layer houses each trade in, and the "
          "projections\nrule 6's tests 2 and 3 are actually evaluated against\n")
    for trade in sorted(housed):
        pairs = sorted(housed[trade])
        families = sorted({f for f, _ in pairs})
        divisions = sorted({d for _, d in pairs})
        cross = [(f, d) for f in families for d in divisions if (f, d) not in pairs]
        print(f"  {trade}")
        print(f"    housed:    {', '.join(f'{f}/{d}' for f, d in pairs)}")
        print(f"    projected: {', '.join(families)} x {', '.join(divisions)}")
        if cross:
            print("    ADMITTED BY THE PROJECTIONS AND HOUSED BY NOTHING: "
                  + ", ".join(f"{f}/{d}" for f, d in cross))
    print("\n  A pair on the last line passes tests 2 and 3 on evidence that is never "
          "about\n  the same roof twice. K28 decided on 2026-08-16 that this is the rule "
          "working and\n  not a defect (rule 6 clause i): requiring the PAIR would refuse "
          "T-A4's fourteenth\n  labouring household, which rule 6 names as one of the four "
          "decisions its third\n  test recovers. What bounds the projections is the cap — "
          "one adoption per trade\n  per block parcel — and not a narrower table.")
    return 0


def floors(programme: dict) -> int:
    census = programme["occupation_census"]
    print("test 1 — which trades state, in their own committed argument, that their "
          "count is a floor\n")
    for entry in sorted(census, key=lambda e: e["occupation"]):
        evidence = floor_evidence(entry["argument"])
        mark = "STATED    " if evidence else "not stated"
        rule3 = "  <- rule 3 calls this trade unbounded" if (
            not evidence and entry["occupation"] in RULE_3_UNBOUNDED) else ""
        print(f"  {entry['occupation']:<22}{mark}{rule3}")
        for line in evidence[:1]:
            print(f"      {line}")
    print("\n  A trade rule 3 calls unbounded whose argument never claims a floor fails "
          "test 1\n  on the literal reading rule 6 is written in, and K28 settled that "
          "reading on\n  2026-08-16 (rule 6 clause iii). "
          "tools/generate_inferred_households.py refuses such an\n  adoption outright, "
          "importing the predicate above so the gate and this report\n  cannot disagree "
          "about what a floor is.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("family", nargs="?", help="programme family, e.g. D1")
    ap.add_argument("division", nargs="?", help="south | north | west")
    ap.add_argument("--roof", help="read the family from a committed structure id")
    ap.add_argument("--floors", action="store_true",
                    help="report test 1 for every trade and quote the evidence")
    ap.add_argument("--pairs", action="store_true",
                    help="the (family, division) pairs this layer houses each trade in, "
                         "against the two projections tests 2 and 3 read")
    ap.add_argument("-v", "--verbose", action="store_true",
                    help="quote the sentence each floor verdict rests on")
    args = ap.parse_args()

    programme = load(PROGRAMME)
    if args.floors:
        return floors(programme)
    if args.pairs:
        return pairs_report(programme)

    family, division = args.family, args.division
    if args.roof:
        family = family_of(args.roof)
        if not family:
            print(f"{args.roof}: no committed record, or it names no family")
            return 1
        record = load(STRUCTURES / f"{args.roof}.json")
        division = division or (record.get("reconstruction") or {}).get("district")
    if not family or not division:
        ap.error("give a family and a division, or --roof, or --floors")
    return report(programme, family.upper(), division.lower(), args.verbose)


if __name__ == "__main__":
    raise SystemExit(main())
