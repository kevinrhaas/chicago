---
id: T-1139
title: Nineteen minted cards wear the transcription's spelling where the 1 January 1834 page image sets another
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-15
closed: 2026-09-15
pr: 1350
claimed_by: run 9/15/2026, 4:41:02 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-15T10:55:03.225Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34953599120
---

Nineteen minted cards wear the transcription's spelling where the 1 January 1834 page image
sets another.

**Filed by T-1133**, which merged two of them and found the class underneath.

## What was found

`data/research/newspapers/letter_list_1834_01_01_concordance.json` (T-1010, out of T-1008)
ties each of the 170 printed lines of the Chicago post office's return of 1 January 1834 —
read at the page image of the ninth impression by T-0424 — to the names this project
extracted from the impressions it transcribed. Its `name_differs` list holds **nineteen**
rows where "the two readings disagree in their letters", each carrying `card_follows`, and
on most of them the card follows THE TRANSCRIPTION while the page image is the stronger
witness. Two examples, both now closed for a different reason:

* line 55 — image `Wm. H. Frazer`, card `Wm. H. Fraser`
* line 158 — image `John Vandine`, card `John Vandino`

Those two were minted TWICE, once from each reading, and T-1133 folded the duplicates under
C9. The fold did not answer this question and deliberately said so: which of two readings
of a line the surviving card wears is a question about what the line says, not about how
many men it names. The other seventeen rows reach one card each and nothing has ever
weighed them.

## Acceptance

1. All nineteen rows are adjudicated, one at a time, with the rule named: the card takes
   the image's reading, or it keeps the transcription's and says what outranks the image
   there. None is left silent and none is decided on which file was written first.
2. Where a card is renamed, the `person_id` is NOT silently rewritten — every crosswalk,
   the identity master and the smoke cohorts cite it. Say how the rename is carried, or
   rule that the displayed name moves and the id does not, and write that rule down.
3. The concordance re-derives (`tools/concord_letter_list_1834_01_01.py --check`) and
   `name_differs` shrinks by exactly the number ruled onto the image.
4. `./tools/check.sh` green, the chain iterated to a fixed point.

**What this is a symptom of, and it is NOT in scope here.** The return of 1 January 1834 is
the only one of this corpus's returns with a concordance at all. The other returns have
none, so the same class exists on them unmeasured. Whether to build a second concordance is
a separate decision and a larger one; this ticket is the nineteen rows that are already
counted.
