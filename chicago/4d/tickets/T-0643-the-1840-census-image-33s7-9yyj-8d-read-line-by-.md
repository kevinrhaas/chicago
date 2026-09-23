---
id: T-0643
title: The 1840 census image 33S7-9YYJ-8D read line by line and closed against its own printed column totals
state: done
epic: META
requested_by: owner
seen: false
effort: S
legacy_id: null
parent: T-0640
opened: 2026-09-03
closed: 2026-09-03
pr: 756
claimed_by: run 9/3/2026, 10:22:48 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-04T03:58:33.747Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/33831662063
---

The 1840 census image 33S7-9YYJ-8D read line by line and closed against its own printed column totals.

Piece 1 of 2 of **T-0640 — The 1840 census images 1-25: continuation sheets 33S7-9YYJ-8D and -9WS read line by line and closed against their own printed column totals**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

- `pages/33S7-9YYJ-8D.json` carries one record per ruled line with an entry: the twelve
  slave columns, the family TOTAL, the seven industry columns, pensioners, the ten
  deaf/dumb/blind/insane columns and the seven schools columns.
- Every committed column is checked against the enumerator's own footer row, transcribed
  as `footer_as_read`. A column that does not close keeps its residual; no line is altered
  to make a total come out.
- The exact count of ruled lines carrying an entry is restated off the sheet, against
  `coverage.json`'s inventory figure "to the nearest line".
- No pairing is asserted. The sheet publishes its page population as the key T-0642's
  pairing test will read, and is recorded as unpaired until then.
- Coverage group 1's `read_state` and `page_file` updated for this image.

`reading: scan_verified`; enumeration order is data; no IPUMS serial here (T-0504);
nothing here mints or regrades an 1835 resident; the deposit is read-only.
