---
id: T-1133
title: The seven one-letter town pairs the post office alone prints
state: done
epic: META
requested_by: loop
seen: false
effort: S
legacy_id: null
parent: T-1130
opened: 2026-09-14
closed: 2026-09-15
pr: 1349
claimed_by: run 9/15/2026, 12:03:04 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-15T06:36:10.976Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34930533221
---

The seven one-letter town pairs the post office alone prints.

Piece 2 of 3 of **T-1130 — Nineteen town cards stand one letter apart in the surname and
identical in the forename, and the merge machinery has never been shown one of them**,
split because the parent needed more than one run's demonstration to be done. The parent
keeps the full ask and its links; this ticket owns one slice of it.

**The line the split is drawn on.** T-1132 took the three pairs with an anchor — a card
that DOCUMENTS its person rather than listing them. Of the seventeen left, seven have BOTH
cards minted by `tools/mint_letter_list_residents.py` out of the Chicago post office's
lists of letters uncalled-for and nothing else: `anchored()` is false on both sides, the
gazetteer holds no other bearer of either stem, and no source outside the post office names
either man. They are:

```
  Joseph Babeu / Joseph Babeue        Reuben Beech / Reuben Bench
  Wm. H. Fraser / Wm. H. Frazer       Robert Hussey / Robert Hussy
  Alonzo Murray / Alonzo Murry        Geo. Square / George Squire
  John Vandine / John Vandino
```

The remaining ten — the pairs the town's own civic lists print — are T-1134, and no card of
theirs is touched here.

## Acceptance

1. Every one of the seven carries a written ruling in `data/residents/card_merge_rulings.json`
   — `merge` under a named C-rule, a refusal that says what keeps the two apart, or
   `undecided` under U1 with the question filed as its own ticket. None left silent, and none
   ruled on the one-letter distance alone: C9's load-bearing clause is a page that
   demonstrates the variation, and a pair with no such page does not fold.
2. The test each pair is weighed on is stated and applied to all seven, not chosen per pair.
3. A merge takes the survivor the existing rules pick, states what each card knew, and the
   town's person count moves by exactly the number merged — the PR says the number.
4. `./tools/check.sh` green, the chain iterated to a fixed point behind the rulings.

## What was done

**The test, and it is the repository's own.** A letter-list card records the RETURN it
stands on — the day the office closed its list — which is not the issue the name was read
in, because the Democrat reprinted one return over as many consecutive issues as it took.
No merge pass had ever read that field. Putting the seven pairs to it splits them three
ways.

**Two stand on ONE PRINTED LINE of one return and fold under C9.** Fraser/Frazer is line 55
and Vandine/Vandino line 158 of the return of 1 January 1834, whose 170 lines T-0424 read at
the page image and T-1010's concordance tied to every extracted reading. The impression of
28 January 1834 sets Fraser and Vandino; the impression of 4 March 1834 sets Frazer and
Vandine; each line's concordance row already carried the other reading as `also_resolved_to`
and nothing had folded the cards. The town's cards fall from 1,283 to 1,281 and its persons
from 1,307 to 1,305.

**Four stand on two different returns and are refused under D6, a new rule.** Babeu/Babeue,
Beech/Bench, Hussey/Hussy, Murray/Murry. D6 is the shape C9 and D5 both miss: the only
witness is a SERIAL closed roll, no single return sets both spellings, so C9's demonstration
is absent and D5's counter-demonstration is absent with it, and one letter is all that is
left — which T-1001 measured and refused. Murray/Murry carries two further discriminators,
both written down: the 1835 line reads ALANZO, and Murray is a surname several Chicago
families bore where Murry is borne by one man.

**One is undecided under U1 and filed.** `square_geo` rests on a line of the 1 April 1834
return that an advertisement bleeds through, and a better impression of the same return
reads it `Geo. Saver`; this corpus already records the disagreement and declines to settle
it off a second transcription. T-1138 owns the page image.

**T-1139** is filed for the class the merges uncovered: nineteen rows of T-1010's
concordance where the card wears the transcription's spelling and the page image sets
another, of which these two were the only ones minted twice.
