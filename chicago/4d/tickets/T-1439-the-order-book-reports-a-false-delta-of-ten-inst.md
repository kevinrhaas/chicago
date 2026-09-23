---
id: T-1439
title: The order book reports a false delta of ten institutional roofs: programme_deltas reads the town model's institutional HIGH end, which includes the fort's ten principal roofs, against district_group_matrix.institutional_public alone — and the boarding-house row beside it compares that matrix with a figure read off the same matrix, so it can never disagree
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-20
closed: 2026-09-20
pr: 1607
claimed_by: run 9/20/2026, 9:30:12 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-21T03:05:14.434Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35554196596
---

The order book reports a false delta of ten institutional roofs: programme_deltas reads the town model's institutional HIGH end, which includes the fort's ten principal roofs, against district_group_matrix.institutional_public alone — and the boarding-house row beside it compares that matrix with a figure read off the same matrix, so it can never disagree.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

1. `programme_deltas`' `institutional_and_public` row sums BOTH matrix groups the model's
   high end counts — `institutional_public` (9) and `fort_principal` (10) — so the row
   reads 19 against 19 and the delta of ten is gone from the book, the report and the
   Order book panel.
2. Every delta row carries `programme_groups`, the `district_group_matrix` groups summed
   on its programme side, so a group left off one side again is visible in the artefact
   rather than only in the arithmetic.
3. Every delta row carries `restates_the_programme`, DERIVED rather than hand-asserted:
   true when the model figure names the roof programme among its `derived_from` sources
   AND lands exactly on the groups it is compared against. `boarding_houses` and
   `institutional_and_public` are true; `inns_and_taverns` names the same file but goes
   past it (15 against 10) and is false.
4. A restating row says so in its own prose (`NOT A CHECK:`), and a row whose flag and
   sentence disagree, or that restates and still reports a non-zero delta, is a Fault —
   so the two cannot drift apart silently.
5. A programme side naming a matrix group that does not exist is a Fault, not a silent
   nought.
6. `--self-test` fires on each of those two faults; `check.sh` green; the re-derivation's
   `owed_out` rows re-pointed at what is still genuinely owed (an independent count of
   the boarding and institutional roofs, to T-1196) rather than at the comparison bug.

**What was wrong.** `model_town_1835.build_lodging` reads `larger_boarding_houses`,
`inns_taverns`, `institutional_public` and `fort_principal` straight out of
`district_group_matrix`. The institutional figure is `low = institutional_public` and
`high = institutional_public + fort_principal`. The order book compared that high end
against `institutional_public` alone, so it charged the roof schedule ten roofs it had
already scheduled under the fort. Correcting the units gives 19 against 19 — and that
zero is a restatement, not an agreement, for exactly the reason the boarding-house row
beside it was one. Both are now printed as restatements instead of passes.
