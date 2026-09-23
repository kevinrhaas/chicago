---
id: T-0552
title: The 1840 census images 26-50: names and cells of the left sheets printed 216 and 217
state: done
epic: META
requested_by: owner
seen: false
effort: S
legacy_id: null
parent: T-0526
opened: 2026-09-03
closed: 2026-09-03
pr: 699
claimed_by: run 9/3/2026, 7:27:58 AM CT
blocked_on: null
needs_bake: false
---

The 1840 census images 26-50: names and cells of the left sheets printed 216 and 217.

Piece 1 of 2 of **T-0526 — The 1840 census images 26-50: names and cells of the left sheets printed 216, 217, 218 and 224**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

- `pages/33S7-9YYJ-DD.json` (printed 216) and `pages/33S7-9YYJ-RC.json` (printed 217): every ruled line with an
  entry present, enumeration order preserved, `reading: scan_verified`, all 38 age-band columns per line, no IPUMS
  serial attached.
- Every column summed and compared against the enumerator's own footings; the eight residuals are recorded on the
  page files rather than tidied.
- `coverage.json` moves these two images out of `inventoried_only` and restates their line counts as counted
  (216 = 31 lines, corrected from the inventory's 33; 217 = 31).

**Filed as T-0547 by the run that read the sheets; restamped T-0552 on merge** because dev had assigned T-0547 to
the continuation sheet 33S7-9YYJ-5V one batch earlier. The queue place is unchanged.
