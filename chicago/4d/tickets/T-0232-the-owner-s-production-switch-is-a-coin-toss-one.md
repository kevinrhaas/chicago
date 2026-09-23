---
id: T-0232
title: The owner's production switch is a coin toss: one promotion in four never reaches a promotion step
state: done
epic: PIPELINE
requested_by: steward
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-08-27
closed: 2026-09-16
pr: 1372
claimed_by: run 9/16/2026, 11:38:24 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-17T01:49:33.685Z
claimed_run: null
---

`chicago-4d-promote-to-prod.yml` is dispatch-only — it is the owner's switch and
nothing else throws it. Twice now it has been thrown and **nothing moved**, both
times because `actions/checkout@v4` was still cloning when the job ran out of
time. The run reads "in progress" and then "cancelled", which is the worst way
for a switch to fail: it looks like it is working right up until it isn't.

## The record, with the hotfix in the middle of it

| run | date | outcome | notes |
|---|---|---|---|
| #12 | 08-24 19:04 | **cancelled** | checkout 14m59s, hit the 15-min cap; steps 3–9 `skipped`. Nothing moved. |
| — | 08-24 | **hotfix #378** | `filter: blob:none`, dropped `setup-python` + `pip install`, cap 15 → 30. |
| #13 | 08-24 19:24 | success | 1m42s total |
| #14 | 08-27 04:23 | success | 50s total |
| #15 | 08-27 13:43 | **cancelled** | **≥18m28s, all of it in checkout.** Steps 3–7 never started. Nothing moved. |
| #16 | 08-27 14:04 | success | **57s total — checkout 35 s** |

**Post-hotfix that is one bad draw in four.** #378 improved the odds and did not
remove the coin toss, which is the thing that needed measuring and is now
measured.

**Runs #15 and #16 are the whole argument.** Same repository, same `ref: main`,
same workflow file, same `blob:none`, dispatched **twenty minutes apart**:
**more than eighteen minutes** against **thirty-five seconds**. Whatever the
variance is, it is not in this repo's size and it is not in this workflow's
configuration, because neither changed between those two runs.

**One honest caveat on #15**: it was cancelled by an operator at 18m28s, about
eleven minutes short of its 30-minute cap. **18m28s is a lower bound, not a
duration** — nobody knows whether it would have finished at 19 minutes or never.
It is recorded that way deliberately; #12 is the only bad draw whose full cost
was actually observed.

## Why the cap is not the fix

#378 raised the cap 15 → 30 and #15 still died. A cap only decides *how long the
switch is inert before someone notices*. The failure is that a single slow clone
can consume the entire job, and every promotion step lives downstream of it — so
the cost of one bad draw is the whole promotion, not the clone.

The job needs the full commit history (`rev-list main..origin/dev`, `merge-base`,
two real merges), so `fetch-depth: 0` has to stay; `blob:none` already removed
the blobs. There is not much left to trim inside `actions/checkout`. **The lever
is not making the clone reliably fast — it is making a slow clone cheap.**

## The plan, in order of value

1. **Bound the clone and re-roll, instead of letting it eat the job.** A
   per-attempt timeout with a retry turns a bad draw from "the promotion is dead
   and the owner must notice and re-dispatch" into "attempt 1 gave up at 4
   minutes, attempt 2 took 35 seconds." On the numbers above a 4-minute bound
   would have cost #15 four minutes instead of eighteen-plus, and would not have
   touched #13, #14 or #16 at all.
   `actions/checkout` has no retry of its own and `timeout-minutes` on a step
   fails the job rather than retrying it, so this wants either a `run:` block
   doing `git clone --filter=blob:none` under `timeout(1)` in a loop, or an
   equivalent. **Plain git, no new action dependency** — the fleet is
   static-first and a third-party retry action is a dependency this does not
   need.
2. **Instrument it, so the distribution stops being reconstructed from
   timestamps.** Every figure in the table above was derived by subtracting
   `created_at` from `updated_at` after the fact, which is how a cancelled run's
   duration got misread once already today. Write the clone's own elapsed time
   into `$GITHUB_STEP_SUMMARY`. Cheap, and it makes the next argument about this
   a reading rather than an inference.
3. **The same lottery runs in `bake.yml` and `deploy.yml`, and nobody has looked.**
   #378 measured eight jobs of ONE bake run on the same commit and the same
   minute — **37s, 47s, 54s, 2m20s, 3m32s, 3m40s, 4m45s, 7m11s**, and a ninth
   still cloning when it was cancelled at 30 minutes. Those two workflows have
   neither `blob:none` nor a bounded clone. The bake is the one that matters:
   T-0165 already records it failing to fit its ceiling.
4. **The pack itself, which is the root cause and the largest job.** 1.31 GiB
   over 18,481 objects, overwhelmingly superseded GLB masters that the nightly
   bake rewrites ~287 of and that no job ever opens again. This is a real piece
   of work with its own risks (history rewriting, LFS, or a different home for
   the masters) and it should not be started casually — but every item above is
   mitigation, and this is the only one that is a cure. **Scope it before
   attempting it; do not let it hide inside a run aimed at item 1.**

## A second finding, which is not about clones

#378's commit message on `main` ends:

> The follow-up — measuring whether blob:none actually moves the number, the
> same lottery in bake.yml and deploy.yml, and whether the pack itself should be
> dealt with — is filed separately on dev, where the ticket ledger is current.

**No such ticket exists.** The ledger was searched for `blob:none`, `GiB`,
`clone`, `checkout`, `pack` and `partial clone` across every ticket file, the
board and `tickets.json`: nothing. **This ticket is that follow-up, filed three
days late**, and the gap is why the same failure was met a second time with no
record of the first analysis to read.

That is the same shape as T-0231 and T-0207: **a claim written down confidently,
by the same run that had the evidence, which nobody afterwards checked against
the artefact it named.** A commit message is not a filing mechanism. If a commit
says work is filed elsewhere, either the id goes in the sentence or the sentence
is a promise with nothing behind it.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

- A promotion whose clone draws the bad ticket **costs minutes and then
  succeeds**, rather than consuming the job. Demonstrated, not asserted: show a
  run where an attempt timed out and a later attempt completed, or show the
  mechanism failing deliberately against an injected delay. **A green run on a
  fast draw proves nothing** — a fast draw was always green.
- The clone's elapsed time appears in the run summary for every promotion.
- `bake.yml` and `deploy.yml` are either given the same treatment or explicitly
  ruled out **in writing, with a reason** — not left unmentioned.
- Item 4 is scoped in this ticket or split out with its risks named. It does not
  close by silently dropping the only item that is a cure.

**Links:** #378 (the hotfix, and the commit message whose promised follow-up
this is) · run #12 · run #15 · T-0165 (the bake cannot finish inside its
ceiling) · T-0231 and T-0207 (a written claim nobody checked against the thing
it named).
