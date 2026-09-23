---
id: T-0412
title: A building offered FOR SALE mints a placement reading on the vendor's own firm, so P. Pruyne & Co.'s store carries a corner it never stood on
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-08-29
closed: 2026-09-05
pr: 892
claimed_by: run 9/5/2026, 9:24:59 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-05T15:20:17.915Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/33971528276
---

A building offered FOR SALE mints a placement reading on the vendor's own firm, so
`P. Pruyne & Co.`'s store carries a corner it never stood on.

Found while judging T-0400. `chicago_democrat_1834_05_21#c001` is a `building` claim —
"[W]E offer for sale the House on [the corner] of Lasalle and Lake streets. [It] is 16 by
30 feet" — and P. Pruyne signs it as VENDOR, not as an occupant. The extractor nonetheless
attached a business record to it with `placement.class: corner`, anchor `Lasalle and Lake
streets`. T-0400 merged that record into `P. Pruyne & Co.`, whose store is documented
between Clark and Dearborn streets across four printings, and the corner now stands in that
firm's `placement_readings` as though it were a second frontage of the store.

The live placement is NOT wrong today, and that is luck rather than design: the source
record's live placement was `none`, so `placement_rank` never promoted the corner. A vendor
notice that happened to be the only reading on its record would have moved a firm to a
house it was selling.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

- A claim whose business role is VENDOR of a building — the seller, not the occupant —
  cannot contribute a placement reading to that business, or the reading is marked in a way
  the Evidence panel and `placement_rank` both respect.
- The rule is stated where the other placement rules are stated, not only in code.
- `P. Pruyne & Co.` no longer carries the Lasalle-and-Lake corner among its store's
  placement readings, and the 16-by-30-foot house itself is not lost — it is a documented
  Chicago building with a corner and a footprint and the corpus should keep it as one.
- The sweep says how many other business records rest on a `building` claim the advertiser
  signs as vendor; if the answer is one, say so.

Links: T-0400 (which found it and states the caution in the merge rule), T-0403.
