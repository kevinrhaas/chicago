---
id: T-1432
title: The attested and inferred half of the staffing join: one tool writes staff[] on every business a source names a hand for and works_at[] on every person the business layer already ties to a workplace, at their own tiers and sources, and the person card prints where they worked
state: done
epic: META
requested_by: owner
seen: true
effort: S
legacy_id: null
parent: T-1189
opened: 2026-09-20
closed: 2026-09-20
pr: 1559
claimed_by: run 9/20/2026, 3:23:17 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-20T09:39:36.567Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35499137151
---

The attested and inferred half of the staffing join: one tool writes staff[] on every business a source names a hand for and works_at[] on every person the business layer already ties to a workplace, at their own tiers and sources, and the person card prints where they worked.

Piece 1 of 3 of **T-1189 — Staff every business — attested, inferred and reconstructed — with real persons: attested partners and clerks first, then the reconstructed residents, then new reconstructed staff to the staffing model, so every working person has a workplace and every workplace its people**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)


**What this piece is, and what it is not.** The business layer already names 196 people
in 197 records — 111 proprietors, 85 partners and one apprentice — and 144 of those rows
carry a `person_id`, 110 distinct town cards between them. The register knows where those
people worked. **Their own cards do not.** `persons[]` has never held a workplace at all:
`works_at` exists only on the HOUSEHOLD, where it is a singular structure id — a PLACE, and
undated — so a man who kept a store and a card that says nothing about a store are the same
record read from two ends, and nothing gates them against each other. This piece writes the
join down and puts a gate on it.

**THE FIELD IS `workplaces`, NOT `works_at`, AND THE PARENT'S WORDING IS WHY THIS SAYS SO.**
T-1189 asks for `works_at[]` on the person. That name is already taken and already means
something else: `works_at` is a SINGULAR, UNDATED structure id — the building — and
`validate.py` and `associations.py` police it as one on persons as well as households.
A list of dated employments under that name would have been refused by the gate as a
malformed link, and would have read as a second opinion about the same field. So the
BUILDING keeps `works_at` and the FIRMS get `workplaces`. Two questions, two words.

It mints nobody: the reconstructed seatings are T-1433's
and the model's shortfall is T-1434's.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

- `tools/staff_businesses_1835.py --build|--check|--selftest` exists and is the only writer
  of `persons[].workplaces`. `--build` is deterministic and re-runnable to a byte; `--check`
  re-derives and exits non-zero on any drift.
- Every business person row that carries a `person_id` — proprietor, partner or staff — has
  a matching `workplaces[]` entry on that person's card, carrying the business id and name, the
  role in the business layer's own word, the date bracket the record gives it, and the row's
  OWN tier and source. Nothing is upgraded: an `inferred` row joins as `inferred`.
- The join is bidirectional and `--check` asserts it BOTH ways: no `workplaces[]` entry without
  a business record naming that person back in that role, and no named row without its entry.
  A row whose `person_id` is null is a statement about the evidence and stays one — it is
  counted in the report, never invented into a card.
- `tools/check.sh` runs `--check`; `--selftest` mutates the join four ways (a dropped entry, an
  entry naming a business that does not name it back, a flipped role, an upgraded tier) and
  each mutation must make the check fail.
- `tools/validate.py` validates the shape of `persons[].workplaces`: the keys, a `role` from the
  businesses schema's role enum, a tier from the residents vocabulary, and a `business_id` that
  resolves.
- Report `data/reconstruction/1835_staffing_join.json`: rows written by role and tier, persons
  tied, businesses with people and without, the unresolved printed names counted rather than
  guessed, and the shortfall against the staffing model left standing with the ticket that owns it.
- `writes_no_person: true` in the report, and `--check` refuses the file if any `workplaces` entry
  sits on a person no business row names.
- **Visible:** a person's own row in the household record on the People card now prints where
  they worked — the firm, their role there, the bracket and the tier chip — and opens its sources.
  It printed nothing about work before this.
