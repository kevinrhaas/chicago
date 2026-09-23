---
id: T-0937
title: The ticket build products come off the PR surface: BOARD.md and both tickets.json are generated on demand, never committed
state: done
epic: META
requested_by: owner
seen: false
effort: S
legacy_id: null
parent: T-0857
opened: 2026-09-06
closed: 2026-09-06
pr: 1022
claimed_by: run 9/6/2026, 10:32:49 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-07T04:01:48.655Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34079629230
---

The ticket build products come off the PR surface: BOARD.md and both tickets.json are generated on demand, never committed.

Piece 1 of 2 of **T-0857 — GitHub's merge never runs this repo's merge drivers, so every PR reads as conflicting and auto-merge can never fire**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**WHY THIS PIECE IS FIRST, and it is measured in the parent's own .gitattributes note.** The
five files that conflict on every lap are `BOARD.md`, `tickets.json` twice, `build.json` and
`walk/index.html`. Of those, the three ticket artifacts are the ones that hit EVERY PR rather
than every publishing PR: a run's first commit is `ticket.mjs claim`, which rewrites all three,
so two branches conflict before either has done any work. PR #906's lap 5 (#858) conflicted on
those three and nothing else. They are also the cheap ones — pure functions of
`tickets/*.md`, with no renderer, no bake and no byte-identity invariant behind them.

**Acceptance:** `chicago/4d/tickets/BOARD.md`, `chicago/4d/tickets/tickets.json` and
`site/chicago/4d/tickets.json` are untracked and ignored; every reader that needs one
materialises it (`ticket.mjs check`/`board` locally and in the gate, `publish.sh` before its
copy, `deploy.yml` before the Pages upload and before the dev-preview assembly); the three
`merge=generated` lines for them are gone from `.gitattributes` and the note there says what
was taken and why; `tools/test_ticket_mirror.mjs` still proves the second half of T-0154 — a
mirror somebody else made stale fails, and a no-op regeneration does not launder it — plus the
new half, that a tree which carries no board at all gets one.

**What stays:** `build.json` and `site/chicago/4d/walk/index.html` keep `merge=generated`;
they are publish-stamp files and they belong to T-0938 with the rest of the mirror.
