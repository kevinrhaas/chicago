---
id: T-1513
title: Seat the policy-only rung: the 1,186 households no source places anywhere, banded by the policy's class rule and dealt a division from the town model — seeded, order-book-counted, and every card's division re-derived so the People view's division filter fills
state: split
epic: TOWN
requested_by: owner
seen: true
effort: S
legacy_id: null
parent: T-1492
opened: 2026-09-21
closed: 2026-09-21
pr: null
claimed_by: run 9/21/2026, 12:15:58 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-21T17:19:13.541Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35629289735
---

Seat the policy-only rung: the 1,186 households no source places anywhere, banded by the policy's class rule and dealt a division from the town model — seeded, order-book-counted, and every card's division re-derived so the People view's division filter fills.

Piece 2 of 2 of **T-1492 — Seat the reach: the address book's reconstructed rungs — a block face for a street-only row, a division band where only the division is known, the policy's band where nothing is — seeded, tier-marked, and every household's division re-derived from its row so the People view's division filter fills**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

1. Every household with no `lives_at` and `division: unplaced` — 1,186 of them on the
   committed layer — reaches rung 5 `policy_only`: the placement policy's band by class
   alone, `tier: reconstructed`, carrying its clause, its seed and its `replaceable_by`,
   and saying in words that no source places this household.
2. The class those households are banded by is DEALT, not read: 1,171 of the 1,393 heads
   carry `occupation: none_recorded`, so the class comes from the town model's own
   occupation distribution, seeded per household, and is counted against the
   reconstruction order book rather than minted free.
3. The division each one reads is re-derived from its row and written back onto the
   household card and `data/residents/index.json`, through the carry slot the mint
   stages use, so the stages that derive a card whole still re-derive it byte for byte.
4. No household that has a rung ≤ 5 seat reads `unplaced`, and **the People view's
   division filter fills**.
5. `--check` in `check.sh`; `--self-test` fires every new assertion.

**Blocked on nothing, but it follows T-1512**, which writes the band vocabulary and the
evidence-bounded rungs this piece deals into.
