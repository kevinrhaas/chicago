---
id: T-0762
title: The 1840 census image 26-50: continuation sheet 33S7-9YYJ-VJ read line by line
state: done
epic: META
requested_by: owner
seen: false
effort: S
legacy_id: null
parent: T-0528
opened: 2026-09-05
closed: 2026-09-06
pr: 1008
claimed_by: run 9/6/2026, 5:22:11 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-06T23:10:02.503Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34063360894
---

The 1840 census image 26-50: continuation sheet 33S7-9YYJ-VJ read line by line.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

Piece 4 of 4 of **T-0528 — The 1840 census images 26-50: the nine continuation sheets, paired
to their left sheets by printed page**. T-0658 owned three sheets and demonstrated two of them
inside one run; this ticket carries the third, which the run split off rather than shipping a
self-invented half. `33S7-9YYJ-VJ` is the 31-line leaf whose TOTAL footing T-0656 read as 117
with 107 named as the arguable alternate, and it is unpaired on both keys.

**What T-0658 leaves you.** The method is in `pages/33S7-9YYN-3CF6.json` and
`pages/33S7-9YYJ-V4.json` and it is worth reading before starting, because
`tools/read_census_continuation.py` will refuse this leaf too: the printed rules of these
leaves LEAN, 12 to 41 px across the body, and that tool fits them from one darkness profile
over the whole body. Take the profile in 300 px bands, interpolate between the bands, and
check the fitted grid against the printed heading before cutting a cell. The TOTAL column's
own ink gives the row grid; on 3CF6 its 27 centres sat on a 76.2 px pitch with no residual
over 16 px. Budget about sixty tool calls of crop-and-read for the sheet, and commit the page
file as soon as it closes rather than at the end of the run.

**The prize on this leaf is the footing itself.** T-0656 could not choose between 117 and 107
— the middle glyph is a short slant with a tick at its foot, not this hand's filled-oval 0 —
and refused to let the pairing rest on the choice. A line-by-line reading of the TOTAL column
that sums to one of them settles it, exactly as V4's did: 21 figures summing to 100 is what
fixed that leaf's line count against two earlier counts of 20 and 31.

**Acceptance:** (one demonstration, never weakened to pass)
- `33S7-9YYJ-VJ` read line by line, with a page file in the shape the two sheets above use.
- Every footed column checked against the enumerator's own figure, and a column committed
  ONLY where the lines read sum to it. A column that does not close keeps its residual, and
  its reading goes to `cells_first_pass` where nothing downstream can consume it.
- The 117-versus-107 question answered by the reading, or recorded as still open with what
  the reading found — never closed by preferring the figure that makes something else work.
- `coverage.json` and `pairing_key_26_50.json` carry whatever the reading corrects.
- `tools/check.sh` green.

**Links:** T-0528 (parent) · T-0656 (the pairing and the two keys) · T-0658 (the two sheets
already read, and the method) · T-0761 (the tooling fix this reading will want and must not
wait for).

