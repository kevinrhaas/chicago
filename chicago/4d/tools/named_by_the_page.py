#!/usr/bin/env python3
"""THE WHOLE PRINTED NAME, WORD FOR WORD — the tie the page itself decides.

T-0987 stretch 14. The four directory crosswalks make a candidate on
SURNAME PLUS FIRST INITIAL and nothing else. Everything the compositor set
after that first letter — `Byram` where the town holds a `Byra`, `John S. C.`
where it holds a bare `John`, `Elston, Daniel T.` beside `Elston, Daniel` — is
read, transcribed, committed, and then never weighed. So a page that names one
person plainly arrives as a TIE, in one of the two shapes this ticket counts:

  * AMBIGUOUS — one person of 1835, two printed entries under the initial.
  * CONTESTED — one printed entry, two people of 1835 under the initial.

They are the same arithmetic with the arguments swapped, and T-0987 stretch 9
built it for the FIRST of the two only: `name_agreement.narrow_by_further_
initials` drops the entries a middle initial refuses. Two things it cannot do,
and both of them are why 43 contests and 69 ambiguities were still standing:

  1. It compares only initials BOTH readings set, so a reading that STOPS
     EARLY is a silence and refuses nothing. `H. B. Clarke` of 1835 against
     `Clarke, Dr. Henry` and `Clarke, Henry B.` sets a B that neither is
     contradicted by — the first prints no second word at all — so the tie
     stood, and the house on Michigan avenue went unnamed.
  2. It has never been run on the CONTEST axis at all. Nothing in the chain
     has ever asked which of two people of 1835 a printed line names.

THE RULING. A printed forename and a reading of 1835 are THE SAME NAME when
they set the SAME NUMBER of words and agree word by word — each pair either
letter for letter, or one of them the single initial the other begins with.
Where exactly ONE candidate is the same name in that sense, the page names
that one and no other. Where none is, or more than one is, nothing happens
and the tie stands with the reason filed.

WHAT THE WORD-COUNT TEST IS FOR, and it is the whole discipline: it makes the
rule fire on what a reading SAYS and never on what it omits. `Hogan, John S.
C.` sets three words; the town's `John S. C. Hogan` sets three and agrees on
all three, and its bare `John Hogan` sets one. The one that fits is the one
that SPOKE and was right, never the one that was silent — which is the safe
direction of stretch 9's own warning, that promoting a silence over a rival's
refusal is how a reconstruction picks the wrong man and calls it a reading.
`Cook, John, tailor` against `J. B. Cook`, baker, still decides nothing here:
one word against two, no fit, tie stands.

IT IS NOT A DISCRIMINATOR. T-0696 rules that a trade may narrow a tie and a
premises may not, and that a narrowed tie is filed `discriminated` and never
promoted to a match. Nothing here weighs a trade, a premises or a year: this
is the MATCHING RULE, which was always about the name, applied to the whole of
the name instead of its first letter. A candidate this clause drops is dropped
the way `narrow_by_further_initials` drops one, and a single survivor is a
match by the crosswalk's own rule.

STRICTER THAN `agrees()`, ON PURPOSE. `name_agreement.agrees` admits a
contraction and a one-letter spelling variant, because it is asked whether two
readings CAN be one man. This is asked something else — which of two rivals the
compositor set — and there `Byra` against a printed `Byram` is the answer, not
a tolerance. The contraction rule still governs whether the pair may match at
all; this clause only chooses between rivals that have already passed it.

AND THE UNREADABLE STOPS IT. Stretch 9's stroke artefacts are the reason: a
further word that was never actually read (`Collins, Jas. PL`, `Taylor, Anson
IT`) cannot be compared to anything, and a rule that read one as a letter would
decide a tie on a scanner's noise. `name_agreement._readable_further` is the
test, imported rather than restated, and an unreadable word makes the whole
comparison DECLINE rather than fail — a declined narrowing leaves the tie
standing, which is the direction that invents nobody.

A WIFE IS NOT HER HUSBAND — the second clause, and it is R6 arriving where it
was always true. `tools/consolidate_resident_evidence.py` holds `Mrs Rufus
Brown` apart from `Rufus Brown` (R6, T-0723) because the honorific strip leaves
the husband's forename tokens on both readings and folds a wife onto him. The
crosswalks strip titles the same way and had no such rule, so the town layer's
two people met `Brown, Rufus B., warehouseman` together and were filed as a
CONTEST — a man contesting a printed line with his own wife. Where one
candidate of 1835 carries a female honorific, its forename tokens are exactly
those of another candidate carried WITHOUT one, and the printed entry sets no
female honorific of its own, the entry is the husband's and she is not named by
it. The proof is the same proof R6 asks for and it is in the contest itself:
the town layer prints both readings, which is what put them here together.

The honorific must stand on HIS name and nothing else. `Mrs. Sabrina Mason`
and `Mrs. Eliza Haight` are women under their own forenames, no bare reading of
that surname sets those tokens, and this clause never reaches them — nor
`Taylor, Mrs. C.`, whose pair no page holds (T-0960) and whose initial is not
`Charles H.` letter for letter.
"""

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import name_agreement as na   # tokens, the title vocabulary, the readable test
import namesake               # female_title — R6's own word, imported not restated

