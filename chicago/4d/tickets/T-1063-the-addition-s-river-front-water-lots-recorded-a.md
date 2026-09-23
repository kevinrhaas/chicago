---
id: T-1063
title: The Addition's river-front water lots recorded as a lot strip rather than a block grid
state: done
epic: META
requested_by: owner
seen: false
effort: S
legacy_id: null
parent: T-0789
opened: 2026-09-12
closed: 2026-09-12
pr: 1186
claimed_by: run 9/12/2026, 4:51:22 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-12T10:21:28.221Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34686733770
---

The Addition's river-front water lots recorded as a lot strip rather than a block grid.

Piece 4 of 4 of **T-0789 — Kinzie's Addition is on the sheet whole — 54 numbered blocks, 13 named streets, the Kinzie Block and the river-front water lots — and the North Division carries four streets**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

**Acceptance, stated 2026-09-12 before the work:** the river-front strip is recorded as a
LOT STRIP and not as a block grid — a committed reading carrying the run's front line (the
drawn bank), its back line, the reach the back line does not cross, the division strokes
the sheet's ink yields, the count of parcels the terminal figures force, and a frontage and
depth measured against the Original Town's platted 80 ft on the same sheet. No tier pitch
and no column pitch, because the sheet draws none. The reading is machine-derived from the
committed raster through the committed affine and re-derived by the gate in both halves
(`--check` offline, `--check-sheet` off the raster). Every figure not legible on the
facsimile is refused by number, and what the reading cannot settle — which stroke bounds
which numbered lot — is named as a refusal rather than filled in.

**What it came to.** 35 parcels over 667.0 m of bank, from the Original Town's east line to
the harbour. Mean frontage 61.1 ft, depth about 38 ft — wharfage proportions, not town-lot
proportions, against Thompson's 80 ft. (Those metres are the reading re-derived through the
ELEVEN-point fit T-1091 adopted on 2026-09-12, after this reading was first taken on the
eight-point one; the count, the strokes and the refusals are identical either way, so the
2-3 per cent is the pinning's correction and not a re-reading.) The back line is absent over three consecutive
stations between the thirteenth cell and the cell lettered 15, and the run's own figures
reach 35 only if that reach carries lot 14; lot 14 is recorded as inferred from the count,
and the reach itself is left unexplained. Fourteen figures are legible and 21 are refused.
The stroke detector returns 34 to 36 strokes across five reasonable settings where the
figures require 34, so the strokes are graded `inferred` throughout and no per-lot frontage
table is written.
---

**FOUND BY T-1061, 2026-09-12 — blocks 1 and 2 are not on the ground this plat covers, and
the river tier is where to look for them.** The block numerals are now read cell by cell
(`data/traces/kinzie_addition_block_numbering.json`): fifty-one figures, a boustrophedon
that reproduces all fifty-two cells, and the run's first two numbers landing on nothing.
The run puts 1 and 2 west of block 3 on the river tier, beyond the Addition's west boundary
rule at NA x 2918, where Wright draws the Original Town's north division instead — two
eight-lot blocks that carry their own bold 1 and 2 across their mid-lines at NA x 2610-2930,
y 2140-2320, on another survey's ground. Nothing inside the Addition's boundary carries
either figure, and T-1061 refused them in writing rather than counting them onto a cell.
This ticket owns the river tier and the water lots, so the next look belongs here: the strip
of numbered water lots runs 1 to about 35 along the north bank and it is the one thing drawn
between block 3 and the river. Whether the Addition's first two blocks were taken by that
strip, or stand west of the boundary on ground Wright letters to another plat, is the
question — and a recorded plat of Kinzie's Addition, or a Democrat notice selling a lot in
its block 1 or 2 with a street named beside it, would settle it.

**ANSWERED IN PART BY THIS TICKET'S READING, 2026-09-12.** The strip is not blocks 1 and 2.
Its figures are one continuous run of THIRTY-FIVE along a single axis — a lot strip's own
series, reaching far past anything a two-block reading could carry — and the run's terminal
figures 1 and 35 are both legible. So whatever became of the Addition's first two block
numbers, the water lots did not take them. Where they did go is still open, and is filed as
its own ticket rather than left in a closed one.
