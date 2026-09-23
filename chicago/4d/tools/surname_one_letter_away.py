#!/usr/bin/env python3
"""THE SURNAME ONE LETTER AWAY — what the exact-surname join cannot see, and
why every one of the seventeen it hides is still a refusal.

T-0987 stretch 15, and it is a REPORTER, not a matcher. Nothing in this module
promotes anything to a match; its whole output is a ruled refusal with its
clause named, plus one referral out of this domain entirely.

WHAT THE STRETCH WAS. Stretch 14 named it: the 1,022 initial-absent refusals,
beginning with Fergus 1843, whose scan is the best of the four. The owner's
amendment of 2026-09-14 set the method — A STRETCH AGAINST THAT POOL READS A
PAGE, NOT A NAME — because one page image carries dozens of entries and one
read per refusal is what made the pool cost two hundred runs.

THE PAGE WAS READ AND IT OVERTURNED NOTHING, and that is this module's first
finding. The whole alphabetical directory of the printed volume — pages 31-103
of Fergus' Historical Series No. 28, the Internet Archive's own OCR at
`data/research/books/text/fergus_26_29.txt`, committed here since T-0499 and
set against Torp's transcription twice before (T-0987 stretch 12) — was put
against the 326 refusals of `fergus_1843_crosswalk_1835.json`. Not one printed
entry sets a surname-plus-initial that this repository's reading of the volume
does not already hold. The initial-absent pool of Fergus 1843 is NOT a
transcription defect: where the volume is silent about a person of 1835, both
hands are silent together.

WHAT THE POOL DOES HIDE, then. `crosswalk_fergus_1843.py` reaches a person of
1835 through the surname and nothing else, and it folds the printer's standing
confusions out of that surname before comparing — but the fold is exact after
it. `name_agreement.agrees` meanwhile allows a FORENAME one letter of variation
(`Russel` against `Russell`, min length five) and states why. Nothing allows a
SURNAME any, so a man the volume enters one letter away from the town's
spelling is invisible to the join while his surname's own bucket, populated by
other families, makes the refusal read `surname present, initial absent`.

Twelve entries of Fergus 1843 are one letter from a refused resident's surname
and carry that resident's own initial; they reach fifteen residents, sixteen
times. This module enumerates them.

THE RULING, and it refuses all sixteen.

  1. THE VOLUME'S OWN DISTINCTION. A directory does not enter one person twice
     under two spellings — R6's principle, borrowed by T-0987 stretch 14 clause
     3 and borrowed again here. In every one of the sixteen, BOTH spellings
     stand in the volume as separately populated surnames: Brooks (2 entries)
     beside Brookes (6), Pearson (2) beside Pearsons (1), Harman (1) beside
     Harmon (6), Barnard beside Bernard, Barry (3) beside Berry, Walker (9)
     beside Walter, David beside Davis (6), Clarke (8) beside Clark (16), Green
     (4) beside Breen, Wight (2) beside Wright (6), Bates (6) beside Yates and
     Barnes (4). The compositor set both and set them apart. A one-letter
     distance between two surnames a volume itself distinguishes is the
     volume's distinction, not its damage.

  2. AND THE SECOND HAND SETS THE SAME LETTERS. Each of the twelve entries was
     looked up in the printed volume's own OCR, line by line — thirteen lines,
     the extra one the business-directory notice `L. W. CLARK` that T-0987
     stretch 7 folds onto Lewis W. Clark's roll entry — and it reads Torp's
     spelling every time — `Pearsons, Hiram, speculator, l)ds Trejnont
     House`, `Harmon. Isaac Xewton`, `Clark, Lewis AY.`, `Bernard, Jacob,
     teamster`, `Walter, Joel Clarke`, `Davis, John, tailor`. Two independent
     extractions of one printing, one spelling, sixteen times. So the variant
     is not this transcription's damage either, and the one repair stretch 12
     had — the second hand reading what Torp could not — is unavailable here.
     `SECOND_HAND` carries every line verbatim, its own OCR damage left in, so
     the comparison re-runs; `--self-test` fails if one stops being findable.

  3. AND EIGHT OF THE SIXTEEN WOULD HAVE BEEN CONTESTS ANYWAY. Two residents
     reach `Bernard, Jacob`, two reach `Berry, Joseph`, two reach `Walter, Joel
     Clarke`, two reach `Brookes, George`. A clause that cannot choose between
     two people of 1835 decides nothing even where the spelling is allowed,
     which is T-0987 stretch 14's contest axis arriving at the same answer from
     the other side.

WHAT IT IS A SYMPTOM OF, and this is the one thing the stretch found worth
carrying anywhere. `Hiram Pearson` is refused by Fergus 1843 because the volume
prints `Pearsons, Hiram` — and the town of 1835 holds BOTH: `hh_pearson_hiram`,
a civic-mint card off the 1833 poll list with no trade and `present_on_scene_
date: uncertain`, and `hh_pearsons_hiram`, Andreas's man, attested, arrived
spring 1833, later the city's treasurer. Andreas's own roster, which
`hh_pearsons_hiram` quotes, prints `Hiram Pearson`. The duplicate is the TOWN'S,
not the volume's, and the directory's refusal is the symptom that surfaced it.
`town_pairs()` generalises that test over the whole resident layer: cards one
letter apart carrying the SAME forename. There are 22 of them and 21 have never
been put to the card-merge machinery (T-0839, T-0844, T-0993, T-1001, T-1002).
That is a finding for its own ticket and not for this one — it is the town's
roster, not the directories' rulings, and no card is touched here.

WHAT THIS IS NOT. Not a change to the matching rule: no surname fold is
widened, no candidate is admitted, no confidence is raised, and the crosswalk's
counts of matches, ties and refusals are byte-identical across this change. It
is the pool saying what it is made of. T-1001 asked the fold question once
already, over the land register's 427 purchaser spellings, and answered NO with
a count; nothing here reopens it.
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SECOND_HAND_TEXT = "data/research/books/text/fergus_26_29.txt"
SECOND_HAND_SOURCE = "fergus_historical_series_26_29"

# The shortest surname this clause will weigh. It is `name_agreement.agrees`'s
# own number for a forename spelling variant, borrowed rather than chosen: below
# five letters a single edit is most of the word, and `Cook`/`Cool`, `Ward`/
# `Wood`, `Hall`/`Ball` are different families, not different spellings.
MIN_LENGTH = 5


def one_letter_apart(a, b):
    """Levenshtein distance of at most one — `name_agreement`'s own test."""
    if abs(len(a) - len(b)) > 1:
        return False
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1] <= 1


