---
id: T-1371
title: Seat the boarders: the single men the household model marked boarding, and new reconstructed lodgers, into the lodging places to their capacities, with each keeper's own household complete
state: done
epic: META
requested_by: owner
seen: true
effort: S
legacy_id: null
parent: T-1175
opened: 2026-09-19
closed: 2026-09-19
pr: 1509
claimed_by: run 9/19/2026, 3:06:59 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-19T10:07:31.927Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35430968124
---

Seat the boarders: the single men the household model marked boarding, and new reconstructed lodgers, into the lodging places to their capacities, with each keeper's own household complete.

Piece 2 of 3 of **T-1175 — Fill the beds: boarders, lodgers, hotel guests, boarding-house keepers' households, the crews of the vessels in port and the hands at the works, seated in the named and reconstructed lodging places to the lodging model's capacities**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Acceptance:** (stated before working — one demonstration, never weakened to pass)

- `tools/seat_lodgers_1835.py --build|--check|--report|--self-test` implements programme
  stage `lodgers`, writes `data/residents/lodgers/` and
  `data/reconstruction/1835_lodgers_seated.json`, re-derives in `tools/check.sh`, and
  REFUSES a house over the lodging model's full capacity, a person seated in two houses,
  an invented name a real person bears, an invented keeper in a documented building, and
  a mint into a house whose division nothing in this dataset states.
- Every built lodging place whose division the dataset settles stands at or above its
  ordinary-night figure and below its crowded ceiling. A bed left empty is NAMED, with
  the reason, rather than filled by a guess.
- The seating order is the parent's: the solitary heads T-1171 and T-1173 already drew
  first, then new reconstructed lodgers against the order book's `lodging` buckets, then
  a keeper for each roof this programme raised as a lodging place. A seat writes nothing
  into a research card.
- Every lodging place's keeper row says who keeps it, how many people stand on their
  card, and the ticket that owes the rest — the title's "household complete", answered as
  a statement rather than a draw, because kin are `family/none` in the order book and
  that quota is T-1171's and T-1174's.

**Result (2026-09-19, PR #1509).** 15 built places, 135 ordinary beds, 30 people on them.
92 beds filled: 17 seated from the layer, 70 lodgers and 5 keepers minted, occupancy
30 → 122. 13 beds left empty and named — the New York House and the Sauganash Hotel,
whose division no committed record gives. 22 order-book buckets filled, none overfilled.
`check.sh` CHECK PASS, 529 steps; `--self-test` 10 of 10.

**Not this piece, refused in writing:** the crews and the pier-works gang and the house
card that prints who lived there (T-1372); a lodger's trade (T-1173); a keeper's family
(T-1171, T-1174); the staff under a keeper (T-1183); the 333 beds of the 37 boarding
houses the programme schedules and has not built (T-1196, T-1187).