UNREADABLE = "unreadable"
CLAUSE = "the whole printed name, word for word"
WIFE_CLAUSE = "a female honorific standing on a man's own name (R6, T-0723)"


def generational(name):
    """`JR` or `SR` — the suffix that says WHICH man of the name, or None.

    `namesake.suffix_of` is the reader and its vocabulary is wider than this:
    `ESQ` is a station and `2D` a numbering, and neither of them separates a
    father from a son. Only the generational pair does, and only it is weighed.
    """
    suffix = namesake.suffix_of(name)
    return suffix if suffix in ("JR", "SR") else None


def _fold(word):
    return re.sub(r"[^a-z]", "", (word or "").lower())


def _word_pair(a, b):
    """(tier, why) for one pair of words — tier None where there is no fit at all.

    THE TIERS ARE THE WHOLE OF THE RULE, and they are ranked by how much of the
    name each kind of agreement actually weighs:

      0  letter for letter. `Byram` against a printed `Byram`.
      1  two whole words the matching rule already admits as one name — a
         printed contraction or a one-letter spelling variant, which is
         `name_agreement.agrees`' own tolerance and not a new one. `Russel`
         against `Russell`, `Byra` against `Byram`.
      2  a single initial standing for a whole word. `R.` against `Russell`.

    AN INITIAL IS THE WEAKEST OF THE THREE and it has to be, because an initial
    fits every man of the letter. Run without the ranking this clause named
    `Heacock, jr., R. E., civil engineer, on the canal` for Russel E. Heacock —
    the attorney and justice of the peace the 1835 layer holds — over
    `Heacock, Russell E., att'y, justice of peace, Adams cor. Clark`, on nothing
    but a doubled L. The son fitted on two initials and the father on a spelling;
    a name spelled out and spelled almost the same is the stronger reading, and
    the ranking says so.
    """
    fa, fb = _fold(a), _fold(b)
    if not fa or not fb:
        return None, "a word with no letters in it"
    if fa == fb:
        return 0, ""
    if len(fa) > 1 and len(fb) > 1:
        if fa.startswith(fb) or fb.startswith(fa):
            return 1, ""
        if min(len(fa), len(fb)) >= 5 and na._one_letter_apart(fa, fb):
            return 1, ""
        return None, "%s against %s" % (a, b)
    if len(fa) == 1 and fb.startswith(fa):
        return 2, ""
    if len(fb) == 1 and fa.startswith(fb):
        return 2, ""
    return None, "%s against %s" % (a, b)