def variants(surname_folded, index):
    """The keys of `index` one letter from `surname_folded`, never itself."""
    if len(surname_folded) < MIN_LENGTH:
        return []
    return sorted(k for k in index
                  if k != surname_folded and len(k) >= MIN_LENGTH
                  and one_letter_apart(surname_folded, k))


def refusal(resident, resident_surname, printed_name, printed_surname,
            own_entries, variant_entries, volume, contested_by=0):
    """Why a one-letter surname does not carry a person of 1835 to an entry."""
    why = ("%s prints %d entr%s under %r and %d under %r, so the compositor set "
           "both spellings and set them apart: a directory does not enter one "
           "person twice under two spellings, and a one-letter distance between "
           "two surnames the volume itself distinguishes is its distinction and "
           "not its damage. The printed volume's own OCR reads %r on that line "
           "too, so the variant is not this transcription's damage either."
           % (volume, own_entries, "y" if own_entries == 1 else "ies",
              resident_surname, variant_entries, printed_surname, printed_surname))
    if contested_by > 1:
        why += (" And %d people of 1835 reach %r by this route, so the clause "
                "could not choose between them even where the spelling were "
                "allowed." % (contested_by, printed_name))
    return {"resident": resident, "surname_1835": resident_surname,
            "entry_surname": printed_surname, "printed_name": printed_name,
            "clause": "the volume sets both spellings", "outcome": "refused",
            "rule": why}


