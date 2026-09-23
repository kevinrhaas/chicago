---
id: T-0236
title: The loop's 10-minute heartbeat fires every one to four hours, and the gaps are widening
state: withdrawn
epic: PIPELINE
requested_by: owner
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-08-27
closed: 2026-09-09
pr: null
claimed_by: null
blocked_on: stale: focus.json runs self-dispatch the next slice within a minute and the cron is a backstop; the lane is at one slice
needs_bake: false
closed_at: 2026-09-10T04:20:11.084Z
claimed_run: null
---

`polecat-platform/.github/workflows/steward-focus.yml` is the loop's heartbeat.
Its cron is `*/10 * * * *` — a tick every ten minutes, and every tick is what
decides whether this app's lane fires a batch. **It is not running every ten
minutes. It is running every one to four hours, and the gap grows through the
day.**

## Measured, from the run list, 2026-08-26 into 2026-08-27 (UTC)

| tick | started | gap to next |
|---|---|---|
| #2168 | 22:00 | 1 h 11 m |
| #2169 | 23:12 | 1 h 16 m |
| #2170 | 00:28 | 1 h 38 m |
| #2171 | 02:07 | 1 h 50 m |
| #2172 | 03:57 | 2 h 14 m |
| #2173 | 06:12 | 3 h 13 m |
| #2174 | 09:25 | 3 h 33 m |
| #2175 | 12:59 | **3 h 47 m** |
| #2177 | 16:46 | — |

Nine consecutive gaps, **every one longer than the last**, against a schedule
that asks for six ticks an hour. The best of them is **seven times** the
interval; the worst is **twenty-three times** it.

(#2176 is absent from that column deliberately: it was a `workflow_dispatch` an
operator threw by hand at 15:17, not a tick. Counting it would understate the
gap it sits inside.)

## Why this is the loop's throughput ceiling, not a cosmetic delay

A lane fires only on a tick where it is **due AND idle**. `everyHours: 1` makes
this app due on essentially every tick, so in practice **the tick IS the
cadence**. A batch that finishes at 12:10 does not start its next one "within
~10 minutes of going idle" as the workflow's own comment promises — it waits for
whenever the next tick happens to land, which on 2026-08-27 meant **12:59, then
16:46**.

Two consequences, both observed today:

1. **A configuration change does not take effect when you make it.** `slices: 3`
   → `5` was committed at 14:35Z. The next tick was at 16:46Z — and it dispatched
   nothing, because the lane was still busy. Over two hours passed between
   changing the dial and the system being in a position to read it. The roster's
   own `_doc` promises "changes take effect on the next tick (~10 min)".
2. **The batch that did run on 2026-08-27 only ran because a human dispatched
   the scheduler by hand.** Runs 1138/1139/1140 — the first parallel batch this
   app ever fired — descend from tick #2176, a manual `workflow_dispatch`. Left
   alone, the loop would have gone from 12:59 to 16:46 having produced one batch.

The workflow already anticipates this in a comment — *"GitHub may delay a
scheduled tick under load, so treat 10 min as the floor, not a guarantee"* — and
that is the right instinct. **A twenty-three-fold miss is not a delay.**

## What is NOT yet known, and must be measured before anything is changed

This ticket deliberately stops at the measurement, because the obvious diagnosis
is a guess:

- GitHub documents that scheduled workflows on busy repositories can be delayed
  or **dropped entirely**, and that the `schedule` event is lowest priority.
  Plausible. **Not established here.**
- The account was demonstrably under heavy Actions load on the days measured —
  the chicago/4d bake was pushing a branch every 10–30 minutes through the
  morning (T-0180), on top of gates, deploys, and up to five concurrent agent
  runs. **Whether that correlates with the widening gaps has not been checked**,
  and it is the first thing to check, because it is testable: the tick history
  and the Actions run history are both readable, and a quiet window is a control.
- **Do NOT conclude "run the cron faster".** Dropping to `*/5` doubles the
  attempts against a mechanism that is already ignoring five out of six of them,
  and if the cause is load it makes the load worse. That would be treating the
  symptom with more of the thing suspected of causing it.

## Candidate answers, in the order they should be considered

1. **Correlate first.** Plot tick gaps against concurrent Actions minutes on the
   account. If they track, the cause is load and the fix is upstream of the cron.
2. **Move the heartbeat off `schedule`.** The tick job is cheap, Claude-free and
   idempotent — it reads a roster and dispatches. It does not have to be a GitHub
   cron. Anything that can fire a `workflow_dispatch` on a reliable interval
   would do, and the reliability is the entire product here.
3. **Make a missed tick visible.** Today nobody could tell "the lane is idle
   because everything is done" from "the lane is idle because nothing has asked
   it in three hours". A tick that recorded its own interval, and a warning when
   that interval exceeds some multiple of the cron, would have surfaced this
   weeks ago rather than on the day someone happened to read the run list.
4. Only then, cadence changes.

## Provenance of this ticket, which is the point of item 3

It was filed on 2026-08-27 **after being claimed in a merged PR body without
being filed at all.** polecat-platform#143 stated the throttling was "filed
against the app repo as T-0232's sibling"; the ledger was searched and no such
ticket existed. That is the identical fault this project recorded against #378
three days earlier — *a commit message is not a filing mechanism* (T-0232) — and
it recurred within hours of being written down, in a PR whose author had just
written it down.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

- The tick interval is **measured over a window that includes both a busy and a
  quiet period**, and the correlation with account Actions load is stated as
  established, refuted, or untested — not assumed.
- A missed or delayed tick is **visible without reading the run list by hand**.
- If the heartbeat moves off `schedule`, the new mechanism is shown to fire on
  its stated interval across at least a day, **including a busy one** — a green
  hour proves nothing about the hour that broke it.
- **The cron is not simply set faster** as the fix. If a cadence change is part
  of the answer, it comes after item 1 and with the load question answered.

**Links:** T-0232 (the promotion's checkout lottery — the other pipeline defect
that only shows under load, and the ticket whose lesson this one repeats) ·
T-0234 (the API budget, the third) · T-0180 (the bake's every-run branch, a
candidate load source) · polecat-platform `.github/workflows/steward-focus.yml`
and `.github/steward/focus.json`.
