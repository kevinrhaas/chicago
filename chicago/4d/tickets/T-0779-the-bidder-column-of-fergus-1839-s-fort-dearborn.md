---
id: T-0779
title: The bidder column of Fergus 1839's Fort Dearborn sale is still the OCR's: three ditto marks it mapped no ink for, and the names it mangled
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-04
closed: 2026-09-06
pr: 1006
claimed_by: run 9/6/2026, 4:24:37 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-06T22:07:43.995Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34060626354
---

The bidder column of Fergus 1839's Fort Dearborn sale is still the OCR's: three ditto marks it mapped no ink for, and the names it mangled.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

T-0679 read every numeral of printed pages 47-50 off the page images and regraded those
rows `scan_verified` — a grade the corrections file is careful to scope to the NUMERAL
columns, because the bidder column was deliberately left alone. Two things are wrong in it,
and both are legible on the same images:

- **Three ditto rows have no bidder at all**, because the OCR mapped no ink to the cell:
  block 10's lot 18 (a ditto of J. Russell), block 10's lot 24 (of J. Y. Scammon) and
  block 11's lot 4 (of A. D. Stewart). The page prints a ditto mark against each.
- **Names the scan mangled** are carried into `bidder` and therefore into `entities` and
  the 1835 crosswalk: `Prancis Walker` for Francis Walker, `John PTnnerty` for John
  Fennerty, `O. II. Thompson` for O. H. Thompson, `J. Iv. Botsford` for J. K. Botsford,
  `D. Brainarcl` for D. Brainard, `!c . Walker` for C. Walker, `J- Burgess` for J. Burgess,
  `R. T. Plaines` for R. T. Haines.

The last one matters most: R. T. Haines is one bidder, and `R. T. Plaines` splits him into
two. `tools/crosswalk_fergus_1839_lots.py` matches on surname, so a repaired name changes
who this list corroborates.

**Acceptance:** the bidder cells read off the page images through the same corrections
layer T-0679 built, the ditto rows given the name their mark carries, the crosswalk
regenerated, and the `grade_note` in the corrections file updated to say the grade now
covers the whole row.
