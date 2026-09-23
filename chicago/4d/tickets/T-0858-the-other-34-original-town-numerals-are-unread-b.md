---
id: T-0858
title: The other 34 Original Town numerals are unread because the street grid stops: Wright's Washington-Madison tier, the North Division and the West Division past Clinton
state: split
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-05
closed: 2026-09-12
pr: null
claimed_by: run 9/12/2026, 3:50:06 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-12T20:55:02.757Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34718095604
---

The other 34 Original Town numerals are unread because the street grid stops: Wright's Washington-Madison tier, the North Division and the West Division past Clinton.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

**Found by T-0788, 2026-09-06.** T-0788 read twenty-two of Wright's block numerals off the
georeferenced BPL scan by cutting each crop from that block's own committed street lines. It
stopped at twenty-four blocks of fifty-eight for one reason, and it is not the sheet: **the
committed street grid does not reach the rest.** `data/streets/1835.json` holds South Water,
Lake, Randolph and Washington east–west, and Clinton to State north–south. It has no Madison
Street, nothing in the North Division, and nothing west of Clinton.

So the unread numerals are:

| where | numerals the sheet carries (per T-0788's ticket, to be read not assumed) |
|---|---|
| Washington – Madison | 52 53 54 55 56 57 58 |
| North Division, Kinzie St to the bank | 7 6 5 4 3 2 1, and 14 15 on the North Branch's west bank |
| West Division outside the two tiers read | 10 9 8 · 11 12 13 · 25 24 23 22 · 26 27 · 47 46 · 48 49 50 51 |

**Do NOT read them by eye off the sheet.** That is the method T-0788 replaced: on paper that
stretches 3.7% anisotropically, a numeral located by the reader is a numeral placed by the
reader. The block-cut crop is what makes the identification the georeference's job instead of
the reader's, and it needs a street line to cut from.

**Block 30 is the small open question inside this.** The Lake–Randolph tier reads 29 on the west
bank of the South Branch and 31 on the first block east of it, and the ground between them is
water — Market Street runs along the east bank there. So 30 is on ground this project has not
read, and this ticket is where it should turn up.

**Acceptance:** either (a) the street control for one of the three areas above is committed
first and its numerals are then read by the same block-cut method, citing a crop region per
block, with the same grading — or (b) the ticket is split so that the street control is its own
unit and this one waits on it. Nothing is read by eye. `blocks_not_in_the_grid` in
`data/traces/thompson_block_numbering.json` already holds two readings (44 and 43) waiting for a
grid cell to land on; anything read here with no cell to land on joins them rather than being
forced onto a cell that is the wrong shape.
