---
id: T-0928
title: Land the finished PRs that need only a dev lap: gated units sitting open because dev moved under them
state: done
epic: PIPELINE
requested_by: owner
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-06
closed: 2026-09-07
pr: 1026
claimed_by: run 9/7/2026, 1:02:39 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-07T06:50:04.363Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34088902007
---

These PRs are finished units. They are gated green and they are open only because `dev`
moved under them and GitHub cannot merge a branch whose generated files need this repo's
merge drivers (**T-0857**, which is why that ticket leads this band).

`#940`, `#951`, `#967`, `#971`, `#1012`, `#1017`.

**The lap, and it is mechanical:**

```
git checkout <branch> && git merge origin/dev     # the drivers resolve the generated files
cd chicago/4d
# if the merge brought data or a tool change, run the cascade in order:
python3 tools/consolidate_resident_evidence.py --build
python3 tools/mint_civic_residents.py --build && python3 tools/mint_civic_residents.py --regrade
python3 tools/compile_liberties.py && python3 tools/compile_register.py --build
# ... the readers, the crosswalks, the spends, the exports ...
python3 tools/consolidate_town_cards.py --apply && python3 tools/town_census.py
python3 tools/compile_scene.py --all
node tools/ticket.mjs board && node tools/ticket.mjs check
node tools/stamp-changelog.mjs && node tools/check-changelog.mjs
bash tools/publish.sh && bash tools/check.sh
```

**Land them ONE AT A TIME, and merge immediately when the gate goes green.** With the lane
at one slice, `dev` only moves when this run moves it, so a lap taken and pushed is a lap
that lands. Two slices is what made this a treadmill: every landing invalidated the other
in-flight branch, and a branch could be lapped four times without ever being mergeable.

**Binary conflicts are not conflicts.** The four `.xlsx` workbooks under
`chicago/reference/resident-research/` are cascade output. Take `dev`'s side and let
`export_resident_research_package --all --build` and `export_resident_audit --build`
rebuild them. Never hand-resolve one.

**A duplicate ticket id is the other lap-killer.** `tools/ticket.mjs check` catches it and
`restamp` repairs it; the ticket keeps its queue place, but anything that CITES the old
number — a card note, a doc line, the changelog — has to move with it, and the gate cannot
see those. Grep for the old id before committing.

**Acceptance:**

1. Each of the six is merged, or a written reason says why it could not be.
2. Every merge is preceded by a green `tools/check.sh` on the merged tree — the seven `FAIL`
   lines the gate prints for the cross-street faces, the southern ground and the far-timber
   census are its own negative-control self-tests and are expected; `CHECK PASS` and exit 0
   are the signal.
3. No changelog entry is landed twice. If `dev` already announced the work, drop the
   branch's entry rather than double-announcing it.

## Closed 2026-09-07 — PR #1026

Five of the six were still open; `#1017` had already landed.

| PR | ticket | outcome |
|---|---|---|
| #940 | T-0681 | merged |
| #967 | T-0843 | merged |
| #951 | T-0764 | lapped twice, `check.sh` green, auto-merge armed |
| #1012 | T-0912 | lapped twice, `check.sh` green, auto-merge armed |
| #971 | T-0837 | left alone — 16 conflict hunks outside the generated set, commented on the PR |

**What the next lap should expect, beyond the mechanical recipe above.**

1. **The untracked three are removed, never taken.** The mirror (T-0938), BOARD.md and both
   `tickets.json` (T-0937) are modify/delete conflicts on every branch cut before those
   landed. `checkout --ours` puts them back in the index and `git add -A` re-tracks on the
   merge exactly what the base untracked.
2. **The queue driver keeps OUR order, and ours can predate a re-rank.** Two of four laps
   failed the gate with *QUEUE.md HAS GONE BACKWARDS*. Take `origin/dev`'s file, run
   `ticket.mjs board`, then put the branch's own rows back: a new ticket appended at the
   BOTTOM, and the line of a ticket the branch CLOSES deleted.
3. **A restamped id has citations the gate cannot see.** #967's T-0865 collided with dev's
   Taylor ruling; `restamp` moved it to T-0950 and the deferral in
   `card_merge_rulings.json` and the STATUS entry had to move by hand.
4. **The PR gate asks a question `check.sh` does not.** A branch touching watched `tools/`
   paths and no renderer, record or generator needs the `Changelog: none — <why>` trailer.
   #940 (the smoke ledger) and #951 (a research compiler's staleness check) both signed one.
5. **A real conflict is refused, not resolved.** #971's merge disagrees about research
   claims — two household records, the synthesis write, its drift baseline, the spend
   baseline, seven hunks of `synthesize_resident_research.py`. That is for the run that owns
   T-0837.

**What did not change:** two branches lapped onto the same `dev` cannot both land, so the
second goes `dirty` the moment the first merges and needs another lap. That is T-0857, and
it is still open.
