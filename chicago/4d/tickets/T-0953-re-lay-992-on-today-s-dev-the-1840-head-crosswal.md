---
id: T-0953
title: Re-lay #992 on today's dev: the 1840 head crosswalk, whose T-0896 collides with a different T-0896 that landed while it waited
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-07
closed: 2026-09-07
pr: 992
claimed_by: null
blocked_on: null
needs_bake: false
closed_at: 2026-09-07T11:40:44.535Z
claimed_run: null
---

Re-lay #992 on today's dev: the 1840 head crosswalk, whose T-0896 collides with a different T-0896 that landed while it waited.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

`#992` re-derives the 1840 head crosswalk and spends its 27 rulings onto the cards.
T-0698 still reads `open` on `dev` and still sits in the workable queue, so nothing has
superseded it.

**It has one hard blocker beyond the lap.** The branch files `T-0896` as *"publish.sh
minifies four resident mirror files"*; `dev` landed a different **T-0896** — *"drain the
18 check-capable tools"* — while it waited. That is a duplicate id, and `check.sh` fails
outright on it: *"an id that names two things is not an id"*. Worse, the branch's T-0896 is
the fifth filing of a fault **T-0933 has already closed** (T-0938 removed the mirror, so
publish.sh and the synthesizer no longer contend) — see also T-0874, T-0880, T-0905. So it
is `withdraw`n as superseded, not restamped. T-0897 on the branch is free.

**Acceptance:** #992 merges with a body whose figures are true of the tree that merged, or
is closed with its salvage recorded.


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