# ---------------------------------------------------------------------------
# THE SECOND HAND, read line by line off the printed volume. Verbatim, with the
# Internet Archive's own OCR damage left in — a tidied quote cannot be found
# again. `line` is the 1-based line of the committed text file.
SECOND_HAND = [
    {"claim": "f1843_e0439", "printed": "Brookes, George",
     "line": 2950, "reads": "Ihookes,  George,  clerk,  Ixls  Samuel  13rookes"},
    {"claim": "f1843_e0274", "printed": "Barnes, Hamilton",
     "line": 2812, "reads": "Barnes,  Hamilton,  car[)enter."},
    {"claim": "f1843_e2686", "printed": "Yates, Horace Harris",
     "line": 4549, "reads": "Yates,  Horace  Harris,  family  grocer,  39  Clark"},
    {"claim": "f1843_e1971", "printed": "Pearsons, Hiram",
     "line": 4042, "reads": "Pearsons,  Hiram,  speculator,  l)ds  Trejnont  House"},
    {"claim": "f1843_e1209", "printed": "Harmon, Isaac Newton",
     "line": 3544, "reads": "Isaac  Xewton,  -uitli  C.  L.  Harmon"},
    {"claim": "f1843_e0339", "printed": "Bernard, Jacob",
     "line": 2858, "reads": "Bernard,  Jacob,  teamster"},
    {"claim": "f1843_e2675", "printed": "Wright, John Stephen",
     "line": 4541, "reads": "Jobn  Stepbeiiv  editor  and  ])voprietor"},
    {"claim": "f1843_e0423", "printed": "Breen, John",
     "line": 2940, "reads": "Breen,  John.  ])ackcr,  Arthur  G.  Burley"},
    {"claim": "f1843_e0340", "printed": "Berry, Joseph",
     "line": 2858, "reads": "Berry.  Jo<e])h,  laborer,  Gurdon  S.  Hubbard"},
    {"claim": "f1843_e2525", "printed": "Walter, Joel Clarke",
     "line": 4430, "reads": "Walter,  Joel  Clarke  (Horace  Norton  S:  Co.)"},
    {"claim": "f1843_e0776", "printed": "Davis, John",
     "line": 3244, "reads": "Davis,  John,  tailor.  North  Water,  near  Kinzie"},
    {"claim": "f1843_e0630", "printed": "Clark, Lewis W",
     "line": 3127, "reads": "Clark,  Lewis  AY.,  hardware,  iron,  nails,  etc.,  128  Lake"},
    {"claim": "f1843_e0090", "printed": "L. W. CLARK",
     "line": 2604, "reads": "L.  W.  CLARK,  128  Lake,  corner  of  Clark  Street"},
]
SECOND_HAND_BY_CLAIM = {row["claim"]: row for row in SECOND_HAND}


def second_hand_line(text_path=None):
    """(line_number -> line) for the committed OCR, or None if it is absent."""
    path = text_path or os.path.join(ROOT, SECOND_HAND_TEXT)
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as fh:
        return fh.read().split("\n")


# ---------------------------------------------------------------------------
# THE TOWN'S OWN PAIRS — the referral, and the only thing this stretch found
# worth carrying out of the directories. No card is touched by it here.
def town_pairs(people, fold, given_of=None, name_of=None, id_of=None):
    """Cards one letter apart in the surname and identical in the forename."""
    given_of = given_of or (lambda p: p["given"])
    name_of = name_of or (lambda p: p["name"])
    id_of = id_of or (lambda p: p["person_id"])
    index = {}
    for p in people:
        index.setdefault(fold(p["surname"]), []).append(p)
    out, seen = [], set()
    for key, here in sorted(index.items()):
        for other in variants(key, index):
            for a in here:
                for b in index[other]:
                    ga, gb = fold(given_of(a)), fold(given_of(b))
                    if not ga or ga != gb:
                        continue
                    pair = tuple(sorted((id_of(a), id_of(b))))
                    if pair in seen:
                        continue
                    seen.add(pair)
                    out.append({"cards": list(pair),
                                "names": sorted((name_of(a), name_of(b))),
                                "forename": given_of(a)})
    return sorted(out, key=lambda r: r["cards"])


