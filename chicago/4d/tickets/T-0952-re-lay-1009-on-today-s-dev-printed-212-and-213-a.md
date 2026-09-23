---
id: T-0952
title: Re-lay #1009 on today's dev: printed 212 and 213 are a real reading on a 29-commit-old tree, and the mirror came off the PR surface underneath it
state: withdrawn
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-07
closed: 2026-09-09
pr: null
claimed_by: null
blocked_on: superseded: printed 212 and 213's page files (RY/RK) landed via T-0963; the 61 heads are on dev
needs_bake: false
closed_at: 2026-09-10T04:20:12.257Z
claimed_run: null
---

Re-lay #1009 on today's dev: printed 212 and 213 are a real reading on a 29-commit-old tree, and the mirror came off the PR surface underneath it.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

`#1009` carries the substance: `data/research/census_1840/pages/33SQ-GYYJ-RY.json` and
`33SQ-GYYJ-RK.json`, printed 212 and 213 read line by line, 61 heads. **Neither file
exists on `dev`**, so nothing has superseded the reading — this is a re-lay, not a
salvage. Its ticket ids are clean: T-0911 and T-0896 on the branch are the same tickets
that landed on `dev`, and T-0916 is unused there.

**Acceptance:** #1009 merges with a body whose figures are true of the tree that merged,
or its two page files land under a fresh PR with the reading intact and #1009 is closed
with that recorded.


**Why this exists.** T-0931 read the four stale reading PRs against `dev` at `0e6e669e4`
and found that all of them predate three structural changes, so none can merge as it
stands. #998 was re-laid and merged in that pass and this is the same lap for its sibling.

**The lap, proved on #998 — follow it rather than rediscovering it**

1. `bash chicago/4d/tools/setup-merge-drivers.sh` FIRST. Without it `QUEUE.md` and
   `changelog.js` conflict the old way and the queue order is what gets wrecked.
2. Merge `origin/dev` in. Resolve by **accepting dev's deletion** of
   `site/chicago/4d/**`, `chicago/4d/tickets/tickets.json` and `tickets/BOARD.md` —
   T-0937 and T-0938 took all three off the PR surface and they are gitignored now.
3. Any ticket the branch filed has to be checked for an id that landed meanwhile:
   `node tools/ticket.mjs restamp <file>` renumbers the younger one, and a ticket whose
   fault has since been closed is `withdraw`n rather than renumbered.
4. Re-run the derived cascade, then run `./tools/check.sh` and re-run whatever it names.
   On #998 the branch's own cascade list was short by twelve steps: `town_census.py`,
   `report_letter_list_collisions.py`, the Norris and Fergus 1843/1839 crosswalks,
   `read_fergus_obits`, `read_second_presbyterian`, `spend_directories`,
   `spend_fergus_1839_later_lists`, `spend_fergus_1839_lot_sale`,
   `back_project_addresses`, `compile_scene --all`.
5. **Correct the PR body before merging.** Its table is a reading of a tree that is gone.
6. `node tools/smoke_budget.mjs --for-diff` names far fewer parts now that the mirror is
   off the diff — on #998 it named 3, 10, 12-13 instead of 1-13.

**A trap worth naming:** `tools/check.sh` prints four `FAIL` lines about cross-street
faces that are the cross-street SELF-TEST's expected output (T-0763). A pristine
`origin/dev` worktree was measured in this run and it is **CHECK PASS** — so a red on your
branch is yours.
