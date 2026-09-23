---
id: T-1296
title: Rule the 1,572 land-sale purchaser units: a sale is never a residence, so say what each row does and does not bound
state: done
epic: META
requested_by: loop
seen: false
effort: S
legacy_id: null
parent: T-1236
opened: 2026-09-17
closed: 2026-09-17
pr: 1421
claimed_by: run 9/17/2026, 5:37:19 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-17T23:23:30.063Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35281931694
---

Rule the 1,572 land-sale purchaser units: a sale is never a residence, so say what each row does and does not bound.

Piece 1 of 3 of **T-1236 — EPIC: rule on the unasserted units the person-fact passes do not own — the land-sale, civic, 1830-census, church, newspaper and directory names, the resident-pass reserved people, and the book readings of ground, harbour, weather, price and institution**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

1. Every one of the 1,572 `land_sales` units the ledger owns to this ticket carries a
   WRITTEN ruling — a named rule with a stated reason, and a note on that unit saying
   why THIS row fell under it — in the shape `data/research/spend_rulings.json`
   established. A silent reclassification is a fail.
2. No ruling upgrades a confidence, mints a person or invents a citation. The identity
   question is NOT reopened: the ruling reads
   `data/research/land_sales/resident_crosswalk.json`'s adjudicated `ruling` blocks
   (T-0700 / T-0850) and re-adjudicates nothing.
3. The standing rule holds in every row: **a purchase is a transaction and not a
   residence.** A row may bound a presence and may never assert one.
4. The rulings are DERIVED, not typed — a tool rebuilds them from the committed records
   and crosswalk, and `--check` proves nothing drifted.
5. `python3 tools/measure_research_spend.py --check` stays green and the ledger carries
   no `land_sales` unit owned by this ticket.

**The corpus:** 1,572 rows, all `unresolved`, in three files —
`data/research/land_sales/records/entries_cook_town_lots_through_1836.json` (619),
`entries_t39n_t40n_r14e_through_1836.json` (566) and
`entries_t39n_t40n_r13e_t38n_t41n_r14e_t38n_r15e_through_1836.json` (387).
Residence column: UNKNOWN 1,459 · COOK 58 · nine other counties or states 55.
Purchase dates: 496 after 1836-01-01, 419 in 1835, 648 in 1830-1834, 8 unreadable.

**Links:** T-1236 (parent) · T-1234 (the pass that filed it) · T-0557 / T-0676 / T-0700 /
T-0850 (the crosswalk and its adjudications) · T-1169 · T-1159.
