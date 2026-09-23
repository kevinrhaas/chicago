---
id: T-1039
title: A row is not a parcel, asked of the town lots: volume L5A enters one lot twice and three times over, in paired and doubled prices that look like halves of a parcel rather than duplicate rows
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-11
closed: 2026-09-11
pr: 1145
claimed_by: run 9/11/2026, 2:03:44 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-11T19:39:00.923Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34636497778
---

A row is not a parcel, asked of the town lots: volume L5A enters one lot twice and three times over, in paired and doubled prices that look like halves of a parcel rather than duplicate rows.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

- the shape is counted, not asserted: how many of the 619 town-lot rows name a block-and-lot
  another row of the same volume also names, on the same day and the same page, and how their
  prices relate — the observed pattern is a PAIR at one price plus a row at exactly twice it;
- the reading is decided against the source and written down: halves of one parcel entered
  under two names with the whole carried as a third row, or duplicate rows of one
  transaction, or an assignment (the `AS` suffix T-0885 found in the school section);
- whatever the answer, no row is dropped and no name is merged — T-0885's rule holds: whether
  a pair is one transaction or two is an identity ruling, and `resident_crosswalk.json` is
  where this domain makes those;
- the effect on the domain's own figures is stated: 619 rows against how many distinct
  parcels, and what that does to the purchase-money totals the cards carry;
- `bash tools/check.sh` green.

## WHERE THIS CAME FROM

T-1034 cohort B, from the register neighbours read to test the sequence argument. Four
instances turned up inside twenty-four purchasers: lot 8 of block 53 entered three times for
GARRETT A at $940, $940 and $1,880; lot 8 of block 32 twice at $3,000 for LOYD A and LOYD J;
lot 5 of block 54 three times at $1,110 for MERRILL G W, SHERWOOD S J and WHITLOCK T; lot 4
of block 29 twice at $50 for ROBERTS E and MENARD PETER JR. **T-0885 asked exactly this of
the school section and answered it there (38 parcels entered twice, 26 of them the Hales);
volume L5A was never asked.**

