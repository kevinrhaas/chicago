---
id: T-0963
title: The 1840 census printed 212 and 213 read to the name and the cell: 33SQ-GYYJ-RY and 33SQ-GYYJ-RK, every line, every column closed against the sheet's own footings
state: done
epic: META
requested_by: owner
seen: false
effort: S
legacy_id: null
parent: T-0746
opened: 2026-09-07
closed: 2026-09-07
pr: 1029
claimed_by: run 9/7/2026, 7:06:13 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-07T13:09:27.574Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34119573505
---

The 1840 census printed 212 and 213 read to the name and the cell: 33SQ-GYYJ-RY and 33SQ-GYYJ-RK, every line, every column closed against the sheet's own footings.

Piece 1 of 5 of **T-0746 — The 1840 census images 51-74: the names and cells of the sheets the inventory finds, read line by line**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)
- Two left sheets: image 70 `33SQ-GYYJ-RY` (printed **212**, inventoried at 31 lines) and
  image 69 `33SQ-GYYJ-RK` (printed **213**, inventoried at 30 lines). Both are
  `inventoried_only` in `coverage.json` and neither is in PR #670's calibration set, so
  there is no cross-check to run against #670 here — the check is the sheet's own arithmetic.
- Every ruled line carrying an entry gets a record — readable or `illegible`, never
  skipped — with `as_read`, `normalized`, `name_confidence` and `reading: scan_verified`,
  in the enumerator's order, never reordered.
- The line count is **counted off the ink**, not taken from the inventory. Groups 1 and 2
  both found the contact/820 px estimate reads LONG by one to four lines and never short,
  so a correction downward is expected and is recorded either way.
- All thirty-eight cell columns of each leaf are read against column bounds MEASURED on
  that leaf, and every column the sheet carries a printed footing for is closed against
  it. A residual is published, never adjusted away; a blank cell on this form is a 0 and
  a column that was not read is not a 0.
- `coverage.json` is updated for both images: `read_state`, `page_file`, the counts block,
  and the group's `declared_by`. A hole must still fail rather than pass quietly.
