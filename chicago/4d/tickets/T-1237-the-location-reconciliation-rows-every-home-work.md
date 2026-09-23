---
id: T-1237
title: The location reconciliation rows: every home, workplace and business-location claim resolved to street, face and anchor, with the clause that limited it
state: done
epic: META
requested_by: owner
seen: true
effort: S
legacy_id: null
parent: T-1147
opened: 2026-09-17
closed: 2026-09-17
pr: 1396
claimed_by: run 9/17/2026, 7:47:09 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-17T13:50:15.545Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35222324991
---

The location reconciliation rows: every home, workplace and business-location claim resolved to street, face and anchor, with the clause that limited it.

Piece 1 of 5 of **T-1147 — Spend every defensible home, workplace and business-location finding, preserve the 123 location limits, and close research with zero unclassified attested or inferred fact**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Acceptance:** (T-1147 clauses 1, 8 and 9; clauses 2-7 belong to T-1238..T-1241)

1. One reconciliation row per home, workplace and business-location claim the committed
   dataset holds, derived and never authored: household `lives_at` and `works_at`, the
   later-directory `address_later` readings with their back-projection ruling, the
   scene-date register's business locations, and the street-face adoptions and refusals.
   Each row carries source ids, claim id, `describes_date`, the resident/household/business
   ids, the printed place, and its resolved street, face, anchor and structure.
2. Every row keeps `resolved_street`, `resolved_face`, `resolved_anchor` and the
   `limit_clause` that stopped it going further, so T-1198's address book starts here and
   no later rung has to re-adjudicate the evidence (T-1147 clause 8).
3. Later directory addresses appear as rows and are NOT 1835 placements unless the
   committed back-projection rule explicitly fired; the row states which clause fired or
   refused. No row invents a coordinate, a lot or an anchor the sources do not carry.
4. The report states the three business location-limit counts (structure / street-only /
   unplaceable) and the household seating classes (structure / lot / face / division /
   none), which T-1157 reads as the sign-off's location axis (T-1147 clause 9).
5. `--check` re-derives the committed file and refuses a hand-edit; `--self-test` breaks
   its own assertions and requires them to fire; both are wired into `tools/check.sh`.

**Stop condition:** a run that wants the address book has one derived file to read, and
every location claim in the dataset is on a row that states how far the evidence reached.

**Links:** T-1147 (parent) · T-1143 · T-1198 · T-1157 · T-0354 · T-0384.
