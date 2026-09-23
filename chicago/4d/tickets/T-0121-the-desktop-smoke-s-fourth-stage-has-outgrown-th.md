---
id: T-0121
title: The desktop smoke's fourth stage has outgrown the ten-minute command ceiling
state: split
epic: META
requested_by: loop
seen: false
effort: S
legacy_id: null
parent: null
opened: 2026-08-20
closed: 2026-08-23
pr: null
claimed_by: run 8/23/2026, 7:22:17 PM CT
blocked_on: null
needs_bake: false
---

The desktop smoke's fourth stage has outgrown the ten-minute command ceiling.

Measured 2026-08-20 by T-0074's run, three attempts on an idle GitHub Actions runner,
against the published mirror: `SMOKE_VIEWPORT=desktop SMOKE_STAGE=4` was killed at the
600 s command ceiling every time, reaching ~36-47 staged checks (through the navigation
and eye-height sections) with the tail of the stage never run. Every other invocation of
the gate fits: mobile stages 1-4 all complete (stage 4 runs 143 staged checks inside the
ceiling) and desktop stages 1-3 complete. The desktop frame is ~3.4x the mobile pixels
under SwiftShader, and the town has grown since T-0060 sized the quarters the same
morning (the sloughs, the dooryard plantings), so the fit was tight and is now gone.

**Acceptance:** `SMOKE_VIEWPORT=desktop SMOKE_STAGE=4` completes inside 600 s on a
standard runner (re-balance the section quarters, split desktop into more stages, or
make the stage boundary cost-aware — never by dropping a check), with the new fit
measured and written where T-0060's was.

**Re-measured by T-0070, 2026-08-21:** it is not only the fourth stage. On this runner
`SMOKE_VIEWPORT=desktop SMOKE_STAGE=3` and `=4` BOTH ran past the ten-minute foreground
command ceiling and were killed (exit 143), while every mobile stage and desktop stages
1 and 2 finished inside it (desktop 1: 129 checks; desktop 2: 100). So a steward run can
no longer verify the desktop half at all past stage 2, which is half the gate the split
was made to preserve. Whatever the repair is — a further cut, or a cheaper section — it
has to be sized against the desktop body rather than the mobile one.

**Re-measured again by T-0154, 2026-08-23, and it has moved another stage down.** On this
runner `SMOKE_VIEWPORT=desktop SMOKE_STAGE=2` AND `=3` both ran past the ten-minute
foreground ceiling and were killed (exit 143); desktop stage 1 finished in **7 m 47 s**,
which is inside the ceiling by two minutes and no more. Mobile is still comfortable —
stage 1 in **2 m 48 s**, and all four stages complete. So the desktop half a steward run
can actually reach is now stage 1 alone, and stage 1's own margin is the next to go. The
erosion is monotonic across three measurements (T-0070: stages 3-4 lost; this: 2-4), which
says the repair has to be a re-cut of the desktop body rather than one more stage boundary
nudged along.

**Re-measured 2026-08-23 by T-0014 (PR #323), and it is no longer the fourth stage
alone.** On this runner, against the published mirror, `SMOKE_STAGE` at
1280x800: stage 1 finished; **stage 2 overran the ten-minute foreground ceiling
and had to be read back after the fact**; **stages 3 and 4 were both killed at
10:00 (exit 143)** and produced no reading at all. Mobile still fits at every
stage (2m34s for stage 1). So three of the desktop quarters are now outside the
ceiling, not one, and a steward run can currently take only half the desktop
gate in the foreground.
