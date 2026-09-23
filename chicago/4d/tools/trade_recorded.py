#!/usr/bin/env python3
"""Does the 1835 layer RECORD a trade for this person? (T-0867)

One line of code, stated once, because it was written four times and two of
them were wrong.

The residents layer does not leave a trade null when it holds none. It writes
the SENTINEL `none_recorded`, and that is the field's most common value — 738
of the 849 people carried it when T-0569 counted. So the obvious test,

    if not person["occupation"]:        # WRONG

reads every one of those 738 as a person who already has a trade, and a
crosswalk asking "whose trade could this directory supply?" answers nobody. It
is a nil that looks like a finding: `could_carry_occupation: 0` is not the
directory failing to print trades, it is the question never being asked.

T-0569 found it in `crosswalk_norris_1844`, where 23 of 48 matched people were
being read as already-traded and 21 of them had a trade printed against their
name in 1844. `crosswalk_fergus_1839` was written correctly and additionally
refuses `unknown`, the other sentinel the layer writes. `crosswalk_fergus_1843`
and `crosswalk_norris_1844_advertiser` kept the truthiness test, so Fergus's
1843 directory — 2,000-odd entries, most of them with a trade printed — was
reporting `could_carry_occupation: 0` beside Norris's fixed twin reporting 63.
That difference was the finding on this ticket, and the two readings differed
only in this predicate.

The sentinels are listed once here. A fifth crosswalk imports this rather than
writing `if not r["occupation"]` a fifth time.
"""
import sys

# What the residents layer writes where it holds NO trade. These are absences
# spelled out, not values: a person carrying one of them is a person a directory
# may still supply a trade for. Adding to this list widens what a directory is
# allowed to carry, so it is gated (check.sh runs the self-test below).
SENTINELS = ("none_recorded", "unknown")


def recorded(value) -> bool:
    """True where the 1835 layer records a trade for this person.

    False for a null, an empty string, whitespace, and for either sentinel —
    all four are the layer saying it holds no trade.
    """
    if not value or not str(value).strip():
        return False
    return str(value).strip().lower() not in SENTINELS


def absent(value) -> bool:
    """The negation, named the way the crosswalks ask the question: may this
    person's trade be supplied by the directory?"""
    return not recorded(value)


CASES = [
    ("cooper", True, "a plain trade is a trade"),
    ("Tavern Keeper", True, "case and spacing do not matter"),
    ("none_recorded", False, "the layer's sentinel for a trade it does not hold"),
    ("NONE_RECORDED", False, "the sentinel, however it is cased"),
    (" none_recorded ", False, "the sentinel, padded by a hand-edit"),
    ("unknown", False, "the other sentinel — fergus_1839 already refused it"),
    (None, False, "a null is no trade"),
    ("", False, "an empty string is no trade"),
    ("   ", False, "whitespace is no trade"),
    ("none", True, "NOT a sentinel — 'none' alone is not what the layer writes, "
                   "and guessing at it would silently widen the carry"),
]


def self_test():
    fired = []
    for value, want, why in CASES:
        got = recorded(value)
        if got != want:
            fired.append("recorded(%r): expected %s (%s), got %s" % (value, want, why, got))
        if absent(value) != (not want):
            fired.append("absent(%r) must be the negation of recorded(%r)" % (value, value))

    # The sentinels are the point of the module; losing one silently re-breaks
    # every crosswalk that imports it.
    for s in ("none_recorded", "unknown"):
        if s not in SENTINELS:
            fired.append("the %r sentinel has been dropped from SENTINELS" % s)

    # And the bug itself, stated as a test: the truthiness predicate this module
    # replaces must disagree with it on the sentinel. If it ever stops
    # disagreeing, the layer has changed and this module is the stale thing.
    if bool("none_recorded") == recorded("none_recorded"):
        fired.append("the truthiness test must still be wrong about the sentinel — "
                     "if it is not, the residents layer no longer writes it")

    if fired:
        for line in fired:
            print("  " + line, file=sys.stderr)
        print("trade_recorded --self-test: %d case(s) failed" % len(fired), file=sys.stderr)
        return 1
    print("trade_recorded --self-test: %d cases and %d sentinels hold"
          % (len(CASES), len(SENTINELS)))
    return 0


if __name__ == "__main__":
    sys.exit(self_test())
