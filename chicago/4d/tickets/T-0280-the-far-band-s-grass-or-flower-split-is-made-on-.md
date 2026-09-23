---
id: T-0280
title: The far band's grass-or-flower split is made on the forb lattice's CLAMPED share
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-08-28
closed: 2026-09-13
pr: 1245
claimed_by: run 9/13/2026, 4:47:39 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-13T10:55:26.878Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34750045325
---

The far band's grass-or-flower split is made on the forb lattice's CLAMPED share.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

Found while declaring the forb lattice's ceiling for T-0019.

`rebuildFar` in `renderers/web/js/flora.js` decides whether a far card stands for a grass or a
flowering plant with

    split = zone.matrixShare * (1 - forbShare / (zone.matrixShare + forbShare))

and `forbShare` there is the **lattice-clamped** number — `min(1, density x cell^2 / perCell)`,
capped at 1.000. Nine of the ten populated forb layers sit on that cap (T-0019,
`tools/forb_clamp_baseline.json`), so for all nine the far band's split is made on 1.000 and not on
anything their records say. `z06_dense_forest` asks 66.381 plants/m2 and `z01_wet_prairie` asks
0.407; the far band splits both as though they asked for exactly the same thing.

The clamp is a property of the FORB RING's lattice — one plant per 2.89 m2 slot. The far band is a
different lattice with a different cell (3.4 m and 9.5 m, `perCell: 1`), and nothing about the forb
ring's slot size bounds a proportion drawn on it. So a ceiling from one layer is deciding the
species mix of another.

**What is NOT obvious, and why this is a ticket rather than a one-line fix.** Simply passing the
unclamped share is probably wrong too: at 66.381 plants/m2 the split would make essentially every
far card in the dense forest a flower, and the formula already mixes units — `matrixShare` is
`cover.matrix_fraction`, a fraction of GROUND COVERED, while `forbShare` is a slot-occupancy chance
derived from stem density. The honest quantity for an aggregate card standing for several square
metres of ground is almost certainly a COVER figure on both sides, which is the territory T-0225 is
already in.

**Acceptance:** the far band's grass-or-flower split is made on a quantity that is the same on both
sides of the ratio and is not bounded by the forb ring's lattice ceiling, with the before/after mix
measured per community at `prairie_west` and in `z06_dense_forest` — or the present formula is
defended in writing against that reading and this ticket withdrawn.
