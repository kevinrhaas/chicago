---
id: T-0389
title: The New York House belongs to no programme the 665-roof ledger can read, and dev's gate is red on it
state: done
epic: TOWN
requested_by: loop
seen: false
effort: S
legacy_id: null
parent: null
opened: 2026-08-29
closed: 2026-08-29
pr: 542
claimed_by: run 8/29/2026, 9:43:39 AM CT
blocked_on: null
needs_bake: false
---

**`tools/check.sh` is RED on an unmodified `origin/dev`**, measured 2026-08-29 at
`9b6e3276`, with a clean worktree and nothing on top:

```
the 665-roof programme reconciles with the town that stands           FAILED
the group rows add up by division too, and every division over one …  FAILED
…and its own assertions still fire when broken                        FAILED
```

**Three failures, one cause,** and the message is the same in all three:

> `new_york_house` belongs to no programme this ledger can read. A structure record must
> carry a reconstruction block, or be an entry in the physical-roof reconciliation, or be
> a building of the inferred-household programme — otherwise it stands in the scene and
> not in the count.

## Where it came from

**PR #536 (T-0380), the most recent merge on `dev`** — "the New York House stands on Lake
Street near Wells". It added a structure record and did not enrol it in any of the three
programmes the 665-roof ledger reads. T-0380 is `done`; the ticket that would carry the
repair did not exist until this one.

## Why this is the first thing a run should take

`chicago-4d-check.yml` IS the dev gate. While this stands, **every branch cut from `dev`
is red before it changes a line**, and every run pays T-0215's cost — proving its own red
is inherited before it can merge. It is the cheap gate, and it is the one that is broken.

Note also the third failing line: the reconciliation's **self-test** fails too, which
means the harness that proves those assertions can fail is itself unable to run. So the
gate is not merely reporting a red — it is currently unable to demonstrate that it works.

## What the run that takes this has to decide, not assume

The fix is one enrolment, and **which programme it belongs in is a judgement about the
building, not a lookup**:

1. **The physical-roof reconciliation** — if the New York House is one of the 665 roofs
   the ledger already counts, it is an entry there and the count does not change.
2. **A reconstruction block** — if it is a roof this project raised, it declares its
   programme and its band like every other reconstructed roof.
3. **The inferred-household programme** — almost certainly NOT: this is a documented
   hotel from the papers, not a household the occupation census raised.

Read T-0380's own record and PR #536 before choosing. If the honest answer is that the
665 count should go up by one, say so and move the target with its reason — the ledger
exists to be argued with, and T-0032 records that the target has been wrong before.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

- `tools/check.sh` is GREEN on an unmodified `dev` after this merges, and the run says so
  from a clean worktree rather than from its own branch.
- The New York House's programme membership is **stated with its reason**, not chosen to
  make the gate pass.
- If the 665 target moves, the move is argued and recorded at the target's definition.
- The reconciliation's self-test runs and passes — a gate that cannot demonstrate its own
  assertions firing is not repaired.
- **The gate is not weakened.** If `new_york_house` cannot be enrolled honestly, the
  finding is that the ledger needs a fourth category, and that is a ticket, not a
  loosened assertion.

**Links:** T-0380 / PR #536 (added the record) · T-0032 (the target has been wrong
before) · T-0215 (the cost every branch pays while dev is red) · T-0377 and T-0388 (the
PREVIOUS standing dev red, three re-derive steps, now green — this replaced it).
