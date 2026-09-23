---
id: T-0646
title: The 1840 census image 33S7-9YYJ-6Q: the TOTAL column reads 173 against a printed 198, and no reading of the matched-pair glyph closes the gap
state: done
epic: META
requested_by: owner
seen: false
effort: S
legacy_id: null
parent: T-0631
opened: 2026-09-04
closed: 2026-09-04
pr: 767
claimed_by: run 9/4/2026, 2:01:37 AM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-04T07:47:24.647Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/33846638378
---

The 1840 census image 33S7-9YYJ-6Q: the TOTAL column reads 173 against a printed 198, and no reading of the matched-pair glyph closes the gap.

Piece 2 of 2 of **T-0631 — The 1840 census image 33S7-9YYJ-6Q: the TOTAL column read digit by digit against the committed line grid and closed against its printed 198**, split because the parent needed more than one run's demonstration to be done. The parent keeps the full ask and its links; this ticket owns one slice of it.

**Acceptance:** (state it before working — one demonstration, never weakened to pass)

**Where this stands after T-0648.** All thirty lines of the TOTAL column are read and committed in
`data/research/census_1840/pages/33S7-9YYJ-6Q.json` `records[]`, each with a confidence and the glyph
note it rests on. They sum to **173** against the enumerator's own printed **198**. The residual of 25
is recorded and was not spent: nothing was moved to make the total come out.

**The one thing this ticket must not assume.** The gap is NOT the matched-pair decision. Reading the
sheet's five matched pairs (lines 6, 8, 9, 10, 17) as 11 instead of 4 gives 208; four of them gives
201; three gives 194. **No count of them gives 198**, so the footing does not adjudicate the pair and
the pair does not explain the residual.

**Where to look.** Seven lines are graded `low` and they are where the 25 most likely lies:
- lines 11 and 13, the two two-digit readings that turn on one ambiguous second glyph — 15 against 12,
  and 16 against 10;
- lines 20 and 21, the sheet's two largest single glyphs, read 2 apiece at ten times magnification
  where the bowl and the hook are one unbroken stroke;
- lines 4, 23 and 26 — the 7, 8 and 9 forms, for which this book has no labelled exemplar on any sheet
  whose TOTAL column closes.

The twelve slave columns are also still unread on this sheet, and the TOTAL is defined as persons in
the family INCLUDING slaves. Nothing on the leaf suggests a mark in that block, but it has not been
demonstrated empty the way the three empty industry columns have.

**Do not weaken the acceptance.** The column closes at 198 or the residual is restated with the reason
it survived a second reading.
