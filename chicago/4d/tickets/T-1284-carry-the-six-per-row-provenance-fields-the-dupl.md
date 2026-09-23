---
id: T-1284
title: Carry the six per-row provenance fields the duplicate reconciliation table had into T-1237's rows
state: done
epic: META
requested_by: loop
seen: false
effort: S
legacy_id: null
parent: null
opened: 2026-09-17
closed: 2026-09-17
pr: 1419
claimed_by: run 9/17/2026, 4:47:22 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-17T22:23:56.109Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35278245295
---

T-1147 was split twice, by two runs that could not see each other. T-1237 landed on `dev`
(#1396) and T-1230 did not (#1389, closed as a duplicate) — and both claimed the SAME three
clauses of the parent, ¶1, ¶8 and ¶9.

**dev's table won on coverage and should stay the one table.** Measured:

| table | rows |
|---|---|
| `dev`, T-1237 | 1,704 |
| #1389, T-1230 | 600 |

**But the duplicate's ROW was richer, and that part is worth having.** Six fields it carried
that dev's row does not:

* `ledger` — which committed ledger made this disposition. dev's row carries `sources`, which
  is not the same statement: the ledger is the thing that ADJUDICATED, and naming it is what
  lets a later rung re-read a row without re-adjudicating it.
* `confidence_from` and `confidence_silent_because` — where a grade came from, and, when
  there is none, which ledger is silent about it rather than a bare null.
* `date_precision` and `describes_date_last` — a date's reach, so a span is not read as a day.
* `resolved_street_id` beside `resolved_street`, and `relation` as a field of its own.

Read them from the closed branch:

    git fetch origin steward/t-1146-profile-fact-table
    git show e3916c84c -- chicago/4d/tools/reconcile_locations.py

**Acceptance:** decide field by field, on the evidence dev's rows already hold, which of the
six `tools/location_reconciliation.py` can populate WITHOUT re-adjudicating anything — a field
it would have to guess at is not adopted, and the ticket records why. Add the ones that
survive, re-derive, keep `--check` and `--self-test` green, and state the new row count and
field list. **No disposition changes**: this adds provenance to rows that already exist, and a
row whose verdict moves means something else is wrong.
