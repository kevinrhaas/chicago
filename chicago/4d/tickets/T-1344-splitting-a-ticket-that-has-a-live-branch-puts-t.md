---
id: T-1344
title: Splitting a ticket that has a live branch puts two runs on one acceptance: the in-flight run retargets onto a child while the child also enters the queue for a fresh claim, and neither claim contends with the other
state: open
epic: META
requested_by: steward
seen: false
effort: S
legacy_id: null
parent: null
opened: 2026-09-18
closed: null
pr: null
claimed_by: null
blocked_on: null
needs_bake: false
closed_at: null
claimed_run: null
---

Splitting a ticket that has a live branch puts two runs on one acceptance: the in-flight run retargets onto a child while the child also enters the queue for a fresh claim, and neither claim contends with the other.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

1. `ticket.mjs split` REFUSES, or warns loudly and requires a `--anyway --why`, when the
   parent has a live claim or an open PR. Measured on the real case: T-1144 held
   `claim/t-1144` and an open PR (#1469's branch) at the moment it was split.
2. A child minted from a parent with a live branch carries, in its own front matter or its
   body, which branch was already working the parent — so the next run to claim it can see
   it is walking into somebody's work rather than finding out at merge time.
3. The refusal fires in the self-test, on a fixture with a claimed parent AND on one with an
   open PR, because those are two different signals and only one of them is local.
4. No existing split is rewritten to satisfy this. T-1144's children are already out and
   #1477/#1480 are already resolved; this is about the next one.

## WHAT HAPPENED, 2026-09-18

T-1144 was split into T-1333 and T-1334 (#1471) while `steward/t-1144-closing-convergence`
was IN FLIGHT on T-1144 — the same branch that had just closed acceptance 6's redirect leg
in #1469. Two things then happened at once:

  * that run retargeted its work onto **T-1333** and opened #1477
  * **T-1333** also entered the queue, a fresh run claimed it, and opened #1480

Both implement the same acceptance, independently: #1477 adds
`tools/report_convergence_closing.py`, #1480 adds `tools/rebuild_closing_set.py`, and five
files overlap including check.sh and derived_manifest.json. #1477 was closed as the
duplicate; roughly a run's work was spent twice.

**THE CLAIM LOCK COULD NOT HAVE STOPPED IT.** The lock is per ticket id, and the in-flight
run held `claim/t-1144`. The second run claimed `claim/t-1333` — a different id, no
contention, both correct by the rules as written. The lock is doing exactly what it was
built for (T-1287's compare-and-swap on the remote) and is not the gap.

The gap is that a SPLIT creates new ids that nobody holds, out of a parent somebody does.
That is invisible to every check in the system: the parent's claim stays valid, the
children's are free, and the queue offers the children immediately.

**AND IT IS THE SPLITTER'S TO SEE.** `ticket.mjs split` runs in the tree that holds the
claim markers and can ask the remote for `claim/t-<parent>` with the same `git ls-remote`
the claim path already uses, so the check costs one network call at the only moment it
matters.
