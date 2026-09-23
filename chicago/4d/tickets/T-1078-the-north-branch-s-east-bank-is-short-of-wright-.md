---
id: T-1078
title: The North Branch's east bank is short of Wright's ink on two stretches, one of them the splice row: 81 rows of 932 by more than 10 m, up to 33.8 m
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-12
closed: 2026-09-12
pr: 1199
claimed_by: run 9/12/2026, 9:57:30 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-12T15:28:49.106Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34700623403
---

The North Branch's east bank is short of Wright's ink on two stretches, one of them the splice row: 81 rows of 932 by more than 10 m, up to 33.8 m.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

Found by T-1072 while tracing the reach, measured rather than suspected, and filed instead of
smoothed over. `tools/trace_north_branch.py` runs at `hue_tol` 7 because at 8 the west bank
steps 93 m into Wabansia's platted lots — a categorical error — and the price is paid on the
east bank, which the looser setting reads better.

**Measured** (all 932 rows of the reach, this trace's east boundary against Wright's inked
east bank, `tools/trace_north_branch.py` + `trace_river.ink_mask`):

| | median | p90 | rows > 10 m short |
|---|---|---|---|
| `hue_tol` 7 (committed) | 1.4 m inside the ink | 8.5 m | **81** — rows 728–779 and 1222–1251 |
| `hue_tol` 11 (the forks value) | 0.7 m | 4.3 m | 34 — but the west bank leaks 93 m |

The second stretch is the splice row itself: at row 1251 Wright's east bank is inked at
x 1234–1237, the committed forks polygon puts its corner at x 1247 (8.2 m outside the ink) and
this trace puts its at x 1188 (33.8 m inside), so the two polygons disagree by 60.1 m on that
one side of one row. The west side of the same splice agrees to 4.9 m.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

1. The east bank over rows 728–779 and 1222–1251 is read from the scan rather than from a
   tolerance — `bank_wash`'s dry-seam rule (T-0834's south-bank precedent) is the obvious
   candidate and is a reading, not a knob.
2. The measurement above is re-run and quoted before and after, on all 932 rows, and the west
   bank is shown NOT to have moved into the lots: no row's west boundary west of Wright's
   inked west bank by more than the p90 this ticket records.
3. The splice disagreement at row 1251 is re-measured against the ink on both sides.
4. `docs/RESEARCH/north_branch_wabansia.md` § 5 is updated with the new numbers, or says why
   the sheet cannot support better.
