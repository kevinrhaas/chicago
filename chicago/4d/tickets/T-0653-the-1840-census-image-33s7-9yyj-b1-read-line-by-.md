---
id: T-0653
title: The 1840 census image 33S7-9YYJ-B1 read line by line and closed against its own printed column totals
state: done
epic: META
requested_by: owner
seen: false
effort: S
legacy_id: null
parent: T-0641
opened: 2026-09-04
closed: 2026-09-04
pr: 768
claimed_by: run 9/4/2026, 2:18:59 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-04T07:47:27.639Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/33846649199
---

The 1840 census image 33S7-9YYJ-B1 read line by line and closed against its own printed column totals.

Piece 1 of 3 of **T-0641 — The 1840 census images 1-25: continuation sheets 33S7-9YYJ-B1, -B2 and -BF read line by line and closed against their own printed column totals**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

A `pages/33S7-9YYJ-B1.json` on 33S7-9YYJ-8D's shape: one record per ruled line, all 37
columns of the continuation sheet as integers in the sheet's own order, and the sheet
closed against its own printed footer row, with any residual recorded rather than
adjusted away. Coverage group 1's `read_state`, `page_file` and line count updated.

`reading: scan_verified`; enumeration order is data; no IPUMS serial here (T-0504);
nothing here mints or regrades an 1835 resident; the deposit is read-only.
