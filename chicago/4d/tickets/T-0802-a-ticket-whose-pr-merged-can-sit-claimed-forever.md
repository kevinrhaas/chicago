---
id: T-0802
title: A ticket whose PR merged can sit 'claimed' forever, because nothing compares ticket state against the PRs that landed
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-05
closed: 2026-09-13
pr: 1253
claimed_by: run 9/13/2026, 8:55:08 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-13T14:38:31.942Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34761019240
---

A ticket whose PR merged can sit `claimed` forever, because nothing compares ticket state
against the PRs that landed.

**The instance.** T-0429 shipped in PR #597, merged to `dev` 2026-09-01T00:40:50Z. The run
died before `ticket.mjs done`, so the ticket stayed `claimed` and stayed in
`list --workable`. Five days later it was still the topmost ticket in the queue carrying no
PR, which is exactly the shape of available work. One branch
(`steward/t-0429-south-water-lasalle`) rebuilt the whole block on the strength of that
reading — 116 files, 5,827 insertions, baked — and every record it produced already existed
on `dev` under the same id.

**Why the existing guards do not catch it.** `inflight` is the guard for this class, and it
is honest about its own blind spot: everything here squash-merges, so a merged branch never
becomes an ancestor of `dev` and `inflight` deliberately refuses to claim a branch landed. It
sorts on branch AGE instead, so T-0429's branch showed as *cold* — correctly — and cold reads
as litter, not as done. `ticket.mjs check` polices sizing and queue membership, not staleness.
Nobody is wrong; there is simply no check that asks the one question that settles it.

**The question that settles it, and it is cheap.** For each ticket not in a terminal state,
does a MERGED PR exist whose title carries its id? That is one REST call
(`/repos/kevinrhaas/custom/pulls?state=closed`), it is the same evidence a human uses, and it
is decisive in the direction that matters: a merged PR naming T-NNNN is strong evidence the
work landed, while its absence proves nothing and should stay silent. Report, never fail —
the id in a title is a convention, not a contract, and a gate that hard-fails on a naming
convention will block a run that did nothing wrong.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

- A tool (`ticket.mjs` subcommand, or a check next to `inflight`) reports every non-terminal
  ticket for which a merged PR names its id, with the PR number and merge instant.
- Run against today's `dev` it reports **zero** — T-0429 was the only one, and this ticket's
  own PR closes it. The demonstration is therefore against a constructed case, not a live
  one: feed it a ticket id known to be `done` and show it would have fired.
- It REPORTS. It does not fail `check.sh`, and it says in its own output why not.
- No network, or a rate-limited call, degrades to silence — never to a false accusation.
  `inflight`'s best-effort construction is the precedent to follow.

**Links:** T-0429 · `tools/ticket.mjs` § `inflight` · `tickets/README.md` § *A claim is only
real once its PR merges*, which names this exact failure and costs it at ~70 minutes of loop
time per recurrence.

---

**Closed by PR #1253, and the acceptance's own "reports zero" clause did not survive
contact.** This ticket was written on 2026-09-05 predicting one instance — T-0429 — and
asking the check to report nothing against `dev`. On its first live run, 2026-09-13, it
reported four, and two of them are this exact fault standing right now:

| ticket | state on `dev` | the merged PR naming it |
|---|---|---|
| **T-0995** | `open`, `pr: null` | #1064, merged 2026-09-10T10:33:18Z |
| **T-1025** | `open`, `pr: null` | #1109, merged 2026-09-11T06:46:39Z |
| T-0987 | `claimed` | #1116 — multi-stretch by design; reported and correctly caveated |
| T-0520 | `open` in this PR's base | #1251, merged by a sibling slice mid-run |

T-0995 and T-1025 are records already on `dev` sitting in the queue as available work.
They are deliberately NOT closed here — closing somebody else's ticket is a second unit,
and a PR must stay one revertible thing — but they are the live evidence the check works,
and the next run that reads `ticket.mjs landed` will find them named with the exact `done`
command. Filed against this ticket rather than as new tickets, per the FILING RULE.

**What was found while building it**, both of which would have made the check lie:

1. `spawnSync`'s default 1 MB `maxBuffer` truncates a page of a hundred pull requests into
   an ENOBUFS, which arrives at the caller indistinguishable from "no network" — so the
   very first live run reported a confident false all-clear. `maxBuffer` is explicit now.
2. Matching an id anywhere in the title's first clause accused three real merged PRs that
   had touched none of the work they named — "Rank T-0727 under the drain band", "Pull
   T-0802 up into the blocking band", "File T-0968: a green deploy is not proof the site is
   reachable". The id must START the title, which is what the convention actually reserves.
