---
id: T-0843
title: Stop the cause: a minting pass must consult the identity master before it writes a card, and --check must fail when a new card's identity already has a canonical one
state: done
epic: META
requested_by: owner
seen: false
effort: S
legacy_id: null
parent: T-0839
opened: 2026-09-05
closed: 2026-09-06
pr: 967
claimed_by: run 9/6/2026, 12:34:17 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-06T06:05:01.136Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34014186285
---

Stop the cause: a minting pass must consult the identity master before it writes a card, and --check must fail when a new card's identity already has a canonical one.

Piece 3 of 3 of **T-0839 — One person, several cards: James Allen stands on four, Gurdon Hubbard on six — 39 surname clusters hold 110 cards that may be fewer people. MERGE them — a report is not the deliverable, the merged cards are — losing nothing**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

---

**CARRIED ACROSS FROM PR #928, 2026-09-05, on the owner's ruling.** #928 filed this as piece
3 of 3 of its T-0839 split and was then closed in favour of #929, which applied the merges
that T-0839 actually asked for ("a report is not the deliverable, the merged cards are").
This piece does not overlap #929 and would have died with the branch: **#929 folds the 42
duplicate cards and gates that every cluster carries a written ruling, but nothing stops a
minting pass writing a NEW duplicate tomorrow.** Its gate is ruling-coverage, not
prevention. So the 42 are cleaned and the cause is untouched, which is why this is ranked in
G1 — the group whose whole job is that the card can be trusted to hold what the spend writes
onto it.

Read #928 before working it: its `tools/merge_resident_cards.py` (793 lines) is the reading
that found the clusters, and is worth diffing against #929's `tools/consolidate_town_cards.py`.

This is the same family as T-0802 (a merged PR's ticket sits `claimed` forever) and dev's
T-0820 (an id used twice is refused on the branch, not on dev): three faults, one cause —
nothing in this project makes a claim or an identity visible before its PR merges.
