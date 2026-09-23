#!/usr/bin/env python3
"""May a second discriminator break a directory tie? (T-0696)

The directory crosswalks match a printed entry to a person of 1835 on the folded
SURNAME plus the first initial, refusing a full-forename disagreement (T-0670).
What is left over is the case that rule genuinely cannot decide: one printed line
that two people of 1835 both meet (CONTESTED), and one person of 1835 who meets
several printed lines (AMBIGUOUS). T-0696 asked whether a trade, an address or a
year may break those ties, and on what terms.

THE RULING, and it is three answers, not one.

  A TRADE MAY NARROW A TIE. It never makes a match. Where exactly one side of a
  tie carries an 1835 trade that agrees with the trade printed against the name,
  that side is NAMED and the tie is filed as `discriminated` — a separate,
  weaker outcome that the pass spending this proposal decides about for itself.
  Nothing enters `matches` on a discriminator, and no grade moves in either
  direction. John S. C. Hogan, postmaster in 1835, against "Hogan, John Stephen
  Coates, ex-postmaster" is the case the rule exists for: his rival John Hogan
  has no trade recorded at all, and the printed line names the office.

  A PREMISES MAY NOT, and the coarse table in T-0696 that said it settled eight
  groups was measuring the wrong thing. The 1835 layer records a premises as a
  STRUCTURE ID — `hogan_store`, `peck_store` — and the directories print an 1843
  or 1844 street address, or, in both surviving cases, not a place at all but a
  person to board with ("bds Charles L. P. Hogan"). The two are never compared,
  because they are not comparable. What "an 1835 premises names exactly one of
  the rivals" actually measures is which rival the town has already placed on the
  ground, and preferring the better-documented record is how a reconstruction
  invents a fact. Both cases the test still finds today are the Hogan group,
  which the trade settles on its own evidence. So: refused, and written down.

  A YEAR MAY NOT, for the plainer reason that there is nothing to compare. The
  1835 layer carries no birth year for either side of any live tie, and Fergus's
  bracketed death notes are T-0574's to read, not this file's.

THE TERMS a trade is narrowed on, written out so they read back without the code:

  1. AGREEMENT IS SUBSTRING, EITHER WAY, after folding underscores to spaces and
     dropping case and punctuation. `none_recorded` is not a trade. The test is
     COARSE BY ADMISSION — the residents vocabulary and the directories' trade
     words are not the same vocabulary, and T-0661 is the ticket for the words
     themselves.
  2. IT MUST NAME EXACTLY ONE SIDE. Two sides named, or none, and the tie stands.
  3. THE LOSER IS FILED, NOT DROPPED, and filed as SILENT: the directory does not
     say he is not the man, it says nothing about him. A refusal that reads as a
     contradiction would be a stronger claim than the evidence.
  4. THE NARROWING IS `reconstructed`, never attested. No source says these two
     readings are one man; the agreement is the reasoning, which is what
     `reconstructed` means here. It CARRIES the confidence of the 1835 trade it
     leaned on, so a reader can see whether that leg is attested.

Run it directly for its self-test: `python3 tools/tiebreak.py --self-test`.
"""
import re
import sys

BLANK = ("", "none_recorded", "none recorded", "unknown", "not_recorded")

CONFIDENCE = "reconstructed"
KIND = "trade"

# The two discriminators the ruling REFUSES, kept here rather than in prose so
# that a later run proposing one has to argue with a named record.
REFUSED_DISCRIMINATORS = {
    "premises": "The 1835 layer records a premises as a structure id and the directories "
                "print a later street address, or a person to board with. They are not "
                "comparable, so what the test measures is which rival the town has already "
                "placed on the ground — and preferring the better-documented record is how "
                "a reconstruction invents a fact.",
    "year": "Neither side of any live tie carries a birth year in the 1835 layer, so there "
            "is nothing to compare. Fergus's bracketed death notes are T-0574's to read.",
}


