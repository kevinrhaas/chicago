---
id: T-0594
title: Hubbard's arrival year is graded 'reconstructed' citing nothing, and Hurlbut prints the sentence it wanted: Montreal 13 May 1818, Mackinaw 4 July, Chicago the last day of October or first of November
state: done
epic: META
requested_by: loop
seen: false
effort: S
legacy_id: null
parent: null
opened: 2026-09-03
closed: 2026-09-04
pr: 821
claimed_by: run 9/4/2026, 5:40:37 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-04T23:34:41.300Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/33926193693
---

Hubbard's arrival year is graded 'reconstructed' citing nothing, and Hurlbut prints the sentence it wanted: Montreal 13 May 1818, Mackinaw 4 July, Chicago the last day of October or first of November.

**What is wrong.** `data/residents/households/hh_hubbard_gurdon.json` carries
`arrival: 1818` at confidence `reconstructed`, and its note says so in as many words:
"NOT ATTESTED IN ANYTHING WORKED FOR THIS PARCEL. Hubbard's arrival with the American
Fur Company as a boy is a commonplace of the Chicago literature and Andreas's own
chapter calls him the oldest living resident; the year could not be traced to a
sentence here, so it is carried as a conjecture citing nothing and flagged for a later
parcel to fix or delete."

**The sentence exists now.** T-0575 read Hurlbut's *Chicago Antiquities* pages 28-36 and
filed it as `bk_afc_004`: "Mr. Hubbard left Montreal, were his parents then lived, May
13, 1818, reaching Mackinaw, July 4 and first arrived at Chicago on the last day of
October or first day of November of that year." The same claim gives his birth — Windsor,
Vermont, 1802, to Elizur and Abigail (Sage) Hubbard — which the household record does not
hold either. The identity is adjudicated: `data/research/books/crosswalk.json` merges
"Gurdon S. Hubbard" into this project's "Gurdon Saltonstall Hubbard" on three agreements.

**What it is not.** Arriving at Chicago in 1818 is not residing at Chicago in 1835, and
Hurlbut is a source of 1881. Under the ladder ratified 2026-09-03 this DATES an arrival
the record already asserts; it does not add a person, a placement or a household member.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)
- `hh_hubbard_gurdon.json` `arrival` cites `chicago_antiquities_american_fur_co` and is
  graded on what the source actually is — a near-primary recollection at sixty years'
  distance — with the note replaced by the reading rather than by the commonplace.
- **The source's own ambiguity survives**: "the last day of October or first day of
  November" is two days and not one, and a `precision` of `year` that quietly drops it is
  the failure to avoid. A date this reconstruction cannot resolve is written as unresolved.
- Nothing else in the household moves — no placement, no `works_at`, no household member.
- `tools/check.sh` green.

**Links:** T-0575 · `data/research/books/claims/american_fur_company_hurlbut.json`
bk_afc_004 · `data/research/books/crosswalk.json` (the Hubbard merge and its
`does_not_follow`, which defers exactly this change to this ticket).
