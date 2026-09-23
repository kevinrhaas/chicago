---
id: T-0754
title: 33S7-9YYJ-6H's SCHOOLS footing under No. of Scholars is written and does not read: two glyphs where a 40 would stand, and no bowl
state: done
epic: META
requested_by: loop
seen: false
effort: S
legacy_id: null
parent: null
opened: 2026-09-05
closed: 2026-09-06
pr: 1020
claimed_by: run 9/6/2026, 9:24:27 PM CT
blocked_on: null
needs_bake: false
closed_at: 2026-09-07T03:20:09.306Z
claimed_run: https://github.com/kevinrhaas/polecat-platform/actions/runs/34075958321
---

33S7-9YYJ-6H's SCHOOLS footing under No. of Scholars is written and does not read: two glyphs where a 40 would stand, and no bowl.


The SCHOOLS, &c. block of `33S7-9YYJ-6H` is footed, which T-0629 found by looking where nothing
had looked. Under **Primary and Common Schools** the footing is a single bold slash of exactly the
body figure's form, read **1**, and that column closes: one entry of 1 in the body, 1 at the foot.

Under **No. of Scholars** the footing is written and **does not read**. Three components at
`x3550-3588 y2967-3009` — a long diagonal, a second below and parallel to it, and a shorter hooked
stroke to their right — spanning 38 px against the body 40's 48. It is a two-glyph figure by
extent, standing where a 40 would stand, and every test that would make it a 40 fails:

- the **bowl test** returns 0 px of enclosed paper against the body 40's 25, so the second glyph
  does not close into a nought;
- the first glyph does not repeat the body 4's near-horizontal crossbar;
- the ink is about half the body figure's depth (mask 582 px against 979) — a drier pen at the
  foot of the leaf, on paper already curling into the binding.

T-0629 refused to assume it, because assuming it is exactly how a column is made to close. So the
No. of Scholars column does not close, and the sheet's second schools figure has no check.

**Acceptance:** (state it before working — the definition of done, never weakened to pass)

- The footing is read at magnification against this hand's own digit forms elsewhere on the leaf
  and on its siblings 5V and 8D, and committed with its confidence — or the refusal is restated
  with what was tried, and the cell stays `null`.
- If it reads 40, `lower_blocks_T0629.schools_footing.no_of_scholars_primary` is filled and the
  column is recorded as closing; if it reads anything else, the disagreement with the body's 40
  is written down and not reconciled by adjusting either.
- No figure is chosen because it makes the column close.

**Links:** T-0629 (the reading this comes out of) · T-0645 (the two-stroke figure) ·
`data/research/census_1840/pages/33S7-9YYJ-6H.json` § `lower_blocks_T0629` ·
`tools/read_census_lower_blocks.py 33S7-9YYJ-6H --footer`
