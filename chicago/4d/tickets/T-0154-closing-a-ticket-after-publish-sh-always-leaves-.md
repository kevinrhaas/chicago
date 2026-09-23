---
id: T-0154
title: Closing a ticket after publish.sh always leaves the published mirror stale
state: done
epic: PIPELINE
requested_by: loop
seen: false
effort: S
legacy_id: null
parent: null
opened: 2026-08-23
closed: 2026-08-23
pr: 321
claimed_by: run 8/23/2026, 1:57:44 AM CT
blocked_on: null
needs_bake: false
---

`site/chicago/4d/tickets.json` is a verbatim copy of `chicago/4d/tickets/tickets.json`,
and `check.sh`'s *published mirror matches its source* step compares them byte for byte.
`ticket.mjs done` rewrites `tickets/tickets.json`. So a run that follows the documented
order lands in a state the gate refuses, every time:

1. do the work, run `./tools/publish.sh` — required, "PUBLISH IN THE SAME COMMIT";
2. push, open the PR — the PR number does not exist until this moment;
3. `ticket.mjs done T-NNNN --pr N` — required, "close it in the merging PR";
4. the mirror is now stale, and the gate fails on the very next push.

The two instructions are each right on their own and cannot both be satisfied in the
stated order, because step 3 needs a number that only exists after step 2. Hit on
T-0153/PR #318 (gate red at 05:11Z on exactly this), and it will be hit by every run
that closes a ticket in its own PR.

Working around it by hand — remembering to re-run `publish.sh` after the close — is what
happens now, and it is precisely the kind of unwritten step that goes wrong at 3am.

**Acceptance:** closing a ticket cannot leave the mirror stale. Either `ticket.mjs done`
re-publishes the paths it dirtied, or `tickets.json` stops being mirrored verbatim and
the gate learns it is generated, or the close moves to a step that runs after publish.
Whichever is chosen, the check must still catch a genuinely stale mirror — this must not
be fixed by making the gate weaker. A run that follows AGENTS.md literally, in order,
must end green without a remembered extra step.
