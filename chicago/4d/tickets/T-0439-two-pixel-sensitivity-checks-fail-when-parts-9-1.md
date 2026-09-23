---
id: T-0439
title: Two pixel-sensitivity checks fail when parts 9-12 run together and pass when part 9 runs alone
state: withdrawn
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-08-30
closed: 2026-09-09
pr: null
claimed_by: null
blocked_on: folded into T-0848: the same parts-9-12 sensitivity collapse; T-0848 carries the per-stage isolation and the filed reading
needs_bake: false
closed_at: 2026-09-10T04:20:05.218Z
claimed_run: null
---

Two pixel-sensitivity checks fail when parts 9-12 run together and pass when part 9 runs alone.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

Measured on 2026-08-30 on the steward runner, twice on each tree, at mobile 390x780
against the published tree.

| run | `the facade tones reach the render` | `the shadow reach reaches the render` |
|---|---|---|
| `SMOKE_STAGE=9` alone, on unmodified `dev` | pass — winding off moves worst cell **10**, mean 0.12 | pass — winding ±120 m back to ±60 m moves worst cell **22** |
| `SMOKE_STAGE=9` alone, on a feature branch | pass — worst **10**, mean 0.12 | pass — worst **22** |
| `SMOKE_STAGE=9-12`, on unmodified `dev` | **FAIL** — worst **2**, mean 0.01 (needs worst>=3, mean>=0.03) | **FAIL** — worst **2** (needs worst>=4) |
| `SMOKE_STAGE=9-12`, on the same feature branch | **FAIL** — worst **2**, mean 0.01 | **FAIL** — worst **2** |

Both checks are *reaches the render* assertions: they wind a shipped value off, photograph
the frame, and require the picture to MOVE. The sensitivity collapses by a factor of five
to ten when parts 10-12 are also selected, on a tree where nothing about facades or shadows
has changed — so the thing being measured is the run, not the town.

**Why it matters more than a flake.** `tools/smoke_budget.mjs` recommends
`SMOKE_STAGE=9-12` as one of the four mobile commands, because that is how the parts pack
under the ten-minute foreground ceiling. So the packing the tooling tells a run to use is
the packing that fails, and the packing that passes — part 9 on its own — is one nobody is
told to run. A run that follows the advice sees two red checks it did not cause, and the
next run to hit it may well merge past them or park a good branch on `hold`.

**Where to start.** Both checks are inside `if (stageOn(9))`, and part 9 is FIRST in that
range, so this is not stage-ordering: something about which parts are SELECTED changes the
frame before part 9 photographs it. `anyStage(...)` guards are the obvious suspect — a
setup that only runs when a later part is also selected (scene detail level, a renderer
option, a camera stand) would do exactly this. Read every `anyStage` reachable before line
7872 and find the one that fires for 10, 11 or 12.

**Acceptance:** (state it before working — never weakened to pass)

- The cause named, not the symptom suppressed: whatever setup differs is identified, and
  the fix is to make part 9's frame independent of which other parts were selected.
- Both checks pass at `SMOKE_STAGE=9`, `SMOKE_STAGE=9-12` and in a full unfiltered run,
  measured, at mobile and at desktop.
- Neither threshold is lowered to make this pass. The whole worth of a *reaches the render*
  check is that the number is big when the value is doing something.

Related: **T-0235** (what the gate costs and which parts cover a change) · **T-0170**,
**T-0173**, **T-0346** (the part-splitting that created these packings) · found while
gating **T-0379**.
