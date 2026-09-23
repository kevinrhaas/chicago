#!/usr/bin/env python3
"""Does a printed forename agree with a resident's forename? (T-0670)

The directory crosswalks match a later entry to a person of 1835 on the folded
SURNAME plus the FIRST INITIAL of the given name. That rule was written when the
residents layer held 848 names, and it was safe then because a surname plus an
initial was very nearly unique in a town that size. T-0514 minted 532 more
people, and the rule then declared merges onto people it had never had an anchor
for — `Abbott, Thomas L.` onto Titus H. Abbott, `Hogan, Michael` onto Mary
Hogan, `Bristol, Calvin D.` onto Charles L. Bristol. Every one of them agrees on
the initial and disagrees on the name behind it.

The tightening, written out so it reads back without the code:

  Where BOTH readings print a FULL forename and the two full forenames disagree,
  the match is REFUSED. An initial standing against a full name is untouched and
  stays a match — that is the case the initial rule exists to serve, and it is
  most of what it catches.

  Two full forenames AGREE when any of these holds, and each is a thing a
  compositor or a scanner actually did to these two volumes:
    same          — they fold to the same string.
    prefix        — one is a prefix of the other ("Alex."/Alexander).
    contraction   — the pair is in CONTRACTIONS below, which is the printers'
                    own list of contractions as they stand in these volumes.
                    It is written out rather than inferred: a rule that guesses
                    which letters an abbreviation may drop merges Ruel Rose onto
                    Russell Rose, and Ruel is a name, not a contraction.
    spelling      — both are at least five letters and they differ by one
                    (Absalom/Absolom, Shubal/Shubael). Five is the floor because
                    at four letters one letter separates Mary from Mark.

  A refusal is FILED, never dropped: the crosswalk reports the resident, the
  entry as printed and both forenames, so the reading can be argued with. Where
  the printed forename is GARBLED — the scanner's `C!;as.` for Chas., `Iia` for
  Ira — the refusal says so, because that is a transcription defect and not a
  disagreement between two people (T-0695).

This module is the rule; the crosswalks import it rather than restate it.
Run it directly for its self-test: `python3 tools/name_agreement.py --self-test`.
"""
import re
import sys

# THE TITLES, and they are a VOCABULARY rather than a list of abbreviations
# (T-0987 stretch 8). A title is not a name, and a rule that reads one as a
# forename decides on a word that names nobody. The abbreviations below were
# written when the four crosswalks each carried their own copy; the FULL
# SPELLINGS are what those copies all missed, and the volumes print them:
#
#   Fergus 1843  DOCTOR BLANEY · DOCTOR EGAN · DOCTOR D. S. SMITH  and four more
#   Fergus 1839  Campbell, Major James B · McClure, Judge Samuel ·
#                Tew, Prof. Geo. C · Handy, Major · Noble, Major · Mulford, Major E. H
#   Norris 1844  none, in the roll or the advertising cards
#
# Thirteen printings in all, and the residents layer prints the same ranks on
# the other side of every comparison — Judge Sidney Breese, Major John Greene,
# Lieut. James Allen, Judge Silver, Major Handy, Lieut J L Thompson. Under the
# old list `Major Handy` met `Handy, Major` on the shared initial `m`, which is
# the M of Major on BOTH sides: a match made on a rank and not on a man.
#
# Each rank is written with its abbreviation AND its full spelling, so the pair
# cannot drift apart again, and `judge` is here because these volumes print the
# office with no abbreviation at all. Nothing is here that the corpus does not
# print: no token below stands as a forename anywhere in the residents layer or
# in the four transcribed volumes (measured, T-0987 stretch 8).
TITLES = (
    "mrs", "mistress", "miss", "mr", "mister",
    "dr", "doctor",
    "capt", "captain",
    "col", "colonel",
    "rev", "reverend",
    "gen", "general",
    "maj", "major",
    "lieut", "lieutenant",
    "hon", "honorable",
    "prof", "professor",
    "judge",
)
SUFFIXES = ("jr", "sr", "jun", "sen", "esq", "esquire", "2d")

