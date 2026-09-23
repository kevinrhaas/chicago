---
id: T-0530
title: The 1840 census images 26-50: the age-band, coloured and industry cells of printed pages 230 and 232, checked against the sheets' own column totals
state: done
epic: META
requested_by: owner
seen: false
effort: S
legacy_id: null
parent: T-0495
opened: 2026-09-03
closed: 2026-09-03
pr: 691
claimed_by: run 9/3/2026, 3:00:53 AM CT
blocked_on: null
needs_bake: false
---

The 1840 census images 26-50: the age-band, coloured and industry cells of printed pages 230 and 232, checked against the sheets' own column totals.

Piece 2 of 7 of **T-0495 — The 1840 census deposit is 75 page images and 210 heads on seven printed pages are the only names read from it: images 26-50**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**What this piece is.** The cells the parent ticket asks for, on the two pages T-0523 read the names of:
`33S7-9YYJ-NY` (printed 230) and `33S7-9YYJ-W6` (printed 232) for the free-white age bands and the free
coloured columns, and their paired continuation sheets for the family total, the six industry columns,
pensioners and the schools and illiteracy columns.

**Why it is its own ticket.** 26 narrow columns of single strokes per line, where a mark read one column
off is a person of the wrong age. It is only safe to commit if it is checked, and the sheet carries its
own check: the PRINTED COLUMN TOTALS at the foot of every page. T-0523 left every `records[].cells` as
`null` with `cells_state: "not_read"` rather than commit a half-checked row.

**Acceptance:** (one demonstration, never weakened to pass)
- Every one of the 62 lines has its cells, or is recorded `illegible` with the reason.
- Each page's per-column sums are compared with the printed totals at the foot of the sheet and the
  comparison is stated; a column that does not reconcile is named, not smoothed.
- `cells_state` on both page files moves off `not_read`.
