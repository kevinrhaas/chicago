---
id: T-0797
title: The School Section's grid and streets: 142 blocks numbered off the sheet, four named and eight unnamed tiers with the unworn status the owner read, and the three Reserved blocks tested against the 1833 sale
state: split
epic: META
requested_by: owner
seen: false
effort: S
legacy_id: null
parent: T-0791
opened: 2026-09-05
closed: 2026-09-06
pr: null
claimed_by: null
blocked_on: null
needs_bake: false
closed_at: 2026-09-06T09:42:03.228Z
claimed_run: null
---

Piece 1 of 2 of **T-0791** — read that ticket for the sheet, the owner's words and the finding; this
piece is the grid, the streets and the reservations, and nothing is spent onto it yet.

## The ask

1. **142 blocks as polygons**, numbered from the registered scan (T-0787), tract-keyed, each numeral
   cited to its crop. The section has its own module — measure a block off the sheet; do not reuse
   Thompson's. Blocks 70/71/78/83–88 close on the South Branch bank once T-0794 lands it, and are
   emitted open-sided until then.
2. **Madison, Monroe, Adams, Jackson** into `data/streets/1835.json`; the **eight unnamed tiers**
   south of Jackson as streets with `name: null` and the sheet cited. All twelve carry the status
   the owner read on 2026-09-05 — *"no alleys and no street names but still a grid that should
   have some wilderness trees"* — platted, unopened, unworn — so a renderer draws a survey line over
   prairie and the flora zones keep their timber across the grid. Record the absence of alleys.
3. **The three "Reserved" blocks** — the north-west corner at Madison and the west line, block 119
   at Madison and State, and 87/88 on the South Branch — into `1835_reserved_ground.json` with the
   sheet as source, **tested against the October 1833 sale**: if no row in `land_sales/` sells a
   lot in them, the sale corroborates the sheet and the grade rises; if one does, both are written.

**Acceptance:** every block polygon carries a numeral with its crop cited; the twelve streets exist
with the unworn status; the three reservations are written with the sale test's result stated
either way. No roof, no land-sale row placed — that is piece 2.
