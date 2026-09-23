---
id: T-1420
title: build_order_book_1835.py hands the west ground units to T-1192, which is now split: the owner list needs its live successor T-1414 (and the same sweep for any other ticket id the order book names that has since closed or split)
state: done
epic: META
requested_by: loop
seen: false
effort: XS
legacy_id: null
parent: null
opened: 2026-09-19
closed: 2026-09-21
pr: 1609
claimed_by: run 9/20/2026, 11:53:24 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-21T06:02:32.039Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35562381510
---

build_order_book_1835.py hands the west ground units to T-1192, which is now split: the owner list needs its live successor T-1414 (and the same sweep for any other ticket id the order book names that has since closed or split).

**Acceptance**, stated 2026-09-21 before working:

1. Every ticket id `build_order_book_1835.py` emits as a WORK ORDER — a bucket's
   `owning_ticket`, `owning_tickets` or `ground_waits_on`, on a bucket that still has
   work left — names a ticket a run can claim (`open`, `claimed`, `review`,
   `blocked-owner`, `blocked-tech`). The west ground reaches T-1414.
2. Each dead id is resolved by READING the ticket tree to its live frontier, and the
   reading is written beside the table. No confidence, no ownership and no modelling
   decision is invented to make a row look owned; where the frontier is empty the
   table says so rather than naming a ticket that cannot act.
3. Backward-looking ticket stamps do not move. `fills[].ticket`, `recut_refusals`,
   `programme_deltas`, `roster_offered.tickets` and the book's own `ticket` record who
   did the work or made the ruling; rewriting provenance to quiet a gate is the worse
   defect and is refused here by name.
4. It cannot silt again: `--check` and `--build` refuse a dead work order, `--self-test`
   fires that guard on `done`, `split`, `withdrawn` and an id that is no ticket at all,
   and holds the three cases that must NOT fire — a blocked owner, a discharged bucket,
   and a provenance stamp.
5. The book and its report re-derive byte for byte, the gate is green, and the mirror
   is published in the same commit.

**What the sweep found.** Thirteen of the twenty-four ids the owner tables named had
closed or split. Only two carried work left, and both are fixed here: the ground table
(T-1191 and T-1194 arrived; T-1192 → T-1414; T-1193 → T-1444, West-Division-only by its
own chain's titles, so the north's remaining wait is owned by nobody and the table is
empty rather than wrong), and the bed buckets, whose 278 persons lost their owner when
T-1175 split — filed as T-1500. The other eleven sit on discharged buckets and keep
the id of the ticket that discharged them.
