---
id: T-0131
title: The fences reach the town's western blocks
state: withdrawn
epic: TOWN
requested_by: steward
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-08-21
closed: 2026-08-21
pr: null
claimed_by: null
blocked_on: null
needs_bake: false
---

The fences reach the town's western blocks.

**WITHDRAWN THE DAY IT WAS OPENED, and the reason is worth keeping.** T-0068 first shipped 83
of the town's 109 fenceable platted lots and held four blocks at the plat's western margin —
`blk_lake_market`, `blk_randolph_market`, `blk_lake_clinton`, `blk_randolph_clinton`, 26
improved lots — back for the renderer's 80-draw-call ceiling. This ticket was that remainder.

The owner ruled the same day, verbatim: *"ok to raise the draw call budget"*. So the ceiling
moved rather than the town — `renderers/web/js/main.js` `BUDGET.drawCalls` is 96 now, with the
measurement that chose it written at the definition site and pinned by the release gate — and
the four blocks went into T-0068's own parcel. There is nothing left here to do.

What is worth carrying forward is the measurement, and it lives in **T-0115's ledger** rather
than in this file: a chunked layer buys culling by SPENDING CALLS, the shadow pass is the larger
half of what it spends, and the packing is still leaving about five calls on the table.

**Acceptance:** withdrawn — the work is in T-0068.
