---
id: T-0679
title: Fergus 1839's Fort Dearborn lot sale has 62 rows with no lot number and 22 with no price: settle the destroyed numerals off the page images
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-04
closed: 2026-09-04
pr: 815
claimed_by: run 9/4/2026, 4:37:12 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-04T21:55:51.552Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/33918590509
---

Fergus 1839's Fort Dearborn lot sale has 62 rows with no lot number and 22 with no price: settle the destroyed numerals off the page images.

T-0666 read printed pages 47-49 — LOTS SOLD IN FT. DEARBORN ADDITION, 10-24 June 1839 —
out of archive.org's OCR, putting the four columns back from the scan's word coordinates.
267 printed rows, 100 named bidders. What it could not do is read numerals the scan
destroyed, and it refused rather than repaired them:

- **62 rows carry no lot number.** Printed page 49's left-hand lot column is readable for
  two lines and then collapses into rotated type — `<J\Ui`, `00^1`, `In)`, `Oo`, `4-`.
  Because the block number is carried only while the lot numbers keep rising, those rows
  lose their block too, and blocks 11 and 12 are not identified at all: their headings sit
  inside the ruined column.
- **22 rows carry no price.** `3°3`, `jjj`, `43i`, `5io`, `35o`, `47°`, `268^`.
- **The population table's 1840 line is gone**, year and figure both: it prints
  `1 S40 .... 4,47!*`.
- **And one numeral is read WRONG rather than refused**, which is worse: block 9's lot 30
  scans as `70`, a number that parses, and nothing in the reading can tell a clean numeral
  from a clean-looking ruin.

All of it is settled by looking at the page images, which nobody has done for these three
sheets. `data/research/directories/claims/fergus_1839_ft_dearborn_lots.json` keeps every
one of these cells verbatim in `normalized.as_printed`, so the work is to read the ink and
fill the null beside it — and to regrade those rows `scan_verified`, which outranks the
`transcription_mediated` the whole file carries now.

**Acceptance:** the lot numbers and prices of printed pages 47-49 read off the page images,
`reading` regraded on the rows that were checked, and the file still rebuilding through
`tools/read_fergus_1839_lots.py --check`. The reading tool would need a committed
corrections layer for that — the claims are generated, so a hand-edit is not the way in.
