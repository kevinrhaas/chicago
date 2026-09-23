---
id: T-1520
title: A cancelled non-required check leaves a PR unstable for ever: gate green, merge-ready passes over it, and the stuck reporter calls it moving — pr-stuck's third shape
state: open
epic: META
requested_by: owner
seen: false
effort: S
legacy_id: null
parent: null
opened: 2026-09-21
closed: null
pr: null
claimed_by: null
blocked_on: null
needs_bake: false
closed_at: null
claimed_run: null
---

A cancelled non-required check leaves a PR `unstable` for ever: the gate is green,
`merge-ready` passes over it, and the stuck reporter calls it moving.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

MEASURED 2026-09-21 ON #1617, and found by the owner rather than by any automation —
which is the whole complaint, because T-1510 had just taught the reporter to find
exactly this class of thing.

`chicago-4d-pr-stuck.yml` carries `concurrency: cancel-in-progress: true` and fires on
every push to `steward/**`. Two pushes inside one window therefore leave a CANCELLED
`report` check on the newer head — and clearing a PR is normally two pushes a minute
apart (the gate-verified commit, then the dev merge that lands under it). On #1617:

    gate      completed success
    generate  completed success
    report    completed cancelled     <- from the first push, cancelled by the second

    mergeable_state: unstable

`unstable` is not `clean`, and `.github/steward/merge-ready.sh` merges only on `clean`,
deliberately. Nothing re-runs a cancelled check. So a PR whose gate has PASSED sits
unmergeable until a person notices — #1617 would still be sitting there. It took a
`POST /actions/runs/{id}/rerun` to clear, and it went `clean` within a minute of that.

THIS IS THE SAME SHAPE AS T-1368 REACHED BY A DIFFERENT ROUTE, and T-1510's new
red-gate shape does NOT catch it: the gate is green, the state is not `dirty`, so
`pr-stuck.sh` prints `something can move this` — the same wrong answer it used to give
a red gate.

**Acceptance:**

- `pr-stuck.sh` reports a THIRD shape: `mergeable_state` is `unstable`, the owning run
  is not alive, and the head is older than `STUCK_MIN_AGE_MIN`. The comment names the
  check(s) that are not `success` and says plainly that the gate may well be green and
  the PR still cannot merge, because `merge-ready` requires `clean`.
- It names the remedy that is NOT an empty commit: re-run the cancelled check run. An
  empty commit to kick CI is refused everywhere else in this repo and must not be
  suggested here.
- `tools/test_pr_stuck.mjs` covers the shape and its near-misses: `unstable` under a
  LIVE run (left alone), `unstable` on a head too young (left alone), and a PR that is
  `clean` with a cancelled check on an OLDER head (not reported — the check that
  matters is the one on the current head).
- SEPARATELY, AND ARGUABLY THE REAL FIX: consider dropping `cancel-in-progress` from
  `chicago-4d-pr-stuck.yml`. That run is cheap — it reads the queue and writes nothing
  but a label and a comment — and its cancellation costs a pull request. State the
  reading either way rather than changing it silently; if it stays, the reporter has to
  cover the state its own trigger creates, which is the acceptance above.
