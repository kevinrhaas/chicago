---
id: T-0523
title: The 1840 census images 26-50: inventory all 25 sheets and read the names on the two pages PR #670 already read
state: done
epic: META
requested_by: owner
seen: false
effort: S
legacy_id: null
parent: T-0495
opened: 2026-09-03
closed: 2026-09-03
pr: 683
claimed_by: run 9/3/2026, 1:57:14 AM CT
blocked_on: null
needs_bake: false
---

The 1840 census images 26-50: inventory all 25 sheets and read the names on the two pages PR #670 already read.

Piece 1 of 7 of **T-0495 — The 1840 census deposit is 75 page images and 210 heads on seven printed pages are the only names read from it: images 26-50**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**What this piece is.** The 25 images of group 26-50 declared in `data/research/census_1840/coverage.json`
with what each one actually is — left sheet or continuation, printed page number, lines carrying an
entry, blank or cancelled — and the NAMES of the two pages in this group that PR #670 already read
(printed 230, `33S7-9YYJ-NY`; printed 232, `33S7-9YYJ-W6`), line by line, cross-checked against #670's
62 rows for those two pages.

**Why this one first.** #670's 210 rows are the calibration set the parent ticket says the reading
"must reproduce before it extends". If they do not reproduce, every later piece — and T-0504's serial
fingerprint and T-0505's crosswalk — is resting on a transcription nobody has checked.

**Acceptance:** (one demonstration, never weakened to pass)
- 25 of 25 images declared, each with sheet side, printed page (or `null`), line count and what it is.
- 62 of 62 lines on the two calibration pages carry an `as_read`, a `normalized`, a
  `name_confidence` and `reading: scan_verified`.
- The agreement count against #670 stated, with every disagreement listed and neither reading deleted.
