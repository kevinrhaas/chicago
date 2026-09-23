---
id: T-0848
title: Two smoke checks fail only when mobile stages 9-12 run together — the facade-tone and shadow-reach sensitivity deltas collapse in a combined range
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-05
closed: 2026-09-13
pr: 1255
claimed_by: run 9/13/2026, 9:43:43 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-13T15:07:36.565Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34763304736
---

Two smoke checks fail only when mobile stages 9-12 run together — the facade-tone and shadow-reach sensitivity deltas collapse in a combined range.

**Acceptance, stated before working, and met (2026-09-13, PR below):** part 9's two
delta checks pass in a combined range AND alone, with the SAME reading, on an unchanged
town; the cause is named rather than the symptom suppressed; neither threshold moves.

**THE CAUSE.** `streetLayer`, the shared street/flora/anchor reading, is guarded on
`anyStage(7, 10, 11)` and opens by teleporting to a dry South Division stand
(`local_e: 107, local_n: -103, yaw_deg: 180`). It never puts the visitor back. Its guard
asks which parts were SELECTED, not which have run, and it sits ABOVE the staged body —
so it is the one thing in the file that changes what a LATER part photographs according
to what the range asked for. Part 9's facade-tone and shadow-reach deltas capture from
wherever the visitor is standing, so alone they photographed the boot view their floors
were measured at, and in a range they photographed that stand. The comment on the block
claimed "it teleports to its own viewpoints, so it does not care what ran before it" —
true, and beside the point: nothing cared what ran before IT.

Under the 13-part numbering the ticket's `9-12` is any range carrying 9 with 7, 10 or 11;
`9,11` is the cheapest reproducer at 2 m 36 s.

**THE FIX.** The boot pose is read once immediately before the staged body, where nothing
has yet moved the visitor, and each delta section teleports to it and states why
(`standAtBootPose`). The view is part of the assertion now instead of an inheritance.

**MEASURED, all four legs in the foreground on the steward runner:**

| leg | tree | command | facade worst/mean | shadow worst | result |
|---|---|---|---|---|---|
| 1 | pristine `dev` a3c49b288 | mobile `9,11` | **2** / **0.01** | **2** | **FAIL ×2** — the ticket's numbers, reproduced |
| 2 | this branch | mobile `9,11` | 10 / 0.19 | 6 | 36 passed, 0 failed |
| 3 | this branch | mobile `9` alone | 10 / 0.19 | 6 | 23 passed, 0 failed |
| 4 | this branch | desktop `9,11` | 10 / 0.27 | 7 | 36 passed, 0 failed |

Legs 2 and 3 are bit-identical, which is the acceptance: the combined range and the
isolated part now measure the same frame. Floors are untouched at `worst>=3, mean>=0.03`
and `worst>=4`.

Legs 1-4 were measured on `dev` a3c49b288. `dev` then advanced to 7b186cd0a under the
branch, so leg 2 was re-run on the rebased tree — 10 / 0.19 and 6 again, 36 passed, 0
failed, 2 m 26 s — and it is THAT reading that is filed in `tools/dev-smoke-state.json`,
because the record stamps the tree a reading was actually taken on and a reading of a
superseded tree filed under the new hash would be a claim the run did not make.

`check.sh` is green but for one step, "…and the strip still reads the same off the sheet",
which fails identically on pristine `dev` and is not this ticket's.

---

**The report as filed.** `SMOKE_VIEWPORT=mobile SMOKE_STAGE=9-12 node tools/smoke_renderer.mjs --published` fails
two checks, and the SAME two, on a pristine `origin/dev` at b77b1ae14 as on a branch that
touches only resident JSON:

    FAIL  the facade tones reach the render — winding the tone off changed 370
          structure(s) (want >=300) and moved the worst cell by 2, mean 0.01
          (need worst>=3, mean>=0.03)
    FAIL  the shadow reach reaches the render — winding ±120 m back to ±60 m moved
          the worst cell by 2, mean 0.00 (need worst>=4)

Run each of those stages ALONE and every one of them passes — 9 (23/0), 10 (32/0),
11 (22/0), 12 (67/0), 128 staged checks between them and no failure. Only the combined
range fails, and it fails on both trees, so it is not a finding about either.

Both failing checks are DELTA measurements: they wind a knob off, re-render, and assert
that the frame moved by at least so much. What moves that measurement is what the camera
is looking at when it is taken, and a combined range reaches the section with a page that
has already walked through three other stages' worth of interaction. So the likely fault
is that the delta section does not restore the view it measures from, and the assertion
silently becomes an assertion about wherever the previous stage left the camera.

WHY IT MATTERS BEYOND THE NOISE: `tools/smoke_budget.mjs --for-diff` prints combined
ranges, because that is what fits under the foreground ceiling. So the shape the budget
tool tells every run to use is the one shape these two checks cannot survive, and every
run that takes the advice meets a red it did not cause and has to spend its remaining
budget proving whose it is. This one spent three extra legs and a second checkout of dev.

**Acceptance:** the two checks either pass in a combined range or state, in the check
itself, the view they require and take it — and `--for-diff`'s advice stops producing a
red on an unchanged tree. A reading filed with `dev-smoke-state.mjs` (2026-09-06, both
trees) is the evidence.

## Folded in from T-0439 (2026-09-10) — the same parts-9-12 sensitivity collapse; T-0848 carries the per-stage isolation and the filed reading

*T-0439: Two pixel-sensitivity checks fail when parts 9-12 run together and pass when part 9 runs alone*

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