# The surname fold, plus the one confusion that shows up in the GIVEN names of
# these two volumes and not in the surnames: an `m` scanned as two strokes and
# read back as `in` — Norris's "Allen, Win." for Wm., "Taylor, Win.H." for
# Wm. H. It is the same confusion the surname fold already carries the other way
# round as `rn` -> `m`, and it is applied to both sides of every comparison.
FOLD = [(r"[^a-z]", ""), (r"^mc", "mac"), (r"ii", "n"), (r"rn", "m"),
        (r"in", "m"), (r"vv", "w"), (r"1", "l"), (r"0", "o")]

# The contractions as these two volumes print them. Read off the entries, not
# invented: each one stands in Fergus 1843 or Norris 1844 against a man the
# other volume or the residents layer names in full. Keys and values are folded.
CONTRACTIONS = {
    "wm": "william", "wilm": "william",
    "jas": "james", "jno": "john", "jn": "john",
    "thos": "thomas", "chas": "charles", "cas": "charles",
    "geo": "george", "robt": "robert", "danl": "daniel", "saml": "samuel",
    "benj": "benjamin", "richd": "richard", "edwd": "edward",
    "nathl": "nathaniel", "michl": "michael", "patk": "patrick",
    "fredk": "frederick", "alexr": "alexander", "matw": "matthew",
    "andw": "andrew", "hy": "henry", "jos": "joseph",
}

# Anything outside these is junk the printer did not set: the scanner's `>`, `!`,
# `;`, a stray digit. A forename carrying one is a GARBLED reading, and a refusal
# against a garbled reading is a transcription defect, not two different people.
CLEAN = re.compile(r"^[A-Za-z'’.\-]+$")


def fold(name):
    """Fold a name the way the crosswalks fold a surname."""
    s = (name or "").lower()
    for pat, rep in FOLD:
        s = re.sub(pat, rep, s)
    return s


def no_forename_refusal(name, surname, volume, candidates):
    """The refusal for a pool row that prints NO forename at all (T-0987 stretch 8).

    `Major Handy`, `Judge Silver`, `Jun Marknoble`, `Sen Marknoble`: a rank or a
    suffix, and a surname. The surname-plus-initial rule has no initial to work
    with, so it refuses — and the refusal says why, rather than reporting a
    missing initial `-` as though a name had been read and had failed. Written
    here, once, because three crosswalks file it."""
    return ("%r carries no forename — a rank or a suffix stands where the given name "
            "would be — so there is no initial to carry the surname %r to. %s prints "
            "%d entr%s under that surname and the rule cannot choose between them."
            % (name, surname, volume, candidates, "y" if candidates == 1 else "ies"))


def tokens(given):
    """The given name's words. Split on whitespace, commas and full stops, so
    the scanner's run-together `Win.H` reads as two words and the hyphenated
    `A-rthur` reads as one."""
    out = []
    for raw in re.split(r"[\s,.]+", given or ""):
        if not raw:
            continue
        bare = re.sub(r"[^A-Za-z]", "", raw).lower()
        if not bare or bare in TITLES or bare in SUFFIXES:
            continue
        out.append(raw)
    return out


def first_word(given):
    """The first word of the given name that is not a title — as printed."""
    t = tokens(given)
    return t[0] if t else ""


def initial(given):
    """The first initial, unchanged from the rule the crosswalks already use."""
    w = first_word(given)
    for ch in w:
        if ch.isalpha():
            return ch.lower()
    return ""


def initials(given):
    """EVERY initial the reading sets, titles and suffixes dropped.

    Lifted out of `printed_twice._initials` (T-0987 stretch 9) so that the
    module which asks "are these two printings one man?" and the module which
    asks "is this printing that person of 1835?" count a name's initials the
    same way. `printed_twice` imports this one."""
    out = []
    for tok in tokens(given):
        for ch in tok:
            if ch.isalpha():
                out.append(ch.lower())
                break
    return out


