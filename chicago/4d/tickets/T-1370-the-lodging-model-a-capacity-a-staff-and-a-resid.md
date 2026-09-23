---
id: T-1370
title: The lodging model: a capacity, a staff and a resident mix for every lodging place the town holds, derived from its own record and shown on its card
state: done
epic: META
requested_by: owner
seen: true
effort: S
legacy_id: null
parent: T-1175
opened: 2026-09-19
closed: 2026-09-19
pr: 1504
claimed_by: run 9/19/2026, 12:24:55 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-19T06:18:35.359Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35423674899
---

The lodging model: a capacity, a staff and a resident mix for every lodging place the town holds, derived from its own record and shown on its card.

Piece 1 of 3 of **T-1175 — Fill the beds: boarders, lodgers, hotel guests, boarding-house keepers' households, the crews of the vessels in port and the hands at the works, seated in the named and reconstructed lodging places to the lodging model's capacities**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Acceptance:**

- `tools/build_lodging_model_1835.py --build|--check|--self-test` writes
  `data/reconstruction/1835_lodging_model.json` and its report, re-derives in `tools/check.sh`,
  and REFUSES a total outside the town model's own 468–1,232, a place that sleeps nobody, or a
  place given more beds than the largest household of 1840.
- Every lodging place the dataset holds carries an ordinary-night and a full capacity, at the
  weakest grade of the claims under it, with its basis and what would retire it.
- Visible: the card of each lodging place prints both numbers and the derivation.

**The staff is NOT in this piece, despite the title.** The business staffing model is T-1183 and
it is open; a bar-keeper, hostler, cook and chambermaid invented here would be that ticket's
answer given by a tool with no licence to give it. The model records the omission and names
T-1183 as its owner. The title was written at `split` time, before that dependency was read.

**What it found.** The town model's bed bracket rests on 42 roofs grouped as
`larger_boarding_houses`, and 32 of them are families the archetype crosswalk — and the built
records' own `function` — call houses. Filed as an open question against T-1293 and T-1196
rather than settled here. The inn programme is complete at 10 of 10; the boarding-house
programme is 5 of 42, so 333–777 of the town's beds are scheduled rather than standing.
