---
id: T-1433
title: Seat the reconstructed residents who have a trade and no workplace: each at a business of their trade in their division, nearest first and seeded, and the no-fixed-premises trades given their implied employer or a casual entry with its reason
state: done
epic: META
requested_by: owner
seen: true
effort: S
legacy_id: null
parent: T-1189
opened: 2026-09-20
closed: 2026-09-20
pr: 1563
claimed_by: run 9/20/2026, 4:57:28 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-20T11:21:25.426Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35503586653
---

Seat the reconstructed residents who have a trade and no workplace: each at a business of their trade in their division, nearest first and seeded, and the no-fixed-premises trades given their implied employer or a casual entry with its reason.

Piece 2 of 3 of **T-1189 — Staff every business — attested, inferred and reconstructed — with real persons: attested partners and clerks first, then the reconstructed residents, then new reconstructed staff to the staffing model, so every working person has a workplace and every workplace its people**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

1. Every reconstructed resident with a trade and no `workplaces` carries exactly one
   `employment` block — across all seven directories of the resident layer, not just
   `households/`, because 308 of them stand in `reconstructed_trades/`.
2. A block either NAMES a house the business layer already holds, with the role the
   staffing model gives that trade in that class of house, or it states in the words
   of the ruling that decided it why no house can be named. No blanks.
3. No house takes more hands in a role than the staffing model's own `count_high` for
   it. The overflow is reported as a town owed more houses, never as a fuller house.
4. Nobody is minted, no business is raised and no business record is written to. The
   `staff[]` side of the join is T-1434's, after the shortfall is minted.
5. The order rule is stated in full and the report counts which of its three terms
   actually decided each seat, so a term that is inert against today's layer is
   visible as inert rather than assumed to have worked.
6. `--check` re-derives every block and the report byte for byte and is in
   `tools/check.sh`; `--self-test` fires all five assertions.

**What it demonstrated.** 524 people answered: 124 seated in 84 houses, 162 owed
premises of their own, 162 with no employer nameable, 71 whose class of house is full
to its band, 5 whose trade `premises_rulings.json` has never ruled on. Of the 124
seats, division decided 0 and distance decided 1 — no business record carries a
division (the order book reserves that to T-1182 and T-1198) and 12 of 414
reconstructed households are seated (T-1198, T-1199). The remaining 123 are a seeded
draw and say so.

**Findings handed on.**
- Five trades in the resident layer's occupation vocabulary — barber, cook, drayman,
  waiter, whitewasher — have no premises ruling. T-1404 owns that table.
- 62 of the 76 reconstructed domestics cannot be seated: the taverns and hotels that
  employ them are full to the model's high band. That is an order-book quantity and
  T-1434 is where it is answered.
- `tools/staff_businesses_1835.py` reads only `data/residents/households/`, so a
  business row naming a person who stands in one of the other six directories would
  join nothing. No such row exists today; T-1190's convergence is where it would show.
