---
id: T-0026
title: The southern buildable ground and its schedule
state: done
epic: GROUND
requested_by: loop
seen: false
effort: M
legacy_id: T-E4
parent: null
opened: 2026-08-17
closed: 2026-08-24
pr: 380
claimed_by: run 8/24/2026, 1:58:10 PM CT
blocked_on: null
needs_bake: true
---

The southern buildable ground and the re-apportioned schedule, after T-E2's reservation
census. Deep history: § T-E4 (~7357).

**Acceptance:** southern parcels build only on ground T-E2 admits; schedule reconciles.

---

## REFUTED 2026-08-24 — there is no southern buildable ground to apportion

**The premise does not survive the parcel's own acceptance clause.** T-E4 said a roof may
stand only where the ground is *covered by the heightfield AND historically plausible*, and
told the next run to widen the eligible ground south. Measured by the new
`tools/measure_southern_ground.py`, the first condition is unsatisfiable everywhere south of
the town: **the modelled box ends at local N -400 m, and that line falls INSIDE Washington
Street's own 80 ft platted corridor.**

| | measured |
|---|---|
| land above the water surface south of Washington's platted corridor | **0.0819 ha** (131 of 135 cells) |
| ...of it in the South Division | **0.0000 ha** — every cell is west of local E -10, the West Division bank across the South Branch |
| Washington's own corridor lying off the field | **0.33 ha**, over **899 m** of its length, up to **7.29 m** deep |
| Madison Street below the field's south edge | **125.2 m** at State, **119.2 m** at Market |
| the plat's last tier — Washington to Madison, Market to State | **6 blocks, 48 lots, 6.28 ha, 0 of 24 boundary points on modelled ground** |

**And the schedule was naming the wrong blocker.** `south_plat_beyond_committed_control`
holds 120 roofs — the largest of the three gated balances — against *street control*. Every
north-south column of the south plat has its committed centreline cut at exactly N -400, the
field's own south edge, and the control that would carry them further is already committed
(`G1`, State & Madison, an OpenStreetMap node with an id). **Street control stops where the
ground does.** Carry the lines without the terrain and every placement on the six blocks that
follow dies in `tools/generate_block_infill.py`.

Ground east of State was never available either: T-E2 settled that it is the United States
Reservation.

**Shipped:** `tools/measure_southern_ground.py` (report + two assertions + self-test, wired
into `tools/check.sh`); `tools/reconcile_665.py` composes the South balance's `waiting_on`
from the measurement and carries the figures in `coverage.southern_ground`;
`tools/compile_scene.py` puts the measured southern edge on the ground card a visitor opens.
No structure record moved, no roof was added or removed, the 665 total is unchanged, nothing
was baked. Full box: ROADMAP § T-E4; narrative: STATUS.md.

**Successor: T-0219** — finish the heightfield south to Madison. What it needs is narrow: the
South Branch's two banks carried from N -405 to about N -531, 126 m per bank. The lake shore
(N -589.2) and the sand bar (N -436) already reach past Madison.
