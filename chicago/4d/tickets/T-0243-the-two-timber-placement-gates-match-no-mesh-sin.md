---
id: T-0243
title: The two timber-placement gates match no mesh since the lattice landed, and one of them is now red on dev
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-08-27
closed: 2026-08-29
pr: 519
claimed_by: run 8/29/2026, 3:05:27 AM CT
blocked_on: null
needs_bake: false
---

The two timber-placement gates in `tools/smoke_renderer.mjs` stage 7 match no mesh since
T-0223's lattice landed. One of them is RED on `dev` today; the other passes vacuously,
which is worse.

## What was measured, 2026-08-27

`SMOKE_VIEWPORT=mobile SMOKE_STAGE=7 node tools/smoke_renderer.mjs --published`, run in a
clean `origin/dev` worktree at `2501f3da` on the steward runner:

    44 passed, 1 failed
     - mobile 390x780: every tree drawn stands at its own station

Re-run on an unrelated branch (T-0147, which changes one triangle constant and one gate
assertion) it fails identically — so it is `dev`'s, not any branch's. `dev`'s standing
record still reads PASS for mobile stage 7-9, taken at `2026-08-27T20:16` — **five minutes
before T-0223 merged**, which is exactly the window the record is honest about not covering.

## The cause, and it is not the trees

`tools/smoke_renderer.mjs` traverses for `if (!o.isMesh || !/^timber__/.test(o.name)) return;`
and counts vertices further than 24 m from a station. T-0223 replaced the four quadrant
meshes `timber__q0…q3` with a single `THREE.BatchedMesh` named **`timber`** — no
double underscore, no quadrant suffix — in `renderers/web/js/trees.js`. The regex now
matches **nothing**, so `drawnWood.meshes` is 0 and the check fails on its own
`meshes > 0` liveness clause. **No tree moved.**

## The half that is worse than the red one

The sibling check two lines down — `no timber is drawn out in the channel` — asserts
`drawnWood.offshore === 0`, and zero meshes traversed gives zero offshore vertices. It is
**passing on an empty traversal**: a green tick that has asserted nothing about the timber
since the lattice merged. The red one at least announced itself.

## What the fix has to deal with, so it is not sized as a rename

Pointing the regex at `timber` is not enough and would be the wrong repair. A
`BatchedMesh` holds every chunk in one pair of buffers with a per-instance transform the
batch owns, so `o.geometry.getAttribute('position')` read through `o.matrixWorld` no longer
gives a chunk's world position: the walk has to go through the batch's geometry ranges and
`getMatrixAt` per instance. The liveness clauses (`meshes > 0`, `verts > 1000`) are what
caught this and must survive the repair — a gate that can pass on an empty traversal is
the defect here, not an implementation detail.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

Both checks read the batched timber's real world positions, at both release viewports;
`stray` and `offshore` are asserted against a non-zero vertex count that the check itself
proves it walked; and the repair is demonstrated to CATCH a deliberately displaced chunk,
not merely to go green. Never weaken the 24 m or 12 m bars to make the red go away — the
bars were argued in T-0110's box and the crowns have not changed.

**Links:** T-0223 (the lattice, `renderers/web/js/trees.js` § the `BatchedMesh`) ·
T-0216 (`tools/dev-smoke-state.json`, whose PASS predates the merge) ·
`tools/smoke_renderer.mjs` stage 7, the `timber__` traversal.
