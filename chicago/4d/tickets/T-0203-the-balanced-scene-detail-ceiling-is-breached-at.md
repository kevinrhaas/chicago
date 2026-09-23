---
id: T-0203
title: The 'balanced' scene-detail ceiling is breached at Lake and Canal by 4,015 triangles
state: withdrawn
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-08-24
closed: 2026-09-09
pr: null
claimed_by: null
blocked_on: superseded by #765, which raised all three scene-detail ceilings on the owner's ruling; every tier is inside its ceiling on dev (balanced PASS by 81,292)
needs_bake: false
closed_at: 2026-09-10T04:20:10.077Z
claimed_run: null
---

The 'balanced' scene-detail ceiling is breached at Lake and Canal by 4,015 triangles.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

Measured 2026-08-24 on the T-0129 branch, desktop 1280x800, published mirror,
`SMOKE_VIEWPORT=desktop SMOKE_STAGE=4 node tools/smoke_renderer.mjs --published`:

    FAIL  scene detail 'balanced' stays inside its own ceiling at the WORST stand
          1,214,015 tris of 1,210,000 at Lake Street at Canal, east down the axis,
          201 calls of 215 at the same stand
          spread: Lake at Canal 1,214,015/201c · the forks, from Wolf Point
          1,187,507/185c · Lake and Market 1,002,280/151c · the Sauganash at 26 m
          850,247/122c · the open aerial 842,911/123c

Over by 4,015 triangles, or 0.33 %. `full` and `light` both pass at every stand,
and the draw-call ceiling passes with 14 calls to spare.

**WHETHER T-0129 CAUSED IT IS NOT SETTLED, AND THE ARITHMETIC SAYS PROBABLY NOT.**
Everything that branch adds, counted off the committed masters: the crossing's own
mesh is 720 triangles, its plank footway is about 550 (46 boards, no stringers —
they are omitted over a deck), and the terrain went from 249,629 to 250,425, which
is +796. That is about 2,070 triangles in total, and only if every one of them is
in view from a stand 450 m to the west. Subtract all of it and the breach is still
about 1,950 triangles. The reading a run should take before believing that
subtraction is the same command on `origin/dev` — which this run did not have the
budget left to take, and which is the first thing to do here.

**Related and open:** T-0089 (the `light` ceiling breached, and breached before
its run's geometry), T-0146 (merge far chunks back into single draws), T-0147
(re-lower the ceilings once the trims land), T-0170/T-0173/T-0181 (the desktop
smoke's parts against the ten-minute ceiling — parts 3-4 together ran past it on
this runner, and part 4 alone took 9 m 39 s).

**Acceptance:** the same stand reads inside the `balanced` ceiling at 1280x800, or
the ceiling is re-set with the measurement that justifies it and the run that
banked it named.