# THE STROKE ARTEFACTS, and why a further initial can be UNREADABLE (T-0987
# stretch 9). The rule below refuses two readings that print different middle
# initials, and it may only do that where both letters were actually read. In
# these scans they very often were not: Fergus 1839's H is set as two strokes
# and comes back as `II`, `I I`, `IT`, `IL`, `Ik`; its D comes back as `I)`.
# `Chapman, Charles II.`, `Beaubien, Charles IT`, `Caton, John I).`,
# `Taylor, Anson IT` — every one of them is a man the 1835 layer holds under the
# very initial the artefact hides, and a rule that read the artefact as a letter
# refused all four. Measured over the four transcribed volumes: 16 further-name
# tokens carry a character no compositor set, and 22 more are two capitals with
# no name behind them.
#
# So this is T-0695's principle applied one field along — a disagreement against
# a GARBLED reading is a transcription defect and not two people — and the
# direction it errs in is the safe one: an unreadable initial refuses nothing
# and the tie stands. A further initial is READ when it is a single letter with
# nothing but a printer's point after it, or a middle name of three letters or
# more spelled out. `I` is excluded even so: it is the shape every one of those
# artefacts collapses to, and a middle initial I does not occur in the 1835
# layer or in these volumes except as one of them.
_READ_INITIAL = re.compile(r"[A-Za-z][.,’']?$")
_READ_NAME = re.compile(r"[A-Za-z][A-Za-z.’'-]{2,}$")
_STROKE = ("i", "l", "1")


def _readable_further(tok):
    """Was this further-name token actually read, or is it a stroke artefact?"""
    if _READ_INITIAL.match(tok):
        return tok[0].lower() not in _STROKE
    return bool(_READ_NAME.match(tok)) and re.sub(r"[^A-Za-z]", "", tok).isalpha() \
        and len(re.sub(r"[^A-Za-z]", "", tok)) >= 3


def further_initials_disagree(given_a, given_b):
    """(disagree?, why) for the initials AFTER the first — T-0987 stretch 9.

    `agrees` above judges the FIRST forename and nothing else, and the
    crosswalks get the first INITIAL from the bucket they look a resident up
    in. So nothing in the chain had ever compared a middle initial, and
    `H. B. Clarke` of 1835 could stand against `Clarke, H. W.` — an attorney
    whose middle initial the volume prints, and prints differently.

    Only initials BOTH readings set are compared, position by position, which
    is the same clause `printed_twice.consistent` applies to two printings.
    A reading that stops early is not contradicted by one that goes on:
    `William Smith` against `Smith, W. W.` sets no second initial and is not
    refused here — it is a silence, not a disagreement — whereas
    `William V Smith` against `Smith, W. W.` sets V where the volume prints W,
    and two men are standing there.

    The comparison is of INITIALS and not of names, so it fires on a middle
    name spelled out as readily as on a letter: `Gurdon Saltonstall Hubbard`
    against `Hubbard, G. S.` agrees, and against `Hubbard, G. W.` does not.
    """
    ta, tb = tokens(given_a)[1:], tokens(given_b)[1:]
    for i, (x, y) in enumerate(zip(ta, tb)):
        if not (_readable_further(x) and _readable_further(y)):
            return False, ""          # unread, so nothing after it can be judged
        if x[0].lower() != y[0].lower():
            return True, ("initial %d disagrees: %s against %s"
                          % (i + 2, x[0].upper(), y[0].upper()))
    return False, ""


def middle_initial_refusal(resident_given, printed_given):
    """The record filed when a further initial disagrees, or None."""
    bad, why = further_initials_disagree(resident_given, printed_given)
    if not bad:
        return None
    return {
        "initials_1835": [c.upper() for c in initials(resident_given)],
        "initials_printed": [c.upper() for c in initials(printed_given)],
        "clause": "further initial",
        "rule": ("The first initial and the first forename agree, and a further "
                 "initial does not: %s. The surname-plus-initial rule reads the "
                 "FIRST letter only, so a middle initial both readings print has "
                 "never been compared, and two men who share a surname and a first "
                 "initial were being merged on the strength of the letter they "
                 "share. Only initials both readings set are compared: a reading "
                 "that stops early is a silence and is not refused here."
                 % why),
    }