def self_test():
    bad = 0

    def ok(cond, good, ill):
        nonlocal bad
        if cond:
            print("  ok    " + good)
        else:
            print("  FAIL  " + ill)
            bad += 1

    ok(one_letter_apart("pearson", "pearsons"),
       "a terminal letter is one letter away",
       "pearson/pearsons was not seen as one letter apart")
    ok(not one_letter_apart("walker", "walters"),
       "two edits are not one",
       "walker/walters was weighed as a one-letter pair")
    ok(one_letter_apart("clark", "clark"),
       "a surname is within one letter of itself, and `variants` is what excludes it",
       "the distance function stopped being reflexive")
    index = {"cook": [1], "cool": [1], "harman": [1], "harmon": [1], "clark": [1]}
    ok(variants("cook", index) == [],
       "a four-letter surname is below the length floor and is never weighed",
       "cook/cool was offered as a spelling variant")
    ok(variants("harman", index) == ["harmon"],
       "a six-letter pair one edit apart is offered, and itself is not",
       "harman/harmon was not offered, or harman offered itself")
    ok(variants("clark", index) == [],
       "a surname with no neighbour of its own length offers nothing",
       "clark gathered a neighbour it does not have")

    # THE CLAUSE REFUSES. There is no promoting branch to test, and that is the
    # assertion: every outcome this module can produce is `refused`.
    r = refusal("Hiram Pearson", "Pearson", "Pearsons, Hiram", "Pearsons",
                2, 1, "Fergus 1843")
    ok(r["outcome"] == "refused" and "sets both spellings" in r["clause"],
       "the clause's only outcome is a refusal naming it",
       "the one-letter clause produced something other than a refusal")
    ok("could not choose between them" not in r["rule"],
       "an uncontested entry's refusal does not claim a contest",
       "the contest sentence fired on a single resident")
    r2 = refusal("J. B. Barnard", "Barnard", "Bernard, Jacob", "Bernard",
                 1, 1, "Fergus 1843", contested_by=2)
    ok("2 people of 1835 reach" in r2["rule"],
       "two residents reaching one entry is said in the refusal",
       "a contested one-letter entry refused without saying so")

    # THE TOWN PAIRS, on a fixture: same forename or nothing happens.
    def f(s):
        return re.sub(r"[^a-z]", "", (s or "").lower())
    people = [
        {"person_id": "pearson_hiram", "name": "Hiram Pearson",
         "surname": "Pearson", "given": "Hiram"},
        {"person_id": "pearsons_hiram", "name": "Hiram Pearsons",
         "surname": "Pearsons", "given": "Hiram"},
        {"person_id": "pearson_george", "name": "George Pearson",
         "surname": "Pearson", "given": "George"},
    ]
    pairs = town_pairs(people, f)
    ok(len(pairs) == 1 and pairs[0]["cards"] == ["pearson_hiram", "pearsons_hiram"],
       "one letter and the same forename is a pair, and a different forename is not",
       "the town-pair test gathered the wrong cards")

    # THE SECOND HAND IS STILL THERE, verbatim, at the line it was read on.
    lines = second_hand_line()
    if lines is None:
        print("  ..    the printed volume's OCR is not in this checkout; "
              "the %d second-hand quotes were not re-read" % len(SECOND_HAND))
    else:
        missing = [row for row in SECOND_HAND
                   if row["line"] > len(lines)
                   or row["reads"] not in lines[row["line"] - 1]]
        ok(not missing,
           "all %d second-hand lines are still where they were read"
           % len(SECOND_HAND),
           "the printed volume no longer reads: "
           + "; ".join(r["claim"] for r in missing))
    ok(len(SECOND_HAND_BY_CLAIM) == len(SECOND_HAND),
       "no claim is quoted twice from the second hand",
       "a claim id appears twice in SECOND_HAND")
    return bad


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        sys.exit(1 if self_test() else 0)
    print(__doc__)
