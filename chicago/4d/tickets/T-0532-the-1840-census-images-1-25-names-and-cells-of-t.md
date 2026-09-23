---
id: T-0532
title: The 1840 census images 1-25: names and cells of the left sheets printed 221, 222 and 226
state: done
epic: META
requested_by: owner
seen: false
effort: S
legacy_id: null
parent: T-0494
opened: 2026-09-03
closed: 2026-09-03
pr: 690
claimed_by: run 9/3/2026, 5:36:52 AM CT
blocked_on: null
needs_bake: false
---

The 1840 census images 1-25: names and cells of the left sheets printed 221, 222 and 226.

Piece 2 of 5 of **T-0494 — The 1840 census deposit is 75 page images and 210 heads on seven printed pages are the only names read from it: images 1-25**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

**What the parent pass already did, so this ticket does not redo it.** T-0494's run declared all 25
images of group 1 in `data/research/census_1840/coverage.json` (kind, printed page, line count),
transcribed the NAMES of the three pages PR #670 also read (229, 231, 234), read printed page 206 —
the certificate and recapitulation sheet — in full, declared the blank page 238, and corrected the
deposit count to 74 distinct images in 75 files. Read that coverage group and
`data/research/census_1840/README.md` first; the inventory line counts there are stated to the
nearest line and this ticket restates its own pages exactly.

**The rules, unchanged from the parent.** `as_read` preserves position — an unread letter is `[?]`,
never an absence (T-0397). `normalized` expands the abbreviation and keeps the `[?]`.
`name_confidence` is `high | medium | low` and is about the LETTERS. `reading: scan_verified`.
Enumeration order is data: never reorder lines, and record a blank or illegible line rather than
skipping it. No IPUMS serial is attached here — T-0504 does that. Nothing here mints or regrades an
1835 resident: the 1840 census is LATER EVIDENCE and the owner's ratified ladder is explicit that
"1839/1840 alone is never a 1835 resident". Do not commit images or crops; the deposit is read-only.
Town findings — any business, street, landscape or appearance fact — go in
`data/research/census_1840/claims.json` with `town_finding: true`, verbatim quote and locator.

**Reading the cells.** The 26 free-white age-band columns are narrow and a mark one column off is a
person of the wrong age, so a cell reading is only committable once it is checked against the
PRINTED COLUMN TOTALS at the foot of the sheet. State the check: per column, the sum of the lines
you read against the figure the enumerator wrote. Where they disagree, say so and leave the column
`illegible` rather than forcing it — a half-checked row is worse than an unread one. Set
`cells_state: "read"` only on a page whose columns balance, and record the residual per column where
they do not.

- The three pages have `pages/<id>.json` files with every ruled line recorded, readable or `illegible`.
- The line count per page is restated exactly and reconciled with the coverage inventory's figure.
- The name-confidence distribution is stated.
- Column totals checked per the cells rule above; `cells_state` set honestly per page.
- Coverage group 1's `read_state` and `page_file` updated for these three images.

**Links:** `data/research/census_1840/README.md` · `coverage.json` group `images 1-25 of 74` ·
`crosswalk_670.json` · `claims.json` · T-0492 (the shared research-domain shape) · T-0504 (serial
mapping) · T-0505 (crosswalk to 1835) · T-0507 (composition calibration) ·
`data/sources/census_1840_chicago_familysearch_images.json`
