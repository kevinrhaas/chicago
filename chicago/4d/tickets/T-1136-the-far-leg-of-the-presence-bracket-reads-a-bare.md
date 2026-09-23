---
id: T-1136
title: The far leg of the presence bracket reads a bare year at the year's END, so a death on 8 April 1835 closes the bracket over 1 July
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-14
closed: 2026-09-17
pr: 1376
claimed_by: run 9/16/2026, 11:27:33 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-17T05:00:03.458Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/35181837149
---

The far leg of the presence bracket reads a bare year at the year's END, so a death on 8 April 1835 closes the bracket over 1 July.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

Found by T-1131, which ruled which evidence CLASS may stand on which leg of the presence
bracket and left this, which is a DATE defect on the same bracket.

**THE DEFECT.** `mint_civic_residents.bound_of()` returns "the latest day a
`describes_date` permits" — a bare `1835` becomes `1835-12-31`. That is right for an
arrival bound, which is a `not_later_than`, and `presence_block` uses the same number for
BOTH legs. The at-or-before leg wants the latest permitted day and gets it. The at-or-after
leg wants the EARLIEST permitted day and gets the latest, so a record that may describe any
day of 1835 is read as describing 31 December 1835 and is allowed to close a bracket over
1 July.

**MEASURED ON DEV AT 8bd9bbc47.** One card is wrong today: `hh_vanderbogart_henry` reads
`present`, and its only at-or-after leg is a death notice dated `April 8, 1835` — three
months BEFORE the scene date — read as 1835-12-31. Its at-or-before legs are real
(a newspaper of 1834-02-04, a letter list of 1835-05-20), so under an honest reading it
has no far leg at all and should read `uncertain`.

**THE TRAP, AND IT IS WHY THIS IS NOT A ONE-LINE FIX.** Giving the after leg the earliest
permitted day withdraws every bracket whose far leg is a bare year — `poll_1835`,
`directory_1843`, `census_1840` are all bare years in the identity master, and
`1843-01-01` is still after the scene date so those survive, but `poll_1835` becomes
`1835-01-01` and stops closing the bracket for everyone who rests on it. COUNT IT BEFORE
WRITING IT, both ways, and if the honest reading withdraws a large cohort that is a
finding to state rather than a reason to weaken the rule.

- Both legs read the end of the date range that is honest for that leg, and the ruling
  says which end and why.
- The cohort each direction moves is counted before it is written, and the count is in
  the PR.
- `hh_vanderbogart_henry` no longer reads `present` on a death three months before the day.
- A death notice's printed date is read for its month and day where the page gives them
  (`April 8, 1835`), not only for its year — or the ticket says why it is not.
- The rule fires in `mint_civic_residents.py --self-test` and asserts on the tree in
  `--gate`. No card hand-edited; `--check` re-derives byte for byte.
- `bash tools/check.sh` green. No bake.
