---
id: T-0831
title: Six generated files conflict on every merge in this repo and always resolve by regenerating, so the conflict costs a hand resolution and buys nothing
state: withdrawn
epic: PIPELINE
requested_by: steward
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-05
closed: 2026-09-05
pr: 910
claimed_by: run 9/5/2026, 2:35:04 PM CT
blocked_on: Duplicates T-0813 (owner-requested), split into T-0832 + T-0833; the work landed as T-0832 via PR #910
needs_bake: false
closed_at: 2026-09-05T19:46:22.713Z
claimed_run: null
---

Six generated files conflict on every merge in this repo and always resolve by regenerating, so the conflict costs a hand resolution and buys nothing.

## The measurement, which is a log rather than an argument

PR #906 (T-0820) was open for about seventy minutes. `dev` moved **five times**
under it — #904, #907, #908, #905, #858 — and every one of the five merges
conflicted, always in generated files and **never once in the substantive diff**:

| lap | dev landed | files that conflicted |
|---|---|---|
| 1 | #904 | BOARD.md, tickets.json ×2, build.json, walk/index.html |
| 2 | #907 | the same five, plus STATUS.md (a real content conflict, hand-merged) |
| 3 | — | (same five, measured with `merge-tree` before the lap) |
| 4 | #905 | the same five |
| 5 | #858 | BOARD.md, tickets.json ×2 |

`check.sh`, `QUEUE.md`, `changelog.js` and every ticket source auto-merged every
time, because those either carry a driver or are hand-authored. Two other PRs
report the identical finding independently:

- **#894**: *"each one collides on the same four generated files"* — BOARD.md,
  tickets.json ×2, build.json, walk/index.html. Four rebases paid; the fifth is
  where that run's clock ran out.
- **#850**: *"Every conflict so far has been in a generated file… The
  substantive diff has merged cleanly every time."* Rebased twice, gate run three
  times on three successive bases with the same result, then parked.

#850 also prices it: ~19 minutes of honest verification per lap, and `dev` took
three more merges inside that window. That is the treadmill, and it is why PRs
get parked on `hold` with finished, green work.

## The two kinds, and treating them alike would destroy data

**This is the part to get right.** The six files are not one category.

**(a) Five BUILD PRODUCTS — regenerable, and already gate-covered when stale:**

| file | what refuses it stale |
|---|---|
| `chicago/4d/tickets/BOARD.md` | `ticket.mjs check` — refuses a stale board |
| `chicago/4d/tickets/tickets.json` | same |
| `site/chicago/4d/tickets.json` | `test_ticket_mirror.mjs` — asserts a mirror somebody made stale still fails |
| `site/chicago/4d/build.json` | `check_published.mjs` |
| `site/chicago/4d/walk/index.html` | `check_published.mjs` — every published file is byte-identical to its source or a declared transform |

Verified by reading `check.sh`, not assumed. **The gate already stands in for the
conflict on all five**, which is precisely the argument `docs/LIBERTIES.md`'s
`.gitattributes` note makes for the liberties register: *"A conflict is safe
because it stops you… and the check is what stands in for the conflict."*

**(b) One LEDGER — `chicago/4d/tools/dev-smoke-state.json`, which must NOT get
the same treatment.** It holds `readings[]` — 62 append-only smoke readings
(T-0216). Measured: the rows carry **no `id`**, so T-0820's uniqueness check does
not see it, and **no step in `check.sh` reads it at all**. Taking one side would
silently discard the other side's readings, with nothing to catch it. #905
resolved it by taking dev's side and said so; that is right for one lap and wrong
as a standing rule.

So (a) wants "keep ours, then regenerate" and (b) wants a union of entries. A
single rule over all six would quietly lose smoke history.

## What NOT to do, and the repo has already paid for it

`merge=union` is banned here on measured grounds and must not come back: it is a
LINE union, and it converted five loud changelog conflicts into five silent
corruptions in one day (2026-08-15). Any driver written for (b) works at ENTRY
granularity, like `merge-queue.mjs` and `merge-changelog.mjs` do, or it is not
written.

And a driver that silently keeps ours removes the merge's own reminder to
regenerate. `merge-changelog.mjs` solves this by PRINTING the follow-up command;
whatever ships for (a) does the same, or the next stale mirror is a gate failure
nobody expected.

## Acceptance

- The five build products no longer conflict on a merge, and the driver prints
  the regeneration command the way the changelog driver prints the stamp command.
- `dev-smoke-state.json` keeps BOTH sides' readings across a merge, at entry
  granularity, with a self-test proving a reading is never dropped — or it is
  deliberately left conflicting, with the reason written down.
- Registered by `tools/setup-merge-drivers.sh` like the existing two, and safe
  unregistered: a fresh clone falls back to the ordinary text merge, never to
  something worse.
- A self-test beside `merge-queue-selftest.mjs`, and a `check.sh` step, so the
  driver cannot quietly stop doing what `.gitattributes` promises.
- Measured after: merge `dev` into a branch and show the conflict set is empty.
