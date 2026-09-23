---
id: T-0450
title: SMOKE-BUDGET.md compares a per-leg cap with a whole-gate total, and calls one runner a different machine from the other
state: done
epic: PIPELINE
requested_by: owner
seen: true
effort: S
legacy_id: null
parent: null
opened: 2026-08-31
closed: 2026-09-04
pr: 674
claimed_by: run 9/2/2026, 11:56:49 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-04T20:21:32.586Z
claimed_run: null
---

Measured on the branch of **PR #589**, which is being closed as stale (its part
numbers were overtaken by #590's renumbering). The measurement is not stale and
is preserved here; nothing else from that branch is.

`docs/SMOKE-BUDGET.md` opens by telling three tickets their margins are taken
against a cap that is *"not this machine's"*, and offers **55 m 10 s** as the
figure that proves it.

## 1. The two numbers are not the same quantity

- **30 minutes caps ONE LEG** of the nightly gate — one viewport, one range of
  parts, eight legs running in parallel (`chicago-4d-bake.yml` § `smoke`,
  `timeout-minutes`).
- **55 m 10 s is all eight legs' work in a single process** on
  `chicago-4d-smoke.yml`, which has no leg cap at all and a 90-minute job
  timeout.

Neither bounds the other. So T-0170, T-0173 and **T-0181** were reasoning about
the leg cap correctly, and the page tells them they were not.

## 2. It is the same machine

`steward-improve.yml`, `chicago-4d-bake.yml` § `smoke` and `chicago-4d-smoke.yml`
all run the same GPU-less runner with SwiftShader. Same leg, same bytes, `dev` at
`415909cf`:

| runner | wall |
|---|---|
| bake runner — run 33290607360, `Smoke the published mirror` step | **4 m 40 s** |
| improve runner — #589's branch | **4 m 44 s** |

Four seconds apart. The page's central claim is that these are different machines.

## Why this is worth a ticket rather than a shrug

**T-0181 is open and is about the desktop 7-9 leg's margin against the 30-minute
cap.** If the page is wrong, that ticket has been arguing against the wrong bound
the whole time, and **PR #591** — which carries it and currently fails
`smoke (desktop, 10-12)` — may be chasing a budget that was never breached. The
same applies to T-0170 and T-0173, both already merged on reasoning this page
contradicts.

A budget document that misstates its own cap silently mis-ranks every ticket that
cites it.

**Acceptance:**

1. `docs/SMOKE-BUDGET.md` states the per-leg cap and the whole-gate total as two
   separate quantities, each named with the workflow and field it comes from, and
   stops telling T-0170/T-0173/T-0181 they measured the wrong thing.
2. The same-machine finding is recorded with both timings and the runs they came
   from, so it can be re-checked rather than believed.
3. `docs/ROADMAP.md` § THE RUN BUDGET is corrected wherever it repeats the claim.
4. The stale leg table is either re-measured against the current legs
   (`1-2 3-6 7-9 10-12` since #590 made PARTS 12) or dropped with a note saying
   which legs its rows described. A table of readings for legs that no longer
   exist is worse than no table.
5. **T-0181 is re-read against the corrected page** before any further work is
   done on it, and the result is written into that ticket.
