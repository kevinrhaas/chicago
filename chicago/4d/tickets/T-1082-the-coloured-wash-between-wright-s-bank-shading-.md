---
id: T-1082
title: The coloured wash between Wright's bank shading and his inked bank line: 51 east-bank rows short by more than 10 m and 34 west-bank rows standing outside the ink, all of them behind a colour the tract layer has not identified
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-12
closed: 2026-09-12
pr: 1222
claimed_by: run 9/12/2026, 8:39:50 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-13T02:23:17.177Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34730968938
---

Found by T-1078 while repairing the other half of the same fault, measured rather than suspected.

`tools/trace_north_branch.py` reads the reach's banks off Wright's grey bank wash. On five
stretches of the west bank and one of the east, a **wash of another colour** stands between that
grey shading and the inked bank line beside it, so the trace has nothing to carry the boundary
across and stops short. `tr.seam_wash` (T-1078) correctly declines: a path that crossed the
colour would be the 93 m leak into Wabansia's platted lots that `hue_tol` 7 exists to prevent
(docs/RESEARCH/north_branch_wabansia.md § 3).

**Measured** (`tools/measure_north_branch_banks.py`, all 932 rows of the reach, against
`trace_river.ink_mask`; the committed baseline carries the columns):

| | rows > 10 m short | worst | rows OUTSIDE the ink | worst outside |
|---|---|---|---|---|
| east bank | **51** — rows 728-779 | 14.94 m | 0 | — |
| west bank | 35 | 20.63 m | **34** — rows 707-710, 715-717, 922-939, 948-951, 1247-1251 | 9.96 m |

At rows 728-779 the intervening band is 17 to 19 px wide and reads `dark` 26-67, `tint` 12-61
against a tolerance of 7 — a coloured wash, not thin grey. Rows 1247-1251 are the west side of
the splice row, where the boundary stands 2.1 m *outside* Wright's pen line.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

1. The colour is IDENTIFIED, against the sheet's own legend swatches, the way T-1076 measured
   the Michigan St tract's wash: which of Wright's nine surveys washed the unplatted ground
   east of the North Branch, and which washed the strip on the west. If the swatches cannot
   separate it, that is the finding and it is recorded as one — do not guess a tract.
2. Only then, whether the boundary may be carried across it: a wash whose tract is known is
   ground with a name, and a bank drawn over named ground is the error `hue_tol` 7 refuses. The
   likely answer is that these rows stay short and the reading is that the sheet does not draw
   a bank there — say so if so.
3. `tools/measure_north_branch_banks.py` is re-run either way, and its committed ceiling
   (`LEAK_BUDGET_M`, a ratchet at 14.23 m) comes down if the west bank improves.
4. docs/RESEARCH/north_branch_wabansia.md § 5 records the outcome.

Depends on the tract layer (T-0792) for what the nine legend washes are. It does not need the
whole layer — one identified swatch for each of these two grounds is enough.
