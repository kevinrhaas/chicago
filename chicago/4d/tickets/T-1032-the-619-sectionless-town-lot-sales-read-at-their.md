---
id: T-1032
title: The 619 sectionless town-lot sales read at their detail pages and committed as their own deposit — the harvest only, nothing joined to ground yet
state: done
epic: META
requested_by: loop
seen: false
effort: S
legacy_id: null
parent: T-1028
opened: 2026-09-11
closed: 2026-09-11
pr: 1121
claimed_by: run 9/11/2026, 5:43:54 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-11T11:41:43.404Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34590257523
---

The 619 sectionless town-lot sales read at their detail pages and committed as their own deposit — the harvest only, nothing joined to ground yet.

Piece 1 of 2 of **T-1028 — The 619 town-lot sales the by-section sweep cannot see: Cook County's register describes a lot and block with no section, so 466 sales of 1836 — the town's own ground — are outside the land_sales deposit**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

- All 619 sectionless rows the probe lists are read at their own detail pages and
  committed as `text/isa_land_tract_sales_cook_town_lots_through_1836.tsv`, in the
  sweep's own sixteen columns.
- The harvest is checked against the probe it was drawn from — same purchase numbers,
  same purchaser, date and legal description, and Section/Township/Range/Meridian
  still empty — and that check runs on the gate, with self-tests proving it fires.
- NOTHING downstream moves: no record id is minted, no crosswalk proposal is made, no
  card is touched, and `complete_for_1836_cook_county` stays `false`. That is T-1033.

**What the reading found.** One event, and the register says so on every row: all 619
are canal sales (`CN`) in volume `L5A` across thirty of its pages, all give Residence
UNKNOWN, and none states an acreage at all — 0000.00 acres at 000.00 an acre, only a
total price. 466 are dated 1836 and **447 of those fall between 20 and 30 June**, 64 of
them on the 28th: the canal land sale of June 1836, day by day. 133 are 1830, 16 are
1831, and four carry a year the register itself mis-prints, carried unsmoothed.

**$1,399,066.33 of ground, against the by-section deposit's $125,223.35** over seven
townships and 57,171 acres. 255 distinct purchaser spellings; the busiest are EGAN
WILLIAM B (35 lots), FOSTER AMOS (25), COOK CNTY COM (24), PECK P F W (15).

**What T-1033 inherits, measured.** 616 of the 619 parse as a lot and a block over 57
distinct blocks, 1 to 58, in four forms — `L4BL36CHIOT` ×517, the shorter `L2B17CHIOT`
×53, a half or quarter OF a lot (`W2L3B34CHIOT`, `E2E2L1B46CHI`) ×46 — and three that
a parser must refuse: `L5BLCHIV`, `L1013CHIOT`, `SEL1B28CHIOT`. `tract()`'s current
`LOT` pattern is the school section's `LOT5BL3` and matches none of them. Town codes:
`CHIOT` 334, `CHIOTV` 107, `CHIV` 92, `CHI` 62, `CHIOTVO` 20, one row with none — and
`CHIOTVO` ends in the `VO` that `tract()` reads as a void sale, which is a question
T-1033 must answer rather than assume.

**How it was fetched.** `harvest_land_sales.py --town-lots COOK`, new in this ticket:
it reads the committed county list back rather than re-walking 83 pages, takes the rows
with no section, and asks for one detail page each at the reader's three-second pace.
`--limit` makes it resume from its own deposit rather than a cache, so 619 pages crossed
the run's 600-second foreground ceiling in five passes with no page asked for twice.
