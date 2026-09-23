---
id: T-0233
title: Eight of seventeen dealt lots carry none of their run's own roofs, and nothing was measuring it
state: done
epic: TOWN
requested_by: owner
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-08-27
closed: 2026-08-29
pr: 526
claimed_by: run 8/29/2026, 4:42:28 AM CT
blocked_on: null
needs_bake: false
---

`tools/measure_frontage_entitlement.py` asks the one question the recipes cannot
answer by being read: **does a party-line frontage run stand on the lots it was
dealt?**

It does not, and not by a little.

## Measured 2026-08-27, on `dev` at `e7c3d9bf`

    party-line frontage runs, dealt lots against the ground they stand on (3 units per dealt lot)

    block                       face   dealt      stands on  units load ceil  roofs already on the dealt lots
    blk_south_water_franklin    north  [2, 4, 6]  [6]            3    3    9  —
    blk_south_water_wells       north  [0, 2, 4]  [2, 4]         3    5    9  lot 0: h_jones_store, lot 2: carpenter_south_water_store
    blk_south_water_lasalle     north  [0, 2, 4]  [4]            3    3    9  —
    blk_south_water_clark       north  [2, 4]     [4]            2    3    6  lot 2: pruyne_kimball_drugstore
    blk_south_water_dearborn    north  [0, 2, 4]  [4]            3    5    9  lot 0: chicago_american_office, lot 2: frederick_thomas_shop
    blk_lake_clark              north  [0]        [0]            3    3    3  —
    blk_randolph_dearborn       north  [4]        [4]            3    3    3  —
    blk_randolph_dearborn       south  [1]        [1]            3    3    3  —

    8 runs · 23 units · 8 dealt lot(s) carry none of their run's own roofs

**17 lots dealt, 9 stood on, 8 carrying nothing of the run they belong to.**
Nearly half the frontage this layer is entitled to has never had a roof put on
it, and the schedule counts every one of those lots as spent.

**The gate passes.** Every run is inside its own ceiling — worst is
`blk_south_water_wells` at 5 of 9. This is a measurement with no red attached to
it, which is exactly why it needs writing down: nothing fails, so nothing was
ever going to surface it.

## Why the gap exists, and why it is not a defect in the recipes

It is what T-0079 built. Before the core density standard a run carried exactly
one roof per lot it was dealt, so *dealt* and *stood on* were the same list and
nothing distinguished them. T-0079 retired that — a row is a claim about the
FACE, bounded by the metres of frontage it stands on rather than by the
conjectural side lines it crosses — and the two lists came apart the moment it
landed. A run PACKS from one end of its own strip and `ROW_UNITS_PER_LOT` = 3 of
its units fit inside one lot of this grid, so three lots get entitled and one or
two get occupied.

Nothing measured them apart until a documented building wanted the difference.

## What this is NOT, so it is not worked twice

The five South Water stores are **already standing** — T-0199, closed by #371 —
and they appear in the table above as the roofs on lots 0 and 2 that their runs
were dealt. The owner's 2026-08-27 business-front clause (`exclusive_lots` in
`tools/plat_occupancy.py`) settled that a documented building at the street does
not exhaust a lot of a declared business front, and `generate_block_infill.py`
stopped refusing them.

**That clause answered the collision. It did not touch the bookkeeping.** The
schedule still deals 17 lots to put 9 lots' worth of roofs on them, and
`schedulable_on_committed_ground` is charged for all 17. The eight idle lots are
not a symptom of the refusal that #371 fixed; they were there before it and they
are there after it.

## Provenance: this instrument is a salvage, and one thing did not carry over

The module was written on `steward/t-0199-south-water-five` (#395) alongside the
five stores. That PR is closed on the owner's instruction: T-0199 landed by
another route, its own T-0222 is superseded by T-0223, and the ceiling readings
that held it are three weeks of content out of date. **The instrument was the
only part of it dev did not already have**, and this is it.

It came with a `plat_occupancy.seated_lots` of its own. That never reached dev —
and in the meantime #371 gave `plat_occupancy.lot_holders` the identical shape,
`{block: {lot: [ids]}}`, for the clause. So the salvage imports dev's function
rather than landing a second copy of the same map.

**The one behaviour that did not carry over is a dedupe, and it is not
cosmetic.** `footprints()` yields every committed phase, so a structure rebuilt
on a footprint seating on the same lot twice appears in that lot's list twice.
Every caller on dev reads that list for a NAME — `occupied_lots` takes `ids[0]`,
the clause asks what is standing there — and a name is unharmed by a repeat.
This module is the first caller that reads it as a COUNT, and a count is not: a
two-phase rebuild would spend a lot's frontage twice and report a run over a
ceiling it is inside. Measured on the committed dataset today: **no lot lists any
id twice**, so it changes no number here. It is guarded anyway, in this module
rather than pushed down into `lot_holders`, because narrowing a function eight
callers share to suit one new reader is how a fix becomes a regression.

**The 2026-08-24 figure is not carried across.** #395 reported *20 dealt, 12
stood on*; today's tree reads *17 and 9*. The eight idle lots survive both
readings, and the totals do not — dev has moved ~25 commits. Anyone citing this
finding cites the run, not the memory.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

The question this ticket does NOT settle, and the next run must answer before it
changes anything: **is a dealt-but-unbuilt lot a defect or a reservation?**
Both readings are defensible and they lead opposite ways.

- If it is a **defect**, the schedule is hoarding: it should deal a run the lots
  it will actually stand on, `schedulable_on_committed_ground` recovers up to
  eight lots of headroom, and documented buildings stop competing with ground
  nothing is using.
- If it is a **reservation** — the run's strip is *entitled* to that frontage
  and will fill it as the town densifies — then the count is correct and what is
  wrong is only that nobody could see it.

Whichever it is, it is argued in writing from the table, not assumed. Then:

- `--gate` is either wired into `tools/check.sh` or explicitly left out with a
  reason. It passes today, so wiring it in is cheap and it would catch the
  regression this module exists to make visible.
- The gate is demonstrated to FAIL on a fixture, not only to pass on a clean
  tree. A check nobody has seen fail has not been tested — `blk_lake_clark` and
  both `blk_randolph_dearborn` deals sit at exactly 3 of 3, so a synthetic roof
  on one of their lots is the fixture.
- If the answer is "defect", the eight lots are recovered and
  `schedulable_on_committed_ground` is re-measured — **not asserted from the
  count of 8**, since the schedule may not be able to use all of them.

**Links:** #395 (closed; this instrument salvaged from it) · T-0199 and #371 (the
five stores, and the owner's business-front clause that seated them) · T-0079
(the core density standard that separated *dealt* from *stood on*) · T-0188 (named
the five refusals in writing and left the untangling to an instrument) ·
`tools/plat_occupancy.py` · `tools/reconcile_665.py` (`ROW_UNITS_PER_LOT`).