def same_name(printed_given, reading_given):
    """(fit, why). `fit` is the tiers worst-first, None for no fit, and the
    string UNREADABLE where a word could not be read and nothing is decided.

    The first word is weighed like every other, and the words after it must also
    have been READ — `name_agreement._readable_further` is the test, and an
    artefact returns UNREADABLE rather than a refusal.
    """
    p, r = na.tokens(printed_given), na.tokens(reading_given)
    if not p or not r:
        return None, "a reading with no forename in it"
    if len(p) != len(r):
        return None, ("the page sets %d word%s and the reading sets %d"
                      % (len(p), "" if len(p) == 1 else "s", len(r)))
    tiers = []
    for i, (x, y) in enumerate(zip(p, r)):
        if i and not (na._readable_further(x) and na._readable_further(y)):
            return UNREADABLE, ("word %d was not read on one side or the other "
                                "(%s against %s)" % (i + 1, x, y))
        tier, why = _word_pair(x, y)
        if tier is None:
            return None, "word %d differs: %s" % (i + 1, why)
        tiers.append(tier)
    return tuple(sorted(tiers, reverse=True)), "%d word%s, %s" % (
        len(p), "" if len(p) == 1 else "s",
        "letter for letter" if max(tiers) == 0 else
        ("an initial standing for a word" if max(tiers) == 2 else "a spelling"))


def decide(printed_given, candidates, given_of, reading_name=None, name_of=None,
           one_body=True):
    """Which candidate the page names — (winner, note) with winner possibly None.

    `candidates` is the tie as the crosswalk built it, in either direction: the
    printed entries under one person of 1835, or the people of 1835 under one
    printed entry. `given_of` reads the given name off a candidate. The BEST fit
    wins and only where it is strictly better than every other — two readings
    equally close is a refusal and not a choice, which is R3's discipline and
    T-0951's. The note is filed whatever happens, because a decision NOT to act
    is a reading like any other and this programme leaves nothing silent.

    `reading_name` is the reading on the FIXED side of the tie, as held, with
    its honorific if it has one. Where it carries a female honorific and no
    candidate agrees with it, the comparison DECLINES rather than weighing a
    name the honorific says may not be hers — `Taylor, Mrs. C.` against a page
    that prints `Taylor, Charles, tailor, Clark street` and nothing else, whose
    pair T-0960 has already ruled no page holds. Where a candidate DOES agree,
    `honorific_must_agree` has already taken the rest out before this is called.

    `one_body` SAYS WHETHER THE CANDIDATES CAME OUT OF ONE BODY OF EVIDENCE,
    and it is the difference between the two axes. Where they are the entries of
    ONE VOLUME, a word one of them sets and another does not is the volume's own
    distinction — R6 states the principle and this clause borrows it: a directory
    does not enter one person twice under two spellings, so Fergus 1839 printing
    `Elston, Daniel, brickmaker, Elston road` AND `Elston, Daniel T., student`
    has separated two men, and the town's bare Daniel Elston is the bare entry.
    Where the candidates are READINGS OF 1835 the guarantee is gone, and this
    programme is the reason: the town layer demonstrably holds one man on two
    cards — `Byra` and `Byram` King, `Ordemus` and `Orsemus` Morrison — so a
    word one reading carries and another does not may be the same man written
    twice. There, a page that sets FEWER words than some reading decides
    nothing: Norris's advertising card for `E. Smith` fits the town's Elded
    Smith exactly and its E. Kirby Smith not at all, and the only thing standing
    between them is a word the compositor did not set.

    A GENERATIONAL SUFFIX STOPS IT DEAD. `name_of` reads a candidate's name as
    the page or the town sets it, suffix and all, because `name_agreement.tokens`
    strips `jr.` before anything is compared — so Fergus 1843's `Heacock, Russel
    E., jr., clerk, Charles Walker & Co.` arrived here letter for letter
    identical to the town's Russel E. Heacock, who is his father and Chicago's
    first lawyer, and beat `Heacock, Russel Easton` on a doubled L. Where the
    page separates a father from a son and the reading of 1835 says nothing
    about which it is, the comparison DECLINES: choosing the unsuffixed one on
    the town's SILENCE is the move T-0987 stretch 9 refuses by name. Where the
    reading does carry a suffix, only the candidates that carry the same one
    are weighed — and where none does, nothing is refused.
    """
    if reading_name and namesake.female_title(reading_name) and not any(
            namesake.female_title(given_of(c)) for c in candidates):
        return None, {"clause": WIFE_CLAUSE, "named": None,
                      "why": ("%r carries a female honorific and no reading offered "
                              "against it does. The honorific says the name under it "
                              "may not be her own, so it is not hers to weigh: the "
                              "comparison is declined and the tie stands." % reading_name)}
    if name_of is not None:
        mine = generational(reading_name or "")
        theirs = {id(c): generational(name_of(c)) for c in candidates}
        if mine is None and any(theirs.values()):
            named = sorted({v for v in theirs.values() if v})
            return None, {"clause": CLAUSE, "named": None,
                          "why": ("the page sets a generational suffix (%s) on %d of "
                                  "the %d readings and %r carries none. Which man of "
                                  "the name is a thing the page distinguishes and this "
                                  "reading does not, so the comparison is declined and "
                                  "the tie stands."
                                  % ("/".join(named),
                                     sum(1 for v in theirs.values() if v),
                                     len(candidates), reading_name or printed_given))}
        if mine is not None and any(v == mine for v in theirs.values()):
            candidates = [c for c in candidates if theirs[id(c)] == mine]
    if not one_body:
        longer = [c for c in candidates
                  if len(na.tokens(given_of(c))) > len(na.tokens(printed_given))]
        if longer:
            return None, {"clause": CLAUSE, "named": None,
                          "why": ("the page sets %d word%s and %d of the %d readings set "
                                  "more. These readings do not come out of one body, so a "
                                  "word the page did not set cannot separate them: the "
                                  "comparison is declined and the tie stands."
                                  % (len(na.tokens(printed_given)),
                                     "" if len(na.tokens(printed_given)) == 1 else "s",
                                     len(longer), len(candidates)))}
    fits, declined = [], []
    for c in candidates:
        rank, why = same_name(printed_given, given_of(c))
        if rank is UNREADABLE:
            declined.append(why)
        elif rank is not None:
            fits.append((rank, c))
    if declined:
        return None, {"clause": CLAUSE, "named": None,
                      "why": ("the comparison was declined: %s. An unreadable word "
                              "decides nothing, and the tie stands." % declined[0])}
    best = sorted(r for r, _ in fits)
    if len(fits) == 1 or (len(fits) > 1 and best[0] < best[1]):
        rank, winner = min(fits)
        return winner, {
            "clause": CLAUSE, "named": _fold(" ".join(na.tokens(given_of(winner)))),
            "why": ("the page sets %r and exactly one of the %d readings is that name "
                    "word for word and most closely: %s. The rest set a different "
                    "number of words, a different word, or the same name less closely."
                    % (" ".join(na.tokens(printed_given)), len(candidates),
                       same_name(printed_given, given_of(winner))[1])),
        }
    return None, {
        "clause": CLAUSE, "named": None,
        "why": ("the page sets %r and %d of the %d readings fit it equally closely, "
                "so the page names no one of them in particular."
                % (" ".join(na.tokens(printed_given)), sum(1 for r in best if r == best[0])
                   if best else 0, len(candidates))),
    }


