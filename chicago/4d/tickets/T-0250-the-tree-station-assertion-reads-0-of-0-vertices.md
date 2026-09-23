---
id: T-0250
title: The tree-station assertion reads 0 of 0 vertices across 0 merged meshes, so it fails by finding nothing to check
state: withdrawn
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-08-27
closed: 2026-08-27
pr: null
claimed_by: null
blocked_on: Duplicate of T-0243, which covers both timber-placement gates that stopped matching a mesh when T-0223's lattice landed. Same finding — a check that examines 0 of 0 vertices and calls it a failure — and T-0243 states it for both gates rather than one. Withdrawn on the merge that discovered the collision.
needs_bake: false
---

The tree-station assertion reads 0 of 0 vertices across 0 merged meshes, so it fails by finding nothing to check.

Measured 2026-08-27 on clean `origin/dev` @ `2ab3065a`, while gating T-0183. It fails at
BOTH viewports — desktop part 7 and mobile part 7-9:

    FAIL  every tree drawn stands at its own station — 0 of 0 vertices further than
          24 m from any of 910 stations across 0 merged meshes; worst 0 m

Read the numbers rather than the verdict. The check found **910 stations** — the tree
census is fine — and **0 merged meshes**, so it examined **0 vertices** and its worst
reading is **0 m**. Nothing is wrong with the trees. The assertion looks for the thing
T-0223 removed: the near timber used to be four merged quadrant meshes, and T-0223 rebuilt
it as one `THREE.BatchedMesh` over a 120 m lattice so the sun's camera could cull it. There
are no merged meshes left to walk, so the check finds nothing and calls that a failure.

That is the worst shape a gate can take — **red because it has stopped looking**, not
because it has found something. It is also cheap to mistake for a real one, which is what
this ticket exists to stop.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

The check reads the `BatchedMesh` lattice and asserts the same property it was written to
assert — every drawn tree vertex within 24 m of a committed station — with a **positive
control** that fires when a vertex is moved off its station, so the pass is a pass and not
an empty walk. A check that examines zero vertices must FAIL LOUDLY with that as the
reason, at every viewport, rather than reporting a worst reading of 0 m. Deleting the
assertion is not an answer.

**Links:** T-0223 (the lattice that replaced the quadrant meshes) · T-0250 was found by
T-0183's gate run · `tools/smoke_renderer.mjs` · `renderers/web/js/trees.js`.
