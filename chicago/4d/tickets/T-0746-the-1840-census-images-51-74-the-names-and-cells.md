---
id: T-0746
title: The 1840 census images 51-74: the names and cells of the sheets the inventory finds, read line by line
state: split
epic: META
requested_by: owner
seen: false
effort: S
legacy_id: null
parent: T-0496
opened: 2026-09-05
closed: 2026-09-07
pr: null
claimed_by: null
blocked_on: null
needs_bake: false
closed_at: 2026-09-07T12:06:10.512Z
claimed_run: null
---

The 1840 census images 51-74: the names and cells of the sheets the inventory finds, read line by line.

Piece 2 of 2 of **T-0496 — The 1840 census deposit is 75 page images and 210 heads on seven printed pages are the only names read from it: images 51-75**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)
- Depends on **T-0741**, which names the 24 sheets. This piece reads them.
- Expect to **split on measurement**, as T-0525, T-0526, T-0528 and T-0535 all were: two
  left sheets to the cell is one run's demonstration, and this group holds more than two.
  The split is by printed page, which T-0741's inventory is what makes possible.
- Every line gets a record — readable or `illegible`, never skipped — with `as_read`,
  `normalized`, `name_confidence` and `reading: scan_verified`; enumeration order kept.
- Any page of this group inside PR #670's calibration set (229-235) is cross-checked line
  by line against #670's rows, with the agreement count stated and every disagreement
  listed. Neither reading is deleted.
