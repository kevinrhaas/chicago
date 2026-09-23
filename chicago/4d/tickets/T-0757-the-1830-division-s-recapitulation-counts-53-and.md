---
id: T-0757
title: The 1830 division's recapitulation counts 53 and 88 families on leaves that carry 55 and 39: re-count both against the enumerator's column
state: done
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-05
closed: 2026-09-07
pr: 953
claimed_by: null
blocked_on: null
needs_bake: false
closed_at: 2026-09-07T08:38:16.021Z
claimed_run: null
---

The 1830 division's recapitulation counts 53 and 88 families on leaves that carry 55 and 39: re-count both against the enumerator's column.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

**The finding, T-0605 (2026-09-05).** The division that contained Chicago in 1830 is leaves n576,
n578, n580, n582 and n584 of Internet Archive item `populationsc18300024unit`, and n586 is its
recapitulation. All five name leaves are now read head by head: 55 + 56 + 39 + 28 + 22 = **200**
heads of family.

The recapitulation's own family column, read off the page, gives **53 / 56 / 88 / 28 / 22**. Pages
2, 4 and 5 agree with the leaves exactly. Pages 1 and 3 do not — 53 written against 55 read on
n576, and 88 written against 39 read on n580. The column as read also sums to 247, not to the
**199** written beneath it, while the leaves sum to 200. So at least one of the two open figures is
a misreading of the enumerator's digits, and possibly both are.

**What this is not.** It is not a reason to change any reading. Nothing in `census_1830` is graded
on the recapitulation; the transcription at
`data/research/census_1830/text/peoria_putnam_1830_recapitulation_n586.txt` states the
disagreement and stops there, and `coverage.json` carries it under `not_declared_and_why`.

**The ask.**

1. Re-read the recapitulation's family column on n586 at higher magnification — the two open cells
   are page 1 (53 or 55) and page 3 (88, 38 or 39) — and the division total (199 or 197).
2. Re-count the name rows of n576 and n580 against the page images, row by row, and say whether 55
   and 39 stand. n576 was counted in four overlapping crops for T-0605; a fifth, single-crop count
   would be an independent check.
3. Write the outcome into the recapitulation transcription and into `LEAF_TOTALS` in
   `tools/read_census_1830.py`. If the figures still do not close, say so in those words and leave
   them open — an enumerator's arithmetic is allowed to be wrong, and this project does not correct
   a page to make a sum work.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

- Every cell of n586's family column and its total is read at a magnification stated in the file,
  and n576's and n580's row counts are re-derived independently of T-0498's and T-0605's crops.
- Whatever the outcome, `read_census_1830.py --check` and `research_domains.py --check` stay green
  and no record's confidence moves because of it.

**Links:** T-0498 · T-0605 · `data/research/census_1830/coverage.json`
