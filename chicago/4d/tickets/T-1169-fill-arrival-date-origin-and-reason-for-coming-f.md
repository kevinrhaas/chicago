---
id: T-1169
title: Fill arrival date, origin and reason for coming for every attested and inferred person: the earliest dated appearance as the bound, the biographies where they speak, the arrival model otherwise — dated, tiered and explained
state: done
epic: META
requested_by: owner
seen: true
effort: S
legacy_id: null
parent: null
opened: 2026-09-16
closed: 2026-09-18
pr: 1449
claimed_by: run 9/18/2026, 3:44:16 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-18T09:56:53.909Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35325408410
---

Every household carries `arrival` (1,201 of them `not_later_than` the first letter-list return),
but `origin` is filled on 18 and `reason_for_coming` on none. Stage `arrival` of T-1167's
writer, drawing on T-1165.

**Rules:** attested/inferred arrival, origin and reason from the sources that state them
(old-settler `arrival_year` + `birthplace_as_read` for the 327; Andreas/Fergus biographies in
`data/research/books/`; the 1830 census (present in 1830 → arrival ≤ 1830); the 1832 muster; the
land-sale `residence_as_read`); the `not_later_than` bound kept as the attested/inferred leg;
then the reconstructed leg: an arrival YEAR drawn from the cohort distribution conditional on the
bound and the trade (a forwarding merchant skews 1833–34; a carpenter 1834–35), an origin
community from the pools' shares conditional on the surname's community where the pools carry
it, and a reason from the model's cohort × trade table — each `{ value, tier: reconstructed,
basis, seed }`.

**Acceptance:**

- Every household has arrival (year at least), origin and reason at some tier; per-tier counts
  before/after; the old-settler and biography facts spent onto the cards they name.
- A person whose bound is a single 1835 letter-list return gets an arrival year no earlier than
  the model's cohort allows and the basis says "drawn, not read".
- Visible: the household card's "Came to Chicago / Came from / Why they came" lines are filled
  everywhere, each with its tier.

**Stop condition:** no household reads "Not attested" for arrival, origin or reason without a
reconstructed value beside it.

**Links:** T-1167 · T-1165 · `data/research/old_settlers/people.json` ·
`docs/RESEARCH/resident-grading-policy.md`.
