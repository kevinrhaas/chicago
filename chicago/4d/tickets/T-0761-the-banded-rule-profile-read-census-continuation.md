---
id: T-0761
title: The banded rule profile read_census_continuation.py needs: the printed rules of a continuation leaf lean up to 41 px and one profile over the whole body loses them
state: withdrawn
epic: META
requested_by: loop
seen: false
effort: S
legacy_id: null
parent: null
opened: 2026-09-05
closed: 2026-09-17
pr: null
claimed_by: null
blocked_on: folded into T-1290
needs_bake: false
closed_at: 2026-09-17T19:18:38.853Z
claimed_run: null
---

The banded rule profile read_census_continuation.py needs: the printed rules of a continuation leaf lean up to 41 px and one profile over the whole body loses them.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

Found by T-0658, which could not use the tool on either of the leaves it read.

**The measurement.** `tools/read_census_continuation.py` locates the printed vertical rules of
a continuation leaf from a single column-darkness profile taken over the whole body band. That
works only if a rule is at the same x at the top of the leaf and the bottom, and on these
exposures it is not. On `33S7-9YYN-3CF6` the nine rules of the TOTAL-and-industry run stand at
1004, 1194, 1265, 1329, 1396, 1480, 1564, 1647 and 1712 px in a band at the head of the body
and 12 to 17 px further right in one at its foot; on `33S7-9YYJ-V4` the same rules lean **41
px**, against column widths of 64 to 84. A rule that walks that far smears out of a
whole-body profile below the tool's threshold, and the tool then reports what it saw: on 3CF6,
`no industry run bracketed by TOTAL and PENSIONERS: the form is not as expected`, at every
`--cover` from 0.40 to 0.60; on V4 it cannot fit a row grid at all.

**What the fix is.** Take the profile in bands — 300 px worked by hand — fit each rule as a
chain across the bands, and interpolate the grid in y. Two page files already carry that
measurement done by hand and can be used as fixtures. Keep the tool's refusal to read a digit:
the boxes are the measurement and a human reads the glyph.

**A second thing the banded profile buys for free.** It separates a printed rule from a
crease, which a single profile cannot. Both leaves carry an apparent tenth rule — x=1250 on
3CF6, x=1333–1365 on V4 — that appears in every band and does NOT lean with the printed ones.
On V4 that crease runs through the TOTAL column and makes the footed `100` look as though its
last `0` has crossed into the mining cell. A rule that does not lean with its neighbours is a
crease, and the banded fit is what can say so.

**Acceptance:** (one demonstration, never weakened to pass)
- The rules located per band and interpolated, with the tool's own self-test carrying a leaf
  whose rules lean.
- `33S7-9YYN-3CF6` and `33S7-9YYJ-V4` both accepted, and the grid the tool fits agreeing with
  the hand measurement committed in their page files.
- The non-leaning crease reported as a crease rather than as a rule.
- No digit read by the tool. `tools/check.sh` green.

**Links:** T-0658 (the two readings that found this) · T-0762 · `pages/33S7-9YYN-3CF6.json`
§ grid_note and § tooling_note · `pages/33S7-9YYJ-V4.json` § grid_note and § exposure_note.

