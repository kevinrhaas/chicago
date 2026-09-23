---
id: T-1132
title: The three one-letter town pairs an anchor reaches: David/Davis, Pearson/Pearsons, Pruyne/Pryne
state: done
epic: META
requested_by: loop
seen: false
effort: S
legacy_id: null
parent: T-1130
opened: 2026-09-14
closed: 2026-09-14
pr: 1347
claimed_by: run 9/14/2026, 8:46:44 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-15T03:27:00.177Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34918213509
---

The three one-letter town pairs an anchor reaches: David/Davis, Pearson/Pearsons, Pruyne/Pryne.

Piece 1 of 3 of **T-1130 — Nineteen town cards stand one letter apart in the surname and
identical in the forename, and the merge machinery has never been shown one of them**,
split because the parent needed more than one run's demonstration to be done. The parent
keeps the full ask and its links; this ticket owns one slice of it.

**The line the split is drawn on is the repository's own, not a convenience.**
`tools/surname_one_letter_away.py` § `town_pairs` joins 20 pairs of cards one letter apart
in the surname and identical in the forename — `compatible()` in
`tools/consolidate_town_cards.py` cannot see any of them, because it buckets the surname as
one string. Put `consolidate_town_cards.anchored()` over those 20 and exactly three have a
card that DOCUMENTS its person rather than listing them: David/Davis (the Steamboat Hotel),
Pearson/Pearsons (Andreas's speculator), Pruyne/Pryne (the druggist). Those three are the
only pairs where a merge has an anchor to land on, so they are worked first and together.
The other seventeen are T-1133 (the seven the post office alone prints) and T-1134 (the ten
the town's own lists print), and no card of theirs is touched here.

## Acceptance

1. Each of the three carries a written ruling in `data/residents/card_merge_rulings.json` —
   `merge` under a named C-rule, a refusal that says what keeps the two apart, or `undecided`
   under U1 with the question filed as its own ticket. None left silent, and none ruled on
   the one-letter distance alone: C9's load-bearing clause is a page that demonstrates the
   variation, and a pair with no such page does not fold.
2. A merge takes the survivor the existing rules pick, states what each card knew, and the
   town's person count moves by exactly the number merged — the PR says the number.
3. The Fergus 1843 crosswalk is re-derived behind the rulings: a merged card changes which
   residents the surname-plus-initial join reaches, and the initial-absent pool falls by one
   for Pearson.
4. `./tools/check.sh` green, the chain iterated to a fixed point behind the rulings.
