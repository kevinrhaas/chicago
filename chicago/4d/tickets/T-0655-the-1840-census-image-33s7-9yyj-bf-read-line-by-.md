---
id: T-0655
title: The 1840 census image 33S7-9YYJ-BF read line by line and closed against its own printed column totals
state: done
epic: META
requested_by: owner
seen: false
effort: S
legacy_id: null
parent: T-0641
opened: 2026-09-04
closed: 2026-09-04
pr: 773
claimed_by: run 9/4/2026, 3:50:23 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-04T10:07:15.403Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/33855127716
---

The 1840 census image 33S7-9YYJ-BF read line by line and closed against its own printed column totals.

Piece 3 of 3 of **T-0641 — The 1840 census images 1-25: continuation sheets 33S7-9YYJ-B1, -B2 and -BF read line by line and closed against their own printed column totals**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

A `pages/<familysearch_id>.json` on 33S7-9YYJ-8D's and -B1's shape: one record per ruled
line, all 37 columns as integers in the sheet's own order, and the sheet closed against
its own printed footer row, with any residual recorded rather than adjusted away.
Coverage group 1's `read_state`, `page_file` and line count updated.

**Start from B1's geometry, it will save the run an hour.** `pages/33S7-9YYJ-B1.json`
§ `geometry_note` records that these leaves are sheared on the exposure and how to undo
it (x' = x - slope*(y-ref), y untouched), and § `form_note` the 37 columns in order.
B1's rules, after de-shearing, stand at x = 1258, 1453, 1519, 1583, 1648, 1729, 1809,
1890, 1955 and then 2394, 2477, 2556, 2634, 2715, 2792, 2874, 2957, 3041, 3121, 3210,
3293, 3364, 3428, 3494, 3575, 3636, 3705. Measure the slope for YOUR leaf — it is not
shared — but the column widths are the printed form's and will be close.

Fit the line grid to the INDUSTRY columns' ink and read the TOTAL column against it,
never the other way round: `tools/fit_census_line_grid.py <id>` does the fit off the
`entry_y` this file commits, and on B1 it separated the right line count from every
other by a factor of five. `tools/read_census_continuation.py` still exits on these
four images; do not spend the run on it.

This hand writes 11 as two strokes about 30 px apart and 1 as one stroke (T-0643's
finding, and it holds on B1); its 5 carries a top bar and its 6 is a closed loop with a
tail rising to the right.

`reading: scan_verified`; enumeration order is data; no IPUMS serial here (T-0504);
nothing here mints or regrades an 1835 resident; the deposit is read-only.