def honorific_must_agree(fixed_name, candidates, name_of):
    """The candidates a female honorific holds off — (kept, refused).

    R6's claim, and nothing more than it: a female honorific is a fact about
    the reading, and two readings that disagree about one are two people. The
    identity layer already holds `Mrs Rufus Brown` apart from `Rufus Brown` on
    it (T-0723); the crosswalks strip titles before they compare anything and
    so had no such rule, which is why the town's wife and the town's husband
    arrived at `Brown, Rufus B., warehouseman` together and were filed as a
    CONTEST — a man contesting a printed line with his own wife.

    R6'S GUARD IS KEPT AS IT STANDS: one body has to set BOTH readings. Here
    that is exactly "at least one candidate agrees about the honorific", and it
    is what stops the rule where the evidence stops. Fergus 1843 prints `Brown,
    Rufus B.` at entry 458 and `Brown, Mrs. Rufus B.` at 459, so the volume
    itself separates them and each reading takes its own. Fergus 1839 prints no
    `Taylor, Mrs. C.` at all, so nothing here reaches her (T-0960) and her tie
    stands. Where every candidate disagrees, this refuses NOTHING: a rule that
    emptied the tie would leave a person with no ruling at all, and clause 1 of
    this programme asks that nothing be left silent.

    `fixed_name` is the reading on the other side of the tie, `name_of` reads a
    candidate's name AS HELD — honorific and all, which is the one form the
    crosswalks' own `split_name` throws away.
    """
    want = bool(namesake.female_title(fixed_name))
    kept = [c for c in candidates
            if bool(namesake.female_title(name_of(c))) is want]
    if not kept or len(kept) == len(candidates):
        return list(candidates), []
    refused = [c for c in candidates if not any(c is k for k in kept)]
    return kept, [(c, {
        "clause": WIFE_CLAUSE,
        "honorific": namesake.female_title(name_of(c)) or namesake.female_title(fixed_name),
        "why": ("%r and %r disagree about a female honorific, and another reading "
                "in this tie agrees with %r about it. A wife is not her husband — "
                "the identity layer already holds that pair apart by R6 — and the "
                "body that sets both readings is what says so."
                % (name_of(c), fixed_name, fixed_name))}) for c in refused]


