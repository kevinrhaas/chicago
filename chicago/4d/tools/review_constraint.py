#!/usr/bin/env python3
"""The one reading of `review_required`, shared by the census and the compiler.

AGENTS.md's standing constraint has exactly one mechanism — `review_required: true`
blocks a scene from being marked `released` — and `measure_review_constraint.py`
assertion 6 holds that a record carrying the flag must also say WHY, in its own
prose, wherever in the record that falls. The sentence it finds is the honest
answer to "what is this building held for", and T-0268 puts that sentence on the
visitor's card.

Which means two programs now need the same reading: the census, which judges it,
and `compile_scene.py`, which carries it to the browser. Two copies of a regex
over prose is how they come to disagree — and a card that names a different
reason from the gate is worse than a card with no reason at all, because the gate
would stay green through the drift. So the reading lives here, once, and assertion
7 re-derives it against the committed sidecars to prove the two have not parted.

Nothing in this module reads the filesystem or decides policy. It turns a record
into the sentence the record makes its own case with, and that is all.
"""

from __future__ import annotations

import re

# Assertion 6's two halves. The first is an ENUMERATION of the phrasings this dataset
# actually uses to refer to the flag — `review_required` named outright, "flagged for
# review", "REVIEW IS FLAGGED", "carries the review flag" — and not a sniff for the
# topic: a record can discuss the removal at length (`robert_kinzie_store` did, in three
# fields) without ever saying that it is held. A phrasing outside this list stops the
# claim being made in a form anything can check, which is the thing to fail over rather
# than to widen the pattern for.
FLAG_PHRASE = re.compile(
    r"review[_ ]required"
    r"|flagged\s+for\s+review"
    r"|review\s+is\s+flagged"
    r"|flagged\s+review"
    r"|held\s+for\s+review"
    r"|review\s+flag\b",
    re.I)
# The second half: the subject AGENTS.md places under the constraint. Broad on purpose —
# it is asking whether the record names the subject at all, and the sentence it matched
# is printed for a reader to judge.
CONSTRAINT_SUBJECT = re.compile(
    r"potawatomi|pottawatomie|indigenous|native|removal|consultation|consult\b"
    r"|indian\s+(?:trade|goods|agency|traders|agent)",
    re.I)
# A full stop followed by whitespace and a capital. Not `[.:]` and not any full stop:
# these notes cite pages ("scan p. 253"), and a splitter that broke there reported
# `clybourn_slaughterhouse`'s reason as beginning "253), a treaty-provision post".
SENTENCE_SPLIT = re.compile(r"(?<=\.)\s+(?=[A-Z'\"])")


def prose(obj) -> list[str]:
    """Every string value in a record, at any depth."""
    if isinstance(obj, str):
        return [obj]
    if isinstance(obj, dict):
        return [s for v in obj.values() for s in prose(v)]
    if isinstance(obj, list):
        return [s for v in obj for s in prose(v)]
    return []


def reason_sentence(text: str) -> str | None:
    """The first sentence in which a record refers to the flag it carries.

    Printed rather than merely counted: assertion 6 can only hold that the claim is
    made, and whether the claim is a REASON is a judgement no regex makes. Handing
    the reader the sentence is the difference between a green tick and evidence.

    A sentence carrying BOTH halves is preferred over the first one carrying the flag,
    because the first is often not the reason: `jb_beaubien_homestead` refers to the
    field in an occupants note ("see review_required and the research note") four
    paragraphs before it argues the flag, and printing that sentence would report the
    cross-reference as the argument.
    """
    fallback = None
    for s in SENTENCE_SPLIT.split(text):
        if not FLAG_PHRASE.search(s):
            continue
        s = " ".join(s.split())
        if CONSTRAINT_SUBJECT.search(s):
            return s
        if fallback is None:
            fallback = s
    return fallback


def record_reason(rec: dict) -> str | None:
    """The sentence a whole record makes its case with, or None if it makes none."""
    return reason_sentence(" ".join(prose(rec)))
