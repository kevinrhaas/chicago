---
id: T-0332
title: The sheet's one brick is called chimney_brick, and a wall now reads it
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-08-28
closed: 2026-09-13
pr: 1242
claimed_by: run 9/13/2026, 3:22:36 AM CT
blocked_on: null
needs_bake: true
closed_at: 2026-09-13T09:34:41.841Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34747315083
---

The sheet's one brick is called `chimney_brick`, and a wall now reads it.

T-0267 converged `fort_structure.WALL_RGBA["brick"]` onto `common/materials.py::CHIMNEY_BRICK`,
so the town has exactly one brick colour again — on three committed masters, two of them attested
brick walls and none of them a chimney. `frame_tavern.py` had already been doing the same thing
(`BRICK_RGBA = materials.CHIMNEY_BRICK.rgba`). The row is therefore named for one surface and read
by three.

**Why it was not fixed inside T-0267.** `generators/common/materials.py` is a geometry module
(`generators/code_inputs.py::geometry_modules`), so its bytes are in the input hash of **every**
asset in the town — a one-word rename costs a town-wide bake. T-0267 moved 14 masters for a
constant lookup; this would move 349 for a name, and it is not worth a bake on its own.

**So it rides with the next town-wide bake**, whatever causes that. Two shapes to choose between,
and the second is the one `materials.md` §8.3 argues for:

1. rename the row `BRICK` and keep `CHIMNEY_BRICK` as an alias, or
2. grow the sheet a selector — `materials.wall_colour(construction=…)` beside the existing
   `wall_substrate` / `wall_finish` — so an archetype ASKS the sheet what colour a bare brick wall
   is rather than naming a row. §8.3: *"Asked the question rather than told the answer, a
   placeholder cannot drift from the archetypes again by pointing at a row that has since moved."*
   `fort_structure`'s `WALL_RGBA` table would then be three archetype-local literals fewer.

**Acceptance:** no surface in the town is painted from a row named for a different surface; the
GLB colours of all three brick masters are UNCHANGED by the rename (this is a naming parcel, not
a palette one, and a moved byte means it was the wrong change); `materials.md` §9.5 closes;
`tools/check.sh` and the smoke green.

**Links:** T-0267 (the convergence) · T-0138 / `materials.md` §8.3 (ask the sheet, do not name the
row) · T-0008 (why there is one brick) · `docs/RESEARCH/materials.md` §9.5.
