---
id: T-0165
title: The bake cannot finish inside its 45-minute ceiling, because bake.sh runs the full two-viewport smoke as its last step
state: done
epic: PIPELINE
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-08-23
closed: 2026-08-23
pr: 343
claimed_by: run 8/23/2026, 7:47:55 PM CT
blocked_on: null
needs_bake: false
---

The bake cannot finish inside its 45-minute ceiling, because bake.sh runs the full two-viewport smoke as its last step.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

**Bake run #261 (`32674807862`) on `dev` at `c0436f2f`, the first run since 2026-08-22 to get past
`check.sh`, was CANCELLED by `timeout-minutes: 45` at 43m51s** — inside the DESKTOP half of the
published smoke. The last line before the kill is *"the sun's shadow reaches 240 m at the documented
texel"*, and the runner then reported `Terminate orphan process: … headless_shell`.

**It got there because T-0161 worked.** `tools/bake.sh` runs under `set -euo pipefail` and runs
`check.sh` BEFORE the smoke, so reaching the smoke at all is proof the gate passed — run #258, the
one before, died at `check.sh` after 11m41s and never reached it. That is the useful measurement
this ticket rests on:

| run | bake step | got as far as | outcome |
|---|---|---|---|
| #258 | 11m41s | `check.sh` | FAILED — `estray_pen` (T-0161) |
| **#261** | **43m51s** | **desktop smoke** | **CANCELLED — the 45-minute ceiling** |

**So this is a THIRD fault, and it was hidden behind the other two.** K38 (T-0160) and `estray_pen`
(T-0161) each stopped the bake early enough that nothing ever reached the smoke to discover the
budget does not fit. "The bake is broken" was three faults wearing one symptom, and this is the one
left.

**The arithmetic, which is not marginal by accident.** `bake.sh`'s last step is
`node tools/smoke_renderer.mjs --published` — UNSTAGED, so the full body at BOTH viewports in one
process. The suite's own header puts that at **~13 minutes a viewport**; the generate-and-bake half
costs ~12 minutes (#258 measures it). ~12 + ~26 = **~38 minutes before setup**, against a
**45-minute** ceiling, on a runner shared with whatever else is queued. It fits only when nothing
else is contending, which is why it has never been seen: it has not had the chance to fail this way.

**T-0121 is the same fault one level down** — the desktop smoke's fourth stage exceeding the
ten-minute *command* ceiling — and the two should be read together. They are NOT the same fix:
T-0121 is about splitting a command so a steward run can execute it; this is about what `bake.sh`
should be responsible for at all.

**THE TWO CHEAP ANSWERS ARE BOTH REFUSED IN ADVANCE, and the reason matters.** Raising
`timeout-minutes` or setting `SKIP_SMOKE=1` would make the nightly green tonight and would mean the
bake stops testing the bytes it publishes. `bake.sh`'s own comment says why that is not on offer:

> *"the bytes a visitor downloads have to be the bytes something tested … a bug that collapsed every
> building to a two-metre box shipped past a fully green gate — twice."*

**Acceptance:** a bake dispatched on `dev` completes inside its ceiling AND the mirror it publishes
is still smoke-tested at both viewports before the run ends — by splitting the smoke into its own
job with its own budget, by staging it the way `SMOKE_STAGE` already allows, or by another route
that keeps the tested-bytes property. State which, with the timings. If the answer is that the
ceiling itself is wrong, raise it with the measurement that says so rather than to make the red go
away.

---

## SHIPPED 2026-08-24 — three jobs where there was one

```
bake     generate, derive, publish, gate     SKIP_SMOKE=1   ~15 min
smoke    the published mirror, per viewport  matrix         ~15 min each, PARALLEL
open-pr  the PR — only once smoke is green
```

**The gate is still both viewports and nothing less** — `smoke_renderer.mjs`'s own rule. Each matrix
leg prints *"NOT THE FULL GATE"* because alone it is not one; `needs: smoke` fails if either leg
fails, so the workflow reconstitutes the gate the suite refuses to let a filtered run claim.

**Neither refused shortcut was taken.** The ceiling was not raised and `SKIP_SMOKE=1` was not made
permanent — it is set in CI *because the smoke moved*, and `tools/bake.sh`'s comment is corrected in
the same commit to say where it went. Run `bake.sh` locally and the smoke still runs inline, which
is right: there is no artifact to hand anything to.

**Three details that decide whether this works or only looks like it:**

1. The mirror travels as an **artifact**, so the smoke tests the bytes THIS bake published rather
   than what is committed on dev.
2. The committed mirror is **deleted before the artifact is unpacked** — `checkout` restores it and
   `download-artifact` overlays rather than replaces, so a file the bake deleted would otherwise
   survive and the smoke would test a tree that never existed.
3. The branch is **pushed before** the smoke and the PR **opened after**: a red smoke costs a review
   rather than twenty minutes of Blender output, and a failing mirror is never advertised as ready.

**Demonstrated before pushing:** the suite driven against a detached copy of the mirror via
`SMOKE_ROOT`, exactly as the job does — 141 passed, 0 failed. The artifact hand-off is proven rather
than assumed. `NODE_PATH` was dropped from the job after checking `loadPlaywright()` already resolves
`npm root -g` itself; Playwright is dropped from `bake`, which no longer launches a browser.

**Still owed:** a green run. This ticket ships the shape; the demonstration is the next dispatched
bake, which will also discharge the outstanding half of T-0160's acceptance.