def _norm(text):
    """Fold a trade word for comparison: underscores to spaces, case and
    punctuation away, runs of space to one."""
    s = (text or "").replace("_", " ").lower()
    s = re.sub(r"[^a-z0-9 ]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def is_trade(value):
    """True where the 1835 layer records a trade. `none_recorded` records none."""
    return _norm(value) not in BLANK


def trades_agree(occupation_1835, printed):
    """(agree?, why) for an 1835 trade against the trade printed in a directory.

    Substring either way — the printed line runs long ("clerk, Charles L. P.
    Hogan", "editor and proprietor Prairie Farmer") and the 1835 word is one or
    two tokens, so the 1835 word inside the printed line is the usual shape; the
    other direction catches `forwarding_and_commission` against "commission".
    """
    a, b = _norm(occupation_1835), _norm(printed)
    if not is_trade(a) or not b:
        return False, "no trade on one side"
    if a == b:
        return True, "the same trade word"
    if a in b:
        return True, "the 1835 trade stands inside the printed line"
    if b in a:
        return True, "the printed trade stands inside the 1835 trade"
    return False, "two trades that do not agree"


def narrow(sides):
    """Narrow a tie on the trade, or leave it standing.

    `sides` is a list of dicts, each `{"key", "occupation_1835", "printed"}` —
    one per side of the tie. For a CONTESTED group the sides are the rival
    residents and `printed` is the one printed line they all meet; for an
    AMBIGUOUS resident the sides are the printed entries and `occupation_1835`
    is the one resident's trade, repeated.

    Returns `{"named", "why", "sides": [...]}` where `named` is the key of the
    one side the trade names, or None when the tie stands.
    """
    named, rows = [], []
    for s in sides:
        ok, why = trades_agree(s.get("occupation_1835"), s.get("printed"))
        rows.append({"key": s["key"], "agrees": ok, "why": why})
        if ok:
            named.append(s["key"])
    if len(named) != 1:
        why = ("the trade names %d of the %d sides, and a discriminator fires only when it "
               "names exactly one" % (len(named), len(sides)))
        return {"named": None, "why": why, "sides": rows}
    winner = named[0]
    for row in rows:
        if row["key"] != winner:
            row["outcome"] = "refused_by_discriminator"
            row["refusal"] = (
                "The trade printed against this name agrees with %r and not with this side. "
                "SILENT, NOT CONTRADICTED: the directory does not say this is not the person, "
                "it says nothing about them. The match is still not made — a narrowed tie is "
                "filed, never matched." % winner)
        else:
            row["outcome"] = "named_by_discriminator"
    return {
        "named": winner,
        "why": "the trade names exactly one of the %d sides" % len(sides),
        "sides": rows,
    }


def block(result, occupation_1835, occupation_confidence):
    """The record filed on a narrowed tie, or None where the tie stands."""
    if not result["named"]:
        return None
    return {
        "kind": KIND,
        "named": result["named"],
        "confidence": CONFIDENCE,
        "occupation_1835": occupation_1835,
        "occupation_1835_confidence": occupation_confidence,
        "test": "substring either way, coarse by admission (T-0661 is the trade vocabulary)",
        "rule": ("T-0696. A trade may NARROW a tie and never make a match: this tie is filed "
                 "as discriminated, stays out of `matches`, and moves no grade. The narrowing "
                 "is reconstructed — no source says these readings are one person, the trade "
                 "agreement is the reasoning — and it carries the confidence %r of the 1835 "
                 "trade it leaned on. A premises and a year are refused discriminators; the "
                 "reasons are in tools/tiebreak.py." % (occupation_confidence or "unrecorded")),
        "sides": result["sides"],
    }


CASES = [
    # (1835 trade, printed line, agree?, what it is)
    ("postmaster", "ex-postmaster", True, "Hogan — the case the rule exists for"),
    ("none_recorded", "ex-postmaster", False, "no trade recorded is not a trade"),
    (None, "tailor", False, "and neither is nothing at all"),
    ("baker", "tailor", False, "two trades that disagree"),
    ("tailor", "tailor", True, "the same word"),
    ("forwarding_and_commission", "commission merchant", False,
     "the printed line is longer than the 1835 word and neither contains the other"),
    ("dry_goods_merchant", "dry goods", True, "the printed trade inside the 1835 trade"),
    ("attorney", "attorney at law", True, "the 1835 trade inside the printed line"),
    ("clerk", "clerk, Charles L. P. Hogan", True, "a printed line that runs long"),
    ("merchant", "", False, "nothing printed is not an agreement"),
]


def self_test():
    fired = []
    for a, b, want, why in CASES:
        got, reason = trades_agree(a, b)
        if got != want:
            fired.append("%r vs %r: expected %s (%s), got %s (%s)"
                         % (a, b, want, why, got, reason))

    # A tie the trade names exactly one side of is narrowed, and the loser is
    # filed as silent rather than contradicted.
    won = narrow([
        {"key": "hogan_john_s_c", "occupation_1835": "postmaster", "printed": "ex-postmaster"},
        {"key": "hogan_john", "occupation_1835": "none_recorded", "printed": "ex-postmaster"},
    ])
    if won["named"] != "hogan_john_s_c":
        fired.append("the Hogan tie must narrow onto the postmaster, got %r" % won["named"])
    loser = [s for s in won["sides"] if s["key"] == "hogan_john"][0]
    if loser.get("outcome") != "refused_by_discriminator" or "SILENT" not in loser["refusal"]:
        fired.append("the loser of a narrowed tie must be filed as silent, not contradicted")

    # Two sides named is not a narrowing, and neither is none.
    both = narrow([
        {"key": "a", "occupation_1835": "tailor", "printed": "tailor"},
        {"key": "b", "occupation_1835": "tailor", "printed": "tailor"},
    ])
    if both["named"] is not None:
        fired.append("a trade that names both sides must leave the tie standing")
    none = narrow([
        {"key": "a", "occupation_1835": "none_recorded", "printed": "tailor"},
        {"key": "b", "occupation_1835": None, "printed": "tailor"},
    ])
    if none["named"] is not None:
        fired.append("a trade that names no side must leave the tie standing")
    if block(none, None, None) is not None:
        fired.append("a tie that stands files no discriminator block")

    # The block carries the leg it stands on, and says it is reconstructed.
    b = block(won, "postmaster", "attested")
    if b["confidence"] != "reconstructed" or b["occupation_1835_confidence"] != "attested":
        fired.append("the block must be reconstructed and carry the 1835 trade's confidence")

    # The refused discriminators stay refused, and stay explained.
    for name in ("premises", "year"):
        if len(REFUSED_DISCRIMINATORS.get(name, "")) < 80:
            fired.append("the %s refusal must carry its reason" % name)

    if fired:
        for line in fired:
            print("  " + line, file=sys.stderr)
        print("tiebreak --self-test: %d case(s) failed" % len(fired), file=sys.stderr)
        return 1
    print("tiebreak --self-test: %d trade cases and 6 tie cases hold" % len(CASES))
    return 0


if __name__ == "__main__":
    sys.exit(self_test())
