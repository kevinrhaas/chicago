---
id: T-0645
title: Ten of the TOTAL figures on 33S7-9YYJ-6H are two strokes and nothing else: 11 over-runs the footing, 4 under-runs 8D's
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-04
closed: 2026-09-04
pr: 764
claimed_by: run 9/4/2026, 1:12:58 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-04T06:34:33.713Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/33839193831
---

Ten of the TOTAL figures on 33S7-9YYJ-6H are two strokes and nothing else: 11 over-runs the footing, 4 under-runs 8D's.

**Found by T-0628**, which read the TOTAL column of `33S7-9YYJ-6H` against the line
index it fitted and could not settle this one figure. The reading it committed is the
one the sheet's own footing fixes; the residual is recorded rather than removed, and
this ticket carries the question so the next pass does not have to rediscover it.

**The figure.** Ten of the twenty-nine numbers in that column are two parallel slanted
strokes, no bowl, nothing else — lines 1, 2, 3, 8, 9, 15, 16, 18, 20 and 27. Two
readings are available and only two: two `1`s, which is `11`, or a single numeral
built from two strokes without a bowl, which in this hand could only be a `4`.

**What argues 11.** The footing under this sheet's manufactures column is the SAME
two-slash form and is `11` beyond argument: T-0627 read eleven entries in that column,
a `2` and nine `1`s, and they close on it exactly. On the sibling continuation sheet
`33S7-9YYJ-8D`, T-0643 met the identical figure on six lines and read it `11` on a
stroke-pitch test — about 30 px there, against that sheet's own two-digit `17` at
32 px and its three-digit `106` at 36 px.

**What argues against it.**

- **The pitch test does not separate them on 6H.** Measured on this leaf, the footing's
  confirmed `11` puts its two slashes 27.4 px apart and the schools block's two-digit
  `40` puts its digits 19 px apart — while the sheet's confirmed single `5` spreads its
  own strokes over 31 px. A within-digit spread and a between-digit pitch overlap here,
  and the ten pairs sit inside the overlap at 12.2 to 26.5 px. The instrument that
  worked on 8D returns nothing on 6H.
- **The arithmetic runs the wrong way.** With the ten read as `11` the column's 27
  committed numbers sum to 207 and floor at 209, and the footing's first glyph is a
  plain slash that reads `1` as surely as anything on the sheet. No three-figure
  footing beginning in 1 can carry 209. Read as `4` the same 27 numbers sum to 137,
  which a `1??` footing carries comfortably.
- **The corpus says 11 is rare.** Over the 527 households already read to the cell from
  this deposit's left sheets the mean household is 4.84 and `11` occurs five times —
  under 1%. Ten of 29 on one sheet is 34%. The nearest continuation sheet with a
  legible footing, 8D, foots at 106 over 32 lines: a mean of 3.3.
- **8D does not close either, and it fails the same way.** Read with six elevens it
  sums to 121 against a printed 106, a residual of +15 that T-0643 recorded and did
  not explain. Two sheets over-running their own footings in the same direction, both
  full of the same figure, is a pattern and not two accidents.

**Acceptance:** the two-stroke figure is settled for the continuation-sheet series by
evidence outside the glyph, and every page file carrying it is restated to match —
including `33S7-9YYJ-6H` (ten instances, currently `11`) and `33S7-9YYJ-8D` (six
instances, currently `11`, residual +15). Settling it means one of:

- pairing a carrying sheet to its left-hand partner, whose households are the same
  families counted a second time, and reading their sizes off the age bands — the
  pairing work T-0642 and T-0528 already own is what would produce it; or
- a third continuation sheet whose footing IS legible and whose body carries the
  figure, so the arithmetic decides it; or
- a demonstration that the hand's `4` is or is not two bowl-less strokes, drawn from
  a page of this deposit where a `4` stands in a cell whose value is independently
  known.

A pass that merely re-reads the ten glyphs at higher magnification and picks does NOT
close this. The glyphs are already read; what is missing is a second source. If the
answer turns out to be `11`, the acceptance is met by saying so with the evidence and
by explaining the two footing residuals it leaves behind — not by leaving them
unremarked.

**Where it is written down:** `data/research/census_1840/pages/33S7-9YYJ-6H.json` §
`two_stroke_figure_problem` and § `footer_total_argument`; the ten records carry
`total_confidence` of `medium` or `low` and each names this problem.
