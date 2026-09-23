---
id: T-1476
title: A household record and a household in the town model are not the same unit: the layer holds 1,391 records where the model wants 643 houses, because 814 of the 820 rulings are one person and 424 of those are one name off a letter list
state: open
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-20
closed: null
pr: null
claimed_by: null
blocked_on: null
needs_bake: false
closed_at: null
claimed_run: null
---

A household record and a household in the town model are not the same unit: the layer holds 1,391 records where the model wants 643 houses, because 814 of the 820 rulings are one person and 424 of those are one name off a letter list.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

Found by T-1463 while summing T-1386's presence rulings into the order book's `known`.
The persons re-cut does not depend on the answer to this; the household quota does, and
it is a modelling question the owner rules on rather than a run.

## What the numbers do

Counting the 820 ruled-in records known takes the book's `households_known` from 436 to
**1,256**, and the layer as a whole holds **1,391** household records. The town model
wants **643** households, within a stated range of **469-816**. So the book's household
quota now reads **0 owed** — arithmetic the ruling forces, and not a finding that the
town has all the houses it needs.

## Why the two counts are not measuring the same thing

| | |
|---|---:|
| records T-1386 ruled present | 820 |
| …of those, holding exactly ONE person | **814** |
| …of those, a single name off a post-office letter list | **424** |
| the model's own people-per-house | 2,536 / 643 ≈ **3.9** |

A letter-list name is evidence that a PERSON was in Chicago and collecting mail. Whether
it is evidence of a HOUSEHOLD — a hearth, a roof, a unit the 1840 schedule would have
enumerated — is the question. Today the layer says yes by construction: `data/residents/`
has no other container for a person, so a lone name becomes a one-person household and
the model's household count and the layer's record count stop being comparable.

**Three readings, and the run declines to pick one:**

1. **A record is a household.** Then the town has 1,391 households of 1.6 people and the
   model's 643 is simply wrong — but the model is derived from the 1840 schedule's own
   people-per-dwelling, so this would retire a reading, not a guess.
2. **A letter-list record is a PERSON awaiting a household.** Then `known_households`
   should count only records the sources give a household shape to, and the other 736 are
   people to be seated into houses the book still has to order. The persons arithmetic is
   unchanged either way.
3. **Both, with a third field.** The record stays, and carries whether it is a household
   or a person-pending-a-household, so both counts can be taken off the same layer.

**Acceptance:** the owner rules; the ruling is written into `1835_town_model.json` or the
resident index's own contract; the order book re-derives against it and its household
quota means something again. Nothing is re-graded and no record is deleted to reach it.

**Links:** T-1463 (found it, and carries the measurement in the book's
`what_the_re_cut_found`) · T-1386 (the rulings) · T-1166 (owns the book) · T-1171 ·
T-1175 · T-1179.

## THE OWNER'S RULING, 2026-09-21: a one-person letter-list record is a PERSON AWAITING A HOUSEHOLD

A name on a post-office letter list is evidence that a man was at Chicago. It is not
evidence that he kept a house. The 814 one-person records are people the model has still
to seat, not houses the model has failed to count.

So 1,391 against 643 is a BACKLOG, not a contradiction, and that is the whole of what this
ruling changes. The book's household quota stops reading `0 owed` — which was never true
and was the symptom that raised this — and starts reading what the town actually still owes
once the one-person records are held out of the count of houses.

WHAT THIS DOES NOT DO, stated because the opposite reading is the tempting one: it does not
retire a single record, and it does not downgrade anybody. Every one of the 814 stays
exactly as it is, with its evidence and its grade. What changes is which QUESTION the
record answers — it answers 'was this man here', and it does not answer 'how many houses
stood in this town'. A record may hold both answers later, when something seats him.

THE TEST IS THE EVIDENCE, NOT THE HEAD COUNT. A one-person record is not held out because
it has one person in it — a man may well have lived alone. It is held out where its whole
evidence is a name on a list that says nothing about a dwelling. A one-person record that
carries a street, a tax line, a trade with a premises or any other reading about where he
WAS is a household, and the run must say which of the 814 those are rather than assuming
the count is the criterion.
