---
id: T-0534
title: The 1840 census images 1-25: the age-band, coloured and industry cells of printed pages 229, 231 and 234, checked against the sheets' own column totals
state: split
epic: META
requested_by: owner
seen: false
effort: S
legacy_id: null
parent: T-0494
opened: 2026-09-03
closed: 2026-09-03
pr: null
claimed_by: null
blocked_on: null
needs_bake: false
---

The 1840 census images 1-25: the age-band, coloured and industry cells of printed pages 229, 231 and 234, checked against the sheets' own column totals.

Piece 4 of 5 of **T-0494 — The 1840 census deposit is 75 page images and 210 heads on seven printed pages are the only names read from it: images 1-25**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

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

- `pages/33S7-9YYJ-9M5.json`, `-38.json` and `-99F.json` gain a `cells` object on every record; the
  NAMES already committed there are not rewritten except where reading the cells corrects a line
  position, and any such correction is stated.
- Per page, per column: the sum of the lines read against the enumerator's own printed total, and
  the residual where they differ.
- Page 229 is the one to watch: the sheet carries 30 ruled entries and #670 carries 31 rows for it.
  The column totals are the independent test of which count is right, and settling it is worth more
  than the cells themselves. Say what they settle.
- `cells_state` set to `read` only on a page whose columns balance.

**Links:** `data/research/census_1840/README.md` · `coverage.json` group `images 1-25 of 74` ·
`crosswalk_670.json` · `claims.json` · T-0492 (the shared research-domain shape) · T-0504 (serial
mapping) · T-0505 (crosswalk to 1835) · T-0507 (composition calibration) ·
`data/sources/census_1840_chicago_familysearch_images.json`

**Note, 2026-09-03.** The run that claimed this ticket before the split (PR #698) read all three pages
to the cell. Its 234 landed as T-0551; its 229 and 231 arrived after T-0550's reading of the same two
pages (PR #697) and disagree with it on 20 and 25 lines — kept verbatim in
`data/research/census_1840/second_readings/`, reconciled by T-0559.
