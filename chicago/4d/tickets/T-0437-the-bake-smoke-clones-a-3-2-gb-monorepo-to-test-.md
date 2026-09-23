---
id: T-0437
title: The bake smoke clones a 3.2 GB monorepo to test one subtree, and that checkout has killed seven legs at the cap
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-08-29
closed: 2026-09-17
pr: 1407
claimed_by: run 9/17/2026, 11:54:46 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-17T18:03:20.953Z
claimed_run: null
---

The bake smoke clones a 3.2 GB monorepo to test one subtree, and that checkout has killed seven legs at the cap.

**Filed by T-0181, which measured it while sizing the smoke job's cap.**

## The measurement

`chicago-4d-bake.yml`'s `smoke` job runs eight legs, each of which does a full
`actions/checkout@v4` of `kevinrhaas/custom`. Read from the Actions API across bake runs
**#271-#391**, the desktop tail leg's checkout step:

| n | min | median | p75 | p90 | max |
|---|---|---|---|---|---|
| 104 | 0 m 31 s | **0 m 38 s** | 0 m 47 s | 5 m 31 s | **30 m 01 s** |

**11 of 104 exceeded five minutes; 7 exceeded thirteen.** The distribution is bimodal and the
upper mode is where the nightly dies.

## What it costs

Seven tail legs have been killed by the job's `timeout-minutes` — runs **#284, #288, #290,
#357, #358, #360, #364** — and in every one the checkout was between 13 m 20 s and 30 m 01 s
while the smoke command itself was inside its normal range or had not started at all:

| run | job total | checkout | smoke |
|---|---|---|---|
| #364 | 30 m 16 s | 13 m 20 s | 16 m 23 s |
| #360 | 30 m 15 s | 21 m 38 s | 8 m 08 s |
| #358 | 30 m 15 s | 15 m 20 s | 14 m 23 s |
| #357 | 30 m 14 s | 21 m 19 s | 8 m 26 s |
| #290 | 30 m 16 s | 23 m 23 s | 6 m 21 s |
| #288 | 30 m 20 s | 29 m 17 s | 0 m 33 s |
| #284 | 30 m 07 s | **30 m 01 s** | 0 m 00 s |

A killed leg fails the `smoke` job, so `open-pr` never runs and a bake whose content was sound
opens nothing. Note that GitHub reports a `timeout-minutes` kill as `cancelled`, not `failure` —
which is why these seven were invisible to every scan that looked for failures.

T-0181 raised the cap to 45 minutes, which absorbs five of the seven. **It cannot absorb #284 or
#288 and no cap can**: a 30-minute checkout exceeds any budget this job could reasonably carry.

## Why it is slow

`custom` is a monorepo of unrelated personal projects. Working tree ~3.2 GB, `.git` ~1.5 GB:

    garage/                968M
    ordovician-sandstone/  571M
    chicago/               532M   (chicago/4d is 182M of it)
    joliet/                354M
    site/                  185M
    …

The smoke job needs exactly two things: `chicago/4d/tools/` and its imports (it runs
`node tools/smoke_renderer.mjs --published` with `working-directory: chicago/4d`), and the
published mirror — **which it does not take from the checkout at all**. The job explicitly does
`rm -rf site/chicago/4d && mkdir -p site/chicago/4d` and then downloads the mirror as an artifact,
precisely so it tests the bytes the bake published. So the ~3 GB outside `chicago/4d` is fetched
and then never read, eight times per bake, twice per viewport.

The upper mode looks like contention rather than a step change: #357/#358/#360/#364 all fall in
one two-hour window on 2026-08-28 during which roughly twenty bake runs were in flight, each
spawning eight of these clones.

## The fix, roughly — and it must be MEASURED, not assumed

The obvious candidate is a sparse, blob-filtered checkout on the `smoke` job:

    - uses: actions/checkout@v4
      with:
        ref: ${{ needs.bake.outputs.sha }}
        sparse-checkout: chicago/4d
        filter: blob:none

**Do not ship this on the reasoning alone.** Two things need checking against the real thing:

1. That `smoke_renderer.mjs` and everything it imports resolve under a cone containing only
   `chicago/4d` plus the repository root files. If it reaches anywhere else in the monorepo, the
   cone has to say so.
2. That the checkout's upper mode actually collapses. The median is already 38 s, so a green run
   proves nothing — the quantity of interest is the tail, and it needs several bakes before and
   after. The p90 (5 m 31 s) and the count over thirteen minutes are the numbers to compare.

The same checkout runs in all eight legs, so whatever is done here applies to every one.

**Acceptance**

- The `smoke` job's checkout is reduced to what the job actually reads, and the PR names what it
  verified about the import graph rather than asserting it.
- The checkout's spread is re-measured from the job history over at least five bakes after the
  change and recorded beside T-0181's table in ROADMAP § THE RUN BUDGET, with the count over five
  and thirteen minutes given both before and after.
- If the tail collapses, the 45-minute cap is re-sized on the new spread in the same way T-0181
  sized it — and the reasoning is written next to the number, not in the commit message.

## Implementation and verification — 2026-09-17

Owner selected this ticket and authorized its workflow PR and merge into `dev`.
Remote lock: `claim/t-0437`; work branch: `steward/t-0437-sparse-bake-smoke`.
The normal claim tool recorded the claim locally; the connector acquired the
remote marker after the tool reported unavailable push credentials.

Smoke checkout now uses exact non-cone patterns for `tools/` and
`docs/SITE-BUDGET.md`, with `blob:none` and depth 1 at the bake output SHA.
ROADMAP § THE RUN BUDGET records the dependency audit and file-size comparison.
Five bakes (#611, #613–#616) supplied all 40 checkout readings: **1–5 s,
p90 4 s, zero over 5 or 13 minutes**. Desktop-tail p90 is 4 s (n=5),
versus historical 331 s (n=104, 11 over 5 minutes, 7 over 13). The completed sample corrects the provisional 30-minute cap to **40 minutes**:
the latest successful body is **32 m 10 s**, and maximum successful-job
overhead is **51 s**, leaving **6 m 59 s / 21.2%** headroom. All 40 checkout
steps succeeded; final body outcomes are 27 passed, 8 inherited triangle-budget
failures, and 5 superseded/cancelled. ROADMAP and
`docs/measurements/T-0437-checkouts.json` retain the completed timestamps,
failed pre-smoke attempt #612, and why the partial-snapshot cap was refuted.
The target `dev` already carries T-1245's renderer-budget fix.

Local sparse-tree stage 9 + always-on smoke: **46 passed, 0 failed**, both
viewports, zero page errors; boot: **7.270 MB / 12 MB**. A fresh filtered fetch
materialized exactly 423 files in 30.423 s. Neither is the required CI tail sample.
