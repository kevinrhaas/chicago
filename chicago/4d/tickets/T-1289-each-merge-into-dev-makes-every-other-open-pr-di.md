---
id: T-1289
title: Each merge into dev makes every other open PR dirty, so N pull requests cost N-squared lap-and-gate rounds
state: done
epic: META
requested_by: owner
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-17
closed: 2026-09-18
pr: 1456
claimed_by: run 9/18/2026, 10:40:09 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-18T17:08:43.319Z
claimed_run: null
---

Every merge into `dev` moves the base, which makes every other open pull request `dirty` —
GitHub reports it conflicting because its server-side merge never runs this repo's merge
drivers (T-0857). So each merge costs a lap over every remaining PR plus a full gate on each
new head, and only then can the next one merge. With N pull requests waiting that is N rounds
of N laps and N gates.

**Measured on 2026-09-17.** Draining six pull requests took four laps and, at two gates per
push (T-1288), roughly forty gate runs of about ten minutes each. Every one of the four
remaining PRs went `dirty` twice in forty minutes purely because other PRs merged, with
nothing wrong in any of them.

Three things would each cut it, and they are independent:

1. **Merge the whole clean set before lapping.** `merge-ready` already loops over the open
   PRs, but each merge it makes invalidates the next one it looks at, so it merges one and
   reports the rest as `needs-a-lap`. If it merged every PR that was `clean` AT THE START of
   its pass — they were all mergeable against the same base — one lap would follow instead of
   one lap per merge. The risk is real and has to be faced: two PRs clean against the same
   base can still conflict with EACH OTHER, so a merge that GitHub refuses must stop the pass
   rather than be forced.
2. **A fast lane for pull requests that change only `chicago/4d/tickets/`.** Those carry no
   scene, no derived layer and no renderer, and today they run the whole 439-step suite —
   #1408 and #1411 both did. A path-filtered gate that runs `ticket.mjs check` and the
   changelog contract alone would turn a ten-minute round into seconds, and this project
   files a lot of tickets.
3. **GitHub's own merge queue**, which is built for exactly this and would replace the
   hand-rolled lap-then-merge cycle. Weigh it honestly against T-0857: the queue builds each
   candidate on the tip, and if its merge still does not run this repo's drivers it buys
   nothing.

**Acceptance:** pick ONE of the three, state why the other two were not taken, and measure
the same drain before and after — number of laps, number of gate runs, wall-clock from first
merge to empty queue. A change here that is not measured is not this ticket, because the


---

## Done — the pool, and why not the three above

**Taken: a fourth option this ticket did not list — the gate runs its steps in
parallel.** The three above all reorder MERGES. None shortens the gate, and the gate's
duration *is* the window in which `dev` can move under an open pull request. Shortening
the window attacks the cause rather than the queueing around it.

### Measured before

`tools/check_harness.sh` now records per-step timings when `CHECK_TIMINGS` names a file.
Nothing in this repo could produce this before, which is why the cost was argued from
impressions:

| | |
| --- | --- |
| gate, uncontended | **775 s (12.9 min)**, 499 timed invocations |
| steps under 1 second | **380 (76 %)** — together under 10 % of the clock |
| slowest 10 steps | 35 % of the clock |
| slowest 20 steps | **50 %** |
| slowest single step | **79.6 s** (`compile_gazetteer.py --self-test`) |

A heavy tail, not a uniformly slow suite. That decided the design: trimming steps cannot
help when three quarters of them are already free.

### Measured after

| | serial | 4 jobs |
| --- | --- | --- |
| wall clock | 775 s | **251 s** |
| verdict | CHECK PASS, 489 steps | CHECK PASS, 489 steps |

**3.1x**, against 3.2x predicted from the distribution. Same verdict, same step count,
same transcript in the same order.

Ordered batching was tried first on paper, because it is far simpler code — each batch
costs its slowest member, and against the real distribution that is **1.4x**. The heavy
tail puts one 79-second step in a batch and idles three workers behind it. So it is a
real work-stealing pool.

### Why the other three were not taken

1. **Merge the whole clean set before lapping.** Reorders merges; the gate is unchanged,
   so each PR is still overtakeable for 13 minutes. Worth doing on its own merits, and
   it does not conflict with this — but it is not the cost.
2. **A fast lane for ticket-only pull requests.** Real, and narrow. Today's pile-ups were
   data PRs of 800-1,300 files; none of them would have taken that lane.
3. **GitHub's merge queue.** T-0857 is the answer and it still holds: GitHub's
   server-side merge does not run this repo's merge drivers, so a branch that merges
   cleanly here is reported conflicting there. The queue would inherit that.

### The drain this was measured against

2026-09-18, four pull requests (#1448, #1449, #1452, #1454): **eleven dev merges**
between them, four of those on #1449 alone, which was overtaken three times while its
gate ran. Every overtake cost a merge, a full re-derivation and another gate.

### What this does not fix, stated

* The 79.6 s self-test is still 79.6 s. Parallelism hides it; it should not need hiding,
  and a self-test that mutates fixtures in memory has no business reading a corpus.
* Output arrives at a barrier rather than step by step, so a parallel run prints little
  until it finishes. Correct, and worse to watch.
* `CHECK_JOBS=1` restores the old path exactly, and is the escape hatch if a step ever
  turns out to share scratch state with another.

### Carried here because each cost a merge round in the same drain

* `ticket.mjs reconcile` restored a base queue line for a ticket **the branch had just
  closed** (#1454, T-1311), and `check` then failed the branch for queueing a closed
  ticket. It now leaves those out and says which.
* `ticket.mjs done` says so when the ticket it closes is the **last open child of a
  split**. That strands every research unit deferring to the parent (T-1237) and fails
  the re-derivation — on the merge, in a tool the closing PR never runs. Three times in
  this drain: #1452 (T-1313 -> nine units on T-1170), #1454 (T-1311 -> seven on T-1180).
