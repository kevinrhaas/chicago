---
id: T-0597
title: James Kinzie and John Harris Kinzie are half brothers and the two household records do not say so
state: done
epic: META
requested_by: loop
seen: false
effort: XS
legacy_id: null
parent: null
opened: 2026-09-03
closed: 2026-09-05
pr: 899
claimed_by: run 9/5/2026, 10:14:50 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-05T16:53:46.252Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/33973909129
---

James Kinzie and John Harris Kinzie are half brothers and the two household records do not say so.

**The reading.** Hurlbut's bracketed note on an 1821 outfit entry: "[The late James
Kinzie, formerly of Chicago, and half brother of the late John H. Kinzie.]" Filed as
`bk_afc_015`. This project models `hh_kinzie_james` and `hh_kinzie_john_h` as two
separate households and neither record says the two men were related at all.

**Why HALF brother is the point.** It is the specific and easily-flattened form — the same
father, different mothers — and it is the fact that makes the third Kinzie confusion
legible: `data/research/books/crosswalk.json` already has to refuse "Mr. John Kinzie" the
elder silversmith against John Harris Kinzie his son, and a household set that records no
Kinzie relationships at all offers no defence against the next run making that merge.

**What it is not.** A kinship is not a placement. Nothing about either household's
position, arrival, trade or membership changes, and Hurlbut writing in 1881 about 1821 does
not touch the scene date.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)
- Both household records state the relationship, in the form the source gives it — half
  brother, not brother — cited to `chicago_antiquities_american_fur_co` and graded for
  what an 1881 editorial note is worth.
- If the residents schema has no field for a relationship between households, that is the
  finding: say so, add nothing invented, and file the schema question rather than forcing
  the fact into a free-text note nobody can query.
- `tools/check.sh` green.

**Links:** T-0575 · `american_fur_company_hurlbut.json` bk_afc_015 · the "Mr. John Kinzie"
and "the Kinzies" refusals in `data/research/books/crosswalk.json`.
