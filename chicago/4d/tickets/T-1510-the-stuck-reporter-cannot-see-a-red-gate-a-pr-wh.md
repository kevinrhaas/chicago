---
id: T-1510
title: The stuck reporter cannot see a red gate: a PR whose gate failed and whose owning run has finished is the one state no automation in this repo owns
state: open
epic: META
requested_by: owner
seen: false
effort: M
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

The stuck reporter cannot see a red gate: a PR whose gate failed and whose owning
run has finished is the one state no automation in this repository owns.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

Found by the owner on 2026-09-21, from a queue that grew 1 -> 5 open PRs in two hours
with `dev` not moving for 95 minutes. Map the states to their owners and the hole is
exactly one row wide:

| PR state | What clears it |
| --- | --- |
| `dirty` | `.github/steward/pr-lap.sh` — merges the base in with the drivers |
| `clean` | GitHub auto-merge, and `.github/steward/merge-ready.sh` |
| `dirty`, no gate, owning run finished | `.github/steward/pr-stuck.sh` — the T-1368 deadlock |
| **`blocked`/`unstable` with a RED gate, owning run finished** | **nobody** |

The lap merges the base in and pushes; it does not care whether the gate then passes,
and it is right not to — it does not gate (that cost ~7 minutes a PR and was why the
queue never converged). `merge-ready` merges only `clean`, and a red PR is never
`clean`. `pr-stuck` reads `mergeable_state` and any state that is not `dirty` prints
`something can move this` and moves on — which is TRUE of `behind` and `blocked`-while-
gating, and FALSE of a gate that has already failed under a run that has already
finished. Nothing is coming for that PR.

MEASURED 2026-09-21. #1616 (T-1294) failed the changelog-entry gate at 09:23:16; its
steward run completed SUCCESS at 09:23:44 and walked away. #1618 (T-1508) failed three
gate steps at 10:26:00; its run completed SUCCESS at 10:21:39. Both sat until a person
read the logs. Both needed real judgement to fix — a dead rule to retire, a report
contradicting its own table — so the fix is NOT to automate the repair.

**Acceptance:**

- `pr-stuck.sh` reports a second shape: the head's `gate` check run is `completed` with
  a failing conclusion, the owning run is not alive by the test it already applies, and
  the head is older than `STUCK_MIN_AGE_MIN`. A gate still running is not this, and a
  PR whose run is still going is not this — both are already-correct refusals and stay.
- The comment NAMES THE FAILING STEPS, read from the job the check run points at. A
  report that says only "the gate is red" sends the reader to the same logs the reporter
  just read, which is most of the cost of this state.
- It still merges nothing, pushes nothing and resolves nothing. The two PRs above needed
  judgement; a robot that re-ran or reverted them would have been worse than silence.
- The label comes back off when the gate goes green, exactly as it does when a `dirty`
  PR comes unstuck.
- `tools/test_pr_stuck.mjs` covers the new shape AND its three near-misses: a gate still
  in progress, a red gate under a live run, and a red gate on a head too young. Every
  case runs the real script against the faked `gh`, as the existing ones do.
- No new workflow. `chicago-4d-pr-stuck.yml` already fires on `steward/**` as well as
  `dev`, which is the trigger that matters — `pr-lap` and `merge-ready` fire on `dev`
  pushes alone, so when the queue jams they stop running with it.
