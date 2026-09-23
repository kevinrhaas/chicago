---
id: T-0945
title: Two open readings of NARA M704 roll 57 leaf n167 disagree on manufactures_and_trades and write the leaf to two different filenames
state: withdrawn
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-07
closed: 2026-09-09
pr: null
claimed_by: null
blocked_on: folded into T-0944: the same leaf n167 and the same 5-residual
needs_bake: false
closed_at: 2026-09-10T04:20:06.090Z
claimed_run: null
---

**Found by T-0927, 2026-09-07,** reading PR #1011 against PR #1012 before closing #1011 as
superseded — which is why #1011 was NOT closed in that pass.

Both PRs read the same leaf, NARA M704 roll 57 leaf n167 (the continuation of printed 232),
line by line, and both commit 31 records. Compared cell by cell across all seven industry
columns and the TOTAL column, they agree everywhere **except one cell**:

| | line 13, `manufactures_and_trades` |
|---|---|
| PR #1011 | **6** |
| PR #1012 | **1** |

That single glyph is the whole of the disagreement, and it decides the column:

- #1011 sums the column to **15** against a printed footing of 15 and records
  `closes: true, residual: 0`.
- #1012 sums it to **10** against the same footing and records "DOES NOT CLOSE, and the 5
  is left open", having swept the column twice at 4.5x for an eighth entry it did not find.

#1012 goes further and records `the_two_residuals`: that the TOTAL column is also short by
exactly 5 (193 against 198), and that the same 5 appearing twice is noted without anything
inferred from it. If line 13 is a 6, one of those two residuals disappears and that
coincidence does not exist.

**Two further conflicts, if both land:**

1. **Two filenames for one leaf.** #1011 writes
   `data/research/census_1840/pages/nara_m704_r57_n167.json`; #1012 writes
   `data/research/census_1840/pages/m704_r57_n167.json`. Neither is on `dev`, so nothing
   collides today and nothing warns — the second to merge simply adds a second page file
   for the same leaf.
2. **Blank cells are recorded two ways.** #1011 writes every empty cell as `0` inside a
   flat `cells` object; #1012 writes them as `null` inside a nested `industry` object, on
   the stated rule that "nothing is read as a zero" because the sheet foots nothing where
   nothing stands above. The second is the convention the rest of this project's census
   pages use.

**Acceptance:**

1. Line 13's `manufactures_and_trades` cell is read again at the image, at the exposure
   each PR names, and the verdict says 6 or 1 with the glyph described — not with the
   column closure as the argument, since the closure is what is in question.
2. The column closure for `manufactures_and_trades` is restated from that verdict, closing
   or not, with nothing adjusted to make it close.
3. One page file, one path, for this leaf. The chosen path is stated and the other reading
   is either merged into it with its disagreements recorded, or cited and dropped.
4. Blank cells carry one convention across the leaf, and it is the one the other census
   pages use.
5. If line 13 reads 6, `the_two_residuals` note is removed rather than left standing on a
   coincidence that no longer exists.

**Links:** T-0912 · T-0911 · T-0927 · T-0944 · PR #1011 · PR #1012.
