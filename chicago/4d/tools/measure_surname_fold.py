#!/usr/bin/env python3
"""What a LOOSER SURNAME FOLD would cost the land register's crosswalk (T-1001).

THE QUESTION, and it is a real one. `tools/namesake.py` folds surnames EXACTLY: the
surname gathers the rivals and the forename decides between them, and two spellings one
letter apart are two surnames to it. So `build_resident_crosswalk` reported `rivals[]`
empty on KIMBERLEY EDMUND S while the residents layer held Dr Edmund Stoughton Kimberly,
the closest namesake it could have had. An empty `rivals[]` means "no namesake of that
spelling", not "no namesake" — and T-0990's cohort B is DEFINED by that field, so the
fault is load-bearing rather than cosmetic.

The ticket asked for an ANSWER WITH A COUNT rather than an opinion: how many purchaser
spellings gain a rival under a fold that admits one letter, and which ruled proposals
change shape. This is that count. It is a MEASUREMENT and not a proposal: nothing here
changes the rule, and running it changes no committed file.

THE ANSWER IT GIVES, measured on the tree that shipped T-1001 — the numbers below are
reproduced by running this file, and are quoted rather than gated because the residents
layer grows on almost every ticket and a gate on them would go red for everybody:

    427 named purchaser spellings (of 431; four are firms or surname-only)
    200 of them gain at least one rival        47%
     42 proposals change shape                 24 named matches LOST, 18 refusals named
     39 of the 72 hand rulings gain a rival, and 18 of them sit on a proposal that moves

AND THE ANSWER IS NO. The losses are not noise. PEARSONS HIRAM is refused against 'Hiram
Pearson', CLYBOURNE ARCHIBALD against 'Archibald Clybourn', LLOYD ALEXANDER against
'Alexander Loyd', PRUYNE PETER against 'Peter Pryne' — in every one of them the "rival"
the loose fold gathers is THE SAME MAN under a variant spelling, and the rule refuses a
correct match for having made him his own rival. T-0993's BLANCHARD GURTREY is worse: its
hand `named` ruling is re-pointed onto the garbled card `blanshard_g`, so a written
judgement quietly changes who it names. And the fold reaches things no reader would
allow — KING NEHEMIAH gathers 'A. M. Wing', SMITH gathers 'Sherrygood Stith', HALL
gathers Hail, Hale, Hill and Hull.

So the mechanical fold stays exact, and a surname the sources spell two ways is RULED, one
cluster at a time, on a page that demonstrates the variation: rule C9 in
`data/residents/card_merge_rulings.json`, and `merged_card_surnames` in
`tools/read_land_sales.py`, which lets the register's spelling still reach the man the
ruling named. A ruling the derivation reads, never a distance it measures.

    tools/measure_surname_fold.py             the counts
    tools/measure_surname_fold.py --detail    every spelling that gains a rival
    tools/measure_surname_fold.py --self-test the distance function's own assertions
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import namesake                                    # noqa: E402
import read_land_sales as rls                      # noqa: E402


def one_letter_apart(a: str, b: str) -> bool:
    """Levenshtein distance of exactly one — a substitution, an insertion or a deletion.

    Equal strings are NOT one letter apart: this asks what a looser fold would ADD to the
    exact one, so the exact bucket is never counted twice.
    """
    if a == b:
        return False
    la, lb = len(a), len(b)
    if abs(la - lb) > 1:
        return False
    if la == lb:
        return sum(1 for x, y in zip(a, b) if x != y) == 1
    if la > lb:
        a, b, la, lb = b, a, lb, la
    i = 0
    while i < la and a[i] == b[i]:
        i += 1
    return a[i:] == b[i + 1:]


def decide(candidates, givens):
    """The person `namesake.choose` names among these candidates, or None."""
    if not candidates:
        return None
    return namesake.choose(" ".join(givens), [
        {"key": pid, "name": name, "given": " ".join(name.split()[:-1])}
        for pid, name, hh in candidates])["named"]


def measure() -> dict:
    rows = rls.read_tsv(rls.DOMAIN)
    by_surname = {}
    people = rls.resident_names()
    for pid, name, hh in people:
        by_surname.setdefault(name.split()[-1].upper(), []).append((pid, name, hh))
    # The comparison is against the rule AS IT STANDS, which since T-1001 gathers a person
    # under the surname a ruled card merge folded away as well as under his live one. So
    # the measured cost is what a loose fold would ADD to that, and Kimberley — the pair
    # that raised the question — is counted the way the crosswalk actually reads it now.
    by_person = {pid: (pid, name, hh) for pid, name, hh in people}
    for surname, survivor, _folded in rls.merged_card_surnames():
        row = by_person.get(survivor)
        if row and all(c[0] != survivor for c in by_surname.setdefault(surname, [])):
            by_surname[surname].append(row)
    surnames = sorted(by_surname)
    ruled = {r["purchaser_as_read"]: r for r in
             rls.load(rls.DOMAIN / rls.RULINGS_NAME).get("ruled") or []}

    spellings, seen = [], set()
    for row in rows:
        if row["purchaser"] not in seen:
            seen.add(row["purchaser"])
            spellings.append(row["purchaser"])

    named_spellings, gained, changed, ruled_gaining = [], [], [], []
    for as_read in spellings:
        surname, givens = rls.surname_of(as_read), rls.givens_of(as_read)
        if not givens or namesake.firm_style(" ".join(givens)):
            continue
        named_spellings.append(as_read)
        extra = [c for other in surnames
                 if one_letter_apart(other, surname)
                 for c in by_surname[other]]
        if not extra:
            continue
        exact = by_surname.get(surname, [])
        row = {"purchaser_as_read": as_read,
               "surname": surname,
               "residents_of_the_surname": [c[1] for c in exact],
               "gains": [c[1] for c in extra],
               "hand_ruled": ruled.get(as_read, {}).get("ruling")}
        gained.append(row)
        if row["hand_ruled"]:
            ruled_gaining.append(row)
        before, after = decide(exact, givens), decide(exact + extra, givens)
        if before != after:
            changed.append(dict(row, names_today=before, names_under_the_loose_fold=after))

    return {
        "spellings": len(spellings),
        "named_spellings": len(named_spellings),
        "gain_a_rival": len(gained),
        "proposals_that_change_shape": len(changed),
        "matches_lost": sum(1 for c in changed if c["names_today"]
                            and not c["names_under_the_loose_fold"]),
        "refusals_turned_into_matches": sum(1 for c in changed if not c["names_today"]
                                            and c["names_under_the_loose_fold"]),
        "matches_repointed": sum(1 for c in changed if c["names_today"]
                                 and c["names_under_the_loose_fold"]
                                 and c["names_today"] != c["names_under_the_loose_fold"]),
        "hand_rulings": len(ruled),
        "hand_rulings_that_gain_a_rival": len(ruled_gaining),
        "hand_rulings_on_a_proposal_that_moves": sum(1 for c in changed if c["hand_ruled"]),
        "gained": gained,
        "changed": changed,
    }


def report(detail: bool = False) -> int:
    m = measure()
    print("A ONE-LETTER SURNAME FOLD, PUT TO THE LAND REGISTER'S CROSSWALK")
    print("  purchaser spellings                          %4d" % m["spellings"])
    print("  …of which name a person (not a firm, not a")
    print("     surname alone)                            %4d" % m["named_spellings"])
    print("  gain at least one rival                      %4d   (%d%%)"
          % (m["gain_a_rival"], round(100 * m["gain_a_rival"] / m["named_spellings"])))
    print("  proposals that change shape                  %4d" % m["proposals_that_change_shape"])
    print("     · a named match LOST                      %4d" % m["matches_lost"])
    print("     · a refusal turned into a match           %4d" % m["refusals_turned_into_matches"])
    print("     · a match re-pointed at somebody else     %4d" % m["matches_repointed"])
    print("  hand rulings                                 %4d" % m["hand_rulings"])
    print("     · gaining a rival                         %4d" % m["hand_rulings_that_gain_a_rival"])
    print("     · sitting on a proposal that moves        %4d" % m["hand_rulings_on_a_proposal_that_moves"])
    if detail:
        print("\nEVERY SPELLING THAT GAINS A RIVAL")
        for row in m["gained"]:
            print("  %-26s %-9s exact: %s" % (
                row["purchaser_as_read"], row["hand_ruled"] or "",
                ", ".join(row["residents_of_the_surname"]) or "—"))
            print("  %-26s %-9s gains: %s" % ("", "", ", ".join(row["gains"])))
        print("\nEVERY PROPOSAL THAT CHANGES SHAPE")
        for row in m["changed"]:
            print("  %-26s %-9s %s -> %s" % (
                row["purchaser_as_read"], row["hand_ruled"] or "",
                row["names_today"] or "(refused)",
                row["names_under_the_loose_fold"] or "(refused)"))
    return 0


def self_test() -> int:
    fails = []

    def ok(cond, why):
        if not cond:
            fails.append(why)

    ok(one_letter_apart("KIMBERLEY", "KIMBERLY"),
       "a deleted letter must be one letter apart — this is the pair the ticket is about")
    ok(one_letter_apart("KIMBERLY", "KIMBERLEY"),
       "…and the distance must be symmetric")
    ok(one_letter_apart("CLYBOURNE", "CLYBOURN"),
       "a dropped final letter must be one letter apart")
    ok(one_letter_apart("HALL", "HULL"), "a substitution must be one letter apart")
    ok(not one_letter_apart("SMITH", "SMITH"),
       "a surname is not one letter from ITSELF — the exact bucket must never be counted "
       "twice, or every spelling would 'gain' its own people")
    ok(one_letter_apart("BLANCHARD", "BLANSHARD"),
       "C against S is a substitution, and this pair is exactly why the loose fold "
       "re-points T-0993's hand ruling onto a garbled card")
    ok(not one_letter_apart("KIMBERLEY", "KIMBALL"),
       "a surname two letters shorter and different besides is not one letter apart")
    ok(not one_letter_apart("KING", "KINGSTON"),
       "four letters apart is not one letter apart")
    ok(not one_letter_apart("", "AB"), "an empty name is not one letter from a pair")
    ok(one_letter_apart("", "A"), "an empty name is one letter from a single letter")

    m = measure()
    ok(m["gain_a_rival"] > 0,
       "the measurement must find SOMETHING — a zero here means the fold is not being "
       "applied at all and the answer would read as 'no cost'")
    ok(m["proposals_that_change_shape"] >= m["hand_rulings_on_a_proposal_that_moves"],
       "a hand ruling on a moving proposal is one of the moving proposals")

    for fail in fails:
        print("   %s" % fail)
    print("   %s" % ("OK: every assertion holds" if not fails
                     else "%d failed" % len(fails)))
    return 1 if fails else 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--detail", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args(argv)
    if args.self_test:
        return self_test()
    if args.json:
        print(json.dumps(measure(), indent=1))
        return 0
    return report(detail=args.detail)


if __name__ == "__main__":
    sys.exit(main())
