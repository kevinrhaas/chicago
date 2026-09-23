---
id: T-1495
title: Migrate the North Division parcel's 9 refamilied roofs whose id moves: the recipe's suffix, family, inventory class and authored footprint re-dealt against the new bands, the parcel's group and family totals recomputed, every file naming an old id moved with it, rebaked and published
state: withdrawn
epic: TOWN
requested_by: owner
seen: true
effort: S
legacy_id: null
parent: T-1452
opened: 2026-09-20
closed: 2026-09-21
pr: 1633
claimed_by: null
blocked_on: null
needs_bake: false
closed_at: 2026-09-21T16:05:31.920Z
claimed_run: null
---

Migrate the North Division parcel's 9 refamilied roofs whose id moves: the recipe's suffix, family, inventory class and authored footprint re-dealt against the new bands, the parcel's group and family totals recomputed, every file naming an old id moved with it, rebaked and published.

Piece 2 of 3 of **T-1452 — Migrate the 26 refamilied roofs whose id moves — the phase-one South parcel, the North Division parcel and the three platted blocks — against the measured reference list: sidecars, enclosures, liberties, signage, yard, frontage, lodgers, seating and business files all name these ids, and blk ancillary slots cross the principal/ancillary line; with the screenshot from Lake and Clark**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

## WITHDRAWN 2026-09-21 — A DUPLICATE T-1452 WAS SPLIT TWICE INTO EXISTENCE

`ticket.mjs split` had no guard on the state of the ticket it was splitting, so
T-1452 was split twice, four hours apart on 2026-09-20:

  13:48  run 35529393603 claims T-1452 and splits it into T-1480/T-1481/T-1482
  17:52  run 35542539851 reads T-1452 and splits it AGAIN into T-1494/T-1495/T-1496

Both cuts carve the SAME twenty-six roofs into the same three parcels, so the queue
carried six rows for three pieces of work, in pairs that read as unrelated rows.
This ticket is the second cut's copy of T-1484.

**The work is not dropped — the North Division parcel's nine roofs are T-1480's pieces: T-1483 measured and gated the migration surface (#1588) and T-1484 carries the nine roofs across it, in flight as this is written.**** The guard that stops the next one is in
`tools/ticket.mjs` (`split` refuses a parent that is already `split`, `done` or
`withdrawn`) with assertions 24-27 of `tools/test_ticket_claim_split.mjs`.

**Reopen rule.** If T-1484 ends without landing — withdrawn, or blocked and
abandoned — set this ticket's `state` back to `open` and append its row at the foot of
its band in QUEUE.md. Nothing here is lost, only deduplicated.
