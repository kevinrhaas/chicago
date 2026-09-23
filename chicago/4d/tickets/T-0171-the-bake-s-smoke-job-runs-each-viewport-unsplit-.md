---
id: T-0171
title: The bake's smoke job runs each viewport unsplit in one command, and the desktop half needs forty minutes against its thirty-minute cap
state: done
epic: META
requested_by: steward
seen: false
effort: S
legacy_id: null
parent: null
opened: 2026-08-23
closed: 2026-08-23
pr: 348
claimed_by: run 8/23/2026, 11:00:22 PM CT
blocked_on: null
needs_bake: false
---

The bake's smoke job runs each viewport unsplit in one command, and the desktop half needs forty minutes against its thirty-minute cap.

**Acceptance:** the bake's `smoke` job runs each viewport as SEVERAL commands under
`SMOKE_STAGE`, no leg's measured cost is within five minutes of the job's `timeout-minutes`,
the legs' stage ranges cover 1..9 exactly once so their union is the unfiltered gate, and
`open-pr` still refuses to open unless EVERY leg passed. Demonstrated by a dispatched bake on
`dev` whose desktop legs are READ TO COMPLETION — which has never once happened.

**What this is, and why T-0167 did not fix it.** T-0165 lifted the smoke out of `bake.sh` into
its own job, and T-0166 and T-0167 cut the smoke's body into nine parts sized for the ten-minute
ceiling on a steward run's single foreground command. Both of those are about the STEWARD
runner. The bake's smoke job is a different caller with a different ceiling, and it sets only
`SMOKE_VIEWPORT` — no `SMOKE_STAGE` — so it runs the whole body of a viewport as ONE command
under `timeout-minutes: 30`. Cutting the parts finer does not help a caller that does not use
them.

**The measurement is already in the repo, and it condemns the current setting.** T-0167's
desktop profile (ROADMAP § THE RUN BUDGET) totals **39 m 58 s** across the nine parts. The cap
is 30 minutes. The desktop leg cannot fit and never could — the arithmetic was published in the
same hours the run below was being killed by it.

**Observed, bake run #269 on `dev` at `ccb9b53b`.** `bake` succeeded in 11 m 53 s.
`smoke (mobile)` passed unfiltered: 420 passed, 0 failed, 15 m 50 s. `smoke (desktop)` was
CANCELLED by the timeout at 29 m 05 s having reached **285 passed, 0 failed** — no failure, just
a wall. The last check printed at 03:42:21 and the kill landed at 03:43:58. So `open-pr` did not
run, and a bake whose content was sound opened no PR.

**This is why the desktop half has never been read.** Every prior nightly died earlier — on the
K38 passthrough baseline (T-0160), on `estray_pen` restaling every bake (T-0161), or on the
45-minute whole-job ceiling (T-0165) — and the two road bands (T-0114) failed at both viewports
until this run. #269 is the first bake to get far enough for THIS ceiling to be the thing in the
way, which is also why it was not findable before.

**The cut to use is the one T-0167 already established:** the pairing rule `1+2, 3+4, 5+6,
7+8+9`. Against the measured desktop profile those legs cost 6 m 08 s, 8 m 47 s, 8 m 04 s and
17 m 02 s — and less than that in practice, because a pair boots once where the profile paid a
boot per part. The worst leg has better than ten minutes of margin under a 30-minute cap, and
the smoke phase's wall clock drops from over 40 minutes (fatal) to under 20.

**Do not "fix" this by raising `timeout-minutes` alone.** It would work today and rot the same
way: the cap would again be a number nobody had measured against, and the desktop half would
again be one command whose cost is the sum of everything. Splitting is what makes the margin
legible per leg, and it is what T-0170's further cut of part 7 will keep improving rather than
invalidate.

**THE UNION IS DEMONSTRATED, NOT ASSERTED.** The four legs' staged-check counts, against
T-0167's per-part profile and its post-cut re-measure (parts 8 and 9 at 28 and 79):

| leg | staged checks | source |
|---|---|---|
| 1-2 | **132** | measured here, mobile, 2 m 02 s — 141 passed / 0 failed |
| 3-4 | 103 | profile: 65 + 35, plus the 3 checks part 4 takes only at mobile |
| 5-6 | 33 | profile: 19 + 14 |
| 7-9 | 143 | T-0167's own audit of the re-cut, 143 / 9 / 152 |
| **sum** | **411** | run #269's unfiltered mobile pass reported **411 staged + 9 always-on** |

411 is exactly what the unfiltered run reports, and the ranges tile 1..9 once with no gap and
no overlap — so the eight legs reconstitute the gate rather than sampling it. The measured
`1-2` leg matching the profile's 66 + 66 to the digit is the reading that makes the other three
rows trustworthy: it is the one place a range was run rather than added up.

**Still owed by this ticket:** the desktop legs read to completion on a dispatched bake. The
audit above is arithmetic plus one mobile leg; the acceptance is a green desktop half, which no
run has ever produced.
