---
id: T-0815
title: Close the five PRs dev has outrun or superseded, and put their tickets back in play
state: done
epic: META
requested_by: owner
seen: false
effort: S
legacy_id: null
parent: null
opened: 2026-09-05
closed: 2026-09-05
pr: 900
claimed_by: null
blocked_on: null
needs_bake: false
closed_at: 2026-09-05T17:01:48.902Z
claimed_run: null
---

Five of the twenty-one PRs open against `dev` cannot be merged and should not be
rebuilt from where they stand. Close them, delete their branches, and leave their
tickets `open` in the queue for a run on today's tree. **Owner's call, 2026-09-05:
"close them, re-queue the tickets."**

| PR | ticket | behind dev | files | why it closes |
|---|---|---|---|---|
| [#799](https://github.com/kevinrhaas/custom/pull/799) | T-0676 | 79 | 36 | **Superseded.** T-0676 is `done` on dev at PR [#816](https://github.com/kevinrhaas/custom/pull/816) (`af5c5e27`). Dev's copies of `read_land_sales.py`, `harvest_land_sales.py` and `land_sales/coverage.json` are all AHEAD of the branch. |
| [#432](https://github.com/kevinrhaas/custom/pull/432) | T-0219 | 672 | 54 | Opened 2026-08-28. Re-traces the river and rebuilds the heightfield + terrain/water GLBs. |
| [#562](https://github.com/kevinrhaas/custom/pull/562) | T-0385 | 559 | 55 | Opened 2026-08-29. A bake, plus every derived layer a new roof moves. |
| [#599](https://github.com/kevinrhaas/custom/pull/599) | T-0432 | 515 | 73 | Opened 2026-08-30. Also parked on T-0441, a triangle-ceiling question that never reached dev. |
| [#601](https://github.com/kevinrhaas/custom/pull/601) | T-0431 | 541 | 73 | Opened 2026-08-30. A bake plus a lot-accounting correction. |

**Nothing is lost, and that is measured, not assumed.** All four of T-0219, T-0385,
T-0432 and T-0431 read `state: open, pr: null` on `dev` today — the claims never
landed, so the tickets are already back in the workable set and already in QUEUE.md.
Closing the PR closes nothing else.

**Why not merge them.** Each is 515–672 commits behind a `dev` that has since moved
the South Branch's east bank (T-0686, #882), re-derived north_water twice (T-0780,
#889), rebuilt the identity master and the Newberry rulings, and changed the street-face
adoption. Every one of these four regenerates baked geometry or derived layers ON TOP of
that older ground. A merge lap is not a conflict resolution here; it is the whole parcel
re-run against inputs that have all moved — which is what the ticket asks for anyway,
minus 600 commits of drift to reconcile first.

**What the closing comment must say**, on each PR, so the argument is not thrown away:
the PR body is the reasoning archive for its ticket, the ticket is open and queued, and
the branch is deleted. For #799, name #816 as the thing that landed instead. Link the
PR from its ticket body under a `Prior attempt:` line so the next run reads the argument
before redoing the work — #599 in particular carries the T-0441 triangle-ceiling
measurement (dev had 1,566 triangles of `balanced` headroom and four roofs cost 2,174),
which is a real finding whoever takes T-0432 next needs.

**Acceptance:** PRs #799, #432, #562, #599 and #601 are CLOSED with a comment stating
why. T-0219, T-0385, T-0432, T-0431 and T-0676 are each verified against `dev`: the first
four `open` and in QUEUE.md, T-0676 `done`. Each of the four open tickets carries a
`Prior attempt:` line naming its closed PR. `./tools/check.sh` passes. The open-PR count
against `dev` is 16.

**THE FIVE BRANCHES ARE STILL ON THE REMOTE, and that is not an oversight.** A ref delete
is refused in the session that closed these PRs — `git push origin --delete` disconnects
mid-sideband and `DELETE /repos/.../git/refs/heads/...` answers **HTTP 403, "Write access
to this GitHub API path is not permitted through this proxy"**. Both routes, all five
branches. So the deletion is the ONE part of this ticket that needs a hand: each closed
PR carries a **Delete branch** button, which is one click apiece, or the janitor's
`branch-delete` path can do it with the `STEWARD_PAT` this environment does not hold.

**What it costs until then, so nobody is surprised by it.** `ticket.mjs claim` checks
`git ls-remote` for a branch carrying the ticket's number and refuses when it finds one —
that guard exists to stop two runs rebuilding one ticket, and here it will fire on a
branch whose PR is closed. **It is a false stop and `--force` is the right answer**, which
is why each of the four tickets now says so in its own body. `ticket.mjs inflight` already
reads all five as COLD (a branch older than any run could be), which is the honest signal
and needs no change.
