---
id: T-1479
title: Move blk_lake_clinton and blk_randolph_clinton onto the West Division grid: blocks 28 and 45 re-cut in the sheet's own arrangement, with the structures seated on their lots re-seated
state: blocked-owner
epic: GROUND
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-20
closed: null
pr: null
claimed_by: run 9/21/2026, 6:33:58 AM CT
blocked_on: Blocks 28 and 45 are cut EIGHT lots four-to-a-face; the plat sheet counts TEN in the West Division's two-by-five arrangement, and the re-cut is refused twice over (measured in data/traces/west_grid_migration_order.json). Three rulings are wanted before any line moves. (1) THE STREET SPACING IS UNOWNED: Clinton to Canal stands at 367.9 ft against the plat's 458 ft, and both tickets the refusal names — T-0444, T-0445 — are closed without having moved it. Does a successor get filed, or does the town keep the short spacing? (2) May the West Division's DOCUMENTED module cut a block that prints no marginal figures of its own? T-1455's rule withholds such a block, so as the rule stands the move yields no lots at all rather than ten. (3) The re-cut re-seats 17 structures across 13 lots, and no withheld block in town has ever carried a seating — so the rule for what a structure on a withdrawn lot is seated on has to be written before the move, not found during it. Nothing has been moved; the measurement and its gate are shipped.
needs_bake: true
closed_at: null
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35594464608
---

Move blk_lake_clinton and blk_randolph_clinton onto the West Division grid: blocks 28 and 45 re-cut in the sheet's own arrangement, with the structures seated on their lots re-seated.

Found working T-1455, which cuts the West Division's own grid. Two cells stand in both
grids — `blk_lake_clinton` (plat block 28) and `blk_randolph_clinton` (block 45) — and
T-1455 left them on the Original Town's grid, carried in the West Division's omissions
with `already_derived_as` and the reason.

**Why they were left.** Both are on the SOUTH Division module: four lots to a face with
an east-west alley, which the sheet's own reading says is the wrong arrangement for
them. Re-cutting them moves ten lot lines each — and committed structure records are
seated against those lots by name (`recon_1835_blk_randolph_clinton_*`, and
`plat_occupancy.py` reports `recon_1835_west_018` lapping onto `blk_randolph_clinton`
lot 2). That is a re-seat and a bake, not a lot-layer change.

**And both print no dimension**, so under T-1455's own rule this grid would WITHHOLD
their lot lines rather than re-cut them — which would take lots away from structures
standing on them. The first question this ticket has to answer is what a structure
seated on a withdrawn lot is seated on.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

1. The pair is DERIVED from the grid's own omissions — an omission carrying
   `already_derived_as` — and never typed, so a third such cell would arrive on its own.
2. The disagreement is stated as a measurement: what the sheet reads against what the
   layer cuts, per block, with the sheet's numerals and its confidence carried.
3. Every reason the re-cut is refused is carried with its arithmetic, re-derived from
   committed files, and each refusal stands independently of the others.
4. What a withheld re-cut would strand is COUNTED — structures by `block_id`, rows by
   lot id, in the committed layers that do the seating — not estimated.
5. The ticket's own first question is answered or shown to be unanswerable, from the
   town's own record rather than from assumption.
6. Nothing moves: no lot line is cut, no record re-seated, no block re-emitted.
7. `--check` re-derives the order byte for byte and is in `tools/check.sh`;
   `--self-test` fires and is gated beside it.


## WHAT IT MEASURED, 2026-09-21 — the re-cut is refused twice over

`tools/measure_west_grid_migration.py` and `data/traces/west_grid_migration_order.json`.

**The disagreement is real and the sheet is `documented`.** On each block
`data/traces/thompson_west_division_lots.json` counts TEN lot numerals in the West
Division's own arrangement — 2|1, 3|4, 6|5, 7|8, 10|9, north to south, two columns by
five rows. The committed grid cuts EIGHT, four to a face, on the module of the other
division. Both blocks, the same gap.

**Refusal 1 — the module does not fit the committed lines.** The West Division block
closes at 378 ft square. The committed lines give block 28 a face of 315.2 ft and block
45 one of 326.1 ft. The two 180 ft lot columns alone want 360 ft, so the arrangement
does not fit *before the alley is cut* — short 62.8 ft and 51.9 ft. North to south the
depths divide into 5.14 and 4.81 lots of the printed 75 3/5 ft, and a plat does not
print a fifth of a lot.

**Refusal 2 — neither block prints a dimension, and this grid withholds such a block.**
Both sheet entries read `Both dimensions; no marginal figures.` Under T-1455's own rule
a block with no figure of its own keeps its boundary, its numeral, its lot COUNT and its
ground, and its lot LINES are withheld. So moving these two onto that grid does not
produce ten lots. It produces none — and takes the eight they have away.

**What that would strand, counted:** 17 structures, 46 seated rows across 13 lots
(`town_lot_line_rails.json` 33 runs + 13 openings, `town_street_edge.json` 1 row).

**The first question has no answer anywhere in the town.** Of the 35 blocks whose lot
lines are withheld, NOT ONE carries a structure or a seated row. The case has never
arisen, so no rule was ever written for it. `blk_randolph_clinton` would be the first,
and it would not arrive alone.

**And the precondition is unowned.** Both refusals name the street spacing — Clinton to
Canal committed at 367.9 ft against the plat's own 458 ft, short 90.1 ft — and both name
T-0445 as the ticket that would move it. T-0444 reported the gap; T-0445 was to close
it. **Both are closed, and the spacing is still short.** The refusal prose in
`tools/generate_plat_lots.py` points a reader forward at work that has already been
done. That is recorded, not repaired: moving a street line is not this ticket's to do.
The gate asserts both tickets are still closed, so the day one is reopened this finding
goes red rather than stale.

## THE OWNER'S RULING, 2026-09-21 (question 1 of 3): FILE A SUCCESSOR for the street spacing

Clinton to Canal stands at 367.9 ft against the plat's 458 ft. That 90 ft is a real defect and
it is nobody's: T-0444 and T-0445 both closed without moving it, which is how a measured error
becomes part of the town by default. A successor ticket owns it.

SO THE WEST DIVISION GRID IS CUT AGAINST A SPACING THAT IS BEING FIXED, not against one that
is known wrong and left. The successor is filed BEFORE blocks 28 and 45 move, and this ticket
names it — re-cutting 32 lots against a grid 90 ft short would bake the error into everything
seated on them, and unpicking that later is far dearer than waiting.

THE SUCCESSOR OWNS THE WHOLE QUESTION, not just the number: which of the two is the control
(the plat's figure or whatever produced 367.9), what moves if the plat wins, and what else in
the West Division is seated on the short spacing today. A ticket that only says '458 not 367.9'
will close the same way its two predecessors did.

QUESTIONS 2 AND 3 ARE STILL OPEN — whether the documented module may cut a block printing no
marginal figures of its own (T-1455's rule withholds it), and what a structure on a withdrawn
lot is seated on. This ticket stays blocked on those two.
