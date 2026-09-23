#!/usr/bin/env python3
"""One man, two printings — Fergus 1843's notices against his own roll (T-0987).

Fergus 1843 is TWO directories bound as one. A `business directory` sets 174
subscribers' notices under trade headings — "SADDLERY AND HARNESS", "ATTORNEYS" —
and names each subscriber in capitals at the head of his own notice. An
`alphabetical directory` then sets the town's roll, 2,521 entries, one line a
person. A tradesman who paid for a notice ALSO stands in the roll, so the volume
prints him twice, and until this module ran the crosswalk's ambiguity test counted
PRINTINGS: Silas B. Cobb's notice and `Cobb, Silas Bowman` arrived as two rivals
for one 1835 saddler, and the tie could only be narrowed, never closed. Eighteen
of the printings standing in the 1843 tie pool were notices of that kind.

THE RULE, written out so it reads back without the code. A notice is the same man
as a roll entry when all four hold:

  1. SURNAME. The folded surnames agree — the fold the crosswalks already use.
  2. NAME CONSISTENT. The first forenames agree by `name_agreement` (the rule
     T-0670 wrote and this module imports rather than restates), and every
     FURTHER initial both printings set agrees, position by position. `Henry W.`
     is `Henry Wilcox` and is not `Henry B.`
  3. ENOUGH OF THE NAME, and this is the clause that keeps the rule honest. A
     notice that prints a surname and TWO OR MORE initials — `G. S. Hubbard`,
     `B. S. Morris` — has said enough to name one man. A notice that prints one
     initial has not, and it must also show a THING IN COMMON with the roll
     entry: a street number both print, or a trade word of five letters or more
     that both print, one a prefix of the other. `A. Garrett`'s two insurance
     notices name neither, and his tie therefore stands.
  4. ONLY HIM. Exactly one roll entry in the WHOLE volume satisfies 1-3. Two
     `Curtiss, James` and `Curtiss, J. W.` are both consistent with the notice
     `JAMES CURTISS`, so the notice attaches to neither.

Where a notice attaches it is no longer a rival: it is recorded on the roll
entry's row as `also_printed`, and the crosswalk counts PEOPLE. Where it does not
attach it stands exactly as it did before, as its own candidate, and the note says
WHICH clause was silent — the refusals are kept in full, as readings.

WHAT THIS IS NOT. It is not a claim about 1835: the crosswalk it feeds is a
proposal, a match there carries 1843 evidence with `describes_date 1843` and no
grade moves either way (T-0571). It is not the tie discriminator — T-0696 rules
on which of two 1835 PEOPLE a printing belongs to, and refuses a premises for it;
this module rules on whether two PRINTINGS in one volume are one man, which is a
different question and is why a printed address may be read here. It is not a
merge of two readings: both printings are kept, both quotable.

Run it directly for its self-test: `python3 tools/printed_twice.py --self-test`.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import back_project_addresses as bpa  # its street tables, clause 3's stoplist
import name_agreement as na

NOTICE = "business directory"
ROLL = "alphabetical directory"

# Words of five letters or more that both sections print and that name no trade:
# the volume's furniture, the compositor's boilerplate, and — the one that matters,
# because half the town shares it — A STREET NAME. The street words are the two
# tables in `back_project_addresses.py`, imported rather than restated, so this
# module cannot come to disagree with the pass that places an address.
FILLER = {
    "streets", "chicago", "illinois", "corner", "between", "doors", "above",
    "below", "opposite", "office", "general", "dealer", "dealers", "store",
    "stores", "house", "block", "building", "buildings", "avenue", "market",
    "markets", "hotel", "company", "companies", "agency", "agent", "agents",
    "would", "which", "their", "there", "other", "respectfully", "public",
    "patronage", "county", "years", "where", "every", "price", "prices",
    "terms", "cheap", "always", "about", "large", "small", "first", "second",
    "third", "subscriber", "friends", "generally", "attention",
} | {w for key in list(bpa.STREET_1835) + list(bpa.NOT_1835) for w in key.split()}

WORD = re.compile(r"[A-Za-z]{5,}")
NUMBERED = re.compile(r"\b(\d{1,3})\s+([A-Z][A-Za-z.-]*(?:\s+[A-Z][A-Za-z.-]*)?)")


# The initial counter now lives in `name_agreement` and is imported (T-0987
# stretch 9), because the clause below and the crosswalks' own further-initial
# refusal have to count a name's initials the same way or the two modules can
# disagree about which man a printing is.
_initials = na.initials


def consistent(notice_given, roll_given):
    """(same man's name?, why) — clause 2.

    EVERY initial both printings set is compared, the first one included.
    `name_agreement.agrees` deliberately does not compare first initials — the
    crosswalks get that from the bucket they look a resident up in — so a module
    that asks its question of two PRINTINGS has to ask for the initial itself,
    or `G. S. HUBBARD` reads as consistent with `Hubbard, Ahira`."""
    a, b = _initials(notice_given), _initials(roll_given)
    if not a or not b:
        return False, "one printing sets no forename at all"
    if a[0] != b[0]:
        return False, ("the first initials disagree: %r against %r"
                       % (a[0].upper(), b[0].upper()))
    ok, why = na.agrees(notice_given, roll_given)
    if not ok:
        return False, "the first forenames disagree: %s" % why
    for i, (x, y) in enumerate(zip(a[1:], b[1:])):
        if x != y:
            return False, ("initial %d disagrees: %r against %r"
                           % (i + 2, x.upper(), y.upper()))
    return True, "the name is consistent"


def _words(*texts):
    out = set()
    for t in texts:
        for w in WORD.findall((t or "").lower()):
            if w not in FILLER:
                out.add(w)
    return out


def _numbers(*texts):
    out = set()
    for t in texts:
        for num, street in NUMBERED.findall(t or ""):
            out.add((num, street.split()[0].rstrip(".,").lower()))
    return out


def in_common(notice, roll):
    """A thing both printings name — clause 3's second half. Returns a sentence
    or None. `notice` and `roll` are the claims' `normalized` blocks."""
    shared = _numbers(notice.get("occupation"), notice.get("address")) & _numbers(
        roll.get("occupation"), roll.get("address"))
    if shared:
        num, street = sorted(shared)[0]
        return "both printings set the address %s %s" % (num, street.title())
    a = _words(notice.get("trade_heading"), notice.get("occupation"))
    b = _words(roll.get("occupation"))
    for x in sorted(a):
        for y in sorted(b):
            if x == y or x.startswith(y) or y.startswith(x):
                return ("both printings set the printed word %r"
                        % (x if len(x) <= len(y) else y))
    return None


def attach(notice, rolls):
    """Which roll entry a notice belongs to, and why — clauses 1-4.

    `notice` is a claim; `rolls` every claim in the roll whose surname folds to
    the notice's. Returns (roll claim or None, note)."""
    kept, refused = [], []
    for r in rolls:
        ok, why = consistent(notice["normalized"]["given"], r["normalized"]["given"])
        if not ok:
            refused.append({"roll": r["id"], "clause": 2, "why": why})
            continue
        if len(_initials(notice["normalized"]["given"])) >= 2:
            kept.append((r, "the notice prints a surname and %d initials"
                         % len(_initials(notice["normalized"]["given"]))))
            continue
        common = in_common(notice["normalized"], r["normalized"])
        if common:
            kept.append((r, common))
        else:
            refused.append({"roll": r["id"], "clause": 3,
                            "why": "the notice prints one initial, and nothing "
                                   "in it is in common with this roll entry"})
    if len(kept) == 1:
        r, why = kept[0]
        return r, {"notice": notice["id"], "roll": r["id"], "attached": True,
                   "why": why, "rule": "T-0987 stretch 7, clauses 1-4"}
    return None, {"notice": notice["id"], "attached": False,
                  "consistent_roll_entries": [r["id"] for r, _ in kept],
                  "why": ("%d roll entries of that surname are consistent with the "
                          "notice and a notice attaches only where exactly one is"
                          % len(kept)) if kept else
                         "no roll entry of that surname passes clause 2 or 3",
                  "refused": refused[:8],
                  "rule": "T-0987 stretch 7, clause 4" if kept else
                          "T-0987 stretch 7, clauses 2-3"}


def fold(claims, fold_surname):
    """The volume's printings, grouped into PEOPLE.

    `claims` every entry of the volume; `fold_surname` the crosswalk's own
    surname fold, passed in so this module cannot disagree with it. Returns
    (also_printed, notes): a map roll-id -> [notice claims], and one note per
    notice in the volume, attached or not."""
    rolls = {}
    notices = []
    for c in claims:
        n = c["normalized"]
        if n.get("firm") or not n.get("surname"):
            continue
        f = fold_surname(n["surname"])
        if not f:
            continue
        if n.get("section") == NOTICE:
            notices.append((f, c))
        elif n.get("section") == ROLL:
            rolls.setdefault(f, []).append(c)
    also, notes = {}, []
    for f, c in notices:
        r, note = attach(c, rolls.get(f, []))
        notes.append(note)
        if r is not None:
            also.setdefault(r["id"], []).append(c)
    return also, notes


CASES = [
    # (notice given, roll given, consistent?, what it is)
    ("Henry W.", "Henry Wilcox", True, "the attorney's two printings"),
    ("Henry W.", "Henry B.", False, "and the farmer he is not"),
    ("G. S.", "Gurdon Saltonstall", True, "initials against the name in full"),
    ("James E.", "Jas. E", True, "a contraction the volume prints"),
    ("Silas B.", "Silas Bowman", True, "a middle initial against a middle name"),
    ("James", "J. W.", True, "consistent — clause 4 is what refuses this one"),
    ("Doctor D. S.", "David Sheppard", True,
     "a title is not a forename: since T-0987 stretch 8 put `doctor` in the "
     "vocabulary these two printings ARE consistent, and this case had gone on "
     "asserting the defect the stretch removed"),
    ("A.", "Augustus", True, "one initial — clause 3 then asks for more"),
    ("G. S.", "Ahira", False, "the first initials disagree, and name_agreement cannot say so"),
    ("B. S.", "Mrs", False, "his wife's line sets no forename at all"),
    ("C L.", "Justus", False, "a first initial against a full forename"),
    ("C L.", "Charles Loomis", True, "the scanner's missing stop"),
]


def self_test():
    fired = []
    for notice, roll, want, what in CASES:
        got, why = consistent(notice, roll)
        if got != want:
            fired.append("  %r against %r: wanted %s, got %s (%s) — %s"
                         % (notice, roll, want, got, why, what))
    checks = [
        (in_common({"occupation": "dry goods, hardware, etc., 131 Lake Street"},
                   {"occupation": "dry goods and groceries, 131 Lake"}) is not None,
         "a street number both printings set"),
        (in_common({"trade_heading": "SADDLERY AND HARNESS",
                    "occupation": "general dealer in saddles, harnesses, trunks"},
                   {"occupation": "saddler and harness maker. 171 Lake"}) is not None,
         "a trade word, one a prefix of the other"),
        (in_common({"trade_heading": "INSURANCE COMPANIES",
                    "occupation": "agent, Fire and Marine Insurance, agency of the "
                                  "National Insurance Company"},
                   {"occupation": "(G. & Seaman)"}) is None,
         "and nothing in common where there is nothing in common"),
        (in_common({"occupation": "attorney, office Clark Street, opposite City Hotel"},
                   {"occupation": "grocer, res Clark"}) is None,
         "a street name alone is not a thing in common"),
        (_initials("Doctor D. S.") == ["d", "s"],
         "a title is NOT counted — T-0987 stretch 8 put `doctor` in the vocabulary, "
         "and this case had asserted the defect rather than the rule ever since"),
    ]
    for ok, what in checks:
        if not ok:
            fired.append("  %s — does not hold" % what)
    for line in fired:
        print(line, file=sys.stderr)
    if fired:
        print("printed_twice --self-test: %d case(s) failed" % len(fired),
              file=sys.stderr)
        return 1
    print("printed_twice --self-test: %d cases hold" % (len(CASES) + len(checks)))
    return 0


if __name__ == "__main__":
    sys.exit(self_test())
