---
id: T-0956
title: Re-lay #841 on today's dev: Moses and Kirkland vol. 1, the oldest base in the drain — 137k lines of extracted text and forty-nine lead surnames
state: done
epic: PIPELINE
requested_by: owner
seen: false
effort: S
legacy_id: null
parent: T-0932
opened: 2026-09-07
closed: 2026-09-07
pr: 841
claimed_by: run 9/7/2026, 5:12:40 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-07T10:13:53.614Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34109535187
---

Re-lay #841 on today's dev: Moses and Kirkland vol. 1, the oldest base in the drain — 137k lines of extracted text and forty-nine lead surnames.

Piece 3 of 3 of **T-0932 — Land or close the stale readings, part two: the map and book PRs — #955, #953, #841**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

**Why a lap kept failing, and what actually works.** Measured on 2026-09-07 while
T-0954 was landed by this method. The branch had been "lapped onto dev" fourteen
times since 2026-09-06 and its merge base never moved, because the lap was
regenerating files that today's `dev` no longer tracks at all:

- `tickets/tickets.json` and `tickets/BOARD.md` came off the PR surface in
  **T-0937** (#1022) — generated, never committed.
- `site/chicago/4d/` came off it in **T-0938** (v663) — generated, untracked,
  `.gitignore`d, and `tools/publish.sh` is its one writer.

Between them those are 800+ lines of the branch's diff and every one of them is a
guaranteed conflict against a `dev` that has deleted the file. Rebasing cannot win.

**The lap that works** — reset the PR branch to `origin/dev` and re-apply only what
a human wrote, then regenerate:

1. `git checkout -B <pr-branch> origin/dev`
2. `git checkout origin/<pr-branch> -- <the hand-written files only>` — the reading,
   the tool, the docs, the ticket `.md`s. Take **nothing** under `site/`, and neither
   `tickets/tickets.json` nor `tickets/BOARD.md`.
3. Re-run the generators on today's tree rather than carrying their output across.
   For T-0954 that was `read_census_1830.py --build`, and then
   `consolidate_resident_evidence.py --build` — the second is easy to miss and it is
   what `check.sh` fails on (`identity_master.json does not re-derive`).
4. Re-author the changelog entry on top of today's file with `v: null, ts: '', date: ''`
   and stamp it. Do not carry the branch's stamped `v:` — it is 48 versions stale.
5. `QUEUE.md` by hand: delete the closed ticket's line, append the new ones at the
   bottom. Never carry the branch's whole QUEUE.md.
6. `ticket.mjs done T-NNNN --pr <n>`, `publish.sh`, `check.sh`, then the legs
   `smoke_budget.mjs --for-diff` names.

**And re-ask the three questions of T-0932 before landing** — the reading is only
honest if its figures still hold on the tree that actually merges.
