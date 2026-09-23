---
id: T-0586
title: The ledger records the instant a ticket finished and which run claimed it
state: done
epic: META
requested_by: owner
seen: false
effort: S
legacy_id: null
parent: null
opened: 2026-09-03
closed: 2026-09-03
pr: 709
claimed_by: run 9/3/2026, 12:09:01 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-03T17:10:25.086Z
claimed_run: null
---

The ledger records the instant a ticket finished and which run claimed it.

**Filed on the owner's ask of 2026-09-03:** "i would like to see what is in queue, what has been completed
and when and what tickets have been claimed and are being worked… in finish order not alpha on when they
are done."

**The hole.** `closed` is a Central Time DAY. Nineteen tickets closed on 2026-09-03; a day cannot order
them, so BOARD.md's only finished list sorted by day and then fell back on the ticket id — the newest work
read as if it had been done alphabetically, and the list was capped at twenty. `claimed_by` records WHEN a
claim happened but not WHICH of five parallel slices holds the ticket or where its log is.

**What this ticket does.**
- `closed_at` (ISO-8601 UTC) written by `done`, `withdraw` and `split` beside the day-granular `closed`;
  `claimed_run` (the Actions run URL, from the runner's own environment) written by `claim`. Both appended
  to the END of the front matter, so a ticket file written by an older checkout is still valid and reads
  them as null.
- BOARD.md opens with **Claimed — being worked now** (who holds what, with a link to the run) and closes
  with **Finished, newest first** — 100 tickets ordered day → instant → PR number → id, each with its
  finish time and a link to its PR. The PR number is what orders the 312 tickets finished before the
  instant existed; the id is the last resort, never the first.
- `check` holds the two new rules honestly: a present `closed_at` must parse, and only tickets closed on or
  after 2026-09-04 are required to carry one. The 312 finished before this landed are history, not a hole.

**Acceptance:** (one demonstration, never weakened to pass)
- `tools/test_ticket_mirror.mjs` asserts that closing a ticket stamps `closed_at` in the published mirror
  and that the board's Finished section leads with the ticket that just closed.
- `node tools/ticket.mjs check` green twice; `bash tools/check.sh` CHECK PASS; `tools/test_ticket_restamp.mjs`
  still green.
- `tickets/README.md` and `AGENTS.md` state both fields and why the day alone was not enough.

**What reads this next:** Manager's 4D queue screen (custom T-0030), which fetches
`custom.polecat.live/chicago/4d/dev/tickets.json` and shows Up next / In flight / Finished newest first;
and the steward journal, which will name the ticket each run picked up.
