---
id: T-0944
title: Printed 232's continuation foots 198 against a column that reads 193: T-0642's footing key no longer closes on the one pairing made outside the deposit
state: withdrawn
epic: META
requested_by: loop
seen: false
effort: M
legacy_id: null
parent: null
opened: 2026-09-07
closed: 2026-09-17
pr: null
claimed_by: null
blocked_on: folded into T-1290
needs_bake: false
closed_at: 2026-09-17T19:18:43.229Z
claimed_run: null
---

**Salvaged verbatim in substance from PR #1011 by T-0927, 2026-09-07.** It was filed there
as T-0922; that number has never existed on `dev`. The finding is the owner's to rule on
and would have gone with the PR.

**Found by T-0912, 2026-09-06, reading printed 232's continuation leaf (NARA M704 roll 57,
leaf n167) line by line.**

T-0911 paired printed 232 to that leaf and read its TOTAL footing as `195` — the figure
printed 232's own footings give — with `198` named as the arguable alternate at that
exposure. T-0912 settled the glyph at 198: the third figure carries a closed upper loop
joined to a lower bowl, which this hand's four 5s on the same leaf do not have and which
its 8 on line 23 does. The reading is on the glyph and not on the arithmetic.

That leaves three figures for one page and no two of them agree:

| what | figure |
|---|---|
| the continuation's TOTAL column, all 31 lines, read line by line | **193** |
| printed 232's free population by its own marks (T-0530) | **193** |
| printed 232's free population by its own printed footings | 195 |
| the continuation's own printed TOTAL footing | **198** |

T-0642's pairing test matches a left sheet's population against the right sheet's printed
TOTAL footing, and that key is now 5 out from the marks and 3 out from the footings. The
pairing itself is NOT in doubt — T-0911 recorded that it does not rest on the footing, and
T-0912 strengthened the sequence screen from 6 positions to 31 of 31 agreeing, on the
line-count key of 31 = 31. But the deposit-wide search of T-0543 REFUSED thirty-three
candidate sheets on that footing key, and the one pairing this project has made outside the
deposit is a pairing whose footing key does not close.

**The question is the owner's**, because it is about a test rather than about a reading:
does a footing key that misses by 5 refuse a pairing that both other strands carry, or is
an enumerator's slip in his own addition — which is what a 198 over a column of 193 is —
inside the tolerance the test always meant to allow? T-0543 already wrote that "a footing
is the enumerator's arithmetic and can be wrong, so a footing that misses by one or two is
a candidate to be screened rather than a refusal", and named 5 as its own threshold when it
recorded that "none of the 33 is within 5". This case sits exactly on that line.

**Acceptance:** the tolerance T-0642's footing key carries is stated as a number with the
reasoning for it; the thirty-three refusals of T-0543 are re-checked against that number and
any that no longer refuse are named; and printed 232's pairing carries whichever verdict
the stated rule gives it, rather than the verdict it has by having been ruled before the
footing was settled.

**Links:** T-0912 · T-0911 · T-0642 · T-0543 · T-0530 · T-0927 · T-0945 · PR #1011 · PR #1012.

## Folded in from T-0945 (2026-09-10) — the same leaf n167 and the same 5-residual

*T-0945: Two open readings of NARA M704 roll 57 leaf n167 disagree on manufactures_and_trades and write the leaf to two different filenames*

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
