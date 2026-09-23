---
id: T-0346
title: Desktop smoke stage 4 no longer fits the ten-minute foreground ceiling, so no steward run can take the whole desktop gate
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-08-28
closed: 2026-08-29
pr: 583
claimed_by: run 8/29/2026, 9:15:46 PM CT
blocked_on: null
needs_bake: false
---

Desktop smoke stage 4 no longer fits the ten-minute foreground ceiling, so no steward run can take the whole desktop gate.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)
Desktop smoke stage 4 no longer fits the ten-minute foreground ceiling, so no steward run can take the whole desktop gate.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

`tools/smoke_renderer.mjs` documents a staged recipe that exists precisely because a
steward run's single foreground command is capped at ten minutes, and it asserts that
each command in that recipe fits:

    for s in 1 2 3 4 5 6 7 8 9; do SMOKE_VIEWPORT=desktop SMOKE_STAGE=$s node tools/smoke_renderer.mjs --published; done

**Stage 4 no longer fits.** Measured on this branch (T-0314, a data-only change that
touches no geometry), on the GitHub-hosted runner, 2026-08-29:

| desktop stage | wall clock |
|---|---|
| 1 | 4 m 30 s |
| 2 | 4 m 02 s |
| 3 | 2 m 09 s |
| **4** | **killed at 10 m 00 s — never printed its clock** |
| 5 | 8 m 46 s |

Stage 5 at 8 m 46 s is the next one to go, so this is not a one-stage problem.
T-0167 halved part 8 when it was the thinnest margin; the town has grown since and the
margin has moved to parts 4 and 5.

**What it costs:** a steward run cannot take the whole desktop gate any more, so every
PR from the loop has to argue its desktop coverage from the stages that did fit. The
unfiltered single-process pass still runs in `.github/workflows/chicago-4d-smoke.yml`,
which has no ceiling — so the gate is not lost, only the loop's own foreground copy of
it.

**What would fix it:** cut stage 4 in half the way T-0060, T-0121 and T-0167 cut the
ones before it, at a section boundary measured for zero crossing bindings, and re-size
stage 5 at the same time. `SMOKE_TIMING=1` is the instrument — and note the trap the
script's own comment records: a part that BREACHES the ceiling is killed before it
prints its wall clock, so stage 4 has to be profiled under a raised ceiling (or in the
no-ceiling workflow) to find where to cut it.

**A second measurement, 2026-08-29 (T-0373's run — this ticket is where it belongs; the duplicate T-0390 filed against it was folded in here rather than queued twice):**

`tools/smoke_renderer.mjs`'s own docstring records the erosion and predicts it is
monotonic: T-0060 cut the body in four, T-0121 re-cut it in eight when three desktop
quarters ran past the ten-minute ceiling, and T-0167 halved part 8 as the thinnest
margin on the desktop profile. Measured again on 2026-08-29, from a steward run:

    desktop stage 1   4 m 08 s   PASS
    desktop stage 2   3 m 54 s   PASS
    desktop stage 3   2 m 10 s   PASS
    desktop stage 4   > 10 m     killed by the ceiling
    desktop stage 5   8 m 48 s   PASS
    desktop stage 6   1 m 54 s   PASS
    desktop stage 7   > 10 m     killed by the ceiling
    desktop stage 8   > 10 m     killed by the ceiling
    desktop stage 9   4 m 07 s   PASS
    mobile 1-2 4 m 36 s · 3-4 6 m 41 s · 5-6 6 m 44 s · 7-9 8 m 39 s — all PASS

Stage 4 was confirmed to blow the ceiling on an UNMODIFIED `origin/dev` worktree as
well — 46 checks taken in nine minutes, the only failure being the suite's own "the
suite body ran to completion" line, which is the clock and not an assertion. So this
is the erosion the docstring predicted arriving again, not any one branch's doing.

The consequence is what makes it worth a ticket rather than a note: a steward run
cannot take the desktop half of its own gate any more, so every branch merges on a
complete mobile pass plus six of the nine desktop parts and an argument about the
other three. Stage 5 at 8 m 48 s is the next one over.

`.github/workflows/chicago-4d-smoke.yml` has no ceiling and takes the unfiltered pass,
so the gate itself is intact — it is the AGENT-side gate that has gone partial.

**A THIRD measurement, later on 2026-08-29 (T-0373's re-derive run), and it does not
agree with the one above.** Every one of the nine desktop stages fit the ten-minute
ceiling on that runner, taken one invocation per stage against `--published`:

    desktop stage 1   3 m 08 s   PASS
    desktop stage 2   2 m 53 s   PASS
    desktop stage 3   1 m 36 s   PASS
    desktop stage 4   7 m 37 s   PASS   (killed by the ceiling nine hours earlier)
    desktop stage 5   6 m 41 s   PASS
    desktop stage 6   1 m 24 s   PASS
    desktop stage 7   7 m 55 s   1 FAIL (T-0279's flower heads; the clock is fine)
    desktop stage 8   2 m 02 s   PASS   (killed by the ceiling nine hours earlier)
    desktop stage 9   3 m 17 s   PASS
    mobile 1-2 3 m 18 s · 3-4 5 m 03 s · 5-6 5 m 06 s · 7-9 6 m 34 s — all PASS

So the failure this ticket describes is NOT monotonic erosion of the suite, or not only
that: the same tree, the same recipe and the same runner image gave >10 m on stages 4,
7 and 8 in the morning and 7 m 37 s, 7 m 55 s and 2 m 02 s in the evening. Stage 8 moved
by a factor of five. That points at contention on the hosted runner — five slices of
this lane run at once — rather than at the suite's own cost, and it changes what the
acceptance above should measure: a single reading is not evidence about the ceiling
either way, and the worst-case margin has to be taken under load or not claimed.