CASES = [
    # (printed, reading, the tiers worst-first, or None for no fit) — every one
    # of them a name off a page in this corpus, weighed against a card of 1835.
    ("Byram", "Byram", (0,)),              # King, Jones, King & Co., Fergus 1839
    ("Byram", "Byra", (1,)),               # ...and the town's other reading of him
    ("Orsemus", "Orsemus", (0,)),          # Morrison, 153 Clark, all three volumes
    ("Orsemus", "Ordemus", (1,)),          # the poll list's spelling, one letter off
    ("John S. C.", "John S. C.", (0, 0, 0)),   # Hogan, 236 Lake street, Fergus 1839
    ("John S. C.", "John", None),          # the bare reading: one word against three
    ("John Stephen Coates", "John S. C.", (2, 2, 0)),  # Fergus 1843 spells them out
    ("John Stephen", "John S.", (2, 0)),   # Wright of the Prairie Farmer, 1843
    ("John Stephen", "John", None),
    ("William Hartt", "William H.", (2, 0)),
    ("William", "William", (0,)),
    ("William", "William V", None),        # W. W. Smith's rival sets a V
    ("E. A.", "Eli A", (2, 0)),            # Rider, clerk to C. L. P. Hogan, 1844
    ("E. A.", "Elia", None),
    ("Dr. Henry", "H. B.", None),          # the title drops; one word against two
    ("Henry B.", "H. B.", (2, 0)),         # ...and the Clarke house is named
    ("Daniel", "Daniel", (0,)),
    ("Daniel T.", "Daniel", None),         # the student, not the brickmaker
    ("Russell E.", "Russel E.", (1, 0)),   # Heacock the attorney: one L apart
    ("R. E.", "Russel E.", (2, 0)),        # ...and his son, on two initials
    ("Jas. PL", "J. H.", UNREADABLE),      # a stroke artefact decides nothing
    ("Anson IT", "Anson H", UNREADABLE),
]


