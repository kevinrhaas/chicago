---
id: T-1405
title: Persons' other significant locations as associated_with[]: civic seats held, church membership and office, agencies held, land purchased and schools taught, each with kind, place, dates, tier and source — counts before and after
state: done
epic: META
requested_by: owner
seen: true
effort: S
legacy_id: null
parent: T-1182
opened: 2026-09-19
closed: 2026-09-19
pr: 1540
claimed_by: run 9/19/2026, 5:19:16 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-19T23:21:59.683Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35472811308
---

Persons' other significant locations as associated_with[]: civic seats held, church membership and office, agencies held, land purchased and schools taught, each with kind, place, dates, tier and source — counts before and after.

Piece 5 of 5 of **T-1182 — Audit every attested and inferred business against the research: proprietors, partners, dates, primary and secondary premises, the Dec 1835 State census classes and the August 1835 American count — and raise an inferred business for every in-window trade that has none**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

The parent's clause 2, unchanged (the owner's "any other locations they were
significantly involved in"): for every person, the civic offices held and where they sat
(the council house, post office, land office, court — `civic_public_buildings_1835.md`),
church membership/office, agency holdings (`1835_agencies.json`), land purchased
(`1835_land_sales_by_tract.json`), schools taught — written as `associated_with[]` on the
person with kind, place/structure id, dates, tier and source. Counts before/after
printed.

The shape and its gate already exist (T-1238, `tools/associations.py`,
`data/research/residents/association_coverage.json`): 4 records, 7 rows, 9 kinds in the
vocabulary. That file is the before number.

