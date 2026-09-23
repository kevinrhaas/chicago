---
id: T-1345
title: step_isolation exempts gitignored build products by a hand-kept path list, when git check-ignore can classify them: a write to an ignored path is a build product and a write to a tracked one is a tree mutation, and the gate should ask rather than be told
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

step_isolation exempts gitignored build products by a hand-kept path list, when git check-ignore can classify them: a write to an ignored path is a build product and a write to a tracked one is a tree mutation, and the gate should ask rather than be told.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

1. `audit_step_isolation.mjs` classifies a measured write by asking git, not by a list:
   a path `git check-ignore` claims is a BUILD PRODUCT, a tracked path is a TREE MUTATION.
2. The three hand-kept exemptions added on 2026-09-18 — `site/`,
   `chicago/4d/tickets/BOARD.md`, `chicago/4d/tickets/tickets.json` — are then redundant
   and removed, and the gate still passes for the same reason it passes today.
3. A write to a TRACKED path is never excused by this. The classification decides which
   question is asked, not whether one is.
4. The measurement records the classification (`wrote` vs `wrote_ignored`) so the cheap
   per-commit half does not shell out to git once per path.

## WHY THE LIST IS THE WRONG SHAPE

T-1339 shipped with `site/` exempted, and #1480 immediately needed two more —
`ticket.mjs board` regenerating BOARD.md and tickets.json. All three are gitignored, and
T-0937 made them so for exactly this reason: they were the most-conflicting files in the
repository, because a run's first act is `ticket.mjs claim` and that rewrites all three
before any work is done.

So every exemption so far has had the SAME underlying reason — it is an untracked build
product — and the file states that reason three times in prose while git already knows it
as a fact. A list that grows one entry per build product is a list that will be wrong the
first time somebody adds one and does not think to extend it, which is the failure mode
T-1339 was built to remove, reappearing one level up.

**AND THE LIST IS WEAKER THAN THE FACT.** A prefix like `site/` excuses anything under it
forever, including a tracked file that ends up there by mistake. `git check-ignore` answers
per path, per commit, and cannot drift from what the repository actually tracks.

## WHAT THIS DOES NOT CHANGE

The residual caveat stays true either way and should stay written down: an ignored build
product is still SHARED STATE that a concurrent gate step can read mid-write, and
regeneration is idempotent rather than atomic. Classifying it correctly is not the same as
proving it safe — it only says which of the two questions the gate is entitled to ask.
