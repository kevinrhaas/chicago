---
id: T-1463
title: The order book counts 457 people known where T-1386 ruled 1,283 into the town, so it is ordering ~826 replacements for people already standing — re-cut the unfilled remainder against the presence rulings the book already reads
state: done
epic: META
requested_by: owner
seen: true
effort: M
legacy_id: null
parent: null
opened: 2026-09-20
closed: 2026-09-20
pr: 1587
claimed_by: run 9/20/2026, 12:09:14 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-20T18:31:58.715Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35524773033
---

The order book counts 457 people known where T-1386 ruled 1,283 into the town, so it is ordering ~826 replacements for people already standing — re-cut the unfilled remainder against the presence rulings the book already reads.

Noticed by the owner off the landing card: 2,267 people against a target of 2,536, and
371 buildings of 668 — *"not sure why they are missing at this point."* The reconstruction
is unfinished, which is expected. What is NOT expected is the size of what the book thinks
is left.

## The book orders replacements for people already standing

`data/reconstruction/1835_reconstruction_order_book.json` says **929 still owed**:

| owner | owed | state | |
|---|---:|---|---|
| T-1175 | 492 | split | fill the beds — boarders, lodgers, hotel guests |
| **T-1171** | **432** | **`done`** | reconstructed families for attested and inferred heads |
| T-1189 | 4 | split | |
| T-1190 | 1 | split | |

Build all 929 and the town reaches **~3,196** against a 2,536 target. The visible gap is
**269**. The book is over-ordering by roughly 826, and it is over-ordering by almost exactly
the number of people T-1386 ruled into the town.

## The book already knows, and already reads the file

Its own `population_ruled_in` block:

```
persons_known_today:                          457
persons_known_if_the_rulings_are_summed_in: 1,283
what_re_cuts_the_quotas:  T-1196, T-1197, T-1179
```

**1,283 is exactly the 409 attested + 874 inferred the card prints.** And
`1835_presence_rulings.json` names `tools/build_order_book_1835.py` in its own `read_by`
list — the book READS the rulings and reports what summing them in would give. It does not
sum them.

The block that stops it is the book's rule 3, *"presence is the test for known"*: a household
whose presence reads `uncertain` is not counted as known. 820 households and 827 persons sit
there — **ruled present by T-1386, still counted unknown by the book.**

## This is applying a ruling already made, not making one

`1835_presence_rulings.json` carries the rule and the owner's words with it:

> An attested or inferred resident is in the town's population unless there is EVIDENCE they
> were not — a documented departure, a dated appearance elsewhere, a source that places them
> outside. `uncertain` with no tier and no contrary reading is not that evidence. The owner,
> 2026-09-19: *"if they are attested that's ideal if we know them already"*, and *"I want a
> full population of the city to work from"*.

So the subtraction is stale, not contested. No new modelling decision is required — and a run
that finds one required should stop and say so rather than invent it.

## T-1171's 432 is probably the same staleness, and must be checked not assumed

T-1171 closed **2026-09-18** (PR #1476) having drawn 124 of 556. T-1386's rulings landed
**2026-09-19** — the day after. So its quota was cut against a town that did not yet hold the
827 ruled-in people, and the 432 may be an artifact of the same lag rather than work never
done. T-1174 (856/856) and T-1347 (308/308) both closed exact, so the counter itself works.

**Verify before concluding.** If the 432 is real, T-1171 reopens; if it is an artifact, the
re-cut discharges it and the ticket says so in writing. Guessing either way is the failure.

**Acceptance:**

- The book's `known` counts the people T-1386 ruled present, or states in writing why rule 3
  should still exclude them. One of the two, argued — not both, and not neither.
- **Only the unfilled remainder is re-cut.** The owner's ruling of 2026-09-20 on T-1459
  stands here too: no bucket's target may fall below what has already been drawn against it,
  and a re-cut that would do so is REFUSED by name with both numbers rather than clamped.
  The 1,370 persons already drawn do not move.
- **T-1171's 432 is adjudicated, with the dates.** Either it is owed — and T-1171 reopens —
  or the re-cut discharges it and the ticket records that its quota was cut against a
  pre-ruling town. The answer is measured, not inferred from the fact that the ticket is
  closed.
- After the re-cut, `persons_to_reconstruct − filled` plus the people now standing lands on
  the model's target within its stated range. A remainder that would overshoot 2,536 is the
  bug this ticket exists to remove, so the check says the number out loud.
- `build_order_book_1835.py --check` re-derives and its self-test gains a guard that fires
  when the book's `known` and the presence rulings disagree — so this cannot go stale again
  in silence, which is how it got here.
- The roofs are NOT touched. `roofs_to_build: 297` lives in `totals` and the structures
  family carries `to_reconstruct: 0`; the roof programme is T-1196 (done) and T-1197's
  re-audit. If the re-cut moves the roof figure, that is a finding to report, not to act on.

**Stop condition:** the book's remainder is what the town actually still needs, and no bucket
orders a person the layer already holds.

**Links:** T-1386 (the rulings, and the owner's direction) · T-1166 (owns the book) ·
T-1459 (the trade re-cut — the same subtraction going stale, and it should run after this) ·
T-1171 · T-1175 · T-1196 · T-1197 · T-1179.
