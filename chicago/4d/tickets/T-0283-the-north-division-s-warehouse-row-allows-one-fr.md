---
id: T-0283
title: The North Division's warehouse row allows one freight roof and six documented ones stand above it
state: done
epic: TOWN
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-08-28
closed: 2026-08-29
pr: 511
claimed_by: run 8/29/2026, 12:21:17 AM CT
blocked_on: null
needs_bake: false
---

The North Division's warehouse row allows one freight roof and six documented ones stand above it.

Found and measured by T-0211 (`tools/measure_group_district_rows.py`), which declares the
breach as a ratchet so it cannot grow, and does NOT repair it — repairing it is a decision
about the authored target, which is this ticket.

`district_group_matrix.warehouses_freight.north` is **1**. Seven freight roofs stand in the
North Division and **six of the seven are documented pre-existing records**: Kinzie & Hunter's
warehouse, the four north-bank sheds at the Dearborn reach (`north_bank_shed_dearborn_e1`,
`e2`, `e3`, `w`) and `brickyard_north_side`. The seventh, `recon_1835_north_f1_022`, is a
generated F1 roof dealt before anything measured this. The row was authored without the north
bank's river-freight fabric in view.

**Why it is not a one-number edit.** The matrix's cells sum to their group's `total` AND to
their division's `target` — both now asserted by T-0211's gate — and the division targets sum
to `roof_total` (662). Raising the North's freight cell by six means finding those six roofs
somewhere: from another North group's cell (which division reads as the same 152 roofs
re-typed), or from another division (which moves two district targets), or from the total
(which moves the authored programme). The three are different claims about the town and the
sources answer them differently.

The live cost, measured: the clamp in `reconcile_665.py` sheds seven North slots — the six here
plus the one institutional overshoot L93 explains — out of the North's **ordinary dwellings**,
so the North is scheduled seven houses short for a reason that until T-0211 appeared nowhere.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

- `warehouses_freight.north` equals what the North's documented freight fabric supports, with
  the six records named and the re-balancing stated: which cells gave up the roofs and on what
  source basis, or an explicit finding that the total itself moves and by how much.
- `reconcile_665.py` re-derives green, `remaining.district_group_rows_overshot` no longer
  carries `north.warehouses_freight`, and `remaining.district_group_slots_shed` falls by six.
- `tools/measure_group_district_rows.py` passes with the declaration RETIRED from
  `DECLARED_OVERSHOOT`, not merely lowered.
- The institutional cell is NOT in scope: it is L93's anonymous school and it moves when that
  liberty is retired.
