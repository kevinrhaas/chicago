#!/usr/bin/env python3
"""What a ONE-LETTER CANDIDATE TEST would propose over the town's cards (T-1002).

THE QUESTION, and T-0961 found it the hard way. `clusters()` in
`tools/consolidate_town_cards.py` buckets the town's cards by the SURNAME AS A STRING and
then lets `compatible()` weigh the forenames — a full word against the same word, an
initial the word begins with, or a card that prints a title and no forename at all.
Nothing in that test admits a LETTER. So three duplicate pairs the project holds were
never proposed to it, not refused and not deferred:

    beaubien_madore     Madore Benjamin Beaubien   / beaubien_medore_b   Medore B Beaubien
    clybourne_archibald Archibald Clybourne        / clybourn_archibald  Archibald Clybourn
    heacock_russel_e    Russel E. Heacock          / heacock_russell_e   Russell E Heacock

and each was found by hand, by one afternoon's reading of one table. The forty-one
clusters `data/residents/card_merge_rulings.json` holds are the pairs the string test
could see, and that file had no way to say how many it could not. This tool is the way.

WHAT IT DOES. It runs the candidate test again with one letter of slack — Levenshtein
distance exactly 1, the same `one_letter_apart()` T-1001 wrote and `check.sh` already
gates — on the SURNAME, and on the first forename token where the surname is exact. Then
it subtracts the pairs the exact test already proposes, and prints what is left. It is a
MEASUREMENT and not a proposal: nothing here changes `clusters()`, and running it changes
no committed file.

THE ANSWER IT GIVES — quoted rather than gated for equality, because the residents layer
grows on almost every ticket. Measured on the tree T-1002 read, BEFORE its three merges:

    1,376 cards that name somebody
       21 pairs the exact candidate test already proposes
       71 pairs a one-letter test would ADD — 63 on the surname, 8 on the forename
       12 of those 71 already carry a written ruling

and on the tree that ticket shipped, with its three folded away: 1,373 cards and 68 pairs,
62 on the surname and 6 on the forename. The three the ticket ruled are gone from the list
because the cards are one card each now, which is the only way a pair leaves it.

SO THE CLASS IS NOT THREE, AND IT IS NOT THE 71 EITHER. Read the list and it falls into
three kinds that want three different answers, which is why T-1002 rules its three and
sends the rest to an epic rather than folding on a distance:

  * A SPELLING THE SOURCES REALLY DO SET TWO WAYS — Clybourn/Clybourne, Foot/Foote,
    Forsyth/Forsythe, Lloyd/Loyd, Pearson/Pearsons, Pruyne/Pryne, Eldredge/Eldridge,
    Wesencraft/Wessencraft. These are the C7/C9 shape and each needs its own page.
  * A CARD MINTED OFF A GARBLE — `chark_john_a` for Clark, `tmple_john_t` for Temple,
    `smow_george_w` for Snow, `canp_george_s` for Camp, `mgregor_a` for McGregor,
    `blanshard_f_g` for Blanchard. R5 refuses these by rule and T-0695 is the ticket that
    reads them; a fold here would repair a wreck by guessing at it.
  * AN INITIAL GATHERED ACROSS A FOLDED SURNAME — J. Green against Major John Greene,
    J. B. Falker against James Walker, J. Ambrose Wight against three Wrights. The slack
    is on the surname and the forename inference is `compatible()`'s own, so the test
    cannot decline it; what it means in practice is that a fold on the surname multiplies
    the initials it reaches, and R2's two-rivals refusal is doing most of the work.
  * TWO PEOPLE ONE LETTER APART — J. H. Collins against John Rollins, John Hale against
    John Vale, Mark Noble against Mary Noble, James Sheldon against James Wheldon. A
    distance cannot tell these from the first kind, and that is the whole argument for
    ruling a cluster on a page instead of on a distance. T-1001 measured the same thing
    over the land register and answered NO for the same reason.

    tools/measure_card_fuzzy_candidates.py             the counts
    tools/measure_card_fuzzy_candidates.py --detail    every pair the fold would add
    tools/measure_card_fuzzy_candidates.py --json      the same, machine-readable
    tools/measure_card_fuzzy_candidates.py --self-test the assertions still fire
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import consolidate_town_cards as ctc                     # noqa: E402
from measure_surname_fold import one_letter_apart        # noqa: E402


def named_cards(town: list) -> list:
    """(surname, forename tokens, person_id, name, household) for every card that names
    somebody. A card whose name parses to nothing is not a candidate for anything."""
    rows = []
    for row in town:
        parsed = ctc.forename_tokens(row["name"])
        if parsed:
            rows.append((parsed[0], parsed[1], row["person"], row["name"], row["household"]))
    return rows


def exact_pairs(town: list) -> set:
    """Every pair the candidate test as it stands already puts in one cluster."""
    out = set()
    for cluster in ctc.clusters(town):
        ids = [card["person"] for card in cluster["cards"]]
        for i in range(len(ids)):
            for j in range(i + 1, len(ids)):
                out.add(tuple(sorted((ids[i], ids[j]))))
    return out


def folds(a: tuple, b: tuple) -> str | None:
    """Which side a one letter of slack would have to fold for these two to meet, or None.

    `surname` where the surnames are one letter apart and the forenames agree under the
    EXISTING rule; `forename` where the surnames are identical and the first forename
    tokens are one letter apart. A pair that needs slack on BOTH sides is not proposed:
    two letters is not one, and admitting it would gather every misread card to every
    other.
    """
    surname_exact = a[0] == b[0]
    surname_near = one_letter_apart(a[0], b[0])
    if not (surname_exact or surname_near):
        return None
    ga, gb = a[1], b[1]
    if surname_near:
        return "surname" if ctc.compatible(a, b) else None
    if not ga or not gb:
        return None                      # a title and no forename: the exact test has it
    x, y = ga[0], gb[0]
    if len(x) == 1 or len(y) == 1:
        return None                      # an initial: the exact test has it, or refuses it
    return "forename" if one_letter_apart(x, y) else None


def measure(root: Path | None = None) -> dict:
    town = ctc.read_town(root)
    cards = named_cards(town)
    already = exact_pairs(ctc.read_town(root))
    ruled = ctc.ruled_cards(ctc.load_rulings())

    added = []
    for i in range(len(cards)):
        for j in range(i + 1, len(cards)):
            a, b = cards[i], cards[j]
            if tuple(sorted((a[2], b[2]))) in already:
                continue
            side = folds(a, b)
            if not side:
                continue
            rulings = sorted({ruled[pid]["cluster"] for pid in (a[2], b[2])
                              if pid in ruled and ruled[pid].get("cluster")})
            added.append({
                "folds": side,
                "cards": [{"person": a[2], "name": a[3], "household": a[4]},
                          {"person": b[2], "name": b[3], "household": b[4]}],
                "ruled_in_clusters": rulings,
            })
    added.sort(key=lambda row: row["cards"][0]["person"])
    return {
        "cards_that_name_somebody": len(cards),
        "pairs_the_exact_test_proposes": len(already),
        "pairs_a_one_letter_test_would_add": len(added),
        "of_those_already_ruled": sum(1 for row in added if row["ruled_in_clusters"]),
        "folding_the_surname": sum(1 for row in added if row["folds"] == "surname"),
        "folding_the_forename": sum(1 for row in added if row["folds"] == "forename"),
        "added": added,
    }


def report(detail: bool = False) -> int:
    m = measure()
    print("   %5d cards that name somebody" % m["cards_that_name_somebody"])
    print("   %5d pairs the exact candidate test already proposes"
          % m["pairs_the_exact_test_proposes"])
    print("   %5d pairs one letter of slack would ADD (%d on the surname, %d on the "
          "forename)" % (m["pairs_a_one_letter_test_would_add"], m["folding_the_surname"],
                         m["folding_the_forename"]))
    print("   %5d of them carry a written ruling already" % m["of_those_already_ruled"])
    if detail:
        for row in m["added"]:
            a, b = row["cards"]
            print("     %-9s %-34s (%s)" % (row["folds"], a["name"], a["person"]))
            print("               %-34s (%s)%s"
                  % (b["name"], b["person"],
                     "  ruled: " + ", ".join(row["ruled_in_clusters"])
                     if row["ruled_in_clusters"] else ""))
    else:
        print("   tools/measure_card_fuzzy_candidates.py --detail lists every pair")
    return 0


def self_test() -> int:
    fails = []

    def ok(cond, why):
        if not cond:
            fails.append(why)

    beaubien = ("beaubien", ["madore", "benjamin"])
    medore = ("beaubien", ["medore", "b"])
    ok(folds(beaubien, medore) == "forename",
       "Madore against Medore must fold on the FORENAME — one of the three pairs the "
       "ticket exists for")
    ok(folds(("clybourne", ["archibald"]), ("clybourn", ["archibald"])) == "surname",
       "Clybourne against Clybourn must fold on the SURNAME")
    ok(folds(("heacock", ["russel", "e"]), ("heacock", ["russell", "e"])) == "forename",
       "Russel against Russell must fold on the FORENAME")
    ok(folds(("smith", ["john"]), ("smith", ["john"])) is None,
       "two cards the EXACT test already joins must not be counted as something the fold "
       "would add — the exact bucket is never counted twice")
    ok(folds(("smith", ["j"]), ("smyth", ["john"])) == "surname",
       "an INITIAL against a full forename IS proposed when the surname folds, and this "
       "assertion records that on purpose: the slack is on the SURNAME and the forename "
       "inference is the one `compatible()` already makes, so refusing it here would be "
       "the fuzzy test declining to run the exact test's own rule. It is also a large "
       "part of why the list this tool prints is noisy — J. Green gathers John Greene, "
       "and J. B. Falker gathers James Walker, on the same clause")
    ok(folds(("smith", ["j"]), ("smith", ["k"])) is None,
       "two bare initials one letter apart are not a spelling variation — every initial "
       "in the alphabet is one letter from every other")
    ok(folds(("smyth", ["john"]), ("smith", ["jahn"])) is None,
       "slack on BOTH sides is two letters, not one, and is never proposed")
    ok(folds(("kimberley", ["edmund", "s"]), ("kimberly", ["edmund", "s"])) == "surname",
       "T-1001's own pair must be reachable by this test — it is the precedent the "
       "ticket's third acceptance clause rests on")

    m = measure()
    ok(m["pairs_a_one_letter_test_would_add"] > 0,
       "the measurement must find SOMETHING — a zero here means the fold is not being "
       "applied at all, and the answer would read as 'the class is only the three'")
    ok(m["cards_that_name_somebody"] > 1000,
       "the town's cards must be being read at all")
    ok(m["folding_the_surname"] + m["folding_the_forename"]
       == m["pairs_a_one_letter_test_would_add"],
       "every added pair folds on exactly one side, so the two counts must sum to the "
       "total — a third kind appearing here means folds() has grown a case the report "
       "does not print")
    ids = {tuple(sorted(c["person"] for c in row["cards"])) for row in m["added"]}
    for pair in (("beaubien_madore", "beaubien_medore_b"),
                 ("clybourn_archibald", "clybourne_archibald"),
                 ("heacock_russel_e", "heacock_russell_e")):
        ok(tuple(sorted(pair)) in ids or all(
            pid not in {c["person"] for row in m["added"] for c in row["cards"]}
            for pid in pair),
           "T-1002's pair %s must either be proposed here or be gone from the layer, "
           "folded away by the ruling — if it is neither, this test has stopped seeing "
           "the pairs it was written for" % " / ".join(pair))

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
        print(json.dumps(measure(), indent=1, ensure_ascii=False))
        return 0
    return report(detail=args.detail)


if __name__ == "__main__":
    sys.exit(main())