def narrow_by_further_initials(resident_given, candidates, given_of):
    """Drop the candidates a further initial refuses — (kept, refused, blocked).

    T-0987 stretch 9. `candidates` is the tie as the crosswalk built it and
    `given_of` reads the printed given name off one of them. Returns the
    candidates that survive, the (candidate, note) pairs this clause refuses,
    and — where the clause declined to fire — the reason, so that a decision
    not to act is filed as a reading like any other.

    **SILENCE IS NOT AGREEMENT.** The one case the clause holds back from is
    the one where firing would manufacture a match out of a candidate that
    says nothing. `J. B. Cook`, baker of 1835, meets `Cook, Josiah P. baker`
    and `Cook, John, tailor`: the P refuses Josiah, and what is left is John,
    who prints no second initial at all. Refusing the rival for SPEAKING and
    then promoting the survivor for its SILENCE is how a reconstruction picks
    the wrong man and calls it a reading — and here it would pick the tailor
    over the baker. So where the refusal would leave exactly one candidate and
    that candidate sets fewer initials than the 1835 reading does, nothing is
    refused: the tie stands, and the narrowing that was declined is recorded.
    A survivor that prints the initial and prints it the same — `Williams,
    Eli B.` against `E. S.` — is not silent, and the tie resolves.
    """
    refused = [(c, middle_initial_refusal(resident_given, given_of(c)))
               for c in candidates]
    refused = [(c, n) for c, n in refused if n]
    if not refused:
        return list(candidates), [], None
    kept = [c for c in candidates if not any(c is d for d, _ in refused)]
    if len(kept) == 1:
        mine = len(initials(resident_given))
        if len(initials(given_of(kept[0]))) < mine:
            return list(candidates), [], (
                "A further initial refuses %d of the %d printings under this name, "
                "and the one left standing prints fewer initials than the 1835 "
                "reading does — it is silent where the refused rival spoke. "
                "Promoting a silence to a match on the strength of a rival's "
                "refusal would decide this tie on the weaker of the two readings, "
                "so nothing is refused and the tie stands."
                % (len(refused), len(candidates)))
    return kept, refused, None


def is_full_forename(given):
    """A full forename, as against an initial: more than one letter."""
    return len(fold(first_word(given))) > 1


def garbled(given):
    """The printed forename carries a character no compositor set."""
    w = first_word(given)
    return bool(w) and not CLEAN.match(w)


def _one_letter_apart(a, b):
    if abs(len(a) - len(b)) > 1:
        return False
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1] <= 1


def agrees(given_a, given_b):
    """(agree?, why) for the first forename of each reading.

    True with `initial` where either side prints only an initial — that case is
    the rule the crosswalks already make and this module does not touch it.
    """
    if not is_full_forename(given_a) or not is_full_forename(given_b):
        return True, "initial"
    a, b = fold(first_word(given_a)), fold(first_word(given_b))
    if a == b:
        return True, "same"
    if a.startswith(b) or b.startswith(a):
        return True, "contraction (prefix)"
    if CONTRACTIONS.get(a) == b or CONTRACTIONS.get(b) == a:
        return True, "contraction (printed)"
    if min(len(a), len(b)) >= 5 and _one_letter_apart(a, b):
        return True, "spelling variant"
    return False, "two full forenames that differ"


def refusal(resident_given, printed_given):
    """The record filed when the two full forenames disagree, or None."""
    ok, _ = agrees(resident_given, printed_given)
    if ok:
        return None
    bad = garbled(printed_given) or garbled(resident_given)
    return {
        "forename_1835": first_word(resident_given),
        "forename_printed": first_word(printed_given),
        "garbled_reading": bad,
        "rule": ("Both readings print a full forename and the two disagree: %r "
                 "against %r. An initial standing against a full name is a match; "
                 "two full names that differ are not.%s"
                 % (first_word(resident_given), first_word(printed_given),
                    " The printed forename is garbled, so this is a transcription "
                    "defect rather than two people (T-0695)." if bad else "")),
    }


CASES = [
    # (1835 reading, printed reading, agree?, what it is)
    ("Titus H", "Thomas L.", False, "the finding: T-0670's own example"),
    ("Mary", "Michael", False, "Hogan"),
    ("Pitman", "Peter H.", False, "Fisher"),
    ("Charles L", "Calvin D.", False, "Bristol"),
    ("Hanna E", "Henry", False, "Brown"),
    ("James", "John", False, "Burke"),
    ("Ruel", "Russell", False, "Rose — Ruel is a name, not a contraction of Russell"),
    ("Mary", "Mark T.", False, "Green — one letter apart, and four letters is too few"),
    ("F.", "Francis", True, "an initial against a full name stays a match"),
    ("William", "W.", True, "and the other way round"),
    ("Absolom", "Absalom", True, "a spelling"),
    ("Shubal Davis", "Shubael D.", True, "a spelling"),
    ("Alexander", "Alex.", True, "a contraction the prefix rule reads"),
    ("William", "Wm.", True, "a contraction the volumes print"),
    ("William", "Win.", True, "and the same one as the scanner read it"),
    ("William H", "Win.H", True, "run together, as Norris prints it"),
    ("Charles", "C!;as.", True, "garbled, but the contraction is still legible"),
    ("Mrs. Margaret", "Mary", False, "a title is not a forename"),
]


