---
id: T-1427
title: inflight cannot see an open pull request: the PR projection drops head.ref and the fetch asks only for closed PRs, so a branch under review — including a hold PR parked for the owner — is printed as work NOBODY CAN SEE and offered up for rebuild
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-20
closed: 2026-09-20
pr: 1550
claimed_by: run 9/20/2026, 12:11:33 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-20T05:33:27.343Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35490582963
---

`inflight` is the instrument the loop uses to answer one question: is somebody already on
this? On 2026-09-20 it answered that question WRONG in the most expensive direction. It
printed `steward/t-1191-north-corridors` under

    RECOVERABLE — branch(es) carrying work NOBODY CAN SEE
      no merged PR names this ticket and no PR ever carried this branch.
      READ IT BEFORE YOU REBUILD IT: .../compare/dev...steward/t-1191-north-corridors

PR **#1533** was open on that exact branch, labelled **`hold`**, parked for the owner on
purpose because its gate is not green and it refuses an alley reading rather than faking
it. The report invited a rebuild of the owner's own parked work.

**Two faults compound, and each is enough on its own.**

1. `restGet` projects a pull request down to `{ number, title, merged_at, created_at }`
   — and `inflight`'s guard is `new Set(pulls.map((pr) => pr?.head?.ref))`. `head` is not
   in the projection, so against the LIVE API that set is always empty and the guard can
   never fire. It passes the gate only because `test_ticket_inflight.mjs` supplies
   `head.ref` in its `--pr-json` fixture. A check that is dead in production and green in
   the gate is worse than no check.
2. `closedPulls` asks `state=closed`. An open PR is therefore not in the collection at
   all, so even a repaired guard could not see #1533. The code knew — it said "Open PRs
   are not in this collection" — and then still printed "no PR ever carried this branch",
   which is a flat false statement, and pointed the reader at a list that does not hold
   the answer either.

**Acceptance:**

- The PR projection keeps `head.ref`, `state` and `labels`, and the fetch asks
  `state=all`. `landedFindings` filters on `merged_at`, so MERGED-PR RECONCILIATION is
  unchanged by the wider ask.
- A branch on an unfinished ticket that has an OPEN pull request gets its own reading,
  `open_pr`: never `recoverable`, and never in the cold list, whose standing advice is
  `git push origin --delete <branch>` — which would shut the pull request.
- It is printed with the PR number and the PR's labels, and a `hold` label is called what
  it is: a run parked this for the owner; do not rebuild it, do not take the ticket, do
  not delete the branch. Every IN FLIGHT line carries the PR number too, so a run reads
  one list and not two.
- `--json` carries `open_pr`.
- `test_ticket_inflight.mjs` holds all of it on a constructed branch list and a
  constructed PR list, reaching no network: the open PR is `open_pr` and not
  `recoverable`, its `hold` label is printed, and — the regression that hid fault 1 —
  a PR list whose rows carry no `head.ref` cannot silently turn the guard off.
- The existing readings are untouched: live, held, cold, recoverable and the refusals
  (silence is not evidence; a claim lock is not work) all still hold.

**Stop condition:** no branch with an open pull request is ever described as work nobody
can see, or offered for deletion.

**Links:** T-1155 (the reading this repairs) · T-0852 · T-0429 · PR #1533.

**No changelog entry, signed:** the three watched files this branch touches —
`tools/ticket.mjs`, `tools/test_ticket_inflight.mjs` and the `check.sh` step that
gates them — are the loop's own instruments. No renderer, record, figure or asset
moves, so there is nothing a visitor or the release feed could read. The branch
carries the `Changelog: none` trailer the gate asks for rather than inventing a
release note for a change no reader has.