def self_test():
    bad = 0
    for printed, reading, want in CASES:
        got, why = same_name(printed, reading)
        if got != want:
            print("  FAIL  %r against %r -> %r, wanted %r (%s)"
                  % (printed, reading, got, want, why))
            bad += 1
    if not bad:
        print("  ok    %d printed names weighed word for word" % len(CASES))

    # exactly one fit, or nothing happens
    people = [("king_byram", "Byram"), ("king_byra", "Byra")]
    win, note = decide("Byram", people, lambda c: c[1])
    if not win or win[0] != "king_byram":
        print("  FAIL  the page sets Byram and the rule did not name Byram King")
        bad += 1
    else:
        print("  ok    one printed line, two people of 1835, and the page names one")
    win, _ = decide("John", [("clark_john_a", "John A"), ("clark_john_k", "John K")],
                    lambda c: c[1])
    if win is not None:
        print("  FAIL  a bare 'John' chose between John A. and John K. Clark")
        bad += 1
    else:
        print("  ok    a page that sets less than its rivals do decides nothing")
    win, _ = decide("Mark", [("noble_a", "Mark"), ("noble_b", "Mark")], lambda c: c[1])
    if win is not None:
        print("  FAIL  two readings fit and the rule still picked one")
        bad += 1
    else:
        print("  ok    two fits of one closeness is a refusal and not a choice")
    # THE RANKING. A name spelled almost the same outranks a pair of initials.
    heacock = [("father", "Russell E."), ("son", "R. E.")]
    win, _ = decide("Russel E.", heacock, lambda c: c[1])
    if not win or win[0] != "father":
        print("  FAIL  the son's two initials outran the father's spelling (Heacock)")
        bad += 1
    else:
        print("  ok    a spelling outranks an initial, and the attorney keeps his entry")

    # R6, on the contest axis: one printed line, a husband and his wife
    rivals = [("brown_rufus", "Rufus Brown"), ("brown_mrs_rufus", "Mrs Rufus Brown")]
    kept, refused = honorific_must_agree("Rufus B.", rivals, lambda c: c[1])
    if len(kept) != 1 or kept[0][0] != "brown_rufus" or len(refused) != 1:
        print("  FAIL  R6 did not hold Mrs Rufus Brown off her husband's entry")
        bad += 1
    else:
        print("  ok    a female honorific on a man's own name is not that man (R6)")
    # ...and on the other axis, where the volume prints the pair itself
    entries = [("e458", "Brown, Rufus B."), ("e459", "Brown, Mrs. Rufus B.")]
    kept, refused = honorific_must_agree("Mrs Rufus Brown", entries, lambda c: c[1])
    if len(kept) != 1 or kept[0][0] != "e459":
        print("  FAIL  the wife was not given her own printed entry")
        bad += 1
    else:
        print("  ok    a volume that prints both readings gives each its own")
    # A GENERATIONAL SUFFIX THE READING DOES NOT CARRY STOPS THE COMPARISON
    heacocks = [("father", "Russel Easton", "Heacock, Russel Easton"),
                ("son", "Russel E.", "Heacock, Russel E., jr.")]
    win, note = decide("Russel E.", heacocks, lambda c: c[1],
                       reading_name="Russel E. Heacock", name_of=lambda c: c[2])
    if win is not None:
        print("  FAIL  a jr. beat his father on a suffix the reading never set")
        bad += 1
    else:
        print("  ok    a generational suffix the reading does not carry declines")
    # ...and a reading that DOES carry one is weighed against its own generation
    win, _ = decide("Russel E.", heacocks, lambda c: c[1],
                    reading_name="Russel E. Heacock, jr.", name_of=lambda c: c[2])
    if not win or win[0] != "son":
        print("  FAIL  a reading carrying jr. was not weighed against the jr. entry")
        bad += 1
    else:
        print("  ok    a reading that sets a suffix keeps to its own generation")
    # A PAGE THAT SETS FEWER WORDS THAN A READING SEPARATES NO TWO READINGS
    smiths = [("kirby", "E Kirby"), ("elded", "Elded")]
    win, _ = decide("E.", smiths, lambda c: c[1], one_body=False)
    if win is not None:
        print("  FAIL  a card printing 'E.' chose between E. Kirby and Elded Smith")
        bad += 1
    else:
        print("  ok    a page setting fewer words than a reading decides no contest")
    win, _ = decide("Daniel", [("bare", "Daniel"), ("initialled", "Daniel T.")],
                    lambda c: c[1], one_body=True)
    if not win or win[0] != "bare":
        print("  FAIL  one volume's own distinction did not name the bare entry")
        bad += 1
    else:
        print("  ok    one volume printing both makes the distinction itself")
    # WHERE NO CANDIDATE AGREES, NOTHING IS REFUSED (T-0960's Mrs. C. Taylor)
    taylors = [("e1464", "Taylor, Charles"), ("e1465", "Taylor, Charles H.")]
    kept, refused = honorific_must_agree("Mrs. C. Taylor", taylors, lambda c: c[1])
    if refused or len(kept) != 2:
        print("  FAIL  a tie was emptied where no page holds the pair")
        bad += 1
    else:
        print("  ok    no candidate agreeing means nothing is refused")
    win, _ = decide("Mrs. C. Taylor", taylors, lambda c: c[1],
                    reading_name="Mrs. C. Taylor")
    if win is not None:
        print("  FAIL  a female honorific was named onto an entry printing none")
        bad += 1
    else:
        print("  ok    a female honorific against pages printing none declines")
    return bad


if __name__ == "__main__":
    sys.exit(1 if self_test() else 0)
