---
id: T-0525
title: The 1840 census images 26-50: names and cells of the left sheets printed 207, 208, 209 and 211
state: split
epic: META
requested_by: owner
seen: false
effort: S
legacy_id: null
parent: T-0495
opened: 2026-09-03
closed: 2026-09-03
pr: null
claimed_by: null
blocked_on: null
needs_bake: false
---

The 1840 census images 26-50: names and cells of the left sheets printed 207, 208, 209 and 211.

Piece 3 of 7 of **T-0495 — The 1840 census deposit is 75 page images and 210 heads on seven printed pages are the only names read from it: images 26-50**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**What this piece is.** Names and cells for four left sheets of group 26-50:
`33SQ-GYYJ-93G` (printed 207), `33SQ-GYYJ-992` (208), `33SQ-GYYJ-93Y` (209), `33SQ-GYYJ-97P` (211).
Inventoried in `data/research/census_1840/coverage.json`; ~31, 31, 31 and 34 lines carrying an entry.

**Acceptance:** (one demonstration, never weakened to pass)
- One `pages/<id>.json` per image, every ruled line with an entry present (or `illegible`), enumeration
  order preserved, `reading: scan_verified`, no IPUMS serial attached.
- Column sums checked against the printed totals at the foot of each sheet, as T-0530 establishes.
- `coverage.json` moves these four from `inventoried_only` and restates their line counts exactly.