def na_initials_stable():
    """`printed_twice` used to carry its own copy of this counter; it imports
    this one now, and these are the cases that copy's self-test held."""
    return (initials("Doctor D. S.") == ["d", "s"]
            and initials("G. S.") == ["g", "s"]
            and initials("Silas B., jr.") == ["s", "b"])


def self_test():
    fired = []
    for a, b, want, why in CASES:
        got, reason = agrees(a, b)
        if got != want:
            fired.append("%r vs %r: expected %s (%s), got %s (%s)"
                         % (a, b, want, why, got, reason))
    assert garbled("C!;as."), "a scanner artefact must read as garbled"
    assert not garbled("A-rthur"), "a hyphen is not an artefact"
    assert refusal("Titus H", "Thomas L.")["forename_printed"] == "Thomas"
    assert refusal("F.", "Francis") is None
    # T-0987 stretch 9 — the further initials, and the silence that is not agreement.
    fi = [
        ("H. B.", "H. W", True, "Clarke: the middle initial the volume prints"),
        ("Eli B", "E. S", True, "Williams: a middle initial against a middle initial"),
        ("Anson H.", "A. D", True, "Taylor: A. D. is Augustine Deodat, not Anson H."),
        ("John A", "J. Coe", True, "Clark: a middle name spelled out still sets its initial"),
        ("Gurdon Saltonstall", "G. S", False, "Hubbard: spelled out and agreeing"),
        ("William", "W. W", False, "a reading that stops early is silent, not refused"),
        ("William V", "William", False, "and the silence the other way round"),
        ("Dr. John Herbert", "John N", True, "a title is dropped before the initials are counted"),
        ("Anson H.", "Anson IT", False, "Fergus's H set as two strokes: unread, not disagreed"),
        ("Charles H", "Charles II.", False, "and the other shape of the same artefact"),
        ("John Dean", "John I).", False, "a D read as I-bracket is not a D that disagrees"),
        ("W B", "Wm. I I.", False, "an I in the further position is a stroke, never a letter"),
        ("Augustine Deodat", "A. D", False, "a middle name spelled out sets its own initial"),
        ("Edward A.", "Edward K.", True, "and a letter that WAS read still refuses"),
    ]
    for a, b, want, why in fi:
        got, _ = further_initials_disagree(a, b)
        if got != want:
            fired.append("further initials %r vs %r: expected %s (%s)" % (a, b, want, why))
    # the narrowing, and the one case it declines to make
    cands = [{"g": "Josiah P"}, {"g": "John"}]
    kept, ref, blocked = narrow_by_further_initials("J. B.", cands, lambda c: c["g"])
    assert len(kept) == 2 and not ref and blocked, "Cook: a silent survivor is not promoted"
    cands = [{"g": "E. S"}, {"g": "Eli B"}]
    kept, ref, blocked = narrow_by_further_initials("Eli B", cands, lambda c: c["g"])
    assert len(kept) == 1 and kept[0]["g"] == "Eli B" and len(ref) == 1 and not blocked, \
        "Williams: the tie resolves onto the printing that agrees"
    kept, ref, blocked = narrow_by_further_initials("W B", [{"g": "William H"}], lambda c: c["g"])
    assert not kept and len(ref) == 1, "Clarke: a lone match is withdrawn, not held"
    assert na_initials_stable(), "printed_twice must count initials the same way"
    if fired:
        for line in fired:
            print("  " + line, file=sys.stderr)
        print("name_agreement --self-test: %d case(s) failed" % len(fired), file=sys.stderr)
        return 1
    print("name_agreement --self-test: %d cases hold" % len(CASES))
    return 0


if __name__ == "__main__":
    sys.exit(self_test() if "--self-test" in sys.argv else self_test())
