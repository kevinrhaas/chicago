---
id: T-0852
title: tools/ticket.mjs inflight has a three-hour cold window, so a run that claims and then reads for four hours is invisible to the next run
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-05
closed: 2026-09-13
pr: 1259
claimed_by: run 9/13/2026, 11:57:25 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-13T17:19:28.894Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34769893923
---

tools/ticket.mjs inflight has a three-hour cold window, so a run that claims and then reads for four hours is invisible to the next run.

**Acceptance, stated 2026-09-13 before the work:** `inflight` gives every branch one of
three readings rather than two. A branch older than the window whose ticket's CLAIM LOCK
still stands on the remote is reported IN FLIGHT with its age — not filed under a heading
that calls it finished or litter. The cold list keeps exactly its present meaning for
everything else, and in particular a `claimed` ticket with no standing lock stays cold, so
T-0429's fault (a run that died after its merge) and T-0987's shape (claimed on `dev`
permanently by design, seven merged branches behind it) are both still read correctly. A
self-test covers a claim older than the window, and holds BOTH wrong answers: age alone
must fail the fault, the ticket file alone must fail T-0987. The tool stays offline — no
PR lookup, and an unreadable remote degrades to silence.

**The measurement.** Cohort 14 (T-0509) was read twice on 2026-09-05 by two runs that could not see
each other; the two ledgers disagreed on 36 of the 76 people and T-0816 had to rule every one of
them. The second run filed this defect itself and the filing died with its branch.

**The mechanism.** `inflight` reports a branch as in flight only if it was pushed within the last
three hours, and files everything older under "Cold — finished tickets, or branches older than a
run". A run that claims, pushes its claim commit, and then reads sources for four hours drops out
of the hot list at exactly the moment duplicating it is most expensive. The heading is also
literally wrong for that branch: it is neither finished nor litter.

**Acceptance:** a branch whose ticket is still `claimed` is reported as in flight however long ago
it was pushed, with its age shown, and the cold list keeps its current meaning for everything else.
A self-test covers a claim older than the window. The tool stays offline — no PR lookup.

**Links:** T-0816 (the reconciliation this cost) · T-0509 · `chicago/4d/tools/ticket.mjs` § inflight.
